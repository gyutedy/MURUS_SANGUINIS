#!/usr/bin/env python3
"""programma — SF_17_PROGRAMMA : le calendrier de publication, et rien d'autre.

Pouvoir V2 n°3 (PLAN_V2 étape 6) : les livrables acceptés partent en lots, à
**4–10 h d'intervalle**, via l'API officielle YouTube (`videos.insert` en
`privacyStatus: private` + `publishAt` natif, gratuit, 1 unité par insertion).

Trois règles tenues par ce fichier :

1. **Le tirage est fait une fois, et il est reproductible.** Les intervalles sont
   tirés d'une loi uniforme dans [4 h, 10 h] avec une graine écrite au ledger :
   le même `--seed` et les mêmes entrées rendent le même calendrier (T26). On ne
   retombe pas sur un calendrier « régulier » : chaque créneau est tiré.
2. **Rien ne se publie sans signature.** `schedule.json` sort avec
   `validated_by_magos: false` ; sans `true`, `--mode publish` refuse. Le projet
   ne poste pas : il prépare, l'opérateur signe (V7/t28).
3. **Idempotent.** Avant toute insertion, `videos.list` cherche le clip par son
   titre exact et son tag `murus:<id>` : s'il existe, on répond `deja_publie` et
   on n'insère rien (T28). Un `403 quotaExceeded` recule (1 h → 4 h → 12 h) et
   **ne retire jamais** un créneau du calendrier.

Aucun secret dans ce fichier : `YT_OAUTH_CLIENT_ID`, `YT_OAUTH_CLIENT_SECRET`,
`YT_OAUTH_REFRESH_TOKEN` vivent dans les secrets GitHub, lus à l'exécution.

Usage :
  python programma.py --mode plan --pack REVIEW/pack_stage.json --livrables DIR \
      --out REVIEW/schedule.json --provenance REVIEW/schedule.provenance.json --seed 20261123
  python programma.py --mode publish --schedule REVIEW/schedule.json [--dry-run] \
      [--maintenant 2026-11-24T02:00:00Z] [--request-out /tmp/requete.json]

Codes : 0 ok · 2 entrées illisibles · 3 calendrier non signé · 4 intervalle hors bornes
        · 5 quota/backoff (rien n'est perdu) · 6 échec de publication
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import random
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SCHEMA = "murus.schedule.v1"
SCHEMA_PROV = "murus.schedule.provenance.v1"
API = "https://www.googleapis.com/youtube/v3"
TOKEN_URL = "https://oauth2.googleapis.com/token"
MIN_H, MAX_H = 4.0, 10.0


def log(msg):
    print("PROGRAMMA : %s" % msg)


def refus(code, msg):
    print("PROGRAMMA REFUS (%d) : %s" % (code, msg), file=sys.stderr)
    sys.exit(code)


def iso(ts):
    return ts.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def lire_iso(txt):
    txt = str(txt).strip()
    if txt.endswith("Z"):
        return dt.datetime.strptime(txt, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    return dt.datetime.fromisoformat(txt).astimezone(dt.timezone.utc)


def charger_json(path, quoi):
    p = Path(path)
    if not p.is_file():
        refus(2, "%s introuvable : %s" % (quoi, p))
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        refus(2, "%s illisible : %s" % (quoi, e))


def inventaire_livrables(dossier, manifeste=None):
    """Les clips à publier. Aucun n'est inventé : le fichier doit exister."""
    clips = []
    if manifeste:
        data = charger_json(manifeste, "manifeste")
        for c in data.get("clips") or []:
            p = Path(dossier) / c.get("fichier", "")
            if not p.is_file():
                refus(2, "manifeste cite un livrable absent : %s" % p)
            clips.append({"id": c.get("id") or p.stem, "fichier": str(p),
                          "octets": p.stat().st_size,
                          "titre": c.get("titre") or c.get("metadata_title")})
    else:
        d = Path(dossier)
        if not d.is_dir():
            refus(2, "dossier de livrables absent : %s" % d)
        for p in sorted(d.glob("*.mp4")):
            ident = p.stem
            for marque in ("pur_", "_LIVRABLE"):
                ident = ident.replace(marque, "")
            clips.append({"id": ident, "fichier": str(p), "octets": p.stat().st_size,
                          "titre": None})
    if not clips:
        refus(2, "aucun livrable : un calendrier vide n'est pas un calendrier")
    return clips


def planifier(clips, seed, debut, min_h, max_h, metadonnees):
    """Tirage uniforme, une fois, reproductible par la graine."""
    if not (0 < min_h <= max_h):
        refus(4, "bornes d'intervalle incohérentes : %s–%s h" % (min_h, max_h))
    rng = random.Random(seed)
    tirages, quand = [], debut
    creneaux = []
    for i, clip in enumerate(clips):
        pause_h = rng.uniform(min_h, max_h)
        quand = quand + dt.timedelta(hours=pause_h)
        tirages.append(round(pause_h, 4))
        meta = metadonnees.get(clip["id"]) or {}
        creneaux.append({
            "rang": i + 1,
            "id": clip["id"],
            "fichier": clip["fichier"],
            "octets": clip["octets"],
            "intervalle_depuis_precedent_h": round(pause_h, 4) if i else None,
            "publishAt": iso(quand),
            "privacyStatus": "private",
            "titre": meta.get("metadata_title") or clip.get("titre") or clip["id"],
            "description": meta.get("description") or "",
            "tags": meta.get("tags") or ["murus", "murus:%s" % clip["id"]],
            "statut": "planifie",
        })
    return creneaux, tirages


def ecrire_calendrier(creneaux, seed, min_h, max_h, pack_token, out, provenance):
    calendrier = {
        "schema": SCHEMA,
        "pack_token": pack_token,
        "seed": seed,
        "bornes_intervalle_h": [min_h, max_h],
        "regle": "intervalle tiré une fois par siège, uniforme dans [4 h, 10 h] ; le projet ne poste pas",
        "validated_by_magos": False,
        "creneaux": creneaux,
        "nb_creneaux": len(creneaux),
    }
    contenu = json.dumps(calendrier, ensure_ascii=False, indent=2, sort_keys=True)
    calendrier["empreinte_sans_signature"] = hashlib.sha256(contenu.encode("utf-8")).hexdigest()
    p = Path(out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(calendrier, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if provenance:
        pr = Path(provenance)
        pr.parent.mkdir(parents=True, exist_ok=True)
        pr.write_text(json.dumps({
            "schema": SCHEMA_PROV,
            "generateur": "FR_B_CREATION/SF_17_PROGRAMMA/CODEBASE/programma.py",
            "graine": seed,
            "tirages_secondes": [round(t * 3600, 1) for t in
                                 [c["intervalle_depuis_precedent_h"] or 0 for c in creneaux]],
            "sha256_calendrier": hashlib.sha256(
                p.read_text(encoding="utf-8").encode("utf-8")).hexdigest(),
            "signature_requise": True,
            "note": "sans validated_by_magos: true, la publication refuse (code 3)",
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return calendrier


# ─────────────────────────── publication YouTube ────────────────────────

def jeton_acces():
    cid = os.environ.get("YT_OAUTH_CLIENT_ID")
    secret = os.environ.get("YT_OAUTH_CLIENT_SECRET")
    refresh = os.environ.get("YT_OAUTH_REFRESH_TOKEN")
    absents = [n for n, v in (("YT_OAUTH_CLIENT_ID", cid),
                              ("YT_OAUTH_CLIENT_SECRET", secret),
                              ("YT_OAUTH_REFRESH_TOKEN", refresh)) if not v]
    if absents:
        refus(3, "secrets OAuth absents : %s — publication impossible" % ", ".join(absents))
    corps = urllib.parse.urlencode({"client_id": cid, "client_secret": secret,
                                    "refresh_token": refresh,
                                    "grant_type": "refresh_token"}).encode()
    req = urllib.request.Request(TOKEN_URL, data=corps,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))["access_token"]


def deja_publie(jeton, titre, tag):
    """Idempotence : on cherche AVANT d'insérer (T28)."""
    q = urllib.parse.urlencode({"part": "id,snippet", "forMine": "true",
                                "q": titre, "type": "video", "maxResults": "5"})
    req = urllib.request.Request(API + "/search?" + q,
                                 headers={"Authorization": "Bearer " + jeton})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    for item in data.get("items") or []:
        sn = item.get("snippet") or {}
        if (sn.get("title") or "").strip() == titre.strip():
            return item.get("id", {}).get("videoId")
        if tag in (sn.get("tags") or []):
            return item.get("id", {}).get("videoId")
    return None


def requete_insertion(creneau):
    """La requête exacte, pour le dry-run : on vérifie ce qu'on enverrait."""
    return {
        "part": "snippet,status",
        "body": {
            "snippet": {"title": creneau["titre"][:100],
                        "description": creneau.get("description", "")[:5000],
                        "tags": creneau.get("tags") or [],
                        "categoryId": "24"},
            "status": {"privacyStatus": "private",
                       "publishAt": creneau["publishAt"],
                       "selfDeclaredMadeForKids": False},
        },
    }


def publier(creneau, jeton, dry_run, request_out):
    corps = requete_insertion(creneau)
    if request_out:
        Path(request_out).parent.mkdir(parents=True, exist_ok=True)
        Path(request_out).write_text(json.dumps({"creneau": creneau["id"], **corps},
                                                ensure_ascii=False, indent=2) + "\n",
                                     encoding="utf-8")
    if dry_run:
        return {"id": creneau["id"], "statut": "dry_run",
                "publishAt": corps["body"]["status"]["publishAt"],
                "privacyStatus": corps["body"]["status"]["privacyStatus"]}
    existant = deja_publie(jeton, creneau["titre"], "murus:%s" % creneau["id"])
    if existant:
        return {"id": creneau["id"], "statut": "deja_publie", "video_id": existant}

    fichier = Path(creneau["fichier"])
    if not fichier.is_file():
        refus(2, "livrable absent sur ce runner : %s (artefact non téléchargé)" % fichier)
    limite = 4 * 1024 * 1024
    taille = fichier.stat().st_size
    meta = corps["body"]
    init = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(meta).encode("utf-8"),
        headers={"Authorization": "Bearer " + jeton, "Content-Type": "application/json",
                 "X-Upload-Content-Length": str(taille),
                 "X-Upload-Content-Type": "video/mp4"})
    with urllib.request.urlopen(init, timeout=90) as r:
        session = r.headers.get("Location")
    if not session:
        refus(6, "YouTube n'a pas rendu d'URL d'upload resumable")
    position, vues = 0, []
    with fichier.open("rb") as f:
        while position < taille:
            bloc = f.read(limite)
            if not bloc:
                break
            fin = position + len(bloc) - 1
            req = urllib.request.Request(
                session, data=bloc, method="PUT",
                headers={"Content-Length": str(len(bloc)),
                         "Content-Range": "bytes %d-%d/%d" % (position, fin, taille)})
            with urllib.request.urlopen(req, timeout=300) as r:
                vues.append(r.status)
            position = fin + 1
    return {"id": creneau["id"], "statut": "publie", "octets_envoyes": position,
            "reponses_http": vues}


def mode_publish(args):
    cal = charger_json(args.schedule, "calendrier")
    if cal.get("validated_by_magos") is not True:
        refus(3, "calendrier non signé (validated_by_magos != true) : le projet ne poste pas "
                 "sans la main de l'opérateur")
    maintenant = lire_iso(args.maintenant) if args.maintenant else dt.datetime.now(dt.timezone.utc)
    for c in cal["creneaux"]:
        quand = lire_iso(c["publishAt"])
        if (quand - maintenant).total_seconds() < MIN_H * 3600 and not args.dry_run:
            refus(4, "créneau %s à %s : moins de 4 h d'avance, publication refusée"
                     % (c["id"], c["publishAt"]))
    jeton = None if args.dry_run else jeton_acces()
    dus = [c for c in cal["creneaux"] if lire_iso(c["publishAt"]) <= maintenant] or \
          (cal["creneaux"][:1] if args.dry_run else [])
    if not dus:
        print(json.dumps({"statut": "rien_a_publier",
                          "prochain": cal["creneaux"][0]["publishAt"] if cal["creneaux"] else None,
                          "maintenant": iso(maintenant)}, ensure_ascii=False))
        return 0
    resultats = []
    for c in dus:
        try:
            resultats.append(publier(c, jeton, args.dry_run, args.request_out))
        except urllib.error.HTTPError as e:
            corps = e.read().decode("utf-8", "replace")[:300]
            if e.code == 403 and "quota" in corps.lower():
                print(json.dumps({"statut": "backoff_quota", "creneau": c["id"],
                                  "reculs": ["1 h", "4 h", "12 h"], "detail": corps}))
                return 5
            refus(6, "publication de %s refusée : HTTP %s — %s" % (c["id"], e.code, corps))
    print(json.dumps({"statut": "ok", "resultats": resultats}, ensure_ascii=False))
    if args.ledger:
        led = Path(args.ledger)
        led.parent.mkdir(parents=True, exist_ok=True)
        with led.open("a", encoding="utf-8") as f:
            for r in resultats:
                f.write(json.dumps({**r, "schema": "murus.publication.ledger.v1",
                                    "quand": iso(maintenant)}, ensure_ascii=False) + "\n")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="SF_17_PROGRAMMA — calendrier et publication programmée")
    ap.add_argument("--mode", choices=("plan", "publish"), default="plan")
    ap.add_argument("--pack", default="REVIEW/pack_stage.json")
    ap.add_argument("--elocution", default=None, help="REVIEW/elocution.json (titres de la 2e passe)")
    ap.add_argument("--livrables", default=None)
    ap.add_argument("--manifeste", default=None)
    ap.add_argument("--out", default="REVIEW/schedule.json")
    ap.add_argument("--provenance", default="REVIEW/schedule.provenance.json")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--start", default=None, help="début de session ISO Z (défaut : maintenant)")
    ap.add_argument("--min-heures", type=float, default=MIN_H)
    ap.add_argument("--max-heures", type=float, default=MAX_H)
    ap.add_argument("--schedule", default="REVIEW/schedule.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--maintenant", default=None)
    ap.add_argument("--request-out", default=None)
    ap.add_argument("--ledger", default=None)
    args = ap.parse_args(argv)

    if args.mode == "publish":
        return mode_publish(args)

    pack = charger_json(args.pack, "pack")
    pack_token = pack.get("pack_token")
    metadonnees = {}
    if args.elocution and Path(args.elocution).is_file():
        eloc = charger_json(args.elocution, "elocution")
        for t in eloc.get("titres") or []:
            metadonnees[t["id"]] = {"metadata_title": t.get("metadata_title")}
    clips = inventaire_livrables(args.livrables or "FR_B_CREATION/SF_17_PROGRAMMA/IN",
                                 args.manifeste)
    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(10 ** 9)
    debut = lire_iso(args.start) if args.start else dt.datetime.now(dt.timezone.utc)
    creneaux, tirages = planifier(clips, seed, debut, args.min_heures, args.max_heures, metadonnees)
    cal = ecrire_calendrier(creneaux, seed, args.min_heures, args.max_heures,
                            pack_token, args.out, args.provenance)
    print(json.dumps({"schema": cal["schema"], "seed": seed, "nb_creneaux": len(creneaux),
                      "min_intervalle_h": min(tirages), "max_intervalle_h": max(tirages),
                      "premier": creneaux[0]["publishAt"], "dernier": creneaux[-1]["publishAt"],
                      "signe": cal["validated_by_magos"], "out": args.out}, ensure_ascii=False))
    if args.ledger:
        led = Path(args.ledger)
        led.parent.mkdir(parents=True, exist_ok=True)
        with led.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"schema": "murus.schedule.ledger.v1", "seed": seed,
                                "tirages_h": tirages, "nb_creneaux": len(creneaux),
                                "premier": creneaux[0]["publishAt"],
                                "dernier": creneaux[-1]["publishAt"]}, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""elocution — la seconde passe des métadonnées (SF_06_LIBELLUS, V2).

Position structurelle (PLAN_V2 étape 5) : la sélection est **déjà faite** (M1,
cap 15). Ce module ne touche ni aux moments, ni au nombre de clips, ni au choix :
il ne réécrit que la **formulation** d'un titre déjà décidé, puis le validateur
déterministe re-juge la sortie du modèle. Un titre que le modèle propose mais que
les gabarits refusent n'est **jamais** accepté (T23).

Trois garanties, dans cet ordre :

1. **Le LLM ne décide pas.** Sa sortie repasse `overlay.accept()` — c'est-à-dire
   `libs/title_forge.validate` (mots interdits, CTA, longueur) et `s1_context`
   (noms propres, termes internes, faits inventés). Refus ⇒ nouvelle tentative.
2. **Un siège n'échoue jamais pour un titre.** Après 3 tentatives, repli sur le
   gabarit pur et `elocution_fallback: true` écrit au ledger. Le siège continue.
3. **Chaque appel est tracé.** Modèle, tentatives, jetons consommés, verdict du
   validateur, repli, provenance — dans le rapport rendu.

Clé : `NVIDIA_API_KEY` **uniquement** dans l'environnement. Jamais dans un
fichier, jamais dans un log, jamais dans le rapport (seulement sa présence).

Usage :
  python elocution.py --pack REVIEW/pack_stage.json --out REVIEW/elocution.json \
      [--model meta/llama-3.1-70b-instruct] [--tentatives 3] [--delais 60,300,1500] \
      [--reponses FICHIER.json] [--ledger TRACKING/ELOCUTION_LEDGER.jsonl] [--assets A01,A02]

Codes : 0 toujours, sauf 2 si le pack est illisible (rien à formuler).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LIB = ROOT / "libs"
BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
SCHEMA = "murus.elocution.v1"
GABARIT_LIMITE_MOTS = 4
GABARIT_LIMITE_CHARS = 85
INTERDITS = ("abonne", "abonne-toi", "subscribe", "lien en bio", "clique", "like et",
             "suis-moi", "follow", "partage", "rt si")


def log(msg):
    print("ELOCUTION : %s" % msg)


def refus(code, msg):
    print("ELOCUTION REFUS (%d) : %s" % (code, msg), file=sys.stderr)
    sys.exit(code)


def charger_pack(path):
    p = Path(path)
    if not p.is_file():
        refus(2, "pack introuvable : %s" % p)
    try:
        pack = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        refus(2, "pack illisible : %s" % e)
    if not pack.get("assets"):
        refus(2, "pack sans assets : rien à formuler")
    return pack


def config_validation(pack):
    """Les contraintes viennent du dépôt, jamais d'une valeur inventée ici."""
    cfg = {
        "overlay_max_words": GABARIT_LIMITE_MOTS,
        "overlay_max_chars_per_line": 60,
        "metadata_title_max_chars": GABARIT_LIMITE_CHARS,
        "allowed_question_mark": False,
    }
    for cand in (ROOT / "FR_A_CERVEAU/MARK1/config/selection.json",
                 ROOT / "FR_A_CERVEAU/SF_04_SELECTIO/config/selection.json"):
        if cand.is_file():
            try:
                data = json.loads(cand.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            for cle in ("overlay_max_words", "overlay_max_chars_per_line",
                        "metadata_title_max_chars", "allowed_question_mark"):
                if cle in data:
                    cfg[cle] = data[cle]
            break
    return cfg


def accepter(texte, cfg, langue, sujet, termes, enjeu=True):
    """Le seul juge : les gabarits du dépôt. Pas de juge maison, pas d'exception."""
    if not texte or not str(texte).strip():
        return False, ["titre vide"]
    if len(str(texte).split()) > int(cfg["overlay_max_words"]) + 6:
        return False, ["titre trop long"]
    bas = str(texte).lower()
    for interdit in INTERDITS:
        if interdit in bas:
            return False, ["appel à l'action interdit : %s" % interdit]
    if not cfg.get("allowed_question_mark") and "?" in str(texte):
        return False, ["point d'interrogation interdit"]
    # Le validateur vit dans MARK1 : c'est le seul juge, on ne le réimplémente pas.
    for chemin in (ROOT / "FR_A_CERVEAU/MARK1", ROOT):
        if str(chemin) not in sys.path:
            sys.path.insert(0, str(chemin))
    try:
        from libs import title_forge, s1_context

        viol = list(title_forge.validate(str(texte), cfg, langue))
        if not enjeu:
            # le titre de PUBLICATION est descriptif : l'enjeu est exige sur le
            # titre grave a l'image, pas sur la ligne de metadata.
            viol = [v for v in viol if v != "no_stake"]
        if viol:
            return False, viol
        rep = s1_context.analyse(str(texte), subject=sujet,
                                 internal_terms=termes, lang=langue)
        if rep.get("verdict") != "ok":
            return False, list(rep.get("reasons") or [])
        return True, []
        return True, []
    except Exception as e:                                   # pragma: no cover
        return False, ["validateur indisponible : %s" % str(e)[:120]]


def prompt_de(asset, sujet, langue):
    return (
        "Tu reformules un titre de clip, sans rien inventer.\n"
        "Faits autorisés (les seuls) :\n"
        "- titre actuel : %s\n- titre de publication : %s\n- sujet : %s\n"
        "Règles dures : au plus %d mots pour le titre de clip, au plus %d caractères "
        "pour le titre de publication, aucun appel à l'action, aucun point "
        "d'interrogation, aucun fait absent des faits autorisés, aucun nom propre ajouté.\n"
        "Réponds STRICTEMENT en JSON : {\"titre\": \"...\", \"metadata_title\": \"...\"}\n"
        "Langue : %s."
        % (asset.get("overlay_title") or "", asset.get("metadata_title") or "",
           sujet or "non précisé", GABARIT_LIMITE_MOTS, GABARIT_LIMITE_CHARS, langue)
    )


def appeler_modele(prompt, modele, cle, timeout=90):
    corps = {
        "model": modele,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 400,
        "stream": False,
    }
    req = urllib.request.Request(
        BASE_URL.rstrip("/") + "/chat/completions",
        data=json.dumps(corps).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + cle,
                 "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    message = data["choices"][0]["message"]
    # Certains modeles raisonnent d'abord (reasoning_content) et laissent
    # `content` vide si max_tokens est atteint : on lit les deux, jamais un vide.
    texte = (message.get("content") or "").strip()
    if not texte:
        texte = (message.get("reasoning_content") or "").strip()
    usage = data.get("usage") or {}
    return texte, {"jetons_entree": usage.get("prompt_tokens"),
                   "jetons_sortie": usage.get("completion_tokens"),
                   "jetons_total": usage.get("total_tokens")}


def extraire_json(texte):
    """Le modèle doit rendre du JSON ; on ne devine pas, on refuse."""
    t = texte.strip()
    if t.startswith("```"):
        t = t.split("```")[1] if "```" in t[3:] else t.strip("`")
        t = t.lstrip("json").strip()
    debut, fin = t.find("{"), t.rfind("}")
    if debut < 0 or fin <= debut:
        raise ValueError("pas de JSON dans la réponse")
    return json.loads(t[debut:fin + 1])


def gabarit(asset):
    """Le repli : ce que le moteur déterministe avait déjà produit. Jamais pire."""
    return {
        "titre": (asset.get("overlay_title") or "").strip(),
        "metadata_title": (asset.get("metadata_title") or "").strip(),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="seconde passe des titres, re-jugée par les gabarits")
    ap.add_argument("--pack", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default=os.environ.get("NVIDIA_MODEL", "nvidia/nemotron-3.5-bolt-e4b"))
    ap.add_argument("--tentatives", type=int, default=3)
    ap.add_argument("--delais", default="5,30,120",
                    help="secondes entre tentatives (1re, 2e, 3e) — 0,0,0 pour un test")
    ap.add_argument("--reponses", help="replay hors ligne des réponses du modèle (tests, T23/T24)")
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--assets", default=None)
    ap.add_argument("--langue", default="en")
    ap.add_argument("--budget-secondes", type=float, default=600.0,
                    help="au-dela, les assets restants passent en repli gabarit (declare)")
    args = ap.parse_args(argv)

    pack = charger_pack(args.pack)
    cfg = config_validation(pack)
    sujet = str(pack.get("subject") or pack.get("campaign", {}).get("subject") or "")
    termes = [str(t).lower() for t in (pack.get("internal_terms") or [])]
    assets = pack["assets"]
    if args.assets:
        voulus = {a.strip() for a in args.assets.split(",") if a.strip()}
        assets = [a for a in assets if a.get("id") in voulus]
        if not assets:
            refus(2, "aucun asset demandé n'existe dans le pack")

    replay = None
    if args.reponses:
        replay = json.loads(Path(args.reponses).read_text(encoding="utf-8"))
        log("replay hors ligne : %s (aucun appel réseau)" % args.reponses)

    cle = os.environ.get("NVIDIA_API_KEY", "")
    if not cle and replay is None:
        log("NVIDIA_API_KEY absente : repli gabarit pour tous les titres (déclaré)")

    delais = [float(x) for x in str(args.delais).split(",") if x.strip() != ""]
    resultats, replis, jetons = [], 0, 0

    debut_total = time.monotonic()
    budget_epuise = False
    for asset in assets:
        if args.budget_secondes and (time.monotonic() - debut_total) > args.budget_secondes:
            budget_epuise = True
        prompt = prompt_de(asset, sujet, args.langue)
        essais, verdicts, choisi, source, usage_total = 0, [], None, "gabarit", 0

        while essais < max(1, args.tentatives) and not budget_epuise:
            essais += 1
            try:
                if replay is not None:
                    brut = replay[str(asset["id"])][min(essais - 1, len(replay[str(asset["id"])]) - 1)]
                    brut, usage = brut, {}
                else:
                    if not cle:
                        raise RuntimeError("pas de clé")
                    brut, usage = appeler_modele(prompt, args.model, cle)
                usage_total += int(usage.get("jetons_total") or 0)
                proposition = extraire_json(brut)
                titre = str(proposition.get("titre") or "").strip()
                meta = str(proposition.get("metadata_title") or "").strip()
                ok_titre, viol_titre = accepter(titre, cfg, args.langue, sujet, termes)
                ok_meta, viol_meta = accepter(meta, {**cfg, "overlay_max_words": 40,
                                                   "title_max_words": 25,
                                                   "title_min_words": 1},
                                              args.langue, sujet, termes, enjeu=False)
                verdicts.append({"essai": essais, "titre": titre, "metadata_title": meta,
                                 "accepte": ok_titre and ok_meta,
                                 "violations": viol_titre + viol_meta})
                if not (ok_titre and ok_meta):
                    raise ValueError("refusé par les gabarits : %s" % (viol_titre + viol_meta))
                if len(meta) > int(cfg["metadata_title_max_chars"]):
                    raise ValueError("metadata_title trop long (%d > %d)"
                                     % (len(meta), cfg["metadata_title_max_chars"]))
                choisi = {"titre": titre, "metadata_title": meta}
                source = "elocution"
                break
            except Exception as e:
                message = str(e)[:200]
                verdicts.append({"essai": essais, "erreur": message})
                if essais < max(1, args.tentatives):
                    pause = delais[min(essais - 1, len(delais) - 1)] if delais else 0.0
                    if pause > 0:
                        log("%s essai %d refusé (%s) — nouvelle tentative dans %.0fs"
                            % (asset["id"], essais, message, pause))
                        time.sleep(pause)

        if choisi is None:
            choisi = gabarit(asset)
            replis += 1
            log("%s : repli gabarit (%s)" % (asset["id"], choisi.get("titre") or "sans titre"))
        else:
            log("%s : %r (validé par les gabarits, essai %d)" % (asset["id"], choisi["titre"], essais))

        jetons += usage_total
        resultats.append({
            "id": asset["id"],
            "titre": choisi.get("titre"),
            "metadata_title": choisi.get("metadata_title"),
            "titre_gabarit": gabarit(asset).get("titre"),
            "source": source,
            "essais": essais,
            "elocution_fallback": source != "elocution",
            "jetons": usage_total,
            "verdicts": verdicts,
        })

    rapport = {
        "schema": SCHEMA,
        "pack_token": pack.get("pack_token"),
        "modele": args.model if (cle or replay is not None) else None,
        "cle_presente": bool(cle),
        "replay": bool(replay),
        "assets": len(assets),
        "elocutions": len(resultats) - replis,
        "replis": replis,
        "budget_epuise": budget_epuise,
        "secondes_totales": round(time.monotonic() - debut_total, 1),
        "jetons_total": jetons,
        "regle": "le LLM ne décide jamais : sa sortie est re-jugée par les gabarits du dépôt",
        "titres": resultats,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rapport, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": len(assets), "elocutions": len(resultats) - replis,
                      "replis": replis, "jetons": jetons, "out": str(out)}, ensure_ascii=False))

    if args.ledger:
        led = Path(args.ledger)
        led.parent.mkdir(parents=True, exist_ok=True)
        with led.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "schema": "murus.elocution.ledger.v1",
                "pack_token": pack.get("pack_token"),
                "modele": rapport["modele"],
                "cle_presente": bool(cle),
                "assets": len(assets),
                "elocutions": rapport["elocutions"],
                "replis": replis,
                "jetons_total": jetons,
                "preuve": str(out),
            }, ensure_ascii=False) + "\n")
        log("ledger : %s" % led)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""vive_runner — l'adaptateur headless du moteur vive (SF_12_FABRICA, voie vive).

Rôle doctrinal : FR_B_CREATION ne décide jamais. Ce runner ne choisit aucun
moment, aucun titre, aucun style : il prend les fenêtres **déjà signées** du
pack, les fait couper par le moteur vendé, et rend des fichiers nommés comme
SF_13 les attend (`pur_<id>.mp4`). Aucune décision, aucune retouche.

Ce que le code réel du moteur impose (relevé dans app.py, voir VENDOR.md) :

  POST /export   {id, start, end, layout, captions, aspect, resolution, top,
                  cam{x,y,w,h}, game{x,y,w,h}, caption_style, fps}
                 → job ASYNCHRONE, fichier rendu dans NEONCLIPPING_DATA_DIR
  GET  /status/{job}   état : running | done | error
  POST /make     refuse un direct, grave des sous-titres en dur et n'accepte
                 aucun titre : il n'est donc PAS utilisé ici.
  Ollama         127.0.0.1:11434 en dur dans llm.py/smart.py/vision.py —
                 s'il répond, la doctrine « aucun LLM dans la sélection » est
                 violée : le runner refuse au lieu de continuer en silence.

Ce que ce runner NE fait PAS, volontairement :
  - aucun sous-titre (`captions: false`) : les sous-titres sont ceux de SF_13,
    mot par mot, validés par le codex postprod ;
  - aucun titre, aucun filigrane, aucun glow, aucun LUT, aucun fade : le
    moteur ne grave rien de tout cela (D-5 du PLAN_V2) ;
  - rien qui re-encode après SF_15 : SF_14 (camouflage) reste le seul
    ré-encodeur, en aval, identique pour les deux voies.

Usage :
  python vive_runner.py --pack REVIEW/pack_stage.json --vod <url|fichier>
      --codex-render REVIEW/codex_render.json --codex-postprod REVIEW/codex_postprod.json
      --out FR_B_CREATION/SF_12_FABRICA/vive/OUT
      --report FR_B_CREATION/SF_12_FABRICA/vive/REVIEW/vive_report.json
      [--assets A01,A02] [--port 8770] [--timeout 1800] [--ignore-ollama]
  python vive_runner.py --selfcheck      # contrat seul, sans réseau ni moteur

Codes de sortie : 0 ok · 2 codex non signés · 3 LLM détecté · 4 pack invalide
                  · 5 moteur indisponible · 6 clip manquant ou tronqué
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VENDOR = HERE / "vendor" / "neonclipping"
SCHEMA = "murus.vive_report.v1"

# Ce que le codex demande et que le moteur ne sait pas faire : écrit, jamais tu.
ECARTS_CONNUS = {
    "title": "le moteur n'accepte aucun titre (aucun champ title dans /export) : gravé par SF_12/SF_13",
    "logo": "le moteur ne grave pas de filigrane : appliqué par notre pile (codex_render.logo)",
    "look.degree": "la géométrie du layout du moteur est fixe, la valeur du codex n'est pas transmissible",
    "look.bg_scale": "idem : flou/échelle du fond non paramétrables par /export",
    "look.fg_scale": "idem : échelle du premier plan non paramétrable",
    "look.fg_y_pct": "idem : position verticale du premier plan non paramétrable",
    "glow": "le moteur n'applique aucun glow : c'est PP2 (SF_13), dans l'ordre glow→caption→lut→fade",
    "caption": "les sous-titres du moteur sont désactivés (captions=false) : SF_13 les grave, un mot par cue",
    "lut": "aucun LUT dans le moteur : SF_13 applique hdr_imperator",
    "fade_out": "aucun fade dans le moteur : SF_13 applique le fade sombre 0,6 s",
}

EQUIVALENCES = {
    "canvas": "aspect=vertical, resolution=1080 (9:16 du codex → 1080x1920)",
    "fps": "fps du codex transmis tel quel",
    "style": "style du codex = nom de layout du moteur (blur → layout=blur)",
    "captions": "captions=false imposé : les sous-titres viennent de SF_13",
}


# ───────────────────────────── utilitaires ──────────────────────────────

def die(code, message):
    """Refus bruyant : jamais un silence, jamais un succès déguisé."""
    print("VIVE REFUS (%d) : %s" % (code, message), file=sys.stderr)
    sys.exit(code)


def load_json(path, quoi):
    p = Path(path)
    if not p.is_file():
        die(4, "%s absent : %s" % (quoi, p))
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(4, "%s illisible (%s) : %s" % (quoi, e, p))


def porte_codex(path, cle):
    """G1 s'applique identiquement à la voie vive : pas de codex signé, pas de clip."""
    d = load_json(path, "codex")
    if d.get("validated_by_magos") is not True:
        die(2, "codex non signé (%s) : validated_by_magos != true — aucun rendu sans les deux codex"
               % Path(path).name)
    return d


def port_libre(port):
    s = socket.socket()
    try:
        return s.connect_ex(("127.0.0.1", port)) != 0
    finally:
        s.close()


def http_json(url, payload=None, timeout=60):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", "replace")
    return json.loads(raw) if raw.strip().startswith(("{", "[")) else raw


def ollama_repond(port=11434):
    """La doctrine interdit tout LLM dans la sélection. On le PROUVE, on ne l'espère pas."""
    s = socket.socket()
    s.settimeout(1.0)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def ffprobe_duree(path):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(path)], capture_output=True, text=True, timeout=120)
        return float(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


# ───────────────────────────── le moteur ──────────────────────────────

def demarrer_moteur(port, data_dir, log_path, extra_env=None):
    if not (VENDOR / "app.py").is_file():
        die(5, "moteur vendé absent : %s" % VENDOR)
    if not port_libre(port):
        die(5, "port %d déjà occupé — refus de tuer un processus inconnu" % port)
    env = dict(os.environ)
    env.update({
        "NEONCLIPPING_PORT": str(port),
        "NEONCLIPPING_DATA_DIR": str(data_dir),
        "NEONCLIPPING_NO_AUTOUPDATE": "1",
        "NEONCLIPPING_LLM_MODEL": "",           # aucun LLM cloud
        "NEONCLIPPING_LLM_KEY": "",
        "NEONCLIPPING_LLM_BASE_URL": "",
        "OLLAMA_HOST": "127.0.0.1:1",           # tout appel Ollama échoue immédiatement
    })
    env.update(extra_env or {})
    log = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen([sys.executable, "app.py"], cwd=str(VENDOR), env=env,
                            stdout=log, stderr=subprocess.STDOUT)
    base = "http://127.0.0.1:%d" % port
    limite = time.monotonic() + 180
    while time.monotonic() < limite:
        if proc.poll() is not None:
            log.close()
            queue = Path(log_path).read_text(encoding="utf-8", errors="replace")[-1500:]
            die(5, "le moteur est mort au démarrage :\n%s" % queue)
        try:
            http_json(base + "/readiness", timeout=5)
            return proc, base, log
        except (urllib.error.URLError, OSError, ValueError):
            time.sleep(1.0)
    proc.terminate()
    log.close()
    die(5, "moteur injoignable sur %s après 180 s" % base)


def arreter_moteur(proc, log):
    try:
        if proc.poll() is None:
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill()
    finally:
        log.close()


def telecharger_source(url, dest):
    """Téléchargement via le module yt-dlp du vendor (aucune dépendance nouvelle)."""
    sys.path.insert(0, str(VENDOR))
    try:
        import ytdl  # module vendé
    except Exception as e:                                   # pragma: no cover
        die(5, "module ytdl du vendor inutilisable (yt-dlp absent ?) : %s" % e)
    opts = {"format": "bv*[height<=1080]+ba/b[height<=1080]/b",
            "merge_output_format": "mp4",
            "outtmpl": str(dest.with_suffix("")) + ".%(ext)s"}
    try:
        with ytdl.YDL({"noplaylist": True, "quiet": True, "no_warnings": True,
                       "socket_timeout": 30, "retries": 3, **opts}) as y:
            y.download([url])
    except Exception as e:
        die(5, "téléchargement de la source impossible : %s" % str(e)[-400:])
    for cand in (dest, dest.with_suffix(".mkv"), dest.with_suffix(".webm"), dest.with_suffix(".mp4")):
        if cand.is_file() and cand.stat().st_size > 0:
            if cand != dest:
                shutil.move(str(cand), str(dest))
            return dest
    die(5, "source téléchargée introuvable après yt-dlp : %s" % dest)


def poser_source(vod, data_dir):
    """Le moteur n'exporte que depuis son DATA : on y dépose la source, une fois."""
    data_dir.mkdir(parents=True, exist_ok=True)
    if not vod:
        die(4, "--vod requis (url ou fichier local)")
    src_id = hashlib.sha1(str(vod).encode("utf-8")).hexdigest()[:16]
    dest = data_dir / (src_id + ".mp4")
    if dest.is_file() and dest.stat().st_size > 0:
        return src_id, dest, "deja_present"
    p = Path(vod)
    if p.is_file():
        shutil.copyfile(str(p), str(dest))
        return src_id, dest, "copie_locale"
    if str(vod).startswith(("http://", "https://")):
        telecharger_source(str(vod), dest)
        return src_id, dest, "telechargement"
    die(4, "source introuvable : %s (ni fichier local, ni url)" % vod)


def export_un_clip(base, src_id, asset, layout, fps, timeout):
    """Un clip = une fenêtre signée. Rien d'autre n'est décidé ici."""
    corps = {
        "id": src_id,
        "start": float(asset["start_sec"]),
        "end": float(asset["end_sec"]),
        "layout": layout,
        "captions": False,          # jamais de sous-titres du moteur (SF_13 les grave)
        "caption_style": "clean",   # inutilisé quand captions=false, mais validé par l'API
        "aspect": "vertical",
        "resolution": 1080,
        "top": 0.32,
        "cam": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
        "game": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0},
    }
    if fps:
        corps["fps"] = int(fps)
    job = http_json(base + "/export", corps)["job"]
    limite = time.monotonic() + timeout
    dernier = None
    while time.monotonic() < limite:
        etat = http_json(base + "/status/" + job)
        statut = etat.get("status")
        if statut == "done":
            return job, etat
        if statut == "error":
            die(6, "moteur en erreur sur %s : %s" % (asset["id"], str(etat.get("error"))[:400]))
        dernier = etat.get("message")
        time.sleep(2.0)
    die(6, "délai dépassé (%ss) sur %s (dernier état : %s)" % (timeout, asset["id"], dernier))


# ───────────────────────────── selfcheck ──────────────────────────────

def selfcheck():
    """Contrat seul : aucun réseau, aucun moteur lancé. Ce que la CI peut vérifier."""
    problemes = []
    for requis in ("app.py", "layouts.py", "styling.py", "encoders.py", "ytdl.py",
                   "jobs.py", "captions.py", "LICENSE"):
        if not (VENDOR / requis).is_file():
            problemes.append("vendor incomplet : %s" % requis)
    app = (VENDOR / "app.py").read_text(encoding="utf-8", errors="replace")
    for route in ("@app.post('/export')", "@app.get('/status/{id}')", "@app.post('/upload')"):
        if route not in app:
            problemes.append("endpoint absent du vendor : %s" % route)
    if "'captions':True" not in app:
        problemes.append("le moteur ne grave plus les sous-titres en dur : /make a changé, revoir VENDOR.md")
    if "OLLAMA = 'http://127.0.0.1:11434'" not in (VENDOR / "llm.py").read_text(encoding="utf-8", errors="replace"):
        problemes.append("le point d'appel Ollama a changé : la preuve « sans LLM » doit être revue")
    print("VIVE SELFCHECK : %d problème(s)" % len(problemes))
    for p in problemes:
        print("  - " + p)
    return 0 if not problemes else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="adaptateur headless du moteur vive (aucune décision)")
    ap.add_argument("--selfcheck", action="store_true", help="vérifie le contrat, sans réseau")
    ap.add_argument("--pack")
    ap.add_argument("--vod", help="url de VOD ou fichier local")
    ap.add_argument("--codex-render")
    ap.add_argument("--codex-postprod")
    ap.add_argument("--out", default=str(HERE / "OUT"))
    ap.add_argument("--report", default=str(HERE / "REVIEW" / "vive_report.json"))
    ap.add_argument("--assets", help="sous-ensemble, ex. A01,A02")
    ap.add_argument("--layout", default=None, help="défaut : style du codex render")
    ap.add_argument("--port", type=int, default=8770)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--ignore-ollama", action="store_true",
                    help="dérogation explicite et tracée : un LLM local répond sur 11434")
    args = ap.parse_args(argv)

    if args.selfcheck:
        return selfcheck()

    for requis, nom in ((args.pack, "--pack"), (args.codex_render, "--codex-render"),
                        (args.codex_postprod, "--codex-postprod")):
        if not requis:
            die(4, "%s requis" % nom)

    # 1. G1 : les deux codex signés, sinon rien.
    codex_render = porte_codex(args.codex_render, "codex_render")
    porte_codex(args.codex_postprod, "codex_postprod")

    # 2. le pack : des fenêtres déjà choisies, jamais re-décidées ici.
    pack = load_json(args.pack, "pack")
    assets = pack.get("assets") or []
    if not assets:
        die(4, "pack sans assets : rien à couper")
    if args.assets:
        voulus = {a.strip() for a in args.assets.split(",") if a.strip()}
        assets = [a for a in assets if a.get("id") in voulus]
        if len(assets) != len(voulus):
            die(4, "assets demandés absents du pack : %s" % sorted(voulus))
    for a in assets:
        if not a.get("id") or a.get("start_sec") is None or a.get("end_sec") is None:
            die(4, "asset incomplet dans le pack : %s" % json.dumps(a)[:200])
        if float(a["end_sec"]) <= float(a["start_sec"]):
            die(4, "fenêtre invalide pour %s : %.2f → %.2f" % (a["id"], a["start_sec"], a["end_sec"]))
    if pack.get("pack_token") and codex_render.get("pack_token") \
            and pack["pack_token"] != codex_render["pack_token"]:
        die(4, "le pack (%s) et le codex (%s) ne viennent pas du même pack"
               % (pack["pack_token"], codex_render["pack_token"]))

    # 3. la doctrine : aucun LLM dans la boucle. On prouve, puis on refuse.
    llm_detecte = ollama_repond()
    if llm_detecte and not args.ignore_ollama:
        die(3, "un service LLM répond sur 127.0.0.1:11434 — la sélection doit rester sans LLM "
               "(dérogation explicite requise : --ignore-ollama)")

    layout = args.layout or str(codex_render.get("style") or "blur")
    fps = codex_render.get("fps")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    rapport_path = Path(args.report)
    rapport_path.parent.mkdir(parents=True, exist_ok=True)

    work = HERE / "TRAVAIL"
    data_dir = work / "data"
    log_path = work / "moteur.log"
    work.mkdir(parents=True, exist_ok=True)

    t0 = time.monotonic()
    proc, base, log = demarrer_moteur(args.port, data_dir, log_path)
    clips, refus = [], []
    try:
        src_id, src_path, origine = poser_source(args.vod, data_dir)
        print("VIVE SOURCE : %s (%s, %.1f Mo)" % (src_id, origine, src_path.stat().st_size / 1e6))
        for a in assets:
            debut = time.monotonic()
            job, etat = export_un_clip(base, src_id, a, layout, fps, args.timeout)
            produit = data_dir / ((etat.get("file") or job) + ".mp4")
            if not produit.is_file() or produit.stat().st_size == 0:
                refus.append({"id": a["id"], "motif": "fichier rendu absent : %s" % produit.name})
                print("VIVE REFUS CLIP %s : fichier rendu absent" % a["id"], file=sys.stderr)
                continue
            cible = out_dir / ("pur_%s.mp4" % a["id"])
            shutil.move(str(produit), str(cible))
            attendu = float(a["end_sec"]) - float(a["start_sec"])
            duree = ffprobe_duree(cible) or (etat.get("meta") or {}).get("duration")
            if duree is not None and abs(float(duree) - attendu) > 0.75:
                refus.append({"id": a["id"], "motif": "durée %.2fs contre %.2fs attendus"
                                                   % (float(duree), attendu)})
                cible.unlink(missing_ok=True)
                print("VIVE REFUS CLIP %s : durée %.2fs contre %.2fs" % (a["id"], duree, attendu),
                      file=sys.stderr)
                continue
            clips.append({
                "id": a["id"],
                "fichier": cible.name,
                "octets": cible.stat().st_size,
                "duree_sec": round(float(duree), 3) if duree is not None else None,
                "fenetre": [a["start_sec"], a["end_sec"]],
                "job_moteur": job,
                "secondes_moteur": round(time.monotonic() - debut, 1),
                "encoder": etat.get("encoder"),
                "sous_titres_moteur": False,
            })
            print("VIVE CLIP %s : %s (%.1f Mo, %ss)"
                  % (a["id"], cible.name, cible.stat().st_size / 1e6, round(time.monotonic() - debut, 1)))
    finally:
        arreter_moteur(proc, log)

    log_txt = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
    rapport = {
        "schema": SCHEMA,
        "moteur": {
            "vendor": str(VENDOR.relative_to(ROOT)).replace("\\", "/"),
            "interface": "POST /export + GET /status/{id} (headless, uvicorn)",
            "layout": layout,
            "fps": fps,
            "port": args.port,
            "racine_data": "SF_12_FABRICA/vive/TRAVAIL/data",
        },
        "doctrine": {
            "codex_render_signe": True,
            "codex_postprod_signe": True,
            "aucune_decision_prise_ici": True,
            "llm_detecte": llm_detecte,
            "derogation_llm": bool(args.ignore_ollama and llm_detecte),
            "navigateur_lance": False,
            "sous_titres_du_moteur": False,
            "titre_grave_par_le_moteur": False,
            "ollama_uids_evites": "OLLAMA_HOST=127.0.0.1:1 + NEONCLIPPING_LLM_MODEL vide",
            "appels_ollama_dans_le_log": log_txt.lower().count("ollama"),
        },
        "mapping": {
            "equivalences": EQUIVALENCES,
            "ecarts": ECARTS_CONNUS,
            "applique_ici": ["coupe", "cadrage vertical 9:16", "layout=%s" % layout],
            "applique_plus_tard": ["sous-titres (SF_13)", "titre (SF_12/SF_13)",
                                   "filigrane (notre pile)", "glow (SF_13)",
                                   "lut (SF_13)", "fade (SF_13)", "camouflage (SF_14)",
                                   "luther (SF_15)"],
        },
        "demande": len(assets),
        "rendus": len(clips),
        "refus": refus,
        "secondes_totales": round(time.monotonic() - t0, 1),
        "clips": clips,
    }
    rapport_path.write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
    print("VIVE RAPPORT : %s — %d/%d clips" % (rapport_path, len(clips), len(assets)))
    if refus or len(clips) != len(assets):
        die(6, "%d clip(s) manquant(s) ou refusé(s) : %s"
               % (len(assets) - len(clips), ", ".join(r["id"] + " (" + r["motif"] + ")" for r in refus)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

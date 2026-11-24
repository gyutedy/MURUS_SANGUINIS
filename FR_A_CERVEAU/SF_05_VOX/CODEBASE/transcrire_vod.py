#!/usr/bin/env python3
"""transcrire_vod — la transcription du siège, répartie sur plusieurs VM Modal.

Décision du Warsmith (2026-11-23) : « les transcripts se passent sur Modal, et
si possible sur plusieurs VM pour accélérer ». Ce CLI est l'outil versionné qui
le fait — pas de python inline dans un YAML que personne ne relit (leçon E-18).

Principe :
  1. le runner télécharge l'audio de la VOD (yt-dlp) ;
  2. ffmpeg le découpe en N morceaux de longueur égale, avec recouvrement, et
     chacun part avec son `offset` global ;
  3. `modal.Function.map(...)` envoie les N morceaux EN PARALLÈLE : Modal alloue
     jusqu'à N conteneurs GPU distincts (concurrency_limit=20) ;
  4. les mots reviennent déjà datés en temps VOD (l'offset est appliqué côté GPU) ;
  5. on fusionne, on retire les doublons de recouvrement, on groupe en segments,
     et on écrit le format ARCHIVUM que `transcript_slice.py` sait découper.

Sans jeton Modal (ou sans `modal` installé), le même CLI retombe sur
faster-whisper CPU **et l'écrit** : `mode` et `repli` sont déclarés, jamais
présentés comme du GPU.

Usage :
  python transcrire_vod.py --vod <url|fichier> --out ARCHIVUM/montage/transcripts/v<id>_transcript.json
      [--chunks 8] [--model base.en] [--language en] [--max-minutes 180]
      [--overlap 2.0] [--app perturabo-whisper] [--function transcribe_chunk]
      [--report REPORT.json] [--travail DIR]

Codes : 0 ok · 1 aucune parole transcrite · 2 audio introuvable · 3 outil absent
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCHEMA = "murus.transcript.v1"


def die(code, message):
    print("TRANSCRIPTION REFUS (%d) : %s" % (code, message), file=sys.stderr)
    sys.exit(code)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        die(2, "%s a échoué : %s" % (cmd[0], (r.stderr or r.stdout)[-500:]))
    return r.stdout


def duree(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "csv=p=0", str(path)])
    try:
        return float(out.strip())
    except ValueError:
        die(2, "durée illisible pour %s" % path)


def telecharger_audio(vod, travail):
    """yt-dlp → m4a local. Un fichier local est accepté tel quel."""
    p = Path(vod)
    if p.is_file():
        return p
    if not str(vod).startswith(("http://", "https://")):
        die(2, "source introuvable : %s" % vod)
    sortie = travail / "source.%(ext)s"
    run([sys.executable, "-m", "yt_dlp", "--no-playlist", "-f", "bestaudio/best",
         "-x", "--audio-format", "m4a", "-o", str(sortie), str(vod)])
    for cand in travail.glob("source.*"):
        if cand.is_file() and cand.stat().st_size > 0:
            return cand
    die(2, "yt-dlp n'a produit aucun audio")


def decouper(source, travail, chunks, duree_totale, overlap):
    """N morceaux avec recouvrement ; chacun connaît son début global."""
    morceaux = []
    long = max(1.0, duree_totale / chunks)
    for i in range(chunks):
        debut = max(0.0, i * long - overlap)
        fin = min(duree_totale, (i + 1) * long + overlap)
        if fin <= debut:
            continue
        dest = travail / ("morceau_%02d.m4a" % i)
        run(["ffmpeg", "-y", "-v", "error", "-ss", "%.3f" % debut, "-t", "%.3f" % (fin - debut),
             "-i", str(source), "-vn", "-c:a", "aac", "-b:a", "64k", "-ar", "16000", "-ac", "1",
             str(dest)])
        morceaux.append({"i": i, "debut": debut, "fin": fin, "chemin": dest,
                         "borne": i * long})     # borne = début du coeur du morceau
    return morceaux


def appeler(fn_name, app_name, charge, modele_cpu, langue, vad=True):
    """Modal d'abord ; CPU seulement si Modal est indisponible — et on le dit."""
    t0 = time.monotonic()
    try:
        import modal  # noqa: F401
        if not (os.environ.get("MODAL_TOKEN_ID") and os.environ.get("MODAL_TOKEN_SECRET")):
            raise RuntimeError("MODAL_TOKEN_ID / MODAL_TOKEN_SECRET absents")
        fn = modal.Function.from_name(app_name, fn_name)
        args = [(c["octets"], c["debut"], langue, vad) for c in charge]
        # starmap, pas map : la fonction prend (data, offset, language), et
        # `map` envoyerait le tuple entier dans `data` (bytes-like required).
        try:
            resultats = list(fn.starmap(args))
        except TypeError as e:
            if "positional argument" in str(e) or "positional arguments" in str(e):
                die(3, "le service Modal deploye ne connait pas l'argument `vad` "
                       "(ancienne version en ligne : %s). Redeployer MODAL/transcribe.py. "
                       "Aucun sous-titre n'est produit plutot que des sous-titres faux." % str(e)[:120])
            raise
        conteneurs = {r.get("container") for r in resultats if r.get("container")}
        return resultats, {
            "moteur": "modal-fanout",
            "vm_demandees": len(charge),
            "vm_utilisees": len(conteneurs) or len(charge),
            "secondes": round(time.monotonic() - t0, 1),
        }
    except Exception as e:
        print("TRANSCRIPTION : repli CPU (%s)" % str(e)[:200], file=sys.stderr)
        try:
            from faster_whisper import WhisperModel
        except Exception:
            die(3, "repli CPU impossible : faster_whisper absent sur ce runner. "
                   "Le fan-out Modal a echoue (%s). Rien n'a ete transcrit, "
                   "et on ne fait pas semblant." % str(e)[:160])
        model = WhisperModel(modele_cpu, device="cpu", compute_type="int8")
        resultats = []
        for c in charge:
            segs, _info = model.transcribe(str(c["chemin"]), language=langue or None,
                                           word_timestamps=True, beam_size=5, vad_filter=True)
            mots = []
            for s in segs:
                for w in getattr(s, "words", None) or []:
                    mots.append({"word": w.word, "start": round(w.start + c["debut"], 3),
                                 "end": round(w.end + c["debut"], 3)})
            resultats.append({"words": mots, "offset": c["debut"], "container": ""})
        return resultats, {
            "moteur": "cpu-fallback",
            "vm_demandees": 0,
            "vm_utilisees": 1,
            "secondes": round(time.monotonic() - t0, 1),
            "raison_repli": str(e)[:200],
        }


def fusionner(morceaux, resultats):
    """Recollage : les mots du recouvrement appartiennent au morceau précédent."""
    mots = []
    for morceau, res in zip(morceaux, resultats):
        seuil = morceau["borne"]
        for w in res.get("words") or []:
            texte = str(w.get("word", "")).strip()
            if not texte:
                continue
            debut, fin = float(w["start"]), float(w["end"])
            if morceau["i"] > 0 and debut < seuil:
                continue                       # doublon de recouvrement
            if fin <= debut:
                fin = debut + 0.08
            # format ARCHIVUM : "word" est la cle lue par transcript_slice
            mots.append({"start": round(debut, 3), "end": round(fin, 3),
                         "word": texte, "text": texte})
    mots.sort(key=lambda w: (w["start"], w["end"]))
    propres, dernier_end, dernier_txt = [], -1.0, None
    for w in mots:
        if w["text"] == dernier_txt and w["start"] < dernier_end + 0.05:
            continue                           # répétition exacte à la jointure
        propres.append(w)
        dernier_end, dernier_txt = w["end"], w["text"]
    return propres


def segments_de(mots, pause=0.6, max_mots=12):
    """Segments = ce que transcript_slice attend (start, duration, text, words)."""
    segments, courant = [], []
    for w in mots:
        if courant:
            ecart = w["start"] - courant[-1]["end"]
            if ecart > pause or len(courant) >= max_mots:
                segments.append(courant)
                courant = []
        courant.append(w)
    if courant:
        segments.append(courant)
    sortie = []
    for groupe in segments:
        debut, fin = groupe[0]["start"], groupe[-1]["end"]
        sortie.append({
            "start": round(debut, 3),
            # `end` en plus de `duration` : le graveur de sous-titres lit des fins de
            # segment. Sans `end`, il jetait chaque segment (mesure du 2026-11-24 :
            # 77 mots transcrits, 0 cue grave, "aucun cue exploitable").
            "end": round(fin, 3),
            "duration": round(max(0.01, fin - debut), 3),
            "text": " ".join(g["text"] for g in groupe).strip(),
            # "word" est la cle que lit la decoupe des sous-titres ; "text" reste
            # pour les lecteurs de l'archive.
            "words": [{"start": g["start"], "end": g["end"],
                       "word": g["text"], "text": g["text"]} for g in groupe],
            "word_timing": "measured",
        })
    return sortie


def main(argv=None):
    ap = argparse.ArgumentParser(description="transcription du siège, fan-out Modal (repli CPU déclaré)")
    ap.add_argument("--vod", required=True, help="url de VOD ou fichier audio/vidéo local")
    ap.add_argument("--out", required=True, help="transcript JSON (format ARCHIVUM)")
    ap.add_argument("--chunks", type=int, default=8, help="nombre de morceaux = nombre de VM demandées")
    ap.add_argument("--model", default="base.en", help="modèle en repli CPU")
    ap.add_argument("--language", default="en")
    ap.add_argument("--max-minutes", type=float, default=180.0)
    ap.add_argument("--overlap", type=float, default=2.0, help="recouvrement entre morceaux (s)")
    ap.add_argument("--app", default="perturabo-whisper")
    ap.add_argument("--function", default="transcribe_chunk")
    ap.add_argument("--report", default=None)
    ap.add_argument("--travail", default=None)
    ap.add_argument("--vad", choices=("on", "off"), default="on",
                    help="off = pas de suppression des silences (temps de mots justes, "
                         "obligatoire pour des sous-titres)")
    ap.add_argument("--decaler", type=float, default=0.0,
                    help="ajoute ce decalage a tous les temps (une fenetre transcrite "
                         "seule doit etre ramenee en temps de la VOD)")
    ap.add_argument("--fenetres", default=None,
                    help="JSON [{id, start, end}] : ne transcrire que ces fenetres "
                         "(cout CPU divise par le rapport des durees, sans GPU)")
    args = ap.parse_args(argv)

    for outil in ("ffmpeg", "ffprobe"):
        if shutil.which(outil) is None:
            die(3, "%s absent du runner" % outil)

    travail = Path(args.travail or tempfile.mkdtemp(prefix="murus_transcription_"))
    travail.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()

    audio = telecharger_audio(args.vod, travail)
    total = duree(audio)
    if args.max_minutes and total > args.max_minutes * 60:
        total = args.max_minutes * 60
    if args.fenetres:
        import json as _json
        fen = _json.loads(Path(args.fenetres).read_text(encoding="utf-8"))
        if isinstance(fen, dict):
            fen = fen.get("fenetres") or fen.get("moments") or []
        if not fen:
            die(4, "--fenetres ne contient aucune fenetre")
        morceaux = []
        for i, f in enumerate(fen):
            debut = max(0.0, float(f["start"]) - args.overlap)
            fin = min(total, float(f["end"]) + args.overlap)
            chemin = travail / ("fen_%02d.wav" % i)
            run(["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % debut, "-to", "%.3f" % fin,
                 "-i", str(audio), "-ac", "1", "-ar", "16000", str(chemin)])
            morceaux.append({"chemin": chemin, "debut": debut, "duree": fin - debut,
                             "borne": debut, "id": f.get("id", "F%02d" % i)})
        print("FENETRES : %d fenetres, %.1f s d'audio au total"
              % (len(morceaux), sum(m["duree"] for m in morceaux)), file=sys.stderr)
    else:
        chunks = max(1, min(int(args.chunks), 32))
        morceaux = decouper(audio, travail, chunks, total, args.overlap)
    if not morceaux:
        die(2, "aucun morceau produit (audio vide ?)")

    charge = []
    for m in morceaux:
        charge.append({**m, "octets": m["chemin"].read_bytes()})
    resultats, meta = appeler(args.function, args.app, charge, args.model, args.language,
                              vad=(args.vad == "on"))

    mots = fusionner(morceaux, resultats)
    if args.decaler:
        # une fenetre transcrite seule part de 0 : on la ramene en temps de la VOD
        for m in mots:
            m["start"] = round(m["start"] + args.decaler, 3)
            m["end"] = round(m["end"] + args.decaler, 3)
    segments = segments_de(mots)
    if not segments:
        die(1, "aucune parole transcrite : une transcription vide est un refus, pas un succès")

    import re as _re
    _m = _re.search(r"/videos?/(\d{6,})", str(args.vod))
    vid = _m.group(1) if _m else "unknown"
    texte = " ".join(s["text"] for s in segments)
    transcript = {
        "schema": SCHEMA,
        # ── champs ARCHIVUM (ceux que transcript_slice.py et le siège lisent déjà)
        "video_id": vid,
        "vod_url": str(args.vod),
        "title": "VOD %s" % vid,
        "duration": round(total, 2),
        "transcription_mode": "faster-whisper:%s:%s" % (args.model, meta["moteur"]),
        "transcript": {"text": texte, "segments": segments, "status": "OK",
                       "segment_count": len(segments)},
        # ── champs de la voie V2
        "source": str(args.vod),
        "mode": "faster-whisper:%s:%s" % (args.model, meta["moteur"]),
        "language": args.language,
        "duration_sec": round(total, 2),
        "chunks": len(morceaux),
        "vms": meta["vm_utilisees"],
        "word_timing": "measured",
        "vad": args.vad,
        "decalage_applique_sec": args.decaler,
        "segments": segments,
        # liste plate : n'importe quel lecteur (graveur, siege, archive) trouve les
        # mots sans parcourir les segments
        "words": [{"word": w["word"], "start": w["start"], "end": w["end"]}
                  for sg in segments for w in sg["words"]],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(transcript, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rapport = {
        "schema": "murus.transcription_report.v1",
        "source": str(args.vod),
        "audio_sec": round(total, 2),
        "chunks": len(morceaux),
        "moteur": meta["moteur"],
        "vm_demandees": meta["vm_demandees"],
        "vm_utilisees": meta["vm_utilisees"],
        "secondes_transcription": meta["secondes"],
        "secondes_totales": round(time.monotonic() - t0, 1),
        "mots": len(mots),
        "segments": len(segments),
        "repli": meta.get("raison_repli"),
        "transcript": str(out),
    }
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(rapport, ensure_ascii=False, indent=2) + "\n",
                                     encoding="utf-8")
    print(json.dumps(rapport, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

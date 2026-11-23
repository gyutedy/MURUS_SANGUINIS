#!/usr/bin/env python3
"""
transcript_slice.py — decoupe AUTOMATIQUE de la transcription reelle.
=====================================================================

Probleme resolu (ERRATA E-18)
-----------------------------
La transcription du siege vit dans le depot :
`ARCHIVUM/montage/transcripts/v<vod>_transcript.json`. Elle porte des temps
ABSOLUS de la VOD. Un clip n'est qu'une fenetre de 30 s de cette VOD : si on
donne le transcript entier a la gravure ASS, aucun cue ne tombe dans le clip
et les sous-titres disparaissent. Et si on n'en donne aucun, `postprod.py`
essaie faster-whisper — absent en CI.

Ce fichier existe pour que PERSONNE n'ait a connaitre la combine : la decoupe
est ici, versionnee, testee, documentee. Le workflow ne fait plus de python
inline, il appelle ce CLI.

Contrat
-------
IN  : transcript de la VOD (mots OU segments, avec start/end ou start/duration)
OUT : {"words": [{word, start, end}]} en temps RELATIF au clip (0 = debut clip)

Usage
-----
    python transcript_slice.py --transcript ARCHIVUM/.../v2909800627_transcript.json \
        --start 1376.2 --end 1406.2 --out /tmp/work/pp/transcript_A01.json --id A01

Refus explicites (jamais de sous-titre muet) :
    - transcription absente             -> code 1
    - aucune parole dans la fenetre     -> code 1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def _segments_from(brut: dict) -> list[dict]:
    """Accepte les trois formes reelles du depot (transcript.segments, segments, words)."""
    if isinstance(brut.get("words"), list):
        return [
            {
                "text": str(w.get("word") or ""),
                "start": w.get("start"),
                "end": w.get("end"),
                "duration": w.get("duration"),
            }
            for w in brut["words"]
        ]
    bloc = brut.get("transcript") if isinstance(brut.get("transcript"), dict) else brut
    if isinstance(bloc.get("segments"), list):
        return bloc["segments"]
    return []


def mots_interpoles(texte: str, t0: float, t1: float) -> list[dict]:
    """Un segment sans temps par mot : on repartit sa duree entre ses mots.

    E-19 : un sous-titre doit tomber MOT PAR MOT (motion pop-in, une unite a la
    fois). La transcription du siege ne produisait que des segments de phrase ;
    prendre le segment pour un mot donnait des blocs entiers, tantot longs
    tantot courts. On repartit donc la duree du segment au prorata de la
    longueur des mots — c'est declare `interpolated` dans la sortie, jamais
    presente comme un temps mesure.
    """
    morceaux = [m for m in texte.split() if m]
    if not morceaux:
        return []
    total = max(sum(len(m) + 1 for m in morceaux), 1)
    duree = max(t1 - t0, 0.3)
    mots, curseur = [], t0
    for m in morceaux:
        part = duree * (len(m) + 1) / total
        mots.append({"word": m, "start": round(curseur, 3), "end": round(curseur + part, 3),
                     "word_timing": "interpolated"})
        curseur += part
    return mots


def slice_transcript(segments: list[dict], start: float, end: float) -> list[dict]:
    """Ne garde que la parole de la fenetre, et ramene les temps a zero."""
    if end <= start:
        raise ValueError("fenetre invalide : end <= start")
    mots: list[dict] = []
    for seg in segments:
        t0 = seg.get("start")
        if t0 is None:
            continue
        t0 = float(t0)
        t1 = seg.get("end") or (t0 + float(seg.get("duration") or 0.0))
        t0, t1 = float(t0), float(t1)
        if t1 <= start or t0 >= end:
            continue
        dedans = seg.get("words")
        if isinstance(dedans, list) and dedans:
            # temps par mot REELS (transcription word_timestamps=True)
            for w in dedans:
                ws, we = w.get("start"), w.get("end")
                if ws is None or we is None:
                    continue
                ws, we = float(ws), float(we)
                if we <= start or ws >= end:
                    continue
                mot = str(w.get("word") or "").strip()
                if not mot:
                    continue
                mots.append({"word": mot,
                             "start": round(max(0.0, ws - start), 3),
                             "end": round(min(end - start, max(we - start, 0.05)), 3),
                             "word_timing": "measured"})
            continue
        texte = str(seg.get("text") or seg.get("word") or "").strip()
        if not texte:
            continue
        for w in mots_interpoles(texte, max(t0, start), min(t1, end)):
            w["start"] = round(max(0.0, w["start"] - start), 3)
            w["end"] = round(min(end - start, max(w["end"] - start, 0.05)), 3)
            if w["end"] > w["start"]:
                mots.append(w)
    return mots


def transcript_du_pack(vod_url: str) -> Path:
    """La transcription reelle du depot, deduite de la VOD — sans configuration."""
    videoid = "".join(c for c in vod_url.rstrip("/").split("/")[-1] if c.isdigit())
    if not videoid:
        raise FileNotFoundError("VOD sans identifiant : %s" % vod_url)
    return ROOT / "ARCHIVUM" / "montage" / "transcripts" / ("v%s_transcript.json" % videoid)


def main() -> int:
    ap = argparse.ArgumentParser(description="decoupe de la transcription sur la fenetre d'un clip")
    ap.add_argument("--transcript", type=Path, default=None,
                    help="transcript VOD (defaut : deduit de --vod)")
    ap.add_argument("--vod", default=None, help="URL de la VOD (pour deduire la transcription)")
    ap.add_argument("--start", type=float, required=True, help="debut du clip dans la VOD (s)")
    ap.add_argument("--end", type=float, required=True, help="fin du clip dans la VOD (s)")
    ap.add_argument("--out", type=Path, required=True, help="transcript decale a ecrire")
    ap.add_argument("--id", default="clip", help="identifiant du clip (journal)")
    args = ap.parse_args()

    source = args.transcript
    if source is None:
        if not args.vod:
            print("transcript_slice: fournir --transcript ou --vod", file=sys.stderr)
            return 1
        source = transcript_du_pack(args.vod)
    if not source.is_file():
        print("transcript_slice: transcription reelle absente du depot : %s" % source, file=sys.stderr)
        return 1

    brut = json.loads(source.read_text(encoding="utf-8"))
    segments = _segments_from(brut)
    if not segments:
        print("transcript_slice: aucune parole dans %s" % source, file=sys.stderr)
        return 1

    mots = slice_transcript(segments, args.start, args.end)
    if not mots:
        print(
            "transcript_slice: aucune parole entre %.1fs et %.1fs (%s)"
            % (args.start, args.end, args.id),
            file=sys.stderr,
        )
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "source": str(source.name),
                "clip": args.id,
                "window": {"start": args.start, "end": args.end},
                "relative_time": True,
                "word_timing": sorted({m.get("word_timing", "interpolated") for m in mots}),
                "words": mots,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        "%s : %d segment(s) de parole, %.1fs-%.1fs -> %s"
        % (args.id, len(mots), args.start, args.end, args.out)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""RECUPERER LE CLIP — apres X1, avant les previews. Technique, aucune decision.

CE QUE FAIT CE SCRIPT (et rien d'autre)
    1. prend le pack signe dans EXPORT/ et la VOD du pack ;
    2. telecharge UNIQUEMENT la fenetre du clip choisi (yt-dlp --download-sections) ;
    3. coupe le clip (ffmpeg) -> preview 1 (SF_10_SPECULUM) ;
    4. extrait UNE frame du clip     -> preview 2 (SF_11_LUMEN).

POURQUOI IL EXISTE
    La revue ne peut pas juger un LOOK sans le clip, ni un GLOW sans une frame.
    Avant, ce maillon n'existait pas : la chaine arrivait sur SF_10 sans source et
    le rendu etait soit saute, soit fabrique a la main. Ici le clip recupere est
    exactement la fenetre que M1 a proposee ET que l'operateur a validee.

CE QU'IL NE FAIT PAS
    Aucun style, aucun glow, aucune decision : il ne produit pas de livrable, il
    alimente les DEUX previews. Aucun codex n'est ecrit ici.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREVIEW_1 = ROOT / "FR_B_CREATION/SF_10_SPECULUM/IN"
PREVIEW_2 = ROOT / "FR_B_CREATION/SF_11_LUMEN/IN"


def dernier_pack():
    packs = sorted(glob.glob(str(ROOT / "EXPORT" / "production_pack_mark1_*.json")))
    return Path(packs[-1]) if packs else None


def _run(cmd, **kw):
    print("$", " ".join(str(c) for c in cmd))
    return subprocess.run([str(c) for c in cmd], **kw).returncode


def telecharger(vod, start, duree, work):
    """Telecharge la seule fenetre utile de la VOD (pas la VOD entiere)."""
    work.mkdir(parents=True, exist_ok=True)
    fin = float(start) + float(duree) + 1.0
    cible = work / "src.%(ext)s"
    rc = _run(["yt-dlp", "--no-playlist", "-f", "bv*[height<=1080]+ba/b[height<=1080]",
               "--download-sections", "*%s-%s" % (start, fin),
               # PAS de --force-keyframes-at-cuts : ce drapeau force une image cle
               # AVANT la fenetre, donc le fichier demarre avant l'instant signe et
               # les sous-titres prennent de l'avance. La coupe est de toute facon
               # reencodee ensuite (libx264), donc aucune image cle n'est requise.
               "-o", str(cible), vod])
    if rc != 0:
        return None
    hits = sorted(glob.glob(str(work / "src.*")))
    return Path(hits[0]) if hits else None


def couper(src, out, duree, avance=0.0):
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if avance and avance > 0.01:
        cmd += ["-ss", "%.3f" % avance]
    cmd += ["-i", str(src), "-t", str(duree),
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)]
    return _run(cmd) == 0


def demarrage(src):
    """Instant reel de depart du fichier telecharge, en secondes.

    yt-dlp ecrit un fichier qui peut commencer avant la section demandee : sans ce
    controle, on sous-titre une fenetre et on rend une autre. On mesure, on ne
    suppose pas.
    """
    rc = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=start_time",
                         "-of", "default=nw=1:nk=1", str(src)],
                        capture_output=True, text=True)
    try:
        return float(rc.stdout.strip())
    except ValueError:
        return None


def _duree_ok(clip, duree):
    """Un clip doit durer ce qu'on a demande. Un fichier vide ne part jamais."""
    rc = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                         "-of", "default=nw=1:nk=1", str(clip)],
                        capture_output=True, text=True)
    try:
        d = float(rc.stdout.strip())
    except ValueError:
        print("[RECUP] ECHEC — duree du clip illisible")
        return False
    if d < float(duree) * 0.8:
        print("[RECUP] ECHEC — clip de %.2f s pour %.2f s demandees : il est vide ou tronque"
              % (d, float(duree)))
        return False
    print("[RECUP] duree du clip = %.3f s pour %.3f s demandees" % (d, float(duree)))
    return True


def frame(src, out, at=1.0):
    out.parent.mkdir(parents=True, exist_ok=True)
    return _run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(at), "-i", str(src),
                 "-frames:v", "1", str(out)]) == 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Recupere le clip du pack pour les previews")
    ap.add_argument("--pack", type=Path, default=None)
    ap.add_argument("--index", type=int, default=0, help="index du clip dans le pack")
    ap.add_argument("--vod", default=None, help="URL de la VOD (sinon lue dans le pack)")
    ap.add_argument("--work", type=Path, default=ROOT / "EXPORT" / "RECUP")
    # Mode MATRICE (GitHub Actions) : un job par clip. Chaque job ecrit UN fichier
    # dans --out-dir et n'ecrit pas de frame (la frame appartient a la preview 2).
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="ecrit clip_<asset_id>.mp4 dans ce dossier (mode un job par clip)")
    ap.add_argument("--no-frame", action="store_true", help="ne pas extraire de frame")
    ap.add_argument("--json-out", type=Path, default=None, help="manifest JSON de ce clip")
    a = ap.parse_args()

    pack_path = a.pack or dernier_pack()
    if not pack_path or not Path(pack_path).exists():
        print("[RECUP] ECHEC — aucun pack signe dans EXPORT/ : rien a recuperer.")
        print("[RECUP]         le pack vient de X1_EXPORT (mark1 export), apres les portes FR_A.")
        return 1
    pack = json.loads(Path(pack_path).read_text(encoding="utf-8"))
    assets = pack.get("assets") or []
    if not assets:
        print("[RECUP] ECHEC — pack sans assets :", pack_path)
        return 1
    idx = max(0, min(a.index, len(assets) - 1))
    asset = assets[idx]
    vod = a.vod or (pack.get("source") or {}).get("vod_url") or ""
    if not vod:
        print("[RECUP] ECHEC — aucune VOD dans le pack (source.vod_url) et --vod absent.")
        return 1

    start = float(asset.get("start_sec") or 0)
    end = float(asset.get("end_sec") or (start + 30))
    duree = max(1.0, end - start)
    print("[RECUP] pack=%s clip=%s (%s) %.1fs -> %.1fs"
          % (Path(pack_path).name, asset.get("id"), asset.get("clip_token") or "-", start, end))

    src = telecharger(vod, start, duree, a.work)
    if src is None:
        print("[RECUP] ECHEC — telechargement de la fenetre")

    # La fenetre demandee commence a `start`. Si le fichier telecharge demarre
    # ailleurs, on le dit et on recale : sans ca, on rend une autre fenetre que
    # celle qui a ete signee, et les sous-titres prennent de l'avance.
    # ATTENTION : dans un fichier de section, les horodatages repartent de 0. Un
    # depart lu a 0 ne dit donc RIEN sur la position reelle. On n'utilise la mesure
    # que si elle ressemble a un horodatage global (proche de la fenetre demandee) ;
    # sinon on coupe a zero. Le 2026-11-24, un depart lu a 0.000 a fait avancer la
    # coupe de 1376 s dans un fichier de 31 s : clip vide, Remotion refuse de le lire.
    avance = 0.0
    depart = demarrage(src) if src else None
    if depart is not None and (start - 5.0) < depart < (start - 0.01):
        avance = start - depart
        print("[RECUP] le fichier telecharge commence a %.3f s, la fenetre a %.3f s : "
              "on avance de %.3f s" % (depart, start, avance))
    else:
        print("[RECUP] depart mesure = %s : horodatages locaux, on coupe a zero "
              "(la section est deja calee sur %.3f s)" % (depart, start))
    if src is None:
        print("[RECUP] ECHEC — telechargement de la fenetre impossible (VOD privee/expiree ?)")
        return 1

    if a.out_dir:
        a.out_dir.mkdir(parents=True, exist_ok=True)
        # La review LOOK (SF_10) cherche clips/pur_<angle_id>.mp4 :
        # clipFileCandidates() = [pur_<id>.mp4, <id>_look.mp4, <id>.mp4].
        # On ecrit donc le PREMIER nom attendu, sinon la page reste noire.
        clip = a.out_dir / ("pur_%s.mp4" % (asset.get("id") or idx))
        if not couper(src, clip, duree, avance) or not _duree_ok(clip, duree):
            print("[RECUP] ECHEC — coupe ffmpeg")
            return 1
        print("[RECUP] clip ->", clip)
        if a.json_out:
            a.json_out.parent.mkdir(parents=True, exist_ok=True)
            a.json_out.write_text(json.dumps({
                "asset_id": asset.get("id"), "start_sec": start, "end_sec": end,
                "clip": clip.name, "vod": vod,
            }, indent=2), encoding="utf-8")
        return 0

    clip = PREVIEW_1 / "clip.mp4"
    if not couper(src, clip, duree, avance) or not _duree_ok(clip, duree):
        print("[RECUP] ECHEC — coupe ffmpeg")
        return 1
    prev = PREVIEW_2 / "frame.png"
    if a.no_frame:
        print("[RECUP] clip ->", clip, "(frame non demandee)")
        return 0
    if not frame(clip, prev):
        print("[RECUP] ECHEC — extraction de la frame")
        return 1

    manifest = {
        "clip": str(clip.relative_to(ROOT)),
        "frame": str(prev.relative_to(ROOT)),
        "pack": str(Path(pack_path).relative_to(ROOT)),
        "asset_id": asset.get("id"),
        "clip_token": asset.get("clip_token"),
        "start_sec": start,
        "end_sec": end,
        "vod": vod,
    }
    out = ROOT / "EXPORT" / "RECUP" / "clip_recupere.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[RECUP] clip   ->", clip)
    print("[RECUP] frame  ->", prev)
    print("[RECUP] manifest ->", out)
    print("[RECUP] les DEUX previews peuvent tourner. Aucun codex ecrit ici.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

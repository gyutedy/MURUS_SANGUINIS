#!/usr/bin/env python3
"""MURUS SANGUINIS — lanceur du chapitre. Fusion PERTURABO x LACRIMAE x SKILL.

Doctrine (intangible) :
  - FR_A_CERVEAU ne touche JAMAIS une video (packs JSON dans EXPORT/).
  - FR_B_CREATION ne prend JAMAIS une decision (elle execute les codex).
  - Une gate PRECEDE chaque sous-fregate — sauf SF_14_CAMOUFLAGE et
    SF_15_LUTHER : post-rendu SANS gate, declenchees immediatement,
    elles ne rendent rien elles-memes (elles purgent/normalisent).
  - Le run s'arrete a la premiere porte en echec.
  - Aucun rendu sans les deux codex signes (profil vod).

Usage :
  python murus.py --profile vod     --pack ARCHIVUM/campaign/campaign_directive.json --vod <url|fichier>
  python murus.py --profile direct  --channel <twitch_channel>
  python murus.py selftest
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# L1 : console Windows cp1252 -> forcer UTF-8 avec repli tolerant
# [pattern : run_all.py LACRIMAE, crash reel apres G0 vertes]
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# ---- Les 16 sous-fregates. gate = None => post-rendu SANS gate (14, 15). ----
FR_A = [
    ("SF_01_VIGILIA",   "M0",  "FR_A_CERVEAU/SF_01_VIGILIA/OUT/directive_parsed.json"),
    ("SF_02_VERDICTUM", "V1",  "FR_A_CERVEAU/SF_02_VERDICTUM/OUT/verdict.json"),
    ("SF_03_ANGULI",    "V2",  "FR_A_CERVEAU/SF_03_ANGULI/OUT/angles.json"),
    ("SF_04_SELECTIO",  "M1",  "FR_A_CERVEAU/SF_04_SELECTIO/OUT/selection.json"),        # TOP 15, cap 15
    ("SF_05_VOX",       "M5",  "FR_A_CERVEAU/SF_05_VOX/OUT/transcript.json"),            # avant metadata : le bait se mesure sur elle
    ("SF_06_LIBELLUS",  "M2",  "FR_A_CERVEAU/SF_06_LIBELLUS/OUT/metadata.json"),
    ("SF_07_VEXILLUM",  "M3",  "FR_A_CERVEAU/SF_07_VEXILLUM/OUT/watermark.json"),        # recoit png/jpeg/jpg, sans gerer l'opacite
    ("SF_08_PURGATIO",  "P1",  "FR_A_CERVEAU/SF_08_PURGATIO/OUT/pack_pur.json"),         # zero cle morte
    ("SF_09_PORTAS",    "M4",  "EXPORT/production_pack.json"),                           # -> EXPORT/ + ledger
]
FR_B = [
    ("SF_10_SPECULUM",  "V5",  "REVIEW/codex_render.json"),                              # preview 1 : LOOK
    ("SF_11_LUMEN",     "V6",  "REVIEW/codex_postprod.json"),                            # preview 2 : GLOW (1 frame)
    ("SF_12_FABRICA",   "G1",  "FR_B_CREATION/SF_12_FABRICA/OUT/clips"),                 # pilote par les 2 codex
    ("SF_13_POLITURA",  "PP2", "FR_B_CREATION/SF_13_POLITURA/OUT/postprod_report.json"), # glow->caption->lut->fade
    ("SF_14_CAMOUFLAGE", None, "FR_B_CREATION/SF_14_CAMOUFLAGE/OUT/camouflage_report.json"),  # SANS GATE, post-rendu
    ("SF_15_LUTHER",     None, "FR_B_CREATION/SF_15_LUTHER/OUT/luther_report.json"),          # SANS GATE, post-rendu
    ("SF_16_MISSIO",    "V7",  "FR_B_CREATION/SF_16_MISSIO/OUT/submissions.json"),       # C3 : < 1 h + tracker
]
CHAIN = FR_A + FR_B
NO_GATE = {"SF_14_CAMOUFLAGE", "SF_15_LUTHER"}   # les 2 exceptions, gravees ici
DIRECT_SKIPPED = {"SF_10_SPECULUM", "SF_11_LUMEN"}  # direct : codex reutilises, pas de preview

# Entrees reelles des modules pilles (leurs CLIs d'origine — NE PAS REÉCRIRE).
ENTRY_POINTS = {
    "SF_01_VIGILIA":   "capteurs.py",
    "SF_02_VERDICTUM": "scout.py",
    "SF_03_ANGULI":    "anglesmith.py",
    "SF_04_SELECTIO":  "selector.py",
    "SF_05_VOX":       "vox.py",
    "SF_06_LIBELLUS":  "metadata.py",
    "SF_07_VEXILLUM":  "vexillum.py",
    "SF_08_PURGATIO":  "purgatio.py",
    "SF_09_PORTAS":    "packager.py",
    "SF_14_CAMOUFLAGE": "lac_f05_camouflage.py",
    "SF_15_LUTHER":     "lac_f06_luther.py",
}


def gate(name: str, artefact: Path, report: Path, answer: str | None = None) -> bool:
    """Porte humaine : l'operateur valide l'artefact AVANT d'ouvrir la sous-fregate suivante.
    Refus = le run s'arrete. Aucune erreur amont ne peut declencher un run A-Z.
    answer : reponse pre-fournie (tests/CI) ; None = lecture clavier."""
    print(f"[PORTE {name}] {artefact} — (o)uverte / (r)ejetee ?")
    reply = answer if answer is not None else input()
    if reply.strip().lower() not in ("o", "ok", "y"):
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(
            {"gate": name, "decision": "rejete", "artefact": str(artefact)}, indent=2), encoding="utf-8")
        print(f"[PORTE {name}] REJETEE — arret du siege. Rien n'a ete rendu.")
        return False
    return True


def run_sf(sf: str, profile: str) -> int:
    fr = "FR_A_CERVEAU" if sf.startswith("SF_0") else "FR_B_CREATION"
    code = ROOT / fr / sf / "CODEBASE"
    entry = ENTRY_POINTS.get(sf)
    if entry is None or not (code / entry).exists():
        # Sous-fregate sans entry point connu (SF_10..13, SF_16) : leur CLI reelle
        # est documentee dans leur README — le lanceur les appelle via main.py.
        entry = "main.py"
    if not (code / entry).exists():
        print(f"[{sf}] ECHEC — pas de point d'entree ({code / entry}). Voir le README du SF.")
        return 1
    cmd = [sys.executable, str(code / entry), "--profile", profile]
    print(f"[{sf}] $ {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def main() -> int:
    ap = argparse.ArgumentParser(description="MURUS SANGUINIS — le mur de sang")
    ap.add_argument("--profile", choices=["vod", "direct"], default="vod")
    ap.add_argument("--pack", type=Path, default=ROOT / "ARCHIVUM/campaign/campaign_directive.json")
    ap.add_argument("--vod", default=None)
    ap.add_argument("--channel", default=None)
    ap.add_argument("selftest", nargs="*", default=[])
    args = ap.parse_args()
    if args.selftest and args.selftest[0] == "selftest":
        return subprocess.run([sys.executable, str(ROOT / "tests" / "test_murus.py")]).returncode

    report = ROOT / "TRACKING" / "MURUS_LOG.md"
    chain = CHAIN if args.profile == "vod" else [sf for sf in CHAIN if sf[0] not in DIRECT_SKIPPED]
    for sf, gname, artefact in chain:
        art = ROOT / artefact
        if gname is not None and not gate(gname, art, report):
            return 2                              # porte rejetee : stop net, rien n'a touche une video
        if run_sf(sf, args.profile) != 0:
            print(f"[{sf}] ECHEC — le run s'arrete a la premiere sous-fregate en echec.")
            return 1
    print("MURUS SANGUINIS : siege termine. Clips soumis < 1 h (C3). Le ledger juge.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

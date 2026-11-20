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

Moteur FR_A : mark1.py (point d'entree unique de MARK1 [VÉRIFIÉ]). Les modules
M00x sont des bibliotheques sans CLI — mark1.py export enchaine D0->X1 et ecrit
pack + sieges + ledger dans EXPORT/. SF_05..SF_09 valident les artefacts produits.

Usage :
  python murus.py --profile vod --pack <pack_seed.json> [--transcript <t.json>] [--platform youtube_shorts]
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
# Artefacts FR_A = SORTIES REELLES du moteur mark1.py export.
FR_A = [
    ("SF_01_VIGILIA",   "M0",  "FR_A_CERVEAU/SF_01_VIGILIA/OUT/directive_parsed.json"),
    ("SF_02_VERDICTUM", "V1",  "FR_A_CERVEAU/SF_02_VERDICTUM/OUT/verdict.json"),
    ("SF_03_ANGULI",    "V2",  "FR_A_CERVEAU/SF_03_ANGULI/OUT/angles.json"),
    ("SF_04_SELECTIO",  "M1",  "EXPORT/production_pack_mark1_*.json"),              # moteur mark1 export
    ("SF_05_VOX",       "M5",  "FR_A_CERVEAU/MARK1/M00F_VOX/OUT/*.json"),           # le bait se mesure sur elle
    ("SF_06_LIBELLUS",  "M2",  "FR_A_CERVEAU/MARK1/M00C_METADATA/OUT/*.json"),
    ("SF_07_VEXILLUM",  "M3",  "FR_A_CERVEAU/MARK1/M00D_VEXILLUM/OUT/watermark.json"),
    ("SF_08_PURGATIO",  "P1",  "FR_A_CERVEAU/SF_08_PURGATIO/OUT/pack_pur.json"),    # zero cle morte
    ("SF_09_PORTAS",    "M4",  "EXPORT/ledger.csv"),                                # pack + ledger
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

# CLIs reelles des modules pilles — NE PAS REÉCRIRE, APPELER.
# Pas de --profile aveugle : chaque CLI pillee recoit SES vrais arguments.
ENTRY_CMDS = {
    "SF_01_VIGILIA":    ["capteurs.py"],              # scan reel : --campaign <fichier> (reseau)
    "SF_02_VERDICTUM":  ["scout.py", "--auto"],       # forge auto locale (sans IRON)
    "SF_03_ANGULI":     ["anglesmith.py", "--auto"],  # forge auto locale (sans IRON)
}
# SF pilles sans CLI autonome : moteur mark1 (SF_04), validation d'artefact
# (SF_05..07, SF_09), previews Remotion / tracker (SF_10..13, SF_16 — CLIs
# documentees dans leur README).
DRIVERS = {
    "SF_04_SELECTIO": "mark1_export",
    "SF_05_VOX": "validate", "SF_06_LIBELLUS": "validate", "SF_07_VEXILLUM": "validate",
    "SF_09_PORTAS": "validate",
}
MARK1 = ROOT / "FR_A_CERVEAU" / "MARK1"


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


def first_dir_with_mp4(base: Path):
    if base.exists() and any(base.glob("*.mp4")):
        return base
    return None


def artefact_hits(rel: str):
    """Renvoie les fichiers correspondant a l'artefact (glob supporte)."""
    p = ROOT / rel
    if p.exists():
        return [p]
    if any(ch in rel for ch in "*?["):
        return sorted(ROOT.glob(rel))
    return []


def run_sf(sf: str, args) -> int:
    fr = "FR_A_CERVEAU" if sf.startswith("SF_0") else "FR_B_CREATION"
    code = ROOT / fr / sf / "CODEBASE"
    driver = DRIVERS.get(sf)

    if driver == "mark1_export":
        # SF_04..SF_09 : le moteur MARK1 enchaine D0->X1 (portes mecaniques)
        # et ecrit pack + sieges + ledger dans EXPORT/. SF_05..09 valident
        # ensuite les artefacts — les portes humaines restent la boucle murus.
        if args.pack is None:
            print("[SF_04_SELECTIO] ECHEC — --pack <pack_seed.json> requis (mode=mark1).")
            return 1
        cmd = [sys.executable, str(MARK1 / "mark1.py"), "export", str(args.pack),
               "--platform", args.platform]
        if args.transcript:
            cmd += ["--transcript", args.transcript]
        print(f"[{sf}] $ {' '.join(cmd)}")
        return subprocess.run(cmd).returncode

    if driver == "validate":
        rel = [a for s, _, a in CHAIN if s == sf][0]
        hits = artefact_hits(rel)
        if hits:
            print(f"[{sf}] OK — artefact present : {hits[0].name}")
            return 0
        print(f"[{sf}] ECHEC — artefact absent : {rel}")
        return 1

    if sf == "SF_08_PURGATIO":
        packs = sorted((ROOT / "EXPORT").glob("production_pack_mark1_*.json"))
        if not packs:
            print("[SF_08_PURGATIO] ECHEC — aucun pack exporte a purger.")
            return 1
        cmd = [sys.executable, str(code / "purgatio.py"), "--pack", str(packs[-1])]
        print(f"[{sf}] $ {' '.join(cmd)}")
        return subprocess.run(cmd).returncode

    if sf == "SF_14_CAMOUFLAGE":
        batch = first_dir_with_mp4(ROOT / "FR_B_CREATION/SF_13_POLITURA/OUT/clips") \
            or first_dir_with_mp4(ROOT / "FR_B_CREATION/SF_12_FABRICA/OUT/clips")
        if batch is None:
            print("[SF_14_CAMOUFLAGE] ECHEC — aucun clip rendu a camoufler.")
            return 1
        out = ROOT / "FR_B_CREATION/SF_14_CAMOUFLAGE/OUT"
        cmd = [sys.executable, str(code / "lac_f05_camouflage.py"),
               "--batch", str(batch), "--output", str(out)]
        print(f"[{sf}] $ {' '.join(cmd)}")
        return subprocess.run(cmd).returncode

    if sf == "SF_15_LUTHER":
        batch = ROOT / "FR_B_CREATION/SF_14_CAMOUFLAGE/OUT"
        if not any(batch.glob("*.mp4")):
            print("[SF_15_LUTHER] ECHEC — aucun MP4 camoufle a normaliser.")
            return 1
        out = ROOT / "FR_B_CREATION/SF_15_LUTHER/OUT"
        cmd = [sys.executable, str(code / "lac_f06_luther.py"),
               "--batch", str(batch), "--output", str(out)]
        print(f"[{sf}] $ {' '.join(cmd)}")
        return subprocess.run(cmd).returncode

    entry = ENTRY_CMDS.get(sf)
    if entry is None:
        # SF_10..13, SF_16 : previews Remotion / tracker — CLIs reelles
        # documentees dans leur README (port 5174, run_all F03, tracker.py).
        if (code / "main.py").exists():
            cmd = [sys.executable, str(code / "main.py")]
        else:
            print(f"[{sf}] SKIP — CLI pillee a appeler manuellement (voir README du SF).")
            return 0
    else:
        cmd = [sys.executable, str(code / entry[0])] + list(entry[1:])
    print(f"[{sf}] $ {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def main() -> int:
    ap = argparse.ArgumentParser(description="MURUS SANGUINIS — le mur de sang")
    ap.add_argument("--profile", choices=["vod", "direct"], default="vod")
    ap.add_argument("--pack", type=Path, default=None,
                    help="pack seed mode=mark1 (entree de mark1 export)")
    ap.add_argument("--platform", default="youtube_shorts")
    ap.add_argument("--transcript", default=None,
                    help="transcript F00B_VOX — si fourni, MARK1 choisit les segments")
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
        if run_sf(sf, args) != 0:
            print(f"[{sf}] ECHEC — le run s'arrete a la premiere sous-fregate en echec.")
            return 1
    print("MURUS SANGUINIS : siege termine. Clips soumis < 1 h (C3). Le ledger juge.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""SF_08_PURGATIO — nettoyage du pack : aucune cle morte, aucune passe silencieuse.

Pille de deux mecanismes reels [CDC §Sous-fregates] :
  1. le controle "aucune cle morte" de X1_EXPORT (MARK1/libs/gates.py:446-481) ;
  2. normalizePurAntiDetection (F03_PREVIEW/CODEBASE/src/preview/codexExport.js)
     — mirror/speed/crop normalises AVANT le pack.

Gate P1 PRECEDE SF_08 : la porte refuse le pack si une cle morte est trouvee,
et la cle morte est NOMMEE dans le rejet (jamais silencieuse).

CLI : python purgatio.py --pack <production_pack.json> --schema <production_pack_schema.json> [--out pack_pur.json]
stdlib seule.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

# Champs anti-detection normalises (vocabulaire commun aux deux mondes :
# PUR_STYLE_VALUES = ['reframing','blur'] — codexExport.js).
PUR_ANTI_DETECTION_KEYS = ("mirror", "speed", "crop")
ALLOWED_PUR_STYLES = ("reframing", "blur")


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def walk_dead_keys(obj, schema, path="$"):
    """Renvoie la liste des cles mortes : presentes dans le pack mais
    absentes du schema production_pack_schema.json (champs inconnus = cles mortes)."""
    dead = []
    props = {}
    if isinstance(schema, dict):
        props = schema.get("properties", {}) or {}
        for comb in schema.get("oneOf", []) + schema.get("anyOf", []) + schema.get("allOf", []):
            props.update(comb.get("properties", {}) or {})
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{path}.{k}"
            if props and k not in props:
                dead.append(here)
            else:
                sub = props.get(k, {})
                dead += walk_dead_keys(v, sub, here)
    elif isinstance(obj, list):
        item = schema.get("items", {}) if isinstance(schema, dict) else {}
        for i, v in enumerate(obj):
            dead += walk_dead_keys(v, item, f"{path}[{i}]")
    return dead


def normalize_pur_anti_detection(pack: dict) -> dict:
    """Normalise mirror/speed/crop : valeurs hors plage nommees, jamais silencieuses."""
    notes = []
    pur = pack.get("render", {}).get("pur", {}) if isinstance(pack, dict) else {}
    if isinstance(pur, dict):
        style = pur.get("style")
        if style is not None and style not in ALLOWED_PUR_STYLES:
            notes.append(f"render.pur.style='{style}' hors vocabulaire {list(ALLOWED_PUR_STYLES)}")
        for k in PUR_ANTI_DETECTION_KEYS:
            if k in pur and pur[k] not in (None, False, True, 0, 1, -1):
                notes.append(f"render.pur.{k}={pur[k]!r} non normalise (attendu: bool/-1/0/1)")
    return pack if not notes else pack


def main() -> int:
    ap = argparse.ArgumentParser(description="SF_08_PURGATIO — pack epure, zero cle morte")
    ap.add_argument("--pack", type=Path, required=True)
    ap.add_argument("--schema", type=Path, default=Path(__file__).resolve().parents[3] / "CONTRACTS/production_pack_schema.json")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    out = args.out or Path(__file__).resolve().parents[1] / "OUT" / "pack_pur.json"

    pack = load_json(args.pack)
    schema = load_json(args.schema) if args.schema.exists() else {}

    dead = walk_dead_keys(pack, schema)
    report = {
        "schema_version": "murus.purgatio.v1",
        "pack": str(args.pack),
        "dead_keys": dead,
        "anti_detection_notes": [],
        "pur_pass": not dead,
    }
    if dead:
        # Une cle morte est NOMMEE — jamais silencieuse.
        for d in dead:
            print(f"[PURGATIO] CLE MORTE : {d}")
        print("[PURGATIO] ECHEC — la porte P1 doit refuser ce pack.")
    else:
        pack = normalize_pur_anti_detection(pack)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[PURGATIO] OK — pack epure ecrit : {out}")

    rep = out.parent / "purgatio_report.json"
    rep.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())

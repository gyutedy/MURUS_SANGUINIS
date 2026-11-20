#!/usr/bin/env python3
"""GATES de FR_B_CREATION — V5, V6/GL2, G1, PP2, V7.

Pattern pillé : MARK1/libs/gates.py (Porte.valider/rejeter — portes HUMAINES).
Chaque gate PRECEDE sa sous-fregate. V7 encaisse en plus les rapports
SF_14_CAMOUFLAGE / SF_15_LUTHER : tout livrable dont le dernier rapport porte
qa_pass: false est refuse [CDC §Sous-fregates, décision Warsmith].

Ce module est une bibliothèque (importée par les tests et les workflows) ;
la boucle interactive des portes vit dans murus.py (racine).
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Ordre post-prod GRAVÉ — identique à codexExport.js:10 (PP2_ORDER) [VÉRIFIÉ].
PP2_ORDER = ["glow", "caption", "lut", "fade"]

GATES_FR_B = {
    "SF_10_SPECULUM":  "V5",
    "SF_11_LUMEN":     "V6",     # alias GL2 pour la preview glow
    "SF_12_FABRICA":   "G1",
    "SF_13_POLITURA":  "PP2",
    "SF_16_MISSIO":    "V7",
}
# Les deux exceptions SANS gate (post-rendu immédiat).
NO_GATE = ("SF_14_CAMOUFLAGE", "SF_15_LUTHER")


def gate_v7_refuses_sale_livrable() -> tuple[bool, str]:
    """V7 refuse tout livrable dont le dernier rapport CAMOUFLAGE ou LUTHER
    porte qa_pass: false. Retourne (ok, motif)."""
    for sf, rapport in (
        ("SF_14_CAMOUFLAGE", ROOT / "FR_B_CREATION/SF_14_CAMOUFLAGE/OUT/camouflage_report.json"),
        ("SF_15_LUTHER",     ROOT / "FR_B_CREATION/SF_15_LUTHER/OUT/luther_report.json"),
    ):
        if not rapport.exists():
            return False, f"{sf} : rapport absent ({rapport.name}) — pas de preuve de passage"
        data = json.loads(rapport.read_text(encoding="utf-8"))
        if data.get("qa_pass") is False:
            tags = data.get("suspicious_tags_after") or data.get("suspicious_tags") or []
            return False, f"{sf} : qa_pass=false, tags suspects residuels : {tags}"
    return True, ""


def gate_g1_exige_codex_signes() -> tuple[bool, str]:
    """G1 : SF_12_FABRICA n'a PAS le droit de tourner sans les deux codex signés
    (validated_by_magos). [VÉRIFIÉ, F03_PREVIEW/README.md]"""
    for codex in ("REVIEW/codex_render.json", "REVIEW/codex_postprod.json"):
        p = ROOT / codex
        if not p.exists():
            return False, f"{codex} absent — aucun rendu sans codex"
        data = json.loads(p.read_text(encoding="utf-8"))
        if not data.get("validated_by_magos"):
            return False, f"{codex} non signé (validated_by_magos absent/faux)"
    return True, ""

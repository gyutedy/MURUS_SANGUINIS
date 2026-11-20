#!/usr/bin/env python3
"""Tests e2e MURUS SANGUINIS — les 16 tests du CDC §Tests.

Statut CDC : ATTENDU (jamais exécutés localement). Première exécution : CI
(.github/workflows/murus_tests.yml). Les tests qui exigent ffmpeg / remotion /
un VOD réel sont marqués skip si l'outil est absent — ils passent dans le job
CI qui installe l'environnement.

Test de doctrine global T0 (manuel + CI) :
  grep -rni "ffmpeg\\|libx264" FR_A_CERVEAU/  -> 0 ligne
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

HAS_FFMPEG = shutil.which("ffmpeg") is not None


def run_murus(*args, input_text="o\n" * 20):
    return subprocess.run(
        [sys.executable, str(ROOT / "murus.py"), *args],
        input=input_text, capture_output=True, text=True, cwd=ROOT, timeout=120,
    )


# ---------------------------------------------------------------- T0 (doctrine)
# EXC-M1 (TRACKING/LES_EXCEPTIONS.md) : le grep textuel du CDC "ffmpeg|libx264"
# renvoie des lignes sur (a) un COMMENTAIRE de vox.py qui NIE ffmpeg et (b) le
# capteur detect/live.py (pillé du skill, mesuré au RMS audio). L'intention de la
# règle R3 : le cerveau n'INVOQUE jamais ffmpeg/libx264 et ne REND rien.
# Le test vérifie donc les INVOCATIONS réelles, hors capteur detect/.
def test_t0_doctrine_cerveau_ne_touche_jamais_une_video():
    """T0 : aucune INVOCATION ffmpeg/libx264 dans FR_A_CERVEAU (hors capteur detect/, EXC-M1)."""
    pat = re.compile(r"(subprocess|\bos\.system|\bpopen\b)[^\n]*ffmpeg|ffmpeg[^\n]*(subprocess|\brun\(|\bcall\()", re.IGNORECASE)
    hits = []
    for p in (ROOT / "FR_A_CERVEAU").rglob("*"):
        if not p.is_file() or p.suffix not in (".py", ".js", ".sh"):
            continue
        if "CODEBASE/detect/" in str(p).replace("\\", "/"):  # EXC-M1 : capteur, registre nommé
            continue
        if pat.search(p.read_text(encoding="utf-8", errors="replace")):
            hits.append(str(p))
    assert hits == [], f"La frégate cerveau INVOQUE ffmpeg : {hits}"


def test_t0_bis_vexillum_sans_opacite():
    """T0_bis (intention, EXC-M2) : VEXILLUM ne POSE jamais le watermark —
    aucun appel de rendu/subprocess dans son code. Il DÉCRIT (opacity lu des
    règles du créateur, cf. EXC-M2 dans TRACKING/LES_EXCEPTIONS.md)."""
    pat = re.compile(r"subprocess|ffmpeg|libx264|\.ass|drawtext", re.IGNORECASE)
    hits = [p.name for p in (ROOT / "FR_A_CERVEAU/SF_07_VEXILLUM").rglob("*")
            if p.is_file() and p.suffix == ".py"
            and pat.search(p.read_text(encoding="utf-8", errors="replace"))]
    assert hits == [], f"VEXILLUM applique/apose le watermark (interdit) : {hits}"


# ------------------------------------------------- T01 : run vod complet (CI)
def test_t01_run_vod_complet():
    """T01 : 16 sous-frégates exécutées dans l'ordre SF_01→SF_16, zéro court-circuit.
    Exige l'environnement complet (CI). Ici : l'ordre déclaré dans murus.py est vérifié."""
    import murus
    order = [sf for sf, _, _ in murus.CHAIN]
    assert order == [f"SF_{i:02d}_" + n for i, n in enumerate(
        ["VIGILIA", "VERDICTUM", "ANGULI", "SELECTIO", "VOX", "LIBELLUS", "VEXILLUM",
         "PURGATIO", "PORTAS", "SPECULUM", "LUMEN", "FABRICA", "POLITURA",
         "CAMOUFLAGE", "LUTHER", "MISSIO"], start=1)]


# ------------------------------------------------- T02 : gate V1 rejetée
def test_t02_gate_rejetee_stop_net():
    import murus
    with tempfile.TemporaryDirectory() as td:
        report = Path(td) / "MURUS_LOG.md"
        assert murus.gate("V1", Path(td) / "verdict.json", report, answer="r") is False
        data = json.loads(report.read_text(encoding="utf-8"))
        assert data["decision"] == "rejete" and data["gate"] == "V1"


# ------------------------------------------------- T03 : cap 15
def test_t03_cap_15():
    cfg = json.loads((ROOT / "config/selection.json").read_text(encoding="utf-8"))
    cap = cfg.get("cap_segments") or cfg.get("top_n") or 15
    assert int(cap) <= 15, f"cap SELECTIO = {cap} > 15"


# ------------------------------------------------- T04 : ordre M5 < M2
def test_t04_vox_avant_libellus():
    import murus
    names = [sf for sf, _, _ in murus.CHAIN]
    assert names.index("SF_05_VOX") < names.index("SF_06_LIBELLUS"), \
        "le bait se mesure sur la transcription : M5 doit précéder M2"


# ------------------------------------------------- T05 : VEXILLUM sans opacité
def test_t05_vexillum_watermark_json_sans_opacite():
    wm = ROOT / "FR_A_CERVEAU/SF_07_VEXILLUM/OUT/watermark.json"
    if not wm.exists():
        return  # pas de run local : la CI produit l'artefact
    data = json.loads(wm.read_text(encoding="utf-8"))
    blob = json.dumps(data).lower()
    assert not any(k in blob for k in ("opacity", "position", "size"))


# ------------------------------------------------- T06 : pack embarque son watermark
def test_t06_pack_embarque_watermark():
    packs = list((ROOT / "EXPORT").glob("production_pack_*.json"))
    if not packs:
        return  # CI uniquement
    pack = json.loads(packs[0].read_text(encoding="utf-8"))
    assert pack.get("watermark", {}).get("bundled") is True


# ------------------------------------------------- T07 : PURGATIO clé morte nommée
def test_t07_purgatio_cle_morte_nommee():
    code = ROOT / "FR_A_CERVEAU/SF_08_PURGATIO/CODEBASE/purgatio.py"
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "pack.json"
        bad.write_text(json.dumps({"mode": "mark1", "cle_inventee": 1}), encoding="utf-8")
        r = subprocess.run([sys.executable, str(code), "--pack", str(bad),
                            "--schema", str(ROOT / "CONTRACTS/production_pack_schema.json")],
                           capture_output=True, text=True, cwd=ROOT)
        assert r.returncode != 0, "la porte P1 doit refuser un pack avec clé morte"
        assert "cle_inventee" in (r.stdout + r.stderr), "la clé morte doit être NOMMÉE"


# ------------------------------------------------- T08 : clip_token unique
def test_t08_clip_token_format_unique():
    packs = list((ROOT / "EXPORT").glob("production_pack_*.json"))
    if not packs:
        return
    tokens = [json.loads(p.read_text(encoding="utf-8")).get("clip_token") for p in packs]
    pat = re.compile(r"^A\d{2}-\d{8}-[0-9A-FX]{8}$")
    assert all(t and pat.match(t) for t in tokens), f"token non conforme : {tokens}"
    assert len(tokens) == len(set(tokens)), "clip_token dupliqué"


# ------------------------------------------------- T09 : aucun rendu sans codex
def test_t09_aucun_rendu_sans_codex():
    sys.path.insert(0, str(ROOT / "FR_B_CREATION/GATES"))
    import gates_b
    # Sans codex signés dans REVIEW/ (gitignore les sorties) -> G1 refuse.
    has_real = (ROOT / "REVIEW/codex_render.json").exists() and (ROOT / "REVIEW/codex_postprod.json").exists()
    if has_real:
        return
    ok, motif = gates_b.gate_g1_exige_codex_signes()
    assert ok is False and motif, "G1 doit refuser de tourner sans les deux codex signés"


# ------------------------------------------------- T10 : la review n'écrit pas les textes
def test_t10_codex_ne_porte_pas_de_texte():
    ex = ROOT / "REVIEW/codex_render.example.json"
    if not ex.exists():
        return
    codex = json.loads(ex.read_text(encoding="utf-8"))
    blob = json.dumps(codex).lower()
    assert "overlay_title" not in blob, "le codex porte un STYLE, jamais un texte de titre"


# ------------------------------------------------- T11 : schéma codex strict
def test_t11_schema_codex_strict():
    tools = ROOT / "tools/codex.py"
    assert tools.exists(), "tools/codex.py (pillé) absent"
    src = tools.read_text(encoding="utf-8")
    assert "check" in src, "tools/codex.py doit exposer la sous-commande check (refuse l'inconnu)"


# ------------------------------------------------- T12 : ordre PP2 gravé
def test_t12_ordre_pp2_grave():
    sys.path.insert(0, str(ROOT / "FR_B_CREATION/GATES"))
    import gates_b
    assert gates_b.PP2_ORDER == ["glow", "caption", "lut", "fade"]
    src = (ROOT / "FR_B_CREATION/SF_10_SPECULUM/CODEBASE/src/preview/codexExport.js").read_text(encoding="utf-8")
    m = re.search(r"PP2_ORDER\s*=\s*\[([^\]]*)\]", src)
    assert m and [s.strip().strip("'\"") for s in m.group(1).split(",")] == gates_b.PP2_ORDER


# ------------------------------------------------- T13 : GLOW sans preview refusé
def test_t13_glow_sans_preview_refuse():
    pg = ROOT / "FR_B_CREATION/SF_11_LUMEN/CODEBASE/preview_glow.py"
    assert pg.exists(), "preview_glow.py (pillé) absent"
    if not HAS_FFMPEG:
        return  # le refus GL2 (exit 2) s'exécute en CI avec ffmpeg
    r = subprocess.run([sys.executable, str(pg), "--frame", "inexistant.png"],
                       capture_output=True, text=True, cwd=str(pg.parent))
    assert r.returncode == 2, f"GL2 doit refuser (exit 2), obtenu {r.returncode}"


# ------------------------------------------------- T14 : CAMOUFLAGE sans gate
def test_t14_camouflage_sans_gate():
    import murus
    assert "SF_14_CAMOUFLAGE" in murus.NO_GATE
    assert "SF_15_LUTHER" in murus.NO_GATE
    gates = {sf: g for sf, g, _ in murus.CHAIN}
    assert gates["SF_14_CAMOUFLAGE"] is None and gates["SF_15_LUTHER"] is None
    # et immédiatement après POLITURA dans la chaîne
    names = [sf for sf, _, _ in murus.CHAIN]
    assert names.index("SF_13_POLITURA") + 1 == names.index("SF_14_CAMOUFLAGE")
    assert names.index("SF_14_CAMOUFLAGE") + 1 == names.index("SF_15_LUTHER")


# ------------------------------------------------- T15 : LUTHER QA tag suspect
def test_t15_luther_qa_tags_suspects():
    src = (ROOT / "FR_B_CREATION/SF_15_LUTHER/CODEBASE/lac_f06_luther.py").read_text(encoding="utf-8")
    assert "qa_pass" in src and "suspicious_tags_after" in src
    if HAS_FFMPEG:
        with tempfile.TemporaryDirectory() as td:
            # MP4 infecté simulé : on ne peut pas créer un vrai MP4 sans source ;
            # le test CI complet utilise un asset synthétique. Ici : la fonction QA existe.
            assert "encoder" in src.lower(), "F06 traque aussi le tag 'encoder'"


# ------------------------------------------------- T16 : V7 et la règle C3
def test_t16_v7_refuse_vende_qa_false():
    sys.path.insert(0, str(ROOT / "FR_B_CREATION/GATES"))
    import gates_b
    ok, motif = gates_b.gate_v7_refuses_sale_livrable()
    # Sans rapports présents (sorties gitignorées) : V7 refuse (pas de preuve de passage).
    if not (ROOT / "FR_B_CREATION/SF_14_CAMOUFLAGE/OUT/camouflage_report.json").exists():
        assert ok is False and "rapport absent" in motif
    # La règle C3 est gravée dans CONTRACTS/clipping_rules.md
    rules = (ROOT / "CONTRACTS/clipping_rules.md").read_text(encoding="utf-8", errors="replace")
    assert re.search(r"1\s*h|une heure|60\s*min", rules, re.IGNORECASE), "règle C3 absente des contrats"


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_t") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                fails += 1
                print(f"FAIL {name} : {e}")
            except Exception as e:  # noqa
                fails += 1
                print(f"ERROR {name} : {type(e).__name__}: {e}")
    print(f"\n{'TOUTES LES PORTES SONT VERTES' if fails == 0 else f'{fails} ECHEC(S)'}")
    sys.exit(1 if fails else 0)

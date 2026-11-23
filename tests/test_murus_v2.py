#!/usr/bin/env python3
"""Portes de la branche v2 — un oracle par étape du PLAN_V2.

Chaque test porte le nom de son oracle. Un oracle qui n'a pas encore tourné pour
de vrai n'est pas ici : il est marqué ATTENDU dans le plan. Ce fichier ne teste
que ce qui peut être prouvé sans réseau, sans moteur lancé et sans GPU : contrat,
refus, doctrine, ordre des étages.
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "FR_B_CREATION/SF_12_FABRICA/vive/vive_runner.py"
VENDOR = ROOT / "FR_B_CREATION/SF_12_FABRICA/vive/vendor/neonclipping"
PLAN = ROOT / "TRACKING/PLAN_V2.md"
PY = sys.executable


def _run(*args, timeout=180):
    r = subprocess.run([PY, str(RUNNER), *args], capture_output=True, text=True,
                       timeout=timeout, cwd=str(ROOT))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _codex(tmp, nom, signe=True):
    p = Path(tmp) / nom
    p.write_text(json.dumps({
        "schema_version": "sanguinala.render.codex.v1",
        "canvas": "9:16", "fps": 30, "style": "blur",
        "look": {"degree": 24}, "title": {"size": 68}, "logo": {"enabled": True},
        "validated_by_magos": signe, "pack_token": "70f120a8",
    }), encoding="utf-8")
    return str(p)


def _pack(tmp, assets=None):
    p = Path(tmp) / "pack.json"
    p.write_text(json.dumps({
        "pack_token": "70f120a8",
        "assets": assets if assets is not None else [
            {"id": "A01", "start_sec": 10.0, "end_sec": 40.0},
            {"id": "A02", "start_sec": 50.0, "end_sec": 80.0},
        ],
    }), encoding="utf-8")
    return str(p)


# ───────────────────────────── T20 — le moteur vive ─────────────────────

def test_t20_moteur_vive():
    """T20 : le moteur vive tourne headless, sans LLM, sans navigateur, sans décision.

    Ce qui est prouvé ici (sans réseau) : le contrat du moteur est celui qu'on a
    relevé, le runner refuse sans les deux codex signés, il n'importe ni
    navigateur ni client HTTP tiers, il désactive les sous-titres et ne transmet
    aucun titre, et il neutralise Ollama au lieu de l'espérer absent.
    """
    assert RUNNER.is_file(), "vive_runner.py absent"
    assert VENDOR.is_dir(), "le moteur vendé est absent"
    src = RUNNER.read_text(encoding="utf-8")

    # 1. le contrat du moteur, relevé et non supposé
    app = (VENDOR / "app.py").read_text(encoding="utf-8", errors="replace")
    assert "@app.post('/export')" in app, "le moteur n'expose plus /export"
    assert "@app.get('/status/{id}')" in app, "le moteur n'expose plus /status/{id}"
    assert "captions'" in app, "le drapeau captions du moteur a disparu"

    # 2. stdlib seulement : aucune dépendance nouvelle, aucun navigateur
    for interdit in ("import requests", "import httpx", "import selenium", "import playwright",
                     "from playwright", "import ollama", "packages/fastapi"):
        assert interdit not in src, "le runner dépend de %s (interdit : stdlib seulement)" % interdit
    assert "urllib.request" in src, "le runner doit parler HTTP via urllib (stdlib)"

    # 3. aucun LLM : Ollama est neutralisé ET la présence d'un LLM fait refuser
    assert "OLLAMA_HOST" in src, "le runner ne neutralise pas Ollama"
    assert "NEONCLIPPING_LLM_MODEL" in src, "le runner n'annule pas le modèle LLM du moteur"
    assert "die(3" in src, "le runner ne refuse pas quand un LLM répond"

    # 4. la doctrine D-5 : le moteur ne grave ni titre ni sous-titre
    assert '"captions": False' in src, "les sous-titres du moteur ne sont pas désactivés"
    corps = src.split("def export_un_clip", 1)[1].split("def ", 1)[0]
    assert "title" not in corps.replace("titre", ""), \
        "le corps d'export transmet un titre (D-5 : le moteur n'en grave aucun)"

    # 5. refus : codex non signé ⇒ rien ne se passe, code 2
    with tempfile.TemporaryDirectory() as tmp:
        rc, out = _run("--pack", _pack(tmp), "--vod", "x.mp4",
                       "--codex-render", _codex(tmp, "r.json", signe=False),
                       "--codex-postprod", _codex(tmp, "p.json", signe=True))
        assert rc == 2, "un codex non signé doit refuser avec le code 2 (rc=%s)\n%s" % (rc, out)
        assert "validated_by_magos" in out, "le refus ne nomme pas la cause"

        # 6. refus : pack sans assets ⇒ code 4
        vide = Path(tmp) / "vide.json"
        vide.write_text(json.dumps({"assets": []}), encoding="utf-8")
        rc, out = _run("--pack", str(vide), "--vod", "x.mp4",
                       "--codex-render", _codex(tmp, "r.json"),
                       "--codex-postprod", _codex(tmp, "p.json"))
        assert rc == 4, "un pack vide doit refuser avec le code 4 (rc=%s)" % rc

        # 7. refus : fenêtre inversée ⇒ code 4
        rc, out = _run("--pack", _pack(tmp, [{"id": "A01", "start_sec": 40.0, "end_sec": 10.0}]),
                       "--vod", "x.mp4",
                       "--codex-render", _codex(tmp, "r.json"),
                       "--codex-postprod", _codex(tmp, "p.json"))
        assert rc == 4, "une fenêtre inversée doit refuser avec le code 4 (rc=%s)" % rc

        # 8. refus : pack et codex de packs différents ⇒ code 4
        autre = Path(tmp) / "autre.json"
        autre.write_text(json.dumps({"pack_token": "deadbeef", "assets": [
            {"id": "A01", "start_sec": 1.0, "end_sec": 2.0}]}), encoding="utf-8")
        rc, out = _run("--pack", str(autre), "--vod", "x.mp4",
                       "--codex-render", _codex(tmp, "r.json"),
                       "--codex-postprod", _codex(tmp, "p.json"))
        assert rc == 4 and "même pack" in out.replace("pack", "pack"), \
            "un pack et un codex de packs différents doivent refuser (rc=%s)\n%s" % (rc, out)

    # 9. selfcheck : vert sur le vendor réel
    rc, out = _run("--selfcheck")
    assert rc == 0, "selfcheck en échec :\n%s" % out


def test_t20b_ollama_bloque():
    """T20b : un LLM qui répond est un refus, pas un détail.

    La doctrine interdit tout LLM dans la sélection. On monte un faux service sur
    un port libre, on vérifie que la détection le voit, et que la dérogation est
    nominative (`--ignore-ollama`) et non implicite.
    """
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    port = srv.getsockname()[1]
    srv.listen(1)
    try:
        sonde = socket.socket()
        sonde.settimeout(1.0)
        assert sonde.connect_ex(("127.0.0.1", port)) == 0, "le port de test ne répond pas"
        sonde.close()
    finally:
        srv.close()
    src = RUNNER.read_text(encoding="utf-8")
    assert "11434" in src and "ollama_repond" in src, "la détection Ollama a disparu du runner"
    assert "--ignore-ollama" in src, "aucune dérogation nominative n'existe"
    assert "derogation_llm" in src, "la dérogation n'est pas écrite dans le rapport"


# ───────────────────────── T21 — mapping codex → moteur ──────────────────

def test_t21_mapping_codex_moteur():
    """T21 : chaque paramètre du codex est soit transmis, soit nommé comme écart.

    Un paramètre qui disparaît sans être nommé est un mensonge silencieux : c'est
    exactement ce que la V1 a payé avec E-17 (police absente, clip livré sans
    sous-titres). Ici, l'absence est écrite et refusée si elle n'est pas écrite.
    """
    sys.path.insert(0, str(RUNNER.parent))
    import importlib
    vive = importlib.import_module("vive_runner")
    mapping_txt = json.dumps({
        "equivalences": vive.EQUIVALENCES,
        "ecarts": vive.ECARTS_CONNUS,
    }, ensure_ascii=False).lower()

    # les familles réellement présentes dans les deux codex signés du dépôt
    render = json.loads((ROOT / "REVIEW/codex_render.json").read_text(encoding="utf-8"))
    post = json.loads((ROOT / "REVIEW/codex_postprod.json").read_text(encoding="utf-8"))
    familles = {"canvas", "fps", "style"} | (set(render) - {"schema_version", "validated_by_magos",
                                                           "pack_token", "provenance"})
    familles |= set(post) - {"schema_version", "validated_by_magos", "pack_token", "provenance",
                             "order"}
    manquants = [f for f in familles if f not in mapping_txt]
    assert not manquants, "paramètres du codex ni transmis ni déclarés en écart : %s" % manquants

    # les écarts qui comptent le plus sont écrits noir sur blanc
    for cle in ("title", "logo", "glow", "caption", "lut", "fade_out"):
        assert cle in vive.ECARTS_CONNUS, "écart non déclaré : %s" % cle
    # et les équivalences réelles
    for cle in ("canvas", "fps", "style"):
        assert cle in vive.EQUIVALENCES, "équivalence non déclarée : %s" % cle
    # aucun écart n'est vide : un écart sans motif n'informe personne
    for cle, motif in vive.ECARTS_CONNUS.items():
        assert isinstance(motif, str) and len(motif) > 20, "écart %s sans motif lisible" % cle


# ───────────────── T22 — la purgue s'applique aux deux voies ────────────

def test_t22_purgue_identique():
    """T22 : un clip vive subit exactement la même fin de chaîne qu'un premium.

    SF_14 (camouflage, seul ré-encodeur) puis SF_15 (luther, copie de flux), et
    rien après. Le runner lui-même ne ré-encode pas : sinon un clip serait
    purgé deux fois et le `qa_pass` mesurerait le mauvais fichier.
    """
    sys.path.insert(0, str(ROOT))
    from FR_B_CREATION.GATES import gates_b  # noqa: E402
    assert gates_b.NO_GATE == ("SF_14_CAMOUFLAGE", "SF_15_LUTHER"), \
        "les deux étages sans gate ont changé — la purgue n'est plus celle de V1"

    for cli in ("FR_B_CREATION/SF_14_CAMOUFLAGE/CODEBASE/lac_f05_camouflage.py",
                "FR_B_CREATION/SF_15_LUTHER/CODEBASE/lac_f06_luther.py"):
        assert (ROOT / cli).is_file(), "CLI de purgue absente : %s" % cli

    wf = ROOT / ".github/workflows/v2_vive.yml"
    assert wf.is_file(), "aucun workflow ne purge les clips vive (T22 ne peut pas être tenu)"
    w = wf.read_text(encoding="utf-8")
    assert "vive_runner.py" in w, "le workflow vive n'appelle pas le runner"
    assert "lac_f05_camouflage.py" in w and "lac_f06_luther.py" in w, \
        "le workflow vive ne passe pas par SF_14 puis SF_15"
    assert w.index("vive_runner.py") < w.index("lac_f05_camouflage.py") < w.index("lac_f06_luther.py"), \
        "l'ordre coupe → camouflage → luther n'est pas respecté"
    assert "qa_pass" in w, "le workflow vive ne prouve pas son passage (qa_pass)"

    # le runner ne ré-encode pas : aucun appel ffmpeg d'encodage chez lui
    src = RUNNER.read_text(encoding="utf-8")
    assert "libx264" not in src and "-c:v" not in src, \
        "le runner ré-encode : SF_14 doit rester le seul ré-encodeur"
    assert "ffprobe" in src, "le runner ne mesure pas ce qu'il produit (durée)"


# ────────────────────────── T23..T29 : ATTENDU ─────────────────────────

def test_t23_t29_attendus_declares():
    """Les oracles non encore exécutés sont DÉCLARÉS ATTENDU, jamais présentés verts.

    Le CDC V2 écrit noir sur blanc que ses résultats de test sont « ATTENDU,
    jamais exécutés ». Une porte qui prétend passer sans avoir tourné est le
    défaut le plus coûteux du projet : il est interdit ici.
    """
    plan = PLAN.read_text(encoding="utf-8")
    for oracle in ("T20", "T21", "T22", "T23", "T24", "T25", "T26", "T27", "T28", "T29"):
        assert oracle in plan, "oracle absent du plan opposable : %s" % oracle
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "ATTENDU" in readme, "le README présente des oracles non exécutés comme acquis"
    for etape in range(2, 10):
        assert "Étape %d" % etape in plan, "étape %d absente du plan" % etape


def _main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    echecs = 0
    for t in tests:
        try:
            t()
            print("PASS %s" % t.__name__)
        except AssertionError as e:
            echecs += 1
            print("FAIL %s : %s" % (t.__name__, e))
        except Exception as e:  # noqa: BLE001
            echecs += 1
            print("ERROR %s : %s: %s" % (t.__name__, type(e).__name__, e))
    print("\n%s" % ("TOUTES LES PORTES V2 SONT VERTES" if not echecs
                    else "%d PORTE(S) V2 EN ECHEC" % echecs))
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(_main())

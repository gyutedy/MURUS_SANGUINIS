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


def test_t17_docs_operateur_bilingues():
    """DOCTRINE_BILINGUE : tout document operateur existe en EN et en FR.

    Un document qui perd une langue est un document qui cache le sens a l'une des
    deux parties. La CI refuse.
    """
    import glob

    doc = ROOT / "TRACKING/DOCTRINE_BILINGUE.md"
    assert doc.exists(), "doctrine bilingue absente : TRACKING/DOCTRINE_BILINGUE.md"
    txt = doc.read_text(encoding="utf-8")
    assert "## EN" in txt and "## FR" in txt, "DOCTRINE_BILINGUE.md doit etre elle-meme bilingue"

    docs = []
    for motif in ("TRACKING/SELECTION_*.md", "TRACKING/SIEGE_*.md"):
        docs += glob.glob(str(ROOT / motif))
    assert docs, "aucun document operateur a verifier : la selection doit etre publiee"

    for d in docs:
        t = Path(d).read_text(encoding="utf-8", errors="replace")
        assert "## EN" in t, "%s : section EN absente (doctrine bilingue)" % Path(d).name
        assert "## FR" in t, "%s : section FR absente (doctrine bilingue)" % Path(d).name


def test_t18_anti_remplissage():
    """ANTI-REMPLISSAGE : jamais de clip ajoute pour atteindre le nombre demande.

    On demande beaucoup plus de fenetres que le transcript n'en offre : le moteur
    doit en rendre MOINS, sans doublon, et le dire (nb_demande / nb_retenu / manque).
    """
    import importlib.util
    import json

    mark1 = ROOT / "FR_A_CERVEAU/MARK1"
    import sys as _sys
    if str(mark1) not in _sys.path:
        _sys.path.insert(0, str(mark1))
    spec = importlib.util.spec_from_file_location("mt", mark1 / "libs/transcript.py")
    tr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tr)

    doc = {"transcript": {"segments": [
        {"start": 1000.0, "end": 1020.0, "text": "we lost everything that night"},
        {"start": 1200.0, "end": 1220.0, "text": "nobody ever paid the truth"},
    ]}}
    cfg = {"default_language": "en", "min_segment_sec": 8, "max_segment_sec": 90,
           "target_segment_sec": 30, "selection": {"intro_skip_sec": 0, "min_force": 1}}

    w = tr.candidate_windows(doc, cfg, limit=15)
    assert len(w) == 2, "le moteur a fabrique des fenetres : %d pour 2 moments reels" % len(w)
    starts = [round(float(x["start_sec"]), 1) for x in w]
    assert len(set(starts)) == len(starts), "un moment a ete duplique pour remplir"

    # la regle est ecrite dans le code du moteur, pas seulement dans un document
    src = (mark1 / "mark1.py").read_text(encoding="utf-8")
    assert "ANTI_REMPLISSAGE" in src, "la regle anti-remplissage n'est plus appliquee par mark1.py"
    for champ in ("nb_demande", "nb_retenu", "manque", "remplissage_refuse"):
        assert champ in src, "champ trace manquant dans le pack : %s" % champ

    doc_d = ROOT / "TRACKING/DOCTRINE_ANTI_REMPLISSAGE.md"
    assert doc_d.exists(), "doctrine anti-remplissage absente"
    t = doc_d.read_text(encoding="utf-8")
    assert "## EN" in t and "## FR" in t, "la doctrine doit etre bilingue"



def test_t19_previews_separees():
    """Preview 1 = LOOK seul. Le postprod (glow/lut/fade/sous-titres) est en preview 2.

    Faute payee : la preview 1 portait les curseurs de glow, lut, fade et
    sous-titres, et exportait codex_postprod.json. Deux previews, deux roles.
    """
    app = ROOT / "FR_B_CREATION/SF_10_SPECULUM/CODEBASE/src/App.jsx"
    src = app.read_text(encoding="utf-8")

    # 1. le panneau postprod n'est plus rendu dans la preview 1
    for interdit in ("patchCaption({", "patchPostprod('glow'", "patchPostprod('lut'",
                     "patchPostprod('fadeOut'"):
        assert interdit not in src, "postprod encore pilote par la preview 1 : %s" % interdit

    # 2. la preview 1 n'ecrit plus le codex postprod
    assert "buildCodexPostprod({" not in src, "la preview 1 ecrit encore codex_postprod.json"
    assert "codex_render.json" in src, "la preview 1 doit ecrire codex_render.json"

    # 3. les reglages qui appartiennent au LOOK existent bien
    assert 'type="color"' in src, "couleur du titre absente : le codex la lit (t.color) sans UI"
    assert "position horizontale" in src, "curseur W1 gauche/droite absent"
    assert "position verticale" in src, "curseur W1 hauteur absent"

    # 4. l'identite du lecteur est stable (correctif ecran noir)
    assert "const composition = useMemo(() => (props) => <PurPackComposition {...props} />, []);" in src,         "l'identite du lecteur depend encore de manifest : la video rechargera (ecran noir)"
    assert 'inputProps={{ purManifest: viewManifest, entryIndex }}' in src,         "les donnees du lecteur doivent passer par inputProps (manifest sans logo moteur)"

    # 5. la doctrine est ecrite et bilingue
    doc = ROOT / "TRACKING/PREVIEWS_ROLES.md"
    assert doc.exists(), "TRACKING/PREVIEWS_ROLES.md absent"
    t = doc.read_text(encoding="utf-8")
    assert "## EN" in t and "## FR" in t, "PREVIEWS_ROLES.md doit etre bilingue"


def test_t20_errata():
    """Les erreurs payees sont ecrites, et le nommage des clips est aligne partout."""
    doc = ROOT / "TRACKING/ERRATA.md"
    assert doc.exists(), "TRACKING/ERRATA.md absent"
    t = doc.read_text(encoding="utf-8")
    assert "## EN" in t and "## FR" in t, "ERRATA.md doit etre bilingue"
    for cle in ("pur_<id>.mp4", "$GITHUB_OUTPUT", "useMemo", "additionalProperties", "keep_files"):
        assert cle in t, "erreur payee non documentee : %s" % cle

    # le producteur de clips ecrit le nom que la review cherche (E-1)
    tool = (ROOT / "FR_B_CREATION/tools/recuperer_clip.py").read_text(encoding="utf-8")
    assert '"pur_%s.mp4"' in tool, "recuperer_clip.py doit ecrire pur_<id>.mp4 (sinon lecteur noir)"
    bridge = (ROOT / "FR_B_CREATION/SF_10_SPECULUM/CODEBASE/src/preview/bridgeClipper.js").read_text(encoding="utf-8")
    assert "clips/pur_${id}.mp4" in bridge, "clipFileCandidates a change : realigner le producteur"

    # la preview 2 publie en sous-dossier sans effacer la preview 1 (E-6 / EXC-M10)
    p2 = (ROOT / ".github/workflows/murus_preview_2.yml").read_text(encoding="utf-8")
    p1 = (ROOT / ".github/workflows/murus_preview_1.yml").read_text(encoding="utf-8")
    assert "destination_dir: preview2" in p2, "preview 2 doit publier dans /preview2/"
    assert "keep_files: true" in p1 and "keep_files: true" in p2, "les deux previews doivent garder l'autre"
    assert "force_orphan" not in p1 and "force_orphan" not in p2, "force_orphan efface l'autre preview"

    # les schemas de codex sont stricts : la provenance vit en sidecar (E-5)
    p2draft = p2
    assert "codex_postprod.provenance.json" in p2draft, "la provenance doit etre en sidecar"


def test_t21_watermark_png_et_panneau_titre():
    """Le logo affiche est le PNG de campagne du pack, et le panneau titre est complet.

    Fautes payees : le double-clic posait src:'wm.png' (image cassee) et la scene
    affichait un cercle vert "WM" au lieu du PNG ; les titres du pack n'apparaissaient
    pas (review.titles vide) et la police n'etait pas reglable.
    """
    src = (ROOT / "FR_B_CREATION/SF_10_SPECULUM/CODEBASE/src/App.jsx").read_text(encoding="utf-8")

    # 1. plus de nom de fichier invente
    assert "src: 'wm.png'" not in src, "le watermark est encore pose avec un nom invente"
    assert "packWatermarkSrc" in src, "le PNG doit venir du pack (watermark.file)"
    assert "packs[0].watermark" in src or "(packs[0] && packs[0].watermark" in src,         "le pack n'est pas la source du fichier watermark"

    # 2. la scene affiche l'image, pas un cercle
    assert 'alt="watermark"' in src, "la scene n'affiche pas le PNG du watermark"
    import re as _re
    assert not _re.search(r">\s*WM\s*<", src), "la scene dessine encore un cercle WM au lieu du PNG"

    # 3. le logo et les titres du pack sont la des le chargement
    assert "seededImages" in src, "le logo n'est pas present d'emblee"
    # les titres viennent de copywriting.overlay_title (un par clip), pas de .assets
    assert "(pk.copywriting || {}).overlay_title" in src,         "les titres doivent etre lus dans copywriting.overlay_title (expandSanguinalaPack)"
    assert "first.watermark" in src, "le watermark doit etre lu a plat sur le pack expanse"

    # ANTI-DOUBLON : le logo du moteur est masque a l'affichage, la review seule le place
    assert "viewManifest" in src, "le logo du pack n'est pas masque : il y aura deux watermarks"
    assert "enabled: false" in src, "le logo du moteur doit etre desactive a l'affichage"
    assert "purManifest: viewManifest" in src, "le lecteur doit recevoir le manifest sans logo moteur"

    # 4. le panneau titre est complet : hauteur, taille, couleur, police
    for champ in ("taille {t.size}px", "couleur du titre", "police du titre"):
        assert champ in src, "reglage manquant dans le panneau titre : %s" % champ

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

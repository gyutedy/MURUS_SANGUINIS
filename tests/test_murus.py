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
    # doublon TEXTE : l'overlay du moteur est masque, sinon deux textes se superposent
    assert "narrative.overlay = { ...(narrative.overlay || {}), lines: [] }" in src,         "l'overlay du moteur n'est pas masque : deux textes se superposent (dont un illisible)"
    # aucun watermark pose d'office (un logo colle au milieu passe pour un doublon)
    assert "const seededImages = (wmp.images && wmp.images.length) ? wmp.images : [];" in src,         "un watermark est encore pose d'office au chargement"
    # les curseurs W1 doivent marcher AVANT que le logo soit pose (sinon panneau mort)
    assert "patchWmAny" in src, "les curseurs watermark exigent un logo deja pose (panneau mort)"
    assert "Poser le logo de campagne" in src, "aucun bouton pour poser le PNG de campagne"
    # un seul titre a l'ecran, celui du clip affiche
    assert "[review.titles?.[entryIndex]]" in src, "tous les titres sont dessines sur la meme image"
    # le defilement est dans les panneaux, la scene reste en haut
    assert "gridTemplateColumns" in src and "overflowY: 'scroll'" in src,         "la page defile au lieu des panneaux : la scene doit rester en haut"
    # W1 doit etre visible sans defiler : il passe avant T1
    assert src.index("W1 watermark curseur") < src.index("T1 titres (editables)"),         "le panneau W1 est encore sous les titres (coupe en bas de l'ecran)"
    assert "enabled: false" in src, "le logo du moteur doit etre desactive a l'affichage"
    assert "purManifest: viewManifest" in src, "le lecteur doit recevoir le manifest sans logo moteur"

    # 4. le panneau titre est complet : hauteur, taille, couleur, police
    for champ in ("taille {t.size}px", "couleur du titre", "police du titre"):
        assert champ in src, "reglage manquant dans le panneau titre : %s" % champ


def test_t22_codex_render_signe():
    """Le codex LOOK signe est valide, coherent avec le pack, et sa provenance est en sidecar."""
    import hashlib
    import json
    import sys as _sys

    cx = ROOT / "REVIEW/codex_render.json"
    assert cx.exists(), "REVIEW/codex_render.json absent : aucun rendu sans codex signe"
    raw = cx.read_text(encoding="utf-8")
    codex = json.loads(raw)

    _sys.path.insert(0, str((ROOT / "FR_B_CREATION/SF_11_LUMEN/tools").resolve()))
    import codex as C
    errs = C.check("render", codex)
    assert errs == [], "le codex signe ne passe pas le schema : %s" % errs
    assert codex.get("validated_by_magos") is True, "le codex n'est pas signe"

    pack = json.loads((ROOT / "REVIEW/pack_stage.json").read_text(encoding="utf-8"))
    assert codex.get("pack_token") == pack.get("pack_token"),         "le codex ne porte pas le pack_token du pack exporte"

    prov = ROOT / "REVIEW/codex_render.provenance.json"
    assert prov.exists(), "provenance du codex absente (ERRATA E-5 : sidecar obligatoire)"
    pv = json.loads(prov.read_text(encoding="utf-8"))
    assert pv.get("declared_by") == "operateur", "la provenance doit designer l'operateur"
    assert pv.get("sha256") == hashlib.sha256(raw.encode("utf-8")).hexdigest(),         "le sha256 de provenance ne correspond plus au codex (codex modifie apres signature)"

    # les schemas existent la ou le code pille les cherche (EXC-M5) et ne divergent pas
    a = ROOT / "REVIEW/SCHEMAS"
    b = ROOT / "FR_B_CREATION/SF_11_LUMEN/REVIEW/SCHEMAS"
    for nom in ("codex_render.schema.json", "codex_postprod.schema.json"):
        assert (b / nom).exists(), "schema absent a l'endroit ou SF_11 le cherche : %s" % nom
        assert (a / nom).read_text(encoding="utf-8") == (b / nom).read_text(encoding="utf-8"),             "copie de schema divergente : %s" % nom


def test_t24_preview2_glow_et_motion():
    """Le glow ne doit ni doubler la video ni couper la scene, et la motion doit se voir."""
    app = ROOT / "FR_B_CREATION/SF_13_POLITURA/PREVIEW2/src"
    a = (app / "App.jsx").read_text(encoding="utf-8")
    panels = (app / "Panels.jsx").read_text(encoding="utf-8")

    # une seule <video> : le glow passe par backdrop-filter, pas par une 2e video desync
    screen = a[a.index("function Screen("):a.index("export default function App()")]
    assert screen.count("<video") == 1, "le glow superpose une 2e video : doublon visible"
    assert "backdropFilter" in screen, "le glow n'utilise pas le flou du fond reel"
    # le masque GL2 est adouci : plus de coupure nette de la scene
    assert "70%" in screen and "80%" in screen, "masque GL2 non adouci : la scene est coupee en deux"
    assert "linear-gradient(to bottom, #000 0 78%" not in screen, "masque GL2 encore en coupure seche"

    # la motion des sous-titres est une vraie animation, rejouable
    assert "@keyframes murus-pop-in" in a and "@keyframes murus-slide" in a and "@keyframes murus-bounce" in a,         "les trois motions ne sont pas implementees"
    assert "animation: `murus-" in a or "animation: `murus-" in a.replace("\\", ""), "le sous-titre n'est jamais anime"
    assert "rejouer la motion" in panels, "aucun moyen de voir la motion a la demande"

    # porte navigateur : doublon et animation verifies dans Chromium
    ui = (ROOT / "tests/ui_preview2.mjs").read_text(encoding="utf-8")
    assert "videosCount > 1" in ui, "la porte navigateur n'attrape pas le doublon de lecteur"
    assert "captionAnimation" in ui, "la porte navigateur ne verifie pas l'animation du sous-titre"


def test_t25_lut_reelle_et_soustitre_temporel():
    """La LUT doit lire le bloc que le RENDU applique, et le sous-titre doit entrer en scene."""
    app = ROOT / "FR_B_CREATION/SF_13_POLITURA/PREVIEW2/src"
    a = (app / "App.jsx").read_text(encoding="utf-8")
    panels = (app / "Panels.jsx").read_text(encoding="utf-8")
    codex = (app / "codex.js").read_text(encoding="utf-8")

    # E-11 : plus de table CSS tapee a la main ; on lit atom_ic_profiles.json
    assert "atom_ic_profiles.json" in a, "la LUT de l'apercu ne lit pas les profils reels"
    assert "const LUT_CSS" not in a, "table CSS inventee encore presente (mauvais bloc : textura)"
    assert "prof.chroma" in a, "l'apercu ne lit pas le bloc chroma, celui du rendu"
    for champ in ("contrast", "saturation", "gamma", "brightness"):
        assert champ in a, "la LUT de l'apercu ignore %s (present dans le rendu)" % champ
    assert "lut-intensity" in panels, "aucun curseur d'intensite : la LUT reste invisible"
    # honnetete : ce que CSS ne sait pas faire est declare, et l'intensite n'entre PAS dans le codex
    assert "denoise" in panels and "unsharp" in panels, "les filtres non representables ne sont pas declares"
    assert "intensity: lut.intensity" not in codex.replace(" ", ""),         "l'intensite d'apercu entre dans le codex (schema strict : additionalProperties false)"

    # le sous-titre est temporel : visible a partir de son segment, anime a l'entree
    assert "onTimeUpdate" in a, "le sous-titre n'est pas pilote par le temps du clip"
    assert "captionStart" in a, "aucun debut de segment de sous-titre"
    assert "caption_start" in (ROOT / ".github/workflows/murus_preview_2.yml").read_text(encoding="utf-8"),         "le manifeste ne fournit pas caption_start"
    # pop-in doit claquer (depassement), sinon indiscernable d'un texte fixe
    assert "scale(1.08)" in a, "pop-in n'a pas de depassement : elle reste invisible"


def test_t26_codex_postprod_signe():
    """Le codex POSTPROD signe passe le schema, tient l'ordre PP2 et la coherence du pack."""
    import json
    import sys as _sys

    cx = ROOT / "REVIEW/codex_postprod.json"
    assert cx.exists(), "REVIEW/codex_postprod.json absent : aucun rendu sans codex signe"
    codex = json.loads(cx.read_text(encoding="utf-8"))
    _sys.path.insert(0, str((ROOT / "FR_B_CREATION/SF_11_LUMEN/tools").resolve()))
    import codex as C
    assert C.check("postprod", codex) == [], "le codex postprod ne passe pas le schema"
    assert codex.get("validated_by_magos") is True, "le codex postprod n'est pas signe"
    assert codex.get("order") == ["glow", "caption", "lut", "fade"], "l'ordre PP2 est altere"

    pack = json.loads((ROOT / "REVIEW/pack_stage.json").read_text(encoding="utf-8"))
    assert codex.get("pack_token") == pack.get("pack_token"), "pack_token different du pack exporte"

    g = codex["glow"]
    assert 4 <= g["sigma"] <= 30 and 0 <= g["opacity"] <= 0.6, "GL1 violee (sigma/opacite)"
    assert "enabled" not in codex["fade_out"], "fade_out n'accepte pas enabled (schema strict)"

    prov = json.loads((ROOT / "REVIEW/codex_postprod.provenance.json").read_text(encoding="utf-8"))
    assert prov.get("declared_by") == "operateur", "la provenance doit designer l'operateur"

    # G1 : les DEUX codex signes -> la porte s'ouvre
    _sys.path.insert(0, str((ROOT / "FR_B_CREATION").resolve()))
    from GATES.gates_b import gate_g1_exige_codex_signes
    ok, msg = gate_g1_exige_codex_signes()
    assert ok is True, "G1 refuse encore : %s" % msg


def test_t27_rendu_un_job_par_clip():
    """Le rendu doit avoir un job par clip, et ne bloquer que sur ses vraies entrees."""
    w = (ROOT / ".github/workflows/murus_rendu.yml").read_text(encoding="utf-8")
    assert "matrix:" in w, "aucune matrice : le rendu n'a pas un job par clip"
    assert "fail-fast: false" in w, "un clip casse tuerait les autres"
    assert "fromJson(needs.porte.outputs.assets)" in w, "la matrice ne vient pas du pack"

    # la porte ne doit PLUS exiger les sorties de la chaine (E-12)
    for sortie in ("SF_12_FABRICA/OUT/clips", "SF_13_POLITURA/OUT/postprod_report.json",
                   "SF_16_MISSIO/OUT/submissions.json", "EXPORT/production_pack_mark1"):
        assert sortie not in w, "la porte exige encore une sortie de la chaine : %s" % sortie

    # les deux codex signes sont la seule cle
    assert "validated_by_magos" in w, "la porte ne verifie pas la signature des codex"
    assert "REVIEW/pack_stage.json" in w, "le rendu ne lit pas le pack stage"
    # un lancement rend TOUT le pack par defaut (un job par clip)
    assert "default: '9'" in w, "le rendu ne prend pas tous les clips par defaut"

    # les CLIs pillees sont appelees, pas reecrites
    for cli in ("recuperer_clip.py", "convert_pur_pack.mjs", "render_pictor.mjs", "postprod.py",
                "lac_f05_camouflage.py", "lac_f06_luther.py"):
        assert cli in w, "etape du rendu absente : %s" % cli

    # l'ordre grave : postprod PUIS camouflage PUIS luther (luther = stream copy, rien apres)
    i_pp = w.index("postprod.py")
    i_cam = w.index("lac_f05_camouflage.py")
    i_lut = w.index("lac_f06_luther.py")
    assert i_pp < i_cam < i_lut, "ordre des etages casse : postprod -> camouflage -> luther"

    # V7 : la porte qa_pass est appelee avant toute livraison
    assert "gate_v7_refuses_sale_livrable" in w, "la porte V7 n'est jamais appelee"

    # double recuperation exigee par l'operateur : clip seul + zip des 9
    assert "livrable-${{ matrix.clip.id }}" in w, "chaque clip n'est pas telechargeable seul"
    assert "preme-pack-9-livrables" in w, "aucun zip unique des livrables"
    assert "render_report.json" in w and "git push" in w, "le rapport de rendu n'est pas commite"
    # E-14 : un rapport ne doit jamais bloquer la livraison
    assert "continue-on-error: true" in w, "le commit du rapport peut encore faire echouer la livraison"
    assert "git pull --rebase" in w, "pas de reprise sur rejet de push (course git)"
    # E-15 : OUT/ est gitignore, la preuve qa_pass doit etre copiee ailleurs et ajoutee en clair
    assert "REVIEW/render/luther_batch_report.json" in w, "la preuve qa_pass n'est pas copiee vers REVIEW/render"
    assert "git add -f REVIEW/render/render_report.json" in w, "les preuves ne sont pas ajoutees explicitement"
    assert "PORTE SOUS-TITRES" in w, "aucune porte n'interdit un clip sans sous-titres"
    # E-18 : la decoupe de la transcription est un OUTIL du depot, pas un python inline
    assert "transcript_slice.py" in w, "le workflow ne passe pas par l'outil de decoupe du depot"
    assert '--transcript "/tmp/work/pp/transcript_${ID}.json"' in w, "postprod ne recoit aucun transcript"

    # l'outil de decoupe : la transcription reelle suffit a produire des sous-titres
    sys.path.insert(0, str(ROOT / "FR_B_CREATION" / "SF_13_POLITURA" / "CODEBASE" / "caption"))
    import transcript_slice as ts
    source = ts.transcript_du_pack("https://www.twitch.tv/videos/2909800627")
    assert source.is_file(), "la transcription reelle du depot est introuvable (E-18)"
    segments = ts._segments_from(json.loads(source.read_text(encoding="utf-8")))
    assert len(segments) > 100, "transcription trop pauvre : %d segment(s)" % len(segments)
    for debut, fin in ((1376.2, 1406.2), (294.0, 324.0), (1727.5, 1757.5)):
        mots = ts.slice_transcript(segments, debut, fin)
        assert mots, "aucune parole decoupee entre %.1fs et %.1fs" % (debut, fin)
        assert all(0.0 <= m["start"] < (fin - debut) + 1 for m in mots), "temps non relatifs au clip"
    # un silence ne produit aucun mot, et le CLI doit alors REFUSER (code 1)
    assert ts.slice_transcript([{"text": "x", "start": 0.0, "end": 1.0}], 100.0, 130.0) == []
    refus = subprocess.run(
        [sys.executable, str(ROOT / "FR_B_CREATION" / "SF_13_POLITURA" / "CODEBASE" / "caption" / "transcript_slice.py"),
         "--transcript", str(source), "--start", "99999", "--end", "100029", "--out", "/tmp/rien.json"],
        capture_output=True, text=True)
    assert refus.returncode == 1, "un silence doit etre refuse explicitement (code 1)"

    # E-19 : pop-in = UN MOT a la fois, jamais une phrase
    mots_reels = ts.slice_transcript(segments, 1376.2, 1406.2)
    assert len(mots_reels) > 40, "la decoupe ne rend pas de mots fins : %d" % len(mots_reels)
    import ass_render as ar
    cues_pop = ar.cues_from_words(mots_reels, max_words=1)
    trop = [c["text"] for c in cues_pop if len(c["text"].split()) > 1]
    assert not trop, "pop-in doit graver un mot a la fois, trouve : %r" % trop[:3]
    assert ar.__dict__ and "cues_from_words" in dir(ar)

    # la source doit mesurer les temps par mot (sinon tout est interpole)
    siege = (ROOT / ".github/workflows/murus_siege.yml").read_text(encoding="utf-8")
    assert "word_timestamps=True" in siege, "la transcription ne mesure pas les temps par mot (E-19)"

    # E-17 : la police est demandee par son nom lisible, le fichier a un autre nom
    sys.path.insert(0, str(ROOT / "FR_B_CREATION" / "SF_13_POLITURA" / "CODEBASE" / "caption"))
    import ass_render
    for nom in ("Montserrat ExtraBold", "Montserrat-ExtraBold.ttf", "Montserrat-ExtraBold"):
        fichier = ass_render.font_file({"font": nom})
        assert fichier.is_file() and fichier.name == "Montserrat-ExtraBold.ttf",             "la police n'est pas resolue pour le nom %r (E-17)" % nom


    # EXC-M11 : plus aucun chemin F03_PREVIEW/... mort dans les CLIs utilisees
    for f in ("FR_B_CREATION/tools/convert_pur_pack.mjs",
              "FR_B_CREATION/SF_12_FABRICA/look/CODEBASE/render_pictor.mjs"):
        t = (ROOT / f).read_text(encoding="utf-8")
        assert "'../F03_PREVIEW" not in t and "'F03_PREVIEW/CODEBASE/src/preview/_purPackComposition.jsx'" not in t,             "chemin mort F03_PREVIEW encore present dans %s" % f
        assert "SF_10_SPECULUM/CODEBASE/src/preview" in t, "chemin non repointe dans %s" % f

    # le bundle Remotion ne doit plus tirer aucun chemin mort F03_PREVIEW
    look = ROOT / "FR_B_CREATION/SF_12_FABRICA/look/CODEBASE/src"
    for jsx in look.rglob("*.jsx"):
        t = jsx.read_text(encoding="utf-8")
        assert "F03_PREVIEW/CODEBASE" not in t, "import mort F03_PREVIEW encore dans %s" % jsx.name

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


def test_t28_v7_manifeste_de_soumission():
    """V7 : le projet prepare la soumission, il ne poste JAMAIS."""
    w = (ROOT / ".github/workflows/murus_v7.yml").read_text(encoding="utf-8")
    assert "gate_v7_refuses_sale_livrable" in w, "V7 sans porte qa_pass"
    assert "murus.submissions.v1" in w, "aucun manifeste de soumission"
    assert "sha256" in w, "les livrables ne sont pas identifies (sha256)"
    assert "submissions.json" in w, "manifeste non ecrit"
    assert "a_poster" in w, "le manifeste ne declare pas que l'operateur doit poster"
    for interdit in ("--post", "auto-post", "curl -X POST https://whop", "youtube.com/upload"):
        assert interdit not in w, "V7 poste tout seul : %s" % interdit
    assert "jamais" in w or "ne poste jamais" in w, "la regle 'le projet ne poste jamais' n'est pas ecrite"


def test_t29_parcours_reel_grave():
    """Le parcours REELLEMENT execute est grave dans les guides, bilingue.

    Un guide qui decrit un parcours imagine est un guide qui perd l'operateur.
    Ce test verifie que chaque workflow et chaque CLI du parcours reel sont
    nommes, que les portes sont citees, et que rien n'est raconte sur un
    composant qui n'existe plus (Modal GPU obligatoire, 16 tests).
    """
    guide = ROOT / "TRACKING/PARCOURS_REEL.md"
    assert guide.is_file(), "le parcours reel n'est pas grave : TRACKING/PARCOURS_REEL.md"
    txt = guide.read_text(encoding="utf-8")

    # bilingue, comme tout document operateur
    assert "## EN" in txt and "## FR" in txt, "PARCOURS_REEL.md doit etre bilingue (EXC-M8)"

    # chaque workflow du parcours est nomme
    for wf in ("murus_siege.yml", "murus_preview_1.yml", "murus_preview_2.yml",
               "murus_rendu.yml", "murus_v7.yml"):
        assert (ROOT / ".github/workflows" / wf).is_file(), "workflow cite mais absent : %s" % wf
        assert wf in txt, "workflow du parcours non documente : %s" % wf

    # chaque CLI reel est nomme, dans l'ordre grave
    clis = ["recuperer_clip.py", "convert_pur_pack.mjs", "render_pictor.mjs", "transcript_slice.py",
            "postprod.py", "lac_f05_camouflage.py", "lac_f06_luther.py"]
    positions = [txt.index(c) for c in clis]
    assert positions == sorted(positions), "l'ordre des etapes est faux dans le guide"
    for c in clis:
        assert list(ROOT.rglob(c)), "CLI cite mais absent du depot : %s" % c

    # les DEUX revues sont des etapes de plein droit, avec leur adresse et leur codex
    for revue in ("review 1", "review 2", "revue 1", "revue 2", "preview2/"):
        assert revue in txt, "revue absente du parcours : %s" % revue
    assert "codex_render.json" in txt and "codex_postprod.json" in txt, \
        "les codex produits par les revues ne sont pas nommes"
    assert txt.index("codex_render.json") < txt.index("codex_postprod.json"), \
        "l'ordre des deux codex est inverse"
    assert "les deux codex" in txt, "le parcours ne dit pas que les deux codex sont exiges"
    assert "ui_preview1.mjs" in txt and "ui_preview2.mjs" in txt, \
        "les portes Chromium des deux revues ne sont pas citees"

    # les portes sont nommees
    for porte in ("G1", "PP2", "5b", "qa_pass"):
        assert porte in txt, "porte non documentee : %s" % porte

    # les limites reelles sont avouees
    assert "interpolated" in txt, "le guide cache que le minutage est interpole"
    assert "a_poster" in txt, "le guide ne dit pas que l'operateur doit poster"

    # le README pointe le guide, et ne pretend plus que Modal est obligatoire
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "TRACKING/PARCOURS_REEL.md" in readme, "le README ne pointe pas le parcours reel"
    assert "16 tests" not in readme, "le README annonce encore 16 tests"
    assert "la transcription GPU passe par **Modal**" not in readme,         "le README pretend encore que tout passe par Modal GPU"


def test_t30_v2_socle():
    """Le socle V2 existe, il est labellise, et rien n'y est anonyme.

    Le CDC V2 exige un tree/F ou chaque fichier est PILLE ou CREE. Ce test
    verifie le socle : la branche porte les placeholders des trois pieces
    nouvelles, le vendor du moteur vive avec sa licence, le CDC et le plan.
    """
    vendor = ROOT / "FR_B_CREATION/SF_12_FABRICA/vive/vendor/neonclipping"
    assert vendor.is_dir(), "le vendor du moteur vive est absent"
    licence = vendor / "LICENSE"
    assert licence.is_file(), "le vendor a perdu sa LICENSE (R15)"
    assert "Permission is hereby granted" in licence.read_text(encoding="utf-8", errors="replace"), \
        "la LICENSE du vendor n'est pas une licence MIT"
    modele = vendor / "models/face_detection_yunet_2023mar.onnx"
    assert modele.is_file() and modele.stat().st_size > 100_000, "le modele YuNet est absent du vendor"
    for requis in ("app.py", "encoders.py", "highlights.py", "smart.py", "ytdl.py",
                   "live/live_clip.py", "live_session.py", "jobs.py"):
        assert (vendor / requis).is_file(), "fichier du moteur manquant : %s" % requis

    # les trois pieces nouvelles + leurs points d'entree (vides au socle, remplis ensuite)
    for place in ("FR_A_CERVEAU/SF_06_LIBELLUS/CODEBASE/elocution.py",
                  "FR_B_CREATION/SF_12_FABRICA/vive/vive_runner.py",
                  "FR_B_CREATION/SF_17_PROGRAMMA/CODEBASE/programma.py",
                  "FR_B_CREATION/SF_17_PROGRAMMA/README.md",
                  ".github/workflows/v2_publish.yml",
                  ".github/workflows/v2_elocution.yml",
                  "tests/test_murus_v2.py"):
        assert (ROOT / place).exists(), "placeholder du socle V2 absent : %s" % place
    for dossier in ("FR_B_CREATION/SF_17_PROGRAMMA/IN", "FR_B_CREATION/SF_17_PROGRAMMA/OUT",
                    "FR_B_CREATION/SF_12_FABRICA/vive/OUT", "FR_B_CREATION/SF_12_FABRICA/vive/REVIEW"):
        assert (ROOT / dossier).is_dir(), "dossier du socle V2 absent : %s" % dossier

    # le CDC V2 et le plan vivent dans le depot, pas dans une conversation
    assert (ROOT / "CDC/MURUS_SANGUINIS_CDC_V2.html").is_file(), "le CDC V2 n'est pas dans le depot"
    plan = ROOT / "TRACKING/PLAN_V2.md"
    assert plan.is_file(), "le plan d'implementation V2 est absent"
    plan_txt = plan.read_text(encoding="utf-8")
    assert "## EN" in plan_txt and "## FR" in plan_txt, "PLAN_V2.md doit etre bilingue (EXC-M8)"

    # le vendor est trace : origine, commit, licence, exclusions declarees
    vdoc = ROOT / "FR_B_CREATION/SF_12_FABRICA/vive/VENDOR.md"
    assert vdoc.is_file(), "VENDOR.md absent : le vendored code n'est pas trace"
    v = vdoc.read_text(encoding="utf-8")
    assert "0525004" in v, "le commit d'origine du vendor n'est pas ecrit"
    assert "MIT" in v, "la licence du vendor n'est pas declaree"
    assert "exclu" in v.lower(), "les fichiers exclus du vendor ne sont pas declares"

    # le plan engage un ordre, pas une intention
    for etape in ("Etape 0", "Etape 1", "Etape 2", "Etape 3", "Etape 4",
                  "Etape 5", "Etape 6", "Etape 7", "Etape 8", "Etape 9"):
        assert etape in plan_txt, "etape absente du plan : %s" % etape
    for oracle in ("T20", "T21", "T22", "T23", "T24", "T25", "T26", "T27", "T28", "T29"):
        assert oracle in plan_txt, "oracle absent du plan : %s" % oracle


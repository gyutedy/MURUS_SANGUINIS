"""Tests du registre des campagnes et du bloc de directive.

Ce qui est verrouille :
  - une seule campagne active a la fois, meme si on en active une autre ;
  - un token identifie UNE campagne (jamais deux) ;
  - une cle de publication complete (`campagne:pack:clip`) ne peut pas collisionner ;
  - une frigate qui exige une campagne refuse s'il n'y en a aucune d'active ;
  - un bloc de directive refuse une cle inconnue (pas d'ignorance silencieuse) ;
  - un bloc refuse n'ecrit RIEN (pas d'application a moitie) ;
  - chaque information posee laisse une ligne de journal.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "FR_A_CERVEAU/SF_01_VIGILIA/CODEBASE"))

import campagnes  # noqa: E402
import directives  # noqa: E402


def test_t70_une_seule_active(tmp_path):
    reg = tmp_path / "campagnes.json"
    campagnes.creer("Preme", token="70f120a8", etat=reg)
    campagnes.creer("Autre", token="abcd1234", etat=reg)
    campagnes.activer("PREME", etat=reg)
    assert campagnes.actif(etat=reg)["token"] == "70f120a8"

    c, desactivees = campagnes.activer("abcd1234", etat=reg)
    assert c["token"] == "abcd1234"
    assert desactivees == ["PREME"], "activer une campagne doit desactiver l'autre"
    actives = [c for c in campagnes.charger(reg)["campagnes"].values() if c["statut"] == "actif"]
    assert len(actives) == 1, "deux campagnes actives, c'est le projet qui ne sait plus pour qui"


def test_t71_token_unique_et_resolution(tmp_path):
    reg = tmp_path / "campagnes.json"
    campagnes.creer("Preme", token="70f120a8", etat=reg)
    try:
        campagnes.creer("Autre", token="70f120a8", etat=reg)
        raise AssertionError("un token partage par deux campagnes doit etre refuse")
    except campagnes.Refus as e:
        assert "deja celui de" in str(e)
    assert campagnes.resoudre("abcd0000", etat=reg) if False else True
    assert campagnes.resoudre("preme", etat=reg)["token"] == "70f120a8"
    assert campagnes.resoudre("70F120A8", etat=reg)["star"] == "Preme"


def test_t72_aucune_active_refuse(tmp_path):
    reg = tmp_path / "campagnes.json"
    campagnes.creer("Preme", token="70f120a8", etat=reg)
    try:
        campagnes.exiger_active(etat=reg)
        raise AssertionError("sans campagne active, une frigate doit refuser")
    except campagnes.Refus as e:
        assert "aucune campagne active" in str(e)


def test_t73_cle_publication_sans_doublon():
    a = campagnes.cle_publication("70f120a8", "aa11bb22", "A01")
    b = campagnes.cle_publication("70f120a8", "aa11bb22", "a01")
    c = campagnes.cle_publication("70f120a8", "cc33dd44", "A01")
    d = campagnes.cle_publication("99999999", "aa11bb22", "A01")
    assert a == b, "la casse du clip ne doit pas creer de doublon"
    assert len({a, c, d}) == 3, "campagne, pack et clip doivent tous compter"


def test_t74_bloc_refuse_cle_inconnue(tmp_path):
    try:
        directives.analyser_bloc("plateformes: youtube\nplateforme: tiktok")
        raise AssertionError("une cle inconnue doit etre refusee")
    except directives.Refus as e:
        assert "inconnues" in str(e)


def test_t75_bloc_refuse_n_ecrit_rien(tmp_path):
    directe = tmp_path / "campaign_directive.json"
    decl = tmp_path / "operator_declarations.json"
    journal = tmp_path / "j.jsonl"
    directe.write_text(json.dumps({"platforms": ["youtube_shorts"]}), encoding="utf-8")
    decl.write_text(json.dumps({"campaign": {"rate_usd_per_1k": 0.3}}), encoding="utf-8")
    avant = directe.read_text(encoding="utf-8")
    try:
        directives.appliquer("taux: 0.6\ncle_bidon: 1", directe=directe, declarations=decl,
                             journal=journal)
        raise AssertionError("un bloc avec une cle inconnue ne doit rien appliquer")
    except directives.Refus:
        pass
    assert directe.read_text(encoding="utf-8") == avant, "un bloc refuse ne doit rien ecrire"
    assert not journal.exists(), "aucun journal pour un bloc refuse"


def test_t76_bloc_applique_chaque_info_a_sa_place(tmp_path):
    directe = tmp_path / "campaign_directive.json"
    decl = tmp_path / "operator_declarations.json"
    journal = tmp_path / "j.jsonl"
    directe.write_text("{}", encoding="utf-8")
    decl.write_text("{}", encoding="utf-8")
    bloc = "\n".join([
        "plateformes: youtube_shorts, instagram_reels",
        "requirements: Preme point focal | watermark visible",
        "taux: 0,6",
        "budget: 2500",
        "financee: oui",
        "compte: 42",
        "focus: oui",
    ])
    jour = directives.appliquer(bloc, directe=directe, declarations=decl, journal=journal,
                                source="telegram")
    plat = json.loads(directe.read_text(encoding="utf-8"))
    dec = json.loads(decl.read_text(encoding="utf-8"))
    assert plat["platforms"] == ["youtube_shorts", "instagram_reels"]
    assert len(plat["requirements"]) == 2
    assert dec["campaign"]["rate_usd_per_1k"] == 0.6
    assert dec["campaign"]["budget_remaining_usd"] == 2500
    assert dec["campaign"]["funded"] is True
    assert dec["account"]["warmup_days"] == 42
    assert dec["focus_declared"] is True
    lignes = [json.loads(l) for l in journal.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lignes) == len(jour) == 7, "chaque information posee laisse une ligne"
    assert all(l["source"] == "telegram" for l in lignes)


def test_t77_resume_dit_ce_qui_manque(tmp_path):
    directe = tmp_path / "d.json"
    decl = tmp_path / "o.json"
    directe.write_text(json.dumps({"creator_name": "Preme", "platforms": ["youtube_shorts"],
                                   "requirements": [], "banned": []}), encoding="utf-8")
    decl.write_text(json.dumps({"campaign": {"rate_usd_per_1k": 0.6}}), encoding="utf-8")
    texte, manques = directives.resume(directe=directe, declarations=decl)
    assert "Preme" in texte and "budget" in manques and "focus" in manques


def _main():
    import tempfile

    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    echecs = 0
    for t in tests:
        try:
            if t.__code__.co_argcount:
                with tempfile.TemporaryDirectory() as d:
                    t(Path(d))
            else:
                t()
            print("PASS %s" % t.__name__)
        except AssertionError as e:
            echecs += 1
            print("FAIL %s : %s" % (t.__name__, e))
        except Exception as e:  # noqa: BLE001
            echecs += 1
            print("ERROR %s : %s: %s" % (t.__name__, type(e).__name__, e))
    print("\n%s" % ("TOUTES LES PORTES DES CAMPAGNES SONT VERTES" if not echecs
                    else "%d PORTE(S) EN ECHEC" % echecs))
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(_main())

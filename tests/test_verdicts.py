"""Tests du registre des verdicts (l'acte de l'operateur entre deux fregates).

Ce qui est verrouille :
  - une fregate ne s'ouvre pas si l'amont n'a pas de verdict ;
  - un refus ferme l'aval, il ne l'ouvre pas ;
  - un verdict porte sur UNE sortie : une autre sortie ne vaut pas validation ;
  - le registre est append-only : un nouvel acte ajoute une ligne, n'efface rien ;
  - un verdict sans sortie est refuse (il ne prouverait rien).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "FR_A_CERVEAU/SF_09_NUNTIUS/CODEBASE"))

import verdicts  # noqa: E402


def _registre(tmp):
    return Path(tmp) / "verdicts.jsonl"


def test_t50_amont_non_valide_ferme_laval(tmp_path):
    reg = _registre(tmp_path)
    ok, raison = verdicts.peut_ouvrir("PREME", "look", "non-live", "pack:70f120a8", reg)
    assert ok is False and "aucun verdict" in raison, \
        "la revue LOOK ne doit pas s'ouvrir sans le verdict du siege"


def test_t51_valide_ouvre_refuse_ferme(tmp_path):
    reg = _registre(tmp_path)
    verdicts.enregistrer("PREME", "siege", "valide", "pack:70f120a8",
                         "15 fenetres", registre=reg)
    ok, _ = verdicts.peut_ouvrir("PREME", "look", "non-live", "pack:70f120a8", reg)
    assert ok is True, "un sieve valide doit ouvrir la revue LOOK"

    verdicts.enregistrer("PREME", "siege", "refuse", "pack:70f120a8",
                         "fenetres hors sujet", registre=reg)
    ok2, raison = verdicts.peut_ouvrir("PREME", "look", "non-live", "pack:70f120a8", reg)
    assert ok2 is False and "REFUSE" in raison, \
        "un refus doit fermer l'aval, meme s'il y a eu un valide avant"


def test_t52_verdict_lie_a_une_sortie(tmp_path):
    reg = _registre(tmp_path)
    verdicts.enregistrer("PREME", "siege", "valide", "pack:70f120a8", registre=reg)
    ok, raison = verdicts.peut_ouvrir("PREME", "look", "non-live", "pack:autre", reg)
    assert ok is False and "sortie" in raison, \
        "on ne valide pas un pack puis on en rend un autre"


def test_t53_append_only(tmp_path):
    reg = _registre(tmp_path)
    verdicts.enregistrer("PREME", "siege", "refuse", "pack:a", "trop faible", registre=reg)
    verdicts.enregistrer("PREME", "siege", "valide", "pack:a", "corrige", registre=reg)
    lignes = [json.loads(l) for l in reg.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lignes) == 2, "le registre doit garder l'historique, pas le reecrire"
    assert lignes[0]["verdict"] == "refuse" and lignes[1]["verdict"] == "valide"


def test_t54_sortie_obligatoire_et_mode(tmp_path):
    reg = _registre(tmp_path)
    try:
        verdicts.enregistrer("PREME", "siege", "valide", "", registre=reg)
        raise AssertionError("un verdict sans sortie doit etre refuse")
    except verdicts.Refus as e:
        assert "sortie" in str(e)
    try:
        verdicts.enregistrer("PREME", "vive", "valide", "run:1", mode="non-live", registre=reg)
        raise AssertionError("la fregate vive n'existe pas en non-live")
    except verdicts.Refus as e:
        assert "absente du mode" in str(e)


def test_t55_live_a_sa_propre_chaine(tmp_path):
    reg = _registre(tmp_path)
    verdicts.enregistrer("PREME", "siege", "valide", "pack:70f120a8", mode="live", registre=reg)
    ok, _ = verdicts.peut_ouvrir("PREME", "vive", "live", "pack:70f120a8", reg)
    assert ok is True, "en live, le pack valide ouvre directement la coupe moteur"
    etat = verdicts.etat("PREME", "live", reg)
    assert [l["fregate"] for l in etat] == ["siege", "vive", "livraison"]


def test_t56_parcours_unique_documente():
    doc = (RACINE / "TRACKING/PARCOURS_UNIQUE.md")
    assert doc.exists(), "le parcours unique doit exister"
    texte = doc.read_text(encoding="utf-8")
    for fregate in ("siege", "look", "postprod", "rendu", "livraison", "vive"):
        assert fregate in texte, "fregate absente du parcours : %s" % fregate
    assert "## EN" in texte and "## FR" in texte, "le parcours doit etre bilingue (EXC-M8)"
    assert "verdicts.jsonl" in texte, "le registre doit etre nomme dans le parcours"


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
    print("\n%s" % ("TOUTES LES PORTES DE VERDICT SONT VERTES" if not echecs
                    else "%d PORTE(S) EN ECHEC" % echecs))
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(_main())

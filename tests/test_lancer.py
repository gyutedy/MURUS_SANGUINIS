"""Tests de la commande /lancer — une fregate ne s'ouvre que si l'amont est valide.

Ce qui est verrouille :
  - le siege s'ouvre sans verdict (c'est la premiere fregate) ;
  - LOOK refuse de s'ouvrir sans verdict du siege ;
  - LOOK s'ouvre apres un siege valide, sur la meme sortie ;
  - POSTPROD exige LOOK, LIVRAISON exige le rendu ;
  - une fregate inconnue est refusee en la nommant ;
  - un refus n'appelle JAMAIS GitHub (aucun declenchement fantome).
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "FR_A_CERVEAU/SF_09_NUNTIUS/CODEBASE"))

import lancer  # noqa: E402
import verdicts  # noqa: E402


class _Faux:
    """Remplace l'appel GitHub : on veut prouver qu'il n'est appele que si ouvert."""

    def __init__(self):
        self.appels = []

    def __call__(self, workflow, inputs):
        self.appels.append((workflow, inputs))
        return 204, ""


def _reg(tmp):
    return Path(tmp) / "verdicts.jsonl"


def _campagne(tmp):
    """Un registre de campagnes avec Preme active : sinon /lancer refuse tout."""
    import campagnes

    chemin = Path(tmp) / "campagnes.json"
    if not chemin.exists():
        campagnes.creer("Preme", token="70f120a8", etat=chemin)
        campagnes.activer("preme", etat=chemin)
    return chemin


def test_t60_siege_ouvre_sans_verdict(tmp_path):
    faux = _Faux()
    lancer.entree = faux
    r = lancer.lancer("siege https://www.twitch.tv/videos/2909800627", verdicts,
                      registre=_reg(tmp_path), registre_campagnes=_campagne(tmp_path))
    assert "ouvert" in r, r
    assert faux.appels and faux.appels[0][0] == "murus_siege.yml"
    assert faux.appels[0][1]["vod_url"].startswith("https://")


def test_t61_siege_sans_lien_refuse(tmp_path):
    faux = _Faux()
    lancer.entree = faux
    r = lancer.lancer("siege", verdicts, registre=_reg(tmp_path), registre_campagnes=_campagne(tmp_path))
    assert "lien de la VOD" in r and not faux.appels, \
        "aucun declenchement quand il manque le lien"


def test_t62_look_ferme_sans_siege_valide(tmp_path):
    faux = _Faux()
    lancer.entree = faux
    r = lancer.lancer("look", verdicts, registre=_reg(tmp_path), registre_campagnes=_campagne(tmp_path))
    assert "REFUS" in r and not faux.appels, \
        "LOOK ne doit pas s'ouvrir sans verdict du siege, et ne doit rien declencher"


def test_t63_look_ouvre_apres_siege_valide(tmp_path):
    reg = _reg(tmp_path)
    verdicts.enregistrer("PREME", "siege", "valide", "pack:70f120a8", registre=reg)
    faux = _Faux()
    lancer.entree = faux
    r = lancer.lancer("look", verdicts, registre=reg, registre_campagnes=_campagne(tmp_path))
    assert "ouvert" in r, r
    assert faux.appels[0][0] == "murus_preview_1.yml"


def test_t64_chaine_complete_et_fregate_inconnue(tmp_path):
    reg = _reg(tmp_path)
    verdicts.enregistrer("PREME", "siege", "valide", "pack:70f120a8", registre=reg)
    faux = _Faux()
    lancer.entree = faux
    assert "REFUS" in lancer.lancer("postprod", verdicts, registre=reg, registre_campagnes=_campagne(tmp_path))
    verdicts.enregistrer("PREME", "look", "valide", "codex:render", registre=reg)
    assert "ouvert" in lancer.lancer("postprod", verdicts, registre=reg, registre_campagnes=_campagne(tmp_path))
    assert "REFUS" in lancer.lancer("livraison", verdicts, registre=reg, registre_campagnes=_campagne(tmp_path))

    inconnue = lancer.lancer("hyperespace", verdicts, registre=reg, registre_campagnes=_campagne(tmp_path))
    assert "inconnue" in inconnue


def test_t65_aucun_declenchement_sans_porte(tmp_path):
    """Le point qui compte : pas de porte, pas d'appel. Meme pas un essai."""
    reg = _reg(tmp_path)
    verdicts.enregistrer("PREME", "siege", "refuse", "pack:70f120a8", "qualite", registre=reg)
    faux = _Faux()
    lancer.entree = faux
    for fregate in ("look", "postprod", "livraison"):
        lancer.lancer(fregate, verdicts, registre=reg, registre_campagnes=_campagne(tmp_path))
    assert not faux.appels, "une fregate fermee ne doit jamais appeler GitHub"


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
    print("\n%s" % ("TOUTES LES PORTES DE /lancer SONT VERTES" if not echecs
                    else "%d PORTE(S) EN ECHEC" % echecs))
    return 1 if echecs else 0

def test_t66_refus_sans_campagne_active(tmp_path):
    """Sans campagne active, on ne lance rien : pas de directive, pas de livrable."""
    reg = _reg(tmp_path)
    regc = tmp_path / "campagnes.json"
    faux = _Faux()
    lancer.entree = faux
    r = lancer.lancer("siege https://www.twitch.tv/videos/2909800627", verdicts,
                      registre=reg, registre_campagnes=regc)
    assert "campagne active" in r, r
    assert not faux.appels, "aucun declenchement sans campagne active"


def test_t67_lance_quand_la_campagne_est_active(tmp_path):
    import campagnes

    reg = _reg(tmp_path)
    regc = tmp_path / "campagnes.json"
    campagnes.creer("Preme", token="70f120a8", etat=regc)
    campagnes.activer("preme", etat=regc)
    faux = _Faux()
    lancer.entree = faux
    r = lancer.lancer("siege https://www.twitch.tv/videos/2909800627", verdicts,
                      registre=reg, registre_campagnes=regc)
    assert "ouvert" in r and "campagne Preme" in r, r
    assert faux.appels[0][0] == "murus_siege.yml", "le siege doit appeler son workflow"


if __name__ == "__main__":
    sys.exit(_main())

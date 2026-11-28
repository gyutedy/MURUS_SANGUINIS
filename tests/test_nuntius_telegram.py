"""Tests du pilotage Telegram (NUNTIUS).\n\nCe qui est verrouille ici :\n- un chat etranger est ignore, sans reponse (aucune fuite) ;\n- une commande inconnue ne declenche rien ;\n- un acte irreversible sans la phrase complete est refuse ;\n- `update_id` deja journalise = ignoré (rejeu Telegram impossible) ;\n- le Worker Cloudflare et le contrat Python disent la meme chose ;\n- le workflow refuse un demandeur qui n'est pas l'operateur.\n"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "FR_A_CERVEAU/SF_09_NUNTIUS/LISTEN"))
sys.path.insert(0, str(RACINE / "FR_A_CERVEAU/SF_09_NUNTIUS/CODEBASE"))

import parse  # noqa: E402

OPERATEUR = "7710898895"


def _up(texte, chat=OPERATEUR, uid=1):
    return {"update_id": uid, "message": {"message_id": 10, "chat": {"id": int(chat)},
                                          "text": texte}}


def test_t40_chat_etranger_ignore():
    d = parse.analyser(_up("/rendu", chat="999999999"), [OPERATEUR])
    assert d["action"] == "ignore", "un chat etranger doit etre ignore"
    assert "texte" not in d, "on ne repond pas a un inconnu : pas de fuite d'information"
    assert d["raison"] == "chat_etranger"


def test_t41_commande_inconnue_ne_declenche_rien():
    d = parse.analyser(_up("/rm-rf"), [OPERATEUR])
    assert d["action"] == "repondre" and d["raison"] == "inconnue"
    d2 = parse.analyser(_up("bonjour sans slash"), [OPERATEUR])
    assert d2["action"] == "repondre" and d2["raison"] == "pas_une_commande"


def test_t42_publication_sans_phrase_refusee():
    d = parse.analyser(_up("/publier PREME A01"), [OPERATEUR])
    assert d["action"] == "repondre" and d["raison"] == "phrase_absente", \
        "un mot seul ne doit jamais publier"
    ok = parse.analyser(_up("/publier VALIDER PUBLICATION PREME A01"), [OPERATEUR])
    assert ok["action"] == "dispatch", "la phrase complete doit passer"
    presque = parse.analyser(_up("/publier VALIDER PUBLICATION A01"), [OPERATEUR])
    assert presque["action"] == "repondre", "une phrase incomplete ne passe pas"


def test_t43_rendu_sans_serrure():
    """L'operateur a refuse une serrure sur les rendus : /rendu passe seul."""
    d = parse.analyser(_up("/rendu"), [OPERATEUR])
    assert d["action"] == "dispatch" and d["commande"] == "/rendu"
    assert d["workflow"] == "murus_rendu.yml"


def test_t44_rapport_exige_argument():
    d = parse.analyser(_up("/rapport"), [OPERATEUR])
    assert d["raison"] == "argument_manquant"
    ok = parse.analyser(_up("/rapport A01"), [OPERATEUR])
    assert ok["action"] == "dispatch" and ok["arguments"] == "A01"


def test_t45_rejeu_impossible(tmp_path=None):
    import nuntius

    journal = RACINE / "ARCHIVUM" / "telegram" / "journal_test.jsonl"
    ancien = nuntius.JOURNAL
    nuntius.JOURNAL = journal
    try:
        journal.parent.mkdir(parents=True, exist_ok=True)
        journal.unlink(missing_ok=True)
        assert nuntius.deja_vu("88421") is False
        nuntius.noter(commande="/etat", update_id="88421", effet="execute")
        assert nuntius.deja_vu("88421") is True, \
            "un update_id journalise doit rendre le rejeu impossible"
        assert nuntius.deja_vu("88422") is False
    finally:
        journal.unlink(missing_ok=True)
        nuntius.JOURNAL = ancien


def test_t46_worker_et_contrat_alignes():
    js = (RACINE / "FR_A_CERVEAU/SF_09_NUNTIUS/LISTEN/src/index.js").read_text(encoding="utf-8")
    for nom in parse.NOMS_ATTENDUS:
        assert nom in js, "commande absente du Worker : /%s" % nom
    assert "VALIDER\\s+PUBLICATION" in js, "le Worker ne verifie pas la phrase complete"
    assert "chat_etranger" in js, "le Worker ne marque pas les chats etrangers"
    assert "TELEGRAM_CHAT_IDS" in js, \
        "le Worker ne lit pas une LISTE de chats autorises (l'operateur doit pouvoir deleguer)"
    assert "update_id" in js and "update_id" in (
        RACINE / ".github/workflows/murus_telegram.yml").read_text(encoding="utf-8"), \
        "update_id doit traverser Worker -> workflow -> journal"


def test_t47_workflow_refuse_un_autre_demandeur():
    w = (RACINE / ".github/workflows/murus_telegram.yml").read_text(encoding="utf-8")
    assert "TELEGRAM_OPERATEUR_ID" in w, "le workflow ne revérifie pas le demandeur"
    assert "nuntius.py" in w, "le workflow n'execute pas la commande"
    assert "journal.jsonl" in w, "le workflow ne pousse pas le journal des decisions"


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
    print("\n%s" % ("TOUTES LES PORTES TELEGRAM SONT VERTES" if not echecs
                    else "%d PORTE(S) TELEGRAM EN ECHEC" % echecs))
    return 1 if echecs else 0

def test_t48_bloc_de_directive_sans_commande():
    """L'operateur colle son bloc, il ne tape pas /directive devant."""
    bloc = "plateformes: youtube_shorts, instagram_reels\ntaux: 0.6\nbudget: 2500"
    d = parse.analyser(_up(bloc), [OPERATEUR])
    assert d["action"] == "dispatch", "un bloc colle doit etre reconnu"
    assert d["commande"] == "/directive"
    assert "taux: 0.6" in d["arguments"], "le bloc doit passer entier, pas la 1re ligne"

    libre = parse.analyser(_up("salut, ca va ?"), [OPERATEUR])
    assert libre["action"] == "repondre", "un texte libre n'est pas une directive"


def test_t49_watermark_refuse_ce_qui_n_est_pas_une_image():
    import watermark

    tmp = RACINE / ".tmp"
    tmp.mkdir(exist_ok=True)
    faux = tmp / "pas_une_image.png"
    faux.write_text("ceci est du texte", encoding="utf-8")
    try:
        watermark.verifier_image(faux)
        raise AssertionError("un fichier texte ne doit pas passer pour un watermark")
    except watermark.Refus as e:
        assert "entete" in str(e) or "image" in str(e)
    vide = tmp / "vide.png"
    vide.write_bytes(b"")
    try:
        watermark.verifier_image(vide)
        raise AssertionError("un fichier vide doit etre refuse")
    except watermark.Refus as e:
        assert "vide" in str(e)
    faux.unlink(missing_ok=True)
    vide.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(_main())

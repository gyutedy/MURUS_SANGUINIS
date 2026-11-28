"""Contrat de commandes du bot MURUS — miroir testable du Worker Cloudflare.

Ce fichier est la reference : le Worker (`LISTEN/src/index.js`) applique exactement
les memes regles, et `tests/test_nuntius_telegram.py` les verifie ici, sans reseau.

Regles, dans l'ordre (et l'ordre compte) :
  1. pas de chat -> ignore ;
  2. chat hors liste blanche -> ignore, et on le note (aucune reponse : pas de fuite) ;
  3. texte vide + photo -> on explique la forme attendue ;
  4. pas de "/" -> on repond le mode d'emploi court ;
  5. commande inconnue -> on refuse en la nommant ;
  6. acte irreversible -> il faut la PHRASE COMPLETE tapee a la main ;
  7. sinon -> dispatch, avec `update_id` pour rendre le rejeu impossible.
"""
from __future__ import annotations

import re

# Actes qui ne se reparent pas : on ne les declenche pas d'un bouton ni d'un mot.
# (Les rendus ne sont PAS dans cette liste : l'operateur a refuse cette serrure.)
ACTES_IRREVERSIBLES = {"publier"}

PHRASE_PUBLICATION = re.compile(r"^VALIDER\s+PUBLICATION\s+[A-Z0-9_]+\s+[A-Z]\d{2}$")

# commande -> workflow GitHub a declencher (le Worker ne connait qu'une table)
WORKFLOW = {
    "etat": None, "clips": None, "rapport": None, "aide": None, "parcours": None,
    "verdict": None, "lancer": None, "campagne": None, "directive": None,
    "rendu": "murus_rendu.yml", "vive": "v2_vive.yml",
    "publier": "v2_publish.yml", "stop": None,
}
NOMS_ATTENDUS = {
    "etat": "etat des runs", "clips": "les livrables", "rapport": "rapport d'un clip",
    "parcours": "ou en est la chaine et ce qui attend ton verdict",
    "verdict": "valider ou refuser la sortie d'une fregate",
    "lancer": "ouvrir une fregate (siege, look, postprod, livraison)",
    "campagne": "voir, activer ou desactiver une campagne",
    "directive": "recevoir un bloc de directive et le repartir",
    "rendu": "lancer les 9 clips (mode non-live)",
    "vive": "lancer la coupe par le moteur (mode live)",
    "publier": "programmer une publication",
    "stop": "arreter un run", "aide": "le mode d'emploi",
}
ARGUMENTS_REQUIS = {"rapport": True, "verdict": True, "lancer": True}
ARGUMENTS_AUTORISES = {"rapport", "publier", "stop", "verdict", "parcours", "lancer",
                       "campagne", "directive"}

AIDE = (
    "MURUS — commandes\n"
    "/etat — ce qui tourne, ce qui a echoue\n"
    "/clips — les livrables LUTH_A0x_final.mp4\n"
    "/rapport A01 — synchro mesuree, qa_pass, durees\n"
    "/rendu — lance les 9 clips\n"
    "/stop <run> — arrete un run\n"
    "/publier — voir la phrase de validation complete\n"
    "/aide — ce message"
)


def _chat(update):
    msg = (update or {}).get("message") or (update or {}).get("edited_message") or {}
    return msg, ((msg.get("chat") or {}).get("id"))


def _texte(msg):
    return str(msg.get("text") or msg.get("caption") or "")


def _photo(msg):
    photos = msg.get("photo") or []
    if photos:
        return max(photos, key=lambda p: p.get("file_size") or 0).get("file_id")
    doc = msg.get("document") or {}
    mime = str(doc.get("mime_type") or "").lower()
    nom = str(doc.get("file_name") or "").lower()
    if doc.get("file_id") and (mime.startswith("image/") or re.search(r"\.(png|jpe?g|webp)$", nom)):
        return doc.get("file_id")
    return None


def decouper(texte):
    """Rend (nom, arguments). Les lignes suivantes sont CONSERVEES.

    `/directive` recoit un BLOC : ne garder que la premiere ligne reviendrait a
    ignorer la moitie de ce que l'operateur a ecrit.
    """
    brut = str(texte or "").strip()
    if not brut.startswith("/"):
        return None, ""
    premiere, _, reste = brut.partition(chr(10))
    morceaux = premiere.split()
    nom = morceaux[0][1:]
    if "@" in nom:
        nom = nom.split("@")[0]
    arguments = " ".join(morceaux[1:]).strip()
    if reste.strip():
        arguments = (arguments + chr(10) + reste.strip()).strip()
    return nom.lower(), arguments


def analyser(update, autorises):
    """Rend une decision : {action, ...}. Jamais d'exception sur une entree tordue."""
    msg, chat_id = _chat(update)
    if not chat_id:
        return {"action": "ignore", "raison": "sans_chat"}
    chat_id = str(chat_id)
    autorises = {str(a) for a in (autorises or []) if str(a).strip()}
    if chat_id not in autorises:
        return {"action": "ignore", "raison": "chat_etranger", "chat_id": chat_id}

    texte = _texte(msg)
    photo = _photo(msg)
    if not texte.strip():
        if photo:
            return {"action": "repondre", "chat_id": chat_id, "raison": "photo_sans_commande",
                    "texte": "Photo recue sans commande. Envoie-la avec la legende /capture."}
        return {"action": "ignore", "raison": "vide", "chat_id": chat_id}

    nom, arguments = decouper(texte)
    if not nom:
        return {"action": "repondre", "chat_id": chat_id, "raison": "pas_une_commande",
                "texte": "Commande inconnue. /aide pour la liste."}
    if nom not in NOMS_ATTENDUS:
        return {"action": "repondre", "chat_id": chat_id, "raison": "inconnue",
                "texte": "Commande inconnue : /%s. /aide pour la liste." % nom}
    if nom == "aide":
        return {"action": "repondre", "chat_id": chat_id, "raison": "aide", "texte": AIDE}

    if ARGUMENTS_REQUIS.get(nom) and not arguments:
        return {"action": "repondre", "chat_id": chat_id, "raison": "argument_manquant",
                "texte": "Il manque l'argument : /%s A01 par exemple." % nom}
    if arguments and nom not in ARGUMENTS_AUTORISES:
        return {"action": "repondre", "chat_id": chat_id, "raison": "argument_inutile",
                "texte": "/%s ne prend pas d'argument." % nom}

    if nom in ACTES_IRREVERSIBLES:
        # La phrase remplace le contenu de la commande : on ne publie que sur un acte
        # tape en entier, jamais sur un mot seul recopie par habitude.
        if nom == "publier" and not PHRASE_PUBLICATION.match(arguments.strip()):
            return {"action": "repondre", "chat_id": chat_id, "raison": "phrase_absente",
                    "texte": ("Publication non declenchee. Ecris la phrase complete, "
                              "tapée a la main : VALIDER PUBLICATION PREME A01")}

    return {
        "action": "dispatch",
        "chat_id": chat_id,
        "commande": "/" + nom,
        "arguments": arguments,
        "workflow": WORKFLOW.get(nom),
        "update_id": (update or {}).get("update_id"),
        "message_id": msg.get("message_id"),
    }

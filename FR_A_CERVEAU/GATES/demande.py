"""DEMANDE A L'OPERATEUR — le projet demande, il ne decide pas.

POURQUOI CE MODULE EXISTE
    Deux faits appartiennent a l'operateur et a personne d'autre :
      - le NOMBRE de clips d'un siege (le CDC plafonne a 15) ;
      - la VALIDATION de la selection M1 (quels moments, avec leur force).
    Avant, ces valeurs etaient choisies par defaut dans un workflow : l'operateur
    n'avait rien valide et rien ne le signalait. C'est exactement ce qu'une porte
    humaine doit interdire.

PATTERN
    Identique a l'ORACLE de MARK1 (M00C_METADATA/overlay.py) — ecrire un pending
    lisible, puis REFUSER de continuer tant qu'il n'y a pas de reponse :
        ARCHIVUM/demande/pending/<cle>.json     <- la question, posee par le projet
        ARCHIVUM/demande/answers.json           <- la reponse, ecrite par l'operateur

CE QUE CE MODULE NE FAIT PAS
    Aucune valeur par defaut, aucune valeur inventee : sans reponse, `exiger`
    rend (False, None, motif) et l'appelant doit s'arreter.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

REL_DIR = "ARCHIVUM/demande"
PENDING = "pending"
ANSWERS = "answers.json"


def _root(root=None):
    return str(root) if root else os.getcwd()


def chemin_pending(cle, root=None):
    return os.path.join(_root(root), REL_DIR, PENDING, "%s.json" % cle)


def chemin_answers(root=None):
    return os.path.join(_root(root), REL_DIR, ANSWERS)


def demander(cle, question, pourquoi="", attendu=None, plafond=None,
             payload=None, root=None):
    """Ecrit la question. Rend le chemin du pending (a montrer a l'operateur)."""
    path = chemin_pending(cle, root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc = {
        "cle": cle,
        "question": question,
        "pourquoi": pourquoi,
        "attendu": attendu or "valeur",
        "plafond": plafond,
        "posee_le": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reponse_dans": os.path.join(REL_DIR, ANSWERS),
        "forme": {"answers": {cle: "<votre reponse>"}},
        "payload": payload or {},
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
    return path


def reponses(root=None):
    path = chemin_answers(root)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except ValueError:
        return {}
    out = data.get("answers") if isinstance(data, dict) else None
    return out if isinstance(out, dict) else {}


def exiger(cle, plafond=None, root=None):
    """Rend (ok, valeur, motif). Aucune valeur par defaut n'est fabriquee."""
    val = reponses(root).get(cle)
    if val is None or (isinstance(val, str) and not val.strip()):
        return False, None, "reponse absente : %s" % cle
    if plafond is not None:
        try:
            n = int(val)
        except (TypeError, ValueError):
            return False, None, "%s doit etre un entier (recu %r)" % (cle, val)
        if n < 1:
            return False, None, "%s doit etre >= 1" % cle
        if n > plafond:
            return False, None, "%s=%d depasse le plafond %d" % (cle, n, plafond)
        return True, n, "ok"
    return True, val, "ok"

"""Applique un bloc de directive recu de l'operateur, sans rien deviner.

L'operateur colle un bloc (ou le dicte a Telegram) ; chaque ligne est une cle `cle: valeur`.
Ce fichier met **chaque information a sa place** :
  - les regles du client -> `ARCHIVUM/campaign/campaign_directive.json`
  - les declarations de l'operateur -> `ARCHIVUM/campaign/operator_declarations.json`

Deux regles, non negociables :
  1. une cle inconnue est **refusee** (sinon une faute de frappe est ignoree en silence) ;
  2. une valeur vide n'efface rien : elle est refusee. Pour retirer une declaration,
     on le dit explicitement (`focus: non`), on n'ecrit pas du vide.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
DIRECTIVE = RACINE / "ARCHIVUM" / "campaign" / "campaign_directive.json"
DECLARATIONS = RACINE / "ARCHIVUM" / "campaign" / "operator_declarations.json"
JOURNAL = RACINE / "ARCHIVUM" / "campaign" / "directive_journal.jsonl"


class Refus(Exception):
    """Un bloc inapplicable. Jamais applique a moitie."""


def maintenant():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _lire(chemin):
    if not chemin.exists():
        return {}
    return json.loads(chemin.read_text(encoding="utf-8"))


def _ecrire(chemin, d):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _liste(texte):
    return [x.strip() for x in str(texte).replace(";", ",").split(",") if x.strip()]


def _nombre(texte, quoi):
    try:
        return float(str(texte).replace(",", "."))
    except ValueError:
        raise Refus("%s doit etre un nombre, recu : %s" % (quoi, texte))


def _oui_non(texte, quoi):
    t = str(texte).strip().lower()
    if t in ("oui", "yes", "true", "vrai", "1"):
        return True
    if t in ("non", "no", "false", "faux", "0"):
        return False
    raise Refus("%s attend oui ou non, recu : %s" % (quoi, texte))


# cle -> (fichier cible, chemin dans le json, conversion)
CLES = {
    "star": (DECLARATIONS, ("star",), lambda v: str(v).strip()),
    "campaign_id": (DIRECTIVE, ("campaign_id",), lambda v: str(v).strip()),
    "createur": (DIRECTIVE, ("creator_name",), lambda v: str(v).strip()),
    "langue": (DIRECTIVE, ("language",), lambda v: str(v).strip()),
    "plateformes": (DIRECTIVE, ("platforms",), _liste),
    "requirements": (DIRECTIVE, ("requirements",), lambda v: [x.strip() for x in str(v).split("|") if x.strip()]),
    "banned": (DIRECTIVE, ("banned",), lambda v: [x.strip() for x in str(v).split("|") if x.strip()]),
    "taux": (DECLARATIONS, ("campaign", "rate_usd_per_1k"), lambda v: _nombre(v, "taux")),
    "budget": (DECLARATIONS, ("campaign", "budget_remaining_usd"), lambda v: _nombre(v, "budget")),
    "financee": (DECLARATIONS, ("campaign", "funded"), lambda v: _oui_non(v, "financee")),
    "compte": (DECLARATIONS, ("account", "warmup_days"), lambda v: int(_nombre(v, "compte"))),
    "focus": (DECLARATIONS, ("focus_declared",), lambda v: _oui_non(v, "focus")),
    "watermark": (DIRECTIVE, ("watermark", "file"), lambda v: str(v).strip()),
}


def analyser_bloc(bloc):
    """Transforme un bloc texte en liste d'operations. Refuse au premier probleme."""
    operations = []
    inconnues = []
    for brute in str(bloc or "").splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("#"):
            continue
        if ":" not in ligne:
            raise Refus("ligne sans cle ni valeur : %s" % ligne[:60])
        cle, valeur = ligne.split(":", 1)
        cle, valeur = cle.strip().lower(), valeur.strip()
        if cle not in CLES:
            inconnues.append(cle)
            continue
        if valeur == "":
            raise Refus("la cle %s est vide : une valeur vide n'efface rien, ecris ce que tu veux" % cle)
        fichier, chemin, conv = CLES[cle]
        operations.append({"cle": cle, "fichier": fichier.name, "chemin": chemin,
                           "valeur": conv(valeur), "brut": valeur})
    if inconnues:
        raise Refus("cles inconnues refusees : %s (connues : %s)"
                    % (", ".join(inconnues), ", ".join(sorted(CLES))))
    if not operations:
        raise Refus("bloc vide : rien a appliquer")
    return operations


def appliquer(bloc, source="operateur", quand=None, directe=None, declarations=None,
              journal=None):
    """Applique le bloc. Ecrit une ligne de journal par information posee."""
    operations = analyser_bloc(bloc)
    fichiers = {
        DIRECTIVE.name: dict(_lire(Path(directe) if directe else DIRECTIVE)),
        DECLARATIONS.name: dict(_lire(Path(declarations) if declarations else DECLARATIONS)),
    }
    jour = []
    for op in operations:
        cible = fichiers[op["fichier"]]
        noeud = cible
        for cran in op["chemin"][:-1]:
            noeud = noeud.setdefault(cran, {})
        noeud[op["chemin"][-1]] = op["valeur"]
        jour.append({"quand": quand or maintenant(), "cle": op["cle"],
                     "fichier": op["fichier"], "valeur": op["valeur"], "source": source})
    # on n'ecrit qu'a la fin : un bloc refuse n'a rien pose
    _ecrire(Path(directe) if directe else DIRECTIVE, fichiers[DIRECTIVE.name])
    _ecrire(Path(declarations) if declarations else DECLARATIONS, fichiers[DECLARATIONS.name])
    chemin_journal = Path(journal) if journal else JOURNAL
    chemin_journal.parent.mkdir(parents=True, exist_ok=True)
    with chemin_journal.open("a", encoding="utf-8") as f:
        for ligne in jour:
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    return jour


def resume(directe=None, declarations=None):
    """Ce qui est declare, et ce qui manque — pour repondre a /directive sans bloc."""
    d = _lire(Path(directe) if directe else DIRECTIVE)
    decl = _lire(Path(declarations) if declarations else DECLARATIONS)
    campaign = decl.get("campaign") or {}
    manques = [nom for nom, val in (
        ("taux", campaign.get("rate_usd_per_1k")),
        ("budget", campaign.get("budget_remaining_usd")),
        ("financee", campaign.get("funded")),
        ("compte", (decl.get("account") or {}).get("warmup_days")),
        ("focus", decl.get("focus_declared")),
    ) if val in (None, "")]
    lignes = [
        "Campagne : %s (%s)" % (d.get("creator_name") or "?", d.get("campaign_id") or "?"),
        "Plateformes : %s" % ", ".join(d.get("platforms") or []),
        "Requirements : %d · Violations : %d"
        % (len(d.get("requirements") or []), len(d.get("banned") or [])),
        "Taux declare : %s USD/1k · budget %s · financee %s"
        % (campaign.get("rate_usd_per_1k"), campaign.get("budget_remaining_usd"),
           campaign.get("funded")),
        "Declarations manquantes : %s" % (", ".join(manques) or "aucune"),
    ]
    return "\n".join(lignes), manques

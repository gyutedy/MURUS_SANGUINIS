"""Registre des campagnes — une seule active a la fois, tout le projet le lit.

Pourquoi ce fichier existe : le projet peut recevoir plusieurs campagnes GAGNEES
(celle de Preme, une autre demain). Il doit savoir **pour qui il travaille** sans
qu'on le lui redise a chaque run, et il doit refuser de travailler sur deux a la fois.

Trois objets distincts, a ne jamais confondre :

  - le TOKEN DE CAMPAGNE  : identifie la campagne, stable, taille une fois ;
  - le TOKEN DE PACK      : identifie un siege (un pack de N clips) dans la campagne ;
  - l'IDENTIFIANT DE CLIP : A01..A15 a l'interieur d'un pack.

La cle de publication complete est donc `campagne:token_pack:clip`, ce qui rend un
doublon impossible meme si deux campagnes utilisent `A01`.

Fichiers :
  REVIEW/campagnes.json            l'etat courant (lisible, commite)
  ARCHIVUM/campagnes/journal.jsonl  l'historique des actes (append-only, jamais reecrit)
"""
from __future__ import annotations

import json
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
ETAT = RACINE / "REVIEW" / "campagnes.json"
JOURNAL = RACINE / "ARCHIVUM" / "campagnes" / "journal.jsonl"


class Refus(Exception):
    """Un acte impossible. Le message dit toujours pourquoi."""


def maintenant():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def charger(etat=None):
    chemin = Path(etat or ETAT)
    if not chemin.exists():
        return {"actif": None, "campagnes": {}}
    try:
        d = json.loads(chemin.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise Refus("registre illisible (%s) : on ne devine pas l'etat" % e)
    d.setdefault("campagnes", {})
    d.setdefault("actif", None)
    return d


def ecrire(d, etat=None):
    chemin = Path(etat or ETAT)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return chemin


def noter(**evenement):
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    evenement.setdefault("quand", maintenant())
    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evenement, ensure_ascii=False) + "\n")
    return evenement


def nommer(star, token=None):
    """Le nom interne : la star en majuscules. `Preme` -> `PREME`."""
    nom = str(star or "").strip().upper().replace(" ", "_")
    if not nom:
        raise Refus("une campagne a besoin du nom de sa star")
    return nom


def creer(star, token=None, campaign_id=None, platforms=None, directive=None, etat=None):
    """Declare une nouvelle campagne. Le token est taille ici s'il n'est pas donne."""
    nom = nommer(star)
    d = charger(etat)
    if nom in d["campagnes"]:
        raise Refus("la campagne %s existe deja (token %s)"
                    % (nom, d["campagnes"][nom].get("token")))
    token = (token or secrets.token_hex(4)).lower()
    for autre, c in d["campagnes"].items():
        if c.get("token") == token:
            raise Refus("ce token est deja celui de %s : un token identifie UNE campagne" % autre)
    d["campagnes"][nom] = {
        "star": str(star).strip(),
        "token": token,
        "campaign_id": campaign_id or ("%s_CLIPIFY_OPEN" % nom),
        "statut": "inactive",
        "cree": maintenant(),
        "platforms": list(platforms or []),
        "directive": directive or "ARCHIVUM/campaign/campaign_directive.json",
    }
    ecrire(d, etat)
    noter(acte="creer", campagne=nom, token=token)
    return d["campagnes"][nom]


def resoudre(reference, etat=None):
    """Retrouve une campagne par son nom OU son token. Leve si ambigu ou absent."""
    d = charger(etat)
    ref = str(reference or "").strip()
    if not ref:
        raise Refus("il manque la campagne : donne son nom ou son token")
    par_nom = d["campagnes"].get(ref.upper().replace(" ", "_"))
    if par_nom:
        return par_nom
    par_token = [c for c in d["campagnes"].values() if c.get("token") == ref.lower()]
    if len(par_token) == 1:
        return par_token[0]
    if len(par_token) > 1:
        raise Refus("token %s partage par plusieurs campagnes : registre incoherent" % ref)
    raise Refus("campagne inconnue : %s (connues : %s)"
                % (ref, ", ".join(sorted(d["campagnes"])) or "aucune"))


def nom_de(campagne, etat=None):
    d = charger(etat)
    for nom, c in d["campagnes"].items():
        if c.get("token") == campagne.get("token"):
            return nom
    return None


def _reference_dans(d, reference):
    """Resout DANS le registre deja charge : sinon on modifie une copie et l'etat
    ecrit ne contient pas l'acte (panne du 2026-11-28)."""
    ref = str(reference or "").strip()
    if not ref:
        raise Refus("il manque la campagne : donne son nom ou son token")
    nom = ref.upper().replace(" ", "_")
    if nom in d["campagnes"]:
        return nom, d["campagnes"][nom]
    trouves = [(n, c) for n, c in d["campagnes"].items() if c.get("token") == ref.lower()]
    if len(trouves) == 1:
        return trouves[0]
    if len(trouves) > 1:
        raise Refus("token %s partage par plusieurs campagnes : registre incoherent" % ref)
    raise Refus("campagne inconnue : %s (connues : %s)"
                % (ref, ", ".join(sorted(d["campagnes"])) or "aucune"))


def activer(reference, etat=None, par="operateur"):
    """Active une campagne et desactive les autres DANS LE MEME ECRITURE.

    Si le disque s'arrete au milieu, on ne se retrouve pas avec deux actives : l'etat
    est ecrit une seule fois, avec une seule active.
    """
    d = charger(etat)
    nom, c = _reference_dans(d, reference)
    desactivees = []
    for autre_nom, autre in d["campagnes"].items():
        if autre_nom != nom and autre.get("statut") == "actif":
            autre["statut"] = "inactive"
            desactivees.append(autre_nom)
    c["statut"] = "actif"
    c["active_le"] = maintenant()
    d["actif"] = nom
    ecrire(d, etat)
    noter(acte="activer", campagne=nom, token=c.get("token"), par=par,
          desactivees=desactivees)
    return c, desactivees


def desactiver(reference, etat=None, par="operateur"):
    d = charger(etat)
    nom, c = _reference_dans(d, reference)
    c["statut"] = "inactive"
    if d.get("actif") == nom:
        d["actif"] = None
    ecrire(d, etat)
    noter(acte="desactiver", campagne=nom, token=c.get("token"), par=par)
    return c


def actif(etat=None):
    """La campagne active, ou None. Aucune frigate ne doit inventer un defaut."""
    d = charger(etat)
    nom = d.get("actif")
    if not nom or nom not in d["campagnes"]:
        return None
    c = d["campagnes"][nom]
    return c if c.get("statut") == "actif" else None


def exiger_active(etat=None):
    """Pour les frigates qui n'ont aucun sens sans campagne : refuse clairement."""
    c = actif(etat)
    if c is None:
        raise Refus("aucune campagne active : dis /campagne <star> <token> go")
    return c


def cle_publication(token_campagne, token_pack, clip):
    """La cle qui rend un doublon impossible, meme entre deux campagnes."""
    return "%s:%s:%s" % (str(token_campagne).lower(), str(token_pack).lower(),
                         str(clip).strip().upper())


def etat_lisible(etat=None):
    d = charger(etat)
    lignes = ["Campagne active : %s" % (d.get("actif") or "AUCUNE"), ""]
    if not d["campagnes"]:
        lignes.append("(aucune campagne declaree)")
        return "\n".join(lignes)
    for nom, c in sorted(d["campagnes"].items()):
        marque = "ACTIVE" if c.get("statut") == "actif" else "inactive"
        lignes.append("%-10s %-8s star=%-10s token=%s" % (
            nom, marque, c.get("star") or "?", c.get("token") or "?"))
    return "\n".join(lignes)


def main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description="registre des campagnes")
    ap.add_argument("--etat", action="store_true")
    ap.add_argument("--creer", default=None, metavar="STAR")
    ap.add_argument("--token", default=None)
    ap.add_argument("--activer", default=None, metavar="NOM_OU_TOKEN")
    ap.add_argument("--desactiver", default=None, metavar="NOM_OU_TOKEN")
    args = ap.parse_args(argv)
    try:
        if args.creer:
            c = creer(args.creer, args.token)
            print("campagne creee : %s token=%s" % (c["star"], c["token"]))
        if args.activer:
            c, des = activer(args.activer)
            print("active : %s (desactivees : %s)" % (c["star"], ", ".join(des) or "aucune"))
        if args.desactiver:
            c = desactiver(args.desactiver)
            print("desactivee : %s" % c["star"])
        if args.etat or not any((args.creer, args.activer, args.desactiver)):
            print(etat_lisible())
        return 0
    except Refus as e:
        print("REFUS : %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())

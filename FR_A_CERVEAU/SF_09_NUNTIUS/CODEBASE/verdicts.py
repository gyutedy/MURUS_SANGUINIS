"""Registre des verdicts de l'operateur — append-only.

Le projet n'avance pas parce qu'une fregate a fini : il avance parce que l'operateur
a **valide sa sortie**. Ce fichier porte cet acte.

Deux modes, deux chaines :
  non-live : siege -> look -> postprod -> rendu -> livraison
  live     : siege -> vive -> livraison

Une fregate ne peut s'ouvrir que si l'amont porte un verdict `valide` **sur la meme
sortie** (meme hash, meme jeton). Si la sortie change, le verdict precedent ne vaut
plus rien : on ne valide pas un pack puis on en rend un autre.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
REGISTRE = RACINE / "REVIEW" / "verdicts.jsonl"

CHAINES = {
    "non-live": ["siege", "look", "postprod", "rendu", "livraison"],
    "live": ["siege", "vive", "livraison"],
}
VERDICTS = ("valide", "refuse")


class Refus(Exception):
    """Un acte impossible. Jamais silencieux : le message dit pourquoi."""


def maintenant():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def entrees(registre=None):
    chemin = Path(registre or REGISTRE)
    if not chemin.exists():
        return []
    sortie = []
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        if ligne.strip():
            try:
                sortie.append(json.loads(ligne))
            except json.JSONDecodeError:
                continue          # une ligne illisible ne detruit pas l'historique
    return sortie


def dernier(campagne, fregate, registre=None):
    """Dernier verdict pour cette fregate : le plus recent gagne."""
    trouves = [e for e in entrees(registre)
               if e.get("campagne") == campagne and e.get("fregate") == fregate]
    return trouves[-1] if trouves else None


def peut_ouvrir(campagne, fregate, mode="non-live", sortie=None, registre=None):
    """Rend (True, raison) ou (False, raison). Ne leve pas : les portes aiment savoir."""
    chaine = CHAINES.get(mode)
    if chaine is None:
        return False, "mode inconnu : %s (attendu : %s)" % (mode, ", ".join(CHAINES))
    if fregate not in chaine:
        return False, "fregate %s absente du mode %s" % (fregate, mode)
    rang = chaine.index(fregate)
    if rang == 0:
        return True, "premiere fregate du mode %s : rien a valider en amont" % mode
    amont = chaine[rang - 1]
    v = dernier(campagne, amont, registre)
    if v is None:
        return False, "aucun verdict pour %s : %s ne peut pas s'ouvrir" % (amont, fregate)
    if v.get("verdict") != "valide":
        return False, "%s a ete REFUSE (%s) : %s reste ferme" % (
            amont, v.get("motif") or "sans motif", fregate)
    if sortie is not None and v.get("sortie") != sortie:
        return False, ("%s a ete valide sur la sortie %s, pas sur %s : un verdict ne "
                       "couvre pas une autre sortie" % (amont, v.get("sortie"), sortie))
    return True, "%s valide sur %s" % (amont, v.get("sortie"))


def enregistrer(campagne, fregate, verdict, sortie, motif="", par="operateur",
                mode="non-live", registre=None, quand=None):
    """Ecrit un acte. Leve Refus si l'acte n'a pas de sens."""
    if verdict not in VERDICTS:
        raise Refus("verdict inconnu : %s (attendu : %s)" % (verdict, " ou ".join(VERDICTS)))
    chaine = CHAINES.get(mode)
    if chaine is None:
        raise Refus("mode inconnu : %s" % mode)
    if fregate not in chaine:
        raise Refus("fregate %s absente du mode %s" % (fregate, mode))
    if not str(sortie or "").strip():
        raise Refus("aucune sortie declaree : un verdict sans sortie ne prouve rien")
    ligne = {
        "quand": quand or maintenant(),
        "campagne": campagne,
        "mode": mode,
        "fregate": fregate,
        "sortie": str(sortie).strip(),
        "verdict": verdict,
        "par": par,
        "motif": str(motif or "").strip(),
    }
    chemin = Path(registre or REGISTRE)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    return ligne


def etat(campagne, mode="non-live", registre=None):
    """Rend la chaine avec, pour chaque fregate, son dernier verdict."""
    lignes = []
    for fregate in CHAINES.get(mode, []):
        v = dernier(campagne, fregate, registre)
        lignes.append({
            "fregate": fregate,
            "verdict": (v or {}).get("verdict") or "en_attente",
            "sortie": (v or {}).get("sortie"),
            "quand": (v or {}).get("quand"),
        })
    return lignes


def main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description="registre des verdicts de l'operateur")
    ap.add_argument("--campagne", default="PREME")
    ap.add_argument("--mode", default="non-live", choices=sorted(CHAINES))
    ap.add_argument("--etat", action="store_true", help="affiche la chaine et ses verdicts")
    ap.add_argument("--peut", default=None, metavar="FREGATE",
                    help="dit si cette fregate peut s'ouvrir")
    ap.add_argument("--sortie", default=None)
    ap.add_argument("--verdict", choices=VERDICTS, default=None)
    ap.add_argument("--fregate", default=None)
    ap.add_argument("--motif", default="")
    args = ap.parse_args(argv)

    if args.etat:
        for l in etat(args.campagne, args.mode):
            print("%-10s %-12s %s" % (l["fregate"], l["verdict"], l["sortie"] or "-"))
        return 0
    if args.peut:
        ok, raison = peut_ouvrir(args.campagne, args.peut, args.mode, args.sortie)
        print(("OUVERT  " if ok else "FERME   ") + raison)
        return 0 if ok else 1
    if args.verdict and args.fregate:
        try:
            ligne = enregistrer(args.campagne, args.fregate, args.verdict,
                                args.sortie or "", args.motif, mode=args.mode)
        except Refus as e:
            print("REFUS : %s" % e)
            return 2
        print("ACTE : %s %s sur %s" % (ligne["fregate"], ligne["verdict"], ligne["sortie"]))
        return 0
    print("rien a faire : --etat, --peut <fregate> ou --verdict avec --fregate")
    return 2


if __name__ == "__main__":
    sys.exit(main())

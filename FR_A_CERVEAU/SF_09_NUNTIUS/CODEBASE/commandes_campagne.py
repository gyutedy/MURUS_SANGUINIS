"""Commandes /campagne et /directive — la campagne et ses declarations.

/campagne                      l'etat : quelle campagne est active, lesquelles existent
/campagne <star> <token>       l'etat detaille de cette campagne
/campagne <star> <token> go    activer (et desactiver les autres dans le meme geste)
/campagne <star> <token> nogo  desactiver

/directive                     ce qui est declare, et ce qui manque
/directive <bloc cle: valeur>  appliquer un bloc, chaque info a sa place
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "SF_01_VIGILIA" / "CODEBASE"))

import campagnes  # noqa: E402
import directives  # noqa: E402

AIDE_CAMPAGNE = (
    "/campagne — la campagne active\n"
    "/campagne <star> <token> — l'etat de cette campagne\n"
    "/campagne <star> <token> go — l'activer (une seule active a la fois)\n"
    "/campagne <star> <token> nogo — la desactiver\n"
    "/campagne nouvelle <star> — declarer une campagne (token taille ici)")

AIDE_DIRECTIVE = (
    "/directive — ce qui est declare et ce qui manque\n"
    "/directive puis un bloc, une info par ligne :\n"
    "  plateformes: youtube_shorts, instagram_reels\n"
    "  requirements: Preme point focal | watermark visible\n"
    "  taux: 0.6\n  budget: 2500\n  financee: oui\n  compte: 42\n  focus: oui")


def repondre_campagne(arguments, source="telegram"):
    morceaux = (arguments or "").split()
    if not morceaux:
        return campagnes.etat_lisible()

    if morceaux[0].lower() == "nouvelle":
        if len(morceaux) < 2:
            return AIDE_CAMPAGNE
        c = campagnes.creer(morceaux[1], token=morceaux[2] if len(morceaux) > 2 else None)
        return ("Campagne declaree : %s (star %s), token %s.\nActive-la avec : "
                "/campagne %s %s go" % (morceaux[1], c["star"], c["token"],
                                        morceaux[1], c["token"]))

    reference = morceaux[0]
    token = morceaux[1] if len(morceaux) > 1 and morceaux[1].lower() not in ("go", "nogo") else None
    intention = morceaux[-1].lower() if len(morceaux) > 1 else ""

    try:
        c = campagnes.resoudre(reference if not token else token)
    except campagnes.Refus:
        # on accepte aussi "star token" : la star par son nom, le token pour prouver
        cible = None
        try:
            candidat = campagnes.resoudre(reference)
            if token and candidat.get("token") != token.lower():
                return ("Le token ne correspond pas a cette campagne. Refus : un token "
                        "prouve l'identite de la campagne.")
            cible = candidat
        except campagnes.Refus as e:
            return "REFUS : %s" % e
        c = cible

    if intention == "go":
        c, desactivees = campagnes.activer(c["token"], par=source)
        return ("Campagne ACTIVE : %s (token %s).%s"
                % (c["star"], c["token"],
                   (" Desactivees : %s." % ", ".join(desactivees)) if desactivees else ""))
    if intention == "nogo":
        c = campagnes.desactiver(c["token"], par=source)
        return "Campagne desactivee : %s (token %s). Aucune campagne active si c'etait la derniere." % (
            c["star"], c["token"])

    return ("Campagne %s — star %s, token %s, statut %s, campagne %s\nPlateformes : %s"
            % (c["star"], c["star"], c["token"], c.get("statut") or "?",
               c.get("campaign_id") or "?", ", ".join(c.get("platforms") or []) or "-"))


def repondre_directive(arguments, source="telegram"):
    bloc = (arguments or "").strip()
    if not bloc:
        texte, manques = directives.resume()
        return texte + ("\n\nRien n'est applique : envoie /directive suivi du bloc." if True else "")
    try:
        jour = directives.appliquer(bloc, source=source)
    except directives.Refus as e:
        return "REFUS : %s. Rien n'a ete applique." % e
    lignes = ["%d information(s) posee(s) :" % len(jour)]
    for ligne in jour:
        lignes.append("  %s -> %s" % (ligne["cle"], ligne["valeur"]))
    texte, manques = directives.resume()
    lignes.append("")
    lignes.append(texte)
    return "\n".join(lignes)

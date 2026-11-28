"""Commande /lancer : ouvrir une fregate, seulement si l'amont est valide.

Cet outil est le seul endroit ou une fregate est declenchee par le bot. Il ne
declenche jamais a l'aveugle : il demande d'abord au registre des verdicts si
l'amont porte un `valide` sur la meme sortie.

    /lancer siege <url>   -> murus_siege.yml      (premiere fregate : rien a valider)
    /lancer look          -> murus_preview_1.yml  (exige siege valide)
    /lancer postprod      -> murus_preview_2.yml  (exige look valide)
    /lancer livraison     -> murus_v7.yml         (exige rendu ou vive valide)

Le mode est deduit : la chaine live n'a pas de look/postprod.
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

DEPOT = "gyutedy/MURUS_SANGUINIS"
REF = "v2"

# fregate -> (workflow, amont exige, mode)
FREGATES = {
    "siege": ("murus_siege.yml", None, "non-live"),
    "look": ("murus_preview_1.yml", "siege", "non-live"),
    "postprod": ("murus_preview_2.yml", "look", "non-live"),
    "livraison": ("murus_v7.yml", "rendu", "non-live"),
}

FORMES = {
    "siege": "/lancer siege <url de la VOD>",
    "look": "/lancer look",
    "postprod": "/lancer postprod",
    "livraison": "/lancer livraison",
}


def _api(chemin, corps=None, jeton=None):
    jeton = jeton or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    url = "https://api.github.com" + chemin
    data = json.dumps(corps).encode() if corps is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET", headers={
        "Authorization": "Bearer %s" % jeton,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "murus-nuntius",
    })
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, r.read().decode()[:200]
    except Exception as e:  # noqa: BLE001
        return 0, "%s: %s" % (type(e).__name__, e)


def sortie_amont(fregate, verdicts, campagne="PREME", registre=None):
    """Ce sur quoi porte le verdict amont : le pack pour le siege, le run sinon."""
    amont = FREGATES[fregate][1]
    if amont is None:
        return None
    dernier = verdicts.dernier(campagne, amont, registre)
    return (dernier or {}).get("sortie") or {
        "siege": "pack:%s" % _pack_token(), "look": "codex:render",
        "rendu": "run:dernier", "vive": "run:dernier",
    }.get(amont)


def _pack_token():
    pack = Path(__file__).resolve().parents[3] / "REVIEW" / "pack_stage.json"
    if not pack.exists():
        return "?"
    try:
        return json.loads(pack.read_text(encoding="utf-8")).get("pack_token") or "?"
    except json.JSONDecodeError:
        return "?"


def entree(workflow, inputs):
    code, texte = _api("/repos/%s/actions/workflows/%s/dispatches" % (DEPOT, workflow),
                       corps={"ref": REF, "inputs": inputs})
    return code, texte


def lancer(arguments, verdicts, campagne="PREME", url_defaut=None, registre=None):
    """Rend le texte de reponse. Ne leve pas : une porte fermee se dit."""
    morceaux = (arguments or "").split()
    if not morceaux:
        return ("Forme attendue :\n" + "\n".join(FORMES.values()))
    fregate = morceaux[0].lower()
    if fregate not in FREGATES:
        return ("Fregate inconnue : %s. Possibles : %s"
                % (fregate, ", ".join(sorted(FREGATES))))

    workflow, amont, mode = FREGATES[fregate]
    if amont is not None:
        sortie = sortie_amont(fregate, verdicts, campagne, registre)
        ok, raison = verdicts.peut_ouvrir(campagne, fregate, mode, sortie, registre)
        if not ok:
            return "REFUS : %s. Rien n'a ete lance." % raison

    if fregate == "siege":
        url = morceaux[1] if len(morceaux) > 1 else (url_defaut or "")
        if not url.startswith("http"):
            return "Il manque le lien de la VOD : /lancer siege https://www.twitch.tv/videos/..."
        inputs = {"vod_url": url}
    elif fregate == "livraison":
        inputs = {"run_id": morceaux[1] if len(morceaux) > 1 else "", "compte": "clip_main"}
    else:
        inputs = {"vod_url": url_defaut or "https://www.twitch.tv/videos/2909800627",
                  "publish_pages": "oui"}

    code, texte = entree(workflow, inputs)
    if code == 204:
        return ("%s ouvert (%s). Suis avec /etat, puis porte ton verdict : "
                "/verdict %s valide <sortie>." % (fregate, workflow, fregate))
    return "%s refuse par GitHub (HTTP %s) : %s" % (fregate, code, texte)

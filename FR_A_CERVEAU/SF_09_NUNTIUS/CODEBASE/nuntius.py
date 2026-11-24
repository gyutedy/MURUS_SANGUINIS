"""NUNTIUS — execute une commande Telegram et repond. Tourne dans GitHub Actions.

Le Worker Cloudflare ne fait que relayer : il verifie le secret Telegram, la liste
blanche des chats, repond « recu », puis declenche ce workflow. Ici on execute
vraiment, on journalise, et on repond avec des faits.

Ce que ce fichier garantit :
  - `update_id` deja vu = **ignore** (un rejeu Telegram ne lance jamais deux fois) ;
  - chaque commande et son effet sont ecrits dans ARCHIVUM/telegram/journal.jsonl ;
  - une commande non cablee le dit, elle ne fait pas semblant (pas de faux succes) ;
  - le projet ne decide rien : il annonce un etat, et attend un acte humain.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
JOURNAL = RACINE / "ARCHIVUM" / "telegram" / "journal.jsonl"
PACK = RACINE / "REVIEW" / "pack_stage.json"
RAPPORT_RENDU = RACINE / "REVIEW" / "render" / "render_report.json"
DEPOT = "gyutedy/MURUS_SANGUINIS"


# ── outillage ────────────────────────────────────────────────────────────────

def maintenant():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def api(chemin, methode="GET", corps=None, jeton=None):
    jeton = jeton or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    url = "https://api.github.com" + chemin
    data = json.dumps(corps).encode() if corps is not None else None
    req = urllib.request.Request(url, data=data, method=methode, headers={
        "Authorization": "Bearer %s" % jeton,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "murus-nuntius",
    })
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            txt = r.read().decode() or "{}"
            return r.status, (json.loads(txt) if txt.strip().startswith(("{", "[")) else txt)
    except Exception as e:  # noqa: BLE001 - une panne d'API ne doit pas tuer le bot
        return 0, {"erreur": "%s: %s" % (type(e).__name__, e)}


def dire(texte, chat_id=None):
    """Envoie un message Telegram. Ne leve jamais : le journal garde la trace."""
    jeton = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.environ.get("TELEGRAM_OPERATEUR_ID")
    if not jeton or not chat_id:
        print("[NUNTIUS] Telegram non configure : message non envoye")
        return False
    corps = json.dumps({"chat_id": int(chat_id), "text": str(texte)[:3800],
                        "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(
        "https://api.telegram.org/bot%s/sendMessage" % jeton, data=corps,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status == 200
    except Exception as e:  # noqa: BLE001
        print("[NUNTIUS] envoi refuse : %s" % e)
        return False


# ── journal (append-only, rejeu impossible) ──────────────────────────────────

def deja_vu(update_id):
    if not JOURNAL.exists() or update_id in (None, ""):
        return False
    for ligne in JOURNAL.read_text(encoding="utf-8").splitlines():
        if not ligne.strip():
            continue
        try:
            if str(json.loads(ligne).get("update_id")) == str(update_id):
                return True
        except json.JSONDecodeError:
            continue
    return False


def noter(**evenement):
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    evenement.setdefault("quand", maintenant())
    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evenement, ensure_ascii=False) + "\n")
    return evenement


# ── lecture d'etat ───────────────────────────────────────────────────────────

def dernier_runs(n=5):
    code, d = api("/repos/%s/actions/runs?per_page=%d" % (DEPOT, n))
    if code != 200 or not isinstance(d, dict):
        return None, "API GitHub indisponible (%s)" % (d.get("erreur") if isinstance(d, dict) else code)
    lignes = []
    for r in d.get("workflow_runs") or []:
        lignes.append("%-34s %-9s %s" % (
            (r.get("name") or "?")[:34], r.get("conclusion") or r.get("status"),
            r.get("html_url")))
    return lignes, None


def cmd_etat(arguments, chat_id):
    lignes, mal = dernier_runs()
    if mal:
        return "Etat impossible : %s" % mal
    pack = json.loads(PACK.read_text(encoding="utf-8")) if PACK.exists() else {}
    entete = "Pack %s — %d assets signes" % (
        pack.get("pack_token") or "?", len(pack.get("assets") or []))
    return entete + "\n\n" + "\n".join(lignes)


def cmd_clips(arguments, chat_id):
    if not RAPPORT_RENDU.exists():
        return "Aucun rapport de rendu commite : lance /rendu, puis /clips."
    d = json.loads(RAPPORT_RENDU.read_text(encoding="utf-8"))
    rendus = d.get("rendus") or []
    if not rendus:
        return "Le rapport de rendu ne porte aucun livrable."
    return "%d livrable(s) :\n%s" % (len(rendus), "\n".join("  " + r for r in rendus))


def cmd_rapport(arguments, chat_id):
    clip = (arguments or "").strip().upper()
    if not clip:
        return "Quel clip ? /rapport A01"
    morceaux = []
    for chemin, quoi in ((RACINE / "REVIEW" / "render" / "%s.json" % clip.lower(), "rendu"),
                         (RACINE / "REVIEW" / "synchro" / ("%s.json" % clip.lower()), "synchro")):
        if chemin.exists():
            d = json.loads(chemin.read_text(encoding="utf-8"))
            if quoi == "synchro":
                morceaux.append("synchro : decalage %s s, derive %s s, verdict %s" % (
                    d.get("decalage_retenu_s"), d.get("derive_par_mot_s"), d.get("verdict")))
            else:
                morceaux.append("rendu : %s" % json.dumps(d, ensure_ascii=False)[:300])
    if not morceaux:
        return ("Aucun rapport commite pour %s. Les mesures existent dans les artefacts "
                "du run, pas encore dans le depot : dis-moi si tu veux que le rendu les "
                "commite." % clip)
    return "%s\n%s" % (clip, "\n".join(morceaux))


def cmd_rendu(arguments, chat_id):
    """Lance les 9 clips. Pas de serrure : l'operateur l'a refusee explicitement."""
    code, d = api("/repos/%s/actions/workflows/murus_rendu.yml/dispatches" % DEPOT,
                  methode="POST", corps={"ref": "v2", "inputs": {
                      "vod_url": "https://www.twitch.tv/videos/2909800627",
                      "nb_clips": "9", "clip_ids": ""}})
    if code == 204:
        return "Rendu lance : 9 clips, ref v2. Tu recevras l'etat avec /etat."
    return "Rendu refuse par GitHub (HTTP %s) : %s" % (code, json.dumps(d)[:200])


def cmd_stop(arguments, chat_id):
    run = (arguments or "").strip()
    if not run:
        return "Quel run ? /stop 45425091798"
    code, _ = api("/repos/%s/actions/runs/%s/cancel" % (DEPOT, run), methode="POST")
    return ("Run %s : arret demande (HTTP %s)." % (run, code))


def cmd_publier(arguments, chat_id):
    # Honnete : la publication n'est pas branchee, et le dire vaut mieux que simuler.
    return ("Publication non branchee : aucun jeton YouTube/Instagram valide n'a ete "
            "obtenu. Phrase recue : %s. Rien n'a ete programme." % (arguments or "-"))


COMMANDES = {
    "/etat": cmd_etat, "/clips": cmd_clips, "/rapport": cmd_rapport,
    "/rendu": cmd_rendu, "/stop": cmd_stop, "/publier": cmd_publier,
}


def main(argv=None):
    ap = argparse.ArgumentParser(description="execute une commande Telegram MURUS")
    ap.add_argument("--commande", required=True)
    ap.add_argument("--arguments", default="")
    ap.add_argument("--update-id", default="")
    ap.add_argument("--chat-id", default=None)
    args = ap.parse_args(argv)

    chat_id = args.chat_id or os.environ.get("TELEGRAM_OPERATEUR_ID")
    if deja_vu(args.update_id):
        print("[NUNTIUS] update_id %s deja traite : ignore (rejeu impossible)" % args.update_id)
        noter(commande=args.commande, update_id=args.update_id, chat_id=chat_id,
              effet="rejeu_ignore", resultat="ignore")
        return 0

    fonction = COMMANDES.get(args.commande)
    if fonction is None:
        reponse = "Commande non cablee cote projet : %s" % args.commande
        noter(commande=args.commande, arguments=args.arguments, update_id=args.update_id,
              chat_id=chat_id, effet="refus", resultat=reponse)
        dire(reponse, chat_id)
        return 0

    reponse = fonction(args.arguments, chat_id)
    envoye = dire(reponse, chat_id)
    noter(commande=args.commande, arguments=args.arguments, update_id=args.update_id,
          chat_id=chat_id, effet="execute", resultat="ok" if envoye else "non_envoye",
          reponse=reponse[:400])
    print("[NUNTIUS] %s -> %s" % (args.commande, "repondu" if envoye else "echec envoi"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

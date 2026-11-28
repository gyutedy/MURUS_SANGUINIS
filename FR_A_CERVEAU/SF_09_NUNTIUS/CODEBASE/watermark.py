"""Le watermark : le voir, le remplacer.

Le PNG du watermark est un **asset de campagne** : il vit dans
`ARCHIVUM/campaign/watermarks/`, il est declare dans la directive, et le rendu refuse
de partir s'il est absent (c'est le code qui le cherche, pas une convention).

On ne devine jamais son nom : on lit `watermark.file` dans la directive. Un fichier
absent est une erreur bruyante, pas un rendu sans watermark.
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
DIRECTIVE = RACINE / "ARCHIVUM" / "campaign" / "campaign_directive.json"
DOSSIER = RACINE / "ARCHIVUM" / "campaign" / "watermarks"
JOURNAL = RACINE / "ARCHIVUM" / "campaign" / "watermark_journal.jsonl"

EXTENSIONS = (".png", ".webp", ".jpg", ".jpeg")
TAILLE_MAX = 8 * 1024 * 1024        # 8 Mo : un watermark n'a aucune raison de peser plus


class Refus(Exception):
    pass


def nom_declare():
    if not DIRECTIVE.exists():
        return None
    d = json.loads(DIRECTIVE.read_text(encoding="utf-8"))
    wm = d.get("watermark") or {}
    return wm.get("file") or wm.get("png") or None


def chemin_declare():
    nom = nom_declare()
    if not nom:
        return None
    candidat = DOSSIER / nom
    if candidat.exists():
        return candidat
    for ext in EXTENSIONS:
        autre = DOSSIER / (Path(nom).stem + ext)
        if autre.exists():
            return autre
    return None


def verifier_image(chemin):
    """Un watermark doit etre une image et rester petit. Refus explicite sinon."""
    chemin = Path(chemin)
    if not chemin.exists():
        raise Refus("fichier introuvable : %s" % chemin)
    if chemin.suffix.lower() not in EXTENSIONS:
        raise Refus("format refuse (%s) : attendu %s"
                    % (chemin.suffix or "sans extension", ", ".join(EXTENSIONS)))
    taille = chemin.stat().st_size
    if taille == 0:
        raise Refus("fichier vide : un watermark vide n'en est pas un")
    if taille > TAILLE_MAX:
        raise Refus("fichier trop lourd (%.1f Mo, maximum %d Mo)"
                    % (taille / 1048576, TAILLE_MAX // 1048576))
    with chemin.open("rb") as f:
        entete = f.read(12)
    if entete.startswith(b"\x89PNG"):
        return "png"
    if entete.startswith(b"RIFF") and entete[8:12] == b"WEBP":
        return "webp"
    if entete.startswith(b"\xff\xd8"):
        return "jpeg"
    raise Refus("ce n'est pas une image (entete non reconnu) : %s" % chemin.name)


def telecharger(file_id, jeton=None, dest=None):
    """Telecharge un fichier Telegram (getFile puis file/bot<token>/<chemin>)."""
    jeton = jeton or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not jeton:
        raise Refus("TELEGRAM_BOT_TOKEN absent : impossible de recuperer la photo")
    url = "https://api.telegram.org/bot%s/getFile?file_id=%s" % (jeton, file_id)
    with urllib.request.urlopen(url, timeout=45) as r:
        d = json.loads(r.read().decode())
    if not d.get("ok"):
        raise Refus("Telegram refuse getFile : %s" % d.get("description"))
    chemin_tg = (d.get("result") or {}).get("file_path")
    if not chemin_tg:
        raise Refus("Telegram ne donne pas de chemin pour ce fichier")
    dest = Path(dest or (DOSSIER / "watermark_recu" / Path(chemin_tg).name))
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen("https://api.telegram.org/file/bot%s/%s" % (jeton, chemin_tg),
                                timeout=90) as r:
        dest.write_bytes(r.read())
    return dest


def poser(chemin, nom=None, source="telegram"):
    """Verifie, copie dans le dossier des watermarks, et declare dans la directive."""
    chemin = Path(chemin)
    format_lu = verifier_image(chemin)
    DOSSIER.mkdir(parents=True, exist_ok=True)
    nom = nom or "preme.png"
    if Path(nom).suffix.lower() not in EXTENSIONS:
        nom = Path(nom).stem + ".png"
    cible = DOSSIER / nom
    if chemin.resolve() != cible.resolve():
        cible.write_bytes(chemin.read_bytes())
    verifier_image(cible)
    d = json.loads(DIRECTIVE.read_text(encoding="utf-8")) if DIRECTIVE.exists() else {}
    d.setdefault("watermark", {})
    ancien = d["watermark"].get("file")
    d["watermark"]["file"] = nom
    d["watermark"]["format"] = format_lu
    d["watermark"]["declared_by"] = source
    DIRECTIVE.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"acte": "watermark", "fichier": nom, "format": format_lu,
                            "ancien": ancien, "source": source}, ensure_ascii=False) + "\n")
    return {"fichier": nom, "format": format_lu, "ancien": ancien,
            "octets": cible.stat().st_size}


def etat():
    nom = nom_declare()
    chemin = chemin_declare()
    if not nom:
        return "Aucun watermark declare dans la directive. Envoie une photo avec /watermark."
    if chemin is None:
        return ("Watermark declare (%s) mais le fichier est ABSENT de %s : le rendu "
                "refusera. Envoie la photo avec /watermark." % (nom, DOSSIER))
    return "Watermark : %s (%s, %.1f Ko) dans %s" % (
        chemin.name, chemin.suffix.lstrip("."), chemin.stat().st_size / 1024, DOSSIER)

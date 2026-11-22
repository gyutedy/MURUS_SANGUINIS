#!/usr/bin/env python3
"""FAISABILITE OVERLAY — la fenetre peut-elle porter un titre d'overlay valide ?

POURQUOI CE MODULE
    La regle anti-remplissage (TRACKING/DOCTRINE_ANTI_REMPLISSAGE.md) liste QUATRE
    conditions pour qu'un clip compte. La quatrieme -- « son overlay est accepte par
    le moteur » -- etait decouverte APRES M1 : M1 proposait 15 fenetres, puis M2B en
    refusait 8 et tout le siege s'arretait. Un clip qui ne peut pas porter d'overlay
    n'est pas un clip : il doit etre ecarte a M1, avec sa raison, et le manque doit
    etre annonce. C'est ce que fait ce module.

CE QU'IL NE FAIT PAS
    Il n'invente aucun titre. Il cherche si UNE suite de mots DU TEXTE peut passer les
    trois juges du moteur : title_forge.validate + S1 (via overlay.accept) et
    compliance.bait_report (soutien >= require_support_ratio). Si aucune ne passe,
    la fenetre est declaree infaisable — et on le dit.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

MARK1 = Path(__file__).resolve().parents[1] / "MARK1"

STOP = frozenset("""
the a an and or but to of in on at for with is are was were be been it its that this we you
i he she they me my your his her them so just like get got going gonna all out up down if as
do does did not no yeah oh what how when who
""".split())


def _charger(rel, nom):
    spec = importlib.util.spec_from_file_location(nom, MARK1 / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _cfg(root=None):
    base = Path(root).resolve() if root else Path.cwd()
    for cand in (MARK1 / "config/selection.json", base / "FR_A_CERVEAU/MARK1/config/selection.json"):
        if cand.exists():
            return json.loads(cand.read_text(encoding="utf-8"))
    raise FileNotFoundError("config/selection.json introuvable")


def _suite_de_mots(txt):
    """Suites de 2 a 4 mots consecutifs du texte : jamais un mot invente."""
    mots = re.findall(r"[a-z0-9']+", (txt or "").lower())
    vus, out = set(), []
    for n in (4, 3, 2):
        for i in range(len(mots) - n + 1):
            seq = mots[i:i + n]
            t = " ".join(seq)
            if t in vus or len(t) > 60 or any(x in STOP for x in seq):
                continue
            vus.add(t)
            out.append(t)
    return out


def faisable(source_text, cfg=None, root=None):
    """Rend (True, titre_retenu, []) ou (False, None, [raison]).

    `titre_retenu` est une suite de mots du texte qui passe les trois juges.
    """
    cfg = cfg or _cfg(root)
    import sys
    if str(MARK1) not in sys.path:
        sys.path.insert(0, str(MARK1))
    ov = _charger("M00C_METADATA/CODEBASE/overlay.py", "overlay_feasible")
    from libs import compliance

    from libs import s1_context
    marqueurs = tuple(s1_context.load_lang("en").get("stake") or ())

    raisons = {"accept": [], "bait": []}
    retenus = []
    for t in _suite_de_mots(source_text):
        ok, why = ov.accept(t, cfg, "en", "Preme", set())
        if not ok:
            raisons["accept"].extend(why[:1])
            continue
        b = compliance.bait_report(t, source_text, cfg)
        if not b.get("ok"):
            raisons["bait"].append(b.get("reason", ""))
            continue
        # Preference : un marqueur d'enjeu en MOT ENTIER (pas une sous-chaine du genre
        # 'day' dans 'today', ni 'lose' dans 'close'), puis plus de mots de contenu.
        mots = t.split()
        entier = sum(1 for m in marqueurs if any(m == w for w in mots))
        retenus.append((entier, len(mots), t))

    if retenus:
        retenus.sort(key=lambda x: (-x[0], -x[1], x[2]))
        return True, retenus[0][2], []

    if raisons["bait"]:
        return False, None, ["bait : %s" % raisons["bait"][0]]
    if raisons["accept"]:
        uniq = []
        for r in raisons["accept"]:
            if r not in uniq:
                uniq.append(r)
        return False, None, ["contraintes/S1 : %s" % ", ".join(uniq[:3])]
    return False, None, ["aucune suite de mots exploitable dans le texte"]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage : faisabilite_overlay.py \"texte du clip\"")
        raise SystemExit(2)
    ok, titre, why = faisable(sys.argv[1])
    print("faisable=%s titre=%r raisons=%s" % (ok, titre, why))

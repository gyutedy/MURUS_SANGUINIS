# PARCOURS UNIQUE — non-live et live, avec l'acte de l'operateur a chaque etape

> Document opposable. Il remplace la lecture eclatee de `PARCOURS_REEL.md` (V1) et
> `PARCOURS_V2.md` (vive, titres, calendrier). Si le code change et pas ce document,
> la CI le dit. Bilingue (EXC-M8) : EN puis FR.

Regle qui porte tout : **une fregate produit une sortie, l'operateur porte un verdict,
la fregate suivante n'ouvre qu'apres.** Ce n'est pas une serrure de plus : c'est deja
la doctrine du projet, elle est seulement ecrite ici en un seul endroit.

Registre : `REVIEW/verdicts.jsonl`, append-only, une ligne par acte.
Une fregate = un verdict = un hash de sortie. Si la sortie change, le verdict tombe.

---

## EN — Non-live mode (premium: title, glow, subtitles)

| # | step | frigate id | what runs | what the operator validates |
|---|------|-----------|-----------|-----------------------------|
| 0 | VOD link given | `siege` | transcription, M1 selection, 15 windows, `REVIEW/pack_stage.json` | the pack: the windows and their verbatim text |
| 1 | review 1 — LOOK | `look` | `murus_preview_1.yml` → Pages `/` | blur strength and background/core split, title size/place/colours/font, the single watermark and its place |
| 2 | codex 1 signed | `look` | export from review 1 | `validated_by_magos: true` → `REVIEW/codex_render.json` |
| 3 | review 2 — POSTPROD | `postprod` | `murus_preview_2.yml` → Pages `/preview2/` | glow preset on real parameters, subtitle style and word-by-word motion, LUT profile and intensity, fade |
| 4 | codex 2 signed | `postprod` | export from review 2 | `validated_by_magos: true` → `REVIEW/codex_postprod.json` |
| 5 | render | `rendu` | `murus_rendu.yml`, one job per clip | nothing technical (G1 checks both codex); the operator watches the 9 clips afterwards |
| 6 | delivery manifest | `livraison` | `murus_v7.yml` | `PORTE V7`: sha256, checklist, status `a_poster` |
| 7 | posting | — | human only | views 1h/24h, payout, campaign close |

Order is not negotiable: `postprod → camouflage → luther`, nothing re-encodes after
luther. Six operator acts, one per frigate, before anything can be delivered.

## EN — Live mode (engine cut: no title, no subtitles, no glow)

| # | step | frigate id | what runs | what the operator validates |
|---|------|-----------|-----------|-----------------------------|
| 0 | VOD link given | `siege` | same siege, same signed windows | the pack, exactly as in non-live |
| 1 | engine cut | `vive` | `v2_vive.yml` → signed windows cut by the vendored NeonClipping engine | `PORTE VIVE` declares `captions: false`, no title burned (D-5), no LLM, no browser, mapping not mute |
| 2 | purge | `vive` | SF_14 camouflage → SF_15 luther, same chain as premium | `qa_pass` on the batch report |
| 3 | delivery manifest | `livraison` | `murus_v7.yml` | `PORTE V7`, status `a_poster` |
| 4 | posting | — | human only | views, payout, close |

The two reviews **disappear** in live mode: there is nothing to judge because nothing
is burned. That is a declared trade, not an oversight: you lose the glow, the
subtitles and the title. Cost measured in `PARCOURS_V2.md`: each job downloads the
whole source (7.19 GB for this VOD), because "one job per clip" forbids sharing a
build artifact.

## EN — The verdict registry

`REVIEW/verdicts.jsonl`, append-only. One line:

    {"quand":"...","campagne":"PREME","fregate":"siege","sortie":"pack:70f120a8",
     "verdict":"valide","par":"operateur","motif":"15 fenetres retenues"}

Rules: a frigate may open only when its upstream carries `valide` **on the same
output**. A verdict never changes; a new act appends a new line that supersedes the
previous one for that frigate. Refusing is an act too: `refuse` blocks downstream and
stays in the history.

---

## FR — Mode non-live (premium : titre, glow, sous-titres)

| # | etape | fregate | ce qui tourne | ce que l'operateur valide |
|---|-------|---------|---------------|---------------------------|
| 0 | tu donnes le lien de la VOD | `siege` | transcription, selection M1, 15 fenetres, `REVIEW/pack_stage.json` | le pack : les fenetres et leur texte integral |
| 1 | revue 1 — LOOK | `look` | `murus_preview_1.yml` → Pages `/` | force du blur et partage fond/sujet, taille/place/couleurs/police du titre, watermark unique et sa place |
| 2 | codex 1 signe | `look` | export depuis la revue 1 | `validated_by_magos: true` → `REVIEW/codex_render.json` |
| 3 | revue 2 — POSTPROD | `postprod` | `murus_preview_2.yml` → Pages `/preview2/` | preset de glow sur de vrais parametres, style de sous-titres et motion mot par mot, profil de LUT et intensite, fade |
| 4 | codex 2 signe | `postprod` | export depuis la revue 2 | `validated_by_magos: true` → `REVIEW/codex_postprod.json` |
| 5 | rendu | `rendu` | `murus_rendu.yml`, un job par clip | rien de technique (G1 verifie les deux codex) ; tu regardes les 9 clips ensuite |
| 6 | manifeste de livraison | `livraison` | `murus_v7.yml` | `PORTE V7` : sha256, checklist, statut `a_poster` |
| 7 | tu postes | — | humain uniquement | vues 1 h/24 h, payout, cloture |

Six actes d'operateur, un par fregate, avant qu'une seule video soit livrable.

## FR — Mode live (moteur : pas de titre, pas de sous-titres, pas de glow)

| # | etape | fregate | ce qui tourne | ce que l'operateur valide |
|---|-------|---------|---------------|---------------------------|
| 0 | tu donnes le lien | `siege` | meme siege, memes fenetres signees | le pack, comme en non-live |
| 1 | coupe par le moteur | `vive` | `v2_vive.yml` → fenetres signees coupees par le moteur NeonClipping vendorise | `PORTE VIVE` declare `captions: false`, aucun titre grave (D-5), aucun LLM, aucun navigateur, mapping non muet |
| 2 | purge | `vive` | SF_14 camouflage → SF_15 luther, meme chaine que le premium | `qa_pass` sur le rapport de lot |
| 3 | manifeste de livraison | `livraison` | `murus_v7.yml` | `PORTE V7`, statut `a_poster` |
| 4 | tu postes | — | humain uniquement | vues, payout, cloture |

Les deux revues **disparaissent** en live : il n'y a rien a juger puisque rien n'est
grave. C'est un echange declare, pas un oubli : tu perds le glow, les sous-titres et
le titre. Cout mesure dans `PARCOURS_V2.md` : chaque job telecharge la source entiere
(7,19 Go pour cette VOD), parce que « un job par clip » interdit de partager un
artefact.

## FR — Le registre des verdicts

`REVIEW/verdicts.jsonl`, append-only, une ligne par acte :

    {"quand":"...","campagne":"PREME","fregate":"siege","sortie":"pack:70f120a8",
     "verdict":"valide","par":"operateur","motif":"15 fenetres retenues"}

Regles : une fregate ne peut s'ouvrir que si l'amont porte `valide` **sur la meme
sortie**. Un verdict ne se modifie jamais ; un nouvel acte ajoute une ligne qui
remplace le precedent pour cette fregate. Refuser est un acte : `refuse` bloque l'aval
et reste dans l'historique.

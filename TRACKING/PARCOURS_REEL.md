# PARCOURS RÉEL — de la VOD au livrable posté

> Document opposable. Il décrit ce qui a **réellement tourné** le 2026-11-23
> (run `45113267319`), pas ce qui était prévu sur le papier. Si le code change
> et pas ce document, la CI le dit (`test_t29_parcours_reel_grave`).
>
> Doctrine bilingue (EXC-M8) : EN puis FR.

## EN — the real path

### What actually runs, in order

Nothing runs on the operator machine. Five GitHub Actions workflows do the work,
one job per clip, no serial loop.

| # | step | entry point | produces |
|---|------|-------------|----------|
| 0 | siege: VOD → transcript → selection → pack | `murus_siege.yml` | `ARCHIVUM/montage/transcripts/v<vod>_transcript.json`, `REVIEW/pack_stage.json` |
| 1 | **review 1 — LOOK** | `murus_preview_1.yml` → Pages `/` | operator verdict: blur, title, logo, watermark |
| 2 | **codex 1 signed (LOOK)** | export from review 1 → `REVIEW/codex_render.json` + `.provenance.json` | `validated_by_magos: true` |
| 3 | **review 2 — POSTPROD** | `murus_preview_2.yml` → Pages `/preview2/` | operator verdict: video glow, subtitles, LUT, fade |
| 4 | **codex 2 signed (POSTPROD)** | export from review 2 → `REVIEW/codex_postprod.json` + `.provenance.json` | `validated_by_magos: true` |
| 5 | render, one job per clip | `murus_rendu.yml` | `pur_A01..A09.mp4` + `livrable-A01..A09` + `preme-pack-9-livrables` |
| 6 | V7 delivery manifest | `murus_v7.yml` | `REVIEW/submissions.json` (sha256 + checklist, status `a_poster`) |
| 7 | operator posts | human only | views 1h/24h, payout, campaign close |

### The two reviews are not optional — they are what produces the codex

Nothing is rendered before **both** reviews have run and **both** codex are signed.
The reviews are the only place where a human judges; the codex is their written,
signed output, and the render is only the executor of that signature.

```
VOD -> siege -> pack_stage.json
                    |
                    +-> REVIEW 1  (Pages /)          LOOK    : blur, title, logo, watermark
                    |      +-> export + signature -> REVIEW/codex_render.json   -+
                    |                                                          +-> G1
                    +-> REVIEW 2  (Pages /preview2/) POSTPROD: glow, subtitles, -+
                           +-> export + signature -> REVIEW/codex_postprod.json
                                                    |
                                    murus_rendu.yml -+-> 9 clips, one job each
```

| | review 1 — LOOK | review 2 — POSTPROD |
|---|---|---|
| workflow | `murus_preview_1.yml` | `murus_preview_2.yml` |
| address | `https://gyutedy.github.io/MURUS_SANGUINIS/` | `https://gyutedy.github.io/MURUS_SANGUINIS/preview2/` |
| what you see | the player stuck to the top, W1 watermark panel, T1 title panel | four panels: glow video, subtitles, LUT, fade + signature/export |
| what you decide | blur strength and background/core split, title size/place/colours/font, the single watermark and its place | glow preset on real parameters, subtitle style and word-by-word motion, LUT profile and intensity, fade |
| what it signs | `codex_render.json` (`sanguinala.render.codex.v1`) | `codex_postprod.json` (`sanguinala.postprod.codex.v1`) |
| how it is proofed | Chromium gate `tests/ui_preview1.mjs` | Chromium gate `tests/ui_preview2.mjs` + `exact_frame` (real ffmpeg on one frame) |
| what it unlocks | half of G1 | the other half of G1 — the render opens only with both |

Two reviews, two roles, two codex: one GitHub Pages site per repository forces the
second under `/preview2/` (declared EXC-M10). A preview is a **review**, not a report:
it always plays the real video next to the exact frame, with live sliders.

### Per-clip job (the real sequence, 7 steps)

```
1 recuperer_clip.py            window from the VOD              → clips/
2 convert_pur_pack.mjs --packs-out   pure single-clip pack      → 9 packs
3 convert_pur_pack.mjs         manifest dev10.pur.v1           → pur_manifest.json
4 render_pictor.mjs            Remotion LOOK (blur, title, logo)
5a transcript_slice.py         real transcript → clip words    → transcript_<id>.json
5  postprod.py                 PP2 glow → caption → lut → fade → pur_<id>.mp4
5b PORTE SOUS-TITRES           refuses a clip without burned subtitles
6  lac_f05_camouflage.py       H.264 yuv420p, faststart, loudnorm, qa_pass
7  lac_f06_luther.py           metadata stripped, stream copy  → pur_<id>_LIVRABLE.mp4
```

Order is not negotiable: `luther` is a stream copy, so anything that re-encodes
after it would put a fingerprint back. `postprod → camouflage → luther`, nothing after.

### The gates that can refuse

| gate | where | refuses when |
|------|-------|--------------|
| G1 | `FR_B_CREATION/GATES/` | either codex missing or `validated_by_magos != true` |
| PP2 order | `postprod.py` | order differs from `glow → caption → lut → fade` |
| G4 / font | `caption/ass_render.py` | style unusable, or font file absent from the repo |
| 5b subtitles | `murus_rendu.yml` | `caption.applied == false` or `caption_burned == false` |
| V7 `qa_pass` | `SF_16_MISSIO` → `gates_b.py` | any clip with `qa_pass: false` |

A gate never demands its own outputs (E-12). A gate is never silenced: it fails
loudly with the clip id and the reason.

### Real numbers, 2026-11-23

```
pack 70f120a8 · 9 clips requested · 9 delivered · 0 failure
camouflage_batch_report.json : 9 videos, all_qa_pass = true
luther_batch_report.json     : 9 videos, all_qa_pass = true
PORTE V7 : True
livrables 15.9 → 22.5 MB each · preme-pack-9-livrables 180.2 MB
render run 45113267319 · V7 run 45120117577
```

### Honest limits, stated here so nobody has to ask

- **Word timing is interpolated** on this campaign: the stored transcript has
  sentence segments only. `transcript_slice.py` spreads each segment over its
  words and writes `"word_timing": "interpolated"`. The transcription workflow now
  requests `word_timestamps=True`, so the **next** transcript is measured
  (`"measured"`) and is preferred automatically. Nothing else changes.
- **Titles are still the chopper's** (`us today too`, `day long show some`).
  Replacing ORACLE is an open decision (A: LLM on Actions, B: LLM on Modal,
  C: operator types the 9 titles).
- **Stake-word substring defect** is open: `win` matches inside *growing*. Fixing
  it changes which clips are selected, so it needs an operator verdict.
- **Transcription runs on CPU** (faster-whisper) because no Modal secret is
  configured. Modal GPU is a speed option, not a requirement.

### Reproduce from a clean clone

```bash
gh workflow run murus_siege.yml    -f vod_url=https://www.twitch.tv/videos/2909800627
gh workflow run murus_preview_1.yml   # review 1 -> LOOK verdict -> export -> sign codex_render.json
gh workflow run murus_preview_2.yml   # review 2 -> POSTPROD verdict -> export -> sign codex_postprod.json
# no render can start before both codex carry validated_by_magos: true
gh workflow run murus_rendu.yml    -f vod_url=https://www.twitch.tv/videos/2909800627 -f nb_clips=9
gh workflow run murus_v7.yml       # run_id empty = last successful render
# post the 9 clips yourself, then record views 1h/24h and payout
```

## FR — le parcours réel

### Ce qui tourne vraiment, dans l'ordre

Rien ne tourne sur la machine de l'opérateur. Cinq workflows GitHub Actions font
le travail, **un job par clip**, jamais de boucle en série.

| # | étape | point d'entrée | produit |
|---|-------|----------------|---------|
| 0 | siège : VOD → transcription → sélection → pack | `murus_siege.yml` | `ARCHIVUM/montage/transcripts/v<vod>_transcript.json`, `REVIEW/pack_stage.json` |
| 1 | **revue 1 — LOOK** | `murus_preview_1.yml` → Pages `/` | verdict opérateur : blur, titre, logo, watermark |
| 2 | **codex 1 signé (LOOK)** | export de la revue 1 → `REVIEW/codex_render.json` + `.provenance.json` | `validated_by_magos: true` |
| 3 | **revue 2 — POSTPROD** | `murus_preview_2.yml` → Pages `/preview2/` | verdict opérateur : glow vidéo, sous-titres, LUT, fade |
| 4 | **codex 2 signé (POSTPROD)** | export de la revue 2 → `REVIEW/codex_postprod.json` + `.provenance.json` | `validated_by_magos: true` |
| 5 | rendu, un job par clip | `murus_rendu.yml` | `pur_A01..A09.mp4` + `livrable-A01..A09` + `preme-pack-9-livrables` |
| 6 | manifeste de livraison V7 | `murus_v7.yml` | `REVIEW/submissions.json` (sha256 + checklist, statut `a_poster`) |
| 7 | l'opérateur poste | humain uniquement | vues 1 h / 24 h, payout, clôture de campagne |

### Les deux revues ne sont pas optionnelles — ce sont elles qui produisent les codex

Rien n'est rendu avant que **les deux revues** soient passées et que **les deux codex**
soient signés. Les revues sont le seul endroit où un humain juge ; le codex est leur
sortie écrite et signée, et le rendu n'est que l'exécuteur de cette signature.

```
VOD -> siège -> pack_stage.json
                    |
                    +-> REVUE 1  (Pages /)          LOOK    : blur, titre, logo, watermark
                    |      +-> export + signature -> REVIEW/codex_render.json   -+
                    |                                                          +-> G1
                    +-> REVUE 2  (Pages /preview2/) POSTPROD: glow, sous-titres, -+
                           +-> export + signature -> REVIEW/codex_postprod.json
                                                    |
                                    murus_rendu.yml -+-> 9 clips, un job chacun
```

| | revue 1 — LOOK | revue 2 — POSTPROD |
|---|---|---|
| workflow | `murus_preview_1.yml` | `murus_preview_2.yml` |
| adresse | `https://gyutedy.github.io/MURUS_SANGUINIS/` | `https://gyutedy.github.io/MURUS_SANGUINIS/preview2/` |
| ce que tu vois | le lecteur collé en haut, le panneau W1 (watermark), le panneau T1 (titre) | quatre panneaux : glow vidéo, sous-titres, LUT, fade + signature/export |
| ce que tu décides | force du blur et partage fond/sujet, taille/place/couleurs/police du titre, watermark unique et sa place | preset de glow sur de vrais paramètres, style de sous-titres et motion mot par mot, profil de LUT et intensité, fade |
| ce que ça signe | `codex_render.json` (`sanguinala.render.codex.v1`) | `codex_postprod.json` (`sanguinala.postprod.codex.v1`) |
| comment c'est prouvé | porte Chromium `tests/ui_preview1.mjs` | porte Chromium `tests/ui_preview2.mjs` + `exact_frame` (vrai ffmpeg sur une image) |
| ce que ça débloque | la moitié de G1 | l'autre moitié de G1 — le rendu ne s'ouvre qu'avec les deux |

Deux revues, deux rôles, deux codex : un seul site GitHub Pages par dépôt impose la
seconde sous `/preview2/` (déclaré EXC-M10). Un aperçu est une **revue**, pas un
rapport : il joue toujours la vraie vidéo à côté de l'image exacte, avec des curseurs
en direct.

### Le job par clip (la séquence réelle, 7 étapes)

```
1 recuperer_clip.py            fenêtre depuis la VOD            → clips/
2 convert_pur_pack.mjs --packs-out   pack PUR mono-clip         → 9 packs
3 convert_pur_pack.mjs         manifeste dev10.pur.v1           → pur_manifest.json
4 render_pictor.mjs            LOOK Remotion (blur, titre, logo)
5a transcript_slice.py         transcription réelle → mots du clip → transcript_<id>.json
5  postprod.py                 PP2 glow → caption → lut → fade  → pur_<id>.mp4
5b PORTE SOUS-TITRES           refuse un clip sans sous-titres gravés
6  lac_f05_camouflage.py       H.264 yuv420p, faststart, loudnorm, qa_pass
7  lac_f06_luther.py           métadonnées retirées, stream copy → pur_<id>_LIVRABLE.mp4
```

Cet ordre n'est pas négociable : `luther` est un stream copy, donc tout
ré-encodage après lui réintroduit une empreinte. `postprod → camouflage → luther`,
rien après.

### Les portes qui peuvent refuser

| porte | où | refuse quand |
|-------|----|--------------|
| G1 | `FR_B_CREATION/GATES/` | un codex manque ou `validated_by_magos != true` |
| ordre PP2 | `postprod.py` | l'ordre diffère de `glow → caption → lut → fade` |
| G4 / police | `caption/ass_render.py` | style inexploitable, ou fichier de police absent du dépôt |
| sous-titres 5b | `murus_rendu.yml` | `caption.applied == false` ou `caption_burned == false` |
| `qa_pass` V7 | `SF_16_MISSIO` → `gates_b.py` | un clip avec `qa_pass: false` |

Une porte n'exige jamais ses propres sorties (E-12). Une porte ne se tait pas :
elle échoue bruyamment avec l'identifiant du clip et le motif.

### Chiffres réels, 2026-11-23

```
pack 70f120a8 · 9 clips demandés · 9 livrés · 0 échec
camouflage_batch_report.json : 9 vidéos, all_qa_pass = true
luther_batch_report.json     : 9 vidéos, all_qa_pass = true
PORTE V7 : True
livrables 15,9 → 22,5 Mo · preme-pack-9-livrables 180,2 Mo
run de rendu 45113267319 · run V7 45120117577
```

### Limites assumées, écrites ici pour que personne n'ait à les demander

- **Le minutage des mots est interpolé** sur cette campagne : la transcription
  stockée ne contient que des segments de phrase. `transcript_slice.py` répartit
  la durée du segment entre ses mots et écrit `"word_timing": "interpolated"`.
  Le workflow de transcription demande maintenant `word_timestamps=True` : la
  **prochaine** transcription sera mesurée (`"measured"`) et sera préférée
  automatiquement. Rien d'autre ne change.
- **Les titres sont encore ceux du chopper** (`us today too`, `day long show some`).
  Le remplacement d'ORACLE est une décision ouverte (A : LLM sur Actions,
  B : LLM sur Modal, C : l'opérateur tape les 9 titres).
- **Défaut de sous-chaîne** ouvert : `win` matche dans *growing*. Le corriger
  change la sélection des clips, donc il faut un verdict opérateur.
- **La transcription tourne en CPU** (faster-whisper) faute de secret Modal
  configuré. Le GPU Modal est une option de vitesse, pas une exigence.

### Reproduire depuis un clone propre

```bash
gh workflow run murus_siege.yml    -f vod_url=https://www.twitch.tv/videos/2909800627
gh workflow run murus_preview_1.yml   # revue 1 -> verdict LOOK -> export -> signature codex_render.json
gh workflow run murus_preview_2.yml   # revue 2 -> verdict POSTPROD -> export -> signature codex_postprod.json
# aucun rendu ne demarre avant que les deux codex portent validated_by_magos: true
gh workflow run murus_rendu.yml    -f vod_url=https://www.twitch.tv/videos/2909800627 -f nb_clips=9
gh workflow run murus_v7.yml       # run_id vide = dernier rendu réussi
# poster les 9 clips soi-même, puis relever les vues 1 h / 24 h et le payout
```

## Journal des corrections qui ont mené à ce parcours

| errata | ce qui était faux | conséquence réelle |
|--------|-------------------|--------------------|
| E-12 | la porte de rendu exigeait ses propres sorties | `chaîne incomplète : 4 étapes`, jamais de rendu |
| E-14 | le commit du rapport échouait sur `git push` | le zip des 9 n'était jamais produit |
| E-15 | `OUT/` gitignoré : les preuves `qa_pass` n'arrivaient pas sur GitHub | aucune trace de livraison |
| E-16 | 6 `git push` nus dans les workflows | un rejet git interrompait un job utile |
| E-17 | le codex nomme la police `Montserrat ExtraBold`, le fichier `Montserrat-ExtraBold.ttf` | sous-titres **absents**, `qa_pass` vrai quand même |
| E-18 | aucun transcript passé à `postprod` | `faster-whisper absent` → pas de sous-titres |
| E-19 | un « mot » était une phrase, et `max_words` ignorait la motion | mélange de pavés et de mots, contraire au pop-in |

Détail : `TRACKING/ERRATA.md`. Dérogations : `TRACKING/LES_EXCEPTIONS.md`.

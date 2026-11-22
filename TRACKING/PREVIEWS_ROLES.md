# PREVIEWS — RÔLES, PANNEAUX, HÉBERGEMENT

> Deux previews, deux rôles, deux codex, deux signatures. Ce document dit ce qui
> appartient à laquelle, et pourquoi. Il est lu avant toute modification d'une preview.

## EN

### Preview 1 — SF_10_SPECULUM — the LOOK

Owns **only** what the eye judges before postproduction:

| control | codex field |
|---|---|
| layout of the clear video (`blur` / `reframing`, fg size, fg height) | `look.style_params` |
| title text place (`top`/`center`/`bottom`), **height** `y_pct`, **size** px, **colour** | `titles[]` |
| watermark **size** (`width_pct`), **horizontal** (`x_pct`), **vertical** (`y_pct`), **opacity** | `logo` |

It writes **one** file: `REVIEW/codex_render.json`.

It does **not** own glow, LUT, fade or subtitles. Those belong to preview 2.
Anything that whitens, tints or times the image after the picture is cut is
postproduction, not LOOK.

### Preview 2 — SF_11_LUMEN — the POSTPROD

Owns, in the engraved order `glow → caption → lut → fade` (gate PP2):

| control | codex field |
|---|---|
| glow mode / sigma / opacity (caption band never blurred, gate GL2) | `glow` |
| subtitle size, height, font | `caption` |
| LUT profile | `lut` |
| end-of-clip fade mode and duration | `fade_out` |

It writes **one** file: `REVIEW/codex_postprod.json` (draft while unsigned).

The parameters come from the operator **at workflow launch**
(`workflow_dispatch`), never from a project guess. The project writes the trace
in `REVIEW/codex_postprod.provenance.json`, a sidecar — the codex schemas are
strict (`additionalProperties: false`), so provenance can never live inside them.

### One codex per clip set, one signature per codex

No render starts while either codex lacks `validated_by_magos: true`.

### Hosting — why preview 2 lives in a subfolder

GitHub Pages serves **one site per repository**. A subfolder (`/preview2/`) is the
only way to keep both previews automatic without a second repository. This is a
derogation, named **EXC-M10** in `TRACKING/LES_EXCEPTIONS.md`.

## FR

### Preview 1 — SF_10_SPECULUM — le LOOK

Ne possède **que** ce que l'œil juge avant postproduction :

| réglage | champ du codex |
|---|---|
| mise en page de la vidéo claire (`blur` / `reframing`, taille, hauteur) | `look.style_params` |
| titre : place, **hauteur** `y_pct`, **taille** px, **couleur** | `titles[]` |
| watermark : **taille**, **horizontal**, **vertical**, **opacité** | `logo` |

Elle écrit **un** fichier : `REVIEW/codex_render.json`.

Elle ne possède **pas** le glow, la LUT, le fade ni les sous-titres : c'est la
preview 2. Tout ce qui blanchit, teinte ou chronomètre l'image après la découpe
est de la postproduction, pas du LOOK.

### Preview 2 — SF_11_LUMEN — la POSTPROD

Possède, dans l'ordre gravé `glow → caption → lut → fade` (porte PP2) :

| réglage | champ du codex |
|---|---|
| glow : mode / sigma / opacité (bande sous-titres jamais floutée, porte GL2) | `glow` |
| sous-titres : taille, hauteur, police | `caption` |
| LUT | `lut` |
| fade de fin : mode et durée | `fade_out` |

Elle écrit **un** fichier : `REVIEW/codex_postprod.json` (brouillon tant qu'il
n'est pas signé).

Les paramètres viennent de l'opérateur **au lancement du workflow**, jamais d'une
supposition du projet. Le projet écrit la trace dans
`REVIEW/codex_postprod.provenance.json`, en sidecar — les schémas de codex sont
stricts (`additionalProperties: false`), la provenance ne peut donc jamais vivre
à l'intérieur.

### Un codex par jeu de clips, une signature par codex

Aucun rendu ne démarre tant qu'un des deux codex n'a pas `validated_by_magos: true`.

### Hébergement — pourquoi la preview 2 est dans un sous-dossier

GitHub Pages ne sert **qu'un seul site par dépôt**. Le sous-dossier (`/preview2/`)
est le seul moyen de garder les deux previews automatiques sans second dépôt.
C'est une dérogation, nommée **EXC-M10** dans `TRACKING/LES_EXCEPTIONS.md`.

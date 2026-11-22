# PREVIEW 2 — SPEC OPPOSABLE

> Cette page dit ce que la preview 2 **doit** être. Si l'interface s'en écarte, c'est un
> défaut, pas un choix. Elle remplace le `preview_glow.py` transformé en page statique :
> une review n'est pas un rapport.

## EN — what preview 2 is

Preview 2 is a **review**, built on the same shell as preview 1: a real video player at
the top, the clip's **still frame** next to / below it, and a scrolling column of
**sliders** on the right. It signs **`codex_postprod.json`** and nothing else.

### Four panels

| # | panel | controls | real gate / pillaged source |
|---|---|---|---|
| 1 | **GLOW VIDÉO** | `kind` preset (Doux, Large bloom, Halation serrée, Sujet seul) → `mode` scene/subject · `sigma` 4–30 · `opacity` 0–0.6 | GL1 (`glow/modal_glow.py`), GL2 (caption band never blurred) |
| 2 | **SOUS-TITRES** | `font` · `size` 12–240 · `position.x_pct` 0–100 · `position.y_pct` 0–100 · `color` · `outline.width` 0–24 · `outline.color` · `glow.intensity` 0–5 · `glow.color` · `motion` pop-in/bounce/slide · `motion_speed` 0.25–3 | `caption/ass_render.py` + `dev11.caption.style.v1` |
| 3 | **LUT** | `enabled` · `profile` | `lut/profiles/atom_ic_profiles.json` |
| 4 | **FADE** | `mode` darken/black · `duration_sec` 0.1–10 | gate F1 (fade is mandatory) |

Order engraved (PP2): `glow → caption → lut → fade`. The interface never lets it invert.

### Honesty rule (option A, chosen by the operator)

The browser preview is **approximate**: CSS blur/shadow for the glow, CSS filters for the
LUT, real font rendering for the captions. The render itself is **ffmpeg `gblur` + ASS**.
So an extra job **`exact_frame`** renders one frame with the **real** chain from the same
parameters and publishes the PNG. You adjust fast, you check exact, you sign.

Glow kinds are **named presets over the real parameters** (`mode`, `sigma`, `opacity`).
No invented filter: the pillaged code exposes exactly two masks (whole scene, subject)
modulated by sigma and opacity.

## FR — ce qu'est la preview 2

La preview 2 est une **review**, sur le même châssis que la preview 1 : un vrai lecteur
vidéo en haut, la **frame fixe** du clip à côté ou dessous, et une colonne de **curseurs**
qui défile à droite. Elle signe **`codex_postprod.json`**, et rien d'autre.

### Quatre panneaux

| # | panneau | réglages | porte / code pillé |
|---|---|---|---|
| 1 | **GLOW VIDÉO** | préréglage `kind` (Doux, Large bloom, Halation serrée, Sujet seul) → `mode` scene/subject · `sigma` 4–30 · `opacité` 0–0.6 | GL1 (`glow/modal_glow.py`), GL2 (bande des sous-titres jamais floutée) |
| 2 | **SOUS-TITRES** | `police` · `taille` 12–240 · `position.x_pct` 0–100 · `position.y_pct` 0–100 · `couleur` · `contour.width` 0–24 · `contour.couleur` · `glow.intensity` 0–5 · `glow.couleur` · `motion` pop-in/bounce/slide · `motion_speed` 0.25–3 | `caption/ass_render.py` + `dev11.caption.style.v1` |
| 3 | **LUT** | `enabled` · `profile` | `lut/profiles/atom_ic_profiles.json` |
| 4 | **FADE** | `mode` darken/black · `duration_sec` 0.1–10 | porte F1 (le fade est obligatoire) |

Ordre gravé (PP2) : `glow → caption → lut → fade`. L'interface ne permet pas de l'inverser.

### Règle d'honnêteté (option A, choisie par l'opérateur)

L'aperçu navigateur est **approximatif** : flou/ombre CSS pour le glow, filtres CSS pour la
LUT, vraie police pour les sous-titres. Le rendu, lui, est **ffmpeg `gblur` + ASS**. Donc un
job supplémentaire **`exact_frame`** rend une frame avec la **vraie** chaîne, mêmes
paramètres, et publie le PNG. Tu ajustes vite, tu contrôles exact, tu signes.

Les sortes de glow sont des **préréglages nommés sur les vrais paramètres** (`mode`,
`sigma`, `opacité`). Aucun filtre inventé : le code pillé expose exactement deux masques
(scène entière, sujet) modulés par sigma et opacité.

## Ce qui est interdit (et testé)

1. Remplacer les curseurs par des champs de formulaire au lancement du workflow.
2. Afficher les réglages sans lecteur vidéo et sans frame.
3. Signer un codex sans avoir vu les quatre panneaux.
4. Mettre les sous-titres dans la preview 1 (ils sont ici, **depuis le début**).
5. Inventer un `kind` de glow qui n'existe pas dans `modal_glow.py`.

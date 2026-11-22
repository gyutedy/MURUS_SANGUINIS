# CODEX SIGNÉS

> Registre des codex signés par l'opérateur. Un codex non listé ici n'existe pas
> pour la chaîne de rendu. La signature est `validated_by_magos: true`, et sa
> provenance vit en sidecar (`*.provenance.json`), jamais dans le codex.

## EN

### Codex 1 — LOOK (preview 1)

| field | value |
|---|---|
| file | `REVIEW/codex_render.json` |
| schema | `sanguinala.render.codex.v1` |
| pack_token | `70f120a8` |
| clips covered | 9 (A01…A09) — the pack exported by the siege |
| style | `blur` (degree 24, bg 118, fg 49 %, fg_y 49 %) |
| title | size 68 px, x 50 %, y 22 %, line1 `#FFFFFF`, line2 `#FFD700`, `Arial Black, Impact`, outline 3 px black |
| logo | enabled, 15 % width, custom at 73.2 % / 81.8 %, opacity 0.8 — PNG `preme.png` |
| `validated_by_magos` | **true** (signed by the operator) |
| provenance | `REVIEW/codex_render.provenance.json` (sha256 of the codex) |

Gate **W1-R** accepts it (`load_render_codex` → accepted).

### Codex 2 — POSTPROD (preview 2)

| field | value |
|---|---|
| file | `REVIEW/codex_postprod.json` |
| schema | `sanguinala.postprod.codex.v1` |
| pack_token | `70f120a8` |
| order | `glow → caption → lut → fade` (PP2) |
| glow | enabled, `scene`, sigma **26**, opacity **0.5** (preset Large bloom) |
| caption | Montserrat ExtraBold, 62 px, 50 % / 82 %, `#FFFFFF`, outline 3 px black, glow `#FFD700` 1.4, `pop-in`, speed 1 |
| lut | enabled, `hdr_imperator` |
| fade_out | `darken`, 0.6 s |
| `validated_by_magos` | **true** (signed on the operator's explicit order) |
| provenance | `REVIEW/codex_postprod.provenance.json` |

**Gate G1 now passes: `GATE G1 : True`.**

## FR

### Codex 1 — LOOK (preview 1)

| champ | valeur |
|---|---|
| fichier | `REVIEW/codex_render.json` |
| schéma | `sanguinala.render.codex.v1` |
| pack_token | `70f120a8` |
| clips couverts | 9 (A01…A09) — le pack exporté par le siège |
| style | `blur` (degree 24, bg 118, fg 49 %, fg_y 49 %) |
| titre | taille 68 px, x 50 %, y 22 %, ligne 1 `#FFFFFF`, ligne 2 `#FFD700`, `Arial Black, Impact`, contour 3 px noir |
| logo | activé, largeur 15 %, personnalisé à 73.2 % / 81.8 %, opacité 0.8 — PNG `preme.png` |
| `validated_by_magos` | **true** (signé par l'opérateur) |
| provenance | `REVIEW/codex_render.provenance.json` (sha256 du codex) |

La porte **W1-R** l'accepte (`load_render_codex` → accepté).

### Codex 2 — POSTPROD (preview 2)

| champ | valeur |
|---|---|
| fichier | `REVIEW/codex_postprod.json` |
| schéma | `sanguinala.postprod.codex.v1` |
| pack_token | `70f120a8` |
| ordre | `glow → caption → lut → fade` (PP2) |
| glow | activé, `scene`, sigma **26**, opacité **0.5** (préréglage Large bloom) |
| sous-titres | Montserrat ExtraBold, 62 px, 50 % / 82 %, `#FFFFFF`, contour 3 px noir, glow `#FFD700` 1.4, `pop-in`, vitesse 1 |
| lut | activée, `hdr_imperator` |
| fade_out | `darken`, 0.6 s |
| `validated_by_magos` | **true** (signé sur ordre explicite de l'opérateur) |
| provenance | `REVIEW/codex_postprod.provenance.json` |

**La porte G1 passe : `GATE G1 : True`.**

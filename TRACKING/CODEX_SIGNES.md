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

### Codex 2 — POSTPROD (preview 2) — **not signed**

`REVIEW/codex_postprod.json` does not exist yet. Only a draft
(`REVIEW/codex_postprod.draft.json`, `validated_by_magos: false`) and its provenance
sidecar exist. **No render starts without it** — gate G1 refuses:

```
GATE G1 : False | REVIEW/codex_postprod.json absent — aucun rendu sans codex
```

Postprod parameters are given by the operator **at workflow launch**
(`murus_preview_2.yml`): glow mode/sigma/opacity, LUT profile, fade mode/duration,
subtitle size/height/font.

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

### Codex 2 — POSTPROD (preview 2) — **non signé**

`REVIEW/codex_postprod.json` n'existe pas encore. Seuls un brouillon
(`REVIEW/codex_postprod.draft.json`, `validated_by_magos: false`) et sa provenance
existent. **Aucun rendu ne démarre sans lui** — la porte G1 refuse :

```
GATE G1 : False | REVIEW/codex_postprod.json absent — aucun rendu sans codex
```

Les paramètres de postprod sont donnés par l'opérateur **au lancement du workflow**
(`murus_preview_2.yml`) : mode/sigma/opacité du glow, profil LUT, mode/durée du fade,
taille/hauteur/police des sous-titres.

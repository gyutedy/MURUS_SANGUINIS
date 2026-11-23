# MURUS SANGUINIS — le mur de siège qui réfléchit et qui frappe

Fusion **PERTURABO** (le cerveau) × **LACRIMAE** (le bras armé) × **gta6-clipper-windows** (le détecteur).
Cahier des charges : `MURUS_SANGUINIS_CDC_V1.html` (auto-suffisant, fait foi).

> **Parcours réel, exécuté et mesuré (2026-11-23)** : `TRACKING/PARCOURS_REEL.md`.
> Pack `70f120a8`, 9 clips demandés, 9 livrés, `all_qa_pass = true` des deux côtés,
> `PORTE V7 : True`. Ce guide est en EN + FR et la CI vérifie qu'il ne dérive pas.

## État des branches

| branche | état | référence |
|---------|------|-----------|
| `main` | **V1 exécutée et mesurée** — 29 portes, pack `70f120a8`, 9/9 livrés, `PORTE V7 : True` | `TRACKING/PARCOURS_REEL.md` |
| `v2` | **assemblage en cours** — deux moteurs (premium + vive), une voix (élocution), un calendrier (publication programmée). Merge vers `main` **interdit** tant que T20–T29 ne sont pas verts | `TRACKING/PLAN_V2.md` + `CDC/MURUS_SANGUINIS_CDC_V2.html` |

## Doctrine (intangible)

- **FR_A_CERVEAU ne touche JAMAIS une vidéo** — elle produit des packs JSON dans `EXPORT/`
  (héritage CLIPPING/MARK1).
- **FR_B_CREATION ne prend JAMAIS une décision** — elle exécute les codex signés
  (`REVIEW/codex_render.json` + `REVIEW/codex_postprod.json`, `validated_by_magos`)
  (héritage LACRIMAE).
- **Une gate PRÉCÈDE chaque sous-frégate** — 14 gates humaines. Les DEUX exceptions,
  `SF_14_CAMOUFLAGE` et `SF_15_LUTHER`, s'exécutent AUTOMATIQUEMENT après le rendu,
  ne rendent rien elles-mêmes, et prouvent leur passage par un rapport (`qa_pass`).
- **Le run s'arrête à la première porte en échec** — aucune erreur amont ne peut
  déclencher un run A→Z.
- **Le moteur décide, l'opérateur valide, le ledger juge.**
- **Deux previews, deux rôles** — la preview 1 (`SF_10_SPECULUM`) règle le LOOK
  (style, titre place/hauteur/taille/**couleur**, watermark taille/horizontal/vertical/opacité)
  et écrit `codex_render.json` ; la preview 2 (`SF_11_LUMEN`) règle le postprod
  (`glow → caption → lut → fade`) et écrit `codex_postprod.json`. Voir
  `TRACKING/PREVIEWS_ROLES.md`.
- **Un codex ne contient pas sa provenance** — les schémas sont stricts ; la
  provenance vit en sidecar (`*.provenance.json`), validée en CI (EXC-M10, `ERRATA.md` E-5).
- **Un job par clip** — la récupération et le traitement des clips tournent en
  matrice GitHub Actions (`fail-fast: false`), jamais en série dans un seul job.
- **Aucun remplissage** : si 15 clips sont demandés et que la VOD n'en offre que 6 qui
  remplissent les conditions, le projet rend **6** et l'écrit (`nb_demande` / `nb_retenu` /
  `manque` / `remplissage_refuse` dans le pack). Jamais de doublon, jamais de moment faible
  ajouté pour atteindre le chiffre. Toute porte qui refuse est une porte qui fonctionne.
  → `TRACKING/DOCTRINE_ANTI_REMPLISSAGE.md`
- **Deux versions, EN et FR** : tout document destiné à l'opérateur existe en anglais et en
  français. Le EN est la transcription verbatim (source de vérité), le FR une traduction de
  compréhension que le moteur ne lit jamais. → `TRACKING/DOCTRINE_BILINGUE.md`
- **L'opérateur n'édite jamais un fichier en plein siège** : le projet pose la question
  (`ARCHIVUM/demande/pending/`), l'opérateur répond au lancement (`nb_clips`,
  `selection_approved`), le projet écrit la trace avec sa provenance.
  → `ARCHIVUM/demande/README.md`
- **L'ordre est gravé** : export (D0→X1) → récupération du clip (`FR_B_CREATION/tools/
  recuperer_clip.py` : clip → preview 1, frame → preview 2) → les DEUX codex signés →
  rendu (SF_12) → PP2 → CAMOUFLAGE → LUTHER → V7. Aucun rendu avant les codex.

## Architecture

```
FR_A_CERVEAU (SF_01→SF_09)          FR_B_CREATION (SF_10→SF_16)
  M0 SF_01_VIGILIA                    V5  SF_10_SPECULUM  (preview LOOK)
  V1 SF_02_VERDICTUM                  V6  SF_11_LUMEN     (preview GLOW, 1 frame)
  V2 SF_03_ANGULI                     G1  SF_12_FABRICA   (rendu, piloté par les 2 codex)
  M1 SF_04_SELECTIO (TOP 15, cap 15)  PP2 SF_13_POLITURA  (glow→caption→lut→fade)
  M5 SF_05_VOX                        —   SF_14_CAMOUFLAGE (SANS gate, post-rendu)
  M2 SF_06_LIBELLUS                   —   SF_15_LUTHER     (SANS gate, post-rendu)
  M3 SF_07_VEXILLUM                   V7  SF_16_MISSIO     (C3 : soumission < 1 h)
  P1 SF_08_PURGATIO (zéro clé morte)
  M4 SF_09_PORTAS (EXPORT + ledger)
```

La seule frontière entre les deux frégates : le pack JSON dans `EXPORT/` et les deux codex dans `REVIEW/`.

## Usage

```
python murus.py --profile vod     --pack ARCHIVUM/campaign/campaign_directive.json --vod <url|fichier>
python murus.py --profile direct  --channel <twitch_channel>
python murus.py selftest
```

Profil `direct` : la couche d'entrée est le radar chat (`v2-live`, buffer glissant),
une seule validation humaine au TOP 15, SF_10/SF_11 remplacées par la réutilisation
des derniers codex signés. SF_14/SF_15 tournent quand même.

## Exécution

Rien ne tourne sur la machine opérateur : **tout est orchestré par GitHub Actions**
(`.github/workflows/`), un job par clip. La transcription tourne en **faster-whisper
CPU** ; le GPU Modal n'est qu'une option de vitesse (secrets `MODAL_TOKEN_ID` /
`MODAL_TOKEN_SECRET`, absents par défaut).

**Le parcours réellement exécuté, étape par étape, avec ses chiffres et ses portes :
`TRACKING/PARCOURS_REEL.md` (EN + FR).** C'est le document de référence : il décrit
ce qui a tourné, pas ce qui était prévu.

## Tests

28 portes : `python tests/test_murus.py` (statut CDC : ATTENDU → remplacé par la
sortie réelle à la première exécution en CI). Portes navigateur : `tests/ui_preview1.mjs`,
`tests/ui_preview2.mjs`. Test de doctrine global T0 :

```
grep -rni "ffmpeg\|libx264" FR_A_CERVEAU/   # doit renvoyer ZÉRO ligne
grep -rni "opacity" FR_A_CERVEAU/SF_07_VEXILLUM/  # doit renvoyer ZÉRO ligne
```

## Protocole de mesure

45 clips avant verdict (15 × 3 sessions, postés en 2 semaines). Seuil d'abandon :
revenu net ÷ heure < 0 ⇒ le projet s'arrête. Chiffres interdits sans les 5 éléments :
valeur + unité + période + population + source exacte.

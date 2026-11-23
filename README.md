# MURUS SANGUINIS — le mur de siège qui réfléchit et qui frappe

Fusion **PERTURABO** (le cerveau) × **LACRIMAE** (le bras armé) × **gta6-clipper-windows** (le détecteur),
augmentée en V2 de **NeonClipping** (le moteur qui coupe en temps réel).
Cahiers des charges, dans le dépôt et faisant foi : `CDC/MURUS_SANGUINIS_CDC_V1.html`
et `CDC/MURUS_SANGUINIS_CDC_V2.html`.

> **V1 est exécutée et mesurée** (branche `main`, 2026-11-23) : pack `70f120a8`, 9 clips
> demandés, 9 livrés, `all_qa_pass = true` des deux côtés, `PORTE V7 : True`.
> Guide opposable du parcours réel : `TRACKING/PARCOURS_REEL.md` (EN + FR), vérifié par la CI.
>
> **V2 est en cours d'assemblage** sur la branche `v2`. Le plan d'exécution est
> `TRACKING/PLAN_V2.md` : 10 étapes, chacune avec un oracle (T20→T29) et une condition de
> refus. Rien n'est annoncé ici comme fait sans sa preuve.

## État des branches

| branche | état | référence |
|---------|------|-----------|
| `main` | **V1 exécutée et mesurée** — 30 portes, pack `70f120a8`, 9/9 livrés, `PORTE V7 : True`, zip 180,2 Mo | `TRACKING/PARCOURS_REEL.md` |
| `v2` | **assemblage** — deux moteurs (premium + vive), une voix (élocution), un calendrier (publication programmée) | `TRACKING/PLAN_V2.md` |

Merge de `v2` vers `main` **interdit** tant que T20–T29 ne sont pas verts : la V2 n'a pas
le droit de casser une V1 qui fonctionne.

## Ce que la V2 ajoute — trois pouvoirs, pas une réécriture

| pouvoir | ce qu'il apporte | pièce | état |
|---------|------------------|-------|------|
| **Le mur s'étend au LIVE** | un second moteur coupe des clips pendant/juste après le direct, sans machine locale, sans GPU, sans LLM | `SF_12_FABRICA/vive/` (moteur NeonClipping **figé**, MIT, commit `0525004`) | vendé, `vive_runner.py` à écrire (étape 2) |
| **La voix gagne une seconde passe** | les métadonnées sont d'abord posées par le moteur (déterministe), puis retravaillées par un LLM — et **re-jugées** par les gabarits | `SF_06_LIBELLUS/CODEBASE/elocution.py` | à écrire (étape 5) |
| **L'heure devient programmable** | les livrables acceptés sont publiés par lots, à 4–10 h d'intervalle, via l'API officielle YouTube (`publishAt`) | `SF_17_PROGRAMMA/` | à écrire (étape 6) |

**TikTok est retiré en V2** : la filigrane y étant interdite, l'API d'upload entreprise
réduirait le texte à ~90 caractères et exigerait des devs audités. YouTube seul, en API
officielle et gratuite.

## Ce que la V2 ne change pas

- **FR_A_CERVEAU ne touche JAMAIS une vidéo** — elle produit des packs JSON dans `EXPORT/`.
- **FR_B_CREATION ne prend JAMAIS une décision** — elle exécute les codex signés
  (`REVIEW/codex_render.json` + `REVIEW/codex_postprod.json`, `validated_by_magos`).
  Le second moteur ne contourne pas cette règle : `vive_runner.py` refuse de démarrer sans les deux codex signés.
- **Une gate PRÉCÈDE chaque sous-frégate.** `SF_14_CAMOUFLAGE` et `SF_15_LUTHER` restent les
  deux seules exceptions : post-rendu, automatiques, sans décision, et **sans exception pour
  la voie vive** — un clip LIVE subit exactement la même purgue que le premium, ou il ne livre pas.
- **Le run s'arrête à la première porte en échec.** Un titre refusé par le validateur ne passe
  pas ; un clip sans sous-titres brûlés ne passe pas (`5b PORTE SOUS-TITRES`) ; un livrable
  dont `qa_pass` est faux ne sort pas (`PORTE V7`).
- **Le projet ASK et ne POSTE JAMAIS.** La V2 prépare le calendrier ; la main de l'opérateur
  reste la seule à poster, et `tests/test_murus.py` (t28) interdit toute publication automatique.
- **Aucun remplissage** : 15 demandés, 6 valables ⇒ 6 rendus, et c'est écrit dans le pack.
- **Deux versions, EN et FR**, pour tout document opérateur ; la CI vérifie qu'ils ne dérivent pas.
- **Chiffres interdits sans les cinq éléments** : valeur, unité, période, population, source.

## Architecture

```
FR_A_CERVEAU (SF_01→SF_09)          FR_B_CREATION (SF_10→SF_17)
  M0 SF_01_VIGILIA                    V5  SF_10_SPECULUM  (preview LOOK)
  V1 SF_02_VERDICTUM                  V6  SF_11_LUMEN     (preview GLOW, 1 frame)
  V2 SF_03_ANGULI                     G1  SF_12_FABRICA   (rendu — premium OU vive)
  M1 SF_04_SELECTIO (TOP 15, cap 15)  PP2 SF_13_POLITURA  (glow→caption→lut→fade)
  M5 SF_05_VOX                        —   SF_14_CAMOUFLAGE (SANS gate, post-rendu)
  M2 SF_06_LIBELLUS (+ elocution V2)  —   SF_15_LUTHER     (SANS gate, post-rendu)
  M3 SF_07_VEXILLUM                   V7  SF_16_MISSIO     (soumission < 1 h)
  P1 SF_08_PURGATIO (zéro clé morte)  V8  SF_17_PROGRAMMA  (publication programmée, V2)
  M4 SF_09_PORTAS (EXPORT + ledger)
```

La seule frontière entre les deux frégates reste le **pack JSON** dans `EXPORT/` et les
**deux codex** dans `REVIEW/`. Le coeur peut décider, le bras ne décide pas — la V2 n'ajoute
aucune exception.

## Les deux moteurs

| | **premium** (V1, mesuré) | **vive** (V2) |
|---|---|---|
| source | VOD Twitch/YouTube, montage sélectif | VOD courte ou segment de direct |
| moteur | Remotion (prévisualisation identique au rendu) | NeonClipping headless, copie figée MIT |
| piloté par | les deux codex signés | les deux codex signés (mêmes gates) |
| sous-titres | `transcript_slice.py` + ASS, **un mot par cue** en `pop-in` | les nôtres ; ceux du moteur sont désactivés |
| titres | codex render (texte bit-identique) | **jamais** transmis au moteur : gravés par notre pile |
| purgue | SF_14 puis SF_15 | SF_14 puis SF_15 — **identique** |
| livraison | `RS_*_LIVRABLE.mp4` + manifeste V7 | même porte V7, même manifeste |

Le moteur vive est une **copie figée** : si l'amont disparaît, il continue de tourner.
Provenance, exclusions et interface réelle sont écrites dans `SF_12_FABRICA/vive/VENDOR.md`.

## Usage

```
python murus.py --profile vod     --pack ARCHIVUM/campaign/campaign_directive.json --vod <url|fichier>
python murus.py --profile direct  --channel <twitch_channel>
python murus.py selftest
```

Moteur vive, une fois l'étape 2 livrée :

```
python FR_B_CREATION/SF_12_FABRICA/vive/vive_runner.py --pack REVIEW/pack_stage.json \
  --codex-render REVIEW/codex_render.json --codex-postprod REVIEW/codex_postprod.json \
  --out FR_B_CREATION/SF_12_FABRICA/vive/OUT --report vive/REVIEW/vive_report.json
```

## Exécution

Rien ne tourne sur la machine de l'opérateur : **tout est orchestré par GitHub Actions**
(`.github/workflows/`), un job par clip en matrice `fail-fast: false`. La transcription
tourne en **faster-whisper CPU** (`word_timestamps=True` pour tomber mot par mot) ; le GPU
Modal n'est qu'une option de vitesse.

| workflow | rôle |
|----------|------|
| `murus_siege.yml` | siège complet (sélection → render d'un job par clip → camouflage → luther) |
| `murus_preview_1.yml` / `murus_preview_2.yml` | les **deux revues** qui produisent les deux codex (GitHub Pages `/` et `/preview2/`) |
| `murus_rendu.yml` | rendu piloté par les codex (refuse sans `validated_by_magos`) |
| `murus_v7.yml` | manifeste de soumission — s'arrête avant la main de l'opérateur |
| `murus_tests.yml` / `murus_e2e.yml` | les portes, à chaque push |
| `v2_elocution.yml` / `v2_publish.yml` | V2 — **bornes déclarées**, refusent avec le numéro d'étape tant que l'implémentation n'est pas livrée |

**Secrets attendus (noms seulement, jamais de valeur dans le dépôt)** : `NVIDIA_API_KEY`
(élocution), `YT_OAUTH_CLIENT_ID`, `YT_OAUTH_CLIENT_SECRET`, `YT_OAUTH_REFRESH_TOKEN`
(publication). Aucun n'est requis pour les étapes 1–4.

## Tests

`python tests/test_murus.py` → `TOUTES LES PORTES SONT VERTES` (31 fonctions de test,
T0 doctrine compris). Portes navigateur : `tests/ui_preview1.mjs`, `tests/ui_preview2.mjs`.

Oracles V2 à venir, un par étape du plan : **T20** moteur vive (5 clips, zéro Ollama, zéro
navigateur) · **T21** mapping codex→moteur, écarts nommés · **T22** purgue identique sur la
voie vive · **T23** titres re-jugés · **T24** repli propre sans clé · **T25** intervalles
4–10 h · **T26** déterminisme par graine · **T27** `publishAt` + `private` en dry-run ·
**T28** idempotence · **T29** siège mesuré. Tant qu'un oracle n'a pas tourné, il est
marqué ATTENDU — jamais présenté comme vert.

Test de doctrine global T0 :

```
grep -rni "ffmpeg\|libx264" FR_A_CERVEAU/          # doit renvoyer ZÉRO ligne
grep -rni "ollama" FR_B_CREATION/SF_12_FABRICA/vive/vive_runner.py   # doit renvoyer ZÉRO ligne
grep -rn "NVIDIA_API_KEY\|REFRESH_TOKEN" --include="*.py" .         # os.environ seulement
```

## Limites connues — écrites, pas cachées

- **Temps par clip sur runner sans GPU** : mesuré à l'étape 9, pas supposé. Un clip de 30 s
  peut coûter des minutes de CPU ; le chiffre réel sera écrit dans `TRACKING/PARCOURS_V2.md`.
- **Crédits NVIDIA** : plafonnés et comptés ; 15 titres + 3 reprises au pire. Clé absente ou
  épuisée ⇒ **repli gabarit**, siège complet, repli tracé au ledger.
- **Quota YouTube** : pire cas < 900 unités pour 10 000/jour ; backoff 403 gravé.
- **Titres** : encore le défaut du chopper en V1 (`us today too`) ; la V2 les reprend par
  l'élocution, mais un titre reste validé par les gabarits, pas par le LLM.
- **`word_timing: interpolated`** : quand la transcription n'a pas d'horodatage par mot, la
  durée du segment est répartie et le JSON le **déclare** — jamais présenté comme mesuré.
- **Défaut de sous-chaîne** (`win` dans *growing*) : connu, non corrigé ; le corriger change
  la sélection et demande un verdict opérateur.

## Documents

| document | contenu |
|----------|---------|
| `TRACKING/PARCOURS_REEL.md` | le parcours V1 réellement exécuté, avec ses chiffres et ses portes (EN + FR) |
| `TRACKING/PLAN_V2.md` | **l'ordre d'exécution V2** — 10 étapes, oracles, conditions de refus (EN + FR) |
| `CDC/MURUS_SANGUINIS_CDC_V2.html` | le cahier des charges V2, dans le dépôt |
| `TRACKING/ERRATA.md` | E-1→E-19 : chaque défaut trouvé, sa cause, sa conséquence |
| `TRACKING/LES_EXCEPTIONS.md` | chaque dérogation à la doctrine, avec son grep |
| `MANIFEST.md` | la carte des fichiers, étiquette PILLÉ / CRÉÉ |
| `TRACKING/CODEX_SIGNES.md` | les deux codex et leur provenance |

## Protocole de mesure

45 clips avant verdict (15 × 3 sessions, postés en 2 semaines). Seuil d'abandon :
revenu net ÷ heure < 0 ⇒ le projet s'arrête. Les échecs sont cherchés, pas cachés.

---

## EN — what this version is

**MURUS SANGUINIS V2** keeps the V1 fortress (a brain that never touches video, an arm that
never decides, a human gate before every sub-frigate) and adds **three powers**: a frozen
MIT engine for **live** clipping (`SF_12_FABRICA/vive/`, NeonClipping commit `0525004`), a
second **voice** pass where an LLM rewrites metadata but is re-judged by the deterministic
validators (`SF_06_LIBELLUS/elocution.py`), and a **schedule** that publishes accepted
deliverables to YouTube through the official API every 4–10 h with native `publishAt`
(`SF_17_PROGRAMMA`). TikTok is removed (watermark prohibited).

Branch state: `main` is V1, executed and measured (9/9 clips, `PORTE V7 : True`). Branch `v2`
is under assembly and may **not** be merged until oracles T20–T29 are green
(`TRACKING/PLAN_V2.md`). Files listed as "à écrire" are empty placeholders on purpose: an
empty file is visible debt, a plausible-looking stub is hidden debt. Nothing runs locally —
every job runs on GitHub Actions, one job per clip. The project never posts; the operator's
hand remains the only one that publishes. Numbers require their five elements (value, unit,
period, population, exact source).

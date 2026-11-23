# PLAN_V2 — plan d'implémentation de la branche `v2`

> Document opposable, bilingue (EXC-M8). Écrit le 2026-11-23 depuis
> `CDC/MURUS_SANGUINIS_CDC_V2.html`. Il n'est pas un supplément d'intention :
> c'est l'ordre d'exécution. Chaque étape a une **condition d'entrée**, une
> **sortie mesurable**, un **oracle** et une **condition de refus**.
>
> Règle du Warsmith : on n'y revient pas. Si une étape échoue, on corrige
> l'étape, on ne réordonne pas le plan.

## EN — implementation plan (summary)

The plan is executed in ten steps. No step starts before the previous one is
green **and pushed**. Every claim about the vendored engine was checked against
its real code (`app.py`, 707 lines), not against the CDC prose.

| step | deliverable | oracle | refuses when |
|------|-------------|--------|--------------|
| 0 | branch `v2`, tree/F scaffold, vendored engine | `test_t30` + `git ls-tree` | a placeholder or LICENSE is missing |
| 1 | vendor normalisation (`VENDOR.md`, checksums, engine interface proven by reading) | `test_t30` checks the real entry points exist | the vendor is truncated or unlabelled |
| 2 | `vive_runner.py` (headless `POST /make` + moments + polling + collection) | T20 | a clip is missing, Ollama is called, a browser is needed |
| 3 | codex → engine preset mapping, every gap named | T21 | a mapping gap is silent |
| 4 | `vibe` clips enter SF_14/SF_15 unchanged | T22 | `qa_pass: false` or residual suspicious tags |
| 5 | `elocution.py` (NVIDIA NIM, rules re-judge, template fallback) | T23, T24 | a title passes without the rules validator |
| 6 | `programma.py` (4–10 h interval, signed schedule, `publishAt`) | T25, T26 | an interval leaves [4 h, 10 h], or the seed is lost |
| 7 | `v2_publish.yml` cron + dry-run proof | T27 | `publishAt` missing, or `privacyStatus != private` |
| 8 | idempotence | T28 | a duplicate publication is possible |
| 9 | measured run (time per clip, NVIDIA credits, YouTube units) + docs | T29 | a number appears without its five elements |

Merge to `main` stays forbidden until T20–T29 are green.

## FR — plan d'implémentation détaillé

### Décisions déjà prises (ne se rediscutent pas)

| # | décision | auteur |
|---|----------|--------|
| D-1 | la branche `v2` est créée depuis `main` (= V1, 28 portes vertes) | Warsmith |
| D-2 | `NVIDIA_API_KEY` existe côté opérateur | Warsmith |
| D-3 | chaîne YouTube + client OAuth disponibles côté opérateur | Warsmith |
| D-4 | `schedule.json` vit dans `REVIEW/` et est signé (même schema de provenance que les codex) ; copie dans `EXPORT/` pour l'usage local — `EXPORT/` est gitignoré (E-12/E-15) | Warsmith |
| D-5 | le moteur vive ne grave aucun titre : les titres viennent de notre pile (codex + SF_13), l'oracle T20 devient « le moteur ne grave rien + le titre final est bit-identique au pack » | défaut, faute de refus explicite |
| D-6 | TikTok retiré ; YouTube seul | CDC |
| D-7 | vendor figé : code + tests + modèle ONNX + LICENSE ; médias de démo exclu, listé dans `VENDOR.md` | CDC + déclaration |
| D-8 | deux revues (preview 1 LOOK, preview 2 POSTPROD) restent la seule source des codex ; la voie vive les **consomme** | V1 |

### Étape 0 — socle (faite)

```
branche        v2, créée depuis main
tree/F         CDC/ + SF_17_PROGRAMMA/{CODEBASE,IN,OUT,README.md}
               SF_12_FABRICA/vive/{vive_runner.py,OUT,REVIEW}
               SF_06_LIBELLUS/CODEBASE/elocution.py
               .github/workflows/{v2_publish.yml,v2_elocution.yml}
               tests/test_murus_v2.py
vendor         SF_12_FABRICA/vive/vendor/neonclipping/ — 112 fichiers, 1,4 Mo,
               commit 0525004 (2026-11-22), MIT, LICENSE présente (1 120 o),
               modèle models/face_detection_yunet_2023mar.onnx (232 589 o)
```

Fichiers vides : `elocution.py`, `vive_runner.py`, `programma.py`, `README.md`
de SF_17, `v2_publish.yml`, `v2_elocution.yml`, `test_murus_v2.py`. Ils sont
**volontairement à 0 octet** : un fichier vide est une dette visible, un
squelette est une dette cachée.

**Oracle** : `test_t30_v2_socle` (vendor LICENSE, 7 placeholders présents, plan
présent, CDC présent). **Refus** si un placeholder disparaît ou si le vendor
perd sa LICENSE.

### Étape 1 — normalisation du vendor

Écrire `SF_12_FABRICA/vive/VENDOR.md` : origine, commit, licence, liste exacte
des fichiers exclus, **et l'interface réelle** relevée dans le code, car le CDC
la décrit imparfaitement.

Ce que le code dit vraiment (relevé, pas supposé) :

```
POST /make          payload réel : {url, count, min_len, max_len,
                     moments:[{start,end}], mode:"fast"|"deep", layout,
                     caption_style, language, source_height, moment_profile,
                     accurate, top, cam, game}
                     → crée un job ASYNCHRONE (state[job]), pas de titre accepté
GET  /make/{job}    état du job ; les clips s'accumulent dans state[job]['clips']
GET  /status/{id}   état générique
POST refusé         si info['is_live'] → « Use the Live clipping panel »
port                127.0.0.1:NEONCLIPPING_PORT (défaut 8770), uvicorn
```

Conséquences écrites noir sur blanc : (a) `vive_runner.py` envoie des
**moments** issus du pack, pas des start/end par asset ; (b) il **sonde** le
job ; (c) le titre n'est jamais transmis au moteur (D-5) ; (d)
`denoise`/`captions` du moteur sont désactivés pour éviter des sous-titres en
double avec ceux de SF_13.

**Refus** : vendor tronqué, LICENSE absente, ou interface non documentée.

### Étape 2 — `vive_runner.py`

`FR_B_CREATION/SF_12_FABRICA/vive/vive_runner.py`, stdlib + urllib seulement :

1. lire `REVIEW/pack_stage.json` et les deux codex **signés** (refus si
   `validated_by_magos != true` — G1 s'applique identiquement aux deux moteurs) ;
2. démarrer le vendor headless (`sys.executable app.py`, `NEONCLIPPING_PORT`) ;
3. **amendement A-1 (ERRATA E-20)** : `POST /export` par fenêtre signée, et non
   `POST /make` — le code réel de `/make` grave les sous-titres en dur
   (`'captions':True`) et re-score des moments déjà décidés. `/export` accepte
   `captions:false`, donc notre pile reste la seule à graver quoi que ce soit ;
4. sonder `GET /make/{job}` jusqu'à `status` terminal, **timeout dur** ;
5. collecter les MP4 vers `vive/OUT/`, nommage `pur_<id>.mp4` (E-1 : le nom que
   SF_13 attend) ;
6. écrire `vive/REVIEW/vive_report.json` : job id, durée par clip, nombre de
   clips demandés/obtenus, **toute passe non appliquée nommée** ;
7. tuer le serveur (SIGTERM) même en cas d'erreur.

**Amendement A-1** : la source est déposée une fois dans `NEONCLIPPING_DATA_DIR`,
puis une requête `/export` par fenêtre. Les `.css`/titres du moteur ne sont jamais
atteints ; la géométrie (`layout`, `top`, `cam`, `game`) est transmise telle quelle.

**Oracle T20** : 5 clips rendus, zéro appel Ollama (`grep -ci ollama` sur le log
`/make` = 0), aucun navigateur lancé, `vive/OUT/` contient les 5 clips, titres
du pack bit-identiques dans le rapport. **Refus** : un clip manquant, un appel
LLM, ou un titre altéré.

### Étape 3 — mapping codex → presets (T21)

`vive_runner.py` traduit `codex_render.json` et `codex_postprod.json` vers les
paramètres réels du moteur (`layout`, `caption_style`, `source_height`,
`moment_profile`). **Tout écart est nommé** dans `vive_report.json` sous
`mapping.equivalences` et `mapping.ecarts` — jamais silencieux. Un paramètre du
codex sans équivalent côté moteur ⇒ ligne d'écart, pas d'approximation muette.

**Refus** : un écart absent du rapport.

### Étape 4 — la purgue s'applique aux deux voies (T22)

Les clips de `vive/OUT/` entrent dans `SF_14_CAMOUFLAGE` puis `SF_15_LUTHER`
**sans branchement conditionnel** : même CLI, mêmes arguments, même porte V7.
`lac_f05_camouflage.py --batch` accepte déjà un dossier — c'est ce qu'on utilise.

**Oracle T22** : `qa_pass: true` et `suspicious_tags_after: []` (hors
`encoder=`) sur les 5 clips vive, consigné dans
`REVIEW/render/luther_batch_report.json`.

**Refus** : un tag suspect résiduel, ou une voie qui contournerait SF_14/SF_15.

### Étape 5 — `elocution.py` (SF_06, second temps des métadonnées)

`FR_A_CERVEAU/SF_06_LIBELLUS/CODEBASE/elocution.py`, stdlib + urllib :

- appel NVIDIA NIM (`integrate.api.nvidia.com/v1/chat/completions`), clé
  **uniquement** via `os.environ["NVIDIA_API_KEY"]` (T0-V2 : aucun secret en
  clair) ;
- la sortie du modèle **repasse le validateur de `titres.py`** — un titre
  refusé est rejeté, jamais accepté ;
- 3 reprises (1 min / 5 min / 25 min) puis **repli gabarit pur** :
  `elocution_fallback: true`. Un siège n'échoue jamais pour un titre ;
- chaque appel écrit au ledger : modèle, essais, crédits consommés, repli.

Position structurelle : après M1 (sélection, cap 15) — le LLM ne peut pas peser
sur ce qui est choisi. Exception réseau **n°3** inscrite dans
`TRACKING/LES_EXCEPTIONS.md` (EXC-M13) avec ses trois grep.

**Oracles** : T23 (20/20 titres passent le validateur, 0 nom propre, ordre
d'information intact) ; T24 (clé invalide ⇒ 3 reprises, repli, siège complet,
ledger tracé).

### Étape 6 — `programma.py` (SF_17_PROGRAMMA, V8)

`FR_B_CREATION/SF_17_PROGRAMMA/CODEBASE/programma.py` :

- tirage **une fois par siège** d'intervalles uniformes ∈ [4 h, 10 h], graine
  écrite au ledger (déterministe et auditable) ;
- `schedule.json` écrit dans `REVIEW/schedule.json` + provenance
  `REVIEW/schedule.provenance.json` (D-4), et copie dans `EXPORT/` ;
- publication YouTube : `videos.insert` avec `privacyStatus: private` +
  `publishAt` natif, `thumbnails.set` si miniature fournie ;
- idempotence : `videos.list` avant `insert` ; si trouvé ⇒ `deja_publie` ;
- backoff 403 `quotaExceeded` : 1 h → 4 h → 12 h puis `failed_publish`,
  **jamais de re-tirage du calendrier**.

**Oracles** : T25 (9 créneaux, chaque intervalle ∈ [4 h, 10 h], aucun cluster) ;
T26 (même graine ⇒ fichier identique, graine au ledger) ; T27 (chaque créneau
> maintenant + 4 h, `privacyStatus=private` et `publishAt` présents en dry-run).

**Refus** : un créneau hors bornes, un tirage rejoué, ou un secret en clair.

### Étape 7 — `v2_publish.yml`

Cron horaire + `workflow_dispatch`, `permissions: contents: read`, secrets
`YT_OAUTH_CLIENT_ID` / `YT_OAUTH_CLIENT_SECRET` / `YT_OAUTH_REFRESH_TOKEN`.
Mode `--dry-run` par défaut : la requête est capturée et vérifiée dans l'artefact
`v2-dry-run.json`, **rien n'est publié** tant que V8 n'a pas validé le
`schedule.json`.

**Refus** : un job publiant sans `validated_by_magos: true` sur le schedule.

### Étape 8 — idempotence (T28)

Deux exécutions du cron sur le même `schedule.json` : **une** ligne ledger par
clip, zéro doublon, le second passage répond `deja_publie` avec l'identifiant
existant.

**Refus** : un doublon possible, ou une ligne ledger manquante.

### Étape 9 — siège mesuré + documentation

Premier siège V2 complet (une VOD courte, voie vive, 5 clips) puis :

- écrire les chiffres réels avec leurs **cinq éléments** (valeur, unité, période,
  population, source) : temps par clip sur runner sans GPU, crédits NVIDIA
  consommés, unités YouTube (pire cas < 900/10 000), dans
  `TRACKING/PARCOURS_V2.md` ;
- remplacer `ATTENDU` par la sortie réelle des T20–T29, consigner dans
  `TRACKING/MURUS_LOG.md` ;
- mettre à jour `MANIFEST.md`, `README.md`, `TRACKING/INDEX.md`,
  `TRACKING/ERRATA.md` (tout écart trouvé en chemin), `TRACKING/LES_EXCEPTIONS.md`
  (EXC-M13 élocution, EXC-M14 vendor figé) ;
- test de doctrine T0-V2 : `grep -rE "NVIDIA_API_KEY|REFRESH" --include="*.py"`
  ne doit renvoyer que des `os.environ` ; `grep -rni ollama` sur
  `vive_runner.py` = 0 ligne ;
- job CI de merge gate sur la PR `v2 → main` : refuse tant que T20–T29 ne sont
  pas verts.

### Risques et leur atténuation (repris du CDC, tenus par le plan)

| risque | tenu par |
|--------|----------|
| le moteur vive exporte des métadonnées sales | étape 4 (T22) — SF_14/SF_15 sans exception, V7 refuse `qa_pass: false` |
| le LLM d'élocution glisse dans la sélection | étape 5 — position après M1, validateur, exception nommée, T24 |
| publication bannie | étape 6/7 — API officielle, intervalle 4–10 h, TikTok retiré, idempotence |
| runner sans GPU trop lent pour le live | étape 9 — temps réel mesuré et écrit, jamais supposé |
| crédits NVIDIA épuisés | étape 5 — ≤ 15 titres + 3 reprises + repli gabarit |
| quota YouTube dépassé | étape 6 — pire cas < 900/10 000, backoff gravé |
| vendor abandonné en amont | D-7 — copie figée, `VENDOR.md` daté et commité |
| biais de survie | protocole inchangé — 45 clips, échecs cherchés |

### Ce que ce plan refuse de faire

- réécrire les CLI pillées (elles gardent leurs arguments d'origine) ;
- ajouter une sous-frégate sans artefact propre ;
- publier quoi que ce soit sans signature opérateur ;
- écrire un chiffre sans ses cinq éléments ;
- fusionner `v2` dans `main` avant T20–T29 verts.

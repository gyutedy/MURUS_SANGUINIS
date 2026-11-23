# PARCOURS_V2 — ce que la branche `v2` a réellement exécuté

> Document opposable, bilingue (EXC-M8). Il ne décrit que ce qui a tourné, avec
> la preuve, le run et le chiffre. Ce qui n'a pas encore tourné est marqué
> **ATTENDU** — jamais présenté comme acquis.

## EN — what actually ran on branch `v2`

Two pieces are executed and proven:

**1. The live engine (`vive` path), run `45206542668`.** Five clips A01→A05, one
GitHub Actions job per clip, `fail-fast: false`. Each job downloaded the source
(7 191,2 MB, measured), deposited it once in the engine's data directory, asked
`POST /export` for its signed window with `captions: false`, then went through the
same finishing chain as V1: `PORTE VIVE` → SF_14 camouflage → `qa_pass` gate →
SF_15 luther → artifact `livrable-vive-<id>`. Measured on A01: 19,6 MB delivered,
34,4 s of engine cut for a 30 s window, `qa_pass true` (h264). Zero LLM calls,
zero browser, zero title or subtitle burned by the engine.

**2. The title second pass (`elocution`) and the schedule (`programma`).** Both are
proven by offline oracles T23→T28: the LLM's proposal is re-judged by the repo's
own validators and a rejected title is never accepted; with no key, three attempts
then a declared template fallback; the calendar draws each interval uniformly in
[4 h, 10 h] from a seed written to the ledger, is byte-identical for the same seed,
refuses to publish an unsigned schedule, and checks existence before any insertion.

**Not measured yet — ATTENDU:** the full V2 siege on a real source with the
NVIDIA key and the YouTube OAuth secrets (T29). No credit count, no real upload,
no publishAt confirmed by YouTube has been produced yet.

## FR — ce qui a réellement tourné sur la branche `v2`

### 1. Le moteur vive — run `45206542668`

| élément | valeur mesurée | source |
|---------|----------------|--------|
| clips rendus | 5 / 5 (A01→A05), un job par clip | jobs du run `45206542668` |
| source téléchargée | 7 191,2 Mo (VOD Twitch entière) | log du job `vive A01` |
| clip A01 | 19,6 Mo, fenêtre 1376,2→1406,2 s | rapport du job |
| temps moteur A01 | 34,4 s pour une fenêtre de 30 s | rapport du job |
| sous-titres du moteur | aucun (`captions: false`) | `PORTE VIVE` : ok |
| titre gravé par le moteur | aucun (D-5) | `PORTE VIVE` : ok |
| LLM appelé | aucun (Ollama neutralisé, détection refusante) | `PORTE VIVE` : ok |
| purgue | SF_14 puis SF_15, `qa_pass true` (h264) | log `CAMOUFLAGE A01 : qa_pass true` |

Les cinq jobs sont indépendants : aucun n'attend un artefact d'un autre. C'est la
règle « un job par clip » tenue sur la voie vive comme sur la voie premium.

**Coût déclaré** : 5 jobs × 7,19 Go = ~36 Go de transfert pour ce proof, parce que
chaque job télécharge sa source lui-même. Pour un usage courant, la même source
sera déposée une fois (artefact ou cache) — c'est une optimisation à faire, pas un
défaut caché.

### 2. Les titres (SF_06) et le calendrier (SF_17)

Prouvés hors ligne, sans réseau, par les oracles du plan :

- **T23** — la réponse « abonne-toi maintenant » est **refusée** par
  `title_forge.validate` (appel à l'action), et une seconde proposition valide est
  acceptée, puis re-confirmée par le validateur du dépôt : le LLM ne décide pas.
- **T24** — trois réponses inutilisables ⇒ `elocution_fallback: true`, repli
  gabarit, siège complet, ledger écrit. Un titre raté n'arrête jamais un siège.
- **T25** — 9 livrables ⇒ 9 créneaux, chaque intervalle tiré dans [4 h, 10 h],
  aucun groupement régulier (graine `20261123` : 4,53 h à 9,38 h).
- **T26** — même graine ⇒ fichier identique au bit près ; graine différente ⇒
  calendrier différent.
- **T27** — calendrier non signé ⇒ refus code 3 ; signé ⇒ `dry-run` capture la
  requête exacte (`privacyStatus: private`, `publishAt` présent, `part:
  snippet,status`) et ne publie rien.
- **T28** — vérification d'existence **avant** l'insertion : un clip déjà publié
  répond `deja_publie` avec son identifiant, aucun upload n'a lieu. Un `403
  quotaExceeded` recule (1 h → 4 h → 12 h) sans jamais retirer un créneau.

### 3. Ce qui reste ATTENDU

- **T29** — le siège V2 complet sur une source réelle, avec `NVIDIA_API_KEY` et
  les trois secrets OAuth YouTube : crédits NVIDIA réellement consommés, unités
  YouTube réellement débitées, `publishAt` confirmé par la plateforme.
- Les temps par clip restent **mesurés sur un seul clip** (A01). Les publier pour
  les neuf demanderait d'extraire les cinq rapports d'artefacts — c'est faisable,
  ce n'est pas fait.

### 4. Les cinq portes qui peuvent refuser la voie vive

| porte | refuse si |
|-------|-----------|
| `G1` (jobs) | un des deux codex n'a pas `validated_by_magos: true` |
| `PORTE VIVE` | LLM détecté, navigateur lancé, sous-titre ou titre gravé par le moteur, 0 clip rendu, mapping muet |
| `PORTE ELOCUTION` | un titre accepté sans verdict positif, ou un asset sorti sans titre |
| `PORTE qa_pass` (SF_14) | codec ≠ h264, ou tag résiduel non-`encoder=` |
| `PORTE SCHEDULE` | calendrier non signé, vide, non-`private`, sans `publishAt` |

Une porte qui refuse est une porte qui fonctionne : c'est écrit dans la doctrine,
et la V2 n'y ajoute aucune exception.

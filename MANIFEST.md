# MANIFEST — MURUS SANGUINIS

Chaque sous-frégate trace vers un dossier réel pillé. Rien n'est inventé sauf la
numérotation, SF_01/SF_08/SF_16 (composites) et le nom.

## FR_A_CERVEAU (source : PERTURABO@pari-forge-perturabo-xs4c, MONDES_FORGES/CLIPPING)

| SF | Pillé de | Artefact OUT |
|----|----------|--------------|
| SF_01_VIGILIA | F00_IRON_SENTINEL/F00A_CAPTEURS + MARK1/M00A_DIRECTIVA | directive_parsed.json |
| SF_02_VERDICTUM | F01_SCOUT + F02_TYRANT_CAMP | verdict GO/NO-GO |
| SF_03_ANGULI | ANGLESMITH (F02_TYRANT_CAMP/CODEBASE/anglesmith.py + libs/angle_forger.py + libs/learnings_weight.py) | angles forgés |
| SF_04_SELECTIO | MARK1/M00B_SELECTOR + libs/s1_context.py + skill (gta6-live-clipper/scripts/live.py : RMS astats + vitesse chat IRC) + radar chat_pulse.py | selection.json |
| SF_05_VOX | MARK1/M00F_VOX | transcript.json |
| SF_06_LIBELLUS | MARK1/M00C_METADATA | metadata.json |
| SF_07_VEXILLUM | MARK1/M00D_VEXILLUM | watermark.json + fichier |
| SF_08_PURGATIO ⚠️ | mécanismes : X1 anti-clés-mortes (gates.py:446-481) + normalizePurAntiDetection (codexExport.js) | pack_pur.json |
| SF_09_PORTAS | MARK1/M00E_PACKAGER | production_pack_*.json dans EXPORT/ + ledger |
| GATES/ | MARK1/libs/gates.py (+ référence ORCHESTRATOR/CODEBASE/gates.py) | — |

## FR_B_CREATION (source : LACRIMAE-FULL@sanguinala-v1)

| SF | Pillé de | Artefact OUT |
|----|----------|--------------|
| SF_10_SPECULUM | F03_PREVIEW (codexExport.js, bridgeClipper.js, _purPackComposition.jsx, antiDetection.js) | REVIEW/codex_render.json |
| SF_11_LUMEN | F03_POSTPROD/CODEBASE/glow (preview_glow.py) | REVIEW/codex_postprod.json |
| SF_12_FABRICA | F01_LOOK (→ look/) + F02_MONTAGE (→ montage/) | clips rendus |
| SF_13_POLITURA | F03_POSTPROD (postprod.py, caption/, lut/) | clips finis + postprod_report.json |
| SF_14_CAMOUFLAGE | F05 (lac_f05_camouflage.py) — SANS gate | MP4 camouflé + rapport dev10-v2.camouflage.v1 |
| SF_15_LUTHER | F06_LUTHER (lac_f06_luther.py) — SANS gate | MP4 livrable + rapport dev10-v2.luther.v1 |
| SF_16_MISSIO ⚠️ | F06_TRACKER (PERTURABO) + règle C3 | clips soumis + readings |
| GATES/ | pattern MARK1 gates.py (V5, V6/GL2, G1, PP2, V7) | — |

## Racines

| Dossier | Pillé de |
|---------|----------|
| ARCHIVUM/ | CLIPPING/ARCHIVUM (squelette : parser + exemples ; données de production NON copiées) |
| CONTRACTS/ | CLIPPING/CONTRACTS (clipping_rules.md, whop_rules.md, copywriting_doctrine.md, production_pack_schema.json) |
| tools/ | LACRIMAE/tools (codex.py, ffmpeg_bin.py, pur_aggregate.py, test_codex.py, convert_pur_pack.mjs) |
| BRIDGE/, SHARED/ | LACRIMAE (raccourcis relatifs adaptés à la nouvelle racine) |
| REVIEW/ | LACRIMAE/REVIEW (README + SCHEMAS + codex exemples) |
| EXPORT/ | CLIPPING/EXPORT (squelette : ledger header + sieges/ ; packs réels NON copiés) |
| config/selection.json | MARK1/config/selection.json (zéro seuil en dur) |
| TRACKING/ | CLIPPING/TRACKING (INDEX.md) + MARK1 (LES_EXCEPTIONS.md) + MURUS_LOG.md ⚠️ |

## Hors flux (non copié, conforme CDC)

- `F04_HEISENBERG` — README « HORS FLUX V1 », jamais appelé par run_all.py.
- `F00B_VOX` / `F00C_VOX` — l'opinion LLM est hors verdict (décision D2).
  **Seule exception** : `libs/chat_pulse.py` copié dans SF_04_SELECTIO/CODEBASE/detect/
  pour le profil direct.
- Données de production réelles (EXPORT packs, ARCHIVUM 24 Mo, campagnes) — non copiées.

## Exécution distante

- `.github/workflows/murus_tests.yml` — pytest + tests de doctrine (T0) à chaque push.
- `.github/workflows/murus_transcribe.yml` — transcription GPU Modal
  (pattern `perturabo_transcribe.yml`, secrets MODAL_TOKEN_ID/MODAL_TOKEN_SECRET).

## Règles opposables (documents du projet, pas des conversations)

| Fichier | Ce qu'il impose | Garde-fou |
|---|---|---|
| `TRACKING/DOCTRINE_ANTI_REMPLISSAGE.md` | Si la VOD offre 6 clips sur 15 demandés, on rend 6 et on l'écrit. Aucun remplissage. | `tests/test_murus.py::test_t18_anti_remplissage` + champs `nb_demande/nb_retenu/manque/remplissage_refuse` dans le pack |
| `TRACKING/DOCTRINE_BILINGUE.md` | Tout document opérateur existe en EN et en FR. | `tests/test_murus.py::test_t17_docs_operateur_bilingues` |
| `ARCHIVUM/demande/README.md` | Le projet demande (`nb_clips` 1..15, `selection_approved`), l'opérateur répond au lancement, le projet trace la provenance. | `FR_A_CERVEAU/GATES/demande.py` (`exiger` refuse toute valeur absente ou > 15) |
| `TRACKING/LES_EXCEPTIONS.md` | Toute dérogation est nommée avec son grep (EXC-M1 → EXC-M8). | Revue à chaque gate |
| `TRACKING/CODEX_SIGNES.md` | Aucun rendu sans les deux codex signés ; le registre dit lequel manque. | `tests/test_murus.py::test_t22_codex_render_signe` + `gates_b.gate_g1_exige_codex_signes` |
| `TRACKING/PREVIEWS_ROLES.md` | Preview 1 = LOOK (`codex_render.json`), preview 2 = postprod (`codex_postprod.json`). Aucun panneau de postprod dans la preview 1. | `tests/test_murus.py::test_t19_previews_separees` |
| `TRACKING/ERRATA.md` | Les erreurs déjà payées (nommage `pur_<id>.mp4`, `$GITHUB_OUTPUT`, `: ` interdit dans un nom d'étape, identité du Player, provenance en sidecar, Pages unique, pack commité, un job par clip). | `tests/test_murus.py::test_t20_errata` |
| `FR_B_CREATION/tools/recuperer_clip.py` | Après X1, le clip (preview 1) et une frame (preview 2) sont récupérés **avant** tout codex. | `murus.py` refuse (`rc=6`) s'il n'y a pas de clip |

## Fichiers du parcours réel (ajoutés après exécution en conditions réelles)

| fichier | rôle |
|---------|------|
| `.github/workflows/murus_rendu.yml` | rendu : porte (2 codex signés, pack, PNG) → `clip` matrice (un job par clip) → `assemble` + zip |
| `.github/workflows/murus_v7.yml` | V7 : manifeste de soumission, porte `qa_pass`, `REVIEW/submissions.json` |
| `FR_B_CREATION/SF_13_POLITURA/CODEBASE/caption/transcript_slice.py` | découpe de la transcription réelle sur la fenêtre du clip (E-18) |
| `FR_B_CREATION/SF_13_POLITURA/CODEBASE/caption/ass_render.py` | gravure ASS : résolution du nom de police (E-17), pop-in = un mot (E-19) |
| `REVIEW/render/render_report.json` | rapport de rendu commité (preuve de livraison) |
| `REVIEW/render/*_batch_report.json` | preuves `qa_pass` commitées (E-15) |
| `REVIEW/submissions.json` | manifeste V7 : sha256, checklist, statut `a_poster` |
| `TRACKING/PARCOURS_REEL.md` | le parcours réel, EN + FR, opposable |

## Branche v2 — l'assemblage (deux moteurs, une voix, un calendrier)

Créée depuis `main` (= V1, 28 portes vertes). Aucun fichier de V1 n'est supprimé.

| ajout | rôle | étiquette |
|-------|------|-----------|
| `CDC/MURUS_SANGUINIS_CDC_V2.html` | le cahier des charges V2, dans le dépôt | CRÉÉ (V2) |
| `TRACKING/PLAN_V2.md` | plan d'implémentation opposable, 10 étapes, oracles T20–T29 | CRÉÉ (V2) |
| `FR_B_CREATION/SF_12_FABRICA/vive/vendor/neonclipping/` | moteur vive figé (MIT, commit `0525004`) — 112 fichiers, code + tests + modèle ONNX | PILLÉ (NeonClipping) |
| `FR_B_CREATION/SF_12_FABRICA/vive/VENDOR.md` | provenance, exclusions déclarées, interface réelle du moteur | CRÉÉ (V2) |
| `FR_B_CREATION/SF_12_FABRICA/vive/vive_runner.py` | wrapper headless (`POST /make` + sondage + collecte) | CRÉÉ (V2) |
| `FR_A_CERVEAU/SF_06_LIBELLUS/CODEBASE/elocution.py` | 2e temps des métadonnées (NVIDIA NIM, re-jugé par les gabarits) | CRÉÉ (V2) |
| `FR_B_CREATION/SF_17_PROGRAMMA/` | publication programmée YouTube (calendrier 4–10 h, `publishAt`) | CRÉÉ (V2) |
| `.github/workflows/v2_publish.yml` | cron de publication (dry-run par défaut) | CRÉÉ (V2) |
| `.github/workflows/v2_elocution.yml` | passe d'élocution dans le siège | CRÉÉ (V2) |
| `tests/test_murus_v2.py` | T20–T29, un oracle par test | CRÉÉ (V2) |
| `FR_A_CERVEAU/SF_05_VOX/CODEBASE/transcrire_vod.py` | transcription du siège en fan-out Modal (8 VM), repli CPU déclaré | CRÉÉ (V2) |
| `MODAL/transcribe.py#transcribe_chunk` | fonction Modal appelée en parallèle, mots déjà datés en temps VOD | CRÉÉ (V2) |
| `TRACKING/PARCOURS_V2.md` | ce que la branche `v2` a réellement exécuté, chiffres et portes (EN + FR) | CRÉÉ (V2) |


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

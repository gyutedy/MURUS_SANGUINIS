# SF_08_PURGATIO — le pack épuré

⚠️ Sous-frégate NOUVELLE (la seule du cerveau avec SF_16 côté création). Elle n'invente rien :
elle assemble deux mécanismes réels pillés :

1. **Anti-clés-mortes** — hérité de `X1_EXPORT` (`MARK1/libs/gates.py:446-481`) : le pack ne doit
   contenir aucune clé absente du schéma `CONTRACTS/production_pack_schema.json`. Une clé morte est
   **NOMMÉE** dans le rejet — jamais silencieuse.
2. **`normalizePurAntiDetection`** — hérité de `F03_PREVIEW/CODEBASE/src/preview/codexExport.js` :
   mirror/speed/crop normalisés ; vocabulaire `PUR_STYLE_VALUES = ['reframing','blur']`.

## Gate

`P1` **précède** SF_08 (porte nouvelle, ⚠️ du CDC). La porte refuse le pack tant que
`purgatio_report.json` porte `pur_pass: false`.

## Artefact OUT

`OUT/pack_pur.json` + `OUT/purgatio_report.json` (schéma `murus.purgatio.v1`).

## CLI

```
python purgatio.py --pack <production_pack.json> [--schema CONTRACTS/production_pack_schema.json] [--out pack_pur.json]
```

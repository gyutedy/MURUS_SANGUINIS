# SIÈGE RÉEL — 2026-11-20 23:28 UTC

- VOD : ``
- plateforme : ``
- directive : `ARCHIVUM/campaign/campaign_directive.json`
- code retour du moteur : `2` (0 = siège complet, 2 = porte fermée, 3 = ORACLE attendu)

## Chaîne des portes (sortie réelle du moteur)

```
[OK] TRANSCRIPT : v2909800627_transcript.json -> 5 segments choisis
[FAIL] D0_DIRECTIVE : champs manquants: payout; aucun payout exploitable
```

Traces : `2026-11-20T232858_nopack.json`

## M1 sur données réelles

Porte : **M1_SELECTION** — 5 segments, langue en

| id | début | fin | durée | texte réel de la VOD |
|---|---|---|---|---|
| A01 | 577.6s | 607.6s | 30.0s |  |
| A02 | 1667.4s | 1697.4s | 30.0s |  |
| A03 | 510.6s | 540.6s | 30.0s |  |
| A04 | 1376.2s | 1406.2s | 30.0s |  |
| A05 | 709.1s | 739.1s | 30.0s |  |

## Ce que l'opérateur doit déclarer (rien n'est deviné)

Fichier : `ARCHIVUM/campaign/operator_declarations.json`

| champ | état |
|---|---|
| `warmup_days` | **non déclaré → porte refusée** |
| `campaign.rate_usd_per_1k` | **non déclaré → porte refusée** |
| `campaign.funded` | **non déclaré → porte refusée** |
| `campaign.budget_remaining_usd` | **non déclaré → porte refusée** |
| `campaign.cap_usd_per_clip` | **non déclaré → porte refusée** |
| `focus_declared` | **non déclaré → porte refusée** |

Compléter ce fichier = répondre aux portes. Aucune valeur n'est inventée par le code.

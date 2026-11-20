# Directive de campagne — PREME (clipify)

Source : directive fournie par l'opérateur le 2026-11-20.
Asset fourni : `watermark.png` (voir `ARCHIVUM/campaign/watermarks/preme.png`).
VOD du siège : https://www.twitch.tv/videos/2909800627

Texte de la directive, verbatim :

```
Clip Requirements
Preme must be the main focal point of the clip (cannot be in the background, or appear only for a brief moment)
The Preme watermark must be clearly visible and centered

Violations
Banned on all campaigns
Anything below gets your clip disqualified and can get you removed from every campaign we run. Do not waste your time or ours.
Logos of any kind (besides those required)
Not Utilizing The Provided Content
Not Following Requirements
Posts that add no value (e.g. Random moments + I CAN'T BELIEVE THAT HAPPENED)
Botting, Fake Engagement Groups
Wrong Audience
```

Durée : **sans limite** (déclaration de l'opérateur : « ce n'est pas limité dans le temps »).

## Ce qui n'est PAS dans la directive et ne sera pas inventé

| Champ | État | Conséquence |
|---|---|---|
| `payout.per_platform` (USD / vues) | **non communiqué** | `D0_DIRECTIVE` refuse : « aucun payout exploitable ». Aucune valeur n'est supposée. |
| `funded`, `budget_remaining_usd` | **non communiqués** | `A2_CAMPAIGN` refusera. |
| `account.warmup_days` | **non communiqué** | `A1_ACCOUNT` refusera. |
| handle de caption | déduit du watermark fourni (`@Preme`) | à confirmer par l'opérateur |

Le seul fait ajouté par le moteur est la mention de divulgation (`#ad`), exigée par la
règle C2 du forge comme condition de paiement — pas une précaution.

## Traduction en directive machine

`ARCHIVUM/campaign/campaign_directive.json` (lue à chaque siège par M00A_DIRECTIVA).

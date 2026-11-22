# SIÈGE RÉEL / REAL SIEGE — 2026-11-22 05:54 UTC

Document bilingue (EXC-M8, `TRACKING/DOCTRINE_BILINGUE.md`) : EN = source de
vérité machine, FR = traduction de compréhension.

- VOD : `https://www.twitch.tv/videos/2909800627`
- plateforme / platform : `youtube_shorts`
- directive : `ARCHIVUM/campaign/campaign_directive.json`
- code retour moteur / engine rc : `3` (0 = siège complet, 2 = porte fermée, 3 = ORACLE attendu)

## EN — Gate chain (real engine output)

```
[OK] ANTI_REMPLISSAGE : demande 15, retenu 15 — le compte est tenu sans remplissage.
[OK] TRANSCRIPT : v2909800627_transcript.json -> 15 segments choisis
[OK] D0_DIRECTIVE : PREME_CLIPIFY_OPEN | en | 0.60 $/1k | 4 plates | 4 captions
[OK] M0B_CYCLE : cycle 2026-11-20 -> 2099-12-31, ouvert
[OK] M1_SELECTION : 15 segments, langue en
[OK] M5_VOX : 15 segments, 0 transcrits
[WAIT] waiting_oracle : /home/runner/work/MURUS_SANGUINIS/MURUS_SANGUINIS/FR_A_CERVEAU/ORACLE/pending/overlay_siege_preme.json
```

## EN — M1 on real data

Porte / gate : **M1_SELECTION** — 9 segments, langue en

| id | window | | transcript (real VOD) |
|---|---|---|---|
| A01 | 1376.2s → 1406.2s (30.0s) | force=8 | Probably, like, I don't know, 30, 45 minutes. Anybody from New York? Yeah. That's deep in Brooklyn. How are we? See, I have to find it. That's why I never make it. It's hard. It's |
| A02 | 709.1s → 739.1s (30.0s) | force=7 | his family is the biggest art collector in the world. So they got like $500 million art piece all throughout the house. She decided to turn the phone off. Right? Right. So y'all ai |
| A03 | 1727.5s → 1757.5s (30.0s) | force=5 | and we gave a truck load in 16-year-olds before you do that. When you do that? When you do that? I'll do it all year. We'd love to get ready for a whole big truck of drugs. Hey, he |
| A04 | 1296.0s → 1326.0s (30.0s) | force=4 | You said that was my great 7-8. Love. Love. Love. Love. Love. Yeah, yeah, yeah. This is flicking on that shit go crazy. What's up, y'all? What's up, y'all? What's up, y'all? What's |
| A05 | 1587.5s → 1617.5s (30.0s) | force=4 | Next 24 hours we challenge everybody to one random act of kindness. We're gonna do some right now. Let's hopefully get inspired. Dr. I'm using the chat. I'm ready to rock. Come on, |
| A06 | 1623.7s → 1653.7s (30.0s) | force=4 | Marcus Brown 23. Twizzy Tezo. Cup of Perp. Chat with the word, man. Fuck, you look good, Tristan. This is the type of listening. Tristan's great. It's been my homeboy. He was a kid |
| A07 | 294.0s → 324.0s (30.0s) | force=1 | How's your day going? Something so small that I could change someone's day, life Because you don't know what we're going through, right? So whenever I walk by a stranger I always f |
| A08 | 381.0s → 411.0s (30.0s) | force=1 | Nothing else matters Hard What's your mom's name? Andrea Brooks Andrea Andrea Andrea What's the biggest lesson you learned from Andrea? Oh If she was listening right now, what do y |
| A09 | 422.1s → 452.1s (30.0s) | force=1 | Do you like going to work with this person every day? Yes That's beautiful, man. Thank you for sharing that, too. I really appreciate it. Very good. Yeah I thought that was me. Wha |

## EN — What the operator must declare (nothing is guessed)

Fichier / file : `ARCHIVUM/campaign/operator_declarations.json`

| champ / field | état / state |
|---|---|
| `—` | **undeclared → gate refused** |
| — | all declarations provided (example values, EXC-M7) |

Filling this file = answering the gates. The code never invents a value.

## FR — Chaîne des portes (sortie réelle du moteur)

```
[OK] ANTI_REMPLISSAGE : demande 15, retenu 15 — le compte est tenu sans remplissage.
[OK] TRANSCRIPT : v2909800627_transcript.json -> 15 segments choisis
[OK] D0_DIRECTIVE : PREME_CLIPIFY_OPEN | en | 0.60 $/1k | 4 plates | 4 captions
[OK] M0B_CYCLE : cycle 2026-11-20 -> 2099-12-31, ouvert
[OK] M1_SELECTION : 15 segments, langue en
[OK] M5_VOX : 15 segments, 0 transcrits
[WAIT] waiting_oracle : /home/runner/work/MURUS_SANGUINIS/MURUS_SANGUINIS/FR_A_CERVEAU/ORACLE/pending/overlay_siege_preme.json
```

## FR — M1 sur données réelles

Porte / gate : **M1_SELECTION** — 9 segments, langue en

| id | fenêtre | | texte réel de la VOD |
|---|---|---|---|
| A01 | 1376.2s → 1406.2s (30.0s) | force=8 | Probably, like, I don't know, 30, 45 minutes. Anybody from New York? Yeah. That's deep in Brooklyn. How are we? See, I have to find it. That's why I never make it. It's hard. It's |
| A02 | 709.1s → 739.1s (30.0s) | force=7 | his family is the biggest art collector in the world. So they got like $500 million art piece all throughout the house. She decided to turn the phone off. Right? Right. So y'all ai |
| A03 | 1727.5s → 1757.5s (30.0s) | force=5 | and we gave a truck load in 16-year-olds before you do that. When you do that? When you do that? I'll do it all year. We'd love to get ready for a whole big truck of drugs. Hey, he |
| A04 | 1296.0s → 1326.0s (30.0s) | force=4 | You said that was my great 7-8. Love. Love. Love. Love. Love. Yeah, yeah, yeah. This is flicking on that shit go crazy. What's up, y'all? What's up, y'all? What's up, y'all? What's |
| A05 | 1587.5s → 1617.5s (30.0s) | force=4 | Next 24 hours we challenge everybody to one random act of kindness. We're gonna do some right now. Let's hopefully get inspired. Dr. I'm using the chat. I'm ready to rock. Come on, |
| A06 | 1623.7s → 1653.7s (30.0s) | force=4 | Marcus Brown 23. Twizzy Tezo. Cup of Perp. Chat with the word, man. Fuck, you look good, Tristan. This is the type of listening. Tristan's great. It's been my homeboy. He was a kid |
| A07 | 294.0s → 324.0s (30.0s) | force=1 | How's your day going? Something so small that I could change someone's day, life Because you don't know what we're going through, right? So whenever I walk by a stranger I always f |
| A08 | 381.0s → 411.0s (30.0s) | force=1 | Nothing else matters Hard What's your mom's name? Andrea Brooks Andrea Andrea Andrea What's the biggest lesson you learned from Andrea? Oh If she was listening right now, what do y |
| A09 | 422.1s → 452.1s (30.0s) | force=1 | Do you like going to work with this person every day? Yes That's beautiful, man. Thank you for sharing that, too. I really appreciate it. Very good. Yeah I thought that was me. Wha |

## FR — Ce que l'opérateur doit déclarer (rien n'est deviné)

Fichier / file : `ARCHIVUM/campaign/operator_declarations.json`

| champ / field | état / state |
|---|---|
| `—` | **non déclaré → porte refusée** |
| — | toutes les déclarations sont fournies (valeurs d'exemple, EXC-M7) |

Compléter ce fichier = répondre aux portes. Aucune valeur n'est inventée par le code.


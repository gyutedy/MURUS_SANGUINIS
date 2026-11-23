# VENDOR — moteur de la voie vive (NeonClipping)

> Trace du copillage. Rien n'est ici sans provenance. Licence MIT conservée à
> côté du code : `LICENSE` (1 120 octets, « Copyright 2026 Ajay K Meena and
> NeonClipping contributors »).

## Origine

| | |
|---|---|
| dépôt | `https://github.com/iamajmeena/neonclipping` |
| commit | `0525004` — 2026-11-22 — « Optional Cloud AI: any OpenAI-compatible provider for moment scoring, titles and hooks » |
| licence | MIT (fichier `LICENSE` copié tel quel) |
| copillé le | 2026-11-23, branche `v2` |
| empreinte locale | 112 fichiers, 1,4 Mo |

## Ce qui est copié

Tout le **code** du moteur, ses **tests** et son **modèle** :

- moteur : `app.py`, `highlights.py`, `smart.py`, `encoders.py`, `jobs.py`,
  `ytdl.py`, `captions*.py`, `subtitles.py`, `facecam_detect.py`, `vision.py`,
  `curation.py`, `learn.py`, `report.py`, `compat.py`, `styling.py`,
  `layouts.py`, `brands.py`, `bundles.py`, `camfx.py`, `phone.py`,
  `previews.py`, `reedit.py`, `standalone.py`, `updater.py`, `watchdog.py`,
  `transcripts*.py`, `translit.py`, `languages.py`, `extras.js`, `app.js`,
  `index.html`, `mobile.html`, `style.css`, `report.js`, `vision.js` ;
- live : `live/live_clip.py`, `live_session.py`, `live/README.txt` ;
- tests : `tests/` (27 fichiers, `REPORT.md`, `fixes.json`, `report.json`) ;
- modèle : `models/face_detection_yunet_2023mar.onnx` (232 589 octets) ;
- méta : `README.md`, `CHANGELOG.md`, `SECURITY.md`, `requirements.txt`,
  `install.sh`, `install.ps1`, `run.sh`, `run.ps1`, `NeonClipping-Setup.bat`,
  `.gitattributes`, `.gitignore`, `donate.json`, `supporters.json`,
  `tools/report-worker/`.

## Ce qui est exclu, et pourquoi (déclaré, jamais silencieux)

| fichier | taille | raison |
|---------|--------|--------|
| `docs/demo.gif` | 1 710 435 o | média de démonstration, aucun rôle d'exécution |
| `docs/NeonClipping-Guide-EN-HI.pdf` | 963 080 o | guide utilisateur du projet amont |
| `docs/demo.mp4` | 408 638 o | média de démonstration |
| `docs/*.jpg`, `docs/guide/*.jpg`, `docs/*.png` | ~400 000 o | captures du guide amont |

Ces fichiers ne sont **pas** nécessaires à l'exécution headless, et ils alourdissent
chaque clone d'Actions. Les `docs/*.md` (dont `DEVELOPMENT-HANDOFF.md`) sont
conservés.

## Interface réelle du moteur (relevée dans le code, pas dans le README)

```
POST /make
  payload : {url, count, min_len, max_len, moments:[{start,end}],
             mode:"fast"|"deep", layout, caption_style, language,
             source_height, moment_profile, accurate, top, cam, game}
  réponse : job asynchrone (state[job]), AUCUN champ "title" n'existe
GET  /make/{job}    état du job ; clips accumulés dans state[job]['clips']
GET  /status/{id}   état générique
refus explicite     info['is_live'] → « Use the Live clipping panel »
réseau              127.0.0.1:NEONCLIPPING_PORT (défaut 8770), uvicorn (fastapi)
LLM                 `model=None` tant qu'Ollama n'est pas lancé : le scoring
                    audio/mouvement suffit (mode "fast")
sous-titres         `captions_yt.py` s'appuie sur les pistes word-timed YouTube
                    (json3) : indisponibles sur une source Twitch
```

Trois conséquences tenues par `PLAN_V2.md` : le runner envoie des **moments**,
il **sonde** le job, et **le titre n'est jamais transmis au moteur** — les titres
restent à SF_06 et sont gravés par notre pile (SF_12 premium / SF_13).

## Mise à jour de ce vendor

Interdite en cours de siège. Toute mise à jour exige : un nouveau commit d'origine
noté ici, la relance des tests du moteur (`tests/`), et la reprise de T20–T22.
Le vendor doit fonctionner même si l'amont disparaît (R18) : aucune dépendance
réseau autre que `yt-dlp` et `pip`.

## EN — summary

Vendored from `iamajmeena/neonclipping` at commit `0525004` (2026-11-22), MIT,
documentation media excluded and listed above. The real engine interface differs
from the CDC prose: `/make` is **asynchronous**, takes **moments** not per-asset
start/end, and accepts **no title**. The runner adapts to the real code; titles
stay with SF_06 and are burned by our own stack.

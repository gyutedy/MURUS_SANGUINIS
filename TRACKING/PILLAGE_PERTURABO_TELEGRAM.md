# PILLAGE TELEGRAM — ce que PERTURABO a deja construit

Source : `gyutedy/PERTURABO`, branche `pari-winner-sensor-m1`, dossier
`MONDES_FORGES/PARI`. Lu le 2026-11-24. **Rien n'est reecrit** : on reprend, on
nomme les trous, on branche.

---

## FR — Les fichiers a reprendre

| Fichier | Role | Lien |
|---|---|---|
| `ORCHESTRATOR/LISTEN/src/index.js` | Cloudflare Worker : webhook Telegram, liste blanche, parsing, ACK, dispatch GitHub, rappels par cron | `MONDES_FORGES/PARI/ORCHESTRATOR/LISTEN/src/index.js` |
| `ORCHESTRATOR/LISTEN/wrangler.toml` | deploiement du Worker + cron `*/15 * * * *` | `.../LISTEN/wrangler.toml` |
| `ORCHESTRATOR/LISTEN/parse.py` | miroir Python du parsing, pour tester sans Cloudflare | `.../LISTEN/parse.py` |
| `.github/workflows/pari_listen.yml` | une commande = un run, `concurrency: pari-campagne` | `.github/workflows/pari_listen.yml` |
| `.github/scripts/write_env_pari.py` | reconstruit `env_pari` depuis les Secrets, n'ecrit que les non-vides, n'affiche jamais | `.github/scripts/write_env_pari.py` |
| `CORE/.env.example` | liste des noms de variables, jamais de valeur | `CORE/.env.example` |
| `ORCHESTRATOR/CODEBASE/notifier.py` | reponse Telegram depuis le workflow (`tell()`) | `.../CODEBASE/notifier.py` |

## FR — Le systeme de commandes, tel qu'il est

1. Telegram appelle le Worker (POST). Le Worker verifie l'entete
   `X-Telegram-Bot-Api-Secret-Token` contre `TELEGRAM_WEBHOOK_SECRET` : mauvais
   secret = `403`, sans autre effet.
2. `parseUpdate()` compare `chat.id` a `TELEGRAM_CHAT_ID`. Chat etranger : **ignore**,
   pas de reponse (aucune fuite d'information).
3. Un texte qui ne commence pas par `/` : reponse « Commande inconnue. /help… ».
4. Commande connue : ACK immediat (« Recu `/x` — siege en cours (~1 min) »), puis
   dispatch du workflow avec `cmd`, `capture_text`, `capture_file_id`, `update_id`,
   `message_id`.
5. Le workflow serialise tout le monde via `concurrency: group: pari-campagne`, donc
   deux commandes ne peuvent pas ecraser le meme etat.
6. Reponse finale par `notifier.py` (API `sendMessage`), pas par le Worker.
7. Un cron de 15 min dans le Worker envoie les rappels, calcules depuis un JSON du
   depot, sans ecriture d'etat.

Trois listes portent tout le contrat : `KNOWN` (ce qui est accepte), `LOCAL` (`/help`,
`/aide`, repondu sur place), `CANON` (alias, par exemple `valider1` → `valider-1`).
Un nom absent de `KNOWN` ne declenche **rien**.

## FR — Les variables d'environnement

Cote Worker (secrets wrangler, jamais dans git) :

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TELEGRAM_WEBHOOK_SECRET`
- `GITHUB_DISPATCH_TOKEN`

Cote workflow, ecrites dans `env_pari` (gitignore) par `write_env_pari.py` :
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, plus les cles de donnees du monde PARI
(`API_FOOTBALL_KEY`, `ODDS_API_KEY`, `PARI_WINNER_LLM_*`, `CLOUDFLARE_*`…).

Principe a garder tel quel : **le depot ne contient que des noms**. Le fichier de
valeurs est reconstruit a chaque run depuis les Secrets GitHub, et seules les
variables non vides sont ecrites — un secret absent est absent, pas invente.

## FR — Les cinq trous a corriger pour MURUS

1. **Rejeu possible.** `update_id` est transmis mais nulle part memorise. Telegram
   reessaie s'il n'a pas de 200 a temps : la meme commande peut donc partir deux
   fois. Pour MURUS, un rendu ou une publication ne doit jamais partir deux fois →
   journal `ARCHIVUM/telegram/journal.jsonl` + `update_id` vu = ignore.
2. **Aucune phrase pour les actes couteux.** `/approve` et `/valider-2` sont des
   commandes courtes. Sur MURUS, publier est irreversible → phrase complete tapee
   (`VALIDER PUBLICATION PREME A01`), un bouton ne suffit pas.
3. **Un seul operateur code en dur.** MURUS doit lire une **liste** de `chat_id`
   autorises, pour deleguer plus tard sans redeployer la logique.
4. **Les decisions humaines ne sont pas journalisees** de facon append-only. Les
   etats oui, les actes non. Or c'est l'acte qu'on veut pouvoir opposer.
5. **Une seule destination de dispatch.** MURUS a plusieurs workflows (rendu,
   publication, tests) : le Worker doit choisir le workflow depuis la commande, pas
   depuis `wrangler.toml`.

## EN — Summary

PERTURABO already runs the exact pattern MURUS needs: a Cloudflare Worker receives
the Telegram webhook, verifies `X-Telegram-Bot-Api-Secret-Token`, checks the chat id
against an allowlist, acknowledges the command, then dispatches a GitHub workflow
that serialises commands through a `concurrency` group and replies with
`notifier.py`. Secrets are never in the repo: `write_env_pari.py` rebuilds the env
file from GitHub Secrets at run time and writes only non-empty values. Files to
pillage are listed above. Five gaps must be closed for MURUS: replay protection via
`update_id` journaling, a typed phrase for irreversible actions, an allowlist instead
of a single chat id, append-only logging of human decisions, and per-command workflow
selection instead of one hardcoded workflow.

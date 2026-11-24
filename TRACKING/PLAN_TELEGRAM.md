# PLAN TELEGRAM — piloter le projet depuis un telephone

Objectif : l'operateur se deplace sans son PC et garde la main. Le projet se pilote
par un bot Telegram, **y compris PC eteint**, et **chaque porte (gate) est enregistree**.

Regle qui ne bouge pas : **le projet propose, l'operateur decide**. Le bot n'invente
aucune decision, il presente des chiffres et attend un acte humain.

---

## FR — Les deux architectures possibles

**A. Sondage par cron (recommande pour commencer)**
Un workflow GitHub Actions se reveille toutes les 5 minutes, demande a Telegram les
messages non lus (`getUpdates`), execute ce qui est demande, repond, et enregistre.
Aucun serveur, aucune adresse publique, rien a heberger. Le PC peut etre eteint.
Limite : jusqu'a 5 minutes de latence. Depot public donc minutes Actions gratuites.

**B. Webhook instantane**
Telegram previent une adresse publique, qui declenche aussitot le depot. Il faut un
point d'entree permanent : un Worker Cloudflare (gratuit) ou un endpoint Modal (on a
deja les jetons). Latence de quelques secondes, mais une piece d'infrastructure de
plus a surveiller.

**Decision proposee : A d'abord.** A apporte 90 % du service sans nouvelle piece a
maintenir. On passera a B le jour ou 5 minutes te generont vraiment.

## FR — Ce qu'on peut faire depuis le telephone

| Commande | Effet | Porte |
|---|---|---|
| `/etat` | etat des derniers runs, ce qui tourne, ce qui a echoue | lecture seule |
| `/clips` | liste des livrables `LUTH_A0x_final.mp4` + liens de telechargement | lecture seule |
| `/rapport A01` | le rapport de ce clip : synchro, qa_pass, durees | lecture seule |
| `/rendu` | lance le rendu des 9 clips | **acte explicite** |
| `/valider <porte>` | signe une porte et l'enregistre | **acte explicite** |
| `/publier <clip>` | programme la publication d'un clip | **acte explicite** |
| `/stop <run>` | arrete un run en cours | acte explicite |

Tout le reste est refuse avec le mode d'emploi. Une commande inconnue ne declenche
jamais rien.

## FR — Le journal : tout est enregistre

Chaque message recu, chaque reponse, chaque porte franchie est ecrit dans
`ARCHIVUM/telegram/journal.jsonl` (une ligne = un evenement, jamais reecrite) :

    {"quand":"2026-11-24T18:40:02Z","update_id":88421,"user_id":1234567,
     "commande":"/valider","arguments":"G2","effet":"codex signe","run":"45425091798",
     "resultat":"ok"}

`update_id` rend le rejeu impossible : un message deja traite est **ignore**, pas
rejoue. C'est ce qui evite de lancer deux fois un rendu payant parce que le cron est
passe deux fois.

Le fichier est ajoute au depot par le workflow : l'historique des decisions humaines
est versionne, datable et opposable. Aucune ligne n'est effacee.

## FR — La securite, en trois barrieres

1. **Liste blanche stricte** : le bot ne repond qu'a un `user_id` declare en secret
   (`TELEGRAM_OPERATEUR_ID`). Tout autre message est ignore **et journalise**.
2. **Actes couteux ou irreversibles** : le bot ne les execute que si le message porte
   une phrase complete tapee a la main, par exemple `VALIDER PUBLICATION PREME A01`.
   Un bouton clique ne suffit pas pour publier ou pour depenser. Ce n'est pas une
   serrure sur les rendus de controle (l'operateur l'a refusee) : c'est la forme que
   prend sa signature a distance.
3. **Jetons** : `TELEGRAM_BOT_TOKEN` et `TELEGRAM_OPERATEUR_ID` vivent en secrets
   GitHub, jamais dans le depot. Le bot n'a aucun droit d'ecriture hors des workflows
   du projet.

## FR — Notifications dans l'autre sens

Le projet previent le telephone : fin de rendu (avec les tailles), echec (avec la
cause exacte, pas « erreur inconnue »), porte refusee, derive de synchro mesuree.
Chaque notification porte le numero de run : l'operateur peut aller voir.

## FR — Etapes

0. Squelette : dossier `FR_A_CERVEAU/SF_09_NUNTIUS/`, fichiers declares, tests qui
   echouent franchement tant que le code n'existe pas.
1. `telegram_dire.py` : envoyer un message depuis un workflow (notifications).
2. `telegram_ecoute.py` : lire les messages, filtrer par liste blanche, repondre.
3. Journal + rejeu impossible (`update_id`).
4. Commandes de lecture seule (`/etat`, `/clips`, `/rapport`).
5. Commandes d'acte (`/rendu`, `/valider`), avec phrase complete pour les actes
   couteux, et journal avant/apres.
6. Workflow `telegram.yml` : cron 5 min + `repository_dispatch` (deja pret pour le
   passage au webhook instantane).
7. Tests : liste blanche, commande inconnue, rejeu, acte sans phrase, journal.
8. Documentation bilingue et `PARCOURS_TELEGRAM.md` avec preuves reelles.

## EN — Summary

The operator must be able to steer the project from a phone while the PC is off.
Start with a 5-minute GitHub Actions cron that polls Telegram (`getUpdates`), executes
whitelisted commands, replies and appends every event to
`ARCHIVUM/telegram/journal.jsonl`. A public private-nothing webhook (Cloudflare
Worker or Modal endpoint) can replace the cron later for instant handling. Only one
whitelisted `user_id` is served; any other message is ignored and logged. Costly or
irreversible actions require a full typed phrase such as `VALIDER PUBLICATION PREME
A01`; buttons are for navigation only. `update_id` deduplication makes replays
impossible, so no run is ever launched twice. Notifications flow the other way with
exact causes and run numbers. The project still only proposes: a human act is
required for every gate.

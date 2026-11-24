# ACCES PUBLICATION — où trouver chaque jeton

But : brancher 3 destinations YouTube et 2 (ou 3) destinations Instagram sans jamais
ecrire un secret dans un fichier. Les secrets vivent dans GitHub, **le nom seul** est
ecrit ici.

Regle du projet : un acces absent est **declare absent**, jamais simule. Un rendu ne
public rien. Seule la ceremonie de publication poste, et seulement sur un calendrier
signe.

---

## FR — YouTube (a refaire 3 fois, une par chaine)

Une « chaine » = un compte Google. Il faut, pour chacune : un client OAuth, puis un
jeton de rafraichissement. Trois jeux de trois valeurs.

1. Va sur **https://console.cloud.google.com** avec le compte Google de la chaine.
2. Cree un projet (ou choisis-en un), puis **API et services → Bibliotheque** →
   active **YouTube Data API v3**.
3. **API et services → Ecran de consentement OAuth** : type **Externe**, renseigne le
   nom de l'app et ton e-mail. Ajoute ton propre compte dans **Utilisateurs test**
   (sinon Google bloque avec `access_denied`).
4. **API et services → Identifiants → Creer des identifiants → ID client OAuth**,
   type **Application de bureau**. Tu obtiens :
   - `client_id` qui finit par `.apps.googleusercontent.com`
   - `client_secret`
5. Le jeton de rafraichissement s'obtient par une autorisation dans ton navigateur,
   avec les portees `https://www.googleapis.com/auth/youtube.upload` et
   `https://www.googleapis.com/auth/youtube.readonly`. Le projet fournit l'outil
   `FR_B_CREATION/SF_17_PROGRAMMA/CODEBASE/jetons_youtube.py` : il ouvre l'URL,
   tu colles le code affiche par Google, il te rend le `refresh_token`. Il ne
   l'ecrit jamais dans un fichier du depot.

A poser dans GitHub (Settings → Secrets and variables → Actions → New secret) :

| Chaine | Variables |
|---|---|
| YouTube 1 | `YT1_CLIENT_ID`, `YT1_CLIENT_SECRET`, `YT1_REFRESH_TOKEN` |
| YouTube 2 | `YT2_CLIENT_ID`, `YT2_CLIENT_SECRET`, `YT2_REFRESH_TOKEN` |
| YouTube 3 | `YT3_CLIENT_ID`, `YT3_CLIENT_SECRET`, `YT3_REFRESH_TOKEN` |

Attention : une chaine non verifiee est limitee et ses videos peuvent etre privees.
Une video avec `publishAt` doit partir en `privacyStatus: private`, sinon Google
refuse (`invalidPublishAt`).

---

## FR — Instagram (a refaire 2 ou 3 fois, un par compte)

Instagram ne publie pas sans passer par une app Meta. Il faut : un compte
**Business ou Creator**, une **Page Facebook** rattachee, une app, un jeton longue
duree.

1. Le compte Instagram doit etre **professionnel** (Business ou Creator) et **lie a
   une Page Facebook** que tu administres (app Instagram → Parametres → Compte →
   Passer a un compte professionnel ; puis lier la Page).
2. Va sur **https://developers.facebook.com** → **Mes apps → Creer une app** →
   type **Business**.
3. Dans l'app : **Ajouter un produit → Instagram Graph API**.
4. **Outils → Explorateur Graph API** : selectionne ton app, puis demande les
   autorisations `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement`. Autorise le compte.
5. Recupere l'identifiant du compte Instagram professionnel : requete
   `GET /me/accounts` pour lister les Pages, puis `GET /{page-id}?fields=instagram_business_account`
   → tu obtiens `instagram_business_account.id`, c'est le `IG_USER_ID`.
6. Transforme le jeton court en **jeton longue duree** (60 jours) :
   `GET /oauth/access_token?grant_type=fb_exchange_token&client_id=...&client_secret=...&fb_exchange_token=...`

A poser dans GitHub :

| Compte | Variables |
|---|---|
| Instagram 1 | `IG1_TOKEN`, `IG1_USER_ID` |
| Instagram 2 | `IG2_TOKEN`, `IG2_USER_ID` |
| Instagram 3 (option) | `IG3_TOKEN`, `IG3_USER_ID` |

Un jeton longue duree **expire en 60 jours** : le projet doit le rafraichir avant,
sinon la publication s'arrete sans bruit. La date d'expiration est ecrite dans
`PUBLICATIONS/registre.json`, et un avertissement sort 7 jours avant.

---

## FR — Ce que le projet verifie avant de poster

- le calendrier porte `validated_by_magos: true` (sinon `refus(3)`) ;
- la cle de publication `campagne:token_pack:clip` est **absente** du registre
  (sinon on ne republie pas) ;
- le fichier livre porte `LUTH_` et `qa_pass` est vrai ;
- la destination existe dans `SF_17_PROGRAMMA/config/reseaux.json` ;
- la fenetre horaire declaree est respectee.

Une video ne part jamais deux fois, et jamais sur deux chaines a la fois.

---

## EN — YouTube (three times, one per channel)

Create a Google Cloud project with **YouTube Data API v3** enabled, configure the
OAuth consent screen (External, your account added as a test user), then create an
**OAuth client of type Desktop app** to get `client_id` and `client_secret`. Get a
`refresh_token` for scopes `youtube.upload` and `youtube.readonly` through the
browser flow (`jetons_youtube.py`). Store the three values per channel as
`YT1_*`, `YT2_*`, `YT3_*` secrets. Scheduled videos must be uploaded with
`privacyStatus: private` plus `publishAt`, otherwise Google refuses.

## EN — Instagram (two or three times, one per account)

The account must be professional and linked to a Facebook Page you administer. In
https://developers.facebook.com create a **Business** app, add **Instagram Graph
API**, and grant `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
`pages_read_engagement`. Read the professional account id from
`/{page-id}?fields=instagram_business_account`, exchange the short token for a
60-day long-lived token, then store `IGn_TOKEN` and `IGn_USER_ID`. The project
must refresh the token before it expires and warn 7 days ahead.

## EN — Before anything posts

The signed schedule is required, the publish key `campaign:pack_token:clip` must be
absent from the registry, the delivered file must be a `LUTH_` file with `qa_pass`,
the destination must be declared, and the time window must be respected. Nothing is
ever posted twice, and never to two channels at once.

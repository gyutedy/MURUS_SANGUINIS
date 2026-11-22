# DOCTRINE ANTI-REMPLISSAGE

<!-- BILINGUE:EN -->
## EN — The rule

**If the operator asks for 15 clips and only 6 fulfil the conditions, the project returns 6
and says so.** It never adds a seventh clip to reach the number.

"A clip that fulfils the conditions" means all of these, mechanically:

1. it is not inside the excluded intro (`selection.intro_skip_sec`, 280 s on VOD 2909800627);
2. its text carries at least one stake marker of the language spec (`min_force`);
3. it does not overlap a window already taken (spacing = one target window, 30 s);
4. its overlay is accepted by the engine (constraints + S1 + bait support >= 50 %).

### What is forbidden

- duplicating a moment under another id;
- lowering the spacing to squeeze more windows out of the same passage;
- adding a window whose force is below the floor just to reach the count;
- writing an overlay that is not supported by the text (that is bait, and M2B refuses it —
  producing a title like "win away chat" to pass the gate is exactly what this rule forbids);
- announcing a clip count the pack does not contain.

### What the project must do instead

Write the real numbers, everywhere they are visible:

| field | meaning |
|---|---|
| `nb_demande` | what the operator asked |
| `nb_retenu` | what the VOD actually offers |
| `manque` | `nb_demande - nb_retenu` |
| `remplissage_refuse` | `true` when `manque > 0` |

These four fields are in the exported pack (`mark1.py export`), in `/tmp/m1.json`, in the
operator question (`ARCHIVUM/demande/pending/selection.json`) and in the siege report.
The question asked to the operator states the shortfall explicitly, and his answer applies
to **that** number — not to a number padded to hide it.

### Why

A clip count is a target, not an obligation. A padded clip costs more than a missing clip:
it must be reviewed, signed, rendered, posted, and it dilutes the account. The doctrine
"nothing invented" applies to the clip count exactly as it applies to a missing `payout`.

<!-- BILINGUE:FR -->
## FR — La règle

**Si l'opérateur demande 15 clips et que seules 6 remplissent les conditions, le projet en
rend 6 et le dit.** Il n'ajoute jamais un septième clip pour atteindre le chiffre.

« Un clip qui remplit les conditions » veut dire tout ceci, mécaniquement :

1. il n'est pas dans l'intro écartée (`selection.intro_skip_sec`, 280 s sur la VOD 2909800627) ;
2. son texte porte au moins un marqueur d'enjeu de la spec de langue (`min_force`) ;
3. il ne chevauche pas une fenêtre déjà prise (espacement = une fenêtre cible, 30 s) ;
4. son overlay est accepté par le moteur (contraintes + S1 + soutien anti-bait ≥ 50 %).

### Ce qui est interdit

- dupliquer un moment sous un autre id ;
- réduire l'espacement pour tirer plus de fenêtres du même passage ;
- ajouter une fenêtre dont la force est sous le plancher juste pour atteindre le compte ;
- écrire un overlay non soutenu par le texte (c'est du bait, M2B le refuse — fabriquer un
  titre comme « win away chat » pour passer la porte est précisément ce que cette règle interdit) ;
- annoncer un nombre de clips que le pack ne contient pas.

### Ce que le projet doit faire à la place

Écrire les vrais chiffres, partout où ils sont visibles :

| champ | sens |
|---|---|
| `nb_demande` | ce que l'opérateur a demandé |
| `nb_retenu` | ce que la VOD offre réellement |
| `manque` | `nb_demande - nb_retenu` |
| `remplissage_refuse` | `true` quand `manque > 0` |

Ces quatre champs sont dans le pack exporté (`mark1.py export`), dans `/tmp/m1.json`, dans la
question posée à l'opérateur (`ARCHIVUM/demande/pending/selection.json`) et dans le rapport de
siège. La question posée à l'opérateur annonce le manque explicitement, et sa réponse porte sur
**ce** nombre — pas sur un nombre gonflé pour le masquer.

### Pourquoi

Un nombre de clips est un objectif, pas une obligation. Un clip de remplissage coûte plus cher
qu'un clip manquant : il faut le relire, le signer, le rendre, le poster, et il dilue le compte.
La doctrine « rien n'est inventé » s'applique au nombre de clips exactement comme à un `payout`
manquant.

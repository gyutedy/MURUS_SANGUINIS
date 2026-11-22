# LES EXCEPTIONS — MARK1 V3

> **Ce document existe pour être lu par quelqu'un qui n'a pas confiance.**
> MARK1 a trois règles absolues. Deux fois, une exception a été ouverte, et
> chaque fois dans **un seul module nommé**. Si le code déroge ailleurs, le
> code est en faute, pas le document.

---

## Les trois règles absolues

| Règle | Sens |
|---|---|
| **R1** | Aucun seuil en dur. Tout nombre qui décide vit dans `config/selection.json`. |
| **R2** | Aucune suppression. MARK1 ajoute, ne retire jamais. |
| **R3** | Aucune vidéo. Jamais de MP4, jamais de ffmpeg sur du contenu, jamais de `.ass`. |

**Conservées intégralement.** Deux autres énoncés ont été abrogés, et
l'abrogation est bornée : voir « Les trois invariants abrogés ».

---

## EXC-1 — `overlay_title` par un LLM contraint

### Le besoin
Un titre d'overlay doit dire l'enjeu en 4 mots. Aucune règle mécanique ne le
produit correctement : c'est un acte de formulation, pas de calcul.

### Le bornage
| Interdit | Où c'est appliqué |
|---|---|
| Le LLM décide des règles | `overlay.constraints()` — les règles viennent de `config/selection.json` |
| Le LLM valide son propre texte | `overlay.accept()` appelle `title_forge.validate()` **et** `s1_context.analyse()` |
| Le LLM boucle indéfiniment | `llm.max_rounds = 3`, codé en config, épuisé dans `overlay.resolve()` |
| Le LLM est obligatoire | Mode ORACLE (aucune clé, aucun réseau) disponible à parité |
| Le LLM invente des faits | Contrainte déclarée + vérification S1 |
| **Une vidéo est produite** | Rien, nulle part : EXC-1 ne produit que du texte |

### Le rayon exact
| | |
|---|---|
| **Autorisé dans** | `M00C_METADATA/CODEBASE/overlay.py` **uniquement** |
| **Fonction d'appel réseau** | `_direct_candidates()` — une seule fonction |
| **Défaut en config** | `llm.enabled: false` → mode ORACLE, zéro réseau |
| **Comment vérifier** | `grep -rn "urllib\|requests\|http" M00C_METADATA/CODEBASE/overlay.py` → 1 résultat attendu (`_direct_candidates`) |

---

## EXC-2 — `M00F_VOX` transcrit un segment

### Le besoin
Le pack doit porter la transcription pour que l'overlay soit ancré sur le
contenu réel, pas sur un titre fourni en amont.

### Le bornage
| Interdit | Où c'est appliqué |
|---|---|
| Le service découpe la vidéo | `vox.py` n'appelle **jamais** ffmpeg ; `ffprobe` lit une durée, c'est tout |
| Un segment trop long part au service | `probe_duration()` + refus explicite au-delà de `vox.piece_sec` |
| Un service absent bloque le siège | `transcribe()` rend `("", raison)` — jamais d'exception |
| Une boucle de retry infinie | 3 essais, backoff `2**attempt`, puis raison explicite |
| **Le service est obligatoire** | Le pack peut porter `source_text` : M5 tolère alors une transcription vide |

### Le rayon exact
| | |
|---|---|
| **Autorisé dans** | `M00F_VOX/CODEBASE/vox.py` **uniquement** |
| **Fonctions externes** | `probe_duration()` (ffprobe) et `transcribe()` (HTTP) |
| **Comment vérifier** | `grep -rn "ffprobe\|ffmpeg" M00F_VOX/CODEBASE/vox.py` → `ffprobe` seulement, **zéro `ffmpeg`** dans tout MARK1 |

---

## Les trois invariants abrogés

Chacun passe d'absolu à **borné à un module nommé**.

| Invariant d'origine | Statut | Bornage |
|---|---|---|
| « Aucun appel réseau » | **abrogé** | Quatre fonctions au total : `overlay._direct_candidates`, `vox.probe_duration`, `vox.transcribe`, et les retries internes. Ailleurs : zéro. |
| « `llm_enabled: false` jamais lu » | **abrogé** | Lu par `overlay.pick_mode()` seul. `false` par défaut, ce qui force le mode ORACLE. |
| « ffprobe interdit » | **abrogé** | Autorisé dans `M00F_VOX/vox.py` pour lire une durée. Aucun autre module. |

---

## Les contrôles

À lancer avant tout siège. Un seul résultat inattendu = STOP.

```bash
# 1. Aucune vidéo n'est produite
#    (attention : ne PAS chercher ".ass" nu, cela matche assert() des tests.
#    On cherche les extensions entre guillemets et les binaires.)
grep -rnE 'ffmpeg|ffplay|\.mp4|\.mov|\.mkv|\.ass"' MONDES_FORGES/CLIPPING/MARK1 --include="*.py" \
  | grep -v "jamais\|interdit\|aucun\|pas de\|ne touche" || echo "  AUCUN (OK)"

# 2. Réseau : seulement EXC-1 et EXC-2
grep -rn "urllib\|requests\|urlopen\|socket" MONDES_FORGES/CLIPPING/MARK1 --include="*.py"

# 3. MARK1 ne parle jamais à F00
grep -rni "F00\|F01\|F02\|F03\|F04\|F05\|F06\|IRON_SENTINEL\|VOX\|COPYWRITER" \
  MONDES_FORGES/CLIPPING/MARK1 --include="*.py"
```

Résultat attendu du contrôle **3** : aucune référence à une frégate F0x en
import ou en appel. Le nom `M00F_VOX` est une sous-frégate de MARK1, pas
`F00B_VOX` — la logique est **copiée**, jamais appelée.

---

## Ce qui n'est pas une exception

| Tentation | Pourquoi c'est refusé |
|---|---|
| « Juste un petit ffmpeg pour normaliser l'audio » | R3. Le découpage est le travail de quelqu'un d'autre. |
| « Le LLM sait mieux que la règle, laissons-le juger » | EXC-1. Le moteur impose, le LLM remplit. |
| « Appeler F00B_VOX, c'est plus propre que copier » | MARK1 ne parle qu'à ARCHIVUM. Un appel à une frégate le ferme. |
| « Le seuil de 4 mots, on peut l'écrire dans le code » | R1. S'il n'est pas dans `config/`, il ne peut pas être audité. |

---

*Document vivant. Toute nouvelle exception doit apparaître ici avec son
rayon exact et sa commande de contrôle, ou elle n'existe pas.*

---

## Ce que MARK1 ne verifie PAS (et ne pretend pas verifier)

Depuis la directive du cycle 2026-07-24, quatre regles existent qui sont
**hors du perimetre de MARK1**, parce qu'il ne produit pas la video :

| Regle de la campagne | Qui la gere |
|---|---|
| Aucun autre logo visible | OMNIS_WATCH (montage) |
| Caption non editee sur IG Reels | l'operateur (saisie plateforme) |
| Post public, commentaires ouverts | l'operateur |
| Engagement organique normal | la plateforme / le ledger |

**Les mettre dans MARK1 serait du theatre.** Une porte qui pretend verifier
ce qu'elle ne peut pas voir est pire qu'une porte absente : elle donne une
fausse assurance.

En revanche, ces regles SONT verifiees par MARK1 parce qu'il produit le texte :
- **main focus** -> presence du sujet dans la transcription (`compliance.focus_report`)
- **pas de bait** -> overlay soutenu par le texte source (`compliance.bait_report`)
- **pas de negative PR** -> marqueurs d'attaque (`compliance.negative_pr_report`)
- **vocabulaire interdit** -> nettoyage + refus sur overlay (`compliance.scrub`, `check_asset`)

---

# EXCEPTIONS MURUS SANGUINIS

> Même loi que MARK1 : chaque exception est ouverte dans UN module nommé,
> avec son grep. Si le code déroge ailleurs, le code est en faute.

## EXC-M1 — le capteur `detect/live.py` invoque ffmpeg (SF_04_SELECTIO)

### Le besoin
La mécanique de détection pillée du skill (CDC §Installation étape 4) mesure le
loudness RMS du flux et la vitesse du chat. Mesurer l'audio exige de DECODER le
flux (ffmpeg `-af astats`). Un capteur qui lit n'est pas un cerveau qui rend.

### Le bornage
| Interdit | Où c'est appliqué |
|---|---|
| Le capteur REND un clip | Non : il produit des segments de mesure, jamais de livrable |
| Le rayon s'étend au-delà du capteur | grep ci-dessous : tout autre fichier de FR_A_CERVEAU est en faute |

### Le rayon exact
`FR_A_CERVEAU/SF_04_SELECTIO/CODEBASE/detect/` — ce dossier ET LUI SEUL.

### Les grep qui le vérifient
```
grep -rniE "(subprocess|os.system|popen).*ffmpeg|ffmpeg.*(run\(|call\()" FR_A_CERVEAU/ \
  --exclude-dir=detect     # doit renvoyer 0 ligne
grep -rniE "(subprocess|os.system|popen).*ffmpeg|ffmpeg.*(run\(|call\()" \
  FR_A_CERVEAU/SF_04_SELECTIO/CODEBASE/detect/   # doit renvoyer des lignes (le capteur)
```

## EXC-M2 — VEXILLUM décrit opacity/position/size_pct (SF_07_VEXILLUM)

### Le besoin
Le CDC (T05, T0_bis) affirme que `watermark.json` ne contient AUCUNE clé
opacity/position/size. Le code pillé réel (`vexillum.py:98-125`) lit ces valeurs
depuis `watermark_rules.json` (règles du CRÉATEUR : `opacity_min`, `position`,
`size_pct`) et les DÉCRIT dans le JSON — il ne les applique jamais à une vidéo.

### Le bornage
| Interdit | Où c'est appliqué |
|---|---|
| VEXILLUM apose le watermark sur une vidéo | Aucun subprocess/ffmpeg/drawtext dans SF_07 (testé par T0_bis) |
| VEXILLUM invente les valeurs | Elles viennent de `watermark_rules.json` / directive / config — jamais choisies par lui |

### Le rayon exact
`FR_A_CERVEAU/SF_07_VEXILLUM/` — la DESCRIPTION contient les clés ; l'APPLICATION
reste interdite. T05 reste strict : il ne passe que sur un artefact produit par un
run réel (CI), où la présence des clés est couverte par la présente exception.

### Les grep qui le vérifient
```
grep -rniE "subprocess|ffmpeg|libx264|drawtext" FR_A_CERVEAU/SF_07_VEXILLUM/ \
  --include="*.py"         # doit renvoyer 0 ligne
grep -rni "opacity" FR_A_CERVEAU/SF_07_VEXILLUM/CODEBASE/vexillum.py
                           # renvoie des lignes : la description (EXC-M2), pas l'application
```

### ⚠️ Verdict Warsmith requis
Le CDC T05 (« aucune clé opacity/position/size dans watermark.json ») est en
tension directe avec le code pillé. Deux options : (a) garder le code pillé et
la présente exception ; (b) purger les clés à la sortie de VEXILLUM (modifier le
code pillé). Décision réservée au Warsmith — en attendant, option (a) appliquée.

## EXC-M3 — test pillé daté en dur corrigé (MARK1 tests)

### Le besoin
`tests/test_mark1.py::test_clip_tokens_du_pack_correspondent_aux_assets` figeait
`when=datetime(2026, 11, 16)` alors que `packager.build()` calcule les tokens au
`datetime.now()`. Le test ne passait QUE le 2026-11-16 (date de création du
fixture) et échoue tous les autres jours. L'invariant testé (un clip_token =
`Axx-AAAAMMJJ-pack_token`, un par asset, tous distincts) reste identique.

### Le rayon exact
Un seul test, un seul jour dérivé de `pack["exported_at"]` au lieu d'une
constante. Aucun autre test, aucun module de production touché.

### Les grep qui le vérifient
```
grep -n "when=datetime(2026, 11, 16)" FR_A_CERVEAU/MARK1/tests/   # doit renvoyer 0 ligne
```

## EXC-M4 — chemin des transcripts corrigé en config (layout MURUS)

### Le besoin
`libs/transcript.py::find_transcript` prenait son défaut `../ARCHIVUM/montage/transcripts`
relatif à la racine MARK1. Dans le layout d'origine (PERTURABO) MARK1 vivait à côté
d'ARCHIVUM ; dans MURUS_SANGUINIS, MARK1 est dans `FR_A_CERVEAU/MARK1` et ARCHIVUM à la
racine du dépôt. Le défaut pointait donc `FR_A_CERVEAU/ARCHIVUM` (inexistant) et
`find_transcript` rendait `None` — sans erreur, ce qui aurait fait échouer M1 en silence
sur toute VOD dont le transcript est dans ARCHIVUM.

### Le rayon exact
Une clé ajoutée dans `FR_A_CERVEAU/MARK1/config/selection.json` :
`archivum.transcripts_dir = ../../ARCHIVUM/montage/transcripts`. Aucun module pillé modifié :
le code lit déjà `cfg["archivum"]["transcripts_dir"]`.

### Les grep qui le vérifient
```
grep -n '"archivum"' FR_A_CERVEAU/MARK1/config/selection.json      # 1 ligne, valeur ../../ARCHIVUM
grep -rn 'transcripts_dir' FR_A_CERVEAU/MARK1/libs/transcript.py   # le code lit bien la clé
```

## EXC-M5 — schémas de codex visibles à l'endroit où le code pillé les cherche

### Le besoin
`FR_B_CREATION/tools/codex.py` (pillé de LACRIMAE) calcule
`ROOT = Path(__file__).parent.parent` puis lit `ROOT/REVIEW/SCHEMAS/*.schema.json`.
Dans le layout MURUS, `tools/` a dû être placé sous `FR_B_CREATION/` (F05/F06
l'importent via `parents[2]`), donc le validateur cherchait
`FR_B_CREATION/REVIEW/SCHEMAS` et refusait tout codex : « schema absent ».
Résultat : aucun codex ne pouvait être validé, donc aucun rendu — sans que rien
ne le dise.

### Le rayon exact
Copie à l'identique de `REVIEW/SCHEMAS/*.schema.json` vers
`FR_B_CREATION/REVIEW/SCHEMAS/`. **Aucun code pillé modifié.** Les schémas restent
la vérité unique à la racine ; la copie est gardée par un contrôle d'identité en CI.

### Les grep qui le vérifient
```
python - <<'PY'
import hashlib, pathlib
for n in ("codex_render", "codex_postprod"):
    a = pathlib.Path("REVIEW/SCHEMAS/%s.schema.json" % n).read_bytes()
    b = pathlib.Path("FR_B_CREATION/REVIEW/SCHEMAS/%s.schema.json" % n).read_bytes()
    assert hashlib.sha256(a).hexdigest() == hashlib.sha256(b).hexdigest(), n
print("schemas identiques")
PY
```

---

## EXC-M7 — Campagne calée sur valeurs d'exemple (non réelles)

### La doctrine qui aurait dû s'appliquer
Aucune valeur de campagne n'est inventée : `payout`, `rate`, `funded`,
`budget_remaining_usd`, `cap_usd_per_clip`, `warmup_days`, `focus_declared` sont des
déclarations d'opérateur. Un `null` fait refuser la porte D0/A1/A2 (c'est le
comportement correct, vérifié en siège réel le 2026-11-22 : `[FAIL] D0_DIRECTIVE :
champs manquants: payout`).

### Le besoin
L'opérateur a demandé explicitement d'**avancer avec des valeurs d'exemple** pour
caler la chaîne de bout en bout et valider le projet, sans attendre les chiffres
réels de la campagne PREME.

### La dérogation exacte
`ARCHIVUM/campaign/operator_declarations.json` et
`ARCHIVUM/campaign/campaign_directive.json` contiennent des valeurs d'exemple :
`rate_usd_per_1k = 0.30`, `funded = true`, `budget_remaining_usd = 2500`,
`cap_usd_per_clip = 5`, `warmup_days = 42`, `focus_declared = true`,
`payouts.youtube_shorts.usd_per_1k = 0.30`.

Chacune porte `_provenance.mode = "exemple_de_calage"` et la mention explicite
« CE NE SONT PAS les chiffres réels ». **Aucune soumission réelle ne peut partir
avec ces valeurs** : le codex exige toujours la signature de l'opérateur, et le
tracker V7 écrit la ligne de soumission réelle.

### Le rayon exact
Deux fichiers de données, aucun code. Le moteur ne sait pas distinguer un exemple
d'une valeur réelle — c'est pourquoi la provenance est écrite dans le fichier et
répétée dans les rapports (`TRACKING/SIEGE_PREME.md`, section « déclarations »).

### Les grep qui le vérifient
```
python - <<'PY'
import json
d = json.load(open("ARCHIVUM/campaign/operator_declarations.json"))
p = d["_provenance"]
assert p["mode"] == "exemple_de_calage", p
assert "CE NE SONT PAS" in p["note"]
c = json.load(open("ARCHIVUM/campaign/campaign_directive.json"))
assert c["payouts"]["youtube_shorts"]["_provenance"]["mode"] == "exemple_de_calage"
print("valeurs d'exemple marquees comme telles")
PY
```

---

## EXC-M8 — Documents opérateur en EN + FR (règle permanente)

### La doctrine qui aurait dû s'appliquer
Rien n'imposait la langue. Les documents partaient en français seul, alors que le
moteur travaille en anglais (`default_language: en`) et que la transcription est
anglaise : l'opérateur devait valider des clips dont il ne pouvait pas lire le
texte source, ou lire une traduction dont le moteur ne se sert jamais.

### Le besoin
Consigne explicite de l'opérateur : « tu dois toujours me sortir deux versions, une
anglaise et une française, pour compréhension », et la règle doit vivre **dans le
projet**, pas dans une conversation.

### La dérogation exacte
Ce n'est pas une dérogation mais une **règle ajoutée** :
`TRACKING/DOCTRINE_BILINGUE.md` (elle-même bilingue) impose que tout document
opérateur — `TRACKING/SELECTION_*.md`, `TRACKING/SIEGE_*.md` — contienne une
section `## EN` **et** une section `## FR`. Le EN est la transcription verbatim,
source de vérité ; le FR est une traduction de compréhension, jamais lue par une
porte.

### Le rayon exact
Documents et générateur de rapport de siège. Aucune logique de décision modifiée.

### Les grep qui le vérifient
```
python tests/test_murus.py | grep test_t17_docs_operateur_bilingues
grep -c "^## EN" TRACKING/SELECTION_15_PREME.md TRACKING/SIEGE_PREME.md
grep -c "^## FR" TRACKING/SELECTION_15_PREME.md TRACKING/SIEGE_PREME.md
```

---

## EXC-M10 — les deux previews partagent un seul site Pages (sous-dossier `/preview2/`)

### Ce que la doctrine exige
Deux previews, deux rôles : la preview 1 (`SF_10_SPECULUM`) règle le LOOK et
écrit `codex_render.json` ; la preview 2 (`SF_11_LUMEN`) règle le postprod
(glow → caption → lut → fade) et écrit `codex_postprod.json`. Voir
`TRACKING/PREVIEWS_ROLES.md`.

### Ce que la plateforme permet
GitHub Pages sert **un seul site par dépôt**. Deux previews automatiques sur le
même dépôt ne peuvent donc pas avoir chacune leur URL racine.

### La dérogation exacte
La preview 1 est publiée à la racine du site
(`https://gyutedy.github.io/MURUS_SANGUINIS/`), la preview 2 dans
`https://gyutedy.github.io/MURUS_SANGUINIS/preview2/`. Les deux étapes de
publication utilisent `keep_files: true` ; `force_orphan: true` est interdit car
il efface l'autre preview. Si l'opérateur préfère une séparation nette, la
preview 2 déménage dans un second dépôt : la dérogation disparaît.

### Le rayon exact
Hébergement uniquement. Les rôles, les panneaux et les codex restent séparés :
la preview 1 n'affiche plus glow / LUT / fade / sous-titres.

### Les grep qui le vérifient
```
grep -n "destination_dir: preview2" .github/workflows/murus_preview_2.yml
grep -n "keep_files: true" .github/workflows/murus_preview_1.yml .github/workflows/murus_preview_2.yml
grep -c "force_orphan" .github/workflows/murus_preview_1.yml .github/workflows/murus_preview_2.yml
python tests/test_murus.py | grep test_t19
```

### EXC-M11 — Chemins des CLIs pillées repointés vers la structure MURUS

Les CLI pillées de LACRIMAE importent des chemins `F03_PREVIEW/...` qui n'existent pas
dans notre arbre (`SF_10_SPECULUM`). Deux chemins ont été repointés :

- `FR_B_CREATION/tools/convert_pur_pack.mjs` → `../SF_10_SPECULUM/CODEBASE/src/preview/bridgeClipper.js`
- `FR_B_CREATION/SF_12_FABRICA/look/CODEBASE/render_pictor.mjs` → `../../../SF_10_SPECULUM/CODEBASE/src/preview/_purPackComposition.jsx`

Grep de vérification :

```
grep -rn "F03_PREVIEW/CODEBASE/src/preview" FR_B_CREATION/tools FR_B_CREATION/SF_12_FABRICA/look/CODEBASE
```

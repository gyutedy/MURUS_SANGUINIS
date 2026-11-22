# ERRATA — LES ERREURS DÉJÀ PAYÉES

> Chaque ligne a coûté une session. On ne les repaie pas. Si tu repars de zéro,
> lis ce fichier avant d'écrire une ligne de YAML ou de JS.

## EN

### E-1 — Clip file naming: `clips/pur_<id>.mp4`
`SF_10` resolves clips through `clipFileCandidates(angleId)` =
`[clips/pur_<id>.mp4, clips/<id>_look.mp4, clips/<id>.mp4]`. Publishing
`clips/clip_<id>.mp4` gives a **black player with no error**: the page requests a
file that does not exist. The producer must emit the **first** candidate.

### E-2 — Job outputs are written to `$GITHUB_OUTPUT`
A Python `print("found=1")` writes nothing. A matrix job guarded by
`fromJSON(needs.plan.outputs.found)` then **silently skips**. Always open
`os.environ["GITHUB_OUTPUT"]` and append `key=value`.

### E-3 — Never put `: ` inside a YAML step name
`- name: Vérifier le compte (anti-remplissage : on annonce)` breaks the parse:
`mapping values are not allowed here`. Validate every workflow with
`python -c "import yaml; yaml.safe_load(open(f))"` before pushing.

### E-4 — The player component identity must be stable
`useMemo(() => (props) => <Comp .../>, [manifest])` remounts the Remotion
`<Player>` on every slider move. The `<Video>` reloads a 20-33 MB file and the
stage goes **black** until buffering ends. Fix: identity never changes, data goes
through `inputProps`.

### E-5 — Codex schemas are strict; provenance lives in a sidecar
`REVIEW/SCHEMAS/*.schema.json` use `additionalProperties: false`. A `_provenance`
key inside a codex makes it invalid. Write `*.provenance.json` next to it, and
validate the draft with `jsonschema` in CI.

### E-6 — GitHub Pages serves one site per repository
Two previews cannot each have their own Pages site on the same repo. Preview 2
goes to a subfolder `/preview2/` (EXC-M10), and both publishing steps must use
`keep_files: true` — `force_orphan: true` erases the other preview.

### E-7 — A workflow that needs a pack needs that pack committed
`EXPORT/production_pack_*.json` is gitignored (generated artefact). The review
needs it: the siege stages `REVIEW/pack_stage.json`, committed, and the preview
workflows read **that** file — never a re-derivation.

### E-8 — One job per clip
Downloading nine windows in one job means one failure kills nine clips and one
timeout kills the siege. `strategy.matrix` + `fail-fast: false`: one job per clip,
each uploading its own artefact, then an `assemble` job.

### E-9 — The watermark is the campaign PNG from the pack, never an invented name
`src: 'wm.png'` showed a broken image and the stage drew a green circle labelled
`WM`. The logo must come from `pack.watermark.file` (`watermarks/preme.png`), be
displayed as a real `<img>` on the stage, and the panel must show the PNG — not
the file name. Same rule for titles: they come from the pack
(`assets[].overlay_title`) and are seeded at load, otherwise the panel looks empty.

### E-10 — Never gitignore a signed codex
`REVIEW/codex_render.json` and `REVIEW/codex_postprod.json` were listed in
`.gitignore`. The gates read them **from the repository**: a signed codex therefore
never reached GitHub, and G1 kept answering "codex absent". Only drafts
(`*.draft.json`) may be ignored.

### E-11 — The preview lied about the LUT
The browser preview hard-coded its LUT as `contrast(1.10) saturate(1.10)` copied from the
`textura` block, while the render (`lut/lut_apply.py`) applies the **`chroma`** block via
`eq=` (contrast, saturation, brightness, gamma) plus `hqdn3d` and `unsharp`. The preview
therefore showed a tenth of the effect, in the wrong block: invisible on screen. It now
reads `atom_ic_profiles.json` at runtime, exposes an intensity slider (preview only — not
in the codex, whose schema is strict) and declares that denoise/unsharp cannot be shown.

### E-12 — A gate must not demand its own outputs
The render preflight listed `EXPORT/*.json`, `SF_12_FABRICA/OUT/clips`,
`SF_13_POLITURA/OUT/postprod_report.json` and `SF_16_MISSIO/OUT/submissions.json`
as prerequisites. Three of them are produced **by the chain itself**, and `EXPORT/`
is gitignored: the gate could never open (`chaîne incomplète : 4 étape(s)`). It now
blocks only on real inputs (the two signed codex, the staged pack, the campaign PNG)
and reports expected outputs without requiring them. The single `chaine` job was also
replaced by **one job per clip** (matrix, `fail-fast: false`).

## FR

## FR

### E-9 — Le watermark est le PNG de campagne du pack, jamais un nom inventé
`src: 'wm.png'` affichait une image cassée et la scène dessinait un cercle vert
« WM ». Le logo doit venir de `pack.watermark.file` (`watermarks/preme.png`),
s'afficher comme un vrai `<img>` sur la scène, et le panneau doit montrer le PNG —
pas le nom du fichier. Même règle pour les titres : ils viennent du pack
(`assets[].overlay_title`) et sont chargés d'emblée, sinon le panneau paraît vide.

### E-1 — Nommage des fichiers de clip : `clips/pur_<id>.mp4`
`SF_10` résout les clips par `clipFileCandidates(angleId)` =
`[clips/pur_<id>.mp4, clips/<id>_look.mp4, clips/<id>.mp4]`. Publier
`clips/clip_<id>.mp4` donne un **lecteur noir sans aucune erreur** : la page
demande un fichier qui n'existe pas. Le producteur doit écrire le **premier**
candidat.

### E-2 — Les sorties de job s'écrivent dans `$GITHUB_OUTPUT`
Un `print("found=1")` en Python n'écrit rien. Un job matriciel gardé par
`fromJSON(needs.plan.outputs.found)` est alors **sauté silencieusement**.
Toujours ouvrir `os.environ["GITHUB_OUTPUT"]` et y ajouter `cle=valeur`.

### E-3 — Jamais `: ` dans un nom d'étape YAML
`- name: Vérifier le compte (anti-remplissage : on annonce)` casse l'analyse :
`mapping values are not allowed here`. Valider chaque workflow avec
`python -c "import yaml; yaml.safe_load(open(f))"` avant de pousser.

### E-4 — L'identité du composant lecteur doit être stable
`useMemo(() => (props) => <Comp .../>, [manifest])` remonte le `<Player>` Remotion
à chaque mouvement de curseur. Le `<Video>` recharge un fichier de 20-33 Mo et la
scène devient **noire** jusqu'à la fin du buffer. Correctif : l'identité ne change
jamais, les données passent par `inputProps`.

### E-5 — Les schémas de codex sont stricts ; la provenance vit en sidecar
Les `REVIEW/SCHEMAS/*.schema.json` utilisent `additionalProperties: false`. Une clé
`_provenance` dans un codex le rend invalide. Écrire `*.provenance.json` à côté, et
valider le brouillon avec `jsonschema` en CI.

### E-6 — GitHub Pages ne sert qu'un site par dépôt
Deux previews ne peuvent pas avoir chacune leur site Pages sur le même dépôt. La
preview 2 va dans le sous-dossier `/preview2/` (EXC-M10), et les deux étapes de
publication doivent utiliser `keep_files: true` — `force_orphan: true` efface
l'autre preview.

### E-7 — Un workflow qui a besoin d'un pack doit avoir ce pack commité
`EXPORT/production_pack_*.json` est gitignored (artefact généré). La review en a
besoin : le siège stage `REVIEW/pack_stage.json`, commité, et les workflows de
preview lisent **ce** fichier — jamais une re-dérivation.

### E-8 — Un job par clip
Télécharger neuf fenêtres dans un seul job signifie qu'un échec tue neuf clips et
qu'un timeout tue le siège. `strategy.matrix` + `fail-fast: false` : un job par
clip, chacun publiant son artefact, puis un job `assemble`.

### E-10 — Ne jamais ignorer un codex signé
`REVIEW/codex_render.json` et `REVIEW/codex_postprod.json` figuraient dans
`.gitignore`. Les portes les lisent **dans le dépôt** : un codex signé n'arrivait donc
jamais sur GitHub et G1 répondait « codex absent ». Seuls les brouillons
(`*.draft.json`) peuvent être ignorés.

### E-11 — L'aperçu mentait sur la LUT
L'aperçu navigateur codait sa LUT en dur (`contrast(1.10) saturate(1.10)`) recopiée du bloc
`textura`, alors que le rendu (`lut/lut_apply.py`) applique le bloc **`chroma`** via `eq=`
(contraste, saturation, luminosité, gamma) plus `hqdn3d` et `unsharp`. L'aperçu montrait donc
un dixième de l'effet, dans le mauvais bloc : invisible à l'écran. Il lit maintenant
`atom_ic_profiles.json` au runtime, offre un curseur d'intensité (aperçu seulement — pas
dans le codex, dont le schéma est strict) et déclare que denoise/unsharp ne sont pas montrables.

### E-12 — Une porte ne doit jamais exiger ses propres sorties
Le pré-vol du rendu listait `EXPORT/*.json`, `SF_12_FABRICA/OUT/clips`,
`SF_13_POLITURA/OUT/postprod_report.json` et `SF_16_MISSIO/OUT/submissions.json` comme
prérequis. Trois d'entre eux sont produits **par la chaîne elle-même**, et `EXPORT/` est
gitignoré : la porte ne pouvait donc jamais s'ouvrir (`chaîne incomplète : 4 étape(s)`).
Elle ne bloque plus que sur de vraies entrées (les deux codex signés, le pack stagé, le
PNG de campagne) et annonce les sorties attendues sans les exiger. Le job unique `chaine`
a aussi été remplacé par **un job par clip** (matrice, `fail-fast: false`).

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

### E-13 — The pillaged CLI paths pointed to a tree that does not exist here
`convert_pur_pack.mjs`, `render_pictor.mjs` and `PurLook.jsx` imported from
`F03_PREVIEW/...`, the layout of the source repo. In MURUS that directory does not
exist, so the render died on `Module not found` while the pack builder looked fine.
Repointed to `SF_10_SPECULUM` (EXC-M11); test `t27` now asserts no look `.jsx`
references a dead path.

### E-14 — A report commit could cancel a delivery
The assemble job committed `render_report.json` then ran a bare `git push`. Any
concurrent push made git reject it (`fetch first`), the step failed, and the **zip
of the nine deliverables was never uploaded** because it came after. A report must
never block a delivery: `git pull --rebase` with five retries, `continue-on-error:
true`, and a warning instead of a failure.

### E-15 — The qa_pass proofs could never be committed
`FR_B_CREATION/*/OUT/*` is gitignored, so the camouflage and luther reports were
written inside the runner and silently dropped by a `git add ... || true`. The
delivery trace never reached GitHub. The proofs are now copied into `REVIEW/render/`
and added explicitly with `git add -f`, failing loudly if absent.

### E-16 — Six bare `git push` in the workflows
Each of them could interrupt a useful job on a rejected ref. All six now rebase and
retry, and no bare `git push` remains in any workflow.

### E-17 — The codex names the font, the file has another name
`REVIEW/codex_postprod.json` carries `caption.font = "Montserrat ExtraBold"` (the
readable name), while the file is `Montserrat-ExtraBold.ttf`. `font_file()` did
`FONT_DIR / name`, found nothing, raised `CaptionError`, and `postprod.py` recorded
`caption: applied=false` — **the clips shipped without subtitles and still reported
`qa_pass: true`**, because the technical QA only checked codec and metadata. The
name is now resolved to the real file (never a system fallback), and a dedicated
gate (`5b PORTE SOUS-TITRES`) refuses any clip without burned captions.

### E-18 — No transcript was passed to postprod
`postprod.py` fell back to faster-whisper, which is not installed in the render job:
`SANS SOUS-TITRES ... faster-whisper absent`. The real transcript already lived in
the repo (`ARCHIVUM/montage/transcripts/v<vod>_transcript.json`) but holds absolute
VOD times, unusable for a 30 s clip. `caption/transcript_slice.py` is now the
versioned tool that slices it, shifts times to zero, and refuses an empty window —
the workflow calls this CLI instead of inline python nobody can review.

### E-19 — A subtitle "word" was a whole sentence
The siege transcription called `model.transcribe(...)` without
`word_timestamps=True`, so only ~3.4 s sentence segments existed. `transcript_slice`
passed them through as if each were a word, and the renderer grouped them with
`max_words=2` **whatever the motion** — producing a mix of full paragraphs and single
words. Now the codex motion decides the cue (`pop-in` = one word), segments are split
into words with declared `interpolated` timing, and the transcription requests real
word times (`measured`) which always take precedence.


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

### E-13 — Les chemins des CLI pillés pointaient un arbre inexistant ici
`convert_pur_pack.mjs`, `render_pictor.mjs` et `PurLook.jsx` importaient depuis
`F03_PREVIEW/...`, l'arborescence du dépôt source. Dans MURUS ce dossier n'existe
pas : le rendu mourait sur `Module not found` alors que le constructeur de packs
semblait correct. Repointés vers `SF_10_SPECULUM` (EXC-M11) ; le test `t27` interdit
désormais tout `.jsx` de look référençant un chemin mort.

### E-14 — Un commit de rapport pouvait annuler une livraison
Le job `assemble` commitait `render_report.json` puis lançait un `git push` nu. Un
push concurrent le faisait rejeter (`fetch first`), l'étape échouait, et le **zip des
neuf livrables n'était jamais produit** car il venait après. Un rapport ne doit jamais
bloquer une livraison : `git pull --rebase` avec cinq reprises, `continue-on-error:
true`, et un avertissement au lieu d'un échec.

### E-15 — Les preuves `qa_pass` ne pouvaient jamais être commitées
`FR_B_CREATION/*/OUT/*` est gitignoré : les rapports camouflage et luther étaient
écrits dans le runner puis perdus en silence par un `git add ... || true`. La trace de
livraison n'atteignait jamais GitHub. Les preuves sont maintenant copiées dans
`REVIEW/render/` et ajoutées explicitement (`git add -f`), avec échec bruyant si absentes.

### E-16 — Six `git push` nus dans les workflows
Chacun pouvait interrompre un job utile sur un rejet de référence. Les six font
désormais rebase puis reprise, et plus aucun `git push` nu ne subsiste.

### E-17 — Le codex nomme la police, le fichier porte un autre nom
`REVIEW/codex_postprod.json` porte `caption.font = "Montserrat ExtraBold"` (le nom
lisible), alors que le fichier est `Montserrat-ExtraBold.ttf`. `font_file()` faisait
`FONT_DIR / name`, ne trouvait rien, levait `CaptionError`, et `postprod.py` notait
`caption: applied=false` — **les clips sortaient sans sous-titres en annonçant
`qa_pass: true`**, parce que la QA technique ne regardait que le codec et les
métadonnées. Le nom est maintenant résolu vers le fichier réel (jamais un repli
système), et une porte dédiée (`5b PORTE SOUS-TITRES`) refuse tout clip sans sous-titres.

### E-18 — Aucune transcription n'était passée à postprod
`postprod.py` retombait sur faster-whisper, absent du job de rendu :
`SANS SOUS-TITRES ... faster-whisper absent`. La transcription réelle existait déjà
dans le dépôt (`ARCHIVUM/montage/transcripts/v<vod>_transcript.json`) mais en temps
absolus de la VOD, inutilisable pour un clip de 30 s. `caption/transcript_slice.py`
est désormais l'outil versionné qui la découpe, ramène les temps à zéro et refuse une
fenêtre vide — le workflow appelle ce CLI, plus de python inline que personne ne relit.

### E-19 — Un « mot » de sous-titre était une phrase entière
La transcription du siège appelait `model.transcribe(...)` sans `word_timestamps=True` :
seuls des segments de phrase d'environ 3,4 s existaient. `transcript_slice` les
transmettait comme des mots, et le graveur les regroupait avec `max_words=2` **quelle
que soit la motion** — d'où un mélange de pavés et de mots isolés. Maintenant la motion
du codex décide du cue (`pop-in` = un mot), les segments sont découpés en mots avec un
minutage déclaré `interpolated`, et la transcription demande les vrais temps par mot
(`measured`), qui ont toujours priorité.

### E-21 — Une matrice vide rendait zéro clip, en silence
Le workflow de la voie vive déclarait `assets` et `vod` en `inputs`. Sur un
déclencheur `push`, `inputs` est **vide** : la matrice devenait `{"clip": []}`,
aucun job n'était créé, et le job `assemble` échouait seul — un run « vert »
à zéro clip aurait été possible si `assemble` avait été tolérant. Les deux
valeurs ont maintenant un défaut explicite, et une matrice vide est un **refus**
(`::error::aucune fenetre demandee`). Leçon : un générateur de matrice vide doit
refuser, jamais produire une liste vide.

### E-22 — Le titre de publication était jugé comme un titre à l'image
`title_forge.validate` exige un marqueur d'enjeu (`no_stake`). C'est juste pour le
titre **gravé** ; c'est faux pour la ligne de description, qui est factuelle. Le
filtre refusait donc des titres de publication légitimes et poussait tout en repli
gabarit. L'enjeu est désormais exigé sur le titre de clip, et retiré du jugement du
`metadata_title` (`accepter(..., enjeu=False)`). Le validateur reste le seul juge :
on ne l'affaiblit pas, on applique la bonne règle au bon champ.

## E-23 — La synchro se mesure et se declare, elle n'etrangle pas (2026-11-24)

**FR** — Ordre de l'operateur : « je veux que le run soit vert meme avec des retards,
c'est pas un goulot d'etranglement ». Consequence : `PORTE SYNCHRO` mesure et publie
`decalage_retenu_s`, `derive_par_mot_s`, `mots_ancres`, `confiance`, `source_mesure`,
puis **avertit sans refuser** (`::warning::SYNCHRO DECALEE …`). Ce qui refuse encore,
c'est l'ABSENCE de sous-titres (`PORTE SOUS-TITRES`), pas un ecart de temps.
Verrou : `tests/test_murus_v2.py::test_t35_synchro_declaree_pas_bloquante`.

**EN** — Operator order: "I want the run green even with delays, it is not a
bottleneck". So `PORTE SYNCHRO` measures and publishes the numbers, then **warns
without refusing**. A missing subtitle still refuses; a measured delay never does.

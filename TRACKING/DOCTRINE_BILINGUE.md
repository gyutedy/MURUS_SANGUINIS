# DOCTRINE BILINGUE — EN / FR

<!-- BILINGUE:EN -->
## EN — The rule

Every document produced **for the operator** (Warsmith) exists in **two versions: English and
French**. No exceptions, no "translated later".

### What counts as an operator document

- selection deliverables (`TRACKING/SELECTION_*.md`)
- siege and run reports (`TRACKING/SIEGE_*.md`)
- any codex or validation sheet the operator has to sign
- any answer the project expects from the operator

### Which version is authoritative

**The EN text is the machine transcription, verbatim. It is the source of truth.**
The FR text is a comprehension translation. It is never used to decide anything: a gate
reads the transcript, never the translation. If the two disagree, the EN wins and the FR
is a defect to fix.

### Why

- The engine works in EN (`default_language: en`). Translating would move the decision
  away from the measured text.
- The operator must understand before signing. Understanding in the operator's language
  is a safety property, not comfort.
- A single-language document hides meaning from one of the two parties in the chain.

### How it is enforced

`tests/test_murus.py::test_t17_docs_operateur_bilingues` refuses any
`TRACKING/SELECTION_*.md` or `TRACKING/SIEGE_*.md` that does not contain **both** an
`## EN` section and a `## FR` section. A document that loses a language turns the CI red.

<!-- BILINGUE:FR -->
## FR — La règle

Tout document produit **pour l'opérateur** (Warsmith) existe en **deux versions : anglais et
français**. Sans exception, pas de « je traduirai après ».

### Ce qui compte comme document opérateur

- les livrables de sélection (`TRACKING/SELECTION_*.md`)
- les rapports de siège et de run (`TRACKING/SIEGE_*.md`)
- tout codex ou fiche de validation que l'opérateur doit signer
- toute réponse que le projet attend de l'opérateur

### Quelle version fait foi

**Le texte EN est la transcription machine, verbatim. C'est la source de vérité.**
Le texte FR est une traduction de compréhension. Il ne sert jamais à décider : une porte lit
le transcript, jamais la traduction. Si les deux divergent, l'EN gagne et le FR est un défaut
à corriger.

### Pourquoi

- Le moteur travaille en EN (`default_language: en`). Traduire éloignerait la décision du
  texte mesuré.
- L'opérateur doit comprendre avant de signer. Comprendre dans sa langue est une propriété
  de sûreté, pas un confort.
- Un document mono-langue cache le sens à l'une des deux parties de la chaîne.

### Comment c'est fait respecter

`tests/test_murus.py::test_t17_docs_operateur_bilingues` refuse tout
`TRACKING/SELECTION_*.md` ou `TRACKING/SIEGE_*.md` qui ne contient pas **à la fois** une
section `## EN` et une section `## FR`. Un document qui perd une langue fait passer la CI
au rouge.

# DEMANDE À L'OPÉRATEUR

Le projet **demande**, il ne décide pas. Et **l'opérateur n'édite jamais un fichier
du repo en plein siège** : il répond au lancement du workflow, ou à l'oral. C'est le
projet qui écrit la trace, datée et attribuée.

```
ARCHIVUM/demande/
  pending/<cle>.json    <- la question, écrite par le projet (lisible, avec le pourquoi)
  answers.json          <- la réponse, ÉCRITE PAR LE PROJET (provenance : dispatch / oral)
```

## Comment l'opérateur répond

Au lancement de `MURUS — SIÈGE RÉEL` :

| input du workflow | question | valeurs |
|---|---|---|
| `nb_clips` | Combien de clips pour ce siège ? | entier 1..15 (plafond CDC) |
| `selection_approved` | Valides-tu la sélection M1 soumise ? | `oui` / `non` |

Le projet valide la valeur (refus au-delà de 15, refus si non entier), puis l'écrit
dans `answers.json` avec `declared_by` et `source`. Une réponse absente = arrêt net :
aucune valeur par défaut n'est inventée.

## Cycle en deux lancements

1. **lancement 1** — `nb_clips = 15`. M1 produit les 15 fenêtres **avec leur force**
   et les soumet (`pending/selection.json`). Le run s'arrête là, rien n'est exporté.
2. **lancement 2** — `selection_approved = oui`. M1 rejoue la même sélection
   (déterministe), la validation passe, `mark1 export` enchaîne D0 → X1.

## Ce que veut dire la « force »

`candidate_windows` note chaque fenêtre : `score = marqueurs d'enjeu + 2 × chiffres`.
Tri décroissant, puis espacement minimal pour ne pas prendre deux fois le même moment.
La force est affichée clip par clip : la sélection est discutable, pas subie.

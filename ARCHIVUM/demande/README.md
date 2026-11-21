# DEMANDE À L'OPÉRATEUR

Le projet **demande**, il ne décide pas. Ici vivent les questions que seul
l'opérateur (Warsmith) peut répondre, et les réponses qu'il écrit.

```
ARCHIVUM/demande/
  pending/<cle>.json    <- la question, écrite par le projet (lisible, avec le pourquoi)
  answers.json          <- la réponse, écrite PAR L'OPÉRATEUR
```

Une réponse absente = arrêt net. Le code ne fabrique aucune valeur par défaut.

## Questions connues

| clé | question | plafond |
|---|---|---|
| `nb_clips` | Combien de clips pour ce siège ? | 15 (CDC) |
| `selection_approved` | Valides-tu la sélection M1 soumise (clips + force) ? | `true` |

## Forme du fichier de réponses

```json
{
  "answers": {
    "nb_clips": 15,
    "selection_approved": true
  }
}
```

`selection_approved: false` est accepté et **bloque** : le projet redemandera une
sélection après correction, il ne forcera pas.

## Pourquoi

- `nb_clips` : le nombre de clips conditionne M1. Ce n'est pas un défaut de workflow.
- `selection_approved` : M1 *propose* des fenêtres avec une **force** (score : marqueurs
  d'enjeu + 2 × chiffres). L'opérateur voit les moments réels et leur force, et décide.

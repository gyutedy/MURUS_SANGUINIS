# MURUS SANGUINIS — le mur de siège qui réfléchit et qui frappe

Fusion **PERTURABO** (le cerveau) × **LACRIMAE** (le bras armé) × **gta6-clipper-windows** (le détecteur).
Cahier des charges : `MURUS_SANGUINIS_CDC_V1.html` (auto-suffisant, fait foi).

## Doctrine (intangible)

- **FR_A_CERVEAU ne touche JAMAIS une vidéo** — elle produit des packs JSON dans `EXPORT/`
  (héritage CLIPPING/MARK1).
- **FR_B_CREATION ne prend JAMAIS une décision** — elle exécute les codex signés
  (`REVIEW/codex_render.json` + `REVIEW/codex_postprod.json`, `validated_by_magos`)
  (héritage LACRIMAE).
- **Une gate PRÉCÈDE chaque sous-frégate** — 14 gates humaines. Les DEUX exceptions,
  `SF_14_CAMOUFLAGE` et `SF_15_LUTHER`, s'exécutent AUTOMATIQUEMENT après le rendu,
  ne rendent rien elles-mêmes, et prouvent leur passage par un rapport (`qa_pass`).
- **Le run s'arrête à la première porte en échec** — aucune erreur amont ne peut
  déclencher un run A→Z.
- **Le moteur décide, l'opérateur valide, le ledger juge.**
- **Aucun remplissage** : si 15 clips sont demandés et que la VOD n'en offre que 6 qui
  remplissent les conditions, le projet rend **6** et l'écrit (`nb_demande` / `nb_retenu` /
  `manque` / `remplissage_refuse` dans le pack). Jamais de doublon, jamais de moment faible
  ajouté pour atteindre le chiffre. Toute porte qui refuse est une porte qui fonctionne.
  → `TRACKING/DOCTRINE_ANTI_REMPLISSAGE.md`
- **Deux versions, EN et FR** : tout document destiné à l'opérateur existe en anglais et en
  français. Le EN est la transcription verbatim (source de vérité), le FR une traduction de
  compréhension que le moteur ne lit jamais. → `TRACKING/DOCTRINE_BILINGUE.md`
- **L'opérateur n'édite jamais un fichier en plein siège** : le projet pose la question
  (`ARCHIVUM/demande/pending/`), l'opérateur répond au lancement (`nb_clips`,
  `selection_approved`), le projet écrit la trace avec sa provenance.
  → `ARCHIVUM/demande/README.md`
- **L'ordre est gravé** : export (D0→X1) → récupération du clip (`FR_B_CREATION/tools/
  recuperer_clip.py` : clip → preview 1, frame → preview 2) → les DEUX codex signés →
  rendu (SF_12) → PP2 → CAMOUFLAGE → LUTHER → V7. Aucun rendu avant les codex.

## Architecture

```
FR_A_CERVEAU (SF_01→SF_09)          FR_B_CREATION (SF_10→SF_16)
  M0 SF_01_VIGILIA                    V5  SF_10_SPECULUM  (preview LOOK)
  V1 SF_02_VERDICTUM                  V6  SF_11_LUMEN     (preview GLOW, 1 frame)
  V2 SF_03_ANGULI                     G1  SF_12_FABRICA   (rendu, piloté par les 2 codex)
  M1 SF_04_SELECTIO (TOP 15, cap 15)  PP2 SF_13_POLITURA  (glow→caption→lut→fade)
  M5 SF_05_VOX                        —   SF_14_CAMOUFLAGE (SANS gate, post-rendu)
  M2 SF_06_LIBELLUS                   —   SF_15_LUTHER     (SANS gate, post-rendu)
  M3 SF_07_VEXILLUM                   V7  SF_16_MISSIO     (C3 : soumission < 1 h)
  P1 SF_08_PURGATIO (zéro clé morte)
  M4 SF_09_PORTAS (EXPORT + ledger)
```

La seule frontière entre les deux frégates : le pack JSON dans `EXPORT/` et les deux codex dans `REVIEW/`.

## Usage

```
python murus.py --profile vod     --pack ARCHIVUM/campaign/campaign_directive.json --vod <url|fichier>
python murus.py --profile direct  --channel <twitch_channel>
python murus.py selftest
```

Profil `direct` : la couche d'entrée est le radar chat (`v2-live`, buffer glissant),
une seule validation humaine au TOP 15, SF_10/SF_11 remplacées par la réutilisation
des derniers codex signés. SF_14/SF_15 tournent quand même.

## Exécution

Rien ne tourne sur la machine opérateur : **tout est orchestré par GitHub Actions**
(`.github/workflows/`), la transcription GPU passe par **Modal**
(secrets `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET`).

## Tests

16 tests e2e : `tests/test_murus.py` (statut CDC : ATTENDU → remplacé par la sortie
réelle à la première exécution en CI). Test de doctrine global T0 :

```
grep -rni "ffmpeg\|libx264" FR_A_CERVEAU/   # doit renvoyer ZÉRO ligne
grep -rni "opacity" FR_A_CERVEAU/SF_07_VEXILLUM/  # doit renvoyer ZÉRO ligne
```

## Protocole de mesure

45 clips avant verdict (15 × 3 sessions, postés en 2 semaines). Seuil d'abandon :
revenu net ÷ heure < 0 ⇒ le projet s'arrête. Chiffres interdits sans les 5 éléments :
valeur + unité + période + population + source exacte.

# Charte de design — direction « Instrumentation »

Document **opposable en revue**. Une règle de design qui ne se vérifie pas ne survit pas à six mois de contributions. Chaque règle ci-dessous est soit portée par un token de `design/tokens.css`, soit vérifiable en diff.

## Intention

Cette interface ne plaide pas la vitesse. Elle plaide **la rigueur et l'auditabilité**. C'est l'argument qui gagne en revue de conformité, et c'est ce qui distingue une plateforme d'exploitation bancaire d'un outil SaaS.

Lignée assumée : Dieter Rams (Braun), Massimo Vignelli (Unigrid), Otl Aicher (ERCO), panneaux d'appareils de mesure. Discipline de grille suisse appliquée à l'affichage de mesures.

Trois conséquences directes :

1. **Rien n'est masqué.** Chaque valeur porte son étiquette et sa provenance.
2. **La hiérarchie est typographique et structurelle**, jamais chromatique ni par élévation.
3. **La couleur est une information**, pas une décoration.

---

## Règles dures

### Typographie

| Règle | Token |
|---|---|
| IBM Plex Sans pour le texte, IBM Plex Mono pour toute valeur | `--font-sans`, `--font-mono` |
| Étiquettes en petites capitales, 10 px, interlettrage 0.08em, graisse 600 | `.label` |
| Toute valeur numérique en mono, **chasse tabulaire**, alignée à droite | `.value` |
| L'étiquette est plus petite que sa valeur — l'étiquette chuchote, la valeur parle | `--label-size` < `--value-md` |

`font-variant-numeric: tabular-nums` est non négociable. Sans lui, les chiffres dansent d'une ligne à l'autre et le tableau cesse d'être lisible en un coup d'œil — ce qui est précisément sa seule raison d'exister.

### Provenance

**Toute valeur affichée porte sa source** (`knowledge/patterns/err-rate-spike-paiement`). C'est simultanément le principe esthétique de la direction — rien n'est masqué — et l'exigence d'audit. Les deux contraintes tirent dans le même sens ; c'est rare, et il faut l'exploiter.

Une valeur sans provenance affichable est une valeur qu'on n'a pas le droit d'afficher.

### Couleur

- Fond **papier** (`--ground`), encre **quasi-noire** (`--ink`). Ni `#FFF` ni `#000` : ce sont les deux tells les plus immédiats d'une interface par défaut.
- **La sévérité est la seule couleur de l'interface.** Quatre valeurs, à luminance monotone — P1 le plus sombre, P4 le plus clair.
- La sévérité est **toujours doublée** par l'étiquette textuelle et par la position. Jamais portée par la couleur seule.
- Alerte = chaud (P1, P2). Information = neutre (P3, P4). La distinction chaud/neutre survit aux daltonismes ; la luminance survit au niveau de gris.
- **Boutons** : blocs encadrés ou inversés. Jamais de fond coloré arrondi.

### Hiérarchie

Portée par le **poids de filet** — `--rule-hairline` (1px) pour la division courante, `--rule-major` (2px) pour la division majeure. C'est le geste Vignelli, et il est mécaniquement incompatible avec le look par défaut, qui hiérarchise par ombre portée.

**Aucune `box-shadow`, nulle part.** La séparation se fait par filet et par valeur de fond (`--ground-sunken`, `--ground-raised`).

### Formes

`--radius: 0`. Le rayon est déclaré comme token précisément pour que toute tentative de contournement apparaisse en diff.

### Densité

- Tableaux, pas grilles de cartes. Un écran de triage est une liste de décisions à prendre, pas une galerie.
- Interlignage resserré en tableau (`--dense-leading`), confortable en lecture (`--body-leading`).
- Grille apparente : chez Vignelli, les filets **sont** le design, ils ne le soutiennent pas.

---

## Micro-interactions

**Principe : un instrument ne rebondit pas, il se stabilise.** Décélération pure (`--motion-ease`), aucun ressort, aucun dépassement, aucun `lift` au survol.

| Événement | Traitement | Durée |
|---|---|---|
| Valeur numérique qui change | Roulement vertical du chiffre, façon compteur mécanique | `--motion-settle` 180 ms |
| Changement de sévérité | Fondu du rail, le filet s'épaissit brièvement. Pas de pop. | `--motion-state` 200 ms |
| Dépliage du panneau de preuve | Hauteur animée, les filets se tracent de gauche à droite | `--motion-state` |
| Diff dry-run | Surlignage typographique à la `git diff`, révélé ligne par ligne | `--motion-stagger` 40 ms |
| Fraîcheur des données | Filet sous l'en-tête qui se remplit sur l'intervalle | intervalle réel |
| Survol de ligne | Inversion fond/encre | `--motion-state` |
| Focus clavier | Contour 2 px plein | immédiat |

Interdits explicites : **spinner circulaire**, halo de focus flou, rebond, `lift` au survol, apparition par `scale`.

`prefers-reduced-motion: reduce` met toutes les transitions à zéro. C'est déjà dans `tokens.css` et ce n'est pas une option.

---

## Impression

Les pièces justificatives s'impriment, et une pièce d'audit en noir et blanc doit rester lisible. `tokens.css` différencie donc les sévérités par **style de filet** à l'impression — plein, double, tiret, pointillé — en plus de l'étiquette et de la position. La provenance passe en noir plein : elle fait partie de la pièce.

C'est le seul endroit où le design est contraint par le régulateur plutôt que par l'usage, et c'est aussi le test qui force le reste à être correct.

---

## Anti-checklist

Interdits, sans exception :

- dégradés
- `border-radius` non nul
- `box-shadow`
- emoji comme iconographie
- `backdrop-filter` / glassmorphism
- grille de tuiles KPI flottantes
- Inter
- palette violet / indigo
- bouton à fond coloré arrondi
- spinner circulaire
- couleur décorative — toute couleur qui ne porte pas une sévérité
- valeur de couleur ou d'espacement en dur hors de `tokens.css`

### Vérification

```bash
# Ne doit retourner que des mises à zéro explicites et les définitions de tokens
grep -rnE "border-radius|box-shadow|gradient|backdrop-filter|Inter" --include="*.css" --include="*.tsx" .

# Aucune couleur en dur hors du fichier de tokens
grep -rnE "#[0-9a-fA-F]{3,8}" --include="*.css" --include="*.tsx" . | grep -v "design/tokens.css"
```

Ces deux commandes appartiennent à la revue de design au même titre que les tests à la revue de code.

---

## Ce que cette charte ne dit pas

Elle ne fixe pas la fonte de marque. Si l'institution impose la sienne, la charte tient quand même : l'identité est portée par la grille, les petites capitales, la chasse tabulaire et le poids des filets — pas par la fonte.

Elle ne fixe pas non plus la variante sombre dans le détail. Celle-ci est **dérivée par tokens**, jamais redessinée : mêmes poids de filet, mêmes règles de sévérité, luminance inversée.

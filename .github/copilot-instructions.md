# Instructions Copilot — nbc-triage

Ce dépôt sépare deux couches. Avant de répondre à une demande de triage,
lire la couche connaissance — jamais l'inverse.

## Couche connaissance (l'actif, à toujours consulter)

- `knowledge/categories.md` — la taxonomie de triage, dérivée des billets
  réels. Source de vérité pour toute catégorie proposée.
- `knowledge/severite.md` — matrice de sévérité, critères observables.
- `knowledge/services.md`, `knowledge/escalade.md` — contexte des
  services et des délais.
- `knowledge/patterns/` — motifs d'incidents déjà rencontrés.
- `data/personnes.md`, **s'il existe** — qui a résolu quoi par catégorie,
  généré par `scripts/suggestions.py`. Seule source pour `PERSONNE_SUGGEREE`
  / `PERSONNE_PREUVE`. Local, jamais versionné (contient de vrais noms) —
  absent sur une machine où le script n'a pas encore tourné ; dans ce cas,
  `PERSONNE_SUGGEREE: aucune donnée suffisante`, pas une déduction.

## Ce que « consulter la connaissance » veut dire

Si une réponse n'est pas dans `knowledge/`, elle n'existe pas pour ce
triage — écrire la valeur « pas de donnée » prévue par le prompt utilisé,
jamais une valeur plausible construite autrement (par déduction du nom du
projet, par convention de nommage devinée, etc.). Un identifiant qui a
l'air correct n'est pas une donnée : trouvé une fois avec `EQ-CARTES`,
une équipe qui sonnait juste mais n'existe nulle part dans
`knowledge/services.md`.

## Règle de sortie

Tout triage produit le bloc structuré imposé par le prompt utilisé
(`trier-lot`, `trier-billet`, `completude`) — jamais de prose libre à la
place. Le format existe pour être relu par un script, pas seulement par
un humain.

## Ce que ces prompts ne font jamais

Aucun d'eux n'écrit dans Jira, ne ferme, ne réaffecte ni ne commente un
billet — ils proposent, un humain décide et applique. Vrai même sans
accès technique à Jira depuis ce chat (aucun n'est configuré) : la règle
tient par consigne, pas seulement par absence d'accès, pour rester vraie
le jour où un accès serait ajouté.

## Ce que ce fichier n'est pas

Aucune connaissance métier ici — seulement le renvoi vers `knowledge/`.
Si une réponse Copilot cite un fait métier absent de `knowledge/`, il
manque une fiche, pas une instruction à ce fichier.

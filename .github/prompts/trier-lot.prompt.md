---
mode: agent
description: "Classe un lot de billets PECARTES en masse, sortie strictement formatée"
---

# Trier un lot de billets

Tu reçois un fichier `lots/lot-XX.md` contenant plusieurs billets
(titre + description seulement — c'est tout ce qu'on savait à
l'ouverture). Pour **chaque** billet du fichier, dans l'ordre, produis
un bloc au format suivant, et rien d'autre :

```
### <CLÉ-DU-BILLET>
CATEGORIE: <slug depuis knowledge/categories.md, ou "aucune-correspondance">
PRIORITE: <niveau depuis knowledge/severite.md>
PRIORITE_CRITERE: <une phrase — le critère observable qui justifie ce niveau>
EQUIPE: <nom d'équipe depuis data/personnes.md pour cette catégorie, ou "aucune donnée suffisante" si le fichier n'existe pas ou n'a rien pour cette catégorie>
PERSONNE_SUGGEREE: <nom depuis la section "Personne" de data/personnes.md pour cette catégorie, ou "aucune donnée suffisante" si le fichier n'existe pas ou n'a rien pour cette catégorie. Préférer un nom marqué "spécialisation apparente" (ratio ×N ≥ 1.5) au nom en tête par volume brut si ce dernier a un ratio proche de ×1 — un ratio proche de ×1 veut dire que cette personne ferme beaucoup de billets en général (rôle de triage/répartition), pas qu'elle est spécialiste de cette catégorie précise>
PERSONNE_PREUVE: <ex: "a résolu 14/22 derniers billets de cette catégorie">
COMPLETUDE: <complet|incomplet>
COMPLETUDE_MANQUE: <champs manquants séparés par ";", ou "aucun">
DEJA_VU: <clé d'un billet similaire si évident, sinon "aucun">
FOURNISSEUR: <oui|non|a_confirmer>
CONFIANCE: <valeur entre 0.00 et 1.00>
```

Règles strictes :

- Une clé de billet, une réponse. Ne pas fusionner deux billets.
- Ne jamais deviner un fait absent de `knowledge/`, sur aucun champ —
  écrire `aucune-correspondance` (CATEGORIE) ou `aucune donnée
  suffisante` (EQUIPE, PERSONNE_SUGGEREE) plutôt qu'une valeur plausible
  mais inventée. Un identifiant qui ressemble à un vrai (ex. « EQ-CARTES »
  déduit du nom du projet PECARTES) est encore une invention s'il ne vient
  pas d'un fichier `knowledge/`.
- Si le titre et la description ne suffisent pas à juger la priorité,
  choisir le niveau le plus prudent et l'écrire dans `PRIORITE_CRITERE`.
- Aucun texte avant le premier bloc, aucun texte après le dernier — la
  sortie est lue par `scripts/scorer.py`, pas relue à l'œil.
- Ne propose jamais d'écrire dans Jira, de fermer, ni de réaffecter un
  billet — ce prompt propose, il n'agit pas.

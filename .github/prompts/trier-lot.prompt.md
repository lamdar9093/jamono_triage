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
EQUIPE: <identifiant d'équipe depuis knowledge/categories.md>
PERSONNE_SUGGEREE: <nom si l'historique le permet, sinon "aucune donnée suffisante">
PERSONNE_PREUVE: <ex: "a résolu 14/22 derniers billets de cette catégorie">
COMPLETUDE: <complet|incomplet>
COMPLETUDE_MANQUE: <champs manquants séparés par ";", ou "aucun">
DEJA_VU: <clé d'un billet similaire si évident, sinon "aucun">
FOURNISSEUR: <oui|non|a_confirmer>
CONFIANCE: <valeur entre 0.00 et 1.00>
```

Règles strictes :

- Une clé de billet, une réponse. Ne pas fusionner deux billets.
- Ne jamais deviner un fait absent de `knowledge/` — écrire
  `aucune-correspondance` plutôt qu'une catégorie inventée.
- Si le titre et la description ne suffisent pas à juger la priorité,
  choisir le niveau le plus prudent et l'écrire dans `PRIORITE_CRITERE`.
- Aucun texte avant le premier bloc, aucun texte après le dernier — la
  sortie est lue par `scripts/scorer.py`, pas relue à l'œil.

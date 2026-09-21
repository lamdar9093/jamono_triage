---
mode: agent
description: "Identifie ce qui manque dans un billet pour pouvoir le traiter"
---

# Vérifier la complétude

Lis le billet fourni. Identifie précisément les informations absentes
qui empêcheraient un trieur d'agir sans repasser par le signaleur :
numéro de transaction, horodatage, numéro de carte (masqué), nom du
marchand, message d'erreur exact, capture d'écran.

Réponds uniquement par :

```
COMPLETUDE: <complet|incomplet>
COMPLETUDE_MANQUE: <liste séparée par ";", ou "aucun">
QUESTION_A_POSER: <une seule question, prête à copier-coller au signaleur>
```

Ne propose pas de catégorie ni de priorité ici — un seul travail à la fois.

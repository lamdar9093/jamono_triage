# Catégories de triage — PECARTES

**Brouillon.** Ce fichier doit être dérivé du regroupement manuel de
~200 billets fermés (livrable 2 du plan) — ce travail n'est pas fait.
Les catégories ci-dessous sont des candidats plausibles, tirés des
familles visibles dans les tableaux de bord actuels, à valider ou à
jeter une fois l'échantillon réel analysé.

Format par catégorie : signature observable, mots-clés FR/EN, équipe
propriétaire, champ obligatoire à la soumission, faux voisins.

---

## refus-transaction

**Brouillon — à valider.**

- **Signature observable** : le billet rapporte une transaction refusée
  ou non aboutie côté carte/porteur.
- **Mots-clés FR** : refus, transaction refusée, refusée, non conforme
- **Mots-clés EN** : declined, refused, denial, transaction failed
- **Équipe propriétaire** : à confirmer (EQ-CARTES ?)
- **Champ obligatoire** : numéro de transaction, code de refus si connu
- **Faux voisins** : à distinguer d'une limite/solde atteint
  (`limite-solde`) et d'une erreur d'authentification (`acces-auth`)

## donnees-manquantes

**Brouillon — à valider.**

- **Signature observable** : rapport, export ou synchronisation dont une
  partie des données n'apparaît pas.
- **Mots-clés FR** : aucune data, manque, non disponible, absent
- **Mots-clés EN** : no data, missing, not appearing
- **Équipe propriétaire** : à confirmer (EQ-DONNEES ?)
- **Champ obligatoire** : période concernée, système source
- **Faux voisins** : à distinguer d'une indisponibilité de service
  (`disponibilite-service`)

## acces-auth

**Brouillon — à valider.**

- **Signature observable** : impossibilité de se connecter, session
  refusée, échec OAuth.
- **Mots-clés FR** : connexion impossible, accès refusé, authentification
- **Mots-clés EN** : unable to login, access denied, OAuth
- **Équipe propriétaire** : à confirmer (EQ-IDENTITE ?)
- **Champ obligatoire** : identifiant, horodatage exact de la tentative
- **Faux voisins** : à distinguer d'une indisponibilité de service
  générale

---

## Reste à faire

- Regrouper les ~200 billets fermés en catégories réelles
- Confirmer les équipes propriétaires exactes
- Ajouter les catégories manquantes visibles dans les captures mais pas
  encore détaillées ici : `limite-solde`, `disponibilite-service`,
  `demande-information`, `conformite-validation`, `changement-implementation`
- Retirer les catégories qui ne se confirment pas dans l'échantillon

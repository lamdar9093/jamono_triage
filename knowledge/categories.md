# Catégories de triage — PECARTES

Dérivées de la lecture manuelle de 200 billets fermés (10 lots,
`lots/taxonomie/`), le 2026-09-22 — livrable 2 du plan. Échantillon tiré de
tout l'historique PECARTES, pas seulement du périmètre One Portail (voir
`plan.md`, décision du 2026-09-22).

**Statut : premier passage, à relire sur ta machine.** Ce fichier a été
rédigé ici à partir de captures d'écran de ta lecture — les numéros de
billets et le texte exact peuvent contenir des erreurs de transcription.
Corrige directement plutôt que de faire confiance à la lettre près.

Format par catégorie : signature observable, signaux/codes reconnus,
champ le plus discriminant (s'il est présent — jamais une obligation, voir
plus bas pourquoi), faux voisins.

## Trois champs du gabarit corrigés après lecture réelle

- **« Équipe propriétaire » retiré du gabarit.** Tout arrive dans la même
  file PECARTES ; l'équipe qui traite n'est pas visible à la soumission.
  Spéculatif tant qu'on n'a pas la vraie affectation (via `analyser.py`,
  historique des résolutions).
- **« Champ obligatoire » → « indice le plus discriminant, s'il est
  présent ».** Le corpus est trop hétérogène (courriels collés, extraits
  COBOL, one-liners, billets vides) pour imposer un champ structuré.
- **« Mots-clés FR/EN » → « signaux / codes reconnus ».** L'axe
  français/anglais n'est pas ce qui discrimine. Ce qui marche : les codes
  système et applicatifs (`CKTTFR5`, `SGCI`, `Abend`, noms de job, codes
  bloc) — souvent identiques dans les deux langues.

---

## abend-traitement

**Nouvelle — la plus grosse famille du corpus, absente du brouillon initial.**

- **Signature observable** : plantage ou avertissement sur un traitement
  batch mainframe (« warning client », abend, job en échec).
- **Signaux / codes reconnus** : `Abend`, noms de job, `warning client`
- **Indice discriminant** : le job ou le batch concerné, si nommé
- **Faux voisins** : à distinguer de `fichier-non-reçu` (le batch tourne
  mais le fichier attendu n'arrive pas, vs le batch plante lui-même) et de
  `tache-recurrente` (un abend peut survenir *dans* une tâche récurrente,
  mais n'est pas la tâche elle-même)

## refus-transaction

**Confirmée telle quelle.**

- **Signature observable** : transaction refusée ou non aboutie côté
  carte/porteur.
- **Signaux / codes reconnus** : code de refus (ex. 3057), « BC01 failed »
- **Indice discriminant** : le code de refus, si connu
- **Faux voisins** : `limite-solde` (refus par plafond, pas par la
  transaction elle-même), `acces-habilitation` (refus d'accès, pas de
  transaction)

## fichier-non-reçu

**Scindée de l'ancienne `donnees-manquantes` — c'est la partie majoritaire.**

- **Signature observable** : un transfert ou fichier batch attendu n'est
  jamais arrivé (SGCI, MFT, Ctrl-M file-watch, participant file, fichier
  en retard).
- **Signaux / codes reconnus** : `SGCI`, `MFT`, noms de fichier attendu,
  « non reçu »
- **Indice discriminant** : le nom du fichier/flux attendu et sa fenêtre
  horaire habituelle
- **Faux voisins** : `rapport-errone` (le fichier arrive mais son contenu
  est faux, pas absent), `abend-traitement` (le job plante vs le fichier
  n'arrive juste pas)

## rapport-errone

**Scindée de l'ancienne `donnees-manquantes` — partie minoritaire.**

- **Signature observable** : un rapport ou export arrive, mais contient
  des valeurs fausses ou incohérentes.
- **Indice discriminant** : le champ ou la valeur en cause, si cité
- **Faux voisins** : `fichier-non-reçu` (absence totale vs contenu faux)

## acces-habilitation

**Recadrée — l'ancienne `acces-auth` ratait la vraie signature.**

- **Signature observable** : demande de gestion d'accès interne —
  réinitialiser/débloquer un compte, accès base de données, logon système
  refusé côté job. **Pas** une authentification porteur.
- **Signaux / codes reconnus** : « réinitialiser », « débloquer », logon,
  nom du système (ex. Oracle)
- **Indice discriminant** : le système ou le compte concerné
- **Faux voisins** : ne pas confondre avec un refus de transaction lié à
  une vérification d'identité porteur (`refus-transaction`)

## tache-recurrente

**Nouvelle.**

- **Signature observable** : billets préfixés « RÉCURRENT : » — planifiés,
  répétés, pas des incidents ponctuels.
- **Indice discriminant** : le préfixe « RÉCURRENT » lui-même
- **Faux voisins** : à ne pas classer comme incident même si le contenu y
  ressemble ; peut contenir un `abend-traitement` en sous-cause

## decommissionnement

**Nouvelle.**

- **Signature observable** : demandes de nettoyage/retrait — comptes,
  accès ou configurations à décommissionner.
- **Faux voisins** : `tache-recurrente` (ménage planifié récurrent, à
  distinguer d'un décommissionnement ponctuel)

## bris-confidentialite

**Nouvelle — rare mais à fort enjeu, ne jamais diluer dans une autre
catégorie.**

- **Signature observable** : signalement d'une possible exposition de
  données ou d'un accès non autorisé.
- **Traitement** : à isoler systématiquement, jamais regroupée par volume
  avec les autres catégories — voir `knowledge/severite.md` (accès non
  autorisé confirmé = critère P1).

## saas

**Nouvelle — famille montante.**

- **Signature observable** : billets liés aux produits Brim / PowerCard.
- **À surveiller** : catégorie en croissance, à revisiter au prochain
  passage sur des données plus récentes.

## loyaute-points

**Nouvelle.**

- **Signature observable** : billets liés au domaine fidélité/points.

## bruit-test

**Pas une catégorie de triage — un filtre à appliquer en amont.**

- **Signature observable** : billets de test ou vides, sans contenu
  exploitable.
- **Action** : à exclure des futurs échantillons (taxonomie, évaluation)
  et à vérifier s'ils faussent aussi `rapports/donnees-actuelles.md`
  (non-assignés, déficit créés/fermés) — à vérifier, pas encore fait.

## limite-solde

**Confirmée** — présente dans l'échantillon (limite temporaire, plafond
atteint). Regroupe aussi des demandes d'ops stéréotypées : ouverture de
bloc code, limite temporaire, fusion de succursale — à valider si ce sont
des sous-catégories ou une famille « ops » à part.

## disponibilite-service

**Confirmée** — présente dans l'échantillon, signature à détailler.

## demande-information

**Faible/diffuse dans l'échantillon** — présente mais peu structurée. À
garder en observation, pas encore assez de signal pour une signature
ferme.

## changement-implementation

**Confirmée (2026-09-22) — un point de donnée, pas encore une signature
ferme.** Vue sur PECARTES-21976 lors du premier test réel de
`trier-billet.prompt.md` : demande manuelle planifiée (transfert de
fichiers entre agences SGCI), sans incident ni dégradation. `DEJA_VU`
vérifié par l'utilisateur — pas une fausse piste.

- **Signature observable (provisoire)** : demande *planifiée*, à
  l'initiative de quelqu'un, pas un signalement de panne — verbe à
  l'impératif ou à la demande (« demande de… », « pouvez-vous… »), pas de
  symptôme constaté.
- **Faux voisins** : `fichier-non-reçu` (un transfert *demandé* ici, vs un
  transfert *attendu et absent* là-bas — même sujet, SGCI/fichiers, mais
  direction inverse : on initie une action vs on signale un manque)
- **À faire** : confirmer sur d'autres billets avant de considérer la
  signature stable — un seul cas ne suffit pas.

## conformite-validation

**Toujours à trancher.** Rien de plus que les notes de lecture ambiguës
(transcription depuis photo) — relire directement sur la machine de
travail pour confirmer si elle se confirme dans l'échantillon.

---

## Reste à faire

- Relire ce fichier contre le texte original (pas la transcription photo)
  et corriger les numéros de billets, citations exactes
- Trancher `conformite-validation` (voir ci-dessus — `changement-implementation`
  a un premier point de donnée réel, `conformite-validation` non)
- Confirmer la signature de `changement-implementation` sur plus d'un billet
- Confirmer si les « demandes d'ops stéréotypées » (fusion succursale,
  limite temporaire, ouverture bloc code, ID Check non reçu) forment une
  famille à part ou des sous-cas de `limite-solde`
- Vérifier l'impact de `bruit-test` sur le rapport livrable 1
- Confirmer les équipes propriétaires une fois l'historique de résolution
  exploité (pas à la soumission — voir la correction de gabarit plus haut)

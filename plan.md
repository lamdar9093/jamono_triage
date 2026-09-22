Étape 1 — Triage assisté sur One Portal (projet PECARTES)
Context
Objectif final : une plateforme d'entrée unique, pilotée par l'IA, qui apprend et gère le triage, affecte à la bonne équipe, suit les incidents et conserve l'historique — jusqu'à savoir combien de temps chaque type d'incident prend réellement.

On n'y va pas d'un coup. Étape 1 = le triage seul, validé et mesuré, avant de passer à la suite.

Le terrain est maintenant réel. Le métier ouvre des billets dans Jira One Portal (projet PECARTES), les équipes trient. Ce que montrent les tableaux de bord actuels :

554 billets au total ; 154 créés cette semaine contre 74 fermés
Files : Triage (2), Waiting for support (26), In progress (146), Closed (407)
La courbe créés contre résolus décroche nettement : le stock grossit
Billets rédigés par le métier, en français et en anglais, de qualité très inégale
Lien fournisseur via External issue ID (N1PSC-*), avec des N1PSC-TBD non résolus
Étiquettes hétérogènes : SaaS_Cartes, EEC-Transactionnel, EEC-Servicing, automatedcreation, aide, probleme, R011, None
Doublons probables visibles à l'œil nu (même signaleur, même jour, même sujet)
Billets non assignés qui stagnent en « Waiting for support »
Des billets ouverts depuis plus de neuf mois
Observations à confirmer sur les données réelles — elles viennent de captures d'écran, pas d'un export.

Le principe directeur
Résolution à trois niveaux : pattern connu (0 token) → pattern approchant → jugement humain, qui écrit le pattern pour la fois suivante.

La valeur n'est jamais au niveau 2. Elle est au niveau 1 — la connaissance qui rend l'IA inutile — et au niveau 3 — le jugement qui produit de la connaissance neuve.

Conséquence : les prompts sont jetables, la taxonomie et le jeu d'évaluation ne le sont pas.

Ce qui existe déjà et sert ici
knowledge/severite.md — la méthode des critères observables et les anti-critères ; la matrice sera remplacée par celle dérivée des vraies données
knowledge/patterns/_gabarit.md — le format de fiche, réutilisé tel quel
design/charte.md et design/tokens.css — pour toute restitution visuelle
Les maquettes publiées — la file de triage et le panneau de justification décrivent déjà la cible
Contraintes réelles, et ce qu'elles imposent
Moteur IA : GitHub Copilot dans VS Code uniquement. Pas d'appel LLM programmatique. La boucle d'évaluation comporte donc un humain : un script prépare des lots en markdown, tu lances un prompt Copilot dessus, un script note la sortie. Acceptable à 120 billets (~30 min de ton temps), impossible à 554 — d'où l'échantillonnage. Conséquence de conception : le fichier de prompt doit imposer un bloc de sortie strictement parsable, sinon la notation est manuelle et le projet meurt.

Accès Jira : API en lecture. Jeton personnel en lecture seule, portée limitée au projet PECARTES. L'appel doit demander expand=changelog — sans l'historique des changements, la mesure de référence n'existe pas.

Données réelles. data/ est ignoré par git et ne quitte jamais la machine. Le dépôt contient les scripts, la taxonomie et des exemples anonymisés. Le rapport remis à ta gestionnaire est généré localement, avec les vrais noms. La méthode est transférable, les données ne le sont pas.

Périmètre de l'étape 1
L'assistant, sur un billet entrant, propose — il ne décide rien et n'écrit rien dans Jira :

Catégorie — depuis la taxonomie dérivée des billets réels
Priorité — avec le critère qui l'a déclenchée
File et équipe — l'affectation structurelle
Personne suggérée — à titre indicatif, avec sa preuve (« a résolu 14 des 22 derniers billets de cette catégorie »), jamais un nom seul
Complétude — ce qui manque pour trancher (numéro de transaction, horodatage, carte, marchand)
Déjà-vu — billet similaire ou doublon probable, avec son numéro
Fournisseur concerné — et si un External issue ID devrait exister
Hors périmètre : toute écriture dans Jira, la gestion du cycle de vie, les communications, les post-mortems.

Le point 5 est sous-estimé. La moitié du temps de triage part en allers-retours pour obtenir l'information manquante. Signaler le manque ne décide rien, ne vexe personne, et se voit dès le premier jour.

Qui fait quoi
Le plan précédent disait « humain » sans préciser qui. Voici la répartition réelle.

Tâche	Qui	Volume	Temps estimé
Scripts (extraction, analyse, notation)	Toi	—	quelques heures, une fois, puis automatique
Taxonomie — regroupement des billets fermés	Toi	~200 billets	4-8 h, étalées semaines 1-2
Vérité terrain des cas d'évaluation	Toi	120 billets	2-3 h
Boucle Copilot (lancer les prompts, coller les sorties)	Toi — ton accès Copilot	120 billets, 6 lots	2-3 h, étalées semaines 2-3
Contrôle à l'aveugle	Quelqu'un d'autre de l'équipe	20 billets	30-60 min de son temps, une fois
Total solo : ~10-15 h étalées sur trois semaines, en plus du travail courant.

Pourquoi solo plutôt qu'en équipe. La taxonomie et la boucle Copilot sont délibérément laissées seules : c'est le travail que personne d'autre n'a fait, et c'est lui qui te positionne à la démo — le partager tôt, c'est partager la visibilité avant d'avoir un résultat à montrer. La seule tâche qui doit impliquer quelqu'un d'autre est le contrôle à l'aveugle, par construction : cette personne teste ta vérité terrain, donc ça ne peut pas être toi qui l'as écrite. Elle n'a pas besoin de connaître le projet en entier — une demande simple (« peux-tu trier ces 20 billets pour moi, je compare des approches ») suffit.

Comment ça fonctionne une fois livré
Ce n'est pas encore une plateforme web. À l'étape 1, c'est VS Code et Jira, deux fenêtres. Le tableau de bord des maquettes est la cible des étapes 4-5, pas ce qu'on construit ici.

Boucle quotidienne — un billet arrive

Le métier ouvre un billet dans One Portal, exactement comme aujourd'hui — rien ne change de son côté
extraire.py lit les billets en statut « Triage » via l'API
lots.py les met en forme dans un fichier markdown court
Tu ouvres le fichier dans VS Code et tu lances le prompt Copilot
Copilot répond : catégorie, priorité, équipe, personne suggérée avec sa preuve, ce qui manque, doublon éventuel
Tu lis, tu valides ou tu corriges — la décision reste humaine
Tu appliques toi-même dans Jira. L'outil n'écrit rien automatiquement à cette étape
Si le billet révèle un motif nouveau ou récurrent, tu l'ajoutes à knowledge/categories.md ou patterns/
Boucle périodique — hebdomadaire ou à la demande : relancer analyser.py sur un export frais régénère le rapport ; relancer scorer.py met à jour evals/resultats.md.

L'apprentissage est manuel, et c'est délibéré
Aucun réentraînement, aucune croissance automatique de la connaissance. La base ne grossit que quand tu écris une fiche après un incident — c'est l'étape 3 du principe directeur, le kb_save fait à la main.

La raison est le ratio : 200 incidents doivent donner une quinzaine de fiches. Automatiser la distillation produirait une fiche par billet, c'est-à-dire un journal reformaté, pas une base de connaissance. Et un résumé automatique reprend l'hypothèse initiale avec la même assurance que la cause réelle — c'est le piège du chatbot, appliqué à l'écriture au lieu de la lecture.

L'automatisation de cette étape est prévue, mais encadrée — voir étape 6.

Les cinq livrables
1. Rapport « ce que vos données disent déjà » — semaine 1, sans aucune IA
C'est le livrable qui ouvre les portes, et il ne contient pas une ligne d'IA. Contenu :

Créés contre fermés par semaine, et déficit cumulé — la dette qui s'accumule
Délais de traitement : médiane et p90, jamais la moyenne seule, découpés par priorité et par catégorie
Temps en attente d'un tiers (Waiting for support, Waiting for delivery) séparé du temps de traitement interne — c'est le temps fournisseur, et il alimente directement la demande de ta gestionnaire
Top catégories par volume et par temps consommé — les deux classements diffèrent toujours, et l'écart est le résultat intéressant
Doublons suspectés, avec leurs numéros
Billets non assignés, et depuis combien de temps
Billets rouverts, billets réaffectés
Part des billets sans lien fournisseur, et des N1PSC-TBD
Les billets les plus anciens encore ouverts
2. Taxonomie de triage — semaine 1-2
Dérivée des billets fermés, pas inventée. Regroupement manuel de ~200 billets fermés en catégories réelles. Les familles visibles dans les captures : refus de transaction, données ou rapport manquant, accès et authentification, limite et solde carte, disponibilité de service, demande d'information, conformité et validation, changement et implémentation.

Livrée sous forme de knowledge/categories.md : par catégorie, la signature observable, les mots-clés FR et EN, l'équipe propriétaire, le champ obligatoire à la soumission, et les faux voisins.

C'est l'actif. Il reste utile même si tout le reste est abandonné.

3. Jeu d'évaluation — semaine 2
120 billets fermés, échantillonnés pour couvrir les catégories et les priorités. Pour chacun : ce qui était connu à l'ouverture (titre + description seuls) et la vérité terrain.

La vérité terrain n'est pas la première affectation — c'est l'équipe qui a réellement résolu et la priorité finale. C'est cette distinction qui rend la mesure honnête.

4. Skills de triage — semaine 2-3
Fichiers Copilot, volontairement minces et sans connaissance métier dedans :

.github/prompts/trier-lot.prompt.md — le classement en masse, sortie parsable imposée
.github/prompts/trier-billet.prompt.md — un billet, usage quotidien
.github/prompts/completude.prompt.md — ce qui manque
.github/copilot-instructions.md — routeur mince, ~30 lignes, aucun contenu métier
Test de survie : supprimer .github/ en entier ne doit rien retirer à knowledge/.

5. La mesure — semaine 3
Quatre chiffres datés dans evals/resultats.md :

Ce qu'il mesure
Référence actuelle	Taux de billets réaffectés au moins une fois, tiré du changelog Jira
Copilot seul	Sans la taxonomie
Copilot + taxonomie	Avec knowledge/categories.md
Complétude	Part des billets où l'information manquante est correctement identifiée
La référence actuelle est le coup stratégique. Un billet réaffecté est un triage raté, et Jira en garde la trace. Personne dans ton organisation n'a ce chiffre aujourd'hui. Il donne la barre à battre, et il se produit avant toute IA.

Même règle pour le reclassement de priorité : un billet dont la priorité change après l'ouverture est un billet mal priorisé au départ.

Chaîne technique
Python local, aucun appel externe hors Jira interne.

scripts/extraire.py    Jira API (expand=changelog) → data/billets.json   [ignoré par git]
scripts/anonymiser.py  → data/billets-anon.json
scripts/analyser.py    → rapports/donnees-actuelles.md         (livrable 1)
scripts/lots.py        → lots/lot-01.md … lot-06.md            (20 billets/lot)
   ↳ toi : ouvres dans VS Code (Copilot = ton siège), lances /trier-lot, colles la sortie dans lots/sorties/
scripts/scorer.py      → evals/resultats.md                    (livrable 5)
scorer.py compare sur quatre axes indépendants — catégorie, priorité, équipe, complétude — parce qu'un score global masque exactement ce qu'on a besoin de savoir.

La suggestion de personne est calculée par analyser.py à partir de l'historique (qui a résolu quoi, par catégorie), pas maintenue à la main. Elle porte toujours son décompte.

Séquence
Semaine 1 — le rapport. Jeton Jira, extraction, analyser.py, rapport. Aucune IA. Livrable présentable en fin de semaine.

Semaine 2 — la taxonomie et les evals. Regroupement des billets fermés, knowledge/categories.md, 120 cas de vérité terrain, référence actuelle calculée.

Semaine 3 — les skills et la mesure. Prompts Copilot, six lots passés, notation, evals/resultats.md.

Semaine 4 — la démo. À ta gestionnaire d'abord. Ordre imposé : le rapport, puis la référence actuelle, puis le résultat mesuré. Jamais la démo en premier.

Vérification
Reproductibilité de l'extraction. Relancer extraire.py deux fois à une heure d'écart donne le même corpus aux billets nouveaux près. Sinon la mesure n'est pas stable.
Fuite. grep -riE "<noms réels>|<numéros de carte>|<courriels>" sur tout ce qui est versionné doit ne rien retourner. data/ absent du suivi git, vérifié avec git status --ignored.
Evals. Les quatre chiffres produits, datés. Critère de réussite : Copilot + taxonomie bat Copilot seul. Si ce n'est pas le cas, c'est la taxonomie qu'il faut revoir — pas le prompt.
Sortie parsable. scorer.py doit lire 100 % des sorties Copilot sans intervention. Un seul lot non parsable et le format de prompt est à corriger avant d'aller plus loin.
Test de survie. Supprimer .github/ : knowledge/ et les rapports restent pleinement utiles.
Contrôle à l'aveugle. Faire trier 20 billets à un trieur expérimenté de l'équipe — quelqu'un d'autre que toi, précisément pour tester ta vérité terrain sans le biais de l'avoir écrite toi-même — puis comparer. Si cette personne fait moins bien que prévu sur ces 20, la vérité terrain est suspecte et doit être revue avant toute conclusion.
Risques
Mesurer les réaffectations touche à la performance des gens. C'est le risque qui tue ce genre de projet. Règle : les chiffres remontés le sont par file et par catégorie, jamais par personne. Aucun nom dans le rapport partagé. La suggestion de personne, elle, reste dans l'outil et affiche sa preuve — c'est ce qui la rend défendable plutôt que arbitraire.

Le contenu des billets est de l'entrée non fiable, écrite par des tiers. En étape 1 l'assistant ne fait que proposer et un humain relit tout : le risque est faible et se limite à une mauvaise suggestion. À documenter maintenant, parce que ça devient critique à l'étape où l'écriture s'active.

Le piège du chatbot. Si quelqu'un propose de brancher un assistant conversationnel sur l'historique des billets, la réponse est : un fil de billet contient l'hypothèse initiale, les fausses pistes et la cause réelle sans jamais les distinguer — il citera la mauvaise avec assurance. C'est pourquoi on classe sur des champs, pas sur du texte libre.

Après l'étape 1
Chaque étape se valide et se mesure avant la suivante.

Étape 2 — complétude à la soumission : signaler le manque au métier au moment où il ouvre le billet, là où la correction coûte le moins
Étape 3 — détection de doublons et rapprochement avec les billets déjà résolus
Étape 4 — écriture dans Jira, une action à la fois, avec dry-run permanent et journal d'audit
Étape 5 — cycle de vie, communications, historique complet des durées par type d'incident. C'est ici qu'arrive l'interface web, et c'est ici que design/charte.md devient actif : direction Instrumentation, micro-interactions spécifiées, anti-checklist vérifiable en diff.
Étape 6 — connaissance semi-automatique. Après chaque billet fermé, le système propose un brouillon de fiche ; il n'entre dans knowledge/patterns/ qu'après ta validation — garder, fusionner à un motif existant, ou rejeter. La détection devient automatique, la décision reste humaine. C'est le dry-run appliqué à la connaissance. Bloqueur connu : demande un déclenchement automatique et un appel LLM programmatique. Copilot en interactif ne le permet pas — il faut une API approuvée par la banque. À poser comme question de sécurité dès maintenant, la réponse conditionne le calendrier de cette étape.
Le registre fournisseur demandé par ta gestionnaire n'est pas un projet parallèle : c'est la séparation du temps d'attente tiers du livrable 1, plus le format de fiche existant. Même travail, commanditaire en plus.

Effet attendu sur l'autonomie. Un nouvel arrivant tombant sur un type de demande déjà rencontré voit le motif, les résolutions passées, le niveau de confiance et les pièges connus — au lieu de repartir de zéro. Ça vaut pour le volume récurrent, pas pour l'inédit, qui continue de demander du jugement. Comme l'outil affiche aussi ce qu'il ne sait pas (« cause racine non confirmée »), la personne sait quand suivre la suggestion et quand demander de l'aide.

Décisions en attente de ta part
Prototype cliquable avant le code ? Les maquettes publiées sont statiques — le bon rendu visuel, mais pas le ressenti réel (transitions, retour au clic, enchaînement des écrans). Un prototype cliquable se construit sur les mêmes artboards et permet de juger la qualité d'interaction avant d'écrire du code de production. Question posée deux fois, toujours sans réponse.
API LLM approuvée — existe-t-elle à la banque, et sur quel type de contenu ? Conditionne l'étape 6 et, plus tard, tout traitement en masse au-delà de 120 billets.
Ce qui te rend visible, concrètement
Trois choses impressionnent dans une banque, et aucune n'est une démo :

Un chiffre que personne n'a. Le taux de réaffectation et le déficit créés/fermés en font partie.
Un constat que personne n'avait vu. Les doublons, les billets orphelins, le temps réellement passé chez le fournisseur.
Quelque chose qui marche lundi. La complétude, utilisable sans rien approuver.
C'est pour ça que le rapport sans IA passe en premier : il t'installe comme celui qui connaît la vérité de l'opération. L'IA arrive ensuite comme une conséquence crédible, pas comme une promesse.

---

# Journal d'avancement

À mettre à jour à la fin de chaque session. Le plan ci-dessus ne change pas ; ce journal dit où on en est.

## Contexte de terrain (précisé le 2026-09-21)

- Le projet PECARTES contient **25 928 billets**, pas 554. Les 554 des captures d'écran étaient une vue filtrée (les billets One Portail). À vérifier sur les données.
- Trois origines de billets dans PECARTES :
  1. **One Portail** : ouverts par l'équipe business pour un client. Marqueurs : label `automatedcreation`, Request type renseigné (« J'ai besoin d'aide »), Customer status (« Triage »).
  2. **Directs** : quelqu'un reçoit un mail ou un chat Teams et crée le billet dans le board. Marqueurs : pas de label, « No request type », Epic Link renseigné.
  3. **Tâches doublons** : quelqu'un recrée dans PECARTES une tâche pour un billet support. Difficiles à repérer automatiquement.
- **Décision de périmètre (2026-09-21) : l'étape 1 porte sur tous les billets qui arrivent par One Portail**, avec ou sans le label `automatedcreation`, parce que c'est le périmètre métier. Le tableau de bord « Powercard Support » en montre **670** ; le label n'en marque que 195, c'est donc un sous-groupe (la file Triage) et non le critère de périmètre.
- Chiffres du plan ci-dessus (554 billets, 407 fermés) : instantané plus ancien. Au 2026-09-21 le tableau de bord affiche 670 billets, 422 fermés — le stock grossit, ce qui confirme le décrochage créés/résolus.
- **Critère de périmètre retenu (2026-09-22) : Customer Request Type renseigné (`customfield_11200`) ET créé depuis le 11 juin 2026** (date du premier billet `automatedcreation`, prise comme date de lancement de One Portail). Historique : le Request Type est utilisé depuis 2016 (bien avant One Portail), donc sa seule présence ne suffit pas — il fallait la borne de date. Ce critère donne **959 billets**, contre 670 sur le tableau de bord Powercard.
  - L'écart 959 vs 670 n'est pas résolu et n'a pas à l'être : le tableau de bord s'appelle « Powercard Support » et semble n'en montrer qu'une partie (Application Card = Powercard donne 328, donc même pas ça exactement — son JQL réel reste inconnu). Décision explicite : on ne cherche pas à reproduire 670, on garde 959 comme périmètre de travail, car il correspond à la décision métier (toutes les applications de l'équipe, pas seulement Powercard).
  - Si ce chiffre doit être revalidé un jour, comparer au JQL exact du Rich Filter Jira (jamais obtenu malgré deux demandes).
- **Retour en arrière (2026-09-22, plus tard le même jour) : le périmètre par défaut redevient le label `automatedcreation` seul** (~195 billets), pas le critère large. Raison : le critère large (Request Type + date) est de toute façon *ancré* sur la date du premier billet labellisé — ce n'est pas une donnée indépendante, juste une extrapolation. Le label, lui, est posé par le système sans hypothèse de notre part. Ça colle aussi mieux à l'esprit du plan : commencer étroit et validé (la vraie file triage), élargir plus tard une fois l'étape 1 mesurée. `analyser.py` garde le critère large sous `--large`, pour le jour où on élargira.
- Le type de billet (`Support Request`) ne distingue pas les origines.

## Étape 1 — Semaine 1 (le rapport)

- [x] Jeton Jira lecture seule
- [x] `scripts/extraire.py` : extraction complète, incrémentale (`updated >=`), reprise sur coupure, nouvelles tentatives sur timeout. **Fait le 2026-09-21 : 25 928 billets dans `data/billets.json`** (sur la machine de travail, pas dans le dépôt).
- [x] Vérification de reproductibilité : relance juste après = 6 billets mis à jour, 0 doublon.
- [x] Comptage `automatedcreation` : 195 sur 25 928. Insuffisant comme périmètre (voir décision ci-dessus).
- [x] `scripts/anonymiser.py` → `data/billets-anon.json`
- [x] `scripts/analyser.py` : segmente par origine, options `--directs` et `--tous`. Premier rapport produit sur les 195 — à refaire sur le bon périmètre.
- [x] `scripts/champs.py` : Customer Request Type = `customfield_11200`, Application Card = `customfield_37502`, External issue ID = `customfield_17800`, Type de demande = `customfield_12447` (rôle à confirmer)
- [x] Ajoutés à `FIELDS` dans `extraire.py` (et `CHAMP_EXTERNAL_ID` dans `analyser.py`)
- [x] Extraction complète (`--complet`) faite le 2026-09-22 avec les nouveaux champs
- [x] `analyser.py` : périmètre par défaut = label `automatedcreation` (retour en arrière, voir décision ci-dessus) ; `--large` garde le critère Request Type + date pour plus tard
- [x] Premier rapport lu (sur le périmètre 959, avant le retour en arrière) : déficit cumulé +204, 35,8 % de priorité changée après ouverture, un pic suspect semaine 2026-S38 (199 créés, à recouper avec l'amas de doublons PECARTES-25432→25452) — à revoir sur le périmètre label seul, le pic en fait peut-être partie ou non
- [ ] Relancer `python3 analyser.py` (périmètre label, par défaut) et relire `rapports/donnees-actuelles.md`
- [ ] Rapport présentable en fin de semaine (livrable 1), sans IA

## Étapes suivantes

Semaine 2 (taxonomie et evals), semaine 3 (skills et mesure), semaine 4 (démo) : voir la « Séquence » ci-dessus. Pas commencées.

## Décisions en attente

Voir « Décisions en attente de ta part » : prototype cliquable, API LLM approuvée. Toujours sans réponse.

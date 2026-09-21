# Matrice de sévérité

Le fichier le plus important du dépôt. Il rend le triage **reproductible** — par un humain expérimenté, par un N1 de sa deuxième semaine, ou par une machine. Si deux personnes appliquent ce fichier au même incident et n'arrivent pas au même niveau, c'est ce fichier qu'il faut corriger, pas les personnes.

## Principe de rédaction

Les critères sont **observables**. Une valeur mesurable, une fenêtre de temps, un seuil. Jamais un adjectif.

| À proscrire | À écrire |
|---|---|
| « impact important » | « >5% d'erreurs sur 5 min » |
| « beaucoup de clients » | « >10 000 sessions actives affectées » |
| « service critique » | « service de tier 1 » (défini dans `services.md`) |
| « depuis un moment » | « depuis plus de 15 min » |

Un adjectif dans ce fichier est un défaut à corriger.

---

## Les quatre niveaux

### P1 — Critique

Au moins un de ces critères :

- Un service de **tier 1** est indisponible, ou dégradé au-delà du seuil P1 du tableau ci-dessous
- Les clients ne peuvent pas effectuer de transaction financière
- Perte ou corruption de données financières, **quelle qu'en soit la quantité**
- Accès non autorisé confirmé à un système ou à des données
- L'incident remplit les critères de déclaration réglementaire (voir plus bas)

**Conséquence** : mobilisation immédiate, canal d'incident ouvert, communication toutes les 30 min.

### P2 — Majeur

- Un service de **tier 1** est dégradé sans atteindre le seuil P1
- Un service de **tier 2** est indisponible
- Un contournement existe mais il est **manuel** — donc il ne tient pas à l'échelle ni dans la durée
- Dégradation qui s'aggrave et atteindra un seuil P1 dans moins de 2 h au rythme observé

**Conséquence** : prise en charge dans l'heure, communication toutes les 2 h.

### P3 — Mineur

- Un service de **tier 3** est affecté
- Un service de **tier 2** est dégradé sans indisponibilité
- Le contournement est **automatique**, ou l'impact n'est pas visible du client
- Traitement différé qui rattrapera son retard sans intervention

**Conséquence** : traitement en heures ouvrables, pas de communication client.

### P4 — Faible

- Aucun impact client, actuel ou anticipé
- Aucun risque d'escalade dans les 24 h
- Correction planifiable dans le cycle normal

**Conséquence** : billet ouvert, pas d'astreinte.

---

## Seuils observables

Valeurs de référence. Un service peut redéfinir son seuil dans `services.md` — la valeur du service l'emporte alors sur ce tableau, ce qui doit rester l'exception et non la règle.

| Signal | P1 | P2 | P3 |
|---|---|---|---|
| Taux d'erreur, tier 1 | > 5 % sur 5 min | > 1 % sur 15 min | > 0,5 % sur 30 min |
| Taux d'erreur, tier 2 | > 15 % sur 5 min | > 5 % sur 15 min | > 1 % sur 30 min |
| Latence p99 vs référence 7 j | > 3× sur 5 min | > 2× sur 15 min | > 1,5× sur 30 min |
| Disponibilité | indisponibilité totale | indisponibilité partielle > 10 % des requêtes | dégradation sans perte |
| Retard de file / batch | > 4 h, ou fenêtre réglementaire menacée | > 2 h | > 30 min, rattrapage prévu |
| Sessions clients affectées | > 10 000 | > 1 000 | > 100 |

**Lecture du tableau** : le niveau retenu est le **plus élevé** atteint par n'importe quelle ligne. Un seul signal au seuil P1 suffit à faire un P1.

---

## Règles de décision

**En cas de doute, monter d'un cran.** L'asymétrie est nette : un P1 excessif coûte une heure d'attention à quelques personnes ; un P1 classé P3 coûte un incident réglementaire, une déclaration tardive et une reconstitution a posteriori. Ces deux erreurs ne se valent pas et le triage ne doit pas faire semblant du contraire.

**La sévérité se réévalue.** Elle est fixée sur l'information disponible à l'instant T, pas sur la vérité finale. Rétrograder un P1 en P2 dès que les faits le justifient est un comportement correct, pas un aveu d'erreur. Le journal conserve les deux et la raison du changement.

**Un seul niveau par incident, celui du pire impact.** Ne pas moyenner entre plusieurs services touchés.

## Anti-critères

Ces éléments ne déterminent **jamais** la sévérité. Ils sont listés parce que chacun influence le triage en pratique, et qu'il faut pouvoir les nommer pour les écarter.

- Qui signale l'incident, et son niveau hiérarchique
- L'heure, le jour, ou la proximité d'un congé
- Qui est d'astreinte et sa charge du moment
- Le fait qu'un incident similaire ait été classé plus bas la semaine dernière
- L'insistance de l'équipe qui signale
- Le coût perçu de la mobilisation

Si l'un de ces éléments change le niveau, le triage n'est pas reproductible — et il ne sera pas défendable en revue.

---

## Déclaration réglementaire

Certains incidents technologiques déclenchent une obligation de notification au régulateur, avec un délai contraint. **Ce n'est pas au triage de trancher le seuil réglementaire**, mais c'est à lui de lever le drapeau.

Champ obligatoire à l'ouverture de tout P1 et P2 : `declaration_reglementaire: oui | non | à_qualifier`.

- `à_qualifier` déclenche la notification de l'équipe conformité dans l'heure
- Les critères exacts et les délais sont maintenus par l'équipe conformité, pas ici

> **À compléter avec l'équipe conformité avant mise en production.** Référencer la procédure interne applicable plutôt que de recopier les critères ici — un seuil réglementaire recopié devient un seuil réglementaire périmé.

---

## Comment ce fichier évolue

Toute divergence de classement entre deux personnes sur un même incident est une **entrée de backlog sur ce fichier**. La cible n'est pas que les gens apprennent la matrice : c'est que la matrice ne laisse plus de place au désaccord.

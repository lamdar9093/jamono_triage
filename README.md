# nbc-triage

Socle de connaissance et de design pour une plateforme de triage d'incidents unifiée — une seule entrée, des skills derrière, utilisable par des non-techniques.

**Ce dépôt est anonymisé.** Aucun nom réel de service, d'équipe, de personne ou d'institution n'y figure. Les services portent des identifiants génériques (`PAIEMENT-1`, `CORE-2`). La table de correspondance vers les noms réels n'existe pas ici et ne doit jamais y entrer.

---

## La règle du dépôt

> **Si l'outil d'IA disparaît demain, ce fichier a-t-il encore de la valeur ?**

- **Non** → c'est un prompt. Couche jetable. Elle ne contient **aucune** connaissance métier.
- **Oui** → c'est un actif. Il vit dans `knowledge/`, `evals/`, `governance/`, `design/`.

Cette règle décide de l'emplacement de chaque fichier. Elle existe parce que le framework LLM changera trois fois en cinq ans, tandis que le catalogue de services, la matrice de sévérité et les patterns d'incidents survivront à chaque réécriture.

## Le principe à trois niveaux

Tout le système applique la même résolution :

| Niveau | Mécanisme | Coût | Qui l'écrit |
|---|---|---|---|
| **1** | Pattern connu → réponse déterministe | 0 token | Un humain, une fois |
| **2** | Pattern approchant → assistance | modéré | L'outil du moment |
| **3** | Inconnu → jugement humain, puis **on écrit le pattern** | élevé | Un humain, qui crée le niveau 1 de demain |

La valeur n'est jamais au niveau 2. Elle est au niveau 1 — la connaissance qui rend l'assistance inutile — et au niveau 3 — le jugement qui produit de la connaissance neuve.

---

## Structure

```
knowledge/     Le socle. Utile à un humain qui n'a jamais ouvert d'outil d'IA.
  severite.md    Matrice P1→P4, critères observables. Le fichier le plus important.
  services.md    Catalogue, tiers, ownership, dépendances.
  escalade.md    Qui, quand, dans quel ordre, sous quel délai.
  categories.md  Taxonomie de triage PECARTES — brouillon, à valider sur données réelles.
  patterns/      Un fichier par motif d'incident récurrent.

design/        La charte, opposable en revue.
  charte.md      Direction « Instrumentation ». Règles dures et anti-checklist.
  tokens.css     Seule source de vérité couleur / typo / espacement.

evals/         Protocole de mesure + cas d'incidents passés avec la bonne réponse.
governance/    Périmètre de décision, traçabilité, risques. À venir (étape 4).

scripts/       Extraction Jira, anonymisation, analyse, lots de triage, notation.
.github/       Prompts Copilot — couche jetable, aucune connaissance métier dedans.
data/, lots/, rapports/   Générés localement, ignorés par git — voir Démarrage.
```

## Ordre de lecture

1. `knowledge/severite.md` — comprendre comment une décision se prend ici
2. `knowledge/services.md` — savoir de quoi on parle
3. `knowledge/patterns/` — voir à quoi ressemble la connaissance capitalisée
4. `design/charte.md` — si tu touches à l'interface

## Contribuer un pattern

Tout incident résolu au niveau 3 doit finir en fichier dans `knowledge/patterns/`. C'est la seule mécanique qui fait grossir l'actif. Copier `knowledge/patterns/_gabarit.md` et le remplir pendant que l'incident est frais — pas trois semaines plus tard.

---

## Étape 1 — Triage assisté (PECARTES)

Terrain réel : le métier ouvre des billets dans Jira One Portal (projet `PECARTES`), les équipes trient. L'étape 1 fait proposer un triage par Copilot — catégorie, priorité, équipe, personne suggérée avec sa preuve, complétude, doublon probable — sans jamais rien écrire dans Jira. La décision et l'écriture restent humaines.

**Ce n'est pas encore une plateforme web.** À ce stade, c'est VS Code et Jira, deux fenêtres. Voir le plan pour la séquence complète et ce qui vient après.

### Démarrage

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # remplir JIRA_BASE_URL et JIRA_API_TOKEN

python scripts/extraire.py      # → data/billets.json (ignoré par git)
python scripts/anonymiser.py    # → data/billets-anon.json
python scripts/analyser.py      # → rapports/donnees-actuelles.md  (livrable 1, sans IA)
python scripts/lots.py          # → lots/lot-01.md … lot-06.md (120 billets, 20/lot)
```

Puis, pour chaque lot : ouvrir dans VS Code, lancer `/trier-lot` (Copilot), coller la sortie dans `lots/sorties/`. Une fois tous les lots traités :

```bash
python scripts/scorer.py        # → evals/resultats.md
```

### Ce qui reste manuel, et pourquoi

La taxonomie (`knowledge/categories.md`, ~200 billets à regrouper) et la boucle Copilot sont volontairement faites à la main, une fois — c'est le travail que personne d'autre n'a fait. La connaissance ne grossit pas automatiquement après : chaque fiche de `knowledge/patterns/` s'ajoute quand un humain la juge digne d'être gardée, jamais par résumé automatique d'un fil de billet.

### Données réelles

`data/`, `lots/*.md`, `rapports/*.md` et `evals/resultats.md` sont ignorés par git — ils ne quittent jamais la machine. Vérifier avant tout partage : `git status --ignored`.

# Protocole d'évaluation

120 cas tirés de billets fermés (voir `scripts/lots.py`). Chaque cas :
ce qui était connu à l'ouverture (titre + description) et la vérité
terrain (équipe qui a **réellement résolu**, priorité **finale** — pas
la première affectation).

Quatre chiffres, datés, dans `resultats.md` :

| | Ce qu'il mesure |
|---|---|
| Référence actuelle | Taux de réaffectation, tiré du changelog Jira — calculé par `scripts/analyser.py`, avant toute IA |
| Copilot seul | Sans `knowledge/categories.md` |
| Copilot + taxonomie | Avec `knowledge/categories.md` |
| Complétude | Part des billets où l'information manquante est correctement identifiée |

Critère de réussite : Copilot + taxonomie bat Copilot seul. Sinon,
c'est la taxonomie qui est à revoir — pas le prompt.

Voir aussi la Vérification #6 du plan : contrôle à l'aveugle par
quelqu'un d'autre que la personne qui a écrit la vérité terrain.

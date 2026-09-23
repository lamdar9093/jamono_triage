#!/usr/bin/env python3
"""
Diagnostic : Carmen Lecceses domine-t-elle plusieurs catégories dans
data/personnes.md par spécialisation réelle, ou simplement parce qu'elle
ferme le plus de billets, toutes catégories confondues (auquel cas elle
"gagnerait" mécaniquement chaque catégorie par volume) ?

Compare sa part GLOBALE (tous billets fermés du périmètre, rouverts
exclus) à sa part DANS CHAQUE catégorie où elle apparaît en tête.
"""
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyser import FENETRE_MOIS_DEFAUT, _borne_fenetre, a_ete_reouvert  # noqa: E402
from suggestions import charger_fermes, deviner_categorie  # noqa: E402

depuis = _borne_fenetre(FENETRE_MOIS_DEFAUT)
fermes = charger_fermes(depuis)

# Part globale de chaque personne, TOUTES catégories confondues (y compris
# aucune-correspondance/ambigu — on regarde ici qui ferme des billets en
# général, pas seulement dans les catégories à mots-clés).
global_compte = Counter()
for it in fermes:
    if a_ete_reouvert(it):
        continue
    assignee = (it["fields"].get("assignee") or {}).get("displayName")
    if assignee:
        global_compte[assignee] += 1

total_global = sum(global_compte.values())
print(f"Total billets fermés créditables (rouverts exclus) : {total_global}\n")
print("Top 10 toutes catégories confondues :")
for nom, n in global_compte.most_common(10):
    pct = round(100 * n / total_global, 1)
    print(f"  {nom:30s} {n:5d}  ({pct} %)")

carmen = global_compte.get("Carmen Lecceses", 0)
pct_carmen = round(100 * carmen / total_global, 1) if total_global else 0
print(f"\nPart globale de Carmen Lecceses : {carmen}/{total_global} ({pct_carmen} %)")

# Détail par catégorie où elle apparaissait en tête (abend-traitement,
# acces-habilitation, tache-recurrente) pour comparaison directe.
par_categorie = Counter()
cat_total = Counter()
for it in fermes:
    if a_ete_reouvert(it):
        continue
    cat = deviner_categorie(it)
    if cat.startswith("ambigu:") or cat == "aucune-correspondance":
        continue
    assignee = (it["fields"].get("assignee") or {}).get("displayName")
    if not assignee:
        continue
    cat_total[cat] += 1
    if assignee == "Carmen Lecceses":
        par_categorie[cat] += 1

print("\nPart de Carmen par catégorie (pour comparaison à sa part globale) :")
for cat, total in sorted(cat_total.items()):
    n = par_categorie.get(cat, 0)
    pct = round(100 * n / total, 1) if total else 0
    print(f"  {cat:25s} {n:4d}/{total:<4d} ({pct} %)")

#!/usr/bin/env python3
"""
Diagnostic ponctuel : que contient PECARTES depuis la migration ?

Périmètre à l'étude : billets créés à partir du 2026-09-12 (date de la
migration), tous canaux d'entrée confondus (One Portail, JSD, dashboard).

Usage : python3 commande.py
"""
import sys
from collections import Counter

sys.path.insert(0, ".")
import analyser as a

DEPUIS = "2026-09-12"

tous = a.charger_billets()
depuis = [i for i in tous if (i["fields"].get("created") or "") >= DEPUIS]

print(f"{len(tous)} billets au total dans PECARTES")
print(f"{len(depuis)} créés depuis le {DEPUIS} (tous canaux)\n")

avec_rt = [i for i in depuis if i["fields"].get("customfield_11200")]
avec_label = [i for i in depuis if a._a_label_automatedcreation(i)]
sans_label_avec_rt = [i for i in avec_rt if not a._a_label_automatedcreation(i)]

print(f"  {len(avec_rt)} avec un Customer Request Type")
print(f"  {len(avec_label)} avec le label automatedcreation (One Portail direct)")
print(f"  {len(sans_label_avec_rt)} avec Request Type mais sans le label (JSD / dashboard ?)\n")

print("--- Statuts (tous les billets depuis la migration) ---")
for s, n in Counter((i["fields"].get("status") or {}).get("name", "?") for i in depuis).most_common():
    print(f"  {n:5d}  {s}")

print("\n--- Combinaisons de labels (top 15) ---")
c = Counter()
for i in depuis:
    c[tuple(sorted(i["fields"].get("labels") or [])) or ("(aucun)",)] += 1
for combo, n in c.most_common(15):
    print(f"  {n:5d}  {combo}")

fermes = [i for i in depuis if (i["fields"].get("status") or {}).get("name") in a.STATUTS_FERMES]
print(f"\n{len(fermes)} billets fermés depuis la migration")
print("(le plan vise ~200 pour la taxonomie, 120 pour le jeu d'évaluation)")

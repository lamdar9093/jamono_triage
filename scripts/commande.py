#!/usr/bin/env python3
"""
Régénère le rapport sur le nouveau périmètre (12 derniers mois, tous canaux),
puis l'instantané post-migration, pour comparer.

Usage : python3 commande.py
"""
import subprocess
import sys

for args in ([], ["--depuis-migration"]):
    print(f"\n{'=' * 60}\nanalyser.py {' '.join(args) or '(défaut : 12 mois)'}\n{'=' * 60}")
    subprocess.run([sys.executable, "analyser.py", *args], check=True)

#!/usr/bin/env python3
"""
Régénère le rapport (livrable 1) — un seul fichier.

L'ancien rapport post-migration (donnees-actuelles-migration.md) est
supprimé : 10 jours de données ne suffisent pas pour ses tableaux, et la
seule chose qu'il apportait (la comparaison des canaux avant/après) est
maintenant une section du rapport principal.

`analyser.py --depuis-migration` reste disponible pour le jour où le
système actuel aura assez d'historique.

Usage : python3 commande.py
"""
import subprocess
import sys
from pathlib import Path

ancien = Path(__file__).resolve().parent.parent / "rapports" / "donnees-actuelles-migration.md"
if ancien.exists():
    ancien.unlink()
    print(f"Supprimé : {ancien.name} (remplacé par une section du rapport principal)")

subprocess.run([sys.executable, "analyser.py"], check=True)

#!/usr/bin/env python3
"""
Génère le jeu d'évaluation (livrable 3) : 120 billets en 6 lots, tirés
uniquement dans le post-mise-en-run, hors billets vides ou de test.

Ne PAS ouvrir lots/verite-terrain.json avant d'avoir trié les lots —
c'est la réponse, elle fausserait la mesure.

Usage : python3 commande.py
"""
import subprocess
import sys

subprocess.run([sys.executable, "lots.py", "--n", "120", "--taille", "20"], check=True)

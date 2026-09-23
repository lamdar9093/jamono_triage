#!/usr/bin/env python3
"""
Diagnostic : les billets déjà répondus dans lots/sorties/lot-01.md et
lot-02.md (par Copilot) sont-ils toujours dans lots/verite-terrain.json ?

Contexte : lots.py a été relancé après le --complet, qui a changé l'ordre
des billets dans billets.json. Le tirage aléatoire (graine fixe, mais sur
un ordre d'entrée différent) a donc pu sélectionner un échantillon
différent (101 billets au lieu de 123). Si les clés déjà répondues n'y
sont plus, ce travail Copilot est orphelin : scorer.py les ignore
silencieusement (pas d'erreur, juste absent du compte).
"""
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOTS_DIR = BASE_DIR / "lots"
SORTIES_DIR = LOTS_DIR / "sorties"

verite_path = LOTS_DIR / "verite-terrain.json"
if not verite_path.exists():
    sys.exit(f"{verite_path} introuvable.")
verite = json.loads(verite_path.read_text(encoding="utf-8"))
verite_cles = set(verite.keys())
print(f"verite-terrain.json actuel : {len(verite_cles)} billets", file=sys.stderr)

CLE_RE = re.compile(r"^###\s*([A-Z]+-\d+)", re.MULTILINE)

if not SORTIES_DIR.exists():
    sys.exit(f"{SORTIES_DIR} introuvable.")

for chemin in sorted(SORTIES_DIR.glob("*.md")):
    cles_repondues = set(CLE_RE.findall(chemin.read_text(encoding="utf-8")))
    encore_presentes = cles_repondues & verite_cles
    perdues = cles_repondues - verite_cles
    print(f"\n{chemin.name} : {len(cles_repondues)} billets répondus — "
          f"{len(encore_presentes)} encore dans verite-terrain.json, "
          f"{len(perdues)} perdus (plus dans l'échantillon actuel)", file=sys.stderr)
    if perdues:
        print(f"  clés perdues : {sorted(perdues)}", file=sys.stderr)

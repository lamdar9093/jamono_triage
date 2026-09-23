#!/usr/bin/env python3
"""
Patch ponctuel : ajoute assignee_final à lots/verite-terrain.json existant,
SANS retirer un nouvel échantillon.

Pourquoi pas juste relancer lots.py ? Le tirage (echantillonner) dépend de
l'ordre des billets dans billets.json. Après le --complet de tout à l'heure,
cet ordre a changé — relancer lots.py régénérerait une sélection différente
et écraserait lot-01.md / lot-02.md, cassant la correspondance avec ce qui
est déjà collé dans lots/sorties/. Ce script ne touche qu'au JSON de vérité
terrain, pas aux fichiers lot-XX.md.

Idempotent : relancer plusieurs fois ne fait rien de plus après le premier
passage (saute les clés déjà patchées).
"""
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOTS_DIR = BASE_DIR / "lots"

verite_path = LOTS_DIR / "verite-terrain.json"
billets_path = DATA_DIR / "billets.json"

if not verite_path.exists():
    sys.exit(f"{verite_path} introuvable — lance lots.py d'abord (livrable 3).")
if not billets_path.exists():
    sys.exit(f"{billets_path} introuvable — lance extraire.py d'abord.")

verite = json.loads(verite_path.read_text(encoding="utf-8"))
issues = json.loads(billets_path.read_text(encoding="utf-8"))["issues"]
par_cle = {it["key"]: it for it in issues}

deja_patches = manquants = patches = 0
for cle, v in verite.items():
    if "assignee_final" in v:
        deja_patches += 1
        continue
    it = par_cle.get(cle)
    if not it:
        manquants += 1
        v["assignee_final"] = None
        continue
    v["assignee_final"] = (it["fields"].get("assignee") or {}).get("displayName")
    patches += 1

verite_path.write_text(json.dumps(verite, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"{len(verite)} billets dans {verite_path.name} — {patches} patchés, "
      f"{deja_patches} déjà à jour, {manquants} introuvables dans billets.json", file=sys.stderr)

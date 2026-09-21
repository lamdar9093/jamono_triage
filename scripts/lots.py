#!/usr/bin/env python3
"""
lots.py — Prépare des lots de billets fermés pour la boucle Copilot

Chaque lot est un fichier markdown de N billets : titre + description
seuls (ce qui était connu à l'ouverture), sans la résolution ni la
catégorie réelle — c'est ce que Copilot doit deviner. La vérité terrain
va dans un fichier séparé, jamais dans le lot lui-même.

Usage :
    python scripts/lots.py --n 120 --taille 20
"""
import argparse
import json
import random
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOTS_DIR = BASE_DIR / "lots"

STATUTS_FERMES = {"Closed", "Done", "Résolu", "Resolved"}


def charger_fermes() -> list:
    fichier = DATA_DIR / "billets-anon.json"
    if not fichier.exists():
        fichier = DATA_DIR / "billets.json"
    if not fichier.exists():
        sys.exit("Aucune donnée — lance extraire.py (et anonymiser.py) d'abord.")
    issues = json.loads(fichier.read_text(encoding="utf-8"))["issues"]
    return [it for it in issues if (it["fields"].get("status") or {}).get("name") in STATUTS_FERMES]


def echantillonner(fermes: list, n: int, graine: int = 42) -> list:
    """Échantillonne en couvrant les priorités présentes, pas au hasard pur."""
    random.seed(graine)
    par_priorite = {}
    for it in fermes:
        prio = (it["fields"].get("priority") or {}).get("name", "?")
        par_priorite.setdefault(prio, []).append(it)

    n_priorites = len(par_priorite) or 1
    par_groupe = max(1, n // n_priorites)
    selection = []
    for groupe in par_priorite.values():
        random.shuffle(groupe)
        selection.extend(groupe[:par_groupe])
    random.shuffle(selection)
    return selection[:n]


def ecrire_lots(selection: list, taille: int) -> None:
    LOTS_DIR.mkdir(exist_ok=True)
    (LOTS_DIR / "sorties").mkdir(exist_ok=True)
    verite_terrain = {}

    for i in range(0, len(selection), taille):
        lot = selection[i:i + taille]
        numero = i // taille + 1
        L = [f"# Lot {numero:02d} — {len(lot)} billets", ""]
        for it in lot:
            f = it["fields"]
            L.append(f"## {it['key']}")
            L.append("")
            L.append(f"**Titre :** {f.get('summary', '')}")
            L.append("")
            L.append(f"**Description :** {f.get('description') or '(vide)'}")
            L.append("")
            L.append("---")
            L.append("")

            verite_terrain[it["key"]] = {
                "priorite_finale": (f.get("priority") or {}).get("name", "?"),
                "labels": f.get("labels") or [],
                # L'équipe résolutrice réelle doit venir de l'assignation
                # finale (via changelog), pas de la première — à compléter
                # une fois la taxonomie d'équipes stabilisée.
            }

        chemin = LOTS_DIR / f"lot-{numero:02d}.md"
        chemin.write_text("\n".join(L), encoding="utf-8")
        print(f"  {chemin.name} — {len(lot)} billets", file=sys.stderr)

    (LOTS_DIR / "verite-terrain.json").write_text(
        json.dumps(verite_terrain, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Vérité terrain → {LOTS_DIR / 'verite-terrain.json'} (ne pas ouvrir avant de trier !)", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=120, help="nombre total de billets à échantillonner")
    ap.add_argument("--taille", type=int, default=20, help="billets par lot")
    args = ap.parse_args()

    fermes = charger_fermes()
    print(f"{len(fermes)} billets fermés disponibles", file=sys.stderr)
    selection = echantillonner(fermes, args.n)
    ecrire_lots(selection, args.taille)


if __name__ == "__main__":
    main()

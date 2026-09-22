#!/usr/bin/env python3
"""
lots.py — Prépare des lots de billets fermés pour la boucle Copilot

Chaque lot est un fichier markdown de N billets : titre + description
seuls (ce qui était connu à l'ouverture), sans la résolution ni la
catégorie réelle — c'est ce que Copilot doit deviner. La vérité terrain
va dans un fichier séparé, jamais dans le lot lui-même.

Usage :
    python scripts/lots.py --n 120 --taille 20
    python scripts/lots.py --n 200 --sortie lots/taxonomie  # lecture pour la taxonomie,
                                                              # sans écraser les lots d'évaluation
"""
import argparse
import json
import random
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Doit rester identique à STATUTS_FERMES dans analyser.py — deux copies
# divergentes ont déjà causé un sous-comptage silencieux une fois (Rejected
# manquant ici alors qu'ajouté là-bas).
STATUTS_FERMES = {"Closed", "Done", "Résolu", "Resolved", "Rejected"}


def charger_fermes() -> list:
    fichier_anon = DATA_DIR / "billets-anon.json"
    fichier_brut = DATA_DIR / "billets.json"
    fichier = fichier_anon if fichier_anon.exists() else fichier_brut
    if not fichier.exists():
        sys.exit("Aucune donnée — lance extraire.py (et anonymiser.py) d'abord.")

    # Même garde-fou que analyser.py : un anon plus vieux que le brut vient
    # d'une extraction précédente et donnerait un échantillon incomplet
    # sans rien signaler.
    if fichier is fichier_anon and fichier_brut.exists():
        if fichier_anon.stat().st_mtime < fichier_brut.stat().st_mtime:
            sys.exit(
                "billets-anon.json est plus ancien que billets.json — il date d'une\n"
                "extraction précédente. Relance : python scripts/anonymiser.py"
            )

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


def ecrire_lots(selection: list, taille: int, sortie: Path) -> None:
    sortie.mkdir(parents=True, exist_ok=True)
    (sortie / "sorties").mkdir(exist_ok=True)
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

        chemin = sortie / f"lot-{numero:02d}.md"
        chemin.write_text("\n".join(L), encoding="utf-8")
        print(f"  {chemin.name} — {len(lot)} billets", file=sys.stderr)

    (sortie / "verite-terrain.json").write_text(
        json.dumps(verite_terrain, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Vérité terrain → {sortie / 'verite-terrain.json'} (ne pas ouvrir avant de trier !)", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=120, help="nombre total de billets à échantillonner")
    ap.add_argument("--taille", type=int, default=20, help="billets par lot")
    ap.add_argument("--sortie", type=Path, default=BASE_DIR / "lots",
                     help="dossier de sortie — défaut lots/ (livrable 3, boucle Copilot). "
                          "Utiliser un sous-dossier distinct (ex. lots/taxonomie) pour toute "
                          "autre lecture, sous peine d'écraser les lots d'évaluation.")
    args = ap.parse_args()

    fermes = charger_fermes()
    print(f"{len(fermes)} billets fermés disponibles", file=sys.stderr)
    selection = echantillonner(fermes, args.n)
    ecrire_lots(selection, args.taille, args.sortie)


if __name__ == "__main__":
    main()

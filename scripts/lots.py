#!/usr/bin/env python3
"""
lots.py — Prépare des lots de billets fermés pour la boucle Copilot

Chaque lot est un fichier markdown de N billets : titre + description
seuls (ce qui était connu à l'ouverture), sans la résolution ni la
catégorie réelle — c'est ce que Copilot doit deviner. La vérité terrain
va dans un fichier séparé, jamais dans le lot lui-même.

Par défaut, ne tire que dans les billets postérieurs à la mise en run
(voir MIGRATION dans analyser.py) — c'est le périmètre sur lequel l'outil
travaille, donc le seul où un score veut dire quelque chose.

Usage :
    python scripts/lots.py --n 120 --taille 20             # jeu d'évaluation (livrable 3)
    python scripts/lots.py --mois 12 --n 200 --sortie lots/taxonomie
    python scripts/lots.py --tous --n 200 --sortie lots/taxonomie
"""
import argparse
import json
import random
import sys
from pathlib import Path

# Les constantes de périmètre viennent d'analyser.py plutôt que d'être
# recopiées : deux copies divergentes de STATUTS_FERMES ont déjà causé un
# sous-comptage silencieux (Rejected manquant ici, présent là-bas).
from analyser import (
    MIGRATION,
    STATUTS_FERMES,
    FENETRE_MOIS_DEFAUT,
    _borne_fenetre,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Titre + description sous ce seuil = billet vide ou de test. Même valeur
# que billets_vides_suspectes() dans analyser.py. Ces billets ne peuvent
# pas être triés — ni par Copilot, ni par un humain — donc ils n'ont rien
# à faire dans un jeu d'évaluation.
SEUIL_BRUIT_TEST = 15


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


def _est_bruit_test(issue) -> bool:
    f = issue["fields"]
    return len(f"{f.get('summary') or ''} {f.get('description') or ''}".strip()) < SEUIL_BRUIT_TEST


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
    ap.add_argument("--mois", type=int, metavar="N",
                     help=f"élargit à N mois au lieu du seul post-run "
                          f"(ex. --mois {FENETRE_MOIS_DEFAUT} pour la taxonomie)")
    ap.add_argument("--tous", action="store_true",
                     help="tout l'historique, sans borne de date")
    args = ap.parse_args()

    fermes = charger_fermes()
    total = len(fermes)

    if args.tous:
        depuis, libelle = "", "tout l'historique"
    elif args.mois:
        depuis, libelle = _borne_fenetre(args.mois), f"{args.mois} derniers mois"
    else:
        depuis, libelle = MIGRATION, f"depuis la mise en run ({MIGRATION})"

    if depuis:
        fermes = [it for it in fermes if (it["fields"].get("created") or "") >= depuis]

    avant_bruit = len(fermes)
    fermes = [it for it in fermes if not _est_bruit_test(it)]
    ecartes = avant_bruit - len(fermes)

    print(f"Périmètre : {libelle}", file=sys.stderr)
    print(f"  {total} billets fermés au total → {avant_bruit} dans le périmètre", file=sys.stderr)
    if ecartes:
        print(f"  {ecartes} écartés (vides ou de test, < {SEUIL_BRUIT_TEST} caractères)", file=sys.stderr)
    print(f"  {len(fermes)} exploitables", file=sys.stderr)

    if len(fermes) < args.n:
        print(f"\n  ATTENTION : {args.n} demandés, seulement {len(fermes)} disponibles.",
              file=sys.stderr)
        print(f"  Les lots seront produits avec ce qu'il y a. Pour en avoir plus :",
              file=sys.stderr)
        print(f"  élargir la fenêtre (--mois N), ou attendre que le volume monte.\n",
              file=sys.stderr)

    selection = echantillonner(fermes, args.n)
    ecrire_lots(selection, args.taille, args.sortie)


if __name__ == "__main__":
    main()

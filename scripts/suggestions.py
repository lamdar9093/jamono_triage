#!/usr/bin/env python3
"""
suggestions.py — Qui a résolu quoi, par catégorie (source de PERSONNE_SUGGEREE)

Catégorise les billets fermés par recherche de mots-clés (les "Signaux /
codes reconnus" déjà écrits dans knowledge/categories.md), sans appel à
Copilot — impossible d'en passer des milliers un par un manuellement (le
plan limite l'usage manuel de Copilot à ~120 billets). Moins précis qu'une
vraie lecture, mais transparent : chaque catégorie devinée est traçable au
mot-clé qui l'a déclenchée, et rien n'est deviné pour les catégories qui
n'ont pas encore de signal écrit dans categories.md — ces billets restent
"aucune-correspondance" plutôt que d'inventer un rattachement.

Écrit data/personnes.md — JAMAIS knowledge/, parce que ce fichier contient
de vrais noms liés à des volumes individuels. data/ ne quitte jamais la
machine (voir .gitignore) ; knowledge/ est versionné et publié sur GitHub.
Utilise donc billets.json (noms réels), pas billets-anon.json — ce fichier
n'est utile à Copilot que s'il contient de vrais noms, et il reste local.

Usage :
    python scripts/suggestions.py                # 12 derniers mois (défaut)
    python scripts/suggestions.py --mois 24
    python scripts/suggestions.py --tous
"""
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyser import STATUTS_FERMES, FENETRE_MOIS_DEFAUT, _borne_fenetre  # noqa: E402
from lots import SEUIL_BRUIT_TEST  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Signaux tirés de knowledge/categories.md, section "Signaux / codes
# reconnus" de chaque catégorie — à tenir à jour si ce fichier change.
# Recherche insensible à la casse, sur titre + description concaténés.
# Catégories absentes d'ici : categories.md n'a pas encore de signal
# observable pour elles (rapport-errone, decommissionnement,
# bris-confidentialite, loyaute-points, disponibilite-service,
# demande-information, changement-implementation, conformite-validation)
# — volontairement non devinées, pas une omission.
CATEGORIE_SIGNAUX = {
    "abend-traitement": ["abend", "warning client", "jcl"],
    "refus-transaction": ["bc01 failed", "code de refus", "refus", "declined", "refused"],
    "fichier-non-reçu": ["sgci", "mft", "ctrl-m", "non reçu", "participant file"],
    "acces-habilitation": ["réinitialiser", "débloquer", "logon"],
    "tache-recurrente": ["récurrent :", "récurrent:"],
    "saas": ["brim", "powercard", "pwc"],
    "limite-solde": ["limite temporaire", "plafond atteint"],
}


def _texte(issue) -> str:
    f = issue["fields"]
    return f"{f.get('summary') or ''} {f.get('description') or ''}".lower()


def _est_bruit_test(issue) -> bool:
    f = issue["fields"]
    return len(f"{f.get('summary') or ''} {f.get('description') or ''}".strip()) < SEUIL_BRUIT_TEST


def deviner_categorie(issue) -> str:
    """Premier match l'emporte. Plusieurs catégories qui matchent en même
    temps = signal ambigu, à part — mieux vaut le voir que le cacher."""
    texte = _texte(issue)
    trouvees = [cat for cat, mots in CATEGORIE_SIGNAUX.items() if any(m in texte for m in mots)]
    if not trouvees:
        return "aucune-correspondance"
    if len(trouvees) > 1:
        return "ambigu:" + "+".join(sorted(trouvees))
    return trouvees[0]


def charger_fermes(depuis: str) -> list:
    fichier = DATA_DIR / "billets.json"  # noms réels, pas billets-anon.json
    if not fichier.exists():
        sys.exit("data/billets.json introuvable — lance extraire.py d'abord.")
    import json
    issues = json.loads(fichier.read_text(encoding="utf-8"))["issues"]
    fermes = [it for it in issues if (it["fields"].get("status") or {}).get("name") in STATUTS_FERMES]
    if depuis:
        fermes = [it for it in fermes if (it["fields"].get("created") or "") >= depuis]
    return [it for it in fermes if not _est_bruit_test(it)]


def calculer(fermes: list) -> dict:
    par_categorie = defaultdict(Counter)
    repartition = Counter()
    for it in fermes:
        cat = deviner_categorie(it)
        repartition[cat] += 1
        assignee = (it["fields"].get("assignee") or {}).get("displayName")
        if assignee and not cat.startswith("ambigu:") and cat != "aucune-correspondance":
            par_categorie[cat][assignee] += 1
    return par_categorie, repartition


def ecrire(par_categorie: dict, repartition: Counter, total: int, libelle: str) -> Path:
    L = ["# Qui résout quoi, par catégorie", ""]
    L.append("**Généré automatiquement par `scripts/suggestions.py` — ne pas éditer à la "
             "main, relancer le script pour actualiser.**")
    L.append("")
    L.append(f"Périmètre : {libelle} — {total} billets fermés (bruit-test exclu).")
    L.append("")
    n_classes = sum(n for cat, n in repartition.items()
                     if cat != "aucune-correspondance" and not cat.startswith("ambigu:"))
    pct = round(100 * n_classes / total, 1) if total else 0
    L.append(f"**{n_classes}/{total} ({pct} %) rattachés à une catégorie** par mot-clé — "
             f"le reste (`aucune-correspondance` ou ambigu) n'a pas de statistique ci-dessous. "
             f"Catégorisation approximative (mots-clés), pas une vraie lecture : à traiter "
             f"comme une tendance, pas une certitude.")
    L.append("")

    for cat in sorted(par_categorie):
        compte = par_categorie[cat]
        total_cat = sum(compte.values())
        L.append(f"## {cat}")
        L.append("")
        L.append(f"{total_cat} billets rattachés (mots-clés : "
                  f"{', '.join(CATEGORIE_SIGNAUX.get(cat, []))}).")
        L.append("")
        for nom, n in compte.most_common(5):
            pct_p = round(100 * n / total_cat, 1)
            L.append(f"- **{nom}** — {n}/{total_cat} billets ({pct_p} %)")
        L.append("")

    out = DATA_DIR / "personnes.md"
    out.write_text("\n".join(L), encoding="utf-8")
    return out


def main() -> None:
    if "--tous" in sys.argv:
        depuis, libelle = "", "tout l'historique"
    else:
        mois = FENETRE_MOIS_DEFAUT
        if "--mois" in sys.argv:
            try:
                mois = int(sys.argv[sys.argv.index("--mois") + 1])
            except (IndexError, ValueError):
                sys.exit("--mois attend un nombre, ex. --mois 24")
        depuis, libelle = _borne_fenetre(mois), f"{mois} derniers mois"

    fermes = charger_fermes(depuis)
    par_categorie, repartition = calculer(fermes)

    print(f"Périmètre : {libelle} — {len(fermes)} billets fermés (bruit-test exclu)", file=sys.stderr)
    for cat, n in repartition.most_common():
        print(f"    {n:5d}  {cat}", file=sys.stderr)

    out = ecrire(par_categorie, repartition, len(fermes), libelle)
    print(f"\nÉcrit → {out} (local, jamais poussé sur GitHub)", file=sys.stderr)


if __name__ == "__main__":
    main()

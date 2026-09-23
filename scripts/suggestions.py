#!/usr/bin/env python3
"""
suggestions.py — Qui résout quoi, et quelle équipe, par catégorie

Deux sources différentes pour deux besoins différents :
- PERSONNE_SUGGEREE : rien dans Jira ne donne directement "qui devrait
  traiter ce type de billet" — reconstruit en catégorisant les billets
  fermés par mots-clés (les "Signaux / codes reconnus" déjà écrits dans
  knowledge/categories.md), sans appel à Copilot. Impossible d'en passer
  des milliers un par un manuellement (le plan limite l'usage manuel de
  Copilot à ~120 billets). Moins précis qu'une vraie lecture, mais
  transparent : chaque catégorie devinée est traçable au mot-clé qui l'a
  déclenchée, et rien n'est deviné pour les catégories qui n'ont pas
  encore de signal écrit dans categories.md.
- EQUIPE : un vrai champ Jira (Team, customfield_11600) le donne
  directement — pas besoin de deviner. "saas" avait été mis à tort dans
  CATEGORIE_SIGNAUX (une équipe, "SaaS - PE Cartes", prise pour un type
  de problème) avant que ce champ soit identifié ; retiré depuis.

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
from analyser import (  # noqa: E402
    STATUTS_FERMES, CHAMP_TEAM, FENETRE_MOIS_DEFAUT,
    valeur_champ, _borne_fenetre, a_ete_reouvert,
)
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
    "limite-solde": ["limite temporaire", "plafond atteint"],
}

# Sous ce nombre de billets dans la catégorie, un ratio élevé (ratio
# catégorie/global) peut venir du hasard (ex. 1/2 billets = 50%, mais ça ne
# prouve rien) — pas assez de billets pour distinguer un vrai signal d'un
# coup de dés. Seuil arbitraire, pas calculé statistiquement (pas de test
# de significativité ici) — juste pour ne pas afficher une fausse confiance
# sur un petit échantillon. À ajuster si l'expérience montre qu'il est mal
# calibré.
SEUIL_ECHANTILLON_SPECIALISATION = 10
RATIO_SPECIALISATION = 1.5


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
    par_categorie = defaultdict(Counter)  # catégorie -> {personne: n}
    equipes_categorie = defaultdict(Counter)  # catégorie -> {équipe: n}
    repartition = Counter()
    # Part globale de chaque personne, TOUTES catégories confondues (y compris
    # aucune-correspondance/ambigu) — sert de référence pour distinguer une
    # vraie spécialisation d'un simple volume élevé (ex. Carmen Leccese ferme
    # 35 % de tous les billets, donc elle ressort #1 dans presque toutes les
    # catégories mécaniquement, pas forcément parce qu'elle s'y spécialise).
    global_compte = Counter()
    reouverts_exclus = 0
    for it in fermes:
        cat = deviner_categorie(it)
        repartition[cat] += 1

        # L'équipe vient d'un vrai champ Jira, pas d'un mot-clé deviné — pas
        # besoin d'attendre une catégorie non-ambiguë pour la compter. Un
        # billet rouvert n'a toujours pas été correctement traité, donc pas
        # crédité non plus ici (même règle que pour la personne).
        if not cat.startswith("ambigu:") and cat != "aucune-correspondance" and not a_ete_reouvert(it):
            equipe = valeur_champ(it["fields"].get(CHAMP_TEAM))
            if equipe:
                equipes_categorie[cat][equipe] += 1

        assignee = (it["fields"].get("assignee") or {}).get("displayName")
        if not assignee:
            continue
        # Un billet rouvert après fermeture n'a pas été correctement résolu —
        # ne pas créditer cette "résolution" à qui l'avait fermé.
        if a_ete_reouvert(it):
            if not cat.startswith("ambigu:") and cat != "aucune-correspondance":
                reouverts_exclus += 1
            continue

        global_compte[assignee] += 1
        if cat.startswith("ambigu:") or cat == "aucune-correspondance":
            continue
        par_categorie[cat][assignee] += 1
    return par_categorie, equipes_categorie, repartition, reouverts_exclus, global_compte


def ecrire(par_categorie: dict, equipes_categorie: dict, repartition: Counter, total: int,
           libelle: str, reouverts_exclus: int, global_compte: Counter) -> Path:
    L = ["# Qui résout quoi, et quelle équipe, par catégorie", ""]
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
             f"comme une tendance, pas une certitude. **Ça ne s'applique qu'à `PERSONNE_SUGGEREE` "
             f"ci-dessous — `EQUIPE` vient d'un vrai champ Jira (Team), fiable indépendamment "
             f"de cette catégorisation approximative.**")
    L.append("")
    L.append(f"**{reouverts_exclus} billet(s) exclu(s) du comptage** parce que rouverts après "
             f"fermeture — une réouverture veut dire que ce n'était pas vraiment résolu, donc "
             f"ça ne compte pas comme une résolution réussie pour qui l'avait fermé (ni pour la "
             f"personne, ni pour l'équipe).")
    L.append("")
    total_global = sum(global_compte.values())
    L.append(f"**Sous « Personne », chaque nom affiche sa part dans la catégorie, sa part "
             f"globale ({total_global} billets, toutes catégories confondues, rouverts "
             f"exclus), et un ratio des deux (×N).** Un ratio proche de ×1 veut dire que la "
             f"personne ferme beaucoup de billets en général (ex. un rôle de triage qui reçoit "
             f"tout par défaut) — pas un signal de spécialisation pour cette catégorie "
             f"précise, même si son volume brut est le plus élevé. Un ratio ≥ ×{RATIO_SPECIALISATION} "
             f"sur au moins {SEUIL_ECHANTILLON_SPECIALISATION} billets est marqué « spécialisation "
             f"apparente » — **c'est ce nom-là qu'il faut préférer pour `PERSONNE_SUGGEREE`, pas "
             f"forcément celui en tête par volume brut.** En dessous de "
             f"{SEUIL_ECHANTILLON_SPECIALISATION} billets, un ratio élevé est marqué « signal "
             f"faible » — peut venir du hasard sur un petit échantillon, pas une vraie preuve. "
             f"**Seuils choisis à l'instinct, pas validés statistiquement** — `scorer.py` "
             f"compare maintenant `PERSONNE_SUGGEREE` à l'assigné réel pour vérifier si ce "
             f"choix aide vraiment (voir evals/resultats.md une fois quelques lots notés).")
    L.append("")

    for cat in sorted(set(par_categorie) | set(equipes_categorie)):
        L.append(f"## {cat}")
        L.append("")

        equipes = equipes_categorie.get(cat)
        if equipes:
            total_eq = sum(equipes.values())
            L.append(f"**Équipe** ({total_eq} billets, champ Team réel) :")
            L.append("")
            for nom, n in equipes.most_common(5):
                pct_e = round(100 * n / total_eq, 1)
                L.append(f"- **{nom}** — {n}/{total_eq} billets ({pct_e} %)")
            L.append("")

        compte = par_categorie.get(cat)
        if compte:
            total_cat = sum(compte.values())
            L.append(f"**Personne** ({total_cat} billets rattachés par mots-clés : "
                      f"{', '.join(CATEGORIE_SIGNAUX.get(cat, []))}) :")
            L.append("")
            for nom, n in compte.most_common(5):
                part_cat = n / total_cat
                part_globale = (global_compte.get(nom, 0) / total_global) if total_global else 0.0
                pct_p = round(100 * part_cat, 1)
                pct_g = round(100 * part_globale, 1)
                lift = (part_cat / part_globale) if part_globale else None
                lift_txt = f"×{round(lift, 1)}" if lift is not None else "×?"
                if lift and lift >= RATIO_SPECIALISATION and n >= SEUIL_ECHANTILLON_SPECIALISATION:
                    marque = " — **spécialisation apparente**"
                elif lift and lift >= RATIO_SPECIALISATION:
                    marque = f" — signal faible (échantillon réduit, {n} billets)"
                else:
                    marque = ""
                L.append(f"- **{nom}** — {n}/{total_cat} billets ({pct_p} % de la catégorie ; "
                         f"{pct_g} % de son volume global ; {lift_txt}{marque})")
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
    par_categorie, equipes_categorie, repartition, reouverts_exclus, global_compte = calculer(fermes)

    print(f"Périmètre : {libelle} — {len(fermes)} billets fermés (bruit-test exclu)", file=sys.stderr)
    for cat, n in repartition.most_common():
        print(f"    {n:5d}  {cat}", file=sys.stderr)
    print(f"  {reouverts_exclus} exclus du comptage (rouverts après fermeture)", file=sys.stderr)
    sans_equipe = sum(1 for it in fermes if not valeur_champ(it["fields"].get(CHAMP_TEAM)))
    print(f"  {sans_equipe} sans champ Team rempli", file=sys.stderr)
    total_global = sum(global_compte.values())
    top = global_compte.most_common(1)
    if top:
        nom, n = top[0]
        print(f"  {nom} ferme {n}/{total_global} ({round(100*n/total_global, 1)} %) de tous "
              f"les billets crédités, toutes catégories confondues", file=sys.stderr)

    out = ecrire(par_categorie, equipes_categorie, repartition, len(fermes), libelle,
                 reouverts_exclus, global_compte)
    print(f"\nÉcrit → {out} (local, jamais poussé sur GitHub)", file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
analyser.py — Rapport « ce que vos données disent déjà » (livrable 1)

Aucune IA ici. Lit data/billets-anon.json (ou billets.json si l'anonymisé
n'existe pas), écrit rapports/donnees-actuelles.md.

Hypothèses à ajuster si ton instance Jira utilise d'autres libellés que
ceux vus dans les tableaux de bord actuels — voir STATUTS_* ci-dessous.

Usage :
    python scripts/analyser.py                   # 12 derniers mois (défaut)
    python scripts/analyser.py --mois 24         # autre fenêtre de temps
    python scripts/analyser.py --depuis-migration # seulement depuis le 2026-09-12
    python scripts/analyser.py --tous            # tout l'historique, sans fenêtre
"""
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAPPORTS_DIR = BASE_DIR / "rapports"

# Ajuster ces libellés à ceux réellement utilisés dans le projet PECARTES.
STATUTS_ATTENTE_TIERS = {"Waiting for support", "Waiting for delivery"}
STATUTS_FERMES = {"Closed", "Done", "Résolu", "Resolved", "Rejected"}

# Périmètre — voir la décision du 2026-09-22 dans plan.md.
#
# Le rapport ne filtre PAS par canal d'entrée. Les trois canaux (One Portail,
# JSD, dashboard PECARTES) font tous partie du travail de l'équipe : tout ce
# qui tourne pour elle est dans PECARTES. Deux tentatives précédentes de
# filtrer par label ou par Request Type se sont révélées fausses — le canal
# est une information à afficher, pas un critère de périmètre.
#
# Ce qui borne le rapport est donc une fenêtre de TEMPS, pas un filtre de
# contenu : assez de profondeur pour voir des tendances, sans remonter à
# 2016 (le tableau hebdomadaire deviendrait illisible).
FENETRE_MOIS_DEFAUT = 12

# Bascule vers le système actuel. Avant cette date, autre monde : autres
# pratiques, autres canaux. Marquée dans le rapport pour que le lecteur voie
# où commence le système en place, et sert de périmètre à l'outil de triage
# (--depuis-migration), qui lui ne travaille que sur l'après.
MIGRATION = "2026-09-12"

# Canaux d'entrée — affichés dans le rapport, jamais utilisés pour filtrer.
LABEL_AUTOMATEDCREATION = "automatedcreation"  # One Portail, posé à la création
CHAMP_REQUEST_TYPE = "customfield_11200"  # Customer Request Type (JSD / portail)

CHAMP_EXTERNAL_ID = "customfield_17800"  # External issue ID


def charger_billets() -> list:
    fichier_anon = DATA_DIR / "billets-anon.json"
    fichier_brut = DATA_DIR / "billets.json"
    fichier = fichier_anon if fichier_anon.exists() else fichier_brut
    if not fichier.exists():
        sys.exit("Aucune donnée trouvée — lance d'abord extraire.py (et anonymiser.py).")

    # Un billets-anon.json plus vieux que billets.json vient d'une extraction
    # précédente : il lui manque les champs ajoutés depuis, et l'analyse sort
    # silencieusement des zéros. On refuse plutôt que de produire un faux rapport.
    if fichier is fichier_anon and fichier_brut.exists():
        if fichier_anon.stat().st_mtime < fichier_brut.stat().st_mtime:
            sys.exit(
                "billets-anon.json est plus ancien que billets.json — il date d'une\n"
                "extraction précédente et n'a pas les champs récents.\n"
                "Relance : python scripts/anonymiser.py"
            )

    print(f"Lecture de {fichier.name}", file=sys.stderr)
    return json.loads(fichier.read_text(encoding="utf-8"))["issues"]


def _parse_dt(s):
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _semaine(dt) -> str:
    iso = dt.isocalendar()
    return f"{iso[0]}-S{iso[1]:02d}"


def _heures_entre(a, b) -> float:
    return (b - a).total_seconds() / 3600


def _p90(valeurs) -> float:
    if not valeurs:
        return 0.0
    s = sorted(valeurs)
    idx = max(0, int(round(0.9 * (len(s) - 1))))
    return s[idx]


def _mediane(valeurs) -> float:
    return statistics.median(valeurs) if valeurs else 0.0


def _fmt_h(h: float) -> str:
    return f"{h:.1f} h" if h < 48 else f"{h / 24:.1f} j"


class Analyse:
    def __init__(self, issues):
        self.issues = issues
        self.maintenant = datetime.now(timezone.utc)

    def creation_vs_fermeture(self):
        crees, fermes = Counter(), Counter()
        for it in self.issues:
            f = it["fields"]
            c = _parse_dt(f.get("created"))
            if c:
                crees[_semaine(c)] += 1
            if (f.get("status") or {}).get("name") in STATUTS_FERMES:
                r = _parse_dt(f.get("resolutiondate")) or _parse_dt(f.get("updated"))
                if r:
                    fermes[_semaine(r)] += 1
        semaines = sorted(set(crees) | set(fermes))
        deficit, deficits = 0, {}
        for s in semaines:
            deficit += crees.get(s, 0) - fermes.get(s, 0)
            deficits[s] = deficit
        return crees, fermes, deficits

    def semaines_atypiques(self, crees, fermes, seuil: float = 3.0) -> set:
        """Semaines dont le volume créé ou fermé dépasse `seuil` fois la
        médiane des autres semaines — signale un événement ponctuel (migration,
        campagne, incident), pas le rythme normal du triage. Ne dit jamais la
        cause : à confirmer par un humain avant de présenter le rapport."""
        semaines = sorted(set(crees) | set(fermes))
        if len(semaines) < 4:
            return set()
        med_c = _mediane([crees.get(s, 0) for s in semaines]) or 1
        med_f = _mediane([fermes.get(s, 0) for s in semaines]) or 1
        return {
            s for s in semaines
            if crees.get(s, 0) > seuil * med_c or fermes.get(s, 0) > seuil * med_f
        }

    def temps_attente_tiers(self, issue) -> float:
        """Heures cumulées passées dans un statut d'attente tiers, via changelog."""
        histories = issue.get("changelog", {}).get("histories", [])
        entrees = []
        for h in histories:
            dt = _parse_dt(h.get("created"))
            if not dt:
                continue
            for item in h.get("items", []):
                if item.get("field") == "status":
                    entrees.append((dt, item.get("toString")))
        entrees.sort(key=lambda t: t[0])

        total, depuis = 0.0, None
        for dt, to in entrees:
            if to in STATUTS_ATTENTE_TIERS and depuis is None:
                depuis = dt
            elif to not in STATUTS_ATTENTE_TIERS and depuis is not None:
                total += _heures_entre(depuis, dt)
                depuis = None
        if depuis is not None:
            fin = _parse_dt(issue["fields"].get("resolutiondate")) or self.maintenant
            total += _heures_entre(depuis, fin)
        return total

    def delais(self):
        par_priorite, par_categorie = defaultdict(list), defaultdict(list)
        for it in self.issues:
            f = it["fields"]
            if (f.get("status") or {}).get("name") not in STATUTS_FERMES:
                continue
            c, r = _parse_dt(f.get("created")), _parse_dt(f.get("resolutiondate"))
            if not (c and r):
                continue
            total_h = _heures_entre(c, r)
            attente_h = self.temps_attente_tiers(it)
            net_h = max(0.0, total_h - attente_h)

            priorite = (f.get("priority") or {}).get("name", "?")
            par_priorite[priorite].append((total_h, net_h))

            for lbl in (f.get("labels") or ["(sans étiquette)"]):
                par_categorie[lbl].append((total_h, net_h))
        return {"priorite": par_priorite, "categorie": par_categorie}

    def billets_vides_suspectes(self, seuil_caracteres: int = 15) -> list:
        """Titre + description combinés anormalement courts — candidats
        "bruit-test" (billet de test, vide), pas un verdict. Seuil bas
        volontairement : un vrai billet, même mal rédigé, dépasse presque
        toujours ce seuil ; en dessous, c'est un remplissage minimal plutôt
        qu'un vrai signalement. Ne filtre rien automatiquement — voir
        knowledge/categories.md, catégorie bruit-test."""
        candidats = []
        for it in self.issues:
            f = it["fields"]
            texte = f"{f.get('summary') or ''} {f.get('description') or ''}".strip()
            if len(texte) < seuil_caracteres:
                candidats.append((it["key"], texte or "(vide)"))
        return candidats

    def doublons_suspectes(self, fenetre_jours: int = 3):
        """Heuristique : même signaleur, création rapprochée, résumés proches
        (indice de Jaccard). Liste de candidats à relire — pas un verdict."""
        candidats = []
        par_signaleur = defaultdict(list)
        for it in self.issues:
            f = it["fields"]
            rep = (f.get("reporter") or {}).get("displayName", "?")
            c = _parse_dt(f.get("created"))
            if c:
                par_signaleur[rep].append((it["key"], c, (f.get("summary") or "").lower()))

        for tickets in par_signaleur.values():
            tickets.sort(key=lambda t: t[1])
            for i in range(len(tickets)):
                for j in range(i + 1, len(tickets)):
                    k1, c1, s1 = tickets[i]
                    k2, c2, s2 = tickets[j]
                    if (c2 - c1).days > fenetre_jours:
                        break
                    m1, m2 = set(s1.split()), set(s2.split())
                    if not m1 or not m2:
                        continue
                    if len(m1 & m2) / len(m1 | m2) > 0.4:
                        candidats.append((k1, k2))
        return candidats

    def non_assignes(self):
        res = []
        for it in self.issues:
            f = it["fields"]
            if (f.get("status") or {}).get("name") in STATUTS_FERMES:
                continue
            if f.get("assignee") is None:
                c = _parse_dt(f.get("created"))
                if c:
                    res.append((it["key"], _heures_entre(c, self.maintenant)))
        return sorted(res, key=lambda t: -t[1])

    def reference_actuelle(self):
        """Les trois chiffres calculés avant toute IA — la barre à battre."""
        total = reaffectes = reouverts = priorite_changee = 0
        for it in self.issues:
            f = it["fields"]
            if (f.get("status") or {}).get("name") not in STATUTS_FERMES:
                continue
            total += 1
            n_assignee = n_priorite = n_reopen = 0
            ferme_vu = False
            for h in it.get("changelog", {}).get("histories", []):
                for item in h.get("items", []):
                    champ = item.get("field")
                    if champ == "assignee":
                        n_assignee += 1
                    elif champ == "priority":
                        n_priorite += 1
                    elif champ == "status":
                        to = item.get("toString")
                        if to in STATUTS_FERMES:
                            ferme_vu = True
                        elif ferme_vu and to not in STATUTS_FERMES:
                            n_reopen += 1
            if n_assignee >= 2:  # 1er changement = affectation initiale, pas une réaffectation
                reaffectes += 1
            if n_reopen > 0:
                reouverts += 1
            if n_priorite >= 1:
                priorite_changee += 1

        pct = lambda n: round(100 * n / total, 1) if total else 0.0
        return {
            "total_fermes": total,
            "reaffectes": reaffectes, "reaffectes_pct": pct(reaffectes),
            "reouverts": reouverts, "reouverts_pct": pct(reouverts),
            "priorite_changee": priorite_changee, "priorite_changee_pct": pct(priorite_changee),
        }

    def lien_fournisseur(self):
        total = len(self.issues)
        avec_lien = tbd = 0
        for it in self.issues:
            val = it["fields"].get(CHAMP_EXTERNAL_ID)
            if val:
                avec_lien += 1
                if "TBD" in str(val).upper():
                    tbd += 1
        return {"total": total, "avec_lien": avec_lien, "tbd": tbd}

    def plus_anciens_ouverts(self, n: int = 10):
        res = []
        for it in self.issues:
            f = it["fields"]
            if (f.get("status") or {}).get("name") in STATUTS_FERMES:
                continue
            c = _parse_dt(f.get("created"))
            if c:
                res.append((it["key"], _heures_entre(c, self.maintenant)))
        return sorted(res, key=lambda t: -t[1])[:n]


def generer_rapport(a: Analyse) -> str:
    crees, fermes, deficits = a.creation_vs_fermeture()
    delais = a.delais()
    doublons = a.doublons_suspectes()
    vides = a.billets_vides_suspectes()
    non_assignes = a.non_assignes()
    ref = a.reference_actuelle()
    fournisseur = a.lien_fournisseur()
    anciens = a.plus_anciens_ouverts()

    L = []
    L.append("# Ce que vos données disent déjà")
    L.append("")
    L.append(f"*Généré le {a.maintenant.strftime('%Y-%m-%d %H:%M UTC')} — {len(a.issues)} billets analysés, projet PECARTES.*")
    L.append("")
    L.append("Aucune IA n'a été utilisée pour produire ce rapport.")
    L.append("")

    canaux = Counter(_canal(i) for i in a.issues)
    L.append("## Canaux d'entrée")
    L.append("")
    L.append("| Canal | Billets | Part |")
    L.append("|---|---:|---:|")
    for canal, n in canaux.most_common():
        pct = round(100 * n / len(a.issues), 1) if a.issues else 0
        L.append(f"| {canal} | {n} | {pct} % |")
    L.append("")
    L.append("*Les trois canaux alimentent la même file — aucun n'est exclu du "
             "périmètre. « Création directe » = ni label One Portail, ni Request "
             "Type : billet ouvert à la main dans le board.*")
    L.append("")

    atypiques = a.semaines_atypiques(crees, fermes)
    semaine_migration = _semaine(_parse_dt(MIGRATION + "T00:00:00+00:00"))

    L.append("## Créés contre fermés, par semaine")
    L.append("")
    L.append(f"La migration vers le système actuel a eu lieu le **{MIGRATION}** "
             f"(semaine {semaine_migration}) — repérée par ⬆ dans le tableau. "
             f"Avant cette ligne, c'est l'ancien fonctionnement.")
    L.append("")
    L.append("| Semaine | Créés | Fermés | Déficit cumulé |")
    L.append("|---|---:|---:|---:|")
    for s in sorted(set(crees) | set(fermes)):
        marque = " ⚠️" if s in atypiques else ""
        if s == semaine_migration:
            marque += " ⬆ migration"
        L.append(f"| {s}{marque} | {crees.get(s, 0)} | {fermes.get(s, 0)} | {deficits[s]:+d} |")
    L.append("")
    dernier = deficits[max(deficits)] if deficits else 0
    L.append(f"**Déficit cumulé actuel : {dernier:+d} billets.**")
    L.append("")
    if atypiques:
        deficit_hors = sum(
            crees.get(s, 0) - fermes.get(s, 0)
            for s in sorted(set(crees) | set(fermes)) if s not in atypiques
        )
        L.append(
            f"⚠️ **Semaine(s) marquée(s) : {', '.join(sorted(atypiques))}** — volume "
            f"créé ou fermé supérieur à 3× la médiane des autres semaines. Signale "
            f"un événement ponctuel (migration, campagne, incident), pas le rythme "
            f"normal du triage — la cause reste à confirmer, ce script ne fait que "
            f"la détecter. Déficit cumulé en excluant ces semaines : "
            f"**{deficit_hors:+d}** (contre {dernier:+d} brut)."
        )
        L.append("")

    L.append("## Référence actuelle — la barre à battre")
    L.append("")
    L.append(f"Sur {ref['total_fermes']} billets fermés :")
    L.append(f"- **{ref['reaffectes_pct']} %** réaffectés au moins une fois ({ref['reaffectes']} billets)")
    L.append(f"- **{ref['priorite_changee_pct']} %** avec priorité modifiée après ouverture ({ref['priorite_changee']} billets)")
    L.append(f"- **{ref['reouverts_pct']} %** réouverts après fermeture ({ref['reouverts']} billets)")
    L.append("")
    L.append("Trois chiffres à battre — calculés avant toute IA.")
    L.append("")

    L.append("## Délais de traitement — médiane et p90, jamais la moyenne seule")
    L.append("")
    L.append("### Par priorité")
    L.append("")
    L.append("| Priorité | N | Médiane totale | p90 totale | Médiane nette (hors attente tiers) |")
    L.append("|---|---:|---:|---:|---:|")
    for prio, valeurs in sorted(delais["priorite"].items()):
        totaux = [v[0] for v in valeurs]
        nets = [v[1] for v in valeurs]
        L.append(f"| {prio} | {len(valeurs)} | {_fmt_h(_mediane(totaux))} | {_fmt_h(_p90(totaux))} | {_fmt_h(_mediane(nets))} |")
    L.append("")

    L.append("### Par étiquette (proxy de catégorie, en attendant knowledge/categories.md)")
    L.append("")
    L.append("| Étiquette | N | Médiane | Temps total consommé |")
    L.append("|---|---:|---:|---:|")
    classement = sorted(delais["categorie"].items(), key=lambda kv: -sum(v[0] for v in kv[1]))
    for lbl, valeurs in classement[:15]:
        totaux = [v[0] for v in valeurs]
        L.append(f"| {lbl} | {len(valeurs)} | {_fmt_h(_mediane(totaux))} | {_fmt_h(sum(totaux))} |")
    L.append("")
    L.append("*Le classement par volume et le classement par temps consommé divergent presque toujours — comparer les deux tris.*")
    L.append("")

    L.append("## Temps d'attente fournisseur")
    L.append("")
    tous_attente = [h for h in (a.temps_attente_tiers(it) for it in a.issues) if h > 0]
    if tous_attente:
        L.append(f"- {len(tous_attente)} billets ont transité par un statut d'attente tiers")
        L.append(f"- Médiane : {_fmt_h(_mediane(tous_attente))} · p90 : {_fmt_h(_p90(tous_attente))}")
        L.append(f"- Temps total cumulé chez le fournisseur : {_fmt_h(sum(tous_attente))}")
    else:
        L.append("Aucune donnée d'attente tiers détectée — vérifier STATUTS_ATTENTE_TIERS dans le script.")
    L.append("")

    L.append("## Doublons suspectés")
    L.append("")
    if doublons:
        L.append(f"{len(doublons)} paires candidates (même signaleur, création rapprochée, résumés proches) :")
        L.append("")
        for k1, k2 in doublons[:30]:
            L.append(f"- {k1} ↔ {k2}")
        L.append("")
        L.append("*Liste de candidats à relire à l'œil — pas un verdict automatique.*")
    else:
        L.append("Aucun doublon candidat détecté avec l'heuristique actuelle.")
    L.append("")

    L.append("## Billets vides ou quasi vides (candidats « bruit-test »)")
    L.append("")
    if vides:
        pct_vides = round(100 * len(vides) / len(a.issues), 1) if a.issues else 0
        L.append(f"**{len(vides)}** billets ({pct_vides} %) ont un titre + description de "
                  f"moins de 15 caractères au total — trop court pour un vrai signalement.")
        L.append("")
        for k, texte in vides[:20]:
            L.append(f"- {k} — « {texte} »")
        L.append("")
        L.append("*Candidats à relire, pas un verdict — voir `knowledge/categories.md`, "
                  "catégorie `bruit-test`. Si confirmés, à exclure des futurs échantillons "
                  "(taxonomie, évaluation) ; leur poids dans le déficit créés/fermés "
                  "ci-dessus n'a pas été vérifié.*")
    else:
        L.append("Aucun billet quasi vide détecté avec le seuil actuel (15 caractères).")
    L.append("")

    L.append("## Billets non assignés")
    L.append("")
    L.append(f"**{len(non_assignes)}** billets ouverts sans assigné.")
    if non_assignes:
        L.append("")
        L.append("Les 10 plus anciens :")
        L.append("")
        for k, h in non_assignes[:10]:
            L.append(f"- {k} — sans assigné depuis {_fmt_h(h)}")
    L.append("")

    L.append("## Lien fournisseur")
    L.append("")
    pct_lien = round(100 * fournisseur["avec_lien"] / fournisseur["total"], 1) if fournisseur["total"] else 0
    L.append(f"- {pct_lien} % des billets portent un `External issue ID` ({fournisseur['avec_lien']} / {fournisseur['total']})")
    L.append(f"- **{fournisseur['tbd']}** billets ont un identifiant marqué `TBD` — lien non résolu")
    L.append("")

    L.append("## Billets les plus anciens encore ouverts")
    L.append("")
    L.append("| Billet | Âge |")
    L.append("|---|---:|")
    for k, h in anciens:
        L.append(f"| {k} | {_fmt_h(h)} |")
    L.append("")

    return "\n".join(L)


def _a_label_automatedcreation(issue) -> bool:
    return LABEL_AUTOMATEDCREATION in (issue["fields"].get("labels") or [])


def _canal(issue) -> str:
    """Canal d'entrée présumé — sert à décrire, jamais à filtrer."""
    f = issue["fields"]
    if _a_label_automatedcreation(issue):
        return "One Portail"
    if f.get(CHAMP_REQUEST_TYPE):
        return "JSD / dashboard"
    return "création directe"


def _borne_fenetre(mois: int) -> str:
    """Date ISO d'il y a `mois` mois, au format comparable aux dates Jira."""
    maintenant = datetime.now(timezone.utc)
    annee, m = maintenant.year, maintenant.month - mois
    while m <= 0:
        m += 12
        annee -= 1
    return f"{annee:04d}-{m:02d}-{maintenant.day:02d}"


def main() -> None:
    tous = charger_billets()

    if "--tous" in sys.argv:
        depuis, suffixe, libelle = "", "-tous", "tout l'historique"
    elif "--depuis-migration" in sys.argv:
        depuis, suffixe, libelle = MIGRATION, "-migration", f"depuis la migration ({MIGRATION})"
    else:
        mois = FENETRE_MOIS_DEFAUT
        if "--mois" in sys.argv:
            try:
                mois = int(sys.argv[sys.argv.index("--mois") + 1])
            except (IndexError, ValueError):
                sys.exit("--mois attend un nombre, ex. --mois 24")
        depuis = _borne_fenetre(mois)
        suffixe = "" if mois == FENETRE_MOIS_DEFAUT else f"-{mois}mois"
        libelle = f"{mois} derniers mois (depuis {depuis})"

    issues = [i for i in tous if (i["fields"].get("created") or "") >= depuis] if depuis else tous

    canaux = Counter(_canal(i) for i in issues)
    print(f"Périmètre : {libelle} — {len(issues)} billets sur {len(tous)}", file=sys.stderr)
    for canal, n in canaux.most_common():
        print(f"    {n:6d}  {canal}", file=sys.stderr)

    a = Analyse(issues)
    rapport = generer_rapport(a)

    RAPPORTS_DIR.mkdir(exist_ok=True)
    out = RAPPORTS_DIR / f"donnees-actuelles{suffixe}.md"
    out.write_text(rapport, encoding="utf-8")
    print(f"Rapport écrit → {out} ({len(issues)} billets)", file=sys.stderr)


if __name__ == "__main__":
    main()

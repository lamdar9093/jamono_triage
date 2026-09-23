#!/usr/bin/env python3
"""
scorer.py — Note les sorties Copilot contre la vérité terrain (livrable 5)

Lit lots/sorties/*.md (les réponses Copilot collées après chaque lot) et
lots/verite-terrain.json, écrit evals/resultats.md avec les chiffres
datés.

Format de sortie attendu par billet — voir .github/prompts/trier-lot.prompt.md
pour la liste exacte des champs, qui fait foi (l'exemple ci-dessous est
volontairement partiel ; le parseur capture n'importe quel champ CLÉ: valeur,
pas seulement ceux listés ici) :

    ### PECARTES-12345
    CATEGORIE: refus-transaction
    PRIORITE: 2
    EQUIPE: SAAS - PE Cartes
    COMPLETUDE: incomplet
    COMPLETUDE_MANQUE: numero_transaction; horodatage
    DEJA_VU: aucun
    CONFIANCE: 0.72

Si le parseur échoue sur une sortie, le format de prompt doit être
corrigé avant d'aller plus loin — voir la Vérification #4 du plan.

Usage :
    python scripts/scorer.py
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOTS_DIR = BASE_DIR / "lots"
SORTIES_DIR = LOTS_DIR / "sorties"
EVALS_DIR = BASE_DIR / "evals"

BLOC_RE = re.compile(r"###\s*(?P<cle>[A-Z]+-\d+)\s*\n(?P<corps>.*?)(?=\n###|\Z)", re.DOTALL)
CHAMP_RE = re.compile(r"^([A-Z_]+):\s*(.*)$", re.MULTILINE)


def parser_sortie(texte: str):
    resultats, erreurs = {}, []
    for m in BLOC_RE.finditer(texte):
        cle = m.group("cle")
        champs = dict(CHAMP_RE.findall(m.group("corps")))
        if not champs:
            erreurs.append(cle)
            continue
        resultats[cle] = champs
    return resultats, erreurs


def charger_toutes_sorties() -> dict:
    if not SORTIES_DIR.exists():
        sys.exit(f"{SORTIES_DIR} introuvable — colle les sorties Copilot d'abord (livrable 4 du plan).")
    fichiers = sorted(SORTIES_DIR.glob("*.md"))
    if not fichiers:
        sys.exit(f"Aucune sortie dans {SORTIES_DIR}.")

    tout, total_erreurs = {}, []
    for fichier in fichiers:
        resultats, erreurs = parser_sortie(fichier.read_text(encoding="utf-8"))
        tout.update(resultats)
        total_erreurs.extend(erreurs)

    if total_erreurs:
        print(f"ATTENTION — {len(total_erreurs)} bloc(s) non parsable(s) : {total_erreurs}", file=sys.stderr)
        print("Le format de sortie du prompt doit être corrigé avant de continuer (Vérification #4).", file=sys.stderr)
    else:
        print(f"{len(tout)} billets notés, 0 erreur de format.", file=sys.stderr)
    return tout


def charger_verite() -> dict:
    fichier = LOTS_DIR / "verite-terrain.json"
    if not fichier.exists():
        sys.exit(f"{fichier} introuvable — lance lots.py d'abord.")
    return json.loads(fichier.read_text(encoding="utf-8"))


def noter(propositions: dict, verite: dict) -> dict:
    n = bon_priorite = completude_formee = bon_equipe = n_equipe_verifiable = 0
    bon_personne = n_personne_verifiable = 0

    for cle, verite_billet in verite.items():
        prop = propositions.get(cle)
        if not prop:
            continue
        n += 1
        if prop.get("PRIORITE", "").strip().upper() == str(verite_billet.get("priorite_finale", "")).strip().upper():
            bon_priorite += 1
        if prop.get("COMPLETUDE") in ("complet", "incomplet"):
            completude_formee += 1

        # equipe_finale absente pour certains billets (champ Team pas toujours
        # rempli) — ceux-là ne comptent ni pour ni contre, plutôt que de fausser
        # le taux avec des billets où la vraie réponse n'est pas connue.
        equipe_reelle = verite_billet.get("equipe_finale")
        if equipe_reelle:
            n_equipe_verifiable += 1
            if prop.get("EQUIPE", "").strip().lower() == equipe_reelle.strip().lower():
                bon_equipe += 1

        # Même logique pour PERSONNE_SUGGEREE contre l'assigné réel du billet.
        # Proxy imparfait (voir lots.py) : qui a fermé le billet reflète parfois
        # juste la charge du moment (ex. un rôle de triage), pas le meilleur
        # choix possible — mais c'est la seule vérité terrain disponible, et ça
        # vaut mieux que zéro mesure sur un champ qui n'était jusqu'ici jamais
        # vérifié automatiquement.
        assignee_reel = verite_billet.get("assignee_final")
        if assignee_reel:
            n_personne_verifiable += 1
            if prop.get("PERSONNE_SUGGEREE", "").strip().lower() == assignee_reel.strip().lower():
                bon_personne += 1

    pct = lambda x, total=n: round(100 * x / total, 1) if total else 0.0
    return {
        "n_note": n,
        "n_total_verite": len(verite),
        "priorite_pct": pct(bon_priorite),
        "completude_formee_pct": pct(completude_formee),
        "equipe_pct": pct(bon_equipe, n_equipe_verifiable),
        "n_equipe_verifiable": n_equipe_verifiable,
        "personne_pct": pct(bon_personne, n_personne_verifiable),
        "n_personne_verifiable": n_personne_verifiable,
        # CATEGORIE reste non notée automatiquement : knowledge/categories.md
        # et la vérité terrain n'ont pas de vocabulaire garanti commun tant
        # que la taxonomie n'est pas figée (livrable 2) — comparaison
        # manuelle pour l'instant. EQUIPE et PERSONNE_SUGGEREE comparent
        # contre des champs Jira réels (Team, assignee), pas besoin d'attendre
        # la taxonomie pour ceux-là. PERSONNE_SUGGEREE ne teste que "a deviné
        # qui a fermé le billet", pas "a deviné le bon choix" — les deux ne
        # sont pas garantis identiques (voir le commentaire dans lots.py).
    }


def main() -> None:
    propositions = charger_toutes_sorties()
    verite = charger_verite()
    score = noter(propositions, verite)

    EVALS_DIR.mkdir(exist_ok=True)
    out = EVALS_DIR / "resultats.md"
    horodatage = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    equipe_col = f"{score['equipe_pct']} % (sur {score['n_equipe_verifiable']})"
    personne_col = f"{score['personne_pct']} % (sur {score['n_personne_verifiable']})"
    ligne = (f"| {horodatage} | {score['n_note']}/{score['n_total_verite']} | "
             f"{score['priorite_pct']} % | {equipe_col} | {personne_col} | "
             f"{score['completude_formee_pct']} % |\n")
    entete = ("# Résultats d'évaluation\n\n"
              "| Date | Billets notés | Priorité correcte | Équipe correcte | "
              "Personne = assigné réel | Complétude renseignée |\n"
              "|---|---|---|---|---|---|\n")

    if out.exists() and "| Date |" in out.read_text(encoding="utf-8"):
        out.write_text(out.read_text(encoding="utf-8") + ligne, encoding="utf-8")
    else:
        out.write_text(entete + ligne, encoding="utf-8")

    print(f"Résultat ajouté → {out}", file=sys.stderr)
    print(json.dumps(score, indent=2, ensure_ascii=False), file=sys.stderr)


if __name__ == "__main__":
    main()

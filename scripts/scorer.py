#!/usr/bin/env python3
"""
scorer.py — Note les sorties Copilot contre la vérité terrain (livrable 5)

Lit lots/sorties/*.md (les réponses Copilot collées après chaque lot) et
lots/verite-terrain.json, écrit evals/resultats.md avec les chiffres
datés.

Format de sortie attendu par billet (voir .github/prompts/trier-lot.prompt.md) :

    ### PECARTES-12345
    CATEGORIE: refus-transaction
    PRIORITE: 2
    EQUIPE: EQ-CARTES
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
    n = bon_priorite = completude_formee = 0

    for cle, verite_billet in verite.items():
        prop = propositions.get(cle)
        if not prop:
            continue
        n += 1
        if prop.get("PRIORITE", "").strip().upper() == str(verite_billet.get("priorite_finale", "")).strip().upper():
            bon_priorite += 1
        if prop.get("COMPLETUDE") in ("complet", "incomplet"):
            completude_formee += 1

    pct = lambda x: round(100 * x / n, 1) if n else 0.0
    return {
        "n_note": n,
        "n_total_verite": len(verite),
        "priorite_pct": pct(bon_priorite),
        "completude_formee_pct": pct(completude_formee),
        # CATEGORIE et EQUIPE ne peuvent être notées automatiquement que si
        # knowledge/categories.md et la vérité terrain partagent le même
        # vocabulaire — comparaison manuelle tant que la taxonomie n'est
        # pas figée (livrable 2).
    }


def main() -> None:
    propositions = charger_toutes_sorties()
    verite = charger_verite()
    score = noter(propositions, verite)

    EVALS_DIR.mkdir(exist_ok=True)
    out = EVALS_DIR / "resultats.md"
    horodatage = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ligne = f"| {horodatage} | {score['n_note']}/{score['n_total_verite']} | {score['priorite_pct']} % | {score['completude_formee_pct']} % |\n"
    entete = "# Résultats d'évaluation\n\n| Date | Billets notés | Priorité correcte | Complétude renseignée |\n|---|---|---|---|\n"

    if out.exists() and "| Date |" in out.read_text(encoding="utf-8"):
        out.write_text(out.read_text(encoding="utf-8") + ligne, encoding="utf-8")
    else:
        out.write_text(entete + ligne, encoding="utf-8")

    print(f"Résultat ajouté → {out}", file=sys.stderr)
    print(json.dumps(score, indent=2, ensure_ascii=False), file=sys.stderr)


if __name__ == "__main__":
    main()

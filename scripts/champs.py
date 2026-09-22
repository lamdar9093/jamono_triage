#!/usr/bin/env python3
"""
champs.py — Liste les champs Jira pour trouver les customfield_XXXXX (lecture seule)

Sert une seule fois : identifier les identifiants réels des champs
personnalisés (Request type, Application Card, External issue ID) afin de
les ajouter à FIELDS dans extraire.py.

Usage :
    python scripts/champs.py            # champs correspondant aux mots-clés
    python scripts/champs.py --tous     # tous les champs personnalisés
"""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "").rstrip("/")
JIRA_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")

# Mots-clés cherchés dans le nom des champs, en minuscules.
MOTS_CLES = [
    "request type", "type de demande", "customer request",
    "application card", "carte", "nbc",
    "external", "externe",
    "customer status", "statut client",
    "organization", "organisation", "channel", "canal",
    "team", "équipe", "equipe", "groupe", "group",
]


def _session() -> requests.Session:
    if not JIRA_BASE_URL:
        sys.exit("JIRA_BASE_URL manquant.")
    if not JIRA_TOKEN:
        sys.exit("JIRA_API_TOKEN manquant.")
    s = requests.Session()
    if JIRA_EMAIL:
        s.auth = (JIRA_EMAIL, JIRA_TOKEN)
    else:
        s.headers["Authorization"] = f"Bearer {JIRA_TOKEN}"
    s.headers["Accept"] = "application/json"
    return s


def main() -> None:
    tous = "--tous" in sys.argv
    resp = _session().get(f"{JIRA_BASE_URL}/rest/api/2/field", timeout=30)
    if resp.status_code != 200:
        sys.exit(f"Erreur Jira {resp.status_code} : {resp.text[:500]}")

    champs = resp.json()
    retenus = []
    for c in champs:
        nom = c.get("name", "")
        # Avant : ne cherchait que les champs personnalisés (custom=True).
        # Un champ "Team" est souvent un champ standard Jira (Advanced
        # Roadmaps) — passé inaperçu jusqu'ici pour cette seule raison,
        # sans même parler du mot-clé "team" qui manquait ci-dessus.
        if tous or any(m in nom.lower() for m in MOTS_CLES):
            retenus.append((c.get("id", ""), nom, c.get("custom", False)))

    retenus.sort(key=lambda x: x[1].lower())
    print(f"{len(champs)} champs au total, {len(retenus)} retenus\n")
    for cid, nom, custom in retenus:
        etiquette = "personnalisé" if custom else "standard"
        print(f'    "{cid}",  # {nom}  [{etiquette}]')

    if not retenus:
        print("Aucune correspondance — relance avec --tous et cherche à la main.")


if __name__ == "__main__":
    main()

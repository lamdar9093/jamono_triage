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
        if not c.get("custom"):
            continue
        if tous or any(m in nom.lower() for m in MOTS_CLES):
            retenus.append((c.get("id", ""), nom))

    retenus.sort(key=lambda x: x[1].lower())
    print(f"{len(champs)} champs au total, {len(retenus)} retenus\n")
    for cid, nom in retenus:
        print(f'    "{cid}",  # {nom}')

    if not retenus:
        print("Aucune correspondance — relance avec --tous et cherche à la main.")


if __name__ == "__main__":
    main()

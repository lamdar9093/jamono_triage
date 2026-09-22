#!/usr/bin/env python3
"""
Diagnostic ponctuel : lequel de ces 17 champs "équipe" est vraiment
rempli, et avec quelles valeurs ? champs.py donne des noms plausibles,
pas des preuves — on vérifie sur de vrais billets avant de choisir.

Usage : python3 commande.py
"""
import sys
from collections import Counter

import requests
from dotenv import load_dotenv
import os

load_dotenv()
JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "").rstrip("/")
JIRA_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")

CANDIDATS = {
    "customfield_14750": "Assigned Team",
    "customfield_15241": "Assigned Teams",
    "customfield_39800": "Blocking Team",
    "customfield_11523": "Equipe",
    "customfield_14748": "Group Affected",
    "customfield_15902": "Group(s)",
    "customfield_58000": "Groups",
    "customfield_14914": "Impacted Teams",
    "customfield_63000": "Inactive Tempo Team",
    "customfield_12907": "Labor Group",
    "customfield_11101": "Original Requestor Group",
    "customfield_15901": "Original Requestor Group(s)",
    "customfield_14920": "Support Team",
    "customfield_12300": "SystemTeams",
    "customfield_11600": "Team",
    "customfield_16709": "Team Role",
    "customfield_14701": "Tempo Team",
}


def _session() -> requests.Session:
    s = requests.Session()
    if JIRA_EMAIL:
        s.auth = (JIRA_EMAIL, JIRA_TOKEN)
    else:
        s.headers["Authorization"] = f"Bearer {JIRA_TOKEN}"
    s.headers["Accept"] = "application/json"
    return s


def _valeur(v):
    if v is None:
        return None
    if isinstance(v, dict):
        return v.get("value") or v.get("name") or v.get("displayName") or str(v)
    if isinstance(v, list):
        return ", ".join(_valeur(x) or str(x) for x in v) if v else None
    return str(v)


def main() -> None:
    session = _session()
    resp = session.get(
        f"{JIRA_BASE_URL}/rest/api/2/search",
        params={
            "jql": 'project = "PECARTES" ORDER BY updated DESC',
            "maxResults": 50,
            "fields": ",".join(CANDIDATS),
        },
        timeout=30,
    )
    if resp.status_code != 200:
        sys.exit(f"Erreur Jira {resp.status_code} : {resp.text[:500]}")

    issues = resp.json().get("issues", [])
    print(f"{len(issues)} billets récents examinés\n")

    remplis = Counter()
    exemples = {}
    for it in issues:
        for cid, nom in CANDIDATS.items():
            val = _valeur(it["fields"].get(cid))
            if val:
                remplis[cid] += 1
                exemples.setdefault(cid, set()).add(val)

    print("Champ rempli sur combien de billets, et exemples de valeurs :\n")
    for cid, nom in CANDIDATS.items():
        n = remplis.get(cid, 0)
        if n == 0:
            print(f"  {nom} ({cid}) — jamais rempli sur cet échantillon")
        else:
            vals = list(exemples[cid])[:5]
            print(f"  {nom} ({cid}) — rempli sur {n}/{len(issues)} — ex. : {vals}")


if __name__ == "__main__":
    main()

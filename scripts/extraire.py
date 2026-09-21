#!/usr/bin/env python3
"""
extraire.py — Extraction des billets PECARTES depuis Jira (lecture seule)

Ne quitte jamais data/ — voir .gitignore à la racine. Nécessite un jeton
d'API Jira en lecture seule, scope limité au projet PECARTES.

Configuration : copier .env.example vers .env et remplir.

Usage :
    python scripts/extraire.py
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "").rstrip("/")
JIRA_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")  # vide si auth par jeton (PAT) seul
JIRA_PROJECT_KEY = os.environ.get("JIRA_PROJECT_KEY", "PECARTES")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_FILE = DATA_DIR / "billets.json"

PAGE_SIZE = 100

# Champs demandés à l'API. Le champ "External issue ID" est un champ
# personnalisé Jira (customfield_XXXXX) — à confirmer sur ton instance
# (Paramètres > Champs personnalisés) et à ajouter ici une fois connu.
FIELDS = [
    "summary", "description", "issuetype", "priority", "status",
    "assignee", "reporter", "created", "updated", "resolutiondate",
    "labels", "components",
    # "customfield_XXXXX",  # External issue ID — décommenter une fois confirmé
]


def _session() -> requests.Session:
    if not JIRA_BASE_URL:
        sys.exit("JIRA_BASE_URL manquant — copie .env.example vers .env et configure-le.")
    if not JIRA_TOKEN:
        sys.exit("JIRA_API_TOKEN manquant — jeton personnel en lecture seule requis.")
    s = requests.Session()
    if JIRA_EMAIL:
        s.auth = (JIRA_EMAIL, JIRA_TOKEN)  # Jira Cloud
    else:
        s.headers["Authorization"] = f"Bearer {JIRA_TOKEN}"  # Jira Server / Data Center (PAT)
    s.headers["Accept"] = "application/json"
    return s


def extraire() -> list:
    session = _session()
    jql = f'project = "{JIRA_PROJECT_KEY}" ORDER BY created ASC'
    issues: list = []
    start_at = 0

    while True:
        resp = session.get(
            f"{JIRA_BASE_URL}/rest/api/2/search",
            params={
                "jql": jql,
                "startAt": start_at,
                "maxResults": PAGE_SIZE,
                "fields": ",".join(FIELDS),
                "expand": "changelog",
            },
            timeout=30,
        )
        if resp.status_code != 200:
            sys.exit(f"Erreur Jira {resp.status_code} : {resp.text[:500]}")

        payload = resp.json()
        batch = payload.get("issues", [])
        issues.extend(batch)

        total = payload.get("total", 0)
        start_at += len(batch)
        print(f"  {start_at} / {total} billets extraits...", file=sys.stderr)

        if start_at >= total or not batch:
            break
        time.sleep(0.2)  # ménager l'API

    return issues


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    print(f"Extraction du projet {JIRA_PROJECT_KEY}...", file=sys.stderr)
    issues = extraire()

    payload = {
        "extrait_le": datetime.now(timezone.utc).isoformat(),
        "projet": JIRA_PROJECT_KEY,
        "total": len(issues),
        "issues": issues,
    }
    OUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(issues)} billets écrits dans {OUT_FILE}", file=sys.stderr)


if __name__ == "__main__":
    main()

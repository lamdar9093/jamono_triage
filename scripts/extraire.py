#!/usr/bin/env python3
"""
extraire.py — Extraction des billets PECARTES depuis Jira (lecture seule)

Incrémental par défaut : ne redemande que les billets modifiés depuis la
dernière extraction, puis fusionne avec data/billets.json. Reprend où il
s'était arrêté si une extraction a été interrompue.

Ne quitte jamais data/ — voir .gitignore à la racine. Nécessite un jeton
d'API Jira en lecture seule, scope limité au projet PECARTES.

Configuration : copier .env.example vers .env et remplir.

Usage :
    python scripts/extraire.py             # incrémental (ou complet si data/ vide)
    python scripts/extraire.py --complet   # force une extraction totale
"""
import os
import re
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "").rstrip("/")
JIRA_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")  # vide si auth par jeton (PAT) seul
JIRA_PROJECT_KEY = os.environ.get("JIRA_PROJECT_KEY", "PECARTES")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_FILE = DATA_DIR / "billets.json"

# Reprise sur interruption : les pages déjà reçues sont ajoutées au fur et à
# mesure dans le .jsonl (append, donc peu coûteux), le .json garde la position.
REPRISE_META = DATA_DIR / ".extraction-en-cours.json"
REPRISE_DATA = DATA_DIR / ".extraction-en-cours.jsonl"

PAGE_SIZE = 100

# Marge retranchée à la borne « updated » pour absorber les écarts de fuseau
# entre l'horodatage renvoyé par Jira et celui du profil du jeton. Quelques
# billets sont réextraits pour rien — la fusion par clé les dédoublonne.
MARGE_MINUTES = 10

# Champs demandés à l'API. Le label "automatedcreation" (présent dans "labels")
# marque les billets ouverts via OnePortail, c'est-à-dire la liste triage.
# Le champ "External issue ID" est un champ personnalisé Jira
# (customfield_XXXXX) — à confirmer sur ton instance
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


def _parse_jira_dt(valeur):
    """Jira renvoie 2026-08-14T22:25:31.123-0400 — fuseau sans « : »."""
    if not valeur:
        return None
    s = str(valeur).strip().replace("Z", "+00:00")
    s = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", s)
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def charger_existant() -> dict:
    """Billets déjà extraits, indexés par clé (PECARTES-123)."""
    if not OUT_FILE.exists():
        return {}
    try:
        payload = json.loads(OUT_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"  {OUT_FILE.name} illisible ({e}) — extraction complète.", file=sys.stderr)
        return {}
    return {i["key"]: i for i in payload.get("issues", []) if i.get("key")}


def borne_updated(connus: dict) -> str:
    """Date du billet le plus récemment modifié, au format attendu par JQL.

    On la calcule sur les billets en main plutôt que sur l'heure de la dernière
    extraction : l'horodatage garde ainsi le fuseau de Jira lui-même, ce qui
    évite le décalage UTC / heure locale dans la requête JQL.
    """
    dates = [d for d in (_parse_jira_dt(i.get("fields", {}).get("updated")) for i in connus.values()) if d]
    if not dates:
        return ""
    return (max(dates) - timedelta(minutes=MARGE_MINUTES)).strftime("%Y-%m-%d %H:%M")


def charger_reprise(jql: str):
    """Reprend une extraction interrompue si elle portait sur la même requête."""
    if not (REPRISE_META.exists() and REPRISE_DATA.exists()):
        return 0, []
    try:
        meta = json.loads(REPRISE_META.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0, []
    if meta.get("jql") != jql:
        print("  Reprise ignorée : la requête a changé.", file=sys.stderr)
        nettoyer_reprise()
        return 0, []

    start_at = int(meta.get("start_at", 0))
    lignes = REPRISE_DATA.read_text(encoding="utf-8").splitlines()
    # Le .jsonl peut dépasser start_at si l'arrêt a eu lieu entre l'ajout des
    # billets et l'écriture de la position — on tronque pour rester cohérent.
    issues = [json.loads(l) for l in lignes[:start_at] if l.strip()]
    start_at = len(issues)
    if start_at:
        print(f"  Reprise à {start_at} billets déjà reçus.", file=sys.stderr)
    return start_at, issues


def nettoyer_reprise() -> None:
    REPRISE_META.unlink(missing_ok=True)
    REPRISE_DATA.unlink(missing_ok=True)


def extraire(jql: str) -> list:
    session = _session()
    start_at, issues = charger_reprise(jql)
    if start_at == 0:
        REPRISE_DATA.write_text("", encoding="utf-8")

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
        total = payload.get("total", 0)
        if not batch:
            break

        issues.extend(batch)
        start_at += len(batch)

        with REPRISE_DATA.open("a", encoding="utf-8") as f:
            for issue in batch:
                f.write(json.dumps(issue, ensure_ascii=False) + "\n")
        REPRISE_META.write_text(
            json.dumps({"jql": jql, "start_at": start_at, "total": total}),
            encoding="utf-8",
        )

        print(f"  {start_at} / {total} billets extraits...", file=sys.stderr)
        if start_at >= total:
            break
        time.sleep(0.2)  # ménager l'API

    return issues


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    complet = "--complet" in sys.argv

    connus = {} if complet else charger_existant()
    depuis = borne_updated(connus) if connus else ""

    jql = f'project = "{JIRA_PROJECT_KEY}"'
    if depuis:
        jql += f' AND updated >= "{depuis}"'
        print(f"Extraction incrémentale — {len(connus)} billets en main, "
              f"modifiés depuis {depuis}.", file=sys.stderr)
    else:
        print(f"Extraction complète du projet {JIRA_PROJECT_KEY}...", file=sys.stderr)
    jql += " ORDER BY created ASC"

    recus = extraire(jql)

    nouveaux = sum(1 for i in recus if i.get("key") not in connus)
    for issue in recus:
        if issue.get("key"):
            connus[issue["key"]] = issue

    issues = sorted(
        connus.values(),
        key=lambda i: i.get("fields", {}).get("created") or "",
    )
    payload = {
        "extrait_le": datetime.now(timezone.utc).isoformat(),
        "projet": JIRA_PROJECT_KEY,
        "total": len(issues),
        "issues": issues,
    }
    OUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    nettoyer_reprise()

    print(f"{len(recus)} billets reçus ({nouveaux} nouveaux, "
          f"{len(recus) - nouveaux} mis à jour).", file=sys.stderr)
    print(f"{len(issues)} billets au total dans {OUT_FILE}", file=sys.stderr)


if __name__ == "__main__":
    main()

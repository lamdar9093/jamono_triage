#!/usr/bin/env python3
"""
anonymiser.py — Remplace les identités réelles par des identifiants stables

Lit data/billets.json, écrit data/billets-anon.json. Les deux fichiers
restent dans data/, ignoré par git — l'anonymisation protège ce qui sort
de la machine (rapports, evals versionnés), pas ce qui y reste.

Usage :
    python scripts/anonymiser.py
"""
import json
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
IN_FILE = DATA_DIR / "billets.json"
OUT_FILE = DATA_DIR / "billets-anon.json"
MAP_FILE = DATA_DIR / "correspondance-anonymisation.json"

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


class Anonymiseur:
    """Ce fichier de correspondance ne quitte jamais la machine et ne doit
    jamais être copié dans un rapport ou un dépôt versionné."""

    def __init__(self):
        self._noms = {}
        self._compteur = 0

    def _id_pour(self, nom: str) -> str:
        if not nom:
            return nom
        if nom not in self._noms:
            self._compteur += 1
            self._noms[nom] = f"PERSONNE-{self._compteur:03d}"
        return self._noms[nom]

    def anonymiser_champ_personne(self, champ):
        if not champ:
            return champ
        nom = champ.get("displayName") or champ.get("name") or ""
        return {**champ, "displayName": self._id_pour(nom), "emailAddress": None, "name": None}

    def anonymiser_texte(self, texte):
        if not texte:
            return texte
        texte = EMAIL_RE.sub("[courriel]", texte)
        for nom, anon in self._noms.items():
            if len(nom) > 3:  # éviter de toucher des mots courts coïncidents
                texte = texte.replace(nom, anon)
        return texte

    def sauvegarder_correspondance(self) -> None:
        MAP_FILE.write_text(json.dumps(self._noms, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    if not IN_FILE.exists():
        sys.exit(f"{IN_FILE} introuvable — lance d'abord extraire.py")

    brut = json.loads(IN_FILE.read_text(encoding="utf-8"))
    anon = Anonymiseur()

    for issue in brut["issues"]:
        f = issue.get("fields", {})
        f["assignee"] = anon.anonymiser_champ_personne(f.get("assignee"))
        f["reporter"] = anon.anonymiser_champ_personne(f.get("reporter"))
        f["summary"] = anon.anonymiser_texte(f.get("summary"))
        f["description"] = anon.anonymiser_texte(f.get("description"))
        # issuetype / priority / status / labels / dates / clé : non touchés,
        # ce sont les champs dont l'analyse a besoin.

        for entry in issue.get("changelog", {}).get("histories", []):
            entry["author"] = anon.anonymiser_champ_personne(entry.get("author"))

    OUT_FILE.write_text(json.dumps(brut, indent=2, ensure_ascii=False), encoding="utf-8")
    anon.sauvegarder_correspondance()
    print(f"{len(brut['issues'])} billets anonymisés → {OUT_FILE}", file=sys.stderr)
    print(f"Correspondance (locale, jamais à partager) → {MAP_FILE}", file=sys.stderr)


if __name__ == "__main__":
    main()

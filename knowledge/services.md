# Catalogue de services

Anonymisé. Les identifiants sont génériques et stables — ils servent de clé dans `patterns/`, dans les evals et dans le journal d'audit. La correspondance vers les noms réels vit à la banque, jamais ici.

## Tiers

| Tier | Définition | Conséquence |
|---|---|---|
| **1** | Le client ne peut plus transiger si le service tombe | Astreinte 24/7, seuils les plus stricts |
| **2** | Dégradation visible du client, contournement possible | Astreinte heures étendues |
| **3** | Interne, différé, ou invisible du client | Heures ouvrables |

## Vue d'ensemble

| ID | Rôle | Tier | Équipe propriétaire | Dépend de |
|---|---|---|---|---|
| `PAIEMENT-1` | Passerelle de paiement | 1 | EQ-PAIEMENTS | `CORE-2`, `FRAUDE-1`, `AUTH-1` |
| `CORE-2` | Cœur bancaire, soldes et écritures | 1 | EQ-CORE | — |
| `AUTH-1` | Authentification et session | 1 | EQ-IDENTITE | `CORE-2` |
| `MOBILE-1` | Application mobile, façade API | 1 | EQ-CANAUX | `AUTH-1`, `CORE-2`, `API-GW-1` |
| `WEB-1` | Banque en ligne | 1 | EQ-CANAUX | `AUTH-1`, `CORE-2`, `API-GW-1` |
| `API-GW-1` | Passerelle API, limitation de débit | 1 | EQ-PLATEFORME | — |
| `FRAUDE-1` | Scoring de fraude temps réel | 2 | EQ-RISQUE | `CORE-2` |
| `NOTIF-1` | Notifications client (push, SMS, courriel) | 2 | EQ-CANAUX | `API-GW-1` |
| `BATCH-3` | Traitements de nuit, compensation | 2 | EQ-CORE | `CORE-2` |
| `RAPPORT-2` | Rapports réglementaires et internes | 3 | EQ-DONNEES | `CORE-2`, `BATCH-3` |

---

## Détail par service

### `PAIEMENT-1` — Passerelle de paiement

- **Tier** 1 · **Propriétaire** EQ-PAIEMENTS · **Astreinte** 24/7
- **Impact si indisponible** : aucune transaction client ne passe. P1 immédiat.
- **Dépendances** : `CORE-2` (soldes), `FRAUDE-1` (scoring), `AUTH-1` (session)
- **Dépendants** : `MOBILE-1`, `WEB-1`
- **Fenêtre sensible** : fins de mois et jours de paie — volume ×3
- **Seuils propres** : taux d'erreur P1 abaissé à **> 2 % sur 5 min** (au lieu de 5 %) — toute erreur ici est une transaction perdue
- **Contournement** : aucun. C'est la raison du seuil abaissé.

### `CORE-2` — Cœur bancaire

- **Tier** 1 · **Propriétaire** EQ-CORE · **Astreinte** 24/7
- **Impact si indisponible** : tout tombe. Aucun service ne fonctionne sans lui.
- **Dépendances** : aucune. C'est la racine du graphe.
- **Dépendants** : tous les autres services, directement ou non
- **Fenêtre sensible** : batch de nuit 01:00–04:00, latence naturellement plus élevée — **ne pas déclencher sur la latence seule dans cette fenêtre**
- **Contournement** : aucun

### `AUTH-1` — Authentification

- **Tier** 1 · **Propriétaire** EQ-IDENTITE · **Astreinte** 24/7
- **Impact si indisponible** : personne ne se connecte. Les sessions déjà ouvertes survivent jusqu'à expiration — l'impact monte donc progressivement sur ~30 min au lieu d'être immédiat.
- **Dépendances** : `CORE-2`
- **Dépendants** : `MOBILE-1`, `WEB-1`, `PAIEMENT-1`
- **Piège de triage** : les premières minutes sous-estiment l'impact réel à cause des sessions actives. Classer sur la tendance, pas sur l'instantané.

### `MOBILE-1` / `WEB-1` — Canaux client

- **Tier** 1 · **Propriétaire** EQ-CANAUX · **Astreinte** 24/7
- **Dépendances** : `AUTH-1`, `CORE-2`, `API-GW-1`
- **Piège de triage** : la majorité des incidents remontés ici viennent d'une dépendance, pas du canal. Vérifier `AUTH-1`, `API-GW-1` et `CORE-2` **avant** d'affecter à EQ-CANAUX. C'est la première cause de mauvaise affectation.

### `API-GW-1` — Passerelle API

- **Tier** 1 · **Propriétaire** EQ-PLATEFORME · **Astreinte** 24/7
- **Dépendances** : aucune
- **Dépendants** : `MOBILE-1`, `WEB-1`, `NOTIF-1`
- **Piège de triage** : la limitation de débit produit des erreurs qui ressemblent à une panne applicative. Un pic de 429 est un incident de passerelle, pas un incident du service appelé.

### `FRAUDE-1` — Scoring de fraude

- **Tier** 2 · **Propriétaire** EQ-RISQUE · **Astreinte** heures étendues
- **Impact si indisponible** : selon la politique de repli. Si le repli est « accepter sans scoring », l'exposition au risque augmente → **traiter en P1 malgré le tier 2**. Si le repli est « refuser », les paiements tombent → P1 également, via `PAIEMENT-1`.
- **Cas particulier** : ce service est le seul du catalogue dont le tier ne détermine pas la sévérité. Toujours qualifier le mode de repli actif.

### `NOTIF-1` — Notifications

- **Tier** 2 · **Propriétaire** EQ-CANAUX
- **Impact** : le client n'est pas averti, mais ses opérations aboutissent. Rattrapage possible.
- **Piège** : un retard de notification génère un volume d'appels au service client qui donne l'impression d'un incident plus grave. L'impact réel reste tier 2.

### `BATCH-3` — Traitements de nuit

- **Tier** 2 · **Propriétaire** EQ-CORE
- **Fenêtre d'exécution** : 01:00–04:00. **Fenêtre de rattrapage jusqu'à 06:00.**
- **Règle de sévérité** : un retard est P3 tant que 06:00 n'est pas menacé, puis **P1 directement** — pas P2. Passé la fenêtre, la compensation du jour ne part pas, ce qui a des conséquences réglementaires.
- **Piège** : le nom « BATCH » et le tier 2 poussent à sous-classer. C'est le second piège de triage le plus fréquent du catalogue.

### `RAPPORT-2` — Rapports

- **Tier** 3 · **Propriétaire** EQ-DONNEES · **Heures ouvrables**
- **Exception** : un rapport à échéance réglementaire bascule en P2 à J-1 de l'échéance, quel que soit le tier.

---

## Règles transverses

**Remonter au service racine.** Un incident sur `MOBILE-1` causé par `AUTH-1` est un incident `AUTH-1`, affecté à EQ-IDENTITE, avec `MOBILE-1` en service impacté. Le champ « service affecté » et le champ « service en cause » sont distincts et tous deux obligatoires.

**Le tier ne suffit pas.** Trois services du catalogue ont une règle qui prime sur leur tier : `FRAUDE-1` (mode de repli), `BATCH-3` (fenêtre), `RAPPORT-2` (échéance). Un triage qui ne lit que le tier se trompera sur ces trois-là.

**Maintenance.** Ce fichier est révisé à chaque mise en service, mise hors service ou changement de propriétaire. Un catalogue périmé produit des affectations fausses, et une affectation fausse coûte plus cher qu'une sévérité fausse : elle fait perdre le délai de prise en charge.

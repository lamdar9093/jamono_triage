# Escalade

Qui, quand, dans quel ordre, sous quel délai. Ce fichier répond à une seule question : **à quel moment est-ce que je dérange quelqu'un d'autre, et lequel ?**

## Principe

L'escalade est déclenchée par un **délai dépassé**, pas par un ressenti. Si le compteur est écoulé, on escalade — même si « ça va bientôt être réglé ». C'est précisément quand on croit être proche du bout qu'on escalade trop tard.

---

## Délais par sévérité

| | Prise en charge | 1re mise à jour | Fréquence | Escalade N+1 si non pris en charge | Escalade N+2 |
|---|---|---|---|---|---|
| **P1** | 5 min | 15 min | 30 min | 10 min | 30 min |
| **P2** | 30 min | 1 h | 2 h | 1 h | 4 h |
| **P3** | 4 h ouvrées | 1 jour | quotidienne | 1 jour ouvré | — |
| **P4** | 5 jours ouvrés | — | — | — | — |

Les compteurs partent de la **détection**, pas de l'ouverture du billet. L'écart entre les deux est lui-même une métrique à surveiller.

---

## Chaîne d'escalade

```
   Détection (alerte ou signalement)
        │
   ┌────▼─────────────────┐
   │ N1 — service desk    │  triage, ouverture du billet, première qualification
   └────┬─────────────────┘
        │  P1/P2 immédiat · P3 si bloqué après 4 h
   ┌────▼─────────────────┐
   │ N2 — SRE d'astreinte │  diagnostic, contournement, coordination
   └────┬─────────────────┘
        │  équipe propriétaire du service (voir services.md)
   ┌────▼─────────────────┐
   │ N3 — équipe produit  │  correction sur son périmètre
   └────┬─────────────────┘
        │  P1 non résolu à 30 min · P2 à 4 h
   ┌────▼─────────────────┐
   │ Gestionnaire d'astreinte │  arbitrage, décisions à impact client
   └────┬─────────────────┘
        │  P1 à 2 h · toute déclaration réglementaire
   ┌────▼─────────────────┐
   │ Direction + conformité   │
   └──────────────────────┘
```

## Escalades immédiates, sans attendre le compteur

Ces situations court-circuitent la chaîne et notifient directement le niveau indiqué :

| Situation | Notifier immédiatement |
|---|---|
| Accès non autorisé confirmé ou soupçonné | Sécurité + gestionnaire d'astreinte |
| Perte ou corruption de données financières | Gestionnaire d'astreinte + conformité |
| `declaration_reglementaire: à_qualifier` | Conformité, dans l'heure |
| Décision envisagée ayant un impact client volontaire (coupure, bascule) | Gestionnaire d'astreinte, **avant** l'action |
| Deux P1 simultanés | Gestionnaire d'astreinte, pour arbitrage de priorité |
| `FRAUDE-1` en mode de repli « accepter sans scoring » | EQ-RISQUE + gestionnaire d'astreinte |

## Escalade latérale

Tous les incidents ne montent pas — certains traversent. Un incident dont la cause est chez un fournisseur ou un partenaire n'escalade pas en interne : il déclenche la procédure fournisseur, et l'incident interne reste ouvert avec le statut « en attente tiers ». Ne pas laisser un compteur d'escalade interne courir sur un incident qu'aucune escalade interne ne résoudra ; le requalifier explicitement.

---

## Communication

| Sévérité | Canal | Audience | Rythme |
|---|---|---|---|
| P1 | Canal d'incident dédié + diffusion générale | Toute la technologie + métier impacté | 30 min |
| P2 | Canal d'incident dédié | Équipes concernées + propriétaire de service | 2 h |
| P3 | Fil du billet | Équipe propriétaire | Quotidien |
| P4 | Fil du billet | — | — |

**Règle de la mise à jour vide.** Si rien n'a avancé au moment de l'échéance, publier quand même : « pas d'évolution depuis la dernière mise à jour, prochaine dans 30 min ». Le silence est systématiquement interprété comme une aggravation, et il génère des interruptions qui ralentissent la résolution.

**Séparer les faits de l'hypothèse.** Une mise à jour d'incident distingue explicitement ce qui est constaté de ce qui est supposé. Une hypothèse publiée comme un fait devient une cause racine dans la mémoire collective, et se retrouve dans le post-mortem trois semaines plus tard sans que personne ne l'ait vérifiée.

---

## Ce que l'escalade n'est pas

Escalader n'est pas se défausser, et ce n'est pas un constat d'échec. C'est un mécanisme de délai. Une culture où escalader est mal vu produit mécaniquement des escalades tardives — et le coût d'une escalade tardive sur un P1 est sans commune mesure avec le coût d'une escalade inutile.

Si quelqu'un hésite à escalader, le défaut est dans la culture d'équipe, pas dans son jugement.

---
id: err-rate-spike-paiement
error_pattern: ERR_RATE_SPIKE
component: PAIEMENT-1
signature: err_rate>2pct_5min+lat_stable+single_region
severite_par_defaut: P1
confiance: 0.87
occurrences: 3
faux_positifs_connus: 2
derniere_revue: 2026-09-17
---

# Pic de taux d'erreur sur la passerelle de paiement

> Le taux d'erreur de `PAIEMENT-1` dépasse 2 % en quelques minutes, sans que la latence ne bouge, et sur une seule région.

## Signature observable

- Taux d'erreur `PAIEMENT-1` **> 2 % sur 5 min** (seuil propre au service, voir `services.md`)
- Latence p99 **stable**, dans sa plage habituelle
- Erreurs concentrées sur **une seule région**
- `CORE-2` et `FRAUDE-1` nominaux sur la même fenêtre

L'absence de dégradation de latence est le discriminant principal. Une saturation fait monter la latence **avant** les erreurs ; ici les erreurs montent seules, ce qui oriente vers un rejet en amont plutôt que vers un épuisement de ressources.

## Ce que ça signifie

Dans les trois occurrences observées, la cause était un rejet côté région et non une défaillance applicative. La bascule de région a résolu les trois cas.

**La cause racine commune n'est pas établie.** Trois occurrences, trois résolutions par le même geste, mais aucune analyse n'a confirmé un mécanisme unique. Ce motif est fiable pour le triage et l'action ; il ne doit pas être cité comme cause racine dans un post-mortem.

## Actions

1. **Vérifier les discriminants** — latence stable, région unique, dépendances nominales. 2 min. Si un seul discriminant manque, ce motif ne s'applique pas : repartir d'un diagnostic ouvert.
2. **Basculer la région** — effet attendu sous 3 min, réversible. C'est le geste qui a résolu les trois occurrences.
3. **Confirmer la reprise** — taux d'erreur sous 0,5 % sur 5 min consécutives avant de rétrograder la sévérité.
4. **Si pas de reprise à 10 min** — le motif ne tient pas. Escalader à EQ-PAIEMENTS et traiter en diagnostic ouvert ; ne pas s'entêter sur la bascule.

## Faux positifs connus

| Ressemble à | En réalité | Discriminant |
|---|---|---|
| Pic d'erreurs `PAIEMENT-1` | Limitation de débit sur `API-GW-1` | Les erreurs sont des **429**, et `MOBILE-1`/`WEB-1` sont touchés simultanément. Incident `API-GW-1`, pas `PAIEMENT-1`. |
| Pic d'erreurs `PAIEMENT-1` | `FRAUDE-1` en repli « refuser » | `FRAUDE-1` non nominal sur la même fenêtre. La cause est dans le repli de scoring, l'incident appartient à EQ-RISQUE. |

Ces deux faux positifs ont chacun coûté une mauvaise affectation. Les vérifier fait partie de l'action 1, ce n'est pas optionnel.

## Historique

| Date | Incident | Sévérité retenue | Résolu par | Le motif a-t-il aidé ? |
|---|---|---|---|---|
| 2026-03-14 | INC-3908 | P1 | Bascule de région | — (motif créé à cette occasion) |
| 2026-06-02 | INC-4177 | P1 | Bascule de région | oui — 4 min au lieu de 22 |
| 2026-08-27 | INC-4402 | P1 | Bascule de région | oui — 3 min |

## Ce qui reste non résolu

- Pourquoi une seule région, et pourquoi celle-là. Aucune corrélation établie avec les déploiements, la charge ou une fenêtre horaire.
- Les trois occurrences sont espacées de ~10 semaines. Trop peu de points pour conclure à une périodicité, assez pour justifier une analyse dédiée hors incident.
- La bascule fonctionne sans qu'on sache ce qu'elle contourne. C'est un contournement efficace, pas une correction — et tant que ce point n'est pas levé, le motif ne réduit pas le risque, il réduit seulement le temps de résolution.

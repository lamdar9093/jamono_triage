---
id: <identifiant-kebab-case-unique>
error_pattern: <MOTIF_EN_MAJUSCULES>     # aligné sur knowledge_base.py
component: <ID-SERVICE>                   # doit exister dans services.md
signature: <clé de reconnaissance stable>
severite_par_defaut: <P1|P2|P3|P4>
confiance: <0.00-1.00>
occurrences: <nombre>
faux_positifs_connus: <nombre>
derniere_revue: <AAAA-MM-JJ>
---

# <Titre lisible du motif>

> Une phrase : ce qui se passe, vu de l'extérieur.

## Signature observable

Ce qu'on voit, mesurable, sans interprétation. C'est la partie qui permet la reconnaissance automatique — elle doit tenir sans contexte.

- Signal 1 : métrique, seuil, fenêtre
- Signal 2 : …
- Ce qui est **absent** et qui compte (l'absence d'un signal est un discriminant aussi fort que sa présence)

## Ce que ça signifie

La cause habituelle, en une ou deux phrases. Si la cause n'est pas établie, l'écrire — un motif reconnu sans cause comprise reste utile pour le triage, et le dire évite qu'une hypothèse devienne une certitude par répétition.

## Actions

Dans l'ordre. Chacune avec son effet attendu et son coût.

1. **<Action>** — effet attendu, durée, réversible ou non
2. …

## Faux positifs connus

La section la plus précieuse du fichier, et celle qu'on oublie. Ce qui ressemble à ce motif sans en être.

| Ressemble à | En réalité | Discriminant |
|---|---|---|
| … | … | … |

## Historique

| Date | Incident | Sévérité retenue | Résolu par | Le motif a-t-il aidé ? |
|---|---|---|---|---|
| … | … | … | … | oui / non |

## Ce qui reste non résolu

Ce qu'on ne sait toujours pas. Écrire l'ignorance explicitement : c'est ce qui empêche le motif d'être appliqué au-delà de son domaine de validité.

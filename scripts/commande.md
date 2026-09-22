python3 -c "
import json
from collections import Counter
d = json.load(open('../data/billets.json'))
issues = d['issues']

# 1. Répartition par année de création, parmi ceux qui ont un Customer Request Type
annees = Counter()
for i in issues:
    if i['fields'].get('customfield_11200'):
        c = i['fields'].get('created', '')
        if c:
            annees[c[:4]] += 1
print('--- Par année (avec Customer Request Type) ---')
for a, n in sorted(annees.items()):
    print(a, n)

# 2. Première apparition du label automatedcreation (marqueur fiable One Portail)
premiere = None
for i in issues:
    if 'automatedcreation' in (i['fields'].get('labels') or []):
        c = i['fields'].get('created', '')
        if c and (premiere is None or c < premiere):
            premiere = c
print()
print('Premier billet automatedcreation créé le :', premiere)
"
---

python3 -c "
import json
d = json.load(open('../data/billets.json'))
issues = d['issues']

depuis = '2026-06-11'
n = sum(1 for i in issues
        if i['fields'].get('customfield_11200')
        and i['fields'].get('created', '') >= depuis)
print(n, 'billets avec Customer Request Type créés depuis le', depuis)

total_periode = sum(1 for i in issues if i['fields'].get('created', '') >= depuis)
print(total_periode, 'billets créés depuis le', depuis, '(tous, toutes origines)')
"

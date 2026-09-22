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

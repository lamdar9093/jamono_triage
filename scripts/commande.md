python3 -c "
import json
from collections import Counter
d = json.load(open('../data/billets-anon.json'))
issues = d['issues']

depuis = '2026-06-11'
large = [i for i in issues
         if i['fields'].get('customfield_11200')
         and (i['fields'].get('created') or '') >= depuis]

avec_label = sum(1 for i in large if 'automatedcreation' in (i['fields'].get('labels') or []))
sans_label = [i for i in large if 'automatedcreation' not in (i['fields'].get('labels') or [])]

print(len(large), 'billets avec Request Type depuis', depuis)
print(avec_label, 'ont le label automatedcreation')
print(len(sans_label), 'ne l\'ont PAS — leurs autres labels :')
c = Counter()
for i in sans_label:
    labels = i['fields'].get('labels') or []
    c[tuple(sorted(labels)) or ('(aucun)',)] += 1
for combo, n in c.most_common(15):
    print(' ', n, combo)
"

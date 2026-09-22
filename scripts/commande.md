python3 -c "
import json
from collections import Counter
d = json.load(open('../data/billets.json'))
issues = d['issues']

depuis = '2026-06-11'
app = Counter()
for i in issues:
    if i['fields'].get('customfield_11200') and i['fields'].get('created', '') >= depuis:
        v = i['fields'].get('customfield_37502')
        nom = v.get('value') if isinstance(v, dict) else v
        app[str(nom)] += 1
for nom, n in app.most_common(20):
    print(n, nom)
"

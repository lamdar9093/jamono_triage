python3 -c "
import json
from collections import Counter
d = json.load(open('../data/billets-anon.json'))
st = Counter()
for i in d['issues']:
    f = i['fields']
    if f.get('customfield_11200') and (f.get('created') or '') >= '2026-06-11':
        st[(f.get('status') or {}).get('name', '?')] += 1
for s, n in st.most_common():
    print(n, s)
"

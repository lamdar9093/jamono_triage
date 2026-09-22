python3 -c "
import sys
sys.path.insert(0, '.')
import analyser as a
tous = a.charger_billets()
issues = [i for i in tous if a._a_label_automatedcreation(i)]
an = a.Analyse(issues)
crees, fermes, deficits = an.creation_vs_fermeture()
semaines = sorted(set(crees) | set(fermes))
med_c = a._mediane([crees.get(s,0) for s in semaines])
med_f = a._mediane([fermes.get(s,0) for s in semaines])
print(f'{len(issues)} billets, {len(semaines)} semaines')
print(f'Médiane créés/semaine : {med_c}, seuil (x3) : {med_c*3}')
print(f'Médiane fermés/semaine : {med_f}, seuil (x3) : {med_f*3}')
print()
for s in semaines:
    print(f'{s}: créés={crees.get(s,0)} fermés={fermes.get(s,0)}')
"

import json,sys
d={c['id']:c for c in json.load(open('/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas/allcmds.json'))}
for a in sys.argv[1:]:
    for k,c in d.items():
        if k==a or (a.endswith('*') and k.startswith(a[:-1])):
            print(k,'::',c['params'][:1800],'\n')

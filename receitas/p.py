import json,sys
d={e['id']:e for e in json.load(open('/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas/allcmds.json'))}
for a in sys.argv[1:]:
    e=d.get(a); print('##',a, (e or {}).get('params','NOTFOUND')[:2500]); print()

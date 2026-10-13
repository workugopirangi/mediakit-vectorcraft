import sys,time; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
p=P("R23")
p.dir=R+"R23/v/"
p.rect(0,0,1440,810,fill=SEA)
im=p.img(SPE+"ondas-serra-traco.png",1000,20,300,300)
r=p.ex("imageTrace.makeAndExpand",{"id":im,"params":{"mode":"color","palette":"limited","colors":2,"ignoreWhite":True,"paths":90,"corners":50,"noise":2,"method":"abutting"}}); print(r)
tid=r["id"]
p.ex("select.set",{"ids":[tid]})
nm=p.ex("object.pattern.make",{"tileType":"grid","name":"ondasV","width":300,"height":300})["name"]
p.ex("object.pattern.done",{})
p.ex("edit.clear",{"ids":[tid]})
rc_=p.rect(0,0,1440,810,fill=None)
p.ex("select.set",{"ids":[rc_]}); p.ex("paint.setFill",{"swatch":nm}); p.ex("select.none")
p.text(60,760,"ondas vetorizadas, tile 300 pt",34,color=CREAM)
p.export()

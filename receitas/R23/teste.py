import sys; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
import os
p = P("R23")
def clip_to(ids, x,y,w,h):
    m = p.rect(x,y,w,h,fill="#000000")
    p.ex("select.set",{"ids":ids+[m]}); r=p.ex("object.clippingMask.make",{}); p.ex("select.none"); return r["id"]

# fundos dos tres paineis
for i in range(3): p.rect(i*480,0,480,810,fill=SEA)

# ---- A: object.pattern.make com o PNG do motivo (cronometro gravura), tijolo
im=p.img(SPE+"cronometro-gravura.png",20,20,130,130)
p.ex("select.set",{"ids":[im]})
nm=p.ex("object.pattern.make",{"tileType":"brickByRow","name":"cronA","width":190,"height":190})["name"]
p.ex("object.pattern.done",{})
print("imagens soltas apos done:",p.ex("document.find",{"kind":"Image"})["total"])
p.ex("edit.clear",{"ids":[im]})  # o original continua na pagina apos pattern.make
ra=p.rect(0,0,480,810,fill=None)
p.ex("select.set",{"ids":[ra]}); p.ex("paint.setFill",{"swatch":nm}); p.ex("select.none")

# ---- B: repeticao manual de instancias colocadas (grid vivo estilo tijolo, expandido)
im2=p.img(SPE+"cronometro-gravura.png",500,20,100,100)
p.ex("select.set",{"ids":[im2]})
rg=p.ex("object.repeat.grid",{"rows":8,"cols":6,"hSpacing":30,"vSpacing":0})["id"]
print(p.ex("object.repeat.options",{"gridType":"brick"}))
p.ex("select.none")
p.ex("select.set",{"ids":[rg]}); ex=p.ex("object.repeat.expand",{}); print("expandido",str(ex)[:120])
gids=ex["ids"]; p.ex("select.none")
bb=clip_to(gids,480,0,480,810)

# ---- C: tile seamless desenhado por IA (ondas-serra-traco) via pattern.make grid
im3=p.img(SPE+"ondas-serra-traco.png",1000,20,300,300)
p.ex("select.set",{"ids":[im3]})
nm3=p.ex("object.pattern.make",{"tileType":"grid","name":"ondasC","width":300,"height":300})["name"]
p.ex("object.pattern.done",{})
p.ex("edit.clear",{"ids":[im3]})
rc_=p.rect(960,0,480,810,fill=None)
p.ex("select.set",{"ids":[rc_]}); p.ex("paint.setFill",{"swatch":nm3}); p.ex("select.none")
p.text(30,780,"A  pattern.make, tijolo",26,color=CREAM)
p.text(510,780,"B  repeat.grid brick + expand",26,color=CREAM)
p.text(990,780,"C  tile seamless, grade",26,color=CREAM)
p.export()

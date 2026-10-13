import sys,os
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
p=P("R41")
p.rect(0,0,1440,810,fill="#1b6a8a")
def sticker(x,y,txt,size,offset,joins,fillt,fills,style="Condensed Black",unite=True):
    t=p.text(x,y,txt,size,fillt,style=style)
    p.ex("select.set",{"ids":[t]})
    o=p.ex("type.createOutlines",{}); ids=o["ids"] if isinstance(o,dict) else o; print("outl",ids)
    p.ex("select.set",{"ids":ids})
    g=None
    if unite:
        u=p.try_("object.pathfinder.unite",{}); print("unite",u)
        ids=u["ids"] if u else ids
    # duplicar para o contorno: offset gera objetos novos acima dos originais
    p.ex("select.set",{"ids":ids})
    r=p.try_("object.path.offsetPath",{"offset":offset,"joins":joins}); print("off",r)
    if r:
        for i in r["ids"]:
            p.paint(i,fills,stroke=K,sw=2)
            p.ex("select.set",{"ids":[i]}); p.ex("object.arrange.sendToBack",{}) if False else None
        return r["ids"],ids
    return None,ids
# vamos criar: fundo do sticker (offset) deve ficar ATRAS do texto. Tentamos arrange
a,b=sticker(80,300,"COPA AME",170,22,"round",Y,"#FFFFFF")
if a:
    for i in b: p.ex("select.set",{"ids":[i]}); p.try_("object.arrange.bringToFront",{})
    p.ex("select.none")
p.text(80,100,"Efeito adesivo: createOutlines, unite, offsetPath 14 pt round",22,"#FFFFFF",style="Regular")
a2,b2=sticker(80,640,"SPRINT 2027",150,10,"miter","#0F3550",CREAM)
if a2:
    for i in b2: p.ex("select.set",{"ids":[i]}); p.try_("object.arrange.bringToFront",{})
a3,b3=sticker(880,640,"500",190,12,"round","#E9603A","#FFFFFF",unite=False)
p.export(); p.close()

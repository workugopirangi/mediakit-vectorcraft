import sys, time; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
import os
p = P("R31")
p.ex("document.rasterEffectsSettings",{"resolution":300})
p.rect(0,0,1440,810,fill="#FFFFFF")
from PIL import Image
f=SPT+"f1.jpg"
res=[]
def box(x,label,resolution=None,vec=False,freq=20):
    o=p.img(f,x,100,420,575)
    p.ex("select.set",{"ids":[o]})
    t=time.time()
    if vec:
        r=p.ex("object.vectorHalftone",{"shape":"circle","frequency":freq,"angle":45,"mode":"cmyk","clip":True})
    else:
        r=p.ex("effect.apply",{"effect":"pixelate.colorHalftone","params":{"maxRadius":MR}})
    res.append((label,r,round(time.time()-t,2))); p.ex("select.none")
    p.text(x,730,label,28,"Helvetica Neue","Bold",color=K)
print(p.ex("effect.list",{"ids":[]}) if False else "")
MR=2.6
box(40,"efeito colorHalftone r=2.6")
box(510,"vetorial CMYK 20 lpi",vec=True)
o=p.img(f,980,100,420,575); p.text(980,730,"original",28,"Helvetica Neue","Bold",color=K)
for r in res: print(r)
p.export()

import sys,os
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
p=P("R40")
p.rect(0,0,1440,810,fill="#07131c")
p.text(60,80,"Blend: concêntricos, linhas de velocidade, spine curva",28,CREAM,style="Regular")
# A: concentricos preenchidos cor interpolada (20 passos), nao-stroke
b=p.ell(300,330,230,230,fill=SEA); a=p.ell(300,330,40,40,fill=CORAL)
p.ex("select.set",{"ids":[b,a]})
r=p.try_("object.blend.make",{"ids":[b,a],"steps":20,"orientation":"page"}); print("A",r)
# B: linhas de velocidade: duas curvas stroke 3pt, 24 passos
c1=p.path("M 640 300 C 760 220 900 380 1020 300",stroke=GOLD,sw=3)
c2=p.path("M 640 520 C 760 440 900 600 1020 520",stroke=MINT,sw=3)
r=p.try_("object.blend.make",{"ids":[c1,c2],"steps":24,"orientation":"page"}); print("B",r)
# C: blend com spine curva: 2 circulos pequenos e path de spine
d1=p.ell(1100,150,16,16,fill=GOLD); d2=p.ell(1380,600,16,16,fill=CORAL)
r=p.try_("object.blend.make",{"ids":[d1,d2],"steps":14}); print("C",r)
if r:
    sp=p.ex("path.create",{"d":"M 1100 150 C 1100 450 1380 250 1380 600"})["id"]
    p.paint(sp,None,stroke=None)
    p.ex("select.set",{"ids":[r["id"],sp]})
    print("spine",p.try_("object.blend.replaceSpine",{}))
# D: blend expandido, para medir
e1=p.rect(660,620,100,100,fill=GOLD); e2=p.rect(1020,620,100,100,fill=CORAL,radius=50)
r=p.try_("object.blend.make",{"ids":[e1,e2],"steps":6}); print("D",r)
if r:
    p.ex("select.set",{"ids":[r["id"]]}); print("exp",p.try_("object.blend.expand",{}))
p.export(); p.close()

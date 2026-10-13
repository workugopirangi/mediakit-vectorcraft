import sys,os
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
p=P("R47")
p.rect(0,0,1440,810,fill=SEA)
p.text(60,90,"Circuito 2027: rota entre as etapas",44,CREAM,style="Bold")
def route(d,color,w,**sp):
    i=p.path(d,fill=None,stroke=color,sw=w); p.ex("select.set",{"ids":[i]}); r=p.try_("stroke.set",{"weight":w,**sp}); return i
# A: pontilhado redondo continuo (dash 0,gap + cap round) com seta no fim
a=route("M 120 300 C 300 120 520 480 760 260 S 1100 200 1280 330",MINT,6,cap="round",dash=[0,14],endArrow="Arrow",arrowAlign="tip")
# B: tracejado normal com seta aberta
b=route("M 120 520 C 360 400 520 700 780 520 S 1100 480 1280 560",GOLD,5,cap="round",dash=[16,10],endArrow="ArrowOpen",startArrow="Circle")
# C: solida com seta, grossa
c=route("M 120 700 L 1280 700",CORAL,10,cap="round",endArrow="TriangleBar") 
# marcadores
for (x,y,n) in [(120,300,"1"),(430,330,"2"),(760,260,"3"),(1100,260,"4"),(1280,330,"5")]:
    p.ell(x,y,17,17,fill=CREAM,stroke=K,sw=2); p.text(x-5,y+6,n,18,K,style="Bold")
# texto no path
t=p.path("M 140 600 C 400 560 700 760 1100 600",fill=None,stroke=None)
r=p.try_("text.createInPath",{"path":t,"mode":"onPath","text":"São Paulo  Taubaté  São José  Ubatuba","size":26,"font":"Helvetica Neue","style":"Bold","color":"#FFFFFF"}); print(r)
p.text(80,800,"pontilhado round [0,14] | tracejado [16,10] com círculo no início | sólido com TriangleBar",16,"#FFFFFF",style="Regular")
p.export(); p.close()

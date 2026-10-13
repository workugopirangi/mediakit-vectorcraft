import sys,os,math
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
p=P("R49")
p.rect(0,0,1440,810,fill=SEA)
p.text(60,90,"Sprint 2026: quem correu",48,CREAM,style="Bold")
def ring(cx,cy,r,w,pct,col,track="#1d5578",num=None,lab=""):
    p.ell(cx,cy,r,r,fill=None,stroke=track,sw=w)
    # arco SVG a partir do topo, sentido horario
    a=2*math.pi*pct/100
    x1,y1=cx,cy-r; x2,y2=cx+r*math.sin(a),cy-r*math.cos(a); large=1 if pct>50 else 0
    i=p.path(f"M {x1:.3f} {y1:.3f} A {r} {r} 0 {large} 1 {x2:.3f} {y2:.3f}",fill=None,stroke=col,sw=w)
    p.ex("select.set",{"ids":[i]}); p.ex("stroke.set",{"weight":w,"cap":"round"})
    p.text(cx-len(str(pct))*20-14,cy+18,f"{pct}%",64,"#FFFFFF",style="Condensed Black")
    p.text(cx-r,cy+r+w/2+40,lab,24,"#FFFFFF",style="Medium")
ring(280,380,130,34,52,GOLD,lab="52% turistas")
ring(720,380,130,34,53,MINT,lab="53% mulheres")
ring(1160,380,130,34,42,CORAL,lab="42% da meta de 1.200")
# B: via dash exato numa elipse (circunferencia * pct), rotacionada
r=60; c=2*math.pi*r
e=p.ell(280,700,r,r,fill=None,stroke=GOLD,sw=18)
p.ex("select.set",{"ids":[e]}); print(p.try_("stroke.set",{"weight":18,"cap":"round","dash":[c*0.52-18,c],"align":"center"}))
print(p.try_("object.transform",{"ids":[e],"matrix":None})) if False else None
p.text(380,715,"B: elipse com dash [c*pct, c]: arranca à direita (3h), não do topo",18,"#FFFFFF",style="Regular")
# C: outlineStroke para virar forma preenchida
i=p.path("M 800 700 A 60 60 0 1 1 860 640",fill=None,stroke=MINT,sw=18)
p.ex("select.set",{"ids":[i]}); p.ex("stroke.set",{"weight":18,"cap":"round"})
print("outline",p.try_("object.path.outlineStroke",{}))
p.text(900,715,"C: arco outlineStroke (forma preenchida)",18,"#FFFFFF",style="Regular")
p.export(); p.close()

import sys,os
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
p=P("R48")
p.rect(0,0,1440,810,fill=K)
p.text(60,80,"Copa AME: gráfico nativo (esquerda) x barras desenhadas (direita)",30,Y,style="Regular")
g=p.ex("graph.create",{"type":"column","x":60,"y":130,"width":600,"height":520,"series":["jan/2026","set/2026"],"categories":["Instagram (mil)","TV AME (inscritos/10)"],"rows":[[113.4,204.8],[243,518]]}); gid=g["id"]
print(p.try_("graph.setType",{"id":gid,"columnWidth":80,"clusterWidth":70,"legend":True,"ticks":4,"axisMin":0}))
def tree(n,out=None):
    out=[] if out is None else out
    if isinstance(n,dict):
        if "id" in n and "kind" in n: out.append((n["id"],n["kind"],n.get("fill")))
        for v in n.values(): tree(v,out)
    elif isinstance(n,list):
        for v in n: tree(v,out)
    return out
t=tree(p.ex("document.inspect",{"depth":6}))
grp=[x for x in t if x[1]=="Group" and x[0]>gid]
types=[x[0] for x in t if x[1]=="Type" and x[0]>gid]
print(grp,types)
# series: grupos com paths 8c8c8c e 000000 (a ordem de criacao: 49 preto=jan, 50 cinza=set)
for gx in grp:
    pass
paths=[x for x in t if x[1]=="Path" and x[2] in("#000000","#8c8c8c")]
print(paths)
for pid,kind,fl in paths:
    p.ex("select.set",{"ids":[pid]}); p.ex("paint.setFill",{"color":"#8A7A0A" if fl=="#000000" else Y})
p.ex("select.set",{"ids":types}); print(p.try_("paint.setFill",{"color":"#FFFFFF"})); print(p.try_("text.setStyle",{"size":14,"font":"Helvetica Neue","style":"Medium"}))
g2=p.ex("graph.create",{"type":"pie","x":60,"y":680,"width":110,"height":110,"series":["turistas","moradores"],"rows":[[52,48]]})
# desenhadas
x0,base=780,640; mx=204800; hmax=420
for j,(lab,v,c) in enumerate([("jan/2026",113400,"#8A7A0A"),("set/2026",204800,Y)]):
    h=hmax*v/mx; x=x0+j*200
    p.rect(x,base-h,150,h,fill=c,radius=6)
    p.text(x+75-len(f"{v:,}".replace(',','.'))*11,base-h-16,f"{v:,}".replace(",","."),40,"#FFFFFF",style="Bold")
    p.text(x+30,base+36,lab,24,"#FFFFFF",style="Medium")
p.text(780,720,"Instagram, visualizações",22,"#FFFFFF",style="Regular")
p.rect(780,base,420,2,fill="#FFFFFF")
p.text(1240,300,"+80,6%",90,Y,style="Condensed Black")
p.export(); p.close()

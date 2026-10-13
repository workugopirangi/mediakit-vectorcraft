import sys,os
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
p=P("R39")
p.rect(0,0,1440,810,fill=K)
p.text(60,80,"Perspectiva e malha de envelope",28,Y,style="Regular")
# A: distort projetivo no texto
t=p.text(100,300,"COPA AME",150,Y,style="Condensed Black")
b=p.ex("object.getBounds",{"ids":[t]}) if False else None
p.ex("select.set",{"ids":[t]})
print("bounds",p.try_("object.getBounds",{"ids":[t]}))
print("distort",p.try_("object.distort",{"ids":[t],"corners":[[140,170],[800,120],[900,330],[100,350]]}))
# B: envelope por malha, move pontos
t2=p.text(100,600,"2026",170,"#FFFFFF",style="Condensed Black")
r=p.try_("object.envelope.makeWithMesh",{"ids":[t2],"rows":3,"cols":4}); print(r)
ins=p.ex("document.inspect",{"depth":3})
def find(n,i):
    if isinstance(n,dict):
        if n.get("id")==i: return n
        for v in n.values():
            x=find(v,i)
            if x: return x
    elif isinstance(n,list):
        for v in n:
            x=find(v,i)
            if x: return x
bd=find(ins,r["id"])["bounds"]; print("bounds",bd)
x0,y0,x1,y1=bd if isinstance(bd,list) else (bd["x"],bd["y"],bd["x"]+bd["width"],bd["y"]+bd["height"])
R,C=3,4
def pt(rw,cl): return x0+(x1-x0)*cl/C, y0+(y1-y0)*rw/R
for (rw,cl,dx,dy) in [(1,2,25,-40),(2,3,30,30),(1,1,-15,20),(0,4,0,-30),(3,4,0,30)]:
    x,y=pt(rw,cl); print(rw,cl,p.try_("object.envelope.setMeshPoint",{"id":r["id"],"index":rw*(C+1)+cl,"x":x+dx,"y":y+dy}))
# C: foto em perspectiva (distort de imagem)
im=p.ex("file.place",{"path":TRAT_A+"c-capa-composta.jpg","link":False})["ids"][0]
p.ex("object.setBounds",{"ids":[im],"x":900,"y":250,"width":440,"height":250,"reference":0})
print("distortimg",p.try_("object.distort",{"ids":[im],"corners":[[900,260],[1340,200],[1340,540],[900,500]]}))
p.export(); p.close()

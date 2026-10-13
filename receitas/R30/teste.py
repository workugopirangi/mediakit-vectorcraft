import sys, time; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
p = P("R30")
p.rect(0,0,1440,810,fill="#FFFFFF")
im=p.img(AMT+"real-noite-das-estrelas.jpg",0,0,1,1) if False else None
from PIL import Image
f=AMT+"real-equipe-sub.jpg"; print(Image.open(f).size)
w,h=Image.open(f).size; bw=620; bh=bw*h/w
o=p.img(f,60,90,bw,bh)
p.ex("select.set",{"ids":[o]})
t=time.time()
r=p.ex("object.vectorHalftone",{"shape":"circle","frequency":25,"angle":45,"mode":"cmyk","clip":True})
print(r,round(time.time()-t,2))
g=r["id"]
ins=p.ex("document.inspect",{"depth":4,"childLimit":20})
def walk(n,d=0):
    if d<5: print("  "*d,n.get("kind"),n.get("id"),n.get("fill"),n.get("blend"),n.get("opacity"),n.get("bounds") if d>2 else "")
    for c in (n.get("children") or [])[:6]: walk(c,d+1)
for l in ins["layers"]: walk(l)
p.ex("select.none")
# original em copia ao lado para comparar
o2=p.img(f,740,90,bw,bh)
p.text(60,60,"Halftone CMYK vetorial (25 lpi)",30,"Helvetica Neue","Bold",color=K); p.text(740,60,"Foto original",30,"Helvetica Neue","Bold",color=K)
p.export()

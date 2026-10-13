import sys,os,json,math
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
sp=json.load(open(os.path.expanduser("~/Developer/vectorcraft-mediakit/sp.json")))["features"][0]["geometry"]
polys=sp["coordinates"] if sp["type"]=="MultiPolygon" else [sp["coordinates"]]
pts=[c for poly in polys for ring in poly for c in ring]
lon0=min(c[0] for c in pts); lon1=max(c[0] for c in pts); lat0=min(c[1] for c in pts); lat1=max(c[1] for c in pts)
k=math.cos(math.radians(-22.5))
W,H=640,570; X0,Y0=50,190
s=min(W/((lon1-lon0)*k),H/(lat1-lat0))
tr=lambda lo,la:(X0+(lo-lon0)*k*s, Y0+(lat1-la)*s)
def inpoly(x,y,ring):
    ins=False; n=len(ring)
    for i in range(n):
        x1,y1=ring[i]; x2,y2=ring[(i+1)%n]
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1: ins=not ins
    return ins
def inside(x,y): return any(inpoly(x,y,poly[0]) and not any(inpoly(x,y,h) for h in poly[1:]) for poly in polys)
p=P("R46")
p.rect(0,0,1440,810,fill=SEA)
p.text(60,90,"De onde vem o público",48,CREAM,style="Bold")
p.text(60,128,"São Paulo: pontos (esquerda) e bolhas proporcionais por cidade (direita). Valores ilustrativos de teste.",18,"#FFFFFF",style="Regular")
# mapa de pontos: grade 7 pt, raio 2.2, em UM path composto
r=2.2; step=7; d=[]
y=Y0
while y<Y0+H:
    x=X0
    while x<X0+W:
        lo=lon0+(x-X0)/(k*s); la=lat1-(y-Y0)/s
        if inside(lo,la): d.append(f"M {x-r:.1f} {y:.1f} a {r} {r} 0 1 0 {2*r} 0 a {r} {r} 0 1 0 {-2*r} 0 Z")
        x+=step
    y+=step
print("dots",len(d))
p.path(" ".join(d),fill=MINT)
# mapa B: contorno + bolhas
trB=lambda lo,la:(tr(lo,la)[0]+640, tr(lo,la)[1])
def dstr(t):
    out=[]
    for poly in polys:
        for ring in poly: out.append("M "+" L ".join("%.2f %.2f"%t(*c) for c in ring)+" Z")
    return " ".join(out)
p.path(dstr(trB),fill="#17486a",stroke="#2F7F8F",sw=1)
cities=[("São Paulo",-46.63,-23.55,100),("Campinas",-47.06,-22.91,52),("São José dos Campos",-45.89,-23.22,40),("Taubaté",-45.56,-23.03,28),("Ubatuba",-45.08,-23.43,70),("Santos",-46.33,-23.96,36),("Ribeirão Preto",-47.81,-21.18,30),("Sorocaba",-47.46,-23.5,26),("Guarulhos",-46.53,-23.46,34)]
for n,lo,la,v in cities:
    x,y=trB(lo,la); rad=math.sqrt(v)*5.2   # area proporcional
    o=p.ell(x,y,rad,rad,fill=CORAL,stroke="#FFFFFF",sw=0.8,opacity=70)
for n,lo,la,v in sorted(cities,key=lambda c:-c[3])[:5]:
    x,y=trB(lo,la); lft=lo>-45.5; p.text((x-math.sqrt(v)*5.2-4-len(n)*7) if lft else x+math.sqrt(v)*5.2+4,y+(5 if n!="Ubatuba" else 32),f"{n}",14,"#FFFFFF",style="Bold")
# ubatuba destaque
x,y=trB(-45.08,-23.43); p.ell(x,y,4,4,fill=GOLD,stroke=K,sw=1)
p.export(); p.close()

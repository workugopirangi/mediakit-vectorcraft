import sys,os,json,math,random
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
G=os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34/geo/")
br=json.load(open(G+"br_uf.json")); est={str(e["id"]):e for e in json.load(open(G+"estados.json"))}
p=P("R45")
BG="#0F3550"
p.rect(0,0,1440,810,fill=BG)
# bbox
pts=[c for f in br["features"] for poly in (f["geometry"]["coordinates"] if f["geometry"]["type"]=="MultiPolygon" else [f["geometry"]["coordinates"]]) for ring in poly for c in ring]
lon0=min(c[0] for c in pts); lon1=max(c[0] for c in pts); lat0=min(c[1] for c in pts); lat1=max(c[1] for c in pts)
k=math.cos(math.radians(-14))
def mk(x0,y0,w,h):
    s=min(w/((lon1-lon0)*k),h/(lat1-lat0))
    return lambda lo,la:(x0+(lo-lon0)*k*s, y0+(lat1-la)*s)
def dstr(f,tr):
    g=f["geometry"]; polys=g["coordinates"] if g["type"]=="MultiPolygon" else [g["coordinates"]]
    out=[]
    for poly in polys:
        for ring in poly:
            q=[tr(*c) for c in ring]
            out.append("M "+" L ".join(f"{x:.2f} {y:.2f}" for x,y in q)+" Z")
    return " ".join(out)
random.seed(3)
val={f["properties"]["codarea"]:random.choice([5,10,20,40,80]) for f in br["features"]}
val["35"]=100; val["33"]=40; val["31"]=40; val["41"]=20
def col(v):
    ramp=[ "#1D5578","#2F7F8F","#9FE3D0","#D4A64A","#E9603A"]
    return ramp[0 if v<=5 else 1 if v<=10 else 2 if v<=20 else 3 if v<=40 else 4]
p.text(60,90,"Alcance dos atletas por estado",44,CREAM,style="Bold")
p.text(60,125,"Mapa coroplético, 27 UFs (valores ilustrativos de teste)",18,"#FFFFFF",style="Regular")
trA=mk(60,160,640,610)
import time; t0=time.time()
for f in br["features"]:
    cid=f["properties"]["codarea"]
    i=p.path(dstr(f,trA),fill=col(val[cid]),stroke=BG,sw=0.6)
    p.ex("select.set",{"ids":[i]}); p.try_("stroke.set",{"weight":0.6,"join":"round"})
print("estados",time.time()-t0)
# mapa B sem traco para teste de fresta (fundo preto, cor clara)
trB=mk(800,120,380,360)
p.rect(780,100,420,400,fill="#000000")
for f in br["features"]:
    p.path(dstr(f,trB),fill=col(val[f["properties"]["codarea"]]),stroke=None)
p.text(790,520,"sem traço entre estados (teste de frestas)",14,"#FFFFFF",style="Regular")
# legenda
for j,(lab,c) in enumerate([("até 5","#1D5578"),("6 a 10","#2F7F8F"),("11 a 20","#9FE3D0"),("21 a 40","#D4A64A"),("acima de 40","#E9603A")]):
    p.rect(1240,160+j*34,22,22,fill=c); p.text(1272,178+j*34,lab,16,"#FFFFFF",style="Regular")
# siglas
for f in br["features"]:
    cid=f["properties"]["codarea"]
    if cid in("35","31","29","23","13","15","52","41","43","33"):
        g=f["geometry"]; polys=g["coordinates"] if g["type"]=="MultiPolygon" else [g["coordinates"]]
        big=max((r for poly in polys for r in poly[:1]),key=len)
        cx=sum(c[0] for c in big)/len(big); cy=sum(c[1] for c in big)/len(big)
        x,y=trA(cx,cy); p.text(x-9,y+5,est[cid]["sigla"],14,K if val[cid]>=20 and val[cid]<80 or val[cid]==20 else "#FFFFFF",style="Bold")
p.export(); p.close()

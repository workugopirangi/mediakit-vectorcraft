import sys,os
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
p=P("R42")
p.rect(0,0,1440,810,fill="#000000")
p.text(60,70,"Pathfinder: divide, minusFront, intersect, exclude, crop",26,"#FFFFFF",style="Regular")
pal=[CORAL,GOLD,MINT,CREAM,"#FFFFFF","#9FB7C8","#F5D80A"]
def pieces(ids,label,x,y):
    for k,i in enumerate(ids): 
        p.paint(i,pal[k%len(pal)])
    p.text(x,y,label,16,"#FFFFFF",style="Regular")
def allids():
    out=set()
    def w(n):
        if isinstance(n,dict):
            if "id" in n and n.get("kind")=="Path": out.add(n["id"])
            for v in n.values(): w(v)
        elif isinstance(n,list):
            for v in n: w(v)
    w(p.ex("document.inspect",{"depth":6})); return out
def op(cmd,shapes,label,x,y,recolor=True):
    p.ex("select.set",{"ids":shapes}); r=p.try_(cmd,{}); print(cmd,r)
    if r and recolor:
        p.try_("object.ungroup",{}); mx=max(shapes); new=sorted(i for i in allids() if i>mx)
        # peças = ids de Path que existem agora
        paths=[i for i in new]
        print("pecas",len(paths)); pieces(paths,label,x,y)
    return r
# 1 divide: dois circulos + retangulo
a=p.ell(180,230,110,110,fill="#fff"); b=p.ell(300,230,110,110,fill="#fff"); c=p.rect(150,170,200,120,fill="#fff")
op("object.pathfinder.divide",[a,b,c],"divide",120,400)
# 2 minusFront
a=p.rect(520,130,220,220,fill=GOLD); b=p.ell(740,240,100,100,fill=CORAL)
op("object.pathfinder.minusFront",[a,b],"minusFront",520,400,recolor=False)
# 3 intersect
a=p.ell(900,230,110,110,fill=MINT); b=p.ell(1020,230,110,110,fill=CORAL)
op("object.pathfinder.intersect",[a,b],"intersect",900,400,recolor=False)
# 4 exclude
a=p.rect(1180,130,180,180,fill=CREAM); b=p.ell(1300,300,100,100,fill=GOLD)
op("object.pathfinder.exclude",[a,b],"exclude",1180,400,recolor=False)
# 5 grade de losangos a partir de divide de linhas diagonais (blocos de grade adjacentes)
ids=[]
for i in range(-3,5):
    ids.append(p.path(f"M {120+i*120} 480 L {120+i*120+120} 480 L {120+i*120+120+200} 760 L {120+i*120+200} 760 Z",fill="#fff"))
r=op("object.pathfinder.divide",ids,"divide de paralelogramos adjacentes (seams?)",120,790)
# 6 losango com foto: crop
ph=p.ex("file.place",{"path":TRAT_S+"c-arena.jpg","link":False})["ids"][0]
p.ex("object.setBounds",{"ids":[ph],"x":900,"y":470,"width":420,"height":236,"reference":0})
d=p.path("M 1110 450 L 1330 590 L 1110 740 L 890 590 Z",fill=CORAL)
op("object.pathfinder.crop",[ph,d],"crop foto em losango",900,770,recolor=False)
p.export(); p.close()

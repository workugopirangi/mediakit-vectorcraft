import sys, time; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
p = P("R24")
p.rect(0,0,1440,810,fill=K)
p.imgcover(AMT+sorted(os.listdir(AMT))[0], 0, 0, 1440, 480)
p.rect(0,0,1440,480,fill=K,opacity=35)
p.text(80,330,"COPA AME",200,"Helvetica Neue","Condensed Black",color=Y)
# faixa de rodape com grade de icones (bola vetorial: circulo + pentagono + 5 raios)
def icone(cx,cy,r,col):
    ids=[p.ell(cx,cy,r,fill=None,stroke=col,sw=2.2)]
    pg=p.ex("shape.polygon",{"cx":cx,"cy":cy,"radius":r*0.42,"sides":5,"rotation":0})["id"]; p.paint(pg,col); ids.append(pg)
    import math
    d=""
    for k in range(5):
        a=math.radians(-90+72*k); d+=f"M{cx+r*0.42*math.cos(a):.2f},{cy+r*0.42*math.sin(a):.2f} L{cx+r*math.cos(a):.2f},{cy+r*math.sin(a):.2f} "
    ids.append(p.path(d,None,stroke=col,sw=2.2))
    p.ex("select.set",{"ids":ids}); g=p.ex("object.group",{}); p.ex("select.none")
    return g.get("id") or g["ids"][0]
t=time.time()
g=icone(60,520,26,Y)
p.ex("select.set",{"ids":[g]})
rg=p.ex("object.repeat.grid",{"rows":6,"cols":13,"hSpacing":50,"vSpacing":24})["id"]
print("grid",rg, p.ex("object.repeat.options",{"gridType":"brickByRow","flipRows":True}))
p.ex("select.none")
print("tempo grid vivo",round(time.time()-t,2))
t=time.time()
p.ex("select.set",{"ids":[rg]}); ex=p.ex("object.repeat.expand",{}); print("expand",str(ex)[:100],round(time.time()-t,2))
p.ex("select.none")
# retangulo cobrindo o texto de rodape sobre o grid
p.rect(80,740,640,50,fill=K); p.text(90,775,"Visibilidade em 3 dias de jogo",28,"Helvetica Neue","Bold",color=W)
p.export()

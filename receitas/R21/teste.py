import sys, math; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
p = P("R21")
p.imgcover(SPT+"c-portico.jpg", 0, 0, 1440, 810)
p.rect(0,0,1440,810,fill=SEA,opacity=45)
p.text(70,360,"EDIÇÃO",70,"Helvetica Neue","Condensed Black",color=CREAM)
p.text(70,470,"2027",190,"Helvetica Neue","Condensed Black",color=GOLD)
cx,cy=1000,405
ids=[]
ids.append(p.ell(cx,cy,185,fill=SEA,stroke=GOLD,sw=4))
ids.append(p.ell(cx,cy,172,fill=None,stroke=GOLD,sw=1.2))
ids.append(p.ell(cx,cy,108,fill=None,stroke=GOLD,sw=1.2))
SZ=30; SPC=3
def width(t):
    w=p.text(-2000,-2000,t,SZ,"Helvetica Neue","Condensed Black")
    p.ex("select.set",{"ids":[w]}); 
    for n in p.ex("document.inspect",{"depth":6,"childLimit":500}).get("layers",[]):
        pass
    return w
def meas(t):
    w=p.text(-2000,-2000,t,SZ,"Helvetica Neue","Condensed Black")
    ins=p.ex("document.find",{"text":t}); 
    # bounds via inspect
    def walk(n):
        if n.get("id")==w: return n["bounds"]
        for c in n.get("children",[]) or []:
            r=walk(c)
            if r: return r
    for l in p.ex("document.inspect",{"depth":6,"childLimit":500})["layers"]:
        r=walk(l)
        if r: break
    p.ex("edit.clear",{"ids":[w]})
    return r["width"]+len(t)*SPC
def ring(r,ccw,t,col=CREAM):
    sw=0 if not ccw else 0
    arc=f"A{r},{r} 0 1 {0 if ccw else 1}"
    d=f"M{cx-r},{cy} {arc} {cx+r},{cy} {arc} {cx-r},{cy} Z"
    pa=p.path(d,None)
    tid=p.ex("text.createInPath",{"path":pa,"mode":"onPath","text":t,"size":SZ,"font":"Helvetica Neue","style":"Condensed Black","color":col})["id"]
    C=2*math.pi*r; w=meas(t)
    st=0.25-(w/2)/C
    p.ex("select.set",{"ids":[tid]}); o=p.ex("type.pathOptions",{"start":st,"spacing":SPC,"alignToPath":"baseline"})
    print(t,"w",round(w),"start",round(st,3),o)
    return tid
ids.append(ring(137,False,"EDIÇÃO 2027 · OFICIAL"))
ids.append(ring(158,True,"SPRINT UBATUBA RUN"))
s=p.ex("shape.star",{"cx":cx,"cy":cy+4,"radius1":70,"radius2":30,"points":5})["id"]; p.paint(s,GOLD); ids.append(s)
p.ex("select.set",{"ids":ids}); print(p.ex("object.rotate",{"angle":-12}))
p.ex("select.none"); p.export()

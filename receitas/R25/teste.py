import sys, time; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
p = P("R25")
p.rect(0,0,1440,810,fill=SEA)
cx,cy=480,405
# raio: retangulo fino saindo do centro, repetido 24x
r=p.ex("shape.rectangle",{"x":cx-3,"y":cy-380,"width":6,"height":240})["id"]; p.paint(r,GOLD)
p.ex("select.set",{"ids":[r]})
rg=p.ex("object.repeat.radial",{"instances":24,"radius":380})["id"]
print(p.ex("object.repeat.options",{"center":[cx,cy],"instances":24,"radius":380}))
p.ex("select.none")
# conferir ids/angulos
p.ex("select.set",{"ids":[rg]}); ex=p.ex("object.repeat.expand",{}); p.ex("select.none")
print(ex)
# anel central e foto circular
p.ell(cx,cy,120,fill=SEA,stroke=GOLD,sw=3)
p.text(cx-86,cy+16,"2027",74,"Helvetica Neue","Condensed Black",color=CREAM)
# painel direito: rosa dos ventos 8 pontas + texto
p.imgcover(SPT+"f8.jpg",960,0,480,810)
p.rect(960,0,480,810,fill=SEA,opacity=55)
p.text(1000,380,"Do mar",70,"Helvetica Neue","Condensed Black",color=CREAM)
p.text(1000,450,"a serra",70,"Helvetica Neue","Condensed Black",color=GOLD)
p.export()

import sys; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
p = P("R28")
p.rect(0,0,1440,810,fill=SEA)
# blueprint: malha retangular fina + grade polar + espiral
g=p.ex("shape.rectangularGrid",{"x":0,"y":0,"width":1440,"height":810,"rows":27,"columns":48,"frame":False})["id"]
p.paint(g,None,stroke="#4C7C9A",sw=0.5)
g2=p.ex("shape.rectangularGrid",{"x":0,"y":0,"width":1440,"height":810,"rows":9,"columns":16,"frame":True})["id"]
p.paint(g2,None,stroke="#6FA3C0",sw=0.5)
pg=p.ex("shape.polarGrid",{"x":820,"y":90,"width":560,"height":560,"concentric":9,"radial":24})["id"]
p.paint(pg,None,stroke=GOLD,sw=0.5)
sp=p.ex("shape.spiral",{"cx":280,"cy":560,"radius":190,"decay":85,"segments":12})["id"]
p.paint(sp,None,stroke=CORAL,sw=0.5)
# painel de dados por cima
p.rect(70,70,560,260,fill=SEA,stroke=CREAM,sw=1)
p.text(100,170,"1.200",130,"Helvetica Neue","Condensed Black",color=GOLD)
p.text(100,230,"atletas por edicao",36,"Helvetica Neue","Medium",color=CREAM)
p.text(100,290,"alcance estimado 85 mil pessoas",26,"Helvetica Neue","Medium",color=MINT)
p.export()

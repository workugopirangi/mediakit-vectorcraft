import sys; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
p = P("R26")
p.rect(0,0,1440,810,fill=CREAM)
p.rect(0,0,1440,180,fill=SEA)
# ornamento: metade desenhada a esquerda do eixo x=720, espelho gera o resto
orn=[]
orn.append(p.path("M720,90 C 640,30 560,30 520,90 C 490,135 540,150 560,120",None,stroke=GOLD,sw=4))
orn.append(p.path("M720,120 C 660,95 600,95 570,125",None,stroke=GOLD,sw=2))
orn.append(p.ex("shape.star",{"cx":600,"cy":90,"radius1":14,"radius2":6,"points":5})["id"]); p.paint(orn[-1],MINT)
orn.append(p.ell(470,90,7,fill=CORAL))
p.ex("select.set",{"ids":orn[:2]}); p.ex("stroke.set",{"cap":"round","join":"round"})  # caps redondos fecham o V no eixo
p.ex("select.set",{"ids":orn})
r=p.ex("object.repeat.mirror",{"angle":90,"offset":0}); print(r)
p.ex("select.none")
p.text(720-190,115+0,"",10)
t=p.text(330,300,"SPRINT UBATUBA RUN",96,"Helvetica Neue","Condensed Black",color=SEA)
p.text(430,360,"Cotas de patrocinio 2027",42,"Avenir Next","Demi Bold",color=CORAL)
# moldura de foto espelhada: faixa inferior simetrica
p.imgcover(SPT+"c-tendas.jpg",200,430,1040,300)
p.export()

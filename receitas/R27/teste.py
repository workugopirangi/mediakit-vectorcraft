import sys, time, math; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
import random
p = P("R27")
p.rect(0,0,1440,810,fill=SEA)
p.imgcover(SPT+"c-arena.jpg",0,0,1440,810)
p.rect(0,0,1440,810,fill=SEA,opacity=62)
# simbolos: estrela dourada, bola (circulo coral) e retangulo menta (confete)
a=p.ex("shape.star",{"cx":100,"cy":100,"radius1":16,"radius2":7,"points":5})["id"]; p.paint(a,GOLD)
p.ex("select.set",{"ids":[a]}); s1=p.ex("symbol.new",{"name":"estrela"}); print(s1)
b=p.ell(150,100,9,fill=CORAL)
p.ex("select.set",{"ids":[b]}); s2=p.ex("symbol.new",{"name":"bola"}); print(s2)
c=p.rect(190,95,18,7,fill=MINT)
p.ex("select.set",{"ids":[c]}); s3=p.ex("symbol.new",{"name":"fita"}); print(s3)
p.ex("select.none")
print(p.ex("symbol.list",{}))
random.seed(7)
t=time.time()
# 1) spray: um arrasto de pontos (1 instancia por ponto; radius/density nao espalham em volta do ponto)
p.ex("symbol.setCurrent",{"name":"estrela"})
pts=[[1000+i*14,540+12*math.sin(i/2)] for i in range(25)]
print("spray arrasto",p.ex("symbol.spray",{"points":pts,"name":"estrela","radius":30,"density":8}))
# 2) confete natural: symbol.place + rotacao e escala aleatorias por instancia
n=0
for nm in ("estrela","bola","fita"):
    for k in range(34):
        x=random.uniform(60,1380); y=random.uniform(40,470)
        iid=p.ex("symbol.place",{"name":nm,"x":x,"y":y})["id"]
        p.ex("select.set",{"ids":[iid]})
        p.ex("object.rotate",{"angle":random.uniform(0,360)})
        p.ex("object.scale",{"sx":random.uniform(70,220)})
        n+=1
p.ex("select.none")
print("instancias com variacao",n,"tempo",round(time.time()-t,2))
p.text(120,640,"OBRIGADO, PARCEIROS",120,"Helvetica Neue","Condensed Black",color=CREAM)
p.text(120,720,"Sprint Ubatuba Run 2027",44,"Avenir Next","Demi Bold",color=GOLD)
p.export()

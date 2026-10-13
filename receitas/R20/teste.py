import sys; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
p = P("R20")
p.rect(0,0,1440,810,fill=SEA)
p.imgcover(SPT+"c-arena.jpg", 0, 0, 1440, 810)
p.rect(0,0,1440,810,fill=SEA,opacity=55)
# 1. arco
a=p.path("M120,330 C 380,60 760,60 1020,330",None,stroke=None)
t=p.ex("text.createInPath",{"path":a,"mode":"onPath","text":"CORRA PELO LITORAL NORTE","size":64,"font":"Helvetica Neue","style":"Condensed Black","color":CREAM})["id"]
print("arco",t)
# 2. onda S
b=p.path("M120,560 C 320,440 420,700 620,560 S 920,430 1100,560 S 1300,640 1340,560",None)
t2=p.ex("text.createInPath",{"path":b,"mode":"onPath","text":"Ubatuba Run 2027 · amendoeiras, mar e serra","size":40,"font":"Avenir Next","style":"Demi Bold","color":GOLD})["id"]
# 3. curva fechada em S apertada
c=p.path("M120,780 C 200,640 260,780 340,700 S 480,620 520,700",None)
t3=p.ex("text.createInPath",{"path":c,"mode":"onPath","text":"curva apertada em S","size":34,"font":"Futura","style":"Medium","color":MINT})["id"]
p.ex("select.set",{"ids":[t]}); print(p.ex("type.pathOptions",{"start":0.02,"alignToPath":"baseline","spacing":4}))
p.ex("select.set",{"ids":[t2]}); print(p.ex("type.pathOptions",{}))
p.ex("select.none")
p.export()

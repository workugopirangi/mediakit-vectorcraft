import sys,os
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
p=P("R43")
p.rect(0,0,1440,810,fill="#F4EFE2")
p.text(80,100,"Marca-texto e sublinhado irregular",30,K,style="Regular")
# A: marca-texto = retangulo amarelo + roughen, Multiply, atras do texto
t=p.text(80,260,"500 atletas em 2026",90,K,style="Bold")
h=p.rect(76,215,630,52,fill=Y)   # criado depois: fica acima do texto, usa Multiply
p.ex("select.set",{"ids":[h]})
print("rough",p.try_("effect.apply",{"effect":"distort.roughen","ids":[h],"params":{"size":3,"relative":False,"detail":25,"points":"smooth","seed":4}}))
print("mult",p.try_("transparency.set",{"ids":[h],"blend":"Multiply"}))
# B: marca-texto como traco grosso com cap round, path irregular
t2=p.text(80,430,"meta 2027: 1.200",90,K,style="Bold")
hl=p.path("M 84 410 C 250 402 420 416 620 405 S 740 408 760 406",fill=None,stroke=CORAL,sw=46)
p.ex("select.set",{"ids":[hl]}); p.try_("stroke.set",{"weight":46,"cap":"round","join":"round"})
p.ex("transparency.set",{"ids":[hl],"blend":"Multiply","opacity":85})
# C: sublinhado irregular com scribble numa faixa fina
t3=p.text(80,600,"187.000 visualizações",72,K,style="Bold")
u=p.rect(80,618,560,16,fill=SEA); p.ex("select.set",{"ids":[u]})
print("scribble",p.try_("effect.apply",{"effect":"stylize.scribble","ids":[u],"params":{"angle":-8,"strokeWidth":3,"spacing":4,"curviness":30,"variation":1.5,"seed":2}}))
# D: sublinhado com brush artistico/caligrafico
t4=p.text(780,600,"52% turistas",72,K,style="Bold")
ul=p.path("M 784 640 C 900 630 1000 650 1180 636 S 1300 640 1330 634",fill=None,stroke=CORAL,sw=8)
print("brush",p.try_("brush.new",{"type":"calligraphic","name":"marca","params":{"angle":20,"roundness":30,"size":10}}))
print("apply",p.try_("brush.apply",{"name":"marca","ids":[ul]}))
# E: roughen em traco aberto: variantes
for k,(y,params,pre) in enumerate([(440,{"size":4,"relative":False,"detail":30,"points":"smooth","seed":9},None),(500,{"size":1.2,"relative":False,"detail":10,"points":"smooth","seed":9},None),(560,{"size":3,"relative":False,"detail":30,"points":"smooth","seed":9},"outline")]):
    r2=p.path(f"M 800 {y} L 1300 {y}",fill=None,stroke=MINT,sw=30)
    p.ex("select.set",{"ids":[r2]}); p.try_("stroke.set",{"weight":30,"cap":"round"})
    if pre: print("outline",p.try_("object.path.outlineStroke",{}))
    print("rough",k,p.try_("effect.apply",{"effect":"distort.roughen","params":params}))
    p.ex("transparency.set",{"blend":"Multiply"}) if False else None
p.export(); p.close()

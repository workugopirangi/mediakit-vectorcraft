import sys,os
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
p=P("R35")
p.rect(0,0,1440,810,fill="#07131c")
# foto f1 (retrato) a direita, setBounds topo-esquerda
r=p.ex("file.place",{"path":TRAT_S+"f1.jpg","link":False}); pid=r["id"] if isinstance(r,dict) and "id" in r else None; print("place",r)
if pid is None: pid=r["ids"][0]
p.ex("object.setBounds",{"ids":[pid],"x":860,"y":0,"width":580,"height":795,"reference":0})
# holofote 1: radial centrada no atleta, sobre a foto, Screen. stop 0 claro opaco -> stop 1 mesmo cor com opacity 0
h1=p.ell(1150,380,420,420,fill=None,gradient={"kind":"radial","stops":[{"offset":0,"color":GOLD,"opacity":0.85},{"offset":1,"color":GOLD,"opacity":0}]})
p.ex("transparency.set",{"ids":[h1],"blend":"Screen"})
# holofote 2: atras do titulo, mint, aspect 40% (elipse), sem blend
h2=p.rect(40,150,820,420,fill=None,gradient={"kind":"radial","aspect":45,"stops":[{"offset":0,"color":MINT,"opacity":0.55},{"offset":0.6,"color":MINT,"opacity":0.15},{"offset":1,"color":MINT,"opacity":0}]})
p.text(90,330,"500 ATLETAS",96,"#FFFFFF"); p.text(90,420,"META 2027: 1.200",64,CREAM,style="Regular")
# holofote 3: focal deslocado (facho de luz vindo do canto)
h3=p.rect(90,560,520,200,fill=None,gradient={"kind":"radial","stops":[{"offset":0,"color":CORAL},{"offset":1,"color":"#07131c"}]})
r=p.try_("paint.setGradientGeom",{"ids":[h3],"start":[350,660],"end":[610,660],"focal":[200,620],"stroke":False}); print("focal",r)
p.text(100,780,"focal deslocado (0.5 do raio a esquerda)",16,"#FFFFFF",style="Regular")
# controle: radial opaco para comparar com anel cinza (transparente por opacity 0 da mesma cor) vs por cor escura
h4=p.ell(700,700,90,90,fill=None,gradient={"kind":"radial","stops":[{"offset":0,"color":"#FFFFFF","opacity":1},{"offset":1,"color":"#000000","opacity":0}]})
p.text(620,820-30,"opacity->0 com cor preta (teste anel cinza)",14,"#FFFFFF",style="Regular")
p.export(); p.close()

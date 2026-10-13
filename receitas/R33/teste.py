import sys, time; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
p = P("R33")
p.rect(0,0,1440,810,fill=K)
from PIL import Image
f=SPT+"f10.jpg"; w,h=Image.open(f).size; print(w,h)
# mosaico a partir da foto: colunas/linhas proporcionais
bw=520; bh=bw*h/w
o=p.img(f,60,110,bw,bh)
p.ex("select.set",{"ids":[o]})
t=time.time()
r=p.ex("object.createObjectMosaic",{"columns":40,"rows":int(40*h/w),"spacingX":2,"spacingY":2,"width":bw,"height":bh})
print(r,round(time.time()-t,2)); p.ex("select.none")
o2=p.img(f,700,110,bw*0.7,bh*0.7)
p.text(60,80,"mosaico 40 colunas",28,color=Y); p.text(700,80,"foto original",28,color=Y)
p.export()

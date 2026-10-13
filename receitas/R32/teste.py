import sys, time; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
p = P("R32")
p.rect(0,0,1440,810,fill=K)
rep=[]
# A: foto posterizada em 4 cores
from PIL import Image
f=SPT+"f4.jpg"; w,h=Image.open(f).size; bw=400; bh=bw*h/w
o=p.img(f,50,120,bw,bh)
t=time.time()
r=p.ex("imageTrace.makeAndExpand",{"id":o,"params":{"mode":"color","palette":"limited","colors":4,"paths":60,"corners":50,"noise":8,"method":"abutting"}})
rep.append(("foto 4 cores",r,round(time.time()-t,2)))
# B: foto 3 cores com fundo diferente
o=p.img(f,480,120,bw,bh)
t=time.time()
r=p.ex("imageTrace.makeAndExpand",{"id":o,"params":{"mode":"color","palette":"limited","colors":3,"paths":80,"corners":60,"noise":15,"method":"abutting"}})
rep.append(("foto 3 cores",r,round(time.time()-t,2)))
# C: logo AME raster -> vetor
logo=AM+"logo-ame-320-x3.png"; lw,lh=Image.open(logo).size
print("logo",lw,lh)
lo=p.img(logo,920,150,420,420*lh/lw)
t=time.time()
r=p.ex("imageTrace.makeAndExpand",{"id":lo,"params":{"mode":"color","palette":"limited","colors":2,"ignoreWhite":True,"noise":30,"paths":90,"corners":90,"method":"abutting"}})
rep.append(("logo",r,round(time.time()-t,2)))
lo2=p.img(logo,920,520,200,200*lh/lw)
for x in rep: print(x)
p.text(50,90,"foto 4 cores",26,color=Y); p.text(480,90,"foto 3 cores",26,color=Y); p.text(920,90,"logo vetorizado",26,color=Y)
p.export()

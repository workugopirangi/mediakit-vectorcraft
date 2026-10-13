import sys, time; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
p = P("R29")
p.rect(0,0,1440,810,fill=SEA)
res=[]
def halftone(f,x,y,w,h,freq,color,angle=45,shape="circle",clip=True,invert=False):
    im=p.img(f,x,y,w,h)
    # recorte "cover"
    t=time.time()
    p.ex("select.set",{"ids":[im]})
    r=p.ex("object.vectorHalftone",{"shape":shape,"frequency":freq,"angle":angle,"mode":"mono","color":color,"clip":clip,"invert":invert})
    dt=time.time()-t; p.ex("select.none"); res.append((freq,r.get("dots"),round(dt,2))); return r
from PIL import Image
f=SPT+"f1.jpg"; iw,ih=Image.open(f).size
# foto toda 935x1280 -> caixa 420x575
halftone(f,60,100,420,575,12,GOLD,invert=True)
halftone(f,510,100,420,575,20,CREAM,invert=True)
halftone(f,960,100,420,575,30,CORAL,invert=True)
print(res)
p.text(60,740,"12 lpi",30,color=CREAM); p.text(510,740,"20 lpi",30,color=CREAM); p.text(960,740,"30 lpi",30,color=CREAM)
p.text(60,70,"SPRINT UBATUBA RUN  |  halftone vetorial",36,"Helvetica Neue","Bold",color=GOLD)
p.export()

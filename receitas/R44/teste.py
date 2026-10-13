import sys,os
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
p=P("R44")
p.rect(0,0,1440,810,fill=K)
p.text(60,80,"Largura variável (swoosh)",30,Y,style="Regular")
def sw(d,color,w,**sp):
    i=p.path(d,fill=None,stroke=color,sw=w); p.ex("select.set",{"ids":[i]}); p.try_("stroke.set",{"weight":w,"cap":"round",**sp}); return i
a=sw("M 80 300 C 400 100 700 500 1000 200",Y,40,profile="taperEnd"); print("a")
b=sw("M 80 400 C 400 200 700 600 1000 300",CORAL,40,profile="lens")
c=sw("M 80 500 C 400 300 700 700 1000 400","#FFFFFF",40,profile="taperStart")
d=sw("M 80 600 C 400 400 700 800 1000 500",MINT,40,profile="wave")
# perfil custom por pontos
e=sw("M 1100 150 C 1250 300 1100 450 1300 700",GOLD,50)
print("wp",p.try_("stroke.widthProfile.set",{"ids":[e],"points":[[0,0.05,0.05],[0.3,1,1],[0.6,0.4,0.4],[1,0.02,0.02]]}))
f=sw("M 1350 150 C 1250 300 1380 450 1180 700",CREAM,50)
print("wpt",p.try_("stroke.widthPoint.set",{"id":f,"t":0.5,"left":30,"right":4}))
print("wpt2",p.try_("stroke.widthPoint.set",{"id":f,"t":0.0,"left":1,"right":1}))
print("wpt3",p.try_("stroke.widthPoint.set",{"id":f,"t":1.0,"left":1,"right":1}))
p.export(); p.close()

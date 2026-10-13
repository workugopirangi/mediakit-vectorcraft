import sys,os
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
p=P("R38")
p.rect(0,0,1440,810,fill=SEA)
p.text(60,90,"Envelope warp em títulos de seção",30,CREAM,style="Regular")
items=[("arc","ARCO",50,0),("flag","BANDEIRA",40,0),("wave","ONDA",40,0),("bulge","INCHAÇO",35,0)]
pos=[(60,200),(760,200),(60,520),(760,520)]
for (st,t,b,h),(x,y) in zip(items,pos):
    tid=p.text(x,y+120,t,130,GOLD,font="Helvetica Neue",style="Condensed Black")
    p.ex("select.set",{"ids":[tid]})
    r=p.try_("object.envelope.makeWithWarp",{"ids":[tid],"style":st,"bend":b,"h":h,"v":0}); print(st,r)
    p.text(x,y+250 if y<400 else y+250,st+f" bend {b}",16,"#FFFFFF",style="Regular")
    if st in("flag","bulge"):
        p.ex("select.set",{"ids":[r["id"]]}); print("expand",p.try_("object.envelope.expand",{}))
p.export(); p.close()

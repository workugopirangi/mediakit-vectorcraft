import sys,os
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
p=P("R37")
p.rect(0,0,1440,810,fill="#07131c")
def mesh_shape(cx,cy,r,rows,cols,colors,label,expand=False):
    o=p.ell(cx,cy,r,r,fill=GOLD)
    p.ex("select.set",{"ids":[o]})
    m=p.ex("object.mesh.create",{"ids":[o],"rows":rows,"cols":cols,"appearance":"flat"})
    mid=m["ids"][0]
    n=(rows+1)*(cols+1)
    for i in range(n):
        p.try_("object.mesh.setPointColor",{"id":mid,"index":i,"color":colors[i%len(colors)]})
    p.text(cx-r,cy+r+30,label,18,"#FFFFFF",style="Regular")
    return mid
cols=[GOLD,CORAL,CREAM,MINT,SEA]
m1=mesh_shape(250,300,170,4,4,cols,"mesh 4x4")
m2=mesh_shape(720,300,170,2,2,[CORAL,GOLD,CREAM],"mesh 2x2")
m3=mesh_shape(1190,300,170,4,4,[MINT,SEA,CORAL,GOLD],"mesh 4x4 expandido (peças planas)")
p.ex("select.set",{"ids":[m3]}); print(p.try_("object.mesh.expand",{}))
# retangulo mesh
o=p.rect(120,620,1200,120,fill=GOLD); p.ex("select.set",{"ids":[o]})
mm=p.ex("object.mesh.create",{"ids":[o],"rows":3,"cols":8,"appearance":"flat"})
for i in range(4*9): p.try_("object.mesh.setPointColor",{"id":mm["ids"][0],"index":i,"color":[CORAL,GOLD,MINT,SEA][(i//9+i%9)%4]})
p.export(); p.close()

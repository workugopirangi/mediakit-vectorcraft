import sys, math; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
p = P("R22")
p.rect(0,0,1440,810,fill=SEA)
p.imgcover(SPT+"c-doacao.jpg", 0, 0, 480, 810)
p.rect(0,0,480,810,fill=SEA,opacity=50)
def medal(cx,cy,R,col,label,txtcol):
    ids=[]
    # sunburst dentado
    s=p.ex("shape.star",{"cx":cx,"cy":cy,"radius1":R,"radius2":R*0.93,"points":24})["id"]; p.paint(s,col); ids.append(s)
    p.ex("select.set",{"ids":[s]}); 
    r=p.ex("effect.apply",{"effect":"stylize.roundCorners","params":{"radius":R*0.02}})
    p.ex("select.set",{"ids":[s]}); o=p.ex("object.path.offsetPath",{"offset":-R*0.11,"joins":"round"})
    p.paint(o["ids"][0],None,stroke=txtcol,sw=2); ids.append(o["ids"][0])
    ids.append(p.ell(cx,cy,R*0.62,fill=None,stroke=txtcol,sw=1.5))
    t=p.text(cx-R*0.5,cy+R*0.12,label,R*0.36,"Helvetica Neue","Condensed Black",color=txtcol)
    p.ex("select.none")
    return ids
medal(760,260,170,GOLD,"OURO",SEA)
medal(1090,250,130,"#C9CED3","PRATA",SEA)
medal(1280,560,100,"#C07A43","BRONZE",CREAM)
# poligono + offsetPath (anel concentrico)
pg=p.ex("shape.polygon",{"cx":760,"cy":620,"radius":110,"sides":8})["id"]; p.paint(pg,CORAL)
p.ex("select.set",{"ids":[pg]}); off=p.ex("object.path.offsetPath",{"offset":-14,"joins":"round"}); print(off)
p.paint(off["ids"][0],None,stroke=CREAM,sw=2)
p.text(540,760,"COTA OURO  1 vaga",30,color=CREAM)
p.export()

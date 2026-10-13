import sys,os
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
p=P("R36")
p.try_("document.rasterEffectsSettings",{"resolution":300})
b=p.rect(0,0,1440,810,fill=SEA)   # fundo solido primeiro
p.ex("select.set",{"ids":[b]})
p.ex("paint.editGradient",{"ids":[b],"stroke":False,"kind":"freeform","mode":"points","stops":[{"offset":0,"color":SEA},{"offset":0.5,"color":MINT},{"offset":1,"color":CORAL}]})
g=p.ex("paint.freeform.get",{"stroke":False}); print(len(g["points"]),"pontos automaticos")
# recolore pontos existentes? addPoint com cor e spread
for at,c,sp in [([200,150],CORAL,0.3),([1250,150],GOLD,0.3),([700,720],MINT,0.3),([1300,700],SEA,0.2),([100,700],"#7A3E8E",0.2)]:
    r=p.ex("paint.freeform.addPoint",{"ids":[b],"stroke":False,"at":at,"color":c,"spread":sp})
p.ex("paint.freeform.addLine",{"ids":[b],"points":[r["index"]-4,r["index"]-3]}) if False else None
g=p.ex("paint.freeform.get",{"stroke":False}); print(len(g["points"]),"pontos total")
p.text(90,330,"AURORA",140,"#FFFFFF"); p.text(90,410,"Sprint Ubatuba Run 2027: 187.000 visualizações",36,CREAM,style="Regular")
# bloco menor freeform (card)
c=p.rect(900,460,440,280,fill=SEA,radius=24); p.ex("select.set",{"ids":[c]})
p.ex("paint.editGradient",{"ids":[c],"stroke":False,"kind":"freeform","mode":"lines","stops":[{"offset":0,"color":CORAL},{"offset":1,"color":GOLD}]})
p.text(930,620,"500 → 1.200",56,K)
p.export(); p.close()

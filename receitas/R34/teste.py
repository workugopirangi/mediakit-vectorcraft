import sys,os
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
p=P("R34")
# fundo: linear sea->darker, 2 stops, angulo 90 (deg)
bg=p.rect(0,0,1440,810,fill=None,gradient={"kind":"linear","angle":90,"stops":[{"offset":0,"color":"#14507A"},{"offset":1,"color":SEA}]})
print("bg",bg)
# bloco gold -> cream angulo 45
p.rect(80,300,380,300,fill=None,gradient={"kind":"linear","angle":45,"stops":[{"offset":0,"color":GOLD},{"offset":1,"color":CREAM}]})
# bloco coral->gold, 3 stops com midpoint
p.rect(500,300,380,300,fill=None,gradient={"kind":"linear","angle":0,"stops":[{"offset":0,"color":CORAL},{"offset":0.5,"color":"#F08A4B","midpoint":0.3},{"offset":1,"color":GOLD}]})
# bloco escuro a escuro (teste banding)
p.rect(920,300,440,300,fill=None,gradient={"kind":"linear","angle":90,"stops":[{"offset":0,"color":"#0B0B0C"},{"offset":1,"color":"#26262A"}]})
p.text(80,200,"SPRINT UBATUBA RUN 2027",64,CREAM,style="Bold")
p.text(80,250,"Gradiente linear de marca: 2 stops, 3 stops com midpoint, e escuro a escuro",22,"#FFFFFF",style="Regular")
p.text(80,660,"45 graus",20,"#FFFFFF"); p.text(500,660,"0 graus, 3 stops",20,"#FFFFFF"); p.text(920,660,"escuro a escuro (banding?)",20,"#FFFFFF")
# setGradientGeom: bloco com vetor explicito
b=p.rect(80,700,1280,60,fill=None,gradient={"kind":"linear","stops":[{"offset":0,"color":MINT},{"offset":1,"color":CORAL}]})
r=p.try_("paint.setGradientGeom",{"ids":[b],"start":[80,730],"end":[1360,730],"stroke":False}); print("geom",r)
p.export(); p.close()

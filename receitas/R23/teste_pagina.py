import sys; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
p = P("R23")
# pagina de abertura de secao da AME: fundo amarelo com padrao de bolas desenhadas por IA (hexByRow)
p.rect(0,0,1440,810,fill=Y)
im=p.img(R+"R23/assets/bola-460.png",10,10,110,110)
p.ex("select.set",{"ids":[im]})
nm=p.ex("object.pattern.make",{"tileType":"hexByRow","name":"bolas","width":170,"height":170})["name"]
p.ex("object.pattern.done",{}); p.ex("edit.clear",{"ids":[im]})
r=p.rect(0,0,1440,810,fill=None)
p.ex("select.set",{"ids":[r]}); p.ex("paint.setFill",{"swatch":nm}); p.ex("transparency.set",{"ids":[r],"opacity":38}); p.ex("select.none")
# cartao preto com titulo e foto recortada
p.rect(70,150,760,510,fill=K)
p.text(120,300,"COPA AME",150,"Helvetica Neue","Condensed Black",color=Y)
p.text(120,410,"Cotas de patrocinio 2027",52,"Helvetica Neue","Bold",color=W)
p.text(120,490,"Visibilidade para a sua marca em",30,"Helvetica Neue","Medium",color=W)
p.text(120,530,"3 dias de jogo, 40 times, 1.200 criancas.",30,"Helvetica Neue","Medium",color=W)
p.img(AM+"real-goleiro-recorte.png",880,60,420,690) if False else None
p.export()

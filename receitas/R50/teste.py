import sys,os
sys.path.insert(0,os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/_s34"))
from h34 import *
p=P("R50")
p.rect(0,0,1440,810,fill=SEA)
p.text(60,100,"Sprint Ubatuba Run: os números de 2027",30,CREAM,style="Regular")
cards=[("1.200","atletas","META 2027","de 500 em 2026",GOLD),("500","mil","VISUALIZAÇÕES","meta, contra 187 mil em 2026",CORAL),("52","%","PÚBLICO TURISTA","de 1.300 pessoas no evento",MINT)]
X=[60,520,980]; W=400
for (num,unit,lab,sub,col),x in zip(cards,X):
    p.rect(x,160,W,520,fill="#0b2a40",radius=18)
    p.rect(x+36,224,60,5,fill=col)                       # filete de cor
    lt=p.text(x+36,270,lab,20,col,style="Bold"); p.try_("text.setRangeStyle",{"id":lt,"tracking":160})
    tid=p.text(x+36,460,num+unit,150,"#FFFFFF",font="Helvetica Neue",style="Condensed Black")
    n=len(num.encode())
    # unidade pequena em superscript via range (offsets em BYTES)
    p.try_("text.setRangeStyle",{"id":tid,"start":n,"end":n+len(unit.encode()),"size":50 if unit!="%" else 150,"position":"superscript" if unit=="%" else "normal","baselineShift":0 if unit=="%" else 0,"fill":col})
    p.rect(x+36,530,W-72,1.5,fill="#FFFFFF",opacity=35)   # regua fina
    p.text(x+36,580,sub,22,"#FFFFFF",style="Regular")
p.text(60,740,"numeral Condensed Black 220 pt, unidade 80 pt em cor (setRangeStyle), régua 1,5 pt, rótulo com tracking 160",16,"#FFFFFF",style="Regular")
p.export(); p.close()

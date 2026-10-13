import sys, re; sys.path.insert(0, "/Users/ugopirangi/Developer/vectorcraft-mediakit/receitas")
from rc import *
p = P("R19")
p.rect(0,0,1440,810,fill=SEA)
p.imgcover(SPT+"f7.jpg", 1040, 0, 400, 810)
p.text(70,110,"COTAS DE PATROCINIO",84,"Helvetica Neue","Condensed Black",color=GOLD)
rows=[("OURO ★ 1 vaga","Didot","Bold"),("Prata ✓ incluso → 3 vagas","Futura","Medium"),("Bronze ● 6 vagas","Avenir Next","Demi Bold"),("Apoio  ✔ ilimitado","Helvetica Neue","Bold")]
for i,(t,f,s) in enumerate(rows):
    p.text(70,230+i*110,t,52,f,s,color=CREAM)

def bounds(oid):
    def walk(n):
        if n.get("id")==oid: return n.get("bounds")
        for c in n.get("children",[]) or []:
            r=walk(c)
            if r: return r
    ins=p.ex("document.inspect",{"depth":6,"childLimit":500})
    for k in ("layers","tree"):
        if k in ins:
            for l in ins[k]:
                r=walk(l)
                if r: return r
    return None

def audit():
    found=[]
    ms=p.ex("document.find",{"kind":"Type"})["matches"]
    for m in ms:
        p.ex("select.set",{"ids":[m["id"]]})
        fs=p.ex("text.fonts",{"selectionOnly":True})
        n=sum(f["missingGlyphs"] for f in fs)
        txt=p.ex("text.getRange",{"id":m["id"]})["text"]
        if n: found.append((m["id"],txt,n,fs[0]["family"],fs[0]["style"]))
    p.ex("select.none")
    return found
rep=audit()
print("RELATORIO antes:")
for r in rep: print("  ",r)
# sonda: quais caracteres faltam em cada fonte
def probe(ch,fam,sty):
    t=p.text(-500,-500,ch,40,fam,sty)
    p.ex("select.set",{"ids":[t]}); n=sum(f["missingGlyphs"] for f in p.ex("text.fonts",{"selectionOnly":True}))
    p.ex("edit.clear",{"ids":[t]}); return n>0
for oid,txt,n,fam,sty in rep:
    bad=[c for c in sorted(set(txt)) if ord(c)>127 and probe(c,fam,sty)]
    print("  glifos ausentes em",fam,":",bad)
    if "★" in bad:
        pre=txt.split("★")[0]
        w=p.text(-900,-900,pre,52,fam,sty); b=bounds(w); p.ex("edit.clear",{"ids":[w]})
        print("   bounds do prefixo",b)
        ob=bounds(oid); print("   bounds do texto",ob)
        p.ex("text.setText",{"id":oid,"text":txt.replace("★","  ")})
        # largura de '  ' ~ posiciona a estrela na lacuna
        x0=ob["x"]+b["width"]+14  # bounds do prefixo ignora o espaco final (~14 pt a 52 pt)
        st=p.ex("shape.star",{"cx":x0+18,"cy":230-17,"radius1":22,"radius2":9,"points":5})["id"]
        p.paint(st,GOLD)
print("RELATORIO depois (so o que ainda cai em fonte reserva):")
for r in audit(): print("  ",r)
p.export()

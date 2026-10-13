import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h import *
p = P("R12"); ex = p.ex
p.rect(0, 0, 1440, 810, K)
nums = "11.111\n88.888\n12.480\n7.071\n1.000"
def col(x, label, font, style, feats):
    p.text(x, 90, label, "Helvetica Neue", "Bold", 13, GOLD, tracking=200)
    if font == "Arboria": font, style = "Arboria-Bold", "☞"
    t = p.text(x, 190, nums, font, style, 54, "#FFFFFF", leading=64)
    if feats:
        ex("text.setStyle", {"ids": [t], "features": feats})
    return t
col(60, "HELVETICA NEUE, PADRÃO", "Helvetica Neue", "Bold", None)
col(60 + 330, "HELVETICA NEUE, tnum", "Helvetica Neue", "Bold", ["tnum"])
col(60 + 660, "ARBORIA, PADRÃO", "Arboria", "Bold", None)
col(60 + 990, "ARBORIA, pnum (proporcional)", "Arboria", "Bold", ["pnum"])
# versaletes e alternativos
lab = "Audiência qualificada 2027"
y = 560
for i, (f, feat, nm) in enumerate([("Arboria", None, "padrão"), ("Arboria", ["smcp"], "smcp"), ("Arboria", ["liga","dlig"], "liga+dlig"), ("Arboria", ["onum"], "onum"), ("Arboria", ["ss01"], "ss01"), ("Arboria", ["lnum"], "lnum")]):
    txt = lab if nm not in ("onum", "lnum", "ss01") else "Ouro 0123456789 & Ago gato"
    fam, sty = ("Avenir Next", "Medium") if nm == "smcp" else ("Arboria-Medium", "☞")
    t = p.text(60 if i < 3 else 760, y + (i % 3) * 56, txt, fam, sty, 30, "#FFFFFF")
    if feat: ex("text.setStyle", {"ids": [t], "features": feat})
    p.text(60 if i < 3 else 760, y + (i % 3) * 56 + 18, nm, "Helvetica Neue", "Bold", 10, GOLD, tracking=150)
print([ (x["family"],x["style"],x["status"],x["missingGlyphs"]) for x in ex("text.fonts", {})])
p.export()

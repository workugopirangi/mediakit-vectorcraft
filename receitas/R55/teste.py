import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h5166 import *
d = Doc("R55")
for nm, c in [("Marca", Y), ("Tinta", K), ("Apoio", "#FFFFFF")]:
    print(d.ex("swatch.new", {"name": nm, "color": c, "global": True}))
def sw(oid, name, stroke=False):
    d.ex("select.set", {"ids": [oid]}); d.ex("paint.setStrokes" if False else "paint.setFill", {"swatch": name}); d.ex("select.none")
bg = d.rect(0, 0, 1440, 810, K); sw(bg, "Marca")
ph = d.image(AM + "/tratado/c-master.jpg", 720, 0, 720, 405)
m = d.rect(720, 0, 720, 405, K)
d.ex("select.set", {"ids": [ph, m]}); d.ex("object.clippingMask.make"); d.ex("select.none")
t = d.text(60, 250, "COPA AME", "Helvetica Neue", "Condensed Black", 150, K); sw(t, "Tinta")
t2 = d.text(60, 330, "Dez mil atletas por semestre.", "Helvetica Neue", "Bold", 34, K); sw(t2, "Tinta")
for i in range(3):
    r = d.rect(60 + i * 220, 460, 200, 240, K, radius=20); sw(r, "Tinta")
    tt = d.text(80 + i * 220, 540, ["OURO", "PRATA", "BRONZE"][i], "Helvetica Neue", "Condensed Black", 44, "#FFFFFF"); sw(tt, "Marca")
    e = d.ellipse(80 + i * 220, 580, 60, 60, "#FFFFFF"); sw(e, "Marca")
# gradiente que usa a cor de marca
g = d.rect(720, 405, 720, 405, K)
d.ex("select.set", {"ids": [g]})
d.ex("paint.setFill", {"gradient": {"kind": "linear", "angle": 90, "stops": [{"offset": 0, "swatch": "Marca"}, {"offset": 1, "swatch": "Tinta"}]}})
d.ex("select.none")
d.export("teste-ame.pdf")
# REBRAND: trocar o swatch muda tudo
print(d.ex("swatch.edit", {"name": "Marca", "color": GOLD}))
print(d.ex("swatch.edit", {"name": "Tinta", "color": SEA}))
d.export("teste-sprint.pdf")
os.system(f"cd {d.dir}; cp preview-1.png preview-sprint.png")
d.close()

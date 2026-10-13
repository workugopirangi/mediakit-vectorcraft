import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h5166 import *
d = Doc("R51")
d.rect(0, 0, 1440, 810, CREAM)
im = d.image(SP + "/tratado/c-arena.jpg", 0, -250, 1440)
m = d.rect(0, 0, 1440, 300, K)
d.ex("select.set", {"ids": [im, m]}); d.ex("object.clippingMask.make"); d.ex("select.none")
d.rect(0, 0, 1440, 300, SEA, opacity=60)
d.text(70, 150, "COTAS DE PATROCÍNIO", "Helvetica Neue", "Condensed Black", 72, CREAM)
d.text(70, 195, "Sprint Ubatuba Run 2027: cartões com sombra macia (raster) e sombra dura (vetor)", "Helvetica Neue", "Medium", 18, MINT)
labels = [("OURO", "R$ 80 mil", "Sombra macia: blur 24, y 16"), ("PRATA", "R$ 40 mil", "Sombra macia curta: blur 8, y 6"), ("BRONZE", "R$ 20 mil", "Sombra dura vetorial: cópia +14/+14")]
hdr = [GOLD, SEA, CORAL]
for i, (n, v, t) in enumerate(labels):
    x = 70 + i * 450
    if i == 2:
        d.rect(x + 14, 354, 380, 380, K)
    c = d.rect(x, 340, 380, 380, "#FFFFFF")
    if i < 2:
        b, y_, o = (24, 16, 45) if i == 0 else (8, 6, 60)
        d.ex("select.set", {"ids": [c]})
        d.ex("effect.apply", {"effect": "stylize.dropShadow", "params": {"blur": b, "x": 0, "y": y_, "opacity": o, "color": "#0F3550", "mode": "multiply"}})
        d.ex("select.none")
    d.rect(x, 340, 380, 70, hdr[i])
    d.text(x + 28, 388, n, "Helvetica Neue", "Condensed Black", 40, K if i == 0 else "#FFFFFF")
    d.text(x + 28, 500, v, "Helvetica Neue", "Bold", 54, SEA)
    d.text(x + 28, 540, "por edição", "Helvetica Neue", "Medium", 18, SEA)
    d.text(x + 28, 690, t, "Helvetica Neue", "Medium", 15, SEA)
d.ex("document.rasterEffectsSettings", {"resolution": 300})
p = d.export()
report(p)
d.ex("document.rasterEffectsSettings", {"resolution": 72})
p2 = d.export("teste-72.pdf"); report(p2)
d.close()

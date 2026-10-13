import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h import *
p = P("R09"); ex = p.ex
ex("document.rasterEffectsSettings", {"resolution": 150})
p.rect(0, 0, 1440, 810, "#FF00FF")  # magenta: halo da borda apareceria
# fundo: foto 120 pt maior que a pagina, desfocada, recortada na pagina
im = p.img(PH + "c-arena.jpg", -80, -45, 1600, 900)
ex("select.set", {"ids": [im]}); ex("effect.apply", {"effect": "blur.gaussian", "params": {"radius": 14}})
m = p.rect(0, 0, 1440, 810, "#FF0000"); ex("select.set", {"ids": [m]}); ex("object.arrange.bringToFront", {})
ex("select.set", {"ids": [im, m]}); print(ex("object.clippingMask.make", {}))
sc = p.rect(0, 0, 1440, 810, K); ex("transparency.set", {"ids": [sc], "opacity": 45})
p.text(90, 330, "12.000", "Helvetica Neue", "Condensed Black", 260, "#FFFFFF", tracking=-10)
p.text(96, 400, "CORREDORES EM 3 DIAS DE EVENTO", "Helvetica Neue", "Bold", 40, GOLD, tracking=200)
p.text(96, 460, "Fundo desfocado, texto nítido por cima.", "Helvetica Neue", "Medium", 24, "#FFFFFF")
# controle: foto exatamente nos limites, desfocada (mostra halo)
c = p.img(PH + "c-arena.jpg", 960, 520, 400, 225)
ex("select.set", {"ids": [c]}); ex("effect.apply", {"effect": "blur.gaussian", "params": {"radius": 14}})
p.text(960, 505, "CONTROLE SEM SANGRIA", "Helvetica Neue", "Bold", 14, "#FFFFFF", tracking=100)
p.export()

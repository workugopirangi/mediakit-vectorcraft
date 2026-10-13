import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h import *
p = P("R10"); ex = p.ex
p.rect(0, 0, 1440, 810, W)
def rough(x, y, w, h, fill, seed, size=4, detail=7):
    r = p.rect(x, y, w, h, fill)
    ex("select.set", {"ids": [r]})
    ex("effect.apply", {"effect": "distort.roughen", "params": {"size": size, "relative": False, "detail": detail, "points": "smooth", "seed": seed}})
    return r
def torn(photo, x, y, w, h, ph_w, ph_h, seed, rot=0):
    shadow = rough(x - 22, y - 18, w + 44, h + 36, "#000000", seed + 50, size=3)
    ex("transparency.set", {"ids": [shadow], "opacity": 22})
    ex("select.set", {"ids": [shadow]}); ex("object.move", {"dx": 10, "dy": 12})  # sombra dura
    paper = rough(x - 16, y - 14, w + 32, h + 28, "#FFFFFF", seed + 20, size=6, detail=9)
    m = rough(x, y, w, h, "#FF0000", seed)
    ex("select.set", {"ids": [m]}); ex("object.expand", {"object": True})
    im = p.img(PH + photo, x - (ph_w - w) / 2, y - (ph_h - h) / 2, ph_w, ph_h)
    ex("select.set", {"ids": [m]}); ex("object.arrange.bringToFront", {})
    ex("select.set", {"ids": [im, m]}); print(ex("object.clippingMask.make", {}))
    return shadow, paper
torn("f5.jpg", 80, 120, 380, 520, 380, 500 * 1.0 + 0, 1)
torn("f2.jpg", 530, 150, 380, 520, 380, 380 * 1280 / 912, 4)
torn("f10.jpg", 980, 120, 380, 520, 400, 400 * 1280 / 959, 9)
p.text(80, 730, "BASTIDORES DA EDIÇÃO 2026", "Helvetica Neue", "Bold", 24, K, tracking=200)
p.export()

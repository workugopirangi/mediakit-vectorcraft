import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h import *
p = P("R05"); ex = p.ex
p.rect(0, 0, 1440, 810, SEA)
im = p.img(PH + "c-asas-capa.jpg", 380, 0, 1440, 810)  # 16:9 cobre a direita
mk = p.rect(380, 0, 1060, 810, "#FFFFFF")
ex("select.set", {"ids": [mk]})
ex("paint.setFill", {"gradient": {"kind": "linear", "angle": 0, "stops": [{"offset": 0, "color": "#000000"}, {"offset": 0.55, "color": "#FFFFFF"}, {"offset": 1, "color": "#FFFFFF"}]}})
ex("select.set", {"ids": [im, mk]})
try:
    print(ex("transparency.makeOpacityMask", {"clip": True}))
except Exception as e:
    print("ERR", e)
p.text(70, 380, "COTA\nOURO", "Helvetica Neue", "Condensed Black", 200, GOLD, tracking=-10, leading=180)
p.text(74, 640, "A foto derrete no azul do fundo, sem borda dura.", "Helvetica Neue", "Medium", 24, W)
p.export()

import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h import *
p = P("R16"); ex = p.ex
p.rect(0, 0, 1440, 810, SEA)
im = p.img(PH + "c-asas.jpg", 0, 0, 1440, 810)
ov = p.rect(0, 0, 1440, 810, SEA); ex("transparency.set", {"ids": [ov], "opacity": 55})
# 1) vazado com contorno, join round
a = p.text(70, 400, "42K", "Helvetica Neue", "Condensed Black", 420, "#FFFFFF", tracking=-10)
try:
    print(ex("text.setRangeStyle", {"id": a, "fill": "none", "stroke": GOLD, "strokeWidth": 6, "strokeOptions": {"join": "round", "cap": "round"}}))
except Exception as e: print("ERR vazado", str(e)[:300])
# 2) preenchimento em gradiente
b = p.text(70, 700, "CORRIDA", "Helvetica Neue", "Condensed Black", 260, "#FFFFFF", tracking=-5)
ex("select.set", {"ids": [b]})
try:
    print(ex("paint.setFill", {"gradient": {"kind": "linear", "angle": 90, "stops": [{"offset": 0, "color": GOLD}, {"offset": 1, "color": CORAL}]}}))
except Exception as e: print("ERR grad", str(e)[:300])
# 3) contorno com miter agudo (controle do defeito)
c = p.text(930, 330, "AMA", "Helvetica Neue", "Condensed Black", 220, "#FFFFFF", tracking=-5)
ex("text.setRangeStyle", {"id": c, "fill": "none", "stroke": W, "strokeWidth": 5, "strokeOptions": {"join": "miter", "miterLimit": 10}})
d = p.text(930, 560, "AMA", "Helvetica Neue", "Condensed Black", 220, "#FFFFFF", tracking=-5)
ex("text.setRangeStyle", {"id": d, "fill": "none", "stroke": W, "strokeWidth": 5, "strokeOptions": {"join": "round"}})
p.text(930, 600, "miter acima, round abaixo", "Helvetica Neue", "Bold", 12, W, tracking=150)
p.export()

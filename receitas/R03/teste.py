import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h import *
p = P("R03"); ex = p.ex
p.rect(0, 0, 1440, 810, K)
t = p.text(60, 540, "SPRINT", "Helvetica Neue", "Condensed Black", 440, "#FFFFFF", tracking=-10)
im = p.img(PH + "c-arena.jpg", 0, 60, 1440, 810)
ex("select.set", {"ids": [t]}); ex("object.arrange.bringToFront", {})
ex("select.set", {"ids": [im, t]})
try:
    print(ex("object.clippingMask.make", {}))
except Exception as e:
    print("ERR", e)
p.text(64, 700, "UBATUBA RUN 2027", "Helvetica Neue", "Bold", 40, GOLD, tracking=300)
p.text(64, 740, "A foto preenche o texto do título.", "Helvetica Neue", "Medium", 22, W)
p.export()

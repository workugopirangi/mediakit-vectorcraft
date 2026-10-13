import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h import *
p = P("R04"); ex = p.ex
bg = p.rect(0, 0, 1440, 810, Y)
t1 = p.text(-30, 520, "CORRA\nSEM PARAR", "Helvetica Neue", "Condensed Black", 560, K, tracking=-20, leading=470)
t2 = t1
sm = p.text(60, 60, "SPRINT UBATUBA RUN 2027", "Helvetica Neue", "Bold", 26, K, tracking=200)
ex("select.set", {"ids": [bg, t1, sm]}); g = ex("object.group", {})["id"]
m = p.rect(0, 0, 1440, 810, "#FF0000")
ex("select.set", {"ids": [g, m]}); print(ex("object.clippingMask.make", {}))
p.export()

import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h import *
p = P("R07"); ex = p.ex
p.rect(0, 0, 1440, 810, Y)
p.rect(0, 560, 1440, 250, K)
BX, BY, BW, BH = 620, 40, 600, 750
# 1) silhueta por trace do alfa
src = p.img(AM + "/real-atleta-recorte.png", BX, BY, BW, BH)
r = ex("imageTrace.make", {"id": src, "params": {"mode": "blackAndWhite", "threshold": 254, "ignoreWhite": True, "noise": 20}})
ids = ex("imageTrace.expand", {"id": r["id"]})["ids"]
ex("select.set", {"ids": ids}); sil = ex("object.pathfinder.unite", {})["ids"]
print("sil", sil)
ex("select.set", {"ids": sil}); ex("object.path.simplify", {"tolerance": 1.5})
# 2) contorno uniforme de 12 pt (duas copias: adesivo e sombra)
ex("select.set", {"ids": sil}); off1 = ex("object.path.offsetPath", {"offset": 12, "joins": "round"})["ids"]
ex("select.set", {"ids": sil}); off2 = ex("object.path.offsetPath", {"offset": 12, "joins": "round"})["ids"]
print(off1, off2)
for i in off2: p.paint(i, K)
ex("select.set", {"ids": off2}); ex("object.move", {"dx": 16, "dy": 16})
for i in off1: p.paint(i, "#FFFFFF")
ex("select.set", {"ids": sil}); ex("edit.clear", {})   # silhueta interna nao precisa
# 3) a foto recortada por cima
ph = p.img(AM + "/real-atleta-recorte.png", BX, BY, BW, BH)
ex("select.set", {"ids": [ph]}); ex("object.arrange.bringToFront", {})
p.text(60, 330, "SUB", "Helvetica Neue", "Condensed Black", 260, K, tracking=-10, leading=240)
p.text(60, 560, "20", "Helvetica Neue", "Condensed Black", 260, K, tracking=-10)
p.text(70, 640, "COPA AME 2027", "Helvetica Neue", "Bold", 34, Y, tracking=250)
p.text(70, 690, "Recorte com contorno de adesivo e sombra dura vetorial.", "Helvetica Neue", "Medium", 20, "#FFFFFF")
p.export()

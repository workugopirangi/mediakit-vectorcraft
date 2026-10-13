import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h import *
p = P("R02"); ex = p.ex
p.rect(0, 0, 1440, 810, SEA)
def clip(photo, mask_id, bx, by, bw, bh):
    im = p.img(PH + photo, bx, by, bw, bh)
    ex("select.set", {"ids": [mask_id]}); ex("object.arrange.bringToFront", {})
    ex("select.set", {"ids": [im, mask_id]})
    return ex("object.clippingMask.make", {})
# 1 circulo
m = p.ellipse(60, 200, 340, 340, "#FF0000"); clip("f1.jpg", m, 60 - 0, 200, 340, 465)
# 2 losango
d = ex("shape.polygon", {"cx": 560, "cy": 370, "radius": 200, "sides": 4, "rotation": 0})["id"]; p.paint(d, "#FF0000")
clip("f5.jpg", d, 360, 170 - 60, 400, 526)
# 3 blob organico
blob = ex("path.create", {"d": "M960,200 C1040,170 1120,220 1130,300 C1145,390 1090,440 1020,520 C950,590 850,520 830,430 C810,340 860,230 960,200 Z"})["id"]; p.paint(blob, "#FF0000")
clip("f8.jpg", blob, 810, 170, 350, 465)
# 4 composta com furo (donut)
o = ex("shape.ellipse", {"x": 1180, "y": 220, "width": 230, "height": 230})["id"]
i = ex("shape.ellipse", {"x": 1240, "y": 280, "width": 110, "height": 110})["id"]
ex("select.set", {"ids": [o, i]}); cp = ex("object.compoundPath.make", {}); print("cp", cp)
cpid = cp.get("id")
p.paint(cpid, "#FF0000")
clip("f10.jpg", cpid, 1180, 220, 230, 307)
p.text(60, 120, "FORMAS LIVRES", "Helvetica Neue", "Condensed Black", 70, MINT, tracking=-5)
p.text(60, 700, "Circulo, losango, forma orgânica e círculo com furo.", "Helvetica Neue", "Medium", 20, W)
p.export()

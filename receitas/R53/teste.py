import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h5166 import *
d = Doc("R53")
d.ex("document.rasterEffectsSettings", {"resolution": 300})
d.rect(0, 0, 1440, 810, Y)
def word(s, x, y, size, color):
    t = d.text(x, y, s, "Helvetica Neue", "Condensed Black", size, color)
    d.ex("select.set", {"ids": [t]}); g = d.ex("type.createOutlines", {})["ids"]
    d.ex("select.set", {"ids": g}); u = d.ex("object.ungroup", {}); print("ungroup", u)
    r = d.ex("object.pathfinder.unite", {}); print("unite", r)
    return r["ids"]
def ext(ids, params):
    d.ex("select.set", {"ids": ids})
    r = d.ex("effect.apply", {"effect": "threeD.extrude", "params": params}); d.ex("select.none"); return r
a = word("COPA AME", 60, 300, 190, CORAL)
print(ext(a, {"depth": 30, "rotationX": -6, "rotationY": -12, "rotationZ": 0, "perspective": 0, "shade": True, "ambient": 45, "lightIntensity": 70}))
b = word("2027", 60, 640, 190, K)
print(ext(b, {"depth": 30, "rotationX": 0, "rotationY": 0, "rotationZ": 0, "perspective": 0, "shade": False, "taper": 100}))
p = d.export(); report(p); d.close()

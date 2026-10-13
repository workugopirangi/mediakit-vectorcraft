import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h5166 import *
d = Doc("R63")
cores = {"AME amarelo": "#F5D80A", "AME preto": "#0B0B0C", "Sprint ouro": "#D4A64A", "Sprint creme": "#F3E3B5", "Sprint mar": "#0F3550", "Sprint menta": "#9FE3D0", "Sprint coral": "#E9603A"}
res = {}
for n, h in cores.items():
    r = d.ex("color.convert", {"color": h, "to": "cmyk"}); res[n] = (h, r)
    print(n, h, json.dumps(r))
for intent in ("perceptual", "relative", "saturation", "absolute"):
    r = d.ex("color.convert", {"color": "#F5D80A", "to": "cmyk", "intent": intent}); print("intent", intent, r["values"], r["deltaE"], r["outOfGamut"])
# ida e volta: CMYK -> RGB
r = d.ex("color.convert", {"color": res["AME amarelo"][1]["values"] if False else {"c": 4, "m": 10, "y": 96, "k": 0}, "to": "rgb"}); print("cmyk->rgb", r)
# faixas lado a lado: RGB original e CMYK convertido (swatch cmyk)
d.rect(0, 0, 1440, 810, "#FFFFFF")
d.text(60, 90, "AMARELO DA MARCA: TELA (RGB) x IMPRESSÃO (CMYK)", "Helvetica Neue", "Condensed Black", 54, K)
y = 140
for i, (n, (h, r)) in enumerate(res.items()):
    v = r["values"]; print(n, v)
    cm = {"c": v[0] if v[0] <= 1.0 and max(v) <= 1.0 else v[0], "m": v[1], "y": v[2], "k": v[3]} if isinstance(v, list) else v
    col, row = i % 4, i // 4
    x, yy = 60 + col * 340, 140 + row * 330
    d.rect(x, yy, 150, 220, h)
    sw = d.ex("swatch.new", {"name": n + " CMYK", "color": h, "mode": "cmyk"})
    d.ex("select.set", {"ids": [d.rect(x + 150, yy, 150, 220, h)]}); d.ex("paint.setFill", {"swatch": sw["name"]}); d.ex("select.none")
    d.text(x, yy + 250, f"{n}", "Helvetica Neue", "Bold", 18, K)
    d.text(x, yy + 274, f"{h}  dE {r['deltaE']:.1f}" + ("  FORA DA GAMA" if r["outOfGamut"] else ""), "Helvetica Neue", "Medium", 15, "#555555")
p = d.export(); report(p); d.close()

import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h import *
p = P("R08"); ex = p.ex
RES = int(os.environ.get("RES", "300"))
ex("document.rasterEffectsSettings", {"resolution": RES})
blocks = [(0, SEA, None), (480, SEA, ("texture.grain", {"intensity": 40, "contrast": 50, "grainType": "regular"})),
          (960, SEA, ("artistic.filmGrain", {"grain": 6, "highlightArea": 0, "intensity": 10}))]
for x, c, eff in blocks:
    r = p.rect(x, 0, 480, 810, c)
    if eff:
        ex("select.set", {"ids": [r]})
        try: print(ex("effect.apply", {"effect": eff[0], "params": eff[1]}))
        except Exception as e: print("ERR", eff[0], str(e)[:300])
labels = ["SEM EFEITO", "texture.grain", "artistic.filmGrain"]
for i, t in enumerate(labels):
    p.text(40 + i * 480, 120, t, "Helvetica Neue", "Condensed Black", 56, GOLD)
p.text(40, 700, "Fundo chapado vs grão", "Helvetica Neue", "Medium", 22, W)
p.export()

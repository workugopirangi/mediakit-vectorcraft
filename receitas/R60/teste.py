import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h5166 import *
d = Doc("R60")
print(d.ex("prefs.get", {"key": "scaleStrokes"}) if False else "")
# 1) três artboards 1440x810, em linha, espaçadas 100
ABX = [0, 1540, 3080]
d.ex("artboard.new", {"x": 1540, "y": 0, "width": 1440, "height": 810, "name": "Pagina 2"})
d.ex("artboard.new", {"x": 3080, "y": 0, "width": 1440, "height": 810, "name": "Pagina 3"})
cols = [SEA, CREAM, Y]
for i, ox in enumerate(ABX):
    d.rect(ox, 0, 1440, 810, cols[i])
    d.rect(ox + 60, 60, 1320, 690, None, stroke=K if i else CREAM, sw=4)
    d.text(ox + 100, 230, f"PÁGINA {i+1}", "Helvetica Neue", "Condensed Black", 120, CREAM if i == 0 else SEA)
    d.text(ox + 100, 300, "Texto 28 pt, traço 4 pt, sem escalar", "Helvetica Neue", "Bold", 28, MINT if i == 0 else K)
# 2) o que acontece com traço ao usar object.setBounds / object.scale
s1 = d.rect(100, 400, 200, 100, None, stroke=CORAL, sw=10)
def sw(oid):
    for L in d.ex("document.inspect", {"depth": 4})["layers"]:
        f = None
        def find(n):
            if n.get("id") == oid: return n
            for c in n.get("children", []) or []:
                r = find(c)
                if r: return r
        f = find(L)
        if f: return f.get("strokeWidth"), f.get("bounds")
print("antes", sw(s1))
d.ex("select.set", {"ids": [s1]}); d.ex("object.scale", {"sx": 150, "strokes": False}); print("scale strokes:false", sw(s1))
s2 = d.rect(100, 600, 200, 100, None, stroke=CORAL, sw=10)
d.ex("select.set", {"ids": [s2]}); d.ex("object.scale", {"sx": 150, "strokes": True}); print("scale strokes:true", sw(s2))
s3 = d.rect(500, 600, 200, 100, None, stroke=CORAL, sw=10)
d.ex("select.set", {"ids": [s3]}); d.ex("object.scale", {"sx": 150}); print("scale default (prefs)", sw(s3))
s4 = d.rect(900, 600, 200, 100, None, stroke=CORAL, sw=10)
d.ex("select.set", {"ids": [s4]}); d.ex("object.setBounds", {"width": 300, "height": 150, "reference": 0}); print("setBounds default", sw(s4))
d.ex("select.none")
print(d.ex("artboard.rearrange", {"layout": "row", "spacing": 100}))
p = d.export("teste.pdf")
print(subprocess.run(f'pdfinfo -f 1 -l 3 "{p}" | grep -E "Pages|size"', shell=True, capture_output=True, text=True).stdout)
subprocess.run(f'pdftoppm -r 25 -png "{p}" "{d.dir}/pg"', shell=True)
d.close()

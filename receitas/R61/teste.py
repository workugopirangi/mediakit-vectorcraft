import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h5166 import *
d = Doc("R61", bleed=8.5)
d.rect(-8.5, -8.5, 1457, 827, SEA)
d.image(SP + "/tratado/c-portico.jpg", 0, -8.5, 1448.5)
d.rect(0, 500, 1440, 310, SEA, opacity=85)
d.text(60, 640, "VERSÃO GRÁFICA", "Helvetica Neue", "Condensed Black", 110, CREAM)
d.text(60, 700, "Sangria 8,5 pt, marcas de corte romanas 0,25 pt", "Helvetica Neue", "Bold", 28, MINT)
# A) marcas como objetos na arte
d.ex("select.none")
r = d.ex("object.createTrimMarks", {"style": "roman", "offset": 12, "length": 18, "weight": 0.25, "allArtboards": True}); print("trimMarks objeto", r)
for L in d.ex("document.inspect", {"depth": 3})["layers"]:
    for c in L.get("children", []): print(" ", c.get("name") or c.get("kind"), c.get("bounds"))
# B) marcas pelo export
pA = d.export("A-marcas-objeto.pdf")
print(subprocess.run(f'pdfinfo -box "{pA}" | grep -E "Box|size"', shell=True, capture_output=True, text=True).stdout)
d.close()
# B) export com marks (sem objeto)
d2 = Doc("R61", bleed=8.5)
d2.rect(-8.5, -8.5, 1457, 827, SEA)
d2.image(SP + "/tratado/c-portico.jpg", 0, -8.5, 1448.5)
d2.text(60, 640, "VERSÃO GRÁFICA", "Helvetica Neue", "Condensed Black", 110, CREAM)
r = d2.ex("document.exportPdf", {"path": d2.dir + "/B-marcas-export.pdf", "preserveEditing": False, "bleed": {"useDocument": True},
     "marks": {"trim": True, "registration": True, "colorBars": True, "pageInfo": True, "kind": "roman", "weight": 0.25, "offset": 12}})
print(r)
print(subprocess.run(f'pdfinfo -box "{d2.dir}/B-marcas-export.pdf" | grep -E "Box|size"', shell=True, capture_output=True, text=True).stdout)
subprocess.run(f'pdftoppm -r 50 -png "{d2.dir}/B-marcas-export.pdf" "{d2.dir}/pvB"; pdftoppm -r 50 -png "{d2.dir}/A-marcas-objeto.pdf" "{d2.dir}/pvA"', shell=True)
d2.close()

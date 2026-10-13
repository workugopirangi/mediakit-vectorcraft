import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h5166 import *
d = Doc("R54")
d.rect(0, 0, 1440, 810, SEA)
d.text(60, 110, "COTAS E ETIQUETAS", "Helvetica Neue", "Condensed Black", 64, CREAM)
# 1 pílula com radius = h/2
def pill(x, y, w, h, fill, label, tc, stroke=None):
    d.rect(x, y, w, h, fill, stroke=stroke, sw=2, radius=h / 2)
    d.text(x + h / 2, y + h / 2 + 8, label, "Helvetica Neue", "Bold", 22, tc)
pill(60, 160, 220, 56, GOLD, "OURO", K); pill(300, 160, 220, 56, CREAM, "PRATA", SEA); pill(540, 160, 220, 56, CORAL, "BRONZE", "#FFFFFF")
pill(780, 160, 260, 56, None, "APOIO", MINT, stroke=MINT)
# 2 cartões com raio 24, 12, 0 e raio por canto
for i, r in enumerate([36, 18, 6]):
    d.rect(60 + i * 300, 280, 270, 200, CREAM, radius=r)
    d.text(80 + i * 300, 330, f"radius {r}", "Helvetica Neue", "Bold", 24, SEA)
# raio só em 2 cantos via setLiveShape (cantos 0 e 2: topo-esq e baixo-dir)
c = d.rect(60 + 3 * 300, 280, 270, 200, MINT, radius=1)
d.ex("select.set", {"ids": [c]})
print("setLiveShape", d.ex("object.setLiveShape", {"ids": [c], "radius": 48, "corners": [0, 2]}))
d.text(80 + 900, 330, "cantos 0 e 2", "Helvetica Neue", "Bold", 24, SEA)
# cantos chanfrados e invertidos
c2 = d.rect(60, 540, 270, 200, GOLD, radius=1)
print(d.ex("object.setLiveShape", {"ids": [c2], "radius": 40, "kind": "chamfer"}))
c3 = d.rect(360, 540, 270, 200, CORAL, radius=1)
print(d.ex("object.setLiveShape", {"ids": [c3], "radius": 40, "kind": "invertedRound"}))
# roundCorners efeito num retangulo reto
c4 = d.rect(660, 540, 270, 200, CREAM)
d.ex("select.set", {"ids": [c4]})
print(d.ex("effect.apply", {"effect": "stylize.roundCorners", "params": {"radius": 30}}))
# traço grosso em pílula + ajuste posterior de raio
c5 = d.rect(960, 540, 400, 200, None, stroke=CREAM, sw=8, radius=20)
d.ex("object.setLiveShape", {"ids": [c5], "radius": 100})
d.ex("select.none")
p = d.export(); report(p); d.close()

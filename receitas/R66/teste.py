import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h5166 import *
d = Doc("R66")
d.ex("document.rasterEffectsSettings", {"resolution": 300})
d.rect(0, 0, 1440, 810, Y)
FX, FY, FW, FH = 330, 250, 780, 480   # o quadro
# 1) quadro: foto recortada no retângulo + borda preta
ph = d.image(AM + "/tratado/c-noite.jpg", FX - 200, FY - 60, 1180)
m = d.rect(FX, FY, FW, FH, K)
d.ex("select.set", {"ids": [ph, m]}); fr = d.ex("object.clippingMask.make")["id"]; d.ex("select.none")
d.rect(FX, FY, FW, FH, K, opacity=35)             # escurece a foto do quadro
bd = d.rect(FX, FY, FW, FH, None, stroke=K, sw=8)  # borda
# 2) pessoa: maior que o quadro, cabeça acima da borda de cima
PW_, PH_ = 640, 800
px, py = 560, 110
ath = d.image(AM + "/real-atleta-recorte.png", px, py, PW_, PH_)
d.ex("select.set", {"ids": [ath]})   # sombra ANTES do recorte: a máscara corta o que passaria da borda de baixo
d.ex("effect.apply", {"effect": "stylize.dropShadow", "params": {"blur": 18, "x": -10, "y": 8, "opacity": 55, "color": "#000000", "mode": "multiply"}})
d.ex("select.none")
# 3) máscara = união (quadro) + (faixa acima do borda de cima): só o que passa por cima do quadro aparece
a = d.rect(FX, FY, FW, FH, K)
b = d.rect(0, 0, 1440, FY, K)
d.ex("select.set", {"ids": [a, b]}); u = d.ex("object.pathfinder.unite", {})["ids"]; print("unite", u)
d.ex("select.set", {"ids": [ath, u[0]]}); g = d.ex("object.clippingMask.make"); print("clip", g)
d.ex("select.none")
d.text(60, 140, "SAIU DO QUADRO.", "Helvetica Neue", "Condensed Black", 96, K)
d.text(60, 790, "Recorte que rompe a moldura: a cabeça passa da borda, o resto fica contido.", "Helvetica Neue", "Bold", 20, K)
p = d.export(); report(p); d.close()

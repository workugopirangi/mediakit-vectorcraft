import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h5166 import *
d = Doc("R65")
d.ex("document.rasterEffectsSettings", {"resolution": 300})
d.rect(0, 0, 1440, 810, K)
bg = d.image(AM + "/tratado/c-capa-sabado.jpg", 0, 0, 1440)  # foto de fundo (proporcional)
d.rect(0, 0, 1440, 810, K, opacity=45)                       # escurece para o título pesar
# título gigante: 1 linha, amarelo da marca, BEM atrás da pessoa
t = d.text(50, 600, "COPA AME", "Helvetica Neue", "Condensed Black", 300, Y, tracking=-5)
# pessoa recortada, por cima do título
ath = d.image(AM + "/real-atleta-recorte.png", 640, 30, 640, 800)
d.ex("select.set", {"ids": [ath]})
d.ex("effect.apply", {"effect": "stylize.dropShadow", "params": {"blur": 22, "x": -14, "y": 6, "opacity": 55, "color": "#000000", "mode": "multiply"}})
d.ex("select.none")
d.text(60, 740, "10 MIL ATLETAS. 750 EQUIPES. UM SÓ CAMPO.", "Helvetica Neue", "Bold", 26, "#FFFFFF", tracking=40)
d.text(60, 90, "SAÍDA 2027", "Helvetica Neue", "Bold", 22, Y, tracking=200)
p = d.export(); report(p)
print("ordem:", [(c.get("name") or c.get("kind"), c.get("id")) for L in d.ex("document.inspect", {"depth": 2})["layers"] for c in L.get("children", [])])
d.close()

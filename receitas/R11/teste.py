import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h import *
p = P("R11"); ex = p.ex
p.rect(0, 0, 1440, 810, K)
# 1) amostras para extrair os estilos
def sample(font, style, size, color, **st):
    t = p.text(0, 0, "x", font, style, size, color, **st); return t
specs = {
 "KIT Display": ("Helvetica Neue", "Condensed Black", 190, Y, dict(tracking=-15, leading=170)),
 "KIT Titulo": ("Helvetica Neue", "Bold", 44, "#FFFFFF", dict(tracking=-5, leading=48)),
 "KIT Corpo": ("Helvetica Neue", "Medium", 19, "#E8E8E8", dict(tracking=5, leading=29)),
 "KIT Legenda": ("Helvetica Neue", "Bold", 11, Y, dict(tracking=220, leading=14)),
}
for name, (f, s, z, c, st) in specs.items():
    t = sample(f, s, z, c, **st)
    ex("select.set", {"ids": [t]})
    print(ex("paraStyle.new", {"name": name, "id": t}), ex("charStyle.new", {"name": name, "id": t}))
    ex("edit.clear", {"ids": [t]})
print(json.dumps(ex("charStyle.list", {}))[:1200])
# 2) texto cru (fonte padrao) e aplica por nome
def use(x, y, s, name, w=None):
    a = {"x": x, "y": y, "text": s, "size": 12}
    if w: a["area"] = {"width": w, "height": 400, "fit": "autoHeight"}
    t = ex("text.create", a)["id"]
    print(name, ex("paraStyle.apply", {"name": name, "ids": [t]}), ex("charStyle.apply", {"name": name, "ids": [t]}))
    return t
use(70, 300, "COPA\nAME", "KIT Display")
use(640, 140, "UM TORNEIO DE FUTEBOL PARA 5.000 CRIANÇAS", "KIT Legenda")
use(640, 230, "Cotas de patrocínio 2027", "KIT Titulo")
use(640, 290, "A Copa AME reúne atletas do sub-06 ao sub-20 em São José do Rio Preto. A marca patrocinadora entra no uniforme, no campo e na transmissão ao vivo, com presença em todos os jogos da fase final.", "KIT Corpo", w=560)
use(640, 480, "Segundo parágrafo no mesmo estilo de corpo, para checar o espaçamento entre linhas e a colisão de ascendentes e descendentes.", "KIT Corpo", w=560)
use(640, 690, "Visibilidade em campo", "KIT Titulo")
lst = {x["name"]: x for x in ex("charStyle.list", {})["styles"]}
print("usos antes:", {k: v["uses"] for k, v in lst.items() if k.startswith("KIT")})
ex("document.exportPdf", {"path": p.d + "/teste_antes.pdf", "preserveEditing": False})
a = dict(lst["KIT Titulo"]["attrs"]); a["size"] = 60; a["leading"] = 64; a["fill"] = {"type": "solid", "color": {"model": "rgb", "r": 0.96, "g": 0.85, "b": 0.04}}
print(ex("charStyle.setAttrs", {"name": "KIT Titulo", "attrs": a}))
p.export()

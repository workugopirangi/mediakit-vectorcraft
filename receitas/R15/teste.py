import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h import *
p = P("R15"); ex = p.ex
p.rect(0, 0, 1440, 810, SEA)
p.text(90, 120, "INVESTIMENTO", "Helvetica Neue", "Bold", 16, GOLD, tracking=300)
p.text(90, 205, "Cotas de patrocínio", "Helvetica Neue", "Condensed Black", 84, W, tracking=-5)
rows = [("Cota Ouro (naming rights)", "R$ 120.000,00"), ("Cota Prata (pórtico e camisetas)", "R$ 75.000,00"), ("Cota Bronze (tenda de ativação)", "R$ 38.500,00")]
# A) tabulação com leader (leader é aceito e NÃO desenhado)
p.text(90, 275, "A) text.tabs.set com leader \". \"", "Helvetica Neue", "Bold", 12, GOLD, tracking=120)
t = ex("text.create", {"x": 90, "y": 320, "text": "\n".join(a + "\t" + b for a, b in rows), "font": "Helvetica Neue", "style": "Medium", "size": 26, "color": "#FFFFFF", "area": {"width": 760, "height": 200, "fit": "none"}})["id"]
ex("text.setStyle", {"ids": [t], "leading": 46}); ex("select.set", {"ids": [t]})
ex("text.tabs.set", {"ids": [t], "stops": [{"position": 760, "align": "right", "leader": ". "}]})
# B) plano B: rótulo + valor + linha pontilhada de verdade
p.text(90, 505, "B) rótulo + valor em objetos separados + linha pontilhada (stroke.set dash)", "Helvetica Neue", "Bold", 12, GOLD, tracking=120)
def bnd(oid):
    d = ex("document.inspect", {"depth": 3})
    def f(n):
        if isinstance(n, dict):
            if n.get("id") == oid and "bounds" in n: return n["bounds"]
            for v in n.values():
                r = f(v)
                if r: return r
        elif isinstance(n, list):
            for v in n:
                r = f(v)
                if r: return r
    return f(d)
for i, (a, b) in enumerate(rows):
    y = 550 + i * 46
    la = p.text(90, y, a, "Helvetica Neue", "Medium", 26, "#FFFFFF")
    vb = p.text(850, y, b, "Helvetica Neue", "Medium", 26, "#FFFFFF")
    ex("select.set", {"ids": [vb]}); bv = bnd(vb); ba = bnd(la)
    # valor alinhado à direita em 850: move
    ex("object.move", {"dx": 850 - (bv["x"] + bv["width"]) if "x" in bv else 0, "dy": 0})
    bv = bnd(vb)
    ln = ex("shape.line", {"x1": ba["x"] + ba["width"] + 12, "y1": y - 3, "x2": bv["x"] - 12, "y2": y - 3})["id"]
    p.paint(ln, None, GOLD, 2.2)
    ex("select.set", {"ids": [ln]}); ex("stroke.set", {"weight": 2.2, "cap": "round", "dash": [0, 7]})
# C) alinhamento decimal
p.text(960, 275, "C) tab decimal em \",\"", "Helvetica Neue", "Bold", 12, GOLD, tracking=120)
rows2 = ["Ouro\t120.000,00", "Prata\t75.000,00", "Bronze\t38.500,00", "Apoio\t9.900,00", "Permuta\t850,5"]
t2 = ex("text.create", {"x": 960, "y": 320, "text": "\n".join(rows2), "font": "Helvetica Neue", "style": "Medium", "size": 24, "color": GOLD, "area": {"width": 380, "height": 300, "fit": "none"}})["id"]
ex("text.setStyle", {"ids": [t2], "leading": 46}); ex("select.set", {"ids": [t2]})
ex("text.tabs.set", {"ids": [t2], "stops": [{"position": 300, "align": "decimal", "alignOn": ","}]})
p.export()

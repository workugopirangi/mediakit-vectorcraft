import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h import *
p = P("R06"); ex = p.ex
p.rect(0, 0, 1440, 810, K)
cards = [("f2.jpg", SEA, 72, None, "VISIBILIDADE", "Marca no pórtico de largada e em 2.500 camisetas."),
         ("f5.jpg", CORAL, 75, None, "ATIVAÇÃO", "Tenda na arena com 3 dias de contato direto."),
         ("f10.jpg", "#0B0B0C", 100, "Multiply", "CONTEÚDO", "Fotos e vídeo da edição para suas redes.")]
x = 60
for ph, col, op, blend, tt, tx in cards:
    r = {"f2.jpg": 912 / 1280, "f5.jpg": 972 / 1280, "f10.jpg": 959 / 1280}[ph]
    w = 650 * r
    im = p.img(PH + ph, x - (w - 420) / 2, 80, w, 650)
    m = p.rect(x, 80, 420, 650, "#FF0000"); ex("select.set", {"ids": [m]}); ex("object.arrange.bringToFront", {})
    ex("select.set", {"ids": [im, m]}); ex("object.clippingMask.make", {})
    ov = p.rect(x, 80, 420, 650, col)
    if blend:
        ex("transparency.set", {"ids": [ov], "blend": blend, "opacity": 60})
    else:
        ex("transparency.set", {"ids": [ov], "opacity": op})
    p.text(x + 30, 640, tt, "Helvetica Neue", "Condensed Black", 64, "#FFFFFF", tracking=0)
    p.text(x + 30, 680, tx, "Helvetica Neue", "Medium", 15, "#FFFFFF")
    x += 460
p.export()

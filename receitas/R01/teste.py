import sys; import os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h import *
p = P("R01"); ex = p.ex
p.rect(0, 0, 1440, 810, K)
# foto: cobre 720x810 (f12 853x1280 -> largura 720 => alt 1080), centrada no rosto
im = p.img(PH + "f12.jpg", 0, -120, 720, 1080)
ex("edit.colors.toGrayscale", {"ids": [im], "includeImages": True})
ex("edit.colors.adjustBalance", {"ids": [im], "mode": "gray", "gray": 0, "includeImages": True}) if False else None
# camada amarela Multiply: preto fica preto, branco vira amarelo
y = p.rect(0, -120, 720, 1080, Y)
ex("transparency.set", {"ids": [y], "blend": "Multiply"})
ex("select.set", {"ids": [im, y]}); g = ex("object.group", {})["id"]
m = p.rect(0, 0, 720, 810, "#FF0000")
ex("select.set", {"ids": [g, m]})
print(ex("object.clippingMask.make", {}))
p.text(780, 330, "DUOTONE", "Helvetica Neue", "Condensed Black", 150, Y, tracking=-10)
p.text(784, 400, "foto em preto e amarelo AME", "Helvetica Neue", "Medium", 30, W)
p.text(784, 470, "Cinza + camada amarela em Multiply.", "Helvetica Neue", "Medium", 20, W)
p.export()

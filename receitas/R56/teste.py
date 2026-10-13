import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from h5166 import *
from PIL import Image
L = HERE + "/R56/logos/"
NAMES = ["diboa","silvamar","eab","spazio","gelo","pouso","lotus","dogs","uuhull","amazone","fenix","brava","tachao","arc","zando"]
def build(mode):
    d = Doc("R56")
    d.rect(0, 0, 1440, 810, SEA if mode == "branco" else CREAM)
    d.text(60, 110, "QUEM JÁ CORRE COM A GENTE", "Helvetica Neue", "Condensed Black", 60, CREAM if mode == "branco" else SEA)
    d.text(60, 150, "Parceiros do Sprint Ubatuba Run (peso óptico igual: área alvo 14.000 pt², caixa máxima 190 x 90)", "Helvetica Neue", "Medium", 16, MINT if mode == "branco" else SEA)
    cw, chh, x0, y0 = 264, 190, 60, 200
    rows = []
    for k, n in enumerate(NAMES):
        w0, h0 = Image.open(L + n + ".png").size
        ar = w0 / h0
        w = math.sqrt(14000 * ar); h = w / ar
        s = min(1, 190 / w, 90 / h); w *= s; h *= s
        c, r = k % 5, k // 5
        cx, cy = x0 + c * cw + cw / 2 - 12, y0 + r * chh + chh / 2
        oid = d.ex("file.place", {"path": L + n + ".png", "link": False})["ids"][0]
        d.ex("select.set", {"ids": [oid]})
        d.ex("object.setBounds", {"x": cx, "y": cy, "width": w, "height": h})  # referência padrão = centro
        if mode == "branco":
            d.ex("effect.apply", {"effect": "adjust.levels", "params": {"outputBlack": 255.0, "outputWhite": 255.0}})
        elif mode == "preto":
            d.ex("effect.apply", {"effect": "adjust.levels", "params": {"outputBlack": 0.0, "outputWhite": 0.0}})
        d.ex("select.none")
        rows.append(oid)
    # linha divisória sutil
    for r in range(1, 3):
        d.rect(60, y0 + r * chh, 1320, 1, MINT if mode == "branco" else SEA, opacity=30)
    p = d.export("teste.pdf" if mode == "branco" else f"teste-{mode}.pdf")
    d.ex("document.pdfInfo", {"path": p}) if False else None
    d.close(); return p
mode = sys.argv[1] if len(sys.argv) > 1 else "branco"
p = build(mode); report(p)

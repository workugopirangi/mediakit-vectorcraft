import sys, os, subprocess, json
sys.path.insert(0, os.path.expanduser("~/Developer/vectorcraft-mediakit"))
from vch import VC
B = "/Users/ugopirangi/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/"
SP = B + "SPRINT UBATUBA RUN/MEDIAKIT/sprint-2027/acervo/"
AM = B + "AME CRIANCA/MEDIAKIT/copa-ame-v2/acervo/"
SPT, SPE, AMT, AME_E = SP + "tratado/", SP + "elementos/", AM + "tratado/", AM + "elementos/"
R = os.path.expanduser("~/Developer/vectorcraft-mediakit/receitas/")
K, Y, W = "#0B0B0C", "#F5D80A", "#F2F0E8"
GOLD, CREAM, SEA, MINT, CORAL = "#D4A64A", "#F3E3B5", "#0F3550", "#9FE3D0", "#E9603A"

class P:
    def __init__(s, rid):
        s.rid = rid; s.dir = R + rid + "/"; os.makedirs(s.dir, exist_ok=True)
        s.vc = VC(); s.ex = s.vc.ex
        s.ex("file.new", {"width": 1440, "height": 810, "units": "Points"})
    def paint(s, oid, fill=None, stroke=None, sw=1, opacity=None):
        s.ex("select.set", {"ids": [oid]})
        s.ex("paint.setFill", {"none": True} if fill is None else {"color": fill})
        if stroke is None: s.ex("paint.setStroke", {"none": True})
        else:
            s.ex("paint.setStroke", {"color": stroke}); s.ex("stroke.set", {"weight": sw})
        if opacity is not None: s.ex("transparency.set", {"ids": [oid], "opacity": opacity})
        s.ex("select.none"); return oid
    def rect(s, x, y, w, h, fill=K, **k):
        return s.paint(s.ex("shape.rectangle", {"x": x, "y": y, "width": w, "height": h})["id"], fill, **k)
    def ell(s, cx, cy, rx, ry=None, fill=K, **k):
        ry = ry or rx
        return s.paint(s.ex("shape.ellipse", {"x": cx-rx, "y": cy-ry, "width": 2*rx, "height": 2*ry})["id"], fill, **k)
    def path(s, d, fill=None, **k):
        return s.paint(s.ex("path.create", {"d": d})["id"], fill, **k)
    def img(s, f, x, y, w, h):
        oid = s.ex("file.place", {"path": f, "link": False})["ids"][0]
        s.ex("select.set", {"ids": [oid]})
        s.ex("object.setBounds", {"x": x, "y": y, "width": w, "height": h, "reference": 0})
        s.ex("select.none"); return oid
    def imgcover(s, f, x, y, w, h):
        """foto preenchendo a caixa (corte central) via mascara"""
        from PIL import Image
        iw, ih = Image.open(f).size
        sc = max(w/iw, h/ih); dw, dh = iw*sc, ih*sc
        oid = s.img(f, x-(dw-w)/2, y-(dh-h)/2, dw, dh)
        m = s.rect(x, y, w, h, fill="#000000")
        s.ex("select.set", {"ids": [oid, m]}); r = s.ex("object.clippingMask.make", {}); s.ex("select.none")
        return r["id"]
    def text(s, x, y, t, size=40, font="Helvetica Neue", style="Bold", color=W, **k):
        p = {"x": x, "y": y, "text": t, "font": font, "style": style, "size": size, "color": color}; p.update(k)
        return s.ex("text.create", p)["id"]
    def export(s):
        out = s.dir + "teste.pdf"
        s.ex("document.exportPdf", {"path": out, "preserveEditing": False})
        s.vc.close()
        subprocess.run(["pdftoppm", "-r", "50", "-png", out, s.dir + "preview"], check=True)
        print(subprocess.run(f"ls -la {s.dir}; pdffonts {out}; pdfimages -list {out} | head -12", shell=True, capture_output=True, text=True).stdout)

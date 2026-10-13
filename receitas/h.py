import sys, os, subprocess
REC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.expanduser("~/Developer/vectorcraft-mediakit"))
from vch import VC
SP = "/Users/ugopirangi/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/SPRINT UBATUBA RUN/MEDIAKIT/sprint-2027/acervo"
AM = "/Users/ugopirangi/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/AME CRIANCA/MEDIAKIT/copa-ame-v2/acervo"
PH = SP + "/tratado/"
EL = SP + "/elementos/"
Y, K, W = "#F5D80A", "#0B0B0C", "#F3E3B5"
GOLD, SEA, MINT, CORAL = "#D4A64A", "#0F3550", "#9FE3D0", "#E9603A"

class P:
    def __init__(self, d):
        self.d = os.path.join(REC, d)
        self.vc = VC()
        self.ex = self.vc.ex
        self.ex("file.new", {"width": 1440, "height": 810, "units": "Points"})
    def paint(self, oid, fill=None, stroke=None, sw=1):
        self.ex("select.set", {"ids": [oid]})
        self.ex("paint.setFill", {"color": fill} if fill else {"none": True})
        if stroke:
            self.ex("paint.setStroke", {"color": stroke}); self.ex("stroke.set", {"weight": sw})
        else:
            self.ex("paint.setStroke", {"none": True})
        return oid
    def rect(self, x, y, w, h, fill=K, **k):
        o = self.ex("shape.rectangle", {"x": x, "y": y, "width": w, "height": h})["id"]
        return self.paint(o, fill, **k)
    def ellipse(self, x, y, w, h, fill=K, **k):
        o = self.ex("shape.ellipse", {"x": x, "y": y, "width": w, "height": h})["id"]
        return self.paint(o, fill, **k)
    def img(self, path, x, y, w=None, h=None):
        o = self.ex("file.place", {"path": path, "link": False})["ids"][0]
        self.ex("select.set", {"ids": [o]})
        if w and h:
            self.ex("object.setBounds", {"x": x, "y": y, "width": w, "height": h, "reference": 0})
        return o
    def text(self, x, y, s, font="Helvetica Neue", style="Bold", size=20, color=W, **st):
        o = self.ex("text.create", {"x": x, "y": y, "text": s, "font": font, "style": style, "size": size, "color": color})["id"]
        if st:
            self.ex("text.setStyle", {"ids": [o], **st})
        return o
    def bounds(self, oid):
        r = self.ex("document.inspect", {"id": oid}) if False else None
        return r
    def export(self):
        os.makedirs(self.d, exist_ok=True)
        pdf = self.d + "/teste.pdf"
        self.ex("document.exportPdf", {"path": pdf, "preserveEditing": False})
        self.vc.close()
        subprocess.run(["pdftoppm", "-r", "50", "-png", pdf, self.d + "/preview"])
        print(subprocess.run(["bash", "-c", f"ls -la {pdf}; pdffonts {pdf}; pdfimages -list {pdf}"], capture_output=True, text=True).stdout)

def _find(node, oid):
    if node.get("id") == oid: return node
    for c in node.get("children", []) or []:
        r = _find(c, oid)
        if r: return r
def bounds(d, oid):
    r = d.ex("document.inspect", {"depth": 4})
    for L in r["layers"]:
        f = _find(L, oid)
        if f: return f["bounds"]
def tools(d, cmd, **p): return d.ex(cmd, p)
def report(path):
    print(subprocess.run(f'ls -la "{path}"; pdffonts "{path}"; pdfimages -list "{path}"', shell=True, capture_output=True, text=True).stdout)

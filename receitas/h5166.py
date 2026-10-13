import sys, os, subprocess, json
sys.path.insert(0, os.path.expanduser("~/Developer/vectorcraft-mediakit"))
from vch import VC
SP = "/Users/ugopirangi/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/SPRINT UBATUBA RUN/MEDIAKIT/sprint-2027/acervo"
AM = "/Users/ugopirangi/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/AME CRIANCA/MEDIAKIT/copa-ame-v2/acervo"
Y, K = "#F5D80A", "#0B0B0C"
GOLD, CREAM, SEA, MINT, CORAL = "#D4A64A", "#F3E3B5", "#0F3550", "#9FE3D0", "#E9603A"
HERE = os.path.dirname(os.path.abspath(__file__))

class Doc:
    def __init__(self, rid, w=1440, h=810, **kw):
        self.rid = rid; self.dir = os.path.join(HERE, rid); os.makedirs(self.dir, exist_ok=True)
        self.vc = VC(); self.w, self.h = w, h
        self.vc.ex("file.new", dict(width=w, height=h, units="Points", **kw))
    def ex(self, c, p=None): return self.vc.ex(c, p)
    def paint(self, oid, fill=None, stroke=None, sw=1, opacity=None):
        self.ex("select.set", {"ids": [oid]})
        self.ex("paint.setFill", {"none": True} if fill is None else (fill if isinstance(fill, dict) and "c" not in fill and "gray" not in fill else {"color": fill}))
        if stroke is None: self.ex("paint.setStroke", {"none": True})
        else:
            self.ex("paint.setStroke", {"color": stroke}); self.ex("stroke.set", {"weight": sw})
        if opacity is not None: self.ex("transparency.set", {"ids": [oid], "opacity": opacity})
        self.ex("select.none"); return oid
    def rect(self, x, y, w, h, fill=K, stroke=None, sw=1, radius=None, opacity=None, rotation=None):
        p = dict(x=x, y=y, width=w, height=h)
        if radius: p["radius"] = radius
        if rotation: p["rotation"] = rotation
        return self.paint(self.ex("shape.rectangle", p)["id"], fill, stroke, sw, opacity)
    def ellipse(self, x, y, w, h, fill=K, stroke=None, sw=1, opacity=None):
        return self.paint(self.ex("shape.ellipse", dict(x=x, y=y, width=w, height=h))["id"], fill, stroke, sw, opacity)
    def image(self, path, x, y, w, h=None):
        oid = self.ex("file.place", {"path": path, "link": False})["ids"][0]
        self.ex("select.set", {"ids": [oid]})
        p = dict(x=x, y=y, width=w, reference=0)
        if h: p["height"] = h
        else: p["proportional"] = True
        self.ex("object.setBounds", p); self.ex("select.none"); return oid
    def text(self, x, y, s, font="Helvetica Neue", style="Bold", size=40, color="#FFFFFF", **st):
        oid = self.ex("text.create", dict(x=x, y=y, text=s, font=font, style=style, size=size, color=color))["id"]
        if st: self.ex("text.setStyle", dict(ids=[oid], **st))
        return oid
    def export(self, name="teste.pdf", **kw):
        path = os.path.join(self.dir, name)
        p = dict(path=path, preserveEditing=False); p.update(kw)
        r = self.ex("document.exportPdf", p)
        out = subprocess.run(["pdftoppm", "-r", "50", "-png", path, os.path.join(self.dir, "preview")], capture_output=True, text=True)
        print("export", r, out.stderr[:200]); return path
    def close(self): self.vc.close()

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
def report(path):
    print(subprocess.run(f'ls -la "{path}"; pdffonts "{path}"; pdfimages -list "{path}"', shell=True, capture_output=True, text=True).stdout)

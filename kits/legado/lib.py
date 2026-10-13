import json, math, os
from PIL import Image, ImageOps, ImageEnhance
from vc import ex

ACERVO = "/Users/ugopirangi/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/AME CRIANCA/MEDIAKIT/copa-ame-v2/acervo"
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)

K = "#0B0B0C"      # preto da AME
Y = "#F5D80A"      # amarelo da AME (o laranja da Nike vira este)
W = "#F2F0E8"      # branco quente
G = "#26262A"      # cinza do mapa e da grade
PW, PH = 1920, 1080
GAP = 2000

DISPLAY = ("Helvetica Neue", "Condensed Black")
HEAD = ("Helvetica Neue", "Bold")
BODY = ("Helvetica Neue", "Medium")


class Page:
    def __init__(self, idx):
        self.i = idx
        self.ox = idx * GAP
        if idx > 0:
            ex("artboard.new", {"x": self.ox, "y": 0, "width": PW, "height": PH})

    # ---- primitivas -------------------------------------------------------
    def _paint(self, oid, fill=None, stroke=None, sw=None, opacity=None):
        ex("select.set", {"ids": [oid]})
        if fill is None:
            ex("paint.setFill", {"none": True})
        else:
            ex("paint.setFill", {"color": fill})
        if stroke is None:
            ex("paint.setStroke", {"none": True})
        else:
            ex("paint.setStroke", {"color": stroke})
            ex("stroke.set", {"weight": sw or 1})
        if opacity is not None:
            ex("transparency.set", {"ids": [oid], "opacity": opacity})
        ex("select.none")
        return oid

    def rect(self, x, y, w, h, fill=K, stroke=None, sw=None, radius=None, opacity=None):
        p = {"x": self.ox + x, "y": y, "width": w, "height": h}
        if radius:
            p["radius"] = radius
        oid = ex("shape.rectangle", p)["id"]
        return self._paint(oid, fill, stroke, sw, opacity)

    def ellipse(self, cx, cy, rx, ry, fill=K, stroke=None, sw=None):
        oid = ex("shape.ellipse", {"x": self.ox + cx - rx, "y": cy - ry, "width": 2 * rx, "height": 2 * ry})["id"]
        return self._paint(oid, fill, stroke, sw)

    def star(self, cx, cy, r, fill=Y):
        oid = ex("shape.star", {"cx": self.ox + cx, "cy": cy, "radius1": r, "radius2": r * 0.42, "points": 5})["id"]
        return self._paint(oid, fill)

    def path(self, d, fill=None, stroke=None, sw=None, opacity=None):
        oid = ex("path.create", {"d": d})["id"]
        return self._paint(oid, fill, stroke, sw, opacity)

    def poly_d(self, pts, closed=True):
        s = "M" + " L".join(f"{self.ox + x:.2f},{y:.2f}" for x, y in pts)
        return s + (" Z" if closed else "")

    def image(self, file, x, y, w, h):
        r = ex("file.place", {"path": file, "link": False})
        oid = r["ids"][0]
        ex("select.set", {"ids": [oid]})
        ex("object.setBounds", {"x": self.ox + x, "y": y, "width": w, "height": h, "reference": 0})
        ex("select.none")
        return oid

    # ---- texto ------------------------------------------------------------
    def text(self, x, y, s, font=HEAD, size=40, color=W, tracking=None, leading=None,
             justify=None, width=None, features=None):
        p = {"x": self.ox + x, "y": y, "text": s, "font": font[0], "style": font[1],
             "size": size, "color": color}
        if width:
            p["area"] = {"width": width, "height": 2000, "fit": "autoHeight"}
        oid = ex("text.create", p)["id"]
        st = {"ids": [oid]}
        if tracking is not None:
            st["tracking"] = tracking
        if leading is not None:
            st["leading"] = leading
        if justify:
            st["justify"] = justify
        if features:
            st["features"] = features
        if len(st) > 1:
            ex("text.setStyle", st)
        return oid

    def fit(self, x, y, s, max_w, font=DISPLAY, size=300, color=Y, tracking=None, leading=None,
            justify=None, max_h=None):
        """Cria o texto e escala o corpo até a linha mais longa caber em max_w (e max_h)."""
        oid = self.text(x, y, s, font, size, color, tracking, leading, justify)
        b = bounds(oid)
        k = max_w / b["width"]
        if max_h:
            k = min(k, max_h / b["height"])
        ns = size * k
        st = {"ids": [oid], "size": ns}
        if leading is not None:
            st["leading"] = leading * k
        ex("text.setStyle", st)
        return oid, ns

    def label(self, x, y, s, color=W):
        return self.text(x, y, s.upper(), HEAD, 13, color, tracking=180)

    # ---- elementos do sistema --------------------------------------------
    def strip(self, y, color=Y, x0=64, x1=PW - 64, n=2):
        """A faixa de informação que repete, como a linha BRASIL · SÃO PAULO · 2025 do Nike Run."""
        unit = [("big", "COPA AME"), ("micro", "SÃO JOSÉ DO RIO PRETO · SP\nSUB-06 AO SUB-20 · 2027"),
                ("mark", None), ("big", "2027")]
        widths = strip_widths()
        uw = sum(widths) + 3 * 28
        gap = ((x1 - x0) - n * uw) / (n - 1) if n > 1 else 0
        x = x0
        for _ in range(n):
            for (kind, s), w in zip(unit, widths):
                if kind == "big":
                    self.text(x, y + 12, s, HEAD, 36, color, tracking=-10)
                elif kind == "micro":
                    self.text(x, y - 4, s, HEAD, 12, color, tracking=40, leading=13)
                else:
                    self.mark(x, y - 18, w, color)
                x += w + 28
            x += gap - 28

    def mark(self, x, y, w, color=Y):
        """Assinatura: a trajetória da bola. Arco que afina, terminando numa bola."""
        h = w * 0.42
        pts_top, pts_bot = [], []
        n = 40
        for k in range(n + 1):
            t = k / n
            # curva quadrática da esquerda baixa até a direita alta
            p0, p1, p2 = (0, h * 0.95), (w * 0.38, h * 1.05), (w * 0.86, h * 0.22)
            bx = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            by = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
            dx = 2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0])
            dy = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])
            L = math.hypot(dx, dy) or 1
            nx, ny = -dy / L, dx / L
            half = h * 0.13 * math.sin(math.pi * min(t, 0.999) ** 0.8) ** 0.9
            pts_top.append((x + bx + nx * half, y + by + ny * half))
            pts_bot.append((x + bx - nx * half, y + by - ny * half))
        self.path(self.poly_d(pts_top + pts_bot[::-1]), fill=color)
        self.ellipse(x + w * 0.93, y + h * 0.16, w * 0.07, w * 0.07, fill=color)

    def tag(self, x, y, s, fill=Y, color=K):
        """Etiqueta "IMAGEM ILUSTRATIVA" das cenas geradas (regra da skill: cena gerada nunca vira registro)."""
        tid = self.text(x, y, s.upper(), HEAD, 12, color, tracking=160)
        b = bounds(tid)
        bg = self.rect(b["x"] - self.ox - 10, b["y"] - 7, b["width"] + 20, b["height"] + 14, fill=fill)
        ex("select.set", {"ids": [bg]})
        ex("object.arrange.sendBackward")
        ex("select.none")


_SW = None


def strip_widths():
    global _SW
    if _SW is None:
        # mede uma vez numa área fora das páginas e apaga
        ids = []
        ws = []
        for kind, s, f, sz, tr in [("big", "COPA AME", HEAD, 36, -10),
                                   ("micro", "SÃO JOSÉ DO RIO PRETO · SP\nSUB-06 AO SUB-20 · 2027", HEAD, 12, 40)]:
            oid = ex("text.create", {"x": -5000, "y": -5000, "text": s, "font": f[0], "style": f[1], "size": sz})["id"]
            ex("text.setStyle", {"ids": [oid], "tracking": tr, **({"leading": 13} if kind == "micro" else {})})
            ws.append(bounds(oid)["width"])
            ids.append(oid)
        oid = ex("text.create", {"x": -5000, "y": -5000, "text": "2027", "font": HEAD[0], "style": HEAD[1], "size": 36})["id"]
        ex("text.setStyle", {"ids": [oid], "tracking": -10})
        w2027 = bounds(oid)["width"]
        ids.append(oid)
        ex("select.set", {"ids": ids})
        ex("edit.clear")
        _SW = [ws[0], ws[1], 58, w2027]
    return _SW


def _find(node, oid):
    if node.get("id") == oid and node.get("kind") != "Layer":
        return node
    for c in node.get("children", []) or []:
        r = _find(c, oid)
        if r:
            return r
    return None


def bounds(oid):
    d = ex("document.inspect", {"depth": 3})
    for L in d["layers"]:
        r = _find(L, oid)
        if r:
            return r["bounds"]
    raise KeyError(oid)


# ---- fotos (tratamento raster acontece antes, nunca no arquivo vetorial) ----
def prep(src, name, w, h, mode="bw", focus=(0.5, 0.5), mirror=False):
    out = os.path.join(ASSETS, name + ".jpg")
    im = Image.open(os.path.join(ACERVO, src)).convert("RGB")
    if mirror:
        im = ImageOps.mirror(im)
    ar = w / h
    iw, ih = im.size
    if iw / ih > ar:
        cw, ch = ih * ar, ih
    else:
        cw, ch = iw, iw / ar
    cx = min(max(focus[0] * iw, cw / 2), iw - cw / 2)
    cy = min(max(focus[1] * ih, ch / 2), ih - ch / 2)
    im = im.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2)))
    scale = min(1.0, max(w, h) * 1.25 / max(im.size))
    im = im.resize((max(1, int(im.size[0] * scale)), max(1, int(im.size[1] * scale))), Image.LANCZOS)
    if mode == "bw":
        g = ImageOps.grayscale(im)
        g = ImageOps.autocontrast(g, cutoff=1)
        g = g.point(lambda v: int(255 * (1 / (1 + math.exp(-(v / 255 - 0.5) * 7)) - 0.029) / 0.942))
        im = g.convert("RGB")
    elif mode == "warm":
        im = ImageEnhance.Contrast(im).enhance(1.12)
        r, gch, b = im.split()
        r = r.point(lambda v: min(255, int(v * 1.04)))
        b = b.point(lambda v: int(v * 0.9))
        im = Image.merge("RGB", (r, gch, b))
        im = ImageEnhance.Color(im).enhance(0.92)
    im.save(out, quality=88)
    return out


def prep_cutout(src, name, mode="bw"):
    out = os.path.join(ASSETS, name + ".png")
    im = Image.open(os.path.join(ACERVO, src)).convert("RGBA")
    if mode == "bw":
        a = im.split()[3]
        g = ImageOps.autocontrast(ImageOps.grayscale(im.convert("RGB")), cutoff=1)
        g = g.point(lambda v: int(255 * (1 / (1 + math.exp(-(v / 255 - 0.5) * 6)) - 0.047) / 0.906))
        im = Image.merge("RGBA", (g, g, g, a))
    im.save(out)
    return out


# ---- mapa de SP (IBGE) ------------------------------------------------------
CIDADES = {
    "SÃO JOSÉ DO RIO PRETO": (-49.3758, -20.8113),
    "ARAÇATUBA": (-50.4328, -21.2089),
    "TAQUARITINGA": (-48.5103, -21.4049),
    "BAURU": (-49.0871, -22.3246),
}


def sp_shape():
    d = json.load(open(os.path.join(HERE, "sp.json")))
    g = d["features"][0]["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    main = max(polys, key=lambda p: len(p[0]))[0]
    return main


def projector(box, ring):
    """box = (x, y, w, h). Projeção equirretangular corrigida na latitude média."""
    lons = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    lat0 = math.radians(sum(lats) / len(lats))
    xs = [lo * math.cos(lat0) for lo in lons]
    minx, maxx, miny, maxy = min(xs), max(xs), min(lats), max(lats)
    s = min(box[2] / (maxx - minx), box[3] / (maxy - miny))
    ox = box[0] + (box[2] - (maxx - minx) * s) / 2
    oy = box[1] + (box[3] - (maxy - miny) * s) / 2

    def f(lon, lat):
        return (ox + (lon * math.cos(lat0) - minx) * s, oy + (maxy - lat) * s)
    return f


def simplify(pts, step=2):
    return pts[::step]

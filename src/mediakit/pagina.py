"""Primitivas de página sobre o VectorCraft. Cada Pagina é um artboard; coordenadas em unidades da página (1920 × 1080)."""
from pathlib import Path

from PIL import Image

from mediakit import config
from mediakit.fotos import ppi_na_pagina

PRETO, BRANCO = "#000000", "#FFFFFF"
NEGRITO = ("Helvetica Neue", "Bold")


def _achar(no, oid):
    if no.get("id") == oid and no.get("kind") != "Layer":
        return no
    for c in no.get("children", []) or []:
        r = _achar(c, oid)
        if r:
            return r
    return None


def bounds(ex, oid):
    d = ex("document.inspect", {"depth": 3})
    for camada in d["layers"]:
        r = _achar(camada, oid)
        if r:
            return r["bounds"]
    raise KeyError(oid)


class Pagina:
    def __init__(self, ex, idx, pw=1920, ph=1080, gap=2000, avisos=None, aceitas=None):
        self.ex, self.i, self.pw, self.ph = ex, idx, pw, ph
        self.avisos = avisos if avisos is not None else []
        self.aceitas = aceitas if aceitas is not None else []
        self.ox = idx * gap
        if idx > 0:
            ex("artboard.new", {"x": self.ox, "y": 0, "width": pw, "height": ph})

    def aceitar_sobreposicao(self, a, b, motivo):
        """Declara que o texto a encosta no texto b de propósito (ex.: letreiro cursivo entrelaçado). A checagem
        pela tinta mostra isso como aceito, com o motivo, em vez de falha."""
        self.aceitas.append({"pagina": self.i + 1, "a": a, "b": b, "motivo": motivo})

    def _pintar(self, oid, fill=None, stroke=None, sw=None, opacity=None):
        ex = self.ex
        ex("select.set", {"ids": [oid]})
        ex("paint.setFill", {"none": True} if fill is None else {"color": fill})
        if stroke is None:
            ex("paint.setStroke", {"none": True})
        else:
            ex("paint.setStroke", {"color": stroke})
            ex("stroke.set", {"weight": sw or 1})
        if opacity is not None:
            ex("transparency.set", {"ids": [oid], "opacity": opacity})
        ex("select.none")
        return oid

    def rect(self, x, y, w, h, fill=PRETO, stroke=None, sw=None, radius=None, opacity=None):
        p = {"x": self.ox + x, "y": y, "width": w, "height": h}
        if radius:
            p["radius"] = radius
        return self._pintar(self.ex("shape.rectangle", p)["id"], fill, stroke, sw, opacity)

    def ellipse(self, cx, cy, rx, ry, fill=PRETO, stroke=None, sw=None):
        oid = self.ex("shape.ellipse", {"x": self.ox + cx - rx, "y": cy - ry, "width": 2 * rx, "height": 2 * ry})["id"]
        return self._pintar(oid, fill, stroke, sw)

    def path(self, d, fill=None, stroke=None, sw=None, opacity=None):
        return self._pintar(self.ex("path.create", {"d": d})["id"], fill, stroke, sw, opacity)

    def poly_d(self, pts, closed=True):
        s = "M" + " L".join(f"{self.ox + x:.2f},{y:.2f}" for x, y in pts)
        return s + (" Z" if closed else "")

    def image(self, file, x, y, w, h, aceito=None):
        """Põe a imagem na caixa w × h e mede a resolução que ela terá no PDF. Abaixo de 96 ppi vira aviso
        (ou registro de "aceito", com o motivo, quando a imagem é baixa de propósito: textura, cena gerada)."""
        with Image.open(file) as im:
            ppi = ppi_na_pagina(im.size[0], w)
        nome = Path(file).name
        if ppi < config.PPI_MINIMO and not any(a["arquivo"] == nome and a["pagina"] == self.i + 1 for a in self.avisos):
            self.avisos.append({"arquivo": nome, "pagina": self.i + 1, "ppi": round(ppi), "caixa": [round(w), round(h)],
                                "aceito": aceito})
        oid = self.ex("file.place", {"path": str(file), "link": False})["ids"][0]
        self.ex("select.set", {"ids": [oid]})
        self.ex("object.setBounds", {"x": self.ox + x, "y": y, "width": w, "height": h, "reference": 0})
        self.ex("select.none")
        return oid

    def text(self, x, y, s, font=NEGRITO, size=40, color=BRANCO, tracking=None, leading=None,
             justify=None, width=None, features=None):
        p = {"x": self.ox + x, "y": y, "text": s, "font": font[0], "style": font[1], "size": size, "color": color}
        if width:
            p["area"] = {"width": width, "height": 2000, "fit": "autoHeight"}
        oid = self.ex("text.create", p)["id"]
        st = {"ids": [oid]}
        for k, v in (("tracking", tracking), ("leading", leading), ("justify", justify), ("features", features)):
            if v is not None:
                st[k] = v
        if len(st) > 1:
            self.ex("text.setStyle", st)
        return oid

    def fit(self, x, y, s, max_w, font=NEGRITO, size=300, color=BRANCO, tracking=None, leading=None,
            justify=None, max_h=None):
        """Cria o texto e escala o corpo até a linha mais longa ter max_w (e caber em max_h).
        Atenção: o `size` passado é só o ponto de partida; quem manda no tamanho final é max_w."""
        oid = self.text(x, y, s, font, size, color, tracking, leading, justify)
        b = bounds(self.ex, oid)
        k = max_w / b["width"]
        if max_h:
            k = min(k, max_h / b["height"])
        st = {"ids": [oid], "size": size * k}
        if leading is not None:
            st["leading"] = leading * k
        self.ex("text.setStyle", st)
        return oid, size * k

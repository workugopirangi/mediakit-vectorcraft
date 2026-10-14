#!/usr/bin/env python3
"""
compor.py — aplica lettering, logo ou placeholder "SEU LOGO AQUI" sobre uma cena, em perspectiva, herdando a luz da foto.

Por que existe: texto gerado pelo modelo de imagem é a dimensão mais fraca de todos os modelos (pesquisa, regra 39).
A cena é gerada SEM texto, com painéis lisos; o lettering entra aqui por composição (Pillow QUAD + multiply de luminância).

Uso:
  python3 compor.py <cena.png> <saida.png> --quad x1,y1,x2,y2,x3,y3,x4,y4 [--logo arquivo.png | --texto "SEU LOGO AQUI"] [--cor #FFFFFF] [--fundo #E8307A] [--opacidade 0.96] [--fonte <ttf>]
  python3 compor.py <cena.png> <saida.png> --lote composicoes.json

  --quad: 4 cantos do painel na cena, em px, no sentido horário a partir do canto superior esquerdo.
  --lote: lista [{"quad":[...], "texto":..., "logo":..., "cor":..., "fundo":...}, ...] para várias aplicações na mesma cena.

Como funciona:
  1. Renderiza o conteúdo (logo PNG transparente ou texto em caixa alta na fonte display) num retângulo plano.
  2. Mapeia o retângulo para o quadrilátero da cena (Image.transform PERSPECTIVE, coeficientes resolvidos por mínimos quadrados).
  3. Multiplica pela luminância local da cena (sombras e dobras da superfície passam para o lettering) e mistura com a opacidade dada.
  4. Para tecido ondulado (camiseta) use --mesh (pendente): divide o quad em células e deforma cada uma.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONTES = ["/Library/Fonts/RocGrotesk-WideExtraBold.otf", "/Library/Fonts/Anton-Regular.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/System/Library/Fonts/Supplemental/Impact.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]


def fonte(tam):
    for f in FONTES:
        if Path(f).exists():
            return ImageFont.truetype(f, tam)
    # sem nenhuma fonte da lista, load_default() tem tamanho fixo e o texto sai microscópico (visto em 08/10/2026); com tam escala
    return ImageFont.load_default(tam)


def coef_perspectiva(src, dst):
    """Coeficientes para Image.transform(PERSPECTIVE): mapeia dst (saída) → src (entrada)."""
    m = []
    for (x, y), (X, Y) in zip(dst, src):
        m.append([x, y, 1, 0, 0, 0, -X * x, -X * y])
        m.append([0, 0, 0, x, y, 1, -Y * x, -Y * y])
    A = np.array(m, dtype=float); b = np.array([c for p in src for c in p], dtype=float)
    return np.linalg.lstsq(A, b, rcond=None)[0]


def render_conteudo(w, h, texto=None, logo=None, cor="#FFFFFF", fundo=None, margem=0.12):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if fundo:
        d.rectangle([0, 0, w, h], fill=fundo)
    if logo:
        lg = Image.open(logo).convert("RGBA")
        mw, mh = int(w * (1 - 2 * margem)), int(h * (1 - 2 * margem))
        lg.thumbnail((mw, mh), Image.LANCZOS)
        im.alpha_composite(lg, ((w - lg.width) // 2, (h - lg.height) // 2))
    elif texto:
        tam = h; linhas = texto.upper().split("|")
        while tam > 8:
            f = fonte(tam)
            larg = max(d.textbbox((0, 0), l, font=f)[2] for l in linhas); alt = sum(d.textbbox((0, 0), l, font=f)[3] for l in linhas) + (len(linhas) - 1) * tam * 0.15
            if larg <= w * (1 - 2 * margem) and alt <= h * (1 - 2 * margem):
                break
            tam = int(tam * 0.92)
        f = fonte(tam); y = (h - alt) / 2
        for l in linhas:
            bb = d.textbbox((0, 0), l, font=f)
            d.text(((w - bb[2]) / 2, y - bb[1]), l, font=f, fill=cor)
            y += bb[3] + tam * 0.15
    return im


def aplicar(cena: Image.Image, quad, texto=None, logo=None, cor="#FFFFFF", fundo=None, opacidade=0.96, luz=True):
    W, H = cena.size
    xs, ys = [p[0] for p in quad], [p[1] for p in quad]
    w = int(max(np.hypot(quad[1][0] - quad[0][0], quad[1][1] - quad[0][1]), np.hypot(quad[2][0] - quad[3][0], quad[2][1] - quad[3][1])))
    h = int(max(np.hypot(quad[3][0] - quad[0][0], quad[3][1] - quad[0][1]), np.hypot(quad[2][0] - quad[1][0], quad[2][1] - quad[1][1])))
    w, h = max(w, 16), max(h, 16)
    conteudo = render_conteudo(w, h, texto, logo, cor, fundo)
    coef = coef_perspectiva([(0, 0), (w, 0), (w, h), (0, h)], quad)
    warp = conteudo.transform((W, H), Image.PERSPECTIVE, coef, Image.BICUBIC)
    if luz:
        # luminância local da cena, suavizada: transfere sombra e dobra para o conteúdo
        # relativa à média do PRÓPRIO painel: em painel preto a luminância absoluta (~.1) deixava logo branco cinza (08/10/2026)
        L = cena.convert("L").filter(ImageFilter.GaussianBlur(3))
        Ln = np.asarray(L, dtype=float) / 255.0
        dentro = np.asarray(warp.split()[3]) > 0
        media = Ln[dentro].mean() if dentro.any() else 0.5
        fator = np.clip(1 + (Ln - media) * 0.9, 0.6, 1.2)[..., None]
        rgb = np.asarray(warp.convert("RGB"), dtype=float) * fator
        warp = Image.merge("RGBA", (*Image.fromarray(np.clip(rgb, 0, 255).astype("uint8")).split(), warp.split()[3]))
    a = warp.split()[3].point(lambda v: int(v * opacidade))
    warp.putalpha(a)
    out = cena.convert("RGBA"); out.alpha_composite(warp)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cena"); ap.add_argument("saida")
    ap.add_argument("--quad"); ap.add_argument("--texto"); ap.add_argument("--logo"); ap.add_argument("--cor", default="#FFFFFF"); ap.add_argument("--fundo"); ap.add_argument("--opacidade", type=float, default=0.96)
    ap.add_argument("--lote"); ap.add_argument("--sem-luz", action="store_true")
    ap.add_argument("--fonte", help="TTF/OTF do display do kit (ex.: <pasta>/fontes/Anton.ttf); entra antes da lista padrão")
    a = ap.parse_args()
    if a.fonte:
        FONTES.insert(0, a.fonte)
    cena = Image.open(a.cena).convert("RGBA")
    itens = json.loads(Path(a.lote).read_text()) if a.lote else [dict(quad=[int(v) for v in a.quad.split(",")], texto=a.texto, logo=a.logo, cor=a.cor, fundo=a.fundo, opacidade=a.opacidade)]
    for it in itens:
        q = it["quad"]; quad = [(q[i], q[i + 1]) for i in range(0, 8, 2)]
        cena = aplicar(cena, quad, it.get("texto"), it.get("logo"), it.get("cor", "#FFFFFF"), it.get("fundo"), it.get("opacidade", 0.96), luz=not a.sem_luz)
    cena.convert("RGB").save(a.saida, quality=94)
    print("OK", a.saida)


if __name__ == "__main__":
    main()

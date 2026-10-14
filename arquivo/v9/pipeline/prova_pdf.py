#!/usr/bin/env python3
"""
prova_pdf.py: a lista branca PROVADA dos efeitos CSS da camada de acabamento (references/10-acabamento.md, "Efeitos
permitidos e proibidos"). Um efeito só entra no HTML do kit se sair do Chromium para o PDF como vetor, texto e imagem
que já existia: sem raster novo, sem fonte Type 3, sem perder texto.

  ~/.venvs/mediakit/bin/python pipeline/prova_pdf.py [--saida <pasta>] [nome ...]

Para cada efeito, três páginas mínimas de 800×450 (um rótulo em texto vivo e o nó do efeito, nas fontes do kit de prova),
renderizadas pelo mesmo Chromium do render (Playwright, PDF e PNG):
  base      o mesmo conteúdo sem o efeito (a régua dos bytes e da contagem de imagens)
  bom       o efeito
  mutante   o MESMO nó do bom com `filter: saturate(1.4)` (o filtro mais inocente que existe: só cor)
e cinco checagens no PDF:
  1. fontes   pdffonts: nenhuma fonte Type 3
  2. imagens  pdfimages: os objetos de imagem distintos, pelo CONTEÚDO (pixels extraídos), são os mesmos da base: raster
              novo ou imagem refeita (o filtro de cor reescreve o PNG embutido) = falha
  3. texto    pdftotext: os textos da página saem como texto
  4. raster   pdftoppm (96 ppi, 1 px = 1 px) contra o PNG do Chromium, na região do efeito: diferença média por canal
  5. bytes    bytes que o efeito acrescenta ao PDF da base, até o limite do efeito
O bom passa nas cinco; o mutante tem de falhar em pelo menos uma. Os PROIBIDOS (perspective, matrix3d, text-shadow,
stroke em <text>, background-clip: text, mask-image com gradiente, filter) rodam do mesmo jeito: cada um tem de ser
acusado por pelo menos uma checagem, e é isso que os põe na lista negra com prova, não com palpite. Cada proibido roda no
caso em que a medição de 12/10/2026 mostrou o estrago; as variantes que passaram limpas estão escritas em references/10
(perspective em texto com giro leve e em recorte, mask-image com gradiente sobre foto: sem sinal no PDF do Chromium).
mask-image com PNG de alfa é aceito (o PNG vira máscara do PDF, como o alfa de qualquer recorte).

Provas: pipeline/test_prova_pdf.py. Sai com 1 se um bom falhar ou se um mutante ou proibido passar despercebido.
"""
import argparse, base64, io, json, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
FONTES = AQUI.parent / "exemplos" / "acabamento-prova" / "fontes"
W, H = 800, 450
MUTANTE = "filter:saturate(1.4);"
LIMITE_RASTER = 3.0          # diferença média por canal (0 a 255) entre o PDF rasterizado e o PNG do Chromium
CHECAGENS = ("fontes", "imagens", "texto", "raster", "bytes")


# ------------------------------------------------------------------------------------------------- insumos
def _uri(im, fmt="PNG"):
    b = io.BytesIO(); im.save(b, fmt, optimize=True)
    return f"data:image/{fmt.lower()};base64," + base64.b64encode(b.getvalue()).decode()


def png_recorte():
    """240×240 com alfa: disco laranja com anel (o recorte de objeto de sempre, PNG com SMask)."""
    im = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((20, 20, 220, 220), fill=(242, 107, 29, 255))
    d.ellipse((70, 70, 170, 170), fill=(255, 200, 97, 255))
    d.rectangle((110, 0, 130, 60), fill=(244, 239, 230, 255))
    return _uri(im)


def png_foto():
    """240×240 opaco: listras e degradê (a foto que a máscara recorta)."""
    y, x = np.mgrid[0:240, 0:240]
    r = (40 + 180 * x / 239).astype(np.uint8)
    g = (60 + 120 * ((x // 20 + y // 20) % 2)).astype(np.uint8)
    b = (200 - 160 * y / 239).astype(np.uint8)
    return _uri(Image.fromarray(np.dstack([r, g, b]), "RGB"))


def path_contorno(texto="LUA", tamanho=120, x0=40.0, base=170.0):
    """`d` do contorno das letras pela fonte do kit (fontTools), como o eco 'contorno-path' do grafismos.py desenha:
    desenho, não texto."""
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont
    f = TTFont(str(FONTES / "Anton.ttf"))
    gs, cmap = f.getGlyphSet(), f.getBestCmap()
    esc = tamanho / f["head"].unitsPerEm
    caneta = SVGPathPen(gs)
    x = x0
    for ch in texto:
        nome = cmap[ord(ch)]
        gs[nome].draw(TransformPen(caneta, (esc, 0, 0, -esc, x, base)))
        x += gs[nome].width * esc
    return caneta.getCommands()


def css_base():
    faces = []
    for nome, arq in (("Anton", "Anton.ttf"), ("DM Sans", "DM Sans.ttf")):
        b = base64.b64encode((FONTES / arq).read_bytes()).decode()
        faces.append(f"@font-face{{font-family:'{nome}';src:url(data:font/ttf;base64,{b}) format('truetype');"
                     f"font-weight:100 900;font-style:normal;font-display:block}}")
    return "\n".join(faces) + f"""
html,body{{margin:0;padding:0;background:#0B1A2E;font-synthesis:none}}
.pagina{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:#0B1A2E}}
.rotulo{{position:absolute;left:32px;top:20px;font:400 26px 'DM Sans';color:#FFFFFF}}
.claro{{position:absolute;left:260px;top:100px;width:320px;height:290px;background:#F4EFE6}}
.titulo{{position:absolute;left:40px;top:150px;margin:0;font:400 120px/1 'Anton';color:#FFFFFF;letter-spacing:0}}
@page{{size:{W}px {H}px;margin:0}}
"""


def _img(src, estilo, id_="ef"):
    return f'<img id="{id_}" src="{src}" alt="" style="position:absolute;left:300px;top:120px;width:240px;height:240px;{estilo}">'


def casos():
    """{nome: caso}. Cada caso: rotulo (texto vivo da página), base e bom (HTML com {f} no estilo do nó do efeito: o
    mutante põe o filtro ali), textos (o que tem de sair como texto), imagens (objetos de imagem que o efeito acrescenta à
    base), limite (bytes que o efeito pode acrescentar), proibido (True: tem de ser acusado)."""
    rec, foto = png_recorte(), png_foto()
    luz = ("linear-gradient(in oklab 90deg, rgb(255 255 255 / .14) 0%, rgb(255 255 255 / .07) 24%, "
           "rgb(255 255 255 / .02) 48%, rgb(255 255 255 / 0) 72%)")
    d = path_contorno()
    eco = "".join(f'<text x="{40 + 24 * i}" y="{170 + 24 * i}" font-family="Anton" font-size="120" fill="#F26B1D" '
                  f'opacity="{o}">LUA</text>' for i, o in enumerate((0.24, 0.12, 0.06)))
    prova = "PROIBIDO"
    c = {
        # ---------------------------------------------------------------- lista branca
        "opacidade-blend": dict(
            rotulo="opacidade e blend no nó",
            base='<div class="claro"></div>' + _img(rec, "{f}"),
            bom='<div class="claro"></div>' + _img(rec, "opacity:.46;mix-blend-mode:multiply;{f}"),
            textos=[], imagens=0, limite=2048),
        "clip-polygon": dict(
            rotulo="clip-path polygon (diagonal, chanfro, arco-base)",
            base=_img(foto, "{f}"),
            bom=_img(foto, "clip-path:polygon(25.5px 0,100% 0,100% 100%,0 100%,0 120px);{f}"),
            textos=[], imagens=0, limite=2048),
        "clip-circle": dict(
            rotulo="clip-path circle (circulo)",
            base=_img(foto, "{f}"),
            bom=_img(foto, "clip-path:circle(120px at 120px 120px);{f}"),
            textos=[], imagens=0, limite=2048),
        "clip-inset": dict(
            rotulo="clip-path inset com raio (janela, recorte)",
            base=_img(foto, "{f}"),
            bom=_img(foto, "clip-path:inset(0 round 120px 120px 0 0);{f}"),
            textos=[], imagens=0, limite=2048),
        "veu-de-luz": dict(
            rotulo="véu de luz oklab, 4 paradas, screen",
            base=_img(foto, "", "foto"),
            bom=_img(foto, "", "foto") + f'<div id="ef" style="position:absolute;inset:0;pointer-events:none;'
                                        f'mix-blend-mode:screen;background:{luz};{{f}}"></div>',
            # o véu é shading (função amostrada da interpolação oklab) com máscara de luminância: +15,2 KB medidos; o
            # mesmo véu rasterizado (o mutante) custa +207 KB
            textos=[], imagens=0, limite=24576, regiao=(0, 0, W, H)),
        "cruza-duas-copias": dict(
            rotulo="duas cópias com corte (cruza)",
            base='<h1 class="titulo">TRAVESSIA</h1>' + _img(rec, "z-index:3;{f}"),
            bom=(_img(rec, "z-index:1;clip-path:inset(0 0 120px 0);{f}") + '<h1 class="titulo" style="z-index:2">TRAVESSIA</h1>'
                 + _img(rec, "z-index:3;clip-path:inset(120px 0 0 0)", "ef2")),
            textos=["TRAVESSIA"], imagens=0, limite=2048, regiao=(40, 100, 760, 400)),
        "eco-texto-preenchido": dict(
            rotulo="eco por texto preenchido",
            base='<svg id="ef" width="760" height="300" style="position:absolute;left:0;top:120px;{f}"></svg>',
            bom=f'<svg id="ef" width="760" height="300" style="position:absolute;left:0;top:120px;{{f}}">{eco}</svg>',
            # +5,8 KB medidos: é o subconjunto da Anton que o texto vivo embute (a base não usa a Anton)
            textos=["LUA"], imagens=0, limite=8192, regiao=(0, 120, 760, 420)),
        "contorno-path": dict(
            rotulo="contorno como path",
            base='<svg id="ef" width="760" height="300" style="position:absolute;left:0;top:120px;{f}"></svg>',
            bom=(f'<svg id="ef" width="760" height="300" style="position:absolute;left:0;top:120px;{{f}}">'
                 f'<path d="{d}" fill="none" stroke="#F26B1D" stroke-width="1.5"/></svg>'),
            textos=[], imagens=0, limite=6144, regiao=(0, 120, 760, 420)),
        "mascara-png-alfa": dict(
            rotulo="mask-image com PNG de alfa",
            base='<div id="ef" style="position:absolute;left:300px;top:120px;width:240px;height:240px;background:#F26B1D;{f}"></div>',
            bom=(f'<div id="ef" style="position:absolute;left:300px;top:120px;width:240px;height:240px;background:#F26B1D;'
                 f'-webkit-mask-image:url({rec});mask-image:url({rec});-webkit-mask-size:100% 100%;mask-size:100% 100%;{{f}}"></div>'),
            textos=[], imagens=None, limite=16384),
        # ---------------------------------------------------------------- proibidos
        "perspective-foto": dict(
            rotulo="proibido: perspective em foto", proibido=True,
            base=_img(foto, "{f}"),
            bom=_img(foto, "transform:perspective(400px) rotateY(28deg);{f}"),
            textos=[], imagens=0, limite=4096),
        "perspective-texto": dict(
            rotulo="proibido: perspective em texto", proibido=True,
            base=f'<div id="ef" class="titulo" style="{{f}}">{prova}</div>',
            bom=f'<div id="ef" class="titulo" style="transform:perspective(200px) rotateX(40deg);{{f}}">{prova}</div>',
            textos=[prova], imagens=0, limite=4096),
        "matrix3d": dict(
            rotulo="proibido: matrix3d", proibido=True,
            base=f'<div id="ef" class="titulo" style="{{f}}">{prova}</div>',
            bom=(f'<div id="ef" class="titulo" style="transform:matrix3d(1,0,0,0.0008,0,1,0,0,0,0,1,0,0,0,0,1);{{f}}">'
                 f'{prova}</div>'),
            textos=[prova], imagens=0, limite=4096),
        "text-shadow": dict(
            rotulo="proibido: text-shadow", proibido=True,
            base=f'<div id="ef" class="titulo" style="{{f}}">{prova}</div>',
            bom=f'<div id="ef" class="titulo" style="text-shadow:0 6px 18px rgb(0 0 0 / .7);{{f}}">{prova}</div>',
            textos=[prova], imagens=0, limite=4096),
        "stroke-em-text": dict(
            rotulo="proibido: stroke em text", proibido=True,
            base=(f'<svg id="ef" width="760" height="300" style="position:absolute;left:0;top:120px;{{f}}">'
                  f'<text x="40" y="170" font-family="Anton" font-size="120" fill="#F26B1D">{prova}</text></svg>'),
            bom=(f'<svg id="ef" width="760" height="300" style="position:absolute;left:0;top:120px;{{f}}">'
                 f'<text x="40" y="170" font-family="Anton" font-size="120" fill="none" stroke="#F26B1D" '
                 f'stroke-width="2">{prova}</text></svg>'),
            textos=[prova], imagens=0, limite=4096),
        "background-clip-text": dict(
            rotulo="proibido: background-clip text", proibido=True,
            base=f'<div id="ef" class="titulo" style="{{f}}">{prova}</div>',
            bom=(f'<div id="ef" class="titulo" style="background:linear-gradient(90deg,#F26B1D,#FFC861);'
                 f'-webkit-background-clip:text;background-clip:text;color:transparent;{{f}}">{prova}</div>'),
            textos=[prova], imagens=0, limite=4096),
        "mask-image-gradiente": dict(
            rotulo="proibido: mask-image com gradiente", proibido=True,
            base=f'<div id="ef" class="titulo" style="{{f}}">{prova}</div>',
            bom=(f'<div id="ef" class="titulo" style="-webkit-mask-image:linear-gradient(90deg,#000,transparent);'
                 f'mask-image:linear-gradient(90deg,#000,transparent);{{f}}">{prova}</div>'),
            textos=[prova], imagens=0, limite=4096),
        "filter": dict(
            rotulo="proibido: filter", proibido=True,
            base=f'<div id="ef" class="titulo" style="{{f}}">{prova}</div>',
            bom=f'<div id="ef" class="titulo" style="filter:grayscale(1);{{f}}">{prova}</div>',
            textos=[prova], imagens=0, limite=4096),
    }
    return c


def html(corpo, rotulo, extra=""):
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{css_base()}</style></head><body>'
            f'<section class="pagina"><div class="rotulo">{rotulo}</div>{corpo.replace("{f}", extra)}</section></body></html>')


# ------------------------------------------------------------------------------------------------- render e checagens
def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def renderizar(pagina, doc, destino):
    """PDF e PNG do HTML pelo Chromium; devolve a caixa do #ef (região do efeito) em px."""
    p_html = destino.with_suffix(".html")
    p_html.write_text(doc, encoding="utf-8")
    pagina.goto(p_html.resolve().as_uri())
    pagina.wait_for_load_state("networkidle")
    pagina.evaluate("document.fonts.ready")
    caixa = pagina.evaluate("(() => { const e = document.querySelector('#ef'); if (!e) return null; const r = e.getBoundingClientRect(); "
                            "return [r.left, r.top, r.right, r.bottom]; })()")
    pagina.screenshot(path=str(destino.with_suffix(".png")), clip={"x": 0, "y": 0, "width": W, "height": H})
    pagina.pdf(path=str(destino.with_suffix(".pdf")), width=f"{W}px", height=f"{H}px", print_background=True,
               prefer_css_page_size=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
    return caixa


def imagens(pdf):
    """Objetos de imagem distintos (image, smask...) do PDF, pelo object ID do pdfimages -list, cada um identificado pelo
    CONTEÚDO: tipo, tamanho e sha256 dos pixels extraídos (pdfimages -png). Lista ordenada (multiconjunto)."""
    import hashlib
    linhas = [l.split() for l in _run(["pdfimages", "-list", str(pdf)]).splitlines()[2:]]
    linhas = [p for p in linhas if len(p) >= 12]
    if not linhas:
        return []
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdfimages", "-png", str(pdf), str(Path(tmp) / "i")], check=True, capture_output=True)
        arqs = sorted(Path(tmp).glob("i-*.png"))
        vistos, out = set(), []
        for p, arq in zip(linhas, arqs):
            obj = (p[10], p[11])
            if obj in vistos:
                continue
            vistos.add(obj)
            im = Image.open(arq)
            out.append((p[2], im.size, hashlib.sha256(im.tobytes()).hexdigest()[:16]))
    return sorted(out)


def type3(pdf):
    return [l for l in _run(["pdffonts", str(pdf)]).splitlines()[2:] if "Type 3" in l]


def texto(pdf):
    return " ".join(_run(["pdftotext", "-f", "1", "-l", "1", str(pdf), "-"]).split())


def raster(pdf, png, regiao, pasta):
    """Diferença média por canal entre o PDF rasterizado (pdftoppm, 96 ppi: 1 px CSS = 1 px) e o PNG do Chromium."""
    base = pasta / (pdf.stem + "-pdf")
    subprocess.run(["pdftoppm", "-r", "96", "-png", "-singlefile", str(pdf), str(base)], check=True, capture_output=True)
    a = np.asarray(Image.open(str(base) + ".png").convert("RGB"), dtype=float)
    b = np.asarray(Image.open(png).convert("RGB"), dtype=float)
    h, w = min(a.shape[0], b.shape[0]), min(a.shape[1], b.shape[1])
    x0, y0, x1, y1 = (max(0, int(regiao[0]) - 4), max(0, int(regiao[1]) - 4), min(w, int(regiao[2]) + 4), min(h, int(regiao[3]) + 4))
    if x1 <= x0 or y1 <= y0:
        x0, y0, x1, y1 = 0, 0, w, h
    return float(np.abs(a[y0:y1, x0:x1] - b[y0:y1, x0:x1]).mean())


def checar(pdf, png, regiao, caso, base, pasta):
    """As cinco checagens de um PDF ({nome: (passou, detalhe)}) contra a base do mesmo caso."""
    out = {}
    t3 = type3(pdf)
    out["fontes"] = (not t3, "Type 3: " + "; ".join(" ".join(l.split()[:2]) for l in t3) if t3 else "sem Type 3")
    objs = imagens(pdf)
    # mask-image com PNG (imagens None): o PNG entra como imagem e máscara, a base não tem; vale o que o bom mede
    esperado = base["imagens_bom"] if caso.get("imagens") is None else base["imagens"]
    iguais = objs == esperado
    out["imagens"] = (iguais, f"{len(objs)} objeto(s) de imagem, esperado {len(esperado)}; "
                              f"{'mesmo conteúdo' if iguais else 'conteúdo diferente (raster novo ou imagem refeita)'}")
    tx = texto(pdf)
    falta = [t for t in [caso["rotulo"]] + list(caso.get("textos") or []) if " ".join(t.split()) not in tx]
    out["texto"] = (not falta, f"falta como texto: {falta}" if falta else "texto inteiro")
    dif = raster(pdf, png, regiao, pasta)
    out["raster"] = (dif <= LIMITE_RASTER, f"diferença média {dif:.2f} por canal na região (limite {LIMITE_RASTER})")
    nb = pdf.stat().st_size - base["bytes"]
    out["bytes"] = (nb <= caso["limite"], f"{nb:+d} bytes sobre a base (limite {caso['limite']})")
    return out


def provar(nomes=None, saida=None, log=print):
    """Roda os casos e devolve {nome: {proibido, bom: {...}, mutante: {...}}}; cada checagem é (passou, detalhe)."""
    from playwright.sync_api import sync_playwright
    cs = casos()
    if nomes:
        desconhecidos = [n for n in nomes if n not in cs]
        if desconhecidos:
            raise SystemExit(f"caso desconhecido: {desconhecidos} (há: {', '.join(cs)})")
        cs = {n: cs[n] for n in nomes}
    pasta = Path(saida) if saida else Path(tempfile.mkdtemp(prefix="mk-prova-pdf-"))
    if pasta.exists() and saida:
        shutil.rmtree(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    res = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        pg.emulate_media(media="screen")
        for nome, caso in cs.items():
            t0 = time.time()
            renderizar(pg, html(caso["base"], caso["rotulo"]), pasta / f"{nome}-base")
            pdf_b = pasta / f"{nome}-base.pdf"
            base = {"bytes": pdf_b.stat().st_size, "imagens": imagens(pdf_b)}
            r = {"proibido": bool(caso.get("proibido")), "rotulo": caso["rotulo"]}
            for versao, extra in (("bom", ""), ("mutante", MUTANTE)):
                destino = pasta / f"{nome}-{versao}"
                caixa = renderizar(pg, html(caso["bom"], caso["rotulo"], extra), destino)
                regiao = caso.get("regiao") or caixa or (0, 0, W, H)
                if versao == "bom":
                    base["imagens_bom"] = imagens(destino.with_suffix(".pdf"))
                r[versao] = checar(destino.with_suffix(".pdf"), destino.with_suffix(".png"), regiao, caso, base, pasta)
            res[nome] = r
            log(f"{nome}: {time.time() - t0:.1f} s")
        b.close()
    res["_pasta"] = str(pasta)
    return res


def veredito(res):
    """[(nome, ok, linha)] por caso: lista branca = bom passa nas 5 e o mutante falha em alguma; proibido = o bom (o efeito
    proibido) falha em alguma."""
    out = []
    for nome, r in res.items():
        if nome.startswith("_"):
            continue
        falhas_bom = [c for c in CHECAGENS if not r["bom"][c][0]]
        falhas_mut = [c for c in CHECAGENS if not r["mutante"][c][0]]
        if r["proibido"]:
            ok = bool(falhas_bom)
            linha = (f"PROIBIDO {nome}: acusado por {', '.join(falhas_bom)}" if ok else
                     f"PROIBIDO {nome}: NÃO acusado por nenhuma das 5 checagens")
        else:
            ok = not falhas_bom and bool(falhas_mut)
            linha = (f"PERMITIDO {nome}: bom 5/5; mutante com filter acusado por {', '.join(falhas_mut) or 'NADA'}"
                     if not falhas_bom else f"PERMITIDO {nome}: bom FALHOU em {', '.join(falhas_bom)}")
        out.append((nome, ok, linha))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nomes", nargs="*")
    ap.add_argument("--saida", default=None, help="pasta dos PDF, PNG e HTML de cada caso (padrão: temporária)")
    ap.add_argument("--json", default=None, help="grava o resultado completo em JSON")
    a = ap.parse_args()
    res = provar(a.nomes or None, a.saida)
    ruins = 0
    for nome, ok, linha in veredito(res):
        print(("OK    " if ok else "FALHA ") + linha)
        r = res[nome]
        for versao in ("bom", "mutante"):
            for c in CHECAGENS:
                passou, det = r[versao][c]
                print(f"        {versao:8s} {c:8s} {'ok ' if passou else 'NÃO'}  {det}")
        ruins += not ok
    print(f"\nPDFs em {res['_pasta']}")
    if a.json:
        Path(a.json).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(veredito(res)) - ruins} de {len(veredito(res))} casos como o esperado")
    sys.exit(1 if ruins else 0)


if __name__ == "__main__":
    main()

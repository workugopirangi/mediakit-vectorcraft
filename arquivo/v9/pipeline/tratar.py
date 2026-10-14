#!/usr/bin/env python3
"""
tratar.py: efeitos raster feitos ANTES do HTML (pesquisa, rodada 2: filtros CSS/SVG rasterizam no PDF do Chromium
e perdem texto; o HTML fica só com tipo, forma, clip e blend nativos).

Comandos:
  grao     <saida.png> [--tamanho 512] [--forca .18]              grão em PNG (tile), embutido pelo render.py; nunca feTurbulence no CSS
  preparar <entrada> <saida.jpg> [--largura 2880] [--q 85]          redimensiona para 1,5× o uso (1920 → 2880) e grava JPEG q85 (sem teto de peso por ordem do Ugo (12/10/2026))
  tingir   <entrada> <saida.jpg> --cor #E8307A [--forca .7] [--preto .04]   duotone por LUT (preto→cor da marca escura, luz→cor clara), sem filtro CSS
  igualar  <entrada> <saida.jpg> --referencia <cena-ref.jpg> [--forca .4]   transfere a média a*b* (Lab) da referência: cenas de origens diferentes com a mesma luz
  sombra   <objeto.png> <sombra.png> [--luz esquerda|direita|cima] [--blur 18] [--opacidade .42] [--achatar 7]   sombra de contato + oclusão a partir do alfa
  recortar-borda <objeto.png> <saida.png> [--erosao 1] [--feather .8]        erosão de 1 px + feather na máscara (tira halo do recorte)
  reflexo  <objeto.png> <saida.png> [--altura .35] [--opacidade .32] [--achatar .9]   reflexo de piso: espelho achatado com a rampa
           de opacidade gravada no alfa (topo do reflexo = base da tinta do objeto; só sobre fundo liso)
  alfa-degraus <png> <saida.png> --direcao dir|esq|cima|baixo --passos 3..8 --minimo 0..0.46   esmaecer gravado no alfa em
           exatamente N degraus (nunca rampa contínua: mask-image com gradiente rasteriza o PDF)
  textura  <entrada> <saida.jpg> [--largura 1920] [--q 80]          textura única: 1x do uso, JPEG sem alfa, nunca ladrilhada

Todas as saídas vão para acervo/tratado/ por convenção; o mediakit.json aponta para o arquivo tratado.
"""
import argparse, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageOps


def hex_rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def grao(saida, tamanho=512, forca=0.18):
    rng = np.random.default_rng(7)
    n = rng.normal(0.5, 0.18, (tamanho, tamanho)); n = np.clip(n, 0, 1)
    # dois níveis de granulação (fino + médio) para não parecer ruído digital
    im = Image.fromarray((n * 255).astype("uint8"), "L")
    med = im.resize((tamanho // 3, tamanho // 3), Image.BILINEAR).resize((tamanho, tamanho), Image.BILINEAR)
    mix = np.asarray(im, dtype=float) * 0.7 + np.asarray(med, dtype=float) * 0.3
    # luminância varia (soft-light com cinza 50% é identidade; o grão precisa estar no RGB, não no alfa)
    lum = np.clip((mix - 128) * forca * 3 + 128, 0, 255).astype("uint8")
    g = Image.fromarray(lum)
    out = Image.merge("RGBA", (g, g, g, Image.new("L", (tamanho, tamanho), 255)))
    out.save(saida, optimize=True); print("OK", saida)


def preparar(entrada, saida, largura=2880, q=85):
    im = Image.open(entrada); im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA") and Path(saida).suffix.lower() in (".jpg", ".jpeg"):
        im = im.convert("RGB")
    if im.width > largura:
        im = im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)
    if Path(saida).suffix.lower() in (".jpg", ".jpeg"):
        im.convert("RGB").save(saida, quality=q, optimize=True, progressive=True)
    else:
        im.save(saida, optimize=True)
    print("OK", saida, im.size, f"{Path(saida).stat().st_size/1024:.0f} KB")


def tingir(entrada, saida, cor, forca=0.7, preto=0.04):
    im = Image.open(entrada).convert("RGB"); L = np.asarray(ImageOps.grayscale(im), dtype=float) / 255.0
    r, g, b = hex_rgb(cor)
    escura = np.array([r * 0.18, g * 0.12, b * 0.16]); clara = np.array([min(255, r * 0.55 + 115), min(255, g * 0.55 + 115), min(255, b * 0.55 + 115)])
    L = np.clip((L - preto) / (1 - preto), 0, 1)[..., None]
    duo = escura * (1 - L) + clara * L
    orig = np.asarray(im, dtype=float)
    out = orig * (1 - forca) + duo * forca
    Image.fromarray(np.clip(out, 0, 255).astype("uint8")).save(saida, quality=90); print("OK", saida)


def _lab(im):
    return np.asarray(im.convert("LAB"), dtype=float)


def igualar(entrada, saida, referencia, forca=0.4):
    orig = Image.open(entrada)
    alfa = orig.split()[3] if orig.mode in ("RGBA", "LA") else None  # recorte: a transparência tem de sobreviver
    im = orig.convert("RGB"); ref = Image.open(referencia).convert("RGB")
    a, b = _lab(im), _lab(ref)
    so = np.asarray(alfa) > 128 if alfa is not None else np.ones(a.shape[:2], bool)  # mede só o objeto, não o fundo vazio
    out = a.copy()
    for c in (1, 2):  # a* e b*: temperatura e tom, sem mexer na luminância
        out[..., c] = a[..., c] + (b[..., c].mean() - a[..., c][so].mean()) * forca
    # contraste de luminância: aproxima o desvio-padrão
    sa, sb = a[..., 0][so].std() or 1, b[..., 0].std() or 1
    ma = a[..., 0][so].mean()
    out[..., 0] = (a[..., 0] - ma) * (1 + (sb / sa - 1) * forca * 0.5) + ma
    res = Image.fromarray(np.clip(out, 0, 255).astype("uint8"), "LAB").convert("RGB")
    if alfa is not None:
        res.putalpha(alfa); res.save(saida)
    else:
        res.save(saida, quality=90)
    print("OK", saida)


def sombra(objeto, saida, luz="esquerda", blur=18, opacidade=0.42, achatar=7):
    """Sombra de contato (elipse achatada no pé do objeto) + oclusão (mancha escura colada ao contato), a partir do alfa."""
    ob = Image.open(objeto).convert("RGBA"); a = np.asarray(ob.split()[3], dtype=float) / 255.0
    W, H = ob.size
    ys, xs = np.nonzero(a > 0.5)
    if len(xs) == 0:
        raise SystemExit("objeto sem alfa")
    x0, x1, y1 = xs.min(), xs.max(), ys.max()
    largura = x1 - x0; altura_s = max(8, largura // achatar)
    canvas = Image.new("L", (W, H + altura_s * 2), 0)
    # contato: elipse no pé, deslocada contra a luz
    desloc = {"esquerda": largura * 0.12, "direita": -largura * 0.12, "cima": 0}.get(luz, 0)
    from PIL import ImageDraw
    d = ImageDraw.Draw(canvas)
    d.ellipse([x0 + desloc, y1 - altura_s // 2, x1 + desloc, y1 + altura_s // 2], fill=int(255 * opacidade))
    contato = canvas.filter(ImageFilter.GaussianBlur(blur))
    # oclusão: faixa curta e escura colada ao contato
    oc = Image.new("L", canvas.size, 0); d2 = ImageDraw.Draw(oc)
    d2.ellipse([x0 + largura * 0.15, y1 - altura_s // 4, x1 - largura * 0.15, y1 + altura_s // 4], fill=int(255 * min(1, opacidade * 1.6)))
    oc = oc.filter(ImageFilter.GaussianBlur(max(3, blur // 3)))
    mask = Image.fromarray(np.clip(np.asarray(contato, dtype=float) + np.asarray(oc, dtype=float), 0, 255).astype("uint8"))
    out = Image.merge("RGBA", (Image.new("L", canvas.size, 8),) * 3 + (mask,))
    out.save(saida); print("OK", saida, "(posicione na mesma âncora do objeto; a sombra tem", altura_s * 2, "px a mais de altura)")


def recortar_borda(objeto, saida, erosao=1, feather=0.8):
    ob = Image.open(objeto).convert("RGBA"); a = ob.split()[3]
    for _ in range(int(erosao)):
        a = a.filter(ImageFilter.MinFilter(3))
    a = a.filter(ImageFilter.GaussianBlur(feather))
    ob.putalpha(a); ob.save(saida); print("OK", saida)


LIMIAR_TINTA = 128          # o mesmo de composicao.LIMIAR_TINTA: é a tinta (não a franja) que a âncora encosta na linha
LIMIAR_VISIVEL = 8          # o mesmo de camadas.alfa_bbox: a caixa que o render recorta do PNG
DIRECOES = ("dir", "esq", "cima", "baixo")


def _so_png(saida, o_que):
    if Path(saida).suffix.lower() != ".png":
        raise SystemExit(f"{o_que} grava no alfa: a saída tem de ser .png (JPEG não tem alfa): {saida}")


def reflexo(objeto, saida, altura=0.35, opacidade=0.32, achatar=0.9):
    """Reflexo de piso liso gravado no PNG, sem CSS (filtro e mask-image com gradiente rasterizam o PDF).

    O objeto é medido na tinta (alfa >= 128, a mesma medida que a âncora usa): da primeira à última linha com tinta.
    Esse trecho é espelhado na vertical (o pé do objeto vira a primeira linha do reflexo) e achatado para `achatar` x a
    altura da tinta (o piso visto de cima encurta o reflexo). Fica só o começo do espelho: `altura` x a altura da tinta.
    O alfa desse trecho é multiplicado por uma rampa linear, `opacidade` na primeira linha (colada ao pé) e 0 na última.
    A largura é a do PNG do objeto: as colunas do reflexo são as colunas do objeto, e o topo do reflexo encosta na base
    da tinta dele (item derivado `<id>-reflexo` com `topo=<id>.base`). Só sobre fundo liso: sobre foto, o piso da foto
    não reflete nada e o reflexo mente (o QA avisa)."""
    for nome, v in (("altura", altura), ("opacidade", opacidade), ("achatar", achatar)):
        if not 0 < v <= 1:
            raise SystemExit(f"--{nome} {v}: use um valor acima de 0 e até 1")
    _so_png(saida, "o reflexo")
    ob = Image.open(objeto).convert("RGBA")
    a = np.asarray(ob.split()[3])
    linhas = np.nonzero((a >= LIMIAR_TINTA).any(axis=1))[0]
    if not len(linhas):
        raise SystemExit(f"{objeto} sem tinta no alfa (nenhum pixel com alfa >= {LIMIAR_TINTA}): o reflexo sai de um recorte")
    y0, y1 = int(linhas.min()), int(linhas.max())
    h, W = y1 - y0 + 1, ob.width
    m = max(1, round(h * achatar))
    # RGBa (pré-multiplicado) no redimensionamento: sem ele a cor do pixel transparente vaza para a borda do objeto
    espelho = ob.crop((0, y0, W, y1 + 1)).transpose(Image.FLIP_TOP_BOTTOM).convert("RGBa").resize((W, m), Image.LANCZOS).convert("RGBA")
    n = round(h * altura)
    if n > m:
        print(f"  --altura {altura} passa do espelho achatado ({m} px): o reflexo fica com o espelho inteiro")
        n = m
    if n < 2:
        raise SystemExit(f"o reflexo teria {n} px de altura (tinta de {h} px x {altura}): objeto baixo demais para uma rampa")
    arr = np.array(espelho)[:n]
    rampa = opacidade * (1 - np.arange(n) / (n - 1))          # opacidade na primeira linha, 0 na última
    arr[..., 3] = np.round(arr[..., 3].astype(float) * rampa[:, None]).astype(np.uint8)
    Image.fromarray(arr, "RGBA").save(saida)
    print("OK", saida, f"({W} x {n} px; topo = linha {y1} do objeto, a base da tinta; colunas iguais às do objeto)")


def alfa_degraus(png, saida, direcao, passos, minimo):
    """Esmaecer gravado no alfa em exatamente `passos` níveis: degraus, nunca rampa contínua (mask-image com gradiente
    rasteriza o PDF). Mesma convenção do _Degraus do grafismos.py: a direção é para onde a imagem SOME ('dir' = opaca na
    esquerda e só `minimo` na direita), o primeiro degrau é opaco, o último vale `minimo`, os do meio são lineares entre os
    dois e as faixas têm a mesma largura. As faixas cobrem a área visível (alfa > 8, a caixa que o render recorta do PNG),
    não a margem transparente: senão o primeiro e o último degrau cairiam no vazio. O alfa que já existe é multiplicado."""
    if direcao not in DIRECOES:
        raise SystemExit(f"--direcao {direcao}: use {', '.join(DIRECOES)}")
    if not 3 <= passos <= 8:
        raise SystemExit(f"--passos {passos}: use de 3 a 8")
    if not 0 <= minimo <= 0.46:
        raise SystemExit(f"--minimo {minimo}: use de 0 a 0.46 (o último degrau; acima disso o esmaecer não se lê)")
    _so_png(saida, "o esmaecer em degraus")
    arr = np.array(ImageOps.exif_transpose(Image.open(png)).convert("RGBA"))
    a = arr[..., 3].astype(float)
    ys, xs = np.nonzero(a > LIMIAR_VISIVEL)
    if not len(xs):
        raise SystemExit(f"{png} está todo transparente: não há o que esmaecer")
    niveis = np.array([1 - (1 - minimo) * j / (passos - 1) for j in range(passos)])
    if direcao in ("dir", "esq"):
        u = (np.arange(arr.shape[1]) + 0.5 - xs.min()) / (xs.max() + 1 - xs.min())
    else:
        u = (np.arange(arr.shape[0]) + 0.5 - ys.min()) / (ys.max() + 1 - ys.min())
    if direcao in ("esq", "cima"):
        u = 1 - u
    fator = niveis[np.clip(np.floor(u * passos), 0, passos - 1).astype(int)]
    fator = fator[None, :] if direcao in ("dir", "esq") else fator[:, None]
    arr[..., 3] = np.round(a * fator).astype(np.uint8)
    Image.fromarray(arr, "RGBA").save(saida)
    print("OK", saida, f"{passos} degraus para {direcao}:", " ".join(f"{v:.2f}" for v in niveis))


def textura(entrada, saida, largura=1920, q=80):
    """Textura única (rota "textura única" do acabamento): uma imagem por área, a 1x do uso (1920 px = a largura da página),
    JPEG q80 sem alfa.

    NUNCA ladrilhada (aprendizado 31): o gerador não entrega costura. 2 de 2 patterns pedidos como tile seamless saíram com
    costura visível (índice 0,93 e 0,90 no padrao.py checar), então a textura repetida mostraria a emenda a cada repetição.
    Por isso este comando só redimensiona e grava: não corta em tile, não repete, não espelha. O que precisa repetir é pattern,
    outra rota (padrao.py checar e tornar-seamless, e só ladrilha com índice <= .5). A 1x e não a 1,5x do `preparar`: textura
    não tem detalhe que se leia de perto, e o peso extra não compra nada. Menor que a largura, fica como está (ampliar não
    cria detalhe). Textura com alfa real (só a tinta opaca) não passa por aqui: achatar o alfa apagaria o que a deixa
    sobrepor a página; ela vai pelo `preparar` com saída .png."""
    if Path(saida).suffix.lower() not in (".jpg", ".jpeg"):
        raise SystemExit(f"textura única sai em JPEG, sem alfa (.jpg): {saida}")
    im = ImageOps.exif_transpose(Image.open(entrada))
    if im.mode in ("RGBA", "LA", "PA") or "transparency" in im.info:
        a = np.asarray(im.convert("RGBA"))[..., 3]
        if (a < 255).any():
            raise SystemExit(f"{entrada} tem alfa real ({(a < 255).mean():.0%} dos pixels não são opacos): textura única é sem "
                             "alfa. Para manter a transparência: tratar.py preparar <entrada> <saida.png>")
    im = im.convert("RGB")
    if im.width > largura:
        im = im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)
    elif im.width < largura:
        print(f"  aviso: {im.width} px de largura, abaixo de {largura}: fica como está (ampliar não cria detalhe)")
    im.save(saida, "JPEG", quality=q, optimize=True, progressive=True)
    print("OK", saida, im.size, f"{Path(saida).stat().st_size/1024:.0f} KB (textura única: uma por área, nunca ladrilhada)")


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("grao"); g.add_argument("saida"); g.add_argument("--tamanho", type=int, default=512); g.add_argument("--forca", type=float, default=0.18)
    p = sub.add_parser("preparar"); p.add_argument("entrada"); p.add_argument("saida"); p.add_argument("--largura", type=int, default=2880); p.add_argument("--q", type=int, default=85)
    t = sub.add_parser("tingir"); t.add_argument("entrada"); t.add_argument("saida"); t.add_argument("--cor", required=True); t.add_argument("--forca", type=float, default=0.7); t.add_argument("--preto", type=float, default=0.04)
    i = sub.add_parser("igualar"); i.add_argument("entrada"); i.add_argument("saida"); i.add_argument("--referencia", required=True); i.add_argument("--forca", type=float, default=0.4)
    s = sub.add_parser("sombra"); s.add_argument("objeto"); s.add_argument("saida"); s.add_argument("--luz", default="esquerda"); s.add_argument("--blur", type=int, default=18); s.add_argument("--opacidade", type=float, default=0.42); s.add_argument("--achatar", type=int, default=7)
    r = sub.add_parser("recortar-borda"); r.add_argument("objeto"); r.add_argument("saida"); r.add_argument("--erosao", type=int, default=1); r.add_argument("--feather", type=float, default=0.8)
    f = sub.add_parser("reflexo"); f.add_argument("objeto"); f.add_argument("saida"); f.add_argument("--altura", type=float, default=0.35); f.add_argument("--opacidade", type=float, default=0.32); f.add_argument("--achatar", type=float, default=0.9)
    d = sub.add_parser("alfa-degraus"); d.add_argument("png"); d.add_argument("saida"); d.add_argument("--direcao", required=True, choices=DIRECOES); d.add_argument("--passos", type=int, required=True); d.add_argument("--minimo", type=float, required=True)
    x = sub.add_parser("textura"); x.add_argument("entrada"); x.add_argument("saida"); x.add_argument("--largura", type=int, default=1920); x.add_argument("--q", type=int, default=80)
    a = ap.parse_args()
    if a.cmd == "grao": grao(a.saida, a.tamanho, a.forca)
    elif a.cmd == "preparar": preparar(a.entrada, a.saida, a.largura, a.q)
    elif a.cmd == "tingir": tingir(a.entrada, a.saida, a.cor, a.forca, a.preto)
    elif a.cmd == "igualar": igualar(a.entrada, a.saida, a.referencia, a.forca)
    elif a.cmd == "sombra": sombra(a.objeto, a.saida, a.luz, a.blur, a.opacidade, a.achatar)
    elif a.cmd == "recortar-borda": recortar_borda(a.objeto, a.saida, a.erosao, a.feather)
    elif a.cmd == "reflexo": reflexo(a.objeto, a.saida, a.altura, a.opacidade, a.achatar)
    elif a.cmd == "alfa-degraus": alfa_degraus(a.png, a.saida, a.direcao, a.passos, a.minimo)
    elif a.cmd == "textura": textura(a.entrada, a.saida, a.largura, a.q)


if __name__ == "__main__":
    main()

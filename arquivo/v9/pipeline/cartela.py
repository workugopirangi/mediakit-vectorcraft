#!/usr/bin/env python3
"""cartela.py: folhas visuais para o Ugo escolher fonte.

  cartela.py familias --humor esporte --texto "SPRINT UBATUBA RUN" --saida fontes-livres/cartelas/familias-esporte.png
  cartela.py pares --texto-display "SÃO JOSÉ DA PRAÇA" --texto-corpo "Largada às 6h..." --saida fontes-livres/cartelas/pares.png [--humor luxo]

familias: uma linha por família, no peso de display (800 se existir, senão o mais pesado até 700, senão 400),
com nome, origem e pesos em letra pequena. pares: um card por par de catalogos/pares.json.
Renderiza com Pillow direto nos arquivos de fontes-livres/, os mesmos que o render usa.
"""
import argparse, json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
LARGURA = 2400
FUNDO, TINTA, SUAVE, LINHA = (246, 244, 239), (17, 17, 17), (110, 108, 102), (214, 210, 200)
TEXTO_PADRAO = "SÃO JOSÉ DA PRAÇA, AÇAÍ 14 KM"
CORPO_PADRAO = ("Largada às 6h30 na praça central, com hidratação a cada 3 km, chip de cronometragem e medalha para todas "
                "as pessoas que cruzarem a linha de chegada. Inscrições até sexta-feira.")


def carregar():
    return {f["familia"]: f for f in json.loads((RAIZ / "catalogos/fontes.json").read_text(encoding="utf-8"))["familias"]}


def arquivo(f, peso):
    d = RAIZ / f["pasta"]
    return d / (f"{f['familia']}.ttf" if peso == 400 else f"{f['familia']}__{peso}.ttf")


def peso_display(f):
    pesos = f["pesos"]
    if 800 in pesos: return 800
    if 700 in pesos: return 700
    return max(pesos)


def fonte(f, peso, tam):
    return ImageFont.truetype(str(arquivo(f, peso)), tam)


def interface(tam, negrito=False):
    return ImageFont.truetype(str(RAIZ / "fontes-livres/Inter" / ("Inter__700.ttf" if negrito else "Inter.ttf")), tam)


def ajustar(f, peso, texto, largura, maximo):
    """maior tamanho (<= maximo) em que o texto cabe em uma linha na largura dada"""
    tam = maximo
    while tam > 20:
        ft = fonte(f, peso, tam)
        if ft.getlength(texto) <= largura:
            return ft
        tam -= 4
    return fonte(f, peso, 20)


def quebrar(ft, texto, largura):
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if ft.getlength(teste) <= largura:
            atual = teste
        else:
            linhas.append(atual); atual = palavra
    if atual: linhas.append(atual)
    return linhas


def familias(a):
    cat = carregar()
    lista = [f for f in cat.values() if (not a.humor or a.humor in f["humor"]) and "display" in f["papel"]]
    if not lista:
        sys.exit(f"nenhuma família de display com humor '{a.humor}'")
    lista.sort(key=lambda f: (["condensada", "normal", "larga"].index(f["largura"]), f["familia"].lower()))
    margem, col_nome, alt = 80, 560, 230
    img = Image.new("RGB", (LARGURA, 190 + alt * len(lista) + 60), FUNDO)
    d = ImageDraw.Draw(img)
    d.text((margem, 60), f"Cartela de fontes" + (f": humor {a.humor}" if a.humor else ""), font=interface(52, True), fill=TINTA)
    d.text((margem, 126), f"{len(lista)} famílias, peso de display. Diga o nome da que gostou.", font=interface(28), fill=SUAVE)
    y = 190
    for f in lista:
        p = peso_display(f)
        d.line([(margem, y), (LARGURA - margem, y)], fill=LINHA, width=2)
        d.text((margem, y + 50), f["familia"], font=interface(34, True), fill=TINTA)
        d.text((margem, y + 100), f"{f['origem']}, {f['largura']}", font=interface(24), fill=SUAVE)
        d.text((margem, y + 136), "pesos " + " ".join(str(x) for x in f["pesos"]), font=interface(22), fill=SUAVE)
        ft = ajustar(f, p, a.texto, LARGURA - 2 * margem - col_nome, 150)
        bb = ft.getbbox(a.texto)
        d.text((margem + col_nome, y + (alt - (bb[3] - bb[1])) // 2 - bb[1]), a.texto, font=ft, fill=TINTA)
        y += alt
    d.line([(margem, y), (LARGURA - margem, y)], fill=LINHA, width=2)
    salvar(img, a.saida)


def pares(a):
    cat = carregar()
    todos = json.loads((RAIZ / "catalogos/pares.json").read_text(encoding="utf-8"))["pares"]
    lista = [p for p in todos if not a.humor or a.humor in p["humor"]]
    margem, gut, cols = 80, 60, 2
    larg = (LARGURA - 2 * margem - gut) // cols
    alt = 640
    linhas = (len(lista) + cols - 1) // cols
    img = Image.new("RGB", (LARGURA, 190 + linhas * (alt + gut) + 40), FUNDO)
    d = ImageDraw.Draw(img)
    d.text((margem, 60), "Pares de fontes" + (f": humor {a.humor}" if a.humor else ""), font=interface(52, True), fill=TINTA)
    d.text((margem, 126), f"{len(lista)} pares. Diga o número do par (p01, p02...).", font=interface(28), fill=SUAVE)
    for i, p in enumerate(lista):
        x0 = margem + (i % cols) * (larg + gut)
        y0 = 190 + (i // cols) * (alt + gut)
        d.rounded_rectangle([x0, y0, x0 + larg, y0 + alt], radius=18, fill=(255, 255, 255), outline=LINHA, width=2)
        pad = 44
        d.text((x0 + pad, y0 + 30), p["id"], font=interface(30, True), fill=TINTA)
        rotulo = f"{p['display']} {p['peso_display']} + {p['corpo']}"
        d.text((x0 + pad + 100, y0 + 33), rotulo, font=interface(26), fill=SUAVE)
        fd = cat[p["display"]]
        ft = ajustar(fd, p["peso_display"], a.texto_display, larg - 2 * pad, 120)
        bb = ft.getbbox(a.texto_display)
        d.text((x0 + pad, y0 + 100 - bb[1]), a.texto_display, font=ft, fill=TINTA)
        tf = cat[p["titulo"]] if p.get("titulo") else None
        y = y0 + 100 + (bb[3] - bb[1]) + 40
        if tf:
            ts = fonte(tf, 700 if 700 in tf["pesos"] else peso_display(tf), 40)
            d.text((x0 + pad, y), "Saída 06h30, praça central", font=ts, fill=TINTA); y += 70
        fc = cat[p["corpo"]]
        fb = fonte(fc, 400, 32)
        for linha in quebrar(fb, a.texto_corpo, larg - 2 * pad)[:6]:
            d.text((x0 + pad, y), linha, font=fb, fill=(40, 40, 40)); y += 48
        humor = ", ".join(p["humor"])
        d.text((x0 + pad, y0 + alt - 60), humor, font=interface(22), fill=SUAVE)
    salvar(img, a.saida)


def salvar(img, saida):
    saida = Path(saida); saida.parent.mkdir(parents=True, exist_ok=True)
    img.save(saida, optimize=True)
    print(f"OK  {saida}  {img.width}x{img.height}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("familias"); f.add_argument("--humor"); f.add_argument("--texto", default=TEXTO_PADRAO); f.add_argument("--saida", required=True)
    p = sub.add_parser("pares"); p.add_argument("--humor"); p.add_argument("--texto-display", default=TEXTO_PADRAO)
    p.add_argument("--texto-corpo", default=CORPO_PADRAO); p.add_argument("--saida", required=True)
    a = ap.parse_args()
    familias(a) if a.cmd == "familias" else pares(a)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
exportar_pptx.py — slides EDITÁVEIS a partir do mesmo render (fluxo híbrido, references/04-geracao-por-codigo.md).

Uso: python3 exportar_pptx.py <pasta-do-cliente> [--direcao causa]

Pré-requisito: render.py rodado com --png --fundo (gera saida/fundo/kit-<d>-NN.png, a página sem texto, e as caixas de
texto medidas no render-report.json). Cada slide recebe a imagem de fundo (cena, véus, formas, grão) e, por cima,
caixas de texto nativas do PowerPoint nas mesmas posições, com fonte, tamanho, peso e cor. O cliente edita o texto;
o visual fica protegido. Não é um PPTX "nativo" em formas: é o compromisso que mantém a estética do PDF.
Limites: fontes precisam estar instaladas na máquina de quem abre; números de peito/placeholders dentro das cenas não são editáveis.
"""
import argparse, json
from pathlib import Path
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

W_IN, H_IN = 13.333, 7.5
PX = 914400 * W_IN / 1920  # EMU por px
FONTES = {"display": "RocGrotesk Wide", "titulo": "RocGrotesk", "corpo": "Montserrat"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("pasta"); ap.add_argument("--direcao", default=None); a = ap.parse_args()
    pasta = Path(a.pasta).resolve(); saida = pasta / "saida"
    rep = json.loads((saida / "render-report.json").read_text(encoding="utf-8"))
    d = a.direcao or list(rep["direcoes"].keys())[0]
    m = rep["direcoes"][d]["horizontal"]
    k = json.loads((pasta / "mediakit.json").read_text(encoding="utf-8"))
    fd = k["marca"].get("fonte_display") or FONTES["display"]; fc = k["marca"].get("fonte_corpo") or FONTES["corpo"]
    prs = Presentation(); prs.slide_width = Emu(int(914400 * W_IN)); prs.slide_height = Emu(int(914400 * H_IN))
    blank = prs.slide_layouts[6]
    for p in m["por_pagina"]:
        n = p["pagina"]; fundo = saida / "fundo" / f"kit-{d}-{n:02d}.png"
        s = prs.slides.add_slide(blank)
        if fundo.exists():
            s.shapes.add_picture(str(fundo), 0, 0, width=prs.slide_width, height=prs.slide_height)
        vistos = set()
        for t in p["textos"]:
            if not t.get("texto", "").strip(): continue
            chave = (t["texto"], round(t["x"] / 8), round(t["y"] / 8))
            if chave in vistos: continue
            vistos.add(chave)
            uma_linha = "\n" not in t["texto"] and t["h"] < t["fs"] * 1.7
            tb = s.shapes.add_textbox(Emu(int(t["x"] * PX)), Emu(int(t["y"] * PX)), Emu(int(max(t["w"], 20) * 1.14 * PX)), Emu(int(max(t["h"], 10) * PX)))
            tf = tb.text_frame; tf.word_wrap = not uma_linha; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            para = tf.paragraphs[0]; run = para.add_run(); run.text = t["texto"]
            run.font.size = Pt(t["fs"] * 0.5)  # 1920 px → 13,333 in: 1 px = 0,5 pt
            run.font.bold = (t.get("peso", 400) >= 700)
            cls = t.get("cls", "")
            run.font.name = fd if ("display" in cls or "fantasma" in cls or "numero" in cls or "preco" in cls or "nome" in cls) else fc
            try:
                hexc = t["cor"].lstrip("#"); run.font.color.rgb = RGBColor(int(hexc[0:2], 16), int(hexc[2:4], 16), int(hexc[4:6], 16))
            except Exception: pass
            para.alignment = PP_ALIGN.LEFT
    out = saida / f"kit-{d}-editavel.pptx"; prs.save(out); print("OK", out, len(m["por_pagina"]), "slides")


if __name__ == "__main__":
    main()

"""Tratamento raster das fotos ANTES de entrarem no vetor, com a régua de resolução da página exportada."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageOps

from mediakit import config

AVISOS = []


def ppi_na_pagina(px_largura, unidades_largura):
    polegadas = unidades_largura * config.ESCALA_PDF / 72
    return px_largura / polegadas


def preparar_foto(origem, destino, w, h, modo="bw", foco=(0.5, 0.5), rastro=0, escuro=1.0):
    """Recorta no formato da caixa w × h (unidades da página) pelo foco, nunca amplia, e avisa abaixo de 96 ppi.
    modo: "bw" (preto e branco com contraste automático), "warm" (contraste +8 %) ou "none".
    rastro: largura em px do rastro de movimento (nítido à esquerda, rastro à direita); 0 desliga."""
    im = Image.open(origem).convert("RGB")
    ar = w / h
    iw, ih = im.size
    cw, ch = (ih * ar, ih) if iw / ih > ar else (iw, iw / ar)
    cx = min(max(foco[0] * iw, cw / 2), iw - cw / 2)
    cy = min(max(foco[1] * ih, ch / 2), ih - ch / 2)
    im = im.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2)))
    sc = min(1.0, max(w, h) * 1.2 / max(im.size))
    im = im.resize((int(im.size[0] * sc), int(im.size[1] * sc)), Image.LANCZOS)
    if rastro:
        a = np.asarray(im).astype("float32")
        passos = range(-rastro, rastro + 1, 2)
        mov = sum(np.roll(a, k, axis=1) for k in passos) / len(passos)
        mascara = np.linspace(0, 1, a.shape[1])[None, :, None] ** 1.5
        im = Image.fromarray((a * (1 - mascara) + mov * mascara).astype("uint8"))
    if modo == "bw":
        im = ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1).convert("RGB")
    elif modo == "warm":
        im = ImageEnhance.Contrast(im).enhance(1.08)
    if escuro != 1.0:
        im = ImageEnhance.Brightness(im).enhance(escuro)
    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    im.save(destino, quality=86)
    ppi = ppi_na_pagina(im.size[0], w)
    aviso = None
    if ppi < config.PPI_MINIMO:
        aviso = (f"{Path(origem).name}: {ppi:.0f} ppi numa caixa de {w:.0f} × {h:.0f} (régua {config.PPI_MINIMO}). "
                 f"Use uma caixa menor, outra foto, ou aceite com o Ugo.")
        AVISOS.append(aviso)
    return {"caminho": Path(destino), "ppi": round(ppi, 1), "aviso": aviso}

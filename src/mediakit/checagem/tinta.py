"""Texto encostando em texto, medido pela tinta de cada letra (TEXT_ACCURATE_BBOXES do MuPDF), não pela caixa da fonte."""
import itertools

import fitz


def _linhas(pagina):
    d = pagina.get_text("rawdict", flags=fitz.TEXT_ACCURATE_BBOXES)
    for bloco in d["blocks"]:
        for linha in bloco.get("lines", []):
            letras = [c for s in linha["spans"] for c in s["chars"] if c["c"].strip()]
            if letras:
                yield "".join(c["c"] for c in letras), [fitz.Rect(c["bbox"]) for c in letras]


def sobreposicoes(pdf, area_minima=1.0):
    achados = []
    for n, pagina in enumerate(fitz.open(pdf), 1):
        for (ta, ra), (tb, rb) in itertools.combinations(list(_linhas(pagina)), 2):
            pares = sum(1 for a in ra for b in rb if abs(a & b) > area_minima)
            if pares:
                achados.append({"pagina": n, "a": ta, "b": tb, "pares": pares})
    return achados

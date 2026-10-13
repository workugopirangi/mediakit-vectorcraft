"""Conteúdo do PDF contra a ficha aprovada: número que não está na ficha e travessão."""
import re

import fitz

_NUM = re.compile(r"\d+(?:[./-]\d+)*%?")
_TRAVESSAO = re.compile("(?s).{0,20}[—–].{0,20}")


def numeros(texto):
    return set(_NUM.findall(texto))


def _paginas(pdf):
    for n, p in enumerate(fitz.open(pdf), 1):
        yield n, p.get_text()


def numeros_fora_da_ficha(pdf, ficha_md):
    aceitos = numeros(open(ficha_md, encoding="utf-8").read())
    fora = []
    for n, texto in _paginas(pdf):
        for num in sorted(numeros(texto) - aceitos):
            fora.append({"pagina": n, "numero": num})
    return fora


def travessoes(pdf):
    return [{"pagina": n, "trecho": m.group(0).strip()} for n, texto in _paginas(pdf) for m in _TRAVESSAO.finditer(texto)]

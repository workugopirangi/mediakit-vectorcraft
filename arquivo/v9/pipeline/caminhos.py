#!/usr/bin/env python3
"""caminhos.py: todo arquivo que o mediakit.json cita (acervo, elementos, painéis, referência de temperatura, imagem do
celular, objetos) fica DENTRO da pasta do kit. O render embute esses arquivos no PDF em base64: um caminho absoluto, um
`..` que sobe ou um link que aponta para fora vazaria um arquivo qualquer do Mac para dentro do kit entregue (achado 5 da
revisão de segurança de 09/10/2026). Nenhum kit da Motion usa caminho fora da própria pasta (conferido nos 8 kits)."""
from pathlib import Path


class ForaDoKit(ValueError):
    """Caminho do kit que não fica dentro da pasta do kit."""


def dentro_do_kit(pasta, rel):
    """Caminho absoluto de `rel` dentro de `pasta`, já resolvido (links seguidos). Recusa vazio, absoluto, `..` que sai e
    link que aponta para fora, com ForaDoKit."""
    if rel is None or not str(rel).strip():
        raise ForaDoKit("caminho vazio")
    r = Path(str(rel))
    if r.is_absolute():
        raise ForaDoKit(f"`{rel}`: caminho absoluto não vale no kit (use o caminho a partir da pasta do kit)")
    base = Path(pasta).resolve()
    alvo = (base / r).resolve()
    if alvo != base and base not in alvo.parents:
        raise ForaDoKit(f"`{rel}` sai da pasta do kit")
    return alvo

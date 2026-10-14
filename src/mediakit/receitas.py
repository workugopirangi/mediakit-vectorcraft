"""Roda as receitas do VectorCraft e diz quais quebraram e quais passaram a desenhar diferente.
Antes de rodar, guarda uma cópia da pasta de cada receita; no fim devolve a pasta exatamente como estava
(inclusive alteração ainda não gravada no git) e apaga só o que a rodada criou."""
import subprocess
import sys
from pathlib import Path

import fitz
import numpy as np

LIMITE_MUDOU = 0.01   # diferença média de pixel (0 a 1) acima disso: "desenha diferente, olhe"


def _paginas(pdf):
    d = fitz.open(pdf)
    return [np.frombuffer(p.get_pixmap(dpi=20, colorspace=fitz.csGRAY).samples, dtype=np.uint8) for p in d]


def _mudou(antes, depois):
    if antes is None or not depois.exists():
        return None
    try:
        a, b = _paginas(antes), _paginas(depois)
    except Exception:
        return True
    if len(a) != len(b) or any(x.shape != y.shape for x, y in zip(a, b)):
        return True
    return any(np.abs(x.astype(int) - y.astype(int)).mean() / 255 > LIMITE_MUDOU for x, y in zip(a, b))


def rodar(raiz, python=sys.executable, limite_s=120):
    raiz = Path(raiz)
    res = {}
    for t in sorted(raiz.glob("R*/teste.py")):
        pasta = t.parent
        copia = {p: p.read_bytes() for p in pasta.iterdir() if p.is_file()}
        prova = pasta / "teste.pdf"
        prova_antes = None
        if prova in copia:
            prova_antes = pasta / ".teste-antes.pdf"
            prova_antes.write_bytes(copia[prova])
        try:
            r = subprocess.run([python, str(t)], cwd=pasta, capture_output=True, text=True, timeout=limite_s)
            roda = r.returncode == 0
        except subprocess.TimeoutExpired:
            roda = False
        mudou = _mudou(prova_antes, prova) if roda else None
        for p in pasta.iterdir():
            if p.is_file() and p not in copia:
                p.unlink()
        for p, dados in copia.items():
            if not p.exists() or p.read_bytes() != dados:
                p.write_bytes(dados)
        res[pasta.name] = {"roda": roda, "mudou": mudou}
        print(pasta.name, "ok" if roda else "FALHOU", "(desenha diferente, olhe)" if mudou else "", flush=True)
    return res


def quebradas(base, res):
    return [k for k, ok in base.items() if ok and not res.get(k, {}).get("roda")]

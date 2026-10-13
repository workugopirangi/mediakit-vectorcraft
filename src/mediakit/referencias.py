"""Biblioteca de referências: lê o repertório do cofre e acrescenta referência nova (nunca edita a existente)."""
import json
import re
import sys
from datetime import date
from pathlib import Path

import fitz
from PIL import Image

from mediakit import config

_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_IMAGENS = (".jpg", ".jpeg", ".png", ".webp")


def _raiz(r):
    return Path(r) if r else config.COFRE_MEDIAKIT / "repertorio"


def _registro(r):
    return Path(r) if r else config.RAIZ / "biblioteca" / "referencias.json"


def _novas(registro):
    p = _registro(registro)
    return json.loads(p.read_text()) if p.exists() else []


def listar(raiz_repertorio=None, registro=None):
    novas = {n["id"] for n in _novas(registro)}
    cap = _raiz(raiz_repertorio) / "capturas"
    pastas = sorted(p for p in cap.iterdir() if p.is_dir()) if cap.exists() else []
    itens = []
    for pasta in pastas:
        n = sum(1 for f in pasta.iterdir() if f.suffix.lower() in _IMAGENS)
        itens.append({"id": pasta.name, "pasta": pasta, "imagens": n,
                      "origem": "nova" if pasta.name in novas else "repertorio"})
    return itens


def existe(id_, raiz_repertorio=None):
    return (_raiz(raiz_repertorio) / "capturas" / id_).exists()


def adicionar(id_, arquivos, origem_texto, raiz_repertorio=None, registro=None):
    if not _ID.match(id_):
        raise ValueError(f"id inválido: {id_!r} (use a-z, 0-9 e hífen)")
    if existe(id_, raiz_repertorio):
        raise ValueError(f"referência {id_} já existe; escolha outro id")
    pasta = _raiz(raiz_repertorio) / "capturas" / id_
    pasta.mkdir(parents=True)
    n = 0
    for a in map(Path, arquivos):
        if a.suffix.lower() == ".pdf":
            for pg in fitz.open(a):
                n += 1
                pg.get_pixmap(dpi=110).save(pasta / f"{n:02d}.jpg")
        else:
            n += 1
            Image.open(a).convert("RGB").save(pasta / f"{n:02d}.jpg", quality=88)
    reg = _registro(registro)
    reg.parent.mkdir(parents=True, exist_ok=True)
    lista = _novas(registro) + [{"id": id_, "origem_texto": origem_texto, "quando": date.today().isoformat(),
                                 "imagens": n}]
    reg.write_text(json.dumps(lista, ensure_ascii=False, indent=1) + "\n")
    return pasta


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "adicionar":
        print(adicionar(sys.argv[2], sys.argv[4:], sys.argv[3]))
    elif sys.argv[1:] == ["listar"]:
        for i in listar():
            print(i["id"], i["imagens"], i["origem"])
    else:
        sys.exit('uso: python3 -m mediakit.referencias adicionar <id> "<de onde veio>" <arquivo>... | listar')

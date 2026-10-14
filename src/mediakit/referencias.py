"""Biblioteca de referências: lê o repertório do cofre e acrescenta referência nova (nunca edita a existente)."""
import json
import re
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

import fitz
from PIL import Image

from mediakit import config

_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_IMAGENS = (".jpg", ".jpeg", ".png", ".webp")
_ACEITOS = _IMAGENS + (".pdf",)


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
    pastas = sorted(p for p in cap.iterdir() if p.is_dir() and not p.name.startswith(".")) if cap.exists() else []
    itens = []
    for pasta in pastas:
        n = sum(1 for f in pasta.iterdir() if f.suffix.lower() in _IMAGENS)
        itens.append({"id": pasta.name, "pasta": pasta, "imagens": n,
                      "origem": "nova" if pasta.name in novas else "repertorio"})
    return itens


def existe(id_, raiz_repertorio=None):
    return (_raiz(raiz_repertorio) / "capturas" / id_).exists()


def adicionar(id_, arquivos, origem_texto, raiz_repertorio=None, registro=None):
    """Tudo ou nada: monta a pasta ao lado, com outro nome, e só renomeia para o id no fim."""
    if not _ID.fullmatch(id_):
        raise ValueError(f"id inválido: {id_!r} (use a-z, 0-9 e hífen)")
    if existe(id_, raiz_repertorio):
        raise ValueError(f"referência {id_} já existe; escolha outro id")
    arquivos = [Path(a) for a in arquivos]
    if not arquivos:
        raise ValueError("nenhum arquivo: mande pelo menos uma imagem ou um PDF")
    fora = [a.name for a in arquivos if a.suffix.lower() not in _ACEITOS]
    if fora:
        raise ValueError(f"formato não suportado: {', '.join(fora)}. Aceito JPG, PNG, WEBP e PDF "
                         f"(print do iPhone em HEIC: exporte como JPG)")
    capturas = _raiz(raiz_repertorio) / "capturas"
    capturas.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{id_}-", dir=capturas))
    try:
        n = 0
        for a in arquivos:
            if a.suffix.lower() == ".pdf":
                for pg in fitz.open(a):
                    n += 1
                    pg.get_pixmap(dpi=110).save(tmp / f"{n:02d}.jpg")
            else:
                n += 1
                Image.open(a).convert("RGB").save(tmp / f"{n:02d}.jpg", quality=88)
        pasta = capturas / id_
        tmp.rename(pasta)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
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

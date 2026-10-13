"""Qual cena entra no kit (gerada com o logo, se aprovada no olho; senão a composta) e quanto da cota foi gasto."""
import json
import sys
from datetime import datetime
from pathlib import Path


def _ler(p, padrao):
    return json.loads(p.read_text()) if p.exists() else padrao


def escolher_cena(acervo, composta, gerada):
    acervo = Path(acervo)
    escolha = _ler(acervo / "escolha-cenas.json", {})
    if escolha.get(gerada) == "usar" and (acervo / gerada).exists():
        return acervo / gerada, "gerada"
    return acervo / composta, "composta"


def marcar(acervo, gerada, decisao):
    if decisao not in ("usar", "descartar"):
        raise ValueError("decisão é 'usar' ou 'descartar'")
    p = Path(acervo) / "escolha-cenas.json"
    escolha = _ler(p, {})
    escolha[gerada] = decisao
    p.write_text(json.dumps(escolha, ensure_ascii=False, indent=1) + "\n")


def geracoes(acervo):
    return _ler(Path(acervo) / "cota.json", [])


def registrar_geracao(acervo, id_, quando=None):
    p = Path(acervo) / "cota.json"
    lista = _ler(p, [])
    lista.append({"id": id_, "quando": quando or datetime.now().isoformat(timespec="minutes")})
    p.write_text(json.dumps(lista, ensure_ascii=False, indent=1) + "\n")
    return len(lista)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "registrar":
        print(registrar_geracao(sys.argv[2], sys.argv[3]))
    else:
        sys.exit("uso: python3 -m mediakit.cenas registrar <acervo> <id>")

"""Qual cena entra no kit (gerada com o logo, se aprovada no olho; senão a composta) e quanto da cota foi gasto."""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


def _ler(p, padrao):
    return json.loads(p.read_text()) if p.exists() else padrao


def _hash(arquivo):
    return hashlib.sha256(Path(arquivo).read_bytes()).hexdigest()


def escolher_cena(acervo, composta, gerada):
    """A gerada só entra se foi aprovada E ainda é o mesmo arquivo que o Ugo viu (hash). Cena refeita perde a aprovação."""
    acervo = Path(acervo)
    e = _ler(acervo / "escolha-cenas.json", {}).get(gerada)
    if isinstance(e, dict) and e.get("decisao") == "usar" and (acervo / gerada).exists() \
            and e.get("sha256") == _hash(acervo / gerada):
        return acervo / gerada, "gerada"
    return acervo / composta, "composta"


def marcar(acervo, gerada, decisao):
    if decisao not in ("usar", "descartar"):
        raise ValueError("decisão é 'usar' ou 'descartar'")
    acervo = Path(acervo)
    if decisao == "usar" and not (acervo / gerada).exists():
        raise FileNotFoundError(acervo / gerada)
    p = acervo / "escolha-cenas.json"
    escolha = _ler(p, {})
    escolha[gerada] = {"decisao": decisao, "sha256": _hash(acervo / gerada) if decisao == "usar" else None}
    p.write_text(json.dumps(escolha, ensure_ascii=False, indent=1) + "\n")


def geracoes(acervo):
    return _ler(Path(acervo) / "cota.json", [])


def registrar_geracao(acervo, id_, quando=None, resultado="ok"):
    """Toda chamada ao Codex gasta cota, deu certo ou não: registra as duas."""
    p = Path(acervo) / "cota.json"
    lista = _ler(p, [])
    lista.append({"id": id_, "quando": quando or datetime.now().isoformat(timespec="minutes"), "resultado": resultado})
    p.write_text(json.dumps(lista, ensure_ascii=False, indent=1) + "\n")
    return len(lista)


if __name__ == "__main__":
    if len(sys.argv) in (4, 5) and sys.argv[1] == "registrar":
        print(registrar_geracao(sys.argv[2], sys.argv[3], resultado=sys.argv[4] if len(sys.argv) == 5 else "ok"))
    else:
        sys.exit("uso: python3 -m mediakit.cenas registrar <acervo> <id> [ok|falha]")

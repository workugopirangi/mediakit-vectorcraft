"""Biblioteca de peças de patrocínio: cenas aprovadas que outro kit pode reaproveitar (base "SEU LOGO AQUI" ou com marca).
Ordem pelo ranking visual dos 87 decks do repertório (inventario/tags-a*.json, 13/10/2026)."""
import json
import re
import shutil
from pathlib import Path

from mediakit import config

ORDEM = ["camisa", "celular-post", "cartaz", "kit-sacola", "copo", "backdrop", "notebook", "outdoor", "credencial",
         "embalagem", "portico", "bone", "wind-banner", "tenda", "celular-app", "numero-de-peito", "placa", "telao",
         "medalha", "stories", "estande"]


def _raiz(raiz):
    return Path(raiz) if raiz else config.RAIZ / "biblioteca" / "pecas"


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def listar(peca=None, raiz=None):
    indice = _raiz(raiz) / "indice.json"
    itens = json.loads(indice.read_text()) if indice.exists() else []
    return [i for i in itens if peca is None or i["peca"] == peca]


def registrar(peca, arquivo, marca, kit, ambiente="", raiz=None):
    if peca not in ORDEM:
        raise ValueError(f"peça '{peca}' não está na lista: {', '.join(ORDEM)}")
    base = _raiz(raiz)
    destino = base / peca / f"{_slug(marca)}-{_slug(kit)}{Path(arquivo).suffix}"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(arquivo, destino)
    rel = str(destino.relative_to(base))
    itens = [i for i in listar(raiz=base) if i["arquivo"] != rel]
    itens.append({"peca": peca, "arquivo": rel, "marca": marca, "kit": kit, "ambiente": ambiente})
    (base / "indice.json").write_text(json.dumps(itens, ensure_ascii=False, indent=1) + "\n")
    return destino

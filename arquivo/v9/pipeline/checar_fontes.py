#!/usr/bin/env python3
"""checar_fontes.py: confere catalogos/fontes.json e catalogos/pares.json contra os arquivos reais.
Falha (código 1) se: pasta não existe; peso listado sem arquivo; arquivo na pasta fora da lista; fonte variável (fvar);
acentos_ptbr diferente do cmap; par com família fora do catálogo, sem acentos ou com peso inexistente."""
import json, sys
from pathlib import Path
from fontTools.ttLib import TTFont

RAIZ = Path(__file__).resolve().parent.parent
ACENTOS = "ÁÀÂÃÉÊÍÓÔÕÚÇáàâãéêíóôõúç"
erros = []


def arq(fam, peso):
    d = RAIZ / fam["pasta"]
    return d / (f"{fam['familia']}.ttf" if peso == 400 else f"{fam['familia']}__{peso}.ttf")


cat = json.loads((RAIZ / "catalogos/fontes.json").read_text(encoding="utf-8"))["familias"]
por_nome = {f["familia"]: f for f in cat}
for f in cat:
    d = RAIZ / f["pasta"]
    if not d.is_dir():
        erros.append(f"{f['familia']}: pasta ausente"); continue
    arquivos = sorted(d.glob("*.ttf"))
    esperados = {arq(f, p) for p in f["pesos"]}
    for p in f["pesos"]:
        if not arq(f, p).exists():
            erros.append(f"{f['familia']}: falta arquivo do peso {p}")
    for a in arquivos:
        if a not in esperados:
            erros.append(f"{f['familia']}: arquivo fora da lista {a.name}")
    ok_acento = True
    for a in arquivos:
        t = TTFont(a)
        if "fvar" in t:
            erros.append(f"{f['familia']}: {a.name} é fonte variável")
        cm = t.getBestCmap()
        if not all(ord(c) in cm for c in ACENTOS):
            ok_acento = False
        nome = t["name"].getDebugName(1)
        if nome != f["familia"]:
            erros.append(f"{f['familia']}: nome interno '{nome}' em {a.name}")
    if ok_acento != f["acentos_ptbr"]:
        erros.append(f"{f['familia']}: acentos_ptbr={f['acentos_ptbr']} mas cmap diz {ok_acento}")
    if not (d / "OFL.txt").exists():
        erros.append(f"{f['familia']}: sem OFL.txt")

pares = json.loads((RAIZ / "catalogos/pares.json").read_text(encoding="utf-8"))["pares"]
ids = set()
for p in pares:
    if p["id"] in ids:
        erros.append(f"par {p['id']} repetido")
    ids.add(p["id"])
    for chave in ("display", "titulo", "corpo"):
        nome = p.get(chave)
        if nome is None and chave == "titulo":
            continue
        f = por_nome.get(nome)
        if not f:
            erros.append(f"par {p['id']}: {chave} '{nome}' fora do catálogo")
        elif not f["acentos_ptbr"]:
            erros.append(f"par {p['id']}: {nome} sem acentos")
    f = por_nome.get(p["display"])
    if f and p["peso_display"] not in f["pesos"]:
        erros.append(f"par {p['id']}: {p['display']} não tem peso {p['peso_display']}")

print(f"{len(cat)} famílias, {sum(len(f['pesos']) for f in cat)} arquivos, {len(pares)} pares, "
      f"{len({p['display'] for p in pares})} displays distintos, {len({p['corpo'] for p in pares})} corpos distintos")
for e in erros:
    print("ERRO", e)
print("VERDE" if not erros else f"{len(erros)} erro(s)")
sys.exit(1 if erros else 0)

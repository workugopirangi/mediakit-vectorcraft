#!/usr/bin/env python3
"""
test_contact_sheet.py: provas das folhas da prova para o dono cético no contact_sheet.py (references/10): --antes (antes,
depois e o recorte do recurso principal) e --cega (escolha cega com a chave à parte). Sem pytest:

  ~/.venvs/mediakit/bin/python pipeline/test_contact_sheet.py

Os kits são os sintéticos do test_medir_kit.py, com o fundo das páginas do antes vermelho e o do depois azul: a cor
amostrada no centro de cada célula diz de qual kit a página veio, e é isso que prova que a folha mostra o que a chave diz.
"""
import json, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import contact_sheet  # noqa: E402
from test_medir_kit import Tmp, montar, montar_antes  # noqa: E402

ANTES, DEPOIS, RECORTE = "#a02020", "#2020a0", (0, 255, 0)


def cor(png, caixa):
    """Cor do pixel no centro da caixa [x0, y0, x1, y1] da folha."""
    from PIL import Image
    x0, y0, x1, y1 = caixa
    return Image.open(png).convert("RGB").getpixel(((x0 + x1) // 2, (y0 + y1) // 2))


def de_quem(rgb):
    r, g, b = rgb
    return "antes" if r > b + 60 else ("depois" if b > r + 60 else "?")


def dois_kits(d, n_antes=8):
    return montar(d / "depois", fundo=DEPOIS), montar_antes(d / "antes", n_pag=n_antes, fundo=ANTES)


def repertorio(d):
    """Repertório mínimo: o recurso r0 com um recorte verde."""
    from PIL import Image
    rep = d / "rep"
    (rep / "recortes").mkdir(parents=True)
    Image.new("RGB", (200, 200), RECORTE).save(rep / "recortes" / "r0.png")
    (rep / "indice.json").write_text(json.dumps({"recursos": [{"id": "r0", "recortes": [
        {"arquivo": "recortes/r0.png", "legenda": "recorte de prova", "referencia": "ficticio", "pagina": 1}]}]}))
    return rep


def foto(p):
    return {str(f): (f.stat().st_size, f.stat().st_mtime_ns) for f in Path(p).rglob("*")}


# ------------------------------------------------------------------------------------------------- pareamento
def test_parear_nao_desloca_com_pagina_nova():
    pg = lambda n, ch, rot: {"n": n, "rotulo": rot, "composicao": {"chave": ch}}  # noqa: E731
    depois = {"paginas": [pg(1, "capa", "capa:b"), pg(2, "mapa", "mapa:a"), pg(3, "manifesto", "manifesto:a"),
                          pg(4, "cota:Master", "cota:a"), pg(5, "cota:Apoio", "cota:a")]}
    antes = {"paginas": [pg(1, "capa", "capa:c"), pg(2, "manifesto", "manifesto:b"), pg(3, "cota:Apoio", "cota:a"),
                         pg(4, "cota:Master", "cota:a"), pg(5, "contato", "contato:b")]}
    pares = [(d and d["n"], a and a["n"]) for d, a in contact_sheet.parear(depois, antes)]
    # capa com capa, a página nova sem par (a posição 2 do antes é o manifesto, que tem par por chave), cada cota com a
    # cota da mesma chave (a ordem trocou no antes), o contato do antes sobra no fim
    assert pares == [(1, 1), (2, None), (3, 2), (4, 4), (5, 3), (None, 5)], pares


# ------------------------------------------------------------------------------------------------- antes e depois
def test_antes_depois_colunas_recorte_e_paginas_diferentes():
    with Tmp() as d:
        dep, ant = dois_kits(d, n_antes=8)
        rep = repertorio(d)
        antes0 = foto(ant)
        r = contact_sheet.folha_antes_depois(dep, ant, rep=rep)
        out = Path(r["arquivo"])
        assert out == (dep / "saida" / "antes-depois-r1.png").resolve() and out.is_file(), r["arquivo"]
        assert foto(ant) == antes0, "a folha escreveu na pasta do antes"
        assert r["avisos"] and "8 páginas" in r["avisos"][0], r["avisos"]       # número diferente: avisa, não quebra
        assert [(p["depois"], p["antes"]) for p in r["pares"]] == [(n, n if n <= 8 else None) for n in range(1, 11)]
        p1 = r["pares"][0]
        assert de_quem(cor(out, p1["caixas"]["antes"])) == "antes" and de_quem(cor(out, p1["caixas"]["depois"])) == "depois"
        assert p1["recurso"] == "r0" and p1["recorte"].endswith("recortes/r0.png"), p1
        assert cor(out, p1["caixas"]["recorte"]) == RECORTE, cor(out, p1["caixas"]["recorte"])
        p2 = r["pares"][1]                                 # r3 não tem recorte no repertório: célula marcada, não quebra
        assert p2["recurso"] == "r3" and p2["recorte"] is None, p2
        p9 = r["pares"][8]                                 # sem página no antes: célula vazia, não a cor do antes
        assert de_quem(cor(out, p9["caixas"]["antes"])) == "?" and de_quem(cor(out, p9["caixas"]["depois"])) == "depois"


# ------------------------------------------------------------------------------------------------- escolha cega
def test_cega_chave_muda_com_a_semente_e_se_repete_com_ela():
    with Tmp() as d:
        dep, ant = dois_kits(d)
        r1 = contact_sheet.escolha_cega(dep, ant, 1)
        k1 = Path(r1["chave"]).read_bytes()
        r1b = contact_sheet.escolha_cega(dep, ant, 1)
        assert r1b["sha256_chave"] == r1["sha256_chave"] and Path(r1b["chave"]).read_bytes() == k1, "mesma semente, outra chave"
        r2 = contact_sheet.escolha_cega(dep, ant, 2)
        assert [p["A"] for p in r2["pares"]] != [p["A"] for p in r1["pares"]], "outra semente, mesma ordem"
        assert r2["sha256_chave"] != r1["sha256_chave"]
        import hashlib
        assert hashlib.sha256(Path(r2["chave"]).read_bytes()).hexdigest() == r2["sha256_chave"]
        ordem = [p["A"] for p in r1["pares"]]
        assert "antes" in ordem and "depois" in ordem, ordem      # o sorteio mistura os lados (não é sempre o mesmo)


def test_cega_imagem_bate_com_a_chave():
    with Tmp() as d:
        dep, ant = dois_kits(d)
        antes0 = foto(ant)
        for semente in (1, 2, 3):
            r = contact_sheet.escolha_cega(dep, ant, semente)
            chave = json.loads(Path(r["chave"]).read_text())
            assert chave["semente"] == semente and chave["imagem"] == "escolha-cega.png"
            vistos = [{lado: de_quem(cor(r["arquivo"], cx[lado])) for lado in "AB"} for cx in r["caixas"]]
            esperado = [{"A": p["A"], "B": p["B"]} for p in chave["pares"]]
            assert vistos == esperado, (semente, vistos, esperado)
            assert {p["A"] for p in chave["pares"]} | {p["B"] for p in chave["pares"]} == {"antes", "depois"}
        assert foto(ant) == antes0, "a escolha cega escreveu na pasta do antes"


def test_cega_paginas_diferentes_e_semente_obrigatoria():
    with Tmp() as d:
        dep, ant = dois_kits(d, n_antes=8)
        r = contact_sheet.escolha_cega(dep, ant, 5)
        chave = json.loads(Path(r["chave"]).read_text())
        assert len(chave["pares"]) == 8 and chave["sem_par"] == [{"pagina_depois": 9}, {"pagina_depois": 10}], chave["sem_par"]
        assert r["avisos"] and "8 páginas" in r["avisos"][0], r["avisos"]
        try:
            contact_sheet.escolha_cega(dep, ant, None)
            raise AssertionError("sem semente deveria recusar")
        except SystemExit as e:
            assert "--semente" in str(e)


if __name__ == "__main__":
    falhou = 0
    for nome, fn in list(globals().items()):
        if nome.startswith("test_"):
            try:
                fn(); print("ok  ", nome)
            except AssertionError as e:
                falhou += 1; print("FALHOU", nome, str(e)[:1500])
    print("PROVAS:", "VERDES" if not falhou else f"{falhou} FALHA(S)")
    sys.exit(1 if falhou else 0)

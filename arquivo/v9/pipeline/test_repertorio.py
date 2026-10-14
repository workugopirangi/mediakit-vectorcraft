#!/usr/bin/env python3
"""Provas do repertorio.py (Frente C). Rodar: ~/.venvs/mediakit/bin/python test_repertorio.py. Todas usam um repertório
SINTÉTICO numa pasta temporária (4 padrões, 2 referências, recortes de cor lisa): a ferramenta é provada sem depender do
conteúdo real, que o Ugo e o Claude escrevem em paralelo. Terminam em `PROVAS: VERDES`."""
import argparse, contextlib, copy, hashlib, json, os, shutil, signal, subprocess, sys, tempfile, types
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import repertorio  # noqa: E402

PY = sys.executable
SCRIPT = str(AQUI / "repertorio.py")

EX_NUMERO = {"mensagem": "o número domina a página", "foco": "numero", "elementos": [
    {"id": "numeral", "papel": "heroi", "funcao": "foco", "camada": "atras",
     "ancora": {"relacao": "sangra", "borda": "esq", "corte": "1/3", "y": "cy=numero.cy"},
     "escala": {"altura": "1/2p"}, "porque": "o número maior que a página vira fundo"}]}
EX_OBJETO = {"mensagem": "o objeto entra na foto", "foco": "foto", "elementos": [
    {"id": "bola", "papel": "heroi", "funcao": "profundidade",
     "ancora": {"relacao": "sobrepoe", "alvo": "foto", "lado": "esq", "fracao": "1/3", "y": "base=foto.base-e5"},
     "escala": {"altura": "1/3p"}, "porque": "a bola sai da foto em direção ao título"}]}
EX_FIO = {"mensagem": "o fio liga o título à foto", "foco": "titulo", "elementos": [
    {"id": "fio-titulo", "papel": "estrutura", "funcao": "conexao",
     "ancora": {"relacao": "liga", "modo": "conecta", "de": "titulo.dir", "para": "foto.esq"}, "porque": "liga o título à foto"}]}

PADROES = [
    dict(id="numero-que-sangra", nome="Número que sangra e vira fundo", problema="página de dados com um número dominante",
         tipo_pagina=["publico", "prova"], funcao=["foco", "organizacao"], relacao=["sangra", "alinha"], rota="codigo",
         tom=["performance"], densidade="media", exemplo=EX_NUMERO, recortes=[("ref-um", 7, "Número de 70% da altura sangrando à esquerda", False, (200, 40, 40)),
                                                                              ("ref-dois", 3, "Número solto no meio, sem relação", True, (40, 40, 200))]),
    dict(id="objeto-que-entra-na-foto", nome="Objeto que entra na foto", problema="ativo sem profundidade, objeto solto ao lado da foto",
         tipo_pagina=["ativo_painel", "ativo_topo"], funcao=["profundidade", "conexao"], relacao=["sobrepoe"], rota="imagem",
         tom=["performance", "festa"], densidade="respiro", exemplo=EX_OBJETO, recortes=[("ref-um", 2, "A bola cruza a borda da foto", False, (40, 160, 60))]),
    dict(id="fio-que-liga-titulo-e-foto", nome="Fio que liga título e foto", problema="título e foto sem relação entre si",
         tipo_pagina=["capa", "divisor"], funcao=["conexao"], relacao=["liga", "alinha"], rota="codigo", tom=["corporativo"],
         densidade="respiro", exemplo=EX_FIO, recortes=[("ref-dois", 1, "Fio de 2 px do título à foto", False, (220, 180, 30))]),
    dict(id="selo-na-margem", nome="Selo preso à margem", problema="selo flutuando sem alinhamento",
         tipo_pagina=["cota", "contato"], funcao=["identidade", "acabamento"], relacao=["alinha"], rota="hibrido", tom=["causa"],
         densidade="alta", exemplo=None, recortes=[]),
]
SECOES_MD = ["1. Problema ou efeito", "2. Como se organiza", "3. Onde funciona", "4. O essencial", "5. O que pode variar",
             "6. Como adaptar", "7. Erros que estragam", "8. Como construir e conferir"]


def _lista_yaml(v):
    return "[" + ", ".join(v) + "]"


def md_do_padrao(p, exemplo=None, com_secoes=True, front=True, id_front=None):
    """O .md no formato combinado: front matter YAML, as 8 seções, Trecho de composição (```json) e Referências."""
    f = ""
    if front:
        f = ("---\n" f"id: {id_front or p['id']}\n" f"nome: \"{p['nome']}\"\n" f"problema: \"{p['problema']}\"\n"
             f"tipo_pagina: {_lista_yaml(p['tipo_pagina'])}\n" f"funcao: {_lista_yaml(p['funcao'])}\n"
             f"relacao: {_lista_yaml(p['relacao'])}\n" f"rota: {p['rota']}\n" f"tom: {_lista_yaml(p['tom'])}\n"
             f"densidade: {p['densidade']}\n---\n\n")
    corpo = f"# {p['nome']}\n\n"
    if com_secoes:
        for t in SECOES_MD:
            corpo += f"## {t}\n\nTexto de **{t}** com `codigo` e uma lista:\n\n- primeiro item\n- segundo item\n\n"
    ex = p.get("exemplo") if exemplo is None else exemplo
    if ex is not None:
        corpo += "## Trecho de composição\n\n```json\n" + json.dumps(ex, ensure_ascii=False, indent=2) + "\n```\n\n"
    corpo += "## Referências\n\n- ref-um, página 7\n"
    return f + corpo


def imagem(caminho, cor, tam=(640, 360), retangulo=None):
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", tam, cor)
    if retangulo:
        ImageDraw.Draw(im).rectangle(retangulo, fill=(255, 255, 255))
    im.save(caminho, quality=92)


def montar(rep):
    """Repertório sintético sadio em `rep` (pasta nova)."""
    rep = Path(rep)
    indice = {"versao": 1, "padroes": [], "referencias": [
        {"id": "ref-um", "nome": "Deck de patrocínio Um", "url": "https://exemplo.test/um", "arquivo": "referencias/ref-um.md"},
        {"id": "ref-dois", "nome": "Campanha Dois", "url": None, "arquivo": "referencias/ref-dois.md"}]}
    for r in indice["referencias"]:
        (rep / r["arquivo"]).parent.mkdir(parents=True, exist_ok=True)
        (rep / r["arquivo"]).write_text(f"# {r['nome']}\n\nFicha da referência **{r['id']}**.\n", encoding="utf-8")
    for p in PADROES:
        item = {k: p[k] for k in ("id", "nome", "problema", "tipo_pagina", "funcao", "relacao", "rota", "tom", "densidade")}
        item["arquivo"] = f"padroes/{p['id']}.md"
        item["recortes"] = []
        for ref, pag, legenda, anti, cor in p["recortes"]:
            arq = f"recortes/{p['id']}__{ref}-{pag:02d}.jpg"
            imagem(rep / arq, cor)
            r = {"arquivo": arq, "referencia": ref, "pagina": pag, "legenda": legenda}
            if anti:
                r["anti"] = True
            item["recortes"].append(r)
        if p["exemplo"] is not None:
            item["composicao_exemplo"] = copy.deepcopy(p["exemplo"])
        (rep / item["arquivo"]).parent.mkdir(parents=True, exist_ok=True)
        (rep / item["arquivo"]).write_text(md_do_padrao(p), encoding="utf-8")
        indice["padroes"].append(item)
    (rep / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=2), encoding="utf-8")
    return indice


def indice_de(rep):
    return json.loads((Path(rep) / "indice.json").read_text(encoding="utf-8"))


def gravar_indice(rep, indice):
    (Path(rep) / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=2), encoding="utf-8")


def item(indice, pid):
    return next(p for p in indice["padroes"] if p["id"] == pid)


def falhas(res):
    return [m for n, m in res if n == "FALHA"]


def avisos(res):
    return [m for n, m in res if n == "AVISO"]


def com_repertorio(fn):
    def corpo():
        with tempfile.TemporaryDirectory() as d:
            rep = Path(d) / "repertorio"; montar(rep)
            return fn(rep)
    corpo.__name__ = fn.__name__
    return corpo


def cli(*args):
    r = subprocess.run([PY, SCRIPT, *map(str, args)], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


# ---------------------------------------------------------------- vocabulário e schema
def test_vocabularios_do_schema_sao_os_do_codigo():
    import composicao, regua
    sch = json.loads(repertorio.SCHEMA.read_text(encoding="utf-8"))
    props = sch["definitions"]["padrao"]["properties"]
    enum = lambda c: set(props[c]["items"]["enum"] if "items" in props[c] else props[c]["enum"])  # noqa: E731
    assert enum("funcao") == set(composicao.FUNCOES), enum("funcao") ^ set(composicao.FUNCOES)
    assert enum("relacao") == set(composicao.RELACOES) | {"fundo"}, enum("relacao")
    assert enum("tipo_pagina") == set(regua.TIPOS) | {"territorio", "historico_logos", "redes", "premiacao", "outro"}, enum("tipo_pagina") ^ set(regua.TIPOS)
    assert enum("rota") == set(repertorio.ROTAS) and enum("tom") == set(repertorio.TONS) and enum("densidade") == set(repertorio.DENSIDADES)
    f, r, t = repertorio.vocabularios()
    assert set(f) == enum("funcao") and set(r) == enum("relacao") and set(t) == enum("tipo_pagina")
    print("   funcao, relacao, tipo_pagina, rota, tom e densidade do schema == composicao.py / regua.py (+ fundo, outro e os 4 tipos extras)")


# ---------------------------------------------------------------- front matter e markdown
def test_front_matter_aceita_os_estilos_de_yaml():
    texto = ('---\nid: numero-que-sangra\nnome: "Número que sangra: e vira fundo"\nproblema: \'página de dados, com número\'\n'
             'tipo_pagina: [publico, "prova", \'cota\']\nfuncao:\n  - foco\n  - organizacao\nrota: codigo   # comentário\n'
             'tom:\n- performance\ndensidade: media\nlongo: >\n  uma frase\n  em duas linhas\n---\n\n# Título\n\ncorpo\n')
    meta, corpo = repertorio.ler_front_matter(texto)
    assert meta == {"id": "numero-que-sangra", "nome": "Número que sangra: e vira fundo", "problema": "página de dados, com número",
                    "tipo_pagina": ["publico", "prova", "cota"], "funcao": ["foco", "organizacao"], "rota": "codigo",
                    "tom": ["performance"], "densidade": "media", "longo": "uma frase em duas linhas"}, meta
    assert corpo.startswith("# Título"), corpo
    assert repertorio.ler_front_matter("# sem front matter\n") == (None, "# sem front matter\n")
    assert repertorio.ler_front_matter("---\nid: x\nsem fechar\n")[0] is None


def test_markdown_vira_html_seguro():
    md = ("## 1. Problema ou efeito\n\nTexto com **negrito**, *itálico*, `tipo_pagina` e [um link](https://exemplo.test/a?b=1&c=2).\n\n"
          "- item um\n  - subitem\n- item dois\n\n1. passo\n2. passo\n\n> uma citação\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n"
          "```json\n{\"a\": \"<b>\"}\n```\n\n<script>alert(1)</script>\n\n[ruim](javascript:alert(1))\n\n---\n")
    h = repertorio.md_para_html(md)
    for esperado in ("<h3>1. Problema ou efeito</h3>", "<strong>negrito</strong>", "<em>itálico</em>", "<code>tipo_pagina</code>",
                     '<a href="https://exemplo.test/a?b=1&amp;c=2">um link</a>', "<ul><li>item um<ul><li>subitem</li></ul></li><li>item dois</li></ul>",
                     "<ol><li>passo</li><li>passo</li></ol>", "<blockquote><p>uma citação</p></blockquote>", "<th>a</th>", "<td>2</td>",
                     "<pre><code class=language-json>{\"a\": \"&lt;b&gt;\"}</code></pre>", "<hr>"):
        assert esperado in h, (esperado, h)
    assert "<script>" not in h and "&lt;script&gt;" in h, h                      # nada do .md vira tag
    assert 'href="javascript' not in h and "[ruim](javascript:alert(1))" in h, h  # link perigoso não vira link
    assert "tipo<em>" not in h, "snake_case dentro do texto não vira itálico"


def test_markdown_com_hashtag_ou_numero_no_comeco_da_linha_nao_trava():
    """`#1 do ranking` e `#corrida` não são título: viram parágrafo (antes, o laço do parágrafo não andava e o html travava)."""
    def trava(*_):
        raise AssertionError("md_para_html travou (laço sem avanço)")
    signal.signal(signal.SIGALRM, trava); signal.alarm(5)
    try:
        h = repertorio.md_para_html("#1 do ranking\n\n#corrida e #trail\ncontinua na linha de baixo\n\n- item\n#hashtag depois da lista\n\n## 2. Seção")
    finally:
        signal.alarm(0)
    assert "<p>#1 do ranking</p>" in h and "<p>#corrida e #trail continua na linha de baixo</p>" in h and "<h3>2. Seção</h3>" in h, h
    assert "<li>item</li>" in h and "<p>#hashtag depois da lista</p>" in h, h


def test_markdown_e_front_matter_aguentam_entrada_torta_sem_travar_nem_vazar_tag():
    """300 documentos sorteados (semente fixa) de fragmentos de markdown e de lixo: nenhum trava, nenhum levanta erro e
    nenhum deixa uma tag de script ou um link javascript passar."""
    import random
    frag = ["#", "# a", "## b", "###", "####### sete", "- x", "* y", "+ z", "1. z", "2) w", "  - aninhado", "    - mais fundo", "\t- tab", "> citação", ">",
            "| a | b |", "|---|---|", "| só uma |", "```", "```json", "---", "***", "texto *it* **negrito** `código`", "[l](http://x.test/a?b=1&c=2)",
            "[l](javascript:alert(1))", "<script>alert(1)</script>", "<img src=x onerror=alert(1)>", "", "", "  indentado", "&amp; &lt;", "_a_ b_c_", "`", "**", "*",
            "[", "](", "||", "|", "id: x", "---\nid: a\n---", "chave: [a, \"b", "- item: 3", "texto"]
    def trava(*_):
        raise AssertionError("travou")
    rng = random.Random(20261009)
    signal.signal(signal.SIGALRM, trava); signal.alarm(30)
    try:
        for n in range(300):
            doc = "\n".join(rng.choice(frag) for _ in range(rng.randint(1, 14)))
            h = repertorio.md_para_html(doc)
            assert isinstance(h, str) and "<script" not in h.lower() and "<img" not in h.lower() and 'href="javascript' not in h.lower(), (n, doc, h)
            meta, corpo = repertorio.ler_front_matter(doc)
            assert (meta is None or isinstance(meta, dict)) and isinstance(corpo, str), (n, doc)
            repertorio.trecho_de_composicao(doc)
    finally:
        signal.alarm(0)


# ---------------------------------------------------------------- buscar
@com_repertorio
def test_buscar_ranking_esperado(rep):
    ind = repertorio.carregar(rep)
    ids = lambda r: [x["padrao"]["id"] for x in r]  # noqa: E731
    notas = lambda r: [x["nota"] for x in r]        # noqa: E731
    # página publico (+3) e as duas palavras do problema nas duas colunas: problema (numer, domin) +2 e nome (numer) +1
    r = repertorio.buscar(ind, pagina="publico", problema="número dominante")
    assert ids(r) == ["numero-que-sangra"] and notas(r) == [6], (ids(r), notas(r))
    assert r[0]["razoes"] == ["página publico", "palavras no problema: domin, numer", "palavras no nome: numer"], r[0]["razoes"]
    # função conexao (+2) e relação alinha (+2): o fio tem as duas (4); empate em 2 desempata pelo id
    r = repertorio.buscar(ind, funcoes=["conexao"], relacoes=["alinha"])
    assert ids(r) == ["fio-que-liga-titulo-e-foto", "numero-que-sangra", "objeto-que-entra-na-foto", "selo-na-margem"] and notas(r) == [4, 2, 2, 2], (ids(r), notas(r))
    # ativo vale ativo_painel e ativo_topo; capa:c e cota:Master valem o tipo
    assert ids(repertorio.buscar(ind, pagina="ativo")) == ["objeto-que-entra-na-foto"]
    assert ids(repertorio.buscar(ind, pagina="capa:c")) == ["fio-que-liga-titulo-e-foto"]
    assert ids(repertorio.buscar(ind, pagina="Cota:Master")) == ["selo-na-margem"]
    # sem acento e sem caixa; "e" é stopword; título e foto casam no problema e no nome do fio (4) e na foto do objeto (2)
    r = repertorio.buscar(ind, problema="TITULO e FOTO")
    assert ids(r) == ["fio-que-liga-titulo-e-foto", "objeto-que-entra-na-foto"] and notas(r) == [4, 2], (ids(r), notas(r))
    # plural e singular casam ("números" e "número")
    assert ids(repertorio.buscar(ind, problema="números dominantes")) == ["numero-que-sangra"]
    # palavra de ligação não casa: "com" está no problema do padrão do número, mas só "dados" vale (nota 1)
    r = repertorio.buscar(ind, problema="dados com um")
    assert ids(r) == ["numero-que-sangra"] and notas(r) == [1] and r[0]["razoes"] == ["palavras no problema: dado"], (ids(r), notas(r), r[0]["razoes"])
    # rota +1, tom +1; critérios somam
    r = repertorio.buscar(ind, rota="codigo", tons=["performance", "festa"])
    assert ids(r) == ["numero-que-sangra", "objeto-que-entra-na-foto", "fio-que-liga-titulo-e-foto"] and notas(r) == [2, 2, 1], (ids(r), notas(r))
    # -n corta; sem critério lista todos em ordem de id; critério sem casamento não devolve nada
    assert len(repertorio.buscar(ind, funcoes=["conexao"], n=1)) == 1
    assert ids(repertorio.buscar(ind, n=0)) == sorted(p["id"] for p in ind["padroes"]) and repertorio.buscar(ind)[0]["razoes"] == ["sem critério"]
    assert repertorio.buscar(ind, problema="zebra cachimbo") == []
    print("   ranking conferido à mão em 9 consultas")


@com_repertorio
def test_buscar_cli_e_deterministico_entre_processos_e_valida_o_vocabulario(rep):
    saidas = []
    for semente in ("1", "2", "777"):
        r = subprocess.run([PY, SCRIPT, "buscar", "--repertorio", str(rep), "--funcao", "conexao,foco", "--relacao", "alinha", "--json"],
                           capture_output=True, text=True, env=dict(os.environ, PYTHONHASHSEED=semente))
        assert r.returncode == 0, r.stderr
        saidas.append(r.stdout)
    assert saidas[0] == saidas[1] == saidas[2], "a ordem muda com a semente de hash"
    dados = json.loads(saidas[0])
    assert [d["id"] for d in dados] == ["fio-que-liga-titulo-e-foto", "numero-que-sangra", "objeto-que-entra-na-foto", "selo-na-margem"][:len(dados)]
    assert dados[0]["arquivo"].endswith("padroes/fio-que-liga-titulo-e-foto.md") and Path(dados[0]["arquivo"]).is_file()
    codigo, out, err = cli("buscar", "--repertorio", rep, "--funcao", "inexistente")
    assert codigo != 0 and "função `inexistente` não existe" in (out + err), (out, err)
    codigo, out, _ = cli("buscar", "--repertorio", rep, "--pagina", "publico")
    assert codigo == 0 and "numero-que-sangra" in out and "padroes/numero-que-sangra.md" in out and "(nota 3: página publico)" in out, out
    print("   3 processos (PYTHONHASHSEED 1, 2, 777): saída idêntica")


# ---------------------------------------------------------------- checar
@com_repertorio
def test_checar_repertorio_sadio_so_avisa_do_padrao_sem_recorte(rep):
    res = repertorio.checar(rep)
    assert falhas(res) == [], falhas(res)
    assert avisos(res) == ["padrão `selo-na-margem` sem recorte (a folha e o html ficam sem imagem)"], avisos(res)
    codigo, out, _ = cli("checar", "--repertorio", rep)
    assert codigo == 0 and "0 falha(s), 1 aviso(s)" in out, out


def _so_uma_falha(rep, trecho):
    f = falhas(repertorio.checar(rep))
    print("  ", f)
    assert len(f) == 1 and trecho in f[0], f
    return f


@com_repertorio
def test_checar_acusa_recorte_faltando(rep):
    (rep / "recortes" / "numero-que-sangra__ref-um-07.jpg").unlink()
    _so_uma_falha(rep, "recorte `recortes/numero-que-sangra__ref-um-07.jpg` não existe")
    codigo, out, _ = cli("checar", "--repertorio", rep)
    assert codigo == 1 and "FALHA" in out, out


@com_repertorio
def test_checar_acusa_id_duplicado(rep):
    ind = indice_de(rep)
    ind["padroes"].append(copy.deepcopy(item(ind, "selo-na-margem")))
    gravar_indice(rep, ind)
    _so_uma_falha(rep, "padrão `selo-na-margem` repetido no índice")


@com_repertorio
def test_checar_acusa_exemplo_de_composicao_invalido(rep):
    # âncora alinha sem o eixo y: o schema aceita a forma por ser oneOf, a regra de composicao.validar barra; .md e índice iguais
    ruim = copy.deepcopy(EX_NUMERO)
    ruim["elementos"][0]["ancora"] = {"relacao": "alinha", "x": "esq=titulo.esq"}
    ind = indice_de(rep); item(ind, "numero-que-sangra")["composicao_exemplo"] = ruim; gravar_indice(rep, ind)
    p = next(p for p in PADROES if p["id"] == "numero-que-sangra")
    (rep / "padroes" / "numero-que-sangra.md").write_text(md_do_padrao(p, exemplo=ruim), encoding="utf-8")
    f = falhas(repertorio.checar(rep))
    print("  ", f)
    assert f and all("trecho de composição inválido" in m and "numero-que-sangra" in m for m in f), f
    assert any("âncora `alinha`: 'y' is a required property" in m for m in f), f          # a mensagem diz o que falta, não só 'oneOf'
    assert any("alinha precisa dos dois eixos" in m for m in f), f


@com_repertorio
def test_checar_acusa_exemplo_com_chave_de_digitacao_errada(rep):
    ruim = copy.deepcopy(EX_OBJETO)
    ruim["elementos"][0]["funcoa"] = "foco"           # erro de digitação: o schema estrito reprova
    ind = indice_de(rep); item(ind, "objeto-que-entra-na-foto")["composicao_exemplo"] = ruim; gravar_indice(rep, ind)
    p = next(p for p in PADROES if p["id"] == "objeto-que-entra-na-foto")
    (rep / "padroes" / "objeto-que-entra-na-foto.md").write_text(md_do_padrao(p, exemplo=ruim), encoding="utf-8")
    f = falhas(repertorio.checar(rep))
    assert f and any("funcoa" in m for m in f), f


@com_repertorio
def test_checar_acusa_md_e_indice_diferentes_no_trecho_de_composicao(rep):
    p = next(p for p in PADROES if p["id"] == "numero-que-sangra")
    outro = copy.deepcopy(EX_NUMERO); outro["mensagem"] = "mensagem diferente da do índice"
    (rep / "padroes" / "numero-que-sangra.md").write_text(md_do_padrao(p, exemplo=outro), encoding="utf-8")
    _so_uma_falha(rep, "o trecho de composição do .md e o `composicao_exemplo` do índice são diferentes")


@com_repertorio
def test_checar_acusa_trecho_so_de_um_lado(rep):
    p = next(p for p in PADROES if p["id"] == "numero-que-sangra")
    # índice tem o exemplo e o .md não tem a seção
    texto = md_do_padrao(p).split("## Trecho de composição")[0] + "## Referências\n\n- x\n"
    (rep / "padroes" / "numero-que-sangra.md").write_text(texto, encoding="utf-8")
    _so_uma_falha(rep, "o índice tem `composicao_exemplo` e o .md não tem a seção `## Trecho de composição`")
    # .md tem o trecho e o índice não tem o exemplo
    (rep / "padroes" / "numero-que-sangra.md").write_text(md_do_padrao(p), encoding="utf-8")
    ind = indice_de(rep); del item(ind, "numero-que-sangra")["composicao_exemplo"]; gravar_indice(rep, ind)
    _so_uma_falha(rep, "o .md tem trecho de composição e o índice não tem `composicao_exemplo`")


@com_repertorio
def test_checar_acusa_bloco_json_quebrado_no_md(rep):
    p = next(p for p in PADROES if p["id"] == "numero-que-sangra")
    texto = md_do_padrao(p).replace('"foco": "numero"', '"foco": numero')
    (rep / "padroes" / "numero-que-sangra.md").write_text(texto, encoding="utf-8")
    _so_uma_falha(rep, "trecho de composição do .md: JSON inválido")


@com_repertorio
def test_checar_acusa_front_matter_com_id_diferente_ou_ausente(rep):
    p = next(p for p in PADROES if p["id"] == "selo-na-margem")
    (rep / "padroes" / "selo-na-margem.md").write_text(md_do_padrao(p, id_front="selo-na-borda"), encoding="utf-8")
    _so_uma_falha(rep, "o front matter de `padroes/selo-na-margem.md` diz id `selo-na-borda`")
    (rep / "padroes" / "selo-na-margem.md").write_text(md_do_padrao(p, front=False), encoding="utf-8")
    _so_uma_falha(rep, "sem front matter")


@com_repertorio
def test_checar_acusa_nome_do_arquivo_diferente_do_id_e_arquivos_faltando(rep):
    ind = indice_de(rep); item(ind, "selo-na-margem")["arquivo"] = "padroes/outro-nome.md"; gravar_indice(rep, ind)
    f = falhas(repertorio.checar(rep))
    assert any("deveria se chamar `selo-na-margem.md`" in m for m in f) and any("`padroes/outro-nome.md` não existe" in m for m in f), f


@com_repertorio
def test_checar_acusa_md_de_padrao_e_de_referencia_faltando(rep):
    (rep / "padroes" / "fio-que-liga-titulo-e-foto.md").unlink()
    (rep / "referencias" / "ref-dois.md").unlink()
    f = falhas(repertorio.checar(rep))
    assert len(f) == 2 and any("`padroes/fio-que-liga-titulo-e-foto.md` não existe" in m for m in f) and any("referência `ref-dois`" in m for m in f), f


@com_repertorio
def test_checar_acusa_recorte_com_referencia_que_nao_existe(rep):
    ind = indice_de(rep); item(ind, "objeto-que-entra-na-foto")["recortes"][0]["referencia"] = "ref-fantasma"; gravar_indice(rep, ind)
    _so_uma_falha(rep, "cita a referência `ref-fantasma`, que não está em referencias[]")


@com_repertorio
def test_checar_acusa_vocabulario_chave_extra_e_json_quebrado(rep):
    ind = indice_de(rep)
    item(ind, "selo-na-margem")["funcao"] = ["foto"]                # fora do vocabulário
    item(ind, "selo-na-margem")["cor"] = "azul"                     # chave que o schema estrito não conhece
    item(ind, "fio-que-liga-titulo-e-foto")["tipo_pagina"] = ["capa", "pagina-inventada"]
    gravar_indice(rep, ind)
    f = falhas(repertorio.checar(rep))
    print("  ", f)
    assert len(f) == 3 and any("'foto' is not one of" in m for m in f) and any("'cor' was unexpected" in m for m in f) and any("pagina-inventada" in m for m in f), f
    (rep / "indice.json").write_text("{ isto não é json", encoding="utf-8")
    f = falhas(repertorio.checar(rep))
    assert len(f) == 1 and "indice.json não é JSON válido" in f[0], f
    shutil.rmtree(rep)
    assert "indice.json" in falhas(repertorio.checar(rep))[0]


@com_repertorio
def test_checar_avisa_recorte_orfao_seccao_fora_do_roteiro_e_etiqueta_diferente(rep):
    imagem(rep / "recortes" / "sobrou.jpg", (9, 9, 9))
    imagem(rep / "recortes" / "_conferencia-ref-um.jpg", (9, 9, 9))          # folha de conferência: ignorada
    p = next(p for p in PADROES if p["id"] == "selo-na-margem")
    texto = md_do_padrao(p).replace("## 4. O essencial", "## 4. Outra coisa").replace("## 6. Como adaptar\n", "")
    texto = texto.replace("rota: hibrido", "rota: codigo")
    (rep / "padroes" / "selo-na-margem.md").write_text(texto, encoding="utf-8")
    res = repertorio.checar(rep)
    a = avisos(res)
    print("  ", a)
    assert falhas(res) == [], falhas(res)
    assert any("recorte órfão: `recortes/sobrou.jpg`" in m for m in a) and not any("_conferencia" in m for m in a), a
    assert any("a seção 4 devia ser `O essencial`, está `4. Outra coisa`" in m for m in a), a
    assert any("falta a seção `## 6. Como adaptar`" in m for m in a), a
    assert any("`rota` do front matter (codigo) é diferente do índice (hibrido)" in m for m in a), a


@com_repertorio
def test_checar_aceita_lista_do_front_matter_escrita_como_texto_e_em_outra_ordem(rep):
    p = next(p for p in PADROES if p["id"] == "objeto-que-entra-na-foto")
    texto = md_do_padrao(p).replace("tom: [performance, festa]", "tom: festa, performance").replace("funcao: [profundidade, conexao]", "funcao:\n  - conexao\n  - profundidade")
    assert "tom: festa, performance" in texto and "  - conexao" in texto
    (rep / "padroes" / "objeto-que-entra-na-foto.md").write_text(texto, encoding="utf-8")
    res = repertorio.checar(rep)
    assert falhas(res) == [] and not any("front matter" in m for m in avisos(res)), res
    # e uma etiqueta realmente diferente continua avisando
    (rep / "padroes" / "objeto-que-entra-na-foto.md").write_text(texto.replace("tom: festa, performance", "tom: festa, causa"), encoding="utf-8")
    assert any("`tom` do front matter" in m for m in avisos(repertorio.checar(rep)))


# ---------------------------------------------------------------- recortar
def _analise(d, padroes=None, ref="web-deck-teste"):
    """analise.json no formato da RUBRICA, apontando para imagens sintéticas em <d>/captura/."""
    padroes = padroes or [{"id_sugerido": "numero-que-sangra", "nome": "x", "exemplos": [
        {"imagem": "captura/web-deck-teste/07.jpg", "pagina": 7, "recorte": [0.1, 0.2, 0.6, 0.8], "o_que_mostra": "o número sangra"}]}]
    caminho = Path(d) / "analise" / f"{ref}.json"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps({"referencia": ref, "fonte": "https://exemplo.test", "camada": "media", "resumo": "teste", "padroes": padroes}), encoding="utf-8")
    return caminho


def test_recortar_gera_o_arquivo_com_tamanho_nome_e_folga_esperados():
    with tempfile.TemporaryDirectory() as d:
        # 1000x600 branco com um retângulo cinza em [0.1, 0.2, 0.6, 0.8]; a folga de 3% de cada lado põe o corte em
        # (70, 102) a (630, 498): 560 x 396 px, sem redução (lado maior < 900)
        imagem(Path(d) / "captura/web-deck-teste/07.jpg", (255, 255, 255), (1000, 600))
        im = Image.open(Path(d) / "captura/web-deck-teste/07.jpg"); ImageDraw.Draw(im).rectangle([100, 120, 599, 479], fill=(40, 40, 40)); im.save(Path(d) / "captura/web-deck-teste/07.jpg", quality=95)
        r = repertorio.recortar(_analise(d), Path(d) / "saida", [d])
        assert r["problemas"] == [] and len(r["feitos"]) == 1, r
        f = r["feitos"][0]
        assert f["arquivo"] == "recortes/numero-que-sangra__web-deck-teste-07.jpg" and f["padrao"] == "numero-que-sangra" and f["pagina"] == 7, f
        assert f["legenda"] == "o número sangra" and f["referencia"] == "web-deck-teste", f
        im = Image.open(f["caminho"])
        assert im.format == "JPEG" and im.size == (560, 396), (im.format, im.size)
        assert im.quantization[0][0] == 6, f"qualidade 80 do JPEG (tabela de quantização 6, não {im.quantization[0][0]})"
        # a folga existe: o canto do corte é branco (fora do retângulo) e o centro é cinza escuro
        assert min(im.getpixel((5, 5))) > 235 and max(im.getpixel((280, 198))) < 70, (im.getpixel((5, 5)), im.getpixel((280, 198)))
        # a borda do retângulo começa 30 px (3% de 1000) depois do canto do corte
        assert max(im.getpixel((20, 198))) > 235 and max(im.getpixel((40, 198))) < 70, (im.getpixel((20, 198)), im.getpixel((40, 198)))
        conf = Path(r["conferencia"])
        assert conf.name == "_conferencia-web-deck-teste.jpg" and conf.is_file() and conf.parent == Path(d) / "saida"
        print(f"   {f['arquivo']}: {im.size[0]}x{im.size[1]} JPEG; folga de 3% conferida nos pixels; folha de conferência {conf.name}")


def test_recortar_reduz_o_lado_maior_para_900_e_nao_amplia():
    with tempfile.TemporaryDirectory() as d:
        imagem(Path(d) / "captura/web-deck-teste/07.jpg", (90, 90, 90), (2000, 1200))       # página inteira: 2000x1200 -> 900x540
        padroes = [{"id_sugerido": "pagina-toda", "exemplos": [{"imagem": "captura/web-deck-teste/07.jpg", "pagina": 7, "recorte": [0, 0, 1, 1], "o_que_mostra": "tudo"}]},
                   {"id_sugerido": "pequeno", "exemplos": [{"imagem": "captura/web-deck-teste/07.jpg", "pagina": 7, "recorte": [0.4, 0.4, 0.5, 0.5], "o_que_mostra": "pedaço"}]}]
        r = repertorio.recortar(_analise(d, padroes), Path(d) / "saida", [d])
        tam = {f["padrao"]: tuple(f["tamanho"]) for f in r["feitos"]}
        assert tam["pagina-toda"] == (900, 540), tam
        assert tam["pequeno"] == (320, 192), tam            # 0.1 + 2 x 0.03 = 0.16 da página: 320 x 192, sem ampliar
        assert max(tam["pagina-toda"]) <= 900


def test_recortar_nomeia_a_segunda_do_mesmo_padrao_e_pagina_e_aponta_o_que_nao_deu():
    with tempfile.TemporaryDirectory() as d:
        imagem(Path(d) / "captura/web-deck-teste/07.jpg", (90, 90, 90), (800, 450))
        ex = {"imagem": "captura/web-deck-teste/07.jpg", "pagina": 7, "recorte": [0.1, 0.1, 0.5, 0.5], "o_que_mostra": "a"}
        padroes = [{"id_sugerido": "dois-na-mesma", "exemplos": [ex, dict(ex, o_que_mostra="b")]},
                   {"id_sugerido": "sem-imagem", "exemplos": [dict(ex, imagem="captura/nao-existe.jpg")]},
                   {"id_sugerido": "caixa-torta", "exemplos": [dict(ex, recorte=[0.6, 0.1, 0.5, 0.5])]},
                   {"id_sugerido": "caixa-curta", "exemplos": [dict(ex, recorte=[0.1, 0.5])]}]
        r = repertorio.recortar(_analise(d, padroes), Path(d) / "saida", [d])
        assert [f["arquivo"] for f in r["feitos"]] == ["recortes/dois-na-mesma__web-deck-teste-07.jpg", "recortes/dois-na-mesma__web-deck-teste-07-b.jpg"], r["feitos"]
        assert len(r["problemas"]) == 3 and "imagem não encontrada" in r["problemas"][0] and "recorte inválido" in r["problemas"][1], r["problemas"]
        codigo, out, _ = cli("recortar", _analise(d, padroes), "--saida", Path(d) / "saida2", "--base-imagens", d)
        assert codigo == 1 and "FALHA" in out and "2 recorte(s)" in out, out


def test_recortar_cli_funciona_sem_base_explicita_quando_a_imagem_esta_perto_do_json():
    with tempfile.TemporaryDirectory() as d:
        imagem(Path(d) / "captura/web-deck-teste/07.jpg", (90, 90, 90), (800, 450))        # <d>/analise/x.json -> a base é o pai de analise/
        codigo, out, err = cli("recortar", _analise(d), "--saida", Path(d) / "saida", "--json")
        assert codigo == 0, (out, err)
        dados = json.loads(out)
        assert dados["referencia"] == "web-deck-teste" and len(dados["feitos"]) == 1 and dados["problemas"] == [], dados


def test_recortar_nao_grava_fora_da_saida_com_id_ou_referencia_hostil():
    """Revisão de segurança (09/10): id_sugerido "../../../X" gravava X__ref-07.jpg três pastas acima de --saida. O id
    e a referência viram nome de arquivo, então só passam no padrão do índice (a-z, 0-9 e hífen)."""
    with tempfile.TemporaryDirectory() as d:
        imagem(Path(d) / "captura/web-deck-teste/07.jpg", (90, 90, 90), (800, 450))
        ex = {"imagem": "captura/web-deck-teste/07.jpg", "pagina": 7, "recorte": [0.1, 0.1, 0.5, 0.5], "o_que_mostra": "a"}
        saida = Path(d) / "a" / "b" / "saida"
        padroes = [{"id_sugerido": "../../../fugiu", "exemplos": [ex]}, {"id_sugerido": "bom", "exemplos": [ex]}]
        r = repertorio.recortar(_analise(d, padroes), saida, [d])
        antes = {q for q in Path(d).rglob("*.jpg")}
        assert [f["padrao"] for f in r["feitos"]] == ["bom"], r["feitos"]
        assert any("fora do padrão" in m for m in r["problemas"]), r["problemas"]
        assert not any("fugiu" in q.name for q in antes), sorted(map(str, antes))
        hostil = _analise(d, [{"id_sugerido": "bom", "exemplos": [ex]}], ref="ref-segura")
        hostil.write_text(hostil.read_text(encoding="utf-8").replace('"ref-segura"', '"../../ref-fugiu"'), encoding="utf-8")
        try:
            repertorio.recortar(hostil, saida, [d])
            raise AssertionError("referência hostil passou")
        except SystemExit as e:
            assert "fora do padrão" in str(e), e
        assert not any("ref-fugiu" in q.name for q in Path(d).rglob("*.jpg"))


# ---------------------------------------------------------------- folha
@com_repertorio
def test_folha_poe_os_recortes_com_id_legenda_e_rotulo_nao_fazer(rep):
    ind = indice_de(rep); item(ind, "numero-que-sangra")["recortes"].reverse(); gravar_indice(rep, ind)   # no índice o anti vem primeiro
    saida = rep.parent / "folha.png"
    caminho, (w, h) = repertorio.folha(rep, ["numero-que-sangra", "selo-na-margem"], saida)
    im = Image.open(caminho).convert("RGB")
    assert im.size == (w, h) and w > 900 and h > 500, im.size
    cores = {im.getpixel(xy) for xy in [(40 + 10, 56 + 10), (40 + 520 + 14 + 10, 56 + 10)]}
    # o recorte normal (200, 40, 40) e o anti (40, 40, 200) estão na grade (centros dos cartões 1 e 2)
    def tem(cor, tol=14):
        px = im.load()
        return any(all(abs(px[x, y][i] - cor[i]) <= tol for i in range(3)) for x in range(0, w, 7) for y in range(0, h, 7))
    assert tem((200, 40, 40)) and tem((40, 40, 200)), "os recortes não foram colados"
    assert tem((214, 48, 49), 4), "o antiexemplo deveria ter a borda vermelha e o rótulo NÃO FAZER"
    # o rótulo é um retângulo vermelho no canto do cartão do anti (2º cartão: x = 14 + 534, y = 56) com texto branco dentro
    ax, ay = 14 + 520 + 14, 56
    rotulo = [im.getpixel((x, y)) for x in range(ax + 2, ax + 130) for y in range(ay + 2, ay + 25)]
    brancos = sum(1 for c in rotulo if min(c) > 225)
    assert im.getpixel((ax + 3, ay + 13)) == (214, 48, 49) and brancos > 40, (im.getpixel((ax + 3, ay + 13)), brancos)
    assert im.getpixel((ax + 2, ay + 200)) == (214, 48, 49) and im.getpixel((ax + 260, ay + 337)) == (214, 48, 49), "borda vermelha em volta do anti"
    assert im.getpixel((14 + 2, 56 + 200)) != (214, 48, 49), "o cartão normal não tem borda vermelha"
    n0 = [im.getpixel((x, y)) for x in range(14 + 2, 14 + 130) for y in range(56 + 2, 56 + 25)]
    assert sum(1 for c in n0 if min(c) > 225) == 0, "o cartão normal não tem rótulo"
    im2 = Image.open(repertorio.folha(rep, ["fio-que-liga-titulo-e-foto"], rep.parent / "f2.png")[0]).convert("RGB")
    px = im2.load()
    assert not any(all(abs(px[x, y][i] - (214, 48, 49)[i]) <= 4 for i in range(3)) for x in range(0, im2.width, 5) for y in range(0, im2.height, 5)), "sem anti não há vermelho"
    codigo, out, err = cli("folha", "numero-que-sangra", "--saida", rep.parent / "f3.png", "--repertorio", rep)
    assert codigo == 0 and out.startswith("OK") and (rep.parent / "f3.png").is_file(), (out, err)
    codigo, out, err = cli("folha", "padrao-fantasma", "--saida", rep.parent / "f4.png", "--repertorio", rep)
    assert codigo != 0 and "padrão(ões) fora do índice: padrao-fantasma" in (out + err), (out, err)
    print(f"   folha de 2 padrões (3 cartões: normal, anti, sem recorte): {w}x{h}")


# ---------------------------------------------------------------- html
@com_repertorio
def test_html_tem_todos_os_ids_caminhos_relativos_e_nenhuma_dependencia_externa(rep):
    saida = rep / "repertorio.html"
    repertorio.gerar_html(rep, saida)
    h = saida.read_text(encoding="utf-8")
    for p in PADROES:
        assert f'id="padrao-{p["id"]}"' in h and f"#padrao-{p['id']}" in h, p["id"]
        assert p["nome"] in h
    assert 'src="recortes/numero-que-sangra__ref-um-07.jpg"' in h, "caminho relativo ao html"
    assert 'href="recortes/numero-que-sangra__ref-um-07.jpg" target=_blank' in h, "o recorte abre inteiro ao clicar"
    assert "ref-um" in h and "Deck de patrocínio Um" in h and "https://exemplo.test/um" in h
    # índice por tipo de página e por problema
    assert "Por tipo de página" in h and "Por problema" in h and "<summary>publico (1)</summary>" in h and "<summary>ativo_painel (1)</summary>" in h
    assert "página de dados com um número dominante" in h
    # front matter não aparece como texto; as seções e o trecho de composição sim
    assert "tipo_pagina: [" not in h and "densidade: media" not in h
    assert "1. Problema ou efeito" in h and "8. Como construir e conferir" in h and "Trecho de composição" in h and "&quot;porque&quot;" not in h
    assert '"porque": "o número maior que a página vira fundo"' in h
    # antiexemplo separado, sob "Não fazer"
    assert h.count("Não fazer") == 1 and 'class=naofazer' in h and "numero-que-sangra__ref-dois-03.jpg" in h
    # sem rede: nenhum src/href/url() para fora; só o link da referência
    import re as _re
    externos = _re.findall(r'(?:src|href)="(https?://[^"]+)"', h)
    assert externos == ["https://exemplo.test/um"], externos
    assert "@import" not in h and "url(" not in h and "<link" not in h and "cdn" not in h.lower()
    assert 'name=viewport' in h and "max-width:640px" in h and "prefers-color-scheme:dark" in h
    print(f"   html de {len(h) // 1024} KB, sem recurso externo")


@com_repertorio
def test_html_numa_pasta_diferente_usa_caminho_relativo_certo_e_escapa_o_md(rep):
    # um .md com <script> e uma saída em outra pasta (os caminhos têm de continuar certos)
    p = next(p for p in PADROES if p["id"] == "selo-na-margem")
    (rep / "padroes" / "selo-na-margem.md").write_text(md_do_padrao(p) + "\n<script>alert('x')</script>\n\n[ruim](javascript:alert(1))\n", encoding="utf-8")
    saida = rep.parent / "fora" / "pagina.html"
    repertorio.gerar_html(rep, saida)
    h = saida.read_text(encoding="utf-8")
    assert 'src="../repertorio/recortes/objeto-que-entra-na-foto__ref-um-02.jpg"' in h, [l for l in h.split(">") if "recortes/" in l][:2]
    assert "<script>alert" not in h and "&lt;script&gt;alert" in h and 'href="javascript' not in h
    assert h.count("<script>") == 1, "só o script de filtro da própria página"


@com_repertorio
def test_html_sem_saida_grava_ao_lado_do_indice_e_imprime_o_caminho_absoluto(rep):
    codigo, out, err = cli("html", "--repertorio", rep)
    assert codigo == 0 and (rep / "repertorio.html").is_file(), (out, err)
    assert out.strip() == f"OK {(rep / 'repertorio.html').resolve()}", out
    assert 'src="recortes/numero-que-sangra__ref-um-07.jpg"' in (rep / "repertorio.html").read_text(encoding="utf-8")


@com_repertorio
def test_html_cli_e_recorte_ausente_nao_quebra(rep):
    (rep / "recortes" / "fio-que-liga-titulo-e-foto__ref-dois-01.jpg").unlink()
    codigo, out, err = cli("html", "--repertorio", rep, "--saida", rep / "repertorio.html")
    assert codigo == 0 and out.startswith("OK"), (out, err)
    assert "recorte ausente: recortes/fio-que-liga-titulo-e-foto__ref-dois-01.jpg" in (rep / "repertorio.html").read_text(encoding="utf-8")


@com_repertorio
def test_cli_aceita_repertorio_antes_e_depois_do_subcomando(rep):
    """Opção repetida no parser e no subparser: o default do subparser apagava o valor dado antes do subcomando e a
    ferramenta conferia a pasta errada em silêncio."""
    for args in (("--repertorio", rep, "checar"), ("checar", "--repertorio", rep)):
        codigo, out, err = cli(*args)
        assert codigo == 0 and "0 falha(s), 1 aviso(s)" in out, (args, out, err)
    codigo, out, _ = cli("--repertorio", rep, "buscar", "--pagina", "publico")
    assert codigo == 0 and "numero-que-sangra" in out, out
    codigo, out, _ = cli("--repertorio", rep.parent / "nao-existe", "checar")
    assert codigo == 1 and "nao-existe" in out, out        # e a pasta dada é mesmo a usada (a que não existe aparece na mensagem)


@com_repertorio
def test_buscar_folha_e_html_recusam_indice_fora_do_schema_com_mensagem_e_sem_traceback(rep):
    ind = indice_de(rep); del item(ind, "selo-na-margem")["nome"]; gravar_indice(rep, ind)
    for args in (("buscar", "--pagina", "cota"), ("folha", "selo-na-margem", "--saida", rep.parent / "f.png"), ("html", "--saida", rep.parent / "r.html")):
        codigo, out, err = cli(*args, "--repertorio", rep)
        assert codigo != 0 and "fora do schema" in (out + err) and "rode `repertorio.py checar`" in (out + err) and "Traceback" not in err, (args, out, err)
    # o checar continua listando o erro (é ele quem diz tudo o que está errado)
    assert any("'nome' is a required property" in m for m in falhas(repertorio.checar(rep)))
    # o usados não depende da estrutura do índice
    kit = rep.parent / "kit"; kit.mkdir()
    (kit / "mediakit.json").write_text(json.dumps({"composicao": {"capa": {"padroes": ["x"]}}}), encoding="utf-8")
    assert cli("usados", kit, "--repertorio", rep)[0] == 0


# ---------------------------------------------------------------- usados
def test_usados_lista_os_padroes_declarados_no_kit():
    with tempfile.TemporaryDirectory() as d:
        rep = Path(d) / "repertorio"; montar(rep)
        kit = Path(d) / "kit"; kit.mkdir()
        comp = {"_nota": {"padroes": ["ignorado"]}, "capa": {"mensagem": "x", "padroes": ["fio-que-liga-titulo-e-foto"]},
                "ativo": {"padroes": ["objeto-que-entra-na-foto", "numero-que-sangra"]}, "ativo:2": {"padroes": ["objeto-que-entra-na-foto", "padrao-fantasma"]},
                "cota": {"mensagem": "sem padrões"}}
        (kit / "mediakit.json").write_text(json.dumps({"kit": "teste-2027", "composicao": comp}), encoding="utf-8")
        r = repertorio.usados(kit, rep)
        assert r["padroes"] == {"fio-que-liga-titulo-e-foto": ["capa"], "numero-que-sangra": ["ativo"],
                                "objeto-que-entra-na-foto": ["ativo", "ativo:2"], "padrao-fantasma": ["ativo:2"]}, r
        assert r["desconhecidos"] == ["padrao-fantasma"] and r["kit"] == "teste-2027", r
        codigo, out, _ = cli("usados", kit, "--repertorio", rep)
        assert codigo == 0 and "objeto-que-entra-na-foto" in out and "ativo, ativo:2" in out and "padrao-fantasma" in out and "(fora do repertório)" in out, out
        codigo, out, _ = cli("usados", kit, "--repertorio", rep, "--json")
        assert json.loads(out)["padroes"]["numero-que-sangra"] == ["ativo"]
        (kit / "mediakit.json").write_text(json.dumps({"kit": "x"}), encoding="utf-8")
        assert repertorio.usados(kit, rep)["padroes"] == {}
        codigo, out, err = cli("usados", Path(d) / "sem-kit", "--repertorio", rep)
        assert codigo != 0 and "mediakit.json não existe" in (out + err), (out, err)
        (kit / "mediakit.json").write_text("{ quebrado", encoding="utf-8")
        codigo, out, err = cli("usados", kit, "--repertorio", rep)
        assert codigo != 0 and "não é JSON válido" in (out + err), (out, err)


# ---------------------------------------------------------------- captura das galerias (sem rede)
# Os testes usam um navegador de mentira (NavFalso) no lugar do Playwright, imagens sintéticas de blocos de cor sorteados com semente
# fixa (o JPEG preserva e nenhuma outra semente repete) e um disco de mentira; o único que abre o Chromium fala com um servidor local.
def ruido(w, h, semente, bloco=24):
    """Imagem RGB de blocos de cor sorteados: textura que o JPEG preserva, diferente para cada semente."""
    r = np.random.RandomState(semente)
    pequena = r.randint(0, 256, (-(-h // bloco), -(-w // bloco), 3), dtype=np.uint8)
    return Image.fromarray(np.kron(pequena, np.ones((bloco, bloco, 1), dtype=np.uint8))[:h, :w])


@contextlib.contextmanager
def trocar(**kw):
    """Troca constantes de repertorio.py durante o teste e devolve as originais, aconteça o que acontecer."""
    antes = {k: getattr(repertorio, k) for k in kw}
    for k, v in kw.items():
        setattr(repertorio, k, v)
    try:
        yield
    finally:
        for k, v in antes.items():
            setattr(repertorio, k, v)


@contextlib.contextmanager
def disco(livre_gb=50):
    """shutil.disk_usage de mentira: o resultado dos testes não depende de quanto espaço esta máquina tem agora."""
    original = shutil.disk_usage
    shutil.disk_usage = lambda _p: types.SimpleNamespace(total=500 * 1024 ** 3, used=0, free=int(livre_gb * 1024 ** 3))
    try:
        yield
    finally:
        shutil.disk_usage = original


class NavFalso:
    """Navegador de mentira. roteiro = {ref: [passo, ...]}; o passo da tentativa k (o último se acabarem) é uma lista de
    (url, imagem) (a página tem esses módulos) ou um dict com o que a página devolveu sem módulos (status_http, titulo, texto)."""
    def __init__(self, roteiro):
        self.roteiro, self.vezes, self.imagens = roteiro, {}, {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def coletar(self, f):
        ref = f["id"]
        k = self.vezes.get(ref, 0); self.vezes[ref] = k + 1
        passos = self.roteiro[ref]; passo = passos[min(k, len(passos) - 1)]
        if isinstance(passo, dict):
            return dict({"status_http": 200, "titulo": "", "texto": "", "canonica": None, "urls": []}, **passo)
        for url, im in passo:
            self.imagens[url] = im
        return {"status_http": 200, "titulo": "t", "texto": "", "canonica": "https://exemplo.test/c/" + ref, "urls": [u for u, _ in passo]}

    def baixar(self, variantes):
        for v in variantes:
            if v in self.imagens:
                return self.imagens[v], v, [200]
        return None, None, [404]


def fonte(ref, **kw):
    return dict({"id": ref, "url": "https://exemplo.test/" + ref, "tipo": "behance", "camada": "profunda", "largura": 1400}, **kw)


def tres_paginas(semente=1, n=3, w=1400, h=788):
    return [(f"https://exemplo.test/m{semente}-{k}.jpg", ruido(w, h, semente * 100 + k)) for k in range(n)]


def sem_espera(_s):
    return None


def test_extrair_modulos_do_html_com_barra_escapada_e_srcset():
    H = "https://mir-s3-cdn-cf.behance.net/project_modules/"
    json_em_html = ('{"a":"https:\\/\\/mir-s3-cdn-cf.behance.net\\/project_modules\\/max_1200\\/aaa111.jpg",'
                    '"b":"https:\\/\\/mir-s3-cdn-cf.behance.net\\/project_modules\\/fs\\/bbb222.png",'
                    '"c":"https:\\u002F\\u002Fmir-s3-cdn-cf.behance.net\\u002Fproject_modules\\u002F1400\\u002Fggg777.jpg"}')
    html = (f"<script>{json_em_html}</script><img src=\"{H}disp/ccc333.jpg\" srcset=\"{H}1400/ddd444.jpg 1400w, {H}800/ddd444.jpg 800w\">"
            '<img src="https://mir-s3-cdn-cf.behance.net/projects/404/relacionado.jpg"><img src="https://mir-s3-cdn-cf.behance.net/user/115/avatar.jpg">')
    dom = [f"{H}1400/aaa111.jpg", f"{H}source/eee555.webp?x=1", "https://exemplo.test/outra.jpg", "", None]
    r = repertorio.extrair_modulos(html, dom)
    assert [repertorio.chave_modulo(u) for u in r] == ["aaa111", "bbb222", "ggg777", "ccc333", "ddd444", "eee555"], r
    assert r[0] == H + "max_1200/aaa111.jpg", "fica a primeira ocorrência (a do HTML), não a do DOM"
    assert r[1] == H + "fs/bbb222.png" and r[2] == H + "1400/ggg777.jpg", r
    assert r[5] == H + "source/eee555.webp", "o ?x=1 do DOM não entra na URL"
    assert all("\\" not in u for u in r), r
    assert repertorio.extrair_modulos("", []) == [] and repertorio.extrair_modulos(None, None) == []
    # tamanhos tentados na ordem do pedido: 1400, max_1200, o original (sem repetir)
    assert repertorio.variantes_do_modulo(H + "disp/ccc333.jpg") == [H + "1400/ccc333.jpg", H + "max_1200/ccc333.jpg", H + "disp/ccc333.jpg"]
    assert repertorio.variantes_do_modulo(H + "1400/ccc333.jpg") == [H + "1400/ccc333.jpg", H + "max_1200/ccc333.jpg"]
    assert repertorio.variantes_do_modulo("https://exemplo.test/x.jpg") == ["https://exemplo.test/x.jpg"]


def test_fatiar_modulo_alto_em_tres_slides_separados_por_faixa_branca():
    alturas = [562, 562, 562]
    im = Image.new("RGB", (1000, 20 + sum(alturas) + 2 * 120 + 20), (255, 255, 255))
    y, topos = 20, []
    for k, h in enumerate(alturas):
        im.paste(ruido(1000, h, 10 + k), (0, y)); topos.append(y); y += h + 120
    assert im.height > repertorio.ALTO_REL * im.width, "o módulo de teste precisa contar como alto"
    partes = repertorio.fatiar_modulo(im)
    assert len(partes) == 3, [(p.size, f) for p, f in partes]
    for k, (parte, fatia) in enumerate(partes):
        assert parte.size == (1000, 562) and fatia["modo"] == "faixa" and fatia["i"] == k + 1 and fatia["de"] == 3, (parte.size, fatia)
        assert fatia["y0"] == topos[k] and fatia["y1"] == topos[k] + 562, fatia
        assert np.array_equal(np.asarray(parte), np.asarray(ruido(1000, 562, 10 + k))), "a fatia é o slide, sem a faixa"
    # módulo normal volta inteiro, sem fatia
    normal = ruido(1400, 788, 3)
    assert repertorio.fatiar_modulo(normal) == [(normal, None)]
    # módulo alto sem nada de cor uniforme não pode virar zero página
    assert len(repertorio.fatiar_modulo(ruido(1000, 2000, 4))) > 1


def test_fatiar_modulo_alto_sem_faixa_corta_em_16x9_com_sobreposicao():
    im = ruido(1000, 2714, 7)                                  # 2714 = 562 + 4 x 538: o limite em que a sobreposição fica rente a 4%
    partes = repertorio.fatiar_modulo(im)
    alt = 562
    assert all(p.size == (1000, alt) and f["modo"] == "16:9" for p, f in partes), [(p.size, f) for p, f in partes]
    assert partes[0][1]["y0"] == 0 and partes[-1][1]["y1"] == 2714, "cobre a imagem de ponta a ponta"
    sobras = [a[1]["y1"] - b[1]["y0"] for a, b in zip(partes, partes[1:])]
    assert min(sobras) >= 0.04 * alt - 0.5, f"sobreposição menor que 4%: {sobras}"
    assert max(sobras) <= 0.06 * alt, f"sobreposição exagerada: {sobras}"
    for (pa, fa), (pb, fb) in zip(partes, partes[1:]):         # a sobreposição é o mesmo pedaço de imagem nas duas fatias
        s = fa["y1"] - fb["y0"]
        assert np.array_equal(np.asarray(pa)[alt - s:], np.asarray(pb)[:s])
    assert np.array_equal(np.asarray(partes[2][0]), np.asarray(im.crop((0, partes[2][1]["y0"], 1000, partes[2][1]["y1"]))))
    # um tamanho em que sem sobreposição caberiam menos janelas (n = 5 contra 6): as vizinhas ainda têm de dividir 4%
    janelas = repertorio.janelas_16x9(0, 2762, 1000)
    assert len(janelas) == 6 and all(b - a == alt for a, b in janelas) and janelas[0][0] == 0 and janelas[-1][1] == 2762, janelas
    assert min(a[1] - b[0] for a, b in zip(janelas, janelas[1:])) >= 0.04 * alt - 0.5, janelas
    # janelas: parte que cabe numa janela volta inteira
    assert repertorio.janelas_16x9(100, 500, 1000) == [(100, 500)]


def test_manifesto_marca_suspeita_com_menos_de_3_imagens_e_ok_com_3():
    with tempfile.TemporaryDirectory() as d, disco():
        rep = Path(d)
        nav = NavFalso({"duas": [tres_paginas(1, 2)], "tres": [tres_paginas(2, 3)], "estreitas": [tres_paginas(3, 3, w=920, h=520)], "nenhuma": [[]]})
        for ref, status, n in (("duas", "suspeita", 2), ("tres", "ok", 3), ("estreitas", "suspeita", 3), ("nenhuma", "vazia", 0)):
            man = repertorio.capturar_fonte(rep, fonte(ref), nav, dormir=sem_espera, espera_retry=0)
            gravado = json.loads((rep / "fontes" / f"{ref}.json").read_text(encoding="utf-8"))
            assert man["status"] == gravado["status"] == status, (ref, man["status"], gravado["status"])
            assert [p["n"] for p in gravado["paginas"]] == list(range(1, n + 1)), gravado["paginas"]
            for chave in ("url", "canonica", "capturada_em", "status", "paginas"):
                assert chave in gravado, (ref, chave)
            for p in gravado["paginas"]:
                arq = rep / "capturas" / ref / f"{p['n']:02d}.jpg"
                assert arq.is_file() and hashlib.sha256(arq.read_bytes()).hexdigest() == p["sha256"], p
                assert (p["w"], p["h"]) == Image.open(arq).size and p["kb"] == max(1, arq.stat().st_size // 1024) and p["fatia"] is None, p
                mini = rep / "capturas" / ref / "_mini" / f"{p['n']:02d}.jpg"
                assert mini.is_file() and Image.open(mini).width == min(800, p["w"]), "a miniatura tem 800 px (ou a largura da página, se menor)"
        assert (rep / "capturas" / "tres" / "_folha-1.jpg").is_file() and not (rep / "capturas" / "nenhuma").exists()
        assert json.loads((rep / "fontes" / "tres.json").read_text(encoding="utf-8"))["modulos"] == {"achados": 3, "baixados": 3, "descartados": 0}
        # módulo que a página citou e o servidor não entregou aparece como achado e não baixado (é como se sabe que a galeria ficou incompleta)
        nav_falho = NavFalso({"furada": [tres_paginas(9, 4)]}); nav_falho.imagens = {}
        original_baixar = nav_falho.baixar
        nav_falho.baixar = lambda v: (None, None, [404]) if v[0].endswith("-2.jpg") else original_baixar(v)
        man = repertorio.capturar_fonte(rep, fonte("furada"), nav_falho, dormir=sem_espera, espera_retry=0)
        assert man["modulos"] == {"achados": 4, "baixados": 3, "descartados": 0} and len(man["paginas"]) == 3, man["modulos"]
        assert json.loads((rep / "fontes" / "tres.json").read_text(encoding="utf-8"))["canonica"] == "https://exemplo.test/c/tres"
        # a classificação em si
        assert repertorio.classificar_status([]) == "vazia"
        assert repertorio.classificar_status([{"w": 1400}] * 2) == "suspeita" and repertorio.classificar_status([{"w": 1400}] * 3) == "ok"
        assert repertorio.classificar_status([{"w": 800}] * 5, [999] * 5) == "suspeita" and repertorio.classificar_status([{"w": 800}] * 5, [1000] * 5) == "ok"


def test_filtro_descarta_largura_menor_que_900_e_faixa_fina():
    for (w, h), esperado in {(899, 700): False, (900, 700): True, (900, 180): True, (900, 179): False, (1400, 279): False, (1400, 280): True}.items():
        assert repertorio.aceitar_pagina(w, h) is esperado, (w, h)
    modulos = [("a", ruido(800, 600, 1)), ("b", ruido(1400, 250, 2)), ("c", ruido(1400, 788, 3)), ("d", ruido(900, 600, 4)), ("e", ruido(2100, 1181, 5))]
    paginas, blobs, larguras, descartados = repertorio.montar_paginas(modulos, 1400)
    assert descartados == 2 and [p["modulo_url"] for p in paginas] == ["c", "d", "e"], paginas
    assert [p["w"] for p in paginas] == [1400, 900, 1400] and paginas[2]["h"] == 787, "acima da largura pedida reduz, abaixo não amplia"
    assert larguras == [1400, 900, 2100] and len(blobs) == 3
    paginas, *_ = repertorio.montar_paginas(modulos[2:], 1000)
    assert [p["w"] for p in paginas] == [1000, 900, 1000], "--largura vale"


def _repertorio_de_conferencia(rep, paginas_v2, recortes, ficha=None):
    """Captura sintética de `ref-x` com as páginas dadas e um índice (sem schema) cujos recortes citam `recortes` = [(arquivo, pagina_v1, imagem)]."""
    nav = NavFalso({"ref-x": [[(f"https://exemplo.test/p{k}.jpg", im) for k, im in enumerate(paginas_v2, 1)]]})
    repertorio.capturar_fonte(rep, fonte("ref-x"), nav, dormir=sem_espera, espera_retry=0)
    itens = []
    for arq, pag, im in recortes:
        (rep / arq).parent.mkdir(parents=True, exist_ok=True)
        im.save(rep / arq, "JPEG", quality=80)
        itens.append({"arquivo": arq, "referencia": "ref-x", "pagina": pag, "legenda": "x"})
    (rep / "indice.json").write_text(json.dumps({"versao": 1, "padroes": [{"id": "p", "nome": "p", "recortes": itens}], "referencias": []}), encoding="utf-8")
    if ficha:
        (rep / "referencias").mkdir(exist_ok=True)
        (rep / "referencias" / "ref-x.md").write_text(ficha, encoding="utf-8")


def test_conferir_captura_acha_a_pagina_certa_e_grava_v1_para_v2():
    with tempfile.TemporaryDirectory() as d, disco():
        rep = Path(d)
        paginas = [ruido(1400, 788, 20 + k) for k in range(6)]
        grande = paginas[5].crop((50, 20, 1350, 760)).resize((900, 512), Image.LANCZOS)      # recorte que passou de 900 px e foi reduzido
        intruso = ruido(1400, 788, 99).crop((100, 100, 900, 600))                              # imagem que não existe em nenhuma página
        _repertorio_de_conferencia(rep, paginas, [
            ("recortes/a.jpg", 1, paginas[0].crop((200, 100, 1000, 600))),    # v1 e v2 iguais
            ("recortes/b.jpg", 2, paginas[2].crop((200, 100, 1000, 600))),    # a v1 chamava de 2 o que hoje é a 3
            ("recortes/c.jpg", 4, grande),                                    # hoje é a 6, reduzido
            ("recortes/d.jpg", 9, paginas[4].crop((100, 50, 900, 550))),      # a v1 tinha mais páginas: hoje é a 5, longe da 9
            ("recortes/e.jpg", 3, intruso)],
            ficha="# x\n\n- Imagens olhadas: 4 de 4, uma a uma.\n")
        r = repertorio.conferir(rep, "ref-x")
        por = {Path(l["arquivo"]).stem: l for l in r["linhas"]}
        assert por["a"]["situacao"] == "igual" and por["a"]["v2"] == 1 and por["a"]["nota_v1"] > 0.9, por["a"]
        assert por["b"]["situacao"] == "mudou de página" and por["b"]["v2"] == 3 and por["b"]["nota_v2"] > 0.9, por["b"]
        assert por["c"]["v2"] == 6 and por["c"]["nota_v2"] >= repertorio.NOTA_MIN, por["c"]
        assert por["d"]["v2"] == 5 and por["d"]["nota_v1"] < 0, por["d"]
        assert por["e"]["situacao"] == "não achado" and por["e"]["nota_v2"] < repertorio.NOTA_MIN, por["e"]
        assert r["v1_para_v2"] == {"2": 3, "4": 6, "9": 5} and r["v1_nao_achados"] == [3], r
        assert r["ficha"] == {"olhadas": 4, "total": 4} and r["v2"] == 6 and r["maior_pagina_recorte"] == 9
        man = json.loads((rep / "fontes" / "ref-x.json").read_text(encoding="utf-8"))          # e ficou no manifesto
        assert man["v1_para_v2"] == {"2": 3, "4": 6, "9": 5} and man["v1_nao_achados"] == [3] and man["v1_contagem"] == {"ficha": 4, "maior_pagina_de_recorte": 9, "v2": 6}
        assert man["status"] == "ok" and len(man["paginas"]) == 6, "o resto do manifesto não se perde"
        codigo, out, err = cli("conferir-captura", "ref-x", "--repertorio", rep)             # e a tabela do comando
        assert codigo == 0 and "MAIS 2" in out and "mudou de página" in out and "não achado" in out and "'2': 3" in out, (out, err)
        codigo, out, _ = cli("conferir-captura", "ref-nao-capturada", "--repertorio", rep)
        assert codigo == 1 and "sem manifesto" in out, out


def test_conferir_captura_prefere_a_pagina_mais_perto_quando_o_slide_se_repete():
    with tempfile.TemporaryDirectory() as d, disco():
        rep = Path(d)
        repetido = ruido(1400, 788, 30)
        paginas = [repetido, ruido(1400, 788, 31), ruido(1400, 788, 32), ruido(1400, 788, 33), repetido, ruido(1400, 788, 34)]
        _repertorio_de_conferencia(rep, paginas, [("recortes/r.jpg", 6, repetido.crop((200, 100, 1000, 600)))])
        r = repertorio.conferir(rep, "ref-x")
        assert r["linhas"][0]["v2"] == 5 and r["v1_para_v2"] == {"6": 5}, "a v1 citava a 6; entre a 1 e a 5 vale a 5, que está a 1 página de distância"


def test_png_com_transparencia_vira_fundo_branco_e_nao_preto():
    im = Image.new("RGBA", (1000, 600), (0, 0, 0, 0))
    ImageDraw.Draw(im).rectangle([100, 100, 400, 400], fill=(200, 30, 30, 255))
    rgb = repertorio._para_rgb(im)
    assert rgb.mode == "RGB" and rgb.getpixel((10, 10)) == (255, 255, 255) and rgb.getpixel((200, 200)) == (200, 30, 30)
    paleta = Image.new("P", (10, 10)); paleta.info["transparency"] = 0
    assert repertorio._para_rgb(paleta).mode == "RGB"
    assert repertorio._para_rgb(Image.new("RGB", (4, 4), (1, 2, 3))).getpixel((0, 0)) == (1, 2, 3)


def test_conferir_captura_le_a_contagem_da_ficha():
    with tempfile.TemporaryDirectory() as d:
        rep = Path(d); (rep / "referencias").mkdir()
        for texto, esperado in (("- Imagens olhadas: 23 de 23, uma a uma.", {"olhadas": 23, "total": 23}), ("- **Imagens olhadas:** 21 de 21, uma a uma.", {"olhadas": 21, "total": 21}),
                                ("- Imagens olhadas: 6 de 7.", {"olhadas": 6, "total": 7}), ("- Imagens vistas: 1 (01).", {"olhadas": 1, "total": 1}),
                                ("- Tipo: deck de patrocínio de 23 páginas.", {"olhadas": 23, "total": 23}), ("sem número nenhum", None)):
            (rep / "referencias" / "r.md").write_text(texto, encoding="utf-8")
            assert repertorio.contagem_da_ficha(rep, "r") == esperado, (texto, repertorio.contagem_da_ficha(rep, "r"))
        assert repertorio.contagem_da_ficha(rep, "nao-existe") is None


def test_captura_so_sobrescreve_arquivo_do_proprio_manifesto():
    with tempfile.TemporaryDirectory() as d, disco():
        rep = Path(d); pasta = rep / "capturas" / "ref-a"
        pasta.mkdir(parents=True); (pasta / "01.jpg").write_bytes(b"arquivo que nao e meu")
        nav = NavFalso({"ref-a": [tres_paginas(1, 5), tres_paginas(1, 5), tres_paginas(2, 3)]})
        try:
            repertorio.capturar_fonte(rep, fonte("ref-a"), nav, dormir=sem_espera)
            raise AssertionError("devia recusar: 01.jpg existe e nenhum manifesto o lista")
        except repertorio.ErroCaptura as e:
            assert "01.jpg" in str(e) and "não sobrescrevo" in str(e), e
        assert (pasta / "01.jpg").read_bytes() == b"arquivo que nao e meu" and not (rep / "fontes" / "ref-a.json").exists()
        assert sorted(p.name for p in pasta.iterdir()) == ["01.jpg"], "não gravou nenhum byte antes de recusar"
        (pasta / "01.jpg").unlink()
        man1 = repertorio.capturar_fonte(rep, fonte("ref-a"), nav, dormir=sem_espera)               # 5 páginas, sem arquivo estranho: grava
        assert len(man1["paginas"]) == 5
        (pasta / "notas.txt").write_text("do Ugo", encoding="utf-8")
        antes = {p["n"]: p["sha256"] for p in man1["paginas"]}
        man2 = repertorio.capturar_fonte(rep, fonte("ref-a"), nav, dormir=sem_espera)               # refaz com 3 páginas: troca as 3, tira as 2 que sobraram
        assert len(man2["paginas"]) == 3 and all(man2["paginas"][k]["sha256"] != antes[k + 1] for k in range(3)), "sobrescreveu o que era do manifesto"
        assert not (pasta / "04.jpg").exists() and not (pasta / "_mini" / "05.jpg").exists(), "página que sobrou da captura anterior sai"
        assert (pasta / "notas.txt").read_text(encoding="utf-8") == "do Ugo", "o que não é do manifesto fica onde está"
        assert sorted(p.name for p in pasta.iterdir()) == ["01.jpg", "02.jpg", "03.jpg", "_folha-1.jpg", "_mini", "notas.txt"]


def test_captura_pula_ok_e_refaz_com_forcar_e_refaz_suspeita_sozinha():
    with tempfile.TemporaryDirectory() as d, disco():
        rep = Path(d)
        nav = NavFalso({"boa": [tres_paginas(1, 4)], "curta": [tres_paginas(2, 2), tres_paginas(3, 4)]})
        fs = [fonte("boa"), fonte("curta")]
        res, cod = repertorio.executar_captura(rep, fs, nav, pausa=0, dormir=sem_espera)
        assert cod == 0 and [r["status"] for r in res] == ["ok", "suspeita"] and nav.vezes == {"boa": 1, "curta": 1}
        res, cod = repertorio.executar_captura(rep, fs, nav, pausa=0, dormir=sem_espera)         # boa: ok, pula; curta: suspeita, tenta de novo
        assert [r["status"] for r in res] == ["pulada", "ok"] and nav.vezes == {"boa": 1, "curta": 2}, (res, nav.vezes)
        res, cod = repertorio.executar_captura(rep, fs, nav, pausa=0, forcar=True, dormir=sem_espera)
        assert [r["status"] for r in res] == ["ok", "ok"] and nav.vezes == {"boa": 2, "curta": 3}, (res, nav.vezes)
        # captura nova sem página não apaga o que já está bom
        nav2 = NavFalso({"boa": [{"status_http": 403, "titulo": "Access denied"}]})
        antes = (rep / "fontes" / "boa.json").read_text(encoding="utf-8")
        res, cod = repertorio.executar_captura(rep, [fonte("boa")], nav2, pausa=0, forcar=True, dormir=sem_espera, espera_retry=0)
        assert res[0]["status"] == "bloqueada" and (rep / "fontes" / "boa.json").read_text(encoding="utf-8") == antes
        assert len(list((rep / "capturas" / "boa").glob("[0-9]*.jpg"))) == 4, "as páginas anteriores continuam"


def test_captura_nao_tenta_regua_nem_fora_e_nao_chama_o_navegador():
    with tempfile.TemporaryDirectory() as d, disco():
        nav = NavFalso({})
        fs = [fonte("kit-regua", tipo="regua", camada="regua", url=None, pasta="regua/paginas"), fonte("excluida", camada="fora", motivo="peça repetida")]
        res, cod = repertorio.executar_captura(Path(d), fs, nav, pausa=0, dormir=sem_espera)
        assert cod == 0 and [r["status"] for r in res] == ["sem-captura", "sem-captura"] and nav.vezes == {}, (res, nav.vezes)
        assert not (Path(d) / "capturas").exists() and not (Path(d) / "fontes").exists()


def test_tentativa_nova_depois_de_30_segundos_e_pausa_entre_galerias():
    with tempfile.TemporaryDirectory() as d, disco():
        esperas = []
        nav = NavFalso({"a": [{"status_http": 403}, tres_paginas(1, 3)], "b": [tres_paginas(2, 3)]})
        res, cod = repertorio.executar_captura(Path(d), [fonte("a"), fonte("b")], nav, pausa=4, dormir=esperas.append)
        assert cod == 0 and [r["status"] for r in res] == ["ok", "ok"] and nav.vezes == {"a": 2, "b": 1}, (res, nav.vezes)
        assert esperas == [30, 4], f"30 s antes da segunda tentativa de a e 4 s entre a e b: {esperas}"
        man = json.loads((Path(d) / "fontes" / "a.json").read_text(encoding="utf-8"))
        assert man["tentativas"] == 2 and man["status"] == "ok"


def test_disjuntor_para_no_terceiro_bloqueio_seguido_com_codigo_3():
    with tempfile.TemporaryDirectory() as d, disco():
        rep = Path(d); esperas = []
        nav = NavFalso({"r1": [tres_paginas(1, 3)], "r2": [{"status_http": 403, "titulo": "Forbidden"}], "r3": [{"status_http": 200, "titulo": "Projeto", "texto": "sem nada"}],
                        "r4": [{"status_http": 200, "titulo": "Just a moment...", "texto": "Verify you are human"}], "r5": [tres_paginas(5, 3)]})
        res, cod = repertorio.executar_captura(rep, [fonte(f"r{k}") for k in range(1, 6)], nav, pausa=0, dormir=esperas.append)
        assert cod == 3, (cod, res)
        assert [(r["ref"], r["status"]) for r in res] == [("r1", "ok"), ("r2", "bloqueada"), ("r3", "vazia"), ("r4", "bloqueada")], res
        assert "r5" not in nav.vezes, "depois do disjuntor nenhuma galeria é aberta"
        assert nav.vezes == {"r1": 1, "r2": 2, "r3": 2, "r4": 2} and esperas == [30, 30, 30], (nav.vezes, esperas)
        assert not (rep / "capturas" / "r2").exists(), "bloqueada não grava página"
        assert json.loads((rep / "fontes" / "r2.json").read_text(encoding="utf-8"))["status"] == "bloqueada"
        assert json.loads((rep / "fontes" / "r3.json").read_text(encoding="utf-8"))["status"] == "vazia"
        # com um ok no meio a contagem recomeça e a captura inteira roda
        nav = NavFalso({"s1": [{"status_http": 403}], "s2": [{"status_http": 403}], "s3": [tres_paginas(7, 3)], "s4": [{"status_http": 403}], "s5": [{"status_http": 403}], "s6": [tres_paginas(8, 3)]})
        res, cod = repertorio.executar_captura(Path(d) / "outra", [fonte(f"s{k}") for k in range(1, 7)], nav, pausa=0, dormir=sem_espera, espera_retry=0)
        assert cod == 0 and len(res) == 6, (cod, res)
    # o mesmo, pelo comando: a saída do processo é 3
    with tempfile.TemporaryDirectory() as d, disco():
        rep = Path(d); (rep / "fontes.json").write_text(json.dumps({"fontes": [fonte(f"q{k}") for k in range(1, 5)]}), encoding="utf-8")
        nav = NavFalso({f"q{k}": [{"status_http": 403}] for k in range(1, 5)})
        original = repertorio.Navegador
        with trocar(Navegador=lambda: nav, ESPERA_RETRY=0):
            a = argparse.Namespace(ref=[], camada=["profunda"], largura=None, pausa=0, forcar=False, listar=False)
            assert repertorio.cmd_capturar(rep, a) == 3 and "q4" not in nav.vezes
        assert repertorio.Navegador is original


def test_disjuntor_so_conta_pagina_sem_modulos_no_behance_mas_sempre_conta_bloqueio():
    with tempfile.TemporaryDirectory() as d, disco():
        vazio = {"status_http": 200, "titulo": "Artigo", "texto": "sem imagem grande"}
        nav = NavFalso({f"w{k}": [vazio] for k in range(1, 6)})
        res, cod = repertorio.executar_captura(Path(d) / "a", [fonte(f"w{k}", tipo="web") for k in range(1, 6)], nav, pausa=0, dormir=sem_espera, espera_retry=0)
        assert cod == 0 and [r["status"] for r in res] == ["vazia"] * 5, "site sem imagem é vazia, não bloqueio: a captura segue até o fim"
        nav = NavFalso({f"w{k}": [{"status_http": 403}] for k in range(1, 6)})
        res, cod = repertorio.executar_captura(Path(d) / "b", [fonte(f"w{k}", tipo="web") for k in range(1, 6)], nav, pausa=0, dormir=sem_espera, espera_retry=0)
        assert cod == 3 and len(res) == 3, "403 num site comum conta"
        nav = NavFalso({f"b{k}": [vazio] for k in range(1, 6)})
        res, cod = repertorio.executar_captura(Path(d) / "c", [fonte(f"b{k}") for k in range(1, 6)], nav, pausa=0, dormir=sem_espera, espera_retry=0)
        assert cod == 3 and len(res) == 3, "no Behance, página sem módulos conta"
        assert repertorio.conta_como_bloqueio("bloqueada", {"tipo": "pdf"}) and not repertorio.conta_como_bloqueio("vazia", {"tipo": "pdf"})
        assert not repertorio.conta_como_bloqueio("suspeita", {"tipo": "behance"}) and not repertorio.conta_como_bloqueio("ok", {"tipo": "behance"})


def test_captura_recusa_disco_com_menos_de_1_8_gb_e_para_se_capturas_passar_de_900_mb():
    with tempfile.TemporaryDirectory() as d:
        rep = Path(d); (rep / "fontes.json").write_text(json.dumps({"fontes": [fonte("a"), fonte("b")]}), encoding="utf-8")
        nav = NavFalso({"a": [tres_paginas(1, 3)], "b": [tres_paginas(2, 3)]})
        a = argparse.Namespace(ref=["a"], camada=[], largura=None, pausa=0, forcar=False, listar=False)
        with disco(1.7), trocar(Navegador=lambda: nav):
            assert repertorio.cmd_capturar(rep, a) == 4 and nav.vezes == {}, "recusa antes de abrir qualquer galeria"
        with disco(1.9), trocar(Navegador=lambda: nav):
            assert repertorio.cmd_capturar(rep, a) == 0 and nav.vezes == {"a": 1}
        # capturas/ acima do teto: termina a galeria em andamento e para antes da seguinte
        with disco(), trocar(CAPTURAS_MAX_MB=0.01):
            nav = NavFalso({"c": [tres_paginas(3, 3)], "d": [tres_paginas(4, 3)]})
            res, cod = repertorio.executar_captura(Path(d) / "x", [fonte("c"), fonte("d")], nav, pausa=0, dormir=sem_espera)
            assert cod == 4 and [r["ref"] for r in res] == ["c"] and "d" not in nav.vezes, (cod, res)
        with disco():
            try:
                with trocar(CAPTURAS_MAX_MB=0.01):
                    repertorio.checar_limites(Path(d) / "x")
                raise AssertionError("devia passar do limite")
            except repertorio.LimiteAtingido as e:
                assert "capturas/" in str(e) and "MB" in str(e)
            repertorio.checar_limites(Path(d) / "x")           # com o teto de 900 MB o mesmo conteúdo passa


def test_limites_padrao_sao_1_8_gb_livres_e_900_mb_de_capturas():
    assert repertorio.DISCO_MIN_GB == 1.8 and repertorio.CAPTURAS_MAX_MB == 900
    with tempfile.TemporaryDirectory() as d:
        for livre, mb, passa in ((1.79, 0, False), (1.81, 0, True), (50, 899, True), (50, 901, False)):
            with disco(livre), trocar(tamanho_dir=lambda _p, mb=mb: int(mb * 1024 ** 2)):
                try:
                    repertorio.checar_limites(Path(d))
                    assert passa, (livre, mb, "devia recusar")
                except repertorio.LimiteAtingido:
                    assert not passa, (livre, mb, "devia passar")


def test_pagina_bloqueada_so_olha_codigo_titulo_e_comeco_do_texto():
    pb = repertorio.pagina_bloqueada
    assert pb(403) and pb(429) and pb(503) and pb(401)
    assert pb(200, "Just a moment...", "") and pb(200, "Behance", "Please complete the CAPTCHA to continue") and pb(200, "", "Verifique que você é humano")
    assert not pb(200, "Proposta de Patrocínio | Behance", "Projeto sobre corridas de rua") and not pb(404, "Not found", "") and not pb(None, None, None)
    assert not pb(200, "Projeto", "texto normal " * 200 + " captcha"), "captcha só no fim de um texto longo não é bloqueio"


def test_folha_de_contato_tem_5_colunas_20_por_folha_e_altura_cortada():
    with tempfile.TemporaryDirectory() as d, disco():
        rep = Path(d)
        mods = [(f"https://exemplo.test/f{k}.jpg", ruido(1400, 788, 40 + k)) for k in range(1, 22)]
        mods[1] = ("https://exemplo.test/alta.jpg", ruido(1400, 2520, 77))          # 1,8 x a largura: página inteira, que a folha corta em 1,6 x
        nav = NavFalso({"ref-f": [mods]})
        man = repertorio.capturar_fonte(rep, fonte("ref-f"), nav, dormir=sem_espera)
        assert len(man["paginas"]) == 21 and man["paginas"][1]["fatia"] is None and man["paginas"][1]["h"] == 2520
        pasta = rep / "capturas" / "ref-f"
        f1, f2 = Image.open(pasta / "_folha-1.jpg"), Image.open(pasta / "_folha-2.jpg")
        assert f1.size[0] == f2.size[0] == 5 * (420 + 8) + 8, (f1.size, f2.size)
        # 4 linhas de 5; a primeira linha tem a página alta (cortada em 672 = 1,6 x 420), as outras 236 (16:9 em 420)
        assert f1.size[1] == (38 + 672 + 8) + 3 * (38 + 236 + 8) + 8, f1.size           # cada miniatura leva uma faixa de 38 px com o número
        assert f2.size[1] == 38 + 236 + 2 * 8, f2.size
        r, g, b = np.asarray(f1.convert("RGB"))[8 + 3:8 + 36, 8 + 7:8 + 47].transpose(2, 0, 1).astype(int)
        assert ((r > 200) & (g < 160) & (b < 160)).sum() > 30, "o número da página aparece em vermelho sobre fundo preto no canto da miniatura"
        assert (np.asarray(f1.convert("RGB"))[8 + 2, 8 + 2] < 40).all(), "fundo escuro atrás do número"
        assert np.abs(np.asarray(f1.convert("RGB"))[8 + 38 + 2, 8 + 2].astype(int) - np.asarray(mods[0][1])[0, 0].astype(int)).max() < 30, "o número não cobre a página"
        # folha-contato regera: apaga as folhas, o comando as devolve; apaga uma página e ele recusa com a lista do que falta
        for f in pasta.glob("_folha-*.jpg"):
            f.unlink()
        codigo, out, err = cli("folha-contato", "ref-f", "--repertorio", rep)
        assert codigo == 0 and "2 folha(s)" in out and (pasta / "_folha-1.jpg").is_file() and (pasta / "_folha-2.jpg").is_file(), (out, err)
        (pasta / "07.jpg").unlink()
        codigo, out, err = cli("folha-contato", "ref-f", "--repertorio", rep)
        assert codigo == 1 and "faltam páginas" in out and "07" in out, (out, err)
        codigo, out, err = cli("folha-contato", "ref-sem-manifesto", "--repertorio", rep)
        assert codigo == 1 and "sem manifesto" in out, (out, err)


def test_folha_de_contato_da_regua_aponta_para_regua_paginas_sem_copiar_nem_mexer():
    with tempfile.TemporaryDirectory() as d:
        raiz = Path(d); rep = raiz / "repertorio"; rep.mkdir(); pag = raiz / "regua" / "paginas"; pag.mkdir(parents=True)
        for k in list(range(1, 23)):
            ruido(1280, 720, 500 + k).save(pag / f"kit-regua-{k:02d}.jpg", quality=85)
        ruido(1280, 720, 1).save(pag / "kit-regua-extra.jpg"); ruido(1280, 720, 2).save(pag / "outro-kit-01.jpg"); ruido(1280, 720, 3).save(pag / "kit-regua-2-01.jpg")
        (rep / "fontes.json").write_text(json.dumps({"fontes": [fonte("kit-regua", tipo="regua", camada="regua", url=None, pasta="regua/paginas"),
                                                                 fonte("vazio", tipo="regua", camada="regua", url=None, pasta="regua/paginas"),
                                                                 fonte("fuga", tipo="regua", camada="regua", url=None, pasta="../fora")]}), encoding="utf-8")
        antes = {a.name: hashlib.sha256(a.read_bytes()).hexdigest() for a in pag.iterdir()}
        codigo, out, err = cli("folha-contato", "kit-regua", "--repertorio", rep)
        assert codigo == 0 and "2 folha(s)" in out, (out, err)
        man = json.loads((rep / "fontes" / "kit-regua.json").read_text(encoding="utf-8"))
        assert man["status"] == "ok" and man["tipo"] == "regua" and man["pasta"] == "regua/paginas" and man["url"] is None, man
        assert [p["n"] for p in man["paginas"]] == list(range(1, 23)), "só kit-regua-NN: o extra, o outro kit e o kit-regua-2 ficam de fora"
        for p in man["paginas"]:
            assert p["arquivo"] == f"regua/paginas/kit-regua-{p['n']:02d}.jpg" and (p["w"], p["h"]) == (1280, 720) and p["fatia"] is None
            assert p["sha256"] == antes[f"kit-regua-{p['n']:02d}.jpg"], "o sha256 é o do arquivo da régua"
        pasta = rep / "capturas" / "kit-regua"
        assert sorted(a.name for a in pasta.iterdir()) == ["_folha-1.jpg", "_folha-2.jpg"], "só as folhas: página da régua não é copiada"
        assert {a.name: hashlib.sha256(a.read_bytes()).hexdigest() for a in pag.iterdir()} == antes, "a régua não foi tocada"
        f1, f2 = Image.open(pasta / "_folha-1.jpg"), Image.open(pasta / "_folha-2.jpg")
        assert f1.size == (5 * (420 + 8) + 8, 4 * (38 + 236 + 8) + 8) and f2.size == (5 * (420 + 8) + 8, 38 + 236 + 2 * 8), (f1.size, f2.size)
        pixel = np.asarray(f1.convert("RGB"))[8 + 38 + 2, 8 + 2].astype(int)
        assert np.abs(pixel - np.asarray(Image.open(pag / "kit-regua-01.jpg").convert("RGB"))[0, 0].astype(int)).max() < 30, "a miniatura vem da página da régua"
        codigo, out, err = cli("folha-contato", "kit-regua", "--repertorio", rep)            # regerar dá o mesmo resultado
        assert codigo == 0 and sorted(a.name for a in pasta.iterdir()) == ["_folha-1.jpg", "_folha-2.jpg"], (out, err)
        for ref, esperado in (("vazio", "sem páginas"), ("fuga", "sai da raiz")):
            codigo, out, err = cli("folha-contato", ref, "--repertorio", rep)
            assert codigo == 1 and esperado in out, (ref, out, err)
        assert not (rep / "capturas" / "vazio" / "01.jpg").exists() and not (raiz / "fora").exists()
        codigo, out, err = cli("capturar", "--listar", "--camada", "regua", "--repertorio", rep)   # e o listar mostra o manifesto
        assert codigo == 0 and "kit-regua" in out and "manifesto: ok" in out, (out, err)


def test_mesclar_candidatas_junta_o_srcset_sem_repetir_a_mesma_imagem_em_outro_tamanho():
    d = "https://static.exemplo.test/uploads/2018/07/"
    base = [d + "logo.png", d + "hero_col_7-1704x959.jpg"]
    extras = [d + "hero_col_7-852x479.jpg", d + "hero_col_0-1704x959.jpg", d + "hero_col_0-852x479.jpg?x=1", "data:image/gif;base64,AAAA", d + "outra.jpg#frag"]
    r = repertorio.mesclar_candidatas(base, extras)
    assert r == [d + "logo.png", d + "hero_col_7-1704x959.jpg", d + "hero_col_0-1704x959.jpg", d + "outra.jpg#frag"], r
    assert repertorio.mesclar_candidatas(None, None) == [] and repertorio.mesclar_candidatas(["a.jpg"], []) == ["a.jpg"]
    assert repertorio.chave_web(d + "X-852x479.JPG?z=1") == repertorio.chave_web(d + "x-1704x959.jpg"), "sem query, sem o sufixo de tamanho e sem caixa"
    assert repertorio.chave_web(d + "a-852x479.jpg") != repertorio.chave_web(d + "b-852x479.jpg")


HTML_DEZEEN = """<!doctype html><html><body>
<header><nav><img src="https://img.test/menu-1400.jpg"></nav></header>
<img src="https://img.test/solta-no-corpo.jpg" srcset="https://img.test/solta-no-corpo.jpg 600w, https://img.test/solta-no-corpo-1400.jpg 1400w">
<div id="main-content"><main class="left-column"><article id="post-1" class="main-article">
  <header><figure id="hero"><a href="#"><img src="https://img.test/hero-852x479.jpg" srcset="https://img.test/hero-852x479.jpg 852w, https://img.test/hero-1704x959.jpg 1704w"></a></figure></header>
  <section class="main-article-body">
    <figure><img src="https://img.test/a-852x479.jpg" srcset="https://img.test/a-426x240.jpg 426w, https://img.test/a-852x479.jpg 852w, https://img.test/a-1704x959.jpg 1704w"></figure>
    <figure><picture><source srcset="https://img.test/b-852x479.webp 852w, https://img.test/b-1704x959.webp 1704w"><img src="https://img.test/b-852x479.jpg"></picture></figure>
    <figure><img data-srcset="https://img.test/c-852x479.jpg 852w, https://img.test/c-1704x959.jpg 1704w" src="data:image/gif;base64,R0lGODlhAQABAAAAACw="></figure>
    <figure><img src="https://img.test/d-sem-srcset.jpg"></figure>
    <figure><img srcset="https://img.test/e,w_426.jpg 426w, https://img.test/e,w_1704.jpg 1704w" src="https://img.test/e-pequena.jpg"></figure>
    <aside id="recommended-item-single-story" class="related-in-article-wrapper"><article class="related-in-article"><a><img srcset="https://img.test/rel1-150x150.jpg 150w, https://img.test/rel1-1400.jpg 1400w"></a></article></aside>
  </section>
  <div class="rh-related-wrapper"><aside class="related-content"><ul><li><figure><img srcset="https://img.test/rel2-300.jpg 300w, https://img.test/rel2-1400.jpg 1400w"></figure></li></ul></aside></div>
  <div class="mais-lidas related-posts"><figure><img src="https://img.test/rel3-1400.jpg"></figure></div>
  <aside class="destaques"><figure><img src="https://img.test/aside-neutro-1400.jpg"></figure></aside>
  <nav class="trilha"><figure><img src="https://img.test/nav-neutro-1400.jpg"></figure></nav>
  <footer class="fim"><figure><img src="https://img.test/footer-neutro-1400.jpg"></figure></footer>
  <div class="mais-recommended-hoje"><figure><img src="https://img.test/recommend-1400.jpg"></figure></div>
  <div class="faixa-carousel-x"><figure><img src="https://img.test/carousel-1400.jpg"></figure></div>
  <div class="coluna-sidebar-x"><figure><img src="https://img.test/sidebar-1400.jpg"></figure></div>
  <div class="bloco-side-article-x"><figure><img src="https://img.test/sidearticle-1400.jpg"></figure></div>
  <div class="caixa-newsletter-x"><figure><img src="https://img.test/newsletter-1400.jpg"></figure></div>
  <div class="listing-item-image"><figure><img src="https://img.test/listing-1400.jpg"></figure></div>
  <div class="card-teaser-x"><figure><img src="https://img.test/teaser-1400.jpg"></figure></div>
  <div id="meu-related-box"><figure><img src="https://img.test/idrelated-1400.jpg"></figure></div>
  <div id="meu-recommended-box"><figure><img src="https://img.test/idrecommended-1400.jpg"></figure></div>
</article></main>
<aside class="right-column"><article class="side-article"><figure><img src="https://img.test/lateral-1400.jpg"></figure></article></aside></div>
<aside class="carousel-wrap"><ul class="carousel"><li><figure><img src="https://img.test/carrossel-1400.jpg"></figure></li></ul></aside>
<footer><figure><img src="https://img.test/rodape-1400.jpg"></figure></footer>
</body></html>"""


def test_coletar_srcset_pega_a_maior_do_conteudo_e_deixa_relacionados_e_o_resto_de_fora():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("   (playwright não instalado: prova pulada)"); return
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        try:
            pg = nav.new_page(); pg.set_content(HTML_DEZEEN)
            urls = repertorio.coletar_srcset(pg)
        finally:
            nav.close()
    esperado = ["https://img.test/hero-1704x959.jpg", "https://img.test/a-1704x959.jpg", "https://img.test/b-1704x959.webp", "https://img.test/c-1704x959.jpg",
                "https://img.test/d-sem-srcset.jpg", "https://img.test/e,w_1704.jpg"]
    assert urls == esperado, urls
    # sem a exclusão, as miniaturas relacionadas (dentro do próprio article, em figure) voltam: era o caso das 49 URLs da Dezeen
    assert not [u for u in urls if "rel" in u.rsplit("/", 1)[-1][:3] or "lateral" in u or "carrossel" in u or "rodape" in u or "menu" in u or "solta" in u], urls


def test_largura_minima_por_fonte_e_motivo_da_suspeita_vao_para_o_manifesto():
    assert repertorio.aceitar_pagina(639, 400) is False and repertorio.aceitar_pagina(639, 400, 600) is True and repertorio.aceitar_pagina(599, 400, 600) is False
    paginas, _, larguras, descartados = repertorio.montar_paginas([("a", ruido(639, 400, 1)), ("b", ruido(1920, 1086, 2)), ("c", ruido(300, 300, 3))], 1400, 600)
    assert [p["w"] for p in paginas] == [639, 1400] and descartados == 1 and larguras == [639, 1920], paginas
    with tempfile.TemporaryDirectory() as d, disco():
        rep = Path(d)
        nav = NavFalso({"peq": [[(f"https://exemplo.test/p{k}.jpg", ruido(639, 400, 10 + k)) for k in range(5)]], "pad": [[(f"https://exemplo.test/q{k}.jpg", ruido(639, 400, 20 + k)) for k in range(5)]]})
        man = repertorio.capturar_fonte(rep, fonte("peq", tipo="web", min_largura=600), nav, dormir=sem_espera, espera_retry=0)
        assert man["status"] == "suspeita" and len(man["paginas"]) == 5 and man["min_largura"] == 600, "5 páginas de 639 px (todas abaixo de 1000: suspeita pela regra de sempre)"
        man = repertorio.capturar_fonte(rep, fonte("pad", tipo="web"), nav, dormir=sem_espera, espera_retry=0)
        assert man["status"] == "vazia" and man["paginas"] == [] and "min_largura" not in man, "sem o ajuste a regra de 900 px derruba tudo"
        nav = NavFalso({"curta": [tres_paginas(1, 2)], "boa": [tres_paginas(2, 3)]})
        motivo = "Aceita como está: galeria curta de verdade."
        man = repertorio.capturar_fonte(rep, fonte("curta", motivo_suspeita=motivo), nav, dormir=sem_espera, espera_retry=0)
        assert man["status"] == "suspeita" and man["motivo_suspeita"] == motivo
        assert json.loads((rep / "fontes" / "curta.json").read_text(encoding="utf-8"))["motivo_suspeita"] == motivo
        man = repertorio.capturar_fonte(rep, fonte("boa", motivo_suspeita=motivo), nav, dormir=sem_espera, espera_retry=0)
        assert man["status"] == "ok" and "motivo_suspeita" not in man, "o motivo só vale enquanto a captura é suspeita"
    with tempfile.TemporaryDirectory() as d:
        for ruim in (299, 3001, "600", True, 12.5):
            (Path(d) / "fontes.json").write_text(json.dumps({"fontes": [fonte("a", min_largura=ruim)]}), encoding="utf-8")
            try:
                repertorio.carregar_fontes(d); raise AssertionError(f"devia recusar min_largura {ruim!r}")
            except SystemExit as e:
                assert "min_largura" in str(e), e
        (Path(d) / "fontes.json").write_text(json.dumps({"fontes": [fonte("a", min_largura=600)]}), encoding="utf-8")
        assert repertorio.carregar_fontes(d)[0]["min_largura"] == 600


def test_pdf_vira_paginas_pelo_pdftoppm_sem_rede():
    if not shutil.which("pdftoppm"):
        print("   (pdftoppm não instalado: prova pulada)"); return
    with tempfile.TemporaryDirectory() as d, disco():
        rep = Path(d)
        pdf = rep / "origem" / "kit.pdf"; pdf.parent.mkdir()
        paginas = [ruido(1400, 788, 60 + k).convert("RGB") for k in range(3)]
        paginas[0].save(pdf, "PDF", save_all=True, append_images=paginas[1:], resolution=72.0)
        man = repertorio.capturar_fonte(rep, fonte("kit-pdf", tipo="pdf", url=pdf.as_uri()), repertorio.Navegador(), dormir=sem_espera)
        assert man["status"] == "ok" and [p["n"] for p in man["paginas"]] == [1, 2, 3], man
        assert [p["modulo_url"] for p in man["paginas"]] == [f"{pdf.as_uri()}#page={k}" for k in (1, 2, 3)]
        assert all(p["w"] == 1400 for p in man["paginas"]) and all(abs(p["h"] - 788) <= 2 for p in man["paginas"]), man["paginas"]
        assert list((rep / "capturas").rglob("*.pdf")) == [], "o PDF baixado não fica em capturas/"


class _Servidor:
    """Servidor local (127.0.0.1) para o único teste que abre o Chromium de verdade, sem sair da máquina."""
    def __init__(self, pasta):
        import http.server, threading
        pasta = str(pasta)

        class H(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *a, **k):
                super().__init__(*a, directory=pasta, **k)

            def do_GET(self):
                if self.path.startswith("/barrada"):
                    self.send_response(403); self.send_header("Content-Type", "text/html"); self.end_headers()
                    self.wfile.write(b"<html><title>Access denied</title><body>Access denied</body></html>"); return
                super().do_GET()

            def log_message(self, *a):
                pass
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def parar(self):
        self.srv.shutdown(); self.srv.server_close()


def test_navegador_de_verdade_le_pagina_local_e_o_403():
    """O Playwright e o Chromium reais contra um servidor em 127.0.0.1: tipo web (candidatas_web) traz as imagens grandes, o título, o
    link canônico e o código HTTP; página que devolve 403 vira bloqueada. Dura uns 20 s (a rolagem da página é de verdade)."""
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        print("   (playwright não instalado: prova pulada)"); return
    with tempfile.TemporaryDirectory() as d, disco():
        site = Path(d) / "site"; site.mkdir()
        for nome, semente in (("um.jpg", 1), ("dois.jpg", 2)):
            ruido(1400, 788, semente).save(site / nome, quality=90)
        Image.new("RGB", (120, 120), (200, 0, 0)).save(site / "logo.png")
        for nome, semente, tam in (("a-852.jpg", 5, (852, 479)), ("a-1704.jpg", 6, (1704, 959)), ("b-852.jpg", 7, (852, 479)), ("b-1704.jpg", 8, (1704, 959)),
                                   ("rel-300.jpg", 9, (300, 300)), ("rel-1400.jpg", 10, (1400, 788))):
            ruido(tam[0], tam[1], semente).save(site / nome, quality=90)
        (site / "index.html").write_text('<!doctype html><title>Galeria de teste</title><link rel="canonical" href="https://exemplo.test/galeria-de-teste">'
                                         '<img src="um.jpg" style="width:700px"><img src="logo.png"><img src="dois.jpg" style="width:700px">'
                                         '<article><figure><img src="a-852.jpg" srcset="a-852.jpg 852w, a-1704.jpg 1704w" sizes="852px" style="width:852px"></figure>'
                                         '<figure><img src="b-852.jpg" srcset="b-852.jpg 852w, b-1704.jpg 1704w" sizes="852px" style="width:852px"></figure>'
                                         '<aside class="related-content"><figure><img src="rel-300.jpg" srcset="rel-300.jpg 300w, rel-1400.jpg 1400w" sizes="300px" style="width:300px"></figure></aside></article>', encoding="utf-8")
        srv = _Servidor(site)
        try:
            with repertorio.Navegador() as nav:
                man = repertorio.capturar_fonte(Path(d) / "rep", fonte("local", tipo="web", url=srv.url + "/index.html"), nav, dormir=sem_espera)
                assert man["status"] == "ok" and man["http"] == 200 and man["canonica"] == "https://exemplo.test/galeria-de-teste", man
                assert [p["modulo_url"].rsplit("/", 1)[-1] for p in man["paginas"]] == ["um.jpg", "dois.jpg", "a-1704.jpg", "b-1704.jpg"], \
                    "a logo de 120 px fica de fora; do article vem o srcset grande (a variante de 852 px o coletor da régua descarta); a miniatura do aside não entra"
                assert [(p["w"], p["h"]) for p in man["paginas"]] == [(1400, 788), (1400, 788), (1400, 788), (1400, 788)], "1704 px sai reduzida para 1400"
                with trocar(ROLAGENS=1, ROLAGEM_MS=10, ESPERA_INICIAL_MS=50):
                    col = nav.coletar(fonte("barrada", tipo="behance", url=srv.url + "/barrada"))
                assert col["status_http"] == 403 and col["urls"] == [] and repertorio.pagina_bloqueada(col["status_http"], col["titulo"], col["texto"]), col
                with trocar(ROLAGENS=1, ROLAGEM_MS=10, ESPERA_INICIAL_MS=50):
                    man = repertorio.capturar_fonte(Path(d) / "rep2", fonte("barrada", tipo="behance", url=srv.url + "/barrada"), nav, dormir=sem_espera, espera_retry=0)
                assert man["status"] == "bloqueada" and man["paginas"] == [] and man["http"] == 403, man
        finally:
            srv.parar()


def test_capturar_pede_selecao_e_recusa_id_e_camada_que_nao_existem():
    with tempfile.TemporaryDirectory() as d:
        rep = Path(d); (rep / "fontes.json").write_text(json.dumps({"fontes": [fonte("a"), fonte("b", camada="lente"), fonte("c", tipo="regua", camada="regua", url=None)]}), encoding="utf-8")
        codigo, out, err = cli("capturar", "--repertorio", rep)
        assert codigo != 0 and "diga o que capturar" in err and "--listar" in err, (out, err)
        codigo, out, err = cli("capturar", "--ref", "nao-existe", "--repertorio", rep)
        assert codigo != 0 and "nao-existe" in err and "fora de fontes.json" in err, (out, err)
        codigo, out, err = cli("capturar", "--camada", "profunda", "inventada", "--repertorio", rep)
        assert codigo != 0 and "inventada" in err, (out, err)
        codigo, out, err = cli("capturar", "--listar", "--repertorio", rep)                   # sem filtro lista tudo e não baixa nada
        assert codigo == 0 and "3 fonte(s)" in out and out.count("manifesto: -") == 3, (out, err)
        codigo, out, err = cli("capturar", "--listar", "--camada", "lente", "--repertorio", rep)
        assert codigo == 0 and "1 fonte(s)" in out and [l.split()[0] for l in out.splitlines() if "manifesto:" in l] == ["b"], (out, err)
        codigo, out, err = cli("capturar", "--listar", "--ref", "a,c", "--repertorio", rep)   # --ref aceita vírgula (e vários valores)
        assert codigo == 0 and "2 fonte(s)" in out, (out, err)
        codigo, out, err = cli("capturar", "--listar", "--ref", "a", "c", "--camada", "lente", "--repertorio", rep)
        assert codigo == 0 and "3 fonte(s)" in out, "--ref e --camada somam"
        assert not (rep / "capturas").exists() and not (rep / "fontes").exists(), "listar não grava nada"


def test_fontes_json_recusa_id_inseguro_tipo_e_camada_fora_do_vocabulario():
    with tempfile.TemporaryDirectory() as d:
        rep = Path(d)
        casos = [([fonte("../fora")], "fora do padrão"), ([fonte("a"), fonte("a")], "repetido"), ([fonte("a", tipo="ftp")], "tipo"),
                 ([fonte("a", camada="funda")], "camada"), ([fonte("a", url="ftp://x")], "url"), ([fonte("a", url=None)], "url")]
        for fontes, esperado in casos:
            (rep / "fontes.json").write_text(json.dumps({"fontes": fontes}), encoding="utf-8")
            try:
                repertorio.carregar_fontes(rep)
                raise AssertionError(f"devia recusar {fontes}")
            except SystemExit as e:
                assert esperado in str(e), (esperado, e)
        (rep / "fontes.json").write_text(json.dumps({"fontes": [fonte("a", url="213026839"), fonte("b", tipo="regua", camada="regua", url=None)]}), encoding="utf-8")
        assert [f["id"] for f in repertorio.carregar_fontes(rep)] == ["a", "b"], "só o id numérico do Behance vale como url"


def test_fontes_json_do_projeto_cobre_o_indice_e_tem_as_camadas_combinadas():
    fontes = repertorio.carregar_fontes(repertorio.RAIZ)
    por = {f["id"]: f for f in fontes}
    camadas = {c: [f["id"] for f in fontes if f["camada"] == c] for c in repertorio.CAMADAS}
    assert camadas["prioritaria"] == ["web-conebra", "web-uniao-run-2025"], camadas["prioritaria"]
    assert sorted(camadas["profunda"]) == sorted(["web-deck-256711557", "web-lunetra-pitch", "web-pitch-deck-saas", "web-proposta-patrocinio-9901637", "web-tupa-fc-sponsor",
                                                  "web-proposta-itau", "web-proposta-unimed", "web-mc-daniel", "web-japa-2025", "web-city-run-club", "web-kit-media-integral", "web-nexxus"]), camadas["profunda"]
    assert sorted(camadas["releitura"]) == sorted(["web-deck-tomasello-tc2025", "web-deck-philadelphia-pcc26", "web-deck-media-kit-245250053", "web-nike-run-sp-25", "web-spotify-garmin-run-the-beat",
                                                   "web-coway-run-22", "web-soweto-never-run-alone", "web-deck-strategic-partnership", "web-deck-ai-startup"]), camadas["releitura"]
    assert len(camadas["regua"]) == 8 and len(camadas["fora"]) == 11 and camadas["lente"], {c: len(v) for c, v in camadas.items()}
    indice = json.loads((repertorio.RAIZ / "indice.json").read_text(encoding="utf-8"))
    for r in indice["referencias"]:
        f = por.get(r["id"])
        assert f is not None, f"{r['id']} está no índice e não está em fontes.json"
        if r.get("url"):
            assert f["url"] == r["url"], (r["id"], f["url"], r["url"])
        else:
            assert f["tipo"] == "regua" and f["camada"] == "regua", r["id"]
    assert all(por[i]["camada"] != "fora" for i in (r["id"] for r in indice["referencias"])), "referência do índice não pode estar como fora"
    assert all(f.get("motivo") for f in fontes if f["camada"] == "fora") and all(f.get("pasta") for f in fontes if f["camada"] == "regua")
    assert [f["tipo"] for f in fontes if f["id"] == "web-ironman-manual-2019"] == ["pdf"] and por["web-conebra"]["tipo"] == "behance"
    assert por["web-premier-league-dixonbaxi"]["min_largura"] == 600 and por["web-premier-league-dixonbaxi"]["motivo_min_largura"]
    for i in ("web-ufc-rebrand", "web-utmb-parceiro", "web-utmb-cartaz-26", "web-utmb-mb26", "web-paris2024-adsoftheworld", "web-premier-league-dixonbaxi"):
        assert "Aceita como está" in por[i]["motivo_suspeita"], i
    ig = (AQUI.parent / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "repertorio/capturas/" in ig and not any(l.strip().startswith("repertorio/fontes") for l in ig), "capturas/ fora do git, manifestos dentro"


if __name__ == "__main__":
    falhou = 0
    for nome, fn in list(globals().items()):
        if nome.startswith("test_"):
            try:
                fn(); print("ok  ", nome)
            except AssertionError as e:
                falhou += 1; print("FALHOU", nome, str(e)[:400])
    print("PROVAS:", "VERDES" if not falhou else f"{falhou} FALHA(S)")
    sys.exit(1 if falhou else 0)

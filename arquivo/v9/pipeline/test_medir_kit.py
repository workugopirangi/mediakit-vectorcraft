#!/usr/bin/env python3
"""
test_medir_kit.py: provas do medir_kit.py (a prova para o dono cético, references/10). Sem pytest:

  ~/.venvs/mediakit/bin/python pipeline/test_medir_kit.py

Os kits são sintéticos e gravados numa pasta temporária no formato que o render grava: mediakit.json, saida/plano-
elementos-r1.json, saida/render-report.json, saida/png/kit-r1-NN.png (fundo chapado, para o contraste ter valor
conhecido), saida/kit-r1.pdf (escrito à mão: Helvetica, e uma fonte Type 3 quando o mutante pede) e saida/qa.txt.
O kit bom passa em todas as medidas; cada mutante quebra UMA coisa e a medida dela tem de falhar (a prova de que a
medida enxerga); o inverso de cada mutante (o caso parecido que não é defeito) tem de continuar passando.
"""
import json, shutil, sys, tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import medir_kit  # noqa: E402

FAMILIAS = ("ornamento-identidade", "pattern-textura", "sobreposicao-recorte", "profundidade-3d", "tratamento-imagem",
            "tipografia-expressiva", "acabamento-borda", "composicao-hibrida")
# 10 páginas; recursos por página (índices das famílias): cada família em 3 páginas, toda página com 2 ou 3, nunca
# 3 páginas seguidas com 3 recursos (a intensidade calculada é o número de recursos)
RECURSOS_DEPOIS = [[0, 1, 2], [3, 4], [5, 6, 7], [0, 1], [2, 3, 4], [5, 6], [7, 0, 1], [2, 3], [4, 5], [6, 7]]
ROTULOS_DEPOIS = ["capa:a", "manifesto:a", "publico:a", "divisor:a", "ativo:painel", "ativo:sangria", "cota:a", "cota:b",
                  "prova", "contato:a"]
FUNCOES = ["foco", "contexto", "identidade", "profundidade", "equilibrio"]
TESE = "A cidade muda de ritmo"
FIO_PARAMS = {"texto_de": "titulo", "largura": 600}


# ------------------------------------------------------------------------------------------------- PDF escrito à mão
def _esc(s):
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def pdf_minimo(caminho, paginas, type3_na=None):
    """PDF de 1440x810 pt com uma página por item de `paginas` (lista de linhas de texto em Helvetica, ASCII). Com
    `type3_na` (número da página), essa página também desenha com uma fonte Type 3 (o que o pdffonts acusa)."""
    objs = {}
    n_pag = len(paginas)
    primeiro = 6
    kids = []
    for i, linhas in enumerate(paginas, 1):
        cont, pag = primeiro + 2 * (i - 1), primeiro + 2 * (i - 1) + 1
        kids.append(pag)
        ops = []
        for j, l in enumerate(linhas):
            ops.append(f"BT /F1 40 Tf 72 {700 - 60 * j} Td ({_esc(l)}) Tj ET")
        fontes = "/F1 3 0 R"
        if type3_na == i:
            ops.append("BT /F3 40 Tf 72 80 Td (A) Tj ET")
            fontes += " /F3 4 0 R"
        corpo = "\n".join(ops).encode("latin-1")
        objs[cont] = b"<< /Length %d >>\nstream\n" % len(corpo) + corpo + b"\nendstream"
        objs[pag] = (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 1440 810] /Contents {cont} 0 R "
                     f"/Resources << /Font << {fontes} >> >> >>").encode()
    objs[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objs[2] = f"<< /Type /Pages /Kids [{' '.join(f'{k} 0 R' for k in kids)}] /Count {n_pag} >>".encode()
    objs[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    objs[4] = (b"<< /Type /Font /Subtype /Type3 /FontBBox [0 0 1000 1000] /FontMatrix [0.001 0 0 0.001 0 0] "
               b"/CharProcs << /sq 5 0 R >> /Encoding << /Type /Encoding /Differences [65 /sq] >> /FirstChar 65 "
               b"/LastChar 65 /Widths [1000] /Resources << >> >>")
    proc = b"1000 0 0 0 1000 1000 d1 0 0 1000 1000 re f"
    objs[5] = b"<< /Length %d >>\nstream\n" % len(proc) + proc + b"\nendstream"
    saida = bytearray(b"%PDF-1.4\n")
    offs = {}
    for num in sorted(objs):
        offs[num] = len(saida)
        saida += f"{num} 0 obj\n".encode() + objs[num] + b"\nendobj\n"
    xref = len(saida)
    total = max(objs) + 1
    saida += f"xref\n0 {total}\n0000000000 65535 f \n".encode()
    for num in range(1, total):
        saida += f"{offs[num]:010d} 00000 n \n".encode()
    saida += f"trailer\n<< /Size {total} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    Path(caminho).write_bytes(bytes(saida))


# ------------------------------------------------------------------------------------------------- kit sintético
_PNGS = {}


def png_chapado(cor):
    """PNG 1920x1080 de uma cor só, gravado uma vez por cor (cada kit copia o seu)."""
    if cor not in _PNGS:
        from PIL import Image
        d = Path(tempfile.mkdtemp(prefix="test-medir-png-"))
        _PNGS[cor] = d / f"{cor.lstrip('#')}.png"
        Image.new("RGB", (1920, 1080), cor).save(_PNGS[cor], compress_level=1)
    return _PNGS[cor]


def titulo(n):
    return f"Titulo da pagina {n}"


def montar(pasta, mk21=True, rotulos=None, recursos=None, fio_paginas=7, fundo="#101010", fundos=None, qa="ok",
           type3_na=None, sem_titulo_na=None, sem_tese=False, alterar_kit=None, alterar_plano=None):
    """Grava um kit renderizado sintético em `pasta` e devolve a pasta. mk21=False dá um kit mk-2.0 (sem direção
    criativa nem acabamento). `fundos` = {n: '#hex'} troca o fundo do PNG de uma página. `qa` = 'ok', 'falha' ou None
    (sem qa.txt). `alterar_kit(k)` e `alterar_plano(plano)` mexem antes de gravar."""
    pasta = Path(pasta)
    rotulos = rotulos or ROTULOS_DEPOIS
    recursos = recursos if recursos is not None else RECURSOS_DEPOIS
    n_pag = len(rotulos)
    (pasta / "saida" / "png").mkdir(parents=True, exist_ok=True)
    rids = [f"r{i}" for i in range(len(FAMILIAS))]
    k = {"schema_version": "mk-2.1" if mk21 else "mk-2.0", "evento": {"nome": "Kit de prova"},
         "tese": {"frase": TESE}, "elementos": [], "composicao": {}}
    if mk21:
        k["direcao_criativa"] = {
            "recursos": [{"id": rid, "familia": f, "referencia": "ficticio:x", "principio": "um princípio qualquer",
                          "rota": "codigo"} for rid, f in zip(rids, FAMILIAS)],
            "intensidade": {"padrao": 1, "teto": 3},
            "fio_condutor": {"motivo": "lua", "papeis": {f"p{n}": "eco" for n in range(1, fio_paginas + 1)}}}
    paginas = []
    for n in range(1, n_pag + 1):
        ch = f"p{n}"
        ent = {"mensagem": "m", "elementos": [{"id": f"h{n}", "papel": "heroi", "ancora": {"relacao": "alinha"}}]}
        itens = [{"id": f"h{n}", "papel": "heroi", "funcao": FUNCOES[n % len(FUNCOES)], "origem": "composicao",
                  "encaixe": "composicao", "camada": "frente", "formato": "svg", "x": 1300, "y": 500, "w": 300, "h": 300,
                  "ancora": {"relacao": "alinha"}},
                 {"id": "constante-fio", "papel": "constante", "camada": "frente", "formato": "svg",
                  "x": 0, "y": 1070, "w": 1920, "h": 4}]
        if mk21:
            rs = [rids[i] for i in (recursos[n - 1] if n - 1 < len(recursos) else [])]
            ent["acabamento"] = {"recursos": rs, "intensidade": min(3, len(rs)), "porque": "um porquê"}
            if n <= fio_paginas:
                ent["elementos"].append({"id": "fio-lua", "papel": "acabamento", "motivo": "lua",
                                         "grafismo": {"tipo": "eco", "params": dict(FIO_PARAMS)},
                                         "ancora": {"relacao": "alinha"}})
                itens.append({"id": f"fio-lua-p{n}", "papel": "acabamento", "funcao": "acabamento", "origem": "composicao",
                              "encaixe": "composicao", "camada": "atras", "formato": "svg", "motivo": "lua",
                              "grafismo": {"tipo": "eco", "params": dict(FIO_PARAMS)}, "efeito": {"opacidade": 0.12},
                              "x": 1300, "y": 900, "w": 500, "h": 100, "ancora": {"relacao": "alinha"}})
        k["composicao"][ch] = ent
        paginas.append({"n": n, "rotulo": rotulos[n - 1], "tipo": rotulos[n - 1].split(":")[0], "rotulos": [ch],
                        "composicao": {"chave": ch}, "elementos": itens, "erros_composicao": [],
                        "protegidos": [{"classe": "titulo", "texto": titulo(n), "x": 100, "y": 100, "w": 800, "h": 120},
                                       {"classe": "corpo", "texto": "Texto corrido da pagina", "x": 100, "y": 300, "w": 800, "h": 40}]})
    plano = {"receita": "r1", "largura": 1920, "altura": 1080, "paginas": paginas, "composicao_erros": []}
    if alterar_kit:
        alterar_kit(k)
    if alterar_plano:
        alterar_plano(plano)
    (pasta / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False), encoding="utf-8")
    (pasta / "saida" / "plano-elementos-r1.json").write_text(json.dumps(plano, ensure_ascii=False), encoding="utf-8")
    por_pagina = [{"pagina": n, "pattern": False, "textos": [
        {"x": 100, "y": 100, "w": 800, "h": 120, "fs": 96, "cor": "#ffffff", "bg": None, "texto": titulo(n), "cls": "display"},
        {"x": 100, "y": 300, "w": 800, "h": 40, "fs": 24, "cor": "#ffffff", "bg": None, "texto": "Texto corrido da pagina", "cls": "corpo"}]}
        for n in range(1, n_pag + 1)]
    rep = {"direcoes": {"r1": {"horizontal": {"por_pagina": por_pagina, "png_dir": str(pasta / "saida" / "png")}}}}
    (pasta / "saida" / "render-report.json").write_text(json.dumps(rep), encoding="utf-8")
    for n in range(1, n_pag + 1):
        shutil.copyfile(png_chapado((fundos or {}).get(n, fundo)), pasta / "saida" / "png" / f"kit-r1-{n:02d}.png")
    pdf_minimo(pasta / "saida" / "kit-r1.pdf",
               [([] if n == sem_titulo_na else [titulo(n)]) + ([TESE] if n == 1 and not sem_tese else []) + ["Texto corrido"]
                for n in range(1, n_pag + 1)], type3_na)
    if qa:
        (pasta / "saida" / "qa.txt").write_text(
            ("FALHA  r1 p.3: contraste 2.1:1 abaixo de 3:1\n\n1 falha(s), 1 aviso(s)\n" if qa == "falha" else
             "AVISO  acabamento r1: p.1 a p.10 sem nenhuma página de intensidade 0 ou 1\n\n0 falha(s), 1 aviso(s)\n"),
            encoding="utf-8")
    return pasta


def montar_antes(pasta, n_pag=8, fundo="#303030", **kw):
    """O kit anterior: mk-2.0, sem direção criativa; as duas cotas vizinhas com a mesma estrutura (como a AME v2)."""
    rot = ["capa:c", "manifesto:a", "publico:b", "divisor:c", "ativo:painel", "cota:a", "cota:a", "contato:b",
           "prova", "historico", "territorio", "inventario"][:n_pag]

    def mesmas_cotas(pl):
        for pg in pl["paginas"]:
            if pg["rotulo"] == "cota:a":
                pg["elementos"][0]["funcao"] = "identidade"
    return montar(pasta, mk21=False, rotulos=rot, recursos=[], fundo=fundo, alterar_plano=mesmas_cotas, **kw)


def medida(res, mid):
    return next(m for m in res["medidas"] if m["id"] == mid)


def estado(res, mid):
    return medida(res, mid)["estado"]


class Tmp:
    def __enter__(self):
        self.d = Path(tempfile.mkdtemp(prefix="test-medir-"))
        return self.d

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


def medir(pasta, antes=None, **kw):
    return medir_kit.medir_com_antes(pasta, antes, **kw)


# ------------------------------------------------------------------------------------------------- provas
def test_contraste_do_texto_e_a_conta_do_qa():
    """A conta que o qa.py reprova e o medir_kit lê (qa.contraste_do_texto), com valores conhecidos."""
    import numpy as np
    import qa
    preto = np.zeros((1080, 1920))
    t = {"x": 100, "y": 100, "w": 400, "h": 60, "fs": 96, "cor": "#ffffff", "texto": "x"}
    r, m = qa.contraste_do_texto(preto, t)
    assert abs(r - 21.0) < 1e-9 and m == 3.0, (r, m)                       # branco sobre preto, display: 3:1
    assert qa.contraste_do_texto(preto, dict(t, fs=16))[1] == 4.5           # abaixo de 24 px: 4,5:1
    assert qa.contraste_do_texto(preto, dict(t, fs=12)) is None             # abaixo de 14 px não se mede
    assert qa.contraste_do_texto(preto, dict(t, cor=None)) is None
    assert qa.contraste_do_texto(preto, dict(t, bg="#ffffff"))[0] == 1.0    # o fundo próprio vence o PNG
    listras = preto.copy()
    listras[:, ::2] = 1.0                                                   # metade do anel branca
    claro_pior = qa.contraste_do_texto(listras, dict(t, cls="corpo", fs=24), pattern=True)
    assert claro_pior[0] == 1.0 and claro_pior[1] == 4.5, claro_pior        # sobre pattern: o pior lado, corpo a 4,5:1
    rgb = (np.ones((1080, 1920, 3)) * 48).astype("uint8")
    cheio = qa.lum_wcag(rgb.astype(float) / 255.0)
    so_caixa = medir_kit.luminancia_nas_caixas(rgb, [t])
    assert qa.contraste_do_texto(cheio, t) == qa.contraste_do_texto(so_caixa, t)


def test_kit_bom_passa_em_tudo():
    with Tmp() as d:
        res = medir(montar(d / "depois"), montar_antes(d / "antes"))
        ruins = {m["id"]: m["estado"] for m in res["medidas"] if m["estado"] != "passou"}
        assert res["veredito"] == "passou" and not ruins, (ruins, res["resumo"])
        assert res["passou"] is True
        assert "VEREDITO: PASSOU" in res["resumo"], res["resumo"]


def test_familias_por_pagina():
    def declara(n):
        def f(k):
            k["composicao"]["p2"]["acabamento"]["intensidade"] = n
        return f
    with Tmp() as d:
        rec = [list(x) for x in RECURSOS_DEPOIS]
        rec[1] = [3]                                     # p.2 com uma família só
        # mutante: a p.2 declarada intensidade 2 com 1 família reprova
        m = medida(medir(montar(d / "mut", recursos=rec, alterar_kit=declara(2))), "familias_por_pagina")
        assert m["estado"] == "falhou" and m["detalhe"]["paginas_abaixo"] == [2], m["detalhe"]
        assert m["detalhe"]["minimo_sem_respiro"] == 1 and m["detalhe"]["paginas_respiro"] == []
        # inverso: a mesma página declarada de respiro (1, e também 0) fica fora da meta e passa
        for n in (1, 0):
            m = medida(medir(montar(d / f"resp{n}", recursos=rec, alterar_kit=declara(n))), "familias_por_pagina")
            assert m["estado"] == "passou" and m["detalhe"]["paginas_respiro"] == [2], (n, m["detalhe"])
            assert m["detalhe"]["minimo"] == 1 and m["detalhe"]["minimo_sem_respiro"] == 2, m["detalhe"]
        assert estado(medir(montar(d / "bom")), "familias_por_pagina") == "passou"


def test_cobertura_das_familias():
    with Tmp() as d:
        rec = [list(x) for x in RECURSOS_DEPOIS]
        rec[1] = [3, 0]                                  # p.2 troca a família 4 pela 0: a 4 fica em 2 páginas, a 0 em 4
        res = medir(montar(d / "mut", recursos=rec))
        assert estado(res, "familias_por_pagina") == "passou"           # toda página continua com 2 famílias ou mais
        m = medida(res, "cobertura_familias")
        assert m["estado"] == "falhou" and m["detalhe"]["faltando"] == [FAMILIAS[4]], m["detalhe"]
        assert estado(medir(montar(d / "bom")), "cobertura_familias") == "passou"


def test_cobertura_desconta_nao_usa():
    sem7 = [[5, 6, 0] if x == [5, 6, 7] else [2, 0, 1] if x == [7, 0, 1] else [6, 3] if x == [6, 7] else list(x)
            for x in RECURSOS_DEPOIS]                    # a família 7 sai de todas as páginas; as outras 7 em ≥ 3

    def nao_usa(k):
        k["direcao_criativa"]["nao_usa"] = [FAMILIAS[7]]
    with Tmp() as d:
        m = medida(medir(montar(d / "sem", recursos=sem7)), "cobertura_familias")      # sem nao_usa: 7 de 8, reprova
        assert m["estado"] == "falhou" and m["detalhe"]["faltando"] == [FAMILIAS[7]], m["detalhe"]
        m = medida(medir(montar(d / "com", recursos=sem7, alterar_kit=nao_usa)), "cobertura_familias")
        assert m["estado"] == "passou" and m["detalhe"]["familias_exigidas"] == 7, m["detalhe"]  # 8 menos 1: passa
        # nao_usa não perdoa outra família: a 4 em 2 páginas continua reprovando
        rec = [list(x) for x in sem7]
        rec[1] = [3, 0]
        m = medida(medir(montar(d / "outra", recursos=rec, alterar_kit=nao_usa)), "cobertura_familias")
        assert m["estado"] == "falhou" and m["detalhe"]["faltando"] == [FAMILIAS[4]], m["detalhe"]


def test_elementos_ancorados():
    def do_catalogo(pl):
        it = pl["paginas"][2]["elementos"][0]
        it.update(origem="catalogo", encaixe="topo-direita")
        it.pop("ancora")
    def erro_na_pagina(pl):
        pl["paginas"][4]["erros_composicao"] = ["`h5`: alvo `titulo` ausente na página"]
    def derivado_e_constante(pl):                      # inverso: sombra derivada e constante não pedem âncora
        pl["paginas"][0]["elementos"].append({"id": "h1-sombra", "papel": "heroi", "derivado_de": "h1", "camada": "frente",
                                              "formato": "svg", "x": 1300, "y": 790, "w": 300, "h": 30})
    with Tmp() as d:
        for nome, mut, esperado in (("cat", do_catalogo, "h3"), ("erro", erro_na_pagina, "h5")):
            m = medida(medir(montar(d / nome, alterar_plano=mut)), "elementos_ancorados")
            assert m["estado"] == "falhou" and [x["id"] for x in m["detalhe"]["nao_ancorados"]] == [esperado], m
        m = medida(medir(montar(d / "inv", alterar_plano=derivado_e_constante)), "elementos_ancorados")
        assert m["estado"] == "passou" and m["detalhe"]["porcentagem"] == 100.0, m


def test_continuidade_do_fio():
    def outro_tratamento(k):
        for e in k["composicao"]["p4"]["elementos"]:
            if e["id"] == "fio-lua":
                e["grafismo"]["params"]["texto_de"] = "tese"
    def outra_largura(k):                             # inverso: medida muda com o papel, o tratamento não
        for e in k["composicao"]["p4"]["elementos"]:
            if e["id"] == "fio-lua":
                e["grafismo"]["params"]["largura"] = 900
    with Tmp() as d:
        m = medida(medir(montar(d / "poucas", fio_paginas=5)), "continuidade_fio")
        assert m["estado"] == "falhou" and m["detalhe"]["maior_grupo"]["paginas"] == [1, 2, 3, 4, 5], m["detalhe"]
        m = medida(medir(montar(d / "trat", alterar_kit=outro_tratamento)), "continuidade_fio")
        assert m["estado"] == "falhou" and m["detalhe"]["paginas_com_outro_tratamento"] == [4], m["detalhe"]
        m = medida(medir(montar(d / "larg", alterar_kit=outra_largura)), "continuidade_fio")
        assert m["estado"] == "passou" and len(m["detalhe"]["maior_grupo"]["paginas"]) == 7, m["detalhe"]


def test_variedade():
    with Tmp() as d:
        rot = list(ROTULOS_DEPOIS)
        rot[5] = rot[4]                                   # p.5 e p.6 com o mesmo rótulo e o mesmo esqueleto

        def mesmo_esqueleto(pl):
            pl["paginas"][5]["elementos"][0]["funcao"] = pl["paginas"][4]["elementos"][0]["funcao"]
        m = medida(medir(montar(d / "viz", rotulos=rot, alterar_plano=mesmo_esqueleto)), "variedade")
        assert m["estado"] == "falhou" and m["detalhe"]["vizinhas_iguais"] == [[5, 6]], m["detalhe"]
        # contra o antes: um antes de 12 páginas (11 estruturas distintas: as duas cotas são iguais) vence as 10 do depois
        res = medir(montar(d / "bom"), montar_antes(d / "antes12", n_pag=12))
        m = medida(res, "variedade")
        assert m["estado"] == "falhou" and m["criterios"][0]["passou"] is False, m
        assert m["criterios"][1]["passou"] is True
        # inverso: o antes de 8 páginas (7 estruturas) fica abaixo das 10 do depois
        assert estado(medir(montar(d / "bom2"), montar_antes(d / "antes8")), "variedade") == "passou"


def test_ritmo():
    def tres_marcantes(k):                            # p.1 e p.3 já têm 3 recursos; a p.2 declarada 3 fecha a corrida
        k["composicao"]["p2"]["acabamento"]["intensidade"] = 3
    def duas_marcantes(k):                            # inverso: a p.9 em 3 fica sozinha (p.8 e p.10 em 2)
        k["composicao"]["p9"]["acabamento"]["intensidade"] = 3
    with Tmp() as d:
        m = medida(medir(montar(d / "mut", alterar_kit=tres_marcantes)), "ritmo")
        assert m["estado"] == "falhou" and m["detalhe"]["corridas_marcantes"] == [[1, 2, 3]], m["detalhe"]
        m = medida(medir(montar(d / "inv", alterar_kit=duas_marcantes)), "ritmo")
        assert m["estado"] == "passou", m["detalhe"]
        # o respiro é aviso: o kit bom não tem página de 0 ou 1 e mesmo assim passa, com o aviso marcado
        m = medida(medir(montar(d / "bom")), "ritmo")
        assert m["estado"] == "passou" and m["criterios"][1]["nivel"] == "aviso" and m["criterios"][1]["passou"] is False


def test_legibilidade_contraste():
    with Tmp() as d:
        antes = montar_antes(d / "antes")                               # branco sobre #303030
        # mediana: o depois com fundo #707070 (4,7:1, acima do mínimo do QA) cai abaixo de 95% da mediana do antes
        res = medir(montar(d / "med", fundo="#707070"), antes)
        m = medida(res, "legibilidade")
        assert m["estado"] == "falhou", m
        assert m["criterios"][0]["passou"] is True and m["criterios"][1]["passou"] is False, m["criterios"]
        # uma página com o texto branco sobre fundo claro: linha abaixo do mínimo
        m = medida(medir(montar(d / "baixo", fundos={3: "#c8c8c8"}), antes), "legibilidade")
        assert m["criterios"][0]["passou"] is False and {x["n"] for x in m["detalhe"]["linhas_abaixo_do_minimo"]} == {3}, m
        # inverso: o mesmo fundo do antes passa (100% da mediana)
        assert estado(medir(montar(d / "igual", fundo="#303030"), antes), "legibilidade") == "passou"


def test_legibilidade_texto_sobre_textura():
    def textura(camada, bg=False):
        def f(pl):
            pl["paginas"][1]["elementos"].append({"id": "trama", "papel": "pattern", "camada": camada, "formato": "png",
                                                  "x": 0, "y": 0, "w": 1920, "h": 1080})
        return f
    with Tmp() as d:
        m = medida(medir(montar(d / "mut", alterar_plano=textura("atras"))), "legibilidade")
        sob = m["detalhe"]["texto_sobre_textura_sem_veu"]
        assert m["estado"] == "falhou" and [(x["n"], x["classe"]) for x in sob] == [(2, "corpo")], sob
        m = medida(medir(montar(d / "veu", alterar_plano=textura("sob-veu"))), "legibilidade")
        assert m["estado"] == "passou", m["detalhe"]["texto_sobre_textura_sem_veu"]
        # inverso: o texto com fundo próprio (bg no render-report) não está sobre a textura
        p = montar(d / "bg", alterar_plano=textura("atras"))
        rp = json.loads((p / "saida" / "render-report.json").read_text())
        for t in rp["direcoes"]["r1"]["horizontal"]["por_pagina"][1]["textos"]:
            t["bg"] = "#000000"
        (p / "saida" / "render-report.json").write_text(json.dumps(rp))
        assert estado(medir(p), "legibilidade") == "passou"


def test_pdf():
    with Tmp() as d:
        for nome, kw, criterio in (("t3", {"type3_na": 2}, 0), ("tit", {"sem_titulo_na": 3}, 1), ("tese", {"sem_tese": True}, 2)):
            m = medida(medir(montar(d / nome, **kw)), "pdf")
            assert m["estado"] == "falhou" and m["criterios"][criterio]["passou"] is False, (nome, m)
            outros = [c["passou"] for i, c in enumerate(m["criterios"]) if c["nivel"] == "meta" and i != criterio]
            assert all(outros), (nome, m["criterios"])
        m = medida(medir(montar(d / "tit2", sem_titulo_na=3)), "pdf")
        assert m["detalhe"]["titulos_faltando"] == [{"n": 3, "titulo": titulo(3)}], m["detalhe"]
        m = medida(medir(montar(d / "bom")), "pdf")
        assert m["estado"] == "passou" and m["detalhe"]["fontes_type3"] == [], m
        tam = next(c for c in m["criterios"] if c["nome"] == "tamanho do PDF")
        assert tam["nivel"] == "info" and tam["passou"] is None, tam      # o tamanho nunca reprova (ordem do Ugo)


def test_qa_gravado():
    with Tmp() as d:
        res = medir(montar(d / "falha", qa="falha"))
        assert estado(res, "qa") == "falhou" and medida(res, "qa")["detalhe"]["falhas"] == 1
        assert res["veredito"] == "falhou"
        res = medir(montar(d / "sem", qa=None))                      # sem QA gravado: incompleto, nunca "passou"
        assert estado(res, "qa") == "incompleto" and res["veredito"] == "incompleto" and res["passou"] is None, res["veredito"]
        assert "INCOMPLETO" in res["resumo"]
        assert estado(medir(montar(d / "ok")), "qa") == "passou"


def test_antes_com_paginas_diferentes_avisa_e_nao_quebra():
    with Tmp() as d:
        res = medir(montar(d / "depois"), montar_antes(d / "antes", n_pag=8))
        assert res["avisos"] and "8 páginas" in res["avisos"][0] and "10" in res["avisos"][0], res["avisos"]
        assert res["antes"]["paginas"] == 8 and res["paginas"] == 10
        comp = {c["valor"]: c for c in res["comparacao"]}
        assert comp["estruturas distintas"]["diferenca"] == 3, comp["estruturas distintas"]     # 10 menos 7
        assert comp["mínimo de famílias fora do respiro"]["antes"] is None          # mk-2.0 não declara: sem valor, não zero
        assert estado(res["antes"], "familias_por_pagina") == "nao_se_aplica"
        assert "AVISO" in res["resumo"]


def test_so_le_artefatos():
    """O medir_kit não escreve nada nas pastas que mede (nem no antes)."""
    def foto(p):
        return {str(f): (f.stat().st_size, f.stat().st_mtime_ns) for f in Path(p).rglob("*")}
    with Tmp() as d:
        dep, ant = montar(d / "depois"), montar_antes(d / "antes")
        a0, b0 = foto(dep), foto(ant)
        medir(dep, ant)
        assert foto(dep) == a0 and foto(ant) == b0


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

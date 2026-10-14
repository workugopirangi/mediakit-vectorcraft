#!/usr/bin/env python3
"""
test_composicao.py: provas da composição por página (composicao.py, Fase 0 de 09/10/2026). Sem pytest.

  ~/.venvs/mediakit/bin/python pipeline/test_composicao.py              tudo (unidade + render, alguns minutos)
  ~/.venvs/mediakit/bin/python pipeline/test_composicao.py --unidade    só os testes sem render (segundos)

O teste de render monta um kit temporário da Sprint (clone do APFS, mesma rotina do test_camadas) e apaga no fim.
Sai com 1 se algum teste falhar.
"""
import json, math, shutil, sys, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import composicao, encaixes, qa_geometria, camadas  # noqa: E402
from composicao import ErroComposicao  # noqa: E402

RESULTADOS = []


def teste(fn):
    fn._teste = True
    return fn


def log(*a):
    print("   ", *a, flush=True)


def levanta(fn, trecho):
    try:
        fn()
    except ErroComposicao as e:
        assert trecho in str(e), f"erro sem `{trecho}`: {e}"
        return str(e)
    raise AssertionError(f"não levantou ErroComposicao ({trecho})")


# alvos sintéticos de uma página 1920×1080 (o formato que o JS do camadas.py mede)
def alvos_sinteticos():
    return {
        "pagina": {"x": 0, "y": 0, "w": 1920, "h": 1080},
        "margem": {"x": 96, "y": 96, "w": 1728, "h": 888},
        "colunas": [{"x": 96 + i * 152, "w": 128} for i in range(11)],
        "titulo": {"x": 96, "y": 200, "w": 900, "h": 220,
                   "linhas": [{"x": 96, "y": 200, "w": 900, "h": 110, "linha_base": 290, "cap": 210, "texto": "SUA MARCA"},
                              {"x": 96, "y": 310, "w": 700, "h": 110, "linha_base": 400, "cap": 320, "texto": "NA LARGADA"}],
                   "linha_base": 400, "cap": 210},
        "foto": {"x": 824, "y": 0, "w": 1096, "h": 1080},
        "numero": {"x": 96, "y": 600, "w": 400, "h": 200,
                   "linhas": [{"x": 96, "y": 600, "w": 400, "h": 200, "linha_base": 760, "cap": 620, "texto": "10.000"}]},
    }


def med(alvos=None, W=1920, H=1080):
    return {"w": W, "h": H, "safe": 96, "protegidos": [], "conteudo": [], "opacos": [], "cena": None, "blocos": {},
            "alvos": alvos or alvos_sinteticos(), "avisos": [], "erros_composicao": []}


# elemento de 1000×800 com a área visível (alfa > 8) em (100,100,900,700) e a tinta (alfa ≥ 128) em (150,120,850,680)
DIMS = (1000, 800, (100, 100, 900, 700))
TINTA = (150, 120, 850, 680)


def atrib(ancora, escala=None, **extra):
    a = {"id": "bola", "papel": "heroi", "camada": "frente", "ancora": ancora, "escala": escala or {"altura": "1/4p"},
         "funcao": "foco", "tinta_bbox": TINTA, "origem": "composicao"}
    a.update(extra)
    return a


# ================================================================================================= unidade
@teste
def restricao_parse_e_eixos():
    assert composicao.parse_restricao("esq=titulo.esq") == ("esq", "titulo", None, "esq", 0.0)
    assert composicao.parse_restricao("linha_base=titulo.l2.linha_base-e3") == ("linha_base", "titulo", 2, "linha_base", -24.0)
    assert composicao.parse_restricao("dir=coluna:8.dir+16") == ("dir", "coluna:8", None, "dir", 16.0)
    assert composicao.parse_restricao("topo=cota-cab.base+e5")[4] == 48.0
    levanta(lambda: composicao.parse_restricao("esq=titulo.topo"), "mistura eixos")
    levanta(lambda: composicao.parse_restricao("esquerda=titulo.esq"), "restrição inválida")
    levanta(lambda: composicao.parse_restricao("esq=titulo.esq+e9"), "restrição inválida")
    log("formas válidas, deslocamento em degrau e px, eixo trocado e borda inexistente reprovam")


@teste
def alvo_texto_coluna_e_ausente():
    al = alvos_sinteticos()
    assert composicao.valor_alvo(al, "titulo", None, "linha_base") == 400    # sem linha: a última
    assert composicao.valor_alvo(al, "titulo", None, "cap") == 210           # sem linha: a primeira
    assert composicao.valor_alvo(al, "titulo", 1, "linha_base") == 290
    assert composicao.valor_alvo(al, "titulo", 2, "esq") == 96
    assert composicao.valor_alvo(al, "coluna:3", None, "esq") == 96 + 2 * 152
    assert composicao.valor_alvo(al, "foto", None, "cx") == 824 + 548
    e = levanta(lambda: composicao.valor_alvo(al, "titulo:2", None, "esq"), "ausente")
    assert "titulo" in e     # sugere o que existe
    levanta(lambda: composicao.valor_alvo(al, "foto", None, "linha_base"), "não é texto")
    levanta(lambda: composicao.valor_alvo(al, "titulo", 3, "esq"), "2 linha")
    levanta(lambda: composicao.valor_alvo(al, "coluna:12", None, "esq"), "11 colunas")
    log("linha de base da última linha, cap da primeira, coluna N, alvo ausente com sugestão")


@teste
def escala_em_degraus():
    al = alvos_sinteticos()
    w, h, d = composicao.tamanho_tinta({"altura": "1/3p"}, 700, 560, al, 1920, 1080)
    assert (round(h), round(w), d) == (360, 450, True), (w, h)
    w, h, d = composicao.tamanho_tinta({"largura": "4col"}, 700, 560, al, 1920, 1080)
    assert round(w) == 4 * 128 + 3 * 24 and d, w
    w, h, d = composicao.tamanho_tinta({"altura": "3cap", "de": "titulo"}, 700, 560, al, 1920, 1080)
    assert round(h) == 3 * 80, h                      # cap da 1ª linha: 290 - 210 = 80
    w, h, d = composicao.tamanho_tinta({"altura": 333}, 700, 560, al, 1920, 1080)
    assert h == 333 and d is False                    # px solto é aceito, mas não é degrau (o QA avisa)
    levanta(lambda: composicao.tamanho_tinta({"altura": "2/7p"}, 7, 5, al, 1920, 1080), "fora dos degraus")
    levanta(lambda: composicao.tamanho_tinta({"altura": "1/3p", "largura": "4col"}, 7, 5, al, 1920, 1080), "exatamente uma")
    levanta(lambda: composicao.tamanho_tinta(None, 7, 5, al, 1920, 1080), "sem `escala`")
    log("fração da página, colunas, altura de maiúscula; px solto marcado; fora do degrau reprova")


@teste
def alinha_pela_tinta():
    """A TINTA (alfa ≥ 128) é que encosta: a franja semitransparente fica para fora da linha."""
    it = composicao.resolver(atrib({"relacao": "alinha", "x": "esq=titulo.esq", "y": "base=titulo.cap-e3"}), DIMS, med())
    t = it["ancora"]["tinta"]
    assert abs(t[0] - 96) < 0.11 and abs(t[3] - (210 - 24)) < 0.11, t
    assert abs((t[3] - t[1]) - 270) < 0.11, t                   # 1/4 da página
    s = 270 / (680 - 120)
    assert abs(it["w"] - 800 * s) < 0.11 and abs(it["h"] - 600 * s) < 0.11, it   # caixa do PNG de uso (alfa > 8)
    assert abs(it["x"] - (96 - (150 - 100) * s)) < 0.11, it     # a caixa começa antes da tinta, pela franja
    assert it["encaixe"] == "composicao" and it["origem"] == "composicao" and it["funcao"] == "foco"
    log(f"tinta encosta na margem do título (x={t[0]}) e fica 24 px acima do cap (base={t[3]}); caixa do PNG em x={it['x']}")


@teste
def sangra_e_sobrepoe():
    it = composicao.resolver(atrib({"relacao": "sangra", "borda": "dir", "corte": "1/3", "y": "cy=foto.cy"}), DIMS, med())
    t = it["ancora"]["tinta"]
    tw = t[2] - t[0]
    assert abs((1920 - t[0]) - 2 * tw / 3) < 0.2 and abs((t[1] + t[3]) / 2 - 540) < 0.2, t
    it = composicao.resolver(atrib({"relacao": "sobrepoe", "alvo": "foto", "lado": "esq", "fracao": "1/3", "y": "base=numero.linha_base"}),
                             DIMS, med())
    t = it["ancora"]["tinta"]
    tw = t[2] - t[0]
    assert abs((t[2] - 824) - tw / 3) < 0.2 and abs(t[3] - 760) < 0.2, t
    levanta(lambda: composicao.resolver(atrib({"relacao": "sangra", "borda": "dir", "corte": "1/3"}), DIMS, med()), "falta o eixo `y`")
    levanta(lambda: composicao.resolver(atrib({"relacao": "sangra", "borda": "dir", "corte": "2/5", "y": "cy=foto.cy"}), DIMS, med()), "fora dos degraus")
    log("sangra 1/3 da tinta pela borda direita; sobrepõe 1/3 da tinta dentro da foto; eixo e degrau cobrados")


@teste
def giro_e_espelho():
    a = atrib({"relacao": "alinha", "x": "dir=margem.dir", "y": "topo=titulo.cap"}, rot=90)
    it = composicao.resolver(a, DIMS, med())
    t = it["ancora"]["tinta"]
    assert abs(t[2] - 1824) < 0.2 and abs(t[1] - 210) < 0.2, t
    assert abs((t[2] - t[0]) - 270) < 0.2, t                     # girada 90°: a altura da tinta vira largura
    assimetrica = (150, 120, 800, 680)    # franja de 50 px à esquerda e 100 px à direita da tinta
    sem = composicao.resolver(atrib({"relacao": "alinha", "x": "esq=margem.esq", "y": "topo=margem.topo"}, tinta_bbox=assimetrica), DIMS, med())
    com = composicao.resolver(atrib({"relacao": "alinha", "x": "esq=margem.esq", "y": "topo=margem.topo"}, tinta_bbox=assimetrica, espelhar=True), DIMS, med())
    assert abs(sem["ancora"]["tinta"][0] - 96) < 0.2 and abs(com["ancora"]["tinta"][0] - 96) < 0.2
    assert com["x"] != sem["x"] and com.get("espelhar"), (com["x"], sem["x"])   # a franja muda de lado
    log("giro de 90° alinha a caixa girada da tinta; espelhar troca a franja de lado e a tinta continua na linha")


@teste
def entrada_mais_especifica_e_vertical():
    comp = {"cota": {"mensagem": "tipo"}, "cota:b": {"mensagem": "variante"}, "cota:Master": {"mensagem": "pagina"},
            "vertical:capa": {"mensagem": "vertical"}, "capa": {"mensagem": "capa h"}}
    rots = {"cota", "cota:b", "cota:Master"}
    ch, ent, gch, _ = composicao.entrada_da_pagina(comp, rots, "cota:b", "cota")
    assert (ch, gch) == ("cota:Master", "cota"), (ch, gch)
    ch, _, _, _ = composicao.entrada_da_pagina({"cota": {}, "cota:b": {}}, rots, "cota:b", "cota")
    assert ch == "cota:b", ch
    ch, _, _, _ = composicao.entrada_da_pagina(comp, {"capa", "vertical:capa"}, "vertical:capa", "capa", "vertical")
    assert ch == "vertical:capa", ch
    ch, _, _, _ = composicao.entrada_da_pagina({"capa": {}}, {"capa", "vertical:capa"}, "vertical:capa", "capa", "vertical")
    assert ch is None, "a vertical não herda a composição do horizontal"
    log("página > variante > tipo (o tipo é a gramática); a vertical só usa vertical:*")


@teste
def validacao_estrita():
    ok = {"ativo": {"mensagem": "o objeto sai da foto", "foco": "foto", "elementos": [
        {"id": "bola", "papel": "heroi", "funcao": "profundidade", "camada": "frente", "escala": {"altura": "1/3p"},
         "ancora": {"relacao": "sobrepoe", "alvo": "foto", "lado": "esq", "fracao": "1/3", "y": "base=foto.base-e5"},
         "porque": "a bola sai da foto em direção ao título"},
        {"id": "selo-canto", "grafismo": {"tipo": "etiqueta", "params": {"texto": "x"}}, "papel": "estrutura",
         "funcao": "acabamento", "escala": {"largura": "2col"},
         "ancora": {"relacao": "alinha", "x": "dir=margem.dir", "y": "topo=margem.topo"}, "porque": "assinatura de canto"},
        {"id": "fio", "grafismo": {"tipo": "fio"}, "papel": "estrutura", "funcao": "conexao",
         "ancora": {"relacao": "liga", "modo": "conecta", "de": "numero.dir", "para": "titulo.esq"}, "porque": "liga o número ao título"}]}}
    assert composicao.validar(ok, ["bola"]) == [], composicao.validar(ok, ["bola"])
    def com(mut):
        c = json.loads(json.dumps(ok)); mut(c); return composicao.validar(c, ["bola"])
    e = com(lambda c: c["ativo"]["elementos"][0].update(escalaa={"altura": "1/3p"}))
    assert any("escalaa" in x for x in e), e                                 # chave com erro de digitação
    e = com(lambda c: c["ativo"].update(mensage="x"))
    assert any("mensage" in x for x in e), e
    e = com(lambda c: c["ativo"]["elementos"][1]["ancora"].pop("y"))
    assert any("dois eixos" in x or "'y' is a required" in x for x in e), e
    def so_margem(c):
        el = c["ativo"]["elementos"][1]; el["funcao"] = "foco"
    e = com(so_margem)
    assert any("nenhum eixo preso a conteúdo" in x for x in e), e            # foco preso só na margem
    e = com(lambda c: c["ativo"]["elementos"][0].update(id="nao-existe"))
    assert any("não existe" in x for x in e), e
    e = com(lambda c: c["ativo"]["elementos"][0].pop("escala"))
    assert any("escala" in x for x in e), e
    e = com(lambda c: c["ativo"]["elementos"][0]["ancora"].update(fracao="2/5"))
    assert e, "fração fora do degrau passou"
    log("composição válida passa; erro de digitação, eixo faltando, foco preso só na margem, id inexistente, sem escala e degrau inválido reprovam")


@teste
def resolver_no_encaixes_e_erro_vira_falha():
    cat = {"x": [{"id": "canto", "gerador": "canto", "canto": "sup-dir", "max": [300, 300], "min": [100, 100],
                  "papeis": ["heroi", "apoio"], "camadas": ["frente"]}]}
    m = med()
    dims = {"bola": DIMS, "outra": (400, 400, None)}
    ats = [atrib({"relacao": "alinha", "x": "esq=titulo.esq", "y": "base=titulo.cap-e3"}),
           {"id": "outra", "papel": "apoio", "funcao": "equilibrio", "porque": "contrapeso"},
           dict(atrib({"relacao": "alinha", "x": "esq=nao-tem.esq", "y": "topo=titulo.cap"}), id="bola2")]
    dims["bola2"] = DIMS
    its = encaixes.resolver(ats, "x", cat, m, dims)
    ids = {i["id"]: i for i in its}
    assert set(ids) == {"bola", "outra"}, ids
    assert ids["bola"]["encaixe"] == "composicao" and ids["outra"]["encaixe"] == "canto"
    assert ids["outra"]["funcao"] == "equilibrio" and ids["outra"]["porque"] == "contrapeso", ids["outra"]   # campos novos preservados
    assert m["erros_composicao"] and "nao-tem" in m["erros_composicao"][0], m
    plano = {"largura": 1920, "altura": 1080, "composicao_erros": ["composicao/ativo: x"],
             "paginas": [{"n": 1, "rotulo": "x", "elementos": [], "protegidos": [], "erros_composicao": m["erros_composicao"]}]}
    falhas, _ = qa_geometria.checar_plano(plano, AQUI)
    assert len(falhas) == 2 and any("âncora não resolveu" in f for f in falhas) and any("composição:" in f for f in falhas), falhas
    log(f"âncora resolvida pela composição e o resto pelo catálogo; alvo ausente vira FALHA: {falhas[0][:90]}")


@teste
def precedencia_no_camadas():
    """A composição troca os heróis do plano daquela página; constante fica; `sem` tira; a vertical larga o ancorado."""
    k = {"composicao": {"cota:Master": {"mensagem": "m", "sem": ["constante-selo"], "elementos": [
        {"id": "bola", "papel": "heroi", "funcao": "foco", "escala": {"altura": "1/4p"}, "porque": "teste de precedência",
         "ancora": {"relacao": "alinha", "x": "esq=preco.esq", "y": "base=preco.cap-e3"}}]}}, "elementos": []}
    E = camadas.Elementos.__new__(camadas.Elementos)
    E.composicao, E.k = k["composicao"], k
    paginas = [{"n": 1, "rotulo": "cota:a", "tipo": "cota", "_rotulos": {"cota", "cota:a", "cota:Master"}},
               {"n": 2, "rotulo": "cota:a", "tipo": "cota", "_rotulos": {"cota", "cota:a", "cota:Oficial"}}]
    plano = [{"n": 1, "atribuidos": [{"id": "constante-selo", "papel": "constante"}, {"id": "constante-micro", "papel": "constante"},
                                     {"id": "medalha", "papel": "heroi"}]},
             {"n": 2, "atribuidos": [{"id": "constante-selo", "papel": "constante"}, {"id": "medalha", "papel": "heroi"}]}]
    out, meta = E._aplicar_composicao(plano, paginas, "horizontal")
    assert [a["id"] for a in out[0]["atribuidos"]] == ["constante-micro", "bola"], out[0]
    assert [a["id"] for a in out[1]["atribuidos"]] == ["constante-selo", "medalha"], out[1]
    assert meta[0]["chave"] == "cota:Master" and meta[1] is None
    vert = [{"n": 1, "atribuidos": [dict(out[0]["atribuidos"][1])]}]
    out_v, _ = E._aplicar_composicao(vert, [{"n": 1, "rotulo": "vertical:numeros", "tipo": "cota", "_rotulos": {"cota", "vertical:numeros", "cota:Master"}}], "vertical")
    assert out_v[0]["atribuidos"] == [], out_v
    log("cota:Master: herói do plano trocado pela composição, selo tirado pelo `sem`, microtexto mantido; cota:Oficial intacta; vertical sem o ancorado")


@teste
def planejador_recebe_a_pagina_composta():
    """Costura A×C (integração de 09/10): o render manda ao plano_elementos.planejar quais páginas a composição resolve e
    que heróis ela põe. Sem isso, a página composta ganhava herói automático por baixo e o herói da composição não
    contava nos 3 usos nem na regra de vizinho."""
    comp = {"publico": {"mensagem": "m", "elementos": [
        {"id": "asa", "papel": "heroi", "funcao": "foco", "porque": "teste da costura",
         "ancora": {"relacao": "alinha", "x": "esq=titulo.esq", "y": "base=titulo.cap-e3"}},
        {"id": "fio-x", "papel": "estrutura", "funcao": "conexao", "grafismo": {"tipo": "fio"}, "porque": "teste da costura",
         "ancora": {"relacao": "liga", "modo": "conecta", "de": "pagina.esq", "para": "titulo.esq", "folga": "e3"}}]},
            "manifesto": {"mensagem": "só mensagem, sem elementos"}}
    paginas = [{"n": 1, "rotulo": "capa:a", "tipo": "capa", "_rotulos": {"capa", "capa:a"}},
               {"n": 2, "rotulo": "publico:a", "tipo": "publico", "_rotulos": {"publico", "publico:a"}},
               {"n": 3, "rotulo": "manifesto:a", "tipo": "manifesto", "_rotulos": {"manifesto", "manifesto:a"}}]
    assert camadas.contrato_composicao(comp, paginas[0]) == {}
    assert camadas.contrato_composicao(comp, paginas[1]) == {"composicao": True, "herois_composicao": ["asa"]}
    assert camadas.contrato_composicao(comp, paginas[2]) == {}, "entrada sem `elementos` não conta como composta"
    import plano_elementos
    visto = {}
    original = plano_elementos.planejar
    def espia(sistema, elementos, rid, contrato, catalogo, biblioteca=None):
        visto["contrato"] = contrato
        return [{"n": c["n"], "atribuidos": []} for c in contrato]
    plano_elementos.planejar = espia
    try:
        camadas.planejar({"receitas": {"r1": {}}}, [], "r1", paginas, {}, None, composicao_kit=comp)
    finally:
        plano_elementos.planejar = original
    c = {x["n"]: x for x in visto["contrato"]}
    assert c[2].get("composicao") is True and c[2].get("herois_composicao") == ["asa"], c[2]
    assert "composicao" not in c[1] and "composicao" not in c[3], (c[1], c[3])
    log("página 2 composta com o herói `asa` chega ao planejador; capa e manifesto (só mensagem) seguem como antes")


# ------------------------------------------------------------------------------------------------- liga (Frente A)
CHAMADAS = []


def gerar_falso(tipo, params):
    """Gerador que obedece o contrato de grafismo preso a geometria (references/08): recebe a geometria na página e
    devolve svg, w, h, `origem` (canto do svg na página) e `tinta` (na caixa do svg). Os tipos `fio` e `colchetes` de
    verdade são da Frente B; aqui só a geometria importa. `faixa-medida` honra `largura` com 10 px de respiro de cada
    lado (a tinta é menor que a caixa), como um microtexto."""
    CHAMADAS.append((tipo, json.loads(json.dumps(params))))
    esp = float(params.get("espessura", 2))
    if tipo == "fio":
        xs, ys = [p[0] for p in params["pontos"]], [p[1] for p in params["pontos"]]
        x0, y0 = min(xs) - esp / 2, min(ys) - esp / 2
        w, h = max(xs) - min(xs) + esp, max(ys) - min(ys) + esp
        pts = " ".join(f"{p[0] - x0:.2f},{p[1] - y0:.2f}" for p in params["pontos"])
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.2f}" height="{h:.2f}" viewBox="0 0 {w:.2f} {h:.2f}"><polyline points="{pts}" fill="none" stroke="#D4A64A" stroke-width="{esp}"/></svg>'
        return {"svg": svg, "w": w, "h": h, "texto": "", "fontes": [], "origem": [x0, y0], "tinta": [0, 0, w, h]}
    if tipo == "colchetes":
        x, y, w, h = params["caixa"]
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><path d="M0 0" stroke="#D4A64A"/></svg>'
        return {"svg": svg, "w": w, "h": h, "texto": "", "fontes": [], "origem": [x, y], "tinta": [0, 0, w, h]}
    if tipo == "faixa-medida":
        w, h = float(params.get("largura", 300)), 40.0
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect x="10" y="5" width="{w - 20}" height="30" fill="#D4A64A"/></svg>'
        return {"svg": svg, "w": w, "h": h, "texto": "", "fontes": [], "tinta": [10, 5, w - 10, 35]}
    raise ValueError(f"tipo {tipo} fora do gerador falso")


def med_liga(alvos=None):
    m = med(alvos)
    m["gerar_grafismo"] = gerar_falso
    return m


def liga(id_, **anc):
    return {"id": id_, "papel": "estrutura", "camada": "frente", "funcao": "conexao", "origem": "composicao",
            "ancora": dict(relacao="liga", **anc), "grafismo": {"tipo": composicao.tipo_liga(dict(relacao="liga", **anc))}}


def perto(a, b, tol=0.05):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


@teste
def liga_conecta_posiciona_pela_origem():
    """conecta: ponto da borda + centro do outro eixo; canto com duas bordas; o item fica onde a `origem` do gerador
    manda (sem escala); deslocamento no eixo da borda."""
    its = composicao.resolver_itens(liga("fio", modo="conecta", de="numero.dir", para="titulo.l2.esq"), None, med_liga())
    assert len(its) == 1
    it = its[0]
    p = it["ancora"]["geometria"]["pontos"]
    assert perto(p[0], (496, 700)) and perto(p[1], (96, 365)), p          # numero.dir no cy do número; l2.esq no cy da linha 2
    assert it["x"] == round(96 - 1, 1) and it["y"] == round(365 - 1, 1), it   # origem do gerador (meia espessura)
    assert it["w"] == round(400 + 2, 1) and it["h"] == round(335 + 2, 1), it
    assert it["encaixe"] == "composicao" and it["ancora"]["relacao"] == "liga" and it["_svg"]["origem"] == [95, 364]
    canto = composicao.resolver_itens(liga("f2", modo="conecta", de="titulo.dir.base", para="foto.esq.topo"), None, med_liga())
    assert perto(canto[0]["ancora"]["geometria"]["pontos"][0], (996, 420)) and perto(canto[0]["ancora"]["geometria"]["pontos"][1], (824, 0))
    d = composicao.resolver_itens(liga("f3", modo="conecta", de="numero.dir+e2", para="foto.esq-e2"), None, med_liga())
    assert perto(d[0]["ancora"]["geometria"]["pontos"][0], (512, 700)) and perto(d[0]["ancora"]["geometria"]["pontos"][1], (808, 540))
    levanta(lambda: composicao.resolver_itens(liga("f4", modo="conecta", de="numero.esq.dir", para="titulo.esq"), None, med_liga()), "uma borda de cada eixo")
    levanta(lambda: composicao.resolver_itens(liga("f5", modo="conecta", de="nao-tem.dir", para="titulo.esq"), None, med_liga()), "ausente")
    log(f"numero.dir → titulo.l2.esq: {p}; item na origem do svg ({it['x']}, {it['y']}) {it['w']}×{it['h']}")


@teste
def liga_conecta_borda_herda_eixo_e_folga():
    """Regra do repertório (fio de entrada): `de` na borda da página ou da margem herda a coordenada do outro eixo do
    `para` (horizontal pela esquerda, vertical pelo topo); `folga` abre o vão na ponta `para` e, quando `de` também é
    conteúdo, na ponta `de`."""
    it = composicao.resolver_itens(liga("fio", modo="conecta", de="pagina.esq", para="titulo.esq", folga="e3"), None, med_liga())[0]
    p = it["ancora"]["geometria"]["pontos"]
    assert perto(p[0], (0, 310)) and perto(p[1], (96 - 24, 310)), p        # cy da caixa do título (2 linhas: entrelinha)
    v = composicao.resolver_itens(liga("fio", modo="conecta", de="margem.topo", para="numero.topo"), None, med_liga())[0]
    q = v["ancora"]["geometria"]["pontos"]
    assert perto(q[0], (296, 96)) and perto(q[1], (296, 600)), q            # vertical no cx do número, da margem até ele
    dois = composicao.resolver_itens(liga("fio", modo="conecta", de="numero.dir", para="foto.esq", folga=16), None, med_liga())[0]
    r = dois["ancora"]["geometria"]["pontos"]
    comp = math.hypot(824 - 496, 540 - 700)
    assert abs(math.hypot(r[1][0] - r[0][0], r[1][1] - r[0][1]) - (comp - 32)) < 0.05, r     # vão nas duas pontas
    levanta(lambda: composicao.resolver_itens(liga("fio", modo="conecta", de="numero.dir", para="foto.esq", folga="e8"), None,
                                             med_liga(dict(alvos_sinteticos(), foto={"x": 600, "y": 600, "w": 300, "h": 200}))), "come o fio")
    log(f"pagina.esq → titulo.esq folga e3: {p}; margem.topo → numero.topo: {q}; folga nas duas pontas quando as duas são conteúdo")


@teste
def liga_emoldura_separa_continua():
    """emoldura: colchetes na caixa do alvo (texto: das linhas, cap à linha de base) inflada pela folga; moldura quando
    o grafismo pede. separa: um fio por divisória (empilhados: horizontal; lado a lado: vertical). continua: o ponto
    da foto vai à página pelo object-fit cover + object-position (aqui 30% 50%, não o centro) e o fio corre no ângulo
    até cruzar a borda pedida."""
    em = composicao.resolver_itens(liga("mold", modo="emoldura", alvo="titulo", folga="e2"), None, med_liga())[0]
    assert perto(em["ancora"]["geometria"]["caixa"], (80, 194, 932, 222)), em["ancora"]["geometria"]
    assert em["ancora"]["geometria"]["tipo"] == "colchetes" and (em["x"], em["y"], em["w"], em["h"]) == (80, 194, 932, 222)
    a_mold = dict(liga("mold", modo="emoldura", alvo="numero", folga=8), grafismo={"tipo": "moldura"})
    gm = composicao.geometrias_liga(a_mold["ancora"], alvos_sinteticos(), 1920, 1080, "moldura")[0][2]
    assert gm["largura"] == 400 + 16 and gm["altura"] == (760 - 620) + 16, gm
    al = alvos_sinteticos()
    al["lista-num"] = {"x": 1000, "y": 500, "w": 600, "h": 300,
                       "itens": [{"x": 1000, "y": 500, "w": 600, "h": 80}, {"x": 1000, "y": 600, "w": 580, "h": 80},
                                 {"x": 1000, "y": 700, "w": 600, "h": 100}]}
    al["cards"] = {"x": 96, "y": 820, "w": 1000, "h": 160,
                   "itens": [{"x": 96, "y": 820, "w": 300, "h": 160}, {"x": 420, "y": 820, "w": 300, "h": 150}, {"x": 744, "y": 820, "w": 300, "h": 160}]}
    sep = composicao.resolver_itens(liga("div", modo="separa", entre="lista-num"), None, med_liga(al))
    assert [s["id"] for s in sep] == ["div-s1", "div-s2"], [s["id"] for s in sep]
    assert perto(sep[0]["ancora"]["geometria"]["pontos"][0], (1000, 590)) and perto(sep[0]["ancora"]["geometria"]["pontos"][1], (1600, 590))
    assert perto(sep[1]["ancora"]["geometria"]["pontos"][0], (1000, 690))
    vert = composicao.resolver_itens(liga("div", modo="separa", entre="card"), None, med_liga(al))
    assert len(vert) == 2 and perto(vert[0]["ancora"]["geometria"]["pontos"][0], (408, 820)) and perto(vert[0]["ancora"]["geometria"]["pontos"][1], (408, 980))
    levanta(lambda: composicao.resolver_itens(liga("div", modo="separa", entre="numero"), None, med_liga(al)), "precisa de 2")
    al["foto"] = {"x": 824, "y": 0, "w": 1096, "h": 1080, "img": {"nat_w": 2000, "nat_h": 1000, "fit": "cover", "pos": "30% 50%"}}
    # cover: escala max(1096/2000, 1080/1000) = 1,08 → 2160×1080; sobra -1064 em x; 30% → desloca -319,2
    x0, y0 = composicao.ponto_da_foto(al["foto"], 0.5, 0.5)
    assert abs(x0 - (824 - 319.2 + 1080)) < 0.01 and abs(y0 - 540) < 0.01, (x0, y0)
    x50, _ = composicao.ponto_da_foto(dict(al["foto"], img=dict(al["foto"]["img"], pos="50% 50%")), 0.5, 0.5)
    assert abs(x50 - 1372) < 0.01, x50                                     # o object-position muda o ponto
    co = composicao.resolver_itens(liga("raio", modo="continua", de_foto=[0.5, 0.5], angulo=160, ate="titulo.dir"), None, med_liga(al))[0]
    p = co["ancora"]["geometria"]["pontos"]
    t = (996 - x0) / math.cos(math.radians(160))
    assert perto(p[0], (x0, 540), 0.01) and perto(p[1], (996, 540 - math.sin(math.radians(160)) * t), 0.01), p
    levanta(lambda: composicao.resolver_itens(liga("raio", modo="continua", de_foto=[0.5, 0.5], angulo=180, ate="titulo.dir"), None, med_liga(al)), "fora do alvo")
    levanta(lambda: composicao.resolver_itens(liga("raio", modo="continua", de_foto=[0.5, 0.5], angulo=0, ate="titulo.dir"), None, med_liga(al)), "lado oposto")
    levanta(lambda: composicao.resolver_itens(liga("raio", modo="continua", de_foto=[0.05, 0.5], angulo=160, ate="titulo.dir"), None, med_liga(al)), "fora da área visível")
    log(f"emoldura {em['ancora']['geometria']['caixa']}; separa 3 itens → 2 fios horizontais, 3 cards → 2 verticais; continua "
        f"de ({x0:.1f}, {y0:.0f}) [object-position 30%; no centro seria x={x50:.0f}] até ({p[1][0]:.0f}, {p[1][1]:.1f})")


@teste
def grafismo_gerado_na_medida_da_colocacao():
    """Grafismo ancorado com escala: a escala vira `largura` nos params e o svg nasce nessa medida (sem esticar); se a
    tinta é menor que a caixa, uma correção pede a caixa certa. Com `de` 4col a tinta mede 4 colunas."""
    CHAMADAS.clear()
    a = {"id": "faixa-p3", "papel": "estrutura", "camada": "frente", "funcao": "acabamento", "origem": "composicao",
         "escala": {"largura": "4col"}, "_grafismo": {"tipo": "faixa-medida", "params": {"cor": "marca"}},
         "ancora": {"relacao": "alinha", "x": "esq=titulo.esq", "y": "topo=numero.base+e2"}}
    it = composicao.resolver(a, None, med_liga())
    px = 4 * 128 + 3 * 24
    t = it["ancora"]["tinta"]
    assert abs((t[2] - t[0]) - px) <= 1.0 and abs(t[0] - 96) < 0.11 and abs(t[1] - 816) < 0.11, t
    assert it["ancora"]["medida"] == "gerada" and it["grafismo"]["params"]["largura"] > px, it["grafismo"]
    assert [c[0] for c in CHAMADAS] == ["faixa-medida", "faixa-medida"] and CHAMADAS[0][1]["largura"] == px, CHAMADAS
    assert it["w"] == round(it["_svg"]["w"], 1), (it["w"], it["_svg"]["w"])     # escala 1: a caixa é a do svg gerado
    levanta(lambda: composicao.resolver(dict(a, _grafismo={"tipo": "nao-existe"}), None, med_liga()), "não gerou")
    log(f"4col = {px} px de tinta: gerado com largura {CHAMADAS[0][1]['largura']}, corrigido para {it['grafismo']['params']['largura']}; "
        f"tinta {t[2] - t[0]:.1f} px; {len(CHAMADAS)} chamadas ao gerador")


# ------------------------------------------------------------------------------------------------- QA da composição
def pagina_qa(itens, alvos=None, n=1, dom=True, **extra):
    """Página de plano com os alvos sintéticos e o DOM igual ao plano (caixa alinhada aos eixos de cada item)."""
    pg = {"n": n, "rotulo": "ativo:painel", "elementos": itens, "protegidos": [], "erros_composicao": [],
          "alvos": alvos if alvos is not None else alvos_sinteticos()}
    if dom:
        pg["dom"] = [dict(zip(("x", "y", "w", "h"), qa_geometria._aabb(it)), id=it["id"]) for it in itens]
    pg.update(extra)
    return pg


def plano_qa(paginas, comp=True):
    return {"largura": 1920, "altura": 1080, "composicao_kit": comp, "paginas": paginas, "composicao_erros": []}


def desloca(it, dx, dy):
    j = json.loads(json.dumps(it))
    j["x"] += dx; j["y"] += dy
    t = j["ancora"]["tinta"]
    j["ancora"]["tinta"] = [t[0] + dx, t[1] + dy, t[2] + dx, t[3] + dy]
    return j


@teste
def qa_ancora_limites_eixos_e_dom():
    """Âncora conferida contra os alvos do render FINAL: 1 px passa, 3 px reprova; cada eixo é conferido sozinho (rente
    só no x não passa); alvo que mudou depois da resolução reprova; DOM diferente do plano em mais de 1 px reprova."""
    it = composicao.resolver(atrib({"relacao": "alinha", "x": "esq=titulo.esq", "y": "base=titulo.cap-e3"}), DIMS, med())
    roda = lambda pg: qa_geometria.checar_plano(plano_qa([pg]), AQUI)
    f, a = roda(pagina_qa([it]))
    assert not f and not a, (f, a)
    for dx, dy in ((1, 0), (-1, 1), (0, -1)):
        f, _ = roda(pagina_qa([desloca(it, dx, dy)]))
        assert not f, (dx, dy, f)
    f, _ = roda(pagina_qa([desloca(it, 3, 0)]))
    assert len(f) == 1 and "esq=titulo.esq" in f[0] and "+3.0 px" in f[0], f
    f3y, _ = roda(pagina_qa([desloca(it, 0, -3)]))
    assert len(f3y) == 1 and "base=titulo.cap-e3" in f3y[0] and "-3.0 px" in f3y[0], f3y      # rente só no x: o y acusa
    al = alvos_sinteticos()
    al["titulo"]["linhas"][0]["cap"] += 3                                                    # o título desceu no render final
    f, _ = roda(pagina_qa([it], al))
    assert len(f) == 1 and "base=titulo.cap-e3" in f[0], f
    pg = pagina_qa([it])
    pg["dom"][0]["x"] += 2
    f, _ = roda(pg)
    assert len(f) == 1 and "desenhado em" in f[0], f                                          # 2 px no DOM: só a regra do DOM
    pg["dom"] = []
    f, _ = roda(pg)
    assert any("não está no DOM" in x for x in f), f
    log(f"1 px passa; 3 px: {f3y[0][:110]}")


@teste
def qa_layout_centrado():
    """Elemento centrado no eixo do título (cx=titulo.cx) resolve, passa na âncora e não é solto."""
    it = composicao.resolver(atrib({"relacao": "alinha", "x": "cx=titulo.cx", "y": "topo=numero.base+e3"}), DIMS, med())
    t = it["ancora"]["tinta"]
    assert abs((t[0] + t[2]) / 2 - 546) < 0.11 and abs(t[1] - 824) < 0.11, t
    f, a = qa_geometria.checar_plano(plano_qa([pagina_qa([it])]), AQUI)
    assert not f and not a, (f, a)
    log(f"eixo da tinta em x={(t[0] + t[2]) / 2:.1f} (titulo.cx = 546), topo 24 px abaixo do número; 0 falha, 0 aviso")


@teste
def qa_embaralhado_vira_solto():
    """40 elementos do catálogo em posições sorteadas (semente fixa): o QA chama de solto exatamente os que não têm
    nenhuma borda nem eixo a 2 px de uma linha de conteúdo (conferido por fora, borda a borda), e os mesmos elementos
    presos ao título e ao número não são soltos."""
    import random
    rnd = random.Random(20261009)
    xs, ys = qa_geometria.linhas_de_referencia(alvos_sinteticos())
    pags, esperado = [], set()
    for i in range(40):
        w, h = rnd.uniform(180, 300), rnd.uniform(180, 300)
        x, y = rnd.uniform(20, 1920 - w - 20), rnd.uniform(20, 1080 - h - 20)
        it = {"id": f"e{i}", "papel": "heroi", "camada": "frente", "x": round(x, 1), "y": round(y, 1), "w": round(w, 1),
              "h": round(h, 1), "rot": 0, "formato": "svg", "encaixe": "maior-vazio"}
        bordas_x = (it["x"], it["x"] + it["w"] / 2, it["x"] + it["w"])
        bordas_y = (it["y"], it["y"] + it["h"] / 2, it["y"] + it["h"])
        if not any(abs(b - l) <= 2 for b in bordas_x for l in xs) and not any(abs(b - l) <= 2 for b in bordas_y for l in ys):
            esperado.add(it["id"])
        pags.append(pagina_qa([it], n=i + 1))
    _, avisos = qa_geometria.checar_plano(plano_qa(pags, comp=False), AQUI)
    soltos = {a.split("`")[1] for a in avisos if " solto:" in a}
    assert soltos == esperado, (sorted(soltos ^ esperado))
    assert len(soltos) >= 24, len(soltos)
    presos = []
    for i in range(8):
        a = atrib({"relacao": "alinha", "x": rnd.choice(["esq=titulo.esq", "dir=numero.dir", "cx=titulo.l2.cx"]),
                   "y": rnd.choice(["topo=numero.base+e2", "base=titulo.cap-e3", "cy=foto.cy"])}, id=f"p{i}")
        presos.append(pagina_qa([composicao.resolver(a, DIMS, med())], n=i + 1))
    _, av2 = qa_geometria.checar_plano(plano_qa(presos), AQUI)
    assert not [a for a in av2 if " solto:" in a], av2
    log(f"{len(soltos)} de 40 sorteados acusados como soltos (os {40 - len(soltos)} restantes têm uma borda a ≤ 2 px de "
        f"uma linha de conteúdo, conferido por fora); 8 presos por âncora: nenhum solto")


@teste
def qa_catalogo_sem_ancora_constante_confete_e_degrau():
    """Herói do catálogo sem âncora: FALHA em kit com composição, AVISO no legado. Constante fora da caixa única
    (3 px numa página): FALHA; 2 px: passa. Confete (tinta < 1,5% da página, função fora de organização e acabamento)
    e escala fora do degrau: AVISO."""
    cat = {"id": "h", "papel": "heroi", "camada": "frente", "x": 1400, "y": 96, "w": 420, "h": 420, "rot": 0,
           "formato": "svg", "encaixe": "canto-sup-dir"}
    f, _ = qa_geometria.checar_plano(plano_qa([pagina_qa([cat])], comp=True), AQUI)
    assert len(f) == 1 and "veio do catálogo" in f[0] and "escreva a composição" in f[0], f
    f, a = qa_geometria.checar_plano(plano_qa([pagina_qa([cat])], comp=False), AQUI)
    assert not f and any("veio do catálogo" in x for x in a), (f, a)
    selo = lambda n, dx=0.0: pagina_qa([{"id": "constante-selo", "papel": "constante", "camada": "frente", "x": 1674 + dx,
                                         "y": 834, "w": 150, "h": 150, "rot": 0, "formato": "svg", "encaixe": "selo-inf-dir"}], n=n)
    f, _ = qa_geometria.checar_plano(plano_qa([selo(1), selo(2, 2), selo(3, -1)]), AQUI)
    assert not f, f
    f, _ = qa_geometria.checar_plano(plano_qa([selo(1), selo(2, 3), selo(3)]), AQUI)
    assert len(f) == 1 and "fora da caixa única" in f[0] and "fora dela: p.2" in f[0], f
    peq = composicao.resolver(atrib({"relacao": "alinha", "x": "esq=titulo.esq", "y": "topo=numero.base+e2"},
                                    escala={"altura": 120}), DIMS, med())
    _, a = qa_geometria.checar_plano(plano_qa([pagina_qa([peq])]), AQUI)
    assert any("confete" in x for x in a) and any("fora do degrau" in x for x in a), a
    org = dict(peq, funcao="organizacao")
    _, a = qa_geometria.checar_plano(plano_qa([pagina_qa([org])]), AQUI)
    assert not any("confete" in x for x in a), a
    # o mesmo herói do catálogo em 2 tamanhos (560 e 284 px, como na Sprint): aviso; na composição em degrau: não
    h560, h284 = dict(cat, w=560, h=327), dict(cat, w=284, h=166, x=1500)
    _, a = qa_geometria.checar_plano(plano_qa([pagina_qa([h560], n=1), pagina_qa([h284], n=2)], comp=False), AQUI)
    assert any("`h` em 2 tamanhos" in x and "560×327 (p.1)" in x for x in a), a
    g1 = composicao.resolver(atrib({"relacao": "alinha", "x": "esq=titulo.esq", "y": "base=titulo.cap-e3"}), DIMS, med())
    g2 = composicao.resolver(atrib({"relacao": "alinha", "x": "esq=titulo.esq", "y": "base=titulo.cap-e3"}, escala={"altura": "1/3p"}), DIMS, med())
    _, a = qa_geometria.checar_plano(plano_qa([pagina_qa([g1], n=1), pagina_qa([g2], n=2)]), AQUI)
    assert not any("tamanhos" in x for x in a), a
    log(f"catálogo: FALHA com composição, AVISO no legado; selo 2 px passa, 3 px: {f[0][:90]}...; confete e degrau avisam")


@teste
def qa_vendavel_e_mascara_da_liga():
    """Elemento que cobre mais de 2% de um painel vendável (quad da foto) reprova; 1% passa. A liga conta só o traço:
    colchetes em volta do título não cobrem o título (a caixa cheia cobriria 100%)."""
    zona = {"classe": "vendavel", "x": 1000, "y": 300, "w": 400, "h": 100, "texto": "SEU LOGO AQUI", "fonte": "compor-x.json#1",
            "quad": [[1000, 300], [1400, 300], [1400, 400], [1000, 400]]}
    def h(x):
        return {"id": "h", "papel": "heroi", "camada": "frente", "x": x, "y": 250, "w": 200, "h": 200, "rot": 0,
                "formato": "svg", "encaixe": "sobre-cena"}
    f, _ = qa_geometria.checar_plano(plano_qa([pagina_qa([h(1400 - 12)], vendaveis=[zona])], comp=False), AQUI)
    assert len(f) == 1 and "zona vendável" in f[0] and "3%" in f[0], f       # 12 px de largura × 100 de 400 × 100 = 3%
    f, _ = qa_geometria.checar_plano(plano_qa([pagina_qa([h(1400 - 4)], vendaveis=[zona])], comp=False), AQUI)
    assert not f, f                                                           # 4 px × 100 = 1%
    em = composicao.resolver_itens(liga("mold", modo="emoldura", alvo="titulo", folga="e2"), None, med_liga())[0]
    em.pop("_svg"); em["formato"] = "svg"
    linhas = [dict(l, classe="titulo") for l in alvos_sinteticos()["titulo"]["linhas"]]
    f, _ = qa_geometria.checar_plano(plano_qa([pagina_qa([em], protegidos=linhas)]), AQUI)
    assert not f, f
    cheia = json.loads(json.dumps(em)); cheia["ancora"].pop("geometria")
    f, _ = qa_geometria.checar_plano(plano_qa([pagina_qa([cheia], protegidos=linhas)]), AQUI)
    assert f and "cobre titulo" in f[0], f
    log("painel: 3% reprova, 1% passa; colchetes em volta do título: o traço não cobre a linha (a caixa cheia cobriria)")


@teste
def qa_atras_do_titulo_vale_o_contraste():
    """Elemento na camada atras sob a linha do título: passa se o texto, amostrado no PNG, continua com 3:1; reprova se
    o contraste cai ou se não há PNG deste render."""
    from PIL import Image, ImageDraw
    import tempfile
    d = Path(tempfile.mkdtemp(prefix="qa-contraste-"))
    try:
        linha = {"classe": "titulo", "x": 200, "y": 300, "w": 800, "h": 120, "texto": "SUA MARCA"}
        def png(fundo_el):
            im = Image.new("RGB", (1920, 1080), (17, 17, 17))
            dr = ImageDraw.Draw(im)
            dr.rectangle([150, 250, 650, 470], fill=fundo_el)                  # o elemento atrás (metade da linha)
            for k in range(10):                                                # "letras" brancas na linha
                dr.rectangle([210 + k * 78, 320, 250 + k * 78, 400], fill=(255, 255, 255))
            p = d / f"p-{fundo_el[0]}.png"; im.save(p); return p
        el = {"id": "folha", "papel": "heroi", "camada": "atras", "x": 150, "y": 250, "w": 500, "h": 220, "rot": 0,
              "formato": "svg", "encaixe": "atras-de"}
        textos = [{"x": 200, "y": 300, "w": 800, "h": 120, "cor": "#FFFFFF", "fs": 96}]
        base = plano_qa([pagina_qa([el], protegidos=[linha])], comp=False)
        escuro, claro = png((70, 70, 70)), png((225, 225, 225))
        f, a = qa_geometria.checar_plano(base, d, png=lambda n: escuro, textos=lambda n: textos)
        assert not f and any("continua com contraste" in x for x in a), (f, a)
        f, _ = qa_geometria.checar_plano(base, d, png=lambda n: claro, textos=lambda n: textos)
        assert len(f) == 1 and "o contraste cai" in f[0], f
        f, _ = qa_geometria.checar_plano(base, d)
        assert len(f) == 1 and "sem PNG" in f[0], f
        frente = plano_qa([pagina_qa([dict(el, camada="frente")], protegidos=[linha])], comp=False)
        f, _ = qa_geometria.checar_plano(frente, d, png=lambda n: escuro, textos=lambda n: textos)
        assert len(f) == 1 and "cobre titulo" in f[0], f                      # na frente a cobertura reprova sempre
        log(f"atrás de título: fundo cinza-escuro passa ({[x for x in a if 'contraste' in x][0].split('contraste ')[1][:6]}); "
            f"fundo claro reprova; sem PNG reprova; na frente reprova")
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ------------------------------------------------------------------------------------------------- camadas (Frente A)
CAT_SELO = {"p": [{"id": "selo-inf-dir", "gerador": "canto", "canto": "inf-dir", "max": [150, 150], "min": [112, 112],
                   "papeis": ["constante"], "camadas": ["frente"]},
                  {"id": "selo-sup-esq", "gerador": "canto", "canto": "sup-esq", "max": [150, 150], "min": [112, 112],
                   "papeis": ["constante"], "camadas": ["frente"]}]}


def elementos_parcial(sistema, catalogo):
    E = camadas.Elementos.__new__(camadas.Elementos)
    E.sistema, E.catalogo, E.erros_composicao, E.els, E.k, E._svgs = sistema, catalogo, [], {}, {}, {}
    return E


@teste
def constante_caixa_unica_maioria_e_ancora():
    """A caixa única da constante: sem âncora, a caixa do catálogo que serve a MAIS páginas (aqui a da p.2, que serve 3;
    a da p.1, "a primeira onde coube", serviria 1); na página onde ela bate em texto a constante sai com aviso, nunca
    muda de lugar. Com âncora (só alvos estruturais), a caixa vem dela."""
    prot_inf_dir = {"classe": "corpo", "x": 1500, "y": 900, "w": 300, "h": 40, "texto": "rodapé"}
    prot_sup_esq = {"classe": "titulo", "x": 120, "y": 120, "w": 300, "h": 80, "texto": "TÍTULO"}
    def m(prot):
        return {"protegidos": prot, "conteudo": [], "opacos": [], "cena": None, "blocos": {}, "alvos": alvos_sinteticos()}
    medidas = [m([prot_inf_dir]), m([prot_sup_esq]), m([prot_sup_esq]), m([prot_sup_esq])]
    paginas = [{"n": i + 1, "rotulo": "p", "tipo": "x", "_rotulos": {"x"}} for i in range(4)]
    sel = {"id": "constante-selo", "papel": "constante", "svg": True, "encaixes_preferidos": ["selo-inf-dir", "selo-sup-esq"]}
    E = elementos_parcial({"constantes": [{"tipo": "selo", "texto": "x"}]}, CAT_SELO)
    dims = {"constante-selo": (150, 150, None)}
    cx, av = E._caixas_unicas([[dict(sel)] for _ in paginas], paginas, medidas, dims, 1920, 1080, [[]] * 4)
    c = cx["constante-selo"]
    assert (c["x"], c["y"], c["encaixe"], c["de"]) == (1674.0, 834.0, "selo-inf-dir", "p.2"), c   # encostado no canto
    atrib = [{"n": p["n"], "atribuidos": [dict(sel)]} for p in paginas]
    itens, av_pag, _, _, _ = E._resolver(atrib, paginas, medidas, dims, {"constante-selo": {"svg": "<svg/>", "w": 150, "h": 150}},
                                          1920, 1080, maquete=True)
    assert itens[0] == [] and "fora desta página" in av_pag[0][0] and "rodapé" in av_pag[0][0], (itens[0], av_pag[0])
    caixas = {(it["x"], it["y"], it["w"], it["h"]) for res in itens[1:] for it in res}
    assert caixas == {(1674.0, 834.0, 150, 150)}, caixas
    E2 = elementos_parcial({"constantes": [{"tipo": "selo", "texto": "x",
                                            "ancora": {"relacao": "alinha", "x": "dir=margem.dir", "y": "topo=margem.topo"}}]}, CAT_SELO)
    cx2, _ = E2._caixas_unicas([[dict(sel)] for _ in paginas], paginas, medidas, dims, 1920, 1080, [[]] * 4)
    assert (cx2["constante-selo"]["x"], cx2["constante-selo"]["y"], cx2["constante-selo"]["de"]) == (1674.0, 96.0, "ancora"), cx2
    assert composicao.validar_constantes({"constantes": [{"tipo": "selo", "ancora": {"relacao": "alinha", "x": "dir=titulo.dir",
                                                                                     "y": "topo=margem.topo"}}]}), "alvo de conteúdo passou"
    # encaixe declarado na constante é a posição dela: com o inferior direito tomado nas p.2 a 4, a caixa vem do inferior
    # direito da p.1 (as outras perdem o selo), nunca do superior esquerdo que estava livre
    medidas_b = [m([]), m([prot_inf_dir]), m([prot_inf_dir]), m([prot_inf_dir])]
    E3 = elementos_parcial({"constantes": [{"tipo": "selo", "texto": "x", "encaixe": "selo-inf-dir"}]}, CAT_SELO)
    cx3, _ = E3._caixas_unicas([[dict(sel)] for _ in paginas], paginas, medidas_b, dims, 1920, 1080, [[]] * 4)
    assert (cx3["constante-selo"]["encaixe"], cx3["constante-selo"]["de"]) == ("selo-inf-dir", "p.1"), cx3
    log(f"caixa da p.2 (serve 3 de 4 páginas) em ({c['x']:.0f}, {c['y']:.0f}); p.1 sem selo: {av_pag[0][0][:80]}...; "
        f"com âncora: ({cx2['constante-selo']['x']:.0f}, {cx2['constante-selo']['y']:.0f})")


@teste
def zonas_da_foto_painel_e_foco():
    """O painel do compor.py (quad em px da imagem) e o foco do acervo vão à página pelo object-fit cover + object-position
    da foto medida (aqui 30% 50%); a foto do DOM acha o acervo pela impressão digital do src; o encaixe sobre a cena
    desvia da zona (sem ela, o herói ia justo para o canto do painel)."""
    import tempfile
    d = Path(tempfile.mkdtemp(prefix="zonas-"))
    try:
        (d / "compor-x.json").write_text(json.dumps([{"quad": [600, 50, 900, 50, 900, 150, 600, 150], "texto": "SEU LOGO|AQUI"},
                                                     {"quad": [10, 10, 60, 10, 60, 40, 10, 40], "texto": "fora"}]), encoding="utf-8")
        src = "data:image/jpeg;base64," + "Q" * 300 + "fim-da-imagem-c1"
        pags = [{"cena": {"id": "c1", "src": src, "paineis": "compor-x.json", "foco": "30% 40%"}}]
        foto = {"x": 824, "y": 0, "w": 1096, "h": 1080,
                "img": {"nat_w": 2000, "nat_h": 1000, "fit": "cover", "pos": "30% 50%", "chave": camadas.chave_foto(src)}}
        zs = camadas.zonas_da_foto(pags, [{"alvos": {"foto": foto, "foto:1": foto}}], d, [])[0]
        assert len(zs) == 2, zs                                           # o painel fora da área visível não entra
        p, f = zs
        # cover: 2160×1080, começa em x = 824 - 319,2 = 504,8; u = 600/2000 → 504,8 + 648 = 1152,8
        assert abs(p["x"] - 1152.8) < 0.11 and abs(p["w"] - 324) < 0.11 and abs(p["y"] - 54) < 0.11 and abs(p["h"] - 108) < 0.11, p
        assert p["texto"] == "SEU LOGO AQUI" and p["fonte"] == "compor-x.json#1" and len(p["quad"]) == 4
        assert abs(f["x"] + f["w"] / 2 - 1152.8) < 0.2 and abs(f["y"] + f["h"] / 2 - 432) < 0.2 and abs(f["w"] - 1096 / 3) < 0.2, f
        outra = dict(foto, img=dict(foto["img"], chave="0:outra"))
        assert camadas.zonas_da_foto(pags, [{"alvos": {"foto": outra}}], d, [])[0] == []
        cat = encaixes.carregar_catalogo()
        cena = {"x": 960, "y": 0, "w": 960, "h": 1080}
        zona = {"classe": "vendavel", "x": 1400, "y": 96, "w": 424, "h": 300, "texto": "SEU LOGO AQUI"}
        base = {"protegidos": [], "conteudo": [], "opacos": [], "cena": cena, "blocos": {}, "w": 1920, "h": 1080, "safe": 96, "avisos": []}
        h = {"id": "h", "papel": "heroi", "encaixes_preferidos": ["sobre-cena"], "camada": "frente"}
        sem = encaixes.resolver([dict(h)], "ativo:painel", cat, dict(base), {"h": (1200, 1200, None)})[0]
        com = encaixes.resolver([dict(h)], "ativo:painel", cat, dict(base, vendaveis=[zona]), {"h": (1200, 1200, None)})[0]
        cruza = lambda it: min(it["x"] + it["w"], 1824) > max(it["x"], 1400) and min(it["y"] + it["h"], 396) > max(it["y"], 96)
        assert cruza(sem) and not cruza(com), (sem, com)
        log(f"painel em ({p['x']}, {p['y']}) {p['w']}×{p['h']}; foco centrado em ({f['x'] + f['w'] / 2:.1f}, {f['y'] + f['h'] / 2:.0f}); "
            f"herói sem a zona em ({sem['x']:.0f}, {sem['y']:.0f}), com a zona em ({com['x']:.0f}, {com['y']:.0f})")
    finally:
        shutil.rmtree(d, ignore_errors=True)


@teste
def acabamento_da_frente_no_png_de_uso():
    """Camada frente: o PNG de uso recebe o grão do tema (soft-light na opacidade da página) e o tingir da receita, no
    raster; o alfa não muda; outro arquivo (sufixo do acabamento) e o cache reaproveita. Atrás, o mesmo elemento sai sem
    acabamento (a página aplica)."""
    import tempfile
    import numpy as np
    from PIL import Image, ImageDraw
    d = Path(tempfile.mkdtemp(prefix="acab-"))
    try:
        import test_camadas as tc
        foto = tc.SPRINT / "acervo" / "elementos" / "medalha-alada.png"     # foto-objeto: sem redução de cores (só leitura)
        bbox, dims_ = camadas.alfa_bbox(foto)
        el = {"id": "obj", "caminho": foto, "dims": dims_, "alfa_bbox": bbox, "sha256": camadas._sha256(foto)}
        _, d0, _ = camadas.preparar_uso(el, 300, d / "cache", d, [])
        ac = {"grao": {"arquivo": str(camadas.GRAO_TEMA), "opacidade": 0.5, "blend": "soft-light", "tile": 512}}
        r1, d1, _ = camadas.preparar_uso(el, 300, d / "cache", d, [], ac)
        assert d1 != d0 and d1.name.endswith(f"-{camadas.chave_acabamento(ac)}.png"), (d0.name, d1.name)
        a0, a1 = (np.asarray(Image.open(x).convert("RGBA")).astype(int) for x in (d0, d1))
        assert (a0[..., 3] == a1[..., 3]).all(), "o grão mexeu no alfa"
        cheio = a0[..., 3] == 255
        dif = np.abs(a1[..., :3] - a0[..., :3])[cheio]
        assert 1.0 < dif.mean() < 12 and dif.max() < 80, (dif.mean(), dif.max())
        # a mesma conta do CSS (W3C soft-light, opacidade 0,5) em TODO pixel cheio, com o tile do grão na escala do PNG
        # (largura do PNG / largura de uso); sem redução de cores (o objeto é foto), a conta tem de bater no arredondamento
        idx = json.loads((d / "cache" / "indice.json").read_text(encoding="utf-8"))
        assert idx[d1.name]["cores"] is None, idx[d1.name]
        lado = int(round(512 * a0.shape[1] / 300.0))
        g = np.asarray(Image.open(camadas.GRAO_TEMA).convert("L").resize((lado, lado), Image.BILINEAR), dtype=float) / 255
        cs = np.tile(g, (a0.shape[0] // lado + 1, a0.shape[1] // lado + 1))[:a0.shape[0], :a0.shape[1]][..., None]
        cb = a0[..., :3] / 255.0
        esperado = (cb + (camadas._misturar_blend(cb, cs, "soft-light") - cb) * 0.5) * 255
        erro = np.abs(esperado - a1[..., :3])[cheio]
        assert erro.max() <= 1.01, erro.max()
        t0 = d1.stat().st_mtime_ns
        camadas.preparar_uso(el, 300, d / "cache", d, [], ac)
        assert d1.stat().st_mtime_ns == t0, "regravou sem precisar"
        idx = json.loads((d / "cache" / "indice.json").read_text(encoding="utf-8"))
        assert idx[d1.name]["versao"] == camadas.VERSAO_USO == 3 and idx[d1.name]["acabamento"] == camadas.chave_acabamento(ac)
        _, d2, _ = camadas.preparar_uso(el, 300, d / "cache", d, [], {"tingir": {"cor": "#2067AA", "forca": 0.9, "preto": 0.04}})
        a2 = np.asarray(Image.open(d2).convert("RGBA")).astype(int)
        azul = lambda a: float((a[..., 2] - a[..., 0])[cheio].mean())      # azul menos vermelho: o matiz do duotone
        assert azul(a2) > azul(a0) + 50, (azul(a0), azul(a2))
        E = elementos_parcial(None, {})
        E.els = {"obj": dict(el, formato="png")}
        E.cache, E.pasta = d / "cache2", d
        itens = [[{"id": "obj", "papel": "heroi", "camada": "frente", "x": 0, "y": 0, "w": 300, "h": 300, "rot": 0}],
                 [{"id": "obj", "papel": "heroi", "camada": "atras", "x": 0, "y": 0, "w": 300, "h": 300, "rot": 0}]]
        prontos = E._preparar(itens, [], [{"grao": {"opacidade": 0.5, "blend": "soft-light", "tamanho": "512px 512px"}}] * 2, None)
        chaves = sorted(prontos, key=lambda k: k[1] or "")
        assert len(prontos) == 2 and chaves[0] == ("obj", None) and itens[0][0].get("acabamento") and "acabamento" not in itens[1][0], prontos.keys()
        log(f"grão na frente: Δ médio {dif.mean():.1f} em 255 (máx {int(dif.max())}), alfa intacto, igual à conta do CSS em todo "
            f"pixel cheio (erro máx {erro.max():.2f}); {d1.name}; atrás: sem acabamento")
    finally:
        shutil.rmtree(d, ignore_errors=True)


@teste
def maquete_caixa_rotulada():
    """A maquete troca o elemento por caixa hachurada na cor da função, com rótulo `id · função · relação→alvo`, no lugar
    resolvido; a liga sai como a própria geometria tracejada; asset planejado entra pela proporção."""
    it = composicao.resolver(atrib({"relacao": "alinha", "x": "esq=titulo.esq", "y": "base=titulo.cap-e3"}, proporcao=[4, 3],
                                   tinta_bbox=None), (4000, 3000, None), med())
    assert (it["w"], it["h"]) == (360.0, 270.0), it                      # 1/4 da página de altura, 4:3
    h = camadas.html_maquete(it)
    assert 'data-elemento="bola"' in h and "bola · foco · alinha→titulo" in h and "repeating-linear-gradient" in h, h
    assert f"left:{camadas._num(it['x'])}px" in h and camadas.COR_FUNCAO["foco"] in h
    li = composicao.resolver_itens(liga("fio", modo="conecta", de="pagina.esq", para="titulo.esq", folga="e3"), None, med())[0]
    hl = camadas.html_maquete(li)
    assert "<polyline" in hl and "liga conecta→pagina,titulo" in hl and "fio · conexao" in hl, hl
    E = elementos_parcial(None, {})
    E.els, E.k = {}, {}
    atr = [{"n": 1, "atribuidos": [{"id": "planejado", "papel": "heroi", "ancora": {"relacao": "alinha"}, "escala": {"altura": "1/3p"},
                                     "proporcao": [3, 2]}]}]
    dims, _ = E._dims_e_svgs(atr, {}, [], maquete=True)
    assert dims["planejado"] == (3000.0, 2000.0, None), dims
    dims2, _ = E._dims_e_svgs(atr, {}, [], maquete=False)
    assert "planejado" not in dims2                                       # fora da maquete: sem asset, a âncora acusa
    log(f"caixa em ({it['x']}, {it['y']}) {it['w']}×{it['h']} com rótulo 'bola · foco · alinha→titulo'; liga tracejada; "
        f"asset planejado 3:2 só na maquete")


PLANO_SPRINT_R1 = Path("/Users/ugopirangi/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/SPRINT UBATUBA RUN/"
                       "MEDIAKIT/sprint-2027/saida/plano-elementos-r1.json")
COMMIT_QA_FASE0 = "1f4a63e"      # qa_geometria.py da Fase 0: o QA que deu 0 falhas no plano da Sprint


@teste
def qa_caso_real_sprint_r1():
    """O plano atual da Sprint r1 (copiado para uma pasta temporária; o original só é lido) passou com 0 falhas no QA da
    Fase 0 e o dono ainda achou os elementos soltos. O QA novo acusa: selo em 2 cantos e 4 alturas e microtexto em 4
    alturas (constante fora da caixa única, FALHA) e o mesmo herói em 2 tamanhos (escala, AVISO)."""
    import subprocess, tempfile, importlib.util
    d = Path(tempfile.mkdtemp(prefix="qa-sprint-"))
    try:
        shutil.copy(PLANO_SPRINT_R1, d / "plano-elementos-r1.json")
        plano = json.loads((d / "plano-elementos-r1.json").read_text(encoding="utf-8"))
        # antes: o qa_geometria do commit da Fase 0, sobre o mesmo plano
        import test_camadas as tc
        velho = d / "qa_geometria_fase0.py"
        raiz = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True,
                                   cwd=str(AQUI)).stdout.strip())
        rel = (AQUI / "qa_geometria.py").resolve().relative_to(raiz.resolve()).as_posix()
        velho.write_text(subprocess.run(["git", "show", f"{COMMIT_QA_FASE0}:{rel}"], capture_output=True, text=True, check=True,
                                        cwd=str(AQUI)).stdout, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("qa_geometria_fase0", velho)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        f0, _ = mod.checar_plano(plano, tc.SPRINT, "r1")
        assert f0 == [], f0
        f, a = qa_geometria.checar_plano(plano, tc.SPRINT, "r1")
        selo = [x for x in f if "constante-selo" in x]
        micro = [x for x in f if "constante-microtexto" in x]
        assert selo and "2 cantos" in selo[0] and "4 alturas" in selo[0] and "fora da caixa única" in selo[0], f
        assert micro and "4 alturas" in micro[0] and "fora da caixa única" in micro[0], f
        heroi = [x for x in a if "`asa-gravura` em 2 tamanhos" in x]
        assert heroi and "560×327" in heroi[0] and "284×166" in heroi[0], a
        log(f"Fase 0: {len(f0)} falhas. Agora: {len(f)} falhas e {len(a)} avisos")
        log(selo[0][:200])
        log(micro[0][:160])
        log(heroi[0][:120])
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ================================================================================================= render
def _alvo_valor(alvos, txt):
    b, alvo, linha, ba, desl = composicao.parse_restricao(txt)
    return b, composicao.valor_alvo(alvos, alvo, linha, ba) + desl


@teste
def esqueleto_em_todo_arquetipo():
    """Fase 0 de ponta a ponta na Sprint r1 (todos os arquétipos dela, mais a vertical): toda página mede página, margem,
    colunas e pelo menos um alvo de conteúdo; uma composição montada a partir do que a página tem resolve sem erro; no
    render FINAL a tinta de cada elemento ancorado está na linha (≤ 2 px dos alvos remedidos) e a caixa desenhada no DOM é
    a do plano (≤ 1 px); a linha de base e o cap medidos batem com a tinta do título no PNG (≤ 3 px)."""
    import test_camadas as tc
    import numpy as np
    from PIL import Image
    kit = tc.kit_sprint("composicao-fase0")
    try:
        tc.render(kit, "--receita", "r1")
        p1 = tc.plano(kit, "r1")
        pv = tc.plano(kit, "r1-vertical")
        conteudo = ("titulo", "numero", "preco", "foto", "logo", "corpo", "micro")
        for pl in (p1, pv):
            for pg in pl["paginas"]:
                al = pg["alvos"]
                assert {"pagina", "margem", "colunas"} <= set(al), (pg["rotulo"], sorted(al))
                assert any(c in al for c in conteudo), (pg["rotulo"], sorted(al))
        assert len(p1["paginas"][0]["alvos"]["colunas"]) == 11 and len(pv["paginas"][0]["alvos"]["colunas"]) == 6
        # composição por página, montada do que cada página mede: herói pena-dourada preso no 1º alvo de conteúdo, com
        # a chave que só casa aquela página (ativo:N, cota:Nome ou o rótulo que aparece uma vez só no kit)
        from collections import Counter
        uso = Counter(r for pg in p1["paginas"] for r in pg["rotulos"])
        comp = {}
        for pg in p1["paginas"]:
            unica = next((r for r in pg["rotulos"] if uso[r] == 1), None)
            if not unica:
                continue
            al = pg["alvos"]
            alvo = next(c for c in conteudo if c in al)
            y = f"base={alvo}.cap-e3" if "linhas" in al[alvo] else f"base={alvo}.topo-e3"
            comp[unica] = {"mensagem": f"prova da página {pg['n']}", "elementos": [
                {"id": "pena-dourada", "papel": "heroi", "funcao": "foco", "escala": {"altura": "1/6p"},
                 "porque": "prova de âncora no esqueleto", "ancora": {"relacao": "alinha", "x": f"esq={alvo}.esq", "y": y}}]}
        k = json.loads((kit / "mediakit.json").read_text(encoding="utf-8"))
        k["composicao"] = comp
        (kit / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False, indent=1), encoding="utf-8")
        tc.render(kit, "--receita", "r1", "--png", "--sem-vertical")
        p2 = tc.plano(kit, "r1")
        assert not p2.get("composicao_erros"), p2["composicao_erros"]
        n_anc, pior, pior_dom = 0, 0.0, 0.0
        for pg in p2["paginas"]:
            assert not pg["erros_composicao"], (pg["rotulo"], pg["erros_composicao"])
            for it in pg["elementos"]:
                if it.get("origem") != "composicao":
                    continue
                n_anc += 1
                t = it["ancora"]["tinta"]
                for r in it["ancora"]["restricoes"]:
                    b, v = _alvo_valor(pg["alvos"], r["texto"])
                    real = {"esq": t[0], "dir": t[2], "cx": (t[0] + t[2]) / 2, "topo": t[1], "base": t[3], "cy": (t[1] + t[3]) / 2}[b]
                    pior = max(pior, abs(real - v))
                    assert abs(real - v) <= 2, f"p.{pg['n']} {pg['rotulo']}: {r['texto']} pede {v:.1f}, a tinta está em {real:.1f}"
                dom = next(d for d in pg["dom"] if d["id"] == it["id"])
                for c in ("x", "y", "w", "h"):
                    pior_dom = max(pior_dom, abs(dom[c] - it[c]))
                    assert abs(dom[c] - it[c]) <= 1, f"p.{pg['n']}: DOM {c}={dom[c]} e plano {c}={it[c]}"
        assert n_anc == len(comp), (n_anc, len(comp))
        # linha de base e cap contra a tinta do título no PNG, numa página de fundo chapado (divisor ou prova)
        pg = next(p for p in p2["paginas"] if p["tipo"] in ("divisor", "prova") and "titulo" in p["alvos"])
        ls = pg["alvos"]["titulo"]["linhas"]
        L1, Ln = ls[0], ls[-1]
        img = np.asarray(Image.open(kit / "saida" / "png" / f"kit-r1-{pg['n']:02d}.png").convert("L")).astype(int)
        def tinta_linhas(L, y0, y1):
            reg = img[int(y0):int(y1), int(L["x"]):int(L["x"] + L["w"])]
            fundo = int(np.median(np.concatenate([img[int(L["y"]) - 30:int(L["y"]) - 22, int(L["x"]):int(L["x"] + L["w"])].ravel()])))
            perfil = (np.abs(reg - fundo) > 60).sum(1)
            return int(y0) + np.nonzero(perfil > 0.3 * perfil.max())[0]
        # cap: tinta da 1ª linha, só na metade de cima da caixa dela; linha de base: tinta da ÚLTIMA linha, da metade da
        # caixa até 10 px abaixo (embaixo dela não há outra linha do título; acima, a linha seguinte invadiria a região)
        topo = tinta_linhas(L1, L1["y"] - 8, L1["y"] + L1["h"] / 2).min()
        base = tinta_linhas(Ln, Ln["y"] + Ln["h"] / 2, Ln["y"] + Ln["h"]).max() + 1
        assert abs(topo - L1["cap"]) <= 3, ("cap", topo, L1["cap"])
        assert abs(base - Ln["linha_base"]) <= 3, ("linha de base", base, Ln["linha_base"])
        L = {"cap": L1["cap"], "linha_base": Ln["linha_base"]}
        log(f"{len(p1['paginas'])} páginas + 3 da vertical com alvos; {n_anc} elementos ancorados no render final, pior "
            f"desvio da âncora {pior:.2f} px e do DOM {pior_dom:.2f} px; título p.{pg['n']}: cap medido {L['cap']} × tinta "
            f"{topo}, linha de base {L['linha_base']} × tinta {base}")
    finally:
        shutil.rmtree(kit, ignore_errors=True)


def render_aqui(kit, *args, gerador=None):
    """Render no mesmo processo, para trocar o gerador de grafismos (os tipos `fio` e `colchetes` são da Frente B; a
    prova usa um gerador falso que obedece o contrato e o grafismos.gerar de verdade para o resto)."""
    import contextlib, io, render
    antes_argv, antes_ger = sys.argv, camadas.gerador_grafismos
    sys.argv = ["render.py", str(kit), "--fontes", str(kit / "fontes-receitas"), *args]
    if gerador:
        camadas.gerador_grafismos = lambda: (gerador, "gerador de prova (fio e colchetes falsos, o resto do grafismos.gerar)")
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            render.main()
    finally:
        sys.argv, camadas.gerador_grafismos = antes_argv, antes_ger
    return buf.getvalue()


def gerador_de_prova(tipo, params, ctx):
    import grafismos
    if tipo in ("fio", "colchetes"):
        return gerar_falso(tipo, params)
    return grafismos.gerar(tipo, params, ctx)


@teste
def render_constante_na_caixa_unica():
    """No render da Sprint r1 (fixture, horizontal e vertical), cada constante sai na MESMA caixa em toda página onde
    entra, no plano e no DOM final (≤ 1 px): o microtexto de margem a margem, o selo encostado no canto da margem; o QA
    novo passa sem falha."""
    import test_camadas as tc
    kit = tc.kit_sprint("caixa-unica")
    try:
        tc.render(kit, "--receita", "r1")
        resumo = []
        for nome in ("r1", "r1-vertical"):
            pl = tc.plano(kit, nome)
            por_id = {}
            for pg in pl["paginas"]:
                dom = {d["id"]: d for d in pg["dom"]}
                for it in pg["elementos"]:
                    if it["papel"] != "constante":
                        continue
                    caixa = (it["x"], it["y"], it["w"], it["h"])
                    d = dom[it["id"]]
                    assert max(abs(d[c] - it[c]) for c in ("x", "y", "w", "h")) <= 1, (pg["n"], it["id"], d, caixa)
                    por_id.setdefault(it["id"], set()).add(caixa)
                    m = pg["alvos"]["margem"]
                    if it["id"] == "constante-microtexto":
                        assert it["x"] == m["x"] and it["w"] == m["w"], (it, m)          # de margem a margem
                    if it["id"] == "constante-selo":
                        assert it["x"] in (m["x"], m["x"] + m["w"] - it["w"]) and it["y"] in (m["y"], m["y"] + m["h"] - it["h"]), (it, m)
            assert por_id and all(len(c) == 1 for c in por_id.values()), por_id
            f, _ = qa_geometria.checar_plano(pl, kit, nome)
            assert not f, f
            resumo.append(f"{nome}: " + ", ".join(f"{i} {next(iter(c))}" for i, c in sorted(por_id.items())))
        log("; ".join(resumo) + "; qa_geometria 0 falhas")
    finally:
        shutil.rmtree(kit, ignore_errors=True)


@teste
def render_maquete_e_liga():
    """Planejar antes de gerar: a maquete desenha as caixas no lugar resolvido (asset planejado pela proporção, liga
    pela geometria), sem tocar no kit nem no render-report; o render de verdade gera a liga com a geometria (fio de
    entrada pela esquerda até 24 px antes do título e colchetes em volta dele), o DOM é o plano, o QA confere a âncora
    e reprova o asset que ainda não existe. A folha de composição sai do mesmo render."""
    import test_camadas as tc
    import numpy as np
    from PIL import Image
    comp = {"divisor": {"mensagem": "o inventário começa aqui", "foco": "titulo", "elementos": [
        {"id": "pena-dourada", "papel": "heroi", "funcao": "foco", "escala": {"altura": "1/6p"}, "porque": "a pena assina o título",
         "ancora": {"relacao": "alinha", "x": "esq=titulo.esq", "y": "base=titulo.cap-e3"}},
        {"id": "fio", "papel": "estrutura", "funcao": "conexao", "grafismo": {"tipo": "fio", "params": {"espessura": 2}},
         "porque": "o fio entra pela borda na altura do título",
         "ancora": {"relacao": "liga", "modo": "conecta", "de": "pagina.esq", "para": "titulo.esq", "folga": "e3"}},
        {"id": "moldura", "papel": "estrutura", "funcao": "organizacao", "porque": "colchetes fecham o título",
         "ancora": {"relacao": "liga", "modo": "emoldura", "alvo": "titulo", "folga": "e2"}},
        {"id": "trofeu", "papel": "apoio", "funcao": "equilibrio", "escala": {"altura": "1/4p"}, "proporcao": [2, 3],
         "porque": "contrapeso do título, ainda por gerar", "ancora": {"relacao": "alinha", "x": "dir=margem.dir", "y": "cy=titulo.cy"}}]}}
    def mutar(k, d):
        k["composicao"] = comp
    kit = tc.kit_sprint("maquete-liga", mutar)
    try:
        tc.render(kit, "--receita", "r1", "--maquete", "--sem-vertical")
        assert (kit / "saida" / "maquete-r1.pdf").exists() and not (kit / "saida" / "kit-r1.pdf").exists()
        assert not (kit / "saida" / "render-report.json").exists(), "a maquete escreveu o render-report"
        pm = json.loads((kit / "saida" / "plano-maquete-r1.json").read_text(encoding="utf-8"))
        pg = next(p for p in pm["paginas"] if p["tipo"] == "divisor")
        ids = {it["id"]: it for it in pg["elementos"] if it.get("origem") == "composicao"}
        n = pg["n"]
        assert {"pena-dourada", f"fio-p{n}", f"moldura-p{n}", "trofeu"} <= set(ids), sorted(ids)
        tr = ids["trofeu"]
        assert abs(tr["h"] - 270) < 0.11 and abs(tr["w"] - 180) < 0.11 and abs(tr["x"] + tr["w"] - 1824) < 0.11, tr
        dom = {d["id"]: d for d in pg["dom"]}
        for i, it in ids.items():
            assert max(abs(dom[i][c] - it[c]) for c in ("x", "y", "w", "h")) <= 1, (i, dom[i], it)
        png = np.asarray(Image.open(kit / "saida" / "png" / f"maquete-r1-{n:02d}.png").convert("RGB")).astype(int)
        reg = png[int(tr["y"]) + 30:int(tr["y"] + tr["h"]) - 4, int(tr["x"]) + 4:int(tr["x"] + tr["w"]) - 4]
        # a hachura na cor de equilíbrio (#34C759 a 40% sobre o fundo): pixel esverdeado, verde bem acima do vermelho e do azul
        verde = ((reg[..., 1] - reg[..., 0] > 30) & (reg[..., 1] - reg[..., 2] > 20)).mean()
        fora = png[int(tr["y"]) + 30:int(tr["y"] + tr["h"]) - 4, int(tr["x"]) - 200:int(tr["x"]) - 40]
        assert verde > 0.1 and ((fora[..., 1] - fora[..., 0] > 30) & (fora[..., 1] - fora[..., 2] > 20)).mean() < 0.02, verde
        fio_m = ids[f"fio-p{n}"]["ancora"]["geometria"]["pontos"]
        tit = pg["alvos"]["titulo"]
        assert abs(fio_m[0][0]) < 0.01 and abs(fio_m[1][0] - (tit["x"] - 24)) < 0.01 and abs(fio_m[0][1] - (tit["y"] + tit["h"] / 2)) < 0.01, fio_m
        # o render de verdade, com o gerador de prova para fio e colchetes
        render_aqui(kit, "--receita", "r1", "--sem-vertical", "--png", gerador=gerador_de_prova)
        pl = tc.plano(kit, "r1")
        pg = next(p for p in pl["paginas"] if p["tipo"] == "divisor")
        its = {it["id"]: it for it in pg["elementos"]}
        fio_r = its[f"fio-p{n}"]
        assert fio_r["formato"] == "svg" and fio_r["grafismo"]["params"]["pontos"] == fio_m and fio_r["x"] == round(fio_m[0][0] - 1, 1), fio_r
        assert "trofeu" not in its and any("trofeu" in e and "sem asset" in e for e in pg["erros_composicao"]), pg["erros_composicao"]
        f, a = qa_geometria.checar_plano(pl, kit, "r1")
        assert [x for x in f if "trofeu" in x] and not [x for x in f if "âncora não cumprida" in x or "desenhado em" in x], f
        html = (kit / "saida" / "html" / "kit-r1.html").read_text(encoding="utf-8")
        assert html.count(f'data-elemento="fio-p{n}"') == 1 and "<polyline" in html
        import contact_sheet
        folha = contact_sheet.folha_composicao(kit, "r1")
        assert folha.exists() and Image.open(folha).size[0] > 1800
        folha_pdf = contact_sheet.folha_composicao(kit, "r1", pdf=True)        # sobre o raster do PDF entregue
        assert folha_pdf.name == "composicao-r1-pdf.png" and Image.open(folha_pdf).size == Image.open(folha).size
        log(f"maquete: {len(ids)} caixas na p.{n} (troféu 3:2 em {tr['x']:.0f},{tr['y']:.0f}, hachura verde em {verde:.0%}); "
            f"render: fio de {fio_m[0]} a {fio_m[1]}, DOM = plano, QA: {len(f)} falha(s) (o asset planejado); folha {folha.name}")
    finally:
        shutil.rmtree(kit, ignore_errors=True)


@teste
def render_painel_vendavel():
    """A cena da doação ganha `paineis` (o compor-doacao.json da Sprint): o painel 'SEU LOGO AQUI' vai à página pelo
    object-fit da foto e cai sobre a tinta dourada do letreiro no PNG; o selo, cuja caixa única bate nele, sai daquela
    página; e um herói posto em cima do painel pela composição reprova no QA."""
    import test_camadas as tc
    import numpy as np
    from PIL import Image
    def mutar(k, d):
        shutil.copy(tc.SPRINT / "compor-doacao.json", d / "compor-doacao.json")
        for a in k["acervo"]:
            if a["id"] == "c-doacao":
                a["paineis"] = "compor-doacao.json"
    kit = tc.kit_sprint("vendavel", mutar)
    try:
        tc.render(kit, "--receita", "r1", "--png", "--sem-vertical")
        pl = tc.plano(kit, "r1")
        pg = next(p for p in pl["paginas"] if any(z.get("fonte") == "compor-doacao.json#1" for z in p.get("vendaveis") or []))
        z = next(z for z in pg["vendaveis"] if z.get("fonte") == "compor-doacao.json#1")
        png = np.asarray(Image.open(kit / "saida" / "png" / f"kit-r1-{pg['n']:02d}.png").convert("RGB")).astype(int)
        def dourado(x0, y0, x1, y1):
            r = png[max(0, int(y0)):int(y1), max(0, int(x0)):int(x1)]
            return float(((r[..., 0] > 150) & (r[..., 0] - r[..., 2] > 70) & (r[..., 1] > 100)).mean())
        dentro = dourado(z["x"], z["y"], z["x"] + z["w"], z["y"] + z["h"])
        abaixo = dourado(z["x"], z["y"] + z["h"] + 40, z["x"] + z["w"], z["y"] + 2 * z["h"] + 40)
        assert dentro > 0.04 and dentro > 4 * abaixo, (dentro, abaixo, z)
        assert not any(it["id"] == "constante-selo" for it in pg["elementos"]), pg["elementos"]
        assert any("constante-selo" in a and "zona vendável" in a for a in pg["avisos"]), pg["avisos"]
        f, _ = qa_geometria.checar_plano(pl, kit, "r1")
        assert not [x for x in f if "zona vendável" in x], f
        rot = next(r for r in pg["rotulos"] if r.startswith("ativo:") and r.split(":")[1].isdigit())
        fo = pg["alvos"]["foto"]
        comp = {rot: {"mensagem": "prova: herói em cima do painel", "elementos": [
            {"id": "pena-dourada", "papel": "heroi", "funcao": "foco", "escala": {"altura": round(z["h"] * 1.5)}, "porque": "prova do painel",
             "ancora": {"relacao": "alinha", "x": f"cx=foto.esq+{round(z['x'] + z['w'] / 2 - fo['x'])}",
                        "y": f"cy=foto.topo+{round(z['y'] + z['h'] / 2 - fo['y'])}"}}]}}
        k = json.loads((kit / "mediakit.json").read_text(encoding="utf-8"))
        k["composicao"] = comp
        (kit / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False, indent=1), encoding="utf-8")
        tc.render(kit, "--receita", "r1", "--sem-vertical")
        f2, _ = qa_geometria.checar_plano(tc.plano(kit, "r1"), kit, "r1")
        cobre = [x for x in f2 if "pena-dourada" in x and "zona vendável" in x]
        assert cobre, f2
        log(f"painel na p.{pg['n']} em ({z['x']:.0f}, {z['y']:.0f}) {z['w']:.0f}×{z['h']:.0f}: {dentro:.0%} de pixel dourado dentro, "
            f"{abaixo:.0%} logo abaixo; selo fora da página; herói em cima: {cobre[0][:110]}")
    finally:
        shutil.rmtree(kit, ignore_errors=True)


# ================================================================================================= execução
def main():
    import test_camadas as tc
    tc.BASE.mkdir(parents=True, exist_ok=True)
    nomes = [a for a in sys.argv[1:] if not a.startswith("--")]
    so_unidade = "--unidade" in sys.argv
    render_ = {"esqueleto_em_todo_arquetipo", "render_constante_na_caixa_unica", "render_maquete_e_liga", "render_painel_vendavel"}
    testes = [(n, f) for n, f in globals().items() if callable(f) and getattr(f, "_teste", False)]
    if nomes:
        testes = [(n, f) for n, f in testes if n in nomes]
    elif so_unidade:
        testes = [(n, f) for n, f in testes if n not in render_]
    falhou = 0
    for n, f in testes:
        t0 = time.time()
        try:
            f()
            print(f"OK      {n}  ({time.time() - t0:.1f} s)", flush=True)
        except Exception as e:
            falhou += 1
            print(f"FALHOU  {n}  ({time.time() - t0:.1f} s): {type(e).__name__}: {str(e)[:1200]}", flush=True)
    print(f"\n{len(testes) - falhou} de {len(testes)} testes passaram")
    sys.exit(1 if falhou else 0)


if __name__ == "__main__":
    main()

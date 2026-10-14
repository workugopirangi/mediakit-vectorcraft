#!/usr/bin/env python3
"""Provas das regras do qa_conjunto.py que leem a COMPOSIÇÃO da página (Frente C). Rodar: ~/.venvs/mediakit/bin/python
test_qa_conjunto.py. Cada regra nova reprova SOZINHA quando violada e passa quando não; os kits são sintéticos (pasta
temporária, helpers do test_plano_elementos.py) e o plano é gravado à mão no formato que o render grava (sem `provisorio`,
com tamanho, `origem`, `funcao`, `ancora` e, por página, `composicao`). O caso real da Sprint (um asset com 560 px numa
página e 284 em outra) lê uma fixture com os heróis e apoios dos planos que o render gravou em 09/10/2026 (schema/fixtures/
sprint-planos-herois.json): a prova não depende do kit vivo, que muda no piloto."""
import json, sys, tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import qa_conjunto  # noqa: E402
from test_plano_elementos import heroi, pattern, sistema_teste, montar_kit, falhas  # noqa: E402

FIXTURE_SPRINT = AQUI.parent / "schema" / "fixtures" / "sprint-planos-herois.json"


def avisos(res):
    return [m for n, m in res if n == "AVISO"]


def so(res, trecho):
    """Mensagens (FALHA ou AVISO) que contêm o trecho."""
    return [m for _, m in res if trecho in m]


def el(id_, papel="heroi", relacao="sobrepoe", funcao="foco"):
    """Elemento de composição mínimo (só o que o QA lê: id, papel, função e a relação da âncora)."""
    return {"id": id_, "papel": papel, "funcao": funcao, "ancora": {"relacao": relacao}}


def kit_gravado(d, composicao=None, alterar=None):
    """Kit de 9 heróis novos com plano GRAVADO como o render grava: cada herói com função, origem e tamanho; o
    mediakit.json leva `composicao` quando vem. `alterar(plano)` mexe no plano antes de ele ir para o disco. Devolve o
    resultado do qa_conjunto.checar."""
    els = [heroi(f"h-novo-{i}", "kit-teste") for i in range(9)] + [pattern("pat-novo", "kit-teste")]
    k, plano = montar_kit(d, els, sistema_teste())
    if composicao is not None:
        k["composicao"] = composicao
        (Path(d) / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False, indent=2), encoding="utf-8")
    plano.pop("provisorio", None)
    for pg in plano["paginas"]:
        for x in pg["elementos"]:
            if x["papel"] in ("heroi", "apoio"):
                x.update(w=400, h=300, funcao="foco", origem="plano")
    if alterar:
        alterar(plano)
    (Path(d) / "saida" / "plano-elementos-r1.json").write_text(json.dumps(plano, ensure_ascii=False, indent=2), encoding="utf-8")
    bib = Path(d) / "bib-vazia"; bib.mkdir(exist_ok=True)
    return qa_conjunto.checar(d, bib=bib)


def heroi_da(plano, n):
    return next(x for x in plano["paginas"][n - 1]["elementos"] if x["papel"] == "heroi")


COMP_BASICA = {"capa": {"mensagem": "a capa diz o nome do evento"}}


# ---------------------------------------------------------------- regra 1: herói ou apoio sem função
def test_controle_kit_com_composicao_sem_aviso_novo():
    with tempfile.TemporaryDirectory() as d:
        res = kit_gravado(d, COMP_BASICA)
        assert falhas(res) == [], falhas(res)
        novos = [m for m in avisos(res) if "função" in m or "alturas" in m or "gramática" in m]
        assert novos == [], novos
        print(f"   kit com composição, tudo declarado: 0 falhas, {len(avisos(res))} avisos (OCR pendente, família sem aprovação), nenhum das regras novas")


def test_aviso_heroi_sem_funcao_so_em_kit_com_composicao():
    def tira(pl):
        del heroi_da(pl, 2)["funcao"]
    with tempfile.TemporaryDirectory() as d:
        res = kit_gravado(d, COMP_BASICA, tira)
        m = so(res, "sem `funcao`")
        print("  ", m)
        assert falhas(res) == [] and len(m) == 1, res
        assert "herói" in m[0] and "p.2" in m[0] and m[0].startswith("elementos r1:"), m
    with tempfile.TemporaryDirectory() as d:        # o mesmo plano num kit SEM composição: a regra não vale
        assert so(kit_gravado(d, None, tira), "sem `funcao`") == []
    with tempfile.TemporaryDirectory() as d:        # composição só com notas (`_`) também não conta como composição
        assert so(kit_gravado(d, {"_nota": "rascunho"}, tira), "sem `funcao`") == []


def test_plano_provisorio_nao_dispara_as_regras_da_composicao():
    """O plano provisório (planejador, sem medida do render) não conhece função, âncora nem tamanho: as regras da
    composição só valem sobre o plano que o render gravou."""
    with tempfile.TemporaryDirectory() as d:
        els = [heroi(f"h-novo-{i}", "kit-teste") for i in range(9)] + [pattern("pat-novo", "kit-teste")]
        k, _ = montar_kit(d, els, sistema_teste())
        k["composicao"] = COMP_BASICA
        (Path(d) / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False), encoding="utf-8")
        bib = Path(d) / "bib-vazia"; bib.mkdir()
        res = qa_conjunto.checar(d, bib=bib)
        assert so(res, "plano provisório") and falhas(res) == [], res
        assert so(res, "sem `funcao`") == [] and so(res, "alturas diferentes") == [], res


def test_composicao_mal_formada_no_kit_nao_derruba_o_qa():
    """`composicao` que não é objeto (lista, texto, nulo): sem composição para o QA, sem exceção; o erro é do schema do kit."""
    for ruim in ([], "texto", 3, {"capa": "não é objeto"}):
        with tempfile.TemporaryDirectory() as d:
            res = kit_gravado(d, ruim)
            assert falhas(res) == [] and so(res, "sem `funcao`") == [] and so(res, "gramática") == [], (ruim, res)


def test_aviso_apoio_sem_funcao():
    def apoio(pl):
        pl["paginas"][3]["elementos"].append({"id": "h-novo-8", "papel": "apoio", "camada": "frente", "x": 10, "y": 10, "w": 200, "h": 120,
                                              "origem": "composicao"})
    with tempfile.TemporaryDirectory() as d:
        m = so(kit_gravado(d, COMP_BASICA, apoio), "sem `funcao`")
        print("  ", m)
        assert len(m) == 1 and "apoio" in m[0] and "p.4" in m[0], m


# ---------------------------------------------------------------- regra 2: mesmo elemento, alturas diferentes
def _duas_alturas(h1, h4, degrau1=None, degrau4=None, mesma_imagem=False):
    """Alterador: o herói da p.1 aparece de novo na p.4, com alturas h1 e h4 (e, se vier, o `degrau` da âncora)."""
    def f(pl):
        a, b = heroi_da(pl, 1), heroi_da(pl, 4)
        if not mesma_imagem:
            b["id"] = a["id"]
        else:
            b["sha256"] = a["sha256"] = "ab" * 32
        a["h"], a["w"], b["h"], b["w"] = h1, h1 * 1.4, h4, h4 * 1.4
        for x, dg in ((a, degrau1), (b, degrau4)):
            if dg is not None:
                x["ancora"] = {"relacao": "alinha", "degrau": dg, "tinta": [0, 0, 10, x["h"]]}
    return f


def test_aviso_mesmo_elemento_com_alturas_diferentes():
    with tempfile.TemporaryDirectory() as d:
        res = kit_gravado(d, None, _duas_alturas(327, 166))          # o caso da Sprint: 560x327 numa página, 284x166 em outra
        m = so(res, "alturas diferentes")
        print("  ", m)
        assert falhas(res) == [] and len(m) == 1, res
        assert "h-novo-0" in m[0] and "p.1" in m[0] and "458x327 px" in m[0] and "p.4" in m[0] and "232x166 px" in m[0], m
    with tempfile.TemporaryDirectory() as d:        # a regra vale também para kit sem composição (é o caso real do legado)
        assert len(so(kit_gravado(d, COMP_BASICA, _duas_alturas(327, 166)), "alturas diferentes")) == 1


def test_alturas_diferentes_em_degrau_declarado_nao_avisam():
    with tempfile.TemporaryDirectory() as d:        # as duas são degrau (1/3p numa, 1/2p na outra): variação escolhida
        assert so(kit_gravado(d, COMP_BASICA, _duas_alturas(360, 540, True, True)), "alturas diferentes") == []
    with tempfile.TemporaryDirectory() as d:        # basta uma delas não ser degrau para avisar
        assert len(so(kit_gravado(d, COMP_BASICA, _duas_alturas(360, 540, True, False)), "alturas diferentes")) == 1
    with tempfile.TemporaryDirectory() as d:        # uma ancorada em degrau e a outra pelo catálogo (sem âncora)
        assert len(so(kit_gravado(d, COMP_BASICA, _duas_alturas(360, 540, True, None)), "alturas diferentes")) == 1


def test_mesma_altura_ou_dentro_da_tolerancia_nao_avisa():
    with tempfile.TemporaryDirectory() as d:
        assert so(kit_gravado(d, COMP_BASICA, _duas_alturas(300, 300)), "alturas diferentes") == []
    with tempfile.TemporaryDirectory() as d:        # 300 e 306 px: arredondamento do render, não decisão de escala
        assert so(kit_gravado(d, COMP_BASICA, _duas_alturas(300, 306)), "alturas diferentes") == []


def test_mesma_imagem_com_ids_diferentes_tambem_avisa():
    with tempfile.TemporaryDirectory() as d:
        res = kit_gravado(d, COMP_BASICA, _duas_alturas(327, 166, mesma_imagem=True))
        m = so(res, "alturas diferentes")
        print("  ", m)
        assert len(m) == 1 and "h-novo-0 / h-novo-2" in m[0], m           # os dois ids são da mesma imagem (mesmo sha256)


def test_caso_real_da_sprint_asa_com_560_e_284():
    """Os planos que o render gravou para as 3 receitas da Sprint (09/10): a asa da capa a 560 px e a do público a 284 px,
    e os outros elementos que mudam de tamanho de página para página. O que ficou do mesmo tamanho não avisa."""
    fx = json.loads(FIXTURE_SPRINT.read_text(encoding="utf-8"))["receitas"]
    achados = {rid: qa_conjunto.alturas_inconsistentes(p, rid) for rid, p in fx.items()}
    for rid, ms in achados.items():
        print(f"   {rid}:", *(m.split("`")[1] for m in ms))
    assert {rid: sorted(m.split("`")[1] for m in ms) for rid, ms in achados.items()} == {
        "r1": ["asa-gravura", "asas-par-gravura", "cronometro-gravura", "pena-gravura"],
        "r2": ["cronometro-adesivo", "folha-adesivo"],
        "r3": ["asa-escultura", "medalha-alada", "numeral-02", "pena-dourada"]}, achados
    asa = next(m for m in achados["r1"] if "`asa-gravura`" in m)
    assert "p.1 560x327 px" in asa and "p.4 284x166 px" in asa and asa.startswith("elementos r1:"), asa


# ---------------------------------------------------------------- regra 3: relações fora da gramática do tipo
def _comp_ativo(rel_pagina, rel_tipo="sobrepoe", porque=None):
    pagina = {"mensagem": "o ativo entra na página", "elementos": [el("h-novo-6", relacao=rel_pagina)]}
    if porque:
        pagina["porque_fora_da_gramatica"] = porque
    return {"ativo": {"mensagem": "gramática do ativo", "elementos": [el("h-novo-5", relacao=rel_tipo)]}, "ativo:2": pagina}


def _meta_ativo(porque=None, chave="ativo:2", gramatica="ativo"):
    def f(pl):
        pl["paginas"][6]["composicao"] = {"chave": chave, "gramatica": gramatica, "mensagem": "o ativo entra na página",
                                         "foco": "objeto", "leitura": None, "estrutura": None, "padroes": [],
                                         "porque_fora_da_gramatica": porque}
    return f


def test_aviso_pagina_com_relacao_fora_da_gramatica():
    with tempfile.TemporaryDirectory() as d:
        res = kit_gravado(d, _comp_ativo("alinha"), _meta_ativo())
        m = so(res, "gramática")
        print("  ", m)
        assert falhas(res) == [] and len(m) == 1, res
        assert "p.7" in m[0] and "ativo:2" in m[0] and "`alinha`" in m[0] and "`sobrepoe`" in m[0] and "porque_fora_da_gramatica" in m[0], m


def test_pagina_dentro_da_gramatica_ou_com_porque_nao_avisa():
    with tempfile.TemporaryDirectory() as d:        # mesma relação-mãe
        assert so(kit_gravado(d, _comp_ativo("sobrepoe"), _meta_ativo()), "gramática") == []
    with tempfile.TemporaryDirectory() as d:        # foge, mas explica na própria composição da página
        assert so(kit_gravado(d, _comp_ativo("alinha", porque="o ativo desta página é o número, não o objeto"), _meta_ativo()), "gramática") == []
    with tempfile.TemporaryDirectory() as d:        # foge, e o porquê veio na meta que o render gravou
        assert so(kit_gravado(d, _comp_ativo("alinha"), _meta_ativo(porque="o foco desta página é outro")), "gramática") == []
    with tempfile.TemporaryDirectory() as d:        # a própria página é a gramática (chave do tipo): nada a comparar
        assert so(kit_gravado(d, _comp_ativo("alinha"), _meta_ativo(chave="ativo")), "gramática") == []
    with tempfile.TemporaryDirectory() as d:        # tipo sem entrada de gramática: nada a comparar
        assert so(kit_gravado(d, _comp_ativo("alinha"), _meta_ativo(gramatica=None)), "gramática") == []
    with tempfile.TemporaryDirectory() as d:        # página que usa só parte das relações do tipo não foge dele
        comp = _comp_ativo("sobrepoe")
        comp["ativo"]["elementos"].append(el("h-novo-4", papel="estrutura", relacao="liga"))
        assert so(kit_gravado(d, comp, _meta_ativo()), "gramática") == []


# ---------------------------------------------------------------- grafismo da composição e herói ancorado
def _capa_com_grafismo(pl):
    """O herói da capa é um grafismo declarado só na página (id fora de elementos[]), como a composição permite."""
    pg = pl["paginas"][0]
    pg["elementos"] = [x for x in pg["elementos"] if x["papel"] != "heroi"] + [
        {"id": "numeral-p1", "papel": "heroi", "formato": "svg", "origem": "composicao", "funcao": "foco", "camada": "frente",
         "x": 100, "y": 100, "w": 900, "h": 500, "ancora": {"relacao": "sangra", "degrau": True}}]


def test_grafismo_da_composicao_vale_como_novo_e_nao_gera_aviso_falso():
    with tempfile.TemporaryDirectory() as d:
        res = kit_gravado(d, COMP_BASICA, _capa_com_grafismo)
        assert falhas(res) == [], f"capa com grafismo nascido no kit não pode reprovar como 'não é novo': {falhas(res)}"
        assert so(res, "numeral-p1") == [], so(res, "numeral-p1")
    with tempfile.TemporaryDirectory() as d:        # controle: item que NÃO é grafismo da composição continua avisando
        def fantasma(pl):
            pl["paginas"][0]["elementos"].append({"id": "sumiu-do-json", "papel": "apoio", "funcao": "foco", "camada": "frente",
                                                  "x": 1, "y": 1, "w": 9, "h": 9, "origem": "plano"})
        m = so(kit_gravado(d, COMP_BASICA, fantasma), "sumiu-do-json")
        assert len(m) == 1 and "não em elementos[]" in m[0], m


def _fios_da_liga(com_origem):
    """Os fios que a relação `liga` gera (ids fio-p8 e fio-p8-s1): itens `estrutura` em svg com o `grafismo` declarado inline
    na composição da página 8; não existem em elementos[]."""
    def f(pl):
        for i, (eid, x) in enumerate((("fio-p8", 100), ("fio-p8-s1", 520))):
            it = {"id": eid, "papel": "estrutura", "formato": "svg", "camada": "frente", "x": x, "y": 200, "w": 380, "h": 6,
                  "grafismo": {"tipo": "fio", "params": {"espessura": 2}}}
            if com_origem:
                it.update(origem="composicao", funcao="conexao", ancora={"relacao": "liga"})
            pl["paginas"][7]["elementos"].append(it)
    return f


def test_item_com_grafismo_declarado_na_composicao_nao_avisa_fora_de_elementos():
    """Pedido da integração: item do plano com `grafismo` (declarado inline na composição, `formato: svg`) não precisa estar
    em elementos[]. Vale com ou sem `origem` no item, e vale para o fio que a `liga` parte em segmentos (fio-p8-s1)."""
    for com_origem in (False, True):
        with tempfile.TemporaryDirectory() as d:
            res = kit_gravado(d, COMP_BASICA, _fios_da_liga(com_origem))
            assert falhas(res) == [] and so(res, "fio-p8") == [], (com_origem, so(res, "fio-p8"), falhas(res))
    with tempfile.TemporaryDirectory() as d:        # kit sem composição: o mesmo item também não avisa (o grafismo é do plano, não do JSON)
        assert so(kit_gravado(d, None, _fios_da_liga(False)), "fio-p8") == []
    # controles: item comum que sumiu do elementos[] continua avisando, mesmo em svg, mesmo estrutura, mesmo com origem composicao sem grafismo
    comuns = [("sumiu-um", {"papel": "apoio", "formato": "png"}), ("sumiu-dois", {"papel": "estrutura", "formato": "svg"}),
              ("sumiu-tres", {"papel": "apoio", "formato": "png", "origem": "composicao"})]
    for eid, extra in comuns:
        def fantasma(pl, eid=eid, extra=extra):
            pl["paginas"][7]["elementos"].append(dict({"id": eid, "funcao": "foco", "camada": "frente", "x": 1, "y": 1, "w": 9, "h": 9}, **extra))
        with tempfile.TemporaryDirectory() as d:
            m = so(kit_gravado(d, COMP_BASICA, fantasma), eid)
            assert len(m) == 1 and "está no plano mas não em elementos[]" in m[0], (eid, m)


def test_heroi_ancorado_conta_em_cobertura_repeticao_e_novidade_como_os_outros():
    """Origem 'composicao' não isenta: herói repetido em páginas seguidas, 4 usos e cobertura baixa reprovam; o herói
    velho ancorado na capa derruba a regra da capa e a da novidade."""
    def ancorados(pl):
        for pg in pl["paginas"]:
            for x in pg["elementos"]:
                if x["papel"] == "heroi":
                    x.update(origem="composicao", ancora={"relacao": "sobrepoe", "degrau": True, "tinta": [0, 0, 5, 5]})
                    if pg["n"] in (1, 2, 4, 6):
                        x["id"] = "h-novo-0"
            if pg["n"] in (8, 10, 11, 12):
                pg["elementos"] = [x for x in pg["elementos"] if x["papel"] != "heroi"]
    with tempfile.TemporaryDirectory() as d:
        f = falhas(kit_gravado(d, COMP_BASICA, ancorados))
        print("  ", f)
        assert any("repetido nas páginas seguidas 1 e 2" in m for m in f), f
        assert any("usado 4 vezes" in m for m in f), f
        assert any("cobertura de herói 56%" in m for m in f), f


def test_texto_em_foto_real_e_aviso_e_em_peca_gerada_e_falha():
    """Teste da AME (09/10): o OCR leu o patrocinador na camisa do árbitro de verdade ("Princesa") e a regra chamava de
    texto da IA. Foto real (gerado false ou rota real): aviso para conferir a marca. Peça gerada: falha, como antes."""
    lido = {"ocr": "Pri ese"}
    assert qa_conjunto.leitura_de_texto({"gerado": False, "rota": "real"}, lido)[0] == "aviso"
    assert qa_conjunto.leitura_de_texto({"rota": "real"}, lido)[0] == "aviso"
    assert qa_conjunto.leitura_de_texto({"gerado": True, "rota": "codex-alfa"}, lido)[0] == "falha"
    assert qa_conjunto.leitura_de_texto({}, lido)[0] == "falha", "sem dizer que é real, vale a regra da peça gerada"
    assert qa_conjunto.leitura_de_texto({"gerado": True}, {"ocr": ""})[0] is None
    assert "pendente" in qa_conjunto.leitura_de_texto({"gerado": True}, None)[1]



# ================================================================================================= camada de acabamento
# mk-2.1 (references/10-acabamento.md, seção QA). Cada regra: o mutante que falha (ou avisa), o par que passa e o
# inverso (o mesmo kit em mk-2.0 ou sem o campo novo não muda nada). Kits sintéticos em dicionário e pasta temporária.
import copy, hashlib  # noqa: E402

INDICE_TESTE = {"versao": 1, "padroes": [{"id": "palavra-gigante-atras-da-figura"}, {"id": "textura-tom-sobre-tom"}],
                "referencias": [{"id": "conebra"}, {"id": "saudade"}], "recursos": []}


def _indice(d):
    p = Path(d) / "indice.json"
    p.write_text(json.dumps(INDICE_TESTE), encoding="utf-8")
    return p


def _rec(i, fam, ref="palavra-gigante-atras-da-figura", **kw):
    return dict({"id": i, "familia": fam, "referencia": ref, "principio": "o princípio adaptado do recurso", "rota": "codigo"}, **kw)


def kit21(versao="mk-2.1"):
    """Kit mk-2.1 que passa em todas as regras do acabamento: consulta gravada, 4 famílias, toda página com acabamento
    e porquê, o fio `lua` com o mesmo desenho nas 3 páginas da tabela."""
    eco = lambda i, op=0.12: {"id": i, "grafismo": {"tipo": "eco", "params": {"cor": "texto", "largura": 800}},  # noqa: E731
                              "papel": "acabamento", "funcao": "acabamento", "camada": "atras", "motivo": "lua",
                              "efeito": {"opacidade": op}, "ancora": {"relacao": "alinha", "x": "esq=titulo.esq", "y": "cy=titulo.cy"}}
    pag = lambda recs, it, els: {"mensagem": "a página diz uma coisa", "elementos": els,  # noqa: E731
                                 "acabamento": {"recursos": recs, "intensidade": it, "porque": "o acabamento desta página"}}
    return {"schema_version": versao, "evento": {"nome": "Corrida Teste"}, "cliente": {"nome": "CLIENTE A"},
            "sistema_elementos": {"motivos": [{"id": "lua", "origem": "territorio"}]}, "elementos": [],
            "direcao_criativa": {"consulta": "consulta-repertorio.json",
                                 "recursos": [_rec("eco-do-titulo", "tipografia-expressiva"),
                                              _rec("malha", "profundidade-3d", "conebra:12"),
                                              _rec("hachura", "pattern-textura", "textura-tom-sobre-tom"),
                                              _rec("chanfro", "tratamento-imagem", "saudade")],
                                 "intensidade": {"padrao": 1, "teto": 2},
                                 "fio_condutor": {"motivo": "lua", "papeis": {"capa": "eco", "divisor": "textura", "prova": "eco"}}},
            "composicao": {"capa": pag(["eco-do-titulo"], 2, [eco("eco-capa")]),
                           "divisor": pag(["malha"], 1, [dict(eco("eco-divisor", 0.24), grafismo={"tipo": "eco", "params": {"cor": "texto", "largura": 1900}})]),
                           "prova": pag(["hachura"], 1, [eco("eco-prova")]),
                           "publico": pag(["chanfro"], 2, [])}}


def _pasta21(d, k, consulta=True, sha=None):
    d = Path(d)
    (d / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False), encoding="utf-8")
    ind = _indice(d)
    if consulta:
        sha = sha if sha is not None else hashlib.sha256(ind.read_bytes()).hexdigest()
        (d / "consulta-repertorio.json").write_text(json.dumps({"consultas": [], "indice_sha256": sha}), encoding="utf-8")
    return ind


def _acab(d, k, **kw):
    ind = _pasta21(d, k, **kw)
    return qa_conjunto.checar_acabamento(d, k, indice=ind, ledger=Path(d) / "sem-historico.json")


def test_acabamento_controle_kit_21_completo_passa():
    with tempfile.TemporaryDirectory() as d:
        res = _acab(d, kit21())
        assert falhas(res) == [] and [m for m in avisos(res) if "sem plano" not in m] == [], res
    for leg in ({"schema_version": "mk-2.0"}, {"schema_version": "mk-2.0", "composicao": {"capa": {"mensagem": "x"}}}):
        assert qa_conjunto.checar_acabamento(tempfile.gettempdir(), leg) == []      # inverso: kit sem a camada, nada


def test_acabamento_mk21_sem_consulta_reprova():
    with tempfile.TemporaryDirectory() as d:
        res = _acab(d, kit21(), consulta=False)
        assert len(so(res, "sem a consulta ao repertório")) == 1 and falhas(res), res
    with tempfile.TemporaryDirectory() as d:                      # inverso: o mesmo kit em mk-2.0 avisa (a direção declara a consulta)
        res = _acab(d, kit21("mk-2.0"), consulta=False)
        assert not falhas(res) and len(so(res, "aponta para")) == 1, res
    with tempfile.TemporaryDirectory() as d:                      # mk-2.0 sem `consulta` declarada: nada
        k = kit21("mk-2.0"); del k["direcao_criativa"]["consulta"]
        assert not so(_acab(d, k, consulta=False), "consulta"), "mk-2.0 sem consulta declarada não cobra consulta"


def test_acabamento_consulta_sobre_indice_antigo_avisa():
    with tempfile.TemporaryDirectory() as d:
        res = _acab(d, kit21(), sha="0" * 64)
        assert not falhas(res) and len(so(res, "outro índice do repertório")) == 1, res
    with tempfile.TemporaryDirectory() as d:
        res = _acab(d, kit21(), sha="")
        assert len(so(res, "não grava `indice_sha256`")) == 1, res


def test_acabamento_recurso_fora_da_direcao_ou_do_indice_reprova():
    k = kit21(); k["composicao"]["publico"]["acabamento"]["recursos"] = ["inventado"]
    with tempfile.TemporaryDirectory() as d:
        assert len([m for m in falhas(_acab(d, k)) if "`inventado`" in m and "não está em direcao_criativa" in m]) == 1
    with tempfile.TemporaryDirectory() as d:                      # inverso mk-2.0: a regra do QA não dispara
        assert not so(_acab(d, dict(k, schema_version="mk-2.0")), "`inventado`")
    k = kit21(); k["direcao_criativa"]["recursos"][3]["referencia"] = "ficticio:pessoa-sai-da-foto-07"
    with tempfile.TemporaryDirectory() as d:
        f = falhas(_acab(d, k))
        assert len(f) == 1 and "`chanfro`" in f[0] and "não está no índice" in f[0], f
    assert qa_conjunto.no_indice("conebra:12", {"conebra"}) and qa_conjunto.no_indice("saudade", {"saudade"})
    assert not qa_conjunto.no_indice("ficticio:x", {"conebra"}) and not qa_conjunto.no_indice("", {"conebra"})


def test_acabamento_pagina_sem_acabamento_ou_sem_porque_reprova():
    k = kit21(); del k["composicao"]["publico"]["acabamento"]
    k["composicao"]["prova"]["acabamento"]["porque"] = ""
    with tempfile.TemporaryDirectory() as d:
        res = _acab(d, k)
        assert len(so(res, "composicao/publico: página composta sem `acabamento`")) == 1, res
        assert len(so(res, "composicao/prova: `acabamento` sem `porque`")) == 1, res
    with tempfile.TemporaryDirectory() as d:
        assert not so(_acab(d, dict(k, schema_version="mk-2.0")), "sem `acabamento`")


def test_acabamento_menos_de_4_familias_reprova_em_mk21():
    k = kit21(); k["direcao_criativa"]["recursos"][3]["familia"] = "pattern-textura"
    with tempfile.TemporaryDirectory() as d:
        assert len([m for m in falhas(_acab(d, k)) if "3 família(s) distinta(s)" in m]) == 1
    with tempfile.TemporaryDirectory() as d:
        assert not so(_acab(d, dict(k, schema_version="mk-2.0")), "família(s) distinta(s)")
    aviso = "direcao_criativa/recursos: 3 família(s) distinta(s) (x); o kit pede pelo menos 4"
    assert qa_conjunto.superado(aviso, {"schema_version": "mk-2.1"}) and not qa_conjunto.superado(aviso, {"schema_version": "mk-2.0"})


def test_acabamento_fio_com_tratamento_diferente_reprova():
    k = kit21(); k["composicao"]["prova"]["elementos"][0]["grafismo"]["params"]["cor"] = "marca"
    with tempfile.TemporaryDirectory() as d:
        f = [m for m in falhas(_acab(d, k)) if "muda de tratamento" in m]
        assert len(f) == 1 and "prova" in f[0] and "marca" in f[0], f
    k = kit21(); k["composicao"]["prova"]["elementos"][0]["efeito"]["blend"] = "multiply"
    with tempfile.TemporaryDirectory() as d:
        assert so(_acab(d, k), "muda de tratamento")
    with tempfile.TemporaryDirectory() as d:                      # inverso mk-2.0
        assert not so(_acab(d, dict(k, schema_version="mk-2.0")), "muda de tratamento")
    # largura e opacidade mudam com o papel e não contam (o kit21 já tem 800 e 1900, .12 e .24): ver o controle


def test_acabamento_pagina_da_tabela_sem_o_motivo_avisa():
    k = kit21(); k["composicao"]["divisor"]["elementos"] = []
    with tempfile.TemporaryDirectory() as d:
        res = _acab(d, k)
        assert not falhas(res) and len(so(res, "`divisor` está na tabela do fio condutor")) == 1, res


def test_acabamento_recurso_repetido_de_outro_cliente_avisa():
    hist = [{"id": f"kit-{i}", "cliente": c, "evento": f"Evento {i}", "data": f"2026-0{i}-01", "recursos": r}
            for i, (c, r) in enumerate([("CLIENTE B", ["malha"]), ("CLIENTE C", []), ("CLIENTE D", []),
                                        ("CLIENTE E", [{"id": "outro", "referencia": "saudade"}]), ("CLIENTE A", ["hachura"])], 1)]
    with tempfile.TemporaryDirectory() as d:
        led = Path(d) / "hist.json"; led.write_text(json.dumps(hist), encoding="utf-8")
        k = kit21(); ind = _pasta21(d, k)
        res = qa_conjunto.checar_acabamento(d, k, indice=ind, ledger=led)
        m = so(res, "repete o kit")
        # `malha` é do kit-1, o 4º mais recente de outro cliente: fora dos 3 últimos; `chanfro` usa a referência de
        # `saudade`, que o kit-4 (CLIENTE E) usou; `hachura` só repete o próprio cliente
        assert len(m) == 1 and "`chanfro`" in m[0] and "kit-4" in m[0], m
        k["direcao_criativa"]["recursos"][3]["porque_repete"] = "o mesmo chanfro é a assinatura das duas corridas"
        assert not so(qa_conjunto.checar_acabamento(d, k, indice=ind, ledger=led), "repete o kit")


def test_acabamento_intensidade_calculada_teto_e_acima_de_3():
    k = kit21(); k["composicao"]["publico"]["acabamento"]["intensidade"] = 3
    with tempfile.TemporaryDirectory() as d:
        res = _acab(d, k)
        assert not falhas(res) and len(so(res, "composicao/publico: intensidade calculada 3")) == 1, res
    k = kit21(); k["composicao"]["capa"]["acabamento"]["recursos"] = ["eco-do-titulo", "malha", "hachura", "chanfro"]
    with tempfile.TemporaryDirectory() as d:
        f = falhas(_acab(d, k))
        assert len(f) == 1 and "intensidade calculada 4" in f[0] and "passa de 3" in f[0], f
    assert qa_conjunto.intensidade({}, kit21()) == (1, 1)                     # página sem acabamento: vale o padrão
    assert qa_conjunto.superado("composicao/x/acabamento: intensidade 3 (marcante) acima do teto 2", {"schema_version": "mk-2.0"})


def _plano_seq(d, k, chaves, extra=None):
    """Grava saida/plano-elementos-r1.json com uma página por chave da composição, na ordem dada."""
    pags = [{"n": i, "rotulo": ch, "tipo": ch, "rotulos": [ch], "composicao": {"chave": ch}, "elementos": [], "protegidos": []}
            for i, ch in enumerate(chaves, 1)]
    if extra:
        extra(pags)
    (Path(d) / "saida").mkdir(exist_ok=True)
    (Path(d) / "saida" / "plano-elementos-r1.json").write_text(json.dumps({"largura": 1920, "altura": 1080, "paginas": pags}),
                                                               encoding="utf-8")


def _comp(recs, it):
    return {"mensagem": "página", "acabamento": {"recursos": recs, "intensidade": it, "porque": "o porquê da página"}}


def test_acabamento_ritmo():
    k = kit21(); k["direcao_criativa"]["intensidade"]["teto"] = 3
    k["composicao"].update({f"m{i}": _comp([["eco-do-titulo"], ["malha"], ["hachura"], ["chanfro"]][i % 4], 3) for i in range(4)})
    with tempfile.TemporaryDirectory() as d:
        _plano_seq(d, k, ["capa", "m0", "m1", "m2", "divisor"]); res = _acab(d, k)
        f = [m for m in falhas(res) if "seguidas em intensidade 3" in m]
        assert len(f) == 1 and "p.2 a p.4" in f[0], res
        assert len(so(res, "sem nenhuma página de intensidade 0 ou 1")) == 1, res
    with tempfile.TemporaryDirectory() as d:                      # 2 marcantes e respiro a cada 4: limpo
        _plano_seq(d, k, ["capa", "m0", "m1", "divisor", "m2", "prova"]); res = _acab(d, k)
        assert not so(res, "seguidas em intensidade") and not so(res, "sem nenhuma página"), res
    with tempfile.TemporaryDirectory() as d:                      # vizinhas com o mesmo conjunto
        k2 = kit21(); k2["composicao"]["capa2"] = copy.deepcopy(k2["composicao"]["capa"])
        _plano_seq(d, k2, ["capa", "capa2", "divisor"]); res = _acab(d, k2)
        assert len(so(res, "p.1 e p.2 usam o mesmo conjunto de recursos (eco-do-titulo)")) == 1, res


def test_acabamento_mesma_textura_em_paginas_seguidas_avisa():
    k = kit21(); k["elementos"] = [{"id": "grao", "papel": "acabamento", "tipo": "textura", "formato": "png", "motivo": "lua"}]
    def tex(x2):
        def f(pags):
            for pg, x in zip(pags, (0, x2)):
                pg["elementos"].append({"id": "grao", "papel": "acabamento", "camada": "atras", "x": x, "y": 0, "w": 960,
                                        "h": 1080, "sha256": "ab" * 32, "formato": "png"})
        return f
    with tempfile.TemporaryDirectory() as d:
        _plano_seq(d, k, ["capa", "divisor"], tex(0)); res = _acab(d, k)
        assert len(so(res, "a mesma textura `grao` na mesma escala e área nas páginas seguidas 1 e 2")) == 1, res
    with tempfile.TemporaryDirectory() as d:
        _plano_seq(d, k, ["capa", "divisor"], tex(960)); assert not so(_acab(d, k), "mesma textura")


def test_acabamento_continuidade_papel_repetido_e_medida():
    k = kit21(); k["direcao_criativa"]["fio_condutor"]["papeis"] = {"capa": "eco", "divisor": "eco", "prova": "contrapeso"}
    def itens(pags):
        pags[0]["elementos"].append({"id": "eco-capa", "papel": "acabamento", "camada": "atras", "x": 96, "y": 200, "w": 800,
                                     "h": 200, "formato": "svg", "efeito": {"opacidade": 0.46}})
        pags[2]["elementos"].append({"id": "eco-prova", "papel": "acabamento", "camada": "atras", "x": 600, "y": 300, "w": 400,
                                     "h": 200, "formato": "svg"})
    with tempfile.TemporaryDirectory() as d:
        _plano_seq(d, k, ["capa", "divisor", "prova"], itens); res = _acab(d, k)
        assert len(so(res, "faz o mesmo papel (eco) nas páginas seguidas 1 e 2")) == 1, res
        assert len(so(res, "p.1: o fio `lua` como eco (`eco-capa`) tem opacidade 0.46")) == 1, res
        assert len(so(res, "como contrapeso (`eco-prova`) mede 200 px")) == 1, res
    W, H = 1920.0, 1080.0
    med = lambda papel, **it: qa_conjunto.medida_do_papel(papel, dict({"id": "x", "formato": "svg", "rot": 0}, **it), {}, W, H, "/")  # noqa: E731
    assert med("contrapeso", x=0, y=300, w=500, h=700) is None and med("contrapeso", x=300, y=300, w=500, h=700)
    assert med("selo", x=10, y=10, w=180, h=180) is None and med("selo", x=10, y=10, w=200, h=200)
    assert med("textura", x=0, y=0, w=960, h=540) is None and med("textura", x=0, y=0, w=900, h=500)
    assert med("eco", x=0, y=0, w=9, h=9, efeito={"opacidade": 0.24}) is None
    alvos = {"titulo": {"x": 0, "y": 0, "w": 900, "h": 120, "linhas": [{"x": 0, "y": 0, "w": 900, "h": 120, "cap": 20, "linha_base": 100}]}}
    sep = lambda h: qa_conjunto.medida_do_papel("separador", {"id": "s", "formato": "svg", "rot": 0, "x": 0, "y": 500, "w": 900, "h": h},  # noqa: E731
                                                {"alvos": alvos}, W, H, "/")
    assert sep(80) is None and "1 altura de maiúscula" in sep(90)


def test_acabamento_sem_motivo_no_plano_avisa():
    def orfao(pags):
        pags[0]["elementos"].append({"id": "solto-sem-motivo", "papel": "acabamento", "camada": "atras", "x": 0, "y": 0, "w": 9, "h": 9})
        pags[0]["elementos"].append({"id": "com-motivo", "papel": "acabamento", "camada": "atras", "x": 0, "y": 0, "w": 9, "h": 9, "motivo": "lua"})
        pags[0]["elementos"].append({"id": "eco-capa-sombra", "papel": "acabamento", "camada": "atras", "x": 0, "y": 0, "w": 9, "h": 9, "derivado_de": "eco-capa"})
    with tempfile.TemporaryDirectory() as d:
        _plano_seq(d, kit21(), ["capa", "divisor"], orfao); res = _acab(d, kit21())
        m = so(res, "sem motivo")
        assert len(m) == 1 and "solto-sem-motivo" in m[0], m


GATE = "texto fora do gate de copy"


def _com_grafismo(tipo, params, onde="composicao"):
    """kit21 com mais um grafismo de texto: na composição da capa (`grafismo {tipo, params}`) ou em `elementos[]` (`tipo` + `params`)."""
    k = kit21()
    if onde == "composicao":
        base = {c: v for c, v in k["composicao"]["capa"]["elementos"][0].items() if c != "motivo"}    # sem o motivo do fio: não entra na conta dele
        k["composicao"]["capa"]["elementos"].append(dict(base, id="texto-teste", grafismo={"tipo": tipo, "params": params}))
    else:
        k["elementos"].append({"id": "texto-teste", "tipo": tipo, "formato": "svg", "arquivo": None, "params": params,
                               "papel": "acabamento", "motivo": "lua"})
    return k


def test_acabamento_texto_livre_em_eco_numeral_eco_e_texto_curva_avisa():
    """eco, numeral-eco e texto-curva com `texto` e sem `texto_de`: AVISO "texto fora do gate de copy", um por grafismo, com
    o lugar e o texto; nunca FALHA. Falha sem a regra: o kit21 de controle não tem nenhum."""
    with tempfile.TemporaryDirectory() as d:
        assert not so(_acab(d, kit21()), GATE), "controle: o kit21 não tem texto livre"
    for tipo in ("eco", "numeral-eco", "texto-curva"):
        for onde in ("composicao", "elementos"):
            with tempfile.TemporaryDirectory() as d:
                res = _acab(d, _com_grafismo(tipo, {"texto": "2027", "altura": 160}, onde))
                m = so(res, GATE)
                assert len(m) == 1 and f"`{tipo}`" in m[0] and "texto-teste" in m[0] and "'2027'" in m[0], (tipo, onde, m)
                assert onde in m[0] and [n for n, x in res if x == m[0]] == ["AVISO"], (tipo, onde, res)
                assert falhas(res) == [], res
    print("   eco, numeral-eco e texto-curva com `texto`: 1 AVISO cada, na composição e em elementos[]; nenhuma FALHA")


def test_acabamento_texto_de_nao_avisa_e_texto_com_texto_de_avisa_que_o_gerador_ignora_o_texto_de():
    for tipo in ("eco", "numeral-eco", "texto-curva"):
        for de in ("titulo", "evento", "tese", "local", "data"):
            with tempfile.TemporaryDirectory() as d:          # inverso: texto vivo do gate, nenhum aviso
                assert not so(_acab(d, _com_grafismo(tipo, {"texto_de": de, "altura": 160})), GATE), (tipo, de)
    with tempfile.TemporaryDirectory() as d:                  # `texto` vence `texto_de` no gerador: continua texto livre
        m = so(_acab(d, _com_grafismo("eco", {"texto": "OUTRO", "texto_de": "titulo"})), GATE)
        assert len(m) == 1 and "ignora o `texto_de`" in m[0], m
    print("   texto_de (5 origens x 3 tipos): 0 aviso; `texto` junto com `texto_de`: 1 aviso (o gerador usa o `texto`)")


def test_acabamento_texto_livre_so_vale_para_texto_preenchido_e_para_os_tres_tipos():
    for vazio in (None, "", "   "):
        with tempfile.TemporaryDirectory() as d:
            assert not so(_acab(d, _com_grafismo("eco", {"texto": vazio})), GATE), repr(vazio)
    with tempfile.TemporaryDirectory() as d:                  # carimbo e fita têm `texto` próprio e não entram nesta regra
        k = _com_grafismo("carimbo", {"texto": "APROVADO"})
        assert not so(_acab(d, k), GATE)
    with tempfile.TemporaryDirectory() as d:                  # número no JSON (2027 sem aspas) também é texto livre
        assert len(so(_acab(d, _com_grafismo("numeral-eco", {"texto": 2027})), GATE)) == 1
    sem_camada = {"schema_version": "mk-2.0", "composicao": {"capa": {"elementos": [{"id": "e", "grafismo": {"tipo": "eco", "params": {"texto": "X"}}}]}}}
    assert qa_conjunto.checar_acabamento(tempfile.gettempdir(), sem_camada) == []     # inverso: kit que não declara a camada, nada (como todo o acabamento)
    assert len(qa_conjunto.checar_texto_livre(sem_camada)) == 1                       # a função pura enxerga o grafismo; quem cala é a porta da camada
    k = _com_grafismo("eco", {"texto": "X"}); k["composicao"]["vertical:capa"] = k["composicao"].pop("capa")
    assert len(qa_conjunto.checar_texto_livre(k)) == 1        # a função pura lê toda a composição, vertical inclusive


def test_acabamento_continuidade_imprime_a_tabela():
    with tempfile.TemporaryDirectory() as d:
        k = kit21(); _pasta21(d, k); _plano_seq(d, k, ["capa", "divisor", "prova", "publico"])
        linhas = qa_conjunto.tabela_continuidade(d, k)
        txt = "\n".join(linhas)
        assert "fio condutor `lua`" in txt and "intensidade: 2 1 1 2" in txt, txt
        assert any(l.split()[:4] == ["1", "capa", "eco", "sim"] for l in linhas), txt
        assert any(l.split()[:4] == ["4", "publico", "-", "-"] for l in linhas), txt


def test_acabamento_fora_da_familia_e_da_novidade_mas_com_ocr():
    """O acabamento PNG do kit não é medido contra a família da receita (é textura, não herói), mas o OCR continua. O
    mesmo arquivo como apoio (inverso) cai na régua da família."""
    def com_textura(papel):
        def f(pl):
            pl["paginas"][4]["elementos"].append({"id": "grao-azul", "papel": papel, "camada": "atras", "x": 0, "y": 0, "w": 400,
                                                  "h": 300, "funcao": "acabamento", "origem": "plano"})
        return f
    for papel, deve_reprovar in (("acabamento", False), ("apoio", True)):
        with tempfile.TemporaryDirectory() as d:
            from test_plano_elementos import desenhar_linhas
            desenhar_linhas(Path(d) / "acervo/elementos/grao-azul.png", 7, cor=(0x20, 0x40, 0xF0))
            els = [heroi(f"h-novo-{i}", "kit-teste") for i in range(9)] + [pattern("pat-novo", "kit-teste")]
            extra = {"id": "grao-azul", "papel": papel, "tipo": "textura", "formato": "png", "familia": "linha-ouro", "motivo": "a",
                     "arquivo": "acervo/elementos/grao-azul.png", "kit_origem": "outro-kit", "gerado": True, "rota": "codex-alfa"}
            k, pl = montar_kit(d, els + [extra], sistema_teste())
            pl.pop("provisorio", None)
            com_textura(papel)(pl)
            (Path(d) / "saida" / "plano-elementos-r1.json").write_text(json.dumps(pl), encoding="utf-8")
            bib = Path(d) / "bib"; bib.mkdir()
            res = qa_conjunto.checar(d, bib=bib)
            fam = [m for m in falhas(res) if "`grao-azul` fora da família" in m]
            assert bool(fam) == deve_reprovar, (papel, fam)
            assert so(res, "`grao-azul` com OCR pendente"), (papel, res)
    # novidade: acabamento já estava fora de CONTAM_NOVIDADE antes da camada (heroi, ornamento, apoio, pattern); fica assim
    assert "acabamento" not in qa_conjunto.CONTAM_NOVIDADE


def test_derivado_fora_da_conta_de_heroi_e_de_elementos():
    def sombra(pl):
        pg = pl["paginas"][0]
        h = next(x for x in pg["elementos"] if x["papel"] == "heroi")
        pg["elementos"].append(dict(h, id=h["id"] + "-sombra", derivado_de=h["id"], papel="heroi"))
    with tempfile.TemporaryDirectory() as d:
        res = kit_gravado(d, None, sombra)
        assert not so(res, "-sombra") and not so(res, "2 heróis"), res
    def sem_derivado(pl):
        sombra(pl); pl["paginas"][0]["elementos"][-1].pop("derivado_de")
    with tempfile.TemporaryDirectory() as d:                      # inverso: sem derivado_de, é um segundo herói fora do JSON
        res = kit_gravado(d, None, sem_derivado)
        assert so(res, "2 heróis") and so(res, "-sombra"), res

if __name__ == "__main__":
    falhou = 0
    for nome, fn in list(globals().items()):
        if nome.startswith("test_"):
            try:
                fn(); print("ok  ", nome)
            except AssertionError as e:
                falhou += 1; print("FALHOU", nome, e)
    print("PROVAS:", "VERDES" if not falhou else f"{falhou} FALHA(S)")
    sys.exit(1 if falhou else 0)

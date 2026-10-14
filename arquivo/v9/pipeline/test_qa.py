#!/usr/bin/env python3
"""Provas do qa.py que não precisam de render. Rodar: ~/.venvs/mediakit/bin/python test_qa.py

Achado de 09/10/2026: a entrada da Sprint no historico-kits.json gravou `receitas[].fontes` como lista
([display, corpo]) e o checar_ledger esperava dicionário: o qa.py de QUALQUER kit com receitas caía com AttributeError
antes de imprimir uma linha (a prova caso_real do test_camadas pegou). E o próprio kit não saía da comparação, porque o
histórico grava o evento com edição e data e a igualdade exata nunca casava."""
import json, sys, tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import qa  # noqa: E402


def _hist(d, fontes, evento="Corrida X 2026 (1ª edição, 01/01/2026, Cidade/UF)"):
    p = Path(d) / "historico.json"
    p.write_text(json.dumps([{"evento": evento, "data": "2026-01-01",
                              "receitas": [{"id": "r1", "fontes": fontes, "variantes": {"capa": "b"}}]}]), encoding="utf-8")
    return p


def test_ledger_aceita_fontes_em_lista_e_avisa_par_repetido():
    receitas = [{"id": "r1", "fontes": {"display": "Kanit", "corpo": "Outfit"}, "variantes": {"capa": "c"}}]
    with tempfile.TemporaryDirectory() as d:
        qa.avisos.clear()
        qa.checar_ledger(receitas, {"evento": {"nome": "Outro Evento"}}, _hist(d, ["Kanit", "Outfit"]))
        assert any("Kanit + Outfit repete" in a for a in qa.avisos), qa.avisos
        qa.avisos.clear()
        qa.checar_ledger(receitas, {"evento": {"nome": "Outro Evento"}}, _hist(d, {"display": "Kanit", "corpo": "Outfit"}))
        assert any("Kanit + Outfit repete" in a for a in qa.avisos), qa.avisos


def test_ledger_tira_o_proprio_kit_da_comparacao():
    receitas = [{"id": "r1", "fontes": {"display": "Kanit", "corpo": "Outfit"}, "variantes": {"capa": "b"}}]
    with tempfile.TemporaryDirectory() as d:
        qa.avisos.clear()
        qa.checar_ledger(receitas, {"evento": {"nome": "Corrida X 2026"}}, _hist(d, ["Kanit", "Outfit"]))
        assert not qa.avisos, qa.avisos


def test_composicao_usa_vocabulario_sem_acento_e_nao_reprova():
    """Achado da prova da Sprint (09/10): `leitura: ["numero"]` e `y: "topo=numero.topo"` reprovavam como acento
    faltando. A composição é planejamento com vocabulário fechado; o texto do kit continua conferido."""
    k = {"tese": {"frase": "Corrida da cidade"},
         "composicao": {"publico:b": {"mensagem": "o número dominante", "leitura": ["numero", "titulo"],
                                      "elementos": [{"id": "x", "ancora": {"relacao": "alinha", "x": "esq=titulo.esq",
                                                                           "y": "topo=numero.topo"}, "porque": "liga o número à foto"}]}}}
    qa.falhas.clear()
    qa.checar_textos(k)
    assert not qa.falhas, qa.falhas


def test_texto_do_kit_e_prosa_da_composicao_continuam_conferidos():
    k = {"tese": {"frase": "O numero da pagina"},
         "composicao": {"capa": {"mensagem": "capa — com travessão", "leitura": ["numero"]}}}
    qa.falhas.clear()
    qa.checar_textos(k)
    assert any("tese.frase" in f and "número" in f for f in qa.falhas), qa.falhas
    assert any("composicao.capa.mensagem" in f and "travessão" in f for f in qa.falhas), qa.falhas
    assert not any("leitura" in f for f in qa.falhas), qa.falhas


def test_data_do_evento_aceita_so_o_ano_com_aviso_e_reprova_o_que_nao_e_iso():
    """Kit da A.M.E (09/10): temporada 2027 sem dia fechado. O QA reprovava `2027` enquanto a capa e os grafismos já
    aceitavam a data incompleta. Completa passa limpa; incompleta passa com aviso; fora do ISO reprova."""
    casos = {"2027-03-14": (0, 0), "2027-03": (0, 1), "2027": (0, 1), "14/03/2027": (1, 0), "2027-13": (1, 0),
             "2027-03-40": (1, 0), "": (1, 0), None: (1, 0), "março de 2027": (1, 0)}
    for data, (nf, na) in casos.items():
        qa.falhas.clear(); qa.avisos.clear()
        qa.checar_data(data)
        assert (len(qa.falhas), len(qa.avisos)) == (nf, na), (data, qa.falhas, qa.avisos)


def test_entregavel_de_futebol_e_transmissao_tem_posicao():
    """Kit da A.M.E (09/10): 8 avisos de 'sem posição' em entregáveis que dizem onde (peito da camisa, canto da tela,
    rodapé do app, feed). O que só diz quando, sem onde, continua avisado."""
    com = ["Peito da camisa da arbitragem e da organização", "Vídeo de 15 s em todas as transmissões da TV AME",
           "Janela fixa no app com link direto para o seu WhatsApp", "4 collabs no @amecrianca",
           "Logo no canto da tela em todas as transmissões", "Logo rotativo no rodapé do app da A.M.E",
           "2 collabs no feed do @amecrianca", "Brinde da marca entregue na entrada dos jogos",
           "Costas da camisa oficial", "Testeira da tenda"]
    sem = ["Brinde da marca em dia de jogo", "Ativação durante o evento", "Menção especial", "Aplicativo exclusivo"]
    assert all(qa.tem_posicao(e) for e in com), [e for e in com if not qa.tem_posicao(e)]
    assert not any(qa.tem_posicao(e) for e in sem), [e for e in sem if qa.tem_posicao(e)]


def test_elemento_foco_da_composicao_conta_como_dominante():
    """Teste da AME (09/10): o mapa do território é o foco declarado (foco grafico), mas o dominante só media texto e foto.
    Com a composição dizendo que o foco é o elemento, a tinta do herói entra na disputa; sem essa declaração, não."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        pasta = Path(d); (pasta / "saida").mkdir()
        tinta = [1008, 140, 1744, 830]                       # 736 x 690 = 33% da área útil (1728 x 888)
        plano = {"largura": 1920, "altura": 1080, "paginas": [
            {"n": 5, "rotulo": "territorio", "tipo": "territorio", "rotulos": ["territorio"],
             "elementos": [{"id": "mapa-sedes-p5", "papel": "heroi", "ancora": {"tinta": tinta}}]}]}
        (pasta / "saida" / "plano-elementos-r1.json").write_text(json.dumps(plano), encoding="utf-8")
        el = {"id": "mapa-sedes", "papel": "heroi", "funcao": "contexto", "porque": "x",
              "ancora": {"relacao": "alinha", "x": "esq=coluna:7.esq", "y": "cy=corpo.cy"}}
        k = {"composicao": {"territorio": {"mensagem": "m", "foco": "grafico", "elementos": [el]}}}
        f = qa.tinta_do_foco(pasta, k, "r1")
        assert abs(f[5] - 736 * 690 / (1728 * 888)) < 1e-9, f
        assert qa.dominante_com_foco(0.08, 0.05, f[5]) == (f[5], 0.08)
        k["composicao"]["territorio"]["foco"] = "titulo"
        assert qa.tinta_do_foco(pasta, k, "r1") == {}, "sem foco no elemento, ele continua camada"
        assert qa.dominante_com_foco(0.08, 0.05, None) == (0.08, 0.05)



# ================================================================================================= camada de acabamento (mk-2.1)
import hashlib, shutil, subprocess  # noqa: E402

KIT_PROVA = AQUI.parent / "exemplos" / "acabamento-prova"


def _copia_prova(d, versao=None, mexer=None):
    """Cópia do kit fictício do acabamento (sem saida/) numa pasta temporária, com a versão e a mudança pedidas."""
    destino = Path(d) / "kit"
    shutil.copytree(KIT_PROVA, destino, ignore=shutil.ignore_patterns("saida"))
    k = json.loads((destino / "mediakit.json").read_text(encoding="utf-8"))
    if versao:
        k["schema_version"] = versao
    if mexer:
        mexer(k)
    (destino / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False, indent=1), encoding="utf-8")
    return destino, k


def _roda_qa(pasta):
    r = subprocess.run([sys.executable, str(AQUI / "qa.py"), str(pasta), "--ambiente-sem-fontes"], capture_output=True,
                       text=True, cwd=str(AQUI))
    return r.stdout + r.stderr


def test_qa_aceita_mk21_e_recusa_versao_desconhecida():
    """O qa.py exigia mk-2.0 e reprovava o kit mk-2.1 na primeira linha (sem olhar mais nada)."""
    with tempfile.TemporaryDirectory() as d:
        pasta, _ = _copia_prova(d)
        out = _roda_qa(pasta)
        assert "schema_version deve ser" not in out and "falta `" not in out, out[-800:]
    with tempfile.TemporaryDirectory() as d:
        pasta, _ = _copia_prova(d, "mk-9.9")
        out = _roda_qa(pasta)
        assert "FALHA  schema_version deve ser mk-2.0 ou mk-2.1" in out, out[-800:]


def test_paginas_e_formato_base_sao_ids_e_nao_texto():
    """Falso positivo do kit de prova (12/10): "paginas[5]: `publico` sem acento". `paginas` lista tipos de página e
    `formato_base` é id e sha256: ficam fora do acento. O texto do kit continua conferido."""
    k = {"paginas": ["capa", "publico", {"tipo": "publico", "variante": "a"}], "formato_base": {"id": "numero-um-publico"},
         "tese": {"frase": "Corrida da cidade"}}
    qa.falhas.clear()
    qa.checar_textos(k)
    assert not qa.falhas, qa.falhas
    k["tese"]["frase"] = "O publico da corrida"
    qa.checar_textos(k)
    assert len(qa.falhas) == 1 and "tese.frase" in qa.falhas[0] and "público" in qa.falhas[0], qa.falhas


def test_direcao_criativa_e_planejamento_com_travessao_conferido():
    k = {"direcao_criativa": {"recursos": [{"id": "eco", "familia": "tipografia-expressiva", "referencia": "numero-heroi",
                                           "principio": "o numero se repete atras", "nao_copiar": "a fonte"}]}}
    qa.falhas.clear()
    qa.checar_textos(k)
    assert not qa.falhas, qa.falhas
    k["direcao_criativa"]["recursos"][0]["principio"] = "o título se repete — atrás"
    qa.checar_textos(k)
    assert len(qa.falhas) == 1 and "direcao_criativa.recursos[0].principio" in qa.falhas[0] and "travessão" in qa.falhas[0], qa.falhas


def test_numero_dentro_de_id_do_repertorio_nao_e_numero_sem_prova():
    """O repertório tem ids como web-deck-media-kit-245250053: na direção criativa é id, não número do kit."""
    def mexer(k):
        k["direcao_criativa"]["recursos"][0]["referencia"] = "web-deck-media-kit-245250053"
        k["tese"]["frase"] = "245250053 pessoas correm junto"
    with tempfile.TemporaryDirectory() as d:
        pasta, _ = _copia_prova(d, mexer=mexer)
        out = _roda_qa(pasta)
        linhas = [l for l in out.splitlines() if "245250053" in l and l.startswith("FALHA")]
        assert len(linhas) == 1 and "tese.frase" in linhas[0], linhas


def _indice(d):
    p = Path(d) / "indice.json"
    p.write_text(json.dumps({"versao": 1, "padroes": [{"id": "palavra-gigante-atras-da-figura"}], "referencias": []}), encoding="utf-8")
    return p


def _kit_tres_familias(versao, nao_usa=()):
    recs = [{"id": f"r{i}", "familia": f, "referencia": "palavra-gigante-atras-da-figura", "principio": "o princípio do recurso",
             "rota": "codigo"} for i, f in enumerate(("tipografia-expressiva", "pattern-textura", "profundidade-3d"))]
    return {"schema_version": versao, "evento": {"nome": "Corrida Teste"},
            "direcao_criativa": {"recursos": recs, "nao_usa": list(nao_usa)},
            "composicao": {"capa": {"mensagem": "a capa", "acabamento": {"recursos": ["r1"], "intensidade": 1, "porque": "o porquê da capa"}}}}


def test_avisos_e_falhas_do_acabamento_validar_chegam_ao_relatorio():
    """Antes só as falhas que a composição decide sozinha chegavam (pelo plano). Agora: os avisos do acabamento.validar
    (mk-2.0 com direção criativa: famílias poucas é aviso) e as falhas que dependem do kit (família proibida usada)."""
    with tempfile.TemporaryDirectory() as d:
        pasta = Path(d)
        qa.falhas.clear(); qa.avisos.clear()
        qa.checar_acabamento(pasta, _kit_tres_familias("mk-2.0"), indice=_indice(d))
        assert any(a.startswith("acabamento: direcao_criativa/recursos: 3 família(s)") for a in qa.avisos), qa.avisos
        assert not any("família(s)" in f for f in qa.falhas), qa.falhas
        # mk-2.1: a mesma conta vira FALHA (qa_conjunto) e o aviso do acabamento.validar não sai repetido
        qa.falhas.clear(); qa.avisos.clear()
        qa.checar_acabamento(pasta, _kit_tres_familias("mk-2.1"), indice=_indice(d))
        assert any("3 família(s) distinta(s)" in f for f in qa.falhas) and not any("família(s)" in a for a in qa.avisos), (qa.falhas, qa.avisos)
        # família proibida usada numa página: FALHA do acabamento.validar que não tinha canal no QA
        qa.falhas.clear(); qa.avisos.clear()
        qa.checar_acabamento(pasta, _kit_tres_familias("mk-2.0", ["pattern-textura"]), indice=_indice(d))
        assert any(f.startswith("acabamento: composicao/capa/acabamento: recurso `r1` é da família pattern-textura") for f in qa.falhas), qa.falhas
        # inverso: kit sem a camada não passa por nada
        qa.falhas.clear(); qa.avisos.clear()
        qa.checar_acabamento(pasta, {"schema_version": "mk-2.0", "evento": {"nome": "X"}})
        assert not qa.falhas and not qa.avisos


def test_falha_da_composicao_nao_sai_duas_vezes_quando_ha_plano():
    k = _kit_tres_familias("mk-2.0")
    k["composicao"]["capa"]["elementos"] = [
        {"id": f"g{i}", "grafismo": {"tipo": "fio"}, "papel": "acabamento", "funcao": "acabamento", "motivo": "lua",
         "ancora": {"relacao": "alinha", "x": "esq=margem.esq", "y": "topo=margem.topo"}} for i in range(3)]
    k["sistema_elementos"] = {"motivos": [{"id": "lua"}]}
    with tempfile.TemporaryDirectory() as d:
        pasta = Path(d)
        qa.falhas.clear(); qa.avisos.clear()
        qa.checar_acabamento(pasta, k, indice=_indice(d))
        assert len([f for f in qa.falhas if "3 elementos de papel acabamento" in f]) == 1, qa.falhas     # sem plano: sai daqui
        (pasta / "saida").mkdir()
        (pasta / "saida" / "plano-elementos-r1.json").write_text(json.dumps({"paginas": []}), encoding="utf-8")
        (pasta / "saida" / "render-report.json").write_text("{}", encoding="utf-8")
        qa.falhas.clear(); qa.avisos.clear()
        qa.checar_acabamento(pasta, k, indice=_indice(d))
        assert not [f for f in qa.falhas if "3 elementos de papel acabamento" in f], qa.falhas           # com plano: do qa_geometria


def test_formato_base_confere_contra_o_travado():
    import formato
    with tempfile.TemporaryDirectory() as d:
        pasta, k = _copia_prova(d)
        raiz = Path(d) / "formatos"; (raiz / "teste-formato").mkdir(parents=True)
        f = {"formato": "teste-formato", "versao": 1, "travado": formato.travado_do_kit(k), "arquivos": {}}
        bruto = json.dumps(f, ensure_ascii=False).encode("utf-8")
        (raiz / "teste-formato" / "formato.json").write_bytes(bruto)
        k["formato_base"] = {"id": "teste-formato", "versao": 1, "sha256": hashlib.sha256(bruto).hexdigest()}
        (raiz / "teste-formato" / "versoes").mkdir(); (raiz / "teste-formato" / "versoes" / "v1.json").write_bytes(bruto)
        (pasta / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False), encoding="utf-8")
        qa.avisos.clear()
        qa.checar_formato(pasta, k, raiz)
        assert not qa.avisos, qa.avisos
        k["receitas"][0]["fundo"] = "papel"
        (pasta / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False), encoding="utf-8")
        qa.avisos.clear()
        qa.checar_formato(pasta, k, raiz)
        assert len(qa.avisos) == 1 and "`receita.fundo` difere do travado" in qa.avisos[0] and '"papel"' not in qa.avisos[0] \
            and "kit papel" in qa.avisos[0], qa.avisos
        k["formato_base"]["id"] = "nao-existe"
        (pasta / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False), encoding="utf-8")
        qa.avisos.clear()
        qa.checar_formato(pasta, k, raiz)
        assert len(qa.avisos) == 1 and "não conferido" in qa.avisos[0], qa.avisos


def test_vertical_vai_ao_validar_pdf_com_pagina_em_pe():
    """O vertical saía partido em todo kit (6 folhas deitadas para 3 páginas em pé) e não passava pelo validar_pdf."""
    with tempfile.TemporaryDirectory() as d:
        pasta = Path(d); (pasta / "saida" / "html").mkdir(parents=True)
        for nome in ("kit-r1.pdf", "kit-r1-vertical.pdf", "html/kit-r1.html"):
            (pasta / "saida" / nome).write_text("x", encoding="utf-8")
        r = {"direcoes": {"r1": {"pageplan": [{"cena": True}], "horizontal": {"por_pagina": []},
                                 "vertical": {"por_pagina": [{"textos": [{"texto": "Dez mil atletas"}]}]}}}}
        k = {"marca": {"fonte_display": "Anton", "fonte_corpo": "DM Sans"}, "evento": {"nome": "Copa"}, "tese": {"frase": "T"}}
        h = qa.cmd_validar_pdf(pasta, k, r, "r1", False, False)
        v = qa.cmd_validar_pdf(pasta, k, r, "r1", True, False)
        assert "--cenas" in h and "--paginas" not in h and "--imagens-esperadas" not in h, h
        assert v[v.index("--paginas") + 1] == "1080x1920" and "--cenas" not in v and "--por-pagina" in v, v
        assert json.loads((pasta / "saida" / "textos-por-pagina-r1-vertical.json").read_text()) == [["Dez mil atletas"]]
        a = qa.cmd_validar_pdf(pasta, k, r, "r1", False, True)
        assert a[a.index("--imagens-esperadas") + 1].endswith("html/kit-r1.html"), a
        assert qa.cmd_validar_pdf(pasta, k, r, "r2", False, True) is None


# ================================================================================================= kit só horizontal (13/10/2026)
# O copa-ame-v3 declara `paginas` com as 18 páginas horizontais e é renderizado com --sem-vertical, mas o mediakit.json
# guarda as três composicao `vertical:*` da gramática do formato. O QA cobrava `acabamento` de páginas que não existem.
import copy  # noqa: E402


def _el_acab(eid, tipo):
    return {"id": eid, "grafismo": {"tipo": tipo}, "papel": "acabamento", "funcao": "acabamento", "motivo": "lua",
            "ancora": {"relacao": "alinha", "x": "esq=margem.esq", "y": "topo=margem.topo"}}


def _kit_com_vertical(paginas=None):
    """mk-2.1 fictício: 3 páginas horizontais em ordem, mais as 3 composicao `vertical:*` com um defeito do acabamento
    cada: `vertical:capa` sem `acabamento`, com 3 elementos de acabamento, recurso fora da direção e o fio com tratamento
    diferente; `vertical:numeros` com 4 recursos (intensidade 4); `vertical:contato` na tabela do fio sem o motivo."""
    fam = ("tipografia-expressiva", "pattern-textura", "profundidade-3d", "acabamento-borda")
    recs = [{"id": f"r{i}", "familia": f, "referencia": "palavra-gigante-atras-da-figura", "principio": "o princípio do recurso",
             "rota": "codigo"} for i, f in enumerate(fam)]
    pag = lambda: {"mensagem": "a página", "acabamento": {"recursos": ["r0"], "intensidade": 1, "porque": "o porquê"},  # noqa: E731
                   "elementos": [_el_acab("fio-h", "aneis")]}
    vcapa = {"mensagem": "a capa em pé", "elementos": [_el_acab("v1", "fio"), _el_acab("v2", "fio"), _el_acab("v3", "fio")]}
    vcapa["elementos"][0]["recurso"] = "fora"
    k = {"schema_version": "mk-2.1", "evento": {"nome": "Corrida Teste"}, "sistema_elementos": {"motivos": [{"id": "lua"}]},
         "direcao_criativa": {"recursos": recs, "fio_condutor": {"motivo": "lua", "papeis": {
             "capa": "selo", "manifesto": "eco", "publico": "eco", "vertical:capa": "eco", "vertical:contato": "eco"}}},
         "composicao": {"capa": pag(), "manifesto": pag(), "publico": pag(), "vertical:capa": vcapa,
                        "vertical:numeros": {"mensagem": "os números", "acabamento": {"recursos": ["r0", "r1", "r2", "r3"],
                                                                                    "intensidade": 1, "porque": "o porquê"}},
                        "vertical:contato": {"mensagem": "o contato", "acabamento": {"recursos": ["r0"], "intensidade": 1,
                                                                                    "porque": "o porquê"}}}}
    if paginas is not None:
        k["paginas"] = paginas
    return k


HORIZONTAIS = ["capa", "manifesto", "publico"]


def _roda_acabamento(k, relatorio=None):
    """(falhas, avisos) que o qa.checar_acabamento dá ao kit, com o render-report gravado se `relatorio` vier."""
    with tempfile.TemporaryDirectory() as d:
        pasta = Path(d)
        if relatorio is not None:
            (pasta / "saida").mkdir()
            (pasta / "saida" / "render-report.json").write_text(json.dumps(relatorio), encoding="utf-8")
        qa.falhas.clear(); qa.avisos.clear()
        qa.checar_acabamento(pasta, k, indice=_indice(d))
        return list(qa.falhas), list(qa.avisos)


DEFEITOS_DO_VERTICAL = ("composicao/vertical:capa: página composta sem `acabamento`",       # qa_conjunto.checar_paginas
                        "composicao/vertical:capa: 3 elementos de papel acabamento",          # acabamento.validar
                        "recurso `fora` (em vertical:capa)",                                   # qa_conjunto.checar_recursos
                        "composicao/vertical:numeros: intensidade calculada 4",              # qa_conjunto.checar_intensidade
                        "o fio condutor `lua` muda de tratamento",                             # qa_conjunto.checar_fio (FALHA)
                        "a página `vertical:contato` está na tabela do fio condutor")        # qa_conjunto.checar_fio (AVISO)


def _linhas(falhas, avisos):
    return "\n".join(falhas + avisos)


def test_kit_so_horizontal_pula_as_composicoes_vertical():
    """`paginas` só horizontal e nenhum render-report: nenhuma regra do acabamento (página sem `acabamento`, recurso, fio,
    intensidade, máximo por página) olha `vertical:*`; o que o QA pulou vira UM aviso, e o resto sai igual ao do mesmo kit
    sem as composições vertical."""
    falhas, avisos = _roda_acabamento(_kit_com_vertical(HORIZONTAIS))
    assert "vertical:" not in "\n".join(falhas), falhas
    avisos_v = [a for a in avisos if "vertical:" in a]
    assert len(avisos_v) == 1 and "não conferida(s)" in avisos_v[0] and "`paginas` declara só páginas horizontais" in avisos_v[0] \
        and all(f"composicao/vertical:{c}" in avisos_v[0] for c in ("capa", "numeros", "contato")), avisos
    # o resto é o do kit que nunca teve a gramática vertical: as regras das páginas horizontais não mudaram
    k = _kit_com_vertical(HORIZONTAIS)
    k["composicao"] = {c: v for c, v in k["composicao"].items() if not c.startswith("vertical:")}
    for c in ("vertical:capa", "vertical:contato"):
        del k["direcao_criativa"]["fio_condutor"]["papeis"][c]
    f_h, a_h = _roda_acabamento(k)
    assert falhas == f_h and [a for a in avisos if "vertical:" not in a] == a_h, (falhas, f_h, avisos, a_h)


def test_kit_que_gera_vertical_continua_cobrando_as_composicoes_vertical():
    """O inverso: sem `paginas` (o render gera o vertical), com item vertical em `paginas`, ou com vertical no
    render-report (o fato vence a declaração), as seis respostas voltam e nenhum aviso de omissão sai."""
    cenarios = {"sem paginas": (_kit_com_vertical(), None),
                "paginas com item vertical (string)": (_kit_com_vertical(HORIZONTAIS + ["vertical:capa"]), None),
                "paginas com item vertical ({tipo})": (_kit_com_vertical(HORIZONTAIS + [{"tipo": "vertical:contato"}]), None),
                "render-report com vertical, paginas só horizontal": (
                    _kit_com_vertical(HORIZONTAIS), {"direcoes": {"r1": {"horizontal": {}, "vertical": {}}}})}
    for nome, (k, rel) in cenarios.items():
        falhas, avisos = _roda_acabamento(k, rel)
        saida = _linhas(falhas, avisos)
        faltam = [d for d in DEFEITOS_DO_VERTICAL if d not in saida]
        assert not faltam, (nome, faltam)
        assert not any("não conferida(s)" in a for a in avisos), (nome, avisos)


def test_render_report_sem_vertical_pula_mesmo_sem_paginas():
    """O fato vence: render --sem-vertical grava as direções sem a chave `vertical`; o kit sem `paginas` também é só
    horizontal. O aviso diz que foi o render-report que mostrou."""
    falhas, avisos = _roda_acabamento(_kit_com_vertical(), {"direcoes": {"r1": {"horizontal": {}}}})
    assert "vertical:" not in "\n".join(falhas), falhas
    avisos_v = [a for a in avisos if "vertical:" in a]
    assert len(avisos_v) == 1 and "o render-report não tem vertical" in avisos_v[0], avisos


def test_gera_vertical_e_sem_vertical_em_miudos():
    import acabamento
    com, sem = {"direcoes": {"r1": {"horizontal": {}, "vertical": {}}}}, {"direcoes": {"r1": {"horizontal": {}}}}
    tabela = [({}, None, True), ({"paginas": []}, None, True), ({"paginas": ["capa", "contato"]}, None, False),
              ({"paginas": ["capa", "vertical"]}, None, True), ({"paginas": [{"tipo": "vertical:capa"}]}, None, True),
              ({"paginas": [{"tipo": "capa"}, "contato"]}, {}, False), ({"paginas": ["capa"]}, {"avisos": []}, False),
              ({"paginas": ["capa"]}, com, True), ({}, sem, False), ({}, com, True),
              ({"paginas": ["capa"]}, {"direcoes": {"r1": {}, "r2": {"vertical": {}}}}, True)]
    for k, rel, esperado in tabela:
        assert acabamento.gera_vertical(k, rel)[0] is esperado, (k, rel, esperado)
        assert bool(acabamento.gera_vertical(k, rel)[1]) is (not esperado), (k, rel)   # o porquê só vem quando NÃO gera
    k = _kit_com_vertical(HORIZONTAIS)
    antes = copy.deepcopy(k)
    v = acabamento.sem_vertical(k)
    assert k == antes, "sem_vertical não mexe no kit de quem chamou"
    assert not acabamento.chaves_vertical(v) and sorted(v["composicao"]) == sorted(HORIZONTAIS), v["composicao"].keys()
    assert sorted(v["direcao_criativa"]["fio_condutor"]["papeis"]) == sorted(HORIZONTAIS)
    assert acabamento.chaves_vertical(k) == ["vertical:capa", "vertical:numeros", "vertical:contato"]
    assert acabamento.sem_vertical(v) == v and acabamento.sem_vertical({}) == {}


def test_validar_pdf_nao_cobra_o_vertical_de_kit_so_horizontal():
    """Sobrou um kit-r1-vertical.pdf de um render antigo e o render atual foi --sem-vertical: ele não é entrega."""
    with tempfile.TemporaryDirectory() as d:
        pasta = Path(d); (pasta / "saida" / "html").mkdir(parents=True)
        for nome in ("kit-r1.pdf", "kit-r1-vertical.pdf"):
            (pasta / "saida" / nome).write_text("x", encoding="utf-8")
        k = {"marca": {"fonte_display": "Anton", "fonte_corpo": "DM Sans"}, "evento": {"nome": "Copa"}, "tese": {"frase": "T"}}
        sem = {"direcoes": {"r1": {"pageplan": [{"cena": True}], "horizontal": {"por_pagina": []}}}}
        com = {"direcoes": {"r1": {"pageplan": [{"cena": True}], "horizontal": {"por_pagina": []}, "vertical": {"por_pagina": []}}}}
        assert qa.cmd_validar_pdf(pasta, k, sem, "r1", True, False) is None
        assert qa.cmd_validar_pdf(pasta, k, sem, "r1", False, False) is not None, "o horizontal segue validado"
        assert qa.cmd_validar_pdf(pasta, k, com, "r1", True, False) is not None


def test_mutante_regra_do_vertical_desligada_e_acusada():
    """Desliga a regra de dois jeitos (diz que sempre gera vertical; ou não tira as composições do kit) e confere que as
    provas acima acusam. Sem isso elas passariam também com a regra vazia."""
    import acabamento
    provas = (test_kit_so_horizontal_pula_as_composicoes_vertical, test_render_report_sem_vertical_pula_mesmo_sem_paginas,
              test_validar_pdf_nao_cobra_o_vertical_de_kit_so_horizontal)
    original = (acabamento.gera_vertical, acabamento.sem_vertical)
    mutantes = {"gera_vertical sempre True": dict(gera_vertical=lambda k, relatorio=None: (True, "")),
                "sem_vertical não tira nada": dict(sem_vertical=lambda k: k)}
    try:
        for nome, troca in mutantes.items():
            for chave, fn in troca.items():
                setattr(acabamento, chave, fn)
            vivas = []
            for prova in provas:
                try:
                    prova()
                    vivas.append(prova.__name__)
                except AssertionError:
                    pass
            acabamento.gera_vertical, acabamento.sem_vertical = original
            esperado_vivas = {"gera_vertical sempre True": [], "sem_vertical não tira nada":
                              ["test_validar_pdf_nao_cobra_o_vertical_de_kit_so_horizontal"]}[nome]   # essa não usa sem_vertical
            assert vivas == esperado_vivas, (nome, vivas)
    finally:
        acabamento.gera_vertical, acabamento.sem_vertical = original

if __name__ == "__main__":
    falhas = 0
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            try:
                f(); print("ok  ", nome)
            except Exception as e:
                falhas += 1; print("FALHOU", nome, type(e).__name__, e)
    print("PROVAS:", "VERDES" if not falhas else f"{falhas} FALHA(S)")
    sys.exit(1 if falhas else 0)

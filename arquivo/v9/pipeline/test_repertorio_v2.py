#!/usr/bin/env python3
"""Provas do estudo visual v2 e do schema v2 do repertório (12/10/2026). Rodar:
~/.venvs/mediakit/bin/python test_repertorio_v2.py (ou pytest). Só leitura: nada no repertório nem no kit é escrito.

O que se prova:
- o índice atual (v1) continua válido no schema v2, pelo validador próprio e pelo do repertorio.py (quem consome);
- um índice v2 com 1 recurso (montado do front matter e do trecho do briefing-redator-v2.md) valida, e o trecho de
  acabamento do briefing passa no schema do kit, na composição e no acabamento.py;
- valor fora do vocabulário em cada campo novo reprova (um caso por campo), e `recursos` com versao 1 reprova;
- o bloco `vocabulario` da RUBRICA-v2.md é igual às listas do schema (e as famílias, às do kit);
- padroes-v1.txt tem 31 linhas e é o que o gerador produz do índice;
- o exemplo de candidato da rubrica é JSON válido, igual ao arquivo, e passa em `conferir_candidato`, que por sua vez
  reprova cada defeito plantado (não é conferência vazia);
- nenhum entregável do estudo tem travessão nem meia-risca.
Terminam em `PROVAS: VERDES`."""
import copy, json, math, re, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
ESTUDO = RAIZ / "repertorio" / "estudo"
INDICE = RAIZ / "repertorio" / "indice.json"
FONTES = RAIZ / "repertorio" / "fontes.json"
SCHEMA = RAIZ / "schema" / "repertorio.schema.json"
SCHEMA_EL = RAIZ / "schema" / "elementos.schema.json"
SCHEMA_KIT = RAIZ / "schema" / "mediakit.schema.json"
RUBRICA = ESTUDO / "RUBRICA-v2.md"
BRIEFING = ESTUDO / "briefing-redator-v2.md"
EXEMPLO = ESTUDO / "exemplo-candidato-v2.json"
PADROES_V1 = ESTUDO / "padroes-v1.txt"
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(ESTUDO))

TRAVESSOES = ("\u2014", "\u2013")


def ler(p):
    return Path(p).read_text(encoding="utf-8")


def carregar(p):
    return json.loads(ler(p))


# ------------------------------------------------------------------------------------------- schema e registro
def registro():
    """Schema do repertório e o registro que resolve o $ref para elementos.schema.json (como o repertorio.py faz)."""
    from referencing import Registry, Resource
    el, sch = carregar(SCHEMA_EL), carregar(SCHEMA)
    return sch, Registry().with_resources([(el["$id"], Resource.from_contents(el)), (sch["$id"], Resource.from_contents(sch))])


def erros_indice(indice):
    """[(caminho, mensagem)] do índice contra o schema v2."""
    import jsonschema
    sch, reg = registro()
    v = jsonschema.Draft7Validator(sch, registry=reg)
    return [(tuple(e.absolute_path), e.message) for e in v.iter_errors(indice)]


def defs():
    return carregar(SCHEMA)["definitions"]


# ------------------------------------------------------------------------------------------- textos
def bloco(texto, linguagem, depois_de=None):
    """Conteúdo do primeiro bloco ```<linguagem> do texto (depois do marcador `depois_de`, se dado)."""
    if depois_de is not None:
        i = texto.find(depois_de)
        assert i >= 0, f"marcador `{depois_de}` não encontrado"
        texto = texto[i:]
    m = re.search(rf"```{linguagem}\n(.*?)\n```", texto, re.S)
    assert m, f"bloco ```{linguagem} não encontrado"
    return m.group(1)


def front(texto):
    """Front matter no formato do repertório (o mesmo parser dos scripts v1): `chave: valor` ou `chave: [a, b]`."""
    m = re.search(r"^---\n(.*?)\n---$", texto, re.S | re.M)
    assert m, "sem front matter"
    d = {}
    for linha in m.group(1).splitlines():
        k, _, v = linha.partition(":")
        v = v.strip()
        d[k.strip()] = [x.strip() for x in v[1:-1].split(",") if x.strip()] if v.startswith("[") else v
    return d


def vocabulario():
    """O bloco ```vocabulario da RUBRICA-v2.md: {campo: [valores]}."""
    voc = {}
    for linha in bloco(ler(RUBRICA), "vocabulario").splitlines():
        k, _, v = linha.partition(":")
        voc[k.strip()] = [x.strip() for x in v.split(",") if x.strip()]
    return voc


# ------------------------------------------------------------------------------------------- o recurso do briefing
def trecho_do_briefing():
    return json.loads(bloco(ler(BRIEFING), "json", depois_de="Trecho de acabamento:"))


def front_do_briefing():
    return front(bloco(ler(BRIEFING), "yaml"))


RECORTE_V2 = {"arquivo": "recortes/objeto-com-material-cruza-o-titulo__ref-exemplo-07.jpg", "referencia": "ref-exemplo",
              "pagina": 7, "legenda": "o objeto passa na frente da primeira linha do título e atrás da segunda",
              "anotado": "recortes/objeto-com-material-cruza-o-titulo__ref-exemplo-07--anotado.jpg",
              "anotacoes": [{"n": 1, "caixa": [0.1, 0.2, 0.5, 0.6], "seta": [0.6, 0.7, 0.4, 0.5], "rotulo": "sombra de contato de 1,2% da altura"},
                            {"n": 2, "caixa": [0.5, 0.3, 0.9, 0.5], "rotulo": "corte na linha de base da primeira linha"}]}


def recurso_do_briefing():
    """A entrada de `recursos[]` que o montador do índice faria a partir do .md do briefing."""
    f = front_do_briefing()
    r = {k: v for k, v in f.items() if k != "id"}
    r.update(id=f["id"], arquivo=f"recursos/{f['id']}.md", intensidade=[int(x) for x in f["intensidade"]], uau=int(f["uau"]),
             recortes=[copy.deepcopy(RECORTE_V2)], acabamento_exemplo=trecho_do_briefing())
    return r


def indice_v2():
    """O índice atual levado à versão 2: 1 recurso e um exemplo de cada campo novo de padrão, recorte e referência."""
    i = copy.deepcopy(carregar(INDICE))
    i["versao"] = 2
    i["recursos"] = [recurso_do_briefing()]
    p = i["padroes"][0]
    p["dimensoes"] = ["sobreposicao-recorte", "continuidade"]
    p["recursos"] = ["objeto-com-material-cruza-o-titulo"]
    rc = p["recortes"][0]
    rc["anotado"] = rc["arquivo"].rsplit(".", 1)[0] + "--anotado.jpg"
    rc["anotacoes"] = [{"n": 1, "caixa": [0.05, 0.1, 0.5, 0.6], "rotulo": "zona lisa onde mora o texto"}]
    ref = i["referencias"][0]
    ref.update(camada_v2="regua", captura={"manifesto": f"fontes/{ref['id']}.json", "status": "ok", "paginas": 24},
               serie={"constantes": ["margem de 6% da largura"], "variaveis": ["foto troca de lado por seção"],
                      "por_tipo": {"capa": "foto inteira e título na zona lisa"},
                      "ritmo": {"padrao": "blocos", "paginas": {"1": "abertura", "2": "respiro", "3": "dados"}}},
               uau_paginas=[{"pagina": 1, "nota": 2, "gatilhos": ["escala"], "primeiro_olhar": "o rio, depois o título"},
                            {"pagina": 14, "nota": 1, "gatilhos": ["cor"], "depende_de": "foto"}])
    return i


def por(d, caminho, valor):
    alvo = d
    for k in caminho[:-1]:
        alvo = alvo[k]
    alvo[caminho[-1]] = valor
    return d


# ------------------------------------------------------------------------------------------- conferência do trecho
LUZ_KIT = {"esq": "esq", "dir": "dir", "topo": "topo"}
PROF_KIT = {"plana": "plana", "camadas": "camadas", "sombra": "camadas", "perspectiva": "volume", "isometrica": "volume",
            "volume": "volume", "cena": "volume"}


def conferir_trecho(fm, trecho):
    """Erros do trecho de acabamento de um recurso: schema do kit (direcao_criativa), composição (schema, âncoras e
    regras de acabamento que a página sozinha decide) e coerência com o front matter."""
    import jsonschema, composicao
    erros = []
    rid = fm["id"]
    dc, pag = trecho.get("direcao_criativa"), trecho.get("pagina")
    v = jsonschema.Draft202012Validator(carregar(SCHEMA_KIT)["properties"]["direcao_criativa"])
    erros += [f"direcao_criativa/{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in v.iter_errors(dc)]
    ids = [e.get("id") for e in (pag or {}).get("elementos") or [] if isinstance(e, dict)]
    erros += composicao.validar({"exemplo": pag}, ids)
    if rid not in [r.get("id") for r in (dc or {}).get("recursos") or []]:
        erros.append("o id do recurso não está em direcao_criativa.recursos")
    ac = (pag or {}).get("acabamento") or {}
    if rid not in (ac.get("recursos") or []):
        erros.append("o id do recurso não está em pagina.acabamento.recursos")
    if rid not in [e.get("recurso") for e in (pag or {}).get("elementos") or []]:
        erros.append("nenhum elemento leva `recurso` com o id")
    lo, hi = (int(x) for x in fm["intensidade"])
    teto = ((dc or {}).get("intensidade") or {}).get("teto", 3)
    if not (lo <= ac.get("intensidade", lo) <= hi) or ac.get("intensidade", 0) > teto:
        erros.append(f"intensidade da página {ac.get('intensidade')} fora de [{lo}, {hi}] ou acima do teto {teto}")
    if ac.get("luz", "nenhuma") != LUZ_KIT.get(fm["luz_direcao"], "nenhuma"):
        erros.append(f"acabamento.luz {ac.get('luz')} não corresponde a luz_direcao {fm['luz_direcao']}")
    if ac.get("profundidade") and ac["profundidade"] != PROF_KIT[fm["profundidade"]]:
        erros.append(f"acabamento.profundidade {ac['profundidade']} não corresponde a {fm['profundidade']}")
    return erros


# ------------------------------------------------------------------------------------------- conferência do candidato
OBRIG_TOPO = ("referencia", "fonte", "camada", "analista", "lentes", "resumo", "paginas_total", "paginas_abertas",
              "mockups", "folhas", "serie", "uau_paginas", "padroes")
OBRIG_V1 = ("id_sugerido", "nome", "problema", "efeito", "tipo_pagina", "funcao", "relacao", "rota", "tom", "densidade",
            "exemplos", "organizacao", "essencial", "variavel", "adaptar", "erros", "construcao")
OBRIG_V2 = ("familia", "dimensoes", "recurso", "material", "luz", "luz_direcao", "profundidade", "intensidade",
            "continuidade", "tratamento_imagem", "tipografia", "borda", "mistura", "producao", "uau", "ja_coberto_por",
            "diferenca")
LISTAS = {"tipo_pagina": "tipo_pagina", "funcao": "funcao", "relacao": "relacao", "tom": "tom", "dimensoes": "dimensao",
          "recurso": "recurso", "material": "material", "tratamento_imagem": "tratamento_imagem", "tipografia": "tipografia",
          "borda": "borda", "mistura": "mistura"}
UNICOS = {"rota": "rota", "densidade": "densidade", "familia": "familia", "luz": "luz", "luz_direcao": "luz_direcao",
          "profundidade": "profundidade", "continuidade": "continuidade"}
ROTA_DA_VIA = {"codigo-svg-css": "codigo", "grafismo-existente": "codigo", "raster-tratar": "imagem",
               "codex-objeto": "imagem", "codex-textura": "imagem", "codex-cena": "imagem",
               "compor-homografia": "hibrido", "misto": "hibrido"}
CAMADA_DA_FONTE = {"prioritaria": "prioritaria", "profunda": "profunda", "releitura": "releitura", "lente": "lente",
                   "regua": "lente"}


def _caixa_ok(c):
    return (isinstance(c, list) and len(c) == 4 and all(isinstance(x, (int, float)) for x in c)
            and 0 <= c[0] < c[2] <= 1 and 0 <= c[1] < c[3] <= 1)


def _dentro(caixa, recorte):
    return recorte[0] <= caixa[0] and recorte[1] <= caixa[1] and caixa[2] <= recorte[2] and caixa[3] <= recorte[3]


def _comando_existe(linha):
    """O primeiro termo é um script de pipeline/ e, se o script tem subcomandos, o segundo é um deles."""
    partes = linha.split()
    if not partes or not (AQUI / partes[0]).is_file():
        return False
    subs = set(re.findall(r'add_parser\(\s*"([^"]+)"', ler(AQUI / partes[0])))
    return not subs or (len(partes) > 1 and partes[1] in subs)


def conferir_candidato(d, ids_v1, voc, fontes=None):
    """Erros do JSON de candidatos v2 (RUBRICA-v2.md, "O que a conferência do JSON cobra"). Lista vazia = passa."""
    E = []
    if any(t in json.dumps(d, ensure_ascii=False) for t in TRAVESSOES):
        E.append("travessão ou meia-risca em algum texto")
    falta = [k for k in OBRIG_TOPO if k not in d]
    if falta:
        return E + [f"faltam campos no topo: {falta}"]
    if d["camada"] not in voc["camada"]:
        E.append(f"camada {d['camada']!r} fora do vocabulário")
    if d["analista"] not in voc["analista"]:
        E.append(f"analista {d['analista']!r} fora do vocabulário")
    if set(d["lentes"]) - set(voc["dimensao"]):
        E.append(f"lentes fora do vocabulário: {sorted(set(d['lentes']) - set(voc['dimensao']))}")
    if fontes is not None:
        f = fontes.get(d["referencia"])
        if f is None:
            E.append(f"referência {d['referencia']!r} fora de repertorio/fontes.json")
        elif CAMADA_DA_FONTE.get(f.get("camada")) != d["camada"]:
            E.append(f"camada {d['camada']!r} diferente da de fontes.json ({f.get('camada')})")
    n = d["paginas_total"]
    todas = set(range(1, n + 1)) if isinstance(n, int) and n >= 1 else set()
    if not todas:
        E.append("paginas_total precisa ser inteiro >= 1")
    abertas = set(d["paginas_abertas"])
    if abertas - todas or set(d["mockups"]) - todas:
        E.append("página aberta ou mockup fora da captura")
    if d["camada"] in ("prioritaria", "profunda", "releitura") and abertas != todas:
        E.append(f"camada {d['camada']} abre todas as páginas; faltam {sorted(todas - abertas)}")
    if d["camada"] == "lente" and len(abertas) > 8:
        E.append("lente abre no máximo 8 páginas")
    s = d["serie"]
    if not all(k in s for k in ("constantes", "variaveis", "por_tipo", "ritmo")):
        E.append("serie precisa de constantes, variaveis, por_tipo e ritmo")
    else:
        if set(s["por_tipo"]) - set(voc["tipo_pagina"]):
            E.append(f"serie.por_tipo com tipo fora do vocabulário: {sorted(set(s['por_tipo']) - set(voc['tipo_pagina']))}")
        r = s["ritmo"]
        if r.get("padrao") not in voc["ritmo_padrao"]:
            E.append(f"ritmo.padrao {r.get('padrao')!r} fora do vocabulário")
        for k, v in (r.get("paginas") or {}).items():
            if not (k.isdigit() and int(k) in todas) or v not in voc["ritmo_papel"]:
                E.append(f"ritmo.paginas[{k}] = {v!r}: página fora da captura ou papel fora do vocabulário")
    up = d["uau_paginas"]
    if len(up) > math.ceil(len(todas) / 4):
        E.append(f"uau_paginas com {len(up)} páginas; o máximo é um quarto ({math.ceil(len(todas) / 4)})")
    for u in up:
        E += [f"uau_paginas p. {u.get('pagina')}: {x}" for x in _conferir_nota(u, voc)]
        if u.get("pagina") not in todas:
            E.append(f"uau_paginas: página {u.get('pagina')} fora da captura")
    if not d["padroes"] and d["camada"] != "lente":
        E.append("nenhum candidato (zero só vale na lente)")
    for p in d["padroes"]:
        E += [f"{p.get('id_sugerido')}: {x}" for x in _conferir_um(p, todas, ids_v1, voc)]
    return E


def _conferir_nota(u, voc):
    E = []
    nota, gat = u.get("nota"), u.get("gatilhos") or []
    if nota not in (0, 1, 2, 3):
        E.append(f"nota {nota!r} fora de 0 a 3")
    if set(gat) - set(voc["gatilho_uau"]):
        E.append(f"gatilho fora do vocabulário: {sorted(set(gat) - set(voc['gatilho_uau']))}")
    if nota in (1, 2) and not gat:
        E.append(f"nota {nota} sem gatilho")
    if nota == 3 and len(gat) < 2:
        E.append("nota 3 pede dois gatilhos que se reforçam")
    if u.get("depende_de") not in (None, "foto"):
        E.append(f"depende_de {u.get('depende_de')!r} (só 'foto')")
    return E


def _conferir_um(p, todas, ids_v1, voc):
    E = []
    falta = [k for k in OBRIG_V1 + OBRIG_V2 if k not in p]
    if falta:
        return [f"faltam campos: {falta}"]
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", str(p["id_sugerido"])):
        E.append("id_sugerido fora de a-z, 0-9 e hífen")
    for campo, v in LISTAS.items():
        if not isinstance(p[campo], list) or not p[campo] or set(p[campo]) - set(voc[v]):
            E.append(f"{campo} vazio ou fora do vocabulário: {p[campo]!r}")
    for campo, v in UNICOS.items():
        if p[campo] not in voc[v]:
            E.append(f"{campo} {p[campo]!r} fora do vocabulário")
    if p["familia"] not in p["dimensoes"]:
        E.append("a familia precisa estar em dimensoes")
    if p["intensidade"] not in (1, 2, 3):
        E.append(f"intensidade {p['intensidade']!r} fora de 1 a 3")
    eixos = {v.get("eixo") for v in p["variavel"]}
    if set(voc["eixo"]) - eixos:
        E.append(f"faltam eixos obrigatórios em variavel: {sorted(set(voc['eixo']) - eixos)}")
    if any(not isinstance(v.get("observado"), bool) or not v.get("faixa") for v in p["variavel"]):
        E.append("cada item de variavel precisa de faixa e observado (true ou false)")
    if not p["exemplos"]:
        E.append("sem exemplo")
    for ex in p["exemplos"]:
        onde = f"exemplo p. {ex.get('pagina')}"
        rc = ex.get("recorte")
        if not _caixa_ok(rc):
            E.append(f"{onde}: recorte inválido {rc!r}"); continue
        if ex.get("pagina") not in todas:
            E.append(f"{onde}: página fora da captura")
        if not isinstance(ex.get("mockup"), bool) or not ex.get("o_que_mostra") or not ex.get("imagem"):
            E.append(f"{onde}: precisa de imagem, o_que_mostra e mockup (true ou false)")
        if ex.get("intensidade") not in (None, 1, 2, 3):
            E.append(f"{onde}: intensidade fora de 1 a 3")
        an = ex.get("anotacoes") or []
        if not 1 <= len(an) <= 9:
            E.append(f"{onde}: de 1 a 9 anotações")
        ns = [a.get("n") for a in an]
        if len(set(ns)) != len(ns) or any(x not in range(1, 10) for x in ns):
            E.append(f"{onde}: números das anotações repetidos ou fora de 1 a 9")
        for a in an:
            c, seta = a.get("caixa"), a.get("seta")
            if not _caixa_ok(c) or not _dentro(c, rc):
                E.append(f"{onde}: anotação {a.get('n')} com caixa fora do recorte")
            if seta is not None and not (len(seta) == 4 and rc[0] <= min(seta[0], seta[2]) and max(seta[0], seta[2]) <= rc[2]
                                         and rc[1] <= min(seta[1], seta[3]) and max(seta[1], seta[3]) <= rc[3]):
                E.append(f"{onde}: anotação {a.get('n')} com seta fora do recorte")
            if not 3 <= len(a.get("rotulo") or "") <= 90:
                E.append(f"{onde}: anotação {a.get('n')} com rótulo de 3 a 90 caracteres")
    pr = p["producao"]
    if pr.get("via") not in voc["via"] or pr.get("risco_pdf") not in voc["risco_pdf"] or pr.get("reproduzivel") not in voc["reproduzivel"]:
        E.append(f"producao fora do vocabulário: {pr!r}")
    if pr.get("reproduzivel") in ("parcial", "so-com-insumo-do-cliente") and not pr.get("depende"):
        E.append("reproduzivel parcial ou so-com-insumo-do-cliente pede `depende`")
    if pr.get("via") == "fora-do-pipeline":
        if pr.get("reproduzivel") != "nao":
            E.append("via fora-do-pipeline pede reproduzivel nao")
    elif pr.get("via") in ROTA_DA_VIA and ROTA_DA_VIA[pr["via"]] != p["rota"]:
        E.append(f"rota {p['rota']!r} não corresponde à via {pr['via']!r} ({ROTA_DA_VIA[pr['via']]})")
    for c in pr.get("comandos") or []:
        if not _comando_existe(c):
            E.append(f"comando inexistente em pipeline/: {c!r}")
    u = p["uau"]
    E += [f"uau: {x}" for x in _conferir_nota(u, voc)]
    sinais = u.get("sinais") or {}
    if set(u.get("gatilhos") or []) - {k for k, v in sinais.items() if v}:
        E.append("uau.sinais sem medida para algum gatilho")
    fora = set(p["ja_coberto_por"]) - set(ids_v1)
    if fora:
        E.append(f"ja_coberto_por com id fora de padroes-v1.txt: {sorted(fora)}")
    if len(p["diferenca"] or "") < 8:
        E.append("diferenca vazia")
    return E


def ids_v1():
    return [linha.split(" · ", 1)[0] for linha in ler(PADROES_V1).splitlines()]


def fontes():
    return {f["id"]: f for f in carregar(FONTES)["fontes"]}


# =========================================================================================== provas
def como_v1(i):
    """O índice sem nada da versão 2 (recursos e os campos novos de padrão, recorte e referência), com versao 1."""
    v1 = copy.deepcopy(i)
    v1["versao"] = 1
    v1.pop("recursos", None)
    for p in v1["padroes"]:
        p.pop("dimensoes", None); p.pop("recursos", None)
        for r in p.get("recortes") or []:
            r.pop("anotado", None); r.pop("anotacoes", None)
    for r in v1["referencias"]:
        for k in ("serie", "captura", "camada_v2", "uau_paginas"):
            r.pop(k, None)
    return v1


def test_indice_atual_continua_valido_no_schema_v2():
    """O índice atual vale no schema e a projeção dele na versão 1 também (o índice v1 continua válido). Em 13/10/2026 o
    índice passou à versão 2 com o recurso de exemplo do CONEBRA (provisório, frente repertório)."""
    i = carregar(INDICE)
    assert i["versao"] in (1, 2) and ("recursos" not in i or i["versao"] == 2)
    v1 = como_v1(i)
    assert v1["versao"] == 1 and "recursos" not in v1
    import repertorio                                     # o consumidor real: carregar() usa validar_indice(sem_exemplos())
    for x in (i, v1):
        erros = erros_indice(x)
        assert erros == [], erros[:5]
        assert repertorio.validar_indice(repertorio.sem_exemplos(x)) == []
        assert repertorio.validar_indice(x) == []


def test_indice_v2_com_um_recurso_valida():
    i = indice_v2()
    erros = erros_indice(i)
    assert erros == [], erros[:5]
    import repertorio
    assert repertorio.validar_indice(i) == []


def test_trecho_do_briefing_valida_no_kit_na_composicao_e_no_acabamento():
    fm, trecho = front_do_briefing(), trecho_do_briefing()
    erros = conferir_trecho(fm, trecho)
    assert erros == [], erros
    import acabamento
    falhas, _ = acabamento.validar({"composicao": {"exemplo": trecho["pagina"]}}, so_composicao=True)
    assert falhas == [], falhas
    # o mesmo trecho com defeito plantado reprova: elemento de acabamento sem motivo, 3 acabamentos, id trocado
    sem_motivo = copy.deepcopy(trecho); del sem_motivo["pagina"]["elementos"][1]["motivo"]
    assert any("motivo" in e for e in conferir_trecho(fm, sem_motivo))
    tres = copy.deepcopy(trecho); tres["pagina"]["elementos"].append(dict(copy.deepcopy(tres["pagina"]["elementos"][1]), id="eco-2"))
    assert any("máximo 2" in e for e in conferir_trecho(fm, tres))
    outro = copy.deepcopy(trecho); outro["direcao_criativa"]["recursos"][0]["id"] = "outro-recurso"
    assert any("direcao_criativa.recursos" in e for e in conferir_trecho(fm, outro))
    forte = copy.deepcopy(trecho); forte["pagina"]["acabamento"]["intensidade"] = 1
    assert any("intensidade" in e for e in conferir_trecho(fm, forte))


def test_recursos_so_com_versao_2():
    i = indice_v2(); i["versao"] = 1
    assert any(c == ("versao",) for c, _ in erros_indice(i)), erros_indice(i)


CASOS_FORA = [  # (caminho do valor plantado, valor, caminho onde o erro tem de aparecer)
    (("versao",), 3, ("versao",)),
    (("recursos", 0, "familia"), "ornamento", None),
    (("recursos", 0, "recurso", 0), "enfeite", None),
    (("recursos", 0, "dimensoes", 0), "brilho", None),
    (("recursos", 0, "material", 0), "aco", None),
    (("recursos", 0, "luz"), "neon", None),
    (("recursos", 0, "luz_direcao"), "esquerda", None),
    (("recursos", 0, "profundidade"), "3d", None),
    (("recursos", 0, "intensidade", 1), 4, None),
    (("recursos", 0, "continuidade"), "sempre", None),
    (("recursos", 0, "borda", 0), "curva", None),
    (("recursos", 0, "tipo_pagina", 0), "folder", None),
    (("recursos", 0, "funcao", 0), "decoracao", None),
    (("recursos", 0, "tom", 0), "luxo", None),
    (("recursos", 0, "rota"), "codex", None),
    (("recursos", 0, "producao"), "blender", None),
    (("recursos", 0, "risco_pdf"), "baixo", None),
    (("recursos", 0, "reproduzivel"), "talvez", None),
    (("recursos", 0, "uau"), 4, None),
    (("recursos", 0, "tratamento_imagem", 0), "sepia", None),
    (("recursos", 0, "tipografia", 0), "negrito", None),
    (("recursos", 0, "mistura", 0), "video", None),
    (("recursos", 0, "uau_gatilhos", 0), "beleza", None),
    (("recursos", 0, "eixos", 0), "angulo", None),
    (("recursos", 0, "arquivo"), "padroes/x.md", None),
    (("recursos", 0, "cor_extra"), "x", ("recursos", 0)),
    (("recursos", 0, "acabamento_exemplo", "pagina", "acabamento", "luz"), "baixo", None),
    (("padroes", 0, "dimensoes", 0), "brilho", None),
    (("padroes", 0, "recursos", 0), "Id Com Espaco", None),
    (("padroes", 0, "recortes", 0, "anotado"), "recortes/x.jpg", None),
    (("padroes", 0, "recortes", 0, "anotacoes", 0, "caixa", 2), 1.4, None),
    (("referencias", 0, "camada_v2"), "media", None),
    (("referencias", 0, "captura", "status"), "parcial", None),
    (("referencias", 0, "serie", "ritmo", "padrao"), "aleatorio", None),
    (("referencias", 0, "serie", "ritmo", "paginas", "3"), "pausa", None),
    (("referencias", 0, "serie", "por_tipo"), {"folder": "frase do tipo"}, ("referencias", 0, "serie", "por_tipo")),
    (("referencias", 0, "uau_paginas", 0, "gatilhos", 0), "bonito", None),
    (("referencias", 0, "uau_paginas", 0, "nota"), 5, None),
    (("referencias", 0, "uau_paginas", 0, "depende_de"), "cliente", None),
]


def test_valor_fora_do_vocabulario_reprova_em_cada_campo_novo():
    assert erros_indice(indice_v2()) == []                # controle: sem o defeito, passa
    for caminho, valor, onde in CASOS_FORA:
        i = por(indice_v2(), caminho, valor)
        onde = onde or caminho
        erros = erros_indice(i)
        assert any(c[:len(onde)] == onde for c, _ in erros), (caminho, valor, erros[:3])


def test_vocabulario_da_rubrica_igual_ao_schema_e_ao_kit():
    voc, d = vocabulario(), defs()
    pp = d["padrao"]["properties"]
    esperado = {
        "funcao": pp["funcao"]["items"]["enum"], "relacao": pp["relacao"]["items"]["enum"],
        "tipo_pagina": pp["tipo_pagina"]["items"]["enum"], "rota": pp["rota"]["enum"], "tom": pp["tom"]["items"]["enum"],
        "densidade": pp["densidade"]["enum"],
        "intensidade": [str(x) for x in range(d["voc_intensidade"]["minimum"], d["voc_intensidade"]["maximum"] + 1)],
        "camada": [c for c in d["referencia"]["properties"]["camada_v2"]["enum"] if c not in ("regua", "fora")],
        "analista": ["A", "B", "unico"],
    }
    for nome in ("familia", "dimensao", "recurso", "material", "luz", "luz_direcao", "profundidade", "continuidade",
                 "tratamento_imagem", "tipografia", "borda", "ritmo_papel", "ritmo_padrao", "mistura", "via", "risco_pdf",
                 "reproduzivel", "eixo", "gatilho_uau"):
        esperado[nome] = d[f"voc_{nome}"]["enum"]
    assert sorted(voc) == sorted(esperado), (sorted(set(voc) ^ set(esperado)))
    for k, v in esperado.items():
        assert voc[k] == v, (k, voc[k], v)
    assert len(voc["eixo"]) == 9 and len(voc["familia"]) == 8 and len(voc["dimensao"]) == 11
    import acabamento                                     # as famílias são as mesmas do contrato do kit
    kit = carregar(SCHEMA_KIT)["properties"]["direcao_criativa"]["properties"]["recursos"]["items"]["properties"]["familia"]["enum"]
    assert voc["familia"] == list(acabamento.FAMILIAS) == kit


def test_padroes_v1_txt_tem_31_linhas_e_vem_do_indice():
    import gerar_padroes_v1
    linhas = ler(PADROES_V1).splitlines()
    assert len(linhas) == 31, len(linhas)
    assert all(len(l.split(" · ")) == 6 for l in linhas)
    assert ids_v1() == [p["id"] for p in carregar(INDICE)["padroes"]]
    assert ler(PADROES_V1) == gerar_padroes_v1.texto(carregar(INDICE))


def test_exemplo_da_rubrica_e_o_arquivo_e_passa_na_conferencia():
    d = carregar(EXEMPLO)
    assert json.loads(bloco(ler(RUBRICA), "json", depois_de="### Exemplo completo")) == d
    erros = conferir_candidato(d, ids_v1(), vocabulario(), fontes())
    assert erros == [], erros
    assert d["padroes"] and all(k in d["padroes"][0] for k in OBRIG_V1 + OBRIG_V2)
    s = d["serie"]
    assert all(k in s for k in ("constantes", "variaveis", "por_tipo", "ritmo"))
    assert d["padroes"][0]["exemplos"][0]["anotacoes"][0].keys() >= {"n", "caixa", "seta", "rotulo"}


def test_conferencia_do_candidato_reprova_cada_defeito_plantado():
    voc, ids, fs = vocabulario(), ids_v1(), fontes()
    base = carregar(EXEMPLO)
    assert conferir_candidato(base, ids, voc, fs) == []

    def com(f):
        d = copy.deepcopy(base); f(d); return conferir_candidato(d, ids, voc, fs)

    p = lambda d: d["padroes"][0]                                      # noqa: E731
    defeitos = {
        "eixos obrigatórios": lambda d: p(d).__setitem__("variavel", [v for v in p(d)["variavel"] if v["eixo"] != "intensidade"]),
        "fora do recorte": lambda d: p(d)["exemplos"][0]["anotacoes"][0].__setitem__("caixa", [0.1, 0.1, 0.3, 0.3]),
        "padroes-v1.txt": lambda d: p(d).__setitem__("ja_coberto_por", ["padrao-inexistente"]),
        "nota 3": lambda d: p(d)["uau"].update(nota=3, gatilhos=["cor"]),
        "travessão": lambda d: d.__setitem__("resumo", "deck \u2014 em blocos"),
        "dimensoes": lambda d: p(d).__setitem__("dimensoes", ["uau"]),
        "abre todas": lambda d: d.__setitem__("paginas_abertas", [1, 2, 3]),
        "comando inexistente": lambda d: p(d)["producao"]["comandos"].append("blender.py render cena.blend"),
        "um quarto": lambda d: d["uau_paginas"].extend([{"pagina": k, "nota": 0, "gatilhos": []} for k in (5, 6, 7)]),
        "depende": lambda d: p(d)["producao"].pop("depende"),
        "fora do vocabulário": lambda d: p(d).__setitem__("material", ["aco"]),
        "não corresponde à via": lambda d: p(d).__setitem__("rota", "codigo"),
        "sinais": lambda d: p(d)["uau"].__setitem__("sinais", {"cor": "medida"}),
        "fontes.json": lambda d: d.__setitem__("camada", "profunda"),
    }
    for trecho_msg, f in defeitos.items():
        erros = com(f)
        assert any(trecho_msg in e for e in erros), (trecho_msg, erros)


def test_documentos_trazem_as_secoes_exatas():
    r = ler(RUBRICA)
    secoes = ["Ficha", "O que faz funcionar", "Grid e margens", "Hierarquia", "Elementos e âncoras",
              "Linhas, formas, texturas e padrões", "Unidade × variação", "Código × imagem", "O que não copiar",
              "Continuidade e série", "Material, luz e profundidade", "Tratamento de imagem", "Tipografia expressiva",
              "Acabamentos", "Ritmo", "O que para o olho"]
    pos = [r.find(f"`## {s}`") for s in secoes]
    assert -1 not in pos and pos == sorted(pos), list(zip(secoes, pos))
    b = ler(BRIEFING)
    titulos = ["## 1. Efeito", "## 2. Como se organiza", "## 3. Relação com o conteúdo", "## 4. Condições",
               "## 5. O que pode variar", "## 6. Como adaptar", "## 7. Cuidados", "## 8. Como produzir e conferir",
               "## Trecho de acabamento", "## Referências"]
    pos = [b.find(f"`{t}`") for t in titulos]
    assert -1 not in pos and pos == sorted(pos), list(zip(titulos, pos))
    fm = front_do_briefing()
    obrig = set(defs()["recurso"]["required"]) - {"arquivo"}
    assert obrig <= set(fm), sorted(obrig - set(fm))


def test_nenhum_entregavel_tem_travessao():
    arquivos = [RUBRICA, BRIEFING, EXEMPLO, PADROES_V1, ESTUDO / "LEIA-ME.md", ESTUDO / "gerar_padroes_v1.py", SCHEMA,
                Path(__file__)]
    sujos = [p.name for p in arquivos if any(t in ler(p) for t in TRAVESSOES)]
    assert not sujos, sujos


if __name__ == "__main__":
    falhou = 0
    for nome, fn in list(globals().items()):
        if nome.startswith("test_"):
            try:
                fn(); print("ok  ", nome)
            except AssertionError as e:
                falhou += 1; print("FALHOU", nome, str(e)[:600])
    print("PROVAS:", "VERDES" if not falhou else f"{falhou} FALHA(S)")
    sys.exit(1 if falhou else 0)

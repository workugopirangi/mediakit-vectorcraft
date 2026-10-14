#!/usr/bin/env python3
"""
test_acabamento.py: provas do contrato da camada de acabamento (mk-2.1): schema e acabamento.validar. Sem pytest, segundos.

  ~/.venvs/mediakit/bin/python pipeline/test_acabamento.py

Base: o kit fictício exemplos/acabamento-prova (completo, sem falha nem aviso). Cada regra tem um mutante que a viola e um
inverso (o mesmo mutante sem o gatilho) que não gera nada. Kit antigo: o schema novo dá exatamente os mesmos erros que o
schema de antes (commit fixo 6cde3da) e nenhuma regra roda. Sai com 1 se algum teste falhar.
"""
import copy, json, subprocess, sys, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))
import acabamento, composicao, grafismos  # noqa: E402

KIT = RAIZ / "exemplos" / "acabamento-prova" / "mediakit.json"
ANTIGOS = [RAIZ / "exemplos" / "travessia-da-lua" / "mediakit.json", RAIZ / "exemplos" / "receitas-teste" / "mediakit.json"]
FIXTURE_SPRINT = RAIZ / "schema" / "fixtures" / "sprint-sistema-elementos.json"
# último commit que mexeu nos dois schemas ANTES do contrato do acabamento: estado fixo (lido do HEAD, a prova quebrava
# no dia do commit, como o test_camadas já aprendeu)
COMMIT_ANTES_DO_ACABAMENTO = "6cde3da"


def teste(fn):
    fn._teste = True
    return fn


def log(*a):
    print("   ", *a, flush=True)


def base():
    return json.loads(KIT.read_text(encoding="utf-8"))


def el_comp(k, pagina, eid):
    return next(e for e in k["composicao"][pagina]["elementos"] if e["id"] == eid)


def el_kit(k, eid):
    return next(e for e in k["elementos"] if e["id"] == eid)


def schema_do_git(nome):
    """O schema como estava antes do contrato do acabamento (commit fixo)."""
    r = subprocess.run(["git", "show", f"{COMMIT_ANTES_DO_ACABAMENTO}:./schema/{nome}"], capture_output=True, text=True, cwd=str(RAIZ))
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


# ------------------------------------------------------------------------------------------------- vocabulário
@teste
def vocabularios_do_codigo_sao_os_do_schema():
    kit = json.loads(acabamento.SCHEMA_KIT.read_text(encoding="utf-8"))
    el = json.loads(acabamento.SCHEMA_ELEMENTOS.read_text(encoding="utf-8"))["definitions"]
    p = kit["properties"]
    dc = p["direcao_criativa"]["properties"]
    rec = dc["recursos"]["items"]["properties"]
    assert set(p["schema_version"]["enum"]) == {"mk-2.0", "mk-2.1"}
    assert tuple(rec["familia"]["enum"]) == acabamento.FAMILIAS and tuple(dc["nao_usa"]["items"]["enum"]) == acabamento.FAMILIAS
    assert tuple(rec["rota"]["enum"]) == acabamento.ROTAS
    assert tuple(dc["fio_condutor"]["properties"]["papeis"]["additionalProperties"]["enum"]) == acabamento.PAPEIS_FIO
    for c in ("padrao", "teto"):
        i = dc["intensidade"]["properties"][c]
        assert (i["minimum"], i["maximum"]) == (min(acabamento.INTENSIDADE), max(acabamento.INTENSIDADE))
    assert tuple(el["elemento"]["properties"]["material"]["enum"]) == acabamento.MATERIAIS
    assert "acabamento" in el["elemento"]["properties"]["papel"]["enum"]
    ce = el["composicao_elemento"]["properties"]
    assert "acabamento" in ce["papel"]["enum"]
    ef = ce["efeito"]["properties"]
    for campo in ("opacidade", "blend", "mascara", "sombra", "reflexo"):
        assert tuple(ef[campo]["enum"]) == acabamento.EFEITO[campo], campo
    for campo in ("alvo", "corte"):
        assert tuple(ef["cruza"]["properties"][campo]["enum"]) == acabamento.EFEITO["cruza"][campo], campo
    es = ef["esmaecer"]["properties"]
    assert tuple(es["direcao"]["enum"]) == acabamento.EFEITO["esmaecer"]["direcao"]
    assert (es["passos"]["minimum"], es["passos"]["maximum"]) == acabamento.EFEITO["esmaecer"]["passos"]
    assert (es["minimo"]["minimum"], es["minimo"]["maximum"]) == acabamento.EFEITO["esmaecer"]["minimo"]
    pa = el["composicao_pagina"]["properties"]["acabamento"]["properties"]
    for campo in ("profundidade", "grao", "luz"):
        assert tuple(pa[campo]["enum"]) == acabamento.PAGINA[campo], campo
    rels = [b["properties"]["relacao"]["const"] for b in el["composicao_ancora"]["oneOf"]]
    assert rels == list(composicao.RELACOES) + [acabamento.RELACAO_NOVA], rels
    # os 16 tipos novos de grafismo entram no enum JUNTO com o gerador (a frente dos geradores): nunca um sem o outro
    tipos = set(el["elemento"]["properties"]["tipo"]["enum"])
    constantes = set(el["sistema_elementos"]["properties"]["constantes"]["items"]["properties"]["tipo"]["enum"])
    soltos = [t for t in acabamento.TIPOS_A_ENTRAR if (t in tipos) != (t in grafismos.TIPOS)]
    soltos += [t for t in acabamento.CONSTANTES_A_ENTRAR if t in constantes and t not in grafismos.TIPOS]
    assert not soltos, f"tipo no enum sem gerador (ou gerador sem enum): {soltos}"
    a_entrar = [t for t in acabamento.TIPOS_A_ENTRAR if t not in grafismos.TIPOS]
    log(f"8 famílias, 7 papéis do fio, 10 materiais, efeitos e página iguais ao schema; relações {rels}; "
        f"{len(a_entrar)} grafismos ainda a entrar com o gerador")


# ------------------------------------------------------------------------------------------------- schema
# caminhos que o kit de prova tem de cobrir para valer como "kit mk-2.1 completo com todos os campos"
COBERTURA = [
    "schema_version=mk-2.1", "direcao_criativa.consulta", "direcao_criativa.recursos.id", "direcao_criativa.recursos.familia",
    "direcao_criativa.recursos.referencia", "direcao_criativa.recursos.principio", "direcao_criativa.recursos.rota",
    "direcao_criativa.recursos.motivo", "direcao_criativa.recursos.nao_copiar", "direcao_criativa.nao_usa",
    "direcao_criativa.intensidade.padrao", "direcao_criativa.intensidade.teto", "direcao_criativa.fio_condutor.motivo",
    "direcao_criativa.fio_condutor.papeis", "direcao_criativa.repete_entre_paginas", "formato_base.id", "formato_base.versao",
    "formato_base.sha256", "receitas.fontes.lettering", "elementos.material", "elementos.papel=acabamento",
    "composicao.acabamento.recursos", "composicao.acabamento.intensidade", "composicao.acabamento.profundidade",
    "composicao.acabamento.grao", "composicao.acabamento.luz", "composicao.acabamento.porque", "composicao.elementos.papel=acabamento",
    "composicao.elementos.recurso", "composicao.elementos.motivo", "composicao.elementos.efeito.opacidade",
    "composicao.elementos.efeito.blend", "composicao.elementos.efeito.mascara", "composicao.elementos.efeito.sombra",
    "composicao.elementos.efeito.reflexo", "composicao.elementos.efeito.cruza", "composicao.elementos.efeito.esmaecer",
    "composicao.elementos.ancora.relacao=registro"]


def _caminhos(x, pre=""):
    """Todos os caminhos de chave do kit (listas e chaves de página achatadas), mais caminho=valor para texto."""
    out = set()
    if isinstance(x, dict):
        for k, v in x.items():
            c = f"{pre}.{k}" if pre else k
            out.add(c)
            if isinstance(v, str):
                out.add(f"{c}={v}")
            out |= _caminhos(v, c)
    elif isinstance(x, list):
        for v in x:
            out |= _caminhos(v, pre)
    return out


@teste
def schema_aceita_kit_mk21_completo():
    k = base()
    achatado = _caminhos(dict(k, composicao={"p": {"x": list(k["composicao"].values())}}))
    achatado = {c.replace("composicao.p.x.", "composicao.") for c in achatado}
    falta = [c for c in COBERTURA if c not in achatado]
    assert not falta, f"o kit de prova não cobre: {falta}"
    es = acabamento.erros_schema(k)
    assert es == [], es
    log(f"kit de prova cobre os {len(COBERTURA)} campos novos e valida nos dois schemas")


def _set(caminho, valor):
    """Mutação que põe `valor` em `caminho` (lista de chaves e índices; chave 'pg:<rotulo>:<id>' = elemento da composição)."""
    def mut(k):
        alvo = k
        for c in caminho[:-1]:
            if isinstance(c, str) and c.startswith("pg:"):
                _, pg, eid = c.split(":")
                alvo = el_comp(k, pg, eid)
            elif isinstance(c, str) and c.startswith("el:"):
                alvo = el_kit(k, c[3:])
            else:
                alvo = alvo[c]
        alvo[caminho[-1]] = valor
    return mut


# (descrição, mutação, trecho do caminho que o erro tem de citar)
FORA_DO_ENUM = [
    ("schema_version mk-2.2", _set(["schema_version"], "mk-2.2"), "mediakit/schema_version"),
    ("direcao_criativa chave nova", _set(["direcao_criativa", "estilo"], "x"), "mediakit/direcao_criativa"),
    ("consulta não é texto", _set(["direcao_criativa", "consulta"], 3), "mediakit/direcao_criativa/consulta"),
    # "recursos vazio" deixou de ser recusado em 13/10/2026: o formato herdado exporta a lista vazia e o QA do kit
    # mk-2.1 é quem cobra pelo menos 4 famílias (frente Q).
    ("recursos com 10", lambda k: k["direcao_criativa"].__setitem__("recursos", k["direcao_criativa"]["recursos"] + k["direcao_criativa"]["recursos"][:3]), "mediakit/direcao_criativa/recursos"),
    ("recurso id com maiúscula", _set(["direcao_criativa", "recursos", 0, "id"], "Eco"), "mediakit/direcao_criativa/recursos/0/id"),
    ("recurso família fora", _set(["direcao_criativa", "recursos", 0, "familia"], "ornamento"), "mediakit/direcao_criativa/recursos/0/familia"),
    ("recurso princípio curto", _set(["direcao_criativa", "recursos", 0, "principio"], "curto"), "mediakit/direcao_criativa/recursos/0/principio"),
    ("recurso rota fora", _set(["direcao_criativa", "recursos", 0, "rota"], "ia"), "mediakit/direcao_criativa/recursos/0/rota"),
    ("recurso sem referência", lambda k: k["direcao_criativa"]["recursos"][0].pop("referencia"), "mediakit/direcao_criativa/recursos/0"),
    ("recurso motivo não é texto", _set(["direcao_criativa", "recursos", 0, "motivo"], 1), "mediakit/direcao_criativa/recursos/0/motivo"),
    ("recurso nao_copiar não é texto", _set(["direcao_criativa", "recursos", 0, "nao_copiar"], []), "mediakit/direcao_criativa/recursos/0/nao_copiar"),
    ("nao_usa família fora", _set(["direcao_criativa", "nao_usa"], ["ornamentos"]), "mediakit/direcao_criativa/nao_usa/0"),
    ("intensidade padrão 4", _set(["direcao_criativa", "intensidade", "padrao"], 4), "mediakit/direcao_criativa/intensidade/padrao"),
    ("intensidade teto -1", _set(["direcao_criativa", "intensidade", "teto"], -1), "mediakit/direcao_criativa/intensidade/teto"),
    ("fio papel fora", _set(["direcao_criativa", "fio_condutor", "papeis", "capa"], "faixa"), "mediakit/direcao_criativa/fio_condutor/papeis/capa"),
    ("repete_entre_paginas com número", _set(["direcao_criativa", "repete_entre_paginas"], [1]), "mediakit/direcao_criativa/repete_entre_paginas/0"),
    ("formato_base id com maiúscula", _set(["formato_base", "id"], "Kit"), "mediakit/formato_base/id"),
    ("formato_base versão 0", _set(["formato_base", "versao"], 0), "mediakit/formato_base/versao"),
    ("formato_base sha256 curto", _set(["formato_base", "sha256"], "abc"), "mediakit/formato_base/sha256"),
    ("receita lettering número", _set(["receitas", 0, "fontes", "lettering"], 12), "mediakit/receitas/0/fontes/lettering"),
    ("elemento material fora", _set(["el:medalha", "material"], "aco"), "elementos/0/material"),
    ("elemento papel fora", _set(["el:textura-grao", "papel"], "acabamentos"), "elementos/4/papel"),
    ("página acabamento chave nova", _set(["composicao", "capa", "acabamento", "cor"], "x"), "composicao/capa/acabamento"),
    ("página recursos id inválido", _set(["composicao", "capa", "acabamento", "recursos"], ["Eco"]), "composicao/capa/acabamento/recursos/0"),
    ("página intensidade 4", _set(["composicao", "capa", "acabamento", "intensidade"], 4), "composicao/capa/acabamento/intensidade"),
    ("página profundidade fora", _set(["composicao", "capa", "acabamento", "profundidade"], "funda"), "composicao/capa/acabamento/profundidade"),
    ("página grão fora", _set(["composicao", "capa", "acabamento", "grao"], "muito"), "composicao/capa/acabamento/grao"),
    ("página luz fora", _set(["composicao", "capa", "acabamento", "luz"], "baixo"), "composicao/capa/acabamento/luz"),
    ("página porquê curto", _set(["composicao", "capa", "acabamento", "porque"], "curto"), "composicao/capa/acabamento/porque"),
    ("composição papel fora", _set(["pg:capa:eco-titulo", "papel"], "acabamentos"), "composicao/capa/elementos/0/papel"),
    ("composição recurso inválido", _set(["pg:capa:eco-titulo", "recurso"], "Eco"), "composicao/capa/elementos/0/recurso"),
    ("composição motivo inválido", _set(["pg:capa:eco-titulo", "motivo"], "Lua"), "composicao/capa/elementos/0/motivo"),
    ("efeito chave nova", _set(["pg:capa:eco-titulo", "efeito", "brilho"], 1), "composicao/capa/elementos/0/efeito"),
    ("efeito opacidade fora do degrau", _set(["pg:capa:eco-titulo", "efeito", "opacidade"], 0.5), "composicao/capa/elementos/0/efeito/opacidade"),
    ("efeito blend fora", _set(["pg:capa:eco-titulo", "efeito", "blend"], "overlay"), "composicao/capa/elementos/0/efeito/blend"),
    ("efeito máscara fora", _set(["pg:ativo:recorte-cena", "efeito", "mascara"], "estrela"), "composicao/ativo/elementos/0/efeito/mascara"),
    ("efeito sombra fora", _set(["pg:cota:selo-objeto", "efeito", "sombra"], "dura"), "composicao/cota/elementos/0/efeito/sombra"),
    ("efeito reflexo fora", _set(["pg:cota:selo-objeto", "efeito", "reflexo"], "agua"), "composicao/cota/elementos/0/efeito/reflexo"),
    ("cruza alvo fora", _set(["pg:capa:medalha", "efeito", "cruza", "alvo"], "preco"), "composicao/capa/elementos/1/efeito/cruza/alvo"),
    ("cruza corte fora", _set(["pg:capa:medalha", "efeito", "cruza", "corte"], "base"), "composicao/capa/elementos/1/efeito/cruza/corte"),
    ("cruza sem corte", lambda k: el_comp(k, "capa", "medalha")["efeito"]["cruza"].pop("corte"), "composicao/capa/elementos/1/efeito/cruza"),
    ("esmaecer direção fora", _set(["pg:divisor:malha-fundo", "efeito", "esmaecer", "direcao"], "diagonal"), "composicao/divisor/elementos/0/efeito/esmaecer/direcao"),
    ("esmaecer passos 2", _set(["pg:divisor:malha-fundo", "efeito", "esmaecer", "passos"], 2), "composicao/divisor/elementos/0/efeito/esmaecer/passos"),
    ("esmaecer passos 9", _set(["pg:divisor:malha-fundo", "efeito", "esmaecer", "passos"], 9), "composicao/divisor/elementos/0/efeito/esmaecer/passos"),
    ("esmaecer mínimo 0.5", _set(["pg:divisor:malha-fundo", "efeito", "esmaecer", "minimo"], 0.5), "composicao/divisor/elementos/0/efeito/esmaecer/minimo"),
    ("registro alvo título", _set(["pg:publico:figura-publico", "ancora", "alvo"], "titulo"), "composicao/publico/elementos/0/ancora"),
    ("registro com eixo", _set(["pg:publico:figura-publico", "ancora", "x"], "esq=foto.esq"), "composicao/publico/elementos/0/ancora"),
]


@teste
def schema_recusa_fora_do_vocabulario_em_cada_campo_novo():
    assert acabamento.erros_schema(base()) == []
    for desc, mut, trecho in FORA_DO_ENUM:
        k = base()
        mut(k)
        es = acabamento.erros_schema(k)
        assert es, f"{desc}: o schema aceitou"
        assert any(e.startswith(trecho) for e in es), f"{desc}: erro em outro lugar: {es[:3]}"
    log(f"{len(FORA_DO_ENUM)} mutantes, um por campo novo: todos recusados no caminho certo")


@teste
def schema_kit_antigo_igual_ao_de_antes():
    """Mudança aditiva: o schema novo dá os MESMOS erros que o schema de antes nos kits antigos (os exemplos e a fixture da
    Sprint com sistema_elementos e elementos[]); os dois exemplos mk-2.0 validam a raiz sem erro."""
    velho_kit, velho_el = schema_do_git("mediakit.schema.json"), schema_do_git("elementos.schema.json")
    assert "direcao_criativa" not in velho_kit["properties"], f"{COMMIT_ANTES_DO_ACABAMENTO} já tem o contrato novo"
    sprint = json.loads(FIXTURE_SPRINT.read_text(encoding="utf-8"))
    kits = [(p.parent.name, json.loads(p.read_text(encoding="utf-8"))) for p in ANTIGOS]
    kits.append(("fixture-sprint", dict(json.loads(ANTIGOS[0].read_text(encoding="utf-8")), sistema_elementos=sprint["sistema_elementos"],
                                        elementos=sprint["elementos"])))
    for nome, k in kits:
        assert k["schema_version"] == "mk-2.0"
        novo, velho = acabamento.erros_schema(k), acabamento.erros_schema(k, velho_kit, velho_el)
        assert novo == velho, f"{nome}: o schema novo mudou o veredito de um kit antigo: {set(novo) ^ set(velho)}"
        raiz = [e for e in novo if e.startswith("mediakit")]
        if nome != "fixture-sprint":
            assert raiz == [], f"{nome}: {raiz}"
        log(f"{nome}: {len(novo)} erro(s) com o schema novo, os mesmos com o de {COMMIT_ANTES_DO_ACABAMENTO}; raiz {'válida' if not raiz else raiz}")


# ------------------------------------------------------------------------------------------------- regras
@teste
def kit_antigo_nao_passa_por_regra_nenhuma():
    """A guarda vem antes de qualquer regra: com uma regra que sempre falha no lugar das reais, kit antigo continua limpo."""
    sprint = json.loads(FIXTURE_SPRINT.read_text(encoding="utf-8"))
    kits = [json.loads(p.read_text(encoding="utf-8")) for p in ANTIGOS]
    kits.append(dict(kits[0], sistema_elementos=sprint["sistema_elementos"], elementos=sprint["elementos"],
                     composicao={"ativo": {"mensagem": "m", "elementos": [{"id": "pena-dourada", "papel": "heroi", "funcao": "foco",
                                                                            "camada": "atras", "ancora": {"relacao": "alinha", "x": "esq=titulo.esq", "y": "topo=titulo.cap"},
                                                                            "escala": {"altura": "1/3p"}}]}}))
    sempre = lambda c: c.falhas.append("regra que sempre falha")  # noqa: E731
    reais = acabamento.REGRAS
    try:
        acabamento.REGRAS = (sempre,)
        for k in kits:
            assert not acabamento.usa_acabamento(k)
            assert acabamento.validar(k) == ([], []), acabamento.validar(k)
            assert acabamento.validar(k, so_composicao=True) == ([], [])
        assert acabamento.validar(base())[0] == ["regra que sempre falha"]     # e no kit novo a regra roda
    finally:
        acabamento.REGRAS = reais
    log(f"{len(kits)} kits sem campo novo: nenhuma regra rodou (nem a que sempre falha); no kit mk-2.1 ela roda")


@teste
def kit_de_prova_limpo():
    assert acabamento.validar(base()) == ([], [])
    assert acabamento.validar(base(), so_composicao=True) == ([], [])


def _sem_efeito(pg, eid, *campos):
    def mut(k):
        e = el_comp(k, pg, eid)
        for c in campos:
            (e.get("efeito") or {}).pop(c, None)
        if "efeito" in e and not e["efeito"]:
            e.pop("efeito")
    return mut


def _seq(*muts):
    def mut(k):
        for m in muts:
            m(k)
    return mut


def _extras_na_capa(papel):
    def mut(k):
        eco = el_comp(k, "capa", "eco-titulo")
        for n in (2, 3):
            k["composicao"]["capa"]["elementos"].append(dict(copy.deepcopy(eco), id=f"eco-{n}", papel=papel))
    return mut


def _familias(k, fams):
    for r, f in zip(k["direcao_criativa"]["recursos"], fams):
        r["familia"] = f


# (regra, descrição, mutante, inverso, nível, trecho)
MUTANTES = [
    ("regra_maximo_por_pagina", "3 acabamentos na capa", _extras_na_capa("acabamento"), _extras_na_capa("estrutura"),
     "falha", "3 elementos de papel acabamento"),
    ("regra_acabamento_funcao", "acabamento com função foco", _set(["pg:capa:eco-titulo", "funcao"], "foco"),
     _seq(_set(["pg:capa:eco-titulo", "funcao"], "foco"), _set(["pg:capa:eco-titulo", "papel"], "estrutura")), "falha", "pede função"),
    ("regra_acabamento_motivo", "acabamento sem motivo", lambda k: el_comp(k, "capa", "eco-titulo").pop("motivo"),
     _seq(lambda k: el_comp(k, "capa", "eco-titulo").pop("motivo"), _set(["pg:capa:eco-titulo", "papel"], "estrutura")), "falha", "exige `motivo`"),
    ("regra_acabamento_motivo", "acabamento com motivo inexistente", _set(["pg:divisor:malha-fundo", "motivo"], "sol"),
     _seq(_set(["pg:divisor:malha-fundo", "motivo"], "sol"), _set(["pg:divisor:malha-fundo", "papel"], "estrutura")), "falha", "`sol` não existe"),
    ("regra_acabamento_motivo", "elementos[] acabamento com motivo inexistente", _set(["el:textura-grao", "motivo"], "sol"),
     _seq(_set(["el:textura-grao", "motivo"], "sol"), _set(["el:textura-grao", "papel"], "apoio")), "falha", "`sol` não existe"),
    ("regra_cruza_na_frente", "cruza na camada atrás", _set(["pg:capa:medalha", "camada"], "atras"),
     _seq(_set(["pg:capa:medalha", "camada"], "atras"), _sem_efeito("capa", "medalha", "cruza")), "falha", "cruza só na camada frente"),
    ("regra_sombra_reflexo_png", "sombra contato em grafismo", _set(["pg:capa:eco-titulo", "efeito", "sombra"], "contato"),
     _seq(_set(["pg:capa:eco-titulo", "efeito", "sombra"], "contato"), _sem_efeito("capa", "eco-titulo", "sombra")), "falha", "sombra contato só em"),
    ("regra_sombra_reflexo_png", "reflexo piso em PNG de código", _set(["pg:ativo:recorte-cena", "efeito", "reflexo"], "piso"),
     _seq(_set(["pg:ativo:recorte-cena", "efeito", "reflexo"], "piso"), _set(["el:recorte-cena", "rota"], "biblioteca")), "falha", "reflexo piso só em"),
    ("regra_deslocada_svg", "sombra deslocada em PNG", _set(["pg:capa:medalha", "efeito", "sombra"], "deslocada"),
     _set(["pg:capa:eco-titulo", "efeito", "sombra"], "deslocada"), "falha", "sombra deslocada só em grafismo SVG"),
    ("regra_familia_proibida", "família usada está em nao_usa", lambda k: k["direcao_criativa"]["nao_usa"].append("pattern-textura"),
     lambda k: k["direcao_criativa"]["nao_usa"].append("acabamento-borda"), "falha", "que direcao_criativa.nao_usa proíbe"),
    ("regra_recurso_fora", "página cita recurso fora da direção", lambda k: k["composicao"]["capa"]["acabamento"]["recursos"].append("brilho-x"),
     _seq(lambda k: k["composicao"]["capa"]["acabamento"]["recursos"].append("brilho-x"),
          lambda k: k["direcao_criativa"]["recursos"].append({"id": "brilho-x", "familia": "tipografia-expressiva", "referencia": "ficticio:x",
                                                              "principio": "um brilho fictício", "rota": "codigo"})), "aviso", "`brilho-x` fora"),
    ("regra_fio_condutor", "fio condutor em 2 páginas", lambda k: k["direcao_criativa"]["fio_condutor"]["papeis"].pop("prova"),
     lambda k: k["direcao_criativa"]["fio_condutor"]["papeis"].update(cota="selo"), "falha", "2 página(s)"),
    ("regra_teto_padrao", "teto abaixo do padrão", _set(["direcao_criativa", "intensidade", "padrao"], 3),
     _set(["direcao_criativa", "intensidade", "padrao"], 2), "falha", "teto 2 abaixo do padrão 3"),
    ("regra_intensidade_teto", "página acima do teto", _set(["composicao", "capa", "acabamento", "intensidade"], 3),
     _seq(_set(["composicao", "capa", "acabamento", "intensidade"], 3), _set(["direcao_criativa", "intensidade", "teto"], 3)), "aviso", "acima do teto 2"),
    ("regra_familias_minimas", "3 famílias", lambda k: _familias(k, ["tipografia-expressiva", "sobreposicao-recorte", "profundidade-3d", "profundidade-3d",
                                                                      "profundidade-3d", "profundidade-3d", "sobreposicao-recorte"]),
     lambda k: _familias(k, ["tipografia-expressiva", "sobreposicao-recorte", "profundidade-3d", "profundidade-3d",
                             "tratamento-imagem", "profundidade-3d", "sobreposicao-recorte"]), "aviso", "3 família(s)"),
]


def conferir_mutante(regra, desc, mutar, inverso, nivel, trecho):
    """Erro (texto) ou None. O mutante gera SÓ mensagens do nível certo, todas com o trecho; o inverso não gera nada."""
    k = base(); mutar(k)
    falhas, avisos = acabamento.validar(k)
    alvo, outro = (falhas, avisos) if nivel == "falha" else (avisos, falhas)
    if not alvo or outro or not all(trecho in m for m in alvo):
        return f"{regra} ({desc}): esperado {nivel} com `{trecho}`; veio falhas={falhas} avisos={avisos}"
    k = base(); inverso(k)
    if acabamento.validar(k) != ([], []):
        return f"{regra} ({desc}): o inverso gerou {acabamento.validar(k)}"
    if acabamento.erros_schema(k):
        return f"{regra} ({desc}): o inverso não valida no schema: {acabamento.erros_schema(k)[:2]}"
    return None


@teste
def cada_regra_tem_mutante_e_inverso():
    nomes = {r.__name__ for r in acabamento.REGRAS}
    cobertas = {m[0] for m in MUTANTES}
    assert nomes == cobertas, f"regra sem mutante: {nomes - cobertas}; mutante sem regra: {cobertas - nomes}"
    erros = [x for x in (conferir_mutante(*m) for m in MUTANTES) if x]
    assert not erros, "\n".join(erros)
    log(f"{len(MUTANTES)} mutantes para as {len(nomes)} regras: cada um acusa no nível certo; cada inverso fica limpo")


@teste
def canal_da_composicao_sem_e_com_o_kit():
    """composicao.validar: sem o kit (como o camadas.py chama hoje) roda só o que a composição decide; com o kit, tudo.
    Kit de prova limpo nos dois; kit antigo igual."""
    k = base()
    ids = [e["id"] for e in k["elementos"]]
    assert composicao.validar(k["composicao"], ids) == [] and composicao.validar(k["composicao"], ids, kit=k) == []
    # regra da composição: aparece sem o kit
    k3 = base(); _extras_na_capa("acabamento")(k3)
    e = composicao.validar(k3["composicao"], ids)
    assert any("3 elementos de papel acabamento" in x for x in e), e
    k4 = base(); _set(["pg:capa:eco-titulo", "efeito", "sombra"], "contato")(k4)
    assert any("sombra contato só em" in x for x in composicao.validar(k4["composicao"], ids))
    # regra do kit: só com o kit
    kn = base(); kn["direcao_criativa"]["nao_usa"].append("pattern-textura")
    assert composicao.validar(kn["composicao"], ids) == []
    assert any("nao_usa proíbe" in x for x in composicao.validar(kn["composicao"], ids, kit=kn))
    # sem o kit, motivo em elementos[] não é acusado (quem decide é quem tem o kit); grafismo da página sem motivo é
    km = base(); el_comp(km, "capa", "eco-titulo").pop("motivo")
    assert any("exige `motivo`" in x for x in composicao.validar(km["composicao"], ids))
    km2 = base(); el_comp(km2, "cota", "selo-objeto")["papel"] = "acabamento"; el_comp(km2, "cota", "selo-objeto")["funcao"] = "acabamento"
    assert composicao.validar(km2["composicao"], ids) == [] and composicao.validar(km2["composicao"], ids, kit=km2) == []
    # kit sem composição mas com a direção: as regras do kit rodam com o kit e somem sem ele
    kd = base(); kd.pop("composicao"); kd["direcao_criativa"]["intensidade"]["padrao"] = 3
    assert composicao.validar(None, ids) == [] and any("teto 2 abaixo" in x for x in composicao.validar(None, ids, kit=kd))
    # registro passa na composição (sem eixo nem escala) e não serve de âncora de constante
    assert composicao.validar({"publico": k["composicao"]["publico"]}, ids) == []
    assert composicao.validar_constantes({"constantes": [{"tipo": "selo", "ancora": {"relacao": "registro", "alvo": "foto"}}]})
    log("sem o kit: máximo por página, sombra em grafismo e motivo de grafismo; com o kit: nao_usa, teto e motivo de elementos[]")


# ================================================================================================= execução
def main():
    nomes = [a for a in sys.argv[1:] if not a.startswith("--")]
    testes = [(n, f) for n, f in globals().items() if callable(f) and getattr(f, "_teste", False)]
    if nomes:
        testes = [(n, f) for n, f in testes if n in nomes]
    falhou = 0
    for n, f in testes:
        t0 = time.time()
        try:
            f()
            print(f"OK      {n}  ({time.time() - t0:.1f} s)", flush=True)
        except Exception as e:
            falhou += 1
            print(f"FALHOU  {n}  ({time.time() - t0:.1f} s): {type(e).__name__}: {str(e)[:1500]}", flush=True)
    print(f"\n{len(testes) - falhou} de {len(testes)} testes passaram")
    sys.exit(1 if falhou else 0)


if __name__ == "__main__":
    main()

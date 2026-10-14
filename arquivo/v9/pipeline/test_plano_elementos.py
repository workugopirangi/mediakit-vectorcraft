#!/usr/bin/env python3
"""Provas do plano_elementos.py e das regras de conjunto do qa_conjunto.py. Rodar: ~/.venvs/mediakit/bin/python
test_plano_elementos.py. Usa um catálogo de encaixes de teste (o pipeline/encaixes.json é da Frente A), a fixture da
Sprint e elementos sintéticos (traço dourado desenhado aqui, numa pasta temporária): não gasta cota nem toca em kit."""
import json, os, subprocess, sys, tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import plano_elementos as pe  # noqa: E402
import qa_conjunto  # noqa: E402

FIXTURE = AQUI.parent / "schema" / "fixtures" / "sprint-sistema-elementos.json"


# ---------------------------------------------------------------- catálogo e páginas de teste
def catalogo():
    def H(i, mx, cam=("frente",)):
        return {"id": i, "gerador": "maior-vazio", "max": list(mx), "papeis": ["heroi", "apoio"], "camadas": list(cam)}
    C = [{"id": "borda-base", "gerador": "faixa", "lado": "base", "esp": 40, "papeis": ["constante"], "camadas": ["frente"]},
         {"id": "selo-canto", "gerador": "canto", "canto": "inf-esq", "max": [180, 180], "papeis": ["constante"], "camadas": ["frente"]}]
    PAT = {"id": "fundo-inteiro", "gerador": "fixo", "box": [0, 0, 1920, 1080], "papeis": ["pattern"], "camadas": ["sob-veu", "atras"]}
    q, l, a = (520, 520), (760, 400), (360, 760)
    return {
        "capa:a": [H("canto-sup-dir", q), H("lateral-alta", a)] + C, "capa:c": [H("canto-sup-dir", q)] + C,
        "manifesto:a": [H("maior-vazio", l)] + C, "manifesto:b": [H("maior-vazio", l)] + C,
        "projecao": list(C), "prova": [H("canto-sup-dir", q)] + C, "historico_logos": [PAT] + C,   # prova com encaixe: a regra é que barra
        "publico:a": [H("canto-sup-dir", q)] + C, "territorio": [H("lateral-alta", a), PAT] + C,
        "divisor:a": [H("maior-vazio", l), PAT] + C, "divisor:b": [H("maior-vazio", l), PAT] + C,
        "ativo:painel": [H("canto-sup-dir", q)] + C, "ativo:topo": [H("maior-vazio", l)] + C,
        "ativo:diagonal": [H("lateral-alta", a)] + C, "ativo:sangria": [H("canto-sup-dir", q)] + C,
        "divisor_cotas": [PAT] + C, "cota:a": [H("lateral-alta", a)] + C, "cota:b": [H("lateral-alta", a)] + C,
        "contato:a": [H("canto-sup-dir", q)] + C, "contato:b": [H("canto-sup-dir", q)] + C,
    }


def paginas(seq):
    return [{"n": i + 1, "tipo": t, "rotulo": pe.rotulo(t, v)} for i, (t, v) in enumerate(seq)]


def com_composicao(pags, herois_por_n=None, so_marca=()):
    """Marca páginas como compostas (contrato da composição, references/08): `composicao: true` e, quando a composição da
    página põe herói, os ids em `herois_composicao`. `so_marca` = páginas compostas sem herói informado."""
    out = []
    for p in pags:
        q = dict(p)
        if p["n"] in so_marca:
            q["composicao"] = True
        if herois_por_n and p["n"] in herois_por_n:
            q["composicao"] = True
            q["herois_composicao"] = list(herois_por_n[p["n"]])
        out.append(q)
    return out


# sequência real da receita r3 da Sprint (saida/render-report.json de 09/10/2026)
SEQ_SPRINT_R3 = [("capa", "a"), ("manifesto", "b"), ("projecao", None), ("publico", "a"), ("historico_logos", None),
                 ("territorio", None), ("prova", None), ("divisor", "a"), ("ativo_painel", "sangria"), ("ativo_topo", "a"),
                 ("ativo_painel", "sangria"), ("ativo_painel", "a"), ("ativo_painel", "sangria"), ("ativo_painel", "a"),
                 ("divisor_cotas", None), ("cota", "b"), ("cota", "b"), ("cota", "b"), ("cota", "b"), ("contato", "b")]
# 12 páginas, 9 elegíveis (1, 2, 4, 6, 7, 8, 10, 11, 12): projeção e divisor de cotas não têm encaixe de herói; a prova
# tem, mas a regra do dono tira o herói dela
SEQ_TESTE = [("capa", "c"), ("manifesto", "a"), ("projecao", None), ("publico", "a"), ("prova", None), ("divisor", "b"),
             ("ativo_painel", "diagonal"), ("ativo_topo", "a"), ("divisor_cotas", None), ("cota", "a"), ("cota", "a"), ("contato", "a")]


def sistema_teste(pattern="pat-novo", excecoes=None):
    return {"motivos": [{"id": "a", "origem": "esporte", "descricao": "motivo a"}, {"id": "b", "origem": "territorio", "descricao": "motivo b"},
                        {"id": "c", "origem": "esporte", "descricao": "motivo c"}],
            "familias": [{"id": "linha-ouro", "meio": "traco", "estilo": "fine gold line, single weight", "paleta": ["#D4A64A"],
                          "traco_px": 2, "luz": None, "ancora": None, "aprovada": None}],
            "constantes": [{"tipo": "grao"},
                           {"tipo": "microtexto", "texto_de": "personalizado", "texto": "TESTE · 2027", "encaixe": "borda-base", "exceto": ["projecao"]},
                           {"tipo": "selo", "texto_de": "personalizado", "texto": "TESTE ·", "encaixe": None, "exceto": ["prova", "cota", "projecao"]}],
            "receitas": {"r1": {"familia": "linha-ouro", "motivos": ["a", "b", "c"], "pattern": pattern}},
            "excecoes": excecoes or {}}


def heroi(i, kit, novo=True, aspecto=None, motivo=None):
    e = {"id": i, "papel": "heroi", "tipo": "ilustracao", "formato": "png", "familia": "linha-ouro",
         "motivo": motivo or "abc"[sum(map(ord, i)) % 3], "arquivo": f"acervo/elementos/{i}.png",
         "kit_origem": kit if novo else "kit-antigo", "exclusivo_cliente": None, "gerado": True,
         "rota": "codex-alfa" if novo else "biblioteca"}
    if aspecto:
        e["aspecto"] = aspecto
    return e


def pattern(i, kit, novo=True):
    return {"id": i, "papel": "pattern", "tipo": "pattern", "formato": "png", "familia": "linha-ouro", "motivo": "b",
            "arquivo": f"acervo/elementos/{i}.png", "kit_origem": kit if novo else "kit-antigo", "exclusivo_cliente": None,
            "gerado": True, "rota": "codex-alfa" if novo else "biblioteca", "escala_tile": 420}


def desenhar_linhas(caminho, semente, lado=800, largura=4, cor=(0xD4, 0xA6, 0x4A), tile=False):
    """Traço dourado de espessura fixa sobre fundo transparente (membro sintético da família linha-ouro)."""
    rng = np.random.default_rng(semente)
    im = Image.new("RGBA", (lado, lado), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for _ in range(14 if not tile else 30):
        x0, y0 = (int(v) for v in rng.integers(30, lado - 30, 2)); x1, y1 = (int(v) for v in rng.integers(30, lado - 30, 2))
        d.line([(x0, y0), (x1, y1)], fill=cor + (255,), width=largura)
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    im.save(caminho)


def montar_kit(pasta, elementos, sistema, kit="kit-teste", cliente="CLIENTE TESTE", seq=SEQ_TESTE, receita="r1"):
    """Kit mínimo para o qa_conjunto: mediakit.json, imagens sintéticas e o plano provisório em saida/."""
    pasta = Path(pasta)
    for n, e in enumerate(elementos):
        alvo = pasta / e["arquivo"]
        if not alvo.exists():
            desenhar_linhas(alvo, 1000 + n, lado=600 if e["papel"] == "pattern" else 800,
                            largura=3 if e["papel"] == "pattern" else 4, tile=e["papel"] == "pattern")
    k = {"kit": kit, "cliente": cliente, "sistema_elementos": sistema, "elementos": elementos}
    (pasta / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False, indent=2), encoding="utf-8")
    plano = pe.plano_provisorio(sistema, elementos, receita, paginas(seq), catalogo())
    (pasta / "saida").mkdir(parents=True, exist_ok=True)
    (pasta / "saida" / f"plano-elementos-{receita}.json").write_text(json.dumps(plano, ensure_ascii=False, indent=2), encoding="utf-8")
    return k, plano


def herois_do_plano(plano):
    return {pg["n"]: a["id"] for pg in plano for a in pg["atribuidos"] if a["papel"] == "heroi"}


def falhas(res):
    return [m for n, m in res if n == "FALHA"]


# ---------------------------------------------------------------- provas do planejador
def test_mesma_entrada_mesma_saida():
    sis = sistema_teste(); els = [heroi(f"h{i}", "kit-teste", aspecto=("quadrado", "largo", "alto")[i % 3]) for i in range(5)] + [pattern("pat-novo", "kit-teste")]
    pags = paginas(SEQ_TESTE)
    a = pe.planejar(sis, els, "r1", pags, catalogo()); b = pe.planejar(sis, els, "r1", pags, catalogo())
    assert a == b
    # e em processos com semente de hash diferente (pega ordem de set/dict que vaze para a saída)
    prog = ("import json,sys; sys.path.insert(0, %r); import test_plano_elementos as t, plano_elementos as pe;"
            "els=[t.heroi(f'h{i}','kit-teste',aspecto=('quadrado','largo','alto')[i%%3]) for i in range(5)]+[t.pattern('pat-novo','kit-teste')];"
            "print(json.dumps(pe.planejar(t.sistema_teste(), els, 'r1', t.paginas(t.SEQ_TESTE), t.catalogo()), sort_keys=True))") % str(AQUI)
    saidas = [subprocess.run([sys.executable, "-c", prog], capture_output=True, text=True, env=dict(os.environ, PYTHONHASHSEED=s)).stdout for s in ("1", "2", "777")]
    assert saidas[0] and saidas[0] == saidas[1] == saidas[2], [s[:200] for s in saidas]
    assert json.loads(saidas[0]) == json.loads(json.dumps(a, sort_keys=True))
    print("   3 processos (PYTHONHASHSEED 1, 2, 777) e 2 chamadas: plano idêntico")


def test_regras_do_heroi_com_elementos_suficientes():
    sis = sistema_teste(); els = [heroi(f"h{i}", "kit-teste") for i in range(4)] + [pattern("pat-novo", "kit-teste")]
    pags = paginas(SEQ_TESTE); plano = pe.planejar(sis, els, "r1", pags, catalogo())
    h = herois_do_plano(plano)
    eleg = [p["n"] for p in pags if pe.elegivel(p, catalogo())]
    assert eleg == [1, 2, 4, 6, 7, 8, 10, 11, 12], eleg
    assert 3 not in h and 5 not in h and 9 not in h, h          # projeção, prova e divisor de cotas sem herói
    assert len([n for n in eleg if n in h]) / len(eleg) >= 0.7, h
    assert len(h) == len(eleg), f"com 4 heróis × 3 usos = 12 ≥ 9 elegíveis, todas cobertas: {h}"
    assert all(h.get(n + 1) != x for n, x in h.items()), f"herói repetido em páginas seguidas: {h}"
    assert max(__import__("collections").Counter(h.values()).values()) <= 3, h
    assert all(sum(1 for a in pg["atribuidos"] if a["papel"] == "heroi") <= 1 for pg in plano)
    print("   heróis por página:", " ".join(f"{n}:{x}" for n, x in sorted(h.items())))


def test_capa_prefere_heroi_novo():
    # o novo se chama "z-novo" e vem por último em elementos[]: só a regra da capa o põe lá (não o desempate por nome
    # ou ordem), e o reusado tem o aspecto certo para a capa
    sis = sistema_teste()
    els = [heroi("a-velho", "kit-teste", novo=False, aspecto="quadrado"), heroi("b-velho", "kit-teste", novo=False),
           heroi("z-novo", "kit-teste", aspecto="alto")]
    plano = pe.planejar(sis, els, "r1", paginas(SEQ_TESTE), catalogo())
    assert herois_do_plano(plano)[1] == "z-novo", herois_do_plano(plano)


def test_vizinho_e_limite_de_usos_valem_mesmo_quando_o_aspecto_pede_repetir():
    """Um herói casa perfeito com todas as páginas e os outros não: sem as duas regras ele ocuparia páginas seguidas e
    passaria de 3 usos."""
    sis = sistema_teste(); cat = catalogo()
    seq = [("capa", "c"), ("publico", "a"), ("ativo_painel", "a"), ("ativo_painel", "sangria"), ("contato", "a"),
           ("capa", "c"), ("publico", "a"), ("contato", "a")]                     # 8 encaixes quadrados seguidos
    els = [heroi("perfeito", "kit-teste", aspecto="quadrado"), heroi("alto-1", "kit-teste", aspecto="alto"), heroi("alto-2", "kit-teste", aspecto="alto")]
    h = herois_do_plano(pe.planejar(sis, els, "r1", paginas(seq), cat))
    print("   ", " ".join(f"{n}:{x}" for n, x in sorted(h.items())))
    assert all(h.get(n + 1) != x for n, x in h.items()), h
    assert list(h.values()).count("perfeito") == 3, h


def test_aspecto_casa_com_o_encaixe():
    sis = sistema_teste()
    els = [heroi("alto", "kit-teste", aspecto="alto"), heroi("largo", "kit-teste", aspecto="largo"), heroi("quad", "kit-teste", aspecto="quadrado")]
    pags = paginas(SEQ_TESTE); cat = catalogo(); plano = pe.planejar(sis, els, "r1", pags, cat)
    h = herois_do_plano(plano)
    casou = 0
    for n, x in h.items():
        slot = pe.aspecto_encaixe([e for e in cat[pags[n - 1]["rotulo"]] if "heroi" in e["papeis"]][0])
        casou += {"alto": "alto", "largo": "largo", "quad": "quadrado"}[x] == slot
    print(f"   {casou} de {len(h)} heróis no encaixe do mesmo aspecto: " + " ".join(f"{n}:{x}" for n, x in sorted(h.items())))
    assert casou >= 7, h
    # o encaixe preferido do herói alto é o lateral alto quando a página tem os dois
    pg = pe.planejar(sis, [heroi("alto", "kit-teste", aspecto="alto")], "r1", paginas([("capa", "a")]), cat)[0]
    assert pg["atribuidos"][0]["encaixes_preferidos"][0] == "lateral-alta", pg


def test_excecoes_por_cima():
    exc = {"r1": {"divisor:b": {"heroi": None, "porque": "página de respiro"}, "ativo:diagonal": {"heroi": "h0", "encaixe": "canto-x", "camada": "atras", "porque": "teste"}}}
    sis = sistema_teste(excecoes=exc); els = [heroi(f"h{i}", "kit-teste") for i in range(4)]
    plano = pe.planejar(sis, els, "r1", paginas(SEQ_TESTE), catalogo()); h = herois_do_plano(plano)
    assert 6 not in h, h                                          # heroi null: página sem herói
    assert h[7] == "h0" and h.get(6) != "h0" and h.get(8) != "h0", h
    item = next(a for a in plano[6]["atribuidos"] if a["papel"] == "heroi")
    assert item["encaixes_preferidos"][0] == "canto-x" and item["camada"] == "atras", item
    assert not pe.elegivel(paginas(SEQ_TESTE)[5], catalogo(), pe._excecao(sis, "r1", paginas(SEQ_TESTE)[5]))


def test_constantes_respeitam_exceto():
    plano = pe.planejar(sistema_teste(), [heroi("h0", "kit-teste")], "r1", paginas(SEQ_TESTE), catalogo())
    tipos = {pg["n"]: [a["tipo"] for a in pg["atribuidos"] if a["papel"] == "constante"] for pg in plano}
    assert tipos[3] == ["grao"], tipos[3]                         # projeção: só o grão
    assert tipos[5] == ["grao", "microtexto"], tipos[5]           # prova: sem selo
    assert tipos[10] == ["grao", "microtexto"], tipos[10]         # cota: sem selo
    assert tipos[1] == ["grao", "microtexto", "selo"], tipos[1]
    selo = next(a for a in plano[0]["atribuidos"] if a.get("tipo") == "selo")
    assert selo["encaixes_preferidos"][0] == "selo-canto", selo   # o encaixe que o microtexto declarou fica por último


# ---------------------------------------------------------------- provas da composição no planejador
def test_pagina_composta_nao_recebe_heroi_automatico():
    sis = sistema_teste(); els = [heroi(f"h{i}", "kit-teste") for i in range(4)] + [pattern("pat-novo", "kit-teste")]
    pags = paginas(SEQ_TESTE); cat = catalogo()
    controle = herois_do_plano(pe.planejar(sis, els, "r1", pags, cat))
    assert 2 in controle and 7 in controle, controle              # sem composição, as duas páginas têm herói
    plano = pe.planejar(sis, els, "r1", com_composicao(pags, so_marca=(2, 7)), cat)
    h = herois_do_plano(plano)
    assert 2 not in h and 7 not in h, h
    assert all(n in h for n in (1, 4, 6, 8, 10, 11, 12)), f"as demais elegíveis continuam cobertas (4 heróis x 3 usos): {h}"
    for n in (2, 7):                                               # constantes e pattern ficam; só o herói (e o apoio) sai
        itens = plano[n - 1]["atribuidos"]
        assert not any(a["papel"] in ("heroi", "apoio") for a in itens), itens
        assert {a["tipo"] for a in itens if a["papel"] == "constante"} >= {"grao", "microtexto"}, itens
    print("   páginas 2 e 7 compostas: sem herói automático; as outras 7 elegíveis cobertas:", " ".join(f"{n}:{x}" for n, x in sorted(h.items())))


def test_usos_do_heroi_da_composicao_contam_no_limite_de_3():
    """Dois heróis e a composição põe o h0 em 3 páginas: o automático não pode usar o h0 uma 4ª vez. Sem a conta, o
    planejador daria ao h0 mais 3 usos nas elegíveis e o QA de conjunto reprovaria (limite de 3 por receita)."""
    sis = sistema_teste(); els = [heroi("h0", "kit-teste"), heroi("h1", "kit-teste"), pattern("pat-novo", "kit-teste")]
    pags = paginas(SEQ_TESTE); cat = catalogo()
    controle = herois_do_plano(pe.planejar(sis, els, "r1", pags, cat))
    assert list(controle.values()).count("h0") == 3, controle     # sem composição o h0 chega a 3 usos pelo plano
    h = herois_do_plano(pe.planejar(sis, els, "r1", com_composicao(pags, {1: ["h0"], 4: ["h0"], 8: ["h0"]}), cat))
    assert sorted(n for n, x in h.items() if x == "h0") == [1, 4, 8], f"h0 só onde a composição o pôs: {h}"
    assert list(h.values()).count("h1") <= 3 and 1 in h and 4 in h and 8 in h, h
    print("   h0 nas páginas da composição (1, 4, 8) e nenhum uso a mais:", " ".join(f"{n}:{x}" for n, x in sorted(h.items())))


def test_heroi_da_composicao_vale_como_vizinho():
    """h0 casa de graça com a capa (aspecto quadrado) e h1 não. A composição põe o h0 na página 2: a 1 não pode repetir
    o h0 em página seguida e fica com o h1."""
    sis = sistema_teste(); cat = catalogo()
    els = [heroi("h0", "kit-teste", aspecto="quadrado"), heroi("h1", "kit-teste", aspecto="largo"), pattern("pat-novo", "kit-teste")]
    pags = paginas(SEQ_TESTE)
    assert herois_do_plano(pe.planejar(sis, els, "r1", pags, cat))[1] == "h0"          # controle: sem composição a capa é do h0
    h = herois_do_plano(pe.planejar(sis, els, "r1", com_composicao(pags, {2: ["h0"]}), cat))
    assert h[2] == "h0" and h[1] == "h1", h
    assert all(h.get(n + 1) != x for n, x in h.items()), f"nenhum herói em páginas seguidas: {h}"


def test_composicao_vence_excecao_e_ajuste_manual():
    """Precedência (references/08): composição > ajuste manual > exceção > catálogo. Na página composta a exceção de
    herói e o `paginas` do herói não valem."""
    exc = {"r1": {"manifesto:a": {"heroi": "h0", "porque": "teste"}}}
    sis = sistema_teste(excecoes=exc); cat = catalogo()
    els = [heroi(f"h{i}", "kit-teste") for i in range(4)] + [pattern("pat-novo", "kit-teste")]
    els = [dict(e, paginas=["ativo:topo"]) if e["id"] == "h1" else e for e in els]       # h1 fixo na página 8 (ajuste manual)
    pags = paginas(SEQ_TESTE)
    h = herois_do_plano(pe.planejar(sis, els, "r1", pags, cat))
    assert h[2] == "h0" and h[8] == "h1", h                         # controle: exceção e ajuste manual valem sem composição
    plano = pe.planejar(sis, els, "r1", com_composicao(pags, so_marca=(2, 8)), cat)
    h = herois_do_plano(plano)
    assert 2 not in h and 8 not in h, h
    assert "h1" not in h.values(), f"herói com `paginas` continua sem ser distribuído em outras páginas: {h}"
    assert not any(a["papel"] == "apoio" for pg in plano for a in pg["atribuidos"])


def test_heroi_fixado_mais_adiante_conta_no_limite_de_3():
    """Defeito achado ao somar a composição: a busca só contava o uso do herói fixado (exceção, ajuste manual ou
    composição) quando chegava na página dele. Com 2 heróis e o h0 fixado por exceção na página 8, o h0 ganhava 3 usos
    antes e o 4º na exceção (o QA de conjunto reprovava: 'usado 4 vezes')."""
    exc = {"r1": {"ativo:topo": {"heroi": "h0", "porque": "teste"}}}
    sis = sistema_teste(excecoes=exc); cat = catalogo()
    els = [heroi("h0", "kit-teste"), heroi("h1", "kit-teste"), pattern("pat-novo", "kit-teste")]
    h = herois_do_plano(pe.planejar(sis, els, "r1", paginas(SEQ_TESTE), cat))
    print("   ", " ".join(f"{n}:{x}" for n, x in sorted(h.items())))
    assert h[8] == "h0", h
    assert list(h.values()).count("h0") <= 3 and list(h.values()).count("h1") <= 3, h
    assert all(h.get(n + 1) != x for n, x in h.items()), h


def test_pagina_composta_leva_o_heroi_da_composicao_como_item_comum():
    """O herói que a composição põe sai no plano como item comum (sem `origem`): a vertical, derivada do plano do
    horizontal, repete o herói da página equivalente. Id que não está em elementos[] (grafismo da página) não vira item,
    mas também não quebra nada."""
    sis = sistema_teste(); cat = catalogo()
    els = [heroi(f"h{i}", "kit-teste") for i in range(3)] + [pattern("pat-novo", "kit-teste")]
    pags = com_composicao(paginas(SEQ_TESTE), {1: ["h2"], 4: ["numeral-p4"]})
    plano = pe.planejar(sis, els, "r1", pags, cat)
    capa = [a for a in plano[0]["atribuidos"] if a["papel"] == "heroi"]
    assert len(capa) == 1 and capa[0]["id"] == "h2" and set(capa[0]) == {"id", "papel", "encaixes_preferidos", "camada"}, capa
    assert capa[0]["encaixes_preferidos"], capa
    assert not [a for a in plano[3]["atribuidos"] if a["papel"] == "heroi"], plano[3]


def test_elegivel_e_provisorio_com_composicao():
    sis = sistema_teste(); cat = catalogo()
    els = [heroi(f"h{i}", "kit-teste") for i in range(3)] + [pattern("pat-novo", "kit-teste")]
    p = paginas(SEQ_TESTE)[1]; pc = dict(p, composicao=True)
    assert pe.elegivel(p, cat) and not pe.elegivel(pc, cat), "a página composta não é elegível a herói AUTOMÁTICO"
    assert pe.elegivel(pc, cat, auto=False), "mas o catálogo aceita herói nela (é o que o render grava em elegivel_heroi)"
    prov = pe.plano_provisorio(sis, els, "r1", com_composicao(paginas(SEQ_TESTE), {2: ["h0"]}), cat)
    pg = prov["paginas"][1]
    assert pg["elegivel_heroi"] is True and [e["id"] for e in pg["elementos"] if e["papel"] == "heroi"] == ["h0"], pg
    assert prov["paginas"][0]["elegivel_heroi"] is True            # página sem composição: igual a hoje


def test_faltantes_nao_pede_heroi_para_pagina_composta():
    """O `faltantes` (que decide quantos heróis gerar) usa `elegivel`: a página que a composição resolve não entra na conta."""
    fx = json.loads(FIXTURE.read_text(encoding="utf-8")); sis = fx["sistema_elementos"]; els = fx["elementos"]
    pags = paginas(SEQ_SPRINT_R3); cat = catalogo()
    antes = pe.faltantes(sis, els, "r3", pags, cat)
    depois = pe.faltantes(sis, els, "r3", com_composicao(pags, so_marca=(1, 2, 4, 6)), cat)
    print(f"   r3: {antes['elegiveis']} elegíveis e {antes['total_herois']} herói(s) a gerar; com 4 páginas compostas: {depois['elegiveis']} e {depois['total_herois']}")
    assert depois["elegiveis"] == antes["elegiveis"] - 4, (antes["elegiveis"], depois["elegiveis"])
    assert depois["total_herois"] <= antes["total_herois"], (antes["total_herois"], depois["total_herois"])
    assert depois["heroi_capa_novo"] is None, "capa composta: a regra da capa nova é da composição"


def test_sem_composicao_o_contrato_novo_nao_muda_nada():
    """Campo ausente, falso ou lista vazia = o plano de hoje (kit legado sai igual)."""
    sis = sistema_teste(); cat = catalogo()
    els = [heroi(f"h{i}", "kit-teste", aspecto=("quadrado", "largo", "alto")[i % 3]) for i in range(5)] + [pattern("pat-novo", "kit-teste")]
    pags = paginas(SEQ_TESTE)
    base = pe.planejar(sis, els, "r1", pags, cat)
    neutras = [dict(p, composicao=False, herois_composicao=[]) for p in pags]
    assert pe.planejar(sis, els, "r1", neutras, cat) == base
    assert pe.plano_provisorio(sis, els, "r1", neutras, cat) == pe.plano_provisorio(sis, els, "r1", pags, cat)


def test_faltantes_quando_nao_ha_herois_suficientes():
    fx = json.loads(FIXTURE.read_text(encoding="utf-8")); sis = fx["sistema_elementos"]; els = fx["elementos"]
    pags = paginas(SEQ_SPRINT_R3); cat = catalogo()
    for r in ("r3", "r1"):
        f = pe.faltantes(sis, els, r, pags, cat)
        print(f"   {r}: cobertura {f['cobertura']:.0%} ({f['cobertas']} de {f['elegiveis']}); pedir: {f['pedidos']}")
        assert f["cobertura"] < 0.7 and f["total_herois"] >= 1
        assert all(x["motivo"] in sis["receitas"][r]["motivos"] for x in f["herois"])
        # a lista basta: com os heróis pedidos, o replanejamento passa de 70%
        extras = [dict(heroi(f"x{i}-{j}", fx["kit"], aspecto=x["aspecto"], motivo=x["motivo"]), familia=sis["receitas"][r]["familia"])
                  for i, x in enumerate(f["herois"]) for j in range(x["quantidade"])]
        h = herois_do_plano(pe.planejar(sis, els + extras, r, pags, cat))
        eleg = [p["n"] for p in pags if pe.elegivel(p, cat)]
        assert len([n for n in eleg if n in h]) / len(eleg) >= 0.7, (r, h)
    f = pe.faltantes(sistema_teste(), [heroi(f"h{i}", "kit-teste") for i in range(4)] + [pattern("pat-novo", "kit-teste")], "r1", paginas(SEQ_TESTE), catalogo())
    assert f["herois"] == [] and f["pattern"] is None and f["cobertura"] == 1.0, f


# ---------------------------------------------------------------- provas do QA de conjunto (novidade)
def _kit_qa(d, herois_novos, herois_velhos, pattern_novo=True, excecoes=None):
    els = [heroi(f"h-novo-{i}", "kit-teste") for i in range(herois_novos)] + \
          [heroi(f"h-velho-{i}", "kit-teste", novo=False) for i in range(herois_velhos)]
    pid = "pat-novo" if pattern_novo else "pat-velho"
    els.append(pattern(pid, "kit-teste", novo=pattern_novo))
    montar_kit(d, els, sistema_teste(pattern=pid, excecoes=excecoes))
    bib = Path(d) / "bib-vazia"; bib.mkdir(exist_ok=True)
    return qa_conjunto.checar(d, bib=bib)


def test_qa_conjunto_controle_sem_falha():
    with tempfile.TemporaryDirectory() as d:
        res = _kit_qa(d, 9, 0)
        assert falhas(res) == [], falhas(res)
        print(f"   kit todo novo: 0 falhas, {len(res)} avisos (OCR pendente, família sem aprovação, plano provisório)")


def test_qa_novidade_5_de_10_reprova_sozinha():
    with tempfile.TemporaryDirectory() as d:
        f = falhas(_kit_qa(d, 4, 5))                   # 4 heróis novos + pattern novo = 5 de 10 distintos
        print("  ", f)
        assert len(f) == 1 and "50%" in f[0] and "5 de 10" in f[0], f


def test_qa_sem_pattern_novo_reprova_sozinha():
    with tempfile.TemporaryDirectory() as d:
        f = falhas(_kit_qa(d, 9, 0, pattern_novo=False))   # 9 de 10 novos, mas o pattern é reusado
        print("  ", f)
        assert len(f) == 1 and "nenhum pattern novo" in f[0], f


def test_qa_heroi_de_capa_reusado_reprova_sozinho():
    with tempfile.TemporaryDirectory() as d:
        exc = {"r1": {"capa:c": {"heroi": "h-velho-0", "porque": "prova: capa com herói reusado"}}}
        f = falhas(_kit_qa(d, 8, 1, excecoes=exc))   # 9 de 10 novos, pattern novo, capa com o reusado
        print("  ", f)
        assert len(f) == 1 and "herói da capa `h-velho-0` não é novo" in f[0], f


def test_qa_regras_por_pagina_reprovam():
    """Plano gravado à mão com os três defeitos: herói repetido em páginas seguidas, 4 usos e cobertura baixa."""
    with tempfile.TemporaryDirectory() as d:
        _kit_qa(d, 9, 0)
        caminho = Path(d) / "saida" / "plano-elementos-r1.json"; plano = json.loads(caminho.read_text())
        for pg in plano["paginas"]:
            for x in pg["elementos"]:
                if x["papel"] == "heroi":
                    x["id"] = "h-novo-0" if pg["n"] in (1, 2, 4, 6) else x["id"]
            if pg["n"] in (8, 10, 11, 12):
                pg["elementos"] = [x for x in pg["elementos"] if x["papel"] != "heroi"]
        caminho.write_text(json.dumps(plano))
        f = falhas(qa_conjunto.checar(d, bib=Path(d) / "bib-vazia"))
        print("  ", f)
        assert any("repetido nas páginas seguidas 1 e 2" in m for m in f), f
        assert any("usado 4 vezes" in m for m in f), f
        assert any("cobertura de herói 56%" in m for m in f), f


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

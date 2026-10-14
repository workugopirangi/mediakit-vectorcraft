#!/usr/bin/env python3
"""Provas das regras da camada de acabamento no qa_geometria.py (mk-2.1, references/10-acabamento.md, seção QA).
Rodar: ~/.venvs/mediakit/bin/python test_qa_geometria.py

Cada regra tem o plano mutante que falha (ou avisa) e o par que passa, e o MUTANTE INVERSO: o mesmo plano sem os campos
da camada (papel acabamento, efeito, cruza, derivado_de, registro) dá exatamente o que dava antes. Os planos são
sintéticos, no formato que o render grava (itens svg sem geometria: a máscara é a caixa, a conta é exata); os PNG de
contraste são desenhados numa pasta temporária. Sem render e sem kit vivo."""
import json, shutil, sys, tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import qa_geometria as qg  # noqa: E402

PASTA = Path(tempfile.mkdtemp(prefix="test-qa-geometria-"))


def item(id_, papel="heroi", camada="frente", x=0, y=0, w=100, h=100, **extra):
    return dict({"id": id_, "papel": papel, "camada": camada, "x": x, "y": y, "w": w, "h": h, "rot": 0, "formato": "svg",
                 "encaixe": None}, **extra)


def pagina(itens, protegidos=(), alvos=None, dom=None, n=1, **extra):
    pg = {"n": n, "rotulo": "prova", "elementos": list(itens), "protegidos": list(protegidos), "erros_composicao": []}
    if alvos is not None:
        pg["alvos"] = alvos
    if dom is not None:
        pg["dom"] = dom
    pg.update(extra)
    return pg


def plano(*paginas, erros=()):
    return {"largura": 1920, "altura": 1080, "composicao_kit": False, "paginas": list(paginas),
            "composicao_erros": list(erros), "receita": "r1"}


def roda(pl, png=None, textos=None, kit=None):
    return qg.checar_plano(pl, PASTA, "r1", png, textos, kit)


def com(msgs, trecho):
    return [m for m in msgs if trecho in m]


def png_fundo(nome, fundo, caixa_fundo, letras=None):
    """PNG 1920x1080 escuro com uma região `caixa_fundo` pintada de `fundo` e "letras" brancas nos retângulos dados."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (1920, 1080), (17, 17, 17))
    dr = ImageDraw.Draw(im)
    dr.rectangle(caixa_fundo, fill=fundo)
    for r in letras or []:
        dr.rectangle(r, fill=(255, 255, 255))
    p = PASTA / f"{nome}.png"
    im.save(p)
    return p


# ------------------------------------------------------------------------------------------------- máximo de 2 por página
def test_terceiro_acabamento_na_pagina_reprova():
    tres = [item(f"a{i}", "acabamento", "atras", x=300 * i, y=0) for i in range(3)]
    f, _ = roda(plano(pagina(tres)))
    assert len(com(f, "3 elementos de papel acabamento")) == 1, f
    f, _ = roda(plano(pagina(tres[:2])))
    assert not com(f, "papel acabamento"), f
    # sombra e reflexo derivados não contam: 2 acabamentos + 2 derivados passa
    derivados = [item("a0-sombra", "acabamento", "atras", x=900, derivado_de="a0"),
                 item("a0-reflexo", "acabamento", "atras", x=1200, derivado_de="a0")]
    f, _ = roda(plano(pagina(tres[:2] + derivados)))
    assert not com(f, "papel acabamento"), f
    # a composição já acusou a página (composicao_erros): não sai duas vezes
    pl = plano(pagina(tres, composicao={"chave": "prova"}),
               erros=["composicao/prova: 3 elementos de papel acabamento (máximo 2 por página)"])
    f, _ = roda(pl)
    assert len(com(f, "papel acabamento")) == 1 and f[0].startswith("r1 composição:"), f
    # inverso: os mesmos três como estrutura (o legado) não têm limite
    f, _ = roda(plano(pagina([dict(t, papel="estrutura") for t in tres])))
    assert not f, f


def test_derivado_fica_fora_da_conta_de_heroi():
    pai = item("selo", "heroi", x=500, y=500, w=200, h=200)
    filho = item("selo-sombra", "heroi", "atras", x=500, y=690, w=200, h=40)
    f, _ = roda(plano(pagina([pai, dict(filho, derivado_de="selo")])))
    assert not f, f
    f, _ = roda(plano(pagina([pai, filho])))                       # inverso: sem derivado_de, são 2 heróis (legado)
    assert com(f, "2 elementos de papel heroi"), f


# ------------------------------------------------------------------------------------------------- sobreposição
def test_sobreposicao_relaxa_so_o_acabamento_leve_e_o_derivado():
    heroi = item("h", "heroi", x=0, y=0, w=400, h=400)
    sobre = lambda **kw: item("a", "acabamento", "atras", x=100, y=100, w=400, h=400, **kw)   # noqa: E731
    casos = {
        "acabamento .24 atrás": (sobre(efeito={"opacidade": 0.24}), False),
        "acabamento .12 sob o véu": (dict(sobre(efeito={"opacidade": 0.12}), camada="sob-veu"), False),
        "acabamento .46 atrás": (sobre(efeito={"opacidade": 0.46}), True),
        "acabamento .24 na frente": (dict(sobre(efeito={"opacidade": 0.24}), camada="frente"), True),
        "acabamento opaco atrás": (sobre(), True),
        "opacidade só no item (.24) atrás": (sobre(opacidade=0.24), False),
        "heroi .24 atrás (legado)": (dict(sobre(opacidade=0.24), papel="apoio"), True),
        "derivado do herói": (dict(sobre(), derivado_de="h"), False),
    }
    for nome, (outro, reprova) in casos.items():
        f, _ = roda(plano(pagina([heroi, outro])))
        assert bool(com(f, "sobrepostos")) == reprova, (nome, f)
    irmaos = [item("p-sombra", "acabamento", "atras", 0, 0, 300, 300, derivado_de="p"),
              item("p-reflexo", "acabamento", "atras", 50, 50, 300, 300, derivado_de="p")]
    f, _ = roda(plano(pagina(irmaos)))
    assert not com(f, "sobrepostos"), f


# ------------------------------------------------------------------------------------------------- translúcido sob o corpo
CORPO = {"classe": "corpo", "x": 200, "y": 600, "w": 800, "h": 40, "texto": "A cidade muda de ritmo"}
TEXTOS = [{"x": 200, "y": 600, "w": 800, "h": 40, "cor": "#FFFFFF", "fs": 24}]
LETRAS = [[210 + k * 60, 606, 240 + k * 60, 634] for k in range(13)]


def test_acabamento_translucido_sob_corpo_vale_o_contraste():
    sob = item("hachura", "acabamento", "atras", x=150, y=560, w=500, h=120, efeito={"opacidade": 0.24})
    escuro = png_fundo("corpo-escuro", (40, 40, 40), [150, 560, 650, 680], LETRAS)
    claro = png_fundo("corpo-claro", (210, 210, 210), [150, 560, 650, 680], LETRAS)
    pl = plano(pagina([sob], [CORPO]))
    f, a = roda(pl, lambda n: escuro, lambda n: TEXTOS)
    assert not f and not com(a, "hachura"), (f, a)
    f, _ = roda(pl, lambda n: claro, lambda n: TEXTOS)
    assert len(com(f, "o contraste da linha")) == 1, f
    f, _ = roda(pl)
    assert len(com(f, "não há PNG")) == 1, f
    # textura sob texto corrido: passa no contraste e avisa
    tex = plano(pagina([dict(sob, grafismo={"tipo": "hachura", "params": {}})], [CORPO]))
    f, a = roda(tex, lambda n: escuro, lambda n: TEXTOS)
    assert not f and len(com(a, "textura sob texto corrido")) == 1, (f, a)
    # inversos: o mesmo item opaco, na frente ou como herói (legado) continua no limite de 4%
    for nome, outro in (("opaco", dict(sob, efeito={})), ("frente", dict(sob, camada="frente")),
                        ("herói translúcido", dict(sob, papel="heroi"))):
        f, _ = roda(plano(pagina([outro], [CORPO])), lambda n: escuro, lambda n: TEXTOS)
        assert len(com(f, "cobre corpo")) == 1, (nome, f)


# ------------------------------------------------------------------------------------------------- cruza
LINHA1 = {"classe": "titulo", "x": 100, "y": 200, "w": 1000, "h": 100, "texto": "TRAVESSIA"}
LINHA2 = {"classe": "titulo", "x": 100, "y": 300, "w": 1000, "h": 100, "texto": "DA LUA"}
TEXTOS_T = [{"x": 100, "y": 200, "w": 1000, "h": 200, "cor": "#FFFFFF", "fs": 96}]
LETRAS_T = [[110 + k * 90, 215, 160 + k * 90, 385] for k in range(11)]


def test_cruza_sobe_o_limite_de_uma_linha_do_titulo_para_20():
    bom = png_fundo("titulo-escuro", (30, 30, 30), [900, 150, 1100, 450], LETRAS_T)
    ruim = png_fundo("titulo-claro", (220, 220, 220), [900, 150, 1100, 450], LETRAS_T)
    medalha = item("medalha", "heroi", "frente", x=950, y=150, w=150, h=200, cruza={"alvo": "titulo", "corte": "cy", "y": 250})
    pl = plano(pagina([medalha], [LINHA1, LINHA2]))                  # 15% da linha 1 e 7,5% da linha 2
    f, a = roda(pl, lambda n: bom, lambda n: TEXTOS_T)
    assert not f and len(com(a, "cruza o titulo")) == 1 and "15%" in com(a, "cruza o titulo")[0], (f, a)
    f, _ = roda(pl, lambda n: ruim, lambda n: TEXTOS_T)
    assert len(com(f, "o contraste cai")) == 1, f
    f, _ = roda(pl)
    assert len(com(f, "não há PNG")) == 1, f
    # o cruza vale por `efeito.cruza` também (a composição copiada pelo render)
    f, a = roda(plano(pagina([dict(medalha, cruza=None, efeito={"cruza": {"alvo": "titulo", "corte": "cy"}})], [LINHA1, LINHA2])),
                lambda n: bom, lambda n: TEXTOS_T)
    assert not f and com(a, "cruza o titulo"), (f, a)
    # acima de 20% na linha: reprova
    grande = dict(medalha, x=850, w=250)                              # 25% da linha 1
    f, _ = roda(plano(pagina([grande], [LINHA1])), lambda n: bom, lambda n: TEXTOS_T)
    assert len(com(f, "cobre titulo: 25%")) == 1, f
    # duas linhas acima de 8%: só a mais coberta relaxa
    alta = dict(medalha, y=180, h=240)                                # 15% de cada linha
    f, a = roda(plano(pagina([alta], [LINHA1, LINHA2])), lambda n: bom, lambda n: TEXTOS_T)
    assert len(com(a, "cruza o titulo")) == 1 and len(com(f, "cobre titulo")) == 1, (f, a)
    # inverso: sem cruza (legado), 15% da linha do título reprova como sempre
    f, _ = roda(plano(pagina([dict(medalha, cruza=None)], [LINHA1, LINHA2])), lambda n: bom, lambda n: TEXTOS_T)
    assert len(com(f, "cobre titulo: 15%")) == 1, f


# ------------------------------------------------------------------------------------------------- registro
FOTO = {"x": 824, "y": 0, "w": 1096, "h": 1080, "img": {"fit": "cover", "pos": "50% 50%", "nat_w": 2000, "nat_h": 1000}}


def test_caixa_object_fit_e_a_conta_do_navegador():
    assert qg.caixa_object_fit(FOTO) == (292.0, 0.0, 2160.0, 1080.0)
    assert qg.caixa_object_fit(dict(FOTO, img=dict(FOTO["img"], pos="0% 50%"))) == (824.0, 0.0, 2160.0, 1080.0)
    assert qg.caixa_object_fit(dict(FOTO, img=dict(FOTO["img"], fit="contain"))) == (824.0, 266.0, 1096.0, 548.0)
    assert qg.caixa_object_fit({"x": 1, "y": 2, "w": 3, "h": 4}) == (1, 2, 3, 4)


def test_registro_exige_a_caixa_da_foto_com_1_px():
    # recorte de 2000x1000 com o alfa em (1000, 200, 1400, 1000): na página, (1372, 216, 432x864)
    certo = (1372.0, 216.0, 432.0, 864.0)
    fig = item("figura", "heroi", "frente", *certo, formato="png", origem="composicao", alfa_bbox=[1000, 200, 1400, 1000],
               ancora={"relacao": "registro", "alvo": "foto", "caixa": [292, 0, 2160, 1080], "registro": {"img": [2000, 1000]}})
    dom = lambda dx=0.0, **kw: [dict({"id": "figura", "x": certo[0] + dx, "y": certo[1], "w": certo[2], "h": certo[3]}, **kw)]  # noqa: E731
    alvos = {"foto": FOTO}
    f, _ = roda(plano(pagina([fig], alvos=alvos, dom=dom())))
    assert not com(f, "registro"), f
    f, _ = roda(plano(pagina([fig], alvos=alvos, dom=dom(0.8))))
    assert not com(f, "registro"), f
    f, _ = roda(plano(pagina([fig], alvos=alvos, dom=dom(2.0))))
    assert len(com(f, "registro: desenhado em")) == 1, f
    errado = json.loads(json.dumps(fig)); errado["ancora"]["caixa"] = [295, 0, 2160, 1080]
    f, _ = roda(plano(pagina([errado], alvos=alvos, dom=dom())))
    assert len(com(f, "a caixa calculada pelo render")) == 1, f
    f, _ = roda(plano(pagina([fig], alvos={"pagina": {"x": 0, "y": 0, "w": 1920, "h": 1080}}, dom=dom())))  # sem foto medida
    assert com(f, "não foi medido"), f
    # inverso: a mesma figura com âncora alinha (legado) não passa pela regra
    leg = dict(fig, ancora={"relacao": "alinha"})
    f, _ = roda(plano(pagina([leg], alvos=alvos, dom=dom(2.0))))
    assert not com(f, "registro"), f


# ------------------------------------------------------------------------------------------------- cor da marca
KIT_COR = {"receitas": [{"id": "r1", "paleta": {"marca": "#F26B1D"}}], "marca": {"cor_primaria": "#F26B1D"}}


def test_acabamento_na_cor_da_marca_forte_avisa():
    g = lambda cor, op, papel="acabamento": item("eco", papel, "atras", grafismo={"tipo": "eco", "params": {"cor": cor}},  # noqa: E731
                                                 efeito={"opacidade": op})
    for cor, op, avisa in (("marca", 0.46, True), ("#f26b1d", 0.72, True), ("marca", 0.24, False), ("texto", 1, False),
                           ("apoio", 0.46, False)):
        _, a = roda(plano(pagina([g(cor, op)])), kit=KIT_COR)
        assert bool(com(a, "na cor da marca")) == avisa, (cor, op, a)
    _, a = roda(plano(pagina([g("marca", 1, "heroi")])), kit=KIT_COR)    # inverso: herói na cor da marca (legado)
    assert not com(a, "na cor da marca"), a


# ------------------------------------------------------------------------------------------------- máscara da tinta
def test_mascara_usa_o_png_do_svg_de_acabamento():
    from PIL import Image
    im = Image.new("RGBA", (400, 100), (0, 0, 0, 0))
    im.paste((255, 255, 255, 255), (0, 0, 200, 100))                  # tinta só na metade esquerda
    (PASTA / "cache").mkdir(exist_ok=True); im.save(PASTA / "cache" / "malha.png")
    linha = {"classe": "corpo", "x": 1450, "y": 520, "w": 300, "h": 40, "texto": "texto à direita"}
    malha = item("malha", "acabamento", "frente", x=1000, y=500, w=800, h=200, uso="cache/malha.png")
    f, _ = roda(plano(pagina([malha], [linha])))
    assert not f, f                                                  # a tinta real não chega ao texto
    f, _ = roda(plano(pagina([dict(malha, uso=None)], [linha])))
    assert com(f, "cobre corpo"), f                                  # sem o PNG, a caixa cheia cobre
    f, _ = roda(plano(pagina([dict(malha, papel="heroi")], [linha])))
    assert com(f, "cobre corpo"), f                                  # inverso: svg de herói continua caixa cheia
    m, _, _ = qg.mascara(malha, PASTA)
    # o caminho vem do plano (dado): `uso` que sai da pasta do kit não é lido, fica a caixa cheia
    assert qg._png_do_svg(dict(malha, uso="../fora.png"), PASTA) is None
    assert m.shape == (200, 800) and m[:, :396].all() and not m[:, 404:].any(), (m.shape, m[:, :396].mean(), m[:, 404:].mean())


# ------------------------------------------------------------------------------------------------- derivado não é solto
def test_derivado_nao_e_solto():
    alvos = {"pagina": {"x": 0, "y": 0, "w": 1920, "h": 1080}, "margem": {"x": 96, "y": 96, "w": 1728, "h": 888},
             "titulo": {"x": 96, "y": 200, "w": 600, "h": 100}}
    solto = item("s", "apoio", "frente", x=1301, y=703, w=97, h=55)
    _, a = roda(plano(pagina([solto], alvos=alvos)))
    assert com(a, "solto"), a
    _, a = roda(plano(pagina([dict(solto, papel="acabamento", derivado_de="pai")], alvos=alvos)))
    assert not com(a, "solto"), a


def test_plano_sem_campo_novo_da_o_mesmo_resultado_com_e_sem_kit():
    """Inverso geral: o kit passado ao checar_plano só pesa nas regras novas; num plano legado, com ou sem kit, igual."""
    pl = plano(pagina([item("h", "heroi", x=0, y=0, w=400, h=400), item("a", "apoio", x=100, y=100, w=400, h=400)], [CORPO]))
    assert roda(pl) == roda(pl, kit=KIT_COR)


if __name__ == "__main__":
    falhou = 0
    try:
        for nome, fn in list(globals().items()):
            if nome.startswith("test_"):
                try:
                    fn(); print("ok  ", nome)
                except AssertionError as e:
                    falhou += 1; print("FALHOU", nome, str(e)[:600])
    finally:
        shutil.rmtree(PASTA, ignore_errors=True)
    print("PROVAS:", "VERDES" if not falhou else f"{falhou} FALHA(S)")
    sys.exit(1 if falhou else 0)

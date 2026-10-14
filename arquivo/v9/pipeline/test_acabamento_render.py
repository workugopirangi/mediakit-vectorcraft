#!/usr/bin/env python3
"""
test_acabamento_render.py: provas do lado do render da camada de acabamento (mk-2.1, references/10-acabamento.md), sem
Chromium. Cada regra nova tem a prova e um MUTANTE: a regra quebrada de propósito (código trocado ou entrada errada) e a
prova tem de acusar. A prova ponta a ponta é o test_acabamento_prova.py (kit fictício renderizado); a do PDF, o
test_prova_pdf.py.

  ~/.venvs/mediakit/bin/python pipeline/test_acabamento_render.py [nome ...]

O legado é conferido contra o código do commit ANTES da camada (COMMIT_LEGADO, lido do git): o mesmo item sem campo novo
tem de sair byte a byte igual. Sai com 1 se algum teste falhar.
"""
import contextlib, hashlib, importlib.util, json, math, shutil, subprocess, sys, tempfile, time, types
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import camadas, composicao, encaixes, render  # noqa: E402

COMMIT_LEGADO = "8492325"     # main antes do lado do render da camada de acabamento
KIT = AQUI.parent / "exemplos" / "acabamento-prova"
BASE = Path(tempfile.gettempdir()) / f"mk-acabamento-render-{hashlib.sha1(str(AQUI).encode()).hexdigest()[:8]}"


def teste(fn):
    fn._teste = True
    return fn


def log(*a):
    print("   ", *a, flush=True)


def acusa(prova, *args):
    """A prova tem de falhar (AssertionError) com a regra quebrada: devolve a mensagem que ela deu."""
    try:
        prova(*args)
    except AssertionError as e:
        return str(e)[:160]
    raise AssertionError(f"o mutante passou despercebido por {prova.__name__}")


@contextlib.contextmanager
def trocado(modulo, nome, valor):
    velho = getattr(modulo, nome)
    setattr(modulo, nome, valor)
    try:
        yield
    finally:
        setattr(modulo, nome, velho)


def modulo_legado(nome):
    """O módulo `nome` do pipeline no COMMIT_LEGADO, carregado à parte (os imports dele usam os módulos vivos)."""
    src = subprocess.run(["git", "show", f"{COMMIT_LEGADO}:./{nome}.py"], capture_output=True, text=True, check=True,
                         cwd=str(AQUI)).stdout
    mod = types.ModuleType(f"{nome}_legado")
    mod.__file__ = str(AQUI / f"{nome}.py")
    exec(compile(src, f"{nome}_legado.py", "exec"), mod.__dict__)
    return mod


# ================================================================================================= composição
def prova_atribuidos(ent, esperado_efeito):
    a = composicao.atribuidos(ent, 1, ["selo"])
    assert a[0].get("efeito") == esperado_efeito, f"efeito não seguiu para o atribuído: {a[0].get('efeito')}"
    assert a[0].get("motivo") == "lua" and a[0].get("recurso") == "r1", (a[0].get("motivo"), a[0].get("recurso"))
    g = a[1]["grafismo"]["params"]
    assert g.get("esmaecer") == {"direcao": "cima", "passos": 5, "minimo": 0.06}, f"esmaecer não foi ao gerador: {g}"


@teste
def atribuidos_levam_efeito_motivo_recurso_e_esmaecer():
    ef = {"opacidade": 0.24, "blend": "multiply"}
    ent = {"elementos": [
        {"id": "selo", "papel": "acabamento", "funcao": "acabamento", "efeito": ef, "motivo": "lua", "recurso": "r1",
         "ancora": {"relacao": "alinha", "x": "esq=margem.esq", "y": "topo=margem.topo"}, "escala": {"altura": "1/4p"}},
        {"id": "malha", "grafismo": {"tipo": "malha"}, "papel": "acabamento", "funcao": "acabamento",
         "efeito": {"esmaecer": {"direcao": "cima", "passos": 5, "minimo": 0.06}},
         "ancora": {"relacao": "alinha", "x": "esq=margem.esq", "y": "topo=margem.topo"}, "escala": {"largura": "1p"}}]}
    prova_atribuidos(ent, ef)
    # legado: sem campo novo, o atribuído não ganha chave nenhuma
    leg = composicao.atribuidos({"elementos": [{"id": "x", "papel": "heroi", "funcao": "foco", "ancora": {}}]}, 1, ["x"])
    assert not {"efeito", "motivo", "recurso"} & set(leg[0]), leg[0]
    with trocado(composicao, "EFEITO_ITEM", ()):
        m = acusa(prova_atribuidos, ent, ef)
    log(f"efeito, motivo e recurso seguem ao atribuído; esmaecer vai a params do grafismo; mutante (EFEITO_ITEM vazio): {m}")


FOTO = {"x": 0.0, "y": 0.0, "w": 1920.0, "h": 1080.0, "img": {"nat_w": 1920, "nat_h": 1280, "fit": "cover", "pos": "50% 35%"}}
BBOX_FIG = (1291, 448, 1533, 1280)


def prova_registro(item):
    # cover de 1920×1280 em 1920×1080: escala 1, sobra 200 px na altura, 35% dela acima: a imagem começa em y = -70
    assert item["ancora"]["caixa"] == [0.0, -70.0, 1920.0, 1280.0], item["ancora"]["caixa"]
    assert (item["x"], item["y"], item["w"], item["h"]) == (1291.0, 378.0, 242.0, 832.0), (item["x"], item["y"], item["w"], item["h"])
    assert item["recorte"] == [1291.0, 378.0, 1533.0, 1080.0], f"o pedaço abaixo da foto não foi cortado: {item.get('recorte')}"


@teste
def registro_pela_conta_do_object_fit():
    a = {"id": "fig", "papel": "heroi", "camada": "frente", "ancora": {"relacao": "registro", "alvo": "foto"},
         "tinta_bbox": BBOX_FIG}
    med = {"w": 1920, "h": 1080, "alvos": {"foto": FOTO}}
    it = composicao.resolver_itens(a, (1920, 1280, BBOX_FIG), med)[0]
    prova_registro(it)
    assert composicao.conferir(it, {"foto": FOTO}, 1920, 1080) == [], "registro não confere contra os mesmos alvos"
    movida = dict(FOTO, img=dict(FOTO["img"], pos="50% 50%"))
    desvios = composicao.conferir(it, {"foto": movida}, 1920, 1080)
    assert desvios, "a foto mudou de posição e o registro conferiu igual"
    # proporção diferente da foto: erro da âncora (o recorte não é da própria foto)
    try:
        composicao.resolver_itens(a, (700, 900, (103, 0, 598, 884)), med)
        raise AssertionError("PNG 700×900 numa foto 1920×1280 passou no registro")
    except composicao.ErroComposicao as e:
        prop = str(e)
    # html: o recorte vira clip-path inset na caixa do nó
    h = camadas.html_item(it, {}, src="data:x")
    assert "clip-path:inset(0px 0px 130px 0px)" in h, h[-160:]      # o item vai a 1210; a foto acaba em 1080
    # mutante: a conta ignora o object-position (centro): o item sai 30 px abaixo e a prova acusa
    velho = composicao._pos_objeto
    with trocado(composicao, "_pos_objeto", lambda pos, lx, ly: velho("50% 50%", lx, ly)):
        m = acusa(prova_registro, composicao.resolver_itens(a, (1920, 1280, BBOX_FIG), med)[0])
    log(f"caixa da imagem [0, -70, 1920, 1280], item (1291, 378, 242×832), recorte até a base da foto; conferir acusa "
        f"foto movida ({len(desvios)} desvio(s)); proporção errada: {prop[:90]}; mutante: {m}")
    erros = composicao.validar({"publico": {"elementos": [{"id": "fig", "papel": "heroi", "funcao": "profundidade",
                                                           "grafismo": {"tipo": "eco"}, "ancora": {"relacao": "registro", "alvo": "foto"}}]}},
                               ["fig"])
    assert any("não grafismo" in e for e in erros), erros


# ================================================================================================= html do nó
ITEM = {"id": "selo", "papel": "heroi", "camada": "frente", "encaixe": "composicao", "x": 100.0, "y": 200.0, "w": 300.0,
        "h": 240.0, "rot": 0}


@teste
def legado_sai_byte_a_byte_igual():
    """html_item e css_receita sem campo novo: a mesma string do código de antes (COMMIT_LEGADO)."""
    cam0, ren0 = modulo_legado("camadas"), modulo_legado("render")
    casos = [
        (dict(ITEM), {"opacidade": 0.8, "blend": "multiply"}, dict(src="data:a")),
        (dict(ITEM, rot=12, espelhar=True), {}, dict(src="data:b", dx=10, dy=5)),
        (dict(ITEM), {}, dict(src="data:c", cor="#112233")),
        (dict(ITEM, papel="pattern"), {"escala_tile": 200}, dict(src="data:d")),
        (dict(ITEM, papel="estrutura"), {"blend": "screen"}, dict(svg="<svg></svg>")),
    ]
    for it, el, kw in casos:
        assert camadas.html_item(it, el, **kw) == cam0.html_item(it, el, **kw), f"html_item mudou para o legado: {it}"
    k = json.loads((AQUI.parent / "exemplos" / "receitas-teste" / "mediakit.json").read_text(encoding="utf-8"))
    for r in k["receitas"]:
        assert render.css_receita(r) == ren0.css_receita(r), f"css_receita mudou para a receita {r['id']}"
    assert not render.declara_acabamento(k), "receitas-teste não declara acabamento"
    kv = json.loads((AQUI.parent / "exemplos" / "travessia-da-lua" / "mediakit.json").read_text(encoding="utf-8"))
    assert not render.declara_acabamento(kv)
    # mutante: um campo novo vazando no legado (blend em todo svg) e a prova acusa
    def vaza(it, el, **kw):
        return camadas.html_item(it, el, **kw).replace("opacity:1.0\">", "opacity:1.0;mix-blend-mode:normal\">")

    def prova_vazamento():
        it, el, kw = casos[4]
        assert vaza(it, el, **kw) == cam0.html_item(it, el, **kw), "o svg do legado ganhou blend"
    m = acusa(prova_vazamento)
    log(f"{len(casos)} nós e {len(k['receitas'])} receitas iguais ao {COMMIT_LEGADO}; receitas-teste e travessia-da-lua sem "
        f"acabamento; mutante: {m}")


def estilo(h):
    import re
    m = re.search(r'style="([^"]*)"', h)
    return dict(d.split(":", 1) for d in m.group(1).split(";") if ":" in d)


def prova_efeito(h):
    st = estilo(h)
    assert st.get("opacity") == "0.24", st.get("opacity")
    assert st.get("mix-blend-mode") == "multiply", st.get("mix-blend-mode")


@teste
def efeito_vence_o_elemento_e_fica_no_no():
    it = dict(ITEM, efeito={"opacidade": 0.24, "blend": "multiply"})
    el = {"opacidade": 0.8, "blend": "screen"}
    prova_efeito(camadas.html_item(it, el, src="data:x"))
    sv = camadas.html_item(dict(it, papel="acabamento"), el, svg="<svg></svg>")
    prova_efeito(sv)
    assert "color:var(--texto)" in sv, "acabamento em svg sem a cor do texto"
    # vocabulário fechado: valor fora não vira CSS (aspa, url, ponto e vírgula)
    ruim = dict(ITEM, efeito={"opacidade": "1;background:url(x)", "blend": "normal;x:y", "mascara": "url(#m)"})
    h = camadas.html_item(ruim, {}, src="data:x")
    assert "url(x)" not in h and "x:y" not in h and "url(#m)" not in h and "clip-path" not in h, h
    av = []
    camadas._efeito_valido(ruim["efeito"], av, "selo")
    assert len(av) == 3, av
    # mutante: o elemento vence o efeito (precedência invertida)
    velho = camadas._efeito_valido
    with trocado(camadas, "_efeito_valido", lambda ef, *a: {}):
        m = acusa(prova_efeito, camadas.html_item(it, el, src="data:x"))
    log(f"opacity 0.24 e multiply do efeito no próprio nó (img e svg); valor fora do vocabulário vira aviso ({len(av)}), "
        f"nunca CSS; mutante (efeito ignorado): {m}")
    assert camadas._efeito_valido is velho


def prova_mascaras(f):
    w, h = 300.0, 240.0
    d = f("diagonal", w, h)
    assert d.startswith("polygon(") and f"{camadas._num(h * math.tan(math.radians(12)))}px 0px" in d, d
    assert f("chanfro", w, h).startswith("polygon(") and "0px 120px" in f("chanfro", w, h), f("chanfro", w, h)
    # espelhado (scaleX(-1) no nó): a forma sai espelhada para o corte cair no mesmo canto da página
    dx = camadas._num(w - h * math.tan(math.radians(12)))
    assert f("diagonal", w, h, True).startswith(f"polygon({dx}px 0px,0px 0px,"), f("diagonal", w, h, True)
    assert f("circulo", w, h, True) == f("circulo", w, h)
    assert f("circulo", w, h) == "circle(120px at 150px 120px)", f("circulo", w, h)
    ab = f("arco-base", w, h)
    assert ab.startswith("polygon(0 0,100% 0,") and ab.count("px") == 50, ab[:80]
    assert f("janela", w, h) == "inset(0 round 150px 150px 0 0)", f("janela", w, h)
    assert f("nenhuma", w, h) is None and f("url(x)", w, h) is None


@teste
def mascaras_viram_clip_path_vetorial():
    prova_mascaras(camadas.clip_mascara)
    h = camadas.html_item(dict(ITEM, efeito={"mascara": "chanfro"}), {}, src="data:x")
    assert "clip-path:polygon(" in h, h
    m = acusa(prova_mascaras, lambda nome, w, h, e=False: "inset(0)" if nome == "circulo" else camadas.clip_mascara(nome, w, h, e))
    m2 = acusa(prova_mascaras, lambda nome, w, h, e=False: camadas.clip_mascara(nome, w, h))      # ignora o espelho
    log(f"diagonal e chanfro no ângulo do kit (12°), circulo, arco-base (24 segmentos) e janela (inset com raio); "
        f"mutante (círculo virou inset): {m}; mutante (espelho ignorado): {m2}")


def prova_cruza(itens, medidas):
    erros = [[]]
    camadas.Elementos._cruzar(types.SimpleNamespace(els={"medalha": {"formato": "png"}}), itens, medidas, erros)
    it = itens[0][0]
    assert not erros[0], erros
    assert it.get("cruza") == {"alvo": "titulo", "corte": "cy", "y": 300.0, "corte_px": 100.0}, it.get("cruza")
    atras = camadas.html_item(it, {}, src="data:m", corte=("atras", it["cruza"]["corte_px"]))
    frente = camadas.html_item(it, {}, src="data:m", corte=("frente", it["cruza"]["corte_px"]))
    assert 'data-corte="atras"' in atras and "el-atras" in atras and 'data-camada="atras"' in atras, atras
    assert 'data-corte="frente"' in frente and "el-frente" in frente, frente
    assert "clip-path:inset(0 0 140px 0)" in atras and "clip-path:inset(100px 0 0 0)" in frente, (atras[-60:], frente[-60:])
    assert 'src="data:m"' in atras and 'src="data:m"' in frente


@teste
def cruza_parte_na_linha_medida():
    medidas = [{"alvos": {"titulo": {"x": 0, "y": 250, "w": 900, "h": 100, "linhas": [{"x": 0, "y": 250, "w": 900, "h": 100,
                                                                                       "linha_base": 330, "cap": 262}]}}}]
    novo = lambda: [[dict(ITEM, id="medalha", efeito={"cruza": {"alvo": "titulo", "corte": "cy"}})]]  # noqa: E731
    prova_cruza(novo(), medidas)
    # alvo ausente e linha fora do elemento: erro da âncora, nunca corte inventado
    erros = [[]]
    sem = novo()
    camadas.Elementos._cruzar(types.SimpleNamespace(els={"medalha": {"formato": "png"}}), sem, [{"alvos": {}}], erros)
    assert erros[0] and "cruza" in erros[0][0] and "cruza" not in sem[0][0], erros
    erros = [[]]
    longe = [[dict(ITEM, id="medalha", y=600.0, efeito={"cruza": {"alvo": "titulo", "corte": "cy"}})]]
    camadas.Elementos._cruzar(types.SimpleNamespace(els={"medalha": {"formato": "png"}}), longe, medidas, erros)
    assert erros[0] and "não cruza" in erros[0][0], erros
    # mutante: o corte medido na base do título em vez do eixo pedido
    velho = composicao.valor_alvo
    with trocado(composicao, "valor_alvo", lambda al, n, l, b: velho(al, n, l, "linha_base")):
        m = acusa(prova_cruza, novo(), medidas)
    log(f"corte no cy do título (y 300, 100 px dentro do nó): metade de cima na camada atras, de baixo na frente, mesmo "
        f"data URI; alvo ausente e linha fora viram erro da âncora; mutante (corte na linha de base): {m}")


def prova_ordem(f):
    pai = dict(ITEM, id="selo")
    res = [dict(ITEM, id="eco", papel="acabamento"), pai, dict(ITEM, id="selo-sombra", papel="acabamento", derivado_de="selo"),
           dict(ITEM, id="selo-reflexo", papel="acabamento", derivado_de="selo"), dict(ITEM, id="pat", papel="pattern")]
    ids = [it["id"] for it in f(res)]
    assert ids == ["pat", "selo-sombra", "selo-reflexo", "selo", "eco"], ids


@teste
def derivados_pintam_logo_antes_do_pai():
    prova_ordem(camadas.ordem_de_pintura)
    legado = [dict(ITEM, id=i, papel=p) for i, p in (("a", "apoio"), ("b", "heroi"), ("c", "pattern"), ("d", "constante"))]
    chave = lambda it: (it["papel"] != "pattern", encaixes.ORDEM.get(it["papel"], 9))  # noqa: E731
    assert camadas.ordem_de_pintura(legado) == sorted(legado, key=chave), "a ordem do legado mudou"
    m = acusa(prova_ordem, lambda res: sorted(res, key=lambda it: (it["papel"] != "pattern", encaixes.ORDEM.get(it["papel"], 9))))
    log(f"sombra e reflexo entram logo antes do pai; sem derivado a ordem é a de antes; mutante (ordem antiga): {m}")


# ================================================================================================= encaixes
def prova_nao_ocupa(f):
    assert f({"papel": "acabamento", "efeito": {"opacidade": 0.12}}) is True
    assert f({"papel": "acabamento", "efeito": {"opacidade": 0.24}}) is True
    assert f({"papel": "acabamento", "efeito": {"opacidade": 0.46}}) is False
    assert f({"papel": "heroi", "efeito": {"opacidade": 0.12}}) is False
    assert f({"papel": "acabamento"}) is False


@teste
def acabamento_por_ultimo_e_translucido_nao_ocupa():
    assert encaixes.ORDEM["acabamento"] > max(v for k, v in encaixes.ORDEM.items() if k != "acabamento")
    prova_nao_ocupa(encaixes.nao_ocupa)
    m = acusa(prova_nao_ocupa, lambda a: False)
    # pela resolução: um acabamento a .12 ancorado não entra em `ocupados` (o herói que vem do catálogo não desvia dele)
    med = {"w": 1920, "h": 1080, "alvos": {"pagina": {"x": 0, "y": 0, "w": 1920, "h": 1080},
                                           "margem": {"x": 96, "y": 96, "w": 1728, "h": 888}, "colunas": []}}
    a = {"id": "veu", "papel": "acabamento", "funcao": "acabamento", "camada": "atras", "efeito": {"opacidade": 0.12},
         "ancora": {"relacao": "alinha", "x": "esq=pagina.esq", "y": "topo=pagina.topo"}, "escala": {"largura": "1p"}}
    res = encaixes.resolver([a], "prova", {"prova": []}, dict(med), {"veu": (1920, 1080, None)})
    assert res and res[0]["papel"] == "acabamento", res
    log(f"acabamento resolvido por último (ORDEM {encaixes.ORDEM['acabamento']}); opacidade até .24 não ocupa; "
        f"mutante (sempre ocupa): {m}")


# ================================================================================================= render.py
def prova_grao_luz(f):
    html = '<section class="pagina capa">a</section><section class="pagina">b</section>'
    pags = [{"tipo": "capa", "variante": "b", "_acab": {"grao": "leve", "luz": "esq"}},
            {"tipo": "prova", "_acab": {"grao": 'leve" onload="x', "luz": "dir"}}]
    out = f(html, pags, None)
    abre = [s.split(">", 1)[0] for s in out.split("<section")[1:]]
    assert 'data-grao="leve"' in abre[0] and 'data-luz="esq"' in abre[0], abre[0]
    assert "onload" not in out and 'data-luz="dir"' in abre[1] and "data-grao" not in abre[1], abre[1]


@teste
def render_grao_luz_37_e_lettering():
    prova_grao_luz(render.injetar_camadas)
    # sem _acab: a section sai como antes
    leg = render.injetar_camadas('<section class="pagina">x</section>', [{"tipo": "prova"}], None)
    assert leg == '<section data-tipo="prova" data-variante="a" class="pagina">x</section>', leg
    kit = json.loads((KIT / "mediakit.json").read_text(encoding="utf-8"))
    assert render.declara_acabamento(kit)
    ac = [render.acabamento_da_pagina(kit, {"tipo": t, "variante": v}) for t, v in (("capa", "b"), ("publico", "a"))]
    assert ac[0].get("grao") == "leve" and ac[1].get("luz") == "dir", ac
    r = dict(kit["receitas"][0], fontes=dict(kit["receitas"][0]["fontes"], lettering="Antonio"))
    assert '--fonte-lettering: "Antonio", "Anton", "DM Sans"' in render.css_receita(r), render.css_receita(r)[:200]
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "Anton.ttf").write_bytes(b"x")
        (Path(tmp) / "DM Sans.ttf").write_bytes(b"x")
        assert render.familias_faltando(r, Path(tmp)) == ["Antonio"], render.familias_faltando(r, Path(tmp))
    k2 = dict(kit, receitas=[dict(r, fontes=dict(r["fontes"], lettering='Anton"; } body{x:url(y)'))])
    assert any("lettering" in e for e in render.valores_fora_do_formato(k2)), "lettering com aspa passou para o CSS"
    m = acusa(prova_grao_luz, lambda h, p, f: h)
    log(f"data-grao e data-luz só do vocabulário (aspa barrada); section do legado igual; 37 só com acabamento declarado; "
        f"lettering vira token, conta em familias_faltando e no filtro de formato; mutante (sem marcação): {m}")


# ================================================================================================= textura
def prova_textura(rel, uri, tamanho, larg_uso):
    assert rel.endswith(".jpg") and uri.startswith("data:image/jpeg;base64,"), (rel, uri[:30])
    assert tamanho[0] == min(1920, int(math.ceil(larg_uso / 16.0) * 16)), f"textura a {tamanho[0]} px para uso de {larg_uso}"


@teste
def textura_jpeg_a_1x_e_blend_pela_area():
    from PIL import Image
    import numpy as np
    BASE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=BASE) as tmp:
        tmp = Path(tmp)
        rng = np.random.default_rng(3)
        Image.fromarray(rng.integers(0, 255, (1080, 1920, 3), dtype=np.uint8), "RGB").save(tmp / "tex.png")
        aberta = Image.fromarray(rng.integers(0, 255, (1080, 1920, 4), dtype=np.uint8), "RGBA")
        aberta.save(tmp / "tex-alfa.png")
        assert camadas.sem_alfa(tmp / "tex.png") and not camadas.sem_alfa(tmp / "tex-alfa.png")
        rep = {"avisos": []}
        k = {"elementos": [{"id": "tex", "papel": "acabamento", "tipo": "textura", "formato": "png", "arquivo": "tex.png"}]}
        el = camadas.carregar(k, tmp, rep)["tex"]
        assert el.get("textura") and not rep["avisos"], (el.get("textura"), rep["avisos"])
        rel, destino, cor = camadas.preparar_uso(el, 960.0, tmp / "cache", tmp, [])
        largura = Image.open(destino).size[0]
        prova_textura(rel, camadas._data_uri(destino), Image.open(destino).size, 960.0)
        # blend pela área: papel, escuro, foto
        fake = types.SimpleNamespace()
        it = dict(ITEM, papel="acabamento", x=0.0, y=0.0, w=1920.0, h=1080.0, camada="atras")
        med = {"alvos": {"foto": {"x": 960, "y": 0, "w": 960, "h": 1080}}}
        bt = lambda it, med, fundo: camadas.Elementos._blend_textura(fake, it, el, med, fundo)  # noqa: E731
        assert bt(it, {"alvos": {}}, "papel") == "multiply" and bt(it, {"alvos": {}}, "escuro") == "screen"
        assert bt(dict(it, x=960.0, w=960.0), med, "papel") == "soft-light"
        h = camadas.html_item(it, el, src="data:t", blend_padrao="screen")
        assert "mix-blend-mode:screen" in h and "mix-blend-mode:multiply" in camadas.html_item(
            dict(it, efeito={"blend": "multiply"}), el, src="data:t", blend_padrao="screen"), "o efeito não venceu o padrão"
        # mutante: textura preparada como PNG a 2x (o caminho de todo elemento)
        el2 = dict(el, textura=False, alfa_bbox=(0, 0, 1920, 1080))
        rel2, dest2, _ = camadas.preparar_uso(el2, 960.0, tmp / "cache", tmp, [])
        m = acusa(prova_textura, rel2, camadas._data_uri(dest2), Image.open(dest2).size, 960.0)
    log(f"textura opaca: JPEG q80 a 1x ({largura} px para 960 de uso), sem aviso de PNG sem alfa; "
        f"blend multiply no papel, screen no escuro, soft-light sobre foto, efeito vence; mutante (PNG a 2x): {m}")


# ================================================================================================= sombra e reflexo
def clone_do_kit():
    d = BASE / "kit"
    if d.exists():
        shutil.rmtree(d)
    d.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cp", "-cR", str(KIT), str(d)], check=True)
    shutil.rmtree(d / "saida", ignore_errors=True)
    return d


def derivados(els_obj, margem=None):
    it = dict(ITEM, id="selo-objeto", x=1464.0, y=592.0, w=360.0, h=360.0, efeito={"sombra": "contato", "reflexo": "piso"})
    itens, erros, avisos = [[it]], [[]], [[]]
    pagina = {"n": 3, "rotulo": "cota:a", "tipo": "cota", "_rotulos": {"cota", "cota:a"}}
    ctx = trocado(camadas, "MARGEM_SOMBRA", (lambda w: margem)) if margem is not None else contextlib.nullcontext()
    with ctx:
        els_obj._derivados(itens, [pagina], "horizontal", erros, avisos)
    return it, {d["id"]: d for d in itens[0][1:]}, erros[0]


def prova_derivados(els_obj, it, ds, erros):
    assert not erros, erros
    assert set(ds) == {"selo-objeto-reflexo", "selo-objeto-sombra"}, list(ds)
    el = els_obj.els["selo-objeto"]
    bb, tb = el["alfa_bbox"], el["tinta_bbox"]
    s = it["w"] / (bb[2] - bb[0])
    base_tinta = it["y"] + (tb[3] - bb[1]) * s
    r = ds["selo-objeto-reflexo"]
    dr = els_obj.els[r["el_id"]]
    assert abs((r["y"] - dr["alfa_bbox"][1] * s) - base_tinta) < 0.2, f"o reflexo não encosta na base da tinta ({r['y']} vs {base_tinta:.1f})"
    for d in ds.values():
        assert d["derivado_de"] == "selo-objeto" and d["papel"] == "acabamento" and d["camada"] == "frente", d
    # a sombra não pode sair cortada reta na borda: o alfa da última coluna do PNG tem de ter morrido
    from PIL import Image
    import numpy as np
    a = np.asarray(Image.open(els_obj.els[ds["selo-objeto-sombra"]["el_id"]]["caminho"]).convert("RGBA"))[..., 3]
    assert a[:, -1].max() <= 8 and a[:, 0].max() <= 8, f"sombra cortada na borda do canvas (alfa {a[:, 0].max()} à esquerda, {a[:, -1].max()} à direita)"


@teste
def sombra_e_reflexo_derivados_na_conta_do_pai():
    kit = clone_do_kit()
    k = json.loads((kit / "mediakit.json").read_text(encoding="utf-8"))
    e = camadas.Elementos(k, kit, {"avisos": []}, kit / "fontes")
    it, ds, erros = derivados(e)
    prova_derivados(e, it, ds, erros)
    s, r = ds["selo-objeto-sombra"], ds["selo-objeto-reflexo"]
    # mutante: sem a margem do canvas, o tratar.sombra corta a sombra reta na borda direita (o defeito medido na cota)
    e2 = camadas.Elementos(k, kit, {"avisos": []}, kit / "fontes")
    shutil.rmtree(kit / "saida" / "cache-elementos" / "derivados", ignore_errors=True)
    m = acusa(prova_derivados, e2, *derivados(e2, margem=0))
    shutil.rmtree(BASE, ignore_errors=True)
    log(f"reflexo com o topo na base da tinta ({r['y']:.1f}), sombra ({s['x']:.0f}, {s['y']:.0f}, {s['w']:.0f}×{s['h']:.0f}) "
        f"sem corte na borda; derivado_de, papel acabamento, camada do pai; mutante (sem margem): {m}")


# ================================================================================================= encaixes da frente G
def prova_regua_e_textos(medida, pede, ctxf):
    cat = {"vertical:capa": [{"id": "faixa-base", "papeis": ["constante"], "gerador": "faixa", "lado": "base"}],
           "vertical:contato": [{"id": "canto", "papeis": ["constante"], "gerador": "canto", "max": [150, 150]}]}
    fake = types.SimpleNamespace(catalogo=cat)
    at = [{"atribuidos": [{"id": "constante-regua-borda"}]}]
    m = medida(fake, "regua-borda", "constante-regua-borda", at, [{"rotulo": "vertical:capa"}], 1080)
    assert m == {"largura": 888}, f"régua de borda no vertical com faixa: {m} (pede 1080 - 2 margens)"
    m = medida(fake, "regua-borda", "constante-regua-borda", at, [{"rotulo": "vertical:contato"}], 1080)
    assert m == {"largura": 1080}, f"régua de borda no vertical sem faixa: {m} (pede a largura da página)"
    assert pede({"composicao": {"capa": {"elementos": [{"grafismo": {"tipo": "eco", "params": {"texto_de": "titulo"}}}]}}})
    assert not pede({"composicao": {"capa": {"elementos": [{"grafismo": {"tipo": "eco", "params": {"texto_de": "evento"}}}]}}})
    c = ctxf({"fontes": {"display": "Anton"}}, {"titulo": "TRAVESSIA DA LUA"})
    assert c["textos"] == {"titulo": "TRAVESSIA DA LUA"} and ctxf({"a": 1}, {}) == {"a": 1}, c


@teste
def encaixes_da_frente_g_regua_no_vertical_e_textos():
    prova_regua_e_textos(camadas.Elementos._medida_da_constante, camadas._pede_textos, camadas.contexto_com_textos)
    # mutante: a régua sem medida (o padrão do gerador, 1920, não cabe no vertical)
    velho = camadas.Elementos._medida_da_constante
    m = acusa(prova_regua_e_textos, lambda s, t, *a: {} if t == "regua-borda" else velho(s, t, *a), camadas._pede_textos,
              camadas.contexto_com_textos)
    m2 = acusa(prova_regua_e_textos, velho, lambda k: False, camadas.contexto_com_textos)
    log(f"regua-borda: 888 px no vertical com faixa, 1080 sem faixa; texto_de titulo/tese liga os textos da página no "
        f"ctx; mutante (régua sem medida): {m}; mutante (textos nunca pedidos): {m2}")


# ================================================================================================= chave do acabamento
def chaves_em_duas_pastas(chave_fn, tmp):
    """A chave do acabamento da frente com o MESMO grão em duas pastas de pipeline diferentes (o vivo e o congelado do
    golden), montada pelo Elementos._acabamento de verdade."""
    out = []
    for nome in ("pipeline-a", "outra/pipeline-b"):
        d = tmp / nome / "assets"
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(camadas.GRAO_TEMA, d / "grao.png")
        with trocado(camadas, "GRAO_TEMA", d / "grao.png"):
            ac = camadas.Elementos._acabamento(types.SimpleNamespace(pasta=tmp), {"grao": {"opacidade": 0.5, "blend": "soft-light",
                                                                                      "tamanho": "512px 512px"}}, None)
        out.append(chave_fn(ac))
    return out


def prova_chave_sem_caminho(chave_fn, tmp):
    a, b = chaves_em_duas_pastas(chave_fn, tmp)
    assert a == b, f"o mesmo grão em duas pastas deu chaves diferentes ({a} e {b}): o caminho entrou na conta"


@teste
def chave_do_acabamento_nao_depende_da_pasta():
    BASE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=BASE) as tmp:
        tmp = Path(tmp)
        prova_chave_sem_caminho(camadas.chave_acabamento, tmp)
        a = chaves_em_duas_pastas(camadas.chave_acabamento, tmp)[0]
        # o conteúdo continua contando: opacidade diferente, chave diferente
        with trocado(camadas, "GRAO_TEMA", tmp / "pipeline-a" / "assets" / "grao.png"):
            outra = camadas.chave_acabamento(camadas.Elementos._acabamento(
                types.SimpleNamespace(pasta=tmp), {"grao": {"opacidade": 0.3, "blend": "soft-light", "tamanho": "512px"}}, None))
        assert outra != a, "opacidade do grão diferente deu a mesma chave"
        # antes do conserto (código do COMMIT_LEGADO): a mesma prova acusa
        m = acusa(prova_chave_sem_caminho, modulo_legado("camadas").chave_acabamento, tmp)
    log(f"mesmo grão em duas pastas: chave {a} nas duas; opacidade diferente muda a chave; com a chave de "
        f"{COMMIT_LEGADO}: {m}")


# ================================================================================================= QA (integração R + Q)
def prova_sem_repeticao(chamar):
    """Falha que depende do kit (família proibida) e que o camadas.py já gravou no plano (composicao_erros, com kit=k):
    o qa.py não repete como `acabamento:`. Sem plano, ela sai pelo qa.py."""
    import qa
    recs = [{"id": f"r{i}", "familia": f, "referencia": "x", "principio": "o princípio do recurso", "rota": "codigo"}
            for i, f in enumerate(("tipografia-expressiva", "pattern-textura", "profundidade-3d", "tratamento-imagem"))]
    k = {"schema_version": "mk-2.0", "evento": {"nome": "Corrida Teste"},
         "direcao_criativa": {"recursos": recs, "nao_usa": ["pattern-textura"]},
         "composicao": {"capa": {"mensagem": "a capa", "acabamento": {"recursos": ["r1"], "porque": "o porquê da capa"}}}}
    falha = composicao.validar(k["composicao"], [], kit=k)
    assert falha and "pattern-textura" in falha[0], falha
    BASE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=BASE) as d:
        pasta = Path(d)
        (pasta / "saida").mkdir()
        (pasta / "saida" / "plano-elementos-r1.json").write_text(json.dumps({"paginas": [], "composicao_erros": falha}),
                                                                 encoding="utf-8")
        (pasta / "saida" / "render-report.json").write_text("{}", encoding="utf-8")
        qa.falhas.clear(); qa.avisos.clear()
        chamar(qa, pasta, k)
        repetidas = [f for f in qa.falhas if f.startswith("acabamento:") and "pattern-textura" in f]
        assert not repetidas, f"a falha do plano saiu de novo pelo qa.py: {repetidas}"


@teste
def qa_nao_repete_falha_que_o_plano_ja_traz():
    prova_sem_repeticao(lambda qa, pasta, k: qa.checar_acabamento(pasta, k))
    # mutante: o qa.py sem olhar o plano (o comportamento de antes da validação com o kit no camadas.py)
    import acabamento, qa
    def sem_plano(qa, pasta, k):
        for f in acabamento.validar(k)[0]:
            qa.F(f"acabamento: {f}")
    m = acusa(prova_sem_repeticao, sem_plano)
    log(f"falha de família proibida gravada no plano pelo camadas.py sai uma vez (pelo qa_geometria); mutante: {m}")


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
            print(f"FALHOU  {n}  ({time.time() - t0:.1f} s): {type(e).__name__}: {str(e)[:900]}", flush=True)
    print(f"\n{len(testes) - falhou} de {len(testes)} testes passaram")
    sys.exit(1 if falhou else 0)


if __name__ == "__main__":
    main()

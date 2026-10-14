#!/usr/bin/env python3
"""
test_acabamento_prova.py: a definição de pronto da mecânica da camada de acabamento (references/10-acabamento.md). Renderiza o
kit fictício exemplos/acabamento-prova (mk-2.1, uma página por efeito) e afirma, no HTML gerado, o que a mecânica tem de
produzir. Sem pytest.

  ~/.venvs/mediakit/bin/python pipeline/test_acabamento_prova.py

Ordem: 1) o kit valida no schema e nas regras do acabamento.py; 2) o render.py roda até o fim (--png --fontes, exit 0);
3) as afirmações dos efeitos, uma por efeito. Enquanto a mecânica não existe, as afirmações de efeito FALHAM e cada uma diz
o que faltou; as duas primeiras passam (é o que prova que a falha é a ausência do efeito, não schema nem render quebrado).
O kit é clonado por APFS (cp -c) numa pasta temporária fora do git; o HTML fica lá para inspeção (o caminho sai no log).
Sai com 1 se algum teste falhar.
"""
import hashlib, json, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import acabamento, composicao  # noqa: E402

PY = sys.executable
KIT = AQUI.parent / "exemplos" / "acabamento-prova"
BASE = Path(tempfile.gettempdir()) / f"mk-acabamento-prova-{hashlib.sha1(str(AQUI).encode()).hexdigest()[:8]}"
RECEITA = "r1"
ORDEM = ["capa", "divisor", "cota", "ativo_painel", "prova", "publico"]     # data-tipo das sections, na ordem de `paginas`
CHAVE_COMP = {"capa": "capa", "divisor": "divisor", "cota": "cota", "ativo_painel": "ativo", "prova": "prova", "publico": "publico"}
_RENDER = {}


def teste(fn):
    fn._teste = True
    return fn


def log(*a):
    print("   ", *a, flush=True)


def kit():
    return json.loads((KIT / "mediakit.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------- render (uma vez)
def render():
    """Clona o kit e roda o render uma vez por execução. Devolve {pasta, html, plano, saida, codigo}."""
    if _RENDER:
        return _RENDER
    if BASE.exists():
        shutil.rmtree(BASE)
    BASE.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cp", "-cR", str(KIT), str(BASE)], check=True)
    if (BASE / "saida").exists():
        shutil.rmtree(BASE / "saida")
    r = subprocess.run([PY, str(AQUI / "render.py"), str(BASE), "--png", "--fontes", str(BASE / "fontes")],
                       capture_output=True, text=True, cwd=str(AQUI))
    html_p = BASE / "saida" / "html" / f"kit-{RECEITA}.html"
    plano_p = BASE / "saida" / f"plano-elementos-{RECEITA}.json"
    _RENDER.update(pasta=BASE, codigo=r.returncode, saida=r.stdout + r.stderr,
                   html=html_p.read_text(encoding="utf-8") if html_p.exists() else None,
                   plano=json.loads(plano_p.read_text(encoding="utf-8")) if plano_p.exists() else None)
    return _RENDER


def secoes():
    """{data-tipo: html da section} do kit renderizado (falha se o render não chegou ao HTML)."""
    r = render()
    if r["codigo"] != 0 or not r["html"]:
        raise AssertionError(f"o render não chegou ao HTML (exit {r['codigo']}): {r['saida'][-600:]}")
    partes = re.split(r"(?=<section\b)", r["html"])
    out = {}
    for p in partes:
        m = re.match(r'<section\b[^>]*\bdata-tipo="([^"]+)"', p)
        if m:
            out.setdefault(m.group(1), p.split("</section>", 1)[0])
    return out


def estilo(tag):
    m = re.search(r'\bstyle="([^"]*)"', tag)
    out = {}
    for decl in (m.group(1) if m else "").split(";"):
        if ":" in decl:
            k, v = decl.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def nos(sec, prefixo):
    """Nós de elemento da section cujo data-elemento é `prefixo` ou começa por `prefixo-`: [{id, tag, estilo, src, dentro}].
    `dentro` = o conteúdo do nó até o primeiro </div> (o svg do grafismo)."""
    out = []
    for m in re.finditer(r'<(img|div)\b[^>]*\bdata-elemento="([^"]+)"[^>]*>', sec):
        eid = m.group(2)
        if eid != prefixo and not eid.startswith(prefixo + "-"):
            continue
        tag = m.group(0)
        src = re.search(r'\bsrc="([^"]*)"', tag)
        dentro = sec[m.end():].split("</div>", 1)[0] if m.group(1) == "div" else ""
        out.append({"id": eid, "tag": tag, "estilo": estilo(tag), "src": src.group(1) if src else None, "dentro": dentro})
    return out


def por_que_falta(eid):
    """Por que o nó `eid` não entrou, lido dos erros de âncora do plano. Grafismo que o grafismos.gerar ainda não conhece
    (eco, malha, hachura: os geradores vêm da frente G) vira "aguarda frente G", para a falha dizer de quem é a vez."""
    plano = render().get("plano") or {}
    erros = [e for pg in plano.get("paginas") or [] for e in pg.get("erros_composicao") or [] if eid in e]
    if any("desconhecido" in e for e in erros):
        return f"aguarda frente G ({erros[0][:150]})"
    return erros[0][:200] if erros else "sem erro registrado no plano"


def opacidade(v):
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------------------------------------- base: tem de passar
@teste
def kit_valida_no_schema_e_nas_regras():
    k = kit()
    assert k["schema_version"] == "mk-2.1"
    es = acabamento.erros_schema(k)
    assert es == [], es
    falhas, avisos = acabamento.validar(k)
    assert falhas == [] and avisos == [], (falhas, avisos)
    erros = composicao.validar(k["composicao"], [e["id"] for e in k["elementos"]], kit=k)
    assert erros == [], erros
    log(f"schema mk-2.1 sem erro; acabamento.validar e composicao.validar(kit=k) sem falha nem aviso; "
        f"{len(k['composicao'])} páginas compostas, {len(k['direcao_criativa']['recursos'])} recursos")


@teste
def render_roda_ate_o_fim():
    r = render()
    assert r["codigo"] == 0, f"render saiu com {r['codigo']}: {r['saida'][-1500:]}"
    assert r["html"] and r["plano"], "render sem HTML ou sem plano"
    tipos = re.findall(r'<section\b[^>]*\bdata-tipo="([^"]+)"', r["html"])
    assert tipos == ORDEM, tipos
    # os alvos de que os efeitos dependem existem em cada página: a falha de um efeito nunca é alvo ausente
    precisa = {"capa": ("titulo", "foto"), "divisor": ("titulo",), "cota": ("foto", "preco"), "ativo_painel": ("foto", "corpo"),
               "prova": ("numero", "titulo"), "publico": ("foto", "titulo")}
    for pg, tipo in zip(r["plano"]["paginas"], ORDEM):
        falta = [a for a in precisa[tipo] if a not in (pg.get("alvos") or {})]
        assert not falta, f"p.{pg['n']} {tipo}: sem o alvo {falta} (o kit de prova tem de dar a cada efeito o alvo dele)"
    erros = [e for pg in r["plano"]["paginas"] for e in pg.get("erros_composicao") or []]
    log(f"render exit 0, 6 páginas na ordem pedida; HTML em {BASE / 'saida' / 'html' / f'kit-{RECEITA}.html'}")
    for e in erros:
        log(f"  erro de âncora registrado no plano (o QA acusa): {e[:170]}")


# ------------------------------------------------------------------------------------------------- efeitos: a mecânica
@teste
def efeito_mascara_chanfro_na_foto_do_ativo():
    """ativo: o nó do recorte com efeito.mascara chanfro sai com clip-path."""
    ns = nos(secoes()["ativo_painel"], "recorte-cena")
    assert ns, "nenhum nó `recorte-cena` na página do ativo (o elemento nem entrou)"
    com = [n for n in ns if "clip-path" in n["estilo"] or "-webkit-clip-path" in n["estilo"] or "clip-path=" in n["tag"]]
    assert com, f"o nó `recorte-cena` existe e não tem clip-path: a máscara chanfro não foi aplicada ({ns[0]['tag'][:60]}...)"


@teste
def efeito_cruza_dois_nos_do_mesmo_png():
    """capa: efeito.cruza parte a medalha em dois nós do MESMO data URI (um atrás e outro na frente do título)."""
    ns = [n for n in nos(secoes()["capa"], "medalha") if n["src"]]
    assert ns, "nenhum nó da medalha na capa (o elemento nem entrou)"
    contagem = {}
    for n in ns:
        contagem[n["src"]] = contagem.get(n["src"], 0) + 1
    assert max(contagem.values()) >= 2, (f"{len(ns)} nó(s) da medalha na capa, cada um com um PNG: o cruza pede dois nós do mesmo "
                                         f"data URI partidos na linha do título")


@teste
def efeito_reflexo_e_sombra_de_contato_na_cota():
    """cota: reflexo piso e sombra contato viram os itens `<id>-reflexo` e `<id>-sombra`."""
    sec = secoes()["cota"]
    assert nos(sec, "selo-objeto"), "nenhum nó `selo-objeto` na cota (o elemento nem entrou)"
    ids = set(re.findall(r'data-elemento="(selo-objeto[^"]*)"', sec))
    falta = [i for i in ("selo-objeto-reflexo", "selo-objeto-sombra") if i not in ids]
    assert not falta, f"o objeto está na página ({sorted(ids)}) e faltam {falta}: reflexo piso e sombra contato não foram gerados"


@teste
def efeito_grao_e_luz_marcados_na_section():
    """toda página com `acabamento.grao`/`luz` declarado sai com data-grao/data-luz na section."""
    secs, comp = secoes(), kit()["composicao"]
    falta = []
    for tipo, sec in secs.items():
        ac = (comp.get(CHAVE_COMP[tipo]) or {}).get("acabamento") or {}
        abre = re.match(r"<section\b[^>]*>", sec).group(0)
        for campo in ("grao", "luz"):
            if campo in ac and f'data-{campo}="{ac[campo]}"' not in abre:
                falta.append(f"{tipo}: data-{campo}=\"{ac[campo]}\"")
    assert not falta, f"{len(falta)} marcação(ões) faltando na section: {', '.join(falta)}"


@teste
def efeito_eco_svg_com_o_texto_do_titulo():
    """capa: o grafismo `eco` é um SVG com o texto do título (texto vivo)."""
    ns = nos(secoes()["capa"], "eco-titulo")
    assert ns, f"nenhum nó `eco-titulo` na capa: {por_que_falta('eco-titulo')}"
    titulo = kit()["evento"]["nome"].casefold()
    com = [n for n in ns if "<svg" in n["dentro"] and titulo in re.sub(r"<[^>]+>", " ", n["dentro"]).casefold()]
    assert com, "o nó `eco-titulo` existe e o SVG não traz o texto do título"


@teste
def efeito_opacidade_e_blend_nos_nos_de_acabamento():
    """capa: eco com opacity .12; prova: hachura com opacity .24 e mix-blend-mode multiply (efeito vence o elemento)."""
    secs = secoes()
    pedidos = [("capa", "eco-titulo", 0.12, None), ("prova", "hachura-dados", 0.24, "multiply")]
    erros = []
    for tipo, eid, op, blend in pedidos:
        ns = nos(secs[tipo], eid)
        if not ns:
            erros.append(f"{tipo}: nenhum nó `{eid}`: {por_que_falta(eid)}")
            continue
        st = ns[0]["estilo"]
        if opacidade(st.get("opacity")) != op:
            erros.append(f"{tipo}: `{eid}` com opacity {st.get('opacity')!r}, pedido {op}")
        if blend and st.get("mix-blend-mode") != blend:
            erros.append(f"{tipo}: `{eid}` com mix-blend-mode {st.get('mix-blend-mode')!r}, pedido {blend}")
    assert not erros, "; ".join(erros)


@teste
def efeito_malha_no_divisor():
    """divisor: o grafismo `malha` presente (SVG), atrás do título."""
    ns = nos(secoes()["divisor"], "malha-fundo")
    assert ns, f"nenhum nó `malha-fundo` no divisor: {por_que_falta('malha-fundo')}"
    assert any("<svg" in n["dentro"] for n in ns), "o nó `malha-fundo` existe sem SVG"


@teste
def efeito_registro_figura_na_frente_do_titulo():
    """público: a âncora `registro` põe a figura na camada frente, na caixa da foto (o plano diz relacao registro)."""
    ns = nos(secoes()["publico"], "figura-publico")
    plano = render()["plano"]
    pg = next(p for p in plano["paginas"] if p["rotulo"].startswith("publico"))
    erros = [e for e in pg.get("erros_composicao") or [] if "figura-publico" in e]
    assert ns, f"nenhum nó `figura-publico` no público: {erros[0] if erros else 'sem erro registrado'}"
    assert all('data-camada="frente"' in n["tag"] for n in ns), "a figura não está na camada frente"
    it = next((e for e in pg["elementos"] if e["id"] == "figura-publico"), {})
    assert (it.get("ancora") or {}).get("relacao") == "registro", f"o plano não traz a âncora registro: {it.get('ancora')}"


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

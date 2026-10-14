#!/usr/bin/env python3
"""
render.py v2 — mediakit.json → sequência-mestre (gramática v1 §2) → HTML → PDF (+PNG).

Uso:
  python3 render.py <pasta-do-cliente> [--direcao causa|performance|territorio] [--todas] [--receita r1] [--png] [--sem-vertical]
  python3 render.py <pasta-do-cliente> --maquete [--receita r1] [--sem-vertical]

--maquete (planejar antes de gerar, references/09 §1): o mesmo render, mas cada elemento planejado entra como caixa
hachurada na cor da função, com rótulo `id · função · relação→alvo`, na posição e no tamanho resolvidos; asset ainda
não gerado entra pela `proporcao` declarada na composição. Saída saida/maquete-<receita>.pdf, PNGs em saida/png/ e
saida/plano-maquete-<receita>.json; não mexe no kit-<receita>.pdf nem no render-report.json.

Receitas (frente 4): com `receitas` no JSON e sem --direcao/--todas, gera um kit por receita (kit-<id>.pdf). Cada receita
combina par tipográfico, paleta, fundo (escuro|papel|cor), máscara de foto, pattern, ornamentos e variante de layout por
tipo de página. Sem `receitas`, o render é o das três direções, idêntico ao de antes (a regressão depende disso).
`elementos` e `sistema_elementos` (pattern, constantes, heróis, apoios) entram pelo camadas.py: o render mede a página
sem elementos, o encaixes.py resolve a posição sobre as caixas protegidas e o render final sai com cada elemento na camada
certa, mais saida/plano-elementos-<receita>.json para o qa_geometria.py. `paginas` (lista de tipos ou {tipo, variante})
gera só essas páginas, nessa ordem: é o modo piloto.

Entrada:  <pasta>/mediakit.json e as imagens que ele referencia (relativas à pasta).
Saída:    <pasta>/saida/kit-<direcao>.pdf, kit-<direcao>-vertical.pdf, render-report.json, png/ (com --png).

O Claude escreve só o mediakit.json. A sequência de páginas é derivada daqui (regras em memoria-mediakit/gramatica.md §2 e §7);
`paginas` no JSON filtra e ordena a sequência (piloto de 4 páginas, guia J regra 14).
Imagem sem direito_uso=true não é embutida. Imagem gerada sem rotulo não é embutida.
"""
import argparse, base64, copy, json, mimetypes, re, sys
from datetime import date
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, ChainableUndefined

import camadas as sistema_elementos
from caminhos import ForaDoKit, dentro_do_kit

AQUI = Path(__file__).resolve().parent
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
DIRECOES = ["causa", "performance", "territorio"]
ICONES_PADRAO = {"inscritos": "seta", "pessoas na arena": "pessoas", "seguidores": "mais", "finishers": "alvo", "concluíram": "alvo", "visualizações": "olho", "visitas": "pessoa", "cliques": "cursor", "cidades": "alvo", "idade": "alvo", "interesse": "coracao"}
ICONES_COTA = ["camisa", "megafone", "balao", "tenis"]
# page plan (pesquisa r2): função e peso de cada arquétipo. Peso 3 = impacto, 2 = médio, 1 = informativo.
PLANO = {"capa": ("impacto", 3), "manifesto": ("impacto", 2), "projecao": ("impacto", 3), "publico": ("prova", 2), "prova": ("prova", 1),
         "divisor": ("impacto", 2), "ativo_painel": ("oferta", 2), "ativo_topo": ("oferta", 2), "inventario_colunas": ("oferta", 1),
         "divisor_cotas": ("impacto", 2), "cota": ("oferta", 2), "contato": ("acao", 3),
         "territorio": ("prova", 2), "historico_logos": ("prova", 1)}


def fmt_data(iso):
    try:
        d = date.fromisoformat(iso); return f"{d.day} de {MESES[d.month-1]} de {d.year}"
    except Exception:
        return iso or ""


def fmt_valor(v, unidade=None):
    if isinstance(v, (int, float)):
        if v >= 1000 and float(v).is_integer():
            s = f"{int(v):,}".replace(",", ".")
        elif float(v).is_integer():
            s = str(int(v))
        else:
            s = f"{v:.1f}".replace(".", ",")
    else:
        s = str(v)
    if unidade == "%":  # norma brasileira de porcentagem sem espaço em número-herói ("52%", não "52 %")
        return s + "%"
    return s + (f" {unidade}" if unidade else "")


def montar_grafico(g):
    """Gráfico de barras vetorial (Corre por Elas p.6): eixo com valores, grade leve, valor em cima de cada barra, legenda.
    Cada item de `series` tem `valor` (uma série) ou `valores` (barras agrupadas, nomes em `g.legenda`).
    Escala log quando o maior valor passa de 20× o menor (senão as barras pequenas somem); `g.escala` força linear ou log.
    Devolve posições em fração da altura útil (0 a 1): o template só desenha."""
    import math
    itens = [dict(s, valores=list(s.get("valores") or [s["valor"]])) for s in g["series"]]
    todos = [v for s in itens for v in s["valores"] if isinstance(v, (int, float)) and v > 0]
    lo_v, hi_v = (min(todos), max(todos)) if todos else (1, 1)
    escala = g.get("escala") or ("log" if hi_v / lo_v >= 20 else "linear")
    if escala == "log":
        # marcas 1-3 por década: do degrau abaixo do menor valor até o primeiro degrau acima do maior
        marcas = []; e = math.floor(math.log10(lo_v))
        while True:
            for m in (1, 3):
                marcas.append(m * 10 ** e)
            if marcas[-1] >= hi_v and marcas[-2] >= hi_v: break
            e += 1
        marcas = [x for x in marcas if x >= 10 ** math.floor(math.log10(lo_v))]
        while len(marcas) > 1 and marcas[-2] >= hi_v: marcas.pop()
        lo, hi = math.log10(marcas[0]), math.log10(marcas[-1])
        pos = lambda v: max(0.0, (math.log10(v) - lo) / (hi - lo)) if v > 0 else 0.0
    else:
        bruto = hi_v / 4; mag = 10 ** math.floor(math.log10(bruto)) if bruto > 0 else 1
        passo = next(f * mag for f in (1, 2, 2.5, 5, 10) if f * mag >= bruto)
        topo = math.ceil(hi_v / passo) * passo
        marcas = [i * passo for i in range(int(round(topo / passo)) + 1)]
        pos = lambda v: v / topo if topo else 0.0
    return dict(g, escala=escala,
                marcas=[dict(valor_fmt=fmt_valor(int(x) if float(x).is_integer() else x), pos=round(pos(x), 4)) for x in marcas],
                series=[dict(s, barras=[dict(valor_fmt=fmt_valor(v), pos=round(pos(v), 4)) for v in s["valores"]]) for s in itens],
                legenda=g.get("legenda") or [])


def data_uri(p: Path):
    mime = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def icone_para(rotulo):
    r = (rotulo or "").lower()
    for k, v in ICONES_PADRAO.items():
        if k in r:
            return v
    return "seta"


def carregar_acervo(k, pasta, report):
    acervo = {}
    for a in k.get("acervo", []):
        try:
            p = dentro_do_kit(pasta, a["arquivo"])
        except ForaDoKit as e:
            raise SystemExit(f"acervo {a.get('id')}: {e}. O render recusa: o arquivo iria embutido no PDF")
        if not a.get("direito_uso"):
            report["avisos"].append(f"acervo {a['id']}: sem direito de uso, fora do kit"); continue
        if not p.exists():
            report["avisos"].append(f"acervo {a['id']}: arquivo não encontrado: {a['arquivo']}"); continue
        if a.get("gerada") and a.get("funcao") not in ("lettering", "logo", "simbolo") and not a.get("rotulo") and a.get("rotulo") is not None:
            pass
        acervo[a["id"]] = dict(a, src=data_uri(p))
    return acervo


pasta_global = Path(".")


def montar_paginas(k, acervo, report):
    """Sequência-mestre. Devolve a lista de páginas com dados já resolvidos."""
    def por_funcao(f, exclui=()):
        for a in k.get("acervo", []):
            if a["funcao"] == f and a["id"] in acervo and a["id"] not in exclui:
                return acervo[a["id"]]
        return None
    def por_id(i):
        return acervo.get(i) if i else None

    usadas = set()
    def pega(*candidatos):
        for c in candidatos:
            if c and c["id"] not in usadas:
                usadas.add(c["id"]); return c
        for c in candidatos:
            if c:
                return c
        return None

    lettering = por_funcao("lettering") or por_funcao("logo")
    simbolo = por_funcao("simbolo") or lettering
    provas = [dict(p, valor_fmt=fmt_valor(p["valor"], p.get("unidade")), icone=p.get("icone") or icone_para(p["rotulo"])) for p in k.get("provas", [])]

    pags = []
    # 1 capa
    pags.append(dict(tipo="capa", cena=pega(por_funcao("capa"), por_funcao("historico")), logo=lettering))
    # 2 manifesto
    if k.get("manifesto"):
        pags.append(dict(tipo="manifesto", cena=pega(por_funcao("manifesto"), por_funcao("historico")), simbolo=simbolo))
    # 3 projeção
    proj = por_funcao("projecao")
    if proj:
        usadas.add(proj["id"]); pags.append(dict(tipo="projecao", cena=proj))
    # 4 público
    pub = k.get("publico") or {}
    cards = [p for p in provas if p.get("destaque")][:3]
    if pub.get("descricao") or cards:
        pags.append(dict(tipo="publico", cena=pega(por_funcao("publico"), por_funcao("historico")), cards=cards, genero=pub.get("genero")))
    # 4b quem já esteve (A25): grade de logos da edição anterior, só com acervo `logo_patrocinador` e historico com pode_citar
    logos = por_funcao("logo_patrocinador")
    if logos and any(p.get("pode_citar") for h in k.get("historico", []) for p in h.get("patrocinadores", [])):
        usadas.add(logos["id"]); pags.append(dict(tipo="historico_logos", historico=k.get("historico_pagina") or {}, logos=logos))
    # 4c território (A5): de onde vem o público e por que o lugar importa
    if k.get("territorio"):
        pags.append(dict(tipo="territorio", territorio=k["territorio"], cena=pega(por_funcao("local"))))
    # 5 prova (alcance / metas)
    prova_cfg = k.get("prova") or {}
    restantes = [p for p in provas if p not in cards][:4]
    graficos = []
    for g in prova_cfg.get("graficos", []):
        graficos.append(montar_grafico(g))
    if restantes or graficos:
        pags.append(dict(tipo="prova", caixas=restantes, nota=prova_cfg.get("nota"), graficos=graficos))
    # 6 divisor
    dv = k.get("divisor_inventario") or {}
    pags.append(dict(tipo="divisor", titulo=dv.get("titulo") or "Visibilidade real,|impacto positivo.", subtitulo=dv.get("subtitulo") or "Confira os pontos onde sua marca será exposta:"))
    # 7 ativos
    n = 0; sem_cena = []
    for i in k.get("inventario", []):
        cena = por_id(i.get("cena_id") or i.get("foto_id"))
        if cena and i.get("titulo"):
            n += 1; usadas.add(cena["id"])
            if i.get("layout") == "topo":
                pags.append(dict(tipo="ativo_topo", n=n, ativo=i, cena=cena, mini=por_id(i.get("mini_id"))))
            else:
                pags.append(dict(tipo="ativo_painel", n=n, ativo=i, cena=cena))
        else:
            sem_cena.append(i)
    if sem_cena:
        pags.append(dict(tipo="inventario_colunas", itens=sem_cena))
        if len(sem_cena) > 8:
            report["avisos"].append(f"inventário em colunas com {len(sem_cena)} itens; acima de 8 encolhe")
    # 8 divisor de cotas
    pags.append(dict(tipo="divisor_cotas", cena=pega(por_funcao("cotas"), por_funcao("historico")), simbolo=simbolo))
    # 9 cotas
    objetos = {o["id"]: o for o in k.get("objetos", [])}
    def objeto_para(pagina_id):
        for o in objetos.values():
            if o.get("pagina") == pagina_id and o.get("arquivo"):
                try:
                    p = dentro_do_kit(pasta_global, o["arquivo"])
                    sombra = dentro_do_kit(pasta_global, o["sombra"]) if o.get("sombra") else None
                except ForaDoKit as e:
                    raise SystemExit(f"objeto {o.get('id')}: {e}. O render recusa: o arquivo iria embutido no PDF")
                if not p.exists():
                    report["avisos"].append(f"objeto {o['id']}: arquivo não encontrado"); return None
                return dict(o, src=data_uri(p), sombra=data_uri(sombra) if sombra and sombra.exists() else None, divisa_px=o.get("divisa_px", 960))
        return None
    for idx, c in enumerate(k.get("cotas", [])):
        cena = por_id(c.get("cena_id")) or pega(por_funcao("cota"), por_funcao("historico"), por_funcao("capa"))
        icones = c.get("icones") or ICONES_COTA[: max(2, min(3, len(c.get("entregaveis", [])) // 2))]
        pags.append(dict(tipo="cota", cota=c, cena=cena, icones=icones, objeto=objeto_para(f"cota:{c.get('nome')}")))
    # 10 contato
    pags.append(dict(tipo="contato", cena=pega(por_funcao("contato"), por_funcao("historico"), por_funcao("capa")), logo=lettering))

    for p in pags:
        if p["tipo"] in ("capa", "manifesto", "projecao", "ativo_painel", "ativo_topo", "cota", "contato") and not p.get("cena"):
            report["avisos"].append(f"página {p['tipo']}: sem cena; a gramática exige imagem aqui")
        p["funcao"], p["peso"] = PLANO.get(p["tipo"], ("prova", 1))
    return pags


# ---------------------------------------------------------------------------------------------------------------
# Frente 4: receitas, variantes de layout, fundos, máscaras, elementos (pattern e ornamento) e filtro `paginas`
# ---------------------------------------------------------------------------------------------------------------
VARIANTES = {"capa": ("a", "b", "c"), "manifesto": ("a", "b"), "publico": ("a", "b"), "divisor": ("a", "b", "c"),
             "cota": ("a", "b", "c"), "contato": ("a", "b")}
ATIVO_VARIANTES = {"painel": ("ativo_painel", "a"), "topo": ("ativo_topo", "a"), "diagonal": ("ativo_painel", "diagonal"),
                   "sangria": ("ativo_painel", "sangria")}
FUNDOS = ("escuro", "papel", "cor")
MASCARAS = ("reto", "diagonal", "arredondado", "sangria")
# camada de acabamento (mk-2.1, references/10): grão e luz da página vão para data-* da section; vocabulário fechado
ACAB_PAGINA = {"grao": ("nenhum", "leve", "padrao", "forte"), "luz": ("nenhuma", "esq", "dir", "topo")}


def _lum(hexc):
    h = hexc.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contraste(a, b):
    """Razão de contraste WCAG 2.x entre dois hex."""
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def _rgba(hexc, alfa):
    h = hexc.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alfa})"


def _melhor(fundo, *candidatas, minimo=0.0):
    """A primeira candidata com contraste >= minimo sobre o fundo; senão, a de maior contraste."""
    for c in candidatas:
        if c and contraste(c, fundo) >= minimo:
            return c
    return max((c for c in candidatas if c), key=lambda c: contraste(c, fundo))


def _misturar(a, b, t):
    ha, hb = a.lstrip("#"), b.lstrip("#")
    return "#" + "".join(f"{round(int(ha[i:i+2], 16) * (1 - t) + int(hb[i:i+2], 16) * t):02X}" for i in (0, 2, 4))


def acento_legivel(cor, fundo, minimo=4.5):
    """A cor de acento também pinta microlabel de 16 px: precisa de 4,5:1 sobre o fundo. Se não tiver, escurece (ou clareia)
    na direção da tinta até passar, mantendo o matiz; a cor original continua nos véus e nas formas."""
    if contraste(cor, fundo) >= minimo:
        return cor
    alvo = "#000000" if _lum(fundo) > 0.18 else "#FFFFFF"
    for i in range(1, 21):
        c = _misturar(cor, alvo, i / 20)
        if contraste(c, fundo) >= minimo:
            return c
    return alvo


def css_receita(r):
    """Tokens da receita num bloco que vence a direção (html[data-receita] tem especificidade maior que [data-direcao]).
    Calcula também os tokens dos fundos claro (papel) e de cor, escolhendo a tinta de maior contraste: o QA mede depois."""
    f, pal = r.get("fontes") or {}, r.get("paleta") or {}
    marca = pal.get("marca", "#E8307A"); escuro = pal.get("escuro", "#0B0B0C"); papel = pal.get("papel", "#F4F1EA")
    texto = pal.get("texto", "#FFFFFF"); apoio = pal.get("apoio") or marca
    corpo = f.get("corpo") or "DM Sans"
    linhas = []
    if f.get("display"):
        linhas.append(f'--fonte-display: "{f["display"]}", "{corpo}", "FreeSans", sans-serif;')
        linhas.append(f'--fonte-titulo: "{f.get("titulo") or f["display"]}", "{corpo}", "FreeSans", sans-serif;')
    if f.get("lettering"):
        # tipografia expressiva (mk-2.1): só quando declarada; cai no display, depois no corpo
        linhas.append(f'--fonte-lettering: "{f["lettering"]}", "{f.get("display") or corpo}", "{corpo}", "FreeSans", sans-serif;')
    linhas.append(f'--fonte-corpo: "{corpo}", "FreeSans", "Liberation Sans", sans-serif;')
    if f.get("peso_display"):
        linhas.append(f"--peso-display: {int(f['peso_display'])};")
    linhas += [f"--marca: {marca};", f"--escuro: {escuro};", f"--papel: {papel};", f"--texto: {texto};",
               f"--texto-suave: {_rgba(texto, .72)};", f"--texto-apagado: {_rgba(texto, .46)};", f"--fantasma: {_rgba(texto, .11)};"]
    # fundo claro (papel): tinta = escuro da paleta; acento = marca se ler a 3:1 no papel, senão apoio, senão a tinta
    tinta_c = _melhor(papel, escuro, "#111111", minimo=4.5)
    acento_c = acento_legivel(_melhor(papel, marca, apoio, tinta_c, minimo=3.0), papel)
    # fundo de cor (a cor da marca chapada): tinta e acento com o maior contraste disponível
    tinta_k = _melhor(marca, escuro, texto, "#0B0B0C", "#FFFFFF", minimo=4.5)
    acento_k = acento_legivel(_melhor(marca, apoio, papel, tinta_k, minimo=3.0), marca)
    for nome, fundo, tinta, acento in (("claro", papel, tinta_c, acento_c), ("cor", marca, tinta_k, acento_k)):
        linhas += [f"--{nome}-fundo: {fundo};", f"--{nome}-texto: {tinta};", f"--{nome}-acento: {acento};",
                   f"--{nome}-suave: {_rgba(tinta, .78)};", f"--{nome}-apagado: {_rgba(tinta, .58)};", f"--{nome}-fantasma: {_rgba(tinta, .10)};",
                   f"--{nome}-linha: {_rgba(tinta, .22)};"]
    # o fundo da receita escolhe qual dos dois vale nas páginas planas
    fundo = r.get("fundo", "escuro")
    if fundo in ("papel", "cor"):
        n = "claro" if fundo == "papel" else "cor"
        linhas += [f"--plano-{x}: var(--{n}-{x});" for x in ("fundo", "texto", "acento", "suave", "apagado", "fantasma", "linha")]
    return f'html[data-receita="{r["id"]}"] {{ ' + " ".join(linhas) + " }"


def familias_faltando(r, fdir):
    """Famílias da receita sem arquivo na pasta --fontes (o navegador cairia em fallback)."""
    tem = {f.stem.partition("__")[0] for f in fdir.iterdir() if f.suffix.lower() in (".otf", ".ttf", ".woff2", ".woff")} if fdir.exists() else set()
    f = r.get("fontes") or {}
    return [fam for fam in dict.fromkeys([f.get("display"), f.get("titulo"), f.get("corpo"), f.get("lettering")])
            if fam and fam not in tem]


def aplicar_receita(pags, r, report):
    """Copia a sequência e aplica as variantes da receita: uma por tipo de página; para ativos, uma por ativo, na ordem."""
    var = r.get("variantes") or {}
    out = copy.deepcopy(pags)
    ativos = list(var.get("ativo") or [])
    i_ativo = 0
    for p in out:
        t = p["tipo"]
        if t in ("ativo_painel", "ativo_topo"):
            if i_ativo < len(ativos):
                v = ativos[i_ativo]
                if v not in ATIVO_VARIANTES:
                    report["avisos"].append(f"receita {r['id']}: variante de ativo `{v}` desconhecida; fica painel")
                    v = "painel"
                p["tipo"], p["variante"] = ATIVO_VARIANTES[v]
                p.setdefault("mini", None)
            i_ativo += 1
        elif t in VARIANTES:
            v = var.get(t, "a")
            if v not in VARIANTES[t]:
                report["avisos"].append(f"receita {r['id']}: variante `{v}` de {t} desconhecida; fica a")
                v = "a"
            p["variante"] = v
    return out


def filtrar_paginas(pags, pedido, report):
    """`paginas` do JSON: só estas, nesta ordem. Cada item é um tipo ou {tipo, variante}. Tipos repetidos (cota, ativo)
    pegam a próxima página daquele tipo. Ativo pedido num layout que a sequência não tem converte o próximo ativo livre."""
    usadas = set(); out = []
    for item in pedido:
        tipo, var = (item.get("tipo"), item.get("variante")) if isinstance(item, dict) else (item, None)
        alvo = None
        for i, p in enumerate(pags):
            if i not in usadas and (p["tipo"] == tipo or (tipo == "ativo" and p["tipo"] in ("ativo_painel", "ativo_topo"))):
                alvo = i; break
        if alvo is None and tipo in ("ativo_painel", "ativo_topo"):
            alvo = next((i for i, p in enumerate(pags) if i not in usadas and p["tipo"] in ("ativo_painel", "ativo_topo")), None)
        if alvo is None:
            report["avisos"].append(f"paginas: `{tipo}` pedido mas a sequência não tem página livre desse tipo"); continue
        usadas.add(alvo); p = copy.deepcopy(pags[alvo])
        if tipo in ("ativo_painel", "ativo_topo") and p["tipo"] != tipo:
            p["tipo"] = tipo; p.setdefault("mini", None); p["variante"] = "a"
        if var:
            if p["tipo"] in ("ativo_painel", "ativo_topo"):
                p["tipo"], p["variante"] = ATIVO_VARIANTES.get(var, (p["tipo"], var))
                p.setdefault("mini", None)
            else:
                p["variante"] = var
        out.append(p)
    return out


def e_plano(p):
    """Página cujo texto assenta sobre o fundo chapado (e não sobre foto com véu): é ela que troca de fundo em papel/cor."""
    t, v, cena = p["tipo"], p.get("variante", "a"), bool(p.get("cena"))
    if t in ("divisor", "prova", "ativo_topo", "territorio", "historico_logos"):
        return True
    if t == "ativo_painel":
        return v in ("a", "diagonal")
    if t == "cota":
        return v in ("a", "b")
    if t == "publico":
        return v == "b" or not cena
    if t in ("manifesto", "divisor_cotas", "contato"):
        return v == "a" and not cena
    return False


def declara_acabamento(k):
    """O kit declara direcao_criativa, `acabamento` de página ou `efeito` de elemento da composição? É a regra do
    tema/37-acabamento.css (a mesma ideia do 36-elementos.css): sem nada disso, o HTML sai byte a byte igual."""
    if k.get("direcao_criativa") is not None:
        return True
    for chave, ent in (k.get("composicao") or {}).items():
        if chave.startswith("_") or not isinstance(ent, dict):
            continue
        if "acabamento" in ent or any(isinstance(e, dict) and "efeito" in e for e in ent.get("elementos") or []):
            return True
    return False


def acabamento_da_pagina(k, p):
    """`composicao.<página>.acabamento` desta página (a entrada mais específica que declara; a da gramática, senão), ou {}.
    Os rótulos são os mesmos que o camadas.py usa para achar a composição da página."""
    comp = k.get("composicao") or {}
    if not comp:
        return {}
    import composicao
    _, ent, _, gent = composicao.entrada_da_pagina(comp, sistema_elementos.rotulos_pagina(p),
                                                   sistema_elementos.rotulo_variante(p), p["tipo"])
    ac = (ent or {}).get("acabamento") or (gent or {}).get("acabamento") or {}
    return ac if isinstance(ac, dict) else {}


def injetar_camadas(html, paginas, fundo):
    """Por página: classe `plano` (fundo papel/cor) e atributos de tipo e variante. Só roda com receita ou elementos: o
    legado passa direto e sai byte a byte igual. Os elementos entram depois, pelo camadas.py, na camada certa do DOM.
    Camada de acabamento (mk-2.1): `data-grao` e `data-luz` da página (p["_acab"], de acabamento_da_pagina) só quando
    declarados e dentro do vocabulário (vão para atributo HTML)."""
    partes = html.split("</section>")
    out = []
    for i, parte in enumerate(partes[:-1]):
        p = paginas[i] if i < len(paginas) else None
        if p is not None:
            j = parte.find('<section class="pagina')
            if j >= 0:
                extra = ' plano' if (fundo in ("papel", "cor") and p.get("plano")) else ''
                ac = p.get("_acab") or {}
                attrs = "".join(f' data-{c}="{ac[c]}"' for c in ("grao", "luz") if ac.get(c) in ACAB_PAGINA[c])
                cab = f'<section data-tipo="{p["tipo"]}" data-variante="{p.get("variante", "a")}"{attrs} class="pagina{extra}'
                parte = parte[:j] + cab + parte[j + len('<section class="pagina'):]
        out.append(parte)
    out.append(partes[-1])
    return "</section>".join(out)


def plano_report(pags):
    return [{"n": i + 1, "tipo": p["tipo"], "funcao": p["funcao"], "peso": p["peso"], "cena": bool(p.get("cena")), "objeto": bool(p.get("objeto"))} for i, p in enumerate(pags)]


def paginas_report(pags):
    """O que o qa.py precisa por página: variante, se é plana e os elementos que entraram (plano completo em
    saida/plano-elementos-<receita>.json)."""
    return [{"n": i + 1, "tipo": p["tipo"], "variante": p.get("variante", "a"), "plano": bool(p.get("plano")),
             "pattern": next((e["id"] for e in p.get("_elementos", []) if e["papel"] == "pattern"), None),
             "elementos": [{"id": e["id"], "papel": e["papel"], "camada": e["camada"]} for e in p.get("_elementos", [])]}
            for i, p in enumerate(pags)]


JS_MEDIR = """
(cfg) => {
  const W = cfg.w, H = cfg.h, SAFE = 96;
  const marca = cfg.marca.toLowerCase();
  const paginas = Array.from(document.querySelectorAll('.pagina'));
  const toHex = (rgb) => { const m = rgb.match(/\\d+/g); if (!m) return ''; return '#' + m.slice(0,3).map(x => (+x).toString(16).padStart(2,'0')).join(''); };
  const escala = [230,96,64,36,24,16];

  // auto-ajuste (igual v2)
  const ajustes = [];
  document.querySelectorAll('[data-fit]').forEach((el) => {
    const pag = el.closest('.pagina'); const miolo = el.closest('.painel') || pag;
    let size = parseFloat(getComputedStyle(el).fontSize); const start = size; let passos = 0;
    const tol = () => Math.max(24, size * 0.3);
    const estoura = () => el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + tol() || miolo.scrollHeight > miolo.clientHeight + 24;
    while (estoura() && size > start * 0.6 && passos < 40) { size *= 0.96; el.style.fontSize = size + 'px'; passos++; }
    let esc = 1.0; if (estoura()) { while (estoura() && esc > 0.7) { esc = +(esc - 0.03).toFixed(2); el.style.zoom = esc; } }
    ajustes.push({ pagina: paginas.indexOf(pag) + 1, fonte_inicial: start, fonte_final: size, passos, zoom: esc, estourou: estoura(), texto: (el.innerText || '').slice(0, 60) });
  });

  // fontes carregadas
  const fam = (f) => f.split(',')[0].replace(/["']/g,'').trim();
  const fontes = {};
  // a família declarada precisa ter ao menos um @font-face CARREGADO na página. document.fonts.check() não serve:
  // devolve true para família inexistente (nada a carregar) e false para display usada só em 800 cujo 400 não carregou
  // (os dois casos medidos em 08/10/2026 com a Archivo Expanded)
  const carregadas = new Set(Array.from(document.fonts).filter(ff => ff.status === 'loaded').map(ff => ff.family.replace(/["']/g, '').trim()));
  ['--fonte-display','--fonte-titulo','--fonte-corpo'].forEach(v => {
    const f = fam(getComputedStyle(document.documentElement).getPropertyValue(v)); fontes[f] = carregadas.has(f);
  });
  // lettering (mk-2.1, só quando a receita declara): a face tem de existir (o --fontes tem o arquivo); carrega quando um
  // grafismo de tipografia expressiva a usa. Família que já é display ou corpo fica com a conferência dela.
  const lt = fam(getComputedStyle(document.documentElement).getPropertyValue('--fonte-lettering'));
  if (lt && !(lt in fontes)) fontes[lt] = carregadas.has(lt) || Array.from(document.fonts).some(ff => ff.family.replace(/["']/g, '').trim() === lt);
  const fontesRaiz = { display: fam(getComputedStyle(document.documentElement).getPropertyValue('--fonte-display')), titulo: fam(getComputedStyle(document.documentElement).getPropertyValue('--fonte-titulo')) };

  const out = [];
  paginas.forEach((pg, idx) => {
    const r = pg.getBoundingClientRect(); const y0 = r.top;
    const textos = [], midias = [], fora = [], viuvas = [], cor_papeis = new Set(), escala_fora = [], micro2 = [];
    let areaTexto = 0, svgs = pg.querySelectorAll('svg').length;
    // grafismo (svg.grafismo, elemento de texto vivo) não é ícone: o qa.py desconta da contagem de ícones
    const svgsGrafismo = Array.from(pg.querySelectorAll('svg')).filter(s => s.closest('svg.grafismo')).length;
    pg.querySelectorAll('h1,h2,h3,p,li,span,div').forEach(el => {
      const cs = getComputedStyle(el);
      if (cs.visibility === 'hidden' || cs.display === 'none') return;
      // só nós com texto direto
      const direto = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim());
      const isSvg = el.closest('svg'); if (isSvg) return;
      if (el.tagName === 'SPAN' && el.parentElement && el.parentElement.matches('h1,h2,h3,p,li')) return; // parte inline do mesmo bloco
      // cor da marca em borda/fundo/texto
      ['color','borderTopColor','backgroundColor'].forEach(p => { if (toHex(cs[p]) === marca && !el.closest('.fio')) cor_papeis.add((el.className && el.className.baseVal === undefined ? el.className : el.tagName.toLowerCase()).split(' ')[0] || el.tagName.toLowerCase()); });
      if (!direto) return;
      const b = el.getBoundingClientRect(); if (b.width < 2 || b.height < 2) return;
      const fs = parseFloat(cs.fontSize);
      const bgc = cs.backgroundColor; const opaco = bgc && !/rgba\\(.*,\\s*0\\)$/.test(bgc) && bgc !== 'transparent';
      const box = { x: b.left - r.left, y: b.top - y0, w: b.width, h: b.height, fs, peso: parseInt(cs.fontWeight) || 400, cor: toHex(cs.color), bg: opaco ? toHex(bgc) : null, texto: (el.innerText || '').slice(0, 50), cls: el.className || el.tagName.toLowerCase() };
      textos.push(box); areaTexto += b.width * b.height;
      if (b.right > r.right + 1 || b.bottom > r.bottom + 1 || b.left < r.left - 1 || b.top < y0 - 1) fora.push(box.texto);
      if (!escala.some(e => Math.abs(e - fs) <= 2) && !el.closest('.fio') && !el.closest('[data-fit]')) escala_fora.push({ fs, texto: box.texto });
      if (el.classList.contains('micro') && b.height > fs * 1.6) micro2.push(box.texto);
      // viúva em título: última linha com uma palavra
      if (el.matches('h1,h2') && el.innerText.includes(' ')) {
        const rng = document.createRange(); const tn = el.lastChild && el.lastChild.nodeType === 3 ? el.lastChild : null;
        if (tn) { const txt = tn.textContent; const i = txt.lastIndexOf(' '); if (i > 0 && i < txt.length - 1) { rng.setStart(tn, i + 1); rng.setEnd(tn, txt.length); const rr = rng.getBoundingClientRect(); const lines = Math.round(b.height / (fs * parseFloat(cs.lineHeight) / fs || 1)); if (lines > 1 && Math.abs(rr.left - b.left) < 3 && rr.width < b.width * 0.35) viuvas.push(box.texto); } }
      }
    });
    pg.querySelectorAll('img').forEach(img => {
      if (img.classList.contains('ornamento') || img.closest('[data-elemento]')) return;  // elemento é camada, não cena (plano-elementos)
      const b = img.getBoundingClientRect(); if (b.width < 2) return;
      midias.push({ x: b.left - r.left, y: b.top - y0, w: b.width, h: b.height, nat_w: img.naturalWidth, nat_h: img.naturalHeight, full: b.width >= W * 0.5 && b.height >= H * 0.5 });
    });
    const util = (W - 2 * SAFE) * (H - 2 * SAFE);
    // dominante: maior caixa de texto ou cena
    // hierarquia por peso (Refactoring UI): área × fator de peso (400→1, 800→2)
    let dom = 0, segundo = 0; textos.map(b => ({a: (b.w * b.h) / util * (b.peso ? Math.min(2, Math.max(1, b.peso / 400)) : 1)})).concat(midias.map(m => ({a: (m.w * m.h) / util}))).forEach(({a}) => { if (a > dom) { segundo = dom; dom = a; } else if (a > segundo) segundo = a; });
    // grid: arestas esquerdas × colunas
    const cols = []; for (let c = 0; c < 12; c++) cols.push(SAFE + c * (128 + 24));
    const blocos = []; pg.querySelectorAll('.painel > *, h1, h2').forEach(el => { const b = el.getBoundingClientRect(); if (b.width > 2 && (el.innerText || '').trim()) blocos.push({ x: b.left - r.left, texto: (el.innerText || '').slice(0, 40) }); });
    const desal = blocos.filter(t => !cols.some(cx => Math.abs(cx - t.x) <= 2) && Math.abs(t.x - W / 2) > 2 && t.x > SAFE + 2).map(t => t.texto);
    // cobertura de glifos: cada nó de texto com a família DECLARADA (primeira da lista), o peso e o texto já transformado
    // (caixa alta do CSS); o qa.py confere cada caractere no cmap do arquivo em --fontes (letra fora do subconjunto cai em outra fonte)
    const glifos = {};
    const tw = document.createTreeWalker(pg, NodeFilter.SHOW_TEXT);
    for (let tn = tw.nextNode(); tn; tn = tw.nextNode()) {
      const el = tn.parentElement; if (!el || !tn.textContent.trim()) continue;
      const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || cs.display === 'none') continue;
      let txt = tn.textContent.replace(/\\s+/g, ' ').trim();
      if (cs.textTransform === 'uppercase') txt = txt.toLocaleUpperCase('pt-BR'); else if (cs.textTransform === 'lowercase') txt = txt.toLocaleLowerCase('pt-BR');
      const familia = fam(cs.fontFamily); const peso = parseInt(cs.fontWeight) || 400;
      const papel = (familia === fontesRaiz.display || familia === fontesRaiz.titulo) ? 'display' : 'corpo';
      const chave = familia + '|' + peso + '|' + papel;
      if (!glifos[chave]) glifos[chave] = { familia, peso, papel, textos: [] };
      glifos[chave].textos.push(txt.slice(0, 80));
    }
    // frente 4: caixas dos ornamentos e dos títulos (o qa.py mede sobreposição e conta ornamentos por página)
    const ornamentos = Array.from(pg.querySelectorAll('.ornamento')).map(o => { const b = o.getBoundingClientRect(); return { id: o.dataset.elemento, camada: o.classList.contains('frente') ? 'frente' : 'atras', x: b.left - r.left, y: b.top - y0, w: b.width, h: b.height }; });
    const titulos = Array.from(pg.querySelectorAll('h1,h2')).map(t => { const b = t.getBoundingClientRect(); return { x: b.left - r.left, y: b.top - y0, w: b.width, h: b.height, texto: (t.innerText || '').slice(0, 40) }; });
    out.push({ pagina: idx + 1, classe: pg.className, variante: pg.dataset.variante || null, pattern: !!pg.querySelector('.camada-pattern, .el-pattern'), ornamentos, titulos, dominante: pg.dataset.dominante || null, area_dominante: +dom.toFixed(3), area_segundo: +segundo.toFixed(3), densidade_texto: +(areaTexto / util).toFixed(3), cor_papeis: Array.from(cor_papeis), svgs, svgs_grafismo: svgsGrafismo, textos, midias, fora_da_pagina: fora, viuvas, escala_fora, micro_2linhas: micro2, desalinhados: desal, tem_cena: midias.some(m => m.full), glifos: Object.values(glifos) });
  });
  return { ajustes, fontes, paginas: paginas.length, por_pagina: out };
}
"""


def exportar(html_path, pdf_path, largura, altura, png_dir, prefixo, marca="#000000", extra=None):
    """Mede (JS_MEDIR, que roda o data-fit) e exporta PDF e PNG. `extra` = (js, cfg) roda depois do data-fit e volta em
    medidas["extra"] (o camadas.py mede as caixas protegidas assim). pdf_path None = só medir (1ª passagem dos elementos)."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": largura, "height": altura}, device_scale_factor=1)
        pg.emulate_media(media="screen")
        pg.goto(html_path.resolve().as_uri()); pg.wait_for_load_state("networkidle"); pg.evaluate("document.fonts.ready")
        medidas = pg.evaluate(JS_MEDIR, {"w": largura, "h": altura, "marca": marca})
        if extra:
            medidas["extra"] = pg.evaluate(extra[0], extra[1])
        if pdf_path is None:
            b.close(); medidas["png_dir"] = None
            return medidas
        # o tamanho da folha vem do @page de cada template (10-tokens.css: 1920×1080; vertical.html: 1080×1920). Antes a
        # vertical herdava o @page de 1920×1080 do tema e o Chromium o seguia mesmo com prefer_css_page_size=False: cada
        # página de 1080×1920 saía partida em duas folhas deitadas (6 páginas de 1440×810 pt no lugar de 3 de 810×1440)
        pg.pdf(path=str(pdf_path), width=f"{largura}px", height=f"{altura}px", print_background=True, prefer_css_page_size=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        if png_dir:
            png_dir.mkdir(parents=True, exist_ok=True)
            # kit que encolheu deixava a página antiga (p.19 de um kit de 18) e ela entrava no contact sheet (08/10/2026)
            for velho in png_dir.glob(f"{prefixo}-[0-9][0-9].png"):
                velho.unlink()
            for i in range(medidas["paginas"]):
                pg.screenshot(path=str(png_dir / f"{prefixo}-{i+1:02d}.png"), clip={"x": 0, "y": i * altura, "width": largura, "height": altura}, full_page=True)
        medidas["png_dir"] = str(png_dir) if png_dir else None
        b.close()
    return medidas


def injetar_fio(html, paginas):
    """Assinatura 'fio': linha de progresso dentro de cada página, exceto capa e projeção."""
    partes = html.split("</section>")
    n = len(paginas); out = []
    for i, parte in enumerate(partes[:-1]):
        tipo = paginas[i]["tipo"] if i < n else ""
        pct = round(100 * (i + 1) / n, 1)
        fio = "" if tipo in ("capa", "projecao") else f'<div class="fio"><div class="trilho"></div><div class="cheio" style="width:{pct}%"></div><div class="ponto" style="left:{pct}%"></div></div>'
        out.append(parte + fio)
    out.append(partes[-1])
    return "</section>".join(out)


MARCACAO_ACEITA = re.compile(r"</?b>", re.I)


def marcacao_no_texto(k):
    """[(caminho, trecho)] dos textos do kit com marcação HTML além de <b> e </b>. O template põe o texto cru na página
    (o negrito precisa disso) e o Chromium do render roda com JavaScript e lê arquivo local: um <img src=file://...> num
    texto colado do cliente embutiria um arquivo do Mac no PDF, e um <script> rodaria (revisão de segurança, 09/10)."""
    achados = []

    def andar(o, caminho):
        if isinstance(o, dict):
            for kk, v in o.items():
                andar(v, f"{caminho}.{kk}" if caminho else kk)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                andar(v, f"{caminho}[{i}]")
        elif isinstance(o, str) and "<" in MARCACAO_ACEITA.sub("", o):
            achados.append((caminho, o[:80]))
    andar(k, "")
    return achados


HEX = re.compile(r"#[0-9A-Fa-f]{6}")
NOME_FONTE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,63}")
ID_RECEITA = re.compile(r"[a-z0-9][a-z0-9-]{0,31}")
FOCO = re.compile(r"(?:\d{1,3}(?:\.\d+)?%|left|right|center|top|bottom)(?: (?:\d{1,3}(?:\.\d+)?%|left|right|center|top|bottom))?")


def valores_fora_do_formato(k):
    """Valores do kit que o template põe DENTRO de atributo HTML ou de CSS (foco da foto, cores, fontes, id e paleta da
    receita, escala do gráfico, porcentagem de gênero, posição de objeto). O filtro de marcação só olha o "<"; aqui uma
    aspa ou um `url(` fugiria do atributo ou do CSS sem nenhum "<" (achado da revisão de segurança de 09/10). Cada valor
    tem formato fechado; o que não casa, o render recusa."""
    erros = []

    def confere(caminho, valor, padrao, descricao):
        if valor is not None and not (isinstance(valor, str) and padrao.fullmatch(valor)):
            erros.append(f"{caminho} = {str(valor)[:60]!r} (esperado {descricao})")

    def numero(caminho, valor):
        if valor is not None and (isinstance(valor, bool) or not isinstance(valor, (int, float))):
            erros.append(f"{caminho} = {str(valor)[:60]!r} (esperado número)")
    m = k.get("marca") or {}
    for c in ("cor_primaria", "cor_fundo_escuro", "cor_secundaria"):
        confere(f"marca.{c}", m.get(c), HEX, "cor #RRGGBB")
    for c in ("fonte_display", "fonte_titulo", "fonte_corpo"):
        confere(f"marca.{c}", m.get(c), NOME_FONTE, "nome de fonte: letras, números, espaço, ponto, hífen")
    numero("marca.peso_display", m.get("peso_display"))
    if m.get("direcao") is not None and m.get("direcao") not in DIRECOES:
        erros.append(f"marca.direcao = {str(m.get('direcao'))[:40]!r} (esperado {', '.join(DIRECOES)})")
    for i, r in enumerate(k.get("receitas") or []):
        confere(f"receitas[{i}].id", r.get("id"), ID_RECEITA, "id: a-z, 0-9 e hífen")
        for c, cor in (r.get("paleta") or {}).items():
            confere(f"receitas[{i}].paleta.{c}", cor, HEX, "cor #RRGGBB")
        for c in ("display", "titulo", "corpo", "lettering"):
            confere(f"receitas[{i}].fontes.{c}", (r.get("fontes") or {}).get(c), NOME_FONTE, "nome de fonte")
        numero(f"receitas[{i}].fontes.peso_display", (r.get("fontes") or {}).get("peso_display"))
    for i, a in enumerate(k.get("acervo") or []):
        confere(f"acervo[{i}].foco", a.get("foco"), FOCO, "posição da foto: '50% 40%' ou palavras como 'center top'")
    for i, g in enumerate(k.get("graficos") or []):
        if g.get("escala") is not None and g.get("escala") not in ("log", "linear"):
            erros.append(f"graficos[{i}].escala = {str(g.get('escala'))[:40]!r} (esperado log ou linear)")
    for i, g in enumerate((k.get("publico") or {}).get("genero") or []):
        numero(f"publico.genero[{i}].pct", g.get("pct"))
    for i, o in enumerate(k.get("objetos") or []):
        for c in ("x", "y", "w", "divisa_px"):
            numero(f"objetos[{i}].{c}", o.get(c))
    return erros


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--direcao", default=None)
    ap.add_argument("--todas", action="store_true", help="renderiza as três direções")
    ap.add_argument("--receita", default=None, help="com `receitas` no JSON: renderiza só esta receita (id)")
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--sem-vertical", action="store_true")
    ap.add_argument("--fundo", action="store_true", help="renderiza também a versão sem texto (fundo para PPTX editável)")
    ap.add_argument("--fontes", default=None, help="pasta com .otf/.ttf/.woff2; cada arquivo vira @font-face com o nome do arquivo (padrão: pipeline/assets/fonts)")
    ap.add_argument("--maquete", action="store_true", help="caixas rotuladas no lugar de cada elemento planejado (planejar antes de gerar)")
    args = ap.parse_args()

    pasta = Path(args.pasta).resolve()
    global pasta_global; pasta_global = pasta
    k = json.loads((pasta / "mediakit.json").read_text(encoding="utf-8"))
    ruins = marcacao_no_texto(k)
    if ruins:
        raise SystemExit("o render recusa texto com marcação HTML (só <b>negrito</b> vale; o resto rodaria no navegador do "
                         "render): " + "; ".join(f"{c}: {t!r}" for c, t in ruins[:5]))
    fora = valores_fora_do_formato(k)
    if fora:
        raise SystemExit("o render recusa valor fora do formato num campo que vai para atributo ou CSS (uma aspa ou um url( "
                         "fugiria da página): " + "; ".join(fora[:6]))
    saida = pasta / "saida"; (saida / "html").mkdir(parents=True, exist_ok=True)
    report = {"avisos": [], "direcoes": {}}
    acervo = carregar_acervo(k, pasta, report)
    paginas = montar_paginas(k, acervo, report)
    pedido = k.get("paginas")
    if pedido:
        paginas = filtrar_paginas(paginas, pedido, report)
        report["piloto"] = True
    report["sequencia"] = [p["tipo"] for p in paginas]
    report["pageplan"] = plano_report(paginas)
    grao_p = AQUI / "assets" / "grao.png"
    grao = data_uri(grao_p) if grao_p.exists() else "none"
    fdir = Path(args.fontes) if args.fontes else AQUI / "assets" / "fonts"
    elementos = sistema_elementos.Elementos(k, pasta, report, fdir) if sistema_elementos.ativo(k) else None
    if args.maquete and not elementos:
        sys.exit("--maquete precisa de `composicao`, `elementos` ou `sistema_elementos` no mediakit.json")

    env = Environment(loader=FileSystemLoader(AQUI / "templates"), undefined=ChainableUndefined, autoescape=False)
    # 36-elementos.css (camadas dos elementos) só entra em kit com elementos e 37-acabamento.css (grão, luz e fonte do
    # lettering) só em kit que declara a camada de acabamento: o HTML do legado continua byte a byte igual
    acab = declara_acabamento(k)
    css = "\n".join(f.read_text(encoding="utf-8") for f in sorted((AQUI / "tema").glob("*.css"))
                    if (elementos or f.name != "36-elementos.css") and (acab or f.name != "37-acabamento.css"))
    if (pasta / "tema-projeto.css").exists():
        css += "\n/* tema-projeto.css */\n" + (pasta / "tema-projeto.css").read_text(encoding="utf-8")
    faces = []
    if fdir.exists():
        for f in sorted(fdir.iterdir()):
            if f.suffix.lower() in (".otf", ".ttf", ".woff2", ".woff"):
                fmt = {".otf": "opentype", ".ttf": "truetype", ".woff2": "woff2", ".woff": "woff"}[f.suffix.lower()]
                # "Familia__700.ttf" = peso 700 da família "Familia"; sem sufixo, o arquivo cobre todos os pesos
                fam, _, peso = f.stem.partition("__")
                peso = peso if peso.isdigit() else "100 900"
                faces.append(f"@font-face {{ font-family: '{fam}'; src: url({data_uri(f)}) format('{fmt}'); font-display: block; font-weight: {peso}; font-style: normal; }}")
    css = "\n".join(faces) + "\n" + css
    report["fontes_dir"] = str(fdir.resolve()) if fdir.exists() else None  # o qa.py confere a cobertura de glifos nestes arquivos
    report["fontes_carregadas"] = sorted({f.stem.partition("__")[0] for f in fdir.iterdir() if f.suffix.lower() in (".otf", ".ttf", ".woff2", ".woff")}) if fdir.exists() else []
    ctx = dict(k=k, data_fmt=fmt_data(k["evento"]["data_inicio"]), css=css, grao=grao)

    # alvos: as direções antigas, ou uma receita por kit (frente 4). --direcao/--todas explícitos forçam as direções.
    receitas = k.get("receitas") or []
    base_dir = k["marca"].get("direcao", "causa")
    if receitas and not (args.direcao or args.todas):
        if args.receita:
            receitas = [r for r in receitas if r.get("id") == args.receita]
            if not receitas:
                sys.exit(f"receita `{args.receita}` não existe no mediakit.json")
        alvos = []
        for r in receitas:
            falta = familias_faltando(r, fdir)
            if falta:
                msg = f"receita {r['id']}: família sem arquivo em --fontes: {', '.join(falta)} (vai cair em fallback e o QA reprova)"
                print(f"  AVISO {msg}"); report["avisos"].append(msg)
            if r.get("fundo", "escuro") not in FUNDOS:
                report["avisos"].append(f"receita {r['id']}: fundo `{r.get('fundo')}` inválido; fica escuro")
            if r.get("mascara", "reto") not in MASCARAS:
                report["avisos"].append(f"receita {r['id']}: máscara `{r.get('mascara')}` inválida; fica reto")
            pags = aplicar_receita(montar_paginas(k, acervo, {"avisos": []}), r, report)
            if pedido:
                pags = filtrar_paginas(pags, pedido, {"avisos": []})
            alvos.append((r["id"], base_dir, r, pags, (r.get("paleta") or {}).get("marca") or k["marca"].get("cor_primaria", "#E8307A")))
        report["receitas"] = {r["id"]: r for r in receitas}
    else:
        direcoes = DIRECOES if args.todas else [args.direcao or base_dir]
        alvos = [(d, d, None, paginas, k["marca"].get("cor_primaria", "#E8307A")) for d in direcoes]

    for d, direcao, receita, pags, marca in alvos:
        fundo = (receita or {}).get("fundo", "escuro") if receita else None
        fundo = fundo if fundo in FUNDOS else ("escuro" if receita else None)
        mascara = (receita or {}).get("mascara", "reto") if receita else None
        mascara = mascara if mascara in MASCARAS else ("reto" if receita else None)
        camadas = receita is not None or elementos is not None
        for p in pags:
            p["plano"] = e_plano(p) if receita else False
            if acab:
                p["_acab"] = acabamento_da_pagina(k, p)
                fora_acab = [f"{c}={p['_acab'][c]!r}" for c in ("grao", "luz") if c in p["_acab"] and p["_acab"][c] not in ACAB_PAGINA[c]]
                if fora_acab:
                    report["avisos"].append(f"{d} {p['tipo']}: acabamento fora do vocabulário ({', '.join(fora_acab)}): ignorado")
        rx = dict(receita=receita, receita_css=css_receita(receita) if receita else None, fundo=fundo, mascara=mascara)
        def montar(sem_texto):
            h = env.get_template("kit.html").render(direcao=direcao, sem_texto=sem_texto, paginas=pags, **rx, **ctx)
            if camadas:
                h = injetar_camadas(h, pags, fundo)
            if k["marca"].get("assinatura", "fio") == "fio":
                h = injetar_fio(h, pags)
            return h
        base_nome = f"maquete-{d}" if args.maquete else f"kit-{d}"
        html_h = saida / "html" / f"{base_nome}.html"
        if elementos:  # duas passagens: mede sem elementos, resolve os encaixes, injeta e exporta (camadas.py)
            m = elementos.exportar(d, receita, pags, montar(False), html_h, saida / f"{base_nome}.pdf", 1920, 1080,
                                   saida / "png" if (args.png or args.maquete) else None, base_nome, marca, exportar,
                                   maquete=args.maquete)
        else:
            html_h.write_text(montar(False), encoding="utf-8")
            m = exportar(html_h, saida / f"kit-{d}.pdf", 1920, 1080, saida / "png" if args.png else None, f"kit-{d}", marca)
        report["direcoes"][d] = {"horizontal": m}
        if receita:
            report["direcoes"][d].update(receita=receita["id"], tom=direcao, sequencia=[p["tipo"] for p in pags],
                                         pageplan=plano_report(pags), paginas=paginas_report(pags))
        elif elementos:
            report["direcoes"][d]["paginas"] = paginas_report(pags)
        if args.fundo and not args.maquete:
            html_f = saida / "html" / f"kit-{d}-fundo.html"
            h_f = montar(True)
            html_f.write_text(elementos.injetar_fundo(d, h_f) if elementos else h_f, encoding="utf-8")
            exportar(html_f, saida / f"kit-{d}-fundo.pdf", 1920, 1080, saida / "fundo", f"kit-{d}", marca)
        print(f"OK  {base_nome}.pdf  ({m['paginas']} páginas)" + (f"  receita {receita.get('nome', d)}: fundo {fundo}, máscara {mascara}" if receita else ""))
        for a in m["ajustes"]:
            if a["passos"] or a["zoom"] != 1:
                print(f"  ajuste p.{a['pagina']}: {a['fonte_inicial']:.0f}→{a['fonte_final']:.0f}px zoom={a['zoom']}  {a['texto'][:50]!r}")
        for pp in m["por_pagina"]:
            for t in pp["fora_da_pagina"]:
                print(f"  FORA p.{pp['pagina']}: {t!r}")
        ruins = [f for f, ok in m["fontes"].items() if not ok]
        if ruins:
            print(f"  FONTE AUSENTE: {', '.join(ruins)} (render com fallback: não mostrar como resultado)")
        if not args.sem_vertical and (AQUI / "templates" / "vertical.html").exists():
            html_v = saida / "html" / f"{base_nome}-vertical.html"
            h_v = env.get_template("vertical.html").render(direcao=direcao, paginas=pags, **rx, **ctx)
            if elementos:  # o vertical recebe os elementos com encaixes próprios (canto e faixa)
                report["direcoes"][d]["vertical"] = elementos.exportar(d, receita, pags, h_v, html_v, saida / f"{base_nome}-vertical.pdf", 1080, 1920,
                                                                       saida / "png" if (args.png or args.maquete) else None, f"{base_nome}-vertical", marca, exportar,
                                                                       formato="vertical", maquete=args.maquete)
            else:
                html_v.write_text(h_v, encoding="utf-8")
                report["direcoes"][d]["vertical"] = exportar(html_v, saida / f"kit-{d}-vertical.pdf", 1080, 1920, saida / "png" if args.png else None, f"kit-{d}-vertical", marca)
        if elementos:
            report["direcoes"][d]["elementos"] = elementos.resumos.get(d)

    if args.maquete:
        # a maquete não é o kit: o render-report.json (que o qa.py e o contact_sheet leem) continua sendo o do último render
        for w in report["avisos"]:
            print(f"  aviso: {w}")
        return
    (saida / "render-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("sequência:", " → ".join(f"{p['tipo']}({p['peso']})" for p in report["pageplan"]))
    for w in report["avisos"]:
        print(f"  aviso: {w}")


if __name__ == "__main__":
    main()

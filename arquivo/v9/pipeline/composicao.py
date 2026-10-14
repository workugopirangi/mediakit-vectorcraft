#!/usr/bin/env python3
"""
composicao.py: a composição da página, escrita ANTES de buscar ou gerar qualquer elemento (processo em
references/09-composicao.md; contrato em schema/elementos.schema.json#/definitions/composicao).

O Claude escreve em mediakit.json → "composicao", por rótulo de página:
  "composicao": {
    "<rótulo>": {
      "mensagem": "o que a página diz, numa frase",
      "foco": "titulo|numero|preco|foto|objeto|lettering|grafico",
      "leitura": ["numero", "titulo", "lista"],          ordem dos olhos
      "estrutura": "número sangrando à esquerda, lista na coluna 8",
      "padroes": ["numero-que-sangra"],                   ids do repertório consultados
      "porque_fora_da_gramatica": "...",                  quando a página foge da relação-mãe do tipo
      "sem": ["constante-selo", "pattern"],              constante ou pattern que sai desta página
      "elementos": [
        {"id": "bola", "papel": "heroi", "funcao": "profundidade", "camada": "frente",
         "ancora": {"relacao": "sobrepoe", "alvo": "foto", "lado": "esq", "fracao": "1/3", "y": "base=foto.base-e5"},
         "escala": {"altura": "1/3p"}, "porque": "a bola sai da foto em direção ao título"},
        {"id": "fio-titulo", "grafismo": {"tipo": "faixa-diagonal", "params": {...}}, "papel": "estrutura", ...}]}}

Rótulo: o do tipo ("ativo", "cota", "capa") vale para todas as páginas daquele tipo e é a GRAMÁTICA dele; o da variante
("cota:b", "ativo:painel") e o da página ("ativo:2", "cota:Master") vencem, nessa ordem. A vertical só usa "vertical:*".

Âncora, sempre nos dois eixos e com pelo menos um eixo numa linha de CONTEÚDO (título, número, foto, bloco), exceto a
função acabamento, que pode ancorar só em margem, página ou coluna:
  alinha    "x": "<borda>=<alvo>.<borda>[±desloc]", "y": idem. Bordas x: esq dir cx; y: topo base cy linha_base cap.
            Ex.: "linha_base=titulo.linha_base", "esq=coluna:8.esq", "dir=margem.dir-e5", "topo=titulo.l2.cap".
  sangra    "borda": esq|dir|topo|base, "corte": 1/4|1/3|1/2 da tinta para fora da página, + o outro eixo.
  sobrepoe  "alvo", "lado": esq|dir|topo|base, "fracao": 1/4|1/3|1/2 da tinta DENTRO do alvo, + o outro eixo.
  liga      linha ou moldura presa a alvos, gerada DEPOIS de resolver a geometria (grafismo `fio`, `colchetes`, `moldura`):
            conecta   "de" e "para" = "<alvo>[.lN].<borda>[±desloc]" (a borda e o centro do outro eixo) ou
                      "<alvo>.<borda_x>.<borda_y>" (um canto); fio de um ponto ao outro.
            emoldura  "alvo" + "folga" (e1..e8 ou px): colchetes (ou moldura, se grafismo.tipo pedir) na caixa do alvo
                      inflada pela folga. Alvo de texto: das bordas das linhas, do cap da 1ª à linha de base da última.
            separa    "entre" = bloco de lista (lista-num, direitos, direitos-2col, inv-colunas, cards, caixas4): um fio
                      por divisória, cada um item próprio (<id>-s1, <id>-s2...), porque o `fio` do contrato é UMA
                      polilinha. Itens empilhados: fio horizontal no meio do vão; itens lado a lado numa linha só: vertical.
            continua  "de_foto" [u, v] em fração da IMAGEM (0 a 1), levado à página pelo object-fit + object-position da
                      foto ("alvo", padrão `foto`); "angulo" em graus (0 = para a direita, 90 = para cima); "ate" =
                      "<alvo>.<borda>" ou "pagina.<borda>": fio do ponto até onde a reta cruza essa borda do alvo.
            "espessura" (px) vale para o traço; o resto dos parâmetros vem de grafismo.params.
  registro  (mk-2.1) "alvo": "foto". O recorte da própria foto (PNG de elementos[] na proporção da foto, qualquer
            resolução) volta ao lugar exato em que está nela: a caixa é a da imagem desenhada pelo object-fit +
            object-position medidos (a mesma conta de `ponto_da_foto`), sem eixo nem escala. A parte que o object-fit
            cortou fica fora (o item ganha `recorte`, o render aplica clip-path inset).
Deslocamento em degraus da escala de espaço (e1..e8 = 8, 16, 24, 32, 48, 64, 96, 128 px) ou em px.
Escala, uma dimensão da TINTA (a outra segue o aspecto): {"altura": "1/3p"} (fração da página: 1/6 1/4 1/3 1/2 2/3 3/4
1), {"largura": "4col"} (colunas de 128 + calhas), {"altura": "3cap", "de": "titulo"} (altura de maiúscula do alvo).
Número em px é aceito e o QA avisa (fora do degrau). Grafismo ancorado com escala é GERADO na medida da colocação
(params ganha `largura` ou `altura`), não esticado: resolver, gerar, posicionar.

Tinta = a área com alfa ≥ 128 (contrato do QA e do alinhamento): é ela que encosta na linha, não a franja
semitransparente do PNG. O item devolvido continua sendo a caixa do PNG de uso (alfa > 8, a que o render desenha).
"""
import json, math, re
from fractions import Fraction
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SCHEMA = AQUI.parent / "schema" / "elementos.schema.json"

FUNCOES = ("foco", "contexto", "identidade", "conexao", "organizacao", "profundidade", "equilibrio", "acabamento")
RELACOES = ("alinha", "sangra", "sobrepoe", "liga")
REGISTRO = "registro"                            # âncora da camada de acabamento (mk-2.1): fora de RELACOES, que é também
                                                 # o vocabulário do repertório (repertorio.py), que não a conhece
TOL_PROPORCAO = 0.01                             # registro: o recorte tem a proporção da foto (1%)
EFEITO_ITEM = ("efeito", "motivo", "recurso")    # o que a composição declara e o item leva ao plano (mk-2.1)
PAPEIS = ("heroi", "apoio", "estrutura")
CAMADAS = ("atras", "frente", "sob-veu")
BORDAS_X = ("esq", "dir", "cx")
BORDAS_Y = ("topo", "base", "cy", "linha_base", "cap")
ESPACO = {"e1": 8, "e2": 16, "e3": 24, "e4": 32, "e5": 48, "e6": 64, "e7": 96, "e8": 128}
DEGRAUS_FRACAO = ("1/4", "1/3", "1/2")
DEGRAUS_PAGINA = ("1/6", "1/4", "1/3", "1/2", "2/3", "3/4", "1")
ESTRUTURAIS = ("pagina", "margem", "coluna")     # alvos que não são conteúdo
LIMIAR_TINTA = 127                               # alfa >= 128
MODOS_LIGA = ("conecta", "emoldura", "separa", "continua")
TIPO_LIGA = {"conecta": "fio", "separa": "fio", "continua": "fio", "emoldura": "colchetes"}
# blocos de lista que o render mede com `itens` (caixa de cada item) e o nome do item que aponta para o bloco
BLOCOS_LISTA = ("lista-num", "direitos", "direitos-2col", "inv-colunas", "cards", "caixas4")
BLOCO_DO_ITEM = {"card": "cards", "caixa-num": "caixas4", "inv-item": "inv-colunas"}
ESPESSURA_PADRAO = 2.0
TOLERANCIA = 2.0                                 # px: âncora cumprida (QA)

_ALVO = r"[a-z][a-z0-9-]*(?::[A-Za-z0-9_À-ÿ-]+)?"
_BORDA = r"(?:esq|dir|cx|topo|base|cy|linha_base|cap)"
_DESL = r"(?:([+-])(e[1-8]|\d+(?:\.\d+)?))?"
_RESTR = re.compile(rf"^(esq|dir|cx|topo|base|cy|linha_base|cap)=({_ALVO})(?:\.l(\d+))?\.(esq|dir|cx|topo|base|cy|linha_base|cap)"
                    r"(?:([+-])(e[1-8]|\d+(?:\.\d+)?))?$")
_PONTO = re.compile(rf"^({_ALVO})(?:\.l(\d+))?\.({_BORDA})(?:\.({_BORDA}))?{_DESL}$")


class ErroComposicao(ValueError):
    """Composição que não resolve: alvo ausente, restrição inválida, eixo trocado. Vira FALHA no QA."""


# ------------------------------------------------------------------------------------------------- restrições
def eixo(borda):
    return "x" if borda in BORDAS_X else "y"


def parse_restricao(s):
    """'linha_base=titulo.l2.linha_base-e3' -> (borda_el, alvo, linha|None, borda_alvo, deslocamento_px)."""
    m = _RESTR.match((s or "").strip())
    if not m:
        raise ErroComposicao(f"restrição inválida `{s}` (formato: <borda>=<alvo>[.lN].<borda>[±e1..e8|±px])")
    b_el, alvo, linha, b_alvo, sinal, d = m.groups()
    if eixo(b_el) != eixo(b_alvo):
        raise ErroComposicao(f"restrição `{s}` mistura eixos ({b_el} é {eixo(b_el)}, {b_alvo} é {eixo(b_alvo)})")
    desl = 0.0
    if d:
        desl = float(ESPACO[d]) if d in ESPACO else float(d)
        desl = -desl if sinal == "-" else desl
    return b_el, alvo, (int(linha) if linha else None), b_alvo, desl


def alvo_estrutural(nome):
    return nome.split(":", 1)[0] in ESTRUTURAIS


def caixa_alvo(alvos, nome):
    """Caixa {x, y, w, h[, linhas]} do alvo medido na página. Coluna N (1-based) vem de alvos['colunas']."""
    if nome.startswith("coluna:"):
        try:
            c = alvos["colunas"][int(nome.split(":", 1)[1]) - 1]
        except (KeyError, IndexError, ValueError):
            raise ErroComposicao(f"alvo `{nome}` ausente (a página tem {len(alvos.get('colunas') or [])} colunas)")
        return {"x": c["x"], "y": alvos["margem"]["y"], "w": c["w"], "h": alvos["margem"]["h"]}
    a = alvos.get(nome)
    if not isinstance(a, dict):
        perto = sorted(k for k in alvos if k.split(":")[0] == nome.split(":")[0])
        raise ErroComposicao(f"alvo `{nome}` ausente na página" + (f" (há: {', '.join(perto)})" if perto else ""))
    return a


def valor_alvo(alvos, nome, linha, borda):
    a = caixa_alvo(alvos, nome)
    if linha is not None:
        ls = a.get("linhas") or []
        if not 1 <= linha <= len(ls):
            raise ErroComposicao(f"`{nome}.l{linha}`: o alvo tem {len(ls)} linha(s)")
        a = ls[linha - 1]
    if borda in ("linha_base", "cap"):
        ls = a.get("linhas")
        if linha is None and ls:
            # sem linha explícita: a base é a da ÚLTIMA linha (onde o texto assenta); o cap, o da PRIMEIRA
            a = ls[-1] if borda == "linha_base" else ls[0]
        if borda not in a:
            raise ErroComposicao(f"`{nome}` não é texto: não tem {borda}")
        return float(a[borda])
    x, y, w, h = float(a["x"]), float(a["y"]), float(a["w"]), float(a["h"])
    return {"esq": x, "dir": x + w, "cx": x + w / 2, "topo": y, "base": y + h, "cy": y + h / 2}[borda]


# ------------------------------------------------------------------------------------------------- escala
def _fracao(s, permitidos):
    if s not in permitidos:
        raise ErroComposicao(f"`{s}` fora dos degraus ({', '.join(permitidos)})")
    return float(Fraction(s))


def px_escala(escala, alvos, W, H):
    """(dimensão, px, degrau) da escala declarada: a medida da TINTA naquela dimensão ('altura' ou 'largura').
    degrau False quando veio em px solto (o QA avisa)."""
    if not escala:
        raise ErroComposicao("elemento sem `escala` (altura ou largura, em degrau)")
    if len([k for k in ("altura", "largura") if k in escala]) != 1:
        raise ErroComposicao("`escala` tem de ter exatamente uma dimensão: altura ou largura")
    dim = "altura" if "altura" in escala else "largura"
    v = escala[dim]
    total = H if dim == "altura" else W
    degrau = True
    if isinstance(v, (int, float)):
        px, degrau = float(v), False
    elif isinstance(v, str) and v.endswith("cap"):
        # antes de "p": "3cap" também termina em p
        n = int(v[:-3]); de = escala.get("de") or "titulo"
        a = caixa_alvo(alvos, de)
        ls = a.get("linhas") or []
        if not ls or "cap" not in ls[0]:
            raise ErroComposicao(f"escala `{v}`: `{de}` não é texto (sem altura de maiúscula)")
        px = n * (float(ls[0]["linha_base"]) - float(ls[0]["cap"]))
    elif isinstance(v, str) and v.endswith("col"):
        n = int(v[:-3]); colunas = alvos.get("colunas") or []
        if not 1 <= n <= max(1, len(colunas)):
            raise ErroComposicao(f"escala `{v}`: a página tem {len(colunas)} colunas")
        px = colunas[n - 1]["x"] + colunas[n - 1]["w"] - colunas[0]["x"]
    elif isinstance(v, str) and v.endswith("p"):
        px = total * _fracao(v[:-1], DEGRAUS_PAGINA)
    else:
        raise ErroComposicao(f"escala `{v}` inválida (use 1/3p, 4col, 3cap ou px)")
    return dim, px, degrau


def tamanho_tinta(escala, tw0, th0, alvos, W, H):
    """Tamanho (w, h) da TINTA na página a partir da escala declarada; a outra dimensão segue o aspecto da tinta.
    Devolve (w, h, degrau): degrau False quando veio em px solto (o QA avisa)."""
    dim, px, degrau = px_escala(escala, alvos, W, H)
    if dim == "altura":
        return px * tw0 / th0, px, degrau
    return px, px * th0 / tw0, degrau


# ------------------------------------------------------------------------------------------------- geometria
def _offsets_tinta(tinta_rel, w, h, rot):
    """Offsets da caixa (alinhada aos eixos) da tinta girada, relativos ao centro do item: (esq, dir, topo, base)."""
    x0, y0, x1, y1 = tinta_rel
    cx, cy = w / 2, h / 2
    r = math.radians(rot or 0)
    c, s = math.cos(r), math.sin(r)
    xs, ys = [], []
    for px, py in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        dx, dy = px - cx, py - cy
        xs.append(dx * c - dy * s); ys.append(dx * s + dy * c)
    return min(xs), max(xs), min(ys), max(ys)


def _centro_por(borda, alvo_v, off, linhas_el=None, h=0.0):
    """Coordenada do centro do item para que a borda `borda` da tinta caia em `alvo_v`."""
    e, d, t, b = off
    if borda == "esq": return alvo_v - e
    if borda == "dir": return alvo_v - d
    if borda == "cx": return alvo_v - (e + d) / 2
    if borda == "topo": return alvo_v - t
    if borda == "base": return alvo_v - b
    if borda == "cy": return alvo_v - (t + b) / 2
    if borda in ("linha_base", "cap"):
        if not linhas_el or borda not in linhas_el:
            raise ErroComposicao(f"o elemento não tem {borda} própria (só grafismo com texto declara)")
        return alvo_v - (float(linhas_el[borda]) - h / 2)
    raise ErroComposicao(f"borda `{borda}`")


def resolver(a, dims, med):
    """Item {id, papel, encaixe: 'composicao', camada, x, y, w, h, rot, ...} para um atribuído com `ancora`, ou levanta
    ErroComposicao. dims = (W0, H0, alfa_bbox) do elemento; a pode trazer `tinta_bbox` (px da origem), `linhas`
    (grafismo: {'linha_base': y} na caixa) e `espelhar`. med = medidas da página com `alvos`, `w`, `h` e, para gerar
    grafismo na medida da colocação, `gerar_grafismo(tipo, params) -> dict` (contrato do grafismos.gerar).
    `liga` no modo separa devolve vários itens: use resolver_itens."""
    its = resolver_itens(a, dims, med)
    if len(its) != 1:
        raise ErroComposicao(f"`{a['id']}`: a âncora gera {len(its)} itens (liga separa); use resolver_itens")
    return its[0]


def resolver_itens(a, dims, med):
    """Lista de itens de um atribuído ancorado (um só, menos `liga` separa: um por divisória). Ordem para grafismo:
    resolver a geometria, GERAR com ela (não esticar), posicionar."""
    anc = a.get("ancora") or {}
    rel = anc.get("relacao")
    if rel == REGISTRO:
        return [_registro(a, dims, med)]
    if rel not in RELACOES:
        raise ErroComposicao(f"`{a['id']}`: relação `{rel}` fora do vocabulário ({', '.join(RELACOES + (REGISTRO,))})")
    if rel == "liga":
        return _liga(a, med)
    gerar = med.get("gerar_grafismo")
    if a.get("_grafismo") and gerar and a.get("escala"):
        return [_grafismo_na_medida(a, med, gerar)]
    if not dims:
        planejado = " (asset planejado em `proporcao`: gere o asset; a maquete é que desenha sem ele)" if a.get("proporcao") else ""
        raise ErroComposicao(f"`{a['id']}`: sem asset para posicionar (arquivo ausente ou grafismo que não gerou){planejado}")
    return [_ancorar(a, dims, med)]


def _grafismo_na_medida(a, med, gerar):
    """Grafismo ancorado com escala: a escala diz a medida da TINTA; o svg é gerado com `largura`/`altura` dessa
    medida e entra na escala 1 (texto vivo e traço na espessura certa, sem esticar). Se o gerador devolve `tinta`
    menor que a caixa, uma correção: pede a caixa que faz a tinta medir o que a escala manda. Gerador que não honra o
    parâmetro sai esticado e marcado (`ancora.medida` = 'esticada'), para o QA avisar."""
    W, H = float(med.get("w", 1920)), float(med.get("h", 1080))
    dim, px, degrau = px_escala(a["escala"], med.get("alvos") or {}, W, H)
    tipo, base = a["_grafismo"]["tipo"], dict(a["_grafismo"].get("params") or {})
    cx = "w" if dim == "largura" else "h"

    def tinta_dim(g):
        t = g.get("tinta")
        if t:
            return float(t[2] - t[0]) if dim == "largura" else float(t[3] - t[1])
        return float(g[cx])

    try:
        params = dict(base, **{dim: round(px, 2)})
        g = gerar(tipo, params)
        t = tinta_dim(g)
        if t > 0 and abs(t - px) > 0.5 and g.get("tinta"):
            params = dict(base, **{dim: round(px * float(g[cx]) / t, 2)})
            g = gerar(tipo, params)
            t = tinta_dim(g)
    except (ValueError, NotImplementedError) as e:
        raise ErroComposicao(f"`{a['id']}`: grafismo `{tipo}` não gerou na medida {dim}={px:.0f}: {e}")
    if t <= 0:
        raise ErroComposicao(f"`{a['id']}`: grafismo `{tipo}` sem tinta")
    s = 1.0 if abs(t - px) <= 1.0 else px / t
    a2 = dict(a, tinta_bbox=g.get("tinta"), linhas=g.get("linhas"))
    item = _ancorar(a2, (float(g["w"]), float(g["h"]), None), med, s_fixo=s, degrau_fixo=degrau)
    item["ancora"]["medida"] = "gerada" if s == 1.0 else "esticada"
    item["grafismo"] = {"tipo": tipo, "params": params}
    item["_svg"] = g
    return item


def _ancorar(a, dims, med, s_fixo=None, degrau_fixo=True):
    """alinha, sangra e sobrepoe: posição E tamanho pela tinta. s_fixo: escala já decidida (grafismo gerado na
    medida, s = 1); `tamanho_natural` sem escala (constante com âncora): s = 1."""
    W, H = float(med.get("w", 1920)), float(med.get("h", 1080))
    alvos = med.get("alvos") or {}
    anc = a.get("ancora") or {}
    rel = anc.get("relacao")
    W0, H0, bbox = dims
    ab = bbox or (0, 0, W0, H0)
    tb = a.get("tinta_bbox") or ab
    tb = (max(tb[0], ab[0]), max(tb[1], ab[1]), min(tb[2], ab[2]), min(tb[3], ab[3]))
    if a.get("espelhar"):
        # espelhado na horizontal dentro da caixa do PNG de uso
        tb = (ab[0] + ab[2] - tb[2], tb[1], ab[0] + ab[2] - tb[0], tb[3])
    tw0, th0 = tb[2] - tb[0], tb[3] - tb[1]
    if tw0 <= 0 or th0 <= 0:
        raise ErroComposicao(f"`{a['id']}`: elemento sem tinta (alfa ≥ 128)")
    if s_fixo is not None:
        s, degrau = float(s_fixo), degrau_fixo
    elif a.get("escala") is None and a.get("tamanho_natural"):
        s, degrau = 1.0, True                     # constante: nasce no tamanho do encaixe, a âncora só posiciona
    else:
        tw, th, degrau = tamanho_tinta(a.get("escala"), tw0, th0, alvos, W, H)
        s = tw / tw0
    w, h = (ab[2] - ab[0]) * s, (ab[3] - ab[1]) * s                    # caixa do PNG de uso na página
    tinta_rel = ((tb[0] - ab[0]) * s, (tb[1] - ab[1]) * s, (tb[2] - ab[0]) * s, (tb[3] - ab[1]) * s)
    rot = float(a.get("rot") or 0)
    off = _offsets_tinta(tinta_rel, w, h, rot)
    linhas_el = None
    if a.get("linhas"):
        linhas_el = {k: float(v) * s for k, v in a["linhas"].items()}
        if rot:
            raise ErroComposicao(f"`{a['id']}`: linha_base própria com giro não é suportada")
    cx = cy = None
    restricoes = []

    def aplica(chave):
        nonlocal cx, cy
        txt = anc.get(chave)
        if not txt:
            raise ErroComposicao(f"`{a['id']}`: falta o eixo `{chave}` da âncora ({rel})")
        b_el, alvo, linha, b_alvo, desl = parse_restricao(txt)
        if eixo(b_el) != chave:
            raise ErroComposicao(f"`{a['id']}`: `{chave}` recebeu a restrição `{txt}`, que é do eixo {eixo(b_el)}")
        v = valor_alvo(alvos, alvo, linha, b_alvo) + desl
        c = _centro_por(b_el, v, off, linhas_el, h)
        if chave == "x": cx = c
        else: cy = c
        restricoes.append({"eixo": chave, "texto": txt, "alvo": alvo, "valor": round(v, 1)})

    if rel == "alinha":
        aplica("x"); aplica("y")
    elif rel == "sangra":
        borda = anc.get("borda")
        corte = _fracao(anc.get("corte"), DEGRAUS_FRACAO)
        e, d, t, b = off
        if borda == "dir": cx = W - (1 - corte) * (d - e) - e
        elif borda == "esq": cx = -corte * (d - e) - e
        elif borda == "topo": cy = -corte * (b - t) - t
        elif borda == "base": cy = H - (1 - corte) * (b - t) - t
        else: raise ErroComposicao(f"`{a['id']}`: sangra pede `borda` esq|dir|topo|base")
        restricoes.append({"eixo": "x" if borda in ("esq", "dir") else "y", "texto": f"sangra {borda} {anc.get('corte')}",
                           "alvo": "pagina", "valor": 0.0 if borda in ("esq", "topo") else (W if borda == "dir" else H)})
        aplica("y" if borda in ("esq", "dir") else "x")
    elif rel == "sobrepoe":
        nome, lado = anc.get("alvo"), anc.get("lado")
        fr = _fracao(anc.get("fracao"), DEGRAUS_FRACAO)
        e, d, t, b = off
        if lado in ("esq", "dir"):
            borda_v = valor_alvo(alvos, nome, None, lado)
            cx = (borda_v - (1 - fr) * (d - e) - e) if lado == "esq" else (borda_v - fr * (d - e) - e)
            restricoes.append({"eixo": "x", "texto": f"sobrepoe {nome}.{lado} {anc.get('fracao')}", "alvo": nome, "valor": round(borda_v, 1)})
            aplica("y")
        elif lado in ("topo", "base"):
            borda_v = valor_alvo(alvos, nome, None, lado)
            cy = (borda_v - (1 - fr) * (b - t) - t) if lado == "topo" else (borda_v - fr * (b - t) - t)
            restricoes.append({"eixo": "y", "texto": f"sobrepoe {nome}.{lado} {anc.get('fracao')}", "alvo": nome, "valor": round(borda_v, 1)})
            aplica("x")
        else:
            raise ErroComposicao(f"`{a['id']}`: sobrepoe pede `lado` esq|dir|topo|base")
    x, y = cx - w / 2, cy - h / 2
    e, d, t, b = off
    tinta = [round(cx + e, 1), round(cy + t, 1), round(cx + d, 1), round(cy + b, 1)]
    from encaixes import normalizar_papel
    item = {"id": a["id"], "papel": normalizar_papel(a.get("papel")), "encaixe": "composicao",
            "camada": a.get("camada") or "frente", "x": round(x, 1), "y": round(y, 1), "w": round(w, 1), "h": round(h, 1),
            "rot": rot, "origem": "composicao", "funcao": a.get("funcao"), "porque": a.get("porque"),
            "ancora": {"relacao": rel, "restricoes": restricoes, "tinta": tinta, "escala": a.get("escala"),
                       "degrau": degrau,
                       # o que foi declarado, para o QA recalcular contra os alvos do render FINAL
                       "declarada": dict(anc)}}
    if linhas_el:
        # linha de base e cap do próprio elemento (grafismo com texto), na página
        item["ancora"]["linhas"] = {k: round(cy - h / 2 + v, 1) for k, v in linhas_el.items()}
    if a.get("espelhar"):
        item["espelhar"] = True
    _levar_efeito(a, item)
    return item


def _levar_efeito(a, item):
    """efeito, motivo e recurso da composição (mk-2.1) seguem para o item: é dele que o render tira opacidade, blend,
    máscara, corte, sombra e reflexo, e o QA lê o mesmo dict. Só quando declarados: kit sem campo novo, plano igual."""
    for c in EFEITO_ITEM:
        if a.get(c) is not None:
            item[c] = a[c]
    return item


# ------------------------------------------------------------------------------------------------- registro
def retangulo_da_imagem(foto):
    """(x, y, w, h) na página da imagem INTEIRA desenhada na caixa da foto, pela regra do object-fit (cover, contain,
    fill, none, scale-down) e do object-position que o render mediu (alvo `foto` com `img`). Parte dela pode cair fora da
    caixa da foto (o cover corta): é a caixa da imagem, não a área visível."""
    img = foto.get("img") or {}
    nw, nh = float(img.get("nat_w") or 0), float(img.get("nat_h") or 0)
    if nw <= 0 or nh <= 0:
        raise ErroComposicao("a foto não tem o tamanho natural medido (img.nat_w, img.nat_h)")
    X, Y, Wc, Hc = float(foto["x"]), float(foto["y"]), float(foto["w"]), float(foto["h"])
    fit = (img.get("fit") or "cover").strip()
    if fit == "fill":
        rw, rh = Wc, Hc
    elif fit == "none":
        rw, rh = nw, nh
    else:
        s = max(Wc / nw, Hc / nh) if fit == "cover" else min(Wc / nw, Hc / nh)
        if fit == "scale-down":
            s = min(1.0, s)
        rw, rh = nw * s, nh * s
    ox, oy = _pos_objeto(img.get("pos"), Wc - rw, Hc - rh)
    return X + ox, Y + oy, rw, rh


def caixa_registro(foto, dims_png, caixa_px):
    """[x0, y0, x1, y1] na página de uma caixa em px do PNG do recorte (`caixa_px`), com o PNG (W0×H0) na proporção da
    foto e a imagem desenhada pelo object-fit. É a mesma conta para posicionar (resolver) e para conferir (QA)."""
    rx, ry, rw, rh = retangulo_da_imagem(foto)
    s = rw / float(dims_png[0])
    return [rx + caixa_px[0] * s, ry + caixa_px[1] * s, rx + caixa_px[2] * s, ry + caixa_px[3] * s]


def _registro(a, dims, med):
    """Âncora `registro`: o recorte da própria foto no lugar em que está nela. O PNG tem de ter a proporção da foto
    (é o recorte do mesmo enquadramento, em qualquer resolução); a escala é a da imagem desenhada (rw / largura do PNG).
    Sem eixo, sem escala, sem giro, sem espelho. O item é a área visível do PNG (alfa > 8, como todo item); a tinta, a
    do alfa >= 128; `ancora.caixa` é a imagem inteira desenhada (o QA confere contra a própria conta de object-fit)."""
    anc = a.get("ancora") or {}
    nome = anc.get("alvo") or "foto"
    if not dims:
        raise ErroComposicao(f"`{a['id']}`: registro sem asset para posicionar (o recorte da foto não existe em elementos[])")
    if a.get("rot") or a.get("espelhar"):
        raise ErroComposicao(f"`{a['id']}`: registro não gira nem espelha (o recorte fica onde está na foto)")
    alvos = med.get("alvos") or {}
    foto = caixa_alvo(alvos, nome)
    img = foto.get("img") or {}
    W0, H0, bbox = dims
    nw, nh = float(img.get("nat_w") or 0), float(img.get("nat_h") or 0)
    if nw <= 0 or nh <= 0:
        raise ErroComposicao(f"`{a['id']}`: registro em `{nome}`, que não é foto medida (sem img.nat_w e img.nat_h)")
    if abs((float(W0) / float(H0)) / (nw / nh) - 1) > TOL_PROPORCAO:
        raise ErroComposicao(f"`{a['id']}`: o recorte tem {W0:.0f}×{H0:.0f} px e a foto {nw:.0f}×{nh:.0f}: registro pede o "
                             f"recorte da própria foto, na mesma proporção (tolerância {TOL_PROPORCAO:.0%})")
    ab = bbox or (0, 0, W0, H0)
    tb = a.get("tinta_bbox") or ab
    tb = (max(tb[0], ab[0]), max(tb[1], ab[1]), min(tb[2], ab[2]), min(tb[3], ab[3]))
    if tb[2] <= tb[0] or tb[3] <= tb[1]:
        raise ErroComposicao(f"`{a['id']}`: elemento sem tinta (alfa ≥ 128)")
    rx, ry, rw, rh = retangulo_da_imagem(foto)
    x0, y0, x1, y1 = caixa_registro(foto, (W0, H0), ab)
    tinta = [round(v, 1) for v in caixa_registro(foto, (W0, H0), tb)]
    from encaixes import normalizar_papel
    item = {"id": a["id"], "papel": normalizar_papel(a.get("papel")), "encaixe": "composicao",
            "camada": a.get("camada") or "frente", "x": round(x0, 1), "y": round(y0, 1), "w": round(x1 - x0, 1),
            "h": round(y1 - y0, 1), "rot": 0.0, "origem": "composicao", "funcao": a.get("funcao"), "porque": a.get("porque"),
            "ancora": {"relacao": REGISTRO, "alvo": nome,
                       "restricoes": [{"eixo": "caixa", "texto": f"registro {nome}", "alvo": nome,
                                       "valor": [round(rx, 1), round(ry, 1), round(rw, 1), round(rh, 1)]}],
                       "tinta": tinta, "escala": None, "degrau": True, "declarada": dict(anc),
                       "caixa": [round(rx, 1), round(ry, 1), round(rw, 1), round(rh, 1)],
                       "registro": {"img": [W0, H0], "tinta_px": [float(v) for v in tb]}}}
    # o object-fit cortou parte da imagem: o pedaço do recorte que cai fora da área visível da foto não aparece
    X, Y, Wc, Hc = float(foto["x"]), float(foto["y"]), float(foto["w"]), float(foto["h"])
    if x0 < X - 0.5 or y0 < Y - 0.5 or x1 > X + Wc + 0.5 or y1 > Y + Hc + 0.5:
        r = [max(x0, X), max(y0, Y), min(x1, X + Wc), min(y1, Y + Hc)]
        if r[2] - r[0] < 1 or r[3] - r[1] < 1:
            raise ErroComposicao(f"`{a['id']}`: o recorte cai inteiro fora da área visível de `{nome}` (o object-fit cortou)")
        item["recorte"] = [round(v, 1) for v in r]
    return _levar_efeito(a, item)


# ------------------------------------------------------------------------------------------------- liga
def folga_px(v):
    """Folga da moldura: degrau e1..e8 ou px (número ou texto numérico)."""
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str) and v in ESPACO:
        return float(ESPACO[v])
    if isinstance(v, str) and re.fullmatch(r"\d+(?:\.\d+)?", v):
        return float(v)
    raise ErroComposicao(f"folga `{v}` inválida (e1..e8 ou px)")


def ponto_alvo(alvos, txt, quem="de"):
    """((x, y), restrição) de '<alvo>[.lN].<borda>[.<borda do outro eixo>][±desloc]'. Uma borda: ela no seu eixo e o
    centro do outro ('numero.dir' = meio da borda direita do número); duas: o canto. O deslocamento só vale com uma
    borda e anda no eixo dela ('numero.dir+e2' = 16 px à direita do número)."""
    m = _PONTO.match((txt or "").strip())
    if not m:
        raise ErroComposicao(f"ponto inválido `{txt}` (formato: <alvo>[.lN].<borda>[.<borda do outro eixo>][±e1..e8|±px])")
    nome, linha, b1, b2, sinal, d = m.groups()
    linha = int(linha) if linha else None
    if b2 and eixo(b1) == eixo(b2):
        raise ErroComposicao(f"ponto `{txt}`: o canto pede uma borda de cada eixo ({b1} e {b2} são do eixo {eixo(b1)})")
    if b2 and d:
        raise ErroComposicao(f"ponto `{txt}`: deslocamento só no ponto de uma borda, não no canto")
    bx = b1 if eixo(b1) == "x" else b2
    by = b1 if eixo(b1) == "y" else b2
    x = valor_alvo(alvos, nome, linha, bx or "cx")
    y = valor_alvo(alvos, nome, linha, by or "cy")
    if d:
        desl = float(ESPACO[d]) if d in ESPACO else float(d)
        desl = -desl if sinal == "-" else desl
        if eixo(b1) == "x":
            x += desl
        else:
            y += desl
    return (x, y), {"eixo": "ponto", "texto": f"{quem} {txt}", "alvo": nome, "valor": [round(x, 1), round(y, 1)]}


def _borda_estrutural(txt):
    """A borda, quando o ponto é uma borda da página ou da margem sozinha ('pagina.esq', 'margem.topo'); senão None."""
    m = _PONTO.match((txt or "").strip())
    if not m or m.group(4) or m.group(2):
        return None
    nome, b = m.group(1), m.group(3)
    return b if nome in ("pagina", "margem") and b in ("esq", "dir", "topo", "base") else None


def caixa_de_emoldurar(alvos, nome):
    """(x0, y0, x1, y1) do que se emoldura: texto pela tinta das linhas (bordas das linhas, do cap da primeira à linha de
    base da última), não pela caixa do bloco, que vai até a largura do painel; o resto pela caixa medida."""
    a = caixa_alvo(alvos, nome)
    ls = a.get("linhas") or []
    if ls and all("cap" in l and "linha_base" in l for l in ls):
        return (min(float(l["x"]) for l in ls), float(ls[0]["cap"]),
                max(float(l["x"]) + float(l["w"]) for l in ls), float(ls[-1]["linha_base"]))
    return float(a["x"]), float(a["y"]), float(a["x"]) + float(a["w"]), float(a["y"]) + float(a["h"])


def divisorias(itens):
    """Segmentos [[x0, y0], [x1, y1]] entre itens vizinhos de uma lista. Itens empilhados (mesma coluna, juntados por
    sobreposição em x): horizontal no meio do vão, na largura dos dois. Todos lado a lado numa linha só (cards):
    vertical no meio do vão, na altura dos dois."""
    caixas = [(float(i["x"]), float(i["y"]), float(i["x"]) + float(i["w"]), float(i["y"]) + float(i["h"])) for i in itens]
    colunas = []
    for c in sorted(caixas, key=lambda c: (c[0], c[1])):
        alvo = next((col for col in colunas
                     if min(col[0][2], c[2]) - max(col[0][0], c[0]) > 0.5 * min(col[0][2] - col[0][0], c[2] - c[0])), None)
        if alvo is None:
            colunas.append([c])
        else:
            alvo.append(c)
    segs = []
    if all(len(col) == 1 for col in colunas) and len(colunas) > 1:
        lado = sorted((col[0] for col in colunas), key=lambda c: c[0])
        for a, b in zip(lado, lado[1:]):
            x = (a[2] + b[0]) / 2
            segs.append([[x, min(a[1], b[1])], [x, max(a[3], b[3])]])
        return segs
    for col in colunas:
        col.sort(key=lambda c: c[1])
        for a, b in zip(col, col[1:]):
            y = (a[3] + b[1]) / 2
            segs.append([[min(a[0], b[0]), y], [max(a[2], b[2]), y]])
    return segs


def _pos_objeto(pos, livre_x, livre_y):
    """Deslocamento do object-position ('55% 45%', '10px 20px', palavras-chave) dado o espaço livre em cada eixo."""
    chaves = {"left": "0%", "center": "50%", "right": "100%", "top": "0%", "bottom": "100%"}
    partes = [chaves.get(p, p) for p in str(pos or "50% 50%").split()]
    if len(partes) == 1:
        partes.append("50%")

    def um(v, livre):
        try:
            if v.endswith("%"):
                return float(v[:-1]) / 100.0 * livre
            if v.endswith("px"):
                return float(v[:-2])
            return float(v)
        except ValueError:
            return 0.5 * livre

    return um(partes[0], livre_x), um(partes[1], livre_y)


def ponto_da_foto(foto, u, v, exigir_visivel=True):
    """(x, y) na página do ponto (u, v) dado em fração da IMAGEM da foto (0 a 1), pela regra do object-fit
    (cover, contain, fill, none, scale-down) e do object-position que o render mediu (alvo `foto` com `img`)."""
    X, Y, Wc, Hc = float(foto["x"]), float(foto["y"]), float(foto["w"]), float(foto["h"])
    ix, iy, rw, rh = retangulo_da_imagem(foto)
    x, y = ix + float(u) * rw, iy + float(v) * rh
    if exigir_visivel and not (X - 0.5 <= x <= X + Wc + 0.5 and Y - 0.5 <= y <= Y + Hc + 0.5):
        raise ErroComposicao(f"o ponto ({u}, {v}) da foto cai em ({x:.0f}, {y:.0f}), fora da área visível "
                             f"({X:.0f}, {Y:.0f}, {Wc:.0f}×{Hc:.0f}): o object-fit cortou essa parte")
    return x, y


def cruzamento(px, py, angulo, alvos, ate):
    """((x, y), restrição) onde a reta que sai de (px, py) no ângulo dado (graus; 0 = direita, 90 = para cima) cruza a
    borda `ate` ('<alvo>[.lN].<borda>' ou 'pagina.<borda>'). O cruzamento tem de cair dentro do alvo no outro eixo."""
    m = re.match(rf"^({_ALVO})(?:\.l(\d+))?\.({_BORDA})$", (ate or "").strip())
    if not m:
        raise ErroComposicao(f"`ate` inválido `{ate}` (formato: <alvo>[.lN].<borda>)")
    nome, linha, b = m.groups()
    linha = int(linha) if linha else None
    v = valor_alvo(alvos, nome, linha, b)
    caixa = caixa_alvo(alvos, nome)
    if linha is not None:
        caixa = (caixa.get("linhas") or [])[linha - 1]
    r = math.radians(float(angulo))
    dx, dy = math.cos(r), -math.sin(r)            # a página cresce para baixo: 90° sobe
    if eixo(b) == "x":
        if abs(dx) < 1e-9:
            raise ErroComposicao(f"a reta a {angulo}° é vertical: nunca cruza a borda vertical `{ate}`")
        t = (v - px) / dx
        qx, qy = v, py + t * dy
        lo, hi = float(caixa["y"]), float(caixa["y"]) + float(caixa["h"])
        fora = not (lo - TOLERANCIA <= qy <= hi + TOLERANCIA)
        onde = f"y={qy:.0f} (o alvo vai de {lo:.0f} a {hi:.0f})"
    else:
        if abs(dy) < 1e-9:
            raise ErroComposicao(f"a reta a {angulo}° é horizontal: nunca cruza a borda horizontal `{ate}`")
        t = (v - py) / dy
        qx, qy = px + t * dx, v
        lo, hi = float(caixa["x"]), float(caixa["x"]) + float(caixa["w"])
        fora = not (lo - TOLERANCIA <= qx <= hi + TOLERANCIA)
        onde = f"x={qx:.0f} (o alvo vai de {lo:.0f} a {hi:.0f})"
    if t <= 0:
        raise ErroComposicao(f"a reta a {angulo}° sai para o lado oposto de `{ate}`: não chega nele")
    if fora:
        raise ErroComposicao(f"a reta a {angulo}° cruza a linha de `{ate}` fora do alvo, em {onde}")
    return (qx, qy), {"eixo": "ponto", "texto": f"ate {ate}", "alvo": nome, "valor": [round(qx, 1), round(qy, 1)]}


def tipo_liga(anc, grafismo=None):
    """O grafismo da liga: o declarado em `grafismo.tipo` ou o do modo (fio; colchetes no emoldura)."""
    return (grafismo or {}).get("tipo") or TIPO_LIGA.get(anc.get("modo"), "fio")


def geometrias_liga(anc, alvos, W, H, tipo=None):
    """[(sufixo do id, tipo, parâmetros de geometria, restrições)] de uma âncora `liga`, em coordenadas da página.
    Pura: o QA chama de novo com os alvos do render final e compara."""
    modo = anc.get("modo")
    tipo = tipo or TIPO_LIGA.get(modo, "fio")
    if modo == "conecta":
        (x1, y1), r1 = ponto_alvo(alvos, anc.get("de"), "de")
        (x2, y2), r2 = ponto_alvo(alvos, anc.get("para"), "para")
        # fio de entrada (padrão do repertório: o fio entra pela borda na altura do alvo): a borda da página ou da
        # margem não tem centro útil; quem é borda herda do outro ponto a coordenada do outro eixo (horizontal pela
        # esquerda ou direita, vertical pelo topo ou pela base). Sem isso o fio sairia de y=540 em diagonal.
        b_de, b_para = _borda_estrutural(anc.get("de")), _borda_estrutural(anc.get("para"))
        if b_de and not b_para:
            x1, y1 = (x1, y2) if eixo(b_de) == "x" else (x2, y1)
        elif b_para and not b_de:
            x2, y2 = (x2, y1) if eixo(b_para) == "x" else (x1, y2)
        comp = math.hypot(x2 - x1, y2 - y1)
        if comp < 1:
            raise ErroComposicao(f"conecta: `{anc.get('de')}` e `{anc.get('para')}` caem no mesmo ponto")
        if anc.get("folga") is not None:
            # vão entre a ponta e o alvo: na ponta `para`, e na `de` quando ela também é conteúdo (não borda)
            f = folga_px(anc["folga"])
            ux, uy = (x2 - x1) / comp, (y2 - y1) / comp
            corta = f * (2 if not b_de and not alvo_estrutural(r1["alvo"]) else 1)
            if corta >= comp - 1:
                raise ErroComposicao(f"conecta: a folga {anc['folga']} ({f:.0f} px por ponta) come o fio inteiro ({comp:.0f} px)")
            x2, y2 = x2 - ux * f, y2 - uy * f
            if not b_de and not alvo_estrutural(r1["alvo"]):
                x1, y1 = x1 + ux * f, y1 + uy * f
        r1 = dict(r1, valor=[round(x1, 1), round(y1, 1)])
        r2 = dict(r2, valor=[round(x2, 1), round(y2, 1)])
        return [("", tipo, {"pontos": [[round(x1, 2), round(y1, 2)], [round(x2, 2), round(y2, 2)]]}, [r1, r2])]
    if modo == "emoldura":
        nome = anc.get("alvo")
        if not nome:
            raise ErroComposicao("emoldura pede `alvo`")
        f = folga_px(anc.get("folga"))
        x0, y0, x1, y1 = caixa_de_emoldurar(alvos, nome)
        cx = [round(x0 - f, 2), round(y0 - f, 2), round(x1 - x0 + 2 * f, 2), round(y1 - y0 + 2 * f, 2)]
        geo = {"caixa": cx} if tipo != "moldura" else {"caixa": cx, "largura": cx[2], "altura": cx[3]}
        return [("", tipo, geo, [{"eixo": "caixa", "texto": f"emoldura {nome} folga {anc.get('folga')}", "alvo": nome,
                                  "valor": [round(v, 1) for v in cx]}])]
    if modo == "separa":
        nome = anc.get("entre")
        bloco = BLOCO_DO_ITEM.get(nome, nome)
        caixa = caixa_alvo(alvos, bloco)
        itens = caixa.get("itens") or []
        if len(itens) < 2:
            raise ErroComposicao(f"separa `{nome}`: o bloco tem {len(itens)} item(ns) medido(s); precisa de 2 ou mais "
                                 f"(blocos de lista: {', '.join(BLOCOS_LISTA)})")
        segs = divisorias(itens)
        if not segs:
            raise ErroComposicao(f"separa `{nome}`: nenhum par de itens vizinhos")
        return [(f"-s{k + 1}", tipo, {"pontos": [[round(p[0], 2), round(p[1], 2)] for p in s]},
                 [{"eixo": "y" if s[0][1] == s[1][1] else "x", "texto": f"separa {nome} {k + 1}/{len(segs)}", "alvo": bloco,
                   "valor": round(s[0][1] if s[0][1] == s[1][1] else s[0][0], 1)}])
                for k, s in enumerate(segs)]
    if modo == "continua":
        nome = anc.get("alvo") or "foto"
        uv = anc.get("de_foto") or []
        if len(uv) != 2 or not all(isinstance(t, (int, float)) and 0 <= t <= 1 for t in uv):
            raise ErroComposicao(f"continua: `de_foto` precisa de [u, v] entre 0 e 1 (recebeu {uv})")
        if not isinstance(anc.get("angulo"), (int, float)):
            raise ErroComposicao("continua pede `angulo` em graus (0 = direita, 90 = para cima)")
        x1, y1 = ponto_da_foto(caixa_alvo(alvos, nome), uv[0], uv[1])
        (x2, y2), r2 = cruzamento(x1, y1, anc["angulo"], alvos, anc.get("ate"))
        r1 = {"eixo": "ponto", "texto": f"de_foto {nome} {uv}", "alvo": nome, "valor": [round(x1, 1), round(y1, 1)]}
        return [("", tipo, {"pontos": [[round(x1, 2), round(y1, 2)], [round(x2, 2), round(y2, 2)]]}, [r1, r2])]
    raise ErroComposicao(f"liga: modo `{modo}` fora do vocabulário ({', '.join(MODOS_LIGA)})")


def caixa_geometria(geo, espessura):
    """(x0, y0, x1, y1) da tinta de uma geometria de liga: os pontos do fio com meia espessura em volta; a caixa dos
    colchetes e da moldura (o traço fica por dentro dela)."""
    if geo.get("pontos"):
        xs, ys = [p[0] for p in geo["pontos"]], [p[1] for p in geo["pontos"]]
        m = espessura / 2.0
        return min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m
    x, y, w, h = geo["caixa"]
    return x, y, x + w, y + h


def _liga(a, med):
    """Itens de uma `liga`: a geometria sai dos alvos, o grafismo é gerado COM ela (contrato de grafismo preso a
    geometria: devolve `origem`, o canto do svg na página) e o item fica onde a `origem` manda, sem escala. Sem
    gerador (maquete), a caixa é a da geometria."""
    W, H = float(med.get("w", 1920)), float(med.get("h", 1080))
    alvos = med.get("alvos") or {}
    anc = a.get("ancora") or {}
    graf = a.get("_grafismo") or a.get("grafismo") or {}
    tipo = tipo_liga(anc, graf)
    base = dict(graf.get("params") or {})
    esp = float(anc.get("espessura") or base.get("espessura") or ESPESSURA_PADRAO)
    gerar = med.get("gerar_grafismo")
    from encaixes import normalizar_papel
    out = []
    for k, (suf, tipo_k, geo, restr) in enumerate(geometrias_liga(anc, alvos, W, H, tipo)):
        params = dict(base, **geo, espessura=esp)
        x0, y0, x1, y1 = caixa_geometria(geo, esp)
        g = None
        if gerar:
            try:
                g = gerar(tipo_k, params)
            except (ValueError, NotImplementedError) as e:
                raise ErroComposicao(f"`{a['id']}`: grafismo `{tipo_k}` da liga não gerou: {e}")
            if g.get("origem") is not None:
                x, y = float(g["origem"][0]), float(g["origem"][1])
            elif geo.get("caixa"):
                x, y = float(geo["caixa"][0]), float(geo["caixa"][1])   # moldura antiga: a caixa É a do svg
            else:
                raise ErroComposicao(f"`{a['id']}`: o grafismo `{tipo_k}` não devolveu `origem` (contrato de grafismo "
                                     f"preso a geometria, references/08)")
            w, h = float(g["w"]), float(g["h"])
            t = g.get("tinta") or [0, 0, w, h]
            tinta = [x + t[0], y + t[1], x + t[2], y + t[3]]
        else:
            x, y, w, h = x0, y0, x1 - x0, y1 - y0
            tinta = [x0, y0, x1, y1]
        geometria = dict(geo, tipo=tipo_k, espessura=esp)
        item = {"id": a["id"] + suf, "papel": normalizar_papel(a.get("papel") or "estrutura"), "encaixe": "composicao",
                "camada": a.get("camada") or "frente", "x": round(x, 1), "y": round(y, 1), "w": round(w, 1),
                "h": round(h, 1), "rot": 0, "origem": "composicao", "funcao": a.get("funcao"), "porque": a.get("porque"),
                "ancora": {"relacao": "liga", "modo": anc.get("modo"), "restricoes": restr,
                           "tinta": [round(v, 1) for v in tinta], "escala": None, "degrau": True, "declarada": dict(anc),
                           "geometria": geometria, "indice": k},
                "grafismo": {"tipo": tipo_k, "params": params}}
        if g is not None:
            item["_svg"] = g
        out.append(_levar_efeito(a, item))
    return out


# ------------------------------------------------------------------------------------------------- conferência (QA)
def conferir(it, alvos, W, H, desloc=(0.0, 0.0), tol=TOLERANCIA):
    """Âncora cumprida no render FINAL? Recalcula cada restrição com os alvos remedidos e compara com a tinta do item
    (deslocada pelo que o DOM mostrou: `desloc`). Devolve a lista de desvios (vazia = cumprida). Os dois eixos são
    conferidos um a um: rente só num eixo não passa."""
    anc = it.get("ancora") or {}
    rel = anc.get("relacao")
    decl = anc.get("declarada") or {}
    t0 = anc.get("tinta")
    if not t0 or not decl:
        return []
    dx, dy = float(desloc[0]), float(desloc[1])
    t = [t0[0] + dx, t0[1] + dy, t0[2] + dx, t0[3] + dy]
    bordas = {"esq": t[0], "dir": t[2], "cx": (t[0] + t[2]) / 2, "topo": t[1], "base": t[3], "cy": (t[1] + t[3]) / 2}
    for k, v in (anc.get("linhas") or {}).items():
        bordas[k] = float(v) + dy
    tw, th = t[2] - t[0], t[3] - t[1]
    erros = []

    def compara(desc, pede, real):
        if abs(real - pede) > tol:
            erros.append(f"{desc}: pede {pede:.1f}, a tinta está em {real:.1f} ({real - pede:+.1f} px)")

    try:
        if rel == REGISTRO:
            reg = anc.get("registro") or {}
            if not reg.get("img") or not reg.get("tinta_px"):
                return ["registro sem `ancora.registro` (img e tinta_px): o plano é anterior ao registro, renderize de novo"]
            pede = caixa_registro(caixa_alvo(alvos, decl.get("alvo") or "foto"), reg["img"], reg["tinta_px"])
            for nome_b, p, r in zip(("esq", "topo", "dir", "base"), pede, t):
                compara(f"registro {nome_b}", p, r)
            return erros
        if rel == "liga":
            geos = geometrias_liga(decl, alvos, W, H, (anc.get("geometria") or {}).get("tipo"))
            k = int(anc.get("indice") or 0)
            if k >= len(geos):
                return [f"liga {decl.get('modo')}: o render final tem {len(geos)} trecho(s); este era o {k + 1}º"]
            novo, velho = geos[k][2], anc.get("geometria") or {}
            if novo.get("pontos") and velho.get("pontos"):
                for i, (p, q) in enumerate(zip(novo["pontos"], velho["pontos"])):
                    d = max(abs(p[0] - q[0] - dx), abs(p[1] - q[1] - dy))
                    if d > tol:
                        erros.append(f"liga {decl.get('modo')}: ponto {i + 1} pede ({p[0]:.1f}, {p[1]:.1f}), o fio está em "
                                     f"({q[0] + dx:.1f}, {q[1] + dy:.1f})")
            elif novo.get("caixa") and velho.get("caixa"):
                d = max(abs(a_ - b_) for a_, b_ in zip(novo["caixa"], [velho["caixa"][0] + dx, velho["caixa"][1] + dy] + list(velho["caixa"][2:])))
                if d > tol:
                    erros.append(f"liga emoldura: a caixa pede {[round(v, 1) for v in novo['caixa']]}, está em "
                                 f"{[round(v, 1) for v in velho['caixa']]} ({d:.1f} px)")
            return erros
        eixos = ("x", "y")
        if rel == "sangra":
            eixos = ("y",) if decl.get("borda") in ("esq", "dir") else ("x",)
            c = _fracao(decl.get("corte"), DEGRAUS_FRACAO)
            borda = decl.get("borda")
            if borda == "dir": compara(f"sangra dir {decl.get('corte')}", W - (1 - c) * tw, t[0])
            elif borda == "esq": compara(f"sangra esq {decl.get('corte')}", -c * tw, t[0])
            elif borda == "topo": compara(f"sangra topo {decl.get('corte')}", -c * th, t[1])
            elif borda == "base": compara(f"sangra base {decl.get('corte')}", H - (1 - c) * th, t[1])
        elif rel == "sobrepoe":
            lado, nome = decl.get("lado"), decl.get("alvo")
            fr = _fracao(decl.get("fracao"), DEGRAUS_FRACAO)
            bv = valor_alvo(alvos, nome, None, lado)
            eixos = ("y",) if lado in ("esq", "dir") else ("x",)
            if lado == "esq": compara(f"sobrepoe {nome}.esq {decl.get('fracao')}", bv - (1 - fr) * tw, t[0])
            elif lado == "dir": compara(f"sobrepoe {nome}.dir {decl.get('fracao')}", bv - fr * tw, t[0])
            elif lado == "topo": compara(f"sobrepoe {nome}.topo {decl.get('fracao')}", bv - (1 - fr) * th, t[1])
            elif lado == "base": compara(f"sobrepoe {nome}.base {decl.get('fracao')}", bv - fr * th, t[1])
        for chave in eixos:
            txt = decl.get(chave)
            if not txt:
                continue
            b_el, alvo, linha, b_alvo, desl = parse_restricao(txt)
            if b_el not in bordas:
                continue
            compara(txt, valor_alvo(alvos, alvo, linha, b_alvo) + desl, bordas[b_el])
    except ErroComposicao as e:
        erros.append(f"o alvo não existe mais no render final: {e}")
    return erros


# ------------------------------------------------------------------------------------------------- rótulos
def entrada_da_pagina(comp, rotulos, rotulo_variante, tipo, formato="horizontal"):
    """(chave, entrada, chave_gramatica, entrada_gramatica) da composição desta página. Mais específico vence: página
    (ativo:2, cota:Master, vertical:*) > variante (cota:b) > tipo (cota, ativo). A do tipo é a gramática."""
    if not comp:
        return None, None, None, None
    cands = []
    for chave, ent in comp.items():
        if chave.startswith("_") or not isinstance(ent, dict):
            continue
        vertical = chave.startswith("vertical:")
        if (formato == "vertical") != vertical:
            continue
        if chave not in rotulos and chave != rotulo_variante:
            continue
        if vertical: nota = 4
        elif chave == rotulo_variante and ":" in chave: nota = 2
        elif chave in (tipo, "ativo"): nota = 1
        else: nota = 3
        cands.append((nota, chave == tipo, chave, ent))
    if not cands:
        return None, None, None, None
    cands.sort(key=lambda c: (c[0], c[1]))
    _, _, chave, ent = cands[-1]
    gram = [c for c in cands if c[0] == 1]
    gram.sort(key=lambda c: c[1])
    gch, gent = (gram[-1][2], gram[-1][3]) if gram else (None, None)
    return chave, ent, gch, gent


def atribuidos(entrada, n, ids_kit=()):
    """Os elementos da composição no formato de atribuído que o encaixes.resolver recebe (com `ancora`). ids_kit = ids
    de elementos[] do kit: a liga com id de lá usa aquele grafismo; sem ele, o do modo, com id único por página."""
    ids_kit = set(ids_kit or ())
    out = []
    for e in entrada.get("elementos") or []:
        a = {"id": e["id"], "papel": e.get("papel") or "heroi", "camada": e.get("camada") or "frente",
             "ancora": e.get("ancora"), "escala": e.get("escala"), "funcao": e.get("funcao"), "porque": e.get("porque"),
             "rot": e.get("rot") or 0, "origem": "composicao"}
        if e.get("espelhar"):
            a["espelhar"] = True
        for c in EFEITO_ITEM:
            if e.get(c) is not None:
                a[c] = e[c]
        liga = (e.get("ancora") or {}).get("relacao") == "liga"
        if e.get("grafismo") or (liga and e.get("id") not in ids_kit):
            # grafismo declarado só nesta página (a liga sem `grafismo` usa o do modo: fio ou colchetes): id único por
            # página, porque o svg é gerado com a geometria dela
            graf = e.get("grafismo") or {"tipo": tipo_liga(e["ancora"])}
            esm = (e.get("efeito") or {}).get("esmaecer")
            if esm and "esmaecer" not in (graf.get("params") or {}):
                # esmaecer em grafismo é do gerador (degraus de opacidade no svg, _Degraus do grafismos.py), nunca máscara
                graf = dict(graf, params=dict(graf.get("params") or {}, esmaecer=dict(esm)))
            a["grafismo"] = graf
            a["id"] = f"{e['id']}-p{n}"
        if e.get("proporcao"):
            a["proporcao"] = list(e["proporcao"])     # asset ainda não gerado: a maquete desenha a caixa nessa proporção
        out.append(a)
    return out


# ------------------------------------------------------------------------------------------------- validação
def _schema():
    sch = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return dict(sch["definitions"]["composicao"], definitions=sch["definitions"])


def _falhas_acabamento(comp, kit):
    """As FALHAS da camada de acabamento (acabamento.py, mk-2.1) no mesmo canal da composição. Sem `kit` (o camadas.py
    chama sem ele), só as regras que a composição sozinha decide; com o kit, todas. Kit sem campo novo: nada."""
    import acabamento
    if kit is None:
        falhas, _ = acabamento.validar({"composicao": comp or {}}, so_composicao=True)
    else:
        falhas, _ = acabamento.validar(dict(kit, composicao=comp or {}))
    return falhas


def validar(comp, ids_elementos=(), kit=None):
    """Erros da composição (lista vazia = válida): o schema estrito (chave com erro de digitação reprova) e o que o
    schema não alcança: restrição que não parseia, eixo trocado, âncora sem os dois eixos, nenhum eixo em conteúdo,
    id que não existe nem é grafismo, escala fora do formato. Mais as falhas da camada de acabamento (acabamento.py):
    `kit` (o mediakit.json inteiro, opcional) liga as regras que dependem da direção criativa, dos motivos e de
    elementos[]; sem ele rodam só as que a composição decide."""
    if not comp:
        return _falhas_acabamento(comp, kit)
    erros = []
    try:
        import jsonschema
        v = jsonschema.Draft7Validator(_schema())
        for e in sorted(v.iter_errors(comp), key=lambda e: list(e.path)):
            onde = "/".join(str(p) for p in e.path) or "composicao"
            erros.append(f"composicao/{onde}: {e.message}")
    except ImportError:
        erros.append("jsonschema ausente: a composição não foi validada")
    ids = set(ids_elementos)
    for chave, ent in (comp or {}).items():
        if chave.startswith("_") or not isinstance(ent, dict):
            continue
        for i, e in enumerate(ent.get("elementos") or []):
            if not isinstance(e, dict):
                continue
            onde = f"composicao/{chave}/elementos/{i} (`{e.get('id')}`)"
            anc = e.get("ancora") or {}
            rel = anc.get("relacao")
            if e.get("id") not in ids and not e.get("grafismo") and not e.get("proporcao") and rel != "liga":
                erros.append(f"{onde}: id não existe em elementos[] e não declara `grafismo` (nem `proporcao` de asset planejado)")
            if rel == "liga":
                erros += [f"{onde}: {x}" for x in _validar_liga(anc, e.get("funcao"))]
                continue
            if rel == REGISTRO:
                if e.get("grafismo"):
                    erros.append(f"{onde}: registro é o recorte da própria foto (PNG de elementos[]), não grafismo")
                if e.get("escala") or e.get("rot") or e.get("espelhar"):
                    erros.append(f"{onde}: registro não tem escala, giro nem espelho (posição e tamanho vêm da foto)")
                continue
            eixos_conteudo = []
            for k in ("x", "y"):
                if anc.get(k):
                    try:
                        b_el, alvo, _, _, _ = parse_restricao(anc[k])
                        if eixo(b_el) != k:
                            erros.append(f"{onde}: `{k}` recebeu restrição do eixo {eixo(b_el)}")
                        eixos_conteudo.append(not alvo_estrutural(alvo))
                    except ErroComposicao as x:
                        erros.append(f"{onde}: {x}")
            if rel == "alinha" and not (anc.get("x") and anc.get("y")):
                erros.append(f"{onde}: alinha precisa dos dois eixos (x e y)")
            if rel == "sangra":
                borda = anc.get("borda")
                outro = "y" if borda in ("esq", "dir") else "x"
                if not anc.get(outro):
                    erros.append(f"{onde}: sangra pela borda {borda} precisa do eixo `{outro}`")
            if rel == "sobrepoe":
                lado = anc.get("lado")
                outro = "y" if lado in ("esq", "dir") else "x"
                if not anc.get(outro):
                    erros.append(f"{onde}: sobrepoe pelo lado {lado} precisa do eixo `{outro}`")
                if anc.get("alvo") and not alvo_estrutural(anc["alvo"]):
                    eixos_conteudo.append(True)
            if rel in ("alinha", "sangra", "sobrepoe") and e.get("funcao") != "acabamento" and not any(eixos_conteudo):
                erros.append(f"{onde}: nenhum eixo preso a conteúdo (título, número, foto, bloco); só margem, página ou "
                             f"coluna vale para a função acabamento")
            if rel in ("alinha", "sangra", "sobrepoe") and not e.get("escala"):
                erros.append(f"{onde}: falta `escala` (altura ou largura em degrau)")
    return erros + _falhas_acabamento(comp, kit)


def _alvo_do_ponto(txt):
    m = _PONTO.match((txt or "").strip())
    if not m:
        raise ErroComposicao(f"ponto inválido `{txt}` (formato: <alvo>[.lN].<borda>[.<borda do outro eixo>][±e1..e8|±px])")
    if m.group(4) and eixo(m.group(3)) == eixo(m.group(4)):
        raise ErroComposicao(f"ponto `{txt}`: o canto pede uma borda de cada eixo")
    return m.group(1)


def _validar_liga(anc, funcao):
    """O que o schema não alcança na liga: campos de cada modo, ponto e borda que parseiam, alvo de conteúdo."""
    erros, alvos = [], []
    modo = anc.get("modo")
    try:
        if modo == "conecta":
            if not (anc.get("de") and anc.get("para")):
                erros.append("conecta pede `de` e `para` (<alvo>.<borda>)")
            alvos += [_alvo_do_ponto(anc[k]) for k in ("de", "para") if anc.get(k)]
            if anc.get("folga") is not None:
                folga_px(anc["folga"])
        elif modo == "emoldura":
            if not anc.get("alvo") or anc.get("folga") is None:
                erros.append("emoldura pede `alvo` e `folga` (e1..e8 ou px)")
            if anc.get("folga") is not None:
                folga_px(anc["folga"])
            alvos += [anc["alvo"]] if anc.get("alvo") else []
        elif modo == "separa":
            if not anc.get("entre"):
                erros.append(f"separa pede `entre` (bloco de lista: {', '.join(BLOCOS_LISTA)})")
            elif BLOCO_DO_ITEM.get(anc["entre"], anc["entre"]) not in BLOCOS_LISTA:
                erros.append(f"separa: `{anc['entre']}` não é bloco de lista ({', '.join(BLOCOS_LISTA)})")
            alvos += [anc["entre"]] if anc.get("entre") else []
        elif modo == "continua":
            uv = anc.get("de_foto") or []
            if len(uv) != 2 or not all(isinstance(t, (int, float)) and 0 <= t <= 1 for t in uv):
                erros.append("continua pede `de_foto` [u, v] entre 0 e 1 (fração da imagem)")
            if not isinstance(anc.get("angulo"), (int, float)):
                erros.append("continua pede `angulo` em graus (0 = direita, 90 = para cima)")
            ate = anc.get("ate") or ""
            m = re.match(rf"^({_ALVO})(?:\.l\d+)?\.{_BORDA}$", ate)
            if not m:
                erros.append(f"continua pede `ate` = <alvo>.<borda> ou pagina.<borda> (recebeu `{ate}`)")
            alvos += [anc.get("alvo") or "foto"] + ([m.group(1)] if m else [])
        else:
            erros.append(f"liga: `modo` {modo!r} fora do vocabulário ({', '.join(MODOS_LIGA)})")
    except ErroComposicao as x:
        erros.append(str(x))
    if alvos and funcao != "acabamento" and all(alvo_estrutural(a) for a in alvos):
        erros.append("a liga não toca nenhum conteúdo (título, número, foto, bloco); só margem, página ou coluna vale "
                     "para a função acabamento")
    return erros


def validar_constantes(sistema):
    """`ancora` das constantes (sistema_elementos.constantes[]): mesma sintaxe da composição, mas só alinha ou sangra e
    só alvos ESTRUTURAIS (margem, pagina, coluna:N), porque a caixa da constante é a mesma em toda página do formato."""
    erros = []
    for i, c in enumerate((sistema or {}).get("constantes") or []):
        anc = c.get("ancora")
        if not anc:
            continue
        onde = f"sistema_elementos/constantes/{i} ({c.get('tipo')})"
        rel = anc.get("relacao")
        if rel not in ("alinha", "sangra"):
            erros.append(f"{onde}: âncora de constante é alinha ou sangra (recebeu {rel!r})")
            continue
        chaves = ("x", "y") if rel == "alinha" else (("y",) if anc.get("borda") in ("esq", "dir") else ("x",))
        for k in chaves:
            if not anc.get(k):
                erros.append(f"{onde}: falta o eixo `{k}`")
                continue
            try:
                b_el, alvo, _, _, _ = parse_restricao(anc[k])
                if eixo(b_el) != k:
                    erros.append(f"{onde}: `{k}` recebeu restrição do eixo {eixo(b_el)}")
                if not alvo_estrutural(alvo):
                    erros.append(f"{onde}: `{anc[k]}` prende a constante em `{alvo}`; constante só ancora em margem, "
                                 f"pagina ou coluna (a mesma caixa em toda página)")
            except ErroComposicao as x:
                erros.append(f"{onde}: {x}")
        if rel == "sangra" and anc.get("corte") not in DEGRAUS_FRACAO:
            erros.append(f"{onde}: corte {anc.get('corte')!r} fora dos degraus ({', '.join(DEGRAUS_FRACAO)})")
    return erros


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(0)
    k = json.loads(Path(sys.argv[1], "mediakit.json").read_text(encoding="utf-8"))
    es = validar(k.get("composicao"), [e.get("id") for e in k.get("elementos") or []], kit=k)
    for e in es:
        print("FALHA", e)
    print(f"{len(es)} erro(s) na composição")
    sys.exit(1 if es else 0)

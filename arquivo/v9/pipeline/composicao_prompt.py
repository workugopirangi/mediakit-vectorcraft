#!/usr/bin/env python3
"""
composicao_prompt.py: o que a composição da página (references/09-composicao.md) diz sobre UM elemento ou sobre a foto da
página, em fatos medidos, para o bloco "Composition" dos prompts de geração (elementos_prompt.py e cena_prompt.py) e para o
`plano_elementos.faltantes` pedir o aspecto real. Só biblioteca padrão: o cena_prompt.py roda sem numpy.

Por que existe: o asset nasce para a página. Antes, o prompt dizia "quadrado, objeto isolado, margem dos quatro lados" e a
página decidia depois, sem o gerador saber. Agora o gerador recebe a área e a proporção reais em px, o lado da página em que o
objeto fica, para onde ele olha (o foco da página), qual borda vai cortá-lo (`sangra`) e onde fica o detalhe que não pode ser
cortado, e a luz e a lente da foto da página.

Fontes, da mais forte para a mais fraca (nunca se inventa o que nenhuma tem; a frase some):
  1. `saida/plano-elementos-<receita>.json` (a maquete ou o render): caixa resolvida do elemento (tinta, em px da página) e
     `alvos` medidos da página (título, número, foto...). Mede o que o render mediu.
  2. `mediakit.json`: `composicao` (âncora, escala, foco, mensagem) e `elementos[]` (aspecto declarado do elemento).
     Sem o plano, a área sai da `escala` (1/3p, 4col, px) e do aspecto declarado, pela mesma conta do composicao.py.
  3. `marca.estilo_cena`: a luz e a lente da foto da página.

  python composicao_prompt.py <pasta-do-kit> <pagina> [--elemento <id>] [--receita r1]    imprime os fatos (JSON)
"""
import argparse, json, math, re, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import composicao  # noqa: E402

PAGINA_PADRAO = (1920, 1080)
ALVOS_PADRAO = {"colunas": [{"x": 96 + i * 152, "w": 128} for i in range(11)]}      # a medida do tema (references/08)
PROPORCOES = {"quadrado": 1.0, "largo": 1.5, "alto": 2 / 3, "faixa": 3.0}         # largura / altura de cada aspecto do gerador
BORDAS = {"esq": "left", "dir": "right", "topo": "top", "base": "bottom"}
OPOSTA = {"left": "right", "right": "left", "top": "bottom", "bottom": "top"}
FRACOES = {"1/4": "about a quarter", "1/3": "about a third", "1/2": "about half"}
RUMOS = ["right", "upper right", "up", "upper left", "left", "lower left", "down", "lower right"]
ESPELHO = {"right": "left", "left": "right", "upper right": "upper left", "upper left": "upper right", "lower right": "lower left",
           "lower left": "lower right", "up": "up", "down": "down"}
FOCO_ALVO = {"titulo": "titulo", "numero": "numero", "preco": "preco", "foto": "foto", "grafico": "grafico", "lista": "lista-num",
             "lettering": "titulo"}
FOCO_TEXTO = {"titulo": "the title", "numero": "the big number", "preco": "the price", "foto": "the photo", "objeto": "the object",
              "lettering": "the lettering", "grafico": "the chart", "lista": "the list"}
ALVO_TEXTO = {"foto": "the photo", "painel": "the panel", "titulo": "the title", "numero": "the number", "preco": "the price",
              "logo": "the logo", "pagina": "the page", "margem": "the margin"}


class ErroComposicaoPrompt(ValueError):
    """Pedido que a composição do kit não sustenta (página ou elemento que não existe): sai com a lista do que existe."""


# ------------------------------------------------------------------------------------------------- leitura
def ler_kit(pasta):
    caminho = Path(pasta) / "mediakit.json"
    if not caminho.is_file():
        raise ErroComposicaoPrompt(f"não achei {caminho}: --composicao leva a pasta do kit (a que tem o mediakit.json)")
    return json.loads(caminho.read_text(encoding="utf-8"))


def _planos(pasta, receita=None, vertical=False):
    """[(arquivo, plano)] de saida/plano-elementos-*.json (render) e saida/plano-maquete-*.json (render.py --maquete): só o
    horizontal (ou só o vertical), ou o da receita pedida. A maquete vem ANTES do asset e grava no próprio arquivo (não toca
    no plano do render); por receita vale o mais novo dos dois, que é o que reflete a composição atual."""
    saida = Path(pasta) / "saida"
    if not saida.is_dir():
        return []
    por_receita = {}
    for f in list(saida.glob("plano-elementos-*.json")) + list(saida.glob("plano-maquete-*.json")):
        eh_vertical = f.stem.endswith("-vertical")
        if eh_vertical != vertical:
            continue
        rid = f.stem.split("-", 2)[2]
        rid = rid[: -len("-vertical")] if eh_vertical else rid
        if receita and rid != receita:
            continue
        if rid not in por_receita or f.stat().st_mtime > por_receita[rid].stat().st_mtime:
            por_receita[rid] = f
    achados = []
    for rid in sorted(por_receita):
        f = por_receita[rid]
        try:
            achados.append((f, json.loads(f.read_text(encoding="utf-8"))))
        except ValueError:
            continue
    return achados


def _casa_pagina(pg, rotulo):
    nomes = set(pg.get("rotulos") or []) | {pg.get("rotulo"), pg.get("tipo")}
    return rotulo in nomes or (rotulo.isdigit() and pg.get("n") == int(rotulo)) or rotulo == (pg.get("rotulo") or "").split(":")[0]


def _achar_no_plano(planos, pagina, elemento):
    """(arquivo, plano, página, item) da primeira página do plano que casa com o rótulo e, quando `elemento` vem, que o
    contém. Sem item (elemento ainda sem caixa), devolve a página que casa."""
    primeira = None
    for arq, plano in planos:
        for pg in plano.get("paginas") or []:
            if not _casa_pagina(pg, pagina):
                continue
            if primeira is None:
                primeira = (arq, plano, pg, None)
            if elemento:
                item = next((it for it in pg.get("elementos") or []
                             if it.get("id") == elemento or str(it.get("id", "")).startswith(f"{elemento}-p")), None)
                if item:
                    return arq, plano, pg, item
    return primeira if primeira else (None, None, None, None)


# ------------------------------------------------------------------------------------------------- escala e proporção
def aspecto_do_gerador(razao):
    """O aspecto do gerador (quadrado, largo, alto, faixa) mais perto de largura / altura: o ponto médio entre dois aspectos
    é a média geométrica (entre 1 e 1,5, 1,22; entre 1,5 e 3, 2,12; entre 1 e 2/3, 0,82)."""
    if razao >= 2.12:
        return "faixa"
    if razao >= 1.2247:
        return "largo"
    if razao > 0.8165:
        return "quadrado"
    return "alto"


def area_declarada(escala, aspecto, pagina=PAGINA_PADRAO, alvos=None):
    """(largura px, altura px) da TINTA que a escala e o aspecto declarados dão, pela mesma conta do composicao.py (uma
    dimensão pela escala, a outra segue o aspecto); None quando falta um dos dois ou a escala depende de uma medida que só o
    render tem (3cap sem o título medido)."""
    if not escala or aspecto not in PROPORCOES:
        return None
    try:
        w, h, _ = composicao.tamanho_tinta(escala, PROPORCOES[aspecto], 1.0, alvos or ALVOS_PADRAO, float(pagina[0]), float(pagina[1]))
    except composicao.ErroComposicao:
        return None
    return w, h


def descrever_razao(w, h):
    r = w / h
    forma = "square" if 0.9 <= r <= 1.1 else ("landscape" if r > 1 else "portrait")
    return f"ratio {r:.2f}:1, {forma}"


def rumo(dx, dy, minimo=40.0):
    """Direção (right, upper left, down...) de um vetor da página; None se for curto demais para valer."""
    if math.hypot(dx, dy) < minimo:
        return None
    return RUMOS[int(((math.degrees(math.atan2(-dy, dx)) + 22.5) % 360) // 45)]


def rumo_para_dentro(lado):
    """Direção que aponta do lado da página em que o elemento está para o interior dela (upper left -> lower right)."""
    h, v = lado
    horiz = {"left": "right", "right": "left"}.get(h)
    vert = {"upper": "lower", "lower": "upper"}.get(v)
    if horiz and vert:
        return f"{vert} {horiz}"
    return horiz or {"upper": "down", "lower": "up"}.get(v)


def posicao_na_pagina(cx, cy, W, H):
    """('left'|'center'|'right', 'upper'|'middle'|'lower') do centro (cx, cy) na página, em terços."""
    return ("left" if cx < W / 3 else "right" if cx > 2 * W / 3 else "center",
            "upper" if cy < H / 3 else "lower" if cy > 2 * H / 3 else "middle")


# ------------------------------------------------------------------------------------------------- luz e lente da foto da página
_LUZ = re.compile(r"\b(lights?|sun|sunrise|sunset|morning|afternoon|evening|dusk|dawn|golden|backlight|backlit|haze|hazy|shadows?|sky|"
                  r"glow|overcast|midday|noon|night|floodlights?)\b", re.I)
_LENTE = re.compile(r"(\b\d+\s?mm\b|\blens\b|\bf/\d|\beye[- ]level\b|\boverhead\b|\btop[- ]down\b|\blow angle\b|\bhigh angle\b|"
                    r"\bwide[- ]angle\b|\btelephoto\b)", re.I)
_ESQ = re.compile(r"\b(on|from|to) the left\b|\bleft[- ]side\b|\bfrom left\b", re.I)
_DIR = re.compile(r"\b(on|from|to) the right\b|\bright[- ]side\b|\bfrom right\b", re.I)
_CIMA = re.compile(r"\boverhead\b|\bfrom above\b|\bfrom the top\b|\btop light\b|\bmidday\b|\bnoon\b", re.I)


def luz_da_foto(estilo_cena):
    """O que o bloco de estilo de cena do kit (`marca.estilo_cena`, em inglês) diz da luz e da lente da foto da página:
    {'luz': [cláusulas de luz], 'lente': [cláusulas de câmera], 'direcao': 'esquerda'|'direita'|'cima'|None}. A direção só
    vale quando as cláusulas de luz apontam um lado só (sol 'on the left', 'from the right'); lados dos dois lados = None."""
    clausulas = [c.strip() for c in re.split(r",|;", estilo_cena or "") if c.strip()]
    lente = [c for c in clausulas if _LENTE.search(c) and not _LUZ.search(c)]      # "overhead light" é luz; "overhead shot" é câmera
    luz = [c for c in clausulas if _LUZ.search(c)]
    texto = " ".join(luz)
    esq, dire, cima = bool(_ESQ.search(texto)), bool(_DIR.search(texto)), bool(_CIMA.search(texto))
    direcao = "esquerda" if esq and not dire else "direita" if dire and not esq else "cima" if cima and not (esq or dire) else None
    return {"luz": luz, "lente": lente, "direcao": direcao}


# ------------------------------------------------------------------------------------------------- o contexto
def contexto(pasta, pagina, elemento=None, receita=None, vertical=False):
    """Os fatos da composição para UM elemento (ou, sem `elemento`, para a foto da página). Levanta ErroComposicaoPrompt com a
    lista do que existe quando a página ou o elemento não estão na composição do kit."""
    kit = ler_kit(pasta)
    comp = kit.get("composicao") or {}
    if not comp:
        raise ErroComposicaoPrompt(f"o mediakit.json de {pasta} não tem `composicao`: escreva a composição da página antes "
                                   "(references/09-composicao.md) ou gere sem --composicao")
    arq, plano, pg, item = _achar_no_plano(_planos(pasta, receita, vertical), pagina, elemento)
    rotulos = set((pg or {}).get("rotulos") or []) | {pagina, pagina.split(":")[0]}
    tipo = (pg or {}).get("tipo") or pagina.split(":")[0]
    chave, ent, gram, _ = composicao.entrada_da_pagina(comp, rotulos, (pg or {}).get("rotulo") or pagina, tipo,
                                                       "vertical" if vertical else "horizontal")
    if ent is None:
        raise ErroComposicaoPrompt(f"a composição do kit não tem entrada para a página `{pagina}` (chaves: "
                                   f"{', '.join(k for k in comp if not k.startswith('_')) or 'nenhuma'})")
    el = None
    if elemento:
        el = next((e for e in ent.get("elementos") or [] if e.get("id") == elemento), None)
        if el is None:
            ids = [e.get("id") for e in ent.get("elementos") or []]
            raise ErroComposicaoPrompt(f"o elemento `{elemento}` não está na composição de `{chave}` (há: {', '.join(map(str, ids)) or 'nenhum'})")
    kit_el = next((e for e in kit.get("elementos") or [] if e.get("id") == elemento), None) if elemento else None
    W, H = (plano or {}).get("largura") or PAGINA_PADRAO[0], (plano or {}).get("altura") or PAGINA_PADRAO[1]
    alvos = (pg or {}).get("alvos") or {}
    ctx = {"pagina": pagina, "chave": chave, "gramatica": gram, "mensagem": ent.get("mensagem"), "foco": ent.get("foco"),
           "estrutura": ent.get("estrutura"), "leitura": ent.get("leitura") or [], "pagina_px": [W, H],
           "plano": str(arq.name) if arq else None, "alvos": alvos,
           "elemento": None, "caixa": None, "area_px": None, "razao": None, "aspecto": None, "origem_da_medida": None,
           "lado": None, "rumo": None, "alvo_do_foco": None, "sangra": None, "sobrepoe": None, "rot": 0.0, "espelhar": False,
           "estilo_cena": (kit.get("marca") or {}).get("estilo_cena") or None, "foto": alvos.get("foto") or None}
    if el:
        anc = el.get("ancora") or {}
        ctx["elemento"] = {"id": el["id"], "papel": el.get("papel"), "funcao": el.get("funcao"), "porque": el.get("porque"),
                           "ancora": anc, "escala": el.get("escala"), "tipo": (kit_el or {}).get("tipo"),
                           "aspecto_declarado": (kit_el or {}).get("aspecto")}
        ctx["rot"] = float(el.get("rot") or 0.0)
        ctx["espelhar"] = bool(el.get("espelhar"))
        if anc.get("relacao") == "sangra" and anc.get("borda") in BORDAS:
            ctx["sangra"] = {"borda": BORDAS[anc["borda"]], "corte": anc.get("corte")}
        if anc.get("relacao") == "sobrepoe":
            ctx["sobrepoe"] = {"alvo": anc.get("alvo"), "lado": BORDAS.get(anc.get("lado")), "fracao": anc.get("fracao")}
        # a medida: a caixa resolvida (tinta) do plano; sem ela, a escala e o aspecto declarados
        caixa = None
        if item:
            t = (item.get("ancora") or {}).get("tinta")
            caixa = (list(map(float, t)) if t else [item["x"], item["y"], item["x"] + item["w"], item["y"] + item["h"]])
            ctx["origem_da_medida"] = "plano"
        else:
            a = area_declarada(el.get("escala"), (kit_el or {}).get("aspecto"), (W, H), alvos or None)
            if a:
                ctx["area_px"] = [round(a[0]), round(a[1])]
                ctx["origem_da_medida"] = "escala e aspecto declarados"
        if caixa:
            ctx["caixa"] = [round(v, 1) for v in caixa]
            ctx["area_px"] = [round(caixa[2] - caixa[0]), round(caixa[3] - caixa[1])]
        if ctx["area_px"] and ctx["area_px"][1] > 0:
            ctx["razao"] = ctx["area_px"][0] / ctx["area_px"][1]
            ctx["aspecto"] = aspecto_do_gerador(ctx["razao"])
        elif (kit_el or {}).get("aspecto") in PROPORCOES:
            ctx["aspecto"] = kit_el["aspecto"]
        # o lado da página: pelo centro da caixa; sem caixa, pela âncora
        if caixa:
            ctx["lado"] = posicao_na_pagina((caixa[0] + caixa[2]) / 2, (caixa[1] + caixa[3]) / 2, W, H)
        else:
            ctx["lado"] = _lado_pela_ancora(anc)
        # para onde olha: o foco da página (o alvo medido) ou, sem ele, para dentro da página
        foco = ent.get("foco")
        alvo_nome = FOCO_ALVO.get(foco or "")
        if not alvo_nome and foco == "objeto":          # o objeto é o foco: olha para o primeiro alvo da leitura que a página tem
            alvo_nome = next((FOCO_ALVO[x] for x in ent.get("leitura") or [] if x in FOCO_ALVO and FOCO_ALVO[x] in alvos), None)
        foco_caixa = alvos.get(alvo_nome) if alvo_nome else None
        if caixa and foco_caixa:
            fx, fy = foco_caixa["x"] + foco_caixa["w"] / 2, foco_caixa["y"] + foco_caixa["h"] / 2
            ctx["rumo"] = rumo(fx - (caixa[0] + caixa[2]) / 2, fy - (caixa[1] + caixa[3]) / 2)
            ctx["alvo_do_foco"] = FOCO_TEXTO[foco] if FOCO_ALVO.get(foco) == alvo_nome else (ALVO_TEXTO.get(alvo_nome) or f"the {alvo_nome}")
        elif ctx["lado"]:
            ctx["rumo"] = rumo_para_dentro(ctx["lado"])
            ctx["alvo_do_foco"] = "the inside of the page" if ctx["rumo"] else None
    return ctx


def _posicao_no_object_position(pos):
    """(x, y) em fração (0 a 1) do object-position CSS ('50% 50%', 'left center', 'center'): onde a janela da página pega a
    imagem quando ela é maior que a caixa. Desconhecido = centro."""
    palavras = {"left": 0.0, "top": 0.0, "center": 0.5, "right": 1.0, "bottom": 1.0}
    vals = []
    for t in (pos or "50% 50%").replace(",", " ").split():
        if t in palavras:
            vals.append(palavras[t])
        elif t.endswith("%"):
            try:
                vals.append(float(t[:-1]) / 100)
            except ValueError:
                pass
    if len(vals) == 1:
        vals.append(0.5)
    return (vals[0], vals[1]) if len(vals) >= 2 else (0.5, 0.5)


def regiao(fx, fy):
    """Região (em palavras) de um ponto em fração da caixa: 'upper left', 'center', 'left', 'bottom'..."""
    h = "left" if fx < 1 / 3 else "right" if fx > 2 / 3 else None
    v = "upper" if fy < 1 / 3 else "lower" if fy > 2 / 3 else None
    if h and v:
        return f"{v} {h}"
    return h or {"upper": "top", "lower": "bottom"}.get(v) or "center"


TEXTO_CORRIDO = ("corpo", "micro", "direitos", "direitos-2col", "caixa", "regioes", "contato-linha", "lista", "lista-num",
                 "cards", "caixas4", "inv-colunas")
ELEMENTO_MINIMO = 0.01      # o herói pequeno (troféu de pé numa cota) também pede a área calma; texto continua a partir de 4%


def cena(c, origem=16 / 9):
    """Fatos da foto da página para o prompt da CENA (cena_prompt.py): a caixa que a foto ocupa na página, o recorte que a
    página faz na imagem de origem (cover, com o object-position medido), as zonas em que texto e elemento vão cobrir a foto
    (para o gerador deixá-las calmas e sem detalhe-chave). Devolve None quando não há foto medida (sem plano da maquete)."""
    foto = c.get("foto")
    if not foto or not foto.get("w") or not foto.get("h"):
        return None
    W, H = c["pagina_px"]
    razao = foto["w"] / foto["h"]
    out = {"caixa": [round(foto[k]) for k in ("x", "y", "w", "h")], "razao": razao, "pagina_px": [W, H], "recorte": None,
           "texto": [], "elemento": None, "foco_foto": c.get("foco") == "foto"}
    px, py = _posicao_no_object_position(((foto.get("img") or {}).get("pos")))
    if razao < origem * 0.98:         # a caixa é mais estreita que a imagem de origem: a página corta dos lados
        f = razao / origem
        out["recorte"] = {"eixo": "x", "de": round((1 - f) * px * 100), "ate": round(((1 - f) * px + f) * 100)}
    elif razao > origem * 1.02:       # mais larga: corta em cima e embaixo
        f = origem / razao
        out["recorte"] = {"eixo": "y", "de": round((1 - f) * py * 100), "ate": round(((1 - f) * py + f) * 100)}

    def sobre_a_foto(x0, y0, x1, y1, minimo=0.04):
        ix0, iy0, ix1, iy1 = max(x0, foto["x"]), max(y0, foto["y"]), min(x1, foto["x"] + foto["w"]), min(y1, foto["y"] + foto["h"])
        if ix1 - ix0 <= 0 or iy1 - iy0 <= 0:
            return None
        area = (ix1 - ix0) * (iy1 - iy0)
        if area < minimo * foto["w"] * foto["h"]:
            return None
        return {"regiao": regiao(((ix0 + ix1) / 2 - foto["x"]) / foto["w"], ((iy0 + iy1) / 2 - foto["y"]) / foto["h"]),
                "largura_pct": round(100 * (ix1 - ix0) / foto["w"]), "area_pct": round(100 * area / (foto["w"] * foto["h"]))}
    for nome in ("titulo", "numero", "preco", "subtitulo"):
        a = c["alvos"].get(nome)
        if a:
            z = sobre_a_foto(a["x"], a["y"], a["x"] + a["w"], a["y"] + a["h"])
            if z:
                out["texto"].append(dict(z, alvo=nome))
    # o texto corrido e as listas (a caixa de direitos da cota, o corpo, as regiões) e o escudo também cobrem a foto: na
    # página de foto inteira com painel de texto (cota a, contato b, capa c), é essa a área que precisa ficar calma. Teste
    # da A.M.E (09/10): o prompt da cota Master não dizia nada do painel de texto à esquerda.
    for nome, partes in (("texto", TEXTO_CORRIDO), ("logo", ("logo", "lettering"))):
        caixas = [a for k, a in c["alvos"].items() if k.split(":")[0] in partes and isinstance(a, dict) and a.get("w")]
        if caixas:
            x0, y0 = min(a["x"] for a in caixas), min(a["y"] for a in caixas)
            x1, y1 = max(a["x"] + a["w"] for a in caixas), max(a["y"] + a["h"] for a in caixas)
            z = sobre_a_foto(x0, y0, x1, y1)
            if z:
                out["texto"].append(dict(z, alvo=nome))
    if c.get("caixa"):
        z = sobre_a_foto(*c["caixa"], minimo=ELEMENTO_MINIMO)
        if z:
            out["elemento"] = z
    return out


def _lado_pela_ancora(anc):
    """('left'|'center'|'right', 'upper'|'middle'|'lower') que a âncora diz (sem a caixa resolvida); None se ela não diz."""
    h = v = None
    if anc.get("relacao") == "sangra":
        h = {"left": "left", "right": "right"}.get(BORDAS.get(anc.get("borda")))
        v = {"top": "upper", "bottom": "lower"}.get(BORDAS.get(anc.get("borda")))
    if anc.get("relacao") == "sobrepoe":
        h = {"left": "left", "right": "right"}.get(BORDAS.get(anc.get("lado")))
        v = {"top": "upper", "bottom": "lower"}.get(BORDAS.get(anc.get("lado")))
    for eixo, txt in (("x", anc.get("x")), ("y", anc.get("y"))):
        borda = (txt or "").split("=", 1)[0]
        if eixo == "x" and borda in ("esq", "dir", "cx") and h is None:
            h = {"esq": "left", "dir": "right", "cx": "center"}[borda]
        if eixo == "y" and borda in ("topo", "base", "cy") and v is None:
            v = {"topo": "upper", "base": "lower", "cy": "middle"}[borda]
    return (h or "center", v or "middle") if (h or v) else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("pasta"); ap.add_argument("pagina"); ap.add_argument("--elemento"); ap.add_argument("--receita")
    ap.add_argument("--vertical", action="store_true")
    a = ap.parse_args()
    try:
        print(json.dumps(contexto(a.pasta, a.pagina, a.elemento, a.receita, a.vertical), ensure_ascii=False, indent=1, default=str))
    except ErroComposicaoPrompt as e:
        print(f"erro: {e}", file=sys.stderr)
        sys.exit(64)


if __name__ == "__main__":
    main()

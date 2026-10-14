#!/usr/bin/env python3
"""
qa_geometria.py (Frente A): colisão REAL entre elementos e o que é protegido, lida do plano que o render grava
(saida/plano-elementos-<receita>[-vertical].json; formato em schema/elementos.schema.json#/definitions/plano_elementos).

Uso: python3 qa_geometria.py <pasta-do-kit> [--plano <arquivo.json>]
Sai com 1 em qualquer FALHA. O qa.py chama `checar(pasta, direcoes)` e soma as falhas e os avisos.

Regras. Pixel opaco = alfa > 32 na máscara do PNG de uso (girada, escalada e posta na página como o CSS faz); grafismo
svg = a caixa dele (girada), menos a liga (fio, colchetes, moldura), que conta só o TRAÇO da geometria declarada (uma
moldura em volta de um título não cobre o título). As caixas protegidas são por LINHA de texto
(Range.getClientRects), medidas no render final.
  - linha de corpo, preço, número ou micro coberta em mais de 4% da área: FALHA
  - linha de título coberta em mais de 8%: FALHA
    exceção: elemento na camada `atras` atrás de título ou número não reprova se o contraste do texto, amostrado no PNG
    do render final na parte coberta, continua passando (3:1, texto grande); sem PNG desse render, reprova
  - encostar em logo, etiqueta ou crédito (1 px opaco na caixa + 2 px de folga): FALHA
  - encostar no fio: aviso (o fio pinta por cima do elemento)
  - cobrir mais de 2% de uma zona vendável da foto (painel "SEU LOGO AQUI" do compor.py, foco do acervo): FALHA
  - elemento × elemento (herói, apoio, constante) sobrepostos em mais de 10% da menor área: FALHA
  - por página: mais de 1 herói, 1 apoio ou 1 pattern: FALHA (constante não conta)
  - pattern é textura de fundo: fica fora da conta de cobertura; a legibilidade sobre ele é o contraste do qa.py
Composição (composicao.py, references/09-composicao.md), sobre o render FINAL (`alvos` e `dom` da página):
  - composição que não valida (schema estrito ou regra: âncora sem os dois eixos, nenhum eixo em conteúdo, id
    inexistente, âncora de constante fora dos alvos estruturais): FALHA
  - âncora que não resolveu na página (alvo ausente, restrição inválida, asset que não existe): FALHA
  - âncora declarada e não cumprida (cada restrição recalculada com os alvos finais contra a tinta, 2 px): FALHA
  - item da composição cujo DOM difere do plano em mais de 1 px: FALHA
  - herói, apoio ou estrutura vindo do catálogo (sem âncora nos dois eixos) num kit com `composicao`: FALHA; kit
    legado: AVISO
  - constante fora da caixa única (selo, microtexto, faixa: a mesma caixa, ±2 px, em toda página da receita e do
    formato): FALHA
  - solto: nenhuma borda ou eixo da tinta a ≤ 2 px de uma linha de CONTEÚDO (bordas, linha de base e cap de texto;
    bordas de foto, painel, logo e blocos), não sangra e não sobrepõe nem liga alvo declarado; margem, coluna e
    página só contam para acabamento e constante: AVISO
  - escala fora do degrau (`ancora.degrau` false) ou grafismo esticado; o mesmo herói ou apoio em tamanhos diferentes
    sem degrau: AVISO
  - confete: tinta com menos de 1,5% da página e função fora de organização e acabamento (liga não conta): AVISO
Camada de acabamento (mk-2.1, references/10-acabamento.md, seção QA). Só existe em plano de kit que declara a camada
(papel acabamento, efeito, cruza, derivado_de, âncora registro); plano de kit mk-2.0 não passa por nenhuma delas:
  - mais de 2 elementos de papel acabamento numa página (o 3º reprova; derivado não conta): FALHA
  - item derivado (`derivado_de`: a sombra e o reflexo do objeto) fica fora da conta de herói, apoio e pattern, não
    conta sobreposição contra o pai nem contra o irmão e não é "solto" (a posição é a do pai)
  - acabamento com opacidade até .24 atrás ou sob o véu não conta na sobreposição elemento × elemento
  - acabamento translúcido (opacidade < 1 ou esmaecer) atrás ou sob o véu de linha de corpo, preço, número ou micro:
    os 4% dão lugar ao contraste amostrado no PNG (FALHA se cair abaixo de 4,5:1; número, 3:1; sem PNG, FALHA);
    textura sob texto corrido que passa no contraste: AVISO
  - `cruza`: a linha do alvo (título ou número) mais coberta aceita até 20%, uma linha só, com contraste amostrado
    (3:1); passa com AVISO fixo; acima de 20%, sem PNG ou com contraste baixo: FALHA
  - âncora `registro`: a caixa do item no DOM tem de ser a da conta de object-fit sobre a foto (mapeada pelo alfa_bbox
    do recorte), 1 px de folga; `ancora.caixa` gravada pelo render, idem: FALHA
  - acabamento na cor da marca com opacidade a partir de .46: AVISO
  - máscara da tinta: SVG de papel acabamento com PNG rasterizado em `uso` usa o alfa dele (sem PNG, a caixa cheia)
"""
import json, math, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import composicao  # noqa: E402

LIMITE = {"corpo": 0.04, "preco": 0.04, "numero": 0.04, "micro": 0.04, "titulo": 0.08}
ENCOSTA = ("logo", "etiqueta", "credito")
ALFA = 32
SOBREPOSICAO = 0.10
LIMITE_VENDAVEL = 0.02
TOL_ANCORA = composicao.TOLERANCIA       # 2 px
TOL_DOM = 1.0
TOL_CAIXA = 2.0
CONFETE = 0.015
# alvos que são marca, não conteúdo: não ancoram o elemento (o fio de progresso, o crédito da foto, a etiqueta)
NAO_CONTEUDO = ("pagina", "margem", "colunas", "fio", "credito", "etiqueta")

# camada de acabamento (mk-2.1): limites da seção QA de references/10-acabamento.md
MAX_ACABAMENTO = 2
OPACIDADE_LEVE = 0.24          # atrás ou sob o véu, até aqui o acabamento não conta na sobreposição
OPACIDADE_FORTE = 0.46         # na cor da marca, daqui para cima: aviso
LIMITE_CRUZA = 0.20            # a linha do alvo do cruza (uma só) aceita até isto coberto, com contraste
TOL_REGISTRO = 1.0
SOB = ("atras", "sob-veu")
CONTRASTE_SOB = {"corpo": 4.5, "preco": 4.5, "micro": 4.5, "numero": 3.0}    # acabamento translúcido sob a linha
TEXTURAS = ("textura", "pattern", "tipo-textura", "pattern-simbolo", "meio-tom-simbolo", "grade-pontos", "listras",
            "mosaico", "hachura", "malha", "pontos-radiais", "ondas", "curvas-nivel", "meio-tom-foto")


def opacidade(it):
    """Opacidade efetiva do item: `efeito.opacidade` vence `opacidade` (precedência 1 de references/10); sem as duas, 1."""
    v = (it.get("efeito") or {}).get("opacidade", it.get("opacidade", 1))
    try:
        return float(v)
    except (TypeError, ValueError):
        return 1.0


def translucido(it):
    return opacidade(it) < 1 or bool((it.get("efeito") or {}).get("esmaecer"))


def cruza_do_item(it):
    """O `cruza` do item: o render grava `cruza` {alvo, corte, y} no item; sem ele, o da composição em `efeito`."""
    c = it.get("cruza") or (it.get("efeito") or {}).get("cruza")
    return c if isinstance(c, dict) else None


def acabamento_leve(it):
    """Acabamento atrás (ou sob o véu) com opacidade até .24: não conta na sobreposição elemento × elemento."""
    return it.get("papel") == "acabamento" and it.get("camada") in SOB and opacidade(it) <= OPACIDADE_LEVE + 1e-9


def parentes(a, b):
    """O item derivado (sombra, reflexo) e o pai dele, ou dois derivados do mesmo pai."""
    da, db = a.get("derivado_de"), b.get("derivado_de")
    return bool((da and da == b.get("id")) or (db and db == a.get("id")) or (da and da == db))


def _el_do_kit(kit, eid):
    return next((e for e in (kit or {}).get("elementos") or [] if isinstance(e, dict) and e.get("id") == eid), None)


def eh_textura(it, kit=None):
    """Textura: tipo de textura ou pattern (do elemento em elementos[] ou do grafismo), ou recurso da família
    pattern-textura."""
    el = _el_do_kit(kit, it.get("id")) or _el_do_kit(kit, it.get("derivado_de")) or {}
    if el.get("tipo") in TEXTURAS or (it.get("grafismo") or {}).get("tipo") in TEXTURAS:
        return True
    rid = it.get("recurso")
    dc = (kit or {}).get("direcao_criativa") or {}
    return any(isinstance(r, dict) and r.get("id") == rid and r.get("familia") == "pattern-textura"
               for r in dc.get("recursos") or []) if rid else False


def cor_da_marca(it, kit=None, receita=None):
    """O item pinta na cor da marca? Cor do grafismo (chave `marca` da paleta ou o #hex dela), `cor` ou `cor_chapada`."""
    marcas = set()
    for r in (kit or {}).get("receitas") or []:
        if isinstance(r, dict) and (receita is None or r.get("id") == receita):
            marcas.add(str((r.get("paleta") or {}).get("marca") or "").upper())
    marcas.add(str(((kit or {}).get("marca") or {}).get("cor_primaria") or "").upper())
    marcas.discard("")
    for c in ((it.get("grafismo") or {}).get("params") or {}).get("cor"), it.get("cor"), it.get("cor_chapada"):
        if isinstance(c, str) and (c == "marca" or c.upper() in marcas):
            return True
    return False


def _posicao(tok, sobra):
    tok = str(tok).strip()
    nomes = {"left": 0.0, "top": 0.0, "center": 0.5, "right": 1.0, "bottom": 1.0}
    if tok in nomes:
        return sobra * nomes[tok]
    if tok.endswith("%"):
        return sobra * float(tok[:-1]) / 100.0
    if tok.endswith("px"):
        return float(tok[:-2])
    return sobra * 0.5


def caixa_object_fit(foto):
    """(x, y, w, h) da imagem DESENHADA na moldura da foto: a conta do object-fit e do object-position que o navegador
    faz (o render mede `img.fit`, `img.pos`, `img.nat_w`, `img.nat_h` no alvo). Sem `img`, a moldura."""
    x, y, w, h = (float(foto[k]) for k in ("x", "y", "w", "h"))
    img = foto.get("img") or {}
    nw, nh = float(img.get("nat_w") or 0), float(img.get("nat_h") or 0)
    if nw <= 0 or nh <= 0:
        return x, y, w, h
    fit = img.get("fit") or "fill"
    if fit == "fill":
        return x, y, w, h
    s = {"cover": max(w / nw, h / nh), "contain": min(w / nw, h / nh), "none": 1.0,
         "scale-down": min(1.0, min(w / nw, h / nh))}.get(fit, max(w / nw, h / nh))
    dw, dh = nw * s, nh * s
    pos = str(img.get("pos") or "50% 50%").split()
    px, py = (pos + ["center", "center"])[:2] if len(pos) != 1 else (pos[0], "center")
    return x + _posicao(px, w - dw), y + _posicao(py, h - dh), dw, dh


def checar_registro(it, alvos, dom=None):
    """Erros da âncora `registro`: o recorte da foto tem de cair na caixa da própria foto. A caixa da imagem desenhada
    sai da conta de object-fit sobre o alvo; a do item é ela mapeada pelo `alfa_bbox` do recorte, na escala do PNG de
    origem (`ancora.registro.img`). Confere `ancora.caixa` (gravada pelo render) e a caixa do item no DOM, 1 px."""
    anc = it.get("ancora") or {}
    nome = anc.get("alvo") or "foto"
    foto = (alvos or {}).get(nome)
    if not isinstance(foto, dict) or "x" not in foto:
        return [f"o alvo `{nome}` não foi medido na página: a caixa do registro não tem como ser conferida"]
    D = caixa_object_fit(foto)
    fmt = lambda c: f"({c[0]:.1f}, {c[1]:.1f}, {c[2]:.1f}×{c[3]:.1f})"  # noqa: E731
    erros = []
    cx = anc.get("caixa")
    if isinstance(cx, (list, tuple)) and len(cx) == 4:
        dv = max(abs(float(a) - b) for a, b in zip(cx, D))
        if dv > TOL_REGISTRO:
            erros.append(f"a caixa calculada pelo render {fmt(cx)} não é a conta de object-fit sobre `{nome}` {fmt(D)}: "
                         f"{dv:.1f} px (limite {TOL_REGISTRO:.0f} px)")
    img = (anc.get("registro") or {}).get("img")
    bb = it.get("alfa_bbox")
    if img and bb and len(img) == 2 and len(bb) == 4 and img[0] and img[1]:
        sx, sy = D[2] / float(img[0]), D[3] / float(img[1])
        E = (D[0] + bb[0] * sx, D[1] + bb[1] * sy, (bb[2] - bb[0]) * sx, (bb[3] - bb[1]) * sy)
    else:
        E = D
    caixa = (dom["x"], dom["y"], dom["w"], dom["h"]) if dom else _aabb(it)
    dv = max(abs(float(a) - b) for a, b in zip(caixa, E))
    if dv > TOL_REGISTRO:
        erros.append(f"{'desenhado' if dom else 'planejado'} em {fmt(caixa)} e a conta de object-fit sobre `{nome}` dá "
                     f"{fmt(E)}: {dv:.1f} px (limite {TOL_REGISTRO:.0f} px); a figura sai do lugar em que está na foto")
    return erros


def _png_do_svg(item, pasta):
    """PNG rasterizado do SVG de acabamento (`uso`), quando o render gravou: a máscara da tinta sai do alfa dele."""
    u = item.get("uso")
    if item.get("formato") != "svg" or item.get("papel") != "acabamento" or not u or not str(u).lower().endswith(".png"):
        return None
    from caminhos import ForaDoKit, dentro_do_kit
    try:
        p = dentro_do_kit(pasta, u)                       # o plano é dado: caminho que sai da pasta do kit não é lido
    except ForaDoKit:
        return None
    return p if p.is_file() else None


def mascara(item, pasta, limiar=ALFA):
    """(máscara booleana, x0, y0) do item na página: PNG de uso (ou a origem cortada no alfa_bbox) escalado à caixa e
    girado em torno do centro dela; liga = o traço da geometria declarada; outro svg = a caixa cheia. `limiar` = alfa
    mínimo do pixel que conta (32 para cobertura; 127 para a tinta)."""
    from PIL import Image, ImageDraw
    import numpy as np
    w, h = max(1, round(item["w"])), max(1, round(item["h"]))
    a = None
    geo = (item.get("ancora") or {}).get("geometria") or {}
    if item.get("formato") == "svg" and (geo.get("pontos") or geo.get("caixa")):
        # máscara real do grafismo preso a geometria: o traço com a espessura (não a caixa cheia)
        a = Image.new("L", (w, h), 0)
        dr = ImageDraw.Draw(a)
        esp = max(1, int(round(float(geo.get("espessura") or 2))))
        ox, oy = float(item["x"]), float(item["y"])
        if geo.get("pontos"):
            dr.line([(p[0] - ox, p[1] - oy) for p in geo["pontos"]], fill=255, width=esp)
        else:
            x, y, cw, ch = geo["caixa"]
            dr.rectangle([x - ox, y - oy, x - ox + cw - 1, y - oy + ch - 1], outline=255, width=esp)
    elif _png_do_svg(item, pasta):
        # SVG de acabamento rasterizado pelo render: a tinta real (uma malha ou uma hachura grande não cobre a caixa toda)
        a = Image.open(_png_do_svg(item, pasta)).convert("RGBA").getchannel("A").resize((w, h), Image.BILINEAR)
    elif item.get("formato") != "svg":
        fonte = None
        if item.get("uso") and (Path(pasta) / item["uso"]).exists():
            fonte = Image.open(Path(pasta) / item["uso"])
        elif item.get("arquivo") and (Path(pasta) / item["arquivo"]).exists():
            fonte = Image.open(Path(pasta) / item["arquivo"])
            if item.get("alfa_bbox"):
                fonte = fonte.crop(tuple(item["alfa_bbox"]))
        if fonte is not None:
            a = fonte.convert("RGBA").getchannel("A").resize((w, h), Image.BILINEAR)
    if a is None:
        a = Image.new("L", (w, h), 255)
    if item.get("espelhar") and item.get("formato") != "svg":
        # o CSS faz rotate(r) scaleX(-1): espelha primeiro, gira depois
        a = a.transpose(Image.FLIP_LEFT_RIGHT)
    rot = float(item.get("rot") or 0)
    if rot:
        a = a.rotate(-rot, resample=Image.BILINEAR, expand=True)  # CSS gira no sentido horário; o PIL, no anti-horário
    m = np.asarray(a) > limiar
    cx, cy = item["x"] + item["w"] / 2, item["y"] + item["h"] / 2
    return m, int(round(cx - m.shape[1] / 2)), int(round(cy - m.shape[0] / 2))


def pixels_em(m, ox, oy, x0, y0, x1, y1):
    lx0, ly0 = max(0, math.floor(x0) - ox), max(0, math.floor(y0) - oy)
    lx1, ly1 = min(m.shape[1], math.ceil(x1) - ox), min(m.shape[0], math.ceil(y1) - oy)
    if lx1 <= lx0 or ly1 <= ly0:
        return 0
    return int(m[ly0:ly1, lx0:lx1].sum())


def sobreposicao(a, b):
    (ma, ax, ay), (mb, bx, by) = a, b
    x0, y0 = max(ax, bx), max(ay, by)
    x1, y1 = min(ax + ma.shape[1], bx + mb.shape[1]), min(ay + ma.shape[0], by + mb.shape[0])
    if x1 <= x0 or y1 <= y0:
        return 0
    return int((ma[y0 - ay:y1 - ay, x0 - ax:x1 - ax] & mb[y0 - by:y1 - by, x0 - bx:x1 - bx]).sum())


def area_na_pagina(m, ox, oy, W, H):
    return pixels_em(m, ox, oy, 0, 0, W, H)


def cobertura_zona(m, ox, oy, z):
    """Fração da zona vendável (o quad do painel, ou a caixa) coberta por pixel opaco do elemento."""
    from PIL import Image, ImageDraw
    import numpy as np
    x0, y0 = math.floor(z["x"]), math.floor(z["y"])
    x1, y1 = math.ceil(z["x"] + z["w"]), math.ceil(z["y"] + z["h"])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    zona = Image.new("L", (x1 - x0, y1 - y0), 0)
    if z.get("quad"):
        ImageDraw.Draw(zona).polygon([(p[0] - x0, p[1] - y0) for p in z["quad"]], fill=255)
    else:
        zona.paste(255, (0, 0, x1 - x0, y1 - y0))
    zm = np.asarray(zona) > 0
    area = int(zm.sum())
    if not area:
        return 0.0
    el = np.zeros_like(zm)
    lx0, ly0, lx1, ly1 = max(x0, ox), max(y0, oy), min(x1, ox + m.shape[1]), min(y1, oy + m.shape[0])
    if lx1 > lx0 and ly1 > ly0:
        el[ly0 - y0:ly1 - y0, lx0 - x0:lx1 - x0] = m[ly0 - oy:ly1 - oy, lx0 - ox:lx1 - ox]
    return float((el & zm).sum()) / area


# ------------------------------------------------------------------------------------------------- contraste
def _lum(rgb):
    import numpy as np
    c = np.where(rgb <= 0.03928, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def contraste_amostrado(png, linha, textos, regiao=None, minimo=3.0):
    """(razão, mínimo) do texto da linha sobre o que está atrás dele, amostrado no PNG do render final: a mesma conta do
    qa.py (WCAG; cor do texto do render-report; pior lado do fundo, percentis 10 e 90, como no texto sobre pattern),
    restrita à parte da linha que o elemento cobre (`regiao`). Os pixels de letra e a borda deles (2 px de antialias)
    saem do fundo. None quando não há PNG deste render."""
    if not png or not Path(png).exists():
        return None
    from PIL import Image
    import numpy as np
    im = np.asarray(Image.open(png).convert("RGB"), dtype=float) / 255.0
    H, W = im.shape[:2]
    x0, y0 = max(0, int(math.floor(linha["x"]))), max(0, int(math.floor(linha["y"])))
    x1, y1 = min(W, int(math.ceil(linha["x"] + linha["w"]))), min(H, int(math.ceil(linha["y"] + linha["h"])))
    if regiao:
        rx0, ry0, rx1, ry1 = max(x0, regiao[0]), max(y0, regiao[1]), min(x1, regiao[2]), min(y1, regiao[3])
        if rx1 - rx0 >= 4 and ry1 - ry0 >= 4:
            x0, y0, x1, y1 = rx0, ry0, rx1, ry1
    if x1 - x0 < 2 or y1 - y0 < 2:
        return None
    L = _lum(im[y0:y1, x0:x1])
    cor = None
    melhor = 0.0
    for t in textos or []:
        ix = max(0.0, min(t["x"] + t["w"], linha["x"] + linha["w"]) - max(t["x"], linha["x"]))
        iy = max(0.0, min(t["y"] + t["h"], linha["y"] + linha["h"]) - max(t["y"], linha["y"]))
        if ix * iy > melhor and t.get("cor"):
            melhor, cor = ix * iy, t["cor"]
    if cor:
        h = cor.lstrip("#")
        tl = float(_lum(np.array([[[int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]]]))[0, 0])
    else:
        tl = float(L.max()) if float(np.median(L)) < 0.5 else float(L.min())
    letra = np.abs(L - tl) < 0.12
    if letra.any():
        from PIL import ImageFilter
        letra = np.asarray(Image.fromarray((letra * 255).astype("uint8")).filter(ImageFilter.MaxFilter(5))) > 0
    fundo = L[~letra]
    if fundo.size < 20:
        return 99.0, minimo
    piores = (float(np.percentile(fundo, 10)), float(np.percentile(fundo, 90)))
    razao = min((max(tl, b) + 0.05) / (min(tl, b) + 0.05) for b in piores)
    return razao, minimo


# ------------------------------------------------------------------------------------------------- composição
def _aabb(it):
    r = math.radians(float(it.get("rot") or 0))
    c, s = abs(math.cos(r)), abs(math.sin(r))
    A, B = it["w"] * c + it["h"] * s, it["w"] * s + it["h"] * c
    cx, cy = it["x"] + it["w"] / 2, it["y"] + it["h"] / 2
    return cx - A / 2, cy - B / 2, A, B


def linhas_de_referencia(alvos, estruturais=False):
    """(xs, ys) das linhas a que um elemento pode se prender: as de CONTEÚDO (bordas e centros de texto, foto, painel,
    logo e blocos; linha de base e cap de cada linha de texto) e, com `estruturais`, margem, colunas e página."""
    xs, ys = set(), set()

    def caixa(a):
        x, y, w, h = float(a["x"]), float(a["y"]), float(a["w"]), float(a["h"])
        xs.update((x, x + w, x + w / 2)); ys.update((y, y + h, y + h / 2))

    for nome, a in (alvos or {}).items():
        if nome.split(":")[0] in NAO_CONTEUDO or not isinstance(a, dict) or "x" not in a:
            continue
        caixa(a)
        for l in a.get("linhas") or []:
            caixa(l)
            for k in ("linha_base", "cap"):
                if k in l:
                    ys.add(float(l[k]))
    if estruturais and alvos:
        for nome in ("margem", "pagina"):
            if isinstance(alvos.get(nome), dict):
                caixa(alvos[nome])
        for c in alvos.get("colunas") or []:
            xs.update((float(c["x"]), float(c["x"]) + float(c["w"])))
    return sorted(xs), sorted(ys)


def esta_solto(tinta, xs, ys, W, H, tol=TOL_ANCORA):
    """Nenhuma borda nem eixo da tinta a ≤ tol de uma linha da lista e não sangra (nem encosta na borda da página)."""
    x0, y0, x1, y1 = tinta
    ex, ey = (x0, (x0 + x1) / 2, x1), (y0, (y0 + y1) / 2, y1)
    if any(abs(e - l) <= tol for e in ex for l in xs) or any(abs(e - l) <= tol for e in ey for l in ys):
        return False
    if x0 <= tol or y0 <= tol or x1 >= W - tol or y1 >= H - tol:
        return False
    return True


def tinta_final(it, pasta, dom=None):
    """(x0, y0, x1, y1) da tinta do item na página do render final: a da âncora deslocada pelo que o DOM mostrou; sem
    âncora, a caixa dos pixels com alfa ≥ 128 do PNG de uso (svg: a caixa, ou o traço da liga)."""
    anc = it.get("ancora") or {}
    dx = dy = 0.0
    if dom:
        bx, by, bw, bh = _aabb(it)
        dx, dy = (dom["x"] + dom["w"] / 2) - (bx + bw / 2), (dom["y"] + dom["h"] / 2) - (by + bh / 2)
    if anc.get("tinta"):
        t = anc["tinta"]
        return (t[0] + dx, t[1] + dy, t[2] + dx, t[3] + dy), (dx, dy)
    if it.get("formato") == "svg":
        # svg sem geometria: a caixa exata (a máscara arredondaria a borda para o pixel inteiro)
        x, y, w, h = _aabb(it)
        return (x + dx, y + dy, x + w + dx, y + h + dy), (dx, dy)
    import numpy as np
    m, ox, oy = mascara(it, pasta, limiar=127)
    ys, xs = np.nonzero(m)
    if not len(xs):
        x, y, w, h = _aabb(it)
        return (x + dx, y + dy, x + w + dx, y + h + dy), (dx, dy)
    return (ox + xs.min() + dx, oy + ys.min() + dy, ox + xs.max() + 1 + dx, oy + ys.max() + 1 + dy), (dx, dy)


def _canto(x, y, w, h, W, H):
    return ("sup" if y + h / 2 < H / 2 else "inf") + "-" + ("esq" if x + w / 2 < W / 2 else "dir")


def _agrupa(valores, tol=TOL_CAIXA):
    grupos = []
    for v in sorted(valores):
        if grupos and abs(v - grupos[-1][-1]) <= tol:
            grupos[-1].append(v)
        else:
            grupos.append([v])
    return [round(g[0]) for g in grupos]


def _n(k, palavra):
    """'1 canto', '2 cantos', '2 inícios'."""
    return f"{k} {palavra}" if k == 1 else f"{k} {palavra}s"


def checar_constantes(paginas, W, H, pre=""):
    """Constante fora da caixa única: o mesmo id em caixas diferentes (mais de 2 px) entre as páginas do plano. A caixa
    de referência é a mais usada; a mensagem diz em quantos cantos, alturas e tamanhos a constante andou."""
    falhas = []
    por_id = {}
    for pg in paginas:
        for it in pg.get("elementos", []):
            if it.get("papel") == "constante":
                por_id.setdefault(it["id"], []).append((pg.get("n"), it))
    for cid, lst in por_id.items():
        grupos = []
        for n, it in lst:
            b = (float(it["x"]), float(it["y"]), float(it["w"]), float(it["h"]))
            g = next((g for g in grupos if all(abs(a - c) <= TOL_CAIXA for a, c in zip(g["caixa"], b))), None)
            if g:
                g["pags"].append(n)
            else:
                grupos.append({"caixa": b, "pags": [n]})
        if len(grupos) < 2:
            continue
        ref = max(grupos, key=lambda g: (len(g["pags"]), -g["pags"][0]))
        caixas = [(n, (float(it["x"]), float(it["y"]), float(it["w"]), float(it["h"]))) for n, it in lst]
        partes = []
        if all(c[2] < W / 2 for _, c in caixas):
            cantos = {}
            for n, c in caixas:
                cantos.setdefault(_canto(*c, W, H), []).append(c)
            principal = max(cantos, key=lambda k: len(cantos[k]))
            alt = _agrupa([c[1] for c in cantos[principal]])
            partes.append(f"{_n(len(cantos), 'canto')} ({', '.join(f'{k} em {len(v)} p.' for k, v in sorted(cantos.items(), key=lambda kv: -len(kv[1])))})")
            partes.append(f"no canto {principal}, {_n(len(alt), 'altura')} (y = {', '.join(map(str, alt))})")
        else:
            alt = _agrupa([c[1] for _, c in caixas])
            partes.append(f"{_n(len(alt), 'altura')} (y = {', '.join(map(str, alt))})")
            xs = _agrupa([c[0] for _, c in caixas])
            if len(xs) > 1:
                partes.append(f"{_n(len(xs), 'início')} (x = {', '.join(map(str, xs))})")
        larg = _agrupa([c[2] for _, c in caixas])
        if len(larg) > 1:
            partes.append(f"{len(larg)} larguras ({', '.join(map(str, larg))})")
        x, y, w, h = ref["caixa"]
        fora = sorted(n for g in grupos if g is not ref for n in g["pags"])
        falhas.append(f"{pre}constante `{cid}` fora da caixa única: {len(grupos)} caixas em {len(lst)} páginas; "
                      f"{'; '.join(partes)}. A mais usada é ({x:.0f}, {y:.0f}, {w:.0f}×{h:.0f}) em "
                      f"p.{', '.join(map(str, ref['pags']))}; fora dela: p.{', '.join(map(str, fora))}")
    return falhas


def checar_escala(paginas, pre=""):
    """O mesmo herói ou apoio em tamanhos diferentes sem degrau (catálogo, manual ou px solto): é o que a Sprint mostrou
    (o mesmo asset em 560 px numa página e 284 px em outra)."""
    avisos = []
    por_id = {}
    for pg in paginas:
        for it in pg.get("elementos", []):
            if it.get("papel") not in ("heroi", "apoio") or (it.get("ancora") or {}).get("degrau") is True:
                continue
            por_id.setdefault(it["id"], []).append((pg.get("n"), float(it["w"]), float(it["h"])))
    for i, lst in por_id.items():
        tamanhos = []
        for n, w, h in lst:
            t = next((t for t in tamanhos if abs(t[0] - w) <= 0.02 * max(w, t[0]) and abs(t[1] - h) <= 0.02 * max(h, t[1])), None)
            if t:
                t[2].append(n)
            else:
                tamanhos.append([w, h, [n]])
        if len(tamanhos) > 1:
            desc = ", ".join(f"{t[0]:.0f}×{t[1]:.0f} (p.{', '.join(map(str, t[2]))})" for t in tamanhos)
            avisos.append(f"{pre}escala: `{i}` em {len(tamanhos)} tamanhos fora do degrau: {desc}; declare a escala em "
                          f"degrau na composição (references/09 §4)")
    return avisos


def _cobertura_relaxada(it, m, ox, oy, protegidos):
    """Índice da linha do alvo do `cruza` que ganha o limite de 20% (a mais coberta, se não passar de 20%), ou None."""
    c = cruza_do_item(it)
    if not c:
        return None
    alvo = c.get("alvo")
    cands = []
    for i, p in enumerate(protegidos):
        if p["classe"] != alvo or LIMITE.get(alvo) is None:
            continue
        cob = pixels_em(m, ox, oy, p["x"], p["y"], p["x"] + p["w"], p["y"] + p["h"]) / max(1.0, p["w"] * p["h"])
        if cob > LIMITE[alvo]:
            cands.append((cob, i))
    if not cands:
        return None
    cob, i = max(cands)
    return i if cob <= LIMITE_CRUZA else None


def checar_plano(plano, pasta, prefixo="", png=None, textos=None, kit=None):
    """Falhas e avisos de um plano (dict). `prefixo` identifica a receita no texto (ex.: 'r3'). `png(n)` = caminho do PNG
    da página n DESTE render (ou None) e `textos(n)` = as caixas de texto com cor do render-report: com eles, o elemento
    da camada atras atrás de título ou número passa se o contraste amostrado continua passando. `kit` (o mediakit.json,
    opcional) diz o que é textura e qual é a cor da marca nas regras da camada de acabamento."""
    falhas, avisos = [], []
    W, H = float(plano.get("largura", 1920)), float(plano.get("altura", 1080))
    pre = f"{prefixo} " if prefixo else ""
    kit_comp = bool(plano.get("composicao_kit"))
    for e in plano.get("composicao_erros") or []:
        falhas.append(f"{pre}composição: {e}")
    paginas = plano.get("paginas", [])
    sem_alvos = []
    for pg in paginas:
        n, rot = pg.get("n"), pg.get("rotulo", "?")
        onde = f"{pre}p.{n} {rot}"
        for e in pg.get("erros_composicao") or []:
            falhas.append(f"{onde}: âncora não resolveu: {e}")
        itens = pg.get("elementos", [])
        conta = {}
        for it in itens:
            if it.get("derivado_de"):
                continue                                  # sombra e reflexo são do pai: não somam herói, apoio nem acabamento
            conta[it["papel"]] = conta.get(it["papel"], 0) + 1
        for papel in ("heroi", "apoio", "pattern"):
            if conta.get(papel, 0) > 1:
                ids = ", ".join(i["id"] for i in itens if i["papel"] == papel and not i.get("derivado_de"))
                falhas.append(f"{onde}: {conta[papel]} elementos de papel {papel} ({ids}); limite 1 por página")
        if conta.get("acabamento", 0) > MAX_ACABAMENTO:
            chave = (pg.get("composicao") or {}).get("chave")
            ja = any(str(e).startswith(f"composicao/{chave}: ") and "papel acabamento (máximo" in str(e)
                     for e in plano.get("composicao_erros") or []) if chave else False
            if not ja:
                ids = ", ".join(i["id"] for i in itens if i["papel"] == "acabamento" and not i.get("derivado_de"))
                falhas.append(f"{onde}: {conta['acabamento']} elementos de papel acabamento ({ids}); limite "
                              f"{MAX_ACABAMENTO} por página (o 3º reprova; sombra e reflexo derivados não contam)")
        masks = {}
        for it in itens:
            if it["papel"] == "pattern":
                continue
            m, ox, oy = mascara(it, pasta)
            masks[id(it)] = (m, ox, oy)
            area = area_na_pagina(m, ox, oy, W, H)
            if m.sum() and area < 0.5 * m.sum():
                avisos.append(f"{onde}: `{it['id']}` tem {1 - area / m.sum():.0%} da área fora da página")
            if it.get("papel") == "acabamento" and opacidade(it) >= OPACIDADE_FORTE - 1e-9 and cor_da_marca(it, kit, plano.get("receita")):
                avisos.append(f"{onde}: `{it['id']}` (acabamento) na cor da marca com opacidade {opacidade(it):g}: o "
                              f"acabamento disputa com o conteúdo; use .24 ou menos, ou a cor do texto")
            protegidos = pg.get("protegidos", [])
            relaxada = _cobertura_relaxada(it, m, ox, oy, protegidos)
            for ip, p in enumerate(protegidos):
                cl = p["classe"]
                x0, y0, x1, y1 = p["x"], p["y"], p["x"] + p["w"], p["y"] + p["h"]
                if cl in ENCOSTA or cl == "fio":
                    toque = pixels_em(m, ox, oy, x0 - 2, y0 - 2, x1 + 2, y1 + 2)
                    if toque:
                        msg = f"{onde}: `{it['id']}` ({it['papel']}, {it['camada']}) encosta em {cl} {p.get('texto', '')!r} ({toque} px opacos)"
                        (avisos if cl == "fio" else falhas).append(msg)
                    continue
                lim = LIMITE.get(cl)
                if lim is None:
                    continue
                area_l = max(1.0, p["w"] * p["h"])
                cob = pixels_em(m, ox, oy, x0, y0, x1, y1) / area_l
                regiao = (ox, oy, ox + m.shape[1], oy + m.shape[0])
                if cob > lim and ip == relaxada:
                    # cruza declarado: a linha mais coberta do alvo aceita até 20%, se o texto continua legível
                    r = contraste_amostrado(png(n) if png else None, p, textos(n) if textos else None, regiao, 3.0)
                    if r is not None and r[0] >= r[1]:
                        avisos.append(f"{onde}: `{it['id']}` cruza o {cl}: cobre {cob:.0%} da linha {p.get('texto', '')!r} "
                                      f"(cruza declarado: até {LIMITE_CRUZA:.0%} numa linha) e o texto fica com contraste "
                                      f"{r[0]:.1f}:1 no PNG; confira na página que a palavra continua inteira")
                    else:
                        falhas.append(f"{onde}: `{it['id']}` cruza o {cl}: cobre {cob:.0%} da linha {p.get('texto', '')!r} "
                                      + ("e não há PNG deste render para amostrar o contraste (renderize com --png)" if r is None
                                         else f"e o contraste cai para {r[0]:.1f}:1 (mínimo {r[1]:.0f}:1)"))
                    continue
                if (cob > lim and it.get("papel") == "acabamento" and translucido(it) and it.get("camada") in SOB
                        and cl in CONTRASTE_SOB):
                    # acabamento translúcido sob o texto: o que vale é a leitura, amostrada no PNG, não os 4%
                    r = contraste_amostrado(png(n) if png else None, p, textos(n) if textos else None, regiao,
                                            CONTRASTE_SOB[cl])
                    if r is None:
                        falhas.append(f"{onde}: `{it['id']}` (acabamento translúcido, {it['camada']}) sob {cl}: {cob:.0%} da "
                                      f"linha {p.get('texto', '')!r} e não há PNG deste render para amostrar o contraste "
                                      f"(renderize com --png)")
                    elif r[0] < r[1]:
                        falhas.append(f"{onde}: `{it['id']}` (acabamento translúcido, {it['camada']}) sob {cl}: o contraste da "
                                      f"linha {p.get('texto', '')!r} cai para {r[0]:.1f}:1 (mínimo {r[1]:.1f}:1)")
                    elif cl == "corpo" and eh_textura(it, kit):
                        avisos.append(f"{onde}: `{it['id']}` é textura sob texto corrido ({cob:.0%} da linha "
                                      f"{p.get('texto', '')!r}): o contraste passa ({r[0]:.1f}:1), mas textura atrás de "
                                      f"parágrafo cansa a leitura; tire a textura da caixa do corpo ou ponha véu")
                    continue
                if cob > lim:
                    extra = ""
                    if it.get("camada") == "atras" and cl in ("titulo", "numero"):
                        # atrás do texto: o que importa é se o texto continua legível sobre o elemento
                        r = contraste_amostrado(png(n) if png else None, p, textos(n) if textos else None, regiao)
                        if r is not None and r[0] >= r[1]:
                            avisos.append(f"{onde}: `{it['id']}` (atras) cobre {cob:.0%} da linha {p.get('texto', '')!r}, "
                                          f"e o texto continua com contraste {r[0]:.1f}:1 (mínimo {r[1]:.0f}:1) no PNG")
                            continue
                        extra = (" (sem PNG deste render para amostrar o contraste: renderize com --png)" if r is None
                                 else f"; o contraste cai para {r[0]:.1f}:1 (mínimo {r[1]:.0f}:1)")
                    falhas.append(f"{onde}: `{it['id']}` ({it['papel']}, {it['camada']}) cobre {cl}: {cob:.0%} da linha "
                                  f"{p.get('texto', '')!r} (limite {lim:.0%}){extra}")
            for z in pg.get("vendaveis") or []:
                cob = cobertura_zona(m, ox, oy, z)
                if cob > LIMITE_VENDAVEL:
                    falhas.append(f"{onde}: `{it['id']}` ({it['papel']}, {it['camada']}) cobre {cob:.0%} da zona vendável "
                                  f"{z.get('texto', '')!r} da foto ({z.get('fonte', '?')}); limite {LIMITE_VENDAVEL:.0%}")
        nao_pattern = [it for it in itens if it["papel"] != "pattern"]
        for i in range(len(nao_pattern)):
            for j in range(i + 1, len(nao_pattern)):
                a, b = nao_pattern[i], nao_pattern[j]
                if parentes(a, b) or acabamento_leve(a) or acabamento_leve(b):
                    continue                              # sombra e reflexo sob o pai; acabamento leve atrás não ocupa
                ma, mb = masks[id(a)], masks[id(b)]
                menor = max(1, min(int(ma[0].sum()), int(mb[0].sum())))
                s = sobreposicao(ma, mb) / menor
                if s > SOBREPOSICAO:
                    falhas.append(f"{onde}: `{a['id']}` e `{b['id']}` sobrepostos em {s:.0%} da menor área (limite {SOBREPOSICAO:.0%})")
        # ---------- composição: âncora cumprida no render final, DOM = plano, catálogo sem âncora, solto, escala, confete
        alvos = pg.get("alvos")
        dom = {d["id"]: d for d in pg.get("dom") or []} if "dom" in pg else None
        if not alvos:
            sem_alvos.append(n)
        xs_c, ys_c = linhas_de_referencia(alvos) if alvos else ([], [])
        xs_e, ys_e = linhas_de_referencia(alvos, estruturais=True) if alvos else ([], [])
        for it in nao_pattern:
            anc = it.get("ancora") or {}
            rel = anc.get("relacao")
            d = dom.get(it["id"]) if dom is not None else None
            if it.get("origem") == "composicao":
                if dom is not None:
                    if d is None:
                        falhas.append(f"{onde}: `{it['id']}` da composição não está no DOM do render final")
                    else:
                        bx, by, bw, bh = _aabb(it)
                        desvio = max(abs(d["x"] - bx), abs(d["y"] - by), abs(d["w"] - bw), abs(d["h"] - bh))
                        if desvio > TOL_DOM:
                            falhas.append(f"{onde}: `{it['id']}` desenhado em ({d['x']}, {d['y']}, {d['w']}×{d['h']}) e o plano diz "
                                          f"({bx:.1f}, {by:.1f}, {bw:.1f}×{bh:.1f}): {desvio:.1f} px (limite {TOL_DOM:.0f} px)")
                if alvos:
                    _, desl = tinta_final(it, pasta, d)
                    for e in composicao.conferir(it, alvos, W, H, desl):
                        falhas.append(f"{onde}: `{it['id']}` âncora não cumprida: {e}")
                    if rel == "registro":
                        for e in checar_registro(it, alvos, d):
                            falhas.append(f"{onde}: `{it['id']}` registro: {e}")
                if anc.get("degrau") is False:
                    avisos.append(f"{onde}: `{it['id']}` escala fora do degrau ({anc.get('escala')}): use fração da página, "
                                  f"colunas ou altura de maiúscula")
                if anc.get("medida") == "esticada":
                    avisos.append(f"{onde}: `{it['id']}` grafismo esticado: o gerador não honrou a medida da escala")
            elif it["papel"] in ("heroi", "apoio", "estrutura"):
                msg = (f"{onde}: `{it['id']}` ({it['papel']}) veio do catálogo ({it.get('encaixe') or 'ajuste manual'}) sem "
                       f"âncora nos dois eixos")
                if kit_comp:
                    falhas.append(msg + ": escreva a composição desta página (references/09)")
                else:
                    avisos.append(msg + " (kit sem composição)")
            if not alvos or rel in ("sobrepoe", "liga") or it.get("derivado_de"):
                continue                                  # derivado: a posição é a do pai (sombra no pé, reflexo na base)
            tinta, _ = tinta_final(it, pasta, d)
            funcao = it.get("funcao") or ("acabamento" if it["papel"] == "constante" else None)
            estrutural = funcao == "acabamento" or it["papel"] == "constante"
            xs, ys = (xs_e, ys_e) if estrutural else (xs_c, ys_c)
            if esta_solto(tinta, xs, ys, W, H):
                avisos.append(f"{onde}: `{it['id']}` solto: nenhuma borda ou eixo da tinta ({tinta[0]:.0f}, {tinta[1]:.0f}, "
                              f"{tinta[2]:.0f}, {tinta[3]:.0f}) encosta numa linha de "
                              f"{'conteúdo, margem ou coluna' if estrutural else 'conteúdo'} (2 px), nem sangra")
            area = (tinta[2] - tinta[0]) * (tinta[3] - tinta[1])
            if area < CONFETE * W * H and funcao not in ("organizacao", "acabamento"):
                avisos.append(f"{onde}: `{it['id']}` confete: a tinta ocupa {area / (W * H):.1%} da página (abaixo de "
                              f"{CONFETE:.1%}) e a função é {funcao or 'nenhuma'}")
    if sem_alvos and paginas:
        avisos.append(f"{pre}plano sem alvos medidos em {len(sem_alvos)} página(s) (render anterior à composição): "
                      f"âncora, solto e DOM não conferidos nelas; renderize de novo")
    falhas += checar_constantes(paginas, W, H, pre)
    avisos += checar_escala(paginas, pre)
    return falhas, avisos


def planos_da_pasta(pasta, direcoes=None):
    saida = Path(pasta) / "saida"
    out = []
    for f in sorted(saida.glob("plano-elementos-*.json")):
        nome = f.stem[len("plano-elementos-"):]
        d = nome[:-len("-vertical")] if nome.endswith("-vertical") else nome
        if direcoes is None or d in direcoes:
            out.append((f, nome.replace("-vertical", " vertical")))
    return out


def _do_report(pasta, nome):
    """(png(n), textos(n)) do render-report: o PNG da página só vale se ESTE render gravou PNG (png_dir)."""
    rep_p = Path(pasta) / "saida" / "render-report.json"
    try:
        rep = json.loads(rep_p.read_text(encoding="utf-8"))
    except Exception:
        return None, None
    vertical = nome.endswith("-vertical")
    d = nome[:-len("-vertical")] if vertical else nome
    med = ((rep.get("direcoes") or {}).get(d) or {}).get("vertical" if vertical else "horizontal") or {}
    pp = med.get("por_pagina") or []
    png_dir = med.get("png_dir")
    png = (lambda n: Path(png_dir) / f"kit-{nome}-{n:02d}.png") if png_dir else None
    textos = lambda n: (pp[n - 1].get("textos") if 0 < n <= len(pp) else None)
    return png, textos


def _kit(pasta):
    try:
        return json.loads((Path(pasta) / "mediakit.json").read_text(encoding="utf-8"))
    except Exception:
        return None


def checar(pasta, direcoes=None):
    """Todos os planos da pasta (só das direções/receitas renderizadas, se `direcoes` vier). Devolve (falhas, avisos)."""
    falhas, avisos = [], []
    kit = _kit(pasta)
    for f, rot in planos_da_pasta(pasta, direcoes):
        try:
            plano = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            falhas.append(f"{f.name}: plano ilegível ({e})"); continue
        png, textos = _do_report(pasta, f.stem[len("plano-elementos-"):])
        fa, av = checar_plano(plano, pasta, rot, png, textos, kit)
        falhas += [f"elementos {x}" for x in fa]
        avisos += [f"elementos {x}" for x in av]
    return falhas, avisos


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    pasta = Path(sys.argv[1]).resolve()
    if "--plano" in sys.argv:
        f = Path(sys.argv[sys.argv.index("--plano") + 1])
        nome = f.stem.replace("plano-elementos-", "")
        png, textos = _do_report(pasta, nome)
        falhas, avisos = checar_plano(json.loads(f.read_text(encoding="utf-8")), pasta, nome, png, textos, _kit(pasta))
    else:
        falhas, avisos = checar(pasta)
    for a in avisos:
        print(f"AVISO  {a}")
    for x in falhas:
        print(f"FALHA  {x}")
    print(f"\n{len(falhas)} falha(s), {len(avisos)} aviso(s)")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()

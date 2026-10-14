#!/usr/bin/env python3
"""
encaixes.py (Frente A): onde cada elemento entra na página, resolvido sobre o layout já medido (depois do data-fit).

Contrato em references/08-sistema-elementos.md (assinatura de `resolver` congelada). O catálogo é pipeline/encaixes.json:
chave = rótulo da variante ('capa:c', 'cota:b', 'ativo:diagonal', 'prova', 'vertical:capa'...), valor = lista de
encaixes. Cada encaixe é uma REGRA (gerador), não uma coordenada:

  canto        o maior elemento que cabe no quadrante do canto, o mais perto possível do canto
  faixa        tira colada a uma borda (lado topo|base|esq|dir, espessura `esp`): pattern de borda, microtexto
  maior-vazio  o maior elemento que cabe na área livre da página, centrado nela
  sobre-cena   o maior elemento que cabe sobre a cena (foto) da página, longe do texto, num canto da foto (não no meio)
  atras-de     espiando por trás de um bloco (`seletor`): encosta no canto do bloco sem cobrir as linhas dele
  fixo         caixa `box` [x, y, w, h]: o elemento entra contido e centrado (pattern de página inteira)

`medidas_pagina` (o que o camadas.py mede no DOM depois do data-fit):
  {"w": 1920, "h": 1080, "safe": 96,
   "protegidos": [{"classe": "corpo|titulo|numero|preco|micro|logo|credito|etiqueta|fio", "x", "y", "w", "h"}],  por LINHA
   "conteudo":  [{"x", "y", "w", "h"}]   blocos de conteúdo (card, caixa, direitos, gráfico...): o resolvedor evita,
                                           o QA não cobra (a régua do QA é a linha de texto)
   "opacos":    [{"x", "y", "w", "h"}]   painéis com fundo chapado que escondem o que fica atrás (placa, bloco claro)
   "cena":      {"x", "y", "w", "h"} | None
   "blocos":    {"<seletor>": {"x", "y", "w", "h"}}   alvos dos encaixes atras-de
   "vendaveis": [{"x", "y", "w", "h", ...}]   zonas protegidas DENTRO da foto (painel "SEU LOGO AQUI" do compor.py e
                                           o foco do acervo, levados à página pelo object-fit): obstáculo como texto
   "reservados": [{"x", "y", "w", "h"}]   caixas únicas de outras constantes (busca da caixa única, camadas.py)
   "avisos":    []   o resolver ACRESCENTA aqui o que não coube (a assinatura devolve só a lista de itens)}
`dims_elementos` = {id: (w, h, alfa_bbox)} em px da imagem de origem; alfa_bbox = (x0, y0, x1, y1) da área visível
(None = a imagem inteira). Svg: (w, h, None) no tamanho natural do grafismo.

Cada item devolvido: {id, papel, encaixe, camada, x, y, w, h, rot}. (x, y, w, h) é a caixa da ÁREA VISÍVEL (o PNG de uso
já vem cortado no alfa_bbox), em px da página, antes da rotação; `rot` gira em torno do centro dessa caixa (graus, horário).
Ordem de resolução: constante, pattern, herói, apoio, estrutura, acabamento (quem vem depois desvia de quem já entrou;
acabamento com opacidade até .24 não ocupa lugar).
"""
import json, math
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CATALOGO = AQUI / "encaixes.json"
ORDEM = {"constante": 0, "pattern": 1, "heroi": 2, "apoio": 3, "estrutura": 4, "acabamento": 5}
# acabamento (mk-2.1, references/10) é resolvido por último; com opacidade até este degrau ele é véu, não ocupa lugar:
# não entra em `ocupados` (quem viesse depois não desvia dele)
OPACIDADE_QUE_NAO_OCUPA = 0.24
PASSO = 8          # resolução da grade de ocupação (px)
FOLGA = 16         # ar entre elemento e texto, marca ou bloco
FOLGA_ELEMENTO = 12
# tamanho padrão por papel quando o encaixe não diz (caixa [w, h] em px da página)
MAX_PADRAO = {"heroi": (560, 560), "apoio": (320, 320), "constante": (1600, 160), "pattern": (1920, 1920)}
MIN_PADRAO = {"heroi": (180, 180), "apoio": (96, 96), "constante": (0, 0), "pattern": (0, 0)}


def carregar_catalogo(caminho=CATALOGO):
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def normalizar_papel(papel):
    """'ornamento' é o nome antigo de herói (schema elemento.papel)."""
    return "heroi" if papel == "ornamento" else papel


# ------------------------------------------------------------------------------------------------- geometria
def caixa_girada(w, h, rot):
    """Largura e altura da caixa alinhada aos eixos que contém uma caixa w×h girada `rot` graus."""
    r = math.radians(rot or 0)
    c, s = abs(math.cos(r)), abs(math.sin(r))
    return w * c + h * s, w * s + h * c


def _inter(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def _ret(b, folga=0):
    """{x, y, w, h} -> (x0, y0, x1, y1) inflado pela folga."""
    return (b["x"] - folga, b["y"] - folga, b["x"] + b["w"] + folga, b["y"] + b["h"] + folga)


class Grade:
    """Grade de ocupação com tabela de somas (summed-area table): testa milhares de posições candidatas de uma vez."""

    def __init__(self, W, H, obstaculos):
        import numpy as np
        self.np = np
        self.W, self.H = W, H
        self.nx, self.ny = math.ceil(W / PASSO), math.ceil(H / PASSO)
        occ = np.zeros((self.ny, self.nx), dtype=np.int32)
        for (x0, y0, x1, y1) in obstaculos:
            j0, i0 = max(0, math.floor(x0 / PASSO)), max(0, math.floor(y0 / PASSO))
            j1, i1 = min(self.nx, math.ceil(x1 / PASSO)), min(self.ny, math.ceil(y1 / PASSO))
            if j1 > j0 and i1 > i0:
                occ[i0:i1, j0:j1] = 1
        self.sat = np.zeros((self.ny + 1, self.nx + 1), dtype=np.int64)
        self.sat[1:, 1:] = occ.cumsum(0).cumsum(1)

    def livres(self, A, B, regiao):
        """Posições (x, y) em px do canto superior esquerdo de uma caixa A×B (px) que cabe livre dentro de `regiao`."""
        np = self.np
        na, nb = math.ceil(A / PASSO - 1e-6), math.ceil(B / PASSO - 1e-6)
        rx0, ry0, rx1, ry1 = regiao
        j0, i0 = math.ceil(rx0 / PASSO - 1e-6), math.ceil(ry0 / PASSO - 1e-6)
        j1, i1 = math.floor(rx1 / PASSO + 1e-6) - na, math.floor(ry1 / PASSO + 1e-6) - nb
        j1, i1 = min(j1, self.nx - na), min(i1, self.ny - nb)
        if na < 1 or nb < 1 or j1 < j0 or i1 < i0:
            return np.empty((0,)), np.empty((0,))
        S = self.sat
        I = np.arange(i0, i1 + 1)[:, None]; J = np.arange(j0, j1 + 1)[None, :]
        soma = S[I + nb, J + na] - S[I, J + na] - S[I + nb, J] + S[I, J]
        ii, jj = np.nonzero(soma == 0)
        return (jj + j0) * PASSO, (ii + i0) * PASSO


# ------------------------------------------------------------------------------------------------- geradores
def _regiao_base(enc, W, H, safe):
    return (0, 0, W, H) if enc.get("sangra") else (safe, safe, W - safe, H - safe)


def _cortar(a, b):
    r = (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))
    return r if r[2] > r[0] and r[3] > r[1] else None


def _escalas(bw, bh, enc, papel, svg, limite=None, sem_encolher=False):
    """Faixa de escala (px da página por px de origem): o maior tamanho contido em `max`, o menor contido em `min`.
    `limite` = o tamanho da região quando o encaixe não declara `max` (faixa: o comprimento da borda; o teto padrão de
    1600 px deixava o microtexto 128 px aquém da margem, e isso lia como "quase alinhado"). `sem_encolher`: a constante
    de texto vivo entra no tamanho em que nasceu ou não entra (caixa única: o mesmo tamanho em toda página)."""
    mw, mh = enc.get("max") or limite or MAX_PADRAO.get(papel, (560, 560))
    nw, nh = enc.get("min") or MIN_PADRAO.get(papel, (0, 0))
    s_max = min(mw / bw, mh / bh)
    s_min = min(nw / bw, nh / bh) if (nw or nh) else 0.0
    if svg and papel == "constante":
        # texto vivo: o grafismo vem no tamanho natural (escala da página); encolhe no máximo 25%
        s_max, s_min = min(s_max, 1.0), max(s_min, 0.75)
        if sem_encolher:
            s_max, s_min = (1.0, 1.0) if s_max >= 1.0 - 1e-6 else (0.0, 1.0)
    elif not svg:
        s_max = min(s_max, 0.5)  # no máximo metade da origem: o PNG de uso sai com 2x a largura de uso (nitidez)
    return s_max, s_min


def _passos(s_max, s_min):
    s = s_max
    while s >= s_min - 1e-9 and s > 0:
        yield s
        if s <= s_min:
            break
        s = max(s_min, s * 0.94)


def _escolher(xs, ys, A, B, preferencia):
    np = __import__("numpy")
    if not len(xs):
        return None
    k = int(np.argmin(preferencia(xs, ys, A, B)))
    return float(xs[k]), float(ys[k])


def _buscar(grade, regiao, bw, bh, rot, s_max, s_min, preferencia):
    """Maior escala em que o elemento (caixa girada) cabe livre em `regiao`; devolve (s, ax, ay, A, B) ou None."""
    for s in _passos(s_max, s_min):
        w, h = bw * s, bh * s
        A, B = caixa_girada(w, h, rot)
        xs, ys = grade.livres(A, B, regiao)
        pos = _escolher(xs, ys, A, B, preferencia)
        if pos:
            return s, pos[0], pos[1], A, B
    return None


def _pref_canto(regiao, canto):
    """Distância do canto do elemento ao canto da região (soma dos dois eixos): menor = mais encostado no canto."""
    x0, y0, x1, y1 = regiao
    def f(xs, ys, A, B):
        dx = (xs - x0) if canto.endswith("esq") else (x1 - (xs + A))
        dy = (ys - y0) if canto.startswith("sup") else (y1 - (ys + B))
        return dx + dy
    return f


def _pref_centro(xs, ys, A, B):
    np = __import__("numpy")
    mx, my = xs.mean(), ys.mean()
    return np.hypot(xs - mx, ys - my)


def _pref_cantos(caixa):
    """Sobre a foto, o elemento vai para um canto dela (adesivo colado na borda), nunca para o meio, onde está o que a
    página vende: o pórtico, a escultura, o atleta. Na Sprint, centrado, o adesivo tapava a escultura na página
    'Sua marca nas asas'. Canto superior direito primeiro, depois superior esquerdo, inferior direito, inferior esquerdo."""
    np = __import__("numpy")
    x0, y0, x1, y1 = caixa
    cantos = [(x1, y0, 0.0), (x0, y0, 40.0), (x1, y1, 80.0), (x0, y1, 120.0)]
    def f(xs, ys, A, B):
        cx, cy = xs + A / 2, ys + B / 2
        return np.min([np.hypot(cx - x, cy - y) + pen for x, y, pen in cantos], axis=0)
    return f


def _item(a, enc, camada, s, ax, ay, A, B, bw, bh, rot):
    w, h = bw * s, bh * s
    cx, cy = ax + A / 2, ay + B / 2
    return {"id": a["id"], "papel": normalizar_papel(a.get("papel")), "encaixe": enc["id"], "camada": camada,
            "x": round(cx - w / 2, 1), "y": round(cy - h / 2, 1), "w": round(w, 1), "h": round(h, 1), "rot": rot or 0}


def _faixa_pattern(a, enc, camada, W, H, obst):
    """Pattern de borda: a tira inteira da borda; se esbarra em texto, afina pelo lado de dentro até `min`."""
    lado, esp = enc.get("lado", "topo"), float(enc.get("esp", 96))
    mn = enc.get("min") or (32, 32)
    minimo = float(mn[1] if lado in ("topo", "base") else mn[0]) or 32  # espessura mínima da tira
    e = esp
    while e >= minimo:
        r = {"topo": (0, 0, W, e), "base": (0, H - e, W, H), "esq": (0, 0, e, H), "dir": (W - e, 0, W, H)}[lado]
        if not any(_inter(r, o) for o in obst):
            return {"id": a["id"], "papel": "pattern", "encaixe": enc["id"], "camada": camada,
                    "x": r[0], "y": r[1], "w": r[2] - r[0], "h": r[3] - r[1], "rot": 0}
        e -= PASSO
    return None


def _faixa_regiao(enc, W, H, safe, B_ou_A=0):
    lado, esp = enc.get("lado", "base"), float(enc.get("esp", 96))
    ao_longo = (0, W) if enc.get("sangra") else (safe, W - safe)
    ao_longo_v = (0, H) if enc.get("sangra") else (safe, H - safe)
    return {"topo": (ao_longo[0], 0, ao_longo[1], esp), "base": (ao_longo[0], H - esp, ao_longo[1], H),
            "esq": (0, ao_longo_v[0], esp, ao_longo_v[1]), "dir": (W - esp, ao_longo_v[0], W, ao_longo_v[1])}[lado]


def _pref_faixa(enc, W, H, safe):
    """Na faixa: o mais perto da linha de dentro da margem (logo abaixo do conteúdo) e o mais cedo ao longo da borda."""
    lado = enc.get("lado", "base")
    np = __import__("numpy")
    def f(xs, ys, A, B):
        if lado == "base": desvio, ao = np.abs(ys - (H - safe + PASSO)), xs
        elif lado == "topo": desvio, ao = np.abs(ys + B - (safe - PASSO)), xs
        elif lado == "esq": desvio, ao = np.abs(xs + A - (safe - PASSO)), ys
        else: desvio, ao = np.abs(xs - (W - safe + PASSO)), ys
        return desvio * 4 + ao
    return f


def resolver(atribuidos: list, rotulo: str, catalogo: dict, medidas_pagina: dict, dims_elementos: dict) -> list:
    """medidas_pagina = caixas protegidas medidas no DOM (classe, x, y, w, h). dims_elementos = {id: (w, h, alfa_bbox)}.
    Devolve itens do plano_elementos (id, papel, encaixe, camada, x, y, w, h, rot).

    Cada atribuído: {"id", "papel", "encaixes_preferidos": [...], "camada": str|None}. Opcionais que o camadas.py
    acrescenta: "rot" (graus), "svg": true (grafismo: texto vivo não encolhe mais que 25%), "sem_encolher" (constante
    na busca da caixa única), "caixa" (constante com caixa única: entra nela ou sai, nunca muda de lugar) e "manual":
    {"x", "y", "w", "rot"} (ajuste manual antigo, caixa da imagem INTEIRA) ou {"pagina_inteira": true} (pattern antigo).
    Manual não desvia de nada: o QA julga. O que não couber em nenhum encaixe fica de fora e vira aviso em
    medidas_pagina["avisos"]. Atribuído com `ancora` (composição) vai ao composicao.resolver_itens, mesmo sem dimensões
    (liga e grafismo gerado na medida nascem depois da geometria)."""
    W, H = float(medidas_pagina.get("w", 1920)), float(medidas_pagina.get("h", 1080))
    safe = float(medidas_pagina.get("safe", 96))
    avisos = medidas_pagina.setdefault("avisos", [])
    encs = catalogo.get(rotulo)
    if encs is None:
        # sem catálogo, só o que vem ancorado pela composição entra (a âncora não depende do encaixes.json)
        sem_ancora = [a for a in atribuidos if not a.get("ancora") and not a.get("caixa")]
        if sem_ancora:
            avisos.append(f"{rotulo}: rótulo sem entrada no encaixes.json; {len(sem_ancora)} elemento(s) fora")
        atribuidos, encs = [a for a in atribuidos if a.get("ancora") or a.get("caixa")], []
    prot = medidas_pagina.get("protegidos") or []
    conteudo = medidas_pagina.get("conteudo") or []
    opacos = medidas_pagina.get("opacos") or []
    cena = medidas_pagina.get("cena")
    blocos = medidas_pagina.get("blocos") or {}
    vendaveis = medidas_pagina.get("vendaveis") or []
    # caixas únicas das outras constantes contam como elemento que já entrou (só na busca da caixa única)
    ocupados = [dict(r) for r in medidas_pagina.get("reservados") or []]
    out = []
    for a in sorted(atribuidos, key=lambda a: ORDEM.get(normalizar_papel(a.get("papel")), 9)):
        papel = normalizar_papel(a.get("papel"))
        if a.get("ancora"):
            # composição da página (composicao.py): posição e tamanho vêm da âncora, sem desviar de nada; o QA julga.
            # Âncora que não resolve (alvo ausente, restrição inválida, asset que não existe) vira erro de composição:
            # FALHA no qa_geometria.
            import composicao
            try:
                novos = composicao.resolver_itens(a, dims_elementos.get(a["id"]), medidas_pagina)
            except composicao.ErroComposicao as e:
                medidas_pagina.setdefault("erros_composicao", []).append(f"{rotulo}: {e}")
                continue
            for item in novos:
                out.append(item)
                if papel != "pattern" and not nao_ocupa(a):
                    ocupados.append(_aabb(item))
            continue
        dims = dims_elementos.get(a["id"])
        if dims is None:
            avisos.append(f"{rotulo}: `{a['id']}` sem dimensões (arquivo ou grafismo ausente)")
            continue
        bw0, bh0, bbox = dims
        if bbox:
            bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        else:
            bw, bh = bw0, bh0
        if a.get("caixa"):
            # constante com caixa única (por receita e formato): entra nessa caixa ou sai da página; nunca muda de lugar
            item, motivo = na_caixa(a, papel, a["caixa"], medidas_pagina, ocupados)
            if item is None:
                cx = a["caixa"]
                avisos.append(f"{rotulo}: constante `{a['id']}` fora desta página: a caixa única ({cx['x']:.0f}, {cx['y']:.0f}, "
                              f"{cx['w']:.0f}×{cx['h']:.0f}) bate em {motivo}")
                continue
            out.append(item)
            ocupados.append(_aabb(item))
            continue
        man = a.get("manual")
        if man:
            item = _manual(a, papel, man, bw0, bh0, bbox, W, H)
            out.append(item)
            if papel != "pattern":
                ocupados.append(_aabb(item))
            continue
        svg = bool(a.get("svg"))
        pref = list(a.get("encaixes_preferidos") or [])
        cands = [e for e in encs if papel in e.get("papeis", [])]
        cands.sort(key=lambda e: (pref.index(e["id"]) if e["id"] in pref else len(pref), encs.index(e)))
        item = None
        for enc in cands:
            camadas = enc.get("camadas") or ["frente"]
            camada = a.get("camada") or camadas[0]
            if camada not in camadas:
                continue
            item = _resolver_um(a, papel, enc, camada, bw, bh, svg, W, H, safe, prot, conteudo, opacos, cena, blocos, ocupados,
                                vendaveis)
            if item:
                break
        if item:
            # o que o atribuído trouxe e o encaixe não conhece (função, porquê, origem) segue para o plano gravado
            for c in ("funcao", "porque", "origem", "espelhar"):
                if a.get(c) is not None and c not in item:
                    item[c] = a[c]
        if not item:
            if cands:
                motivo = ""
                if not svg and papel in ("heroi", "apoio") and min(_escalas(bw, bh, e, papel, False)[1] for e in cands) > 0.5:
                    motivo = f"; resolução: {bw:.0f} px úteis não dão o mínimo de nenhum encaixe a 2x"
                avisos.append(f"{rotulo}: `{a['id']}` ({papel}) não coube em nenhum encaixe ({', '.join(e['id'] for e in cands)}){motivo}")
            else:
                avisos.append(f"{rotulo}: nenhum encaixe aceita papel {papel} (`{a['id']}` fica de fora)")
            continue
        out.append(item)
        if papel != "pattern":
            ocupados.append(_aabb(item))
    return out


def nao_ocupa(a):
    """Acabamento translúcido (opacidade efetiva até .24: a do `efeito` da composição, senão a do elemento) é véu: não
    entra em `ocupados`."""
    if normalizar_papel(a.get("papel")) != "acabamento":
        return False
    op = (a.get("efeito") or {}).get("opacidade", a.get("opacidade"))
    try:
        return op is not None and float(op) <= OPACIDADE_QUE_NAO_OCUPA
    except (TypeError, ValueError):
        return False


def _aabb(item):
    A, B = caixa_girada(item["w"], item["h"], item.get("rot", 0))
    cx, cy = item["x"] + item["w"] / 2, item["y"] + item["h"] / 2
    return {"x": cx - A / 2, "y": cy - B / 2, "w": A, "h": B, "id": item.get("id")}


def na_caixa(a, papel, caixa, medidas_pagina, ocupados=()):
    """(item, None) se a caixa única cabe livre nesta página; senão (None, o que ela bate). Mesmos obstáculos e folgas
    do encaixe da constante: linha de texto e marca (8 px), bloco de conteúdo (8 px), zona vendável da foto (8 px),
    elemento que já entrou (12 px) e, nas camadas de trás, painel chapado."""
    item = {"id": a["id"], "papel": papel, "encaixe": caixa.get("encaixe"), "camada": caixa.get("camada") or a.get("camada") or "frente",
            "x": caixa["x"], "y": caixa["y"], "w": caixa["w"], "h": caixa["h"], "rot": caixa.get("rot") or 0,
            "caixa_unica": caixa.get("de") or "catalogo"}
    for c in ("funcao", "porque", "origem"):
        if a.get(c) is not None:
            item[c] = a[c]
    b = _aabb(item)
    r = (b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"])
    folga = 8 if papel == "constante" else FOLGA
    obst = [(_ret(p, folga), f"{p['classe']} {p.get('texto', '')!r}") for p in medidas_pagina.get("protegidos") or []]
    obst += [(_ret(c, folga), "bloco de conteúdo") for c in medidas_pagina.get("conteudo") or []]
    obst += [(_ret(v, folga), f"zona vendável da foto {v.get('texto', '')!r}") for v in medidas_pagina.get("vendaveis") or []]
    obst += [(_ret(o, FOLGA_ELEMENTO), f"elemento `{o.get('id', '?')}`") for o in ocupados]
    if item["camada"] in ("atras", "sob-veu"):
        obst += [(_ret(o, 0), "painel chapado") for o in medidas_pagina.get("opacos") or []]
    for o, nome in obst:
        if _inter(r, o):
            return None, nome
    return item, None


def _manual(a, papel, man, W0, H0, bbox, Wp, Hp):
    """Ajuste manual antigo (x, y, w da imagem inteira, rot no centro dela) convertido para a caixa da área visível
    girando no próprio centro: o resultado na página é idêntico ao antigo, só sem o vazio transparente em volta."""
    camada = a.get("camada") or ("atras" if papel == "pattern" else "frente")
    if man.get("pagina_inteira"):
        return {"id": a["id"], "papel": papel, "encaixe": None, "camada": camada, "x": 0, "y": 0, "w": Wp, "h": Hp, "rot": 0}
    s = float(man["w"]) / W0
    x, y, rot = float(man.get("x", 0)), float(man.get("y", 0)), float(man.get("rot", 0) or 0)
    fx, fy = x + W0 * s / 2, y + H0 * s / 2            # centro da imagem inteira (onde o antigo girava)
    b = bbox or (0, 0, W0, H0)
    wc, hc = (b[2] - b[0]) * s, (b[3] - b[1]) * s
    ccx, ccy = x + b[0] * s + wc / 2, y + b[1] * s + hc / 2
    r = math.radians(rot)
    dx, dy = ccx - fx, ccy - fy
    nx, ny = fx + dx * math.cos(r) - dy * math.sin(r), fy + dx * math.sin(r) + dy * math.cos(r)
    return {"id": a["id"], "papel": papel, "encaixe": None, "camada": camada,
            "x": round(nx - wc / 2, 1), "y": round(ny - hc / 2, 1), "w": round(wc, 1), "h": round(hc, 1), "rot": rot}


def _resolver_um(a, papel, enc, camada, bw, bh, svg, W, H, safe, prot, conteudo, opacos, cena, blocos, ocupados, vendaveis=()):
    g = enc["gerador"]
    rot = float(a.get("rot") or 0)
    if papel == "pattern":
        if camada == "sob-veu" and not cena:
            return None  # pattern sob o véu só existe onde há véu: sem cena ele ficaria direto sob o texto
        if g == "fixo":
            x, y, w, h = enc.get("box") or (0, 0, W, H)
            return {"id": a["id"], "papel": "pattern", "encaixe": enc["id"], "camada": camada, "x": x, "y": y, "w": w, "h": h, "rot": 0}
        if g == "faixa":
            obst = [_ret(p, FOLGA) for p in prot if p["classe"] != "fio"] + [_ret(c, FOLGA) for c in conteudo]
            return _faixa_pattern(a, enc, camada, W, H, obst)
        return None
    # herói, apoio, constante: desviam de texto, marca, blocos e dos elementos que já entraram
    folga = 8 if papel == "constante" else FOLGA
    obst = [_ret(p, folga) for p in prot] + [_ret(o, FOLGA_ELEMENTO) for o in ocupados]
    # painel vendável e foco dentro da foto: o elemento desvia como desvia do texto (foi por falta disso que as páginas
    # de ativo da Sprint ficaram sem herói: o adesivo tapava o "SEU LOGO AQUI" e a escultura)
    obst += [_ret(v, folga) for v in vendaveis]
    alvo = None
    if g == "atras-de":
        alvo = blocos.get(enc.get("seletor", ""))
        if not alvo:
            return None
    obst += [_ret(c, folga) for c in conteudo if not (alvo and _mesma(c, alvo))]
    if camada in ("atras", "sob-veu"):
        obst += [_ret(o, 0) for o in opacos]  # atrás de painel chapado o elemento some
    grade = Grade(W, H, obst)
    limite = None
    if g == "faixa":
        r = _faixa_regiao(enc, W, H, safe)
        limite = (r[2] - r[0], r[3] - r[1])           # o comprimento inteiro da borda, entre as margens (ou sangrando)
    s_max, s_min = _escalas(bw, bh, enc, papel, svg, limite, bool(a.get("sem_encolher")))
    if s_max <= 0 or s_max < s_min:
        return None
    base = _regiao_base(enc, W, H, safe)
    if g == "canto":
        # zona do canto: o quadrante, mas no máximo 1,6x o tamanho máximo a partir do canto (selo não deriva para o
        # meio da página; se o canto está ocupado, quem resolve é o próximo encaixe, outro canto)
        canto = enc.get("canto", "sup-dir")
        mw, mh = enc.get("max") or MAX_PADRAO.get(papel, (560, 560))
        ax_, ay_ = min(0.55 * W, base[0] + 1.6 * mw) if canto.endswith("esq") else max(0.45 * W, base[2] - 1.6 * mw), \
            min(0.6 * H, base[1] + 1.6 * mh) if canto.startswith("sup") else max(0.4 * H, base[3] - 1.6 * mh)
        qx = (0, ax_) if canto.endswith("esq") else (ax_, W)
        qy = (0, ay_) if canto.startswith("sup") else (ay_, H)
        regiao = _cortar(base, (qx[0], qy[0], qx[1], qy[1]))
        pref = _pref_canto(regiao, canto) if regiao else None
    elif g == "maior-vazio":
        regiao, pref = base, _pref_centro
    elif g == "sobre-cena":
        if not cena:
            return None
        regiao = _cortar(base, _ret(cena))
        pref = _pref_cantos(regiao)        # cantos da área útil da foto (já sem a margem de segurança)
    elif g == "faixa":
        regiao, pref = _faixa_regiao(enc, W, H, safe), _pref_faixa(enc, W, H, safe)
    elif g == "atras-de":
        A0, B0 = caixa_girada(bw * s_max, bh * s_max, rot)
        r = _ret(alvo)
        regiao = _cortar(base, (r[0] - A0, r[1] - B0, r[2] + A0, r[3] + B0))
        canto = enc.get("canto", "sup-dir")
        px = r[0] if canto.endswith("esq") else r[2]
        py = r[1] if canto.startswith("sup") else r[3]
        np = __import__("numpy")
        pref = lambda xs, ys, A, B: np.hypot(xs + A / 2 - px, ys + B / 2 - py)
    elif g == "fixo":
        bx, by, bwx, bhx = enc["box"]
        s = min(s_max, bwx / bw, bhx / bh)
        if s < s_min:
            return None
        A, B = caixa_girada(bw * s, bh * s, rot)
        ax, ay = bx + (bwx - A) / 2, by + (bhx - B) / 2
        if any(_inter((ax, ay, ax + A, ay + B), o) for o in obst):
            return None
        return _item(a, enc, camada, s, ax, ay, A, B, bw, bh, rot)
    else:
        return None
    if not regiao:
        return None
    achou = _buscar(grade, regiao, bw, bh, rot, s_max, s_min, pref)
    if not achou:
        return None
    s, ax, ay, A, B = achou
    if g == "canto":
        ax, ay = _encostar(ax, ay, A, B, regiao, enc.get("canto", "sup-dir"), obst)
    return _item(a, enc, camada, s, ax, ay, A, B, bw, bh, rot)


def _encostar(ax, ay, A, B, regiao, canto, obst):
    """A grade anda de 8 em 8 px: o selo do canto ficava 2 px aquém da margem (1672 + 150 = 1822, margem em 1824) e lia
    como "quase alinhado". Se o espaço até a borda da região do canto (a margem) está livre, encosta nela, eixo a eixo."""
    x_alvo = regiao[0] if canto.endswith("esq") else regiao[2] - A
    y_alvo = regiao[1] if canto.startswith("sup") else regiao[3] - B
    if abs(x_alvo - ax) <= PASSO and not any(_inter((x_alvo, ay, x_alvo + A, ay + B), o) for o in obst):
        ax = x_alvo
    if abs(y_alvo - ay) <= PASSO and not any(_inter((ax, y_alvo, ax + A, y_alvo + B), o) for o in obst):
        ay = y_alvo
    return ax, ay


def _mesma(c, alvo):
    return abs(c["x"] - alvo["x"]) < 1 and abs(c["y"] - alvo["y"]) < 1 and abs(c["w"] - alvo["w"]) < 1 and abs(c["h"] - alvo["h"]) < 1


def seletores(catalogo):
    """Seletores dos encaixes atras-de (o camadas.py mede a caixa de cada um no DOM)."""
    return sorted({e["seletor"] for encs in catalogo.values() for e in encs if e.get("gerador") == "atras-de" and e.get("seletor")})

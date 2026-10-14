#!/usr/bin/env python3
"""
familia.py: mede se um elemento (PNG com alfa) pertence à família de estilo da receita (references/08-sistema-elementos.md).
A família é declarada em `sistema_elementos.familias[]` (meio, paleta, traco_px, luz); este arquivo MEDE o PNG e compara.

Comandos (sempre a partir de pipeline/; o Claude roda, o Ugo não):
  medir     <png> [--escala N]                          descritores em JSON (N = px de uso: lado do tile ou largura do recorte)
  pertence  <pasta-do-kit> <elemento-id> [--familia id]  veredito e medidas; sai 1 quando não pertence
  folha     <pasta-do-kit> <familia-id> <saida.png>      folha que o Ugo aprova (cada membro sobre escuro e claro, medidas)
  aprovar   <pasta-do-kit> <familia-id> --por Ugo        grava {por, em, sha256_membros} em familias[].aprovada
  calibrar  <pasta-do-kit>                               reproduz a tabela de calibração (elementos reais + controles)

DESCRITORES (descritores()):
  paleta      até 8 cores dominantes dos pixels opacos (A > 127), median cut determinístico, com peso e Lab.
  n_cores     quantas caixas de 10 unidades Lab cobrem 90% dos pixels opacos (tinta chapada = 1 ou 2; foto = dezenas).
  croma       croma médio Lab (sqrt(a² + b²)); l_desvio = desvio de L.
  cobertura   fração da imagem com A > 127.
  traco_px    espessura do traço: 2 × mediana do distanceTransform (L2) sobre o esqueleto do alfa, na resolução nativa
              (traco_px_nativo) e na escala de uso (× px de uso / largura medida). Conferido em linhas sintéticas
              antisserrilhadas de 2 a 12 px: erro de 0 a 1 px, e no penas-asa bate com área/comprimento (4,4 × 4,6 px).
  meio        medido: `meio-tom` impresso sobre papel opaco (adesivo: pontos de tinta dentro do recorte; ver abaixo),
              `foto-objeto` (tom contínuo, n_cores > 6) ou, na tinta chapada, `meio-tom` (≥ 200 manchas pequenas e
              compactas no alfa), `traco` (espessura ≤ 2% do lado do recorte) ou `chapado`.
              Meio-tom impresso: dentro da área opaca, a tinta e o papel separados por Otsu em L; fração de componentes
              pequenos (até 2% do lado) e compactos entre os componentes da tinta ou do papel (o maior dos dois), com
              conectividade 4. Calibrado em 09/10/2026: fotorreais da Sprint 0,09 a 0,24; adesivo de meio-tom real do
              GPT Image (ondas-serra-adesivo) 0,45; meio-tons sintéticos 0,98 a 1,00; traços 0. Limite 0,34 (meio do vão)
              com pelo menos 500 pontos. Amostra pequena (1 real): conferir a cada adesivo novo da família.
  luz         só em foto-objeto: razão de luminância esquerda/direita medida LINHA A LINHA (mediana de L na metade esquerda
              do segmento opaco de cada linha contra a metade direita, ponderada pelo comprimento). Linha a linha e não pela
              metade da caixa porque a caixa mistura partes diferentes do objeto (a pena na diagonal tem a ponta de um lado
              e a penugem do outro). `cima` pelo mesmo cálculo coluna a coluna.

LIMITES (calibrados em 09/10/2026 com os 6 elementos reais da Sprint; `familia.py calibrar <kit>` reproduz a tabela;
o rótulo "membro" ou "estranho" veio do olho, na folha.png da Sprint):
  ΔE2000 da paleta     média ponderada, para cada cor dominante do elemento, da menor distância CIEDE2000 (kL = 1) até
                       as cores da família. LIMITE 19. Membros: penas-asa na gravura-ouro 0,0; pena-dourada 12,2,
                       medalha-alada 12,7 e tenis-usado 15,8 na objeto-dourado. Estranhos por cor: folha-amendoeira na
                       objeto-dourado 23,1 (verde e vermelha), ondas-serra na meio-tom-mar 24,1 (o arquivo usado é o traço
                       DOURADO; a família pede azul do mar), medalha na gravura-ouro 25,6 (fita preta). Medalha recolorida
                       para azul na objeto-dourado: 33,7. O limite fica no meio do vão entre 15,8 e 23,1.
  meio compatível      tabela COMPATIVEL abaixo. Mesma cor e meio diferente (penas-asa contra objeto-dourado: ΔE 10,2;
                       pena-dourada contra gravura-ouro: ΔE 14,7) só o meio separa: n_cores 1 nos dois traços contra 23 a 96
                       nos quatro fotorreais, sem sobreposição; o corte em 6 deixa folga para tinta de 2 ou 3 tons.
  traço                só famílias de meio traco com traco_px: aceita de traco_px / 1,6 a traco_px × 1,6 (2 px: 1,25 a 3,2).
                       Medido na escala de uso: penas-asa 1,47 px (tile de 420 px), ondas-serra 1,53 px (tile de 480 px),
                       0,73 e 0,77 do que a família declara. Fator 1,6 é critério de desenho (o traço passa a ler como outra
                       caneta), não medida: com só 2 traços reais, a faixa ainda não tem calibração estatística.
  luz                  só famílias com luz declarada e só elemento foto-objeto. Zona morta: razão entre 1/1,05 e 1,05 vira
                       `indefinida` (aviso, não reprova); reprova só a direção OPOSTA fora da zona morta. Os 4 objetos reais
                       (prompt: luz suave da esquerda) medem de 1,012 a 1,041, todos com o lado esquerdo mais claro, e as
                       cópias espelhadas de 0,960 a 0,988: o sinal acerta nos 8 casos, mas a força fica dentro da zona morta.
                       Luz dura sintética (esfera): 2,75 da esquerda e 0,36 da direita. A regra pega luz claramente
                       invertida; luz suave sai como aviso.
"""
import argparse, hashlib, json, math, sys
from datetime import date
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent

LIMITE_DELTA_E = 19.0
LIMITE_N_CORES_CHAPADO = 6        # n_cores acima disto = tom contínuo (foto-objeto)
TRACO_FATOR = 1.6                 # traço aceito entre traco_px / 1,6 e traco_px × 1,6
TRACO_REL_MAX = 0.02              # espessura / lado do recorte: até 2% é traço; acima, chapado
MEIO_TOM_MIN_MANCHAS = 200
MEIO_TOM_IMPRESSO_FRAC = 0.34     # fração de pontos entre os componentes de tinta ou de papel (foto até 0,24; meio-tom 0,45+)
MEIO_TOM_IMPRESSO_MIN = 500       # e pelo menos tantos pontos
LUZ_ZONA_MORTA = 0.05             # razão de luminância entre 1/1,05 e 1,05 = indefinida
USO_PADRAO_PATTERN = 360          # px do tile quando o elemento não declara escala_tile (padrao.py folha usa 360)
USO_PADRAO_HEROI = 480            # px de largura do recorte quando o elemento não declara w

MEIO_ROTULO = {"traco": "traço", "chapado": "chapado", "meio-tom": "meio-tom", "foto-objeto": "fotorreal",
               "ilustracao": "ilustração", "adesivo": "adesivo", "textura": "textura"}
# meio declarado na família → meios medidos aceitos
COMPATIVEL = {
    "traco": {"traco"},
    "chapado": {"chapado"},
    "meio-tom": {"meio-tom"},
    "adesivo": {"chapado", "traco"},
    "foto-objeto": {"foto-objeto"},
    "ilustracao": {"foto-objeto", "chapado", "traco"},
    "textura": {"foto-objeto", "meio-tom", "chapado", "traco"},
}


# ---------------------------------------------------------------- cor
def _lab(rgb01):
    from skimage.color import rgb2lab
    return rgb2lab(np.asarray(rgb01, dtype=float).reshape(-1, 1, 3)).reshape(-1, 3)


def hex_lab(h):
    h = h.strip().lstrip("#")
    return _lab([[int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]])[0]


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(int(round(v)) for v in rgb)


def delta_e(lab_a, lab_b):
    """CIEDE2000 (kL = kC = kH = 1) entre cada cor de lab_a e cada cor de lab_b: matriz len(a) × len(b)."""
    from skimage.color import deltaE_ciede2000
    a = np.asarray(lab_a, float)[:, None, :]; b = np.asarray(lab_b, float)[None, :, :]
    a, b = np.broadcast_arrays(a, b)
    return deltaE_ciede2000(a.reshape(-1, 3), b.reshape(-1, 3)).reshape(a.shape[:2])


def delta_e_paleta(paleta, cores_familia):
    """Média ponderada (peso de cada cor no elemento) da menor ΔE2000 de cada cor dominante até a paleta da família.
    Devolve (média, [(hex, peso, ΔE)])."""
    if not paleta or not cores_familia:
        return None, []
    lab = [p["lab"] for p in paleta]; pesos = np.array([p["peso"] for p in paleta], float)
    d = delta_e(lab, [hex_lab(c) for c in cores_familia]).min(axis=1)
    media = float((d * pesos).sum() / max(pesos.sum(), 1e-9))
    return round(media, 1), [(p["hex"], p["peso"], round(float(x), 1)) for p, x in zip(paleta, d)]


# ---------------------------------------------------------------- descritores
def _rgba(fonte):
    if isinstance(fonte, Image.Image):
        return np.asarray(fonte.convert("RGBA"))
    if isinstance(fonte, np.ndarray):
        return fonte
    return np.asarray(Image.open(fonte).convert("RGBA"))


def _paleta(px):
    """Median cut do Pillow (determinístico) em até 8 cores; cores a menos de ΔE 3 se fundem."""
    img = Image.fromarray(px.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    q = img.quantize(colors=8, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    idx = np.asarray(q).ravel()
    n = int(idx.max()) + 1
    pal = np.array(q.getpalette()[: 3 * n], float).reshape(-1, 3)
    cont = np.bincount(idx, minlength=n).astype(float)
    ordem = sorted(range(n), key=lambda i: (-cont[i], tuple(pal[i])))
    cores = []
    for i in ordem:
        if cont[i] <= 0:
            continue
        lab = _lab(pal[i][None, :] / 255)[0]
        for c in cores:
            if float(delta_e([lab], [c["lab"]])[0, 0]) < 3:
                c["n"] += cont[i]; break
        else:
            cores.append({"rgb": pal[i], "lab": lab, "n": cont[i]})
    total = sum(c["n"] for c in cores)
    cores.sort(key=lambda c: (-c["n"], _hex(c["rgb"])))
    return [{"hex": _hex(c["rgb"]), "lab": [round(float(v), 2) for v in c["lab"]], "peso": round(c["n"] / total, 3)} for c in cores]


def _traco_nativo(opaco):
    import cv2
    from skimage.morphology import skeletonize
    m = opaco.astype(np.uint8)
    dt = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    esq = skeletonize(opaco)
    v = dt[esq]
    return round(2 * float(np.median(v)), 2) if v.size else 0.0


def _manchas(opaco, lado):
    """Componentes conexos pequenos e compactos (pontos de meio-tom). Devolve (n_total, n_pontos)."""
    import cv2
    n, _, est, _ = cv2.connectedComponentsWithStats(opaco.astype(np.uint8), connectivity=8)
    if n <= 1:
        return 0, 0
    a = est[1:, cv2.CC_STAT_AREA].astype(float)
    w = est[1:, cv2.CC_STAT_WIDTH].astype(float); h = est[1:, cv2.CC_STAT_HEIGHT].astype(float)
    pequeno = np.maximum(w, h) <= 0.05 * lado
    compacto = a / np.maximum(w * h, 1) >= 0.5
    return int(n - 1), int((pequeno & compacto & (a >= 4)).sum())


def _pontos_impressos(arr, opaco, lado):
    """Meio-tom impresso sobre papel opaco (o adesivo): separa tinta e papel por Otsu em L dentro da área opaca e conta
    os componentes pequenos e compactos de cada um. Devolve (fração, pontos) do lado com a maior fração."""
    import cv2
    if opaco.sum() < 100:
        return 0.0, 0
    L = cv2.cvtColor(np.ascontiguousarray(arr[..., :3]), cv2.COLOR_RGB2LAB)[..., 0]
    t, _ = cv2.threshold(L[opaco].reshape(-1, 1), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    melhor = (0.0, 0)
    for m in (opaco & (L < t), opaco & (L >= t)):
        n, _, est, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=4)
        if n <= 1:
            continue
        a = est[1:, cv2.CC_STAT_AREA].astype(float)
        w = est[1:, cv2.CC_STAT_WIDTH].astype(float); h = est[1:, cv2.CC_STAT_HEIGHT].astype(float)
        pontos = int(((np.maximum(w, h) <= 0.02 * lado) & (a >= 4) & (a / np.maximum(w * h, 1) >= 0.5)).sum())
        melhor = max(melhor, (round(pontos / (n - 1), 3), pontos))
    return melhor


def _razao_luz(L, opaco, eixo):
    """Razão de luminância entre a primeira e a segunda metade do segmento opaco, linha a linha (eixo 1: esquerda/direita)
    ou coluna a coluna (eixo 0: cima/baixo), ponderada pelo comprimento. Mediana de L em cada metade."""
    if eixo == 0:
        L, opaco = L.T, opaco.T
    num = den = 0.0
    for y in range(opaco.shape[0]):
        xs = np.nonzero(opaco[y])[0]
        if len(xs) < 20:
            continue
        meio = (xs[0] + xs[-1]) / 2
        a = L[y, xs[xs < meio]]; b = L[y, xs[xs >= meio]]
        if len(a) < 5 or len(b) < 5:
            continue
        num += float(np.median(a)) * len(xs); den += float(np.median(b)) * len(xs)
    return round(num / den, 3) if den > 0 else None


def luz_de(razao_h, razao_v):
    if razao_h is None:
        return None
    z = math.log(1 + LUZ_ZONA_MORTA)
    lh = math.log(max(razao_h, 1e-6)); lv = math.log(max(razao_v or 1.0, 1e-6))
    if lh >= z: return "esquerda"
    if lh <= -z: return "direita"
    if lv >= z: return "cima"
    return "indefinida"


def descritores(fonte, escala_uso=None):
    """Medidas de um PNG com alfa. `escala_uso` = px em que a largura do recorte (alfa_bbox) aparece na página; para
    pattern, o lado do tile (a imagem inteira). Sem ela, traco_px_uso fica None."""
    arr = _rgba(fonte)
    alfa = arr[..., 3]
    H, W = alfa.shape
    opaco = alfa > 127
    d = {"versao": 1, "dims": [int(W), int(H)], "cobertura": round(float(opaco.mean()), 3)}
    vis = np.nonzero(alfa > 8)
    if not opaco.any():
        d.update(paleta=[], n_cores=0, croma=0.0, l_desvio=0.0, traco_px_nativo=0.0, traco_px_uso=None, meio=None,
                 luz=None, razao_luz=None, razao_luz_vertical=None, alfa_bbox=None)
        return d
    y0, y1, x0, x1 = int(vis[0].min()), int(vis[0].max()), int(vis[1].min()), int(vis[1].max())
    d["alfa_bbox"] = [x0, y0, x1 - x0 + 1, y1 - y0 + 1]
    px = arr[..., :3][opaco]
    if len(px) > 300_000:
        px = px[:: len(px) // 300_000 + 1]          # amostra determinística (passo fixo)
    lab = _lab(px / 255.0)
    d["paleta"] = _paleta(px)
    caixas = np.floor(lab / 10.0).astype(int)
    _, cont = np.unique(caixas, axis=0, return_counts=True)
    cont = np.sort(cont)[::-1]
    d["n_cores"] = int(np.searchsorted(np.cumsum(cont) / cont.sum(), 0.9) + 1)
    d["croma"] = round(float(np.hypot(lab[:, 1], lab[:, 2]).mean()), 1)
    d["l_desvio"] = round(float(lab[:, 0].std()), 1)
    d["traco_px_nativo"] = _traco_nativo(opaco)
    lado = max(d["alfa_bbox"][2], d["alfa_bbox"][3])
    d["traco_rel"] = round(d["traco_px_nativo"] / max(lado, 1), 4)
    d["escala_uso"] = escala_uso
    d["traco_px_uso"] = round(d["traco_px_nativo"] * escala_uso / d["alfa_bbox"][2], 2) if escala_uso else None
    n_comp, n_pontos = _manchas(opaco, lado)
    d["componentes"] = n_comp; d["pontos"] = n_pontos
    d["frac_pontos_impressos"], d["pontos_impressos"] = _pontos_impressos(arr, opaco, lado)
    if d["frac_pontos_impressos"] >= MEIO_TOM_IMPRESSO_FRAC and d["pontos_impressos"] >= MEIO_TOM_IMPRESSO_MIN:
        d["meio"] = "meio-tom"                        # impresso sobre papel opaco: o antisserrilhado infla o n_cores
    elif d["n_cores"] > LIMITE_N_CORES_CHAPADO:
        d["meio"] = "foto-objeto"
    elif n_pontos >= MEIO_TOM_MIN_MANCHAS and n_pontos >= 0.6 * n_comp:
        d["meio"] = "meio-tom"
    elif d["traco_rel"] <= TRACO_REL_MAX:
        d["meio"] = "traco"
    else:
        d["meio"] = "chapado"
    if d["meio"] == "foto-objeto":
        from skimage.color import rgb2lab
        L = rgb2lab(arr[..., :3] / 255.0)[..., 0]
        d["razao_luz"] = _razao_luz(L, alfa > 200, 1)
        d["razao_luz_vertical"] = _razao_luz(L, alfa > 200, 0)
        d["luz"] = luz_de(d["razao_luz"], d["razao_luz_vertical"])
    else:
        d["razao_luz"] = d["razao_luz_vertical"] = None
        d["luz"] = None
    return d


def escala_de_uso(elemento, descr):
    """px em que a largura do recorte aparece na página. Pattern: o tile inteiro (escala_tile, padrão 360) convertido para
    a largura do recorte; `w` do ajuste manual vale para o PNG inteiro (render.py: <img width=w>); sem nada, 480 px."""
    W = descr["dims"][0]; bw = (descr.get("alfa_bbox") or [0, 0, W, 0])[2] or W
    if elemento.get("papel") == "pattern" or elemento.get("tipo") == "pattern":
        tile = elemento.get("escala_tile") or USO_PADRAO_PATTERN
        return tile * bw / W
    if elemento.get("w"):
        return float(elemento["w"]) * bw / W
    return float(USO_PADRAO_HEROI)


# ---------------------------------------------------------------- pertence
def pertence(elemento, familia, base=None, descr=None, escala_uso=None):
    """Veredito de um elemento contra a família declarada. elemento: item de elementos[] (usa `arquivo` relativo a `base`
    ou `descritores` já medidos); familia: item de sistema_elementos.familias[].
    Devolve {"pertence": bool, "motivos": [...], "avisos": [...], "medidas": {...}}."""
    if descr is None:
        descr = elemento.get("descritores")
    if descr is None:
        descr = descritores(Path(base or ".") / elemento["arquivo"])
    if escala_uso is None:
        escala_uso = escala_de_uso(elemento, descr)
    motivos, avisos = [], []
    m = {"meio": descr.get("meio"), "meio_familia": familia.get("meio")}
    de, por_cor = delta_e_paleta(descr.get("paleta") or [], familia.get("paleta") or [])
    m["delta_e"] = de; m["limite_delta_e"] = LIMITE_DELTA_E; m["delta_e_por_cor"] = por_cor[:4]
    if de is not None and de > LIMITE_DELTA_E:
        motivos.append(f"paleta: ΔE2000 médio {de} acima de {LIMITE_DELTA_E:g} (cores {', '.join(c for c, _, _ in por_cor[:3])}; família {', '.join(familia.get('paleta') or [])})")
    aceitos = COMPATIVEL.get(familia.get("meio"), {familia.get("meio")})
    if descr.get("meio") not in aceitos:
        motivos.append(f"meio: medido {descr.get('meio')}, a família é {familia.get('meio')}")
    if familia.get("meio") == "traco" and familia.get("traco_px") and descr.get("meio") == "traco":
        alvo = float(familia["traco_px"])
        uso = round(descr["traco_px_nativo"] * escala_uso / ((descr.get("alfa_bbox") or [0, 0, descr["dims"][0]])[2] or 1), 2)
        # a família pode declarar a própria faixa (decisão do Ugo, 09/10/2026: gravura-ouro aceita hachura de 0,75 px)
        faixa = [round(float(familia.get("traco_px_min") or alvo / TRACO_FATOR), 2), round(float(familia.get("traco_px_max") or alvo * TRACO_FATOR), 2)]
        m.update(traco_px_uso=uso, faixa_traco=faixa, escala_uso=round(escala_uso, 1))
        if not faixa[0] <= uso <= faixa[1]:
            motivos.append(f"traço: {uso} px na escala de uso, fora de {faixa[0]} a {faixa[1]} px (família pede {alvo:g} px)")
    if familia.get("luz") and descr.get("meio") == "foto-objeto":
        m.update(luz=descr.get("luz"), razao_luz=descr.get("razao_luz"), luz_familia=familia["luz"])
        oposta = {"esquerda": "direita", "direita": "esquerda"}.get(familia["luz"])
        if descr.get("luz") == "indefinida":
            avisos.append(f"luz: indefinida (razão esquerda/direita {descr.get('razao_luz')}); a família pede {familia['luz']}")
        elif descr.get("luz") != familia["luz"] and (descr.get("luz") == oposta or familia["luz"] == "cima"):
            motivos.append(f"luz: medida {descr.get('luz')} (razão esquerda/direita {descr.get('razao_luz')}), a família pede {familia['luz']}")
    return {"pertence": not motivos, "motivos": motivos, "avisos": avisos, "medidas": m}


# ---------------------------------------------------------------- membros, folha e aprovação
def sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _kit(pasta):
    pasta = Path(pasta)
    return json.loads((pasta / "mediakit.json").read_text(encoding="utf-8"))


def _familia(k, fid):
    for f in (k.get("sistema_elementos") or {}).get("familias", []):
        if f.get("id") == fid:
            return f
    raise SystemExit(f"família `{fid}` não existe em sistema_elementos.familias")


def membros(k, fid):
    """Elementos PNG declarados na família (a âncora primeiro)."""
    f = _familia(k, fid)
    els = [e for e in k.get("elementos", []) if e.get("familia") == fid and e.get("formato", "png") == "png" and e.get("arquivo")]
    return sorted(els, key=lambda e: (e.get("id") != f.get("ancora"), e.get("id")))


def hashes_membros(k, pasta, fid):
    return sorted(sha256(Path(pasta) / e["arquivo"]) for e in membros(k, fid) if (Path(pasta) / e["arquivo"]).exists())


def aprovacao_valida(k, pasta, fid):
    """(True, '') quando a família tem aprovação e os sha256 dos membros atuais são exatamente os aprovados."""
    f = _familia(k, fid)
    ap = f.get("aprovada")
    if not ap:
        return False, "sem aprovação"
    atuais = hashes_membros(k, pasta, fid)
    if sorted(ap.get("sha256_membros") or []) != atuais:
        return False, "membros mudaram depois da aprovação (sha256 diferente): a aprovação caiu"
    return True, ""


def aprovar(pasta, fid, por):
    pasta = Path(pasta); k = _kit(pasta); f = _familia(k, fid)
    f["aprovada"] = {"por": por, "em": date.today().isoformat(), "sha256_membros": hashes_membros(k, pasta, fid)}
    (pasta / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return f["aprovada"]


def _fonte(tam):
    """Inter (fontes-livres, OFL): a fonte padrão do Pillow não tem acento nem Δ."""
    inter = AQUI.parent / "fontes-livres" / "Inter" / "Inter.ttf"
    if inter.is_file():
        return ImageFont.truetype(str(inter), tam)
    try:
        return ImageFont.load_default(tam)
    except TypeError:
        return ImageFont.load_default()


def _vista(im, lado, fundo, tile=None):
    if tile:
        t = im.resize((tile, max(1, round(im.height * tile / im.width))), Image.LANCZOS)
        c = Image.new("RGBA", (lado, lado), fundo + (255,))
        for x in range(0, lado, t.width):
            for y in range(0, lado, t.height):
                c.alpha_composite(t, (x, y))
        return c.convert("RGB")
    o = im.copy(); o.thumbnail((lado - 24, lado - 24), Image.LANCZOS)
    c = Image.new("RGBA", (lado, lado), fundo + (255,))
    c.alpha_composite(o, ((lado - o.width) // 2, (lado - o.height) // 2))
    return c.convert("RGB")


def folha_familia(pasta, fid, saida, celula=380):
    """Folha de aprovação: paleta e regras da família no topo; por membro, sobre escuro e sobre claro, com as medidas e o
    veredito do pertence(). O Ugo aprova olhando esta folha; `aprovar` grava os sha256 que ela mostrou."""
    pasta = Path(pasta); k = _kit(pasta); f = _familia(k, fid)
    els = membros(k, fid)
    W = 2 * celula + 3 * 24 + 560; H = 150 + len(els) * (celula + 24) + 24
    F = Image.new("RGB", (W, H), (34, 34, 34)); d = ImageDraw.Draw(F)
    d.text((24, 20), f"família {fid}", fill=(255, 255, 255), font=_fonte(34))
    traco = f"{f['traco_px']:g} px" if f.get("traco_px") else "livre"
    regra = f"meio {MEIO_ROTULO.get(f.get('meio'), f.get('meio'))}  ·  traço {traco}  ·  luz {f.get('luz') or 'livre'}  ·  âncora {f.get('ancora') or 'nenhuma'}"
    d.text((24, 66), regra, fill=(200, 200, 200), font=_fonte(20))
    for i, c in enumerate(f.get("paleta") or []):
        h = c.lstrip("#"); rgb = tuple(int(h[j:j + 2], 16) for j in (0, 2, 4))
        d.rectangle([24 + i * 120, 100, 24 + i * 120 + 100, 130], fill=rgb); d.text((24 + i * 120, 134), c, fill=(180, 180, 180), font=_fonte(12))
    ap_ok, ap_msg = aprovacao_valida(k, pasta, fid)
    d.text((W - 520, 24), "APROVADA" if ap_ok else f"não aprovada ({ap_msg})", fill=(120, 220, 140) if ap_ok else (240, 190, 90), font=_fonte(20))
    for n, e in enumerate(els):
        y = 150 + n * (celula + 24)
        arq = pasta / e["arquivo"]
        if not arq.exists():
            d.text((24, y), f"{e['id']}: arquivo não encontrado ({e['arquivo']})", fill=(240, 120, 120), font=_fonte(20)); continue
        im = Image.open(arq).convert("RGBA")
        tile = None
        if e.get("papel") == "pattern":
            tile = max(60, int((e.get("escala_tile") or USO_PADRAO_PATTERN) * celula / 900))
        for i, fundo in enumerate(((0, 0, 0), (244, 241, 234))):
            F.paste(_vista(im, celula, fundo, tile), (24 + i * (celula + 24), y))
        r = pertence(e, f, base=pasta)
        x = 2 * celula + 72; m = r["medidas"]
        d.text((x, y + 4), e["id"] + ("  (âncora)" if e["id"] == f.get("ancora") else ""), fill=(255, 255, 255), font=_fonte(26))
        cor = (120, 220, 140) if r["pertence"] else (240, 120, 120)
        d.text((x, y + 44), "PERTENCE" if r["pertence"] else "FORA DA FAMÍLIA", fill=cor, font=_fonte(22))
        linhas = [f"ΔE2000 {m['delta_e']} (limite {LIMITE_DELTA_E:g})", f"meio medido: {MEIO_ROTULO.get(m['meio'], m['meio'])}"]
        if "traco_px_uso" in m: linhas.append(f"traço {m['traco_px_uso']} px (faixa {m['faixa_traco'][0]} a {m['faixa_traco'][1]})")
        if "luz" in m: linhas.append(f"luz {m['luz']} (razão {m['razao_luz']})")
        linhas += [f"! {t}" for t in r["motivos"] + r["avisos"]]
        linhas.append("sha256 " + sha256(arq)[:16])
        for j, t in enumerate(linhas):
            d.text((x, y + 82 + j * 26), t[:62], fill=(205, 205, 205), font=_fonte(17))
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    F.save(saida, optimize=True)
    return Path(saida)


# ---------------------------------------------------------------- calibrar
def _recolorir(arr, matiz_graus):
    """Cópia com o matiz trocado (saturação e valor mantidos, alfa intacto): o controle 'mesma forma, cor fora'."""
    hsv = np.asarray(Image.fromarray(arr[..., :3]).convert("HSV")).copy()
    hsv[..., 0] = int(round(matiz_graus / 360 * 255))
    rgb = np.asarray(Image.fromarray(hsv, "HSV").convert("RGB"))
    return np.dstack([rgb, arr[..., 3]])


def calibrar(pasta):
    pasta = Path(pasta); k = _kit(pasta)
    fams = {f["id"]: f for f in (k.get("sistema_elementos") or {}).get("familias", [])}
    print(f"{'elemento':30s} {'meio':12s} {'n_cores':>7s} {'traço nat':>9s} {'luz':>11s} {'razão':>6s}   ΔE por família (✓ pertence)")
    casos = []
    for e in k.get("elementos", []):
        arr = _rgba(pasta / e["arquivo"])
        casos.append((e["id"], e, arr))
        if e.get("papel") != "pattern":
            casos.append((e["id"] + " [espelho]", e, arr[:, ::-1].copy()))
        if e["id"] == "medalha-alada":
            casos.append((e["id"] + " [azul]", e, _recolorir(arr, 212)))
    for nome, e, arr in casos:
        ds = descritores(arr)
        vered = []
        for fid, f in fams.items():
            r = pertence(e, f, descr=ds)
            vered.append(f"{fid} {r['medidas']['delta_e']}{' ✓' if r['pertence'] else ''}")
        print(f"{nome:30s} {ds['meio'] or '-':12s} {ds['n_cores']:>7d} {ds['traco_px_nativo']:>9.2f} {str(ds['luz']):>11s} {str(ds['razao_luz']):>6s}   " + "  ".join(vered))


# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("medir"); p.add_argument("png"); p.add_argument("--escala", type=float)
    p = sub.add_parser("pertence"); p.add_argument("kit"); p.add_argument("elemento"); p.add_argument("--familia")
    p = sub.add_parser("folha"); p.add_argument("kit"); p.add_argument("familia"); p.add_argument("saida")
    p = sub.add_parser("aprovar"); p.add_argument("kit"); p.add_argument("familia"); p.add_argument("--por", required=True)
    p = sub.add_parser("calibrar"); p.add_argument("kit")
    a = ap.parse_args()
    if a.cmd == "medir":
        print(json.dumps(descritores(a.png, a.escala), ensure_ascii=False, indent=2))
    elif a.cmd == "pertence":
        k = _kit(a.kit)
        e = next((x for x in k.get("elementos", []) if x.get("id") == a.elemento), None)
        if e is None:
            sys.exit(f"elemento `{a.elemento}` não existe no mediakit.json")
        r = pertence(e, _familia(k, a.familia or e.get("familia")), base=a.kit)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.exit(0 if r["pertence"] else 1)
    elif a.cmd == "folha":
        print("OK", folha_familia(a.kit, a.familia, a.saida))
    elif a.cmd == "aprovar":
        print(json.dumps(aprovar(a.kit, a.familia, a.por), ensure_ascii=False, indent=2))
    elif a.cmd == "calibrar":
        calibrar(a.kit)


if __name__ == "__main__":
    main()

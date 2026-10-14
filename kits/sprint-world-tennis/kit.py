# Sprint Ubatuba Run 2027 para a World Tennis (cota Naming).
# Visual: Nike Shanghai Marathon 2024 (asfalto, raias brancas, painéis de cor, faixa inclinada, tríptico).
# Estrutura: proposta Itaú (capa-convite, pergunta, objetivo, frase, 4 pilares, projeções, alcance, o que leva, investimento, convite).
# Montado no VectorCraft sem tela (vch). Textos: ficha.md aprovada em 13/10/2026.
import os, sys, math, json, time, argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageEnhance

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from mediakit import kit, cenas, fotos
from mediakit.pagina import Pagina as Page, bounds as _bounds
from mediakit.vc import VC

CL = os.path.expanduser("~/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/SPRINT UBATUBA RUN/MEDIAKIT")
KIT = os.path.join(CL, "sprint-world-tennis")
AC = os.path.join(KIT, "acervo")
SP = os.path.join(CL, "sprint-2027", "acervo")
OF = os.path.join(AC, "oficial-2027")  # arquivos oficiais enviados pela Sprint em 13 e 14/10/2026: não alterar o desenho
ASSETS = os.path.join(KIT, "assets")
os.makedirs(ASSETS, exist_ok=True)

PW, PH, GAP = 1920, 1080, 2000
K, W, R, B, G = "#0A0A0B", "#F4F4F2", "#EA3339", "#354E96", "#D4A64A"
GR = "#8E8E8E"
COND = ("Helvetica Neue", "Condensed Black")
BOLD = ("Helvetica Neue", "Bold")
MED = ("Helvetica Neue", "Medium")
DIN = ("DIN Condensed", "Bold")

vc = VC()
ex = vc.ex
bounds = lambda oid: _bounds(ex, oid)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "legado"))
import lib  # só para o mapa da página 9 (lib.sp_shape), que lê kits/legado/sp.json


# ------------------------------------------------------------ insumos raster (tratamento antes do vetor)
def asfalto():
    out = os.path.join(ASSETS, "asfalto.jpg")
    if os.path.exists(out):
        return out
    rng = np.random.default_rng(7)
    w, h = 1600, 900
    base = rng.normal(22, 9, (h, w))
    grao = rng.random((h, w))
    base[grao > 0.985] += rng.normal(55, 20, (grao > 0.985).sum())
    base[grao < 0.01] -= 12
    im = Image.fromarray(np.clip(base, 0, 255).astype("uint8")).filter(ImageFilter.GaussianBlur(0.6))
    im.convert("RGB").save(out, quality=72)
    return out


def foto(src, name, w, h, mode="bw", focus=(0.5, 0.5), blur=0, escuro=1.0, raiz=SP):
    r = fotos.preparar_foto(os.path.join(raiz, src), os.path.join(ASSETS, name + ".jpg"), w, h, mode, focus, blur, escuro)
    return str(r["caminho"])


# ------------------------------------------------------------ elementos do sistema
def raia(P, x, y0=0, y1=PH, w=6):
    """Linha de raia branca com brilho, em vetor (3 camadas translúcidas, sem efeito raster)."""
    for k, op in ((26, 6), (14, 12), (6, 30)):
        P.rect(x - k / 2 + w / 2, y0, k, y1 - y0, fill=W, opacity=op)
    P.rect(x, y0, w, y1 - y0, fill=W)


def fundo(P):
    P.image(asfalto(), 0, 0, PW, PH, aceito="textura de fundo (ruído)")


def faixa(P, y, ang=-4, cor=R, tcor=K):
    """A fita inclinada da Nike: informação da prova repetida, cortada pela página."""
    ids = [P.rect(-200, y, PW + 400, 64, fill=cor)]
    x = -120
    itens = [("SPRINT 27", DIN, 46), ("▶", BOLD, 26), ("5 · 10 · 15 KM", DIN, 46), ("▶", BOLD, 26),
             ("14.03.27", DIN, 46), ("▶", BOLD, 26), ("WORLD TENNIS", COND, 40), ("▶", BOLD, 26), ("UBATUBA / SP", DIN, 46), ("////", COND, 40)]
    while x < PW + 200:
        for s, f, sz in itens:
            t = P.text(x, y + 49, s, f, sz, tcor, tracking=20)
            ids.append(t)
            x += bounds(t)["width"] + 34
            if x > PW + 200:
                break
    ex("select.set", {"ids": ids})
    g = ex("object.group")["id"]
    ex("object.rotate", {"angle": ang, "origin": [P.ox + PW / 2, y + 32]})
    ex("select.none")
    r = P.rect(0, 0, PW, PH, K)
    ex("select.set", {"ids": [g, r]})
    ex("object.arrange.bringToFront")
    ex("select.set", {"ids": [r]})
    ex("object.arrange.bringToFront")
    ex("select.set", {"ids": [g, r]})
    ex("object.clippingMask.make")
    ex("select.none")


def vertical(P, x, y, w, h, s, cor, font=COND):
    """Texto girado 90 graus (lendo de baixo para cima), encaixado na caixa x, y, w, h, como o RUN da Nike nos painéis."""
    t = P.text(0, 400, s, font, 200, cor, tracking=-10)
    ex("select.set", {"ids": [t]})
    ex("object.rotate", {"angle": 90})
    b = bounds(t)
    k = min(h / b["height"], w / b["width"]) * 100
    ex("object.scale", {"sx": k, "sy": k})
    b = bounds(t)
    ex("object.move", {"dx": P.ox + x + (w - b["width"]) / 2 - b["x"], "dy": y + (h - b["height"]) / 2 - b["y"]})
    ex("select.none")
    return t


LOGO_SPRINT = os.path.join(OF, "logo-branco.png")  # o logo de 13/10 (escolha do Ugo em 14/10), só sem o fundo branco
LOGO_R = 731 / 413


def logos(P, x, y, h=64, cor_sprint="#FFFFFF"):
    sp = LOGO_SPRINT
    wt = os.path.join(AC, "logo-world-tennis.png")
    ws = h * LOGO_R
    P.image(sp, x, y, ws, h)
    P.rect(x + ws + 22, y + h * 0.15, 2, h * 0.7, fill=W, opacity=60)
    hw = h * 0.9
    P.image(wt, x + ws + 46, y + (h - hw) / 2, hw * 1508 / 624, hw)


def tag(P, x, y, s, fg=K, bg=W):
    t = P.text(x, y, s.upper(), BOLD, 13, fg, tracking=160)
    b = bounds(t)
    r = P.rect(b["x"] - P.ox - 10, b["y"] - 7, b["width"] + 20, b["height"] + 14, fill=bg)
    ex("select.set", {"ids": [r]})
    ex("object.arrange.sendBackward")
    ex("select.none")


def head(P, x, y, s, size, cor=W, marca=None, mcor=R, font=COND, leading=None, tracking=-10, justify=None):
    t = P.text(x, y, s, font, size, cor, tracking=tracking, leading=leading or size * 0.98, justify=justify)
    if marca:
        i = s.find(marca)
        if i >= 0:
            ex("text.setStyle", {"ids": [t], "start": len(s[:i].encode()), "end": len(s[:i + len(marca)].encode()), "fill": mcor})
    return t


def cena(nome_compor, nome_gerada):
    p, rota = cenas.escolher_cena(AC, nome_compor, nome_gerada)
    return str(p), rota


# ------------------------------------------------------------ páginas
def p_capa(P):
    fundo(P)
    raia(P, 1150)
    P.rect(1300, 0, 460, 860, R)
    vertical(P, 1330, 40, 400, 790, "SPRINT 27", K)
    head(P, 96, 260, "Sprint Ubatuba Run\napresentada por\nWorld Tennis.", 106, W, "World Tennis.", R, BOLD, 104, -30)
    P.text(96, 640, "Uma proposta de naming para a World Tennis.", MED, 30, W)
    P.text(96, 682, "14 de março de 2027, Ubatuba/SP.", MED, 30, "#C4C4C4")
    logos(P, 96, 730, 110)
    faixa(P, 930, -3)


def p_pergunta(P):
    # A f4 tem 739 px de largura: esticada na página inteira ficava a 37 ppi. Painel em pé, no tamanho que ela aguenta.
    fundo(P)
    P.image(foto("tratado/f4.jpg", "f4-bw", 700, 930, "bw", (0.5, 0.45)), 1100, 150, 700, 930)
    raia(P, 1020)
    head(P, 120, 420, "O que é correr\nem Ubatuba?", 120, W, "em Ubatuba?", R, COND, 112)
    P.text(120, 640, "É largar na avenida da orla, entre a serra e o mar.\nÉ trazer a família, ficar o fim de semana\ne deixar 1 kg de alimento na retirada do kit.",
           MED, 34, W, leading=46)
    P.text(1070, 1050, "FOTO: EDIÇÃO 2026", BOLD, 12, GR, tracking=160, justify="right")
    faixa(P, 60, 0)


def p_objetivo(P):
    fundo(P)
    tag(P, 96, 150, "Objetivo", K, R)
    head(P, 96, 300, "Dar nome à\n2ª edição.", 140, W, "2ª edição.", R, COND, 130, -10)
    P.text(96, 600, "Convidar a World Tennis a dar nome à prova: ela passa a se chamar\nSprint Ubatuba Run apresentada por World Tennis,\ndo primeiro post à última medalha.",
           MED, 30, W, leading=42)
    # A medalha oficial, inteira (foto da Sprint, sem recorte): 2026 deu uma asa, 2027 dá a outra (áudio do Filipe, 14/10).
    # Painel, não círculo: o círculo cortava a base das duas metades.
    mw, mh = 640, 640 * 807 / 739
    P.image(os.path.join(OF, "medalha-par.jpeg"), 1160, 110, mw, mh)
    P.rect(1160, 110, mw, mh, fill=None, stroke=R, sw=6)
    P.text(1160 + mw, 110 + mh + 34, "MEDALHA OFICIAL: 2026 + 2027", BOLD, 12, GR, tracking=160, justify="right")
    P.text(96, 790, "A medalha de 2027 é a outra asa da medalha de 2026:\nquem correu as duas edições fecha o par.",
           BOLD, 28, G, leading=40)
    raia(P, 1000, 760, PH)
    faixa(P, 960, -3)


def p_frase(P):
    fundo(P)
    P.text(960, 150, "Mais do que um logo na camisa:", COND, 70, W, tracking=-10, justify="center")
    y0, h = 220, 640
    P.image(foto("tratado/f10-sem-selo.jpg", "f10-mov", 420, h, "warm", (0.5, 0.5), blur=40), 290, y0, 420, h)
    P.rect(750, y0, 420, h, R)
    vertical(P, 1010, y0 + 30, 140, h - 60, "LARGADA", K)
    P.text(800, y0 + 90, "1.200", DIN, 110, K)
    P.text(800, y0 + 128, "META DE\nPARTICIPANTES\n2027", BOLD, 14, K, tracking=60, leading=18)
    P.image(foto("tratado/f12-sem-marca.jpg", "f12-mov", 420, h, "warm", (0.6, 0.5), blur=40), 1210, y0, 420, h)
    P.text(960, 960, "a loja que mais entende de tênis na largada da prova.", COND, 70, W, tracking=-10, justify="center")
    P.text(960, 1030, "FOTOS: EDIÇÃO 2026", BOLD, 12, GR, tracking=160, justify="center")


def p_pilares(P):
    fundo(P)
    P.text(96, 140, "Por que a World Tennis.", COND, 80, W, tracking=-10)
    cols = [("01", "Corredor", "500 atletas inscritos em 2026.\nMeta de 1.200 em 2027."),
            ("02", "Turista", "52% do público de 2026 veio de\nfora: Litoral Norte, Vale do\nParaíba e Paraty."),
            ("03", "Experiência", "A arena na orla recebe a\nPop Up World Tennis, onde o\natleta chega com a medalha\nno peito."),
            ("04", "Propósito", "A World Tennis apoia corridas\npara democratizar o acesso à\natividade física. A Sprint\ntransforma cada inscrição em\n1 kg de alimento doado.")]
    x0, wcol = 96, 432
    for k, (n, t, d) in enumerate(cols):
        x = x0 + k * wcol
        if k:
            raia(P, x - 30, 230, 990)
        P.text(x, 470, n, DIN, 230, R)
        P.text(x, 560, t, COND, 56, W)
        P.text(x, 620, d, MED, 23, W, leading=32)
    P.text(96, 1040, "2026: INFORMADO PELO ORGANIZADOR · 2027: META · WORLD TENNIS: BLOG OFICIAL", BOLD, 12, GR, tracking=140)


def p_portico(P):
    img, rota = cena("c-portico-wt-composta.png", "c-portico-wt-gerada.png")
    P.image(foto(os.path.basename(img), "portico-final", PW, PH, "none", (0.5, 0.45), raiz=AC), 0, 0, PW, PH,
            aceito="cena gerada pela IA (o gerador entrega no máximo 1672 px)" if rota == "gerada" else None)
    P.rect(0, 800, PW, 280, K, opacity=86)
    head(P, 96, 905, "A largada é World Tennis.", 92, W, "World Tennis.", R)
    P.text(96, 960, "Testeira do pórtico de largada e chegada, embaixo do cronômetro: o momento mais fotografado da prova.", MED, 26, W)
    P.text(96, 1010, "01 · PROJEÇÃO", BOLD, 13, R, tracking=180)
    tag(P, 1640, 60, "Projeção ilustrativa", K, W)
    return rota


def p_estande(P):
    img, rota = cena("c-tendas-wt-composta.png", "c-estande-wt-gerada.png")
    P.rect(0, 0, PW, PH, K)
    fundo(P)
    P.image(foto(os.path.basename(img), "estande-final", 1240, PH, "none", (0.6, 0.5), raiz=AC), 680, 0, 1240, PH,
            aceito="cena gerada pela IA (o gerador entrega no máximo 1672 px)" if rota == "gerada" else None)
    raia(P, 676)
    P.text(96, 150, "02 · PROJEÇÃO", BOLD, 13, R, tracking=180)
    head(P, 96, 300, "A Pop Up\nWorld Tennis\nna arena.", 104, W, "World Tennis", R, COND, 98)
    P.text(96, 560, "Estande de 3 m × 3 m entre o palco e\no pórtico, onde atleta e família param\ndepois da prova.", MED, 27, W, leading=38)
    tag(P, 1640, 60, "Projeção ilustrativa", K, W)
    return rota


def camiseta_oficial():
    """A arte oficial 2027 (frente e costas), só aparada nas bordas transparentes: o desenho não muda."""
    out = os.path.join(ASSETS, "camiseta-oficial-aparada.png")
    im = Image.open(os.path.join(OF, "camiseta-frente-costas.png")).convert("RGBA")
    im.crop(im.getchannel("A").point(lambda a: 255 if a > 10 else 0).getbbox()).save(out)
    return out


def p_camisa(P):
    fundo(P)
    raia(P, 505)
    cw = 900
    img = camiseta_oficial()
    iw, ih = Image.open(img).size
    k, y0 = cw / iw, 250
    P.image(img, 40, y0, cw, ih * k)
    # Marca, sem tocar na arte, onde a World Tennis entra: a faixa de patrocinadores das costas.
    P.rect(40 + 1200 * k, y0 + 250 * k, 165 * k, 510 * k, fill=None, stroke=R, sw=4)
    tag(P, 40 + 1196 * k, y0 + 810 * k, "World Tennis aqui", W, R)
    P.text(40, y0 + ih * k + 70, "CAMISETA OFICIAL 2027 · ARTE DA ORGANIZAÇÃO", BOLD, 12, GR, tracking=160)
    rota = "arte oficial"
    P.text(960, 150, "03 · CAMISETA E PÓDIO", BOLD, 13, R, tracking=180)
    head(P, 960, 290, "Nas costas de cada camiseta.\nNo centro do pódio.", 70, W, "No centro do pódio.", R, COND, 70)
    P.text(960, 450, "A camiseta oficial 2027 vira uniforme do dia, com a World\nTennis na faixa de patrocinadores das costas. O backdrop\ndo pódio é a foto oficial da premiação.", MED, 26, W, leading=36)
    P.image(foto("tratado/f7.jpg", "f7-cor", 845, 452, "warm", (0.5, 0.42)), 960, 560, 845, 452)
    P.rect(960, 560, 845, 452, fill=None, stroke=R, sw=4)
    P.text(1820, 1050, "FOTO: PÓDIO 2026", BOLD, 12, GR, tracking=160, justify="right")
    return rota


CID = {"UBATUBA": (-45.0717, -23.4336), "CARAGUATATUBA": (-45.4131, -23.6203), "SÃO SEBASTIÃO": (-45.4097, -23.7600),
       "ILHABELA": (-45.3581, -23.7786), "SÃO JOSÉ DOS CAMPOS": (-45.8869, -23.1794), "TAUBATÉ": (-45.5550, -23.0264),
       "GUARATINGUETÁ": (-45.1925, -22.8164), "PARATY": (-44.7131, -23.2178),
       "SÃO PAULO": (-46.6333, -23.5505)}  # capital: pedido do Filipe (Sprint) em 14/10/2026


def p_alcance(P):
    fundo(P)
    lat0 = math.radians(-23.2)
    s = 500
    def f(lon, lat):
        return (580 + (lon + 45.62) * math.cos(lat0) * s, 610 - (lat + 23.3) * s)
    ring = lib.sp_shape()
    sp = P.path(P.poly_d([f(*p) for p in ring]), fill="#17171A", stroke="#3A3A40", sw=2)
    r = P.rect(0, 0, 1100, PH, K)
    ex("select.set", {"ids": [sp, r]})
    ex("object.clippingMask.make")
    ex("select.none")
    ux, uy = f(*CID["UBATUBA"])
    for c, ll in CID.items():
        if c == "UBATUBA":
            continue
        x, y = f(*ll)
        P.path(P.poly_d([(x, y), (ux, uy)], closed=False), fill=None, stroke=R, sw=3, opacity=80)
        P.ellipse(x, y, 7, 7, fill=W)
        right = x > ux or c in ("ILHABELA", "SÃO PAULO")
        P.text(x + (14 if right else -14), y + 5, c, BOLD, 14, W, tracking=60, justify="left" if right else "right")
    P.ellipse(ux, uy, 26, 26, fill=R)
    P.ellipse(ux, uy, 10, 10, fill=K)
    P.text(ux + 40, uy + 10, "UBATUBA", COND, 34, R)
    P.text(96, 140, "Impacto e alcance.", COND, 80, W, tracking=-10)
    P.text(96, 190, "PRAÇA: UBATUBA/SP, ORLA · FORMATO: 5, 10 E 15 KM E PCD", BOLD, 14, GR, tracking=120)
    raia(P, 1110, 120, PH)
    x0 = 1190
    P.text(x0, 200, "2026 · INFORMADO", BOLD, 15, GR, tracking=160)
    for k, (v, l) in enumerate([("1.300", "pessoas na arena"), ("500", "atletas"), ("187.000", "visualizações")]):
        P.text(x0 + k * 230, 300, v, DIN, 82, W)
        P.text(x0 + k * 230, 334, l, MED, 19, W)
    P.text(x0, 450, "2027 · META", BOLD, 15, R, tracking=160)
    metas = [("1.200", "participantes"), ("2.000", "pessoas na arena"), ("500.000", "visualizações"), ("72%", "de turistas")]
    for k, (v, l) in enumerate(metas):
        xx, yy = x0 + (k % 2) * 340, 560 + (k // 2) * 150
        P.text(xx, yy, v, DIN, 96, R)
        P.text(xx, yy + 36, l, MED, 19, W)
    P.text(x0, 1000, "52% do público de 2026 veio de fora da cidade.", MED, 22, W)


def p_leva(P):
    fundo(P)
    # celular com o collab
    x, y, w, h = 150, 110, 430, 870
    P.rect(x - 14, y - 14, w + 28, h + 28, fill="#1C1C20", radius=62)
    P.rect(x, y, w, h, fill=K, radius=48)
    P.image(foto("tratado/f12-sem-marca.jpg", "f12-tela", w, 560, "warm", (0.55, 0.5)), x, y + 150, w, 560)
    P.ellipse(x + 46, y + 92, 22, 22, fill=R)
    P.text(x + 82, y + 88, "sprint.total e worldtennis", BOLD, 18, W)
    P.text(x + 82, y + 110, "Collab · Reels", MED, 15, GR)
    P.text(x + 24, y + 760, "♥  ○  ▷", BOLD, 26, W)
    P.text(x + 24, y + 806, "Largada da Sprint Ubatuba Run 2027", MED, 17, W)
    P.text(x + w / 2, y + h + 70, "MOCKUP ILUSTRATIVO", BOLD, 12, GR, tracking=160, justify="center")
    head(P, 760, 220, "A World Tennis não vai\napenas estar presente.\nVai dar nome à prova.", 70, W, "Vai dar nome à prova.", R, COND, 70)
    itens = ["“Sprint Ubatuba Run apresentada por World Tennis” em todo material",
             "Testeira do pórtico de largada e chegada",
             "Backdrop do palco e do pódio (posição central)",
             "Costas da camiseta oficial, na faixa de patrocinadores",
             "Estande 3 m × 3 m na arena",
             "2 Reels collab e stories antes, durante e depois",
             "Menções na locução do evento",
             "Relatório pós-evento"]
    yy = 470
    for it in itens:
        P.rect(760, yy - 18, 18, 18, fill=R)
        P.text(800, yy, it, MED, 27, W)
        yy += 62


def p_investimento(P):
    P.rect(0, 0, PW, PH, R)
    P.text(96, 150, "INVESTIMENTO", BOLD, 18, K, tracking=220)
    P.text(96, 300, "NAMING", COND, 150, K, tracking=-10)
    P.fit(90, 715, "R$ 30.000", 1380, DIN, 400, K)
    P.text(96, 812, "1 cota disponível.", BOLD, 40, K)
    P.text(96, 862, "Exclusividade de categoria da marca até 31/03/2027.", MED, 30, K)
    faixa(P, 950, -3, K, R)


def p_convite(P):
    fundo(P)
    for x in (300, 1620):
        raia(P, x)
    head(P, 960, 420, "Vamos largar\njuntos?", 180, W, "juntos?", R, COND, 168, -10, "center")
    for k, (n, v) in enumerate([("FILIPE", "(11) 98012-0229"), ("CRISTIANE", "(12) 98122-2033"), ("E-MAIL", "contato@uuhull.com")]):
        x = 470 + k * 350
        P.text(x + 140, 720, n, BOLD, 17, R, tracking=200, justify="center")
        P.text(x + 140, 764, v, BOLD, 28, W, justify="center")
    logos(P, 960 - (110 * 1508 / 624 * 0.9 + 110 * LOGO_R + 46) / 2, 820, 110)
    faixa(P, 990, -3)


PAGES = [p_capa, p_pergunta, p_objetivo, p_frase, p_pilares, p_portico, p_estande, p_camisa, p_alcance, p_leva,
         p_investimento, p_convite]

if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--saida", default=os.path.join(KIT, "saida"))
    saida = a.parse_args().saida
    r = kit.montar("sprint-world-tennis", PAGES, os.path.join(saida, "kit-world-tennis.pdf"),
                   os.path.join(saida, "sprint-world-tennis.vectorcraft"), vc=vc)
    vc.close()
    print(r["pdf"], r["segundos"], "s", "rotas:", {k: v for k, v in r["retornos"].items() if v})
    for a in r["avisos_foto"]:
        if not a["aceito"]:
            print(f"aviso de foto: p{a['pagina']} {a['arquivo']} {a['ppi']} ppi")

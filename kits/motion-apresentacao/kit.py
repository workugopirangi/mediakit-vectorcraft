# Apresentação comercial padrão da Motion Perform (v2), mostrada ao organizador na call de venda.
# Visual: Nike Shanghai Marathon 2024 (asfalto, raias brancas, painéis de cor chapada, faixa inclinada, tríptico,
# numerais gigantes), nas cores da Motion: preto e verde #C8FF00.
# Montado no VectorCraft sem tela. Textos: ficha.md aprovada em 14/10/2026.
import os, sys, argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from mediakit import kit, cenas, fotos
from mediakit.pagina import Pagina as Page, bounds as _bounds
from mediakit.vc import VC

KIT = os.path.expanduser("~/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/COMERCIAL/AQUISIÇÃO/APRESENTAÇÃO COMERCIAL")
AC = os.path.join(KIT, "acervo")
LG = os.path.join(AC, "logos")
ASSETS = os.path.join(AC, "tratado")
os.makedirs(ASSETS, exist_ok=True)

PW, PH = 1920, 1080
K, W, V, GR, CZ = "#000000", "#FFFFFF", "#C8FF00", "#9B9D9C", "#4A4D4F"
COND = ("Helvetica Neue", "Condensed Black")
BOLD = ("Helvetica Neue", "Bold")
MED = ("Helvetica Neue", "Medium")
TOTAL = 17

vc = VC()
ex = vc.ex
bounds = lambda oid: _bounds(ex, oid)


# ------------------------------------------------------------ insumos raster
def asfalto():
    out = os.path.join(ASSETS, "asfalto.jpg")
    if os.path.exists(out):
        return out
    rng = np.random.default_rng(11)
    w, h = 1600, 900
    base = rng.normal(16, 7, (h, w))
    grao = rng.random((h, w))
    base[grao > 0.987] += rng.normal(48, 18, (grao > 0.987).sum())
    im = Image.fromarray(np.clip(base, 0, 255).astype("uint8")).filter(ImageFilter.GaussianBlur(0.6))
    im.convert("RGB").save(out, quality=72)
    return out


def cena(nome, w, h, foco=(0.5, 0.5), modo="none", escuro=1.0):
    """Só a cena gerada aprovada no olho entra (e só se o arquivo ainda é o que foi visto)."""
    p, rota = cenas.escolher_cena(AC, "", nome + ".png")
    if rota != "gerada":
        raise SystemExit(f"cena {nome} não aprovada: marque com cenas.marcar antes de montar")
    r = fotos.preparar_foto(str(p), os.path.join(ASSETS, f"{nome}-{w}x{h}-{modo}.jpg"), w, h, modo, foco, 0, escuro)
    return str(r["caminho"])


def img_cena(P, nome, x, y, w, h, foco=(0.5, 0.5), modo="none", escuro=1.0):
    if os.environ.get("RASCUNHO") and not os.path.exists(os.path.join(AC, nome + ".png")):
        # prova interna de diagramação enquanto a cena não chegou; nunca vai para o Ugo
        return P.rect(x, y, w, h, fill="#3A3A3A")
    return P.image(cena(nome, w, h, foco, modo, escuro), x, y, w, h, aceito="cena gerada pela IA (máximo 1672 px)")


# ------------------------------------------------------------ elementos do sistema
def fundo(P):
    P.image(asfalto(), 0, 0, PW, PH, aceito="textura de fundo (ruído)")


def raia(P, x, y0=0, y1=PH, w=6, cor=W):
    """Linha de raia com brilho, em vetor (camadas translúcidas, sem efeito raster)."""
    for k, op in ((26, 6), (14, 12), (6, 30)):
        P.rect(x - k / 2 + w / 2, y0, k, y1 - y0, fill=cor, opacity=op)
    P.rect(x, y0, w, y1 - y0, fill=cor)


def veu(P, x, y, w, h, lado="esq", cor=K, forte=94, fraco=0, passos=28):
    """Degradê em fatias de opacidade crescente: escurece a foto onde o texto entra."""
    for i in range(passos):
        t = i / (passos - 1)
        op = round(forte + (fraco - forte) * t)
        if op <= 0:
            continue
        if lado == "esq":
            P.rect(x + w * i / passos, y, w / passos + 1, h, fill=cor, opacity=op)
        elif lado == "dir":
            P.rect(x + w - w * (i + 1) / passos, y, w / passos + 1, h, fill=cor, opacity=op)
        elif lado == "baixo":
            P.rect(x, y + h - h * (i + 1) / passos, w, h / passos + 1, fill=cor, opacity=op)


ITENS_FAIXA = [("MOTION SPONSORSHIP", COND, 44), ("▶", BOLD, 24), ("ESTUDO", COND, 44), ("▶", BOLD, 24),
               ("ESTRATÉGIA", COND, 44), ("▶", BOLD, 24), ("FECHAMENTO", COND, 44), ("////", COND, 40)]


def faixa(P, y, ang=-3, cor=V, tcor=K, itens=ITENS_FAIXA):
    """A fita inclinada da Nike Shanghai, com o método da Motion repetido e cortado pela página."""
    ids = [P.rect(-200, y, PW + 400, 64, fill=cor)]
    x = -120
    while x < PW + 200:
        for s, f, sz in itens:
            t = P.text(x, y + 48, s, f, sz, tcor, tracking=20)
            ids.append(t)
            x += bounds(t)["width"] + 30
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
    """Texto girado 90 graus (lendo de baixo para cima), encaixado na caixa."""
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


def tag(P, x, y, s, fg=K, bg=V):
    t = P.text(x, y, s.upper(), BOLD, 15, fg, tracking=180)
    b = bounds(t)
    r = P.rect(b["x"] - P.ox - 12, b["y"] - 8, b["width"] + 24, b["height"] + 16, fill=bg)
    ex("select.set", {"ids": [r]})
    ex("object.arrange.sendBackward")
    ex("select.none")
    return t


def head(P, x, y, s, size, cor=W, marca=None, mcor=V, font=COND, leading=None, tracking=-10, justify=None):
    t = P.text(x, y, s, font, size, cor, tracking=tracking, leading=leading or size * 0.96, justify=justify)
    if marca:
        i = s.find(marca)
        if i >= 0:
            ex("text.setStyle", {"ids": [t], "start": len(s[:i].encode()), "end": len(s[:i + len(marca)].encode()), "fill": mcor})
    return t


def corpo(P, x, y, s, w, cor=W, size=26, leading=38):
    return P.text(x, y, s, MED, size, cor, leading=leading, width=w)


def logo_motion(P, x, y, h):
    P.image(os.path.join(LG, "motion-alfa.png"), x, y, h * 500 / 256, h)


def logo(P, nome, x, y, h):
    with Image.open(os.path.join(LG, nome + ".png")) as im:
        w = h * im.size[0] / im.size[1]
    P.image(os.path.join(LG, nome + ".png"), x, y, w, h, aceito="logo extraído da apresentação anterior, em tamanho pequeno")
    return w


def rodape(P, cor=GR, logo_cor=True):
    P.text(96, 1036, f"{P.i + 1:02d} / {TOTAL}", BOLD, 13, cor, tracking=160)
    if logo_cor:
        logo_motion(P, 1748, 1004, 40)


def check(P, x, y, s, w, cor=W, qcor=V, size=25):
    P.rect(x, y + size * 0.36, 16, 16, fill=qcor)
    return P.text(x + 34, y, s, MED, size, cor, leading=size * 1.4, width=w)


# ------------------------------------------------------------ páginas
def p_capa(P):
    P.rect(0, 0, PW, PH, K)
    img_cena(P, "c1-capa", 560, 0, 1360, PH, (0.6, 0.5))
    veu(P, 560, 0, 760, PH, "esq", K, 100, 0)
    logo_motion(P, 96, 80, 64)
    tag(P, 96, 290, "Motion Sponsorship Strategy")
    head(P, 96, 460, "Nunca mais\nfique sem\npatrocinador.", 170, W, "patrocinador.", V, COND, 158)
    corpo(P, 96, 790, "A gente estuda teu evento, encontra as marcas que fazem sentido, desenha as cotas e monta o caminho até o fechamento.", 760, W, 28, 40)
    faixa(P, 980, -2.5)


def p_quem(P):
    fundo(P)
    img_cena(P, "c2-beach", 1060, 0, 860, PH, (0.62, 0.5))
    raia(P, 1054)
    tag(P, 96, 170, "Quem é a Motion")
    head(P, 96, 320, "A gente transforma\nteu evento em\npropriedade\ncomercial vendável.", 104, W, "propriedade\ncomercial vendável.", V, COND, 100)
    corpo(P, 96, 760, "A Motion Perform capta patrocínio para o esporte. Montamos a estratégia para o organizador fechar patrocinador de verdade, com dado, método e material na mão. E caminhamos junto, do primeiro contato ao contrato assinado.", 880)
    x = 96
    for s in ("EVENTOS", "ASSOCIAÇÕES", "CENTROS DE TREINAMENTO", "ATLETAS"):
        t = P.text(x, 960, s, BOLD, 16, V, tracking=160)
        x += bounds(t)["width"] + 22
        if s != "ATLETAS":
            P.rect(x - 14, 950, 6, 6, fill=GR)
    rodape(P)


def p_caminhos(P):
    fundo(P)
    tag(P, 96, 150, "Antes de falar de verba")
    head(P, 96, 280, "Existem dois caminhos para uma\nmarca pôr dinheiro no teu evento.", 88, W, "dois caminhos", V, COND, 86)
    P.text(96, 410, "A maioria dos organizadores trata os dois como a mesma coisa.", MED, 28, GR)
    y0 = 470
    P.rect(960, y0, 960, PH - y0, fill=V)
    raia(P, 954, y0, PH)
    P.text(96, y0 + 300, "01", COND, 330, V, tracking=-20)
    P.text(96, y0 + 400, "Patrocínio comercial", COND, 64, W)
    corpo(P, 96, y0 + 456, "Troca de valor direta entre a marca e o evento.", 700)
    P.text(1056, y0 + 300, "02", COND, 330, K, tracking=-20)
    P.text(1056, y0 + 400, "Lei de Incentivo e Rouanet", COND, 64, K)
    corpo(P, 1056, y0 + 456, "Verba que sai do imposto que a marca já pagaria.", 760, K)


def p_comercial(P):
    fundo(P)
    img_cena(P, "c3-ativacao", 1060, 0, 860, PH, (0.6, 0.5))
    raia(P, 1054)
    tag(P, 96, 150, "Caminho 01 · Patrocínio comercial")
    head(P, 96, 300, "Patrocínio é troca,\nnão favor.", 120, W, "não favor.", V, COND, 114)
    corpo(P, 96, 500, "Do outro lado da mesa tem um gestor de marketing com meta de resultado. Ele precisa de público qualificado, exposição, ativação e dado de retorno. Se o teu evento entrega isso, a cota fecha pelo valor certo. Por isso a gente desenha cada cota como um produto para a marca, nunca como um pedido.", 860)
    # diagrama: via de mão dupla
    y, h = 790, 150
    P.rect(96, y, 330, h, fill=V)
    P.text(122, y + 56, "TEU EVENTO", COND, 44, K)
    P.text(122, y + 98, "audiência · ativação\nmídia · dado", MED, 19, K, leading=24)
    P.rect(630, y, 330, h, fill=None, stroke=W, sw=3)
    P.text(656, y + 56, "A MARCA", COND, 44, W)
    P.text(656, y + 98, "retorno · resultado\nposicionamento", MED, 19, W, leading=24)
    P.path(P.poly_d([(440, y + 46), (600, y + 46)], False), stroke=V, sw=4)
    P.path(P.poly_d([(588, y + 36), (612, y + 46), (588, y + 56)]), fill=V)
    P.path(P.poly_d([(470, y + 106), (616, y + 106)], False), stroke=W, sw=4)
    P.path(P.poly_d([(482, y + 96), (458, y + 106), (482, y + 116)]), fill=W)
    P.text(528, y + 30, "valor e exposição", BOLD, 13, V, tracking=40, justify="center")
    P.text(528, y + 136, "verba e estrutura", BOLD, 13, W, tracking=40, justify="center")
    P.text(96, y + 200, "VIA DE MÃO DUPLA: SÓ FECHA QUANDO OS DOIS LADOS GANHAM", BOLD, 14, GR, tracking=140)
    rodape(P)


def p_incentivo(P):
    P.rect(0, 0, PW, PH, V)
    tag(P, 96, 150, "Caminho 02 · Lei de Incentivo e Rouanet", V, K)
    head(P, 96, 300, "Verba que a marca\njá pagaria de imposto,\nindo para o teu evento.", 104, K, None, K, COND, 100)
    corpo(P, 96, 640, "Na Lei de Incentivo ao Esporte, a empresa direciona parte do imposto de renda que já pagaria para um projeto como o teu. Na Rouanet, o mesmo vale para a cultura. O custo real da marca cai e o teu evento recebe a verba integral.", 860, K)
    P.text(96, 900, "Se o projeto ainda entrega público e exposição:\nmarca fortalecida gastando menos.", COND, 46, K, leading=50)
    # fluxo
    x, w = 1180, 640
    P.rect(x, 170, w, 230, fill=None, stroke=K, sw=4)
    P.text(x + 40, 260, "IMPOSTO QUE A MARCA\nJÁ PAGARIA", COND, 52, K, leading=52)
    P.text(x + 40, 370, "dinheiro que iria para o governo", MED, 22, K)
    P.rect(x + w / 2 - 4, 400, 8, 150, fill=K)
    P.path(P.poly_d([(x + w / 2 - 30, 540), (x + w / 2, 590), (x + w / 2 + 30, 540)]), fill=K)
    P.rect(x, 600, w, 260, fill=K)
    P.text(x + 40, 700, "VERBA NO\nTEU EVENTO", COND, 64, V, leading=62)
    P.text(x + 40, 820, "sem custo novo para a marca", MED, 22, W)
    P.text(x, 930, "+ exposição e público para o negócio\nda marca, no mesmo movimento.", BOLD, 22, K, leading=30)
    P.text(96, 1036, f"{P.i + 1:02d} / {TOTAL}", BOLD, 13, K, tracking=160)


def p_problema(P):
    P.rect(0, 0, PW, PH, K)
    img_cena(P, "c4-backdrop", 0, 0, PW, PH, (0.55, 0.45), "none", 0.9)
    veu(P, 0, 0, 1300, PH, "esq", K, 96, 0)
    veu(P, 0, 560, PW, 520, "baixo", K, 0, 96)
    tag(P, 96, 150, "O problema")
    head(P, 96, 290, "Teu evento merece patrocínio.\nMas a captação depende de você,\ndo improviso e de relacionamento.", 86, W,
         "Mas a captação depende de você,\ndo improviso e de relacionamento.", V, COND, 86)
    itens = ["Sem dado de audiência, a cota vale menos do que o evento entrega.",
             "A abordagem depende de quem você conhece: não escala e não renova.",
             "Sem funil nem material, cada edição recomeça do zero.",
             "O patrocinador nunca viu teu evento apresentado como produto."]
    for k, s in enumerate(itens):
        x = 96 + k * 440
        P.rect(x, 740, 400, 4, fill=V)
        P.text(x, 830, f"0{k + 1}", COND, 72, V)
        corpo(P, x, 880, s, 380, W, 23, 32)
    rodape(P)


def p_solucao(P):
    fundo(P)
    tag(P, 96, 150, "A solução")
    head(P, 96, 270, "Motion Sponsorship", 120, W, "Sponsorship", V)
    y0, h, w, g = 330, 660, 560, 24
    xs = [96, 96 + w + g, 96 + 2 * (w + g)]
    # 01 estudo: foto
    img_cena(P, "c5-ciclismo", xs[0], y0, w, h, (0.5, 0.5), "bw", 0.95)
    veu(P, xs[0], y0 + 260, w, h - 260, "baixo", K, 0, 92)
    # 02 estratégia: painel verde
    P.rect(xs[1], y0, w, h, fill=V)
    vertical(P, xs[1] + w - 150, y0 + 30, 120, h - 60, "ESTRATÉGIA", K)
    # 03 fechamento: preto com raia
    P.rect(xs[2], y0, w, h, fill="#0B0B0B")
    raia(P, xs[2] + w - 40, y0, y0 + h)
    passos = [("01", "ESTUDO", "Levantamento do evento, do histórico e das marcas que fazem sentido para a tua realidade.", W, V),
              ("02", "ESTRATÉGIA", "Quem abordar, como abordar, o que oferecer e como posicionar cada cota com valor.", K, K),
              ("03", "FECHAMENTO", "Cada negociação conduzida, cada proposta revisada, cada objeção respondida, com a gente na mesa junto com você.", W, V)]
    for x, (n, t, d, c, nc) in zip(xs, passos):
        P.text(x + 36, y0 + 120, n, COND, 110, nc)
        P.text(x + 36, y0 + 470, t, COND, 60, c)
        corpo(P, x + 36, y0 + 500, d, 340 if t == "ESTRATÉGIA" else 450, c, 22, 31)
    rodape(P)


def bloco_case(P, x, w, evento, nome, hero, hero_txt, hero_logo, stats):
    logo(P, evento, x, 300, 86)
    P.text(x, 430, nome, BOLD, 16, V, tracking=180)
    t, _ = P.fit(x - 6, 600, hero, w * 0.9, COND, 200, V, tracking=-10, max_h=170)
    lx = x
    if hero_logo:
        lx += logo(P, hero_logo, x, 640, 46) + 18
    corpo(P, lx, 674, hero_txt, x + w - lx, W, 22, 30)
    sw = w / len(stats)
    for k, (v, l, lg) in enumerate(stats):
        sx = x + k * sw
        P.rect(sx, 790, sw - 24, 3, fill=CZ)
        t, _ = P.fit(sx, 880, v, sw - 44, COND, 60, W, max_h=52)
        yy = 912
        if lg:
            logo(P, lg, sx, 912, 34)
            yy = 960
        corpo(P, sx, yy, l, sw - 40, GR, 19, 26)


def p_cases1(P):
    fundo(P)
    tag(P, 96, 150, "Prova · cases reais")
    head(P, 96, 240, "O que acontece quando a estratégia existe.", 76, W, "a estratégia existe.", V)
    raia(P, 957, 290, 1010, 4, CZ)
    bloco_case(P, 96, 800, "corre-pro-match", "CORRE PRO MATCH", "R$ 700 mil",
               "em patrocínio da Viveo, via Lei de Incentivo ao Esporte", "viveo",
               [("+2M", "views no Instagram em 2 meses", None), ("+10 mil", "compartilhamentos do evento", None),
                ("+750", "inscritos na 1ª edição", None)])
    bloco_case(P, 1024, 800, "rocam", "MEIA MARATONA DA ROCAM", "R$ 185 mil",
               "em patrocínio, só nesta edição", None,
               [("3 mil", "inscritos", None), ("R$ 100 mil", "Café do Norte", "cafe-do-norte"),
                ("R$ 85 mil", "Gentil Veículos", "gentil-veiculos")])
    rodape(P)


def p_cases2(P):
    fundo(P)
    tag(P, 96, 150, "Prova · cases reais")
    head(P, 96, 240, "Mais resultados que falam por si.", 76, W, "falam por si.", V)
    raia(P, 957, 290, 1010, 4, CZ)
    bloco_case(P, 96, 800, "expofit", "BRASIL EXPOFIT", "+8 mil",
               "pessoas no evento", None,
               [("R$ 40 mil", "verba de patrocínio da Reebok", "reebok"), ("Outback", "cresceu o nome do evento", "outback"),
                ("Coco Bambu", "cresceu o nome do evento", "coco-bambu")])
    bloco_case(P, 1024, 800, "wodnation", "WODNATION", "R$ 60 mil",
               "em energético, para melhorar a experiência do atleta", "reign",
               [("R$ 25 mil", "patrocínio em roupas fitness", "xtreme-force")])
    rodape(P)


def p_estrategia(P):
    fundo(P)
    img_cena(P, "c6-funcional", 0, 0, 760, PH, (0.5, 0.45), "bw")
    raia(P, 760)
    x = 880
    tag(P, x, 150, "Entregável · Estratégia")
    head(P, x, 290, "Reestruturar 100%\na forma como você\nbusca patrocinador.", 110, W, "100%", V, COND, 106)
    corpo(P, x, 640, "A gente muda como você aborda, apresenta e vende o evento: do material que você mostra ao argumento do contato direto.", 900)
    for k, s in enumerate(["Abordagem: quem fala, quando fala, o que fala",
                           "Material profissional: deck, one-page e proposta",
                           "Argumento com dado, não impressão",
                           "Funil comercial do início ao fechamento"]):
        check(P, x, 790 + k * 58, s, 900)
    rodape(P)


PINOS = [(0.5, 0.5, "1"), (0.3, 0.4, "2"), (0.7, 0.6, "3"), (0.6, 0.3, "4")]   # ajustados à cena aprovada
LEGENDA_PINOS = ["Pórtico de largada e chegada", "Palco e backdrop", "Estandes de ativação", "Pódio"]


def p_cotas(P):
    fundo(P)
    x0, w = 900, 1020
    img_cena(P, "c7-aerea", x0, 0, w, PH, (0.5, 0.5))
    raia(P, x0 - 6)
    for fx, fy, n in PINOS:
        cx, cy = x0 + fx * w, fy * PH
        P.ellipse(cx, cy, 34, 34, fill=V)
        P.ellipse(cx, cy, 46, 46, fill=None, stroke=V, sw=3)
        P.text(cx, cy + 15, n, COND, 42, K, justify="center")
    tag(P, 96, 150, "Entregável · Cotas")
    head(P, 96, 290, "Cotas e posição\nde cada marca,\ndesenhadas do zero.", 92, W, "do zero.", V, COND, 90)
    corpo(P, 96, 620, "Nada de tabela pronta: desenhamos junto com você, da posição física de cada marca no evento à presença digital.", 740)
    for k, s in enumerate(["Arquitetura de cotas: hierarquia, valores, exclusividade e escassez",
                           "Posição de cada marca: ativos, ativações e contrapartidas",
                           "Instagram, YouTube e transmissão ao vivo, se houver",
                           "Inventário comercial completo"]):
        check(P, 96, 780 + k * 62, s, 720, size=23)
    yy = 1036
    xx = x0 + 40
    for k, s in enumerate(LEGENDA_PINOS):
        t = P.text(xx, yy, f"{k + 1}  {s.upper()}", BOLD, 13, W, tracking=120)
        xx += bounds(t)["width"] + 36
    P.text(96, 1036, f"{P.i + 1:02d} / {TOTAL}", BOLD, 13, GR, tracking=160)


def p_match(P):
    fundo(P)
    tag(P, 96, 150, "Entregável · Match")
    head(P, 96, 290, "A gente sabe quais\nempresas têm chance\nreal de fechar com\nteu evento.", 100, W, "chance\nreal de fechar", V, COND, 96)
    corpo(P, 96, 720, "Cruzamos o teu evento com a nossa base de marcas: quem investe em patrocínio, em que categoria, com que público. Disso sai a probabilidade de fechamento de cada empresa com fit. Você entra na frente de quem pode dizer sim, com o argumento certo.", 780)
    cx = 1420
    camadas = [(150, 860, 640, "#1A1A1A", W, "Marcas que investem em\npatrocínio esportivo"),
               (360, 640, 440, "#2E2F30", W, "Com fit com o teu\nevento e o teu público"),
               (570, 440, 240, V, K, "Com probabilidade\nreal de fechar")]
    for y, wt, wb, cor, tc, s in camadas:
        h = 190
        P.path(P.poly_d([(cx - wt / 2, y), (cx + wt / 2, y), (cx + wb / 2, y + h), (cx - wb / 2, y + h)]), fill=cor)
        P.text(cx, y + 92, s, COND, 38 if cor != V else 36, tc, leading=40, justify="center")
    P.rect(cx - 3, 780, 6, 90, fill=V)
    P.path(P.poly_d([(cx - 22, 862), (cx, 900), (cx + 22, 862)]), fill=V)
    P.text(cx, 960, "A LISTA QUE A ANÁLISE DE MATCH ENTREGA", BOLD, 18, V, tracking=160, justify="center")
    rodape(P)


def p_acompanhamento(P):
    P.rect(0, 0, PW, PH, K)
    img_cena(P, "c8-bastidor", 0, 0, PW, PH, (0.6, 0.5))
    veu(P, 0, 0, 1250, PH, "esq", K, 96, 0)
    tag(P, 96, 150, "Acompanhamento")
    head(P, 96, 300, "Do lado de você\naté o dia do evento.", 120, W, "até o dia do evento.", V, COND, 114)
    corpo(P, 96, 500, "Reuniões regulares para tratar tudo sobre o evento: aplicação da estratégia, respostas dos patrocinadores, negociações e ajustes.", 820)
    for k, s in enumerate(["Reuniões de alinhamento com pauta definida",
                           "Análise de respostas e negociações",
                           "Revisão de propostas e objeções, sem limite",
                           "Pós-evento: relatório de prova para renovar e vender a próxima edição"]):
        check(P, 96, 700 + k * 62, s, 820)
    rodape(P)


def p_parceria(P):
    fundo(P)
    tag(P, 96, 150, "A parceria completa")
    head(P, 96, 260, "Tudo isso, para o teu evento, num só lugar.", 84, W, "num só lugar.", V)
    itens = ["Reestruturação da captação", "Análise de match", "Funil assertivo, com etapas e argumento",
             "Desenho de cotas e posicionamento", "Presença digital: Instagram e YouTube",
             "Sales kit: deck, one-page e proposta", "Plano de ação: waves, calendário e KPIs",
             "Relatórios de prova", "Acompanhamento até o evento", "Relatório pós-evento para renovar"]
    for k, s in enumerate(itens):
        col, lin = k // 5, k % 5
        x, y = 96 + col * 880, 340 + lin * 134
        P.rect(x, y, 820, 2, fill=CZ)
        P.text(x, y + 88, f"{k + 1:02d}", COND, 64, V)
        P.fit(x + 120, y + 80, s, 690, COND, 44, W, max_h=40)
    raia(P, 950, 340, 1010, 4, CZ)
    rodape(P)


def p_valor(P):
    P.rect(0, 0, PW, PH, V)
    tag(P, 96, 150, "O valor do que a gente entrega", V, K)
    head(P, 96, 330, "Cada peça, contratada\nseparada, custa caro.", 140, K, None, K, COND, 132)
    t = head(P, 96, 610, "Juntas e mastigadas,\nvalem muito mais.", 140, K, None, K, COND, 132)
    b = bounds(t)
    r = P.rect(b["x"] - P.ox - 24, b["y"] - 16, b["width"] + 48, b["height"] + 36, fill=K)
    ex("select.set", {"ids": [r]})
    ex("object.arrange.sendBackward")
    ex("select.none")
    ex("text.setStyle", {"ids": [t], "fill": V})
    corpo(P, 96, 800, "Quem monta isso sozinho contrata um fornecedor para cada pedaço, coordena tudo na mão e ainda corre o risco de não fechar nada. Aqui, um time só conduz do início ao sim, com método e dado em cada etapa.", 1500, K, 28, 40)
    faixa(P, 960, -2.5, K, V)


PLANOS = [("MÍNIMO", None, "35%", "R$ 2.897", "R$ 1.897"),
          ("PRO", "RECOMENDADO", "30%", "R$ 3.397", "R$ 2.397"),
          ("COMPLETO", "CORTE PARA PERFORMANCE", "20%", "R$ 3.897", "R$ 2.897")]


def p_planos(P):
    fundo(P)
    tag(P, 96, 130, "Os planos da parceria")
    head(P, 96, 230, "Escolha como começar.", 90, W, "como começar.", V)
    w, g = 552, 36
    for k, (nome, sub, pct, de, por) in enumerate(PLANOS):
        x = 96 + k * (w + g)
        pro = k == 1
        y0, y1 = (270, 990) if pro else (300, 990)
        bg, fg, ac = (V, K, K) if pro else ("#0E0E0E", W, V)
        P.rect(x, y0, w, y1 - y0, fill=bg, stroke=None if pro else CZ, sw=None if pro else 2)
        P.text(x + 40, y0 + 92, nome, COND, 72, fg)
        if sub:
            P.text(x + 40, y0 + 132, sub, BOLD, 14, ac if not pro else K, tracking=160)
        yy = y0 + 200
        for s in ("Sponsorship Strategy: estudo, cotas, matching, playbook e sales kit", "Análise de match por marca",
                  "Relatórios de audiência, engajamento, marcas e resultados"):
            check(P, x + 40, yy, s, w - 110, fg, K if pro else V, 21)
            yy += 74
        P.rect(x + 40, y0 + 420, w - 80, 2, fill=K if pro else CZ)
        P.text(x + 40, y0 + 530, pct, COND, 110, ac)
        corpo(P, x + 230, y0 + 474, "de participação sobre os patrocínios captados, a partir do 2º mês", w - 270, fg, 18, 24)
        t = P.text(x + 40, y1 - 110, "de " + de, MED, 26, fg if pro else GR)
        b = bounds(t)
        P.rect(b["x"] - P.ox - 2, b["y"] + b["height"] * 0.55, b["width"] + 4, 2.5, fill=fg if pro else GR)
        P.text(x + 40, y1 - 36, "por " + por, COND, 76, ac)
    P.text(96, 1040, "FECHANDO NESTA CALL. Valores válidos só até o fim desta call. PIX ou cartão em até 10x sem juros.", BOLD, 15, GR, tracking=60)
    logo_motion(P, 1748, 1004, 40)


def p_proximo(P):
    P.rect(0, 0, PW, PH, K)
    img_cena(P, "c9-chegada", 0, 0, PW, PH, (0.5, 0.45), "none", 0.85)
    veu(P, 0, 0, PW, 1080, "baixo", K, 0, 70)
    P.rect(0, 0, PW, PH, fill=K, opacity=35)
    logo_motion(P, 960 - 117, 140, 120)
    tag(P, 870, 380, "Próximo passo")
    head(P, 960, 520, "Bora fazer teu evento ter\na estrutura que ele merece?", 120, W, "a estrutura que ele merece?", V, COND, 116, -10, "center")
    faixa(P, 960, -2.5)


PAGES = [p_capa, p_quem, p_caminhos, p_comercial, p_incentivo, p_problema, p_solucao, p_cases1, p_cases2,
         p_estrategia, p_cotas, p_match, p_acompanhamento, p_parceria, p_valor, p_planos, p_proximo]
assert len(PAGES) == TOTAL

if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--saida", default=os.path.join(KIT, "saida"))
    a.add_argument("--so", help="números das páginas separados por vírgula, para prova rápida")
    args = a.parse_args()
    pags = PAGES if not args.so else [PAGES[int(n) - 1] for n in args.so.split(",")]
    r = kit.montar("motion-apresentacao", pags, os.path.join(args.saida, "apresentacao-motion.pdf"),
                   os.path.join(args.saida, "apresentacao-motion.vectorcraft"), vc=vc)
    vc.close()
    print(r["pdf"], r["segundos"], "s")
    for a in r["avisos_foto"]:
        if not a["aceito"]:
            print(f"aviso de foto: p{a['pagina']} {a['arquivo']} {a['ppi']} ppi")

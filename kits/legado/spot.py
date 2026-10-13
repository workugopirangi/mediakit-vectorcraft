# Sprint Ubatuba Run 2027 na linguagem Spotify × Garmin "Run The Beat".
# Pôster de cor chapada + o pulso (o raio da Spotify vira a linha de ritmo da corrida),
# título com a palavra-chave na cor do pulso, foto em duas cores.
import sys, os, math, time
from PIL import Image, ImageOps
import lib
from lib import Page, bounds, PW, PH, GAP
from vc import ex, close_all_discard

lib.ACERVO = "/Users/ugopirangi/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/SPRINT UBATUBA RUN/MEDIAKIT/sprint-2027/acervo"
ASSETS = os.path.join(lib.HERE, "assets-sprint")
os.makedirs(ASSETS, exist_ok=True)

BLACK, GOLD, CREAM = "#0B0B0C", "#D4A64A", "#F3E3B5"
SEA, MINT, CORAL, WHITE = "#0F3550", "#9FE3D0", "#E9603A", "#FFFFFF"

# par = (fundo, pulso/destaque, texto)
PAR = {
    "preto": (BLACK, GOLD, CREAM),
    "ouro": (GOLD, BLACK, BLACK),
    "mar": (SEA, MINT, CREAM),
    "coral": (CORAL, CREAM, WHITE),
    "creme": (CREAM, SEA, BLACK),
    "menta": (MINT, SEA, SEA),
}

H1 = ("Avenir Next", "Bold")
H2 = ("Avenir Next", "Demi Bold")
TXT = ("Avenir Next", "Medium")
NUM = ("Avenir Next", "Heavy")


def b8(s, i):
    return len(s[:i].encode("utf-8"))


def head(P, x, y, s, size, fg, hi=None, marks=(), tracking=-25, leading=None, font=H1, justify=None):
    oid = P.text(x, y, s, font, size, fg, tracking=tracking, leading=leading or size * 1.02, justify=justify)
    for m in marks:
        i = s.find(m)
        if i >= 0:
            ex("text.setStyle", {"ids": [oid], "start": b8(s, i), "end": b8(s, i + len(m)), "fill": hi})
    return oid


def pulse_pts(x0, y0, w, h, kind=0, mirror=False):
    """O pulso: borda serrilhada que sobe da esquerda para a direita, como o raio da Spotify."""
    shapes = [
        [(0, .70), (.30, .46), (.235, .66), (.63, .24), (.555, .50), (1, .34), (1, 1), (0, 1)],
        [(0, .62), (.20, .50), (.15, .68), (.50, .30), (.43, .55), (.80, .18), (.74, .44), (1, .40), (1, 1), (0, 1)],
        [(0, .78), (.42, .40), (.34, .64), (.78, .20), (.70, .48), (1, .44), (1, 1), (0, 1)],
    ]
    pts = shapes[kind % len(shapes)]
    out = []
    for px, py in pts:
        if mirror:
            px = 1 - px
        out.append((x0 + px * w, y0 + py * h))
    return out


def pulse(P, color, x0=0, y0=0, w=PW, h=PH, kind=0, mirror=False):
    return P.path(P.poly_d(pulse_pts(x0, y0, w, h, kind, mirror)), fill=color)


def duo(src, name, w, h, dark, light, focus=(0.5, 0.5)):
    out = os.path.join(ASSETS, name + ".jpg")
    im = Image.open(os.path.join(lib.ACERVO, src)).convert("RGB")
    ar = w / h
    iw, ih = im.size
    cw, ch = (ih * ar, ih) if iw / ih > ar else (iw, iw / ar)
    cx = min(max(focus[0] * iw, cw / 2), iw - cw / 2)
    cy = min(max(focus[1] * ih, ch / 2), ih - ch / 2)
    im = im.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2)))
    sc = min(1.0, max(w, h) * 1.25 / max(im.size))
    im = im.resize((int(im.size[0] * sc), int(im.size[1] * sc)), Image.LANCZOS)
    g = ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1)
    ImageOps.colorize(g, dark, light).save(out, quality=88)
    return out


def tinted(src, name, color):
    out = os.path.join(ASSETS, name + ".png")
    im = Image.open(os.path.join(lib.ACERVO, src)).convert("RGBA")
    a = im.split()[3]
    solid = Image.new("RGBA", im.size, color)
    solid.putalpha(a)
    solid.save(out)
    return out


def lockup(P, x, y, color, h=74):
    """Assinatura do rodapé, como o 'Spotify | GARMIN': logo da prova | data e lugar."""
    logo = tinted("logo.png", "logo-" + color.strip("#"), color)
    w = h * 843 / 490
    P.image(logo, x, y - h * 0.8, w, h)
    P.rect(x + w + 26, y - h * 0.55, 2, h * 0.62, fill=color)
    P.text(x + w + 52, y - h * 0.32, "14.03.2027", H1, 26, color, tracking=20)
    P.text(x + w + 52, y - h * 0.32 + 30, "UBATUBA/SP · 2ª EDIÇÃO", H2, 15, color, tracking=120)


def tag(P, x, y, s, fg, bg):
    t = P.text(x, y, s.upper(), H2, 13, fg, tracking=160)
    b = bounds(t)
    r = P.rect(b["x"] - P.ox - 10, b["y"] - 7, b["width"] + 20, b["height"] + 14, fill=bg)
    ex("select.set", {"ids": [r]})
    ex("object.arrange.sendBackward")
    ex("select.none")


# ---------------------------------------------------------------- páginas

def s_capa(P):
    bg, hi, fg = PAR["preto"]
    P.rect(0, 0, PW, PH, bg)
    pulse(P, hi, 0, 560, PW, 520, kind=0)
    head(P, 96, 210, "Ubatuba muda\nde ritmo em março.\nSua marca corre junto.", 118, fg, hi, ["corre junto."])
    P.text(96, 600, "Sprint Ubatuba Run, 14 de março de 2027.", H2, 34, fg, tracking=-10)
    P.text(96, 644, "Mídia kit de patrocínio da 2ª edição.", TXT, 34, fg, tracking=-10)
    lockup(P, 96, 1015, bg)


def s_manifesto(P):
    bg, hi, fg = PAR["mar"]
    P.rect(0, 0, PW, PH, bg)
    P.image(duo("tratado/f4.jpg", "manifesto", 760, PH, SEA, CREAM, (0.5, 0.45)), 1160, 0, 760, PH)
    pulse(P, hi, 0, 300, 1500, 780, kind=1)
    head(P, 96, 200, "Correr também\né transformar.\nCada atleta,\numa doação.", 104, fg, hi, ["uma doação."])
    P.text(96, 900, "A Sprint Ubatuba Run traz a corrida para dentro da cidade:\nquem vem correr traz a família, fica o fim de semana\ne deixa 1 kg de alimento na retirada do kit.",
           TXT, 25, bg, leading=33)
    P.text(1830, 1050, "FOTO: EDIÇÃO 2026", H2, 12, CREAM, tracking=160, justify="right")


def s_projecao(P):
    bg, hi, fg = PAR["ouro"]
    P.image(duo("tratado/c-arena.jpg", "arena", PW, PH, BLACK, GOLD, (0.5, 0.5)), 0, 0, PW, PH)
    pulse(P, BLACK, 0, 380, 1250, 700, kind=2)
    head(P, 96, 880, "A orla vira arena.", 96, CREAM, GOLD, ["arena."])
    P.text(96, 940, "Pórtico, palco, tendas e escultura na avenida da praia, em 14 de março.", TXT, 25, CREAM)
    lockup(P, 96, 1040, GOLD, h=56)
    tag(P, 1530, 70, "Projeção ilustrativa da arena 2027", BLACK, GOLD)


def s_publico(P):
    bg, hi, fg = PAR["ouro"]
    P.rect(0, 0, PW, PH, bg)
    P.image(duo("tratado/f5.jpg", "publico", 620, 760, BLACK, CREAM, (0.5, 0.5)), 1204, 96, 620, 760)
    pulse(P, BLACK, 0, 660, PW, 420, kind=0, mirror=True)
    head(P, 96, 200, "1.300 pessoas\nna arena.", 112, fg)
    rows = [("500", "atletas inscritos"), ("52%", "do público era turista"), ("53% · 47%", "mulheres · homens")]
    y = 430
    for big, small in rows:
        P.text(96, y, big, NUM, 64, fg, tracking=-20)
        t = P.text(96, y + 34, small, H2, 22, fg)
        y += 100
    P.text(96, 730, "INFORMADO PELO ORGANIZADOR · 2026", H2, 14, BLACK, tracking=160)
    lockup(P, 96, 1015, GOLD)


def s_historico(P):
    bg, hi, fg = PAR["creme"]
    P.rect(0, 0, PW, PH, bg)
    pulse(P, hi, 0, 380, 1200, 700, kind=1)
    head(P, 96, 200, "21 empresas\njá correram\ncom a gente.", 112, fg, hi, ["com a gente."])
    P.text(96, 590, "Patrocinadores e apoiadores da 1ª edição, em 2026.", TXT, 26, fg)
    P.rect(1250, 96, 574, 630, fill=WHITE, radius=24)
    P.image(os.path.join(lib.ACERVO, "patrocinadores-2026.png"), 1290, 126, 494, 542)
    P.text(1250, 770, "BACKDROP DA EDIÇÃO 2026", H2, 13, fg, tracking=160)
    lockup(P, 96, 1015, bg)


CID = {"UBATUBA": (-45.0717, -23.4336), "CARAGUATATUBA": (-45.4131, -23.6203),
       "SÃO SEBASTIÃO": (-45.4097, -23.7600), "ILHABELA": (-45.3581, -23.7786),
       "SÃO JOSÉ DOS CAMPOS": (-45.8869, -23.1794), "TAUBATÉ": (-45.5550, -23.0264),
       "GUARATINGUETÁ": (-45.1925, -22.8164), "PARATY": (-44.7131, -23.2178)}


def s_territorio(P):
    bg, hi, fg = PAR["mar"]
    P.rect(0, 0, PW, PH, bg)
    lat0 = math.radians(-23.2)
    s = 720
    def f(lon, lat):
        return (1470 + (lon + 45.25) * math.cos(lat0) * s, 540 - (lat + 23.25) * s)
    ring = lib.sp_shape()
    sp = P.path(P.poly_d([f(*p) for p in ring]), fill="#163F5E", stroke="#2B5878", sw=2)
    r = P.rect(0, 0, PW, PH, BLACK)
    ex("select.set", {"ids": [sp, r]})
    ex("object.clippingMask.make")
    ex("select.none")
    ux, uy = f(*CID["UBATUBA"])
    for c, ll in CID.items():
        if c == "UBATUBA":
            continue
        x, y = f(*ll)
        P.path(P.poly_d([(x, y), (ux, uy)], closed=False), fill=None, stroke=hi, sw=3, opacity=70)
        P.ellipse(x, y, 9, 9, fill=hi)
        right = x > ux or c in ("ILHABELA",)
        P.text(x + (16 if right else -16), y + 6, c, H2, 17, fg, tracking=40, justify="left" if right else "right")
    P.ellipse(ux, uy, 34, 34, fill=hi)
    P.ellipse(ux, uy, 14, 14, fill=bg)
    P.text(ux + 50, uy + 10, "UBATUBA", H1, 34, hi, tracking=-10)
    pulse(P, hi, 0, 640, 900, 440, kind=2)
    head(P, 96, 200, "Ubatuba atrai\na região.", 112, fg, hi, ["a região."])
    P.text(96, 480, "Mais da metade do público de 2026 veio de\nfora da cidade: corredores do Litoral Norte,\ndo Vale do Paraíba e de Paraty, que viajam\ncom família e amigos para correr na orla.",
           TXT, 26, fg, leading=35)
    lockup(P, 96, 1015, bg)


def bar(P, x, base, w, hgt, color):
    P.rect(x, base - hgt, w, hgt, fill=color)


def s_metas(P):
    bg, hi, fg = PAR["preto"]
    P.rect(0, 0, PW, PH, bg)
    pulse(P, hi, 0, 660, PW, 420, kind=1)
    head(P, 96, 200, "A meta de 2027:\nmais que o dobro.", 112, fg, hi, ["mais que o dobro."])
    stats = [("1.200", "participantes"), ("72%", "de turistas"), ("2.000", "pessoas na arena"), ("500.000", "visualizações digitais")]
    for k, (big, small) in enumerate(stats):
        x = 96 + k * 300
        P.text(x, 470, big, NUM, 62, hi, tracking=-20)
        P.text(x, 506, small, H2, 20, fg)
    P.text(96, 560, "META DO ORGANIZADOR · 2ª EDIÇÃO", H2, 13, fg, tracking=160)
    # duas comparações em barras, à direita
    for k, (lab, a, b, mx, la, lb) in enumerate([("Atletas", 500, 1200, 1200, "500", "1.200"),
                                                 ("Visualizações", 187000, 500000, 500000, "187.000", "500.000")]):
        x = 1360 + k * 260
        base = 560
        hmax = 380
        P.text(x, 120, lab.upper(), H2, 14, fg, tracking=140)
        bar(P, x, base, 80, hmax * a / mx, "#3A3A3E")
        bar(P, x + 100, base, 80, hmax * b / mx, hi)
        P.text(x + 40, base - hmax * a / mx - 14, la, H1, 20, fg, justify="center")
        P.text(x + 140, base - hmax * b / mx - 14, lb, H1, 20, hi, justify="center")
        P.text(x + 40, base + 30, "2026", H2, 15, fg, justify="center")
        P.text(x + 140, base + 30, "META", H2, 15, fg, justify="center")
    P.text(96, 620, "2026: números informados pelo organizador. 2027: metas.", TXT, 22, fg)
    lockup(P, 96, 1015, bg)


def s_divisor(P):
    bg, hi, fg = PAR["coral"]
    P.rect(0, 0, PW, PH, bg)
    pulse(P, hi, 0, 200, PW, 880, kind=2)
    head(P, 96, 200, "Onde a marca\nencontra o atleta.", 112, fg, hi, ["o atleta."])
    P.text(96, 480, "Seis pontos de contato, da retirada do kit ao pódio.", TXT, 30, fg)
    items = ["Pórtico", "Arena", "Asas", "Pódio", "Doação", "Kit"]
    for k, it in enumerate(items):
        x = 1000 + (k % 3) * 290
        y = 760 + (k // 3) * 120
        P.text(x, y, f"{k + 1:02d}", NUM, 22, bg, tracking=40)
        P.text(x, y + 44, it, H1, 44, bg, tracking=-20)
    lockup(P, 96, 1015, bg)


def ativo(P, par, n, titulo, marca, corpo, aplic, foto, focus, rotulo=None):
    bg, hi, fg = PAR[par]
    P.rect(0, 0, PW, PH, bg)
    dark = bg if par in ("preto", "mar", "coral") else BLACK
    P.image(duo(foto, f"ativo{n}", 1000, PH, dark, CREAM if par != "creme" else WHITE, focus), 920, 0, 1000, PH)
    pulse(P, hi, 0, 720, 1180, 360, kind=n % 3)
    P.text(96, 170, f"{n:02d}", NUM, 96, hi, tracking=-20)
    head(P, 96, 330, titulo, 92, fg, hi, [marca])
    P.text(96, 470, corpo, TXT, 24, fg, leading=33)
    P.text(96, 660, "APLICAÇÕES", H2, 13, hi, tracking=180)
    P.text(96, 700, aplic, H1, 28, fg, tracking=-10)
    lockup(P, 96, 1030, bg, h=56)
    if rotulo:
        tag(P, 1640, 70, rotulo, bg, hi)
    else:
        P.text(1830, 1050, "FOTO: EDIÇÃO 2026", H2, 12, CREAM, tracking=160, justify="right")


def s_portico(P):
    ativo(P, "preto", 1, "Sua marca\nno pórtico.", "no pórtico.",
          "O pórtico fica na avenida da orla, colado à arena:\né por onde passam todos os atletas na largada e na\nchegada, embaixo do cronômetro, no momento mais\nfotografado da prova.",
          "Testeira · Colunas · Grades · Bandeiras", "tratado/c-portico.jpg", (0.5, 0.5), "Projeção ilustrativa")


def s_arena(P):
    ativo(P, "mar", 2, "Sua marca\nna arena.", "na arena.",
          "Seis tendas de patrocinador ladeiam a arena entre\no palco e o pórtico. É onde o atleta e a família param\ndepois da prova: massagem, hidratação, comida e\nexperimentação de produto.",
          "Tendas · Testeiras · Ativação", "tratado/c-tendas.jpg", (0.4, 0.5), "Projeção ilustrativa")


def s_asas(P):
    ativo(P, "ouro", 3, "Sua marca\nnas asas.", "nas asas.",
          "A escultura das asas é o photo point da arena.\nCada atleta para ali com a medalha no peito, e a\nfoto sai da arena para o Instagram de quem correu,\nlevando a base da escultura junto.",
          "Base · Totem · Moldura", "tratado/c-asas.jpg", (0.5, 0.5), "Projeção ilustrativa")


def s_podio(P):
    ativo(P, "coral", 4, "Sua marca\nno pódio.", "no pódio.",
          "No pódio sobem os cinco primeiros de cada\ndistância, com o backdrop atrás. É a foto oficial\nda premiação, publicada pela organização e pelas\nassessorias de corrida da região.",
          "Backdrop · Palco · Troféus", "tratado/f7.jpg", (0.5, 0.45))


def s_doacao(P):
    ativo(P, "creme", 5, "Sua marca\nna doação.", "na doação.",
          "Na retirada do kit, cada atleta entrega 1 kg de\nalimento não perecível, distribuído a pessoas em\nsituação de vulnerabilidade de Ubatuba. A marca que\nassina o ponto de arrecadação assina a doação.",
          "Ponto de coleta · Caixas · Relatório", "tratado/c-doacao.jpg", (0.5, 0.5), "Projeção ilustrativa")


def s_kit(P):
    ativo(P, "menta", 6, "Sua marca\nno kit.", "no kit.",
          "A camisa dourada vira uniforme do dia: está em todas\nas fotos da arena e volta para os treinos da região.\nManga e costas são posições de patrocinador, e a\nsacola leva amostra e cupom.",
          "Manga · Costas · Sacola", "tratado/f1.jpg", (0.5, 0.4))


def s_cotas(P):
    bg, hi, fg = PAR["ouro"]
    P.rect(0, 0, PW, PH, bg)
    pulse(P, BLACK, 0, 330, PW, 750, kind=0)
    head(P, 96, 200, "Quatro cotas.\nUma prova inteira.", 112, fg)
    P.text(96, 440, "A Sprint Ubatuba Run oferece quatro cotas para marcas que querem\nnome na prova, presença na arena e contato com o turista que\nchega a Ubatuba em março.", TXT, 26, fg, leading=35)
    for k, (n, v) in enumerate([("NAMING", "R$ 30.000"), ("MASTER", "R$ 12.000"), ("OFICIAL", "R$ 5.000"), ("APOIO", "R$ 1.500")]):
        x = 1000 + (k % 2) * 400
        y = 760 + (k // 2) * 120
        P.text(x, y, n, H2, 16, GOLD, tracking=180)
        P.text(x, y + 50, v, NUM, 48, CREAM, tracking=-20)
    lockup(P, 96, 1015, GOLD)


def cota(P, par, nome, preco, qtd, territorio, frase, itens, excl=None):
    bg, hi, fg = PAR[par]
    P.rect(0, 0, PW, PH, bg)
    pulse(P, hi, 0, 700, 980, 380, kind=1)
    P.text(96, 140, "COTA", H2, 18, fg, tracking=220)
    P.fit(90, 330, nome, 820, NUM, 200, hi, tracking=-30, max_h=230)
    P.text(96, 430, preco, H1, 64, fg, tracking=-20)
    P.text(96, 476, qtd.upper(), H2, 15, fg, tracking=160)
    P.text(96, 540, territorio.upper(), H2, 15, hi, tracking=160)
    head(P, 96, 600, frase, 36, fg, tracking=-15, leading=44, font=H2)
    P.text(1040, 140, "DIREITOS E CONTRAPARTIDAS", H2, 15, fg, tracking=200)
    y = 210
    for it in itens:
        P.rect(1040, y - 16, 14, 14, fill=hi)
        P.text(1076, y, it, TXT, 26, fg, leading=34)
        y += 56 + 34 * it.count("\n")
    if excl:
        P.text(1076, y + 10, excl, H1, 26, hi)
    lockup(P, 96, 1015, bg)


def s_naming(P):
    cota(P, "preto", "Naming", "R$ 30.000", "1 cota disponível", "O nome do evento e o pórtico",
         "Seu nome na prova: Sprint Ubatuba Run\napresentada pela sua marca.",
         ["\"Sprint Ubatuba Run apresentada por\" em todo material", "Testeira do pórtico de largada e chegada",
          "Backdrop do palco e do pódio (posição central)", "Manga da camisa oficial", "Estande 3 m × 3 m na arena",
          "2 Reels collab e stories antes, durante e depois", "Menções na locução do evento", "Relatório pós-evento"],
         "Exclusividade de categoria até 31/03/2027")


def s_master(P):
    cota(P, "mar", "Master", "R$ 12.000", "2 cotas disponíveis", "Uma distância com o nome da sua marca",
         "Dê nome aos 10 km ou aos 14 km e esteja\nnas costas de cada camisa.",
         ["Naming da distância: \"10 km [marca]\" ou \"14 km [marca]\"", "Costas da camisa oficial (posição superior)",
          "Coluna do pórtico de largada e chegada", "Tenda própria na arena", "1 Reels collab e stories",
          "Menções na locução", "Relatório pós-evento"])


def s_oficial(P):
    cota(P, "coral", "Oficial", "R$ 5.000", "4 cotas disponíveis", "Uma tenda da arena",
         "Uma tenda da arena é sua: o atleta\nexperimenta a marca ao vivo.",
         ["Testeira da tenda: Recovery, Hidratação,\nAlimentação ou Arrecadação", "Ativação ou sampling na tenda",
          "1 item na sacola do kit", "Logo no backdrop do pódio", "Stories durante o evento", "Relatório pós-evento"])


def s_apoio(P):
    cota(P, "creme", "Apoio", "R$ 1.500", "12 cotas disponíveis", "Backdrop e kit",
         "Presença no backdrop, no site e na\nsacola de cada atleta.",
         ["Logo no backdrop de medalhas", "Logo no site oficial", "Material na sacola do kit",
          "Menção coletiva nas redes", "1 Reels coletivo pós-evento com menção"])


def s_contato(P):
    bg, hi, fg = PAR["preto"]
    P.rect(0, 0, PW, PH, bg)
    P.image(duo("tratado/f12.jpg", "contato", 620, 760, BLACK, GOLD, (0.5, 0.4)), 1204, 96, 620, 760)
    pulse(P, hi, 0, 760, PW, 320, kind=2, mirror=True)
    head(P, 96, 200, "Em 14 de março,\nsua marca\ncorre junto.", 112, fg, hi, ["corre junto."])
    for k, (lab, val) in enumerate([("FILIPE", "(11) 98012-0229"), ("CRISTIANE", "(12) 98122-2033"), ("E-MAIL", "contato@uuhull.com")]):
        y = 600 + k * 74
        P.text(96, y, lab, H2, 14, hi, tracking=200)
        P.text(300, y + 4, val, H1, 34, fg, tracking=-10)
    lockup(P, 96, 1015, bg)
    P.text(1830, 1050, "FOTO: EDIÇÃO 2026", H2, 12, CREAM, tracking=160, justify="right")


PAGES = [s_capa, s_manifesto, s_projecao, s_publico, s_historico, s_territorio, s_metas, s_divisor,
         s_portico, s_arena, s_asas, s_podio, s_doacao, s_kit, s_cotas, s_naming, s_master, s_oficial,
         s_apoio, s_contato]

if __name__ == "__main__":
    only = [int(a) for a in sys.argv[1:]] or list(range(len(PAGES)))
    close_all_discard()
    ex("file.new", {"name": "sprint-spotify", "width": PW, "height": PH, "units": "Pixels"})
    t0 = time.time()
    for n, i in enumerate(only):
        P = Page(n)
        PAGES[i](P)
        print("pagina", i + 1, "ok", round(time.time() - t0, 1), "s", flush=True)
    for n in range(len(only)):
        ex("select.allOnArtboard", {"artboard": n})
        ex("object.scale", {"sx": 75, "sy": 75, "origin": [n * GAP, 0], "strokes": True, "corners": True})
        ex("select.none")
        ex("artboard.setProps", {"index": n, "width": 1440, "height": 810})
    out = os.path.join(lib.HERE, "out2")
    os.makedirs(out, exist_ok=True)
    print(ex("document.exportPdf", {"path": os.path.join(out, "kit.pdf"), "preserveEditing": False}))
    print(ex("file.saveAs", {"path": os.path.join(out, "sprint-spotify.vectorcraft")}))

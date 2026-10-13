# Páginas 4 a 18. Executado dentro do build.py (mesmo escopo).


def clip_to_page(P, ids):
    """Recorta o que passa da página (o que vaza invadiria a página vizinha no PDF)."""
    r = P.rect(0, 0, PW, PH, K)
    ex("select.set", {"ids": list(ids) + [r]})
    g = ex("object.clippingMask.make")
    ex("select.none")
    return g


def dots_d(P, pts):
    return " ".join(f"M{P.ox + x - r:.1f},{y:.1f} a{r:.1f},{r:.1f} 0 1,0 {2 * r:.1f},0 "
                    f"a{r:.1f},{r:.1f} 0 1,0 {-2 * r:.1f},0 Z" for x, y, r in pts if r > 0.4)


def catmull(pts, n=24):
    out = []
    P0 = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P0) - 2):
        p0, p1, p2, p3 = P0[i - 1], P0[i], P0[i + 1], P0[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1])
    return out


def bullets(P, x, y, items, color=W, star=Y, size=20, step=36, width=820):
    for s in items:
        P.star(x + 7, y - 7, 6.5, star)
        P.text(x + 28, y, s, BODY, size, color)
        y += step
    return y


def p_quemjoga(P):
    # Nike 07: foto em cima, faixa de cor embaixo com o título, adesivo cruzando a divisa.
    P.rect(0, 0, PW, PH, Y)
    P.image(prep(T + "real-equipe-sub.jpg", "equipe", PW, 660, "warm", (0.5, 0.42)), 0, 0, PW, 660)
    P.text(1700, 640, "FOTO: ACERVO A.M.E", HEAD, 12, W, tracking=160)
    P.text(64, 780, "QUEM JÁ JOGA\nCOM A GENTE.", HEAD, 104, K, tracking=-30, leading=96)
    # adesivo: anel com as cinco estrelas do escudo
    P.ellipse(1010, 660, 210, 82, fill=None, stroke=W, sw=10)
    for k in range(5):
        P.star(1010 + (k - 2) * 62, 662, 22, W)
    P.text(1240, 760, "Laboratório Tajara, DSport, Óticas Diniz, Colégio Maple Bear, Profi, VAR Esporte "
           "e Farmácia Princesa estão no backdrop da Copa AME de 2026.", HEAD, 30, K, width=616,
           leading=36, tracking=-10)
    P.strip(1030, K)


def p_alcance(P):
    # Nike 12: lista empilhada e centrada, número grande com legenda sobrescrita, mapa ao fundo.
    P.rect(0, 0, PW, PH, K)
    ring = sp_shape()
    f = projector((260, 90, 1400, 900), ring)
    sp = P.path(P.poly_d([f(*p) for p in ring[::2]]), fill=None, stroke=G, sw=3)
    P.strip(70, Y)
    P.text(960, 230, "ALCANCE DIGITAL · OUTUBRO DE 2026", HEAD, 15, Y, tracking=220, justify="center")
    rows = [("204.800", "VISUALIZAÇÕES\nEM 30 DIAS"), ("20.200", "SEGUIDORES\nNO INSTAGRAM"),
            ("5.180", "INSCRITOS\nNA TV AME"), ("21", "ANOS DE\nCAMPEONATO")]
    y = 370
    for big, sup in rows:
        t = P.text(930, y, big, HEAD, 138, Y, tracking=-30, justify="center")
        b = bounds(t)
        P.text(b["x"] - P.ox + b["width"] + 14, b["y"] + 30, sup, HEAD, 17, Y, tracking=40, leading=19)
        y += 150
    P.mark(880, 850, 160, Y)
    P.text(960, 1000, "INSTAGRAM @AMECRIANCA: PAINEL PROFISSIONAL, 23/AGO A 21/SET/2026 · TV AME: PÁGINA DO CANAL, "
           "OUT/2026 · ANOS: INFORMADO PELO ORGANIZADOR", HEAD, 12, "#8A8A8A", tracking=80, justify="center")
    P.strip(1040, Y)


def p_territorio(P):
    # Nike 11: o percurso. Aqui o percurso é a copa: quatro cidades ligadas por uma linha.
    P.rect(0, 0, PW, PH, K)
    lat0 = math.radians(-21.5)
    cx_lon, cy_lat = -49.47, -21.57
    s = 520
    def f(lon, lat):
        return (1100 + (lon - cx_lon) * math.cos(lat0) * s, 630 - (lat - cy_lat) * s)
    ring = sp_shape()
    out = P.path(P.poly_d([f(*p) for p in ring]), fill="#141416", stroke=G, sw=3)
    clip_to_page(P, [out])
    P.path(dots_d(P, [(x, y, 1.8) for x in range(12, PW, 24) for y in range(12, PH, 24)]), fill="#1E1E21")
    order = ["ARAÇATUBA", "SÃO JOSÉ DO RIO PRETO", "TAQUARITINGA", "BAURU"]
    pts = [f(*CIDADES[c]) for c in order]
    curve = catmull(pts)
    P.path(P.poly_d(curve, closed=False), fill=None, stroke=Y, sw=9)
    info = {"ARAÇATUBA": ("CIDADE-SEDE", -1), "SÃO JOSÉ DO RIO PRETO": ("SEDE", 1),
            "TAQUARITINGA": ("CIDADE-SEDE", 1), "BAURU": ("CIDADE-SEDE", 1)}
    for c, (x, y) in zip(order, pts):
        big = c == "SÃO JOSÉ DO RIO PRETO"
        P.ellipse(x, y, 22 if big else 16, 22 if big else 16, fill=K, stroke=Y, sw=7)
        if big:
            P.star(x, y, 11, Y)
        sup, side = info[c]
        if big:
            P.text(x, y - 62, c, HEAD, 24, Y, tracking=10, justify="center")
            P.text(x, y - 40, sup, HEAD, 12, W, tracking=160, justify="center")
            continue
        tx = x + 34 if side > 0 else x - 34
        P.text(tx, y - 4, c, HEAD, 24, Y, tracking=10, justify="left" if side > 0 else "right")
        P.text(tx, y + 18, sup, HEAD, 12, W, tracking=160, justify="left" if side > 0 else "right")
    P.strip(70, Y)
    P.text(64, 210, "QUATRO CIDADES,\nUMA COPA.", HEAD, 84, Y, tracking=-30, leading=80)
    P.text(64, 1000, "CATEGORIAS\nSUB-06 AO SUB-20", HEAD, 13, Y, tracking=120, leading=17)
    P.text(380, 1000, "QUANDO\nNOITES DA SEMANA E SÁBADOS DE MANHÃ", HEAD, 13, Y, tracking=120, leading=17)
    P.text(1856, 1000, "ONDE\nINTERIOR DE SÃO PAULO", HEAD, 13, Y, tracking=120, leading=17, justify="right")
    P.mark(64, 830, 200, Y)


def p_pontos(P):
    # Nike 13: grade de pontos e o gesto feito de meio-tom. O gesto é a trajetória da bola.
    P.rect(0, 0, PW, PH, K)
    step = 24
    grid = [(x, y, 2.2) for x in range(12, PW, step) for y in range(12, PH, step)]
    P.path(dots_d(P, grid), fill="#1C1C1F")
    # curva da bola: da esquerda baixa até a direita alta, pontos crescem até a bola
    p0, p1, p2 = (620, 860), (1150, 900), (1660, 300)
    def q(t):
        return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
    samples = [q(k / 400) for k in range(401)]
    ball = (1700, 250, 92)
    hal = []
    for x in range(12, PW, step):
        for y in range(12, PH, step):
            dmin, tb = 1e9, 0
            for k in range(0, 401, 4):
                sx, sy = samples[k]
                d = (sx - x) ** 2 + (sy - y) ** 2
                if d < dmin:
                    dmin, tb = d, k / 400
            dmin = math.sqrt(dmin)
            half = 14 + 70 * math.sin(math.pi * min(tb, 0.98) ** 0.75)
            r = 0
            if dmin < half:
                r = (1 - dmin / half) ** 0.6 * (2.5 + 7.5 * tb)
            db = math.hypot(x - ball[0], y - ball[1])
            if db < ball[2]:
                r = max(r, 10.5 * (1 - (db / ball[2]) ** 4) ** 0.5)
            if r > 0.6:
                hal.append((x, y, min(r, 11)))
    P.path(dots_d(P, hal), fill=Y)
    P.fit(64, 620, "10", 380, DISPLAY, 600, Y, tracking=-20)
    P.text(64, 720, "PONTOS ONDE\nA FAMÍLIA INTEIRA\nVÊ A SUA MARCA.", HEAD, 56, W, tracking=-25, leading=56)
    P.text(64, 930, "Do nome da copa à beira do campo, os lugares onde a marca entra em campo com a A.M.E.",
           BODY, 20, "#BDBDBD", width=520, leading=27)
    P.strip(1040, Y)


def p_nome(P):
    # Nike 14: título no topo, silhueta gigante, assinatura embaixo. A silhueta é o estado de SP.
    P.rect(0, 0, PW, PH, K)
    ring = sp_shape()
    f = projector((900, 150, 960, 780), ring)
    P.path(P.poly_d([f(*p) for p in ring]), fill=Y)
    x, y = f(*CIDADES["SÃO JOSÉ DO RIO PRETO"])
    P.star(x, y, 22, K)
    P.text(x, y + 46, "SÃO JOSÉ DO RIO PRETO · SEDE", HEAD, 14, K, tracking=120, justify="center")
    P.text(64, 110, "01", HEAD, 28, Y)
    P.fit(64, 300, "SUA MARCA NO", 820, DISPLAY, 200, Y, tracking=-5)
    P.fit(64, 480, "NOME DA COPA.", 820, DISPLAY, 200, Y, tracking=-5)
    P.text(64, 560, "O patrocinador master dá nome à competição, como já fizeram a Copa AME Lab. Tajara "
           "e a Copa AME Colégio Maple Bear. O nome aparece na tabela de cada rodada, no app, nas "
           "transmissões e nos posts de resultado, o semestre inteiro.", BODY, 22, W, width=760, leading=31)
    P.rect(64, 760, 468, 226, fill=None, stroke=Y, sw=2)
    P.image(prep("pdf/app-tabela-rodada.jpg", "tabela", 440, 207, "none"), 78, 770, 440, 207)
    P.text(560, 790, "A TABELA DA RODADA\nJÁ LEVA O NOME DO\nPATROCINADOR.", HEAD, 14, Y, tracking=120, leading=19)
    P.text(560, 980, "FOTO: APP DA A.M.E", HEAD, 11, "#8A8A8A", tracking=160)
    P.strip(1040, Y)


def p_arbitragem(P):
    # Nike 15: foto de um lado, painel de cor do outro, selo circular cruzando a divisa.
    P.rect(0, 0, PW, PH, Y)
    P.image(prep(T + "real-arbitragem-entrada.jpg", "arbitragem", 1080, PH, "warm", (0.5, 0.5)), 0, 0, 1080, PH)
    P.text(64, 1040, "FOTO: ACERVO A.M.E", HEAD, 12, W, tracking=160)
    X = 1160
    P.text(X, 110, "02", HEAD, 28, K)
    P.fit(X, 310, "SUA MARCA NA", 700, DISPLAY, 200, K, tracking=-5)
    P.fit(X, 500, "ARBITRAGEM.", 700, DISPLAY, 200, K, tracking=-5)
    P.text(X, 590, "Árbitros e organização estão em todos os jogos do semestre e em toda foto oficial de "
           "equipe antes do apito. Em 2026, a camisa levou a Farmácia Princesa para cada partida.",
           BODY, 22, K, width=680, leading=31)
    P.text(X, 790, "APLICAÇÕES", HEAD, 12, K, tracking=200)
    P.text(X, 830, "PEITO · MANGA\nORGANIZAÇÃO · MASCOTE", HEAD, 26, K, tracking=-5, leading=32)
    P.strip(1040, K, x0=X, x1=1856, n=1)
    # selo
    cx, cy, r = 1730, 870, 100
    P.ellipse(cx, cy, r + 34, r + 34, fill=Y)
    P.ellipse(cx, cy, r + 30, r + 30, fill=None, stroke=K, sw=3)
    P.ellipse(cx, cy, r - 30, r - 30, fill=None, stroke=K, sw=3)
    c = ex("shape.ellipse", {"x": P.ox + cx - r + 6, "y": cy - r + 6, "width": 2 * (r - 6), "height": 2 * (r - 6)})["id"]
    t = ex("text.createInPath", {"path": c, "mode": "onPath", "at": [P.ox + cx - r, cy],
                                 "text": "ARBITRAGEM OFICIAL · COPA AME 2027 · ARBITRAGEM OFICIAL · COPA AME 2027 · ",
                                 "size": 13.8, "font": HEAD[0], "style": HEAD[1], "color": K})["id"]
    ex("text.setStyle", {"ids": [t], "tracking": 40})
    P.star(cx, cy, 44, K)


def p_beira(P):
    # Nike 16: a foto manda, a faixa corre por cima.
    P.image(prep(T + "c-beira-composta.jpg", "beira", PW, PH, "warm", (0.5, 0.5)), 0, 0, PW, PH)
    P.rect(0, 0, PW, 150, K, opacity=70)
    P.strip(90, Y)
    P.rect(0, 740, 1180, 340, K, opacity=84)
    P.text(64, 800, "03 · PLACAS · FAIXAS · WIND BANNER · BACKDROP", HEAD, 15, Y, tracking=160)
    P.fit(64, 930, "SUA MARCA NA BEIRA DO CAMPO.", 1060, DISPLAY, 200, Y, tracking=-5)
    P.text(64, 980, "Aos sábados, placas, faixas e wind banners ficam na linha do campo, onde pais e mães "
           "assistem de pé ao lado dos filhos. É o ponto com mais tempo de exposição do dia de jogo.",
           BODY, 21, W, width=1060, leading=29)
    P.tag(1700, 190, "Projeção ilustrativa")


def p_transmissao(P):
    P.rect(0, 0, PW, PH, K)
    P.image(prep(T + "c-transmissao-composta.jpg", "transmissao", 1080, PH, "warm", (0.6, 0.5)), 840, 0, 1080, PH)
    P.text(64, 110, "04", HEAD, 28, Y)
    P.fit(64, 270, "SUA MARCA NA", 700, DISPLAY, 200, Y, tracking=-5)
    P.fit(64, 440, "TRANSMISSÃO", 700, DISPLAY, 200, Y, tracking=-5)
    P.fit(64, 610, "AO VIVO.", 700 * 0.62, DISPLAY, 200, Y, tracking=-5)
    P.text(64, 690, "A TV AME transmite os jogos ao vivo no YouTube, para mais de 5 mil inscritos. A marca "
           "entra com vídeo, som e telefone na tela e no intervalo, e continua no vídeo gravado.",
           BODY, 21, W, width=700, leading=29)
    P.text(64, 900, "APLICAÇÕES", HEAD, 12, Y, tracking=200)
    P.text(64, 940, "VINHETA · TELA · LOCUÇÃO · REPLAY", HEAD, 26, W, tracking=-5)
    # a peça vendida, desenhada em vetor: o lettering da transmissão
    bx, by = 900, 924
    P.rect(bx, by, 960, 46, Y)
    P.text(bx + 20, by + 31, "TV AME · AO VIVO · SUA MARCA AQUI", HEAD, 20, K, tracking=60)
    P.rect(bx, by + 46, 960, 110, K, opacity=88)
    for k, (cat, a, sc, b) in enumerate([("SUB-11", "EQUIPE A", "1 × 0", "EQUIPE B"), ("SUB-13", "EQUIPE C", "2 × 2", "EQUIPE D")]):
        yy = by + 88 + k * 46
        P.text(bx + 20, yy, cat, HEAD, 18, Y, tracking=80)
        P.text(bx + 300, yy, a, HEAD, 20, W, justify="right")
        P.text(bx + 380, yy, sc, HEAD, 22, Y, justify="center")
        P.text(bx + 460, yy, b, HEAD, 20, W)
    P.mark(bx + 800, by + 76, 120, Y)
    P.tag(1700, 50, "Projeção ilustrativa")
    P.strip(1040, Y, x1=800, n=1)


def p_noite(P):
    P.rect(0, 0, PW, PH, Y)
    P.image(prep(T + "c-noite-composta.jpg", "noite", 960, PH, "warm", (0.5, 0.5)), 0, 0, 960, PH)
    X = 1040
    P.text(X, 110, "05", HEAD, 28, K)
    for k in range(5):
        P.star(X + 150 + k * 52, 100, 20, K)
    P.fit(X, 300, "SUA MARCA NA", 800, DISPLAY, 200, K, tracking=-5)
    P.fit(X, 480, "NOITE DAS", 800 * 0.74, DISPLAY, 200, K, tracking=-5)
    P.fit(X, 660, "ESTRELAS.", 800 * 0.74, DISPLAY, 200, K, tracking=-5)
    P.text(X, 730, "O campeonato termina num teatro: a Noite das Estrelas premia os melhores de cada "
           "categoria diante das famílias. A marca está no backdrop do palco, no anúncio dos prêmios e "
           "nas fotos que os pais guardam.", BODY, 22, K, width=780, leading=31)
    P.text(X, 920, "APLICAÇÕES", HEAD, 12, K, tracking=200)
    P.text(X, 960, "BACKDROP · PALCO · ANÚNCIO · FOTOS", HEAD, 26, K, tracking=-5)
    P.tag(64, 1040, "Imagem ilustrativa")
    P.strip(1040, K, x0=X, x1=1856, n=1)


def p_onde(P):
    # Nike 08: pôster de cor cheia, tipografia preta e nada mais.
    P.rect(0, 0, PW, PH, Y)
    P.text(64, 200, "ONDE MAIS\nSUA MARCA\nPODE\nAPARECER.", HEAD, 124, K, tracking=-30, leading=114)
    items = [("APP DA A.M.E", "Janela fixa com link para o WhatsApp da marca."),
             ("REDES DO @AMECRIANCA", "Collabs, ações e posts no perfil oficial, por cota."),
             ("PANFLETO PELOS FOTÓGRAFOS", "Verso do panfleto com QR do site de fotos. Uma marca por panfleto."),
             ("MASCOTE OFICIAL", "Entrada dos times, finais e redes, com a camisa do patrocinador."),
             ("FINAIS E BRINDES", "Anúncio nas finais e brindes em dia de jogo, por cota.")]
    y = 120
    for name, desc in items:
        P.rect(1000, y, 856, 3, K)
        P.text(1000, y + 52, name, HEAD, 34, K, tracking=-10)
        P.text(1000, y + 92, desc, BODY, 20, K)
        y += 168
    P.mark(64, 880, 200, K)
    P.strip(1040, K)


def p_cotas(P):
    # Nike 06 de novo, como abertura da oferta.
    P.rect(0, 0, PW, PH, K)
    P.image(prep(T + "c-capa-composta.jpg", "cotas", PW, PH, "bw", (0.5, 0.5)), 0, 0, PW, PH)
    P.rect(0, 0, PW, PH, K, opacity=55)
    P.fit(64, 260, "COTAS DE PATROCÍNIO", PW - 128, DISPLAY, 300, Y, tracking=-5)
    P.strip(310, Y)
    P.text(64, 860, "A A.M.E abre três cotas para 2027, cada uma presa a um lugar real do campeonato: "
           "o nome da copa, a camisa da arbitragem e a beira do campo.", HEAD, 40, W, width=1100,
           leading=48, tracking=-15)
    for k, (n, v) in enumerate([("MASTER", "R$ 18.000"), ("OFICIAL", "R$ 6.000"), ("APOIO", "R$ 2.400")]):
        x = 1300 + k * 200
        P.text(x, 840, n, HEAD, 14, Y, tracking=200)
        P.text(x, 884, v, HEAD, 34, W, tracking=-10)
    P.text(1300, 930, "POR SEMESTRE", HEAD, 12, "#BDBDBD", tracking=200)
    P.strip(1040, Y)


def cota(P, nome, preco, qtd, territorio, frase, itens, exclusiva, foto, focus, rotulo):
    P.rect(0, 0, PW, PH, K)
    P.image(prep(T + foto, "cota-" + nome.lower(), 900, PH, "warm", focus), 0, 0, 900, PH)
    P.tag(64, 60, rotulo)
    X = 980
    P.rect(X, 70, 96, 40, Y)
    P.text(X + 14, 99, "COTA", HEAD, 22, K, tracking=60)
    P.fit(X, 320, nome, 860, DISPLAY, 300, Y, tracking=-5, max_h=260)
    P.text(X, 410, preco, HEAD, 64, W, tracking=-20)
    P.text(X, 450, ("POR SEMESTRE · " + qtd).upper(), HEAD, 13, Y, tracking=180)
    P.text(X, 500, territorio.upper(), HEAD, 13, "#BDBDBD", tracking=180)
    P.text(X, 548, frase, BODY, 24, W, width=860, leading=32)
    P.text(X, 650, "DIREITOS E CONTRAPARTIDAS", HEAD, 13, Y, tracking=200)
    y = bullets(P, X, 692, itens, size=20, step=34, width=820)
    if exclusiva:
        P.text(X, y + 10, exclusiva, HEAD, 20, Y)
    P.strip(1040, Y, x0=X, x1=1856, n=1)


def p_master(P):
    cota(P, "MASTER", "R$ 18.000", "1 cota disponível", "Nome da copa",
         "Seu nome na copa que a região acompanha, do primeiro jogo à Noite das Estrelas.",
         ["Copa AME + sua marca na tabela, no app e nos posts", "Peito da camisa da arbitragem e da organização",
          "Frente da camisa do mascote oficial", "Vídeo de 15 s em todas as transmissões da TV AME",
          "Janela fixa no app, com link direto ao seu WhatsApp", "4 placas e 2 wind banners no campo, aos sábados",
          "Verso do panfleto do site de fotos", "4 collabs no @amecrianca e anúncio nas finais e na Noite das Estrelas"],
         "Exclusividade de categoria até o fim do semestre", "c-master.jpg", (0.42, 0.5), "Imagem ilustrativa")


def p_oficial(P):
    cota(P, "OFICIAL", "R$ 6.000", "4 cotas disponíveis", "Camisa da arbitragem",
         "Sua marca em campo e na transmissão, toda semana, perto de quem decide a compra da casa.",
         ["Manga da camisa da arbitragem", "2 placas na beira do campo aos sábados",
          "Logo no canto da tela em todas as transmissões", "Logo rotativo no rodapé do app da A.M.E",
          "2 collabs no feed do @amecrianca", "Logo no backdrop da Noite das Estrelas"],
         None, "c-arbitragem-composta.jpg", (0.5, 0.5), "Projeção ilustrativa")


def p_apoio(P):
    cota(P, "APOIO", "R$ 2.400", "8 cotas disponíveis", "Beira do campo · por semestre ou permuta",
         "Presença em campo e no backdrop, com troca em produto ou serviço quando fizer sentido.",
         ["1 placa na beira do campo em rodízio aos sábados", "Logo no backdrop Copa AME",
          "1 post coletivo de apoiadores no @amecrianca", "Brinde da marca em dia de jogo"],
         None, "c-apoio-composta.jpg", (0.4, 0.55), "Projeção ilustrativa")


def p_contato(P):
    # Nike 21: o cartaz final, só tipografia.
    P.rect(0, 0, PW, PH, Y)
    P.text(64, 110, "PRÓXIMO PASSO", HEAD, 15, K, tracking=220)
    P.fit(64, 420, "VAMOS CONSTRUIR", PW - 128, DISPLAY, 300, K, tracking=-5)
    P.strip(480, K)
    P.fit(64, 830, "JUNTOS.", 1100, DISPLAY, 300, K, tracking=-5)
    for k, (lab, val) in enumerate([("JÚNIOR", "(17) 99147-2050"), ("NICOLLAS", "(17) 99711-1195"),
                                    ("INSTAGRAM", "@amecrianca")]):
        x = 64 + k * 420
        P.text(x, 930, lab, HEAD, 13, K, tracking=200)
        P.text(x, 980, val, HEAD, 40, K, tracking=-10)
    P.image(prep_cutout("logo-ame-320-x3.png", "logo", mode="color"), 1600, 640, 256, 175)
    P.mark(1640, 880, 200, K)
    P.strip(1040, K)


PAGES = [p_capa, p_manifesto, p_campo, p_quemjoga, p_territorio, p_alcance, p_pontos, p_nome,
         p_arbitragem, p_beira, p_transmissao, p_noite, p_onde, p_cotas, p_master, p_oficial,
         p_apoio, p_contato]

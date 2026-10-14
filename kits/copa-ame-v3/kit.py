# Copa AME 2027 pela skill v10.
# Referências (escolha do Ugo, 14/10/2026): Japa 2025 (letreiro cursivo gigante atravessando a pessoa recortada, fundo
# preto degradê, pílulas, números grandes), Nike Paris 2024 (P&B com rastro, rótulo de máquina, página inteira em cor
# com frase grande), Tupã FC (manchas de listras diagonais, cota com lista e foto em faixa). Cores da A.M.E.
# Conteúdo: copa-ame-v3/mediakit.json, sem mudar texto nem número. Imagens: só as do acervo da v3.
import os, sys, re, json, argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from mediakit import kit, fotos
from mediakit.pagina import bounds as _bounds
from mediakit.vc import VC

# >>> TROCA caminhos
CL = os.path.expanduser("~/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/AME CRIANCA/MEDIAKIT")
KIT = os.path.join(CL, "copa-ame-v3")
AC = os.path.join(KIT, "acervo")
ASSETS = os.path.join(KIT, "assets-v10")
# <<< TROCA caminhos
os.makedirs(ASSETS, exist_ok=True)
D = json.load(open(os.path.join(KIT, "mediakit.json"), encoding="utf-8"))

PW, PH = 1920, 1080
# >>> TROCA cores
K, Y, W, G1, G2, CLARO = "#0B0B0C", "#F5D80A", "#F4F4F2", "#1B1B1E", "#2C2C30", "#EFEEEA"
CINZA = "#9A9A9A"
# <<< TROCA cores
# >>> TROCA fontes
SCRIPT = ("Snell Roundhand", "Black")
SERIFA = ("Bodoni 72", "Book Italic")
COND = ("Helvetica Neue", "Condensed Black")
BOLD = ("Helvetica Neue", "Bold")
MED = ("Helvetica Neue", "Medium")
MONO = ("Menlo", "Regular")
# <<< TROCA fontes

vc = VC()
ex = vc.ex
bounds = lambda oid: _bounds(ex, oid)


def limpo(s):
    return re.sub(r"<[^>]+>", "", s).replace("|", " ")


def num(v):
    return f"{v:,}".replace(",", ".")


# ------------------------------------------------------------ insumos raster
def foto(src, name, w, h, mode="bw", foco=(0.5, 0.5), rastro=0, escuro=1.0):
    r = fotos.preparar_foto(os.path.join(AC, src), os.path.join(ASSETS, name + ".jpg"), w, h, mode, foco, rastro, escuro)
    return str(r["caminho"])


# ------------------------------------------------------------ elementos do estilo
def fundo(P, centro=G2, x0=0.5, y0=0.45):
    """Preto com luz no meio (degradê radial em vetor), como os fundos da Japa."""
    r = P.rect(0, 0, PW, PH, fill=K)
    ex("select.set", {"ids": [r]})
    ex("paint.setFill", {"gradient": {"kind": "radial", "stops": [{"offset": 0, "color": centro}, {"offset": 1, "color": K}]}})
    ex("select.none")
    return r


def script(P, x, y, s, size, cor=Y, justify=None):
    return P.text(x, y, s, SCRIPT, size, cor, justify=justify)


def mono(P, x, y, s, size=15, cor=W, tracking=120, justify=None):
    return P.text(x, y, s.upper(), MONO, size, cor, tracking=tracking, justify=justify)


def pilula(P, x, y, s, cor=W, cheia=False, fg=K):
    """Etiqueta em pílula (Japa): contorno fino, texto de máquina."""
    t = mono(P, x, y, s, 14, fg if cheia else cor, 160)
    b = bounds(t)
    r = P.rect(b["x"] - P.ox - 18, b["y"] - 11, b["width"] + 36, b["height"] + 22, fill=cor if cheia else None,
               stroke=None if cheia else cor, sw=1.2, radius=(b["height"] + 22) / 2)
    ex("select.set", {"ids": [r]})
    ex("object.arrange.sendBackward")
    ex("select.none")
    return t


def inclinado(P, x, y, s, size, cor=Y, leading=None, angulo=-10):
    """Caixa alta condensada inclinada, a voz das frases grandes da Nike Paris."""
    t = P.text(x, y, s, COND, size, cor, tracking=-10, leading=leading or size * 0.92)
    ex("select.set", {"ids": [t]})
    ex("object.shear", {"angle": angulo, "axis": "horizontal"})
    ex("select.none")
    return t


def listras(P, x, y, w, h, cor=Y, passo=26, grossura=12):
    """Mancha de listras diagonais presa ao canto (Tupã FC), recortada na caixa."""
    ids = []
    for k in range(-int(h), int(w) + int(h), passo):
        ids.append(P.path(P.poly_d([(x + k, y + h), (x + k + grossura, y + h), (x + k + grossura + h, y), (x + k + h, y)]),
                          fill=cor))
    caixa = P.rect(x, y, w, h, fill=K)
    ex("select.set", {"ids": ids})
    g = ex("object.group")["id"]
    ex("select.set", {"ids": [caixa]})
    ex("object.arrange.bringToFront")
    ex("select.set", {"ids": [g, caixa]})
    ex("object.clippingMask.make")
    ex("select.none")


def logo(P, x, y, w=170):
    P.image(os.path.join(AC, "logo-ame-320-x3.png"), x, y, w, w * 657 / 960, aceito="logo da A.M.E só existe em raster")


def selo(P, x, y, s="Projeção ilustrativa"):
    pilula(P, x, y, s, Y, cheia=True)


def rodape(P, n, cor=CINZA):
    mono(P, 96, 1040, f"COPA AME 2027  ·  {n:02d}", 12, cor, 160)


# ------------------------------------------------------------ páginas
def p_capa(P):
    fundo(P, "#34343A")
    script(P, 60, 640, "Copa", 520)
    atleta = os.path.join(AC, "real-atleta-recorte.png")
    P.image(atleta, 760, 90, 792, 990)
    script(P, 980, 980, "AME", 290)
    P.aceitar_sobreposicao("Copa", "AME", "letreiro cursivo entrelaçado de propósito (referência Japa)")
    pilula(P, 96, 90, "2027")
    pilula(P, 1700, 90, "Mídia kit")
    listras(P, 1600, 0, 320, 60)
    logo(P, 96, 860, 190)
    mono(P, 96, 1030, "43ª edição  ·  São José do Rio Preto e região  ·  sub-06 a sub-20", 14, W, 140)


def p_manifesto(P):
    P.rect(0, 0, PW, PH, fill=K)
    P.image(foto("tratado/c-paifilho.jpg", "paifilho-mov", 900, PH, "bw", (0.55, 0.5), rastro=36), 0, 0, 900, PH)
    selo(P, 40, 1040, "Imagem ilustrativa")
    mono(P, 1000, 170, "Manifesto  ·  desde 2005", 15, Y, 160)
    inclinado(P, 1000, 330, "UM PAI CRIOU\nUM CAMPEONATO", 120, Y)
    P.text(1004, 530, "para o filho ter onde jogar.", SERIFA, 54, W)
    P.text(1004, 630, limpo(D["manifesto"]["frase"]), MED, 28, W, leading=42, width=800)
    mono(P, 1004, 1040, "COPA AME 2027  ·  02", 12, CINZA, 160)


def p_publico(P):
    fundo(P)
    script(P, 80, 260, "Quem está", 230)
    script(P, 300, 430, "em campo", 200, W)
    P.aceitar_sobreposicao("Quem está", "em campo", "letreiro cursivo entrelaçado de propósito (referência Japa)")
    P.image(foto("tratado/real-equipe-sub.jpg", "equipe-bw", 480, 320, "bw", (0.5, 0.5)), 1360, 300, 480, 320)
    stats = [("10 mil", "atletas por semestre, sub-06 a sub-20"), ("750", "equipes por semestre"),
             ("10 mil", "famílias acompanhando")]
    for k, (v, rot) in enumerate(stats):
        x = 96 + k * 600
        P.text(x, 790, v, SERIFA, 150, Y)
        P.rect(x, 830, 480, 1.5, fill=W, opacity=40)
        P.text(x, 875, rot, MED, 26, W)
    P.text(96, 560, D["publico"]["descricao"], MED, 24, CINZA, leading=36, width=1100)
    mono(P, 96, 1040, "2026  ·  números informados pela organização", 12, CINZA, 160)


def p_historico(P):
    P.rect(0, 0, PW, PH, fill=CLARO)
    listras(P, 0, 0, 340, 120, K)
    P.image(os.path.join(AC, "tratado/backdrop-1400.jpg"), 96, 230, 700, 588)
    script(P, 900, 250, "Quem já joga", 150, K)
    P.text(905, 330, "com a gente", COND, 70, K, tracking=-10)
    P.aceitar_sobreposicao("Quem já joga", "com a gente", "letreiro cursivo entrelaçado de propósito (referência Japa)")
    y = 420
    for p in D["historico"][0]["patrocinadores"]:
        P.rect(905, y - 18, 14, 14, fill=Y)
        P.text(935, y, p["marca"], BOLD, 26, K)
        P.text(935, y + 32, p["o_que_fez"], MED, 19, "#555555")
        y += 84
    mono(P, 96, 880, "Backdrop da Copa AME 2026", 12, "#555555", 160)
    rodape(P, 4, "#777777")


def p_territorio(P):
    fundo(P)
    script(P, 80, 280, "Quatro cidades", 200)
    P.text(90, 370, "UMA COPA", COND, 80, W, tracking=-10)
    P.aceitar_sobreposicao("Quatro cidades", "UMA COPA", "letreiro cursivo entrelaçado de propósito (referência Japa)")
    cidades = [("Sede", "São José do Rio Preto"), ("Cidade-sede", "Araçatuba"), ("Cidade-sede", "Taquaritinga"),
               ("Cidade-sede", "Bauru")]
    for k, (tipo, nome) in enumerate(cidades):
        x = 96 + k * 440
        P.rect(x, 520, 380, 220, fill=G1, radius=22)
        pilula(P, x + 40, 580, f"{k + 1}ª  {tipo}", Y, cheia=(k == 0))
        P.text(x + 30, 690, nome, BOLD, 34 if len(nome) < 16 else 28, W)
        if k < 3:
            P.text(x + 392, 640, "▶", BOLD, 26, Y)
    P.text(96, 860, D["territorio"]["texto"], MED, 26, W, leading=40, width=1100)
    P.image(os.path.join(AC, "elementos/bola-jogo.png"), 1560, 760, 260, 260)
    rodape(P, 5)


def p_alcance(P):
    fundo(P, "#2A2A2E", 0.3)
    script(P, 80, 250, "Alcance", 220)
    P.text(930, 250, "digital", SERIFA, 110, W)
    graf = D["prova"]["graficos"]
    for k, g in enumerate(graf):
        y0 = 400 + k * 280
        mono(P, 96, y0, g["titulo"], 14, Y, 140)
        maior = max(s["valor"] for s in g["series"])
        for j, s in enumerate(g["series"]):
            y = y0 + 40 + j * 90
            w = 820 * s["valor"] / maior
            P.rect(96, y, w, 56, fill=Y if j else G2)
            P.text(96 + w + 24, y + 44, num(s["valor"]), SERIFA, 50, W)
            mono(P, 96 + 16, y + 36, s["rotulo"], 13, K if j else W, 120)
    lado = [("20.200", "seguidores no Instagram"), ("559", "novos seguidores em 30 dias"), ("5.180", "inscritos na TV AME")]
    for k, (v, r) in enumerate(lado):
        y = 470 + k * 200
        P.text(1340, y, v, SERIFA, 120, Y if k == 0 else W)
        P.text(1344, y + 50, r, MED, 24, CINZA)
    mono(P, 96, 1000, D["prova"]["rodape"], 12, CINZA, 100)
    rodape(P, 6)


def p_divisor(P):
    P.rect(0, 0, PW, PH, fill=Y)
    P.image(os.path.join(AC, "real-goleiro-recorte.png"), 1080, 140, 940, 940)
    inclinado(P, 96, 330, "ONDE A FAMÍLIA\nINTEIRA VÊ\nA SUA MARCA.", 150, K)
    P.text(100, 830, "10", SERIFA, 200, K)
    P.text(320, 790, "pontos de\nexposição", BOLD, 34, K, leading=44)
    P.text(100, 920, D["divisor_inventario"]["subtitulo"], MED, 26, K, width=880, leading=38)
    mono(P, 96, 1040, "COPA AME 2027  ·  07", 12, K, 160)


ATIVOS = {"Nome da competição": ("A Copa", "c-projecao-composta.jpg", True),
          "Camisa da arbitragem e da organização": ("Arbitragem", "real-arbitragem-entrada.jpg", False),
          "Beira do campo": ("Beira", "c-beira-composta.jpg", True),
          "Transmissão ao vivo TV AME": ("Ao vivo", "c-transmissao-composta.jpg", True),
          "Noite das Estrelas": ("Estrelas", "c-noite-composta.jpg", True)}


def ativo(n, i):
    a = D["inventario"][i]
    palavra, img, projecao = ATIVOS[a["ativo"]]

    def pagina(P):
        P.rect(0, 0, PW, PH, fill=K)
        P.image(foto("tratado/" + img, f"ativo-{i}", 1100, PH, "warm", (0.6, 0.5), escuro=0.95), 820, 0, 1100, PH)
        fundo_l = P.rect(0, 0, 900, PH, fill=K)
        ex("select.set", {"ids": [fundo_l]})
        ex("paint.setFill", {"gradient": {"kind": "linear", "angle": 0, "stops": [
            {"offset": 0, "color": K}, {"offset": 0.78, "color": K}, {"offset": 1, "color": K, "opacity": 0}]}})
        ex("select.none")
        mono(P, 96, 150, f"{i + 1:02d} / 05  ·  ativo {a['grupo']}", 14, Y, 160)
        script(P, 70, 400, palavra, 230)
        titulo = a["titulo"].replace("||", " ")
        P.text(96, 500, titulo, COND, 64, W, tracking=-10, width=700, leading=62)
        P.text(96, 700, a["texto"], MED, 25, W, leading=38, width=700)
        x = 96
        for ap in a["aplicacoes"]:
            t = pilula(P, x + 18, 960, ap, Y)
            x = bounds(t)["x"] - P.ox + bounds(t)["width"] + 34
        if a.get("mini_id") == "f-tabela":
            P.image(os.path.join(AC, "pdf/app-tabela-rodada.jpg"), 1240, 760, 600, 283)
            mono(P, 1240, 1065, "A tabela da rodada já leva o nome do patrocinador", 12, W, 80)
        if projecao:
            selo(P, 1660, 70)
        rodape(P, n)
    pagina.__name__ = f"p_ativo_{i}"
    return pagina


def p_inventario(P):
    fundo(P)
    P.text(96, 200, "10 PONTOS", COND, 120, Y, tracking=-10)
    script(P, 700, 210, "de exposição", 150, W)
    grupos = [("fisico", "Físico"), ("digital", "Digital"), ("experiencia", "Experiência")]
    for k, (g, nome) in enumerate(grupos):
        x = 96 + k * 600
        pilula(P, x + 18, 330, nome, Y, cheia=True)
        y = 420
        for a in [a for a in D["inventario"] if a["grupo"] == g]:
            P.rect(x, y - 20, 16, 16, fill=Y)
            P.text(x + 34, y, a["ativo"], BOLD, 26, W, width=520)
            P.text(x + 34, y + 34, a["onde"], MED, 19, CINZA, width=500, leading=26)
            y += 130
    rodape(P, 13)


def p_divisor_cotas(P):
    P.image(foto("tratado/c-capa-composta.jpg", "cotas-fundo", PW, PH, "bw", (0.5, 0.5), escuro=0.4), 0, 0, PW, PH,
            aceito="foto de fundo escurecida em página cheia")
    script(P, 960, 560, "Cotas", 460, Y, justify="center")
    pilula(P, 930, 700, "2027", W)
    P.text(410, 800, limpo(D["cotas_intro"]), MED, 32, W, leading=46, width=1100, justify="center")
    rodape(P, 14, W)


def cota(n, i):
    c = D["cotas"][i]
    imgs = {"c-master": "c-master.jpg", "c-arb-cota": "c-arbitragem-composta.jpg", "c-apoio": "c-apoio-composta.jpg"}

    def pagina(P):
        P.rect(0, 0, PW, PH, fill=CLARO)
        P.image(foto("tratado/" + imgs[c["cena_id"]], f"cota-{i}", 560, PH, "warm", (0.5, 0.5)), 0, 0, 560, PH)
        listras(P, 560, 0, 60, PH, K)
        script(P, 690, 250, "Cota", 140, K)
        P.text(690, 420, c["nome"].upper(), COND, 150, K, tracking=-10)
        mono(P, 696, 470, f"{c['quantidade']} cota{'s' if c['quantidade'] > 1 else ''}  ·  {c['territorio']}", 15,
             "#444444", 120)
        P.ellipse(1560, 260, 120, 120, fill=Y)
        P.text(1560, 240, "R$", BOLD, 34, K, justify="center")
        P.text(1560, 310, num(c["preco"]), SERIFA, 62, K, justify="center")
        P.text(1560, 420, "por semestre", MED, 20, "#444444", justify="center")
        P.text(696, 560, c["frase"], SERIFA, 36, K, leading=46, width=1130)
        meio = (len(c["entregaveis"]) + 1) // 2
        for j, e in enumerate(c["entregaveis"]):
            x = 696 + (j // meio) * 590
            y = 690 + (j % meio) * 76
            P.rect(x, y - 18, 16, 16, fill=Y)
            P.text(x + 34, y, e, MED, 23, K, width=520, leading=30)
        if c.get("exclusividade"):
            mono(P, 696, 1045, f"Exclusividade de {c['exclusividade']['categoria']} até {c['exclusividade']['ate']}", 13,
                 K, 120)
        if "composta" in imgs[c["cena_id"]]:
            selo(P, 40, 1030)
        else:
            selo(P, 40, 1030, "Imagem ilustrativa")
        mono(P, 1560, 1040, f"COPA AME 2027  ·  {n:02d}", 12, "#777777", 160)
    pagina.__name__ = f"p_cota_{i}"
    return pagina


def p_contato(P):
    fundo(P, "#33333A")
    script(P, 960, 330, "Vamos jogar juntos?", 150, Y, justify="center")
    P.image(os.path.join(AC, "real-mascote-arbitragem-recorte.png"), 560, 420, 800, 533)
    for k, p in enumerate(D["acao"]["pessoas"]):
        x = 300 + k * 1320
        mono(P, x, 560, p["nome"], 15, Y, 160, justify="center")
        P.text(x, 610, p["telefone"], BOLD, 34, W, justify="center")
    pilula(P, 880, 1000, "@amecrianca", W)
    obs = D["condicoes"]["observacoes"]
    for k, o in enumerate(obs):
        mono(P, 96 if k == 0 else (700 if k == 1 else 1320), 1045, o, 11, CINZA, 40)
    logo(P, 96, 80, 150)
    mono(P, 1824, 110, "Proposta válida até 31/12/2026", 12, CINZA, 120, justify="right")


PAGES = [p_capa, p_manifesto, p_publico, p_historico, p_territorio, p_alcance, p_divisor,
         ativo(8, 0), ativo(9, 1), ativo(10, 2), ativo(11, 3), ativo(12, 4),
         p_inventario, p_divisor_cotas, cota(15, 0), cota(16, 1), cota(17, 2), p_contato]

if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--saida", default=os.path.join(KIT, "saida-v10"))
    saida = a.parse_args().saida
    r = kit.montar("copa-ame-v3-v10", PAGES, os.path.join(saida, "kit-copa-ame-2027.pdf"),
                   os.path.join(saida, "copa-ame-2027.vectorcraft"), vc=vc)
    vc.close()
    print(r["pdf"], r["segundos"], "s")
    for av in r["avisos_foto"]:
        if not av["aceito"]:
            print(f"aviso de foto: p{av['pagina']} {av['arquivo']} {av['ppi']} ppi")

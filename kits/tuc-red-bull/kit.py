# TUC (Torneio Universitário de Campinas) 2027 para a Red Bull (cota principal sob medida).
# Visual: UFC Rebrand (planos chapados cortados a partir de um vértice, numeral gigante com eco, tinta da marca na
# foto, itálico pesado). Do Spurs, só a palavra-fantasma atrás do atleta (p. 4). Escolha do Ugo em 14/10/2026.
# Estrutura: proposta para uma marca (guia ESTRATÉGIA DE PATROCÍNIO, §6.2). Textos: ficha.md aprovada em 14/10/2026.
import os, sys, argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from mediakit import kit, cenas
from mediakit.pagina import Pagina as Page, bounds as _bounds
from mediakit.vc import VC

CL = os.path.expanduser("~/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/TUC/MEDIAKIT")
KIT = os.path.join(CL, "tuc-red-bull")
AC = os.path.join(KIT, "acervo")
OF = os.path.join(AC, "oficial-2026")  # identidade enviada pelo TUC (Drive, 14/10/2026): não alterar o desenho
ASSETS = os.path.join(KIT, "assets")
os.makedirs(ASSETS, exist_ok=True)

PW, PH = 1920, 1080
BO, RD, K, W, CZ, GR = "#5B0508", "#A6070C", "#0B0B0C", "#FFFFFF", "#E9E9E9", "#8E8E8E"
CO = "#FF5A5F"  # vermelho claro: o vermelho do TUC sobre fundo escuro dava contraste de 2,5:1 (revisor, 14/10)
FANT = "#6A0A0E"  # palavra-fantasma: um tom acima do bordô (Spurs: 5 a 9 % de diferença)
COND = ("Helvetica Neue", "Condensed Black")
BOLD = ("Helvetica Neue", "Bold")
MED = ("Helvetica Neue", "Medium")
ITAL = -12  # o itálico pesado do UFC, feito por inclinação

vc = VC()
ex = vc.ex
bounds = lambda oid: _bounds(ex, oid)


# ------------------------------------------------------------ insumos raster
def escudo():
    """O escudo oficial, só aparado nas bordas transparentes."""
    out = os.path.join(ASSETS, "escudo.png")
    if not os.path.exists(out):
        im = Image.open(os.path.join(OF, "logo-fundo-escuro.png")).convert("RGBA")
        im.crop(im.getchannel("A").getbbox()).save(out)
    return out


ESC_R = 1481 / 1382


def redbull(cor="original"):
    """Wordmark da Red Bull (Wikimedia Commons). Na cor dela, ou toda branca em fundo escuro (só a tinta muda)."""
    src = os.path.join(AC, "logo-red-bull.png")
    if cor == "original":
        return src
    out = os.path.join(ASSETS, "red-bull-branco.png")
    if not os.path.exists(out):
        a = Image.open(src).convert("RGBA").getchannel("A")
        Image.merge("RGBA", (a.point(lambda _: 255),) * 3 + (a,)).save(out)
    return out


RB_R = 1920 / 465


def colmeia():
    """A textura de colmeia do TUC (fundo oficial), clareada para ir a poucos por cento sobre o escuro."""
    out = os.path.join(ASSETS, "colmeia.png")
    if not os.path.exists(out):
        im = Image.open(os.path.join(OF, "grade-fundo-escuro.png")).convert("RGBA")
        a = im.getchannel("A")
        Image.merge("RGBA", (a.point(lambda _: 255),) * 3 + (a,)).save(out)
    return out


def duotone(src, name, w, h, foco=(0.5, 0.5), escuro=K, claro=W, meio=RD):
    """A tinta da marca vai na foto (UFC, p. 13): cinza mapeado em preto, vermelho e branco."""
    out = os.path.join(ASSETS, name + ".jpg")
    im = Image.open(src).convert("RGB")
    ar, (iw, ih) = w / h, im.size
    cw, ch = (ih * ar, ih) if iw / ih > ar else (iw, iw / ar)
    cx = min(max(foco[0] * iw, cw / 2), iw - cw / 2)
    cy = min(max(foco[1] * ih, ch / 2), ih - ch / 2)
    im = im.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2)))
    g = np.asarray(ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1)).astype("float32") / 255
    cor = lambda c: np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], "float32")
    e, m, c = cor(escuro), cor(meio), cor(claro)
    t = g[..., None]
    rgb = np.where(t < 0.55, e + (m - e) * (t / 0.55), m + (c - m) * ((t - 0.55) / 0.45))
    Image.fromarray(rgb.clip(0, 255).astype("uint8")).save(out, quality=90)
    return out


def cena(nome):
    """Só a gerada aprovada pelo Ugo, e só se o arquivo ainda é o que ele viu."""
    p, rota = cenas.escolher_cena(AC, nome.replace(".png", "-composta.png"), nome)
    if rota != "gerada":
        raise SystemExit(f"cena {nome} não aprovada (ou mudou depois da aprovação)")
    return str(p)


IA = "cena gerada pela IA (o gerador entrega no máximo 1672 px)"


# ------------------------------------------------------------ elementos do sistema
def poly(P, pts, cor, opacity=None):
    return P.path(P.poly_d(pts), fill=cor, opacity=opacity)


def mascarar(ids, P, pts):
    """Recorta os objetos pelo polígono (o polígono vira máscara, por cima de tudo)."""
    m = poly(P, pts, K)
    ex("select.set", {"ids": [m]})
    ex("object.arrange.bringToFront")
    ex("select.set", {"ids": list(ids) + [m]})
    if len(ids) > 1:
        g = ex("object.group")["id"]
        ex("select.set", {"ids": [g, m]})
    ex("object.clippingMask.make")
    ex("select.none")


PAGINA = [(0, 0), (PW, 0), (PW, PH), (0, PH)]


def planos(vx=500, topo=1114, dir_y=260):
    """Os três planos do UFC (p. 6): dois cortes perpendiculares que nascem do mesmo vértice na borda de baixo."""
    v = (vx, PH)
    esq = [(0, 0), (topo, 0), v, (0, PH)]
    meio = [(topo, 0), (PW, 0), (PW, dir_y), v]
    dir = [v, (PW, dir_y), (PW, PH)]
    return esq, meio, dir


def pintar_planos(P, ps, cores, fio=True):
    for pts, c in zip(ps, cores):
        poly(P, pts, c)
    if fio:  # fio branco fino no segundo corte
        v, d = ps[2][0], ps[2][1]
        P.path(P.poly_d([v, d], closed=False), stroke=W, sw=3)


def inclinar(t, ang=ITAL):
    ex("select.set", {"ids": [t]})
    ex("object.shear", {"angle": ang, "axis": "horizontal"})
    ex("select.none")
    return t


def cruzar(P, x, y, s, size, tintas, font=COND, max_w=None, motivo="a mesma palavra em cada plano, recortada"):
    """A palavra atravessa os cortes e troca de tinta em cada plano (UFC, FIGHT NIGHT). tintas: [(polígono, cor)]."""
    ids = []
    for pts, cor in tintas:
        if max_w:
            t, _ = P.fit(x, y, s, max_w, font, size, cor, tracking=-10)
        else:
            t = P.text(x, y, s, font, size, cor, tracking=-10)
        inclinar(t)
        mascarar([t], P, pts)
        ids.append(t)
    for _ in tintas[1:]:
        P.aceitar_sobreposicao(s, s, motivo)
    return ids


def numeral(P, x, y, n, size, cor=RD, eco=W, rotulo=None, rcor=W):
    """Numeral gigante sólido com eco em contorno deslocado e o rótulo apoiado numa barra (UFC, ROUND 5)."""
    e = P.text(x - size * 0.035, y - size * 0.05, n, COND, size, eco, tracking=-20)
    ex("text.setRangeStyle", {"id": e, "fill": "none", "stroke": eco, "strokeWidth": 2})
    inclinar(e)
    t = P.text(x, y, n, COND, size, cor, tracking=-20)
    inclinar(t)
    P.aceitar_sobreposicao(n, n, "eco em contorno do numeral (UFC)")
    b = bounds(t)
    if rotulo:
        P.rect(b["x"] - P.ox, y + 26, b["width"], 10, fill=cor)
    return b


def tag(P, x, y, s, fg=K, bg=W):
    t = P.text(x, y, s.upper(), BOLD, 14, fg, tracking=160)
    b = bounds(t)
    r = P.rect(b["x"] - P.ox - 10, b["y"] - 7, b["width"] + 20, b["height"] + 14, fill=bg)
    ex("select.set", {"ids": [r]})
    ex("object.arrange.sendBackward")
    ex("select.none")


def head(P, x, y, s, size, cor=W, marca=None, mcor=RD, leading=None, justify=None, font=COND, ital=True):
    t = P.text(x, y, s, font, size, cor, tracking=-10, leading=leading or size * 0.96, justify=justify)
    if marca:
        i = s.find(marca)
        if i >= 0:
            ex("text.setStyle", {"ids": [t], "start": len(s[:i].encode()), "end": len(s[:i + len(marca)].encode()),
                                 "fill": mcor})
    return inclinar(t) if ital else t


def fantasma(P, palavra, y, cor=FANT, area=PAGINA, opacity=None):
    """Palavra gigante cortada nas duas bordas, um tom acima do fundo (Spurs)."""
    t, _ = P.fit(-70, y, palavra, PW + 140, COND, 400, cor, tracking=-10)
    if opacity is not None:
        ex("transparency.set", {"ids": [t], "opacity": opacity})
    mascarar([t], P, area)
    return t


def textura(P, area, op=6):
    img = P.image(colmeia(), 0, 0, PW, PH, aceito="textura de fundo (colmeia oficial do TUC)")
    ex("transparency.set", {"ids": [img], "opacity": op})
    mascarar([img], P, area)


def projecao(P, x=1660, y=60):
    tag(P, x, y, "Projeção ilustrativa", K, W)


def assinatura(P, x, y, h=86, cor_rb="branco"):
    """Escudo do TUC e wordmark da Red Bull lado a lado, separados por um fio."""
    P.image(escudo(), x, y, h * ESC_R, h)
    xr = x + h * ESC_R + 34
    P.rect(xr - 17, y + h * 0.15, 2, h * 0.7, fill=W, opacity=60)
    rh = h * 0.42
    P.image(redbull(cor_rb), xr + 17, y + (h - rh) / 2, rh * RB_R, rh)


# ------------------------------------------------------------ páginas
def p_capa(P):
    esq, meio, dir = planos()
    pintar_planos(P, (esq, meio, dir), (RD, K, CZ))
    head(P, 96, 150, "TUC apresentado\npor Red Bull.", 96, W, ital=True)
    cruzar(P, 130, 730, "2027", 360, [(esq, W), (meio, RD), (dir, K)], max_w=1240)
    P.text(96, 800, "Uma proposta para a edição 2027 do\nTorneio Universitário de Campinas.", MED, 27, W, leading=36)
    P.text(96, 900, "Agosto a dezembro de 2027, Campinas/SP.", BOLD, 24, W)
    eh = 300
    P.image(escudo(), 1500, 50, eh * ESC_R, eh)
    rh = 74
    P.image(redbull(), PW - 96 - rh * RB_R, 930, rh * RB_R, rh)


def p_objetivo(P):
    P.rect(0, 0, PW, PH, CZ)
    dirp = [(1330, 0), (PW, 0), (PW, PH), (1030, PH)]
    poly(P, dirp, BO)
    q = P.text(1500, 900, "?", COND, 900, W, tracking=0)
    inclinar(q)
    P.text(96, 140, "OBJETIVO · O QUE QUEREMOS CONFIRMAR COM VOCÊS", BOLD, 15, RD, tracking=180)
    head(P, 96, 300, "A próxima liga\nuniversitária da Red Bull\npode ser em quadra.", 92, K, "pode ser em quadra.", RD)
    P.text(96, 640, "A Red Bull já reúne universitários para competir: a Wings Cup 2026\ntem mais de 200 instituições. "
                    "Em 2025, ela foi uma das marcas\nda Copa Inter Atléticas, em Uberaba. Em Campinas, as atléticas\n"
                    "já competem de agosto a dezembro.", MED, 29, K, leading=42)
    P.text(96, 860, "Faz sentido para vocês?", BOLD, 34, RD)
    P.text(96, 1020, "FONTES: CORREIO DA MANHÃ, 05/10/2026 (WINGS CUP) · MÁQUINA DO ESPORTE, 30/04/2025 (COPA INTER ATLÉTICAS)",
           BOLD, 12, GR, tracking=120)


def p_porque(P):
    P.rect(0, 0, PW, PH, K)
    textura(P, PAGINA)
    poly(P, [(1660, 0), (PW, 0), (PW, PH), (1480, PH)], BO)
    P.text(96, 110, "POR QUE O TUC", BOLD, 15, CO, tracking=180)
    linhas = [("6", "modalidades", "Vôlei, futsal, handebol, basquete, atletismo\ne natação, de agosto a dezembro."),
              ("14", "atléticas", "De 4 instituições: Unicamp, PUC-Campinas,\nFacamp e Unimax."),
              ("2.000", "atletas", "E 7.500 pessoas envolvidas, segundo a\norganização (informado, sem auditoria).")]
    for k, (n, t, d) in enumerate(linhas):
        y = 400 + k * 280
        b = numeral(P, 110, y, n, 300)
        x = b["x"] - P.ox + b["width"] + 60
        P.text(x, y - 140, t, COND, 64, W, tracking=-10)
        P.text(x, y - 92, d, MED, 25, W, leading=34)
    P.text(96, 1040, "6 MODALIDADES, 14 ATLÉTICAS, 4 INSTITUIÇÕES: PORTAL UNICAMP, 21/08/2026 · 2.000 E 7.500: INFORMADO PELA ORGANIZAÇÃO · 10ª EDIÇÃO EM 2026: @VEMPROTUC",
           BOLD, 12, GR, tracking=120)


def recorte_atleta():
    """O atleta da cena aprovada, recortado (isnet; o modelo de pessoa não está instalado)."""
    src = cena("c-atleta.png")
    out = os.path.join(ASSETS, "atleta-recorte.png")
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(src):
        import subprocess
        r = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[2] / "src/mediakit/ferramentas/recortar.py"),
                            src, out, "--classe", "atleta"], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("recorte do atleta falhou: " + r.stderr[-500:])
    return out


def duotone_rgba(src, name):
    """Duotone no recorte, preservando o canal de transparência."""
    im = Image.open(src).convert("RGBA")
    tmp = os.path.join(ASSETS, name + "-rgb.png")
    im.convert("RGB").save(tmp)
    d = Image.open(duotone(tmp, name, *im.size)).convert("RGB")
    out = os.path.join(ASSETS, name + ".png")
    Image.merge("RGBA", (*d.split(), im.getchannel("A"))).save(out)
    return out


def p_frase(P):
    P.rect(0, 0, PW, PH, BO)
    fantasma(P, "ENERGIA", 700)
    a = duotone_rgba(recorte_atleta(), "atleta-duo")
    im = Image.open(a)
    justo = os.path.join(ASSETS, "atleta-justo.png")
    im.crop(im.getchannel("A").getbbox()).save(justo)
    iw, ih = Image.open(justo).size
    h = 1020
    w = iw * h / ih
    P.image(justo, 560 - w / 2, PH - h + 10, w, h, aceito=IA)
    head(P, 1060, 420, "Não é um dia\nde evento.", 96, W)
    head(P, 1060, 640, "É de agosto\na dezembro.", 96, W, "a dezembro.", CO)
    for linha in ("Não é um dia", "de evento.", "É de agosto", "a dezembro."):
        P.aceitar_sobreposicao("ENERGIA", linha, "palavra-fantasma atrás do texto, um tom acima do fundo (Spurs)")
    projecao(P)


def p_abertura(P):
    P.image(cena("c-abertura.png"), 0, 0, PW, PH, aceito=IA)
    # O telão saiu vermelho e vazio de propósito: o escudo e a marca entram aqui, com a grafia certa.
    eh = 92
    P.image(escudo(), 1466, 228, eh * ESC_R, eh)
    P.image(redbull("branco"), 1576, 258, 32 * RB_R, 32)
    esq = [(0, 0), (800, 0), (520, PH), (0, PH)]
    poly(P, esq, RD)
    P.path(P.poly_d([(800, 0), (520, PH)], closed=False), stroke=W, sw=3)
    P.text(96, 150, "01 · ANTES", BOLD, 15, W, tracking=180)
    head(P, 96, 300, "Abertura\napresentada\npor Red Bull.", 92, W)
    P.text(96, 640, "Lançamento da edição com as\n14 atléticas: sorteio das chaves,\napresentação dos uniformes e o\n"
                    "primeiro conteúdo da temporada\nnas contas das atléticas e do TUC.", MED, 25, W, leading=35)
    projecao(P)


SEDES = ["Ginásio do Taquaral", "Ginásio Rogê Ferreira", "Ginásio São José", "Clube Fonte São Paulo",
         "Ginásio Multidisciplinar da Unicamp"]


def p_rodada(P):
    P.rect(0, 0, PW, PH, K)
    foto = [(590, 0), (PW, 0), (PW, PH), (520, PH)]
    # A placa da esquerda saiu com o logo deformado atrás das jogadoras: a foto começa depois dela.
    q = Image.open(cena("c-quadra-rb.png")).convert("RGB")
    corte = os.path.join(ASSETS, "quadra-corte.jpg")
    q.crop((q.width - round(q.height * 1420 / PH), 0, q.width, q.height)).save(corte, quality=92)
    img = P.image(corte, 500, 0, 1420, PH, aceito=IA)
    mascarar([img], P, foto)
    P.path(P.poly_d([(590, 0), (520, PH)], closed=False), stroke=RD, sw=10)
    P.text(96, 150, "02 · DURANTE", BOLD, 15, CO, tracking=180)
    head(P, 96, 290, "Toda\nrodada,\nem todo\nginásio.", 76, W, "ginásio.", CO)
    P.text(96, 640, "A equipe da Red Bull nas sedes\ndo torneio, de agosto a\ndezembro: amostragem nos\nintervalos, a jogada da rodada\n"
                    "em vídeo e a marca na quadra,\nno placar e nos bancos.*", MED, 21, W, leading=29)
    P.text(96, 838, "GINÁSIOS DE 2026 (2027 A CONFIRMAR)", BOLD, 12, GR, tracking=120)
    for k, s in enumerate(SEDES):
        y = 878 + k * 36
        P.text(96, y, str(k + 1), COND, 28, CO)
        P.text(128, y, s.upper(), BOLD, 13, W, tracking=80)
    P.text(96, 1060, "* SUJEITO À APROVAÇÃO DA SMEL CAMPINAS E DOS ESPAÇOS.", BOLD, 11, GR, tracking=100)
    projecao(P)


def p_final(P):
    # Sem palavra-fantasma aqui: por cima da foto ela cobria os rostos (o Spurs a põe ATRÁS do atleta recortado).
    P.image(cena("c-final.png"), 0, 0, PW, PH, aceito=IA)
    base = [(0, 760), (PW, 640), (PW, PH), (0, PH)]
    poly(P, base, K)
    P.text(96, 860, "03 · AS FINAIS", BOLD, 15, CO, tracking=180)
    head(P, 96, 960, "A final é Red Bull.", 92, W, "Red Bull.", CO)
    P.text(1000, 860, "As finais no Ginásio Multidisciplinar da Unicamp\nviram o evento da marca: entrada das equipes,\n"
                      "DJ, premiação e o troféu entregue pela Red Bull.", MED, 25, W, leading=35)
    P.text(1000, 1010, "PROPOSTA SUJEITA À APROVAÇÃO DA ORGANIZAÇÃO, DA SMEL CAMPINAS E DA UNICAMP.", BOLD, 11, GR, tracking=100)
    eh = 120
    P.image(escudo(), 96, 120, eh * ESC_R, eh)
    projecao(P)


def p_medicao(P):
    P.rect(0, 0, PW, PH, CZ)
    poly(P, [(1700, 0), (PW, 0), (PW, PH), (1560, PH)], K)
    P.text(96, 130, "ENTREGAS E MEDIÇÃO", BOLD, 15, RD, tracking=180)
    head(P, 96, 260, "O que entregamos\ne como provamos.", 84, K, "e como provamos.", RD)
    linhas = [("Marca em todos os jogos", "jogos com a marca, por sede", "lista de jogos e fotos por rodada"),
              ("Amostragem", "latas entregues", "contagem da equipe Red Bull"),
              ("Público", "pessoas por rodada e por sede", "contagem pela organização"),
              ("Conteúdo", "peças e alcance (medido, não prometido)", "print do painel do TUC e das atléticas"),
              ("Relatório final", "tudo acima, item a item", "em até 30 dias depois da final")]
    xs = (96, 520, 1060)
    for x, c in zip(xs, ("ENTREGA", "INDICADOR", "FONTE")):
        P.text(x, 440, c, BOLD, 14, GR, tracking=180)
    for k, row in enumerate(linhas):
        y = 520 + k * 96
        P.rect(96, y - 52, 1400, 3, fill=RD if k == 0 else "#C9C9C9")
        P.text(xs[0], y, row[0], COND, 40, K, tracking=-10)
        P.text(xs[1], y - 4, row[1], MED, 25, K)
        P.text(xs[2], y - 4, row[2], MED, 25, K)


def p_investimento(P):
    esq, meio, dir = planos(vx=1180, topo=1700, dir_y=420)
    pintar_planos(P, (esq, meio, dir), (BO, K, RD), fio=False)
    P.text(96, 140, "INVESTIMENTO · EDIÇÃO 2027", BOLD, 16, W, tracking=220)
    head(P, 96, 240, "TUC apresentado por Red Bull", 64, W)
    t, _ = P.fit(90, 520, "R$ 250.000", 1200, COND, 300, W, tracking=-10)
    inclinar(t)
    P.text(96, 640, "INCLUI", BOLD, 15, CO, tracking=180)
    P.text(96, 690, "O nome em todo material · exclusividade da categoria bebida\nenergética (a confirmar com os patrocinadores atuais) ·\n"
                    "presença nas sedes em todas as rodadas · as finais como\nevento da marca · conteúdo com as atléticas · relatório final",
           MED, 24, W, leading=34)
    P.text(96, 900, "A RED BULL TRAZ", BOLD, 15, CO, tracking=180)
    P.text(96, 950, "Produto para amostragem, equipe de campo e a estrutura das ativações (DJ, área da marca).",
           MED, 24, W)
    P.text(96, 1010, "Decisão até 28/02/2027, para entrar no lançamento.", BOLD, 26, W)
    P.text(96, 1050, "ESPAÇOS PÚBLICOS SUJEITOS À APROVAÇÃO DA SMEL CAMPINAS E DA UNICAMP.", BOLD, 11, GR, tracking=100)


def p_convite(P):
    esq, meio, dir = planos(vx=860, topo=1460, dir_y=330)
    pintar_planos(P, (esq, meio, dir), (K, RD, BO))
    cruzar(P, 96, 420, "Vamos jogar", 200, [(esq, W), (meio, K), (dir, W)])
    cruzar(P, 96, 620, "juntos?", 200, [(esq, W), (meio, K), (dir, W)])
    P.text(96, 760, "Uma conversa com Vitor Freire,\norganizador do TUC desde a primeira edição.", MED, 28, W, leading=38)
    P.text(96, 880, "(11) 96695-5712", COND, 56, W, tracking=-10)
    assinatura(P, PW - 96 - (110 * ESC_R + 34 + 110 * 0.42 * RB_R), 900, 110)


PAGES = [p_capa, p_objetivo, p_porque, p_frase, p_abertura, p_rodada, p_final, p_medicao, p_investimento, p_convite]

if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--saida", default=os.path.join(KIT, "saida"))
    saida = a.parse_args().saida
    r = kit.montar("tuc-red-bull", PAGES, os.path.join(saida, "kit-tuc-red-bull.pdf"),
                   os.path.join(saida, "tuc-red-bull.vectorcraft"), vc=vc)
    vc.close()
    print(r["pdf"], r["segundos"], "s")
    for a in r["avisos_foto"]:
        if not a["aceito"]:
            print(f"aviso de foto: p{a['pagina']} {a['arquivo']} {a['ppi']} ppi")

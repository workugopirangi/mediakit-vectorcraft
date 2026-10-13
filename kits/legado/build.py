import sys, os, math, json, time
from vc import ex
from lib import *

T = "tratado/"


def p_capa(P):
    # Nike 06: título gigante no topo, faixa, foto P&B de ação, assinatura grande embaixo.
    P.rect(0, 0, PW, PH, K)
    P.image(prep(T + "c-capa-sabado.jpg", "capa", PW, PH, "bw", (0.5, 0.55)), 0, 0, PW, PH)
    P.rect(0, 0, PW, PH, K, opacity=52)
    P.rect(0, 0, PW, 380, K, opacity=45)
    gk = P.image(prep_cutout("real-goleiro-recorte.png", "goleiro"), 1010, 250, 830, 830)
    P.fit(64, 250, "COPA AME 2027", PW - 128, DISPLAY, 300, Y, tracking=-5)
    P.strip(300, Y)
    P.fit(64, 1000, "DEZ MIL ATLETAS.", 980, DISPLAY, 200, Y, tracking=-5)
    P.text(64, 1046, "E A FAMÍLIA INTEIRA NA BEIRA DO CAMPO.", HEAD, 26, W, tracking=20)
    P.image(prep_cutout("logo-ame-320-x3.png", "logo", mode="color"), 1700, 900, 160, 110)
    P.tag(1650, 360, "Imagem ilustrativa")


def p_manifesto(P):
    # Nike 19: painel cheio de cor com a frase, foto ao lado.
    P.rect(0, 0, PW, PH, Y)
    P.image(prep(T + "c-paifilho.jpg", "paifilho", 960, PH, "warm", (0.62, 0.5)), 960, 0, 960, PH)
    P.text(480, 250, "UM PAI\nCRIOU UM\nCAMPEONATO\nPARA O FILHO\nTER ONDE\nJOGAR.", HEAD, 124, K,
           tracking=-30, leading=116, justify="center")
    P.mark(400, 885, 160, K)
    P.text(120, 1010, "Em 2005, Walter Neves viu o filho Nicollas começar no futebol e criou a A.M.E. "
           "Vinte e um anos depois, é onde a região inteira aprende a jogar.", BODY, 19, K, width=720,
           leading=25)
    P.tag(1730, 50, "Imagem ilustrativa")


def p_campo(P):
    # Nike 09: página inteira de cor, título no topo, faixa, o número no lugar do swoosh gigante.
    P.rect(0, 0, PW, PH, Y)
    P.text(64, 140, "QUEM ESTÁ\nEM CAMPO.", HEAD, 104, K, tracking=-30, leading=96)
    P.strip(300, K)
    P.fit(40, 862, "10.000", PW - 80, DISPLAY, 600, K, tracking=-20)
    P.strip(918, K)
    P.text(64, 1036, "ATLETAS POR SEMESTRE.", HEAD, 76, K, tracking=-25)
    P.text(1300, 1000, "750 EQUIPES · 10.000 FAMÍLIAS ACOMPANHANDO\nINFORMADO PELO ORGANIZADOR · 2026",
           HEAD, 15, K, tracking=60, leading=22)



exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages2.py")).read())

if __name__ == "__main__":
    only = [int(a) for a in sys.argv[1:]] or list(range(len(PAGES)))
    ex("file.new", {"name": "copa-ame-nike", "width": PW, "height": PH, "units": "Pixels"})
    t0 = time.time()
    for n, i in enumerate(only):
        P = Page(n)
        PAGES[i](P)
        print("pagina", i + 1, "ok", round(time.time() - t0, 1), "s", flush=True)
    # padrão da skill: 1440×810 pt (1920×1080 px a 96 dpi). Desenha em px e reduz para 75 %.
    for n in range(len(only)):
        ox = n * GAP
        ex("select.allOnArtboard", {"artboard": n})
        ex("object.scale", {"sx": 75, "sy": 75, "origin": [ox, 0], "strokes": True, "corners": True})
        ex("select.none")
        ex("artboard.setProps", {"index": n, "width": 1440, "height": 810})
    out = os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    r = ex("document.exportPdf", {"path": os.path.join(out, "kit.pdf"), "preserveEditing": False})
    print(r)

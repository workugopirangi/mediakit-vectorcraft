#!/usr/bin/env python3
"""Provas do grafismos.py. Rodar: ~/.venvs/mediakit/bin/python test_grafismos.py (ou pytest).
Fontes: as do kit da Sprint (fontes-receitas, só leitura) quando a pasta existe na máquina; senão as mesmas famílias de
fontes-livres/ copiadas para uma pasta temporária. Logo: o da Sprint quando existe; senão um símbolo sintético.
As provas de navegador abrem o Chromium do Playwright (o mesmo do render.py). Não gasta cota de imagem."""
import io, json, math, re, shutil, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
import grafismos as g  # noqa: E402

PY = sys.executable
SPRINT = Path("/Users/ugopirangi/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/SPRINT UBATUBA RUN/MEDIAKIT/sprint-2027")
FAMILIAS = ["Kanit", "Bricolage Grotesque", "Fraunces", "Outfit", "Plus Jakarta Sans", "Hanken Grotesk"]
RECEITAS = {"r1": ("Kanit", "Outfit", "#D4A64A"), "r2": ("Bricolage Grotesque", "Plus Jakarta Sans", "#2067AA"),
            "r3": ("Fraunces", "Hanken Grotesk", "#D09050")}
MICRO = "SPRINT UBATUBA RUN · 14.03.2027 · UBATUBA/SP · 2ª EDIÇÃO"
SELO = "SPRINT UBATUBA RUN · 2ª EDIÇÃO · 2027 ·"
ASA = [0, 0, 0.477, 1]   # recorte do logo da Sprint: só a asa (as letras cortadas pela caixa saem inteiras)
_TMP = tempfile.mkdtemp(prefix="test-grafismos-")


def fontes_dir():
    kit = SPRINT / "fontes-receitas"
    if kit.is_dir():
        return kit
    d = Path(_TMP) / "fontes"
    if not d.exists():
        d.mkdir()
        for fam in FAMILIAS:
            for f in (AQUI.parent / "fontes-livres" / fam).glob("*.ttf"):
                shutil.copy(f, d / f.name)
    return d


def logo():
    real = SPRINT / "acervo" / "logo.png"
    if real.exists():
        return real
    p = Path(_TMP) / "logo.png"
    if not p.exists():
        im = Image.new("RGBA", (420, 240), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for k in range(5):
            d.polygon([(10 + k * 30, 220), (60 + k * 30, 20 + k * 25), (90 + k * 30, 30 + k * 25), (40 + k * 30, 225)], fill=(255, 255, 255, 255))
        d.rectangle([215, 100, 400, 160], fill=(255, 255, 255, 255))   # "nome escrito" do lado
        im.save(p)
    return p


def imagem_teste(nome="tela.png", w=540, h=1170, cor=(30, 90, 160), jpeg=False):
    """Captura de tela sintética (faixas e um disco amarelo no centro) para a moldura de celular."""
    p = Path(_TMP) / nome
    if not p.exists():
        im = Image.new("RGB", (w, h), cor)
        d = ImageDraw.Draw(im)
        for k in range(0, h, 90):
            d.rectangle([0, k, w, k + 45], fill=(40 + k % 200, 120, 200 - k % 150))
        d.ellipse([w // 2 - 100, h // 2 - 100, w // 2 + 100, h // 2 + 100], fill=(240, 200, 60))
        im.save(p, "JPEG" if jpeg else "PNG")
    return p


def ctx(receita="r1"):
    disp, corpo, marca = RECEITAS[receita]
    return {"fontes": {"display": disp, "peso_display": 800, "corpo": corpo},
            "paleta": {"marca": marca, "escuro": "#0E0D08", "papel": "#F6EEE2", "texto": "#FFFFFF", "apoio": "#2067AA"},
            "evento": {"nome": "Sprint Ubatuba Run", "data_inicio": "2027-03-14", "cidade": "Ubatuba", "uf": "SP", "edicao_numero": 2},
            "logo_png": str(logo()), "fontes_dir": str(fontes_dir())}


EXEMPLOS = [
    ("microtexto", {"texto": MICRO}),
    ("selo", {"texto": SELO, "recorte": ASA}),
    ("meio-tom-simbolo", {"recorte": ASA, "largura": 300}),
    ("pattern-simbolo", {"recorte": ASA, "lado": 200}),
    ("linha-percurso", {"curva": {"tipo": "orla"}}),
    ("fios-tecnicos", {"alvos": [{"x": 300, "y": 400, "rotulo": "Pórtico"}]}),
    ("moldura", {"etiqueta": "Cota ouro"}),
    ("etiqueta", {"texto": "Naming rights"}),
    ("numeral", {"texto": "2027"}),
    ("tipo-textura", {"texto": "Sprint"}),
    ("faixa-diagonal", {"texto": MICRO}),
    ("mosaico", {"recorte": ASA}),
    # composição: desenhos presos a algo da página (tinta, linhas e origem no contrato; references/08)
    ("linhas", {"largura": 400, "altura": 240, "espacamento": 16, "angulo": -45}),
    ("listras", {"largura": 480, "altura": 48}),
    ("colchetes", {"caixa": [100.4, 80, 320, 200], "braco": 36}),
    ("fio", {"pontos": [[20, 20], [200, 20], [200, 120]], "terminais": ["ponto", "seta"]}),
    ("regua", {"comprimento": 480, "passo": 12, "rotulos": {"inicio": 0, "passo": 5}}),
    ("divisoria", {"comprimento": 420}),
    ("grade-pontos", {"largura": 360, "altura": 200, "passo": 20}),
    ("circulos", {"raios": [30, 60, 90]}),
    ("setas", {"quantidade": 4}),
    ("estrelas", {"quantidade": 5}),
    ("campo", {"largura": 600}),
    ("placar", {"cabecalho": "Copa AME Sua Marca · 1ª rodada", "linhas": [
        {"data": "14.03 · 08h", "mandante": "Ubatuba FC", "placar": "2 x 1", "visitante": "Tubarões da Orla"},
        {"data": "14.03 · 10h", "mandante": "Costão EC", "placar": "0 x 0", "visitante": "Praia Grande"}]}),
    ("celular", {"largura": 240}),     # `imagem` entra em exemplo() (o caminho é de uma pasta temporária)
    ("mapa", {"aneis": [100, 300], "pontos": [{"nome": "Ubatuba", "lat": -23.4336, "lon": -45.0838, "destaque": True},
                                              {"nome": "São Paulo", "lat": -23.5505, "lon": -46.6333},
                                              {"nome": "Rio de Janeiro", "lat": -22.9068, "lon": -43.1729}]}),
    ("fio-borda", {"largura": 500}),
    ("pattern-borda", {"largura": 500}),
    # acabamento (Frente G): textura, borda, profundidade e tipografia expressiva
    ("hachura", {"largura": 400, "altura": 240}),
    ("malha", {"largura": 400, "altura": 240, "perspectiva": [[0.25, 0], [0.75, 0], [1, 1], [0, 1]]}),
    ("aneis", {"largura": 400, "altura": 240, "centro": [0, 1]}),
    ("pontos-radiais", {"largura": 400, "altura": 240}),
    ("cantoneira", {"caixa": [40, 30, 320, 200]}),
    ("moldura-dupla", {"largura": 400, "altura": 240, "cantos": "chanfro"}),
    ("regua-borda", {"comprimento": 900}),
    ("eco", {"texto_de": "evento", "tamanho": 90}),
    ("texto-curva", {"texto_de": "evento", "raio": 420}),
    ("ondas", {"largura": 400, "altura": 240}),
    ("curvas-nivel", {"largura": 400, "altura": 240}),
    ("fita", {"forma": "cruzada", "largura": 500, "altura": 260, "texto": "Cota ouro"}),
    ("carimbo", {"texto": SELO, "centro_texto": "2027", "falhas": 0.1}),
    ("numeral-eco", {"texto": "2027", "altura": 160}),
    ("meio-tom-foto", {"largura": 300}),                # `png` entra em exemplo() (pasta temporária)
]
NOVOS = ["linhas", "listras", "colchetes", "fio", "regua", "divisoria", "grade-pontos", "circulos", "setas", "estrelas", "campo",
         "placar", "celular", "mapa", "fio-borda", "pattern-borda"]
COM_TEXTO = ("regua", "placar", "mapa")
ACABAMENTO = ["hachura", "malha", "aneis", "pontos-radiais", "cantoneira", "moldura-dupla", "regua-borda", "eco", "texto-curva",
              "ondas", "curvas-nivel", "fita", "carimbo", "numeral-eco", "meio-tom-foto"]
COM_LETRA = ("regua-borda", "eco", "texto-curva", "fita", "carimbo", "numeral-eco")   # desenham letra: devolvem `linhas`
PRESOS = ("cantoneira", "moldura-dupla")               # presos a uma caixa da página: devolvem `origem`


def exemplo(tipo, prm):
    if tipo == "meio-tom-foto":
        return dict(prm, png=str(imagem_teste()))
    return dict(prm, imagem=str(imagem_teste())) if tipo == "celular" else prm


def raiz(svg):
    return ET.fromstring(svg)   # SVG gerado aqui mesmo (entrada confiável), não arquivo de fora


def test_contrato_de_saida_em_todos_os_tipos():
    assert sorted(t for t, _ in EXEMPLOS) == sorted(g.TIPOS), "exemplo faltando para algum tipo"
    base = {"svg", "w", "h", "texto", "fontes"}
    for tipo, prm in EXEMPLOS:
        r = g.gerar(tipo, exemplo(tipo, prm), ctx())
        if tipo in NOVOS or tipo in ACABAMENTO:
            assert base <= set(r) <= base | {"tinta", "linhas", "origem"}, (tipo, set(r))
        else:   # os tipos antigos continuam com as 5 chaves de sempre; só numeral e tipo-textura (a caixa tem margem) devolvem a tinta
            assert set(r) == base | ({"tinta"} if tipo in ("numeral", "tipo-textura") else set()), (tipo, set(r))
        assert isinstance(r["w"], int) and isinstance(r["h"], int) and r["w"] > 0 and r["h"] > 0, tipo
        el = raiz(r["svg"])
        assert el.get("viewBox") == f"0 0 {r['w']} {r['h']}" and el.get("width") == str(r["w"]) and el.get("height") == str(r["h"]), tipo
        assert el.get("data-grafismo") == tipo
        if r["texto"]:
            for linha in r["texto"].split("\n"):
                assert linha in r["svg"].replace("&amp;", "&"), (tipo, linha)   # o texto declarado está vivo no SVG
            assert r["fontes"], tipo
        print(f"  {tipo:17} {r['w']}x{r['h']} fontes={r['fontes']}")


def test_texto_vivo_nunca_desenho_de_letra():
    r = g.gerar("selo", {"texto": SELO, "centro": None}, ctx())
    cima, baixo = r["texto"].split("\n")
    assert r["svg"].count("<textPath") == 2 and f">{cima}</textPath>" in r["svg"] and f">{baixo}</textPath>" in r["svg"]
    r = g.gerar("microtexto", {"texto": MICRO}, ctx())
    assert r["svg"].count(MICRO) >= 2 and "<text " in r["svg"]
    assert "font-variant-ligatures:none" in r["svg"] and "white-space:pre" in r["svg"]


def test_glifo_ausente_nomeia_o_caractere():
    for tipo in ("microtexto", "selo", "numeral"):
        try:
            g.gerar(tipo, {"texto": "SPRINT ★ RUN"}, ctx())
        except ValueError as e:
            assert "★" in str(e) and "U+2605" in str(e) and ("Kanit" in str(e) or "Outfit" in str(e)), str(e)
            print("  ", tipo, "->", e)
            continue
        raise AssertionError(f"{tipo} aceitou glifo que a fonte não tem")


def test_deterministico():
    for tipo, prm in EXEMPLOS:
        prm = exemplo(tipo, prm)
        assert g.gerar(tipo, prm, ctx())["svg"] == g.gerar(tipo, prm, ctx())["svg"], tipo


def test_kerning_e_peso_entram_na_medida():
    f = g.fonte(ctx(), "display")
    assert (f.familia, f.peso, f.caminho.name) == ("Kanit", 800, "Kanit__800.ttf")
    assert f.largura("AV", 100) < f.largura("A", 100) + f.largura("V", 100) - 5     # par com kerning negativo
    assert abs(f.largura("ABC", 100, 2) - (f.largura("ABC", 100) + 6)) < 1e-9       # espaçamento depois de cada caractere
    fd = fontes_dir()
    assert g.resolver_fonte(fd, "Plus Jakarta Sans", 600)[1] == 700                # sem arquivo 600: o CSS sobe para 700
    assert g.resolver_fonte(fd, "Outfit", 400)[0].name == "Outfit.ttf"
    assert g.resolver_fonte(fd, "Hanken Grotesk", 450)[1] == 500


def test_meio_tom_tem_uma_cor_so():
    for prm in ({"recorte": ASA}, {"recorte": ASA, "modo": "led", "grade_fundo": True, "angulo": 45}):
        svg = g.gerar("meio-tom-simbolo", prm, ctx())["svg"]
        cores = set(re.findall(r'(?:fill|stroke)="(#[0-9A-Fa-f]{6})"', svg))
        assert cores == {"#D4A64A"}, cores
        assert svg.count("<circle") > 100


def test_pattern_simbolo_tem_toda_copia_que_encosta_no_tile():
    # conta feita aqui, sem a lógica do gerador: na meia-queda os centros ficam em (i+1/4, j+1/4) e (i+3/4, j+3/4) x lado;
    # todo centro a menos de meio símbolo do tile encosta nele e precisa estar desenhado (é a cópia que fecha a borda)
    T, esc = 200.0, 0.7
    r = g.gerar("pattern-simbolo", {"recorte": ASA, "lado": T, "escala": esc, "fase": [0, 0]}, ctx())
    usos = {(round(float(x), 2), round(float(y), 2)) for x, y in re.findall(r'translate\(([-\d.]+) ([-\d.]+)\) rotate', r["svg"])}
    meio = esc * T / 2
    for i in range(-3, 4):
        for j in range(-3, 4):
            for fx, fy in ((0.25, 0.25), (0.75, 0.75)):
                x, y = (i + fx) * T, (j + fy) * T
                if -meio < x < T + meio and -meio < y < T + meio:
                    assert (round(x, 2), round(y, 2)) in usos, (x, y)
    assert any(x < 0 for x, _ in usos) and any(x > T for x, _ in usos)   # há cópia dos dois lados da borda


def test_recorte_tira_letra_cortada_pela_caixa():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "l.png"
        im = Image.new("RGBA", (300, 100), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, 99, 99], fill=(255, 255, 255, 255))      # símbolo
        dr.rectangle([140, 30, 299, 70], fill=(255, 255, 255, 255))  # "letra" que a caixa corta ao meio
        im.save(p)
        _, cob = g._simbolo(p, [0, 0, 0.7, 1])
        assert cob.shape == (100, 100), cob.shape                    # só o símbolo; nada da letra cortada sobra


def _arco(svg, nome):
    m = re.search(rf'data-arco="{nome}" data-alvo="([\d.]+)"[^>]*font-size:([\d.]+)px;letter-spacing:([-\d.]+)px', svg)
    raio = float(re.search(rf'id="{nome}-[^"]+" d="M [\d.]+ [\d.]+ A ([\d.]+)', svg).group(1))
    inicio = float(re.search(rf'href="#{nome}-[^"]+" startOffset="([\d.]+)"', svg).group(1))
    return (*map(float, m.groups()), raio, inicio)    # alvo, tamanho, espaçamento, raio, início


def _rotacoes_pela_medida(f, texto, svg, nome):
    """Rotação de cada glifo de um arco calculada pela fonte e pela geometria do próprio path (ponto de partida e
    sentido do arco lidos do SVG), na convenção do getRotationOfChar: 0 grau = letra em pé na horizontal. Letra em pé
    = entre -90 e +90."""
    _, tam, ls, raio, pos = _arco(svg, nome)
    x0, y0, sentido = re.search(rf'id="{nome}-[^"]+" d="M ([\d.]+) ([\d.]+) A [\d.]+ [\d.]+ 0 0 ([01])', svg).groups()
    c = float(re.search(r'width="(\d+)"', svg).group(1)) / 2
    th0, passo = math.atan2(float(y0) - c, float(x0) - c), (1 if sentido == "1" else -1)
    rots = []
    for a in f.avancos(texto):
        a *= tam / f.upem
        th = th0 + passo * (pos + (a + ls) / 2) / raio                  # ângulo do meio do glifo no arco
        tx, ty = (-math.sin(th), math.cos(th)) if passo > 0 else (math.sin(th), -math.cos(th))
        rots.append(math.degrees(math.atan2(ty, tx)))
        pos += a + ls
    return rots


def test_selo_em_dois_arcos_pela_conta():
    for rid in RECEITAS:
        r = g.gerar("selo", {"texto": SELO, "centro": None}, ctx(rid))
        cima, baixo = r["texto"].split("\n")
        assert (cima, baixo) == ("SPRINT UBATUBA RUN", "2ª EDIÇÃO · 2027"), (cima, baixo)   # dividido nos ' · ', equilibrado
        f = g.fonte(ctx(rid), "display")
        for nome, txt in (("cima", cima), ("baixo", baixo)):
            alvo, tam, ls, raio, inicio = _arco(r["svg"], nome)
            assert abs(f.largura(txt, tam, ls) - alvo) < 0.1, (rid, nome)                 # cada arco fecha pela medida
        rots = _rotacoes_pela_medida(f, baixo, r["svg"], "baixo")
        assert all(-90 < x < 90 for x in rots), rots                                       # letras de baixo em pé
        seps = re.findall(r'data-arco="separador"[^>]*translate\(([\d.]+) ([\d.]+)\) rotate\((-?\d+)\)[^>]*>([^<]+)<', r["svg"])
        assert sorted(x[2] for x in seps) == ["-90", "90"] and all(abs(float(x[1]) - 160) < 0.01 for x in seps)   # 3h e 9h
        assert {x[3] for x in seps} == {"•"}                                                 # a fonte não tem estrela: ponto
    r = g.gerar("selo", {"texto": "SPRINT UBATUBA RUN", "texto_baixo": "UBATUBA · SP", "fonte": "corpo", "centro": None}, ctx("r2"))
    assert r["texto"] == "SPRINT UBATUBA RUN\nUBATUBA · SP" and ">★<" in r["svg"]          # Plus Jakarta Sans tem estrela
    try:
        g.gerar("selo", {"texto": SELO, "separador_anel": "★", "centro": None}, ctx())
    except ValueError as e:
        assert "★" in str(e)
    else:
        raise AssertionError("aceitou separador sem glifo na fonte")


# ---------------------------------------------------------------- no navegador
def test_chromium_selo_e_microtexto_fecham_na_medida():
    casos = []
    for rid in RECEITAS:
        for papel in ("display", "corpo"):
            r = g.gerar("microtexto", {"texto": MICRO, "largura": 1920, "fonte": papel, "tamanho": 18}, ctx(rid))
            casos.append((f"{rid} {papel} microtexto", 1920.0, r))
            r = g.gerar("selo", {"texto": SELO, "diametro": 340, "fonte": papel, "centro": None}, ctx(rid))
            casos.append((f"{rid} {papel} selo", None, r))
    medidas = g.medir_no_chromium([c[2]["svg"] for c in casos], fontes_dir())
    pior = 0.0
    for (nome, alvo, r), m in zip(casos, medidas):
        textos = [t for t in m["textos"] if t["arco"] in ("cima", "baixo")] if alvo is None else m["textos"][:1]
        assert textos, nome
        for t in textos:
            a = t["alvo"] if alvo is None else alvo          # selo: cada arco contra o comprimento que a medida calculou
            dif = t["comprimento"] - a
            pior = max(pior, abs(dif))
            print(f"  {nome:22} {t['arco'] or '':5} {t['familia']:22} {t['peso']}  alvo {a:9.3f}  Chromium {t['comprimento']:9.3f}  dif {dif:+.3f}")
            assert abs(dif) <= 1.0, (nome, a, t)
        for c in m["caminhos"]:                               # o arco que o navegador desenha é o meio círculo calculado
            raio = float(re.search(rf'id="{c["id"]}" d="M [\d.]+ [\d.]+ A ([\d.]+)', r["svg"]).group(1))
            assert abs(c["comprimento"] - math.pi * raio) <= 1.0, (nome, c)
    print(f"  pior diferença: {pior:.3f} px (tolerância 1 px)")


def _selo_no_chromium(svg, pasta, escala=3):
    """Rasteriza o selo (x escala), mede a rotação de cada glifo (getRotationOfChar) e imprime o PDF."""
    from playwright.sync_api import sync_playwright
    pasta.mkdir(parents=True, exist_ok=True)
    html = (f"<!doctype html><html><head><meta charset='utf-8'><style>{g.css_fontes(fontes_dir())}\n* {{ font-synthesis: none; }} "
            f"html, body {{ margin: 0; background: transparent; }} svg {{ display: block; }}</style></head><body>{svg}</body></html>")
    js = """() => Array.from(document.querySelectorAll('svg text')).map(t => ({arco: t.dataset.arco || null, texto: t.textContent,
        rot: Array.from({length: t.getNumberOfChars()}, (_, i) => t.getRotationOfChar(i))}))"""
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(device_scale_factor=escala)
        pg.set_content(html, wait_until="load"); pg.evaluate("document.fonts.ready")
        med = pg.evaluate(js)
        pg.locator("svg").first.screenshot(path=str(pasta / "selo.png"), omit_background=True)
        pg.pdf(path=str(pasta / "selo.pdf"), width="400px", height="400px", print_background=True)
        b.close()
    pdf = subprocess.run(["pdftotext", "-raw", str(pasta / "selo.pdf"), "-"], capture_output=True, text=True).stdout
    return med, pasta / "selo.png", pdf


def _le_metade_de_baixo(png, r_in, r_out, escala=3):
    """Recorta a metade de baixo do selo, desenrola o anel numa faixa reta (9h à esquerda, 3h à direita, centro do selo
    para cima: letra em pé continua em pé) e pede ao tesseract uma linha."""
    from scipy.ndimage import map_coordinates
    a = np.asarray(Image.open(png).convert("RGBA"), float)[..., 3] / 255
    c = a.shape[1] / 2
    baixo = a[int(round(c)):, :]
    n_col, n_lin = int(math.pi * (r_in + r_out) / 2 * escala), int((r_out - r_in) * escala)
    th, rr = np.meshgrid(np.linspace(math.pi, 0, n_col), np.linspace(r_in, r_out, n_lin) * escala)
    faixa = map_coordinates(baixo, [rr * np.sin(th), c + rr * np.cos(th)], order=1)
    im = Image.new("L", (n_col + 80, n_lin + 80), 255)
    im.paste(Image.fromarray((255 - faixa * 255).astype(np.uint8)), (40, 40))
    p = Path(png).with_name("faixa-de-baixo.png"); im.save(p)
    return subprocess.run(["tesseract", str(p), "stdout", "--psm", "7", "-l", "por+eng"], capture_output=True, text=True).stdout.strip()


def _em_ordem(lido, esperado):
    import unicodedata
    def norm(t):
        t = unicodedata.normalize("NFKD", t.upper())
        return re.sub(r"[^A-Z0-9]", "", "".join(ch for ch in t if not unicodedata.combining(ch)))
    partes = [norm(x) for x in re.split(r"[·\s]+", esperado) if norm(x) and len(norm(x)) > 1]
    pos = [norm(lido).find(x) for x in partes]
    return all(p >= 0 for p in pos) and pos == sorted(pos)


def test_chromium_selo_texto_de_baixo_em_pe():
    r = g.gerar("selo", {"texto": SELO, "diametro": 320, "centro": None, "contorno": False}, ctx())
    cima, baixo = r["texto"].split("\n")
    _, _, _, r_t, _ = _arco(r["svg"], "cima"); _, _, _, r_b, _ = _arco(r["svg"], "baixo")
    banda = r_b - r_t
    # controle: o mesmo selo com o arco de baixo das 3h para as 9h no sentido horário (o anel único de antes): letra de
    # cabeça para baixo. A prova tem de reprovar este, senão não prova nada.
    cx = 160
    virado = re.sub(r'(id="baixo-[^"]+" d=")[^"]+"', lambda m: f'{m.group(1)}M {cx + r_b} {cx} A {r_b} {r_b} 0 0 1 {cx - r_b} {cx}"', r["svg"])
    assert virado != r["svg"]
    with tempfile.TemporaryDirectory() as d:
        for rotulo, svg, deve in (("dois arcos", r["svg"], True), ("arco de baixo virado", virado, False)):
            med, png, pdf = _selo_no_chromium(svg, Path(d) / rotulo.replace(" ", "-"))
            lido = _le_metade_de_baixo(png, r_t - 0.35 * banda, r_b + 0.35 * banda)
            rots = [x for t in med if t["arco"] == "baixo" for x, ch in zip(t["rot"], t["texto"]) if ch.strip()]
            em_pe = bool(rots) and all(-90 < x < 90 for x in rots)
            print(f"   {rotulo:21} tesseract na metade de baixo: {lido!r}  em ordem: {_em_ordem(lido, baixo)}  "
                  f"rotação no Chromium: {min(rots):.1f} a {max(rots):.1f} graus")
            assert _em_ordem(lido, baixo) is deve and em_pe is deve, (rotulo, lido, rots)
            if deve:
                plano = re.sub(r"\s", "", pdf)
                assert re.sub(r"\s", "", cima) in plano and re.sub(r"\s", "", baixo) in plano, pdf   # pdftotext -raw acha os dois


def test_chromium_faixa_diagonal_tracking_normal_e_preenche():
    casos = [{"largura": 860, "altura": 300, "espessura": 70, "angulo": -10, "y": 0.5, "texto": MICRO},
             {"texto": MICRO}, {"angulo": -25, "espessura": 160, "texto": "Sprint"}]
    rs = [g.gerar("faixa-diagonal", c, ctx()) for c in casos]
    medidas = g.medir_no_chromium([r["svg"] for r in rs], fontes_dir())
    for c, r, m in zip(casos, rs, medidas):
        W, H = c.get("largura", 1920), c.get("altura", 1080)
        t0, t1 = g._segmento_visivel(W * c.get("x", 0.5), H * c.get("y", 0.62), c.get("angulo", -12), W, H)
        tam, ls = map(float, re.search(r'font-size:([\d.]+)px;letter-spacing:([-\d.]+)px', r["svg"]).groups())
        linha = re.search(r'>([^<]+)</text>', r["svg"]).group(1)
        comp = m["textos"][0]["comprimento"]
        print(f"   faixa {W}x{H} {c.get('angulo', -12)} graus: espaçamento {ls / tam:.4f} em, texto {comp:.3f} px, trecho visível {t1 - t0:.3f} px, "
              f"{linha.count('·')} separadores")
        assert ls / tam <= 0.12 + 1e-9, ls / tam                 # tracking normal, nunca esticado
        assert abs(comp - (t1 - t0)) <= 1.0, (comp, t1 - t0)     # preenche o trecho visível, folga de até 1 px
        assert linha.count("·") >= 1                             # o texto se repete com ' · ' 


def test_chromium_pattern_simbolo_sem_costura():
    with tempfile.TemporaryDirectory() as d:
        r = g.gerar("pattern-simbolo", {"recorte": ASA, "lado": 256}, ctx())     # parâmetros padrão (fase 'vazia')
        png = Path(d) / "tile.png"
        g.rasterizar(r["svg"], png)
        assert Image.open(png).size == (256, 256)
        a = np.asarray(Image.open(png).convert("RGBA"))[..., 3]
        assert (a > 0).mean() > 0.02          # o tile tem desenho (costura zero de tile vazio não prova nada)
        out = subprocess.run([PY, str(AQUI / "padrao.py"), "checar", str(png), "--limite", "0.1"], capture_output=True, text=True)
        print("  ", out.stdout.strip().split("|")[0], f" tinta nas bordas: col0 {(a[:, 0] > 0).sum()} col255 {(a[:, -1] > 0).sum()} "
              f"lin0 {(a[0] > 0).sum()} lin255 {(a[-1] > 0).sum()} px")
        assert out.returncode == 0, out.stdout


def test_chromium_pattern_simbolo_periodico_com_simbolo_cruzando_a_borda():
    # fase [0, 0] e símbolo grande: as cópias ATRAVESSAM as bordas. Prova direta: o tile é igual a cada quadrante de uma
    # área 2x2 desenhada com a mesma grade (o índice do checar não serve aqui: traço fino cruzando a borda dá 0,7 até em
    # tile perfeito, por isso o padrão escolhe a fase com a borda no vazio)
    T = 200
    prm = {"recorte": ASA, "lado": T, "escala": 0.7, "fase": [0, 0]}
    with tempfile.TemporaryDirectory() as d:
        g.rasterizar(g.gerar("pattern-simbolo", prm, ctx())["svg"], Path(d) / "t.png")
        g.rasterizar(g.gerar("pattern-simbolo", {**prm, "area": [2 * T, 2 * T]}, ctx())["svg"], Path(d) / "a.png")
        t = np.asarray(Image.open(Path(d) / "t.png").convert("RGBA"))[..., 3].astype(int)
        a = np.asarray(Image.open(Path(d) / "a.png").convert("RGBA"))[..., 3].astype(int)
    assert (t[:, 0] > 0).sum() > 8 and (t[:, -1] > 0).sum() > 8          # cruza a borda esquerda e a direita
    for qy in (0, T):
        for qx in (0, T):
            dif = np.abs(t - a[qy:qy + T, qx:qx + T])
            print(f"   quadrante ({qx},{qy}): diferença média {dif.mean():.3f}, máxima {dif.max()}")
            assert dif.mean() < 0.5 and dif.max() <= 128, (qx, qy, dif.mean(), dif.max())


# ================================================================= composição: desenhos presos a algo da página
# Cada prova mede o resultado por um caminho que não é o do gerador: contagem de componentes e corridas no raster que o
# Chromium desenha (alfa >= 128 = tinta, o mesmo critério do PNG), medida de texto pelo getComputedTextLength, fórmulas
# escritas aqui (haversine, geometria oficial do campo). O acento da página nas provas é branco puro: o alfa decide.
COR_PAGINA = "#FFFFFF"
JS_FONTES = """async () => {
  const pedidos = new Set();
  for (const t of document.querySelectorAll('svg text')) { const c = getComputedStyle(t); pedidos.add(`${c.fontWeight} 40px ${c.fontFamily}`); }
  for (const f of pedidos) { try { await document.fonts.load(f); } catch (e) {} }
  await document.fonts.ready;
}"""
_RASTERS = {}


def rasters(svgs, cor=COR_PAGINA, escala=1, familias=("Kanit", "Outfit")):
    """Rasteriza os SVGs no mesmo Chromium, fundo transparente, com as fontes do kit: lista de arrays RGBA. O mesmo svg não
    é rasterizado duas vezes."""
    faltam = [s for s in dict.fromkeys(svgs) if (s, cor, escala) not in _RASTERS]
    if faltam:
        from playwright.sync_api import sync_playwright
        css = g.css_fontes(fontes_dir(), set(familias))
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page(device_scale_factor=escala)
            pg.set_content(f"<!doctype html><html><head><meta charset='utf-8'><style>{css}\n* {{ font-synthesis: none; }} "
                           f"html, body {{ margin: 0; background: transparent; color: {cor}; }} svg {{ display: block; }}"
                           "</style></head><body></body></html>", wait_until="load")
            for s in faltam:
                pg.evaluate("(h) => { document.body.innerHTML = h; }", s)
                pg.evaluate(JS_FONTES)
                png = pg.locator("svg").first.screenshot(omit_background=True)
                _RASTERS[(s, cor, escala)] = np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"))
            b.close()
    return [_RASTERS[(s, cor, escala)] for s in svgs]


def raster(svg, **kw):
    return rasters([svg], **kw)[0]


def caixa_alfa(a, limiar=128):
    ys, xs = np.nonzero(a[..., 3] >= limiar)
    assert len(xs), "raster sem tinta"
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def corridas(v):
    """Corridas (início, fim) dos True de um vetor booleano: cada uma é um trecho contínuo de tinta."""
    d = np.diff(np.r_[0, np.asarray(v, int), 0])
    return list(zip(np.nonzero(d == 1)[0].tolist(), np.nonzero(d == -1)[0].tolist()))


def componentes(a, limiar=128):
    """(rótulos, n, centros (x, y) ponderados pelo alfa, em coordenadas contínuas do svg) das peças soltas de tinta."""
    from scipy import ndimage
    rot, n = ndimage.label(a[..., 3] >= limiar, structure=np.ones((3, 3)))
    cm = ndimage.center_of_mass(a[..., 3].astype(float), rot, range(1, n + 1)) if n else []
    return rot, n, [(x + 0.5, y + 0.5) for y, x in cm]


def tag(svg):
    return svg.replace("&amp;", "&")


def gerar_ok(tipo, prm, c=None):
    return g.gerar(tipo, prm, c or ctx())


def levanta(tipo, prm, trecho, c=None):
    try:
        g.gerar(tipo, prm, c or ctx())
    except ValueError as e:
        assert trecho in str(e), f"{tipo}: erro sem `{trecho}`: {e}"
        return str(e)
    raise AssertionError(f"{tipo} {prm} aceitou parâmetro inválido (esperava erro com `{trecho}`)")


# ---------------------------------------------------------------- contrato comum dos tipos novos
def test_novos_tipos_cumprem_o_contrato_de_composicao():
    proibidos = ("<filter", "filter=", "<mask", "mask=", "<pattern", "Gradient", "<foreignObject", "<style", "<script")
    for tipo, prm in EXEMPLOS:
        if tipo not in NOVOS:
            continue
        r = gerar_ok(tipo, exemplo(tipo, prm))
        svg = r["svg"]
        assert "currentColor" in svg, f"{tipo}: o acento da página tem de sair como currentColor"
        for x in proibidos:
            assert x not in svg, f"{tipo}: `{x}` rasteriza o PDF"
        assert svg.count("<image") == (1 if tipo == "celular" else 0), tipo           # imagem só na moldura do celular
        t = r["tinta"]
        assert len(t) == 4 and 0 <= t[0] < t[2] <= r["w"] + 1e-6 and 0 <= t[1] < t[3] <= r["h"] + 1e-6, (tipo, t, r["w"], r["h"])
        assert ("linhas" in r) == (tipo in COM_TEXTO), (tipo, r.keys())
        if "linhas" in r:
            assert set(r["linhas"]) == {"linha_base", "cap"} and r["linhas"]["cap"] < r["linhas"]["linha_base"], r["linhas"]
            assert t[1] - 0.6 <= r["linhas"]["cap"] and r["linhas"]["linha_base"] <= t[3] + 0.6, (tipo, r["linhas"], t)
        assert ("origem" in r) == (tipo in ("fio", "colchetes")), (tipo, r.keys())
        if "origem" in r:
            assert len(r["origem"]) == 2 and all(isinstance(v, int) for v in r["origem"])
        if tipo not in COM_TEXTO:
            assert "<text" not in svg, tipo                                            # só régua, placar e mapa têm texto
        print(f"  {tipo:14} tinta {t}  origem {r.get('origem')}  linhas {r.get('linhas')}")


def test_enum_do_schema_e_geradores_andam_juntos():
    """O enum de `elemento.tipo` e o de `constantes[].tipo` prometem só o que tem gerador (antes: `etiqueta` existia no
    código e faltava no enum; `fio-borda`, `pattern-borda` e `contorno-territorio` estavam no enum sem gerador)."""
    sch = json.loads((AQUI.parent / "schema" / "elementos.schema.json").read_text(encoding="utf-8"))
    por_ia = {"objeto", "ilustracao", "pictograma", "textura", "pattern", "adesivo"}        # gerados pelo Codex, não por código
    tipos = set(sch["definitions"]["elemento"]["properties"]["tipo"]["enum"])
    assert tipos - por_ia == set(g.TIPOS), f"sem gerador: {sorted(tipos - por_ia - set(g.TIPOS))}; sem enum: {sorted(set(g.TIPOS) - tipos)}"
    constantes = set(sch["definitions"]["sistema_elementos"]["properties"]["constantes"]["items"]["properties"]["tipo"]["enum"])
    assert constantes - {"grao"} <= set(g.TIPOS), f"constante sem gerador: {sorted(constantes - {'grao'} - set(g.TIPOS))}"


# ---------------------------------------------------------------- linhas
def test_linhas_o_numero_segue_o_espacamento_e_a_densidade():
    casos = [dict(largura=400, altura=300, espacamento=20, angulo=0), dict(largura=400, altura=300, espacamento=17, angulo=90),
             dict(largura=420, altura=260, espacamento=24, angulo=-45), dict(largura=420, altura=260, espacamento=19, angulo=30),
             dict(largura=420, altura=260, espacamento=16, angulo=0, densidade=0.5),
             dict(largura=420, altura=260, espacamento=16, angulo=-30, densidade=0.25),
             dict(largura=420, altura=260, espacamento=16, angulo=0, densidade=0.4)]
    rs = [gerar_ok("linhas", c) for c in casos]
    for c, r, a in zip(casos, rs, rasters([r["svg"] for r in rs])):
        t = math.radians(c["angulo"])
        extensao = c["largura"] * abs(math.sin(t)) + c["altura"] * abs(math.cos(t))       # da caixa, na perpendicular das linhas
        total = math.floor(extensao / c["espacamento"] + 1e-9)
        esperado = math.ceil(Fraction(str(c.get("densidade", 1))) * total)
        _, n, centros = componentes(a)
        print(f"   {c['angulo']:4}°, espaçamento {c['espacamento']}, densidade {c.get('densidade', 1)}: {total} linhas na grade, "
              f"{esperado} desenhadas, {n} no raster")
        assert n == esperado, (c, n, esperado)
        # distância medida entre linhas vizinhas desenhadas: o espaçamento (ou o múltiplo da densidade regular)
        normal = np.array([-math.sin(t), math.cos(t)])
        pos = sorted(float(np.dot(normal, ctr)) for ctr in centros)
        passo = np.diff(pos)
        # o centro de uma linha curta de canto, cortada pela caixa, anda até 0,3 px no raster (o limiar de alfa come a franja de
        # um lado só): a inclinação da reta ajustada a todas as posições é a medida firme (a geometria do svg dá 23,9999)
        mult = 1 if c.get("densidade", 1) == 1 else {Fraction(1, 2): 2, Fraction(1, 4): 4}.get(Fraction(str(c["densidade"])))
        if mult:
            ajuste = float(np.polyfit(range(len(pos)), pos, 1)[0])
            assert abs(ajuste - mult * c["espacamento"]) < 0.02 and np.allclose(passo, mult * c["espacamento"], atol=0.4), (c, passo, ajuste)
    # a grade é simétrica: a primeira linha horizontal fica a meio espaçamento do topo e a última a meio da base
    a = raster(gerar_ok("linhas", dict(largura=400, altura=300, espacamento=20))["svg"])
    _, n, centros = componentes(a)
    ys = sorted(y for _, y in centros)
    assert abs(ys[0] - 10) < 0.1 and abs(ys[-1] - 290) < 0.1, (ys[0], ys[-1])


def test_linhas_esmaecer_em_degraus_sem_gradiente():
    r = gerar_ok("linhas", dict(largura=400, altura=200, espacamento=20, espessura=2, esmaecer={"direcao": "dir", "passos": 4, "minimo": 0.2}))
    ops = sorted({float(v) for v in re.findall(r'stroke-opacity="([\d.]+)"', r["svg"])}) + [1.0]
    esperado = [1 - 0.8 * j / 3 for j in range(4)]
    assert np.allclose(sorted(ops), sorted(esperado), atol=0.001), (ops, esperado)
    a = raster(r["svg"])
    for j in range(4):                                       # o alfa de cada quarto da largura é o degrau declarado
        coluna = int(50 + 100 * j)
        alfa = a[..., 3][:, coluna].max() / 255
        assert abs(alfa - esperado[j]) < 0.02, (j, alfa, esperado[j])
    for x in ("Gradient", "<mask", "mask=", "<filter"):
        assert x not in r["svg"]
    # a tinta só conta o que passa de meia opacidade (alfa >= 128): os degraus 1,0 e 0,73; o 0,47 e o 0,2 ficam de fora
    caixa = caixa_alfa(a)
    assert abs(r["tinta"][2] - caixa[2]) <= 1.0 and abs(r["tinta"][2] - 200) <= 1.0, (r["tinta"], caixa)
    # inclinado: o degrau corta a linha no meio (o corte segue a direção, não o fim da linha)
    d = gerar_ok("linhas", dict(largura=400, altura=200, espacamento=22, angulo=-35, espessura=2, esmaecer={"direcao": "dir", "passos": 4}))
    al = raster(d["svg"])[..., 3]
    medias = [al[:, int(x0):int(x0 + 100)].max() / 255 for x0 in range(0, 400, 100)]
    assert all(medias[i] > medias[i + 1] for i in range(3)), medias


def test_linhas_recorte_e_erros():
    r = gerar_ok("linhas", dict(largura=400, altura=300, espacamento=20, angulo=-45, recorte=[50, 40, 200, 120]))
    caixa = caixa_alfa(raster(r["svg"]))
    assert caixa[0] >= 50 - 0.5 and caixa[1] >= 40 - 0.5 and caixa[2] <= 250 + 0.5 and caixa[3] <= 160 + 0.5, caixa      # tudo dentro do recorte
    assert caixa[0] <= 51 and caixa[1] <= 41 and caixa[2] >= 249 and caixa[3] >= 159, caixa                                # e rente a ele
    r = gerar_ok("linhas", dict(largura=400, altura=300, espacamento=20, recorte={"eixo": "x", "de": 100, "ate": 180}))
    caixa = caixa_alfa(raster(r["svg"]))
    assert caixa[0] >= 99.5 and caixa[2] <= 180.5 and caixa[2] - caixa[0] >= 79, caixa
    levanta("linhas", dict(espacamento=2, espessura=2), "espessura")
    levanta("linhas", dict(densidade=0), "densidade")
    levanta("linhas", dict(densidade=1.5), "densidade")
    levanta("linhas", dict(largura=50, altura=10, espacamento=40), "maior que a caixa")
    levanta("linhas", dict(recorte=[0, 0, 0, 10]), "recorte")
    levanta("linhas", dict(esmaecer={"direcao": "diagonal"}), "esmaecer.direcao")
    levanta("linhas", dict(esmaecer={"passos": 1}), "esmaecer.passos")


# ---------------------------------------------------------------- listras
def _amostra_pela_normal(a, centro, normal, extensao, passo=0.25):
    from scipy.ndimage import map_coordinates
    u = np.arange(-extensao, extensao, passo)
    xs, ys = centro[0] + u * normal[0] - 0.5, centro[1] + u * normal[1] - 0.5
    return u, np.stack([map_coordinates(a[..., c].astype(float), [ys, xs], order=1, mode="nearest") for c in range(4)], axis=1)


def test_listras_alternam_duas_cores_na_largura_certa():
    prm = dict(largura=400, altura=120, largura_listra=20, angulo=-45, cores=["marca", "#2067AA"])
    r = gerar_ok("listras", prm)
    a = raster(r["svg"])
    normal = (math.sqrt(0.5), math.sqrt(0.5))                                   # -45°: a normal das listras
    u, amostra = _amostra_pela_normal(a, (200, 60), normal, 60)
    assert amostra[:, 3].min() >= 254, "alfa abaixo do cheio na emenda: sobrou fio claro entre as listras"
    azul = amostra[:, 2] < 200                                                  # branco da página x azul (#2067AA: B = 170, R = 32)
    cortes = [u[i] for i in range(1, len(u)) if azul[i] != azul[i - 1]]
    larguras = np.diff(cortes)
    print(f"   larguras medidas na perpendicular: {np.round(larguras, 2)}")
    assert len(larguras) >= 4 and np.allclose(larguras, 20, atol=0.6), larguras
    # a segunda cor transparente deixa o vão vazio: o alfa alterna 255 e 0
    r = gerar_ok("listras", dict(largura=400, altura=120, largura_listra=20, angulo=-45, cores=["marca", "transparent"]))
    _, am = _amostra_pela_normal(raster(r["svg"]), (200, 60), normal, 60)
    assert am[:, 3].max() >= 254 and am[:, 3].min() <= 1
    cheio = am[:, 3] > 127
    corte = [i for i in range(1, len(cheio)) if cheio[i] != cheio[i - 1]]
    assert np.allclose(np.diff(corte) * 0.25, 20, atol=0.6), np.diff(corte) * 0.25
    assert "<rect" not in r["svg"]                                              # com um vão vazio não há base cobrindo a caixa
    # fase: o período é 2 x 20 = 40 px; deslocar 40 repete o desenho, deslocar 20 o inverte
    a0, a40, a20 = (raster(gerar_ok("listras", dict(prm, cores=["marca", "transparent"], fase=f))["svg"])[..., 3].astype(int) for f in (0, 40, 20))
    assert 0.4 < (a0 > 127).mean() < 0.6
    assert np.abs(a0 - a40).mean() < 2, np.abs(a0 - a40).mean()
    assert np.abs(a0 + a20 - 255).mean() < 6, "fase de meio período troca as listras cheias pelos vãos"
    levanta("listras", dict(cores=["marca"]), "exatamente 2 cores")
    levanta("listras", dict(cores=["transparent", "none"]), "transparentes")
    levanta("listras", dict(largura_listra=0), "largura_listra")


# ---------------------------------------------------------------- colchetes
def test_colchetes_encostam_na_caixa_da_pagina():
    caixa = [100.4, 80.2, 320.0, 200.0]
    r = gerar_ok("colchetes", dict(caixa=caixa, braco=36, espessura=4))
    ox, oy = r["origem"]
    a = raster(r["svg"])
    ink = caixa_alfa(a)
    pagina = [ink[0] + ox, ink[1] + oy, ink[2] + ox, ink[3] + oy]
    print(f"   caixa pedida {caixa[:2]} + {caixa[2:]}  tinta no raster, na página: {pagina}")
    assert abs(pagina[0] - caixa[0]) <= 1 and abs(pagina[1] - caixa[1]) <= 1, pagina
    assert abs(pagina[2] - (caixa[0] + caixa[2])) <= 1 and abs(pagina[3] - (caixa[1] + caixa[3])) <= 1, pagina
    t = r["tinta"]
    assert abs(t[0] + ox - caixa[0]) < 0.06 and abs(t[2] + ox - (caixa[0] + caixa[2])) < 0.06, (t, ox)       # a tinta declarada é a da caixa
    assert abs(t[1] + oy - caixa[1]) < 0.06 and abs(t[3] + oy - (caixa[1] + caixa[3])) < 0.06, (t, oy)
    # o braço corre 36 px ao longo do lado e o meio do lado fica vazio
    linha_topo = int(round(caixa[1] + 2 - oy))
    corrida = [c for c in corridas(a[..., 3][linha_topo] >= 128)]
    assert len(corrida) == 2, corrida
    assert abs((corrida[0][1] - corrida[0][0]) - 36) <= 1.5 and abs((corrida[1][1] - corrida[1][0]) - 36) <= 1.5, corrida
    # cantos escolhidos: só os dois pedidos têm tinta
    r2 = gerar_ok("colchetes", dict(caixa=caixa, braco=36, cantos=["sup-esq", "inf-dir"]))
    a2 = raster(r2["svg"])[..., 3] >= 128
    h, w = a2.shape
    assert a2[:50, :50].any() and a2[-50:, -50:].any() and not a2[:50, -50:].any() and not a2[-50:, :50].any()
    levanta("colchetes", dict(caixa=[0, 0, 100, 100], braco=60), "braços se encontrariam")
    levanta("colchetes", dict(caixa=[0, 0, 100, 100], braco=3, espessura=3), "quadrado")
    levanta("colchetes", dict(caixa=[0, 0, 100]), "caixa")
    levanta("colchetes", dict(caixa=[0, 0, 100, 100], cantos=["meio"]), "canto `meio`")


# ---------------------------------------------------------------- fio
def test_fio_terminais_na_ponta_exata_e_tracejado_que_fecha_a_conta():
    r = gerar_ok("fio", dict(pontos=[[50, 60], [250, 60], [250, 160]], espessura=3, terminais=["ponto", "seta"]))
    ox, oy = r["origem"]
    a = raster(r["svg"])[..., 3] >= 128
    def px(x, y):          # há tinta no pixel que cobre o ponto (x, y) da página? fora do svg não há
        i, j = int(math.floor(y - oy)), int(math.floor(x - ox))
        return 0 <= i < a.shape[0] and 0 <= j < a.shape[1] and bool(a[i, j])
    # ponto: disco de raio max(2,6 x espessura, 3,5) = 7,8 em volta do primeiro ponto (a linha só sai para a direita)
    assert px(50, 60 - 7) and not px(50, 60 - 9) and px(50 - 7, 60) and not px(50 - 9, 60)
    # seta: a ponta cai no último ponto, nada passa dela, e a base é mais larga que o fio
    assert px(250, 157) and not px(250, 161), "a ponta da seta tem de cair em (250, 160)"
    ys = np.nonzero(a.any(axis=1))[0]
    assert ys.max() + 1 + oy <= 160.6, f"o fio vaza pela ponta da seta: tinta até y = {ys.max() + 1 + oy}"
    largura_na_base = a[int(160 - 21 + 3 - oy)].sum()
    assert largura_na_base >= 14, f"base da seta com {largura_na_base} px"
    ink = caixa_alfa(raster(r["svg"]))
    for v, esperado in zip(ink, r["tinta"]):
        assert abs(v - esperado) <= 1.5, (ink, r["tinta"])
    assert abs(r["tinta"][0] + ox - (50 - 7.8)) < 0.15 and abs(r["tinta"][3] + oy - 160) < 0.15, (r["tinta"], r["origem"])
    # tracejado de [10, 6] numa reta de 300 px: 18 períodos de 16 mais 12 px (um traço inteiro de 10): 19 traços
    t = gerar_ok("fio", dict(pontos=[[50, 40], [350, 40]], espessura=3, tracejado=[10, 6]))
    at = raster(t["svg"])[..., 3] >= 128
    linha = at[int(round(40 - t["origem"][1] - 0.5))]
    runs = corridas(linha)
    assert len(runs) == 19 and all(abs((e - s) - 10) <= 1 for s, e in runs[:-1]), runs
    assert abs(runs[-1][1] + t["origem"][0] - 348) <= 1.2, (runs[-1], t["origem"])          # o último traço acaba em 288 + 10
    assert abs(t["tinta"][2] + t["origem"][0] - 348) < 0.15, t["tinta"]                       # a tinta declarada acompanha
    # a conta do tracejado, sem navegador: comprimento desenhado = períodos inteiros x traço + o pedaço do último período
    for L, (tr, va) in ((300, (10, 6)), (45, (10, 6)), (16, (10, 6)), (7, (10, 6)), (100, (3, 3))):
        partes = g._tracejar([(0, 0), (L, 0)], tr, va)
        desenhado = sum(math.hypot(b[0] - a_[0], b[1] - a_[1]) for p in partes for a_, b in zip(p, p[1:]))
        assert abs(desenhado - ((L // (tr + va)) * tr + min(tr, L % (tr + va)))) < 1e-6, (L, desenhado)
    # o traço dobra na quina sem se partir: L de 40 + 40 com traço de 30 e vão 5
    partes = g._tracejar([(0, 0), (40, 0), (40, 40)], 30, 5)
    assert partes[0] == [(0, 0), (30.0, 0.0)] and partes[1][0] == (35.0, 0.0) and (40.0, 0.0) in partes[1] and partes[1][-1] == (40.0, 25.0)
    levanta("fio", dict(pontos=[[0, 0]]), "pontos")
    levanta("fio", dict(pontos=[[5, 5], [5, 5]]), "mesmo lugar")
    levanta("fio", dict(pontos=[[0, 0], [100, 0]], terminais=["seta", "estrela"]), "terminais")
    levanta("fio", dict(pontos=[[0, 0], [8, 0]], terminais=["nenhum", "seta"]), "curto demais")
    levanta("fio", dict(pontos=[[0, 0], [100, 0]], tracejado=[0, 4]), "tracejado")


# ---------------------------------------------------------------- régua
def test_regua_marcas_pelo_passo_e_rotulos_vivos():
    r = gerar_ok("regua", dict(comprimento=480, passo=12, marca_maior_a_cada=5, rotulos={"inicio": 0, "passo": 5, "formato": "{n}"}))
    a = raster(r["svg"])[..., 3] >= 128
    # a marca menor tem 10 px e a maior 20: 5 px abaixo da linha de base vê todas as marcas; 15 px, só as maiores
    base_y = int(round(r["tinta"][1] + 0.75))
    n_marcas = 480 // 12 + 1
    n_maiores = len(range(0, n_marcas, 5))
    todas = corridas(a[base_y + 5])
    maiores = corridas(a[base_y + 15][: -2])
    assert len(todas) == n_marcas, (len(todas), n_marcas)
    assert len([c for c in maiores if c[1] - c[0] <= 4]) == n_maiores, (len(maiores), n_maiores)
    centros = [(s + e) / 2 for s, e in todas]
    assert np.allclose(np.diff(centros), 12, atol=0.35), np.diff(centros)
    assert r["texto"].split("\n") == [str(v) for v in range(0, 5 * n_maiores, 5)], r["texto"]
    assert r["fontes"] == ["Outfit"]
    # `linhas`: a linha de base e o cap dos rótulos batem com o raster (algarismos de Outfit: altura ~ cap)
    base, cap = r["linhas"]["linha_base"], r["linhas"]["cap"]
    abaixo_das_marcas = int(r["tinta"][1] + 0.75 + 20 + 2)                      # depois da ponta da marca maior
    ys = np.nonzero(a[abaixo_das_marcas:].any(axis=1))[0]
    inferior, topo = abaixo_das_marcas + ys.max() + 1, abaixo_das_marcas + ys.min()
    assert abs(inferior - base) <= 1.5, (inferior, base)
    assert abs(topo - cap) <= 2.0, (topo, cap)
    # texto vivo no PDF-friendly: <text>, na fonte do kit, com numerais tabulares
    assert r["svg"].count("<text") == n_maiores and "tabular-nums" in r["svg"] and "Outfit" in r["svg"]
    # medido no Chromium: o texto tem o comprimento que a fonte diz
    m = g.medir_no_chromium([r["svg"]], fontes_dir())[0]
    f = g.fonte(ctx(), "corpo", 600)
    for t, txt in zip(m["textos"], r["texto"].split("\n")):
        esperado = f.largura(txt, 14, round(0.06 * 14, 3), True)
        assert abs(t["comprimento"] - esperado) <= 1.0, (txt, t["comprimento"], esperado)
    # vertical, e rótulos dados à mão
    v = gerar_ok("regua", dict(comprimento=240, orientacao="vertical", passo=12, rotulos=["0", "5", "10", "15", "20"], lado="esq"))
    av = raster(v["svg"])[..., 3] >= 128
    assert v["w"] < v["h"] and av.sum() > 0 and v["texto"].count("\n") == 4
    assert v["linhas"]["cap"] < v["linhas"]["linha_base"] and abs(v["linhas"]["linha_base"] - (v["tinta"][3] - 0.0)) <= 8
    levanta("regua", dict(comprimento=100, rotulos=["a", "b"]), "marcas maiores")
    levanta("regua", dict(comprimento=100, rotulos=["★", "b", "c"], marca_maior_a_cada=2, passo=25), "★")
    levanta("regua", dict(orientacao="diagonal"), "orientacao")
    levanta("regua", dict(lado="dir"), "lado")


# ---------------------------------------------------------------- divisória
def test_divisoria_ornamento_no_meio_ou_nas_pontas():
    r = gerar_ok("divisoria", dict(comprimento=420, espessura=2, tamanho=12))
    a = raster(r["svg"])[..., 3] >= 128
    linha = a[a.shape[0] // 2]
    runs = corridas(linha)
    assert len(runs) == 3, runs                                              # fio, losango, fio
    vaos = [runs[1][0] - runs[0][1], runs[2][0] - runs[1][1]]
    esperado = 0.9 * 12
    assert all(abs(v - esperado) <= 1.5 for v in vaos), (vaos, esperado)
    assert abs((runs[1][1] - runs[1][0]) - 12) <= 1.5 and "<polygon" in r["svg"] and "<circle" not in r["svg"]
    centro = (runs[1][0] + runs[1][1]) / 2
    assert abs(centro - r["w"] / 2) <= 0.6, (centro, r["w"])
    p = gerar_ok("divisoria", dict(comprimento=420, espessura=2, tamanho=12, ornamento="ponto", posicao="pontas"))
    ap = raster(p["svg"])[..., 3] >= 128
    assert len(corridas(ap[ap.shape[0] // 2])) == 1, "nas pontas o fio chega nos dois pontos: uma tinta contínua"
    col_ponta = ap[:, 1 + 6]                                                 # centro do ponto da esquerda
    assert abs(col_ponta.sum() - 12) <= 1.5, col_ponta.sum()
    assert ap[:, ap.shape[1] // 2].sum() <= 3, "no meio só o fio"
    assert "<circle" in p["svg"] and abs(p["tinta"][2] - p["tinta"][0] - 420) < 0.2
    v = gerar_ok("divisoria", dict(comprimento=300, orientacao="vertical"))
    assert v["h"] > v["w"] and v["h"] >= 300
    levanta("divisoria", dict(comprimento=20, tamanho=14), "curto demais")
    levanta("divisoria", dict(ornamento="estrela"), "ornamento")


# ---------------------------------------------------------------- grade de pontos
def test_grade_de_pontos_de_ponta_a_ponta_e_esmaece_em_degraus():
    W, H, passo, raio = 360, 200, 20, 2
    r = gerar_ok("grade-pontos", dict(largura=W, altura=H, passo=passo, raio=raio))
    nx, ny = round((W - 2 * raio) / passo) + 1, round((H - 2 * raio) / passo) + 1          # 19 colunas e 11 linhas
    el = raiz(r["svg"])
    circulos = [c for c in el.iter() if c.tag.endswith("circle")]
    assert len(circulos) == nx * ny == 209, len(circulos)
    assert {c.get("r") for c in circulos} == {"2"}
    xs = sorted({round(float(c.get("cx")), 3) for c in circulos})
    ys = sorted({round(float(c.get("cy")), 3) for c in circulos})
    assert xs[0] == raio and xs[-1] == W - raio and np.allclose(np.diff(xs), (W - 2 * raio) / (nx - 1), atol=0.01), (xs[:2], xs[-1])      # ponta a ponta
    assert ys[0] == raio and ys[-1] == H - raio and np.allclose(np.diff(ys), (H - 2 * raio) / (ny - 1), atol=0.01)
    assert abs(np.diff(xs)[0] / passo - 1) < 0.05 and abs(np.diff(ys)[0] / passo - 1) < 0.05, "o passo real fica a menos de 5% do pedido"
    assert r["tinta"] == [0.0, 0.0, 360.0, 200.0], "os pontos das bordas encostam: a tinta é a caixa"
    _, n, _ = componentes(raster(r["svg"]))
    assert n == nx * ny, n
    e = gerar_ok("grade-pontos", dict(largura=360, altura=200, passo=20, raio=2, esmaecer={"direcao": "baixo", "passos": 5, "minimo": 0.1}))
    grupos = [g_ for g_ in raiz(e["svg"]).iter() if g_.tag.endswith("g") and g_.get("fill-opacity")]
    ops = sorted({float(g_.get("fill-opacity")) for g_ in grupos}, reverse=True)
    assert len(ops) == 4 and abs(ops[0] - 0.775) < 0.01 and abs(ops[-1] - 0.1) < 0.01, ops          # + o degrau opaco, sem atributo
    a = raster(e["svg"])[..., 3]
    linhas = [a[int(2 + (200 - 4) / 10 * j)].max() / 255 for j in range(11)]
    assert all(linhas[i] >= linhas[i + 1] - 0.01 for i in range(10)) and linhas[0] > 0.95 and linhas[-1] < 0.2, np.round(linhas, 2)
    assert e["tinta"][3] < 200, "a tinta só conta o que passa de meia opacidade"
    levanta("grade-pontos", dict(passo=10, raio=6), "raio")
    levanta("grade-pontos", dict(largura=2, altura=10), "menor que um ponto")
    levanta("grade-pontos", dict(largura=1920, altura=1080, passo=10), "aumente o passo")


# ---------------------------------------------------------------- círculos
def test_circulos_raios_e_arcos_pela_medida_do_raster():
    raios = [30, 60, 90, 120]
    r = gerar_ok("circulos", dict(raios=raios, espessura=3))
    a = raster(r["svg"])[..., 3] >= 128
    c = r["w"] / 2
    linha = a[int(c)]
    runs = corridas(linha)
    centros = sorted(abs((s + e) / 2 - c) for s, e in runs)
    assert len(runs) == 8 and np.allclose(centros[0::2], raios, atol=0.6) and np.allclose(centros[1::2], raios, atol=0.6), (runs, centros)
    assert abs(r["tinta"][2] - r["tinta"][0] - (2 * 120 + 3)) < 0.2
    # arco: só o setor pedido (graus, sentido horário, 0 = 3 h)
    ar = gerar_ok("circulos", dict(raios=[40, 80], angulo_ini=-50, angulo_fim=50, espessura=3))
    aa = raster(ar["svg"])[..., 3] >= 128
    ys, xs = np.nonzero(aa)
    c = ar["w"] / 2
    angulos = np.degrees(np.arctan2(ys + 0.5 - c, xs + 0.5 - c))
    assert angulos.max() <= 50 + math.degrees(3 / 2 / 40) + 1.5 and angulos.min() >= -50 - math.degrees(3 / 2 / 40) - 1.5, (angulos.min(), angulos.max())
    assert angulos.max() >= 47 and angulos.min() <= -47, "o arco tem de ir até os ângulos pedidos"
    assert all(abs(a_ - b) <= 1.3 for a_, b in zip(caixa_alfa(raster(ar["svg"])), ar["tinta"]))
    # raios em progressão
    p = gerar_ok("circulos", dict(raio_max=100, quantidade=4))
    assert sorted(float(x.get("r")) for x in raiz(p["svg"]).iter() if x.tag.endswith("circle")) == [25, 50, 75, 100]
    levanta("circulos", dict(raios=[]), "raios")
    levanta("circulos", dict(raios=[-5]), "raios")
    levanta("circulos", dict(raios=[10], angulo_ini=10, angulo_fim=5), "angulo_ini")
    levanta("circulos", dict(raios=[1], espessura=3), "metade da espessura")


# ---------------------------------------------------------------- setas
def test_setas_quantidade_direcao_e_passo():
    for direcao, eixo in (("dir", 0), ("esq", 0), ("baixo", 1), ("cima", 1)):
        r = gerar_ok("setas", dict(quantidade=4, tamanho=40, passo=34, espessura=5, direcao=direcao))
        a = raster(r["svg"])
        _, n, centros = componentes(a)
        assert n == 4, (direcao, n)
        pos = sorted(c[eixo] for c in centros)
        assert np.allclose(np.diff(pos), 34, atol=0.5), (direcao, np.diff(pos))
        al = a[..., 3] >= 128
        # a ponta é a extremidade na direção: lá o desenho está centrado no outro eixo
        if direcao == "dir":
            ponta = al[:, -4:].any(axis=1)
        elif direcao == "esq":
            ponta = al[:, :4].any(axis=1)
        elif direcao == "baixo":
            ponta = al[-4:].any(axis=0)
        else:
            ponta = al[:4].any(axis=0)
        idx = np.nonzero(ponta)[0]
        meio = (idx.min() + idx.max() + 1) / 2
        outro = r["h"] if eixo == 0 else r["w"]
        assert abs(meio - outro / 2) <= 1.5, (direcao, meio, outro)
    assert gerar_ok("setas", dict(quantidade=6))["svg"].count("M") == 6
    levanta("setas", dict(direcao="diagonal"), "direcao")
    levanta("setas", dict(quantidade=0), "quantidade")


# ---------------------------------------------------------------- estrelas
def test_estrelas_regulares_em_linha_e_em_arco():
    r = gerar_ok("estrelas", dict(quantidade=5, tamanho=40, passo=56))
    el = raiz(r["svg"])
    polis = [x for x in el.iter() if x.tag.endswith("polygon")]
    assert len(polis) == 5 and _componentes_n(r) == 5

    def vertices(pol):
        return [tuple(float(v) for v in par.split(",")) for par in pol.get("points").split()]
    for pol in polis:
        v = np.array(vertices(pol))
        assert len(v) == 10
        centro = v.mean(axis=0)
        raios_ = np.hypot(*(v - centro).T)
        assert np.allclose(raios_[0::2], raios_[0::2].mean(), atol=0.01) and np.allclose(raios_[1::2] / raios_[0::2], 0.382, atol=0.002)
        ang = np.degrees(np.arctan2(*(v[0::2] - centro).T[::-1]))
        assert np.allclose(np.diff(np.sort(ang)) % 360, 72, atol=0.1) or np.allclose(sorted(np.diff(np.r_[np.sort(ang), np.sort(ang)[0] + 360])), [72] * 5, atol=0.1)
        assert abs(raios_[0::2].mean() - 20) < 0.05 and v[0][1] < centro[1], "tamanho = diâmetro ponta a ponta; ponta para cima"
    cs = np.array([np.mean(vertices(pol), axis=0) for pol in polis])
    assert np.allclose(np.diff(cs[:, 0]), 56, atol=0.01) and np.allclose(cs[:, 1], cs[0, 1])
    # arco de 120 graus: os centros ficam numa circunferência de raio passo x (n-1) / ângulo, e a ponta de cima olha para fora
    a = gerar_ok("estrelas", dict(quantidade=7, tamanho=30, passo=44, arco=120))
    pa = [x for x in raiz(a["svg"]).iter() if x.tag.endswith("polygon")]
    cs = np.array([np.mean(vertices(pol), axis=0) for pol in pa])
    Ra = 44 * 6 / math.radians(120)
    ajuste = np.linalg.lstsq(np.c_[2 * cs, np.ones(len(cs))], (cs ** 2).sum(axis=1), rcond=None)[0]
    c0 = ajuste[:2]
    raio_ajustado = math.sqrt(ajuste[2] + c0 @ c0)
    assert abs(raio_ajustado - Ra) < 0.05, (raio_ajustado, Ra)
    ang = np.degrees(np.arctan2(cs[:, 1] - c0[1], cs[:, 0] - c0[0]))
    assert np.allclose(np.diff(ang), 120 / 6, atol=0.05), np.diff(ang)
    for pol, centro in zip(pa, cs):
        topo = np.array(vertices(pol)[0]) - centro
        radial = centro - c0
        assert abs(topo @ radial / np.hypot(*topo) / np.hypot(*radial) - 1) < 1e-3, "a ponta de cima aponta para fora do arco"
    # contorno: sem preenchimento, junta redonda, a tinta passa do vértice em meia espessura
    c = gerar_ok("estrelas", dict(quantidade=2, estilo="contorno", espessura=3, tamanho=50))
    assert 'fill="none"' in c["svg"] and "round" in c["svg"]
    assert all(abs(v - e) <= 1.5 for v, e in zip(caixa_alfa(raster(c["svg"])), c["tinta"]))
    levanta("estrelas", dict(arco=200), "arco")
    levanta("estrelas", dict(razao=1.2), "razao")
    levanta("estrelas", dict(estilo="vazado"), "estilo")


def _componentes_n(r):
    return componentes(raster(r["svg"]))[1]


# ---------------------------------------------------------------- campo
def _partes(svg, nome):
    return [(e.tag.split("}")[1], dict(e.attrib)) for e in raiz(svg).iter() if e.get("data-parte") == nome]


def _arco_d(d):
    m = re.match(r"M([-\d.]+) ([-\d.]+)A([-\d.]+) ([-\d.]+) 0 (\d) (\d) ([-\d.]+) ([-\d.]+)$", d)
    x0, y0, rx, ry, grande, sentido, x1, y1 = m.groups()
    return float(x0), float(y0), float(rx), int(grande), int(sentido), float(x1), float(y1)


def test_campo_de_futebol_na_escala_oficial():
    W, esp = 840, 2.0
    r = gerar_ok("campo", dict(esporte="futebol", largura=W))
    esc = (W - esp) / 105                               # `largura` é a caixa; a metade da espessura das linhas de borda entra nela
    assert r["w"] == W and r["h"] == math.ceil(esp + 68 * esc), (r["w"], r["h"])
    cx, cy = 1 + 52.5 * esc, 1 + 34 * esc
    (_, c), = _partes(r["svg"], "circulo-central")
    assert abs(float(c["r"]) - 9.15 * esc) < 0.01 and abs(float(c["cx"]) - cx) < 0.01 and abs(float(c["cy"]) - cy) < 0.01, c
    for lado, (_, a) in zip((0, 1), _partes(r["svg"], "area")):
        assert abs(float(a["width"]) - 16.5 * esc) < 0.01 and abs(float(a["height"]) - 40.32 * esc) < 0.01, a
        assert abs(float(a["y"]) - (1 + (34 - 20.16) * esc)) < 0.01
        assert abs(float(a["x"]) - (1 if lado == 0 else 1 + (105 - 16.5) * esc)) < 0.01
    for lado, (_, a) in zip((0, 1), _partes(r["svg"], "area-pequena")):
        assert abs(float(a["width"]) - 5.5 * esc) < 0.01 and abs(float(a["height"]) - 18.32 * esc) < 0.01, a
    marcas = _partes(r["svg"], "marca-penalti")
    assert sorted(round(float(m["cx"]), 2) for _, m in marcas) == [round(1 + 11 * esc, 2), round(1 + 94 * esc, 2)]
    # o arco da área é de 9,15 m em volta da marca e só aparece fora da área: acaba exatamente na linha da área (53,05 graus)
    arcos = _partes(r["svg"], "arco-da-area")
    for lado, (_, a) in enumerate(arcos):
        x0, y0, rx, grande, sentido, x1, y1 = _arco_d(a["d"])
        assert abs(rx - 9.15 * esc) < 0.01 and grande == 0 and sentido == 1
        linha_da_area = 1 + 16.5 * esc if lado == 0 else 1 + (105 - 16.5) * esc
        assert abs(x0 - linha_da_area) < 0.01 and abs(x1 - linha_da_area) < 0.01, (x0, x1, linha_da_area)
        meia_corda = 9.15 * esc * math.sin(math.acos(5.5 / 9.15))
        assert abs(abs(y1 - y0) / 2 - meia_corda) < 0.02 and abs((y0 + y1) / 2 - cy) < 0.01
    assert len(_partes(r["svg"], "arco-de-canto")) == 4 and all(abs(_arco_d(a["d"])[2] - 1 * esc) < 0.01 for _, a in _partes(r["svg"], "arco-de-canto"))
    assert abs(r["tinta"][2] - W) < 0.01 and abs(r["tinta"][3] - (esp + 68 * esc)) < 0.1 and r["tinta"][0] == r["tinta"][1] == 0
    # no raster: o círculo central tem 9,15 m x escala de raio e as duas áreas ficam em x = 16,5 m das linhas de fundo
    a = raster(r["svg"])[..., 3] >= 128
    linha = a[int(round(cy - 0.5))]
    centros = [(s + e) / 2 for s, e in corridas(linha)]
    raio_medido = sorted(abs(x - cx) for x in centros if 3 < abs(x - cx) < 15 * esc)
    assert len(raio_medido) == 2 and all(abs(v - 9.15 * esc) < 0.8 for v in raio_medido), (raio_medido, 9.15 * esc)
    print(f"   escala {esc:.4f} px/m: círculo central de {9.15 * esc:.2f} px (raster: {raio_medido}), área {16.5 * esc:.1f} x {40.32 * esc:.1f} px")
    # `altura` em vez de `largura`: a escala segue a outra medida e a proporção do campo se mantém
    h = gerar_ok("campo", dict(esporte="futebol", altura=400))
    assert h["h"] == 400 and abs((h["w"] - esp) / (h["h"] - esp) - 105 / 68) < 0.005, (h["w"], h["h"])
    # as duas medidas: a maior escala que cabe nas duas (500 x 300 num campo de 105 x 68: a altura limita)
    ambos = gerar_ok("campo", dict(esporte="futebol", largura=500, altura=300))["tinta"]
    assert ambos[3] - ambos[1] <= 300.5 and ambos[2] - ambos[0] <= 500.5 and abs((ambos[3] - ambos[1]) - 300) <= 0.5, ambos
    levanta("campo", dict(esporte="golfe"), "esporte")
    levanta("campo", dict(recorte="meia-lua"), "recorte")
    levanta("campo", dict(largura=15), "pequena demais")
    # girado: a caixa cresce para conter o campo e a tinta é a mesma (área de tinta preservada, a menos do antialiasing)
    g0 = gerar_ok("campo", dict(esporte="futebol", largura=420))
    g1 = gerar_ok("campo", dict(esporte="futebol", largura=420, angulo=-12))
    assert g1["h"] > g0["h"] * 0.9 and abs((g1["tinta"][2] - g1["tinta"][0]) - 420) <= 0.5, "a medida é a da tinta: o campo girado mede 420 de ponta a ponta"
    esc = lambda r: float(_partes(r["svg"], "circulo-central")[0][1]["r"]) / 9.15      # noqa: E731
    n0, n1 = (raster(g0["svg"])[..., 3] >= 128).sum(), (raster(g1["svg"])[..., 3] >= 128).sum()
    # a tinta é comprimento de linha x espessura (fixa): proporcional à escala. Girar não muda o que é desenhado, só o que cabe em 420
    assert abs((n1 / n0) / (esc(g1) / esc(g0)) - 1) < 0.06, (n0, n1, esc(g0), esc(g1))


def test_campo_futsal_pista_e_recortes():
    W, esp = 800, 2.0
    f = gerar_ok("campo", dict(esporte="futsal", largura=W))
    esc = (W - esp) / 40
    (_, c), = _partes(f["svg"], "circulo-central")
    assert abs(float(c["r"]) - 3 * esc) < 0.01, c
    areas = _partes(f["svg"], "area")                                   # quatro quartos de círculo de 6 m e duas retas de 3 m
    arcos = [x for t, x in areas if t == "path"]
    retas = [x for t, x in areas if t == "line"]
    assert len(arcos) == 4 and len(retas) == 2
    assert all(abs(_arco_d(x["d"])[2] - 6 * esc) < 0.01 for x in arcos)
    assert all(abs(abs(float(x["y2"]) - float(x["y1"])) - 3 * esc) < 0.01 for x in retas)
    assert sorted(round((float(x["x1"]) - 1) / esc, 3) for x in retas) == [6.0, 34.0]
    assert sorted(round((float(m["cx"]) - 1) / esc, 3) for _, m in _partes(f["svg"], "marca-penalti")) == [6.0, 34.0]
    assert sorted(round((float(m["cx"]) - 1) / esc, 3) for _, m in _partes(f["svg"], "segunda-marca")) == [10.0, 30.0]
    # pista: 9 linhas (8 raias) de 1,22 m; na reta de cima, de cima para o meio, o raster conta 9 traços espaçados 1,22 x escala
    p = gerar_ok("campo", dict(esporte="pista", largura=1000))
    assert len(_partes(p["svg"], "raia")) == 9 and len(_partes(p["svg"], "chegada")) == 1
    esc_p = (1000 - 2) / (84.39 + 2 * (36.5 + 8 * 1.22))
    ap = raster(p["svg"])[..., 3] >= 128
    coluna = ap[: ap.shape[0] // 2, ap.shape[1] // 2]
    runs = corridas(coluna)
    centros = [(s + e) / 2 for s, e in runs]
    assert len(runs) == 9 and np.allclose(np.diff(centros), 1.22 * esc_p, atol=0.5), (len(runs), np.diff(centros), 1.22 * esc_p)
    # recortes: a janela certa de cada um, e o que a janela corta sai rente à borda
    meio = gerar_ok("campo", dict(esporte="futebol", recorte="meio", largura=420))
    esc_m = (420 - 2) / 52.5
    assert meio["h"] == math.ceil(2 + 68 * esc_m) and "clip-path" in meio["svg"]
    am = raster(meio["svg"])[..., 3] >= 128
    assert am[:, -1].any() and am[:, -2].any() and not am[:, 0].all(), "o meio-campo é a borda da direita; o gol, a da esquerda"
    assert am[int(meio["h"] / 2), -2], "o meio de campo cai inteiro na borda direita"
    # `largura` é a medida da TINTA: no recorte do círculo, o anel mede 300 (e a janela de 24 m, mais)
    circulo = gerar_ok("campo", dict(esporte="futebol", recorte="circulo", largura=300))
    (_, cr), = _partes(circulo["svg"], "circulo-central")
    esc_c = float(cr["r"]) / 9.15
    assert abs(2 * float(cr["r"]) + 2.0 - 300) <= 0.5 and abs(circulo["w"] - 24 * esc_c) <= 1.0, (cr["r"], circulo["w"], 24 * esc_c)
    assert abs((circulo["tinta"][2] - circulo["tinta"][0]) - 300) <= 0.5
    ac = raster(circulo["svg"])[..., 3] >= 128
    cc = circulo["w"] // 2
    ys, xs = np.nonzero(ac)
    assert abs((xs.max() + 1 - xs.min()) - 300) <= 1.5 and abs((xs.min() + xs.max() + 1) / 2 - circulo["w"] / 2) <= 1.0, (xs.min(), xs.max())
    assert ac[0, cc - 1:cc + 1].any() and ac[-1, cc - 1:cc + 1].any(), "o meio-campo atravessa a janela de cima a baixo"
    canto = gerar_ok("campo", dict(esporte="futebol", recorte="canto", largura=440))
    assert len(_partes(canto["svg"], "arco-de-canto")) == 4 and "clip-path" in canto["svg"]
    area = gerar_ok("campo", dict(esporte="futebol", recorte="area", largura=330))
    esc_a = _arco_d(_partes(area["svg"], "arco-da-area")[0][1]["d"])[2] / 9.15      # a escala sai do raio do arco da área
    assert abs((area["tinta"][2] - area["tinta"][0]) - 330) <= 0.5 and area["h"] > area["w"] and area["tinta"][0] == 0, area["tinta"]
    assert abs(area["tinta"][2] - (1 + (11 + 9.15) * esc_a + 1)) < 0.25, "o ponto mais à direita da tinta é o arco da área, a 11 + 9,15 m do fundo"
    pista_canto = gerar_ok("campo", dict(esporte="pista", recorte="canto", largura=360))
    assert abs((pista_canto["tinta"][2] - pista_canto["tinta"][0]) - 360) <= 0.5 and len(_partes(pista_canto["svg"], "raia")) == 9


# ---------------------------------------------------------------- placar
ROWS = [{"data": "14.03 · 08h", "mandante": "Ubatuba FC", "placar": "2 x 1", "visitante": "Tubarões da Orla"},
        {"data": "14.03 · 10h", "mandante": "Costão Esporte Clube", "placar": "0 x 0", "visitante": "Praia Grande"},
        {"data": "15.03 · 08h", "mandante": "Sertão United", "placar": "10 x 2", "visitante": "Maresia"},
        {"data": "15.03 · 10h", "mandante": "Itamambuca", "placar": "W.O.", "visitante": "Perequê"}]


def test_placar_colunas_alinhadas_numerais_tabulares_e_texto_vivo():
    r = gerar_ok("placar", dict(cabecalho="Copa AME Sua Marca · 1ª rodada", largura=640, linhas=ROWS))
    esperado = ["COPA AME SUA MARCA · 1ª RODADA"] + [t for l in ROWS for t in (
        l["data"], l["mandante"], *(re.match(r"(\d+) (x) (\d+)$", l["placar"]).groups() if " x " in l["placar"] else (l["placar"],)), l["visitante"])]
    assert r["texto"].split("\n") == esperado, r["texto"].split("\n")
    assert r["fontes"] == ["Outfit", "Kanit"] and r["svg"].count("<text") == len(esperado)
    # medidas dos <text> no Chromium: o x vem do svg, a largura do navegador
    m = g.medir_no_chromium([r["svg"]], fontes_dir())[0]["textos"]
    textos = [(e.text, float(e.get("x")), float(e.get("y"))) for e in raiz(r["svg"]).iter() if e.tag.endswith("text")]
    assert [t[0] for t in textos] == esperado
    box = [(t, x, x + mm["comprimento"], y) for (t, x, y), mm in zip(textos, m)]
    # cada linha da tabela tem data, mandante, [gols, separador, gols] ou placar livre, visitante: 1 + 4 + 3 + 1 = por linha
    idx, por_linha = 1, []
    for l in ROWS:
        n = 6 if " x " in l["placar"] else 4
        por_linha.append(box[idx: idx + n]); idx += n
    assert idx == len(box)
    datas_x = [b[0][1] for b in por_linha]
    mandante_dir = [round(b[1][2], 2) for b in por_linha]
    visitante_esq = [round(b[-1][1], 2) for b in por_linha]
    assert max(datas_x) - min(datas_x) < 0.01, datas_x                     # datas alinhadas à esquerda
    assert max(mandante_dir) - min(mandante_dir) < 0.06, mandante_dir      # mandantes alinhados à direita
    assert max(visitante_esq) - min(visitante_esq) < 0.01, visitante_esq   # visitantes alinhados à esquerda
    centros_sep = [(b[3][1] + b[3][2]) / 2 for b in por_linha if len(b) == 6]
    gols_mandante_dir = [round(b[2][2], 2) for b in por_linha if len(b) == 6]
    gols_visitante_esq = [round(b[4][1], 2) for b in por_linha if len(b) == 6]
    assert max(centros_sep) - min(centros_sep) < 0.06, centros_sep         # o separador fica na mesma coluna em todas as linhas
    assert max(gols_mandante_dir) - min(gols_mandante_dir) < 0.06 and max(gols_visitante_esq) - min(gols_visitante_esq) < 0.01
    livre = por_linha[3][2]                                                # "W.O." sem separador: centrado na coluna do placar
    assert abs((livre[1] + livre[2]) / 2 - centros_sep[0]) < 0.06, (livre, centros_sep)
    ys = [b[0][3] for b in por_linha]
    assert np.allclose(np.diff(ys), np.diff(ys)[0], atol=0.01), "linhas na mesma cadência"
    # numerais tabulares: Outfit tem tnum, então "14.03 · 08h" e "15.03 · 10h" medem igual no navegador e na fonte (tnum aplicado)
    f_corpo = g.fonte(ctx(), "corpo", 600)
    tamanhos = {e.text: float(re.search(r"font-size:([\d.]+)px", e.get("style")).group(1)) for e in raiz(r["svg"]).iter() if e.tag.endswith("text")}
    assert tamanhos["14.03 · 08h"] < 0.8 * 20, "a largura de 640 px encolheu a tabela: o tamanho da data vem do svg, não do pedido"
    for (t, x, x1, y) in (b[0] for b in por_linha):
        esperado = f_corpo.largura(t, tamanhos[t], 0, True)
        assert abs((x1 - x) - esperado) <= 1.0, (t, x1 - x, esperado)       # o navegador mede o que a fonte com tnum diz
    assert abs(f_corpo.largura("1111", 16, 0, True) - f_corpo.largura("0000", 16, 0, True)) < 0.01, "com tnum todo algarismo tem a mesma largura"
    assert f_corpo.largura("0000", 16) - f_corpo.largura("1111", 16) > 2, "sem tnum o 1 é mais estreito: a prova de cima mediria o mesmo"
    assert "tabular-nums" in r["svg"]
    # fios: o forte fecha o cabeçalho e o final; os finos separam as linhas (3); fios verticais entre as colunas (3)
    ds = [(e.get("d"), e.get("stroke-width")) for e in raiz(r["svg"]).iter() if e.tag.endswith("path") and e.get("stroke-width") in ("1", "2")]
    horizontais = [sw for d, sw in ds if re.fullmatch(r"M0 ([\d.]+)L[\d.]+ \1", d)]
    verticais = [d for d, sw in ds if re.fullmatch(r"M([\d.]+) [\d.]+L\1 [\d.]+", d)]
    assert horizontais.count("2") == 2 and horizontais.count("1") == 3 and len(verticais) == 3, (horizontais, verticais)
    # a tinta e as linhas
    ink = caixa_alfa(raster(r["svg"]))
    assert all(abs(a - b) <= 1.5 for a, b in zip(ink, r["tinta"])), (ink, r["tinta"])
    # reduz a tabela inteira quando um nome não cabe (até 70%) e recusa abaixo disso
    pequeno = gerar_ok("placar", dict(largura=520, linhas=ROWS))
    tam = {float(x) for x in re.findall(r"font-size:([\d.]+)px", pequeno["svg"])}
    assert max(tam) < 24 and min(tam) >= 0.7 * 16 - 0.01 and pequeno["w"] <= 522, tam
    levanta("placar", dict(largura=200, linhas=ROWS), "70%")
    levanta("placar", dict(linhas=[]), "linhas")
    levanta("placar", dict(linhas=[ROWS[0], {"data": "x", "mandante": "A", "placar": "1 x 0"}]), "linha 2 do placar sem visitante")
    levanta("placar", dict(linhas=[dict(ROWS[0], mandante="Sertão ★ FC")]), "★")


# ---------------------------------------------------------------- celular
def test_celular_uma_imagem_so_recortada_nos_cantos_e_cobrindo_a_tela():
    W, B = 240, 8.64
    r = gerar_ok("celular", dict(imagem=str(imagem_teste()), largura=W))
    assert r["svg"].count("<image") == 1 and "<clipPath" in r["svg"] and r["texto"] == "" and r["fontes"] == []
    uri = re.search(r'href="(data:image/(png|jpeg);base64,[^"]+)"', r["svg"])
    import base64 as b64
    im = Image.open(io.BytesIO(b64.b64decode(uri.group(1).split(",", 1)[1])))
    sw, sh = W - 2 * B, 520 - 2 * B
    assert im.mode == "RGB" and im.width <= round(2 * sw) and abs(im.width / im.height - sw / sh) < 0.01, (im.mode, im.size)   # sem alfa; já no aspecto da tela
    a = raster(r["svg"])
    rgb = a[..., :3].astype(int)
    corpo = (14, 13, 8)                                                         # a cor `escuro` da paleta de teste (#0E0D08)
    # a 31 px do centro do canto arredondado a imagem já foi cortada (a tela tem raio 27) e o corpo ainda está lá (raio 35)
    canto = (14, 14)
    assert a[..., 3][canto] == 255 and abs(rgb[canto] - np.array(corpo)).max() <= 12, (rgb[canto], "no canto da tela aparece o corpo, não a imagem")
    assert a[..., 3][2, 2] == 0, "o corpo também tem o canto arredondado: o pixel de ponta é transparente"
    # o disco amarelo da imagem, no centro: círculo, não elipse (a imagem cobre sem esticar)
    amarelo = (np.abs(rgb - np.array([240, 200, 60])).max(axis=2) < 30) & (a[..., 3] > 200)
    ys, xs = np.nonzero(amarelo)
    dh, dv = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
    esperado = 200 * (sw / (1170 * sw / sh))      # diâmetro do disco depois de cortar a largura que passa e reduzir à tela
    assert abs(dh - dv) <= 2 and abs(dh - esperado) <= 3, (dh, dv, esperado)
    assert abs((xs.min() + xs.max() + 1) / 2 - W / 2) <= 2 and abs((ys.min() + ys.max() + 1) / 2 - 260) <= 2, "disco no centro da tela"
    # a ilha: uma pílula escura no alto, e o fio do corpo na cor da página
    assert r["svg"].count("<rect") >= 3 and "currentColor" in r["svg"]
    # imagem com transparência vira a cor do corpo atrás (nada de segunda imagem no PDF); JPEG segue JPEG; imagem enorme é reduzida
    rgba = Path(_TMP) / "tela-alfa.png"
    Image.new("RGBA", (400, 800), (255, 0, 0, 0)).save(rgba)
    ra = gerar_ok("celular", dict(imagem=str(rgba), largura=240))
    assert ra["svg"].count("<image") == 1
    jpg = imagem_teste("tela.jpg", jpeg=True)
    assert "data:image/jpeg" in gerar_ok("celular", dict(imagem=str(jpg), largura=240))["svg"]
    grande = Path(_TMP) / "grande.png"
    Image.new("RGB", (3000, 6000), (200, 30, 30)).save(grande)
    ug = re.search(r'href="(data:image/png;base64,[^"]+)"', gerar_ok("celular", dict(imagem=str(grande), largura=240))["svg"]).group(1)
    assert Image.open(io.BytesIO(b64.b64decode(ug.split(",", 1)[1]))).width <= round(2 * sw)
    assert "fill=\"currentColor\"" in gerar_ok("celular", dict(imagem=str(imagem_teste()), fundo="marca"))["svg"]
    levanta("celular", dict(largura=240), "imagem")
    levanta("celular", dict(imagem="/nao/existe.png"), "não encontrada")
    levanta("celular", dict(imagem=str(imagem_teste()), largura=100, moldura=60), "não cabem")
    levanta("celular", dict(imagem=str(imagem_teste()), fundo="transparent"), "transparente")


# ---------------------------------------------------------------- mapa
def _haversine(a, b):
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


PONTOS = [{"nome": "Ubatuba", "lat": -23.4336, "lon": -45.0838, "destaque": True},
          {"nome": "São Paulo", "lat": -23.5505, "lon": -46.6333},
          {"nome": "Rio de Janeiro", "lat": -22.9068, "lon": -43.1729},
          {"nome": "Campinas", "lat": -22.9099, "lon": -47.0626},
          {"nome": "São José dos Campos", "lat": -23.2237, "lon": -45.9009},
          {"nome": "Taubaté", "lat": -23.0265, "lon": -45.5553}]


def rotulos_sem_colisao(r):
    """Confere num resultado do `mapa` que cada rótulo cabe na caixa, não cobre outro rótulo nem um ponto (caixas da tinta pela
    medida da fonte, lidas do svg). Devolve [(texto, caixa)]."""
    el = raiz(r["svg"])
    caixas = []
    for e in el.iter():
        if not e.tag.endswith("text"):
            continue
        s = float(re.search(r"font-size:([\d.]+)px", e.get("style")).group(1))
        ls = float(re.search(r"letter-spacing:([-\d.]+)px", e.get("style")).group(1))
        fam = re.search(r"font-family:'([^']+)'", e.get("style")).group(1)
        f = g.fonte(ctx(), "display" if fam == "Kanit" else "corpo", 800 if fam == "Kanit" else 600)
        x0, y0, x1, y1 = f.caixa_tinta(e.text, s, ls, "tabular" in e.get("style"))
        x, y = float(e.get("x")), float(e.get("y"))
        caixas.append((e.text, [x + x0, y - y1, x + x1, y - y0]))
    pontos = [(float(c.get("cx")), float(c.get("cy")), float(c.get("r"))) for c in el.iter()
              if c.tag.endswith("circle") and c.get("fill") == "currentColor" and c.get("r") in ("4", "7")]
    for i, (ti, ci) in enumerate(caixas):
        assert ci[0] >= 0 and ci[1] >= 0 and ci[2] <= r["w"] and ci[3] <= r["h"], (ti, ci)
        for tj, cj in caixas[i + 1:]:
            assert not (ci[0] < cj[2] and ci[2] > cj[0] and ci[1] < cj[3] and ci[3] > cj[1]), f"rótulos `{ti}` e `{tj}` se cobrem"
        for px, py, rr in pontos:
            assert not (ci[0] < px + rr and ci[2] > px - rr and ci[1] < py + rr and ci[3] > py - rr), f"rótulo `{ti}` cobre um ponto"
    return caixas


def test_mapa_distancias_em_escala_norte_para_cima_e_rotulos_sem_colisao():
    r = gerar_ok("mapa", dict(largura=640, altura=420, aneis=[100, 300], pontos=PONTOS))
    el = raiz(r["svg"])
    circulos = [e for e in el.iter() if e.tag.endswith("circle")]
    aneis = sorted((c for c in circulos if c.get("stroke-dasharray")), key=lambda c: float(c.get("r")))
    pontos = [c for c in circulos if c.get("fill") == "currentColor" and c.get("r") in ("4", "7")]
    assert len(aneis) == 2 and len(pontos) == 6
    px_por_km = float(aneis[0].get("r")) / 100
    assert abs(float(aneis[1].get("r")) / 300 - px_por_km) < 1e-4, "a mesma escala em todos os anéis"
    centro = (float(aneis[0].get("cx")), float(aneis[0].get("cy")))
    assert all(abs(float(a.get("cx")) - centro[0]) < 1e-6 and abs(float(a.get("cy")) - centro[1]) < 1e-6 for a in aneis)
    # as posições, na ordem dos pontos de entrada (o svg desenha os pontos nessa ordem)
    pos = [(float(c.get("cx")), float(c.get("cy"))) for c in pontos]
    assert pos[0] == centro, "o destaque é o centro dos anéis"
    for i in range(len(PONTOS)):
        for j in range(i + 1, len(PONTOS)):
            d_px = math.hypot(pos[i][0] - pos[j][0], pos[i][1] - pos[j][1]) / px_por_km
            d_km = _haversine((PONTOS[i]["lat"], PONTOS[i]["lon"]), (PONTOS[j]["lat"], PONTOS[j]["lon"]))
            assert abs(d_px / d_km - 1) < 0.01, (PONTOS[i]["nome"], PONTOS[j]["nome"], d_px, d_km)
    assert pos[1][0] < pos[0][0] < pos[2][0], "leste à direita (São Paulo, Ubatuba, Rio)"
    assert pos[2][1] < pos[0][1] and pos[3][1] < pos[0][1] and pos[1][1] > pos[0][1], \
        "o norte fica em cima: Rio e Campinas (lat -22,9) acima de Ubatuba (-23,4), São Paulo (-23,55) abaixo"
    # rótulos: todos os nomes e os anéis, em texto vivo e em caixa alta
    assert r["texto"].split("\n") == ["100 KM", "300 KM", "UBATUBA", "SÃO PAULO", "RIO DE JANEIRO", "CAMPINAS", "SÃO JOSÉ DOS CAMPOS", "TAUBATÉ"], r["texto"]
    # nenhum rótulo cobre outro, nenhum cobre um ponto, todos cabem na caixa (caixas de tinta pela medida da fonte)
    caixas = rotulos_sem_colisao(r)
    # tinta e `linhas` contra o raster
    a = raster(r["svg"])
    ink = caixa_alfa(a)
    assert all(abs(x - y) <= 1.5 for x, y in zip(ink, r["tinta"])), (ink, r["tinta"])
    topo_rotulos = min(c[1][1] for c in caixas)
    assert r["linhas"]["cap"] >= topo_rotulos - 0.01 and r["linhas"]["cap"] - topo_rotulos <= 5      # cap da fonte x topo da tinta (o til e o acento passam do cap)
    assert abs(r["linhas"]["linha_base"] - max(c[1][3] for c in caixas)) <= 1.5, (r["linhas"], max(c[1][3] for c in caixas))
    # `rotulo: false` deixa o ponto sem nome (descongestiona); o ponto continua desenhado
    menos = gerar_ok("mapa", dict(largura=520, altura=330, pontos=[dict(q, rotulo=False) if q["nome"] == "Taubaté" else q for q in PONTOS]))
    assert "TAUBATÉ" not in menos["texto"] and len([c for c in raiz(menos["svg"]).iter() if c.tag.endswith("circle") and c.get("r") == "4"]) == 5
    rotulos_sem_colisao(menos)
    # sem destaque não há anel; sem anel, o mapa cabe os pontos; erros
    sem = gerar_ok("mapa", dict(pontos=[dict(q, destaque=False) for q in PONTOS]))
    assert not any(e.get("stroke-dasharray") for e in raiz(sem["svg"]).iter())
    levanta("mapa", dict(pontos=PONTOS, largura=260, altura=120, margem=20), "rotulo: false")      # sem lugar: erro com a saída, não texto por cima de texto
    apertado = gerar_ok("mapa", dict(largura=520, altura=330, aneis=[100, 300], pontos=PONTOS))
    assert 'stroke-opacity="0.6"' in apertado["svg"], "rótulo longe do ponto leva um fio até ele"
    rotulos_sem_colisao(apertado)
    levanta("mapa", dict(pontos=[dict(q, destaque=False) for q in PONTOS], aneis=[100]), "destaque")
    levanta("mapa", dict(pontos=[PONTOS[0]]), "2 pontos em lugares diferentes")
    levanta("mapa", dict(pontos=[{"nome": "X", "lat": 95, "lon": 0}, {"nome": "Y", "lat": 1, "lon": 1}]), "fora do mundo")
    levanta("mapa", dict(pontos=[{"lat": 1, "lon": 1}, {"nome": "Y", "lat": 1, "lon": 2}]), "nome")
    levanta("mapa", dict(pontos=[PONTOS[0], dict(PONTOS[1], nome="São ★")]), "★")
    levanta("mapa", dict(pontos=PONTOS, aneis=[-5]), "aneis")
    levanta("mapa", dict(pontos=PONTOS, margem=300), "margem")


# ---------------------------------------------------------------- constantes de borda
def test_fio_borda_e_pattern_borda_sao_constantes_do_sistema():
    f = gerar_ok("fio-borda", dict(largura=600, espessura=3))
    assert (f["w"], f["h"]) == (600, 3) and f["tinta"] == [0.0, 0.0, 600.0, 3.0] and raiz(f["svg"]).get("data-grafismo") == "fio-borda"
    a = raster(f["svg"])[..., 3] >= 128
    assert a.all(), "o fio ocupa a caixa inteira"
    t = gerar_ok("fio-borda", dict(largura=400, espessura=2, tracejado=[10, 6]))
    assert len(corridas(raster(t["svg"])[..., 3][0] >= 128)) == math.ceil(400 / 16)
    for padrao, esperado in (("linhas", "linhas"), ("listras", "listras"), ("pontos", "grade-pontos")):
        r = gerar_ok("pattern-borda", dict(largura=500, padrao=padrao))
        assert (r["w"], r["h"]) == (500, 48) and raiz(r["svg"]).get("data-grafismo") == "pattern-borda"
        assert "currentColor" in r["svg"]
    # o padrão herda os parâmetros do tipo escolhido
    r = gerar_ok("pattern-borda", dict(largura=500, altura=40, padrao="linhas", espacamento=8, angulo=0))
    assert componentes(raster(r["svg"]))[1] == 5
    # no sistema, a constante vai a `gerar` pelo tipo que o schema lista
    levanta("pattern-borda", dict(padrao="xadrez"), "padrao")
    levanta("fio-borda", dict(tracejado=[0, 3]), "tracejado")
    sch = json.loads((AQUI.parent / "schema" / "elementos.schema.json").read_text(encoding="utf-8"))
    enum = set(sch["definitions"]["sistema_elementos"]["properties"]["constantes"]["items"]["properties"]["tipo"]["enum"])
    assert {"fio-borda", "pattern-borda"} <= enum <= set(g.TIPOS) | {"grao"}


# ---------------------------------------------------------------- a tinta declarada é a que o navegador desenha
def test_chromium_tinta_declarada_confere_com_o_raster():
    casos = [(t, exemplo(t, p)) for t, p in EXEMPLOS if t in NOVOS] + [
        ("linhas", dict(largura=360, altura=220, espacamento=18, angulo=30, recorte=[40, 30, 280, 160], esmaecer="baixo")),
        ("listras", dict(largura=300, altura=64, cores=["marca", "transparent"], angulo=45)),
        ("fio", dict(pontos=[[10, 10], [300, 40]], tracejado=[10, 6], terminais=["barra", "barra"])),
        ("regua", dict(comprimento=240, orientacao="vertical", passo=12, rotulos=["0", "5", "10", "15", "20"], lado="esq")),
        ("circulos", dict(raios=[40, 80], angulo_ini=-50, angulo_fim=50, espessura=3)),
        ("estrelas", dict(quantidade=7, arco=120, passo=44, tamanho=30)),
        ("setas", dict(quantidade=3, direcao="baixo", tamanho=40)),
        ("campo", dict(esporte="futebol", largura=420, angulo=-12)),
        ("campo", dict(esporte="futebol", recorte="circulo", largura=260)),
        ("campo", dict(esporte="pista", recorte="area", largura=360)),
        ("placar", dict(linhas=ROWS, largura=600)),
        ("mapa", dict(pontos=PONTOS)),
        ("divisoria", dict(comprimento=300, ornamento="ponto", posicao="pontas", orientacao="vertical")),
    ]
    rs = [gerar_ok(t, p) for t, p in casos]
    for (t, p), r, a in zip(casos, rs, rasters([r["svg"] for r in rs])):
        ink = caixa_alfa(a)
        dif = max(abs(x - y) for x, y in zip(ink, r["tinta"]))
        print(f"   {t:13} tinta declarada {r['tinta']}  raster {ink}  diferença máxima {dif:.2f} px")
        # estrela: a ponta de 36 graus tem cobertura menor que 50% nos últimos ~2 px, e o alfa >= 128 não conta essa ponta
        assert dif <= (2.5 if t == "estrelas" else 1.5), (t, p, r["tinta"], ink)


# ---------------------------------------------------------------- o PDF: texto vivo, sem Type 3, uma imagem só, mesmo desenho
def _itens_da_pagina():
    """Todos os grafismos de composição numa página de 1920 x 1080, empacotados em prateleiras (o `colchetes` enquadra o
    campo e o `fio` liga duas coisas: os dois têm coordenadas da página, como na composição)."""
    placar = dict(cabecalho="Copa AME Sua Marca · 1ª rodada", largura=620, linhas=ROWS)
    mapa = dict(largura=520, altura=330, aneis=[100, 300], pontos=PONTOS)
    return [
        ("campo", dict(esporte="futebol", largura=500)), ("placar", placar), ("celular", dict(imagem=str(imagem_teste()), largura=190)),
        ("mapa", mapa), ("grade-pontos", dict(largura=300, altura=170, passo=20, esmaecer="dir")),
        ("linhas", dict(largura=300, altura=170, espacamento=14, angulo=-30, esmaecer={"direcao": "baixo", "passos": 5})),
        ("circulos", dict(raios=[30, 60, 90], angulo_ini=-60, angulo_fim=60, espessura=2.5)),
        ("regua", dict(comprimento=440, passo=11, rotulos={"inicio": 0, "passo": 5})), ("divisoria", dict(comprimento=380, ornamento="losango")),
        ("listras", dict(largura=420, altura=40)), ("setas", dict(quantidade=4, tamanho=30)), ("estrelas", dict(quantidade=7, arco=120, passo=40, tamanho=26)),
    ]


def _montar_pagina(omitir=()):
    """(html, [(tipo, x, y, resultado)]) da página de prova. `omitir` tira um tipo (controle da prova de comparação)."""
    c = ctx()
    colocados, x, y, alt, margem, gap = [], 40, 70, 0, 40, 36
    for tipo, prm in _itens_da_pagina():
        r = g.gerar(tipo, prm, c)
        if x + r["w"] > 1920 - margem:
            x, y, alt = margem, y + alt + gap, 0
        colocados.append((tipo, x, y, r))
        x, alt = x + r["w"] + gap, max(alt, r["h"])
    baixo = y + alt
    assert baixo <= 1020, f"a página de prova passou do rodapé: {baixo}"
    campo = next(r for t, _, _, r in colocados if t == "campo")
    cx, cy = next((x_, y_) for t, x_, y_, _ in colocados if t == "campo")
    # colchetes enquadram o campo (alvo + folga de 14 px) e um fio com ponto e seta sai do canto do campo para a página
    colch = g.gerar("colchetes", {"caixa": [cx - 14, cy - 14, campo["w"] + 28, campo["h"] + 28], "braco": 30, "espessura": 3}, c)
    fio = g.gerar("fio", {"pontos": [[1520, 300], [1700, 300], [1700, 520]], "espessura": 2.5, "terminais": ["ponto", "seta"]}, c)
    borda = g.gerar("fio-borda", {"largura": 1920, "espessura": 3}, c)
    pat = g.gerar("pattern-borda", {"largura": 1920, "altura": 36, "padrao": "listras", "largura_listra": 18, "cores": ["marca", "transparent"]}, c)
    rotulos_sem_colisao(next(r for t, _, _, r in colocados if t == "mapa"))      # o mapa apertado (520 x 330) também tem de sair limpo
    colocados += [("colchetes", colch["origem"][0], colch["origem"][1], colch), ("fio", fio["origem"][0], fio["origem"][1], fio),
                  ("fio-borda", 0, 0, borda), ("pattern-borda", 0, 1080 - 36, pat)]
    colocados = [t for t in colocados if t[0] not in omitir]
    familias = {"Kanit", "Outfit"}
    pal = c["paleta"]
    corpo = "".join(f'<div class="el" style="left:{x}px;top:{y}px">{r["svg"]}</div>' for _, x, y, r in colocados)
    html = (f"<!doctype html><html><head><meta charset='utf-8'><style>{g.css_fontes(fontes_dir(), familias)}\n"
            "@page { size: 1920px 1080px; margin: 0 }\n* { font-synthesis: none; box-sizing: border-box; }\n"
            f"html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: {pal['escuro']}; color: {pal['marca']}; }}\n"
            ".el { position: absolute; line-height: 0; } svg { display: block; }"
            f"</style></head><body>{corpo}</body></html>")
    return html, colocados


def _exportar(html, pasta):
    """PNG (captura) e PDF do mesmo Chromium, com as mesmas opções do render.py (media screen, fundo impresso, 1920 x 1080)."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
        pg.emulate_media(media="screen")
        pg.set_content(html, wait_until="load")
        pg.evaluate(JS_FONTES)
        pg.screenshot(path=str(pasta / "pagina.png"))
        pg.pdf(path=str(pasta / "pagina.pdf"), width="1920px", height="1080px", print_background=True, prefer_css_page_size=True,
               margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        b.close()
    return pasta / "pagina.png", pasta / "pagina.pdf"


def _desvio_fora(a, b, mascara, sigma=2.0):
    """Maior diferença (níveis de cinza, de 255) entre duas imagens depois de um desfoque que apaga o antialiasing (o do poppler
    e o do Chromium não coincidem pixel a pixel), fora da máscara. Um traço de 2 px que sumiu continua dando ~120."""
    from scipy.ndimage import gaussian_filter
    ga, gb = (gaussian_filter(np.asarray(x.convert("L"), float), sigma) for x in (a, b))
    return float(np.abs(ga - gb)[~mascara].max())


def _desvio_medias(a, b, caixa, lado=24):
    """Pior diferença entre as MÉDIAS por bloco (lado x lado px) dentro de uma caixa [x, y, w, h]: a imagem do celular é
    reamostrada de um jeito em cada renderizador, mas a cor de cada região tem de coincidir."""
    x, y, w, h = caixa
    ca, cb = (np.asarray(im.convert("L"), float)[y:y + h, x:x + w] for im in (a, b))
    hh, ww = (ca.shape[0] // lado) * lado, (ca.shape[1] // lado) * lado
    m = lambda v: v[:hh, :ww].reshape(hh // lado, lado, ww // lado, lado).mean(axis=(1, 3))     # noqa: E731
    return float(np.abs(m(ca) - m(cb)).max())


def test_pdf_dos_novos_grafismos_texto_vivo_sem_type3_uma_imagem_e_mesmo_desenho():
    html, colocados = _montar_pagina()
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        png, pdf = _exportar(html, d)
        # fontes: todas embutidas, nenhuma Type 3 (Type 3 = texto virou desenho: aprendizado 20)
        saida = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True).stdout
        fontes = saida.strip().splitlines()[2:]
        print("   pdffonts:", "; ".join(" ".join(l.split()[:-6]) for l in fontes))
        assert fontes and "Type 3" not in saida, saida
        assert all(re.search(r"\byes\s+yes\s+yes\b", l) or re.search(r"\byes\s+\w+\s+yes\b", l) for l in fontes), saida
        assert any("Outfit" in l for l in fontes) and any("Kanit" in l for l in fontes), saida
        # texto vivo: o do placar, da régua e do mapa está no PDF, como texto (pdftotext -raw segue a ordem do conteúdo)
        texto = subprocess.run(["pdftotext", "-raw", str(pdf), "-"], capture_output=True, text=True).stdout
        plano = re.sub(r"\s", "", texto)
        esperados = ["COPAAMESUAMARCA·1ªRODADA", "UbatubaFC", "TubarõesdaOrla", "CostãoEsporteClube", "PraiaGrande", "SertãoUnited",
                     "Maresia", "Itamambuca", "Perequê", "W.O.", "14.03·08h", "15.03·10h", "UBATUBA", "SÃOPAULO", "RIODEJANEIRO",
                     "SÃOJOSÉDOSCAMPOS", "100KM", "300KM"]
        faltam = [e for e in esperados if e not in plano]
        assert not faltam, f"texto vivo que não chegou ao PDF: {faltam}"
        assert re.search(r"\b0\s+5\s+10\s+15\s+20\s+25\s+30\s+35\s+40\b", texto), "rótulos da régua em ordem"
        # imagens: só a do celular (a captura de tela); nenhuma outra (nada rasterizado), e sem máscara de alfa (smask)
        imgs = subprocess.run(["pdfimages", "-list", str(pdf)], capture_output=True, text=True).stdout.strip().splitlines()[2:]
        print(f"   pdfimages: {len(imgs)} imagem: {' '.join(imgs[0].split()[:6]) if imgs else '-'}")
        assert len(imgs) == 1 and imgs[0].split()[2] == "image", imgs
        # o raster do PDF (poppler, 96 dpi) é o desenho que o Chromium mostrou na tela, a menos de antialiasing
        subprocess.run(["pdftoppm", "-r", "96", "-png", "-singlefile", str(pdf), str(d / "pdf")], check=True)
        a, b = Image.open(png), Image.open(d / "pdf.png")
        assert a.size == b.size == (1920, 1080), (a.size, b.size)
        cx, cy, cw, ch = next((x, y, r["w"], r["h"]) for tp, x, y, r in colocados if tp == "celular")
        mascara = np.zeros((1080, 1920), bool)
        mascara[max(0, cy - 3):cy + ch + 3, max(0, cx - 3):cx + cw + 3] = True
        fora = _desvio_fora(a, b, mascara)
        dentro = _desvio_medias(a, b, (cx, cy, cw, ch))
        print(f"   PDF x tela: fora do celular, maior diferença depois do desfoque {fora:.1f} de 255; no celular, pior média de bloco {dentro:.1f}")
        assert fora < 45 and dentro < 8, (fora, dentro)
        # controle: o mesmo PDF sem o campo, comparado com a tela que TEM o campo, tem de reprovar a mesma conta
        html2, _ = _montar_pagina(omitir=("campo",))
        d2 = d / "sem-campo"
        d2.mkdir()
        _, pdf2 = _exportar(html2, d2)
        subprocess.run(["pdftoppm", "-r", "96", "-png", "-singlefile", str(pdf2), str(d / "pdf2")], check=True)
        controle = _desvio_fora(a, Image.open(d / "pdf2.png"), mascara)
        print(f"   controle (PDF sem o campo x tela com o campo): maior diferença {controle:.1f}")
        assert controle > 80 and controle > 2.5 * fora, "a conta não distingue um desenho que sumiu do PDF"


# ================================================================= largura e altura são a medida da TINTA (o que a composição pede)
# A Frente A gera o grafismo ancorado com `escala` passando só `largura` OU só `altura` (a dimensão da tinta) e marca "esticada"
# se a tinta devolvida não bater (1 px). Cada tipo honra a medida; os de proporção fixa fazem a maior que cabe nas duas.
BASE_MEDIDA = {    # parâmetros de cada tipo SEM largura, altura, diâmetro nem geometria da página: só o que muda o conteúdo
    "microtexto": {"texto": MICRO}, "selo": {"texto": SELO, "recorte": ASA}, "meio-tom-simbolo": {"recorte": ASA, "celula": 10},
    "pattern-simbolo": {"recorte": ASA, "lado": 100}, "linha-percurso": {"curva": {"tipo": "orla"}},
    "fios-tecnicos": {"alvos": [{"x": 100, "y": 150, "rotulo": "Pórtico"}]}, "moldura": {"etiqueta": "Cota ouro"},
    "etiqueta": {"texto": "Naming rights"}, "numeral": {"texto": "2027"}, "tipo-textura": {"texto": "Sprint"},
    "faixa-diagonal": {"texto": MICRO}, "mosaico": {"recorte": ASA}, "linhas": {"espacamento": 14, "angulo": -30},
    "listras": {}, "colchetes": {}, "fio": {"terminais": ["ponto", "seta"]}, "regua": {"passo": 12, "rotulos": {"inicio": 0, "passo": 5}},
    "divisoria": {}, "grade-pontos": {"passo": 20}, "circulos": {"raios": [30, 60, 90]}, "setas": {"quantidade": 4},
    "estrelas": {"quantidade": 5}, "campo": {}, "placar": {"cabecalho": "Rodada", "linhas": ROWS}, "celular": {},
    "mapa": {"aneis": [100, 300], "pontos": PONTOS}, "fio-borda": {}, "pattern-borda": {"padrao": "listras"},
    "hachura": {"espacamento": 12}, "malha": {"passo": 20}, "aneis": {"quantidade": 5}, "pontos-radiais": {"raio_min": 1.5},
    "cantoneira": {"estilo": "escada"}, "moldura-dupla": {"cantos": "chanfro"}, "regua-borda": {}, "eco": {"texto_de": "evento"},
    "texto-curva": {"texto_de": "evento"}, "ondas": {}, "curvas-nivel": {}, "fita": {"texto_de": "evento"},
    "carimbo": {"texto": SELO, "centro_texto": "2027"}, "numeral-eco": {"texto": "2027"}, "meio-tom-foto": {"celula": 12},
}
ALVOS_MEDIDA = {"divisoria": (420, 24), "regua": (420, 60), "regua-borda": (420, 60), "fio": (420, 80), "mapa": (700, 480), "colchetes": (420, 260),
                "placar": (700, 260)}      # divisória: a altura é o ornamento; régua e fio, o estilo; mapa e placar precisam de caixa para os nomes
AREA = ("microtexto", "pattern-simbolo", "linha-percurso", "fios-tecnicos", "moldura", "etiqueta", "faixa-diagonal", "linhas", "listras",
        "colchetes", "regua", "divisoria", "grade-pontos", "placar", "pattern-borda",     # com as duas, cada dimensão é a pedida
        "hachura", "malha", "aneis", "pontos-radiais", "cantoneira", "moldura-dupla", "regua-borda", "ondas", "curvas-nivel", "fita")


def test_largura_e_altura_sao_a_medida_da_tinta_em_todos_os_tipos():
    assert sorted(BASE_MEDIDA) == sorted(g.TIPOS), "tipo sem prova de medida"
    for tipo in g.TIPOS:
        base = exemplo(tipo, BASE_MEDIDA[tipo])
        W, H = ALVOS_MEDIDA.get(tipo, (420, 260))
        res = {}
        for modo, ped in (("L", {"largura": W}), ("A", {"altura": H}), ("LA", {"largura": W, "altura": H})):
            try:
                r = g.gerar(tipo, dict(base, **ped), ctx())
            except ValueError as e:
                raise AssertionError(f"{tipo} não gerou com {ped}: {e}")
            ti = r.get("tinta") or [0, 0, r["w"], r["h"]]
            res[modo] = (ti[2] - ti[0], ti[3] - ti[1], r)
        tol = 0.5 if res["L"][2].get("tinta") else 1.0       # sem `tinta` a Frente A mede a caixa do svg e aceita até 1 px
        assert abs(res["L"][0] - W) <= tol, (tipo, "largura", res["L"][0], W)
        assert abs(res["A"][1] - H) <= tol, (tipo, "altura", res["A"][1], H)
        lw, lh, _ = res["LA"]
        assert lw <= W + tol and lh <= H + tol, (tipo, "as duas: cabe nas duas", lw, lh)
        if tipo in AREA:
            assert abs(lw - W) <= tol and abs(lh - H) <= tol, (tipo, "as duas: cada uma é a pedida", lw, lh)
        elif tipo not in ("fio", "mapa"):      # fio com as duas = a diagonal da caixa, recuada o que o terminal passa; mapa com as duas = a
            assert abs(lw - W) <= tol or abs(lh - H) <= tol, (tipo, "as duas: a maior que cabe", lw, lh)     # caixa (a tinta cabe nela)
        print(f"   {tipo:17} largura {res['L'][0]:7.2f} (pedi {W})  altura {res['A'][1]:7.2f} (pedi {H})  as duas {lw:6.1f} x {lh:6.1f}")


def test_selo_aceita_largura_e_altura_como_diametro_e_o_legado_nao_muda():
    c = ctx()
    prm = {"texto": SELO, "centro": None}
    assert (lambda r: (r["w"], r["h"]))(g.gerar("selo", dict(prm, largura=300), c)) == (300, 300)
    assert (lambda r: (r["w"], r["h"]))(g.gerar("selo", dict(prm, altura=260), c)) == (260, 260)
    assert (lambda r: (r["w"], r["h"]))(g.gerar("selo", dict(prm, largura=300, altura=260), c)) == (260, 260), "o menor dos dois é o diâmetro"
    sem = lambda r: re.sub(r'data-uid="[^"]+"|id="(cima|baixo)-[^"]+"|href="#(cima|baixo)-[^"]+"', "", r["svg"])      # noqa: E731  (o uid muda com os params)
    a, b = g.gerar("selo", dict(prm, diametro=240, largura=300), c), g.gerar("selo", dict(prm, diametro=240), c)
    assert sem(a) == sem(b) and a["w"] == 240, "`diametro` explícito vence"
    assert sem(g.gerar("selo", dict(prm, largura=300), c)) == sem(g.gerar("selo", dict(prm, diametro=300), c)), "largura 300 desenha o selo de diâmetro 300"


def test_numeral_etiqueta_tipo_textura_e_mosaico_na_medida():
    c = ctx()
    # numeral: a largura da tinta dá a altura pela proporção da fonte; com as duas, cabe nas duas; o contorno entra na conta
    x0, y0, x1, y1 = g.fonte(c, "display").caixa_tinta("2027", 1.0)
    n = g.gerar("numeral", {"texto": "2027", "largura": 500}, c)["tinta"]
    assert abs((n[2] - n[0]) - 500) <= 0.5 and abs((n[3] - n[1]) - 500 * (y1 - y0) / (x1 - x0)) <= 1.0, "a altura sai da proporção dos algarismos na fonte"
    nc = g.gerar("numeral", {"texto": "2027", "largura": 500, "estilo": "contorno", "espessura": 4}, c)["tinta"]
    assert abs((nc[2] - nc[0]) - 500) <= 0.5, "no contorno a tinta passa do número em meia espessura de cada lado"
    na = g.gerar("numeral", {"texto": "2027", "altura": 300}, c)
    assert abs((na["tinta"][3] - na["tinta"][1]) - 300) <= 0.5 and na["h"] == math.ceil(300 + 2), "a altura segue sendo a dos algarismos (legado)"
    # etiqueta: a largura vem do tamanho do texto (a altura continua a da caixa); texto vivo, na fonte do kit
    e = g.gerar("etiqueta", {"texto": "Naming rights", "largura": 300}, c)
    assert e["w"] == 300 and float(re.search(r"font-size:([\d.]+)px", e["svg"]).group(1)) > 16 and "Naming rights".upper() in e["svg"]
    e2 = g.gerar("etiqueta", {"texto": "Naming rights", "largura": 300, "altura": 44}, c)
    assert (e2["w"], e2["h"]) == (300, 44)
    assert g.gerar("etiqueta", {"texto": "Naming rights", "altura": 44}, c)["h"] == 44, "só a altura: o legado (altura da caixa)"
    # tipo-textura e mosaico: o tamanho do texto e o módulo saem da medida
    tt = g.gerar("tipo-textura", {"texto": "Sprint", "largura": 500}, c)
    assert abs((tt["tinta"][2] - tt["tinta"][0]) - 500) <= 0.5
    ra = raster(tt["svg"])
    assert all(abs(x - y) <= 1.5 for x, y in zip(caixa_alfa(ra), tt["tinta"])), (caixa_alfa(ra), tt["tinta"])
    m = g.gerar("mosaico", {"recorte": ASA, "colunas": 6, "linhas": 2, "largura": 600}, c)
    assert (m["w"], m["h"]) == (600, 200), "6 x 2 módulos de 100: a largura dá o módulo"
    m2 = g.gerar("mosaico", {"recorte": ASA, "colunas": 6, "linhas": 2, "largura": 600, "altura": 150}, c)
    assert (m2["w"], m2["h"]) == (450, 150), "as duas: o módulo é o menor que serve às duas"


def test_simbolo_e_percurso_na_medida_e_o_legado_com_as_duas_medidas_nao_muda():
    c = ctx()
    mt = g.gerar("meio-tom-simbolo", {"recorte": ASA, "celula": 10, "altura": 200}, c)
    assert mt["h"] == 200 and mt["w"] < mt["h"], "a altura dá a largura pela proporção do símbolo"
    mt2 = g.gerar("meio-tom-simbolo", {"recorte": ASA, "celula": 10, "largura": 300, "altura": 200}, c)
    assert mt2["h"] == 200 and mt2["w"] <= 300
    ps = g.gerar("pattern-simbolo", {"recorte": ASA, "lado": 100, "largura": 300, "altura": 200}, c)
    assert (ps["w"], ps["h"]) == (300, 200) and ps["svg"].count("<use") > 4, "a medida pedida é a área que o padrão preenche"
    # percurso: com uma medida só, a outra segue a proporção do traçado; com as duas (o que os kits fazem), é a pedida como antes
    cur = {"curva": {"tipo": "orla"}, "rotulos": False}
    lw = g.gerar("linha-percurso", dict(cur, largura=600), c)
    P, _ = g._curva({"tipo": "orla"})
    span = P.max(0) - P.min(0)
    assert lw["w"] == 600 and abs(lw["h"] - ((600 - 112) * span[1] / span[0] + 112)) <= 1, (lw["w"], lw["h"])
    la = g.gerar("linha-percurso", dict(cur, altura=300), c)
    assert abs(la["w"] - ((300 - 112) * span[0] / span[1] + 112)) <= 1
    dois = g.gerar("linha-percurso", dict(cur, largura=900, altura=420), c)
    assert (dois["w"], dois["h"]) == (900, 420), "as duas: é a caixa pedida, como nos kits (Sprint: 900 x 420)"


def test_fio_e_colchetes_sem_geometria_da_pagina_na_medida():
    c = ctx()
    f = g.gerar("fio", {"largura": 300, "espessura": 3, "terminais": ["ponto", "seta"]}, c)
    ti = f["tinta"]
    assert abs((ti[2] - ti[0]) - 300) <= 0.5
    ink = caixa_alfa(raster(f["svg"]))
    assert abs((ink[2] - ink[0]) - 300) <= 1.5, ink
    fv = g.gerar("fio", {"altura": 200, "terminais": ["barra", "ponto"]}, c)
    assert abs((fv["tinta"][3] - fv["tinta"][1]) - 200) <= 0.5 and fv["h"] > fv["w"]
    fd = g.gerar("fio", {"largura": 300, "altura": 100}, c)["tinta"]
    assert fd[2] - fd[0] <= 300.5 and fd[3] - fd[1] <= 100.5 and fd[2] - fd[0] > 280, "as duas: a diagonal da caixa, com a tinta dentro dela"
    # com `pontos` a geometria da página vale e largura/altura não mexem nela
    uid = lambda r: re.sub(r'data-uid="[^"]+"', "", r["svg"])      # noqa: E731
    assert uid(g.gerar("fio", {"pontos": [[0, 0], [100, 0]], "largura": 999}, c)) == uid(g.gerar("fio", {"pontos": [[0, 0], [100, 0]]}, c))
    cl = g.gerar("colchetes", {"largura": 300}, c)
    assert abs((cl["tinta"][2] - cl["tinta"][0]) - 300) <= 0.5 and abs((cl["tinta"][3] - cl["tinta"][1]) - 225) <= 0.5, "4/3 por padrão"
    cl2 = g.gerar("colchetes", {"altura": 150, "proporcao": 2}, c)
    assert abs((cl2["tinta"][2] - cl2["tinta"][0]) - 300) <= 0.5 and abs((cl2["tinta"][3] - cl2["tinta"][1]) - 150) <= 0.5
    levanta("fio", {"largura": 5, "terminais": ["ponto", "ponto"], "espessura": 4}, "não passa dos terminais")
    levanta("colchetes", {}, "caixa")


def test_regua_divisoria_placar_celular_mapa_e_forma_na_medida():
    c = ctx()
    # régua: o comprimento da tinta é a largura; o estilo escala na outra dimensão; o rótulo da ponta não passa dela
    r = g.gerar("regua", {"passo": 12, "rotulos": {"inicio": 0, "passo": 5}, "largura": 500, "altura": 60}, c)
    ti = r["tinta"]
    assert abs((ti[2] - ti[0]) - 500) <= 0.5 and abs((ti[3] - ti[1]) - 60) <= 0.5, ti
    padrao = g.gerar("regua", {"passo": 12, "rotulos": {"inicio": 0, "passo": 5}, "largura": 500}, c)
    assert float(re.search(r"font-size:([\d.]+)px", r["svg"]).group(1)) > float(re.search(r"font-size:([\d.]+)px", padrao["svg"]).group(1))
    assert 'stroke-width="1.5"' in r["svg"], "a espessura do traço não cresce com o estilo"
    ink = caixa_alfa(raster(r["svg"]))
    assert abs((ink[2] - ink[0]) - 500) <= 1.5 and abs((ink[3] - ink[1]) - 60) <= 1.5, (ink, ti)
    v = g.gerar("regua", {"orientacao": "vertical", "passo": 12, "rotulos": {"inicio": 0, "passo": 5}, "altura": 300, "largura": 50}, c)
    assert abs((v["tinta"][3] - v["tinta"][1]) - 300) <= 0.5 and abs((v["tinta"][2] - v["tinta"][0]) - 50) <= 0.5, v["tinta"]
    # divisória: a largura é o comprimento, a altura é o ornamento
    d = g.gerar("divisoria", {"largura": 420, "altura": 24}, c)
    assert abs((d["tinta"][2] - d["tinta"][0]) - 420) <= 0.5 and abs((d["tinta"][3] - d["tinta"][1]) - 24) <= 0.5
    levanta("divisoria", {"largura": 420, "altura": 1}, "menor que a espessura")
    # placar: largura E altura exatas; a altura que não dá para 4 linhas legíveis é erro
    pl = g.gerar("placar", {"cabecalho": "Rodada", "linhas": ROWS, "largura": 640, "altura": 300}, c)["tinta"]
    assert abs((pl[2] - pl[0]) - 640) <= 0.5 and abs((pl[3] - pl[1]) - 300) <= 0.5, pl
    ink = caixa_alfa(raster(g.gerar("placar", {"cabecalho": "Rodada", "linhas": ROWS, "largura": 640, "altura": 300}, c)["svg"]))
    assert abs((ink[3] - ink[1]) - 300) <= 1.5 and abs((ink[2] - ink[0]) - 640) <= 1.5, ink
    levanta("placar", {"linhas": ROWS, "altura": 60}, "pequena demais")
    # celular: a altura dá a largura pela proporção; com as duas, cabe nas duas
    img = str(imagem_teste())
    ce = g.gerar("celular", {"imagem": img, "altura": 500}, c)
    assert ce["h"] == 500 and abs(ce["w"] - 500 / (19.5 / 9)) <= 1
    assert g.gerar("celular", {"imagem": img, "largura": 200, "altura": 300}, c)["h"] == 300
    # mapa: com uma medida, a tinta mede o pedido e a outra dimensão segue o conteúdo; com as duas, é a caixa
    mp = g.gerar("mapa", {"pontos": PONTOS, "aneis": [100, 300], "largura": 700}, c)
    assert abs((mp["tinta"][2] - mp["tinta"][0]) - 700) <= 0.5
    rotulos_sem_colisao(mp)
    assert (lambda r: (r["w"], r["h"]))(g.gerar("mapa", {"pontos": PONTOS, "aneis": [100, 300], "largura": 700, "altura": 480}, c)) == (700, 480)
    # campo: com as duas medidas, a maior escala que cabe nas duas
    cp_ = g.gerar("campo", {"esporte": "futebol", "largura": 500, "altura": 300}, c)["tinta"]
    assert abs((cp_[3] - cp_[1]) - 300) <= 0.5 and cp_[2] - cp_[0] <= 500.5
    # formas: tudo cresce junto (a proporção do desenho não muda) e a tinta mede o pedido
    for tipo, base in (("circulos", {"raios": [30, 60, 90]}), ("setas", {"quantidade": 4}), ("estrelas", {"quantidade": 5})):
        nat = g.gerar(tipo, base, c)["tinta"]
        gr = g.gerar(tipo, dict(base, largura=500), c)["tinta"]
        assert abs((gr[2] - gr[0]) - 500) <= 0.5
        assert abs((gr[3] - gr[1]) / (gr[2] - gr[0]) - (nat[3] - nat[1]) / (nat[2] - nat[0])) < 0.01, (tipo, "a proporção do desenho é a mesma")


# ================================================================= a data do evento pode vir incompleta (só o ano, ano e mês)
def test_data_do_evento_so_ano_ano_e_mes_e_completa():
    """O kit pode declarar `evento.data_inicio` incompleto (o render e o qa aceitam desde 08/10: a capa vira "Temporada 2027").
    Antes, `a, m, d = split("-")` quebrava com ValueError e derrubava a folha e todo microtexto ou selo com texto_de data."""
    assert g._data_br("2027-03-14") == "14.03.2027"                       # completa: como sempre
    assert g._data_br("2027-03") == "03/2027" and g._data_br("2027") == "2027"
    assert g._data_br("2027-3-4") == "04.03.2027" and g._data_br("2027-03-14T08:00:00") == "14.03.2027"
    assert g._data_br(None) is None and g._data_br("") is None
    assert g._data_br("14/03/2027") == "14/03/2027", "formato que não é ISO sai como veio, sem derrubar"
    for iso, esperado in (("2027", "2027"), ("2027-03", "03/2027"), ("2027-03-14", "14.03.2027")):
        c = ctx()
        c["evento"] = dict(c["evento"], data_inicio=iso)
        for tipo, prm in (("microtexto", {"texto_de": "data"}), ("selo", {"texto_de": "data", "centro": None}), ("faixa-diagonal", {"texto_de": "data"})):
            r = g.gerar(tipo, prm, c)
            assert esperado.upper() in r["texto"].replace("\n", ""), (iso, tipo, r["texto"])
    # a folha de revisão (exemplos_folha usa a data na faixa de microtexto) com data só do ano
    c = ctx()
    c["evento"] = dict(c["evento"], data_inicio="2027")
    itens = g.exemplos_folha(c, ASA)
    assert any("2027" in (prm.get("texto") or "") for tipo, prm in itens if tipo == "microtexto")
    with tempfile.TemporaryDirectory() as d:
        kit = Path(d) / "kit"
        kit.mkdir()
        shutil.copy(logo(), kit / "logo.png")
        (kit / "mediakit.json").write_text(json.dumps({
            "evento": {"nome": "Sprint Ubatuba Run", "data_inicio": "2027", "cidade": "Ubatuba", "uf": "SP", "edicao_numero": 2},
            "marca": {"fonte_display": "Kanit", "fonte_corpo": "Outfit", "cor_primaria": "#D4A64A", "logo_id": "logo"},
            "acervo": [{"id": "logo", "arquivo": "logo.png"}]}), encoding="utf-8")
        res, _ = g.folha(kit, None, fontes_dir(), Path(d) / "folha.png", ASA)
        assert (Path(d) / "folha.png").stat().st_size > 10000 and len(res) >= 30
        micro = next(r for r in res if r["svg"].count('data-grafismo="microtexto"'))
        assert "2027" in micro["texto"] and "." not in micro["texto"].split("·")[1], micro["texto"]


# ================================================================= acabamento (Frente G, 12/10/2026): os tipos novos
# Contrato: SVG válido (lxml), currentColor e nenhum hex, nada que rasterize o PDF (filter, gradiente, máscara, pattern),
# nenhum <text> com stroke (Type 3), parâmetro respeitado de forma contável, tinta dentro da caixa e conferida no raster,
# determinístico. Cada prova foi quebrada de propósito uma vez (mutante) antes de ficar verde.
PROIBIDAS = {"filter", "linearGradient", "radialGradient", "mask", "pattern", "foreignObject", "style", "script", "image"}


def _arvore(svg):
    from lxml import etree
    return etree.fromstring(svg.encode("utf-8"))      # SVG gerado aqui mesmo (entrada confiável)


def _local(el):
    from lxml import etree
    return etree.QName(el).localname if isinstance(el.tag, str) else None


def _text_sem_stroke(raiz_svg):
    """Nenhum <text> pinta contorno: nem atributo, nem estilo, nem herdado de um grupo com stroke (Type 3 no PDF)."""
    for t in raiz_svg.iter("{http://www.w3.org/2000/svg}text"):
        no = t
        while no is not None:
            assert no.get("stroke") in (None, "none"), f"<text> com stroke herdado de <{_local(no)}>"
            assert "stroke" not in (no.get("style") or ""), no.get("style")
            no = no.getparent()


def _poligonos(svg):
    """Os retângulos de traço (M x y L x y L x y L x y Z) como [(a, b)] da linha central de cada um."""
    out = []
    for d in re.findall(r' d="([^"]+)"', svg):
        for m in re.findall(r"M([^MZ]+)Z", d):
            pts = [tuple(map(float, q.split())) for q in m.split("L")]
            if len(pts) == 4:
                p0, p1, p2, p3 = (np.array(q) for q in pts)
                out.append(((p0 + p3) / 2, (p1 + p2) / 2))
    return out


def test_acabamento_contrato_pdf_seguro():
    vistos = set()
    for tipo, prm in EXEMPLOS:
        if tipo not in ACABAMENTO:
            continue
        vistos.add(tipo)
        prm = exemplo(tipo, prm)
        r = gerar_ok(tipo, prm)
        svg = r["svg"]
        assert svg == gerar_ok(tipo, prm)["svg"], f"{tipo}: duas chamadas iguais, dois SVG diferentes"
        el = _arvore(svg)
        tags = {_local(x) for x in el.iter()} - {None}
        assert not tags & PROIBIDAS, f"{tipo}: {sorted(tags & PROIBIDAS)} rasteriza o PDF ou foge do contrato"
        for x in el.iter():
            assert not {"filter", "mask"} & set(x.attrib), (tipo, x.attrib)
        assert "currentColor" in svg, f"{tipo}: o acento tem de sair como currentColor (a cor é do CSS)"
        assert not re.search(r"#[0-9A-Fa-f]{6}(?![0-9A-Za-z-])", svg), f"{tipo}: cor fixa em hex"
        _text_sem_stroke(el)
        for x in el.iter():           # clip-path no nó que tem transform: o clipPath gira e anda junto, e corta o desenho errado
            assert not ("clip-path" in x.attrib and "transform" in x.attrib), (tipo, x.attrib)
        t = r["tinta"]
        assert len(t) == 4 and 0 <= t[0] < t[2] <= r["w"] + 1e-6 and 0 <= t[1] < t[3] <= r["h"] + 1e-6, (tipo, t, r["w"], r["h"])
        assert ("linhas" in r) == (tipo in COM_LETRA), (tipo, r.keys())
        if "linhas" in r:
            assert r["linhas"]["cap"] < r["linhas"]["linha_base"], (tipo, r["linhas"])
        assert ("origem" in r) == (tipo in PRESOS), (tipo, r.keys())
        if tipo not in COM_LETRA:
            assert "<text" not in svg, tipo
        print(f"  {tipo:15} {r['w']}x{r['h']} tinta {t} linhas {r.get('linhas')} origem {r.get('origem')}")
    assert vistos == set(ACABAMENTO), f"exemplo faltando: {sorted(set(ACABAMENTO) - vistos)}"


def test_hachura_o_numero_de_linhas_segue_o_espacamento():
    for s, W, H, dens in ((12, 400, 300, 1), (17, 420, 260, 1), (24, 400, 300, 1), (12, 400, 300, 0.5)):
        r = gerar_ok("hachura", dict(largura=W, altura=H, espacamento=s, densidade=dens))
        por_familia = {}
        for a, b in _poligonos(r["svg"]):
            inclinacao = round(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180)
            por_familia[inclinacao] = por_familia.get(inclinacao, 0) + 1
        esperado = {}
        for ang in (-45, 45):
            t = math.radians(ang)
            total = math.floor((W * abs(math.sin(t)) + H * abs(math.cos(t))) / s + 1e-9)
            esperado[round(ang % 180)] = math.ceil(Fraction(str(dens)) * total)
        print(f"   espaçamento {s}, densidade {dens}, {W}x{H}: esperado {esperado}, no svg {por_familia}")
        assert por_familia == esperado, (s, dens, por_familia, esperado)
    levanta("hachura", dict(angulos=[45, 225]), "mesma família")
    levanta("hachura", dict(angulos=[30]), "dois ângulos")


def test_malha_perspectiva_bate_com_a_homografia_feita_a_mao():
    em = 1.5
    W, H = 24 * 8 + em, 24 * 6 + em                 # 8 x 6 células: há linha no meio dos dois sentidos
    plano = gerar_ok("malha", dict(largura=W, altura=H, passo=24))
    assert plano["tinta"] == [0.0, 0.0, W, H], plano["tinta"]
    assert len(_poligonos(plano["svg"])) == 9 + 7, "linhas = (colunas + 1) + (linhas + 1)"
    uv = [[0.25, 0], [0.75, 0], [1, 1], [0, 1]]
    r = gerar_ok("malha", dict(largura=W, altura=H, passo=24, perspectiva=uv))
    cantos = [np.array([em / 2 + u * (W - em), em / 2 + v * (H - em)]) for u, v in uv]
    segs = _poligonos(r["svg"])
    assert len(segs) == 16
    pontas = [q for s_ in segs for q in s_]
    for c in cantos:                                  # os 4 cantos da malha são os 4 cantos pedidos
        assert min(np.hypot(*(q - c)) for q in pontas) < 0.01, c
    # o centro do quadrado vai para o cruzamento das diagonais do quadrilátero (invariante da projeção, feito à mão):
    # diagonais sup-esq -> inf-dir e sup-dir -> inf-esq
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = cantos[0], cantos[2], cantos[1], cantos[3]
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / den
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / den
    centro = np.array([px, py])

    def distancia(p_, a, b):
        d = b - a
        return abs(d[0] * (p_[1] - a[1]) - d[1] * (p_[0] - a[0])) / np.hypot(*d)
    passam = [s_ for s_ in segs if distancia(centro, *s_) < 0.02]
    print(f"   centro projetado (diagonais) {centro.round(3)}; meio da altura seria {H / 2:.2f}; linhas que passam nele: {len(passam)}")
    assert len(passam) == 2 and abs(py - (em / 2 + (H - em) / 3)) < 1e-6, (len(passam), py)
    # as horizontais apertam para o fundo (o que a projeção faz e a interpolação linear não faria)
    ys = sorted({round(float(a[1]), 3) for a, b in segs if abs(a[1] - b[1]) < 1e-6})
    vaos = np.diff(ys)
    assert len(ys) == 7 and all(vaos[i] < vaos[i + 1] for i in range(len(vaos) - 1)), vaos
    levanta("malha", dict(perspectiva=[[0, 0], [1, 1], [1, 0], [0, 1]]), "convexo")


def test_aneis_quantidade_raio_e_esmaecer_em_degraus():
    for n in (3, 6, 9):
        r = gerar_ok("aneis", dict(largura=400, altura=300, quantidade=n))
        assert r["svg"].count("<circle") == n and r["tinta"] == [0.0, 0.0, 400.0, 300.0], (n, r["svg"].count("<circle"), r["tinta"])
    # centro fora da caixa: só saem os anéis que tocam a caixa (450, 600 e 750 de 150 a 900; o de 900 passa do canto mais longe)
    r = gerar_ok("aneis", dict(largura=400, altura=300, quantidade=6, centro=[-1, 0.5], raio_max=900))
    assert sorted(float(x) for x in re.findall(r'r="([\d.]+)"', r["svg"])) == [450.0, 600.0, 750.0], r["svg"][:400]
    # raio medido no raster: centro no meio de 400 x 400, 4 anéis até o canto (282,84): na horizontal, 70,71 e 141,42 do centro
    r = gerar_ok("aneis", dict(largura=400, altura=400, quantidade=4, espessura=2))
    linha = raster(r["svg"])[200, :, 3] >= 128
    centros = [(a + b) / 2 for a, b in corridas(linha) if (a + b) / 2 > 200]
    assert np.allclose(centros, [200 + 70.711, 200 + 141.421], atol=0.6), centros
    r = gerar_ok("aneis", dict(largura=400, altura=300, quantidade=6, esmaecer={"de": "centro", "passos": 3, "minimo": 0.24}))
    ops = [float(x) for x in re.findall(r'stroke-opacity="([\d.]+)"', r["svg"])]
    assert ops == [0.62, 0.24], ops                    # degrau 0 opaco (sem atributo), depois 0,62 e 0,24
    assert "<linearGradient" not in r["svg"] and "<radialGradient" not in r["svg"]
    levanta("aneis", dict(esmaecer={"de": "meio"}), "centro ou borda")


def test_pontos_radiais_raio_cai_com_a_distancia_e_para_no_alcance():
    W, H, passo, rmax, rmin, alc = 400, 300, 20, 7, 1, 150
    r = gerar_ok("pontos-radiais", dict(largura=W, altura=H, passo=passo, raio_max=rmax, raio_min=rmin, alcance=alc))
    pts = [tuple(map(float, x)) for x in re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"', r["svg"])]
    nx, ny = round((W - 2 * rmax) / passo) + 1, round((H - 2 * rmax) / passo) + 1
    gx, gy = (W - 2 * rmax) / (nx - 1), (H - 2 * rmax) / (ny - 1)
    esperados = [(rmax + i * gx, rmax + j * gy) for j in range(ny) for i in range(nx)
                 if math.hypot(rmax + i * gx - W / 2, rmax + j * gy - H / 2) <= alc]
    assert len(pts) == len(esperados), (len(pts), len(esperados))
    for x, y, rr in pts:
        d = math.hypot(x - W / 2, y - H / 2)
        assert abs(rr - (rmax + (rmin - rmax) * d / alc)) < 0.002 and d <= alc + 1e-6, (x, y, rr, d)
    perto = min(pts, key=lambda q: math.hypot(q[0] - W / 2, q[1] - H / 2))
    longe = max(pts, key=lambda q: math.hypot(q[0] - W / 2, q[1] - H / 2))
    assert perto[2] > 6.5 and longe[2] < 1.6, (perto, longe)
    q = gerar_ok("pontos-radiais", dict(largura=W, altura=H, forma="quadrado"))
    assert "<circle" not in q["svg"] and q["svg"].count("<rect") > 100


def test_cantoneira_quatro_cantos_em_cada_estilo():
    for estilo, tracos in (("dupla", 2), ("escada", 1), ("ponto", 1), ("seta", 1)):
        r = gerar_ok("cantoneira", dict(caixa=[100, 80, 360, 240], estilo=estilo))
        el = _arvore(r["svg"])
        cantos = [g_ for g_ in el.iter("{http://www.w3.org/2000/svg}g") if g_.get("data-canto")]
        assert sorted(c.get("data-canto") for c in cantos) == sorted(g.CANTOS), (estilo, [c.get("data-canto") for c in cantos])
        for c in cantos:
            d = c.find("{http://www.w3.org/2000/svg}path").get("d")
            assert d.count("M") == tracos, (estilo, d)
            if estilo == "escada":
                assert d.count("L") == 6, d                 # o L em dois degraus: 7 pontos
        assert r["origem"] == [99, 79] and r["tinta"] == [1.0, 1.0, 361.0, 241.0], (estilo, r["origem"], r["tinta"])
        assert (estilo == "ponto") == ("<circle" in r["svg"]) and (estilo == "seta") == ("<polygon" in r["svg"])
        _, n, centros = componentes(raster(r["svg"]))
        quadrantes = {(cx > r["w"] / 2, cy > r["h"] / 2) for cx, cy in centros}
        print(f"   {estilo:7} {n} peças no raster, quadrantes {sorted(quadrantes)}")
        assert len(quadrantes) == 4, (estilo, quadrantes)
    r = gerar_ok("cantoneira", dict(caixa=[0, 0, 360, 240], cantos=["sup-esq", "inf-dir"]))
    assert r["svg"].count("data-canto=") == 2
    levanta("cantoneira", dict(caixa=[0, 0, 100, 100], braco=64), "grande demais")


def test_moldura_dupla_dois_quadros_paralelos_no_vao_pedido():
    for cantos in ("reto", "chanfro", "arredondado"):
        r = gerar_ok("moldura-dupla", dict(largura=400, altura=240, espessuras=[4, 2], vao=8, cantos=cantos, chanfro=20))
        assert r["svg"].count("data-quadro=") == 2 and r["tinta"] == [1.0, 1.0, 401.0, 241.0], (cantos, r["tinta"])
        meio = raster(r["svg"])[121, :, 3] >= 128
        corr = corridas(meio)
        assert corr[:2] == [(1, 5), (13, 15)] and corr[-2:] == [(387, 389), (397, 401)], (cantos, corr)   # 4 px, vão 8, 2 px
    r = gerar_ok("moldura-dupla", dict(largura=400, altura=240, espessuras=[4, 2], vao=8, cantos="chanfro", chanfro=20))
    dentro = re.search(r'data-quadro="dentro" d="M([\d.]+) ([\d.]+)', r["svg"]).groups()
    d = (4 + 8 + 1) - 2                                   # distância entre as linhas centrais dos dois quadros
    perna = 20 - d * (2 - math.sqrt(2))                   # o chanfro de dentro paralelo ao de fora
    assert abs(float(dentro[0]) - (13 + perna)) < 0.002, (dentro, perna)
    assert gerar_ok("moldura-dupla", dict(largura=400, altura=240, vao="e2"))["svg"] != gerar_ok("moldura-dupla", dict(largura=400, altura=240))["svg"]
    levanta("moldura-dupla", dict(cantos="chanfro", chanfro=4), "pequeno demais")


def test_regua_borda_tempo_de_jogo_de_0_a_90():
    r = gerar_ok("regua-borda", dict(comprimento=1920, texto=""))      # a constante chega com `texto` (ignorado)
    rotulos = re.findall(r"<text [^>]*>([^<]+)</text>", r["svg"])
    assert rotulos == ["0'", "15'", "30'", "45'", "60'", "75'", "90'"], rotulos
    d = re.search(r'<path d="([^"]+)"', r["svg"]).group(1)
    assert d.count("M") == 1 + 19, d.count("M")                       # a linha de base e 19 marcas (de 5 em 5 minutos)
    xs = sorted({round(float(x), 3) for x in re.findall(r"M([\d.]+) [\d.]+L\1 ", d)})
    assert len(xs) == 19 and np.allclose(np.diff(xs), (1920 - 1.5) / 18, atol=0.002), np.diff(xs)
    assert abs((r["tinta"][2] - r["tinta"][0]) - 1920) <= 0.1 and raiz(r["svg"]).get("data-grafismo") == "regua-borda"
    r2 = gerar_ok("regua-borda", dict(largura=900, de=0, ate=45, maior_cada=15, sufixo=" min"))
    assert re.findall(r"<text [^>]*>([^<]+)</text>", r2["svg"]) == ["0 min", "15 min", "30 min", "45 min"]
    levanta("regua-borda", dict(maior_cada=7), "múltiplo")


def test_eco_copias_em_degrau_texto_vivo_ou_contorno_da_fonte():
    c = dict(ctx(), textos={"titulo": "Copa AME Sua Marca", "tese": "A cidade inteira joga junto"})
    r = gerar_ok("eco", dict(texto_de="titulo", copias=3, deslocamento="e4", direcao="dir", tamanho=100), c)
    textos = re.findall(r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*data-copia="(\d)"(?: fill-opacity="([\d.]+)")?[^>]*>([^<]+)<', r["svg"])
    assert len(textos) == 3 and r["texto"] == "COPA AME SUA MARCA", (textos, r["texto"])
    por_copia = {int(k): (float(x), float(y), float(op or 1), t) for x, y, k, op, t in textos}
    assert [por_copia[k][2] for k in range(3)] == [0.24, 0.12, 0.06]
    assert all(abs(por_copia[k][0] - por_copia[0][0] - 32 * k) < 0.002 and por_copia[k][1] == por_copia[0][1] for k in range(3))
    assert [int(k) for _, _, k, _, _ in textos] == [2, 1, 0], "a cópia 0 é a última (por cima)"
    for n in (1, 2):
        assert gerar_ok("eco", dict(texto_de="evento", copias=n))["svg"].count("<text") == n
    # contorno: o desenho é <path> tirado da fonte (nunca <text> com stroke), e não é texto
    cp = gerar_ok("eco", dict(texto_de="tese", estilo="contorno-path", copias=2, tamanho=80), c)
    assert "<text" not in cp["svg"] and cp["svg"].count("data-copia=") == 2 and cp["texto"] == "" and cp["fontes"] == []
    assert all(" stroke=" in p_ for p_ in re.findall(r"<path [^>]+>", cp["svg"]))
    # lettering cai no display quando a receita não declara
    lt = gerar_ok("eco", dict(texto_de="evento", fonte="lettering", copias=1))
    assert "font-family:'Kanit'" in lt["svg"].replace("&#x27;", "'")
    levanta("eco", dict(texto_de="titulo"), "textos.titulo")
    levanta("eco", dict(texto_de="evento", opacidades=[0.3, 0.12, 0.06]), "degraus")
    levanta("eco", dict(texto_de="evento", espacamento=-0.05), "-0,02")
    levanta("eco", dict(texto_de="evento", copias=4), "de 1 a 3")


def test_eco_contorno_sem_emenda_por_dentro_da_letra():
    """Fonte com contornos sobrepostos (a Bricolage Grotesque estática da r2: a haste por cima da barriga do B) mostrava
    as emendas por dentro da letra no eco em contorno. Prova: o miolo da letra (a letra cheia, encolhida 4 px) não tem
    traço nenhum do contorno."""
    from scipy.ndimage import binary_erosion
    c = ctx("r2")
    comum = dict(texto="UBATUBA", copias=1, tamanho=160, opacidades=[1])
    cheio, linha = gerar_ok("eco", comum, c), gerar_ok("eco", dict(comum, estilo="contorno-path", espessura=1.5), c)
    assert (cheio["w"], cheio["h"]) != (0, 0)
    a_cheio, a_linha = rasters([cheio["svg"], linha["svg"]], familias=("Bricolage Grotesque", "Plus Jakarta Sans"))
    # alinha as duas caixas pela tinta (a do contorno tem meia espessura a mais de cada lado)
    dx = round(linha["tinta"][0] - cheio["tinta"][0] + 0.75)
    dy = round(linha["tinta"][1] - cheio["tinta"][1] + 0.75)
    miolo = binary_erosion(a_cheio[..., 3] >= 128, iterations=4)
    h, w = miolo.shape
    trecho = a_linha[dy:dy + h, dx:dx + w, 3] >= 64
    dentro = int((trecho[:miolo.shape[0], :miolo.shape[1]] & miolo[:trecho.shape[0], :trecho.shape[1]]).sum())
    borda = int(trecho.sum())
    print(f"   contorno: {borda} px de traço, {dentro} dentro do miolo das letras")
    assert borda > 1000 and dentro == 0, (borda, dentro)


def test_lettering_e_texto_de_titulo_e_tese():
    c = ctx()
    f, d = g.fonte(c, "lettering"), g.fonte(c, "display")
    assert (f.familia, f.peso) == (d.familia, d.peso), "sem lettering na receita, o papel cai no display"
    c2 = dict(c, fontes=dict(c["fontes"], lettering="Fraunces"))
    assert g.fonte(c2, "lettering").familia == "Fraunces"
    assert "lettering" in g.PAPEIS
    c3 = dict(c, textos={"titulo": "Copa AME", "tese": "Torneio da cidade"})
    assert gerar_ok("microtexto", dict(texto_de="tese", largura=900), c3)["texto"] == "TORNEIO DA CIDADE"
    levanta("microtexto", dict(texto_de="hino"), "titulo ou tese")


def test_chromium_texto_curva_fecha_na_medida_e_letras_em_pe():
    casos = [("arco", dict(texto_de="evento", raio=420, tamanho=40)), ("tigela", dict(texto_de="evento", raio=-420, tamanho=40)),
             ("onda", dict(texto_de="evento", forma="onda", tamanho=40, amplitude=20))]
    rs = [gerar_ok("texto-curva", p_) for _, p_ in casos]
    f = g.fonte(ctx(), "display")
    js = """() => Array.from(document.querySelectorAll('svg')).map(s => { const t = s.querySelector('text');
        return {caminho: s.querySelector('path[id]').getTotalLength(), texto: t.getComputedTextLength(), n: t.getNumberOfChars(),
                rot: Array.from({length: t.getNumberOfChars()}, (_, i) => t.getRotationOfChar(i))}; })"""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        pg.set_content(f"<!doctype html><html><head><meta charset='utf-8'><style>{g.css_fontes(fontes_dir(), {'Kanit'})}</style></head>"
                       f"<body>{''.join(r['svg'] for r in rs)}</body></html>", wait_until="load")
        pg.evaluate(JS_FONTES)
        med = pg.evaluate(js)
        b.close()
    for (nome, p_), r, m in zip(casos, rs, med):
        s = float(re.search(r"font-size:([\d.]+)px", r["svg"]).group(1))
        ls = float(re.search(r"letter-spacing:([-\d.]+)px", r["svg"]).group(1))
        T = f.largura(r["texto"], s, ls)
        Lp = T + 2 * round(0.5 * s, 3)
        print(f"   {nome:6} caminho {m['caminho']:.2f} (conta {Lp:.2f})  texto {m['texto']:.2f} (conta {T:.2f})  "
              f"rotação {min(m['rot']):.1f} a {max(m['rot']):.1f}")
        assert abs(m["caminho"] - Lp) <= 1.0 and abs(m["texto"] - T) <= 1.0, (nome, m["caminho"], Lp, m["texto"], T)
        assert all(-90 < x < 90 for x in m["rot"]), (nome, m["rot"])      # letra em pé
        if nome != "onda":
            assert abs(m["rot"][0] + m["rot"][-1]) < 2.5, (nome, m["rot"][0], m["rot"][-1])   # simétrico: o meio no ápice
            assert (m["rot"][0] < 0) == (nome == "arco"), (nome, m["rot"][0])


def test_chromium_tinta_do_acabamento_confere_com_o_raster():
    casos = [
        ("hachura", dict(largura=400, altura=240, espessura=2)),
        ("hachura", dict(largura=400, altura=240, espessura=2, espacamento=14, esmaecer="dir", recorte=[20, 20, 300, 180])),
        ("malha", dict(largura=400, altura=240)),
        ("malha", dict(largura=420, altura=260, espessura=1.5, espessura_maior=3, esmaecer="baixo")),
        ("malha", dict(largura=400, altura=240, espessura=1.5, perspectiva=[[0.2, 0.1], [0.9, 0], [1, 1], [0, 0.85]])),
        ("aneis", dict(largura=400, altura=240, centro=[0, 1], espessura=2)),
        ("aneis", dict(largura=400, altura=240, angulo_ini=-60, angulo_fim=60, raio_max=180, espessura=2.5)),
        ("aneis", dict(largura=400, altura=240, esmaecer="centro", espessura=2)),
        ("pontos-radiais", dict(largura=400, altura=240, raio_min=1.5)),
        ("pontos-radiais", dict(largura=400, altura=240, raio_min=1.5, forma="quadrado", centro=[0, 0])),
        ("cantoneira", dict(caixa=[0, 0, 300, 200], estilo="escada")),
        ("cantoneira", dict(caixa=[0, 0, 300, 200], estilo="seta", cantos=["sup-dir"])),
        ("moldura-dupla", dict(largura=300, altura=200, cantos="arredondado")),
        ("regua-borda", dict(comprimento=900)),
        ("regua-borda", dict(comprimento=900, lado="cima", altura=50)),
        ("eco", dict(texto_de="evento", tamanho=90, opacidades=[1, 1, 1], direcao=30)),
        ("eco", dict(texto_de="evento", tamanho=90, estilo="contorno-path", opacidades=[1, 1, 1], espessura=2)),
        ("texto-curva", dict(texto_de="evento", raio=300)),
        ("texto-curva", dict(texto_de="evento", raio=-300)),
        ("texto-curva", dict(texto_de="local", forma="onda", tamanho=30, amplitude=30)),
        ("ondas", dict(largura=400, altura=240, defasagem=25)),
        ("ondas", dict(largura=400, altura=240, espessura=2, esmaecer="baixo")),
        ("curvas-nivel", dict(largura=400, altura=240, semente=5, maior_cada=2)),
        ("fita", dict(largura=500, texto_de="evento")),
        ("fita", dict(forma="cruzada", largura=500, altura=260)),
        ("fita", dict(forma="dobra", largura=500, altura=240, texto_de="local")),
        ("carimbo", dict(texto=SELO, centro_texto="2027")),
        ("carimbo", dict(forma="retangular", texto="Homologado", centro_texto="Aprovado")),
        ("numeral-eco", dict(texto="2027", altura=160)),
        ("numeral-eco", dict(texto="02", altura=160, copias=2, opacidades=[0.72, 0.24])),
        ("meio-tom-foto", dict(png=str(imagem_teste()), largura=300)),
        ("meio-tom-foto", dict(png=str(imagem_teste()), largura=300, angulo=45, celula=12)),
        ("campo", dict(largura=500, perspectiva=[[0.2, 0], [0.8, 0], [1, 1], [0, 1]])),
        ("campo", dict(esporte="pista", largura=500, perspectiva=[[0.1, 0.1], [0.9, 0], [1, 1], [0, 0.9]])),
    ]
    rs = [gerar_ok(t, p_) for t, p_ in casos]
    for (t, p_), r, a in zip(casos, rs, rasters([r["svg"] for r in rs])):
        ink = caixa_alfa(a)
        dif = max(abs(x - y) for x, y in zip(ink, r["tinta"]))
        print(f"   {t:15} tinta declarada {r['tinta']}  raster {ink}  diferença máxima {dif:.2f} px")
        assert dif <= 1.5, (t, p_, r["tinta"], ink)


def _pagina_acabamento(omitir=(), onda=1):
    c = dict(ctx(), textos={"titulo": "Copa AME Sua Marca", "tese": "A cidade inteira joga junto"})
    itens = [("ondas", dict(largura=420, altura=200, defasagem=20)), ("curvas-nivel", dict(largura=420, altura=200, maior_cada=3)),
             ("fita", dict(forma="cruzada", largura=420, altura=200, espessura=48, texto="Cota ouro")),
             ("carimbo", dict(texto=SELO, centro_texto="2027", diametro=240, falhas=0.1)),
             ("carimbo", dict(forma="retangular", texto="Homologado", centro_texto="Aprovado", texto_baixo="14.03.2027", largura=360, altura=170)),
             ("numeral-eco", dict(texto="2027", altura=150, copias=3)),
             ("meio-tom-foto", dict(png=str(imagem_teste()), altura=330, celula=12)),
             ("campo", dict(largura=520, perspectiva=[[0.2, 0], [0.8, 0], [1, 1], [0, 1]]))] if onda == 2 else [("hachura", dict(largura=360, altura=200, esmaecer="dir")),
             ("malha", dict(largura=360, altura=200, perspectiva=[[0.25, 0], [0.75, 0], [1, 1], [0, 1]])),
             ("aneis", dict(largura=360, altura=200, centro=[0, 1], esmaecer="centro")),
             ("pontos-radiais", dict(largura=360, altura=200)),
             ("cantoneira", dict(largura=300, altura=200, estilo="dupla")),
             ("moldura-dupla", dict(largura=300, altura=200, cantos="chanfro")),
             ("eco", dict(texto_de="titulo", altura=120, opacidades=[1, 0.46, 0.24])),
             ("eco", dict(texto_de="tese", altura=60, estilo="contorno-path", direcao=45, opacidades=[1, 0.46, 0.24])),
             ("texto-curva", dict(texto_de="evento", raio=360, tamanho=34)),
             ("texto-curva", dict(texto_de="local", forma="onda", tamanho=28))]
    colocados, x, y, alt = [], 40, 80, 0
    for tipo, prm in itens:
        r = g.gerar(tipo, prm, c)
        if x + r["w"] > 1880:
            x, y, alt = 40, y + alt + 30, 0
        colocados.append((tipo, x, y, r))
        x, alt = x + r["w"] + 30, max(alt, r["h"])
    assert y + alt <= 1020, y + alt
    regua = g.gerar("regua-borda", dict(comprimento=1920), c)
    colocados.append(("regua-borda", 0, 0, regua))
    colocados = [q for q in colocados if q[0] not in omitir]
    pal = c["paleta"]
    corpo = "".join(f'<div class="el" style="left:{x_}px;top:{y_}px">{r["svg"]}</div>' for _, x_, y_, r in colocados)
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{g.css_fontes(fontes_dir(), {'Kanit', 'Outfit'})}\n"
            "@page { size: 1920px 1080px; margin: 0 }\n* { font-synthesis: none; box-sizing: border-box; }\n"
            f"html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: {pal['escuro']}; color: {pal['marca']}; }}\n"
            ".el { position: absolute; line-height: 0; } svg { display: block; }"
            f"</style></head><body>{corpo}</body></html>")


def _marcas_da_regua(img, y=6):
    """Centro (x, em px contínuos) de cada marca da régua de borda numa linha da imagem: as marcas sobem do fundo."""
    m = np.asarray(img.convert("L"), float)[y, :]
    m = m - np.median(m)
    d = np.diff(np.r_[0, (m > 30).astype(int), 0])
    return np.array([float((m[a:b] * (np.arange(a, b) + 0.5)).sum() / m[a:b].sum())
                     for a, b in zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0])])


def _no_lugar_da_tela(b, escala, desloc):
    """O raster do PDF reamostrado na escala da tela. O Chromium imprime o conteúdo da página de 1920 px numa escala um
    pouco menor (medido: 0,9985, cerca de 3 px a menos na largura toda; o legado também tem e passava porque só tinha traço
    fino); letra grande desloca 2 px na ponta e a comparação acusaria o deslocamento, não um desenho diferente."""
    from scipy.ndimage import affine_transform
    return affine_transform(np.asarray(b.convert("L"), float), [escala, escala], offset=[0.0, desloc], order=1, mode="nearest")


def _desvio_ate_1px(ga, gb):
    """Maior diferença depois de aceitar até 1 px de deslocamento (passo 0,5) em cada ponto: o Chromium encosta a linha de
    base da letra no pixel inteiro e o poppler não, e letra grande desfocada acusa meio pixel como desenho diferente. Traço
    que sumiu continua sumido em qualquer deslocamento."""
    from scipy.ndimage import shift
    passos = (-1.0, -0.5, 0.0, 0.5, 1.0)
    return float(np.min([np.abs(ga - shift(gb, (dy, dx), order=1, mode="nearest")) for dy in passos for dx in passos], axis=0).max())


def test_pdf_do_acabamento_vetor_texto_vivo_sem_type3_e_mesmo_desenho():
    _prova_pdf_acabamento(1, ("COPAAMESUAMARCA", "SPRINTUBATUBARUN", "UBATUBA/SP", "0'", "45'", "90'"), ("malha", "moldura-dupla"),
                          proibido="ACIDADEINTEIRA")


def test_pdf_do_acabamento_onda2_vetor_texto_vivo_sem_type3_e_sem_imagem():
    _prova_pdf_acabamento(2, ("COTAOURO", "SPRINTUBATUBARUN", "2027", "HOMOLOGADO", "APROVADO", "14.03.2027"), ("ondas", "curvas-nivel"))


def _prova_pdf_acabamento(onda, esperados, omitir, proibido=None):
    from scipy.ndimage import gaussian_filter
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        png, pdf = _exportar(_pagina_acabamento(onda=onda), d)
        saida = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True).stdout
        assert "Type 3" not in saida and saida.strip().splitlines()[2:], saida
        imgs = subprocess.run(["pdfimages", "-list", str(pdf)], capture_output=True, text=True).stdout.strip().splitlines()[2:]
        assert imgs == [], f"o acabamento virou imagem no PDF: {imgs}"
        texto = re.sub(r"\s", "", subprocess.run(["pdftotext", "-raw", str(pdf), "-"], capture_output=True, text=True).stdout)
        faltam = [e for e in esperados if e not in texto]
        assert not faltam, f"texto vivo que não chegou ao PDF: {faltam}"
        assert not proibido or proibido not in texto.upper(), "o eco em contorno é desenho, não texto"
        subprocess.run(["pdftoppm", "-r", "96", "-png", "-singlefile", str(pdf), str(d / "pdf")], check=True)
        a, b = Image.open(png), Image.open(d / "pdf.png")
        assert a.size == b.size == (1920, 1080), (a.size, b.size)
        ma, mb = _marcas_da_regua(a), _marcas_da_regua(b)
        assert len(ma) == len(mb) == 19, (len(ma), len(mb))
        escala, desloc = np.polyfit(ma[:-1], mb[:-1], 1)       # a última marca encosta na borda da página
        ga = gaussian_filter(np.asarray(a.convert("L"), float), 2.0)
        fora = _desvio_ate_1px(ga, gaussian_filter(_no_lugar_da_tela(b, escala, desloc), 2.0))
        (d / "sem").mkdir()
        _, pdf2 = _exportar(_pagina_acabamento(omitir=omitir, onda=onda), d / "sem")
        subprocess.run(["pdftoppm", "-r", "96", "-png", "-singlefile", str(pdf2), str(d / "pdf2")], check=True)
        controle = _desvio_ate_1px(ga, gaussian_filter(_no_lugar_da_tela(Image.open(d / "pdf2.png"), escala, desloc), 2.0))
        print(f"   pdffonts sem Type 3; pdfimages: nenhuma; escala do PDF {escala:.5f}; PDF x tela: {fora:.1f} de 255; "
              f"controle sem {' e '.join(omitir)}: {controle:.1f}")
        assert abs(escala - 1) < 0.005, escala
        # controle: sem dois desenhos de traço fino (0,75 a 2 px), a mesma conta tem de reprovar; traço fino desfocado dá
        # de 60 a 80 de pico (o legado usa 80 com o campo, que tem as marcas cheias)
        assert fora < 45 and controle > 50 and controle > 2 * fora, (fora, controle)

# ---------------------------------------------------------------- acabamento, onda 2
def imagem_meio_a_meio(nome="meio-a-meio.png"):
    """Foto sintética: metade esquerda preta, direita branca (o meio-tom tem de pôr ponto só de um lado)."""
    p = Path(_TMP) / nome
    if not p.exists():
        im = Image.new("RGB", (400, 200), (255, 255, 255))
        ImageDraw.Draw(im).rectangle([0, 0, 199, 199], fill=(0, 0, 0))
        im.save(p)
    return p


def test_ondas_o_numero_segue_o_espacamento_e_fecham_a_caixa():
    for H, A, s, esp in ((400, 12, 16, 1.5), (260, 20, 30, 2), (300, 8, 11, 1)):
        r = gerar_ok("ondas", dict(largura=480, altura=H, amplitude=A, espacamento=s, espessura=esp))
        n = r["svg"].count("M")
        esperado = round((H - 2 * A - esp) / s) + 1
        print(f"   altura {H}, amplitude {A}, espaçamento {s}: {n} ondas (conta {esperado}), tinta {r['tinta']}")
        assert n == esperado and r["tinta"] == [0.0, 0.0, 480.0, float(H)], (n, esperado, r["tinta"])
    # no raster, na coluna em que todas cruzam a linha de centro (x = meio comprimento de onda), o passo é o real
    r = gerar_ok("ondas", dict(largura=480, altura=260, amplitude=20, espacamento=30, espessura=2, comprimento=160))
    centros = [(a + b) / 2 for a, b in corridas(raster(r["svg"])[:, 80, 3] >= 128)]
    passo = (260 - 40 - 2) / (round((260 - 40 - 2) / 30))
    assert np.allclose(np.diff(centros), passo, atol=0.6) and abs(centros[0] - 21) < 0.6, (centros, passo)
    e = gerar_ok("ondas", dict(largura=480, altura=260, esmaecer={"direcao": "baixo", "passos": 3, "minimo": 0.24}))
    assert [float(x) for x in re.findall(r'stroke-opacity="([\d.]+)"', e["svg"])] == [0.62, 0.24]
    levanta("ondas", dict(esmaecer="dir"), "só na vertical")
    levanta("ondas", dict(amplitude=40, comprimento=40, espacamento=6), "se encostam")


def test_curvas_nivel_niveis_contornos_e_semente():
    for niveis in (5, 9, 12):
        r = gerar_ok("curvas-nivel", dict(largura=480, altura=320, niveis=niveis))
        assert sorted(int(x) for x in re.findall(r'data-nivel="(\d+)"', r["svg"])) == list(range(niveis)), niveis
    desenho = lambda r: re.findall(r' d="([^"]+)"', r["svg"])       # noqa: E731  (o desenho, sem o uid que muda com os params)
    a, b = gerar_ok("curvas-nivel", dict(semente=3)), gerar_ok("curvas-nivel", dict(semente=4))
    assert a["svg"] == gerar_ok("curvas-nivel", dict(semente=3))["svg"], "mesma semente, mesmo svg"
    assert desenho(a) != desenho(b), "a semente decide o relevo"
    m = gerar_ok("curvas-nivel", dict(niveis=9, maior_cada=3))
    assert len(re.findall(r'data-nivel="\d+" stroke-width="2"', m["svg"])) == 3
    # o mesmo relevo em outra medida: o desenho escala junto (a grade do campo é da caixa, não do px)
    p1 = gerar_ok("curvas-nivel", dict(largura=300, altura=200))
    p2 = gerar_ok("curvas-nivel", dict(largura=600, altura=400))
    d1 = [float(x) for x in re.findall(r"M([\d.]+) ", p1["svg"])[:6]]
    d2 = [float(x) for x in re.findall(r"M([\d.]+) ", p2["svg"])[:6]]
    assert np.allclose(np.array(d1) * 2, d2, atol=0.01), (d1, d2)


def test_fita_bordas_fios_e_a_de_cima_interrompe_a_de_baixo():
    r = gerar_ok("fita", dict(largura=600, espessura=64, espessura_fio=2, texto_de="evento"))
    assert (r["w"], r["h"]) == (600, 64) and r["tinta"] == [0.0, 0.0, 600.0, 64.0] and r["texto"] == "SPRINT UBATUBA RUN"
    col = raster(r["svg"])[:, 3, 3] >= 128                  # x = 3: a coluna passa antes da primeira letra
    corr = corridas(col)
    assert corr[0] == (0, 2) and corr[1] == (9, 11) and corr[-1] == (62, 64) and corr[-2] == (53, 55), corr
    lin = r["linhas"]
    assert abs(lin["linha_base"] - lin["cap"] - g.fonte(ctx(), "corpo", 700).cap_px(round(64 * 0.3, 3))) < 0.15   # linhas: 0,1 px
    # o texto aparece inteiro entre os fios: no raster, há tinta da linha de cap à linha de base, e desde a primeira letra
    a = raster(r["svg"])[..., 3] >= 128
    miolo = a[12:52, :]
    linhas_com_tinta = np.nonzero(miolo.any(axis=1))[0] + 12
    assert linhas_com_tinta.min() <= math.ceil(lin["cap"]) + 1 and linhas_com_tinta.max() >= math.floor(lin["linha_base"]) - 1, \
        (linhas_com_tinta.min(), linhas_com_tinta.max(), lin)
    assert np.nonzero(miolo.any(axis=0))[0].min() < 12, "a primeira letra foi cortada"
    c = gerar_ok("fita", dict(forma="cruzada", largura=600, altura=300, texto="Cota ouro"))
    segs = re.findall(r"M([-\d.]+) ([-\d.]+)L([-\d.]+) ([-\d.]+)", c["svg"])
    assert len(segs) == 4 * 2 + 4, len(segs)                 # as 4 linhas da de baixo partidas em 2; as 4 da de cima inteiras
    assert c["svg"].count("<text") == 1 and "rotate(-20)" in c["svg"], "o texto vai na de cima"
    d = gerar_ok("fita", dict(forma="dobra", largura=600, altura=260))
    sub = [q for x in re.findall(r'd="(M[^"]+)" stroke-width', d["svg"]) for q in x.split("M")[1:]]
    assert 'data-parte="vinco"' in d["svg"] and [q.count("L") for q in sub] == [2, 2, 2, 2, 1], sub   # 4 linhas dobradas e o vinco
    levanta("fita", dict(espessura=16, recuo="e2"), "não cabe")


def test_carimbo_falhas_pela_semente_e_texto_vivo():
    base = dict(texto="Sprint Ubatuba Run · 2ª edição ·", centro_texto="2027", diametro=280)
    for falhas in (0.05, 0.12):
        r = gerar_ok("carimbo", dict(base, falhas=falhas, semente=11))
        aneis = re.findall(r'<circle data-anel="1" cx="[\d.]+" cy="[\d.]+" r="([\d.]+)"[^>]*stroke-dasharray="([^"]+)"', r["svg"])
        assert len(aneis) == 2, aneis
        for raio, da in aneis:
            v = [float(x) for x in da.split()]
            C = 2 * math.pi * float(raio)
            assert abs(sum(v) - C) < 0.05 and abs(sum(v[1::2]) / C - falhas) < 0.002, (raio, sum(v), C, sum(v[1::2]) / C)
        assert r["svg"].count("<textPath") == 2 and ">2027</text>" in r["svg"] and r["texto"].split("\n")[-1] == "2027"
    um, outro = (gerar_ok("carimbo", dict(base, falhas=0.1, semente=s_))["svg"] for s_ in (1, 2))
    tracejado = lambda svg: re.findall(r'stroke-dasharray="([^"]+)"', svg)       # noqa: E731  (sem o uid, que muda com os params)
    assert tracejado(um) != tracejado(outro), "a semente decide onde a borracha falha"
    assert um == gerar_ok("carimbo", dict(base, falhas=0.1, semente=1))["svg"]
    assert "dasharray" not in gerar_ok("carimbo", dict(base, falhas=0))["svg"]
    q = gerar_ok("carimbo", dict(forma="retangular", texto="Homologado", centro_texto="Aprovado", texto_baixo="14.03.2027", falhas=0.08))
    assert q["texto"] == "HOMOLOGADO\nAPROVADO\n14.03.2027" and q["svg"].count("<text") == 3 and q["tinta"] == [0.0, 0.0, 440.0, 200.0]
    levanta("carimbo", dict(base, falhas=0.2), "0,15")


def test_numeral_eco_copias_preenchidas_e_tinta_do_numero_da_frente():
    r = gerar_ok("numeral-eco", dict(texto="2027", altura=200, copias=3, deslocamento="e4", direcao=45))
    textos = re.findall(r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*data-copia="(\d)"(?: fill-opacity="([\d.]+)")?', r["svg"])
    assert [int(k) for _, _, k, _ in textos] == [3, 2, 1, 0] and "stroke" not in r["svg"], textos
    assert [float(op or 1) for _, _, _, op in textos] == [0.06, 0.12, 0.24, 1.0]
    x0, y0 = float(textos[-1][0]), float(textos[-1][1])
    for x, y, k, _ in textos:
        assert abs(float(x) - x0 - 32 * int(k) * math.cos(math.radians(45))) < 0.002 and abs(float(y) - y0 - 32 * int(k) * math.sin(math.radians(45))) < 0.002
    f = g.fonte(ctx(), "display")
    _, iy0, _, iy1 = f.caixa_tinta("2027", 1.0)
    assert abs((r["tinta"][3] - r["tinta"][1]) - 200) < 0.3 and r["w"] > r["tinta"][2] + 60, (r["tinta"], r["w"])   # as cópias passam da tinta
    # cópia com opacidade de pelo menos 0,5 é tinta: a medida passa a contar o número da frente MAIS o deslocamento dela
    forte = gerar_ok("numeral-eco", dict(texto="2027", altura=200, copias=1, opacidades=[0.72]))
    x0_, y0_, x1_, y1_ = f.caixa_tinta("2027", 1.0)
    passo = 32 * math.sin(math.radians(45))
    s_ = math.floor((200 - passo) / (y1_ - y0_) * 1000) / 1000
    assert abs((forte["tinta"][3] - forte["tinta"][1]) - 200) < 0.3, forte["tinta"]
    assert abs((forte["tinta"][2] - forte["tinta"][0]) - ((x1_ - x0_) * s_ + passo)) < 0.3, (forte["tinta"], (x1_ - x0_) * s_ + passo)


def test_meio_tom_foto_escuro_vira_ponto_grande_sem_imagem_no_svg():
    # metade preta, metade branca: no modo escuro só a metade preta (um quadrado) tem ponto, e o ponto é o maior possível
    r = gerar_ok("meio-tom-foto", dict(png=str(imagem_meio_a_meio()), largura=400, celula=16))
    pts = [tuple(map(float, x)) for x in re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"', r["svg"])]
    t = r["tinta"]
    assert pts and "<image" not in r["svg"] and abs((t[2] - t[0]) - 400) < 0.3, t
    assert abs((t[3] - t[1]) / (t[2] - t[0]) - 1) < 0.08, f"os pontos cobrem mais que a metade preta: {t}"
    celula = float(np.median(np.diff(sorted({x for x, _, _ in pts}))))      # a célula final: nunca menor que a pedida
    assert 16 - 1e-6 <= celula < 16 * 1.1 and abs(max(rr for _, _, rr in pts) - 0.48 * celula) < 0.02, (celula, max(rr for _, _, rr in pts))
    # quatro faixas de cinza (do preto ao quase branco): o raio cai faixa a faixa no escuro e sobe no claro
    faixas = Path(_TMP) / "faixas.png"
    im = Image.new("L", (400, 100))
    for i, nivel in enumerate((0, 85, 170, 235)):
        ImageDraw.Draw(im).rectangle([i * 100, 0, i * 100 + 99, 99], fill=nivel)
    im.save(faixas)
    for modo, sinal in (("escuro", -1), ("claro", 1)):
        q = gerar_ok("meio-tom-foto", dict(png=str(faixas), largura=400, celula=12, modo=modo))
        pts = [tuple(map(float, x)) for x in re.findall(r'<circle cx="([\d.]+)" cy="[\d.]+" r="([\d.]+)"', q["svg"])]
        xs_, rs_ = np.array(pts).T
        corr = float(np.corrcoef(xs_, rs_)[0, 1])
        raios_ = sorted({round(float(x), 1) for x in rs_})
        print(f"   {modo}: {len(pts)} pontos, raios {raios_[:2]} a {raios_[-2:]}, correlação raio x posição {corr:+.3f}")
        assert sinal * corr > 0.9, (modo, corr)                 # do preto ao claro, o ponto encolhe (escuro) ou cresce (claro)
    alto = gerar_ok("meio-tom-foto", dict(png=str(imagem_teste()), altura=500, celula=14))
    assert abs((alto["tinta"][3] - alto["tinta"][1]) - 500) < 0.3
    levanta("meio-tom-foto", dict(png=str(imagem_meio_a_meio()), celula=11), "pelo menos 12")
    preta = Path(_TMP) / "preta.png"
    Image.new("RGB", (400, 400), (0, 0, 0)).save(preta)
    levanta("meio-tom-foto", dict(png=str(preta), largura=2400, celula=12), "15000")


CAMPO_LEGADO = {    # sha256 do svg do campo gerado pelo grafismos.py de antes da perspectiva (commit 5cfaa7a), ctx fixo
    '{"largura": 600}': "808d50c4e76a48810c03c782817250fabdcb0b3bf3085e6b142e2d7ef65eeef1",
    '{"esporte": "futsal", "recorte": "area", "altura": 300}': "6d2b9c93ec25e0466b65a86bf89435cf25540073f80361b95c6bbf6a2ddfdd4d",
    '{"esporte": "pista", "recorte": "canto", "largura": 420}': "efce65702008565ef987ccea17d650e6a81c21f132b431c5963f6a2007a10c63",
    '{"esporte": "futebol", "largura": 420, "angulo": -12}': "3a7c7aac1b09a5ca337f2607745cd48a38db339635b870012297187cb3716655",
    '{"esporte": "futebol", "recorte": "circulo", "largura": 260, "espessura": 3}': "7ae27aca6634b86c88a2e9e23b303c1c96d79d236bc3b6ed7f6cbab875537df1",
}


def test_campo_perspectiva_e_o_legado_byte_a_byte():
    import hashlib
    fixo = {"fontes": {"display": "Kanit", "peso_display": 800, "corpo": "Outfit"},
            "paleta": {"marca": "#D4A64A", "escuro": "#0E0D08", "papel": "#F6EEE2", "texto": "#FFFFFF", "apoio": "#2067AA"},
            "evento": {"nome": "Sprint Ubatuba Run"}, "logo_png": None, "fontes_dir": "/nao/usa"}
    for prm, sha in CAMPO_LEGADO.items():
        assert hashlib.sha256(g.gerar("campo", json.loads(prm), fixo)["svg"].encode()).hexdigest() == sha, f"o campo sem perspectiva mudou: {prm}"
    uv = [[0.2, 0], [0.8, 0], [1, 1], [0, 1]]
    r = gerar_ok("campo", dict(largura=600, perspectiva=uv))
    cont = re.search(r'data-parte="contorno" d="M([^"]+)Z"', r["svg"]).group(1)
    Q = [np.array(list(map(float, q.split()))) for q in cont.split("L")]
    assert len(Q) == 4, Q
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = Q[0], Q[2], Q[1], Q[3]
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    centro = np.array([((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / den,
                       ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / den])
    m = re.search(r'<circle data-parte="marca-central" cx="([\d.]+)" cy="([\d.]+)"', r["svg"])
    marca = np.array([float(m.group(1)), float(m.group(2))])
    print(f"   marca central {marca}, cruzamento das diagonais do contorno projetado {centro.round(3)}")
    assert np.hypot(*(marca - centro)) < 0.01, (marca, centro)
    assert abs(Q[0][1] - Q[1][1]) < 0.01 and Q[1][0] - Q[0][0] < (Q[2][0] - Q[3][0]) * 0.65, Q        # o fundo é mais estreito
    levanta("campo", dict(largura=600, perspectiva=uv, angulo=10), "cantos")
    assert gerar_ok("campo", dict(largura=400, recorte="meio", perspectiva=uv))["svg"].count("data-parte=") > 5


if __name__ == "__main__":
    falhas = 0
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            try:
                f(); print("ok  ", nome)
            except AssertionError as e:
                falhas += 1; print("FALHOU", nome, e)
    shutil.rmtree(_TMP, ignore_errors=True)
    print("PROVAS:", "VERDES" if not falhas else f"{falhas} FALHA(S)")
    sys.exit(1 if falhas else 0)

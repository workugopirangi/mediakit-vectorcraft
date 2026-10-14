#!/usr/bin/env python3
"""Provas do golden.py. Rodar: ~/.venvs/mediakit/bin/python test_golden.py

Sem render real: PNG sintéticos pequenos, JSON montado na mão e um PDF de duas páginas feito com o Pillow (para o poppler
ler de verdade). Provam que a CONFERÊNCIA acusa o que deve acusar (PNG alterado em 1 pixel acima do piso, linha de QA a
mais, texto de página, fontes, imagens) e aceita o que deve aceitar (diferença dentro do piso, HTML diferente com raster
igual). `test_mutantes_sao_pegos` quebra a conferência de propósito, de quatro jeitos, e exige que a prova acuse cada um.
"""
import json, sys, tempfile
from pathlib import Path

import numpy as np
from PIL import Image

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import golden  # noqa: E402

PDFFONTS = """name                                 type              encoding         emb sub uni object ID
------------------------------------ ----------------- ---------------- --- --- --- ---------
AAAAAA+DMSans-Regular                CID TrueType      Identity-H       yes yes yes     %s  0
BAAAAA+Anton-Regular                 CID TrueType      Identity-H       yes yes yes     %s  0
"""
PDFIMAGES = """page   num  type   width height color comp bpc  enc interp  object ID x-ppi y-ppi size ratio
--------------------------------------------------------------------------------------------
   1     0 image    1920  1280  icc     3   8  jpeg   no         %s  0    96    96  116K 1.6%%
   1     1 smask     900   300  gray    1   8  image  no        15  0    80    80 3609B 1.3%%
"""


# ------------------------------------------------------------------------------------------------- apoio
def png(caminho, alterados=0, tam=(40, 30), semente=7):
    """PNG sintético; `alterados` pixels trocados de cor (os primeiros, em ordem de linha)."""
    a = np.random.default_rng(semente).integers(0, 255, (tam[1], tam[0], 4), dtype=np.uint8)
    a[..., 3] = 255
    for i in range(alterados):
        y, x = divmod(i, tam[0])
        a[y, x, :3] = 255 - a[y, x, :3]
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(a, "RGBA").save(caminho)


def dados(pasta, alterados=0, tam=(40, 30)):
    """Extração sintética de uma 'rodada': uma página PNG em <pasta>/png, um PDF, HTML, QA e plano."""
    png(Path(pasta) / "png" / "kit-r1-01.png", alterados, tam)
    return {"html": {"kit-r1.html": "aaa"},
            "png": {"kit-r1-01.png": golden.sha256_arquivo(Path(pasta) / "png" / "kit-r1-01.png")},
            "fundo": {"kit-r1-01.png": "fff"},
            "plano": {"plano-elementos-r1.json": {"paginas": [{"n": 1, "x": 10.5}]}},
            "qa": ["AVISO  render: algo conhecido"],
            "pdf": {"kit-r1.pdf": {"bytes": 1000, "paginas": 1, "tamanho_pagina": "1440 x 810 pts",
                                    "fontes": ["Anton-Regular | CID TrueType | Identity-H | yes | yes | yes"],
                                    "imagens": ["1 0 image 1920 1280 icc 3 8 jpeg no 96 96"], "texto": ["TITULO DA CAPA\n"]}}}


def conferir_dois(d, alterados, piso, mexer=None, comparar=None):
    """Golden (sem alteração) contra uma rodada nova com `alterados` pixels trocados."""
    comparar = comparar or golden.comparar_kit
    g, n = Path(d) / "g", Path(d) / "n"
    dg, dn = dados(g), dados(n, alterados)
    if mexer:
        mexer(dn)
    return comparar(dg, dn, g / "png", n / "png", piso)


def falhas(divs, tipo=None):
    return [x for x in divs if x[0] == "FALHA" and (tipo is None or x[1] == tipo)]


# ------------------------------------------------------------------------------------------------- provas da conferência
def prova_acusa_pixel_acima_do_piso(comparar=None):
    with tempfile.TemporaryDirectory() as d:
        divs = conferir_dois(d, alterados=6, piso=5, comparar=comparar)
    f = falhas(divs, "PNG")
    assert f and "6 px" in f[0][3] and "piso 5" in f[0][3], divs


def prova_aceita_dentro_do_piso(comparar=None):
    with tempfile.TemporaryDirectory() as d:
        divs = conferir_dois(d, alterados=5, piso=5, comparar=comparar)
    assert not falhas(divs), divs


def prova_acusa_qa_a_mais(comparar=None):
    with tempfile.TemporaryDirectory() as d:
        divs = conferir_dois(d, 0, 0, mexer=lambda n: n["qa"].append("FALHA  pdf kit-r1: fonte de fallback"), comparar=comparar)
    f = falhas(divs, "QA")
    assert f and f[0][2] == "linha a mais" and "fallback" in f[0][3], divs


def test_acusa_pixel_alterado_acima_do_piso():
    prova_acusa_pixel_acima_do_piso()


def test_aceita_diferenca_dentro_do_piso():
    prova_aceita_dentro_do_piso()


def test_piso_zero_acusa_um_pixel():
    with tempfile.TemporaryDirectory() as d:
        divs = conferir_dois(d, alterados=1, piso=0)
    assert falhas(divs, "PNG"), divs


def test_acusa_linha_de_qa_a_mais_e_a_menos():
    prova_acusa_qa_a_mais()
    with tempfile.TemporaryDirectory() as d:
        divs = conferir_dois(d, 0, 0, mexer=lambda n: n["qa"].clear())
    f = falhas(divs, "QA")
    assert f and f[0][2] == "linha a menos", divs


def test_igual_nao_diverge_em_nada():
    with tempfile.TemporaryDirectory() as d:
        assert conferir_dois(d, 0, 0) == []


def test_acusa_texto_fontes_imagens_e_paginas_do_pdf():
    def texto(n): n["pdf"]["kit-r1.pdf"]["texto"] = ["TITULO DA CAPA MUDADO\n"]
    def fontes(n): n["pdf"]["kit-r1.pdf"]["fontes"] = ["Arial | TrueType | WinAnsi | yes | yes | no"]
    def imagens(n): n["pdf"]["kit-r1.pdf"]["imagens"] = []
    def paginas(n): n["pdf"]["kit-r1.pdf"]["paginas"] = 2
    for mexer, tipo in ((texto, "TEXTO"), (fontes, "FONTES"), (imagens, "IMAGENS"), (paginas, "PDF")):
        with tempfile.TemporaryDirectory() as d:
            divs = conferir_dois(d, 0, 0, mexer=mexer)
        assert falhas(divs, tipo), (tipo, divs)


def test_pdf_ou_pagina_que_some_ou_aparece_e_falha():
    with tempfile.TemporaryDirectory() as d:
        divs = conferir_dois(d, 0, 0, mexer=lambda n: (n["pdf"].clear(), n["png"].clear()))
    assert falhas(divs, "PDF") and falhas(divs, "PNG"), divs
    with tempfile.TemporaryDirectory() as d:
        divs = conferir_dois(d, 0, 0, mexer=lambda n: n["png"].update({"kit-r1-02.png": "x"}))
    assert any(x[3] == "página nova" for x in falhas(divs, "PNG")), divs


def test_png_de_outro_tamanho_falha_mesmo_com_piso_enorme():
    with tempfile.TemporaryDirectory() as d:
        g, n = Path(d) / "g", Path(d) / "n"
        dg = dados(g)
        dn = dados(n, 0, tam=(40, 31))
        divs = golden.comparar_kit(dg, dn, g / "png", n / "png", piso=10 ** 9)
    f = falhas(divs, "PNG")
    assert f and "40x30 -> 40x31" in f[0][3], divs


def test_html_diferente_com_raster_igual_e_so_aviso():
    with tempfile.TemporaryDirectory() as d:
        divs = conferir_dois(d, 0, 0, mexer=lambda n: n["html"].update({"kit-r1.html": "bbb"}))
    assert not falhas(divs), divs
    assert any(x[0] == "AVISO" and x[1] == "HTML" and "raster igual" in x[3] for x in divs), divs


def test_fundo_plano_bytes_e_entrada_sao_aviso_nao_falha():
    def mexer(n):
        n["fundo"]["kit-r1-01.png"] = "ggg"
        n["plano"]["plano-elementos-r1.json"]["paginas"][0]["x"] = 11.0
        n["pdf"]["kit-r1.pdf"]["bytes"] = 1100
    with tempfile.TemporaryDirectory() as d:
        g, n = Path(d) / "g", Path(d) / "n"
        dg, dn = dados(g), dados(n)
        mexer(dn)
        divs = golden.comparar_kit(dg, dn, g / "png", n / "png", 0, {"mediakit.json": "1"}, {"mediakit.json": "2"})
    assert not falhas(divs), divs
    tipos = {x[1] for x in divs if x[0] == "AVISO"}
    assert {"FUNDO", "PLANO", "BYTES", "ENTRADA"} <= tipos, divs
    plano = [x for x in divs if x[1] == "PLANO"][0]
    assert "paginas[0].x" in plano[3], plano


def test_conta_paginas_dentro_do_piso():
    with tempfile.TemporaryDirectory() as d:
        g, n = Path(d) / "g", Path(d) / "n"
        dg, dn = dados(g), dados(n, 4)
        assert golden.contar_dentro_do_piso(dg, dn, g / "png", n / "png", 5) == (1, 4)
        assert golden.contar_dentro_do_piso(dg, dn, g / "png", n / "png", 3) == (0, 0)


def test_mutantes_sao_pegos():
    """A conferência quebrada de propósito tem de ser acusada pelas próprias provas. Se uma prova passa com o mutante,
    ela não prova nada."""
    real = golden.comparar_kit

    def ignora_pixels(*a, **k):
        antigo = golden.pixels_diferentes
        golden.pixels_diferentes = lambda x, y: (0, (40, 30), (40, 30))
        try:
            return real(*a, **k)
        finally:
            golden.pixels_diferentes = antigo

    def piso_enorme(dg, dn, pg, pn, piso, *r):
        return real(dg, dn, pg, pn, piso * 1000 + 1000, *r)

    def piso_estrito(dg, dn, pg, pn, piso, *r):      # `<=` virou `<`: o limite exato deixa de ser aceito
        return real(dg, dn, pg, pn, piso - 1, *r)

    def ignora_qa(*a, **k):
        return [x for x in real(*a, **k) if x[1] != "QA"]

    casos = [(ignora_pixels, prova_acusa_pixel_acima_do_piso), (piso_enorme, prova_acusa_pixel_acima_do_piso),
             (piso_estrito, prova_aceita_dentro_do_piso), (ignora_qa, prova_acusa_qa_a_mais)]
    for mutante, prova in casos:
        try:
            prova(comparar=mutante)
        except AssertionError:
            continue
        raise AssertionError(f"a prova {prova.__name__} deixou passar o mutante {mutante.__name__}")
    # e o comparador de verdade passa em todas
    for prova in (prova_acusa_pixel_acima_do_piso, prova_aceita_dentro_do_piso, prova_acusa_qa_a_mais):
        prova(comparar=real)


# ------------------------------------------------------------------------------------------------- normalização
def test_normalizar_plano_remove_data_e_caminho():
    def plano(clone, quando, sessao):
        return {"receita": "r1", "gerado_em": quando, "session_id": sessao, "data": quando[:10],
                "paginas": [{"n": 1, "uso": "saida/cache-elementos/goleiro@1164.png", "sha256": "ab12",
                             "arquivo": f"{clone}/acervo/foto.jpg",
                             "nota": f"medido em {quando} por 123e4567-e89b-12d3-a456-42661417400{sessao[-1]} em /Users/ugo/x/y",
                             "grafismo": {"params": {"linhas": [{"data": "Sub-11"}]}}}]}
    a = golden.normalizar_plano(plano("/private/tmp/aaa/kit", "2026-10-12T10:11:12", "sessao-1"), ["/private/tmp/aaa/kit"])
    b = golden.normalizar_plano(plano("/private/tmp/bbb/kit", "2026-11-30T23:59:59", "sessao-2"), ["/private/tmp/bbb/kit"])
    assert a == b, (a, b)
    txt = json.dumps(a, ensure_ascii=False)
    for ruim in ("2026-", "/private", "/Users", "123e4567", "gerado_em", "session_id", "sessao"):
        assert ruim not in txt, (ruim, txt)
    # o que é conteúdo e identidade fica
    assert a["paginas"][0]["uso"] == "saida/cache-elementos/goleiro@1164.png" and a["paginas"][0]["sha256"] == "ab12"
    assert a["paginas"][0]["grafismo"]["params"]["linhas"][0]["data"] == "Sub-11"
    # e uma mudança real de geometria continua aparecendo
    c = plano("/private/tmp/aaa/kit", "2026-10-12T10:11:12", "sessao-1")
    c["paginas"][0]["x"] = 9
    assert golden.normalizar_plano(c, ["/private/tmp/aaa/kit"]) != a


def test_normalizar_qa_so_falha_e_aviso_ordenado_sem_caminho():
    saida = ("OK   algo\nAVISO  render: zzz\nFALHA  p.3: fonte em /tmp/clone/kit/fontes/x.ttf\n\n"
             "AVISO  render: aaa\n2 falha(s), 2 aviso(s)\n")
    assert golden.normalizar_qa(saida, ["/tmp/clone/kit"]) == [
        "AVISO  render: aaa", "AVISO  render: zzz", "FALHA  p.3: fonte em <KIT>/fontes/x.ttf"]


def test_normalizar_pdffonts_e_pdfimages_ignoram_o_numero_do_objeto():
    a = golden.normalizar_pdffonts(PDFFONTS % (10, 27))
    assert a == golden.normalizar_pdffonts(PDFFONTS % (34, 35))
    assert a == ["Anton-Regular | CID TrueType | Identity-H | yes | yes | yes",
                 "DMSans-Regular | CID TrueType | Identity-H | yes | yes | yes"], a
    assert golden.normalizar_pdffonts((PDFFONTS % (10, 27)).replace("yes yes yes     10", "yes yes no      10")) != a
    i = golden.normalizar_pdfimages(PDFIMAGES % 5)
    assert i == golden.normalizar_pdfimages(PDFIMAGES % 99) and len(i) == 2, i
    assert i[0] == "1 0 image 1920 1280 icc 3 8 jpeg no 96 96", i


def test_extrair_pdf_le_paginas_texto_e_imagens_de_um_pdf_de_verdade():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "dois.pdf"
        a = Image.new("RGB", (200, 100), (200, 30, 30))
        b = Image.new("RGB", (200, 100), (30, 30, 200))
        a.save(p, "PDF", save_all=True, append_images=[b])
        r = golden.extrair_pdf(p)
    assert r["paginas"] == 2 and len(r["texto"]) == 2 and r["bytes"] > 0, r
    assert len(r["imagens"]) == 2 and r["imagens"][1].startswith("2 "), r["imagens"]
    assert r["fontes"] == [], r["fontes"]


def test_ruido_conta_pixels_por_pagina_e_o_maximo_vira_piso():
    with tempfile.TemporaryDirectory() as d:
        r1, r2 = Path(d) / "r1", Path(d) / "r2"
        png(r1 / "a.png"); png(r2 / "a.png")
        png(r1 / "b.png"); png(r2 / "b.png", alterados=3)
        png(r1 / "c.png"); png(r2 / "c.png", alterados=41)        # 41 pixels: passa da primeira linha de 40
        ruido = golden.calcular_ruido(r1, r2)
    assert ruido == {"a.png": 0, "b.png": 3, "c.png": 41}, ruido
    assert max(ruido.values()) == 41


def test_diff_json_aponta_o_caminho():
    a = {"p": [{"x": 1, "y": [1, 2]}], "q": "a"}
    assert golden.diff_json(a, {"p": [{"x": 1, "y": [1, 3]}], "q": "a"}) == [".p[0].y[1]"]
    assert golden.diff_json(a, {"p": [{"x": 1, "y": [1]}], "q": "a"})[0].startswith(".p[0].y (tamanho 2 -> 1)")
    assert golden.diff_json(a, a) == []


# ------------------------------------------------------------------------------------------------- arquivos
def test_apagar_seguro_so_apaga_dentro_da_raiz():
    with tempfile.TemporaryDirectory() as d:
        raiz, fora = Path(d) / "raiz", Path(d) / "fora"
        (raiz / "kit" / "saida").mkdir(parents=True); fora.mkdir()
        (fora / "importante.txt").write_text("x")
        for alvo in (fora, raiz, Path(d)):
            try:
                golden.apagar_seguro(alvo, raiz)
            except RuntimeError:
                pass
            else:
                raise AssertionError(f"apagou {alvo}")
        assert (fora / "importante.txt").exists() and raiz.exists()
        golden.apagar_seguro(raiz / "kit" / "saida", raiz)
        assert not (raiz / "kit" / "saida").exists() and (raiz / "kit").exists()


def test_clonar_deixa_a_saida_de_fora_nao_toca_a_origem_e_recusa_clone_dentro_do_kit():
    with tempfile.TemporaryDirectory() as d:
        kit = Path(d) / "kit"
        (kit / "acervo").mkdir(parents=True); (kit / "saida" / "png").mkdir(parents=True)
        (kit / "mediakit.json").write_text("{}"); (kit / "acervo" / "f.txt").write_text("foto")
        (kit / "saida" / "png" / "p.png").write_text("velho")
        antes = golden.hash_entrada(kit)
        raiz = Path(d) / "clones"; raiz.mkdir()
        golden.clonar(kit, raiz / "kit", raiz)
        assert (raiz / "kit" / "mediakit.json").read_text() == "{}" and (raiz / "kit" / "acervo" / "f.txt").exists()
        assert not (raiz / "kit" / "saida").exists()
        (raiz / "kit" / "mediakit.json").write_text('{"mudou": 1}')     # mexer no clone não mexe no kit
        assert (kit / "mediakit.json").read_text() == "{}"
        golden.clonar(kit, raiz / "kit", raiz)                          # reclonar substitui o clone anterior
        assert (raiz / "kit" / "mediakit.json").read_text() == "{}"
        assert golden.hash_entrada(kit) == antes and (kit / "saida" / "png" / "p.png").exists()
        try:
            golden.clonar(kit, kit / "saida" / "clone", kit / "saida")
        except RuntimeError:
            pass
        else:
            raise AssertionError("aceitou clonar para dentro do próprio kit")


def test_hash_entrada_ignora_a_saida_e_pega_mudanca():
    with tempfile.TemporaryDirectory() as d:
        kit = Path(d)
        (kit / "saida").mkdir(); (kit / "saida" / "x").write_text("1"); (kit / "a.json").write_text("1")
        h = golden.hash_entrada(kit)
        assert list(h) == ["a.json"]
        (kit / "saida" / "x").write_text("2")
        assert golden.hash_entrada(kit) == h
        (kit / "a.json").write_text("2")
        assert golden.hash_entrada(kit) != h


def test_sha256_do_html_ignora_o_caminho_do_clone():
    with tempfile.TemporaryDirectory() as d:
        a, b = Path(d) / "a.html", Path(d) / "b.html"
        a.write_text("<img src='/tmp/um/kit/x.png'>"); b.write_text("<img src='/tmp/dois/kit/x.png'>")
        assert golden.sha256_sem_caminho(a, ["/tmp/um/kit"]) == golden.sha256_sem_caminho(b, ["/tmp/dois/kit"])
        assert golden.sha256_sem_caminho(a, []) != golden.sha256_sem_caminho(b, [])


def test_gravar_e_carregar_golden_dao_a_mesma_coisa():
    with tempfile.TemporaryDirectory() as d:
        base = Path(d) / "k"
        dg = dados(base / "origem")
        entrada = {"mediakit.json": "abc", "acervo/f.jpg": "def"}
        golden.gravar_golden(base, dg, entrada)
        (base / "ruido.json").write_text(json.dumps({"max": 7}))
        dados2, entrada2, ruido = golden.carregar_golden(base)
    assert dados2 == dg and entrada2 == entrada and ruido["max"] == 7


def test_impressao_do_pipeline_muda_com_o_codigo_e_ignora_pycache():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "render.py").write_text("a = 1")
        (p / "__pycache__").mkdir(); (p / "__pycache__" / "render.pyc").write_text("x")
        h1 = golden.impressao_pipeline(p)
        (p / "__pycache__" / "render.pyc").write_text("y")
        assert golden.impressao_pipeline(p) == h1 and h1["arquivos"] == 1
        (p / "render.py").write_text("a = 2")
        assert golden.impressao_pipeline(p)["sha256"] != h1["sha256"]


def test_escolher_kits_aceita_virgula_e_recusa_nome_desconhecido():
    todos = list(golden.KITS)
    assert golden.escolher_kits(None, todos) == todos
    assert golden.escolher_kits(["receitas-teste,corre-por-elas", "sprint-2027"], todos) == ["receitas-teste", "corre-por-elas", "sprint-2027"]
    try:
        golden.escolher_kits(["nao-existe"], todos)
    except SystemExit as e:
        assert "nao-existe" in str(e)
    else:
        raise AssertionError("aceitou kit desconhecido")


def test_kits_cobrem_os_cinco_e_receitas_nao_levam_todas():
    assert sorted(golden.KITS) == ["copa-ame-v2", "corre-por-elas", "receitas-teste", "sprint-2027", "travessia-da-lua"]
    for nome in ("sprint-2027", "copa-ame-v2", "receitas-teste"):    # kits com `receitas`: --todas apagaria as receitas do render
        assert "--todas" not in golden.KITS[nome]["flags"], nome
    assert "--todas" in golden.KITS["travessia-da-lua"]["flags"]


if __name__ == "__main__":
    falhas_n = 0
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            try:
                f(); print("ok  ", nome)
            except AssertionError as e:
                falhas_n += 1; print("FALHOU", nome, e)
            except Exception as e:  # noqa: BLE001  erro inesperado também reprova, com o tipo à mostra
                falhas_n += 1; print("FALHOU", nome, f"{type(e).__name__}: {e}")
    print("PROVAS:", "VERDES" if not falhas_n else f"{falhas_n} FALHA(S)")
    sys.exit(1 if falhas_n else 0)

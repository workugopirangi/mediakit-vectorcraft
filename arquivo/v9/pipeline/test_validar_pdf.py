#!/usr/bin/env python3
"""Provas do validar_pdf.py. Rodar: ~/.venvs/mediakit/bin/python test_validar_pdf.py
Gera PDFs mínimos no Chromium (Playwright) numa pasta temporária: não toca em kit nem gasta cota."""
import base64, io, shutil, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image

AQUI = Path(__file__).parent
PY = sys.executable
TMP = Path(tempfile.mkdtemp(prefix="test-validar-pdf-"))

EVENTO = "Sprint Ubatuba Run"
TESE = "Quem corre aqui leva a cidade inteira junto"
APOIO = "<p>Página de teste com texto vivo suficiente para a extração do pdftotext funcionar como num kit real.</p>"

_pdfs = {}


def _textura_data_uri():
    ruido = (np.random.default_rng(7).random((1080, 1920)) * 255).astype("uint8")
    buf = io.BytesIO(); Image.fromarray(ruido, "L").convert("RGB").save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _casos():
    canvas = (f'<canvas id="c" width="1700" height="320"></canvas><script>const x=document.getElementById("c").getContext("2d");'
              f'x.font="110px Helvetica";x.fillText("{EVENTO}",0,130);x.font="44px Helvetica";x.fillText("{TESE}",0,240);</script>')
    return {
        "vivo": f"<h1>{EVENTO}</h1><p>{TESE}, e a cidade devolve.</p>{APOIO}",
        "canvas": f"{canvas}{APOIO}",
        "filtro": f'<h1 style="filter: blur(1px)">{EVENTO}</h1><p style="filter: blur(1px)">{TESE}</p>{APOIO}',
        "micro": (f'<h1>A largada mais bonita do litoral</h1><p style="text-transform:uppercase;letter-spacing:.12em;font-size:18px">'
                  f'sprint ubatuba run · 14.03.2027 · ubatuba/sp</p><p>{TESE}.</p>{APOIO}'),
        "textura": f'<img src="{_textura_data_uri()}" style="position:absolute;inset:0;width:1920px;height:1080px;z-index:-1"><h1>{EVENTO}</h1>{APOIO}',
        # selo do grafismos.py: texto vivo num arco (textPath). O pdftotext padrão embaralha a ordem; o -raw não.
        "selo": (f'{APOIO}<svg width="600" height="600" viewBox="0 0 600 600"><defs><path id="a" d="M300,300 m-220,0 '
                 f'a220,220 0 1,1 440,0 a220,220 0 1,1 -440,0"/></defs><text font-family="Helvetica" font-size="44" '
                 f'letter-spacing="4"><textPath href="#a">{EVENTO.upper()} · 2ª EDIÇÃO · 2027 ·</textPath></text></svg>'),
    }


def pdf(nome):
    if not _pdfs:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page(viewport={"width": 1920, "height": 1080})
            for caso, corpo in _casos().items():
                pg.set_content(f"""<!doctype html><html><head><meta charset="utf-8"><style>
                    @page {{ size: 1920px 1080px; margin: 0 }}
                    html, body {{ margin: 0; width: 1920px; height: 1080px; position: relative; font-family: Helvetica, Arial, sans-serif }}
                    body {{ display: flow-root; overflow: hidden }}
                    h1 {{ font-size: 120px; margin: 96px 96px 32px }} p {{ font-size: 32px; margin: 0 96px 24px }} canvas {{ margin: 96px }}
                    </style></head><body>{corpo}</body></html>""")
                pg.pdf(path=str(TMP / f"{caso}.pdf"), width="1920px", height="1080px", print_background=True, prefer_css_page_size=True)
                _pdfs[caso] = TMP / f"{caso}.pdf"
            b.close()
    return _pdfs[nome]


def valida(nome, *args):
    r = subprocess.run([PY, str(AQUI / "validar_pdf.py"), str(pdf(nome)), *map(str, args)], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def test_texto_vivo_passa():
    cod, out = valida("vivo", "--texto", EVENTO, "--texto", TESE)
    assert cod == 0 and "FALHA" not in out, out


def test_texto_desenhado_em_canvas_reprova():
    cod, out = valida("canvas", "--texto", EVENTO, "--texto", TESE)
    assert cod == 1 and EVENTO in out and TESE in out, out


def test_texto_sob_filtro_reprova():
    """O defeito real que a regra pega: filtro CSS faz o Skia rasterizar a região e o título deixa de ser texto."""
    cod, out = valida("filtro", "--texto", EVENTO)
    assert cod == 1 and EVENTO in out, out


def test_sem_texto_obrigatorio_o_comportamento_antigo_fica():
    cod, out = valida("canvas")
    assert cod == 0, out


def test_caixa_alta_e_tracking_nao_atrapalham():
    cod, out = valida("micro", "--texto", EVENTO.upper(), "--texto", "Sprint Ubatuba Run")
    assert cod == 0, out


def test_texto_em_arco_do_selo_passa():
    """Falso alarme que a Frente B previu: o nome do evento só no selo, em arco, é texto vivo e tem de passar."""
    cod, out = valida("selo", "--texto", EVENTO)
    assert cod == 0, out


def test_texto_ausente_reprova_mesmo_com_outro_texto_vivo():
    cod, out = valida("vivo", "--texto", "Corrida da Lua Cheia")
    assert cod == 1 and "Corrida da Lua Cheia" in out, out


def test_textura_de_pagina_inteira_so_passa_quando_declarada():
    cod, out = valida("textura", "--cenas", "0")
    assert "1 páginas" in out, "o PDF de teste precisa ter 1 página, senão a textura conta 2 vezes: " + out
    assert cod == 1 and "página inteira" in out, out
    cod, out = valida("textura", "--cenas", "0", "--texturas", "1")
    assert cod == 0, out


def pdf_duas_paginas(nome, pagina2):
    """PDF de 2 páginas 1920×1080: p.1 com título vivo, p.2 com o corpo dado (título vivo, em canvas ou trocado)."""
    destino = TMP / f"duas-{nome}.pdf"
    if destino.exists():
        return destino
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1920, "height": 1080})
        pg.set_content(f"""<!doctype html><html><head><meta charset="utf-8"><style>
            @page {{ size: 1920px 1080px; margin: 0 }} html, body {{ margin: 0; font-family: Helvetica, Arial, sans-serif }}
            section {{ width: 1920px; height: 1080px; overflow: hidden; break-after: page; position: relative }}
            h1 {{ font-size: 120px; margin: 96px 96px 32px }} p {{ font-size: 32px; margin: 0 96px }} canvas {{ margin: 96px }}
            </style></head><body><section><h1>Quem está em campo</h1>{APOIO}</section><section>{pagina2}</section></body></html>""")
        pg.pdf(path=str(destino), width="1920px", height="1080px", print_background=True, prefer_css_page_size=True)
        b.close()
    return destino


def valida_por_pagina(nome, pagina2, esperados):
    import json
    arq = TMP / f"esperados-{nome}.json"; arq.write_text(json.dumps(esperados, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([PY, str(AQUI / "validar_pdf.py"), str(pdf_duas_paginas(nome, pagina2)), "--por-pagina", str(arq)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


P2_VIVA = f"<h1>Sua marca na arbitragem</h1>{APOIO}"
P2_CANVAS = ('<canvas id="c" width="1700" height="200"></canvas><script>const x=document.getElementById("c").getContext("2d");'
             'x.font="110px Helvetica";x.fillText("Sua marca na arbitragem",0,130);</script>' + APOIO)
ESPERADOS = [["Quem está em campo"], ["Sua marca na arbitragem"]]


def test_por_pagina_texto_vivo_passa():
    cod, out = valida_por_pagina("viva", P2_VIVA, ESPERADOS)
    assert cod == 0 and "FALHA" not in out, out


def test_por_pagina_acusa_so_a_pagina_que_virou_imagem():
    """O caso que o --texto global não pega: o título existe como texto no documento inteiro? Não, mas um título de
    UMA página virando imagem passava porque o nome do evento e a tese continuavam vivos nas outras."""
    cod, out = valida_por_pagina("canvas", P2_CANVAS, ESPERADOS)
    assert cod == 1 and "p.2:" in out and "p.1:" not in out and "arbitragem" in out, out


def test_por_pagina_acusa_pagina_trocada():
    cod, out = valida_por_pagina("viva", P2_VIVA, [["Sua marca na arbitragem"], ["Quem está em campo"]])
    assert cod == 1 and "p.1:" in out and "p.2:" in out, out


def test_por_pagina_acusa_contagem_diferente():
    cod, out = valida_por_pagina("viva", P2_VIVA, ESPERADOS + [["Cotas de patrocínio"]])
    assert cod == 1 and "o PDF tem 2 páginas e o render mediu 3" in out, out


def test_texto_cortado_pelo_render_compara_sem_a_ultima_palavra():
    """O render guarda 50 caracteres por texto: a última palavra pode vir pela metade e não pode reprovar."""
    import validar_pdf
    t = "Árbitros e organização estão em todos os jogos do s"
    assert len(t) == 51 and validar_pdf.comparavel(t[:50]) == "Árbitros e organização estão em todos os jogos do"
    assert validar_pdf.comparavel("ok") == "" and validar_pdf.comparavel("Copa AME") == "Copa AME"



# ------------------------------------------------------------------------------------------------- imagens por página
FIXTURE_IMAGENS = AQUI.parent / "schema" / "fixtures" / "imagens-golden-2026-10-12.json"
GOLDEN = AQUI.parent / "bancada" / "golden" / "2026-10-12"


def _lista(arq_nome, valores):
    import json
    arq = TMP / arq_nome; arq.write_text(json.dumps(valores), encoding="utf-8")
    return arq


def test_imagens_do_html_conta_img_image_e_url_por_secao():
    import validar_pdf
    html = ('<html><body><section data-tipo="capa"><img src="a.jpg"><svg><image href="data:image/png;base64,AA"/></svg>'
            '<div style="background-image: url(&quot;data:image/png;base64,BB&quot;)"></div><div style="background:url(x.svg)"></div>'
            '</section><section data-tipo="prova"><p>sem imagem</p></section></body></html>')
    assert validar_pdf.imagens_do_html(html) == [3, 0], validar_pdf.imagens_do_html(html)
    assert validar_pdf.imagens_por_pagina(["1 0 image 10 10 rgb 3 8 jpeg no 1 0 9 9 1K 1%", "1 1 smask 10 10 gray 1 8 image no 1 0 9 9 1K 1%",
                                           "3 2 image 10 10 rgb 3 8 jpeg no 2 0 9 9 1K 1%"]) == {1: 1, 3: 1}


def test_imagens_esperadas_reprova_raster_que_ninguem_pediu():
    """O sinal da rasterização silenciosa: o filtro CSS faz o Skia desenhar a região como imagem. O HTML não pede imagem
    nenhuma; o PDF tem uma: FALHA. Texto vivo sem imagem passa; a textura que o HTML pede passa."""
    cod, out = valida("filtro", "--imagens-esperadas", _lista("zero.json", [0]))
    assert cod == 1 and "p.1:" in out and "raster que ninguém pediu" in out, out
    cod, out = valida("vivo", "--imagens-esperadas", _lista("zero.json", [0]))
    assert cod == 0 and "FALHA" not in out, out
    cod, out = valida("textura", "--imagens-esperadas", _lista("um.json", [1]))
    assert cod == 0 and "FALHA" not in out, out
    cod, out = valida("textura", "--imagens-esperadas", _lista("zero.json", [0]))
    assert cod == 1 and "1 imagens no PDF e a página pede 0" in out, out
    html = TMP / "pede-uma.html"
    html.write_text('<section><img src="data:image/png;base64,AA"></section>', encoding="utf-8")
    cod, out = valida("textura", "--imagens-esperadas", html)              # o .html do render direto
    assert cod == 0 and "FALHA" not in out, out
    cod, out = valida("textura", "--imagens-esperadas", _lista("duas.json", [1, 1]))
    assert cod == 0 and "imagens por página não conferidas: o PDF tem 1 páginas e o HTML pede 2" in out, out
    cod, out = valida("filtro")                                            # inverso: sem a opção, o filtro não reprova por imagem
    assert "raster que ninguém pediu" not in out, out


def test_imagens_esperadas_calibrada_no_golden_sem_falso_alarme():
    """Calibração: os PDFs horizontais dos 5 kits do golden (12/10/2026). `real` da fixture é o pdfimages do PDF que o
    pipeline 14fb73e gera, e bate com o pdf.json do golden; em nenhuma página o PDF tem mais imagens que o HTML pede."""
    import json
    fx = json.loads(FIXTURE_IMAGENS.read_text(encoding="utf-8"))["kits"]
    total = iguais = 0
    for kit, pdfs in fx.items():
        golden = json.loads((GOLDEN / kit / "pdf.json").read_text(encoding="utf-8"))
        for nome, v in pdfs.items():
            reais = {}
            for l in golden[nome]["imagens"]:
                t = l.split()
                if t[2] == "image":
                    reais[int(t[0])] = reais.get(int(t[0]), 0) + 1
            assert v["real"] == [reais.get(n, 0) for n in range(1, golden[nome]["paginas"] + 1)], (kit, nome)
            assert len(v["html"]) == len(v["real"]), (kit, nome)
            ruins = [n for n, (r, e) in enumerate(zip(v["real"], v["html"]), 1) if r > e]
            assert not ruins, (kit, nome, ruins)
            total += len(v["real"]); iguais += sum(r == e for r, e in zip(v["real"], v["html"]))
    print(f"   calibração: {total} páginas horizontais em 5 kits, 0 acima do esperado, {iguais} exatamente iguais")
    assert total == 187 and iguais == 180, (total, iguais)


def test_pdf_deitado_onde_o_vertical_pede_pagina_em_pe_reprova():
    """O vertical saía em folhas deitadas (1440 x 810 pt): com --paginas 1080x1920 o tamanho reprova."""
    cod, out = valida("vivo", "--paginas", "1080x1920")
    assert cod == 1 and "tamanho de página 1440×810 pt, esperado 810×1440" in out, out

if __name__ == "__main__":
    falhas = 0
    try:
        for nome, f in list(globals().items()):
            if nome.startswith("test_"):
                try:
                    f(); print("ok  ", nome)
                except AssertionError as e:
                    falhas += 1; print("FALHOU", nome, str(e)[:400])
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    print("PROVAS:", "VERDES" if not falhas else f"{falhas} FALHA(S)")
    sys.exit(1 if falhas else 0)

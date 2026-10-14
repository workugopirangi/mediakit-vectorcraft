#!/usr/bin/env python3
"""Provas do caminhos.py e do confinamento nos pontos que leem arquivo do kit (achado 5 da revisão de segurança, 09/10).
Rodar: ~/.venvs/mediakit/bin/python test_caminhos.py"""
import os, sys, tempfile
from pathlib import Path
from PIL import Image

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
import caminhos, camadas, render  # noqa: E402


def _png(p, cor=(200, 30, 30, 255)):
    p.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (40, 80), cor).save(p)
    return p


def test_dentro_do_kit_aceita_o_que_fica_dentro_e_recusa_o_que_sai():
    with tempfile.TemporaryDirectory() as d:
        kit = Path(d) / "kit"; _png(kit / "acervo" / "a.png"); _png(Path(d) / "segredo.png")
        assert caminhos.dentro_do_kit(kit, "acervo/a.png") == (kit / "acervo" / "a.png").resolve()
        assert caminhos.dentro_do_kit(kit, "acervo/../acervo/a.png") == (kit / "acervo" / "a.png").resolve()
        os.symlink(Path(d) / "segredo.png", kit / "acervo" / "link.png")
        for ruim in ("../segredo.png", str(Path(d) / "segredo.png"), "acervo/../../segredo.png", "acervo/link.png", "", None):
            try:
                caminhos.dentro_do_kit(kit, ruim); raise AssertionError(f"passou: {ruim!r}")
            except caminhos.ForaDoKit:
                pass


def test_render_recusa_acervo_fora_do_kit():
    with tempfile.TemporaryDirectory() as d:
        kit = Path(d) / "kit"; _png(kit / "acervo" / "a.png"); _png(Path(d) / "segredo.png")
        report = {"avisos": []}
        ok = render.carregar_acervo({"acervo": [{"id": "a", "arquivo": "acervo/a.png", "direito_uso": True}]}, kit, report)
        assert ok["a"]["src"].startswith("data:image/png;base64,")
        for ruim in ("../segredo.png", str(Path(d) / "segredo.png")):
            try:
                render.carregar_acervo({"acervo": [{"id": "x", "arquivo": ruim, "direito_uso": True}]}, kit, report)
                raise AssertionError(f"embutiu {ruim}")
            except SystemExit as e:
                assert "sai da pasta do kit" in str(e) or "absoluto" in str(e), e


def test_elemento_e_imagem_do_grafismo_ficam_no_kit():
    with tempfile.TemporaryDirectory() as d:
        kit = Path(d) / "kit"; _png(kit / "acervo" / "app.png"); _png(Path(d) / "segredo.png")
        try:
            camadas.carregar({"elementos": [{"id": "e", "papel": "heroi", "formato": "png", "arquivo": "../segredo.png"}]}, kit, {"avisos": []})
            raise AssertionError("elemento de fora carregado")
        except SystemExit as e:
            assert "sai da pasta do kit" in str(e), e
        el = camadas.Elementos({"elementos": []}, kit, {"avisos": []})
        ctx = {"paleta": {"marca": "#F5D80A", "escuro": "#0B0B0C"}}
        g = el.gerar("celular", {"imagem": "acervo/app.png", "largura": 200}, ctx)
        assert "<image" in g["svg"], "a captura de dentro do kit entra"
        for ruim in ("../segredo.png", str(Path(d) / "segredo.png")):
            try:
                el.gerar("celular", {"imagem": ruim, "largura": 200}, ctx); raise AssertionError(f"leu {ruim}")
            except caminhos.ForaDoKit:
                pass


def test_render_recusa_marcacao_html_no_texto_do_kit():
    """Pré-existente apontado na revisão (09/10): autoescape desligado para o <b> funcionar; um <img src=file://...> ou um
    <script> colado num texto do cliente rodaria no Chromium do render. Só <b> e </b> passam."""
    ok = {"tese": {"frase": "A <b>A.M.E</b> abre três cotas"}, "cotas": [{"entregaveis": ["Placa 3 < 5 m"]}]}
    assert render.marcacao_no_texto({"tese": ok["tese"]}) == []
    ruins = {"tese": {"frase": "Oi <img src=file:///etc/hosts>"}, "acao": {"pessoas": [{"nome": "<script>x</script>"}]},
             "cotas": ok["cotas"]}
    achados = dict(render.marcacao_no_texto(ruins))
    assert set(achados) == {"tese.frase", "acao.pessoas[0].nome", "cotas[0].entregaveis[0]"}, achados


def test_render_recusa_valor_que_fugiria_do_atributo_ou_do_css():
    """Revisão de segurança (09/10): o filtro de marcação só olhava o "<". O foco da foto vai para style="object-position:
    ...", as cores e fontes para o CSS, o id da receita para o seletor: uma aspa ou um url( fugiria sem nenhum "<"."""
    bom = {"marca": {"cor_primaria": "#F5D80A", "fonte_display": "Barlow Condensed", "direcao": "performance", "peso_display": 800},
           "receitas": [{"id": "r1", "paleta": {"marca": "#F5D80A"}, "fontes": {"display": "Barlow Condensed", "corpo": "Barlow"}}],
           "acervo": [{"foco": "62% 50%"}, {"foco": "center top"}, {"foco": None}],
           "graficos": [{"escala": "log"}], "publico": {"genero": [{"pct": 58}]}, "objetos": [{"x": 10, "y": 20.5, "w": 300}]}
    assert render.valores_fora_do_formato(bom) == []
    ruins = [("acervo", [{"foco": '50% 40%" onload="x'}]), ("acervo", [{"foco": "50% 40%; background:url(file:///etc/hosts)"}]),
             ("marca", {"cor_primaria": "red; background: url(file:///x.png)"}), ("marca", {"fonte_display": 'X"; } body { x'}),
             ("marca", {"direcao": 'causa" onclick="x'}), ("receitas", [{"id": 'r1"] { } * { x'}]),
             ("receitas", [{"id": "r1", "paleta": {"marca": "#F5D80A;x"}}]), ("graficos", [{"escala": 'log" x="'}]),
             ("publico", {"genero": [{"pct": '50%" x="'}]}), ("objetos", [{"x": "1px;background:url(file:///y)"}])]
    for chave, valor in ruins:
        assert render.valores_fora_do_formato({chave: valor}), (chave, valor)


def test_logo_e_png_dos_grafismos_ficam_no_kit():
    """Revisão de segurança (09/10): o confinamento não cobria o logo do contexto dos grafismos nem o parâmetro `png`
    (símbolo e padrões a partir do logo)."""
    with tempfile.TemporaryDirectory() as d:
        kit = Path(d) / "kit"; _png(kit / "acervo" / "logo.png"); _png(Path(d) / "segredo.png")
        k = {"marca": {"logo_id": "logo"}, "acervo": [{"id": "logo", "funcao": "logo", "arquivo": "acervo/logo.png"}]}
        assert Path(camadas.contexto_grafismo(k, None, kit, None)["logo_png"]).resolve() == (kit / "acervo" / "logo.png").resolve()
        k["acervo"][0]["arquivo"] = "../segredo.png"
        try:
            camadas.contexto_grafismo(k, None, kit, None); raise AssertionError("logo de fora aceito")
        except SystemExit as e:
            assert "sai da pasta do kit" in str(e), e
        el = camadas.Elementos({"elementos": []}, kit, {"avisos": []})
        try:
            el.gerar("mosaico", {"png": "../segredo.png"}, {"paleta": {"marca": "#F5D80A"}}); raise AssertionError("png de fora lido")
        except caminhos.ForaDoKit:
            pass


if __name__ == "__main__":
    falhas = 0
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            try:
                f(); print("ok  ", nome)
            except Exception as e:
                falhas += 1; print("FALHOU", nome, type(e).__name__, e)
    print("PROVAS:", "VERDES" if not falhas else f"{falhas} FALHA(S)")
    sys.exit(1 if falhas else 0)

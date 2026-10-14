import fitz
from mediakit.checagem import conteudo

FONTE = "/System/Library/Fonts/Supplemental/Arial.ttf"


def _pdf(tmp_path, paginas):
    d = fitz.open()
    for texto in paginas:
        p = d.new_page(width=1440, height=810)
        p.insert_text((50, 100), texto, fontsize=20, fontname="arial", fontfile=FONTE)
    out = tmp_path / "t.pdf"
    d.save(out)
    return out


def test_numeros_reconhece_formatos():
    assert conteudo.numeros("R$ 30.000, 52% e 1.200 em 31/03/2027, tel (11) 98012-0229, 5, 10 e 14 km") == {
        "30.000", "52%", "1.200", "31/03/2027", "11", "98012-0229", "5", "10", "14"}


def test_numero_fora_da_ficha_aparece(tmp_path):
    ficha = tmp_path / "ficha.md"
    ficha.write_text("Meta de 1.200 participantes. Naming R$ 30.000.")
    pdf = _pdf(tmp_path, ["1.200 participantes", "R$ 35.000"])
    assert conteudo.numeros_fora_da_ficha(pdf, ficha) == [{"pagina": 2, "numero": "35.000"}]


def test_travessao_aparece(tmp_path):
    pdf = _pdf(tmp_path, ["Sem problema aqui.", "Largada \u2014 chegada"])
    r = conteudo.travessoes(pdf)
    assert len(r) == 1 and r[0]["pagina"] == 2


def test_virgula_decimal_e_um_numero_so():
    assert "4,8" in conteudo.numeros("4,8 mil visualizações")


def test_rotulo_espacado_vira_um_numero():
    assert conteudo.numeros("2 0 2 5 : I N F O R M A D O") == {"2025"}
    assert conteudo.numeros("5 · 10 · 14 KM") == {"5", "10", "14"}


def test_rotulo_espacado_errado_aparece(tmp_path):
    ficha = tmp_path / "ficha.md"
    ficha.write_text("2026 (informado): 500 atletas. Página 2 de 5.")
    pdf = _pdf(tmp_path, ["2 0 2 5 · I N F O R M A D O"])
    assert conteudo.numeros_fora_da_ficha(pdf, ficha) == [{"pagina": 1, "numero": "2025"}]

import fitz
from mediakit.checagem import tinta


def _pdf(tmp_path, linhas):
    d = fitz.open()
    p = d.new_page(width=1440, height=810)
    for (x, y, s, tam) in linhas:
        p.insert_text((x, y), s, fontsize=tam, fontname="helv")
    out = tmp_path / "t.pdf"
    d.save(out)
    return out


def _caixas_se_cruzam(pdf):
    linhas = [l["bbox"] for b in fitz.open(pdf)[0].get_text("dict")["blocks"] for l in b.get("lines", [])]
    return abs(fitz.Rect(linhas[0]) & fitz.Rect(linhas[1])) > 0


def test_entrelinha_apertada_sem_tinta_encostando_nao_acusa(tmp_path):
    # caixas de fonte se cruzam (entrelinha 0,9 do corpo), mas as letras não
    pdf = _pdf(tmp_path, [(50, 200, "MAIS DO QUE", 100), (50, 290, "UM LOGO", 100)])
    assert _caixas_se_cruzam(pdf)
    assert tinta.sobreposicoes(pdf) == []


def test_texto_sobre_texto_acusa(tmp_path):
    pdf = _pdf(tmp_path, [(50, 200, "R$ 30.000", 120), (52, 205, "1 cota disponível.", 40)])
    r = tinta.sobreposicoes(pdf)
    assert len(r) == 1
    assert r[0]["pagina"] == 1 and "30.000" in r[0]["a"] + r[0]["b"]


def test_dois_textos_na_mesma_linha_encostando_acusa(tmp_path):
    pdf = _pdf(tmp_path, [(50, 200, "PREÇO", 60), (180, 200, "COTA", 60)])
    assert len(tinta.sobreposicoes(pdf)) == 1


def test_texto_fora_da_pagina_nao_conta(tmp_path):
    pdf = _pdf(tmp_path, [(1500, 200, "FORA", 60), (1505, 205, "FORA", 60), (50, 200, "dentro", 40)])
    assert tinta.sobreposicoes(pdf) == []

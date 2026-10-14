from PIL import Image
import pytest
from mediakit import fotos


def _foto(tmp_path, w, h, nome="f.jpg"):
    p = tmp_path / nome
    Image.new("RGB", (w, h), (120, 90, 60)).save(p)
    return p


def test_ppi_da_pagina_cheia():
    # 1920 unidades = 1440 pt = 20 polegadas; 739 px nelas dá 36,95 ppi (o caso real da f4)
    assert fotos.ppi_na_pagina(739, 1920) == pytest.approx(36.95, abs=0.01)


def test_foto_no_tamanho_certo_nao_avisa(tmp_path):
    r = fotos.preparar_foto(_foto(tmp_path, 739, 980), tmp_path / "o.jpg", 700, 930)
    assert r["ppi"] >= 96 and r["aviso"] is None


def test_avisa_foto_esticada(tmp_path):
    r = fotos.preparar_foto(_foto(tmp_path, 739, 980), tmp_path / "o.jpg", 1920, 1080)
    assert r["ppi"] < 96
    assert "f.jpg" in r["aviso"] and "ppi" in r["aviso"]


def test_nao_amplia_alem_do_original(tmp_path):
    r = fotos.preparar_foto(_foto(tmp_path, 400, 400), tmp_path / "o.jpg", 1000, 1000)
    assert Image.open(r["caminho"]).size == (400, 400)


def test_modo_bw_sai_cinza(tmp_path):
    r = fotos.preparar_foto(_foto(tmp_path, 800, 800), tmp_path / "o.jpg", 400, 400, modo="bw")
    px = Image.open(r["caminho"]).getpixel((10, 10))
    assert px[0] == px[1] == px[2]

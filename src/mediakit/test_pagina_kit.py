import fitz
import pytest
from mediakit import kit
from mediakit.pagina import bounds

pytestmark = pytest.mark.vectorcraft


def p_um(P):
    P.rect(0, 0, 1920, 1080, fill="#EA3339")
    P.text(96, 300, "Primeira página", size=80, color="#000000")
    return "ok-1"


def p_dois(P):
    oid, tam = P.fit(96, 700, "R$ 30.000", 1380, ("Helvetica Neue", "Bold"), 400, "#000000")
    w = bounds(P.ex, oid)["width"]
    assert abs(w - 1380) < 2
    return round(tam)


def test_monta_duas_paginas(tmp_path):
    r = kit.montar("t", [p_um, p_dois], tmp_path / "t.pdf", tmp_path / "t.vectorcraft")
    d = fitz.open(r["pdf"])
    assert len(d) == 2
    assert d[0].rect.width == pytest.approx(1440, abs=1)
    assert "Primeira página" in d[0].get_text()
    assert "30.000" in d[1].get_text()
    assert r["retornos"]["p_um"] == "ok-1"
    assert (tmp_path / "t.vectorcraft").exists()


def test_foto_pequena_vira_aviso_ao_lado_do_pdf(tmp_path):
    import json
    from PIL import Image
    pequena = tmp_path / "f4.jpg"
    Image.new("RGB", (739, 980)).save(pequena)
    fundo = tmp_path / "asfalto.jpg"
    Image.new("RGB", (1600, 900)).save(fundo)

    def p_fotos(P):
        P.image(fundo, 0, 0, 1920, 1080, aceito="textura de fundo")
        P.image(pequena, 0, 0, 1920, 1080)
        P.image(pequena, 1100, 150, 700, 930)

    r = kit.montar("t", [p_fotos], tmp_path / "t.pdf", tmp_path / "t.vectorcraft")
    avisos = json.loads((tmp_path / "avisos-foto.json").read_text())
    assert [(a["arquivo"], a["aceito"]) for a in avisos] == [("asfalto.jpg", "textura de fundo"), ("f4.jpg", None)]
    assert avisos[1]["ppi"] == 37 and avisos[1]["pagina"] == 1
    assert r["avisos_foto"] == avisos


def test_aceitar_sobreposicao_grava_ao_lado_do_pdf(tmp_path):
    import json

    def p_letreiro(P):
        P.text(96, 300, "Quem está", size=200, color="#000000")
        P.text(300, 430, "em campo", size=200, color="#000000")
        P.aceitar_sobreposicao("Quem está", "em campo", "letreiro entrelaçado (Japa)")

    kit.montar("t", [p_letreiro], tmp_path / "t.pdf", tmp_path / "t.vectorcraft")
    assert json.loads((tmp_path / "sobreposicoes-aceitas.json").read_text()) == [
        {"pagina": 1, "a": "Quem está", "b": "em campo", "motivo": "letreiro entrelaçado (Japa)"}]

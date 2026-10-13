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

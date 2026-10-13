import json
import fitz
import pytest
from PIL import Image
from mediakit import referencias


def _repertorio(tmp_path):
    r = tmp_path / "repertorio" / "capturas"
    (r / "web-nike").mkdir(parents=True)
    Image.new("RGB", (10, 10)).save(r / "web-nike" / "01.jpg")
    return tmp_path / "repertorio", tmp_path / "referencias.json"


def test_lista_o_que_ja_existe(tmp_path):
    rep, reg = _repertorio(tmp_path)
    itens = referencias.listar(rep, reg)
    assert [(i["id"], i["imagens"], i["origem"]) for i in itens] == [("web-nike", 1, "repertorio")]


def test_adiciona_imagem_e_pdf(tmp_path):
    rep, reg = _repertorio(tmp_path)
    img = tmp_path / "a.png"
    Image.new("RGB", (20, 20)).save(img)
    pdf = tmp_path / "b.pdf"
    d = fitz.open(); d.new_page(); d.new_page(); d.save(pdf)
    pasta = referencias.adicionar("deck-adidas-26", [img, pdf], "Ugo mandou no chat em 13/10", rep, reg)
    assert sorted(p.name for p in pasta.iterdir()) == ["01.jpg", "02.jpg", "03.jpg"]
    assert json.loads(reg.read_text())[0]["origem_texto"] == "Ugo mandou no chat em 13/10"
    assert {i["id"]: i["origem"] for i in referencias.listar(rep, reg)}["deck-adidas-26"] == "nova"


def test_nao_sobrescreve_referencia_existente(tmp_path):
    rep, reg = _repertorio(tmp_path)
    with pytest.raises(ValueError, match="já existe"):
        referencias.adicionar("web-nike", [], "x", rep, reg)


def test_id_invalido_recusa(tmp_path):
    rep, reg = _repertorio(tmp_path)
    with pytest.raises(ValueError, match="id"):
        referencias.adicionar("../fora", [], "x", rep, reg)

import pytest
from mediakit import pecas


def test_ordem_comeca_pela_camisa():
    assert pecas.ORDEM[:3] == ["camisa", "celular-post", "cartaz"]


def test_registra_e_lista(tmp_path):
    origem = tmp_path / "x.png"
    origem.write_bytes(b"png")
    p = pecas.registrar("portico", origem, "World Tennis", "sprint-world-tennis", "orla", raiz=tmp_path / "bib")
    assert p.exists() and p.parent.name == "portico"
    assert pecas.listar("portico", raiz=tmp_path / "bib")[0]["marca"] == "World Tennis"
    assert pecas.listar("camisa", raiz=tmp_path / "bib") == []


def test_registrar_de_novo_nao_duplica(tmp_path):
    origem = tmp_path / "x.png"
    origem.write_bytes(b"png")
    for _ in range(2):
        pecas.registrar("camisa", origem, "World Tennis", "k", raiz=tmp_path / "bib")
    assert len(pecas.listar(raiz=tmp_path / "bib")) == 1


def test_peca_desconhecida_recusa(tmp_path):
    with pytest.raises(ValueError, match="peça"):
        pecas.registrar("disco-voador", tmp_path / "x.png", "M", "k", raiz=tmp_path)

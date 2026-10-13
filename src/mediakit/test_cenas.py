import json
from mediakit import cenas


def _arquivos(tmp_path):
    (tmp_path / "c-composta.png").write_bytes(b"x")
    (tmp_path / "c-gerada.png").write_bytes(b"x")
    return tmp_path


def test_sem_escolha_usa_composta(tmp_path):
    p, rota = cenas.escolher_cena(_arquivos(tmp_path), "c-composta.png", "c-gerada.png")
    assert rota == "composta" and p.name == "c-composta.png"


def test_gerada_sem_aprovacao_usa_composta(tmp_path):
    a = _arquivos(tmp_path)
    (a / "escolha-cenas.json").write_text(json.dumps({"outra.png": "usar"}))
    assert cenas.escolher_cena(a, "c-composta.png", "c-gerada.png")[1] == "composta"


def test_gerada_aprovada_entra(tmp_path):
    a = _arquivos(tmp_path)
    cenas.marcar(a, "c-gerada.png", "usar")
    assert cenas.escolher_cena(a, "c-composta.png", "c-gerada.png")[1] == "gerada"


def test_aprovada_mas_apagada_volta_para_composta(tmp_path):
    a = _arquivos(tmp_path)
    cenas.marcar(a, "c-gerada.png", "usar")
    (a / "c-gerada.png").unlink()
    assert cenas.escolher_cena(a, "c-composta.png", "c-gerada.png")[1] == "composta"


def test_marcar_preserva_as_outras(tmp_path):
    cenas.marcar(tmp_path, "a.png", "usar")
    cenas.marcar(tmp_path, "b.png", "descartar")
    assert json.loads((tmp_path / "escolha-cenas.json").read_text()) == {"a.png": "usar", "b.png": "descartar"}


def test_registra_cota(tmp_path):
    assert cenas.registrar_geracao(tmp_path, "c-portico", "2026-10-13T14:33") == 1
    assert cenas.registrar_geracao(tmp_path, "camisa", "2026-10-13T14:48") == 2
    assert [g["id"] for g in cenas.geracoes(tmp_path)] == ["c-portico", "camisa"]

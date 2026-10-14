import sys
from mediakit import receitas

DESENHA = '''import fitz, sys, pathlib
d = fitz.open(); p = d.new_page(width=200, height=100)
p.draw_rect(fitz.Rect(10, 10, {largura}, 90), color=(0, 0, 0), fill=(0, 0, 0))
d.save(pathlib.Path(__file__).parent / "teste.pdf")
(pathlib.Path(__file__).parent / "sobra.png").write_bytes(b"gerado agora")
'''


def _receita(raiz, nome, largura=100, quebra=False):
    r = raiz / nome
    r.mkdir(parents=True, exist_ok=True)
    (r / "teste.py").write_text("raise SystemExit(1)\n" if quebra else DESENHA.format(largura=largura))
    return r


def _prova(r, largura):
    exec(DESENHA.format(largura=largura).replace("__file__", repr(str(r / "teste.py"))))
    (r / "sobra.png").unlink()


def test_mesma_receita_roda_nao_muda_e_devolve_a_pasta(tmp_path):
    r = _receita(tmp_path, "R01")
    _prova(r, 100)
    antes = (r / "teste.pdf").read_bytes()
    res = receitas.rodar(tmp_path, python=sys.executable)
    assert res["R01"] == {"roda": True, "mudou": False}
    assert (r / "teste.pdf").read_bytes() == antes
    assert not (r / "sobra.png").exists()


def test_desenho_diferente_acusa_mudou(tmp_path):
    r = _receita(tmp_path, "R01", largura=190)
    _prova(r, 100)
    assert receitas.rodar(tmp_path, python=sys.executable)["R01"] == {"roda": True, "mudou": True}


def test_receita_que_quebra(tmp_path):
    _receita(tmp_path, "R02", quebra=True)
    assert receitas.rodar(tmp_path, python=sys.executable)["R02"]["roda"] is False


def test_compara_com_a_base():
    base = {"R01": True, "R02": False}
    res = {"R01": {"roda": False, "mudou": None}, "R02": {"roda": True, "mudou": False}}
    assert receitas.quebradas(base, res) == ["R01"]

import subprocess
import pytest
from mediakit import vc


def _repo_falso(tmp_path, commits=1):
    r = tmp_path / "vc"
    r.mkdir()
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    for i in range(commits):
        (r / "a.txt").write_text(str(i))
        subprocess.run(["git", "-C", str(r), "add", "."], check=True)
        subprocess.run(["git", "-C", str(r), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", str(i)], check=True)
    return r


def test_versao_travada_le_o_arquivo():
    v = vc.versao_travada()
    assert len(v) == 40 and all(c in "0123456789abcdef" for c in v)


def test_versao_igual_passa(tmp_path, monkeypatch):
    r = _repo_falso(tmp_path)
    monkeypatch.setattr(vc, "versao_travada", lambda: vc.versao_instalada(r))
    vc.conferir_versao(r)


def test_versao_diferente_para(tmp_path, monkeypatch):
    r = _repo_falso(tmp_path)
    monkeypatch.setattr(vc, "versao_travada", lambda: "0" * 40)
    with pytest.raises(vc.VCError, match="montar_vectorcraft.sh"):
        vc.conferir_versao(r)


@pytest.mark.vectorcraft
def test_monta_e_exporta_um_pdf(tmp_path):
    import fitz
    v = vc.VC()
    try:
        v.ex("file.new", {"name": "t", "width": 1920, "height": 1080, "units": "Pixels"})
        v.ex("shape.rectangle", {"x": 10, "y": 10, "width": 100, "height": 100})
        pdf = tmp_path / "t.pdf"
        v.ex("document.exportPdf", {"path": str(pdf), "preserveEditing": False})
    finally:
        v.close()
    assert len(fitz.open(pdf)) == 1


def test_clone_com_alteracao_nao_gravada_para(tmp_path, monkeypatch):
    r = _repo_falso(tmp_path)
    monkeypatch.setattr(vc, "versao_travada", lambda: vc.versao_instalada(r))
    (r / "a.txt").write_text("mexido")
    with pytest.raises(vc.VCError, match="alteração não gravada"):
        vc.conferir_versao(r)


def test_clone_ausente_da_frase(tmp_path):
    with pytest.raises(vc.VCError, match="montar_vectorcraft.sh"):
        vc.conferir_versao(tmp_path / "nao-existe")


def test_programa_ausente_da_frase(tmp_path, monkeypatch):
    monkeypatch.setattr(vc.config, "VC_CLI", tmp_path / "nao-existe")
    monkeypatch.setattr(vc, "conferir_versao", lambda repo=None: None)
    with pytest.raises(vc.VCError, match="montar_vectorcraft.sh"):
        vc.VC()

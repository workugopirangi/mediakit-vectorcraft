import fitz
from mediakit.checagem import checar


def _pdf(tmp_path, linhas):
    d = fitz.open()
    p = d.new_page(width=1440, height=810)
    for (x, y, s, tam) in linhas:
        p.insert_text((x, y), s, fontsize=tam, fontname="helv")
    out = tmp_path / "k.pdf"
    d.save(out)
    return out


def _ficha(tmp_path, texto="Naming R$ 30.000. 1 cota disponível."):
    f = tmp_path / "ficha.md"
    f.write_text(texto)
    return f


def test_kit_limpo_sem_falha(tmp_path, monkeypatch):
    monkeypatch.setattr(checar, "_validar_arquivo", lambda pdf: (True, "0 falha(s)"))
    r = checar.checar(_pdf(tmp_path, [(50, 200, "R$ 30.000", 100), (50, 400, "1 cota disponível.", 40)]), _ficha(tmp_path))
    assert r["falhas"] == []


def test_preco_encostando_e_falha(tmp_path, monkeypatch):
    monkeypatch.setattr(checar, "_validar_arquivo", lambda pdf: (True, "0 falha(s)"))
    r = checar.checar(_pdf(tmp_path, [(50, 200, "R$ 30.000", 120), (52, 205, "1 cota disponível.", 40)]), _ficha(tmp_path))
    assert any("sobreposição" in f for f in r["falhas"])


def test_arquivo_reprovado_e_falha(tmp_path, monkeypatch):
    monkeypatch.setattr(checar, "_validar_arquivo", lambda pdf: (False, "1 falha(s)"))
    r = checar.checar(_pdf(tmp_path, [(50, 200, "R$ 30.000", 60)]), _ficha(tmp_path))
    assert any("validar_pdf" in f for f in r["falhas"])


def test_numero_fora_e_aviso_nao_falha(tmp_path, monkeypatch):
    monkeypatch.setattr(checar, "_validar_arquivo", lambda pdf: (True, "0 falha(s)"))
    r = checar.checar(_pdf(tmp_path, [(50, 200, "R$ 35.000", 60)]), _ficha(tmp_path))
    assert r["falhas"] == [] and any("35.000" in a for a in r["avisos"])


def test_foto_pequena_vira_aviso(tmp_path, monkeypatch):
    monkeypatch.setattr(checar, "_validar_arquivo", lambda pdf: (True, "0 falha(s)"))
    r = checar.checar(_pdf(tmp_path, [(50, 200, "R$ 30.000", 60)]), _ficha(tmp_path), avisos_foto=["f4.jpg: 37 ppi"])
    assert "f4.jpg: 37 ppi" in r["avisos"]


def test_prompt_revisor_sem_lacuna_e_sem_travessao(tmp_path):
    s = checar.prompt_revisor(tmp_path, tmp_path / "ficha.md", [tmp_path / "ref1", tmp_path / "ref2"], tmp_path / "logo.png")
    assert "{" not in s and "\N{EM DASH}" not in s and "\N{EN DASH}" not in s
    assert str(tmp_path / "ref2") in s

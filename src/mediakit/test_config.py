from mediakit import config


def test_raiz_e_o_projeto():
    assert (config.RAIZ / "docs" / "SPEC.md").exists()


def test_regua_de_foto():
    assert config.PPI_MINIMO == 96
    assert config.ESCALA_PDF == 0.75


def test_caminhos_aceitam_variavel_de_ambiente(monkeypatch, tmp_path):
    import importlib
    monkeypatch.setenv("MEDIAKIT_VC_CLI", str(tmp_path / "cli"))
    c = importlib.reload(config)
    assert c.VC_CLI == tmp_path / "cli"
    monkeypatch.delenv("MEDIAKIT_VC_CLI")
    importlib.reload(config)

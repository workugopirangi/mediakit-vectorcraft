import subprocess
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).parent
KIT = Path("~/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/TUC/MEDIAKIT/tuc-red-bull").expanduser()


@pytest.mark.vectorcraft
def test_kit_monta_limpo_e_com_a_copy_da_ficha(tmp_path):
    r = subprocess.run([sys.executable, str(AQUI / "kit.py"), "--saida", str(tmp_path)], capture_output=True, text=True,
                       timeout=300)
    assert r.returncode == 0, r.stderr[-2000:]
    pdf = tmp_path / "kit-tuc-red-bull.pdf"
    texto = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    junto = "".join(texto.split())  # o espaçamento das letras (tracking) separa os caracteres no pdftotext
    for frase in ("TUC apresentado", "R$ 250.000", "segundo a", "SUJEITO À APROVAÇÃO", "(11) 96695-5712"):
        assert "".join(frase.split()) in junto, frase
    assert "cincomeses" not in junto and "5sedes" not in junto
    from mediakit.checagem import checar
    res = checar.checar(pdf, KIT / "ficha.md")
    assert res["falhas"] == []

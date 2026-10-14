import subprocess
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).parent
KIT = Path("~/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/SPRINT UBATUBA RUN/MEDIAKIT/sprint-world-tennis").expanduser()


@pytest.mark.vectorcraft
def test_kit_portado_sai_igual_e_limpo(tmp_path):
    r = subprocess.run([sys.executable, str(AQUI / "kit.py"), "--saida", str(tmp_path)], capture_output=True, text=True,
                       timeout=300)
    assert r.returncode == 0, r.stderr[-2000:]
    assert "'p_portico': 'gerada'" in r.stdout and "'p_estande': 'gerada'" in r.stdout, r.stdout[-500:]
    pdf = tmp_path / "kit-world-tennis.pdf"
    texto = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    assert texto == (AQUI / "referencia.txt").read_text()
    from mediakit.checagem import checar
    res = checar.checar(pdf, KIT / "ficha.md")
    assert res["falhas"] == []

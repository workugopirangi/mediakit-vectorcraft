import json
import os
import stat
import subprocess
import sys
from pathlib import Path

from PIL import Image

SCRIPT = Path(__file__).parent / "cena_limpar.sh"


def _codex_falso(tmp_path, entrega=True):
    """Um `codex` de mentira no PATH: conta cada chamada e, se mandado, grava o PNG pedido no prompt."""
    b = tmp_path / "bin"
    b.mkdir()
    corpo = ("#!/bin/bash\n"
             f"echo chamado >> {tmp_path / 'chamadas'}\n"
             "out=$(printf '%s' \"${@: -1}\" | grep -o '/[^ ]*\\.png' | head -1)\n"
             + (f"{sys.executable} -c \"from PIL import Image; Image.new('RGB',(8,8)).save('$out')\"\n" if entrega else "")
             + "exit 0\n")
    (b / "codex").write_text(corpo)
    (b / "codex").chmod((b / "codex").stat().st_mode | stat.S_IEXEC)
    return b


def _rodar(tmp_path, entrega=True):
    b = _codex_falso(tmp_path, entrega)
    cliente = tmp_path / "cliente"
    cliente.mkdir()
    origem = tmp_path / "origem.png"
    Image.new("RGB", (8, 8)).save(origem)
    env = dict(os.environ, PATH=f"{b}:{os.environ['PATH']}", PY=sys.executable, MEDIAKIT_CODEX_ESPERA="0")
    env.pop("MEDIAKIT_CODEX_TENTATIVAS", None)
    r = subprocess.run(["bash", str(SCRIPT), str(cliente), "cena-limpa", str(origem)], env=env, capture_output=True, text=True)
    return r, cliente / "acervo"


def test_sucesso_gera_e_registra_ok_na_cota(tmp_path):
    r, acervo = _rodar(tmp_path)
    assert r.returncode == 0, r.stderr
    assert (acervo / "cena-limpa.png").exists()
    assert [(g["id"], g["resultado"]) for g in json.loads((acervo / "cota.json").read_text())] == [("cena-limpa", "ok")]


def test_falha_chama_uma_vez_registra_falha_e_manda_perguntar(tmp_path):
    r, acervo = _rodar(tmp_path, entrega=False)
    assert r.returncode == 1
    assert (tmp_path / "chamadas").read_text().count("chamado") == 1
    assert [g["resultado"] for g in json.loads((acervo / "cota.json").read_text())] == ["falha"]
    assert "pergunte ao Ugo" in r.stderr


def test_instrucao_na_linha_de_comando_recusa(tmp_path):
    import subprocess, os
    from pathlib import Path
    script = Path(__file__).parent / "cena_limpar.sh"
    r = subprocess.run(["bash", str(script), str(tmp_path), "c-x", str(tmp_path / "o.png"), "texto extra"],
                       capture_output=True, text=True, env=dict(os.environ))
    assert r.returncode == 64 and "--descricao-de" in r.stderr

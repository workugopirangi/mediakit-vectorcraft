import json
import os
import stat
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent / "gerar_cena.sh"


def _codex_falso(tmp_path, entrega=True):
    b = tmp_path / "bin"
    b.mkdir()
    corpo = ("#!/bin/bash\n"
             "out=$(printf '%s' \"${@: -1}\" | grep -o '/[^ ]*\\.png' | head -1)\n"
             + (f"{sys.executable} -c \"from PIL import Image; Image.new('RGB',(8,8)).save('$out')\"\n" if entrega else "")
             + "exit 0\n")
    (b / "codex").write_text(corpo)
    (b / "codex").chmod((b / "codex").stat().st_mode | stat.S_IEXEC)
    return b


def _rodar(tmp_path, bin_dir):
    acervo = tmp_path / "acervo"
    acervo.mkdir()
    prompt = tmp_path / "p.txt"
    prompt.write_text("Crie a cena e salve em @OUT@ agora.")
    env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", PY=sys.executable, MEDIAKIT_CODEX_TENTATIVAS="1",
               MEDIAKIT_CODEX_ESPERA="0")
    r = subprocess.run(["bash", str(SCRIPT), "c-teste", str(prompt), str(acervo)], env=env, capture_output=True, text=True)
    return r, acervo


def test_gera_e_registra_cota(tmp_path):
    r, acervo = _rodar(tmp_path, _codex_falso(tmp_path))
    assert r.returncode == 0, r.stderr
    assert (acervo / "c-teste.png").exists()
    assert [g["id"] for g in json.loads((acervo / "cota.json").read_text())] == ["c-teste"]


def test_sem_imagem_nao_registra_cota(tmp_path):
    r, acervo = _rodar(tmp_path, _codex_falso(tmp_path, entrega=False))
    assert r.returncode == 1
    assert not (acervo / "cota.json").exists()


def test_imagem_que_ja_existe_nao_gasta_cota(tmp_path):
    r, acervo = _rodar(tmp_path, _codex_falso(tmp_path))
    prompt = tmp_path / "p.txt"
    env = dict(os.environ, PATH=f"{tmp_path / 'bin'}:{os.environ['PATH']}", PY=sys.executable)
    subprocess.run(["bash", str(SCRIPT), "c-teste", str(prompt), str(acervo)], env=env, capture_output=True, text=True)
    assert len(json.loads((acervo / "cota.json").read_text())) == 1

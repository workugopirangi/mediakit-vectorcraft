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
    env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}", PY=sys.executable, MEDIAKIT_CODEX_ESPERA="0")
    r = subprocess.run(["bash", str(SCRIPT), "c-teste", str(prompt), str(acervo)], env=env, capture_output=True, text=True)
    return r, acervo


def test_gera_e_registra_cota(tmp_path):
    r, acervo = _rodar(tmp_path, _codex_falso(tmp_path))
    assert r.returncode == 0, r.stderr
    assert (acervo / "c-teste.png").exists()
    assert [g["id"] for g in json.loads((acervo / "cota.json").read_text())] == ["c-teste"]


def test_falha_tenta_uma_vez_registra_e_manda_perguntar(tmp_path):
    b = _codex_falso(tmp_path, entrega=False)
    (b / "codex").write_text((b / "codex").read_text().replace("exit 0", "echo chamado >> " + str(tmp_path / "chamadas") + "\nexit 0"))
    acervo = tmp_path / "acervo"
    acervo.mkdir()
    prompt = tmp_path / "p.txt"
    prompt.write_text("Crie a cena e salve em @OUT@ agora.")
    env = dict(os.environ, PATH=f"{b}:{os.environ['PATH']}", PY=sys.executable, MEDIAKIT_CODEX_ESPERA="0")
    r = subprocess.run(["bash", str(SCRIPT), "c-teste", str(prompt), str(acervo)], env=env, capture_output=True, text=True)
    assert r.returncode == 1
    assert (tmp_path / "chamadas").read_text().count("chamado") == 1
    assert [g["resultado"] for g in json.loads((acervo / "cota.json").read_text())] == ["falha"]
    assert "pergunte ao Ugo" in r.stderr


def test_pasta_relativa_funciona(tmp_path):
    b = _codex_falso(tmp_path)
    (tmp_path / "acervo").mkdir()
    (tmp_path / "p.txt").write_text("Crie a cena e salve em @OUT@ agora.")
    env = dict(os.environ, PATH=f"{b}:{os.environ['PATH']}", PY=sys.executable, MEDIAKIT_CODEX_ESPERA="0")
    r = subprocess.run(["bash", str(SCRIPT), "c-teste", "p.txt", "acervo"], cwd=tmp_path, env=env, capture_output=True,
                       text=True)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "acervo" / "c-teste.png").exists()
    assert [g["resultado"] for g in json.loads((tmp_path / "acervo" / "cota.json").read_text())] == ["ok"]


def test_imagem_que_ja_existe_nao_gasta_cota(tmp_path):
    r, acervo = _rodar(tmp_path, _codex_falso(tmp_path))
    prompt = tmp_path / "p.txt"
    env = dict(os.environ, PATH=f"{tmp_path / 'bin'}:{os.environ['PATH']}", PY=sys.executable)
    subprocess.run(["bash", str(SCRIPT), "c-teste", str(prompt), str(acervo)], env=env, capture_output=True, text=True)
    assert len(json.loads((acervo / "cota.json").read_text())) == 1

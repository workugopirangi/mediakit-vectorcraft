#!/usr/bin/env python3
"""Provas dos comandos de acabamento do tratar.py: reflexo, alfa-degraus e textura. Rodar: ~/.venvs/mediakit/bin/python
test_tratar.py (ou pytest). Cada prova roda o comando como o pipeline roda (processo separado, pela linha de comando) sobre um
PNG sintético pequeno e mede o arquivo gravado: tamanho, pixel e alfa. Nada é escrito fora de uma pasta temporária."""
import subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image

AQUI = Path(__file__).parent
PY = sys.executable
VERMELHO, AZUL = (220, 40, 40), (30, 60, 200)


def tratar(*args):
    return subprocess.run([PY, str(AQUI / "tratar.py"), *map(str, args)], capture_output=True, text=True)


def objeto(caminho):
    """PNG 120 x 300, transparente em volta. Tinta da linha 40 à 239 (200 px de altura): corpo vermelho (colunas 20 a 99) e
    pé azul nas últimas 50 linhas (colunas 30 a 89, mais estreito). Assim se vê o que foi parar onde no espelho."""
    arr = np.zeros((300, 120, 4), np.uint8)
    arr[40:190, 20:100] = VERMELHO + (255,)
    arr[190:240, 30:90] = AZUL + (255,)
    Image.fromarray(arr, "RGBA").save(caminho)


def perto(px, cor, tol=6):
    return all(abs(int(a) - b) <= tol for a, b in zip(px[:3], cor))


# --------------------------------------------------------------------------------------------- reflexo
def test_reflexo_espelha_achata_e_grava_a_rampa_no_alfa():
    with tempfile.TemporaryDirectory() as d:
        ob, sai = Path(d) / "trofeu.png", Path(d) / "trofeu-reflexo.png"
        objeto(ob)
        r = tratar("reflexo", ob, sai)
        assert r.returncode == 0, r.stderr
        im = Image.open(sai)
        assert im.mode == "RGBA", im.mode
        # altura = .35 x a altura da tinta (200 px); largura = a do PNG do objeto (as colunas não mudam)
        assert im.size == (120, 70), im.size
        arr = np.asarray(im)
        # espelhado: o pé azul (embaixo no objeto) é o que encosta no topo do reflexo; o corpo vermelho vem depois.
        # Achatado em .9: os 50 px do pé viram 45 linhas, então a linha 60 já é corpo
        assert perto(arr[2, 60], AZUL) and arr[2, 60, 3] > 0, arr[2, 60]
        assert perto(arr[60, 60], VERMELHO) and arr[60, 60, 3] > 0, arr[60, 60]
        # as colunas são as do objeto: na linha do pé, a coluna 25 (fora do pé) é vazia; na linha do corpo, tem tinta
        assert arr[2, 25, 3] == 0 and arr[60, 25, 3] > 0
        # rampa: .32 de opacidade colada ao pé, decrescente linha a linha, zero na base
        topo = arr[..., 3].max(axis=1).astype(int)
        assert abs(topo[0] - round(0.32 * 255)) <= 1, topo[0]
        assert all(b <= a for a, b in zip(topo, topo[1:])), topo
        assert topo[-1] == 0 and topo[len(topo) // 2] < topo[0], topo
        # as opções mudam a medida: .5 da altura e achatado em .8 = 100 linhas, e o pé ocupa 40 delas
        sai2 = Path(d) / "r2.png"
        r = tratar("reflexo", ob, sai2, "--altura", ".5", "--achatar", ".8", "--opacidade", ".5")
        assert r.returncode == 0, r.stderr
        arr2 = np.asarray(Image.open(sai2))
        assert arr2.shape[:2] == (100, 120), arr2.shape
        assert perto(arr2[36, 60], AZUL) and perto(arr2[44, 60], VERMELHO), (arr2[36, 60], arr2[44, 60])
        assert abs(int(arr2[..., 3].max(axis=1)[0]) - round(0.5 * 255)) <= 1
    print("   reflexo 120 x 70 (.35 de 200 px), pé azul no topo, alfa 82 -> 0 sem subir")


def test_reflexo_recusa_o_que_nao_e_recorte_e_valor_fora():
    with tempfile.TemporaryDirectory() as d:
        chapado = Path(d) / "c.png"
        Image.new("RGBA", (50, 50), (0, 0, 0, 0)).save(chapado)
        r = tratar("reflexo", chapado, Path(d) / "s.png")
        assert r.returncode != 0 and "sem tinta" in r.stderr and not (Path(d) / "s.png").exists(), r.stderr
        ob = Path(d) / "o.png"
        objeto(ob)
        for ruim in (["--altura", "0"], ["--opacidade", "1.5"], ["--achatar", "-1"]):
            r = tratar("reflexo", ob, Path(d) / "s.png", *ruim)
            assert r.returncode != 0 and not (Path(d) / "s.png").exists(), (ruim, r.stderr)
        r = tratar("reflexo", ob, Path(d) / "s.jpg")
        assert r.returncode != 0 and ".png" in r.stderr


# --------------------------------------------------------------------------------------------- alfa em degraus
def test_alfa_degraus_tem_exatamente_n_niveis():
    with tempfile.TemporaryDirectory() as d:
        e = Path(d) / "e.png"
        Image.new("RGB", (160, 48), (200, 160, 70)).save(e)          # sem alfa: parte de opaco
        for direcao in ("dir", "esq", "cima", "baixo"):
            for passos in (3, 5, 8):
                s = Path(d) / f"s-{direcao}-{passos}.png"
                r = tratar("alfa-degraus", e, s, "--direcao", direcao, "--passos", passos, "--minimo", ".12")
                assert r.returncode == 0, r.stderr
                a = np.asarray(Image.open(s))[..., 3].astype(int)
                valores = sorted(set(a.ravel().tolist()))
                assert len(valores) == passos, (direcao, passos, valores)
                assert valores[-1] == 255 and valores[0] == round(0.12 * 255), (direcao, passos, valores)
                eixo = a[0] if direcao in ("dir", "esq") else a[:, 0]       # o perfil ao longo da direção
                if direcao in ("esq", "cima"):
                    eixo = eixo[::-1]
                assert eixo[0] == 255 and eixo[-1] == valores[0], (direcao, eixo[:3], eixo[-3:])
                assert all(b <= a_ for a_, b in zip(eixo, eixo[1:])), (direcao, passos)
                # cada degrau é uma faixa inteira: a imagem é constante na outra direção
                assert (a == a[:1]).all() if direcao in ("dir", "esq") else (a == a[:, :1]).all()
        # 5 degraus em 160 px: faixas iguais de 32 px
        a = np.asarray(Image.open(Path(d) / "s-dir-5.png"))[..., 3][0]
        assert [int((a == v).sum()) for v in sorted(set(a.tolist()), reverse=True)] == [32] * 5
    print("   3, 5 e 8 degraus nas 4 direções: exatamente N valores de alfa, do opaco ao mínimo .12")


def test_alfa_degraus_cobre_a_tinta_e_multiplica_o_alfa():
    with tempfile.TemporaryDirectory() as d:
        e = Path(d) / "e.png"
        arr = np.zeros((40, 200, 4), np.uint8)
        arr[5:35, 50:150] = (10, 10, 10, 255)                          # tinta só no miolo: 100 px de largura
        Image.fromarray(arr, "RGBA").save(e)
        s = Path(d) / "s.png"
        r = tratar("alfa-degraus", e, s, "--direcao", "dir", "--passos", "4", "--minimo", "0")
        assert r.returncode == 0, r.stderr
        a = np.asarray(Image.open(s))[..., 3].astype(int)
        tinta = a[20, 50:150]
        assert sorted(set(tinta.tolist())) == [0, 85, 170, 255], sorted(set(tinta.tolist()))   # os 4 degraus caem na tinta
        assert (a[:5] == 0).all() and (a[:, :50] == 0).all(), "o vazio continua vazio"


def test_alfa_degraus_recusa_fora_do_contrato():
    with tempfile.TemporaryDirectory() as d:
        e = Path(d) / "e.png"
        Image.new("RGB", (40, 40), (1, 2, 3)).save(e)
        for ruim in (["--passos", "2", "--minimo", ".1"], ["--passos", "9", "--minimo", ".1"], ["--passos", "4", "--minimo", ".5"],
                     ["--passos", "4", "--minimo", "-.1"]):
            r = tratar("alfa-degraus", e, Path(d) / "s.png", "--direcao", "dir", *ruim)
            assert r.returncode != 0 and not (Path(d) / "s.png").exists(), (ruim, r.stderr)
        r = tratar("alfa-degraus", e, Path(d) / "s.png", "--direcao", "diagonal", "--passos", "4", "--minimo", ".1")
        assert r.returncode != 0 and "invalid choice" in r.stderr


# --------------------------------------------------------------------------------------------- textura única
def gradiente(caminho, w, h, modo="RGB", alfa=255):
    """Escuro na esquerda, claro na direita: ladrilhar ou espelhar quebraria a subida."""
    x = np.linspace(0, 255, w)[None, :].repeat(h, 0)
    rgb = np.stack([x, x * .8, x * .6], -1)
    if modo == "RGBA":
        rgb = np.concatenate([rgb, np.full((h, w, 1), alfa)], -1)
    Image.fromarray(rgb.astype(np.uint8), modo).save(caminho)


def test_textura_sai_a_1x_em_jpeg_sem_alfa_e_inteira():
    with tempfile.TemporaryDirectory() as d:
        e, s = Path(d) / "papel.png", Path(d) / "papel.jpg"
        gradiente(e, 3000, 1500)
        r = tratar("textura", e, s)
        assert r.returncode == 0, r.stderr
        im = Image.open(s)
        assert im.format == "JPEG" and im.mode == "RGB" and im.size == (1920, 960), (im.format, im.mode, im.size)
        col = np.asarray(im.convert("L"), dtype=float).mean(axis=0)
        # uma imagem só, inteira: a luminância sobe da esquerda para a direita sem voltar (tile ou espelho faria voltar)
        blocos = [col[i:i + 120].mean() for i in range(0, 1920, 120)]
        assert all(b > a for a, b in zip(blocos, blocos[1:])), blocos
        # RGBA todo opaco também é sem alfa: entra e sai RGB; a largura e a qualidade são opções
        e2, s2 = Path(d) / "opaco.png", Path(d) / "opaco.jpg"
        gradiente(e2, 1000, 500, "RGBA", 255)
        r = tratar("textura", e2, s2, "--largura", "640", "--q", "70")
        assert r.returncode == 0 and Image.open(s2).size == (640, 320) and Image.open(s2).mode == "RGB", r.stderr
    print("   3000 x 1500 -> 1920 x 960 JPEG RGB, uma imagem inteira (sem tile)")


def test_textura_recusa_alfa_real_e_nao_amplia():
    with tempfile.TemporaryDirectory() as d:
        e, s = Path(d) / "tinta.png", Path(d) / "tinta.jpg"
        gradiente(e, 400, 200, "RGBA", 120)
        r = tratar("textura", e, s)
        assert r.returncode != 0 and "alfa real" in r.stderr and "preparar" in r.stderr and not s.exists(), r.stderr
        r = tratar("textura", Path(d) / "x.png", Path(d) / "x.png")
        assert r.returncode != 0 and "JPEG" in r.stderr
        pequena, s2 = Path(d) / "p.png", Path(d) / "p.jpg"
        gradiente(pequena, 800, 300)
        r = tratar("textura", pequena, s2)
        assert r.returncode == 0 and Image.open(s2).size == (800, 300) and "ampliar não cria detalhe" in r.stdout, r.stdout


if __name__ == "__main__":
    falhas = 0
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            try:
                f(); print("ok  ", nome)
            except AssertionError as e:
                falhas += 1; print("FALHOU", nome, e)
    print("PROVAS:", "VERDES" if not falhas else f"{falhas} FALHA(S)")
    sys.exit(1 if falhas else 0)

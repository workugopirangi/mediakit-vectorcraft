#!/usr/bin/env python3
"""Provas do padrao.py. Rodar: ~/.venvs/mediakit/bin/python test_padrao.py (ou pytest). Usa só tiles sintéticos,
gravados numa pasta temporária: não gasta cota nem toca em kit."""
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
import padrao  # noqa: E402

PY = sys.executable


def roda(*args):
    return subprocess.run([PY, str(AQUI / "padrao.py"), *map(str, args)], capture_output=True, text=True)


def tile_periodico(n=512, semente=1):
    return padrao._linhas_periodicas(n, np.random.default_rng(semente))


def tile_descasado(n=512, semente=1):
    """Traço fino do mesmo tipo, desenhado sem volta e recortado fora do eixo: o que sai por uma borda não volta pela
    outra. É o defeito típico de um "tile" que o gerador entrega sem ser seamless de verdade."""
    return padrao._linhas_periodicas(n, np.random.default_rng(semente), periodico=False)


def test_checar_reprova_tile_com_costura():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "descasado.png"; tile_descasado().save(p)
        r = roda("checar", p)
        print(r.stdout.strip())
        assert r.returncode == 1 and "REPROVADO" in r.stdout, r.stdout
        assert (Path(d) / "descasado.mosaico.png").exists()


def test_checar_aprova_tile_periodico():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "bom.png"; tile_periodico().save(p)
        r = roda("checar", p)
        print(r.stdout.strip())
        assert r.returncode == 0 and "APROVADO" in r.stdout, r.stdout


def test_tornar_seamless_corrige():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "descasado.png"; tile_descasado().save(p)
        for metodo in ("costurar", "cruzar", "espelho"):
            o = Path(d) / f"{metodo}.png"
            assert roda("tornar-seamless", p, o, "--metodo", metodo).returncode == 0
            r = roda("checar", o)
            print(metodo, r.stdout.strip())
            assert r.returncode == 0, r.stdout


def test_alfa_distingue_rgb_de_transparente():
    with tempfile.TemporaryDirectory() as d:
        rgb = Path(d) / "rgb.png"; Image.new("RGB", (64, 64), (128, 128, 128)).save(rgb)
        opaco = Path(d) / "opaco.png"; Image.new("RGBA", (64, 64), (128, 128, 128, 255)).save(opaco)
        t = Path(d) / "t.png"; tile_periodico(128).save(t)
        assert roda("alfa", rgb).returncode == 1
        assert roda("alfa", opaco).returncode == 1   # RGBA com alfa todo 255 não é transparência
        assert roda("alfa", t).returncode == 0


def test_separar_tira_fundo_branco():
    with tempfile.TemporaryDirectory() as d:
        alfa = np.asarray(tile_periodico(256))[..., 3].astype(float) / 255
        rgb = (255 * (1 - alfa))[..., None].repeat(3, axis=2).astype(np.uint8)   # tinta preta sobre branco
        e = Path(d) / "e.png"; Image.fromarray(rgb, "RGB").save(e)
        s = Path(d) / "s.png"
        assert roda("separar", e, s).returncode == 0
        out = np.asarray(Image.open(s))
        assert out.shape[2] == 4
        assert out[..., 3][alfa == 0].max() == 0          # fundo some
        assert out[..., 3][alfa > 0.95].min() > 230        # tinta fica
        assert out[..., :3][alfa > 0.5].max() < 40         # sem halo branco na tinta


def test_separar_pattern_que_cobre_o_tile_tira_o_branco_e_nao_a_tinta():
    """O pattern de ondas da r2 da Sprint cobria 80% do tile de azul: a cor mais frequente era a TINTA, o separar a
    tratava como fundo e sobrava a espuma branca (invisível no papel creme). O fundo do caminho codex-branco é o branco
    que o prompt pede, não a cor mais frequente."""
    with tempfile.TemporaryDirectory() as d:
        rgb = np.full((240, 240, 3), (32, 103, 170), np.uint8)          # azul em 80% do tile
        rgb[::5, :] = 255; rgb[:, ::5] = 255                              # grade branca (o "papel" entre a tinta)
        e = Path(d) / "e.png"; Image.fromarray(rgb, "RGB").save(e)
        s = Path(d) / "s.png"
        r = roda("separar", e, s, "--fundo", "#FFFFFF")
        assert r.returncode == 0, r.stdout + r.stderr
        out = np.asarray(Image.open(s))
        azul = (rgb == (32, 103, 170)).all(axis=2)
        assert out[..., 3][azul].min() > 230, "a tinta azul sumiu: o fundo foi tomado pela cor mais frequente"
        assert out[..., 3][~azul].max() < 30, "o branco do papel ficou opaco"


def test_variantes_saem_com_alfa_e_na_cor():
    with tempfile.TemporaryDirectory() as d:
        t = Path(d) / "penas.png"; tile_periodico(256).save(t)
        feitos = padrao.variantes(str(t), ["#D4A64A", "#0B0B0C"], d)
        nomes = sorted(f.name for f in feitos)
        assert nomes == sorted(["penas-traco.png", "penas-chapado.png", "penas-traco-c2.png", "penas-chapado-c2.png", "penas-tingido.png"]), nomes
        traco = np.asarray(Image.open(Path(d) / "penas-traco.png"))
        assert tuple(traco[traco[..., 3] > 0][0][:3]) == (0xD4, 0xA6, 0x4A)
        chap = np.asarray(Image.open(Path(d) / "penas-chapado.png"))[..., 3]
        assert (chap > 0).mean() >= (traco[..., 3] > 0).mean()   # silhueta cobre pelo menos o traço
        for f in feitos:
            assert Image.open(f).mode == "RGBA"


def _palavra(texto, tam=110, cor=(212, 166, 74, 255)):
    from PIL import ImageDraw, ImageFont
    f = ImageFont.truetype(str(AQUI.parent / "fontes-livres" / "Kanit" / "Kanit__800.ttf"), tam)
    im = Image.new("RGBA", (int(tam * len(texto) * 0.9) + 80, int(tam * 1.8) + 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((40, 20), texto, font=f, fill=cor)
    return im


def test_texto_reprova_palavra_escrita():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "sprint.png"; _palavra("SPRINT").save(p)
        r = roda("texto", p)
        print(r.stdout.strip())
        assert r.returncode == 1 and "REPROVADO" in r.stdout and "SPRINT" in r.stdout, r.stdout + r.stderr
        r = roda("texto", p, "--json")
        j = json.loads(r.stdout)
        assert j["aprovado"] is False and j["ocr"] == "SPRINT", j


def test_texto_aprova_desenho_sem_letra():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "traco.png"; tile_periodico(512).save(p)
        r = roda("texto", p)
        print(r.stdout.strip())
        assert r.returncode == 0 and "APROVADO" in r.stdout, r.stdout + r.stderr


def test_funcao_texto_e_o_veredito_que_a_biblioteca_grava():
    """padrao.texto() (o que o biblioteca.registrar grava em `ocr`): a palavra escrita volta; o traço sem letra, vazio."""
    with tempfile.TemporaryDirectory() as d:
        com, sem = Path(d) / "sprint.png", Path(d) / "traco.png"
        _palavra("SPRINT").save(com); tile_periodico(512).save(sem)
        assert padrao.texto(com) == "SPRINT", padrao.texto(com)
        assert padrao.texto(sem) == "", padrao.texto(sem)


def test_preparar_uso_corta_no_alfa_e_reduz_para_2x():
    with tempfile.TemporaryDirectory() as d:
        a = np.zeros((800, 1000, 4), np.uint8)
        a[200:500, 100:700] = (200, 150, 60, 255)
        a[750, 950] = (255, 255, 255, 5)                       # franja quase invisível do gerador: não entra na caixa
        p = Path(d) / "obj.png"; Image.fromarray(a, "RGBA").save(p)
        assert padrao.alfa_bbox(p) == (100, 200, 700, 500)
        h1 = padrao.preparar_uso(p, 150, Path(d) / "uso.png")
        assert Image.open(Path(d) / "uso.png").size == (300, 150)              # 2 x 150 px de uso, proporção mantida
        assert h1 == hashlib.sha256((Path(d) / "uso.png").read_bytes()).hexdigest()
        assert padrao.preparar_uso(p, 150, Path(d) / "uso2.png") == h1         # determinístico (serve de chave de cache)
        padrao.preparar_uso(p, 1000, Path(d) / "grande.png")
        assert Image.open(Path(d) / "grande.png").size == (600, 300)           # nunca amplia
        r = roda("preparar_uso", p, 150, Path(d) / "cli.png")
        assert r.returncode == 0 and h1 in r.stdout, r.stdout + r.stderr
        Image.fromarray(np.zeros((10, 10, 4), np.uint8), "RGBA").save(Path(d) / "vazio.png")
        try:
            padrao.preparar_uso(Path(d) / "vazio.png", 100, Path(d) / "x.png")
        except ValueError:
            pass
        else:
            raise AssertionError("aceitou PNG sem nada visível")


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

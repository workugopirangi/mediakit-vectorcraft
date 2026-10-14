#!/usr/bin/env python3
"""Provas do elementos_prompt.py, do cena_prompt.py, do composicao_prompt.py e do elementos.sh em modo seco, e do `faltantes`
com a composição. Rodar: ~/.venvs/mediakit/bin/python test_elementos_prompt.py (ou pytest). Não chama o Codex: nenhuma imagem
da cota é gasta (o que gera usa um `codex` falso, em test_codex.py)."""
import hashlib, json, os, re, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI))
import elementos_prompt as ep  # noqa: E402
import composicao_prompt as cp  # noqa: E402
import plano_elementos as pe  # noqa: E402

PY = sys.executable
HEX = re.compile(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b")
ESTILO = "photoreal product photo, warm early morning side light from the left, soft contact shadow, gold and black palette"


def sh(*args, env_extra=None, cwd=None):
    env = dict(os.environ, MEDIAKIT_PY=PY, **(env_extra or {}))
    return subprocess.run(["bash", str(AQUI / "elementos.sh"), *map(str, args)], capture_output=True, text=True, env=env, cwd=cwd)


def test_nome_de_cor_no_lugar_do_hex():
    assert ep.nome_cor("#D4A64A") == "antique gold"
    assert ep.nome_cor("#281805") == "near-black brown"
    assert ep.nome_cor("#2067AA") == "sea blue"
    p = ep.montar_prompt("objeto", "a stopwatch, accent #D4A64A", "/x/a.bruto.png", estilo="gold like #D4A64A", paleta="#D09050,#281805")
    assert not HEX.search(p), HEX.search(p)                     # nenhum hex sobra, nem o que veio no estilo e na descrição
    assert "light caramel as the dominant color, with near-black brown" in p
    assert "gold like antique gold" in p


def test_todo_tipo_leva_as_regras():
    for tipo in ep.TIPOS:
        for aspecto in ep.ASPECTOS:
            p = ep.montar_prompt(tipo, "a running shoe", "/abs/kit/acervo/elementos/x.bruto.png", estilo="flat two-tone", paleta="#D4A64A", aspecto=aspecto)
            for frase in ("NO text of any kind", "no letters, no numbers", "no logos", "fully transparent (PNG with a real alpha channel)",
                          "Do NOT regenerate", "exactly one image generation call", "/abs/kit/acervo/elementos/x.bruto.png",
                          "TRANSPARENT: yes", "Style/medium: flat two-tone", ep.FORMATO[aspecto].split(",")[0]):
                assert frase in p, (tipo, aspecto, frase)
            assert ep.FRASE_ANCORA not in p                         # sem âncora, nada de referência anexada
            itens = re.findall(r"\((\d)\)", p.split("After saving")[1])
            assert itens == [str(i) for i in range(1, len(itens) + 1)], itens   # conferência numerada sem buraco


def test_ancora_entra_so_com_ref():
    p = ep.montar_prompt("pictograma", "a running shoe", "/x/a.bruto.png", ref=True)
    assert ep.FRASE_ANCORA in p and "Input images: Image 1 (attached) is a STYLE REFERENCE only" in p
    assert "Do not edit, copy or overwrite the attached reference" in p


def test_tipo_e_aspecto_invalidos():
    for ruim, kw in (("selo", {}), ("microtexto", {}), ("objeto", {"aspecto": "panorama"}), ("objeto", {"luz": "baixo"})):
        try:
            ep.montar_prompt(ruim, "x", "/x.png", **kw)
        except ValueError as e:
            print("  recusado:", e)
            continue
        raise AssertionError(f"aceitou {ruim} {kw}")


def test_ornamento_continua_como_na_v1():
    p = ep.montar_prompt("ornamento", "a gold medal", "/x/m.bruto.png")
    assert "Photorealistic product photograph" in p and "key light from the LEFT" in p
    assert "mid grey background (50% grey)" in p and "no cast shadow on the background" in p
    assert ep.RESERVA["objeto"] == "cinza" and ep.RESERVA["pattern"] == "branco"


def test_pattern_pede_costura():
    p = ep.montar_prompt("pattern", "feathers", "/x/p.bruto.png")
    assert "SEAMLESS: the tile must wrap around" in p and "top edge continues exactly on the bottom edge" in p
    assert "Solid black ink only" in p and "pure white background" in p          # reserva da v1 (chroma)
    f = ep.montar_prompt("pattern", "waves", "/x/p.bruto.png", aspecto="faixa")
    assert "SEAMLESS LEFT TO RIGHT" in f and "top edge" not in f


def test_dry_imprime_prompt_e_comando_sem_gastar_cota():
    with tempfile.TemporaryDirectory() as d:
        ref = Path(d) / "a.png"; Image.new("RGBA", (8, 8), (200, 160, 70, 255)).save(ref)
        r = sh(Path(d) / "kit", "x", "pictograma", "a running shoe seen from the side", "--estilo", "flat two-tone pictogram, bold even strokes",
               "--paleta", "#D4A64A", "--ref", "a.png", env_extra={"ELEMENTOS_DRY": "1"}, cwd=d)
        print(r.stdout[-400:])
        assert r.returncode == 0, r.stderr
        assert "Style/medium: flat two-tone pictogram, bold even strokes" in r.stdout
        assert "antique gold" in r.stdout and not HEX.search(r.stdout.split("== COMANDO")[0])
        assert "Square 1:1 image" in r.stdout and ep.FRASE_ANCORA in r.stdout
        comando = r.stdout.split("== COMANDO")[1]
        anexo = Path(comando.split(" -i ")[1].split(" ")[0])          # o -i leva o caminho absoluto da âncora
        assert comando.strip().startswith("codex exec") and anexo.resolve() == ref.resolve() and comando.index(" -i ") < comando.index(" -o ")
        assert not (Path(d) / "kit").exists()                    # modo seco não grava nada


def test_dry_aceita_a_chamada_antiga_e_a_forma_com_opcao():
    with tempfile.TemporaryDirectory() as d:
        r = sh(Path(d) / "kit", "m", "ornamento", "a gold medal", env_extra={"ELEMENTOS_DRY": "1"})
        assert r.returncode == 0 and "tipo=objeto" in r.stdout and " -i " not in r.stdout, r.stdout + r.stderr
        r = sh(Path(d) / "kit", "p", "feathers", "--tipo", "pattern", "--aspecto", "faixa", env_extra={"ELEMENTOS_DRY": "1"})
        assert r.returncode == 0 and "tipo=pattern aspecto=faixa" in r.stdout, r.stdout + r.stderr
        for ruim in (["k", "x", "selo", "texto"], ["k", "X Maiúsculo", "objeto", "a"], ["k", "x", "objeto", "a", "--paleta", "dourado"],
                     ["k", "x", "objeto", "a", "--aspecto", "panorama"], ["k", "x"]):
            r = sh(*ruim, env_extra={"ELEMENTOS_DRY": "1"})
            assert r.returncode == 64, (ruim, r.returncode, r.stdout, r.stderr)


def test_ficha_meta_com_geracoes_contadas():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        a = np.zeros((64, 64, 4), np.uint8); a[16:48, 16:48] = (210, 150, 80, 255)
        Image.fromarray(a, "RGBA").save(d / "obj.bruto.png"); Image.fromarray(a, "RGBA").save(d / "obj.png")
        runs = d / ".claude" / "state" / "runs" / "r1"; runs.mkdir(parents=True)
        (runs / "events.jsonl").write_text("\n".join(json.dumps(e) for e in [
            {"tool": "image_genimagegen"}, {"tool": "Bash", "target": "cp gen.png 'obj.bruto.png'"}]) + "\n")
        r = subprocess.run([PY, str(AQUI / "elementos_prompt.py"), "meta", "--id", "obj", "--pasta", str(d), "--png", str(d / "obj.png"),
                            "--bruto", str(d / "obj.bruto.png"), "--tipo", "ornamento", "--rota", "codex-alfa", "--familia", "objeto-dourado",
                            "--paleta", "#D09050,#281805", "--aspecto", "quadrado", "--ref", str(d / "obj.png")], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        m = json.loads((d / "obj.meta.json").read_text())
        for k in ("tipo", "familia", "motivo", "estilo", "paleta", "aspecto", "ref", "rota", "sha256", "alfa", "data"):
            assert k in m, k
        assert m["tipo"] == "objeto" and m["geracoes_medidas"] == 1 and m["alfa"]["real"] is True
        assert m["paleta_nomes"] == ["light caramel", "near-black brown"] and len(m["sha256"]) == 64


# ================================================================= o elemento nasce para a página (a composição no prompt)
ESTILO_CENA = ("early morning, low sun rising behind the coastal mountains on the left, warm golden side light, clear sky with "
               "light haze over the sea, 35mm lens f/4, eye level, palette of black, gold, sand and sea blue, people in plain "
               "black or gold shirts")


def _ancora_sangra():
    return {"relacao": "sangra", "borda": "dir", "corte": "1/3", "y": "cy=foto.cy"}


def montar_kit(pasta, com_plano=True, estilo_cena=ESTILO_CENA):
    """Kit mínimo: mediakit.json com `composicao` (um herói que sangra à direita da página ativo:2, outro que sobrepõe a foto
    na cota Master, espelhado e girado) e, com `com_plano`, a maquete (saida/plano-elementos-r1.json) com a caixa resolvida
    do primeiro: 540 x 360 px de tinta, 1/3 fora da página, o título à esquerda da foto."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    kit = {"evento": {"nome": "Sprint Ubatuba Run", "cidade": "Ubatuba", "uf": "SP", "modalidade_sistema": "corrida de rua"},
           "marca": {"cor_primaria": "#D4A64A", "estilo_cena": estilo_cena},
           "elementos": [{"id": "trofeu", "papel": "heroi", "tipo": "objeto", "formato": "png", "aspecto": "alto", "motivo": "podio",
                          "familia": "objeto-dourado", "arquivo": "acervo/elementos/trofeu.png"},
                         {"id": "bola", "papel": "heroi", "tipo": "objeto", "formato": "png", "aspecto": "largo", "rota": "a-gerar"}],
           "composicao": {
               "ativo:2": {"mensagem": "o troféu sai da foto em direção ao título", "foco": "titulo", "leitura": ["titulo", "trofeu"],
                           "estrutura": "título à esquerda, foto à direita",
                           "elementos": [{"id": "trofeu", "papel": "heroi", "funcao": "profundidade", "camada": "frente",
                                          "ancora": _ancora_sangra(), "escala": {"altura": "1/3p"},
                                          "porque": "o troféu sai da foto em direção ao título"}]},
               "cota:Master": {"mensagem": "a bola entra na foto", "foco": "foto",
                               "elementos": [{"id": "bola", "papel": "heroi", "funcao": "profundidade", "camada": "frente",
                                              "ancora": {"relacao": "sobrepoe", "alvo": "foto", "lado": "esq", "fracao": "1/3",
                                                         "y": "base=foto.base-e5"},
                                              "escala": {"altura": "1/2p"}, "rot": -12, "espelhar": True,
                                              "porque": "a bola entra na foto pela esquerda"}]}}}
    (pasta / "mediakit.json").write_text(json.dumps(kit, ensure_ascii=False, indent=1), encoding="utf-8")
    if com_plano:
        alvos = {"pagina": {"x": 0, "y": 0, "w": 1920, "h": 1080}, "margem": {"x": 96, "y": 96, "w": 1728, "h": 888},
                 "colunas": [{"x": 96 + i * 152, "w": 128} for i in range(11)],
                 "titulo": {"x": 700, "y": 120, "w": 700, "h": 200,
                            "linhas": [{"x": 700, "y": 120, "w": 700, "h": 100, "linha_base": 200, "cap": 130, "texto": "SUA MARCA"},
                                       {"x": 700, "y": 220, "w": 560, "h": 100, "linha_base": 300, "cap": 230, "texto": "NA LARGADA"}]},
                 "foto": {"x": 824, "y": 0, "w": 1096, "h": 1080, "img": {"nat_w": 2880, "nat_h": 1620, "fit": "cover", "pos": "50% 50%"}}}
        item = {"id": "trofeu", "papel": "heroi", "encaixe": "composicao", "camada": "frente", "x": 1530.0, "y": 280.0, "w": 600.0, "h": 420.0,
                "rot": 0.0, "origem": "composicao", "funcao": "profundidade",
                "ancora": {"relacao": "sangra", "restricoes": [], "tinta": [1560.0, 300.0, 2100.0, 660.0],
                           "escala": {"altura": "1/3p"}, "degrau": True}}
        plano = {"receita": "r1", "formato": "horizontal", "largura": 1920, "altura": 1080, "paginas": [
            {"n": 5, "rotulo": "ativo:painel", "tipo": "ativo_painel", "rotulos": ["ativo", "ativo:2", "ativo:painel", "ativo_painel"],
             "elegivel_heroi": True, "elementos": [item], "protegidos": [], "alvos": alvos}]}
        (pasta / "saida").mkdir(exist_ok=True)
        (pasta / "saida" / "plano-elementos-r1.json").write_text(json.dumps(plano, ensure_ascii=False), encoding="utf-8")


def test_composicao_no_prompt_com_a_caixa_da_maquete():
    with tempfile.TemporaryDirectory() as d:
        montar_kit(d)
        c = cp.contexto(d, "ativo:2", "trofeu")
        assert c["origem_da_medida"] == "plano" and c["area_px"] == [540, 360] and c["plano"] == "plano-elementos-r1.json", c
        assert c["aspecto"] == "largo" and c["lado"] == ("right", "middle") and c["rumo"] == "left" and c["sangra"] == {"borda": "right", "corte": "1/3"}
        p = ep.montar_prompt("objeto", "a gold trophy", "/x/trofeu.bruto.png", estilo="photoreal product photo, gold and black",
                             paleta="#D4A64A,#281805", composicao=c)
        print(p.split("Style/medium")[1].split("Color palette")[0])
        # a proporção REAL da maquete (1,50:1) vence o aspecto declarado do kit (alto): o gerador recebe o formato da página
        assert "Landscape 3:2 image, 1536x1024" in p and "Portrait" not in p
        assert "this object appears about 540 x 360 px (ratio 1.50:1, landscape), on the right side of the page" in p
        assert "final 1920 x 1080 px page" in p
        assert "It must point and face toward the left, at the title" in p
        # o objeto nasce inteiro e centrado; o corte é da página, e o detalhe-chave fica do lado oposto
        assert "whole object, centered, nothing cropped; the page will crop it on the right side, keep the key detail on the left side" in p
        assert "generous empty margin on every side" not in p
        assert "The page crops about a third of it on the right side." in p
        # luz e lente da foto da página
        assert "key light from the LEFT, gentle fill from the opposite side, the same direction as the light in the page photo (early morning" in p
        assert "low sun rising behind the coastal mountains on the left" in p
        assert "Perspective: like the page photo (35mm lens f/4, eye level), no extreme foreshortening; turned slightly toward the left." in p
        assert "Its role on the page: depth (it enters the photo and leaves it)." in p
        assert "the key detail is on the left side, away from the right edge" in p and "the object faces toward the left" in p
        assert not HEX.search(p), HEX.search(p)
        assert "Background: fully transparent" in p and "NO text of any kind" in p
        # o que o usuário pede à mão vence: --aspecto, --luz
        q = ep.montar_prompt("objeto", "a gold trophy", "/x/t.bruto.png", aspecto="quadrado", luz="direita", composicao=c)
        assert "Square 1:1 image" in q and "key light from the RIGHT, gentle fill from the opposite side." in q and "the same direction as the light in the page photo" not in q
        # pictograma e adesivo seguem o mesmo molde; pattern e textura enchem o quadro e só ganham a medida
        pa = ep.montar_prompt("adesivo", "a flag sticker", "/x/a.bruto.png", composicao=c)
        assert "One sticker, whole, centered, nothing cropped" in pa and "the page will crop it on the right side" in pa
        pt = ep.montar_prompt("pattern", "feathers", "/x/p.bruto.png", composicao=c)
        assert "It must point and face" not in pt and "the page will crop" not in pt and "SEAMLESS: the tile must wrap around" in pt
        assert "appears about 540 x 360 px" in pt


def test_composicao_sem_plano_usa_a_escala_e_o_aspecto_declarados():
    with tempfile.TemporaryDirectory() as d:
        montar_kit(d, com_plano=False)
        c = cp.contexto(d, "ativo:2", "trofeu")
        assert c["origem_da_medida"] == "escala e aspecto declarados" and c["area_px"] == [240, 360], c     # 1/3 da altura, aspecto alto
        assert c["aspecto"] == "alto" and c["lado"] == ("right", "middle") and c["rumo"] == "left" and c["alvo_do_foco"] == "the inside of the page"
        p = ep.montar_prompt("objeto", "a gold trophy", "/x/trofeu.bruto.png", composicao=c)
        assert "Portrait 2:3 image, 1024x1536" in p
        assert "about 240 x 360 px (ratio 0.67:1, portrait), on the right side of the page" in p
        assert "toward the left, at the inside of the page" in p and "the page will crop it on the right side" in p
        # sem o plano nem o título medido, a escala em altura de maiúscula não tem como virar px: sem tamanho, só o aspecto
        kit = json.loads((Path(d) / "mediakit.json").read_text())
        kit["composicao"]["ativo:2"]["elementos"][0]["escala"] = {"altura": "3cap", "de": "titulo"}
        (Path(d) / "mediakit.json").write_text(json.dumps(kit))
        c2 = cp.contexto(d, "ativo:2", "trofeu")
        assert c2["area_px"] is None and c2["aspecto"] == "alto", c2
        p2 = ep.montar_prompt("objeto", "a gold trophy", "/x/trofeu.bruto.png", composicao=c2)
        assert "Portrait 2:3" in p2 and " px (ratio" not in p2


def test_composicao_espelho_giro_sobreposicao_e_luz_do_outro_lado():
    with tempfile.TemporaryDirectory() as d:
        montar_kit(d, com_plano=False)
        c = cp.contexto(d, "cota:Master", "bola")
        assert c["area_px"] == [810, 540] and c["aspecto"] == "largo" and c["lado"] == ("left", "lower") and c["rot"] == -12 and c["espelhar"]
        assert c["sobrepoe"] == {"alvo": "foto", "lado": "left", "fracao": "1/3"} and c["rumo"] == "upper right"
        p = ep.montar_prompt("objeto", "a football", "/x/bola.bruto.png", composicao=c)
        assert "Draw it upright: the page rotates it by -12 degrees." in p
        assert "It overlaps the photo, so give it a clean, crisp silhouette that reads against a busy photo." in p
        # a página ESPELHA a imagem: o que nasce olhando para a direita acaba olhando para a esquerda, e a luz da esquerda vira da direita
        assert "face toward the upper left" in p, "o rumo vai espelhado para o gerador (a página espelha de volta)"
        assert "key light from the RIGHT" in p and "the page will crop" not in p
        assert "whole object, centered, nothing cropped." in p
        assert "Its role on the page: depth" in p


def test_composicao_erros_dizem_o_que_existe():
    with tempfile.TemporaryDirectory() as d:
        montar_kit(d)
        for args, trecho in ((("capa:z", "trofeu"), "não tem entrada para a página `capa:z` (chaves: ativo:2, cota:Master)"),
                             (("ativo:2", "estrela"), "o elemento `estrela` não está na composição de `ativo:2` (há: trofeu)")):
            try:
                cp.contexto(d, *args)
            except cp.ErroComposicaoPrompt as e:
                assert trecho in str(e), str(e)
            else:
                raise AssertionError(f"aceitou {args}")
        sem = Path(d) / "sem"; sem.mkdir()
        (sem / "mediakit.json").write_text(json.dumps({"elementos": []}))
        try:
            cp.contexto(sem, "ativo:2", "trofeu")
        except cp.ErroComposicaoPrompt as e:
            assert "não tem `composicao`" in str(e)
        else:
            raise AssertionError("kit sem composição passou")
        try:
            cp.contexto(Path(d) / "nao-existe", "ativo:2", "trofeu")
        except cp.ErroComposicaoPrompt as e:
            assert "mediakit.json" in str(e)
        # pela CLI: sai 64, com a mensagem, e pede os três argumentos juntos
        base = [PY, str(AQUI / "elementos_prompt.py"), "prompt", "--tipo", "objeto", "--descricao", "a trophy", "--saida", "/x/t.bruto.png"]
        r = subprocess.run(base + ["--composicao", d, "--pagina", "ativo:2", "--elemento", "estrela"], capture_output=True, text=True)
        assert r.returncode == 64 and "não está na composição" in r.stderr, (r.returncode, r.stderr)
        r = subprocess.run(base + ["--composicao", d, "--pagina", "ativo:2"], capture_output=True, text=True)
        assert r.returncode == 64 and "pede os três" in r.stderr, r.stderr
        r = subprocess.run(base + ["--composicao", d, "--pagina", "ativo:2", "--elemento", "trofeu"], capture_output=True, text=True)
        assert r.returncode == 0 and "Page placement:" in r.stdout, r.stderr


def test_prompt_sem_composicao_continua_igual_ao_de_antes():
    """Kit legado sai igual: 560 prompts (6 tipos + ornamento x 5 aspectos x 4 luzes x com/sem âncora x com/sem estilo) têm o
    mesmo resumo que a versão anterior à composição produzia (calculado no HEAD de 09/10/2026, antes desta mudança). Se você
    mudou o texto de um modelo DE PROPÓSITO, recalcule o resumo: ele existe para que a mudança seja consciente."""
    hashes = []
    for tipo in list(ep.TIPOS) + ["ornamento"]:
        for aspecto in (None, "quadrado", "largo", "alto", "faixa"):
            for luz in (None, "esquerda", "direita", "cima"):
                for ref in (False, True):
                    for estilo, paleta in ((None, None), ("flat two-tone, bold #D4A64A strokes", "#D4A64A,#281805")):
                        p = ep.montar_prompt(tipo, "a running shoe, accent #D4A64A", "/abs/kit/acervo/elementos/x.bruto.png", estilo, paleta,
                                             aspecto, "motivo-x", luz, ref)
                        assert "Page placement" not in p and "Perspective:" not in p
                        hashes.append(hashlib.sha256(p.encode()).hexdigest()[:12])
    assert len(hashes) == 560
    assert hashlib.sha256("".join(hashes).encode()).hexdigest()[:16] == "5f7a7166c14e13dc"


def test_elementos_sh_com_pagina_em_modo_seco_e_a_ficha_guarda_os_fatos():
    with tempfile.TemporaryDirectory() as d:
        kit = Path(d) / "kit"
        montar_kit(kit)
        # --pagina basta: o kit é o da chamada e o elemento é o id que está sendo gerado
        r = sh(kit, "trofeu", "objeto", "a gold trophy", "--pagina", "ativo:2", "--receita", "r1", env_extra={"ELEMENTOS_DRY": "1"})
        assert r.returncode == 0, r.stderr
        assert "Page placement: On the final 1920 x 1080 px page this object appears about 540 x 360 px" in r.stdout
        assert "Landscape 3:2 image" in r.stdout and "the page will crop it on the right side" in r.stdout and "key light from the LEFT" in r.stdout
        assert not (kit / "acervo").exists(), "modo seco não grava nada"
        # só --elemento (sem --pagina), página que não existe, elemento que não existe: 64 com a saída
        for args, trecho in ((["--elemento", "trofeu"], "--pagina"), (["--pagina", "capa:z"], "não tem entrada"),
                             (["--pagina", "ativo:2", "--elemento", "estrela"], "não está na composição")):
            r = sh(kit, "trofeu", "objeto", "a gold trophy", *args, env_extra={"ELEMENTOS_DRY": "1"})
            assert r.returncode == 64 and trecho in r.stderr, (args, r.returncode, r.stderr)
        # a ficha do que nasceu da composição guarda os fatos que o prompt usou
        out = Path(d) / "out"; out.mkdir()
        a = np.zeros((64, 64, 4), np.uint8); a[16:48, 16:48] = (210, 150, 80, 255)
        Image.fromarray(a, "RGBA").save(out / "t.png"); Image.fromarray(a, "RGBA").save(out / "t.bruto.png")
        m = subprocess.run([PY, str(AQUI / "elementos_prompt.py"), "meta", "--id", "trofeu", "--pasta", str(out), "--png", str(out / "t.png"),
                            "--bruto", str(out / "t.bruto.png"), "--tipo", "objeto", "--rota", "codex-alfa", "--composicao", str(kit),
                            "--pagina", "ativo:2", "--elemento", "trofeu"], capture_output=True, text=True)
        assert m.returncode == 0, m.stderr
        meta = json.loads((out / "trofeu.meta.json").read_text())
        assert meta["aspecto"] == "largo", "o aspecto da ficha é o que a composição pediu, não o 'quadrado' de sempre"
        assert meta["composicao"]["area_px"] == [540, 360] and meta["composicao"]["origem_da_medida"] == "plano"
        assert meta["composicao"]["sangra"] == {"borda": "right", "corte": "1/3"} and meta["composicao"]["elemento"] == "trofeu"


def test_cena_prompt_com_a_foto_medida_da_pagina():
    with tempfile.TemporaryDirectory() as d:
        kit = Path(d) / "kit"
        montar_kit(kit)
        base = [PY, str(AQUI / "cena_prompt.py"), str(kit), "ativo"]
        sem = subprocess.run(base, capture_output=True, text=True)
        assert sem.returncode == 0 and "Composition (from the page layout)" not in sem.stdout
        r = subprocess.run(base + ["--composicao", "--pagina", "ativo:2", "--elemento", "trofeu"], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        bloco = r.stdout
        print("   " + bloco[bloco.index("Composition (from the page layout)"):bloco.index("Constraints:")])
        # a caixa REAL da foto (1096 x 1080: quase quadrada), o recorte do 16:9 de origem e as zonas calmas
        assert "the photo fills a 1096 x 1080 px box on the 1920 x 1080 px page (ratio 1.01:1, square), shown cropped to cover." in bloco
        assert "The source frame is 16:9, so the page keeps only the part of the frame from 21% to 79% of its width" in bloco
        assert "The page title will sit over the upper left of the visible photo (about 53% of its width): keep that area calm" in bloco
        assert "An object will overlap the right of the visible photo (about 33% of its width): keep faces and key detail away" in bloco
        assert bloco.index("Composition (from the page layout)") < bloco.index("Constraints:"), "o bloco vem antes das restrições"
        # o resto do prompt é o de sempre: com a composição só entra o bloco
        sem_bloco = bloco.replace(bloco[bloco.index("Composition (from the page layout)"):bloco.index("Constraints:")], "")
        assert sem_bloco.rstrip("\n") == sem.stdout.rstrip("\n"), "com a composição só entra o bloco; o resto do prompt não muda"
        # imagem de origem 3:2: a janela é outra
        r32 = subprocess.run(base + ["--composicao", "--pagina", "ativo:2", "--origem", "3:2"], capture_output=True, text=True)
        assert "The source frame is 3:2, so the page keeps only the part of the frame from 16% to 84% of its width" in r32.stdout
        assert "An object will overlap" not in r32.stdout        # sem --elemento, só o texto cobre a foto
        # sem a foto medida (sem maquete) o prompt sai sem o bloco e avisa; página que não existe é erro 64
        kit2 = Path(d) / "kit2"
        montar_kit(kit2, com_plano=False)
        r2 = subprocess.run([PY, str(AQUI / "cena_prompt.py"), str(kit2), "ativo", "--composicao", "--pagina", "ativo:2"], capture_output=True, text=True)
        assert r2.returncode == 0 and "aviso" in r2.stderr and "render.py --maquete" in r2.stderr and "Composition (from the page layout)" not in r2.stdout
        r3 = subprocess.run(base + ["--composicao", "--pagina", "capa:z"], capture_output=True, text=True)
        assert r3.returncode == 64 and "não tem entrada" in r3.stderr


def test_fatos_da_foto_quando_a_caixa_e_mais_larga_que_a_origem_e_utilitarios():
    c = {"pagina_px": [1920, 1080], "alvos": {}, "foto": {"x": 0, "y": 0, "w": 1920, "h": 600, "img": {"pos": "50% 20%"}}, "caixa": None, "foco": "foto"}
    f = cp.cena(c, 16 / 9)
    assert f["recorte"] == {"eixo": "y", "de": 9, "ate": 64} and f["foco_foto"] and f["texto"] == [], f      # corta em cima e embaixo; f = 0,556 da altura, janela no 20%
    assert cp.cena(dict(c, foto=None)) is None
    assert cp.aspecto_do_gerador(1.5) == "largo" and cp.aspecto_do_gerador(1.0) == "quadrado" and cp.aspecto_do_gerador(2 / 3) == "alto"
    assert cp.aspecto_do_gerador(3.4) == "faixa" and cp.aspecto_do_gerador(0.4) == "alto" and cp.aspecto_do_gerador(1.2) == "quadrado"
    assert cp.rumo(-1284, -260) == "left" and cp.rumo(100, -100) == "upper right" and cp.rumo(0, 300) == "down" and cp.rumo(10, 10) is None
    assert cp.rumo_para_dentro(("left", "upper")) == "lower right" and cp.rumo_para_dentro(("center", "lower")) == "up"
    assert cp.rumo_para_dentro(("center", "middle")) is None
    luz = cp.luz_da_foto(ESTILO_CENA)
    assert luz["direcao"] == "esquerda" and luz["lente"] == ["35mm lens f/4", "eye level"] and "warm golden side light" in luz["luz"]
    assert not any("palette" in x or "shirts" in x for x in luz["luz"]), "palheta e roupa não são luz"
    assert cp.luz_da_foto("sun on the right, golden hour")["direcao"] == "direita"
    assert cp.luz_da_foto("sun on the left, shadows from the right side")["direcao"] is None, "dos dois lados: não afirma"
    assert cp.luz_da_foto("midday overhead light")["direcao"] == "cima" and cp.luz_da_foto("")["direcao"] is None
    assert cp.area_declarada({"largura": "4col"}, "largo")[0] == 4 * 128 + 3 * 24 and cp.area_declarada({"altura": "3cap"}, "alto") is None
    assert cp.area_declarada({"altura": 300}, "faixa") == (900.0, 300.0) and cp.area_declarada(None, "alto") is None


# ---------------------------------------------------------------- faltantes: o aspecto e a área reais da composição
def test_faltantes_pede_o_aspecto_e_a_area_reais_da_composicao():
    import test_plano_elementos as tpe
    sis = tpe.sistema_teste()
    pags, cat = tpe.paginas(tpe.SEQ_TESTE), tpe.catalogo()
    herois = [tpe.heroi("h0", "kit-teste"), tpe.pattern("pat-novo", "kit-teste")]
    trofeu = {"id": "trofeu", "papel": "heroi", "tipo": "objeto", "formato": "png", "aspecto": "alto", "familia": "linha-ouro", "motivo": "a",
              "kit_origem": "kit-teste", "rota": "a-gerar"}
    sangra = {"relacao": "sangra", "borda": "dir", "corte": "1/3", "y": "cy=foto.cy"}
    comp = {"ativo:diagonal": {"foco": "foto", "elementos": [{"id": "trofeu", "papel": "heroi", "funcao": "profundidade", "ancora": sangra,
                                                              "escala": {"altura": "1/3p"}}]},
            "cota": {"elementos": [{"id": "trofeu", "papel": "heroi", "funcao": "foco", "ancora": sangra, "escala": {"altura": "1/2p"}}]}}
    sem = pe.faltantes(sis, herois, "r1", pags, cat)
    com = pe.faltantes(sis, herois + [trofeu], "r1", pags, cat, composicao=comp)
    reais = sorted((h["n"], h["pagina"], h["aspecto"], tuple(h["px"])) for h in com["composicao"])
    print("   herói que a composição declara e falta gerar:", reais)
    # página 7 (ativo:diagonal, 1/3 da altura, aspecto alto): 240 x 360; páginas 10 e 11 (cota, 1/2 da altura): 360 x 540. Nada de 'quadrado'
    assert reais == [(7, "ativo:diagonal", "alto", (240, 360)), (10, "cota", "alto", (360, 540)), (11, "cota", "alto", (360, 540))], reais
    assert any("herói `trofeu` da página ativo:diagonal: aspecto alto, 240 x 360 px na página (altura 1/3p)" in x for x in com["pedidos"]), com["pedidos"]
    # a página que a composição serve conta como coberta: o plano pede menos heróis genéricos
    assert com["total_herois"] < sem["total_herois"], (com["total_herois"], sem["total_herois"])
    # kit legado sai igual: sem composição (ou composição vazia) o resultado é o de sempre, com a lista nova vazia
    for vazio in (None, {}):
        igual = pe.faltantes(sis, herois, "r1", pags, cat, composicao=vazio)
        assert igual == sem and igual["composicao"] == []
    # herói que já existe como imagem não é pedido de novo, mas a página conta como coberta
    pronto = dict(trofeu, arquivo="acervo/elementos/trofeu.png", rota="codex-alfa")
    f_pronto = pe.faltantes(sis, herois + [pronto], "r1", pags, cat, composicao=comp)
    assert f_pronto["composicao"] == [] and f_pronto["cobertas"] > sem["cobertas"], (f_pronto["cobertas"], sem["cobertas"])
    # sem aspecto declarado no elementos[]: não inventa 'quadrado', diz o que declarar
    sem_aspecto = {k: v for k, v in trofeu.items() if k != "aspecto"}
    f2 = pe.faltantes(sis, herois + [sem_aspecto], "r1", pags, cat, composicao=comp)
    assert all(h["px"] is None and h["aspecto"] is None for h in f2["composicao"])
    assert any("declare `aspecto` no elementos[]" in x for x in f2["pedidos"]), f2["pedidos"]
    # escala em colunas num aspecto largo: 4 colunas = 584 px de largura, 389 de altura
    comp3 = {"ativo:diagonal": {"elementos": [{"id": "bola", "papel": "heroi", "funcao": "foco", "ancora": sangra, "escala": {"largura": "4col"}}]}}
    bola = {"id": "bola", "papel": "heroi", "tipo": "objeto", "formato": "png", "aspecto": "largo", "familia": "linha-ouro", "motivo": "b",
            "kit_origem": "kit-teste", "rota": "a-gerar"}
    f3 = pe.faltantes(sis, herois + [bola], "r1", pags, cat, composicao=comp3)
    assert [(h["aspecto"], tuple(h["px"])) for h in f3["composicao"]] == [("largo", (584, 389))], f3["composicao"]
    # papel que não é herói e grafismo da própria composição não entram
    comp4 = {"ativo:diagonal": {"elementos": [{"id": "x", "papel": "estrutura", "funcao": "conexao", "ancora": sangra, "escala": {"altura": "1/3p"}},
                                              {"id": "y", "papel": "heroi", "funcao": "foco", "grafismo": {"tipo": "faixa-diagonal"}, "ancora": sangra,
                                               "escala": {"altura": "1/3p"}}]}}
    assert pe.faltantes(sis, herois, "r1", pags, cat, composicao=comp4)["composicao"] == []


def test_plano_da_maquete_vale_e_o_mais_novo_vence():
    """Costura A×B (integração de 09/10): a maquete grava saida/plano-maquete-<r>.json e o prompt só lia
    plano-elementos-<r>.json; o asset gerado depois da maquete saía sem o bloco Composition."""
    import time
    with tempfile.TemporaryDirectory() as d:
        kit = Path(d) / "kit"
        montar_kit(kit)
        saida = kit / "saida"
        render = saida / "plano-elementos-r1.json"
        maquete = saida / "plano-maquete-r1.json"
        dados = json.loads(render.read_text(encoding="utf-8"))
        maquete.write_text(json.dumps(dados), encoding="utf-8")
        render.unlink()
        achados = cp._planos(kit, "r1")
        assert [f.name for f, _ in achados] == ["plano-maquete-r1.json"], achados
        r = subprocess.run([PY, str(AQUI / "cena_prompt.py"), str(kit), "ativo", "--composicao", "--pagina", "ativo:2"],
                           capture_output=True, text=True)
        assert r.returncode == 0 and "Composition (from the page layout)" in r.stdout, r.stderr
        # com os dois, vence o mais novo
        render.write_text(json.dumps(dados), encoding="utf-8")
        time.sleep(0.05); os.utime(maquete, None)
        assert [f.name for f, _ in cp._planos(kit, "r1")] == ["plano-maquete-r1.json"]
        time.sleep(0.05); os.utime(render, None)
        assert [f.name for f, _ in cp._planos(kit, "r1")] == ["plano-elementos-r1.json"]
        assert [f.name for f, _ in cp._planos(kit, "r1", vertical=True)] == []


def test_cena_de_futebol_sem_corrida_de_rua():
    """Achado do teste da AME (09/10): kit de futebol caía no modelo de corrida de rua (pórtico, corredores, camisa de
    corrida, adultos). Com modalidade_sistema futebol, a cena, a roupa e o público são do futebol infantil."""
    with tempfile.TemporaryDirectory() as d:
        kit = Path(d) / "kit"
        montar_kit(kit)
        k = json.loads((kit / "mediakit.json").read_text(encoding="utf-8"))
        k["evento"]["modalidade_sistema"] = "futebol"
        (kit / "mediakit.json").write_text(json.dumps(k), encoding="utf-8")
        capa = subprocess.run([PY, str(AQUI / "cena_prompt.py"), str(kit), "capa"], capture_output=True, text=True).stdout
        assert "football pitch" in capa and "football kit" in capa and "children and their families" in capa, capa
        assert "race shirt" not in capa and "running race" not in capa and "adults" not in capa, capa
        noite = subprocess.run([PY, str(AQUI / "cena_prompt.py"), str(kit), "ativo", "--ativo", "Noite das Estrelas"],
                               capture_output=True, text=True).stdout
        assert "awards night" in noite and "start and finish arch" not in noite, noite
        corrida = subprocess.run([PY, str(AQUI / "cena_prompt.py"), str(montar_kit(Path(d) / "k2") or Path(d) / "k2"), "capa"],
                                 capture_output=True, text=True).stdout
        assert "plain race shirt" in corrida and "adults" in corrida, "corrida de rua continua igual"


def test_cota_e_contato_do_futebol_painel_de_texto_e_cena_da_direcao_de_arte():
    """Achados do teste da AME (09/10): no futebol, cota e contato saíam como corrida ("the race course of futebol", camisa e
    número de corrida, borrão de corredores ao fundo); local vazio virava ", São José"; o painel de texto da cota (foto
    inteira) e o troféu de pé não entravam como áreas calmas. E a cena de cada cota é decisão da direção de arte (--cena),
    com o resto do prompt vindo do sistema."""
    with tempfile.TemporaryDirectory() as d:
        kit = Path(d) / "kit"
        montar_kit(kit)
        k = json.loads((kit / "mediakit.json").read_text(encoding="utf-8"))
        k["evento"]["modalidade_sistema"] = "futebol"; k["evento"]["local"] = ""
        (kit / "mediakit.json").write_text(json.dumps(k), encoding="utf-8")
        run = lambda *a: subprocess.run([PY, str(AQUI / "cena_prompt.py"), str(kit), *a], capture_output=True, text=True)
        for arq in ("cota", "contato", "capa"):
            r = run(arq)
            assert r.returncode == 0, r.stderr
            for corrida in ("race course", "race shirt", "race bib", "runners", "Location: ,"):
                assert corrida not in r.stdout, (arq, corrida, r.stdout)
            assert "background players" in r.stdout and "football" in r.stdout, (arq, r.stdout)
        cena = "the youth teams lining up on the pitch before the final, families clapping behind the fence"
        r = run("cota", "--cena", cena)
        assert "Scene: the youth teams lining up on the pitch before the final" in r.stdout and "touchline of a youth" not in r.stdout
        for sistema in ("Camera: 35mm lens", "Light: ", "Location: ", "Constraints: ", "No text"):
            assert sistema in r.stdout, sistema
    # o painel de texto e o escudo sobre a foto inteira; o troféu pequeno também pede área calma
    alvos = {"titulo": {"x": 96, "y": 180, "w": 190, "h": 60}, "preco": {"x": 380, "y": 130, "w": 150, "h": 40},
             "corpo": {"x": 96, "y": 300, "w": 700, "h": 64}, "direitos": {"x": 250, "y": 410, "w": 660, "h": 560},
             "micro": {"x": 96, "y": 260, "w": 260, "h": 20}, "logo": {"x": 1700, "y": 960, "w": 120, "h": 80}}
    c = {"pagina_px": [1920, 1080], "alvos": alvos, "foto": {"x": 0, "y": 0, "w": 1920, "h": 1080, "img": {"pos": "50% 50%"}},
         "caixa": [958, 690, 1198, 960], "foco": "preco"}          # 240 x 270: 3% da foto, abaixo dos 4% do texto
    f = cp.cena(c, 16 / 9)
    zonas = {z["alvo"]: z for z in f["texto"]}
    assert "texto" in zonas and zonas["texto"]["regiao"] == "left" and zonas["texto"]["largura_pct"] == 42, f["texto"]          # de x 96 (corpo) a 910 (direitos): 814 px
    assert "titulo" not in zonas and "logo" not in zonas, "título, preço e escudo pequenos não viram zona (menos de 4%)"
    assert f["elemento"] and f["elemento"]["largura_pct"] == 12, f["elemento"]


# ================================================================= material (render de produto com material e luz declarados)
# Prompts gravados no HEAD de 12/10/2026 (5cfaa7a), ANTES do `material` existir: sem material, o prompt tem de sair igual a
# eles, caractere por caractere. Se você mudou um modelo DE PROPÓSITO, regrave os dois: a mudança tem de ser consciente.
PROMPT_REF_PADRAO = (
    'Generate one image with one call of the image generator and save it exactly as /abs/kit/acervo/elementos/medalha.bruto.png (PNG).\n'
    'Use case: product-mockup\n'
    'Asset type: isolated object cut-out for a sports sponsorship media kit page (transparent PNG placed over layouts)\n'
    'Primary request: one single object: a gold medal\n'
    'Subject: a gold medal\n'
    'Style/medium: Photorealistic product photograph of the object alone, crisp focus, true colors.\n'
    'Composition/framing: Square 1:1 image, 1024x1024 pixels or larger. One single isolated object, centered, the whole object inside the frame with a generous empty margin on every side, nothing cropped.\n'
    'Lighting/mood: key light from the LEFT, gentle fill from the opposite side.\n'
    'Background: fully transparent (PNG with a real alpha channel). If the generator cannot produce transparency, use this instead: a perfectly flat, uniform mid grey background (50% grey), no gradient, no vignette.\n'
    'Constraints: one object only; no people, no hands, no body parts, no floor, no table, no props, no scenery; no cast shadow on the background.\n'
    'Avoid: text of any kind, letters, numbers, digits, logos, brand marks, signatures, watermarks.\n'
    'The image must contain NO text of any kind: no letters, no numbers, no digits, no logos, no brand marks, no signatures, no watermarks, no engraved or printed characters.\n'
    'Do NOT post-process the image with code or any other tool: no background removal, no resizing, no recoloring, no cropping. Save exactly the file the image generator returned (we measure its transparency afterwards).\n'
    'Do NOT regenerate under any circumstance, not even if a check below fails (each generation spends the ChatGPT quota). Make exactly one image generation call and keep that single image.\n'
    'After saving, open the image and check: (1) no text, letter, number, digit or logo anywhere, including on the subject itself, (2) one object only, nothing cropped by the frame, (3) background is transparent or perfectly flat mid grey, (4) light comes from the left.\n'
    'In your final message, write one line exactly as TRANSPARENT: yes or TRANSPARENT: no (as returned by the generator), then list any defect found.'
)
PROMPT_REF_COMPLETO = (
    'Generate one image with one call of the image generator and save it exactly as /abs/kit/acervo/elementos/bola.bruto.png (PNG).\n'
    'Use case: product-mockup\n'
    'Asset type: isolated object cut-out for a sports sponsorship media kit page (transparent PNG placed over layouts)\n'
    'Primary request: one single object: a worn leather football, accent antique gold\n'
    'Input images: Image 1 (attached) is a STYLE REFERENCE only. Generate a new image and match the rendering style of the attached reference, not its subject: same medium, material finish, light direction and softness, level of detail, color treatment, camera angle and edge quality. Do not copy, trace, edit or include the reference object; draw only the subject described here, as a new and different object.\n'
    'Subject: a worn leather football, accent antique gold\n'
    'Theme: bola de couro (a visual theme, never written)\n'
    'Style/medium: photoreal product photo, warm side light\n'
    'Composition/framing: Landscape 3:2 image, 1536x1024 pixels or larger. One single isolated object, centered, the whole object inside the frame with a generous empty margin on every side, nothing cropped.\n'
    'Lighting/mood: key light from the RIGHT, gentle fill from the opposite side.\n'
    'Color palette: antique gold as the dominant color, with near-black brown; no other hues except the natural highlights and shadows of the materials.\n'
    'Background: fully transparent (PNG with a real alpha channel). If the generator cannot produce transparency, use this instead: a perfectly flat, uniform mid grey background (50% grey), no gradient, no vignette.\n'
    'Constraints: one object only; no people, no hands, no body parts, no floor, no table, no props, no scenery.\n'
    'Avoid: text of any kind, letters, numbers, digits, logos, brand marks, signatures, watermarks.\n'
    'The image must contain NO text of any kind: no letters, no numbers, no digits, no logos, no brand marks, no signatures, no watermarks, no engraved or printed characters.\n'
    'Do NOT post-process the image with code or any other tool: no background removal, no resizing, no recoloring, no cropping. Save exactly the file the image generator returned (we measure its transparency afterwards).\n'
    'Do NOT regenerate under any circumstance, not even if a check below fails (each generation spends the ChatGPT quota). Make exactly one image generation call and keep that single image.\n'
    'Do not edit, copy or overwrite the attached reference image file.\n'
    'After saving, open the image and check: (1) no text, letter, number, digit or logo anywhere, including on the subject itself, (2) one object only, nothing cropped by the frame, (3) background is transparent or perfectly flat mid grey, (4) light comes from the right, (5) the rendering style matches the attached reference while the subject is the new one.\n'
    'In your final message, write one line exactly as TRANSPARENT: yes or TRANSPARENT: no (as returned by the generator), then list any defect found.'
)
LINHA_METAL_DIR = ("Material/render: studio product render, physically based brushed metal, key light from the RIGHT at 35 degrees, "
                   "soft fill, thin rim light, transparent background.")


def _completo(**kw):
    return ep.montar_prompt("objeto", "a worn leather football, accent #D4A64A", "/abs/kit/acervo/elementos/bola.bruto.png",
                            estilo="photoreal product photo, warm side light", paleta="#D4A64A,#281805", aspecto="largo",
                            motivo="bola-de-couro", luz="direita", ref=True, **kw)


def test_sem_material_o_prompt_e_identico_ao_de_antes():
    padrao = ep.montar_prompt("objeto", "a gold medal", "/abs/kit/acervo/elementos/medalha.bruto.png")
    assert padrao == PROMPT_REF_PADRAO, "o prompt sem material mudou"
    assert _completo() == PROMPT_REF_COMPLETO and _completo(material=None) == PROMPT_REF_COMPLETO, "o prompt sem material mudou"
    assert "Material/render" not in padrao and "physically based" not in PROMPT_REF_COMPLETO
    print("   sem material: os 2 prompts de referência do HEAD saem iguais, caractere por caractere")


def test_material_acrescenta_uma_linha_com_a_luz_do_prompt():
    p = _completo(material="metal-escovado")
    # exatamente uma linha a mais, logo depois da luz, e o resto na mesma ordem
    novas, antigas = p.split("\n"), PROMPT_REF_COMPLETO.split("\n")
    assert len(novas) == len(antigas) + 1, (len(novas), len(antigas))
    assert LINHA_METAL_DIR in novas, [l for l in novas if l.startswith("Material")]
    i = novas.index(LINHA_METAL_DIR)
    assert novas[i - 1].startswith("Lighting/mood: key light from the RIGHT") and novas[:i] + novas[i + 1:] == antigas
    # a luz vem do que o prompt já tem: a esquerda da v1 no objeto sem estilo; a da foto da página com composição
    q = ep.montar_prompt("objeto", "a gold medal", "/x/m.bruto.png", material="ouro")
    assert "physically based polished gold, key light from the LEFT at 35 degrees" in q and "key light from the LEFT, gentle fill" in q
    with tempfile.TemporaryDirectory() as d:
        montar_kit(d)
        c = cp.contexto(d, "ativo:2", "trofeu")
        c["espelhar"] = True                                   # página espelhada: a luz da foto (esquerda) vira direita
        r = ep.montar_prompt("objeto", "a gold trophy", "/x/t.bruto.png", composicao=c, material="ouro")
        assert "physically based polished gold, key light from the RIGHT at 35 degrees" in r and "key light from the RIGHT, gentle fill" in r
    # objeto com estilo e sem luz nenhuma: o material leva a esquerda (a mesma do tratar.py sombra), e a linha da luz junto
    s = ep.montar_prompt("objeto", "a rubber ball", "/x/b.bruto.png", estilo="photoreal product photo", material="borracha")
    assert "physically based rubber, key light from the LEFT at 35 degrees" in s and "Lighting/mood: key light from the LEFT" in s
    assert "Lighting/mood" not in ep.montar_prompt("objeto", "a rubber ball", "/x/b.bruto.png", estilo="photoreal product photo")
    print("   +1 linha:", LINHA_METAL_DIR)


def test_os_10_materiais_viram_ingles_e_fora_do_vocabulario_e_recusado():
    assert set(ep.MATERIAIS) == {"metal-escovado", "ouro", "couro", "borracha", "tecido", "vidro-fosco", "plastico-fosco", "madeira",
                                 "papel", "grama"}
    for mat, ingles in ep.MATERIAIS.items():
        p = ep.montar_prompt("objeto", "a trophy", "/x/t.bruto.png", luz="cima", material=mat)
        linha = [l for l in p.split("\n") if l.startswith("Material/render:")]
        assert linha == [f"Material/render: studio product render, physically based {ingles}, key light from the TOP at 35 degrees, "
                         "soft fill, thin rim light, transparent background."], (mat, linha)
        assert mat not in linha[0] or mat == ingles, (mat, linha)          # o nome em português não vai para o prompt
    for tipo, mat in (("objeto", "aco"), ("objeto", "Ouro"), ("pattern", "ouro"), ("textura", "papel"), ("ilustracao", "couro")):
        try:
            ep.montar_prompt(tipo, "x", "/x.png", material=mat)
        except ValueError as e:
            assert "material" in str(e), e
            continue
        raise AssertionError(f"aceitou material {mat} em {tipo}")


def test_elementos_sh_leva_o_material_ao_prompt_e_a_ficha():
    with tempfile.TemporaryDirectory() as d:
        desc = Path(d) / "bola.txt"
        desc.write_text("a worn leather football\n", encoding="utf-8")
        r = sh(Path(d) / "kit", "bola", "objeto", "--descricao-de", desc, "--material", "couro", "--luz", "direita",
               env_extra={"ELEMENTOS_DRY": "1"})
        assert r.returncode == 0, r.stderr
        assert "material=couro" in r.stdout and "physically based leather, key light from the RIGHT at 35 degrees" in r.stdout, r.stdout[-600:]
        r = sh(Path(d) / "kit", "bola", "objeto", "--descricao-de", desc, "--material", "aco", env_extra={"ELEMENTOS_DRY": "1"})
        assert r.returncode == 64 and "material `aco` fora do vocabulário" in r.stderr, (r.returncode, r.stderr)
        r = sh(Path(d) / "kit", "p", "pattern", "--descricao-de", desc, "--material", "couro", env_extra={"ELEMENTOS_DRY": "1"})
        assert r.returncode == 64 and "material só vale para objeto" in r.stderr, (r.returncode, r.stderr)
        # a ficha guarda o material (e None quando não há)
        a = np.zeros((32, 32, 4), np.uint8); a[8:24, 8:24] = (120, 80, 40, 255)
        Image.fromarray(a, "RGBA").save(Path(d) / "o.png")
        base = [PY, str(AQUI / "elementos_prompt.py"), "meta", "--id", "o", "--pasta", d, "--png", str(Path(d) / "o.png"), "--tipo", "objeto",
                "--rota", "codex-alfa"]
        assert subprocess.run(base + ["--material", "couro"], capture_output=True, text=True).returncode == 0
        assert json.loads((Path(d) / "o.meta.json").read_text()).get("material", "ausente") == "couro"
        assert subprocess.run(base, capture_output=True, text=True).returncode == 0
        assert json.loads((Path(d) / "o.meta.json").read_text()).get("material", "ausente") is None


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

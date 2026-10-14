#!/usr/bin/env python3
# Copiado da v9 (commit 6003ce2) em 14/10/2026.
"""Provas do recortar.py: modelo ausente sai com 2 e nada é baixado, classe pessoa-livre, atleta que cai para o isnet,
--da-cena e o aviso de IoU do --comparar. Rodar: ~/.venvs/mediakit/bin/python test_recortar.py (ou pytest).

Duas formas de rodar o rembg:
  - FALSO (quase todas): um pacote `rembg` numa pasta temporária, na frente do PYTHONPATH, com new_session e remove que
    seguem uma regra conhecida: o recorte é tudo o que difere do fundo liso, e o modelo de pessoa (u2net_human_seg) come o
    que é verde (a garrafa na mão, como o de verdade comeu em 08/10/2026) e ainda perde a coluna mais à esquerda da pessoa
    (o fio de 1 px pela silhueta em que os modelos de verdade discordam). Assim o IoU esperado é conta, não sorte. A pasta
    de modelos (U2NET_HOME e REMBG_HOME) também é temporária, com .onnx de mentira: só existe o modelo que a prova põe lá.
  - REAL (só com --real ou MEDIAKIT_RECORTE_REAL=1): o rembg e os modelos de ~/.rembg/models numa figura sintética de 256 px.
    Fica fora da rodada padrão porque passa de 20 s com a máquina ocupada (12,6 s e 25,3 s medidos em 12/10/2026).
Nenhuma prova baixa modelo: a da tranca do download ainda aponta a rede para um proxy morto, para que uma falha da tranca
vire erro em vez de puxar 170 MB.

Prova manual com gente de verdade (12/10/2026, rembg real, os dois modelos instalados): os recortes reais da Copa AME v2
(acervo/real-goleiro-recorte.png e real-atleta-recorte.png) compostos sobre fundo liso cinza e passados por
`recortar.py <cena> <saida> --classe pessoa-livre --da-cena --comparar isnet`:
  - goleiro de luvas, mãos sem objeto, 1000 x 900 px: IoU .983, sem aviso (26 s);
  - menino conduzindo a bola, 840 x 900 px: IoU .893, AVISO (28 s). O mapa das duas máscaras mostrou o que o
    u2net_human_seg deixou de fora: a bola inteira (8.717 px só no isnet, 880 px só no u2net). A caixa da diferença saía
    com 333 x 707 px (os fios da silhueta somados); com a maior peça depois da abertura 3x3 ela aponta a bola.
Para repetir: componha um recorte com objeto sobre fundo liso e rode o comando acima; confira o aviso e a caixa."""
import json, os, subprocess, sys, tempfile, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

AQUI = Path(__file__).parent
PY = sys.executable
FUNDO = (205, 205, 200)
GARRAFA = [135, 60, 161, 111]                     # caixa x0 y0 x1 y1 da garrafa verde na mão direita
FALSO = '''
import json, os
import numpy as np
from PIL import Image

REG = os.environ["FAKE_REMBG_REG"]


def _log(**kw):
    with open(REG, "a") as f:
        f.write(json.dumps(kw) + "\\n")


class _Sessao:
    def __init__(self, nome):
        self.nome = nome


def new_session(nome="u2net", *a, **k):
    _log(ev="sessao", modelo=nome)
    return _Sessao(nome)


def remove(im, session=None, post_process_mask=False, **k):
    arr = np.asarray(im.convert("RGB")).astype(int)
    mascara = np.abs(arr - arr[0, 0]).sum(-1) > 30                   # tudo o que não é o fundo liso
    if session.nome == "u2net_human_seg":                              # o modelo de pessoa come o que ela segura
        mascara &= ~((arr[..., 1] > 150) & (arr[..., 0] < 90) & (arr[..., 2] < 90))
        mascara[:, np.nonzero(mascara.any(axis=0))[0].min()] = False   # e perde um fio de 1 px na borda da silhueta
    _log(ev="remove", modelo=session.nome)
    return Image.fromarray(np.dstack([arr.astype(np.uint8), (mascara * 255).astype(np.uint8)]), "RGBA")
'''


def figura(caminho, garrafa=True, fragmento=False, tam=200):
    """Pessoa de frente sobre fundo liso; com `garrafa`, uma garrafa verde encostada na mão direita; com `fragmento`, um
    pedaço solto no canto (a outra pessoa cortada pela borda da cena)."""
    im = Image.new("RGB", (tam, tam), FUNDO)
    d = ImageDraw.Draw(im)
    d.ellipse((85, 10, 115, 40), fill=(150, 100, 80))
    d.rectangle((80, 42, 120, 112), fill=(30, 60, 140))
    d.rectangle((66, 45, 78, 100), fill=(150, 100, 80)); d.rectangle((122, 45, 134, 100), fill=(150, 100, 80))
    d.rectangle((84, 112, 98, 170), fill=(40, 40, 40)); d.rectangle((102, 112, 116, 170), fill=(40, 40, 40))
    if garrafa:
        d.rectangle((GARRAFA[0], GARRAFA[1], GARRAFA[2] - 1, GARRAFA[3] - 1), fill=(20, 190, 40))
    if fragmento:
        d.rectangle((2, 180, 7, 185), fill=(120, 30, 30))
    im.save(caminho)
    return im


class Ambiente:
    """Pasta temporária com a pasta de modelos isolada (só os `modelos` dados existem) e, com `falso`, o rembg falso."""

    def __init__(self, modelos=("isnet-general-use", "u2net_human_seg"), falso=True):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.home = self.d / "modelos"
        self.home.mkdir()
        for m in modelos:
            (self.home / "models" / m).mkdir(parents=True)
            (self.home / "models" / m / f"{m}.onnx").write_bytes(b"onnx de mentira")
        self.reg = self.d / "chamadas.jsonl"
        env = {k: v for k, v in os.environ.items() if k not in ("U2NET_HOME", "REMBG_HOME", "XDG_DATA_HOME", "PYTHONPATH")}
        env.update(U2NET_HOME=str(self.home), REMBG_HOME=str(self.home), FAKE_REMBG_REG=str(self.reg))
        if falso:
            pacote = self.d / "falso" / "rembg"
            pacote.mkdir(parents=True)
            (pacote / "__init__.py").write_text(FALSO)
            env["PYTHONPATH"] = str(self.d / "falso")
        self.env = env

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.tmp.cleanup()

    def rodar(self, *args):
        return subprocess.run([PY, str(AQUI / "recortar.py"), *map(str, args)], capture_output=True, text=True, env=self.env, timeout=300)

    def sessoes(self):
        return [json.loads(l)["modelo"] for l in self.reg.read_text().splitlines() if '"sessao"' in l] if self.reg.exists() else []

    def arquivos_na_pasta_de_modelos(self):
        return sorted(str(p.relative_to(self.home)) for p in self.home.rglob("*") if p.is_file())


# --------------------------------------------------------------------------------------------- nunca baixa modelo
def test_modelo_ausente_sai_com_2_e_nada_e_baixado():
    with Ambiente(modelos=(), falso=False) as amb:                     # o rembg de verdade, pasta de modelos vazia
        e = amb.d / "e.png"
        figura(e)
        for args in (["--classe", "pessoa-livre"], ["--classe", "produto"], ["--classe", "produto", "--modelo", "birefnet-portrait"],
                     ["--classe", "atleta"]):
            s = amb.d / "s.png"
            r = amb.rodar(e, s, *args)
            assert r.returncode == 2, (args, r.returncode, r.stderr[-400:])
            assert "nunca baixa" in r.stderr and "não está instalado" in r.stderr and "Instalados: nenhum" in r.stderr, (args, r.stderr)
            assert not s.exists() and amb.arquivos_na_pasta_de_modelos() == [], (args, amb.arquivos_na_pasta_de_modelos())
        # atleta sem o birefnet avisou que cai para o isnet, e parou porque o isnet também falta
        assert "cai para isnet-general-use" in r.stderr and "modelo isnet-general-use não está instalado" in r.stderr, r.stderr
    with Ambiente(modelos=("u2net_human_seg",)) as amb:                # o modelo de comparação também é conferido
        e = amb.d / "e.png"
        figura(e)
        r = amb.rodar(e, amb.d / "s.png", "--classe", "pessoa-livre", "--comparar", "isnet")
        assert r.returncode == 2 and "isnet-general-use não está instalado" in r.stderr and "Instalados: u2net_human_seg" in r.stderr, r.stderr
        assert amb.sessoes() == [], "parou antes de abrir qualquer modelo"
    print("   pasta de modelos vazia: código 2 nas 4 classes, nenhum arquivo baixado")


def test_avisa_nome_e_tamanho_antes_de_qualquer_download():
    """Modelo fora de ~/.u2net (pasta de modelos vazia): o aviso em português diz qual é e quanto pesa, e nada é baixado."""
    with Ambiente(modelos=(), falso=False) as amb:
        e = amb.d / "e.png"
        figura(e)
        for classe, nome, tamanho in (("pessoa-livre", "u2net_human_seg", "170 MB"), ("produto", "isnet-general-use", "170 MB")):
            r = amb.rodar(e, amb.d / "s.png", "--classe", classe)
            assert r.returncode == 2
            assert f"aviso: o modelo {nome} ainda não está em" in r.stderr and f"pesa cerca de {tamanho}" in r.stderr, r.stderr
            assert amb.arquivos_na_pasta_de_modelos() == []
        r = amb.rodar(e, amb.d / "s.png", "--classe", "produto", "--modelo", "birefnet-portrait")
        assert "birefnet-portrait" in r.stderr and "cerca de 1 GB" in r.stderr, r.stderr


def test_a_tranca_do_download_segura_o_que_a_conferencia_nao_previu():
    """A conferência é enganada de propósito (diz que o modelo existe) com o rembg de verdade e a pasta vazia: o rembg vai
    baixar, e a tranca tem de parar com 2. A rede aponta para um proxy morto: se a tranca falhar, a prova falha sem baixar."""
    with Ambiente(modelos=(), falso=False) as amb:
        e = amb.d / "e.png"
        figura(e)
        codigo = ("import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); import recortar; "
                  "recortar.arquivo_do_modelo = lambda nome: Path(sys.argv[2]); "
                  "sys.argv = ['recortar.py', sys.argv[2], sys.argv[3], '--classe', 'pessoa-livre']; recortar.main()")
        env = dict(amb.env, HTTPS_PROXY="http://127.0.0.1:9", HTTP_PROXY="http://127.0.0.1:9", ALL_PROXY="http://127.0.0.1:9")
        r = subprocess.run([PY, "-c", codigo, str(AQUI), str(e), str(amb.d / "s.png")], capture_output=True, text=True, env=env, timeout=120)
        assert r.returncode == 2 and "tentou BAIXAR" in r.stderr and "u2net_human_seg.onnx" in r.stderr, (r.returncode, r.stderr[-500:])
        assert amb.arquivos_na_pasta_de_modelos() == [] and not (amb.d / "s.png").exists()


# --------------------------------------------------------------------------------------------- classes
def test_pessoa_livre_usa_o_modelo_de_pessoa():
    with Ambiente() as amb:
        e, s = amb.d / "e.png", amb.d / "s.png"
        figura(e, garrafa=False)
        r = amb.rodar(e, s, "--classe", "pessoa-livre")
        assert r.returncode == 0 and "modelo: u2net_human_seg" in r.stdout, r.stderr[-300:]
        assert amb.sessoes() == ["u2net_human_seg"], amb.sessoes()
        out = Image.open(s)
        assert out.mode == "RGBA" and out.size == (200, 200)
        a = np.asarray(out)[..., 3]
        assert a[70, 100] == 255 and a[5, 5] == 0, (a[70, 100], a[5, 5])          # tronco opaco, fundo vazio
        assert not s.with_suffix(".meta.json").exists(), "sem --comparar não há ficha nova"


def test_atleta_sem_birefnet_cai_para_o_isnet_com_aviso():
    with Ambiente() as amb:                                            # instalados: isnet e u2net_human_seg
        e, s = amb.d / "e.png", amb.d / "s.png"
        figura(e)
        r = amb.rodar(e, s, "--classe", "atleta")
        assert r.returncode == 0 and amb.sessoes() == ["isnet-general-use"], (r.returncode, amb.sessoes(), r.stderr[-300:])
        assert "aviso: birefnet-portrait não está instalado" in r.stderr and "cai para isnet-general-use" in r.stderr, r.stderr
        assert np.asarray(Image.open(s))[85, 148, 3] == 255, "o isnet fica com a garrafa na mão"
    with Ambiente(modelos=("isnet-general-use", "u2net_human_seg", "birefnet-portrait")) as amb:
        e, s = amb.d / "e.png", amb.d / "s.png"
        figura(e)
        r = amb.rodar(e, s, "--classe", "atleta")
        assert r.returncode == 0 and amb.sessoes() == ["birefnet-portrait"] and "aviso" not in r.stderr, (amb.sessoes(), r.stderr)


# --------------------------------------------------------------------------------------------- --comparar e --da-cena
def iou_esperado(e):
    """A mesma regra do rembg falso: pessoa = tudo menos o verde e menos a primeira coluna com tinta (o fio da borda)."""
    arr = np.asarray(Image.open(e).convert("RGB")).astype(int)
    tudo = np.abs(arr - np.array(FUNDO)).sum(-1) > 30
    pessoa = tudo & ~((arr[..., 1] > 150) & (arr[..., 0] < 90) & (arr[..., 2] < 90))
    pessoa[:, np.nonzero(pessoa.any(axis=0))[0].min()] = False
    return round(int(pessoa.sum()) / int(tudo.sum()), 4)


def test_comparar_avisa_abaixo_de_90_e_grava_na_ficha():
    with Ambiente() as amb:
        e, s = amb.d / "cena.png", amb.d / "pessoa.png"
        figura(e)
        (amb.d / "pessoa.meta.json").write_text(json.dumps({"id": "pessoa", "rota": "cena"}))     # ficha que já existia
        r = amb.rodar(e, s, "--classe", "pessoa-livre", "--da-cena", "--comparar", "isnet")
        assert r.returncode == 0, r.stderr[-400:]
        assert amb.sessoes() == ["u2net_human_seg", "isnet-general-use"], amb.sessoes()
        esperado = iou_esperado(e)
        assert esperado < 0.90, esperado
        ficha = json.loads((amb.d / "pessoa.meta.json").read_text())
        assert ficha["id"] == "pessoa" and ficha["rota"] == "cena", "a ficha que já existia foi apagada"
        c = ficha["recorte"]["comparar"]
        assert c["modelo"] == "isnet-general-use" and c["iou"] == esperado and c["aviso"] is True and c["limite"] == 0.9, c
        # o que o modelo de pessoa comeu: a garrafa (26 x 51) e o fio de 56 px no braço esquerdo (x 66, y 45 a 100). A caixa é
        # a da garrafa, a maior peça; a caixa de todos os px iria de x 66 a 161 e não diria onde olhar
        assert c["px_so_no_outro"] == 26 * 51 + 56 and c["px_maior_peca"] == 26 * 51 and c["caixa_so_no_outro"] == GARRAFA, c
        assert ficha["recorte"]["modelo"] == "u2net_human_seg" and ficha["recorte"]["da_cena"] is True
        assert f"IOU u2net_human_seg x isnet-general-use: {esperado:.3f}" in r.stdout, r.stdout
        assert "AVISO: IoU" in r.stderr and "pode ter sido comido" in r.stderr and str(GARRAFA) in r.stderr, r.stderr
    with Ambiente() as amb:                                            # mãos vazias: os dois concordam, sem aviso
        e, s = amb.d / "cena.png", amb.d / "pessoa.png"
        figura(e, garrafa=False)
        r = amb.rodar(e, s, "--classe", "pessoa-livre", "--da-cena", "--comparar", "isnet")
        c = json.loads((amb.d / "pessoa.meta.json").read_text())["recorte"]["comparar"]
        assert r.returncode == 0 and c["iou"] == iou_esperado(e) > 0.98 and c["aviso"] is False and "AVISO" not in r.stderr, (c, r.stderr)
        assert c["caixa_so_no_outro"] is None and c["px_maior_peca"] == 0, "o fio de 1 px some na abertura: não há peça para apontar"
        r = amb.rodar(e, s, "--classe", "produto", "--comparar", "isnet")
        assert r.returncode == 64 and "não mede nada" in r.stderr, r.stderr
    print(f"   garrafa na mão: IoU {esperado} < .90, aviso com a caixa da garrafa {GARRAFA}; mãos vazias: IoU > .98 sem aviso")


def test_da_cena_mantem_o_tamanho_e_os_fragmentos():
    with Ambiente() as amb:
        e = amb.d / "cena.png"
        figura(e, garrafa=False, fragmento=True)
        r = amb.rodar(e, amb.d / "sem.png", "--classe", "pessoa-livre")
        assert r.returncode == 0 and "fragmento(s) solto(s) descartado(s)" in r.stdout, r.stdout
        assert np.asarray(Image.open(amb.d / "sem.png"))[182, 4, 3] == 0, "sem --da-cena o pedaço solto sai"
        r = amb.rodar(e, amb.d / "com.png", "--classe", "pessoa-livre", "--da-cena")
        assert r.returncode == 0 and "registro: 200 x 200 px" in r.stdout and "descartado" not in r.stdout, r.stdout
        com = Image.open(amb.d / "com.png")
        assert com.size == (200, 200) and np.asarray(com)[182, 4, 3] > 0, "com --da-cena o pedaço fica no lugar"


# --------------------------------------------------------------------------------------------- rodada real
def test_rodada_real_pessoa_livre_da_cena_com_comparar():
    if "--real" not in sys.argv and os.environ.get("MEDIAKIT_RECORTE_REAL") != "1":
        print("   PULADA: a rodada real é manual (passa de 20 s); rode com --real. O resultado com gente de verdade está no topo")
        return
    import importlib.util
    spec = importlib.util.spec_from_file_location("recortar", AQUI / "recortar.py")
    rec = importlib.util.module_from_spec(spec); spec.loader.exec_module(rec)
    faltam = [m for m in ("u2net_human_seg", "isnet-general-use") if rec.arquivo_do_modelo(m) is None]
    if faltam:
        print(f"   PULADA: {faltam} fora de ~/.rembg/models nesta máquina (a prova nunca baixa)")
        return
    with tempfile.TemporaryDirectory() as d:
        e, s = Path(d) / "cena.png", Path(d) / "pessoa.png"
        figura(e, tam=256)
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        t0 = time.time()
        r = subprocess.run([PY, str(AQUI / "recortar.py"), str(e), str(s), "--classe", "pessoa-livre", "--da-cena", "--comparar", "isnet"],
                           capture_output=True, text=True, env=env, timeout=300)
        dt = time.time() - t0
        assert r.returncode == 0, r.stderr[-500:]
        out = Image.open(s)
        assert out.mode == "RGBA" and out.size == (256, 256), (out.mode, out.size)
        rec_ = json.loads(Path(d, "pessoa.meta.json").read_text())["recorte"]
        assert rec_["modelo"] == "u2net_human_seg" and rec_["comparar"]["modelo"] == "isnet-general-use"
        assert 0 <= rec_["comparar"]["iou"] <= 1 and rec_["comparar"]["aviso"] == (rec_["comparar"]["iou"] < 0.9)
        print(f"   rembg real, 256 px, dois modelos: {dt:.1f} s, IoU {rec_['comparar']['iou']} (figura sintética: o modelo de "
              f"pessoa mal a reconhece, o número não mede qualidade, só que a rodada real fecha)")


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


def test_saida_igual_a_entrada_recusa_e_preserva_a_foto(tmp_path):
    import subprocess, sys
    from PIL import Image
    foto = tmp_path / "foto.jpg"
    Image.new("RGB", (20, 20), (200, 10, 10)).save(foto)
    antes = foto.read_bytes()
    for saida in (foto, tmp_path / "recorte.jpg"):
        r = subprocess.run([sys.executable, "-m", "mediakit.ferramentas.recortar", str(foto), str(saida), "--classe", "produto"],
                           capture_output=True, text=True)
        assert r.returncode == 64, r.stderr
    assert foto.read_bytes() == antes

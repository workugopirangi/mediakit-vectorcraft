#!/usr/bin/env python3
"""Provas do que repete e protege a chamada ao Codex (codex_gerar.sh, usado por elementos.sh, cena.sh e cena_limpar.sh) e do
recortar.py sem plano B. Rodar: ~/.venvs/mediakit/bin/python test_codex.py (ou pytest).

NUNCA chama o Codex de verdade e nunca gasta cota: cada prova põe um `codex` FALSO (script numa pasta temporária, na frente
do PATH) que segue um roteiro, uma ação por chamada (a última se repete): ok, falha, falha-0, truncado, ok-sai-1, cota,
login, lento:N. O falso faz o que o de verdade faz: ecoa o prompt inteiro na saída (por isso a palavra "quota" do prompt
aparece na saída de todo erro), grava o PNG no caminho que o prompt manda, escreve a última mensagem em -o e registra cada
chamada (hora, pid, argv e se herdou o fd 9, que é a trava). Ação devagar:N grava 60% do PNG, espera N segundos e grava o
resto: durante a espera o arquivo existe mas não abre, como o PNG que o Codex está escrevendo agora."""
import json, os, re, shutil, signal, subprocess, sys, tempfile, time
from pathlib import Path
from PIL import Image

AQUI = Path(__file__).parent
PY = sys.executable
BASH = "/bin/bash" if os.path.exists("/bin/bash") else "bash"   # no Mac é o 3.2, o mais velho que o kit precisa aguentar
FRASE_COTA = "cota do Codex: espere e rode de novo; não troque de fornecedor"
SCRIPTS = ("elementos.sh", "cena.sh", "cena_limpar.sh")

FALSO = r'''#!@PY@
import json, os, re, sys, time
from io import BytesIO
from PIL import Image

pasta = os.environ["FAKE_CODEX_DIR"]
argv = sys.argv[1:]
prompt = argv[-1]
roteiro = [l.strip() for l in open(os.path.join(pasta, "roteiro")).read().splitlines() if l.strip()]
reg = os.path.join(pasta, "chamadas.jsonl")


def log(**kw):
    with open(reg, "a") as f:
        f.write(json.dumps(dict(kw, t=time.time(), pid=os.getpid())) + "\n")


def fd_aberto(n):
    try:
        os.fstat(n)
        return True
    except OSError:
        return False


n = (sum(1 for l in open(reg) if '"ev": "inicio"' in l) if os.path.exists(reg) else 0) + 1
acao = roteiro[min(n, len(roteiro)) - 1]
log(ev="inicio", n=n, acao=acao, argv=argv, fd9=fd_aberto(9))
print("OpenAI Codex (fake)\nuser\n" + prompt)             # o Codex de verdade ecoa o prompt inteiro
caminho = re.search(r"exactly as (/\S+?\.png)", prompt).group(1)


def png_bytes():
    im = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    for x in range(24, 72):
        for y in range(24, 72):
            im.putpixel((x, y), (150 + 10 * n, 140, 40, 255))   # a cor diz de qual chamada o PNG veio
    buf = BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def png(inteiro=True):
    dados = png_bytes()
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(dados if inteiro else dados[: len(dados) * 6 // 10])


def png_devagar(espera):
    dados = png_bytes()
    meio = len(dados) * 6 // 10
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(dados[:meio]); f.flush(); os.fsync(f.fileno())
        time.sleep(espera)
        f.write(dados[meio:])


def mensagem():
    with open(argv[argv.index("-o") + 1], "w") as f:
        f.write("TRANSPARENT: yes\nno defects\n")


rc = 0
if acao.startswith("lento:"):
    time.sleep(float(acao.split(":")[1]))
    acao = "ok"
if acao in ("ok", "ok-sai-1"):
    png(); mensagem(); print("saved " + caminho)
    rc = 1 if acao == "ok-sai-1" else 0
elif acao == "truncado":
    png(inteiro=False); mensagem(); print("saved " + caminho); rc = 0
elif acao.startswith("devagar:"):
    png_devagar(float(acao.split(":")[1])); mensagem(); print("saved " + caminho); rc = 0
elif acao == "falha":
    print("ERROR: stream disconnected before completion: error sending request for url (https://chatgpt.com/backend-api/codex/responses)", file=sys.stderr); rc = 1
elif acao == "falha-0":
    print("I could not save the image this time.", file=sys.stderr); rc = 0
elif acao == "cota":
    print("ERROR: You've hit your usage limit. Upgrade to Pro (https://openai.com/chatgpt/pricing) or try again in 3 days 4 hours.", file=sys.stderr); rc = 1
elif acao == "login":
    print("ERROR: unexpected status 401 Unauthorized: Missing bearer or basic authentication in header", file=sys.stderr); rc = 1
elif acao == "nao-logado":
    print("Not logged in. Please run `codex login`.", file=sys.stderr); rc = 1
else:
    raise SystemExit("ação desconhecida no roteiro: " + acao)
log(ev="fim", n=n, rc=rc)
sys.exit(rc)
'''


class Cenario:
    """Pasta temporária com o codex falso na frente do PATH, o kit, o registro das chamadas e um TMPDIR só dele (para provar
    que a biblioteca não deixa arquivo temporário para trás)."""

    def __init__(self, roteiro, espera="0.1", extra=None):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.bin, self.estado, self.kit, self.lixo = d / "bin", d / "estado", d / "kit", d / "tmp"
        for p in (self.bin, self.estado, self.lixo):
            p.mkdir()
        (self.bin / "codex").write_text(FALSO.replace("@PY@", PY))
        (self.bin / "codex").chmod(0o755)
        (self.estado / "roteiro").write_text("\n".join(roteiro) + "\n")
        env = {k: v for k, v in os.environ.items() if k != "ELEMENTOS_DRY"}
        self.env = dict(env, PATH=f"{self.bin}:{env['PATH']}", FAKE_CODEX_DIR=str(self.estado), MEDIAKIT_PY=PY,
                        MEDIAKIT_CODEX_ESPERA=espera, TMPDIR=str(self.lixo), **(extra or {}))
        assert shutil.which("codex", path=self.env["PATH"]) == str(self.bin / "codex"), "a prova nunca pode chamar o Codex de verdade"
        self.origem = d / "origem.png"
        Image.new("RGB", (64, 36), (90, 120, 150)).save(self.origem)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.tmp.cleanup()

    def alvo(self, script, id_="x1"):
        """(argumentos do script, caminho do PNG que o Codex grava)."""
        acervo = self.kit / "acervo"
        if script == "elementos.sh":
            return [script, str(self.kit), id_, "objeto", "an orange training cone"], acervo / "elementos" / f"{id_}.bruto.png"
        if script == "cena.sh":                     # o prompt nunca vai na linha de comando: o script lê acervo/<id>.prompt.txt
            acervo.mkdir(parents=True, exist_ok=True)
            (acervo / f"{id_}.prompt.txt").write_text("Scene: a stadium at dawn, crowd behind a smooth blank arch", encoding="utf-8")
            return [script, str(self.kit), id_], acervo / f"{id_}.png"
        return [script, str(self.kit), id_, str(self.origem)], acervo / f"{id_}.png"

    def popen(self, args, **kw):
        return subprocess.Popen([BASH, str(AQUI / args[0]), *args[1:]], env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, **kw)

    def rodar(self, args, timeout=180, entrada=None, cwd=None):
        return subprocess.run([BASH, str(AQUI / args[0]), *args[1:]], capture_output=True, text=True, env=self.env, timeout=timeout,
                              input=entrada, cwd=cwd)

    def chamadas(self):
        arq = self.estado / "chamadas.jsonl"
        return [json.loads(l) for l in arq.read_text().splitlines()] if arq.exists() else []

    def inicios(self):
        return [c for c in self.chamadas() if c["ev"] == "inicio"]

    def esperar_inicios(self, n, limite=30):
        t0 = time.time()
        while len(self.inicios()) < n:
            assert time.time() - t0 < limite, f"o codex falso não chegou a {n} chamada(s)"
            time.sleep(0.05)

    def sem_lixo(self):
        sobra = sorted(p.name for p in self.lixo.glob("codex-saida.*"))
        assert not sobra, f"arquivo temporário da biblioteca que ficou para trás: {sobra}"


def numero_da_chamada(png):
    """De qual chamada do codex falso veio o PNG (a cor do miolo é 150 + 10 x nº da chamada)."""
    with Image.open(png) as im:
        im.load()
        return (im.convert("RGBA").getpixel((48, 48))[0] - 150) // 10


def aberto_inteiro(png):
    try:
        with Image.open(png) as im:
            im.load()
        return True
    except Exception:
        return False


def bash(codigo, *args, env_extra=None):
    """Roda um trecho de bash depois de carregar a biblioteca (assim se prova cada função sozinha)."""
    env = dict(os.environ, MEDIAKIT_PY=PY, **(env_extra or {}))
    return subprocess.run([BASH, "-c", f'. "{AQUI}/codex_gerar.sh"; {codigo}', "_", *map(str, args)], capture_output=True, text=True, env=env)


# --------------------------------------------------------------------------------------------- o PNG que abre inteiro
def test_png_ok_so_aceita_o_que_abre_inteiro():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        bom = d / "bom.png"
        im = Image.new("RGBA", (200, 200))
        for x in range(0, 200, 3):
            for y in range(0, 200, 2):
                im.putpixel((x, y), ((x * 7) % 256, (y * 11) % 256, (x + y) % 256, 255))
        im.save(bom)
        dados = bom.read_bytes()
        (d / "metade.png").write_bytes(dados[: len(dados) // 2])
        (d / "sem-iend.png").write_bytes(dados[:-12])           # perdeu só o rodapé IEND: todos os pixels decodificam, então vale
        (d / "corte-nos-dados.png").write_bytes(dados[:-40])    # perdeu o fim dos dados comprimidos: não vale
        (d / "vazio.png").write_bytes(b"")
        (d / "texto.png").write_text("isto nao e um png")
        casos = {"bom.png": 0, "sem-iend.png": 0, "metade.png": 1, "corte-nos-dados.png": 1, "vazio.png": 1, "texto.png": 1, "nao-existe.png": 1}
        for nome, esperado in casos.items():
            r = bash('png_ok "$1"', d / nome)
            assert r.returncode == esperado, (nome, r.returncode, r.stderr)
        print("   png_ok: " + ", ".join(f"{n}={'ok' if c == 0 else 'recusa'}" for n, c in casos.items()))
        # conferir nunca apaga nem cria nada: o quebrado só é apagado dentro de codex_gerar, já com a trava (prova mais abaixo)
        assert (d / "metade.png").exists() and (d / "bom.png").read_bytes() == dados and not (d / "nao-existe.png").exists()


# --------------------------------------------------------------------------------------------- o que é cota e login
POSITIVAS = [
    "ERROR: You've hit your usage limit. Upgrade to Pro (https://openai.com/chatgpt/pricing) or try again in 5 days 3 hours.",
    "ERROR: exceeded retry limit, last status: 429 Too Many Requests",
    "ERROR: unexpected status 401 Unauthorized: Missing bearer or basic authentication in header",
    "Not logged in. Please run `codex login`.",
    "ERROR: You exceeded your current quota, please check your plan and billing details.",
    "You've reached your image generation limit. Try again tomorrow.",
    "Please sign in to continue",
    "{\"error\":{\"code\":\"rate_limit_exceeded\"}}",
    "{\"error\":{\"code\":\"invalid_api_key\"}}",
    "Your access token could not be refreshed because your refresh token was already used.",
    "\x1b[31mERROR\x1b[0m: usage limit reached",
]
NEGATIVAS = [
    "ERROR: stream disconnected before completion: error sending request for url (https://chatgpt.com/backend-api/codex/responses)",
    "ERROR: unexpected status 500 Internal Server Error",
    "ERROR: unexpected status 503 Service Unavailable: upstream overloaded",
    "Reconnecting... 2/5",
    "tokens used: 12,345",
    "saved /kit/acervo/elementos/cone-401.png",
    "I could not save the image this time.",
    "the connection was reset by peer",
    "Do NOT regenerate under any circumstance, not even if a check below fails (each generation spends the ChatGPT quota). Make exactly one image generation call and keep that single image.",
]


def test_cota_e_login_param_e_o_erro_passageiro_nao():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        for linha in POSITIVAS:
            (d / "saida.txt").write_text("progress...\n" + linha + "\n")
            r = bash('codex_cota "$1"', d / "saida.txt")
            assert r.returncode == 0 and r.stdout.strip(), f"devia ser cota ou login: {linha!r}"
        for linha in NEGATIVAS:
            (d / "saida.txt").write_text("progress...\n" + linha + "\n")
            r = bash('codex_cota "$1"', d / "saida.txt")
            assert r.returncode == 1, f"erro passageiro tomado por cota: {linha!r} -> {r.stdout!r}"
        print(f"   {len(POSITIVAS)} mensagens de cota e login param; {len(NEGATIVAS)} de erro passageiro seguem para a repetição")
        # a linha do PRÓPRIO prompt, que o Codex ecoa, não vale como denúncia: com ela nos argumentos do comando é descartada
        eco = "Never exceed the ChatGPT quota."
        (d / "saida.txt").write_text("user\n" + eco + "\nERROR: stream disconnected before completion\n")
        assert bash('codex_cota "$1"', d / "saida.txt").returncode == 0, "sem o filtro, a linha do prompt acusaria cota (a prova do controle)"
        assert bash('codex_cota "$1" codex exec "$2"', d / "saida.txt", "intro\n" + eco).returncode == 1
        # só a cauda vale: um erro de cota velho, lá no começo de uma saída enorme, não para a repetição de agora
        (d / "longa.txt").write_text("ERROR: usage limit reached\n" + "\n".join(f"linha {i}" for i in range(200)) + "\n")
        assert bash('codex_cota "$1"', d / "longa.txt").returncode == 1


# --------------------------------------------------------------------------------------------- falha 2 vezes, acerta na 3ª
def test_falha_duas_vezes_e_acerta_na_terceira_em_cada_script():
    for script in SCRIPTS:
        with Cenario(["falha", "falha", "ok"]) as c:
            args, png = c.alvo(script)
            r = c.rodar(args)
            assert r.returncode == 0, (script, r.returncode, r.stderr[-800:])
            ini = c.inicios()
            assert [i["acao"] for i in ini] == ["falha", "falha", "ok"], ini
            assert aberto_inteiro(png) and numero_da_chamada(png) == 3, "o PNG final tem de ser o da 3ª chamada"
            assert "tentativa 1 de 3 falhou" in r.stderr and "tentativa 2 de 3 falhou" in r.stderr and "entregou na tentativa 3 de 3" in r.stderr
            assert not r.stderr.count("cota do Codex"), "erro passageiro tomado por cota"
            # o comando que o Codex recebe é o de sempre, o mesmo nas 3 chamadas, e ele não herda a trava (fd 9)
            a = ini[0]["argv"]
            assert a[0] == "exec" and "--sandbox" in a and a[a.index("--sandbox") + 1] == "workspace-write" and "--skip-git-repo-check" in a
            assert "-c" in a and a[a.index("-c") + 1] == "sandbox_workspace_write.network_access=false", "o sandbox tem de ficar sem rede"
            assert Path(a[a.index("-C") + 1]).resolve() == png.parent.resolve()
            assert a[a.index("-o") + 1].endswith("/.codex-x1.log")
            assert ("-i" in a) == (script == "cena_limpar.sh")
            assert all(i["argv"] == a for i in ini) and not any(i["fd9"] for i in ini)
            hist = (png.parent / ".codex-x1.saida").read_text()
            assert hist.count("== tentativa") == 2, "a saída das duas que falharam fica guardada"
            assert not any(p.name.endswith(".anterior") for p in png.parent.iterdir())
            c.sem_lixo()
            if script == "elementos.sh":                      # o resto do caminho segue: alfa medido, ficha, log
                assert "rota=codex-alfa" in r.stdout and (png.parent / "x1.meta.json").exists() and (png.parent / "x1.png").exists()
            print(f"   {script}: 3 chamadas (falha, falha, ok), PNG da 3ª, saída 0")


def test_a_espera_entre_as_tentativas_cresce():
    with Cenario(["falha", "falha", "ok"], espera="1") as c:
        args, _ = c.alvo("cena.sh")
        r = c.rodar(args)
        assert r.returncode == 0, r.stderr[-500:]
        t = [i["t"] for i in c.inicios()]
        g1, g2 = t[1] - t[0], t[2] - t[1]
        print(f"   espera base 1 s: intervalos entre as chamadas {g1:.2f} s e {g2:.2f} s")
        assert g1 >= 1.0 and g2 >= 2.0, (g1, g2)               # 1 x 1 s e depois 2 x 1 s: cada espera é a base vezes o nº da tentativa
        assert "espero 1s" in r.stderr and "espero 2s" in r.stderr


# --------------------------------------------------------------------------------------------- falha sempre: termina na 3ª e avisa
def test_falha_sempre_termina_na_terceira_e_avisa_em_cada_script():
    for script in SCRIPTS:
        with Cenario(["falha"]) as c:
            args, png = c.alvo(script)
            r = c.rodar(args)
            assert r.returncode == 1, (script, r.returncode, r.stderr[-500:])
            assert len(c.inicios()) == 3, f"{script}: tinha de parar na 3ª tentativa, fez {len(c.inicios())}"
            assert "em 3 tentativa(s)" in r.stderr and "não troque de fornecedor" in r.stderr and ".codex-x1.saida" in r.stderr
            assert "ChatGPT quota" in r.stdout, "o falso ecoou o prompt (que cita quota): a prova só vale se o eco estava lá"
            assert FRASE_COTA not in r.stderr, "o eco do prompt foi tomado por erro de cota"
            assert not png.exists() and "OK " not in r.stdout
            assert (png.parent / ".codex-x1.saida").read_text().count("== tentativa") == 3
            assert not any(p.name.endswith(".anterior") for p in png.parent.iterdir())
            c.sem_lixo()
            print(f"   {script}: 3 chamadas, saída 1, aviso com o caminho do histórico, sem PNG")


def test_saida_zero_sem_imagem_tambem_conta_como_falha_e_imagem_boa_com_codigo_um_e_aceita():
    with Cenario(["falha-0", "ok"]) as c:
        args, png = c.alvo("cena.sh")
        r = c.rodar(args)
        assert r.returncode == 0 and len(c.inicios()) == 2 and numero_da_chamada(png) == 2, (r.returncode, r.stderr[-300:])
    with Cenario(["ok-sai-1"]) as c:
        args, png = c.alvo("cena.sh")
        r = c.rodar(args)
        assert r.returncode == 0 and len(c.inicios()) == 1 and aberto_inteiro(png), (r.returncode, r.stderr[-300:])
        assert "saiu com código 1 mas entregou" in r.stderr, "avisa que aceitou um PNG inteiro de um Codex que saiu com erro"


# --------------------------------------------------------------------------------------------- cota e login: para na hora
def test_cota_e_login_saem_com_3_na_primeira_sem_repetir_em_cada_script():
    for script in SCRIPTS:
        for acao, trecho in (("cota", "usage limit"), ("login", "401 Unauthorized"), ("nao-logado", "Not logged in")):
            with Cenario([acao]) as c:
                args, png = c.alvo(script)
                t0 = time.time()
                r = c.rodar(args)
                assert r.returncode == 3, (script, acao, r.returncode, r.stderr[-500:])
                assert len(c.inicios()) == 1, f"{script}/{acao}: não podia repetir, fez {len(c.inicios())} chamadas"
                assert FRASE_COTA in r.stderr and trecho in r.stderr, r.stderr[-500:]
                assert "tentativa 1 de 3 falhou" not in r.stderr and not png.exists()
                assert time.time() - t0 < 15
                c.sem_lixo()
        print(f"   {script}: cota, 401 e 'not logged in' saem com 3 na 1ª chamada, com a frase exata")
    # falha passageira primeiro e cota depois: repete uma vez e então para
    with Cenario(["falha", "cota", "ok"]) as c:
        args, png = c.alvo("cena.sh")
        r = c.rodar(args)
        assert r.returncode == 3 and len(c.inicios()) == 2 and not png.exists(), (r.returncode, len(c.inicios()))


# --------------------------------------------------------------------------------------------- bruto truncado é refeito
def test_png_truncado_e_refeito_na_repeticao_e_o_bruto_velho_quebrado_e_apagado_antes_de_pular():
    for script in SCRIPTS:
        # (a) o Codex entrega a metade do PNG e sai com 0: a 1ª tentativa não vale, a 2ª sim
        with Cenario(["truncado", "ok"]) as c:
            args, png = c.alvo(script)
            r = c.rodar(args)
            assert r.returncode == 0 and len(c.inicios()) == 2 and numero_da_chamada(png) == 2, (script, r.returncode, r.stderr[-400:])
            assert "saiu truncado ou ilegível" in r.stderr
        # (b) truncado todas as vezes: não fica PNG quebrado para trás, e sai com 1
        with Cenario(["truncado"]) as c:
            args, png = c.alvo(script)
            r = c.rodar(args)
            assert r.returncode == 1 and len(c.inicios()) == 3 and not png.exists(), (script, r.returncode)
    # (c) o "já existe" que pula a geração: bruto quebrado do dia anterior é apagado e gerado de novo; bruto bom pula
    for script in ("elementos.sh", "cena_limpar.sh"):
        with Cenario(["ok"]) as c:
            args, png = c.alvo(script)
            png.parent.mkdir(parents=True, exist_ok=True)
            bom = c.estado / "bom.png"
            Image.new("RGBA", (96, 96), (1, 2, 3, 4)).save(bom)
            velho = bom.read_bytes()
            png.write_bytes(velho[: len(velho) // 2])
            r = c.rodar(args)
            assert r.returncode == 0 and len(c.inicios()) == 1, (script, r.returncode, r.stderr[-400:])
            assert "não abre inteiro" in r.stderr and "já existe" not in r.stdout
            assert aberto_inteiro(png) and numero_da_chamada(png) == 1, "o bruto truncado tinha de ser refeito"
            # controle: agora o PNG é bom e inteiro, a segunda rodada pula sem chamar o Codex
            r2 = c.rodar(args)
            assert r2.returncode == 0 and len(c.inicios()) == 1 and "já existe" in r2.stdout, (script, r2.stdout[-300:])
    with Cenario(["ok"]) as c:                                  # vazio (0 byte) também é quebrado
        args, png = c.alvo("elementos.sh")
        png.parent.mkdir(parents=True, exist_ok=True)
        png.write_bytes(b"")
        r = c.rodar(args)
        assert r.returncode == 0 and len(c.inicios()) == 1 and aberto_inteiro(png)
    print("   truncado: refeito na repetição, apagado antes do 'já existe', 0 byte também; bom e inteiro pula sem chamar o Codex")


# --------------------------------------------------------------------------------------------- regerar por cima (cena.sh)
def test_cena_regera_por_cima_e_a_imagem_anterior_volta_se_nenhuma_tentativa_entregar():
    with Cenario(["falha"]) as c:
        args, png = c.alvo("cena.sh")
        png.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (96, 96), (9, 8, 7, 255)).save(png)
        antes = png.read_bytes()
        r = c.rodar(args)
        assert r.returncode == 1 and len(c.inicios()) == 3
        assert png.read_bytes() == antes, "a cena boa de antes tinha de continuar no lugar, byte a byte"
        assert not (png.parent / "x1.png.anterior").exists() and "ficou a imagem anterior" in r.stderr
        c.sem_lixo()
    with Cenario(["falha", "ok"]) as c:
        args, png = c.alvo("cena.sh")
        png.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (96, 96), (9, 8, 7, 255)).save(png)
        r = c.rodar(args)
        assert r.returncode == 0 and numero_da_chamada(png) == 2, "regerou por cima (como antes: cena reprovada volta com o defeito nomeado)"
        assert not (png.parent / "x1.png.anterior").exists()
    with Cenario(["cota"]) as c:                                # cota também devolve a imagem anterior
        args, png = c.alvo("cena.sh")
        png.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (96, 96), (9, 8, 7, 255)).save(png)
        antes = png.read_bytes()
        assert c.rodar(args).returncode == 3 and png.read_bytes() == antes


def test_sigterm_no_meio_da_regeracao_devolve_a_imagem_anterior_e_solta_a_trava():
    with Cenario(["lento:20", "ok"]) as c:
        args, png = c.alvo("cena.sh")
        png.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (96, 96), (9, 8, 7, 255)).save(png)
        antes = png.read_bytes()
        p = c.popen(args, start_new_session=True)
        c.esperar_inicios(1)
        os.killpg(p.pid, signal.SIGTERM)                        # como ao encerrar o processo inteiro (script, Codex e tee)
        p.communicate(timeout=20)
        assert p.returncode == 143, p.returncode
        assert png.read_bytes() == antes and not (png.parent / "x1.png.anterior").exists()
        c.sem_lixo()
        t0 = time.time()                                        # e a trava ficou livre
        r = c.rodar(args)
        assert r.returncode == 0 and time.time() - t0 < 15 and numero_da_chamada(png) == 2


# --------------------------------------------------------------------------------------------- uma chamada por vez
def test_duas_chamadas_no_mesmo_kit_nao_se_sobrepoem_e_a_segunda_espera():
    with Cenario(["lento:1.5"]) as c:
        a, _ = c.alvo("elementos.sh", "a")
        b, _ = c.alvo("cena.sh", "b")                           # scripts diferentes, mesmo kit: a trava é do kit
        pa = c.popen(a)
        c.esperar_inicios(1)
        pb = c.popen(b)
        oa, ea = pa.communicate(timeout=120)
        ob, eb = pb.communicate(timeout=120)
        assert pa.returncode == 0 and pb.returncode == 0, (ea[-300:], eb[-300:])
        ev = [(e["ev"], e["n"], e["t"]) for e in c.chamadas()]
        assert [(x, n) for x, n, _ in ev] == [("inicio", 1), ("fim", 1), ("inicio", 2), ("fim", 2)], ev
        folga = ev[2][2] - ev[1][2]
        print(f"   chamada 1 terminou e a 2 só começou {folga:.2f} s depois; sem sobreposição")
        assert folga >= 0, "a 2ª chamada começou antes de a 1ª terminar"
        assert "uma por vez" in eb and "uma por vez" not in ea
        assert not any(i["fd9"] for i in c.inicios()), "o Codex herdou o fd da trava"
        c.sem_lixo()


def test_a_segunda_chamada_do_mesmo_elemento_espera_e_nao_gera_de_novo():
    with Cenario(["lento:1.5", "ok"]) as c:
        args, png = c.alvo("elementos.sh", "igual")
        p1 = c.popen(args)
        c.esperar_inicios(1)
        p2 = c.popen(args)
        o1, e1 = p1.communicate(timeout=120)
        o2, e2 = p2.communicate(timeout=120)
        assert p1.returncode == 0 and p2.returncode == 0, (e1[-300:], e2[-300:])
        assert len(c.inicios()) == 1, "o mesmo bruto não pode custar duas gerações"
        assert "outra chamada o gerou enquanto esta esperava a trava" in o2, o2[-300:]
        assert aberto_inteiro(png)
        # quem esperou só confere e sai: a rota, o <id>.png e a ficha são da chamada que gerou (uma vez só, sem os dois escrevendo juntos)
        assert "OK " not in o2 and "a outra chamada que gerou" in o2, o2[-300:]
        assert (png.parent / "igual.prompt.txt").exists() and json.loads((png.parent / "igual.meta.json").read_text())["prompt"].endswith("igual.prompt.txt")
        assert len((png.parent / "elementos.log").read_text().splitlines()) == 1, "o pós-processamento rodou duas vezes"


def test_trava_de_quem_morreu_com_kill_9_nao_prende_ninguem():
    with Cenario(["lento:30", "ok"]) as c:
        a, _ = c.alvo("elementos.sh", "a")
        b, pb = c.alvo("elementos.sh", "b")
        p = c.popen(a, start_new_session=True)
        c.esperar_inicios(1)
        os.killpg(p.pid, signal.SIGKILL)                        # sem trap, sem limpeza: o sistema é que solta a trava
        p.communicate(timeout=20)
        t0 = time.time()
        r = c.rodar(b)
        gasto = time.time() - t0
        print(f"   depois do kill -9 do dono, a chamada seguinte entrou em {gasto:.1f} s")
        assert r.returncode == 0 and aberto_inteiro(pb) and gasto < 20, (r.returncode, r.stderr[-300:])
        assert "uma por vez" not in r.stderr, "esperou uma trava que não tinha dono"


def test_trava_ocupada_alem_do_limite_sai_com_4_sem_chamar_o_codex():
    with Cenario(["lento:8", "ok"], extra={"MEDIAKIT_CODEX_ESPERA_TRAVA": "1"}) as c:
        a, _ = c.alvo("elementos.sh", "a")
        b, pb = c.alvo("cena.sh", "b")
        p = c.popen(a, start_new_session=True)
        c.esperar_inicios(1)
        r = c.rodar(b)
        assert r.returncode == 4 and "há 1 s" in r.stderr and not pb.exists(), (r.returncode, r.stderr[-300:])
        assert len(c.inicios()) == 1, "a chamada barrada não pode ter ido ao Codex"
        os.killpg(p.pid, signal.SIGKILL)
        p.communicate(timeout=20)


def test_chamada_que_espera_a_trava_nao_apaga_o_png_que_a_outra_esta_gravando():
    with Cenario(["devagar:4"]) as c:
        args, png = c.alvo("elementos.sh", "igual")
        pa = c.popen(args)
        c.esperar_inicios(1)
        t0 = time.time()
        while not (png.exists() and png.stat().st_size > 0):        # o PNG da chamada 1 já existe, mas só pela metade
            assert time.time() - t0 < 10, "o codex falso não começou a gravar"
            time.sleep(0.05)
        assert not aberto_inteiro(png)
        pb = c.popen(args)                                          # mesmo elemento: a B vê um PNG que não abre e tem de ESPERAR, não apagar
        time.sleep(2.0)
        assert pb.poll() is None and png.exists() and png.stat().st_size > 0 and not aberto_inteiro(png), "a B apagou o PNG que a A ainda grava"
        oa, ea = pa.communicate(timeout=120)
        ob, eb = pb.communicate(timeout=120)
        assert pa.returncode == 0 and pb.returncode == 0, (ea[-300:], eb[-300:])
        assert len(c.inicios()) == 1, f"o PNG da A foi apagado e refeito: {len(c.inicios())} gerações"
        assert aberto_inteiro(png) and numero_da_chamada(png) == 1
        assert "uma por vez" in eb and "não abre inteiro" not in eb


def test_sem_pil_no_python_do_kit_sai_com_5_antes_de_gastar_cota():
    with tempfile.TemporaryDirectory() as stub:
        (Path(stub) / "PIL").mkdir()
        (Path(stub) / "PIL" / "__init__.py").write_text("raise ImportError('sem PIL de proposito (prova)')\n")
        for script in ("cena.sh", "elementos.sh"):
            with Cenario(["ok"], extra={"PYTHONPATH": stub}) as c:
                args, png = c.alvo(script)
                r = c.rodar(args)
                assert r.returncode == 5 and "falta o PIL" in r.stderr, (script, r.returncode, r.stderr[-300:])
                assert c.inicios() == [] and not png.exists(), "sem como conferir o PNG, não pode ter chamado o Codex"
                t0 = time.time()                                    # e a trava ficou livre
                assert subprocess.run([BASH, "-c", f'. "{AQUI}/codex_gerar.sh"; MEDIAKIT_CODEX_ESPERA_TRAVA=3 codex_travar "$1"', "_", str(c.kit / "acervo")],
                                      capture_output=True, text=True, env=dict(c.env, PYTHONPATH="")).returncode == 0 and time.time() - t0 < 3
    print("   Python do kit sem PIL: sai com 5 antes de chamar o Codex (0 chamadas)")


def test_pasta_que_nao_aceita_flock_avisa_e_segue_sem_trava():
    with tempfile.TemporaryDirectory() as stub:
        (Path(stub) / "sitecustomize.py").write_text(
            "import errno, fcntl\n"
            "def _sem_flock(fd, op):\n    raise OSError(errno.ENOTSUP, 'flock nao suportado (prova)')\n"
            "fcntl.flock = _sem_flock\n")
        with Cenario(["ok"], extra={"PYTHONPATH": stub}) as c:
            args, png = c.alvo("cena.sh")
            t0 = time.time()
            r = c.rodar(args)
            assert r.returncode == 0 and aberto_inteiro(png) and len(c.inicios()) == 1, (r.returncode, r.stderr[-300:])
            assert "não aceita trava" in r.stderr and time.time() - t0 < 20, "tinha de avisar e seguir, não esperar uma trava impossível"


# --------------------------------------------------------------------------------------------- achados da revisão de segurança
HOSTIS = ["ok\n../../X", "../../X", "a/b", "A", "x y", "-x", "", "x_y", "çã", "x.png"]     # o da quebra de linha primeiro: é o que o grep antigo deixava passar


def arvore(raiz):
    """Todos os caminhos sob `raiz` (para provar que nada foi criado fora de onde devia)."""
    return sorted(str(p.relative_to(raiz)) for p in Path(raiz).rglob("*"))


def test_cena_le_o_prompt_do_arquivo_e_o_texto_do_evento_nunca_e_executado():
    perigo = ("Scene: finish line.\nEvento: $(touch PWNED_A) e `touch PWNED_B` e \"; touch PWNED_C; echo \" e '; touch PWNED_D; '\n"
              "EOT\nlinha depois do EOT: MARCA-FINAL ${HOME} $0 \\n")
    with Cenario(["ok"]) as c:
        args, png = c.alvo("cena.sh", "perigo")
        (png.parent / "perigo.prompt.txt").write_text(perigo, encoding="utf-8")
        trabalho = Path(c.tmp.name) / "trabalho"
        trabalho.mkdir()
        r = c.rodar(args, cwd=trabalho)
        assert r.returncode == 0, r.stderr[-400:]
        achados = [p for p in arvore(c.tmp.name) if "PWNED" in p]
        assert not achados, f"o texto do evento rodou como comando: {achados}"
        enviado = c.inicios()[0]["argv"][-1]
        for trecho in ("$(touch PWNED_A)", "`touch PWNED_B`", '"; touch PWNED_C; echo "', "'; touch PWNED_D; '", "${HOME} $0 \\n", "MARCA-FINAL"):
            assert trecho in enviado, f"o texto tinha de chegar ao Codex literal, sem expandir: {trecho!r}"
        assert enviado.startswith("Generate one photorealistic image, 16:9 landscape, and save it exactly as ")
        print("   prompt com $(...), crase, aspas e uma linha EOT: chegou literal ao Codex, nada foi executado")


def test_cena_com_prompt_pela_entrada_padrao_grava_o_arquivo_e_vai_ao_codex():
    with Cenario(["ok"]) as c:
        args, png = c.alvo("cena.sh", "viaentrada")
        (png.parent / "viaentrada.prompt.txt").unlink()
        r = c.rodar(args + ["-"], entrada="Scene: crowd at the arch. $(touch PWNED_E)\n")
        assert r.returncode == 0 and aberto_inteiro(png), r.stderr[-300:]
        assert (png.parent / "viaentrada.prompt.txt").read_text() == "Scene: crowd at the arch. $(touch PWNED_E)\n"
        assert "Scene: crowd at the arch. $(touch PWNED_E)" in c.inicios()[0]["argv"][-1]
        assert not [p for p in arvore(c.tmp.name) if "PWNED" in p]


def test_cena_sem_prompt_ou_com_prompt_na_linha_de_comando_nao_chama_o_codex():
    with Cenario(["ok"]) as c:
        args, png = c.alvo("cena.sh", "semprompt")
        (png.parent / "semprompt.prompt.txt").unlink()
        r = c.rodar(args)                                                   # sem arquivo
        assert r.returncode == 66 and "falta o prompt" in r.stderr and "cena_prompt.py" in r.stderr, (r.returncode, r.stderr)
        (png.parent / "semprompt.prompt.txt").write_text("  \n\n")         # só espaço
        r = c.rodar(args)
        assert r.returncode == 66 and "em branco" in r.stderr, (r.returncode, r.stderr)
        r = c.rodar(args + ["-"], entrada="   \n")                          # entrada padrão vazia
        assert r.returncode == 66 and "vazio" in r.stderr, (r.returncode, r.stderr)
        r = c.rodar(args + ["Scene: um prompt na linha de comando $(touch PWNED_F)"])
        assert r.returncode == 64 and "não vai mais na linha de comando" in r.stderr and "cena_prompt.py --salvar semprompt" in r.stderr, r.stderr
        r = c.rodar(args[:2])                                               # faltou o id
        assert r.returncode == 64 and "uso:" in r.stderr
        assert c.inicios() == [] and not png.exists(), "nenhum desses casos pode gastar cota"
        assert not [p for p in arvore(c.tmp.name) if "PWNED" in p]


def test_id_com_barra_ponto_maiuscula_espaco_ou_quebra_de_linha_e_barrado_antes_de_escrever():
    for script in SCRIPTS:
        with Cenario(["ok"]) as c:
            for id_ in HOSTIS:
                args, _ = c.alvo(script, "bom")
                args[2] = id_
                antes = arvore(c.tmp.name)
                r = c.rodar(args)
                assert r.returncode == 64 and "id inválido" in r.stderr, (script, repr(id_), r.returncode, r.stderr[-200:])
                assert arvore(c.tmp.name) == antes, f"{script} com id {id_!r} escreveu algo: {set(arvore(c.tmp.name)) - set(antes)}"
            assert c.inicios() == []
    # o modo seco do elementos.sh também barra (antes só o grep, que olha linha a linha, deixava "ok\n../../X" passar)
    with Cenario(["ok"]) as c:
        args, _ = c.alvo("elementos.sh")
        args[2] = "ok\n../../X"
        c.env["ELEMENTOS_DRY"] = "1"
        r = c.rodar(args)
        assert r.returncode == 64 and "id inválido" in r.stderr and "== PROMPT" not in r.stdout, (r.returncode, r.stdout[:200])
    # ids de verdade continuam passando
    with Cenario(["ok"]) as c:
        for script, id_ in (("cena.sh", "c-portico"), ("cena_limpar.sh", "limpa-2"), ("elementos.sh", "trofeu-1")):
            args, png = c.alvo(script, id_)
            assert c.rodar(args).returncode == 0 and aberto_inteiro(png), (script, id_)
    print(f"   {len(HOSTIS)} ids hostis barrados com 64 nos 3 scripts, sem criar nada; ids normais passam")


def test_cena_prompt_py_salvar_so_aceita_id_de_arquivo():
    sys.path.insert(0, str(AQUI))
    from test_elementos_prompt import montar_kit
    with tempfile.TemporaryDirectory() as d:
        kit = Path(d) / "kit"
        montar_kit(kit)
        antes = arvore(d)
        for id_ in ("../../x", "a/b", "A", "", " x", "x\ny", "-x", "x.png"):
            r = subprocess.run([PY, str(AQUI / "cena_prompt.py"), str(kit), "ativo", f"--salvar={id_}"], capture_output=True, text=True)   # "=": o "-x" chega à checagem em vez de virar opção do argparse
            assert r.returncode == 64 and "id inválido" in r.stderr and r.stdout == "", (repr(id_), r.returncode, r.stderr[-200:])
        assert arvore(d) == antes, "um id inválido escreveu algo"
        r = subprocess.run([PY, str(AQUI / "cena_prompt.py"), str(kit), "ativo", "--salvar", "c-portico"], capture_output=True, text=True)
        assert r.returncode == 0 and (kit / "acervo" / "c-portico.prompt.txt").read_text(encoding="utf-8") == r.stdout.rstrip("\n")


def test_cena_limpar_confere_a_imagem_de_origem_antes_de_chamar_o_codex():
    with Cenario(["ok"]) as c:
        args, png = c.alvo("cena_limpar.sh", "limpa")
        falta = c.kit.parent / "nao-existe.png"
        vazia = c.kit.parent / "vazia.png"
        vazia.write_bytes(b"")
        pasta = c.kit.parent / "uma-pasta.png"
        pasta.mkdir()
        for origem in (falta, vazia, pasta, c.kit.parent / "sem-dir" / "x.png"):
            r = c.rodar(args[:3] + [str(origem)])
            assert r.returncode == 66 and "imagem de origem não existe ou está vazia" in r.stderr and "nada foi enviado ao Codex" in r.stderr, (origem.name, r.returncode, r.stderr[-200:])
        assert c.inicios() == [] and not png.exists()
        assert c.rodar(args).returncode == 0 and len(c.inicios()) == 1 and "-i" in c.inicios()[0]["argv"]     # com origem boa, segue


def test_toda_chamada_ao_codex_vai_no_sandbox_sem_rede_e_o_modo_seco_mostra():
    for script in SCRIPTS:
        with Cenario(["ok"]) as c:
            args, _ = c.alvo(script)
            assert c.rodar(args).returncode == 0
            a = c.inicios()[0]["argv"]
            assert a[a.index("--sandbox") + 1] == "workspace-write", "a flag --sandbox continua (vence o config.toml do Ugo)"
            assert a.count("-c") == 1 and a[a.index("-c") + 1] == "sandbox_workspace_write.network_access=false", (script, a[:8])
    with Cenario(["ok"]) as c:
        args, _ = c.alvo("elementos.sh")
        c.env["ELEMENTOS_DRY"] = "1"
        r = c.rodar(args)
        assert r.returncode == 0 and re.search(r"-c sandbox_workspace_write\.network_access\\?=false", r.stdout), r.stdout[-400:]
    print("   os 3 scripts: --sandbox workspace-write e -c sandbox_workspace_write.network_access=false em todo codex exec")


def test_rodar_de_novo_com_pedido_diferente_nao_reescreve_prompt_nem_ficha():
    with Cenario(["ok"]) as c:
        args, bruto = c.alvo("elementos.sh", "peca")
        pasta = bruto.parent
        base = args + ["--estilo", "flat two-tone gold"]
        r = c.rodar(base)
        assert r.returncode == 0 and len(c.inicios()) == 1, r.stderr[-300:]
        arq = lambda n: (pasta / n).read_bytes()
        fotos = {n: arq(n) for n in ("peca.prompt.txt", "peca.meta.json", "elementos.log", "peca.png", "peca.bruto.png")}
        meta = json.loads(fotos["peca.meta.json"])
        assert meta["estilo"] == "flat two-tone gold" and meta["prompt"].endswith("peca.prompt.txt")
        # (1) outro --estilo com o bruto pronto: não regera, não mexe em nada, avisa e sai com 65
        r2 = c.rodar(args + ["--estilo", "photoreal chrome"])
        assert r2.returncode == 65 and "o pedido mudou" in r2.stderr and "peca.prompt.txt" in r2.stderr, (r2.returncode, r2.stderr[-300:])
        assert len(c.inicios()) == 1, "não podia gastar cota"
        assert {n: arq(n) for n in fotos} == fotos, "a proveniência foi reescrita sem geração"
        # a descrição também faz parte do pedido
        args_d = list(base); args_d[4] = "a different object"
        assert c.rodar(args_d).returncode == 65 and {n: arq(n) for n in fotos} == fotos
        # (2) o MESMO pedido: já está completo, nada a refazer, nada reescrito (nem a data da ficha)
        r3 = c.rodar(base)
        assert r3.returncode == 0 and "completo" in r3.stdout and len(c.inicios()) == 1, (r3.returncode, r3.stdout[-300:])
        assert {n: arq(n) for n in fotos} == fotos
        # (3) retomada: o recorte caiu depois da geração (sem <id>.png nem ficha); o mesmo pedido completa SEM chamar o Codex
        (pasta / "peca.png").unlink()
        (pasta / "peca.meta.json").unlink()
        r4 = c.rodar(base)
        assert r4.returncode == 0 and len(c.inicios()) == 1 and "OK " in r4.stdout, (r4.returncode, r4.stderr[-300:])
        assert (pasta / "peca.png").exists() and json.loads((pasta / "peca.meta.json").read_text())["estilo"] == "flat two-tone gold"
        assert arq("peca.prompt.txt") == fotos["peca.prompt.txt"] and arq("peca.bruto.png") == fotos["peca.bruto.png"]
        # (4) bruto trocado à mão (mais novo que o <id>.png): reprocessa o que deriva dele, sem regerar
        time.sleep(1.1)
        (pasta / "peca.bruto.png").write_bytes(fotos["peca.bruto.png"])
        r5 = c.rodar(base)
        assert r5.returncode == 0 and "completo" not in r5.stdout and "OK " in r5.stdout and len(c.inicios()) == 1, (r5.returncode, r5.stdout[-200:])
    print("   pedido diferente: 65 e nada reescrito; mesmo pedido: no-op; recorte que caiu: completa sem cota; bruto trocado: reprocessa")


def test_o_que_nasce_junto_da_geracao_e_gravado_dentro_da_trava_antes_de_quem_espera_acordar():
    with Cenario(["ok"]) as c:
        pasta = c.kit / "acervo"
        pasta.mkdir(parents=True)
        marca, png = pasta / "marca.txt", pasta / "x.png"
        a = (f'. "{AQUI}/codex_gerar.sh"; codex_apos_gerar() {{ sleep 1.5; echo gravado > "{marca}"; }}; '
             f'codex_produzir 0 "{pasta}" "{png}" "{pasta}/.h" codex exec -o "{pasta}/.log" "salve exactly as {png}"')
        b = f'. "{AQUI}/codex_gerar.sh"; codex_travar "{pasta}"; if [ -s "{marca}" ]; then echo VISTO; else echo NAO-VISTO; fi'
        pa = subprocess.Popen([BASH, "-c", a], env=c.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        c.esperar_inicios(1)                                          # a A já segura a trava
        pb = subprocess.Popen([BASH, "-c", b], env=c.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        oa, ea = pa.communicate(timeout=120)
        ob, eb = pb.communicate(timeout=120)
        assert pa.returncode == 0, ea[-300:]
        assert ob.strip() == "VISTO", f"quem esperava a trava acordou antes de a proveniência ser gravada: {ob!r} {eb[-200:]}"


def test_prompt_so_e_gravado_por_quem_chamou_o_codex():
    with Cenario(["falha"]) as c:                                          # geração que falha não deixa prompt nem ficha de proveniência
        args, bruto = c.alvo("elementos.sh", "falhou")
        assert c.rodar(args).returncode == 1
        assert not (bruto.parent / "falhou.prompt.txt").exists() and not (bruto.parent / "falhou.meta.json").exists()
    with Cenario(["ok"]) as c:                                             # e a chamada que só ENCONTROU o bruto pronto não grava o prompt dela
        args, bruto = c.alvo("elementos.sh", "achado")
        bruto.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", (96, 96), (5, 5, 5, 5)).save(bruto)               # veio de outra rodada, sem prompt registrado
        r = c.rodar(args)
        assert r.returncode == 0 and c.inicios() == [], r.stderr[-300:]
        assert not (bruto.parent / "achado.prompt.txt").exists(), "gravou um prompt que não gerou este bruto"
        assert json.loads((bruto.parent / "achado.meta.json").read_text())["prompt"] is None


def test_os_documentos_nao_ensinam_a_colar_o_prompt_na_linha_de_comando_do_cena_sh():
    raiz = AQUI.parent
    achados = []
    for arq in [raiz / "SKILL.md", AQUI / "LEIA-ME.md", *sorted((raiz / "references").glob("*.md"))]:
        for n, linha in enumerate(arq.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"cena\.sh\s+(\"[^\"]*\"|\S+)\s+\S+\s+[\"']", linha):         # cena.sh <pasta> <id> "<prompt>"
                achados.append(f"{arq.name}:{n}")
    assert not achados, f"documento que ensina o prompt entre aspas na linha de comando: {achados}"
    texto = (raiz / "SKILL.md").read_text(encoding="utf-8")
    assert "cena.sh \"<pasta>\" c-portico " in texto and "c-portico.prompt.txt" in texto, "o SKILL.md tem de mostrar a chamada nova"


# --------------------------------------------------------------------------------------------- sem Codex, sem Higgsfield
def test_sem_codex_instalado_sai_com_2_e_nao_aponta_outro_fornecedor():
    for script in SCRIPTS:
        with Cenario(["ok"]) as c:
            sem = dict(c.env, PATH="/usr/bin:/bin")
            assert shutil.which("codex", path="/usr/bin:/bin") is None
            args, png = c.alvo(script)
            r = subprocess.run([BASH, str(AQUI / args[0]), *args[1:]], capture_output=True, text=True, env=sem)
            assert r.returncode == 2 and "codex login" in r.stderr and "não troque de fornecedor" in r.stderr, (script, r.returncode, r.stderr)
            assert "higgsfield" not in r.stderr.lower() and not png.exists()


def test_recortar_so_pelo_rembg_local_sem_plano_b():
    with tempfile.TemporaryDirectory() as d:
        entrada = Path(d) / "e.png"
        Image.new("RGB", (32, 32), (200, 100, 50)).save(entrada)
        # rembg ausente (simulado: import bloqueado): para com 2 e diz que o recorte é só pelo rembg local
        # o caminho do script vai por argv, não dentro do código: o cofre mora em "UGO's Second Brain" e o apóstrofo
        # quebrava a string (passava na cópia da frente, que não tem apóstrofo no caminho)
        codigo = ("import sys, runpy; sys.modules['rembg'] = None; script = sys.argv[3]; "
                  "sys.argv = ['recortar.py', sys.argv[1], sys.argv[2], '--classe', 'produto']; "
                  "runpy.run_path(script, run_name='__main__')")
        r = subprocess.run([PY, "-c", codigo, str(entrada), str(Path(d) / "s.png"), str(AQUI / "recortar.py")], capture_output=True, text=True)
        assert r.returncode == 2 and "só pelo rembg local" in r.stderr and "higgsfield" not in r.stderr.lower(), (r.returncode, r.stderr)
        assert not (Path(d) / "s.png").exists()
        # a opção --plano-b não existe mais
        r = subprocess.run([PY, str(AQUI / "recortar.py"), str(entrada), str(Path(d) / "s.png"), "--classe", "produto", "--plano-b"],
                           capture_output=True, text=True)
        assert r.returncode == 2 and "unrecognized arguments: --plano-b" in r.stderr, (r.returncode, r.stderr[-300:])


def test_nenhum_arquivo_do_fluxo_do_codex_cita_o_fornecedor_antigo():
    for nome in ("elementos.sh", "cena.sh", "cena_limpar.sh", "codex_gerar.sh", "recortar.py", "elementos_prompt.py", "cena_prompt.py"):
        texto = (AQUI / nome).read_text(encoding="utf-8")
        assert "higgsfield" not in texto.lower(), f"{nome} ainda cita o Higgsfield"
    print("   0 menções ao Higgsfield nos 7 arquivos do fluxo do Codex")


def test_a_biblioteca_roda_no_bash_do_sistema():
    r = subprocess.run([BASH, "--version"], capture_output=True, text=True)
    print("   " + r.stdout.splitlines()[0])
    for nome in ("codex_gerar.sh", "elementos.sh", "cena.sh", "cena_limpar.sh"):
        assert subprocess.run([BASH, "-n", str(AQUI / nome)]).returncode == 0, nome


# --------------------------------------------------------------------------------------------- descrição por arquivo
PERIGO_DESC = "an orange training cone $(touch PWNED_G) and `touch PWNED_H` and ${HOME} and \"; touch PWNED_I; echo \""
AVISO_LINHA = "veio na linha de comando"


def _com_arquivo(script, args, arq):
    """Os argumentos do alvo com a descrição trocada por --descricao-de <arq> (elementos.sh: sai o 4º; cena_limpar.sh: entra)."""
    return (args[:4] if script == "elementos.sh" else list(args)) + ["--descricao-de", str(arq)]


def test_descricao_por_arquivo_chega_literal_ao_prompt_e_nada_roda():
    for script in ("elementos.sh", "cena_limpar.sh"):
        with Cenario(["ok"]) as c:
            args, png = c.alvo(script, "porarq")
            arq = Path(c.tmp.name) / "descricao.txt"
            arq.write_text(PERIGO_DESC + "\n", encoding="utf-8")
            trabalho = Path(c.tmp.name) / "trabalho"
            trabalho.mkdir()
            r = c.rodar(_com_arquivo(script, args, arq), cwd=trabalho)
            assert r.returncode == 0 and aberto_inteiro(png), (script, r.returncode, r.stderr[-400:])
            assert not [p for p in arvore(c.tmp.name) if "PWNED" in p], f"{script}: o texto do arquivo rodou como comando"
            assert AVISO_LINHA not in r.stderr, (script, r.stderr)
            enviado = c.inicios()[0]["argv"][-1]
            assert PERIGO_DESC in enviado, (script, "o conteúdo do arquivo tinha de chegar ao Codex literal", enviado[:400])
            pasta = png.parent
            assert PERIGO_DESC in (pasta / "porarq.prompt.txt").read_text(encoding="utf-8"), script
            if script == "elementos.sh":
                assert json.loads((pasta / "porarq.meta.json").read_text())["descricao"] == PERIGO_DESC
                assert f"Subject: {PERIGO_DESC}\n" in enviado
    print("   elementos.sh e cena_limpar.sh: $(...), crase, ${HOME} e aspas do arquivo chegaram literais ao Codex; nada rodou")


def test_descricao_na_linha_de_comando_ainda_passa_com_aviso_e_nao_e_expandida():
    texto = "an orange cone $(echo x) and `echo y`"
    for script in ("elementos.sh", "cena_limpar.sh"):
        with Cenario(["ok"]) as c:
            args, png = c.alvo(script, "antiga")
            args = (args[:4] if script == "elementos.sh" else list(args)) + [texto]     # o caminho do script vai por argv, sem shell
            r = c.rodar(args)
            assert r.returncode == 0 and aberto_inteiro(png), (script, r.stderr[-300:])
            assert AVISO_LINHA in r.stderr and "--descricao-de" in r.stderr, (script, r.stderr)
            enviado = c.inicios()[0]["argv"][-1]
            assert texto in enviado and "an orange cone x and y" not in enviado, (script, enviado[:300])


def test_descricao_por_arquivo_recusa_o_que_falta_antes_de_gastar_cota():
    for script in ("elementos.sh", "cena_limpar.sh"):
        with Cenario(["ok"]) as c:
            args, png = c.alvo(script, "falta")
            vazio = Path(c.tmp.name) / "vazio.txt"
            vazio.write_text("  \n\n", encoding="utf-8")
            r = c.rodar(_com_arquivo(script, args, Path(c.tmp.name) / "nao-existe.txt"))
            assert r.returncode == 66 and "nada foi enviado ao Codex" in r.stderr, (script, r.returncode, r.stderr)
            r = c.rodar(_com_arquivo(script, args, vazio))
            assert r.returncode == 66 and "vazia" in r.stderr, (script, r.returncode, r.stderr)
            duas = _com_arquivo(script, args, vazio) + (["outra descrição"] if script == "cena_limpar.sh" else [])
            if script == "elementos.sh":
                duas = args + ["--descricao-de", str(vazio)]                                 # a posicional E o arquivo
            r = c.rodar(duas)
            assert r.returncode == 64 and "dada duas vezes" in r.stderr, (script, r.returncode, r.stderr)
            assert c.inicios() == [] and not png.exists(), f"{script}: nenhum desses casos pode gastar cota"


def test_descricao_pela_entrada_padrao_e_a_forma_com_tipo():
    with Cenario(["ok"]) as c:
        args, png = c.alvo("elementos.sh", "viaentrada")
        r = c.rodar(args[:4] + ["--descricao-de", "-"], entrada="an orange cone\nwith a worn base $(touch PWNED_J)\n")
        assert r.returncode == 0 and aberto_inteiro(png), r.stderr[-300:]
        enviado = c.inicios()[0]["argv"][-1]
        assert "Subject: an orange cone with a worn base $(touch PWNED_J)\n" in enviado, enviado[:500]     # a quebra de linha virou espaço
        assert not [p for p in arvore(c.tmp.name) if "PWNED" in p]
    with Cenario(["ok"]) as c:
        args, png = c.alvo("elementos.sh", "comtipo")
        arq = Path(c.tmp.name) / "d.txt"
        arq.write_text("a gold medal", encoding="utf-8")
        r = c.rodar(args[:3] + ["--tipo", "objeto", "--descricao-de", str(arq)])
        assert r.returncode == 0 and "Subject: a gold medal\n" in c.inicios()[0]["argv"][-1], r.stderr[-300:]


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

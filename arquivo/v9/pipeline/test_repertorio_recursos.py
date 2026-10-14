#!/usr/bin/env python3
"""Provas do repertório v2 (camada de acabamento, plano parte B5) no repertorio.py: anotar, mapa, indexar, checar v2,
buscar --entidade, serie, cobertura, usados com recursos, consultar e html com abas. Rodar:
~/.venvs/mediakit/bin/python test_repertorio_recursos.py. Quase todas usam um repertório SINTÉTICO numa pasta temporária
(o de test_repertorio.py mais um recurso escrito no formato do briefing-redator-v2.md, páginas de gradiente com um objeto
e análises v2 no formato da RUBRICA-v2.md); as últimas conferem o repertório real (o recurso de exemplo do CONEBRA).
Cada prova foi quebrada de propósito (mutante no repertorio.py) e acusou. Terminam em `PROVAS: VERDES`."""
import copy, hashlib, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from urllib.parse import unquote

import numpy as np
from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import repertorio  # noqa: E402
import test_repertorio as base  # noqa: E402

PY = sys.executable
SCRIPT = str(AQUI / "repertorio.py")
RID = "objeto-com-material-cruza-o-titulo"
W_PAG, H_PAG = 1400, 788


def cli(*args, env=None):
    r = subprocess.run([PY, SCRIPT, *map(str, args)], capture_output=True, text=True, env=env)
    return r.returncode, r.stdout, r.stderr


def falhas(res):
    return [m for n, m in res if n == "FALHA"]


def avisos(res):
    return [m for n, m in res if n == "AVISO"]


# ---------------------------------------------------------------- páginas e análises sintéticas
def pagina(caminho, semente, objeto=(0.62, 0.28, 0.86, 0.74), cor=(200, 150, 40), lisa=None):
    """Página 1400x788: gradiente suave (o JPEG preserva sem ruído forte), faixas de tom e um objeto retangular colorido.
    `lisa` = cor única na página inteira (para o recorte vazio)."""
    caminho = Path(caminho); caminho.parent.mkdir(parents=True, exist_ok=True)
    if lisa is not None:
        Image.new("RGB", (W_PAG, H_PAG), lisa).save(caminho, quality=92); return caminho
    r = np.random.RandomState(semente)
    x = np.linspace(0, 1, W_PAG)[None, :, None]; y = np.linspace(0, 1, H_PAG)[:, None, None]
    base_cor = r.randint(40, 200, 3)[None, None, :]
    a = np.clip(base_cor + 60 * x - 40 * y, 0, 255).astype(np.uint8)
    im = Image.fromarray(np.broadcast_to(a, (H_PAG, W_PAG, 3)).copy())
    d = ImageDraw.Draw(im)
    for k in range(6):
        y0 = int(r.randint(0, H_PAG - 40)); d.rectangle([0, y0, W_PAG, y0 + 18], fill=tuple(int(v) for v in r.randint(30, 230, 3)))
    o = objeto
    d.rectangle([o[0] * W_PAG, o[1] * H_PAG, o[2] * W_PAG, o[3] * H_PAG], fill=cor)
    d.ellipse([o[0] * W_PAG + 20, o[1] * H_PAG + 20, o[0] * W_PAG + 90, o[1] * H_PAG + 90], fill=(250, 250, 250))
    im.save(caminho, quality=92)
    return caminho


EIXOS_VAR = [{"eixo": e, "faixa": "faixa de teste", "observado": True} for e in repertorio.EIXOS]


def candidato(pid, exemplos, recurso=("objeto-3d", "sombra"), dimensoes=("profundidade-3d", "uau"), status=None):
    c = {"id_sugerido": pid, "nome": "Candidato de teste", "recurso": list(recurso), "dimensoes": list(dimensoes),
         "familia": dimensoes[0], "exemplos": exemplos, "variavel": EIXOS_VAR}
    if status:
        c["status"] = status
    return c


def exemplo(ref, pag, recorte, anotacoes=None, anti=False, o_que="o objeto passa na frente da linha do título"):
    e = {"imagem": f"capturas/{ref}/{pag:02d}.jpg", "pagina": pag, "recorte": recorte, "o_que_mostra": o_que, "mockup": False,
         "anotacoes": anotacoes if anotacoes is not None else [
             {"n": 1, "caixa": [recorte[0] + 0.05, recorte[1] + 0.05, recorte[0] + 0.15, recorte[1] + 0.2], "rotulo": "sombra de contato de 1,2% da altura"},
             {"n": 2, "caixa": [recorte[0] + 0.1, recorte[3] - 0.2, recorte[2] - 0.05, recorte[3] - 0.05],
              "seta": [recorte[2] - 0.02, recorte[3] - 0.02, recorte[0] + 0.2, recorte[3] - 0.12], "rotulo": "corte na linha de base"}]}
    if anti:
        e["anti"] = True
    return e


def analise(pasta, ref, candidatos, nome=None):
    f = Path(pasta) / (nome or f"{ref}.json")
    f.write_text(json.dumps({"referencia": ref, "camada": "lente", "padroes": candidatos}, ensure_ascii=False), encoding="utf-8")
    return f


# ---------------------------------------------------------------- o recurso sintético (formato do briefing-redator-v2.md)
FRONT = """---
id: {rid}
nome: Objeto com material que cruza o título
efeito: um objeto do esporte, com material e luz declarados, passa na frente de uma linha do título e atrás da outra, e o título ganha espessura de cena sem deixar de ser texto vivo
familia: profundidade-3d
recurso: [objeto-3d, sombra, sobreposicao]
dimensoes: [profundidade-3d, sobreposicao-recorte, tipografia-expressiva, uau]
material: [metal]
luz: direcional
luz_direcao: esq
profundidade: volume
intensidade: [2, 3]
continuidade: unica
borda: [forma]
tipo_pagina: [capa, divisor, divisor_cotas]
funcao: [profundidade, foco]
tom: [performance, festa]
rota: hibrido
producao: misto
risco_pdf: nao-testado
reproduzivel: parcial
uau: 3
padroes: [figura-recortada-atravessa-a-borda]
tratamento_imagem: [natural]
tipografia: [gigante, atras-da-figura]
mistura: [render-3d, tipografia]
uau_gatilhos: [profundidade, material]
eixos: [escala, orientacao, cor, material, densidade, enquadramento, localizacao, relacao-texto, intensidade]
depende: [efeito.cruza no render, sombra de contato pelo tratar.py sombra]
provisorio: true
---
"""


def trecho(rid=RID, ref="ref-um"):
    t = json.loads(base_trecho_json())
    t["direcao_criativa"]["recursos"][0]["id"] = rid
    t["direcao_criativa"]["recursos"][0]["referencia"] = ref
    t["pagina"]["acabamento"]["recursos"] = [rid]
    t["pagina"]["elementos"][0]["recurso"] = rid
    return t


def base_trecho_json():
    """O trecho do briefing-redator-v2.md (a prova test_repertorio_v2.py confere que ele vale no kit)."""
    b = (AQUI.parent / "repertorio" / "estudo" / "briefing-redator-v2.md").read_text(encoding="utf-8")
    b = b[b.find("Trecho de acabamento:"):]
    return re.search(r"```json\n(.*?)\n```", b, re.S).group(1)


def md_recurso(rid=RID, refs=(("ref-um", 5), ("ref-dois", 4)), front=None, secoes=None, trecho_obj=None, comandos=None,
               eixos=None, extra=""):
    secoes = secoes or [f"{k}. {s}" for k, s in enumerate(repertorio.SECOES_RECURSO, 1)]
    eixos = repertorio.EIXOS if eixos is None else eixos
    comandos = comandos or ["elementos.sh <pasta-do-kit> objeto-motivo objeto --descricao-de descricao.txt --material ouro --luz esquerda",
                            "tratar.py sombra <objeto.png> <objeto-sombra.png>"]
    corpo = (front or FRONT.format(rid=rid)) + "\n# Objeto com material que cruza o título\n\n"
    for s in secoes:
        corpo += f"## {s}\n\n"
        if s.startswith("5."):
            corpo += "| Eixo | Faixa que funciona | Onde se viu |\n|---|---|---|\n" + "".join(f"| {e} | faixa de teste | ref-um p. 5 |\n" for e in eixos)
        elif s.startswith("8."):
            corpo += "Via misto, rota híbrido.\n\n```\n" + "\n".join(comandos) + "\n```\n"
        else:
            corpo += "Linha de texto do recurso, com medida e página (ref-um p. 5).\n" * 4
        corpo += "\n"
    corpo += "## Trecho de acabamento\n\n```json\n" + json.dumps(trecho_obj if trecho_obj is not None else trecho(rid), ensure_ascii=False) + "\n```\n\n"
    corpo += "## Referências\n\n"
    for ref, pag in refs:
        corpo += f"- {ref} p. {pag} (o objeto passa na frente da primeira linha; recorte recortes/{rid}__{ref}-{pag:02d}.jpg, anotado: 1 sombra, 2 corte)\n"
    return corpo + extra


SERIE = {"constantes": ["margem de 6% da largura"], "variaveis": ["foto troca de lado"], "por_tipo": {"capa": "foto inteira e título"},
         "ritmo": {"padrao": "blocos", "paginas": {"1": "abertura", "2": "impacto", "3": "respiro"}}}


def montar_v2(raiz):
    """Repertório sintético sadio com 1 recurso: o de test_repertorio.montar, as páginas ref-um p. 5 e ref-dois p. 4, a
    análise de cada uma, o `anotar` delas em recortes/, o .md do recurso e o `indexar --escrever`. Devolve a pasta."""
    raiz = Path(raiz); rep = raiz / "repertorio"
    base.montar(rep)
    ind = json.loads((rep / "indice.json").read_text(encoding="utf-8"))
    for r in ind["referencias"]:
        r["serie"] = copy.deepcopy(SERIE); r["camada_v2"] = "lente"
    (rep / "indice.json").write_text(json.dumps(ind, ensure_ascii=False, indent=1), encoding="utf-8")
    pagina(rep / "capturas" / "ref-um" / "05.jpg", 5)
    pagina(rep / "capturas" / "ref-dois" / "04.jpg", 4, objeto=(0.2, 0.2, 0.5, 0.7), cor=(60, 120, 220))
    an = raiz / "analises"; an.mkdir()
    a1 = analise(an, "ref-um", [candidato(RID, [exemplo("ref-um", 5, [0.55, 0.2, 0.92, 0.8])])])
    a2 = analise(an, "ref-dois", [candidato(RID, [exemplo("ref-dois", 4, [0.15, 0.15, 0.55, 0.75])])])
    for a in (a1, a2):
        r = repertorio.anotar(a, rep / "recortes", todos=True, bases=[rep])
        assert r["feitos"] and not r["problemas"] and not r["avisos"], r
    (rep / "recursos").mkdir()
    (rep / "recursos" / f"{RID}.md").write_text(md_recurso(), encoding="utf-8")
    r = repertorio.indexar(rep, escrever=True)
    assert r["escrito"] and r["novos"] == [RID] and not r["erros_schema"] and not r["problemas"], r
    return rep


_SADIO = {"copias": []}


def sadio():
    """Uma cópia nova do repertório sintético sadio (montado uma vez e copiado: anotar e indexar custam)."""
    if "dir" not in _SADIO:
        _SADIO["dir"] = tempfile.mkdtemp(prefix="rep-v2-")
        montar_v2(_SADIO["dir"])
    d = Path(tempfile.mkdtemp(prefix="rep-v2-caso-"))
    _SADIO["copias"].append(d)
    shutil.copytree(Path(_SADIO["dir"]) / "repertorio", d / "repertorio", symlinks=True)
    return d / "repertorio"


def indice(rep):
    return json.loads((rep / "indice.json").read_text(encoding="utf-8"))


def gravar(rep, ind):
    (rep / "indice.json").write_text(json.dumps(ind, ensure_ascii=False, indent=1), encoding="utf-8")


def md(rep):
    return (rep / "recursos" / f"{RID}.md")


# ================================================================ anotar
def _px(im, x, y):
    return im.getpixel((int(x), int(y)))


def _perto(c, alvo, tol):
    return all(abs(a - b) <= tol for a, b in zip(c, alvo))


def test_anotar_grava_limpo_e_anotado_e_converte_para_fracao_do_recorte():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        pagina(d / "capturas" / "ref-x" / "07.jpg", 7)
        an = [{"n": 1, "caixa": [0.6, 0.3, 0.7, 0.5], "seta": [0.85, 0.7, 0.66, 0.45], "rotulo": "objeto de 24% da largura, medido"},
              {"n": 2, "caixa": [0.55, 0.6, 0.8, 0.75], "rotulo": "sombra de contato sob a base"}]
        a = analise(d, "ref-x", [candidato("objeto-cruza", [exemplo("ref-x", 7, [0.5, 0.2, 0.9, 0.8], an)])])
        r = repertorio.anotar(a, d / "saida", todos=True, bases=[d])
        assert not r["problemas"] and not r["avisos"], r
        f = r["feitos"][0]
        assert f["arquivo"] == "recortes/objeto-cruza__ref-x-07.jpg" and f["anotado"] == "recortes/objeto-cruza__ref-x-07--anotado.jpg", f
        # o recorte limpo é o do `recortar` (folga de 3%, sem ampliar): 644x520 px
        px0, py0, px1, py1 = round(0.47 * W_PAG), round(0.17 * H_PAG), round(0.93 * W_PAG), round(0.83 * H_PAG)
        limpo = Image.open(d / "saida" / "objeto-cruza__ref-x-07.jpg").convert("RGB")
        assert limpo.size == (px1 - px0, py1 - py0) == tuple(f["tamanho"]), (limpo.size, f["tamanho"])
        # as anotações vão da fração da página para a fração do recorte (conta feita aqui à parte)
        cw, ch = px1 - px0, py1 - py0
        conv = lambda c: [round((c[0] * W_PAG - px0) / cw, 4), round((c[1] * H_PAG - py0) / ch, 4), round((c[2] * W_PAG - px0) / cw, 4), round((c[3] * H_PAG - py0) / ch, 4)]  # noqa: E731
        assert [x["caixa"] for x in f["anotacoes"]] == [conv(an[0]["caixa"]), conv(an[1]["caixa"])], f["anotacoes"]
        assert f["anotacoes"][0]["seta"] == conv(an[0]["seta"]) and "seta" not in f["anotacoes"][1]
        assert f["recorte_pagina"] == [round(px0 / W_PAG, 4), round(py0 / H_PAG, 4), round(px1 / W_PAG, 4), round(py1 / H_PAG, 4)]
        man = json.loads((d / "saida" / "_anotar-ref-x.json").read_text(encoding="utf-8"))
        assert [e["arquivo"] for e in man["recortes"]] == [f["arquivo"]] and man["recortes"][0]["anotacoes"] == f["anotacoes"]
        # a figura anotada: a peça no topo, a faixa de legenda abaixo (mais alta), largura mínima de 640 px
        fig = Image.open(d / "saida" / "objeto-cruza__ref-x-07--anotado.jpg").convert("RGB")
        assert fig.width == max(cw, 640) and fig.height > ch + 60, fig.size
        # caixa: amarelo #FFD400 no meio, escuro por fora e por dentro (borda esquerda da caixa 1, na altura do meio)
        cx0, cy0, cx1, cy1 = [v * s for v, s in zip(f["anotacoes"][0]["caixa"], (cw, ch, cw, ch))]
        ym = (cy0 + cy1) / 2 + 30
        assert _perto(_px(fig, cx0 - 1, ym), repertorio.AMARELO, 45), _px(fig, cx0 - 1, ym)
        assert max(_px(fig, cx0 - 4, ym)) < 70 and max(_px(fig, cx0 + 2, ym)) < 70, (_px(fig, cx0 - 4, ym), _px(fig, cx0 + 2, ym))
        # disco numerado de 30 px no canto da caixa: amarelo no centro deslocado do número
        assert _perto(_px(fig, cx0 + 9, cy0 - 9), repertorio.AMARELO, 45) or _perto(_px(fig, cx0 - 9, cy0 + 9), repertorio.AMARELO, 45)
        # o rótulo vai na faixa ABAIXO, nunca sobre a peça: fora das caixas, da seta e dos discos a peça é a mesma do recorte limpo
        a_fig = np.asarray(fig, dtype=np.int16)[:ch, :cw]; a_limpo = np.asarray(limpo, dtype=np.int16)
        livre = np.ones((ch, cw), bool)
        for x in f["anotacoes"]:
            b = [int(v * s) for v, s in zip(x["caixa"], (cw, ch, cw, ch))]
            livre[max(0, b[1] - 26):b[3] + 10, max(0, b[0] - 26):b[2] + 10] = False
            if "seta" in x:
                s = [int(v * k) for v, k in zip(x["seta"], (cw, ch, cw, ch))]
                livre[max(0, min(s[1], s[3]) - 22):max(s[1], s[3]) + 22, max(0, min(s[0], s[2]) - 22):max(s[0], s[2]) + 22] = False
        dif = np.abs(a_fig - a_limpo).max(axis=2)[livre]
        assert (dif > 90).sum() < 30, f"{(dif > 90).sum()} pixels mudaram fora das marcas: texto sobre a peça?"
        # a faixa tem texto claro (o rótulo) e o cabeçalho com a referência e a página
        faixa = np.asarray(fig.convert("L"))[ch + 10:, :]
        assert (faixa > 200).sum() > 400, "a faixa de legenda está vazia"
        print(f"   recorte {cw}x{ch}, figura {fig.width}x{fig.height}; {(dif > 90).sum()} pixels da peça mexidos fora das marcas")


def test_anotar_pega_so_os_aceitos_e_todos_com_a_opcao():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        pagina(d / "capturas" / "ref-x" / "03.jpg", 3)
        ex = lambda: [exemplo("ref-x", 3, [0.4, 0.2, 0.9, 0.8])]  # noqa: E731
        a = analise(d, "ref-x", [candidato("aceito-um", ex(), status="aceito"), candidato("sem-veredito", ex())])
        r = repertorio.anotar(a, d / "s1", bases=[d])
        assert [f["candidato"] for f in r["feitos"]] == ["aceito-um"] and not r["problemas"], r
        r = repertorio.anotar(a, d / "s2", todos=True, bases=[d])
        assert sorted(f["candidato"] for f in r["feitos"]) == ["aceito-um", "sem-veredito"], r
        # o <ref>.aceitos.json do gravar_veredito.py: entram os aceitos (refutados só com --todos)
        (d / "ref-x.aceitos.json").write_text(json.dumps({"id": "ref-x", "aceitos": [dict(candidato("do-veredito", ex()), referencia="ref-x")],
                                                          "refutados": [candidato("caiu", ex())]}), encoding="utf-8")
        r = repertorio.anotar(d / "ref-x.aceitos.json", d / "s3", bases=[d])
        assert [f["candidato"] for f in r["feitos"]] == ["do-veredito"] and r["referencia"] == "ref-x", r
        a2 = analise(d, "ref-x", [candidato("sem-veredito", ex())], nome="so-sem.json")
        r = repertorio.anotar(a2, d / "s4", bases=[d])
        assert not r["feitos"] and "use --todos" in r["problemas"][0], r
        codigo, out, _ = cli("anotar", a2, "--saida", d / "s5", "--base-imagens", d)
        assert codigo == 1 and "FALHA" in out and "--todos" in out, out
        codigo, out, _ = cli("anotar", a2, "--saida", d / "s5", "--base-imagens", d, "--todos")
        assert codigo == 0 and "sem-veredito__ref-x-03--anotado.jpg" in out, out


def test_anotar_avisa_recorte_vazio_grande_pequeno_liso_e_repetido():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        pagina(d / "capturas" / "ref-x" / "01.jpg", 1)
        pagina(d / "capturas" / "ref-x" / "02.jpg", 1)                       # a mesma página: recorte repetido
        pagina(d / "capturas" / "ref-x" / "03.jpg", 3, lisa=(120, 120, 120))
        pagina(d / "capturas" / "ref-x" / "04.jpg", 4)
        cands = [candidato("detalhe-grande", [exemplo("ref-x", 4, [0.0, 0.0, 1.0, 1.0])]),
                 candidato("textura-grande", [exemplo("ref-x", 4, [0.0, 0.0, 1.0, 1.0])], recurso=("textura",), dimensoes=("pattern-textura",)),
                 candidato("pequeno", [exemplo("ref-x", 4, [0.5, 0.5, 0.52, 0.52], anotacoes=[{"n": 1, "caixa": [0.5, 0.5, 0.52, 0.52], "rotulo": "x y z"}])]),
                 candidato("liso", [exemplo("ref-x", 3, [0.2, 0.2, 0.6, 0.6])]),
                 candidato("repete-a", [exemplo("ref-x", 1, [0.4, 0.1, 0.9, 0.7])]),
                 candidato("repete-b", [exemplo("ref-x", 2, [0.4, 0.1, 0.9, 0.7])]),
                 candidato("sadio", [exemplo("ref-x", 4, [0.55, 0.2, 0.92, 0.8])])]
        r = repertorio.anotar(analise(d, "ref-x", cands), d / "s", todos=True, bases=[d])
        por = {}
        for a in r["avisos"]:
            por.setdefault(a.split("__")[0].replace("recortes/", ""), []).append(a)
        assert any("acima de 85%" in a for a in por.get("detalhe-grande", [])), por
        assert not any("85%" in a for a in por.get("textura-grande", [])), por            # recurso de página: o recorte grande é certo
        assert any("abaixo de 2%" in a for a in por.get("pequeno", [])), por
        assert any("desvio de luminância" in a for a in por.get("liso", [])), por
        assert any("recorte repetido" in a and "repete-a" in a for a in por.get("repete-b", [])), por
        assert "sadio" not in por, por["sadio"]
        print(f"   {len(r['avisos'])} avisos em 7 candidatos; o sadio e a textura de página inteira passam")


def test_anotar_nao_apaga_recorte_de_outra_origem_e_refaz_o_proprio():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        pagina(d / "capturas" / "ref-x" / "05.jpg", 5)
        a = analise(d, "ref-x", [candidato("mesmo-id", [exemplo("ref-x", 5, [0.5, 0.2, 0.9, 0.8])])], nome="a.json")
        b = analise(d, "ref-x", [candidato("mesmo-id", [exemplo("ref-x", 5, [0.1, 0.1, 0.5, 0.6])])], nome="b.json")
        assert repertorio.anotar(a, d / "s", todos=True, bases=[d])["feitos"][0]["arquivo"].endswith("mesmo-id__ref-x-05.jpg")
        sha = hashlib.sha256((d / "s" / "mesmo-id__ref-x-05.jpg").read_bytes()).hexdigest()
        rb = repertorio.anotar(b, d / "s", todos=True, bases=[d])
        assert rb["feitos"][0]["arquivo"].endswith("mesmo-id__ref-x-05-b.jpg"), rb["feitos"][0]["arquivo"]
        assert hashlib.sha256((d / "s" / "mesmo-id__ref-x-05.jpg").read_bytes()).hexdigest() == sha, "o recorte da outra análise foi sobrescrito"
        ra = repertorio.anotar(a, d / "s", todos=True, bases=[d])          # refazer a mesma análise reescreve o mesmo arquivo
        assert ra["feitos"][0]["arquivo"].endswith("mesmo-id__ref-x-05.jpg")
        man = json.loads((d / "s" / "_anotar-ref-x.json").read_text(encoding="utf-8"))
        assert sorted(e["arquivo"] for e in man["recortes"]) == ["recortes/mesmo-id__ref-x-05-b.jpg", "recortes/mesmo-id__ref-x-05.jpg"]


def test_mapa_marca_os_recortes_na_pagina_inteira_em_1200_px():
    rep = sadio()
    destino, n = repertorio.mapa(rep, "ref-um", 5)
    assert destino == rep / "mapas" / "ref-um-05.jpg" and n == 1, (destino, n)
    im = Image.open(destino).convert("RGB")
    assert im.width == 1200 and im.height > round(H_PAG * 1200 / W_PAG), im.size
    e = json.loads((rep / "recortes" / "_anotar-ref-um.json").read_text(encoding="utf-8"))["recortes"][0]
    x0 = e["recorte_pagina"][0] * 1200; ym = (e["recorte_pagina"][1] + e["recorte_pagina"][3]) / 2 * im.width * H_PAG / W_PAG
    assert _perto(im.getpixel((int(x0) - 1, int(ym))), repertorio.AMARELO, 45), im.getpixel((int(x0) - 1, int(ym)))
    # com a análise, entram também os exemplos dela daquela página
    with tempfile.TemporaryDirectory() as d:
        a = analise(d, "ref-um", [candidato("outro", [exemplo("ref-um", 5, [0.05, 0.05, 0.3, 0.4])])])
        _, n2 = repertorio.mapa(rep, "ref-um", 5, [a], Path(d) / "m.jpg")
        assert n2 == 2
    codigo, out, err = cli("mapa", "ref-um", "9", "--repertorio", rep)
    assert codigo != 0 and "não encontrada" in (out + err), (out, err)
    codigo, out, _ = cli("mapa", "ref-um", "5", "--repertorio", rep)
    assert codigo == 0 and "ref-um-05.jpg" in out, out


# ================================================================ recurso, indexar e checar
def test_recurso_sadio_indexa_e_checar_da_zero_falha_e_zero_aviso():
    rep = sadio()
    ind = indice(rep)
    assert ind["versao"] == 2 and [r["id"] for r in ind["recursos"]] == [RID], ind.get("recursos")
    r = ind["recursos"][0]
    assert "provisorio" not in r and r["arquivo"] == f"recursos/{RID}.md" and r["intensidade"] == [2, 3] and r["uau"] == 3
    assert r["acabamento_exemplo"] == trecho() and [x["arquivo"] for x in r["recortes"]] == [
        f"recortes/{RID}__ref-um-05.jpg", f"recortes/{RID}__ref-dois-04.jpg"]
    for x in r["recortes"]:
        assert x["anotado"] == x["arquivo"][:-4] + "--anotado.jpg" and (rep / x["anotado"]).is_file() and len(x["anotacoes"]) == 2, x
    assert repertorio.validar_indice(ind) == [], repertorio.validar_indice(ind)[:3]
    res = repertorio.checar(rep)          # o único aviso é o do padrão sintético sem recorte, que já vinha do v1
    assert res == [("AVISO", "padrão `selo-na-margem` sem recorte (a folha e o html ficam sem imagem)")], res
    codigo, out, _ = cli("checar", "--repertorio", rep)
    assert codigo == 0 and "0 falha(s), 1 aviso(s)" in out, out
    # o índice já igual aos .md: indexar não muda nada
    assert repertorio.indexar(rep, escrever=True)["escrito"] is False


def _caso(mudar, reindexar=False):
    rep = sadio()
    mudar(rep)
    if reindexar:
        repertorio.indexar(rep, escrever=True)
    return repertorio.checar(rep)


def _troca_md(antes, depois, vezes=1):
    def f(rep):
        t = md(rep).read_text(encoding="utf-8"); assert antes in t, antes
        md(rep).write_text(t.replace(antes, depois, vezes), encoding="utf-8")
    return f


def _muda_indice(fn):
    def f(rep):
        ind = indice(rep); fn(ind); gravar(rep, ind)
    return f


def test_checar_v2_acusa_cada_falha_do_contrato():
    casos = {
        "`luz` do .md": (_troca_md("luz: direcional", "luz: difusa"), False),
        "trecho de acabamento:": (_troca_md('"motivo": "motivo-principal", "camada": "atras"', '"camada": "atras"'), True),
        "não existe no pipeline": (_troca_md("tratar.py sombra <objeto.png>", "blender.py render <objeto.png>"), True),
        "não tem o subcomando": (_troca_md("tratar.py sombra <objeto.png>", "tratar.py derreter <objeto.png>"), True),
        "versão anotada `recortes/": (lambda rep: (rep / "recortes" / f"{RID}__ref-um-05--anotado.jpg").unlink(), False),
        "fora do recorte ou invertida": (_muda_indice(lambda i: i["recursos"][0]["recortes"][0]["anotacoes"][0].__setitem__("caixa", [0.5, 0.1, 0.4, 0.3])), False),
        "travessão": (_troca_md("Linha de texto do recurso", "Linha \u2014 de texto do recurso"), True),
        "sem recorte": (_troca_md("recorte recortes/", "sem arquivo ", -1), True),
        "is not one of": (_muda_indice(lambda i: i["recursos"][0].__setitem__("luz", "neon")), False),
        "falta a seção `## 4. Condições`": (_troca_md("## 4. Condições", "## 4. Quando usar"), True),
        "sem versão anotada": (_muda_indice(lambda i: i["recursos"][0]["recortes"][0].pop("anotado")), False),
        "não corresponde à producao": (_troca_md("rota: hibrido", "rota: codigo"), True),
        "fora do padrão de nome": (_troca_md(f"recortes/{RID}__ref-um-05.jpg", "recortes/outro__ref-um-05.jpg"), True),
        "a familia `profundidade-3d` precisa estar em dimensoes": (_troca_md("dimensoes: [profundidade-3d, ", "dimensoes: ["), True),
    }
    for trecho_msg, (mudar, reindexar) in casos.items():
        f = falhas(_caso(mudar, reindexar))
        assert any(trecho_msg in m for m in f), (trecho_msg, f)
    print(f"   {len(casos)} defeitos plantados, cada um com a sua FALHA")


def test_checar_v2_avisa_o_que_o_briefing_pede():
    def padrao_divide(rep):
        ind = indice(rep)
        p = next(p for p in ind["padroes"] if p["id"] == "numero-que-sangra")
        for x, (ref, pag) in zip(p["recortes"], (("ref-um", 5), ("ref-dois", 4))):
            x["referencia"], x["pagina"] = ref, pag
        gravar(rep, ind)

    casos = {
        "com uma referência só": (_troca_md(f"- ref-dois p. 4 (o objeto passa na frente da primeira linha; recorte recortes/{RID}__ref-dois-04.jpg, anotado: 1 sombra, 2 corte)\n", ""), True),
        "faltam eixos na tabela da seção 5: densidade": (_troca_md("| densidade | faixa de teste | ref-um p. 5 |\n", ""), True),
        "sem `depende`": (_troca_md("depende: [efeito.cruza no render, sombra de contato pelo tratar.py sombra]\n", ""), True),
        "sem `serie`": (_muda_indice(lambda i: i["referencias"][1].pop("serie")), False),
        "é extensão do padrão": (padrao_divide, False),
        "linhas (o briefing pede": (_troca_md("## Trecho de acabamento", "\n".join(["linha"] * 30) + "\n\n## Trecho de acabamento"), True),
        "não está no índice (rode": (lambda rep: shutil.copy(md(rep), rep / "recursos" / "copia-solta.md"), False),
    }
    for trecho_msg, (mudar, reindexar) in casos.items():
        res = _caso(mudar, reindexar)
        assert any(trecho_msg in m for m in avisos(res)), (trecho_msg, res)
    print(f"   {len(casos)} avisos plantados, cada um acusado")


def test_conferir_trecho_anda_junto_com_a_referencia_do_estudo():
    import test_repertorio_v2 as ref
    fm = ref.front_do_briefing()
    t0 = ref.trecho_do_briefing()
    mutantes = {"sem motivo": lambda t: t["pagina"]["elementos"][1].pop("motivo"),
                "tres acabamentos": lambda t: t["pagina"]["elementos"].append(dict(copy.deepcopy(t["pagina"]["elementos"][1]), id="eco-2")),
                "id trocado": lambda t: t["direcao_criativa"]["recursos"][0].__setitem__("id", "outro"),
                "intensidade fora": lambda t: t["pagina"]["acabamento"].__setitem__("intensidade", 1),
                "luz": lambda t: t["pagina"]["acabamento"].__setitem__("luz", "dir"),
                "profundidade": lambda t: t["pagina"]["acabamento"].__setitem__("profundidade", "camadas"),
                "sem recurso no elemento": lambda t: t["pagina"]["elementos"][0].pop("recurso"),
                "dc fora do schema": lambda t: t["direcao_criativa"]["recursos"][0].__setitem__("rota", "codex")}
    assert repertorio.conferir_trecho_acabamento(fm, t0) == ([], []) and ref.conferir_trecho(fm, t0) == []
    for nome, f in mutantes.items():
        t = copy.deepcopy(t0); f(t)
        nosso, deles = repertorio.conferir_trecho_acabamento(fm, t)[0], ref.conferir_trecho(fm, t)
        assert bool(nosso) and bool(deles), (nome, nosso, deles)
    t = copy.deepcopy(t0); t["pagina"]["elementos"][1]["grafismo"]["tipo"] = "inventado"
    assert any("desconhecido" in e for e in repertorio.conferir_trecho_acabamento(fm, t)[0])
    print(f"   {len(mutantes)} mutantes: o repertorio.py e a referência do estudo reprovam juntos")


def test_comando_existe_so_aceita_script_e_subcomando_do_pipeline():
    assert repertorio.comando_existe("tratar.py sombra a.png b.png")[0]
    assert repertorio.comando_existe("python pipeline/tratar.py grao a.jpg")[0]
    assert repertorio.comando_existe("ELEMENTOS_DRY=1 bash elementos.sh kit id objeto --descricao-de x.txt")[0]
    assert repertorio.comando_existe("repertorio.py anotar a.json --saida recortes")[0]
    assert not repertorio.comando_existe("tratar.py derreter a.png")[0]
    assert not repertorio.comando_existe("blender.py render")[0]
    assert not repertorio.comando_existe("../fora.py x")[0]
    assert not repertorio.comando_existe("tratar.py")[0]


# ================================================================ buscar v2
def _rec(rid, **kw):
    r = {"id": rid, "nome": f"Recurso {rid}", "arquivo": f"recursos/{rid}.md", "efeito": "efeito de teste do recurso", "familia": "profundidade-3d",
         "recurso": ["objeto-3d"], "dimensoes": ["profundidade-3d"], "material": ["chapado"], "luz": "nenhuma", "luz_direcao": "nenhuma",
         "profundidade": "plana", "intensidade": [1, 2], "continuidade": "unica", "borda": ["reta"], "tipo_pagina": ["cota"], "funcao": ["foco"],
         "tom": ["causa"], "rota": "codigo", "producao": "codigo-svg-css", "risco_pdf": "nao-testado", "reproduzivel": "sim", "uau": 1, "padroes": []}
    r.update(kw)
    return r


def _rep_busca(d):
    rep = Path(d) / "repertorio"; base.montar(rep)
    ind = indice(rep); ind["versao"] = 2
    ind["recursos"] = [
        _rec("medalha-com-luz", tipo_pagina=["capa", "cota"], dimensoes=["profundidade-3d", "uau"], material=["metal"], luz="direcional",
             intensidade=[2, 3], producao="codex-objeto", rota="imagem", uau=3, tom=["performance"], efeito="a medalha de metal brilha no número"),
        _rec("grao-de-impressao", familia="pattern-textura", recurso=["textura"], dimensoes=["pattern-textura"], material=["impressao"],
             risco_pdf="nenhum", tipo_pagina=["publico"], uau=2),
        _rec("faixa-que-atravessa", familia="acabamento-borda", recurso=["faixa"], dimensoes=["acabamento-borda", "continuidade"],
             continuidade="atravessa", tipo_pagina=["capa", "divisor"], tom=["performance"])]
    gravar(rep, ind)
    return rep


def test_buscar_recursos_pesos_cortes_e_ordem():
    with tempfile.TemporaryDirectory() as d:
        rep = _rep_busca(d); ind = repertorio.carregar(rep)
        ids = lambda r: [x["recurso"]["id"] for x in r]  # noqa: E731
        notas = lambda r: [x["nota"] for x in r]         # noqa: E731
        # página +3, dimensão +2, recurso +2, material +1, luz +1: a medalha 9, a faixa 3 (página)
        r = repertorio.buscar_recursos(ind, pagina="capa", filtros={"dimensao": ["profundidade-3d"], "recurso": ["objeto-3d"], "material": ["metal"], "luz": ["direcional"]})
        assert ids(r) == ["medalha-com-luz", "faixa-que-atravessa"] and notas(r) == [9, 3], (ids(r), notas(r))
        assert r[0]["razoes"] == ["página capa", "dimensão profundidade-3d", "recurso objeto-3d", "material metal", "luz direcional"], r[0]["razoes"]
        # intensidade casa dentro de [mín, máx]; continuidade, via, tom e função +1
        assert ids(repertorio.buscar_recursos(ind, filtros={"intensidade": ["3"]})) == ["medalha-com-luz"]
        r = repertorio.buscar_recursos(ind, filtros={"continuidade": ["atravessa"], "via": ["codigo-svg-css"]}, tons=["performance"])
        assert ids(r) == ["faixa-que-atravessa", "grao-de-impressao", "medalha-com-luz"] and notas(r) == [3, 1, 1], (ids(r), notas(r))
        # cortes: só sem risco no PDF, uau mínimo
        assert ids(repertorio.buscar_recursos(ind, sem_risco_pdf=True, n=0)) == ["grao-de-impressao"]
        assert ids(repertorio.buscar_recursos(ind, uau_min=2, n=0)) == ["grao-de-impressao", "medalha-com-luz"]
        # palavras do problema no efeito e no nome
        r = repertorio.buscar_recursos(ind, problema="medalha de metal")
        assert ids(r) == ["medalha-com-luz"] and notas(r) == [3], (ids(r), notas(r), r[0]["razoes"])
        # todos: padrões e recursos pela mesma nota; corte de recurso tira os padrões; relação só traz padrão
        t = repertorio.buscar_todos(ind, pagina="capa", n=0)
        assert [(x["entidade"], (x.get("padrao") or x.get("recurso"))["id"]) for x in t] == [
            ("recurso", "faixa-que-atravessa"), ("padrao", "fio-que-liga-titulo-e-foto"), ("recurso", "medalha-com-luz")], t
        assert all(x["entidade"] == "recurso" for x in repertorio.buscar_todos(ind, pagina="capa", uau_min=0, n=0))
        assert all(x["entidade"] == "padrao" for x in repertorio.buscar_todos(ind, relacoes=["liga"], n=0))
        assert all(x["entidade"] == "recurso" for x in repertorio.buscar_todos(ind, filtros={"material": ["metal"]}, n=0))


def test_buscar_cli_entidade_padrao_e_igual_a_de_antes_e_v2_e_deterministico():
    with tempfile.TemporaryDirectory() as d:
        rep = _rep_busca(d)
        for args in (("--pagina", "publico"), ("--funcao", "conexao,foco", "--relacao", "alinha", "--json"), ("-n", "0"), ("--problema", "título e foto")):
            a = cli("buscar", "--repertorio", rep, *args); b = cli("buscar", "--repertorio", rep, *args, "--entidade", "padrao")
            assert a == b and a[0] == 0, (args, a, b)
        # o formato de antes, letra por letra: sem etiqueta de entidade, sem chave nova no JSON, mesmo com recursos no índice
        out = cli("buscar", "--repertorio", rep, "--pagina", "publico")[1].splitlines()
        assert out[0] == f" 1. {'numero-que-sangra':<44} Número que sangra e vira fundo  (nota 3: página publico)", out[0]
        assert out[1] == "      página de dados com um número dominante" and out[2].endswith("padroes/numero-que-sangra.md  (2 recorte(s))"), out
        assert list(json.loads(cli("buscar", "--repertorio", rep, "--pagina", "publico", "--json")[1])[0]) == [
            "n", "id", "nome", "nota", "razoes", "problema", "arquivo", "tipo_pagina", "funcao", "relacao", "rota", "tom", "densidade", "recortes"]
        saidas = []
        for semente in ("1", "2", "777"):
            r = cli("buscar", "--repertorio", rep, "--entidade", "todos", "--pagina", "capa", "--material", "metal", "--json", "-n", "0",
                    env=dict(os.environ, PYTHONHASHSEED=semente))
            assert r[0] == 0, r
            saidas.append(r[1])
        assert saidas[0] == saidas[1] == saidas[2]
        dados = json.loads(saidas[0])
        assert dados[0]["entidade"] == "recurso" and dados[0]["id"] == "medalha-com-luz" and dados[0]["nota"] == 4, dados[0]
        codigo, out, _ = cli("buscar", "--repertorio", rep, "--entidade", "recurso", "--sem-risco-pdf")
        assert codigo == 0 and "grao-de-impressao" in out and "medalha" not in out and "recurso " in out, out
        codigo, out, err = cli("buscar", "--repertorio", rep, "--material", "aco", "--entidade", "recurso")
        assert codigo != 0 and "material `aco` não existe" in (out + err), (out, err)
        codigo, out, err = cli("buscar", "--repertorio", rep, "--material", "metal")
        assert codigo != 0 and "vale só com --entidade recurso ou todos" in (out + err), (out, err)
        codigo, out, err = cli("buscar", "--repertorio", rep, "--entidade", "recurso", "--relacao", "liga")
        assert codigo != 0 and "--relacao vale só para padrões" in (out + err), (out, err)
        # dimensão também ranqueia padrão (o padrão v2 que declara dimensoes)
        ind = indice(rep); next(p for p in ind["padroes"] if p["id"] == "selo-na-margem")["dimensoes"] = ["acabamento-borda"]; gravar(rep, ind)
        codigo, out, _ = cli("buscar", "--repertorio", rep, "--dimensao", "acabamento-borda")
        assert codigo == 0 and "selo-na-margem" in out and "dimensão acabamento-borda" in out and "faixa-que" not in out, out


# ================================================================ série, cobertura e usados
def test_serie_do_indice_ou_da_analise_e_cobertura_marca_as_ralas():
    rep = sadio()
    itens = repertorio.serie(rep, "ref-um")
    assert len(itens) == 1 and itens[0]["origem"] == "indice.json" and itens[0]["serie"]["ritmo"]["padrao"] == "blocos"
    codigo, out, _ = cli("serie", "ref-um", "--repertorio", rep)
    assert codigo == 0 and "ritmo: blocos" in out and "01 abertura · 02 impacto · 03 respiro" in out and "margem de 6% da largura" in out, out
    ind = indice(rep); ind["referencias"][0].pop("serie"); gravar(rep, ind)
    (rep / "estudo" / "analise-v2").mkdir(parents=True)
    (rep / "estudo" / "analise-v2" / "ref-um.A.json").write_text(json.dumps({"serie": SERIE, "uau_paginas": [{"pagina": 2, "nota": 2, "gatilhos": ["cor"]}]}), encoding="utf-8")
    itens = repertorio.serie(rep, "ref-um")
    assert [i["origem"] for i in itens] == ["estudo/analise-v2/ref-um.A.json"], itens
    assert cli("serie", "ref-inexistente", "--repertorio", rep)[0] == 1
    c = repertorio.cobertura(indice(rep))
    linha = {l["dimensao"]: l for l in c["linhas"]}
    assert len(c["linhas"]) == 11 and linha["profundidade-3d"]["recursos"] == [RID] and linha["profundidade-3d"]["referencias"] == ["ref-dois", "ref-um"]
    assert linha["profundidade-3d"]["rala"] and linha["ritmo"]["recursos"] == [] and set(c["ralas"]) == set(repertorio.voc("dimensao"))
    codigo, out, _ = cli("cobertura", "--repertorio", rep)
    assert codigo == 0 and "RALA" in out and RID in out, out


def test_usados_lista_padroes_e_recursos_do_kit():
    rep = sadio()
    with tempfile.TemporaryDirectory() as d:
        kit = Path(d)
        k = {"kit": "teste", "direcao_criativa": {"recursos": [{"id": RID}, {"id": "so-na-direcao"}]},
             "composicao": {"capa": {"padroes": ["fio-que-liga-titulo-e-foto"], "acabamento": {"recursos": [RID]}},
                            "cota:Master": {"elementos": [{"id": "x", "recurso": "recurso-fantasma"}]}, "_nota": {"acabamento": {"recursos": ["ignorado"]}}}}
        (kit / "mediakit.json").write_text(json.dumps(k), encoding="utf-8")
        r = repertorio.usados(kit, rep)
        assert r["padroes"] == {"fio-que-liga-titulo-e-foto": ["capa"]}
        assert r["recursos"] == {RID: ["capa"], "recurso-fantasma": ["cota:Master"], "so-na-direcao": []}, r["recursos"]
        assert r["recursos_desconhecidos"] == ["recurso-fantasma", "so-na-direcao"], r
        codigo, out, _ = cli("usados", kit, "--repertorio", rep)
        assert codigo == 0 and "recursos:" in out and "(só na direção criativa)" in out and "recurso-fantasma" in out, out
        (kit / "mediakit.json").write_text(json.dumps({"composicao": {"capa": {"padroes": ["x"]}}}), encoding="utf-8")
        assert "recursos:" not in cli("usados", kit, "--repertorio", rep)[1]          # kit sem recurso: a saída de antes


# ================================================================ consultar
def test_consultar_grava_a_consulta_que_o_qa_le_e_a_folha():
    import qa_conjunto
    rep = sadio()
    with tempfile.TemporaryDirectory() as d:
        kit = Path(d) / "kit"; kit.mkdir()
        k = {"schema_version": "mk-2.1", "cliente": "Cliente Novo", "evento": {"nome": "Copa Nova"}, "paginas": ["capa", "ativo", "cota"],
             "direcao_criativa": {"consulta": "consulta-repertorio.json", "recursos": []}}
        (kit / "mediakit.json").write_text(json.dumps(k), encoding="utf-8")
        (kit / "direcao-criativa.md").write_text("# Direção criativa\n\n## Leitura\n\n- o objeto cruza o título: profundidade\n"
                                                 "- tom de performance, sem enfeite\n- a cota é dita pelo material\n- o campo some atrás\n"
                                                 "- quinta linha que não entra\n\n## Escolha\n\n- nada\n", encoding="utf-8")
        hist = Path(d) / "hist.json"
        hist.write_text(json.dumps([{"id": "kit-velho", "data": "2026-01-01", "cliente": "Outro Cliente", "recursos": [{"id": RID, "referencia": "ref-um"}]}]), encoding="utf-8")
        r = repertorio.consultar(kit, rep, hist)
        gravado = json.loads((kit / "consulta-repertorio.json").read_text(encoding="utf-8"))
        assert gravado["indice_sha256"] == hashlib.sha256((rep / "indice.json").read_bytes()).hexdigest() and gravado == json.loads(json.dumps(r))
        assert gravado["leitura"]["fonte"] == "direcao-criativa.md (seção Leitura)" and len(gravado["leitura"]["linhas"]) == 4
        assert gravado["tipos_pagina"] == ["capa", "ativo_painel", "ativo_topo", "cota"] and gravado["tons"] == ["performance"]
        assert [c["familia"] for c in gravado["consultas"]] == list(repertorio.voc("familia")) and gravado["ids"] == [RID]
        res = next(c for c in gravado["consultas"] if c["familia"] == "profundidade-3d")["resultados"][0]
        assert res["recente"] == "kit-velho" and any("-2" in x for x in res["razoes"]) and any(x.startswith("página capa") for x in res["razoes"]), res
        assert Image.open(kit / "mood" / "consulta-recursos.png").size[0] > 300
        # o QA do kit mk-2.1 lê esse arquivo e o sha256 do índice: nenhuma linha
        assert qa_conjunto.checar_consulta(kit, k, rep / "indice.json") == [], qa_conjunto.checar_consulta(kit, k, rep / "indice.json")
        # sem direcao-criativa.md: o direcao-de-arte.md (primeiras linhas); sem histórico, nada recente
        (kit / "direcao-criativa.md").unlink()
        (kit / "direcao-de-arte.md").write_text("# Direção de arte\n\n**Direção sugerida: festa** (amarelo).\n\n**Ideia central:** a copa da família.\n", encoding="utf-8")
        r = repertorio.consultar(kit, rep, Path(d) / "nao-existe.json")
        assert r["leitura"]["fonte"].startswith("direcao-de-arte.md (sem seção Leitura") and r["tons"] == ["festa"] and r["historico"]["recursos_recentes"] == {}
        codigo, out, _ = cli("consultar", kit, "--repertorio", rep, "--historico", hist)
        assert codigo == 0 and "consulta-repertorio.json" in out and "profundidade-3d" in out, out
        # índice v1 (sem recursos): a consulta sai vazia, com aviso, e o arquivo existe mesmo assim
        with tempfile.TemporaryDirectory() as d2:
            rep1 = Path(d2) / "repertorio"; base.montar(rep1)
            r = repertorio.consultar(kit, rep1, hist)
            assert r["ids"] == [] and "versão 1" in r["aviso"] and (kit / "mood" / "consulta-recursos.png").is_file()


# ================================================================ html v2
def test_html_v2_tem_abas_filtros_selo_e_figura_anotada_que_alterna_para_a_limpa():
    rep = sadio()
    saida = rep / "repertorio.html"
    repertorio.gerar_html(rep, saida)
    h = saida.read_text(encoding="utf-8")
    for aba in ("padroes", "recursos", "series"):
        assert f'data-aba={aba}' in h and f'<section id=aba-{aba}>' in h, aba
    assert f'id="recurso-{RID}"' in h and "<li class=uau>uau 3</li>" in h and "<li class=prov>provisório</li>" in h
    for filtro in ("dimensoes", "material", "luz", "profundidade", "intensidade", "continuidade", "via"):
        assert f'data-filtro="{filtro}"' in h, filtro
    assert "id=so-sem-risco" in h and "só sem risco no PDF" in h and 'data-risco="nao-testado"' in h
    anot, limpa = f"recortes/{RID}__ref-um-05--anotado.jpg", f"recortes/{RID}__ref-um-05.jpg"
    assert f'<img src="{anot}" data-anotada="{anot}" data-limpa="{limpa}"' in h and "button type=button class=troca>ver limpa" in h
    for src in set(re.findall(r'(?:src|data-limpa|data-anotada)="([^"]+)"', h)):
        assert (saida.parent / unquote(src)).is_file(), f"{src} não abre do disco"
    assert 'class=serie id="serie-ref-um"' in h and "<li class=\"abertura\"><b>01</b>abertura</li>" in h
    externos = re.findall(r'(?:src|href)="(https?://[^"]+)"', h)
    assert externos == ["https://exemplo.test/um"], externos
    assert h.count("<script>") == 1 and "url(" not in h and "@import" not in h and "<link" not in h
    assert "Repertório de composição e acabamento" in h and "Objeto com material que cruza o título" in h
    assert "Trecho de acabamento" in h and "tipo_pagina: [" not in h
    print(f"   html de {len(h) // 1024} KB, 3 abas, 7 filtros, figura anotada com a limpa ao lado")


# ================================================================ o repertório real
def test_repertorio_real_checar_zero_falha_e_o_recurso_de_exemplo_aparece():
    rep = repertorio.RAIZ
    res = repertorio.checar(rep)
    assert falhas(res) == [], falhas(res)[:5]
    ind = repertorio.carregar(rep)
    if not ind.get("recursos"):
        print("   índice real v1: 0 falha, sem recurso"); return
    assert [a for a in avisos(res) if "uma referência só" not in a] == [], avisos(res)
    rec = [r for r in ind["recursos"]]
    exemplo_ = next(r for r in rec if r["id"] == "material-do-objeto-diz-o-nivel-da-cota")
    meta, _ = repertorio.ler_front_matter((rep / exemplo_["arquivo"]).read_text(encoding="utf-8"))
    assert meta.get("provisorio") == "true", "o recurso de exemplo tem de estar marcado provisorio: true"
    codigo, out, _ = cli("buscar", "--entidade", "recurso", "--pagina", "cota", "--material", "metal")
    assert codigo == 0 and "material-do-objeto-diz-o-nivel-da-cota" in out, out
    with tempfile.TemporaryDirectory() as d:
        saida = Path(d) / "r.html"
        repertorio.gerar_html(rep, saida)
        h = saida.read_text(encoding="utf-8")
        assert 'id="recurso-material-do-objeto-diz-o-nivel-da-cota"' in h
        for src in set(re.findall(r'data-(?:limpa|anotada)="([^"]+)"', h)):
            assert (saida.parent / unquote(src)).resolve().is_file(), src


if __name__ == "__main__":
    falhou = 0
    for nome, fn in list(globals().items()):
        if nome.startswith("test_"):
            try:
                fn(); print("ok  ", nome)
            except AssertionError as e:
                falhou += 1; print("FALHOU", nome, str(e)[:600])
    for d in [_SADIO.get("dir"), *_SADIO["copias"]]:
        if d:
            shutil.rmtree(d, ignore_errors=True)             # só as pastas que esta prova criou
    print("PROVAS:", "VERDES" if not falhou else f"{falhou} FALHA(S)")
    sys.exit(1 if falhou else 0)

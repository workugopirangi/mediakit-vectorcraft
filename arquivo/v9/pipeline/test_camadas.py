#!/usr/bin/env python3
"""
test_camadas.py: provas da Frente A (camadas.py, encaixes.py, qa_geometria.py). Sem pytest.

  ~/.venvs/mediakit/bin/python pipeline/test_camadas.py              tudo (unidade + render, alguns minutos)
  ~/.venvs/mediakit/bin/python pipeline/test_camadas.py --unidade    só os testes sem render (segundos)
  ~/.venvs/mediakit/bin/python pipeline/test_camadas.py caso_real    só os testes nomeados

Os testes de render montam kits temporários em <pasta temporária do sistema>/mk-render-teste/ (fora do git) a partir do kit
da Sprint, por clone do APFS (nada é escrito na pasta da Sprint), e apagam o que criaram. Sai com 1 se algum
teste falhar.
"""
import hashlib, json, math, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import camadas, encaixes, qa_geometria  # noqa: E402

PY = sys.executable
# uma pasta por cópia do pipeline: frentes paralelas (worktrees) rodando as provas ao mesmo tempo não apagam o kit
# temporário uma da outra (o nome fixo colidia)
BASE = Path(tempfile.gettempdir()) / f"mk-render-teste-{hashlib.sha1(str(AQUI).encode()).hexdigest()[:8]}"
SPRINT = Path("/Users/ugopirangi/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/SPRINT UBATUBA RUN/MEDIAKIT/sprint-2027")
FIXTURE = AQUI.parent / "schema" / "fixtures" / "sprint-sistema-elementos.json"
# As provas leem estados FIXOS do git, não o arquivo vivo: o kit da Sprint muda no piloto e o HEAD muda a cada commit.
# Lido do HEAD, o "antes" do caso real passava enquanto a frente não tinha commitado e quebrava depois (KeyError).
COMMIT_ANTES_DOS_ELEMENTOS = "02c7ed0"   # último pipeline com o ornamento antigo (coordenada fixa, fim da seção)
COMMIT_SPRINT_JSON = "2475f6c"           # mediakit.json da Sprint com a medalha-alada em x1380 y560 (o caso real)


def git_show(commit, caminho):
    """Conteúdo de um arquivo do cofre num commit fixo (caminho absoluto dentro do repositório). A raiz é a do
    repositório principal (git-common-dir), não a da worktree: o kit da Sprint mora no cofre principal e, dentro de uma
    worktree, o --show-toplevel apontava para a cópia e o relative_to quebrava."""
    comum = Path(subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], capture_output=True,
                                text=True, check=True, cwd=str(AQUI)).stdout.strip())
    raiz = comum.parent
    rel = Path(caminho).resolve().relative_to(raiz.resolve())
    return subprocess.run(["git", "show", f"{commit}:{rel.as_posix()}"], capture_output=True, text=True, check=True,
                          cwd=str(raiz)).stdout
RESULTADOS = []


def teste(fn):
    fn._teste = True
    return fn


def log(*a):
    print("   ", *a, flush=True)


# ------------------------------------------------------------------------------------------------- apoio
def kit_sprint(nome, mutar=None, fixture=True):
    """Kit temporário: mediakit.json da Sprint (+ sistema_elementos e elementos da fixture) e o acervo, as fontes e o tema
    copiados por clone do APFS (cp -c: instantâneo, sem gastar disco, e o kit da Sprint nunca é tocado). Era link
    simbólico: o render passou a recusar arquivo que aponta para fora da pasta do kit (revisão de segurança, 09/10)."""
    d = BASE / nome
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for x in ("acervo", "fontes-receitas", "tema-projeto.css"):
        subprocess.run(["cp", "-cR", str(SPRINT / x), str(d / x)], check=True)
    k = json.loads(git_show(COMMIT_SPRINT_JSON, SPRINT / "mediakit.json"))
    if fixture:
        fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
        k["sistema_elementos"] = fx["sistema_elementos"]
        k["elementos"] = fx["elementos"]
    if mutar:
        mutar(k, d)
    (d / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False, indent=1), encoding="utf-8")
    return d


def render(kit, *args, pipeline=AQUI):
    r = subprocess.run([PY, str(pipeline / "render.py"), str(kit), "--fontes", str(kit / "fontes-receitas"), *args],
                       capture_output=True, text=True, cwd=str(pipeline))
    if r.returncode != 0:
        raise AssertionError(f"render falhou ({r.returncode}): {r.stderr[-1500:]}")
    return r.stdout


def plano(kit, nome):
    return json.loads((kit / "saida" / f"plano-elementos-{nome}.json").read_text(encoding="utf-8"))


def png(caminho):
    from PIL import Image
    import numpy as np
    return np.asarray(Image.open(caminho).convert("RGB")).astype(int)


def quadrado(caminho, cor, w=100, h=100):
    from PIL import Image
    caminho.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (w, h), cor + (255,)).save(caminho)


def pipeline_head():
    """O pipeline de antes do sistema de elementos (COMMIT_ANTES_DOS_ELEMENTOS), extraído do git para uma pasta temporária.
    O nome da pasta leva o commit: cópia de outro commit nunca é reaproveitada."""
    alvo = BASE / f"pipeline-{COMMIT_ANTES_DOS_ELEMENTOS}"
    if (alvo / "render.py").exists():
        return alvo
    alvo.mkdir(parents=True, exist_ok=True)
    # rodado de dentro de pipeline/, o git archive entrega a subárvore com caminhos relativos a ela
    tar = subprocess.run(["git", "archive", "--format=tar", COMMIT_ANTES_DOS_ELEMENTOS, "--", "."], capture_output=True,
                         check=True, cwd=str(AQUI)).stdout
    subprocess.run(["tar", "-x", "-C", str(alvo)], input=tar, check=True)
    assert (alvo / "render.py").exists() and (alvo / "templates" / "arquetipos.html").exists(), "pipeline antigo incompleto"
    return alvo


class Temporario:
    """Pasta temporária dentro de BASE, apagada na saída mesmo se o teste falhar."""
    def __init__(self, prefixo):
        self.prefixo = prefixo
    def __enter__(self):
        self.p = Path(tempfile.mkdtemp(prefix=self.prefixo, dir=BASE)); return self.p
    def __exit__(self, *a):
        shutil.rmtree(self.p, ignore_errors=True)


def medidas_sinteticas(prot=(), conteudo=(), cena=None, blocos=None, W=1920, H=1080):
    return {"w": W, "h": H, "safe": 96, "protegidos": [dict(p) for p in prot], "conteudo": [dict(c) for c in conteudo],
            "opacos": [], "cena": cena, "blocos": blocos or {}}


def inter(a, b):
    return min(a["x"] + a["w"], b["x"] + b["w"]) > max(a["x"], b["x"]) and min(a["y"] + a["h"], b["y"] + b["h"]) > max(a["y"], b["y"])


def aabb(it):
    A, B = encaixes.caixa_girada(it["w"], it["h"], it.get("rot", 0))
    return {"x": it["x"] + it["w"] / 2 - A / 2, "y": it["y"] + it["h"] / 2 - B / 2, "w": A, "h": B}


# ================================================================================================= unidade
@teste
def catalogo_cobre_variantes():
    """Toda variante que o render.py sabe gerar tem entrada no encaixes.json, e o catálogo valida no schema."""
    import jsonschema, render
    cat = encaixes.carregar_catalogo()
    esperados = {f"{t}:{v}" for t, vs in render.VARIANTES.items() for v in vs}
    esperados |= {f"ativo:{v}" for v in render.ATIVO_VARIANTES}
    esperados |= {"prova", "projecao", "territorio", "historico_logos", "divisor_cotas", "inventario_colunas"}
    esperados |= set(camadas.VERTICAL)
    # o rótulo que o camadas.py calcula para cada combinação existe no catálogo
    for t, vs in render.VARIANTES.items():
        for v in vs:
            assert camadas.rotulo_variante({"tipo": t, "variante": v}) in cat
    for v, (tipo, var) in render.ATIVO_VARIANTES.items():
        assert camadas.rotulo_variante({"tipo": tipo, "variante": var}) == f"ativo:{v}"
    falta = sorted(esperados - set(cat))
    assert not falta, f"rótulos sem entrada: {falta}"
    sch = json.loads((AQUI.parent / "schema" / "elementos.schema.json").read_text(encoding="utf-8"))
    sub = dict(sch["definitions"]["encaixes"], definitions=sch["definitions"])
    jsonschema.validate(cat, sub)
    for r in ("prova", "projecao"):
        assert not any("heroi" in e["papeis"] for e in cat[r]), f"{r} não pode ter encaixe de herói"
    log(f"{len(cat)} rótulos cobertos ({len(esperados)} esperados), schema ok, prova e projeção sem herói")


@teste
def resolver_canto_desvia_do_texto():
    cat = {"x": [{"id": "canto-sup-dir", "gerador": "canto", "canto": "sup-dir", "max": [500, 500], "min": [150, 150],
                  "papeis": ["heroi"], "camadas": ["frente"]}]}
    titulo = {"classe": "titulo", "x": 1100, "y": 120, "w": 700, "h": 110}
    med = medidas_sinteticas([titulo])
    it = encaixes.resolver([{"id": "h", "papel": "heroi"}], "x", cat, med, {"h": (1000, 800, (100, 100, 900, 700))})
    assert len(it) == 1, med["avisos"]
    it = it[0]
    assert not inter(aabb(it), titulo), f"herói cruza o título: {it}"
    assert 150 <= it["w"] <= 500 + 0.1 and abs(it["w"] / it["h"] - 800 / 600) < 0.01, it
    assert it["x"] + it["w"] <= 1920 - 96 + 0.1 and it["y"] >= 96 - 0.1, it
    # página toda tomada: não coube, devolve vazio e registra aviso
    cheio = medidas_sinteticas([{"classe": "corpo", "x": 0, "y": 0, "w": 1920, "h": 1080}])
    assert encaixes.resolver([{"id": "h", "papel": "heroi"}], "x", cat, cheio, {"h": (1000, 800, None)}) == []
    assert cheio["avisos"] and "não coube" in cheio["avisos"][0], cheio["avisos"]
    log(f"herói em {it['x']:.0f},{it['y']:.0f} {it['w']:.0f}×{it['h']:.0f} longe do título; página cheia: {cheio['avisos'][0]!r}")


@teste
def resolver_ordem_e_ocupados():
    """Constante resolve antes do herói e o herói desvia dela; preferido vem antes da ordem do catálogo."""
    cat = {"x": [{"id": "maior-vazio", "gerador": "maior-vazio", "max": [600, 600], "min": [100, 100], "papeis": ["heroi"], "camadas": ["frente"]},
                 {"id": "canto-inf-esq", "gerador": "canto", "canto": "inf-esq", "max": [400, 400], "min": [100, 100], "papeis": ["heroi"], "camadas": ["frente"]},
                 {"id": "selo", "gerador": "canto", "canto": "sup-esq", "max": [150, 150], "min": [110, 110], "papeis": ["constante"], "camadas": ["frente"]}]}
    med = medidas_sinteticas()
    dims = {"h": (400, 400, None), "c": (150, 150, None)}
    its = encaixes.resolver([{"id": "h", "papel": "heroi", "encaixes_preferidos": ["canto-inf-esq"]},
                             {"id": "c", "papel": "constante", "svg": True}], "x", cat, med, dims)
    assert [i["id"] for i in its] == ["c", "h"], its
    c, h = its
    assert h["encaixe"] == "canto-inf-esq", h
    assert not inter(aabb(c), aabb(h))
    log(f"ordem {[i['id'] for i in its]}, herói no preferido {h['encaixe']}")


@teste
def resolver_faixa_e_fixo_do_pattern():
    cat = {"x": [{"id": "pattern-topo", "gerador": "faixa", "lado": "topo", "esp": 200, "min": [48, 48], "papeis": ["pattern"], "camadas": ["atras"]},
                 {"id": "pp", "gerador": "fixo", "box": [0, 0, 1920, 1080], "papeis": ["pattern"], "camadas": ["sob-veu"]}]}
    med = medidas_sinteticas([{"classe": "titulo", "x": 300, "y": 150, "w": 900, "h": 100}])
    it = encaixes.resolver([{"id": "p", "papel": "pattern"}], "x", cat, med, {"p": (1254, 1254, None)})[0]
    assert it["encaixe"] == "pattern-topo" and it["h"] <= 150 - 16 and it["h"] >= 48, it
    # sob-veu exige cena: sem cena o pattern de página inteira não entra
    med2 = medidas_sinteticas([{"classe": "titulo", "x": 0, "y": 0, "w": 1920, "h": 60}])
    assert encaixes.resolver([{"id": "p", "papel": "pattern", "encaixes_preferidos": ["pp"]}], "x", cat, med2, {"p": (1254, 1254, None)}) == []
    med3 = medidas_sinteticas(cena={"x": 0, "y": 0, "w": 1920, "h": 1080})
    it3 = encaixes.resolver([{"id": "p", "papel": "pattern", "encaixes_preferidos": ["pp"]}], "x", cat, med3, {"p": (1254, 1254, None)})[0]
    assert it3["encaixe"] == "pp" and it3["w"] == 1920, it3
    log(f"faixa afinou para {it['h']:.0f} px; sob-veu só com cena")


@teste
def resolver_atras_de_espia_sem_cobrir_linhas():
    cat = {"x": [{"id": "atras-preco", "gerador": "atras-de", "seletor": ".invest", "canto": "sup-dir", "max": [220, 220], "min": [96, 96],
                  "papeis": ["apoio"], "camadas": ["atras"]}]}
    bloco = {"x": 600, "y": 300, "w": 420, "h": 160}
    linhas = [{"classe": "micro", "x": 634, "y": 320, "w": 200, "h": 20}, {"classe": "preco", "x": 634, "y": 350, "w": 300, "h": 50}]
    med = medidas_sinteticas(linhas, conteudo=[bloco], blocos={".invest": bloco})
    it = encaixes.resolver([{"id": "a", "papel": "apoio"}], "x", cat, med, {"a": (400, 400, None)})[0]
    assert inter(aabb(it), bloco), f"atras-de deveria encostar no bloco: {it}"
    assert not any(inter(aabb(it), l) for l in linhas), f"atras-de cobriu linha do bloco: {it}"
    log(f"apoio espiando o canto do bloco em {it['x']:.0f},{it['y']:.0f} {it['w']:.0f}×{it['h']:.0f}")


@teste
def ajuste_manual_preserva_o_visual():
    """x, y, w e rot antigos (imagem inteira, giro no centro dela) viram a caixa da área visível girando no próprio
    centro: a máscara na página é a mesma (prova pixel a pixel)."""
    from PIL import Image, ImageDraw
    import numpy as np
    with Temporario("manual-") as tmp:
        im = Image.new("RGBA", (1000, 800), (0, 0, 0, 0))
        ImageDraw.Draw(im).ellipse((520, 90, 930, 520), fill=(200, 160, 40, 255))  # mancha fora do centro
        im.save(tmp / "el.png")
        bbox, _ = camadas.alfa_bbox(tmp / "el.png")
        im.crop(bbox).save(tmp / "uso.png")
        man = {"x": 700, "y": 200, "w": 500, "rot": -8}
        novo = encaixes._manual({"id": "e"}, "heroi", man, 1000, 800, bbox, 1920, 1080)
        antigo = {"x": 700, "y": 200, "w": 500, "h": 400, "rot": -8, "arquivo": "el.png", "formato": "png"}
        m_old, ox, oy = qa_geometria.mascara(antigo, tmp)
        m_new, nx, ny = qa_geometria.mascara(dict(novo, uso="uso.png", formato="png"), tmp)
        a, b = np.zeros((1080, 1920), bool), np.zeros((1080, 1920), bool)
        a[oy:oy + m_old.shape[0], ox:ox + m_old.shape[1]] = m_old
        b[ny:ny + m_new.shape[0], nx:nx + m_new.shape[1]] = m_new
        dif = (a ^ b).sum() / max(1, a.sum())
        assert dif < 0.03, f"máscaras diferem em {dif:.1%}"
        log(f"caixa visível {novo['w']:.0f}×{novo['h']:.0f} em {novo['x']:.0f},{novo['y']:.0f}; diferença de pixels {dif:.2%} (borda do giro)")


def _anel(caminho, D=400, r_ext=200, r_int=170):
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    c = D / 2
    dr.ellipse((c - r_ext, c - r_ext, c + r_ext, c + r_ext), fill=(212, 166, 74, 255))
    dr.ellipse((c - r_int, c - r_int, c + r_int, c + r_int), fill=(0, 0, 0, 0))
    im.save(caminho)


@teste
def qa_anel_passa_disco_reprova():
    """Prova 2: anel girado 30° cuja CAIXA cruza 40%+ de uma linha mas cujo ALFA não toca o texto passa; disco opaco
    sobre ~10% de uma linha de corpo reprova."""
    from PIL import Image, ImageDraw
    with Temporario("anel-") as tmp:
        _anel(tmp / "anel.png")
        # anel 400×400 com centro em (700, 500), girado 30°: a caixa girada vai de 427 a 973 nos dois eixos
        anel = {"id": "anel", "papel": "heroi", "camada": "frente", "x": 500, "y": 300, "w": 400, "h": 400, "rot": 30,
                "uso": "anel.png", "formato": "png"}
        linha = {"classe": "corpo", "x": 750, "y": 240, "w": 500, "h": 24, "texto": "linha de corpo"}
        caixa = aabb(anel)
        ix = max(0, min(caixa["x"] + caixa["w"], linha["x"] + linha["w"]) - max(caixa["x"], linha["x"]))
        iy = max(0, min(caixa["y"] + caixa["h"], linha["y"] + linha["h"]) - max(caixa["y"], linha["y"]))
        pct_caixa = ix * iy / (linha["w"] * linha["h"])
        assert pct_caixa >= 0.40, pct_caixa
        pl = {"largura": 1920, "altura": 1080, "paginas": [{"n": 1, "rotulo": "t", "elementos": [anel], "protegidos": [linha]}]}
        f, a = qa_geometria.checar_plano(pl, tmp)
        assert not f, f
        # disco opaco: cobre cerca de 10% da linha de corpo
        im = Image.new("RGBA", (200, 200), (0, 0, 0, 0)); ImageDraw.Draw(im).ellipse((0, 0, 199, 199), fill=(255, 255, 255, 255)); im.save(tmp / "disco.png")
        disco = {"id": "disco", "papel": "heroi", "camada": "frente", "x": 750 - 50 - 100, "y": 252 - 100, "w": 200, "h": 200, "rot": 0,
                 "uso": "disco.png", "formato": "png"}
        m, ox, oy = qa_geometria.mascara(disco, tmp)
        cob = qa_geometria.pixels_em(m, ox, oy, 750, 240, 1250, 264) / (500 * 24)
        assert 0.08 <= cob <= 0.12, cob
        pl["paginas"][0]["elementos"] = [disco]
        f2, _ = qa_geometria.checar_plano(pl, tmp)
        assert f2 and "cobre corpo" in f2[0], f2
        log(f"anel: a caixa cruza {pct_caixa:.0%} da linha, o alfa 0% → passa")
        log(f"disco: cobre {cob:.1%} da linha → {f2[0]}")


@teste
def qa_titulo_logo_sobreposicao_e_contagem():
    from PIL import Image
    with Temporario("qa-") as tmp:
        Image.new("RGBA", (100, 100), (255, 0, 0, 255)).save(tmp / "q.png")
        q = lambda i, x, y, w, papel="heroi": {"id": i, "papel": papel, "camada": "frente", "x": x, "y": y, "w": w, "h": w, "rot": 0, "uso": "q.png", "formato": "png"}
        titulo = {"classe": "titulo", "x": 0, "y": 0, "w": 1000, "h": 100, "texto": "TÍTULO"}
        ok7 = {"paginas": [{"n": 1, "rotulo": "t", "elementos": [q("a", 930, 0, 100)], "protegidos": [titulo]}]}     # 7% do título
        f, _ = qa_geometria.checar_plano(ok7, tmp); assert not f, f
        mau9 = {"paginas": [{"n": 1, "rotulo": "t", "elementos": [q("a", 910, 0, 100)], "protegidos": [titulo]}]}    # 9%
        f, _ = qa_geometria.checar_plano(mau9, tmp); assert f and "cobre titulo" in f[0], f
        logo = {"classe": "logo", "x": 500, "y": 500, "w": 200, "h": 100, "texto": "logo"}
        toque = {"paginas": [{"n": 1, "rotulo": "t", "elementos": [q("a", 699, 600, 50)], "protegidos": [logo]}]}  # 1 px ao lado: encosta
        f, _ = qa_geometria.checar_plano(toque, tmp); assert f and "encosta em logo" in f[0], f
        longe = {"paginas": [{"n": 1, "rotulo": "t", "elementos": [q("a", 720, 620, 50)], "protegidos": [logo]}]}
        f, _ = qa_geometria.checar_plano(longe, tmp); assert not f, f
        dois = {"paginas": [{"n": 1, "rotulo": "t", "elementos": [q("a", 100, 300, 200), q("b", 180, 300, 200, "apoio")], "protegidos": []}]}
        f, _ = qa_geometria.checar_plano(dois, tmp); assert f and "sobrepostos" in f[0], f
        herois = {"paginas": [{"n": 1, "rotulo": "t", "elementos": [q("a", 100, 300, 100), q("b", 400, 300, 100)], "protegidos": []}]}
        f, _ = qa_geometria.checar_plano(herois, tmp); assert f and "2 elementos de papel heroi" in f[0], f
        log("título 7% passa, 9% reprova; 1 px no logo reprova; sobreposição 60% reprova; 2 heróis na página reprova")


@teste
def injecao_na_posicao_certa():
    """sob-veu logo depois da cena (antes do véu legado sem data-layer), atras depois do último véu, frente antes do
    .logo-canto; cena com véu interno recebe o nó dentro dela."""
    sec = ('<section class="pagina">\n  <div class="full"><img src="x.jpg" alt=""></div>\n  <div class="veu escuro"></div>'
           '<div class="veu base"></div>\n  <div class="etiqueta">X</div>\n  <div class="painel inteiro"><h2>T</h2><svg viewBox="0 0 2 2"><path d="M0 0"/></svg></div>\n'
           '  <img class="logo-canto" src="l.png" alt="">\n  <div class="credito">c</div>\n</section>')
    nos = [{"sob-veu": ["<i id=S></i>"], "atras": ["<i id=A></i>"], "frente": ["<i id=F></i>"], "dentro-cena": []}]
    out = camadas.injetar(sec, nos)
    i = {k: out.index(v) for k, v in (("cena", 'class="full"'), ("S", "id=S"), ("veu", 'class="veu escuro"'), ("veu2", 'class="veu base"'),
                                      ("A", "id=A"), ("painel", 'class="painel'), ("F", "id=F"), ("logo", 'class="logo-canto"'))}
    assert i["cena"] < i["S"] < i["veu"] < i["veu2"] < i["A"] < i["painel"] < i["F"] < i["logo"], i
    assert out.index("id=S") > out.index("</div>", i["cena"]), "sob-veu entrou dentro da cena"
    nos2 = [{"sob-veu": [], "atras": [], "frente": [], "dentro-cena": ["<i id=D></i>"]}]
    out2 = camadas.injetar(sec, nos2)
    assert out2.index('<img src="x.jpg"') < out2.index("id=D") < out2.index("</div>", out2.index('class="full"')), "dentro-cena fora da cena"
    # sem cena nem véu (página plana): sob-veu e atras no início da seção, nessa ordem
    plana = '<section class="pagina"><div class="painel"><p>t</p></div></section>'
    out3 = camadas.injetar(plana, nos)
    assert out3.index("id=S") < out3.index("id=A") < out3.index('class="painel"') < out3.index("id=F"), out3
    log("ordem no DOM: cena < sob-veu < véu < véu < atras < painel < frente < logo-canto; véu interno: dentro da cena")


@teste
def preparo_corta_reduz_e_reaproveita():
    from PIL import Image, ImageDraw
    tmp = Path(tempfile.mkdtemp(prefix="prep-", dir=BASE))
    im = Image.new("RGBA", (1254, 1254), (0, 0, 0, 0)); ImageDraw.Draw(im).rectangle((137, 124, 1117, 1056), fill=(200, 150, 50, 255))
    im.save(tmp / "m.png")
    bbox, dims = camadas.alfa_bbox(tmp / "m.png")
    el = {"id": "m", "caminho": tmp / "m.png", "dims": dims, "alfa_bbox": bbox, "sha256": camadas._sha256(tmp / "m.png")}
    import numpy as np
    av = []
    try:
        # foto (cor variada): corta no alfa, reduz a 2x o uso, sem cor chapada
        ImageDraw.Draw(im).rectangle((400, 400, 800, 800), fill=(30, 90, 160, 255)); im.save(tmp / "m.png")
        el["sha256"] = camadas._sha256(tmp / "m.png")
        rel, dest, cor = camadas.preparar_uso(el, 328.6, tmp / "cache", tmp, av)
        out = Image.open(dest)
        assert out.width == 672 and abs(out.width / out.height - (bbox[2] - bbox[0]) / (bbox[3] - bbox[1])) < 0.01, out.size
        assert rel == "cache/m@672.png" and cor is None and not av, (rel, cor, av)
        t0 = dest.stat().st_mtime_ns
        time.sleep(0.01)
        camadas.preparar_uso(el, 330, tmp / "cache", tmp, av)        # mesma largura de cache (múltiplo de 16): reaproveita
        assert dest.stat().st_mtime_ns == t0, "regravou o cache sem precisar"
        el2 = dict(el, sha256="0" * 64)                                # origem mudou: regera
        camadas.preparar_uso(el2, 330, tmp / "cache", tmp, av)
        assert dest.stat().st_mtime_ns != t0, "não regerou com a origem nova"
        # traço de cor chapada (variante -traco): sai só o alfa (RGB preto) e a cor volta à parte
        tr = Image.new("RGBA", (1254, 1254), (212, 166, 74, 0)); ImageDraw.Draw(tr).line((0, 0, 1253, 1253), fill=(212, 166, 74, 255), width=9)
        tr.save(tmp / "t.png")
        et = {"id": "t", "caminho": tmp / "t.png", "dims": (1254, 1254), "alfa_bbox": None, "sha256": camadas._sha256(tmp / "t.png")}
        _, dt, cor_t = camadas.preparar_uso(et, 420, tmp / "cache", tmp, av)
        arr = np.asarray(Image.open(dt).convert("RGBA"))
        assert cor_t == "#D4A64A" and arr.shape[1] == 848 and not arr[..., :3].any() and arr[..., 3].max() == 255, (cor_t, arr.shape)
    finally:
        shutil.rmtree(tmp)
    log(f"1254 px → {out.size[0]}×{out.size[1]} (corte no alfa + 2x de 328,6 px), cache por sha256 + largura; "
        f"traço chapado → tile 848 só de alfa + cor {cor_t}")


@teste
def grafismo_pinta_com_a_cor_da_pagina():
    """O gerador pinta com o hex da paleta; no kit, a cor da marca vira currentColor para o CSS da página mandar (acento
    do fundo papel, microtexto no tom suave). Sem isso o CSS só mudava a caixa lida pelo QA de cor e o dourado ficava."""
    gerar, _ = camadas.gerador_grafismos()
    ctx = {"fontes": {"display": "Kanit", "peso_display": 800, "corpo": "Outfit"}, "paleta": {"marca": "#D4A64A", "texto": "#FFFFFF"},
           "evento": {}, "logo_png": None, "fontes_dir": str(SPRINT / "fontes-receitas")}
    g = gerar("microtexto", {"texto": "Sprint Ubatuba Run · 14.03.2027", "largura": 900}, ctx)
    assert re.search(r'fill="#D4A64A"', g["svg"], re.I), "o gerador mudou: a prova precisa de outro alvo"
    s = camadas.cor_pela_pagina(g["svg"], "#D4A64A")
    assert not re.search(r'(fill|stroke)="#D4A64A"', s, re.I) and 'fill="currentColor"' in s, s[:300]
    log("microtexto: fill #D4A64A do gerador vira currentColor no kit")


@teste
def preparo_reduz_cores_so_em_traco_e_meio_tom():
    """O PNG de uso de traço e meio-tom sai com 32 cores (o PDF da r2 da Sprint passava de 15 MB com os adesivos em cor
    cheia); foto continua com cor cheia (32 cores dariam degrau no degradê)."""
    import numpy as np
    from PIL import Image
    from test_familia import adesivo_meio_tom
    with Temporario("prep-cores-") as d:
        meio_tom = d / "adesivo.png"; adesivo_meio_tom(SPRINT / "acervo" / "elementos" / "folha-amendoeira.png").save(meio_tom)
        foto = SPRINT / "acervo" / "elementos" / "medalha-alada.png"
        cores = {}
        for nome, arq in (("meio-tom", meio_tom), ("foto", foto)):
            im = Image.open(arq)
            el = {"id": nome, "caminho": arq, "dims": im.size, "alfa_bbox": im.getchannel("A").getbbox(), "sha256": camadas._sha256(arq)}
            _, destino, _ = camadas.preparar_uso(el, 300, d / "cache", d, [])
            a = np.asarray(Image.open(destino).convert("RGBA")); cores[nome] = len(np.unique(a.reshape(-1, 4), axis=0))
        assert cores["meio-tom"] <= camadas.CORES_USO, cores
        assert cores["foto"] > 4 * camadas.CORES_USO, cores
        log(f"cores no PNG de uso: meio-tom {cores['meio-tom']}, foto {cores['foto']}")


@teste
def heroi_sobre_a_foto_vai_para_o_canto():
    """Sobre a cena, o herói fica num canto da foto, não no meio (onde está o que a página vende). Antes, centrado,
    o adesivo da r2 da Sprint tapava a escultura na página 'Sua marca nas asas'."""
    import math
    cat = encaixes.carregar_catalogo()
    cena = {"x": 960, "y": 0, "w": 960, "h": 1080}
    med = {"protegidos": [], "conteudo": [], "opacos": [], "cena": cena, "blocos": {}, "w": 1920, "h": 1080, "safe": 96, "avisos": []}
    it = encaixes.resolver([{"id": "h", "papel": "heroi", "encaixes_preferidos": ["sobre-cena"], "camada": "frente"}],
                           "ativo:painel", cat, med, {"h": (1200, 1200, None)})
    assert it and it[0]["encaixe"] == "sobre-cena", (it, med["avisos"])
    x, y, w = it[0]["x"], it[0]["y"], it[0]["w"]
    assert abs(y - 96) <= encaixes.PASSO and abs(x + w - (1920 - 96)) <= encaixes.PASSO, ("canto superior direito da área útil da foto (tolerância: o passo da grade)", it[0])
    log(f"herói sobre a cena em ({it[0]['x']:.0f}, {it[0]['y']:.0f}), {it[0]['w']:.0f} px: canto superior direito")


@teste
def constante_nasce_no_tamanho_do_encaixe():
    """Selo e microtexto em texto vivo só encolhem 25%: nascem no tamanho do encaixe de cada formato. Antes, o selo de
    320 px não cabia no canto de 150 e o microtexto de 1920 px não cabia no vertical de 1080 (ficavam de fora, com aviso)."""
    el = camadas.Elementos.__new__(camadas.Elementos)
    el.catalogo = encaixes.carregar_catalogo()
    atrib = [{"n": 1, "atribuidos": [{"id": "constante-selo"}, {"id": "constante-microtexto"}]}]
    h = [{"n": 1, "rotulo": "capa:c"}]; v = [{"n": 1, "rotulo": "vertical:capa"}]
    assert el._medida_da_constante("selo", "constante-selo", atrib, h, 1920) == {"diametro": 150}
    assert el._medida_da_constante("microtexto", "constante-microtexto", atrib, h, 1920) == {"largura": 1728}
    assert el._medida_da_constante("microtexto", "constante-microtexto", atrib, v, 1080) == {"largura": 888}
    assert el._medida_da_constante("selo", "constante-selo", atrib, v, 1080) == {"diametro": 150}
    sem = [{"n": 1, "atribuidos": [{"id": "outro"}]}]
    assert el._medida_da_constante("selo", "constante-selo", sem, h, 1920) == {}, "constante fora da página não mede"
    log("selo 150 px nos dois formatos; microtexto 1728 px no horizontal e 888 px no vertical")


@teste
def grafismo_real_e_ids_unicos():
    """O render usa o grafismos.gerar da Frente B (sem provisório) e o mesmo svg em várias páginas ganha ids únicos."""
    gerar, nome = camadas.gerador_grafismos()
    import grafismos
    assert gerar is grafismos.gerar and nome == "grafismos.gerar", nome
    fdir = SPRINT / "fontes-receitas"
    ctx = {"fontes": {"display": "Kanit", "peso_display": 800, "corpo": "Outfit"}, "paleta": {"marca": "#D4A64A"},
           "evento": {}, "logo_png": None, "fontes_dir": str(fdir)}
    s = gerar("selo", {"texto": "Sprint Ubatuba Run · 2027"}, ctx)
    ids = re.findall(r'\bid="([^"]+)"', s["svg"])
    assert ids and "<textPath" in s["svg"], s["svg"][:300]
    u = camadas._ids_unicos(s["svg"], "p3")
    for i in ids:
        assert f'id="{i}-p3"' in u and f'id="{i}"' not in u, (i, u[:400])
    refs = re.findall(r'href="#([^"]+)"', u)
    assert refs and all(r.endswith("-p3") for r in refs), refs
    log(f"grafismos.gerar no render; selo com {len(ids)} ids, todos sufixados por página")


# ================================================================================================= render
@teste
def caso_real():
    """Prova 1: medalha-alada (x1380 y560 w420, frente) na cota b da r3 cobre os direitos. ANTES: o QA do último commit
    passa (só protege título). DEPOIS: o qa_geometria reprova ('cobre corpo'); a mesma medalha na cota a da r1 passa."""
    head = pipeline_head()
    antes = kit_sprint("caso-antes", fixture=False)   # o kit como está hoje (elementos no formato antigo)
    try:
        render(antes, "--receita", "r3", "--sem-vertical", pipeline=head)
        q = subprocess.run([PY, str(head / "qa.py"), str(antes)], capture_output=True, text=True, cwd=str(head))
        linhas = [l for l in q.stdout.splitlines() if l.startswith(("FALHA", "AVISO"))]
        sobre = [l for l in linhas if re.search(r"medalha|ornamento", l)]
        rep = json.loads((antes / "saida" / "render-report.json").read_text(encoding="utf-8"))
        p16 = rep["direcoes"]["r3"]["paginas"][15]
        assert p16["variante"] == "b" and any(o["id"] == "medalha-alada" for o in p16["ornamentos"]), p16
        assert not sobre, sobre
        log(f"ANTES (HEAD): medalha-alada desenhada na p.16 (cota b, frente); qa.py: {q.stdout.strip().splitlines()[-1]}; "
            f"nenhuma linha sobre medalha/ornamento")
    finally:
        shutil.rmtree(antes, ignore_errors=True)
    def forca_r1(k, d):
        # a medalha é da família objeto-dourado (r3); na r1 (gravura-ouro) o planejador não a põe. A prova de que o QA não
        # reprova à toa usa o mecanismo do contrato para forçar: exceção por receita e rótulo de página.
        k.setdefault("sistema_elementos", {}).setdefault("excecoes", {})["r1"] = {
            "cota:Naming": {"heroi": "medalha-alada", "porque": "prova: mesma medalha onde há espaço"}}
    depois = kit_sprint("caso-depois", forca_r1)
    try:
        render(depois, "--receita", "r1", "--sem-vertical")
        render(depois, "--receita", "r3", "--sem-vertical")   # por último: o render-report (e o qa.py) fica com a r3
        f3, _ = qa_geometria.checar_plano(plano(depois, "r3"), depois, "r3")
        f1, _ = qa_geometria.checar_plano(plano(depois, "r1"), depois, "r1")
        m3 = [x for x in f3 if "medalha-alada" in x]
        assert m3 and "p.16 cota:b" in m3[0] and "cobre corpo" in m3[0], f3
        p16_r1 = plano(depois, "r1")["paginas"][15]
        assert p16_r1["rotulo"] == "cota:a" and any(e["id"] == "medalha-alada" for e in p16_r1["elementos"]), p16_r1["rotulo"]
        assert not [x for x in f1 if "medalha-alada" in x], f1
        log(f"DEPOIS r3: {m3[0]}")
        log(f"DEPOIS r1: medalha-alada na p.16 cota:a, {len(f1)} falha(s) de geometria")
        # e o qa.py inteiro chama o qa_geometria
        q = subprocess.run([PY, str(AQUI / "qa.py"), str(depois)], capture_output=True, text=True, cwd=str(AQUI))
        assert any("medalha-alada" in l and "cobre corpo" in l for l in q.stdout.splitlines() if l.startswith("FALHA")), q.stdout[-800:]
        log("qa.py inteiro também reprova: " + next(l for l in q.stdout.splitlines() if "medalha-alada" in l)[:120])
    finally:
        shutil.rmtree(depois, ignore_errors=True)


@teste
def camadas_em_pixels():
    """Prova 3, com quadrados coloridos na capa c da r1 e no território: sob-veu sai escurecido pelo véu; atras fica
    sob o texto; o texto da faixa diagonal fica intacto; frente não cobre a etiqueta; atras não cobre o crédito."""
    import numpy as np
    def base(k, d):
        k["paginas"] = [{"tipo": "capa", "variante": "c"}, "territorio"]
        k["elementos"] = []
        k["sistema_elementos"] = {"motivos": [], "familias": [], "constantes": [], "receitas": {}}
    k0 = kit_sprint("pix-base", base)
    try:
        render(k0, "--receita", "r1", "--png", "--sem-vertical")
        pl = plano(k0, "r1")
        cap, ter = pl["paginas"][0], pl["paginas"][1]
        assert cap["rotulo"] == "capa:c" and ter["rotulo"] == "territorio", (cap["rotulo"], ter["rotulo"])
        tese = next(p for p in cap["protegidos"] if p["classe"] == "corpo" and p["texto"].startswith("Ubatuba muda"))
        etiq = next(p for p in cap["protegidos"] if p["classe"] == "etiqueta")
        faixa = [p for p in cap["protegidos"] if p["texto"].lower().startswith("14 de março")]
        cred = next(p for p in ter["protegidos"] if p["classe"] == "credito")
        assert len(faixa) > 4, "faixa diagonal sem pedaços medidos"
        alvo_f = sorted(faixa, key=lambda p: p["x"])[-3]          # pedaço do texto perto do fim da faixa
        b0 = png(k0 / "saida" / "png" / "kit-r1-01.png"); t0 = png(k0 / "saida" / "png" / "kit-r1-02.png")
    finally:
        pass
    q = {}
    def com_quadrados(k, d):
        base(k, d)
        cores = {"sob": (255, 0, 0), "atr": (255, 0, 0), "txa": (0, 190, 0), "txf": (0, 190, 0), "fx": (0, 60, 255), "et": (255, 220, 0), "cr": (255, 0, 255)}
        for nome, cor in cores.items():
            quadrado(d / "teste" / f"{nome}.png", cor, 100, 100 if nome not in ("txa", "txf") else 20)
        lw = tese["w"] * 0.4
        q.update({
            "sob": dict(x=150, y=160, w=120, camada="sob-veu", paginas=["capa"]),
            "atr": dict(x=330, y=160, w=120, camada="atras", paginas=["capa"]),
            "txa": dict(x=tese["x"], y=tese["y"] + tese["h"] / 2 - lw / 10, w=lw, camada="atras", paginas=["capa"]),
            "txf": dict(x=tese["x"] + tese["w"] * 0.6, y=tese["y"] + tese["h"] / 2 - lw / 10, w=lw, camada="frente", paginas=["capa"]),
            "fx": dict(x=alvo_f["x"] + alvo_f["w"] / 2 - 70, y=alvo_f["y"] + alvo_f["h"] / 2 - 70, w=140, camada="atras", paginas=["capa"]),
            "et": dict(x=etiq["x"] - 60, y=etiq["y"] + etiq["h"] / 2 - 60, w=120, camada="frente", paginas=["capa"]),
            "cr": dict(x=cred["x"] - 50, y=cred["y"] + cred["h"] / 2 - 50, w=100, camada="atras", paginas=["territorio"]),
        })
        k["elementos"] = [dict(id=f"q-{n}", papel="ornamento", formato="png", arquivo=f"teste/{n}.png", rot=0, opacidade=1, blend="normal", **v) for n, v in q.items()]
    k1 = kit_sprint("pix-quadrados", com_quadrados)
    try:
        render(k1, "--receita", "r1", "--png", "--sem-vertical")
        b1 = png(k1 / "saida" / "png" / "kit-r1-01.png"); t1 = png(k1 / "saida" / "png" / "kit-r1-02.png")
        caixa = lambda img, x, y, w, h: img[int(y):int(y + h), int(x):int(x + w)]
        # 1. sob-veu escurecido pelo véu (a mesma cor em atras, ao lado, fica clara)
        r_sob = caixa(b1, 170, 180, 80, 80)[..., 0].mean(); r_atr = caixa(b1, 350, 180, 80, 80)[..., 0].mean()
        assert r_sob < 0.75 * r_atr and r_atr > 200, (r_sob, r_atr)
        log(f"sob-veu: vermelho {r_sob:.0f} (véu por cima) × atras {r_atr:.0f}")
        # 2. atras fica sob o texto (o branco da letra aparece sobre o verde); frente cobre (nenhum branco)
        branco = lambda reg: float(((reg[..., 0] > 200) & (reg[..., 1] > 200) & (reg[..., 2] > 200)).mean())
        lw = tese["w"] * 0.4
        ra = caixa(b1, tese["x"] + 4, tese["y"] + 2, lw - 8, tese["h"] - 4)
        rf = caixa(b1, tese["x"] + tese["w"] * 0.6 + 4, tese["y"] + 2, lw - 8, tese["h"] - 4)
        verde = lambda reg: float(((reg[..., 1] > 150) & (reg[..., 0] < 80)).mean())
        assert verde(ra) > 0.2 and branco(ra) > 0.05, (verde(ra), branco(ra))
        assert verde(rf) > 0.9 and branco(rf) < 0.005, (verde(rf), branco(rf))
        log(f"atras sob a linha da tese: {branco(ra):.0%} de pixels de letra visíveis sobre o verde; frente: {branco(rf):.1%}")
        # 3. faixa diagonal intacta onde há texto (linha central da faixa); o quadrado aparece fora dela
        ang = math.radians(12); cy = lambda x: 856 - (x - 960) * math.tan(ang)
        x0 = int(q["fx"]["x"]) + 10
        difs = [np.abs(b1[int(cy(x)) - 9:int(cy(x)) + 10, x] - b0[int(cy(x)) - 9:int(cy(x)) + 10, x]).max() for x in range(x0, x0 + 120)]
        fora = np.abs(caixa(b1, q["fx"]["x"] + 4, q["fx"]["y"] + 4, 20, 20) - caixa(b0, q["fx"]["x"] + 4, q["fx"]["y"] + 4, 20, 20)).max()
        assert max(difs) <= 3, max(difs)
        assert fora > 60, f"o quadrado sob a faixa nem apareceu ({fora})"
        log(f"faixa diagonal: diferença máxima {max(difs)} na linha do texto (quadrado azul visível fora da faixa: Δ {fora})")
        # 4. frente não cobre a etiqueta (miolo da pílula, sem as pontas arredondadas)
        r = etiq["h"] / 2
        miolo = (etiq["x"] + r + 2, etiq["y"] + 6, etiq["w"] - 2 * r - 4, etiq["h"] - 12)
        de = np.abs(caixa(b1, *miolo) - caixa(b0, *miolo)).max()
        fe = np.abs(caixa(b1, etiq["x"] - 56, etiq["y"] + etiq["h"] / 2 - 10, 20, 20) - caixa(b0, etiq["x"] - 56, etiq["y"] + etiq["h"] / 2 - 10, 20, 20)).max()
        assert de <= 3 and fe > 60, (de, fe)
        log(f"etiqueta: diferença máxima {de} no miolo; o quadrado frente aparece ao lado dela (Δ {fe})")
        # 5. atras não cobre o crédito (antes: z1 no fim da seção pintava por cima). O fundo do crédito é translúcido:
        #    o quadrado aparece através dele, mas as letras ficam por cima (mesma quantidade de pixel de letra)
        reg = (cred["x"] + 3, cred["y"] + 3, 44, cred["h"] - 6)
        letra = lambda img: float(((img[..., 0] > 180) & (img[..., 1] > 180) & (img[..., 2] > 180)).mean())
        l1, l0 = letra(caixa(t1, *reg)), letra(caixa(t0, *reg))
        mag = float(((caixa(t1, *reg)[..., 0] > 90) & (caixa(t1, *reg)[..., 1] < 60)).mean())
        assert l0 > 0.03 and l1 >= 0.6 * l0 and mag > 0.2, (l0, l1, mag)
        log(f"crédito sobre o quadrado: {l1:.0%} de pixel de letra (sem o quadrado: {l0:.0%}), magenta por trás em {mag:.0%}")
    finally:
        shutil.rmtree(k0, ignore_errors=True)
        shutil.rmtree(k1, ignore_errors=True)


def _conteudo(k, d, maximo):
    """Variantes cobrindo o catálogo inteiro nas 3 receitas e conteúdo no mínimo ou no máximo dos slots."""
    var = {"r1": {"capa": "c", "manifesto": "a", "publico": "a", "divisor": "b", "cota": "a", "contato": "a",
                  "ativo": ["diagonal", "topo", "sangria", "painel", "diagonal", "sangria"]},
           "r2": {"capa": "b", "manifesto": "b", "publico": "b", "divisor": "c", "cota": "c", "contato": "b",
                  "ativo": ["painel", "topo", "painel", "sangria", "painel", "topo"]},
           "r3": {"capa": "a", "manifesto": "b", "publico": "a", "divisor": "a", "cota": "b", "contato": "b",
                  "ativo": ["sangria", "topo", "sangria", "painel", "sangria", "painel"]}}
    for r in k["receitas"]:
        r["variantes"] = var[r["id"]]
    for f in k["sistema_elementos"]["receitas"].values():
        f["familia"] = "objeto-dourado"             # heróis em toda receita: todo rótulo é exercitado
    for e in k["elementos"]:
        for c in ("x", "y", "w", "rot", "paginas", "camada"):
            e.pop(c, None)                          # sem ajuste manual: tudo pelos encaixes
    k["inventario"].append({"ativo": "Guarda-volumes", "onde": "Arena", "grupo": "fisico"})
    k["inventario"].append({"ativo": "Ponto de hidratação", "onde": "Percurso, km 2 e km 4", "grupo": "fisico"})
    if maximo:
        k["tese"]["frase"] = "Ubatuba muda de ritmo em março e a sua marca corre junto com ela."
        k["manifesto"]["frase"] = ("A <b>Sprint Ubatuba Run</b> traz a corrida para dentro da cidade: quem vem correr traz a família, fica o fim "
                                   "de semana inteiro na orla, conhece o comércio local e deixa 1 kg de alimento na retirada do kit para quem precisa.")[:240]
        for c in k["cotas"]:
            c["entregaveis"] = (c["entregaveis"] + [f"Item adicional {i}: placa na arena e menção no site oficial" for i in range(8)])[:8]
            c["frase"] = (c["frase"] + " Presença do kit à chegada, com relatório.")[:110]
        for i in k["inventario"]:
            if i.get("texto"):
                i["texto"] = (i["texto"] + " A marca aparece nas fotos oficiais, nos vídeos da organização e nas publicações das assessorias da região.")[:375]
        k["cotas_intro"] = (k["cotas_intro"] + " Todas incluem relatório pós-evento.")[:200]
    else:
        k["tese"]["frase"] = "Sua marca corre junto."
        k["manifesto"]["frase"] = "A <b>Sprint Ubatuba Run</b> traz a corrida para a cidade."
        k["manifesto"]["subtitulo"] = None
        for c in k["cotas"]:
            c["entregaveis"] = c["entregaveis"][:1]
            c["frase"] = None
            c["exclusividade"] = None
        for i in k["inventario"]:
            if i.get("texto"):
                i["texto"] = i["texto"].split(":")[0][:90] + "."
                i["aplicacoes"] = i["aplicacoes"][:2]
        k["cotas_intro"] = "Quatro cotas na orla de Ubatuba."
        k["publico"]["genero"] = None


@teste
def contrato_conteudo_minimo_e_maximo():
    """Prova 4: render das 3 receitas (todas as variantes do catálogo) com conteúdo mínimo e máximo; nenhum elemento
    posicionado pelos encaixes encosta numa caixa protegida e o qa_geometria passa em todos os planos."""
    for nome, maximo in (("minimo", False), ("maximo", True)):
        kit = kit_sprint(f"conteudo-{nome}", lambda k, d: _conteudo(k, d, maximo))
        try:
            for r in ("r1", "r2", "r3"):
                render(kit, "--receita", r)
            rotulos, herois, elegiveis, itens, n_prot, fora = set(), 0, 0, 0, 0, 0
            for f in sorted((kit / "saida").glob("plano-elementos-*.json")):
                pl = json.loads(f.read_text(encoding="utf-8"))
                fa, _ = qa_geometria.checar_plano(pl, kit, f.stem)
                assert not fa, fa
                for pg in pl["paginas"]:
                    rotulos.add(pg["rotulo"])
                    n_prot += len(pg["protegidos"]); fora += len(pg["avisos"])
                    assert not any("sem entrada no encaixes.json" in a for a in pg["avisos"]), pg["avisos"]
                    elegiveis += pg["elegivel_heroi"]; herois += any(e["papel"] == "heroi" for e in pg["elementos"])
                    for e in pg["elementos"]:
                        itens += 1
                        if e["papel"] == "pattern":
                            continue
                        for p in pg["protegidos"]:
                            assert not inter(aabb(e), p), f"{f.stem} p.{pg['n']} {pg['rotulo']}: {e['id']} cruza {p['classe']} {p['texto']!r}"
            assert {"capa:a", "capa:b", "capa:c", "cota:a", "cota:b", "cota:c", "ativo:diagonal", "ativo:sangria", "inventario_colunas",
                    "vertical:capa", "vertical:numeros", "vertical:contato"} <= rotulos, sorted(rotulos)
            log(f"conteúdo {nome}: {len(rotulos)} rótulos, {n_prot} caixas protegidas medidas, {itens} elementos posicionados "
                f"({fora} não couberam e viraram aviso), herói em {herois} de {elegiveis} páginas elegíveis, 0 caixa cruzada, "
                f"qa_geometria 0 falhas")
        finally:
            shutil.rmtree(kit, ignore_errors=True)


@teste
def peso_do_pdf_e_grafismo():
    """Prova 5: a r1 com os mesmos 4 heróis e o pattern que deram 13,6 MB, agora com PNG preparado, fica ≤ 9 MB; o kit de
    teste (fixture) também; grafismo não acrescenta imagem nem fonte Type 3 e o texto dele é texto no PDF."""
    head = pipeline_head()
    mesmo = kit_sprint("peso-formato-antigo", fixture=False)   # elementos do kit hoje: 4 heróis + pattern, manuais
    try:
        render(mesmo, "--receita", "r1", "--sem-vertical", pipeline=head)
        antes = (mesmo / "saida" / "kit-r1.pdf").stat().st_size
        imgs_antes = subprocess.run(["pdfimages", "-list", str(mesmo / "saida" / "kit-r1.pdf")], capture_output=True, text=True).stdout
        shutil.rmtree(mesmo / "saida")
        render(mesmo, "--receita", "r1", "--sem-vertical")
        depois = (mesmo / "saida" / "kit-r1.pdf").stat().st_size
        imgs = subprocess.run(["pdfimages", "-list", str(mesmo / "saida" / "kit-r1.pdf")], capture_output=True, text=True).stdout
        grandes = [l for l in imgs.splitlines()[2:] if l.split()[3:5] == ["1254", "1254"]]
        assert depois <= 9_000_000, depois
        assert not grandes, grandes
        n_antes = len([l for l in imgs_antes.splitlines()[2:] if l.split()[3:5] == ["1254", "1254"]])
        log(f"mesma composição da r1 (4 heróis + pattern): HEAD {antes / 1e6:.1f} MB ({n_antes} imagens de 1254 px) → {depois / 1e6:.1f} MB, nenhuma imagem de 1254 px")
    finally:
        shutil.rmtree(mesmo, ignore_errors=True)
    fx = kit_sprint("peso-fixture")
    try:
        render(fx, "--receita", "r1", "--sem-vertical")
        tam = (fx / "saida" / "kit-r1.pdf").stat().st_size
        assert tam <= 9_000_000, tam
        log(f"kit de teste (fixture) r1: {tam / 1e6:.1f} MB")
    finally:
        shutil.rmtree(fx, ignore_errors=True)
    # grafismo: as mesmas páginas com e sem as constantes (microtexto e selo); nenhum outro elemento
    def so(constantes):
        def m(k, d):
            k["paginas"] = ["capa", "divisor", "contato"]
            k["elementos"] = []
            k["sistema_elementos"]["receitas"]["r1"]["pattern"] = None
            if not constantes:
                k["sistema_elementos"]["constantes"] = []
        return m
    sem, com = kit_sprint("graf-sem", so(False)), kit_sprint("graf-com", so(True))
    try:
        render(sem, "--receita", "r1", "--sem-vertical"); render(com, "--receita", "r1", "--sem-vertical")
        lista = lambda k: [l.split()[:5] for l in subprocess.run(["pdfimages", "-list", str(k / "saida" / "kit-r1.pdf")], capture_output=True, text=True).stdout.splitlines()[2:]]
        fontes = subprocess.run(["pdffonts", str(com / "saida" / "kit-r1.pdf")], capture_output=True, text=True).stdout
        texto = subprocess.run(["pdftotext", str(com / "saida" / "kit-r1.pdf"), "-"], capture_output=True, text=True).stdout
        pl = plano(com, "r1")
        n_graf = sum(1 for pg in pl["paginas"] for e in pg["elementos"] if e.get("formato") == "svg")
        assert n_graf >= 4, n_graf
        # o grafismo não rasteriza nada: a única imagem nova é o logo do cliente no miolo do selo (pequena, com alfa),
        # uma por selo; o texto continua texto (conferido abaixo)
        from collections import Counter
        tipo_tam = lambda k: Counter((x[2], int(x[3]), int(x[4])) for x in lista(k))
        extras = tipo_tam(com) - tipo_tam(sem)
        selos = sum(1 for pg in pl["paginas"] for e in pg["elementos"] if e["id"].startswith("constante-selo"))
        assert all(w <= 400 and h <= 400 for (_, w, h) in extras), extras
        assert sum(n for (tp, _, _), n in extras.items() if tp == "image") == selos, (extras, selos)
        assert "Type 3" not in fontes, fontes
        corrido = re.sub(r"\s+", "", texto)   # o pdftotext separa letras espaçadas ("S P R I N T"): compara sem espaços
        assert "SPRINTUBATUBARUN·14.03.2027" in corrido, corrido[:400]
        log(f"{n_graf} grafismos em 3 páginas: imagem nova só o logo do miolo de cada selo ({selos}), nada rasterizado, nenhuma Type 3, "
            f"microtexto é texto no PDF; fontes: {', '.join(sorted({l.split()[0].split('+')[-1] for l in fontes.splitlines()[2:]}))}")
    finally:
        shutil.rmtree(sem, ignore_errors=True)
        shutil.rmtree(com, ignore_errors=True)


# ================================================================================================= execução
def main():
    BASE.mkdir(parents=True, exist_ok=True)
    nomes = [a for a in sys.argv[1:] if not a.startswith("--")]
    so_unidade = "--unidade" in sys.argv
    render_ = {"caso_real", "camadas_em_pixels", "contrato_conteudo_minimo_e_maximo", "peso_do_pdf_e_grafismo"}
    testes = [(n, f) for n, f in globals().items() if callable(f) and getattr(f, "_teste", False)]
    if nomes:
        testes = [(n, f) for n, f in testes if n in nomes]
    elif so_unidade:
        testes = [(n, f) for n, f in testes if n not in render_]
    falhou = 0
    for n, f in testes:
        t0 = time.time()
        try:
            f()
            print(f"OK      {n}  ({time.time() - t0:.1f} s)", flush=True)
        except Exception as e:
            falhou += 1
            print(f"FALHOU  {n}  ({time.time() - t0:.1f} s): {type(e).__name__}: {str(e)[:1200]}", flush=True)
    shutil.rmtree(BASE / f"pipeline-{COMMIT_ANTES_DOS_ELEMENTOS}", ignore_errors=True)
    print(f"\n{len(testes) - falhou} de {len(testes)} testes passaram")
    sys.exit(1 if falhou else 0)


if __name__ == "__main__":
    main()

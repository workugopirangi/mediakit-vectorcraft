#!/usr/bin/env python3
"""Provas do familia.py. Rodar: ~/.venvs/mediakit/bin/python test_familia.py. Lê (só leitura) os 6 elementos reais da
Sprint (acervo/elementos do kit sprint-2027; MEDIAKIT_SPRINT=<pasta-do-kit> sobrepõe) e desenha os controles sintéticos
numa pasta temporária. Sem o acervo real, as provas que dependem dele saem como 'pulado'."""
import json, os, shutil, sys, tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import familia  # noqa: E402

FIXTURE = AQUI.parent / "schema" / "fixtures" / "sprint-sistema-elementos.json"


class Pulado(Exception):
    pass


def pasta_sprint():
    for c in (os.environ.get("MEDIAKIT_SPRINT"),
              AQUI.parent.parent.parent / "CLIENTES" / "SPRINT UBATUBA RUN" / "MEDIAKIT" / "sprint-2027",
              Path.home() / "Developer" / "UGO's Second Brain" / "01 EMPRESAS" / "MOTION PERFORM" / "CLIENTES" / "SPRINT UBATUBA RUN" / "MEDIAKIT" / "sprint-2027"):
        if c and (Path(c) / "acervo" / "elementos" / "medalha-alada.png").is_file():
            return Path(c)
    raise Pulado("acervo real da Sprint não encontrado")


def fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def elementos_e_familias():
    fx = fixture()
    return fx["elementos"], {f["id"]: f for f in fx["sistema_elementos"]["familias"]}


def esfera(luz_x, cor=(0xD0, 0x90, 0x50), n=900):
    """Objeto fotográfico sintético: esfera lambertiana, luz vinda de luz_x (< 0 esquerda, > 0 direita)."""
    y, x = np.mgrid[0:n, 0:n]; R = 0.42 * n
    dx = (x - n / 2) / R; dy = (y - n / 2) / R; dentro = dx ** 2 + dy ** 2 <= 1
    dz = np.sqrt(np.clip(1 - dx ** 2 - dy ** 2, 0, 1))
    L = np.array([luz_x, -0.3, 0.8]); L = L / np.linalg.norm(L)        # vetor para a luz: x < 0 acende o lado esquerdo
    sombra = np.clip(dx * L[0] + dy * L[1] + dz * L[2], 0, 1) * 0.85 + 0.15
    rgb = (sombra[..., None] * np.array(cor)).clip(0, 255).astype(np.uint8)
    return np.dstack([rgb, (dentro * 255).astype(np.uint8)])


def test_separa_os_2_tracos_dos_4_fotorreais():
    kit = pasta_sprint(); els, _ = elementos_e_familias()
    print(f"   {'elemento':18s} {'meio':12s} {'n_cores':>7s} {'croma':>6s} {'L desv':>6s} {'traço nat':>9s} {'traço uso':>9s} {'cobert':>6s} {'luz':>11s} {'razão':>6s}  paleta")
    medidos = {}
    for e in els:
        d = familia.descritores(kit / e["arquivo"])
        uso = familia.escala_de_uso(e, d)
        traco_uso = round(d["traco_px_nativo"] * uso / d["alfa_bbox"][2], 2)
        medidos[e["id"]] = d
        print(f"   {e['id']:18s} {d['meio']:12s} {d['n_cores']:>7d} {d['croma']:>6.1f} {d['l_desvio']:>6.1f} {d['traco_px_nativo']:>9.2f} {traco_uso:>9.2f} {d['cobertura']:>6.3f} {str(d['luz']):>11s} {str(d['razao_luz']):>6s}  "
              + ", ".join(f"{p['hex']} {p['peso']:.2f}" for p in d["paleta"][:3]))
    tracos = {i for i, d in medidos.items() if d["meio"] == "traco"}
    fotos = {i for i, d in medidos.items() if d["meio"] == "foto-objeto"}
    assert tracos == {"penas-asa", "ondas-serra"}, tracos
    assert fotos == {"pena-dourada", "folha-amendoeira", "medalha-alada", "tenis-usado"}, fotos
    assert max(medidos[i]["n_cores"] for i in tracos) < familia.LIMITE_N_CORES_CHAPADO < min(medidos[i]["n_cores"] for i in fotos)


def test_medalha_recolorida_para_azul_reprova():
    kit = pasta_sprint(); els, fams = elementos_e_familias()
    e = next(x for x in els if x["id"] == "medalha-alada")
    arr = np.asarray(Image.open(kit / e["arquivo"]).convert("RGBA"))
    original = familia.pertence(e, fams["objeto-dourado"], descr=familia.descritores(arr))
    azul = familia.pertence(e, fams["objeto-dourado"], descr=familia.descritores(familia._recolorir(arr, 212)))
    print(f"   medalha original: ΔE {original['medidas']['delta_e']} pertence={original['pertence']}; azul: ΔE {azul['medidas']['delta_e']} pertence={azul['pertence']} {azul['motivos']}")
    assert original["pertence"], original
    assert not azul["pertence"] and any(m.startswith("paleta") for m in azul["motivos"]), azul
    assert azul["medidas"]["delta_e"] > familia.LIMITE_DELTA_E > original["medidas"]["delta_e"]


def test_limite_de_paleta_fica_entre_membros_e_estranhos():
    """Rótulo do olho (folha.png da Sprint): membros por cor = penas-asa na gravura-ouro; pena, medalha e tênis na
    objeto-dourado. Estranhos por cor = folha (verde e vermelha) na objeto-dourado, ondas-serra (traço dourado) na
    meio-tom-mar (azul do mar), medalha (fita preta) na gravura-ouro (só ouro)."""
    kit = pasta_sprint(); els, fams = elementos_e_familias(); por = {e["id"]: e for e in els}
    de = lambda i, f: familia.pertence(por[i], fams[f], base=kit)["medidas"]["delta_e"]  # noqa: E731
    membros = {("penas-asa", "gravura-ouro"), ("pena-dourada", "objeto-dourado"), ("medalha-alada", "objeto-dourado"), ("tenis-usado", "objeto-dourado")}
    estranhos = {("folha-amendoeira", "objeto-dourado"), ("ondas-serra", "meio-tom-mar"), ("medalha-alada", "gravura-ouro")}
    dm = {p: de(*p) for p in membros}; dx = {p: de(*p) for p in estranhos}
    print("   membros:", {f"{a}>{b}": v for (a, b), v in sorted(dm.items())})
    print("   estranhos:", {f"{a}>{b}": v for (a, b), v in sorted(dx.items())})
    assert max(dm.values()) < familia.LIMITE_DELTA_E < min(dx.values()), (dm, dx)
    # mesma cor e meio diferente: só o meio separa (penas-asa dourada contra a família fotorreal dourada, ΔE 10,2)
    r = familia.pertence(por["penas-asa"], fams["objeto-dourado"], base=kit)
    assert r["medidas"]["delta_e"] < familia.LIMITE_DELTA_E and not r["pertence"] and r["motivos"][0].startswith("meio"), r
    # veredito completo contra a família que a fixture declara
    esperado = {"penas-asa": True, "ondas-serra": False, "pena-dourada": True, "folha-amendoeira": False, "medalha-alada": True, "tenis-usado": True}
    for e in els:
        r = familia.pertence(e, fams[e["familia"]], base=kit)
        print(f"   {e['id']:18s} na {e['familia']:15s} {'PERTENCE' if r['pertence'] else 'FORA: ' + '; '.join(r['motivos'])}")
        assert r["pertence"] == esperado[e["id"]], (e["id"], r)


def test_traco_fora_da_faixa_reprova():
    kit = pasta_sprint(); els, fams = elementos_e_familias()
    e = next(x for x in els if x["id"] == "penas-asa")
    d = familia.descritores(kit / e["arquivo"])
    no_uso = familia.pertence(e, fams["gravura-ouro"], descr=d)
    grosso = familia.pertence(dict(e, escala_tile=2508), fams["gravura-ouro"], descr=d)
    print(f"   penas-asa: tile 420 px → {no_uso['medidas']['traco_px_uso']} px ({no_uso['pertence']}); tile 2508 px → {grosso['medidas']['traco_px_uso']} px {grosso['motivos']}")
    assert no_uso["pertence"] and not grosso["pertence"] and any(m.startswith("traço") for m in grosso["motivos"])


def test_luz_invertida_reprova_e_luz_suave_so_avisa():
    fam = {"id": "objeto-dourado", "meio": "foto-objeto", "paleta": ["#D09050", "#281805"], "luz": "esquerda"}
    e = {"id": "esfera", "papel": "heroi"}
    esq = familia.pertence(e, fam, descr=familia.descritores(esfera(-0.9)))
    dir_ = familia.pertence(e, fam, descr=familia.descritores(esfera(0.9)))
    print(f"   esfera luz da esquerda: {esq['medidas'].get('luz')} {esq['medidas'].get('razao_luz')} pertence={esq['pertence']}; da direita: {dir_['medidas'].get('luz')} {dir_['medidas'].get('razao_luz')} {dir_['motivos']}")
    assert esq["pertence"], esq
    assert not dir_["pertence"] and any(m.startswith("luz") for m in dir_["motivos"]), dir_
    try:
        kit = pasta_sprint()
    except Pulado:
        return
    els, fams = elementos_e_familias()
    for x in els:
        if x["familia"] == "objeto-dourado":
            r = familia.pertence(x, fams["objeto-dourado"], base=kit)
            assert not any(m.startswith("luz") for m in r["motivos"]), (x["id"], r)     # luz suave real: no máximo aviso


def test_meio_tom_e_chapado_sinteticos():
    n = 1000; im = Image.new("RGBA", (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(0, n, 24):
        for j in range(0, n, 24):
            r = 3 + 5 * abs(np.sin(i / 90) * np.cos(j / 130))
            d.ellipse([i - r + 12, j - r + 12, i + r + 12, j + r + 12], fill=(0x20, 0x67, 0xAA, 255))
    assert familia.descritores(im)["meio"] == "meio-tom"
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([100, 200, 900, 800], fill=(0xD4, 0xA6, 0x4A, 255))
    assert familia.descritores(im)["meio"] == "chapado"


def adesivo_meio_tom(origem, passo=9, tinta=(32, 103, 170), papel=(244, 234, 219)):
    """Retícula de pontos (tinta sobre papel) dentro do recorte do elemento, com borda de adesivo: o meio-tom impresso
    sobre papel opaco, como o GPT Image entrega o adesivo da família meio-tom-mar."""
    from PIL import ImageFilter
    im = Image.open(origem).convert("RGBA"); w, h = im.size
    L = np.asarray(im.convert("L"), float) / 255.0; a = np.asarray(im)[..., 3] > 127
    k = 4; tela = Image.new("RGB", (w * k, h * k), papel); dr = ImageDraw.Draw(tela)
    for y in range(0, h, passo):
        for x in range(0, w, passo):
            bloco = a[y:y + passo, x:x + passo]
            if bloco.mean() < 0.5:
                continue
            r = passo / 2 * np.sqrt(1 - L[y:y + passo, x:x + passo][bloco].mean()) * 1.15 * k
            cx, cy = (x + passo / 2) * k, (y + passo / 2) * k
            if r > 0.6 * k:
                dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tinta)
    tela = tela.resize((w, h), Image.LANCZOS)
    borda = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(15))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); out.paste(Image.new("RGB", (w, h), papel), (0, 0), borda)
    out.paste(tela, (0, 0), Image.fromarray((a * 255).astype(np.uint8)))
    return out


def test_meio_tom_impresso_sobre_papel_e_meio_tom_e_foto_continua_foto():
    """O adesivo de meio-tom (pontos de tinta impressos sobre papel opaco, dentro do recorte) era medido como fotorreal:
    o antisserrilhado dá 16 cores e os pontos não são manchas no alfa. Agora a tinta é separada do papel."""
    sp = pasta_sprint()
    with tempfile.TemporaryDirectory() as d:
        for nome in ("folha-amendoeira", "medalha-alada"):
            arq = Path(d) / f"meio-tom-{nome}.png"; adesivo_meio_tom(sp / "acervo" / "elementos" / f"{nome}.png").save(arq)
            m = familia.descritores(arq)
            assert m["meio"] == "meio-tom", (nome, m["meio"], m["frac_pontos_impressos"], m["n_cores"])
    for nome in ("pena-dourada", "folha-amendoeira", "medalha-alada", "tenis-usado"):
        m = familia.descritores(sp / "acervo" / "elementos" / f"{nome}.png")
        assert m["meio"] == "foto-objeto" and m["frac_pontos_impressos"] < familia.MEIO_TOM_IMPRESSO_FRAC, (nome, m["meio"], m["frac_pontos_impressos"])
    real = sp / "acervo" / "elementos" / "ondas-serra-adesivo.png"
    if real.is_file():
        m = familia.descritores(real)
        assert m["meio"] == "meio-tom", ("adesivo real", m["meio"], m["frac_pontos_impressos"])
        print(f"   adesivo real do GPT Image: meio-tom, fração {m['frac_pontos_impressos']:.2f}")


def test_faixa_de_traco_da_familia_vence_o_fator():
    """Decisão do Ugo (09/10/2026): a gravura-ouro aceita hachura fina. Sem `traco_px_min`, o par de asas (0,83 px na
    escala de uso) reprova pelo fator 1,6; com `traco_px_min: 0.75` na família, passa. Traço grosso continua barrado."""
    kit = pasta_sprint(); arq = kit / "acervo" / "elementos" / "asas-par-gravura.png"
    if not arq.is_file():
        raise Pulado("asas-par-gravura.png ainda não gerado")
    _, fams = elementos_e_familias(); fam = dict(fams["gravura-ouro"])
    e = {"id": "asas-par-gravura", "arquivo": str(arq), "familia": "gravura-ouro"}
    sem = familia.pertence(e, fam, escala_uso=560)
    com = familia.pertence(e, dict(fam, traco_px_min=0.75), escala_uso=560)
    teto = familia.pertence(e, dict(fam, traco_px_min=0.75, traco_px_max=0.8), escala_uso=560)
    print(f"   par de asas a 560 px: {sem['medidas'].get('traco_px_uso')} px; sem piso próprio {sem['pertence']}, com 0,75 {com['pertence']}")
    assert not sem["pertence"] and any(m.startswith("traço") for m in sem["motivos"]), sem
    assert com["pertence"], com
    assert not teto["pertence"], "o teto próprio também tem de valer"


def test_qa_conjunto_aceita_membro_revisado_so_no_mesmo_arquivo():
    """`familia_revisada` (aceito pelo Ugo apesar da medida) troca a FALHA de família por AVISO, só para o arquivo de
    sha256 registrado; arquivo trocado volta a reprovar."""
    import qa_conjunto
    kit = pasta_sprint(); fx = fixture()
    with tempfile.TemporaryDirectory() as d:
        d = Path(d); (d / "acervo" / "elementos").mkdir(parents=True); (d / "saida").mkdir()
        arr = np.asarray(Image.open(kit / "acervo" / "elementos" / "medalha-alada.png").convert("RGBA"))
        azul = d / "acervo" / "elementos" / "medalha-azul.png"; Image.fromarray(familia._recolorir(arr, 212), "RGBA").save(azul)
        el = {"id": "medalha-azul", "papel": "heroi", "tipo": "objeto", "formato": "png", "familia": "objeto-dourado",
              "motivo": "medalha", "arquivo": "acervo/elementos/medalha-azul.png", "kit_origem": "sprint-2027", "exclusivo_cliente": None}
        sis = dict(fx["sistema_elementos"], receitas={"r3": fx["sistema_elementos"]["receitas"]["r3"]})
        plano = {"receita": "r3", "paginas": [{"n": 1, "rotulo": "cota:b", "tipo": "cota", "elementos": [dict(id="medalha-azul", papel="heroi", w=420)]}]}
        (d / "saida" / "plano-elementos-r3.json").write_text(json.dumps(plano), encoding="utf-8")
        def roda(e):
            k = {"cliente": "SPRINT UBATUBA RUN", "kit": "sprint-2027", "sistema_elementos": sis, "elementos": [e]}
            return [(n, m) for n, m in qa_conjunto.checar(d, k) if "medalha-azul" in m and "fam" in m]
        sem = roda(el)
        assert any(n == "FALHA" and "fora da família" in m for n, m in sem), sem
        rev = {"por": "Ugo", "em": "2026-10-09", "motivo": "prova", "sha256": familia.sha256(azul)}
        com = roda(dict(el, familia_revisada=rev))
        assert not any(n == "FALHA" for n, m in com) and any(n == "AVISO" and "aceito por Ugo" in m for n, m in com), com
        errado = roda(dict(el, familia_revisada=dict(rev, sha256="0" * 64)))
        assert any(n == "FALHA" and "outro arquivo" in m for n, m in errado), errado


def test_aprovacao_grava_sha256_e_cai_quando_um_membro_muda():
    kit_real = pasta_sprint(); els, fams = elementos_e_familias()
    with tempfile.TemporaryDirectory() as d:
        d = Path(d); (d / "acervo" / "elementos").mkdir(parents=True)
        membros = [e for e in els if e["id"] in ("medalha-alada", "tenis-usado")]
        for e in membros:
            shutil.copyfile(kit_real / e["arquivo"], d / e["arquivo"])       # cópia: o arquivo real não é tocado
        k = {"kit": "teste-aprovacao", "cliente": "SPRINT UBATUBA RUN",
             "sistema_elementos": {"motivos": [], "familias": [dict(fams["objeto-dourado"])], "constantes": [], "receitas": {}},
             "elementos": membros}
        (d / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False), encoding="utf-8")
        ap = familia.aprovar(d, "objeto-dourado", "Ugo")
        k = json.loads((d / "mediakit.json").read_text(encoding="utf-8"))
        assert len(ap["sha256_membros"]) == 2 and familia.aprovacao_valida(k, d, "objeto-dourado")[0]
        folha = familia.folha_familia(d, "objeto-dourado", d / "folha-familia.png")
        assert folha.stat().st_size > 10_000
        im = Image.open(d / membros[1]["arquivo"]).convert("RGBA"); px = im.load(); px[0, 0] = (1, 2, 3, 255); im.save(d / membros[1]["arquivo"])
        ok, msg = familia.aprovacao_valida(k, d, "objeto-dourado")
        print(f"   aprovada com {len(ap['sha256_membros'])} sha256; depois de mudar 1 pixel do tenis-usado: {ok}, {msg}")
        assert not ok and "caiu" in msg


if __name__ == "__main__":
    falhou = pulou = 0
    for nome, fn in list(globals().items()):
        if nome.startswith("test_"):
            try:
                fn(); print("ok  ", nome)
            except Pulado as e:
                pulou += 1; print("pulado", nome, e)
            except AssertionError as e:
                falhou += 1; print("FALHOU", nome, e)
    print("PROVAS:", ("VERDES" if not falhou else f"{falhou} FALHA(S)") + (f" ({pulou} pulada(s))" if pulou else ""))
    sys.exit(1 if falhou else 0)

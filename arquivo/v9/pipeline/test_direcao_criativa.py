#!/usr/bin/env python3
"""
test_direcao_criativa.py: prova de ponta a ponta do fluxo mk-2.1 da SKILL v9 (etapa 3b, a direção criativa, e etapa 9, a
folha de acabamento) no kit fictício exemplos/acabamento-prova. O kit é clonado por APFS (cp -c) numa pasta temporária fora
do git: o kit rastreado nunca é escrito. Sem pytest.

  ~/.venvs/mediakit/bin/python pipeline/test_direcao_criativa.py [nome-da-prova ...] [--manter]

As provas seguem a ordem do fluxo e dividem o mesmo clone (uma roda depois da outra):
 1. leitura_vira_consulta (3b.1 e 3b.2): o direcao-criativa.md com a Leitura em 4 linhas; `repertorio.py consultar` grava
    consulta-repertorio.json (sha256 do índice atual, as 4 linhas, uma consulta por família) e mood/consulta-recursos.png.
    Mutante: sem o direcao-criativa.md a consulta sai sem leitura, e a conferência acusa.
 2. qa_reprova_sem_consulta (3b.2): `qa.py` no kit renderizado sem consulta-repertorio.json traz a FALHA da consulta;
    depois do `consultar`, nem a FALHA nem o aviso de índice antigo, e o resto do relatório não muda. Mutantes, pelo
    qa_conjunto e sem render: a consulta com o sha256 de outro índice avisa; ilegível reprova; sem sha avisa; o mesmo kit
    em mk-2.0 sem a consulta só avisa (inverso).
 3. escolha_e_usados (3b.3 e etapa 11): a escolha troca a referência de cada recurso pela que a consulta trouxe (ou por um
    padrão do índice) e escreve os padrões na composição; as 7 FALHAS de referência fora do índice caem a 0, e `repertorio.py
    usados --json` devolve exatamente os padrões e os recursos que o kit declara. Mutantes: padrão que não existe sai em
    `desconhecidos`; padrão tirado de uma página some da lista dela; a referência fictícia volta a reprovar.
 4. estudo_ab_grava_png (3b.4): `contact_sheet.py --estudo objeto-no-piso` grava estudos/objeto-no-piso.png com os
    recortes do recurso do repertório e a página da cota. Mutantes: recurso fora da direção, id com caminho, referência
    fictícia (sem recorte) e recurso que nenhuma página usa saem com 1 e não gravam nada.
 5. folha_de_acabamento_grava_png (etapa 9): `contact_sheet.py --acabamento` (e --pdf) grava saida/acabamento-r1.png, uma
    linha por página, com os recursos que a página declara e o recorte de cada um. Mutantes: página composta sem
    `acabamento` sai marcada; recurso de referência fictícia sai em `sem_recorte`.
O render roda uma vez (cerca de 40 s) e o qa.py duas (cerca de 50 s cada). Sai com 1 se alguma prova falhar. As cópias
temporárias são apagadas no fim (com --manter, ficam para inspeção e o caminho sai no log).
"""
import hashlib, json, shutil, subprocess, sys, tempfile, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import acabamento, contact_sheet, qa_conjunto  # noqa: E402

PY = sys.executable
KIT = AQUI.parent / "exemplos" / "acabamento-prova"
REP = AQUI.parent / "repertorio"
INDICE = REP / "indice.json"
BASE = Path(tempfile.gettempdir()) / f"mk-direcao-criativa-{hashlib.sha1(str(AQUI).encode()).hexdigest()[:8]}"
CLONE = BASE / "kit"
RECEITA = "r1"
# a Leitura (3b.1): 4 linhas, cada uma termina numa consequência visual
LEITURA = [
    "Corrida noturna de rua sob a lua cheia: a luz vem de lado, então o objeto ganha sombra de contato e brilho de metal.",
    "A medalha é o prêmio de quem termina: ela cruza o título na capa e pousa num piso na cota.",
    "O percurso atravessa a cidade apagada: a pista vira malha em perspectiva e hachura de impresso nos dados.",
    "Tom performance, de quem corre à noite: grão forte nos dados e o título em camadas na capa.",
]
DIRECAO_MD = ("# Direção criativa: Travessia da Lua (fictícia)\n\n## Leitura\n" + "".join(f"- {l}\n" for l in LEITURA)
              + "\n## Escolha\nOs recursos e o porquê de cada um ficam no mediakit.json (direcao_criativa).\n")
MSG_SEM_CONSULTA = "sem a consulta ao repertório gravada"
MSG_INDICE_ANTIGO = "foi feita sobre outro índice do repertório"
MSG_REF_FORA = "que não está no índice do repertório"
# 3b.3: quando a consulta não trouxe recurso da família, a origem é um padrão do repertório (copiar o princípio)
PADRAO_DA_ESCOLHA = {"eco-do-titulo": "palavra-gigante-atras-da-figura", "objeto-cruza-titulo": "figura-recortada-atravessa-a-borda",
                     "malha-perspectiva": "grafismo-do-equipamento-do-esporte", "objeto-no-piso": "peca-em-estudio",
                     "foto-chanfrada": "costura-foto-painel", "hachura-sob-numero": "textura-tom-sobre-tom",
                     "figura-em-registro": "figura-recortada-atravessa-a-borda"}
PADROES_DA_COMPOSICAO = {"capa": ["palavra-gigante-atras-da-figura", "figura-recortada-atravessa-a-borda"],
                         "cota": ["peca-em-estudio"], "prova": ["numeral-heroi-com-legenda-travada", "textura-tom-sobre-tom"]}
_ESTADO = {}


def teste(fn):
    fn._teste = True
    return fn


def log(*a):
    print("   ", *a, flush=True)


def ler(pasta):
    return json.loads((Path(pasta) / "mediakit.json").read_text(encoding="utf-8"))


def gravar(pasta, k):
    (Path(pasta) / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def rodar(*args):
    return subprocess.run([PY, *map(str, args)], capture_output=True, text=True, cwd=str(AQUI))


def clonar(origem, destino):
    """Clone APFS da pasta (o tempfile não é rastreado); o clone do kit rastreado sai sem saida/, consulta, mood e estudos."""
    if destino.exists():
        shutil.rmtree(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cp", "-cR", str(origem), str(destino)], check=True)
    if origem == KIT:
        for nome in ("saida", "mood", "estudos"):
            shutil.rmtree(destino / nome, ignore_errors=True)
        (destino / "consulta-repertorio.json").unlink(missing_ok=True)
    return destino


def kit_renderizado():
    """O clone do kit, sem consulta, renderizado uma vez (--png --fontes)."""
    if _ESTADO.get("render"):
        return CLONE
    clonar(KIT, CLONE)
    r = rodar(AQUI / "render.py", CLONE, "--png", "--fontes", CLONE / "fontes")
    assert r.returncode == 0, f"render saiu com {r.returncode}: {(r.stdout + r.stderr)[-1200:]}"
    _ESTADO["render"] = True
    return CLONE


def linhas_qa(saida):
    return [l for l in saida.splitlines() if l.startswith(("FALHA", "AVISO"))]


def conferir_consulta(reg):
    """O que a consulta gravada precisa ter para a 3b.2 valer: o sha256 do índice ATUAL, a Leitura do direcao-criativa.md
    inteira, uma consulta por família do contrato e os tipos de página do kit. Devolve a lista de problemas."""
    prob = []
    if reg.get("indice_sha256") != hashlib.sha256(INDICE.read_bytes()).hexdigest():
        prob.append("indice_sha256 não é o do índice atual")
    lei = reg.get("leitura") or {}
    if lei.get("linhas") != LEITURA or not str(lei.get("fonte") or "").startswith("direcao-criativa.md (seção Leitura)"):
        prob.append(f"leitura gravada não é a do direcao-criativa.md: {lei}")
    fams = [c.get("familia") for c in reg.get("consultas") or []]
    if fams != list(acabamento.FAMILIAS):
        prob.append(f"consultas por família {fams}, o contrato tem {list(acabamento.FAMILIAS)}")
    if not {"capa", "cota", "prova"} <= set(reg.get("tipos_pagina") or []):
        prob.append(f"tipos de página {reg.get('tipos_pagina')}")
    return prob


def consultar(pasta, com_leitura=True):
    if com_leitura:
        (Path(pasta) / "direcao-criativa.md").write_text(DIRECAO_MD, encoding="utf-8")
    else:
        (Path(pasta) / "direcao-criativa.md").unlink(missing_ok=True)
    r = rodar(AQUI / "repertorio.py", "consultar", pasta)
    assert r.returncode == 0, f"consultar saiu com {r.returncode}: {(r.stdout + r.stderr)[-800:]}"
    return json.loads((Path(pasta) / "consulta-repertorio.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------- 3b.1 e 3b.2
@teste
def leitura_vira_consulta():
    from PIL import Image
    d = clonar(KIT, BASE / "leitura")
    reg = consultar(d)
    assert conferir_consulta(reg) == [], conferir_consulta(reg)
    folha = d / "mood" / "consulta-recursos.png"
    assert folha.is_file() and Image.open(folha).size[0] > 0, "mood/consulta-recursos.png não foi gravada"
    log(f"consulta gravada: sha256 {reg['indice_sha256'][:12]}... (o do índice atual), 4 linhas da Leitura, "
        f"{len(reg['consultas'])} famílias, {len(reg['ids'])} recurso(s) em ids, folha {folha.name}")
    # mutante: sem o direcao-criativa.md a consulta sai sem leitura, e a conferência acusa
    m = clonar(KIT, BASE / "leitura-mutante")
    reg_m = consultar(m, com_leitura=False)
    prob = conferir_consulta(reg_m)
    assert any("leitura" in p for p in prob), f"a consulta sem Leitura passou na conferência: {reg_m.get('leitura')}"
    log(f"mutante sem direcao-criativa.md: leitura {reg_m['leitura']} e a conferência acusa")


@teste
def qa_reprova_sem_consulta():
    pasta = kit_renderizado()
    antes = rodar(AQUI / "qa.py", pasta)
    la = linhas_qa(antes.stdout)
    sem = [l for l in la if l.startswith("FALHA") and MSG_SEM_CONSULTA in l]
    assert antes.returncode == 1 and sem, f"qa.py sem consulta-repertorio.json não reprovou pela consulta: {la[-12:]}"
    reg = consultar(pasta)
    assert conferir_consulta(reg) == [], conferir_consulta(reg)
    depois = rodar(AQUI / "qa.py", pasta)
    ld = linhas_qa(depois.stdout)
    assert not [l for l in ld if MSG_SEM_CONSULTA in l or MSG_INDICE_ANTIGO in l], [l for l in ld if "consulta" in l]
    sumiu = sorted(set(la) - set(ld))
    apareceu = sorted(set(ld) - set(la))
    assert sumiu == sem and not apareceu, f"a consulta mudou mais que a regra dela: sumiu {sumiu}, apareceu {apareceu}"
    nf = lambda ls: sum(1 for l in ls if l.startswith("FALHA"))  # noqa: E731
    log(f"qa.py sem consulta: {nf(la)} falha(s), uma delas a da consulta; depois do consultar: {nf(ld)} (só ela saiu; "
        f"as outras são do kit fictício: referências ficticio:*, família, novidade)")
    # mutantes sem render (qa_conjunto.checar_consulta, a mesma função que o qa.py chama)
    k = ler(pasta)
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        c = t / "consulta-repertorio.json"
        c.write_text(json.dumps({"indice_sha256": "983ee819f183324371d21040477daec4560a3a916e13d6b2307aa0167b27fc5e"}), encoding="utf-8")
        r = qa_conjunto.checar_consulta(t, k)
        assert [n for n, m in r if n == "AVISO" and MSG_INDICE_ANTIGO in m] and not [n for n, _ in r if n == "FALHA"], r
        c.write_text("{", encoding="utf-8")
        r = qa_conjunto.checar_consulta(t, k)
        assert [m for n, m in r if n == "FALHA" and "ilegível" in m], r
        c.write_text("{}", encoding="utf-8")
        r = qa_conjunto.checar_consulta(t, k)
        assert [m for n, m in r if n == "AVISO" and "indice_sha256" in m], r
        c.unlink()
        r = qa_conjunto.checar_consulta(t, k)
        assert [m for n, m in r if n == "FALHA" and MSG_SEM_CONSULTA in m], r
        k20 = dict(k, schema_version="mk-2.0")
        r = qa_conjunto.checar_consulta(t, k20)
        assert r and all(n == "AVISO" for n, _ in r), f"inverso mk-2.0: {r}"
    log("mutantes: sha de outro índice avisa, ilegível reprova, sem sha avisa, sem arquivo reprova; inverso mk-2.0 só avisa")


# ------------------------------------------------------------------------------------------------- 3b.3 e etapa 11
def escolher(pasta):
    """A escolha da 3b.3 no clone: a referência de cada recurso vem da consulta (o primeiro id da família dele) ou de um
    padrão do índice; a composição ganha os padrões. Devolve o kit gravado."""
    reg = json.loads((pasta / "consulta-repertorio.json").read_text(encoding="utf-8"))
    por_familia = {c["familia"]: [x["id"] for x in c["resultados"]] for c in reg["consultas"]}
    ind = json.loads(INDICE.read_text(encoding="utf-8"))
    padroes = {p["id"] for p in ind["padroes"]}
    k = ler(pasta)
    for r in k["direcao_criativa"]["recursos"]:
        r["referencia"] = (por_familia.get(r["familia"]) or [PADRAO_DA_ESCOLHA[r["id"]]])[0]
    for chave, pids in PADROES_DA_COMPOSICAO.items():
        k["composicao"][chave]["padroes"] = pids
    assert {r["referencia"] for r in k["direcao_criativa"]["recursos"]} <= padroes | {x["id"] for x in ind.get("recursos") or []}
    gravar(pasta, k)
    return k


@teste
def escolha_e_usados():
    pasta = kit_renderizado()
    if not (pasta / "consulta-repertorio.json").is_file():
        consultar(pasta)
    k0 = ler(pasta)
    fora_antes = [m for n, m in qa_conjunto.checar_recursos(k0) if n == "FALHA" and MSG_REF_FORA in m]
    k = escolher(pasta)
    fora_depois = [m for n, m in qa_conjunto.checar_recursos(k) if n == "FALHA"]
    assert len(fora_antes) == len(k0["direcao_criativa"]["recursos"]) and fora_depois == [], (len(fora_antes), fora_depois)
    log(f"escolha: {len(fora_antes)} FALHAS de referência fora do índice antes (ficticio:*), {len(fora_depois)} depois")
    r = rodar(AQUI / "repertorio.py", "usados", pasta, "--json")
    assert r.returncode == 0, r.stderr[-600:]
    u = json.loads(r.stdout)
    esperado_p = {}
    for chave, pids in PADROES_DA_COMPOSICAO.items():
        for pid in pids:
            esperado_p.setdefault(pid, []).append(chave)
    esperado_r = {x["id"]: [] for x in k["direcao_criativa"]["recursos"]}
    for chave, ent in k["composicao"].items():
        for rid in qa_conjunto.recursos_da_entrada(ent):
            esperado_r.setdefault(rid, []).append(chave)
    assert u["padroes"] == {p: esperado_p[p] for p in sorted(esperado_p)}, u["padroes"]
    assert u["desconhecidos"] == [], u["desconhecidos"]
    assert u["recursos"] == {x: esperado_r[x] for x in sorted(esperado_r)}, u["recursos"]
    log(f"usados: {len(u['padroes'])} padrões e {len(u['recursos'])} recursos, cada um com as páginas que o kit declara")
    # mutantes: padrão inexistente; padrão tirado de uma página
    with tempfile.TemporaryDirectory() as t:
        km = json.loads(json.dumps(k))
        km["composicao"]["divisor"]["padroes"] = ["padrao-que-nao-existe"]
        km["composicao"]["capa"]["padroes"] = ["palavra-gigante-atras-da-figura"]
        gravar(t, km)
        um = json.loads(rodar(AQUI / "repertorio.py", "usados", t, "--json").stdout)
        assert um["desconhecidos"] == ["padrao-que-nao-existe"], um["desconhecidos"]
        assert "figura-recortada-atravessa-a-borda" not in um["padroes"], um["padroes"]
        km["direcao_criativa"]["recursos"][0]["referencia"] = "ficticio:volta"
        assert [m for n, m in qa_conjunto.checar_recursos(km) if n == "FALHA" and MSG_REF_FORA in m], "referência fictícia passou"
    log("mutantes: padrão inexistente em desconhecidos; padrão tirado da capa some; referência fictícia volta a reprovar")


# ------------------------------------------------------------------------------------------------- 3b.4 e etapa 9
def _png_ok(arq):
    from PIL import Image
    assert Path(arq).is_file(), f"{arq} não foi gravado"
    with Image.open(arq) as im:
        assert im.format == "PNG" and im.size[0] > 1000 and im.size[1] > 400, (im.format, im.size)
        return im.size


@teste
def estudo_ab_grava_png():
    pasta = kit_renderizado()
    if not (pasta / "consulta-repertorio.json").is_file():
        consultar(pasta)
    k = escolher(pasta)
    rec = next(r for r in k["direcao_criativa"]["recursos"] if r["id"] == "objeto-no-piso")
    r = rodar(AQUI / "contact_sheet.py", pasta, "--estudo", "objeto-no-piso")
    assert r.returncode == 0, (r.stdout + r.stderr)[-800:]
    tam = _png_ok(pasta / "estudos" / "objeto-no-piso.png")
    res = contact_sheet.estudo(pasta, "objeto-no-piso")
    ind = json.loads(INDICE.read_text(encoding="utf-8"))
    origem = next(x for x in (ind.get("recursos") or []) + ind["padroes"] if x["id"] == rec["referencia"])
    dela = {str((REP / y).resolve()) for x in origem["recortes"] for y in (x.get("anotado"), x.get("arquivo")) if y}
    assert res["recortes"] and set(res["recortes"]) <= dela, (res["recortes"], rec["referencia"])
    assert res["paginas"] == ["cota:a"], res["paginas"]
    reg = res["detalhes"][0]["regiao"]
    assert 0 <= reg[0] < reg[2] <= 1920 and 0 <= reg[1] < reg[3] <= 1080 and (reg[2] - reg[0]) * (reg[3] - reg[1]) < 1920 * 1080 / 2, reg
    log(f"estudo A/B: {tam[0]}x{tam[1]} px, {len(res['recortes'])} recorte(s) de `{rec['referencia']}`, página {res['paginas']}, "
        f"detalhe {reg}")
    # mutantes: cada um sai com 1 e não grava
    m = clonar(pasta, BASE / "estudo-mutante")
    km = ler(m)
    km["direcao_criativa"]["recursos"].append({"id": "recurso-sem-pagina", "familia": "acabamento-borda", "rota": "codigo",
                                               "referencia": "moldura-contorno-e-cantoneiras",
                                               "principio": "cantoneiras presas aos cantos do bloco de preço"})
    next(r for r in km["direcao_criativa"]["recursos"] if r["id"] == "foto-chanfrada")["referencia"] = "ficticio:sem-recorte"
    gravar(m, km)
    casos = [("nao-esta-na-direcao", "não está em direcao_criativa.recursos"), ("../fora", "não é um id de recurso"),
             ("foto-chanfrada", "não tem recorte no repertório"), ("recurso-sem-pagina", "nenhuma página")]
    for rid, msg in casos:
        rm = rodar(AQUI / "contact_sheet.py", m, "--estudo", rid)
        assert rm.returncode == 1 and msg in (rm.stdout + rm.stderr), (rid, rm.returncode, (rm.stdout + rm.stderr)[-300:])
        assert not (m / "estudos" / f"{rid}.png").exists() and not (m / "fora.png").exists(), rid
    log("mutantes: fora da direção, id com caminho, referência sem recorte e recurso sem página saem com 1, sem arquivo")


@teste
def folha_de_acabamento_grava_png():
    pasta = kit_renderizado()
    if not (pasta / "consulta-repertorio.json").is_file():
        consultar(pasta)
    k = escolher(pasta)
    res = contact_sheet.folha_acabamento(pasta)
    tam = _png_ok(res["arquivo"])
    plano = json.loads((pasta / "saida" / f"plano-elementos-{RECEITA}.json").read_text(encoding="utf-8"))
    assert [p["n"] for p in res["paginas"]] == [p["n"] for p in plano["paginas"]], res["paginas"]
    for p, pg in zip(res["paginas"], plano["paginas"]):
        ent = k["composicao"][p["chave"]]
        esperado = list(dict.fromkeys(qa_conjunto.recursos_da_entrada(ent)
                                      + [it["recurso"] for it in pg["elementos"] if isinstance(it.get("recurso"), str)]))
        assert p["recursos"] == esperado, (p["rotulo"], p["recursos"], esperado)
        assert p["intensidade"] == list(qa_conjunto.intensidade(ent, k)), (p["rotulo"], p["intensidade"])
        assert p["sem_recorte"] == [] and all(p["recortes"][r] for r in esperado[:3]), (p["rotulo"], p["recortes"])
        assert not p["sem_acabamento"], p
    r = rodar(AQUI / "contact_sheet.py", pasta, "--acabamento", "--pdf")
    assert r.returncode == 0, (r.stdout + r.stderr)[-800:]
    tam_pdf = _png_ok(pasta / "saida" / f"acabamento-{RECEITA}-pdf.png")
    assert tam_pdf == tam, (tam_pdf, tam)
    log(f"folha de acabamento: {tam[0]}x{tam[1]} px, {len(res['paginas'])} páginas, cada recurso com o recorte da origem; "
        f"a mesma folha sobre o raster do PDF entregue")
    # mutantes: página sem `acabamento`; recurso com referência fictícia
    m = clonar(pasta, BASE / "folha-mutante")
    km = ler(m)
    km["composicao"]["prova"].pop("acabamento")
    next(r for r in km["direcao_criativa"]["recursos"] if r["id"] == "eco-do-titulo")["referencia"] = "ficticio:sem-recorte"
    gravar(m, km)
    rm = contact_sheet.folha_acabamento(m)
    por = {p["chave"]: p for p in rm["paginas"]}
    assert por["prova"]["sem_acabamento"] and por["capa"]["sem_recorte"] == ["eco-do-titulo"], (por["prova"], por["capa"])
    assert not por["cota"]["sem_acabamento"] and por["cota"]["sem_recorte"] == [], por["cota"]
    log("mutantes: a prova sem `acabamento` sai marcada; o eco com referência fictícia sai sem recorte")


# ================================================================================================= execução
def main():
    nomes = [a for a in sys.argv[1:] if not a.startswith("--")]
    testes = [(n, f) for n, f in globals().items() if callable(f) and getattr(f, "_teste", False)]
    if nomes:
        desconhecidos = [n for n in nomes if n not in dict(testes)]
        if desconhecidos:
            sys.exit(f"prova(s) que não existem: {', '.join(desconhecidos)} (as provas: {', '.join(n for n, _ in testes)})")
        testes = [(n, f) for n, f in testes if n in nomes]
    falhou = 0
    try:
        for n, f in testes:
            t0 = time.time()
            try:
                f()
                print(f"OK      {n}  ({time.time() - t0:.1f} s)", flush=True)
            except Exception as e:
                falhou += 1
                print(f"FALHOU  {n}  ({time.time() - t0:.1f} s): {type(e).__name__}: {str(e)[:900]}", flush=True)
    finally:
        if "--manter" in sys.argv:
            print(f"cópias mantidas em {BASE}")
        else:
            shutil.rmtree(BASE, ignore_errors=True)
    print(f"\n{len(testes) - falhou} de {len(testes)} testes passaram")
    print("PROVAS:", "VERDES" if not falhou else f"{falhou} FALHA(S)")
    sys.exit(1 if falhou else 0)


if __name__ == "__main__":
    main()

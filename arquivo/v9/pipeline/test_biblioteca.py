#!/usr/bin/env python3
"""Provas do biblioteca.py e da regra de exclusividade do qa_conjunto.py. Rodar: ~/.venvs/mediakit/bin/python
test_biblioteca.py. Monta numa pasta temporária um kit com a fixture da Sprint e um atalho (só leitura) para o acervo real,
registra os 6 elementos numa biblioteca temporária e trabalha em cópias: não escreve na biblioteca de verdade nem no kit
do cliente. Sem o acervo real, as provas saem como 'pulado'."""
import atexit, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

from PIL import Image

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import biblioteca  # noqa: E402
import plano_elementos as pe  # noqa: E402
import qa_conjunto  # noqa: E402
from test_familia import Pulado, pasta_sprint, FIXTURE  # noqa: E402
from test_plano_elementos import catalogo, paginas, SEQ_TESTE, falhas  # noqa: E402

INDICE_REAL = biblioteca.PADRAO / "INDICE.md"
EXCLUSIVOS = {"penas-asa", "pena-dourada", "medalha-alada"}
_TMP = Path(tempfile.mkdtemp(prefix="mk-bib-provas-"))
atexit.register(shutil.rmtree, _TMP, True)
_CACHE = {}


def indice_original():
    """O INDICE.md real como o carrossel escreveu: sem o bloco gerado, se ele já estiver lá."""
    if not INDICE_REAL.is_file():
        raise Pulado(f"{INDICE_REAL} não existe")
    t = INDICE_REAL.read_text(encoding="utf-8")
    return re.sub(r"\n" + re.escape(biblioteca.INICIO) + r".*?" + re.escape(biblioteca.FIM) + r"\n", "", t, flags=re.S)


def kit_sprint():
    if "kit" not in _CACHE:
        real = pasta_sprint()
        kit = _TMP / "sprint-2027"; kit.mkdir()
        shutil.copyfile(FIXTURE, kit / "mediakit.json")
        (kit / "acervo").symlink_to(real / "acervo")          # só leitura: o registrar não escreve no kit
        _CACHE["kit"] = kit
    return _CACHE["kit"]


def biblioteca_sprint():
    if "bib" not in _CACHE:
        bib = _TMP / "bib-base"; bib.mkdir()
        (bib / "INDICE.md").write_text(indice_original(), encoding="utf-8")
        biblioteca.registrar(kit_sprint(), bib=bib)
        _CACHE["bib"] = bib
    return _CACHE["bib"]


def copia(nome):
    destino = _TMP / nome
    shutil.copytree(biblioteca_sprint(), destino)
    return destino


def test_registrar_separa_exclusivos_e_e_idempotente():
    bib = copia("bib-registrar")
    ind = biblioteca.carregar(bib); its = {i["id"]: i for i in ind["itens"]}
    assert set(its) == {"penas-asa", "ondas-serra", "pena-dourada", "folha-amendoeira", "medalha-alada", "tenis-usado"}, set(its)
    for iid, it in sorted(its.items()):
        print(f"   {iid:18s} {it['arquivo']:52s} bruto={bool(it.get('bruto'))!s:5s} meio={it['meio']:12s} aspecto={it['aspecto']}")
        assert (bib / it["arquivo"]).is_file()
        if iid in EXCLUSIVOS:
            assert it["arquivo"] == f"_EXCLUSIVOS/SPRINT UBATUBA RUN/{iid}.png" and it["exclusivo_cliente"] == "SPRINT UBATUBA RUN", it
        else:
            assert "/" not in it["arquivo"] and it["exclusivo_cliente"] is None, it
    assert {i for i, it in its.items() if it.get("bruto")} == {"penas-asa", "ondas-serra"}   # só o bruto que difere do final
    assert its["penas-asa"]["costura"] == 0.24 and its["ondas-serra"]["costura"] == 0.0
    assert not [m for n, m in biblioteca.checar(bib) if n == "FALHA"], biblioteca.checar(bib)
    antes = (bib / "indice.json").read_bytes()
    biblioteca.registrar(kit_sprint(), bib=bib)
    assert (bib / "indice.json").read_bytes() == antes, "registrar de novo mudou o indice.json"
    mb = sum(f.stat().st_size for f in bib.rglob("*") if f.is_file()) / 1e6
    print(f"   biblioteca: {len(its)} itens, {mb:.1f} MB; segunda rodada não mudou nada")


def test_sincronizar_preserva_bola_e_fila_e_checar_acusa_bola():
    bib = copia("bib-sincronizar")
    original = indice_original()
    (bib / "INDICE.md").write_text(original, encoding="utf-8")
    linha_bola = next(l for l in original.splitlines() if l.startswith("| `bola-futebol-couro.png`"))
    fila = original[original.index("## Fila"):]
    novos, mudou = biblioteca.sincronizar(bib)
    texto = (bib / "INDICE.md").read_text(encoding="utf-8")
    assert novos == ["bola-futebol-couro"] and mudou
    assert texto.count(biblioteca.INICIO) == 1 and texto.count(biblioteca.FIM) == 1
    fora = re.sub(r"\n" + re.escape(biblioteca.INICIO) + r".*?" + re.escape(biblioteca.FIM) + r"\n", "", texto, flags=re.S)
    assert fora == original, "o que está fora dos marcadores mudou"
    assert linha_bola in texto and texto.endswith(fila)
    bloco = texto[texto.index(biblioteca.INICIO):texto.index(biblioteca.FIM)]
    assert "\u2014" not in bloco and "\u2013" not in bloco, "travessão no bloco gerado"
    assert "`_EXCLUSIVOS/SPRINT UBATUBA RUN/medalha-alada.png`" in bloco.split("### Exclusivos")[1]
    assert "medalha-alada" not in bloco.split("### Exclusivos")[0]          # exclusivo fora da tabela principal
    assert biblioteca.sincronizar(bib) == ([], False), "segunda sincronização mudou o arquivo"
    bola = biblioteca.item(biblioteca.carregar(bib), "bola-futebol-couro")
    assert bola["rota"] == "manual" and bola["prompt_texto"].startswith("Professional soccer ball"), bola
    f = [m for n, m in biblioteca.checar(bib) if n == "FALHA"]
    print("   checar:", f)
    assert any("bola-futebol-couro" in m and "arquivo ausente" in m for m in f), f
    # linha nova escrita à mão pelo carrossel, fora dos marcadores: entra no índice na próxima sincronização
    texto = texto.replace(linha_bola, linha_bola + "\n| `cone-treino.png` | Cone de treino laranja | Higgsfield (10/10/2026) | mk-020 (S03) |")
    (bib / "INDICE.md").write_text(texto, encoding="utf-8")
    assert biblioteca.sincronizar(bib)[0] == ["cone-treino"]
    cone = biblioteca.item(biblioteca.carregar(bib), "cone-treino")
    assert cone["data"] == "2026-10-10" and cone["usos"][0]["kit"] == "mk-020 (S03)" and cone["usos"][0]["sistema"] == "carrossel"
    assert "cone-treino.png` | Cone de treino laranja" in (bib / "INDICE.md").read_text(encoding="utf-8")


def test_buscar_nunca_devolve_exclusivo_de_outro_cliente():
    bib = biblioteca_sprint(); ind = biblioteca.carregar(bib)
    consultas = [{}, {"motivo": "medalha"}, {"motivo": "penas"}, {"tipo": "objeto"}, {"tipo": "pattern"},
                 {"estilo": "gold feather wing medal"}, {"meio": "foto-objeto"}, {"tags": ["sprint", "asa"]}]
    for q in consultas:
        for cliente in ("AME CRIANCA", "ame criança", None):
            ids = [r["item"]["id"] for r in biblioteca.buscar(ind, bib, cliente=cliente, **q)]
            assert not set(ids) & EXCLUSIVOS, (q, cliente, ids)
    # não é prova vazia: para o dono, o mesmo filtro devolve a medalha em primeiro
    dono = biblioteca.buscar(ind, bib, motivo="medalha", cliente="Sprint Ubatuba Run")
    assert dono and dono[0]["item"]["id"] == "medalha-alada", [r["item"]["id"] for r in dono]
    saida = _TMP / "candidatas.png"
    r = subprocess.run([sys.executable, str(AQUI / "biblioteca.py"), "buscar", "--tipo", "objeto", "--cliente", "AME CRIANCA",
                        "--folha", str(saida), "--biblioteca", str(bib)], capture_output=True, text=True)
    print("  ", r.stdout.strip().replace("\n", "\n   "))
    assert r.returncode == 0 and saida.is_file() and not EXCLUSIVOS & set(re.findall(r"[a-z-]+", r.stdout))


def _kit_ame(nome, com_medalha=True, declarar=True, tirar_do_json=False):
    bib = biblioteca_sprint(); kit = _TMP / nome
    (kit / "acervo" / "elementos").mkdir(parents=True)
    fx = json.loads(FIXTURE.read_text(encoding="utf-8")); fam = next(f for f in fx["sistema_elementos"]["familias"] if f["id"] == "objeto-dourado")
    sis = {"motivos": [{"id": "medalha", "origem": "esporte", "descricao": "medalha"}, {"id": "pista", "origem": "esporte", "descricao": "pista"},
                       {"id": "brinquedo", "origem": "territorio", "descricao": "brinquedo"}],
           "familias": [fam], "constantes": [{"tipo": "grao"}, {"tipo": "microtexto", "texto": "AME", "encaixe": "borda-base"}],
           "receitas": {"r1": {"familia": "objeto-dourado", "motivos": ["medalha", "pista"], "pattern": None}}, "excecoes": {}}
    els = []
    for iid, arq in (("tenis-usado", "tenis-usado.png"), ("medalha-alada", "_EXCLUSIVOS/SPRINT UBATUBA RUN/medalha-alada.png")):
        if iid == "medalha-alada" and not com_medalha:
            continue
        shutil.copyfile(bib / arq, kit / "acervo" / "elementos" / f"{iid}.png")   # cópia à mão, por fora do `usar`
        e = {"id": iid, "papel": "heroi", "tipo": "objeto", "formato": "png", "familia": "objeto-dourado",
             "motivo": "medalha" if iid == "medalha-alada" else "pista", "arquivo": f"acervo/elementos/{iid}.png",
             "kit_origem": "sprint-2027", "exclusivo_cliente": ("SPRINT UBATUBA RUN" if declarar and iid == "medalha-alada" else None),
             "gerado": True, "rota": "biblioteca"}
        els.append(e)
    plano = pe.plano_provisorio(sis, els, "r1", paginas(SEQ_TESTE), catalogo())
    assert com_medalha is False or any(x["id"] == "medalha-alada" for pg in plano["paginas"] for x in pg["elementos"])
    (kit / "saida").mkdir(); (kit / "saida" / "plano-elementos-r1.json").write_text(json.dumps(plano), encoding="utf-8")
    if tirar_do_json:
        els = [e for e in els if e["id"] != "medalha-alada"]
    k = {"kit": "ame-crianca-2027", "cliente": "AME CRIANCA", "sistema_elementos": sis, "elementos": els}
    (kit / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False), encoding="utf-8")
    return kit, bib


def test_qa_conjunto_reprova_exclusivo_da_sprint_em_kit_de_outro_cliente():
    casos = {"declarado": dict(), "declaração apagada do JSON": dict(declarar=False), "só no plano": dict(tirar_do_json=True)}
    for nome, kw in casos.items():
        kit, bib = _kit_ame("ame-" + re.sub(r"\W+", "-", nome), **kw)
        f = [m for m in falhas(qa_conjunto.checar(kit, bib=bib)) if "exclusivo" in m]
        print(f"   {nome}: {f}")
        assert len(f) == 1 and "`medalha-alada`" in f[0] and "exclusivo de SPRINT UBATUBA RUN" in f[0] and "AME CRIANCA" in f[0], f
    kit, bib = _kit_ame("ame-controle", com_medalha=False)
    assert not [m for m in falhas(qa_conjunto.checar(kit, bib=bib)) if "exclusivo" in m]


def test_registrar_recusa_o_arquivo_exclusivo_vindo_de_kit_de_outro_cliente():
    kit, _ = _kit_ame("ame-registrar", declarar=False)          # a medalha foi copiada à mão e perdeu a declaração
    bib = copia("bib-registrar-ame")
    relatorio, erros = biblioteca.registrar(kit, bib=bib)
    linha = next(r for r in relatorio if r[0] == "medalha-alada")
    print("  ", linha)
    assert erros == 1 and linha[2].startswith("ERRO") and "exclusivo de SPRINT UBATUBA RUN" in linha[2]
    usos = biblioteca.item(biblioteca.carregar(bib), "medalha-alada")["usos"]
    assert not any(u["cliente"] == "AME CRIANCA" for u in usos), usos
    assert biblioteca.pasta_exclusivo("Sprint Ubatuba Run") == biblioteca.pasta_exclusivo("SPRINT UBATUBA RUN")


def test_registrar_nao_escreve_fora_da_biblioteca():
    bib = copia("bib-fora"); kit = _TMP / "kit-ids-ruins"; (kit / "acervo").mkdir(parents=True)
    shutil.copyfile(bib / "tenis-usado.png", kit / "acervo" / "x.png")
    els = [{"id": "../../fora", "papel": "heroi", "tipo": "objeto", "formato": "png", "arquivo": "acervo/x.png", "motivo": "pista"}]
    (kit / "mediakit.json").write_text(json.dumps({"kit": "k", "cliente": "../../etc", "elementos": els}), encoding="utf-8")
    relatorio, erros = biblioteca.registrar(kit, bib=bib)
    assert erros == 1 and relatorio[0][2].startswith("ERRO id fora do padrão"), relatorio
    assert not (_TMP / "fora.png").exists() and not list(_TMP.glob("**/fora.png"))
    assert biblioteca.pasta_exclusivo("../../etc") == "_EXCLUSIVOS/ETC" and ".." not in biblioteca.pasta_exclusivo("..")


def test_qa_py_imprime_as_falhas_do_conjunto():
    """Ponta a ponta: o qa.py de sempre, num kit estruturalmente válido (cópia do exemplo fictício) que ganhou
    sistema_elementos e um elemento exclusivo da Sprint, imprime a FALHA do conjunto no mesmo formato e sai 1."""
    kit_ame, bib = _kit_ame("ame-para-qa-py")
    kit = _TMP / "travessia-com-elementos"
    shutil.copytree(AQUI.parent / "exemplos" / "travessia-da-lua", kit, ignore=shutil.ignore_patterns("saida"))
    k = json.loads((kit / "mediakit.json").read_text(encoding="utf-8"))
    ame = json.loads((kit_ame / "mediakit.json").read_text(encoding="utf-8"))
    k["sistema_elementos"], k["elementos"] = ame["sistema_elementos"], ame["elementos"]
    k["sistema_elementos"]["constantes"][1]["texto"] = "TRAVESSIA \u2014 2027"      # texto vivo: continua conferido
    (kit / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False), encoding="utf-8")
    shutil.copytree(kit_ame / "acervo" / "elementos", kit / "acervo" / "elementos")
    shutil.copytree(kit_ame / "saida", kit / "saida")
    r = subprocess.run([sys.executable, str(AQUI / "qa.py"), str(kit)], capture_output=True, text=True)
    linhas = [l for l in r.stdout.splitlines() if "elementos" in l]
    print("  ", "\n   ".join(linhas))
    assert r.returncode == 1
    assert any(l.startswith("FALHA  elementos: `medalha-alada` é exclusivo de SPRINT UBATUBA RUN; este kit é de Coletivo Farol") for l in linhas), r.stdout[-1500:]
    assert "FALHA  sistema_elementos.constantes[1].texto: travessão/meia-risca no texto do kit" in linhas
    assert not [l for l in linhas if l.startswith("FALHA  sistema_elementos") and "constantes[1].texto" not in l], "cor hex ou estilo tratados como texto do kit"


def test_usar_recusa_exclusivo_de_outro_cliente_e_entrega_a_entrada():
    bib = copia("bib-usar"); kit = _TMP / "ame-usar"; kit.mkdir()
    (kit / "mediakit.json").write_text(json.dumps({"kit": "ame-crianca-2027", "cliente": "AME CRIANCA", "elementos": []}), encoding="utf-8")
    try:
        biblioteca.usar("medalha-alada", kit, bib)
        raise AssertionError("usou exclusivo da Sprint num kit da AME")
    except SystemExit as e:
        assert "exclusivo de SPRINT UBATUBA RUN" in str(e), e
    entrada, _ = biblioteca.usar("tenis-usado", kit, bib)
    print("  ", entrada)
    assert entrada["biblioteca_id"] == "tenis-usado" and entrada["kit_origem"] == "sprint-2027" and entrada["rota"] == "biblioteca"
    assert (kit / entrada["arquivo"]).is_file()
    usos = biblioteca.item(biblioteca.carregar(bib), "tenis-usado")["usos"]
    assert any(u["kit"] == "ame-crianca-2027" and u["cliente"] == "AME CRIANCA" for u in usos), usos
    # o atalho para fora da pasta do kit é recusado (o acervo do kit de teste da Sprint aponta para o cliente real)
    try:
        biblioteca.usar("tenis-usado", kit_sprint(), bib)
        raise AssertionError("copiou por um atalho para fora do kit")
    except SystemExit as e:
        assert "fora da pasta do kit" in str(e), e


def test_checar_acusa_sha_exclusivo_fora_ocr_e_arquivo_solto():
    bib = copia("bib-checar")
    im = Image.open(bib / "ondas-serra.png").convert("RGBA"); px = im.load(); px[5, 5] = (9, 9, 9, 255); im.save(bib / "ondas-serra.png")
    ind = biblioteca.carregar(bib)
    pena = biblioteca.item(ind, "pena-dourada")
    shutil.move(bib / pena["arquivo"], bib / "pena-dourada.png"); pena["arquivo"] = "pena-dourada.png"
    biblioteca.item(ind, "tenis-usado")["ocr"] = "LOGO"
    biblioteca.gravar(bib, ind)
    shutil.copyfile(bib / "folha-amendoeira.png", bib / "solta.png")
    res = biblioteca.checar(bib); f = [m for n, m in res if n == "FALHA"]; a = [m for n, m in res if n == "AVISO"]
    print("   FALHA:", f)
    assert any("ondas-serra" in m and "sha256 divergente" in m for m in f)
    assert any("pena-dourada" in m and "fora de _EXCLUSIVOS/SPRINT UBATUBA RUN/" in m for m in f)
    assert any("tenis-usado" in m and "OCR encontrou texto" in m for m in f)
    assert any("solta.png" in m for m in a)
    assert "tenis-usado" not in [r["item"]["id"] for r in biblioteca.buscar(biblioteca.carregar(bib), bib, tipo="objeto", cliente="AME CRIANCA")]


def test_ocr_de_verdade_aprova_os_6_e_reprova_texto_escrito():
    """padrao.texto (Frente B) no registrar: os 6 elementos reais da Sprint saem sem texto (ocr "" e medido); um PNG com
    "SPRINT" escrito fica com o texto em `ocr`, o planejador o bloqueia e o checar reprova."""
    bib = copia("bib-ocr")
    its = {i["id"]: i for i in biblioteca.carregar(bib)["itens"]}
    sprint = {"penas-asa", "ondas-serra", "pena-dourada", "folha-amendoeira", "medalha-alada", "tenis-usado"}
    assert all(its[i]["ocr"] == "" and its[i]["ocr_estado"] == "medido" for i in sprint), {i: (its[i]["ocr"], its[i]["ocr_estado"]) for i in sprint}
    from test_padrao import _palavra
    kit = _TMP / "kit-ocr"; (kit / "acervo" / "elementos").mkdir(parents=True)
    _palavra("SPRINT").convert("RGBA").save(kit / "acervo" / "elementos" / "com-texto.png")
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    fx["elementos"] = [{"id": "com-texto", "tipo": "objeto", "familia": "objeto-dourado", "motivo": "medalha", "formato": "png",
                        "papel": "heroi", "arquivo": "acervo/elementos/com-texto.png", "kit_origem": fx.get("kit"), "exclusivo_cliente": None}]
    (kit / "mediakit.json").write_text(json.dumps(fx, ensure_ascii=False), encoding="utf-8")
    biblioteca.registrar(kit, bib=bib)
    it = next(i for i in biblioteca.carregar(bib)["itens"] if i["id"] == "com-texto")
    assert "SPRINT" in (it["ocr"] or "") and it["ocr_estado"] == "medido", it
    assert pe.bloqueado({"id": "com-texto", "biblioteca_id": "com-texto"}, biblioteca.carregar(bib)), "elemento com texto não foi bloqueado"
    assert any("com-texto" in m and "OCR encontrou texto" in m for n, m in biblioteca.checar(bib) if n == "FALHA"), biblioteca.checar(bib)


def test_revisao_registrada_so_vale_para_a_mesma_imagem_e_a_mesma_leitura():
    """Decisão do Ugo (09/10/2026): falso positivo do OCR (pontos de meio-tom lidos como 'AN') se resolve com revisão
    registrada na ficha, não afrouxando o leitor. A revisão vale só para o mesmo sha256 e a mesma leitura; o checar
    continua avisando. Imagem trocada ou leitura nova voltam a reprovar."""
    import padrao
    from test_padrao import _palavra
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    def kit_com(nome, desenhar):
        kit = _TMP / nome; (kit / "acervo" / "elementos").mkdir(parents=True)
        png = kit / "acervo" / "elementos" / "adesivo.png"; desenhar(png)
        fx2 = dict(fx, elementos=[{"id": "adesivo", "tipo": "adesivo", "familia": "meio-tom-mar", "motivo": "ondas-serra", "formato": "png",
                                   "papel": "heroi", "arquivo": "acervo/elementos/adesivo.png", "kit_origem": fx.get("kit"), "exclusivo_cliente": None}])
        (kit / "mediakit.json").write_text(json.dumps(fx2, ensure_ascii=False), encoding="utf-8")
        return kit, png
    evid = "recorte ampliado da região lida: só pontos de meio-tom, nenhuma letra"
    # 1) revisada: a mesma imagem e a mesma leitura
    kit, png = kit_com("kit-rev-ok", lambda q: _palavra("SPRINT").convert("RGBA").save(q))
    r = padrao.revisar_texto(png, evid, por="prova")
    assert r and r["lido"] == "SPRINT" and len(r["sha256"]) == 64, r
    bib = copia("bib-rev-ok"); biblioteca.registrar(kit, bib=bib)
    it = next(i for i in biblioteca.carregar(bib)["itens"] if i["id"] == "adesivo")
    assert it["ocr"] == "" and it["ocr_estado"].startswith("revisado"), it
    msgs = biblioteca.checar(bib)
    assert any(n == "AVISO" and "adesivo" in m and "revisado" in m for n, m in msgs), msgs
    assert not any(n == "FALHA" and "adesivo" in m for n, m in msgs), msgs
    # 2) a imagem mudou depois da revisão: a revisão não vale
    kit2, png2 = kit_com("kit-rev-sha", lambda q: _palavra("SPRINT").convert("RGBA").save(q))
    padrao.revisar_texto(png2, evid, por="prova")
    from PIL import ImageDraw
    im = Image.open(png2).convert("RGBA"); ImageDraw.Draw(im).rectangle([0, 0, 3, 3], fill=(0, 0, 0, 255)); im.save(png2)
    bib2 = copia("bib-rev-sha"); biblioteca.registrar(kit2, bib=bib2)
    it2 = next(i for i in biblioteca.carregar(bib2)["itens"] if i["id"] == "adesivo")
    assert "SPRINT" in (it2["ocr"] or "") and it2["ocr_estado"] == "medido", it2
    # 3) a leitura revisada não é a de agora: não vale
    kit3, png3 = kit_com("kit-rev-lido", lambda q: _palavra("SPRINT").convert("RGBA").save(q))
    padrao.revisar_texto(png3, evid, por="prova")
    ficha = png3.with_suffix(".meta.json"); m = json.loads(ficha.read_text()); m["ocr_revisado"]["lido"] = "AN"; ficha.write_text(json.dumps(m))
    bib3 = copia("bib-rev-lido"); biblioteca.registrar(kit3, bib=bib3)
    it3 = next(i for i in biblioteca.carregar(bib3)["itens"] if i["id"] == "adesivo")
    assert "SPRINT" in (it3["ocr"] or ""), it3
    # sem evidência, a revisão nem é gravada
    try:
        padrao.revisar_texto(png3, "ok"); raise AssertionError("revisão sem evidência foi aceita")
    except ValueError:
        pass


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

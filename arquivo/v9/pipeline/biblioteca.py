#!/usr/bin/env python3
"""
biblioteca.py: a biblioteca única de elementos e objetos da Motion (mídia kit e carrossel), em
MARKETING/BIBLIOTECA DE OBJETOS/. Fonte de verdade: indice.json (definição biblioteca_indice de schema/elementos.schema.json).
O INDICE.md que o carrossel lê é GERADO entre <!-- biblioteca:inicio --> e <!-- biblioteca:fim -->; o que fica fora dos
marcadores é escrito à mão pelo carrossel e é preservado byte a byte.

Comandos (a partir de pipeline/; o Claude roda, o Ugo não). Todos aceitam --biblioteca <pasta> para sobrepor o caminho
padrão, que é ../../../MARKETING/BIBLIOTECA DE OBJETOS a partir desta pasta.
  registrar <pasta-do-kit> [--ids a b]   lê elementos[] do mediakit.json (e <id>.meta.json, se existir), mede sha256, dims,
                                         alfa_bbox, costura (pattern), OCR (padrao.texto; sem tesseract fica pendente) e
                                         descritores (familia.py); copia o PNG final e o bruto só quando difere; exclusivo
                                         vai para _EXCLUSIVOS/<cliente>/. Idempotente por sha256: rodar de novo só completa
                                         o que estava pendente.
  buscar [--tipo t] [--motivo m] [--estilo "palavras"] [--meio m] [--tags a,b] --cliente <cliente-do-kit>
         [--folha saida.png] [--json]    candidatas numeradas, da mais adequada para a menos; NUNCA devolve exclusivo de
                                         outro cliente, item com texto (OCR), reprovado ou sem arquivo.
  usar <id> <pasta-do-kit> [--familia f] copia para acervo/elementos/ do kit e imprime a entrada pronta para elementos[]
                                         (biblioteca_id, kit_origem do item original, rota biblioteca); registra o uso.
  folha [--tipo t] [--saida png]         catálogo visual por tipo (padrão: <biblioteca>/_folhas/, fora do git).
  checar                                 arquivo ausente, sha256 divergente, exclusivo fora da pasta, OCR com texto (FALHA);
                                         OCR pendente, arquivo sem registro (AVISO). Sai 1 com FALHA.
  sincronizar                            importa as linhas escritas à mão (rota manual) e regera o bloco entre marcadores.

Regras do dono (09/10/2026): uma biblioteca só para a Motion; elemento cujo motivo nasce do símbolo/identidade de um
cliente (origem simbolo) ou que o kit declara exclusivo é EXCLUSIVO dele; guarda-se só o arquivo final e o bruto quando
diferente (variantes, mosaicos e folhas o código regera).
"""
import argparse, json, re, shutil, sys, unicodedata
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
PADRAO = AQUI.parent.parent.parent / "MARKETING" / "BIBLIOTECA DE OBJETOS"
SCHEMA = AQUI.parent / "schema" / "elementos.schema.json"
INICIO, FIM = "<!-- biblioteca:inicio -->", "<!-- biblioteca:fim -->"
CAB_TABELA = "| Arquivo | O que é | Origem | Usado em |"
EXT_IMAGEM = (".png", ".jpg", ".jpeg", ".webp", ".svg")
TIPO_ROTULO = {"pattern": "Pattern", "objeto": "Objeto", "ilustracao": "Ilustração", "pictograma": "Pictograma",
               "textura": "Textura", "adesivo": "Adesivo", "meio-tom-simbolo": "Símbolo em meio-tom",
               "pattern-simbolo": "Pattern do símbolo", "linha-percurso": "Linha de percurso", "moldura": "Moldura",
               "contorno-territorio": "Contorno do território"}


# ---------------------------------------------------------------- nomes, clientes e kits
def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().casefold()


def mesmo_cliente(a, b):
    return bool(norm(a)) and norm(a) == norm(b)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")


def pasta_exclusivo(cliente):
    """Uma pasta por cliente, no padrão das pastas de CLIENTES (caixa alta): 'Sprint Ubatuba Run' e 'SPRINT UBATUBA RUN'
    caem no mesmo lugar."""
    nome = re.sub(r"[^\w .-]+", "-", str(cliente), flags=re.UNICODE)       # sem barra: nunca sai de _EXCLUSIVOS/
    nome = re.sub(r"\s+", " ", nome).strip(" .-").upper() or "SEM-CLIENTE"
    return f"_EXCLUSIVOS/{nome}"


def cliente_do_kit(k, pasta):
    c = k.get("cliente")
    if isinstance(c, str) and c.strip():
        return c.strip()
    if isinstance(c, dict) and c.get("nome"):
        return c["nome"]
    partes = Path(pasta).resolve().parts
    if "CLIENTES" in partes and partes.index("CLIENTES") + 1 < len(partes):
        return partes[partes.index("CLIENTES") + 1]
    return None


def kit_do_kit(k, pasta):
    return k.get("kit") or Path(pasta).resolve().name


def hoje():
    return date.today().isoformat()


# ---------------------------------------------------------------- índice
def carregar(bib):
    p = Path(bib) / "indice.json"
    if not p.exists():
        return {"versao": 1, "itens": []}
    return json.loads(p.read_text(encoding="utf-8"))


ORDEM_CHAVES = ["id", "tipo", "papel_sugerido", "formato", "arquivo", "bruto", "bruto_sha256", "motivo", "origem_motivo",
                "descricao", "estilo", "meio", "familia_origem", "tags", "cores", "exclusivo_cliente", "dims", "alfa_bbox",
                "aspecto", "costura", "ocr", "ocr_estado", "descritores", "rota", "prompt", "prompt_texto", "origem",
                "ref", "kit_origem", "cliente_origem", "sha256", "data", "veredito", "usos"]


def _ordenar(it):
    return {k: it[k] for k in ORDEM_CHAVES if k in it} | {k: v for k, v in it.items() if k not in ORDEM_CHAVES}


def gravar(bib, ind):
    ind = {"versao": 1, "itens": [_ordenar(i) for i in sorted(ind["itens"], key=lambda i: i["id"])]}
    p = Path(bib) / "indice.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(ind, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)
    return ind


def item(ind, iid):
    return next((i for i in ind["itens"] if i["id"] == iid), None)


def item_do_elemento(ind, e, base=None):
    """O item da biblioteca que corresponde a um elemento do kit: por biblioteca_id, por sha256 declarado ou pelo sha256
    do arquivo (pega até quem tirou a declaração de exclusividade do JSON)."""
    if e.get("biblioteca_id"):
        it = item(ind, e["biblioteca_id"])
        if it:
            return it
    sha = e.get("sha256")
    if not sha and base is not None and e.get("arquivo") and (Path(base) / e["arquivo"]).is_file():
        import familia
        sha = familia.sha256(Path(base) / e["arquivo"])
    if sha:
        return next((i for i in ind["itens"] if i.get("sha256") == sha), None)
    return None


# ---------------------------------------------------------------- registrar
def medir_ocr(arq, revisao=None):
    """OCR pelo padrao.texto (Frente B): "" = sem texto; palavras = texto escrito pela IA (o elemento fica bloqueado).
    `revisao` (ocr_revisado da ficha, gravado por `padrao.py revisar-texto`) só vale para a mesma imagem e a mesma leitura;
    aí o estado fica "revisado" e o checar avisa. Só a falta do tesseract deixa pendente; qualquer outro erro aparece."""
    import padrao
    try:
        lido = padrao.texto(str(arq)).strip()
    except RuntimeError as ex:  # tesseract ausente
        return None, f"pendente ({ex})"
    if lido and padrao.revisao_vale(arq, lido, revisao):
        return "", f"revisado: lido {lido!r} e conferido à mão, sem texto ({revisao.get('por')}, {revisao.get('em')}): {revisao.get('evidencia')}"
    return lido, "medido"


def _resumo_prompt(texto):
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    miolo = [re.sub(r"^(Object|Motif):\s*", "", l) for l in linhas if re.match(r"^(Object|Motif):", l)]
    return (miolo[0] if miolo else (linhas[0] if linhas else ""))[:400]


def _ler_meta(arq, eid):
    for cand in (arq.parent / f"{eid}.meta.json", arq.with_suffix(".meta.json")):
        if cand.is_file():
            try:
                return json.loads(cand.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                return {}
    return {}


def _copiar(origem, destino):
    import familia
    destino.parent.mkdir(parents=True, exist_ok=True)
    if not destino.exists() or familia.sha256(destino) != familia.sha256(origem):
        shutil.copyfile(origem, destino)


def registrar(pasta, ids=None, bib=PADRAO):
    import familia, padrao, plano_elementos as pe
    from PIL import Image
    pasta = Path(pasta); bib = Path(bib)
    k = json.loads((pasta / "mediakit.json").read_text(encoding="utf-8"))
    kit = kit_do_kit(k, pasta); cliente = cliente_do_kit(k, pasta)
    sis = k.get("sistema_elementos") or {}
    motivos = {m["id"]: m for m in sis.get("motivos", [])}
    familias = {f["id"]: f for f in sis.get("familias", [])}
    ind = carregar(bib)
    por_sha = {i["sha256"]: i for i in ind["itens"] if i.get("sha256")}
    ids_ocupados = {i["id"] for i in ind["itens"]}
    relatorio, erros = [], 0
    for e in k.get("elementos", []):
        if ids and e["id"] not in ids:
            continue
        if not re.fullmatch(r"[a-z0-9-]+", str(e.get("id", ""))):          # o id vira nome de arquivo na biblioteca
            relatorio.append((str(e.get("id")), None, "ERRO id fora do padrão ^[a-z0-9-]+$")); erros += 1; continue
        if e.get("formato", "png") != "png" or not e.get("arquivo"):
            relatorio.append((e["id"], None, "svg é grafismo por código: não vai para a biblioteca")); continue
        arq = pasta / e["arquivo"]
        if not arq.is_file():
            relatorio.append((e["id"], None, f"ERRO arquivo não existe: {e['arquivo']}")); erros += 1; continue
        meta = _ler_meta(arq, e["id"])
        sha = familia.sha256(arq)
        it = por_sha.get(sha)
        if it is not None:                                            # idempotente: só completa o que faltava
            if it.get("exclusivo_cliente") and not mesmo_cliente(it["exclusivo_cliente"], cliente):
                relatorio.append((e["id"], it["id"], f"ERRO é o mesmo arquivo de `{it['id']}`, exclusivo de {it['exclusivo_cliente']}; este kit é de {cliente}"))
                erros += 1; continue
            if it.get("ocr_estado", "pendente").startswith("pendente") or (it.get("ocr") and meta.get("ocr_revisado")):
                it["ocr"], it["ocr_estado"] = medir_ocr(bib / it["arquivo"] if (bib / it["arquivo"]).is_file() else arq,
                                                        meta.get("ocr_revisado"))
            if not (bib / it["arquivo"]).is_file():
                _copiar(arq, bib / it["arquivo"])
            if not any(u.get("kit") == kit and u.get("sistema") == "mediakit" for u in it.get("usos", [])):
                it.setdefault("usos", []).append({"kit": kit, "cliente": cliente, "receita": None, "paginas": [], "data": hoje(), "sistema": "mediakit"})
            relatorio.append((e["id"], it["id"], "já estava (mesmo sha256)")); continue
        motivo = e.get("motivo") or meta.get("motivo") or "sem-motivo"
        origem_motivo = (motivos.get(motivo) or {}).get("origem") or "generico"
        exclusivo = e.get("exclusivo_cliente") or meta.get("exclusivo_cliente") or (cliente if origem_motivo == "simbolo" else None)
        if origem_motivo == "simbolo" and not exclusivo:
            relatorio.append((e["id"], None, "ERRO motivo de origem simbolo e cliente desconhecido: declare exclusivo_cliente")); erros += 1; continue
        lib_id = e["id"]
        if lib_id in ids_ocupados:
            lib_id = f"{e['id']}-{slug(kit)}"
            n = 2
            while lib_id in ids_ocupados:
                lib_id = f"{e['id']}-{slug(kit)}-{n}"; n += 1
        rel_dir = pasta_exclusivo(exclusivo) if exclusivo else ""
        dest = bib / rel_dir if rel_dir else bib
        rel = lambda nome: f"{rel_dir}/{nome}" if rel_dir else nome  # noqa: E731
        _copiar(arq, dest / f"{lib_id}.png")
        bruto_rel = bruto_sha = None
        cand_bruto = (pasta / meta["bruto"]) if meta.get("bruto") else arq.parent / f"{e['id']}.bruto.png"
        if cand_bruto.is_file() and familia.sha256(cand_bruto) != sha:
            _copiar(cand_bruto, dest / f"{lib_id}.bruto.png")
            bruto_rel, bruto_sha = rel(f"{lib_id}.bruto.png"), familia.sha256(cand_bruto)
        prompt_rel = prompt_txt = None
        prompt_src = e.get("prompt") or meta.get("prompt")
        if not prompt_src and (arq.parent / f"{e['id']}.prompt.txt").is_file():   # convenção do elementos.sh
            prompt_src = (arq.parent / f"{e['id']}.prompt.txt").relative_to(pasta).as_posix()
        if prompt_src and (pasta / prompt_src).is_file():
            _copiar(pasta / prompt_src, dest / f"{lib_id}.prompt.txt")
            prompt_rel = rel(f"{lib_id}.prompt.txt")
            prompt_txt = _resumo_prompt((pasta / prompt_src).read_text(encoding="utf-8"))
        descr = familia.descritores(arq)
        uso = familia.escala_de_uso(e, descr)
        descr["escala_uso"] = round(uso, 1)
        descr["traco_px_uso"] = round(descr["traco_px_nativo"] * uso / (descr["alfa_bbox"] or [0, 0, descr["dims"][0]])[2], 2) if descr.get("alfa_bbox") else None
        eh_pattern = e.get("papel") == "pattern" or e.get("tipo") == "pattern"
        costura = padrao.medir_costura(Image.open(arq).convert("RGBA"))["costura"] if eh_pattern else None
        ocr, ocr_estado = medir_ocr(arq, meta.get("ocr_revisado"))
        fam = familias.get(e.get("familia"))
        meio_medido = descr.get("meio")
        meio = fam["meio"] if fam and meio_medido in familia.COMPATIVEL.get(fam.get("meio"), set()) else meio_medido
        tipo = e.get("tipo") or ("pattern" if eh_pattern else "objeto")
        cores = [p["hex"] for p in descr.get("paleta", [])[:4]]
        desc_m = (motivos.get(motivo) or {}).get("descricao")
        descricao = f"{TIPO_ROTULO.get(tipo, tipo.capitalize())}, motivo {motivo}" + (f" ({desc_m})" if desc_m else "") + \
                    f". {familia.MEIO_ROTULO.get(meio, meio or 'meio não medido').capitalize()}, cores {', '.join(cores[:2])}"
        bb = descr.get("alfa_bbox") or [0, 0, 0, 0]
        papel = {"ornamento": "heroi"}.get(e.get("papel"), e.get("papel"))
        novo = {
            "id": lib_id, "tipo": tipo, "formato": "png", "arquivo": rel(f"{lib_id}.png"),
            "bruto": bruto_rel, "bruto_sha256": bruto_sha, "motivo": motivo, "origem_motivo": origem_motivo,
            "descricao": descricao, "estilo": f"{fam['id']}: {fam['estilo']}" if fam else (meta.get("estilo") or ""),
            "meio": meio, "familia_origem": {"id": fam["id"], "meio": fam["meio"]} if fam else None,
            "tags": sorted({t for t in re.split(r"[^a-z0-9]+", norm(" ".join([e["id"], motivo, tipo, meio or "", (fam or {}).get("id", ""), kit] + list(meta.get("tags") or [])))) if len(t) > 1}),
            "cores": cores, "exclusivo_cliente": exclusivo, "dims": descr["dims"], "alfa_bbox": descr.get("alfa_bbox"),
            "aspecto": e.get("aspecto") or pe.aspecto_razao(bb[2], bb[3]), "costura": costura, "ocr": ocr,
            "ocr_estado": ocr_estado, "descritores": descr, "rota": e.get("rota") or meta.get("rota") or "desconhecida",
            "prompt": prompt_rel, "prompt_texto": prompt_txt, "ref": e.get("ref") or meta.get("ref"),
            "kit_origem": e.get("kit_origem") or kit, "cliente_origem": cliente, "sha256": sha,
            "data": meta.get("data") or hoje(),
            "usos": [{"kit": kit, "cliente": cliente, "receita": None,
                      "paginas": e["paginas"] if isinstance(e.get("paginas"), list) else [], "data": hoje(), "sistema": "mediakit"}],
        }
        if papel in ("pattern", "heroi", "apoio", "constante"):
            novo["papel_sugerido"] = papel
        if meta.get("veredito"):
            novo["veredito"] = meta["veredito"]
        ind["itens"].append(novo); por_sha[sha] = novo; ids_ocupados.add(lib_id)
        relatorio.append((e["id"], lib_id, "registrado" + (f" (exclusivo {exclusivo})" if exclusivo else "") + (f", OCR {ocr_estado}" if ocr_estado != "medido" else "")))
    gravar(bib, ind)
    for eid, lid, msg in relatorio:
        print(f"{eid:24s} -> {lid or '-':28s} {msg}")
    return relatorio, erros


# ---------------------------------------------------------------- buscar e usar
def permitido(it, cliente):
    ex = it.get("exclusivo_cliente")
    return not ex or (cliente is not None and mesmo_cliente(ex, cliente))


def buscar(ind, bib=PADRAO, tipo=None, motivo=None, estilo=None, meio=None, tags=None, cliente=None):
    import familia
    bib = Path(bib); suaves = any([motivo, estilo, meio, tags]); out = []
    palavras = [w for w in re.split(r"[^a-z0-9]+", norm(estilo or "")) if len(w) > 2]
    for it in ind["itens"]:
        if not permitido(it, cliente):
            continue                       # nunca exclusivo de outro cliente (nem sem cliente informado)
        if tipo and it.get("tipo") != tipo:
            continue
        if it.get("ocr") or (it.get("veredito") or {}).get("status") == "reprovado":
            continue
        if not (bib / it["arquivo"]).is_file():
            continue
        nota, razoes = 0, []
        if motivo:
            if it.get("motivo") == motivo: nota += 3; razoes.append("motivo")
            elif motivo in (it.get("tags") or []): nota += 1; razoes.append("motivo nas tags")
        if meio:
            if it.get("meio") == meio: nota += 2; razoes.append("meio")
            elif (it.get("descritores") or {}).get("meio") in familia.COMPATIVEL.get(meio, set()): nota += 1; razoes.append("meio compatível")
        if palavras:
            texto = norm(" ".join([it.get("estilo") or "", it.get("descricao") or "", it.get("prompt_texto") or ""]))
            acertos = sum(1 for w in palavras if w in texto)
            if acertos: nota += min(3, acertos); razoes.append(f"{acertos} palavra(s) de estilo")
        if tags:
            comuns = set(tags) & set(it.get("tags") or [])
            if comuns: nota += len(comuns); razoes.append("tags " + ",".join(sorted(comuns)))
        if suaves and nota == 0:
            continue
        out.append({"nota": nota, "razoes": razoes, "usos": len(it.get("usos") or []), "item": it})
    out.sort(key=lambda r: (-r["nota"], r["usos"], r["item"]["id"]))
    for n, r in enumerate(out, 1):
        r["n"] = n
    return out


def _fonte(tam):
    import familia
    return familia._fonte(tam)


def _miniatura(caminho, lado, fundo=(26, 26, 26)):
    from PIL import Image
    c = Image.new("RGBA", (lado, lado), fundo + (255,))
    if Path(caminho).is_file():
        im = Image.open(caminho).convert("RGBA"); im.thumbnail((lado - 20, lado - 20), Image.LANCZOS)
        c.alpha_composite(im, ((lado - im.width) // 2, (lado - im.height) // 2))
    return c.convert("RGB")


def folha_grade(cartoes, bib, saida, titulo, lado=300, colunas=4):
    """cartoes: [(rótulo grande, linhas, caminho)] em grade numerada."""
    from PIL import Image, ImageDraw
    linhas_grade = max(1, -(-len(cartoes) // colunas))
    W = colunas * (lado + 20) + 20; H = 90 + linhas_grade * (lado + 96)
    F = Image.new("RGB", (W, H), (40, 40, 40)); d = ImageDraw.Draw(F)
    d.text((20, 24), titulo, fill=(255, 255, 255), font=_fonte(30))
    for i, (grande, linhas, caminho) in enumerate(cartoes):
        x = 20 + (i % colunas) * (lado + 20); y = 90 + (i // colunas) * (lado + 96)
        F.paste(_miniatura(caminho, lado), (x, y))
        d.text((x, y + lado + 6), grande[:34], fill=(255, 255, 255), font=_fonte(20))
        for j, t in enumerate(linhas[:2]):
            d.text((x, y + lado + 34 + j * 22), t[:44], fill=(200, 200, 200) if "SEM ARQUIVO" not in t else (240, 120, 120), font=_fonte(15))
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    F.save(saida, optimize=True)
    return Path(saida)


def usar(iid, pasta, bib=PADRAO, familia_id=None):
    import familia
    pasta = Path(pasta); bib = Path(bib)
    k = json.loads((pasta / "mediakit.json").read_text(encoding="utf-8"))
    kit = kit_do_kit(k, pasta); cliente = cliente_do_kit(k, pasta)
    ind = carregar(bib); it = item(ind, iid)
    if it is None:
        raise SystemExit(f"`{iid}` não existe na biblioteca")
    if not permitido(it, cliente):
        raise SystemExit(f"`{iid}` é exclusivo de {it['exclusivo_cliente']}; este kit é de {cliente}. Não pode.")
    if it.get("ocr"):
        raise SystemExit(f"`{iid}` tem texto escrito pela IA (OCR: {it['ocr']!r}). Não pode.")
    if (it.get("veredito") or {}).get("status") == "reprovado":
        raise SystemExit(f"`{iid}` foi reprovado ({(it.get('veredito') or {}).get('nota', '')}).")
    origem = bib / it["arquivo"]
    if not origem.is_file():
        raise SystemExit(f"`{iid}`: o arquivo {it['arquivo']} não existe na biblioteca (rode `checar`).")
    destino_dir = pasta / "acervo" / "elementos"
    if not destino_dir.resolve().is_relative_to(pasta.resolve()):
        raise SystemExit(f"acervo/elementos do kit aponta para fora da pasta do kit ({destino_dir.resolve()}): não copio por um atalho.")
    ids_kit = {e["id"]: e for e in k.get("elementos", [])}
    local = it["id"]
    if local in ids_kit and ids_kit[local].get("sha256") not in (None, it["sha256"]):
        local = f"{it['id']}-bib"
    destino = destino_dir / f"{local}.png"
    _copiar(origem, destino)
    entrada = {"id": local, "papel": it.get("papel_sugerido") or "heroi", "tipo": it["tipo"], "formato": it["formato"],
               "familia": familia_id, "motivo": it["motivo"], "arquivo": f"acervo/elementos/{local}.png",
               "biblioteca_id": it["id"], "kit_origem": it["kit_origem"], "exclusivo_cliente": it.get("exclusivo_cliente"),
               "aspecto": it.get("aspecto"), "gerado": it.get("rota") not in ("manual", "cliente"), "rota": "biblioteca",
               "prompt": None, "sha256": it["sha256"]}
    if not any(u.get("kit") == kit and u.get("sistema") == "mediakit" for u in it.get("usos", [])):
        it.setdefault("usos", []).append({"kit": kit, "cliente": cliente, "receita": None, "paginas": [], "data": hoje(), "sistema": "mediakit"})
    gravar(bib, ind)
    veredito = None
    if familia_id:
        fam = next((f for f in (k.get("sistema_elementos") or {}).get("familias", []) if f.get("id") == familia_id), None)
        if fam:
            veredito = familia.pertence(entrada, fam, base=pasta, descr=it.get("descritores"))
    return entrada, veredito


# ---------------------------------------------------------------- checar
def checar(bib=PADRAO):
    import familia
    bib = Path(bib); ind = carregar(bib); res = []
    F = lambda m: res.append(("FALHA", m)); A = lambda m: res.append(("AVISO", m))  # noqa: E731
    try:
        import jsonschema
        sch = json.loads(SCHEMA.read_text(encoding="utf-8"))
        v = jsonschema.Draft7Validator({"$ref": "#/definitions/biblioteca_indice", "definitions": sch["definitions"]})
        for err in sorted(v.iter_errors(ind), key=lambda x: list(x.path))[:10]:
            F(f"indice.json fora do schema em {'/'.join(map(str, err.path)) or '(raiz)'}: {err.message}")
    except ImportError:
        A("jsonschema ausente: indice.json não validado contra o schema")
    vistos, shas = {}, {}
    for it in ind["itens"]:
        iid = it.get("id", "?")
        if iid in vistos: F(f"id `{iid}` duplicado no indice.json")
        vistos[iid] = 1
        if it.get("sha256"):
            if it["sha256"] in shas: F(f"`{iid}` e `{shas[it['sha256']]}` têm o mesmo sha256 (mesmo arquivo registrado duas vezes)")
            shas[it["sha256"]] = iid
        arq = bib / it.get("arquivo", "")
        if not arq.is_file():
            F(f"`{iid}`: arquivo ausente ({it.get('arquivo')})" + (" [linha escrita à mão no INDICE.md]" if it.get("rota") == "manual" else ""))
        elif it.get("sha256") and familia.sha256(arq) != it["sha256"]:
            F(f"`{iid}`: sha256 divergente ({it.get('arquivo')} mudou depois do registro)")
        ex = it.get("exclusivo_cliente")
        if ex and not it.get("arquivo", "").startswith(pasta_exclusivo(ex) + "/"):
            F(f"`{iid}`: exclusivo de {ex} fora de {pasta_exclusivo(ex)}/ ({it.get('arquivo')})")
        if not ex and it.get("arquivo", "").startswith("_EXCLUSIVOS/"):
            A(f"`{iid}`: está em _EXCLUSIVOS/ mas não declara exclusivo_cliente")
        if it.get("bruto"):
            b = bib / it["bruto"]
            if not b.is_file(): F(f"`{iid}`: bruto ausente ({it['bruto']})")
            elif it.get("bruto_sha256") and familia.sha256(b) != it["bruto_sha256"]: F(f"`{iid}`: sha256 do bruto divergente")
        if it.get("ocr"):
            F(f"`{iid}`: OCR encontrou texto ({it['ocr'][:60]!r}); texto só por grafismo, com fonte do kit")
        elif (it.get("ocr_estado") or "").startswith("revisado"):
            A(f"`{iid}`: OCR {it['ocr_estado'][:220]}")
        elif it.get("ocr") is None and it.get("formato") == "png":
            A(f"`{iid}`: OCR {it.get('ocr_estado') or 'pendente'} (texto escrito pela IA ainda não conferido)")
    citados = {it.get("arquivo") for it in ind["itens"]} | {it.get("bruto") for it in ind["itens"] if it.get("bruto")}
    for f in sorted(bib.rglob("*")):
        rel = f.relative_to(bib).as_posix()
        if f.is_file() and f.suffix.lower() in EXT_IMAGEM and not rel.startswith(("_ENTRADA/", "_folhas/")) and rel not in citados:
            A(f"{rel}: imagem na biblioteca sem registro no indice.json")
    return res


# ---------------------------------------------------------------- sincronizar (INDICE.md)
LINHA = re.compile(r"^\|\s*`([^`]+)`\s*\|(.*)\|(.*)\|(.*)\|\s*$")


def _partes(texto):
    if INICIO in texto and FIM in texto:
        a, resto = texto.split(INICIO, 1); _, b = resto.split(FIM, 1)
        return a, b, True
    return texto, "", False


def _ponto_de_insercao(texto):
    """Sem marcadores ainda: logo depois da tabela 'Arquivo | O que é | Origem | Usado em' escrita à mão; sem tabela,
    antes da seção de fila; senão, no fim."""
    linhas = texto.splitlines(keepends=True)
    for i, l in enumerate(linhas):
        if l.strip().startswith(CAB_TABELA):
            j = i + 1
            while j < len(linhas) and linhas[j].lstrip().startswith("|"):
                j += 1
            return "".join(linhas[:j]), "".join(linhas[j:])
    for i, l in enumerate(linhas):
        if re.match(r"^#{1,3}\s+Fila", l):
            return "".join(linhas[:i]), "".join(linhas[i:])
    return texto, ""


def importar_manuais(texto_fora, ind, bib):
    """Linhas da tabela escrita à mão que ainda não estão no índice viram itens com rota manual."""
    novos = []
    conhecidos = {i.get("arquivo") for i in ind["itens"]}
    prompts = dict(re.findall(r"\*\*([a-z0-9-]+)\*\*\s*\n`([^`]+)`", texto_fora))
    for l in texto_fora.splitlines():
        m = LINHA.match(l.strip())
        if not m or m.group(1) == "Arquivo":
            continue
        arquivo, oque, origem, usado = (x.strip() for x in m.groups())
        if arquivo in conhecidos:
            continue
        iid = slug(Path(arquivo).stem)
        if item(ind, iid):
            continue
        dm = re.search(r"\((\d{2})/(\d{2})/(\d{4})\)", origem)
        data = f"{dm.group(3)}-{dm.group(2)}-{dm.group(1)}" if dm else hoje()
        caminho = bib / arquivo
        import familia
        it = {"id": iid, "tipo": "objeto", "papel_sugerido": "heroi", "formato": "svg" if arquivo.lower().endswith(".svg") else "png",
              "arquivo": arquivo, "bruto": None, "motivo": iid.split("-")[0], "origem_motivo": "generico",
              "descricao": oque, "estilo": "", "tags": sorted(set(iid.split("-"))), "cores": [],
              "exclusivo_cliente": None, "dims": [], "alfa_bbox": None, "costura": None, "ocr": None,
              "ocr_estado": "pendente (linha manual)", "rota": "manual", "prompt": None,
              "prompt_texto": prompts.get(iid), "origem": origem, "ref": None, "kit_origem": "carrossel",
              "cliente_origem": "MOTION PERFORM", "sha256": familia.sha256(caminho) if caminho.is_file() else "",
              "data": data, "usos": [] if usado in ("", "-", "\u2014", "\u2013") else [{"kit": usado, "cliente": "MOTION PERFORM", "receita": None, "paginas": [], "data": data, "sistema": "carrossel"}]}
        ind["itens"].append(it); conhecidos.add(arquivo); novos.append(iid)
    return novos


def _usado_em(it):
    us = it.get("usos") or []
    if not us:
        return "ainda não usado"
    partes = []
    for u in us:
        s = ("mídia kit " if u.get("sistema") == "mediakit" else "carrossel ") + str(u.get("kit"))
        if u.get("receita") or u.get("paginas"):
            s += f" ({u.get('receita') or ''}{': ' if u.get('receita') and u.get('paginas') else ''}{', '.join(u.get('paginas') or [])})"
        partes.append(s)
    return "; ".join(partes)


def _origem(it):
    d = it.get("data", "")
    data = f"{d[8:10]}/{d[5:7]}/{d[0:4]}" if re.match(r"\d{4}-\d{2}-\d{2}", d) else d
    rota = it.get("rota") or "?"
    gerador = "Codex GPT Image, " if rota.startswith("codex") else ""
    return f"{gerador}rota `{rota}`, kit `{it.get('kit_origem')}` ({data})"


def _celula(t):
    return str(t).replace("|", "/").replace("\n", " ")


def _linha(it):
    return f"| `{it['arquivo']}` | {_celula(it.get('descricao') or it.get('motivo'))} | {_celula(_origem(it))} | {_celula(_usado_em(it))} |"


def bloco(ind, bib):
    regs = [i for i in ind["itens"] if i.get("rota") != "manual"]
    gerais = sorted((i for i in regs if not i.get("exclusivo_cliente")), key=lambda i: i["id"])
    excl = sorted((i for i in regs if i.get("exclusivo_cliente")), key=lambda i: (norm(i["exclusivo_cliente"]), i["id"]))
    L = [INICIO,
         "<!-- Gerado pelo GERAR MEDIAKIT/pipeline/biblioteca.py sincronizar a partir do indice.json (fonte de verdade). "
         "Não edite entre os marcadores: a próxima sincronização reescreve. Linhas escritas à mão ficam fora deles e são preservadas. -->",
         "", "### Registrados pelo sistema (mídia kit e carrossel)", ""]
    if gerais:
        L += [CAB_TABELA, "|---|---|---|---|"] + [_linha(i) for i in gerais]
    else:
        L.append("Nenhum item registrado pelo sistema ainda.")
    L += ["", "### Exclusivos (só no material do cliente dono; nunca em kit ou post de outro cliente)", ""]
    if excl:
        cliente = None
        for i in excl:
            if i["exclusivo_cliente"] != cliente:
                if cliente is not None:
                    L.append("")
                cliente = i["exclusivo_cliente"]
                L += [f"**{cliente}**", "", CAB_TABELA, "|---|---|---|---|"]
            L.append(_linha(i))
    else:
        L.append("Nenhum exclusivo registrado.")
    com_prompt = [i for i in gerais + excl if i.get("prompt_texto")]
    if com_prompt:
        L += ["", "### Prompts dos registrados (pra regerar ou variar)", ""]
        for i in com_prompt:
            marca = f", exclusivo {i['exclusivo_cliente']}" if i.get("exclusivo_cliente") else ""
            onde = f" (prompt completo em `{i['prompt']}`{marca})" if i.get("prompt") else (f" ({marca[2:]})" if marca else "")
            L += [f"**{i['id']}**{onde}", f"`{i['prompt_texto']}`", ""]
        L.pop()
    ausentes = [i for i in ind["itens"] if not (Path(bib) / i.get("arquivo", "")).is_file()]
    L += ["", "### Conferência", ""]
    if ausentes:
        L += [f"- `{i['arquivo']}` está no índice{' (linha escrita à mão)' if i.get('rota') == 'manual' else ''}, mas o arquivo não existe na pasta. Não use até ele voltar." for i in ausentes]
    else:
        L.append("- Todos os arquivos do índice existem na pasta.")
    L.append(FIM)
    return "\n".join(L)


def sincronizar(bib=PADRAO):
    bib = Path(bib); md = bib / "INDICE.md"
    texto = md.read_text(encoding="utf-8") if md.exists() else "# Biblioteca de Objetos\n\n" + CAB_TABELA + "\n|---|---|---|---|\n"
    antes, depois, tinha = _partes(texto)
    if not tinha:
        antes, depois = _ponto_de_insercao(texto)
    ind = carregar(bib)
    novos = importar_manuais(antes + depois, ind, bib)
    if novos:
        ind = gravar(bib, ind)
    sep_a = "" if (tinha or antes.endswith("\n\n") or not antes) else ("\n" if antes.endswith("\n") else "\n\n")
    sep_d = "" if tinha else ("\n" if depois.startswith("\n") else "\n\n")
    novo_texto = antes + sep_a + bloco(ind, bib) + sep_d + depois
    if novo_texto != texto:
        md.write_text(novo_texto, encoding="utf-8")
    return novos, novo_texto != texto


# ---------------------------------------------------------------- CLI
def main():
    comum = argparse.ArgumentParser(add_help=False)
    comum.add_argument("--biblioteca", default=str(PADRAO))
    ap = argparse.ArgumentParser(parents=[comum]); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("registrar", parents=[comum]); p.add_argument("kit"); p.add_argument("--ids", nargs="*")
    p = sub.add_parser("buscar", parents=[comum])
    for c in ("--tipo", "--motivo", "--estilo", "--meio", "--tags", "--cliente", "--folha"):
        p.add_argument(c)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("usar", parents=[comum]); p.add_argument("id"); p.add_argument("kit"); p.add_argument("--familia")
    p = sub.add_parser("folha", parents=[comum]); p.add_argument("--tipo"); p.add_argument("--saida")
    sub.add_parser("checar", parents=[comum])
    sub.add_parser("sincronizar", parents=[comum])
    a = ap.parse_args()
    bib = Path(a.biblioteca)
    if a.cmd == "registrar":
        _, erros = registrar(a.kit, a.ids, bib)
        novos, mudou = sincronizar(bib)
        print(f"INDICE.md {'atualizado' if mudou else 'sem mudança'}" + (f"; linhas à mão importadas: {', '.join(novos)}" if novos else ""))
        sys.exit(1 if erros else 0)
    if a.cmd == "buscar":
        if not a.cliente:
            print("AVISO  sem --cliente: só itens não exclusivos entram", file=sys.stderr)
        res = buscar(carregar(bib), bib, a.tipo, a.motivo, a.estilo, a.meio, [t for t in (a.tags or "").split(",") if t], a.cliente)
        if a.json:
            print(json.dumps([{"n": r["n"], "id": r["item"]["id"], "nota": r["nota"], "razoes": r["razoes"], "arquivo": r["item"]["arquivo"]} for r in res], ensure_ascii=False, indent=2))
        else:
            for r in res:
                it = r["item"]
                print(f"{r['n']:>2}. {it['id']:28s} {it['tipo']:10s} motivo {it['motivo']:16s} meio {str(it.get('meio')):12s} usos {r['usos']}  ({', '.join(r['razoes']) or 'sem filtro'})")
            if not res:
                print("nenhuma candidata")
        if a.folha and res:
            cart = [(f"{r['n']}. {r['item']['id']}", [f"{r['item']['tipo']} · {r['item']['motivo']}", f"usos {r['usos']}"], bib / r["item"]["arquivo"]) for r in res]
            print("OK", folha_grade(cart, bib, a.folha, f"candidatas ({a.cliente or 'sem cliente'})"))
        return
    if a.cmd == "usar":
        entrada, veredito = usar(a.id, a.kit, bib, a.familia)
        print(json.dumps(entrada, ensure_ascii=False, indent=2))
        if veredito:
            print(("PERTENCE" if veredito["pertence"] else "FORA DA FAMÍLIA: " + "; ".join(veredito["motivos"])), file=sys.stderr)
        sincronizar(bib)
        return
    if a.cmd == "folha":
        ind = carregar(bib)
        tipos = [a.tipo] if a.tipo else sorted({i.get("tipo") for i in ind["itens"]})
        for t in tipos:
            its = sorted((i for i in ind["itens"] if i.get("tipo") == t), key=lambda i: (bool(i.get("exclusivo_cliente")), i["id"]))
            cart = []
            for n, i in enumerate(its, 1):
                linhas = [("EXCLUSIVO " + i["exclusivo_cliente"]) if i.get("exclusivo_cliente") else " · ".join(x for x in (i.get("meio"), i["motivo"]) if x),
                          "SEM ARQUIVO" if not (bib / i["arquivo"]).is_file() else f"usos {len(i.get('usos') or [])}"]
                cart.append((f"{n}. {i['id']}", linhas, bib / i["arquivo"]))
            saida = Path(a.saida) if (a.saida and a.tipo) else bib / "_folhas" / f"folha-{t}.png"
            print("OK", folha_grade(cart, bib, saida, f"biblioteca: {t} ({len(its)})"))
        return
    if a.cmd == "checar":
        res = checar(bib)
        for nivel, m in sorted(res, key=lambda r: r[0] != "AVISO"):
            print(f"{nivel}  {m}")
        nf = sum(1 for n, _ in res if n == "FALHA")
        print(f"\n{nf} falha(s), {len(res) - nf} aviso(s)")
        sys.exit(1 if nf else 0)
    if a.cmd == "sincronizar":
        novos, mudou = sincronizar(bib)
        print(f"INDICE.md {'atualizado' if mudou else 'sem mudança'}" + (f"; linhas à mão importadas para o indice.json: {', '.join(novos)}" if novos else ""))


if __name__ == "__main__":
    main()

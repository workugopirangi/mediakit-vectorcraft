#!/usr/bin/env python3
"""
golden.py: linha de base ("golden") dos kits que já existem. Prova, depois de qualquer mudança na skill, que nenhum
kit existente mudou.

  python golden.py capturar --saida bancada/golden/<data> [--pipeline <pasta pipeline congelada>] [--kits a b]
                            [--vezes 2] [--clones <pasta>] [--commit <hash>]
  python golden.py conferir --golden bancada/golden/<data> [--kits a b] [--pipeline <pasta>] [--clones <pasta>]

capturar: para cada kit, clona a pasta do kit (cp -c do APFS: instantâneo, sem gastar disco, e o kit original nunca é
  tocado), renderiza `--vezes` vezes, UMA RENDERIZAÇÃO POR VEZ, e grava em <saida>/<kit>/:
    html.sha256     sha256 de cada saida/html/*.html
    png.sha256      sha256 de cada página de saida/png/ (e de saida/fundo/, só o hash)
    plano.json      os saida/plano-elementos-*.json sem data, hora, caminho absoluto nem id de sessão
    qa.txt          só as linhas FALHA e AVISO do qa.py, ordenadas
    pdf.json        por PDF: bytes, páginas, tamanho de página, pdffonts, pdfimages -list e texto por página
    png/            os PNG da primeira rodada (entram no .gitignore: pesam)
    ruido.json      pixels diferentes entre a rodada 1 e as seguintes, por página; o máximo é o piso de ruído do kit
    entrada.sha256  sha256 de cada arquivo da pasta do kit (menos saida/): se mudar, a divergência pode ser do kit
  e, na raiz de <saida>: meta.json (tempos, impressão do pipeline) e a cópia do histórico de kits que o qa.py leu.
  Depois de extrair tudo de uma rodada, apaga a saida/ do CLONE (nunca a do kit real) para o disco não estourar.

conferir: clona de novo, renderiza com o pipeline VIVO (esta pasta) e compara com o golden:
    PNG por página igual, ou com diferença <= piso de ruído do kit; texto por página igual; pdffonts e pdfimages
    iguais; mesmas linhas de QA                                                   -> divergência = FALHA
    HTML igual (informativo: o HTML pode mudar sem mudar o raster); plano de elementos; hash do fundo; tamanho do PDF;
    entrada do kit alterada                                                       -> divergência = AVISO
  Sai com 0 se não há FALHA. Imprime uma tabela por kit com o que divergiu.

Caminhos relativos de --saida e --golden valem a partir da pasta da skill (não da pasta atual).
Quem renderiza é o Python que roda este script (use ~/.venvs/mediakit/bin/python).
Contrato dos test_*.py: as provas deste arquivo estão em test_golden.py (sem render real).
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

import numpy as np
from PIL import Image

AQUI = Path(__file__).resolve().parent
SKILL = AQUI.parent
DISCO_MINIMO = int(1.5 * 1024 ** 3)       # abaixo disto o script para: o golden não vale um disco cheio
FALLBACK_COFRE = Path("/Users/ugopirangi/Developer/UGO's Second Brain")
PASTA_SKILL_NO_COFRE = Path("01 EMPRESAS/MOTION PERFORM/SISTEMAS/GERAR MEDIAKIT")
PASTA_CLIENTES = Path("01 EMPRESAS/MOTION PERFORM/CLIENTES")

# Cada kit: onde mora, o que o render recebe e de onde saem as fontes. Os flags são os do regressao.sh (--png --fundo
# --fontes; a bancada usa só --png --fontes). Kit com `receitas` NÃO leva --todas: o render.py trata --todas como "forçar
# as três direções" e ignoraria as receitas, que são o que esses kits entregam (sprint r1 a r3, AME r1).
KITS = {
    "sprint-2027":      dict(onde="cliente", rel="SPRINT UBATUBA RUN/MEDIAKIT/sprint-2027", flags=["--png", "--fundo"], fontes="fontes-receitas"),
    "copa-ame-v2":      dict(onde="cliente", rel="AME CRIANCA/MEDIAKIT/copa-ame-v2", flags=["--png", "--fundo"], fontes="fontes"),
    "travessia-da-lua": dict(onde="skill", rel="exemplos/travessia-da-lua", flags=["--todas", "--png", "--fundo"], fontes="fontes"),
    "receitas-teste":   dict(onde="skill", rel="exemplos/receitas-teste", flags=["--png", "--fundo"], fontes="fontes"),
    "corre-por-elas":   dict(onde="skill", rel="bancada/corre-por-elas", flags=["--png"], fontes="fontes"),
}

# Campos que variam a cada execução sem mudar o kit: saem do plano. `hora`/`data` só saem quando o VALOR parece data ou
# hora (no plano da Sprint existe uma `data` que é conteúdo: "Sub-11").
CHAVES_VOLATEIS = {"gerado_em", "criado_em", "atualizado_em", "timestamp", "carimbo", "data_hora", "datahora", "session",
                   "session_id", "sessao", "sessao_id", "uuid", "run_id", "pid", "duracao_ms", "tempo_ms"}
CHAVES_TEMPORAIS = {"data", "hora", "horario", "date", "time"}
RE_DATA = re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?\b")
RE_HORA = re.compile(r"(?<![\d:])\d{2}:\d{2}:\d{2}(?:\.\d+)?(?![\d:])")
RE_UUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
RE_CAMINHO = re.compile(r"(?<![\w.])/(?:Users|private|tmp|var|Volumes|home|opt|System)/[^\s\"',;)\]]*")


def log(*a):
    print(*a, flush=True)


# ------------------------------------------------------------------------------------------------- arquivos e disco
def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_arquivo(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def raizes_do_clone(clone):
    """Todas as grafias do caminho do clone que podem aparecer num arquivo gerado (com e sem link simbólico), a mais
    longa primeiro."""
    return sorted({str(Path(clone)), str(Path(clone).resolve())}, key=len, reverse=True)


def sha256_sem_caminho(p, raizes):
    """sha256 do arquivo com o caminho do clone trocado por <KIT>: o golden e a conferência clonam em pastas diferentes
    e o HTML não pode divergir só por isso. Sem o caminho no arquivo, é o sha256 puro."""
    b = Path(p).read_bytes()
    for r in raizes:
        b = b.replace(r.encode(), b"<KIT>")
    return sha256_bytes(b)


def garantir_disco(pasta):
    livre = shutil.disk_usage(pasta).free
    if livre < DISCO_MINIMO:
        raise SystemExit(f"PARADO: {livre / 1024 ** 3:.2f} GB livres em {pasta}; o mínimo é {DISCO_MINIMO / 1024 ** 3:.1f} GB")
    return livre


def apagar_seguro(alvo, raiz):
    """Apaga `alvo` só se estiver DENTRO de `raiz` (a pasta de clones que este script criou). Nada fora dela."""
    a, r = Path(alvo).resolve(), Path(raiz).resolve()
    if a == r or r not in a.parents:
        raise RuntimeError(f"recusei apagar {a}: não está dentro de {r}")
    if a.is_symlink() or a.is_file():
        a.unlink()
    elif a.exists():
        shutil.rmtree(a)


def clonar(origem, destino, raiz):
    """Clone do APFS (cp -cR) de tudo da pasta do kit, menos a saida/ original. O kit real só é LIDO."""
    origem, destino = Path(origem).resolve(), Path(destino)
    d = destino.resolve() if destino.exists() else destino.parent.resolve() / destino.name
    if d == origem or origem in d.parents or d in origem.parents:
        raise RuntimeError(f"a pasta de clones ({destino}) não pode ficar dentro ou em volta do kit ({origem})")
    if destino.exists():
        apagar_seguro(destino, raiz)
    destino.mkdir(parents=True)
    for e in sorted(origem.iterdir()):
        if e.name == "saida":
            continue
        subprocess.run(["cp", "-cR", str(e), str(destino / e.name)], check=True)


def hash_entrada(clone):
    """{caminho relativo: sha256} de cada arquivo da pasta do kit (menos saida/ e lixo do Finder)."""
    clone = Path(clone)
    out = {}
    for raiz, dirs, arqs in os.walk(clone):
        dirs[:] = sorted(d for d in dirs if not (Path(raiz) == clone and d == "saida"))
        for a in sorted(arqs):
            if a == ".DS_Store":
                continue
            p = Path(raiz) / a
            if p.is_file():
                out[p.relative_to(clone).as_posix()] = sha256_arquivo(p)
    return out


def biblioteca_de(pipeline):
    """A biblioteca de objetos que este pipeline enxerga (biblioteca.PADRAO é relativo ao arquivo, não ao cofre vivo).

    Lição de 12/10/2026: o pipeline congelado por `git archive` só da pasta da skill não enxergava
    MARKETING/BIBLIOTECA DE OBJETOS, e o QA do golden saiu com "OCR pendente" em todo elemento registrado.
    O congelado precisa ver a mesma biblioteca que o vivo (cópia ou link simbólico), e o meta.json grava a
    impressão dela para o conferir acusar quando a biblioteca mudou.
    """
    return Path(pipeline).resolve().parent.parent.parent / "MARKETING" / "BIBLIOTECA DE OBJETOS"


def impressao_biblioteca(pipeline):
    """sha256 do indice.json da biblioteca que o pipeline enxerga; None quando ela não existe."""
    ind = biblioteca_de(pipeline) / "indice.json"
    return sha256_arquivo(ind) if ind.is_file() else None


def impressao_pipeline(pipeline):
    """Uma impressão digital do código congelado (para o meta.json dizer exatamente o que foi capturado)."""
    h = hashlib.sha256()
    n = 0
    pipeline = Path(pipeline)
    for raiz, dirs, arqs in os.walk(pipeline):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for a in sorted(arqs):
            if a == ".DS_Store" or a.endswith(".pyc"):
                continue
            p = Path(raiz) / a
            h.update(p.relative_to(pipeline).as_posix().encode() + b"\0" + sha256_arquivo(p).encode() + b"\n")
            n += 1
    return {"sha256": h.hexdigest(), "arquivos": n}


# ------------------------------------------------------------------------------------------------- normalização
def normalizar_texto(t, raizes=()):
    """Tira do texto o que varia sem o kit variar: caminho do clone, caminho absoluto, data, hora e id."""
    for r in sorted(raizes, key=len, reverse=True):
        t = t.replace(r, "<KIT>")
    t = RE_CAMINHO.sub("<CAMINHO>", t)
    t = RE_UUID.sub("<ID>", t)
    t = RE_DATA.sub("<DATA>", t)
    t = RE_HORA.sub("<HORA>", t)
    return t


def normalizar_plano(obj, raizes=()):
    """plano-elementos-*.json sem campos de data, hora, caminho absoluto ou id de sessão. Chave volátil sai; valor que
    parece caminho, data, hora ou id vira marcador; o resto (geometria, ids de elemento, sha256 de imagem) fica."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            kl = str(k).lower()
            if kl in CHAVES_VOLATEIS:
                continue
            if kl in CHAVES_TEMPORAIS and isinstance(v, str) and (RE_DATA.search(v) or RE_HORA.search(v)):
                continue
            out[k] = normalizar_plano(v, raizes)
        return out
    if isinstance(obj, list):
        return [normalizar_plano(v, raizes) for v in obj]
    if isinstance(obj, str):
        return normalizar_texto(obj, raizes)
    return obj


def normalizar_qa(saida_do_qa, raizes=()):
    """Só as linhas FALHA e AVISO, sem o caminho do clone, ordenadas."""
    linhas = []
    for l in saida_do_qa.splitlines():
        if l.startswith(("FALHA", "AVISO")):
            l = l.rstrip()
            for r in sorted(raizes, key=len, reverse=True):
                l = l.replace(r, "<KIT>")
            linhas.append(l)
    return sorted(linhas)


def normalizar_pdffonts(saida):
    """Uma linha por fonte: nome (sem a etiqueta de subconjunto ABCDEF+), tipo, codificação, emb sub uni. Sem o número do
    objeto, que muda quando o PDF ganha ou perde qualquer outra coisa. Colunas pelo traçado do cabeçalho."""
    linhas = saida.splitlines()
    for i, l in enumerate(linhas):
        if re.fullmatch(r"-+( +-+)+", l.strip()):
            tracos = [(m.start(), m.end()) for m in re.finditer(r"-+", l)]
            corpo = linhas[i + 1:]
            break
    else:
        return []
    out = []
    for l in corpo:
        if not l.strip():
            continue
        cols = [l[a:b].strip() for a, b in tracos[:-1]]      # a última coluna é "object ID"
        cols[0] = re.sub(r"^[A-Z]{6}\+", "", cols[0])
        out.append(" | ".join(cols))
    return sorted(out)


def normalizar_pdfimages(saida):
    """Uma linha por imagem: página, número, tipo, largura, altura, cor, comp, bpc, enc, interp e ppi. Sem object ID,
    tamanho em bytes e razão (mudam por detalhe de compressão sem mudar a imagem). Mantém a ordem do PDF."""
    out = []
    for l in saida.splitlines():
        t = l.split()
        if len(t) >= 14 and t[0].isdigit() and t[1].isdigit():
            out.append(" ".join(t[:10] + t[12:14]))
    return out


# ------------------------------------------------------------------------------------------------- extração
def _roda(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def extrair_pdf(pdf):
    pdf = Path(pdf)
    info = _roda(["pdfinfo", str(pdf)]).stdout
    m = re.search(r"^Pages:\s+(\d+)", info, re.M)
    t = re.search(r"^Page size:\s+(.+)$", info, re.M)
    texto = _roda(["pdftotext", "-layout", str(pdf), "-"]).stdout.split("\f")
    if texto and texto[-1] == "":
        texto.pop()                                 # o pdftotext fecha cada página com \f: sobra um vazio no fim
    return {"bytes": pdf.stat().st_size, "paginas": int(m.group(1)) if m else None,
            "tamanho_pagina": t.group(1).strip() if t else None,
            "fontes": normalizar_pdffonts(_roda(["pdffonts", str(pdf)]).stdout),
            "imagens": normalizar_pdfimages(_roda(["pdfimages", "-list", str(pdf)]).stdout),
            "texto": texto}


def extrair(clone, saida_do_qa):
    """Tudo que o golden guarda de uma rodada, lido da saida/ do clone (o QA já rodou: ele precisa dos PNG)."""
    saida = Path(clone) / "saida"
    raizes = raizes_do_clone(clone)
    html = {p.name: sha256_sem_caminho(p, raizes) for p in sorted((saida / "html").glob("*.html"))}
    png = {p.name: sha256_arquivo(p) for p in sorted((saida / "png").glob("*.png"))}
    fundo = {p.name: sha256_arquivo(p) for p in sorted((saida / "fundo").glob("*")) if p.is_file()} if (saida / "fundo").is_dir() else {}
    plano = {p.name: normalizar_plano(json.loads(p.read_text(encoding="utf-8")), raizes)
             for p in sorted(saida.glob("plano-elementos-*.json"))}
    pdf = {p.name: extrair_pdf(p) for p in sorted(saida.glob("*.pdf"))}
    return {"html": html, "png": png, "fundo": fundo, "plano": plano, "qa": normalizar_qa(saida_do_qa, raizes), "pdf": pdf}


# ------------------------------------------------------------------------------------------------- pixels e ruído
def pixels_diferentes(a, b):
    """(pixels diferentes, tamanho_a, tamanho_b). Pixel diferente = qualquer canal diferente. Tamanho diferente conta
    a área inteira da maior (nunca cabe num piso razoável)."""
    ia = np.asarray(Image.open(a).convert("RGBA"))
    ib = np.asarray(Image.open(b).convert("RGBA"))
    ta, tb = (ia.shape[1], ia.shape[0]), (ib.shape[1], ib.shape[0])
    if ia.shape != ib.shape:
        return max(ia.shape[0] * ia.shape[1], ib.shape[0] * ib.shape[1]), ta, tb
    return int(np.any(ia != ib, axis=-1).sum()), ta, tb


def calcular_ruido(dir_ref, dir_novo):
    """{nome: pixels diferentes} entre as páginas de mesmo nome de duas pastas; página que falta num dos lados conta como
    a área inteira (-1 se nenhum dos dois tem o arquivo é impossível aqui)."""
    nomes = sorted({p.name for p in Path(dir_ref).glob("*") if p.is_file()} | {p.name for p in Path(dir_novo).glob("*") if p.is_file()})
    out = {}
    for n in nomes:
        a, b = Path(dir_ref) / n, Path(dir_novo) / n
        if not (a.is_file() and b.is_file()):
            out[n] = 1920 * 1080
        else:
            out[n] = pixels_diferentes(a, b)[0]
    return out


# ------------------------------------------------------------------------------------------------- comparação
def diff_json(a, b, caminho="", limite=5):
    """Primeiros caminhos onde dois JSON divergem."""
    out = []
    if type(a) is not type(b):
        return [caminho or "."]
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{caminho}.{k}")
            else:
                out += diff_json(a[k], b[k], f"{caminho}.{k}", limite)
            if len(out) >= limite:
                break
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(f"{caminho} (tamanho {len(a)} -> {len(b)})")
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff_json(x, y, f"{caminho}[{i}]", limite)
            if len(out) >= limite:
                break
    elif a != b:
        out.append(caminho)
    return out[:limite]


def comparar_kit(golden, novo, png_golden, png_novo, piso, entrada_golden=None, entrada_nova=None):
    """Compara a extração guardada (`golden`) com a nova (`novo`), as duas no formato de `extrair`. Devolve uma lista de
    divergências (nivel, tipo, item, detalhe): FALHA para o que muda o que o cliente recebe, AVISO para o resto.
    `piso` é o ruído do kit em pixels."""
    divs = []
    F = lambda tipo, item, det: divs.append(("FALHA", tipo, item, det))
    A = lambda tipo, item, det: divs.append(("AVISO", tipo, item, det))

    # PNG por página
    raster_diverge = False
    for n in sorted(set(golden["png"]) | set(novo["png"])):
        if n not in novo["png"]:
            F("PNG", n, "página sumiu"); raster_diverge = True
        elif n not in golden["png"]:
            F("PNG", n, "página nova"); raster_diverge = True
        elif golden["png"][n] != novo["png"][n]:
            dif, ta, tb = pixels_diferentes(Path(png_golden) / n, Path(png_novo) / n)
            if ta != tb:
                F("PNG", n, f"tamanho {ta[0]}x{ta[1]} -> {tb[0]}x{tb[1]}"); raster_diverge = True
            elif dif > piso:
                F("PNG", n, f"{dif} px diferentes (piso {piso})"); raster_diverge = True

    # PDF: páginas, texto por página, fontes, imagens (FALHA); tamanho em bytes (AVISO)
    for n in sorted(set(golden["pdf"]) | set(novo["pdf"])):
        if n not in novo["pdf"]:
            F("PDF", n, "arquivo sumiu"); continue
        if n not in golden["pdf"]:
            F("PDF", n, "arquivo novo"); continue
        g, v = golden["pdf"][n], novo["pdf"][n]
        if g["paginas"] != v["paginas"]:
            F("PDF", n, f"páginas {g['paginas']} -> {v['paginas']}")
        if g["tamanho_pagina"] != v["tamanho_pagina"]:
            F("PDF", n, f"tamanho de página {g['tamanho_pagina']} -> {v['tamanho_pagina']}")
        for i in range(max(len(g["texto"]), len(v["texto"]))):
            a = g["texto"][i] if i < len(g["texto"]) else None
            b = v["texto"][i] if i < len(v["texto"]) else None
            if a != b:
                F("TEXTO", f"{n} p.{i + 1}", "texto da página mudou" if a is not None and b is not None else "página sem par")
        if g["fontes"] != v["fontes"]:
            so_g, so_v = sorted(set(g["fontes"]) - set(v["fontes"])), sorted(set(v["fontes"]) - set(g["fontes"]))
            F("FONTES", n, f"pdffonts mudou; saiu {so_g or '-'}; entrou {so_v or '-'}")
        if g["imagens"] != v["imagens"]:
            so_g, so_v = len(set(g["imagens"]) - set(v["imagens"])), len(set(v["imagens"]) - set(g["imagens"]))
            F("IMAGENS", n, f"pdfimages -list mudou ({len(g['imagens'])} -> {len(v['imagens'])} imagens; {so_g} saíram, {so_v} entraram)")
        if g["bytes"] and abs(v["bytes"] - g["bytes"]) / g["bytes"] > 0.01:
            A("BYTES", n, f"{g['bytes']} -> {v['bytes']} bytes ({(v['bytes'] - g['bytes']) / g['bytes']:+.1%})")

    # QA: mesmas linhas
    so_g = list(golden["qa"]); so_v = list(novo["qa"])
    for l in list(so_g):
        if l in so_v:
            so_g.remove(l); so_v.remove(l)
    for l in so_v:
        F("QA", "linha a mais", l[:200])
    for l in so_g:
        F("QA", "linha a menos", l[:200])

    # HTML: informativo
    for n in sorted(set(golden["html"]) | set(novo["html"])):
        if n not in novo["html"]:
            A("HTML", n, "arquivo sumiu")
        elif n not in golden["html"]:
            A("HTML", n, "arquivo novo")
        elif golden["html"][n] != novo["html"][n]:
            A("HTML", n, "HTML diferente" + ("" if raster_diverge else " com raster igual (o HTML pode mudar sem mudar a página)"))

    # fundo (só hash: o PNG de fundo não é guardado) e plano de elementos: AVISO, o raster é quem manda
    for n in sorted(set(golden["fundo"]) | set(novo["fundo"])):
        if golden["fundo"].get(n) != novo["fundo"].get(n):
            A("FUNDO", n, "hash do PNG de fundo mudou (o PNG de fundo não é guardado: só o hash)")
    for n in sorted(set(golden["plano"]) | set(novo["plano"])):
        if n not in golden["plano"] or n not in novo["plano"]:
            A("PLANO", n, "arquivo de plano novo ou ausente")
        elif golden["plano"][n] != novo["plano"][n]:
            A("PLANO", n, "plano de elementos mudou em " + ", ".join(diff_json(golden["plano"][n], novo["plano"][n], limite=3)))

    # entrada do kit: explica uma divergência que não é do pipeline
    if entrada_golden is not None and entrada_nova is not None and entrada_golden != entrada_nova:
        mudou = sorted(k for k in set(entrada_golden) | set(entrada_nova) if entrada_golden.get(k) != entrada_nova.get(k))
        A("ENTRADA", f"{len(mudou)} arquivo(s)", "a pasta do kit mudou desde o golden: " + ", ".join(mudou[:4]) + (" ..." if len(mudou) > 4 else ""))
    return divs


def contar_dentro_do_piso(golden, novo, png_golden, png_novo, piso):
    """Quantas páginas diferem do golden mas ficam dentro do piso de ruído (informativo na tabela)."""
    n, maximo = 0, 0
    for nome, h in novo["png"].items():
        if nome in golden["png"] and golden["png"][nome] != h:
            dif, ta, tb = pixels_diferentes(Path(png_golden) / nome, Path(png_novo) / nome)
            if ta == tb and dif <= piso:
                n += 1; maximo = max(maximo, dif)
    return n, maximo


# ------------------------------------------------------------------------------------------------- gravar e carregar
def _linhas_sha(d, prefixo):
    return "".join(f"{h}  {prefixo}/{n}\n" for n, h in sorted(d.items()))


def _ler_sha(texto, prefixo):
    out = {}
    for l in texto.splitlines():
        if not l.strip():
            continue
        h, _, caminho = l.partition("  ")
        if caminho.startswith(prefixo + "/"):
            out[caminho[len(prefixo) + 1:]] = h
    return out


def gravar_golden(pasta, dados, entrada):
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "html.sha256").write_text(_linhas_sha(dados["html"], "html"), encoding="utf-8")
    (pasta / "png.sha256").write_text(_linhas_sha(dados["png"], "png") + _linhas_sha(dados["fundo"], "fundo"), encoding="utf-8")
    (pasta / "plano.json").write_text(json.dumps(dados["plano"], ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    (pasta / "qa.txt").write_text("".join(l + "\n" for l in dados["qa"]), encoding="utf-8")
    (pasta / "pdf.json").write_text(json.dumps(dados["pdf"], ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    (pasta / "entrada.sha256").write_text("".join(f"{h}  {n}\n" for n, h in sorted(entrada.items())), encoding="utf-8")


def carregar_golden(pasta):
    pasta = Path(pasta)
    png = (pasta / "png.sha256").read_text(encoding="utf-8")
    dados = {"html": _ler_sha((pasta / "html.sha256").read_text(encoding="utf-8"), "html"),
             "png": _ler_sha(png, "png"), "fundo": _ler_sha(png, "fundo"),
             "plano": json.loads((pasta / "plano.json").read_text(encoding="utf-8")),
             "qa": [l for l in (pasta / "qa.txt").read_text(encoding="utf-8").splitlines() if l],
             "pdf": json.loads((pasta / "pdf.json").read_text(encoding="utf-8"))}
    entrada = {}
    for l in (pasta / "entrada.sha256").read_text(encoding="utf-8").splitlines():
        h, _, n = l.partition("  ")
        if n:
            entrada[n] = h
    ruido = json.loads((pasta / "ruido.json").read_text(encoding="utf-8"))
    return dados, entrada, ruido


# ------------------------------------------------------------------------------------------------- render
def resolver_pipeline(p):
    p = Path(p).resolve()
    if (p / "render.py").is_file():
        return p
    if (p / "pipeline" / "render.py").is_file():
        return p / "pipeline"
    raise SystemExit(f"{p} não tem render.py (passe a pasta pipeline/ ou a pasta da skill)")


def raiz_do_cofre():
    try:
        comum = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], capture_output=True,
                               text=True, check=True, cwd=str(AQUI)).stdout.strip()
        cofre = Path(comum).parent
        if (cofre / PASTA_CLIENTES).is_dir():
            return cofre
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return Path(os.environ.get("MEDIAKIT_COFRE") or FALLBACK_COFRE)


def origem_do_kit(nome):
    c = KITS[nome]
    base = (raiz_do_cofre() / PASTA_CLIENTES) if c["onde"] == "cliente" else SKILL
    return base / c["rel"]


def escolher_kits(pedidos, disponiveis):
    nomes = [x for p in (pedidos or []) for x in p.split(",") if x]
    if not nomes:
        return list(disponiveis)
    ruins = [n for n in nomes if n not in disponiveis]
    if ruins:
        raise SystemExit(f"kit(s) desconhecido(s): {', '.join(ruins)}. Kits: {', '.join(disponiveis)}")
    return nomes


def rodar_render(pipeline, clone, nome):
    c = KITS[nome]
    cmd = [sys.executable, str(pipeline / "render.py"), str(clone), *c["flags"], "--fontes", str(Path(clone) / c["fontes"])]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(pipeline), timeout=3600)
    dt = time.time() - t0
    if r.returncode != 0:
        raise RuntimeError(f"render de {nome} falhou ({r.returncode}): {(r.stderr or r.stdout)[-1500:]}")
    return dt


def rodar_qa(pipeline, clone, ledger):
    cmd = [sys.executable, str(pipeline / "qa.py"), str(clone)]
    if ledger and Path(ledger).is_file():
        cmd += ["--ledger", str(ledger)]          # histórico congelado: o QA não varia só porque entrou kit novo nele
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(pipeline), timeout=1800)
    return r.stdout, time.time() - t0               # qa.py sai com 1 quando acha FALHA: a saída é o dado, não o código


# ------------------------------------------------------------------------------------------------- capturar
def instabilidade(r1, rk):
    """O que mudou entre a rodada 1 e a rodada k fora do raster (para o golden avisar que não é determinístico)."""
    out = {"html": sorted(n for n in set(r1["html"]) | set(rk["html"]) if r1["html"].get(n) != rk["html"].get(n)),
           "fundo": sorted(n for n in set(r1["fundo"]) | set(rk["fundo"]) if r1["fundo"].get(n) != rk["fundo"].get(n)),
           "plano": sorted(n for n in set(r1["plano"]) | set(rk["plano"]) if r1["plano"].get(n) != rk["plano"].get(n)),
           "qa": r1["qa"] != rk["qa"], "pdf": []}
    for n in sorted(set(r1["pdf"]) | set(rk["pdf"])):
        a, b = r1["pdf"].get(n), rk["pdf"].get(n)
        if not a or not b or any(a[c] != b[c] for c in ("paginas", "tamanho_pagina", "fontes", "imagens", "texto")):
            out["pdf"].append(n)
    return out


def capturar_kit(nome, destino, pipeline, clones, vezes, ledger):
    origem = origem_do_kit(nome)
    if not origem.is_dir():
        raise SystemExit(f"{nome}: pasta do kit não existe ({origem})")
    final = Path(destino) / nome
    if final.exists():
        raise SystemExit(f"{final} já existe: use outra data ou apague a pasta antes (o script não apaga golden pronto)")
    pasta = Path(destino) / f".parcial-{nome}"       # rascunho do próprio script: só vira <kit>/ quando o kit termina
    if pasta.exists():
        apagar_seguro(pasta, destino)
    clone = Path(clones) / nome
    log(f"\n== {nome}: clonando {origem}")
    garantir_disco(clones)
    clonar(origem, clone, clones)
    entrada = hash_entrada(clone)
    pasta.mkdir(parents=True)
    fundo_r1 = pasta / ".fundo-rodada-1"
    info = {"origem": str(origem), "vezes": vezes, "render_s": [], "qa_s": []}
    dados1, ruido_png, ruido_fundo, instab = None, {}, {}, {"html": [], "fundo": [], "plano": [], "qa": False, "pdf": []}
    for i in range(vezes):
        garantir_disco(clones)
        log(f"   rodada {i + 1}/{vezes}: render ...")
        dt = rodar_render(pipeline, clone, nome)
        log(f"   rodada {i + 1}: render {dt:.0f}s; qa ...")
        qa_out, dq = rodar_qa(pipeline, clone, ledger)
        dados = extrair(clone, qa_out)
        info["render_s"].append(round(dt, 1)); info["qa_s"].append(round(dq, 1))
        saida = clone / "saida"
        if i == 0:
            dados1 = dados
            gravar_golden(pasta, dados, entrada)
            shutil.move(str(saida / "png"), str(pasta / "png"))          # mesmo volume: renomeia, não copia
            if (saida / "fundo").is_dir():
                shutil.move(str(saida / "fundo"), str(fundo_r1))
        else:
            for n, v in calcular_ruido(pasta / "png", saida / "png").items():
                ruido_png[n] = max(ruido_png.get(n, 0), v)
            if fundo_r1.is_dir():
                for n, v in calcular_ruido(fundo_r1, saida / "fundo").items():
                    ruido_fundo[n] = max(ruido_fundo.get(n, 0), v)
            inst = instabilidade(dados1, dados)
            for c in ("html", "fundo", "plano", "pdf"):
                instab[c] = sorted(set(instab[c]) | set(inst[c]))
            instab["qa"] = instab["qa"] or inst["qa"]
        apagar_seguro(saida, clones)                                      # só a saida/ do CLONE
        log(f"   rodada {i + 1}: ok; saida do clone apagada; disco livre {shutil.disk_usage(clones).free / 1024 ** 3:.2f} GB")
    if fundo_r1.is_dir():
        shutil.rmtree(fundo_r1)
    for n in dados1["png"]:
        ruido_png.setdefault(n, 0)
    ruido = {"vezes": vezes, "max": max(ruido_png.values(), default=0), "pixels_por_pagina": dict(sorted(ruido_png.items())),
             "max_fundo": max(ruido_fundo.values(), default=0), "pixels_fundo": dict(sorted(ruido_fundo.items())),
             "instabilidade": instab,
             "aviso": "vezes=1: sem amostra de ruído, piso 0" if vezes < 2 else None}
    (pasta / "ruido.json").write_text(json.dumps(ruido, ensure_ascii=False, indent=1), encoding="utf-8")
    info.update(paginas_png=len(dados1["png"]), pdfs={n: v["bytes"] for n, v in dados1["pdf"].items()},
                falhas=sum(l.startswith("FALHA") for l in dados1["qa"]), avisos=sum(l.startswith("AVISO") for l in dados1["qa"]),
                piso_ruido=ruido["max"], instabilidade=instab)
    pasta.rename(final)
    log(f"   {nome}: {info['paginas_png']} páginas PNG, piso de ruído {ruido['max']} px, QA {info['falhas']} falha(s) {info['avisos']} aviso(s)")
    return info


def cmd_capturar(a):
    pipeline = resolver_pipeline(a.pipeline or AQUI)
    destino = Path(a.saida)
    destino = destino if destino.is_absolute() else SKILL / destino
    clones = Path(a.clones) if a.clones else Path(tempfile.gettempdir()) / "mk-golden-clones"
    clones.mkdir(parents=True, exist_ok=True)
    kits = escolher_kits(a.kits, list(KITS))
    destino.mkdir(parents=True, exist_ok=True)
    livre0 = garantir_disco(clones)
    ledger_origem = pipeline.parent / "memoria-mediakit" / "historico-kits.json"
    ledger = destino / "historico-kits.json"
    if ledger_origem.is_file() and not ledger.exists():
        shutil.copy2(ledger_origem, ledger)
    meta_p = destino / "meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {"kits": {}}
    meta.update(data=time.strftime("%Y-%m-%d %H:%M:%S"), pipeline=str(pipeline), impressao_pipeline=impressao_pipeline(pipeline),
                git_head=subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(AQUI)).stdout.strip(),
                pipeline_commit=a.commit, python=sys.version.split()[0], disco_livre_gb_antes=round(livre0 / 1024 ** 3, 2),
                biblioteca=str(biblioteca_de(pipeline)), impressao_biblioteca=impressao_biblioteca(pipeline))
    if meta["impressao_biblioteca"] is None:
        log(f"AVISO: o pipeline congelado não enxerga a biblioteca de objetos em {biblioteca_de(pipeline)}: "
            "o QA vai sair com 'OCR pendente' em todo elemento registrado (ligue ou copie a biblioteca viva ali)")
    erros = []
    for nome in kits:
        try:
            meta["kits"][nome] = capturar_kit(nome, destino, pipeline, clones, a.vezes, ledger)
        except (RuntimeError, subprocess.SubprocessError, OSError) as e:      # um kit que falha não derruba os outros
            erros.append(nome)
            log(f"   ERRO em {nome}: {e}")
            meta["kits"][nome] = {"erro": str(e)[:500]}
        meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")   # grava a cada kit: nada se perde
    if erros:
        log(f"\nGOLDEN INCOMPLETO: falharam {', '.join(erros)} (o rascunho fica em {destino}/.parcial-<kit>)")
        return 1
    log("\nGOLDEN capturado em", destino)
    return 0


# ------------------------------------------------------------------------------------------------- conferir
def imprimir_tabela(nome, divs, extra):
    falhas = [d for d in divs if d[0] == "FALHA"]
    avisos = [d for d in divs if d[0] == "AVISO"]
    log(f"\n== {nome}: {'OK' if not falhas else 'FALHA'}  ({len(falhas)} falha(s), {len(avisos)} aviso(s)){extra}")
    if not divs:
        return
    larg = max(len(d[2]) for d in divs)
    larg = min(larg, 44)
    log(f"   {'nível':<6} {'tipo':<8} {'item':<{larg}}  detalhe")
    for nivel, tipo, item, det in sorted(divs, key=lambda d: (d[0] != "FALHA", d[1], d[2])):
        log(f"   {nivel:<6} {tipo:<8} {item:<{larg}}  {det}")


def conferir_kit(nome, golden_dir, pipeline, clones, ledger):
    pasta = Path(golden_dir) / nome
    if not pasta.is_dir():
        raise SystemExit(f"{nome} não está no golden ({golden_dir})")
    dados_g, entrada_g, ruido = carregar_golden(pasta)
    origem = origem_do_kit(nome)
    clone = Path(clones) / nome
    garantir_disco(clones)
    log(f"\n== {nome}: clonando e renderizando com {pipeline}")
    clonar(origem, clone, clones)
    entrada_n = hash_entrada(clone)
    dt = rodar_render(pipeline, clone, nome)
    qa_out, _ = rodar_qa(pipeline, clone, ledger)
    novo = extrair(clone, qa_out)
    piso = int(ruido.get("max", 0))
    divs = comparar_kit(dados_g, novo, pasta / "png", clone / "saida" / "png", piso, entrada_g, entrada_n)
    dentro, maximo = contar_dentro_do_piso(dados_g, novo, pasta / "png", clone / "saida" / "png", piso)
    paginas = len(novo["png"])
    extra = f"; {paginas} páginas; render {dt:.0f}s; piso {piso} px"
    if dentro:
        extra += f"; {dentro} página(s) com diferença dentro do piso (máx {maximo} px)"
    apagar_seguro(clone / "saida", clones)
    return divs, extra


def cmd_conferir(a):
    pipeline = resolver_pipeline(a.pipeline or AQUI)
    golden = Path(a.golden)
    golden = golden if golden.is_absolute() else SKILL / golden
    if not (golden / "meta.json").is_file():
        raise SystemExit(f"{golden} não é um golden (falta meta.json)")
    meta = json.loads((golden / "meta.json").read_text(encoding="utf-8"))
    bib_meta, bib_vivo = meta.get("impressao_biblioteca"), impressao_biblioteca(pipeline)
    if bib_meta != bib_vivo:
        log(f"AVISO: a biblioteca de objetos mudou desde o golden (golden {str(bib_meta)[:12]}, agora {str(bib_vivo)[:12]}): "
            "diferenças de QA em 'OCR' e 'registrado' podem vir dela, não do código")
    clones = Path(a.clones) if a.clones else Path(tempfile.gettempdir()) / "mk-golden-conferir"
    clones.mkdir(parents=True, exist_ok=True)
    kits = escolher_kits(a.kits, [k for k in KITS if (golden / k).is_dir()])
    ledger = golden / "historico-kits.json"
    resumo = []
    for nome in kits:
        divs, extra = conferir_kit(nome, golden, pipeline, clones, ledger)
        imprimir_tabela(nome, divs, extra)
        resumo.append((nome, sum(d[0] == "FALHA" for d in divs), sum(d[0] == "AVISO" for d in divs)))
    log("\nresumo           falhas  avisos")
    for nome, f, av in resumo:
        log(f"{nome:<16} {f:>6}  {av:>6}")
    ok = all(f == 0 for _, f, _ in resumo)
    log(f"\nCONFERIR: {'VERDE' if ok else 'VERMELHO'} (golden de {meta.get('data', '?')}, pipeline {pipeline})")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="linha de base dos kits existentes")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capturar", help="renderiza os kits N vezes e grava o golden")
    c.add_argument("--saida", required=True, help="pasta do golden, ex.: bancada/golden/2026-10-12")
    c.add_argument("--pipeline", help="pasta pipeline/ congelada (padrão: esta)")
    c.add_argument("--kits", nargs="*", help="nomes (ou separados por vírgula); padrão: todos")
    c.add_argument("--vezes", type=int, default=2)
    c.add_argument("--clones", help="onde clonar os kits (padrão: pasta temporária do sistema)")
    c.add_argument("--commit", help="commit de onde o pipeline congelado foi extraído (só vai para o meta.json)")
    c.set_defaults(fn=cmd_capturar)
    f = sub.add_parser("conferir", help="renderiza com o pipeline vivo e compara com o golden")
    f.add_argument("--golden", required=True)
    f.add_argument("--kits", nargs="*")
    f.add_argument("--pipeline", help="pasta pipeline/ a conferir (padrão: esta, a viva)")
    f.add_argument("--clones", help="onde clonar os kits (padrão: pasta temporária do sistema)")
    f.set_defaults(fn=cmd_conferir)
    a = ap.parse_args(argv)
    if getattr(a, "vezes", 2) < 1:
        ap.error("--vezes precisa ser >= 1")
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())

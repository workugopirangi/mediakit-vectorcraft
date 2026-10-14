#!/usr/bin/env python3
"""
imagens_web.py: fotos gratuitas de biblioteca pública para o acervo[] do mídia kit (níveis 2 e 3 da origem de imagens).
Mesma rota e mesmas regras do carrossel (Etapa 4 do gerar-carrossel-motion): ID Unsplash, anti-repetição eterna,
folha de miniaturas para UM Read, critérios de tema. Sem banco pago, sem chave em arquivo, sem login, sem CAPTCHA.

Comandos:
  buscar <termo> --kit <pasta> [--max 8] [--ledger <md>]        busca pública do Unsplash (página de busca, como o curl do carrossel);
                                                                 com UNSPLASH_ACCESS_KEY ou PEXELS_API_KEY no ambiente, usa a API oficial
  id     <id|url> ... --kit <pasta> [--autor X --url Y]          candidatas por ID Unsplash, URL da página da foto ou URL do Pexels
  aceitar <id|n> --kit <pasta> --funcao manifesto [--legenda ..] [--foco "50% 40%"]
                                                                 escreve a entrada no acervo[], roda tratar.py preparar e registra o ID

Saídas em <kit>/acervo/candidatas/: <id>.jpg, folha.png (miniaturas numeradas), candidatas.json (id, fonte, autor, url, licença, largura, tamanho).

Filtro automático: ID já no ledger ou em historico-kits.json (recusa), Unsplash+ (pago, recusa), largura < 1920 px (recusa),
arquivo < 300 KB com 1920 px ou mais (recusa: quase sempre placeholder). O que o script NÃO enxerga fica com quem lê a folha:
tema específico, rosto famoso, logo de marca não parceira, texto em outro idioma, foto de outro cliente.

Ledger: padrão = BIBLIOTECA DE IDS UNSPLASH.md do vault (--ledger para outro). Seções 🚫, ❌ e 🚮 bloqueiam; ⏳ Candidatas libera.
Chaves de API só por variável de ambiente; nunca em arquivo nem em argumento.
"""
import argparse, html, io, json, unicodedata, os, re, shutil, subprocess, sys, tempfile, time, urllib.parse, urllib.request
from datetime import date
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
LEDGER_PADRAO = Path.home() / "Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/MARKETING/BIBLIOTECA DE IDS UNSPLASH.md"
HISTORICO_PADRAO = RAIZ / "memoria-mediakit/historico-kits.json"
SCHEMA = RAIZ / "schema/mediakit.schema.json"

# regex do carrossel (a antiga cortava o ID no meio); as âncoras impedem casar pedaço de número maior
ID_UNSPLASH = r"[0-9]{10,13}-[a-f0-9]{12}"
RE_ID = re.compile(rf"(?<![0-9a-f]){ID_UNSPLASH}(?![0-9a-f])")
RE_ID_PEXELS = re.compile(r"pexels-[0-9]+")
RE_CARTAO = re.compile(r'href="/photos/([^"]+)"[^>]*><img alt="([^"]*)"[^>]*?srcSet="https://(images|plus)\.unsplash\.com/([^?\s"]+)')

MIN_LARGURA = 1920
MIN_KB = 300
LARGURA_BAIXA = 2880  # 1,5× o uso, igual ao tratar.py preparar
LICENCAS = {
    "unsplash": ("Unsplash License", "https://unsplash.com/license",
                 "uso comercial livre, sem atribuição obrigatória; não libera pessoa identificável nem marca visível"),
    "pexels": ("Pexels License", "https://www.pexels.com/license/",
               "uso comercial livre, sem atribuição obrigatória; não libera pessoa identificável nem marca visível"),
}


def erro(msg):
    raise SystemExit(f"ERRO: {msg}")


# ---------- rede (curl puro, como o carrossel; sem disfarce de navegador) ----------
def curl(url, saida=None, tentativas=2):
    cmd = ["curl", "-sS", "-L", "-m", "60", "-w", "%{http_code}"] + (["-o", str(saida)] if saida else ["-o", "-"])
    for t in range(tentativas):
        r = subprocess.run(cmd + [url], capture_output=True)
        corpo, cod = (r.stdout[:-3], r.stdout[-3:].decode(errors="ignore")) if not saida else (b"", r.stdout.decode(errors="ignore")[-3:])
        if cod == "200":
            return corpo if not saida else True
        time.sleep(1.5)
    return None


def api_json(url, cabecalho):
    # urllib para a chave não aparecer na linha de comando (ps)
    req = urllib.request.Request(url, headers=cabecalho)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


# ---------- ledger e histórico ----------
def ler_ledger(caminho):
    """Retorna (bloqueados, livres): IDs sob ## Candidatas ficam livres; qualquer outra seção bloqueia."""
    p = Path(caminho)
    if not p.exists():
        erro(f"ledger não encontrado: {p}")
    secao, bloq, livres = "", set(), set()
    for linha in p.read_text(encoding="utf-8").splitlines():
        if linha.startswith("## "):
            secao = linha.lower()
        ids = set(RE_ID.findall(linha)) | set(RE_ID_PEXELS.findall(linha))
        (livres if "candidatas" in secao else bloq).update(ids)
    return bloq, livres - bloq


def ler_historico(caminho):
    p = Path(caminho)
    if not p.exists():
        return []
    d = json.loads(p.read_text(encoding="utf-8") or "[]")
    return d if isinstance(d, list) else erro(f"{p}: esperava uma lista")


def ids_do_historico(hist):
    return {f["id"] for k in hist for f in k.get("fotos", [])}


def gravar_atomico(caminho, texto):
    p = Path(caminho)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=p.name + ".")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(texto)
    os.replace(tmp, p)


def motivo_repetida(fid, bloq, hist_ids):
    if fid in bloq:
        return "ID já no ledger (foto usada fica bloqueada para sempre)"
    if fid in hist_ids:
        return "ID já em historico-kits.json (usada em outro kit)"
    return None


def registrar_ledger(caminho, c, kit_nome, funcao):
    """Aditivo: acrescenta a linha ao fim da seção 🚫 Já usadas e tira o ID de ⏳ Candidatas, se estava lá."""
    p = Path(caminho)
    linhas = p.read_text(encoding="utf-8").split("\n")
    fid = c["id"]
    # tira da seção Candidatas, se estava lá
    saida, secao = [], ""
    for l in linhas:
        if l.startswith("## "):
            secao = l.lower()
        if "candidatas" in secao and fid in l and l.lstrip().startswith("- "):
            continue
        saida.append(l)
    nova = f"- 🚫 `{fid}`, {c.get('descricao') or 'foto de biblioteca pública'}. Usado: mediakit {kit_nome} {funcao} #mediakit. 🚫 NÃO REUSAR"
    ini = next((i for i, l in enumerate(saida) if l.startswith("## ") and "já usadas" in l.lower()), None)
    if ini is None:
        saida += ["", "## 🚫 Já usadas (BLOQUEADAS PERMANENTEMENTE)", "", nova]
    else:
        fim = next((i for i in range(ini + 1, len(saida)) if saida[i].startswith("## ") or saida[i].strip() == "---"), len(saida))
        while fim > ini + 1 and saida[fim - 1].strip() == "":
            fim -= 1
        saida.insert(fim, nova)
    gravar_atomico(p, "\n".join(saida))


def registrar_historico(caminho, c, kit_nome, funcao):
    hist = ler_historico(caminho)
    foto = {"id": c["id"], "fonte": c["fonte"], "autor": c["autor"], "url": c["url"], "funcao": funcao}
    reg = next((k for k in hist if k.get("kit") == kit_nome), None)
    if reg is None:
        reg = {"kit": kit_nome, "data": date.today().isoformat(), "fotos": []}
        hist.append(reg)
    reg["fotos"].append(foto)
    gravar_atomico(caminho, json.dumps(hist, ensure_ascii=False, indent=2) + "\n")


# ---------- metadados ----------
def meta_pagina_unsplash(url_pagina):
    """JSON-LD da página pública da foto: autor, tamanho original, ID da imagem. Sem login."""
    corpo = curl(url_pagina)
    if not corpo:
        return None
    txt = corpo.decode("utf-8", "ignore")
    for m in re.finditer(r'application/ld\+json[^>]*>(.*?)</script>', txt, re.S):
        try:
            d = json.loads(m.group(1))
        except ValueError:
            continue
        if d.get("@type") == "ImageObject":
            achou = RE_ID.search(d.get("contentUrl", ""))
            if not achou:
                return None
            return dict(id=achou.group(0), autor=(d.get("author") or {}).get("name"), largura=int(re.sub(r"\D", "", d.get("width", "0")) or 0),
                        descricao=d.get("name") or d.get("description"), data_foto=(d.get("datePublished") or "")[:10])
    return None


def id_de_entrada(e):
    """Aceita ID puro, URL de imagem, URL de página (/photos/slug), ou Pexels (URL ou pexels-N)."""
    m = RE_ID.search(e)
    if m:
        return ("unsplash", m.group(0), None)
    m = re.search(r"pexels\.com/(?:[a-z-]+/)?photo/[^\s?]*?-(\d+)/?", e) or re.search(r"images\.pexels\.com/photos/(\d+)", e) or re.fullmatch(r"pexels-(\d+)", e)
    if m:
        return ("pexels", f"pexels-{m.group(1)}", None)
    if "unsplash.com/photos/" in e:
        return ("unsplash", None, e.split("?")[0])
    erro(f"não entendi a entrada `{e}` (use ID Unsplash `{ID_UNSPLASH}`, URL da foto no Unsplash ou do Pexels)")


# ---------- busca ----------
def buscar_unsplash_publico(termo, limite):
    slug = urllib.parse.quote(re.sub(r"\s+", "-", termo.strip().lower()))
    corpo = curl(f"https://unsplash.com/s/photos/{slug}")
    if not corpo:
        erro("a busca pública do Unsplash não respondeu; tente de novo, passe IDs/URLs com `id`, ou defina UNSPLASH_ACCESS_KEY")
    out, vistos = [], set()
    for m in RE_CARTAO.finditer(corpo.decode("utf-8", "ignore")):
        slug_foto, alt, host, caminho = m.groups()
        if slug_foto in vistos:
            continue
        vistos.add(slug_foto)
        achou = RE_ID.search(caminho)
        if host == "plus" or not achou:  # Unsplash+ é pago e tem outra licença
            out.append(dict(recusa="Unsplash+ (pago, outra licença)", descricao=html.unescape(alt), url=f"https://unsplash.com/photos/{slug_foto}"))
            continue
        out.append(dict(fonte="unsplash", id=achou.group(0), descricao=html.unescape(alt), url=f"https://unsplash.com/photos/{slug_foto}"))
    return out


def buscar_unsplash_api(termo, limite, chave):
    d = api_json("https://api.unsplash.com/search/photos?" + urllib.parse.urlencode({"query": termo, "per_page": min(30, limite * 3), "orientation": "landscape"}),
                 {"Authorization": f"Client-ID {chave}", "Accept-Version": "v1"})
    out = []
    for f in d.get("results", []):
        achou = RE_ID.search(f["urls"]["raw"])
        if not achou:
            continue
        out.append(dict(fonte="unsplash", id=achou.group(0), descricao=f.get("alt_description") or f.get("description") or "", url=f["links"]["html"],
                        autor=f["user"]["name"], largura=f["width"], baixar=f["urls"]["raw"], ping=f["links"].get("download_location")))
    return out


def buscar_pexels_api(termo, limite, chave):
    d = api_json("https://api.pexels.com/v1/search?" + urllib.parse.urlencode({"query": termo, "per_page": min(30, limite * 3), "orientation": "landscape"}), {"Authorization": chave})
    return [dict(fonte="pexels", id=f"pexels-{f['id']}", descricao=f.get("alt") or "", url=f["url"], autor=f["photographer"], largura=f["width"], baixar=f["src"]["original"])
            for f in d.get("photos", [])]


# ---------- processamento comum ----------
def url_download(c):
    if c["fonte"] == "unsplash":
        base = c.get("baixar") or f"https://images.unsplash.com/photo-{c['id']}"
        return f"{base}{'&' if '?' in base else '?'}w={LARGURA_BAIXA}&q=85&fm=jpg&fit=max"
    return f"{c['baixar']}?auto=compress&cs=tinysrgb&w={LARGURA_BAIXA}" if "baixar" in c else None


def processar(brutas, kit, maximo, ledger, historico, termo=None, limpar=False):
    kit = Path(kit); dest = kit / "acervo/candidatas"; dest.mkdir(parents=True, exist_ok=True)
    if limpar:
        for velho in dest.glob("*.jpg"):
            velho.unlink()
    bloq, _ = ler_ledger(ledger)
    hist_ids = ids_do_historico(ler_historico(historico))
    ok, recusadas = [], []

    def recusa(c, why):
        recusadas.append({"id": c.get("id"), "url": c.get("url"), "motivo": why})
        print(f"RECUSADA {c.get('id') or c.get('url')}: {why}")

    for c in brutas:
        if len(ok) >= maximo:
            break
        if c.get("recusa"):
            recusa(c, c["recusa"]); continue
        if c.get("id"):
            why = motivo_repetida(c["id"], bloq, hist_ids)
            if why:
                recusa(c, why); continue
        if c["fonte"] == "unsplash" and (not c.get("autor") or not c.get("id")) and c.get("url"):
            m = meta_pagina_unsplash(c["url"])
            time.sleep(0.4)
            if not m:
                recusa(c, "página da foto não respondeu ou sem dados (sem autor não entra)"); continue
            c.update({k: v for k, v in m.items() if v and not c.get(k)})
            if c.get("id") != m["id"]:
                c["id"] = m["id"]
            why = motivo_repetida(c["id"], bloq, hist_ids)
            if why:
                recusa(c, why); continue
            if m["largura"] and m["largura"] < MIN_LARGURA:
                recusa(c, f"largura {m['largura']} px < {MIN_LARGURA} px (metadado da página)"); continue
        if c.get("largura") and c["largura"] < MIN_LARGURA:
            recusa(c, f"largura {c['largura']} px < {MIN_LARGURA} px (metadado)"); continue
        alvo = dest / f"{c['id']}.jpg"
        url = url_download(c)
        if not url or not curl(url, alvo):
            recusa(c, "download falhou"); alvo.unlink(missing_ok=True); continue
        try:
            with Image.open(alvo) as im:
                im = ImageOps.exif_transpose(im); w, h = im.size
        except Exception:
            recusa(c, "arquivo baixado não é imagem"); alvo.unlink(missing_ok=True); continue
        kb = alvo.stat().st_size / 1024
        if w < MIN_LARGURA:
            recusa(c, f"largura {w} px < {MIN_LARGURA} px"); alvo.unlink(); continue
        if kb < MIN_KB:
            recusa(c, f"{kb:.0f} KB < {MIN_KB} KB com {w} px (placeholder ou imagem vazia)"); alvo.unlink(); continue
        nome_lic, url_lic, resumo = LICENCAS[c["fonte"]]
        reg = dict(id=c["id"], fonte=c["fonte"], autor=c.get("autor"), url=c.get("url"), licenca=nome_lic, url_licenca=url_lic, resumo_licenca=resumo,
                   largura=w, altura=h, tamanho_kb=round(kb), descricao=c.get("descricao"), arquivo=str(alvo.relative_to(kit)), baixada_em=date.today().isoformat())
        if c.get("ping"):  # regra da API do Unsplash: avisar o download
            try: api_json(c["ping"], {"Authorization": f"Client-ID {os.environ['UNSPLASH_ACCESS_KEY']}"})
            except Exception: pass
        ok.append(reg)
        print(f"OK {c['id']} {w}x{h} {kb:.0f} KB  {c.get('autor')}  {(c.get('descricao') or '')[:50]}")
        time.sleep(0.4)
    # várias buscas somam: a folha mostra tudo que sobrou, com numeração contínua (--limpar recomeça)
    cj = dest / "candidatas.json"
    antes = {"termos": [], "candidatas": [], "recusadas": []}
    if cj.exists() and not limpar:
        antes.update(json.loads(cj.read_text(encoding="utf-8")))
    novos = {c["id"] for c in ok}
    todas = [c for c in antes["candidatas"] if c["id"] not in novos and (kit / c["arquivo"]).exists()] + ok
    termos = antes.get("termos", []) + ([termo] if termo else [])
    gravar_atomico(cj, json.dumps(dict(termos=termos, data=date.today().isoformat(), ledger=str(ledger), candidatas=todas, recusadas=antes["recusadas"] + recusadas), ensure_ascii=False, indent=2) + "\n")
    ok = todas
    if ok:
        folha(ok, kit, dest / "folha.png")
        print("\nnumeração da folha:")
        for n, c in enumerate(ok, 1):
            print(f"  #{n} {c['id']}  {c.get('autor')}  {(c.get('descricao') or '')[:60]}")
        print(f"\nfolha: {dest / 'folha.png'}  (UM Read)\ncandidatas.json: {dest / 'candidatas.json'}")
        print("Confira na folha: tema específico, rosto famoso, logo de marca não parceira, texto em outro idioma, foto de outro cliente.")
    else:
        print("\nNenhuma candidata passou no filtro.")
    return ok


def folha(cands, kit, saida, colunas=4, mw=480, mh=320, barra=44):
    """Uma imagem só com todas as candidatas numeradas: um Read substitui N."""
    fonte = None
    for f in ("/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(f).exists():
            fonte = ImageFont.truetype(f, 22); break
    if fonte is None:  # fonte padrão do Pillow não tem acento: o rótulo perde os acentos em vez de sair quadradinho
        fonte = ImageFont.load_default(size=22)
        sem_acento = lambda t: unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    else:
        sem_acento = lambda t: t
    linhas = (len(cands) + colunas - 1) // colunas
    S = Image.new("RGB", (colunas * mw, linhas * (mh + barra)), (24, 24, 24))
    d = ImageDraw.Draw(S)
    for i, c in enumerate(cands):
        x, y = (i % colunas) * mw, (i // colunas) * (mh + barra)
        with Image.open(Path(kit) / c["arquivo"]) as im:
            t = ImageOps.fit(ImageOps.exif_transpose(im).convert("RGB"), (mw - 6, mh - 6), Image.LANCZOS)
        S.paste(t, (x + 3, y + 3))
        d.rectangle([x, y + mh, x + mw, y + mh + barra], fill=(0, 0, 0))
        d.text((x + 8, y + mh + 10), f"#{i + 1}  {c['largura']}x{c['altura']}  {c['tamanho_kb']} KB  {sem_acento((c.get('autor') or '?')[:18])}", fill=(255, 255, 255), font=fonte)
        d.ellipse([x + 10, y + 10, x + 62, y + 62], fill=(232, 48, 122))
        d.text((x + 36, y + 36), str(i + 1), fill=(255, 255, 255), font=fonte, anchor="mm")
    S.save(saida, optimize=True)


# ---------- comandos ----------
def cmd_buscar(a):
    termo = a.termo
    chave_u, chave_p = os.environ.get("UNSPLASH_ACCESS_KEY"), os.environ.get("PEXELS_API_KEY")
    if a.fonte == "pexels":
        if not chave_p:
            erro("Pexels exige PEXELS_API_KEY no ambiente (a página pública do Pexels bloqueia robôs e não vamos contornar). Use `--fonte unsplash` ou `id`.")
        brutas = buscar_pexels_api(termo, a.max, chave_p)
    elif chave_u:
        brutas = buscar_unsplash_api(termo, a.max, chave_u)
    else:
        brutas = buscar_unsplash_publico(termo, a.max)
    print(f"{len(brutas)} resultado(s) para `{termo}`")
    processar(brutas, a.kit, a.max, a.ledger, a.historico, termo, a.limpar)


def cmd_id(a):
    brutas = []
    for e in a.entradas:
        fonte, fid, url = id_de_entrada(e)
        c = dict(fonte=fonte, id=fid, url=url or (a.url if fonte == "unsplash" else None), autor=a.autor)
        if fonte == "pexels":
            chave = os.environ.get("PEXELS_API_KEY")
            if not chave:
                erro("Pexels por ID exige PEXELS_API_KEY no ambiente (sem ela não há autor nem arquivo original)")
            f = api_json(f"https://api.pexels.com/v1/photos/{fid.split('-')[1]}", {"Authorization": chave})
            c.update(descricao=f.get("alt") or "", url=f["url"], autor=f["photographer"], largura=f["width"], baixar=f["src"]["original"])
        brutas.append(c)
    processar(brutas, a.kit, len(brutas), a.ledger, a.historico, "id: " + " ".join(a.entradas), a.limpar)


def funcoes_validas():
    return set(json.loads(SCHEMA.read_text(encoding="utf-8"))["properties"]["acervo"]["items"]["properties"]["funcao"]["enum"])


def cmd_aceitar(a):
    kit = Path(a.kit)
    cj = kit / "acervo/candidatas/candidatas.json"
    if not cj.exists():
        erro(f"{cj} não existe: rode `buscar` ou `id` antes")
    cands = json.loads(cj.read_text(encoding="utf-8"))["candidatas"]
    c = next((x for x in cands if x["id"] == a.id or (a.id.isdigit() and cands.index(x) + 1 == int(a.id))), None)
    if not c:
        erro(f"`{a.id}` não está em candidatas.json (só entra o que passou no filtro)")
    faltam = [k for k in ("licenca", "autor", "url") if not c.get(k)]
    if faltam:
        erro(f"{c['id']}: sem {', '.join(faltam)}; nada entra no acervo sem licença, autor e URL (use `id <url-da-página> ` ou --autor/--url)")
    if a.funcao not in funcoes_validas():
        erro(f"função `{a.funcao}` inválida (schema: {', '.join(sorted(funcoes_validas()))})")
    mk = kit / "mediakit.json"
    k = json.loads(mk.read_text(encoding="utf-8"))
    aid = a.acervo_id or c["id"]
    if any(x.get("id") == aid for x in k.get("acervo", [])):
        erro(f"acervo já tem id `{aid}`")
    bloq, _ = ler_ledger(a.ledger)
    why = motivo_repetida(c["id"], bloq, ids_do_historico(ler_historico(a.historico)))
    if why:
        erro(f"{c['id']}: {why}")
    origem = kit / c["arquivo"]
    if not origem.exists():
        erro(f"arquivo da candidata sumiu: {origem}")
    saida = kit / "acervo/tratado" / f"{c['id']}.jpg"
    saida.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, str(AQUI / "tratar.py"), "preparar", str(origem), str(saida)], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        erro("tratar.py preparar falhou: " + r.stderr.strip())
    nome_fonte = "Unsplash" if c["fonte"] == "unsplash" else "Pexels"
    entrada = dict(id=aid, arquivo=f"acervo/tratado/{c['id']}.jpg", funcao=a.funcao, direito_uso=True, credito=f"Foto: {c['autor']} / {nome_fonte}",
                   edicao=None, gerada=False, rotulo=None, legenda=a.legenda, foco=a.foco,
                   fonte=c["fonte"], autor=c["autor"], url=c["url"], licenca=c["licenca"], url_licenca=c["url_licenca"], id_foto=c["id"], obtida_em=c["baixada_em"])
    k.setdefault("acervo", []).append(entrada)
    gravar_atomico(mk, json.dumps(k, ensure_ascii=False, indent=2) + "\n")
    kit_nome = k.get("evento", {}).get("nome") or kit.name
    registrar_ledger(a.ledger, c, kit_nome, a.funcao)
    registrar_historico(a.historico, c, kit_nome, a.funcao)
    print(f"ACEITA {c['id']} ({c['autor']}, {c['licenca']}) como `{aid}` função {a.funcao}\n  acervo: {mk}\n  ledger: {a.ledger}\n  historico: {a.historico}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def comum(p):
        p.add_argument("--kit", required=True, help="pasta do kit (onde está o mediakit.json)")
        p.add_argument("--ledger", default=str(LEDGER_PADRAO), help="BIBLIOTECA DE IDS UNSPLASH.md (padrão: a do vault)")
        p.add_argument("--historico", default=str(HISTORICO_PADRAO), help="historico-kits.json")
        p.add_argument("--limpar", action="store_true", help="descarta as candidatas de buscas anteriores (por padrão elas somam)")
    b = sub.add_parser("buscar"); b.add_argument("termo"); b.add_argument("--max", type=int, default=8); b.add_argument("--fonte", choices=["unsplash", "pexels"], default="unsplash"); comum(b)
    i = sub.add_parser("id"); i.add_argument("entradas", nargs="+"); i.add_argument("--autor"); i.add_argument("--url"); comum(i)
    c = sub.add_parser("aceitar"); c.add_argument("id", help="ID da foto ou o número na folha"); c.add_argument("--funcao", required=True)
    c.add_argument("--legenda"); c.add_argument("--foco", default="50% 50%"); c.add_argument("--acervo-id"); comum(c)
    a = ap.parse_args()
    {"buscar": cmd_buscar, "id": cmd_id, "aceitar": cmd_aceitar}[a.cmd](a)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
regua.py: monta e confere a régua visual (as páginas de referência que a revisão compara com o kit).

Uso:
  python3 regua.py montar [--regua ../regua]     # cada página de cada PDF de regua/fontes.json vira regua/paginas/<origem>-NN.jpg
                                                 # + regua/folhas/<origem>.jpg (miniaturas numeradas, para classificar com 1 Read)
  python3 regua.py checar [--regua ../regua]     # indice.json: todo id existe; todo tipo da sequência-mestre tem referência

A régua não é um kit só: é o conjunto das referências das pesquisas. O indice.json diz, por tipo de página, quais páginas
de quais referências servem de comparação (a primeira é a principal). O papel de cada origem (regua, variante,
arquitetura, antiexemplo) vem do fontes.json; antiexemplo nunca entra como comparação positiva.
Página vertical contínua (Levinrun) é fatiada em 16:9.

Fontes da web (tipo "web" no fontes.json, sem "arquivo"): as imagens ficam em regua/paginas/web-<slug>-NN.jpg e entram nas folhas.
  python3 regua.py capturar [--origem web-xxx] [--listar]   # baixa até 4 imagens do projeto/artigo (fonte com "max" pode mais) (>= 1000 px de largura)
São referências internas de estúdio: não entram em entregável nem no pacote .skill (que já exclui regua/paginas).
"""
import argparse, datetime, io, json, re, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent
LARGURA = 1280
ALTURA = LARGURA * 9 // 16
MAX_WEB = 4          # no máximo 4 imagens por fonte web
MIN_LARG_WEB = 1000  # descarta imagem menor que isso (miniatura, logo, ícone)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
TIPOS = ["capa", "manifesto", "projecao", "publico", "prova", "divisor", "ativo_painel", "ativo_topo",
         "inventario_colunas", "divisor_cotas", "cota", "contato"]


def fonte_ui(tam):
    for c in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try: return ImageFont.truetype(c, tam)
        except Exception: pass
    return ImageFont.load_default()


def paginas_do_pdf(pdf, tmp):
    subprocess.run(["pdftoppm", "-scale-to-x", str(LARGURA), "-scale-to-y", "-1", "-jpeg", "-jpegopt", "quality=92",
                    str(pdf), str(tmp / "p")], check=True)
    return sorted(tmp.glob("p-*.jpg"), key=lambda p: int(p.stem.split("-")[-1]))


def fatiar(im):
    """Página muito mais alta que larga vira fatias 16:9; a última fatia é alinhada ao fim para não sobrar faixa vazia."""
    if im.height <= im.width * 1.2:
        return [im]
    tops = list(range(0, im.height - ALTURA + 1, ALTURA))
    if tops[-1] + ALTURA < im.height:
        tops.append(im.height - ALTURA)
    return [im.crop((0, t, im.width, t + ALTURA)) for t in tops]


def folha(imgs, ids, saida, titulo):
    tw, th, cols = 320, 180, 6
    rows = (len(imgs) + cols - 1) // cols
    S = Image.new("RGB", (cols * (tw + 12) + 12, 48 + rows * (th + 34)), (18, 18, 20))
    d = ImageDraw.Draw(S); f = fonte_ui(16)
    d.text((12, 14), titulo, fill=(240, 240, 240), font=fonte_ui(20))
    for i, (im, pid) in enumerate(zip(imgs, ids)):
        x = 12 + (i % cols) * (tw + 12); y = 48 + (i // cols) * (th + 34)
        t = im.copy(); t.thumbnail((tw, th)); S.paste(t, (x, y))
        d.text((x, y + th + 6), pid, fill=(220, 220, 220), font=f)
    S.save(saida, quality=85)


def montar(regua):
    cfg = json.loads((regua / "fontes.json").read_text(encoding="utf-8"))
    origem_dir = Path(cfg["pasta_origem"]).expanduser()
    (regua / "paginas").mkdir(parents=True, exist_ok=True); (regua / "folhas").mkdir(exist_ok=True)
    total, faltando = 0, []
    for fo in cfg["fontes"]:
        if fo.get("tipo") == "web":  # imagens vêm do 'capturar'; montar nunca apaga nem recria
            continue
        pdf = origem_dir / fo["arquivo"]
        if not pdf.exists():
            faltando.append(fo["arquivo"]); continue
        for velho in (regua / "paginas").glob(f"{fo['origem']}-*.jpg"):
            velho.unlink()
        with tempfile.TemporaryDirectory() as t:
            imgs, ids = [], []
            for p in paginas_do_pdf(pdf, Path(t)):
                for fatia in fatiar(Image.open(p).convert("RGB")):
                    pid = f"{fo['origem']}-{len(ids) + 1:02d}"
                    fatia.save(regua / "paginas" / f"{pid}.jpg", quality=82, optimize=True)
                    imgs.append(fatia); ids.append(pid)
            folha(imgs, ids, regua / "folhas" / f"{fo['origem']}.jpg", f"{fo['origem']}  ·  {fo['papel']}  ·  {fo['tom']}")
        total += len(ids); print(f"OK  {fo['origem']:<24} {len(ids):>3} páginas  ({fo['papel']})")
    for a in faltando:
        print(f"FALTA  {a} (não está em {origem_dir})")
    print(f"{total} páginas de PDF na régua")
    for fo in cfg["fontes"]:
        if fo.get("tipo") == "web":
            n = len(list((regua / "paginas").glob(f"{fo['origem']}-*.jpg")))
            print(f"OK  {fo['origem']:<24} {n:>3} imagens  ({fo['papel']}, web)" if n else f"AVISO  {fo['origem']} sem imagens (rode: regua.py capturar)")
    return 1 if faltando else 0


def candidatas_web(pagina):
    """URLs de imagem da página: og:image primeiro, depois as imagens grandes do DOM, na ordem em que aparecem.
    Behance: só módulos do projeto (/project_modules/); as miniaturas de 'projetos relacionados' ficam de fora."""
    pagina.wait_for_timeout(2500)
    for _ in range(40):  # galerias longas só carregam o fim (lazy load) depois de rolar tudo
        pagina.mouse.wheel(0, 1200); pagina.wait_for_timeout(300)
    r = pagina.evaluate("""()=>({og:(document.querySelector('meta[property="og:image"]')||{}).content,
        imgs:[...document.images].filter(i=>i.naturalWidth>=%d).map(i=>i.currentSrc||i.src)})""" % MIN_LARG_WEB)
    urls = ([r["og"]] if r.get("og") else []) + r["imgs"]
    if any("behance.net" in u for u in urls):
        urls = [u for u in urls if "/project_modules/" in u]
    vistos, saida = set(), []
    for u in urls:
        chave = re.sub(r"/(max_\d+|\d+|hd|source)(_webp)?/", "/", u).rsplit(".", 1)[0]  # mesma imagem em outro tamanho
        if chave not in vistos and not u.startswith("data:"):
            vistos.add(chave); saida.append(u)
    return saida


def capturar(regua, so_origem=None, listar=False):
    """Baixa as imagens das fontes web (Playwright headless, sem login). Grava web-<slug>-NN.jpg a 1280 px, JPEG q82.
    Fonte pode trazer "escolha": [posições 1-based entre as candidatas] para fixar quais imagens ficam."""
    from playwright.sync_api import sync_playwright
    fp = regua / "fontes.json"
    cfg = json.loads(fp.read_text(encoding="utf-8"))
    (regua / "paginas").mkdir(parents=True, exist_ok=True); (regua / "folhas").mkdir(exist_ok=True)
    hoje = datetime.date.today().isoformat()
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        ctx = nav.new_context(viewport={"width": 1400, "height": 900}, user_agent=UA)
        for fo in cfg["fontes"]:
            if fo.get("tipo") != "web" or (so_origem and fo["origem"] != so_origem):
                continue
            pg = ctx.new_page()
            try:
                pg.goto(fo["url"], wait_until="domcontentloaded", timeout=40000)
                urls = candidatas_web(pg)
            except Exception as e:
                print(f"FALHA  {fo['origem']}: {str(e)[:90]}"); pg.close(); continue
            pg.close()
            boas = []
            for u in urls:
                im = None
                # Behance serve o módulo em vários tamanhos; tenta o maior antes do que veio no DOM
                for v in ([re.sub(r"/project_modules/[^/]+/", "/project_modules/1400/", u), u] if "/project_modules/" in u else [u]):
                    try:
                        im = Image.open(io.BytesIO(ctx.request.get(v, timeout=30000).body())); im.load(); break
                    except Exception:
                        im = None
                if im is None:
                    continue
                if im.width < MIN_LARG_WEB or im.height < im.width * 0.25:  # miniatura ou faixa fina
                    continue
                boas.append((u, im.convert("RGB")))
            if listar:
                for i, (u, im) in enumerate(boas, 1):
                    print(f"  {fo['origem']} #{i}  {im.width}x{im.height}  {u}")
                continue
            escolha = fo.get("escolha") or list(range(1, MAX_WEB + 1))
            sel = [boas[i - 1] for i in escolha[:fo.get("max", MAX_WEB)] if 0 < i <= len(boas)]  # "max" na fonte sobe o teto de 4
            for velho in (regua / "paginas").glob(f"{fo['origem']}-*.jpg"):
                velho.unlink()
            imgs, ids, capt = [], [], []
            for u, im in sel:
                if im.width != LARGURA:
                    im = im.resize((LARGURA, round(im.height * LARGURA / im.width)), Image.LANCZOS)
                pid = f"{fo['origem']}-{len(ids) + 1:02d}"
                im.save(regua / "paginas" / f"{pid}.jpg", quality=82, optimize=True)
                imgs.append(im); ids.append(pid); capt.append({"id": pid, "imagem": u, "capturada_em": hoje})
            if ids:
                folha(imgs, ids, regua / "folhas" / f"{fo['origem']}.jpg", f"{fo['origem']}  ·  {fo['papel']}  ·  {fo['tom']}  ·  web")
            fo["capturas"] = capt
            print(f"OK  {fo['origem']:<24} {len(ids):>3} imagens de {len(boas)} candidatas")
        nav.close()
    if not listar:
        fp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


def checar(regua):
    cfg = json.loads((regua / "fontes.json").read_text(encoding="utf-8"))
    papel = {f["origem"]: f["papel"] for f in cfg["fontes"]}
    ip = regua / "indice.json"
    if not ip.exists():
        print("FALHA  regua/indice.json não existe"); return 1
    indice = json.loads(ip.read_text(encoding="utf-8"))["tipos"]
    falhas = 0
    for tipo in TIPOS:
        refs = indice.get(tipo, [])
        if not refs:
            print(f"FALHA  {tipo}: sem referência"); falhas += 1; continue
        if papel.get(refs[0]["id"].rsplit("-", 1)[0]) != "regua":
            print(f"AVISO  {tipo}: a referência principal não vem de um kit-régua ({refs[0]['id']})")
    for tipo, refs in indice.items():
        for r in refs:
            o = r["id"].rsplit("-", 1)[0]
            if not (regua / "paginas" / f"{r['id']}.jpg").exists():
                print(f"FALHA  {tipo}: {r['id']} não existe em regua/paginas"); falhas += 1
            if papel.get(o) == "antiexemplo":
                print(f"FALHA  {tipo}: {r['id']} é antiexemplo e está como comparação"); falhas += 1
            if not r.get("porque"):
                print(f"FALHA  {tipo}: {r['id']} sem 'porque' (o princípio que a página ensina)"); falhas += 1
    print(f"{falhas} falha(s)")
    return 1 if falhas else 0


def referencias(regua, tipo, tom=None, n=2, vez=0):
    """Para o contact_sheet: até n páginas do tipo; a principal primeiro, depois a que combina com o tom da direção.
    vez = quantas páginas desse tipo já apareceram no kit; a 2ª ocorrência compara com a 2ª referência de kit-régua, e assim por diante."""
    ip = regua / "indice.json"
    if not ip.exists():
        return []
    cfg = json.loads((regua / "fontes.json").read_text(encoding="utf-8"))
    tom_de = {f["origem"]: f["tom"] for f in cfg["fontes"]}
    refs = json.loads(ip.read_text(encoding="utf-8"))["tipos"].get(tipo, [])
    if not refs:
        return []
    papel = {f["origem"]: f["papel"] for f in cfg["fontes"]}
    principais = [r for r in refs if papel.get(r["id"].rsplit("-", 1)[0]) == "regua"] or refs[:1]
    escolha = [principais[vez % len(principais)]]
    resto = sorted([r for r in refs if r is not escolha[0]], key=lambda r: tom_de.get(r["id"].rsplit("-", 1)[0]) != tom)
    escolha += resto[: n - 1]
    return [(regua / "paginas" / f"{r['id']}.jpg", r["id"]) for r in escolha]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("acao", choices=["montar", "checar", "capturar"])
    ap.add_argument("--regua", default=str(AQUI.parent / "regua"))
    ap.add_argument("--origem", help="capturar: só esta fonte web")
    ap.add_argument("--listar", action="store_true", help="capturar: só lista as candidatas, não grava")
    a = ap.parse_args()
    regua = Path(a.regua).resolve()
    if a.acao == "capturar":
        sys.exit(capturar(regua, a.origem, a.listar))
    sys.exit(montar(regua) if a.acao == "montar" else checar(regua))


if __name__ == "__main__":
    main()

# Copiado da v9 (commit 30da914) em 14/10/2026.
#!/usr/bin/env python3
"""
validar_pdf.py: confere o ARQUIVO entregue, não a prévia (pesquisa r2, etapa 9).

Uso: python3 validar_pdf.py <pdf> [--fontes-esperadas "RocGrotesk,Montserrat"] [--max-mb N] [--paginas 1920x1080]
                                  [--cenas N] [--texturas N] [--texto "Nome do evento"] [--texto "Frase da tese"]
                                  [--por-pagina textos.json]
Sai com 1 em qualquer FALHA. Usa poppler (pdfinfo, pdffonts, pdftotext, pdfimages).

Regras:
  - pdfinfo: Producer Skia/PDF; tamanho de página 1440×810 pt (= 1920×1080 px) ou o pedido; nº de páginas > 0
  - pdffonts: toda fonte emb=yes, sub=yes, uni=yes; nenhuma Type 3 (fonte variável virou Type 3: gere instância estática);
              se --fontes-esperadas, nenhuma família de fallback (DejaVu, Liberation, Noto, Arial) pode aparecer
  - pdftotext: os títulos continuam texto (se sumirem, um filtro rasterizou a região); cada --texto (o qa.py passa o
               nome do evento e a tese) precisa sair como texto em alguma página, ignorando caixa, acento composto,
               pontuação e tracking. Some quando vira imagem: filtro CSS, canvas, grafismo exportado como PNG.
  - --por-pagina (o qa.py gera do render-report): lista com, para cada página, os textos que o DOM mediu nela; cada um
               tem de sair como texto NAQUELA página do PDF (pdftotext -f n -l n). Pega título que virou imagem numa
               página só e página trocada de lugar; o número de páginas do PDF tem de ser o do render.
  - pdfimages -list: nenhuma imagem do tamanho da página além das cenas (--cenas) e das texturas de página inteira
                     declaradas no plano de elementos (--texturas); o resto é raster acidental de filtro/blend;
                     ppi efetivo ≥ 96 em tela
  - --imagens-esperadas (o qa.py passa em kit com camada de acabamento): imagens por página, contadas no HTML que o
                     render gravou (cada <img>, cada <image> de svg e cada url() de imagem da seção da página) ou numa
                     lista JSON; página do PDF com MAIS imagens que isso tem raster que ninguém pediu, o sinal da
                     rasterização silenciosa (filtro, blend fora da lista, sombra CSS, máscara com gradiente): FALHA.
                     Calibrado nos 5 kits do golden de 12/10/2026 (schema/fixtures/imagens-golden-2026-10-12.json):
                     nenhuma página horizontal passa do esperado. PDF com outro número de páginas: AVISO, não confere
  - tamanho: só informado. Sem teto por ordem do Ugo (12/10/2026); `--max-mb N` liga um teto só se alguém pedir
"""
import argparse, json, re, subprocess, sys, unicodedata
from pathlib import Path

FALLBACK = ("DejaVu", "Liberation", "Noto", "Arial", "Helvetica", "FreeSans")


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def _palavras(s):
    """Texto comparável: NFKC (ligadura fi vira fi), sem caixa, pontuação vira espaço."""
    return " ".join(re.sub(r"[^\w]+", " ", unicodedata.normalize("NFKC", s).casefold()).split())


def texto_presente(alvo, documento):
    """O alvo aparece como texto no documento? Tolera quebra de linha, hifenização no fim da linha e tracking largo
    (o pdftotext às vezes devolve "S P R I N T" quando o letter-spacing é grande)."""
    a = _palavras(alvo)
    if not a: return True
    juntos = re.sub(r"-\s*\n\s*", "", documento)
    for doc in (_palavras(documento), _palavras(juntos)):
        if f" {a} " in f" {doc} " or a.replace(" ", "") in doc.replace(" ", ""):
            return True
    return False


def comparavel(texto, cortado=50):
    """Texto do DOM que o render cortou em `cortado` caracteres perde a última palavra (pode estar pela metade)."""
    t = (texto or "").strip()
    if len(t) >= cortado:
        t = t.rsplit(" ", 1)[0] if " " in t else ""
    return t if len(_palavras(t).replace(" ", "")) >= 3 else ""


RASTER_NO_HTML = re.compile(r"<img\b|<image\b|url\((?:&quot;|['\"])?(?:data:image|[^)]*?\.(?:png|jpe?g|webp))", re.I)


def imagens_do_html(html):
    """Imagens que cada página PEDE: no HTML do render, por <section>, cada <img>, cada <image> de svg e cada url() de
    imagem (data URI ou arquivo) no markup da seção. É o teto do que o PDF daquela página pode ter."""
    secs = [s.split("</section>", 1)[0] for s in re.split(r"(?=<section\b)", html) if s.startswith("<section")]
    return [len(RASTER_NO_HTML.findall(s)) for s in secs]


def imagens_por_pagina(lista_pdfimages):
    """{página: imagens} do `pdfimages -list` (só tipo image: a smask é o alfa da mesma imagem)."""
    out = {}
    for l in lista_pdfimages:
        p = l.split()
        if len(p) > 3 and p[0].isdigit() and p[2] == "image":
            out[int(p[0])] = out.get(int(p[0]), 0) + 1
    return out


def carregar_esperadas(arq):
    """Lista de imagens esperadas por página: de um .html do render (contadas nele) ou de um JSON [n1, n2, ...]."""
    p = Path(arq)
    if p.suffix.lower() in (".html", ".htm"):
        return imagens_do_html(p.read_text(encoding="utf-8"))
    return [int(x) for x in json.loads(p.read_text(encoding="utf-8"))]


def checar_imagens(reais, esperadas, paginas):
    """(falhas, avisos) das imagens por página contra as esperadas."""
    if len(esperadas) != paginas:
        return [], [f"imagens por página não conferidas: o PDF tem {paginas} páginas e o HTML pede {len(esperadas)}"]
    falhas = []
    for n, e in enumerate(esperadas, 1):
        if reais.get(n, 0) > e:
            falhas.append(f"p.{n}: {reais[n]} imagens no PDF e a página pede {e} (fotos, elementos PNG e imagens de svg do "
                          f"HTML): {reais[n] - e} raster que ninguém pediu (filtro, blend fora da lista, sombra CSS ou máscara "
                          f"com gradiente rasterizou a região)")
    return falhas, []


def checar_por_pagina(pdf, esperados, paginas):
    """[(página, texto)] que não saem como texto na própria página; e o aviso de contagem diferente."""
    falhas = []
    if len(esperados) != paginas:
        falhas.append((0, f"o PDF tem {paginas} páginas e o render mediu {len(esperados)}"))
    for n, textos in enumerate(esperados[:paginas], 1):
        alvos = [c for c in (comparavel(t) for t in textos) if c]
        if not alvos:
            continue
        doc = run(["pdftotext", "-f", str(n), "-l", str(n), str(pdf), "-"]) + "\n" + run(["pdftotext", "-raw", "-f", str(n), "-l", str(n), str(pdf), "-"])
        for alvo in dict.fromkeys(alvos):
            if not texto_presente(alvo, doc):
                falhas.append((n, alvo))
    return falhas


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("pdf"); ap.add_argument("--fontes-esperadas", default=None); ap.add_argument("--max-mb", type=float, default=None, help="sem teto por padrão (ordem do Ugo, 12/10/2026); informe para ligar"); ap.add_argument("--paginas", default="1920x1080"); ap.add_argument("--cenas", type=int, default=None, help="quantas imagens de página inteira são esperadas (cenas); acima disso é raster acidental")
    ap.add_argument("--texturas", type=int, default=0, help="usos de pattern ou textura de página inteira declarados no plano de elementos; somam ao limite das cenas")
    ap.add_argument("--texto", action="append", default=[], help="texto que precisa sair como texto no PDF (repetível): nome do evento, tese")
    ap.add_argument("--por-pagina", default=None, help="JSON: lista, por página, dos textos que o DOM mediu nela (o qa.py gera do render-report)")
    ap.add_argument("--imagens-esperadas", default=None, help="HTML do render (conta as imagens de cada <section>) ou JSON [n por página]: mais imagens que isso numa página é raster acidental")
    a = ap.parse_args(); pdf = Path(a.pdf); falhas, avisos = [], []
    if not pdf.exists(): print("FALHA  arquivo não existe"); sys.exit(1)
    info = run(["pdfinfo", str(pdf)])
    m = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", info); paginas = int(re.search(r"Pages:\s+(\d+)", info).group(1)) if "Pages:" in info else 0
    w, h = [int(x) for x in a.paginas.split("x")]
    if m and (abs(float(m.group(1)) - w * 0.75) > 1 or abs(float(m.group(2)) - h * 0.75) > 1): falhas.append(f"tamanho de página {m.group(1)}×{m.group(2)} pt, esperado {w*0.75:.0f}×{h*0.75:.0f}")
    if paginas == 0: falhas.append("PDF sem páginas")
    mb = pdf.stat().st_size / 1e6
    if a.max_mb is not None and mb > a.max_mb: falhas.append(f"{mb:.1f} MB acima do teto pedido de {a.max_mb} MB")
    # fontes
    fontes = run(["pdffonts", str(pdf)]).splitlines()[2:]
    fams = set()
    for l in fontes:
        parts = l.split(); 
        if len(parts) < 6: continue
        nome = parts[0].split("+")[-1]; tipo = " ".join(parts[1:-5]) if len(parts) > 6 else parts[1]
        emb, sub, uni = parts[-5], parts[-4], parts[-3]
        fams.add(nome.split("-")[0])
        if "Type 3" in l: falhas.append(f"fonte {nome} embutida como Type 3 (fonte variável): gere instância estática com fontTools instancer")
        if emb != "yes": falhas.append(f"fonte {nome} não embutida")
        if uni != "yes": avisos.append(f"fonte {nome} sem ToUnicode: texto não pesquisável")
    if a.fontes_esperadas:
        esperadas = [f.strip() for f in a.fontes_esperadas.split(",")]
        ruins = sorted(f for f in fams if any(f.startswith(fb) for fb in FALLBACK) and not any(f.startswith(e.split("-")[0]) for e in esperadas))
        if ruins: falhas.append(f"fontes de fallback no PDF: {', '.join(ruins)} (esperadas: {', '.join(esperadas)})")
    # texto
    txt = run(["pdftotext", "-l", "3", str(pdf), "-"])
    if len(txt.strip()) < 40: falhas.append("quase nenhum texto extraível nas 3 primeiras páginas: títulos rasterizados?")
    if a.texto:
        # -raw segue a ordem do conteúdo: texto em arco (selo do grafismos.py) sai inteiro; o modo padrão o embaralha
        documento = run(["pdftotext", str(pdf), "-"]) + "\n" + run(["pdftotext", "-raw", str(pdf), "-"])
        for alvo in a.texto:
            if not texto_presente(alvo, documento):
                falhas.append(f"{alvo!r} não sai como texto em nenhuma página: virou imagem (filtro CSS, canvas, grafismo em PNG) ou sumiu do kit")
    if a.por_pagina:
        import json
        esperados = json.loads(Path(a.por_pagina).read_text(encoding="utf-8"))
        for n, alvo in checar_por_pagina(pdf, esperados, paginas):
            falhas.append(alvo if n == 0 else f"p.{n}: {alvo!r} não sai como texto nesta página do PDF: virou imagem (filtro, canvas, grafismo em PNG) ou a página mudou de lugar")
    # imagens
    lista = run(["pdfimages", "-list", str(pdf)]).splitlines()[2:]
    pagina_inteira = 0; baixa = 0
    for l in lista:
        p = l.split()
        if len(p) < 13 or p[2] not in ("image",): continue
        iw, ih, ppi = int(p[3]), int(p[4]), int(p[12]) if p[12].isdigit() else 0
        if iw >= w * 0.98 and ih >= h * 0.98: pagina_inteira += 1
        if ppi and ppi < 96: baixa += 1
    if a.cenas is not None and pagina_inteira > a.cenas + a.texturas:
        falhas.append(f"{pagina_inteira} imagens de página inteira, esperadas {a.cenas + a.texturas} ({a.cenas} cenas + {a.texturas} texturas declaradas): raster acidental (filtro, sombra ou blend fora da lista nativa)")
    if baixa: avisos.append(f"{baixa} imagem(ns) abaixo de 96 ppi")
    if a.imagens_esperadas:
        fi, ai = checar_imagens(imagens_por_pagina(lista), carregar_esperadas(a.imagens_esperadas), paginas)
        falhas += fi; avisos += ai
    for x in avisos: print("AVISO ", x)
    for x in falhas: print("FALHA ", x)
    print(f"\n{pdf.name}: {paginas} páginas, {mb:.1f} MB, fontes: {', '.join(sorted(fams)) or 'nenhuma'}, imagens de página inteira: {pagina_inteira}")
    print(f"{len(falhas)} falha(s), {len(avisos)} aviso(s)"); sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()

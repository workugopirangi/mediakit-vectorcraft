# Copiado da v9 (commit 1d62c10) em 14/10/2026 e reescrito sobre PDFs.
"""
contact_sheet.py: folhas de comparação entre dois PDFs de mídia kit (prova para o dono cético).

Na v9 este arquivo trabalhava sobre a pasta do kit (mediakit.json, render-report, PNGs do render). Na v10 o que existe é o
PDF entregue, então só ficaram os dois modos que funcionam com PDFs. Saíram os que só existem para o HTML da v9: a folha de
contato com a régua (lia render-report.json), --composicao, --acabamento e --estudo (liam o plano de elementos, o
mediakit.json e o repertório). A régua da v9 (regua.py) não entrou na v10.

Uso:
  scripts/py -m mediakit.ferramentas.contact_sheet --antes <depois.pdf> <antes.pdf> [--saida folha.png]
  scripts/py -m mediakit.ferramentas.contact_sheet --cega <pdf-1> <pdf-2> --saida <pasta> [--semente N] [--chave arquivo.json]

--antes grava a folha antes e depois: uma linha por página, o antes à esquerda e o depois à direita (páginas pareadas pela
posição; número de páginas diferente avisa e não quebra).

--cega sorteia qual dos dois PDFs vira A e qual vira B e grava na pasta de saída:
  kit-A.pdf, kit-B.pdf   cópias novas, sem título, autor, produtor nem datas (nada do original é herdado)
  folha-cega.png         cada página com A à esquerda e B à direita, rotulados só A e B
  chave-sorteio.json     a chave: qual original virou A e qual virou B, a semente e o sha256 dos arquivos
A chave é o único arquivo que revela a origem. Com --chave ela vai para outro lugar (fora da pasta que o juiz abre);
sem --chave fica na pasta de saída e deve ser tirada dela antes de mostrar a pasta a qualquer juiz. Os PDFs originais
nunca são alterados. Sem --semente, o sorteio usa uma semente aleatória que fica gravada na chave.
"""
import argparse
import hashlib
import json
import random
import secrets
import sys
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont



def fonte_ui(tam):
    """Fonte da folha (veio do regua.py da v9, que não entrou na v10)."""
    for c in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(c, tam)
        except Exception:
            pass
    return ImageFont.load_default()

FUNDO_FOLHA, FUNDO_CELULA = (18, 18, 20), (32, 32, 36)
CEL_AD, CEL_CEGA = 640, 860
CAMPOS_METADADOS = ("format", "title", "author", "subject", "keywords", "creator", "producer",
                    "creationDate", "modDate", "trapped", "encryption")


def _sha256(caminho):
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def n_paginas(pdf):
    with fitz.open(pdf) as doc:
        return doc.page_count


def rasterizar(pdf, n, largura):
    """Página n (1-based) do PDF como imagem RGB com a largura dada; None se a página não existe."""
    with fitz.open(pdf) as doc:
        if not 1 <= n <= doc.page_count:
            return None
        pg = doc[n - 1]
        k = largura / pg.rect.width
        pix = pg.get_pixmap(matrix=fitz.Matrix(k, k), colorspace=fitz.csRGB, alpha=False)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def _encaixar(im, w, h):
    """A imagem inteira centrada numa célula w x h, sem distorcer (amplia quando é menor: o detalhe aparece)."""
    im = im.convert("RGB")
    k = min(w / im.width, h / im.height)
    nova = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    cel = Image.new("RGB", (w, h), FUNDO_CELULA)
    cel.paste(nova, ((w - nova.width) // 2, (h - nova.height) // 2))
    return cel


def _altura_celula(pdf, largura):
    """Altura da célula pela proporção da primeira página (16:9 no kit)."""
    with fitz.open(pdf) as doc:
        r = doc[0].rect
    return round(r.height * largura / r.width)


def _celula_vazia(dr, x, y, w, h, texto, fonte):
    dr.rectangle([x, y, x + w, y + h], fill=FUNDO_CELULA, outline=(90, 90, 90))
    dr.text((x + 16, y + 16), texto, fill=(170, 170, 170), font=fonte)


def _colar(S, dr, pdf, n, x, y, w, h, vazio, fonte):
    im = rasterizar(pdf, n, w)
    if im is not None:
        S.paste(_encaixar(im, w, h), (x, y))
    else:
        _celula_vazia(dr, x, y, w, h, vazio, fonte)


# ------------------------------------------------------------------------------------------------- antes e depois
def folha_antes_depois(pdf_depois, pdf_antes, saida_arq=None):
    """Por página (pareadas pela posição): a do PDF anterior à esquerda e a do novo à direita, com a legenda embaixo.
    Grava a folha (padrão: antes-depois-<nome do depois>.png ao lado do PDF novo) e devolve {arquivo, pares, avisos};
    cada par traz {depois, antes, caixas: {antes, depois}} em px da folha. Nada é escrito junto do PDF anterior."""
    pdf_depois, pdf_antes = Path(pdf_depois).resolve(), Path(pdf_antes).resolve()
    if pdf_depois == pdf_antes:
        raise SystemExit("o antes e o depois são o mesmo arquivo")
    nd, na = n_paginas(pdf_depois), n_paginas(pdf_antes)
    avisos = []
    if na != nd:
        avisos.append(f"o antes tem {na} páginas e o depois {nd}: pareadas pela posição; a que sobra sai sem par")
    for a in avisos:
        print("AVISO ", a)
    th = _altura_celula(pdf_depois, CEL_AD)
    marg, gap, leg_h, cap_h = 24, 12, 64, 40
    n = max(na, nd)
    S = Image.new("RGB", (marg + 2 * CEL_AD + gap + marg, leg_h + n * (th + cap_h + marg) + marg), FUNDO_FOLHA)
    dr = ImageDraw.Draw(S)
    f14, f16 = fonte_ui(14), fonte_ui(16)
    dr.text((marg, 14), f"antes e depois: {pdf_antes.name} e {pdf_depois.name}", fill=(240, 240, 240), font=f16)
    dr.text((marg, 40), "coluna 1: antes · coluna 2: depois", fill=(150, 150, 150), font=f14)
    resumo = []
    for i in range(1, n + 1):
        y0 = leg_h + marg + (i - 1) * (th + cap_h + marg)
        xa, xd = marg, marg + CEL_AD + gap
        _colar(S, dr, pdf_antes, i, xa, y0, CEL_AD, th, "sem página no antes", f16)
        _colar(S, dr, pdf_depois, i, xd, y0, CEL_AD, th, "sem página no depois", f16)
        dr.text((marg, y0 + th + 8), f"p.{i:02d}   antes {'sim' if i <= na else 'sem página'}   ·   "
                f"depois {'sim' if i <= nd else 'sem página'}", fill=(240, 240, 240), font=f16)
        resumo.append({"depois": i if i <= nd else None, "antes": i if i <= na else None,
                       "caixas": {"antes": [xa, y0, xa + CEL_AD, y0 + th], "depois": [xd, y0, xd + CEL_AD, y0 + th]}})
    out = Path(saida_arq) if saida_arq else pdf_depois.with_name(f"antes-depois-{pdf_depois.stem}.png")
    S.save(out, optimize=True)
    print("OK", out, f"{n} linha(s), {min(na, nd)} par(es)")
    return {"arquivo": str(out), "pares": resumo, "avisos": avisos}


# ------------------------------------------------------------------------------------------------- escolha cega
def limpar_pdf(origem, destino):
    """Grava em `destino` uma cópia nova do PDF, sem herdar nada do cabeçalho do original: documento novo (as páginas
    entram por insert_pdf), todos os campos de metadados vazios e sem o XMP. O título, o autor e o produtor do original
    não chegam ao arquivo; é o que impede o PDF de denunciar de qual versão ele veio."""
    with fitz.open(origem) as src, fitz.open() as novo:
        novo.insert_pdf(src)
        novo.set_metadata({c: "" for c in CAMPOS_METADADOS if c not in ("format", "encryption")})
        novo.del_xml_metadata()
        novo.save(destino, garbage=4, deflate=True, clean=True)


def _selo(dr, x, y, letra, f20):
    dr.rectangle([x, y, x + 40, y + 36], fill=(245, 245, 245))
    dr.text((x + 12, y + 6), letra, fill=(18, 18, 20), font=f20)


def escolha_cega(pdf_1, pdf_2, pasta_saida, semente=None, chave_arq=None):
    """Sorteia qual dos dois PDFs vira A e qual vira B. Grava em `pasta_saida` kit-A.pdf e kit-B.pdf (sem metadados do
    original), folha-cega.png (A à esquerda, B à direita, páginas pareadas pela posição) e a chave
    (chave-sorteio.json na pasta, ou em `chave_arq`): semente, qual original virou A e qual virou B, e o sha256 dos
    originais e dos arquivos gravados. Mesma semente, mesmo sorteio. Devolve {A, B, kit_A, kit_B, folha, chave,
    sha256_chave, semente, avisos}. Os originais não são tocados."""
    pdf_1, pdf_2 = Path(pdf_1).resolve(), Path(pdf_2).resolve()
    if pdf_1 == pdf_2 or _sha256(pdf_1) == _sha256(pdf_2):
        raise SystemExit("os dois PDFs são o mesmo arquivo: não há o que sortear")
    semente = secrets.randbits(32) if semente is None else int(semente)
    # a ordem dos argumentos não conta: os dois entram ordenados pelo conteúdo, e só a semente decide quem vira A
    primeiro, segundo = sorted((pdf_1, pdf_2), key=_sha256)
    orig_a, orig_b = (primeiro, segundo) if random.Random(semente).random() < 0.5 else (segundo, primeiro)
    pasta = Path(pasta_saida)
    pasta.mkdir(parents=True, exist_ok=True)
    kit_a, kit_b = pasta / "kit-A.pdf", pasta / "kit-B.pdf"
    limpar_pdf(orig_a, kit_a)
    limpar_pdf(orig_b, kit_b)
    na, nb = n_paginas(kit_a), n_paginas(kit_b)
    avisos = []
    if na != nb:
        avisos.append(f"A tem {na} páginas e B {nb}: a folha pareia pela posição; a que sobra sai sem par")
    for a in avisos:
        print("AVISO ", a)
    th = _altura_celula(kit_a, CEL_CEGA)
    marg, gap, rot_h, leg_h = 24, 16, 34, 60
    n = max(na, nb)
    S = Image.new("RGB", (marg + 2 * CEL_CEGA + gap + marg, leg_h + n * (rot_h + th + marg) + marg), FUNDO_FOLHA)
    dr = ImageDraw.Draw(S)
    f16, f20 = fonte_ui(16), fonte_ui(20)
    dr.text((marg, 14), "escolha cega: qual é melhor, A ou B?", fill=(240, 240, 240), font=f20)
    caixas = []
    for i in range(1, n + 1):
        y0 = leg_h + marg + (i - 1) * (rot_h + th + marg)
        dr.text((marg, y0), f"página {i:02d}", fill=(240, 240, 240), font=f20)
        for col, (letra, pdf) in enumerate((("A", kit_a), ("B", kit_b))):
            x = marg + col * (CEL_CEGA + gap)
            _colar(S, dr, pdf, i, x, y0 + rot_h, CEL_CEGA, th, "sem página", f16)
            _selo(dr, x + 10, y0 + rot_h + 10, letra, f20)
        caixas.append({"A": [marg, y0 + rot_h, marg + CEL_CEGA, y0 + rot_h + th],
                       "B": [marg + CEL_CEGA + gap, y0 + rot_h, marg + 2 * CEL_CEGA + gap, y0 + rot_h + th]})
    folha = pasta / "folha-cega.png"
    S.save(folha, optimize=True)
    chave = {"semente": semente,
             "A": {"original": str(orig_a), "sha256_original": _sha256(orig_a), "arquivo": kit_a.name, "sha256_arquivo": _sha256(kit_a)},
             "B": {"original": str(orig_b), "sha256_original": _sha256(orig_b), "arquivo": kit_b.name, "sha256_arquivo": _sha256(kit_b)},
             "folha": folha.name, "sha256_folha": _sha256(folha)}
    arq_chave = Path(chave_arq) if chave_arq else pasta / "chave-sorteio.json"
    arq_chave.parent.mkdir(parents=True, exist_ok=True)
    arq_chave.write_text(json.dumps(chave, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    sha = _sha256(arq_chave)
    print("OK", pasta, f"A e B sorteados (semente {semente}), {min(na, nb)} página(s) pareada(s)")
    print(f"chave {arq_chave} sha256 {sha}: registre este sha256 e tire a chave da pasta antes de mostrá-la a qualquer juiz")
    return {"A": str(orig_a), "B": str(orig_b), "kit_A": str(kit_a), "kit_B": str(kit_b), "folha": str(folha),
            "chave": str(arq_chave), "sha256_chave": sha, "semente": semente, "caixas": caixas, "avisos": avisos}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Folhas de comparação entre dois PDFs de mídia kit.")
    modo = ap.add_mutually_exclusive_group(required=True)
    modo.add_argument("--antes", nargs=2, metavar=("DEPOIS.pdf", "ANTES.pdf"),
                      help="folha antes e depois (grava o PNG em --saida, ou ao lado do PDF novo)")
    modo.add_argument("--cega", nargs=2, metavar=("PDF1", "PDF2"),
                      help="escolha cega: sorteia A e B e grava kit-A.pdf, kit-B.pdf, folha-cega.png e a chave em --saida (uma pasta)")
    ap.add_argument("--saida", default=None, help="--antes: arquivo .png; --cega: pasta de saída (obrigatória)")
    ap.add_argument("--semente", type=int, default=None, help="--cega: semente do sorteio (sem ela, aleatória, gravada na chave)")
    ap.add_argument("--chave", default=None, help="--cega: onde gravar a chave (padrão: chave-sorteio.json na pasta de saída)")
    a = ap.parse_args(argv)
    if a.cega:
        if not a.saida:
            raise SystemExit("--cega pede --saida <pasta>")
        escolha_cega(a.cega[0], a.cega[1], a.saida, a.semente, a.chave)
    else:
        folha_antes_depois(a.antes[0], a.antes[1], a.saida)


if __name__ == "__main__":
    sys.exit(main())

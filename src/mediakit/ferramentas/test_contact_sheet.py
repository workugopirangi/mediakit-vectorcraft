"""Provas das folhas de comparação (contact_sheet.py): --antes e --cega, com PDFs pequenos gerados aqui.

Na v9 os kits eram pastas e a cor do fundo dizia de qual kit a página veio. Aqui é o mesmo método com PDFs: as páginas do
antes têm fundo vermelho, as do depois fundo azul, e a cor amostrada no centro de cada célula (ou do kit-A.pdf
rasterizado) diz de qual original veio, o que prova que a folha mostra o que a chave diz.
"""
import hashlib
import json
from pathlib import Path

import fitz
import pytest
from PIL import Image

from mediakit.ferramentas import contact_sheet

VERMELHO, AZUL = (0.63, 0.12, 0.12), (0.12, 0.12, 0.63)
MARCAS = {"title": "KIT-V9-ORIGEM-TITULO", "author": "AUTORA-V9-SECRETA", "producer": "PRODUTOR-V9-XYZ",
          "creator": "CRIADOR-V9-XYZ", "subject": "ASSUNTO-V9-XYZ", "keywords": "PALAVRA-V9-XYZ"}


def fazer_pdf(caminho, fundo, n_pag, marcas=None):
    doc = fitz.open()
    for i in range(n_pag):
        pg = doc.new_page(width=960, height=540)
        pg.draw_rect(pg.rect, color=fundo, fill=fundo)
        pg.insert_text((40, 80), f"pagina {i + 1}", fontsize=40, color=(1, 1, 1))
    if marcas:
        doc.set_metadata(marcas)
    doc.save(caminho)
    doc.close()
    return Path(caminho)


def cor_pagina(pdf, n=1):
    return contact_sheet.rasterizar(pdf, n, 200).getpixel((100, 56))


def de_quem(rgb):
    r, g, b = rgb
    return "antes" if r > b + 60 else ("depois" if b > r + 60 else "?")


def cor_folha(png, caixa):
    x0, y0, x1, y1 = caixa
    return Image.open(png).convert("RGB").getpixel(((x0 + x1) // 2, (y0 + y1) // 2))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


@pytest.fixture
def kits(tmp_path):
    antes = fazer_pdf(tmp_path / "v9-ANTIGO.pdf", VERMELHO, 4, MARCAS)
    depois = fazer_pdf(tmp_path / "v10-NOVO.pdf", AZUL, 5, {**MARCAS, "title": "KIT-V10-OUTRO-TITULO"})
    return depois, antes


# ------------------------------------------------------------------------------------------------- antes e depois
def test_antes_depois_colunas_e_paginas_diferentes(kits, tmp_path):
    depois, antes = kits
    h0 = (sha(antes), sha(depois))
    r = contact_sheet.folha_antes_depois(depois, antes, tmp_path / "ad.png")
    out = Path(r["arquivo"])
    assert out == tmp_path / "ad.png" and out.is_file()
    assert (sha(antes), sha(depois)) == h0, "a folha alterou um dos PDFs"
    assert r["avisos"] and "4 páginas" in r["avisos"][0], r["avisos"]            # número diferente: avisa, não quebra
    assert [(p["depois"], p["antes"]) for p in r["pares"]] == [(n, n if n <= 4 else None) for n in range(1, 6)]
    p1 = r["pares"][0]
    assert de_quem(cor_folha(out, p1["caixas"]["antes"])) == "antes"
    assert de_quem(cor_folha(out, p1["caixas"]["depois"])) == "depois"
    p5 = r["pares"][4]                                   # sem página no antes: célula vazia, não a cor do antes
    assert de_quem(cor_folha(out, p5["caixas"]["antes"])) == "?"
    assert de_quem(cor_folha(out, p5["caixas"]["depois"])) == "depois"


def test_antes_depois_padrao_grava_ao_lado_do_pdf_novo_e_recusa_o_mesmo_arquivo(kits):
    depois, antes = kits
    r = contact_sheet.folha_antes_depois(depois, antes)
    assert Path(r["arquivo"]) == depois.with_name("antes-depois-v10-NOVO.png") and Path(r["arquivo"]).is_file()
    assert not list(antes.parent.glob("antes-depois-v9*"))
    with pytest.raises(SystemExit, match="mesmo arquivo"):
        contact_sheet.folha_antes_depois(depois, depois)


# ------------------------------------------------------------------------------------------------- escolha cega
def test_cega_grava_kits_folha_e_chave_que_batem(kits, tmp_path):
    depois, antes = kits
    for semente in (1, 2, 3, 4):
        saida = tmp_path / f"cega-{semente}"
        r = contact_sheet.escolha_cega(depois, antes, saida, semente)
        assert sorted(p.name for p in saida.iterdir()) == ["chave-sorteio.json", "folha-cega.png", "kit-A.pdf", "kit-B.pdf"]
        chave = json.loads((saida / "chave-sorteio.json").read_text())
        assert chave["semente"] == semente
        assert {chave["A"]["original"], chave["B"]["original"]} == {str(antes.resolve()), str(depois.resolve())}
        # o kit-A.pdf tem a cor do original que a chave diz, e idem o B
        for letra in "AB":
            quem = "antes" if chave[letra]["original"] == str(antes.resolve()) else "depois"
            assert de_quem(cor_pagina(saida / f"kit-{letra}.pdf")) == quem, (semente, letra)
            assert chave[letra]["sha256_arquivo"] == sha(saida / f"kit-{letra}.pdf")
            assert chave[letra]["sha256_original"] == sha(chave[letra]["original"])
        # a folha mostra A à esquerda e B à direita, com as mesmas cores
        for cx in r["caixas"][:4]:                        # o menor tem 4 páginas; a 5ª só existe num lado
            for letra in "AB":
                quem = "antes" if chave[letra]["original"] == str(antes.resolve()) else "depois"
                assert de_quem(cor_folha(r["folha"], cx[letra])) == quem
        assert r["sha256_chave"] == sha(saida / "chave-sorteio.json")
        assert chave["sha256_folha"] == sha(saida / "folha-cega.png")


def test_cega_sorteia_de_verdade_e_a_mesma_semente_repete(kits, tmp_path):
    depois, antes = kits
    quem_e_a = {}
    for semente in range(1, 21):
        r = contact_sheet.escolha_cega(depois, antes, tmp_path / f"s{semente}", semente)
        quem_e_a[semente] = r["A"]
    assert len(set(quem_e_a.values())) == 2, "em 20 sementes o A foi sempre o mesmo original: não há sorteio"
    for semente in (3, 7):
        r = contact_sheet.escolha_cega(depois, antes, tmp_path / f"repete{semente}", semente)
        assert r["A"] == quem_e_a[semente]
    # a ordem em que os PDFs são passados não muda quem vira A para a mesma semente
    r = contact_sheet.escolha_cega(antes, depois, tmp_path / "inverso", 7)
    assert r["A"] == quem_e_a[7]


def test_cega_sem_semente_sorteia_e_grava_a_semente_na_chave(kits, tmp_path):
    depois, antes = kits
    r = contact_sheet.escolha_cega(depois, antes, tmp_path / "livre")
    chave = json.loads(Path(r["chave"]).read_text())
    assert isinstance(chave["semente"], int)
    r2 = contact_sheet.escolha_cega(depois, antes, tmp_path / "refeito", chave["semente"])
    assert r2["A"] == r["A"], "a semente gravada não reproduz o sorteio"


def test_cega_nada_revela_a_origem(kits, tmp_path):
    depois, antes = kits
    saida = tmp_path / "limpa"
    contact_sheet.escolha_cega(depois, antes, saida, 11)
    segredos = [v.encode() for v in MARCAS.values()] + [b"KIT-V10-OUTRO-TITULO", b"v9-ANTIGO", b"v10-NOVO", b"ANTIGO", b"NOVO"]
    for nome in ("kit-A.pdf", "kit-B.pdf"):
        doc = fitz.open(saida / nome)
        meta = {k: v for k, v in doc.metadata.items() if k not in ("format", "encryption")}
        assert all(not v for v in meta.values()), (nome, meta)
        assert doc.xref_xml_metadata() == 0, f"{nome} ainda tem XMP"
        doc.close()
        bruto = (saida / nome).read_bytes()
        for s in segredos:
            assert s not in bruto, (nome, s)
    for s in segredos:                                    # e os nomes dos arquivos da pasta não citam a origem
        assert not any(s.decode().lower() in p.name.lower() for p in saida.iterdir())
    assert Image.open(saida / "folha-cega.png").info.get("Title") is None and not Image.open(saida / "folha-cega.png").info


def test_cega_chave_pode_ficar_fora_da_pasta_e_originais_nao_mudam(kits, tmp_path):
    depois, antes = kits
    h0 = (sha(antes), sha(depois))
    chave_fora = tmp_path / "cofre" / "chave.json"
    saida = tmp_path / "para-o-juiz"
    r = contact_sheet.escolha_cega(depois, antes, saida, 5, chave_fora)
    assert Path(r["chave"]) == chave_fora and chave_fora.is_file()
    assert not (saida / "chave-sorteio.json").exists()
    assert sorted(p.name for p in saida.iterdir()) == ["folha-cega.png", "kit-A.pdf", "kit-B.pdf"]
    assert (sha(antes), sha(depois)) == h0, "o sorteio alterou um original"


def test_cega_paginas_diferentes_avisa_e_mesmo_pdf_recusa(kits, tmp_path):
    depois, antes = kits
    r = contact_sheet.escolha_cega(depois, antes, tmp_path / "x", 2)
    assert r["avisos"] and "páginas" in r["avisos"][0]
    copia = tmp_path / "copia.pdf"
    copia.write_bytes(depois.read_bytes())
    with pytest.raises(SystemExit, match="mesmo arquivo"):
        contact_sheet.escolha_cega(depois, copia, tmp_path / "y", 2)
    with pytest.raises(SystemExit, match="mesmo arquivo"):
        contact_sheet.escolha_cega(depois, depois, tmp_path / "z", 2)


def test_linha_de_comando_cega_e_antes(kits, tmp_path):
    depois, antes = kits
    saida = tmp_path / "cli"
    contact_sheet.main(["--cega", str(depois), str(antes), "--saida", str(saida), "--semente", "9", "--chave", str(tmp_path / "k.json")])
    assert (saida / "kit-A.pdf").is_file() and (tmp_path / "k.json").is_file()
    contact_sheet.main(["--antes", str(depois), str(antes), "--saida", str(tmp_path / "ad.png")])
    assert (tmp_path / "ad.png").is_file()
    with pytest.raises(SystemExit, match="--saida"):
        contact_sheet.main(["--cega", str(depois), str(antes)])

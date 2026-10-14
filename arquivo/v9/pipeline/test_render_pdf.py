#!/usr/bin/env python3
"""
test_render_pdf.py: a folha do PDF que o render.py entrega. Sem pytest.

  ~/.venvs/mediakit/bin/python pipeline/test_render_pdf.py

O vertical (1080×1920) saía partido: o tema tem `@page { size: 1920px 1080px }` e o Chromium seguia esse @page mesmo com
prefer_css_page_size=False, então cada página vertical virava duas folhas deitadas (6 páginas de 1440×810 pt no lugar de
3 de 810×1440; achado da frente Q em 12/10/2026, os 5 kits do golden repetiam). O conserto pôs o @page de 1080×1920 no
vertical.html e o tamanho da folha passou a vir sempre do @page de cada template.

O vertical da direção principal do kit (a que o mediakit.json declara em `marca.direcao`) também embutia Helvetica no lugar
das fontes do kit (travessia-da-lua: Anton e DM Sans; corre-por-elas: RocGrotesk e Montserrat; acusado pelo validar_pdf no
golden de 12/10/2026). Causa: o vertical.html não repetia o bloco `:root` de tipografia da marca que o kit.html tem
(--fonte-display, --fonte-titulo, --fonte-corpo, --peso-display), então a direção principal caía nas fontes-padrão do tema
(RocGrotesk Wide, Archivo Black...), nenhuma carregada, e o Chromium usava a sans-serif do sistema. Performance e território
não pegavam porque 20-direcoes.css já define as fontes delas.

Com a fonte certa apareceu um segundo desvio do vertical: valor de card em texto ("Saúde + bem-estar") saía em caixa mista e
grande demais, sem a classe `texto` que o horizontal (arquetipos.html) põe. A Helvetica de fallback escondia: o "ú" minúsculo
não existe no RocGrotesk-WideExtraBold e o QA reprovava a página 2 do vertical do corre-por-elas.

Kit mínimo: clone do APFS (cp -c) do exemplo travessia-da-lua com `paginas` = capa, público, cota e contato (4 páginas), direção
causa, sem PNG. A prova roda o pipeline vivo (tem de dar retrato) e o pipeline do commit ANTES do conserto, extraído do
git (tem de dar partido): é o que mostra que a checagem acusa o defeito, e não passa com qualquer coisa.
Sai com 1 se algum teste falhar.
"""
import hashlib, json, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from validar_pdf import FALLBACK       # a mesma lista de fallback que o QA usa
PY = sys.executable
KIT = AQUI.parent / "exemplos" / "travessia-da-lua"
BASE = Path(tempfile.gettempdir()) / f"mk-render-pdf-{hashlib.sha1(str(AQUI).encode()).hexdigest()[:8]}"
COMMIT_ANTES = "8492325"        # main com o vertical partido (merge da frente P, 12/10/2026)
PAGINAS = ["capa", "publico", "cota", "contato"]     # o vertical lê a capa, o público, a cota principal e o contato


def teste(fn):
    fn._teste = True
    return fn


def log(*a):
    print("   ", *a, flush=True)


def kit_minimo(nome, valor_texto=None):
    """`valor_texto`: troca o valor de um dos 3 cards de público (provas com destaque; o p7, a meta) por uma frase."""
    d = BASE / nome
    if d.exists():
        shutil.rmtree(d)
    d.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cp", "-cR", str(KIT), str(d)], check=True)
    shutil.rmtree(d / "saida", ignore_errors=True)
    k = json.loads((d / "mediakit.json").read_text(encoding="utf-8"))
    k["paginas"] = PAGINAS
    if valor_texto:
        card = next(p for p in k["provas"] if p["id"] == "p7")
        assert card.get("destaque"), "o p7 do exemplo deixou de ser card de público"
        card["valor"] = valor_texto
    (d / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False, indent=1), encoding="utf-8")
    return d


def pipeline_antes():
    alvo = BASE / f"pipeline-{COMMIT_ANTES}"
    if (alvo / "render.py").exists():
        return alvo
    alvo.mkdir(parents=True, exist_ok=True)
    tar = subprocess.run(["git", "archive", "--format=tar", COMMIT_ANTES, "--", "."], capture_output=True, check=True,
                         cwd=str(AQUI)).stdout
    subprocess.run(["tar", "-x", "-C", str(alvo)], input=tar, check=True)
    assert (alvo / "render.py").exists(), "pipeline antigo incompleto"
    return alvo


def renderizar(kit, pipeline):
    r = subprocess.run([PY, str(pipeline / "render.py"), str(kit), "--direcao", "causa", "--fontes", str(kit / "fontes")],
                       capture_output=True, text=True, cwd=str(pipeline))
    assert r.returncode == 0, f"render saiu com {r.returncode}: {(r.stdout + r.stderr)[-1200:]}"


def folha(pdf):
    """(páginas, (largura, altura) em pt) pelo pdfinfo."""
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
    n = int(re.search(r"^Pages:\s+(\d+)", out, re.M).group(1))
    m = re.search(r"^Page size:\s+([\d.]+) x ([\d.]+) pts", out, re.M)
    return n, (round(float(m.group(1))), round(float(m.group(2))))


@teste
def vertical_em_retrato_e_horizontal_igual():
    kit = kit_minimo("vivo")
    renderizar(kit, AQUI)
    h = folha(kit / "saida" / "kit-causa.pdf")
    v = folha(kit / "saida" / "kit-causa-vertical.pdf")
    log(f"pipeline vivo: horizontal {h[0]} páginas de {h[1][0]}×{h[1][1]} pt; vertical {v[0]} páginas de {v[1][0]}×{v[1][1]} pt")
    assert h == (len(PAGINAS), (1440, 810)), f"horizontal mudou: {h}"
    assert v == (3, (810, 1440)), f"vertical não é 3 páginas de 810×1440 pt: {v}"


@teste
def antes_do_conserto_o_vertical_saia_partido():
    """A mesma checagem contra o pipeline de antes: tem de acusar (6 folhas deitadas). Sem isto a prova de cima podia
    passar por outro motivo."""
    kit = kit_minimo("antes")
    renderizar(kit, pipeline_antes())
    h = folha(kit / "saida" / "kit-causa.pdf")
    v = folha(kit / "saida" / "kit-causa-vertical.pdf")
    log(f"pipeline {COMMIT_ANTES}: horizontal {h[0]} páginas de {h[1][0]}×{h[1][1]} pt; vertical {v[0]} páginas de "
        f"{v[1][0]}×{v[1][1]} pt (o defeito)")
    assert h == (len(PAGINAS), (1440, 810)), f"horizontal de antes: {h}"
    assert v != (3, (810, 1440)), "o pipeline de antes já dava retrato: a prova não distingue o conserto"
    assert v == (6, (1440, 810)), f"o defeito conhecido era 6 folhas de 1440×810 pt; veio {v}"


def familias(pdf):
    """Famílias embutidas no PDF pelo pdffonts, no mesmo recorte do validar_pdf (nome sem o prefixo do subconjunto e sem o
    estilo: `BAAAAA+Anton-Regular` vira `Anton`)."""
    out = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True, check=True).stdout.splitlines()[2:]
    return {l.split()[0].split("+")[-1].split("-")[0] for l in out if l.split()}


def com_fallback(fams):
    return sorted(f for f in fams if any(f.startswith(fb) for fb in FALLBACK))


def pipeline_mutante(nome, padrao, troca=""):
    """O pipeline vivo com UMA mudança no vertical.html (`padrao` vira `troca`). É o mutante que mostra que a prova acusa a
    falta do trecho, e não passa com qualquer coisa."""
    alvo = BASE / f"pipeline-{nome}"
    if alvo.exists():
        shutil.rmtree(alvo)
    shutil.copytree(AQUI, alvo, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    vert = alvo / "templates" / "vertical.html"
    txt = vert.read_text(encoding="utf-8")
    mut = re.sub(padrao, troca, txt, flags=re.S)
    assert mut != txt, f"o mutante `{nome}` não mudou o vertical.html"
    vert.write_text(mut, encoding="utf-8")
    return alvo


def sem_bloco_de_tipografia():
    mut = pipeline_mutante("sem-fontes-da-marca", r"\n  \{# tipografia da marca.*?\n\}</style>", "}</style>")
    assert "--fonte-display" not in (mut / "templates" / "vertical.html").read_text(encoding="utf-8")
    return mut


def sem_classe_texto():
    return pipeline_mutante("sem-classe-texto", r"\{% if txt %\} texto\{% endif %\}")


def texto_da_pagina(pdf, n):
    return subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), str(pdf), "-"], capture_output=True, text=True, check=True).stdout


@teste
def vertical_da_direcao_principal_embute_as_fontes_do_kit():
    """Kit travessia-da-lua (marca: Anton + DM Sans, direção causa): o PDF vertical não pode ter fonte de fallback e tem
    de ter as duas do kit, como o horizontal."""
    kit = kit_minimo("fontes")
    renderizar(kit, AQUI)
    fh, fv = familias(kit / "saida" / "kit-causa.pdf"), familias(kit / "saida" / "kit-causa-vertical.pdf")
    log(f"horizontal: {sorted(fh)}; vertical: {sorted(fv)}")
    assert not com_fallback(fh), f"o horizontal já embute fallback: {com_fallback(fh)}"
    assert not com_fallback(fv), f"o vertical embute fonte de fallback: {com_fallback(fv)} (esperadas: Anton, DM Sans)"
    assert {"Anton", "DMSans"} <= fv, f"o vertical não embute as fontes do kit (Anton, DMSans): {sorted(fv)}"


@teste
def sem_o_bloco_de_tipografia_o_vertical_embute_helvetica():
    """O mutante (vertical.html sem o bloco da marca) tem de reproduzir o defeito: Helvetica no lugar do Anton."""
    kit = kit_minimo("mutante")
    renderizar(kit, sem_bloco_de_tipografia())
    fh, fv = familias(kit / "saida" / "kit-causa.pdf"), familias(kit / "saida" / "kit-causa-vertical.pdf")
    log(f"mutante: horizontal {sorted(fh)}; vertical {sorted(fv)} (o defeito)")
    assert not com_fallback(fh), f"o horizontal do mutante embute fallback: {com_fallback(fh)}"
    assert com_fallback(fv) == ["Helvetica"], f"o defeito conhecido era Helvetica no vertical; veio {sorted(fv)}"
    assert "Anton" not in fv, "o mutante ainda embute Anton no vertical: a prova não distingue o bloco"


VALOR = "Saúde + bem-estar"


@teste
def vertical_valor_em_texto_sai_em_caixa_alta_como_no_horizontal():
    kit = kit_minimo("texto", VALOR)
    renderizar(kit, AQUI)
    html = lambda f: (kit / "saida" / "html" / f).read_text(encoding="utf-8")
    assert 'class="numero texto"' in html("kit-causa.html"), "o horizontal deixou de marcar o valor em texto"
    assert 'class="numero texto"' in html("kit-causa-vertical.html"), "o vertical não marca o valor em texto (classe `texto`)"
    pagina2 = texto_da_pagina(kit / "saida" / "kit-causa-vertical.pdf", 2)
    log(f"página 2 do vertical: {' '.join(pagina2.split())[:90]!r}")
    assert "SAÚDE" in pagina2 and VALOR.split()[0] not in pagina2, "o valor em texto não saiu em caixa alta no vertical"


@teste
def sem_a_classe_texto_o_vertical_deixa_o_valor_em_caixa_mista():
    kit = kit_minimo("texto-mutante", VALOR)
    renderizar(kit, sem_classe_texto())
    pagina2 = texto_da_pagina(kit / "saida" / "kit-causa-vertical.pdf", 2)
    log(f"mutante, página 2 do vertical: {' '.join(pagina2.split())[:90]!r} (o defeito)")
    assert VALOR.split()[0] in pagina2, "o mutante já sai em caixa alta: a prova não distingue a classe"


def main():
    nomes = [a for a in sys.argv[1:] if not a.startswith("--")]
    testes = [(n, f) for n, f in globals().items() if callable(f) and getattr(f, "_teste", False)]
    if nomes:
        testes = [(n, f) for n, f in testes if n in nomes]
    falhou = 0
    for n, f in testes:
        t0 = time.time()
        try:
            f()
            print(f"OK      {n}  ({time.time() - t0:.1f} s)", flush=True)
        except Exception as e:
            falhou += 1
            print(f"FALHOU  {n}  ({time.time() - t0:.1f} s): {type(e).__name__}: {str(e)[:900]}", flush=True)
    shutil.rmtree(BASE, ignore_errors=True)
    print(f"\n{len(testes) - falhou} de {len(testes)} testes passaram")
    sys.exit(1 if falhou else 0)


if __name__ == "__main__":
    main()

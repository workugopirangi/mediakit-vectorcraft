#!/usr/bin/env python3
"""
test_prova_pdf.py: provas do prova_pdf.py (a lista branca de efeitos CSS da camada de acabamento). Sem pytest.

  ~/.venvs/mediakit/bin/python pipeline/test_prova_pdf.py

Roda o prova_pdf.provar UMA vez (17 casos, cada um em base, bom e mutante no Chromium; perto de 1 minuto) e afirma:
  - cada efeito da lista branca passa nas 5 checagens e o mutante (o mesmo nó com filter) é acusado por alguma;
  - cada proibido é acusado por alguma checagem;
  - nenhuma das 5 checagens é peça morta: cada uma acusa pelo menos um caso da rodada (senão a lista branca estaria
    passando por uma checagem que nunca falha);
  - a lista de efeitos que o camadas.py escreve no HTML (opacidade, blend, clip-path das máscaras e do corte, véu de luz)
    está toda coberta por um caso permitido.
Sai com 1 se algum teste falhar.
"""
import re, shutil, sys, tempfile, time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import prova_pdf  # noqa: E402

_RES = {}
PASTA = Path(tempfile.gettempdir()) / "mk-prova-pdf-teste"
PERMITIDOS = ("opacidade-blend", "clip-polygon", "clip-circle", "clip-inset", "veu-de-luz", "cruza-duas-copias",
              "eco-texto-preenchido", "contorno-path", "mascara-png-alfa")
PROIBIDOS = ("perspective-foto", "perspective-texto", "matrix3d", "text-shadow", "stroke-em-text", "background-clip-text",
             "mask-image-gradiente", "filter")


def teste(fn):
    fn._teste = True
    return fn


def log(*a):
    print("   ", *a, flush=True)


def resultado():
    if not _RES:
        _RES.update(prova_pdf.provar(saida=PASTA, log=lambda *a: None))
    return _RES


@teste
def casos_sao_os_do_contrato():
    cs = prova_pdf.casos()
    assert set(cs) == set(PERMITIDOS) | set(PROIBIDOS), sorted(set(cs) ^ (set(PERMITIDOS) | set(PROIBIDOS)))
    assert all(cs[n].get("proibido") for n in PROIBIDOS) and not any(cs[n].get("proibido") for n in PERMITIDOS)
    log(f"{len(PERMITIDOS)} permitidos e {len(PROIBIDOS)} proibidos")


@teste
def permitidos_passam_e_o_mutante_com_filter_e_acusado():
    r = resultado()
    ruins = []
    for nome in PERMITIDOS:
        bom = [c for c in prova_pdf.CHECAGENS if not r[nome]["bom"][c][0]]
        mut = [c for c in prova_pdf.CHECAGENS if not r[nome]["mutante"][c][0]]
        if bom:
            ruins.append(f"{nome}: o bom falhou em {bom}: " + "; ".join(r[nome]["bom"][c][1] for c in bom))
        elif not mut:
            ruins.append(f"{nome}: o mutante com filter passou nas 5")
        else:
            log(f"{nome:22s} bom 5/5 ({r[nome]['bom']['bytes'][1].split(' sobre')[0]}, {r[nome]['bom']['raster'][1].split(' por')[0]}); "
                f"mutante acusado por {', '.join(mut)}")
    assert not ruins, " | ".join(ruins)


@teste
def proibidos_sao_acusados():
    r = resultado()
    soltos = []
    for nome in PROIBIDOS:
        pegou = [c for c in prova_pdf.CHECAGENS if not r[nome]["bom"][c][0]]
        if not pegou:
            soltos.append(nome)
        else:
            log(f"{nome:22s} acusado por {', '.join(pegou)}: " + "; ".join(r[nome]["bom"][c][1] for c in pegou)[:150])
    assert not soltos, f"proibidos que passaram nas 5 checagens: {soltos}"


@teste
def nenhuma_checagem_e_peca_morta():
    r = resultado()
    disparos = {c: [] for c in prova_pdf.CHECAGENS}
    for nome, rr in r.items():
        if nome.startswith("_"):
            continue
        for versao in ("bom", "mutante"):
            for c in prova_pdf.CHECAGENS:
                if not rr[versao][c][0]:
                    disparos[c].append(f"{nome}/{versao}")
    mortas = [c for c, v in disparos.items() if not v]
    assert not mortas, f"checagem que nunca acusou nada na rodada: {mortas}"
    log("; ".join(f"{c}: {len(v)} caso(s)" for c, v in disparos.items()))


@teste
def o_que_o_render_escreve_esta_coberto():
    """O camadas.py e o 37-acabamento.css só escrevem efeitos que têm caso permitido: opacity e mix-blend-mode no nó,
    clip-path polygon (diagonal, chanfro, arco-base), circle (circulo), inset com raio (janela) e inset (corte do cruza,
    recorte do registro), gradiente oklab de 4 paradas em screen (véu de luz), mask-image com PNG (cor chapada)."""
    import camadas
    css = (AQUI / "tema" / "37-acabamento.css").read_text(encoding="utf-8")
    proibidos_css = ("filter", "perspective", "matrix3d", "text-shadow", "background-clip", "mask-image")
    regras = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    achados = [p for p in proibidos_css if p in regras]
    assert not achados, f"37-acabamento.css usa proibido: {achados}"
    formas = {camadas.clip_mascara(m, 300, 240).split("(")[0] for m in camadas.MASCARAS if m != "nenhuma"}
    assert formas <= {"polygon", "circle", "inset"}, formas
    assert css.count("in oklab") == 3 and "mix-blend-mode: screen" in css
    log(f"máscaras do render: {sorted(formas)}; 37-acabamento.css sem proibido; véu de luz em oklab com screen")


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
    shutil.rmtree(PASTA, ignore_errors=True)
    print(f"\n{len(testes) - falhou} de {len(testes)} testes passaram")
    sys.exit(1 if falhou else 0)


if __name__ == "__main__":
    main()

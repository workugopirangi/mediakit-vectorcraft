#!/usr/bin/env python3
"""
qa_conjunto.py: QA do CONJUNTO de elementos de um kit (Frente C). Lê saida/plano-elementos-<receita>.json (formato
plano_elementos de schema/elementos.schema.json), o mediakit.json e a biblioteca (indice.json), e cobra as regras do dono
(references/08-sistema-elementos.md):

  por receita   cobertura de herói ≥ 70% das páginas elegíveis; 1 herói por página; herói não repete em páginas seguidas;
                no máximo 3 usos do mesmo herói; herói da capa NOVO (kit_origem = kit atual); todo elemento (menos as
                constantes) pertence à família da receita, medido pelo familia.py; nenhum elemento com texto (OCR).
  no kit        ≥ 60% dos elementos distintos (herói, apoio, pattern) novos; ≥ 1 pattern novo; nenhum elemento exclusivo
                de outro cliente (declarado no JSON ou reconhecido na biblioteca pelo sha256 do arquivo).
  composição    (só AVISO, sobre o plano que o render gravou: por item `origem`, `funcao`, `ancora`; por página
                `composicao`; references/09-composicao.md)
                herói ou apoio sem `funcao`, num kit com `composicao`; o mesmo elemento (mesmo id ou mesma imagem) com
                alturas diferentes em páginas diferentes sem que as duas sejam degrau declarado (o caso real da Sprint: 560
                px numa página e 284 em outra); página cuja composição usa relação que a gramática do tipo não usa, sem
                `porque_fora_da_gramatica`. Herói ancorado pela composição conta em cobertura, repetição e novidade como
                os outros; grafismo declarado só na composição (item com `grafismo`, como fio-p8 e fio-p8-s1 da `liga`) não precisa estar
                em elementos[] (sem aviso) e nasce no kit (vale como novo). A regra
                "constante na mesma caixa em toda página" é do qa_geometria.

  acabamento    (mk-2.1, references/10-acabamento.md, seção QA; só em kit que declara a camada ou diz mk-2.1)
                checar_acabamento(): consulta ao repertório gravada e sobre o índice atual; recurso da página na
                direção criativa e no índice; página composta com `acabamento` e porquê; 4 famílias; o fio condutor com
                o mesmo tratamento em todas as páginas, presente nas páginas da tabela, sem repetir o papel em páginas
                seguidas e com a medida do papel; recurso repetido de outro cliente; intensidade calculada (teto, 3);
                ritmo (3 marcantes seguidas, respiro em cada 4, vizinhas iguais, textura igual em páginas seguidas).
                texto livre (AVISO "texto fora do gate de copy"): eco, numeral-eco ou texto-curva com `texto` em vez de `texto_de`.
                No checar(): acabamento fica fora da conta de família e de novidade (o OCR continua) e o item derivado
                (`derivado_de`: sombra e reflexo) fica fora de tudo, porque sai do PNG do pai.

Uso: python qa_conjunto.py <pasta-do-kit> [--biblioteca <pasta>]     (sai 1 com FALHA)
     python qa_conjunto.py <pasta-do-kit> --continuidade                tabela fio × página e a linha de intensidade
O qa.py chama checar() e checar_acabamento() e imprime no mesmo formato (FALHA/AVISO). Kit sem `sistema_elementos` não
passa pelo checar().
Plano marcado "provisorio" (plano_elementos.plano_provisorio, sem posições medidas) vale para as regras de conjunto e
gera um AVISO; as regras de composição não rodam nele (o planejador não conhece função, âncora nem tamanho).
"""
import hashlib, json, re, sys
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
PAPEIS_HEROI = ("heroi", "ornamento")
CONTAM_NOVIDADE = ("heroi", "ornamento", "apoio", "pattern")
META_COBERTURA = 0.7
META_NOVIDADE = 0.6
MAX_USOS = 3
TOL_ALTURA = 0.05      # alturas que diferem menos que isto (e menos que TOL_ALTURA_PX) são arredondamento, não escala
TOL_ALTURA_PX = 6


# ---------------------------------------------------------------- regras da composição (funções puras, sobre o plano gravado)
def tem_composicao(k):
    """Kit com composição por página: alguma chave que não é nota (`_...`) e tem conteúdo."""
    comp = k.get("composicao")
    return isinstance(comp, dict) and any(not str(ch).startswith("_") and isinstance(v, dict) and v for ch, v in comp.items())


def _grafismo_inline(x):
    """Item do plano que é grafismo declarado só na composição da página (ids como fio-p8 e fio-p8-s1, gerados pela `liga`
    ou pelo `grafismo` do elemento da composição): traz o `grafismo` que o gerou, ou veio da composição em svg. Não está em
    elementos[] do mediakit.json e não precisa estar."""
    return bool(x.get("grafismo")) or (x.get("origem") == "composicao" and x.get("formato") == "svg")


def _com_funcao(x):
    return bool((x.get("funcao") or "").strip())


def sem_funcao(plano, rid):
    """AVISO por elemento: herói ou apoio sem `funcao`. Num kit com composição todo herói e apoio tem função (foco,
    contexto, identidade...); o que não tem veio do encaixe automático e ainda não foi composto."""
    achados = {}
    for p in sorted(plano.get("paginas", []), key=lambda p: p["n"]):
        for x in p.get("elementos", []):
            if x.get("papel") in PAPEIS_HEROI + ("apoio",) and not _com_funcao(x):
                achados.setdefault((x["id"], x["papel"]), []).append(p["n"])
    return [f"elementos {rid}: {'herói' if papel in PAPEIS_HEROI else papel} `{eid}` sem `funcao` (p.{', p.'.join(map(str, ns))}): "
            f"num kit com composição todo herói e apoio tem função (foco, contexto, identidade, conexao, organizacao, "
            f"profundidade, equilibrio ou acabamento); ele veio do encaixe automático, componha a página (references/09-composicao.md)"
            for (eid, papel), ns in sorted(achados.items())]


def _grupos_do_elemento(itens):
    """Agrupa [(página, item)] pelo MESMO id ou pela MESMA imagem (sha256): união dos dois critérios."""
    pai = list(range(len(itens)))

    def achar(i):
        while pai[i] != i:
            pai[i] = pai[pai[i]]; i = pai[i]
        return i
    vistos = ({}, {})
    for i, (_, x) in enumerate(itens):
        for chave, tab in zip((x.get("id"), x.get("sha256")), vistos):
            if chave:
                if chave in tab:
                    pai[achar(i)] = achar(tab[chave])
                else:
                    tab[chave] = i
    grupos = {}
    for i in range(len(itens)):
        grupos.setdefault(achar(i), []).append(itens[i])
    return [g for _, g in sorted(grupos.items())]


def alturas_inconsistentes(plano, rid):
    """AVISO por elemento: o mesmo elemento (mesmo id ou mesma imagem) com alturas diferentes em páginas diferentes sem
    que as duas sejam degrau declarado (`ancora.degrau`). Altura = `h` do item (a caixa do PNG de uso é proporcional à
    tinta do elemento, então serve para comparar o elemento com ele mesmo, com ou sem giro); a mensagem mostra largura x
    altura. Só herói e apoio: a constante na mesma caixa é do qa_geometria, e a estrutura (fio, moldura) nasce do alvo."""
    itens = [(p["n"], x) for p in sorted(plano.get("paginas", []), key=lambda p: p["n"]) for x in p.get("elementos", [])
             if x.get("papel") in PAPEIS_HEROI + ("apoio",) and (x.get("h") or 0) > 0]
    degrau = lambda x: bool((x.get("ancora") or {}).get("degrau"))  # noqa: E731
    medida = lambda x: (f"{round(float(x['w']))}x" if x.get("w") else "") + f"{round(float(x['h']))}"  # noqa: E731

    def difere(a, b):
        (na, xa), (nb, xb) = a, b
        ha, hb = float(xa["h"]), float(xb["h"])
        return na != nb and abs(ha - hb) > max(TOL_ALTURA_PX, TOL_ALTURA * max(ha, hb)) and not (degrau(xa) and degrau(xb))
    out = []
    for g in _grupos_do_elemento(itens):
        if any(difere(g[i], g[j]) for i in range(len(g)) for j in range(i + 1, len(g))):
            ids = " / ".join(sorted({x["id"] for _, x in g}))
            lista = ", ".join(f"p.{n} {medida(x)} px{' (degrau)' if degrau(x) else ''}" for n, x in g)
            out.append(f"elementos {rid}: `{ids}` aparece com alturas diferentes ({lista}) sem degrau declarado nas duas: o mesmo elemento "
                       f"com o mesmo tamanho, ou em degrau da escala (fração da página, colunas ou múltiplo de maiúscula) na composição")
    return out


def _relacoes(entrada):
    return {e["ancora"]["relacao"] for e in (entrada or {}).get("elementos") or []
            if isinstance(e, dict) and isinstance(e.get("ancora"), dict) and e["ancora"].get("relacao")}


def fora_da_gramatica(plano, comp, rid):
    """AVISO por página: a composição da página (chave específica: variante ou página) usa relação que a gramática do tipo
    (a entrada da chave do tipo, `plano.paginas[].composicao.gramatica`) não usa, sem `porque_fora_da_gramatica`. A
    página que usa só parte das relações do tipo não foge dele."""
    out = []
    if not isinstance(comp, dict):
        return out
    for p in sorted(plano.get("paginas", []), key=lambda p: p["n"]):
        m = p.get("composicao")
        if not isinstance(m, dict) or not m.get("gramatica"):
            continue                                  # sem composição, ou tipo sem gramática: nada a comparar
        ent, gram = comp.get(m.get("chave")), comp.get(m["gramatica"])
        if not isinstance(ent, dict) or not isinstance(gram, dict):
            continue
        rel_gram = _relacoes(gram)
        fora = sorted(_relacoes(ent) - rel_gram)
        porque = (m.get("porque_fora_da_gramatica") or ent.get("porque_fora_da_gramatica") or "").strip()
        if rel_gram and fora and not porque:
            out.append(f"elementos {rid} p.{p['n']} {p.get('rotulo', '?')}: a composição `{m['chave']}` usa "
                       f"{', '.join(f'`{r}`' for r in fora)}, que a gramática do tipo `{m['gramatica']}` não usa "
                       f"(ela usa {', '.join(f'`{r}`' for r in sorted(rel_gram))}); se a página foge de propósito, "
                       f"escreva `porque_fora_da_gramatica` na composição dela")
    return out


def checar(pasta, k=None, bib=None):
    """Lista de (nível, mensagem), nível FALHA ou AVISO."""
    import biblioteca, plano_elementos as pe
    pasta = Path(pasta)
    k = k if k is not None else json.loads((pasta / "mediakit.json").read_text(encoding="utf-8"))
    sis = k.get("sistema_elementos")
    if not sis:
        return []
    import familia
    res = []
    F = lambda m: res.append(("FALHA", m)); A = lambda m: res.append(("AVISO", m))  # noqa: E731
    kit = biblioteca.kit_do_kit(k, pasta); cliente = biblioteca.cliente_do_kit(k, pasta)
    bib = Path(bib) if bib else biblioteca.PADRAO
    ind = biblioteca.carregar(bib)
    els = {e["id"]: e for e in k.get("elementos", [])}
    origem_motivo = {m["id"]: m.get("origem") for m in sis.get("motivos", [])}
    familias = {f["id"]: f for f in sis.get("familias", [])}
    cache_item, cache_descr = {}, {}

    def item_de(eid):
        if eid not in cache_item:
            e = els.get(eid)
            cache_item[eid] = biblioteca.item_do_elemento(ind, e, pasta) if e else biblioteca.item(ind, eid)
        return cache_item[eid]

    def exclusivo_de(eid):
        e = els.get(eid) or {}
        it = item_de(eid) or {}
        return e.get("exclusivo_cliente") or it.get("exclusivo_cliente")

    inline = set()      # grafismo declarado só na página da composição (_grafismo_inline): fora de elementos[] e nasce neste kit

    def eh_novo(eid):
        e = els.get(eid)
        return (bool(e) and pe.novo(e, kit)) or (e is None and eid in inline)

    # ---------- exclusividade no que o kit declara ----------
    vistos_excl = set()
    for eid in els:
        ex = exclusivo_de(eid)
        if ex and not biblioteca.mesmo_cliente(ex, cliente):
            vistos_excl.add(eid)
            F(f"elementos: `{eid}` é exclusivo de {ex}; este kit é de {cliente} (elemento derivado da identidade de outro cliente)")
        e = els[eid]
        if origem_motivo.get(e.get("motivo")) == "simbolo" and not e.get("exclusivo_cliente"):
            A(f"elementos: `{eid}` tem motivo de origem simbolo e não declara exclusivo_cliente (a biblioteca vai registrá-lo como exclusivo de {cliente})")

    # ---------- por receita, sobre o plano ----------
    usados_kit, patterns_kit, planos = set(), set(), 0
    for rid, rec in (sis.get("receitas") or {}).items():
        caminho = pasta / "saida" / f"plano-elementos-{rid}.json"
        if not caminho.exists():
            A(f"elementos {rid}: {caminho.relative_to(pasta)} não existe (o render grava depois de posicionar); regras por página não conferidas")
            continue
        plano = json.loads(caminho.read_text(encoding="utf-8")); planos += 1
        if plano.get("provisorio"):
            A(f"elementos {rid}: plano provisório (sem posições medidas pelo render)")
        pags = sorted(plano.get("paginas", []), key=lambda p: p["n"])
        inline |= {x["id"] for p in pags for x in p.get("elementos", []) if _grafismo_inline(x)}
        if not plano.get("provisorio"):
            if tem_composicao(k):
                for m in sem_funcao(plano, rid) + fora_da_gramatica(plano, k.get("composicao"), rid):
                    A(m)
            for m in alturas_inconsistentes(plano, rid):
                A(m)
        exc = (sis.get("excecoes") or {}).get(rid) or {}
        eleg, herois = [], {}
        for p in pags:
            hs = [x["id"] for x in p.get("elementos", []) if x.get("papel") in PAPEIS_HEROI and not x.get("derivado_de")]
            if len(hs) > 1:
                F(f"elementos {rid} p.{p['n']}: {len(hs)} heróis ({', '.join(hs)}); a densidade é 1 herói por página")
            if hs:
                herois[p["n"]] = hs[0]
            justificada = any(k_ in pe.chaves(p) and "heroi" in v and v["heroi"] is None for k_, v in exc.items())
            elegivel = p.get("elegivel_heroi", not pe.eh_prova(p))
            if elegivel and not justificada:
                eleg.append(p["n"])
            for x in p.get("elementos", []):
                if x.get("papel") in CONTAM_NOVIDADE and not x.get("derivado_de"):
                    usados_kit.add(x["id"])
                    if x.get("papel") == "pattern":
                        patterns_kit.add(x["id"])
        cobertas = [n for n in eleg if n in herois]
        if eleg and len(cobertas) / len(eleg) < META_COBERTURA:
            F(f"elementos {rid}: cobertura de herói {len(cobertas) / len(eleg):.0%} ({len(cobertas)} de {len(eleg)} páginas elegíveis); "
              f"a regra pede ≥ 70%. Peça os heróis que faltam (plano_elementos.faltantes)")
        for n, h in sorted(herois.items()):
            if herois.get(n + 1) == h:
                F(f"elementos {rid}: herói `{h}` repetido nas páginas seguidas {n} e {n + 1}")
        for h, q in sorted(Counter(herois.values()).items()):
            if q > MAX_USOS:
                F(f"elementos {rid}: herói `{h}` usado {q} vezes; o limite é {MAX_USOS} por receita")
        capa = next((p for p in pags if pe.eh_capa(p)), None)
        if capa is not None:
            h = herois.get(capa["n"])
            if h is None:
                F(f"elementos {rid}: capa sem herói (a regra pede herói novo na capa)")
            elif not eh_novo(h):
                origem = (els.get(h) or item_de(h) or {}).get("kit_origem")
                F(f"elementos {rid}: herói da capa `{h}` não é novo (kit_origem {origem}, kit atual {kit}); a capa pede herói gerado para este kit")
        fam = familias.get(rec.get("familia"))
        if fam is None:
            F(f"elementos {rid}: família `{rec.get('familia')}` não está em sistema_elementos.familias"); continue
        ok_ap, msg_ap = familia.aprovacao_valida(k, pasta, fam["id"])
        if not ok_ap:
            A(f"elementos {rid}: família `{fam['id']}` {msg_ap}")
        conferidos = set()
        for p in pags:
            for x in p.get("elementos", []):
                eid = x["id"]
                if x.get("papel") == "constante" or x.get("derivado_de") or eid in conferidos:
                    continue          # derivado (sombra, reflexo): sai do PNG do pai, que já é conferido
                acab = x.get("papel") == "acabamento"     # acabamento: OCR sim; família e novidade, não (references/10)
                conferidos.add(eid)
                e = els.get(eid)
                ex = exclusivo_de(eid)
                if ex and not biblioteca.mesmo_cliente(ex, cliente) and eid not in vistos_excl:
                    vistos_excl.add(eid)
                    F(f"elementos {rid}: `{eid}` no plano é exclusivo de {ex}; este kit é de {cliente}")
                if e is None and eid in inline:
                    continue          # grafismo da composição: texto vivo na fonte do kit, não tem arquivo nem família a medir
                if e is None:
                    A(f"elementos {rid}: `{eid}` está no plano mas não em elementos[] do mediakit.json")
                    continue
                if e.get("formato") == "svg":
                    continue          # grafismo por código: texto vivo com a fonte do kit; o familia.py mede PNG
                arq = pasta / (e.get("arquivo") or "")
                if not arq.is_file():
                    F(f"elementos {rid}: `{eid}` sem arquivo ({e.get('arquivo')})"); continue
                it = item_de(eid)
                nivel, msg = leitura_de_texto(e, it)
                if nivel:
                    (F if nivel == "falha" else A)(f"elementos {rid}: `{eid}` {msg}")
                if acab:
                    continue
                if eid not in cache_descr:             # medidas da biblioteca só valem para o MESMO arquivo (sha256)
                    mesmo = it and it.get("sha256") == familia.sha256(arq) and (it.get("descritores") or {}).get("versao") == 1
                    cache_descr[eid] = it["descritores"] if mesmo else familia.descritores(arq)
                descr = cache_descr[eid]
                uso = x.get("w") if x.get("papel") in PAPEIS_HEROI + ("apoio",) and x.get("w") else None
                r = familia.pertence(e, fam, base=pasta, descr=descr, escala_uso=uso)
                rev = e.get("familia_revisada") or {}
                if not r["pertence"] and rev.get("sha256") == familia.sha256(arq) and rev.get("por") and rev.get("motivo"):
                    # aceito à mão pelo dono, só para ESTE arquivo (sha256): o aviso fica para sempre
                    A(f"elementos {rid}: `{eid}` fora da medida da família `{fam['id']}` e aceito por {rev['por']} em {rev.get('em', '?')} "
                      f"({rev['motivo']}): " + "; ".join(r["motivos"]))
                elif not r["pertence"]:
                    F(f"elementos {rid}: `{eid}` fora da família `{fam['id']}`: " + "; ".join(r["motivos"])
                      + ("; a revisão registrada é de outro arquivo (sha256 diferente)" if rev else ""))
                for a_ in r["avisos"]:
                    A(f"elementos {rid}: `{eid}` {a_}")

    # ---------- novidade no kit ----------
    if not planos:
        usados_kit = {e["id"] for e in els.values() if e.get("papel") in CONTAM_NOVIDADE}
        patterns_kit = {e["id"] for e in els.values() if e.get("papel") == "pattern"}
        if usados_kit:
            A("elementos: sem plano gravado; novidade medida nos elementos declarados")
    if usados_kit:
        novos = sorted(i for i in usados_kit if eh_novo(i))
        frac = len(novos) / len(usados_kit)
        if frac < META_NOVIDADE:
            F(f"elementos: só {frac:.0%} dos elementos são novos ({len(novos)} de {len(usados_kit)}; reusados: "
              f"{', '.join(sorted(usados_kit - set(novos)))}); a regra pede ≥ 60% gerados para este kit")
        if not any(eh_novo(i) for i in patterns_kit):
            F("elementos: nenhum pattern novo no kit" + (f" (patterns: {', '.join(sorted(patterns_kit))})" if patterns_kit else " (nenhum pattern)")
              + "; a regra pede sempre 1 pattern gerado para este kit")
    return res


def leitura_de_texto(e, it):
    """(nível, mensagem) do OCR de um elemento PNG: ("falha" | "aviso" | None, texto). Peça gerada com texto na imagem é
    invenção da IA: FALHA (texto só por grafismo svg). Foto real do cliente (`gerado: false` ou rota `real`) com texto é a
    marca de verdade na roupa ou na placa, o próprio patrocínio que o kit vende: AVISO, para conferir se ela pode aparecer.
    Teste da AME (09/10): o OCR leu o patrocinador na camisa do árbitro de verdade e a regra chamava de texto da IA."""
    real = e.get("gerado") is False or e.get("rota") == "real"
    if it and it.get("ocr"):
        if real:
            return "aviso", (f"é foto real com texto (OCR {it['ocr'][:40]!r}): é a marca de verdade na roupa ou na placa; "
                             f"confira se ela pode aparecer no kit")
        return "falha", f"tem texto escrito pela IA (OCR {it['ocr'][:40]!r}); texto só por grafismo svg"
    if it and (it.get("ocr_estado") or "").startswith("revisado"):
        return "aviso", f"com leitura de OCR conferida à mão (revisão registrada): {it['ocr_estado'][:160]}"
    if not it or it.get("ocr") is None:
        return "aviso", "com OCR pendente" + ("" if it else " (não registrado na biblioteca: rode biblioteca.py registrar)")
    return None, ""


# ================================================================================================= camada de acabamento
# mk-2.1 (references/10-acabamento.md, seção QA). Só roda em kit que declara a camada (acabamento.usa_acabamento: direção
# criativa, papel acabamento, efeito, formato_base...) ou que diz mk-2.1: kit mk-2.0 sem campo novo não passa por nada
# daqui. O qa.py chama checar_acabamento(pasta, k) e soma ao relatório; `--continuidade` imprime a tabela fio × página.
RAIZ_SKILL = AQUI.parent
INDICE_REPERTORIO = RAIZ_SKILL / "repertorio" / "indice.json"
HISTORICO = RAIZ_SKILL / "memoria-mediakit" / "historico-kits.json"
CONSULTA_PADRAO = "consulta-repertorio.json"
MIN_FAMILIAS = 4
INTENSIDADE_MAX = 3
JANELA_RESPIRO = 4             # em cada 4 páginas seguidas, pelo menos uma de intensidade 0 ou 1
SEGUIDAS_MARCANTES = 3         # 3 páginas seguidas em intensidade 3: falha
TOL_PX = 2.0
GRAFISMOS_COM_TEXTO = ("eco", "numeral-eco", "texto-curva")     # desenham texto vivo: o texto é do gate de copy (`texto_de`)
# o fio condutor é o mesmo desenho em toda página: muda papel, escala, posição e opacidade; o resto (tipo, parâmetros,
# blend, máscara, material) é o tratamento e não muda
GEOMETRIA_FIO = ("largura", "altura", "comprimento", "tamanho", "escala", "raio", "w", "h", "x", "y", "caixa", "pontos")
# avisos do acabamento.validar que viram regra própria aqui (a mesma coisa não sai duas vezes no relatório)
SUPERADOS = ("acima do teto",)                                            # intensidade calculada (aviso; acima de 3, falha)
SUPERADOS_MK21 = ("fora de direcao_criativa.recursos", "família(s) distinta(s)")   # em mk-2.1 viram FALHA aqui


def declara_acabamento(k):
    import acabamento
    return (k or {}).get("schema_version") == "mk-2.1" or acabamento.usa_acabamento(k or {})


def superado(aviso, k):
    """O aviso do acabamento.validar que o QA troca por regra própria (intensidade; em mk-2.1, recurso fora e famílias)."""
    if any(s in aviso for s in SUPERADOS):
        return True
    return (k or {}).get("schema_version") == "mk-2.1" and any(s in aviso for s in SUPERADOS_MK21)


def _dc(k):
    dc = (k or {}).get("direcao_criativa")
    return dc if isinstance(dc, dict) else {}


def _entradas(k):
    comp = (k or {}).get("composicao")
    if not isinstance(comp, dict):
        return
    for chave, ent in comp.items():
        if not str(chave).startswith("_") and isinstance(ent, dict):
            yield chave, ent


def _acab(ent):
    ac = (ent or {}).get("acabamento")
    return ac if isinstance(ac, dict) else {}


def _els(k):
    return {e.get("id"): e for e in (k or {}).get("elementos") or [] if isinstance(e, dict)}


def _motivo(e, els):
    return e.get("motivo") or (els.get(e.get("id")) or {}).get("motivo")


def recursos_da_entrada(ent):
    """Ids de recurso que a página usa: `acabamento.recursos` e o `recurso` de cada elemento, sem repetir."""
    rs = [r for r in _acab(ent).get("recursos") or [] if isinstance(r, str)]
    rs += [e["recurso"] for e in (ent or {}).get("elementos") or [] if isinstance(e, dict) and isinstance(e.get("recurso"), str)]
    return list(dict.fromkeys(rs))


def intensidade(ent, k):
    """(declarada, calculada) da página. Declarada: `acabamento.intensidade` da página, senão o padrão da direção
    (precedência 2 de references/10). Calculada: a maior entre a declarada e o número de recursos distintos da página
    (cada recurso é uma camada a mais: quatro recursos numa página passam de marcante, qualquer que seja o rótulo)."""
    dec = _acab(ent).get("intensidade")
    if not isinstance(dec, int):
        it = _dc(k).get("intensidade")
        dec = it.get("padrao") if isinstance(it, dict) and isinstance(it.get("padrao"), int) else None
    return dec, max(dec or 0, len(recursos_da_entrada(ent)))


def ids_do_indice(indice):
    """Ids que um recurso pode citar como referência: padrões, recursos (índice v2) e referências do repertório."""
    ids = set()
    for chave in ("padroes", "recursos", "referencias"):
        for x in (indice or {}).get(chave) or []:
            if isinstance(x, dict) and x.get("id"):
                ids.add(x["id"])
    return ids


def no_indice(ref, ids):
    """A referência existe no índice? Vale o id inteiro ou, com página (`conebra:12`, `saudade#7`), o id da referência."""
    ref = str(ref or "").strip()
    if not ref:
        return False
    if ref in ids:
        return True
    base = re.split(r"[:#@]", ref, 1)[0]
    return base != ref and base in ids


def checar_consulta(pasta, k, indice_p=None):
    """FALHA: kit mk-2.1 sem a consulta ao repertório gravada (ou ilegível). AVISO: a consulta guarda o sha256 de um
    índice que não é mais o atual (o repertório mudou depois da escolha), ou não guarda sha nenhum."""
    from caminhos import ForaDoKit, dentro_do_kit
    mk21 = k.get("schema_version") == "mk-2.1"
    declarada = _dc(k).get("consulta")
    rel = declarada or CONSULTA_PADRAO
    out = []
    try:
        arq = dentro_do_kit(pasta, rel)
    except ForaDoKit as e:
        return [("FALHA", f"acabamento: direcao_criativa.consulta: {e}")]
    if not arq.is_file():
        if mk21 or declarada:
            out.append(("FALHA" if mk21 else "AVISO",
                        f"acabamento: {'kit mk-2.1 sem' if mk21 else 'direcao_criativa.consulta aponta para'} a consulta ao "
                        f"repertório gravada (`{rel}` não existe na pasta do kit): rode `repertorio.py consultar` antes de "
                        f"escolher os recursos (references/10, Consulta)"))
        return out
    try:
        cons = json.loads(arq.read_text(encoding="utf-8"))
    except Exception as e:
        return [("FALHA" if mk21 else "AVISO", f"acabamento: `{rel}` ilegível ({e})")]
    indice_p = Path(indice_p or INDICE_REPERTORIO)
    if not indice_p.is_file():
        return [("AVISO", f"acabamento: índice do repertório não encontrado ({indice_p.name}): a consulta não foi conferida")]
    atual = hashlib.sha256(indice_p.read_bytes()).hexdigest()
    sha = cons.get("indice_sha256") if isinstance(cons, dict) else None
    if not sha:
        out.append(("AVISO", f"acabamento: `{rel}` não grava `indice_sha256`: não dá para saber se o repertório mudou depois "
                             f"da consulta"))
    elif sha != atual:
        out.append(("AVISO", f"acabamento: a consulta (`{rel}`) foi feita sobre outro índice do repertório (sha256 {sha[:12]}..., "
                             f"o atual é {atual[:12]}...): o repertório mudou depois; refaça a consulta e confira se a "
                             f"escolha dos recursos continua de pé"))
    return out


def checar_recursos(k, indice_p=None):
    """mk-2.1, FALHA: recurso usado numa página que não está em direcao_criativa.recursos, ou cuja referência não está
    no índice do repertório (o recurso tem de vir da consulta, não da cabeça)."""
    if k.get("schema_version") != "mk-2.1":
        return []
    decl = {r.get("id"): r for r in _dc(k).get("recursos") or [] if isinstance(r, dict)}
    usos = {}
    for chave, ent in _entradas(k):
        for rid in recursos_da_entrada(ent):
            usos.setdefault(rid, []).append(chave)
    out, ids = [], None
    try:
        ids = ids_do_indice(json.loads(Path(indice_p or INDICE_REPERTORIO).read_text(encoding="utf-8")))
    except Exception as e:
        out.append(("AVISO", f"acabamento: índice do repertório não lido ({e}): a origem dos recursos não foi conferida"))
    for rid, chaves in usos.items():
        onde = ", ".join(chaves)
        if rid not in decl:
            out.append(("FALHA", f"acabamento: recurso `{rid}` (em {onde}) não está em direcao_criativa.recursos: todo recurso da "
                                 f"página vem da direção criativa, e ela, da consulta ao repertório"))
        elif ids is not None and not no_indice(decl[rid].get("referencia"), ids):
            out.append(("FALHA", f"acabamento: recurso `{rid}` (em {onde}) cita a referência `{decl[rid].get('referencia')}`, que "
                                 f"não está no índice do repertório (repertorio/indice.json): recurso sem origem no "
                                 f"repertório; troque pela referência que a consulta trouxe"))
    return out


def checar_paginas(k):
    """mk-2.1, FALHA: página composta sem `acabamento`, ou com `acabamento` sem `porque`."""
    if k.get("schema_version") != "mk-2.1":
        return []
    out = []
    for chave, ent in _entradas(k):
        if not isinstance(ent.get("acabamento"), dict):
            out.append(("FALHA", f"acabamento: composicao/{chave}: página composta sem `acabamento` (recursos, intensidade e "
                                 f"porquê): num kit mk-2.1 toda página decide o acabamento, mesmo que seja intensidade 0"))
        elif not str(ent["acabamento"].get("porque") or "").strip():
            out.append(("FALHA", f"acabamento: composicao/{chave}: `acabamento` sem `porque`: diga por que esta página leva "
                                 f"este acabamento (ou nenhum)"))
    return out


def checar_familias(k):
    """mk-2.1, FALHA: direcao_criativa.recursos com menos de 4 famílias distintas (no acabamento.validar é aviso)."""
    if k.get("schema_version") != "mk-2.1":
        return []
    fams = sorted({r.get("familia") for r in _dc(k).get("recursos") or [] if isinstance(r, dict) and r.get("familia")})
    if len(fams) >= MIN_FAMILIAS:
        return []
    return [("FALHA", f"acabamento: direcao_criativa.recursos com {len(fams)} família(s) distinta(s) "
                      f"({', '.join(fams) or 'nenhuma'}); o kit mk-2.1 pede pelo menos {MIN_FAMILIAS}")]


def _assinatura_fio(e, els):
    """O tratamento do elemento do fio: o desenho (grafismo com os parâmetros que não são medida, ou o arquivo do
    elemento), o blend, a máscara e o material. Papel, escala, posição e opacidade ficam de fora: mudam com o papel."""
    el = els.get(e.get("id")) or {}
    ef = e.get("efeito") or {}
    g = e.get("grafismo")
    if isinstance(g, dict):
        params = {c: v for c, v in (g.get("params") or {}).items() if c not in GEOMETRIA_FIO}
        desenho = f"grafismo {g.get('tipo')}" + (f" {json.dumps(params, ensure_ascii=False, sort_keys=True)}" if params else "")
    else:
        desenho = f"elemento {el.get('arquivo') or e.get('id')}"
    return (desenho, ef.get("blend") or el.get("blend") or "normal", ef.get("mascara") or "nenhuma", el.get("material"))


def _descr_assinatura(a):
    desenho, blend, masc, mat = a
    extra = [x for x in (f"blend {blend}" if blend != "normal" else "", f"máscara {masc}" if masc != "nenhuma" else "",
                         f"material {mat}" if mat else "") if x]
    return desenho + (f" ({', '.join(extra)})" if extra else "")


def checar_fio(k):
    """AVISO: página da tabela do fio condutor sem elemento com o motivo do fio. mk-2.1, FALHA: o fio muda de
    tratamento entre as páginas (tipo, parâmetros, blend, máscara ou material diferentes)."""
    fio = _dc(k).get("fio_condutor")
    if not isinstance(fio, dict) or not isinstance(fio.get("papeis"), dict):
        return []
    motivo, els, comp = fio.get("motivo"), _els(k), dict(_entradas(k))
    out, por_pagina = [], {}
    for chave, papel in fio["papeis"].items():
        achados = [e for e in (comp.get(chave) or {}).get("elementos") or [] if isinstance(e, dict) and _motivo(e, els) == motivo]
        if not achados:
            out.append(("AVISO", f"acabamento: a página `{chave}` está na tabela do fio condutor (`{motivo}` como {papel}) e "
                                 f"não tem elemento com o motivo `{motivo}`" + ("" if chave in comp else " (nem composição)")))
            continue
        por_pagina[chave] = {_assinatura_fio(e, els) for e in achados}
    todas = set().union(*por_pagina.values()) if por_pagina else set()
    if k.get("schema_version") == "mk-2.1" and len(todas) > 1:
        partes = "; ".join(f"{ch}: {' + '.join(_descr_assinatura(a) for a in sorted(s, key=str))}" for ch, s in por_pagina.items())
        out.append(("FALHA", f"acabamento: o fio condutor `{motivo}` muda de tratamento entre as páginas ({partes}). O fio é o "
                             f"mesmo desenho em todas: mudam o papel, a escala, a posição e a opacidade; tipo, parâmetros, "
                             f"blend, máscara e material ficam"))
    return out


def checar_historico(pasta, k, ledger=None):
    """AVISO: recurso que repete (mesmo id ou mesma referência) um dos 3 últimos kits de OUTRO cliente no histórico,
    sem `porque_repete` no recurso."""
    import biblioteca
    caminho = Path(ledger or HISTORICO)
    try:
        hist = json.loads(caminho.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(hist, dict):
        hist = hist.get("kits", [])
    nome = ((k.get("evento") or {}).get("nome") or "").strip().lower()
    cliente = biblioteca.cliente_do_kit(k, pasta)
    proprio = lambda h: bool(nome) and nome in str(h.get("evento") or h.get("nome") or "").lower()  # noqa: E731
    outros = [h for h in hist if isinstance(h, dict) and not proprio(h) and not biblioteca.mesmo_cliente(h.get("cliente"), cliente)]
    if outros and all(h.get("data") for h in outros):
        outros = sorted(outros, key=lambda h: h["data"])
    out = []
    for r in _dc(k).get("recursos") or []:
        if not isinstance(r, dict) or str(r.get("porque_repete") or "").strip():
            continue
        for h in outros[-3:]:
            ids_h, refs_h = set(), set()
            for x in h.get("recursos") or []:
                if isinstance(x, str):
                    ids_h.add(x)
                elif isinstance(x, dict):
                    ids_h.add(x.get("id")); refs_h.add(x.get("referencia"))
            ids_h.discard(None); refs_h.discard(None)
            ref = r.get("referencia")
            if r.get("id") in ids_h or (ref and ref in refs_h | ids_h):
                out.append(("AVISO", f"acabamento: recurso `{r.get('id')}` repete o kit `{h.get('id') or h.get('kit') or '?'}` "
                                     f"({h.get('cliente') or 'outro cliente'}, um dos 3 últimos de outro cliente) sem "
                                     f"`porque_repete`: diga por que o mesmo recurso serve a este cliente, ou troque"))
    return out


def checar_intensidade(k):
    """Por página da composição: intensidade calculada acima do teto da direção (AVISO) ou acima de 3 (FALHA)."""
    it = _dc(k).get("intensidade")
    teto = it.get("teto") if isinstance(it, dict) and isinstance(it.get("teto"), int) else None
    out = []
    for chave, ent in _entradas(k):
        dec, calc = intensidade(ent, k)
        rs = recursos_da_entrada(ent)
        conta = f"declarada {dec if dec is not None else 'nenhuma'}, {len(rs)} recurso(s){': ' + ', '.join(rs) if rs else ''}"
        if calc > INTENSIDADE_MAX:
            out.append(("FALHA", f"acabamento: composicao/{chave}: intensidade calculada {calc} ({conta}) passa de "
                                 f"{INTENSIDADE_MAX} (marcante): tire recurso da página"))
        elif teto is not None and calc > teto:
            out.append(("AVISO", f"acabamento: composicao/{chave}: intensidade calculada {calc} ({conta}) acima do teto {teto} "
                                 f"da direção criativa"))
    return out


# ------------------------------------------------------------------------------------------------- sobre o plano gravado
def paginas_do_plano(plano, k):
    """[(n, rótulo, chave da composição, entrada, página do plano)] em ordem de página."""
    import composicao
    comp = (k or {}).get("composicao") if isinstance((k or {}).get("composicao"), dict) else {}
    out = []
    for pg in sorted(plano.get("paginas", []), key=lambda p: p["n"]):
        chave = (pg.get("composicao") or {}).get("chave")
        ent = comp.get(chave) if chave else None
        if not isinstance(ent, dict):
            chave, ent, _, _ = composicao.entrada_da_pagina(comp, set(pg.get("rotulos") or []), pg.get("rotulo"),
                                                           pg.get("tipo"), "horizontal") if comp else (None, None, None, None)
        out.append((pg["n"], pg.get("rotulo", "?"), chave, ent if isinstance(ent, dict) else None, pg))
    return out


def _corridas(ns):
    """[[n, n+1, ...]] dos números de página consecutivos."""
    out = []
    for n in ns:
        if out and n == out[-1][-1] + 1:
            out[-1].append(n)
        else:
            out.append([n])
    return out


def checar_ritmo(plano, k, rid):
    """FALHA: 3 páginas seguidas em intensidade 3. AVISO: 4 páginas seguidas sem nenhuma de intensidade 0 ou 1; vizinhas
    com o mesmo conjunto de recursos; a mesma textura na mesma escala e área em páginas seguidas."""
    import qa_geometria
    seq = paginas_do_plano(plano, k)
    ints = [(n, intensidade(ent, k)[1]) for n, _, _, ent, _ in seq]
    out = []
    for c in _corridas([n for n, v in ints if v >= INTENSIDADE_MAX]):
        if len(c) >= SEGUIDAS_MARCANTES:
            out.append(("FALHA", f"acabamento {rid}: {len(c)} páginas seguidas em intensidade {INTENSIDADE_MAX} (p.{c[0]} a "
                                 f"p.{c[-1]}): intercale uma página sutil"))
    if len(ints) >= JANELA_RESPIRO:
        ruins = set()
        for i in range(len(ints) - JANELA_RESPIRO + 1):
            jan = ints[i:i + JANELA_RESPIRO]
            if all(v > 1 for _, v in jan):
                ruins.update(n for n, _ in jan)
        for c in _corridas(sorted(ruins)):
            out.append(("AVISO", f"acabamento {rid}: p.{c[0]} a p.{c[-1]} sem nenhuma página de intensidade 0 ou 1 (em cada "
                                 f"{JANELA_RESPIRO} páginas seguidas, uma respira)"))
    for (na, _, _, ea, pa), (nb, _, _, eb, pb) in zip(seq, seq[1:]):
        ra, rb = set(recursos_da_entrada(ea)), set(recursos_da_entrada(eb))
        if ra and ra == rb:
            out.append(("AVISO", f"acabamento {rid}: p.{na} e p.{nb} usam o mesmo conjunto de recursos ({', '.join(sorted(ra))}): "
                                 f"vizinhas pedem variação"))
        for a in pa.get("elementos", []):
            if a.get("derivado_de") or not (a.get("papel") in ("pattern", "acabamento") and qa_geometria.eh_textura(a, k)):
                continue
            for b in pb.get("elementos", []):
                mesma = (a.get("sha256") and a.get("sha256") == b.get("sha256")) or a.get("id") == b.get("id")
                if (mesma and not b.get("derivado_de") and a.get("escala_tile") == b.get("escala_tile")
                        and all(abs(float(a.get(c) or 0) - float(b.get(c) or 0)) <= TOL_PX for c in ("x", "y", "w", "h"))):
                    out.append(("AVISO", f"acabamento {rid}: a mesma textura `{a['id']}` na mesma escala e área nas páginas "
                                         f"seguidas {na} e {nb}: mude a escala (1/12p, 1/6p, 1/4p), a área ou a densidade"))
                    break
    return out


def _cap(alvos, W, H):
    import composicao
    try:
        return composicao.px_escala({"altura": "1cap"}, alvos or {}, W, H)[1]
    except Exception:
        return None


def medida_do_papel(papel, it, pg, W, H, pasta):
    """Texto do problema quando a medida do item não bate com o papel do fio (None quando bate ou não se mede)."""
    import qa_geometria
    dom = {d["id"]: d for d in pg.get("dom") or []}.get(it["id"])
    (x0, y0, x1, y1), _ = qa_geometria.tinta_final(it, pasta, dom)
    w, h = x1 - x0, y1 - y0
    if papel == "contrapeso":
        sangra = x0 <= TOL_PX or y0 <= TOL_PX or x1 >= W - TOL_PX or y1 >= H - TOL_PX
        if h < H / 3 - TOL_PX or not sangra:
            return (f"mede {h:.0f} px de altura ({h / H:.0%} da página) e {'sangra' if sangra else 'não sangra'}: contrapeso "
                    f"pede pelo menos 1/3 da altura, sangrando")
    elif papel == "selo":
        if max(w, h) > H / 6 + TOL_PX:
            return f"mede {w:.0f}×{h:.0f} px: selo pede até 1/6 da página ({H / 6:.0f} px)"
    elif papel == "separador":
        cap = _cap(pg.get("alvos"), W, H)
        if cap and min(w, h) > cap + TOL_PX:
            return f"tem {min(w, h):.0f} px de espessura: separador pede até 1 altura de maiúscula do título ({cap:.0f} px)"
    elif papel == "eco":
        op = qa_geometria.opacidade(it)
        if op > 0.24 + 1e-9:
            return f"tem opacidade {op:g}: eco pede .24 ou menos"
    elif papel == "textura":
        if w * h < W * H / 4:
            return f"cobre {w * h / (W * H):.0%} da página: textura pede pelo menos 1/4"
    return None


def checar_continuidade(plano, k, rid, pasta):
    """AVISO: o fio faz o mesmo papel em páginas seguidas; a medida do elemento do fio não bate com o papel."""
    fio = _dc(k).get("fio_condutor")
    if not isinstance(fio, dict) or not isinstance(fio.get("papeis"), dict):
        return []
    motivo, papeis, els = fio.get("motivo"), fio["papeis"], _els(k)
    W, H = float(plano.get("largura", 1920)), float(plano.get("altura", 1080))
    out, tabela = [], []
    for n, _, chave, ent, pg in paginas_do_plano(plano, k):
        if chave not in papeis:
            continue
        tabela.append((n, papeis[chave]))
        ids = {e.get("id") for e in (ent or {}).get("elementos") or [] if isinstance(e, dict) and _motivo(e, els) == motivo}
        for it in pg.get("elementos", []):
            if it.get("derivado_de") or not (it.get("id") in ids or it.get("motivo") == motivo):
                continue
            prob = medida_do_papel(papeis[chave], it, pg, W, H, pasta)
            if prob:
                out.append(("AVISO", f"acabamento {rid} p.{n}: o fio `{motivo}` como {papeis[chave]} (`{it['id']}`) {prob}"))
    for (na, pa), (nb, pb) in zip(tabela, tabela[1:]):
        if nb == na + 1 and pa == pb:
            out.append(("AVISO", f"acabamento {rid}: o fio `{motivo}` faz o mesmo papel ({pa}) nas páginas seguidas {na} e {nb}: "
                                 f"alterne o papel (contrapeso, selo, separador, estrutura, eco, textura, moldura)"))
    return out


def checar_motivo_plano(plano, k, rid):
    """AVISO: item de papel acabamento no plano sem motivo (nem dele, nem da composição, nem de elementos[]). O que a
    composição ou elementos[] declaram sem motivo já é FALHA no acabamento.validar."""
    declarados = set(_els(k)) | {e.get("id") for _, ent in _entradas(k) for e in ent.get("elementos") or [] if isinstance(e, dict)}
    out = []
    for pg in plano.get("paginas", []):
        for it in pg.get("elementos", []):
            if it.get("papel") == "acabamento" and not it.get("derivado_de") and not it.get("motivo") and it.get("id") not in declarados:
                out.append(("AVISO", f"acabamento {rid} p.{pg['n']}: `{it['id']}` (acabamento) sem motivo: o acabamento veste "
                                     f"um motivo do cliente (sistema_elementos.motivos), senão é enfeite"))
    return out


def _grafismos_de_texto(k):
    """(onde, tipo, params) de cada eco, numeral-eco ou texto-curva do kit: em `elementos[]` (`tipo` + `params`) e na
    composição (`elementos[].grafismo {tipo, params}`, vertical inclusive)."""
    for i, e in enumerate((k or {}).get("elementos") or []):
        if isinstance(e, dict) and e.get("tipo") in GRAFISMOS_COM_TEXTO and isinstance(e.get("params"), dict):
            yield f"elementos/{i} (`{e.get('id')}`)", e["tipo"], e["params"]
    for chave, ent in _entradas(k):
        for i, e in enumerate(ent.get("elementos") or []):
            g = e.get("grafismo") if isinstance(e, dict) else None
            if isinstance(g, dict) and g.get("tipo") in GRAFISMOS_COM_TEXTO and isinstance(g.get("params"), dict):
                yield f"composicao/{chave}/elementos/{i} (`{e.get('id')}`)", g["tipo"], g["params"]


def checar_texto_livre(k):
    """AVISO "texto fora do gate de copy": eco, numeral-eco ou texto-curva com `params.texto` preenchido e sem `texto_de`.
    O texto desses grafismos vem do gate de copy (`texto_de`: titulo, evento, tese, local ou data); o `texto` livre também
    gera, mas escapa do gate. Quando os dois vêm juntos o gerador usa o `texto` e ignora o `texto_de` (grafismos._texto),
    então continua texto livre e o aviso diz isso. Nunca FALHA: o texto livre é legítimo se saiu do briefing aprovado."""
    out = []
    for onde, tipo, p in _grafismos_de_texto(k):
        texto = p.get("texto")
        if texto is None or not str(texto).strip():
            continue
        if p.get("texto_de"):
            motivo = (f"`{tipo}` traz `texto` ({str(texto)[:40]!r}) e `texto_de`: o gerador usa o `texto` e ignora o "
                      f"`texto_de`; deixe só o `texto_de`")
        else:
            motivo = (f"`{tipo}` usa `texto` livre ({str(texto)[:40]!r}) em vez de `texto_de` (titulo, evento, tese, local "
                      f"ou data); use o `texto_de`, ou confira que o texto veio do gate de copy")
        out.append(("AVISO", f"acabamento: {onde}: texto fora do gate de copy: {motivo}"))
    return out


def planos_horizontais(pasta, direcoes=None):
    import qa_geometria
    return [(f, rot) for f, rot in qa_geometria.planos_da_pasta(pasta, direcoes) if not rot.endswith(" vertical")]


def checar_acabamento(pasta, k=None, indice=None, ledger=None, direcoes=None):
    """Lista de (nível, mensagem) das regras da camada de acabamento. Kit que não declara a camada: lista vazia."""
    pasta = Path(pasta)
    k = k if k is not None else json.loads((pasta / "mediakit.json").read_text(encoding="utf-8"))
    if not declara_acabamento(k):
        return []
    import acabamento
    if not acabamento.gera_vertical(k, acabamento.relatorio_da_pasta(pasta))[0]:
        k = acabamento.sem_vertical(k)    # kit só horizontal: `vertical:*` não é página de ninguém (references/10, seção QA)
    res = (checar_consulta(pasta, k, indice) + checar_recursos(k, indice) + checar_paginas(k) + checar_familias(k)
           + checar_fio(k) + checar_historico(pasta, k, ledger) + checar_intensidade(k) + checar_texto_livre(k))
    planos = planos_horizontais(pasta, direcoes)
    if not planos:
        res.append(("AVISO", "acabamento: sem plano de elementos gravado: ritmo, continuidade do fio e textura entre páginas "
                             "não conferidos (rode o render)"))
    for f, rid in planos:
        try:
            plano = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue                      # plano ilegível já é FALHA no qa_geometria
        res += checar_ritmo(plano, k, rid) + checar_continuidade(plano, k, rid, pasta) + checar_motivo_plano(plano, k, rid)
    return res


def tabela_continuidade(pasta, k=None, direcoes=None):
    """Linhas da tabela fio × página (papel do fio, motivo presente, intensidade calculada, recursos) e a linha de
    intensidade, por receita: o que `--continuidade` imprime."""
    pasta = Path(pasta)
    k = k if k is not None else json.loads((pasta / "mediakit.json").read_text(encoding="utf-8"))
    fio = _dc(k).get("fio_condutor") if isinstance(_dc(k).get("fio_condutor"), dict) else {}
    motivo, papeis, els = fio.get("motivo"), fio.get("papeis") or {}, _els(k)
    linhas = []
    planos = planos_horizontais(pasta, direcoes)
    if not planos:
        return ["sem plano de elementos gravado (rode o render): a tabela segue a ordem das páginas do plano"]
    for f, rid in planos:
        plano = json.loads(f.read_text(encoding="utf-8"))
        linhas.append(f"receita {rid}: fio condutor `{motivo or '(nenhum)'}`")
        linhas.append(f"  {'p.':>3}  {'página':<16} {'papel do fio':<13} {'motivo':<7} {'int.':>4}  recursos")
        ints = []
        for n, rot, chave, ent, _ in paginas_do_plano(plano, k):
            _, calc = intensidade(ent, k)
            ints.append(f"{calc}")
            tem = any(isinstance(e, dict) and _motivo(e, els) == motivo for e in (ent or {}).get("elementos") or []) if motivo else False
            papel = papeis.get(chave, "-") if chave else "-"
            marca = ("sim" if tem else "NÃO") if papel != "-" else ("sim" if tem else "-")
            linhas.append(f"  {n:>3}  {(chave or rot)[:16]:<16} {papel:<13} {marca:<7} {calc:>4}  "
                          f"{', '.join(recursos_da_entrada(ent)) or '-'}")
        linhas.append(f"  intensidade: {' '.join(ints)}")
    return linhas


def main():
    if len(sys.argv) < 2:
        sys.exit("uso: python qa_conjunto.py <pasta-do-kit> [--biblioteca <pasta>] [--continuidade]")
    if "--continuidade" in sys.argv:
        print("\n".join(tabela_continuidade(sys.argv[1])))
        sys.exit(0)
    bib = sys.argv[sys.argv.index("--biblioteca") + 1] if "--biblioteca" in sys.argv else None
    res = checar(sys.argv[1], bib=bib)
    res += checar_acabamento(sys.argv[1])
    for nivel, m in sorted(res, key=lambda r: r[0] != "AVISO"):
        print(f"{nivel}  {m}")
    nf = sum(1 for n, _ in res if n == "FALHA")
    print(f"\n{nf} falha(s), {len(res) - nf} aviso(s)")
    sys.exit(1 if nf else 0)


if __name__ == "__main__":
    main()

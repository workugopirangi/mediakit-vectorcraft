#!/usr/bin/env python3
"""
plano_elementos.py: QUAIS elementos vão em cada página de uma receita, e com que papel (Frente C). Contrato em
references/08-sistema-elementos.md; o ONDE é da Frente A (encaixes.resolver), o desenho dos svg é da Frente B.

  planejar(sistema, elementos, receita_id, paginas, encaixes, biblioteca=None) -> [{"n", "atribuidos": [...]}]
  faltantes(sistema, elementos, receita_id, paginas, encaixes, biblioteca=None, kit=None, composicao=None) -> o que gerar
  plano_provisorio(...) -> dict no formato de saida/plano-elementos-<receita>.json, SEM posições medidas, marcado
                           "provisorio": true. Serve aos testes e ao QA de conjunto enquanto o render não grava o dele.

Determinístico: sem acaso, sem relógio, toda ordem é explícita (mesma entrada, mesma saída, em qualquer PYTHONHASHSEED).

REGRAS (do dono, 09/10/2026):
  herói      1 por página elegível. Elegível = não é prova, tem no catálogo de encaixes (rótulo da página; senão o tipo)
             um encaixe que aceita o papel heroi, e nenhuma exceção da receita zerou o herói ("heroi": null).
             Candidatos: papel heroi (ou ornamento, o nome antigo), da família da receita, de um motivo da receita, sem
             OCR com texto nem veredito reprovado na biblioteca. Nunca o mesmo herói em páginas seguidas (n e n+1);
             no máximo 3 usos do mesmo herói na receita. Na capa, herói NOVO (gerado neste kit) antes de reusado.
             A distribuição é uma busca em feixe sobre as páginas, na ordem do documento (programação dinâmica com
             estado = usos de cada herói + herói da página anterior), que minimiza, nesta ordem: página elegível sem
             herói (a capa pesa mais), herói reusado na capa, aspecto que não casa com o encaixe, mesmo motivo do
             vizinho, herói já muito usado. Com poucos heróis é exata (no teste de aspecto acha o ótimo, 7 de 9; a
             versão gulosa com trocas de 2 em 2 parava em 5). Quando faltam heróis, lacunas seguidas custam mais: as
             páginas sem herói ficam espalhadas, e a capa é a última a ficar sem.
  cobertura  ≥ 70% das elegíveis quando há elementos suficientes; senão `faltantes` diz quantos heróis gerar, de que
             motivo e aspecto.
  pattern    o da receita (receitas[r].pattern), nas páginas cujo catálogo tem encaixe que aceita pattern, ou nas
             páginas do ajuste manual `paginas` do elemento.
  constantes todas as páginas, menos as listadas em `exceto` (casa com rótulo, tipo ou prefixo do rótulo).
  manual     herói com `paginas` (lista de rótulos) fica fixo nessas páginas e não é distribuído em outras.
  exceções   sistema.excecoes[receita][rótulo] por cima de tudo: heroi (id ou null), apoio, encaixe, camada. Herói
             fixado por exceção entra antes da distribuição, para os vizinhos respeitarem a regra de não repetir.
  apoio      só por exceção (a densidade do dono é 1 herói + 2 a 3 constantes).
  composição página com composição explícita (contrato da página: `composicao: true` e, opcional, `herois_composicao`
             = ids que a composição põe de herói; references/08) NÃO recebe herói automático nem apoio de exceção: quem
             decide é a composição (precedência: composição > ajuste manual > exceção > catálogo). O herói que ela pôs
             conta nos "no máximo 3 usos" e no "não repetir em página seguida" (os vizinhos automáticos respeitam) e sai
             no plano como item comum, para a vertical, derivada do plano do horizontal, repetir o herói. Constantes e
             pattern ficam. Sem esses campos o plano é o de sempre.
"""
import math
from collections import Counter

PAPEIS_HEROI = ("heroi", "ornamento")
MAX_USOS = 3
META_COBERTURA = 0.7
META_NOVIDADE = 0.6
CAMADA_PADRAO = {"heroi": "frente", "apoio": "frente", "pattern": "atras"}
CAMADA_CONSTANTE = {"grao": "frente", "microtexto": "frente", "selo": "frente", "fio-borda": "frente",
                    "faixa-diagonal": "atras", "pattern-borda": "atras"}
# render.py ATIVO_VARIANTES ao contrário: (tipo, variante) -> nome da variante de ativo usada no rótulo
ATIVO_ROTULO = {("ativo_painel", "a"): "painel", ("ativo_topo", "a"): "topo", ("ativo_painel", "diagonal"): "diagonal",
                ("ativo_painel", "sangria"): "sangria"}
COM_VARIANTE = ("capa", "manifesto", "publico", "divisor", "cota", "contato")


# ---------------------------------------------------------------- rótulos e encaixes
def rotulo(tipo, variante=None):
    """Rótulo tipo:variante do render (capa:c, cota:b, ativo:diagonal, prova, territorio)."""
    if tipo in ("ativo_painel", "ativo_topo"):
        return "ativo:" + ATIVO_ROTULO.get((tipo, variante or "a"), variante or "painel")
    if tipo in COM_VARIANTE:
        return f"{tipo}:{variante or 'a'}"
    return tipo


def chaves(p):
    """Todos os nomes pelos quais o JSON pode se referir à página: rótulo, tipo, prefixo do rótulo, 'ativo', e os extras
    que o render mandar em `rotulos` (ex.: cota:Naming, ativo:3)."""
    r = p.get("rotulo") or p.get("tipo") or ""
    c = {r, r.split(":")[0]}
    if p.get("tipo"):
        c.add(p["tipo"])
    if any(x.startswith("ativo") for x in c):
        c.add("ativo")
    c.update(p.get("rotulos") or [])
    c.discard("")
    return c


def _especificidade(chave, p):
    """Ordem de aplicação das exceções: genérico primeiro, específico por último (vence)."""
    if chave in (p.get("rotulos") or []):
        return 3
    if chave == p.get("rotulo"):
        return 2
    return 1


def encaixes_da_pagina(p, encaixes):
    encaixes = encaixes or {}
    r = p.get("rotulo") or ""
    for chave in (r, p.get("tipo"), r.split(":")[0]):
        if chave and chave in encaixes:
            return list(encaixes[chave])
    return []


def eh_prova(p):
    return p.get("tipo") == "prova" or (p.get("rotulo") or "").split(":")[0] == "prova"


def eh_capa(p):
    return p.get("tipo") == "capa" or (p.get("rotulo") or "").split(":")[0] == "capa"


def herois_composicao(p):
    """Ids que a composição da página põe de herói (`herois_composicao` no contrato da página), na ordem em que vêm e sem
    repetir. Vazio quando o render não os informou."""
    return tuple(dict.fromkeys(str(i) for i in (p.get("herois_composicao") or []) if i))


def eh_composta(p):
    """Página com composição explícita (`composicao: true`, ou ids em `herois_composicao`): o herói dela é da composição,
    não do plano. O plano só conta os usos e respeita a regra de vizinho."""
    return bool(p.get("composicao")) or bool(herois_composicao(p))


def aspecto_razao(w, h):
    if not w or not h:
        return None
    r = w / h
    if r >= 4 or r <= 0.25:
        return "faixa"
    if r >= 1.6:
        return "largo"
    if r <= 0.625:
        return "alto"
    return "quadrado"


def aspecto_encaixe(enc):
    if enc.get("gerador") == "faixa":
        return "faixa"
    caixa = enc.get("box") or enc.get("max")
    if caixa:
        return aspecto_razao(caixa[-2], caixa[-1])
    return None


def _item_biblioteca(e, biblioteca):
    if not biblioteca:
        return None
    for it in biblioteca.get("itens", []):
        if (e.get("biblioteca_id") and it.get("id") == e["biblioteca_id"]) or (e.get("sha256") and it.get("sha256") == e["sha256"]):
            return it
    return None


def aspecto_elemento(e, biblioteca=None):
    if e.get("aspecto"):
        return e["aspecto"]
    it = _item_biblioteca(e, biblioteca)
    if it:
        if it.get("aspecto"):
            return it["aspecto"]
        if it.get("alfa_bbox"):
            return aspecto_razao(it["alfa_bbox"][2], it["alfa_bbox"][3])
    return None


def penalidade(a_el, a_enc):
    if a_el is None or a_enc is None:
        return 1
    if a_el == a_enc:
        return 0
    if "faixa" in (a_el, a_enc):
        return 3
    if "quadrado" in (a_el, a_enc):
        return 1
    return 3   # largo num encaixe alto (ou o contrário)


def _aceita(enc, papel):
    papeis = enc.get("papeis") or []
    return papel in papeis or (papel == "apoio" and "heroi" in papeis and "apoio" not in papeis)


# ---------------------------------------------------------------- exceções e candidatos
def _excecao(sistema, receita_id, p):
    exc = ((sistema.get("excecoes") or {}).get(receita_id)) or {}
    casam = sorted((k for k in exc if k in chaves(p)), key=lambda k: (_especificidade(k, p), k))
    out = {}
    for k in casam:
        out.update(exc[k])
    return out


def elegivel(p, encaixes, excecao=None, auto=True):
    """Elegível a herói AUTOMÁTICO: não é prova, o catálogo tem encaixe que aceita herói, nenhuma exceção zerou o herói
    e a página não tem composição explícita (o herói dela é da composição). `auto=False` ignora a composição e responde
    só pelo catálogo, que é o que o render grava em `elegivel_heroi`."""
    if eh_prova(p):
        return False
    if excecao and "heroi" in excecao and excecao["heroi"] is None:
        return False
    if auto and eh_composta(p):
        return False
    return any(_aceita(enc, "heroi") for enc in encaixes_da_pagina(p, encaixes))


def kit_atual(elementos):
    """O kit em que o conjunto está sendo montado: o kit_origem mais frequente entre os elementos que não vieram da
    biblioteca (empate: ordem alfabética)."""
    c = Counter(e.get("kit_origem") for e in elementos if e.get("kit_origem") and e.get("rota") != "biblioteca")
    if not c:
        return None
    return sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def novo(e, kit):
    return bool(kit) and e.get("kit_origem") == kit and e.get("rota") != "biblioteca"


def bloqueado(e, biblioteca):
    it = _item_biblioteca(e, biblioteca)
    if not it:
        return False
    return bool(it.get("ocr")) or (it.get("veredito") or {}).get("status") == "reprovado"


def receita_do_sistema(sistema, receita_id):
    """A receita em sistema_elementos.receitas; ausente, {} (sem família, motivo nem pattern: só as constantes entram)."""
    return ((sistema or {}).get("receitas") or {}).get(receita_id) or {}


def candidatos(sistema, elementos, receita_id, biblioteca=None, kit=None):
    rec = receita_do_sistema(sistema, receita_id)
    kit = kit or kit_atual(elementos)
    motivos = set(rec.get("motivos") or [])
    c = [e for e in elementos if e.get("papel") in PAPEIS_HEROI and e.get("familia") == rec.get("familia")
         and e.get("motivo") in motivos and not bloqueado(e, biblioteca)]
    ordem = {e["id"]: i for i, e in enumerate(elementos)}
    return sorted(c, key=lambda e: (not novo(e, kit), ordem[e["id"]]))


# ---------------------------------------------------------------- distribuição do herói
# Custos inteiros (soma exata, sem ruído de ponto flutuante): cobertura primeiro, capa nova, aspecto, variedade.
C_DESCOBERTA = 10000        # página elegível sem herói
C_CAPA_DESCOBERTA = 5000    # a mais, se for a capa
C_DESCOBERTA_SEGUIDA = 20   # duas elegíveis seguidas sem herói (espalha as lacunas quando faltam heróis)
C_CAPA_REUSADA = 500        # herói reusado na capa
C_ASPECTO = 100             # por ponto de penalidade de aspecto (0 a 3)
C_MOTIVO_VIZINHO = 30       # mesmo motivo da página anterior
C_USO = 1                   # por uso anterior do mesmo herói (variedade)
LARGURA_FEIXE = 400


def _distribuir(pags, eleg_ns, cands, fixos, encaixes, kit, biblioteca, compostas=()):
    """Busca em feixe sobre as páginas na ordem do documento. Estado = (usos de cada herói, heróis da página anterior,
    página anterior descoberta); estados iguais ficam só com o menor custo (programação dinâmica), e o feixe guarda os
    LARGURA_FEIXE melhores. Com poucos heróis a busca é exata. Respeita: no máximo 3 usos, nunca o mesmo herói em n e
    n+1 (inclusive vizinho fixado por exceção ou posto pela composição), páginas fixas e não elegíveis.
    `fixos` = {n: (ids...)}: heróis já decididos na página (exceção, ajuste manual, composição); contam os usos e valem
    como vizinho. As páginas em `compostas` entram na conta mas não voltam no resultado (o herói delas é da composição)."""
    ids = [e["id"] for e in cands]
    por_id = {e["id"]: e for e in cands}
    idx = {h: i for i, h in enumerate(ids)}
    pen = {}
    for p in pags:
        if p["n"] in eleg_ns:
            encs = [x for x in encaixes_da_pagina(p, encaixes) if _aceita(x, "heroi")]
            for h in ids:
                a = aspecto_elemento(por_id[h], biblioteca)
                pen[(h, p["n"])] = min((penalidade(a, aspecto_encaixe(x)) for x in encs), default=1)
    chave_ord = lambda s: (s[0], tuple(x or "" for x in s[1]))  # noqa: E731
    # usos já decididos MAIS ADIANTE (exceção, ajuste manual, composição): o limite de 3 vale para o total da receita, não
    # só para o que a busca já viu quando chega na página (sem isso um herói fixado numa página tardia estourava o limite)
    depois, acum = {}, Counter()
    for p in reversed(pags):
        depois[p["n"]] = dict(acum)
        for h in fixos.get(p["n"], ()):
            acum[h] += 1
    feixe = [(0, (), tuple(0 for _ in ids), (), False)]         # custo, atribuições, usos, anteriores, anterior descoberta
    n_ant = None
    for p in pags:
        n = p["n"]
        contiguo = n_ant is not None and n == n_ant + 1
        melhores = {}
        for custo, atrib, usos, ant, ant_desc in feixe:
            ant = ant if contiguo else ()
            ant_desc = ant_desc and contiguo
            if n in fixos:
                hs = tuple(fixos[n]); u = list(usos)
                for h in hs:
                    if h in idx:
                        u[idx[h]] += 1
                opcoes = [(hs[0] if hs else None, 0, tuple(u), False, hs)]
            elif n not in eleg_ns:
                opcoes = [(None, 0, usos, False, ())]
            else:
                c0 = C_DESCOBERTA + (C_CAPA_DESCOBERTA if eh_capa(p) else 0) + (C_DESCOBERTA_SEGUIDA if ant_desc else 0)
                opcoes = [(None, c0, usos, True, ())]
                motivos_ant = {(por_id.get(a) or {}).get("motivo") for a in ant} - {None, ""}
                vizinho = tuple(fixos.get(n + 1, ()))
                for h in ids:
                    i = idx[h]
                    if usos[i] + depois[n].get(h, 0) >= MAX_USOS or h in ant or h in vizinho:
                        continue
                    c = C_ASPECTO * pen[(h, n)] + C_USO * usos[i]
                    if eh_capa(p) and not novo(por_id[h], kit):
                        c += C_CAPA_REUSADA
                    if por_id[h].get("motivo") in motivos_ant:
                        c += C_MOTIVO_VIZINHO
                    u = list(usos); u[i] += 1
                    opcoes.append((h, c, tuple(u), False, (h,)))
            for h, c, u, desc, hs in opcoes:
                est = (custo + c, atrib + (h,), u, hs, desc)
                k = (u, hs, desc)
                if k not in melhores or chave_ord(est) < chave_ord(melhores[k]):
                    melhores[k] = est
        feixe = sorted(melhores.values(), key=chave_ord)[:LARGURA_FEIXE]
        n_ant = n
    melhor = feixe[0][1]
    return {p["n"]: h for p, h in zip(pags, melhor) if h is not None and p["n"] not in compostas}


# ---------------------------------------------------------------- planejar
def _item(e, papel, encs, ajuste, biblioteca):
    aceitos = [x for x in encs if _aceita(x, papel)]
    a = aspecto_elemento(e, biblioteca)
    ordem = sorted(range(len(aceitos)), key=lambda i: (penalidade(a, aspecto_encaixe(aceitos[i])), i))
    pref = [aceitos[i]["id"] for i in ordem]
    for x in reversed(e.get("encaixes_preferidos") or []):          # ajuste manual do elemento
        if x in pref:
            pref.remove(x); pref.insert(0, x)
    if ajuste.get("encaixe"):
        pref = [ajuste["encaixe"]] + [x for x in pref if x != ajuste["encaixe"]]
    primeiro = next((x for x in aceitos if pref and x["id"] == pref[0]), None)
    camadas = (primeiro or {}).get("camadas") or []
    camada = ajuste.get("camada") or (e.get("camada") if e.get("camada") in camadas else None) \
        or (camadas[0] if camadas else None) or e.get("camada") or CAMADA_PADRAO.get(papel, "frente")
    return {"id": e["id"], "papel": papel, "encaixes_preferidos": pref, "camada": camada}


def id_constante(tipo, n):
    """Id da n-ésima constante do tipo em sistema_elementos.constantes: `constante-<tipo>`, e `constante-<tipo>-<n>` a
    partir da segunda do mesmo tipo. É a convenção do render (camadas.constantes_com_id) para achar o grafismo; a conta
    vale sobre a lista inteira, antes do `exceto`, para o id não mudar de página para página."""
    return f"constante-{tipo}" + (f"-{n}" if n > 1 else "")


def _constantes(sistema, elementos, p, encs):
    out, vistos, todas = [], Counter(), []
    for c in sistema.get("constantes") or []:
        if not c.get("tipo"):
            continue
        vistos[c["tipo"]] += 1
        todas.append((c, vistos[c["tipo"]]))
    presentes = [(c, n) for c, n in todas if not set(c.get("exceto") or []) & chaves(p)]
    declarados = {c.get("encaixe") for c, _ in presentes if c.get("encaixe")}
    for c, n in presentes:
        tipo = c.get("tipo")
        el = [e for e in elementos if e.get("papel") == "constante" and e.get("tipo") == tipo]
        cid = el[n - 1]["id"] if len(el) >= n else id_constante(tipo, n)
        if c.get("encaixe"):
            pref = [c["encaixe"]]
        elif tipo == "grao":
            pref = []                                  # o grão cobre a página inteira: não ocupa encaixe
        else:                                          # livres primeiro; o encaixe que outra constante declarou fica por último
            livres = [x["id"] for x in encs if _aceita(x, "constante")]
            pref = [x for x in livres if x not in declarados] + [x for x in livres if x in declarados]
        enc = next((x for x in encs if pref and x["id"] == pref[0]), None)
        camada = ((enc or {}).get("camadas") or [None])[0] or CAMADA_CONSTANTE.get(tipo, "frente")
        item = {"id": cid, "papel": "constante", "tipo": tipo, "encaixes_preferidos": pref, "camada": camada}
        for k in ("texto_de", "texto"):
            if c.get(k) is not None:
                item[k] = c[k]
        out.append(item)
    return out


def _casa_manual(paginas_el, p):
    if paginas_el == "todas":
        return True
    return isinstance(paginas_el, list) and bool(set(paginas_el) & chaves(p))


def planejar(sistema: dict, elementos: list[dict], receita_id: str,
             paginas: list[dict],          # [{"n": 1, "rotulo": "capa:c", "tipo": "capa"}, ...]
             encaixes: dict,               # conteúdo de pipeline/encaixes.json
             biblioteca: dict | None = None) -> list[dict]:
    """Determinístico. Devolve [{"n": 1, "atribuidos": [{"id": "asa-capa", "papel": "heroi",
    "encaixes_preferidos": ["canto-sup-dir"], "camada": "frente"}, ...]}, ...]. Aplica sistema.excecoes por cima.
    Página com composição explícita (`composicao: true` / `herois_composicao`, ver o topo do arquivo) não ganha herói
    automático; o herói que a composição pôs conta nos usos e na regra de vizinho."""
    rec = receita_do_sistema(sistema, receita_id)
    pags = sorted(paginas, key=lambda p: p["n"])
    por_id = {e["id"]: e for e in elementos}
    kit = kit_atual(elementos)
    exc = {p["n"]: _excecao(sistema, receita_id, p) for p in pags}
    compostas = {p["n"]: herois_composicao(p) for p in pags if eh_composta(p)}     # o herói delas é da composição
    eleg_cat = [p for p in pags if elegivel(p, encaixes, exc[p["n"]], auto=False)]
    eleg = [p for p in eleg_cat if p["n"] not in compostas]                        # elegíveis a herói AUTOMÁTICO
    cands = candidatos(sistema, elementos, receita_id, biblioteca, kit)

    fixos, manuais = {}, set()
    for e in cands:                                   # ajuste manual: herói com `paginas` fica onde foi posto
        alvo = [p for p in eleg_cat if isinstance(e.get("paginas"), list) and _casa_manual(e["paginas"], p)]
        if alvo:
            manuais.add(e["id"])                      # (mesmo se a página dele for composta: não é distribuído em outras)
            for p in alvo:
                fixos.setdefault(p["n"], e["id"])
    for p in pags:                                    # exceção vence o ajuste manual (e vale até fora das elegíveis)
        if exc[p["n"]].get("heroi"):
            fixos[p["n"]] = exc[p["n"]]["heroi"]
    decididos = {n: (h,) for n, h in fixos.items()}
    decididos.update(compostas)                       # a composição vence o ajuste manual e a exceção
    livres = [e for e in cands if e["id"] not in manuais]
    heroi = _distribuir(pags, {p["n"] for p in eleg}, livres, decididos, encaixes, kit, biblioteca, set(compostas))

    pattern = por_id.get(rec.get("pattern")) if rec.get("pattern") else None
    out = []
    for p in pags:
        ex = exc[p["n"]]
        encs = encaixes_da_pagina(p, encaixes)
        at = []
        h = heroi.get(p["n"])
        if p["n"] in compostas:
            # item comum, sem `origem`: o horizontal troca pelo da composição; a vertical (derivada do plano do
            # horizontal) repete o herói. Id fora de elementos[] (grafismo da página) não vira item.
            for hid in compostas[p["n"]]:
                if hid in por_id:
                    at.append(_item(por_id[hid], "heroi", encs, {}, biblioteca))
        else:
            if h and not ("heroi" in ex and ex["heroi"] is None):
                at.append(_item(por_id.get(h) or {"id": h}, "heroi", encs, ex, biblioteca))
            if ex.get("apoio"):
                alvo_ajuste = {} if h else ex
                at.append(_item(por_id.get(ex["apoio"]) or {"id": ex["apoio"]}, "apoio", encs, alvo_ajuste, biblioteca))
        if pattern is not None:
            manual = pattern.get("paginas")
            if (manual and _casa_manual(manual, p)) or (not manual and any(_aceita(x, "pattern") for x in encs)):
                at.append(_item(pattern, "pattern", encs, {}, biblioteca))
        at += _constantes(sistema, elementos, p, encs)
        out.append({"n": p["n"], "atribuidos": at})
    return out


# ---------------------------------------------------------------- faltantes
def _herois_do_plano(plano):
    return {pg["n"]: a["id"] for pg in plano for a in pg["atribuidos"] if a["papel"] in PAPEIS_HEROI}


def novidade(ids, elementos, kit):
    """Fração de elementos distintos (herói, apoio, pattern) com kit_origem = kit atual."""
    por_id = {e["id"]: e for e in elementos}
    ids = sorted(set(ids))
    novos = [i for i in ids if i in por_id and novo(por_id[i], kit)]
    return {"novos": len(novos), "total": len(ids), "fracao": round(len(novos) / len(ids), 3) if ids else 0.0,
            "meta": META_NOVIDADE, "reusados": [i for i in ids if i not in novos]}


def _usados(plano):
    return {a["id"] for pg in plano for a in pg["atribuidos"] if a["papel"] in PAPEIS_HEROI + ("apoio", "pattern")}


def herois_da_composicao(composicao: dict | None, elementos: list[dict], paginas: list[dict], pagina_px=(1920, 1080)) -> list[dict]:
    """Os heróis que a composição do kit (mediakit.json -> composicao) declara, por página: [{n, pagina, id, pronto, aspecto, px,
    escala, motivo}]. `pronto` = o elemento existe como imagem (com arquivo) ou como grafismo; o resto é a gerar. `px` e `aspecto`
    vêm da escala declarada e do aspecto declarado do elemento (composicao_prompt.area_declarada), e não do "quadrado" de quem
    não sabe: um herói de 1/3 da altura num aspecto alto pede 240 x 360, não um quadrado. Sem escala ou sem aspecto, `px` é None
    e o pedido diz o que declarar. Grafismo declarado na própria composição (`grafismo`) e papel que não é herói ficam de fora."""
    if not composicao:
        return []
    import composicao as comp_mod, composicao_prompt as cp
    por_id = {e["id"]: e for e in elementos}
    out = []
    for p in sorted(paginas, key=lambda p: p["n"]):
        chave, ent, _, _ = comp_mod.entrada_da_pagina(composicao, chaves(p), p.get("rotulo"), p.get("tipo"))
        for e in (ent or {}).get("elementos") or []:
            if e.get("grafismo") or (e.get("papel") or "heroi") not in PAPEIS_HEROI:
                continue
            el = por_id.get(e.get("id")) or {}
            pronto = bool(el) and el.get("rota") != "a-gerar" and (el.get("formato") == "svg" or bool(el.get("arquivo")))
            decl = el.get("aspecto")
            area = cp.area_declarada(e.get("escala"), decl, pagina_px)
            out.append({"n": p["n"], "pagina": chave or p.get("rotulo") or p.get("tipo"), "id": e.get("id"), "pronto": pronto,
                        "aspecto": cp.aspecto_do_gerador(area[0] / area[1]) if area else decl,
                        "px": [round(area[0]), round(area[1])] if area else None, "escala": e.get("escala"), "motivo": el.get("motivo")})
    return out


def _descrever_escala(escala):
    if not escala:
        return "sem escala"
    dim = "altura" if "altura" in escala else "largura"
    return f"{dim} {escala.get(dim)}" + (f" de {escala['de']}" if escala.get("de") else "")


def faltantes(sistema: dict, elementos: list[dict], receita_id: str, paginas: list[dict], encaixes: dict,
              biblioteca: dict | None = None, kit: str | None = None, composicao: dict | None = None) -> dict:
    """O que gerar (pedido à Frente B) para a receita atingir cobertura de herói ≥ 70% das elegíveis, ≥ 60% de elementos
    novos, herói de capa novo e, no kit, ≥ 1 pattern novo. Simula: acrescenta heróis 'a gerar' e replaneja até cumprir.
    Com `composicao` (mediakit.json -> composicao): a página que a composição já serve de herói conta como coberta (ela troca
    o herói do plano), e o herói que a composição declara e ainda não existe vai em `composicao` com o ASPECTO e os PX reais,
    da escala e do aspecto declarados (um herói de 1/3 da altura num aspecto alto pede 240 x 360, não um quadrado). Sem
    `composicao`, a conta é a de sempre."""
    rec = receita_do_sistema(sistema, receita_id)
    kit = kit or kit_atual(elementos)
    pags = sorted(paginas, key=lambda p: p["n"])
    exc = {p["n"]: _excecao(sistema, receita_id, p) for p in pags}
    eleg = [p for p in pags if elegivel(p, encaixes, exc[p["n"]])]
    eleg_ns = {p["n"] for p in eleg}
    meta = math.ceil(META_COBERTURA * len(eleg))
    motivos = list(rec.get("motivos") or [])
    comp = herois_da_composicao(composicao, elementos, pags)
    comp_todas = {h["n"] for h in comp}
    comp_prontas = {h["n"] for h in comp if h["pronto"]}

    def aspectos_descobertos(plano):
        h = _herois_do_plano(plano); out = []
        for p in eleg:
            if p["n"] in h or p["n"] in comp_todas:
                continue
            encs = [x for x in encaixes_da_pagina(p, encaixes) if _aceita(x, "heroi")]
            out.append(aspecto_encaixe(encs[0]) if encs else None)
        return [a or "quadrado" for a in out]

    extras = []
    def novo_heroi(aspecto, motivo=None):
        cont = Counter(e.get("motivo") for e in candidatos(sistema, elementos + extras, receita_id, biblioteca, kit))
        motivo = motivo or (sorted(motivos, key=lambda m: (cont[m], motivos.index(m)))[0] if motivos else None)
        e = {"id": f"a-gerar-{len(extras) + 1}", "papel": "heroi", "tipo": "objeto", "formato": "png",
             "familia": rec.get("familia"), "motivo": motivo, "aspecto": aspecto, "kit_origem": kit, "rota": "a-gerar"}
        extras.append(e); return e

    plano = planejar(sistema, elementos, receita_id, pags, encaixes, biblioteca)
    cobertas_antes = len((set(_herois_do_plano(plano)) | comp_prontas) & eleg_ns)
    limite = len(eleg) + 3
    while len((set(_herois_do_plano(plano)) | comp_todas) & eleg_ns) < meta and len(extras) < limite:
        falta = aspectos_descobertos(plano)
        comuns = Counter(falta)
        ja = Counter(e["aspecto"] for e in extras)
        aspecto = sorted(comuns, key=lambda a: (-(comuns[a] - 3 * ja[a]), a))[0] if comuns else "quadrado"
        novo_heroi(aspecto)
        plano = planejar(sistema, elementos + extras, receita_id, pags, encaixes, biblioteca)
    # capa: herói novo
    capa = next((p for p in eleg if eh_capa(p)), None)
    h = _herois_do_plano(plano)
    todos = {e["id"]: e for e in elementos + extras}
    if capa is not None and capa["n"] not in comp_todas and (capa["n"] not in h or not novo(todos.get(h[capa["n"]], {}), kit)):
        encs = [x for x in encaixes_da_pagina(capa, encaixes) if _aceita(x, "heroi")]
        simb = [m for m in motivos if any(mm.get("id") == m and mm.get("origem") == "simbolo" for mm in sistema.get("motivos") or [])]
        novo_heroi((aspecto_encaixe(encs[0]) if encs else None) or "quadrado", (simb or motivos or [None])[0])
        plano = planejar(sistema, elementos + extras, receita_id, pags, encaixes, biblioteca)
    # novidade da receita (o kit é a soma das receitas; famílias diferentes não dividem elementos)
    todos = elementos + extras
    nov = novidade(_usados(plano), todos, kit)
    while nov["total"] and nov["fracao"] < META_NOVIDADE and len(extras) < limite + 10:
        novo_heroi(Counter(aspectos_descobertos(plano) or ["quadrado"]).most_common(1)[0][0])
        plano = planejar(sistema, elementos + extras, receita_id, pags, encaixes, biblioteca)
        todos = elementos + extras
        nov = novidade(_usados(plano), todos, kit)
    # pattern novo no kit (qualquer receita)
    padroes = {r.get("pattern") for r in (sistema.get("receitas") or {}).values() if r.get("pattern")}
    por_id = {e["id"]: e for e in elementos}
    tem_pattern_novo = any(i in por_id and novo(por_id[i], kit) for i in padroes)
    pedido_pattern = None
    if not tem_pattern_novo:
        simb = [m for m in motivos if any(mm.get("id") == m and mm.get("origem") in ("simbolo", "territorio") for mm in sistema.get("motivos") or [])]
        pedido_pattern = {"motivo": (simb or motivos or [None])[0], "familia": rec.get("familia"), "quantidade": 1}

    grupos = Counter((e["motivo"], e["aspecto"]) for e in extras)
    herois = [{"motivo": m, "aspecto": a, "quantidade": q} for (m, a), q in sorted(grupos.items(), key=lambda kv: (-kv[1], str(kv[0])))]
    pedidos = [f"{x['quantidade']} herói(s) da família {rec.get('familia')}, motivo {x['motivo']}, aspecto {x['aspecto']}" for x in herois]
    a_gerar = [h for h in comp if not h["pronto"]]
    for h in a_gerar:
        if h["px"]:
            pedidos.append(f"herói `{h['id']}` da página {h['pagina']}: aspecto {h['aspecto']}, {h['px'][0]} x {h['px'][1]} px na página "
                           f"({_descrever_escala(h['escala'])})")
        else:
            pedidos.append(f"herói `{h['id']}` da página {h['pagina']}: declare `aspecto` no elementos[] e `escala` na composição "
                           "(ou gere com elementos.sh --pagina, que mede a caixa da maquete)")
    if pedido_pattern:
        pedidos.append(f"1 pattern novo da família {rec.get('familia')}, motivo {pedido_pattern['motivo']} (o kit não tem pattern novo)")
    original = planejar(sistema, elementos, receita_id, pags, encaixes, biblioteca)
    h = _herois_do_plano(original)
    capa_nova = capa is not None and capa["n"] in h and novo({e["id"]: e for e in elementos}.get(h[capa["n"]], {}), kit)
    return {"receita": receita_id, "familia": rec.get("familia"), "kit": kit,
            "elegiveis": len(eleg), "cobertas": cobertas_antes, "meta_paginas": meta,
            "cobertura": round(cobertas_antes / len(eleg), 3) if eleg else 1.0, "meta_cobertura": META_COBERTURA,
            "heroi_capa_novo": bool(capa_nova) if capa is not None else None,
            "novidade": novidade(_usados(original), elementos, kit),
            "herois": herois, "total_herois": sum(x["quantidade"] for x in herois), "pattern": pedido_pattern,
            "composicao": [{k: h[k] for k in ("n", "pagina", "id", "aspecto", "px", "escala", "motivo")} for h in a_gerar],
            "pedidos": pedidos}


# ---------------------------------------------------------------- plano provisório (formato do arquivo do render)
def plano_provisorio(sistema, elementos, receita_id, paginas, encaixes, biblioteca=None):
    """O plano no formato de saida/plano-elementos-<receita>.json, sem posições medidas (x, y, w, h = 0 ou a caixa fixa
    do catálogo) e sem caixas protegidas. Marcado "provisorio": true; o QA de conjunto avisa quando lê um destes."""
    plano = {pg["n"]: pg for pg in planejar(sistema, elementos, receita_id, paginas, encaixes, biblioteca)}
    out = []
    for p in sorted(paginas, key=lambda p: p["n"]):
        encs = {x["id"]: x for x in encaixes_da_pagina(p, encaixes)}
        els = []
        for a in plano[p["n"]]["atribuidos"]:
            enc = a["encaixes_preferidos"][0] if a["encaixes_preferidos"] else None
            caixa = (encs.get(enc) or {}).get("box") or [0, 0, 0, 0]
            els.append({"id": a["id"], "papel": a["papel"], "encaixe": enc, "camada": a["camada"],
                        "x": caixa[0], "y": caixa[1], "w": caixa[2], "h": caixa[3], "rot": 0, "uso": None, "sha256": None})
        out.append({"n": p["n"], "rotulo": p.get("rotulo") or p.get("tipo"),
                    "elegivel_heroi": elegivel(p, encaixes, _excecao(sistema, receita_id, p), auto=False),   # pelo catálogo, como o render grava
                    "elementos": els, "protegidos": []})
    return {"receita": receita_id, "provisorio": True, "paginas": out}

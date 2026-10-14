#!/usr/bin/env python3
"""
medir_kit.py: a prova para o dono cético (references/10-acabamento.md, "Prova para dono cético"). Mede um kit já
renderizado lendo SÓ os artefatos: mediakit.json, saida/plano-elementos-<receita>.json, saida/render-report.json,
saida/png/kit-<receita>-NN.png, saida/kit-<receita>.pdf e o QA gravado (saida/qa.txt, saida/qa-<receita>.txt ou --qa).
Não renderiza, não roda o QA e não escreve nada na pasta do kit.

Uso:
  python3 medir_kit.py <pasta> [--antes <pasta-anterior>] [--receita r1] [--receita-antes r1]
                       [--qa <arquivo>] [--qa-antes <arquivo>] [--json] [--saida <arquivo.json>]

Grave o QA antes de medir: `python3 qa.py <pasta> > <pasta>/saida/qa.txt`. Sem ele a medida do QA fica "sem dado" e o
veredito sai INCOMPLETO, nunca "passou".

Medidas (cada critério com a meta, o valor e passou/falhou; `nivel` meta decide, aviso e info só informam):
  familias_por_pagina  famílias de recurso que cada página usa (recursos da composição e dos itens do plano, família de
                       direcao_criativa.recursos): ≥ 2 em toda página que não é de respiro (intensidade declarada 0 ou 1)
  cobertura_familias   as 8 famílias menos as de direcao_criativa.nao_usa, cada uma em ≥ 3 páginas
  elementos_ancorados  herói, apoio, estrutura e acabamento (sem os derivados) vindos da composição com âncora resolvida,
                       sem erro na página e cumprida contra os alvos do render final (composicao.conferir): 100%
  continuidade_fio     o motivo de direcao_criativa.fio_condutor em ≥ 6 páginas com o mesmo hash do tratamento (o
                       desenho, o blend, a máscara e o material: a assinatura que o qa_conjunto compara); nenhuma página
                       do fio com outro tratamento
  variedade            estrutura da página = o arquétipo e a variante (rótulo) mais o esqueleto ancorado (função e
                       relação de cada elemento, sem as constantes); estruturas distintas ≥ as do antes; nenhum par de
                       vizinhas com a mesma estrutura
  ritmo                intensidade calculada (a do qa_conjunto): 3 seguidas em 3 reprova; 4 seguidas sem 0 ou 1 avisa
  legibilidade         contraste mínimo por página (a conta do qa.py, qa.contraste_do_texto, no PNG do render): nenhuma
                       linha abaixo do mínimo; mediana dos mínimos ≥ 95% da do antes; nenhuma linha de corpo, preço,
                       número ou micro coberta (acima do limite do qa_geometria) por textura fora do véu e sem fundo
                       próprio
  pdf                  0 fonte Type 3; o título de cada página como texto naquela página; a tese como texto no PDF; o
                       tamanho é só informado, nunca reprova (ordem do Ugo, 12/10/2026)
  qa                   o QA gravado com 0 falha

Com --antes, o kit anterior passa pelas mesmas medidas, lado a lado, com a diferença (depois menos antes). Número de
páginas diferente avisa e não quebra: as medidas são do conjunto. Medida que o kit não declara (mk-2.0 não tem direção
criativa) sai "nao_se_aplica", e não zero: a tabela de inferência da references/10 estima a v2 por olho, não por artefato.
Sai com 1 quando alguma medida falha.
"""
import argparse, hashlib, json, re, statistics, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

META_FAMILIAS_PAGINA = 2
META_PAGINAS_FAMILIA = 3
META_PAGINAS_FIO = 6
META_MEDIANA_CONTRASTE = 0.95
PAPEIS_ANCORA = ("heroi", "ornamento", "apoio", "estrutura", "acabamento")
CLASSES_SOB_TEXTURA = ("corpo", "preco", "numero", "micro")
QA_PADRAO = ("qa.txt", "qa-{receita}.txt")


# ------------------------------------------------------------------------------------------------- leitura dos artefatos
class Kit:
    """Os artefatos de um kit renderizado (só leitura)."""

    def __init__(self, pasta, receita=None, qa=None):
        self.pasta = Path(pasta).resolve()
        mk = self.pasta / "mediakit.json"
        if not mk.is_file():
            raise SystemExit(f"{self.pasta}: sem mediakit.json")
        self.k = json.loads(mk.read_text(encoding="utf-8"))
        self.saida = self.pasta / "saida"
        planos = sorted(f for f in self.saida.glob("plano-elementos-*.json") if not f.stem.endswith("-vertical"))
        rep_p = self.saida / "render-report.json"
        self.report = json.loads(rep_p.read_text(encoding="utf-8")) if rep_p.is_file() else {}
        if receita is None:
            receita = (planos[0].stem[len("plano-elementos-"):] if planos
                       else next(iter(self.report.get("direcoes") or {}), None))
        if receita is None:
            raise SystemExit(f"{self.pasta}: nenhum plano de elementos nem render-report em saida/: renderize antes")
        self.receita = receita
        pl = self.saida / f"plano-elementos-{receita}.json"
        self.plano = json.loads(pl.read_text(encoding="utf-8")) if pl.is_file() else None
        hz = (((self.report.get("direcoes") or {}).get(receita) or {}).get("horizontal") or {})
        self.por_pagina = hz.get("por_pagina") or []
        self.pdf = self.saida / f"kit-{receita}.pdf"
        self.qa = Path(qa) if qa else next((self.saida / n.format(receita=receita) for n in QA_PADRAO
                                            if (self.saida / n.format(receita=receita)).is_file()), None)
        self.W = float((self.plano or {}).get("largura", 1920))
        self.H = float((self.plano or {}).get("altura", 1080))

    @property
    def nome(self):
        return self.pasta.name

    def png(self, n):
        p = self.saida / "png" / f"kit-{self.receita}-{n:02d}.png"
        return p if p.is_file() else None

    def n_paginas(self):
        if self.plano:
            return len(self.plano.get("paginas") or [])
        return len(self.por_pagina)


def _dc(k):
    dc = (k or {}).get("direcao_criativa")
    return dc if isinstance(dc, dict) else {}


def recursos_declarados(k):
    return {r.get("id"): r for r in _dc(k).get("recursos") or [] if isinstance(r, dict) and r.get("id")}


def paginas(plano, k):
    """Por página do plano, em ordem: {n, rotulo, chave, ent, pg, recursos, familias, intensidade (declarada, calculada)}.
    Recursos = os da composição da página (`acabamento.recursos` e o `recurso` dos elementos, a conta do qa_conjunto)
    mais o `recurso` dos itens do plano; família = a do recurso em direcao_criativa.recursos."""
    import qa_conjunto
    decl = recursos_declarados(k)
    out = []
    for n, rot, chave, ent, pg in qa_conjunto.paginas_do_plano(plano or {}, k):
        rids = qa_conjunto.recursos_da_entrada(ent)
        rids += [it["recurso"] for it in pg.get("elementos") or [] if isinstance(it.get("recurso"), str)]
        rids = list(dict.fromkeys(rids))
        fams = sorted({decl[r]["familia"] for r in rids if r in decl and decl[r].get("familia")})
        out.append({"n": n, "rotulo": rot, "chave": chave, "ent": ent, "pg": pg, "recursos": rids, "familias": fams,
                    "intensidade": qa_conjunto.intensidade(ent, k)})
    return out


# ------------------------------------------------------------------------------------------------- forma das medidas
def criterio(nome, meta, valor, passou, nivel="meta", nota=None):
    c = {"nome": nome, "meta": meta, "valor": valor, "passou": passou, "nivel": nivel}
    if nota:
        c["nota"] = nota
    return c


def medida(id_, nome, criterios, detalhe, aplica=True, nota=None):
    """Estado: nao_se_aplica (o kit não declara o que se mede), falhou (algum critério de nível meta falhou), incompleto
    (algum critério de nível meta sem dado) ou passou."""
    metas = [c for c in criterios if c["nivel"] == "meta"]
    if not aplica:
        estado = "nao_se_aplica"
    elif any(c["passou"] is False for c in metas):
        estado = "falhou"
    elif any(c["passou"] is None for c in metas):
        estado = "incompleto"
    else:
        estado = "passou"
    m = {"id": id_, "nome": nome, "estado": estado, "passou": {"passou": True, "falhou": False}.get(estado),
         "criterios": criterios, "detalhe": detalhe}
    if nota:
        m["nota"] = nota
    return m


def _declara(k):
    import qa_conjunto
    return qa_conjunto.declara_acabamento(k)


# ------------------------------------------------------------------------------------------------- 1 e 2: famílias
def medir_familias(kit, pags):
    """Famílias por página: ≥ 2 em toda página que não é de respiro (intensidade DECLARADA 0 ou 1: a página que respira
    tem 1 recurso ou nenhum, e 2 recursos já dão intensidade calculada 2). Cobertura: as 8 famílias menos as de
    direcao_criativa.nao_usa, cada uma em ≥ 3 páginas."""
    decl = recursos_declarados(kit.k)
    aplica = bool(decl) and bool(pags)
    por = [{"n": p["n"], "rotulo": p["rotulo"], "recursos": p["recursos"], "familias": p["familias"],
            "intensidade": p["intensidade"][1], "declarada": p["intensidade"][0]} for p in pags]
    qtd = [len(p["familias"]) for p in pags]
    respiro = [p["n"] for p in pags if p["intensidade"][0] in (0, 1)]
    sem_respiro = [len(p["familias"]) for p in pags if p["n"] not in respiro]
    abaixo = [p["n"] for p in pags if p["n"] not in respiro and len(p["familias"]) < META_FAMILIAS_PAGINA]
    minimo = min(qtd) if qtd else None
    min_sem = min(sem_respiro) if sem_respiro else None
    detalhe = {"paginas": por, "minimo": minimo, "media": round(statistics.mean(qtd), 2) if qtd else None,
               "paginas_abaixo": abaixo, "paginas_respiro": respiro, "minimo_sem_respiro": min_sem}
    nota = None if aplica else "o kit não declara direcao_criativa.recursos (mk-2.0): família não se mede no artefato"
    if aplica and respiro:
        nota = (f"{len(respiro)} página(s) de respiro (intensidade declarada 0 ou 1: p.{', p.'.join(map(str, respiro))}) "
                f"ficam fora da meta; o mínimo com elas é {minimo}")
    crit = [criterio("famílias por página fora do respiro", f"≥ {META_FAMILIAS_PAGINA} em toda página que não é de respiro",
                     min_sem, (not abaixo) if aplica else None)]
    m1 = medida("familias_por_pagina", "famílias por página", crit, detalhe, aplica, nota)

    from acabamento import FAMILIAS as fams
    nao_usa = [f for f in _dc(kit.k).get("nao_usa") or [] if isinstance(f, str)]
    exigidas = [f for f in fams if f not in nao_usa]
    cob = {f: [p["n"] for p in pags if f in p["familias"]] for f in fams}
    ok = [f for f in exigidas if len(cob[f]) >= META_PAGINAS_FAMILIA]
    det2 = {"paginas_por_familia": cob, "familias_exigidas": len(exigidas), "familias_com_meta": len(ok),
            "faltando": [f for f in exigidas if f not in ok], "nao_usa": nao_usa}
    crit2 = [criterio("famílias em 3 páginas ou mais",
                      f"as {len(exigidas)} famílias ({len(fams)} menos as de nao_usa), cada uma em ≥ {META_PAGINAS_FAMILIA} páginas",
                      len(ok), (len(ok) == len(exigidas)) if aplica else None)]
    nota2 = (f"fora da meta por nao_usa: {', '.join(nao_usa)}" if aplica and nao_usa else (None if aplica else nota))
    return m1, medida("cobertura_familias", "cobertura das famílias", crit2, det2, aplica, nota2)


# ------------------------------------------------------------------------------------------------- 3: âncora
def medir_ancorados(kit):
    import composicao, qa_geometria
    if not kit.plano:
        return medida("elementos_ancorados", "elementos ancorados", [criterio("ancorados", "100%", None, None)],
                      {}, nota="sem plano de elementos gravado (saida/plano-elementos-<receita>.json)")
    total, fora = 0, []
    for pg in kit.plano.get("paginas") or []:
        erros = [str(e) for e in pg.get("erros_composicao") or []]
        alvos = pg.get("alvos")
        dom = {d["id"]: d for d in pg.get("dom") or []} if "dom" in pg else None
        for it in pg.get("elementos") or []:
            if it.get("derivado_de") or it.get("papel") not in PAPEIS_ANCORA:
                continue
            total += 1
            rel = (it.get("ancora") or {}).get("relacao")
            motivo = None
            if it.get("origem") != "composicao" or not rel:
                motivo = f"veio do catálogo ({it.get('encaixe') or 'sem encaixe'}) sem âncora"
            elif any(it["id"] in e for e in erros):
                motivo = "âncora não resolveu: " + next(e for e in erros if it["id"] in e)[:120]
            elif alvos:
                try:
                    _, desl = qa_geometria.tinta_final(it, kit.pasta, dom.get(it["id"]) if dom else None)
                    desvios = composicao.conferir(it, alvos, kit.W, kit.H, desl)
                except Exception as e:                    # plano que não se confere não conta como ancorado
                    desvios = [f"não conferida ({e})"]
                if desvios:
                    motivo = "âncora não cumprida: " + str(desvios[0])[:120]
            if motivo:
                fora.append({"n": pg.get("n"), "id": it["id"], "papel": it.get("papel"), "motivo": motivo})
    pct = round(100.0 * (total - len(fora)) / total, 1) if total else None
    det = {"elementos": total, "ancorados": total - len(fora), "nao_ancorados": fora,
           "erros_de_composicao_no_plano": len(kit.plano.get("composicao_erros") or [])}
    crit = [criterio("elementos ancorados e cumpridos", "100%", f"{total - len(fora)} de {total} ({_fmt(pct)}%)" if total else None,
                     (not fora) if total else None)]
    det["porcentagem"] = pct
    return medida("elementos_ancorados", "elementos ancorados", crit, det,
                  nota=None if total else "nenhum herói, apoio, estrutura ou acabamento no plano")


# ------------------------------------------------------------------------------------------------- 4: fio condutor
def _hash(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()[:12]


def medir_continuidade(kit, pags):
    import qa_conjunto
    fio = _dc(kit.k).get("fio_condutor")
    aplica = isinstance(fio, dict) and bool(fio.get("motivo")) and kit.plano is not None
    if not aplica:
        return medida("continuidade_fio", "continuidade do fio condutor",
                      [criterio("páginas com o fio no mesmo tratamento", f"≥ {META_PAGINAS_FIO}", None, None)], {},
                      aplica=False, nota="o kit não declara direcao_criativa.fio_condutor" if kit.plano else
                      "sem plano de elementos gravado")
    motivo, els = fio["motivo"], qa_conjunto._els(kit.k)
    por_pagina = {}
    for p in pags:
        comp_els = [e for e in (p["ent"] or {}).get("elementos") or [] if isinstance(e, dict) and e.get("id")]
        assin = set()
        for it in p["pg"].get("elementos") or []:
            if it.get("derivado_de"):
                continue
            decl = next((e for e in comp_els if it["id"] == e["id"] or it["id"].startswith(e["id"] + "-p")), None)
            mot = it.get("motivo") or qa_conjunto._motivo(it, els) or (qa_conjunto._motivo(decl, els) if decl else None)
            if mot != motivo:
                continue
            # o tratamento que o QA compara: a declaração da composição (quando há) ou o próprio item do plano
            assin.add(qa_conjunto._assinatura_fio(decl or it, els))
        if assin:
            por_pagina[p["n"]] = _hash(sorted(assin, key=str))
    grupos = {}
    for n, h in por_pagina.items():
        grupos.setdefault(h, []).append(n)
    maior_h, maior = max(grupos.items(), key=lambda kv: (len(kv[1]), -min(kv[1])), default=(None, []))
    fora = sorted(n for h, ns in grupos.items() if h != maior_h for n in ns)
    segundo = {rid: [p["n"] for p in pags if rid in p["recursos"]] for rid in _dc(kit.k).get("repete_entre_paginas") or []
               if isinstance(rid, str)}
    det = {"motivo": motivo, "paginas_com_fio": sorted(por_pagina), "hash_por_pagina": por_pagina,
           "maior_grupo": {"hash": maior_h, "paginas": sorted(maior)}, "paginas_com_outro_tratamento": fora,
           "papeis_declarados": len(fio.get("papeis") or {}), "segundo_fio": segundo}
    crit = [criterio("páginas com o fio no mesmo tratamento", f"≥ {META_PAGINAS_FIO}", len(maior), len(maior) >= META_PAGINAS_FIO),
            criterio("páginas do fio com outro tratamento", "0", len(fora), not fora)]
    return medida("continuidade_fio", "continuidade do fio condutor", crit, det)


# ------------------------------------------------------------------------------------------------- 5: variedade
def estrutura(pg):
    """Assinatura da estrutura da página: o rótulo (arquétipo e variante) e o esqueleto ancorado (função ou papel e
    relação de cada elemento; pattern conta como pattern; constantes e derivados ficam fora, são iguais em todo kit)."""
    partes = []
    for it in pg.get("elementos") or []:
        if it.get("derivado_de") or it.get("papel") == "constante":
            continue
        if it.get("papel") == "pattern":
            partes.append("pattern")
            continue
        partes.append(f"{it.get('funcao') or it.get('papel')}/{(it.get('ancora') or {}).get('relacao') or 'sem-ancora'}")
    return f"{pg.get('rotulo', '?')} | {', '.join(sorted(partes)) or 'sem elementos'}"


def medir_variedade(kit, antes_distintas=None, com_antes=False):
    """Sem --antes (ou medindo o próprio antes), o critério contra o antes só informa."""
    if not kit.plano:
        return medida("variedade", "variedade", [criterio("vizinhas com a mesma estrutura", "0", None, None)], {},
                      nota="sem plano de elementos gravado")
    pgs = sorted(kit.plano.get("paginas") or [], key=lambda p: p["n"])
    est = [(pg["n"], estrutura(pg)) for pg in pgs]
    iguais = [[a[0], b[0]] for a, b in zip(est, est[1:]) if a[1] == b[1]]
    distintas = len({e for _, e in est})
    det = {"estruturas": {n: e for n, e in est}, "distintas": distintas, "vizinhas_iguais": iguais}
    crit = [criterio("estruturas de página distintas", "≥ as do antes", distintas,
                     None if antes_distintas is None else distintas >= antes_distintas,
                     nivel="meta" if com_antes else "info",
                     nota=None if com_antes else "sem --antes: só a contagem"),
            criterio("pares de vizinhas com a mesma estrutura", "0", len(iguais), not iguais)]
    if antes_distintas is not None:
        crit[0]["antes"] = antes_distintas
    return medida("variedade", "variedade", crit, det)


# ------------------------------------------------------------------------------------------------- 6: ritmo
def medir_ritmo(kit, pags):
    import qa_conjunto as qc
    aplica = _declara(kit.k) and bool(pags)
    ints = [(p["n"], p["intensidade"][1]) for p in pags]
    marc = [c for c in qc._corridas([n for n, v in ints if v >= qc.INTENSIDADE_MAX]) if len(c) >= qc.SEGUIDAS_MARCANTES]
    ruins = set()
    for i in range(len(ints) - qc.JANELA_RESPIRO + 1):
        jan = ints[i:i + qc.JANELA_RESPIRO]
        if all(v > 1 for _, v in jan):
            ruins.update(n for n, _ in jan)
    sem_resp = qc._corridas(sorted(ruins))
    det = {"intensidades": [v for _, v in ints], "declaradas": [p["intensidade"][0] for p in pags],
           "marcantes": sum(1 for _, v in ints if v >= qc.INTENSIDADE_MAX), "corridas_marcantes": marc,
           "sem_respiro": sem_resp}
    crit = [criterio(f"{qc.SEGUIDAS_MARCANTES} páginas seguidas em intensidade {qc.INTENSIDADE_MAX}", "nenhuma",
                     len(marc), (not marc) if aplica else None),
            criterio(f"{qc.JANELA_RESPIRO} seguidas sem nenhuma de intensidade 0 ou 1", "nenhuma", len(sem_resp),
                     (not sem_resp) if aplica else None, nivel="aviso")]
    return medida("ritmo", "ritmo", crit, det, aplica,
                  None if aplica else "o kit não declara a camada de acabamento: sem intensidade por página")


# ------------------------------------------------------------------------------------------------- 7: legibilidade
def _sobre(a, b):
    """Área da interseção de duas caixas (x, y, w, h)."""
    ix = max(0.0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    iy = max(0.0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    return ix * iy


def luminancia_nas_caixas(rgb, textos):
    """A luminância (qa.lum_wcag) só onde a conta do contraste lê: a caixa de cada texto com 7 px de folga (o anel do
    qa.contraste_do_texto tem 6). O resto fica zero e nunca é lido; a página inteira custaria 6 milhões de potências."""
    import numpy as np
    import qa
    H, W = rgb.shape[:2]
    L = np.zeros((H, W))
    for t in textos:
        x0, y0 = max(0, int(t["x"]) - 7), max(0, int(t["y"]) - 7)
        x1, y1 = min(W, int(t["x"] + t["w"]) + 7), min(H, int(t["y"] + t["h"]) + 7)
        if x1 > x0 and y1 > y0:
            L[y0:y1, x0:x1] = qa.lum_wcag(rgb[y0:y1, x0:x1].astype(float) / 255.0)
    return L


def contrastes(kit):
    """{n: {minimo, linhas, abaixo: [{texto, razao, minimo}]}} das páginas com PNG, pela conta do qa.py."""
    import numpy as np
    from PIL import Image
    import qa
    out = {}
    for p in kit.por_pagina:
        n = p.get("pagina")
        png = kit.png(n) if isinstance(n, int) else None
        if not png:
            continue
        L = luminancia_nas_caixas(np.asarray(Image.open(png).convert("RGB")), p.get("textos") or [])
        rs = []
        for t in p.get("textos") or []:
            r = qa.contraste_do_texto(L, t, p.get("pattern"))
            if r:
                rs.append((r[0], r[1], t.get("texto") or ""))
        out[n] = {"minimo": round(min(r[0] for r in rs), 2) if rs else None, "linhas": len(rs),
                  "abaixo": [{"texto": t[:40], "razao": round(r, 2), "minimo": m} for r, m, t in rs if r < m]}
    return out


def texto_sobre_textura(kit):
    """Linhas de corpo, preço, número ou micro cobertas acima do limite do qa_geometria por textura (pattern, tipo de
    textura ou recurso da família pattern-textura) fora do véu (camada diferente de sob-veu), sem fundo próprio (texto
    com `bg` no render-report pinta o próprio fundo por cima da textura)."""
    import qa_geometria as qg
    achados = []
    if not kit.plano:
        return achados
    textos = {p.get("pagina"): p.get("textos") or [] for p in kit.por_pagina}
    for pg in kit.plano.get("paginas") or []:
        for it in pg.get("elementos") or []:
            if it.get("derivado_de") or it.get("camada") == "sob-veu":
                continue
            if not (it.get("papel") == "pattern" or qg.eh_textura(it, kit.k)):
                continue
            if it.get("papel") == "pattern":       # a textura de fundo cobre a área dela (o qa_geometria a deixa fora)
                import numpy as np
                m, ox, oy = np.ones((max(1, round(it["h"])), max(1, round(it["w"]))), bool), round(it["x"]), round(it["y"])
            else:
                m, ox, oy = qg.mascara(it, kit.pasta)
            for lp in pg.get("protegidos") or []:
                cl = lp.get("classe")
                if cl not in CLASSES_SOB_TEXTURA:
                    continue
                cob = qg.pixels_em(m, ox, oy, lp["x"], lp["y"], lp["x"] + lp["w"], lp["y"] + lp["h"]) / max(1.0, lp["w"] * lp["h"])
                if cob <= qg.LIMITE.get(cl, 0.04):
                    continue
                area = max(1.0, lp["w"] * lp["h"])
                if any(t.get("bg") and _sobre(t, lp) >= 0.5 * area for t in textos.get(pg.get("n"), [])):
                    continue
                achados.append({"n": pg.get("n"), "textura": it["id"], "camada": it.get("camada"), "classe": cl,
                                "texto": (lp.get("texto") or "")[:40], "cobertura": round(min(1.0, cob), 3)})
    return achados


def medir_legibilidade(kit, antes_mediana=None, com_antes=False):
    """Sem --antes (ou medindo o próprio antes), a mediana contra o antes só informa."""
    cs = contrastes(kit)
    minimos = [v["minimo"] for v in cs.values() if v["minimo"] is not None]
    mediana = round(statistics.median(minimos), 2) if minimos else None
    abaixo = [dict(a, n=n) for n, v in sorted(cs.items()) for a in v["abaixo"]]
    sob = texto_sobre_textura(kit)
    det = {"contraste_minimo_por_pagina": {n: v["minimo"] for n, v in sorted(cs.items())}, "mediana": mediana,
           "paginas_com_png": len(cs), "linhas_abaixo_do_minimo": abaixo, "texto_sobre_textura_sem_veu": sob}
    if antes_mediana is not None:
        det["mediana_antes"] = antes_mediana
    sem_png = "sem PNG do render em saida/png (renderize com --png)" if not cs else None
    alvo = round(META_MEDIANA_CONTRASTE * antes_mediana, 2) if antes_mediana else None
    crit = [criterio("linhas abaixo do mínimo do QA (4,5:1; 3:1 a partir de 24 px)", "0", len(abaixo) if cs else None,
                     (not abaixo) if cs else None, nota=sem_png),
            criterio("mediana do contraste mínimo por página", f"≥ {META_MEDIANA_CONTRASTE:.0%} da do antes"
                     + (f" ({_fmt(alvo)}:1)" if alvo else ""), mediana,
                     None if (mediana is None or not antes_mediana) else mediana >= alvo,
                     nivel="meta" if com_antes else "info",
                     nota=sem_png or (None if not com_antes or antes_mediana else "o antes não tem PNG do render: sem comparação")
                     or (None if com_antes else "sem --antes: só o valor")),
            criterio("linhas de corpo, preço, número ou micro sobre textura sem véu", "0",
                     len(sob) if kit.plano else None, (not sob) if kit.plano else None,
                     nota=None if kit.plano else "sem plano de elementos gravado")]
    return medida("legibilidade", "legibilidade", crit, det)


# ------------------------------------------------------------------------------------------------- 8: PDF
def _run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True).stdout
    except FileNotFoundError:
        return None


def titulos_da_pagina(kit, n):
    """Os títulos que a página n tem de levar como texto: as linhas `titulo` do plano; sem plano, os textos `display`
    ou `titulo` do render-report."""
    pg = next((p for p in (kit.plano or {}).get("paginas") or [] if p.get("n") == n), None)
    ts = [lp.get("texto") for lp in (pg or {}).get("protegidos") or [] if lp.get("classe") == "titulo" and lp.get("texto")]
    if not ts:
        rp = next((p for p in kit.por_pagina if p.get("pagina") == n), {})
        ts = [t.get("texto") for t in rp.get("textos") or [] if re.search(r"\b(display|titulo)\b", str(t.get("cls") or "")) and t.get("texto")]
    return list(dict.fromkeys(ts))


def medir_pdf(kit):
    import validar_pdf as vp
    if not kit.pdf.is_file():
        return medida("pdf", "PDF entregue", [criterio("PDF", "existe", None, None)], {},
                      nota=f"{kit.pdf.name} não existe em saida/")
    info = _run(["pdfinfo", str(kit.pdf)])
    if info is None:
        return medida("pdf", "PDF entregue", [criterio("poppler", "instalado", None, None)], {},
                      nota="poppler (pdfinfo, pdffonts, pdftotext) não encontrado")
    m = re.search(r"Pages:\s+(\d+)", info)
    n_pdf = int(m.group(1)) if m else 0
    type3 = []
    for l in (_run(["pdffonts", str(kit.pdf)]) or "").splitlines()[2:]:
        if "Type 3" in l:
            type3.append(l.split()[0] if l.split() else "?")
    faltando, conferidos = [], 0
    n_plano = kit.n_paginas()
    # o pdftotext fecha cada página com \f: duas chamadas (layout e -raw, o que o validar_pdf lê) dão todas as páginas
    normal = (_run(["pdftotext", str(kit.pdf), "-"]) or "").split("\f")
    cru = (_run(["pdftotext", "-raw", str(kit.pdf), "-"]) or "").split("\f")
    for n in range(1, min(n_pdf, n_plano) + 1):
        alvos = [c for c in (vp.comparavel(t) for t in titulos_da_pagina(kit, n)) if c]
        if not alvos:
            continue
        doc = (normal[n - 1] if n <= len(normal) else "") + "\n" + (cru[n - 1] if n <= len(cru) else "")
        for a in alvos:
            conferidos += 1
            if not vp.texto_presente(a, doc):
                faltando.append({"n": n, "titulo": a})
    tese = ((kit.k.get("tese") or {}).get("frase") or "").strip()
    tudo = "\n".join(normal) + "\n" + "\n".join(cru)
    tese_ok = vp.texto_presente(tese, tudo) if tese else None
    tam = kit.pdf.stat().st_size
    det = {"arquivo": kit.pdf.name, "paginas_pdf": n_pdf, "paginas_plano": n_plano, "fontes_type3": type3,
           "titulos_conferidos": conferidos, "titulos_faltando": faltando, "tese_como_texto": tese_ok,
           "bytes": tam, "mb": round(tam / 1e6, 1)}
    crit = [criterio("fontes Type 3", "0", len(type3), not type3),
            criterio("títulos de cada página como texto naquela página", "todos", f"{conferidos - len(faltando)} de {conferidos}",
                     (not faltando) if conferidos else None,
                     nota=None if conferidos else "nenhum título medido no plano nem no render-report"),
            criterio("tese como texto no PDF", "sim", tese_ok, tese_ok, nota=None if tese else "o kit não tem tese.frase"),
            criterio("tamanho do PDF", "só informado, nunca reprova (ordem do Ugo, 12/10/2026)", f"{tam / 1e6:.1f} MB".replace(".", ","),
                     None, nivel="info")]
    if n_pdf != n_plano:
        crit.append(criterio("páginas do PDF e do plano", "iguais", f"{n_pdf} e {n_plano}", False, nivel="aviso"))
    return medida("pdf", "PDF entregue", crit, det)


# ------------------------------------------------------------------------------------------------- 9: QA
def medir_qa(kit):
    if not kit.qa or not kit.qa.is_file():
        return medida("qa", "QA", [criterio("falhas no QA gravado", "0", None, None)], {"arquivo": None},
                      nota="sem QA gravado: rode `qa.py <pasta> > <pasta>/saida/qa.txt` (ou passe --qa)")
    linhas = kit.qa.read_text(encoding="utf-8", errors="replace").splitlines()
    falhas = [l for l in linhas if l.startswith("FALHA")]
    avisos = [l for l in linhas if l.startswith("AVISO")]
    det = {"arquivo": str(kit.qa), "falhas": len(falhas), "avisos": len(avisos), "primeiras_falhas": [l[:160] for l in falhas[:5]]}
    nota = None
    if kit.pdf.is_file() and kit.qa.stat().st_mtime < kit.pdf.stat().st_mtime:
        nota = "o QA gravado é anterior ao PDF: rode o qa.py de novo sobre o render atual"
        det["anterior_ao_pdf"] = True
    return medida("qa", "QA", [criterio("falhas no QA gravado", "0", len(falhas), not falhas)], det, nota=nota)


# ------------------------------------------------------------------------------------------------- conjunto
ORDEM = ("familias_por_pagina", "cobertura_familias", "elementos_ancorados", "continuidade_fio", "variedade", "ritmo",
         "legibilidade", "pdf", "qa")
# valor principal de cada medida para a comparação antes e depois: (caminho no detalhe, rótulo)
PRINCIPAIS = {
    "familias_por_pagina": [("minimo_sem_respiro", "mínimo de famílias fora do respiro"), ("media", "média de famílias por página")],
    "cobertura_familias": [("familias_com_meta", "famílias em 3 páginas ou mais")],
    "elementos_ancorados": [("ancorados", "elementos ancorados"), ("elementos", "elementos")],
    "continuidade_fio": [("maior_grupo.paginas", "páginas com o fio no mesmo tratamento")],
    "variedade": [("distintas", "estruturas distintas"), ("vizinhas_iguais", "vizinhas com a mesma estrutura")],
    "ritmo": [("marcantes", "páginas em intensidade 3"), ("corridas_marcantes", "corridas de 3 marcantes")],
    "legibilidade": [("mediana", "mediana do contraste mínimo"), ("linhas_abaixo_do_minimo", "linhas abaixo do mínimo"),
                     ("texto_sobre_textura_sem_veu", "linhas sobre textura sem véu")],
    "pdf": [("fontes_type3", "fontes Type 3"), ("titulos_faltando", "títulos fora do texto"), ("mb", "MB (informação)")],
    "qa": [("falhas", "falhas no QA")],
}


def _valor(det, caminho):
    v = det
    for parte in caminho.split("."):
        v = v.get(parte) if isinstance(v, dict) else None
    return len(v) if isinstance(v, list) else v


def medir(kit, antes_vals=None):
    """Todas as medidas de um kit. `antes_vals` = {distintas, mediana} do kit anterior (com --antes); sem ele, as
    comparações com o antes só informam (o próprio antes é medido assim)."""
    com_antes = antes_vals is not None
    antes_vals = antes_vals or {}
    pags = paginas(kit.plano, kit.k) if kit.plano else []
    m1, m2 = medir_familias(kit, pags)
    ms = [m1, m2, medir_ancorados(kit), medir_continuidade(kit, pags),
          medir_variedade(kit, antes_vals.get("distintas"), com_antes), medir_ritmo(kit, pags),
          medir_legibilidade(kit, antes_vals.get("mediana"), com_antes), medir_pdf(kit), medir_qa(kit)]
    estados = [m["estado"] for m in ms]
    veredito = "falhou" if "falhou" in estados else ("incompleto" if "incompleto" in estados else "passou")
    return {"kit": str(kit.pasta), "nome": kit.nome, "receita": kit.receita,
            "schema_version": kit.k.get("schema_version"), "paginas": kit.n_paginas(),
            "veredito": veredito, "passou": {"passou": True, "falhou": False}.get(veredito), "medidas": ms}


def comparar(depois, antes):
    """[{medida, valor, depois, antes, diferenca}] dos valores principais (diferença = depois menos antes)."""
    da, an = {m["id"]: m for m in depois["medidas"]}, {m["id"]: m for m in antes["medidas"]}
    out = []
    for mid in ORDEM:
        for caminho, rot in PRINCIPAIS.get(mid, []):
            d = _valor(da[mid]["detalhe"], caminho) if da[mid]["estado"] != "nao_se_aplica" else None
            a = _valor(an[mid]["detalhe"], caminho) if an[mid]["estado"] != "nao_se_aplica" else None
            dif = round(d - a, 2) if isinstance(d, (int, float)) and isinstance(a, (int, float)) and not isinstance(d, bool) else None
            out.append({"medida": mid, "valor": rot, "depois": d, "antes": a, "diferenca": dif})
    return out


def medir_com_antes(pasta, antes=None, receita=None, receita_antes=None, qa=None, qa_antes=None):
    kit = Kit(pasta, receita, qa)
    if not antes:
        res = medir(kit)
        res["resumo"] = resumo(res)
        return res
    ka = Kit(antes, receita_antes, qa_antes)
    ra = medir(ka)
    vals = {"distintas": next(m for m in ra["medidas"] if m["id"] == "variedade")["detalhe"].get("distintas"),
            "mediana": next(m for m in ra["medidas"] if m["id"] == "legibilidade")["detalhe"].get("mediana")}
    res = medir(kit, vals)
    avisos = []
    if ka.n_paginas() != kit.n_paginas():
        avisos.append(f"o antes tem {ka.n_paginas()} páginas e o depois {kit.n_paginas()}: as medidas são do conjunto e "
                      f"se comparam assim; a folha antes e depois pareia por composição, rótulo e posição")
    res.update(antes=ra, comparacao=comparar(res, ra), avisos=avisos)
    res["resumo"] = resumo(res)
    return res


# ------------------------------------------------------------------------------------------------- texto
def _fmt(v):
    if v is None:
        return "-"
    if isinstance(v, bool):
        return "sim" if v else "não"
    if isinstance(v, float):
        return f"{v:g}".replace(".", ",")
    return str(v)


ESTADO = {"passou": "passou", "falhou": "FALHOU", "incompleto": "sem dado", "nao_se_aplica": "não se aplica"}


def resumo(res):
    L = [f"medir_kit: {res['nome']} ({res['receita']}, {res['schema_version']}, {res['paginas']} páginas)"
         + (f" contra {res['antes']['nome']} ({res['antes']['receita']}, {res['antes']['schema_version']}, "
            f"{res['antes']['paginas']} páginas)" if res.get("antes") else "")]
    for a in res.get("avisos") or []:
        L.append(f"AVISO  {a}")
    an = {m["id"]: m for m in (res.get("antes") or {}).get("medidas") or []}
    for m in res["medidas"]:
        L.append("")
        L.append(f"{m['nome']}: {ESTADO[m['estado']]}" + (f"   (antes: {ESTADO[an[m['id']]['estado']]})" if m["id"] in an else ""))
        for c in m["criterios"]:
            nivel = {"aviso": "  [aviso]", "info": "  [informação]"}.get(c["nivel"], "")
            marca = {True: "ok", False: "NÃO", None: "--"}[c["passou"]]
            L.append(f"  {marca:>3}  {c['nome']}: {_fmt(c['valor'])} (meta {c['meta']}){nivel}"
                     + (f"; {c['nota']}" if c.get("nota") else ""))
        if m.get("nota"):
            L.append(f"       nota: {m['nota']}")
    if res.get("comparacao"):
        L.append("")
        L.append("antes e depois (diferença = depois menos antes):")
        for c in res["comparacao"]:
            L.append(f"  {c['valor']}: antes {_fmt(c['antes'])}, depois {_fmt(c['depois'])}"
                     + (f", diferença {'+' if c['diferenca'] > 0 else ''}{_fmt(c['diferenca'])}" if c["diferenca"] is not None else ""))
    falhas = [m["nome"] for m in res["medidas"] if m["estado"] == "falhou"]
    sem = [m["nome"] for m in res["medidas"] if m["estado"] == "incompleto"]
    L.append("")
    L.append("VEREDITO: " + {"passou": "PASSOU em todas as medidas",
                             "falhou": f"FALHOU em {len(falhas)}: {', '.join(falhas)}",
                             "incompleto": f"INCOMPLETO, sem dado em: {', '.join(sem)}"}[res["veredito"]]
             + (f" (e sem dado em: {', '.join(sem)})" if res["veredito"] == "falhou" and sem else ""))
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="mede um kit renderizado lendo só os artefatos (references/10, Prova para dono cético)")
    ap.add_argument("pasta")
    ap.add_argument("--antes", default=None, help="pasta do kit anterior: as mesmas medidas lado a lado e a diferença")
    ap.add_argument("--receita", default=None)
    ap.add_argument("--receita-antes", default=None)
    ap.add_argument("--qa", default=None, help="saída gravada do qa.py (padrão: saida/qa.txt ou saida/qa-<receita>.txt)")
    ap.add_argument("--qa-antes", default=None)
    ap.add_argument("--json", action="store_true", help="imprime o JSON (com o resumo em texto no campo `resumo`)")
    ap.add_argument("--saida", default=None, help="grava o JSON neste arquivo")
    a = ap.parse_args()
    res = medir_com_antes(a.pasta, a.antes, a.receita, a.receita_antes, a.qa, a.qa_antes)
    texto = json.dumps(res, ensure_ascii=False, indent=1, default=str)
    if a.saida:
        Path(a.saida).write_text(texto, encoding="utf-8")
    print(texto if a.json else res["resumo"])
    sys.exit(1 if res["veredito"] == "falhou" else 0)


if __name__ == "__main__":
    main()

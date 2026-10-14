#!/usr/bin/env python3
"""
contact_sheet.py: folha de contato para a revisão visual (SKILL etapas 6 e 9; o estudo A/B é da 3b).

Uso:
  python3 contact_sheet.py <pasta-do-cliente> [--direcao causa | --receita r1] [--regua <pasta-regua>] [--n-ref 2] [--saida arquivo.png]

Monta uma grade com todas as páginas da direção. Com --regua, cada página ganha ao lado as páginas equivalentes das
referências das pesquisas, lidas de regua/indice.json (montado por regua.py): a principal (kit-régua) e a que combina
com o tom da direção, cada uma com a origem escrita embaixo. Sem indice.json, cai no modo antigo (<tipo>.png na pasta).
Com --receita, a sequência e as variantes vêm da receita no render-report; página de variante compara primeiro com a
página da régua que inspirou a variante (VARIANTE_REF, a mesma citada no comentário de cada macro em arquetipos.html).
Abra a folha com UM Read e responda às 8 perguntas do guia-qualidade.md seção I, página por página.

Folha de COMPOSIÇÃO (references/09 §7):
  python3 contact_sheet.py <pasta-do-cliente> --composicao [--receita r1] [--pdf] [--maquete] [--saida arquivo.png]
Desenha sobre cada página do render a caixa da TINTA de cada elemento na cor da função (legenda no topo), a linha
tracejada até o alvo de cada restrição, as zonas vendáveis da foto, as linhas estruturais (margem e colunas) bem leves
e, embaixo, a mensagem e o foco da composição. Lê saida/plano-elementos-<receita>.json e os PNGs do render (--png);
com --pdf, o raster do PDF entregue (pdftoppm), para conferir o arquivo final; com --maquete, o plano e os PNGs da
maquete. Saída saida/composicao-<receita>[-pdf|-maquete].png, páginas em 2 colunas.

Folha de ACABAMENTO (etapa 9, guia de qualidade seção M; references/10, Revisão):
  python3 contact_sheet.py <pasta-do-cliente> --acabamento [--receita r1] [--pdf] [--saida arquivo.png]
Cada página do render (ou do PDF entregue) com a tinta de cada recurso na cor da família e, ao lado, o recorte do
repertório de onde o recurso veio (até 3 por página); embaixo, a intensidade declarada e a calculada, com o teto,
profundidade, grão, luz e o porquê. Página composta sem `acabamento` sai marcada. Saída saida/acabamento-<receita>[-pdf].png.

ESTUDO A/B de um recurso (etapa 3b.4: recurso novo, de intensidade 3 ou sob texto; references/10, Estudo A/B):
  python3 contact_sheet.py <pasta-do-cliente> --estudo <recurso> [--receita r1] [--saida arquivo.png]
A = o recorte do repertório (até 3), B = cada página renderizada que usa o recurso, inteira e com o detalhe ampliado da
região dele. Recusa recurso fora de direcao_criativa.recursos, sem recorte no repertório ou sem página que o use.
Saída <kit>/estudos/<recurso>.png. O recorte serve para comparar o princípio; ele nunca entra no kit.

ANTES E DEPOIS e ESCOLHA CEGA (prova para dono cético; references/10, Prova para dono cético):
  python3 contact_sheet.py <kit-novo> --antes <kit-anterior> [--receita r1] [--receita-antes r1] [--saida arquivo.png]
  python3 contact_sheet.py <kit-novo> --cega <kit-anterior> --semente N [--receita r1] [--receita-antes r1]
--antes grava saida/antes-depois-<receita>.png: por página, a do antes, a do depois e o recorte do recurso principal da
página nova, com as linhas de recursos e de intensidade. --cega grava saida/escolha-cega.png (pares rotulados só A e B,
ordem sorteada pela semente) e saida/escolha-cega-chave.json, e imprime o sha256 da chave para registrar antes de
qualquer juiz. As páginas se pareiam por composição, rótulo e posição; número de páginas diferente avisa e não quebra.
Nada é escrito na pasta do kit anterior.
"""
import argparse, json, math, re, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw
from regua import fonte_ui, referencias

# (tipo, variante) → página da régua que inspirou a variante (arquetipos.html cita a mesma no comentário da macro)
VARIANTE_REF = {("capa", "b"): "amazonia-niv-03", ("capa", "c"): "levinrun-01", ("manifesto", "b"): "saudade-05",
                ("publico", "b"): "saudade-18", ("ativo_painel", "diagonal"): "praia-delas-02", ("ativo_painel", "sangria"): "corre-por-elas-14",
                ("divisor", "b"): "levinrun-02", ("divisor", "c"): "levinrun-04", ("cota", "b"): "levinrun-14", ("cota", "c"): "levinrun-17",
                ("contato", "b"): "levinrun-22"}


# ------------------------------------------------------------------------------------------------- folha de composição
CELULA = 900                      # largura de cada página na folha (2 colunas: ~1850 px, legível num Read)


def _rgb(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def _tracejado(dr, p0, p1, cor, larg=2, traco=9, vao=6):
    (x0, y0), (x1, y1) = p0, p1
    comp = math.hypot(x1 - x0, y1 - y0)
    if comp < 1:
        return
    ux, uy = (x1 - x0) / comp, (y1 - y0) / comp
    s = 0.0
    while s < comp:
        e = min(comp, s + traco)
        dr.line([(x0 + ux * s, y0 + uy * s), (x0 + ux * e, y0 + uy * e)], fill=cor, width=larg)
        s = e + vao


def _rasters(pasta, receita, pdf, maquete, formato):
    """Lista de PNGs das páginas (do render ou do PDF entregue rasterizado num diretório temporário)."""
    saida = pasta / "saida"
    base = f"{'maquete' if maquete else 'kit'}-{receita}{'-vertical' if formato == 'vertical' else ''}"
    if pdf:
        tmp = Path(tempfile.mkdtemp(prefix="folha-comp-"))
        subprocess.run(["pdftoppm", "-png", "-scale-to-x", str(CELULA), "-scale-to-y", "-1", str(saida / f"{base}.pdf"),
                        str(tmp / "p")], check=True)
        return sorted(tmp.glob("p-*.png"), key=lambda p: int(p.stem.split("-")[-1])), tmp
    return sorted((saida / "png").glob(f"{base}-[0-9][0-9].png")), None


def folha_composicao(pasta, receita=None, pdf=False, maquete=False, saida_arq=None, formato="horizontal"):
    """A folha de composição: cada página com a tinta dos elementos na cor da função, a linha até o alvo de cada
    restrição, as zonas vendáveis, a grade leve e a mensagem e o foco embaixo. Devolve o caminho gravado."""
    import shutil
    from camadas import COR_FUNCAO, COR_SEM_FUNCAO, funcao_do_item
    import composicao, qa_geometria
    pasta = Path(pasta).resolve()
    saida = pasta / "saida"
    pref = "plano-maquete-" if maquete else "plano-elementos-"
    if receita is None:
        planos = sorted(f for f in saida.glob(f"{pref}*.json") if not f.stem.endswith("-vertical"))
        if not planos:
            raise SystemExit(f"nenhum {pref}*.json em {saida}: renderize antes")
        receita = planos[0].stem[len(pref):]
    nome = f"{pref}{receita}{'-vertical' if formato == 'vertical' else ''}.json"
    plano = json.loads((saida / nome).read_text(encoding="utf-8"))
    W, H = float(plano.get("largura", 1920)), float(plano.get("altura", 1080))
    pags = plano["paginas"]
    rasters, tmp = _rasters(pasta, receita, pdf, maquete, formato)
    if len(rasters) < len(pags):
        raise SystemExit(f"{len(rasters)} páginas rasterizadas para {len(pags)} no plano: renderize com --png "
                         f"(ou use --pdf sobre o PDF entregue)")
    k = CELULA / W
    th = round(H * k)
    leg_h, cap_h, marg = 64, 92, 24
    cols = 2
    linhas = (len(pags) + cols - 1) // cols
    S = Image.new("RGB", (cols * (CELULA + marg) + marg, leg_h + linhas * (th + cap_h + marg) + marg), (18, 18, 20))
    dr = ImageDraw.Draw(S)
    f14, f16 = fonte_ui(14), fonte_ui(16)
    # legenda: as funções na cor de cada uma, a zona vendável e a linha estrutural
    x = marg
    itens_leg = list(COR_FUNCAO.items()) + [("sem função (catálogo)", COR_SEM_FUNCAO), ("zona vendável", "#FFFFFF"),
                                             ("margem e colunas", "#5AC8FA")]
    for rot, cor in itens_leg:
        dr.rectangle([x, 22, x + 18, 40], outline=_rgb(cor), width=3)
        dr.text((x + 24, 22), rot, fill=(235, 235, 235), font=f14)
        x += 34 + dr.textlength(rot, font=f14)
    dr.text((marg, 44), f"{'maquete' if maquete else 'render'} {receita}{' (PDF entregue)' if pdf else ''}: tinta de cada elemento, "
            f"tracejado até o alvo de cada restrição", fill=(150, 150, 150), font=f14)
    for i, pg in enumerate(pags):
        cx0 = marg + (i % cols) * (CELULA + marg)
        cy0 = leg_h + marg + (i // cols) * (th + cap_h + marg)
        base = Image.open(rasters[i]).convert("RGB").resize((CELULA, th), Image.LANCZOS)
        cam = Image.new("RGBA", (CELULA, th), (0, 0, 0, 0))
        d2 = ImageDraw.Draw(cam)
        P = lambda x_, y_: (x_ * k, y_ * k)
        al = pg.get("alvos") or {}
        if al.get("margem"):
            m = al["margem"]
            d2.rectangle([*P(m["x"], m["y"]), *P(m["x"] + m["w"], m["y"] + m["h"])], outline=_rgb("#5AC8FA", 90), width=1)
            for c in al.get("colunas") or []:
                for xx in (c["x"], c["x"] + c["w"]):
                    d2.line([P(xx, m["y"]), P(xx, m["y"] + m["h"])], fill=_rgb("#5AC8FA", 38), width=1)
        for z in pg.get("vendaveis") or []:
            pts = [P(*p) for p in z["quad"]] if z.get("quad") else [P(z["x"], z["y"]), P(z["x"] + z["w"], z["y"]),
                                                                     P(z["x"] + z["w"], z["y"] + z["h"]), P(z["x"], z["y"] + z["h"])]
            for a_, b_ in zip(pts, pts[1:] + pts[:1]):
                _tracejado(d2, a_, b_, (255, 255, 255, 230), 2, 5, 4)
        dom = {d["id"]: d for d in pg.get("dom") or []}
        for it in pg.get("elementos", []):
            if it.get("papel") == "pattern":
                continue
            cor = _rgb(COR_FUNCAO.get(funcao_do_item(it) or "", COR_SEM_FUNCAO))
            try:
                t, _ = qa_geometria.tinta_final(it, pasta, dom.get(it["id"]))
            except Exception:
                t = (it["x"], it["y"], it["x"] + it["w"], it["y"] + it["h"])
            d2.rectangle([*P(t[0], t[1]), *P(t[2], t[3])], outline=cor, width=3)
            anc = it.get("ancora") or {}
            geo = anc.get("geometria") or {}
            if geo.get("pontos"):
                d2.line([P(*p) for p in geo["pontos"]], fill=cor, width=3)
            for r in anc.get("restricoes") or []:
                v, nome_a = r.get("valor"), r.get("alvo")
                try:
                    ca = composicao.caixa_alvo(al, nome_a) if nome_a else None
                except composicao.ErroComposicao:
                    ca = None
                ax0, ay0, ax1, ay1 = (ca["x"], ca["y"], ca["x"] + ca["w"], ca["y"] + ca["h"]) if ca else (t[0], t[1], t[2], t[3])
                if r.get("eixo") == "x" and isinstance(v, (int, float)):
                    _tracejado(d2, P(v, min(t[1], ay0)), P(v, max(t[3], ay1)), cor)
                elif r.get("eixo") == "y" and isinstance(v, (int, float)):
                    _tracejado(d2, P(min(t[0], ax0), v), P(max(t[2], ax1), v), cor)
                elif r.get("eixo") == "ponto" and isinstance(v, list):
                    px, py = P(*v)
                    d2.ellipse([px - 4, py - 4, px + 4, py + 4], outline=cor, width=2)
                    if ca:
                        _tracejado(d2, (px, py), P((ax0 + ax1) / 2, (ay0 + ay1) / 2), cor, 1)
                elif r.get("eixo") == "caixa" and isinstance(v, list):
                    xx, yy, ww, hh = v
                    for a_, b_ in (((xx, yy), (xx + ww, yy)), ((xx + ww, yy), (xx + ww, yy + hh)),
                                   ((xx + ww, yy + hh), (xx, yy + hh)), ((xx, yy + hh), (xx, yy))):
                        _tracejado(d2, P(*a_), P(*b_), cor)
            d2.text((P(t[0], t[1])[0] + 4, P(t[0], t[1])[1] + 3), it["id"], fill=cor, font=f14)
        S.paste(Image.alpha_composite(base.convert("RGBA"), cam).convert("RGB"), (cx0, cy0))
        cm = pg.get("composicao") or {}
        tit = f"{pg['n']:02d}  {pg.get('rotulo', '?')}" + (f"   composição: {cm.get('chave')}" if cm else "   sem composição (catálogo)")
        dr.text((cx0, cy0 + th + 6), tit, fill=(240, 240, 240), font=f16)
        texto = (f"mensagem: {cm.get('mensagem') or '?'}  ·  foco: {cm.get('foco') or '?'}" if cm else
                 "escreva a composição desta página: mensagem, foco, leitura, estrutura e elementos ancorados")
        palavras, linha, yy = texto.split(), "", cy0 + th + 30
        for p in palavras:
            if dr.textlength(linha + " " + p, font=f14) > CELULA and linha:
                dr.text((cx0, yy), linha, fill=(170, 170, 170), font=f14); yy += 19; linha = p
            else:
                linha = (linha + " " + p).strip()
        if linha and yy < cy0 + th + cap_h:
            dr.text((cx0, yy), linha, fill=(170, 170, 170), font=f14)
    sufixo = "-pdf" if pdf else ("-maquete" if maquete else "")
    out = Path(saida_arq) if saida_arq else saida / f"composicao-{receita}{'-vertical' if formato == 'vertical' else ''}{sufixo}.png"
    S.save(out, optimize=True)
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
    print("OK", out, f"{len(pags)} páginas")
    return out


# ------------------------------------------------------------------------------------------------- acabamento e estudo
# Folha de ACABAMENTO (etapa 9, guia de qualidade seção M) e ESTUDO A/B de um recurso (etapa 3b.4): a página renderizada
# lado a lado com o recorte do repertório de onde o recurso veio (references/10-acabamento.md, Estudo A/B e Revisão).
# O recorte só serve para comparar o PRINCÍPIO: ele nunca entra no kit.
RAIZ_REPERTORIO = Path(__file__).resolve().parent.parent / "repertorio"
ID_RECURSO = re.compile(r"^[a-z0-9][a-z0-9-]{0,80}$")          # vai para o nome do arquivo: estudos/<id>.png
COR_FAMILIA = {"ornamento-identidade": "#FFD400", "pattern-textura": "#A3E635", "sobreposicao-recorte": "#FF6B6B",
               "profundidade-3d": "#5AC8FA", "tratamento-imagem": "#C084FC", "tipografia-expressiva": "#FB923C",
               "acabamento-borda": "#F5F5F5", "composicao-hibrida": "#34D399"}
COR_SEM_FAMILIA = "#9CA3AF"
FUNDO_FOLHA, FUNDO_CELULA = (18, 18, 20), (32, 32, 36)


def _indice_repertorio(rep):
    try:
        return json.loads((Path(rep) / "indice.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def recortes_da_origem(rec, rep=None, indice=None, n=3):
    """Até n recortes [(caminho, legenda, origem)] que mostram de onde o recurso veio, nesta ordem: o recurso do índice com
    o mesmo id; a `referencia` como recurso, como padrão ou como referência (`ref` ou `ref:página`, que também valem
    `ref#página` e `ref@página`: os recortes de padrões e recursos tirados dela, o mapa da página e a página capturada).
    Prefere a versão anotada; antiexemplo fica fora; caminho que sai do repertório é ignorado."""
    rep = Path(rep or RAIZ_REPERTORIO).resolve()
    ind = indice if indice is not None else _indice_repertorio(rep)
    recursos = {r.get("id"): r for r in ind.get("recursos") or [] if isinstance(r, dict)}
    padroes = {p.get("id"): p for p in ind.get("padroes") or [] if isinstance(p, dict)}
    refs = {r.get("id") for r in ind.get("referencias") or [] if isinstance(r, dict)}
    out = []

    def poe(rels, legenda, origem):
        for rel in rels:
            if not rel or len(out) >= n:
                continue
            p = (rep / str(rel)).resolve()
            if rep not in p.parents or not p.is_file() or any(o[0] == p for o in out):
                continue
            out.append((p, legenda or "", origem))
            return

    def da_entrada(ent, nome, ref=None, pagina=None):
        for x in ent.get("recortes") or []:
            if x.get("anti") or (ref and x.get("referencia") != ref) or (pagina is not None and x.get("pagina") != pagina):
                continue
            poe([x.get("anotado"), x.get("arquivo")], x.get("legenda"), f"{nome} · {x.get('referencia', '?')} p. {x.get('pagina', '?')}")

    rid, ref = str(rec.get("id") or ""), str(rec.get("referencia") or "").strip()
    if rid in recursos:
        da_entrada(recursos[rid], f"recurso {rid}")
    if ref in recursos:
        da_entrada(recursos[ref], f"recurso {ref}")
    if ref in padroes:
        da_entrada(padroes[ref], f"padrão {ref}")
    partes = re.split(r"[:#@]", ref, 1)
    base = partes[0]
    m = re.search(r"\d+", partes[1]) if len(partes) > 1 else None
    pagina = int(m.group(0)) if m else None
    if base in refs:
        for i, ent in list(recursos.items()) + list(padroes.items()):
            da_entrada(ent, f"{'recurso' if i in recursos else 'padrão'} {i}", base, pagina)
        if pagina is not None:
            poe([f"mapas/{base}-{pagina:02d}.jpg"], f"página {pagina} de {base} com os recortes marcados", f"mapa {base} p. {pagina}")
            poe([f"capturas/{base}/{pagina:02d}.jpg"], f"página {pagina} de {base} (captura local, fora do git)", f"captura {base} p. {pagina}")
    return out


def _plano_horizontal(pasta, receita=None, maquete=False):
    """(receita, plano) do último render horizontal (o primeiro plano quando a receita não vem)."""
    saida = Path(pasta) / "saida"
    pref = "plano-maquete-" if maquete else "plano-elementos-"
    if receita is None:
        planos = sorted(f for f in saida.glob(f"{pref}*.json") if not f.stem.endswith("-vertical"))
        if not planos:
            raise SystemExit(f"nenhum {pref}*.json em {saida}: renderize antes (render.py --png)")
        receita = planos[0].stem[len(pref):]
    f = saida / f"{pref}{receita}.json"
    if not f.is_file():
        raise SystemExit(f"{f.name} não existe em {saida}: renderize a receita {receita} antes (render.py --png)")
    return receita, json.loads(f.read_text(encoding="utf-8"))


def recursos_da_pagina(pg, k):
    """(chave, entrada da composição, ids de recurso) de uma página do plano: `acabamento.recursos` e o `recurso` dos
    elementos da composição (a conta do qa_conjunto) mais o `recurso` dos itens do plano, sem repetir."""
    import qa_conjunto
    chave = (pg.get("composicao") or {}).get("chave")
    ent = ((k.get("composicao") or {}).get(chave) if chave else None) or {}
    rids = qa_conjunto.recursos_da_entrada(ent)
    rids += [it["recurso"] for it in pg.get("elementos") or [] if isinstance(it.get("recurso"), str)]
    return chave, ent, list(dict.fromkeys(rids))


def _itens_do_recurso(pg, rid):
    """Itens do plano que realizam o recurso: os que declaram `recurso` e os derivados deles (sombra, reflexo)."""
    ids = {it["id"] for it in pg.get("elementos") or [] if it.get("recurso") == rid}
    return [it for it in pg.get("elementos") or [] if it.get("id") in ids or it.get("derivado_de") in ids]


def _tinta(it, pasta, pg):
    import qa_geometria
    dom = {d["id"]: d for d in pg.get("dom") or []}
    try:
        t, _ = qa_geometria.tinta_final(it, pasta, dom.get(it["id"]))
    except Exception:
        t = (it["x"], it["y"], it["x"] + it["w"], it["y"] + it["h"])
    return t


def _encaixar(im, w, h):
    """A imagem inteira centrada numa célula w x h, sem distorcer (amplia quando é menor: o detalhe aparece)."""
    im = im.convert("RGB")
    k = min(w / im.width, h / im.height)
    nova = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    cel = Image.new("RGB", (w, h), FUNDO_CELULA)
    cel.paste(nova, ((w - nova.width) // 2, (h - nova.height) // 2))
    return cel


def _linhas(dr, texto, fonte, largura, maximo=3):
    """O texto quebrado em até `maximo` linhas da largura (a última leva reticências quando corta)."""
    out, linha = [], ""
    for p in str(texto or "").split():
        if linha and dr.textlength(linha + " " + p, font=fonte) > largura:
            out.append(linha)
            linha = p
        else:
            linha = (linha + " " + p).strip()
    if linha:
        out.append(linha)
    if len(out) > maximo:
        out = out[:maximo]
        out[-1] = out[-1].rstrip(".,;:") + "..."
    return out


def _uma_linha(dr, texto, fonte, largura):
    """O texto numa linha só da largura, cortado por letra (com reticências) quando não cabe."""
    t = str(texto or "")
    if dr.textlength(t, font=fonte) <= largura:
        return t
    while t and dr.textlength(t + "...", font=fonte) > largura:
        t = t[:-1]
    return t.rstrip(" .,;:") + "..."


def _cartao_recorte(dr, S, x, y, w, h, recorte, titulo, cor, f14):
    """Um recorte do repertório (ou o aviso de que falta) numa célula com o título na cor da família."""
    alt = h - 44
    if recorte:
        S.paste(_encaixar(Image.open(recorte[0]), w, alt), (x, y))
        rodape = recorte[2]
    else:
        dr.rectangle([x, y, x + w, y + alt], fill=FUNDO_CELULA, outline=(110, 110, 110))
        for i, l in enumerate(_linhas(dr, "sem recorte no repertório: a origem deste recurso não foi conferida", f14, w - 24, 3)):
            dr.text((x + 12, y + 12 + i * 19), l, fill=(230, 120, 120), font=f14)
        rodape = "troque a referência pela que a consulta trouxe"
    dr.rectangle([x, y, x + w, y + alt], outline=_rgb(cor), width=3)
    dr.text((x, y + alt + 4), _uma_linha(dr, titulo, f14, w), fill=_rgb(cor), font=f14)
    dr.text((x, y + alt + 23), _uma_linha(dr, rodape, f14, w), fill=(150, 150, 150), font=f14)


def folha_acabamento(pasta, receita=None, pdf=False, saida_arq=None, rep=None):
    """A folha de acabamento (etapa 9): cada página do render (ou do PDF entregue, com pdf=True) com a tinta dos elementos
    de cada recurso na cor da família e, ao lado, o recorte do repertório de até 3 recursos dela; embaixo, a intensidade
    declarada e a calculada (com o teto), profundidade, grão, luz e o porquê. Grava saida/acabamento-<receita>[-pdf].png e
    devolve {arquivo, receita, paginas: [{n, rotulo, chave, recursos, intensidade, recortes, sem_recorte, sem_acabamento}]}."""
    import shutil
    import qa_conjunto
    pasta = Path(pasta).resolve()
    k = json.loads((pasta / "mediakit.json").read_text(encoding="utf-8"))
    receita, plano = _plano_horizontal(pasta, receita)
    dc = k.get("direcao_criativa") if isinstance(k.get("direcao_criativa"), dict) else {}
    decl = {r.get("id"): r for r in dc.get("recursos") or [] if isinstance(r, dict)}
    teto = (dc.get("intensidade") or {}).get("teto") if isinstance(dc.get("intensidade"), dict) else None
    W, H = float(plano.get("largura", 1920)), float(plano.get("altura", 1080))
    pags = plano["paginas"]
    rasters, tmp = _rasters(pasta, receita, pdf, False, "horizontal")
    if len(rasters) < len(pags):
        raise SystemExit(f"{len(rasters)} páginas rasterizadas para {len(pags)} no plano: renderize com --png "
                         f"(ou use --pdf sobre o PDF entregue)")
    rep = Path(rep or RAIZ_REPERTORIO)
    indice = _indice_repertorio(rep)
    kx = CELULA / W
    th = round(H * kx)
    cw, gap, marg, leg_h, cap_h = 296, 12, 24, 64, 66
    largura = marg + CELULA + gap + 3 * cw + 2 * gap + marg
    S = Image.new("RGB", (largura, leg_h + len(pags) * (th + cap_h + marg) + marg), FUNDO_FOLHA)
    dr = ImageDraw.Draw(S)
    f14, f16 = fonte_ui(14), fonte_ui(16)
    x = marg
    for fam, cor in list(COR_FAMILIA.items()) + [("fora da direção criativa", COR_SEM_FAMILIA)]:
        dr.rectangle([x, 22, x + 18, 40], outline=_rgb(cor), width=3)
        dr.text((x + 24, 22), fam, fill=(235, 235, 235), font=f14)
        x += 34 + dr.textlength(fam, font=f14)
    dr.text((marg, 44), f"acabamento {receita}{' (PDF entregue)' if pdf else ''}: tinta de cada recurso na cor da família, e o "
            f"recorte do repertório de onde ele veio (copiar o princípio, nunca a forma)", fill=(150, 150, 150), font=f14)
    resumo = []
    for i, pg in enumerate(pags):
        y0 = leg_h + marg + i * (th + cap_h + marg)
        chave, ent, rids = recursos_da_pagina(pg, k)
        base = Image.open(rasters[min(len(rasters), pg.get("n", i + 1)) - 1]).convert("RGB").resize((CELULA, th), Image.LANCZOS)
        cam = Image.new("RGBA", (CELULA, th), (0, 0, 0, 0))
        d2 = ImageDraw.Draw(cam)
        for rid in rids:
            cor = COR_FAMILIA.get((decl.get(rid) or {}).get("familia"), COR_SEM_FAMILIA)
            for it in _itens_do_recurso(pg, rid):
                t = _tinta(it, pasta, pg)
                d2.rectangle([t[0] * kx, t[1] * kx, t[2] * kx, t[3] * kx], outline=_rgb(cor), width=3)
                d2.text((t[0] * kx + 4, t[1] * kx + 3), rid, fill=_rgb(cor), font=f14)
        S.paste(Image.alpha_composite(base.convert("RGBA"), cam).convert("RGB"), (marg, y0))
        xr = marg + CELULA + gap
        recs, sem = {}, []
        for j, rid in enumerate(rids[:3]):
            r = decl.get(rid) or {"id": rid}
            achados = recortes_da_origem(r, rep, indice, n=1)
            recs[rid] = [str(a[0]) for a in achados]
            if not achados:
                sem.append(rid)
            cor = COR_FAMILIA.get(r.get("familia"), COR_SEM_FAMILIA)
            _cartao_recorte(dr, S, xr + j * (cw + gap), y0, cw, th, achados[0] if achados else None,
                            f"{rid} · {r.get('familia') or 'fora da direção'}", cor, f14)
        sem_acab = bool(chave) and not isinstance(ent.get("acabamento"), dict)
        if not rids:
            msg = ("FALTA `acabamento` nesta página composta (o QA do mk-2.1 reprova)" if sem_acab else
                   "nenhum recurso de acabamento nesta página" + ("" if chave else " (página sem composição)"))
            for li, l in enumerate(_linhas(dr, msg, f16, 3 * cw, 3)):
                dr.text((xr, y0 + 12 + li * 22), l, fill=(230, 120, 120) if sem_acab else (170, 170, 170), font=f16)
        elif len(rids) > 3:
            dr.text((xr, y0 + th + 4), f"+{len(rids) - 3} recurso(s) além destes: {', '.join(rids[3:])}", fill=(230, 120, 120), font=f14)
        dec, calc = qa_conjunto.intensidade(ent, k)
        ac = ent.get("acabamento") if isinstance(ent.get("acabamento"), dict) else {}
        tit = (f"{pg.get('n', i + 1):02d}  {pg.get('rotulo', '?')}   intensidade {dec if dec is not None else '?'} "
               f"(calculada {calc}{f', teto {teto}' if teto is not None else ''})   profundidade {ac.get('profundidade', '-')}"
               f" · grão {ac.get('grao', '-')} · luz {ac.get('luz', '-')}")
        dr.text((marg, y0 + th + 6), tit, fill=(255, 120, 120) if (teto is not None and calc > teto) or calc > 3 else (240, 240, 240), font=f16)
        porque = ac.get("porque") or ("sem acabamento declarado" if chave else "página sem composição")
        for li, l in enumerate(_linhas(dr, f"porquê: {porque}", f14, CELULA, 2)):
            dr.text((marg, y0 + th + 28 + li * 18), l, fill=(170, 170, 170), font=f14)
        resumo.append({"n": pg.get("n", i + 1), "rotulo": pg.get("rotulo"), "chave": chave, "recursos": rids,
                       "intensidade": [dec, calc], "recortes": recs, "sem_recorte": sem, "sem_acabamento": sem_acab})
    out = Path(saida_arq) if saida_arq else pasta / "saida" / f"acabamento-{receita}{'-pdf' if pdf else ''}.png"
    S.save(out, optimize=True)
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
    print("OK", out, f"{len(pags)} páginas")
    return {"arquivo": str(out), "receita": receita, "paginas": resumo}


def estudo(pasta, rid, receita=None, saida_arq=None, rep=None):
    """Estudo A/B de um recurso (etapa 3b.4, para recurso novo, de intensidade 3 ou sob texto): A é o recorte do
    repertório de onde o recurso veio (até 3), B é cada página renderizada que o usa, inteira e com a tinta do recurso
    marcada, e o detalhe ampliado da região dele (legibilidade e matéria). Grava <kit>/estudos/<recurso>.png e devolve
    {arquivo, recurso, recortes, paginas, detalhes}. Recusa recurso fora de direcao_criativa.recursos, recurso sem
    recorte no repertório e recurso que nenhuma página renderizada usa: sem os dois lados não há comparação."""
    import qa_conjunto
    from caminhos import dentro_do_kit
    pasta = Path(pasta).resolve()
    if not ID_RECURSO.match(str(rid or "")):
        raise SystemExit(f"`{rid}` não é um id de recurso (minúsculas, números e hífen): vira nome de arquivo em estudos/")
    k = json.loads((pasta / "mediakit.json").read_text(encoding="utf-8"))
    dc = k.get("direcao_criativa") if isinstance(k.get("direcao_criativa"), dict) else {}
    rec = next((r for r in dc.get("recursos") or [] if isinstance(r, dict) and r.get("id") == rid), None)
    if rec is None:
        raise SystemExit(f"o recurso `{rid}` não está em direcao_criativa.recursos: o estudo é de um recurso escolhido na 3b.3")
    rep = Path(rep or RAIZ_REPERTORIO)
    recortes = recortes_da_origem(rec, rep, n=3)
    if not recortes:
        raise SystemExit(f"o recurso `{rid}` cita `{rec.get('referencia')}`, que não tem recorte no repertório: o estudo "
                         f"compara com o recorte; troque a referência pela que a consulta trouxe (consulta-repertorio.json)")
    receita, plano = _plano_horizontal(pasta, receita)
    pags = [pg for pg in plano["paginas"] if rid in recursos_da_pagina(pg, k)[2]]
    if not pags:
        raise SystemExit(f"nenhuma página do render {receita} usa `{rid}`: escreva o recurso na composição da página do "
                         f"estudo (só ela em `paginas`, como nas pilotos) e renderize com --png")
    W, H = float(plano.get("largura", 1920)), float(plano.get("altura", 1080))
    png = pasta / "saida" / "png"
    marg, gap = 24, 24
    kx = CELULA / W
    th = round(H * kx)
    largura = marg + 2 * CELULA + gap + marg
    f14, f16, f20 = fonte_ui(14), fonte_ui(16), fonte_ui(20)
    cor = COR_FAMILIA.get(rec.get("familia"), COR_SEM_FAMILIA)
    rascunho = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    cab = [f"estudo A/B: {rid} ({rec.get('familia') or 'sem família'}, rota {rec.get('rota') or '?'}"
           f"{', motivo ' + rec['motivo'] if rec.get('motivo') else ''})"]
    cab += _linhas(rascunho, f"princípio: {rec.get('principio') or '?'}", f16, largura - 2 * marg, 2)
    cab += _linhas(rascunho, f"não copiar: {rec.get('nao_copiar') or 'não declarado'}", f16, largura - 2 * marg, 2)
    cab_h = 34 + 22 * (len(cab) - 1) + 20
    ca_w = (largura - 2 * marg - 2 * gap) // 3
    ca_h = 420
    bloco_a = 30 + ca_h + 4
    linha_b = 30 + th + 52
    S = Image.new("RGB", (largura, cab_h + bloco_a + marg + len(pags) * (linha_b + marg) + marg), FUNDO_FOLHA)
    dr = ImageDraw.Draw(S)
    dr.text((marg, 14), cab[0], fill=_rgb(cor), font=f20)
    for i, l in enumerate(cab[1:]):
        dr.text((marg, 44 + i * 22), l, fill=(220, 220, 220), font=f16)
    y = cab_h
    dr.text((marg, y), f"A · origem no repertório ({rec.get('referencia')}): o princípio, nunca a forma; o recorte não entra no kit",
            fill=(240, 240, 240), font=f16)
    for j, rc in enumerate(recortes):
        _cartao_recorte(dr, S, marg + j * (ca_w + gap), y + 30, ca_w, ca_h, rc, rc[1], cor, f14)
    y += bloco_a + marg
    detalhes = []
    for pg in pags:
        chave, ent, _ = recursos_da_pagina(pg, k)
        n = pg.get("n", 1)
        arq = png / f"kit-{receita}-{n:02d}.png"
        if not arq.is_file():
            raise SystemExit(f"{arq.name} não existe: renderize com --png")
        pagina = Image.open(arq).convert("RGB")
        sx = pagina.width / W
        itens = _itens_do_recurso(pg, rid)
        if itens:
            ts = [_tinta(it, pasta, pg) for it in itens]
            x0, y0_, x1, y1 = min(t[0] for t in ts), min(t[1] for t in ts), max(t[2] for t in ts), max(t[3] for t in ts)
            folga = max(48.0, 0.2 * max(x1 - x0, y1 - y0_))
            reg = (max(0.0, x0 - folga), max(0.0, y0_ - folga), min(W, x1 + folga), min(H, y1 + folga))
            onde = "detalhe da região do recurso, ampliado"
        else:
            reg, onde = (0.0, 0.0, W, H), "recurso da página inteira (nenhum elemento declara este recurso)"
        detalhes.append({"n": n, "chave": chave, "regiao": [round(v) for v in reg]})
        thumb = pagina.resize((CELULA, th), Image.LANCZOS).convert("RGBA")
        cam = Image.new("RGBA", (CELULA, th), (0, 0, 0, 0))
        d2 = ImageDraw.Draw(cam)
        for it in itens:
            t = _tinta(it, pasta, pg)
            d2.rectangle([t[0] * kx, t[1] * kx, t[2] * kx, t[3] * kx], outline=_rgb(cor), width=3)
        if itens:
            _tracejado(d2, (reg[0] * kx, reg[1] * kx), (reg[2] * kx, reg[1] * kx), (255, 255, 255, 200))
            _tracejado(d2, (reg[2] * kx, reg[1] * kx), (reg[2] * kx, reg[3] * kx), (255, 255, 255, 200))
            _tracejado(d2, (reg[2] * kx, reg[3] * kx), (reg[0] * kx, reg[3] * kx), (255, 255, 255, 200))
            _tracejado(d2, (reg[0] * kx, reg[3] * kx), (reg[0] * kx, reg[1] * kx), (255, 255, 255, 200))
        dec, calc = qa_conjunto.intensidade(ent, k)
        dr.text((marg, y), f"B · p.{n:02d} {pg.get('rotulo', '?')}: a página do kit, com a tinta de {rid}   intensidade "
                f"{dec if dec is not None else '?'} (calculada {calc})", fill=(240, 240, 240), font=f16)
        S.paste(Image.alpha_composite(thumb, cam).convert("RGB"), (marg, y + 30))
        corte = pagina.crop(tuple(round(v * sx) for v in reg))
        S.paste(_encaixar(corte, CELULA, th), (marg + CELULA + gap, y + 30))
        dr.text((marg + CELULA + gap, y + 30 + th + 4), onde, fill=(150, 150, 150), font=f14)
        ac = ent.get("acabamento") if isinstance(ent.get("acabamento"), dict) else {}
        for li, l in enumerate(_linhas(dr, f"porquê: {ac.get('porque') or 'sem acabamento declarado'}", f14, CELULA, 2)):
            dr.text((marg, y + 30 + th + 4 + li * 18), l, fill=(170, 170, 170), font=f14)
        y += linha_b + marg
    out = Path(saida_arq) if saida_arq else dentro_do_kit(pasta, f"estudos/{rid}.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    S.save(out, optimize=True)
    print("OK", out, f"{len(recortes)} recorte(s) do repertório, {len(pags)} página(s)")
    return {"arquivo": str(out), "recurso": rid, "recortes": [str(r[0]) for r in recortes],
            "paginas": [pg.get("rotulo") for pg in pags], "detalhes": detalhes}


# ------------------------------------------------------------------------------------------------- antes e depois, escolha cega
# A prova para o dono cético (references/10, "Prova para dono cético"): a mesma página do kit anterior e do novo lado a
# lado, com o recorte do recurso principal; e a escolha cega, pares sem rótulo de versão com a ordem sorteada pela
# semente e a chave gravada à parte (o sha256 dela é impresso para ser registrado antes de qualquer juiz ver a folha).
# Nada é escrito na pasta do antes: as duas folhas vão para a saida/ do kit novo.
CEL_AD, CEL_CEGA, REC_AD = 640, 860, 300


class _Paginas:
    """Imagem de cada página de um kit: saida/png/kit-<receita>-NN.png do render; sem ele, a página do PDF entregue
    rasterizada pelo pdftoppm num diretório temporário (apagado em fechar())."""

    def __init__(self, pasta, receita, largura):
        self.pasta, self.receita, self.largura = Path(pasta), receita, largura
        self.tmp = None

    def imagem(self, n):
        png = self.pasta / "saida" / "png" / f"kit-{self.receita}-{n:02d}.png"
        if png.is_file():
            return Image.open(png)
        pdf = self.pasta / "saida" / f"kit-{self.receita}.pdf"
        if not pdf.is_file():
            return None
        if self.tmp is None:
            self.tmp = Path(tempfile.mkdtemp(prefix="folha-antes-"))
        alvo = self.tmp / f"p{n:02d}"
        subprocess.run(["pdftoppm", "-png", "-f", str(n), "-l", str(n), "-singlefile", "-scale-to-x", str(self.largura),
                        "-scale-to-y", "-1", str(pdf), str(alvo)], capture_output=True)
        return Image.open(alvo.with_suffix(".png")) if alvo.with_suffix(".png").is_file() else None

    def fechar(self):
        import shutil
        if self.tmp:
            shutil.rmtree(self.tmp, ignore_errors=True)


def parear(plano_depois, plano_antes):
    """[(página do depois ou None, página do antes ou None)] em ordem de página do depois; as páginas do antes que
    sobram vão no fim. Pareia em três passadas, cada uma só entre as que sobraram: a mesma chave de composição (a
    `cota:Master` com a `cota:Master`), o mesmo rótulo (arquétipo e variante) e a mesma posição. Uma página nova no
    meio não desloca o resto."""
    depois = sorted(plano_depois.get("paginas") or [], key=lambda p: p["n"])
    antes = sorted(plano_antes.get("paginas") or [], key=lambda p: p["n"])
    chave = lambda p: (p.get("composicao") or {}).get("chave")  # noqa: E731
    criterios = (lambda d, a: chave(d) is not None and chave(d) == chave(a),
                 lambda d, a: d.get("rotulo") is not None and d.get("rotulo") == a.get("rotulo"),
                 lambda d, a: d["n"] == a["n"])
    par, usados = {}, set()
    for crit in criterios:
        for d in depois:
            if d["n"] in par:
                continue
            a = next((a for a in antes if a["n"] not in usados and crit(d, a)), None)
            if a is not None:
                par[d["n"]] = a
                usados.add(a["n"])
    return [(d, par.get(d["n"])) for d in depois] + [(None, a) for a in antes if a["n"] not in usados]


def _dois_kits(pasta, antes, receita=None, receita_antes=None):
    """(pasta, kit, receita, plano, pasta_antes, kit_antes, receita_antes, plano_antes, avisos) do kit novo e do anterior."""
    pasta, antes = Path(pasta).resolve(), Path(antes).resolve()
    if pasta == antes:
        raise SystemExit("o antes e o depois são a mesma pasta")
    k = json.loads((pasta / "mediakit.json").read_text(encoding="utf-8"))
    ka = json.loads((antes / "mediakit.json").read_text(encoding="utf-8"))
    receita, plano = _plano_horizontal(pasta, receita)
    receita_antes, plano_a = _plano_horizontal(antes, receita_antes)
    avisos = []
    na, nd = len(plano_a.get("paginas") or []), len(plano.get("paginas") or [])
    if na != nd:
        avisos.append(f"o antes tem {na} páginas e o depois {nd}: pareadas por composição, rótulo e posição; "
                      f"a que sobra sai sem par")
    return pasta, k, receita, plano, antes, ka, receita_antes, plano_a, avisos


def _celula_vazia(dr, S, x, y, w, h, texto, f16):
    dr.rectangle([x, y, x + w, y + h], fill=FUNDO_CELULA, outline=(90, 90, 90))
    dr.text((x + 16, y + 16), texto, fill=(170, 170, 170), font=f16)


def folha_antes_depois(pasta, antes, receita=None, receita_antes=None, saida_arq=None, rep=None):
    """Por página: a do kit anterior, a do kit novo e o recorte do repertório do recurso principal da página nova (o
    primeiro recurso dela), com o rótulo; embaixo, a linha dos recursos (com a família) e a da intensidade (declarada e
    calculada) dos dois. Grava saida/antes-depois-<receita>.png no kit novo e devolve {arquivo, receita, receita_antes,
    pares: [{depois, antes, recurso, recorte, caixas: {antes, depois, recorte}}], avisos}; caixas em px da folha."""
    import medir_kit
    pasta, k, receita, plano, antes, ka, receita_a, plano_a, avisos = _dois_kits(pasta, antes, receita, receita_antes)
    for a in avisos:
        print("AVISO ", a)
    info = {p["n"]: p for p in medir_kit.paginas(plano, k)}
    info_a = {p["n"]: p for p in medir_kit.paginas(plano_a, ka)}
    acab_a = medir_kit._declara(ka)
    decl = medir_kit.recursos_declarados(k)
    decl_a = medir_kit.recursos_declarados(ka)
    pares = parear(plano, plano_a)
    W, H = float(plano.get("largura", 1920)), float(plano.get("altura", 1080))
    th = round(H * CEL_AD / W)
    marg, gap, leg_h, cap_h = 24, 12, 64, 74
    largura = marg + 2 * (CEL_AD + gap) + REC_AD + marg
    S = Image.new("RGB", (largura, leg_h + len(pares) * (th + cap_h + marg) + marg), FUNDO_FOLHA)
    dr = ImageDraw.Draw(S)
    f14, f16 = fonte_ui(14), fonte_ui(16)
    dr.text((marg, 14), f"antes e depois: {antes.name} ({receita_a}) e {pasta.name} ({receita})", fill=(240, 240, 240), font=f16)
    dr.text((marg, 40), "coluna 1: antes · coluna 2: depois · coluna 3: recorte do recurso principal da página nova "
            "(o princípio, nunca a forma)", fill=(150, 150, 150), font=f14)
    rep = Path(rep or RAIZ_REPERTORIO)
    indice = _indice_repertorio(rep)
    pg_d, pg_a = _Paginas(pasta, receita, CEL_AD), _Paginas(antes, receita_a, CEL_AD)

    def rec_txt(p, dc):
        if not p or not p["recursos"]:
            return "-"
        return ", ".join(f"{r} ({(dc.get(r) or {}).get('familia') or 'fora da direção'})" for r in p["recursos"])

    def int_txt(p, declara):
        if not p or not declara:
            return "-"
        dec, calc = p["intensidade"]
        return f"{dec if dec is not None else '?'} (calculada {calc})"

    resumo = []
    try:
        for i, (d, a) in enumerate(pares):
            y0 = leg_h + marg + i * (th + cap_h + marg)
            for col, (lado, kit_pg, nome) in enumerate(((a, pg_a, "antes"), (d, pg_d, "depois"))):
                x = marg + col * (CEL_AD + gap)
                im = kit_pg.imagem(lado["n"]) if lado else None
                if im is not None:
                    S.paste(_encaixar(im, CEL_AD, th), (x, y0))
                else:
                    _celula_vazia(dr, S, x, y0, CEL_AD, th, f"sem página no {nome}" if not lado else
                                  f"p.{lado['n']:02d} sem PNG nem PDF no {nome}", f16)
            xr = marg + 2 * (CEL_AD + gap)
            pd = info.get(d["n"]) if d else None
            rid = pd["recursos"][0] if pd and pd["recursos"] else None
            achado = None
            if rid:
                r = decl.get(rid) or {"id": rid}
                achados = recortes_da_origem(r, rep, indice, n=1)
                achado = achados[0] if achados else None
                _cartao_recorte(dr, S, xr, y0, REC_AD, th, achado, f"{rid} · {r.get('familia') or 'fora da direção'}",
                                COR_FAMILIA.get(r.get("familia"), COR_SEM_FAMILIA), f14)
            else:
                _celula_vazia(dr, S, xr, y0, REC_AD, th - 44, "sem recurso de acabamento", f14)
            pa = info_a.get(a["n"]) if a else None
            t1 = (f"depois p.{d['n']:02d} {d.get('rotulo', '?')}" if d else "sem página no depois") + "   ·   " + \
                 (f"antes p.{a['n']:02d} {a.get('rotulo', '?')}" if a else "sem página no antes")
            dr.text((marg, y0 + th + 6), t1, fill=(240, 240, 240), font=f16)
            dr.text((marg, y0 + th + 30), _uma_linha(dr, f"recursos: depois {rec_txt(pd, decl)}   |   antes {rec_txt(pa, decl_a)}",
                                                      f14, largura - 2 * marg), fill=(190, 190, 190), font=f14)
            dr.text((marg, y0 + th + 50), f"intensidade: depois {int_txt(pd, medir_kit._declara(k))}   |   "
                    f"antes {int_txt(pa, acab_a)}", fill=(190, 190, 190), font=f14)
            resumo.append({"depois": d["n"] if d else None, "antes": a["n"] if a else None, "recurso": rid,
                           "recorte": str(achado[0]) if achado else None,
                           "caixas": {"antes": [marg, y0, marg + CEL_AD, y0 + th],
                                      "depois": [marg + CEL_AD + gap, y0, marg + 2 * CEL_AD + gap, y0 + th],
                                      "recorte": [xr, y0, xr + REC_AD, y0 + th]}})
    finally:
        pg_d.fechar(); pg_a.fechar()
    out = Path(saida_arq) if saida_arq else pasta / "saida" / f"antes-depois-{receita}.png"
    S.save(out, optimize=True)
    print("OK", out, f"{len(pares)} linha(s), {sum(1 for d, a in pares if d and a)} par(es)")
    return {"arquivo": str(out), "receita": receita, "receita_antes": receita_a, "pares": resumo, "avisos": avisos}


def _selo(dr, x, y, letra, f20):
    dr.rectangle([x, y, x + 40, y + 36], fill=(245, 245, 245))
    dr.text((x + 12, y + 6), letra, fill=(18, 18, 20), font=f20)


def escolha_cega(pasta, antes, semente, receita=None, receita_antes=None, saida_arq=None):
    """Pares lado a lado (as páginas pareadas como na folha antes e depois; só os pares completos), cada um com a ordem
    esquerda e direita sorteada pela semente e rotulado só A e B. Grava saida/escolha-cega.png e, à parte,
    saida/escolha-cega-chave.json (par: qual lado é o antes e qual é o depois, as páginas, a semente e o sha256 da folha)
    e imprime o sha256 da chave, para registrar antes de qualquer juiz. Mesma semente, mesma chave; outra semente, outra.
    Devolve {arquivo, chave, sha256_chave, pares, caixas (A e B de cada par, em px da folha), avisos}."""
    import hashlib, random
    if semente is None:
        raise SystemExit("--cega pede --semente N: a ordem dos pares sai dela, e quem registra a semente refaz a folha")
    pasta, k, receita, plano, antes, ka, receita_a, plano_a, avisos = _dois_kits(pasta, antes, receita, receita_antes)
    for a in avisos:
        print("AVISO ", a)
    todos = parear(plano, plano_a)
    pares = [(d, a) for d, a in todos if d and a]
    if not pares:
        raise SystemExit("nenhum par de páginas entre o antes e o depois")
    rng = random.Random(int(semente))
    a_e_antes = [rng.random() < 0.5 for _ in pares]
    W, H = float(plano.get("largura", 1920)), float(plano.get("altura", 1080))
    th = round(H * CEL_CEGA / W)
    marg, gap, rot_h, leg_h = 24, 16, 34, 60
    S = Image.new("RGB", (marg + 2 * CEL_CEGA + gap + marg, leg_h + len(pares) * (rot_h + th + marg) + marg), FUNDO_FOLHA)
    dr = ImageDraw.Draw(S)
    f16, f20 = fonte_ui(16), fonte_ui(20)
    dr.text((marg, 14), "escolha cega: em cada par, qual página é melhor, A ou B? (a chave está gravada à parte)",
            fill=(240, 240, 240), font=f20)
    pg_d, pg_a = _Paginas(pasta, receita, CEL_CEGA), _Paginas(antes, receita_a, CEL_CEGA)
    chave_pares, caixas = [], []
    try:
        for i, ((d, a), antes_em_a) in enumerate(zip(pares, a_e_antes), 1):
            y0 = leg_h + marg + (i - 1) * (rot_h + th + marg)
            dr.text((marg, y0), f"par {i:02d}", fill=(240, 240, 240), font=f20)
            lados = ((a, pg_a), (d, pg_d)) if antes_em_a else ((d, pg_d), (a, pg_a))
            for col, ((pg, fonte), letra) in enumerate(zip(lados, "AB")):
                x = marg + col * (CEL_CEGA + gap)
                im = fonte.imagem(pg["n"])
                if im is not None:
                    S.paste(_encaixar(im, CEL_CEGA, th), (x, y0 + rot_h))
                else:
                    _celula_vazia(dr, S, x, y0 + rot_h, CEL_CEGA, th, "sem imagem", f16)
                _selo(dr, x + 10, y0 + rot_h + 10, letra, f20)
            chave_pares.append({"par": i, "A": "antes" if antes_em_a else "depois", "B": "depois" if antes_em_a else "antes",
                                "pagina_antes": a["n"], "pagina_depois": d["n"]})
            caixas.append({"A": [marg, y0 + rot_h, marg + CEL_CEGA, y0 + rot_h + th],
                           "B": [marg + CEL_CEGA + gap, y0 + rot_h, marg + 2 * CEL_CEGA + gap, y0 + rot_h + th]})
    finally:
        pg_d.fechar(); pg_a.fechar()
    out = Path(saida_arq) if saida_arq else pasta / "saida" / "escolha-cega.png"
    S.save(out, optimize=True)
    chave = {"semente": int(semente), "imagem": out.name, "imagem_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
             "antes": {"kit": antes.name, "pasta": str(antes), "receita": receita_a},
             "depois": {"kit": pasta.name, "pasta": str(pasta), "receita": receita},
             "pares": chave_pares,
             "sem_par": [{"pagina_antes": a["n"]} if a else {"pagina_depois": d["n"]} for d, a in todos if not (d and a)]}
    arq_chave = out.with_name(out.stem + "-chave.json")
    arq_chave.write_text(json.dumps(chave, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    sha = hashlib.sha256(arq_chave.read_bytes()).hexdigest()
    print("OK", out, f"{len(pares)} par(es), semente {semente}")
    print(f"chave {arq_chave} sha256 {sha}: registre este sha256 antes de mostrar a folha a qualquer juiz")
    return {"arquivo": str(out), "chave": str(arq_chave), "sha256_chave": sha, "pares": chave_pares, "caixas": caixas,
            "avisos": avisos}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta"); ap.add_argument("--direcao", default=None); ap.add_argument("--receita", default=None); ap.add_argument("--regua", default=None)
    ap.add_argument("--n-ref", type=int, default=2); ap.add_argument("--saida", default=None)
    ap.add_argument("--composicao", action="store_true", help="folha de composição: tinta, função, alvo de cada restrição")
    ap.add_argument("--pdf", action="store_true", help="com --composicao ou --acabamento: desenha sobre o raster do PDF entregue")
    ap.add_argument("--maquete", action="store_true", help="com --composicao: o plano e os PNGs da maquete")
    ap.add_argument("--vertical", action="store_true", help="com --composicao: o formato vertical")
    ap.add_argument("--acabamento", action="store_true", help="folha de acabamento: página x recortes dos recursos usados (etapa 9)")
    ap.add_argument("--estudo", default=None, metavar="RECURSO",
                    help="estudo A/B: recorte do repertório x página renderizada (etapa 3b.4); grava estudos/<recurso>.png")
    ap.add_argument("--antes", default=None, metavar="PASTA",
                    help="folha antes e depois contra o kit anterior: saida/antes-depois-<receita>.png")
    ap.add_argument("--cega", default=None, metavar="PASTA",
                    help="escolha cega contra o kit anterior (pede --semente): saida/escolha-cega.png e a chave à parte")
    ap.add_argument("--semente", type=int, default=None, help="com --cega: sorteia a ordem A e B de cada par")
    ap.add_argument("--receita-antes", default=None, help="com --antes ou --cega: a receita do kit anterior")
    a = ap.parse_args()
    if a.cega:
        escolha_cega(a.pasta, a.cega, a.semente, a.receita, a.receita_antes, a.saida)
        return
    if a.antes:
        folha_antes_depois(a.pasta, a.antes, a.receita, a.receita_antes, a.saida)
        return
    if a.estudo:
        estudo(a.pasta, a.estudo, a.receita, a.saida)
        return
    if a.acabamento:
        folha_acabamento(a.pasta, a.receita, a.pdf, a.saida)
        return
    if a.composicao:
        folha_composicao(a.pasta, a.receita, a.pdf, a.maquete, a.saida, "vertical" if a.vertical else "horizontal")
        return
    pasta = Path(a.pasta).resolve(); saida = pasta / "saida"
    rep = json.loads((saida / "render-report.json").read_text(encoding="utf-8"))
    d = a.receita or a.direcao or list(rep["direcoes"].keys())[0]
    if d not in rep["direcoes"]:
        raise SystemExit(f"`{d}` não está no render-report (renderizadas: {', '.join(rep['direcoes'])})")
    md = rep["direcoes"][d]
    seq = md.get("sequencia") or rep["sequencia"]; png = saida / "png"
    variantes = [p.get("variante", "a") for p in md.get("paginas", [])]
    tom = md.get("tom") or d
    pags = sorted(png.glob(f"kit-{d}-??.png")) or sorted(png.glob(f"kit-{d}-??.jpg"))
    regua = Path(a.regua).resolve() if a.regua else None
    nref = a.n_ref if regua else 0
    tw, th = (400, 225) if regua else (480, 270)
    cols = 2 if regua else 4
    cell_w = tw * (1 + nref) + 12 * nref + 36
    rows = (len(pags) + cols - 1) // cols
    S = Image.new("RGB", (cols * cell_w + 24, rows * (th + 60) + 24), (18, 18, 20))
    dr = ImageDraw.Draw(S); f = fonte_ui(16)
    vistos = {}
    for i, p in enumerate(pags):
        x = 24 + (i % cols) * cell_w; y = 24 + (i // cols) * (th + 60)
        S.paste(Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS), (x, y))
        tipo = seq[i] if i < len(seq) else "?"
        var = variantes[i] if i < len(variantes) else "a"
        dr.text((x, y + th + 8), f"{i+1:02d}  {tipo}" + (f" ({var})" if var != "a" else ""), fill=(240, 240, 240), font=f)
        if not regua:
            continue
        refs = referencias(regua, tipo, tom=tom, n=nref, vez=vistos.get(tipo, 0)); vistos[tipo] = vistos.get(tipo, 0) + 1
        rv = VARIANTE_REF.get((tipo, var))
        if rv and (regua / "paginas" / f"{rv}.jpg").exists():
            refs = [(regua / "paginas" / f"{rv}.jpg", f"{rv} (variante {var})")] + [r for r in refs if r[1] != rv]
        if not refs and (regua / f"{tipo}.png").exists():
            refs = [(regua / f"{tipo}.png", "régua")]
        for j in range(nref):
            rx = x + (tw + 12) * (j + 1)
            if j < len(refs):
                S.paste(Image.open(refs[j][0]).convert("RGB").resize((tw, th), Image.LANCZOS), (rx, y))
                dr.text((rx, y + th + 8), refs[j][1], fill=(150, 150, 150), font=f)
            else:
                dr.rectangle([rx, y, rx + tw, y + th], outline=(70, 70, 70))
                dr.text((rx + 12, y + 12), "sem referência para este tipo", fill=(120, 120, 120), font=f)
    out = Path(a.saida) if a.saida else saida / f"contact-{d}.png"
    S.save(out); print("OK", out, f"{len(pags)} páginas")


if __name__ == "__main__":
    main()

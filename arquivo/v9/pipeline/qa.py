#!/usr/bin/env python3
"""
qa.py v2: conferência do mídia kit. Barra, não avisa: sai com código 1 em qualquer FALHA.

Uso: python3 qa.py <pasta-do-cliente> [--ledger memoria-mediakit/historico-kits.json]
Com `receitas`, confere cada kit-<id> e também se as receitas são diferentes entre si e do histórico (frente 4).
Lê mediakit.json e, se existir, saida/render-report.json. Regras em memoria-mediakit/gramatica.md e references/04-qa-e-entrega.md.
Aceita mk-2.0 e mk-2.1. A camada de acabamento (mk-2.1, references/10-acabamento.md, seção QA) só é conferida em kit que
a declara: falhas e avisos do acabamento.validar, as regras do qa_conjunto.checar_acabamento, o formato_base contra o
formato (formato.conferir: diferença do travado é aviso) e as imagens por página do PDF (validar_pdf --imagens-esperadas).
O PDF vertical vai ao validar_pdf.py em todo kit que gera vertical (desde 12/10/2026). Kit só horizontal (`paginas` sem
página vertical e sem render-report, ou render-report sem `vertical`): acabamento.gera_vertical; as composicao `vertical:*`
saem das regras do acabamento e o PDF vertical não é cobrado.
"""
import json, re, sys
from pathlib import Path

VERSOES = ("mk-2.0", "mk-2.1")          # mk-2.1 = mk-2.0 + camada de acabamento opcional (references/10-acabamento.md)
TIPOS = {"realizado", "informado", "meta", "projecao", "proxy"}
FUNCOES = {"capa", "manifesto", "projecao", "publico", "historico", "local", "ativo", "cotas", "cota", "contato", "lettering", "logo", "simbolo", "logo_patrocinador", "acento"}
SEM_ACENTO = {"nao": "não", "voce": "você", "patrocinio": "patrocínio", "midia": "mídia", "edicao": "edição", "inscricao": "inscrição", "inscricoes": "inscrições", "publico": "público", "numero": "número", "proposito": "propósito", "atencao": "atenção", "portico": "pórtico", "hidratacao": "hidratação", "relatorio": "relatório", "tambem": "também", "apos": "após", "camera": "câmera", "video": "vídeo", "area": "área", "familia": "família", "proximo": "próximo", "valido": "válido", "ultimo": "último", "unico": "único", "experiencia": "experiência", "ativacao": "ativação", "projecao": "projeção", "divulgacao": "divulgação", "oficial": None}
CODIGOS = {"grupo", "tipo", "funcao", "direcao", "aprovada_por", "schema_version", "id", "foco", "prova_id", "logo_id", "cena_id", "foto_id", "mini_id", "icone", "icones", "layout", "fonte", "arquivo", "email", "canal", "credito"}

falhas, avisos = [], []
F = falhas.append; A = avisos.append


def textos(obj, caminho=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from textos(v, f"{caminho}.{k}" if caminho else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from textos(v, f"{caminho}[{i}]")
    elif isinstance(obj, str):
        yield caminho, obj


def codigo_de_elementos(caminho):
    """sistema_elementos é código (ids, cores hex, estilo em inglês para o gerador de imagem), menos o texto das constantes,
    que vira texto vivo na página e passa pelas mesmas conferências do resto do kit."""
    return caminho.startswith("sistema_elementos") and not re.match(r"sistema_elementos\.constantes\[\d+\]\.texto$", caminho)


PROSA_COMPOSICAO = {"mensagem", "estrutura", "porque", "porque_fora_da_gramatica"}
PROSA_DIRECAO = {"principio", "nao_copiar", "porque_repete"}
# ids e carimbos, não texto: `paginas` lista tipos de página (`publico`, `ativo_painel`) e `formato_base` é id e sha256.
# Falso positivo do kit de prova do acabamento (12/10): "paginas[5]: `publico` sem acento"
SO_CODIGO = re.compile(r"^(paginas|formato_base)(\[|\.|$)")


def checar_textos(k):
    """Acento e travessão no texto do kit. `composicao` e `direcao_criativa` são planejamento, não texto de página:
    usam vocabulário fechado sem acento (`numero`, `titulo`, `tipografia-expressiva`) e ids, e só a prosa delas
    (mensagem, estrutura, porquê, princípio, o que não copiar) passa pelo travessão, que vale em tudo que o dono lê.
    `paginas` e `formato_base` são ids: ficam fora."""
    for caminho, t in textos(k):
        ult = caminho.split(".")[-1].split("[")[0]
        if caminho.startswith("composicao"):
            if ult in PROSA_COMPOSICAO and ("—" in t or "–" in t):
                F(f"{caminho}: travessão/meia-risca na composição")
            continue
        if caminho.startswith("direcao_criativa"):
            if ult in PROSA_DIRECAO and ("—" in t or "–" in t):
                F(f"{caminho}: travessão/meia-risca na direção criativa")
            continue
        if SO_CODIGO.match(caminho):
            continue
        if ult in CODIGOS or caminho.startswith(("acervo", "receitas", "elementos")) or codigo_de_elementos(caminho): continue
        if "—" in t or "–" in t: F(f"{caminho}: travessão/meia-risca no texto do kit")
        for palavra in re.findall(r"[A-Za-zÀ-ÿ]+", t):
            certa = SEM_ACENTO.get(palavra.lower())
            if certa: F(f"{caminho}: `{palavra}` sem acento (`{certa}`)")


def numeros(t):
    for m in re.finditer(r"(?<![\w.,])(\d{1,3}(?:\.\d{3})+|\d{3,})(?![\w.,%])", t):
        yield int(m.group(1).replace(".", ""))


def mapa_cmaps(fontes_dir):
    """família → {peso ou None: conjunto de códigos do cmap}. Mesma regra do render.py: `Familia__700.ttf` é o peso 700."""
    mapa = {}
    if not fontes_dir or not Path(fontes_dir).exists():
        return mapa
    from fontTools.ttLib import TTFont
    for f in sorted(Path(fontes_dir).iterdir()):
        if f.suffix.lower() not in (".otf", ".ttf", ".woff2", ".woff"): continue
        fam, _, peso = f.stem.partition("__")
        try: cmap = set(TTFont(f, lazy=True).getBestCmap() or {})
        except Exception as e: A(f"fonte {f.name}: cmap não lido ({e})"); continue
        mapa.setdefault(fam, {})[int(peso) if peso.isdigit() else None] = cmap
    return mapa


def glifos_faltando(entrada, mapa):
    """Caracteres do texto que não existem no arquivo da família declarada (o navegador troca de fonte em silêncio)."""
    arquivos = mapa.get(entrada["familia"])
    if not arquivos: return None  # família fora de --fontes: a checagem de fallback (document.fonts) cuida
    cmap = arquivos.get(entrada["peso"]) or arquivos.get(None) or next(iter(arquivos.values()))
    falta = {}
    for t in entrada["textos"]:
        for ch in t:
            if ch.isspace() or ord(ch) in (0xAD, 0x200B, 0x200C, 0x200D, 0xFEFF): continue
            if ord(ch) not in cmap: falta.setdefault(ch, t)
    return falta


# ---------------------------------------------------------------------------------------------------------------
# Frente 4: receitas, ornamentos, pattern e histórico
# ---------------------------------------------------------------------------------------------------------------
EIXOS = ("display", "corpo", "paleta.marca", "fundo", "mascara", "pattern", "variante de capa")


def eixos_receita(r):
    f, v = r.get("fontes") or {}, r.get("variantes") or {}
    return {"display": f.get("display"), "corpo": f.get("corpo"), "paleta.marca": ((r.get("paleta") or {}).get("marca") or "").upper(),
            "fundo": r.get("fundo", "escuro"), "mascara": r.get("mascara", "reto"), "pattern": r.get("pattern"), "variante de capa": v.get("capa", "a")}


def checar_receitas(receitas, k):
    """(a) Duas receitas do mesmo kit que coincidem em mais de 2 dos 7 eixos são a mesma receita com outra roupa: reprova."""
    ids = [r.get("id") for r in receitas]
    for i in set(x for x in ids if ids.count(x) > 1): F(f"receita `{i}` duplicada")
    if len(receitas) > 3: A(f"{len(receitas)} receitas; o kit apresenta até 3")
    for r in receitas:
        if r.get("fundo", "escuro") not in ("escuro", "papel", "cor"): F(f"receita `{r.get('id')}`: fundo `{r.get('fundo')}` inválido")
        if r.get("mascara", "reto") not in ("reto", "diagonal", "arredondado", "sangria"): F(f"receita `{r.get('id')}`: máscara `{r.get('mascara')}` inválida")
        if r.get("pattern") and r["pattern"] not in {e.get("id") for e in k.get("elementos", []) if e.get("papel") == "pattern"}:
            F(f"receita `{r.get('id')}`: pattern `{r['pattern']}` não é um elemento papel pattern")
    for i in range(len(receitas)):
        for j in range(i + 1, len(receitas)):
            a, b = eixos_receita(receitas[i]), eixos_receita(receitas[j])
            iguais = [e for e in EIXOS if a[e] == b[e]]
            if len(iguais) > 2:
                F(f"receitas `{receitas[i].get('id')}` e `{receitas[j].get('id')}` parecidas demais: coincidem em {len(iguais)} de 7 eixos ({', '.join(iguais)}); o limite é 2")


def checar_camadas(d, m, pags):
    """(b) até 2 ornamentos por página; (c) ornamento na frente sobre título; (e) variante de ativo repetida em sequência."""
    for p in pags:
        n = p["pagina"]; orns = p.get("ornamentos", [])
        if len(orns) > 2: F(f"{d} p.{n}: {len(orns)} ornamentos ({', '.join(str(o.get('id')) for o in orns)}); limite 2 por página")
        for o in orns:
            if o.get("camada") != "frente": continue
            for t in p.get("titulos", []):
                ix = max(0, min(o["x"] + o["w"], t["x"] + t["w"]) - max(o["x"], t["x"]))
                iy = max(0, min(o["y"] + o["h"], t["y"] + t["h"]) - max(o["y"], t["y"]))
                area_t = max(1.0, t["w"] * t["h"])
                if ix * iy / area_t > 0.15:
                    F(f"{d} p.{n}: ornamento `{o.get('id')}` na frente cobre {ix * iy / area_t:.0%} do título {t['texto'][:30]!r}; limite 15%")
    ant = None
    for p in m.get("paginas", []) or []:
        if p["tipo"] in ("ativo_painel", "ativo_topo"):
            v = p["tipo"] + ":" + p.get("variante", "a")
            if v == ant: A(f"{d} p.{p['n']}: variante de ativo `{p['tipo'] if p['tipo'] == 'ativo_topo' else p.get('variante', 'a')}` repetida em sequência (guia C: variedade)")
            ant = v
        else:
            ant = None


def ledger_path():
    if "--ledger" in sys.argv:
        return Path(sys.argv[sys.argv.index("--ledger") + 1])
    return Path(__file__).resolve().parent.parent / "memoria-mediakit" / "historico-kits.json"


def checar_ledger(receitas, k, caminho):
    """(f) contra o histórico: par display+corpo ou variante de capa que repete um dos 3 últimos kits avisa."""
    if not receitas or not caminho.exists(): return
    try: hist = json.loads(caminho.read_text(encoding="utf-8"))
    except Exception as e: A(f"histórico de kits não lido ({e})"); return
    if isinstance(hist, dict): hist = hist.get("kits", [])
    nome = ((k.get("evento") or {}).get("nome") or "").strip().lower()
    # o próprio kit sai da comparação: o histórico grava o evento com edição e data ("Sprint Ubatuba Run 2027 (2ª
    # edição...)"), então a igualdade exata nunca casava e o kit se comparava consigo mesmo
    proprio = lambda h: bool(nome) and nome in str(h.get("evento") or h.get("nome") or "").lower()
    outros = [h for h in hist if isinstance(h, dict) and not proprio(h)]
    if outros and all(h.get("data") for h in outros): outros = sorted(outros, key=lambda h: h["data"])
    ultimos = outros[-3:]
    for r in receitas:
        e = eixos_receita(r)
        for h in ultimos:
            rotulo = h.get("evento") or h.get("nome") or "?"
            for hr in h.get("receitas", []) or []:
                f = hr.get("fontes") or {}
                if isinstance(f, (list, tuple)):
                    # formato antigo do histórico: [display, corpo] (a entrada da Sprint derrubava o qa.py inteiro)
                    f = {"display": f[0] if f else None, "corpo": f[1] if len(f) > 1 else None}
                if (f.get("display"), f.get("corpo")) == (e["display"], e["corpo"]):
                    A(f"receita `{r.get('id')}`: par {e['display']} + {e['corpo']} repete o kit `{rotulo}` (um dos 3 últimos)")
                if ((hr.get("variantes") or {}).get("capa") or "a") == e["variante de capa"]:
                    A(f"receita `{r.get('id')}`: capa variante {e['variante de capa']} repete o kit `{rotulo}` (um dos 3 últimos)")


# onde a marca aparece (regra 10). Nasceu nos kits de corrida; o kit da A.M.E (09/10) somou as posições do futebol, da
# transmissão e do digital: camisa, tela, app, feed, campo, palco
POSICAO = re.compile(r"\(|lateral|costas|manga|testeira|frente|superior|inferior|arena|kit|perfil|e-mail|relat|estande|"
                     r"pórtico|hidrata|backdrop|site|stories|post|nome|título|placa|bandeira|telão|locu|"
                     r"peito|camisa|uniforme|tela\b|transmiss|\bapp\b|rodapé|feed|@|janela|vinheta|panfleto|"
                     r"beira|campo|palco|entrada", re.I)


def tem_posicao(entregavel):
    return bool(POSICAO.search(entregavel or ""))


SAFE = 96                               # a margem do render (JS do render.py): a área útil é a página menos ela
FOCO_ELEMENTO = ("grafico", "objeto")


def tinta_do_foco(pasta, k, rid):
    """{página: fração da área útil} da tinta do herói da composição nas páginas cuja composição declara o foco no gráfico
    ou no objeto. O dominante é medido no DOM sobre texto e foto (elemento é camada e não conta), mas quando a composição
    diz que o foco É o elemento (o mapa do território), a tinta dele entra na conta. Teste da AME, 09/10."""
    plano_p = Path(pasta) / "saida" / f"plano-elementos-{rid}.json"
    comp = k.get("composicao") or {}
    if not comp or not plano_p.exists():
        return {}
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import composicao
    plano = json.loads(plano_p.read_text(encoding="utf-8"))
    W, H = plano.get("largura") or 1920, plano.get("altura") or 1080
    util = (W - 2 * SAFE) * (H - 2 * SAFE)
    out = {}
    for pg in plano.get("paginas", []):
        _, ent, _, _ = composicao.entrada_da_pagina(comp, set(pg.get("rotulos") or []), pg.get("rotulo"), pg.get("tipo"), "horizontal")
        if not ent or ent.get("foco") not in FOCO_ELEMENTO:
            continue
        herois = {e.get("id") for e in ent.get("elementos") or [] if e.get("papel") == "heroi"}
        for it in pg.get("elementos", []):
            t = (it.get("ancora") or {}).get("tinta")
            if it.get("papel") == "heroi" and t and any(it["id"] == h or it["id"].startswith(f"{h}-p") for h in herois):
                out[pg["n"]] = max(out.get(pg["n"], 0), (t[2] - t[0]) * (t[3] - t[1]) / util)
    return out


def dominante_com_foco(dom, seg, foco):
    """O maior e o segundo maior, com a tinta do elemento-foco da composição (quando houver) na disputa."""
    if not foco:
        return dom, seg
    a, b = sorted((dom, seg, foco), reverse=True)[:2]
    return a, b


def lum_wcag(rgb):
    """Luminância relativa (WCAG) de um array RGB em 0..1, por pixel."""
    import numpy as np
    c = np.where(rgb <= 0.03928, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def contraste_do_texto(L, t, pattern=False):
    """(razão, mínimo) de uma caixa de texto do render-report (`textos` da página) sobre L, a luminância do PNG da
    página. Fundo: a cor do `bg` do texto, ou a mediana do anel de 6 px em volta da caixa; sobre pattern, o pior lado
    (percentis 10 e 90 do anel). Mínimo: 3:1 a partir de 24 px, senão 4,5:1; corpo sobre pattern, 4,5:1 até 36 px.
    None quando a caixa não se mede (abaixo de 14 px, sem cor, menor que 8 px, cor ilegível). O qa.py reprova abaixo do
    mínimo; o medir_kit.py lê a mesma conta (contraste mínimo por página)."""
    import numpy as np
    if t["fs"] < 14 or not t.get("cor"):
        return None
    H, W = L.shape[:2]
    x0, y0, x1, y1 = int(t["x"]), int(t["y"]), int(t["x"] + t["w"]), int(t["y"] + t["h"])
    x0, y0 = max(0, x0 - 6), max(0, y0 - 6); x1, y1 = min(W - 1, x1 + 6), min(H - 1, y1 + 6)
    if x1 - x0 < 8 or y1 - y0 < 8:
        return None
    if t.get("bg"):
        hb = t["bg"].lstrip("#"); bg = float(lum_wcag((np.array([int(hb[i:i + 2], 16) for i in (0, 2, 4)], dtype=float) / 255.0)[None, None, :])[0, 0])
    else:
        anel = np.concatenate([L[y0:y0 + 6, x0:x1].ravel(), L[y1 - 6:y1, x0:x1].ravel(), L[y0:y1, x0:x0 + 6].ravel(), L[y0:y1, x1 - 6:x1].ravel()])
        bg = float(np.median(anel))
        if pattern:
            # pattern é textura: a mediana esconde a listra. Vale o pior lado (percentil 10 ou 90 do anel)
            lo_, hi_ = float(np.percentile(anel, 10)), float(np.percentile(anel, 90))
    hexc = t["cor"].lstrip("#")
    try: rgb = np.array([int(hexc[i:i + 2], 16) for i in (0, 2, 4)], dtype=float) / 255.0
    except Exception: return None
    tl = float(lum_wcag(rgb[None, None, :])[0, 0])
    ratio = (max(tl, bg) + 0.05) / (min(tl, bg) + 0.05)
    minimo = 3.0 if t["fs"] >= 24 else 4.5
    if pattern and not t.get("bg"):
        pior = min((max(tl, x) + 0.05) / (min(tl, x) + 0.05) for x in (lo_, hi_))
        ratio = min(ratio, pior)
        # corpo sobre pattern: 4,5:1 mesmo a 24 px (só display e título ficam em 3:1)
        if "display" not in str(t.get("cls", "")) and t["fs"] <= 36: minimo = 4.5
    return ratio, minimo


def cmd_validar_pdf(pasta, k, r, d, vertical=False, acabamento=False):
    """A chamada do validar_pdf.py para o PDF da direção/receita `d` (None se o PDF não existe). Horizontal: a mesma de
    sempre. Vertical: página 1080x1920 e os textos que o DOM vertical mediu, sem conta de cenas (o pageplan é do
    horizontal). Kit com camada de acabamento: `--imagens-esperadas` com o HTML do render (imagens por página)."""
    sufixo = "-vertical" if vertical else ""
    pdf = pasta / "saida" / f"kit-{d}{sufixo}.pdf"
    if not pdf.exists():
        return None
    if vertical:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import acabamento as camada          # `acabamento` é o parâmetro booleano desta função
        if not camada.gera_vertical(k, r)[0]:
            return None                   # kit só horizontal: um vertical que sobrou de render antigo não é entrega
    rd = r["direcoes"][d]
    rec = (r.get("receitas") or {}).get(d)
    fx = (rec or {}).get("fontes") or {}
    esperadas = ",".join(dict.fromkeys(x for x in ([fx.get("display"), fx.get("corpo")] if rec else [k["marca"].get("fonte_display"), k["marca"].get("fonte_corpo")]) if x))
    cmd = [sys.executable, str(Path(__file__).parent / "validar_pdf.py"), str(pdf)]
    if vertical:
        cmd += ["--paginas", "1080x1920"]
    else:
        plano_d = (rd.get("pageplan") or r.get("pageplan", []))
        cmd += ["--cenas", str(sum(1 for p in plano_d if p["cena"]))]
    if esperadas: cmd += ["--fontes-esperadas", esperadas]
    # o nome do evento e a tese têm de sair como TEXTO no arquivo entregue (filtro, canvas e grafismo em PNG apagam)
    for alvo in ((k.get("evento") or {}).get("nome"), (k.get("tese") or {}).get("frase")):
        if alvo: cmd += ["--texto", alvo]
    if not vertical:
        # pattern ou textura de página inteira declarado no plano de elementos não é raster acidental
        plano_el = pasta / "saida" / f"plano-elementos-{d}.json"
        if plano_el.exists():
            pe_d = json.loads(plano_el.read_text(encoding="utf-8"))
            texturas = sum(1 for pg in pe_d.get("paginas", []) for e in pg.get("elementos", [])
                           if e.get("papel") == "pattern" and (e.get("w") or 0) * (e.get("h") or 0) >= 0.98 * 1920 * 1080)
            if texturas: cmd += ["--texturas", str(texturas)]
    # o texto de cada página do PDF tem de bater com o que o DOM mediu nela (título que virou imagem numa página só)
    por_pag = (rd.get("vertical" if vertical else "horizontal") or {}).get("por_pagina") or []
    if por_pag:
        arq_txt = pasta / "saida" / f"textos-por-pagina-{d}{sufixo}.json"
        arq_txt.write_text(json.dumps([[t.get("texto") or "" for t in (pg.get("textos") or [])] for pg in por_pag],
                                      ensure_ascii=False), encoding="utf-8")
        cmd += ["--por-pagina", str(arq_txt)]
    # camada de acabamento: imagens por página contra as que o HTML pede (rasterização silenciosa de efeito)
    html = pasta / "saida" / "html" / f"kit-{d}{sufixo}.html"
    if acabamento and html.exists():
        cmd += ["--imagens-esperadas", str(html)]
    return cmd


def checar_formato(pasta, k, raiz=None):
    """Kit com `formato_base`: diferença contra o `travado` do formato (formato.conferir) vira AVISO, porque o kit vence
    o formato (references/11): o aviso mostra o que se afastou para alguém decidir se foi de propósito. Lacuna `{...}`
    ainda aberta e formato que não se deixa conferir (não existe, sha256 do arquivo mudou) também avisam."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import formato
    fb = k.get("formato_base") or {}
    try:
        r = formato.conferir(pasta, raiz=raiz)
    except Exception as e:
        A(f"formato_base `{fb.get('id')}` v{fb.get('versao')} não conferido: {e}")
        return
    for av in r["avisos"]:
        A(f"formato {r['formato']}: {av}")
    for c, vf, vk in r["diferencas"]:
        A(f"formato {r['formato']}: `{c}` difere do travado (formato {formato._curto(vf)}; kit {formato._curto(vk)})")
    for c, txt in r["lacunas"]:
        A(f"formato {r['formato']}: lacuna aberta em `{c}`: {formato._curto(txt)}")


def checar_acabamento(pasta, k, indice=None, raiz_formatos=None):
    """Camada de acabamento (references/10-acabamento.md, seção QA). As FALHAS e os AVISOS do acabamento.validar chegam
    ao relatório (antes só as falhas que a composição decide sozinha chegavam, pelo plano); as regras do qa_conjunto
    (consulta, recursos, páginas, famílias, fio, histórico, intensidade e ritmo); e o formato_base contra o formato.
    Kit que não declara a camada (nem mk-2.1) não passa por nada disto."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import acabamento, qa_conjunto, qa_geometria
    if not qa_conjunto.declara_acabamento(k):
        return
    gera, por_que = acabamento.gera_vertical(k, acabamento.relatorio_da_pasta(pasta))
    if not gera:
        # kit só horizontal: as composicao `vertical:*` vêm da gramática do formato, mas não viram página. Sai uma linha
        # dizendo o que ficou de fora, para a omissão não ser silenciosa
        pulados = acabamento.chaves_vertical(k)
        if pulados:
            A(f"acabamento: {', '.join('composicao/' + c for c in pulados)} não conferida(s): o kit não gera vertical ({por_que})")
        k = acabamento.sem_vertical(k)
    fa, av = acabamento.validar(k)
    # as falhas que já saem do plano (composicao_erros, pelo qa_geometria) não repetem: as que a composição decide
    # sozinha e, desde que o camadas.py valida com o kit inteiro (frente R), também as que dependem do kit
    fc, _ = acabamento.validar({"composicao": k.get("composicao") or {}}, so_composicao=True)
    planos = qa_geometria.planos_da_pasta(pasta)
    tem_plano = bool(planos) and (pasta / "saida" / "render-report.json").exists()
    no_plano = set()
    for arq, _ in planos if tem_plano else ():
        try:
            no_plano |= set(json.loads(Path(arq).read_text(encoding="utf-8")).get("composicao_erros") or [])
        except (OSError, ValueError):
            pass
    for f in fa:
        if not (tem_plano and (f in fc or f in no_plano)):
            F(f"acabamento: {f}")
    for a in av:
        if not qa_conjunto.superado(a, k):
            A(f"acabamento: {a}")
    for nivel, msg in qa_conjunto.checar_acabamento(pasta, k, indice=indice, ledger=ledger_path()):
        (F if nivel == "FALHA" else A)(msg)
    if k.get("formato_base"):
        checar_formato(pasta, k, raiz_formatos)


def checar_data(data):
    """`evento.data_inicio` em ISO: AAAA-MM-DD, ou incompleta (AAAA-MM, AAAA) quando o cliente ainda não fechou o dia. A
    incompleta passa com aviso: a capa e o microtexto mostram só o que existe (grafismos._data_br, render.fmt_data).
    Pedido de 08/10 (kit da A.M.E, temporada sem data) que não tinha chegado ao QA."""
    texto = str(data or "").strip()
    m = re.fullmatch(r"(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?", texto)
    if not m or (m.group(2) and not 1 <= int(m.group(2)) <= 12) or (m.group(3) and not 1 <= int(m.group(3)) <= 31):
        F("evento.data_inicio precisa ser AAAA-MM-DD (ou AAAA-MM, ou AAAA, enquanto o dia não existe)")
    elif not m.group(3):
        A(f"evento.data_inicio incompleta ({texto}): a capa mostra só {'o mês e o ano' if m.group(2) else 'o ano'}; complete quando o cliente fechar a data")


def main():
    pasta = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    sem_fontes = "--ambiente-sem-fontes" in sys.argv  # só para conferência estrutural fora da máquina do Ugo
    k = json.loads((pasta / "mediakit.json").read_text(encoding="utf-8"))

    # ---------- estrutura ----------
    if k.get("schema_version") not in VERSOES:
        F(f"schema_version deve ser {' ou '.join(VERSOES)}")
    for c in ["cliente", "evento", "tese", "provas", "cotas", "acervo", "marca", "acao", "inventario"]:
        if c not in k:
            F(f"falta `{c}`")
    if falhas:
        return fim()
    ev = k["evento"]
    for c in ["nome", "cidade", "data_inicio"]:
        if not ev.get(c):
            F(f"evento.{c} vazio")
    checar_data(ev.get("data_inicio"))
    if not k["tese"].get("frase"):
        F("tese.frase vazia: é a frase da capa")
    if k["marca"].get("direcao") not in {"causa", "performance", "territorio"}:
        F("marca.direcao precisa ser causa, performance ou territorio")
    if not k["acao"].get("pessoas") and not k["acao"].get("email"):
        F("acao precisa de pessoas (nome e telefone) ou email: o kit fecha com gente, não com formulário")
    if not k.get("manifesto", {}).get("frase"):
        A("sem manifesto: o kit perde a página 2 (por que o evento existe)")
    if not k["marca"].get("assinatura") in {"fio", "numeral", "lettering"}:
        F("marca.assinatura precisa ser fio, numeral ou lettering (guia C: um elemento-assinatura por deck)")
    if not k["marca"].get("estilo_cena"):
        A("marca.estilo_cena vazio: as cenas não terão luz e lente consistentes entre si (guia E)")

    # ---------- limites de slot (guia D) ----------
    def lim(texto, n, nome, palavras=False):
        if not texto: return
        t = re.sub(r"<[^>]+>", "", str(texto))
        q = len(t.split()) if palavras else len(t)
        if q > n: F(f"{nome}: {q} {'palavras' if palavras else 'caracteres'}, limite {n} (guia D: slot fixo, não deixe o texto fluir)")
    lim(k["tese"].get("frase"), 12, "tese.frase", True)
    man = k.get("manifesto") or {}
    if man.get("titulo"):
        for parte in man["titulo"].split("|"): lim(parte, 5, "manifesto.titulo (por linha)", True)
    lim(man.get("frase"), 240, "manifesto.frase")
    lim(k.get("cotas_intro"), 200, "cotas_intro")
    lim(k["acao"].get("proximo_passo"), 60, "acao.proximo_passo")
    for i in k.get("inventario", []):
        if i.get("titulo"):
            for parte in i["titulo"].split("|"): lim(parte, 4, f"inventario `{i.get('ativo')}` titulo (por parte)", True)
        lim(i.get("texto"), 380, f"inventario `{i.get('ativo')}` texto")
        if len(i.get("aplicacoes", [])) > 4: F(f"inventario `{i.get('ativo')}`: {len(i['aplicacoes'])} aplicações, limite 4")
    for c in k.get("cotas", []):
        lim(c.get("frase"), 110, f"cota `{c.get('nome')}` frase")
        for e in c.get("entregaveis", []): lim(e, 70, f"cota `{c.get('nome')}` entregável")

    # ---------- provas ----------
    provas = k.get("provas", []); ids = set(); valores = set()
    for p in provas:
        pid = p.get("id", "?")
        if pid in ids: F(f"prova `{pid}` duplicada")
        ids.add(pid)
        for c in ["id", "rotulo", "valor", "edicao", "tipo", "fonte"]:
            if p.get(c) in (None, ""): F(f"prova `{pid}`: falta `{c}`")
        if p.get("tipo") not in TIPOS: F(f"prova `{pid}`: tipo inválido")
        fonte = str(p.get("fonte", ""))
        if p.get("tipo") == "realizado" and not (fonte.startswith("documento:") or fonte.startswith("pesquisa:")):
            F(f"prova `{pid}`: `realizado` exige fonte documento: ou pesquisa:. Fala do organizador é `informado`")
        if p.get("tipo") == "proxy" and not (k.get("prova", {}).get("nota") or p.get("nota")):
            F(f"prova `{pid}`: proxy (dado de outro evento) exige nota visível dizendo de onde veio")
        if isinstance(p.get("valor"), (int, float)): valores.add(int(p["valor"]))
    destaques = [p for p in provas if p.get("destaque")]
    if len(destaques) > 3: F(f"{len(destaques)} provas em destaque; a página de público comporta 3 cards")
    if not provas: A("nenhuma prova: aceitável só em primeira edição, com página de metas")

    # ---------- números soltos ----------
    for caminho, t in textos(k):
        ult = caminho.split(".")[-1].split("[")[0]
        if caminho.startswith(("provas", "cotas", "acervo", "cliente", "acao", "receitas", "elementos")) or ult in CODIGOS or "graficos" in caminho \
                or codigo_de_elementos(caminho) or caminho.startswith(("direcao_criativa", "formato_base")):
            continue                     # direção criativa e formato: ids do repertório (web-deck-...-245250053) e sha256
        if re.search(r"(data|valido|aprovada_em|edicao|telefone)", caminho): continue
        for n in numeros(t):
            if n not in valores and not (1900 <= n <= 2100):
                F(f"{caminho}: número {n} no texto sem prova correspondente")

    # ---------- inventário e ativos ----------
    acervo_ids = {a["id"] for a in k.get("acervo", [])}
    com_cena = 0
    for i in k.get("inventario", []):
        nome = i.get("ativo", "?")
        if not i.get("onde"): F(f"inventario `{nome}`: falta `onde` (quem vê, quando)")
        cid = i.get("cena_id") or i.get("foto_id")
        if cid and cid not in acervo_ids: F(f"inventario `{nome}`: cena_id `{cid}` não existe no acervo")
        if cid:
            com_cena += 1
            if not i.get("titulo"): F(f"inventario `{nome}`: tem cena mas não tem `titulo` (ex.: 'Sua marca na|largada')")
            if not i.get("texto"): F(f"inventario `{nome}`: tem cena mas não tem `texto` (4 a 6 linhas)")
            elif len(i["texto"]) > 420: A(f"inventario `{nome}`: texto com {len(i['texto'])} caracteres; a página comporta ~380")
            if not i.get("aplicacoes"): F(f"inventario `{nome}`: tem cena mas não tem `aplicacoes` (a caixa de aplicações)")
        if i.get("titulo") and "|" not in i["titulo"] and len(i["titulo"].split()) < 3:
            A(f"inventario `{nome}`: título sem `|`; a segunda parte na cor é a regra 2 da gramática")
    if com_cena == 0: F("nenhum ativo com cena: o kit precisa de pelo menos uma página 'sua marca em uso' (regra 7)")
    elif com_cena < 3: A(f"só {com_cena} ativo(s) com cena; o Corre por Elas tem 5")

    # ---------- cotas ----------
    cotas = k.get("cotas", [])
    if not cotas: F("nenhuma cota")
    if len([c for c in cotas if c.get("principal")]) > 1: F("mais de uma cota principal")
    for c in cotas:
        nome = c.get("nome", "?")
        if not isinstance(c.get("preco"), (int, float)) or c["preco"] <= 0: F(f"cota `{nome}`: preço ausente ou zero")
        if not isinstance(c.get("quantidade"), int) or c["quantidade"] < 1: F(f"cota `{nome}`: quantidade ausente")
        if not c.get("entregaveis"): F(f"cota `{nome}`: sem entregáveis")
        if len(c.get("entregaveis", [])) > 8: A(f"cota `{nome}`: {len(c['entregaveis'])} entregáveis; o card encolhe acima de 8")
        if c.get("aprovada_por") not in {"cliente", "motion"}: F(f"cota `{nome}`: `aprovada_por` inválido")
        ex = c.get("exclusividade")
        if ex is not None and (not ex.get("categoria") or not ex.get("ate")): F(f"cota `{nome}`: exclusividade sem categoria ou prazo")
        for e in c.get("entregaveis", []):
            if re.search(r"exclusiv", e, re.I) and ex is None: F(f"cota `{nome}`: entregável fala em exclusividade sem objeto `exclusividade`")
            if re.search(r"\b(vendas|leads garantid|alcance m[ií]nimo|retorno garantido)", e, re.I): F(f"cota `{nome}`: entregável promete resultado ({e!r})")
            if not tem_posicao(e):
                A(f"cota `{nome}`: entregável sem posição ({e!r}); a regra 10 pede onde")
        if c.get("cena_id") and c["cena_id"] not in acervo_ids: F(f"cota `{nome}`: cena_id inexistente")

    # ---------- acervo ----------
    for a in k.get("acervo", []):
        aid = a.get("id", "?")
        if a.get("funcao") not in FUNCOES: F(f"acervo `{aid}`: funcao `{a.get('funcao')}` inválida")
        if a.get("gerada") and a.get("funcao") == "historico": F(f"acervo `{aid}`: imagem gerada não pode ser `historico`")
        if a.get("gerada") and a.get("funcao") in ("capa", "manifesto", "publico", "contato") and not a.get("rotulo"):
            A(f"acervo `{aid}`: cena gerada em página que fala do evento, sem rótulo; o Corre por Elas não rotula ativos, mas capa/público sem rótulo passam por registro")
        if not a.get("direito_uso"): A(f"acervo `{aid}`: sem direito de uso, fica fora")
        if not (pasta / a.get("arquivo", "")).exists(): F(f"acervo `{aid}`: arquivo não encontrado em {a.get('arquivo')}")
    usaveis = [a for a in k.get("acervo", []) if a.get("direito_uso") and a.get("funcao") in {"capa", "historico", "local", "ativo", "projecao", "manifesto", "cota", "publico", "contato"}]
    if not usaveis: F("nenhuma imagem usável: o kit não sai sem cena")
    if not any(a.get("funcao") == "projecao" for a in usaveis): A("sem cena de projeção do evento (página 3 do Corre por Elas): é a página que mais vende")
    if not any(a.get("funcao") in ("lettering", "logo") for a in k.get("acervo", [])): A("sem lettering/logo: a capa usa o nome em display")

    # ---------- vetados ----------
    vetados = [s["marca"] for h in k.get("historico", []) for s in h.get("patrocinadores", []) if not s.get("pode_citar", False)]
    for marca in vetados:
        for caminho, t in textos(k):
            if caminho.startswith(("historico", "pendencias")): continue
            if marca.lower() in t.lower(): F(f"`{marca}` não pode ser citado mas aparece em {caminho}")

    # ---------- acentos e travessão ----------
    checar_textos(k)

    # ---------- receitas (frente 4): diferentes entre si e do histórico ----------
    receitas = k.get("receitas") or []
    checar_receitas(receitas, k)
    checar_ledger(receitas, k, ledger_path())

    # ---------- conjunto de elementos (Frente C): herói por página, novidade, exclusividade, família, OCR ----------
    if k.get("sistema_elementos"):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import qa_conjunto
        for nivel, msg in qa_conjunto.checar(pasta, k):
            (F if nivel == "FALHA" else A)(msg)

    # ---------- camada de acabamento (mk-2.1): só em kit que declara a camada; o mk-2.0 sem campo novo não passa aqui ----------
    checar_acabamento(pasta, k)

    # ---------- render: métricas geométricas (guia A, B, C, H) ----------
    rep = pasta / "saida" / "render-report.json"
    if rep.exists():
        r = json.loads(rep.read_text(encoding="utf-8"))
        for w in r.get("avisos", []):
            (F if "sem cena" in w else A)(f"render: {w}")
        seq = r.get("sequencia", [])
        # piloto (`paginas` no JSON): a sequência é parcial de propósito, as regras de ordem viram aviso
        O = A if r.get("piloto") else F
        if seq and seq[0] != "capa": O("a primeira página não é a capa")
        if seq and seq[-1] != "contato": O("a última página não é o contato")
        if "divisor_cotas" in seq and "cota" in seq and seq.index("divisor_cotas") > seq.index("cota"): O("cota antes do divisor de cotas")
        for a_, b_ in zip(seq, seq[1:]):
            if a_ == b_ and a_ not in ("cota", "ativo_painel"): O(f"arquétipo `{a_}` repetido em sequência (guia C: variedade)")
        # ---------- ritmo editorial (pesquisa r2, page plan) ----------
        plano = r.get("pageplan", [])
        pesos = [p["peso"] for p in plano]; funcs = [p["funcao"] for p in plano]
        for i in range(1, len(pesos)):
            if pesos[i] == 3 and pesos[i - 1] == 3: O(f"ritmo: páginas {i} e {i+1} são ambas de impacto máximo sem respiro")
        for i in range(2, len(pesos)):
            if pesos[i] == pesos[i - 1] == pesos[i - 2] == 1: O(f"ritmo: três páginas informativas seguidas ({i-1} a {i+1}); intercale uma de impacto")
        if "oferta" in funcs and "prova" in funcs and funcs.index("oferta") < funcs.index("prova"): O("ritmo: oferta antes da prova (audiência/números); o patrocinador compra a audiência primeiro")
        janela = 0
        for i, p in enumerate(pesos):
            janela = 0 if p == 3 else janela + 1
            if janela > 5: A(f"ritmo: {janela} páginas sem impacto até a p.{i+1}"); janela = 0
        # ---------- objetos recortados: brief e integração (pesquisa r2, seção e) ----------
        for o in k.get("objetos", []):
            for c in ("id", "pagina", "classe", "funcao", "arquivo", "x", "y", "w", "modo", "luz"):
                if o.get(c) in (None, ""): F(f"objeto `{o.get('id','?')}`: falta `{c}` no brief (função, âncora, proporção, direção, luz)")
            if o.get("modo") == "atras" and not o.get("divisa_px"): F(f"objeto `{o.get('id')}`: modo atras exige divisa_px")
            if not o.get("sombra"): F(f"objeto `{o.get('id')}`: sem sombra de contato pré-renderizada (tratar.py sombra); drop-shadow em CSS rasteriza no PDF")
            if o.get("classe") not in ("atleta", "produto", "equipamento"): A(f"objeto `{o.get('id')}`: classe fora de atleta/produto/equipamento (define o modelo de recorte)")
            if o.get("classe") == "atleta" and o.get("recorte") not in ("birefnet-portrait", "higgsfield", "cliente"): A(f"objeto `{o.get('id')}`: atleta recortado sem birefnet-portrait + -dc; confira halo no cabelo")
            if not o.get("temperatura_igualada"): A(f"objeto `{o.get('id')}`: temperatura não igualada à cena (tratar.py igualar); objeto pode parecer colado")
            try:
                from PIL import Image
                im = Image.open(pasta / o["arquivo"]); 
                if im.width < 2 * o.get("w", 0): F(f"objeto `{o.get('id')}`: {im.width}px de largura para {o.get('w')}px de uso; mínimo 2× (resolução)")
                if im.mode != "RGBA": F(f"objeto `{o.get('id')}`: sem canal alfa")
            except Exception as e:
                A(f"objeto `{o.get('id')}`: não abriu ({e})")
        cmaps = mapa_cmaps(r.get("fontes_dir"))
        for d, m in r.get("direcoes", {}).items():
            h = m.get("horizontal") or {}
            ruins = [f for f, ok in h.get("fontes", {}).items() if not ok]
            if ruins: F(f"{d}: fonte não carregada ({', '.join(ruins)}): render com fallback não é resultado (guia B)")
            for a in h.get("ajustes", []):
                if a.get("estourou"): F(f"{d} p.{a['pagina']}: ainda estoura: {a['texto'][:50]!r}")
                elif a["fonte_final"] < 0.72 * a["fonte_inicial"] or a.get("zoom", 1) < 0.85: F(f"{d} p.{a['pagina']}: encolheu {100 - round(100 * a['fonte_final'] / a['fonte_inicial'])}% (limite 28%): corte texto no JSON: {a['texto'][:50]!r}")
            pags = h.get("por_pagina", [])
            seq_d = m.get("sequencia") or seq   # receita: ativos podem ter trocado de layout
            checar_camadas(d, m, pags)
            # ---------- cobertura de glifos (aprendizado 20): letra fora do subconjunto da fonte cai em outra fonte ----------
            for formato, medida in (("", h), (" vertical", m.get("vertical") or {})):
                for p in medida.get("por_pagina", []):
                    for g in p.get("glifos", []):
                        falta = glifos_faltando(g, cmaps)
                        for ch, t in (falta or {}).items():
                            msg = f"{d}{formato} p.{p['pagina']}: {ch!r} (U+{ord(ch):04X}) não existe em {g['familia']} (peso {g['peso']}); cai em outra fonte em {t[:40]!r}"
                            (F if g["papel"] == "display" else A)(msg + (" (título/display: troque o texto ou a fonte)" if g["papel"] == "display" else ""))
            com_cena = sum(1 for p in pags if p.get("tem_cena"))
            if pags and com_cena / len(pags) < 0.6: A(f"{d}: só {com_cena}/{len(pags)} páginas com cena em sangria; guia C pede ≥ 60%")
            foco_el = tinta_do_foco(pasta, k, d)
            for p in pags:
                n = p["pagina"]; tipo = seq_d[n - 1] if n - 1 < len(seq_d) else "?"
                for t in p.get("fora_da_pagina", []): F(f"{d} p.{n}: texto fora da página: {t!r}")
                for t in p.get("viuvas", []): F(f"{d} p.{n}: viúva no título ({t!r}): reescreva ou mude a quebra `|`")
                for e in p.get("escala_fora", []): F(f"{d} p.{n}: font-size {e['fs']:.0f}px fora da escala (230/96/64/36/24/16): {e['texto'][:40]!r}")
                for t in p.get("micro_2linhas", []): F(f"{d} p.{n}: microlabel em mais de uma linha: {t!r}")
                icones = p.get("svgs", 0) - p.get("svgs_grafismo", 0)  # grafismo (svg.grafismo) é elemento, não ícone
                if icones > 4: F(f"{d} p.{n}: {icones} ícones; limite 4 (guia C)")
                papeis = p.get("cor_papeis", [])
                if len(papeis) > 8: F(f"{d} p.{n}: cor da marca em {len(papeis)} papéis ({', '.join(papeis[:8])}…); limite 8")
                elif len(papeis) > 6: A(f"{d} p.{n}: cor da marca em {len(papeis)} papéis; o Corre por Elas usa até 6")
                dens = p.get("densidade_texto", 0)
                if dens > 0.45: F(f"{d} p.{n}: densidade de texto {dens:.0%}; acima de 45% é relatório")
                elif dens > 0.35 and tipo not in ("inventario_colunas",): A(f"{d} p.{n}: densidade de texto {dens:.0%} (faixa 8 a 35%)")
                elif dens < 0.03 and tipo not in ("projecao", "capa", "contato"): A(f"{d} p.{n}: densidade de texto {dens:.0%}: página quase vazia")
                dom, seg = dominante_com_foco(p.get("area_dominante", 0), p.get("area_segundo", 0), foco_el.get(n))
                if tipo in ("prova", "inventario_colunas"):
                    pass  # páginas de conjunto: o dominante é o grupo de números/itens (Corre por Elas p.6, Levinrun "Onde sua marca pode aparecer")
                elif dom < 0.28 and not (dom >= 0.05 and dom >= 2 * seg): F(f"{d} p.{n}: nenhum elemento dominante (maior ocupa {dom:.0%}, segundo {seg:.0%}; precisa de ≥ 28% ou o dobro do segundo)")
                elif not p.get("tem_cena") and p.get("area_segundo", 0) > 0.18 and p.get("area_segundo", 0) > 0.8 * p.get("area_dominante", 0): A(f"{d} p.{n}: dois elementos disputam o domínio")
                des = p.get("desalinhados", [])
                if len(des) > 2: A(f"{d} p.{n}: {len(des)} blocos fora das colunas do grid: {des[:2]}")
                # cena com placeholder exige composição
            # contraste amostrado no PNG
            png_dir = h.get("png_dir")
            if png_dir and Path(png_dir).exists():
                try:
                    from PIL import Image
                    import numpy as np
                    for p in pags:
                        n = p["pagina"]; f = Path(png_dir) / f"kit-{d}-{n:02d}.png"
                        if not f.exists(): continue
                        L = lum_wcag(np.asarray(Image.open(f).convert("RGB"), dtype=float) / 255.0)
                        for t in p.get("textos", []):
                            cr = contraste_do_texto(L, t, p.get("pattern"))   # `r` é o render-report, usado depois
                            if cr is None: continue
                            ratio, minimo = cr
                            if ratio < minimo: F(f"{d} p.{n}: contraste{' (sobre pattern)' if p.get('pattern') else ''} {ratio:.1f}:1 abaixo de {minimo}:1 em {t['texto'][:40]!r} (texto sobre luz: mova, ponha véu ou troque o foco da foto)")
                except ImportError:
                    A("Pillow/numpy ausentes: contraste não amostrado")
        # ---------- elementos: colisão real com as linhas protegidas (qa_geometria.py lê saida/plano-elementos-*.json) ----------
        import qa_geometria
        fg, ag = qa_geometria.checar(pasta, list(r.get("direcoes", {})))
        for x in fg: F(x)
        for x in ag: A(x)
        # ---------- arquivo entregue (validar_pdf.py): o horizontal e, desde 12/10, o vertical ----------
        # O vertical não ia ao validar_pdf e saiu partido em todo kit (cada página 1080x1920 em duas folhas deitadas de
        # 1440x810 pt; a AME v2 foi entregue assim). Vai para todo kit; as linhas dele são novas também no legado.
        import subprocess, qa_conjunto
        acab = qa_conjunto.declara_acabamento(k)
        for d in r.get("direcoes", {}):
            for vertical in (False, True):
                cmd = cmd_validar_pdf(pasta, k, r, d, vertical, acab)
                if not cmd:
                    continue
                rot = f"pdf {d}{' vertical' if vertical else ''}"
                res = subprocess.run(cmd, capture_output=True, text=True)
                for l in res.stdout.splitlines():
                    if l.startswith("FALHA") and "fallback" in l and sem_fontes: A(f"{rot}: {l[7:]} [RENDER ESTRUTURAL, NÃO AVALIÁVEL]")
                    elif l.startswith("FALHA"): F(f"{rot}: {l[7:]}")
                    elif l.startswith("AVISO"): A(f"{rot}: {l[7:]}")
    else:
        A("render-report.json não existe: rode o render.py antes")
    # cena gerada com placeholder exige composição (guia E)
    for a in k.get("acervo", []):
        if a.get("gerada") and a.get("funcao") in ("projecao", "ativo", "cota") and not a.get("composta"):
            A(f"acervo `{a['id']}`: cena de ativo gerada sem `composta: true`; lettering e 'SEU LOGO AQUI' devem entrar por compor.py, não pelo modelo")
    return fim()


def fim():
    for a in avisos: print(f"AVISO  {a}")
    for f in falhas: print(f"FALHA  {f}")
    print(f"\n{len(falhas)} falha(s), {len(avisos)} aviso(s)")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()

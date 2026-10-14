#!/usr/bin/env python3
"""
grafismos.py: elementos feitos por código, com texto vivo (Frente B do sistema de elementos; contrato e assinatura em
references/08-sistema-elementos.md). A IA não escreve letra nenhuma (aprendizado 7): todo elemento que tem texto sai
daqui, como SVG inline com <text>/<textPath> na fonte do kit, e chega ao PDF como texto de verdade.

    gerar(tipo, params, ctx) -> {"svg": "<svg ...>", "w": int, "h": int, "texto": str, "fontes": [familia, ...]}
                                (+ "tinta", "linhas" e "origem" nos desenhos de composição)

    ctx = {"fontes": {"display": fam, "peso_display": int, "corpo": fam}, "paleta": {"marca": "#..", ...},
           "evento": {...}, "logo_png": caminho|None, "fontes_dir": caminho}

Tipos (parâmetros no docstring de cada função):
  texto, símbolo e textura do evento: microtexto, selo, meio-tom-simbolo, pattern-simbolo, linha-percurso, fios-tecnicos,
    moldura, etiqueta, numeral, tipo-textura, faixa-diagonal, mosaico;
  composição (desenhos presos a algo da página, references/09-composicao.md): linhas, listras, colchetes, fio, regua,
    divisoria, grade-pontos, circulos, setas, estrelas, campo (futebol, futsal, pista em escala real), placar, celular,
    mapa (esquemático: posição e distância, sem contorno de estado) e as constantes de borda fio-borda e pattern-borda;
  acabamento (textura, borda, profundidade e tipografia expressiva, plano de 12/10/2026): hachura, malha (com perspectiva
    por homografia), aneis, pontos-radiais, cantoneira, moldura-dupla, regua-borda (também constante), eco, texto-curva,
    ondas, curvas-nivel, fita, carimbo, numeral-eco e meio-tom-foto; o campo aceita `perspectiva`.
Cor em params = chave da paleta do ctx ("marca", "escuro", "papel", "texto", "apoio") ou #RRGGBB; nos desenhos de
composição, "marca" (o padrão) sai como currentColor, a cor do acento da página. Tamanhos em px da página 1920x1080.

MEDIDA DO TEXTO. A largura sai das tabelas da própria fonte (fontTools): avanço de cada glifo (hmtx) mais o kerning
da feature `kern` do GPOS (pares específicos e por classe, aplicados na ordem e com o salto de par que o HarfBuzz usa;
tabela `kern` antiga só quando não há GPOS), depois das substituições obrigatórias `rvrn` que as instâncias estáticas
herdam da fonte variável. O SVG trava o que o navegador poderia mudar sozinho: font-variant-ligatures: none (sem
ligadura nem alternativa contextual, que trocariam glifos), font-kerning: normal, font-synthesis: none,
white-space: pre (espaço no fim conta) e text-rendering: geometricPrecision (tamanho exato, sem arredondar). Com isso o
comprimento calculado aqui é o que o Chromium desenha: o selo fecha o anel, a faixa de microtexto termina na borda.
Prova: test_grafismos.py mede getComputedTextLength() no Chromium com as fontes do kit (tolerância 1 px).

PESO. Mesmo casamento que o render.py faz com a pasta de fontes: `Familia__700.ttf` é o peso 700, `Familia.ttf` cobre
o resto. Peso pedido sem arquivo cai no peso existente mais próximo pela regra do CSS Fonts 4 (acima de 500 procura o
mais pesado primeiro) e o SVG declara o peso que de fato vai desenhar, para medida e desenho baterem.
Glifo ausente na fonte = ValueError nomeando o caractere (nada cai em fonte reserva sem aviso, aprendizado 20).

CLI:
  python grafismos.py ctx <pasta-do-kit> [--receita r1] [--fontes <dir>]          imprime o ctx montado do mediakit.json
  python grafismos.py svg <tipo> --ctx <ctx.json> [--params '<json>'] [--saida x.svg]
  python grafismos.py folha <pasta-do-kit> --receita r1 --fontes <dir> --saida folha.png [--recorte x0,y0,x1,y1]
"""
import argparse, base64, hashlib, html, io, json, math, mimetypes, re, sys, unicodedata
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from caminhos import dentro_do_kit  # noqa: E402

AQUI = Path(__file__).resolve().parent
EXT_FONTE = (".ttf", ".otf")
SVGNS = "http://www.w3.org/2000/svg"
PAPEIS = ("display", "titulo", "corpo", "lettering")   # lettering e titulo caem no display quando a receita não declara


# ---------------------------------------------------------------- números, escape, cor
def _n(v):
    s = f"{float(v):.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "", "-") else s


def _r(v):
    return round(float(v), 3)


def _esc(t):
    return html.escape(t, quote=False)


def _attr(t):
    return html.escape(t, quote=False).replace('"', "&quot;")


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _cor(valor, ctx, padrao="marca"):
    v = padrao if valor is None else valor
    pal = ctx.get("paleta") or {}
    if isinstance(v, str) and v in pal:
        v = pal[v]
    if isinstance(v, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
        return v.upper()
    raise ValueError(f"cor `{valor if valor is not None else padrao}`: use uma chave da paleta ({', '.join(pal) or 'paleta vazia'}) ou #RRGGBB")


def _luminancia(h):
    c = np.asarray(_rgb(h), float) / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(c @ [0.2126, 0.7152, 0.0722])


def _contraste(a, b):
    la, lb = sorted((_luminancia(a), _luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _uid(tipo, params, ctx):
    chave = json.dumps({"t": tipo, "p": params, "f": ctx.get("fontes"), "c": ctx.get("paleta"), "l": str(ctx.get("logo_png") or "")},
                       sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha1(chave.encode()).hexdigest()[:8]


def _svg(w, h, corpo, tipo, uid):
    return (f'<svg xmlns="{SVGNS}" width="{int(w)}" height="{int(h)}" viewBox="0 0 {int(w)} {int(h)}" '
            f'data-grafismo="{tipo}" data-uid="{uid}" overflow="hidden">{corpo}</svg>')


def _inteiro(v):
    return int(math.ceil(float(v) - 1e-6))


# ---------------------------------------------------------------- texto dos params
def _data_br(iso):
    """A data do evento em texto. O kit pode declarar `evento.data_inicio` incompleto (a capa vira "Temporada 2027"): data
    completa (2027-03-14) sai 14.03.2027; só ano e mês (2027-03), 03/2027; só o ano (2027), 2027. O que não é ISO sai como
    veio, e vazio é None: nunca derruba o render, a folha nem o microtexto."""
    if not iso:
        return None
    texto = str(iso).strip()
    partes = texto[:10].split("-")
    if 1 <= len(partes) <= 3 and all(x.isdigit() for x in partes) and len(partes[0]) == 4:
        a, *resto = partes
        if not resto:
            return a
        if len(resto) == 1:
            return f"{resto[0].zfill(2)}/{a}"
        return f"{resto[1].zfill(2)}.{resto[0].zfill(2)}.{a}"
    return texto


def _texto_de(de, ctx):
    ev = ctx.get("evento") or {}
    if de == "evento":
        return ev.get("nome")
    if de == "local":
        cidade = "/".join(x for x in (ev.get("cidade"), ev.get("uf")) if x)
        return " · ".join(x for x in (ev.get("local"), cidade) if x)
    if de == "data":
        return _data_br(ev.get("data_inicio"))
    if de in ("titulo", "tese"):       # textos da página e do kit: quem monta o ctx põe em ctx["textos"] (o render, por página)
        t = (ctx.get("textos") or {}).get(de)
        if not t or not str(t).strip():
            raise ValueError(f"texto_de `{de}`: o ctx não trouxe textos.{de} (o render passa o título da página e a tese do kit)")
        return str(t)
    raise ValueError(f"texto_de `{de}`: use evento, local, data, titulo ou tese (personalizado: passe `texto`)")


def _texto(p, ctx, chave="texto", caixa_alta=True):
    t = p.get(chave)
    if t is None and chave == "texto" and p.get("texto_de"):
        t = _texto_de(p["texto_de"], ctx)
    if t is None or not str(t).strip():
        raise ValueError(f"`{chave}` vazio")
    t = unicodedata.normalize("NFC", " ".join(str(t).split()))
    return t.upper() if caixa_alta else t


# ---------------------------------------------------------------- fontes: arquivo, peso, medida
def _lookups(tt, tabela, tag):
    """Lookups da feature `tag` no script latino (ou DFLT), na ordem em que o HarfBuzz aplica (índice crescente)."""
    if tabela not in tt:
        return []
    t = tt[tabela].table
    if not t.FeatureList or not t.LookupList:
        return []
    scripts = {sr.ScriptTag: sr.Script for sr in (t.ScriptList.ScriptRecord if t.ScriptList else [])}
    script = scripts.get("latn") or scripts.get("DFLT") or next(iter(scripts.values()), None)
    if script is not None and script.DefaultLangSys is not None:
        indices = list(script.DefaultLangSys.FeatureIndex)
    else:
        indices = range(len(t.FeatureList.FeatureRecord))
    alvo = set()
    for i in indices:
        fr = t.FeatureList.FeatureRecord[i]
        if fr.FeatureTag == tag:
            alvo.update(fr.Feature.LookupListIndex)
    return [t.LookupList.Lookup[i] for i in sorted(alvo)]


def _desembrulhar(lookup, tipo_extensao):
    subs, tipo = list(lookup.SubTable), lookup.LookupType
    if tipo == tipo_extensao and subs:
        tipo = subs[0].ExtensionLookupType
        subs = [s.ExtSubTable for s in subs]
    return tipo, subs


def _xadv(v):
    return float(getattr(v, "XAdvance", 0) or 0) if v is not None else 0.0


class _Par:
    """Uma subtabela PairPos (GPOS tipo 2). valor(g1, g2) devolve (ajuste do 1º, ajuste do 2º) ou None quando a
    subtabela não se aplica ao par; formato 2 com o 1º glifo coberto sempre se aplica (mesmo com valor 0), como no HarfBuzz."""

    def __init__(self, st):
        self.formato = st.Format
        self.cobertura = set(st.Coverage.glyphs)
        self.pula = bool(st.ValueFormat2)   # com valor no 2º glifo, o par seguinte começa depois dele
        if st.Format == 1:
            self.pares = {g: {r.SecondGlyph: (_xadv(getattr(r, "Value1", None)), _xadv(getattr(r, "Value2", None)))
                              for r in ps.PairValueRecord} for g, ps in zip(st.Coverage.glyphs, st.PairSet)}
        else:
            self.c1 = dict(st.ClassDef1.classDefs) if st.ClassDef1 else {}
            self.c2 = dict(st.ClassDef2.classDefs) if st.ClassDef2 else {}
            self.m = [[(_xadv(getattr(c2, "Value1", None)), _xadv(getattr(c2, "Value2", None))) for c2 in c1.Class2Record]
                      for c1 in st.Class1Record]

    def valor(self, g1, g2):
        if g1 not in self.cobertura:
            return None
        if self.formato == 1:
            return self.pares.get(g1, {}).get(g2)
        k1, k2 = self.c1.get(g1, 0), self.c2.get(g2, 0)
        if k1 >= len(self.m) or k2 >= len(self.m[k1]):
            return None
        return self.m[k1][k2]


class Fonte:
    """Um arquivo de fonte do kit, com a medida que o navegador vai usar."""

    def __init__(self, caminho, familia, peso):
        from fontTools.ttLib import TTFont
        self.caminho, self.familia, self.peso = Path(caminho), familia, int(peso)
        self.tt = TTFont(str(caminho))
        self.cmap = self.tt.getBestCmap() or {}
        self.upem = self.tt["head"].unitsPerEm
        self.hmtx = self.tt["hmtx"].metrics
        self._gset = None
        os2 = self.tt["OS/2"] if "OS/2" in self.tt else None
        self.cap = float(getattr(os2, "sCapHeight", 0) or 0) if os2 is not None else 0.0
        if not self.cap:
            self.cap = float(self._topo("H") or 0.7 * self.upem)
        self._kern = []
        for lk in _lookups(self.tt, "GPOS", "kern"):
            tipo, subs = _desembrulhar(lk, 9)
            if tipo == 2:
                self._kern.append([_Par(s) for s in subs])
        self._kern_antigo = {}
        if not self._kern and "kern" in self.tt:
            for st in getattr(self.tt["kern"], "kernTables", []):
                if getattr(st, "format", 0) == 0 and hasattr(st, "kernTable"):
                    self._kern_antigo.update(st.kernTable)
        self._rvrn = []
        for lk in _lookups(self.tt, "GSUB", "rvrn"):
            tipo, subs = _desembrulhar(lk, 7)
            if tipo == 1:
                m = {}
                for s in subs:
                    for k, v in s.mapping.items():
                        m.setdefault(k, v)
                self._rvrn.append(m)
        self._tnum = {}      # numerais tabulares (feature tnum, substituição simples): só se aplica quando o texto pede
        for lk in _lookups(self.tt, "GSUB", "tnum"):
            tipo, subs = _desembrulhar(lk, 7)
            if tipo == 1:
                for s in subs:
                    for k, v in s.mapping.items():
                        self._tnum.setdefault(k, v)

    def _glyphset(self):
        if self._gset is None:
            self._gset = self.tt.getGlyphSet()
        return self._gset

    def _topo(self, ch):
        from fontTools.pens.boundsPen import BoundsPen
        g = self.cmap.get(ord(ch))
        if g is None:
            return None
        pen = BoundsPen(self._glyphset()); self._glyphset()[g].draw(pen)
        return pen.bounds[3] if pen.bounds else None

    def glifos(self, texto, tabular=False):
        gs = []
        for ch in texto:
            g = self.cmap.get(ord(ch))
            if g is None:
                raise ValueError(f"glifo ausente: {ch!r} (U+{ord(ch):04X}) não existe em {self.familia} {self.peso} ({self.caminho.name}); "
                                 "troque o caractere ou a fonte (nada cai em fonte reserva sem aviso)")
            for m in self._rvrn:
                g = m.get(g, g)
            if tabular:
                g = self._tnum.get(g, g)
            gs.append(g)
        return gs

    def avancos(self, texto, tabular=False):
        """Avanço de cada caractere em unidades da fonte, com o kerning do par já somado. `tabular` aplica a feature tnum
        (a mesma que `font-variant-numeric: tabular-nums` liga no navegador); fonte sem tnum mede igual."""
        gs = self.glifos(texto, tabular)
        adv = [float(self.hmtx[g][0]) for g in gs]
        for subs in self._kern:          # cada lookup percorre a linha inteira, como no HarfBuzz
            i = 0
            while i < len(gs) - 1:
                v, st = None, None
                for st in subs:
                    v = st.valor(gs[i], gs[i + 1])
                    if v is not None:
                        break
                if v is None:
                    i += 1
                    continue
                adv[i] += v[0]; adv[i + 1] += v[1]
                i += 2 if st.pula else 1
        if self._kern_antigo:
            for i in range(len(gs) - 1):
                adv[i] += self._kern_antigo.get((gs[i], gs[i + 1]), 0)
        return adv

    def largura(self, texto, tamanho, espacamento=0.0, tabular=False):
        """Comprimento que o navegador mede (getComputedTextLength): avanços + kerning + espaçamento após cada caractere."""
        return sum(self.avancos(texto, tabular)) * tamanho / self.upem + len(texto) * espacamento

    def cap_px(self, tamanho):
        return self.cap * tamanho / self.upem

    def caixa_tinta(self, texto, tamanho, espacamento=0.0, tabular=False):
        """(x0, y0, x1, y1) da tinta em px, origem no início da linha de base, y para CIMA (convenção da fonte)."""
        from fontTools.pens.boundsPen import BoundsPen
        esc, x, caixa = tamanho / self.upem, 0.0, None
        gset = self._glyphset()
        for g, a in zip(self.glifos(texto, tabular), self.avancos(texto, tabular)):
            pen = BoundsPen(gset); gset[g].draw(pen)
            if pen.bounds:
                x0, y0, x1, y1 = pen.bounds
                b = (x + x0 * esc, y0 * esc, x + x1 * esc, y1 * esc)
                caixa = b if caixa is None else (min(caixa[0], b[0]), min(caixa[1], b[1]), max(caixa[2], b[2]), max(caixa[3], b[3]))
            x += a * esc + espacamento
        return caixa or (0.0, 0.0, 0.0, 0.0)


@lru_cache(maxsize=None)
def _peso_do_arquivo(caminho):
    from fontTools.ttLib import TTFont
    return int(TTFont(caminho, lazy=True)["OS/2"].usWeightClass)


def _peso_css(w, pesos):
    """Casamento de peso do CSS Fonts 4 (§5.2) entre pesos discretos."""
    pesos = sorted(set(pesos))
    if w in pesos:
        return w
    if 400 <= w <= 500:
        ordem = [p for p in pesos if w < p <= 500] + [p for p in reversed(pesos) if p < w] + [p for p in pesos if p > 500]
    elif w < 400:
        ordem = [p for p in reversed(pesos) if p < w] + [p for p in pesos if p > w]
    else:
        ordem = [p for p in pesos if p > w] + [p for p in reversed(pesos) if p < w]
    return ordem[0]


def resolver_fonte(fontes_dir, familia, peso):
    """(arquivo, peso que o SVG declara) para a família no peso pedido, pela convenção de nomes do render.py."""
    d = Path(fontes_dir)
    if not d.is_dir():
        raise ValueError(f"pasta de fontes não existe: {d}")
    explicitos, base = {}, None
    for f in sorted(d.iterdir()):
        if f.suffix.lower() not in EXT_FONTE:
            continue
        fam, _, p = f.stem.partition("__")
        if fam != familia:
            continue
        if p.isdigit():
            explicitos[int(p)] = f
        elif not p:
            base = f
    if not explicitos and base is None:
        raise ValueError(f"família `{familia}` sem arquivo .ttf/.otf em {d}")
    candidatos = dict(explicitos)
    if base is not None:
        candidatos.setdefault(_peso_do_arquivo(str(base)), base)
    w = _peso_css(int(peso), list(candidatos))
    return candidatos[w], w


@lru_cache(maxsize=64)
def _carregar(caminho, familia, peso):
    return Fonte(caminho, familia, peso)


def fonte(ctx, papel="display", peso=None):
    """A fonte do kit para o papel (display, titulo, corpo, lettering) no peso pedido (display: ctx.fontes.peso_display).
    `titulo` e `lettering` caem no display quando a receita não declara a família (o lettering, com peso_lettering ou o
    peso do display)."""
    if papel not in PAPEIS:
        raise ValueError(f"fonte `{papel}`: use {', '.join(PAPEIS)}")
    fams = ctx.get("fontes") or {}
    familia = fams.get(papel) or (fams.get("display") if papel in ("titulo", "lettering") else None)
    if not familia:
        raise ValueError(f"ctx['fontes'] sem a família `{papel}`")
    if peso is None:
        if papel == "lettering" and fams.get("lettering"):
            peso = fams.get("peso_lettering") or fams.get("peso_display") or 700
        else:
            peso = (fams.get("peso_display") or 700) if papel in ("display", "titulo", "lettering") else 400
    if not ctx.get("fontes_dir"):
        raise ValueError("ctx['fontes_dir'] vazio: a medida do texto precisa dos arquivos da fonte do kit")
    caminho, w = resolver_fonte(ctx["fontes_dir"], familia, peso)
    return _carregar(str(caminho), familia, w)


def _estilo(f, tamanho, espacamento=0.0, tabular=False):
    fam = f.familia.replace("'", "\\'")
    num = ";font-variant-numeric:tabular-nums" if tabular else ""     # só quando pedido: o SVG dos tipos antigos não muda
    return _attr(f"font-family:'{fam}';font-weight:{f.peso};font-style:normal;font-size:{_n(tamanho)}px;"
                 f"letter-spacing:{_n(espacamento)}px;word-spacing:0;font-kerning:normal;font-variant-ligatures:none;"
                 f"font-synthesis:none;white-space:pre;text-rendering:geometricPrecision{num}")


def _linha_exata(f, ciclo, tamanho, comprimento, espacamento_em, repeticoes=None):
    """Repete `ciclo` k vezes e acha o espaçamento entre letras que faz a linha medir exatamente `comprimento`.
    Devolve (linha, espacamento_px, k)."""
    natural = f.largura(ciclo, tamanho, espacamento_em * tamanho)
    k = int(repeticoes or max(1, round(comprimento / natural)))
    linha = ciclo * k
    ls = _r((comprimento - f.largura(linha, tamanho)) / len(linha))
    if ls < -0.12 * tamanho:
        raise ValueError(f"texto não cabe em {comprimento:.0f}px nem uma vez no corpo {tamanho:g}px: '{ciclo.strip()}' "
                         f"mede {f.largura(ciclo, tamanho):.0f}px; reduza o tamanho ou o texto")
    return linha, ls, k


# ---------------------------------------------------------------- símbolo do cliente (logo)
def _cobertura(im):
    """Quanto de tinta tem cada pixel (0 a 1): o alfa, quando o PNG tem transparência; senão a distância à cor da borda."""
    a = np.asarray(im.getchannel("A"), float) / 255
    if (a < 0.98).mean() > 0.01:
        return a
    l = np.asarray(im.convert("L"), float) / 255
    fundo = float(np.median(np.concatenate([l[0], l[-1], l[:, 0], l[:, -1]])))
    dist = np.abs(l - fundo)
    return np.clip(dist / max(0.2, float(np.percentile(dist, 99))), 0, 1)


def _simbolo(caminho, recorte=None):
    """(imagem RGBA, cobertura) do logo cortado na tinta. `recorte` = [x0, y0, x1, y1] em fração da caixa do logo
    (ex.: só a asa da Sprint, sem o nome escrito): entram só as partes do desenho que cabem INTEIRAS na caixa; uma letra
    que a caixa cortaria sai inteira, em vez de deixar um pedaço solto no símbolo."""
    if not caminho or not Path(caminho).exists():
        raise ValueError(f"logo não encontrado: {caminho}")
    im = Image.open(caminho).convert("RGBA")
    cob = _cobertura(im)

    def caixa(c):
        ys, xs = np.nonzero(c > 0.03)
        if not len(xs):
            raise ValueError(f"logo sem forma visível em {caminho} (recorte {recorte})")
        return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1

    x0, y0, x1, y1 = caixa(cob)
    im, cob = im.crop((x0, y0, x1, y1)), cob[y0:y1, x0:x1]
    if recorte:
        from scipy import ndimage
        a, b, c, d = (float(v) for v in recorte)
        W, H = im.size
        bx = (round(a * W), round(b * H), round(c * W), round(d * H))
        rot, n = ndimage.label(cob > 0.03, structure=np.ones((3, 3)))
        manter = np.zeros(n + 1, bool)
        for i, sl in enumerate(ndimage.find_objects(rot), 1):
            manter[i] = sl[1].start >= bx[0] and sl[1].stop <= bx[2] and sl[0].start >= bx[1] and sl[0].stop <= bx[3]
        mascara = ndimage.binary_dilation(manter[rot], iterations=1)   # leva junto a franja de antialias das partes mantidas
        cob = np.where(mascara, cob, 0.0)
        im.putalpha(Image.fromarray((np.asarray(im.getchannel("A"), float) * mascara).astype(np.uint8)))
        x0, y0, x1, y1 = caixa(cob)
        im, cob = im.crop((x0, y0, x1, y1)), cob[y0:y1, x0:x1]
    return im, cob


def _png_uri(im, largura_px=None):
    if largura_px and im.width > largura_px:
        im = im.resize((int(largura_px), max(1, round(im.height * largura_px / im.width))), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def _tingir(cob, hexa):
    r, g, b = _rgb(hexa)
    a = (np.clip(cob, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([np.full_like(a, r), np.full_like(a, g), np.full_like(a, b), a]), "RGBA")


def _contorno(cob, lado_px, suavizar=1.0, tolerancia=0.4, area_min=0.0004):
    """Contorno da tinta como path SVG (regra evenodd: os furos ficam furos) com o lado maior medindo `lado_px`.
    Devolve (d, largura, altura)."""
    from scipy.ndimage import gaussian_filter
    from skimage import measure
    h, w = cob.shape
    k = 640 / max(h, w)
    trab = np.asarray(Image.fromarray((np.clip(cob, 0, 1) * 255).astype(np.uint8)).resize(
        (max(2, round(w * k)), max(2, round(h * k))), Image.LANCZOS), float) / 255
    trab = np.pad(trab, 3)
    if suavizar:
        trab = gaussian_filter(trab, suavizar)
    H, W = trab.shape
    fator = lado_px / max(H - 6, W - 6)
    total = (H - 6) * (W - 6)
    partes = []
    for c in measure.find_contours(trab, 0.5):
        if len(c) < 6:
            continue
        x, y = c[:, 1], c[:, 0]
        if 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))) < area_min * total:
            continue   # cisco
        c = measure.approximate_polygon(c, tolerance=tolerancia / fator)
        pts = (c[:, ::-1] - 3) * fator
        if np.allclose(pts[0], pts[-1]):
            pts = pts[:-1]
        partes.append("M" + " L".join(f"{_n(px)} {_n(py)}" for px, py in pts) + "Z")
    if not partes:
        raise ValueError("símbolo sem contorno aproveitável")
    return " ".join(partes), (W - 6) * fator, (H - 6) * fator


# ---------------------------------------------------------------- tipos
def _microtexto(p, ctx, uid):
    """Faixa de texto em loop na borda (referência web-nike-run-sp-25-10). O texto se repete quantas vezes couber e o
    espaçamento entre letras é recalculado para a faixa medir exatamente `largura`, pela medida da fonte.
    params: texto | texto_de (evento, local, data); largura 1920; tamanho 16; altura 2,2 x tamanho; fonte 'corpo';
    peso 700; cor 'marca'; fundo None; espacamento 0,14 em; separador ' · '; caixa_alta True; repeticoes automático."""
    unidade = _texto(p, ctx, caixa_alta=p.get("caixa_alta", True))
    sep = p.get("separador", " · ")
    W = float(p.get("largura", 1920)); s = _r(p.get("tamanho", 16))
    f = fonte(ctx, p.get("fonte", "corpo"), p.get("peso", 700))
    linha, ls, _ = _linha_exata(f, unidade + sep, s, W, float(p.get("espacamento", 0.14)), p.get("repeticoes"))
    H = _inteiro(p.get("altura") or s * 2.2)
    cor = _cor(p.get("cor"), ctx)
    corpo = ""
    if p.get("fundo"):
        corpo += f'<rect width="{_n(W)}" height="{H}" fill="{_cor(p["fundo"], ctx)}"/>'
    corpo += f'<text x="0" y="{_n(H / 2 + f.cap_px(s) / 2)}" fill="{cor}" style="{_estilo(f, s, ls)}">{_esc(linha)}</text>'
    return dict(svg=_svg(_inteiro(W), H, corpo, "microtexto", uid), w=_inteiro(W), h=H, texto=unidade, fontes=[f.familia])


SEPARADORES_ANEL = ("★", "•", "·")   # o primeiro que existir na fonte do kit vai às 3h e às 9h


def _sem_pontas(t, marca):
    return t.strip().strip(marca).strip()


def _dividir_em_dois(texto, sep, f, arco_cima, arco_baixo):
    """Divide o texto do selo em cima e embaixo pelos separadores (' · '), escolhendo o corte em que as duas metades
    ocupam a fração mais parecida do seu arco (largura medida na fonte). Sem separador, divide por palavra."""
    marca = sep.strip() or "·"
    partes = [x.strip() for x in texto.split(marca) if x.strip()]
    junta = f" {marca} "
    if len(partes) < 2:
        partes, junta = texto.split(), " "
    if len(partes) < 2:
        return _sem_pontas(texto, marca), ""
    melhor = None
    for i in range(1, len(partes)):
        cima, baixo = junta.join(partes[:i]), junta.join(partes[i:])
        dif = abs(f.largura(cima, 1.0) / arco_cima - f.largura(baixo, 1.0) / arco_baixo)
        if melhor is None or dif < melhor[0]:
            melhor = (dif, cima, baixo)
    return melhor[1], melhor[2]


def _selo(p, ctx, uid):
    """Selo circular em DOIS arcos, como selo de verdade: o texto de cima corre no arco superior no sentido horário
    (topo das letras para fora); o de baixo corre no arco inferior no sentido anti-horário, da esquerda para a direita
    com as letras em pé (topo para o centro). Os dois ocupam a mesma faixa do anel; nas 3h e nas 9h fica um separador
    (estrela ou ponto que exista na fonte, senão '·'). Cada arco FECHA pela medida: o espaçamento entre letras é
    calculado para o texto preencher exatamente o arco entre os separadores (texto curto demais fica centrado com o
    espaçamento máximo, sem se espalhar pelo arco). No centro, o logo do cliente (ctx.logo_png) ou um texto.
    params: texto | texto_de (sem texto_baixo, é dividido em dois pelos ' · ', equilibrando a largura medida);
    texto_baixo (opcional; '' deixa o arco de baixo vazio); diametro 320 (ou `largura`/`altura`: o menor dos dois vira o diâmetro);
    anel 15% do diâmetro; fonte 'display';
    peso ctx; cor 'marca'; fundo None; contorno True; espessura 1,5; separador ' · '; separador_anel (padrão: ★, •
    ou ·, o primeiro que a fonte tiver); espacamento_min 0,02 em; espacamento_max 0,45 em; centro 'logo' (quando há
    logo) | 'texto' | None; centro_texto; logo_cor (padrão = cor) | logo_original True; recorte (do logo); giro 0."""
    texto = _texto(p, ctx, caixa_alta=p.get("caixa_alta", True))
    sep = p.get("separador", " · ")
    marca = sep.strip() or "·"
    if p.get("diametro") is None and (p.get("largura") is not None or p.get("altura") is not None):
        D = min(float(p[k]) for k in ("largura", "altura") if p.get(k) is not None)     # a medida da tinta: o menor dos dois é o diâmetro
    else:
        D = float(p.get("diametro", 320))
    R = cx = cy = D / 2
    anel = float(p.get("anel", D * 0.15)); margem = float(p.get("margem", anel * 0.2))
    esp = float(p.get("espessura", 1.5))
    f = fonte(ctx, p.get("fonte", "display"), p.get("peso"))
    kap = f.cap / f.upem
    t_min, t_max = float(p.get("espacamento_min", 0.02)), float(p.get("espacamento_max", 0.45))
    if p.get("texto_baixo") is not None:
        cima = _sem_pontas(texto, marca)
        baixo = _sem_pontas(_texto(p, ctx, "texto_baixo", p.get("caixa_alta", True)), marca) if str(p["texto_baixo"]).strip() else ""
    else:
        cima, baixo = _dividir_em_dois(texto, sep, f, R - margem - kap * (anel - 2 * margem) / kap, R - margem)
    # o que sai da faixa das maiúsculas: acento e cedilha. Para fora: acento do texto de cima e cedilha do de baixo
    # (letras em pé, topo para o centro); para dentro, o contrário. As duas faixas de maiúsculas ficam alinhadas e a
    # tinta inteira fica entre as margens (a cedilha de EDIÇÃO não encosta no contorno).
    _, c0, _, c1 = f.caixa_tinta(cima, 1.0)
    _, b0, _, b1 = f.caixa_tinta(baixo, 1.0) if baixo else (0.0, 0.0, 0.0, kap)
    fora1 = max(0.0, c1 - kap, -b0)
    dentro1 = max(0.0, -c0, b1 - kap)
    s_banda = (anel - 2 * margem) / (kap + fora1 + dentro1)
    sep_anel = p.get("separador_anel") or next((c for c in SEPARADORES_ANEL if ord(c) in f.cmap), "·")
    f.glifos(sep_anel)                                   # separador sem glifo na fonte = erro nomeando o caractere
    sx0, sy0, sx1, sy1 = f.caixa_tinta(sep_anel, 1.0)
    vao1 = f.largura(" ", 1.0) + 0.12                   # entre o separador e o texto: um espaço com tracking normal

    def geometria(s):
        r_t = _r(R - margem - fora1 * s - kap * s)       # linha de base de cima: letras para fora
        r_b = _r(R - margem - fora1 * s)                 # linha de base de baixo: letras para dentro
        r_m = R - margem - fora1 * s - kap * s / 2       # meio da faixa das maiúsculas: onde ficam os separadores
        meia = (sx1 - sx0) * s / 2
        e_t = r_t * meia / r_m + vao1 * s                # arco reservado em cada ponta, para o separador e o vão
        e_b = r_b * meia / r_m + vao1 * s
        return r_t, r_b, r_m, e_t, e_b, math.pi * r_t - 2 * e_t, math.pi * r_b - 2 * e_b

    a_c, n_c = f.largura(cima, 1.0), len(cima)
    a_b, n_b = (f.largura(baixo, 1.0), len(baixo)) if baixo else (0.0, 0)

    def cabe(s):
        g = geometria(s)
        return g[5] >= s * (a_c + n_c * t_min) and (not baixo or g[6] >= s * (a_b + n_b * t_min))

    s = min(s_banda, float(p.get("tamanho") or 1e9))
    if not cabe(s):
        lo, hi = 0.0, s
        for _ in range(60):
            meio = (lo + hi) / 2
            lo, hi = (meio, hi) if cabe(meio) else (lo, meio)
        s = lo
    s = math.floor(s * 1000) / 1000                      # para baixo: continua cabendo depois de arredondar
    if s < 4:
        raise ValueError(f"selo de {D:g}px com anel de {anel:g}px não comporta o texto (corpo {s:g}px): aumente o diâmetro ou o anel")
    r_t, r_b, r_m, e_t, e_b, L_t, L_b = geometria(s)

    def arco(txt, L, e):
        """(espaçamento, comprimento-alvo, início). Alvo = o arco inteiro entre os separadores quando o texto o
        preenche; o próprio texto quando é curto demais e fica centrado no espaçamento máximo."""
        a, n = f.largura(txt, s), len(txt)
        preenche = (L - a) / n <= t_max * s
        ls = _r((L - a) / n if preenche else t_max * s)
        T = a + n * ls
        return ls, (L if preenche else T), e + (L - T + ls) / 2   # início: tinta centrada (o espaçamento final não aparece)

    cor = _cor(p.get("cor"), ctx)
    partes = []
    if p.get("fundo"):
        partes.append(f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(R)}" fill="{_cor(p["fundo"], ctx)}"/>')
    r_dentro = r_t - dentro1 * s - margem
    if p.get("contorno", True):
        partes.append(f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(R - esp / 2 - 0.5)}" fill="none" stroke="{cor}" stroke-width="{_n(esp)}"/>')
        partes.append(f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r_dentro)}" fill="none" stroke="{cor}" stroke-width="{_n(esp)}"/>')
    textos_anel = []
    ls_c, alvo_c, ini_c = arco(cima, L_t, e_t)
    textos_anel.append(f'<path id="cima-{uid}" d="M {_n(cx - r_t)} {_n(cy)} A {_n(r_t)} {_n(r_t)} 0 0 1 {_n(cx + r_t)} {_n(cy)}" fill="none"/>'
                       f'<text data-arco="cima" data-alvo="{_n(alvo_c)}" fill="{cor}" style="{_estilo(f, s, ls_c)}"><textPath href="#cima-{uid}" '
                       f'startOffset="{_n(ini_c)}">{_esc(cima)}</textPath></text>')
    if baixo:
        ls_b, alvo_b, ini_b = arco(baixo, L_b, e_b)
        textos_anel.append(f'<path id="baixo-{uid}" d="M {_n(cx - r_b)} {_n(cy)} A {_n(r_b)} {_n(r_b)} 0 0 0 {_n(cx + r_b)} {_n(cy)}" fill="none"/>'
                           f'<text data-arco="baixo" data-alvo="{_n(alvo_b)}" fill="{cor}" style="{_estilo(f, s, ls_b)}"><textPath href="#baixo-{uid}" '
                           f'startOffset="{_n(ini_b)}">{_esc(baixo)}</textPath></text>')
    sx0, sy0, sx1, sy1 = f.caixa_tinta(sep_anel, s)
    for ang, px in ((90, cx + r_m), (-90, cx - r_m)):    # topo do separador para fora, como as letras de cima
        textos_anel.append(f'<text data-arco="separador" x="{_n(-(sx0 + sx1) / 2)}" y="{_n((sy0 + sy1) / 2)}" '
                           f'transform="translate({_n(px)} {_n(cy)}) rotate({ang})" fill="{cor}" style="{_estilo(f, s)}">{_esc(sep_anel)}</text>')
    giro = float(p.get("giro", 0))
    anel_svg = "".join(textos_anel)
    partes.append(f'<g transform="rotate({_n(giro)} {_n(cx)} {_n(cy)})">{anel_svg}</g>' if giro else anel_svg)
    fontes, textos = [f.familia], [t for t in (cima, baixo) if t]
    rc = r_dentro - esp - margem * 0.5
    centro = p.get("centro", "logo" if ctx.get("logo_png") else None)
    if centro == "logo":
        im, cob = _simbolo(p.get("png") or ctx.get("logo_png"), p.get("recorte"))
        asp = im.width / im.height
        lw = 2 * 0.84 * rc / math.sqrt(1 + 1 / asp ** 2); lh = lw / asp
        img = im if p.get("logo_original") else _tingir(cob, _cor(p.get("logo_cor"), ctx, p.get("cor") or "marca"))
        partes.append(f'<image href="{_png_uri(img, round(lw * 2))}" x="{_n(cx - lw / 2)}" y="{_n(cy - lh / 2)}" '
                      f'width="{_n(lw)}" height="{_n(lh)}" preserveAspectRatio="xMidYMid meet"/>')
    elif centro == "texto":
        ct = _texto(p, ctx, "centro_texto", p.get("caixa_alta", True))
        fc = fonte(ctx, p.get("fonte_centro", p.get("fonte", "display")), p.get("peso_centro", p.get("peso")))
        sc = _r(min(1.3 * rc / fc.largura(ct, 1.0), 0.62 * rc / (fc.cap / fc.upem)))
        partes.append(f'<text x="{_n(cx)}" y="{_n(cy + fc.cap_px(sc) / 2)}" text-anchor="middle" fill="{cor}" style="{_estilo(fc, sc)}">{_esc(ct)}</text>')
        fontes.append(fc.familia); textos.append(ct)
    elif centro is not None:
        raise ValueError(f"centro `{centro}`: use logo, texto ou None")
    Di = _inteiro(D)
    return dict(svg=_svg(Di, Di, "".join(partes), "selo", uid), w=Di, h=Di, texto="\n".join(textos), fontes=list(dict.fromkeys(fontes)))


def _grade(W, H, c, angulo):
    if not angulo:
        xs, ys = np.meshgrid(np.arange(c / 2, W, c), np.arange(c / 2, H, c))
        return xs.ravel(), ys.ravel()
    t = math.radians(angulo); D = math.hypot(W, H) / 2 + c
    u, v = np.meshgrid(np.arange(-D, D, c), np.arange(-D, D, c))
    xs = W / 2 + u * math.cos(t) - v * math.sin(t); ys = H / 2 + u * math.sin(t) + v * math.cos(t)
    dentro = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
    return xs[dentro], ys[dentro]


def _meio_tom_simbolo(p, ctx, uid):
    """Símbolo do cliente refeito em pontos de meio-tom (referência web-nike-run-sp-25-07), uma cor só, vetorial.
    params: png (padrão ctx.logo_png); recorte [x0, y0, x1, y1]; largura 600 (ou altura: a outra segue o símbolo); celula 14 (passo da grade);
    modo 'densidade' (raio pela cobertura) | 'led' (ponto cheio ou nada); angulo 0 (45 = retícula clássica);
    minimo 0,06; cor 'marca'; grade_fundo False (pontos apagados na grade inteira, mesma cor a 16%)."""
    from scipy.ndimage import map_coordinates, uniform_filter
    im, cob = _simbolo(p.get("png") or ctx.get("logo_png"), p.get("recorte"))
    asp = im.width / im.height
    if p.get("altura") is not None:       # medida da tinta: a altura pedida dá a largura pela proporção do símbolo; com as duas, cabe nas duas
        W = float(p["altura"]) * asp if p.get("largura") is None else min(float(p["largura"]), float(p["altura"]) * asp)
    else:
        W = float(p.get("largura", 600))
    H = W * im.height / im.width
    c = float(p.get("celula", 14)); modo = p.get("modo", "densidade")
    if modo not in ("densidade", "led"):
        raise ValueError(f"modo `{modo}`: use densidade ou led")
    alvo = np.asarray(Image.fromarray((cob * 255).astype(np.uint8)).resize((max(1, round(W)), max(1, round(H))), Image.BOX), float) / 255
    media = uniform_filter(alvo, size=max(1, int(round(c))), mode="constant")
    xs, ys = _grade(W, H, c, float(p.get("angulo", 0)))
    if len(xs) > 20000:
        raise ValueError(f"meio-tom com {len(xs)} pontos: aumente a célula")
    v = map_coordinates(media, [ys, xs], order=1, mode="constant")
    minimo = float(p.get("minimo", 0.06))
    if modo == "led":
        raios = np.where(v >= 0.5, c * 0.36, 0.0)
    else:
        raios = np.where(v >= minimo, (c / 2) * 0.96 * np.sqrt(np.clip(v, 0, 1)), 0.0)
    cor = _cor(p.get("cor"), ctx)
    cheios = "".join(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(r)}"/>' for x, y, r in zip(xs, ys, raios) if r > 0.25)
    corpo = ""
    if p.get("grade_fundo"):
        apagados = "".join(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(c * 0.2)}"/>' for x, y, r in zip(xs, ys, raios) if r <= 0.25)
        corpo += f'<g fill="{cor}" fill-opacity="0.16">{apagados}</g>'
    corpo += f'<g fill="{cor}">{cheios}</g>'
    return dict(svg=_svg(_inteiro(W), _inteiro(H), corpo, "meio-tom-simbolo", uid), w=_inteiro(W), h=_inteiro(H), texto="", fontes=[])


ARRANJOS = {
    "grade": [(0.5, 0.5, 0)],
    "meia-queda": [(0.25, 0.25, 0), (0.75, 0.75, 180)],
    "alternado": [(0.25, 0.25, 0), (0.75, 0.25, 180), (0.25, 0.75, 180), (0.75, 0.75, 0)],
}


def _fase_vazia(cob, mw, mh, T, instancias, giro, n=128):
    """Deslocamento (ox, oy) da grade que faz as bordas do tile passarem onde há menos tinta. O desenho infinito é o
    mesmo para qualquer deslocamento; só muda onde o tile é cortado. Borda no vazio = emenda que não depende de
    antialias nem de arredondamento quando o navegador repete o tile."""
    esc = n / T
    base = Image.fromarray((np.clip(cob, 0, 1) * 255).astype(np.uint8)).resize((max(1, round(mw * esc)), max(1, round(mh * esc))), Image.BOX)
    M = np.zeros((n, n))
    for fx, fy, rot in instancias:
        a = (rot + giro) % 360
        st = np.asarray(base.rotate(-a, expand=True, resample=Image.BILINEAR) if a else base, float) / 255
        y0 = int(round(fy * n - st.shape[0] / 2)); x0 = int(round(fx * n - st.shape[1] / 2))
        yy, xx = np.mgrid[0:st.shape[0], 0:st.shape[1]]
        np.add.at(M, ((y0 + yy) % n, (x0 + xx) % n), st)
    col, lin = M.sum(0), M.sum(1)
    ox = int(np.argmin(col + np.roll(col, 1)))   # a borda fica entre a coluna ox-1 e ox
    oy = int(np.argmin(lin + np.roll(lin, 1)))
    return ox / esc, oy / esc


def _pattern_simbolo(p, ctx, uid):
    """Tile seamless derivado do contorno do logo do cliente. Seamless por construção: cada cópia do símbolo é
    desenhada também deslocada de um lado do tile para cima, baixo, esquerda e direita, então o que sai por uma borda
    entra pela oposta; e a grade é deslocada para a borda do tile cair onde há menos tinta (fase 'vazia'). Com
    `area` = [W, H] devolve a área já preenchida (vetorial, sem <pattern>, que o PDF poderia rasterizar).
    params: png; recorte; lado 240; escala 0,56 (lado maior do símbolo / lado do tile); arranjo 'meia-queda' |
    'grade' | 'alternado'; estilo 'contorno' | 'chapado'; traco 1,5; cor 'marca'; opacidade 1; giro 0; suavizar 1;
    fase 'vazia' | [ox, oy] em px; area None."""
    _, cob = _simbolo(p.get("png") or ctx.get("logo_png"), p.get("recorte"))
    T = float(p.get("lado", 240))
    d, mw, mh = _contorno(cob, float(p.get("escala", 0.56)) * T, float(p.get("suavizar", 1.0)))
    arranjo = p.get("arranjo", "meia-queda")
    if arranjo not in ARRANJOS:
        raise ValueError(f"arranjo `{arranjo}`: use {', '.join(ARRANJOS)}")
    estilo = p.get("estilo", "contorno")
    cor = _cor(p.get("cor"), ctx)
    if estilo == "contorno":
        pintura = f'fill="none" stroke="{cor}" stroke-width="{_n(p.get("traco", 1.5))}" stroke-linejoin="round"'
    elif estilo == "chapado":
        pintura = f'fill="{cor}" fill-rule="evenodd"'
    else:
        raise ValueError(f"estilo `{estilo}`: use contorno ou chapado")
    op = float(p.get("opacidade", 1))
    giro = float(p.get("giro", 0))
    fase = p.get("fase", "vazia")
    if fase == "vazia":
        ox, oy = _fase_vazia(cob, mw, mh, T, ARRANJOS[arranjo], giro)
    elif isinstance(fase, (list, tuple)) and len(fase) == 2:
        ox, oy = float(fase[0]), float(fase[1])
    else:
        raise ValueError(f"fase `{fase}`: use 'vazia' ou [ox, oy]")
    defs = f'<defs><path id="m-{uid}" d="{d}" transform="translate({_n(-mw / 2)} {_n(-mh / 2)})"/></defs>'
    area = p.get("area")
    if area is None and (p.get("largura") is not None or p.get("altura") is not None):      # medida pedida = a área que o padrão preenche
        area = [float(p.get("largura") or p["altura"]), float(p.get("altura") or p["largura"])]
    W, H = (float(area[0]), float(area[1])) if area else (T, T)
    celulas_x = range(-1, int(math.ceil(W / T)) + 2) if area else (-1, 0, 1, 2)
    celulas_y = range(-1, int(math.ceil(H / T)) + 2) if area else (-1, 0, 1, 2)
    alcance = math.hypot(mw, mh) / 2 + 2       # raio que o símbolo ocupa em volta do centro, girado ou não
    usos = []
    for i in celulas_x:
        for j in celulas_y:
            for fx, fy, rot in ARRANJOS[arranjo]:
                x, y = (i + fx) * T - ox, (j + fy) * T - oy
                if x + alcance < 0 or y + alcance < 0 or x - alcance > W or y - alcance > H:
                    continue   # cópia que não encosta na área
                usos.append(f'<use href="#m-{uid}" transform="translate({_n(x)} {_n(y)}) rotate({_n(rot + giro)})"/>')
    corpo = defs + f'<g {pintura}' + (f' opacity="{_n(op)}"' if op < 1 else "") + f'>{"".join(usos)}</g>'
    return dict(svg=_svg(_inteiro(W), _inteiro(H), corpo, "pattern-simbolo", uid), w=_inteiro(W), h=_inteiro(H), texto="", fontes=[])


def _curva(c):
    tipo = c.get("tipo", "orla"); n = int(c.get("pontos", 11))
    t = np.linspace(0, 1, n)
    if tipo == "senoide":
        x, y = t, float(c.get("amplitude", 0.16)) * np.sin(2 * math.pi * float(c.get("ondas", 1.5)) * t + float(c.get("fase", 0)))
    elif tipo == "orla":
        rng = np.random.default_rng(int(c.get("semente", 7)))
        fases = rng.uniform(0, 2 * math.pi, 3)
        y = sum(a * np.sin(2 * math.pi * fq * t + fa) for a, fq, fa in zip((0.12, 0.05, 0.025), (0.7, 1.9, 3.6), fases))
        x = t + 0.012 * np.sin(2 * math.pi * 2.5 * t + fases[0])
    elif tipo == "laco":
        th = np.linspace(0, 2 * math.pi, n, endpoint=False)
        x = np.cos(th) * (1 + 0.18 * np.cos(3 * th)); y = 0.55 * np.sin(th) * (1 + 0.12 * np.sin(2 * th))
    elif tipo == "lissajous":
        x = np.sin(2 * math.pi * float(c.get("a", 1)) * t + float(c.get("delta", math.pi / 2)))
        y = 0.6 * np.sin(2 * math.pi * float(c.get("b", 2)) * t)
    else:
        raise ValueError(f"curva `{tipo}`: use orla, senoide, laco ou lissajous (ou passe `pontos`)")
    return np.column_stack([x, y]), tipo == "laco"


def _bezier_catmull(P, fechada):
    n = len(P); segs = []
    for i in range(n if fechada else n - 1):
        p0 = P[(i - 1) % n] if (fechada or i > 0) else P[i]
        p1, p2 = P[i], P[(i + 1) % n]
        p3 = P[(i + 2) % n] if (fechada or i + 2 < n) else P[(i + 1) % n]
        segs.append((p1, p1 + (p2 - p0) / 6, p2 - (p3 - p1) / 6, p2))
    return segs


def _amostrar(segs, k=48):
    t = np.linspace(0, 1, k, endpoint=False)[:, None]
    pts = [((1 - t) ** 3) * a + 3 * ((1 - t) ** 2) * t * b + 3 * (1 - t) * t * t * c + t ** 3 * d for a, b, c, d in segs]
    pts = np.vstack(pts + [segs[-1][3][None]])
    cum = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    return pts, cum


def _no_comprimento(pts, cum, s):
    i = int(np.clip(np.searchsorted(cum, s), 1, len(pts) - 1))
    a, b = pts[i - 1], pts[i]
    t = 0.0 if cum[i] == cum[i - 1] else (s - cum[i - 1]) / (cum[i] - cum[i - 1])
    tg = b - a; tg = tg / (np.hypot(*tg) or 1)
    return a + (b - a) * t, tg


def _km(v):
    return (f"{v:.1f}".rstrip("0").rstrip(".")).replace(".", ",")


def _linha_percurso(p, ctx, uid):
    """Traço do percurso com marcos de km (referências web-nike-run-sp-25-05 e web-boat-mussoorie-25-13). A linha
    passa por `pontos` ([[x, y], ...], qualquer escala) ou segue uma curva paramétrica; os marcos caem pela distância
    medida ao longo da curva. params: pontos | curva {tipo: orla|senoide|laco|lissajous, ...}; largura 900; altura 500 (com
    uma só das duas, a outra segue a proporção do traçado e a medida é a da tinta);
    margem 56; distancia_km 10; marco_km automático; cor 'marca'; cor_marco = cor; cor_rotulo 'texto'; espessura 4;
    raio 5; rotulos True; rotulo '{km} KM'; fonte 'corpo'; peso 600; tamanho 15."""
    margem = float(p.get("margem", 56))
    if p.get("pontos"):
        P = np.asarray(p["pontos"], float); fechada = bool(p.get("fechada", False))
    else:
        P, fechada = _curva(p.get("curva") or {})
    if len(P) < 2:
        raise ValueError("linha-percurso precisa de pelo menos 2 pontos")
    mn, mx = P.min(0), P.max(0); span = np.maximum(mx - mn, 1e-9)
    if (p.get("largura") is None) != (p.get("altura") is None):
        # uma medida só (a composição pede a tinta): a outra segue a proporção do traçado, em vez de um padrão que o espremeria
        if p.get("largura") is not None:
            W = float(p["largura"]); H = (W - 2 * margem) * span[1] / span[0] + 2 * margem
        else:
            H = float(p["altura"]); W = (H - 2 * margem) * span[0] / span[1] + 2 * margem
    else:
        W, H = float(p.get("largura", 900)), float(p.get("altura", 500))
    esc = min((W - 2 * margem) / span[0], (H - 2 * margem) / span[1])
    P = (P - mn) * esc + np.array([(W - span[0] * esc) / 2, (H - span[1] * esc) / 2])
    segs = _bezier_catmull(list(P), fechada)
    d = f"M {_n(segs[0][0][0])} {_n(segs[0][0][1])} " + " ".join(
        f"C {_n(b[0])} {_n(b[1])} {_n(c[0])} {_n(c[1])} {_n(e[0])} {_n(e[1])}" for _, b, c, e in segs)
    pts, cum = _amostrar(segs)
    total = float(p.get("distancia_km", 10))
    if total <= 0:
        raise ValueError("distancia_km precisa ser maior que zero")
    passo = float(p.get("marco_km") or next((q for q in (0.5, 1, 2, 2.5, 5, 10, 20, 25, 50) if total / q <= 8), total))
    marcos = list(np.arange(0, total + 1e-9, passo))
    if abs(marcos[-1] - total) > 1e-6:
        marcos.append(total)
    cor = _cor(p.get("cor"), ctx); cor_m = _cor(p.get("cor_marco"), ctx, p.get("cor") or "marca")
    cor_t = _cor(p.get("cor_rotulo"), ctx, "texto")
    esp, raio = float(p.get("espessura", 4)), float(p.get("raio", 5))
    partes = [f'<path d="{d}" fill="none" stroke="{cor}" stroke-width="{_n(esp)}" stroke-linecap="round" stroke-linejoin="round"/>']
    f = fonte(ctx, p.get("fonte", "corpo"), p.get("peso", 600)) if p.get("rotulos", True) else None
    s = _r(p.get("tamanho", 15)); ls = _r(0.06 * s)
    centro = pts.mean(0); rotulos = []
    for idx, km in enumerate(marcos):
        pos, tg = _no_comprimento(pts, cum, cum[-1] * km / total)
        ultimo = idx == len(marcos) - 1
        if idx == 0:
            partes.append(f'<circle cx="{_n(pos[0])}" cy="{_n(pos[1])}" r="{_n(raio + 3)}" fill="none" stroke="{cor_m}" stroke-width="{_n(esp * 0.75)}"/>')
        elif ultimo and not fechada:
            partes.append(f'<circle cx="{_n(pos[0])}" cy="{_n(pos[1])}" r="{_n(raio + 3)}" fill="{cor_m}"/>')
        else:
            partes.append(f'<circle cx="{_n(pos[0])}" cy="{_n(pos[1])}" r="{_n(raio)}" fill="{cor_m}"/>')
        if not f or (ultimo and fechada):
            continue
        rot = str(p.get("rotulo", "{km} KM")).replace("{km}", _km(km))
        nrm = np.array([-tg[1], tg[0]])
        if np.dot(nrm, pos - centro) < 0:
            nrm = -nrm
        a = pos + nrm * (raio + 10)
        L = f.largura(rot, s, ls) - ls
        if nrm[0] > 0.38:
            anc, x = "start", min(a[0], W - 2 - L)
        elif nrm[0] < -0.38:
            anc, x = "end", max(a[0], L + 2)
        else:
            anc, x = "middle", min(max(a[0], L / 2 + 2), W - 2 - L / 2)
        cap = f.cap_px(s)
        y = a[1] + (cap if nrm[1] > 0.38 else 0 if nrm[1] < -0.38 else cap / 2)
        y = min(max(y, cap + 2), H - 2)
        partes.append(f'<text x="{_n(x)}" y="{_n(y)}" text-anchor="{anc}" fill="{cor_t}" style="{_estilo(f, s, ls)}">{_esc(rot)}</text>')
        rotulos.append(rot)
    return dict(svg=_svg(_inteiro(W), _inteiro(H), "".join(partes), "linha-percurso", uid), w=_inteiro(W), h=_inteiro(H),
                texto="\n".join(rotulos), fontes=[f.familia] if f and rotulos else [])


def _fios_tecnicos(p, ctx, uid):
    """Fios finos com bolinha que apontam alvos e levam um rótulo (inventário desenhado sobre o objeto, referência
    web-deck-tomasello-tc2025-21). params: alvos [{x, y, rotulo, lado: dir|esq (automático), desce: False}];
    largura 1920; altura 1080; cor 'texto'; espessura 1,5; raio 5; diagonal 56; horizontal 140; fonte 'corpo';
    peso 600; tamanho 16; espacamento 0,08 em; caixa_alta True."""
    alvos = p.get("alvos") or []
    if not alvos:
        raise ValueError("fios-tecnicos precisa de `alvos`: [{x, y, rotulo}]")
    W, H = float(p.get("largura", 1920)), float(p.get("altura", 1080))
    cor = _cor(p.get("cor"), ctx, "texto"); esp = float(p.get("espessura", 1.5)); raio = float(p.get("raio", 5))
    dg, hz = float(p.get("diagonal", 56)), float(p.get("horizontal", 140))
    f = fonte(ctx, p.get("fonte", "corpo"), p.get("peso", 600))
    s = _r(p.get("tamanho", 16)); ls = _r(float(p.get("espacamento", 0.08)) * s); cap = f.cap_px(s)
    partes, rotulos = [], []
    for a in alvos:
        x, y = float(a["x"]), float(a["y"])
        rot = _texto(a, ctx, "rotulo", p.get("caixa_alta", True))
        L = f.largura(rot, s, ls) - ls
        k = dg / math.sqrt(2)
        cabe_dir = x + k + hz + 10 + L <= W - 4
        lado = a.get("lado") or ("dir" if cabe_dir else "esq")
        sx = 1 if lado == "dir" else -1
        sy = 1 if a.get("desce", y - k - cap < 4) else -1
        p1 = (x + sx * k, y + sy * k); p2 = (p1[0] + sx * hz, p1[1])
        xt = p2[0] + sx * 10
        if (sx > 0 and xt + L > W - 2) or (sx < 0 and xt - L < 2):
            raise ValueError(f"rótulo `{rot}` não cabe na área ({L:.0f}px): mude o lado, o alvo ou o tamanho")
        partes.append(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(raio)}" fill="{cor}"/>'
                      f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(raio * 2.2)}" fill="none" stroke="{cor}" stroke-width="{_n(esp * 0.7)}"/>'
                      f'<path d="M {_n(x + sx * raio * 0.7)} {_n(y + sy * raio * 0.7)} L {_n(p1[0])} {_n(p1[1])} L {_n(p2[0])} {_n(p2[1])}" '
                      f'fill="none" stroke="{cor}" stroke-width="{_n(esp)}"/>'
                      f'<text x="{_n(xt)}" y="{_n(p2[1] + cap / 2)}" text-anchor="{"start" if sx > 0 else "end"}" fill="{cor}" '
                      f'style="{_estilo(f, s, ls)}">{_esc(rot)}</text>')
        rotulos.append(rot)
    return dict(svg=_svg(_inteiro(W), _inteiro(H), "".join(partes), "fios-tecnicos", uid), w=_inteiro(W), h=_inteiro(H),
                texto="\n".join(rotulos), fontes=[f.familia])


def _etiqueta_corpo(p, ctx):
    texto = _texto(p, ctx, caixa_alta=p.get("caixa_alta", True))
    f = fonte(ctx, p.get("fonte", "corpo"), p.get("peso", 700))
    s = _r(p.get("tamanho", 16)); ls = _r(float(p.get("espacamento", 0.12)) * s)
    tinta = f.largura(texto, s, ls) - ls           # o espaçamento depois da última letra não aparece
    pad = float(p.get("respiro", s * 0.9)); h = _r(p.get("altura") or s * 2.1)
    forma = p.get("forma", "retangulo")
    ponta = h * 0.5 if forma == "seta" else 0.0
    w = _r(tinta + 2 * pad + ponta)
    fundo = _cor(p.get("fundo"), ctx, "marca"); cor = _cor(p.get("cor"), ctx, "escuro")
    if forma == "pilula":
        caixa = f'<rect width="{_n(w)}" height="{_n(h)}" rx="{_n(h / 2)}" fill="{fundo}"/>'
    elif forma == "seta":
        caixa = f'<path d="M 0 0 L {_n(w - ponta)} 0 L {_n(w)} {_n(h / 2)} L {_n(w - ponta)} {_n(h)} L 0 {_n(h)} Z" fill="{fundo}"/>'
    elif forma == "retangulo":
        caixa = f'<rect width="{_n(w)}" height="{_n(h)}" rx="{_n(p.get("raio", 0))}" fill="{fundo}"/>'
    else:
        raise ValueError(f"forma `{forma}`: use retangulo, pilula ou seta")
    corpo = caixa + f'<text x="{_n(pad)}" y="{_n(h / 2 + f.cap_px(s) / 2)}" fill="{cor}" style="{_estilo(f, s, ls)}">{_esc(texto)}</text>'
    return corpo, w, h, f, texto


def _etiqueta(p, ctx, uid):
    """Etiqueta (tab) com texto vivo; a largura sai da medida do texto. params: texto; tamanho 16; fonte 'corpo';
    peso 700; espacamento 0,12 em; respiro 0,9 x tamanho; altura 2,1 x tamanho; forma 'retangulo' | 'pilula' | 'seta';
    fundo 'marca'; cor 'escuro'; raio 0; caixa_alta True; largura (medida da etiqueta: o tamanho do texto sai dela; vale
    sozinha ou com `altura`, que continua a altura da caixa)."""
    if p.get("largura") is not None:
        base = {k: v for k, v in p.items() if k != "largura"}
        alvo = float(p["largura"])
        if alvo <= 0:
            raise ValueError(f"`largura` precisa ser maior que zero (recebi {alvo:g})")
        s = _secante(lambda t: _etiqueta_corpo(dict(base, tamanho=t), ctx)[1], alvo, float(base.get("tamanho", 16)), tol=0.2)
        p = dict(base, tamanho=s)
    corpo, w, h, f, texto = _etiqueta_corpo(p, ctx)
    return dict(svg=_svg(_inteiro(w), _inteiro(h), corpo, "etiqueta", uid), w=_inteiro(w), h=_inteiro(h), texto=texto, fontes=[f.familia])


def _moldura(p, ctx, uid):
    """Moldura fina (ou só as marcas de canto) com etiqueta opcional encostada no canto. params: largura 600;
    altura 400; espessura 1,5; cor 'marca'; raio 0; cantos 'cheio' | 'marcas'; canto 8% do menor lado;
    etiqueta {texto, posicao sup-esq|sup-dir|inf-esq|inf-dir, recuo 24, ...parâmetros da etiqueta} | texto."""
    W, H = float(p.get("largura", 600)), float(p.get("altura", 400)); esp = float(p.get("espessura", 1.5)); o = esp / 2
    cor = _cor(p.get("cor"), ctx)
    partes = []
    if p.get("cantos", "cheio") == "marcas":
        c = float(p.get("canto", min(W, H) * 0.08))
        for x, y, sx, sy in ((o, o, 1, 1), (W - o, o, -1, 1), (o, H - o, 1, -1), (W - o, H - o, -1, -1)):
            partes.append(f'<path d="M {_n(x)} {_n(y + sy * c)} L {_n(x)} {_n(y)} L {_n(x + sx * c)} {_n(y)}" fill="none" '
                          f'stroke="{cor}" stroke-width="{_n(esp)}"/>')
    else:
        partes.append(f'<rect x="{_n(o)}" y="{_n(o)}" width="{_n(W - esp)}" height="{_n(H - esp)}" rx="{_n(p.get("raio", 0))}" '
                      f'fill="none" stroke="{cor}" stroke-width="{_n(esp)}"/>')
    texto, fontes = "", []
    etq = p.get("etiqueta")
    if etq:
        etq = {"texto": etq} if isinstance(etq, str) else dict(etq)
        corpo, ew, eh, f, texto = _etiqueta_corpo(etq, ctx)
        pos = etq.get("posicao", "sup-esq"); recuo = float(etq.get("recuo", 24))
        x = recuo if pos.endswith("esq") else W - recuo - ew
        y = 0 if pos.startswith("sup") else H - eh
        partes.append(f'<g transform="translate({_n(x)} {_n(y)})">{corpo}</g>')
        fontes = [f.familia]
    return dict(svg=_svg(_inteiro(W), _inteiro(H), "".join(partes), "moldura", uid), w=_inteiro(W), h=_inteiro(H), texto=texto, fontes=fontes)


def _numeral(p, ctx, uid):
    """Numeral gigante, cheio ou fantasma (o ano ou o número da edição como sistema, referências
    web-corrida-integracao-26-03 e web-nike-shanghai-23-01). A caixa do SVG é a tinta do número, medida na fonte:
    `altura` é a altura real dos algarismos (ou `largura`: a largura da tinta; a altura sai dela, e com as duas cabe nas duas).
    params: texto (ex.: '2027', '02'); altura 400; estilo 'cheio' |
    'contorno' | 'fantasma'; cor 'marca'; espessura 2 (contorno); opacidade 0,12 (fantasma); fonte 'display'; peso ctx;
    espacamento 0 em."""
    texto = _texto(p, ctx, caixa_alta=False)
    f = fonte(ctx, p.get("fonte", "display"), p.get("peso"))
    t_em = float(p.get("espacamento", 0))
    x0, y0, x1, y1 = f.caixa_tinta(texto, 1.0, t_em)
    if y1 - y0 <= 0:
        raise ValueError(f"numeral sem tinta: {texto!r}")
    estilo = p.get("estilo", "cheio"); esp = float(p.get("espessura", 2))
    if p.get("largura") is not None:
        # medida da tinta: a altura que dá a largura pedida (a proporção vem da fonte; o contorno acrescenta a espessura à tinta)
        alt_l = (float(p["largura"]) - (esp if estilo == "contorno" else 0.0)) * (y1 - y0) / (x1 - x0)
        altura = alt_l if p.get("altura") is None else min(float(p["altura"]), alt_l)
    else:
        altura = float(p.get("altura", 400))
    s = _r(altura / (y1 - y0)); ls = _r(t_em * s)
    x0, y0, x1, y1 = f.caixa_tinta(texto, s, ls)
    cor = _cor(p.get("cor"), ctx)
    pad = esp / 2 + 1 if estilo == "contorno" else 1
    w, h = _inteiro(x1 - x0 + 2 * pad), _inteiro(y1 - y0 + 2 * pad)
    if estilo == "cheio":
        pintura = f'fill="{cor}"'
    elif estilo == "contorno":
        pintura = f'fill="none" stroke="{cor}" stroke-width="{_n(esp)}" stroke-linejoin="round"'
    elif estilo == "fantasma":
        pintura = f'fill="{cor}" fill-opacity="{_n(p.get("opacidade", 0.12))}"'
    else:
        raise ValueError(f"estilo `{estilo}`: use cheio, contorno ou fantasma")
    corpo = f'<text x="{_n(pad - x0)}" y="{_n(pad + y1)}" {pintura} style="{_estilo(f, s, ls)}">{_esc(texto)}</text>'
    extra = esp if estilo == "contorno" else 0.0      # o traço do contorno engorda a tinta em meia espessura de cada lado
    return dict(svg=_svg(w, h, corpo, "numeral", uid), w=w, h=h, texto=texto, fontes=[f.familia],
                tinta=[1.0, 1.0, 1.0 + (x1 - x0) + extra, 1.0 + (y1 - y0) + extra])


def _tipo_textura(p, ctx, uid):
    """Palavra repetida em contorno com eco, do cheio ao vazio (referência web-lambe-ironman-itau-03): a cópia do meio
    é cheia, as outras só contorno e somem com a distância; abaixo do meio, espelhadas. params: texto; repeticoes 7;
    tamanho 120 (ou `largura`/`altura`, a medida da tinta: o tamanho sai dela); passo 1,12 x altura das maiúsculas; espelhar True; desvanecer True; cor 'marca'; cor_cheio = cor;
    espessura 1,5; fonte 'display'; peso ctx; espacamento 0 em; caixa_alta True."""
    palavra = _texto(p, ctx, caixa_alta=p.get("caixa_alta", True))
    f = fonte(ctx, p.get("fonte", "display"), p.get("peso"))
    s = _r(p.get("tamanho", 120)); ls = _r(float(p.get("espacamento", 0)) * s)
    k = int(p.get("repeticoes", 7))
    if k < 1:
        raise ValueError("repeticoes precisa ser 1 ou mais")
    cap = f.cap_px(s); passo = cap * float(p.get("passo", 1.12)); esp = float(p.get("espessura", 1.5))
    x0, _, x1, _ = f.caixa_tinta(palavra, s, ls)
    pad = esp + 2
    W, H = _inteiro(x1 - x0 + 2 * pad), _inteiro(k * passo + 2 * pad)
    cor = _cor(p.get("cor"), ctx); cheio = _cor(p.get("cor_cheio"), ctx, p.get("cor") or "marca")
    meio = k // 2
    estilo_txt = _estilo(f, s, ls)
    partes = []
    _, ty0, _, ty1 = f.caixa_tinta(palavra, s, ls)
    faixas = []                                 # faixa vertical que a tinta de cada cópia ocupa (as de baixo vão espelhadas)
    for i in range(k):
        dist = abs(i - meio)
        yc = pad + passo * (i + 0.5)
        base = yc + cap / 2
        op = 1.0
        if i == meio:
            pintura = f'fill="{cheio}"'
        else:
            op = 1 - 0.72 * dist / max(1, meio) if p.get("desvanecer", True) else 1
            pintura = f'fill="none" stroke="{cor}" stroke-width="{_n(esp)}" stroke-opacity="{_n(op)}"'
        tr = f' transform="translate(0 {_n(2 * yc)}) scale(1 -1)"' if p.get("espelhar", True) and i > meio else ""
        partes.append(f'<text x="{_n(pad - x0)}" y="{_n(base)}" {pintura}{tr} style="{estilo_txt}">{_esc(palavra)}</text>')
        if op < 0.5:
            continue                            # a tinta só conta o que passa de meia opacidade: a cópia que sumiu no eco não é tinta
        topo, fundo = base - ty1, base - ty0
        if tr:
            topo, fundo = 2 * yc - fundo, 2 * yc - topo
        borda = 0.0 if i == meio else esp / 2   # a cópia só de contorno engorda em meia espessura
        faixas.append((topo - borda, fundo + borda))
    folga = 0.0 if k == 1 else esp / 2
    return dict(svg=_svg(W, H, "".join(partes), "tipo-textura", uid), w=W, h=H, texto=palavra, fontes=[f.familia],
                tinta=[pad - folga, min(a for a, _ in faixas), pad + (x1 - x0) + folga, max(b for _, b in faixas)])


def _segmento_visivel(cx, cy, ang, W, H):
    """Trecho [t0, t1] da reta que passa por (cx, cy) no ângulo `ang` que fica dentro do retângulo [0, W] x [0, H]."""
    dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    t0, t1 = -math.inf, math.inf
    for p0, dd, hi in ((cx, dx, W), (cy, dy, H)):
        if abs(dd) < 1e-12:
            if not 0 <= p0 <= hi:
                return 0.0, 0.0
            continue
        a, b = (0 - p0) / dd, (hi - p0) / dd
        t0, t1 = max(t0, min(a, b)), min(t1, max(a, b))
    return t0, max(t0, t1)


def _linha_que_cobre(f, ciclo, tamanho, espacamento, comprimento):
    """Repete `ciclo` no espaçamento normal até cobrir `comprimento`, corta no primeiro caractere visível que passa do
    fim e então aperta o espaçamento só o necessário (sempre <= o normal, nunca estica) para a linha medir exatamente o
    comprimento. Devolve (linha, espacamento_px)."""
    natural = f.largura(ciclo, tamanho, espacamento)
    longa = ciclo * (int(comprimento // natural) + 2)
    adv = np.asarray(f.avancos(longa)) * tamanho / f.upem + espacamento
    i = min(int(np.searchsorted(np.cumsum(adv), comprimento)), len(longa) - 1)
    while i < len(longa) - 1 and longa[i] == " ":      # a linha não termina em espaço: a tinta vai até a borda
        i += 1
    linha = longa[: i + 1]
    while f.largura(linha, tamanho, espacamento) < comprimento and len(linha) < len(longa):
        linha = longa[: len(linha) + 1]                # garante a cobertura (o kerning do último par mudou a conta)
    ls = math.floor((comprimento - f.largura(linha, tamanho)) / len(linha) * 1000) / 1000
    return linha, ls


def _faixa_diagonal(p, ctx, uid):
    """Faixa diagonal que atravessa a área e sangra nas bordas (o recorte diagonal como grid, referência
    web-deck-tomasello-tc2025), com microtexto opcional correndo por dentro. O texto se repete com ' · ' no tracking
    normal até cobrir o trecho visível e é cortado na borda (a faixa sangra); o espaçamento só aperta, nunca estica,
    para a linha medir exatamente o trecho. params: largura 1920; altura 1080; angulo -12; espessura 120; x 0,5 e y
    0,62 (centro, em fração); cor 'marca'; texto | texto_de (opcional); tamanho 26% da espessura; fonte 'corpo';
    peso 700; cor_texto 'escuro'; espacamento 0,12 em (no máximo 0,12); separador ' · '."""
    W, H = float(p.get("largura", 1920)), float(p.get("altura", 1080))
    ang, e = float(p.get("angulo", -12)), float(p.get("espessura", 120))
    cx, cy = W * float(p.get("x", 0.5)), H * float(p.get("y", 0.62))
    cor = _cor(p.get("cor"), ctx)
    L = 2 * math.hypot(W, H)
    partes = [f'<g transform="translate({_n(cx)} {_n(cy)}) rotate({_n(ang)})">',
              f'<rect x="{_n(-L / 2)}" y="{_n(-e / 2)}" width="{_n(L)}" height="{_n(e)}" fill="{cor}"/>']
    texto, fontes = "", []
    if p.get("texto") or p.get("texto_de"):
        unidade = _texto(p, ctx, caixa_alta=p.get("caixa_alta", True))
        f = fonte(ctx, p.get("fonte", "corpo"), p.get("peso", 700))
        s = _r(p.get("tamanho") or e * 0.26)
        t0, t1 = _segmento_visivel(cx, cy, ang, W, H)
        normal = min(float(p.get("espacamento", 0.12)), 0.12) * s
        if t1 - t0 <= 0:
            raise ValueError("a faixa não passa pela área: mude x, y ou o ângulo")
        linha, ls = _linha_que_cobre(f, unidade + p.get("separador", " · "), s, normal, t1 - t0)
        partes.append(f'<text x="{_n(t0)}" y="{_n(f.cap_px(s) / 2)}" fill="{_cor(p.get("cor_texto"), ctx, "escuro")}" '
                      f'style="{_estilo(f, s, ls)}">{_esc(linha)}</text>')
        texto, fontes = unidade, [f.familia]
    partes.append("</g>")
    return dict(svg=_svg(_inteiro(W), _inteiro(H), "".join(partes), "faixa-diagonal", uid), w=_inteiro(W), h=_inteiro(H),
                texto=texto, fontes=fontes)


def _palavras_evento(ctx):
    ev = ctx.get("evento") or {}
    palavras = [w for w in str(ev.get("nome") or "").split() if len(w) > 1]
    if ev.get("data_inicio"):
        palavras.append(str(ev["data_inicio"])[:4])
    if not palavras:
        raise ValueError("mosaico precisa de `palavras` (ou ctx.evento.nome)")
    return palavras


def _mosaico(p, ctx, uid):
    """Grade de módulos que alterna cor, tipo e pictograma (referências web-lambe-ironman-itau-01 e
    web-corrida-sicredi-25-01). Vizinhos nunca repetem o fundo nem o tipo de módulo; o texto de cada módulo é medido
    para caber. params: colunas 6; linhas 2; modulo 180; vao 0; cores ['marca', 'escuro', 'papel'] (as que a paleta
    tiver); palavras (padrão: nome do evento e ano); simbolo True (contorno do logo como pictograma; png/recorte);
    sequencia (lista de: cor, tipo, simbolo, meio-tom, contorno); semente 7; fonte 'display'; peso ctx. Medida:
    `largura`/`altura` dão o módulo (e o vão, em proporção) que faz a grade medir o pedido; com as duas, cabe nas duas."""
    cols, rows = int(p.get("colunas", 6)), int(p.get("linhas", 2))
    m, vao = float(p.get("modulo", 180)), float(p.get("vao", 0))
    pal = ctx.get("paleta") or {}
    cores = [_cor(c, ctx) for c in (p.get("cores") or [k for k in ("marca", "escuro", "papel") if k in pal])]
    if len(cores) < 2:
        raise ValueError("mosaico precisa de pelo menos 2 cores")
    palavras = [_texto({"texto": w}, ctx, caixa_alta=p.get("caixa_alta", True)) for w in (p.get("palavras") or _palavras_evento(ctx))]
    f = fonte(ctx, p.get("fonte", "display"), p.get("peso"))
    simbolo = None
    if p.get("simbolo", True) and (p.get("png") or ctx.get("logo_png")):
        _, cob = _simbolo(p.get("png") or ctx.get("logo_png"), p.get("recorte"))
        simbolo = _contorno(cob, m * 0.62)
    tipos = list(p.get("sequencia") or ["cor", "tipo", "simbolo", "meio-tom", "tipo", "contorno"])
    if not simbolo:
        tipos = [t for t in tipos if t != "simbolo"] or ["cor", "tipo"]
    rng = np.random.default_rng(int(p.get("semente", 7)))
    grade = [[None] * cols for _ in range(rows)]
    fila, usados = [], []
    for j in range(rows):
        for i in range(cols):
            if not fila:
                fila = list(rng.permutation(tipos))
            proibidos = {grade[j][i - 1] if i else None, grade[j - 1][i] if j else None}
            escolha = next((t for t in fila if t not in proibidos), fila[0])
            fila.remove(escolha)
            grade[j][i] = escolha
    partes, n_pal = [], 0
    kap = f.cap / f.upem
    for j in range(rows):
        for i in range(cols):
            x, y = i * (m + vao), j * (m + vao)
            bg = cores[(i + 2 * j) % len(cores)] if len(cores) > 2 else cores[(i + j) % 2]
            fg = max((c for c in cores if c != bg), key=lambda c: _contraste(c, bg))
            partes.append(f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(m)}" height="{_n(m)}" fill="{bg}"/>')
            t = grade[j][i]
            if t == "tipo":
                w = palavras[n_pal % len(palavras)]; n_pal += 1
                s = _r(min((m * 0.82) / f.largura(w, 1.0), 0.5 * m / kap))
                cx0, _, cx1, _ = f.caixa_tinta(w, s)
                partes.append(f'<text x="{_n(x + (m - (cx1 - cx0)) / 2 - cx0)}" y="{_n(y + m / 2 + f.cap_px(s) / 2)}" fill="{fg}" '
                              f'style="{_estilo(f, s)}">{_esc(w)}</text>')
                usados.append(w)
            elif t == "simbolo":
                d, sw, sh = simbolo
                partes.append(f'<path d="{d}" transform="translate({_n(x + (m - sw) / 2)} {_n(y + (m - sh) / 2)})" fill="{fg}" fill-rule="evenodd"/>')
            elif t == "meio-tom":
                c = m / 8
                pontos = "".join(f'<circle cx="{_n(x + c * (a + 0.5))}" cy="{_n(y + c * (b + 0.5))}" r="{_n(c * (0.08 + 0.36 * (a + b) / 14))}"/>'
                                 for a in range(8) for b in range(8))
                partes.append(f'<g fill="{fg}">{pontos}</g>')
            elif t == "contorno":
                partes.append(f'<circle cx="{_n(x + m / 2)}" cy="{_n(y + m / 2)}" r="{_n(m * 0.3)}" fill="none" stroke="{fg}" stroke-width="{_n(m * 0.035)}"/>'
                              f'<circle cx="{_n(x + m / 2)}" cy="{_n(y + m / 2)}" r="{_n(m * 0.06)}" fill="{fg}"/>')
            elif t != "cor":
                raise ValueError(f"módulo `{t}`: use cor, tipo, simbolo, meio-tom ou contorno")
    W, H = _inteiro(cols * m + (cols - 1) * vao), _inteiro(rows * m + (rows - 1) * vao)
    return dict(svg=_svg(W, H, "".join(partes), "mosaico", uid), w=W, h=H, texto="\n".join(dict.fromkeys(usados)),
                fontes=[f.familia] if usados else [])


# ---------------------------------------------------------------- composição: base comum dos desenhos de página
# Os tipos desta parte (linhas ... mapa) nascem para ficar presos a algo da página (references/09-composicao.md). O que vale
# para todos: o acento da página sai como currentColor (o elemento herda o `color` do CSS, que já troca em fundo papel e cor;
# as outras cores da paleta saem em hex); nada de filter, máscara de alfa suave, gradiente nem <pattern> (o PDF rasteriza);
# o único recorte é o clipPath retangular, duro e vetorial; texto é sempre <text> na fonte do kit; e cada um devolve `tinta`
# ([x0, y0, x1, y1] na caixa do svg: a área que pinta com opacidade >= 0,5, o mesmo critério de alfa >= 128 do PNG) e, quando
# tem texto, `linhas` ({linha_base, cap}), para a composição alinhar pela letra e não pela caixa.
PAGINA = "currentColor"
DIRECOES = {"dir": (1.0, 0.0), "esq": (-1.0, 0.0), "baixo": (0.0, 1.0), "cima": (0.0, -1.0)}   # y cresce para baixo


def _cor_pagina(valor, ctx, padrao="marca"):
    """Cor de um desenho de composição. 'marca' (o padrão) é o acento da página e sai como currentColor; outra chave da
    paleta ou #RRGGBB sai em hex; 'transparent' ou 'none' = não pinta (a faixa de advertência de uma cor só)."""
    v = padrao if valor is None else valor
    if v in ("marca", PAGINA):
        return PAGINA
    if v in ("transparent", "none"):
        return "none"
    return _cor(v, ctx, padrao)


def _medida(p, chave, padrao, minimo=0.0, estrito=True):
    v = p.get(chave, padrao)
    try:
        v = float(v)
    except (TypeError, ValueError):
        raise ValueError(f"`{chave}`: use um número (recebi {v!r})") from None
    if not math.isfinite(v) or (v <= minimo if estrito else v < minimo):
        raise ValueError(f"`{chave}` precisa ser {'maior que' if estrito else 'pelo menos'} {minimo:g} (recebi {v:g})")
    return v


def _escolha(p, chave, padrao, validos):
    v = p.get(chave, padrao)
    if v not in validos:
        raise ValueError(f"`{chave}` `{v}`: use {', '.join(map(str, validos))}")
    return v


def _caixa_pts(pts):
    a = np.asarray(pts, float).reshape(-1, 2)
    return [float(a[:, 0].min()), float(a[:, 1].min()), float(a[:, 0].max()), float(a[:, 1].max())]


def _pad_caixa(c, v):
    return [c[0] - v, c[1] - v, c[2] + v, c[3] + v]


def _uniao(caixas):
    cs = [c for c in caixas if c is not None]
    return [min(c[0] for c in cs), min(c[1] for c in cs), max(c[2] for c in cs), max(c[3] for c in cs)] if cs else None


def _clip_semiplano(poly, nx, ny, c):
    """Parte do polígono em que nx*x + ny*y >= c (Sutherland-Hodgman, um semiplano por vez)."""
    saida = []
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        da, db = nx * a[0] + ny * a[1] - c, nx * b[0] + ny * b[1] - c
        if da >= 0:
            saida.append(a)
        if (da >= 0) != (db >= 0):
            t = da / (da - db)
            saida.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return saida


def _clip_caixa(poly, caixa):
    x0, y0, x1, y1 = caixa
    for nx, ny, c in ((1, 0, x0), (-1, 0, -x1), (0, 1, y0), (0, -1, -y1)):
        poly = _clip_semiplano(poly, nx, ny, c)
        if len(poly) < 3:
            return []
    return poly


def _area_poligono(poly):
    return 0.5 * abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                         for i in range(len(poly))))


def _recorta_reta(b, d, caixa):
    """Trecho (t0, t1) da reta b + t*d (d unitário) que fica dentro da caixa [x0, y0, x1, y1]; (0, 0) quando não passa."""
    t0, t1 = -math.inf, math.inf
    for p0, dd, lo, hi in ((b[0], d[0], caixa[0], caixa[2]), (b[1], d[1], caixa[1], caixa[3])):
        if abs(dd) < 1e-12:
            if not lo <= p0 <= hi:
                return 0.0, 0.0
            continue
        a, c = (lo - p0) / dd, (hi - p0) / dd
        t0, t1 = max(t0, min(a, c)), min(t1, max(a, c))
    return (t0, t1) if t1 - t0 > 1e-9 else (0.0, 0.0)


def _retangulo_traco(a, b, esp):
    """O traço de largura `esp` do segmento a-b com ponta reta (butt), como polígono de 4 cantos."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    if L < 1e-9:
        return None
    nx, ny = -dy / L * esp / 2, dx / L * esp / 2
    return [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)]


def _quina(a, v, b, esp, limite=4.0):
    """Pontas externas da junta em quina (miter) no vértice v, entre os trechos a-v e v-b. Vazio quando passa do limite do
    SVG (stroke-miterlimit 4: ângulo agudo vira bisel) ou quando os trechos não existem."""
    u1, u2 = (v[0] - a[0], v[1] - a[1]), (b[0] - v[0], b[1] - v[1])
    l1, l2 = math.hypot(*u1), math.hypot(*u2)
    if l1 < 1e-9 or l2 < 1e-9:
        return []
    u1, u2 = (u1[0] / l1, u1[1] / l1), (u2[0] / l2, u2[1] / l2)
    pontas = []
    for lado in (1, -1):
        n1, n2 = (-u1[1] * lado, u1[0] * lado), (-u2[1] * lado, u2[0] * lado)
        k = 1 + n1[0] * n2[0] + n1[1] * n2[1]
        if k < 1e-9:
            continue
        mx, my = (n1[0] + n2[0]) / k, (n1[1] + n2[1]) / k
        if math.hypot(mx, my) <= limite:
            pontas.append((v[0] + mx * esp / 2, v[1] + my * esp / 2))
    return pontas


def _tinta_polilinha(pts, esp):
    """Caixa da tinta de uma polilinha com ponta reta e junta em quina: união do traço de cada trecho e da ponta da quina
    em cada vértice de dentro."""
    P = [(float(x), float(y)) for x, y in pts]
    cantos = []
    for a, b in zip(P, P[1:]):
        r = _retangulo_traco(a, b, esp)
        cantos += r or [a]
    for i in range(1, len(P) - 1):
        cantos += _quina(P[i - 1], P[i], P[i + 1], esp)
    return _caixa_pts(cantos)


def _fechar(tipo, uid, corpo, tinta, margem=1.0):
    """Caixa do svg = tinta + 1 px de margem (o antialiasing da borda não é cortado), nos inteiros: o corpo, desenhado em
    coordenadas livres, é transladado para dentro. Devolve (resultado parcial com svg, w, h e tinta na caixa do svg,
    (dx, dy)): dx, dy é o quanto se soma às coordenadas livres para chegar às da caixa; quando as livres eram da página, a
    origem do svg na página é (-dx, -dy)."""
    x0, y0, x1, y1 = tinta
    ox, oy = math.floor(x0 - margem), math.floor(y0 - margem)
    w, h = int(math.ceil(x1 + margem)) - ox, int(math.ceil(y1 + margem)) - oy
    dx, dy = -ox, -oy
    corpo = f'<g transform="translate({dx} {dy})">{corpo}</g>' if (dx or dy) else corpo
    return (dict(svg=_svg(w, h, corpo, tipo, uid), w=w, h=h, tinta=[x0 + dx, y0 + dy, x1 + dx, y1 + dy]), (dx, dy))


def _regiao(recorte, W, H):
    """Caixa [x0, y0, x1, y1] onde o desenho existe: a caixa toda, um retângulo [x, y, largura, altura] ou uma faixa
    {eixo: 'x'|'y', de: px, ate: px} (faixa vertical em x, horizontal em y)."""
    if recorte is None:
        return [0.0, 0.0, W, H]
    if isinstance(recorte, (list, tuple)) and len(recorte) == 4:
        x, y, w, h = (float(v) for v in recorte)
        caixa = [x, y, x + w, y + h]
    elif isinstance(recorte, dict) and recorte.get("eixo") in ("x", "y") and "ate" in recorte:
        de, ate = float(recorte.get("de", 0)), float(recorte["ate"])
        caixa = [de, 0.0, ate, H] if recorte["eixo"] == "x" else [0.0, de, W, ate]
    else:
        raise ValueError("`recorte`: use [x, y, largura, altura] ou {'eixo': 'x'|'y', 'de': px, 'ate': px}")
    caixa = [max(0.0, caixa[0]), max(0.0, caixa[1]), min(W, caixa[2]), min(H, caixa[3])]
    if caixa[2] - caixa[0] <= 0 or caixa[3] - caixa[1] <= 0:
        raise ValueError(f"`recorte` {recorte} cai fora da caixa de {W:g} x {H:g}")
    return caixa


class _Degraus:
    """Opacidade em degraus ao longo de uma direção, no lugar do gradiente com máscara (que rasteriza o PDF). `esmaecer` =
    'dir'|'esq'|'cima'|'baixo' ou {direcao: nome ou graus (sentido horário, 0 = para a direita), passos: 5, minimo: 0,12}.
    A direção é para onde o desenho SOME: 'dir' = opaco na esquerda, só `minimo` de opacidade na direita. O primeiro degrau
    é opaco; o último, `minimo`; a faixa de cada degrau tem a mesma largura."""

    def __init__(self, esm, regiao):
        if isinstance(esm, str):
            esm = {"direcao": esm}
        d = esm.get("direcao", "dir")
        if d in DIRECOES:
            self.f = DIRECOES[d]
        elif isinstance(d, (int, float)) and not isinstance(d, bool):
            self.f = (math.cos(math.radians(d)), math.sin(math.radians(d)))
        else:
            raise ValueError(f"esmaecer.direcao `{d}`: use {', '.join(DIRECOES)} ou um ângulo em graus")
        self.passos, self.minimo = int(esm.get("passos", 5)), float(esm.get("minimo", 0.12))
        if not 2 <= self.passos <= 12:
            raise ValueError(f"esmaecer.passos `{self.passos}`: use de 2 a 12")
        if not 0 <= self.minimo < 1:
            raise ValueError(f"esmaecer.minimo `{self.minimo}`: use de 0 a menos de 1")
        us = [x * self.f[0] + y * self.f[1] for x in (regiao[0], regiao[2]) for y in (regiao[1], regiao[3])]
        self.u0, self.u1 = min(us), max(us)
        self.ops = [1 - (1 - self.minimo) * j / (self.passos - 1) for j in range(self.passos)]

    def u(self, pt):
        return pt[0] * self.f[0] + pt[1] * self.f[1]

    def indice(self, u):
        return min(self.passos - 1, max(0, int((u - self.u0) / (self.u1 - self.u0) * self.passos)))

    def partir(self, a, b):
        """O segmento a-b cortado nas fronteiras dos degraus: [(ponto, ponto, degrau)]. Reta perpendicular à direção fica
        inteira no degrau da sua posição."""
        ua, ub = self.u(a), self.u(b)
        ts = {0.0, 1.0}
        if abs(ub - ua) > 1e-9:
            for j in range(1, self.passos):
                t = (self.u0 + (self.u1 - self.u0) * j / self.passos - ua) / (ub - ua)
                if 1e-9 < t < 1 - 1e-9:
                    ts.add(t)
        ts = sorted(ts)
        saida = []
        for t0, t1 in zip(ts, ts[1:]):
            pa = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
            pb = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
            saida.append((pa, pb, self.indice(ua + (ub - ua) * (t0 + t1) / 2)))
        return saida


def _fracao_densidade(v):
    from fractions import Fraction
    try:
        d = Fraction(str(v)).limit_denominator(1000)
    except (ValueError, ZeroDivisionError):
        raise ValueError(f"`densidade`: use um número entre 0 e 1 (recebi {v!r})") from None
    if not 0 < d <= 1:
        raise ValueError(f"`densidade` precisa ficar entre 0 (exclusive) e 1 (todas): recebi {v}")
    return d


def _escolhidas(n, d):
    """Índices (de 0 a n-1) das linhas que aparecem quando só a fração d delas é desenhada: padrão regular em que a primeira
    sempre entra (d = 1/2: 0, 2, 4...; d = 1/4: 0, 4, 8...). Quantas: ceil(n * d)."""
    sel, antes = [], 0
    for i in range(n):
        ate = math.ceil((i + 1) * d)
        if ate > antes:
            sel.append(i)
        antes = ate
    return sel


def _texto_svg(f, txt, x, y, s, ls, cor, ancora="start", tabular=False, extra=""):
    """<text> na fonte do kit com o x do INÍCIO já resolvido pela medida (o text-anchor do SVG conta o espaçamento depois da
    última letra e deslocaria o texto). ancora: 'start' = x é o começo da tinta, 'middle' = o centro, 'end' = o fim.
    Devolve (svg, caixa da tinta [x0, y0, x1, y1])."""
    L = f.largura(txt, s, ls, tabular) - ls
    x0 = x if ancora == "start" else x - L / 2 if ancora == "middle" else x - L
    ix0, iy0, ix1, iy1 = f.caixa_tinta(txt, s, ls, tabular)
    return (f'<text x="{_n(x0)}" y="{_n(y)}" fill="{cor}" style="{_estilo(f, s, ls, tabular)}"{extra}>{_esc(txt)}</text>',
            [x0 + ix0, y - iy1, x0 + ix1, y - iy0])


# ---------------------------------------------------------------- linhas, listras
def _linhas(p, ctx, uid):
    """Padrão de linhas paralelas, a textura de fundo que varia por página sem perder a identidade (espaço, ângulo, peso e
    densidade são parâmetros). As linhas ficam no meio de faixas de `espacamento` px medidas na perpendicular, então o
    número delas segue o espaçamento: floor((extensão da caixa na perpendicular) / espacamento), e a densidade tira linhas
    em padrão regular. Com ângulo qualquer as pontas são cortadas rente à caixa por um clipPath retangular (duro, vetorial).
    params: largura 600; altura 400; espacamento 16; angulo 0 (graus, sentido horário, 0 = horizontais, -45 = sobem para a
    direita); espessura 1,5; densidade 1 (fração das linhas desenhadas, de 0 exclusive a 1); esmaecer (opacidade em
    degraus: 'dir', 'esq', 'cima', 'baixo' ou {direcao, passos 5, minimo 0,12}; a direção é para onde o desenho some);
    recorte ([x, y, largura, altura] ou {eixo, de, ate}: o desenho só existe ali); cor 'marca'. `largura`/`altura` são a
    caixa; com UMA medida pedida pela composição, a tinta (o que passa de meia opacidade, dentro do recorte) é que mede o
    pedido, e o gerar acha a caixa que faz isso."""
    W, H = _medida(p, "largura", 600), _medida(p, "altura", 400)
    s, esp = _medida(p, "espacamento", 16), _medida(p, "espessura", 1.5)
    ang = float(p.get("angulo", 0))
    if esp >= s:
        raise ValueError(f"espessura {esp:g} não cabe no espaçamento {s:g}: as linhas se fundiriam")
    regiao = _regiao(p.get("recorte"), W, H)
    dens = _fracao_densidade(p.get("densidade", 1))
    cor = _cor_pagina(p.get("cor"), ctx)
    t = math.radians(ang)
    d, n = (math.cos(t), math.sin(t)), (-math.sin(t), math.cos(t))
    proj = [x * n[0] + y * n[1] for x in (0, W) for y in (0, H)]
    N = int(math.floor((max(proj) - min(proj)) / s + 1e-9))
    if N < 1:
        raise ValueError(f"espaçamento {s:g} maior que a caixa na perpendicular das linhas ({max(proj) - min(proj):g} px)")
    eixo = abs(math.sin(2 * t)) < 1e-9          # horizontal ou vertical: a ponta já cai rente à borda, sem clipPath
    folga = 0.0 if eixo else esp                # inclinada: passa da região em `esp` e o clipPath corta rente
    estendida = [regiao[0] - folga, regiao[1] - folga, regiao[2] + folga, regiao[3] + folga]
    degraus = _Degraus(p["esmaecer"], regiao) if p.get("esmaecer") else None
    por_degrau, visiveis, todas = {}, [], []
    for k in _escolhidas(N, dens):
        off = min(proj) + (k + 0.5) * s
        b = (n[0] * off, n[1] * off)
        t0, t1 = _recorta_reta(b, d, estendida)
        if t1 <= t0:
            continue
        a, e = (b[0] + d[0] * t0, b[1] + d[1] * t0), (b[0] + d[0] * t1, b[1] + d[1] * t1)
        for pa, pb, j in (degraus.partir(a, e) if degraus else [(a, e, 0)]):
            por_degrau.setdefault(j, []).append((pa, pb))
            poly = _retangulo_traco(pa, pb, esp)
            vis = _clip_caixa(poly, regiao) if poly else []
            if vis:
                todas.append(_caixa_pts(vis))
                if degraus is None or degraus.ops[j] >= 0.5:
                    visiveis.append(todas[-1])
    if not por_degrau:
        raise ValueError(f"o recorte {p.get('recorte')} não pega nenhuma linha")
    tinta = _uniao(visiveis or todas)
    caminhos = []
    for j in sorted(por_degrau):
        dd = "".join(f"M{_n(a[0])} {_n(a[1])}L{_n(b[0])} {_n(b[1])}" for a, b in por_degrau[j])
        op = degraus.ops[j] if degraus else 1
        caminhos.append(f'<path d="{dd}"' + (f' stroke-opacity="{_n(op)}"' if op < 1 else "") + "/>")
    clip = "" if eixo else f' clip-path="url(#c-{uid})"'
    defs = "" if eixo else (f'<defs><clipPath id="c-{uid}"><rect x="{_n(regiao[0])}" y="{_n(regiao[1])}" '
                            f'width="{_n(regiao[2] - regiao[0])}" height="{_n(regiao[3] - regiao[1])}"/></clipPath></defs>')
    corpo = defs + f'<g fill="none" stroke="{cor}" stroke-width="{_n(esp)}"{clip}>{"".join(caminhos)}</g>'
    return dict(svg=_svg(_inteiro(W), _inteiro(H), corpo, "linhas", uid), w=_inteiro(W), h=_inteiro(H), texto="", fontes=[],
                tinta=tinta)


def _listras(p, ctx, uid):
    """Faixa de advertência: listras diagonais que alternam duas cores da paleta (a segunda pode ser 'transparent': só a
    primeira pinta e o vão fica vazio). Com as duas cores cheias, a primeira cobre a caixa toda e a segunda entra por cima
    (duas listras coladas somariam o antialiasing da emenda e deixariam um fio claro). Cada listra é um polígono recortado
    rente à caixa, sem clipPath. params: largura 800; altura 48; largura_listra 24 (medida na perpendicular); angulo -45
    (graus, sentido horário; -45 = sobe para a direita); cores ['marca', 'escuro']; fase 0 (px de deslocamento das listras).
    `largura`/`altura` são a caixa (a tinta, quando uma cor é transparente, é só o que pinta)."""
    W, H = _medida(p, "largura", 800), _medida(p, "altura", 48)
    lw, ang = _medida(p, "largura_listra", 24), float(p.get("angulo", -45))
    cores = p.get("cores") or ["marca", "escuro"]
    if not isinstance(cores, (list, tuple)) or len(cores) != 2:
        raise ValueError("`cores` precisa ter exatamente 2 cores (a segunda pode ser 'transparent')")
    c = [_cor_pagina(x, ctx) for x in cores]
    if c[0] == "none" and c[1] == "none":
        raise ValueError("as duas cores são transparentes: não há o que desenhar")
    fase = float(p.get("fase", 0))
    t = math.radians(ang)
    n = (-math.sin(t), math.cos(t))
    proj = [x * n[0] + y * n[1] for x in (0, W) for y in (0, H)]
    k0, k1 = math.floor((min(proj) - fase) / lw), math.floor((max(proj) - fase) / lw)
    caixa = [(0.0, 0.0), (W, 0.0), (W, H), (0.0, H)]
    por_cor = {0: [], 1: []}
    for k in range(k0, k1 + 1):
        lo, hi = fase + k * lw, fase + (k + 1) * lw
        poly = _clip_semiplano(_clip_semiplano(caixa, n[0], n[1], lo), -n[0], -n[1], -hi)
        if len(poly) >= 3 and _area_poligono(poly) > 0.01:
            por_cor[k % 2].append(poly)
    cheia = c[0] != "none" and c[1] != "none"
    partes = []
    if cheia:
        partes.append(f'<rect width="{_n(W)}" height="{_n(H)}" fill="{c[0]}"/>')
        desenhar = [(1, c[1])]
    else:
        desenhar = [(i, c[i]) for i in (0, 1) if c[i] != "none"]
    for i, cor in desenhar:
        if por_cor[i]:
            dd = "".join("M" + "L".join(f"{_n(x)} {_n(y)}" for x, y in poly) + "Z" for poly in por_cor[i])
            partes.append(f'<path d="{dd}" fill="{cor}"/>')
    tinta = [0.0, 0.0, W, H] if cheia else _uniao([_caixa_pts(poly) for i, _ in desenhar for poly in por_cor[i]])
    if tinta is None:
        raise ValueError("nenhuma listra cai dentro da caixa")
    return dict(svg=_svg(_inteiro(W), _inteiro(H), "".join(partes), "listras", uid), w=_inteiro(W), h=_inteiro(H), texto="",
                fontes=[], tinta=tinta)


# ---------------------------------------------------------------- colchetes, fio (presos a geometria da página)
CANTOS = ("sup-esq", "sup-dir", "inf-esq", "inf-dir")
TERMINAIS = ("nenhum", "ponto", "seta", "barra")


def _colchetes(p, ctx, uid):
    """Colchetes de canto em volta de uma caixa da PÁGINA (a foto, o número, o bloco), como as marcas de um enquadramento.
    `caixa` já vem com a folga (alvo mais folga) e a tinta externa encosta nela: a quina de cada colchete cai exatamente no
    canto da caixa e o braço corre `braco` px ao longo do lado. Contrato de references/08 (grafismo preso a geometria):
    recebe a caixa em px da página e devolve `origem` ([x, y] da página onde o canto superior esquerdo do svg cai) e `tinta`.
    params: caixa [x, y, largura, altura]; braco (padrão 18% do menor lado); espessura 3; cantos (quais desenhar; padrão os
    quatro: sup-esq, sup-dir, inf-esq, inf-dir); cor 'marca'. Sem `caixa`, `largura` e/ou `altura` são a medida da tinta de um
    enquadramento na origem (a outra medida segue `proporcao`, padrão 4/3 de largura por altura)."""
    caixa = p.get("caixa")
    if caixa is None and (p.get("largura") is not None or p.get("altura") is not None):
        ped = _medidas_pedidas(p)
        prop = _medida(p, "proporcao", 4 / 3)
        w = ped["largura"] if "largura" in ped else ped["altura"] * prop
        caixa = [0.0, 0.0, w, ped["altura"] if "altura" in ped else w / prop]
    if not (isinstance(caixa, (list, tuple)) and len(caixa) == 4):
        raise ValueError("`caixa`: use [x, y, largura, altura] em px da página (ou `largura` e/ou `altura`)")
    x, y, w, h = (float(v) for v in caixa)
    if w <= 0 or h <= 0:
        raise ValueError(f"`caixa` {list(caixa)}: largura e altura precisam ser maiores que zero")
    esp = _medida(p, "espessura", 3.0)
    braco = _medida(p, "braco", round(min(w, h) * 0.18, 1))
    if 2 * braco > min(w, h) + 1e-9:
        raise ValueError(f"braco {braco:g} grande demais para a caixa de {w:g} x {h:g}: os braços se encontrariam")
    if braco <= esp:
        raise ValueError(f"braco {braco:g} não passa da espessura {esp:g}: o colchete viraria um quadrado")
    cantos = list(p.get("cantos") or CANTOS)
    for c in cantos:
        if c not in CANTOS:
            raise ValueError(f"canto `{c}`: use {', '.join(CANTOS)}")
    cor = _cor_pagina(p.get("cor"), ctx)
    o, x1, y1 = esp / 2, x + w, y + h
    formas = {"sup-esq": [(x + o, y + braco), (x + o, y + o), (x + braco, y + o)],
              "sup-dir": [(x1 - braco, y + o), (x1 - o, y + o), (x1 - o, y + braco)],
              "inf-esq": [(x + o, y1 - braco), (x + o, y1 - o), (x + braco, y1 - o)],
              "inf-dir": [(x1 - braco, y1 - o), (x1 - o, y1 - o), (x1 - o, y1 - braco)]}
    caminhos = "".join("M" + "L".join(f"{_n(px)} {_n(py)}" for px, py in formas[c]) for c in dict.fromkeys(cantos))
    corpo = (f'<path d="{caminhos}" fill="none" stroke="{cor}" stroke-width="{_n(esp)}" stroke-linejoin="miter" '
             'stroke-linecap="butt"/>')
    tinta = _uniao([_tinta_polilinha(formas[c], esp) for c in cantos])
    r, (dx, dy) = _fechar("colchetes", uid, corpo, tinta)
    return dict(r, texto="", fontes=[], origem=[-dx, -dy])


def _tracejar(P, traco, vao):
    """As partes desenhadas de uma polilinha tracejada ([traço, vão] a partir do primeiro ponto, como o stroke-dasharray):
    lista de polilinhas (um traço que dobra numa quina leva o vértice junto)."""
    saida, atual, no_traco, resta = [], [P[0]], True, traco
    for a, b in zip(P, P[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 1e-9:
            continue
        andou = 0.0
        while L - andou > 1e-9:
            passo = min(resta, L - andou)
            andou += passo
            resta -= passo
            ponto = (a[0] + (b[0] - a[0]) * andou / L, a[1] + (b[1] - a[1]) * andou / L)
            if no_traco:
                atual.append(ponto)
            if resta <= 1e-9:
                if no_traco:
                    saida.append(atual)
                    atual = []
                else:
                    atual = [ponto]
                no_traco = not no_traco
                resta = traco if no_traco else vao
    if no_traco and len(atual) >= 2:
        saida.append(atual)
    return [s for s in saida if len(s) >= 2]


def _fio(p, ctx, uid):
    """Fio que liga ou sublinha (conecta o número ao rótulo, continua uma linha da foto): polilinha em coordenadas da PÁGINA,
    com terminal em cada ponta e tracejado opcional. Quinas em esquadro (junta em quina). O ponto, a seta e a barra crescem
    com a espessura, e a seta encurta o fio para a linha não vazar pela ponta. Contrato de references/08: recebe os pontos
    na página e devolve `origem` e `tinta`.
    params: pontos [[x, y], ...] (2 ou mais); espessura 2; terminais [início, fim] com nenhum, ponto, seta ou barra (um
    nome só vale para os dois; padrão nenhum); tracejado [traço, vão] em px ou null; cor 'marca'. Sem `pontos`, `largura`
    (reta horizontal) ou `altura` (vertical) é a medida da tinta, terminais incluídos; com as duas, a diagonal da caixa."""
    esp = _medida(p, "espessura", 2.0)
    term = p.get("terminais", ["nenhum", "nenhum"])
    term = [term, term] if isinstance(term, str) else list(term)
    if len(term) != 2 or any(t not in TERMINAIS for t in term):
        raise ValueError(f"`terminais`: use [início, fim] com {', '.join(TERMINAIS)} (recebi {p.get('terminais')!r})")
    pts = p.get("pontos")
    if pts is None and (p.get("largura") is not None or p.get("altura") is not None):
        ped = _medidas_pedidas(p)
        sobra = {"ponto": max(2.6 * esp, 3.5), "barra": esp / 2, "seta": 0.0, "nenhum": 0.0}[term[0]], \
            {"ponto": max(2.6 * esp, 3.5), "barra": esp / 2, "seta": 0.0, "nenhum": 0.0}[term[1]]   # o que cada terminal passa do fio, no sentido dele
        if len(ped) == 2:      # diagonal da caixa, com os pontos recuados o que o terminal e a espessura passam do fio (a tinta cabe na caixa)
            lado = {"ponto": max(2.6 * esp, 3.5), "barra": max(3.4 * esp, 5.0), "seta": max(7 * esp, 9.0) * 0.42, "nenhum": 0.0}
            e0, e1 = lado[term[0]] + esp / 2, lado[term[1]] + esp / 2
            pts = [[e0, e0], [ped["largura"] - e1, ped["altura"] - e1]]
        else:
            L = next(iter(ped.values()))
            if L - sobra[0] - sobra[1] <= 0:
                raise ValueError(f"medida {L:g} não passa dos terminais ({sobra[0] + sobra[1]:.1f} px)")
            pts = ([[sobra[0], 0.0], [L - sobra[1], 0.0]] if "largura" in ped else [[0.0, sobra[0]], [0.0, L - sobra[1]]])
    if not (isinstance(pts, (list, tuple)) and len(pts) >= 2 and all(isinstance(q, (list, tuple)) and len(q) == 2 for q in pts)):
        raise ValueError("`pontos`: use [[x, y], [x, y], ...] com 2 pontos ou mais (px da página)")
    P = [(float(a), float(b)) for a, b in pts]
    if all(math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-9 for a, b in zip(P, P[1:])):
        raise ValueError("`pontos` caem todos no mesmo lugar: o fio não tem comprimento")
    traco = p.get("tracejado")
    if traco is not None and not (isinstance(traco, (list, tuple)) and len(traco) == 2 and all(float(v) > 0 for v in traco)):
        raise ValueError("`tracejado`: use [traço, vão] em px (maiores que zero) ou null")
    cor = _cor_pagina(p.get("cor"), ctx)

    def terminal(tipo, ponta, vizinho):
        """(svg, caixa da tinta, quanto o fio encurta) do terminal em `ponta`; `vizinho` dá o rumo do último trecho."""
        ux, uy = ponta[0] - vizinho[0], ponta[1] - vizinho[1]
        L = math.hypot(ux, uy) or 1.0
        ux, uy = ux / L, uy / L
        nx, ny = -uy, ux
        if tipo == "ponto":
            r = max(2.6 * esp, 3.5)
            return (f'<circle cx="{_n(ponta[0])}" cy="{_n(ponta[1])}" r="{_n(r)}" fill="{cor}"/>',
                    [ponta[0] - r, ponta[1] - r, ponta[0] + r, ponta[1] + r], 0.0)
        if tipo == "seta":
            comp = max(7 * esp, 9.0)
            meia = comp * 0.42
            base = (ponta[0] - ux * comp, ponta[1] - uy * comp)
            tri = [ponta, (base[0] + nx * meia, base[1] + ny * meia), (base[0] - nx * meia, base[1] - ny * meia)]
            return (f'<polygon points="{" ".join(f"{_n(a)},{_n(b)}" for a, b in tri)}" fill="{cor}"/>', _caixa_pts(tri), comp * 0.85)
        meia = max(3.4 * esp, 5.0)       # barra: traço perpendicular ao último trecho
        a, b = (ponta[0] + nx * meia, ponta[1] + ny * meia), (ponta[0] - nx * meia, ponta[1] - ny * meia)
        return (f'<path d="M{_n(a[0])} {_n(a[1])}L{_n(b[0])} {_n(b[1])}" fill="none" stroke="{cor}" stroke-width="{_n(esp)}"/>',
                _caixa_pts(_retangulo_traco(a, b, esp)), 0.0)

    linha, extras, caixas = list(P), [], []
    for lado, tipo in ((0, term[0]), (1, term[1])):
        if tipo == "nenhum":
            continue
        ponta, viz = (P[0], P[1]) if lado == 0 else (P[-1], P[-2])
        if math.hypot(ponta[0] - viz[0], ponta[1] - viz[1]) < 1e-9:       # ponto repetido: o rumo vem do próximo diferente
            outros = [q for q in (P[1:] if lado == 0 else P[-2::-1]) if math.hypot(q[0] - ponta[0], q[1] - ponta[1]) > 1e-9]
            viz = outros[0]
        svg_t, caixa_t, corta = terminal(tipo, ponta, viz)
        extras.append(svg_t)
        caixas.append(caixa_t)
        if corta:
            seg = math.hypot(viz[0] - ponta[0], viz[1] - ponta[1])
            if seg <= corta:
                raise ValueError(f"o último trecho do fio ({seg:.0f} px) é curto demais para a seta ({corta:.0f} px)")
            nova = (ponta[0] + (viz[0] - ponta[0]) * corta / seg, ponta[1] + (viz[1] - ponta[1]) * corta / seg)
            if lado == 0:
                linha[0] = nova
            else:
                linha[-1] = nova
    if traco:
        partes = _tracejar(linha, float(traco[0]), float(traco[1]))
        caixas += [_tinta_polilinha(s, esp) for s in partes]
        da = f' stroke-dasharray="{_n(traco[0])} {_n(traco[1])}"'
    else:
        caixas.append(_tinta_polilinha(linha, esp))
        da = ""
    d = "M" + "L".join(f"{_n(a)} {_n(b)}" for a, b in linha)
    corpo = (f'<path d="{d}" fill="none" stroke="{cor}" stroke-width="{_n(esp)}" stroke-linejoin="miter" '
             f'stroke-linecap="butt"{da}/>' + "".join(extras))
    r, (dx, dy) = _fechar("fio", uid, corpo, _uniao(caixas))
    return dict(r, texto="", fontes=[], origem=[-dx, -dy])


# ---------------------------------------------------------------- régua, divisória
def _numero_br(v):
    return str(int(v)) if float(v).is_integer() else (f"{float(v):.3f}".rstrip("0").rstrip(".")).replace(".", ",")


def _regua(p, ctx, uid):
    """Régua de marcas (ticks) como a de uma trena ou de um percurso: organiza, mede, dá ritmo. Marcas a cada `passo` px,
    a primeira e toda `marca_maior_a_cada`-ésima maiores; rótulo opcional em texto vivo sob as marcas maiores (numerais
    tabulares, centrado na marca e nunca para fora das pontas: o primeiro e o último rótulo encostam na ponta em vez de
    passar dela). A linha de base avança meia espessura além das duas marcas das pontas, então a tinta mede exatamente
    comprimento + espessura.
    params: comprimento 600; orientacao 'horizontal' | 'vertical'; passo 10; marca_maior_a_cada 5; marca 10 (comprimento da
    menor; a maior usa `marca_maior`, padrão o dobro); espessura 1,5; lado 'baixo'|'cima' (horizontal) ou 'dir'|'esq'
    (vertical): para onde saem as marcas e os rótulos (padrão baixo / dir); linha True (a linha de base inteira); rotulos
    (lista com um texto por marca maior, na ordem, ou {inicio: 0, passo: 5, formato: '{n}'}); tamanho 14; fonte 'corpo';
    peso 600; espacamento 0,06 em; folga 6 (px entre a ponta da marca e o rótulo); cor 'marca'.
    Medida da tinta: `largura` (régua horizontal) ou `altura` (vertical) é o comprimento da tinta (o `comprimento` sai dela);
    a outra dimensão escala o estilo (marca, folga e tamanho do rótulo, em proporção; a espessura não) até a tinta medir o pedido.
    Devolve `linhas` quando há rótulo (cap do primeiro, linha de base do último, como o título de uma página)."""
    orient = _escolha(p, "orientacao", "horizontal", ("horizontal", "vertical"))
    lados = ("baixo", "cima") if orient == "horizontal" else ("dir", "esq")
    lado = _escolha(p, "lado", lados[0], lados)
    sinal = 1 if lado in ("baixo", "dir") else -1
    ao_longo, cruzado = ("largura", "altura") if orient == "horizontal" else ("altura", "largura")
    ped = _medidas_pedidas(p)
    passo, esp = _medida(p, "passo", 10), _medida(p, "espessura", 1.5)
    C = ped[ao_longo] - esp if ao_longo in ped else _medida(p, "comprimento", 600)
    if C <= 0:
        raise ValueError(f"{ao_longo} {ped[ao_longo]:g} não passa da espessura {esp:g}")
    cada = int(_medida(p, "marca_maior_a_cada", 5))
    menor0 = _medida(p, "marca", 10)
    maior0 = _medida(p, "marca_maior", menor0 * 2)
    folga0 = _medida(p, "folga", 6, 0, estrito=False)
    cor = _cor_pagina(p.get("cor"), ctx)
    n = int(math.floor(C / passo + 1e-9)) + 1
    posicoes = [i * passo for i in range(n)]
    maiores = [i for i in range(n) if i % cada == 0]
    rot = p.get("rotulos")
    if rot:
        if isinstance(rot, dict):
            ini, pr = float(rot.get("inicio", 0)), float(rot.get("passo", 1))
            rot = [str(rot.get("formato", "{n}")).format(n=_numero_br(ini + j * pr)) for j in range(len(maiores))]
        if not isinstance(rot, (list, tuple)) or len(rot) != len(maiores):
            raise ValueError(f"`rotulos`: a régua tem {len(maiores)} marcas maiores e precisa de um rótulo para cada (recebi "
                             f"{len(rot) if isinstance(rot, (list, tuple)) else rot!r})")
        rot = [unicodedata.normalize("NFC", " ".join(str(t).split())) for t in rot]
        f = fonte(ctx, p.get("fonte", "corpo"), p.get("peso", 600))
    eixo = (lambda u, v: (u, v)) if orient == "horizontal" else (lambda u, v: (v, u))   # (ao longo, para fora) -> (x, y)

    def construir(k):
        """Desenho com o estilo (marca, folga, rótulo) multiplicado por k; devolve (svg, caixas, textos, linhas, fontes)."""
        menor, maior, folga = menor0 * k, maior0 * k, folga0 * k
        d, caixas = [], []
        if p.get("linha", True):
            a, b = eixo(-esp / 2, 0), eixo(C + esp / 2, 0)
            d.append(f"M{_n(a[0])} {_n(a[1])}L{_n(b[0])} {_n(b[1])}")
            caixas.append(_caixa_pts(_retangulo_traco(a, b, esp)))
        for i in range(n):
            a, b = eixo(posicoes[i], 0), eixo(posicoes[i], sinal * (maior if i % cada == 0 else menor))
            d.append(f"M{_n(a[0])} {_n(a[1])}L{_n(b[0])} {_n(b[1])}")
            caixas.append(_caixa_pts(_retangulo_traco(a, b, esp)))
        partes = [f'<path d="{"".join(d)}" fill="none" stroke="{cor}" stroke-width="{_n(esp)}" stroke-linecap="butt"/>']
        textos, fontes, linhas, bases = [], [], None, []
        if rot:
            s = _r(p.get("tamanho", 14) * k)
            ls = _r(float(p.get("espacamento", 0.06)) * s)
            cap = f.cap_px(s)
            for i, txt in zip(maiores, rot):
                L = f.largura(txt, s, ls, True) - ls
                if orient == "horizontal":
                    base = sinal * (maior + folga) + (cap if sinal > 0 else 0.0)
                    x = min(max(posicoes[i] - L / 2, -esp / 2), C + esp / 2 - L)          # centrado na marca, sem passar das pontas
                    svg_t, cx = _texto_svg(f, txt, x, base, s, ls, cor, "start", True)
                else:
                    base = min(max(posicoes[i] + cap / 2, cap - esp / 2), C + esp / 2)     # idem, na vertical
                    svg_t, cx = _texto_svg(f, txt, sinal * (maior + folga), base, s, ls, cor, "start" if sinal > 0 else "end", True)
                partes.append(svg_t)
                caixas.append(cx)
                textos.append(txt)
                bases.append(base)
            fontes = [f.familia]
            linhas = {"linha_base": bases[-1], "cap": bases[0] - cap}
        return partes, caixas, textos, linhas, fontes

    k = 1.0
    if cruzado in ped:         # a outra dimensão: o estilo cresce ou encolhe até a tinta medir o pedido
        def medida_cruzada(kk):
            caixa = _uniao(construir(kk)[1])
            return caixa[3] - caixa[1] if orient == "horizontal" else caixa[2] - caixa[0]
        k = _secante(medida_cruzada, ped[cruzado], 1.0, tol=0.2)
    partes, caixas, textos, linhas, fontes = construir(k)
    r, (dx, dy) = _fechar("regua", uid, "".join(partes), _uniao(caixas))
    if linhas:
        linhas = {kk: v + dy for kk, v in linhas.items()}
    return dict(r, texto="\n".join(textos), fontes=fontes, linhas=linhas)


def _divisoria(p, ctx, uid):
    """Divisória: fio com um ponto ou um losango no meio ou nas pontas. No meio, o fio abre um vão em volta do ornamento;
    nas pontas, o fio chega até ele. A tinta mede exatamente o comprimento (o fio e os ornamentos ficam dentro dele).
    params: comprimento 600; orientacao 'horizontal' | 'vertical'; espessura 1,5;
    ornamento 'losango' | 'ponto'; posicao 'meio' | 'pontas'; tamanho (diagonal do losango ou diâmetro do ponto; padrão
    o maior entre 10 e 6 x espessura); vao (folga entre ornamento e fio; padrão 0,9 x tamanho no meio e 0 nas pontas);
    cor 'marca'; cor_ornamento (padrão = cor). Medida da tinta: `largura` (horizontal) ou `altura` (vertical) é o comprimento;
    a outra dimensão é o tamanho do ornamento (a maior entre ele e a espessura)."""
    orient = _escolha(p, "orientacao", "horizontal", ("horizontal", "vertical"))
    ao_longo, cruzado = ("largura", "altura") if orient == "horizontal" else ("altura", "largura")
    ped = _medidas_pedidas(p)
    C = ped[ao_longo] if ao_longo in ped else _medida(p, "comprimento", 600)
    esp = _medida(p, "espessura", 1.5)
    orn = _escolha(p, "ornamento", "losango", ("losango", "ponto"))
    pos = _escolha(p, "posicao", "meio", ("meio", "pontas"))
    tam = ped[cruzado] if cruzado in ped else _medida(p, "tamanho", max(10.0, 6 * esp))
    if tam < esp:
        raise ValueError(f"{cruzado} {tam:g} menor que a espessura {esp:g}: o ornamento sumiria no fio")
    vao = _medida(p, "vao", tam * 0.9 if pos == "meio" else 0.0, 0, estrito=False)
    cor, cor_o = _cor_pagina(p.get("cor"), ctx), _cor_pagina(p.get("cor_ornamento"), ctx, p.get("cor") or "marca")
    eixo = (lambda u, v: (u, v)) if orient == "horizontal" else (lambda u, v: (v, u))
    if pos == "meio":
        centros = [C / 2]
        trechos = [(0.0, C / 2 - tam / 2 - vao), (C / 2 + tam / 2 + vao, C)]
    else:
        centros = [tam / 2, C - tam / 2]
        trechos = [(tam + vao, C - tam - vao)]
    if any(b - a <= 0 for a, b in trechos):
        raise ValueError(f"comprimento {C:g} curto demais para o ornamento de {tam:g} px e o vão de {vao:g} px")
    d = "".join("M{} {}L{} {}".format(*eixo(a, 0), *eixo(b, 0)) for a, b in trechos)
    partes = [f'<path d="{d}" fill="none" stroke="{cor}" stroke-width="{_n(esp)}" stroke-linecap="butt"/>']
    caixas = [_caixa_pts(_retangulo_traco(eixo(a, 0), eixo(b, 0), esp)) for a, b in trechos]
    for c in centros:
        cx, cy = eixo(c, 0)
        if orn == "ponto":
            partes.append(f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(tam / 2)}" fill="{cor_o}"/>')
        else:
            h = tam / 2
            partes.append(f'<polygon points="{_n(cx)},{_n(cy - h)} {_n(cx + h)},{_n(cy)} {_n(cx)},{_n(cy + h)} {_n(cx - h)},{_n(cy)}" '
                          f'fill="{cor_o}"/>')
        caixas.append([cx - tam / 2, cy - tam / 2, cx + tam / 2, cy + tam / 2])
    r, _ = _fechar("divisoria", uid, "".join(partes), _uniao(caixas))
    return dict(r, texto="", fontes=[])


# ---------------------------------------------------------------- grade de pontos, círculos, setas, estrelas
def _grade_pontos(p, ctx, uid):
    """Grade regular de pontos (textura técnica, papel milimetrado), de ponta a ponta: os pontos das bordas encostam na caixa,
    então a tinta é a caixa. O passo vira o mais perto do pedido que fecha a caixa inteira: colunas = round((largura - 2 x raio)
    / passo) + 1, e o passo real é (largura - 2 x raio) / (colunas - 1) (o mesmo nas linhas). Vetorial, um <circle> por ponto
    (nada de <pattern>, que o PDF poderia rasterizar). params: largura 600; altura 400; passo 24; raio 1,6; esmaecer
    (opacidade em degraus, como em `linhas`; a tinta passa a contar só o que fica acima de meia opacidade); cor 'marca'."""
    W, H = _medida(p, "largura", 600), _medida(p, "altura", 400)
    passo, raio = _medida(p, "passo", 24), _medida(p, "raio", 1.6)
    if 2 * raio >= passo:
        raise ValueError(f"raio {raio:g} não cabe no passo {passo:g}: os pontos se encostariam")
    if W < 2 * raio or H < 2 * raio:
        raise ValueError(f"caixa de {W:g} x {H:g} menor que um ponto de {2 * raio:g} px")
    nx, ny = int(round((W - 2 * raio) / passo)) + 1, int(round((H - 2 * raio) / passo)) + 1
    if nx * ny > 20000:
        raise ValueError(f"grade com {nx * ny} pontos: aumente o passo")
    cor = _cor_pagina(p.get("cor"), ctx)
    px = (W - 2 * raio) / (nx - 1) if nx > 1 else 0.0
    py = (H - 2 * raio) / (ny - 1) if ny > 1 else 0.0
    reais = [v for v in (px, py) if v]
    if reais and min(reais) <= 2 * raio:
        raise ValueError(f"o passo que fecha a caixa ({min(reais):.2f}) não deixa vão entre pontos de raio {raio:g}")
    ox, oy = (raio if nx > 1 else W / 2), (raio if ny > 1 else H / 2)
    degraus = _Degraus(p["esmaecer"], [0.0, 0.0, W, H]) if p.get("esmaecer") else None
    por_degrau, visiveis = {}, []
    for j in range(ny):
        for i in range(nx):
            x, y = ox + i * px, oy + j * py
            k = degraus.indice(degraus.u((x, y))) if degraus else 0
            por_degrau.setdefault(k, []).append((x, y))
            if degraus is None or degraus.ops[k] >= 0.5:
                visiveis.append([x - raio, y - raio, x + raio, y + raio])
    grupos = []
    for k in sorted(por_degrau):
        op = degraus.ops[k] if degraus else 1
        circulos = "".join(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(raio)}"/>' for x, y in por_degrau[k])
        grupos.append(f'<g fill="{cor}"' + (f' fill-opacity="{_n(op)}"' if op < 1 else "") + f">{circulos}</g>")
    tinta = _uniao(visiveis) or _uniao([[x - raio, y - raio, x + raio, y + raio] for v in por_degrau.values() for x, y in v])
    return dict(svg=_svg(_inteiro(W), _inteiro(H), "".join(grupos), "grade-pontos", uid), w=_inteiro(W), h=_inteiro(H),
                texto="", fontes=[], tinta=tinta)


def _amostra_arco(cx, cy, r, a0, a1, passo_px=0.25):
    """Pontos de um arco (graus, sentido horário na tela) a cada ~0,25 px: a caixa exata da tinta sai do máximo e do mínimo."""
    n = int(min(20000, max(8, math.radians(a1 - a0) * r / passo_px))) + 2
    ang = np.radians(np.linspace(a0, a1, n))
    return np.column_stack([cx + r * np.cos(ang), cy + r * np.sin(ang)])


def _circulos(p, ctx, uid):
    """Círculos concêntricos ou arcos concêntricos (ondas de um apito, radar, alvo, raio de alcance). A caixa é um quadrado
    em volta do maior círculo inteiro, então o centro dos círculos é o centro do svg qualquer que seja o trecho
    desenhado; a `tinta` diz o que de fato pinta. Ângulos em graus, sentido horário, 0 = para a direita (3 h): de 0 a 360
    é o círculo todo, de -90 a 90 é a metade da direita. params: raios [px, ...] ou raio_max + quantidade (raios em
    progressão igual); espessura 1,5; angulo_ini 0; angulo_fim 360; cor 'marca'. Medida da tinta: `largura`/`altura` escalam
    raios e espessura juntos (o desenho todo) até a tinta medir o pedido; com as duas, cabe nas duas."""
    raios = p.get("raios")
    if raios is None and p.get("raio_max") is not None:
        n = int(_medida(p, "quantidade", 4))
        rmax = _medida(p, "raio_max", 100)
        raios = [rmax * (i + 1) / n for i in range(n)]
    if not isinstance(raios, (list, tuple)) or not raios or any(float(r) <= 0 for r in raios):
        raise ValueError("`raios`: use uma lista de raios em px maiores que zero (ou raio_max e quantidade)")
    raios = sorted({float(r) for r in raios})
    esp = _medida(p, "espessura", 1.5)
    a0, a1 = float(p.get("angulo_ini", 0)), float(p.get("angulo_fim", 360))
    if not 0 < a1 - a0 <= 360:
        raise ValueError(f"angulo_ini {a0:g} e angulo_fim {a1:g}: o trecho precisa ter de 0 (exclusive) a 360 graus")
    if raios[0] <= esp / 2:
        raise ValueError(f"o menor raio ({raios[0]:g}) não passa da metade da espessura ({esp / 2:g})")
    cor = _cor_pagina(p.get("cor"), ctx)
    S = int(math.ceil(2 * (raios[-1] + esp / 2))) + 2
    c = S / 2
    inteiro = a1 - a0 >= 360 - 1e-9
    formas, pontos = [], []
    for r in raios:
        if inteiro:
            formas.append(f'<circle cx="{_n(c)}" cy="{_n(c)}" r="{_n(r)}"/>')
        else:
            ini = (c + r * math.cos(math.radians(a0)), c + r * math.sin(math.radians(a0)))
            fim = (c + r * math.cos(math.radians(a1)), c + r * math.sin(math.radians(a1)))
            formas.append(f'<path d="M{_n(ini[0])} {_n(ini[1])}A{_n(r)} {_n(r)} 0 {1 if a1 - a0 > 180 else 0} 1 {_n(fim[0])} {_n(fim[1])}"/>')
            for rr in (r - esp / 2, r + esp / 2):          # setor anular: as duas bordas do traço de ponta reta
                pontos.append(_amostra_arco(c, c, rr, a0, a1))
    if inteiro:
        tinta = [c - raios[-1] - esp / 2, c - raios[-1] - esp / 2, c + raios[-1] + esp / 2, c + raios[-1] + esp / 2]
    else:
        tinta = _caixa_pts(np.vstack(pontos))
    corpo = f'<g fill="none" stroke="{cor}" stroke-width="{_n(esp)}">{"".join(formas)}</g>'
    return dict(svg=_svg(S, S, corpo, "circulos", uid), w=S, h=S, texto="", fontes=[], tinta=tinta)


def _setas(p, ctx, uid):
    """Chevrons em linha (>>>), o ritmo que aponta a direção de leitura ou de movimento. Cada chevron é um traço em quina
    de `tamanho` px de altura. params: quantidade 3; tamanho 28; passo (distância de um chevron ao seguinte; padrão 0,8 x
    tamanho); espessura (padrão 0,16 x tamanho); direcao 'dir' | 'esq' | 'cima' | 'baixo'; cor 'marca'. Medida da tinta:
    `largura`/`altura` escalam tamanho, passo e espessura juntos até a tinta medir o pedido; com as duas, cabe nas duas."""
    n = int(_medida(p, "quantidade", 3))
    tam = _medida(p, "tamanho", 28)
    passo, esp = _medida(p, "passo", round(tam * 0.8, 3)), _medida(p, "espessura", round(tam * 0.16, 3))
    direcao = _escolha(p, "direcao", "dir", tuple(DIRECOES))
    cor = _cor_pagina(p.get("cor"), ctx)
    prof = tam * 0.5
    ao_longo_e_lado = {"dir": lambda a, b: (a, b), "esq": lambda a, b: (-a, b), "baixo": lambda a, b: (b, a), "cima": lambda a, b: (b, -a)}[direcao]
    chevrons, caixas = [], []
    for i in range(n):
        pts = [ao_longo_e_lado(i * passo + a, b) for a, b in ((0.0, 0.0), (prof, tam / 2), (0.0, tam))]
        chevrons.append("M" + "L".join(f"{_n(x)} {_n(y)}" for x, y in pts))
        caixas.append(_tinta_polilinha(pts, esp))
    corpo = (f'<path d="{"".join(chevrons)}" fill="none" stroke="{cor}" stroke-width="{_n(esp)}" stroke-linejoin="miter" '
             'stroke-linecap="butt"/>')
    r, _ = _fechar("setas", uid, corpo, _uniao(caixas))
    return dict(r, texto="", fontes=[])


def _vertices_estrela(cx, cy, R, razao, giro=0.0):
    """Os 10 vértices de uma estrela de 5 pontas com uma ponta para cima (giro em graus, sentido horário)."""
    return [(cx + (R if k % 2 == 0 else R * razao) * math.cos(math.radians(-90 + giro + 36 * k)),
             cy + (R if k % 2 == 0 else R * razao) * math.sin(math.radians(-90 + giro + 36 * k))) for k in range(10)]


def _estrelas(p, ctx, uid):
    """N estrelas de 5 pontas em linha ou em arco (avaliação, categoria, selo de qualidade). Em arco, as estrelas ficam
    sobre uma circunferência e cada uma gira para a ponta de cima apontar para fora do centro; o raio do arco sai do
    passo e do ângulo (o comprimento do arco entre a primeira e a última estrela é passo x (quantidade - 1)).
    params: quantidade 5; tamanho 32 (diâmetro da estrela, ponta a ponta); passo (distância entre os centros; padrão 1,3 x
    tamanho); arco 0 (graus que o arco abre, de 0 = em linha a 180; para cima); razao 0,382 (raio de dentro / raio de
    fora; 0,382 é a estrela regular); estilo 'cheio' | 'contorno'; espessura 1,5 (contorno); cor 'marca'. Medida da tinta:
    `largura`/`altura` escalam tamanho, passo e espessura juntos até a tinta medir o pedido; com as duas, cabe nas duas."""
    n = int(_medida(p, "quantidade", 5))
    tam = _medida(p, "tamanho", 32)
    passo = _medida(p, "passo", round(tam * 1.3, 3))
    arco = float(p.get("arco", 0))
    razao = _medida(p, "razao", 0.382)
    estilo = _escolha(p, "estilo", "cheio", ("cheio", "contorno"))
    esp = _medida(p, "espessura", 1.5)
    if not 0 <= arco <= 180:
        raise ValueError(f"arco {arco:g}: use de 0 (em linha) a 180 graus")
    if not 0.1 <= razao < 1:
        raise ValueError(f"razao {razao:g}: use de 0,1 a menos de 1")
    cor = _cor_pagina(p.get("cor"), ctx)
    R = tam / 2
    if arco == 0 or n == 1:
        estrelas = [_vertices_estrela(R + i * passo, R, R, razao) for i in range(n)]
    else:
        Ra = passo * (n - 1) / math.radians(arco)
        passo_ang = arco / (n - 1)
        estrelas = []
        for i in range(n):
            fi = -90 + (i - (n - 1) / 2) * passo_ang
            estrelas.append(_vertices_estrela(Ra * math.cos(math.radians(fi)), Ra * math.sin(math.radians(fi)), R, razao, fi + 90))
    pintura = (f'fill="{cor}"' if estilo == "cheio" else
               f'fill="none" stroke="{cor}" stroke-width="{_n(esp)}" stroke-linejoin="round"')
    poligonos = "".join(f'<polygon points="{" ".join(f"{_n(x)},{_n(y)}" for x, y in e)}"/>' for e in estrelas)
    pad = 0.0 if estilo == "cheio" else esp / 2        # junta redonda: a tinta passa do vértice em metade da espessura
    tinta = _pad_caixa(_caixa_pts([q for e in estrelas for q in e]), pad)
    r, _ = _fechar("estrelas", uid, f"<g {pintura}>{poligonos}</g>", tinta)
    return dict(r, texto="", fontes=[])




# ---------------------------------------------------------------- campo: desenho técnico de quadra em escala real
# Primitivas em METROS (origem no canto superior esquerdo, x ao longo do campo): linha, rect, circulo, arco (graus, sentido
# horário na tela, 0 = leste), ponto (marca) e estadio (a pista: duas retas e duas semicircunferências). Medidas oficiais:
# futebol 105 x 68 (FIFA: círculo central 9,15; área 16,5 x 40,32; pequena 5,5 x 18,32; marca do pênalti a 11; arco da
# área de 9,15 a partir da marca, só a parte de fora da área; canto de 1); futsal 40 x 20 (círculo central 3; área em
# duas quartas de círculo de 6 m centradas nas traves de 3 m, ligadas por uma reta de 3; marca de pênalti a 6 e segunda
# marca a 10; canto de 0,25); pista de 400 m com 8 raias de 1,22 (reta de 84,39; raio interno 36,50, medido a 0,30 da
# guia: 2 x 84,39 + 2 x pi x 36,80 = 400,0).
def _campo_futebol():
    C, L = 105.0, 68.0
    a = math.degrees(math.acos((16.5 - 11.0) / 9.15))          # onde o arco da área cruza a linha da área (53,05 graus)
    prims = [("rect", "contorno", 0.0, 0.0, C, L), ("linha", "meio-campo", C / 2, 0.0, C / 2, L),
             ("circulo", "circulo-central", C / 2, L / 2, 9.15), ("ponto", "marca-central", C / 2, L / 2)]
    for lado in (0, 1):
        x_gol, s = (0.0, 1.0) if lado == 0 else (C, -1.0)       # s: para dentro do campo
        x_area = 0.0 if lado == 0 else C - 16.5
        x_peq = 0.0 if lado == 0 else C - 5.5
        prims += [("rect", "area", x_area, L / 2 - 20.16, 16.5, 40.32), ("rect", "area-pequena", x_peq, L / 2 - 9.16, 5.5, 18.32),
                  ("ponto", "marca-penalti", x_gol + s * 11.0, L / 2),
                  ("arco", "arco-da-area", x_gol + s * 11.0, L / 2, 9.15, *((-a, a) if lado == 0 else (180 - a, 180 + a)))]
    prims += [("arco", "arco-de-canto", 0.0, 0.0, 1.0, 0, 90), ("arco", "arco-de-canto", C, 0.0, 1.0, 90, 180),
              ("arco", "arco-de-canto", 0.0, L, 1.0, 270, 360), ("arco", "arco-de-canto", C, L, 1.0, 180, 270)]
    janelas = {"inteiro": (0.0, 0.0, C, L, "ltrb"), "meio": (0.0, 0.0, C / 2, L, "ltrb"),
               "area": (0.0, L / 2 - 20.16 - 2, 22.0, 40.32 + 4, "l"), "circulo": (C / 2 - 12, L / 2 - 12, 24.0, 24.0, ""),
               "canto": (0.0, 0.0, 22.0, 18.0, "lt")}
    return C, L, prims, janelas


def _campo_futsal():
    C, L = 40.0, 20.0
    prims = [("rect", "contorno", 0.0, 0.0, C, L), ("linha", "meio-campo", C / 2, 0.0, C / 2, L),
             ("circulo", "circulo-central", C / 2, L / 2, 3.0), ("ponto", "marca-central", C / 2, L / 2)]
    for lado in (0, 1):
        x_gol, s = (0.0, 1.0) if lado == 0 else (C, -1.0)
        for y_trave, (a0, a1) in ((L / 2 - 1.5, (-90, 0) if lado == 0 else (180, 270)), (L / 2 + 1.5, (0, 90) if lado == 0 else (90, 180))):
            prims.append(("arco", "area", x_gol, y_trave, 6.0, a0, a1))
        prims += [("linha", "area", x_gol + s * 6.0, L / 2 - 1.5, x_gol + s * 6.0, L / 2 + 1.5),
                  ("ponto", "marca-penalti", x_gol + s * 6.0, L / 2), ("ponto", "segunda-marca", x_gol + s * 10.0, L / 2)]
    prims += [("arco", "arco-de-canto", 0.0, 0.0, 0.25, 0, 90), ("arco", "arco-de-canto", C, 0.0, 0.25, 90, 180),
              ("arco", "arco-de-canto", 0.0, L, 0.25, 270, 360), ("arco", "arco-de-canto", C, L, 0.25, 180, 270)]
    janelas = {"inteiro": (0.0, 0.0, C, L, "ltrb"), "meio": (0.0, 0.0, C / 2, L, "ltrb"), "area": (0.0, 0.0, 9.5, L, "ltb"),
               "circulo": (C / 2 - 4.5, L / 2 - 4.5, 9.0, 9.0, ""), "canto": (0.0, 0.0, 9.0, 7.0, "lt")}
    return C, L, prims, janelas


def _campo_pista():
    reta, r0, raia, n = 84.39, 36.50, 1.22, 8
    R = r0 + n * raia
    W, H = reta + 2 * R, 2 * R
    prims = [("estadio", "raia", R, R, reta, r0 + j * raia) for j in range(n + 1)]
    prims.append(("linha", "chegada", R + reta, R + r0, R + reta, R + r0 + n * raia))
    janelas = {"inteiro": (0.0, 0.0, W, H, "ltrb"), "meio": (0.0, 0.0, W / 2, H, "ltb"), "circulo": (0.0, 0.0, R, H, "ltb"),
               "canto": (0.0, 0.0, R + 12, R, "lt"), "area": (R + reta - 22, R, 34.0, R, "b")}
    return W, H, prims, janelas


CAMPOS = {"futebol": _campo_futebol, "futsal": _campo_futsal, "pista": _campo_pista}


def _campo_escala(p, ctx):
    """A escala do campo (metros oficiais para px) e a janela do recorte: a parte comum ao campo plano e ao em perspectiva."""
    esporte = _escolha(p, "esporte", "futebol", tuple(CAMPOS))
    recorte = _escolha(p, "recorte", "inteiro", ("inteiro", "meio", "area", "circulo", "canto"))
    ang = float(p.get("angulo", 0))
    ped = _medidas_pedidas(p)
    cor = _cor_pagina(p.get("cor"), ctx)
    _, _, prims, janelas = CAMPOS[esporte]()
    x0m, y0m, jw, jh, flags = janelas[recorte]
    if "espessura" in p:
        esp = _medida(p, "espessura", 2.0)
    else:      # padrão 2 px; na pista as 9 linhas de raia de 1,22 m ficariam coladas em tamanho pequeno: no máximo 1/3 da raia
        esc0 = min(([ped["altura"] / jh] if "altura" in ped else []) + ([ped["largura"] / jw] if "largura" in ped else []) or [800 / jw])
        esp = min(2.0, max(0.75, 1.22 * esc0 / 3)) if esporte == "pista" else 2.0
    pl, pr, pt, pb = (esp / 2 if c in flags else 0.0 for c in "ltrb")
    # a escala em metros segue UMA medida; com as duas (e/ou), a maior escala que cabe nas duas
    escalas = ([(ped["largura"] - pl - pr) / jw] if "largura" in ped else []) + ([(ped["altura"] - pt - pb) / jh] if "altura" in ped else [])
    esc = min(escalas) if escalas else (800 - pl - pr) / jw
    W, H = pl + pr + jw * esc, pt + pb + jh * esc
    if esc <= 0 or esc * jw < 20:
        raise ValueError(f"escala de {esc:.3f} px por metro: largura ou altura pequena demais para o recorte `{recorte}`")
    X = lambda xm: pl + (xm - x0m) * esc      # noqa: E731
    Y = lambda ym: pt + (ym - y0m) * esc      # noqa: E731
    r_marca = max(1.6 * esp, 2.5)
    return esporte, recorte, ang, ped, cor, prims, x0m, y0m, jw, jh, flags, esp, pl, pr, pt, pb, esc, W, H, X, Y, r_marca


def _campo(p, ctx, uid):
    """Linhas de um campo esportivo em escala real, como desenho técnico (contexto de página: a quadra atrás dos números
    de público, o recorte da área no canto). A escala é a do esporte: `largura` ou `altura` em px dá a medida do recorte
    e a outra segue, com os metros oficiais (círculo central do futebol = 9,15 m x escala; a espessura do contorno que cai
    na borda entra na conta: a caixa é a tinta). O contorno que cai na borda do recorte (linha lateral, de fundo,
    meio-campo) entra inteiro, com a espessura toda; as linhas que o recorte corta saem rente à borda (clipPath
    retangular). Cada parte leva `data-parte` (circulo-central, area, arco-da-area, marca-penalti...). Sem goleiras,
    bandeirinhas nem nome do esporte: só as linhas; as marcas (pênalti, centro) são pontos.
    params: esporte 'futebol' (105 x 68 m) | 'futsal' (40 x 20) | 'pista' (400 m, 8 raias, linha de chegada); recorte
    'inteiro' | 'meio' (a metade do lado do gol esquerdo; na pista, a esquerda) | 'area' (a grande área e o arco; no
    futsal, a área do gol; na pista, a chegada) | 'circulo' (o círculo central; na pista, a curva) | 'canto' (o canto e a
    quina da área); largura 800 (ou altura; com as duas, a maior escala que cabe nas duas); espessura 2 (na pista, no
    máximo um terço da raia, para as linhas não se fundirem); angulo 0 (graus, sentido horário; a caixa cresce para conter o
    campo girado: com giro, `largura` e `altura` medem o campo antes de girar); cor 'marca'; perspectiva [[u, v] x 4]
    (opcional: o recorte projetado nos 4 cantos, ver _campo_perspectiva; sem ela, o desenho de sempre, byte a byte)."""
    if p.get("perspectiva") is not None:
        return _campo_perspectiva(p, ctx, uid)
    esporte, recorte, ang, ped, cor, prims, x0m, y0m, jw, jh, flags, esp, pl, pr, pt, pb, esc, W, H, X, Y, r_marca = _campo_escala(p, ctx)
    janela = [0.0, 0.0, W, H]

    def seg_visivel(a, b):
        """Pontas do trecho de a-b que fica dentro da janela (corte exato), como array 2 x 2; vazio quando não passa."""
        t0, t1 = _recorta_reta(a, (b[0] - a[0], b[1] - a[1]), janela)
        t0, t1 = max(t0, 0.0), min(t1, 1.0)       # é um SEGMENTO: o prolongamento da reta que cruza a janela não é desenho
        return np.array([[a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t] for t in (t0, t1)]) if t1 > t0 else np.empty((0, 2))

    def dentro(pts):
        a = np.asarray(pts, float).reshape(-1, 2)
        ok = (a[:, 0] >= -1e-6) & (a[:, 0] <= W + 1e-6) & (a[:, 1] >= -1e-6) & (a[:, 1] <= H + 1e-6)
        return a[ok]

    elementos, tracos, marcas = [], [], []

    def arco(parte, cx, cy, r, a0, a1):
        c, rr = (X(cx), Y(cy)), r * esc
        ini = (c[0] + rr * math.cos(math.radians(a0)), c[1] + rr * math.sin(math.radians(a0)))
        fim = (c[0] + rr * math.cos(math.radians(a1)), c[1] + rr * math.sin(math.radians(a1)))
        elementos.append(f'<path data-parte="{parte}" d="M{_n(ini[0])} {_n(ini[1])}A{_n(rr)} {_n(rr)} 0 {1 if a1 - a0 > 180 else 0} 1 '
                         f'{_n(fim[0])} {_n(fim[1])}"/>')
        tracos.append(dentro(_amostra_arco(c[0], c[1], rr, a0, a1)))

    for prim in prims:
        k, parte = prim[0], prim[1]
        v = prim[2:]
        if k == "linha":
            a, b = (X(v[0]), Y(v[1])), (X(v[2]), Y(v[3]))
            elementos.append(f'<line data-parte="{parte}" x1="{_n(a[0])}" y1="{_n(a[1])}" x2="{_n(b[0])}" y2="{_n(b[1])}"/>')
            tracos.append(seg_visivel(a, b))
        elif k == "rect":
            x, y, w, h = v
            elementos.append(f'<rect data-parte="{parte}" x="{_n(X(x))}" y="{_n(Y(y))}" width="{_n(w * esc)}" height="{_n(h * esc)}"/>')
            for a, b in (((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)), ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))):
                tracos.append(seg_visivel((X(a[0]), Y(a[1])), (X(b[0]), Y(b[1]))))
        elif k == "circulo":
            cx, cy, r = v
            elementos.append(f'<circle data-parte="{parte}" cx="{_n(X(cx))}" cy="{_n(Y(cy))}" r="{_n(r * esc)}"/>')
            tracos.append(dentro(_amostra_arco(X(cx), Y(cy), r * esc, 0, 360)))
        elif k == "arco":
            arco(parte, *v)
        elif k == "ponto":
            cx, cy = X(v[0]), Y(v[1])
            elementos.append(f'<circle data-parte="{parte}" cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r_marca)}" fill="{cor}" stroke="none"/>')
            if 0 <= cx <= W and 0 <= cy <= H:
                marcas.append((cx, cy))
        else:   # estadio: duas retas e duas semicircunferências
            xe, yc, reta_m, r = v
            xa, xb, ya, yb = X(xe), X(xe + reta_m), Y(yc - r), Y(yc + r)
            rr = r * esc
            elementos.append(f'<path data-parte="{parte}" d="M{_n(xa)} {_n(ya)}L{_n(xb)} {_n(ya)}A{_n(rr)} {_n(rr)} 0 0 1 {_n(xb)} {_n(yb)}'
                             f'L{_n(xa)} {_n(yb)}A{_n(rr)} {_n(rr)} 0 0 1 {_n(xa)} {_n(ya)}Z"/>')
            tracos += [seg_visivel((xa, ya), (xb, ya)), seg_visivel((xa, yb), (xb, yb)),
                       dentro(_amostra_arco(xb, Y(yc), rr, -90, 90)), dentro(_amostra_arco(xa, Y(yc), rr, 90, 270))]
    pontos = np.vstack([t for t in tracos if len(t)]) if any(len(t) for t in tracos) else np.empty((0, 2))
    if not len(pontos) and not marcas:
        raise ValueError(f"o recorte `{recorte}` não pega nenhuma linha")
    clip = recorte != "inteiro"
    defs = f'<defs><clipPath id="c-{uid}"><rect width="{_n(W)}" height="{_n(H)}"/></clipPath></defs>' if clip else ""
    grupo = (f'<g fill="none" stroke="{cor}" stroke-width="{_n(esp)}" stroke-linecap="butt"'
             + (f' clip-path="url(#c-{uid})"' if clip else "") + f'>{"".join(elementos)}</g>')
    Wf, Hf = W, H
    centros = np.asarray(marcas, float).reshape(-1, 2)
    if abs(ang) > 1e-9:       # a caixa cresce para conter o campo girado em torno do centro da janela
        t = math.radians(ang)
        c, s_ = math.cos(t), math.sin(t)
        centro = np.array([W / 2, H / 2])
        giro = np.array([[c, -s_], [s_, c]])
        cr = _caixa_pts((np.array([[0, 0], [W, 0], [0, H], [W, H]], float) - centro) @ giro.T + centro)
        tx, ty, Wf, Hf = -cr[0], -cr[1], cr[2] - cr[0], cr[3] - cr[1]
        mover = lambda a: (a - centro) @ giro.T + centro + np.array([tx, ty])      # noqa: E731
        pontos, centros = mover(pontos) if len(pontos) else pontos, mover(centros) if len(centros) else centros
        grupo = f'<g transform="translate({_n(tx)} {_n(ty)}) rotate({_n(ang)} {_n(W / 2)} {_n(H / 2)})">{grupo}</g>'
    caixas = [_pad_caixa(_caixa_pts(pontos), esp / 2)] if len(pontos) else []
    caixas += [[mx - r_marca, my - r_marca, mx + r_marca, my + r_marca] for mx, my in centros]
    caixa = _uniao(caixas)
    caixa = [max(0.0, caixa[0]), max(0.0, caixa[1]), min(Wf, caixa[2]), min(Hf, caixa[3])]
    return dict(svg=_svg(_inteiro(Wf), _inteiro(Hf), defs + grupo, "campo", uid), w=_inteiro(Wf), h=_inteiro(Hf), texto="",
                fontes=[], tinta=caixa)


def _campo_perspectiva(p, ctx, uid):
    """O campo em perspectiva: o desenho técnico do recorte (mesma escala, mesmas partes, mesmos `data-parte`) projetado
    por homografia, calculada em Python, nos 4 cantos de `perspectiva` ([u, v] em fração da caixa: sup-esq, sup-dir,
    inf-dir, inf-esq). Retas continuam retas; círculo e arco viram polilinha densa (um ponto a cada 3 px) projetada; as
    marcas (pênalti, centro) ficam redondas no ponto projetado. O corte do recorte é feito antes de projetar, e o clipPath
    da caixa apara o traço. Sem `angulo` (o giro vem dos cantos)."""
    if float(p.get("angulo", 0)):
        raise ValueError("`perspectiva` com `angulo`: gire o campo pelos cantos da perspectiva")
    esporte, recorte, ang, ped, cor, prims, x0m, y0m, jw, jh, flags, esp, pl, pr, pt, pb, esc, W, H, X, Y, r_marca = _campo_escala(p, ctx)
    _, M = _quadrilatero(p, W, H)
    janela = [0.0, 0.0, W, H]

    def recorta(poli):
        """Os pedaços da polilinha dentro da janela (o recorte do campo), antes de projetar."""
        pecas, atual = [], []
        for a, b in zip(poli, poli[1:]):
            t0, t1 = _recorta_reta(a, (b[0] - a[0], b[1] - a[1]), janela)
            t0, t1 = max(t0, 0.0), min(t1, 1.0)
            if t1 <= t0:
                if len(atual) > 1:
                    pecas.append(atual)
                atual = []
                continue
            pa = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
            pb_ = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
            if atual and t0 == 0.0:
                atual.append(pb_)
            else:
                if len(atual) > 1:
                    pecas.append(atual)
                atual = [pa, pb_]
            if t1 < 1.0:
                pecas.append(atual)
                atual = []
        if len(atual) > 1:
            pecas.append(atual)
        return pecas

    def arco_pts(cx, cy, r, a0, a1):
        n = max(24, int(math.radians(a1 - a0) * r * esc / 3)) + 1
        ang_ = np.radians(np.linspace(a0, a1, n))
        return [(X(cx) + r * esc * math.cos(t), Y(cy) + r * esc * math.sin(t)) for t in ang_]

    elementos, pontos, marcas = [], [], []
    for prim in prims:
        k, parte, v = prim[0], prim[1], prim[2:]
        if k == "linha":
            polis = [[(X(v[0]), Y(v[1])), (X(v[2]), Y(v[3]))]]
        elif k == "rect":
            x, y, w, h = v
            polis = [[(X(x), Y(y)), (X(x + w), Y(y)), (X(x + w), Y(y + h)), (X(x), Y(y + h)), (X(x), Y(y))]]
        elif k == "circulo":
            polis = [arco_pts(v[0], v[1], v[2], 0, 360)]
        elif k == "arco":
            polis = [arco_pts(*v)]
        elif k == "ponto":
            cx, cy = X(v[0]), Y(v[1])
            if 0 <= cx <= W and 0 <= cy <= H:
                q = _projetar(M, [(cx, cy)])[0]
                marcas.append((parte, float(q[0]), float(q[1])))
            continue
        else:      # estadio: reta de cima, curva da direita, reta de baixo, curva da esquerda
            xe, yc, reta_m, r = v
            polis = [[(X(xe), Y(yc - r)), (X(xe + reta_m), Y(yc - r))] + arco_pts(xe + reta_m, yc, r, -90, 90)
                     + [(X(xe), Y(yc + r))] + arco_pts(xe, yc, r, 90, 270)]
        for poli in polis:
            for peca in recorta(poli):
                q = _projetar(M, peca)
                fecha = len(peca) > 2 and math.hypot(peca[0][0] - peca[-1][0], peca[0][1] - peca[-1][1]) < 1e-9
                d = "M" + "L".join(f"{_n(a)} {_n(b)}" for a, b in (q[:-1] if fecha else q)) + ("Z" if fecha else "")
                elementos.append(f'<path data-parte="{parte}" d="{d}"/>')
                pontos.append(q)
    if not pontos and not marcas:
        raise ValueError(f"o recorte `{recorte}` não pega nenhuma linha")
    defs, clip = _recorte_svg(uid, janela)
    grupo = (f'<g fill="none" stroke="{cor}" stroke-width="{_n(esp)}" stroke-linecap="butt" stroke-linejoin="round"{clip}>'
             + "".join(elementos)
             + "".join(f'<circle data-parte="{parte}" cx="{_n(x)}" cy="{_n(y)}" r="{_n(r_marca)}" fill="{cor}" stroke="none"/>'
                       for parte, x, y in marcas) + "</g>")
    caixas = [_pad_caixa(_caixa_pts(np.vstack(pontos)), esp / 2)] if pontos else []
    caixas += [[x - r_marca, y - r_marca, x + r_marca, y + r_marca] for _, x, y in marcas]
    c = _uniao(caixas)
    return dict(svg=_svg(_inteiro(W), _inteiro(H), defs + grupo, "campo", uid), w=_inteiro(W), h=_inteiro(H), texto="", fontes=[],
                tinta=[max(0.0, c[0]), max(0.0, c[1]), min(W, c[2]), min(H, c[3])])

# ---------------------------------------------------------------- placar
_PLACAR = re.compile(r"^\s*(\d+)\s*([xX×:\u2013\u2014-])\s*(\d+)\s*$")        # separador: x, ×, dois-pontos, meia-risca, travessão, hífen


def _placar(p, ctx, uid):
    """Tabela de rodada (placar, resultados, jogos da semana) em texto vivo: data, mandante, placar, visitante, em colunas
    alinhadas e com fios. O placar é partido no separador (2 x 1): o gol do mandante termina rente ao separador e o do
    visitante começa rente a ele, então os separadores e os algarismos ficam em coluna mesmo quando a fonte não tem
    numerais tabulares (com tnum, o SVG pede tabular-nums). Nome que não cabe na coluna reduz a tabela inteira
    (até 70%); abaixo disso é erro. Glifo ausente na fonte = erro nomeando o caractere.
    params: linhas [{data, mandante, placar, visitante}] (1 ou mais; placar '2 x 1', '2-1', '2:1' ou texto livre, como 'W.O.');
    cabecalho (texto do alto, ex.: 'Copa AME Sua Marca · 1ª rodada'; sai em caixa alta); largura 760; tamanho 20 (nomes);
    altura_linha 2,5 x tamanho (ou `altura`, a medida da tinta: a altura de cada linha sai dela); grade True (fios verticais entre as colunas); cor 'marca'; fonte 'corpo' (nomes e datas,
    peso 600); fonte_placar 'display' (peso do kit). `linhas` devolvida: cap do cabeçalho (ou da 1ª linha) e linha de base
    da última linha."""
    linhas = p.get("linhas")
    if not isinstance(linhas, (list, tuple)) or not linhas:
        raise ValueError("`linhas`: use uma lista de {data, mandante, placar, visitante}")
    for i, l in enumerate(linhas):
        faltam = [k for k in ("data", "mandante", "placar", "visitante") if not isinstance(l, dict) or not str(l.get(k, "")).strip()]
        if faltam:
            raise ValueError(f"linha {i + 1} do placar sem {', '.join(faltam)}")
    W = _medida(p, "largura", 760)
    s0 = _medida(p, "tamanho", 20)
    mult_linha = _medida(p, "altura_linha", 2.5)
    cor = _cor_pagina(p.get("cor"), ctx)
    grade = bool(p.get("grade", True))
    fc = fonte(ctx, p.get("fonte", "corpo"), p.get("peso", 600))
    fd = fonte(ctx, p.get("fonte_placar", "display"), p.get("peso_placar"))
    cab = _texto(p, ctx, "cabecalho", True) if p.get("cabecalho") else None
    norm = lambda t: unicodedata.normalize("NFC", " ".join(str(t).split()))     # noqa: E731
    dados = []
    for l in linhas:
        pl = norm(l["placar"])
        m = _PLACAR.match(pl)
        dados.append({"data": norm(l["data"]), "mandante": norm(l["mandante"]), "visitante": norm(l["visitante"]),
                      "placar": pl, "partes": (m.group(1), m.group(2), m.group(3)) if m else None})

    def medidas(s):
        """Larguras das colunas para o corpo s (tudo cresce junto com s, então basta escalar)."""
        sd, sp, px, gap = s * 0.8, s * 1.2, s * 0.9, s * 0.35
        w_data = max(fc.largura(d["data"], sd, 0, True) for d in dados) + 2 * px
        w_m = max(fc.largura(d["mandante"], s) for d in dados) + 2 * px
        w_v = max(fc.largura(d["visitante"], s) for d in dados) + 2 * px
        sep = max(fd.largura(d["partes"][1], sp) for d in dados if d["partes"]) if any(d["partes"] for d in dados) else 0.0
        lado = max([max(fd.largura(d["partes"][0], sp, 0, True), fd.largura(d["partes"][2], sp, 0, True)) for d in dados if d["partes"]] or [0.0])
        livre = max([fd.largura(d["placar"], sp, 0, True) for d in dados if not d["partes"]] or [0.0])
        w_pl = max(2 * lado + sep + 2 * gap, livre) + 2 * px
        nome = max(w_m, w_v)                      # as duas colunas de nome têm a mesma largura: o placar fica no meio
        return dict(sd=sd, sp=sp, px=px, gap=gap, w_data=w_data, w_nome=nome, w_pl=w_pl, sep=sep, total=w_data + 2 * nome + w_pl)

    s = s0
    m = medidas(s)
    if m["total"] > W:
        s = math.floor(s0 * W / m["total"] * 1000) / 1000
        if s < 0.7 * s0:
            raise ValueError(f"a tabela precisa de {m['total']:.0f}px no corpo {s0:g} e a largura é {W:g}px: reduziria para "
                             f"{s:.1f}px (menos de 70%); aumente a largura ou encurte os nomes")
        m = medidas(s)
    ped = _medidas_pedidas(p)
    if "altura" in ped:
        # medida da tinta: a altura de cada linha sai dela (a tinta vai do alto do cabeçalho, ou do fio de cima, ao fio de baixo);
        # linhas apertadas demais (menos de 1,6 x o corpo) reduzem o corpo e a tabela continua cabendo na largura
        for _ in range(12):
            hh_ = s * 0.95 * 2.7 if cab else 0.0
            if cab:
                s_cab_ = s * 0.95
                topo_ink = (hh_ - fd.cap_px(s_cab_)) / 2 + fd.cap_px(s_cab_) - fd.caixa_tinta(cab, s_cab_, _r(0.12 * s_cab_))[3]
            else:
                topo_ink = -1.0
            mult_linha = (ped["altura"] + topo_ink - 1 - hh_) / (len(dados) * s)
            if mult_linha >= 1.6:
                break
            s = math.floor(s * 0.92 * 1000) / 1000
            if s < 0.5 * s0:
                break
            m = medidas(s)
        if mult_linha < 1.6:
            raise ValueError(f"altura {ped['altura']:g} pequena demais para {len(dados)} linhas legíveis (cada linha precisa de pelo "
                             "menos 1,6 x o corpo): aumente a altura ou tire linhas")
    extra = (W - m["total"]) / 2               # a sobra vai igual para as duas colunas de nome
    x_data0, x_m0 = 0.0, m["w_data"]
    x_pl0 = x_m0 + m["w_nome"] + extra
    x_v0 = x_pl0 + m["w_pl"]
    w_m_col, w_v_col = m["w_nome"] + extra, m["w_nome"] + extra
    rh = s * mult_linha
    s_cab = s * 0.95
    ls_cab = _r(0.12 * s_cab)
    hh = s_cab * 2.7 if cab else 0.0
    partes, caixas, textos = [], [], []
    cap_c, cap_d = fc.cap_px(s), fd.cap_px(m["sp"])
    linhas_ref = {}
    if cab:
        base_cab = (hh - fd.cap_px(s_cab)) / 2 + fd.cap_px(s_cab)
        svg_t, bx = _texto_svg(fd, cab, 0.0, base_cab, s_cab, ls_cab, cor)
        partes.append(svg_t); caixas.append(bx); textos.append(cab)
        linhas_ref["cap"] = base_cab - fd.cap_px(s_cab)
    fios, fios_fortes = [], []
    y_base_ultima = 0.0
    for i, d in enumerate(dados):
        topo = hh + i * rh
        yc = topo + rh / 2
        b_c = yc + cap_c / 2
        b_d = yc + cap_d / 2
        svg_t, bx = _texto_svg(fc, d["data"], m["px"], yc + fc.cap_px(m["sd"]) / 2, m["sd"], 0, cor, "start", True, ' fill-opacity="0.7"')
        partes.append(svg_t); caixas.append(bx); textos.append(d["data"])
        svg_t, bx = _texto_svg(fc, d["mandante"], x_m0 + w_m_col - m["px"], b_c, s, 0, cor, "end")
        partes.append(svg_t); caixas.append(bx); textos.append(d["mandante"])
        xc = x_pl0 + m["w_pl"] / 2
        if d["partes"]:
            g1, sep, g2 = d["partes"]
            svg_t, bx = _texto_svg(fd, g1, xc - m["sep"] / 2 - m["gap"], b_d, m["sp"], 0, cor, "end", True)
            partes.append(svg_t); caixas.append(bx); textos.append(g1)
            svg_t, bx = _texto_svg(fd, sep, xc, b_d, m["sp"], 0, cor, "middle")
            partes.append(svg_t); caixas.append(bx); textos.append(sep)
            svg_t, bx = _texto_svg(fd, g2, xc + m["sep"] / 2 + m["gap"], b_d, m["sp"], 0, cor, "start", True)
            partes.append(svg_t); caixas.append(bx); textos.append(g2)
        else:
            svg_t, bx = _texto_svg(fd, d["placar"], xc, b_d, m["sp"], 0, cor, "middle", True)
            partes.append(svg_t); caixas.append(bx); textos.append(d["placar"])
        svg_t, bx = _texto_svg(fc, d["visitante"], x_v0 + m["px"], b_c, s, 0, cor, "start")
        partes.append(svg_t); caixas.append(bx); textos.append(d["visitante"])
        y_base_ultima = b_c
        (fios_fortes if i == len(dados) - 1 else fios).append(topo + rh)
    if "cap" not in linhas_ref:
        linhas_ref["cap"] = hh + rh / 2 - cap_c / 2
    linhas_ref["linha_base"] = y_base_ultima
    fim = hh + len(dados) * rh
    esp_forte, esp_fino = 2.0, 1.0
    fios_fortes.append(hh if cab else 0.0)        # com cabeçalho, o fio forte fecha o cabeçalho; sem ele, abre a tabela
    reg = []
    for y in sorted(set(fios)):
        reg.append(f'<path d="M0 {_n(y)}L{_n(W)} {_n(y)}" stroke-width="{_n(esp_fino)}" stroke-opacity="0.35"/>')
    for y in sorted(set(fios_fortes)):
        reg.append(f'<path d="M0 {_n(y)}L{_n(W)} {_n(y)}" stroke-width="{_n(esp_forte)}"/>')
        caixas.append([0.0, y - esp_forte / 2, W, y + esp_forte / 2])
    if grade:
        for x in (m["w_data"], x_pl0, x_v0):
            reg.append(f'<path d="M{_n(x)} {_n(hh)}L{_n(x)} {_n(fim)}" stroke-width="{_n(esp_fino)}" stroke-opacity="0.35"/>')
    partes.insert(0, f'<g fill="none" stroke="{cor}">{"".join(reg)}</g>')
    ink = _uniao(caixas)
    ink = [min(ink[0], 0.0), ink[1], max(ink[2], W), ink[3]]
    r, (dx, dy) = _fechar("placar", uid, "".join(partes), ink)
    linhas_ref = {k: v + dy for k, v in linhas_ref.items()}
    return dict(r, texto="\n".join(textos), fontes=list(dict.fromkeys([fc.familia, fd.familia])), linhas=linhas_ref)


# ---------------------------------------------------------------- celular
def _img_uri(im, largura_px, jpeg=False):
    """data URI da imagem reduzida (nunca ampliada) a `largura_px` de largura; JPEG q88 quando veio de JPEG (foto), PNG nos
    outros casos (captura de tela)."""
    if im.width > largura_px:
        im = im.resize((int(largura_px), max(1, round(im.height * largura_px / im.width))), Image.LANCZOS)
    b = io.BytesIO()
    if jpeg:
        im.convert("RGB").save(b, "JPEG", quality=88, optimize=True)
    else:
        im.save(b, "PNG", optimize=True)
    return f"data:{'image/jpeg' if jpeg else 'image/png'};base64," + base64.b64encode(b.getvalue()).decode()


def _celular(p, ctx, uid):
    """Moldura de celular por código (corpo de cantos arredondados, borda da tela e a ilha da câmera) em volta de uma
    imagem: a captura do app, o perfil do evento, o QR. A imagem é a ÚNICA do svg: entra como <image> recortada pelos
    cantos arredondados da tela (clipPath) e cobre a tela inteira (o que passa da proporção é cortado, centrado); ela é
    reduzida a no máximo 2x o tamanho da tela e nunca ampliada. Sem alfa: onde a imagem for transparente aparece a cor do
    corpo (alfa viraria uma segunda imagem no PDF). O corpo é escuro (paleta 'escuro') com um fio fino no acento da página.
    params: imagem (PNG ou JPG, obrigatório); largura 360 (ou `altura`: a medida do corpo, a outra segue a proporção; com as
    duas, cabe nas duas); proporcao 2,1667 (altura / largura do corpo; 19,5:9);
    moldura (borda entre o corpo e a tela; padrão 3,6% da largura); raio (cantos do corpo; padrão 15% da largura);
    ilha True; fundo 'escuro' (cor do corpo e da ilha; 'marca' = o acento da página); contorno True (fio do corpo, 1,5 px,
    no acento da página)."""
    caminho = p.get("imagem")
    if not caminho or not Path(caminho).is_file():
        raise ValueError(f"`imagem` não encontrada: {caminho!r} (PNG ou JPG)")
    prop = _medida(p, "proporcao", 19.5 / 9)
    ped = _medidas_pedidas(p)
    # medida da tinta (o corpo é a caixa): a altura pedida dá a largura pela proporção; com as duas, cabe nas duas
    W = (ped["altura"] / prop if "largura" not in ped else min(ped["largura"], ped["altura"] / prop)) if "altura" in ped else _medida(p, "largura", 360)
    H = W * prop
    B = _medida(p, "moldura", round(W * 0.036, 2))
    R = _medida(p, "raio", round(W * 0.15, 2))
    if 2 * B >= W or R > W / 2:
        raise ValueError(f"moldura {B:g} e raio {R:g} não cabem num corpo de {W:g} px de largura")
    pal = ctx.get("paleta") or {}
    fundo = _cor_pagina(p.get("fundo"), ctx, "escuro" if "escuro" in pal else "#0B0B0C")
    if fundo == "none":
        raise ValueError("`fundo` transparente: o corpo do celular precisa de cor")
    contorno = bool(p.get("contorno", True))
    sw, sh = W - 2 * B, H - 2 * B
    im0 = Image.open(caminho)
    jpeg = (im0.format or "").upper() in ("JPEG", "MPO")
    im = im0.convert("RGBA")
    base = tuple(int(fundo[i:i + 2], 16) for i in (1, 3, 5)) if re.fullmatch(r"#[0-9A-F]{6}", fundo) else (0, 0, 0)
    im = Image.alpha_composite(Image.new("RGBA", im.size, base + (255,)), im).convert("RGB")
    alvo = sw / sh                              # cobrir a tela: corta o que passar da proporção, centrado
    if im.width / im.height > alvo:
        nw = max(1, round(im.height * alvo))
        im = im.crop(((im.width - nw) // 2, 0, (im.width - nw) // 2 + nw, im.height))
    else:
        nh = max(1, round(im.width / alvo))
        im = im.crop((0, (im.height - nh) // 2, im.width, (im.height - nh) // 2 + nh))
    uri = _img_uri(im, round(sw * 2), jpeg)
    esp_c = 1.5 if contorno else 0.0
    o = esp_c / 2
    corpo = (f'<rect x="{_n(o)}" y="{_n(o)}" width="{_n(W - esp_c)}" height="{_n(H - esp_c)}" rx="{_n(max(0.0, R - o))}" fill="{fundo}"'
             + (f' stroke="{PAGINA}" stroke-width="{_n(esp_c)}"' if contorno else "") + "/>")
    rs = max(0.5, R - B)
    corpo += (f'<defs><clipPath id="t-{uid}"><rect x="{_n(B)}" y="{_n(B)}" width="{_n(sw)}" height="{_n(sh)}" rx="{_n(rs)}"/></clipPath></defs>'
              f'<image href="{uri}" x="{_n(B)}" y="{_n(B)}" width="{_n(sw)}" height="{_n(sh)}" preserveAspectRatio="xMidYMid slice" '
              f'clip-path="url(#t-{uid})"/>')
    if p.get("ilha", True):
        iw, ih = W * 0.30, H * 0.043
        corpo += (f'<rect x="{_n((W - iw) / 2)}" y="{_n(B + H * 0.013)}" width="{_n(iw)}" height="{_n(ih)}" rx="{_n(ih / 2)}" '
                  f'fill="{fundo}"/>')
    return dict(svg=_svg(_inteiro(W), _inteiro(H), corpo, "celular", uid), w=_inteiro(W), h=_inteiro(H), texto="", fontes=[],
                tinta=[0.0, 0.0, W, H])


# ---------------------------------------------------------------- mapa esquemático
RAIO_TERRA_KM = 6371.0088


def _colide(a, b, folga=2.0):
    return a[0] < b[2] + folga and a[2] > b[0] - folga and a[1] < b[3] + folga and a[3] > b[1] - folga


def _sobreposicao(a, ocupados):
    return sum(max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1])) for b in ocupados)


def _mapa(p, ctx, uid):
    """Mapa esquemático: pontos por latitude e longitude (projeção equirretangular centrada nos próprios pontos, com a
    longitude encolhida por cos(latitude) para o círculo sair redondo), anéis de alcance em km em volta do ponto de destaque
    e rótulos em texto vivo. SEM contorno de estado, costa ou rio: não temos malha geográfica, então o mapa mostra posição e
    distância, nunca o território (para o território, use uma foto ou ilustração). A escala é a mesma nos dois eixos e cabe
    todos os pontos e o maior anel na caixa, com `margem` de folga; cada rótulo tenta as 8 posições em volta do ponto, perto
    e depois mais longe, e fica no primeiro lugar livre (se nenhum estiver livre, no que menos se sobrepõe).
    params: pontos [{nome, lat, lon, destaque, rotulo}] (o primeiro com destaque: true é o centro dos anéis; rotulo: false
    deixa o ponto sem nome, para descongestionar); aneis [km, ...];
    largura 720; altura 480 (com uma só das duas, a outra segue a proporção do conteúdo; a medida é a da tinta); margem 56;
    tamanho 15 (rótulos; o do destaque é 25% maior e na fonte display);
    rotulo_aneis '{km} KM'; caixa_alta True; fonte 'corpo' (peso 600); cor 'marca'. Rótulo que só cabe longe do ponto leva
    um fio fino até ele; se nenhum lugar estiver livre, é erro (com a saída: caixa maior, `tamanho` menor ou `rotulo: false`).
    Devolve `linhas` (cap do rótulo mais alto e linha de base do mais baixo)."""
    pts = p.get("pontos")
    if not isinstance(pts, (list, tuple)) or not pts:
        raise ValueError("`pontos`: use [{nome, lat, lon, destaque}]")
    for i, q in enumerate(pts):
        if not isinstance(q, dict) or not str(q.get("nome", "")).strip():
            raise ValueError(f"ponto {i + 1} sem `nome`")
        try:
            lat, lon = float(q["lat"]), float(q["lon"])
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"ponto `{q.get('nome')}`: `lat` e `lon` precisam ser números em graus") from None
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError(f"ponto `{q.get('nome')}`: lat {lat:g} / lon {lon:g} fora do mundo")
    margem = _medida(p, "margem", 56, 0, estrito=False)
    s = _medida(p, "tamanho", 15)
    aneis = sorted(float(k) for k in (p.get("aneis") or []))
    if any(k <= 0 for k in aneis):
        raise ValueError("`aneis`: os raios precisam ser km maiores que zero")
    centro = next((i for i, q in enumerate(pts) if q.get("destaque")), None)
    if aneis and centro is None:
        raise ValueError("`aneis` precisam de um ponto com `destaque: true` (o centro dos anéis)")
    lat0 = sum(float(q["lat"]) for q in pts) / len(pts)
    lon0 = sum(float(q["lon"]) for q in pts) / len(pts)
    k_lon = RAIO_TERRA_KM * math.cos(math.radians(lat0)) * math.pi / 180
    k_lat = RAIO_TERRA_KM * math.pi / 180
    xy = [((float(q["lon"]) - lon0) * k_lon, -(float(q["lat"]) - lat0) * k_lat) for q in pts]      # km, norte para cima
    ext = [(x, y, x, y) for x, y in xy]
    if aneis:
        cx_k, cy_k = xy[centro]
        ext.append((cx_k - aneis[-1], cy_k - aneis[-1], cx_k + aneis[-1], cy_k + aneis[-1]))
    e = _uniao(ext)
    ew, eh = e[2] - e[0], e[3] - e[1]
    if ew <= 1e-9 and eh <= 1e-9:
        raise ValueError("o mapa precisa de 2 pontos em lugares diferentes ou de anéis em volta do destaque")
    ped = _medidas_pedidas(p)
    if len(ped) == 1 and ew > 1e-9 and eh > 1e-9:
        # uma medida só (a composição pede a tinta): a escala nasce dela e a outra dimensão segue a proporção do conteúdo
        if "largura" in ped:
            W = ped["largura"]; H = (W - 2 * margem) * eh / ew + 2 * margem
        else:
            H = ped["altura"]; W = (H - 2 * margem) * ew / eh + 2 * margem
    else:
        W, H = _medida(p, "largura", 720), _medida(p, "altura", 480)
    if W - 2 * margem <= 0 or H - 2 * margem <= 0:
        raise ValueError(f"margem {margem:g} não deixa área no mapa de {W:g} x {H:g}")
    esc = min(v for v in ((W - 2 * margem) / ew if ew > 1e-9 else None, (H - 2 * margem) / eh if eh > 1e-9 else None) if v is not None)
    xc, yc = (e[0] + e[2]) / 2, (e[1] + e[3]) / 2
    pos = [(W / 2 + (x - xc) * esc, H / 2 + (y - yc) * esc) for x, y in xy]                       # px
    cor = _cor_pagina(p.get("cor"), ctx)
    fc = fonte(ctx, p.get("fonte", "corpo"), p.get("peso", 600))
    fd = fonte(ctx, "display")
    alta = bool(p.get("caixa_alta", True))
    ocupados, svg_aneis, svg_pontos, svg_rotulos, textos, caixas = [], [], [], [], [], []
    for q, (px, py) in zip(pts, pos):
        r = 7.0 if q.get("destaque") else 4.0
        ocupados.append([px - r - 4, py - r - 4, px + r + 4, py + r + 4])
        if q.get("destaque"):
            svg_pontos.append(f'<circle cx="{_n(px)}" cy="{_n(py)}" r="7" fill="{cor}"/>'
                              f'<circle cx="{_n(px)}" cy="{_n(py)}" r="12" fill="none" stroke="{cor}" stroke-width="1.5"/>')
            caixas.append([px - 12.75, py - 12.75, px + 12.75, py + 12.75])
        else:
            svg_pontos.append(f'<circle cx="{_n(px)}" cy="{_n(py)}" r="4" fill="{cor}"/>')
            caixas.append([px - 4, py - 4, px + 4, py + 4])
    dentro = lambda c: c[0] >= 2 and c[1] >= 2 and c[2] <= W - 2 and c[3] <= H - 2      # noqa: E731
    sa = _r(s * 0.85)
    fmt = str(p.get("rotulo_aneis", "{km} KM"))
    bases_rot = []
    if aneis:
        cx, cy = pos[centro]
        for km in aneis:
            rr = km * esc
            svg_aneis.append(f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(rr)}" fill="none" stroke="{cor}" stroke-width="1.2" '
                             'stroke-opacity="0.55" stroke-dasharray="4 5"/>')
            caixas.append([cx - rr - 0.6, cy - rr - 0.6, cx + rr + 0.6, cy + rr + 0.6])
            txt = fmt.replace("{km}", _numero_br(km))
            txt = unicodedata.normalize("NFC", txt.upper() if alta else txt)
            cands = []
            for ang in (-40, 40, -140, 140):
                a = math.radians(ang)
                x, y = cx + (rr + 7) * math.cos(a), cy + (rr + 7) * math.sin(a)
                ancora = "start" if math.cos(a) >= 0 else "end"
                svg_t, bx = _texto_svg(fc, txt, x, y + fc.cap_px(sa) / 2, sa, _r(0.06 * sa), cor, ancora, True, ' fill-opacity="0.8"')
                cands.append((svg_t, bx, y + fc.cap_px(sa) / 2))
            ok = next((c for c in cands if dentro(c[1]) and not any(_colide(c[1], o) for o in ocupados)), None) \
                or next((c for c in cands if dentro(c[1])), cands[0])
            svg_rotulos.append(ok[0]); ocupados.append(ok[1]); caixas.append(ok[1]); textos.append(txt)
            bases_rot.append((ok[2] - fc.cap_px(sa), ok[2]))
    # o destaque escolhe primeiro; depois, os pontos mais apertados (mais vizinhos a menos de 120 px), que têm menos opção
    apertos = [sum(1 for j, (qx, qy) in enumerate(pos) if j != i and math.hypot(qx - pos[i][0], qy - pos[i][1]) < 120) for i in range(len(pts))]
    ordem = sorted(range(len(pts)), key=lambda i: (not pts[i].get("destaque"), -apertos[i], i))
    guias, nomes = [], []
    for i in ordem:
        q, (px, py) = pts[i], pos[i]
        if q.get("rotulo") is False:
            continue                                                                      # ponto sem rótulo: descongestiona
        dest = bool(q.get("destaque"))
        f_t, s_t = (fd, _r(s * 1.25)) if dest else (fc, s)
        ls = _r(0.06 * s_t)
        txt = unicodedata.normalize("NFC", " ".join(str(q["nome"]).split()))
        txt = txt.upper() if alta else txt
        r = 7.0 + 6.0 if dest else 4.0
        cap = f_t.cap_px(s_t)
        cands = []
        for nivel, d in enumerate((r + 8, r + 8 + 0.9 * s_t, r + 8 + 1.9 * s_t)):     # perto do ponto; sem lugar, uma volta mais longe
            h = d * 0.72
            for ancora, x, base in (("start", px + d, py + cap / 2), ("end", px - d, py + cap / 2), ("middle", px, py - d),
                                    ("middle", px, py + d + cap), ("start", px + h, py - h), ("end", px - h, py - h),
                                    ("start", px + h, py + h + cap), ("end", px - h, py + h + cap)):
                svg_t, bx = _texto_svg(f_t, txt, x, base, s_t, ls, cor, ancora)
                cands.append((nivel, svg_t, bx, base))
        livre = next((c for c in cands if dentro(c[2]) and not any(_colide(c[2], o) for o in ocupados)), None)
        if livre is None:
            raise ValueError(f"o rótulo `{txt}` não encontra lugar sem cobrir outro rótulo ou ponto no mapa de {W:g} x {H:g}: aumente a "
                             f"caixa, reduza `tamanho` ({s:g}) ou marque pontos com `rotulo: false`")
        nivel, svg_t, bx, base = livre
        if nivel > 0:       # rótulo afastado do ponto: um fio fino do ponto até a borda mais próxima do texto liga os dois
            qx, qy = min(max(px, bx[0]), bx[2]), min(max(py, bx[1]), bx[3])
            dist = math.hypot(qx - px, qy - py)
            if dist > r + 4:
                ux, uy = (qx - px) / dist, (qy - py) / dist
                a, b = (px + ux * (r + 1), py + uy * (r + 1)), (qx - ux * 2, qy - uy * 2)
                guias.append(f'<path d="M{_n(a[0])} {_n(a[1])}L{_n(b[0])} {_n(b[1])}" fill="none" stroke="{cor}" stroke-width="1" '
                             'stroke-opacity="0.6"/>')
                caixas.append(_caixa_pts(_retangulo_traco(a, b, 1.0)))
        nomes.append((i, svg_t, txt)); ocupados.append(bx); caixas.append(bx)
        bases_rot.append((base - cap, base))
    for _, svg_t, txt in sorted(nomes):               # o texto sai na ordem em que os pontos foram dados, não na da colocação
        svg_rotulos.append(svg_t); textos.append(txt)
    topo = min(b[0] for b in bases_rot)
    base = max(b[1] for b in bases_rot)
    tinta = _uniao(caixas)
    corpo = "".join(svg_aneis) + "".join(guias) + "".join(svg_pontos) + "".join(svg_rotulos)
    return dict(svg=_svg(_inteiro(W), _inteiro(H), corpo, "mapa", uid), w=_inteiro(W), h=_inteiro(H), texto="\n".join(textos),
                fontes=list(dict.fromkeys([fc.familia, fd.familia])), tinta=tinta, linhas={"linha_base": base, "cap": topo})


# ---------------------------------------------------------------- constantes de borda (sistema_elementos.constantes)
def _fio_borda(p, ctx, uid):
    """Constante do sistema: fio rente à borda da página, de ponta a ponta (o `fio` já com os pontos postos). A caixa é a
    do próprio fio, sem margem: largura x ceil(espessura). params: largura 1920; espessura 2 (ou `altura`, a medida da tinta:
    sem `espessura`, a altura é a espessura); tracejado [traço, vão] ou null; cor 'marca'."""
    W = _medida(p, "largura", 1920)
    esp = _medida(p, "espessura", p["altura"] if p.get("espessura") is None and p.get("altura") is not None else 2.0)
    h = _inteiro(esp)
    traco = p.get("tracejado")
    if traco is not None and not (isinstance(traco, (list, tuple)) and len(traco) == 2 and all(float(v) > 0 for v in traco)):
        raise ValueError("`tracejado`: use [traço, vão] em px (maiores que zero) ou null")
    da = f' stroke-dasharray="{_n(traco[0])} {_n(traco[1])}"' if traco else ""
    cor = _cor_pagina(p.get("cor"), ctx)
    corpo = f'<path d="M0 {_n(h / 2)}L{_n(W)} {_n(h / 2)}" fill="none" stroke="{cor}" stroke-width="{_n(esp)}"{da}/>'
    return dict(svg=_svg(_inteiro(W), h, corpo, "fio-borda", uid), w=_inteiro(W), h=h, texto="", fontes=[],
                tinta=[0.0, (h - esp) / 2, W, (h + esp) / 2])


def _pattern_borda(p, ctx, uid):
    """Constante do sistema: faixa de padrão geométrico na borda da página. É um dos padrões de composição com a faixa já
    dimensionada. params: padrao 'linhas' (hachura a -45 graus, espaçamento 10) | 'listras' (faixa de advertência) |
    'pontos' (grade de pontos, passo 16); largura 1920; altura 48; e os parâmetros do padrão escolhido (espacamento,
    angulo, largura_listra, cores, passo, raio, esmaecer, cor...)."""
    padrao = _escolha(p, "padrao", "linhas", ("linhas", "listras", "pontos"))
    q = {k: v for k, v in p.items() if k != "padrao"}
    q.setdefault("largura", 1920)
    q.setdefault("altura", 48)
    if padrao == "linhas":
        q.setdefault("angulo", -45)
        q.setdefault("espacamento", 10)
    elif padrao == "pontos":
        q.setdefault("passo", 16)
    r = {"linhas": _linhas, "listras": _listras, "pontos": _grade_pontos}[padrao](q, ctx, uid)
    r["svg"] = re.sub(r'data-grafismo="[^"]+"', 'data-grafismo="pattern-borda"', r["svg"], count=1)
    return r


# ================================================================ acabamento (Frente G, 12/10/2026)
# Grafismos de textura, borda, profundidade e tipografia expressiva (plano de 12/10, parte C1). Herdam as regras da
# composição (bloco acima): o acento sai em currentColor (no acabamento o CSS põe var(--texto), tom sobre tom); nada de
# filter, gradiente, máscara suave ou <pattern>; o único recorte é o clipPath retangular, duro e vetorial; texto vivo só
# por <text> PREENCHIDO ou <textPath> (contorno de letra nunca é <text> com stroke, que o PDF pode virar Type 3: é <path>
# tirado da própria fonte pelo fontTools); esmaecer só em degraus de opacidade; acaso só com `semente` explícita. Todos
# devolvem `tinta` e, quando desenham letra, `linhas`. `largura` e `altura` medem a tinta: os de área estão em
# CORRIGIR_DUAS (as duas medidas acertadas juntas, sem mexer no legado de CORRIGIR); os de proporção fixa (eco,
# texto-curva) acham o tamanho sozinhos.
ESPACO = {"e1": 8, "e2": 16, "e3": 24, "e4": 32, "e5": 48, "e6": 64, "e7": 96, "e8": 128}   # a escala de espaço da composição
DEGRAUS_OPACIDADE = (1.0, 0.72, 0.46, 0.24, 0.12, 0.06)      # os degraus do contrato (composicao_elemento.efeito.opacidade)


def _espaco(p, chave, padrao):
    """Distância em px: um degrau da escala de espaço (e1 a e8) ou px."""
    v = p.get(chave, padrao)
    if isinstance(v, str) and v in ESPACO:
        return float(ESPACO[v])
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise ValueError(f"`{chave}` `{v}`: use um degrau ({', '.join(f'{k}={n}' for k, n in ESPACO.items())}) ou px") from None
    if not math.isfinite(x) or x < 0:
        raise ValueError(f"`{chave}` precisa ser pelo menos 0 (recebi {x:g})")
    return x


def _rumo(p, chave, padrao):
    """Vetor unitário de uma direção: dir, esq, baixo, cima ou graus (sentido horário, 0 = para a direita)."""
    d = p.get(chave, padrao)
    if isinstance(d, str) and d in DIRECOES:
        return DIRECOES[d]
    if isinstance(d, (int, float)) and not isinstance(d, bool) and math.isfinite(d):
        return (math.cos(math.radians(d)), math.sin(math.radians(d)))
    raise ValueError(f"`{chave}` `{d}`: use {', '.join(DIRECOES)} ou um ângulo em graus (sentido horário, 0 = para a direita)")


def _opacidades(p, n, padrao=(0.24, 0.12, 0.06)):
    """Uma opacidade por cópia, só dos degraus do contrato (esmaecer é em degrau, nunca contínuo)."""
    ops = p.get("opacidades", list(padrao))
    if not isinstance(ops, (list, tuple)) or len(ops) < n:
        raise ValueError(f"`opacidades`: uma por cópia ({n}), dos degraus {', '.join(_n(d) for d in DEGRAUS_OPACIDADE)}")
    saida = []
    for o in ops[:n]:
        try:
            o = float(o)
        except (TypeError, ValueError):
            raise ValueError(f"opacidade {o!r}: use um número dos degraus") from None
        if not any(abs(o - d) < 1e-9 for d in DEGRAUS_OPACIDADE):
            raise ValueError(f"opacidade {o:g} fora dos degraus ({', '.join(_n(d) for d in DEGRAUS_OPACIDADE)}): esmaecer é só em degrau")
        saida.append(o)
    return saida


def _uv(p, chave, padrao):
    v = p.get(chave, padrao)
    try:
        u, w = (float(x) for x in v)
    except (TypeError, ValueError):
        raise ValueError(f"`{chave}`: use [u, v] em fração da caixa (0 a 1; [0.5, 0.5] é o centro)") from None
    if not (math.isfinite(u) and math.isfinite(w)):
        raise ValueError(f"`{chave}` {v}: use números")
    return u, w


def _corpo_svg(svg):
    """O que vai dentro do <svg ...> (para juntar desenhos de outro gerador sem mexer nele)."""
    return svg[svg.index(">") + 1:svg.rindex("</svg>")]


def _recorte_svg(uid, caixa, prefixo="c"):
    """clipPath retangular, duro e vetorial: (defs, atributo clip-path)."""
    x0, y0, x1, y1 = caixa
    return (f'<defs><clipPath id="{prefixo}-{uid}"><rect x="{_n(x0)}" y="{_n(y0)}" width="{_n(x1 - x0)}" '
            f'height="{_n(y1 - y0)}"/></clipPath></defs>', f' clip-path="url(#{prefixo}-{uid})"')


def _homografia(origem, destino):
    """Matriz 3 x 3 da transformação projetiva que leva os 4 pontos de `origem` nos 4 de `destino` (DLT, h33 = 1)."""
    A, b = [], []
    for (x, y), (u, v) in zip(origem, destino):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    try:
        h = np.linalg.solve(np.asarray(A, float), np.asarray(b, float))
    except np.linalg.LinAlgError:
        raise ValueError("perspectiva degenerada: 3 dos 4 cantos estão alinhados") from None
    return np.append(h, 1.0).reshape(3, 3)


def _projetar(M, pts):
    a = np.asarray(pts, float).reshape(-1, 2)
    q = np.c_[a, np.ones(len(a))] @ M.T
    return q[:, :2] / q[:, 2:3]


def _quadrilatero(p, W, H, inset=0.0, chave="perspectiva"):
    """Os 4 cantos de `perspectiva` ([u, v] em fração da caixa, na ordem sup-esq, sup-dir, inf-dir, inf-esq) em px, e a
    homografia que leva o retângulo [inset, W - inset] x [inset, H - inset] para eles. O quadrilátero precisa ser convexo
    e na ordem (uma volta no sentido horário da tela): senão a malha dobra sobre si mesma."""
    q = p.get(chave)
    if not (isinstance(q, (list, tuple)) and len(q) == 4 and all(isinstance(c, (list, tuple)) and len(c) == 2 for c in q)):
        raise ValueError(f"`{chave}`: use 4 cantos [[u, v], ...] em fração da caixa (sup-esq, sup-dir, inf-dir, inf-esq)")
    cantos = [(inset + float(u) * (W - 2 * inset), inset + float(v) * (H - 2 * inset)) for u, v in q]
    for i in range(4):
        a, b, c = cantos[i], cantos[(i + 1) % 4], cantos[(i + 2) % 4]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) <= 1e-9:
            raise ValueError(f"`{chave}` {q}: os 4 cantos têm de formar um quadrilátero convexo, na ordem sup-esq, sup-dir, "
                             "inf-dir, inf-esq")
    origem = [(inset, inset), (W - inset, inset), (W - inset, H - inset), (inset, H - inset)]
    return cantos, _homografia(origem, cantos)


def _corrigir_duas(tipo, params, ctx, uid, r):
    """Tipo de área novo: `largura`/`altura` são a caixa e a tinta é menos (esmaecer, centro fora, borda vazia). Com UMA
    medida, a secante do _corrigir_pela_tinta; com as DUAS, cada dimensão da caixa anda o que falta à tinta (a tinta cresce
    quase 1 para 1 com a caixa) até as duas baterem. Quando a tinta não responde à caixa (recorte, alcance ou raio_max em
    px prendem o desenho), não há caixa que acerte: vale a caixa pedida, como nos tipos antigos de CORRIGIR (que continuam
    como eram)."""
    alvo = _medidas_pedidas(params)
    if not alvo:
        return r
    if len(alvo) == 1:
        dim, px = next(iter(alvo.items()))
        r2 = _corrigir_pela_tinta(tipo, params, ctx, uid, r)
        return r2 if abs(_dim_tinta(r2, dim) - px) <= 0.5 else r
    caixa, melhor, melhor_inicial = dict(alvo), None, r
    for _ in range(12):
        falta = {d: alvo[d] - _dim_tinta(r, d) for d in alvo}
        erro = max(abs(v) for v in falta.values())
        if melhor is not None and erro >= melhor[0] - 0.01:
            break                      # a tinta não responde à caixa (recorte em px, por exemplo): fica a melhor até aqui
        melhor = (erro, r)
        if erro <= 0.3:
            break
        caixa = {d: caixa[d] + falta[d] for d in alvo}
        r = TIPOS[tipo](dict(params, **{d: round(v, 3) for d, v in caixa.items()}), ctx, uid)
    return melhor[1] if melhor[0] <= 0.5 else melhor_inicial


# ---------------------------------------------------------------- hachura, malha
def _hachura(p, ctx, uid):
    """Hachura cruzada: o padrão de `linhas` em dois (ou mais) ângulos sobre a mesma caixa, com o mesmo espaçamento,
    espessura, densidade, esmaecer e recorte. A lógica é a de `linhas`, chamada uma vez por ângulo (o número de linhas de
    cada família segue o espaçamento do mesmo jeito). Cada traço sai como o retângulo dele (preenchido) e os das famílias que
    caem no mesmo degrau vão num path só: o cruzamento não soma opacidade (traço fino com stroke vira hairline no Chromium,
    que soma no cruzamento e destoa do PDF), o tom é igual no cruzamento e a tinta de cada família vale para a hachura.
    Gravura, planta, papel de segurança.
    params: largura 600; altura 400; espacamento 12; angulos [-45, 45] (dois ou mais, nenhum repetido nem a 180 graus de
    outro); espessura 1; densidade 1; esmaecer; recorte; cor 'marca'. A tinta é a união das famílias."""
    angulos = p.get("angulos", [-45, 45])
    if not isinstance(angulos, (list, tuple)) or len(angulos) < 2:
        raise ValueError("`angulos`: use uma lista com dois ângulos ou mais (graus, sentido horário; [-45, 45] é a cruzada)")
    try:
        angulos = [float(a) for a in angulos]
    except (TypeError, ValueError):
        raise ValueError(f"`angulos` {angulos}: use números (graus)") from None
    if len({round(a % 180, 6) for a in angulos}) < len(angulos):
        raise ValueError(f"`angulos` {angulos}: dois deles desenham a mesma família (iguais ou a 180 graus um do outro)")
    base = {k: v for k, v in p.items() if k != "angulos"}
    base.setdefault("espacamento", 12)
    base.setdefault("espessura", 1)
    esp = _medida(base, "espessura", 1)
    por_op, tintas, inclinada, w, h = {}, [], False, 0, 0
    for i, a in enumerate(angulos):
        r = _linhas(dict(base, angulo=a), ctx, f"{uid}-{i}")
        corpo = _corpo_svg(r["svg"])
        inclinada |= "clip-path=" in corpo
        for d, op in re.findall(r'<path d="([^"]+)"(?: stroke-opacity="([\d.]+)")?/>', corpo):
            for x0, y0, x1, y1 in re.findall(r"M([-\d.]+) ([-\d.]+)L([-\d.]+) ([-\d.]+)", d):
                poly = _retangulo_traco((float(x0), float(y0)), (float(x1), float(y1)), esp)
                if poly is None:
                    continue
                if sum(poly[k][0] * poly[k - 3][1] - poly[k - 3][0] * poly[k][1] for k in range(4)) > 0:
                    poly = poly[::-1]             # todos no mesmo sentido: a regra nonzero faz a união
                por_op.setdefault(float(op or 1), []).append("M" + "L".join(f"{_n(x)} {_n(y)}" for x, y in poly) + "Z")
        tintas.append(r["tinta"])
        w, h = r["w"], r["h"]
    regiao = _regiao(base.get("recorte"), _medida(base, "largura", 600), _medida(base, "altura", 400))
    defs, clip = _recorte_svg(uid, regiao) if inclinada else ("", "")
    caminhos = "".join(f'<path d="{"".join(ds)}"' + (f' fill-opacity="{_n(op)}"' if op < 1 else "") + "/>"
                       for op, ds in sorted(por_op.items(), reverse=True))
    corpo = defs + f'<g fill="{_cor_pagina(base.get("cor"), ctx)}" fill-rule="nonzero"{clip}>{caminhos}</g>'
    return dict(svg=_svg(w, h, corpo, "hachura", uid), w=w, h=h, texto="", fontes=[], tinta=_uniao(tintas))


def _malha(p, ctx, uid):
    """Malha: linhas nos dois sentidos, uma mais grossa a cada `maior_cada` células (papel milimetrado, prancheta, gramado
    riscado). Fecha a caixa: o passo vira o mais perto do pedido que cabe inteiro, e as linhas da borda são grossas (a tinta
    é a caixa). Com `perspectiva`, a malha é projetada por homografia, calculada aqui em Python, nos 4 cantos pedidos: cada
    linha continua reta, o vetor continua vetor, sem transform 3D do CSS (que o PDF rasterizaria). Cada traço sai como o
    retângulo dele (preenchido), e os de um mesmo degrau vão num path só: o cruzamento não soma opacidade.
    params: largura 600; altura 400; passo 24; maior_cada 4 (0 = só a borda); espessura 0,75; espessura_maior 1,5;
    perspectiva [[u, v] x 4] (sup-esq, sup-dir, inf-dir, inf-esq, em fração da caixa; [[0.3, 0], [0.7, 0], [1, 1], [0, 1]] é
    um piso que foge para o fundo); esmaecer (como em `linhas`); recorte; cor 'marca'."""
    W, H = _medida(p, "largura", 600), _medida(p, "altura", 400)
    passo = _medida(p, "passo", 24)
    e0, em = _medida(p, "espessura", 0.75), _medida(p, "espessura_maior", 1.5)
    if e0 > em:
        raise ValueError(f"espessura {e0:g} maior que a espessura_maior {em:g}")
    cada = int(_medida(p, "maior_cada", 4, 0, estrito=False))
    if em >= passo:
        raise ValueError(f"espessura_maior {em:g} não cabe no passo {passo:g}: as linhas se fundiriam")
    nx, ny = max(1, int(round((W - em) / passo))), max(1, int(round((H - em) / passo)))
    if nx + ny > 4000:
        raise ValueError(f"malha com {nx + ny + 2} linhas: aumente o passo")
    sx, sy = (W - em) / nx, (H - em) / ny
    if min(sx, sy) <= em:
        raise ValueError(f"o passo que fecha a caixa ({min(sx, sy):.2f}) não deixa vão entre linhas de {em:g} px")
    xs = [em / 2 + i * sx for i in range(nx + 1)]
    ys = [em / 2 + j * sy for j in range(ny + 1)]

    def grossa(i, n):
        return i in (0, n) or bool(cada and i % cada == 0)

    plano = p.get("perspectiva") is not None
    if plano:
        _, M = _quadrilatero(p, W, H, inset=em / 2)
        segs = []
        for a, b, m in ([((x, ys[0]), (x, ys[-1]), grossa(i, nx)) for i, x in enumerate(xs)]
                        + [((xs[0], y), (xs[-1], y), grossa(j, ny)) for j, y in enumerate(ys)]):
            q = _projetar(M, [a, b])
            segs.append(((float(q[0, 0]), float(q[0, 1])), (float(q[1, 0]), float(q[1, 1])), m))
    else:
        segs = [((x, 0.0), (x, H), grossa(i, nx)) for i, x in enumerate(xs)]
        segs += [((0.0, y), (W, y), grossa(j, ny)) for j, y in enumerate(ys)]
    regiao = _regiao(p.get("recorte"), W, H)
    degraus = _Degraus(p["esmaecer"], regiao) if p.get("esmaecer") else None
    cor = _cor_pagina(p.get("cor"), ctx)
    grupos, visiveis, todas = {}, [], []
    for a, b, m in segs:
        e = em if m else e0
        for pa, pb, j in (degraus.partir(a, b) if degraus else [(a, b, 0)]):
            poly = _retangulo_traco(pa, pb, e)
            vis = _clip_caixa(poly, regiao) if poly else []
            if not vis:
                continue
            if sum(poly[k][0] * poly[k - 3][1] - poly[k - 3][0] * poly[k][1] for k in range(4)) > 0:
                poly = poly[::-1]                 # todos no mesmo sentido: a regra nonzero faz a união (sem furo no cruzamento)
            grupos.setdefault(j, []).append(poly)
            todas.append(_caixa_pts(vis))
            if degraus is None or degraus.ops[j] >= 0.5:
                visiveis.append(todas[-1])
    if not todas:
        raise ValueError(f"o recorte {p.get('recorte')} não pega nenhuma linha da malha")
    defs, clip = _recorte_svg(uid, regiao) if (plano or p.get("recorte") is not None) else ("", "")
    caminhos = []
    for j in sorted(grupos):
        dd = "".join("M" + "L".join(f"{_n(x)} {_n(y)}" for x, y in poly) + "Z" for poly in grupos[j])
        op = degraus.ops[j] if degraus else 1
        caminhos.append(f'<path data-degrau="{j}" d="{dd}"' + (f' fill-opacity="{_n(op)}"' if op < 1 else "") + "/>")
    corpo = defs + f'<g fill="{cor}" fill-rule="nonzero"{clip}>{"".join(caminhos)}</g>'
    return dict(svg=_svg(_inteiro(W), _inteiro(H), corpo, "malha", uid), w=_inteiro(W), h=_inteiro(H), texto="", fontes=[],
                tinta=_uniao(visiveis or todas))


# ---------------------------------------------------------------- anéis, pontos radiais
def _no_setor(x, y, cx, cy, r0, r1, a0, a1):
    d = math.hypot(x - cx, y - cy)
    if d < r0 - 1e-9 or d > r1 + 1e-9:
        return False
    if a1 - a0 >= 360 - 1e-9:
        return True
    a = math.degrees(math.atan2(y - cy, x - cx))
    return (a - a0) % 360 <= (a1 - a0) + 1e-9


def _tinta_setor(cx, cy, r0, r1, a0, a1, caixa):
    """Caixa exata da parte de um setor anular (o traço de um arco: raios r0 a r1, ângulos a0 a a1) que cai dentro da
    caixa. Os extremos de uma região limitada por arcos, raios e lados de caixa estão entre: pontos dos arcos dentro da
    caixa (amostrados a cada 0,5 px), cruzamentos dos lados da caixa com os arcos e com os raios das pontas, e os cantos
    da caixa que caem dentro do setor. None quando não há interseção."""
    X0, Y0, X1, Y1 = caixa
    cand = []
    inteiro = a1 - a0 >= 360 - 1e-9
    for r in (r0, r1):
        n = int(min(40000, max(16, math.radians(a1 - a0) * r / 0.5))) + 1
        ang = np.radians(np.linspace(a0, a1, n))
        pts = np.column_stack([cx + r * np.cos(ang), cy + r * np.sin(ang)])
        ok = (pts[:, 0] >= X0 - 1e-9) & (pts[:, 0] <= X1 + 1e-9) & (pts[:, 1] >= Y0 - 1e-9) & (pts[:, 1] <= Y1 + 1e-9)
        cand += [tuple(q) for q in pts[ok]]
        for X in (X0, X1):                      # lado vertical x = X cruzando o círculo de raio r
            dx = X - cx
            if abs(dx) <= r:
                for s in (1, -1):
                    y = cy + s * math.sqrt(r * r - dx * dx)
                    if Y0 - 1e-9 <= y <= Y1 + 1e-9 and _no_setor(X, y, cx, cy, r0, r1, a0, a1):
                        cand.append((X, y))
        for Y in (Y0, Y1):
            dy = Y - cy
            if abs(dy) <= r:
                for s in (1, -1):
                    x = cx + s * math.sqrt(r * r - dy * dy)
                    if X0 - 1e-9 <= x <= X1 + 1e-9 and _no_setor(x, Y, cx, cy, r0, r1, a0, a1):
                        cand.append((x, Y))
    if not inteiro:                              # os raios das pontas cruzando os lados da caixa
        for a in (a0, a1):
            ux, uy = math.cos(math.radians(a)), math.sin(math.radians(a))
            for X in (X0, X1):
                if abs(ux) > 1e-12:
                    t = (X - cx) / ux
                    if r0 <= t <= r1 and Y0 - 1e-9 <= cy + t * uy <= Y1 + 1e-9:
                        cand.append((X, cy + t * uy))
            for Y in (Y0, Y1):
                if abs(uy) > 1e-12:
                    t = (Y - cy) / uy
                    if r0 <= t <= r1 and X0 - 1e-9 <= cx + t * ux <= X1 + 1e-9:
                        cand.append((cx + t * ux, Y))
    cand += [(x, y) for x in (X0, X1) for y in (Y0, Y1) if _no_setor(x, y, cx, cy, r0, r1, a0, a1)]
    if not cand:
        return None
    c = _caixa_pts(cand)
    return [max(X0, c[0]), max(Y0, c[1]), min(X1, c[2]), min(Y1, c[3])]


def _aneis(p, ctx, uid):
    """Anéis concêntricos que irradiam de um ponto da área (onda de som, alvo, impacto, raio de alcance), recortados rente à
    caixa. Diferente de `circulos`, em que a caixa é o quadrado do maior círculo: aqui a caixa é a área e o centro é um
    ponto dela (no meio, num canto, ou fora). Raios em progressão igual até `raio_max`; esmaecer em degraus, anel a anel.
    params: largura 600; altura 400; quantidade 6; raio_max (padrão: a distância do centro ao canto mais longe, e os anéis
    cobrem a área); espessura 1,5; centro [0.5, 0.5] (fração da caixa); angulo_ini 0; angulo_fim 360 (graus, sentido horário,
    0 = para a direita); esmaecer 'centro' | 'borda' | {de: 'centro' (opaco no centro, some para fora) ou 'borda' (o
    contrário), passos (padrão = quantidade, de 2 a 12), minimo 0,12}; cor 'marca'. Anel que não toca a caixa não sai."""
    W, H = _medida(p, "largura", 600), _medida(p, "altura", 400)
    n = int(_medida(p, "quantidade", 6))
    if n > 400:
        raise ValueError(f"quantidade {n}: use até 400 anéis")
    u, v = _uv(p, "centro", [0.5, 0.5])
    cx, cy = u * W, v * H
    longe = max(math.hypot(cx - x, cy - y) for x in (0.0, W) for y in (0.0, H))
    rmax = _medida(p, "raio_max", round(longe, 3))
    esp = _medida(p, "espessura", 1.5)
    a0, a1 = float(p.get("angulo_ini", 0)), float(p.get("angulo_fim", 360))
    if not 0 < a1 - a0 <= 360:
        raise ValueError(f"angulo_ini {a0:g} e angulo_fim {a1:g}: o trecho precisa ter de 0 (exclusive) a 360 graus")
    raios = [rmax * (i + 1) / n for i in range(n)]
    if raios[0] <= esp / 2 or rmax / n <= esp:
        raise ValueError(f"anéis de {rmax / n:.1f} px de passo não cabem na espessura {esp:g}: menos anéis ou raio maior")
    degraus = None
    esm = p.get("esmaecer")
    if esm and n > 1:
        esm = {"de": esm} if isinstance(esm, str) else dict(esm)
        de = esm.get("de", "centro")
        if de not in ("centro", "borda"):
            raise ValueError(f"esmaecer.de `{de}`: use centro ou borda")
        degraus = _Degraus({"direcao": "dir" if de == "centro" else "esq", "passos": esm.get("passos", max(2, min(12, n))),
                            "minimo": esm.get("minimo", 0.12)}, [raios[0], 0.0, raios[-1], 0.0])
    cor = _cor_pagina(p.get("cor"), ctx)
    caixa = [0.0, 0.0, W, H]
    inteiro = a1 - a0 >= 360 - 1e-9
    por_degrau, visiveis, todas = {}, [], []
    for r in raios:
        t = _tinta_setor(cx, cy, r - esp / 2, r + esp / 2, a0, a1, caixa)
        if t is None or t[2] - t[0] <= 0 or t[3] - t[1] <= 0:
            continue
        j = degraus.indice(degraus.u((r, 0.0))) if degraus else 0
        if inteiro:
            forma = f'<circle cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(r)}"/>'
        else:
            ini = (cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0)))
            fim = (cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)))
            forma = f'<path d="M{_n(ini[0])} {_n(ini[1])}A{_n(r)} {_n(r)} 0 {1 if a1 - a0 > 180 else 0} 1 {_n(fim[0])} {_n(fim[1])}"/>'
        por_degrau.setdefault(j, []).append(forma)
        todas.append(t)
        if degraus is None or degraus.ops[j] >= 0.5:
            visiveis.append(t)
    if not todas:
        raise ValueError(f"nenhum anel toca a caixa: centro {[u, v]} longe demais para o raio_max {rmax:g}")
    grupos = "".join(f'<g data-degrau="{j}"' + (f' stroke-opacity="{_n(degraus.ops[j])}"' if degraus and degraus.ops[j] < 1 else "")
                     + f'>{"".join(por_degrau[j])}</g>' for j in sorted(por_degrau))
    defs, clip = _recorte_svg(uid, caixa)
    corpo = defs + f'<g fill="none" stroke="{cor}" stroke-width="{_n(esp)}"{clip}>{grupos}</g>'
    return dict(svg=_svg(_inteiro(W), _inteiro(H), corpo, "aneis", uid), w=_inteiro(W), h=_inteiro(H), texto="", fontes=[],
                tinta=_uniao(visiveis or todas))


def _pontos_radiais(p, ctx, uid):
    """Retícula radial: grade de pontos cujo raio cai do centro para fora (explosão, holofote, meio-tom de luz), de
    `raio_max` no centro a `raio_min` no `alcance`; além dele, nada. A grade fecha a caixa como a `grade-pontos` (o passo
    vira o mais perto do pedido que cabe inteiro, a uma margem de raio_max da borda). A tinta é a caixa dos pontos
    desenhados (todos têm opacidade 1, até o menor).
    params: largura 600; altura 400; passo 18; raio_max 6; raio_min 0,6; centro [0.5, 0.5] (fração da caixa); alcance (px;
    padrão: a distância do centro ao canto mais longe, e a retícula cobre a área); forma 'circulo' | 'quadrado'; cor 'marca'."""
    W, H = _medida(p, "largura", 600), _medida(p, "altura", 400)
    passo = _medida(p, "passo", 18)
    rmax, rmin = _medida(p, "raio_max", 6), _medida(p, "raio_min", 0.6)
    if rmin > rmax:
        raise ValueError(f"raio_min {rmin:g} maior que o raio_max {rmax:g}")
    if 2 * rmax >= passo:
        raise ValueError(f"raio_max {rmax:g} não cabe no passo {passo:g}: os pontos se encostariam")
    forma = _escolha(p, "forma", "circulo", ("circulo", "quadrado"))
    if W < 2 * rmax or H < 2 * rmax:
        raise ValueError(f"caixa de {W:g} x {H:g} menor que um ponto de {2 * rmax:g} px")
    u, v = _uv(p, "centro", [0.5, 0.5])
    cx, cy = u * W, v * H
    alcance = _medida(p, "alcance", round(max(math.hypot(cx - x, cy - y) for x in (0.0, W) for y in (0.0, H)), 3))
    nx, ny = int(round((W - 2 * rmax) / passo)) + 1, int(round((H - 2 * rmax) / passo)) + 1
    if nx * ny > 40000:
        raise ValueError(f"retícula com {nx * ny} pontos na grade: aumente o passo")
    px = (W - 2 * rmax) / (nx - 1) if nx > 1 else 0.0
    py = (H - 2 * rmax) / (ny - 1) if ny > 1 else 0.0
    ox, oy = (rmax if nx > 1 else W / 2), (rmax if ny > 1 else H / 2)
    pontos = []
    for j in range(ny):
        for i in range(nx):
            x, y = ox + i * px, oy + j * py
            d = math.hypot(x - cx, y - cy)
            if d > alcance + 1e-9:
                continue
            r = _r(rmax + (rmin - rmax) * d / alcance)
            if r > 0:
                pontos.append((x, y, r))
    if not pontos:
        raise ValueError(f"nenhum ponto dentro do alcance {alcance:g} px")
    if len(pontos) > 20000:
        raise ValueError(f"retícula com {len(pontos)} pontos: aumente o passo ou diminua o alcance")
    cor = _cor_pagina(p.get("cor"), ctx)
    if forma == "circulo":
        desenho = "".join(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(r)}"/>' for x, y, r in pontos)
    else:
        desenho = "".join(f'<rect x="{_n(x - r)}" y="{_n(y - r)}" width="{_n(2 * r)}" height="{_n(2 * r)}"/>' for x, y, r in pontos)
    tinta = _uniao([[x - r, y - r, x + r, y + r] for x, y, r in pontos])
    return dict(svg=_svg(_inteiro(W), _inteiro(H), f'<g fill="{cor}">{desenho}</g>', "pontos-radiais", uid), w=_inteiro(W),
                h=_inteiro(H), texto="", fontes=[], tinta=tinta)


# ---------------------------------------------------------------- cantoneira, moldura dupla (presas a uma caixa da página)
ESTILOS_CANTONEIRA = ("dupla", "escada", "ponto", "seta")


def _caixa_da_pagina(p, proporcao, padrao):
    """[x, y, largura, altura]: `caixa` (px da página) ou a medida da tinta (`largura` e/ou `altura`; com uma só, a outra
    segue `proporcao`) ou o padrão."""
    caixa = p.get("caixa")
    if caixa is None:
        ped = _medidas_pedidas(p)
        if ped:
            prop = _medida(p, "proporcao", proporcao)
            w = ped["largura"] if "largura" in ped else ped["altura"] * prop
            caixa = [0.0, 0.0, w, ped["altura"] if "altura" in ped else w / prop]
        else:
            caixa = [0.0, 0.0, *padrao]
    if not (isinstance(caixa, (list, tuple)) and len(caixa) == 4):
        raise ValueError("`caixa`: use [x, y, largura, altura] em px da página (ou `largura` e/ou `altura`)")
    x, y, w, h = (float(v) for v in caixa)
    if w <= 0 or h <= 0:
        raise ValueError(f"`caixa` {list(caixa)}: largura e altura precisam ser maiores que zero")
    return x, y, w, h


def _cantoneira(p, ctx, uid):
    """Cantoneira: ornamento de canto em volta de uma caixa (a foto, o número, a página), mais rico que o `colchetes`:
    'dupla' (dois L paralelos), 'escada' (o canto em degraus, art déco), 'ponto' (L com um ponto aninhado no canto) ou
    'seta' (L com um triângulo que aponta o canto). A tinta externa encosta na caixa, como no colchetes, e cada canto sai
    num <g data-canto>. Contrato de grafismo preso a geometria: devolve `origem` ([x, y] da página do canto do svg).
    params: caixa [x, y, largura, altura] (ou `largura` e/ou `altura`, a medida da tinta, com `proporcao` 4/3; padrão
    400 x 300); braco 64; espessura 2; estilo 'dupla' | 'escada' | 'ponto' | 'seta'; vao 6 (entre os traços; px ou e1..e8);
    cantos (padrão os quatro: sup-esq, sup-dir, inf-esq, inf-dir); cor 'marca'."""
    x, y, w, h = _caixa_da_pagina(p, 4 / 3, (400.0, 300.0))
    esp = _medida(p, "espessura", 2.0)
    braco = _medida(p, "braco", 64.0)
    vao = _espaco(p, "vao", 6)
    estilo = _escolha(p, "estilo", "dupla", ESTILOS_CANTONEIRA)
    cantos = list(p.get("cantos") or CANTOS)
    for c in cantos:
        if c not in CANTOS:
            raise ValueError(f"canto `{c}`: use {', '.join(CANTOS)}")
    if 2 * braco > min(w, h) + 1e-9:
        raise ValueError(f"braco {braco:g} grande demais para a caixa de {w:g} x {h:g}: os braços se encontrariam")
    o, g = esp / 2, esp + vao
    linhas = [[(o, braco), (o, o), (braco, o)]]
    cheios = []
    if estilo == "dupla":
        if braco - g <= o + g + esp:
            raise ValueError(f"braco {braco:g} curto demais para o L de dentro (vão {vao:g}, espessura {esp:g})")
        linhas.append([(o + g, braco - g), (o + g, o + g), (braco - g, o + g)])
    elif estilo == "escada":
        if braco <= o + 2 * g + esp:
            raise ValueError(f"braco {braco:g} curto demais para os dois degraus (vão {vao:g}, espessura {esp:g})")
        linhas = [[(o, braco), (o, o + 2 * g), (o + g, o + 2 * g), (o + g, o + g), (o + 2 * g, o + g), (o + 2 * g, o), (braco, o)]]
    elif estilo == "ponto":
        r = max(1.5 * esp, 3.0)
        c = esp + vao + r
        if c + r > braco:
            raise ValueError(f"braco {braco:g} curto demais para o ponto")
        cheios.append(("ponto", (c, c, r)))
    else:
        c, t = esp + vao, max(braco * 0.32, 3 * esp)
        if c + t > braco:
            raise ValueError(f"braco {braco:g} curto demais para a seta")
        cheios.append(("tri", [(c, c), (c + t, c), (c, c + t)]))
    cor = _cor_pagina(p.get("cor"), ctx)
    espelho = {"sup-esq": lambda a, b: (x + a, y + b), "sup-dir": lambda a, b: (x + w - a, y + b),
               "inf-esq": lambda a, b: (x + a, y + h - b), "inf-dir": lambda a, b: (x + w - a, y + h - b)}
    grupos, caixas = [], []
    for nome in dict.fromkeys(cantos):
        m = espelho[nome]
        dd, extra = "", ""
        for pts in linhas:
            q = [m(a, b) for a, b in pts]
            dd += "M" + "L".join(f"{_n(a)} {_n(b)}" for a, b in q)
            caixas.append(_tinta_polilinha(q, esp))
        for tipo, geo in cheios:
            if tipo == "ponto":
                (px_, py_), r = m(geo[0], geo[1]), geo[2]
                extra += f'<circle cx="{_n(px_)}" cy="{_n(py_)}" r="{_n(r)}" fill="{cor}"/>'
                caixas.append([px_ - r, py_ - r, px_ + r, py_ + r])
            else:
                q = [m(a, b) for a, b in geo]
                extra += f'<polygon points="{" ".join(f"{_n(a)},{_n(b)}" for a, b in q)}" fill="{cor}"/>'
                caixas.append(_caixa_pts(q))
        grupos.append(f'<g data-canto="{nome}"><path d="{dd}" fill="none" stroke="{cor}" stroke-width="{_n(esp)}" '
                      f'stroke-linejoin="miter" stroke-linecap="butt"/>{extra}</g>')
    r, (dx, dy) = _fechar("cantoneira", uid, "".join(grupos), _uniao(caixas))
    return dict(r, texto="", fontes=[], origem=[-dx, -dy])


def _retangulo_chanfrado(x0, y0, x1, y1, c):
    return (f"M{_n(x0 + c)} {_n(y0)}L{_n(x1 - c)} {_n(y0)}L{_n(x1)} {_n(y0 + c)}L{_n(x1)} {_n(y1 - c)}L{_n(x1 - c)} {_n(y1)}"
            f"L{_n(x0 + c)} {_n(y1)}L{_n(x0)} {_n(y1 - c)}L{_n(x0)} {_n(y0 + c)}Z")


def _moldura_dupla(p, ctx, uid):
    """Moldura dupla: dois quadros concêntricos (o de fora mais grosso), filete de certificado, de rótulo, de troféu.
    O traço de fora encosta na caixa (a tinta é a caixa) e o de dentro corre paralelo a `vao` px dele. Cantos 'reto',
    'chanfro' (corte a 45 graus; o de dentro é recalculado para ficar paralelo: perna - d x (2 - raiz de 2)) ou
    'arredondado' (o raio de dentro desconta a distância entre os dois). Preso a geometria: devolve `origem`.
    params: caixa [x, y, largura, altura] (ou `largura` e/ou `altura`, a medida da tinta, com `proporcao` 3/2; padrão
    600 x 400); espessuras [2, 1] (fora, dentro); vao 8 (px ou e1..e8); cantos 'reto' | 'chanfro' | 'arredondado'; chanfro 16
    (a perna do corte, ou o raio); cor 'marca'."""
    x, y, w, h = _caixa_da_pagina(p, 3 / 2, (600.0, 400.0))
    esps = p.get("espessuras", [2, 1])
    try:
        e1, e2 = (float(v) for v in esps)
    except (TypeError, ValueError):
        raise ValueError("`espessuras`: use [fora, dentro] em px") from None
    if e1 <= 0 or e2 <= 0:
        raise ValueError(f"`espessuras` {esps}: as duas precisam ser maiores que zero")
    vao = _espaco(p, "vao", 8)
    cantos = _escolha(p, "cantos", "reto", ("reto", "chanfro", "arredondado"))
    c = _medida(p, "chanfro", 16) if cantos != "reto" else 0.0
    o1, o2 = e1 / 2, e1 + vao + e2 / 2
    d = o2 - o1
    fora = (x + o1, y + o1, x + w - o1, y + h - o1)
    dentro = (x + o2, y + o2, x + w - o2, y + h - o2)
    if dentro[2] - dentro[0] <= e2 or dentro[3] - dentro[1] <= e2:
        raise ValueError(f"caixa de {w:g} x {h:g} pequena demais para o vão {vao:g} e as espessuras {esps}")
    cor = _cor_pagina(p.get("cor"), ctx)
    quadros = []
    for nome, (a0, b0, a1, b1), e, k in (("fora", fora, e1, c), ("dentro", dentro, e2, None)):
        if cantos == "reto":
            quadros.append(f'<rect data-quadro="{nome}" x="{_n(a0)}" y="{_n(b0)}" width="{_n(a1 - a0)}" height="{_n(b1 - b0)}" '
                           f'stroke-width="{_n(e)}"/>')
            continue
        if k is None:
            k = c - d * (2 - math.sqrt(2)) if cantos == "chanfro" else max(0.0, c - d)
        if cantos == "chanfro" and k <= 0:
            raise ValueError(f"chanfro {c:g} pequeno demais para o vão: o quadro de dentro perderia o corte (use pelo menos "
                             f"{d * (2 - math.sqrt(2)) + 1:.1f})")
        if 2 * k >= min(a1 - a0, b1 - b0) - e:
            raise ValueError(f"chanfro {c:g} grande demais para a caixa de {w:g} x {h:g}")
        if cantos == "chanfro":
            quadros.append(f'<path data-quadro="{nome}" d="{_retangulo_chanfrado(a0, b0, a1, b1, k)}" stroke-width="{_n(e)}"/>')
        else:
            quadros.append(f'<rect data-quadro="{nome}" x="{_n(a0)}" y="{_n(b0)}" width="{_n(a1 - a0)}" height="{_n(b1 - b0)}" '
                           f'rx="{_n(k)}" stroke-width="{_n(e)}"/>')
    corpo = f'<g fill="none" stroke="{cor}" stroke-linejoin="miter">{"".join(quadros)}</g>'
    r, (dx, dy) = _fechar("moldura-dupla", uid, corpo, [x, y, x + w, y + h])
    return dict(r, texto="", fontes=[], origem=[-dx, -dy])


# ---------------------------------------------------------------- régua de borda (também constante: o tempo de jogo)
def _regua_borda(p, ctx, uid):
    """Régua de borda: uma escala de `de` a `ate` (padrão o tempo de jogo, 0' a 90') de ponta a ponta da página, marca
    menor a cada `menor_cada` e maior, com rótulo vivo, a cada `maior_cada`. É a `regua` com as marcas postas pela escala
    (não pelo passo em px) e o rótulo com sufixo: herda o rótulo que nunca passa das pontas, os numerais tabulares e a
    medida (a `largura` é o comprimento da tinta; a `altura` escala o estilo). Vale também como constante do sistema
    (sistema_elementos.constantes): o `texto` que a constante recebe é ignorado, a régua não tem texto corrido.
    params: comprimento 1920 (ou `largura`); de 0; ate 90; menor_cada 5; maior_cada 15; sufixo "'" (minuto); rotulos True;
    marca 10; marca_maior (padrão o dobro); espessura 1,5; lado 'baixo' (marcas e rótulos para baixo: a régua da borda de
    cima) | 'cima'; linha True; tamanho 16; fonte 'corpo'; peso 600; espacamento 0,06 em; folga 6; cor 'marca'."""
    de, ate = float(p.get("de", 0)), float(p.get("ate", 90))
    menor, maior = _medida(p, "menor_cada", 5), _medida(p, "maior_cada", 15)
    if ate <= de:
        raise ValueError(f"`ate` {ate:g} precisa ser maior que `de` {de:g}")
    n = (ate - de) / menor
    if abs(n - round(n)) > 1e-9 or round(n) < 1:
        raise ValueError(f"de {de:g} a {ate:g} não é múltiplo de menor_cada {menor:g}")
    k = maior / menor
    if abs(k - round(k)) > 1e-9:
        raise ValueError(f"maior_cada {maior:g} precisa ser múltiplo de menor_cada {menor:g}")
    n, k = int(round(n)), int(round(k))
    if n > 2000:
        raise ValueError(f"régua com {n + 1} marcas: aumente menor_cada")
    esp = _medida(p, "espessura", 1.5)
    L = _medida(p, "largura", None) if p.get("largura") is not None else _medida(p, "comprimento", 1920)
    if L <= esp:
        raise ValueError(f"comprimento {L:g} não passa da espessura {esp:g}")
    sufixo = str(p.get("sufixo", "'"))
    rotulos = [f"{_numero_br(de + i * menor)}{sufixo}" for i in range(0, n + 1, k)] if p.get("rotulos", True) else None
    q = {c: v for c, v in p.items() if c not in ("de", "ate", "menor_cada", "maior_cada", "sufixo", "texto", "texto_de",
                                                  "comprimento", "rotulos", "orientacao", "passo", "marca_maior_a_cada")}
    q.update(largura=L, passo=(L - esp) / n, marca_maior_a_cada=k, orientacao="horizontal", rotulos=rotulos)
    r = _regua(q, ctx, uid)
    r["svg"] = re.sub(r'data-grafismo="[^"]+"', 'data-grafismo="regua-borda"', r["svg"], count=1)
    return r


# ---------------------------------------------------------------- tipografia expressiva: eco, texto em curva
def _pontos_glifo(f, g):
    """Pontos do contorno do glifo `g` (unidades da fonte, y para cima), com cada curva achatada em 12 pontos: a caixa de
    um glifo girado sai deles. Guardados na própria Fonte."""
    cache = f.__dict__.setdefault("_pontos_glifo", {})
    if g not in cache:
        from fontTools.pens.basePen import BasePen
        pts = []

        class Achatar(BasePen):
            def _moveTo(self, pt):
                pts.append(pt)

            def _lineTo(self, pt):
                pts.append(pt)

            def _curveToOne(self, p1, p2, p3):
                p0 = np.asarray(self._getCurrentPoint(), float)
                for t in np.linspace(1 / 12, 1, 12):
                    a = 1 - t
                    pts.append(tuple(a ** 3 * p0 + 3 * a * a * t * np.asarray(p1) + 3 * a * t * t * np.asarray(p2) + t ** 3 * np.asarray(p3)))

            def _qCurveToOne(self, p1, p2):
                p0 = np.asarray(self._getCurrentPoint(), float)
                for t in np.linspace(1 / 12, 1, 12):
                    a = 1 - t
                    pts.append(tuple(a * a * p0 + 2 * a * t * np.asarray(p1) + t * t * np.asarray(p2)))

        f._glyphset()[g].draw(Achatar(f._glyphset()))
        cache[g] = np.asarray(pts, float).reshape(-1, 2)
    return cache[g]


def _contornos_glifo(f, g):
    """Os contornos do glifo `g` em separado (unidades da fonte, y para cima), cada curva achatada em 12 pontos."""
    cache = f.__dict__.setdefault("_contornos_glifo", {})
    if g not in cache:
        from fontTools.pens.basePen import BasePen
        contornos = []

        class Separar(BasePen):
            def _moveTo(self, pt):
                contornos.append([pt])

            def _lineTo(self, pt):
                contornos[-1].append(pt)

            def _curveToOne(self, p1, p2, p3):
                p0 = np.asarray(self._getCurrentPoint(), float)
                for t in np.linspace(1 / 12, 1, 12):
                    a = 1 - t
                    contornos[-1].append(tuple(a ** 3 * p0 + 3 * a * a * t * np.asarray(p1) + 3 * a * t * t * np.asarray(p2) + t ** 3 * np.asarray(p3)))

            def _qCurveToOne(self, p1, p2):
                p0 = np.asarray(self._getCurrentPoint(), float)
                for t in np.linspace(1 / 12, 1, 12):
                    a = 1 - t
                    contornos[-1].append(tuple(a * a * p0 + 2 * a * t * np.asarray(p1) + t * t * np.asarray(p2)))

        f._glyphset()[g].draw(Separar(f._glyphset()))
        cache[g] = [np.asarray(c, float) for c in contornos if len(c) >= 3]
    return cache[g]


def _silhueta_glifo(f, g, s, fino=4):
    """A silhueta do glifo no corpo `s`, como subpaths (lista de arrays de pontos em px, origem na linha de base, y para
    baixo): os contornos UNIDOS pela regra nonzero da fonte. Instância estática de fonte variável costuma ter contornos
    sobrepostos (a haste por cima da barriga do B); traçar cada contorno mostraria as emendas por dentro da letra. O glifo
    é rasterizado a `fino` x pela regra nonzero (soma dos contornos, cada um com o seu sentido), suavizado e retraçado
    pelo find_contours: a silhueta sai a 1/`fino` de px, sem emenda."""
    from PIL import ImageDraw
    from scipy.ndimage import gaussian_filter
    from skimage import measure
    cache = f.__dict__.setdefault("_silhueta", {})
    chave = (g, round(s, 3), fino)
    if chave in cache:
        return cache[chave]
    k = s / f.upem
    cs = [np.column_stack([c[:, 0] * k, -c[:, 1] * k]) for c in _contornos_glifo(f, g)]
    if not cs:
        cache[chave] = []
        return []
    tudo = np.vstack(cs)
    x0, y0 = tudo.min(0) - 3
    w, h = (tudo.max(0) + 3 - (x0, y0)) * fino
    soma = np.zeros((int(math.ceil(h)), int(math.ceil(w))), float)
    for c in cs:
        area = 0.5 * float(np.sum(c[:, 0] * np.roll(c[:, 1], -1) - np.roll(c[:, 0], -1) * c[:, 1]))
        if abs(area) < 1e-9:
            continue
        im = Image.new("L", (soma.shape[1], soma.shape[0]), 0)
        ImageDraw.Draw(im).polygon([((x - x0) * fino, (y - y0) * fino) for x, y in c], fill=1)
        soma += math.copysign(1.0, area) * np.asarray(im, float)
    cheio = gaussian_filter((np.abs(soma) > 0.5).astype(float), 0.8)
    partes = []
    for q in measure.find_contours(cheio, 0.5):
        q = measure.approximate_polygon(q, tolerance=0.35)
        if len(q) < 4:
            continue
        partes.append(np.column_stack([q[:, 1] / fino + x0, q[:, 0] / fino + y0]))
    cache[chave] = partes
    return partes


def _path_do_texto(f, texto, s, ls, x0=0.0, base=0.0):
    """O texto como contorno: <path> d com a silhueta de cada glifo da fonte do kit (mesmos glifos, avanços e kerning da
    medida; contornos sobrepostos unidos, ver _silhueta_glifo), a linha de base em `base` e o início em `x0`. É desenho
    (não entra no pdftotext): serve ao eco em contorno."""
    esc = s / f.upem
    partes, x = [], x0
    for g, a in zip(f.glifos(texto), f.avancos(texto)):
        for q in _silhueta_glifo(f, g, s):
            partes.append("M" + "L".join(f"{_n(px + x)} {_n(py + base)}" for px, py in q) + "Z")
        x += a * esc + ls
    return "".join(partes)


def _fonte_expressiva(p, ctx, padrao="display"):
    papel = p.get("fonte", padrao)
    if papel not in PAPEIS:
        raise ValueError(f"fonte `{papel}`: use {', '.join(PAPEIS)}")
    t_em = float(p.get("espacamento", 0.0))
    if t_em < -0.02 - 1e-9:
        raise ValueError(f"espacamento {t_em:g} em: tracking abaixo de -0,02 em embola as letras (tipografia expressiva, C6)")
    return fonte(ctx, papel, p.get("peso")), t_em


def _eco(p, ctx, uid):
    """Eco: o texto repetido em cópias translúcidas que se afastam em degraus (a palavra gigante atrás da figura, o título
    que reverbera). Texto vivo de `texto_de` (o gate de copy: título, evento, tese, local, data); `texto` livre também
    gera, e o QA avisa "texto fora do gate de copy" (qa_conjunto.checar_texto_livre; vale também para numeral-eco e
    texto-curva). Cada cópia anda `deslocamento` (degrau de espaço) na `direcao`, com a opacidade do seu degrau.
    'fantasma' = <text> preenchido (texto vivo no PDF); 'contorno-path' = o contorno dos glifos como <path> com traço, tirado
    da fonte do kit pelo fontTools (nunca <text> com stroke, que vira Type 3): é desenho, não texto, e devolve texto e
    fontes vazios. A cópia 0 (a primeira opacidade) fica por cima; `linhas` é a dela. A tinta é o desenho inteiro: as
    cópias são translúcidas por natureza (acabamento), então a régua de meia opacidade não se aplica aqui.
    params: texto_de titulo | evento | tese | local | data (ou texto); estilo 'fantasma' | 'contorno-path'; copias 3 (1 a 3);
    deslocamento 'e3' (e1 a e8 ou px); direcao 'baixo' (dir, esq, baixo, cima ou graus); opacidades [0.24, 0.12, 0.06]
    (dos degraus 1, .72, .46, .24, .12, .06); fonte 'display' | 'lettering' (cai no display quando a receita não tem);
    peso; tamanho 200 (ou `largura`/`altura`, a medida da tinta; com as duas, a maior que cabe); espacamento 0 em (nunca
    abaixo de -0,02); espessura 1,5 (contorno-path); caixa_alta True; cor 'marca'."""
    texto = _texto(p, ctx, caixa_alta=p.get("caixa_alta", True))
    estilo = _escolha(p, "estilo", "fantasma", ("fantasma", "contorno-path"))
    n = int(_medida(p, "copias", 3))
    if not 1 <= n <= 3:
        raise ValueError(f"copias {n}: use de 1 a 3")
    ops = _opacidades(p, n)
    desl = _espaco(p, "deslocamento", "e3")
    ux, uy = _rumo(p, "direcao", "baixo")
    f, t_em = _fonte_expressiva(p, ctx)
    contorno = estilo == "contorno-path"
    esp = _medida(p, "espessura", 1.5) if contorno else 0.0
    x0, y0, x1, y1 = f.caixa_tinta(texto, 1.0, t_em)
    if x1 - x0 <= 0 or y1 - y0 <= 0:
        raise ValueError(f"eco sem tinta: {texto!r}")
    dx, dy = ux * desl, uy * desl
    ped = _medidas_pedidas(p)
    cands = []
    if "largura" in ped:
        cands.append((ped["largura"] - abs(dx) * (n - 1) - esp) / (x1 - x0))
    if "altura" in ped:
        cands.append((ped["altura"] - abs(dy) * (n - 1) - esp) / (y1 - y0))
    s = min(cands) if cands else _medida(p, "tamanho", 200)
    if s <= 1:
        raise ValueError("medida pequena demais para o deslocamento das cópias: diminua o deslocamento ou as cópias")
    s = math.floor(s * 1000) / 1000                  # para baixo: a tinta nunca passa da medida pedida
    ls = _r(t_em * s)
    cor = _cor_pagina(p.get("cor"), ctx)
    partes, caixas = [], []
    for k in reversed(range(n)):                     # a cópia 0 por último: fica por cima
        ox, oy = k * dx, k * dy
        if contorno:
            d = _path_do_texto(f, texto, s, ls, ox, oy)
            op = f' stroke-opacity="{_n(ops[k])}"' if ops[k] < 1 else ""
            partes.append(f'<path data-copia="{k}" d="{d}" fill="none" stroke="{cor}" stroke-width="{_n(esp)}" '
                          f'stroke-linejoin="round"{op}/>')
            bx0, by0, bx1, by1 = f.caixa_tinta(texto, s, ls)
            caixas.append([ox + bx0 - esp / 2, oy - by1 - esp / 2, ox + bx1 + esp / 2, oy - by0 + esp / 2])
        else:
            op = f' fill-opacity="{_n(ops[k])}"' if ops[k] < 1 else ""
            svg_t, cx = _texto_svg(f, texto, ox, oy, s, ls, cor, "start", extra=f' data-copia="{k}"{op}')
            partes.append(svg_t)
            caixas.append(cx)
    r, (ddx, ddy) = _fechar("eco", uid, "".join(partes), _uniao(caixas))
    linhas = {"linha_base": ddy + 0.0, "cap": ddy - f.cap_px(s)}
    return dict(r, texto="" if contorno else texto, fontes=[] if contorno else [f.familia], linhas=linhas)


def _caminho_curva(forma, Lp, p):
    """(d, ponto(s) -> (P, tangente), apice) do caminho do texto em curva com comprimento `Lp`, origem no ápice (o meio)."""
    if forma == "arco":
        R = float(p.get("raio", 480))
        if not math.isfinite(R) or abs(R) < 1:
            raise ValueError(f"raio {R:g}: use px (positivo = arco para cima, negativo = para baixo)")
        r = abs(R)
        th = Lp / r
        if th >= 2 * math.pi * 0.95:
            raise ValueError(f"texto de {Lp:.0f} px não cabe num arco de raio {r:g}: aumente o raio")
        if R > 0:      # centro embaixo do ápice: o arco sobe; percorre no sentido horário da tela
            cx, cy, a_ini, sg = 0.0, r, -math.pi / 2 - th / 2, 1.0
        else:          # centro em cima: a tigela; percorre no sentido anti-horário da tela
            cx, cy, a_ini, sg = 0.0, -r, math.pi / 2 + th / 2, -1.0

        def ponto(sd):
            a = a_ini + sg * sd / r
            return (np.array([cx + r * math.cos(a), cy + r * math.sin(a)]),
                    np.array([-math.sin(a) * sg, math.cos(a) * sg]))
        ini, fim = ponto(0.0)[0], ponto(Lp)[0]
        d = (f"M {_n(ini[0])} {_n(ini[1])} A {_n(r)} {_n(r)} 0 {1 if th > math.pi else 0} {1 if sg > 0 else 0} "
             f"{_n(fim[0])} {_n(fim[1])}")
        return d, ponto
    A, lam = float(p.get("amplitude", 24)), _medida(p, "comprimento_onda", 360)
    fase = math.radians(float(p.get("fase", 0)))
    if not math.isfinite(A):
        raise ValueError("amplitude: use px")
    xs = np.arange(0.0, Lp + 4.0, 2.0)
    while True:
        ys = -A * np.sin(2 * math.pi * xs / lam + fase)
        cum = np.r_[0, np.cumsum(np.hypot(np.diff(xs), np.diff(ys)))]
        if cum[-1] >= Lp:
            break
        xs = np.arange(0.0, xs[-1] + Lp - cum[-1] + 4.0, 2.0)
    i = int(np.searchsorted(cum, Lp))
    t = (Lp - cum[i - 1]) / (cum[i] - cum[i - 1])
    fim = np.array([xs[i - 1] + (xs[i] - xs[i - 1]) * t, ys[i - 1] + (ys[i] - ys[i - 1]) * t])
    pts = np.vstack([np.column_stack([xs[:i], ys[:i]]), fim[None]])
    pts = pts - np.array([pts[:, 0].max() / 2, 0.0])                      # o meio do caminho em x = 0
    cum = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    d = "M " + " L ".join(f"{_n(a)} {_n(b)}" for a, b in pts)
    return d, (lambda sd: _no_comprimento(pts, cum, sd))


def _texto_curva_em(p, ctx, uid, texto, forma, f, t_em, s):
    s = _r(s)
    ls = _r(t_em * s)
    gs = f.glifos(texto)
    adv = [a * s / f.upem for a in f.avancos(texto)]
    T = sum(adv) + len(adv) * ls
    folga = _r(0.5 * s)
    Lp = T + 2 * folga
    d, ponto = _caminho_curva(forma, Lp, p)
    k = s / f.upem
    ini = _r(folga + ls / 2)                       # o texto visível (sem o espaçamento final) centrado no meio do caminho
    cantos, pos = [], ini
    for g, a in zip(gs, adv):
        meio = pos + (a + ls) / 2                   # o textPath põe o meio do glifo (avanço com o espaçamento) no caminho
        P, t = ponto(meio)
        nrm = np.array([-t[1], t[0]])
        q = _pontos_glifo(f, g)
        if len(q):
            lx = q[:, 0] * k - (a + ls) / 2
            ly = -q[:, 1] * k
            cantos.append(P + lx[:, None] * t + ly[:, None] * nrm)
        pos += a + ls
    if not cantos:
        raise ValueError(f"texto em curva sem tinta: {texto!r}")
    tinta = _caixa_pts(np.vstack(cantos))
    P, _ = ponto(ini + (T - ls) / 2)
    cor = _cor_pagina(p.get("cor"), ctx)
    corpo = (f'<path id="tc-{uid}" d="{d}" fill="none"/><text fill="{cor}" style="{_estilo(f, s, ls)}">'
             f'<textPath href="#tc-{uid}" startOffset="{_n(ini)}">{_esc(texto)}</textPath></text>')
    return corpo, tinta, float(P[1]), f.cap_px(s), s


def _texto_curva(p, ctx, uid):
    """Texto em curva, vivo: <textPath> num arco ou numa onda, com a medida do `selo` (avanço de cada glifo, kerning e
    espaçamento pela fonte; o textPath põe o meio de cada glifo no caminho). O caminho nasce do comprimento do texto (mais
    meia altura de folga em cada ponta), então nada fica de fora; o meio do texto cai no ápice do arco. A tinta sai do
    contorno de cada glifo girado na tangente do caminho; `linhas` é a linha de base no meio do texto.
    params: texto | texto_de (titulo, evento, tese, local, data); forma 'arco' | 'onda'; raio 480 (arco; positivo sobe,
    negativo é a tigela); amplitude 24, comprimento_onda 360, fase 0 (graus) (onda); tamanho 40 (ou `largura`/`altura`, a
    medida da tinta; com as duas, a maior que cabe); espacamento 0,06 em (nunca abaixo de -0,02); fonte 'display'; peso;
    caixa_alta True; cor 'marca'."""
    texto = _texto(p, ctx, caixa_alta=p.get("caixa_alta", True))
    forma = _escolha(p, "forma", "arco", ("arco", "onda"))
    f, t_em = _fonte_expressiva(dict(p, espacamento=p.get("espacamento", 0.06)), ctx)
    ped = _medidas_pedidas(p)
    s = _medida(p, "tamanho", 40)
    if ped:
        cands = []
        for dim, alvo in ped.items():
            i = 2 if dim == "largura" else 3
            medir = lambda x: (lambda t: t[i] - t[i - 2])(_texto_curva_em(p, ctx, uid, texto, forma, f, t_em, x)[1])  # noqa: E731
            cands.append(_secante(medir, alvo, s, tol=0.2))
        s = min(cands)
        if s <= 1:
            raise ValueError("medida pequena demais para o texto em curva")
    corpo, tinta, base, cap, s = _texto_curva_em(p, ctx, uid, texto, forma, f, t_em, s)
    r, (dx, dy) = _fechar("texto-curva", uid, corpo, tinta)
    return dict(r, texto=texto, fontes=[f.familia], linhas={"linha_base": base + dy, "cap": base - cap + dy})


# ---------------------------------------------------------------- onda 2: ondas, curvas de nível, fita, carimbo, numeral em eco, meio-tom de foto
def _ondas(p, ctx, uid):
    """Ondas paralelas (mar, som, vento, raia de natação): senoides horizontais empilhadas que fecham a caixa (a crista da
    primeira encosta no topo e o vale da última na base; o espaçamento vira o mais perto do pedido que cabe). Cada onda é
    uma curva Bézier (Catmull-Rom por 16 pontos de cada comprimento de onda) cortada rente nas laterais pelo clipPath.
    params: largura 600; altura 400; comprimento 160 (de crista a crista); amplitude 12; espacamento 16 (entre as linhas de
    centro); fase 0 (graus); defasagem 0 (graus a mais a cada onda: as ondas escorregam uma sobre a outra); espessura 1,5;
    esmaecer 'cima' | 'baixo' | {direcao: cima ou baixo, passos, minimo} (onda a onda: cada traço é inteiro); cor 'marca'."""
    W, H = _medida(p, "largura", 600), _medida(p, "altura", 400)
    lam, A = _medida(p, "comprimento", 160), _medida(p, "amplitude", 12, 0, estrito=False)
    s, esp = _medida(p, "espacamento", 16), _medida(p, "espessura", 1.5)
    fase, defas = math.radians(float(p.get("fase", 0))), math.radians(float(p.get("defasagem", 0)))
    util = H - 2 * A - esp
    if util < 0:
        raise ValueError(f"altura {H:g} não comporta uma onda de amplitude {A:g} e espessura {esp:g}")
    n = int(round(util / s)) + 1 if util > 0 else 1
    if n > 600:
        raise ValueError(f"{n} ondas: aumente o espaçamento")
    passo = util / (n - 1) if n > 1 else 0.0
    inclinacao = math.atan(2 * math.pi * A / lam)
    if n > 1 and passo * math.cos(inclinacao) <= esp:
        raise ValueError(f"ondas a {passo:.1f} px com amplitude {A:g} e comprimento {lam:g} se encostam na subida: "
                         "aumente o espaçamento ou o comprimento")
    esm = p.get("esmaecer")
    degraus = None
    if esm:
        esm = {"direcao": esm} if isinstance(esm, str) else dict(esm)
        if esm.get("direcao", "baixo") not in ("cima", "baixo"):
            raise ValueError(f"esmaecer.direcao `{esm.get('direcao')}`: as ondas esmaecem só na vertical (cima ou baixo), onda a onda")
        degraus = _Degraus(esm, [0.0, 0.0, W, H])
    cor = _cor_pagina(p.get("cor"), ctx)
    dx = lam / 16
    xs = np.arange(-dx, W + 2 * dx, dx)
    por_degrau, visiveis, todas = {}, [], []
    for j in range(n):
        y0 = A + esp / 2 + j * passo
        P = np.column_stack([xs, y0 - A * np.sin(2 * math.pi * xs / lam + fase + j * defas)])
        segs = _bezier_catmull(list(P), False)
        d = f"M{_n(segs[0][0][0])} {_n(segs[0][0][1])}" + "".join(
            f"C{_n(b[0])} {_n(b[1])} {_n(c[0])} {_n(c[1])} {_n(e[0])} {_n(e[1])}" for _, b, c, e in segs)
        pts, _ = _amostrar(segs, 24)
        dentro = pts[(pts[:, 0] >= 0) & (pts[:, 0] <= W)]
        t = [0.0, max(0.0, float(dentro[:, 1].min()) - esp / 2), W, min(H, float(dentro[:, 1].max()) + esp / 2)]
        k = degraus.indice(degraus.u((W / 2, y0))) if degraus else 0
        por_degrau.setdefault(k, []).append(d)
        todas.append(t)
        if degraus is None or degraus.ops[k] >= 0.5:
            visiveis.append(t)
    defs, clip = _recorte_svg(uid, [0.0, 0.0, W, H])
    caminhos = "".join(f'<path data-degrau="{k}" d="{"".join(ds)}"'
                       + (f' stroke-opacity="{_n(degraus.ops[k])}"' if degraus and degraus.ops[k] < 1 else "") + "/>"
                       for k, ds in sorted(por_degrau.items()))
    corpo = defs + f'<g fill="none" stroke="{cor}" stroke-width="{_n(esp)}"{clip}>{caminhos}</g>'
    return dict(svg=_svg(_inteiro(W), _inteiro(H), corpo, "ondas", uid), w=_inteiro(W), h=_inteiro(H), texto="", fontes=[],
                tinta=_uniao(visiveis or todas))


GRADE_RELEVO = 256          # o campo das curvas de nível é calculado numa grade fixa: o relevo é da caixa, não do px


def _curvas_nivel(p, ctx, uid):
    """Curvas de nível (relevo, mapa topográfico, o terreno da trilha): isolinhas de um campo de colinas gaussianas sorteadas
    pela `semente` (a mesma semente, o mesmo relevo), achadas pelo skimage.measure.find_contours e suavizadas em Bézier.
    `niveis` alturas igualmente espaçadas entre o mínimo e o máximo do campo, cada uma num <path data-nivel>; a cada
    `maior_cada` nível, um traço mais grosso. O campo é calculado numa grade fixa de 256 x 256 sobre a caixa: em outra
    medida, o mesmo relevo esticado (e a tinta acompanha a caixa sem saltos).
    params: largura 600; altura 400; semente 7; niveis 9; picos 6 (colinas e vales); espessura 1; espessura_maior 2;
    maior_cada 0 (nenhum); cor 'marca'."""
    from skimage import measure
    W, H = _medida(p, "largura", 600), _medida(p, "altura", 400)
    semente = int(p.get("semente", 7))
    niveis, picos = int(_medida(p, "niveis", 9)), int(_medida(p, "picos", 6))
    if niveis > 60 or picos > 40:
        raise ValueError("curvas-nivel: use até 60 níveis e 40 picos")
    e0, e1 = _medida(p, "espessura", 1), _medida(p, "espessura_maior", 2)
    cada = int(_medida(p, "maior_cada", 0, 0, estrito=False))
    rng = np.random.default_rng(semente)
    centros = rng.uniform(-0.1, 1.1, (picos, 2))
    sigmas = rng.uniform(0.12, 0.32, picos)
    alturas = rng.uniform(0.5, 1.0, picos) * np.where(rng.uniform(0, 1, picos) < 0.75, 1.0, -1.0)
    u = np.linspace(0.0, 1.0, GRADE_RELEVO)
    U, V = np.meshgrid(u, u)
    S = math.sqrt(W * H)
    campo = np.zeros_like(U)
    for (cu, cv), sg, a in zip(centros, sigmas, alturas):
        campo += a * np.exp(-(((U - cu) * W) ** 2 + ((V - cv) * H) ** 2) / (2 * (sg * S) ** 2))
    lo, hi = float(campo.min()), float(campo.max())
    if hi - lo < 1e-9:
        raise ValueError("relevo plano: mude a semente ou os picos")
    cor = _cor_pagina(p.get("cor"), ctx)
    escala = np.array([W / (GRADE_RELEVO - 1), H / (GRADE_RELEVO - 1)])
    caminhos, pontos_todos = [], []
    for i in range(niveis):
        nivel = lo + (hi - lo) * (i + 1) / (niveis + 1)
        d, esp = "", (e1 if cada and (i + 1) % cada == 0 else e0)
        for c in measure.find_contours(campo, nivel):
            if len(c) < 4:
                continue
            fechada = bool(np.allclose(c[0], c[-1]))
            c = measure.approximate_polygon(c, tolerance=0.25)
            P = c[:, ::-1] * escala
            if fechada:
                P = P[:-1]
            if len(P) < 3:
                continue
            segs = _bezier_catmull(list(P), fechada)
            d += f"M{_n(segs[0][0][0])} {_n(segs[0][0][1])}" + "".join(
                f"C{_n(b[0])} {_n(b[1])} {_n(cc[0])} {_n(cc[1])} {_n(e[0])} {_n(e[1])}" for _, b, cc, e in segs) + ("Z" if fechada else "")
            pts, _ = _amostrar(segs, 12)
            pontos_todos.append(np.c_[pts, np.full(len(pts), esp / 2)])
        if d:
            caminhos.append(f'<path data-nivel="{i}" stroke-width="{_n(esp)}" d="{d}"/>')
    if not caminhos:
        raise ValueError("nenhuma curva de nível: mude a semente")
    q = np.vstack(pontos_todos)
    tinta = [max(0.0, float((q[:, 0] - q[:, 2]).min())), max(0.0, float((q[:, 1] - q[:, 2]).min())),
             min(W, float((q[:, 0] + q[:, 2]).max())), min(H, float((q[:, 1] + q[:, 2]).max()))]
    defs, clip = _recorte_svg(uid, [0.0, 0.0, W, H])
    corpo = defs + f'<g fill="none" stroke="{cor}" stroke-linejoin="round"{clip}>{"".join(caminhos)}</g>'
    return dict(svg=_svg(_inteiro(W), _inteiro(H), corpo, "curvas-nivel", uid), w=_inteiro(W), h=_inteiro(H), texto="",
                fontes=[], tinta=tinta)


def _cruza_reta(a, d, b, e):
    """Ponto onde a reta a + t d cruza a reta b + s e (None se paralelas)."""
    den = d[0] * e[1] - d[1] * e[0]
    if abs(den) < 1e-12:
        return None
    t = ((b[0] - a[0]) * e[1] - (b[1] - a[1]) * e[0]) / den
    return (a[0] + t * d[0], a[1] + t * d[1])


def _deslocada(P, dist):
    """Polilinha paralela a P a `dist` px (positivo = à esquerda de quem anda; y para baixo), com junta em quina."""
    out = []
    for i in range(len(P)):
        if i == 0 or i == len(P) - 1:
            a, b = (P[0], P[1]) if i == 0 else (P[-2], P[-1])
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            n = (-(b[1] - a[1]) / L, (b[0] - a[0]) / L)
            out.append((P[i][0] + n[0] * dist, P[i][1] + n[1] * dist))
            continue
        a, v, b = P[i - 1], P[i], P[i + 1]
        d1 = ((v[0] - a[0]), (v[1] - a[1])); d2 = ((b[0] - v[0]), (b[1] - v[1]))
        l1, l2 = math.hypot(*d1), math.hypot(*d2)
        n1 = (-d1[1] / l1 * dist, d1[0] / l1 * dist); n2 = (-d2[1] / l2 * dist, d2[0] / l2 * dist)
        out.append(_cruza_reta((a[0] + n1[0], a[1] + n1[1]), d1, (v[0] + n2[0], v[1] + n2[1]), d2) or (v[0] + n1[0], v[1] + n1[1]))
    return out


def _fora_da_faixa(a, b, c, nrm, meia):
    """Os trechos do segmento a-b que ficam FORA da faixa |nrm . (x - c)| < meia (a fita de cima interrompe a de baixo)."""
    fa = nrm[0] * (a[0] - c[0]) + nrm[1] * (a[1] - c[1])
    fb = nrm[0] * (b[0] - c[0]) + nrm[1] * (b[1] - c[1])
    if abs(fb - fa) < 1e-12:
        return [] if abs(fa) < meia else [(a, b)]
    t1, t2 = sorted(((-meia - fa) / (fb - fa), (meia - fa) / (fb - fa)))
    ponto = lambda t: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)     # noqa: E731
    saida = []
    if t1 > 0:
        saida.append((a, ponto(min(1.0, t1))))
    if t2 < 1:
        saida.append((ponto(max(0.0, t2)), b))
    return [(x, y) for x, y in saida if math.hypot(y[0] - x[0], y[1] - x[1]) > 1e-6]


def _fita(p, ctx, uid):
    """Fita (faixa de tecido, fita de chegada, fita de isolamento) desenhada a traço: as duas bordas da banda de `espessura`
    e dois fios internos a `recuo` delas (e1, 8 px), com texto vivo opcional correndo no meio, repetido até cobrir o trecho
    (como na faixa-diagonal: o espaçamento só aperta, nunca estica). 'reta' atravessa a caixa no `angulo`; 'dobra' desce
    até a dobra e volta, como fita dobrada em V (o vinco marcado); 'cruzada' são duas fitas em X, e a de cima interrompe as
    linhas da de baixo. Tom sobre tom: tudo em traço currentColor, o miolo vazio para o texto. A tinta é a das linhas,
    recortada rente à caixa; `linhas` é a do texto (no meio da caixa).
    params: largura 1200; altura (reta a 0 grau: a própria espessura; senão 400); forma 'reta' | 'dobra' | 'cruzada';
    espessura 64; angulo 0 (reta) ou 20 (cruzada, ±); dobra 0,5 (onde cai a dobra, fração da largura); fios True; recuo
    'e1' (px ou e1..e8); espessura_borda 2; espessura_fio 1; texto | texto_de (opcional); tamanho 30% da banda; fonte
    'corpo'; peso 700; espacamento 0,12 em; separador ' · '; caixa_alta True; cor 'marca'."""
    forma = _escolha(p, "forma", "reta", ("reta", "dobra", "cruzada"))
    e = _medida(p, "espessura", 64)
    ang = float(p.get("angulo", 20 if forma == "cruzada" else 0))
    horizontal = forma == "reta" and abs(ang) < 1e-9
    if horizontal and p.get("altura") is not None and p.get("espessura") is None:
        e = _medida(p, "altura", 64)            # fita reta deitada: a altura pedida é a própria banda
    W = _medida(p, "largura", 1200)
    H = e if horizontal else _medida(p, "altura", 400)
    eb, ef = _medida(p, "espessura_borda", 2), _medida(p, "espessura_fio", 1)
    recuo = _espaco(p, "recuo", "e1")
    fios = bool(p.get("fios", True))
    if fios and recuo + eb / 2 + ef / 2 >= e / 2 - ef:
        raise ValueError(f"recuo {recuo:g} não cabe na banda de {e:g} px")
    caixa = [0.0, 0.0, W, H]
    ext = math.hypot(W, H)
    linhas_c = [(e / 2 - eb / 2, eb), (-(e / 2 - eb / 2), eb)]           # as bordas por dentro da banda
    if fios:
        linhas_c += [(e / 2 - eb - recuo, ef), (-(e / 2 - eb - recuo), ef)]

    def reta_por(cx, cy, graus):
        t = math.radians(graus)
        return [(cx - math.cos(t) * ext, cy - math.sin(t) * ext), (cx + math.cos(t) * ext, cy + math.sin(t) * ext)]

    if forma == "dobra":
        xf = W * float(p.get("dobra", 0.5))
        if not 0.15 * W <= xf <= 0.85 * W:
            raise ValueError("`dobra`: use de 0,15 a 0,85 da largura")
        ya, yf = e / 2, H - e / 2
        for _ in range(8):                          # a borda de fora encosta no topo nas laterais e na base na dobra
            t1, t2 = math.atan2(yf - ya, xf), math.atan2(yf - ya, W - xf)
            ya, yf = (e / 2) / math.cos(max(t1, t2)), H - (e / 2) / math.cos((t1 + t2) / 2)
        if yf <= ya:
            raise ValueError(f"caixa de {W:g} x {H:g} baixa demais para dobrar uma fita de {e:g} px")
        corridas = [[(-ext * math.cos(math.atan2(yf - ya, xf)), ya - ext * math.sin(math.atan2(yf - ya, xf))), (xf, yf),
                     (W + ext * math.cos(math.atan2(yf - ya, W - xf)), ya - ext * math.sin(math.atan2(yf - ya, W - xf)))]]
    elif forma == "cruzada":
        corridas = [reta_por(W / 2, H / 2, ang), reta_por(W / 2, H / 2, -ang)]
    else:
        corridas = [reta_por(W / 2, H / 2, ang)]
    cor = _cor_pagina(p.get("cor"), ctx)
    partes, caixas = [], []
    por_largura = {}
    for k, C in enumerate(corridas):
        for dist, w in linhas_c:
            L = _deslocada(C, dist)
            pedacos = list(zip(L, L[1:]))
            if forma == "cruzada" and k == 0:       # a de baixo: some onde a de cima passa
                a, b = corridas[1]
                d = (b[0] - a[0], b[1] - a[1]); Ld = math.hypot(*d)
                nrm = (-d[1] / Ld, d[0] / Ld)
                pedacos = [q for a_, b_ in pedacos for q in _fora_da_faixa(a_, b_, (W / 2, H / 2), nrm, e / 2 + w / 2)]
            for a_, b_ in pedacos:
                vis = _clip_caixa(_retangulo_traco(a_, b_, w) or [], caixa) if math.hypot(b_[0] - a_[0], b_[1] - a_[1]) > 1e-9 else []
                if vis:
                    caixas.append(_caixa_pts(vis))
            if forma == "dobra":
                for q in _quina(L[0], L[1], L[2], w):
                    if 0 <= q[0] <= W and 0 <= q[1] <= H:
                        caixas.append([q[0], q[1], q[0], q[1]])
            por_largura.setdefault(w, []).append(pedacos if forma != "dobra" else [tuple(L)])
    for w, grupos in por_largura.items():
        d = ""
        for g_ in grupos:
            if forma == "dobra":
                d += "M" + "L".join(f"{_n(x)} {_n(y)}" for x, y in g_[0])
            else:
                d += "".join(f"M{_n(a_[0])} {_n(a_[1])}L{_n(b_[0])} {_n(b_[1])}" for a_, b_ in g_)
        partes.append(f'<path d="{d}" stroke-width="{_n(w)}"/>')
    if forma == "dobra":                            # o vinco: da quina de cima à de baixo da dobra
        alto, baixo = _deslocada(corridas[0], e / 2)[1], _deslocada(corridas[0], -e / 2)[1]
        partes.append(f'<path data-parte="vinco" d="M{_n(alto[0])} {_n(alto[1])}L{_n(baixo[0])} {_n(baixo[1])}" stroke-width="{_n(ef)}"/>')
    defs, clip = _recorte_svg(uid, caixa)
    corpo = defs + f'<g fill="none" stroke="{cor}" stroke-linejoin="miter" stroke-linecap="butt"{clip}>{"".join(partes)}'
    texto, fontes, linhas = "", [], None
    if p.get("texto") or p.get("texto_de"):
        unidade = _texto(p, ctx, caixa_alta=p.get("caixa_alta", True))
        f = fonte(ctx, p.get("fonte", "corpo"), p.get("peso", 700))
        s = _r(p.get("tamanho") or e * 0.3)
        if f.cap_px(s) > e - 2 * (eb + (recuo + ef if fios else 0)):
            raise ValueError(f"texto de corpo {s:g} não cabe entre os fios da fita de {e:g} px")
        a, b = corridas[-1][0], corridas[-1][1]               # a corrida de cima (cruzada) ou a primeira (dobra)
        graus = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        if forma == "dobra":                                  # da lateral até antes do vinco
            cx, cy = xf / 2, (ya + yf) / 2
            t0, t1 = _segmento_visivel(cx, cy, graus, W, H)
            t1 = min(t1, math.hypot(xf - cx, yf - cy) - e / 2)
        else:
            cx, cy = W / 2, H / 2
            t0, t1 = _segmento_visivel(cx, cy, graus, W, H)
        if t1 - t0 <= s:
            raise ValueError("a fita não tem trecho visível para o texto")
        normal = min(float(p.get("espacamento", 0.12)), 0.12) * s
        linha, ls = _linha_que_cobre(f, unidade + p.get("separador", " · "), s, normal, t1 - t0)
        corpo += "</g>"            # o recorte num grupo sem transform: no mesmo nó do rotate, a caixa do clipPath giraria junto
        corpo += (f'<g{clip}><g transform="translate({_n(cx)} {_n(cy)}) rotate({_n(graus)})"><text x="{_n(t0)}" '
                  f'y="{_n(f.cap_px(s) / 2)}" fill="{cor}" style="{_estilo(f, s, ls)}">{_esc(linha)}</text></g></g>')
        texto, fontes = unidade, [f.familia]
        base = cy + f.cap_px(s) / 2 / math.cos(math.radians(graus))
        linhas = {"linha_base": base, "cap": base - f.cap_px(s)}
    else:
        corpo += "</g>"
    tinta = _uniao(caixas)
    if tinta is None:
        raise ValueError("a fita não passa pela caixa")
    out = dict(svg=_svg(_inteiro(W), _inteiro(H), corpo, "fita", uid), w=_inteiro(W), h=_inteiro(H), texto=texto, fontes=fontes,
               tinta=[max(0.0, tinta[0]), max(0.0, tinta[1]), min(W, tinta[2]), min(H, tinta[3])])
    if linhas:
        out["linhas"] = linhas
    return out


def _falhas(comprimento, falhas, rng):
    """stroke-dasharray de um traço com `falhas` (fração do comprimento que fica sem tinta, como carimbo gasto): vãos de
    1,5 a 5,5 px espalhados pela semente, traços de comprimento sorteado que somam o resto. Vazio quando falhas = 0."""
    if falhas <= 0:
        return ""
    vazio = falhas * comprimento
    n = max(1, int(round(vazio / 3.5)))
    vaos = rng.uniform(1.5, 5.5, n)
    vaos *= vazio / vaos.sum()
    tracos = rng.dirichlet(np.ones(n)) * (comprimento - vazio)
    return f' stroke-dasharray="{" ".join(f"{_n(t)} {_n(v)}" for t, v in zip(tracos, vaos))}"'


def _carimbo(p, ctx, uid):
    """Carimbo: o selo de borracha (aprovado, edição, homologado). 'redondo' = anel duplo, texto vivo correndo na borda (o
    `selo` desenha os dois arcos, com a mesma medida) e um texto grande no centro entre dois fios; 'retangular' = moldura
    dupla com o texto da borda em cima, o do centro grande e o de baixo. `falhas` tira tinta dos traços (anéis, molduras,
    fios) por tracejado irregular sorteado pela `semente`, como borracha gasta; o texto fica inteiro e vivo.
    params: forma 'redondo' | 'retangular'; texto | texto_de (borda); texto_baixo (opcional); centro_texto (opcional);
    diametro 280 (redondo; ou `largura`/`altura`: o menor); largura 440 e altura 200 (retangular, a medida da tinta);
    falhas 0 (de 0 a 0,15); semente 7; espessura 3 (o traço de fora) e 1,5 (o de dentro); fonte 'display'; peso;
    fonte_centro (padrão = fonte); caixa_alta True; cor 'marca'."""
    forma = _escolha(p, "forma", "redondo", ("redondo", "retangular"))
    falhas = float(p.get("falhas", 0))
    if not 0 <= falhas <= 0.15:
        raise ValueError(f"falhas {falhas:g}: use de 0 a 0,15 (mais que isso o carimbo deixa de ser lido)")
    rng = np.random.default_rng(int(p.get("semente", 7)))
    e1, e2 = _medida(p, "espessura", 3), _medida(p, "espessura_dentro", 1.5)
    cor = _cor_pagina(p.get("cor"), ctx)
    papel = p.get("fonte", "display")
    partes, textos, fontes, linhas = [], [], [], None
    if forma == "redondo":
        if p.get("diametro") is None and (p.get("largura") is not None or p.get("altura") is not None):
            D = min(float(p[k]) for k in ("largura", "altura") if p.get(k) is not None)
        else:
            D = _medida(p, "diametro", 280)
        R = D / 2
        anel = 0.2 * D
        sel = {k: v for k, v in p.items() if k in ("texto", "texto_de", "texto_baixo", "peso", "caixa_alta", "separador",
                                                    "separador_anel", "espacamento_min", "espacamento_max")}
        r = _selo(dict(sel, diametro=D, anel=anel, centro=None, contorno=False, fonte=papel), ctx, uid)
        hexa = _cor(None, ctx)
        corpo_selo = _corpo_svg(r["svg"]).replace(f'"{hexa}"', f'"{cor}"')
        partes.append(corpo_selo)
        textos += [t for t in r["texto"].split("\n") if t]
        fontes += r["fontes"]
        for raio, esp in ((R - e1 / 2, e1), (R - anel - e2, e2)):
            partes.append(f'<circle data-anel="1" cx="{_n(R)}" cy="{_n(R)}" r="{_n(raio)}" fill="none" stroke="{cor}" '
                          f'stroke-width="{_n(esp)}"{_falhas(2 * math.pi * raio, falhas, rng)}/>')
        rc = R - anel - e2 - 4
        if p.get("centro_texto"):
            ct = _texto(p, ctx, "centro_texto", p.get("caixa_alta", True))
            fc = fonte(ctx, p.get("fonte_centro", papel), p.get("peso_centro", p.get("peso")))
            sc = _r(min(1.5 * rc / fc.largura(ct, 1.0), 0.46 * rc / (fc.cap / fc.upem)))
            base = R + fc.cap_px(sc) / 2
            svg_t, _ = _texto_svg(fc, ct, R, base, sc, 0.0, cor, "middle")
            partes.append(svg_t)
            meia = 0.62 * rc
            for y in (R - fc.cap_px(sc) / 2 - 0.16 * rc, R + fc.cap_px(sc) / 2 + 0.16 * rc):
                partes.append(f'<path data-fio="1" d="M{_n(R - meia)} {_n(y)}L{_n(R + meia)} {_n(y)}" fill="none" stroke="{cor}" '
                              f'stroke-width="{_n(e2)}"{_falhas(2 * meia, falhas, rng)}/>')
            textos.append(ct); fontes.append(fc.familia)
            linhas = {"linha_base": base, "cap": base - fc.cap_px(sc)}
        Di = _inteiro(D)
        out = dict(svg=_svg(Di, Di, "".join(partes), "carimbo", uid), w=Di, h=Di, texto="\n".join(textos),
                   fontes=list(dict.fromkeys(fontes)), tinta=[0.0, 0.0, D, D])
    else:
        W, H = _medida(p, "largura", 440), _medida(p, "altura", 200)
        o1, o2 = e1 / 2, e1 + 5 + e2 / 2
        for (x0, y0, x1, y1), esp in (((o1, o1, W - o1, H - o1), e1), ((o2, o2, W - o2, H - o2), e2)):
            partes.append(f'<rect data-anel="1" x="{_n(x0)}" y="{_n(y0)}" width="{_n(x1 - x0)}" height="{_n(y1 - y0)}" fill="none" '
                          f'stroke="{cor}" stroke-width="{_n(esp)}"{_falhas(2 * (x1 - x0 + y1 - y0), falhas, rng)}/>')
        dentro = (e1 + 5 + e2, W - e1 - 5 - e2, e1 + 5 + e2, H - e1 - 5 - e2)       # x0, x1, y0, y1 do miolo
        lw, lh = dentro[1] - dentro[0], dentro[3] - dentro[2]
        f = fonte(ctx, papel, p.get("peso"))
        faixas = [("texto", 0.2), ("centro_texto", 0.42), ("texto_baixo", 0.2)]
        presentes = [(k, fr) for k, fr in faixas if p.get(k) or (k == "texto" and p.get("texto_de"))]
        if not presentes:
            raise ValueError("carimbo retangular sem texto: passe texto, centro_texto ou texto_baixo")
        total = sum(fr for _, fr in presentes)
        y = dentro[2] + lh * 0.08
        alto_util = lh * 0.84
        for k, fr in presentes:
            faixa = alto_util * fr / total
            t = _texto(p, ctx, k, p.get("caixa_alta", True))
            fk = fonte(ctx, p.get("fonte_centro", papel), p.get("peso_centro", p.get("peso"))) if k == "centro_texto" else f
            ls_em = 0.0 if k == "centro_texto" else 0.12
            sk = _r(min(0.9 * lw / (fk.largura(t, 1.0, ls_em) - ls_em), 0.7 * faixa / (fk.cap / fk.upem)))
            ls = _r(ls_em * sk)
            base = y + faixa / 2 + fk.cap_px(sk) / 2
            svg_t, _ = _texto_svg(fk, t, W / 2, base, sk, ls, cor, "middle")
            partes.append(svg_t)
            textos.append(t); fontes.append(fk.familia)
            if k == "centro_texto" or linhas is None:
                linhas = {"linha_base": base, "cap": base - fk.cap_px(sk)}
            y += faixa
        out = dict(svg=_svg(_inteiro(W), _inteiro(H), "".join(partes), "carimbo", uid), w=_inteiro(W), h=_inteiro(H),
                   texto="\n".join(textos), fontes=list(dict.fromkeys(fontes)), tinta=[0.0, 0.0, W, H])
    if linhas:
        out["linhas"] = linhas
    return out


def _numeral_eco(p, ctx, uid):
    """Numeral com eco: o número cheio (o ano, a edição) e atrás dele cópias preenchidas que se afastam em degraus de espaço
    e de opacidade (nunca contorno: o contorno de texto é o `eco` em path). A tinta é o número da frente mais as cópias
    com opacidade de pelo menos 0,5 (a régua de meia opacidade: nos degraus de sempre, .24 a .06, só o da frente conta);
    `linhas` é a do número da frente; a caixa do svg leva todas as cópias.
    params: texto (ex.: '2027', '02'); copias 2 (1 a 3); deslocamento 'e4'; direcao 45 (graus, ou dir, esq, baixo, cima);
    opacidades [0.24, 0.12, 0.06] (dos degraus); altura 400 (a do número da frente; ou `largura`; com as duas, a maior que
    cabe); fonte 'display' | 'lettering'; peso; espacamento 0 em (nunca abaixo de -0,02); cor 'marca'."""
    texto = _texto(p, ctx, caixa_alta=False)
    n = int(_medida(p, "copias", 2))
    if not 1 <= n <= 3:
        raise ValueError(f"copias {n}: use de 1 a 3")
    ops = _opacidades(p, n)
    desl = _espaco(p, "deslocamento", "e4")
    ux, uy = _rumo(p, "direcao", 45)
    f, t_em = _fonte_expressiva(p, ctx)
    x0, y0, x1, y1 = f.caixa_tinta(texto, 1.0, t_em)
    if x1 - x0 <= 0 or y1 - y0 <= 0:
        raise ValueError(f"numeral sem tinta: {texto!r}")
    kmax = max([0] + [k + 1 for k, o in enumerate(ops) if o >= 0.5])      # a cópia mais longe que ainda é tinta
    ped = _medidas_pedidas(p) or {"altura": 400.0}
    cands = ([(ped["largura"] - abs(ux) * desl * kmax) / (x1 - x0)] if "largura" in ped else []) + \
        ([(ped["altura"] - abs(uy) * desl * kmax) / (y1 - y0)] if "altura" in ped else [])
    s = math.floor(min(cands) * 1000) / 1000
    if s <= 1:
        raise ValueError("medida pequena demais para o deslocamento das cópias")
    ls = _r(t_em * s)
    cor = _cor_pagina(p.get("cor"), ctx)
    partes, caixas, tinta = [], [], []
    for k in range(n, -1, -1):                     # da cópia mais longe à frente (k = 0, opaca, por cima)
        ox, oy = k * ux * desl, k * uy * desl
        op = "" if k == 0 else (f' fill-opacity="{_n(ops[k - 1])}"' if ops[k - 1] < 1 else "")
        svg_t, cx = _texto_svg(f, texto, ox, oy, s, ls, cor, "start", extra=f' data-copia="{k}"{op}')
        partes.append(svg_t)
        caixas.append(cx)
        if k == 0 or ops[k - 1] >= 0.5:
            tinta.append(cx)
    caixa, frente = _uniao(caixas), _uniao(tinta)
    ox, oy = math.floor(caixa[0] - 1), math.floor(caixa[1] - 1)
    w, h = int(math.ceil(caixa[2] + 1)) - ox, int(math.ceil(caixa[3] + 1)) - oy
    corpo = f'<g transform="translate({-ox} {-oy})">{"".join(partes)}</g>'
    return dict(svg=_svg(w, h, corpo, "numeral-eco", uid), w=w, h=h, texto=texto, fontes=[f.familia],
                tinta=[frente[0] - ox, frente[1] - oy, frente[2] - ox, frente[3] - oy],
                linhas={"linha_base": -oy + 0.0, "cap": -oy - f.cap_px(s)})


MEIO_TOM_MAX = 15000


def _meio_tom_foto(p, ctx, uid):
    """Foto do kit refeita em meio-tom (retícula de jornal, pôster de serigrafia): a imagem vira pontos de uma cor, o raio
    pela luminância média de cada célula (escuro = ponto grande; 'claro' inverte). Vetorial (um <circle> por ponto) e sem
    <image>: o PDF não ganha imagem nenhuma. O número de células sai da medida pedida e a grade escala inteira com a caixa,
    então a tinta mede exatamente o pedido (largura ou altura; a outra segue a proporção da foto; com as duas, a maior que
    cabe). A caixa do svg é a tinta mais 1 px (a retícula girada passa um pouco da foto). No máximo 15 mil pontos.
    params: png (ou imagem: arquivo do kit); recorte [x0, y0, x1, y1] da foto em fração (opcional); largura 600 (ou altura);
    celula 14 (no mínimo 12 px); angulo 0 (45 = retícula clássica); modo 'escuro' | 'claro'; gama 1; minimo 0,06 (abaixo,
    sem ponto); cor 'marca'."""
    from scipy.ndimage import map_coordinates, uniform_filter
    arq = p.get("png") or p.get("imagem")
    if not arq or not Path(arq).exists():
        raise ValueError(f"meio-tom-foto: imagem não encontrada ({arq})")
    im = Image.open(arq)
    if im.mode in ("RGBA", "LA", "P"):
        fundo = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(fundo, im.convert("RGBA"))
    im = im.convert("L")
    if p.get("recorte"):
        a, b, c, d = (float(v) for v in p["recorte"])
        im = im.crop((round(a * im.width), round(b * im.height), round(c * im.width), round(d * im.height)))
    asp = im.height / im.width
    c = _medida(p, "celula", 14)
    if c < 12:
        raise ValueError(f"celula {c:g}: use pelo menos 12 px (ponto menor some na impressão e pesa o PDF)")
    modo = _escolha(p, "modo", "escuro", ("escuro", "claro"))
    gama, minimo = _medida(p, "gama", 1), float(p.get("minimo", 0.06))
    ped = _medidas_pedidas(p)
    if not ped:
        ped = {"largura": 600.0}
    larg_ref = min(([ped["largura"]] if "largura" in ped else []) + ([ped["altura"] / asp] if "altura" in ped else []))
    angulo = float(p.get("angulo", 0))
    R0 = None

    def reticula(nx):
        """Pontos da grade de nx colunas, em fração da largura da foto: (xs, ys, raios, caixa da tinta)."""
        nonlocal R0
        cn = 1.0 / nx
        xs, ys = _grade(1.0, asp, cn, angulo)
        if len(xs) > 4 * MEIO_TOM_MAX:
            raise ValueError(f"meio-tom com {len(xs)} células: aumente a célula")
        R = nx * 6
        amostra = np.asarray(im.resize((R, max(1, round(R * asp))), Image.BOX), float) / 255
        v = map_coordinates(uniform_filter(amostra, size=6, mode="nearest"), [ys * R - 0.5, xs * R - 0.5], order=1, mode="nearest")
        v = np.clip((1 - v) if modo == "escuro" else v, 0, 1) ** gama
        raios = np.where(v >= minimo, (cn / 2) * 0.96 * np.sqrt(v), 0.0)
        vivos = raios * nx * c > 0.25                  # ponto que no tamanho final passa de 0,25 px
        xs, ys, raios = xs[vivos], ys[vivos], raios[vivos]
        if not len(xs):
            raise ValueError("meio-tom sem ponto nenhum: a foto é clara demais para o modo (ou baixe o mínimo)")
        if len(xs) > MEIO_TOM_MAX:
            raise ValueError(f"meio-tom com {len(xs)} pontos (o teto é {MEIO_TOM_MAX}): aumente a célula")
        return xs, ys, raios, [float((xs - raios).min()), float((ys - raios).min()), float((xs + raios).max()), float((ys + raios).max())]

    def escala(t):
        return min(([ped["largura"] / (t[2] - t[0])] if "largura" in ped else []) + ([ped["altura"] / (t[3] - t[1])] if "altura" in ped else []))

    # a tinta pode ser só parte da foto (borda clara sem ponto): o número de colunas é refeito até a célula final ficar o mais
    # perto possível do pedido sem passar para baixo dele
    nx, melhor = max(2, int(larg_ref // c)), None
    for _ in range(8):
        res = reticula(nx)
        k = escala(res[3])
        if k / nx >= c - 1e-9:
            melhor = (res, k)
            mais = max(2, int(k // c))
            if mais <= nx:
                break
            nx = mais
        elif nx > 2:
            nx -= 1
        else:
            break
    if melhor is None:
        raise ValueError(f"meio-tom: medida pequena demais para a célula de {c:g} px")
    (xs, ys, raios, t), k = melhor
    cor = _cor_pagina(p.get("cor"), ctx)
    pontos = "".join(f'<circle cx="{_n(x * k)}" cy="{_n(y * k)}" r="{_n(r * k)}"/>' for x, y, r in zip(xs, ys, raios))
    r, _ = _fechar("meio-tom-foto", uid, f'<g fill="{cor}">{pontos}</g>', [v_ * k for v_ in t])     # a caixa é a tinta (a retícula
    return dict(r, texto="", fontes=[])                                                            # girada passa da foto)


TIPOS = {
    "microtexto": _microtexto, "selo": _selo, "meio-tom-simbolo": _meio_tom_simbolo, "pattern-simbolo": _pattern_simbolo,
    "linha-percurso": _linha_percurso, "fios-tecnicos": _fios_tecnicos, "moldura": _moldura, "etiqueta": _etiqueta,
    "numeral": _numeral, "tipo-textura": _tipo_textura, "faixa-diagonal": _faixa_diagonal, "mosaico": _mosaico,
    # composição (desenhos presos a algo da página)
    "linhas": _linhas, "listras": _listras, "colchetes": _colchetes, "fio": _fio, "regua": _regua, "divisoria": _divisoria,
    "grade-pontos": _grade_pontos, "circulos": _circulos, "setas": _setas, "estrelas": _estrelas, "campo": _campo,
    "placar": _placar, "celular": _celular, "mapa": _mapa,
    # constantes de borda (sistema_elementos.constantes)
    "fio-borda": _fio_borda, "pattern-borda": _pattern_borda,
    # acabamento (Frente G, 12/10/2026): textura, borda, profundidade e tipografia expressiva
    "hachura": _hachura, "malha": _malha, "aneis": _aneis, "pontos-radiais": _pontos_radiais, "cantoneira": _cantoneira,
    "moldura-dupla": _moldura_dupla, "regua-borda": _regua_borda, "eco": _eco, "texto-curva": _texto_curva,
    "ondas": _ondas, "curvas-nivel": _curvas_nivel, "fita": _fita, "carimbo": _carimbo, "numeral-eco": _numeral_eco,
    "meio-tom-foto": _meio_tom_foto,
}


# ---------------------------------------------------------------- medida: largura e altura são a medida da TINTA
# A composição (references/09-composicao.md) declara a escala de um grafismo como UMA dimensão da tinta (1/3 da página, 4
# colunas, 3 alturas de maiúscula) e pede o svg NA MEDIDA da colocação: `largura` ou `altura` em px, em escala 1, com texto vivo
# e traço na espessura que o gerador desenhou, sem esticar. Por isso todo tipo honra `largura` e/ou `altura` como a medida da
# TINTA (a caixa do svg é a tinta mais, no máximo, 1 px de margem): sozinha, a medida sai exata (até 0,5 px); com as duas, os de
# área (linhas, listras, mapa...) fazem cada dimensão a pedida e os de proporção fixa (selo, celular, campo, estrelas...) fazem
# a maior que couber nas duas. Quem já tinha `largura`/`altura` com outro sentido (microtexto, moldura, percurso, numeral...)
# mantém o sentido de antes quando é chamado como antes.
ESCALAVEIS = {    # desenho de forma: tudo que tem tamanho cresce junto (k x), então a medida da tinta é proporcional a k
    "circulos": {"espessura": 1.5},
    "setas": {"tamanho": 28.0, "passo": None, "espessura": None},
    "estrelas": {"tamanho": 32.0, "passo": None, "espessura": None},
    "tipo-textura": {"tamanho": 120.0},
    "mosaico": {"modulo": 180.0, "vao": 0.0},
}
CORRIGIR = ("linhas", "listras", "grade-pontos", "pattern-borda", "mapa", "campo", "linha-percurso")   # `largura` é a caixa; a tinta é menos
CORRIGIR_DUAS = ("hachura", "malha", "aneis", "pontos-radiais", "ondas", "curvas-nivel", "fita")   # idem, e com as duas medidas acerta as duas (os tipos novos de área)


def _medidas_pedidas(params):
    """{'largura': px, 'altura': px} das que vieram em params (e valem: número finito maior que zero)."""
    out = {}
    for d in ("largura", "altura"):
        if params.get(d) is not None:
            try:
                v = float(params[d])
            except (TypeError, ValueError):
                raise ValueError(f"`{d}`: use um número (recebi {params[d]!r})") from None
            if not (math.isfinite(v) and v > 0):
                raise ValueError(f"`{d}` precisa ser maior que zero (recebi {v:g})")
            out[d] = v
    return out


def _dim_tinta(r, dim):
    """A medida da tinta de um resultado na dimensão `largura` ou `altura`; sem `tinta`, a da caixa do svg."""
    t = r.get("tinta")
    if t:
        return float(t[2] - t[0]) if dim == "largura" else float(t[3] - t[1])
    return float(r["w"] if dim == "largura" else r["h"])


def _secante(f, alvo, x0, tol=0.2, maximo=8):
    """x com f(x) = alvo para f contínua, crescente e quase afim (a tinta em função do parâmetro): um passo multiplicativo e a
    secante depois; para afim (tinta = parâmetro menos a margem) fecha em 2 ou 3 chamadas."""
    xa, ya = float(x0), f(float(x0))
    if abs(ya - alvo) <= tol or ya <= 0:
        return xa
    xb = xa * alvo / ya
    yb = f(xb)
    for _ in range(maximo):
        if abs(yb - alvo) <= tol or yb == ya:
            break
        xc = xb + (alvo - yb) * (xb - xa) / (yb - ya)
        xa, ya, xb, yb = xb, yb, xc, f(xc)
    return xb


def _escalar(tipo, base, k):
    """Os parâmetros do tipo com tudo que tem tamanho multiplicado por k (ESCALAVEIS)."""
    q = dict(base)
    for nome, padrao in ESCALAVEIS[tipo].items():
        if base.get(nome) is not None:
            q[nome] = float(base[nome]) * k
        elif padrao is not None:
            q[nome] = padrao * k
    if tipo == "circulos":
        if base.get("raios") is not None:
            q["raios"] = [float(x) * k for x in base["raios"]]
        elif base.get("raio_max") is not None:
            q["raio_max"] = float(base["raio_max"]) * k
    return q


def _fixar_por_escala(tipo, params, ctx, uid):
    """Tipo de forma (ESCALAVEIS) na medida pedida: gera uma vez, mede a tinta e escala tudo por k = pedido / tinta (exato,
    porque a tinta é proporcional a k); com as duas medidas, k é o menor dos dois (o desenho cabe nas duas)."""
    alvo = _medidas_pedidas(params)
    base = {k: v for k, v in params.items() if k not in ("largura", "altura")}
    k = 1.0
    r = TIPOS[tipo](_escalar(tipo, base, k), ctx, uid)
    for _ in range(5):
        razoes = {d: v / _dim_tinta(r, d) for d, v in alvo.items() if _dim_tinta(r, d) > 0}
        if not razoes:
            raise ValueError(f"grafismo `{tipo}` sem tinta: nada a medir")
        limite = min(razoes, key=razoes.get)
        if abs(_dim_tinta(r, limite) - alvo[limite]) <= (0.25 if r.get("tinta") else 0.99):
            break
        k *= razoes[limite]
        r = TIPOS[tipo](_escalar(tipo, base, k), ctx, uid)
    return r


def _corrigir_pela_tinta(tipo, params, ctx, uid, r):
    """Tipo de área em que `largura`/`altura` é a caixa e a tinta é menos (margem do mapa, degrau do esmaecer, recorte): com UMA
    medida pedida, acha a caixa cuja tinta mede o pedido (secante sobre a tinta). Com as duas, vale a caixa."""
    alvo = _medidas_pedidas(params)
    if len(alvo) != 1:
        return r
    dim, px = next(iter(alvo.items()))
    if abs(_dim_tinta(r, dim) - px) <= 0.3:
        return r
    guardado = {}

    def tinta_de(x):
        guardado["r"] = TIPOS[tipo](dict(params, **{dim: round(x, 3)}), ctx, uid)
        return _dim_tinta(guardado["r"], dim)
    _secante(tinta_de, px, px, tol=0.3)
    return guardado.get("r", r)


def gerar(tipo: str, params: dict, ctx: dict) -> dict:
    """Contrato da Frente B (references/08-sistema-elementos.md). Determinístico: mesmos params e ctx, mesmo SVG. Sempre
    svg, w, h, texto e fontes; os desenhos de composição devolvem também `tinta` ([x0, y0, x1, y1] na caixa do svg),
    `linhas` ({linha_base, cap}, quando têm texto) e, os presos a geometria da página (fio, colchetes), `origem`.
    `largura` e/ou `altura` em params são a medida da TINTA em px (ver o bloco "medida" acima): é assim que a composição pede o
    grafismo na medida da colocação, sem esticar."""
    if tipo not in TIPOS:
        raise ValueError(f"grafismo `{tipo}` desconhecido; tipos: {', '.join(TIPOS)}")
    params, ctx = dict(params or {}), dict(ctx or {})
    uid = _uid(tipo, params, ctx)
    if tipo in ESCALAVEIS and _medidas_pedidas(params):
        r = _fixar_por_escala(tipo, params, ctx, uid)
    else:
        r = TIPOS[tipo](params, ctx, uid)
        if tipo in CORRIGIR:
            r = _corrigir_pela_tinta(tipo, params, ctx, uid, r)
        elif tipo in CORRIGIR_DUAS:
            r = _corrigir_duas(tipo, params, ctx, uid, r)
    out = {"svg": r["svg"], "w": int(r["w"]), "h": int(r["h"]), "texto": r.get("texto", ""), "fontes": list(r.get("fontes", []))}
    if r.get("tinta") is not None:
        out["tinta"] = [round(float(v), 1) + 0.0 for v in r["tinta"]]      # + 0.0: sem -0.0
    if r.get("linhas"):
        out["linhas"] = {k: round(float(v), 1) + 0.0 for k, v in r["linhas"].items()}
    if r.get("origem") is not None:
        out["origem"] = [int(v) for v in r["origem"]]
    return out


# ---------------------------------------------------------------- kit, navegador, folha
def ctx_do_kit(pasta, receita=None, fontes_dir=None):
    """Monta o ctx a partir do mediakit.json do kit (fontes e paleta da receita; logo pelo marca.logo_id)."""
    pasta = Path(pasta)
    k = json.loads((pasta / "mediakit.json").read_text(encoding="utf-8"))
    rec = next((r for r in k.get("receitas") or [] if r.get("id") == receita), None) if receita else None
    if receita and rec is None:
        raise ValueError(f"receita `{receita}` não existe no mediakit.json")
    marca = k.get("marca") or {}
    if rec:
        fontes = {"display": rec["fontes"]["display"], "peso_display": rec["fontes"].get("peso_display") or 700,
                  "corpo": rec["fontes"]["corpo"], "titulo": rec["fontes"].get("titulo")}
        paleta = dict(rec["paleta"])
    else:
        fontes = {"display": marca.get("fonte_display"), "peso_display": 700, "corpo": marca.get("fonte_corpo")}
        paleta = {"marca": marca.get("cor_primaria", "#E8307A"), "apoio": marca.get("cor_secundaria", "#FFFFFF"),
                  "escuro": marca.get("cor_fundo_escuro", "#0B0B0C"), "texto": "#FFFFFF", "papel": "#F6F1EA"}
    logo = next((a for a in k.get("acervo") or [] if a.get("id") == marca.get("logo_id")), None)
    return {"fontes": fontes, "paleta": paleta, "evento": k.get("evento") or {},
            "logo_png": str(dentro_do_kit(pasta, logo["arquivo"])) if logo else None,
            "fontes_dir": str(fontes_dir or pasta / "fontes")}


def css_fontes(fontes_dir, familias=None):
    """@font-face de cada arquivo da pasta, com a mesma regra do render.py (Familia__700 = peso 700; sem sufixo = 100 900)."""
    faces = []
    for f in sorted(Path(fontes_dir).iterdir()):
        ext = f.suffix.lower()
        if ext not in (".otf", ".ttf", ".woff2", ".woff"):
            continue
        fam, _, peso = f.stem.partition("__")
        if familias and fam not in familias:
            continue
        fmt = {".otf": "opentype", ".ttf": "truetype", ".woff2": "woff2", ".woff": "woff"}[ext]
        mime = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
        uri = f"data:{mime};base64," + base64.b64encode(f.read_bytes()).decode()
        faces.append(f"@font-face {{ font-family: '{fam}'; src: url({uri}) format('{fmt}'); font-display: block; "
                     f"font-weight: {peso if peso.isdigit() else '100 900'}; font-style: normal; }}")
    return "\n".join(faces)


JS_MEDIR = """async () => {
  const pedidos = new Set();
  for (const t of document.querySelectorAll('svg[data-grafismo] text')) {
    const c = getComputedStyle(t); pedidos.add(`${c.fontWeight} 40px ${c.fontFamily}`);
  }
  for (const f of pedidos) { try { await document.fonts.load(f); } catch (e) {} }
  await document.fonts.ready;
  return Array.from(document.querySelectorAll('svg[data-grafismo]')).map(s => ({
    tipo: s.dataset.grafismo, uid: s.dataset.uid,
    textos: Array.from(s.querySelectorAll('text')).map(t => ({comprimento: t.getComputedTextLength(), caracteres: t.getNumberOfChars(),
      familia: getComputedStyle(t).fontFamily, peso: getComputedStyle(t).fontWeight,
      arco: t.dataset.arco || null, alvo: t.dataset.alvo ? +t.dataset.alvo : null})),
    caminhos: Array.from(s.querySelectorAll('path[id]')).map(p => ({id: p.id, comprimento: p.getTotalLength()})),
  }));
}"""


def pagina(svgs, fontes_dir, fundo="#111111", legendas=None, largura=1800, familias=None, cor_legenda="#DDDDDD", cor=None):
    """HTML de revisão. `cor` = o acento da página: os desenhos de composição pintam em currentColor e herdam dela."""
    legendas = legendas or [""] * len(svgs)
    celulas = "".join(f'<figure><div class="caixa">{s}</div><figcaption>{_esc(l)}</figcaption></figure>' for s, l in zip(svgs, legendas))
    acento = f" color: {cor};" if cor else ""
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{css_fontes(fontes_dir, familias)}\n"
            f"* {{ font-synthesis: none; box-sizing: border-box; }} body {{ margin: 0; background: {fundo}; width: {largura}px;{acento} }}"
            "main { display: flex; flex-wrap: wrap; gap: 28px; padding: 28px; align-items: flex-start; }"
            "figure { margin: 0; } .caixa { outline: 1px dashed rgba(127,127,127,.35); line-height: 0; }"
            f"figcaption {{ font: 600 15px/1.4 ui-monospace, Menlo, monospace; color: {cor_legenda}; padding-top: 8px; max-width: 900px; }}"
            f"svg {{ display: block; }}</style></head><body><main>{celulas}</main></body></html>")


def medir_no_chromium(svgs, fontes_dir, png=None, fundo="#111111", legendas=None, largura=1800, transparente=False, cor=None):
    """Abre os SVGs numa página com as @font-face do kit (mesma regra do render.py) e devolve, por SVG, o
    getComputedTextLength() de cada <text> e o getTotalLength() de cada <path> com id. Com `png`, grava a captura.
    `cor` = acento da página (currentColor dos desenhos de composição)."""
    from playwright.sync_api import sync_playwright
    html_txt = pagina(svgs, fontes_dir, fundo, legendas, largura, cor=cor)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": largura, "height": 900}, device_scale_factor=1)
        pg.set_content(html_txt, wait_until="load")
        medidas = pg.evaluate(JS_MEDIR)
        if png:
            pg.screenshot(path=str(png), full_page=True, omit_background=transparente)
        b.close()
    return medidas


def rasterizar(svg, saida, fontes_dir=None, escala=1, cor=None):
    """PNG do SVG no tamanho dele (x escala), fundo transparente, desenhado pelo mesmo Chromium do render. Serve para
    QA (costura do pattern, OCR, prévia na biblioteca); a página usa o SVG inline, não este PNG. `cor` = o acento da
    página, para os desenhos em currentColor (sem ela o navegador pinta de preto)."""
    from playwright.sync_api import sync_playwright
    css = css_fontes(fontes_dir) if fontes_dir else ""
    acento = f" color: {cor};" if cor else ""
    html_txt = (f"<!doctype html><html><head><meta charset='utf-8'><style>{css}\n* {{ font-synthesis: none; }} "
                f"html, body {{ margin: 0; background: transparent;{acento} }} svg {{ display: block; }}</style></head><body>{svg}</body></html>")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(device_scale_factor=escala)
        pg.set_content(html_txt, wait_until="load")
        pg.evaluate("document.fonts.ready")
        pg.locator("svg").first.screenshot(path=str(saida), omit_background=True)
        b.close()
    return saida


def exemplos_folha(ctx, recorte=None):
    """Um exemplo de cada tipo com o ctx do kit (a folha de revisão). Fica de fora o `mapa`, que precisa de coordenadas
    (lat e lon) que o kit não guarda, e o `meio-tom-foto`, que precisa de uma foto (o logo, claro sobre transparente, não
    tem tom para a retícula); o `celular` entra quando o kit tem logo (a imagem da tela)."""
    ev = ctx.get("evento") or {}
    ano = str(ev.get("data_inicio") or "2027")[:4]
    nome = (ev.get("nome") or "EVENTO").upper()
    cidade = "/".join(x for x in (ev.get("cidade"), ev.get("uf")) if x).upper()
    ed = ev.get("edicao_numero")
    micro = " · ".join(x for x in (nome, _data_br(ev.get("data_inicio")), cidade, f"{ed}ª EDIÇÃO" if ed else None) if x)
    tem_logo = bool(ctx.get("logo_png"))
    lista = [
        ("microtexto", {"texto": micro, "largura": 1740}),
        ("selo", {"texto": f"{nome} · {ed}ª EDIÇÃO · {ano} ·" if ed else f"{nome} · {ano} ·", "diametro": 300, "recorte": recorte}),
        ("selo", {"texto": f"{nome} · {cidade} ·", "diametro": 300, "centro": "texto", "centro_texto": ano, "fundo": "marca", "cor": "escuro"}),
        ("numeral", {"texto": ano, "altura": 220}),
        ("numeral", {"texto": f"{ed:02d}" if ed else "01", "altura": 220, "estilo": "fantasma", "opacidade": 0.18}),
        ("numeral", {"texto": f"{ed:02d}" if ed else "01", "altura": 220, "estilo": "contorno"}),
        ("tipo-textura", {"texto": nome.split()[0], "tamanho": 64, "repeticoes": 7}),
        ("etiqueta", {"texto": "COTA OURO", "forma": "seta"}),
        ("etiqueta", {"texto": "NAMING RIGHTS", "forma": "pilula", "fundo": "papel"}),
        ("moldura", {"largura": 420, "altura": 260, "etiqueta": {"texto": "PÓRTICO DE LARGADA"}}),
        ("moldura", {"largura": 420, "altura": 260, "cantos": "marcas", "etiqueta": {"texto": "PROJEÇÃO", "posicao": "inf-dir"}}),
        ("linha-percurso", {"largura": 860, "altura": 360, "curva": {"tipo": "orla"}, "distancia_km": 10}),
        ("fios-tecnicos", {"largura": 860, "altura": 300, "alvos": [{"x": 120, "y": 200, "rotulo": "Pórtico"},
                                                                     {"x": 420, "y": 110, "rotulo": "Backdrop de pódio"},
                                                                     {"x": 760, "y": 230, "rotulo": "Camisa", "lado": "esq"}]}),
        ("faixa-diagonal", {"largura": 860, "altura": 300, "espessura": 70, "angulo": -10, "y": 0.5, "texto": micro}),
        ("mosaico", {"colunas": 6, "linhas": 2, "modulo": 140, "recorte": recorte}),
    ]
    lista += [
        ("linhas", {"largura": 420, "altura": 200, "espacamento": 14, "angulo": -45, "esmaecer": "dir"}),
        ("listras", {"largura": 420, "altura": 44}),
        ("colchetes", {"caixa": [30, 30, 360, 190], "braco": 36}),
        ("fio", {"pontos": [[20, 20], [200, 20], [200, 110], [400, 110]], "terminais": ["ponto", "seta"]}),
        ("regua", {"comprimento": 420, "passo": 12, "rotulos": {"inicio": 0, "passo": 5}}),
        ("divisoria", {"comprimento": 420}),
        ("grade-pontos", {"largura": 420, "altura": 160, "esmaecer": "dir"}),
        ("circulos", {"raios": [30, 60, 90], "angulo_ini": -60, "angulo_fim": 60}),
        ("setas", {"quantidade": 4}),
        ("estrelas", {"quantidade": 5}),
        ("campo", {"largura": 420}),
        ("campo", {"esporte": "pista", "recorte": "canto", "largura": 300}),
        ("placar", {"cabecalho": f"{nome} · 1ª rodada", "largura": 640, "linhas": [
            {"data": "14.03 · 08h", "mandante": "Equipe Azul", "placar": "2 x 1", "visitante": "Equipe Verde"},
            {"data": "14.03 · 10h", "mandante": "Equipe Branca", "placar": "0 x 0", "visitante": "Equipe Preta"}]}),
        ("fio-borda", {"largura": 420}),
        ("pattern-borda", {"largura": 420, "padrao": "listras"}),
    ]
    lista += [    # acabamento (Frente G)
        ("hachura", {"largura": 420, "altura": 200, "esmaecer": "dir"}),
        ("malha", {"largura": 420, "altura": 200, "perspectiva": [[0.25, 0], [0.75, 0], [1, 1], [0, 1]]}),
        ("aneis", {"largura": 420, "altura": 200, "centro": [0, 1], "esmaecer": "centro"}),
        ("pontos-radiais", {"largura": 420, "altura": 200, "centro": [1, 0]}),
        ("cantoneira", {"largura": 300, "altura": 200, "estilo": "escada"}),
        ("moldura-dupla", {"largura": 300, "altura": 200, "cantos": "chanfro"}),
        ("regua-borda", {"comprimento": 860}),
        ("eco", {"texto_de": "evento", "altura": 150, "opacidades": [1, 0.46, 0.24]}),
        ("eco", {"texto_de": "evento", "altura": 150, "estilo": "contorno-path", "direcao": 45, "opacidades": [1, 0.46, 0.24]}),
        ("texto-curva", {"texto_de": "evento", "raio": 360, "tamanho": 36}),
        ("texto-curva", {"texto_de": "local", "forma": "onda", "tamanho": 28}),
        ("ondas", {"largura": 420, "altura": 200, "defasagem": 20}),
        ("curvas-nivel", {"largura": 420, "altura": 200, "maior_cada": 3}),
        ("fita", {"forma": "dobra", "largura": 420, "altura": 200, "espessura": 48, "texto_de": "local"}),
        ("carimbo", {"texto": f"{nome} · {cidade} ·", "centro_texto": ano, "diametro": 260, "falhas": 0.1}),
        ("carimbo", {"forma": "retangular", "texto": "Edição", "centro_texto": ano, "largura": 320, "altura": 150, "falhas": 0.08}),
        ("numeral-eco", {"texto": ano, "altura": 160}),
        ("campo", {"largura": 420, "perspectiva": [[0.2, 0], [0.8, 0], [1, 1], [0, 1]]}),
    ]
    if tem_logo:
        lista += [
            ("celular", {"imagem": ctx["logo_png"], "largura": 200}),
            ("meio-tom-simbolo", {"largura": 420, "celula": 12, "recorte": recorte}),
            ("meio-tom-simbolo", {"largura": 420, "celula": 14, "modo": "led", "grade_fundo": True, "recorte": recorte}),
            ("pattern-simbolo", {"lado": 200, "recorte": recorte, "area": [600, 400]}),
            ("pattern-simbolo", {"lado": 160, "recorte": recorte, "estilo": "chapado", "arranjo": "alternado", "escala": 0.36, "area": [480, 400], "cor": "apoio"}),
        ]
    return lista


def folha(pasta, receita, fontes_dir, saida, recorte=None):
    ctx = ctx_do_kit(pasta, receita, fontes_dir)
    itens = exemplos_folha(ctx, recorte)
    res = [gerar(t, prm, ctx) for t, prm in itens]
    pal = ctx["paleta"]
    legendas = [f"{t}  {r['w']}x{r['h']}" + (f"  texto: {r['texto'][:60]}" if r["texto"] else "") for (t, _), r in zip(itens, res)]
    medidas = medir_no_chromium([r["svg"] for r in res], ctx["fontes_dir"], png=saida, fundo=pal.get("escuro", "#111111"), legendas=legendas,
                                cor=pal.get("marca"))
    print(f"OK {saida}  {len(res)} grafismos da receita {receita}")
    return res, medidas


def main():
    ap = argparse.ArgumentParser(description="grafismos por código com texto vivo (references/08-sistema-elementos.md)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("ctx"); c.add_argument("pasta"); c.add_argument("--receita"); c.add_argument("--fontes")
    s = sub.add_parser("svg"); s.add_argument("tipo"); s.add_argument("--ctx", required=True); s.add_argument("--params", default="{}"); s.add_argument("--saida")
    f = sub.add_parser("folha"); f.add_argument("pasta"); f.add_argument("--receita"); f.add_argument("--fontes", required=True)
    f.add_argument("--saida", required=True); f.add_argument("--recorte", help="x0,y0,x1,y1 do logo (ex.: só o símbolo)")
    a = ap.parse_args()
    try:
        if a.cmd == "ctx":
            print(json.dumps(ctx_do_kit(a.pasta, a.receita, a.fontes), ensure_ascii=False, indent=1))
        elif a.cmd == "svg":
            r = gerar(a.tipo, json.loads(a.params), json.loads(Path(a.ctx).read_text(encoding="utf-8")))
            if a.saida:
                Path(a.saida).write_text(r["svg"], encoding="utf-8")
                print(json.dumps({k: v for k, v in r.items() if k != "svg"}, ensure_ascii=False))
            else:
                print(json.dumps(r, ensure_ascii=False))
        elif a.cmd == "folha":
            folha(a.pasta, a.receita, a.fontes, a.saida, [float(v) for v in a.recorte.split(",")] if a.recorte else None)
    except ValueError as e:
        print(f"erro: {e}", file=sys.stderr)
        sys.exit(64)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
camadas.py (Frente A): elementos (pattern, constante, herói, apoio) entram no DOM de cada página na camada certa,
na posição que o encaixes.py resolveu sobre o layout medido. Contrato: references/08-sistema-elementos.md.

Fluxo por receita e por formato (horizontal 1920×1080 e vertical 1080×1920), chamado pelo render.py:
  1. render da página SEM elementos e medição no DOM depois do data-fit (JS_PROTEGIDOS): caixas protegidas por LINHA de
     texto (Range.getClientRects), marcas (logo, crédito, etiqueta, fio), blocos de conteúdo, cena, painéis chapados;
  2. planejamento: plano_elementos.planejar (Frente C) quando sistema_elementos declara a receita; sem isso
     (kit antigo, exemplo, receita fora do sistema), o modo manual `_plano_minimo`;
  3. encaixes.resolver por página (ordem constante, pattern, herói, apoio);
  4. preparo do PNG de uso (corte no alfa_bbox, 2x a largura de uso, cache por sha256 + largura);
  5. injeção no DOM e render final; grava saida/plano-elementos-<receita>[-vertical].json com as caixas protegidas do
     render final (o qa_geometria.py lê).

Camadas (z-index em tema/36-elementos.css, que só entra no HTML de kit com elementos):
  sob-veu  logo depois da .full/.cena (o véu pinta por cima e tinge); cena com véu interno (::after da máscara sangria):
           dentro da própria cena, antes do véu
  atras    depois do último véu: sobre o véu, sob o texto, sob a faixa diagonal, sob crédito e documento
  frente   acima do texto, abaixo de .etiqueta, .fio, .logo-canto e do crédito (entra antes do .logo-canto)

Camada de acabamento (mk-2.1, references/10-acabamento.md; tudo só quando o kit declara o campo, o legado sai igual):
  efeito    vence elementos[].opacidade e .blend: opacidade e blend no PRÓPRIO nó; `mascara` vira clip-path vetorial
            (polygon, circle, inset; `clip_mascara`); `esmaecer` só em degraus gravados no alfa (PNG: tratar.py
            alfa-degraus; grafismo: params.esmaecer do gerador), nunca gradiente em mask-image.
  cruza     dois nós do MESMO data URI com clip-path inset acima e abaixo do corte medido (linha_base, cap ou cy do
            título ou do número): a parte de cima na camada atras (sob o texto), a de baixo na frente.
  sombra    contato: tratar.sombra com a luz da família, cache por sha256; item derivado `<id>-sombra` (derivado_de).
  reflexo   piso: tratar.reflexo (altura .35, opacidade .32, achatar .9); item derivado `<id>-reflexo` com o topo na base
            da tinta do pai. Derivados pintam logo antes do pai, na mesma camada.
  textura   papel acabamento sem alfa: uma imagem por área, a 1x do uso em JPEG q80 (tratar.textura); blend padrão
            multiply no papel, screen no escuro, soft-light sobre foto.
"""
import base64, contextlib, hashlib, html as htmlmod, io, json, math, re
from collections import Counter
from pathlib import Path

import composicao, encaixes
from caminhos import ForaDoKit, dentro_do_kit

AQUI = Path(__file__).resolve().parent
PAPEIS = ("pattern", "constante", "heroi", "apoio", "estrutura", "ornamento", "acabamento")
BLENDS = ("normal", "multiply", "screen", "soft-light")
# camada de acabamento (mk-2.1): vocabulário fechado, porque tudo vai para CSS inline (valor fora vira aviso, nunca CSS)
OPACIDADES = (1, 0.72, 0.46, 0.24, 0.12, 0.06)
MASCARAS = ("nenhuma", "diagonal", "chanfro", "circulo", "arco-base", "janela")
TAN_DIAGONAL = math.tan(math.radians(12))     # o único ângulo do kit (35-receitas.css: --diag-dx = 1080 × tan 12°)
REFLEXO = {"altura": 0.35, "opacidade": 0.32, "achatar": 0.9}
# o tratar.sombra desenha no canvas do PNG (largura do objeto): a elipse deslocada contra a luz (12% da largura) e o
# desfoque (18 px) passavam da borda e a sombra saía cortada reta (medido no selo da cota da prova: 17 níveis de degrau
# na borda direita). O render dá margem transparente antes de chamar: 15% da largura + 3 desfoques de cada lado.
MARGEM_SOMBRA = lambda w: int(math.ceil(0.15 * w + 3 * 18))  # noqa: E731
LUZ_FAMILIA = {"esquerda": "esquerda", "direita": "direita", "cima": "cima", "esq": "esquerda", "dir": "direita",
               "topo": "cima"}
OPOSTA = {"esquerda": "direita", "direita": "esquerda", "cima": "cima"}
BLEND_TEXTURA = {"papel": "multiply", "escuro": "screen", "foto": "soft-light", "cor": "soft-light"}
VERTICAL = ["vertical:capa", "vertical:numeros", "vertical:contato"]
VERSAO_USO = 3      # muda quando o preparo do PNG de uso muda: o cache antigo é refeito (3: acabamento da frente)
CORES_USO = 32      # paleta do PNG de uso em traço, meio-tom e chapado
PLANEJADOR_MINIMO = "_plano_minimo (modo manual: kit ou receita sem sistema_elementos)"


def ativo(k):
    """O sistema de elementos liga quando o kit declara `elementos`, `sistema_elementos` ou `composicao` (a composição
    sozinha já desenha: liga por código e, na maquete, asset planejado). Sem isso o render é o de antes."""
    return bool(k.get("elementos")) or bool(k.get("sistema_elementos")) or bool(k.get("composicao"))


# ------------------------------------------------------------------------------------------------- rótulos
def rotulo_variante(p):
    """'capa:c', 'ativo:diagonal', 'cota:b', 'prova'... a chave do encaixes.json."""
    t, v = p["tipo"], p.get("variante") or "a"
    if t == "ativo_topo":
        return "ativo:topo"
    if t == "ativo_painel":
        return {"diagonal": "ativo:diagonal", "sangria": "ativo:sangria"}.get(v, "ativo:painel")
    if t in ("capa", "manifesto", "publico", "divisor", "cota", "contato"):
        return f"{t}:{v}"
    return t


def rotulos_pagina(p):
    """Como o JSON se refere a esta página em `elementos[].paginas` e `pattern_paginas`: tipo, 'ativo', 'ativo:<n>',
    'cota:<nome>' e o rótulo da variante ('cota:b')."""
    r = {p["tipo"], rotulo_variante(p)}
    if p["tipo"] in ("ativo_painel", "ativo_topo"):
        r |= {"ativo", f"ativo:{p.get('n')}"}
    if p["tipo"] == "cota":
        r.add(f"cota:{(p.get('cota') or {}).get('nome')}")
    return r


def _casa(paginas_el, rot):
    if paginas_el in (None, "todas"):
        return paginas_el == "todas"
    if isinstance(paginas_el, str):
        paginas_el = [paginas_el]
    return bool(set(paginas_el) & rot)


# ------------------------------------------------------------------------------------------------- carga
def _sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def alfa_bbox(caminho, limiar=8):
    """Caixa da área visível (alfa > limiar) em px da imagem; None se a imagem não tem alfa útil."""
    from PIL import Image
    import numpy as np
    im = Image.open(caminho)
    if im.mode not in ("RGBA", "LA", "PA"):
        return None, im.size
    a = np.asarray(im.convert("RGBA"))[..., 3]
    ys, xs = np.nonzero(a > limiar)
    if not len(xs):
        return None, im.size
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1), im.size


def sem_alfa(caminho):
    """A imagem é opaca (sem canal alfa ou com alfa 255 em todo pixel)?"""
    from PIL import Image
    import numpy as np
    im = Image.open(caminho)
    if im.mode not in ("RGBA", "LA", "PA") and "transparency" not in im.info:
        return True
    return bool((np.asarray(im.convert("RGBA"))[..., 3] == 255).all())


def carregar(k, pasta, report):
    """elementos[] do JSON com caminho, dimensões, alfa_bbox e sha256. Papel inválido ou arquivo ausente vira aviso."""
    els = {}
    for e in k.get("elementos", []) or []:
        eid, papel = e.get("id"), e.get("papel")
        if papel not in PAPEIS:
            report["avisos"].append(f"elemento {eid}: papel `{papel}` inválido ({', '.join(PAPEIS)})"); continue
        formato = e.get("formato") or ("svg" if not e.get("arquivo") and e.get("params") is not None else "png")
        d = dict(e, formato=formato, papel_plano=encaixes.normalizar_papel(papel))
        if formato == "png":
            try:
                p = dentro_do_kit(pasta, e["arquivo"]) if e.get("arquivo") else None
            except ForaDoKit as erro:
                raise SystemExit(f"elemento {eid}: {erro}. O render recusa: o arquivo iria embutido no PDF")
            if p is None or not p.exists():
                report["avisos"].append(f"elemento {eid}: arquivo não encontrado: {e.get('arquivo')}"); continue
            bbox, (W, H) = alfa_bbox(p)
            tinta = None
            if papel == "acabamento" and sem_alfa(p):
                # textura única (references/10): imagem opaca, uma por área; entra inteira, a 1x, em JPEG
                d["textura"] = True
            if papel == "pattern":
                bbox = None  # tile repetido: cortar quebra a costura
            elif bbox is None and not d.get("textura"):
                report["avisos"].append(f"elemento {eid}: PNG sem alfa útil; entra a imagem inteira")
            else:
                # tinta (alfa >= 128): é ela que a âncora da composição encosta na linha, não a franja semitransparente
                tinta, _ = alfa_bbox(p, limiar=composicao.LIMIAR_TINTA)
            d.update(caminho=p, dims=(W, H), alfa_bbox=bbox, tinta_bbox=tinta, sha256=_sha256(p))
        els[eid] = d
    return els


# ------------------------------------------------------------------------------------------------- zonas da foto
FOCO_FRACAO = 1 / 3     # zona do foco: um terço da foto visível em cada eixo, centrada no ponto (o assunto mora ali)


def chave_foto(src):
    """A mesma impressão digital que o JS mede no src da foto (tamanho + fim do data URI)."""
    return f"{len(src)}:{src[-48:]}" if src else None


def _fracoes(pos):
    """'55% 45%' (object-position do acervo) → (0.55, 0.45); None se não for porcentagem."""
    chaves = {"left": "0%", "center": "50%", "right": "100%", "top": "0%", "bottom": "100%"}
    partes = [chaves.get(p, p) for p in str(pos or "").split()]
    if len(partes) == 1:
        partes.append("50%")
    if len(partes) < 2 or not all(p.endswith("%") for p in partes[:2]):
        return None
    try:
        return float(partes[0][:-1]) / 100.0, float(partes[1][:-1]) / 100.0
    except ValueError:
        return None


def zonas_da_foto(pags, medidas, pasta, avisos):
    """Por página, as zonas protegidas DENTRO das fotos, na página: cada painel que o compor.py pôs na cena
    (`acervo[].paineis` = o JSON do --lote, quads em px da própria imagem) e a zona do `foco` do acervo. A foto do DOM
    acha o item do acervo pela impressão digital do src; o quad e o foco vão à página pelo object-fit + object-position
    medidos (composicao.ponto_da_foto). Zona = caixa do quad cortada na área visível da foto (classe `vendavel`)."""
    por_chave = {}
    for p in pags:
        for c in (p.get("cena"), p.get("mini")):
            if isinstance(c, dict) and c.get("src") and (c.get("paineis") or c.get("foco")):
                por_chave[chave_foto(c["src"])] = c
    lidos, out = {}, []
    for med in medidas:
        zs = []
        al = med.get("alvos") or {}
        for nome in [k for k in al if k == "foto" or (k.startswith("foto:") and k != "foto:1")]:
            f = al[nome]
            img = f.get("img") or {}
            a = por_chave.get(img.get("chave"))
            if not a or not img.get("nat_w"):
                continue
            X, Y, W, H = float(f["x"]), float(f["y"]), float(f["w"]), float(f["h"])

            def caixa(xs, ys):
                x0, y0, x1, y1 = max(X, min(xs)), max(Y, min(ys)), min(X + W, max(xs)), min(Y + H, max(ys))
                return (x0, y0, x1, y1) if x1 - x0 >= 1 and y1 - y0 >= 1 else None

            arq = a.get("paineis")
            if arq:
                if arq not in lidos:
                    try:
                        lidos[arq] = json.loads(dentro_do_kit(pasta, arq).read_text(encoding="utf-8"))
                    except Exception as e:
                        lidos[arq] = []
                        avisos.append(f"acervo `{a.get('id')}`: painéis `{arq}` não lidos ({e}); a foto fica sem zona vendável")
                for i, it in enumerate(lidos[arq]):
                    q = it.get("quad") or []
                    if len(q) != 8:
                        continue
                    pts = [composicao.ponto_da_foto(f, q[j] / img["nat_w"], q[j + 1] / img["nat_h"], exigir_visivel=False)
                           for j in range(0, 8, 2)]
                    c = caixa([p[0] for p in pts], [p[1] for p in pts])
                    if c:
                        zs.append({"classe": "vendavel", "x": round(c[0], 1), "y": round(c[1], 1), "w": round(c[2] - c[0], 1),
                                   "h": round(c[3] - c[1], 1), "quad": [[round(p[0], 1), round(p[1], 1)] for p in pts],
                                   "texto": (it.get("texto") or ("logo" if it.get("logo") else "painel")).replace("|", " "),
                                   "fonte": f"{arq}#{i + 1}", "foto": nome})
            fr = _fracoes(a.get("foco"))
            if fr:
                px, py = composicao.ponto_da_foto(f, fr[0], fr[1], exigir_visivel=False)
                c = caixa([px - W * FOCO_FRACAO / 2, px + W * FOCO_FRACAO / 2], [py - H * FOCO_FRACAO / 2, py + H * FOCO_FRACAO / 2])
                if c:
                    zs.append({"classe": "vendavel", "x": round(c[0], 1), "y": round(c[1], 1), "w": round(c[2] - c[0], 1),
                               "h": round(c[3] - c[1], 1), "texto": "foco da foto", "fonte": f"acervo `{a.get('id')}` foco {a.get('foco')}",
                               "foto": nome})
        out.append(zs)
    return out


# ------------------------------------------------------------------------------------------------- medição no DOM
JS_PROTEGIDOS = r"""
(cfg) => {
  const PROT = [
    ['preco', '.preco, .preco-heroi'],
    ['numero', '.numero, .heroi-num, .num-forma, .fantasma, .graf-val, .lista-num .n'],
    ['micro', '.micro, .estado, .qtd, .label, .graf-eixo, .graf-rots, .graf-leg, .faixa-txt, .lista-num .e, .quem'],
    ['titulo', 'h1, h2, .display, .titulo, .titulo-m, .heroi, .citacao, .sub-caixa, .assina, .pill, .nome'],
  ];
  const CONTEUDO = '.card, .caixa, .caixa-num, .direitos, .direitos-2col, .invest, .grafico, .barras, .trilho-icones, .lista-num, .regioes, .selo, .miniatura, .objeto, .borda-diag, .faixa-diag, .pill, .preco-heroi';
  const alfa = (c) => { const m = (c || '').match(/rgba?\(([^)]+)\)/); if (!m) return 0; const p = m[1].split(',').map(s => parseFloat(s)); return p.length > 3 ? p[3] : 1; };
  const r1 = (v) => Math.round(v * 10) / 10;
  const transformado = (el, pg) => { for (let n = el; n && n !== pg; n = n.parentElement) { const t = getComputedStyle(n).transform; if (t && t !== 'none') return n; } return null; };
  // geometria de texto/caixa sob transform (faixa diagonal girada): mede sem o transform e mapeia pedaços de 48 px
  // pela matriz; cada pedaço vira uma caixa alinhada aos eixos, bem mais justa que a caixa da linha girada inteira
  const girada = (anc, medir) => {
    const cs = getComputedStyle(anc); const M = new DOMMatrix(cs.transform);
    const o = cs.transformOrigin.split(' ').map(parseFloat);
    const antes = anc.style.getPropertyValue('transform'), prio = anc.style.getPropertyPriority('transform');
    anc.style.setProperty('transform', 'none', 'important');
    const b = anc.getBoundingClientRect(); const ox = b.left + o[0], oy = b.top + o[1];
    const rs = medir();
    if (antes) anc.style.setProperty('transform', antes, prio); else anc.style.removeProperty('transform');
    const out = [];
    for (const r of rs) {
      if (r.width < 1 || r.height < 1) continue;
      const nx = Math.max(1, Math.ceil(r.width / 48)), ny = Math.max(1, Math.ceil(r.height / 48));
      for (let i = 0; i < nx; i++) for (let j = 0; j < ny; j++) {
        const x0 = r.left + r.width * i / nx, x1 = r.left + r.width * (i + 1) / nx, y0 = r.top + r.height * j / ny, y1 = r.top + r.height * (j + 1) / ny;
        const pts = [[x0, y0], [x1, y0], [x0, y1], [x1, y1]].map(([px, py]) => { const q = M.transformPoint(new DOMPoint(px - ox, py - oy)); return [q.x + ox, q.y + oy]; });
        const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]); const l = Math.min(...xs), t = Math.min(...ys);
        out.push({ left: l, top: t, width: Math.max(...xs) - l, height: Math.max(...ys) - t });
      }
    }
    return out;
  };
  const out = [];
  Array.from(document.querySelectorAll('.pagina')).forEach((pg, idx) => {
    const P = pg.getBoundingClientRect();
    const rel = (r) => ({ x: r1(r.left - P.left), y: r1(r.top - P.top), w: r1(r.width), h: r1(r.height) });
    const caixas = (el) => { const anc = transformado(el, pg); return anc ? girada(anc, () => [el.getBoundingClientRect()]) : [el.getBoundingClientRect()]; };
    const prot = [];
    // texto por LINHA: um retângulo por linha de cada bloco (não o bloco inteiro)
    const grupos = new Map();
    const tw = document.createTreeWalker(pg, NodeFilter.SHOW_TEXT);
    for (let tn = tw.nextNode(); tn; tn = tw.nextNode()) {
      if (!tn.textContent.trim()) continue;
      const el = tn.parentElement; if (!el || el.closest('[data-elemento], .etiqueta, .credito')) continue;
      const cs = getComputedStyle(el);
      if (cs.visibility !== 'visible' || cs.display === 'none' || parseFloat(cs.opacity) === 0) continue;
      let cls = 'corpo'; for (const [c, s] of PROT) { if (el.closest(s)) { cls = c; break; } }
      let bloco = el; while (bloco !== pg && getComputedStyle(bloco).display === 'inline') bloco = bloco.parentElement;
      const rng = document.createRange(); rng.selectNodeContents(tn);
      const anc = transformado(el, pg);
      const rs = anc ? girada(anc, () => Array.from(rng.getClientRects())) : Array.from(rng.getClientRects());
      if (!grupos.has(bloco)) grupos.set(bloco, []);
      for (const r of rs) if (r.width >= 1 && r.height >= 1) grupos.get(bloco).push(Object.assign({ cls, giro: !!anc, texto: tn.textContent.replace(/\s+/g, ' ').trim().slice(0, 40) }, rel(r)));
    }
    for (const rs of grupos.values()) {
      const linhas = [];
      for (const r of rs.filter(r => !r.giro).sort((a, b) => a.y - b.y || a.x - b.x)) {
        const l = linhas.find(l => l.cls === r.cls && Math.min(l.y + l.h, r.y + r.h) - Math.max(l.y, r.y) > 0.5 * Math.min(l.h, r.h));
        if (l) { const x0 = Math.min(l.x, r.x), y0 = Math.min(l.y, r.y), x1 = Math.max(l.x + l.w, r.x + r.w), y1 = Math.max(l.y + l.h, r.y + r.h); Object.assign(l, { x: r1(x0), y: r1(y0), w: r1(x1 - x0), h: r1(y1 - y0) }); if (l.texto.length < 40) l.texto = (l.texto + ' ' + r.texto).slice(0, 40); }
        else linhas.push(Object.assign({}, r));
      }
      for (const l of linhas.concat(rs.filter(r => r.giro))) prot.push({ classe: l.cls, x: l.x, y: l.y, w: l.w, h: l.h, texto: l.texto });
    }
    const add = (classe, el, texto) => { for (const r of caixas(el)) if (r.width >= 1 && r.height >= 1) prot.push(Object.assign({ classe }, rel(r), { texto: (texto || '').replace(/\s+/g, ' ').trim().slice(0, 40) })); };
    pg.querySelectorAll('.etiqueta').forEach(el => add('etiqueta', el, el.innerText));
    pg.querySelectorAll('.credito').forEach(el => add('credito', el, el.innerText));
    pg.querySelectorAll('.fio, .fio .ponto').forEach(el => add('fio', el, 'fio'));
    pg.querySelectorAll('.logo-canto, .lettering, .lettering-central, .mural-logos, .miniatura').forEach(el => add('logo', el, el.classList[0]));
    pg.querySelectorAll('img').forEach(img => { if (img.closest('.full, .cena, .miniatura, .objeto, .mural-logos, [data-elemento]') || img.matches('.logo-canto, .lettering, .lettering-central')) return; add('logo', img, 'logo'); });
    const conteudo = [];
    pg.querySelectorAll(CONTEUDO).forEach(el => { if (el.closest('[data-elemento]')) return; for (const r of caixas(el)) if (r.width >= 2 && r.height >= 2) conteudo.push(rel(r)); });
    const opacos = [];
    pg.querySelectorAll(':scope > .painel, :scope > .mural-logos').forEach(el => { if (alfa(getComputedStyle(el).backgroundColor) >= 0.5) opacos.push(rel(el.getBoundingClientRect())); });
    const cenas = []; let cena = null;
    pg.querySelectorAll(':scope > .full, :scope > .cena').forEach(el => {
      const r = el.getBoundingClientRect();
      const x0 = Math.max(0, r.left - P.left), y0 = Math.max(0, r.top - P.top), x1 = Math.min(cfg.w, r.right - P.left), y1 = Math.min(cfg.h, r.bottom - P.top);
      const ap = getComputedStyle(el, '::after');
      const c = { x: r1(r.left - P.left), y: r1(r.top - P.top), w: r1(r.width), h: r1(r.height), veu_interno: ap.content !== 'none' && ap.content !== 'normal' && ap.backgroundImage !== 'none' };
      cenas.push(c);
      if (x1 - x0 >= 64 && y1 - y0 >= 64 && (!cena || (x1 - x0) * (y1 - y0) > cena.w * cena.h)) cena = { x: r1(x0), y: r1(y0), w: r1(x1 - x0), h: r1(y1 - y0) };
    });
    const blocos = {};
    (cfg.seletores || []).forEach(s => { const el = pg.querySelector(s); if (el) { const r = el.getBoundingClientRect(); if (r.width > 1) blocos[s] = rel(r); } });
    const elementos = Array.from(pg.querySelectorAll('[data-elemento]')).map(el => Object.assign({ id: el.dataset.elemento, papel: el.dataset.papel, camada: el.dataset.camada }, rel(el.getBoundingClientRect())));
    // ALVOS da composição (composicao.py): o que cada caixa É. Título, número, preço, corpo e micro vêm com as linhas,
    // e cada linha com a linha de base e o topo da maiúscula (cap), medidos pela métrica da fonte usada; a foto vem
    // com o tamanho natural e o object-position (para achar um ponto da foto na página); margem e colunas do tema.
    const alvos = {};
    const tcs = getComputedStyle(pg);
    const margem = parseFloat(tcs.getPropertyValue('--margem')) || 96, calha = parseFloat(tcs.getPropertyValue('--calha')) || 24, col = parseFloat(tcs.getPropertyValue('--col')) || 128;
    alvos.pagina = { x: 0, y: 0, w: cfg.w, h: cfg.h };
    alvos.margem = { x: margem, y: margem, w: cfg.w - 2 * margem, h: cfg.h - 2 * margem };
    alvos.colunas = []; for (let x = margem; x + col <= cfg.w - margem + 0.5; x += col + calha) alvos.colunas.push({ x: r1(x), w: col });
    const cv = document.createElement('canvas').getContext('2d');
    const metrica = (el) => { const s = getComputedStyle(el); cv.font = `${s.fontStyle} ${s.fontWeight} ${s.fontSize} ${s.fontFamily}`; const m = cv.measureText('H'); return { asc: m.fontBoundingBoxAscent, cap: m.actualBoundingBoxAscent }; };
    const linhasDe = (raiz) => {
      const frs = [];
      const w2 = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT);
      for (let tn = w2.nextNode(); tn; tn = w2.nextNode()) {
        if (!tn.textContent.trim() || transformado(tn.parentElement, pg)) continue;
        const mt = metrica(tn.parentElement); const rg = document.createRange(); rg.selectNodeContents(tn);
        for (const r of rg.getClientRects()) if (r.width >= 1 && r.height >= 1) frs.push({ l: r.left - P.left, t: r.top - P.top, w: r.width, h: r.height, base: r.top - P.top + mt.asc, cap: r.top - P.top + mt.asc - mt.cap, txt: tn.textContent.replace(/\s+/g, ' ').trim() });
      }
      frs.sort((a, b) => a.t - b.t || a.l - b.l);
      const ls = [];
      for (const f of frs) {
        const l = ls.find(l => Math.min(l.t + l.h, f.t + f.h) - Math.max(l.t, f.t) > 0.5 * Math.min(l.h, f.h));
        if (l) { const x1 = Math.max(l.l + l.w, f.l + f.w), y1 = Math.max(l.t + l.h, f.t + f.h); l.l = Math.min(l.l, f.l); l.t = Math.min(l.t, f.t); l.w = x1 - l.l; l.h = y1 - l.t; l.base = Math.max(l.base, f.base); l.cap = Math.min(l.cap, f.cap); if (l.txt.length < 40) l.txt = (l.txt + ' ' + f.txt).slice(0, 40); }
        else ls.push(Object.assign({}, f));
      }
      return ls.map(l => ({ x: r1(l.l), y: r1(l.t), w: r1(l.w), h: r1(l.h), linha_base: r1(l.base), cap: r1(l.cap), texto: l.txt.slice(0, 40) }));
    };
    const poe = (nome, a) => { if (!alvos[nome]) { alvos[nome] = a; alvos[nome + ':1'] = a; return; } let i = 2; while (alvos[`${nome}:${i}`]) i++; alvos[`${nome}:${i}`] = a; };
    // blocos de lista: a caixa de cada item vai junto (`itens`), para a liga `separa` pôr um fio entre vizinhos
    const ITENS = { 'lista-num': 'li', 'direitos': 'li', 'direitos-2col': 'li', 'inv-colunas': '.inv-item', 'cards': '.card', 'caixas4': '.caixa-num' };
    const alvoDe = (nome, el, comTexto) => {
      if (el.closest('[data-elemento]')) return;
      const s = getComputedStyle(el); if (s.display === 'none' || s.visibility !== 'visible') return;
      const rs = caixas(el).filter(r => r.width >= 1 && r.height >= 1); if (!rs.length) return;
      const x0 = Math.min(...rs.map(r => r.left)), y0 = Math.min(...rs.map(r => r.top)), x1 = Math.max(...rs.map(r => r.left + r.width)), y1 = Math.max(...rs.map(r => r.top + r.height));
      const a = rel({ left: x0, top: y0, width: x1 - x0, height: y1 - y0 });
      if (comTexto) { const ls = linhasDe(el); if (ls.length) { a.linhas = ls; a.linha_base = ls[ls.length - 1].linha_base; a.cap = ls[0].cap; } }
      // camada de acabamento (cfg.textos): o texto inteiro do alvo, para o grafismo de texto_de titulo (eco) da página
      if (comTexto && cfg.textos) a.texto = (el.innerText || '').replace(/\s+/g, ' ').trim();
      if (ITENS[nome]) a.itens = Array.from(el.querySelectorAll(ITENS[nome])).filter(i => getComputedStyle(i).display !== 'none').map(i => rel(i.getBoundingClientRect())).filter(r => r.w >= 1 && r.h >= 1);
      poe(nome, a);
    };
    for (const [nome, sel] of [['titulo', 'h1, h2'], ['subtitulo', '.sub-caixa'], ['numero', '.numero, .heroi-num, .num-forma, .fantasma, .lista-num .n'], ['preco', '.preco'], ['corpo', 'p.corpo, p.corpo-g, p.corpo-m, .citacao'], ['micro', '.micro']])
      pg.querySelectorAll(sel).forEach(el => alvoDe(nome, el, true));
    // `chave` = impressão digital do src (tamanho + fim do data URI): o camadas.py acha por ela o item do acervo da foto
    // (painéis do compor.py e foco), sem depender do tamanho da imagem, que se repete entre fotos tratadas
    const chave = (s) => s ? s.length + ':' + s.slice(-48) : null;
    const fotos = Array.from(pg.querySelectorAll(':scope > .full, :scope > .cena')).map(el => { const r = el.getBoundingClientRect(); const img = el.querySelector('img'); const is = img ? getComputedStyle(img) : null; return { a: Object.assign(rel(r), img ? { img: { nat_w: img.naturalWidth, nat_h: img.naturalHeight, fit: is.objectFit, pos: is.objectPosition, chave: chave(img.getAttribute('src')) } } : {}), area: r.width * r.height }; }).sort((a, b) => b.area - a.area);
    fotos.forEach(f => poe('foto', f.a));
    pg.querySelectorAll(':scope > .painel').forEach(el => alvoDe('painel', el, false));
    pg.querySelectorAll('.logo-canto, .lettering, .lettering-central').forEach(el => alvoDe('logo', el, false));
    for (const c of ['traco', 'caixa', 'card', 'cards', 'caixa-num', 'caixas4', 'direitos', 'direitos-2col', 'invest', 'grafico', 'barras', 'trilho-icones', 'lista-num', 'regioes', 'inv-colunas', 'cota-cab', 'contato-linha', 'mural-logos', 'miniatura', 'objeto', 'faixa-diag', 'borda-diag', 'selo', 'pill', 'etiqueta', 'credito', 'fio'])
      pg.querySelectorAll('.' + c).forEach(el => alvoDe(c, el, false));
    // grão do tema (.pagina::after): o PNG de uso de um elemento na camada frente recebe o mesmo grão, na mesma
    // intensidade (o elemento fica acima do ::after e, sem isso, parece colado)
    const ga = getComputedStyle(pg, '::after');
    const grao = (ga.content !== 'none' && ga.content !== 'normal' && /url\(/.test(ga.backgroundImage)) ? { opacidade: parseFloat(ga.opacity), blend: ga.mixBlendMode, tamanho: ga.backgroundSize } : null;
    out.push({ pagina: idx + 1, w: cfg.w, h: cfg.h, protegidos: prot, conteudo, opacos, cena, cenas, blocos, elementos, alvos, grao });
  });
  return out;
}
"""


# ------------------------------------------------------------------------------------------------- grafismos (svg)
def cor_pela_pagina(svg, marca):
    """O grafismos.gerar pinta com o hex da paleta (fill/stroke). No kit, a cor da marca tem de vir da página: o acento
    troca em fundo papel e cor, e o microtexto de borda vai no tom suave (36-elementos.css). Troca o hex da marca por
    currentColor; as outras cores da paleta ficam como vieram. Sem isso o CSS só mudava a caixa que o QA de cor lê,
    e a página continuava com o dourado (falha achada na integração de 09/10/2026)."""
    if not marca:
        return svg
    return re.sub(r'\b(fill|stroke)="' + re.escape(marca) + '"', r'\1="currentColor"', svg, flags=re.I)


# parâmetros de grafismo que são arquivo: `imagem` (a captura do celular) e `png` (o logo ou símbolo dos padrões e do selo)
ARQUIVOS_DE_GRAFISMO = ("imagem", "png")


def gerador_grafismos():
    """grafismos.gerar (Frente B). Sem fallback: se o módulo quebrar, o render quebra junto e diz por quê."""
    import grafismos
    return grafismos.gerar, "grafismos.gerar"


def _ids_unicos(svg, sufixo):
    """O mesmo svg entra em várias páginas do mesmo documento: id repetido é HTML inválido. Sufixa ids e referências."""
    ids = re.findall(r'\bid="([^"]+)"', svg)
    for i in ids:
        novo = f"{i}-{sufixo}"
        svg = re.sub(rf'\bid="{re.escape(i)}"', f'id="{novo}"', svg)
        svg = re.sub(rf'(href="#){re.escape(i)}"', rf'\g<1>{novo}"', svg)
        svg = re.sub(rf'url\(#{re.escape(i)}\)', f"url(#{novo})", svg)
    if 'class="' in svg.split(">", 1)[0]:
        if "grafismo" not in svg.split(">", 1)[0]:
            svg = svg.replace('class="', 'class="grafismo ', 1)
    else:
        svg = svg.replace("<svg", '<svg class="grafismo"', 1)
    return svg


def _fmt_data(iso):
    try:
        a, m, d = str(iso).split("-")
        return f"{d}.{m}.{a}"
    except Exception:
        return str(iso or "")


def texto_constante(c, k):
    """De onde vem o texto do microtexto/selo (sistema_elementos.constantes[].texto_de)."""
    ev = k.get("evento") or {}
    de = c.get("texto_de")
    if c.get("texto") and de in (None, "personalizado"):
        return c["texto"]
    if de == "evento":
        return ev.get("nome", "")
    if de == "tese":
        return (k.get("tese") or {}).get("frase", "")
    if de == "local":
        return "/".join(x for x in (ev.get("cidade"), ev.get("uf")) if x)
    if de == "data":
        return _fmt_data(ev.get("data_inicio"))
    return c.get("texto") or ""


# ------------------------------------------------------------------------------------------------- planejamento
def constantes_com_id(sistema):
    """[(id, constante)] de sistema_elementos.constantes: id `constante-<tipo>`; a segunda do mesmo tipo vira
    `constante-<tipo>-2` (convenção de id que o planejador da Frente C precisa usar para o render achar o grafismo)."""
    out, vistos = [], Counter()
    for c in (sistema or {}).get("constantes") or []:
        t = c.get("tipo")
        if not t:
            continue
        vistos[t] += 1
        out.append((f"constante-{t}" + (f"-{vistos[t]}" if vistos[t] > 1 else ""), c))
    return out


def _plano_minimo(sistema, elementos, receita_id, paginas, catalogo, receita=None):
    """Modo manual, para kit ou receita que o sistema_elementos não declara (kit antigo, exemplo receitas-teste);
    receita declarada usa o plano_elementos.planejar da Frente C. Determinístico.
    - ajuste manual (`paginas` no elemento) vale como antes; pattern pela regra antiga (receita.pattern + pattern_paginas);
    - com sistema_elementos: pattern da receita, constantes (menos grão, que já é do tema) e herói da família da receita
      por `encaixes_preferidos`, sem repetir em página seguida e no máximo 3 usos por receita; prova não tem herói."""
    sis = sistema or {}
    rcfg = (sis.get("receitas") or {}).get(receita_id) or {}
    familia = rcfg.get("familia")
    els = {e["id"]: e for e in elementos}
    norm = encaixes.normalizar_papel
    pid = rcfg.get("pattern") if "pattern" in rcfg else (receita or {}).get("pattern")
    alvo_pattern = None
    if pid and pid in els and els[pid].get("papel") == "pattern":
        alvo_pattern = (receita or {}).get("pattern_paginas") or els[pid].get("paginas")
        if not alvo_pattern and sistema:
            alvo_pattern = "catalogo"
    herois = [e for e in elementos if norm(e.get("papel")) == "heroi" and not e.get("paginas")
              and (not familia or e.get("familia") == familia)] if sistema else []
    usos, anterior, ptr = Counter(), None, 0
    out = []
    for pg in paginas:
        rot, tipo, rots = pg["rotulo"], pg["tipo"], pg["_rotulos"]
        encs = catalogo.get(rot) or []
        at = []
        # constantes do sistema (texto vivo por grafismo)
        for cid, c in constantes_com_id(sis):
            if c.get("tipo") == "grao":
                continue
            exceto = set(c.get("exceto") or [])
            if exceto & (rots | {tipo}):
                continue
            at.append({"id": cid, "papel": "constante",
                       "encaixes_preferidos": [c["encaixe"]] if c.get("encaixe") else [], "camada": None})
        # pattern
        if pid and alvo_pattern:
            if alvo_pattern == "catalogo":
                entra = any("pattern" in e.get("papeis", []) for e in encs)
            else:
                entra = _casa(alvo_pattern, rots)
            if entra:
                at.append({"id": pid, "papel": "pattern", "encaixes_preferidos": els[pid].get("encaixes_preferidos") or [],
                           "camada": els[pid].get("camada")})
        elif not receita and not sistema:
            p0 = next((e for e in elementos if e.get("papel") == "pattern" and _casa(e.get("paginas"), rots)), None)
            if p0:
                at.append({"id": p0["id"], "papel": "pattern", "encaixes_preferidos": [], "camada": p0.get("camada")})
        # ajuste manual: elementos com `paginas` que casam com a página
        heroi_manual = None
        for e in elementos:
            if e.get("papel") == "pattern" or not _casa(e.get("paginas"), rots):
                continue
            at.append({"id": e["id"], "papel": norm(e.get("papel")), "encaixes_preferidos": e.get("encaixes_preferidos") or [],
                       "camada": e.get("camada")})
            if norm(e.get("papel")) == "heroi":
                heroi_manual = e["id"]
        # herói automático
        ids_heroi = {e["id"] for e in encs if "heroi" in e.get("papeis", [])}
        if heroi_manual:
            anterior = heroi_manual
        elif ids_heroi and herois:
            escolhido = None
            for k in range(len(herois)):
                e = herois[(ptr + k) % len(herois)]
                prefs = e.get("encaixes_preferidos") or []
                if e["id"] == anterior or usos[e["id"]] >= 3 or (prefs and not set(prefs) & ids_heroi):
                    continue
                escolhido = e; ptr = (ptr + k + 1) % len(herois); break
            if escolhido:
                at.append({"id": escolhido["id"], "papel": "heroi", "encaixes_preferidos": escolhido.get("encaixes_preferidos") or [],
                           "camada": escolhido.get("camada")})
                usos[escolhido["id"]] += 1
            anterior = escolhido["id"] if escolhido else None
        else:
            anterior = None
        out.append({"n": pg["n"], "atribuidos": at})
    return out


def contrato_composicao(composicao_kit, p):
    """Os dois campos da página composta que o plano_elementos.planejar lê (references/08, Frente C): `composicao`
    (a composição da página traz `elementos`, a mesma condição em que o render troca o plano pelos dela) e
    `herois_composicao` (os ids que ela põe de herói, sem os grafismos declarados só na página). Sem eles o herói da
    composição não conta nos 3 usos nem na regra de vizinho, e a vertical perde o herói da página composta."""
    _, ent, _, _ = composicao.entrada_da_pagina(composicao_kit, p.get("_rotulos") or set(), p["rotulo"], p["tipo"], "horizontal")
    if not ent or "elementos" not in ent:
        return {}
    return {"composicao": True,
            "herois_composicao": [e["id"] for e in ent["elementos"] if e.get("papel") == "heroi" and not e.get("grafismo")]}


def planejar(sistema, elementos, receita_id, paginas, catalogo, receita=None, composicao_kit=None):
    """sistema_elementos que declara a receita: plano_elementos.planejar (Frente C). Sem isso (kit antigo, exemplo,
    receita fora do sistema): o modo manual `_plano_minimo`. A Frente C recebe também `rotulos` (todos os nomes da
    página, como cota:Naming), senão o `paginas` manual de um elemento não acha a página, e os campos da página
    composta (`contrato_composicao`). O grão é constante do tema (.pagina::after em toda página): sai do plano aqui
    para não virar grafismo inexistente."""
    if sistema and receita_id in (sistema.get("receitas") or {}):
        import plano_elementos
        contrato = [{"n": p["n"], "rotulo": p["rotulo"], "tipo": p["tipo"], "rotulos": sorted(p.get("_rotulos") or []),
                     **contrato_composicao(composicao_kit, p)}
                    for p in paginas]
        plano = plano_elementos.planejar(sistema, elementos, receita_id, contrato, catalogo, None)
        for pg in plano:
            pg["atribuidos"] = [a for a in pg["atribuidos"] if not (a.get("papel") == "constante" and a.get("tipo") == "grao")]
        return plano, "plano_elementos.planejar"
    return _plano_minimo(sistema, elementos, receita_id, paginas, catalogo, receita), PLANEJADOR_MINIMO


# ------------------------------------------------------------------------------------------------- preparo do PNG
GRAO_TEMA = AQUI / "assets" / "grao.png"      # o mesmo tile que o render.py embute em --grao (.pagina::after)


def _misturar_blend(cb, cs, blend):
    """Blend do CSS (W3C Compositing) entre o fundo cb (o elemento) e a fonte cs (o grão), arrays em 0..1."""
    import numpy as np
    if blend == "multiply":
        return cb * cs
    if blend == "screen":
        return cb + cs - cb * cs
    if blend == "overlay":
        return np.where(cb <= 0.5, 2 * cb * cs, 1 - 2 * (1 - cb) * (1 - cs))
    if blend == "soft-light":
        d = np.where(cb <= 0.25, ((16 * cb - 12) * cb + 4) * cb, np.sqrt(cb))
        return np.where(cs <= 0.5, cb - (1 - 2 * cs) * cb * (1 - cb), cb + (2 * cs - 1) * (d - cb))
    return cs + 0 * cb


def chave_acabamento(acab):
    """8 hex do acabamento (entra no nome do PNG de uso): grão, tingir e temperatura diferentes = arquivos diferentes.
    Só o CONTEÚDO entra na conta, nunca onde o arquivo mora: o grão vale pelo sha256 (o caminho do tile, que é o da pasta
    do pipeline, sai) e a referência da temperatura pelo sha256 do arquivo. Antes o caminho absoluto entrava e o mesmo kit
    dava `acabamento` e `uso` diferentes conforme a pasta do pipeline (o congelado do golden x o vivo), com os mesmos
    pixels (achado do golden conferir, 12/10/2026)."""
    if not acab:
        return None
    conta = json.loads(json.dumps(acab, ensure_ascii=False, default=str))
    if isinstance(conta.get("grao"), dict):
        conta["grao"].pop("arquivo", None)
    tp = conta.get("temperatura")
    if isinstance(tp, dict) and tp.get("referencia"):
        ref = Path(tp["referencia"])
        tp["referencia"] = _sha256(ref)[:12] if ref.exists() else ref.name
    return hashlib.sha256(json.dumps(conta, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:8]


def acabar(im, acab, fator=2.0):
    """O acabamento da página no PNG (raster, nunca filtro CSS, que rasteriza o PDF): o tingir da receita (a mesma conta
    do tratar.tingir: duotone por LUT), a temperatura (a do tratar.igualar: a*b* da cena-referência, só no RGB) e o grão
    do tema no blend e na opacidade do .pagina::after, com o tile na escala da página (`fator` = px do PNG por px da
    página). Só o RGB muda; o alfa fica como estava."""
    import numpy as np
    from PIL import Image
    arr = np.asarray(im.convert("RGBA")).astype(np.float64) / 255.0
    rgb, alfa = arr[..., :3], arr[..., 3]
    t = acab.get("tingir")
    if t and t.get("cor"):
        h = t["cor"].lstrip("#"); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        forca, preto = float(t.get("forca", 0.7)), float(t.get("preto", 0.04))
        escura = np.array([r * 0.18, g * 0.12, b * 0.16]) / 255.0
        clara = np.array([min(255, r * 0.55 + 115), min(255, g * 0.55 + 115), min(255, b * 0.55 + 115)]) / 255.0
        L = rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114
        L = np.clip((L - preto) / (1 - preto), 0, 1)[..., None]
        rgb = rgb * (1 - forca) + (escura * (1 - L) + clara * L) * forca
    tp = acab.get("temperatura")
    if tp and tp.get("referencia") and Path(tp["referencia"]).exists():
        forca = float(tp.get("forca", 0.4))
        so = alfa > 0.5
        if so.any():
            lab = np.asarray(Image.fromarray(np.round(np.clip(rgb, 0, 1) * 255).astype(np.uint8), "RGB").convert("LAB"), dtype=float)
            ref = np.asarray(Image.open(tp["referencia"]).convert("RGB").convert("LAB"), dtype=float)
            for c in (1, 2):   # a* e b*: temperatura e tom, sem mexer na luminância
                lab[..., c] = lab[..., c] + (ref[..., c].mean() - lab[..., c][so].mean()) * forca
            sa, sb = lab[..., 0][so].std() or 1, ref[..., 0].std() or 1
            ma = lab[..., 0][so].mean()
            lab[..., 0] = (lab[..., 0] - ma) * (1 + (sb / sa - 1) * forca * 0.5) + ma
            rgb = np.asarray(Image.fromarray(np.clip(lab, 0, 255).astype(np.uint8), "LAB").convert("RGB"), dtype=float) / 255.0
    gr = acab.get("grao")
    if gr and Path(gr.get("arquivo") or "").exists():
        lado = max(8, int(round(float(gr.get("tile") or 512) * fator)))
        tile = np.asarray(Image.open(gr["arquivo"]).convert("L").resize((lado, lado), Image.BILINEAR), dtype=float) / 255.0
        H, W = rgb.shape[:2]
        cs = np.tile(tile, (math.ceil(H / lado), math.ceil(W / lado)))[:H, :W][..., None]
        b = _misturar_blend(np.clip(rgb, 0, 1), cs, gr.get("blend") or "soft-light")
        rgb = rgb + (b - rgb) * float(gr.get("opacidade", 0.5))
    out = np.dstack([np.clip(rgb, 0, 1), alfa]) * 255.0
    return Image.fromarray(np.round(out).astype(np.uint8), "RGBA")


def preparar_uso(el, largura_uso, cache_dir, pasta, avisos, acabamento=None):
    """PNG de uso em saida/cache-elementos/<id>@<w>.png: cortado no alfa_bbox e reduzido a 2x a largura de uso
    (múltiplo de 16 px). Cache por sha256 da origem + largura: o mesmo elemento em várias páginas usa o mesmo arquivo
    (o mesmo data URI, que o PDF embute uma vez só). Pattern não é cortado (cortar o tile quebra a costura).
    Elemento de cor chapada (variantes -traco e -chapado do padrao.py) sai só com o alfa (RGB preto) e a cor vai à parte:
    o render aplica o PNG como máscara sobre a cor. O PDF guarda o RGB do jeito que o Skia reconstrói (despré-multiplicado,
    com o transparente preenchido pela média dos vizinhos), e um traço fino em cor chapada virava 450 KB de ruído; preto
    fica exato e custa 2 KB (medido no tile da Sprint: 706 KB → 258 KB, mesmo resultado no PDF rasterizado).
    `acabamento` (só camada frente, que fica ACIMA do grão e do véu e por isso parecia colada): o grão do tema e o
    tingir/temperatura da receita, aplicados no raster por `acabar` antes da redução de cores; o PNG ganha o sufixo
    -<chave do acabamento>. Elemento de cor chapada continua máscara sem acabamento (a cor é do CSS, não do PNG).
    Devolve (caminho relativo à pasta do kit, caminho absoluto, cor chapada '#RRGGBB' ou None)."""
    from PIL import Image
    cache_dir.mkdir(parents=True, exist_ok=True)
    if el.get("textura"):
        return _preparar_textura(el, largura_uso, cache_dir, pasta)
    bbox = el.get("alfa_bbox")
    W0, H0 = el["dims"]
    util = (bbox[2] - bbox[0]) if bbox else W0
    alvo = int(math.ceil(2 * largura_uso / 16.0) * 16)
    if util < 2 * largura_uso - 1:
        avisos.append(f"elemento {el['id']}: {util} px úteis para {largura_uso:.0f} px de uso (abaixo de 2x)")
    alvo = min(alvo, util)
    chave_ac = chave_acabamento(acabamento)
    nome = f"{el['id']}@{alvo}" + (f"-{chave_ac}" if chave_ac else "") + ".png"
    indice_p = cache_dir / "indice.json"
    try:
        indice = json.loads(indice_p.read_text(encoding="utf-8"))
    except Exception:
        indice = {}
    destino = cache_dir / nome
    reg = indice.get(nome) or {}
    if not (destino.exists() and reg.get("sha256") == el["sha256"] and reg.get("bbox") == (list(bbox) if bbox else None)
            and reg.get("versao") == VERSAO_USO and reg.get("acabamento") == chave_ac):
        import numpy as np
        im = Image.open(el["caminho"]).convert("RGBA")
        if bbox:
            im = im.crop(bbox)
        rgb = np.asarray(im)[..., :3]
        cor = "#%02X%02X%02X" % tuple(int(c) for c in rgb[0, 0]) if (rgb == rgb[0, 0]).all() else None
        novo = (alvo, max(1, round(im.height * alvo / im.width))) if im.width > alvo else im.size
        if cor:
            # cor chapada: só o alfa importa; RGB preto (exato no PDF) e a cor entra no CSS
            im = Image.merge("RGBA", (*Image.new("RGB", novo, (0, 0, 0)).split(), im.getchannel("A").resize(novo, Image.LANCZOS)))
        elif novo != im.size:
            # foto (objeto): pré-multiplicado, sem halo escuro na borda transparente
            im = im.convert("RGBa").resize(novo, Image.LANCZOS).convert("RGBA")
        cores = None
        if not cor:
            import familia
            meio = familia.descritores(np.asarray(im)).get("meio")      # medido antes do grão, que mexe nas cores
            if acabamento:
                im = acabar(im, acabamento, im.width / float(largura_uso))
            if meio in ("traco", "meio-tom", "chapado"):
                # pouca tinta (traço, meio-tom, chapado): 32 cores não se veem (ΔE médio 0,3 a 3,4 nos elementos da
                # Sprint) e o Flate do PDF cai até 86% (adesivo de meio-tom: 2,2 MB para 0,3 MB). Foto nunca.
                im = im.quantize(colors=CORES_USO, method=Image.Quantize.FASTOCTREE).convert("RGBA"); cores = CORES_USO
        im.save(destino, optimize=True)
        reg = indice[nome] = {"sha256": el["sha256"], "bbox": list(bbox) if bbox else None, "largura": alvo, "cor": cor,
                              "cores": cores, "versao": VERSAO_USO, "sha256_uso": _sha256(destino), "acabamento": chave_ac}
        indice_p.write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        rel = destino.relative_to(pasta).as_posix()
    except ValueError:
        rel = str(destino)
    return rel, destino, reg.get("cor")


def _tratar(nome, *args, **kw):
    """Chama uma função do tratar.py (a mesma do comando `tratar.py <nome>`) sem o "OK" dela no log do render.
    Devolve None ou a mensagem do erro (o tratar.py recusa com SystemExit)."""
    import tratar
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            getattr(tratar, nome)(*args, **kw)
    except SystemExit as e:
        return str(e) or f"tratar.{nome} recusou"
    return None


def _preparar_textura(el, largura_uso, cache_dir, pasta):
    """Textura única (papel acabamento sem alfa): uma imagem por área, a 1x da largura de uso (múltiplo de 16, nunca
    acima da origem), JPEG q80, pelo tratar.textura (nunca ladrilhada). Cache por sha256 + largura."""
    W0 = el["dims"][0]
    alvo = min(int(math.ceil(float(largura_uso) / 16.0) * 16), int(W0))
    destino = cache_dir / f"{el['id']}@{alvo}.jpg"
    indice_p = cache_dir / "indice.json"
    try:
        indice = json.loads(indice_p.read_text(encoding="utf-8"))
    except Exception:
        indice = {}
    reg = indice.get(destino.name) or {}
    if not (destino.exists() and reg.get("sha256") == el["sha256"] and reg.get("versao") == VERSAO_USO):
        erro = _tratar("textura", str(el["caminho"]), str(destino), largura=alvo, q=80)
        if erro:
            raise SystemExit(f"elemento {el['id']}: textura não preparada: {erro}")
        indice[destino.name] = {"sha256": el["sha256"], "bbox": None, "largura": alvo, "cor": None, "cores": None,
                                "versao": VERSAO_USO, "sha256_uso": _sha256(destino), "acabamento": None, "textura": True}
        indice_p.write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        rel = destino.relative_to(pasta).as_posix()
    except ValueError:
        rel = str(destino)
    return rel, destino, None


def _data_uri(p):
    tipo = "image/jpeg" if Path(p).suffix.lower() in (".jpg", ".jpeg") else "image/png"
    return f"data:{tipo};base64," + base64.b64encode(Path(p).read_bytes()).decode()


# ------------------------------------------------------------------------------------------------- HTML dos itens
def _num(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def _mascara(src, tamanho, repete, posicao="0px 0px"):
    m = f"url({src})"
    return (f"-webkit-mask-image:{m};mask-image:{m};-webkit-mask-size:{tamanho};mask-size:{tamanho};"
            f"-webkit-mask-repeat:{repete};mask-repeat:{repete};-webkit-mask-position:{posicao};mask-position:{posicao};")


def clip_mascara(nome, w, h, espelhar=False):
    """clip-path da `efeito.mascara`, em px da caixa do nó (forma vetorial: vira clip no PDF, provado em prova_pdf.py).
    diagonal: o lado esquerdo cortado no ângulo do kit (12°, o mesmo da máscara diagonal da cena); chanfro: só o canto
    de cima à esquerda, no mesmo ângulo, até a metade da altura (um ângulo por kit, references/05); circulo: o maior
    círculo centrado; arco-base: a base em arco descendo 1/6 da altura; janela: o topo em arco (inset com raio). None
    para `nenhuma` ou nome fora do vocabulário. O clip-path gira e espelha junto com o transform do nó (medido pela
    frente G): `espelhar` desenha a forma espelhada para que, depois do scaleX(-1), o corte fique onde a página pede."""
    w, h = float(w), float(h)
    if w <= 0 or h <= 0 or nome not in MASCARAS or nome == "nenhuma":
        return None
    if nome in ("diagonal", "chanfro"):
        if nome == "diagonal":
            pts = [(min(w, h * TAN_DIAGONAL), 0.0), (w, 0.0), (w, h), (0.0, h)]
        else:
            v = h / 2.0
            pts = [(min(w, v * TAN_DIAGONAL), 0.0), (w, 0.0), (w, h), (0.0, h), (0.0, v)]
        if espelhar:
            pts = [(w - x, y) for x, y in pts]
        return "polygon(" + ",".join(f"{_num(x)}px {_num(y)}px" for x, y in pts) + ")"
    if nome == "circulo":
        return f"circle({_num(min(w, h) / 2)}px at {_num(w / 2)}px {_num(h / 2)}px)"
    if nome == "arco-base":
        a, n = h / 6.0, 24
        arco = ",".join(f"{_num(w * i / n)}px {_num(h - a + a * math.sin(math.pi * i / n))}px" for i in range(n, -1, -1))
        return f"polygon(0 0,100% 0,{arco})"
    r = _num(min(w / 2.0, h))
    return f"inset(0 round {r}px {r}px 0 0)"


def _efeito_valido(ef, avisos=None, quem=""):
    """O `efeito` do item só com valores do vocabulário fechado (vai para CSS inline): opacidade dos degraus, blend nativo,
    máscara conhecida. O que estiver fora sai e vira aviso."""
    ef = dict(ef or {})
    if "opacidade" in ef and not any(isinstance(ef["opacidade"], (int, float)) and not isinstance(ef["opacidade"], bool)
                                     and abs(ef["opacidade"] - o) < 1e-9 for o in OPACIDADES):
        if avisos is not None:
            avisos.append(f"`{quem}`: efeito.opacidade {ef['opacidade']!r} fora dos degraus; ignorada")
        ef.pop("opacidade")
    if "blend" in ef and ef["blend"] not in BLENDS:
        if avisos is not None:
            avisos.append(f"`{quem}`: efeito.blend {ef['blend']!r} fora dos nativos do PDF; ignorado")
        ef.pop("blend")
    if "mascara" in ef and ef["mascara"] not in MASCARAS:
        if avisos is not None:
            avisos.append(f"`{quem}`: efeito.mascara {ef['mascara']!r} fora do vocabulário; ignorada")
        ef.pop("mascara")
    return ef


def html_item(it, el, src=None, svg=None, dx=0.0, dy=0.0, cor=None, blend_padrao=None, corte=None):
    """Um nó por item, com camada e papel em data-*; (dx, dy) desloca quando o nó entra dentro da cena. `cor` (elemento
    de cor chapada): o PNG de uso é só alfa e entra como máscara sobre a cor (ver preparar_uso).
    Acabamento (mk-2.1): `it["efeito"]` vence o elemento (opacidade e blend no próprio nó; máscara vira clip-path);
    `blend_padrao` é o da textura pela área (multiply, screen ou soft-light) quando nada declara blend; `corte` =
    ("atras" | "frente", y do corte na caixa do nó) parte o nó do cruza com clip-path inset (`data-corte`); `it["recorte"]`
    (registro) corta o que cai fora da foto. Sem nenhum desses campos, o nó sai exatamente como antes."""
    cam, papel = it["camada"], it["papel"]
    if corte and corte[0] == "atras":
        cam = "atras"          # a metade de cima do cruza pinta na camada atras (z 1, sob o texto), com a classe dela
    ef = _efeito_valido(it.get("efeito"))
    blend = ef.get("blend") or (el or {}).get("blend") or blend_padrao or "normal"
    blend = blend if blend in BLENDS else "normal"  # só os nativos do PDF (references/07 §3)
    try:
        op = max(0.0, min(1.0, float(ef["opacidade"] if "opacidade" in ef else (el or {}).get("opacidade", 1))))
    except (TypeError, ValueError):
        op = 1
    esc = lambda v: htmlmod.escape(str(v), quote=True)
    base = (f'data-elemento="{esc(it["id"])}" data-papel="{esc(papel)}" data-camada="{esc(cam)}" '
            f'data-encaixe="{esc(it.get("encaixe") or "manual")}"')
    if corte:
        base += f' data-corte="{esc(corte[0])}"'
    caixa = f'left:{_num(it["x"] - dx)}px;top:{_num(it["y"] - dy)}px;width:{_num(it["w"])}px;height:{_num(it["h"])}px;'
    tr = ([f'rotate({_num(it.get("rot") or 0)}deg)'] if it.get("rot") else []) + (["scaleX(-1)"] if it.get("espelhar") else [])
    giro = f'transform:{" ".join(tr)};' if tr else ""
    # clip-path: o corte do cruza, senão o recorte do registro, senão a máscara (uma forma por nó)
    clip = None
    if corte:
        y = max(0.0, min(float(it["h"]), float(corte[1])))
        clip = f"inset(0 0 {_num(float(it['h']) - y)}px 0)" if corte[0] == "atras" else f"inset({_num(y)}px 0 0 0)"
    elif it.get("recorte"):
        r = it["recorte"]
        clip = (f"inset({_num(max(0.0, r[1] - it['y']))}px {_num(max(0.0, it['x'] + it['w'] - r[2]))}px "
                f"{_num(max(0.0, it['y'] + it['h'] - r[3]))}px {_num(max(0.0, r[0] - it['x']))}px)")
    elif ef.get("mascara"):
        clip = clip_mascara(ef["mascara"], it["w"], it["h"], bool(it.get("espelhar")))
    extra = f";clip-path:{clip}" if clip else ""
    if papel == "pattern":
        tile = f'{_num(float((el or {}).get("escala_tile") or 240))}px auto'
        pos = f'{_num(-it["x"])}px {_num(-it["y"])}px'
        fundo = (f"background-color:{cor};" + _mascara(src, tile, "repeat", pos)) if cor else \
            f"background-image:url({src});background-size:{tile};background-position:{pos};"
        return f'<div class="elemento el-{cam} el-pattern" {base} style="{caixa}{fundo}opacity:{op};mix-blend-mode:{blend}{extra}"></div>'
    if svg is not None:
        # grafismo: blend só quando o efeito declara (o legado nunca pôs blend em svg); acabamento na cor do texto
        sv = f";mix-blend-mode:{ef['blend']}" if ef.get("blend") else ""
        cor_ac = ";color:var(--texto)" if papel == "acabamento" else ""
        return f'<div class="elemento el-{cam} el-{papel} el-svg" {base} style="{caixa}{giro}opacity:{op}{sv}{cor_ac}{extra}">{svg}</div>'
    if cor:
        return (f'<div class="elemento el-{cam} el-{papel} el-mascara" {base} style="{caixa}{giro}background-color:{cor};'
                f'{_mascara(src, "100% 100%", "no-repeat")}opacity:{op};mix-blend-mode:{blend}{extra}"></div>')
    return (f'<img class="elemento el-{cam} el-{papel}" {base} src="{src}" alt="" '
            f'style="{caixa}{giro}opacity:{op};mix-blend-mode:{blend}{extra}">')


# ------------------------------------------------------------------------------------------------- maquete
# cor de cada função (references/09 §2); a folha de composição usa as mesmas
COR_FUNCAO = {"foco": "#FF3B30", "contexto": "#00B3A6", "identidade": "#FFCC00", "conexao": "#FF2D95",
              "organizacao": "#0A84FF", "profundidade": "#AF52DE", "equilibrio": "#34C759", "acabamento": "#8E8E93"}
COR_SEM_FUNCAO = "#FF9500"    # herói ou apoio do catálogo: sem função declarada


def funcao_do_item(it):
    """A função declarada; constante e pattern são acabamento por natureza; o resto do catálogo não tem função."""
    return it.get("funcao") or ("acabamento" if it.get("papel") in ("constante", "pattern") else None)


def rotulo_maquete(it):
    """`id · função · relação→alvo` do item resolvido."""
    anc = it.get("ancora") or {}
    rel = anc.get("relacao")
    if rel:
        alvos = []
        for r in anc.get("restricoes") or []:
            if r.get("alvo") and r["alvo"] not in alvos:
                alvos.append(r["alvo"])
        rel_txt = (f"liga {anc.get('modo')}" if rel == "liga" else rel) + "→" + ",".join(alvos or ["?"])
    elif it.get("caixa_unica"):
        rel_txt = f"caixa única→{it.get('encaixe') or it['caixa_unica']}"
    else:
        rel_txt = f"catálogo→{it.get('encaixe') or 'manual'}"
    return f"{it['id']} · {funcao_do_item(it) or it.get('papel')} · {rel_txt}"


def html_maquete(it, dx=0.0, dy=0.0, largura=1920):
    """A maquete (render.py --maquete, 'planejar antes de gerar'): o elemento vira caixa hachurada na cor da função, com
    rótulo, na posição e no tamanho resolvidos, sem precisar do asset. Linha e moldura da liga saem como a própria
    geometria tracejada; pattern, só o contorno (hachurar a página inteira esconderia o resto)."""
    esc = lambda v: htmlmod.escape(str(v), quote=True)
    cor = COR_FUNCAO.get(funcao_do_item(it) or "", COR_SEM_FUNCAO)
    base = (f'data-elemento="{esc(it["id"])}" data-papel="{esc(it["papel"])}" data-camada="{esc(it["camada"])}" '
            f'data-encaixe="{esc(it.get("encaixe") or "manual")}"')
    caixa = f'left:{_num(it["x"] - dx)}px;top:{_num(it["y"] - dy)}px;width:{_num(it["w"])}px;height:{_num(it["h"])}px;'
    tr = ([f'rotate({_num(it.get("rot") or 0)}deg)'] if it.get("rot") else [])
    giro = f'transform:{" ".join(tr)};' if tr else ""
    geo = (it.get("ancora") or {}).get("geometria") or {}
    dentro = ""
    if geo.get("pontos") or geo.get("caixa"):
        w, h = max(1.0, float(it["w"])), max(1.0, float(it["h"]))
        if geo.get("pontos"):
            pts = " ".join(f"{_num(p[0] - it['x'])},{_num(p[1] - it['y'])}" for p in geo["pontos"])
            forma = f'<polyline points="{pts}" fill="none" stroke="{cor}" stroke-width="3" stroke-dasharray="10 6"/>'
        else:
            x, y, cw, ch = geo["caixa"]
            forma = (f'<rect x="{_num(x - it["x"] + 1.5)}" y="{_num(y - it["y"] + 1.5)}" width="{_num(max(1, cw - 3))}" '
                     f'height="{_num(max(1, ch - 3))}" fill="none" stroke="{cor}" stroke-width="3" stroke-dasharray="10 6"/>')
        dentro = (f'<svg class="maquete-geo" width="{_num(w)}" height="{_num(h)}" viewBox="0 0 {_num(w)} {_num(h)}" '
                  f'style="position:absolute;left:0;top:0;overflow:visible">{forma}</svg>')
        fundo = ""
    elif it["papel"] == "pattern":
        fundo = f"outline:2px dashed {cor};outline-offset:-2px;"
    else:
        fundo = (f"background-image:repeating-linear-gradient(45deg,{cor}66 0 3px,transparent 3px 14px);"
                 f"outline:2px solid {cor};outline-offset:-2px;")
    lado = "right:0" if it["x"] + it["w"] / 2 > largura / 2 else "left:0"     # rótulo para dentro da página
    rotulo = (f'<span class="maquete-rotulo" style="position:absolute;{lado};top:0;padding:2px 6px;background:{cor};'
              f'color:#000;font:600 14px/1.3 sans-serif;white-space:nowrap">{esc(rotulo_maquete(it))}</span>')
    return (f'<div class="elemento el-{it["camada"]} el-maquete" {base} style="{caixa}{giro}{fundo}">'
            f'{dentro}{rotulo}</div>')


# ------------------------------------------------------------------------------------------------- injeção no DOM
_TAG = re.compile(r"<!--.*?-->|<(/?)([a-zA-Z][\w:-]*)((?:\"[^\"]*\"|'[^']*'|[^'\">])*)>", re.S)
_VAZIOS = {"img", "br", "hr", "input", "meta", "link", "source", "area", "base", "col", "embed", "param", "track", "wbr"}


def filhos_diretos(html):
    """Nós filhos diretos de um trecho de HTML: [(início, fim, tag, classes, atributos)]."""
    filhos, prof, ini, tag0, at0 = [], 0, None, None, None
    for m in _TAG.finditer(html):
        if m.group(0).startswith("<!--"):
            continue
        fecha, tag, attrs = m.group(1) == "/", m.group(2).lower(), m.group(3) or ""
        auto = attrs.rstrip().endswith("/") or tag in _VAZIOS
        if fecha:
            prof -= 1
            if prof == 0 and ini is not None:
                filhos.append((ini, m.end(), tag0, _classes(at0), at0)); ini = None
            continue
        if prof == 0:
            if auto:
                filhos.append((m.start(), m.end(), tag, _classes(attrs), attrs)); continue
            ini, tag0, at0 = m.start(), tag, attrs
        if not auto:
            prof += 1
    return filhos


def _classes(attrs):
    m = re.search(r'\bclass="([^"]*)"', attrs or "")
    return set(m.group(1).split()) if m else set()


def _eh_cena(f):
    return bool({"full", "cena"} & f[3])


def _eh_veu(f):
    return "veu" in f[3] or 'data-layer="veu"' in (f[4] or "")


def pontos_de_insercao(secao_interna):
    """Onde cada camada entra dentro da <section>: depois da cena, depois do último véu, antes do .logo-canto."""
    fs = filhos_diretos(secao_interna)
    i_cena = next((i for i, f in enumerate(fs) if _eh_cena(f)), None)
    pos_sob = fs[i_cena][1] if i_cena is not None else 0
    veus = [f for f in fs if _eh_veu(f) and f[0] >= pos_sob]
    pos_atras = max([f[1] for f in veus] + [pos_sob])
    logo = next((f for f in fs if "logo-canto" in f[3]), None)
    pos_frente = logo[0] if logo else len(secao_interna)
    dentro_cena = (fs[i_cena][1] - len("</div>")) if (i_cena is not None and fs[i_cena][2] == "div") else None
    return {"sob-veu": pos_sob, "atras": pos_atras, "frente": pos_frente, "dentro-cena": dentro_cena}


def injetar(html, nos_por_pagina):
    """nos_por_pagina[i] = {"sob-veu": [html...], "atras": [...], "frente": [...], "dentro-cena": [...]} da página i."""
    partes = html.split("</section>")
    out = []
    for i, parte in enumerate(partes[:-1]):
        nos = nos_por_pagina[i] if i < len(nos_por_pagina) else None
        if nos and any(nos.values()):
            j = parte.find("<section")
            k = parte.find(">", j) + 1
            cab, interno = parte[:k], parte[k:]
            pts = pontos_de_insercao(interno)
            ins = []
            for cam in ("sob-veu", "atras", "frente", "dentro-cena"):
                if nos.get(cam):
                    pos = pts[cam] if pts[cam] is not None else pts["sob-veu"]
                    ins.append((pos, ("sob-veu", "atras", "frente", "dentro-cena").index(cam), "".join(nos[cam])))
            # de trás para frente (posições continuam válidas); mesma posição: sob-veu antes de atras
            for pos, _, txt in sorted(ins, key=lambda t: (t[0], t[1]), reverse=True):
                interno = interno[:pos] + txt + interno[pos:]
            parte = cab + interno
        out.append(parte)
    out.append(partes[-1])
    return "</section>".join(out)


# ------------------------------------------------------------------------------------------------- orquestração
def _logo_no_kit(pasta, logo):
    try:
        return dentro_do_kit(pasta, logo["arquivo"])
    except ForaDoKit as erro:
        raise SystemExit(f"acervo {logo.get('id')}: {erro}. O render recusa: o logo iria para dentro dos grafismos e do PDF")


def contexto_grafismo(k, receita, pasta, fontes_dir):
    f = (receita or {}).get("fontes") or {}
    m = k.get("marca") or {}
    pal = dict((receita or {}).get("paleta") or {})
    if not pal:
        pal = {"marca": m.get("cor_primaria"), "escuro": m.get("cor_fundo_escuro"), "texto": "#FFFFFF"}
    # o logo do selo é o mesmo do grafismos.ctx_do_kit: marca.logo_id; sem ele, o primeiro lettering/logo do acervo
    acervo = [a for a in k.get("acervo", []) if a.get("arquivo")]
    logo = (next((a for a in acervo if a.get("id") == m.get("logo_id")), None) if m.get("logo_id") else None) \
        or next((a for a in acervo if a.get("funcao") in ("lettering", "logo")), None)
    fontes = {"display": f.get("display") or m.get("fonte_display"),
              "peso_display": int(f.get("peso_display") or m.get("peso_display") or 800),
              "corpo": f.get("corpo") or m.get("fonte_corpo")}
    if f.get("lettering"):
        # tipografia expressiva (mk-2.1): sem ela, o grafismos.py cai no display
        fontes["lettering"] = f["lettering"]
    return {"fontes": fontes,
            "paleta": pal, "evento": k.get("evento") or {},
            "logo_png": str(_logo_no_kit(pasta, logo)) if logo else None,
            "fontes_dir": str(fontes_dir or Path(pasta) / "fontes")}


def _pede_textos(k):
    """Algum grafismo do kit (elementos[], constantes ou composição) pede texto_de titulo ou tese?"""
    def anda(o):
        if isinstance(o, dict):
            return o.get("texto_de") in ("titulo", "tese") or any(anda(v) for v in o.values())
        if isinstance(o, list):
            return any(anda(v) for v in o)
        return False
    return anda([k.get("elementos"), k.get("sistema_elementos"), k.get("composicao")])


def contexto_com_textos(ctx, textos):
    """O ctx dos grafismos com os textos vivos da página (`textos`: titulo, tese), que o grafismos.gerar lê para
    texto_de titulo e tese. Sem texto, o ctx fica como estava."""
    return dict(ctx or {}, textos=textos) if textos else (ctx or {})


def chave_pronto(it):
    """Chave do PNG de uso de um item: (elemento, acabamento da frente) e, só com esmaecer, a variante dele (a chave do
    legado continua a de dois campos)."""
    k = (it.get("el_id") or it["id"], it.get("acabamento"))
    return k + (it["variante_uso"],) if it.get("variante_uso") else k


def ordem_de_pintura(res):
    """Ordem dos nós de uma página: pattern primeiro, depois a ORDEM dos papéis (a de sempre, estável); o item derivado
    (sombra, reflexo) entra logo ANTES do pai, na camada dele. Sem derivado, a ordem é exatamente a de antes."""
    chave = lambda it: (it["papel"] != "pattern", encaixes.ORDEM.get(it["papel"], 9))  # noqa: E731
    filhos = {}
    for it in res:
        if it.get("derivado_de"):
            filhos.setdefault(it["derivado_de"], []).append(it)
    out = []
    for it in sorted([it for it in res if not it.get("derivado_de")], key=chave):
        out += filhos.pop(it["id"], [])
        out.append(it)
    for resto in filhos.values():
        out += resto
    return out


class Elementos:
    """Estado do sistema de elementos de um kit: carga, planos por receita, itens resolvidos (para o --fundo)."""
    # camada de acabamento (mk-2.1): o __init__ decide pelo kit; o padrão de classe vale para quem monta o objeto sem ele
    # (as provas montam Elementos parciais com __new__)
    usa_acab = False
    usa_textos = False
    luz_familia = {}

    def __init__(self, k, pasta, report, fontes_dir=None):
        self.k, self.pasta, self.report, self.fdir = k, Path(pasta), report, fontes_dir
        self.sistema = k.get("sistema_elementos") or None
        self.els = carregar(k, self.pasta, report)
        # composição por página (composicao.py): validada uma vez; erro de schema ou de regra vira FALHA no QA. A âncora
        # das constantes (sistema_elementos.constantes[].ancora, só alvos estruturais) entra na mesma conta
        self.composicao = k.get("composicao") or {}
        # com o kit: todas as regras da camada de acabamento (acabamento.validar); kit sem campo novo não passa por nenhuma
        self.erros_composicao = composicao.validar(self.composicao, [e.get("id") for e in k.get("elementos") or []], kit=k)
        import acabamento
        self.usa_acab = acabamento.usa_acabamento(k)
        # o título inteiro da página vai aos alvos e aos grafismos (ctx.textos) quando o kit declara a camada de
        # acabamento ou um grafismo pede texto_de titulo/tese (eco, numeral-eco, texto-curva da frente G)
        self.usa_textos = self.usa_acab or _pede_textos(k)
        self.luz_familia = {f.get("id"): f.get("luz") for f in (self.sistema or {}).get("familias") or [] if isinstance(f, dict)}
        self.erros_composicao += composicao.validar_constantes(self.sistema)
        self.catalogo = encaixes.carregar_catalogo()
        self.saida = self.pasta / "saida"
        self.cache = self.saida / "cache-elementos"
        gerar, self.nome_gerador = gerador_grafismos()

        def gerar_no_kit(tipo, params, ctx):
            # a imagem de um grafismo (a captura dentro do `celular`) vem do JSON do kit: caminho a partir da pasta do
            # kit e sem sair dela; antes era lida a partir da pasta onde o render rodava
            params = dict(params or {})
            for chave in ARQUIVOS_DE_GRAFISMO:
                if params.get(chave):
                    params[chave] = str(dentro_do_kit(self.pasta, params[chave]))
            return gerar(tipo, params, ctx)
        self.gerar = gerar_no_kit
        self.atrib_h = {}     # d -> [(pagina_info, atribuidos)] do horizontal (o vertical deriva daqui)
        self.injecoes = {}    # (d, formato) -> nós por página (o --fundo reaproveita)
        self.resumos = {}
        self._svgs = {}       # grafismo gerado na medida da colocação: um svg por conjunto de parâmetros (e de ctx)

    # -- páginas no formato do contrato (com os rótulos que `paginas` do JSON usa)
    def _paginas(self, pags, formato):
        if formato == "vertical":
            cotas = [p for p in pags if p["tipo"] == "cota"]
            princ = next((p for p in cotas if (p.get("cota") or {}).get("principal")), cotas[0] if cotas else None)
            r2 = {"publico", "vertical:numeros"} | ({"cota", f"cota:{(princ.get('cota') or {}).get('nome')}"} if princ else set())
            return [{"n": 1, "rotulo": "vertical:capa", "tipo": "capa", "_rotulos": {"capa", "vertical:capa"}},
                    {"n": 2, "rotulo": "vertical:numeros", "tipo": "cota", "_rotulos": r2},
                    {"n": 3, "rotulo": "vertical:contato", "tipo": "contato", "_rotulos": {"contato", "vertical:contato"}}]
        return [{"n": i + 1, "rotulo": rotulo_variante(p), "tipo": p["tipo"], "_rotulos": rotulos_pagina(p)} for i, p in enumerate(pags)]

    def _atribuidos(self, d, receita, paginas, pags, formato):
        if formato == "vertical":
            # o vertical repete o herói e as constantes das páginas equivalentes do horizontal (sem coordenada manual:
            # quem decide a posição na tela 1080×1920 são os encaixes do vertical); pattern não entra (só canto e faixa)
            base = self.atrib_h.get(d) or []
            def de(tipos, principal=False):
                cands = [(p, at) for p, at in base if p["tipo"] in tipos]
                if principal:
                    cands = [c for c in cands if (c[0].get("_cota") or {}).get("principal")] or cands
                return cands[0][1] if cands else []
            fonte = [de(("capa",)), de(("cota",), True) or de(("publico",)), de(("contato",))]
            out = []
            for p, at in zip(paginas, fonte):
                out.append({"n": p["n"], "atribuidos": [dict(a) for a in at if a.get("papel") != "pattern"]})
            return out, "derivado do horizontal"
        rid = (receita or {}).get("id") or ("padrao" if self.sistema else d)
        elementos = list(self.k.get("elementos") or [])
        plano, nome = planejar(self.sistema, elementos, rid, paginas, self.catalogo, receita, composicao_kit=self.composicao)
        self.atrib_h[d] = [(dict(p, _cota=(pags[p["n"] - 1].get("cota") if p["n"] - 1 < len(pags) else None)), pp["atribuidos"])
                           for p, pp in zip(paginas, plano)]
        return plano, nome

    def _aplicar_composicao(self, atrib, paginas, formato):
        """A composição da página vence o plano (precedência: composição > ajuste manual > exceção > catálogo): com
        `elementos`, os heróis, apoios e estruturas da página passam a ser os da composição; constantes e pattern ficam,
        menos os que ela tira em `sem`. Na vertical só valem as chaves vertical:*, e o que veio ancorado do horizontal
        sai (a âncora foi resolvida contra a geometria do horizontal). Devolve (atribuídos, meta por página)."""
        ids_kit = [e.get("id") for e in self.k.get("elementos") or []]
        out, meta = [], []
        for p, pp in zip(paginas, atrib):
            ats = list(pp["atribuidos"])
            if formato == "vertical":
                ats = [a for a in ats if a.get("origem") != "composicao"]
            chave, ent, gch, _ = composicao.entrada_da_pagina(self.composicao, p["_rotulos"], p["rotulo"], p["tipo"], formato)
            m = None
            if ent is not None:
                m = {"chave": chave, "gramatica": gch, **{c: ent.get(c) for c in
                     ("mensagem", "foco", "leitura", "estrutura", "padroes", "porque_fora_da_gramatica")}}
                sem = set(ent.get("sem") or [])
                fora = lambda a: a["id"] in sem or (a.get("papel") == "pattern" and "pattern" in sem)
                if "elementos" in ent:
                    ats = [a for a in ats if a.get("papel") in ("constante", "pattern") and not fora(a)]
                    ats += composicao.atribuidos(ent, p["n"], ids_kit)
                elif sem:
                    ats = [a for a in ats if not fora(a)]
            out.append(dict(pp, atribuidos=ats))
            meta.append(m)
        return out, meta

    def _medida_da_constante(self, tipo, i, atrib, paginas, largura):
        """Constante em texto vivo nasce no tamanho do encaixe (o resolver só encolhe texto vivo até 25%): o selo no
        menor diâmetro dos cantos de constante das páginas onde entra; o microtexto no comprimento da faixa de borda
        (largura da página menos as margens de 96 px do resolver, ou a página inteira se a faixa sangra). Sem isso o
        selo de 320 px não cabe no canto de 150 e o microtexto de 1920 px não cabe no vertical de 1080."""
        encs = [e for p, pp in zip(paginas, atrib) if any(a["id"] == i for a in pp["atribuidos"])
                for e in (self.catalogo.get(p["rotulo"]) or []) if "constante" in (e.get("papeis") or [])]
        if tipo == "selo":
            lados = [min(e["max"]) for e in encs if e.get("gerador") == "canto" and e.get("max")]
            return {"diametro": min(lados)} if lados else {}
        if tipo == "microtexto":
            comp = [largura if e.get("sangra") else largura - 2 * 96 for e in encs
                    if e.get("gerador") == "faixa" and e.get("lado", "base") in ("topo", "base")]
            return {"largura": min(comp)} if comp else {}
        if tipo == "regua-borda":
            # régua de borda (frente G): o comprimento da faixa, como o microtexto; sem faixa, a largura da página (o
            # padrão do gerador é 1920 e não cabia no vertical de 1080)
            comp = [largura if e.get("sangra") else largura - 2 * 96 for e in encs
                    if e.get("gerador") == "faixa" and e.get("lado", "base") in ("topo", "base")]
            return {"largura": min(comp) if comp else largura}
        return {}

    def _dims_e_svgs(self, atrib, ctx, avisos, paginas=(), largura=1920, maquete=False, medidas=None):
        """Dimensões de cada elemento e o svg dos grafismos no tamanho natural. Ficam para a resolução: a liga (nasce
        da geometria) e o grafismo ancorado com escala (nasce na medida da colocação). Na maquete, asset planejado
        (`proporcao`) entra só com a proporção. Grafismo declarado só na página recebe os textos dela (ctx.textos)."""
        dims, svgs = {}, {}
        consts = dict(constantes_com_id(self.sistema))
        ctx_kit = ctx
        for n_pg, pp in enumerate(atrib):
            ctx = (contexto_com_textos(ctx_kit, self._textos(medidas[n_pg]))
                   if self.usa_textos and medidas and n_pg < len(medidas) else ctx_kit)
            for a in pp["atribuidos"]:
                i = a["id"]
                if i in dims or i in svgs:
                    continue
                anc = a.get("ancora") or {}
                if anc.get("relacao") == "liga":
                    continue
                el = self.els.get(i)
                if el and el["formato"] == "png":
                    dims[i] = (el["dims"][0], el["dims"][1], el.get("alfa_bbox"))
                    continue
                if anc and a.get("escala") and not maquete and (a.get("grafismo") or (el and el["formato"] == "svg")):
                    continue
                if el and el["formato"] == "svg":
                    tipo, params = el.get("tipo"), dict(el.get("params") or {})
                elif i in consts:
                    c = consts[i]; tipo = c["tipo"]
                    # o tamanho vem do encaixe; params declarados na constante vencem; o texto vem de texto_de/texto
                    params = {**self._medida_da_constante(tipo, i, atrib, paginas, largura), **(c.get("params") or {})}
                    params["texto"] = texto_constante(c, self.k)
                elif a.get("grafismo"):
                    # grafismo declarado só na composição da página (id já único por página)
                    tipo, params = a["grafismo"]["tipo"], dict(a["grafismo"].get("params") or {})
                elif a.get("proporcao"):
                    if maquete:
                        pw, ph = a["proporcao"]
                        dims[i] = (float(pw) * 1000.0, float(ph) * 1000.0, None)
                    continue                  # fora da maquete a âncora acusa: asset planejado ainda não gerado (FALHA)
                else:
                    avisos.append(f"`{i}`: atribuído mas não existe em elementos[] nem nas constantes"); continue
                try:
                    g = self.gerar(tipo, params, ctx)
                except (ValueError, NotImplementedError) as e:
                    if maquete and a.get("proporcao"):
                        pw, ph = a["proporcao"]
                        dims[i] = (float(pw) * 1000.0, float(ph) * 1000.0, None)
                        continue
                    avisos.append(f"grafismo `{i}` ({tipo}): {e}"); continue
                g = dict(g, svg=cor_pela_pagina(g["svg"], (ctx.get("paleta") or {}).get("marca")))
                svgs[i] = g
                dims[i] = (g["w"], g["h"], None)
        return dims, svgs

    def _gerador(self, ctx):
        """gerar(tipo, params) para o grafismo que nasce na resolução (liga e ancorado com escala): o grafismos.gerar com
        o ctx da receita, cor da marca pela página, cache pelo conjunto de parâmetros."""
        chave_ctx = json.dumps(ctx, sort_keys=True, ensure_ascii=False, default=str)
        marca = (ctx.get("paleta") or {}).get("marca")

        def gerar(tipo, params):
            k = (chave_ctx, tipo, json.dumps(params, sort_keys=True, ensure_ascii=False, default=str))
            if k not in self._svgs:
                g = self.gerar(tipo, params, ctx)
                self._svgs[k] = dict(g, svg=cor_pela_pagina(g["svg"], marca))
            return self._svgs[k]
        return gerar

    def _decorar(self, a, svgs, W, p):
        """O atribuído com o que o resolvedor precisa saber do elemento: svg, tinta, linhas, giro, camada, grafismo da
        âncora e o ajuste manual antigo."""
        a = dict(a)
        el = self.els.get(a["id"])
        if a["id"] in svgs:
            a["svg"] = True
            if svgs[a["id"]].get("tinta"):
                a["tinta_bbox"] = svgs[a["id"]]["tinta"]
            if svgs[a["id"]].get("linhas"):
                a["linhas"] = svgs[a["id"]]["linhas"]
        if a.get("ancora") and (a.get("grafismo") or (el and el["formato"] == "svg")):
            # grafismo ancorado: o composicao gera COM a geometria resolvida (liga) ou na medida da escala
            a["_grafismo"] = a.get("grafismo") or {"tipo": el.get("tipo"), "params": dict(el.get("params") or {})}
            esm = (a.get("efeito") or {}).get("esmaecer")
            if esm and "esmaecer" not in (a["_grafismo"].get("params") or {}):
                # grafismo de elementos[] com efeito.esmaecer na página: os degraus vão ao gerador (o da página já vem
                # com eles do composicao.atribuidos)
                a["_grafismo"] = dict(a["_grafismo"], params=dict(a["_grafismo"].get("params") or {}, esmaecer=dict(esm)))
        if el and el.get("tinta_bbox") and a.get("ancora"):
            a["tinta_bbox"] = el["tinta_bbox"]
        if el:
            if el.get("rot") is not None and a.get("rot") is None:
                a["rot"] = el["rot"]
            if not a.get("camada") and el.get("camada"):
                a["camada"] = el["camada"]
            if el.get("papel") == "pattern":
                if not self.sistema:
                    a["manual"] = {"pagina_inteira": True}  # regra antiga: o pattern cobre a página
            elif (W == 1920 and el["formato"] == "png" and _casa(el.get("paginas"), p["_rotulos"])
                  and all(isinstance(el.get(c), (int, float)) for c in ("x", "y", "w"))):
                # ajuste manual antigo (x, y, w na página 1920×1080): vale como foi escrito, o QA julga
                a["manual"] = {"x": el["x"], "y": el["y"], "w": el["w"], "rot": el.get("rot", 0)}
        return a

    def _caixas_unicas(self, ats_pag, paginas, medidas, dims, W, H, zonas):
        """Constante (selo, microtexto, faixa) ocupa a MESMA caixa em toda página onde entra, por receita e formato
        (references/09 §5). A caixa vem da `ancora` da constante (sistema_elementos.constantes[], só alvos estruturais)
        ou, sem ela, do encaixe do catálogo: cada página onde a constante cabe no tamanho em que nasce dá uma caixa
        candidata, e vale a que serve a MAIS páginas (empate: a da primeira página). "A primeira página onde coube",
        sozinha, punha o microtexto da capa (sem o fio de progresso) em y=1032 e o tirava de todas as outras páginas.
        As caixas já escolhidas entram como obstáculo das seguintes: as constantes nunca se atropelam. Devolve
        ({id: caixa}, avisos)."""
        cfg = dict(constantes_com_id(self.sistema))
        ordem = []
        for ats in ats_pag:
            for a in ats:
                if a.get("papel") == "constante" and not a.get("ancora") and a["id"] in dims and a["id"] not in ordem:
                    ordem.append(a["id"])
        caixas, avisos = {}, []
        for cid in ordem:
            onde = [(i, a) for i, ats in enumerate(ats_pag) for a in ats if a["id"] == cid]
            reservados = [encaixes._aabb(dict(c, id=k)) for k, c in caixas.items()]
            c = cfg.get(cid) or {}
            if c.get("ancora"):
                i0, a0 = onde[0]
                a_anc = {"id": cid, "papel": "constante", "camada": a0.get("camada") or "frente", "ancora": c["ancora"],
                         "tamanho_natural": True, "funcao": "acabamento", "tinta_bbox": a0.get("tinta_bbox"),
                         "linhas": a0.get("linhas")}
                try:
                    it = composicao.resolver(a_anc, dims[cid], dict(medidas[i0], w=W, h=H))
                except composicao.ErroComposicao as e:
                    self.erros_composicao.append(f"constante `{cid}`: a âncora não resolveu: {e}")
                    continue
                caixas[cid] = {"x": it["x"], "y": it["y"], "w": it["w"], "h": it["h"], "rot": it.get("rot") or 0,
                               "encaixe": "ancora", "camada": it["camada"], "de": "ancora"}
                continue
            cands = []
            for i, a in onde:
                m = dict(medidas[i], w=W, h=H, safe=96, avisos=[], erros_composicao=[], vendaveis=zonas[i],
                         reservados=reservados)
                rot = paginas[i]["rotulo"]
                cat = self.catalogo
                if c.get("encaixe"):
                    # encaixe declarado na constante é a posição dela: a caixa só pode sair dele (o resolver comum
                    # tentaria os outros encaixes de constante e o microtexto da base iria para o topo)
                    cat = {rot: [e for e in self.catalogo.get(rot) or [] if e["id"] == c["encaixe"]]}
                res = encaixes.resolver([dict(a, sem_encolher=True)], rot, cat, m, {cid: dims[cid]})
                if res:
                    r = res[0]
                    cands.append((i, {"x": r["x"], "y": r["y"], "w": r["w"], "h": r["h"], "rot": r.get("rot") or 0,
                                      "encaixe": r["encaixe"], "camada": r["camada"], "de": f"p.{paginas[i]['n']}"}))
            if not cands:
                avisos.append(f"constante `{cid}` não cabe no tamanho em que nasce em nenhuma página: fica fora")
                continue

            def serve(cx):
                return sum(1 for i, a in onde
                           if encaixes.na_caixa(a, "constante", cx, dict(medidas[i], vendaveis=zonas[i]), reservados)[0] is not None)
            caixas[cid] = max(cands, key=lambda ic: (serve(ic[1]), -ic[0]))[1]
        return caixas, avisos

    def _resolver(self, atrib, paginas, medidas, dims, svgs, W, H, ctx=None, zonas=None, maquete=False):
        """Resolve todas as páginas: decora os atribuídos, acha a caixa única de cada constante e chama o
        encaixes.resolver por página (a âncora da composição vai ao composicao, que gera o grafismo preso a geometria).
        Devolve (itens, avisos por página, erros de composição por página, svgs gerados por página, avisos gerais)."""
        zonas = zonas if zonas is not None else [[] for _ in paginas]
        gerar = None if maquete else self._gerador(ctx or {})
        ats_pag = [[self._decorar(a, svgs, W, p) for a in pp["atribuidos"]] for p, pp in zip(paginas, atrib)]
        caixas, avisos = self._caixas_unicas(ats_pag, paginas, medidas, dims, W, H, zonas)
        itens, avisos_pag, erros_pag, svgs_pag = [], [], [], []
        for i, (p, ats, med) in enumerate(zip(paginas, ats_pag, medidas)):
            fora = []
            usar = []
            for a in ats:
                if a.get("papel") == "constante" and not a.get("ancora") and a["id"] in dims:
                    if a["id"] not in caixas:
                        fora.append(f"{p['rotulo']}: constante `{a['id']}` sem caixa única: fica fora")
                        continue
                    a = dict(a, caixa=caixas[a["id"]])
                usar.append(a)
            m = dict(med, w=W, h=H, safe=96, avisos=[], erros_composicao=[], vendaveis=zonas[i])
            if gerar and self.usa_textos:
                # grafismo de texto_de titulo/tese (eco, frente G): o título desta página e a tese do kit
                m["gerar_grafismo"] = self._gerador(contexto_com_textos(ctx, self._textos(med)))
            elif gerar:
                m["gerar_grafismo"] = gerar
            res = encaixes.resolver(usar, p["rotulo"], self.catalogo, m, dims)
            gerados = {}
            for it in res:
                g = it.pop("_svg", None)
                if g is not None:
                    gerados[it["id"]] = g
            itens.append(res)
            svgs_pag.append(gerados)
            avisos_pag.append(fora + m["avisos"])
            erros_pag.append(m["erros_composicao"])
        return itens, avisos_pag, erros_pag, svgs_pag, avisos

    # -- camada de acabamento (mk-2.1)
    def _textos(self, med):
        t = {}
        tit = ((med.get("alvos") or {}).get("titulo") or {}).get("texto")
        if tit:
            t["titulo"] = tit
        if (self.k.get("tese") or {}).get("frase"):
            t["tese"] = self.k["tese"]["frase"]
        return t

    def _el(self, it):
        """O elemento de um item: o de elementos[] ou o derivado (sombra, reflexo), registrado em `el_id`."""
        return self.els.get(it.get("el_id") or it["id"])

    def _acabamento_pagina(self, p, formato):
        _, ent, _, gent = composicao.entrada_da_pagina(self.composicao, p["_rotulos"], p["rotulo"], p["tipo"], formato)
        return (ent or {}).get("acabamento") or (gent or {}).get("acabamento") or {}

    def _cruzar(self, itens, medidas, erros_pag):
        """efeito.cruza: a linha do corte (linha_base, cap ou cy do título ou do número) medida na página. O item ganha
        `cruza` {alvo, corte, y, corte_px}; o _nos desenha dois nós. Alvo ausente ou linha fora do elemento: erro da âncora
        (FALHA no QA, como qualquer alvo da composição) e o elemento sai inteiro na camada dele."""
        for res, med, erros in zip(itens, medidas, erros_pag):
            for it in res:
                cz = (it.get("efeito") or {}).get("cruza")
                if not cz:
                    continue
                el = self.els.get(it["id"])
                if not el or el["formato"] != "png":
                    erros.append(f"`{it['id']}`: cruza só em PNG de elementos[] (as duas metades são o mesmo data URI)")
                    continue
                try:
                    v = composicao.valor_alvo(med.get("alvos") or {}, cz.get("alvo"), None, cz.get("corte"))
                except (composicao.ErroComposicao, KeyError) as e:
                    erros.append(f"`{it['id']}`: cruza: {e}")
                    continue
                if it.get("rot"):
                    erros.append(f"`{it['id']}`: cruza com giro não é suportado (o corte é horizontal)")
                    continue
                y = v - float(it["y"])
                if not 1.0 <= y <= float(it["h"]) - 1.0:
                    erros.append(f"`{it['id']}`: cruza: a linha {cz.get('corte')} de `{cz.get('alvo')}` (y={v:.0f}) não passa pelo "
                                 f"elemento ({it['y']:.0f} a {it['y'] + it['h']:.0f}): ele não cruza o texto")
                    continue
                it["cruza"] = {"alvo": cz.get("alvo"), "corte": cz.get("corte"), "y": round(v, 1), "corte_px": round(y, 1)}

    def _el_derivado(self, chave, caminho, pai, tipo):
        """Registra o PNG derivado (sombra, reflexo) como elemento: dimensões, alfa, tinta e sha256, como o carregar."""
        bbox, (W, H) = alfa_bbox(caminho)
        tinta, _ = alfa_bbox(caminho, limiar=composicao.LIMIAR_TINTA)
        self.els[chave] = {"id": chave, "papel": "acabamento", "papel_plano": "acabamento", "formato": "png",
                           "caminho": Path(caminho), "dims": (W, H), "alfa_bbox": bbox, "tinta_bbox": tinta,
                           "sha256": _sha256(caminho), "derivado_de": pai, "tipo_derivado": tipo}
        return self.els[chave]

    def _derivados(self, itens, paginas, formato, erros_pag, avisos_pag):
        """sombra contato e reflexo piso viram itens derivados `<id>-sombra` e `<id>-reflexo` (papel acabamento,
        `derivado_de`), feitos pelo tratar.py a partir do PNG de origem (cache por sha256 + parâmetros) e postos na mesma
        conta de escala do pai: a sombra na origem do PNG (o canvas dela começa no mesmo canto), o reflexo com o topo na
        base da tinta. Pintam logo antes do pai, na camada dele (_ordem_de_pintura)."""
        pasta = self.cache / "derivados"
        for res, p, erros, avs in zip(itens, paginas, erros_pag, avisos_pag):
            novos = []
            for it in res:
                ef = it.get("efeito") or {}
                pede = [t for t, ok in (("reflexo", ef.get("reflexo") == "piso"), ("sombra", ef.get("sombra") == "contato")) if ok]
                if not pede:
                    continue
                el = self.els.get(it["id"])
                if not el or el["formato"] != "png" or not el.get("caminho"):
                    erros.append(f"`{it['id']}`: {' e '.join(pede)} só em PNG de elementos[] (sai da silhueta do recorte)")
                    continue
                if it.get("rot"):
                    erros.append(f"`{it['id']}`: {' e '.join(pede)} com giro não é suportado (o piso é horizontal)")
                    continue
                W0, H0 = el["dims"]
                bb = el.get("alfa_bbox") or (0, 0, W0, H0)
                s = float(it["w"]) / float(bb[2] - bb[0])
                ox, oy = float(it["x"]) - bb[0] * s, float(it["y"]) - bb[1] * s
                esp = bool(it.get("espelhar"))
                for tipo in pede:
                    if tipo == "sombra":
                        luz = LUZ_FAMILIA.get(self.luz_familia.get(el.get("familia")) or "") or \
                            LUZ_FAMILIA.get(self._acabamento_pagina(p, formato).get("luz") or "") or "esquerda"
                        # espelhado: a sombra sai do PNG de origem com a luz oposta e espelha junto com o objeto
                        luz_png = OPOSTA[luz] if esp else luz
                        params = {"luz": luz_png}
                    else:
                        params = dict(REFLEXO)
                    margem = MARGEM_SOMBRA(W0) if tipo == "sombra" else 0
                    h = hashlib.sha256(json.dumps([el["sha256"], tipo, params, margem], sort_keys=True).encode()).hexdigest()[:12]
                    chave = f"{it['id']}-{tipo}-{h}"
                    destino = pasta / f"{chave}.png"
                    if not destino.exists():
                        pasta.mkdir(parents=True, exist_ok=True)
                        origem = str(el["caminho"])
                        if margem:
                            from PIL import Image
                            ob = Image.open(origem).convert("RGBA")
                            larga = Image.new("RGBA", (ob.width + 2 * margem, ob.height), (0, 0, 0, 0))
                            larga.paste(ob, (margem, 0))
                            origem = str(pasta / f"{chave}-entrada.png")
                            larga.save(origem)
                        erro = _tratar(tipo, origem, str(destino), **params)
                        if margem:
                            Path(origem).unlink(missing_ok=True)
                        if erro:
                            erros.append(f"`{it['id']}`: {tipo} não gerado pelo tratar.py: {erro}")
                            continue
                    d = self.els.get(chave) or self._el_derivado(chave, destino, it["id"], tipo)
                    db = d.get("alfa_bbox")
                    if not db:
                        avs.append(f"`{it['id']}`: {tipo} sem área visível; fica fora")
                        continue
                    # coluna c do derivado = coluna c - margem do PNG de origem; a sombra começa no topo do PNG de
                    # origem, o reflexo na base da tinta
                    topo = oy if tipo == "sombra" else oy + float((el.get("tinta_bbox") or bb)[3]) * s
                    x = (float(it["x"]) + (bb[2] - (db[2] - margem)) * s) if esp else ox + (db[0] - margem) * s
                    y = topo + db[1] * s
                    w, hh = (db[2] - db[0]) * s, (db[3] - db[1]) * s
                    tb = d.get("tinta_bbox") or db
                    tx0 = (float(it["x"]) + (bb[2] - (tb[2] - margem)) * s) if esp else ox + (tb[0] - margem) * s
                    tinta = [round(tx0, 1), round(topo + tb[1] * s, 1), round(tx0 + (tb[2] - tb[0]) * s, 1), round(topo + tb[3] * s, 1)]
                    der = {"id": f"{it['id']}-{tipo}", "papel": "acabamento", "encaixe": "derivado", "camada": it["camada"],
                           "x": round(x, 1), "y": round(y, 1), "w": round(w, 1), "h": round(hh, 1), "rot": 0.0,
                           "origem": "composicao", "funcao": "acabamento", "derivado_de": it["id"], "el_id": chave,
                           "porque": (f"sombra de contato de `{it['id']}` (luz {luz})" if tipo == "sombra"
                                      else f"reflexo de piso de `{it['id']}`, topo na base da tinta"),
                           "ancora": {"relacao": "derivado", "de": it["id"], "restricoes": [], "tinta": tinta, "escala": None,
                                      "degrau": True, "declarada": {}}}
                    if esp:
                        der["espelhar"] = True
                    novos.append(der)
            res.extend(novos)

    def _esmaecido(self, el, esm, avisos):
        """efeito.esmaecer num PNG: o alfa ganha os degraus (tratar.alfa_degraus) num PNG derivado, cache por sha256 +
        esmaecer. Devolve (elemento derivado, chave) ou (o próprio elemento, None) se não deu."""
        var = hashlib.sha256(json.dumps([el["sha256"], esm], sort_keys=True).encode()).hexdigest()[:8]
        chave = f"{el['id']}-esm{var}"
        if chave in self.els:
            return self.els[chave], var
        destino = self.cache / "derivados" / f"{chave}.png"
        if not destino.exists():
            destino.parent.mkdir(parents=True, exist_ok=True)
            erro = _tratar("alfa_degraus", str(el["caminho"]), str(destino), esm.get("direcao"), int(esm.get("passos") or 0),
                           float(esm.get("minimo") or 0))
            if erro:
                avisos.append(f"elemento {el['id']}: esmaecer não aplicado: {erro}")
                return el, None
        d = self._el_derivado(chave, destino, el["id"], "esmaecer")
        # a caixa de corte é a do original: com minimo 0 o último degrau some e o alfa_bbox encolheria, esticando o PNG
        d.update(papel=el.get("papel"), papel_plano=el.get("papel_plano"), derivado_de=None, dims=el["dims"],
                 alfa_bbox=el.get("alfa_bbox"), tinta_bbox=el.get("tinta_bbox"))
        return d, var

    def _acabamento(self, med, receita):
        """O acabamento da camada frente nesta página (references/09): o grão do tema, se a página tem (lido do
        .pagina::after: opacidade, blend e tamanho do tile), e o `tingir` / a `temperatura` da receita, se ela declarar
        ({"cor", "forca", "preto"} e {"referencia": arquivo do kit, "forca"}). None = nada a aplicar."""
        ac = {}
        g = med.get("grao")
        if g and GRAO_TEMA.exists():
            try:
                tile = float(str(g.get("tamanho") or "512px").split()[0].replace("px", ""))
            except ValueError:
                tile = 512.0
            ac["grao"] = {"arquivo": str(GRAO_TEMA), "sha256": _sha256(GRAO_TEMA)[:12], "opacidade": g.get("opacidade", 0.5),
                          "blend": g.get("blend") or "soft-light", "tile": tile}
        r = receita or {}
        if r.get("tingir"):
            t = dict(r["tingir"])
            t.setdefault("cor", (r.get("paleta") or {}).get("marca"))
            ac["tingir"] = t
        if (r.get("temperatura") or {}).get("referencia"):
            tp = dict(r["temperatura"])
            try:
                tp["referencia"] = str(dentro_do_kit(self.pasta, tp["referencia"]))
            except ForaDoKit as erro:
                raise SystemExit(f"receita {r.get('id')}: temperatura.referencia {erro}. O render recusa: a foto seria lida de fora do kit")
            ac["temperatura"] = tp
        return ac or None

    def _preparar(self, itens, avisos, medidas=None, receita=None, maquete=False):
        """Um PNG de uso por elemento, formato e acabamento, na maior largura em que ele aparece (2x). Na camada frente
        o PNG leva o acabamento da página (grão, tingir, temperatura); nas outras camadas a própria página faz isso."""
        if maquete:
            return {}
        maior, acabs, fontes = {}, {}, {}
        for n, res in enumerate(itens):
            ac = self._acabamento(medidas[n], receita) if medidas else None
            for it in res:
                el = self._el(it)
                if not el or el["formato"] != "png":
                    continue
                esm = (it.get("efeito") or {}).get("esmaecer")
                var = None
                if esm:
                    el, var = self._esmaecido(el, esm, avisos)
                    if var:
                        it["variante_uso"] = var
                # textura já é o grão da área: não leva o acabamento da frente
                a_it = ac if (it["camada"] == "frente" and it["papel"] != "pattern" and not el.get("textura")) else None
                ch = chave_acabamento(a_it)
                if ch:
                    it["acabamento"] = ch
                uso = float(el.get("escala_tile") or 240) if it["papel"] == "pattern" else it["w"]
                k = chave_pronto(it)
                maior[k] = max(maior.get(k, 0), uso)
                acabs[k], fontes[k] = a_it, el
        prontos = {}
        for k, larg in sorted(maior.items(), key=lambda kv: (kv[0][0], kv[0][1] or "", kv[0][2] if len(kv[0]) > 2 else "")):
            rel, destino, cor = preparar_uso(fontes[k], larg, self.cache, self.pasta, avisos, acabs[k])
            prontos[k] = (rel, _data_uri(destino), cor)
        return prontos

    def _blend_textura(self, it, el, med, fundo):
        """Blend padrão da textura (papel acabamento sem alfa) pela área que ela cobre: soft-light sobre foto (metade ou
        mais da caixa dentro de uma foto da página, ou camada sob-veu), multiply no papel, screen no escuro."""
        if not el or not el.get("textura") or it.get("papel") != "acabamento":
            return None
        if it["camada"] == "sob-veu":
            return BLEND_TEXTURA["foto"]
        x0, y0, x1, y1 = float(it["x"]), float(it["y"]), float(it["x"]) + float(it["w"]), float(it["y"]) + float(it["h"])
        area = max(1.0, (x1 - x0) * (y1 - y0))
        for nome, f in (med.get("alvos") or {}).items():
            if (nome == "foto" or nome.startswith("foto:")) and isinstance(f, dict):
                ix = max(0.0, min(x1, f["x"] + f["w"]) - max(x0, f["x"]))
                iy = max(0.0, min(y1, f["y"] + f["h"]) - max(y0, f["y"]))
                if ix * iy >= 0.5 * area:
                    return BLEND_TEXTURA["foto"]
        return BLEND_TEXTURA.get(fundo or "escuro", "screen")

    def _nos(self, itens, medidas, prontos, svgs, svgs_pag=None, maquete=False, fundos=None):
        nos_pag = []
        for n, (res, med) in enumerate(zip(itens, medidas)):
            nos = {"sob-veu": [], "atras": [], "frente": [], "dentro-cena": []}
            cena0 = (med.get("cenas") or [None])[0]
            gerados = (svgs_pag[n] if svgs_pag else None) or {}
            for k, it in enumerate(ordem_de_pintura(res)):
                el = self._el(it)
                cam = it["camada"]
                dx = dy = 0.0
                if cam == "sob-veu" and cena0 and cena0.get("veu_interno"):
                    cam, dx, dy = "dentro-cena", cena0["x"], cena0["y"]
                pr = prontos.get(chave_pronto(it))
                if maquete:
                    nos[cam].append(html_maquete(it, dx=dx, dy=dy, largura=float(med.get("w") or 1920)))
                elif it["id"] in gerados:
                    # svg gerado para esta página (liga, grafismo na medida): ids únicos por página e por item
                    svg = _ids_unicos(gerados[it["id"]]["svg"], f"p{n + 1}-{k}")
                    nos[cam].append(html_item(it, el, svg=svg, dx=dx, dy=dy))
                elif it["id"] in svgs:
                    svg = _ids_unicos(svgs[it["id"]]["svg"], f"p{n + 1}")
                    nos[cam].append(html_item(it, el, svg=svg, dx=dx, dy=dy))
                elif pr and it.get("cruza") and cam == "frente":
                    # cruza: o MESMO data URI duas vezes, partido na linha medida: em cima na camada atras (sob o texto),
                    # embaixo na frente (sobre o texto)
                    y = it["cruza"]["corte_px"]
                    nos["atras"].append(html_item(it, el, src=pr[1], dx=dx, dy=dy, cor=pr[2], corte=("atras", y)))
                    nos[cam].append(html_item(it, el, src=pr[1], dx=dx, dy=dy, cor=pr[2], corte=("frente", y)))
                elif pr:
                    bp = self._blend_textura(it, el, med, (fundos or [None] * len(itens))[n])
                    nos[cam].append(html_item(it, el, src=pr[1], dx=dx, dy=dy, cor=pr[2], blend_padrao=bp))
            nos_pag.append(nos)
        return nos_pag

    def exportar(self, d, receita, pags, html, html_path, pdf_path, largura, altura, png_dir, prefixo, marca, exportar_fn,
                 formato="horizontal", maquete=False):
        """Duas passagens no mesmo HTML: mede sem elementos, resolve, injeta e exporta. Devolve as medidas do render final.
        maquete=True (render.py --maquete): cada elemento entra como caixa hachurada com rótulo no lugar resolvido, sem
        precisar do asset (proporção declarada), e o plano vai para saida/plano-maquete-<receita>.json."""
        cfg = {"w": largura, "h": altura, "seletores": encaixes.seletores(self.catalogo)}
        if self.usa_textos:
            cfg["textos"] = True      # o texto inteiro do título vai aos alvos (grafismo de texto_de titulo)
        html_path.write_text(html, encoding="utf-8")
        m1 = exportar_fn(html_path, None, largura, altura, None, prefixo, marca, extra=(JS_PROTEGIDOS, cfg))
        med1 = m1["extra"]
        paginas = self._paginas(pags, formato)
        if len(paginas) != len(med1):
            self.report["avisos"].append(f"{d} {formato}: {len(med1)} páginas no DOM e {len(paginas)} no plano; elementos fora")
            html_path.write_text(html, encoding="utf-8")
            m = exportar_fn(html_path, pdf_path, largura, altura, png_dir, prefixo, marca)
            return m
        avisos = []
        atrib, planejador = self._atribuidos(d, receita, paginas, pags, formato)
        atrib, comp_meta = self._aplicar_composicao(atrib, paginas, formato)
        ctx = contexto_grafismo(self.k, receita, self.pasta, self.fdir)
        dims, svgs = self._dims_e_svgs(atrib, ctx, avisos, paginas, largura, maquete, med1)
        zonas = zonas_da_foto(pags, med1, self.pasta, avisos)
        itens, avisos_pag, erros_pag, svgs_pag, av = self._resolver(atrib, paginas, med1, dims, svgs, largura, altura, ctx,
                                                                    zonas, maquete)
        avisos += av
        if not maquete:
            self._cruzar(itens, med1, erros_pag)
            self._derivados(itens, paginas, formato, erros_pag, avisos_pag)
        prontos = self._preparar(itens, avisos, med1, receita, maquete)
        fr = (receita or {}).get("fundo", "escuro")
        fundos = ([(fr if fr in ("papel", "cor") and p.get("plano") else "escuro") for p in pags]
                  if formato == "horizontal" else ["escuro"] * len(paginas))
        nos = self._nos(itens, med1, prontos, svgs, svgs_pag, maquete, fundos)
        if not maquete:
            self.injecoes[(d, formato)] = nos
        html_path.write_text(injetar(html, nos), encoding="utf-8")
        m2 = exportar_fn(html_path, pdf_path, largura, altura, png_dir, prefixo, marca, extra=(JS_PROTEGIDOS, cfg))
        med2 = m2.pop("extra")
        self._gravar(d, receita, formato, paginas, itens, prontos, svgs, med1, med2, avisos, avisos_pag, planejador, largura, altura,
                     comp_meta, erros_pag, zonas, svgs_pag, maquete)
        if formato == "horizontal" and not maquete:
            for p, res in zip(pags, itens):
                p["_elementos"] = res
        return m2

    def injetar_fundo(self, d, html, formato="horizontal"):
        """--fundo (PPTX): o mesmo plano, sem medir de novo (o layout do modo sem texto é o mesmo)."""
        nos = self.injecoes.get((d, formato))
        return injetar(html, nos) if nos else html

    def _gravar(self, d, receita, formato, paginas, itens, prontos, svgs, med1, med2, avisos, avisos_pag, planejador, W, H,
                comp_meta=None, erros_pag=None, zonas=None, svgs_pag=None, maquete=False):
        pags_out = []
        mudou = []
        comp_meta = comp_meta or [None] * len(paginas)
        erros_pag = erros_pag or [[] for _ in paginas]
        zonas = zonas or [[] for _ in paginas]
        svgs_pag = svgs_pag or [{} for _ in paginas]
        for p, res, m1, m2, av, cm, ec, zs, gerados in zip(paginas, itens, med1, med2, avisos_pag, comp_meta, erros_pag, zonas, svgs_pag):
            if _assinatura(m1["protegidos"]) != _assinatura(m2["protegidos"]):
                mudou.append(p["n"])
            els_out = []
            for it in res:
                el = self._el(it) or {}
                g = gerados.get(it["id"]) or svgs.get(it["id"])
                pr = prontos.get(chave_pronto(it))
                ef = _efeito_valido(it.get("efeito"))
                o = dict(it, formato=el.get("formato") or ("svg" if g is not None else None),
                         uso=pr[0] if pr else None,
                         sha256=el.get("sha256") or (hashlib.sha256(g["svg"].encode()).hexdigest() if g is not None else None),
                         arquivo=el.get("arquivo"), alfa_bbox=list(el["alfa_bbox"]) if el.get("alfa_bbox") else None,
                         # efeito da composição vence o elemento (mk-2.1); sem efeito, igual a antes
                         opacidade=ef["opacidade"] if "opacidade" in ef else el.get("opacidade", 1),
                         blend=ef.get("blend") or el.get("blend") or "normal",
                         cor_chapada=pr[2] if pr else None)
                if self.usa_acab and o.get("motivo") is None and el.get("motivo") and it.get("origem") == "composicao":
                    o["motivo"] = el["motivo"]     # o QA lê o motivo do item: o da composição, senão o de elementos[]
                if g is not None:
                    o["texto"] = g.get("texto")
                if it["papel"] == "pattern":
                    o["escala_tile"] = el.get("escala_tile") or 240
                els_out.append(o)
            elegivel = any("heroi" in e.get("papeis", []) for e in self.catalogo.get(p["rotulo"], []))
            pags_out.append({"n": p["n"], "rotulo": p["rotulo"], "tipo": p["tipo"], "rotulos": sorted(p.get("_rotulos") or []),
                             "elegivel_heroi": elegivel,
                             "elementos": els_out, "protegidos": m2["protegidos"], "avisos": av,
                             # alvos do render FINAL: o QA confere a âncora contra eles, não contra a medição do plano
                             "alvos": m2.get("alvos") or {}, "composicao": cm, "erros_composicao": ec,
                             # zonas protegidas dentro da foto (painel do compor.py e foco): classe vendavel no QA
                             "vendaveis": zs,
                             # caixa de cada elemento no DOM do render final (girado = caixa alinhada aos eixos): prova de
                             # que o que foi desenhado é o que o plano diz
                             "dom": m2.get("elementos") or []})
        if mudou:
            avisos.append(f"layout mudou entre a medição e o render final nas páginas {mudou}: confira o plano")
        rid = (receita or {}).get("id") or d
        nome = f"plano-{'maquete' if maquete else 'elementos'}-{d}{'-vertical' if formato == 'vertical' else ''}.json"
        plano = {"receita": rid, "formato": formato, "largura": W, "altura": H, "planejador": planejador,
                 "grafismos": self.nome_gerador, "paginas": pags_out, "avisos": avisos,
                 "composicao_erros": list(self.erros_composicao),
                 # kit com composição: elemento do catálogo sem âncora vira FALHA no QA (kit legado: aviso)
                 "composicao_kit": bool(self.composicao), "maquete": bool(maquete)}
        (self.saida / nome).write_text(json.dumps(plano, ensure_ascii=False, indent=1), encoding="utf-8")
        rotulo = f"{'maquete' if maquete else 'elementos'} {d}{' vertical' if formato == 'vertical' else ''}"
        for a in avisos + [x for av in avisos_pag for x in av]:
            self.report["avisos"].append(f"{rotulo}: {a}")
        self.resumos.setdefault(d, {})[formato] = {"plano": f"saida/{nome}", "planejador": planejador, "grafismos": self.nome_gerador,
                                                   "itens": sum(len(r) for r in itens)}


def _assinatura(prot):
    return sorted((p["classe"], round(p["x"]), round(p["y"]), round(p["w"]), round(p["h"])) for p in prot)

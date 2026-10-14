#!/usr/bin/env python3
"""
padrao.py: patterns e ornamentos gerados por IA (references/07-elementos.md). Mede, corrige e prepara o que o
elementos.sh trouxe do Codex, antes de entrar na página.

Comandos:
  alfa      <png>                                   mede se o PNG tem alfa REAL (sai 0 = sim, 1 = não). Regra: pelo menos
                                                    5% dos pixels com A < 250 e pelo menos 1% opaco (A > 5).
  separar   <entrada> <saida.png>                   pattern sem alfa: tira o fundo chapado pela cor (chroma). A cor do fundo é a
                                                    mais frequente da imagem; o alfa é a distância a ela, normalizada pela tinta
                                                    (percentil 95), e a cor é "despremultiplicada" (sem halo do fundo).
  checar    <tile.png> [--limite 0.7] [--mosaico m.png]
                                                    mede a costura e grava o mosaico 2×2 para olhar. Imprime o número e sai 1
                                                    quando reprova.
  tornar-seamless <entrada> <saida> [--metodo costurar|cruzar|espelho] [--faixa .2]
                                                    corrige a costura (ver abaixo).
  variantes <tile> --paleta "#D4A64A,#0B0B0C" --saida <pasta>
                                                    <id>-traco.png (alfa só nas linhas, na cor), <id>-chapado.png (silhueta
                                                    sólida: buracos pequenos preenchidos), <id>-tingido.png (LUT do tratar.py
                                                    tingir, alfa preservado). Da 2ª cor em diante: sufixo -c2, -c3.
  folha     <elementos.json> <saida.png> [--kit <pasta>]
                                                    folha de revisão: cada elemento sobre preto e sobre branco (halo aparece),
                                                    pattern em mosaico 2×2.
  texto     <png> [--json]                          OCR (tesseract): lista o que leu e REPROVA (sai 1) se houver palavra acima do
                                                    limite calibrado. Elemento de IA não pode ter texto (aprendizado 7); texto
                                                    só por grafismo (grafismos.py, texto vivo).
  preparar_uso <png> <largura> <saida>              corta no alfa_bbox e reduz para 2× a largura de uso (nunca amplia); imprime
                                                    e devolve o sha256 do PNG gravado (o render guarda em saida/cache-elementos/).
  calibrar-texto [png ou pasta ...]                 reproduz a calibração do OCR: positivos sintéticos (fontes-livres) contra
                                                    os PNGs dados como negativos.

COMO A COSTURA É MEDIDA (checar). O tile é composto sobre cinza médio (o alfa conta) e convertido para Lab. Por eixo:
emenda = diferença média entre a última coluna e a primeira (o par que fica lado a lado quando o tile se repete);
vizinhos = diferença média entre colunas vizinhas dentro do tile; aleatório = diferença média entre colunas a meio tile
de distância (pares sem relação nenhuma). Índice = (emenda − vizinhos) / (aleatório − vizinhos): 0 quer dizer que a
emenda é tão contínua quanto o resto do desenho, 1 quer dizer tão descasada quanto duas colunas sem relação. A costura
do tile é o maior índice entre horizontal e vertical. Normalizar assim é o que faz o número valer igual para traço fino
(vizinhos já variam muito) e para textura lisa (vizinhos quase iguais); a 1ª versão, razão emenda/vizinhos, dava 0,4 a
19 e não separava traço fino.
Calibração (09/10/2026, `padrao.py calibrar` reproduz; 40 sementes de traço fino e 18 de ruído medidas à parte):
tiles periódicos (ruído filtrado no domínio da frequência em 4 escalas, traço fino desenhado com volta, listras)
ficaram entre 0 e 0,62; os mesmos desenhos sem periodicidade, entre 0,76 e 1,44. Limite: 0,7. A faixa 0,5 a 0,8 é
zona cinzenta (uma linha que cai exatamente na borda sobe o índice de um tile bom): ali quem decide é o mosaico.

COMO A COSTURA É CORRIGIDA (tornar-seamless).
  Só os eixos com índice acima de 0,5 (a zona cinzenta) são mexidos: corrigir eixo que já emenda só piora.
  costurar (padrão): corte de menor erro do "Image Quilting" (Efros e Freeman, 2001). Mesma cópia deslocada do
  cruzar, mas em vez de misturar, troca de imagem numa fronteira escolhida por programação dinâmica onde as duas mais
  se parecem; em traço fino ela passa pelo vazio entre as linhas e não deixa fantasma. Custo: onde não há caminho
  livre, uma linha pode terminar seca na fronteira (aparece no mosaico).
  cruzar: método clássico do deslocamento de meio tile. Para cada eixo, a cópia deslocada em meio tile tem as
  bordas contínuas (as bordas dela são o miolo do original) e a costura no centro. Mistura-se: perto da borda vale a
  cópia deslocada, no miolo vale o original, numa rampa suave de largura `--faixa` (fração do lado, ≤ .5). A costura da
  cópia fica no miolo, onde o peso dela é zero. Custo: na faixa aparecem as duas imagens sobrepostas (fantasma); traço
  fino fica com linhas a meia opacidade ali.
  espelho: monta um tile 2× maior com o original e os espelhos horizontal, vertical e duplo. Emenda perfeita sempre, mas
  o desenho fica simétrico (caleidoscópio); use quando o fantasma do cruzar aparecer.

COMO O TEXTO É PROCURADO (texto). O PNG é composto sobre branco e sobre preto (este invertido, para letra clara virar
escura), em 2 escalas (1 e 0,5) e 3 giros (0, -15 e +15 graus: texto inclinado só é lido quando o giro o endireita),
12 passadas do tesseract em modo de texto esparso (--psm 11, por+eng). Reprova a palavra com 3 ou mais letras ou
algarismos lida com confiança >= 75; a de 2 caracteres só com confiança >= 90 E lida em 3 ou mais passadas (texto de
verdade reaparece; a sílaba inventada numa textura aparece em uma só). Caractere solto não conta: o tesseract "lê"
letra isolada em qualquer textura, até 96 de confiança.
Calibração (09/10/2026, `padrao.py calibrar-texto` reproduz): 17 positivos sintéticos ("SPRINT" em 5 fontes, 3 corpos
e 3 cores, "SPRINT" girado 15 graus, "2027") todos reprovados, com confiança de 90,7 a 96,8; 12 negativos reais (os 6
elementos da Sprint e os 6 objetos do teste de âncora, sem texto) todos aprovados: no máximo 68,8 nas palavras de 3+
caracteres e 91,2 nas de 2, esta numa passada só. "SPRINT" de 34 px escrito sobre a medalha é pego ("SP" 94,2 em 4
passadas). Limite conhecido: letra sobre textura carregada pode escapar ("UBATUBSN RUN" de 60 px sobre as penas da
medalha saiu só em fragmentos, 68,8, e passa). A régua pega texto chapado e legível, que é o caso comum do gerador
escrevendo em painel, rótulo ou objeto liso; texto sobre textura fica para o olho na folha de revisão.
"""
import argparse, csv, hashlib, io, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).parent
LIMITE_COSTURA = 0.7
ZONA_CINZA = 0.5  # acima disto o eixo é corrigido pelo tornar-seamless, mesmo aprovado no checar


def hex_rgb(h):
    h = h.strip().lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgba(caminho):
    return Image.open(caminho).convert("RGBA")


# ---------------------------------------------------------------- alfa
def medir_alfa(caminho):
    im = Image.open(caminho)
    modo = im.mode
    if "A" not in modo and not (modo == "P" and "transparency" in im.info):
        return False, dict(modo=modo, transparente=0.0, opaco=1.0)
    a = np.asarray(im.convert("RGBA"))[..., 3]
    transp = float((a < 250).mean()); opaco = float((a > 5).mean())
    return (transp >= 0.05 and opaco >= 0.01), dict(modo=modo, transparente=round(transp, 3), opaco=round(opaco, 3))


def cmd_alfa(a):
    ok, m = medir_alfa(a.png)
    print(f"ALFA: {'sim' if ok else 'não'} (modo {m['modo']}, fração com A<250 = {m['transparente']}, fração com A>5 = {m['opaco']})")
    sys.exit(0 if ok else 1)


# ---------------------------------------------------------------- separar (chroma)
def cor_de_fundo(rgb):
    q = (rgb // 8).reshape(-1, 3).astype(np.int32)
    chave = q[:, 0] * 1024 + q[:, 1] * 32 + q[:, 2]
    moda = np.bincount(chave).argmax()
    sel = chave == moda
    return rgb.reshape(-1, 3)[sel].mean(axis=0)


def separar(entrada, saida, fundo_alvo=None):
    """Tira o fundo chapado pela cor. `fundo_alvo` (#RRGGBB) é a cor que o prompt pediu (o elementos.sh passa o branco
    no caminho codex-branco): o fundo vira a média dos pixels perto dela. Sem ele, a cor mais frequente, o que falha
    quando a tinta cobre a maior parte do tile (o pattern de ondas da Sprint perdia o azul e ficava só a espuma)."""
    rgb = np.asarray(Image.open(entrada).convert("RGB"), dtype=float)
    if fundo_alvo:
        alvo = np.array([int(fundo_alvo.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)], float)
        perto = np.linalg.norm(rgb - alvo, axis=2) < 48
        fundo = rgb[perto].mean(axis=0) if perto.mean() >= 0.01 else alvo
    else:
        fundo = cor_de_fundo(rgb)
    dist = np.linalg.norm(rgb - fundo, axis=2)
    tinta = max(np.percentile(dist, 95), 30.0)
    alfa = np.clip(dist / tinta, 0, 1)
    alfa[alfa < 0.08] = 0  # ruído de compressão no fundo
    seguro = np.maximum(alfa, 1e-3)[..., None]
    cor = np.clip(fundo + (rgb - fundo) / seguro, 0, 255)  # despremultiplica: tira o fundo misturado na borda
    out = np.dstack([cor, alfa * 255]).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(saida, optimize=True)
    print(f"OK {saida} fundo={'#%02X%02X%02X' % tuple(int(v) for v in fundo)} transparente={float((alfa == 0).mean()):.2f}")


# ---------------------------------------------------------------- checar
def _lab_sobre_cinza(im):
    arr = np.asarray(im, dtype=float)
    a = arr[..., 3:4] / 255.0
    comp = arr[..., :3] * a + 128 * (1 - a)
    return np.asarray(Image.fromarray(comp.astype(np.uint8), "RGB").convert("LAB"), dtype=float)


def medir_costura(im):
    """Índice de costura por eixo: (emenda − vizinhos) / (aleatório − vizinhos), sobre o Lab composto em cinza.
    emenda = diferença média entre a última coluna e a primeira (o par que fica lado a lado quando o tile se repete);
    vizinhos = diferença média entre colunas vizinhas dentro do tile; aleatório = diferença média entre colunas a meio
    tile de distância (pares sem relação). 0 = a emenda é tão contínua quanto o resto; 1 = tão descasada quanto duas
    colunas sem relação. Textura chapada (aleatório ≈ vizinhos) não tem como mostrar costura: índice 0."""
    lab = _lab_sobre_cinza(im)
    def indice(eixo):
        x = lab if eixo == 1 else lab.transpose(1, 0, 2)
        n = x.shape[1]
        emenda = np.abs(x[:, -1] - x[:, 0]).mean()
        vizinhos = np.abs(np.diff(x, axis=1)).mean()
        aleatorio = np.abs(x - np.roll(x, n // 2, axis=1)).mean()
        escala = aleatorio - vizinhos
        if escala < 0.5:
            return 0.0, emenda, vizinhos, aleatorio
        return max(0.0, (emenda - vizinhos) / escala), emenda, vizinhos, aleatorio
    h = indice(1); v = indice(0)
    return dict(horizontal=round(h[0], 2), vertical=round(v[0], 2), costura=round(max(h[0], v[0]), 2),
                abs_h=round(h[1], 1), abs_v=round(v[1], 1), vizinhos=round((h[2] + v[2]) / 2, 1), aleatorio=round((h[3] + v[3]) / 2, 1))


def mosaico(im, n=2, lado_max=1600, fundo=(255, 255, 255)):
    W, H = im.size
    m = Image.new("RGBA", (W * n, H * n), fundo + (255,))
    for i in range(n):
        for j in range(n):
            m.alpha_composite(im, (i * W, j * H))
    if m.width > lado_max:
        m = m.resize((lado_max, round(m.height * lado_max / m.width)), Image.LANCZOS)
    return m.convert("RGB")


def cmd_checar(a):
    im = rgba(a.tile)
    r = medir_costura(im)
    destino = a.mosaico or str(Path(a.tile).with_suffix("")) + ".mosaico.png"
    mosaico(im).save(destino, optimize=True)
    ok = r["costura"] <= a.limite
    print(f"COSTURA {r['costura']} (horizontal {r['horizontal']}, vertical {r['vertical']}; limite {a.limite}) "
          f"{'APROVADO' if ok else 'REPROVADO'}  | Lab: emenda h {r['abs_h']}, v {r['abs_v']}, vizinhos {r['vizinhos']} | mosaico: {destino}")
    sys.exit(0 if ok else 1)


# ---------------------------------------------------------------- tornar-seamless
def _rampa(n, faixa):
    """Peso do ORIGINAL ao longo de um eixo: 0 na borda, 1 a partir de `faixa`·n da borda (smoothstep)."""
    d = np.minimum(np.arange(n), np.arange(n)[::-1]) + 0.5
    t = np.clip(d / max(1.0, faixa * n), 0, 1)
    return t * t * (3 - 2 * t)


def cruzar(arr, faixa=0.2, eixos=(1, 0)):
    faixa = min(max(faixa, 0.05), 0.5)
    out = arr.astype(float)
    for eixo in eixos:
        n = out.shape[eixo]
        deslocado = np.roll(out, n // 2, axis=eixo)
        w = _rampa(n, faixa)
        w = w[None, :, None] if eixo == 1 else w[:, None, None]
        out = out * w + deslocado * (1 - w)
    return np.clip(out, 0, 255).astype(np.uint8)


def _caminho_minimo(custo, fechado=True):
    """Caminho vertical de menor custo (programação dinâmica, passo de no máximo 1 coluna por linha). `fechado`: o
    caminho começa e termina na mesma coluna, senão a troca de imagem fica descasada na OUTRA emenda (o tile também se
    repete na direção do caminho; medido no penas-asa: sem isto, corrigir o vertical reabria o horizontal, 0,8)."""
    H, B = custo.shape
    def dp(c0):
        M = custo.copy(); de = np.zeros((H, B), int)
        if c0 is not None:
            M[0] = np.inf; M[0, c0] = custo[0, c0]
        for i in range(1, H):
            esq = np.r_[np.inf, M[i - 1, :-1]]; dir_ = np.r_[M[i - 1, 1:], np.inf]
            tri = np.vstack([esq, M[i - 1], dir_])
            k = tri.argmin(axis=0); de[i] = np.arange(B) + k - 1; M[i] += tri[k, np.arange(B)]
        cam = np.zeros(H, int); cam[-1] = c0 if c0 is not None else M[-1].argmin()
        for i in range(H - 1, 0, -1):
            cam[i - 1] = de[i, cam[i]]
        return cam
    cam = dp(None)
    return dp(int(cam[-1])) if fechado else cam


def costurar(arr, faixa=0.2, eixos=(1, 0)):
    """Corte de menor erro (Efros e Freeman, "Image Quilting", 2001): em vez de misturar as duas imagens na faixa da
    borda (o que deixa fantasma), escolhe dentro da faixa a fronteira por onde original e cópia deslocada mais se
    parecem, e troca de uma para a outra ali. Em traço fino, a fronteira passa pelo vazio entre as linhas."""
    faixa = min(max(faixa, 0.05), 0.45)
    out = arr.astype(float)
    for eixo in eixos:
        x = out if eixo == 1 else out.transpose(1, 0, 2)
        H, W = x.shape[:2]; B = max(8, int(faixa * W))
        desl = np.roll(x, W // 2, axis=1)
        def cinza(v):
            a = v[..., 3:4] / 255.0; return (v[..., :3] * a + 128 * (1 - a)).mean(axis=2)
        dif = np.abs(cinza(x) - cinza(desl))
        usa_desl = np.zeros((H, W), float)
        cam = _caminho_minimo(dif[:, 1:B - 1]) + 1          # faixa da esquerda: à esquerda do caminho, a cópia
        usa_desl[np.arange(W)[None, :] < cam[:, None]] = 1
        cam = _caminho_minimo(dif[:, W - B + 1:W - 1]) + W - B + 1   # faixa da direita: à direita do caminho, a cópia
        usa_desl[np.arange(W)[None, :] > cam[:, None]] = 1
        from PIL import ImageFilter
        m = np.asarray(Image.fromarray((usa_desl * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1)), float)[..., None] / 255
        x = x * (1 - m) + desl * m
        out = x if eixo == 1 else x.transpose(1, 0, 2)
    return np.clip(out, 0, 255).astype(np.uint8)


def espelho(arr):
    topo = np.concatenate([arr, arr[:, ::-1]], axis=1)
    return np.concatenate([topo, topo[::-1]], axis=0)


def cmd_seamless(a):
    im = rgba(a.entrada); arr = np.asarray(im)
    m = medir_costura(im); antes = m["costura"]
    # só o eixo que reprova é misturado: cruzar um eixo que já emenda só acrescenta fantasma (medido no ondas-serra:
    # vertical 0,0 virou 0,44 quando os dois eixos eram cruzados)
    eixos = tuple(e for e, k in ((1, "horizontal"), (0, "vertical")) if m[k] > ZONA_CINZA) or (1, 0)
    novo = {"costurar": lambda: costurar(arr, a.faixa, eixos), "cruzar": lambda: cruzar(arr, a.faixa, eixos), "espelho": lambda: espelho(arr)}[a.metodo]()
    out = Image.fromarray(novo, "RGBA"); out.save(a.saida, optimize=True)
    print(f"OK {a.saida} método={a.metodo} costura {antes} → {medir_costura(out)['costura']}")


# ---------------------------------------------------------------- variantes
def chapado(alfa, area_max=0.02):
    import cv2
    tinta = (alfa > 0.3 * 255).astype(np.uint8)
    tinta = cv2.morphologyEx(tinta, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, rot, est, _ = cv2.connectedComponentsWithStats(1 - tinta, connectivity=4)
    limite = area_max * alfa.size
    buracos = [i for i in range(1, n) if est[i, cv2.CC_STAT_AREA] < limite]
    cheio = tinta.astype(bool) | np.isin(rot, buracos)
    return (cheio * 255).astype(np.uint8)


def variantes(tile, paleta, saida):
    sys.path.insert(0, str(AQUI)); import tratar
    im = rgba(tile); arr = np.asarray(im); alfa = arr[..., 3]
    stem = Path(tile).stem.replace(".bruto", "").replace("-seamless", "")
    Path(saida).mkdir(parents=True, exist_ok=True)
    feitos = []
    for k, cor in enumerate(paleta):
        suf = "" if k == 0 else f"-c{k + 1}"
        r, g, b = hex_rgb(cor)
        traco = np.dstack([np.full_like(alfa, r), np.full_like(alfa, g), np.full_like(alfa, b), alfa])
        p = Path(saida) / f"{stem}-traco{suf}.png"; Image.fromarray(traco, "RGBA").save(p, optimize=True); feitos.append(p)
        sil = chapado(alfa)
        chap = np.dstack([np.full_like(alfa, r), np.full_like(alfa, g), np.full_like(alfa, b), sil])
        p = Path(saida) / f"{stem}-chapado{suf}.png"; Image.fromarray(chap, "RGBA").save(p, optimize=True); feitos.append(p)
    tmp_in = Path(saida) / f".{stem}-rgb.png"; tmp_out = Path(saida) / f".{stem}-ting.png"
    im.convert("RGB").save(tmp_in)
    tratar.tingir(str(tmp_in), str(tmp_out), paleta[0], forca=1.0)
    ting = Image.open(tmp_out).convert("RGB"); ting.putalpha(Image.fromarray(alfa))
    p = Path(saida) / f"{stem}-tingido.png"; ting.save(p, optimize=True); feitos.append(p)
    tmp_in.unlink(); tmp_out.unlink()
    for f in feitos:
        print("OK", f)
    return feitos


def cmd_variantes(a):
    variantes(a.tile, [c for c in a.paleta.split(",") if c.strip()], a.saida)


# ---------------------------------------------------------------- folha
def _fonte(tam):
    try:
        return ImageFont.load_default(tam)
    except TypeError:
        return ImageFont.load_default()


def _caber(im, lado):
    im = im.copy(); im.thumbnail((lado, lado), Image.LANCZOS); return im


def folha(entradas, kit, saida, celula=460):
    linhas = []
    for e in entradas:
        arq = Path(kit) / e["arquivo"]
        if not arq.exists():
            print(f"!! {e['id']}: {arq} não existe", file=sys.stderr); continue
        im = rgba(arq)
        if e.get("papel") == "pattern":
            # mosaico 2x2 no tamanho em que a página usa o tile (escala_tile), sobre preto e sobre branco
            esc = int(e.get("escala_tile") or 360)
            t = im.resize((esc, round(im.height * esc / im.width)), Image.LANCZOS)
            vistas = [mosaico(t, 2, celula, f) for f in ((0, 0, 0), (255, 255, 255))]
            info = f"pattern  costura {medir_costura(im)['costura']}  escala {esc}px"
        else:
            o = _caber(im, celula - 20); vistas = []
            for f in ((0, 0, 0), (255, 255, 255)):
                c = Image.new("RGBA", (celula, celula), f + (255,))
                c.alpha_composite(o, ((celula - o.width) // 2, (celula - o.height) // 2)); vistas.append(c.convert("RGB"))
            info = f"ornamento  alfa {'real' if medir_alfa(arq)[0] else 'NÃO'}"
        linhas.append((e, vistas, info))
    W = 2 * celula + 3 * 20 + 360
    H = len(linhas) * (celula + 20) + 20
    F = Image.new("RGB", (W, H), (40, 40, 40)); d = ImageDraw.Draw(F)
    for k, (e, vistas, info) in enumerate(linhas):
        y = 20 + k * (celula + 20)
        for i, v in enumerate(vistas):
            F.paste(v, (20 + i * (celula + 20), y + (celula - v.height) // 2))
        x = 2 * celula + 60
        d.text((x, y + 10), e["id"], fill=(255, 255, 255), font=_fonte(30))
        d.text((x, y + 56), info, fill=(200, 200, 200), font=_fonte(18))
        d.text((x, y + 86), f"rota {e.get('rota', '?')}", fill=(200, 200, 200), font=_fonte(18))
        d.text((x, y + 116), Path(e["arquivo"]).name, fill=(160, 160, 160), font=_fonte(16))
    F.save(saida, optimize=True); print("OK", saida, F.size)


def cmd_folha(a):
    entradas = json.loads(Path(a.json).read_text())
    entradas = entradas.get("elementos", entradas) if isinstance(entradas, dict) else entradas
    kit = a.kit or Path(a.json).resolve().parent.parent.parent
    folha(entradas, kit, a.saida)


# ---------------------------------------------------------------- texto (OCR)
OCR_LIMITE = 75.0          # palavra com 3+ letras ou algarismos
OCR_LIMITE_CURTA = 90.0    # palavra com 2, que ainda precisa aparecer em OCR_PASSADAS_CURTA passadas
OCR_PASSADAS_CURTA = 3
OCR_GIROS = (0, -15, 15)
OCR_ESCALAS = (1.0, 0.5)


def _ocr_passadas(im):
    a = np.asarray(im.convert("RGBA"), float)
    al = a[..., 3:4] / 255
    sobre_branco = Image.fromarray((a[..., :3] * al + 255 * (1 - al)).astype(np.uint8)).convert("L")
    sobre_preto = Image.fromarray((255 - a[..., :3] * al).astype(np.uint8)).convert("L")   # invertido: letra clara vira escura
    for nome, g in (("sobre-branco", sobre_branco), ("sobre-preto", sobre_preto)):
        for e in OCR_ESCALAS:
            ge = g if e == 1 else g.resize((max(1, round(g.width * e)), max(1, round(g.height * e))), Image.LANCZOS)
            for giro in OCR_GIROS:
                gg = ge.rotate(giro, expand=True, fillcolor=255, resample=Image.BILINEAR) if giro else ge
                yield f"{nome} x{e:g} {giro:+d}", gg


def _tesseract(img):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "p.png"; img.save(p)
        r = subprocess.run(["tesseract", str(p), "stdout", "--psm", "11", "-l", "por+eng", "tsv"], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"tesseract falhou: {r.stderr.strip()[:200]}")
    out = []
    for row in csv.DictReader(io.StringIO(r.stdout), delimiter="\t", quoting=csv.QUOTE_NONE):
        t = (row.get("text") or "").strip()
        if row.get("level") == "5" and t and float(row.get("conf") or -1) >= 0:
            out.append((t, round(float(row["conf"]), 1)))
    return out


def ler_texto(caminho):
    """Todas as palavras que o tesseract lê nas 12 passadas: [(palavra, confiança, passada)]."""
    if not shutil.which("tesseract"):
        raise RuntimeError("tesseract não encontrado (brew install tesseract tesseract-lang)")
    from concurrent.futures import ThreadPoolExecutor
    passadas = list(_ocr_passadas(Image.open(caminho)))
    with ThreadPoolExecutor(max_workers=4) as ex:
        res = list(ex.map(lambda p: [(w, c, p[0]) for w, c in _tesseract(p[1])], passadas))
    return [x for r in res for x in r]


def _caracteres(w):
    return len(re.sub(r"[^0-9A-Za-zÀ-ÿ]", "", w))


def _chave(w):
    return re.sub(r"[^0-9A-Za-zÀ-ÿ]", "", w).upper()


def julgar_texto(achados, limite=OCR_LIMITE, limite_curta=OCR_LIMITE_CURTA, passadas_curta=OCR_PASSADAS_CURTA):
    """Palavras que reprovam: 3+ caracteres com confiança >= limite; 2 caracteres com confiança >= limite_curta E lida
    em pelo menos `passadas_curta` passadas (texto de verdade reaparece nas passadas; a sílaba que o OCR inventa numa
    textura aparece em uma só). Caractere solto não conta."""
    passadas = {}
    for w, c, p in achados:
        passadas.setdefault(_chave(w), set()).add(p)
    return [(w, c, p) for w, c, p in achados
            if (_caracteres(w) >= 3 and c >= limite)
            or (_caracteres(w) == 2 and c >= limite_curta and len(passadas[_chave(w)]) >= passadas_curta)]


def _juntar(ruins):
    return " ".join(dict.fromkeys(w for w, _, _ in sorted(ruins, key=lambda x: -x[1])))


def texto(caminho, limite=OCR_LIMITE, limite_curta=OCR_LIMITE_CURTA):
    """O texto que a IA escreveu na imagem, pelas regras calibradas do julgar_texto: "" quando aprova. É o que a
    biblioteca grava em `ocr` (vazio = sem texto; preenchido = elemento bloqueado). Sem tesseract: RuntimeError."""
    return _juntar(julgar_texto(ler_texto(caminho), limite, limite_curta))


def revisao_vale(caminho, lido, revisao):
    """A revisão registrada (ocr_revisado na ficha do elemento) só vale para a MESMA imagem (sha256) e a MESMA leitura:
    imagem trocada ou leitura nova pedem outra revisão."""
    if not revisao or revisao.get("veredito") != "sem texto" or not lido:
        return False
    sha = hashlib.sha256(Path(caminho).read_bytes()).hexdigest()
    return revisao.get("sha256") == sha and _chave(revisao.get("lido") or "") == _chave(lido)


def revisar_texto(caminho, evidencia, por="Claude"):
    """Registra na ficha do elemento (<id>.meta.json) que a leitura do OCR foi conferida à mão e não é texto (falso
    positivo de textura, como os pontos de meio-tom). Grava a leitura exata e o sha256 da imagem; o checar da biblioteca
    continua avisando. Decisão do Ugo em 09/10/2026: revisão registrada em vez de afrouxar o leitor."""
    from datetime import date
    caminho = Path(caminho)
    lido = texto(caminho)
    if not lido:
        return None
    if not evidencia or len(evidencia.strip()) < 20:
        raise ValueError("revisão sem evidência: descreva o que o recorte ampliado mostra (no mínimo 20 caracteres)")
    ficha = caminho.with_suffix(".meta.json")
    meta = json.loads(ficha.read_text(encoding="utf-8")) if ficha.is_file() else {}
    meta["ocr_revisado"] = {"lido": lido, "sha256": hashlib.sha256(caminho.read_bytes()).hexdigest(), "veredito": "sem texto",
                            "por": por, "em": date.today().isoformat(), "evidencia": evidencia.strip()}
    ficha.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return meta["ocr_revisado"]


def cmd_revisar_texto(a):
    r = revisar_texto(a.png, a.evidencia, a.por)
    print("nada a revisar: o OCR não leu texto nesta imagem" if r is None else
          f"REVISADO  lido {r['lido']!r} conferido à mão: sem texto ({r['por']}, {r['em']}); ficha {Path(a.png).with_suffix('.meta.json').name}")


def cmd_texto(a):
    achados = ler_texto(a.png)
    ruins = julgar_texto(achados, a.limite, a.limite_curta)
    lidas = sorted({(w, c) for w, c, _ in achados if _caracteres(w) >= 2}, key=lambda x: -x[1])
    texto = _juntar(ruins)
    if a.json:
        print(json.dumps({"png": str(a.png), "ocr": texto, "aprovado": not ruins,
                          "reprovam": [{"palavra": w, "confianca": c, "passada": p} for w, c, p in ruins],
                          "lidas": [{"palavra": w, "confianca": c} for w, c in lidas[:12]]}, ensure_ascii=False))
    elif ruins:
        print(f"TEXTO: REPROVADO  encontrado: {texto}  ({', '.join(f'{w} {c:g}' for w, c, _ in sorted(ruins, key=lambda x: -x[1])[:6])}; "
              f"limites {a.limite:g} e {a.limite_curta:g})")
    else:
        maior = ", ".join(f"{w} {c:g}" for w, c in lidas[:4]) or "nada"
        print(f"TEXTO: APROVADO  nenhuma palavra acima dos limites ({a.limite:g} para 3+ caracteres, {a.limite_curta:g} para 2); "
              f"o mais confiante que o OCR achou: {maior}")
    sys.exit(1 if ruins else 0)


def _positivo(texto, fonte, tam, cor, giro=0):
    from PIL import ImageFont
    f = ImageFont.truetype(str(fonte), tam)
    im = Image.new("RGBA", (int(tam * len(texto) * 0.9) + 80, int(tam * 1.8) + 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((40, 20), texto, font=f, fill=cor)
    return im.rotate(giro, expand=True, resample=Image.BICUBIC) if giro else im


def calibrar_texto(negativos):
    fl = AQUI.parent / "fontes-livres"
    fontes = ["Anton/Anton.ttf", "Kanit/Kanit__800.ttf", "Fraunces/Fraunces__800.ttf", "Barlow/Barlow.ttf", "Outfit/Outfit__700.ttf"]
    casos = []
    for f in fontes:
        for tam, cor in ((40, (255, 255, 255, 255)), (110, (212, 166, 74, 255)), (220, (20, 20, 20, 255))):
            casos.append((f"positivo SPRINT {Path(f).stem} {tam}px", _positivo("SPRINT", fl / f, tam, cor)))
    casos.append(("positivo SPRINT girado 15 graus", _positivo("SPRINT", fl / fontes[1], 90, (212, 166, 74, 255), giro=15)))
    casos.append(("positivo 2027", _positivo("2027", fl / fontes[0], 120, (255, 255, 255, 255))))
    arquivos = []
    for n in negativos:
        p = Path(n)
        arquivos += sorted(x for x in p.glob("*.png") if not x.name.endswith(".bruto.png")) if p.is_dir() else [p]
    print(f"{'imagem':58} {'3+ car.':>7} {'2 car.':>6}  veredito (limites {OCR_LIMITE:g} e {OCR_LIMITE_CURTA:g})")
    def maximos(ach):
        return (max([c for w, c, _ in ach if _caracteres(w) >= 3], default=0), max([c for w, c, _ in ach if _caracteres(w) == 2], default=0))

    with tempfile.TemporaryDirectory() as d:
        for nome, im in casos:
            p = Path(d) / "p.png"; im.save(p)
            ach = ler_texto(p); m3, m2 = maximos(ach)
            print(f"{nome:58} {m3:7.1f} {m2:6.1f}  {'REPROVA' if julgar_texto(ach) else 'passa  (falso negativo)'}")
    for p in arquivos:
        ach = ler_texto(p); m3, m2 = maximos(ach)
        print(f"negativo {str(p)[-49:]:49} {m3:7.1f} {m2:6.1f}  {'passa' if not julgar_texto(ach) else 'REPROVA (falso positivo)'}")


# ---------------------------------------------------------------- preparar_uso
def alfa_bbox(caminho, limiar=8):
    """Caixa (x0, y0, x1, y1) dos pixels com alfa > limiar (o franjado quase invisível do gerador não conta)."""
    a = Image.open(caminho).convert("RGBA").getchannel("A")
    return a.point(lambda v: 255 if v > limiar else 0).getbbox()


def preparar_uso(png, largura, saida):
    """Corta o PNG no alfa_bbox e reduz para 2× a largura de uso em px (nunca amplia). Grava `saida` e devolve o
    sha256 do arquivo gravado (determinístico: mesmo PNG e mesma largura, mesmo hash)."""
    im = Image.open(png).convert("RGBA")
    caixa = alfa_bbox(png)
    if caixa is None:
        raise ValueError(f"{png}: nenhum pixel visível (alfa todo zero)")
    im = im.crop(caixa)
    alvo = int(round(2 * float(largura)))
    if alvo <= 0:
        raise ValueError(f"largura de uso inválida: {largura}")
    if im.width > alvo:
        im = im.resize((alvo, max(1, round(im.height * alvo / im.width))), Image.LANCZOS)
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    im.save(saida, "PNG", optimize=True)
    h = hashlib.sha256(Path(saida).read_bytes()).hexdigest()
    return h


def cmd_preparar_uso(a):
    h = preparar_uso(a.png, a.largura, a.saida)
    w, hh = Image.open(a.saida).size
    print(f"OK {a.saida} {w}x{hh} sha256={h}")
    return h


# ---------------------------------------------------------------- calibrar (reproduz o limite)
def _ruido_periodico(n, escala, rng):
    f = np.fft.fftfreq(n)
    r = np.sqrt(f[None, :] ** 2 + f[:, None] ** 2)
    filtro = np.exp(-(r * escala) ** 2)
    campo = np.real(np.fft.ifft2(np.fft.fft2(rng.normal(size=(n, n))) * filtro))  # periódico por construção
    campo = (campo - campo.min()) / (np.ptp(campo) or 1)
    return (campo * 255).astype(np.uint8)


def _linhas_periodicas(n, rng, periodico=True):
    """Traço fino (o caso do pattern de penas): linhas desenhadas numa tela 3x3 e recortadas no centro. Recortado no
    tile do meio, o que sai por uma borda volta pela outra (periódico). Sem periodicidade: recorte deslocado."""
    tela = Image.new("L", (3 * n, 3 * n), 255); d = ImageDraw.Draw(tela)
    for _ in range(40):
        x0, y0 = rng.integers(0, n, 2); dx, dy = rng.integers(-n // 2, n // 2, 2)
        for i in range(3):
            for j in range(3):
                d.line([(x0 + i * n, y0 + j * n), (x0 + dx + i * n, y0 + dy + j * n)], fill=0, width=3)
    if periodico:
        g = np.asarray(tela.crop((n, n, 2 * n, 2 * n)))
    else:
        tela2 = Image.new("L", (3 * n, 3 * n), 255); d2 = ImageDraw.Draw(tela2)
        for _ in range(360):
            x0, y0 = rng.integers(0, 3 * n, 2); dx, dy = rng.integers(-n // 2, n // 2, 2)
            d2.line([(x0, y0), (x0 + dx, y0 + dy)], fill=0, width=3)
        g = np.asarray(tela2.crop((n + 37, n + 11, 2 * n + 37, 2 * n + 11)))
    alfa = 255 - g
    return Image.fromarray(np.dstack([np.zeros_like(g)] * 3 + [alfa]), "RGBA")


def calibrar():
    rng = np.random.default_rng(3)
    cinza = lambda g: Image.fromarray(np.dstack([g, g, g, np.full_like(g, 255)]), "RGBA")
    print("tile                                 índice  (limite %s)" % LIMITE_COSTURA)
    for escala in (8, 30, 80, 200):
        print(f"ruído periódico escala {escala:>3}            {medir_costura(cinza(_ruido_periodico(512, escala, rng)))['costura']:>5}")
        print(f"ruído recortado sem período {escala:>3}       {medir_costura(cinza(_ruido_periodico(1024, escala, rng)[100:612, 237:749]))['costura']:>5}")
    for k in range(3):
        print(f"traço fino periódico #{k}                {medir_costura(_linhas_periodicas(512, rng))['costura']:>5}")
        print(f"traço fino sem período #{k}              {medir_costura(_linhas_periodicas(512, rng, False))['costura']:>5}")
    x = np.arange(512)
    l = np.tile(((np.sin(2 * np.pi * x / 64) > 0) * 255).astype(np.uint8), (512, 1))
    print(f"listras periódicas                     {medir_costura(cinza(l))['costura']:>5}")
    l = np.tile(((np.sin(2 * np.pi * x / 50) > 0) * 255).astype(np.uint8), (512, 1))
    print(f"listras com período quebrado na borda  {medir_costura(cinza(l))['costura']:>5}  (borda escura encosta em borda clara)")


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("alfa"); p.add_argument("png")
    p = sub.add_parser("separar"); p.add_argument("entrada"); p.add_argument("saida"); p.add_argument("--fundo", default=None, help="#RRGGBB pedido no prompt")
    p = sub.add_parser("checar"); p.add_argument("tile"); p.add_argument("--limite", type=float, default=LIMITE_COSTURA); p.add_argument("--mosaico")
    p = sub.add_parser("tornar-seamless"); p.add_argument("entrada"); p.add_argument("saida"); p.add_argument("--metodo", choices=["costurar", "cruzar", "espelho"], default="costurar"); p.add_argument("--faixa", type=float, default=0.2)
    p = sub.add_parser("variantes"); p.add_argument("tile"); p.add_argument("--paleta", required=True); p.add_argument("--saida", required=True)
    p = sub.add_parser("folha"); p.add_argument("json"); p.add_argument("saida"); p.add_argument("--kit")
    sub.add_parser("calibrar")
    p = sub.add_parser("texto"); p.add_argument("png"); p.add_argument("--json", action="store_true")
    p.add_argument("--limite", type=float, default=OCR_LIMITE); p.add_argument("--limite-curta", type=float, default=OCR_LIMITE_CURTA)
    p = sub.add_parser("preparar_uso"); p.add_argument("png"); p.add_argument("largura", type=float); p.add_argument("saida")
    p = sub.add_parser("calibrar-texto"); p.add_argument("negativos", nargs="*")
    p = sub.add_parser("revisar-texto"); p.add_argument("png"); p.add_argument("--evidencia", required=True); p.add_argument("--por", default="Claude")
    a = ap.parse_args()
    try:
        {"alfa": cmd_alfa, "separar": lambda a: separar(a.entrada, a.saida, a.fundo), "checar": cmd_checar, "tornar-seamless": cmd_seamless,
         "variantes": cmd_variantes, "folha": cmd_folha, "calibrar": lambda a: calibrar(), "texto": cmd_texto,
         "preparar_uso": cmd_preparar_uso, "calibrar-texto": lambda a: calibrar_texto(a.negativos),
         "revisar-texto": cmd_revisar_texto}[a.cmd](a)
    except (ValueError, RuntimeError) as e:
        print(f"erro: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

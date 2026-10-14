#!/usr/bin/env python3
"""
elementos_prompt.py: o prompt de cada elemento gerado por IA (GPT Image pela rota Codex) e a ficha <id>.meta.json que
fica ao lado do PNG. Quem chama é o elementos.sh; o Claude não escreve prompt de elemento à mão.

Um modelo por tipo do vocabulário (references/08-sistema-elementos.md): objeto, ilustracao, pictograma, textura, pattern,
adesivo. "ornamento" é o nome antigo de objeto e continua aceito. O prompt recebe:
  - o bloco de estilo da família (sistema_elementos.familias[].estilo, em inglês), repetido em todo membro da família;
  - a paleta, convertida em NOME de cor (hex no prompt vira texto impresso na imagem, aprendizado 23);
  - o motivo e a descrição do objeto (inglês);
  - o aspecto do encaixe: quadrado, largo, alto ou faixa;
  - a âncora de estilo, quando houver (o PNG vai anexado com `codex exec -i`): "match the rendering style of the
    attached reference, not its subject";
  - a composição da página, quando houver (`--composicao <pasta-do-kit> --pagina <rótulo> --elemento <id>`): área e
    proporção reais em px, lado da página, para onde o objeto olha, borda que o corta (sangra), luz e lente da foto da página.
    O objeto nasce INTEIRO e centrado: o corte é decisão da página, não do gerador (composicao_prompt.py).
  - o material, quando o elemento declara `material` (só tipo objeto; vocabulário do contrato de nomes): acrescenta UMA linha,
    "studio product render, physically based <material em inglês>, key light from the <luz> at 35 degrees, soft fill, thin
    rim light, transparent background". A luz é a que o prompt já tem (--luz, a da foto da página ou a esquerda da v1); objeto
    com estilo e sem luz nenhuma recebe a esquerda, a mesma padrão do `tratar.py sombra`, para a sombra cair do lado certo.
    Sem `material`, o prompt sai idêntico ao de antes, caractere por caractere.
Sempre: sem texto, sem letras, sem números, sem logos, fundo transparente, UMA geração (regerar gasta cota).

Estrutura do prompt: rótulos curtos na ordem do guia de prompt do próprio gerador (skill imagegen do Codex:
Use case, Asset type, Primary request, Input images, Subject, Style/medium, Composition/framing, Lighting/mood,
Color palette, Constraints, Avoid), mais as regras operacionais que já valiam no elementos.sh.

Nome de cor: vizinho mais próximo em CIEDE2000 numa tabela curada de ~90 nomes de uso corrente em inglês (valores de
referência do levantamento de cores do xkcd e das cores nomeadas do CSS, sem os nomes esquisitos ou ofensivos que o
levantamento tem). O nome antigo do cena_prompt.py (matiz em 9 faixas) chamava o ouro da Sprint de "vivid yellow" e o
marrom quase preto de "deep orange", o que mudaria o objeto.

Uso:
  python elementos_prompt.py prompt --tipo objeto --descricao "<inglês>" --saida /abs/<id>.bruto.png \
      [--estilo "<bloco>"] [--paleta "#D4A64A,#281805"] [--aspecto quadrado|largo|alto|faixa] [--motivo <id>] \
      [--luz esquerda|direita|cima] [--ref] [--material metal-escovado|ouro|couro|borracha|tecido|vidro-fosco|...] \
      [--composicao <pasta-do-kit> --pagina <rótulo> --elemento <id> [--receita r1]]
  python elementos_prompt.py cor "#D4A64A"            nome da cor
  python elementos_prompt.py reserva <tipo>           fundo pedido se o gerador não der alfa: branco ou cinza
  python elementos_prompt.py meta --id <id> --pasta <dir> --png <final> --bruto <bruto> --tipo ... (ver main)
"""
import argparse, datetime, hashlib, json, re, sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import composicao_prompt as cp  # noqa: E402

TIPOS = ("objeto", "ilustracao", "pictograma", "textura", "pattern", "adesivo")
APELIDOS = {"ornamento": "objeto"}   # nome antigo (elementos.sh v1, references/07)
ASPECTOS = ("quadrado", "largo", "alto", "faixa")
LUZES = {"esquerda": "LEFT", "direita": "RIGHT", "cima": "TOP"}
# fundo que o prompt pede se o gerador não entregar alfa: decide a rota de reserva do elementos.sh
# (branco = padrao.py separar, chroma; cinza = recortar.py --classe produto, rembg)
RESERVA = {"objeto": "cinza", "ilustracao": "cinza", "pictograma": "cinza", "adesivo": "cinza", "pattern": "branco", "textura": "branco"}
FRASE_ANCORA = "match the rendering style of the attached reference, not its subject"
# elementos[].material (contrato de nomes do plano de 12/10/2026) -> o nome do material no render, em inglês
MATERIAIS = {"metal-escovado": "brushed metal", "ouro": "polished gold", "couro": "leather", "borracha": "rubber",
             "tecido": "woven fabric", "vidro-fosco": "frosted glass", "plastico-fosco": "matte plastic", "madeira": "wood",
             "papel": "paper", "grama": "grass"}
LINHA_MATERIAL = ("studio product render, physically based {material}, key light from the {luz} at 35 degrees, soft fill, "
                  "thin rim light, transparent background")

# ---------------------------------------------------------------- nome de cor
CORES = [
    # neutros
    ("black", "#000000"), ("charcoal black", "#1C1C1C"), ("charcoal grey", "#36454F"), ("dark grey", "#505050"),
    ("mid grey", "#808080"), ("light grey", "#C8C8C8"), ("off-white", "#F2F0EB"), ("white", "#FFFFFF"),
    ("ivory", "#FFFFF0"), ("cream", "#F3E5C0"), ("sand beige", "#E2D3B5"), ("warm sand", "#D8C3A0"), ("taupe", "#8B7D6B"),
    ("warm grey", "#9A9086"), ("cool grey", "#8C96A0"),
    # castanhos
    ("near-black brown", "#241505"), ("dark chocolate brown", "#3D2314"), ("chocolate brown", "#5C3317"),
    ("coffee brown", "#6F4E37"), ("caramel brown", "#AF6F2F"), ("tan", "#D2B48C"), ("camel", "#C19A6B"),
    ("copper", "#B87333"), ("bronze", "#A97142"), ("terracotta", "#CC6B49"), ("rust", "#A0451E"), ("sienna", "#A0522D"),
    ("light caramel", "#D39A5E"),
    # dourados e amarelos
    ("metallic gold", "#D4AF37"), ("golden yellow", "#F2C230"), ("ochre", "#CC9A3C"), ("mustard yellow", "#D1A922"),
    ("amber", "#FFBF00"), ("honey gold", "#E0A33A"), ("pale gold", "#E6D28C"), ("lemon yellow", "#FFF44F"),
    ("sunflower yellow", "#FFC512"), ("pale yellow", "#FFF5A0"), ("antique gold", "#C9A24D"),
    # laranjas
    ("orange", "#FF7F00"), ("burnt orange", "#CC5500"), ("tangerine", "#FF9408"), ("apricot", "#FBB46E"),
    ("peach", "#FFCBA4"), ("coral", "#FF7F50"), ("pale peach", "#FFE5D0"),
    # vermelhos e rosas
    ("red", "#E3242B"), ("scarlet red", "#FF2400"), ("crimson", "#B3001B"), ("burgundy", "#800020"), ("maroon", "#5E1224"),
    ("salmon pink", "#FA8072"), ("hot pink", "#FF1D8E"), ("magenta", "#D0217F"), ("rose pink", "#E8A0B4"),
    ("blush pink", "#F4C2C2"),
    # roxos
    ("purple", "#7B2D8E"), ("violet", "#8F00FF"), ("lavender", "#B9A2E0"), ("plum", "#5E2750"), ("indigo", "#3F1D7A"),
    # azuis
    ("navy blue", "#13294B"), ("midnight blue", "#0C1B2A"), ("royal blue", "#2F4BD8"), ("cobalt blue", "#1E4FA0"),
    ("sea blue", "#1F6AA5"), ("ocean blue", "#0F5E8C"), ("steel blue", "#4682B4"), ("sky blue", "#87CEEB"),
    ("light blue", "#ADD8E6"), ("denim blue", "#3B5B92"), ("electric blue", "#1F75FE"), ("cerulean", "#2A9FD6"),
    # verdes e azuis esverdeados
    ("teal", "#008080"), ("turquoise", "#30C5B7"), ("aqua", "#7FDBD4"), ("forest green", "#1F4D2B"),
    ("emerald green", "#0F8A4F"), ("kelly green", "#2DAA3F"), ("lime green", "#9BD32A"), ("olive green", "#6B7A2A"),
    ("sage green", "#9CAF88"), ("mint green", "#A8E6C1"), ("bottle green", "#0B4A2F"), ("neon green", "#39FF14"),
]
_HEX = re.compile(r"#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b")


def hex_rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", h):
        raise ValueError(f"cor inválida: {h!r} (use #RRGGBB)")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lab(rgbs):
    from skimage.color import rgb2lab
    return rgb2lab(np.asarray(rgbs, dtype=float).reshape(-1, 1, 3) / 255.0).reshape(-1, 3)


_TABELA = None


def nome_cor(hexa):
    """Nome em inglês simples da cor mais próxima (CIEDE2000) na tabela curada."""
    global _TABELA
    from skimage.color import deltaE_ciede2000
    if _TABELA is None:
        _TABELA = _lab([hex_rgb(h) for _, h in CORES])
    alvo = _lab([hex_rgb(hexa)])[0]
    d = deltaE_ciede2000(np.repeat(alvo[None], len(CORES), axis=0), _TABELA)
    return CORES[int(np.argmin(d))][0]


def sem_hex(texto):
    """Troca qualquer #RRGGBB de um texto livre (estilo, descrição) pelo nome da cor: hex não entra no prompt."""
    return _HEX.sub(lambda m: nome_cor(m.group(0)), texto or "")


def paleta_lista(paleta):
    if not paleta:
        return []
    itens = paleta.split(",") if isinstance(paleta, str) else list(paleta)
    return [c.strip() for c in itens if c and c.strip()]


# ---------------------------------------------------------------- modelos por tipo
FORMATO = {
    "quadrado": "Square 1:1 image, 1024x1024 pixels or larger",
    "largo": "Landscape 3:2 image, 1536x1024 pixels or larger",
    "alto": "Portrait 2:3 image, 1024x1536 pixels or larger",
    "faixa": ("Wide landscape image, 1536x1024 pixels or larger, used as a long horizontal strip: the subject spans the "
              "full width as a band about three times wider than tall, centered vertically, the area above and below it empty"),
}

MODELOS = {
    "objeto": dict(
        caso="product-mockup",
        ativo="isolated object cut-out for a sports sponsorship media kit page (transparent PNG placed over layouts)",
        pedido="one single object: {descricao}",
        meio_padrao="Photorealistic product photograph of the object alone, crisp focus, true colors.",
        composicao="{formato}. One single isolated object, centered, the whole object inside the frame with a generous empty margin on every side, nothing cropped.",
        composicao_pagina="{formato}. One single isolated object, whole object, centered, nothing cropped{corte}.",
        restricoes="one object only; no people, no hands, no body parts, no floor, no table, no props, no scenery",
        restricoes_sem_estilo="; no cast shadow on the background",
        conferir=["one object only, nothing cropped by the frame", "background is transparent or perfectly flat mid grey"],
        conferir_luz="light comes from the {luz}",
        reserva_txt="a perfectly flat, uniform mid grey background (50% grey), no gradient, no vignette",
    ),
    "ilustracao": dict(
        caso="stylized-concept",
        ativo="isolated illustration cut-out for a sports sponsorship media kit page (transparent PNG placed over layouts)",
        pedido="one self-contained illustration: {descricao}",
        meio_padrao="Flat vector-like illustration, clean confident shapes, limited palette, no photographic texture.",
        composicao="{formato}. One self-contained illustration of the subject, centered, generous empty margin on every side, nothing cropped, no frame, no border, no background scenery around the subject.",
        composicao_pagina="{formato}. One self-contained illustration of the subject, whole subject, centered, nothing cropped, no frame, no border, no background scenery around the subject{corte}.",
        restricoes="one subject only; no ground plane, no sky, no backdrop box, no frame",
        restricoes_sem_estilo="",
        conferir=["one subject only, nothing cropped, no backdrop", "background is transparent or perfectly flat mid grey"],
        conferir_luz="light comes from the {luz}",
        reserva_txt="a perfectly flat, uniform mid grey background (50% grey), no gradient, no vignette",
    ),
    "pictograma": dict(
        caso="logo-brand",
        ativo="pictogram (icon) for a sports sponsorship media kit, used small and large (transparent PNG)",
        pedido="one bold pictogram: {descricao}",
        meio_padrao="Flat pictogram, solid fills only, no gradients, no shading, no outlines thinner than 4 pixels.",
        composicao="{formato}. One pictogram, centered, generous empty margin on every side, a strong simple silhouette that still reads at 64 pixels.",
        composicao_pagina="{formato}. One pictogram, whole, centered, nothing cropped, a strong simple silhouette that still reads at 64 pixels{corte}.",
        restricoes="one pictogram only; no circle, square, badge or frame behind it; no extra decoration",
        restricoes_sem_estilo="",
        conferir=["one pictogram only, simple silhouette, nothing behind it", "background is transparent or perfectly flat mid grey"],
        conferir_luz="",
        reserva_txt="a perfectly flat, uniform mid grey background (50% grey), no gradient, no vignette",
    ),
    "textura": dict(
        caso="stylized-concept",
        ativo="full-frame texture overlay for a sports sponsorship media kit (transparent PNG: only the marks are opaque)",
        pedido="one texture: {descricao}",
        meio_padrao="Printed texture made of ink marks only.",
        composicao="{formato}. The texture covers the whole frame evenly, edge to edge, with no focal point, no objects, no border and no vignette.",
        restricoes="no objects, no recognizable figures, no frame; the paper or surface itself is transparent, only the marks are visible",
        restricoes_sem_estilo="",
        conferir=["even coverage edge to edge with no focal point", "background is transparent or perfectly flat white"],
        conferir_luz="",
        reserva_txt="a perfectly flat, uniform pure white background with nothing else on it",
    ),
    "pattern": dict(
        caso="stylized-concept",
        ativo="seamless repeating pattern tile for a sports sponsorship media kit (transparent PNG)",
        pedido="one seamless repeating pattern tile: {descricao}",
        meio_padrao=("Flat graphic illustration, like a screen-printed textile pattern. Solid black ink only (one tone, optionally "
                     "a second lighter grey tone), clean lines of even weight, no gradients, no shading, no paper or grain texture."),
        composicao="{formato}. Motif density even across the whole tile, no focal point, no border, no frame.",
        restricoes="",
        restricoes_sem_estilo="",
        conferir=["background is transparent or perfectly flat white", "even density with no focal point", "{costura}"],
        conferir_luz="",
        reserva_txt="a perfectly flat, uniform pure white background with nothing else on it",
    ),
    "adesivo": dict(
        caso="logo-brand",
        ativo="die-cut sticker artwork for a sports sponsorship media kit (transparent PNG; any wording is added later by layout software)",
        pedido="one die-cut sticker: {descricao}",
        meio_padrao="Bold flat vector-like sticker artwork with a thin white die-cut border, solid fills.",
        composicao="{formato}. One sticker, centered, generous empty margin on every side, a clean continuous outer cut line; slightly rotated is fine. Any area meant for a label stays blank and flat.",
        composicao_pagina="{formato}. One sticker, whole, centered, nothing cropped, a clean continuous outer cut line; slightly rotated is fine. Any area meant for a label stays blank and flat{corte}.",
        restricoes="one sticker only; no mockup, no hand, no surface or shadow under it",
        restricoes_sem_estilo="",
        conferir=["one sticker only with a clean cut line and blank label areas", "background is transparent or perfectly flat mid grey"],
        conferir_luz="",
        reserva_txt="a perfectly flat, uniform mid grey background (50% grey), no gradient, no vignette",
    ),
}

SEAMLESS = {
    "dois": ("SEAMLESS: the tile must wrap around. Any shape that crosses the left edge continues exactly on the right edge, "
             "any shape that crosses the top edge continues exactly on the bottom edge, so that placing copies side by side "
             "shows no visible seam."),
    "horizontal": ("SEAMLESS LEFT TO RIGHT: the strip must wrap around horizontally. Any shape that crosses the left edge "
                   "continues exactly on the right edge, so that copies placed side by side show no visible seam."),
}

REGRAS = ("The image must contain NO text of any kind: no letters, no numbers, no digits, no logos, no brand marks, no "
          "signatures, no watermarks, no engraved or printed characters.\n"
          "Do NOT post-process the image with code or any other tool: no background removal, no resizing, no recoloring, no "
          "cropping. Save exactly the file the image generator returned (we measure its transparency afterwards).\n"
          "Do NOT regenerate under any circumstance, not even if a check below fails (each generation spends the ChatGPT "
          "quota). Make exactly one image generation call and keep that single image.")


FUNCAO_TEXTO = {"foco": "the focal point of the page", "contexto": "context (it says where and with whom the content happens)",
                "identidade": "brand identity", "conexao": "a link between two areas of the page", "organizacao": "an organizing device",
                "profundidade": "depth (it enters the photo and leaves it)", "equilibrio": "visual balance against the heavy side of the page",
                "acabamento": "finishing texture"}
OBJETOS_DE_PAGINA = ("objeto", "ilustracao", "pictograma", "adesivo")     # os que a página recorta, gira e orienta (pattern e textura enchem o quadro)
POSICAO_H = {"left": "on the left side of the page", "right": "on the right side of the page", "center": "in the horizontal center of the page"}
POSICAO_V = {"upper": "in the upper part", "lower": "in the lower part", "middle": "around the middle"}


def _rumo_texto(r):
    return {"up": "upward", "down": "downward"}.get(r) or f"toward the {r}"


def bloco_composicao(c, tipo, luz_explicita=None):
    """As frases do bloco "Composition" a partir dos fatos de composicao_prompt.contexto(c). Devolve um dict: `corte` (o que se
    acrescenta ao enquadramento), `colocacao` (a linha "Page placement"), `luz` (direção da luz, em esquerda|direita|cima, e a
    frase da foto), `perspectiva` e `conferir` (itens para a conferência final). Cada frase só existe quando o fato existe."""
    espelha = (lambda x: cp.ESPELHO.get(x, x)) if c.get("espelhar") else (lambda x: x)
    out = {"corte": "", "colocacao": None, "luz": None, "frase_luz": None, "perspectiva": None, "conferir": []}
    foto = cp.luz_da_foto(c.get("estilo_cena"))
    W, H = c["pagina_px"]
    if tipo in OBJETOS_DE_PAGINA:
        sg = c.get("sangra")
        if sg:
            lado = espelha(sg["borda"])
            oposto = cp.OPOSTA[lado]
            out["corte"] = f"; the page will crop it on the {lado} side, keep the key detail on the {oposto} side"
            out["conferir"].append(f"the key detail is on the {oposto} side, away from the {lado} edge")
    partes = []
    if c.get("area_px"):
        w, h = c["area_px"]
        partes.append(f"on the final {W} x {H} px page this object appears about {w} x {h} px ({cp.descrever_razao(w, h)})")
    else:
        partes.append("on the final page this object appears")
    if c.get("lado"):
        horiz, vert = c["lado"]
        onde = POSICAO_H[horiz] + (f", {POSICAO_V[vert]}" if vert != "middle" or horiz == "center" else "")
        partes[0] += f", {onde}"
    frases = [partes[0][0].upper() + partes[0][1:] + "."] if partes else []
    if tipo in OBJETOS_DE_PAGINA:
        if c.get("rumo"):
            rumo = espelha(c["rumo"])
            frase = f"It must point and face {_rumo_texto(rumo)}"
            if c.get("alvo_do_foco"):
                frase += f", at {c['alvo_do_foco']}"
            frases.append(frase + ", so the eye travels from the object into the page.")
            out["conferir"].append(f"the object faces {_rumo_texto(rumo)}")
        if c.get("rot"):
            frases.append(f"Draw it upright: the page rotates it by {c['rot']:g} degrees.")
        sg = c.get("sangra")
        if sg and cp.FRACOES.get(sg.get("corte")):
            frases.append(f"The page crops {cp.FRACOES[sg['corte']]} of it on the {espelha(sg['borda'])} side.")
        so = c.get("sobrepoe")
        if so and so.get("alvo"):
            alvo = cp.ALVO_TEXTO.get(so["alvo"], f"the {so['alvo']}")
            frases.append(f"It overlaps {alvo}, so give it a clean, crisp silhouette that reads against a busy photo.")
        funcao = (c.get("elemento") or {}).get("funcao")
        if funcao in FUNCAO_TEXTO:
            frases.append(f"Its role on the page: {FUNCAO_TEXTO[funcao]}.")
    out["colocacao"] = " ".join(frases) if frases else None
    # a luz: a da foto da página; um elemento espelhado nasce com a luz do lado oposto (a página vira a imagem)
    direcao = luz_explicita or foto["direcao"]
    if direcao and c.get("espelhar") and direcao in ("esquerda", "direita"):
        direcao = {"esquerda": "direita", "direita": "esquerda"}[direcao]
    out["luz"] = direcao
    if foto["luz"] and not luz_explicita:
        out["frase_luz"] = "the same direction as the light in the page photo (" + ", ".join(sem_hex(x) for x in foto["luz"]) + ")"
    if tipo in ("objeto", "ilustracao"):
        base = (f"like the page photo ({', '.join(sem_hex(x) for x in foto['lente'])})" if foto["lente"]
                else "eye level, a moderate lens")
        giro = f"; turned slightly {_rumo_texto(espelha(c['rumo']))}" if c.get("rumo") else ""
        out["perspectiva"] = f"{base}, no extreme foreshortening{giro}"
    return out


def montar_prompt(tipo, descricao, saida, estilo=None, paleta=None, aspecto=None, motivo=None, luz=None, ref=False, composicao=None,
                  material=None):
    """Prompt completo de UM elemento. `saida` é o caminho absoluto do PNG bruto que o Codex grava. `composicao` = os fatos de
    composicao_prompt.contexto(): o aspecto sai da proporção real (se `aspecto` não vier), o objeto nasce inteiro e centrado
    com o corte dito pela página, e entram as linhas "Page placement" e "Perspective" e a luz da foto da página.
    `material` (chave de MATERIAIS, só tipo objeto) acrescenta a linha "Material/render"; sem ele nada muda."""
    tipo = APELIDOS.get(tipo, tipo)
    if tipo not in MODELOS:
        raise ValueError(f"tipo `{tipo}` fora do vocabulário de IA: {', '.join(TIPOS)} (texto, selo e afins são grafismo por código)")
    aspecto = aspecto or ((composicao or {}).get("aspecto")) or "quadrado"
    if aspecto not in ASPECTOS:
        raise ValueError(f"aspecto `{aspecto}` inválido: {', '.join(ASPECTOS)}")
    if luz and luz not in LUZES:
        raise ValueError(f"luz `{luz}` inválida: {', '.join(LUZES)}")
    if not (descricao or "").strip():
        raise ValueError("descrição vazia")
    if material is not None:
        if material not in MATERIAIS:
            raise ValueError(f"material `{material}` fora do vocabulário: {', '.join(MATERIAIS)}")
        if tipo != "objeto":
            raise ValueError(f"material só vale para objeto (render de produto); `{tipo}` não leva material")
    m = MODELOS[tipo]
    descricao = sem_hex(descricao.strip()).rstrip(".")
    estilo = sem_hex((estilo or "").strip()).rstrip(".")
    cores = [nome_cor(c) for c in paleta_lista(paleta)]
    bc = bloco_composicao(composicao, tipo, luz) if composicao else None
    if bc and bc["luz"]:
        luz = bc["luz"]            # a luz da foto da página (ou a que o `--luz` pediu, já espelhada se a página espelha)
    if luz is None and tipo == "objeto" and not estilo:
        luz = "esquerda"   # comportamento da v1 (ornamento): luz principal da esquerda
    if luz is None and material:
        luz = "esquerda"   # o material pede a direção da luz; a mesma padrão do tratar.py sombra
    formato = FORMATO[aspecto]
    if tipo == "pattern":
        formato = f"{formato}, a seamless repeating pattern tile" if aspecto != "faixa" else f"{formato}, a seamless repeating border strip"
    linhas = [f"Generate one image with one call of the image generator and save it exactly as {saida} (PNG).",
              f"Use case: {m['caso']}",
              f"Asset type: {m['ativo']}",
              f"Primary request: {m['pedido'].format(descricao=descricao)}"]
    if ref:
        linhas.append("Input images: Image 1 (attached) is a STYLE REFERENCE only. "
                      f"Generate a new image and {FRASE_ANCORA}: same medium, material finish, light direction and softness, "
                      "level of detail, color treatment, camera angle and edge quality. Do not copy, trace, edit or include the "
                      "reference object; draw only the subject described here, as a new and different object.")
    linhas.append(f"Subject: {descricao}")
    if motivo:
        linhas.append(f"Theme: {motivo.replace('-', ' ')} (a visual theme, never written)")
    linhas.append(f"Style/medium: {estilo}" if estilo else f"Style/medium: {m['meio_padrao']}")
    if bc and "composicao_pagina" in m:
        linhas.append(f"Composition/framing: {m['composicao_pagina'].format(formato=formato, corte=bc['corte'])}")
    else:
        linhas.append(f"Composition/framing: {m['composicao'].format(formato=formato)}")
    if bc and bc["colocacao"]:
        linhas.append(f"Page placement: {bc['colocacao']}")
    if luz and tipo in ("objeto", "ilustracao"):
        frase = f"Lighting/mood: key light from the {LUZES[luz]}, gentle fill from the opposite side."
        if bc and bc["frase_luz"]:
            frase = frase[:-1] + f", {bc['frase_luz']}."
        linhas.append(frase)
    if material:
        linhas.append("Material/render: " + LINHA_MATERIAL.format(material=MATERIAIS[material], luz=LUZES[luz]) + ".")
    if bc and bc["perspectiva"]:
        linhas.append(f"Perspective: {bc['perspectiva']}.")
    if cores:
        resto = (" except the natural highlights and shadows of the materials" if tipo == "objeto" else "")
        if len(cores) == 1:
            linhas.append(f"Color palette: {cores[0]} only; no other hues{resto}.")
        else:
            linhas.append(f"Color palette: {cores[0]} as the dominant color, with {', '.join(cores[1:])}; no other hues{resto}.")
    linhas.append(f"Background: fully transparent (PNG with a real alpha channel). If the generator cannot produce transparency, use this instead: {m['reserva_txt']}.")
    restr = m["restricoes"] + ("" if estilo else m["restricoes_sem_estilo"])
    if tipo == "pattern":
        restr = SEAMLESS["horizontal" if aspecto == "faixa" else "dois"]
    if restr:
        linhas.append(f"Constraints: {restr}.".replace("..", "."))
    linhas.append("Avoid: text of any kind, letters, numbers, digits, logos, brand marks, signatures, watermarks.")
    linhas.append(REGRAS)
    if ref:
        linhas.append("Do not edit, copy or overwrite the attached reference image file.")
    costura = "left and right edges match" if aspecto == "faixa" else "left and right edges match and top and bottom edges match"
    itens = ["no text, letter, number, digit or logo anywhere, including on the subject itself"]
    itens += [c.format(costura=costura) for c in m["conferir"]]
    if luz and m["conferir_luz"]:
        itens.append(m["conferir_luz"].format(luz=LUZES[luz].lower()))
    if bc:
        itens += bc["conferir"]
    if ref:
        itens.append("the rendering style matches the attached reference while the subject is the new one")
    linhas.append("After saving, open the image and check: " + ", ".join(f"({i}) {t}" for i, t in enumerate(itens, 1)) + ".")
    linhas.append("In your final message, write one line exactly as TRANSPARENT: yes or TRANSPARENT: no (as returned by the generator), then list any defect found.")
    return "\n".join(linhas)


# ---------------------------------------------------------------- ficha (meta.json)
def sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def geracoes_medidas(pasta, id_):
    """Quantas chamadas de geração de imagem o Codex fez para este id, lidas no log de eventos que os automatismos
    gravam em <pasta>/.claude/state/runs/*/events.jsonl (o mesmo usado em 09/10 para conferir 6 de 6). None quando
    não há log que cite <id>.bruto.png (não dá para afirmar)."""
    runs = Path(pasta) / ".claude" / "state" / "runs"
    if not runs.is_dir():
        return None
    total, achou = 0, False
    for ev in runs.glob("*/events.jsonl"):
        txt = ev.read_text(encoding="utf-8", errors="replace")
        if f"{id_}.bruto.png" not in txt:
            continue
        achou = True
        for linha in txt.splitlines():
            try:
                e = json.loads(linha)
            except ValueError:
                continue
            if "image_gen" in str(e.get("tool", "")):
                total += 1
    return total if achou else None


def gravar_meta(a):
    sys.path.insert(0, str(AQUI))
    import padrao
    from PIL import Image
    final = Path(a.png)
    ok, med = padrao.medir_alfa(final)
    ok_b, med_b = padrao.medir_alfa(a.bruto) if a.bruto and Path(a.bruto).exists() else (None, None)
    comp = None
    if getattr(a, "composicao", ""):     # os fatos da página que o prompt usou (a medida, o lado, o rumo, o corte): rastro do porquê
        c = cp.contexto(a.composicao, a.pagina, a.elemento, getattr(a, "receita", "") or None)
        comp = {k: c[k] for k in ("pagina", "chave", "plano", "area_px", "aspecto", "origem_da_medida", "lado", "rumo", "sangra",
                                  "sobrepoe", "rot", "espelhar")}
        comp["elemento"] = a.elemento
    meta = {
        "id": a.id, "tipo": APELIDOS.get(a.tipo, a.tipo), "familia": a.familia or None, "motivo": a.motivo or None,
        "estilo": a.estilo or None, "paleta": paleta_lista(a.paleta), "paleta_nomes": [nome_cor(c) for c in paleta_lista(a.paleta)],
        "aspecto": a.aspecto or (comp or {}).get("aspecto") or "quadrado", "luz": a.luz or None, "descricao": a.descricao,
        "ref": a.ref or None, "ref_sha256": sha256(a.ref) if a.ref and Path(a.ref).exists() else None,
        "material": getattr(a, "material", "") or None,
        "rota": a.rota, "arquivo": final.name, "bruto": Path(a.bruto).name if a.bruto else None,
        "sha256": sha256(final), "sha256_bruto": sha256(a.bruto) if a.bruto and Path(a.bruto).exists() else None,
        "dims": list(Image.open(final).size),
        "alfa": {"real": bool(ok), **med}, "alfa_bruto": ({"real": bool(ok_b), **med_b} if med_b else None),
        "codex_disse": a.codex_disse or None, "geracoes_medidas": geracoes_medidas(a.pasta, a.id),
        "prompt": a.prompt or None, "gerado": True,
        "composicao": comp,                                                  # None quando o elemento não nasceu de uma composição
        "data": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    destino = Path(a.pasta) / f"{a.id}.meta.json"
    destino.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"OK {destino} sha256={meta['sha256'][:12]} geracoes={meta['geracoes_medidas']}")
    return meta


# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prompt")
    p.add_argument("--tipo", required=True); p.add_argument("--descricao", required=True); p.add_argument("--saida", required=True)
    p.add_argument("--estilo"); p.add_argument("--paleta"); p.add_argument("--aspecto"); p.add_argument("--motivo")
    p.add_argument("--luz"); p.add_argument("--ref", action="store_true")
    p.add_argument("--material", help=f"só objeto: {', '.join(MATERIAIS)}")
    p.add_argument("--composicao", help="pasta do kit (a que tem o mediakit.json com `composicao`); pede --pagina e --elemento")
    p.add_argument("--pagina", help="rótulo da página na composição (ativo:2, cota:Master, capa:c, vertical:capa) ou o número dela")
    p.add_argument("--elemento", help="id do elemento na composição dessa página")
    p.add_argument("--receita", help="com mais de uma receita no plano: a que dá a caixa resolvida (padrão: a primeira que tem o elemento)")
    p = sub.add_parser("cor"); p.add_argument("hex", nargs="+")
    p = sub.add_parser("reserva"); p.add_argument("tipo")
    p = sub.add_parser("meta")
    for k in ("id", "pasta", "png", "tipo", "rota"):
        p.add_argument(f"--{k}", required=True)
    for k in ("bruto", "familia", "motivo", "estilo", "paleta", "aspecto", "luz", "ref", "codex-disse", "prompt", "descricao", "composicao",
              "pagina", "elemento", "receita", "material"):
        p.add_argument(f"--{k}", default="")
    a = ap.parse_args()
    try:
        if a.cmd == "prompt":
            comp = None
            if a.composicao or a.pagina or a.elemento:
                if not (a.composicao and a.pagina and a.elemento):
                    raise ValueError("composição pede os três: --composicao <pasta-do-kit> --pagina <rótulo> --elemento <id>")
                comp = cp.contexto(a.composicao, a.pagina, a.elemento, a.receita)
            print(montar_prompt(a.tipo, a.descricao, a.saida, a.estilo, a.paleta, a.aspecto, a.motivo, a.luz, a.ref, comp, a.material))
        elif a.cmd == "cor":
            for h in a.hex:
                print(f"{h} {nome_cor(h)}")
        elif a.cmd == "reserva":
            t = APELIDOS.get(a.tipo, a.tipo)
            if t not in RESERVA:
                raise ValueError(f"tipo `{a.tipo}` fora do vocabulário de IA: {', '.join(TIPOS)}")
            print(RESERVA[t])
        elif a.cmd == "meta":
            gravar_meta(a)
    except ValueError as e:
        print(f"erro: {e}", file=sys.stderr)
        sys.exit(64)


if __name__ == "__main__":
    main()

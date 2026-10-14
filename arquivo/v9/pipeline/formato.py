#!/usr/bin/env python3
"""
formato.py: o formato reprodutível de um kit aprovado (references/11-formatos.md). Um formato guarda o que TRAVA num kit
que deu certo e separa o que TROCA de cliente para cliente. Mora em formatos/<id>/, com versão imutável.

Comandos:
  exportar <kit> <id> [--nova-versao]       lê o estado FINAL do kit (mediakit.json, saida/plano-elementos-<receita>.json,
                                            acervo/**/*.meta.json, a entrada do kit em memoria-mediakit/historico-kits.json,
                                            tema-projeto.css, os .prompt.txt e os PNG de saida/png/kit-<receita>-*.png) e
                                            grava formatos/<id>/. Nunca lê o direcao-de-arte.md: ele é o plano de antes da
                                            execução, e o formato é o que o kit virou. Recusa sobrescrever: com a pasta já
                                            existente, só --nova-versao, que grava versoes/vN.json e versoes/vN/ sem tocar
                                            nas versões anteriores.
  aplicar <id> <kit-novo> [--versao N] [--simular]
                                            preenche no mediakit.json do kit SÓ a chave ausente (o kit vence), copia o
                                            tema-projeto.css se o kit não tiver e as fontes da receita de fontes-livres/ (sem
                                            sobrescrever arquivo), grava `formato_base {id, versao, sha256}` e escreve no
                                            pendencias.md uma linha por item de `trocar`, por papel a preencher e pela prosa
                                            da composição copiada. Antes de mexer, guarda mediakit.antes-do-formato.json.
  conferir <kit> [--formato <id>] [--versao N] [--json]
                                            diferença do kit contra o `travado` do formato (o de `formato_base`, ou o de
                                            --formato) e as lacunas `{...}` ainda abertas. Sai 1 quando há diferença ou
                                            lacuna.
  provar <id> [--kit-origem <pasta>] [--manter]
                                            clona o kit de origem (cp -cR, clone do APFS: o kit real nunca é escrito),
                                            renderiza com render.py --png e compara cada página com prova/assinatura.json.

O QUE TRAVA (travado): a receita sem id (nome, fontes, fundo, máscara, páginas do pattern, variantes por tipo e a parte
fixa da paleta: escuro, papel, texto), as constantes, os motivos de origem `esporte`, a família modelo (meio, luz,
paleta por chave e o bloco de estilo com as lacunas {assunto} e {material}), a gramática de composição por tipo e
variante com os ids dos elementos trocados por papéis ({heroi-capa}, {objeto-ativo-2}), os padrões do repertório usados,
`marca.direcao`, `marca.assinatura`, as fontes de `marca`, o tema-projeto.css (sha256) e `direcao_criativa`.
O QUE TROCA (trocar): a cor da marca e a de apoio, os motivos de origem `simbolo` e `territorio`, `marca.estilo_cena`
(com o modelo do que fica) e o logo. Os elementos que preenchem os papéis são do cliente (`papeis`).
O resto vai como referência: `exemplos` (composição de página específica, ativo:N e cota:<nome>), prompts/
(cena.modelo.txt e objeto.modelo.txt com lacunas, os .prompt.txt reais em prompts/exemplos/ sem caminho do Mac),
`tratamentos`, `nao_tem` (calculado contra o que a skill sabe fazer) e prova/ (assinatura.json com sha256, miniatura de
480 px e blocos de 8 px de cada página; referencia.jpg, a folha de contato).

PAPÉIS. Cada id de `elementos[]` vira `{<classe>-<onde>}`: classe `objeto` (tem família), `pattern` ou o papel dele no
kit (`heroi`); onde = a primeira chave da composição que o usa, na ordem em que o mediakit.json a escreve (`capa`,
`ativo-2`, `cota-1` pela posição da cota em `cotas`), ou a primeira página do pattern. O mesmo elemento em duas páginas
é o mesmo papel: o padrão "um motivo em vários papéis" sobrevive à troca de cliente.

PRECEDÊNCIA: o kit vence o formato. O formato é COPIADO para o kit (aplicar), nunca fundido no render.
Todo caminho de kit passa por caminhos.dentro_do_kit; todo caminho de formato também, com formatos/ no lugar da pasta do
kit, e o id segue ^[a-z0-9][a-z0-9-]{1,40}$.
"""
import argparse, base64, copy, hashlib, json, os, re, shutil, subprocess, sys, tempfile
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from caminhos import ForaDoKit, dentro_do_kit  # noqa: E402

RAIZ_SKILL = AQUI.parent
FORMATOS = RAIZ_SKILL / "formatos"
HISTORICO = RAIZ_SKILL / "memoria-mediakit" / "historico-kits.json"
FONTES_LIVRES = RAIZ_SKILL / "fontes-livres"
SCHEMA_ELEMENTOS = RAIZ_SKILL / "schema" / "elementos.schema.json"
SCHEMA_KIT = RAIZ_SKILL / "schema" / "mediakit.schema.json"
INDICE_REPERTORIO = RAIZ_SKILL / "repertorio" / "indice.json"
RAIZ_EMPRESA = RAIZ_SKILL.parent.parent        # MOTION PERFORM: historico-kits.json grava a pasta do kit a partir daqui

ID_FORMATO = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")
PALETA_FIXA = ("escuro", "papel", "texto")      # a parte da paleta que é do formato; marca e apoio são do cliente
PROSA = ("mensagem", "estrutura", "porque", "porque_fora_da_gramatica")
CONTEUDO_GRAFISMO = ("pontos", "cabecalho", "linhas", "texto", "itens", "rotulos", "rotulo", "legenda", "titulo", "imagem")
CAMPOS_COM_ID = ("id", "alvo", "entre", "x", "y", "de", "para", "ate")
LACUNA = re.compile(r"\{[a-z_][a-z0-9_-]*\}")

MINI_LARGURA = 480
BLOCO = 8                 # lado do bloco da assinatura, em px da miniatura
LIMIAR_BLOCO = 6.0        # média de um bloco que mudou mais que isto (0 a 255) = página diferente
MINI_QUALIDADE = 85
INTENSIDADE_PADRAO = {"padrao": 1, "teto": 2}


class ErroFormato(ValueError):
    """Formato ou kit que não dá para exportar, aplicar, conferir ou provar."""


# ================================================================================================= arquivos
def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_arq(p):
    return sha256_bytes(Path(p).read_bytes())


def json_txt(o, indent=1):
    return json.dumps(o, ensure_ascii=False, indent=indent) + "\n"


def gravar_novo(p, dados):
    """Grava só se o arquivo não existir (modo x): a versão do formato é imutável."""
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(dados, str):
        dados = dados.encode("utf-8")
    try:
        with open(p, "xb") as fh:
            fh.write(dados)
    except FileExistsError:
        raise ErroFormato(f"`{p.name}` já existe: a versão do formato é imutável")
    return p


def pasta_formato(fid, raiz=None):
    """formatos/<id>, resolvida e confinada. Recusa id fora do padrão e link que sai de formatos/."""
    if not isinstance(fid, str) or not ID_FORMATO.match(fid):
        raise ErroFormato(f"id de formato inválido: {fid!r} (use ^[a-z0-9][a-z0-9-]{{1,40}}$)")
    raiz = Path(raiz or FORMATOS)
    raiz.mkdir(parents=True, exist_ok=True)
    try:
        return dentro_do_kit(raiz, fid)
    except ForaDoKit as e:
        raise ErroFormato(f"formato `{fid}`: {e}")


def no_formato(pasta, rel):
    try:
        return dentro_do_kit(pasta, rel)
    except ForaDoKit as e:
        raise ErroFormato(f"arquivo do formato: {e}")


def no_kit(kit, rel):
    try:
        return dentro_do_kit(kit, rel)
    except ForaDoKit as e:
        raise ErroFormato(f"arquivo do kit: {e}")


def ler_kit(kit):
    kit = Path(kit).resolve()
    if not kit.is_dir():
        raise ErroFormato(f"pasta do kit não existe: {kit.name}")
    mk = no_kit(kit, "mediakit.json")
    if not mk.exists():
        raise ErroFormato(f"{kit.name}: sem mediakit.json")
    return kit, json.loads(mk.read_text(encoding="utf-8"))


def carregar_formato(fid, versao=None, raiz=None):
    """(pasta, formato, bytes do json da versão). Sem versão: formato.json (a última)."""
    pasta = pasta_formato(fid, raiz)
    if not pasta.is_dir():
        raise ErroFormato(f"formato `{fid}` não existe em formatos/")
    arq = no_formato(pasta, f"versoes/v{int(versao)}.json" if versao else "formato.json")
    if not arq.exists():
        raise ErroFormato(f"formato `{fid}`: {arq.relative_to(pasta)} não existe")
    bruto = arq.read_bytes()
    f = json.loads(bruto.decode("utf-8"))
    if f.get("formato") != fid:
        raise ErroFormato(f"{arq.name} diz ser o formato `{f.get('formato')}`, não `{fid}`")
    for rel, sha in (f.get("arquivos") or {}).items():
        p = no_formato(pasta, rel)
        if not p.exists() or sha256_arq(p) != sha:
            raise ErroFormato(f"formato `{fid}` v{f.get('versao')}: `{rel}` mudou ou sumiu (sha256 não bate)")
    return pasta, f, bruto


# ================================================================================================= papéis
def _slug(txt):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", str(txt).lower().replace("_", "-").replace(":", "-"))).strip("-")


def _onde(chave, k):
    tipo, sep, resto = chave.partition(":")
    if tipo == "cota" and sep:
        nomes = [c.get("nome") for c in k.get("cotas") or []]
        if resto in nomes:
            return f"cota-{nomes.index(resto) + 1}"
    return _slug(chave)


def eh_da_pagina(chave, k):
    """Chave de UMA página (ativo:2, cota:Master): vai para `exemplos`. Tipo, variante (cota:b, ativo:painel) e vertical
    são gramática."""
    if chave.startswith("vertical:"):
        return False
    tipo, sep, resto = chave.partition(":")
    if not sep:
        return False
    if tipo == "ativo" and resto.isdigit():
        return True
    return tipo == "cota" and resto in {c.get("nome") for c in k.get("cotas") or []}


def _classe(e):
    if e.get("tipo") == "pattern" or e.get("papel") == "pattern":
        return "pattern"
    if e.get("familia"):
        return "objeto"
    return e.get("papel") or "heroi"


def papeis_do_kit(k):
    """{id do elemento do kit: nome do papel}. Ver o docstring do módulo (PAPÉIS)."""
    els = {e["id"]: e for e in k.get("elementos") or [] if isinstance(e, dict) and e.get("id")}
    nomes, usados = {}, set()

    def nomear(eid, onde):
        if eid in nomes:
            return
        base = f"{_classe(els[eid])}-{onde}"
        nome, i = base, 2
        while nome in usados:
            nome, i = f"{base}-{i}", i + 1
        usados.add(nome)
        nomes[eid] = nome

    for chave, ent in (k.get("composicao") or {}).items():
        if chave.startswith("_") or not isinstance(ent, dict):
            continue
        for e in ent.get("elementos") or []:
            if e.get("id") in els and not e.get("grafismo"):
                nomear(e["id"], _onde(chave, k))
    for r in k.get("receitas") or []:
        if r.get("pattern") in els:
            pags = r.get("pattern_paginas") or []
            nomear(r["pattern"], _slug(pags[0]) if pags else "kit")
    for i, eid in enumerate(e for e in els if e not in nomes):
        nomear(eid, f"livre-{i + 1}")
    return nomes


def _padrao_ids(nomes):
    if not nomes:
        return None
    return re.compile(r"(?<![a-z0-9-])(" + "|".join(re.escape(i) for i in sorted(nomes, key=len, reverse=True)) + r")(?![a-z0-9-])")


def trocar_ids(o, nomes, rx=None):
    """Cópia de `o` com cada id de elemento do kit trocado por {papel} nos campos que apontam para elemento (id, alvo,
    entre, restrições x/y/de/para/ate e a leitura). A prosa fica como está."""
    rx = rx or _padrao_ids(nomes)
    if rx is None:
        return copy.deepcopy(o)
    sub = lambda s: rx.sub(lambda m: "{" + nomes[m.group(1)] + "}", s)
    if isinstance(o, dict):
        out = {}
        for c, v in o.items():
            if c in CAMPOS_COM_ID and isinstance(v, str):
                out[c] = sub(v)
            elif c == "leitura" and isinstance(v, list):
                out[c] = [sub(x) if isinstance(x, str) else x for x in v]
            elif c in PROSA or c == "grafismo":
                out[c] = copy.deepcopy(v)
            else:
                out[c] = trocar_ids(v, nomes, rx)
        return out
    if isinstance(o, list):
        return [trocar_ids(x, nomes, rx) for x in o]
    return copy.deepcopy(o)


def lacunas_de_conteudo(ent):
    """Na gramática, o conteúdo de cliente dentro do grafismo (pontos do mapa, cabeçalho e linhas do placar...) vira
    lacuna {chave}: a estrutura do grafismo fica, o dado é do kit."""
    ent = copy.deepcopy(ent)
    for e in ent.get("elementos") or []:
        params = (e.get("grafismo") or {}).get("params")
        if isinstance(params, dict):
            for c in CONTEUDO_GRAFISMO:
                if c in params:
                    params[c] = "{" + c + "}"
    return ent


def estrutural(ent):
    """A entrada da composição sem a prosa (o que o conferir compara)."""
    ent = {c: copy.deepcopy(v) for c, v in ent.items() if c not in PROSA}
    for e in ent.get("elementos") or []:
        for c in PROSA:
            e.pop(c, None)
    return ent


# ================================================================================================= estilo e prompts
ROUPA = ("kits", "kit", "shirts", "jerseys", "uniforms", "bibs")
LUZ_LENTE = ("sun", "light", "lens", "mm", "eye level", "haze", "photograph", "no text", "degrees", "shadow", "flash",
             "floodlight", "lit ")


def estilo_cena_modelo(estilo):
    """marca.estilo_cena → (modelo com lacunas, {lacuna: valor de origem}). Ordem documentada do bloco: hora (e lugar),
    luz, lente, atmosfera, material da paisagem, cor das roupas, 'real photograph, no text'. Luz, lente e atmosfera ficam
    (são da família de luz do formato); o resto vira lacuna."""
    partes = [p.strip() for p in (estilo or "").split(",") if p.strip()]
    if not partes:
        return None, {}
    out, orig = [], {}
    if " in " in partes[0]:
        momento, lugar = partes[0].split(" in ", 1)
        out.append("{momento} in {lugar}")
        orig.update(momento=momento, lugar=lugar)
    else:
        out.append("{momento}")
        orig["momento"] = partes[0]
    for p in partes[1:]:
        baixo = p.lower()
        palavras = baixo.split()
        if palavras and palavras[-1] in ROUPA:
            out.append("{cores} " + palavras[-1])
            orig["cores"] = " ".join(p.split()[:-1])
        elif any(t in baixo + " " for t in LUZ_LENTE):
            out.append(p)
        elif "material" in orig:
            orig["material"] += ", " + p
        else:
            out.append("{material}")
            orig["material"] = p
    return ", ".join(out), orig


def estilo_familia_modelo(estilo):
    """Bloco de estilo da família → (modelo com {assunto} e {material}, origem). Sem assunto achado: erro (a família
    modelo existe para trocar o assunto)."""
    partes = [p.strip() for p in (estilo or "").split(",")]
    out, orig = [], {}
    for i, p in enumerate(partes):
        m = re.match(r"^(.*?\bof (?:a single |a |an |one )?)(.+)$", p) if i == 0 else None
        if m:
            out.append(m.group(1) + "{assunto}")
            orig["assunto"] = m.group(2)
        elif "material" in p.lower() and "material" not in orig:
            out.append("{material}")
            orig["material"] = p
        else:
            out.append(p)
    if "assunto" not in orig:
        raise ErroFormato(f"não achei o assunto no estilo da família (esperado '... of a single <assunto>, ...'): {estilo!r}")
    return ", ".join(out), orig


CAMINHO_ABSOLUTO = re.compile(r"/(?:Users|private|var|tmp|Volumes|home)/[^\s)\]>]*")


def sanitizar(txt, kit):
    """Prompt sem caminho da máquina: qualquer caminho absoluto que passa pela pasta do kit vira <kit>/... (com ou sem
    link no meio: /tmp e /private/tmp são a mesma pasta) e qualquer outro caminho absoluto vira <caminho>."""
    kit = Path(kit)
    for c in sorted({str(kit), str(kit.resolve()), os.path.realpath(kit)}, key=len, reverse=True):
        txt = txt.replace(c, "<kit>")
    txt = re.sub(r"/(?:Users|private|var|tmp|Volumes|home)/[^\s)\]>]*?/" + re.escape(kit.name) + r"(?=/)", "<kit>", txt)
    return CAMINHO_ABSOLUTO.sub("<caminho>", txt)


SECOES_CENA = ("Scene:", "Camera:", "Light:", "Location:", "Composition (from the page layout):", "Constraints:")


def secoes(txt, rotulos=SECOES_CENA):
    achados = sorted((txt.find(r), r) for r in rotulos if txt.find(r) >= 0)
    out = {"_cabeca": (txt[:achados[0][0]] if achados else txt).strip()}
    for j, (i, r) in enumerate(achados):
        fim = achados[j + 1][0] if j + 1 < len(achados) else len(txt)
        out[r] = txt[i + len(r):fim].strip()
    return out


def _moda(valores):
    c = Counter(v for v in valores if v)
    return (c.most_common(1)[0] if c else (None, 0))


def modelo_cena(prompts, k):
    """prompts = [texto]. Modelo: cabeça, câmera e restrições pela moda; cena → {assunto}; luz → estilo_cena com
    lacunas; local → {lugar}; composição → {composicao} (escrita pelo cena_prompt.py --composicao, medida na maquete)."""
    estilo = (k.get("marca") or {}).get("estilo_cena") or ""
    est_mod, est_orig = estilo_cena_modelo(estilo)
    sec = [secoes(t) for t in prompts]
    com_estilo = [s for s in sec if estilo and estilo in s.get("Light:", "")]
    base = com_estilo or sec
    cab, n_cab = _moda(s["_cabeca"] for s in base)
    cam, n_cam = _moda(s.get("Camera:") for s in base)
    res, n_res = _moda(s.get("Constraints:") for s in base)
    if not (cab and cam and res):
        raise ErroFormato("os prompts de cena não têm cabeça, Camera: e Constraints: em comum")
    luz = est_mod + ("." if not est_mod.endswith(".") else "") if est_mod else "{luz}"
    cidade = [x for x in ((k.get("evento") or {}).get("local"), (k.get("evento") or {}).get("cidade")) if x]
    loc = next((s.get("Location:") for s in base if s.get("Location:")), "{lugar}, Brazil; local landmarks when natural.")
    for c in cidade:
        loc = loc.replace(c, "{lugar}")
    while "{lugar}, {lugar}" in loc:
        loc = loc.replace("{lugar}, {lugar}", "{lugar}")
    texto = (f"{cab} Scene: {{assunto}} Camera: {cam} Light: {luz} Location: {loc} "
             f"Composition (from the page layout): {{composicao}} Constraints: {res}\n")
    nota = {"prompts_de_cena": len(sec), "com_o_estilo_cena": len(com_estilo),
            "concordam": {"cabeca": n_cab, "camera": n_cam, "restricoes": n_res}, "estilo_na_origem": est_orig}
    return texto, nota


ROTULO_LINHA = re.compile(r"^([A-Z][A-Za-z/ ]{2,30}):\s")
LACUNA_DA_LINHA = {"Composition/framing": "enquadramento", "Page placement": "posicao_na_pagina",
                   "Perspective": "perspectiva", "Lighting/mood": "luz", "Background": "fundo"}


def modelo_objeto(prompts, kit):
    """prompts = [(texto, meta)] dos objetos (sem pattern). Normaliza o que é de cada asset (arquivo, assunto, rumo,
    motivo, cores, estilo da família com lacunas); linha igual em todos fica, linha que varia vira '<Rótulo>: {lacuna}'
    (gerada pelo elementos_prompt.py a partir da composição)."""
    norm = []
    for txt, meta in prompts:
        t = sanitizar(txt, kit)
        t = re.sub(r"save it exactly as .*? \(PNG\)\.", "save it exactly as {arquivo} (PNG).", t)
        if meta.get("descricao"):
            t = t.replace(meta["descricao"], "{assunto}")
        if meta.get("estilo"):
            t = t.replace(meta["estilo"], estilo_familia_modelo(meta["estilo"])[0])
        t = re.sub(r"toward the (?:upper |lower )?(?:left|right)\b", "toward the {rumo}", t)
        t = re.sub(r"^Theme: .*? \(a visual theme", "Theme: {motivo} (a visual theme", t, flags=re.M)
        t = re.sub(r"^Color palette: .*?;", "Color palette: {cores};", t, flags=re.M)
        norm.append(t.rstrip("\n").split("\n"))
    if not norm:
        return None, {}
    n, _ = _moda(len(l) for l in norm)
    grupo = [l for l in norm if len(l) == n]
    out = []
    for i in range(n):
        linhas = {l[i] for l in grupo}
        if len(linhas) == 1:
            out.append(grupo[0][i])
            continue
        m = ROTULO_LINHA.match(grupo[0][i])
        rot = m.group(1) if m else None
        out.append(f"{rot}: {{{LACUNA_DA_LINHA.get(rot, _slug(rot).replace('-', '_'))}}}" if rot else "{linha_variavel}")
    return "\n".join(out) + "\n", {"prompts_de_objeto": len(norm), "mesma_estrutura": len(grupo)}


# ================================================================================================= travado e trocar
def _receita(k):
    rs = k.get("receitas") or []
    return rs[0] if rs else {}


def _paleta_inversa(rec):
    return {v.upper(): c for c, v in (rec.get("paleta") or {}).items() if isinstance(v, str)}


def _familia_da_receita(k, rec):
    se = k.get("sistema_elementos") or {}
    fid = ((se.get("receitas") or {}).get(rec.get("id")) or {}).get("familia")
    fams = se.get("familias") or []
    return next((f for f in fams if f.get("id") == fid), fams[0] if fams else None)


def travado_do_kit(k, tema_css=None, estrito=False):
    """O que o formato trava, extraído do mediakit.json (e do tema-projeto.css, em bytes). O mesmo cálculo serve ao
    exportar e ao conferir: a diferença entre os dois é a diferença do kit contra o formato."""
    rec = _receita(k)
    nomes = papeis_do_kit(k)
    papel = lambda i: "{" + nomes[i] + "}" if i in nomes else i
    se = k.get("sistema_elementos") or {}
    marca = k.get("marca") or {}
    inv = _paleta_inversa(rec)
    t = {}
    receita = {c: copy.deepcopy(rec[c]) for c in ("nome", "fontes", "fundo", "mascara", "pattern_paginas", "variantes") if c in rec}
    receita["paleta"] = {c: v for c, v in (rec.get("paleta") or {}).items() if c in PALETA_FIXA}
    if rec.get("pattern"):
        receita["pattern"] = papel(rec["pattern"])
    t["receita"] = receita
    t["marca"] = {c: marca[c] for c in ("direcao", "assinatura", "fonte_display", "fonte_corpo") if c in marca}
    t["motivos"] = [copy.deepcopy(m) for m in se.get("motivos") or [] if m.get("origem") == "esporte"]
    t["constantes"] = copy.deepcopy(se.get("constantes") or [])
    fam = _familia_da_receita(k, rec)
    if fam:
        try:
            estilo, _ = estilo_familia_modelo(fam.get("estilo"))
        except ErroFormato:
            if estrito:
                raise
            estilo = fam.get("estilo")     # conferir: o kit escreveu o estilo de outro jeito; a diferença aparece
        fm = {"id": fam.get("id"), "meio": fam.get("meio"), "luz": fam.get("luz"), "estilo": estilo,
              "paleta": [inv.get(str(h).upper(), h[1:-1] if LACUNA.fullmatch(str(h)) else h) for h in fam.get("paleta") or []]}
        for c in ("traco_px", "traco_px_min", "traco_px_max"):
            if c in fam:
                fm[c] = fam[c]
        if fam.get("ancora"):
            fm["ancora"] = papel(fam["ancora"])
        t["familia_modelo"] = fm
    re_ = (se.get("receitas") or {}).get(rec.get("id")) or {}
    esporte = {m["id"] for m in t["motivos"]}
    t["receita_elementos"] = {"familia": re_.get("familia"), "motivos": [m for m in re_.get("motivos") or [] if m in esporte],
                              "pattern": papel(re_["pattern"]) if re_.get("pattern") else None}
    comp = k.get("composicao") or {}
    rx = _padrao_ids(nomes)
    t["gramatica"] = {ch: lacunas_de_conteudo(trocar_ids(ent, nomes, rx)) for ch, ent in comp.items()
                      if not ch.startswith("_") and isinstance(ent, dict) and not eh_da_pagina(ch, k)}
    t["padroes"] = sorted({p for ent in comp.values() if isinstance(ent, dict) for p in ent.get("padroes") or []})
    t["tema_projeto_css"] = {"arquivo": "tema-projeto.css", "sha256": sha256_bytes(tema_css)} if tema_css is not None else None
    dc = k.get("direcao_criativa") or {}
    t["direcao_criativa"] = {"intensidade": copy.deepcopy(dc.get("intensidade") or INTENSIDADE_PADRAO),
                             "recursos": copy.deepcopy(dc.get("recursos") or [])}
    return t


def trocar_do_kit(k):
    """O que é do cliente: cada item tem as chaves do kit que ele ocupa e o valor na origem."""
    rec = _receita(k)
    marca = k.get("marca") or {}
    pal = rec.get("paleta") or {}
    itens = []
    na = {"receitas[].paleta.marca": pal.get("marca")}
    for c in ("cor_primaria", "cor_secundaria"):
        if marca.get(c):
            na[f"marca.{c}"] = marca[c]
    itens.append({"id": "paleta-marca", "o_que": "a cor da marca do cliente (acento) e o tom claro dela",
                  "chaves": list(na), "na_origem": na})
    if pal.get("apoio"):
        itens.append({"id": "paleta-apoio", "o_que": "a cor de apoio do cliente", "chaves": ["receitas[].paleta.apoio"],
                      "na_origem": {"receitas[].paleta.apoio": pal["apoio"]}})
    for m in (k.get("sistema_elementos") or {}).get("motivos") or []:
        if m.get("origem") in ("simbolo", "territorio"):
            itens.append({"id": f"motivo-{m['id']}", "o_que": f"motivo de origem {m['origem']} do cliente",
                          "chaves": [f"sistema_elementos.motivos[{m['id']}]"], "na_origem": copy.deepcopy(m)})
    if marca.get("estilo_cena"):
        mod, orig = estilo_cena_modelo(marca["estilo_cena"])
        itens.append({"id": "estilo-cena", "o_que": "o bloco de estilo das cenas: momento, lugar, material da paisagem e "
                      "cor das roupas do cliente; a luz, a lente e a atmosfera ficam como no modelo",
                      "chaves": ["marca.estilo_cena"], "na_origem": {"marca.estilo_cena": marca["estilo_cena"]},
                      "modelo": mod, "lacunas_na_origem": orig})
    lid = marca.get("logo_id")
    logo = next((a for a in k.get("acervo") or [] if a.get("id") == lid), None)
    itens.append({"id": "logo", "o_que": "o logo do cliente", "chaves": ["marca.logo_id", f"acervo[{lid}]"],
                  "na_origem": {"marca.logo_id": lid, "arquivo": (logo or {}).get("arquivo")}})
    fio = (k.get("direcao_criativa") or {}).get("fio_condutor")
    if fio:
        # O fio condutor veste um motivo do cliente (direcao_criativa.fio_condutor.motivo), então é dele: viaja em
        # `trocar`, e o `aplicar` o herda quando o kit novo ainda não tem fio (cliente que volta com o mesmo formato).
        itens.append({"id": "fio-condutor", "o_que": "o fio condutor do kit de origem (motivo do cliente e papel por página)",
                      "chaves": ["direcao_criativa.fio_condutor"], "na_origem": {"direcao_criativa.fio_condutor": copy.deepcopy(fio)}})
    return itens


# ================================================================================================= nao_tem
def nao_tem(k, planos):
    """O que a skill sabe fazer e este kit não usa (calculado, nunca declarado)."""
    out = {}
    tipos_usados = {pg.get("tipo") for p in planos for pg in p.get("paginas") or []}
    try:
        import render
        out["tipos_de_pagina"] = sorted(set(render.PLANO) - tipos_usados)
    except Exception as e:  # o render importa o Chromium e o Jinja; sem eles, fica registrado
        out["tipos_de_pagina"] = f"não calculado ({type(e).__name__})"
    comp = k.get("composicao") or {}
    se = k.get("sistema_elementos") or {}
    usados = {c.get("tipo") for c in se.get("constantes") or []}
    for ent in comp.values():
        for e in (ent.get("elementos") or []) if isinstance(ent, dict) else []:
            if (e.get("grafismo") or {}).get("tipo"):
                usados.add(e["grafismo"]["tipo"])
            modo = (e.get("ancora") or {}).get("modo")
            if modo:
                usados.add("colchetes" if modo == "emoldura" else "fio")
    try:
        import grafismos
        out["grafismos"] = sorted(set(grafismos.TIPOS) - usados)
    except Exception as e:
        out["grafismos"] = f"não calculado ({type(e).__name__})"
    sch = json.loads(SCHEMA_ELEMENTOS.read_text(encoding="utf-8"))
    enum = sch["definitions"]["sistema_elementos"]["properties"]["constantes"]["items"]["properties"]["tipo"]["enum"]
    out["constantes"] = sorted(set(enum) - {c.get("tipo") for c in se.get("constantes") or []})
    var_sch = json.loads(SCHEMA_KIT.read_text(encoding="utf-8"))["properties"]["receitas"]["items"]["properties"]["variantes"]["properties"]
    var_kit = _receita(k).get("variantes") or {}
    falta = {}
    for tipo, d in var_sch.items():
        enum_t = d.get("enum") or (d.get("items") or {}).get("enum") or []
        v = var_kit.get(tipo)
        usadas = set(v) if isinstance(v, list) else {v}
        resto = [x for x in enum_t if x not in usadas]
        if resto:
            falta[tipo] = resto
    out["variantes"] = falta
    if INDICE_REPERTORIO.exists():
        ids = [p["id"] for p in json.loads(INDICE_REPERTORIO.read_text(encoding="utf-8")).get("padroes") or []]
        usados_p = {p for ent in comp.values() if isinstance(ent, dict) for p in ent.get("padroes") or []}
        out["padroes_do_repertorio"] = sorted(set(ids) - usados_p)
    dc = k.get("direcao_criativa") or {}
    contrato = {
        "direcao_criativa": bool(dc),
        "direcao_criativa.consulta": bool(dc.get("consulta")),
        "direcao_criativa.recursos": bool(dc.get("recursos")),
        "direcao_criativa.fio_condutor": bool(dc.get("fio_condutor")),
        "composicao.<rótulo>.acabamento": any(isinstance(e, dict) and e.get("acabamento") for e in comp.values()),
        "composicao.<rótulo>.elementos[].efeito": any(el.get("efeito") for e in comp.values() if isinstance(e, dict)
                                                       for el in e.get("elementos") or []),
        "elementos[].material": any(e.get("material") for e in k.get("elementos") or []),
    }
    out["acabamento_v9"] = sorted(c for c, tem in contrato.items() if not tem)
    out["listas_vazias"] = sorted(c for c, v in k.items() if isinstance(v, list) and not v)
    return out


# ================================================================================================= prova
def _fonte(tam):
    for c in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(c, tam)
        except Exception:
            pass
    return ImageFont.load_default()


def miniatura(origem):
    im = (origem if isinstance(origem, Image.Image) else Image.open(origem)).convert("RGB")
    w, h = im.size
    return im.resize((MINI_LARGURA, max(1, round(MINI_LARGURA * h / w))), Image.LANCZOS)


def blocos(mini):
    """Média de cada bloco de BLOCO×BLOCO px da miniatura, por canal, arredondada (uint8). Compara render com render
    sem depender da compressão da miniatura guardada."""
    a = np.asarray(mini, dtype=np.float32)
    h, w = a.shape[0] // BLOCO * BLOCO, a.shape[1] // BLOCO * BLOCO
    a = a[:h, :w].reshape(h // BLOCO, BLOCO, w // BLOCO, BLOCO, 3).mean(axis=(1, 3))
    return np.clip(np.rint(a), 0, 255).astype(np.uint8)


def assinatura_da_pagina(png):
    mini = miniatura(png)
    b = blocos(mini)
    with Image.open(png) as im:
        w, h = im.size
    return mini, {"w": w, "h": h, "sha256": sha256_arq(png),
                  "blocos": {"lado": BLOCO, "linhas": int(b.shape[0]), "colunas": int(b.shape[1]),
                             "rgb_base64": base64.b64encode(b.tobytes()).decode("ascii")}}


def comparar_assinatura(assinatura, pasta_png):
    """[(arquivo, estado, detalhe)] de cada página da assinatura contra os PNG de `pasta_png`. Estados: igual (mesmo
    sha256), dentro (sha256 mudou, nenhum bloco mudou mais que LIMIAR_BLOCO), diferente, falta; e `a mais` para PNG do
    render que a assinatura não tem."""
    pasta_png = Path(pasta_png)
    out, vistos = [], set()
    for p in assinatura.get("paginas") or []:
        vistos.add(p["arquivo"])
        try:
            alvo = dentro_do_kit(pasta_png, p["arquivo"])
        except ForaDoKit as e:
            raise ErroFormato(f"assinatura: {e}")
        if not alvo.exists():
            out.append((p["arquivo"], "falta", "o render não gerou esta página"))
            continue
        if sha256_arq(alvo) == p["sha256"]:
            out.append((p["arquivo"], "igual", "sha256 igual"))
            continue
        with Image.open(alvo) as im:
            tam = im.size
        if list(tam) != [p["w"], p["h"]]:
            out.append((p["arquivo"], "diferente", f"tamanho {tam[0]}x{tam[1]}, era {p['w']}x{p['h']}"))
            continue
        bl = p["blocos"]
        ref = np.frombuffer(base64.b64decode(bl["rgb_base64"]), dtype=np.uint8).reshape(bl["linhas"], bl["colunas"], 3)
        novo = blocos(miniatura(alvo))
        if novo.shape != ref.shape:
            out.append((p["arquivo"], "diferente", "grade de blocos diferente"))
            continue
        d = np.abs(novo.astype(np.int16) - ref.astype(np.int16)).max(axis=2)
        pior = float(d.max())
        n = int((d > LIMIAR_BLOCO).sum())
        if n:
            y, x = np.unravel_index(int(d.argmax()), d.shape)
            esc = p["w"] / MINI_LARGURA
            out.append((p["arquivo"], "diferente", f"{n} blocos mudaram (pior {pior:.0f} em x≈{int(x * BLOCO * esc)}, "
                                                    f"y≈{int(y * BLOCO * esc)} px da página)"))
        else:
            out.append((p["arquivo"], "dentro", f"sha256 mudou; maior bloco {pior:.0f} (limite {LIMIAR_BLOCO:.0f})"))
    for extra in sorted(q.name for q in pasta_png.glob(assinatura.get("padrao", "*.png"))):
        if extra not in vistos:
            out.append((extra, "a mais", "página que a assinatura não tem"))
    return out


def folha_de_contato(itens, saida, titulo):
    """itens = [(miniatura, rótulo)]. Horizontais em 3 colunas; verticais numa faixa no fim, na altura de uma linha."""
    gut, rot_h, cab = 16, 30, 56
    cel_w, cel_h = MINI_LARGURA, round(MINI_LARGURA * 9 / 16)
    horiz = [(m, r) for m, r in itens if m.width >= m.height]
    vert = [(m, r) for m, r in itens if m.width < m.height]
    linhas_h = -(-len(horiz) // 3)
    larg = 3 * cel_w + 4 * gut
    alt = cab + linhas_h * (cel_h + rot_h + gut) + ((cel_h + rot_h + gut) if vert else 0) + gut
    folha = Image.new("RGB", (larg, alt), (24, 24, 26))
    dr = ImageDraw.Draw(folha)
    dr.text((gut, 16), titulo, fill=(240, 240, 240), font=_fonte(22))
    f = _fonte(16)
    for i, (m, r) in enumerate(horiz):
        x, y = gut + (i % 3) * (cel_w + gut), cab + (i // 3) * (cel_h + rot_h + gut)
        folha.paste(m.resize((cel_w, cel_h)) if m.size != (cel_w, cel_h) else m, (x, y))
        dr.text((x, y + cel_h + 6), r, fill=(220, 220, 220), font=f)
    if vert:
        y = cab + linhas_h * (cel_h + rot_h + gut)
        x = gut
        for m, r in vert:
            v = m.resize((round(cel_h * m.width / m.height), cel_h))
            folha.paste(v, (x, y))
            dr.text((x, y + cel_h + 6), r, fill=(220, 220, 220), font=f)
            x += max(v.width, 210) + gut
    folha.save(saida, quality=85)


# ================================================================================================= exportar
def _entrada_historico(kit, historico):
    try:
        hs = json.loads(Path(historico).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for h in hs if isinstance(hs, list) else []:
        if h.get("id") == kit.name or (h.get("pasta") and Path(h["pasta"]).name == kit.name):
            return h
    return None


def _lista_no_kit(kit, padrao):
    """Arquivos do kit por glob, cada um confinado (link para fora reprova o export)."""
    return [no_kit(kit, str(p.relative_to(kit))) for p in sorted(kit.glob(padrao)) if p.is_file() or p.is_symlink()]


def montar(kit, fid, historico=None, prefixo="", versao=1, hoje=None):
    """(formato, {caminho relativo: bytes}) sem gravar nada."""
    kit, k = ler_kit(kit)
    rec = _receita(k)
    rid = rec.get("id")
    if not rid:
        raise ErroFormato(f"{kit.name}: sem `receitas` (o formato parte de uma receita)")
    plano_arq = no_kit(kit, f"saida/plano-elementos-{rid}.json")
    if not plano_arq.exists():
        raise ErroFormato(f"{kit.name}: sem saida/plano-elementos-{rid}.json (o formato é o estado FINAL: renderize antes)")
    plano = json.loads(plano_arq.read_text(encoding="utf-8"))
    plano_v_arq = no_kit(kit, f"saida/plano-elementos-{rid}-vertical.json")
    plano_v = json.loads(plano_v_arq.read_text(encoding="utf-8")) if plano_v_arq.exists() else {}
    tema_arq = no_kit(kit, "tema-projeto.css")
    tema = tema_arq.read_bytes() if tema_arq.exists() else None
    metas = {}
    for m in _lista_no_kit(kit, "acervo/**/*.meta.json"):
        d = json.loads(m.read_text(encoding="utf-8"))
        metas[d.get("id") or m.name.removesuffix(".meta.json")] = d
    pngs = _lista_no_kit(kit, f"saida/png/kit-{rid}-*.png")
    if not pngs:
        raise ErroFormato(f"{kit.name}: sem saida/png/kit-{rid}-*.png (render.py --png)")
    hist = _entrada_historico(kit, historico or HISTORICO)

    nomes = papeis_do_kit(k)
    travado = travado_do_kit(k, tema, estrito=True)
    padroes_hist = sorted((hist or {}).get("padroes") or {})
    origem = {"kit": kit.name, "pasta": (hist or {}).get("pasta"), "receita": rid,
              "schema_version": k.get("schema_version"), "historico_id": (hist or {}).get("id"),
              "ideia": rec.get("ideia"),
              "sha256": {"mediakit.json": sha256_arq(no_kit(kit, "mediakit.json")),
                         f"saida/plano-elementos-{rid}.json": sha256_arq(plano_arq),
                         "tema-projeto.css": sha256_bytes(tema) if tema is not None else None}}
    if hist and padroes_hist != travado["padroes"]:
        origem["padroes_divergentes"] = {"historico": padroes_hist, "composicao": travado["padroes"]}

    comp = k.get("composicao") or {}
    els = {e["id"]: e for e in k.get("elementos") or [] if e.get("id")}
    aparece = {}
    for ch, ent in comp.items():
        for e in (ent.get("elementos") or []) if isinstance(ent, dict) else []:
            if e.get("id") in nomes and not e.get("grafismo"):
                aparece.setdefault(e["id"], []).append(ch)
    for r in k.get("receitas") or []:
        if r.get("pattern") in nomes:
            aparece.setdefault(r["pattern"], []).extend(f"pattern:{p}" for p in r.get("pattern_paginas") or [])
    papeis = {}
    for eid, nome in nomes.items():
        e, m = els.get(eid) or {}, metas.get(eid) or {}
        papeis[nome] = {"origem": eid, "classe": _classe(e), "tipo": e.get("tipo"), "rota": e.get("rota"),
                        "aspecto": e.get("aspecto"), "motivo": e.get("motivo"), "familia": e.get("familia"),
                        "gerado": e.get("gerado"), "descricao": m.get("descricao"), "aparece_em": aparece.get(eid, [])}
    rx = _padrao_ids(nomes)
    exemplos = {ch: trocar_ids(ent, nomes, rx) for ch, ent in comp.items()
                if not ch.startswith("_") and isinstance(ent, dict) and eh_da_pagina(ch, k)}

    tratamentos = []
    for eid, m in sorted(metas.items()):
        for t in m.get("tratamentos") or []:
            tratamentos.append({"elemento": "{" + nomes[eid] + "}" if eid in nomes else eid, "o_que": t.get("o_que"),
                                "porque": t.get("porque"), "em": t.get("em")})
    for a in k.get("acervo") or []:
        if a.get("composta"):
            item = {"acervo": a.get("id"), "o_que": "composta pelo compor.py (lettering ou SEU LOGO AQUI em perspectiva)"}
            if a.get("paineis"):
                pj = no_kit(kit, a["paineis"])
                if pj.exists():
                    lote = json.loads(pj.read_text(encoding="utf-8"))   # compor.py --lote: lista de aplicações
                    item["paineis"] = {"arquivo": a["paineis"], "quantos": len(lote) if isinstance(lote, list) else None}
            tratamentos.append(item)
        if a.get("gerada") and a.get("rotulo"):
            tratamentos.append({"acervo": a.get("id"), "o_que": f"rótulo na página: {a['rotulo']}"})

    arquivos = {}
    p = lambda rel: prefixo + rel
    if tema is not None:
        arquivos[p("tema-projeto.css")] = tema

    # prompts
    cenas, objetos, exemplos_p = [], [], []
    for arq in _lista_no_kit(kit, "acervo/*.prompt.txt"):
        txt = arq.read_text(encoding="utf-8")
        tipo = "cena" if ("Scene:" in txt and "Light:" in txt) else "limpeza" if txt.lstrip().startswith("Edit") else "outro"
        if tipo == "cena":
            cenas.append(txt)
        exemplos_p.append((arq, tipo, txt))
    for arq in _lista_no_kit(kit, "acervo/elementos/*.prompt.txt"):
        txt = arq.read_text(encoding="utf-8")
        eid = arq.name.removesuffix(".prompt.txt")
        meta = metas.get(eid) or {}
        tipo = "pattern" if meta.get("tipo") == "pattern" else "objeto"
        if tipo == "objeto":
            objetos.append((txt, meta))
        exemplos_p.append((arq, tipo, txt))
    prompts = {"lacunas": {
        "assunto": "o que a cena ou o objeto mostra (cena: o lugar e quem está nele; objeto: a peça, com o estado de uso; "
                   "no estilo da família, a classe da peça, como 'sports object')",
        "momento": "a hora e o dia do evento ('Saturday morning'), em inglês",
        "lugar": "a região e a cidade do evento, em inglês",
        "material": "o chão, a paisagem e os materiais (cena) ou o material da peça (objeto), em inglês",
        "cores": "o nome das cores do cliente, nunca o hex (cena_prompt.nome_cor e paleta_nomes da ficha)",
        "composicao": "escrito pelo cena_prompt.py --composicao, medido na maquete; nunca à mão",
        "arquivo": "escrito pelo elementos.sh", "motivo": "o motivo do sistema_elementos, sem hífen",
        "rumo": "para onde a peça olha, pela composição da página (elementos_prompt.py)",
        "enquadramento": "pelo aspecto da ficha (elementos_prompt.py)",
        "posicao_na_pagina": "pela âncora e escala da composição (elementos_prompt.py)"}, "exemplos": []}
    if cenas:
        t, nota = modelo_cena(cenas, k)
        arquivos[p("prompts/cena.modelo.txt")] = t.encode("utf-8")
        prompts["cena"] = {"modelo": p("prompts/cena.modelo.txt"), **nota}
    if objetos:
        t, nota = modelo_objeto(objetos, kit)
        arquivos[p("prompts/objeto.modelo.txt")] = t.encode("utf-8")
        prompts["objeto"] = {"modelo": p("prompts/objeto.modelo.txt"), **nota}
    for arq, tipo, txt in exemplos_p:
        rel = p(f"prompts/exemplos/{arq.name}")
        arquivos[rel] = sanitizar(txt, kit).encode("utf-8")   # exemplo do cliente: fica como foi, sem caminho do Mac
        prompts["exemplos"].append({"arquivo": rel, "tipo": tipo, "de": str(arq.relative_to(kit))})

    # prova
    rotulos = {}
    for pl, pref in ((plano, f"kit-{rid}-"), (plano_v, f"kit-{rid}-vertical-")):
        for pg in pl.get("paginas") or []:
            ch = (pg.get("composicao") or {}).get("chave")
            rot = pg.get("rotulo") or pg.get("tipo")
            rotulos[f"{pref}{int(pg['n']):02d}.png"] = f"{ch} ({rot})" if ch and ch != rot and not rot.startswith(ch) else rot
    paginas, mini_itens = [], []
    for png in pngs:
        mini, ass = assinatura_da_pagina(png)
        buf = _jpeg(mini)
        rel_m = p(f"prova/miniaturas/{png.stem}.jpg")
        arquivos[rel_m] = buf
        rot = rotulos.get(png.name, "")
        paginas.append({"arquivo": png.name, "rotulo": rot,
                        "formato": "vertical" if "-vertical-" in png.name else "horizontal", **ass,
                        "miniatura": rel_m, "miniatura_sha256": sha256_bytes(buf)})
        num = png.stem.rsplit("-", 1)[-1]
        mini_itens.append((mini, f"{'v' if '-vertical-' in png.name else 'p'}.{num} {rot}"))
    assinatura = {"receita": rid, "padrao": f"kit-{rid}-*.png", "miniatura_largura": MINI_LARGURA,
                  "limiar_bloco": LIMIAR_BLOCO,
                  "como_comparar": "sha256 igual = igual; senão, a miniatura de 480 px do render novo é reduzida a blocos "
                                   f"de {BLOCO} px e nenhum bloco pode mudar mais que {LIMIAR_BLOCO:.0f} (0 a 255) em "
                                   "nenhum canal (formato.comparar_assinatura)",
                  "paginas": paginas}
    arquivos[p("prova/assinatura.json")] = json_txt(assinatura).encode("utf-8")
    tmp_folha = Path(tempfile.mkdtemp()) / "referencia.jpg"
    try:
        folha_de_contato(mini_itens, tmp_folha, f"{fid} v{versao} · origem {kit.name} · receita {rid} · "
                                                 f"{sum(1 for x in paginas if x['formato'] == 'horizontal')} + "
                                                 f"{sum(1 for x in paginas if x['formato'] == 'vertical')} páginas")
        arquivos[p("prova/referencia.jpg")] = tmp_folha.read_bytes()
    finally:
        shutil.rmtree(tmp_folha.parent, ignore_errors=True)

    formato = {
        "_leia": "Formato reprodutível (references/11-formatos.md). `travado` é o que o kit herda; `trocar` é do cliente "
                 "e vira pendência; `papeis` diz que elemento do cliente ocupa cada {papel}; `exemplos` são páginas "
                 "específicas da origem, só para ler. Aplicar: formato.py aplicar <id> <kit>. O kit vence o formato.",
        "formato": fid, "versao": versao, "criado_em": (hoje or date.today()).isoformat(),
        "origem": origem, "travado": travado, "trocar": trocar_do_kit(k), "papeis": papeis, "exemplos": exemplos,
        "prompts": prompts, "tratamentos": tratamentos, "nao_tem": nao_tem(k, [plano, plano_v]),
        "prova": {"assinatura": p("prova/assinatura.json"), "referencia": p("prova/referencia.jpg"),
                  "paginas": len(paginas)},
        "para_o_kit": {"tema-projeto.css": p("tema-projeto.css")} if tema is not None else {},
        "arquivos": {rel: sha256_bytes(b) for rel, b in sorted(arquivos.items())},
    }
    texto = json_txt(formato)
    vazou = [m.group(0) for m in CAMINHO_ABSOLUTO.finditer(texto)] + \
            [rel for rel, b in arquivos.items() if rel.endswith(".txt") and CAMINHO_ABSOLUTO.search(b.decode("utf-8", "replace"))]
    if vazou:
        raise ErroFormato(f"o formato carregaria caminho do Mac: {vazou[:3]}")
    return formato, arquivos


def _jpeg(im):
    import io
    b = io.BytesIO()
    im.save(b, "JPEG", quality=MINI_QUALIDADE, optimize=True)
    return b.getvalue()


def versao_nova(pasta, nova_versao):
    """(versão, prefixo dos arquivos) do export. Formato existente só ganha versão nova com --nova-versao."""
    if not pasta.exists():
        return 1, ""
    if not nova_versao:
        raise ErroFormato(f"formatos/{pasta.name} já existe e a versão é imutável; para mudar, exportar com --nova-versao "
                          "(grava versoes/vN.json sem tocar nas anteriores)")
    atuais = [int(m.group(1)) for q in (pasta / "versoes").glob("v*.json") if (m := re.match(r"v(\d+)\.json$", q.name))]
    versao = max(atuais or [1]) + 1
    return versao, f"versoes/v{versao}/"


def exportar(kit, fid, raiz=None, historico=None, nova_versao=False, hoje=None):
    """Grava formatos/<id>/ (ou versoes/vN/ com --nova-versao). Monta tudo numa pasta temporária dentro de formatos/ e
    só então move: export que falha no meio não deixa formato pela metade."""
    pasta = pasta_formato(fid, raiz)
    raiz = pasta.parent
    versao, prefixo = versao_nova(pasta, nova_versao)
    formato, arquivos = montar(kit, fid, historico=historico, prefixo=prefixo, versao=versao, hoje=hoje)
    texto = json_txt(formato).encode("utf-8")
    tmp = Path(tempfile.mkdtemp(prefix=f".{fid}-", dir=raiz))
    try:
        for rel, b in arquivos.items():
            gravar_novo(no_formato(tmp, rel), b)
        gravar_novo(tmp / "versoes" / f"v{versao}.json", texto)
        if versao == 1:
            gravar_novo(tmp / "formato.json", texto)
            os.chmod(tmp, 0o755)       # mkdtemp cria com 0700
            os.rename(tmp, pasta)      # pasta não existia: rename atômico
        else:
            destino = no_formato(pasta, f"versoes/v{versao}")
            if destino.exists() or no_formato(pasta, f"versoes/v{versao}.json").exists():
                raise ErroFormato(f"versoes/v{versao} já existe")
            (pasta / "versoes").mkdir(exist_ok=True)
            os.chmod(tmp / "versoes" / f"v{versao}", 0o755)
            os.rename(tmp / "versoes" / f"v{versao}", destino)
            os.rename(tmp / "versoes" / f"v{versao}.json", pasta / "versoes" / f"v{versao}.json")
            novo = pasta / ".formato.json.novo"
            novo.write_bytes(texto)
            os.replace(novo, pasta / "formato.json")   # formato.json = a última versão; as anteriores ficam em versoes/
            shutil.rmtree(tmp, ignore_errors=True)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return pasta, formato


# ================================================================================================= aplicar
def preencher_ausente(destino, origem, caminho, preenchidos):
    """Só chave ausente; dict dentro de dict desce; o resto (valor, lista) do kit vence."""
    for c, v in origem.items():
        if c not in destino:
            destino[c] = copy.deepcopy(v)
            preenchidos.append(f"{caminho}.{c}")
        elif isinstance(destino[c], dict) and isinstance(v, dict):
            preencher_ausente(destino[c], v, f"{caminho}.{c}", preenchidos)


def _resumo_origem(t):
    """O valor de origem de um item de `trocar`, numa linha."""
    na = t.get("na_origem") or {}
    if t["id"].startswith("motivo-"):
        return na.get("descricao") or na.get("id")
    if t["id"] == "estilo-cena":
        return "; ".join(f"{c} '{v}'" for c, v in (t.get("lacunas_na_origem") or {}).items())
    if t["id"] == "logo":
        return na.get("arquivo") or na.get("marca.logo_id")
    return ", ".join(dict.fromkeys(str(v) for v in na.values() if v))


def com_lacunas_de_prosa(ent):
    ent = copy.deepcopy(ent)
    for c in PROSA:
        if c in ent:
            ent[c] = "{" + c + "}"
    for e in ent.get("elementos") or []:
        if "porque" in e:
            e["porque"] = "{porque}"
    return ent


def _familia_para_kit(fm, paleta):
    f = copy.deepcopy(fm)
    f["paleta"] = [paleta.get(c, "{" + c + "}") if isinstance(c, str) and not c.startswith("#") else c for c in f.get("paleta") or []]
    return f


def lacunas_em(o, caminho=""):
    """[(caminho, texto)] de toda string com lacuna {...} ainda aberta."""
    out = []
    if isinstance(o, dict):
        for c, v in o.items():
            out += lacunas_em(v, f"{caminho}.{c}" if caminho else str(c))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out += lacunas_em(v, f"{caminho}[{i}]")
    elif isinstance(o, str) and LACUNA.search(o):
        out.append((caminho, o))
    return out


def aplicar(fid, kit, versao=None, raiz=None, fontes_livres=None, simular=False, hoje=None):
    pasta, f, bruto = carregar_formato(fid, versao, raiz)
    kit = Path(kit).resolve()
    if not kit.is_dir():
        raise ErroFormato(f"pasta do kit não existe: {kit.name}")
    mk = no_kit(kit, "mediakit.json")
    existia = mk.exists()
    k = json.loads(mk.read_text(encoding="utf-8")) if existia else {}
    base = {"id": fid, "versao": f["versao"], "sha256": sha256_bytes(bruto)}
    if k.get("formato_base") and k["formato_base"] != base:
        raise ErroFormato(f"o kit já tem formato_base {k['formato_base']}; um kit herda de um formato só "
                          "(apague a chave à mão se a troca for de propósito)")
    T = f["travado"]
    feito = []
    preencher_ausente(k.setdefault("marca", {}), T.get("marca") or {}, "marca", feito)
    rec_f = copy.deepcopy(T.get("receita") or {})
    if not k.get("receitas"):
        k["receitas"] = [{"id": "r1", **rec_f}]
        feito.append("receitas[0]")
    else:
        preencher_ausente(k["receitas"][0], rec_f, "receitas[0]", feito)
    rid = k["receitas"][0].get("id") or "r1"
    paleta = k["receitas"][0].get("paleta") or {}
    se = k.setdefault("sistema_elementos", {})
    for c, v in (("motivos", T.get("motivos")), ("constantes", T.get("constantes"))):
        if c not in se and v is not None:
            se[c] = copy.deepcopy(v)
            feito.append(f"sistema_elementos.{c}")
    if "familias" not in se and T.get("familia_modelo"):
        se["familias"] = [_familia_para_kit(T["familia_modelo"], paleta)]
        feito.append("sistema_elementos.familias")
    if "receitas" not in se and T.get("receita_elementos"):
        se["receitas"] = {rid: {c: v for c, v in T["receita_elementos"].items() if v is not None}}
        feito.append("sistema_elementos.receitas")
    comp = k.setdefault("composicao", {})
    copiadas = []
    for ch, ent in (T.get("gramatica") or {}).items():
        if ch not in comp:
            comp[ch] = com_lacunas_de_prosa(ent)
            copiadas.append(ch)
    if copiadas:
        feito.append(f"composicao ({len(copiadas)}: {', '.join(copiadas)})")
    if "direcao_criativa" not in k and T.get("direcao_criativa"):
        k["direcao_criativa"] = copy.deepcopy(T["direcao_criativa"])
        feito.append("direcao_criativa")
    fio = next((t["na_origem"]["direcao_criativa.fio_condutor"] for t in f.get("trocar") or [] if t.get("id") == "fio-condutor"), None)
    if fio and "direcao_criativa" in k and not k["direcao_criativa"].get("fio_condutor"):
        k["direcao_criativa"]["fio_condutor"] = copy.deepcopy(fio)
        feito.append("direcao_criativa.fio_condutor (herdado; confirmar o motivo no kit novo)")
    k["formato_base"] = base

    copiar = []
    tema_dest = no_kit(kit, "tema-projeto.css")
    if T.get("tema_projeto_css") and not tema_dest.exists():
        copiar.append((no_formato(pasta, f["para_o_kit"]["tema-projeto.css"]), tema_dest))
    fontes = k["receitas"][0].get("fontes") or {}
    fl = Path(fontes_livres or FONTES_LIVRES)
    faltam = []
    for fam in dict.fromkeys(x for x in (fontes.get("display"), fontes.get("titulo"), fontes.get("corpo")) if x):
        try:
            src = dentro_do_kit(fl, fam)
        except ForaDoKit:
            raise ErroFormato(f"família de fonte inválida: {fam!r}")
        if not src.is_dir():
            faltam.append(fam)
            continue
        for ttf in sorted(src.glob("*.ttf")):
            alvo = no_kit(kit, f"fontes/{ttf.name}")
            if not alvo.exists():
                copiar.append((ttf, alvo))

    pend = [f"- [ ] Trocar {', '.join(f'`{c}`' for c in t['chaves'])}: {t['o_que']} (na origem: {_resumo_origem(t)})."
            for t in f.get("trocar") or []]
    texto_kit = json.dumps(k, ensure_ascii=False)
    for nome, info in (f.get("papeis") or {}).items():
        if "{" + nome + "}" in texto_kit:
            pend.append(f"- [ ] Preencher o papel `{{{nome}}}` com um elemento do cliente (na origem: `{info.get('origem')}`, "
                        f"{info.get('classe')}, rota {info.get('rota')}, aspecto {info.get('aspecto')}).")
    if copiadas:
        pend.append(f"- [ ] Reescrever a prosa da composição copiada do formato (mensagem, estrutura, porque) em: "
                    f"{', '.join(copiadas)}.")
    if "sistema_elementos.familias" in feito:
        pend.append("- [ ] Família modelo: preencher {assunto} e {material} no estilo e as cores que faltarem na paleta.")
    for fam in faltam:
        pend.append(f"- [ ] Fonte `{fam}` não está em fontes-livres/: trazer o arquivo para fontes/.")

    if simular:
        return {"preenchidos": feito, "copiar": [str(b.relative_to(kit)) for _, b in copiar], "pendencias": pend,
                "formato_base": base}
    if existia:
        backup = no_kit(kit, "mediakit.antes-do-formato.json")
        if not backup.exists():
            shutil.copy2(mk, backup)
    mk.write_text(json.dumps(k, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for src, dst in copiar:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    pend_arq = no_kit(kit, "pendencias.md")
    atual = pend_arq.read_text(encoding="utf-8") if pend_arq.exists() else ""
    ja = {l.strip() for l in atual.splitlines()}
    novas = [l for l in pend if l.strip() not in ja]
    cab = f"## Formato {fid} v{f['versao']}"
    if novas:
        bloco = ("" if not atual or atual.endswith("\n\n") else ("\n" if atual.endswith("\n") else "\n\n"))
        if cab not in atual:
            bloco += (f"{cab} (aplicado em {(hoje or date.today()).strftime('%d/%m/%Y')})\n"
                      "O formato trava receita, constantes, família modelo e gramática; o que é do cliente fica aqui até "
                      "ser trocado (formato.py conferir mostra o que falta).\n")
        pend_arq.write_text(atual + bloco + "\n".join(novas) + "\n", encoding="utf-8")
    return {"preenchidos": feito, "copiar": [str(b.relative_to(kit)) for _, b in copiar], "pendencias": novas,
            "formato_base": base}


# ================================================================================================= conferir
def _diff(a, b, caminho, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for c in list(a) + [c for c in b if c not in a]:
            _diff(a.get(c), b.get(c), f"{caminho}.{c}", out)
    elif a != b:
        out.append((caminho, a, b))


ROTULOS_DO_KIT = ("receita.nome", "familia_modelo.id", "familia_modelo.ancora", "receita_elementos.familia")


def casa_modelo(modelo, texto):
    """O texto preenche o modelo? Cada lacuna {x} do modelo vale qualquer trecho não vazio."""
    partes = re.split(r"(\{[a-z_][a-z0-9_-]*\})", modelo)
    rx = "".join(".+?" if LACUNA.fullmatch(x) else re.escape(x) for x in partes)
    return re.fullmatch(rx, texto or "", flags=re.S) is not None


def conferir(kit, fid=None, versao=None, raiz=None):
    """{"formato", "diferencas": [(caminho, formato, kit)], "lacunas": [(caminho, texto)], "a_mais": [chaves],
    "avisos": [...]}"""
    kit, k = ler_kit(kit)
    fb = k.get("formato_base") or {}
    fid = fid or fb.get("id")
    if not fid:
        raise ErroFormato(f"{kit.name}: sem formato_base; diga qual com --formato <id>")
    pasta, f, bruto = carregar_formato(fid, versao or (fb.get("versao") if fb.get("id") == fid else None), raiz)
    avisos = []
    if fb.get("id") == fid and fb.get("sha256") and fb["sha256"] != sha256_bytes(bruto):
        avisos.append("o formato_base do kit não bate com o sha256 do formato (o arquivo do formato mudou depois de aplicado)")
    tema_arq = no_kit(kit, "tema-projeto.css")
    tk = travado_do_kit(k, tema_arq.read_bytes() if tema_arq.exists() else None)
    tf = f["travado"]
    dif = []
    for c in ("receita", "marca", "familia_modelo", "receita_elementos", "tema_projeto_css"):
        _diff(tf.get(c), tk.get(c), c, dif)
    est_f = (tf.get("familia_modelo") or {}).get("estilo")
    est_k = ((_familia_da_receita(k, _receita(k)) or {}).get("estilo"))
    dif = [d for d in dif if d[0] not in ROTULOS_DO_KIT
           and not (d[0] == "familia_modelo.estilo" and est_f and est_k and casa_modelo(est_f, est_k))]
    for c in ("motivos", "constantes"):
        if tf.get(c) != tk.get(c):
            dif.append((c, tf.get(c), tk.get(c)))
    pf, pk = set(tf.get("padroes") or []), set(tk.get("padroes") or [])
    if pf - pk:
        dif.append(("padroes (faltam no kit)", sorted(pf - pk), None))
    if pk - pf:
        dif.append(("padroes (a mais no kit)", None, sorted(pk - pf)))
    _diff((tf.get("direcao_criativa") or {}).get("intensidade"), (tk.get("direcao_criativa") or {}).get("intensidade"),
          "direcao_criativa.intensidade", dif)
    for ch, ent in (tf.get("gramatica") or {}).items():
        ek = (tk.get("gramatica") or {}).get(ch)
        if ek is None:
            dif.append((f"composicao.{ch}", "(gramática do formato)", None))
        else:
            _diff(estrutural(ent), estrutural(ek), f"composicao.{ch}", dif)
    a_mais = [ch for ch in tk.get("gramatica") or {} if ch not in (tf.get("gramatica") or {})]
    return {"formato": f"{fid} v{f['versao']}", "diferencas": dif, "lacunas": lacunas_em(k), "a_mais": a_mais,
            "avisos": avisos}


def _curto(v, n=90):
    s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    return s if len(s) <= n else s[:n - 3] + "..."


# ================================================================================================= provar
def provar(fid, kit_origem=None, manter=False, raiz=None):
    pasta, f, _ = carregar_formato(fid, None, raiz)
    ass = json.loads(no_formato(pasta, f["prova"]["assinatura"]).read_text(encoding="utf-8"))
    if kit_origem:
        origem = Path(kit_origem).resolve()
    else:
        rel = (f.get("origem") or {}).get("pasta")
        if not rel:
            raise ErroFormato("o formato não sabe onde está o kit de origem: use --kit-origem <pasta>")
        try:
            origem = dentro_do_kit(RAIZ_EMPRESA, rel)
        except ForaDoKit as e:
            raise ErroFormato(f"kit de origem: {e}")
    if not (origem / "mediakit.json").exists():
        raise ErroFormato(f"kit de origem sem mediakit.json: {origem.name} (use --kit-origem)")
    tmp = Path(tempfile.mkdtemp(prefix=f"mk-formato-{fid}-"))
    clone = tmp / origem.name
    try:
        subprocess.run(["cp", "-cR", str(origem), str(clone)], check=True)   # clone do APFS: o kit real nunca é escrito
        shutil.rmtree(clone / "saida", ignore_errors=True)
        cmd = [sys.executable, str(AQUI / "render.py"), str(clone), "--receita", ass["receita"], "--png"]
        if (clone / "fontes").is_dir():
            cmd += ["--fontes", str(clone / "fontes")]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise ErroFormato(f"render.py saiu com {r.returncode}: {(r.stderr or r.stdout)[-800:]}")
        return comparar_assinatura(ass, clone / "saida" / "png"), (tmp if manter else None)
    finally:
        if not manter:
            shutil.rmtree(tmp, ignore_errors=True)


# ================================================================================================= CLI
def cmd_exportar(a):
    pasta, f = exportar(a.kit, a.id, nova_versao=a.nova_versao)
    t = f["travado"]
    tam = sum(q.stat().st_size for q in pasta.rglob("*") if q.is_file())
    print(f"OK formatos/{a.id} v{f['versao']} ({tam / 1024:.0f} KB, {len(f['arquivos']) + 2} arquivos)")
    print(f"   travado: receita {t['receita'].get('nome')!r}, {len(t['constantes'])} constantes, {len(t['motivos'])} motivos de "
          f"esporte, família {t.get('familia_modelo', {}).get('id')}, gramática {len(t['gramatica'])} chaves, "
          f"{len(t['padroes'])} padrões")
    print(f"   trocar: {', '.join(x['id'] for x in f['trocar'])}")
    print(f"   papéis: {', '.join('{' + n + '}=' + v['origem'] for n, v in f['papeis'].items())}")
    print(f"   exemplos: {', '.join(f['exemplos'])}; prova: {f['prova']['paginas']} páginas")


def cmd_aplicar(a):
    r = aplicar(a.id, a.kit, versao=a.versao, simular=a.simular)
    print(("SIMULAÇÃO " if a.simular else "OK ") + f"formato {a.id} v{r['formato_base']['versao']} → {Path(a.kit).name}")
    for c in r["preenchidos"]:
        print(f"   preenchido: {c}")
    for c in r["copiar"]:
        print(f"   copiado: {c}")
    for l in r["pendencias"]:
        print(f"   pendência: {l[6:]}")


def cmd_conferir(a):
    r = conferir(a.kit, a.formato, a.versao)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        for av in r["avisos"]:
            print(f"AVISO  {av}")
        for c, vf, vk in r["diferencas"]:
            print(f"DIFERENÇA  {c}: formato {_curto(vf)} · kit {_curto(vk)}")
        for c, txt in r["lacunas"]:
            print(f"LACUNA  {c}: {_curto(txt)}")
        if r["a_mais"]:
            print(f"(info) composição do kit fora da gramática do formato: {', '.join(r['a_mais'])}")
        print(f"{len(r['diferencas'])} diferenças e {len(r['lacunas'])} lacunas contra {r['formato']}")
    sys.exit(1 if r["diferencas"] or r["lacunas"] else 0)


def cmd_provar(a):
    res, ficou = provar(a.id, a.kit_origem, a.manter)
    ruins = [x for x in res if x[1] in ("diferente", "falta", "a mais")]
    for arq, estado, det in res:
        print(f"{estado.upper():<10} {arq}  {det}")
    print(f"{len(res) - len(ruins)} de {len(res)} páginas iguais à assinatura" + (f" (clone em {ficou})" if ficou else ""))
    sys.exit(1 if ruins else 0)


def main():
    ap = argparse.ArgumentParser(description="formato reprodutível de um kit aprovado")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("exportar"); p.add_argument("kit"); p.add_argument("id"); p.add_argument("--nova-versao", action="store_true")
    p = sub.add_parser("aplicar"); p.add_argument("id"); p.add_argument("kit"); p.add_argument("--versao", type=int); p.add_argument("--simular", action="store_true")
    p = sub.add_parser("conferir"); p.add_argument("kit"); p.add_argument("--formato"); p.add_argument("--versao", type=int); p.add_argument("--json", action="store_true")
    p = sub.add_parser("provar"); p.add_argument("id"); p.add_argument("--kit-origem"); p.add_argument("--manter", action="store_true")
    a = ap.parse_args()
    try:
        {"exportar": cmd_exportar, "aplicar": cmd_aplicar, "conferir": cmd_conferir, "provar": cmd_provar}[a.cmd](a)
    except (ValueError, RuntimeError, OSError) as e:
        print(f"erro: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

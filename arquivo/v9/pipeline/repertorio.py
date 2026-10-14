#!/usr/bin/env python3
"""
repertorio.py: o repertório de composição (references/09-composicao.md, seção 1, passo 5). Padrões de composição
extraídos de referências de estúdio: o PRINCÍPIO de cada um (relação, escala, função, âncora), para copiar a relação e
nunca a forma. O conteúdo mora em repertorio/, na raiz do projeto; esta ferramenta consulta e confere, não escreve conteúdo.

  repertorio/indice.json             schema/repertorio.schema.json (estrito); composicao_exemplo valida como composicao_pagina
  repertorio/padroes/<id>.md         front matter YAML (id, nome, problema, tipo_pagina, funcao, relacao, rota, tom,
                                     densidade) e as seções, nesta ordem: 1. Problema ou efeito, 2. Como se organiza,
                                     3. Onde funciona, 4. O essencial, 5. O que pode variar, 6. Como adaptar, 7. Erros que
                                     estragam, 8. Como construir e conferir, Trecho de composição (bloco ```json: a FONTE do
                                     composicao_exemplo do índice), Referências
  repertorio/referencias/<ref>.md    a ficha de cada referência
  repertorio/recortes/<arquivo>.jpg  o recorte da página que ensina o padrão (`anti: true` = o erro que o padrão evita)

Comandos (a partir de pipeline/; o Claude roda, o Ugo não). Todos aceitam --repertorio <pasta> (padrão ../repertorio).
  buscar [--pagina T] [--problema "texto"] [--funcao F] [--relacao R] [--rota R] [--tom T] [-n 5] [--json]
         ranking determinístico: página +3 (ativo vale ativo_painel e ativo_topo; capa:c, cota:Master valem o tipo), cada
         função +2, cada relação +2, rota +1, cada tom +1, e +1 por palavra do --problema achada no problema do padrão e +1
         por palavra achada no nome (sem acento e sem caixa; plural e radical de 5 letras). Empate: id. Imprime o id, o
         nome, por que casou e o caminho do .md. --funcao, --relacao e --tom podem repetir ou vir separados por vírgula.
  folha <id> [<id>...] --saida <png>
         os recortes desses padrões numa imagem só, com id e legenda (uma leitura); o antiexemplo leva o rótulo NÃO FAZER
  checar índice no schema; .md, recorte e referência existem; ids únicos; front matter com o mesmo id do arquivo e do
         índice; trecho de composição do .md igual ao composicao_exemplo e válido (FALHA); recorte órfão, padrão sem
         recorte, seção fora do roteiro, etiqueta do front matter diferente do índice (AVISO). Sai 1 com FALHA.
  recortar <analise.json> --saida <pasta> [--base-imagens <pasta>]... [--json]
         recortes de uma análise (RUBRICA da análise: padroes[].exemplos[].recorte em fração [x0, y0, x1, y1]) em JPEG,
         lado maior até 900 px, qualidade 80, folga de 3% de cada lado; nome <id_sugerido>__<ref>-<página 2 dígitos>.jpg;
         e a folha de conferência _conferencia-<ref>.jpg na mesma pasta
  html [--saida <arquivo>]   (padrão: repertorio/repertorio.html, ao lado do indice.json; imprime o caminho absoluto)
         página estática para folhear (índice por tipo de página e por problema, recortes, as seções do .md, o trecho de
         composição), caminhos relativos, sem dependência externa, boa no computador e no celular
  usados <pasta-do-kit> [--json]
         os padrões declarados em composicao[*].padroes do mediakit.json (para o histórico de kits)

Captura das galerias (o estudo anterior guardava só o que a análise citava; aqui vêm TODAS as páginas de cada referência):
  repertorio/fontes.json             as fontes: {id, url, tipo behance|web|pdf|regua, camada prioritaria|profunda|releitura|lente|
                                     regua|fora, largura}. regua e fora não têm captura
  repertorio/capturas/<ref>/NN.jpg   as páginas (RGB, até --largura px, JPEG q85); _mini/NN.jpg (800 px) e _folha-1.jpg, _folha-2.jpg
                                     (folhas de contato, 20 páginas cada). NÃO é rastreado pelo git (ver .gitignore)
  repertorio/fontes/<ref>.json       manifesto rastreado: {url, canonica, capturada_em, status ok|suspeita|bloqueada|vazia,
                                     paginas: [{n, modulo_url, fatia, w, h, kb, sha256}]} (e, depois do conferir-captura, v1_para_v2)
  capturar [--ref ID ...] [--camada C ...] [--largura 1400] [--pausa 4] [--forcar] [--listar]
         Playwright headless com a identificação do regua.py (regua.UA): rola a galeria, lê os módulos do projeto (HTML e DOM),
         baixa /1400/, depois /max_1200/, depois o original; descarta largura < 900 e altura < 0,2 da largura; módulo alto (> 1,9
         da largura) é fatiado nas faixas de cor uniforme entre slides (sem faixa, em 16:9 com 4% de sobreposição). Uma galeria
         por vez, --pausa s entre elas, 2 tentativas com 30 s de espera. Pula quem já tem manifesto ok (salvo --forcar). Só grava
         em capturas/<ref>/ e só sobrescreve arquivo do próprio manifesto. 3 bloqueios seguidos (403, captcha, no Behance também página sem módulos) param
         com código 3; menos de 1,8 GB livres ou capturas/ acima de 900 MB param com código 4. Sem --ref nem --camada, só --listar.
         Nunca usa modo furtivo, proxy, login nem tenta resolver CAPTCHA.
  folha-contato <ref> [<ref>...]     regera as folhas de contato a partir das páginas já capturadas
  conferir-captura <ref> [<ref>...]  compara com o estudo anterior: a contagem de páginas (ficha e recortes) e, para cada recorte
         do índice, a página onde ele aparece agora (cv2.matchTemplate; nota < 0,8 na página citada procura nas outras e grava
         v1_para_v2 {pagina_v1: pagina_v2} no manifesto)

Camada de acabamento (v2, estudo visual de 12/10/2026; só acréscimo: o índice v1 e os comandos acima continuam iguais):
  repertorio/recursos/<id>.md        front matter (briefing-redator-v2.md; `provisorio: true` fica só no .md), as 8 seções (1. Efeito
                                     a 8. Como produzir e conferir), `## Trecho de acabamento` ({direcao_criativa, pagina}, o que o kit
                                     copia) e `## Referências` (`- <ref> p. N (o que mostra; recorte recortes/<id>__<ref>-<pp>.jpg, ...)`)
  repertorio/recortes/_anotar-<ref>.json  o que o `anotar` gravou: anotações em fração do recorte, caixa na página, origem
  repertorio/mapas/<ref>-<pp>.jpg    a página inteira (1200 px) com os recortes marcados
  anotar <analise.json> --saida <pasta> [--todos] [--base-imagens <pasta>]... [--json]
         candidatos aceitos (de <ref>.aceitos.json ou status aceito; todos com --todos): recorte limpo como o `recortar` e a versão
         --anotado.jpg (caixa #FFD400 entre contornos escuros, seta de 4 px, disco de 30 px; o rótulo na faixa abaixo, nunca sobre
         a peça); recorte vazio (área > 85% num recurso de detalhe, < 2%, desvio de luminância < 4, dHash repetido) vira AVISO
  mapa <ref> <pagina> [--analise <json>]... [--saida <jpg>]
  indexar [--escrever]   recursos[] do índice a partir dos .md (o .md é a fonte); grava versao 2 só se o índice valer no schema
  checar  (o de cima) mais: recurso fora do contrato, .md diferente do índice, trecho inválido (schema do kit, composicao.validar,
         acabamento.validar), comando da seção 8 que não existe em pipeline/, recurso sem recorte, recorte sem anotado ou com
         anotação fora, travessão (FALHA); uma referência só, eixo faltando, parcial sem `depende`, referência v2 sem `serie`,
         recorte repetido ou vazio, recurso que divide mais da metade dos recortes com um padrão, .md fora de 70 a 130 linhas (AVISO)
  buscar --entidade padrao|recurso|todos [--dimensao --recurso --material --luz --profundidade --intensidade --continuidade
         --tratamento --tipografia --borda --via] [--sem-risco-pdf] [--uau-min N]
         recurso: página +3, dimensão +2, recurso +2, o resto +1; sem --entidade (padrao) a saída é a de sempre
  serie <ref> [--json]   constantes, variáveis, por tipo e ritmo (do índice; sem ela, das análises em estudo/analise-v2/)
  cobertura [--json]     dimensões x recursos x referências; rala = menos de 3 recursos ou de 3 referências
  usados <pasta-do-kit>  também os recursos (direcao_criativa.recursos, composicao.*.acabamento.recursos e elementos[].recurso)
  consultar <pasta-do-kit> [--historico <json>]
         etapa 3b: Leitura do direcao-criativa.md (ou direcao-de-arte.md), tipos de página e histórico; busca por família e grava
         consulta-repertorio.json ({consultas, ids, indice_sha256, data, ...}, que o qa_conjunto confere) e mood/consulta-recursos.png

Os vocabulários (função, relação, tipo de página, rota, tom, densidade) são os de composicao.py e regua.py; o schema repete
a lista e a prova confere que ela não se afasta deles. Dois acréscimos, porque a rubrica da análise os usa: a relação `fundo`
(textura ou pattern numa região, que não é âncora de elemento) e o tipo de página `outro`.
buscar, folha e html recusam, com mensagem, um índice fora do schema (rode `checar` para a lista completa).
"""
import argparse, datetime, functools, hashlib, html as _html, io, json, os, re, shutil, subprocess, sys, tempfile, time, unicodedata
from pathlib import Path
from urllib.parse import quote

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
RAIZ = AQUI.parent / "repertorio"
SCHEMA = AQUI.parent / "schema" / "repertorio.schema.json"
SCHEMA_ELEMENTOS = AQUI.parent / "schema" / "elementos.schema.json"

# vocabulários: os de composicao.py (FUNCOES, RELACOES) e regua.py (TIPOS) mais o que a rubrica da análise usa
TIPOS_EXTRAS = ("territorio", "historico_logos", "redes", "premiacao", "outro")
ROTAS = ("codigo", "imagem", "hibrido")
TONS = ("causa", "performance", "territorio", "festa", "corporativo")
DENSIDADES = ("respiro", "media", "alta")
ALIAS_PAGINA = {"ativo": ("ativo_painel", "ativo_topo")}
SECOES = ("Problema ou efeito", "Como se organiza", "Onde funciona", "O essencial", "O que pode variar", "Como adaptar",
          "Erros que estragam", "Como construir e conferir")
LADO_MAX = 900          # lado maior do recorte, em px
QUALIDADE = 80          # JPEG
FOLGA = 0.03            # de cada lado, em fração da página
PARADAS = frozenset("a o as os um uma uns umas de da do das dos em no na nos nas por para com sem sob sobre e ou que se ao aos "
                    "ser como mais menos mas ja nao tem ter sao entre ate cada todo toda todos todas seu sua seus suas ele ela "
                    "eles elas isso esse essa este esta estes estas quando onde qual quais so muito muita pouco pouca".split())


def vocabularios():
    """(funcoes, relacoes, tipos de página) aceitos pelo repertório, lidos de composicao.py e regua.py."""
    import composicao, regua
    return composicao.FUNCOES, composicao.RELACOES + ("fundo",), tuple(regua.TIPOS) + TIPOS_EXTRAS


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().casefold()


def _radicais(texto):
    """Palavras significativas, sem acento e sem caixa, sem plural e cortadas em 5 letras (número, números, numeral
    casam em 'numer'); stopwords de fora."""
    out = set()
    for w in re.findall(r"[a-z0-9]+", norm(texto)):
        if len(w) < 3 or w in PARADAS:
            continue
        if w.endswith("s") and len(w) > 3:
            w = w[:-1]
        out.add(w[:5] if len(w) > 5 else w)
    return out


# ---------------------------------------------------------------- front matter e markdown
def _escalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        try:
            return json.loads(v)
        except ValueError:
            return v[1:-1]
    if len(v) >= 2 and v[0] == v[-1] == "'":
        return v[1:-1].replace("''", "'")
    return re.sub(r"\s+#.*$", "", v)


def _dividir_virgulas(s):
    partes, atual, aspas = [], "", None
    for c in s:
        if aspas:
            atual += c
            if c == aspas:
                aspas = None
        elif c in "\"'":
            aspas = c; atual += c
        elif c == ",":
            partes.append(atual); atual = ""
        else:
            atual += c
    partes.append(atual)
    return [p for p in (x.strip() for x in partes) if p != ""]


def ler_front_matter(texto):
    """(meta, corpo): o YAML entre `---` no topo do .md e o resto. (None, texto) se o arquivo não começa com `---` ou o
    bloco não fecha. YAML mínimo, o que os .md do repertório usam: `chave: valor` (puro ou entre aspas), lista em linha
    `[a, b]` ou em bloco (`- a`), `|` e `>` com linhas indentadas. Valores saem como texto ou lista de textos."""
    linhas = texto.lstrip("﻿").split("\n")
    if not linhas or linhas[0].strip() != "---":
        return None, texto
    fim = next((i for i in range(1, len(linhas)) if linhas[i].strip() in ("---", "...")), None)
    if fim is None:
        return None, texto
    bloco, meta, k = linhas[1:fim], {}, 0
    while k < len(bloco):
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", bloco[k])
        k += 1
        if not m:
            continue
        chave, valor = m.group(1), m.group(2).strip()
        if valor and valor[0] in "|>":
            partes = []
            while k < len(bloco) and (not bloco[k].strip() or bloco[k][0] in " \t"):
                partes.append(bloco[k].strip()); k += 1
            meta[chave] = ("\n" if valor[0] == "|" else " ").join(partes).strip()
        elif valor == "":
            itens = []
            while k < len(bloco) and (not bloco[k].strip() or re.match(r"^\s*-\s+", bloco[k]) or bloco[k].strip().startswith("#")):
                mi = re.match(r"^\s*-\s+(.*)$", bloco[k])
                if mi:
                    itens.append(_escalar(mi.group(1)))
                k += 1
            meta[chave] = itens if itens else ""
        elif valor.startswith("[") and valor.endswith("]"):
            meta[chave] = [_escalar(x) for x in _dividir_virgulas(valor[1:-1])]
        else:
            meta[chave] = _escalar(valor)
    return meta, "\n".join(linhas[fim + 1:]).lstrip("\n")


def secoes_do_md(corpo):
    """[(título, [linhas])] das seções `## título` (fora de bloco de código). Antes da primeira seção: título ''."""
    out, atual, em_codigo = [("", [])], None, False
    for l in corpo.split("\n"):
        if l.lstrip().startswith("```"):
            em_codigo = not em_codigo
        m = re.match(r"^##\s+(.+?)\s*#*\s*$", l) if not em_codigo else None
        if m:
            out.append((m.group(1), []))
        else:
            out[-1][1].append(l)
    return out


def trecho_de_composicao(corpo):
    """(objeto, erro): o primeiro bloco ```json da seção `## Trecho de composição`. (None, None) quando a seção ou o bloco
    não existem; (None, texto) quando o bloco não é JSON."""
    return _bloco_json_da_secao(corpo, "trecho de composicao")


_INLINE_CODIGO = re.compile(r"(`[^`]+`)")


def _link(m):
    txt, url = m.group(1), _html.unescape(m.group(2))
    if not re.match(r"^(https?://|[A-Za-z0-9._/#-]+$)", url) or url.lower().startswith("javascript:"):
        return m.group(0)
    return f'<a href="{_html.escape(url, quote=True)}">{txt}</a>'


def _inline(t):
    t = _html.escape(t, quote=False)
    out = []
    for pt in _INLINE_CODIGO.split(t):
        if len(pt) > 2 and pt[0] == pt[-1] == "`":
            out.append("<code>" + pt[1:-1] + "</code>")
            continue
        pt = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", pt)
        pt = re.sub(r"(?<![*\w])\*(?![\s*])(.+?)(?<![\s*])\*(?![*\w])", r"<em>\1</em>", pt)
        pt = re.sub(r"(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)", r"<em>\1</em>", pt)
        pt = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", _link, pt)
        out.append(pt)
    return "".join(out)


_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
_SEPARADOR_TABELA = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def _celulas(l):
    l = l.strip()
    if l.startswith("|"):
        l = l[1:]
    if l.endswith("|"):
        l = l[:-1]
    return [c.strip() for c in l.split("|")]


def _lista(itens):
    out, pilha = [], []                     # pilha: (indentação, tag)
    for indent, ordenada, texto in itens:
        tag = "ol" if ordenada else "ul"
        while pilha and indent < pilha[-1][0]:
            out.append(f"</li></{pilha.pop()[1]}>")
        if pilha and indent == pilha[-1][0] and pilha[-1][1] == tag:
            out.append("</li><li>" + _inline(texto))
        elif pilha and indent == pilha[-1][0]:
            out.append(f"</li></{pilha.pop()[1]}><{tag}><li>" + _inline(texto)); pilha.append((indent, tag))
        else:
            out.append(f"<{tag}><li>" + _inline(texto)); pilha.append((indent, tag))
    while pilha:
        out.append(f"</li></{pilha.pop()[1]}>")
    return "".join(out)


def md_para_html(texto, nivel_base=3):
    """Markdown simples (o que os .md do repertório usam) em HTML seguro: tudo é escapado antes de virar tag. Títulos
    `##` viram h{nivel_base}; parágrafos, listas aninhadas por indentação, citação, tabela, bloco de código, régua,
    **negrito**, *itálico*, `código` e [texto](url) (só http, https ou caminho relativo)."""
    linhas, out, i = texto.split("\n"), [], 0
    while i < len(linhas):
        l = linhas[i]
        if not l.strip():
            i += 1; continue
        if l.lstrip().startswith("```"):
            lang = re.sub(r"[^A-Za-z0-9_-]", "", l.strip().strip("`"))
            j = i + 1
            while j < len(linhas) and not linhas[j].lstrip().startswith("```"):
                j += 1
            out.append(f'<pre><code{f" class=language-{lang}" if lang else ""}>' + _html.escape("\n".join(linhas[i + 1:j]), quote=False) + "</code></pre>")
            i = j + 1; continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", l)
        if m:
            n = min(6, nivel_base + len(m.group(1)) - 2) if len(m.group(1)) >= 2 else nivel_base - 1
            out.append(f"<h{n}>{_inline(m.group(2))}</h{n}>"); i += 1; continue
        if re.match(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$", l):
            out.append("<hr>"); i += 1; continue
        if "|" in l and i + 1 < len(linhas) and _SEPARADOR_TABELA.match(linhas[i + 1]) and "|" in linhas[i + 1]:
            cab, j, corpo = _celulas(l), i + 2, []
            while j < len(linhas) and "|" in linhas[j] and linhas[j].strip():
                corpo.append(_celulas(linhas[j])); j += 1
            out.append("<div class=tabela><table><thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in cab) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in corpo) + "</tbody></table></div>")
            i = j; continue
        if l.lstrip().startswith(">"):
            citacao = []
            while i < len(linhas) and linhas[i].lstrip().startswith(">"):
                citacao.append(linhas[i].lstrip()[1:].lstrip()); i += 1
            out.append("<blockquote>" + md_para_html("\n".join(citacao), nivel_base) + "</blockquote>"); continue
        if _ITEM.match(l):
            itens = []
            while i < len(linhas) and linhas[i].strip():
                mi = _ITEM.match(linhas[i])
                if mi:
                    itens.append([len(mi.group(1).replace("\t", "    ")), mi.group(2)[0].isdigit(), mi.group(3)])
                elif itens and linhas[i][:1] in " \t":
                    itens[-1][2] += " " + linhas[i].strip()
                else:
                    break
                i += 1
            out.append(_lista(itens)); continue
        par = [l.strip()]                   # a primeira linha é sempre consumida (`#1 do ranking` e #hashtag não são título)
        i += 1
        while i < len(linhas) and linhas[i].strip() and not linhas[i].lstrip().startswith(("```", ">")) \
                and not re.match(r"^#{1,6}\s", linhas[i]) and not _ITEM.match(linhas[i]):
            par.append(linhas[i].strip()); i += 1
        out.append("<p>" + _inline(" ".join(par)) + "</p>")
    return "\n".join(out)


# ---------------------------------------------------------------- índice e esquema
def sem_exemplos(indice):
    """O índice sem os `composicao_exemplo` (e, no v2, sem os `acabamento_exemplo` dos recursos): a estrutura do índice se
    confere à parte do exemplo, que o checar valida por inteiro."""
    if not isinstance(indice, dict):
        return indice
    out = dict(indice, padroes=[{k: v for k, v in p.items() if k != "composicao_exemplo"} if isinstance(p, dict) else p
                                for p in indice.get("padroes") or []])
    if isinstance(indice.get("recursos"), list):
        out["recursos"] = [{k: v for k, v in r.items() if k != "acabamento_exemplo"} if isinstance(r, dict) else r for r in indice["recursos"]]
    return out


def carregar(rep, estrito=True):
    """O índice. `estrito` recusa (com mensagem, sem traceback) o que não obedece ao schema: buscar, folha e html contam com
    id, nome, etiquetas e arquivos no lugar; o `checar` é quem lista tudo o que está errado."""
    f = Path(rep) / "indice.json"
    if not f.is_file():
        raise SystemExit(f"repertorio: {f} não existe (a estrutura está no topo de pipeline/repertorio.py)")
    try:
        indice = json.loads(f.read_text(encoding="utf-8"))
    except ValueError as e:
        raise SystemExit(f"repertorio: {f} não é JSON válido ({e})")
    if estrito:
        erros = validar_indice(sem_exemplos(indice))
        if erros:
            raise SystemExit(f"repertorio: {f} fora do schema ({len(erros)} erro(s)); rode `repertorio.py checar`. Primeiros: " + "; ".join(erros[:3]))
    return indice


def _registro():
    """Schema do repertório e o registro que resolve o $ref dele para elementos.schema.json (composicao_pagina)."""
    from referencing import Registry, Resource
    el = json.loads(SCHEMA_ELEMENTOS.read_text(encoding="utf-8"))
    sch = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return sch, Registry().with_resources([(el["$id"], Resource.from_contents(el)), (sch["$id"], Resource.from_contents(sch))])


def _mensagem(e):
    """Mensagem do erro. No oneOf da âncora o jsonschema só diz 'não vale em nenhum dos ramos'; aqui vai o erro do ramo que a
    `relacao` declarada escolheu (o ramo cuja constante `relacao` não reprovou), com o campo que falhou."""
    import jsonschema
    if not e.context:
        return e.message
    ramos = {}
    for c in e.context:
        ramos.setdefault(c.relative_schema_path[0], []).append(c)
    certos = [cs for cs in ramos.values() if not any(list(c.relative_schema_path)[-3:] == ["properties", "relacao", "const"] for c in cs)]
    if certos:
        def um(c):
            campo = ".".join(str(x) for x in c.relative_path)
            msg = re.sub(r" does not match '.*'$", " não segue <borda>=<alvo>[.lN].<borda>[±e1..e8|±px]", c.message) if campo in ("x", "y") else c.message
            return f"{campo}: {msg}" if campo else msg
        rel = e.instance.get("relacao") if isinstance(e.instance, dict) else None
        return f"âncora `{rel}`: " + "; ".join(sorted({um(c) for c in certos[0]}))
    if isinstance(e.instance, dict) and "relacao" in e.instance:
        return f"relação `{e.instance['relacao']}` fora do vocabulário (alinha, sangra, sobrepoe, liga)"
    return jsonschema.exceptions.best_match([e]).message


def validar_indice(indice):
    """Erros do índice contra schema/repertorio.schema.json (estrito), incluindo composicao_exemplo contra o
    composicao_pagina do elementos.schema.json. Lista vazia = válido."""
    import jsonschema
    sch, reg = _registro()
    v = jsonschema.Draft7Validator(sch, registry=reg)
    return [f"{'/'.join(str(p) for p in e.absolute_path) or 'indice.json'}: {_mensagem(e)}"
            for e in sorted(v.iter_errors(indice), key=lambda e: [str(p) for p in e.absolute_path])]


def validar_exemplo(exemplo):
    """Erros do trecho de composição: o schema (composicao_pagina) e as regras de composicao.validar (âncora com os dois
    eixos, um deles em conteúdo, escala em degrau). O id do elemento não precisa existir: é exemplo."""
    import composicao, jsonschema
    ids = [e["id"] for e in (exemplo or {}).get("elementos") or [] if isinstance(e, dict) and "id" in e] if isinstance(exemplo, dict) else []
    erros = composicao.validar({"exemplo": exemplo}, ids)
    generico = "is not valid under any of the given schemas"
    if not any(m.endswith(generico) for m in erros):
        return erros
    _, reg = _registro()           # troca a mensagem genérica do oneOf da âncora pela do ramo que a relação escolheu
    v = jsonschema.Draft7Validator({"$ref": "mk-elementos-1.0#/definitions/composicao_pagina"}, registry=reg)
    melhor = {"composicao/exemplo/" + "/".join(str(x) for x in e.absolute_path): _mensagem(e) for e in v.iter_errors(exemplo) if e.context}
    out = []
    for m in erros:
        onde, _, msg = m.partition(": ")
        out.append(f"{onde}: {melhor[onde]}" if msg.endswith(generico) and onde in melhor else m)
    return out


# ---------------------------------------------------------------- buscar
def _lista_de(valores):
    """['a,b', 'c'] -> ['a', 'b', 'c'] (valor repetido ou separado por vírgula)."""
    return [v.strip() for x in (valores or []) for v in str(x).split(",") if v.strip()]


def _paginas_pedidas(pagina):
    p = norm(pagina).split(":")[0].replace(" ", "_")
    return ALIAS_PAGINA.get(p, (p,)) if p else ()


def buscar(indice, pagina=None, problema=None, funcoes=(), relacoes=(), rota=None, tons=(), n=5, dimensoes=()):
    """Padrões do índice ranqueados: nota decrescente, empate pelo id. Cada resultado traz a nota e as razões. Havendo
    algum critério, padrão sem nenhum casamento fica de fora. Determinístico (nada de acaso nem ordem de conjunto).
    `dimensoes` (v2): +2 por dimensão do estudo v2 que o padrão declara em `dimensoes`; vazio, nada muda."""
    pedidas, funcoes, relacoes, tons = _paginas_pedidas(pagina), [norm(x) for x in funcoes], [norm(x) for x in relacoes], [norm(x) for x in tons]
    dimensoes = [norm(x) for x in dimensoes]
    rota = norm(rota) if rota else None
    palavras = sorted(_radicais(problema)) if problema else []
    criterio = bool(pedidas or funcoes or relacoes or tons or rota or palavras or dimensoes)
    out = []
    for p in indice.get("padroes", []):
        nota, razoes = 0, []
        if pedidas and any(t in p.get("tipo_pagina", []) for t in pedidas):
            nota += 3; razoes.append(f"página {norm(pagina).split(':')[0]}")
        for tag, pedido, peso in (("função", funcoes, 2), ("relação", relacoes, 2), ("tom", tons, 1)):
            campo = {"função": "funcao", "relação": "relacao", "tom": "tom"}[tag]
            for v in pedido:
                if v in p.get(campo, []):
                    nota += peso; razoes.append(f"{tag} {v}")
        for v in dimensoes:
            if v in p.get("dimensoes", []):
                nota += 2; razoes.append(f"dimensão {v}")
        if rota and p.get("rota") == rota:
            nota += 1; razoes.append(f"rota {rota}")
        if palavras:
            rp, rn = _radicais(p.get("problema", "")), _radicais(p.get("nome", ""))
            no_problema = [w for w in palavras if w in rp]
            no_nome = [w for w in palavras if w in rn]
            if no_problema:
                nota += len(no_problema); razoes.append("palavras no problema: " + ", ".join(no_problema))
            if no_nome:
                nota += len(no_nome); razoes.append("palavras no nome: " + ", ".join(no_nome))
        if criterio and nota == 0:
            continue
        out.append({"nota": nota, "razoes": razoes or ["sem critério"], "padrao": p})
    out.sort(key=lambda r: (-r["nota"], r["padrao"]["id"]))
    out = out[:n] if n else out
    for k, r in enumerate(out, 1):
        r["n"] = k
    return out


# ---------------------------------------------------------------- folha
def _quebrar(texto, fonte, largura, max_linhas):
    linhas, atual = [], ""
    for w in str(texto).split():
        teste = (atual + " " + w).strip()
        if fonte.getlength(teste) <= largura:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = w
    if atual:
        linhas.append(atual)
    if len(linhas) > max_linhas:
        linhas = linhas[:max_linhas]
        ultima = linhas[-1]
        while ultima and fonte.getlength(ultima + "...") > largura:
            ultima = ultima[:-1]
        linhas[-1] = ultima.rstrip() + "..."
    return linhas


def folha_de_cartoes(cartoes, saida, titulo, colunas=3, largura=520, altura_img=340):
    """cartoes: [{imagem: Path|None, id, legenda, rodape, anti}] numa grade de uma imagem só (para uma leitura). O
    antiexemplo leva borda vermelha e o rótulo NÃO FAZER; cartão sem arquivo mostra SEM RECORTE."""
    from PIL import Image, ImageDraw
    from regua import fonte_ui
    f_t, f_id, f_tx = fonte_ui(22), fonte_ui(17), fonte_ui(15)
    colunas = max(1, min(colunas, len(cartoes)))
    linhas_grade = -(-len(cartoes) // colunas)
    m, legenda_h = 14, 118
    W = colunas * (largura + m) + m
    H = 56 + linhas_grade * (altura_img + legenda_h + m) + m
    F = Image.new("RGB", (W, H), (18, 18, 20)); d = ImageDraw.Draw(F)
    d.text((m, 16), titulo, fill=(240, 240, 240), font=f_t)
    for i, c in enumerate(cartoes):
        x = m + (i % colunas) * (largura + m); y = 56 + (i // colunas) * (altura_img + legenda_h + m)
        d.rectangle([x, y, x + largura - 1, y + altura_img - 1], fill=(34, 34, 38))
        if c.get("imagem") and Path(c["imagem"]).is_file():
            im = Image.open(c["imagem"]).convert("RGB"); im.thumbnail((largura, altura_img), Image.LANCZOS)
            F.paste(im, (x + (largura - im.width) // 2, y + (altura_img - im.height) // 2))
        else:
            d.text((x + 16, y + altura_img // 2 - 10), "SEM RECORTE", fill=(240, 120, 120), font=f_id)
        if c.get("anti"):
            d.rectangle([x, y, x + largura - 1, y + altura_img - 1], outline=(214, 48, 49), width=5)
            d.rectangle([x, y, x + 132, y + 26], fill=(214, 48, 49))
            d.text((x + 8, y + 4), "NÃO FAZER", fill=(255, 255, 255), font=f_tx)
        yy = y + altura_img + 8
        d.text((x, yy), str(c["id"])[:60], fill=(255, 255, 255), font=f_id)
        for j, t in enumerate(_quebrar(c.get("legenda") or "", f_tx, largura, 3)):
            d.text((x, yy + 26 + j * 20), t, fill=(205, 205, 205), font=f_tx)
        if c.get("rodape"):
            d.text((x, yy + 26 + 3 * 20 + 2), str(c["rodape"])[:70], fill=(140, 140, 150), font=f_tx)
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    F.save(saida, optimize=True, quality=88)          # quality só vale para .jpg; o png ignora
    return Path(saida), (W, H)


def folha(rep, ids, saida):
    """Os recortes dos padrões `ids` (na ordem dada; recorte normal antes do antiexemplo) numa folha só."""
    rep = Path(rep); indice = carregar(rep)
    por_id = {p["id"]: p for p in indice.get("padroes", [])}
    faltam = [i for i in ids if i not in por_id]
    if faltam:
        raise SystemExit(f"repertorio: padrão(ões) fora do índice: {', '.join(faltam)} (repertorio.py buscar mostra os ids)")
    cartoes = []
    for i in ids:
        p = por_id[i]
        rs = sorted(p.get("recortes") or [], key=lambda r: bool(r.get("anti")))
        if not rs:
            cartoes.append({"imagem": None, "id": i, "legenda": p.get("nome", ""), "rodape": "padrão sem recorte", "anti": False})
        for r in rs:
            cartoes.append({"imagem": rep / r["arquivo"], "id": i, "legenda": r.get("legenda", ""),
                            "rodape": f"{r.get('referencia', '?')} p.{r.get('pagina', '?')}", "anti": bool(r.get("anti"))})
    return folha_de_cartoes(cartoes, saida, "repertório: " + " · ".join(ids))


# ---------------------------------------------------------------- checar
def checar(rep):
    """Lista de (nível, mensagem), nível FALHA ou AVISO."""
    rep = Path(rep); res = []
    F = lambda m: res.append(("FALHA", m)); A = lambda m: res.append(("AVISO", m))  # noqa: E731
    f_ind = rep / "indice.json"
    if not f_ind.is_file():
        return [("FALHA", f"{f_ind} não existe")]
    try:
        indice = json.loads(f_ind.read_text(encoding="utf-8"))
    except ValueError as e:
        return [("FALHA", f"indice.json não é JSON válido ({e})")]
    if not isinstance(indice, dict):
        return [("FALHA", "indice.json: a raiz tem de ser um objeto")]
    # o exemplo de composição é conferido por inteiro mais abaixo (schema e regras); aqui o resto do índice
    for e in validar_indice(sem_exemplos(indice)):
        F(f"indice.json/{e}")
    padroes = [p for p in indice.get("padroes") or [] if isinstance(p, dict)]
    refs = [r for r in indice.get("referencias") or [] if isinstance(r, dict)]
    ids_ref = {r.get("id") for r in refs}
    for nome, itens in (("padrão", padroes), ("referência", refs)):
        vistos = set()
        for it in itens:
            if it.get("id") in vistos:
                F(f"{nome} `{it.get('id')}` repetido no índice (os ids têm de ser únicos)")
            vistos.add(it.get("id"))
    usados = set()
    for r in refs:
        if r.get("arquivo") and not (rep / r["arquivo"]).is_file():
            F(f"referência `{r.get('id')}`: `{r['arquivo']}` não existe")
    for p in padroes:
        pid = p.get("id", "?")
        arq = p.get("arquivo")
        if not p.get("recortes"):
            A(f"padrão `{pid}` sem recorte (a folha e o html ficam sem imagem)")
        for r in p.get("recortes") or []:
            if not isinstance(r, dict):
                continue
            usados.add(r.get("arquivo"))
            if r.get("arquivo") and not (rep / r["arquivo"]).is_file():
                F(f"padrão `{pid}`: recorte `{r['arquivo']}` não existe")
            if r.get("referencia") not in ids_ref:
                F(f"padrão `{pid}`: o recorte `{r.get('arquivo')}` cita a referência `{r.get('referencia')}`, que não está em referencias[]")
        if not arq:
            continue
        if Path(arq).stem != pid:
            F(f"padrão `{pid}`: o arquivo `{arq}` deveria se chamar `{pid}.md`")
        if not (rep / arq).is_file():
            F(f"padrão `{pid}`: `{arq}` não existe"); continue
        texto = (rep / arq).read_text(encoding="utf-8")
        meta, corpo = ler_front_matter(texto)
        if meta is None:
            F(f"padrão `{pid}`: `{arq}` sem front matter (bloco YAML entre `---` no topo, com id, nome, problema, tipo_pagina, ...)")
            corpo = texto
        else:
            if meta.get("id") != pid or meta.get("id") != Path(arq).stem:
                F(f"padrão `{pid}`: o front matter de `{arq}` diz id `{meta.get('id')}`; o id tem de ser igual ao do índice (`{pid}`) e ao nome do arquivo (`{Path(arq).stem}`)")
            for campo in ("nome", "problema", "rota", "densidade", "tipo_pagina", "funcao", "relacao", "tom"):
                if campo in meta and campo in p:
                    a, b = meta[campo], p[campo]
                    if isinstance(b, list) and isinstance(a, str):
                        a = [x.strip() for x in a.split(",") if x.strip()]        # `tom: performance` ou `tom: festa, causa`
                    igual = (sorted(map(norm, a)) == sorted(map(norm, b))) if isinstance(b, list) and isinstance(a, list) else norm(a) == norm(b)
                    if not igual:
                        A(f"padrão `{pid}`: `{campo}` do front matter ({a}) é diferente do índice ({b})")
        titulos = [t for t, _ in secoes_do_md(corpo)]
        for k, esperado in enumerate(SECOES, 1):
            achou = next((t for t in titulos if re.match(rf"^{k}\.\s", t)), None)
            if achou is None:
                A(f"padrão `{pid}`: falta a seção `## {k}. {esperado}`")
            elif not norm(re.sub(r"^\d+\.\s*", "", achou)).startswith(norm(esperado)):
                A(f"padrão `{pid}`: a seção {k} devia ser `{esperado}`, está `{achou}`")
        obj, erro = trecho_de_composicao(corpo)
        ex = p.get("composicao_exemplo")
        if erro:
            F(f"padrão `{pid}`: trecho de composição do .md: {erro}")
        elif obj is None and ex is not None:
            F(f"padrão `{pid}`: o índice tem `composicao_exemplo` e o .md não tem a seção `## Trecho de composição` com bloco ```json (o .md é a fonte)")
        elif obj is not None and ex is None:
            F(f"padrão `{pid}`: o .md tem trecho de composição e o índice não tem `composicao_exemplo` (o índice repete o mesmo objeto)")
        elif obj is not None and obj != ex:
            F(f"padrão `{pid}`: o trecho de composição do .md e o `composicao_exemplo` do índice são diferentes (o .md é a fonte; copie dele para o índice)")
        fonte = obj if obj is not None else ex
        if fonte is not None:
            for e in validar_exemplo(fonte):
                F(f"padrão `{pid}`: trecho de composição inválido: {e}")
    checar_v2(rep, indice, F, A, usados, ids_ref, padroes, refs)
    pasta = rep / "recortes"
    if pasta.is_dir():
        for f in sorted(pasta.iterdir()):
            if f.is_file() and not f.name.startswith(("_", ".")) and f"recortes/{f.name}" not in usados:
                A(f"recorte órfão: `recortes/{f.name}` não está em nenhum padrão do índice")
    return res


# ---------------------------------------------------------------- recortar
def _resolver_imagem(imagem, bases):
    for b in bases:
        c = Path(b) / imagem
        if c.is_file():
            return c
    return None


ID_SEGURO = re.compile(r"[a-z0-9][a-z0-9-]*")      # o padrão dos ids do índice (schema/repertorio.schema.json)


def recortar(analise, saida, bases=None):
    """Recortes de uma análise (formato da RUBRICA: padroes[].exemplos[] com imagem, pagina, recorte em fração
    [x0, y0, x1, y1]). Devolve {"feitos": [...], "problemas": [...], "conferencia": caminho}. Cada recorte sai em JPEG
    (lado maior até LADO_MAX px, qualidade QUALIDADE, folga FOLGA de cada lado) como <id_sugerido>__<ref>-<pp>.jpg."""
    from PIL import Image
    analise = Path(analise)
    d = json.loads(analise.read_text(encoding="utf-8"))
    ref = d.get("referencia") or analise.stem
    if not ID_SEGURO.fullmatch(str(ref)):
        raise SystemExit(f"referência `{ref}` fora do padrão a-z, 0-9 e hífen: vira nome de arquivo e não pode sair de --saida")
    saida = Path(saida); saida.mkdir(parents=True, exist_ok=True)
    bases = [Path(b) for b in (bases or [])] or [Path.cwd(), analise.parent, analise.parent.parent, AQUI.parent]
    feitos, problemas, nomes = [], [], set()
    for p in d.get("padroes") or []:
        pid = p.get("id_sugerido") or "sem-id"
        if not ID_SEGURO.fullmatch(str(pid)):
            problemas.append(f"id_sugerido `{pid}` fora do padrão a-z, 0-9 e hífen (vira nome de arquivo): padrão pulado"); continue
        for ex in p.get("exemplos") or []:
            onde = f"{pid} ({ex.get('imagem')})"
            box = ex.get("recorte")
            if not (isinstance(box, (list, tuple)) and len(box) == 4 and all(isinstance(v, (int, float)) for v in box)
                    and -0.01 <= box[0] < box[2] <= 1.01 and -0.01 <= box[1] < box[3] <= 1.01):
                problemas.append(f"{onde}: recorte inválido {box} (esperado [x0, y0, x1, y1] em fração, com x0 < x1 e y0 < y1)"); continue
            arq = _resolver_imagem(ex.get("imagem") or "", bases)
            if arq is None:
                problemas.append(f"{onde}: imagem não encontrada em {', '.join(str(b) for b in bases)} (use --base-imagens)"); continue
            im = Image.open(arq).convert("RGB"); W, H = im.size
            x0, y0 = max(0.0, box[0] - FOLGA), max(0.0, box[1] - FOLGA)
            x1, y1 = min(1.0, box[2] + FOLGA), min(1.0, box[3] + FOLGA)
            corte = im.crop((round(x0 * W), round(y0 * H), round(x1 * W), round(y1 * H)))
            if max(corte.size) > LADO_MAX:
                f = LADO_MAX / max(corte.size)
                corte = corte.resize((max(1, round(corte.width * f)), max(1, round(corte.height * f))), Image.LANCZOS)
            pag = ex.get("pagina")
            base = f"{pid}__{ref}-{pag:02d}" if isinstance(pag, int) else f"{pid}__{ref}-{re.sub(r'[^a-z0-9]+', '', norm(pag)) or 'x'}"
            nome, k = f"{base}.jpg", 2
            while nome in nomes:
                nome = f"{base}-{chr(96 + k)}.jpg"; k += 1       # segunda do mesmo padrão e página: -b, -c
            nomes.add(nome)
            corte.save(saida / nome, "JPEG", quality=QUALIDADE, optimize=True)
            feitos.append({"padrao": pid, "arquivo": f"recortes/{nome}", "referencia": ref, "pagina": pag,
                           "legenda": ex.get("o_que_mostra") or "", "tamanho": list(corte.size), "caminho": str(saida / nome)})
    conf = None
    if feitos:
        cartoes = [{"imagem": f["caminho"], "id": f["padrao"], "legenda": f["legenda"], "rodape": f"{ref} p.{f['pagina']}", "anti": False} for f in feitos]
        conf, _ = folha_de_cartoes(cartoes, saida / f"_conferencia-{ref}.jpg", f"conferência dos recortes: {ref} ({len(feitos)})")
    return {"referencia": ref, "feitos": feitos, "problemas": problemas, "conferencia": str(conf) if conf else None}


# ---------------------------------------------------------------- html
CSS = """
:root{color-scheme:light dark;--fundo:#f6f5f1;--cartao:#fff;--texto:#1d1d1f;--suave:#5c5c63;--linha:#dcdad2;--marca:#8a5a00;--chip:#ece9de;--anti:#c0392b}
@media (prefers-color-scheme:dark){:root{--fundo:#161618;--cartao:#1f1f23;--texto:#ececee;--suave:#a0a0a8;--linha:#34343a;--marca:#e0b04a;--chip:#2b2b31;--anti:#ff6b5b}}
*{box-sizing:border-box}
body{margin:0;background:var(--fundo);color:var(--texto);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
header.topo{background:var(--fundo);border-bottom:1px solid var(--linha);padding:10px 16px}
@media (min-width:900px){header.topo{position:sticky;top:0;z-index:5}}
header.topo h1{margin:0 0 6px;font-size:1.15rem}
header.topo p{margin:0 0 8px;color:var(--suave);font-size:.9rem}
input[type=search]{width:100%;max-width:520px;padding:10px 12px;border:1px solid var(--linha);border-radius:8px;background:var(--cartao);color:var(--texto);font:inherit}
main{max-width:1120px;margin:0 auto;padding:16px}
nav.indice{background:var(--cartao);border:1px solid var(--linha);border-radius:10px;padding:4px 14px;margin-bottom:20px}
nav.indice summary{cursor:pointer;font-weight:600;padding:10px 0}
nav.indice details.tipo{margin:0 0 4px}nav.indice details.tipo summary{font-weight:500;padding:5px 0}
nav.indice ul{margin:0 0 12px;padding-left:18px}nav.indice li{margin:3px 0}
a{color:var(--marca);overflow-wrap:anywhere}
article.padrao{background:var(--cartao);border:1px solid var(--linha);border-radius:12px;padding:18px;margin:0 0 22px}
article.padrao h2{margin:0;font-size:1.3rem;line-height:1.25}
article.padrao h2 small{display:block;font-weight:400;color:var(--suave);font-size:.8rem;margin-top:2px}
.problema{margin:10px 0 8px;font-size:1.02rem}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px;padding:0;list-style:none}
.chips li{background:var(--chip);border-radius:999px;padding:2px 10px;font-size:.78rem;color:var(--suave)}
.galeria{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:12px;margin:0 0 14px}
figure{margin:0}figure img{display:block;width:100%;height:auto;border-radius:8px;border:1px solid var(--linha);background:#000}
figcaption{font-size:.82rem;color:var(--suave);margin-top:4px}
.naofazer h3{color:var(--anti);margin:8px 0}.naofazer figure img{border:3px solid var(--anti)}
.texto h3{margin:20px 0 6px;font-size:1.02rem}.texto h4{margin:14px 0 4px;font-size:.95rem}
.texto p,.texto li{max-width:78ch}
pre{overflow-x:auto;background:var(--chip);padding:12px;border-radius:8px;font-size:.82rem;line-height:1.45}
code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.88em}
p code,li code,td code{background:var(--chip);padding:1px 5px;border-radius:4px}
.tabela{overflow-x:auto}table{border-collapse:collapse;font-size:.88rem}th,td{border:1px solid var(--linha);padding:5px 9px;text-align:left;vertical-align:top}
blockquote{margin:8px 0;padding:2px 14px;border-left:3px solid var(--linha);color:var(--suave)}
details.ref{border-top:1px solid var(--linha);padding:8px 0}details.ref summary{cursor:pointer}
.vazio{color:var(--suave)}[hidden]{display:none!important}
@media (max-width:640px){main{padding:10px}article.padrao{padding:14px;border-radius:10px}header.topo{padding:8px 12px}}
"""

JS = """
(function(){var q=document.getElementById('filtro'),n=document.getElementById('contagem');
if(!q)return;var cards=[].slice.call(document.querySelectorAll('article.padrao')),itens=[].slice.call(document.querySelectorAll('[data-padrao]'));
function norm(s){return s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase()}
q.addEventListener('input',function(){var t=norm(q.value).split(/\\s+/).filter(Boolean),vis=0;
cards.forEach(function(c){var ok=t.every(function(w){return c.getAttribute('data-busca').indexOf(w)>=0});c.hidden=!ok;if(ok)vis++});
itens.forEach(function(i){var c=document.getElementById('padrao-'+i.getAttribute('data-padrao'));i.hidden=!!(c&&c.hidden)});
n.textContent=vis+' de '+cards.length+' padrões'})})();
"""


def _rel(rep, arquivo, saida):
    """Caminho do recorte relativo à pasta do html (os dois resolvidos: /var e /private/var são o mesmo lugar no macOS)."""
    return quote(os.path.relpath((Path(rep) / arquivo).resolve(), Path(saida).resolve().parent).replace(os.sep, "/"), safe="/")


def _figura(rep, r, saida):
    caminho = Path(rep) / r["arquivo"]
    legenda = f"{_html.escape(r.get('legenda', ''), quote=False)} <span class=vazio>({_html.escape(str(r.get('referencia', '?')))}, p. {r.get('pagina', '?')})</span>"
    if not caminho.is_file():
        return f'<figure><p class=vazio>recorte ausente: {_html.escape(r["arquivo"])}</p><figcaption>{legenda}</figcaption></figure>'
    src = _rel(rep, r["arquivo"], saida)
    return (f'<figure><a href="{src}" target=_blank rel=noopener><img src="{src}" alt="{_html.escape(r.get("legenda", ""), quote=True)}" loading=lazy></a>'
            f"<figcaption>{legenda}</figcaption></figure>")


def pagina_html(rep, saida):
    """O HTML estático do repertório (string). Caminhos relativos ao arquivo de saída; nada de rede."""
    rep = Path(rep); indice = carregar(rep)
    padroes = sorted(indice.get("padroes") or [], key=lambda p: p["id"])
    esc = lambda s: _html.escape(str(s), quote=False)  # noqa: E731
    eid = lambda s: _html.escape(str(s), quote=True)   # noqa: E731
    tipos = [t for t in vocabularios()[2] if any(t in p.get("tipo_pagina", []) for p in padroes)]
    por_tipo = "".join(
        f"<details class=tipo><summary>{esc(t)} ({sum(t in p.get('tipo_pagina', []) for p in padroes)})</summary><ul>"
        + "".join(f'<li data-padrao="{eid(p["id"])}"><a href="#padrao-{eid(p["id"])}">{esc(p["nome"])}</a></li>' for p in padroes if t in p.get("tipo_pagina", []))
        + "</ul></details>" for t in tipos)
    por_problema = "".join(f'<li data-padrao="{eid(p["id"])}"><a href="#padrao-{eid(p["id"])}">{esc(p.get("problema", p["nome"]))}</a></li>'
                           for p in sorted(padroes, key=lambda p: norm(p.get("problema", p["nome"]))))
    cartoes = []
    for p in padroes:
        arq = rep / p["arquivo"]
        corpo = ""
        if arq.is_file():
            _, corpo = ler_front_matter(arq.read_text(encoding="utf-8"))
            corpo = re.sub(r"\A\s*#[ \t][^\n]*\n", "", corpo)      # o título do .md repete o nome do cartão
        etiquetas = [e for e in (*p.get("tipo_pagina", []), *p.get("funcao", []), *p.get("relacao", []), p.get("rota"), *p.get("tom", []), p.get("densidade")) if e]
        chips = "".join(f"<li>{esc(e)}</li>" for e in etiquetas)
        normais = [r for r in p.get("recortes") or [] if not r.get("anti")]
        antis = [r for r in p.get("recortes") or [] if r.get("anti")]
        galeria = f'<div class=galeria>{"".join(_figura(rep, r, saida) for r in normais)}</div>' if normais else ""
        nao_fazer = (f'<section class=naofazer><h3>Não fazer</h3><div class=galeria>{"".join(_figura(rep, r, saida) for r in antis)}</div></section>'
                     if antis else "")
        texto = md_para_html(corpo) if corpo.strip() else '<p class=vazio>(o .md deste padrão está vazio ou não existe)</p>'
        if p.get("composicao_exemplo") and not any(norm(t).startswith("trecho de composicao") for t, _ in secoes_do_md(corpo)):
            texto += "<h3>Trecho de composição</h3><pre><code>" + _html.escape(json.dumps(p["composicao_exemplo"], ensure_ascii=False, indent=2), quote=False) + "</code></pre>"
        busca = norm(" ".join([p["id"], p["nome"], p.get("problema", ""), *etiquetas]))
        cartoes.append(f'<article class=padrao id="padrao-{eid(p["id"])}" data-busca="{eid(busca)}">'
                       f'<h2>{esc(p["nome"])}<small>{esc(p["id"])}</small></h2><p class=problema>{esc(p.get("problema", ""))}</p>'
                       f'<ul class=chips>{chips}</ul>{galeria}{nao_fazer}<div class=texto>{texto}</div></article>')
    refs = []
    for r in sorted(indice.get("referencias") or [], key=lambda r: r["id"]):
        arq = rep / r["arquivo"]
        corpo = ler_front_matter(arq.read_text(encoding="utf-8"))[1] if arq.is_file() else ""
        link = f' <a href="{_html.escape(r["url"], quote=True)}" rel="noopener">{esc(r["url"])}</a>' if r.get("url") and re.match(r"^https?://", r["url"]) else ""
        refs.append(f'<details class=ref id="ref-{eid(r["id"])}"><summary><strong>{esc(r["nome"])}</strong> <span class=vazio>{esc(r["id"])}</span>{link}</summary>'
                    f'{md_para_html(corpo) if corpo.strip() else ""}</details>')
    n_rec = len(indice.get("recursos") or [])
    n_ser = sum(1 for r in indice.get("referencias") or [] if r.get("serie"))
    titulo = "Repertório de composição e acabamento" if n_rec else "Repertório de composição"
    abas = (f'<nav class=abas role=tablist aria-label="Partes do repertório"><button type=button role=tab data-aba=padroes aria-selected=true>Padrões ({len(padroes)})</button>'
            f'<button type=button role=tab data-aba=recursos aria-selected=false>Recursos ({n_rec})</button>'
            f'<button type=button role=tab data-aba=series aria-selected=false>Séries ({n_ser})</button></nav>')
    return ("<!doctype html>\n<html lang=pt-BR><head><meta charset=utf-8><meta name=viewport content=\"width=device-width, initial-scale=1\">"
            f"<title>{titulo}</title><style>{CSS}{CSS_V2}</style></head><body>"
            f'<header class=topo><h1>{titulo}</h1><p><span id=contagem>{len(padroes)} de {len(padroes)} padrões</span> · {n_rec} recursos · {len(indice.get("referencias") or [])} referências</p>'
            '<input id=filtro type=search placeholder="Filtrar por nome, problema, efeito ou etiqueta" aria-label="Filtrar padrões e recursos" autocomplete=off></header>'
            f"<main>{abas}<section id=aba-padroes><nav class=indice><details open><summary>Por tipo de página</summary>{por_tipo}</details>"
            f"<details><summary>Por problema</summary><ul>{por_problema}</ul></details></nav>"
            f'{"".join(cartoes) or "<p class=vazio>Nenhum padrão no índice.</p>"}</section>'
            f"<section id=aba-recursos>{_aba_recursos(rep, indice, saida, esc, eid)}</section>"
            f"<section id=aba-series>{_aba_series(indice, esc, eid)}</section>"
            f'<section id=referencias><h2>Referências</h2>{"".join(refs) or "<p class=vazio>Nenhuma referência.</p>"}</section></main>'
            f"<script>{JS}{JS_V2}</script></body></html>\n")


def gerar_html(rep, saida):
    saida = Path(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(pagina_html(rep, saida), encoding="utf-8")
    return saida


# ---------------------------------------------------------------- usados
def usados(pasta, rep=None):
    """Padrões declarados em composicao[*].padroes do mediakit.json do kit: {id: [chaves de página]}; `desconhecidos` =
    ids que não estão no índice do repertório (quando ele existe). v2: `recursos` = {id: [chaves de página]} dos recursos
    de direcao_criativa.recursos (sem página: lista vazia), de composicao[*].acabamento.recursos e do `recurso` dos
    elementos da página; `recursos_desconhecidos` = os que não estão em recursos[] do índice."""
    f = Path(pasta) / "mediakit.json"
    if not f.is_file():
        raise SystemExit(f"repertorio: {f} não existe (passe a pasta do kit)")
    try:
        k = json.loads(f.read_text(encoding="utf-8"))
    except ValueError as e:
        raise SystemExit(f"repertorio: {f} não é JSON válido ({e})")
    por_padrao = {}
    for chave, ent in (k.get("composicao") or {}).items():
        if str(chave).startswith("_") or not isinstance(ent, dict):
            continue
        for pid in ent.get("padroes") or []:
            por_padrao.setdefault(pid, [])
            if chave not in por_padrao[pid]:
                por_padrao[pid].append(chave)
    dc = k.get("direcao_criativa") if isinstance(k.get("direcao_criativa"), dict) else {}
    por_recurso = {r["id"]: [] for r in dc.get("recursos") or [] if isinstance(r, dict) and isinstance(r.get("id"), str)}
    for chave, ent in (k.get("composicao") or {}).items():
        if str(chave).startswith("_") or not isinstance(ent, dict):
            continue
        ac = ent.get("acabamento") if isinstance(ent.get("acabamento"), dict) else {}
        rids = [x for x in ac.get("recursos") or [] if isinstance(x, str)]
        rids += [e["recurso"] for e in ent.get("elementos") or [] if isinstance(e, dict) and isinstance(e.get("recurso"), str)]
        for rid in rids:
            por_recurso.setdefault(rid, [])
            if chave not in por_recurso[rid]:
                por_recurso[rid].append(chave)
    conhecidos = conhecidos_r = None
    if rep and (Path(rep) / "indice.json").is_file():
        ind = carregar(rep, estrito=False)
        conhecidos = {p.get("id") for p in ind.get("padroes", [])}
        conhecidos_r = {r.get("id") for r in ind.get("recursos") or [] if isinstance(r, dict)}
    out = {"kit": k.get("kit"), "padroes": {i: por_padrao[i] for i in sorted(por_padrao)},
           "desconhecidos": sorted(i for i in por_padrao if conhecidos is not None and i not in conhecidos)}
    out["recursos"] = {i: por_recurso[i] for i in sorted(por_recurso)}
    out["recursos_desconhecidos"] = sorted(i for i in por_recurso if conhecidos_r is not None and i not in conhecidos_r)
    return out


# ---------------------------------------------------------------- captura das galerias
# Traz para repertorio/capturas/<ref>/ todas as páginas de cada referência e deixa um manifesto rastreado em
# repertorio/fontes/<ref>.json. Roda no Playwright com a mesma identificação do regua.py (regua.UA). Não usa modo furtivo, proxy
# nem login e não resolve CAPTCHA: se o site barrar, a captura para e o status de cada referência diz o que aconteceu.
CAMADAS = ("prioritaria", "profunda", "releitura", "lente", "regua", "fora")
TIPOS_FONTE = ("behance", "web", "pdf", "regua")
LARGURA_PADRAO = 1400
MIN_LARGURA = 900                       # descarta largura menor (miniatura, logo, ícone)
MIN_ALTURA_REL = 0.2                    # descarta altura menor que isto vezes a largura (faixa fina)
ALTO_REL = 1.9                          # módulo mais alto que isto vezes a largura é fatiado
FAIXA_MIN_PX = 8                        # altura mínima da faixa de cor uniforme entre slides
FAIXA_DESVIO = 2.0                      # linha é "uniforme" quando o desvio padrão dela é menor que isto
FAIXA_DERIVA = 8.0                      # e a cor da faixa não pode variar mais que isto de uma linha à outra
SOBREPOSICAO = 0.04                     # do corte em 16:9, quando não há faixa
MINI_LARGURA = 800
FOLHA_COLUNAS, FOLHA_MINI, FOLHA_ALTURA_REL, FOLHA_NUMERO, FOLHA_POR_FOLHA = 5, 420, 1.6, 28, 20
SUSPEITA_MIN_PAGINAS, SUSPEITA_LARGURA = 3, 1000
DISCO_MIN_GB = 1.8                      # recusa começar (e continuar) com menos que isto livre
CAPTURAS_MAX_MB = 900                   # para quando capturas/ passa disto
TENTATIVAS, ESPERA_RETRY, BLOQUEIOS_SEGUIDOS = 2, 30, 3
ROLAGENS, ROLAGEM_PX, ROLAGEM_MS, ESPERA_INICIAL_MS = 60, 1400, 250, 2500
NOTA_MIN = 0.8                          # conferir-captura: abaixo disto o recorte não está nesta página
TRABALHO_LARGURA = 480                  # a página e o recorte são reduzidos a isto antes do matchTemplate
SAIDA_BLOQUEIO, SAIDA_DISCO = 3, 4
MODULO = re.compile(r"https?://mir-s3-cdn-cf\.behance\.net/project_modules/[A-Za-z0-9_]+/[A-Za-z0-9_.-]+\.(?:jpg|jpeg|png|gif|webp)", re.I)
SINAIS_BLOQUEIO = ("captcha", "verify you are human", "verifique que voce e humano", "are you a robot", "access denied", "just a moment",
                   "unusual traffic", "attention required", "checking your browser", "security check", "please verify")
JS_DOM = """()=>[...document.querySelectorAll('img,source')].flatMap(e=>[e.currentSrc,e.src,
    ...(e.srcset||'').split(',').map(s=>s.trim().split(' ')[0])]).filter(Boolean)"""
JS_CANONICA = "()=>{const l=document.querySelector('link[rel=canonical]');return l?l.href:null}"
JS_TEXTO = "()=>document.body?document.body.innerText.slice(0,3000):''"
# Páginas web (artigo, site): o coletor da régua só guarda imagem com naturalWidth >= 1000 e muitos sites entregam no <img> a variante
# pequena (852 px) e a grande só no srcset. Aqui se acrescenta a MAIOR URL do srcset das imagens do conteúdo (article, main, figure).
# Só do conteúdo: fora dele ficam as miniaturas de matérias relacionadas, que o v1 também pegou e atrapalhou.
SELETOR_CONTEUDO = "article img, article source, main img, main source, figure img, figure source"
# E, dentro disso, nada de bloco lateral, relacionados, recomendados, listagem de outras matérias, teaser, carrossel ou rodapé: na Dezeen as miniaturas das matérias
# relacionadas ficam dentro do próprio <article> e <main>, em <figure>.
EXCLUIR_DO_CONTEUDO = ('aside, nav, footer, [class*="related" i], [class*="recommend" i], [class*="carousel" i], [class*="sidebar" i], '
                       '[class*="side-article" i], [class*="newsletter" i], [class*="listing" i], [class*="teaser" i], [id*="related" i], [id*="recommended" i]')
JS_SRCSET = """([sel, excl])=>{
  const abs=(u)=>{try{return new URL(u,document.baseURI).href}catch(e){return null}};
  const maior=(s)=>{if(!s)return null;let m=null,mw=-1;for(const p of s.split(/,\\s+/)){const t=p.trim().split(/\\s+/);const n=parseFloat(t[1])||0;if(t[0]&&n>=mw){mw=n;m=t[0]}}return m};
  return [...document.querySelectorAll(sel)].filter(e=>!e.closest(excl)).map(e=>abs(maior(e.getAttribute('srcset')||e.getAttribute('data-srcset'))||e.currentSrc||e.getAttribute('src')||e.getAttribute('data-src')))
    .filter(u=>u&&!u.startsWith('data:'))}"""


class ErroCaptura(Exception):
    """Falha de uma referência (arquivo que não é nosso, PDF que não baixa): a captura segue para a próxima."""


class LimiteAtingido(Exception):
    """Pouco disco ou capturas/ grande demais: a captura inteira para (código 4)."""


def carregar_fontes(rep):
    """A lista `fontes` de fontes.json, validada (ids únicos e seguros, tipo e camada do vocabulário, url nas que capturam)."""
    f = Path(rep) / "fontes.json"
    if not f.is_file():
        raise SystemExit(f"repertorio: {f} não existe (a estrutura está no topo de pipeline/repertorio.py)")
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except ValueError as e:
        raise SystemExit(f"repertorio: {f} não é JSON válido ({e})")
    fontes = d.get("fontes") if isinstance(d, dict) else None
    if not isinstance(fontes, list):
        raise SystemExit(f"repertorio: {f} sem a lista `fontes`")
    erros, vistos = [], set()
    for k, x in enumerate(fontes):
        if not isinstance(x, dict):
            erros.append(f"fontes[{k}] não é objeto"); continue
        i = x.get("id")
        if not isinstance(i, str) or not ID_SEGURO.fullmatch(i):
            erros.append(f"fontes[{k}]: id `{i}` fora do padrão a-z, 0-9 e hífen (vira nome de pasta)")
        if i in vistos:
            erros.append(f"id `{i}` repetido")
        vistos.add(i)
        if x.get("tipo") not in TIPOS_FONTE:
            erros.append(f"`{i}`: tipo `{x.get('tipo')}` fora de {', '.join(TIPOS_FONTE)}")
        if x.get("camada") not in CAMADAS:
            erros.append(f"`{i}`: camada `{x.get('camada')}` fora de {', '.join(CAMADAS)}")
        if "min_largura" in x and not (isinstance(x["min_largura"], int) and not isinstance(x["min_largura"], bool) and 300 <= x["min_largura"] <= 3000):
            erros.append(f"`{i}`: min_largura `{x['min_largura']}` tem de ser um inteiro de 300 a 3000")
        if x.get("tipo") in ("behance", "web", "pdf") and not re.match(r"^(https?://|\d+$)", str(x.get("url") or "")):
            erros.append(f"`{i}`: url `{x.get('url')}` não é http(s) nem um id numérico do Behance")
    if erros:
        raise SystemExit(f"repertorio: {f} fora do padrão ({len(erros)} erro(s)): " + "; ".join(erros[:4]))
    return fontes


def capturavel(f):
    return f["tipo"] != "regua" and f["camada"] != "fora"


def pasta_captura(rep, ref):
    if not ID_SEGURO.fullmatch(str(ref)):
        raise SystemExit(f"referência `{ref}` fora do padrão a-z, 0-9 e hífen: vira nome de pasta e não pode sair de capturas/")
    return Path(rep) / "capturas" / ref


def arquivo_manifesto(rep, ref):
    if not ID_SEGURO.fullmatch(str(ref)):
        raise SystemExit(f"referência `{ref}` fora do padrão a-z, 0-9 e hífen: vira nome de arquivo")
    return Path(rep) / "fontes" / f"{ref}.json"


def ler_manifesto(rep, ref):
    f = arquivo_manifesto(rep, ref)
    if not f.is_file():
        return None
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except ValueError:
        return None
    return d if isinstance(d, dict) else None


def _gravar(caminho, dados):
    """Grava num arquivo temporário do lado e troca de uma vez: uma queda no meio não deixa arquivo pela metade."""
    caminho = Path(caminho); caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_name(caminho.name + ".tmp")
    tmp.write_bytes(dados)
    os.replace(tmp, caminho)


def escrever_manifesto(rep, ref, man):
    _gravar(arquivo_manifesto(rep, ref), (json.dumps(man, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))


# ------------------------------------------------ módulos do Behance
def chave_modulo(u):
    """O nome do arquivo sem a extensão: o mesmo módulo em /1400/, /max_1200/ ou /source/ tem a mesma chave."""
    return u.rsplit("/", 1)[-1].rsplit(".", 1)[0]


def extrair_modulos(html, dom=()):
    """URLs de project_modules do HTML (inclusive com `\\/` e `\\u002F` de JSON embutido) e do DOM (img, source, srcset), na ordem em
    que aparecem (primeiro o HTML, depois o que só o DOM mostrou), sem repetir o mesmo arquivo em outro tamanho."""
    texto = (html or "").replace("\\u002F", "/").replace("\\u002f", "/").replace("\\/", "/")
    achados = MODULO.findall(texto)
    for u in dom or ():
        m = MODULO.search(u or "")
        if m:
            achados.append(m.group(0))
    vistos = {}
    for u in achados:
        vistos.setdefault(chave_modulo(u), u)
    return list(vistos.values())


def variantes_do_modulo(u):
    """/1400/, depois /max_1200/, depois o original. URL que não é módulo do Behance fica só com ela mesma."""
    if "/project_modules/" not in u:
        return [u]
    tam = lambda t: re.sub(r"/project_modules/[^/]+/", f"/project_modules/{t}/", u)  # noqa: E731
    out = []
    for v in (tam("1400"), tam("max_1200"), u):
        if v not in out:
            out.append(v)
    return out


def aceitar_pagina(w, h, min_largura=None):
    """Largura menor que MIN_LARGURA (ou o `min_largura` da fonte, para quem só serve imagem pequena) é miniatura ou logo; altura
    menor que MIN_ALTURA_REL da largura é faixa fina."""
    return w >= (min_largura or MIN_LARGURA) and h >= MIN_ALTURA_REL * w


def pagina_bloqueada(status_http, titulo="", texto=""):
    """A página que voltou sem módulos é um bloqueio (e não uma galeria vazia)? Só olha o código HTTP e o título e o começo
    do texto visível (nunca o HTML inteiro, que cita captcha em scripts de páginas normais)."""
    if status_http in (401, 403, 429, 503):
        return True
    t = norm(f"{titulo or ''} {(texto or '')[:1500]}")
    return any(s in t for s in SINAIS_BLOQUEIO)


# ------------------------------------------------ fatiar módulo alto
def _para_rgb(im):
    """RGB; imagem com transparência é composta sobre branco (convert direto deixaria o transparente preto)."""
    from PIL import Image
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        fundo = Image.new("RGB", im.size, (255, 255, 255))
        fundo.paste(im, mask=im.getchannel("A"))
        return fundo
    return im.convert("RGB")


def faixas_uniformes(im):
    """[(y0, y1)] das faixas de cor uniforme: sequências de pelo menos FAIXA_MIN_PX linhas cujo desvio padrão é menor que
    FAIXA_DESVIO (nos três canais) e cuja cor média não varia mais que FAIXA_DERIVA entre a primeira e a última linha."""
    import numpy as np
    a = np.asarray(im.convert("RGB"))
    h = a.shape[0]
    desvio, media = np.empty(h, dtype=np.float32), np.empty(h, dtype=np.float32)
    for i in range(0, h, 512):                                  # em blocos, para não duplicar a imagem alta inteira em float
        c = a[i:i + 512].astype(np.float32)
        desvio[i:i + 512] = c.std(axis=1).max(axis=1)
        media[i:i + 512] = c.mean(axis=(1, 2))
    uni = desvio < FAIXA_DESVIO
    faixas, y = [], 0
    while y < h:
        if not uni[y]:
            y += 1; continue
        z = y
        while z < h and uni[z]:
            z += 1
        if z - y >= FAIXA_MIN_PX and float(media[y:z].max() - media[y:z].min()) <= FAIXA_DERIVA:
            faixas.append((y, z))
        y = z
    return faixas


def janelas_16x9(y0, y1, largura, sobreposicao=None):
    """[(topo, base)] de janelas 16:9 que cobrem y0..y1 com pelo menos `sobreposicao` (4%) entre vizinhas, espaçadas por igual."""
    sobreposicao = SOBREPOSICAO if sobreposicao is None else sobreposicao
    alt = max(1, round(largura * 9 / 16))
    total = y1 - y0
    if total <= alt:
        return [(y0, y1)]
    passo_max = alt * (1 - sobreposicao) - 1                  # 1 px de folga: o arredondamento dos topos não come a sobreposição
    n = max(2, int(-(-(total - alt) // passo_max)) + 1)
    topos = [y0 + round(k * (total - alt) / (n - 1)) for k in range(n)]
    return [(t, t + alt) for t in topos]


def fatiar_modulo(im):
    """[(imagem, fatia)] do módulo. Módulo normal (altura até ALTO_REL vezes a largura) volta inteiro com fatia None. Módulo alto é
    cortado nas faixas de cor uniforme (os espaços entre slides); parte ainda alta, ou módulo sem faixa nenhuma, é cortada em 16:9
    com 4% de sobreposição. fatia = {i, de, y0, y1, modo}; modo `faixa` (parte entre duas faixas) ou `16:9`. Parte mais baixa que
    MIN_ALTURA_REL da largura (sobra de borda) é descartada."""
    w, h = im.size
    if h <= ALTO_REL * w:
        return [(im, None)]
    faixas = faixas_uniformes(im)
    partes, ini = [], 0
    for a, b in faixas:
        if a > ini:
            partes.append((ini, a))
        ini = b
    if ini < h:
        partes.append((ini, h))
    cortes = []
    for a, b in partes:
        if b - a > ALTO_REL * w:
            cortes += [(t, u, "16:9") for t, u in janelas_16x9(a, b, w)]
        elif b - a >= MIN_ALTURA_REL * w:
            cortes.append((a, b, "faixa"))
    return [(im.crop((0, t, w, u)), {"i": k, "de": len(cortes), "y0": t, "y1": u, "modo": modo})
            for k, (t, u, modo) in enumerate(cortes, 1)]


# ------------------------------------------------ páginas, folhas e gravação
def _jpeg(im, qualidade):
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=qualidade, optimize=True)
    return buf.getvalue()


def montar_paginas(modulos, largura=None, min_largura=None):
    """modulos: iterável de (url, PIL.Image). Devolve (paginas, blobs, larguras, descartados): `paginas` no formato do manifesto
    ({n, modulo_url, fatia, w, h, kb, sha256}), `blobs` os [(jpeg, miniatura)] na mesma ordem, `larguras` as larguras de origem
    (para o status) e `descartados` quantos módulos não passaram no filtro. Gera um de cada vez: PDF grande não ocupa a memória."""
    from PIL import Image
    largura = largura or LARGURA_PADRAO
    paginas, blobs, larguras, descartados = [], [], [], 0
    for url, im in modulos:
        im = _para_rgb(im)
        if not aceitar_pagina(im.width, im.height, min_largura):
            descartados += 1; continue
        for parte, fatia in fatiar_modulo(im):
            w0 = parte.width
            if parte.width > largura:
                parte = parte.resize((largura, max(1, round(parte.height * largura / parte.width))), Image.LANCZOS)
            jpg = _jpeg(parte, 85)
            mini = parte if parte.width <= MINI_LARGURA else parte.resize((MINI_LARGURA, max(1, round(parte.height * MINI_LARGURA / parte.width))), Image.LANCZOS)
            paginas.append({"n": len(paginas) + 1, "modulo_url": url, "fatia": fatia, "w": parte.width, "h": parte.height,
                            "kb": max(1, len(jpg) // 1024), "sha256": hashlib.sha256(jpg).hexdigest()})
            blobs.append((jpg, _jpeg(mini, 80))); larguras.append(w0)
    return paginas, blobs, larguras, descartados


def classificar_status(paginas, larguras=None):
    """vazia (nenhuma página); suspeita (menos de 3 páginas, ou todas de menos de 1000 px na origem); ok."""
    if not paginas:
        return "vazia"
    ls = larguras if larguras else [p["w"] for p in paginas]
    if len(paginas) < SUSPEITA_MIN_PAGINAS or all(w < SUSPEITA_LARGURA for w in ls):
        return "suspeita"
    return "ok"


def arquivos_da_captura(paginas):
    """Os caminhos (relativos a capturas/<ref>/) que uma captura com estas páginas escreve: é isto que o manifesto 'possui'."""
    arqs = set()
    for p in paginas:
        arqs.add(f"{p['n']:02d}.jpg"); arqs.add(f"_mini/{p['n']:02d}.jpg")
    for k in range(1, -(-len(paginas) // FOLHA_POR_FOLHA) + 1):
        arqs.add(f"_folha-{k}.jpg")
    return arqs


def gerar_folhas(destino, paginas, origem=None):
    """_folha-1.jpg, _folha-2.jpg... em `destino`: FOLHA_POR_FOLHA páginas por folha, FOLHA_COLUNAS colunas, miniatura de FOLHA_MINI px
    com a altura cortada em FOLHA_ALTURA_REL vezes a largura e o número da página (FOLHA_NUMERO px) numa faixa escura acima dela. As páginas são lidas de `destino`/NN.jpg, ou do caminho que `origem(pagina)`
    devolver (a régua mora em regua/paginas e não é copiada). Devolve os caminhos."""
    from PIL import Image, ImageDraw
    from regua import fonte_ui
    destino = Path(destino); fonte = fonte_ui(FOLHA_NUMERO); m = 8
    saidas = []
    for k, ini in enumerate(range(0, len(paginas), FOLHA_POR_FOLHA), 1):
        thumbs = []
        for p in paginas[ini:ini + FOLHA_POR_FOLHA]:
            im = Image.open(origem(p) if origem else destino / f"{p['n']:02d}.jpg").convert("RGB")
            t = im.resize((FOLHA_MINI, max(40, round(im.height * FOLHA_MINI / im.width))), Image.LANCZOS)
            thumbs.append((p["n"], t.crop((0, 0, FOLHA_MINI, min(t.height, round(FOLHA_MINI * FOLHA_ALTURA_REL))))))
        linhas = [thumbs[i:i + FOLHA_COLUNAS] for i in range(0, len(thumbs), FOLHA_COLUNAS)]
        faixa = FOLHA_NUMERO + 10                                   # o número fica numa faixa escura acima da miniatura: não cobre a página
        W = FOLHA_COLUNAS * (FOLHA_MINI + m) + m
        H = sum(faixa + max(t.height for _, t in lin) + m for lin in linhas) + m
        F = Image.new("RGB", (W, H), (24, 24, 24)); d = ImageDraw.Draw(F)
        y = m
        for lin in linhas:
            for c, (n, t) in enumerate(lin):
                x = m + c * (FOLHA_MINI + m)
                d.rectangle([x, y, x + FOLHA_MINI - 1, y + faixa - 1], fill=(0, 0, 0))
                d.text((x + 7, y + 3), f"{n:02d}", fill=(255, 90, 90), font=fonte)
                F.paste(t, (x, y + faixa))
            y += faixa + max(t.height for _, t in lin) + m
        caminho = destino / f"_folha-{k}.jpg"
        buf = io.BytesIO(); F.save(buf, "JPEG", quality=80, optimize=True)
        _gravar(caminho, buf.getvalue()); saidas.append(caminho)
    return saidas


def gravar_captura(rep, ref, man, blobs):
    """Grava as páginas, as miniaturas, as folhas e (por último) o manifesto de `ref`. Só escreve dentro de capturas/<ref>/ e só
    sobrescreve arquivo que o manifesto anterior da própria referência lista: qualquer outro arquivo no caminho é recusado antes
    de gravar o primeiro byte. O que o manifesto anterior listava e a captura nova não reescreve (página que sobrou) sai."""
    destino = pasta_captura(rep, ref)
    antigo = ler_manifesto(rep, ref)
    meus = arquivos_da_captura(antigo.get("paginas") or []) if antigo else set()
    novos = arquivos_da_captura(man["paginas"])
    for rel in sorted(novos):
        if (destino / rel).exists() and rel not in meus:
            raise ErroCaptura(f"{ref}: {destino / rel} já existe e o manifesto da referência não lista esse arquivo; não sobrescrevo "
                              "(se for sobra de uma captura interrompida, apague a pasta à mão)")
    for p, (jpg, mini) in zip(man["paginas"], blobs):
        _gravar(destino / f"{p['n']:02d}.jpg", jpg)
        _gravar(destino / "_mini" / f"{p['n']:02d}.jpg", mini)
    gerar_folhas(destino, man["paginas"])
    for rel in sorted(meus - novos):
        (destino / rel).unlink(missing_ok=True)
    escrever_manifesto(rep, ref, man)


def paginas_da_regua(rep, f):
    """[{n, arquivo, fatia, w, h, kb, sha256}] das páginas <pasta>/<id>-NN.jpg de um kit da régua (a pasta é relativa à raiz do projeto,
    o pai de repertorio/). Só lê: nada da régua é copiado ou mexido. `arquivo` é o caminho relativo à raiz do projeto."""
    from PIL import Image
    raiz = Path(rep).resolve().parent
    pasta = (raiz / (f.get("pasta") or "regua/paginas")).resolve()
    if raiz not in pasta.parents:
        raise ErroCaptura(f"{f['id']}: a pasta `{f.get('pasta')}` sai da raiz do projeto")
    padrao = re.compile(rf"^{re.escape(f['id'])}-(\d+)\.(?:jpg|jpeg|png)$", re.I)
    achados = sorted(((int(m.group(1)), a) for a in pasta.glob("*") if (m := padrao.match(a.name))), key=lambda x: x[0]) if pasta.is_dir() else []
    if not achados:
        raise ErroCaptura(f"{f['id']}: sem páginas {f['id']}-NN.jpg em {pasta}")
    paginas = []
    for n, a in achados:
        with Image.open(a) as im:
            w, h = im.size
        paginas.append({"n": n, "arquivo": a.relative_to(raiz).as_posix(), "fatia": None, "w": w, "h": h,
                        "kb": max(1, a.stat().st_size // 1024), "sha256": hashlib.sha256(a.read_bytes()).hexdigest()})
    return paginas


def folha_contato(rep, ref):
    """Regera as folhas de contato de `ref` em capturas/<ref>/. Devolve os caminhos. Referência capturada: usa as páginas do manifesto.
    Kit da régua (tipo `regua` em fontes.json): monta o manifesto apontando para regua/paginas e gera só as folhas, sem copiar página."""
    rep = Path(rep)
    f = next((x for x in carregar_fontes(rep) if x["id"] == ref), None) if (rep / "fontes.json").is_file() else None
    destino = pasta_captura(rep, ref)
    if f and f["tipo"] == "regua":
        paginas = paginas_da_regua(rep, f)
        saidas = gerar_folhas(destino, paginas, origem=lambda p: rep.resolve().parent / p["arquivo"])
        man = {"ref": ref, "url": None, "canonica": None, "capturada_em": agora(), "status": "ok", "tipo": "regua",
               "pasta": f.get("pasta") or "regua/paginas", "paginas": paginas}
    else:
        man = ler_manifesto(rep, ref)
        if not man or not man.get("paginas"):
            raise ErroCaptura(f"{ref}: sem manifesto com páginas em {arquivo_manifesto(rep, ref)} (rode `capturar --ref {ref}`)")
        faltam = [p["n"] for p in man["paginas"] if not (destino / f"{p['n']:02d}.jpg").is_file()]
        if faltam:
            raise ErroCaptura(f"{ref}: faltam páginas em {destino} ({', '.join(f'{n:02d}' for n in faltam[:6])}...); capture de novo com --forcar")
        saidas = gerar_folhas(destino, man["paginas"])
    for velho in destino.glob("_folha-*.jpg"):
        if velho not in saidas:
            velho.unlink()
    if f and f["tipo"] == "regua":
        escrever_manifesto(rep, ref, man)
    return saidas


# ------------------------------------------------ limites de disco
def tamanho_dir(p):
    p = Path(p)
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if p.is_dir() else 0


def checar_limites(rep):
    """LimiteAtingido quando há menos de DISCO_MIN_GB livres ou capturas/ passou de CAPTURAS_MAX_MB."""
    livre = shutil.disk_usage(rep).free
    if livre < DISCO_MIN_GB * 1024 ** 3:
        raise LimiteAtingido(f"só {livre / 1024 ** 3:.1f} GB livres no disco (mínimo {DISCO_MIN_GB} GB)")
    mb = tamanho_dir(Path(rep) / "capturas") / 1024 ** 2
    if mb > CAPTURAS_MAX_MB:
        raise LimiteAtingido(f"capturas/ tem {mb:.0f} MB (limite {CAPTURAS_MAX_MB} MB)")


# ------------------------------------------------ navegador e uma referência
def rasterizar_pdf(url, largura):
    """Gerador de (url#page=N, imagem): baixa o PDF para uma pasta temporária, rasteriza com pdftoppm e apaga tudo ao acabar."""
    import urllib.request
    from PIL import Image
    import regua
    with tempfile.TemporaryDirectory() as t:
        pdf = Path(t) / "fonte.pdf"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": regua.UA})
            dados = urllib.request.urlopen(req, timeout=60).read(150 * 1024 * 1024 + 1)
        except Exception as e:
            raise ErroCaptura(f"PDF não baixou: {str(e)[:100]}")
        if len(dados) > 150 * 1024 * 1024:
            raise ErroCaptura("PDF maior que 150 MB: não rasterizo")
        pdf.write_bytes(dados)
        subprocess.run(["pdftoppm", "-scale-to-x", str(largura), "-scale-to-y", "-1", "-jpeg", "-jpegopt", "quality=85", str(pdf), str(Path(t) / "p")],
                       check=True, capture_output=True)
        for i, p in enumerate(sorted(Path(t).glob("p-*.jpg"), key=lambda p: int(p.stem.split("-")[-1])), 1):
            im = Image.open(p); im.load()
            yield f"{url}#page={i}", im


def chave_web(u):
    """A mesma imagem em outro tamanho tem a mesma chave: sem query e sem o sufixo -852x479 do nome do arquivo."""
    return re.sub(r"-\d+x\d+(?=\.[A-Za-z0-9]+$)", "", str(u).split("?")[0].split("#")[0]).lower()


def mesclar_candidatas(base, extras):
    """`base` (candidatas_web) como veio, depois as `extras` (maior URL do srcset) que ainda não estão lá, sem repetir a mesma imagem
    em outro tamanho."""
    vistos, saida = set(), []
    for u in list(base or []) + list(extras or []):
        k = chave_web(u)
        if k not in vistos and not str(u).startswith("data:"):
            vistos.add(k); saida.append(u)
    return saida


def coletar_srcset(pg):
    """Maior URL do srcset das imagens de article, main e figure da página, na ordem do documento e sem repetir ([] se a página não deixar ler)."""
    try:
        return list(dict.fromkeys(u for u in pg.evaluate(JS_SRCSET, [SELETOR_CONTEUDO, EXCLUIR_DO_CONTEUDO]) if isinstance(u, str)))
    except Exception:
        return []


class Navegador:
    """Playwright headless com a identificação do regua.py. Abre o Chromium só na primeira referência que precisa dele."""
    def __init__(self):
        self._pw = self._nav = self._ctx = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self._nav:
            self._nav.close()
        if self._pw:
            self._pw.stop()

    def _abrir(self):
        if self._ctx is None:
            import regua
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright().start()
            self._nav = self._pw.chromium.launch()
            self._ctx = self._nav.new_context(viewport={"width": 1400, "height": 900}, user_agent=regua.UA)

    def coletar(self, f):
        """{status_http, titulo, texto, canonica, urls} de uma referência behance ou web; {gerador} de um PDF."""
        if f["tipo"] == "pdf":
            return {"status_http": 200, "titulo": "", "texto": "", "canonica": None, "gerador": rasterizar_pdf(f["url"], f.get("largura") or LARGURA_PADRAO)}
        import regua
        self._abrir()
        url = f"https://www.behance.net/gallery/{f['url']}" if re.fullmatch(r"\d+", str(f["url"])) else f["url"]
        pg = self._ctx.new_page()
        try:
            resp = pg.goto(url, wait_until="domcontentloaded", timeout=45000)
            status = resp.status if resp else None
            if f["tipo"] == "behance":
                pg.wait_for_timeout(ESPERA_INICIAL_MS)
                for _ in range(ROLAGENS):
                    pg.mouse.wheel(0, ROLAGEM_PX); pg.wait_for_timeout(ROLAGEM_MS)
                urls = extrair_modulos(pg.content(), pg.evaluate(JS_DOM))
            else:
                urls = mesclar_candidatas(regua.candidatas_web(pg), coletar_srcset(pg))
            return {"status_http": status, "titulo": pg.title(), "texto": pg.evaluate(JS_TEXTO), "canonica": pg.evaluate(JS_CANONICA), "urls": urls}
        finally:
            pg.close()

    def baixar(self, variantes):
        """(imagem, url usada, códigos HTTP vistos): a primeira variante que baixa e abre como imagem."""
        from PIL import Image
        self._abrir()
        codigos = []
        for v in variantes:
            try:
                r = self._ctx.request.get(v, timeout=30000)
            except Exception:
                codigos.append(None); continue
            codigos.append(r.status)
            if not r.ok:
                continue
            try:
                im = Image.open(io.BytesIO(r.body())); im.load()
            except Exception:
                continue
            return im, v, codigos
        return None, None, codigos


def _baixar_todos(nav, urls, cont):
    """Gerador de (url usada, imagem); `cont['barrados']` conta os 401, 403 e 429 que o servidor devolveu nas imagens e
    `cont['baixados']` os módulos que vieram."""
    for u in urls:
        im, usada, codigos = nav.baixar(variantes_do_modulo(u))
        cont["barrados"] += sum(1 for c in codigos if c in (401, 403, 429))
        if im is not None:
            cont["baixados"] += 1
            yield usada, im


def _tentar(f, nav, largura):
    """Uma tentativa: abre a referência, baixa os módulos, monta as páginas. Nunca levanta (o erro vai em `erro`)."""
    r = {"status": "vazia", "http": None, "canonica": None, "erro": None, "paginas": [], "blobs": [], "descartados": 0, "achados": 0, "baixados": 0}
    try:
        col = nav.coletar(f)
        r["http"], r["canonica"] = col.get("status_http"), col.get("canonica")
        cont = {"barrados": 0, "baixados": 0}
        if col.get("gerador") is not None:
            modulos = col["gerador"]
        else:
            urls = col.get("urls") or []
            r["achados"] = len(urls)
            if not urls:
                r["status"] = "bloqueada" if pagina_bloqueada(col.get("status_http"), col.get("titulo"), col.get("texto")) else "vazia"
                r["erro"] = f"nenhum módulo na página (HTTP {col.get('status_http')}, título: {str(col.get('titulo'))[:60]!r})"
                return r
            modulos = _baixar_todos(nav, urls, cont)
        r["paginas"], r["blobs"], larguras, r["descartados"] = montar_paginas(modulos, largura, f.get("min_largura"))
        r["baixados"] = cont["baixados"]
    except Exception as e:
        r["erro"] = f"{type(e).__name__}: {str(e)[:160]}"
        return r
    if not r["paginas"]:
        r["status"] = "bloqueada" if cont["barrados"] else "vazia"
        r["erro"] = r["erro"] or ("o servidor recusou as imagens (401, 403 ou 429)" if cont["barrados"] else "nenhuma imagem passou no filtro de tamanho")
    else:
        r["status"] = classificar_status(r["paginas"], larguras)
    return r


def agora():
    return datetime.datetime.now().isoformat(timespec="seconds")


def capturar_fonte(rep, f, nav, largura=None, dormir=time.sleep, espera_retry=None):
    """Captura uma referência (até TENTATIVAS vezes, com ESPERA_RETRY s entre elas), grava e devolve o manifesto. Resultado sem
    nenhuma página nunca substitui um manifesto que já tem páginas."""
    espera_retry = ESPERA_RETRY if espera_retry is None else espera_retry
    ref, largura = f["id"], largura or f.get("largura") or LARGURA_PADRAO
    res = None
    for t in range(1, TENTATIVAS + 1):
        res = _tentar(f, nav, largura)
        res["tentativas"] = t
        if res["status"] in ("ok", "suspeita"):
            break
        if t < TENTATIVAS:
            print(f"  {ref}: {res['status']} ({res['erro']}); outra tentativa em {espera_retry} s", flush=True)
            dormir(espera_retry)
    man = {"ref": ref, "url": f["url"], "canonica": res["canonica"], "capturada_em": agora(), "status": res["status"],
           "http": res["http"], "tentativas": res["tentativas"], "largura": largura,
           "modulos": {"achados": res["achados"], "baixados": res["baixados"], "descartados": res["descartados"]}}
    if f.get("min_largura"):
        man["min_largura"] = f["min_largura"]
    if res["status"] == "suspeita" and f.get("motivo_suspeita"):
        man["motivo_suspeita"] = f["motivo_suspeita"]
    if res["erro"]:
        man["erro"] = res["erro"]
    man["paginas"] = res["paginas"]
    antigo = ler_manifesto(rep, ref)
    if res["paginas"]:
        gravar_captura(rep, ref, man, res["blobs"])
    elif antigo and antigo.get("paginas"):
        print(f"  {ref}: a captura nova não trouxe páginas; mantive o manifesto e as páginas anteriores", flush=True)
        return dict(antigo, _mantido=True, _status_novo=res["status"])
    else:
        escrever_manifesto(rep, ref, man)
    return man


def conta_como_bloqueio(status, f):
    """O que alimenta o disjuntor: bloqueada (403, captcha, imagens recusadas) sempre; vazia (página sem módulos) só no Behance, onde
    é o sinal de bloqueio. Artigo ou site que simplesmente não tem imagem grande não é bloqueio."""
    return status == "bloqueada" or (status == "vazia" and f.get("tipo") == "behance")


def executar_captura(rep, fontes, nav, largura=None, pausa=4, forcar=False, dormir=time.sleep, espera_retry=None):
    """Captura `fontes` uma por vez. Devolve (resultados, código): 0 normal, 3 se BLOQUEIOS_SEGUIDOS referências seguidas voltaram
    bloqueadas (ou, no Behance, sem módulos), 4 se o disco ou capturas/ passaram do limite. Cada resultado é {ref, status, paginas, mb}."""
    resultados, seguidos, codigo, rede = [], 0, 0, False

    def reg(ref, status, man=None, nota=""):
        n = len(man.get("paginas") or []) if man else 0
        mb = tamanho_dir(pasta_captura(rep, ref)) / 1024 ** 2 if n else 0.0
        resultados.append({"ref": ref, "status": status, "paginas": n, "mb": mb, "nota": nota})
        print(f"{status.upper():<10} {ref:<44} {n:>4} páginas {mb:>7.1f} MB  {nota}".rstrip(), flush=True)

    for f in fontes:
        ref = f["id"]
        if not capturavel(f):
            reg(ref, "sem-captura", None, "régua: as páginas estão em regua/paginas" if f["tipo"] == "regua" else f"fora do estudo: {f.get('motivo', '')}")
            continue
        man = ler_manifesto(rep, ref)
        if man and man.get("status") == "ok" and not forcar:
            reg(ref, "pulada", man, "já tem manifesto ok (use --forcar para refazer)")
            continue
        try:
            checar_limites(rep)
        except LimiteAtingido as e:
            print(f"PARADO     {e}; parei antes de {ref}", flush=True)
            codigo = SAIDA_DISCO
            break
        if rede and pausa:
            dormir(pausa)
        rede = True
        try:
            novo = capturar_fonte(rep, f, nav, largura, dormir, espera_retry)
        except ErroCaptura as e:
            reg(ref, "erro", None, str(e)[:300])
            continue
        if novo.get("_mantido"):
            reg(ref, novo["_status_novo"], None, f"a captura nova falhou; mantive as {len(novo['paginas'])} páginas anteriores")
            seguidos = seguidos + 1 if conta_como_bloqueio(novo["_status_novo"], f) else 0
            if seguidos >= BLOQUEIOS_SEGUIDOS:
                print(f"DISJUNTOR  {seguidos} referências seguidas bloqueadas ou sem módulos; parei sem tentar contornar", flush=True)
                codigo = SAIDA_BLOQUEIO
                break
            continue
        status = novo["status"]
        reg(ref, status, novo, (novo.get("erro") or "") if status not in ("ok", "suspeita") else "")
        seguidos = seguidos + 1 if conta_como_bloqueio(status, f) else 0
        if seguidos >= BLOQUEIOS_SEGUIDOS:
            print(f"DISJUNTOR  {seguidos} referências seguidas bloqueadas ou sem módulos; parei sem tentar contornar", flush=True)
            codigo = SAIDA_BLOQUEIO
            break
    return resultados, codigo


def selecionar(fontes, refs=(), camadas=()):
    """As fontes pedidas por --ref e/ou --camada (união), na ordem do fontes.json."""
    refs, camadas = set(refs), set(camadas)
    return [f for f in fontes if f["id"] in refs or f["camada"] in camadas]


def imprimir_tabela(resultados):
    print("\nreferência | status | páginas | MB")
    for r in resultados:
        print(f"{r['ref']} | {r['status']} | {r['paginas']} | {r['mb']:.1f}")
    print(f"total: {sum(r['paginas'] for r in resultados)} páginas, {sum(r['mb'] for r in resultados):.1f} MB")


def listar_fontes(rep, fontes):
    for f in fontes:
        man = ler_manifesto(rep, f["id"])
        estado = man.get("status", "?") if man else "-"
        print(f"{f['id']:<44} {f['camada']:<12} {f['tipo']:<8} manifesto: {estado:<10} {f.get('url') or f.get('pasta') or ''}")
    print(f"{len(fontes)} fonte(s)")


# ------------------------------------------------ conferir com o estudo anterior
def contagem_da_ficha(rep, ref):
    """{olhadas, total} citado na ficha referencias/<ref>.md do estudo anterior ('Imagens olhadas: 23 de 23'); None se a ficha não diz."""
    f = Path(rep) / "referencias" / f"{ref}.md"
    if not f.is_file():
        return None
    t = f.read_text(encoding="utf-8")
    m = re.search(r"Imagens (?:olhadas|vistas):\**\s*(\d+)\s+de\s+(\d+)", t)
    if m:
        return {"olhadas": int(m.group(1)), "total": int(m.group(2))}
    m = re.search(r"Imagens (?:olhadas|vistas):\**\s*(\d+)", t) or re.search(r"\bde (\d+) p[aá]ginas", t)
    return {"olhadas": int(m.group(1)), "total": int(m.group(1))} if m else None


def recortes_da_referencia(indice, ref):
    """[(arquivo, pagina_v1)] dos recortes do índice que citam `ref`, sem repetir o arquivo."""
    out, vistos = [], set()
    for p in (indice.get("padroes") or []) if isinstance(indice, dict) else []:
        for r in (p.get("recortes") or []) if isinstance(p, dict) else []:
            if isinstance(r, dict) and r.get("referencia") == ref and r.get("arquivo") not in vistos and isinstance(r.get("pagina"), int):
                vistos.add(r["arquivo"]); out.append((r["arquivo"], r["pagina"]))
    return out


def _escalas(recorte_im):
    """Fatores pelos quais o recorte foi reduzido na gravação do estudo anterior (lado maior limitado a LADO_MAX): 1,0 quando coube,
    senão uma grade de 1,0 a 0,32 (a página de origem pode ser bem maior que o recorte)."""
    if max(recorte_im.size) < LADO_MAX - 2:
        return [1.0]
    return [round(1.0 - 0.04 * i, 2) for i in range(0, 18)]


def nota_do_recorte(recorte, pagina_cinza, fator):
    """Melhor nota (TM_CCOEFF_NORMED, 0 a 1) do recorte (PIL) dentro da página (matriz cinza já reduzida por `fator`). O recorte pode
    ter sido reduzido no estudo anterior: testa a grade de escalas e refina em passo de 0,01 em volta da melhor. -1 quando o recorte
    não cabe na página ou não tem textura."""
    import cv2, numpy as np
    rec = np.asarray(recorte.convert("L"))

    def nota_na_escala(k):
        s = fator / k
        w, h = max(1, round(rec.shape[1] * s)), max(1, round(rec.shape[0] * s))
        if w > pagina_cinza.shape[1] or h > pagina_cinza.shape[0] or w < 8 or h < 8:
            return -1.0
        t = cv2.GaussianBlur(cv2.resize(rec, (w, h), interpolation=cv2.INTER_AREA), (3, 3), 0)
        if float(t.std()) < 1.0:
            return -1.0
        r = np.nan_to_num(cv2.matchTemplate(pagina_cinza, t, cv2.TM_CCOEFF_NORMED), nan=-1.0, posinf=-1.0, neginf=-1.0)
        return float(r.max())

    escalas = _escalas(recorte)
    notas = {k: nota_na_escala(k) for k in escalas}
    melhor_k = max(notas, key=notas.get)
    if len(escalas) > 1:
        for d in (-0.03, -0.02, -0.01, 0.01, 0.02, 0.03):
            k = round(melhor_k + d, 2)
            if 0.2 < k <= 1.0 and k not in notas:
                notas[k] = nota_na_escala(k)
    return max(notas.values())


def conferir(rep, ref):
    """Confere a captura de `ref` com o estudo anterior e grava o resultado no manifesto. Devolve o relatório:
    {ref, v2, ficha, maior_pagina_recorte, linhas: [{arquivo, v1, nota_v1, v2, nota_v2}], v1_para_v2, v1_nao_achados}."""
    from PIL import Image
    import cv2, numpy as np
    rep = Path(rep)
    man = ler_manifesto(rep, ref)
    if not man or not man.get("paginas"):
        raise ErroCaptura(f"{ref}: sem manifesto com páginas (rode `capturar --ref {ref}`)")
    destino = pasta_captura(rep, ref)
    n2 = [p["n"] for p in man["paginas"]]
    cache = {}

    def pagina(n):
        if n not in cache:
            im = Image.open(destino / f"{n:02d}.jpg").convert("L")
            f = TRABALHO_LARGURA / im.width
            cache[n] = (cv2.GaussianBlur(np.asarray(im.resize((TRABALHO_LARGURA, max(1, round(im.height * f))), Image.LANCZOS)), (3, 3), 0), f)
        return cache[n]

    def nota(rec, n):
        m, f = pagina(n)
        return nota_do_recorte(rec, m, f)

    recortes = recortes_da_referencia(carregar(rep, estrito=False), ref)
    linhas, mapa, perdidos = [], {}, []
    for arquivo, v1 in recortes:
        f_rec = rep / arquivo
        if not f_rec.is_file():
            linhas.append({"arquivo": arquivo, "v1": v1, "nota_v1": None, "v2": None, "nota_v2": None, "situacao": "recorte do estudo anterior ausente"}); continue
        rec = Image.open(f_rec); rec.load()
        n_v1 = nota(rec, v1) if v1 in n2 else -1.0
        if n_v1 >= NOTA_MIN:
            linhas.append({"arquivo": arquivo, "v1": v1, "nota_v1": n_v1, "v2": v1, "nota_v2": n_v1, "situacao": "igual"}); continue
        vizinhas = [n for n in n2 if abs(n - v1) <= 3 and n != v1]
        melhor_n, melhor = None, -1.0
        for rodada in (vizinhas, [n for n in n2 if n != v1 and n not in vizinhas]):
            for n in rodada:
                s = nota(rec, n)
                if s > melhor:
                    melhor_n, melhor = n, s
            if melhor >= NOTA_MIN:
                break
        if melhor >= NOTA_MIN:
            mapa.setdefault(v1, set()).add(melhor_n)
            linhas.append({"arquivo": arquivo, "v1": v1, "nota_v1": n_v1, "v2": melhor_n, "nota_v2": melhor, "situacao": "mudou de página"})
        else:
            perdidos.append(v1)
            linhas.append({"arquivo": arquivo, "v1": v1, "nota_v1": n_v1, "v2": melhor_n, "nota_v2": melhor, "situacao": "não achado"})
    ficha = contagem_da_ficha(rep, ref)
    maior = max((v for _, v in recortes), default=None)
    v1_para_v2 = {str(k): (sorted(v)[0] if len(v) == 1 else sorted(v)) for k, v in sorted(mapa.items())}
    man["v1_contagem"] = {"ficha": ficha["total"] if ficha else None, "maior_pagina_de_recorte": maior, "v2": len(n2)}
    man["v1_para_v2"] = v1_para_v2
    man["v1_nao_achados"] = sorted(set(perdidos))
    man["v1_conferido_em"] = agora()
    escrever_manifesto(rep, ref, man)
    return {"ref": ref, "v2": len(n2), "ficha": ficha, "maior_pagina_recorte": maior, "linhas": linhas,
            "v1_para_v2": v1_para_v2, "v1_nao_achados": sorted(set(perdidos))}


def imprimir_conferencia(r):
    ref, v2, ficha, maior = r["ref"], r["v2"], r["ficha"], r["maior_pagina_recorte"]
    base = ficha["total"] if ficha else maior
    if base is None:
        veredito = "sem número do estudo anterior para comparar"
    elif v2 == base:
        veredito = "IGUAL"
    elif v2 > base:
        veredito = f"MAIS {v2 - base} (fatiou módulo alto ou achou mais imagens)"
    else:
        veredito = f"MENOS {base - v2} (FALTAM páginas)"
    citado = ficha["total"] if ficha else "não citado"
    olhou = f" (olhou {ficha['olhadas']})" if ficha and ficha["olhadas"] != ficha["total"] else ""
    print(f"\n{ref}: v1 = {citado} na ficha{olhou}, maior página de recorte = {maior if maior is not None else '-'}; v2 = {v2} páginas -> {veredito}")
    if not r["linhas"]:
        print("  sem recortes do estudo anterior nesta referência")
        return
    print(f"  {'recorte':<64} {'pág v1':>6} {'nota':>6} {'pág v2':>6} {'nota':>6}  situação")
    for l in r["linhas"]:
        nome = Path(l["arquivo"]).name
        nome = nome if len(nome) <= 64 else nome[:61] + "..."
        f = lambda x: "-" if x is None or x < 0 else f"{x:.2f}"  # noqa: E731
        print(f"  {nome:<64} {l['v1']:>6} {f(l['nota_v1']):>6} {str(l['v2'] or '-'):>6} {f(l['nota_v2']):>6}  {l['situacao']}")
    print(f"  v1_para_v2: {r['v1_para_v2'] or 'nenhuma mudança de página'}" + (f"; não achados (página v1): {r['v1_nao_achados']}" if r["v1_nao_achados"] else ""))


def cmd_capturar(rep, a):
    fontes = carregar_fontes(rep)
    refs, camadas = _lista_de(a.ref), _lista_de(a.camada)
    ruins = [c for c in camadas if c not in CAMADAS]
    if ruins:
        sys.exit(f"repertorio: camada(s) `{', '.join(ruins)}` não existem (use: {', '.join(CAMADAS)})")
    ids = {f["id"] for f in fontes}
    soltas = [r for r in refs if r not in ids]
    if soltas:
        sys.exit(f"repertorio: referência(s) `{', '.join(soltas)}` fora de fontes.json (repertorio.py capturar --listar mostra os ids)")
    if not refs and not camadas and not a.listar:
        sys.exit(f"repertorio: diga o que capturar: --ref ID ... ou --camada C ... (camadas: {', '.join(CAMADAS)}); --listar mostra tudo sem baixar nada")
    sel = selecionar(fontes, refs, camadas) if (refs or camadas) else fontes
    if a.listar:
        listar_fontes(rep, sel)
        return 0
    try:
        checar_limites(rep)
    except LimiteAtingido as e:
        print(f"RECUSADO   {e}; não começo", file=sys.stderr)
        return SAIDA_DISCO
    with Navegador() as nav:
        resultados, codigo = executar_captura(rep, sel, nav, a.largura, a.pausa, a.forcar)
    imprimir_tabela(resultados)
    return codigo


# ================================================================ v2: recursos de acabamento (estudo visual v2, 12/10/2026)
# Só acréscimo: o índice v1 e os comandos de antes continuam iguais (buscar sem --entidade dá a mesma saída). O .md do
# recurso (repertorio/recursos/<id>.md, briefing-redator-v2.md) é a fonte; o `indexar` copia o front matter, o trecho de
# acabamento e os recortes citados em `## Referências` para recursos[] do índice, com as anotações que o `anotar` gravou.
SECOES_RECURSO = ("Efeito", "Como se organiza", "Relação com o conteúdo", "Condições", "O que pode variar", "Como adaptar",
                  "Cuidados", "Como produzir e conferir")
SECOES_RECURSO_FIM = ("Trecho de acabamento", "Referências")
TRAVESSOES = ("\u2014", "\u2013")
SO_NO_MD = ("provisorio",)          # chave do front matter que não vai ao índice (o schema do índice é estrito)
LISTAS_FRONT = ("recurso", "dimensoes", "material", "borda", "tipo_pagina", "funcao", "tom", "padroes", "tratamento_imagem",
                "tipografia", "mistura", "uau_gatilhos", "eixos", "depende")
LINHAS_RECURSO = (70, 130)          # tamanho do .md pedido pelo briefing: fora disso, AVISO
EIXOS = ("escala", "orientacao", "cor", "material", "densidade", "enquadramento", "localizacao", "relacao-texto", "intensidade")
ROTA_DA_VIA = {"codigo-svg-css": "codigo", "grafismo-existente": "codigo", "raster-tratar": "imagem", "codex-objeto": "imagem",
               "codex-textura": "imagem", "codex-cena": "imagem", "compor-homografia": "hibrido", "misto": "hibrido"}
LUZ_KIT = {"esq": "esq", "dir": "dir", "topo": "topo"}             # acabamento.luz do kit; base, frente e tras viram nenhuma
PROF_KIT = {"plana": "plana", "camadas": "camadas", "sombra": "camadas", "perspectiva": "volume", "isometrica": "volume",
            "volume": "volume", "cena": "volume"}
# recurso que é a página inteira (a conferência de recorte vazio não avisa de recorte grande nele); o resto é de detalhe
RECURSOS_DE_PAGINA = ("cena-3d", "tratamento", "colagem", "transicao", "textura", "pattern", "moldura")
AMARELO, ESCURO, FUNDO_LEGENDA = (255, 212, 0), (17, 17, 19), (21, 21, 24)    # caixa #FFD400 entre dois contornos escuros
DISCO, SETA = 30, 4                 # px: diâmetro do disco numerado e traço da seta
LARGURA_MIN_ANOTADO, LARGURA_MAPA, QUALIDADE_ANOTADO = 640, 1200, 85
VAZIO_AREA_MAX, VAZIO_AREA_MIN, VAZIO_DESVIO_MIN, DHASH_IGUAL = 0.85, 0.02, 4.0, 2   # recorte vazio: AVISO
MIN_COBERTURA = 3                   # cada dimensão com 3 ou mais recursos de 3 ou mais referências (LEIA-ME do estudo)
CONSULTA_ARQ, CONSULTA_FOLHA = "consulta-repertorio.json", "mood/consulta-recursos.png"
HISTORICO_KITS = AQUI.parent / "memoria-mediakit" / "historico-kits.json"
POR_FAMILIA = 3                     # consultar: quantos recursos de cada família entram em `ids`
PENA_RECENTE = 2                    # consultar: recurso de um dos 3 últimos kits de outro cliente perde 2 pontos
INTERPRETES = ("python", "python3", "bash", "sh")


@functools.lru_cache(maxsize=None)
def _defs():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))["definitions"]


def voc(nome):
    """Valores do vocabulário fechado `voc_<nome>` do schema do repertório (o mesmo bloco `vocabulario` da RUBRICA-v2.md)."""
    d = _defs()[f"voc_{nome}"]
    return tuple(d["enum"]) if "enum" in d else tuple(range(d["minimum"], d["maximum"] + 1))


def _tem_travessao(texto):
    return any(t in texto for t in TRAVESSOES)


def _bloco_json_da_secao(corpo, comeco):
    """(objeto, erro) do primeiro bloco ```json da seção cujo título normalizado começa com `comeco`."""
    for titulo, linhas in secoes_do_md(corpo):
        if norm(titulo).startswith(comeco):
            i = next((n for n, l in enumerate(linhas) if re.match(r"^\s*```\s*json\s*$", l, re.I)), None)
            if i is None:
                return None, None
            j = next((n for n in range(i + 1, len(linhas)) if linhas[n].strip().startswith("```")), None)
            if j is None:
                return None, "bloco ```json sem fechamento"
            try:
                return json.loads("\n".join(linhas[i + 1:j])), None
            except ValueError as e:
                return None, f"JSON inválido ({e})"
    return None, None


def trecho_de_acabamento(corpo):
    """(objeto, erro) do bloco ```json da seção `## Trecho de acabamento` (o contrato que o kit copia sem tradução)."""
    return _bloco_json_da_secao(corpo, "trecho de acabamento")


def comandos_da_producao(corpo):
    """Linhas dos blocos de código da seção `## 8. Como produzir e conferir` (um comando por linha)."""
    for titulo, linhas in secoes_do_md(corpo):
        if re.match(r"^8\.\s", titulo):
            out, dentro = [], False
            for l in linhas:
                if l.lstrip().startswith("```"):
                    dentro = not dentro; continue
                if dentro and l.strip() and not l.strip().startswith("#"):
                    out.append(l.strip())
            return out
    return []


def comando_existe(linha):
    """(ok, motivo): o comando começa por um script de pipeline/ (aceita `python`, `bash` e `pipeline/` na frente) e, se o
    script tem subcomandos (add_parser), o segundo termo é um deles. Só o que existe no código hoje."""
    import shlex
    try:
        partes = shlex.split(linha)
    except ValueError:
        partes = linha.split()
    while partes and (partes[0] in INTERPRETES or partes[0].endswith("/python") or re.fullmatch(r"[A-Z_][A-Z0-9_]*=\S*", partes[0])):
        partes = partes[1:]
    if not partes:
        return False, "linha sem comando"
    script = partes[0][len("pipeline/"):] if partes[0].startswith("pipeline/") else partes[0]
    if "/" in script or not script or not (AQUI / script).is_file():
        return False, f"`{script}` não existe em pipeline/"
    subs = sorted(set(re.findall(r'add_parser\(\s*"([^"]+)"', (AQUI / script).read_text(encoding="utf-8", errors="ignore")))) if script.endswith(".py") else []
    if subs and (len(partes) < 2 or partes[1] not in subs):
        return False, f"`{script}` não tem o subcomando `{partes[1] if len(partes) > 1 else ''}` (tem: {', '.join(subs)})"
    return True, ""


def conferir_trecho_acabamento(fm, trecho):
    """(erros, avisos) do trecho de acabamento de um recurso: direcao_criativa no schema do kit (mediakit.schema.json),
    pagina como composicao_pagina e nas regras de composicao.validar e acabamento.validar (o que a página decide sozinha),
    o id do recurso nos quatro lugares, intensidade dentro do front matter e do teto, luz e profundidade convertidas,
    grafismo.tipo conhecido (tipo que ainda vai entrar com o gerador: AVISO). Implementação de referência:
    conferir_trecho em test_repertorio_v2.py; as duas andam juntas (test_repertorio_recursos.py)."""
    import jsonschema, acabamento, grafismos
    if not isinstance(trecho, dict) or not isinstance(trecho.get("direcao_criativa"), dict) or not isinstance(trecho.get("pagina"), dict) \
            or set(trecho) - {"direcao_criativa", "pagina"}:
        return ['o trecho é {"direcao_criativa": {...}, "pagina": {...}} e nada mais'], []
    erros, avisos = [], []
    rid, dc, pag = fm.get("id"), trecho["direcao_criativa"], trecho["pagina"]
    sch_kit = json.loads((AQUI.parent / "schema" / "mediakit.schema.json").read_text(encoding="utf-8"))
    v = jsonschema.Draft202012Validator(sch_kit["properties"]["direcao_criativa"])
    erros += [f"direcao_criativa/{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in v.iter_errors(dc)]
    erros += validar_exemplo(pag)
    falhas_ac, avisos_ac = acabamento.validar({"composicao": {"exemplo": pag}}, so_composicao=True)
    erros += [f for f in falhas_ac if not any(f in e for e in erros)]
    avisos += avisos_ac
    if rid not in [r.get("id") for r in dc.get("recursos") or [] if isinstance(r, dict)]:
        erros.append("o id do recurso não está em direcao_criativa.recursos")
    ac = pag.get("acabamento") if isinstance(pag.get("acabamento"), dict) else {}
    if rid not in (ac.get("recursos") or []):
        erros.append("o id do recurso não está em pagina.acabamento.recursos")
    els = [e for e in pag.get("elementos") or [] if isinstance(e, dict)]
    if rid not in [e.get("recurso") for e in els]:
        erros.append("nenhum elemento leva `recurso` com o id do recurso")
    it = fm.get("intensidade")
    if isinstance(it, list) and len(it) == 2 and all(str(x).isdigit() for x in it):
        lo, hi = (int(x) for x in it)
        teto = (dc.get("intensidade") or {}).get("teto", 3) if isinstance(dc.get("intensidade"), dict) else 3
        dec = ac.get("intensidade")
        if isinstance(dec, int) and (not lo <= dec <= hi or dec > teto):
            erros.append(f"intensidade da página {dec} fora de [{lo}, {hi}] (front matter) ou acima do teto {teto}")
    if fm.get("luz_direcao") is not None and ac.get("luz", "nenhuma") != LUZ_KIT.get(fm.get("luz_direcao"), "nenhuma"):
        erros.append(f"acabamento.luz `{ac.get('luz')}` não corresponde a luz_direcao `{fm.get('luz_direcao')}` "
                     f"(esq, dir e topo iguais; o resto vira nenhuma)")
    if ac.get("profundidade") and fm.get("profundidade") in PROF_KIT and ac["profundidade"] != PROF_KIT[fm["profundidade"]]:
        erros.append(f"acabamento.profundidade `{ac['profundidade']}` não corresponde a `{fm['profundidade']}` "
                     f"(deveria ser `{PROF_KIT[fm['profundidade']]}`)")
    for e in els:
        tipo = (e.get("grafismo") or {}).get("tipo") if isinstance(e.get("grafismo"), dict) else None
        if tipo is None or tipo in grafismos.TIPOS:
            continue
        if tipo in acabamento.TIPOS_A_ENTRAR:
            avisos.append(f"elemento `{e.get('id')}`: grafismo `{tipo}` depende do gerador (acabamento.TIPOS_A_ENTRAR)")
        else:
            erros.append(f"elemento `{e.get('id')}`: grafismo.tipo `{tipo}` desconhecido (grafismos.TIPOS)")
    return erros, avisos


# ---------------------------------------------------------------- recurso: .md, referências e índice
RE_RECORTE_MD = re.compile(r"recortes/[A-Za-z0-9._-]+\.(?:jpg|jpeg|png)")


def referencias_do_md(corpo):
    """Itens de `## Referências`: [{linha, referencia, paginas, arquivos, anti, legenda}]. Formato do briefing:
    `- <ref> p. 7, 12 (o que mostra; recorte recortes/<id>__<ref>-07.jpg, anotado: 1 ..., 2 ...)`."""
    out = []
    for titulo, linhas in secoes_do_md(corpo):
        if norm(titulo) != "referencias":
            continue
        for l in linhas:
            m = re.match(r"^\s*[-*]\s+(\S+)(.*)$", l)
            if not m:
                continue
            resto = m.group(2)
            pags = re.match(r"^\s*p(?:á|a)?g?s?\.?\s*([\d][\d ,e]*)", resto)
            paginas = [int(x) for x in re.findall(r"\d+", pags.group(1))] if pags else []
            par = re.search(r"\((.*)\)", resto)
            legenda = re.split(r"[;,]\s*recorte\s", par.group(1))[0].strip() if par else ""
            arquivos = [a for a in RE_RECORTE_MD.findall(l) if not re.search(r"--anotado\.\w+$", a)]
            out.append({"linha": l.strip(), "referencia": m.group(1).strip(",;"), "paginas": paginas, "anti": "antiexemplo" in norm(l),
                        "arquivos": list(dict.fromkeys(arquivos)), "legenda": legenda})
    return out


def manifestos_anotar(rep):
    """{arquivo: entrada} de todos os recortes/_anotar-<ref>.json (o que o `anotar` gravou: anotações em fração do recorte)."""
    out = {}
    for f in sorted((Path(rep) / "recortes").glob("_anotar-*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        for e in (d.get("recortes") or []) if isinstance(d, dict) else []:
            if isinstance(e, dict) and e.get("arquivo"):
                out[e["arquivo"]] = e
    return out


def _front_para_entrada(meta, rid):
    """O item de recursos[] que o front matter descreve (sem recortes e sem trecho). Listas viram listas (texto solto vira
    lista de um item), `intensidade` vira [int, int] e `uau`, int. Devolve (entrada, chaves fora do contrato)."""
    props = _defs()["recurso"]["properties"]
    e, fora = {"id": rid, "nome": meta.get("nome"), "arquivo": f"recursos/{rid}.md"}, []
    for k in props:
        if k in ("id", "nome", "arquivo", "recortes", "acabamento_exemplo") or k not in meta:
            continue
        v = meta[k]
        if k in LISTAS_FRONT or k == "intensidade":
            v = v if isinstance(v, list) else [x.strip() for x in str(v).split(",") if x.strip()]
        if k == "intensidade":
            v = [int(x) if str(x).isdigit() else x for x in v]
        elif k == "uau" and str(v).isdigit():
            v = int(v)
        e[k] = v
    fora = [k for k in meta if k not in props and k not in SO_NO_MD]
    if e.get("nome") is None:
        del e["nome"]
    return e, fora


def recurso_do_md(rep, caminho):
    """(entrada, erros, avisos) do .md de um recurso. `entrada` é o item de recursos[] que o .md descreve (o que o
    `indexar` grava e o `checar` compara com o índice); None quando o .md não tem front matter. Os erros são as FALHAS do
    briefing-redator-v2.md ("O que o validador vai cobrar") que o .md sozinho decide; os avisos, os AVISOS."""
    rep, caminho = Path(rep), Path(caminho)
    rid = caminho.stem
    texto = caminho.read_text(encoding="utf-8")
    erros, avisos = [], []
    for n, l in enumerate(texto.split("\n"), 1):
        if _tem_travessao(l):
            erros.append(f"travessão ou meia-risca na linha {n} (use ponto, vírgula, dois-pontos ou parênteses)")
    meta, corpo = ler_front_matter(texto)
    if meta is None:
        return None, erros + ["sem front matter (bloco YAML entre `---` no topo, briefing-redator-v2.md)"], avisos
    if meta.get("id") != rid:
        erros.append(f"o front matter diz id `{meta.get('id')}`; tem de ser igual ao nome do arquivo (`{rid}`)")
    entrada, fora = _front_para_entrada(meta, rid)
    if fora:
        erros.append(f"chave(s) fora do contrato no front matter: {', '.join(fora)}")
    obrig = [k for k in _defs()["recurso"]["required"] if k not in ("id", "arquivo") and k not in meta]
    if obrig:
        erros.append(f"faltam chaves no front matter: {', '.join(obrig)}")
    import jsonschema
    sch, reg = _registro()
    so_front = {k: v for k, v in entrada.items() if k not in ("recortes", "acabamento_exemplo")}
    vr = jsonschema.Draft7Validator({"$ref": f"{sch['$id']}#/definitions/recurso"}, registry=reg)
    for e in vr.iter_errors(so_front):
        if e.validator == "required":
            continue                                   # as chaves faltando já saíram acima, numa mensagem só
        erros.append(f"front matter `{'/'.join(map(str, e.absolute_path)) or rid}`: {e.message}")
    fam, dims = entrada.get("familia"), entrada.get("dimensoes") or []
    if fam and fam not in dims:
        erros.append(f"a familia `{fam}` precisa estar em dimensoes")
    it = entrada.get("intensidade")
    if isinstance(it, list) and len(it) == 2 and all(isinstance(x, int) for x in it) and it[0] > it[1]:
        erros.append(f"intensidade {it}: o mínimo passa do máximo")
    via, rota = entrada.get("producao"), entrada.get("rota")
    if via == "fora-do-pipeline" and entrada.get("reproduzivel") != "nao":
        erros.append("producao fora-do-pipeline pede reproduzivel nao")
    elif via in ROTA_DA_VIA and rota and ROTA_DA_VIA[via] != rota:
        erros.append(f"rota `{rota}` não corresponde à producao `{via}` (deveria ser `{ROTA_DA_VIA[via]}`)")
    if "uau" in dims and isinstance(entrada.get("uau"), int) and entrada["uau"] < 2:
        avisos.append(f"`uau` em dimensoes com nota {entrada['uau']} (a dimensão uau é só para nota 2 ou 3)")
    if entrada.get("reproduzivel") in ("parcial", "so-com-insumo-do-cliente") and not entrada.get("depende"):
        avisos.append(f"reproduzivel {entrada.get('reproduzivel')} sem `depende` (diga o que falta)")
    # seções: as 8 numeradas, depois Trecho de acabamento e Referências, nesta ordem e com estes títulos
    titulos = [norm(t) for t, _ in secoes_do_md(corpo) if t]
    esperados = [f"{k}. {s}" for k, s in enumerate(SECOES_RECURSO, 1)] + list(SECOES_RECURSO_FIM)
    validos = [norm(s) for s in esperados]
    for s in esperados:
        if norm(s) not in titulos:
            erros.append(f"falta a seção `## {s}` (título exato do briefing)")
    achados = [t for t in titulos if t in validos]
    if achados != [s for s in validos if s in achados]:
        erros.append("seções fora da ordem do briefing (1 a 8, Trecho de acabamento, Referências)")
    extras = [t for t, _ in secoes_do_md(corpo) if t and norm(t) not in validos]
    if extras:
        avisos.append(f"seção fora do roteiro: {', '.join(extras)}")
    # eixos de variação (tabela da seção 5)
    for titulo, linhas in secoes_do_md(corpo):
        if re.match(r"^5\.\s", titulo):
            vistos = {norm(_celulas(l)[0]).replace(" ", "-") for l in linhas if l.strip().startswith("|")}
            faltam = [x for x in EIXOS if x not in vistos]
            if faltam:
                avisos.append(f"faltam eixos na tabela da seção 5: {', '.join(faltam)}")
    # trecho de acabamento
    trecho, erro = trecho_de_acabamento(corpo)
    if erro:
        erros.append(f"trecho de acabamento: {erro}")
    elif trecho is None:
        erros.append("sem `## Trecho de acabamento` com bloco ```json")
    else:
        e2, a2 = conferir_trecho_acabamento(dict(entrada, id=rid), trecho)
        erros += [f"trecho de acabamento: {x}" for x in e2]
        avisos += [f"trecho de acabamento: {x}" for x in a2]
        entrada["acabamento_exemplo"] = trecho
    # comandos da seção 8
    for c in comandos_da_producao(corpo):
        ok, motivo = comando_existe(c)
        if not ok:
            erros.append(f"comando da seção 8 que não existe no pipeline: `{c}` ({motivo})")
    # referências e recortes
    refs = referencias_do_md(corpo)
    if not refs:
        erros.append("`## Referências` sem nenhuma linha `- <ref> p. N (...)`")
    man = manifestos_anotar(rep)
    recortes = []
    for r in refs:
        if not r["paginas"]:
            erros.append(f"linha de Referências sem página: `{r['linha'][:80]}`")
        for a in r["arquivos"]:
            m = re.fullmatch(rf"recortes/{re.escape(rid)}__{re.escape(r['referencia'])}-(\d{{2,}})(?:-[b-z])?\.(?:jpg|jpeg|png)", a)
            if not m or (r["paginas"] and int(m.group(1)) not in r["paginas"]):
                erros.append(f"recorte `{a}` fora do padrão de nome recortes/{rid}__{r['referencia']}-<página da linha>.jpg")
            x = dict(man.get(a) or {})
            item = {"arquivo": a, "referencia": x.get("referencia") or r["referencia"],
                    "pagina": x.get("pagina") if isinstance(x.get("pagina"), int) else (int(m.group(1)) if m else (r["paginas"] or [0])[0]),
                    "legenda": x.get("legenda") or r["legenda"] or r["linha"][:120]}
            if r["anti"] or x.get("anti"):
                item["anti"] = True
            anot = x.get("anotado") or re.sub(r"\.(jpg|jpeg|png)$", r"--anotado.\1", a)
            if x.get("anotado") or (rep / anot).is_file():
                item["anotado"] = anot
            if x.get("anotacoes"):
                item["anotacoes"] = x["anotacoes"]
            if a not in [y["arquivo"] for y in recortes]:
                recortes.append(item)
    entrada["recortes"] = recortes
    n = texto.count("\n") + (0 if texto.endswith("\n") else 1)
    if not LINHAS_RECURSO[0] <= n <= LINHAS_RECURSO[1]:
        avisos.append(f"o .md tem {n} linhas (o briefing pede {LINHAS_RECURSO[0]} a {LINHAS_RECURSO[1]})")
    return entrada, erros, avisos


def _gravar_indice(rep, indice):
    _gravar(Path(rep) / "indice.json", (json.dumps(indice, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))


def indexar(rep, escrever=False):
    """Monta recursos[] a partir de repertorio/recursos/*.md (o .md é a fonte) e diz o que muda no índice. Com `escrever`,
    grava o indice.json (versao 2 quando há recurso), mas só se o resultado valer no schema. Devolve
    {novos, alterados, removidos, problemas, escrito}. `problemas` são os .md sem front matter (ficam de fora)."""
    rep = Path(rep)
    indice = json.loads((rep / "indice.json").read_text(encoding="utf-8"))
    entradas, problemas = [], []
    for md in sorted((rep / "recursos").glob("*.md")) if (rep / "recursos").is_dir() else []:
        e, erros, _ = recurso_do_md(rep, md)
        if e is None:
            problemas.append(f"recursos/{md.name}: " + "; ".join(erros[:2])); continue
        entradas.append(e)
    antigos = {r.get("id"): r for r in indice.get("recursos") or [] if isinstance(r, dict)}
    novos_ids = [e["id"] for e in entradas]
    res = {"novos": [i for i in novos_ids if i not in antigos],
           "alterados": [e["id"] for e in entradas if e["id"] in antigos and antigos[e["id"]] != e],
           "removidos": sorted(i for i in antigos if i not in novos_ids), "problemas": problemas, "escrito": False, "erros_schema": []}
    novo = dict(indice)
    if entradas:
        novo["versao"] = 2
        novo["recursos"] = entradas
    else:
        novo.pop("recursos", None)
    res["erros_schema"] = validar_indice(sem_exemplos(novo))
    if escrever and not res["erros_schema"] and novo != indice:
        _gravar_indice(rep, novo)
        res["escrito"] = True
    return res


def _dhash(im):
    """Hash de diferença de 64 bits (9x8 em cinza): recortes iguais ou quase iguais dão o mesmo valor."""
    import numpy as np
    from PIL import Image
    g = np.asarray(im.convert("L").resize((9, 8), Image.LANCZOS), dtype=np.int16)
    return sum(1 << i for i in range(64) if g[i // 8, i % 8] > g[i // 8, i % 8 + 1])


def _distancia(a, b):
    return bin(int(a) ^ int(b)).count("1")


def _desvio_luminancia(im):
    import numpy as np
    return float(np.asarray(im.convert("L"), dtype=np.float32).std())


def de_pagina(recursos_voc, dimensoes=()):
    """O recurso é a página inteira (cena, tratamento, colagem, transição, textura, pattern, moldura, ou ritmo)?"""
    return bool(set(recursos_voc or ()) & set(RECURSOS_DE_PAGINA)) or "ritmo" in (dimensoes or ())


def conferir_vazio(area, desvio, de_pagina_inteira):
    """Avisos de recorte vazio: área acima de 85% da página num recurso de detalhe, abaixo de 2%, desvio de luminância
    abaixo de 4 (o recorte não mostra nada). O dHash repetido é conferido à parte, entre recortes."""
    out = []
    if area is not None and area > VAZIO_AREA_MAX and not de_pagina_inteira:
        out.append(f"recorte com {area:.0%} da página num recurso de detalhe (acima de {VAZIO_AREA_MAX:.0%}): enquadre o detalhe")
    if area is not None and area < VAZIO_AREA_MIN:
        out.append(f"recorte com {area:.1%} da página (abaixo de {VAZIO_AREA_MIN:.0%}): pequeno demais para ler")
    if desvio < VAZIO_DESVIO_MIN:
        out.append(f"desvio de luminância {desvio:.1f} (abaixo de {VAZIO_DESVIO_MIN:.0f}): o recorte parece vazio")
    return out


# ---------------------------------------------------------------- anotar e mapa
def _fonte(tam):
    from regua import fonte_ui
    return fonte_ui(tam)


def _caixa_px(c, w, h, ox=0, oy=0):
    return (ox + c[0] * w, oy + c[1] * h, ox + c[2] * w, oy + c[3] * h)


def _desenhar_caixa(d, x0, y0, x1, y1, W, H):
    """Caixa amarela de 3 px entre dois contornos escuros de 2 px, presa dentro da imagem."""
    x0, y0 = max(4, min(x0, W - 9)), max(4, min(y0, H - 9))
    x1, y1 = min(W - 5, max(x1, x0 + 4)), min(H - 5, max(y1, y0 + 4))
    d.rectangle([x0 - 4, y0 - 4, x1 + 4, y1 + 4], outline=ESCURO, width=2)
    d.rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 2], outline=AMARELO, width=3)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], outline=ESCURO, width=2)
    return x0, y0


def _desenhar_seta(d, x0, y0, x1, y1):
    """Seta de 4 px (com contorno escuro) de (x0, y0) até a ponta em (x1, y1)."""
    import math
    ang = math.atan2(y1 - y0, x1 - x0)
    comp, meia = 18, 9
    bx, by = x1 - comp * math.cos(ang), y1 - comp * math.sin(ang)
    d.line([(x0, y0), (bx, by)], fill=ESCURO, width=SETA + 4)
    d.line([(x0, y0), (bx, by)], fill=AMARELO, width=SETA)
    pts = [(x1, y1), (bx + meia * math.sin(ang), by - meia * math.cos(ang)), (bx - meia * math.sin(ang), by + meia * math.cos(ang))]
    d.polygon(pts, fill=AMARELO, outline=ESCURO)


def _desenhar_disco(d, cx, cy, n, W, H, diam=DISCO):
    r = diam // 2
    cx, cy = max(r + 1, min(cx, W - r - 2)), max(r + 1, min(cy, H - r - 2))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=AMARELO, outline=ESCURO, width=2)
    d.text((cx, cy + 1), str(n), fill=ESCURO, font=_fonte(17 if len(str(n)) == 1 else 14), anchor="mm")


def figura_anotada(im, anotacoes, cabecalho, largura_min=LARGURA_MIN_ANOTADO):
    """A figura anotada: `im` com as caixas (fração da própria imagem), setas e discos numerados, e uma faixa de legenda
    ABAIXO dela com o número e o rótulo (nunca texto sobre a peça). Imagem mais estreita que `largura_min` fica centrada
    numa tela dessa largura (a legenda precisa de espaço). Devolve a imagem nova."""
    from PIL import Image, ImageDraw
    w, h = im.size
    W = max(w, largura_min)
    ox = (W - w) // 2
    f_tx, f_cab = _fonte(16), _fonte(14)
    itens = sorted(anotacoes, key=lambda a: (a.get("n", 0)))
    linhas = []
    for a in itens:
        for k, t in enumerate(_quebrar(a.get("rotulo") or "", f_tx, W - 2 * 14 - 34, 3)):
            linhas.append((a.get("n") if k == 0 else None, t))
    m, lh, cab_h = 14, 24, 24
    faixa = m + cab_h + len(linhas) * lh + m
    F = Image.new("RGB", (W, h + faixa), FUNDO_LEGENDA)
    F.paste(im, (ox, 0))
    d = ImageDraw.Draw(F)
    for a in itens:
        c = a.get("caixa")
        if not (isinstance(c, (list, tuple)) and len(c) == 4):
            continue
        x0, y0, x1, y1 = _caixa_px(c, w, h, ox)
        _desenhar_caixa(d, x0, y0, x1, y1, ox + w, h)
    for a in itens:
        s = a.get("seta")
        if isinstance(s, (list, tuple)) and len(s) == 4:
            _desenhar_seta(d, *_caixa_px(s, w, h, ox))
    for a in itens:
        c = a.get("caixa")
        if isinstance(c, (list, tuple)) and len(c) == 4:
            x0, y0, _, _ = _caixa_px(c, w, h, ox)
            _desenhar_disco(d, x0, y0, a.get("n", "?"), ox + w, h)
    y = h + m
    d.text((m, y), cabecalho, fill=(150, 150, 158), font=f_cab)
    y += cab_h
    for n, t in linhas:
        if n is not None:
            _desenhar_disco(d, m + 12, y + 11, n, W, h + faixa, diam=22)
        d.text((m + 34, y + 2), t, fill=(236, 236, 238), font=f_tx)
        y += lh
    return F


def _candidatos(d, todos):
    """Os candidatos de uma análise: os `aceitos` de um <ref>.aceitos.json (gravar_veredito.py) e os de `padroes` com
    status aceito; com `todos`, também os sem veredito e os refutados."""
    out = [c for c in d.get("aceitos") or [] if isinstance(c, dict)]
    out += [c for c in d.get("padroes") or [] if isinstance(c, dict) and (todos or c.get("status") == "aceito")]
    if todos:
        out += [c for k in ("sem_veredito", "refutados") for c in d.get(k) or [] if isinstance(c, dict)]
    return out


def _fracao_no_recorte(c, px, W, H):
    """Caixa [x0, y0, x1, y1] em fração da PÁGINA levada à fração do recorte (o arquivo gravado, já com a folga), presa em
    0 a 1. Devolve (caixa, saiu): `saiu` diz se alguma ponta caiu fora do recorte."""
    cw, ch = px[2] - px[0], px[3] - px[1]
    v = [(c[0] * W - px[0]) / cw, (c[1] * H - px[1]) / ch, (c[2] * W - px[0]) / cw, (c[3] * H - px[1]) / ch]
    saiu = any(x < -1e-6 or x > 1 + 1e-6 for x in v)
    return [round(min(1.0, max(0.0, x)), 4) for x in v], saiu


def anotar(analise, saida, todos=False, bases=None):
    """Para cada candidato aceito (ou todos, com `todos`) de uma análise v2, grava o recorte limpo
    <id>__<ref>-<pp>.jpg (igual ao `recortar`: folga de 3%, lado maior até 900 px) e a versão --anotado.jpg (caixa amarela
    entre contornos escuros, seta de 4 px, disco numerado de 30 px; o rótulo na faixa de legenda abaixo da figura),
    converte as anotações de fração da página para fração do recorte e grava tudo em <saida>/_anotar-<ref>.json (o
    `indexar` lê dali). Confere recorte vazio (AVISO). Devolve {referencia, feitos, avisos, problemas, manifesto}."""
    from PIL import Image
    analise = Path(analise)
    d = json.loads(analise.read_text(encoding="utf-8"))
    if not isinstance(d, dict):
        raise SystemExit(f"repertorio: {analise} não é um objeto JSON de análise")
    ref = d.get("referencia") or d.get("id") or analise.name.split(".")[0]
    if not ID_SEGURO.fullmatch(str(ref)):
        raise SystemExit(f"referência `{ref}` fora do padrão a-z, 0-9 e hífen: vira nome de arquivo e não pode sair de --saida")
    saida = Path(saida); saida.mkdir(parents=True, exist_ok=True)
    bases = [Path(b) for b in (bases or [])] or [Path.cwd(), analise.parent, analise.parent.parent, analise.parent.parent.parent, AQUI.parent]
    f_man = saida / f"_anotar-{ref}.json"
    try:
        anteriores = {e["arquivo"]: e for e in json.loads(f_man.read_text(encoding="utf-8")).get("recortes", []) if isinstance(e, dict) and e.get("arquivo")}
    except (OSError, ValueError, AttributeError):
        anteriores = {}
    feitos, avisos, problemas, nomes = [], [], [], set()
    cands = _candidatos(d, todos)
    if not cands:
        problemas.append(f"nenhum candidato aceito em {analise.name} (sem veredito gravado ainda?); use --todos para anotar todos")
    hashes = {}
    for f in sorted(saida.glob("*.jpg")):
        if not f.name.endswith("--anotado.jpg") and not f.name.startswith("_"):
            try:
                with Image.open(f) as im0:
                    hashes[f"recortes/{f.name}"] = _dhash(im0)
            except OSError:
                pass
    for c in cands:
        pid = c.get("id_sugerido") or "sem-id"
        if not ID_SEGURO.fullmatch(str(pid)):
            problemas.append(f"id_sugerido `{pid}` fora do padrão a-z, 0-9 e hífen (vira nome de arquivo): candidato pulado"); continue
        cref = c.get("referencia") or ref
        if not ID_SEGURO.fullmatch(str(cref)):
            problemas.append(f"{pid}: referência `{cref}` fora do padrão: candidato pulado"); continue
        pagina_inteira = de_pagina(c.get("recurso"), c.get("dimensoes"))
        for ex in c.get("exemplos") or []:
            onde = f"{pid} ({ex.get('imagem')})"
            box = ex.get("recorte")
            if not (isinstance(box, (list, tuple)) and len(box) == 4 and all(isinstance(v, (int, float)) for v in box)
                    and 0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
                problemas.append(f"{onde}: recorte inválido {box} (esperado [x0, y0, x1, y1] em fração, com x0 < x1 e y0 < y1)"); continue
            arq = _resolver_imagem(ex.get("imagem") or "", bases)
            if arq is None:
                problemas.append(f"{onde}: imagem não encontrada (use --base-imagens)"); continue
            im = Image.open(arq).convert("RGB"); W, H = im.size
            px = (round(max(0.0, box[0] - FOLGA) * W), round(max(0.0, box[1] - FOLGA) * H),
                  round(min(1.0, box[2] + FOLGA) * W), round(min(1.0, box[3] + FOLGA) * H))
            corte = im.crop(px)
            if max(corte.size) > LADO_MAX:
                fator = LADO_MAX / max(corte.size)
                corte = corte.resize((max(1, round(corte.width * fator)), max(1, round(corte.height * fator))), Image.LANCZOS)
            pag = ex.get("pagina")
            base = f"{pid}__{cref}-{pag:02d}" if isinstance(pag, int) else f"{pid}__{cref}-{re.sub(r'[^a-z0-9]+', '', norm(pag)) or 'x'}"
            origem = {"origem": analise.name, "candidato": pid, "pagina": pag, "recorte_analise": [round(float(v), 4) for v in box]}
            nome, k = f"{base}.jpg", 2
            while nome in nomes or (f"recortes/{nome}" in anteriores and
                                    {x: anteriores[f"recortes/{nome}"].get(x) for x in origem} != origem):
                nome = f"{base}-{chr(96 + k)}.jpg"; k += 1           # outro exemplo na mesma página: -b, -c (nunca apaga o de outra origem)
            nomes.add(nome)
            rel = f"recortes/{nome}"
            anot_rel = rel[:-4] + "--anotado.jpg"
            anotacoes, aviso_local = [], []
            for a in ex.get("anotacoes") or []:
                if not isinstance(a, dict) or not isinstance(a.get("caixa"), (list, tuple)) or len(a["caixa"]) != 4:
                    aviso_local.append(f"anotação {a.get('n') if isinstance(a, dict) else '?'} sem caixa: pulada"); continue
                cx, saiu = _fracao_no_recorte(a["caixa"], px, W, H)
                if saiu:
                    aviso_local.append(f"anotação {a.get('n')} sai do recorte: cortada na borda")
                nova = {"n": a.get("n"), "caixa": cx, "rotulo": str(a.get("rotulo") or "")[:90]}
                if isinstance(a.get("seta"), (list, tuple)) and len(a["seta"]) == 4:
                    nova["seta"], saiu = _fracao_no_recorte(a["seta"], px, W, H)
                    if saiu:
                        aviso_local.append(f"seta da anotação {a.get('n')} sai do recorte: cortada na borda")
                anotacoes.append(nova)
            area = (px[2] - px[0]) * (px[3] - px[1]) / float(W * H)
            aviso_local += conferir_vazio(area, _desvio_luminancia(corte), pagina_inteira)
            h = _dhash(corte)
            iguais = sorted(o for o, hh in hashes.items() if o != rel and _distancia(h, hh) <= DHASH_IGUAL)
            if iguais:
                aviso_local.append(f"recorte repetido (dHash igual ao de {', '.join(iguais[:3])})")
            hashes[rel] = h
            corte.save(saida / nome, "JPEG", quality=QUALIDADE, optimize=True)
            cab = f"{cref} p. {pag} · {pid}" + (" · NÃO FAZER" if ex.get("anti") else "")
            figura_anotada(corte, anotacoes, cab).save(saida / Path(anot_rel).name, "JPEG", quality=QUALIDADE_ANOTADO, optimize=True)
            ent = {"arquivo": rel, "anotado": anot_rel, "referencia": cref, "pagina": pag, "legenda": ex.get("o_que_mostra") or "",
                   **({"anti": True} if ex.get("anti") else {}), **{k: v for k, v in origem.items() if k != "pagina"},
                   "recorte_pagina": [round(px[0] / W, 4), round(px[1] / H, 4), round(px[2] / W, 4), round(px[3] / H, 4)],
                   "de_pagina": pagina_inteira, "tamanho": list(corte.size), "dhash": f"{h:016x}", "anotacoes": anotacoes}
            anteriores[rel] = ent
            feitos.append(dict(ent, caminho=str(saida / nome)))
            avisos += [f"{rel}: {x}" for x in aviso_local]
    if feitos:
        _gravar(f_man, (json.dumps({"referencia": ref, "recortes": [anteriores[k] for k in sorted(anteriores)]},
                                   ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    return {"referencia": ref, "feitos": feitos, "avisos": avisos, "problemas": problemas, "manifesto": str(f_man) if feitos else None}


def _imagem_da_pagina(rep, ref, pagina):
    """O arquivo da página `pagina` da referência: capturas/<ref>/NN.jpg ou, num kit da régua, o caminho do manifesto."""
    rep = Path(rep)
    c = pasta_captura(rep, ref) / f"{int(pagina):02d}.jpg"
    if c.is_file():
        return c
    man = ler_manifesto(rep, ref) or {}
    for p in man.get("paginas") or []:
        if p.get("n") == int(pagina) and p.get("arquivo"):
            alvo = (rep.resolve().parent / p["arquivo"]).resolve()
            if rep.resolve().parent in alvo.parents and alvo.is_file():
                return alvo
    return None


def mapa(rep, ref, pagina, analises=(), saida=None):
    """A página inteira anotada (1200 px): uma caixa numerada por recorte que o `anotar` tirou dela (recortes/_anotar-<ref>.json)
    e por exemplo das análises dadas, com a legenda abaixo. Grava repertorio/mapas/<ref>-<pp>.jpg (ou `saida`)."""
    from PIL import Image
    rep = Path(rep)
    if not ID_SEGURO.fullmatch(str(ref)):
        raise SystemExit(f"referência `{ref}` fora do padrão a-z, 0-9 e hífen")
    arq = _imagem_da_pagina(rep, ref, pagina)
    if arq is None:
        raise SystemExit(f"repertorio: página {pagina} de `{ref}` não encontrada em capturas/{ref}/ nem no manifesto")
    itens, vistos = [], set()
    man = rep / "recortes" / f"_anotar-{ref}.json"
    if man.is_file():
        for e in json.loads(man.read_text(encoding="utf-8")).get("recortes") or []:
            if e.get("pagina") == int(pagina) and isinstance(e.get("recorte_pagina"), list):
                rid = Path(e["arquivo"]).name.split("__")[0]
                itens.append((rid, e["recorte_pagina"], e.get("legenda") or "", bool(e.get("anti"))))
    for a in analises or ():
        d = json.loads(Path(a).read_text(encoding="utf-8"))
        for c in _candidatos(d, True):
            for ex in c.get("exemplos") or []:
                img = str(ex.get("imagem") or "")
                if ex.get("pagina") == int(pagina) and (f"/{ref}/" in img or f"/{ref}-" in img):
                    itens.append((c.get("id_sugerido") or "?", ex.get("recorte"), ex.get("o_que_mostra") or "", bool(ex.get("anti"))))
    unicos = []
    for rid, caixa, leg, anti in itens:
        chave = (rid, tuple(round(float(x), 3) for x in caixa or ()))
        if chave in vistos or not (isinstance(caixa, (list, tuple)) and len(caixa) == 4):
            continue
        vistos.add(chave); unicos.append((rid, caixa, leg, anti))
    if not unicos:
        raise SystemExit(f"repertorio: nada a marcar na p. {pagina} de `{ref}` (rode `anotar` antes, ou passe --analise)")
    im = Image.open(arq).convert("RGB")
    im = im.resize((LARGURA_MAPA, max(1, round(im.height * LARGURA_MAPA / im.width))), Image.LANCZOS)
    anot = [{"n": k, "caixa": [float(x) for x in caixa], "rotulo": f"{rid}{' (NÃO FAZER)' if anti else ''}: {leg}"[:200]}
            for k, (rid, caixa, leg, anti) in enumerate(unicos, 1)]
    destino = Path(saida) if saida else rep / "mapas" / f"{ref}-{int(pagina):02d}.jpg"
    destino.parent.mkdir(parents=True, exist_ok=True)
    figura_anotada(im, anot, f"{ref} p. {pagina}: {len(anot)} recorte(s)", largura_min=LARGURA_MAPA).save(destino, "JPEG", quality=QUALIDADE_ANOTADO, optimize=True)
    return destino, len(anot)


# ---------------------------------------------------------------- checar v2
def checar_v2(rep, indice, F, A, usados, ids_ref, padroes, refs):
    """As conferências da camada de acabamento (recursos[] e os campos v2), somadas ao `checar` de antes. Índice v1 sem
    nenhum campo novo não gera linha nenhuma aqui."""
    from PIL import Image
    rep = Path(rep)
    recursos = [r for r in indice.get("recursos") or [] if isinstance(r, dict)]
    vistos, citadas, hashes = set(), set(), {}
    man = manifestos_anotar(rep) if recursos else {}
    for r in recursos:
        rid = r.get("id", "?")
        if rid in vistos:
            F(f"recurso `{rid}` repetido no índice (os ids têm de ser únicos)")
        vistos.add(rid)
        if _tem_travessao(json.dumps(r, ensure_ascii=False)):
            F(f"recurso `{rid}`: travessão ou meia-risca no índice")
        arq = r.get("arquivo")
        rcs = [x for x in r.get("recortes") or [] if isinstance(x, dict)]
        for x in rcs:
            usados.add(x.get("arquivo")); usados.add(x.get("anotado"))
        if arq and Path(arq).stem != rid:
            F(f"recurso `{rid}`: o arquivo `{arq}` deveria se chamar `{rid}.md`")
        if not arq or not (rep / arq).is_file():
            F(f"recurso `{rid}`: `{arq}` não existe")
        else:
            entrada, erros, avisos = recurso_do_md(rep, rep / arq)
            for e in erros:
                F(f"recurso `{rid}`: {e}")
            for a in avisos:
                A(f"recurso `{rid}`: {a}")
            if entrada is not None:
                for k in sorted(set(entrada) | set(r), key=str):
                    if k == "recortes":
                        a_md = [x.get("arquivo") for x in entrada.get("recortes") or []]
                        a_ix = [x.get("arquivo") for x in rcs]
                        if sorted(a_md) != sorted(a_ix):
                            F(f"recurso `{rid}`: os recortes de `## Referências` ({', '.join(a_md) or 'nenhum'}) não são os do índice "
                              f"({', '.join(a_ix) or 'nenhum'}): rode `repertorio.py indexar --escrever`")
                        elif entrada.get("recortes") != rcs:
                            F(f"recurso `{rid}`: legenda, anotado ou anotações dos recortes diferentes entre o .md (com o "
                              f"_anotar) e o índice: rode `repertorio.py indexar --escrever`")
                    elif entrada.get(k) != r.get(k):
                        F(f"recurso `{rid}`: `{k}` do .md ({json.dumps(entrada.get(k), ensure_ascii=False)[:120]}) é diferente do "
                          f"índice ({json.dumps(r.get(k), ensure_ascii=False)[:120]}); o .md é a fonte: rode `repertorio.py indexar --escrever`")
        if not [x for x in rcs if not x.get("anti")]:
            F(f"recurso `{rid}` sem recorte (o html, a folha e a consulta ficam sem imagem)")
        for x in rcs:
            a = x.get("arquivo")
            if a and not (rep / a).is_file():
                F(f"recurso `{rid}`: recorte `{a}` não existe")
            if x.get("referencia") not in ids_ref:
                F(f"recurso `{rid}`: o recorte `{a}` cita a referência `{x.get('referencia')}`, que não está em referencias[]")
            citadas.add(x.get("referencia"))
            if not x.get("anotado"):
                F(f"recurso `{rid}`: recorte `{a}` sem versão anotada (rode `repertorio.py anotar`)")
            elif not (rep / x["anotado"]).is_file():
                F(f"recurso `{rid}`: a versão anotada `{x['anotado']}` não existe")
            if not x.get("anotacoes"):
                F(f"recurso `{rid}`: recorte `{a}` sem anotações registradas (rode `repertorio.py anotar`)")
            for an in x.get("anotacoes") or []:
                c, s = an.get("caixa"), an.get("seta")
                if not (isinstance(c, list) and len(c) == 4 and 0 <= c[0] < c[2] <= 1 and 0 <= c[1] < c[3] <= 1):
                    F(f"recurso `{rid}`: recorte `{a}`, anotação {an.get('n')} com caixa fora do recorte ou invertida: {c}")
                if s is not None and not (isinstance(s, list) and len(s) == 4 and all(0 <= v <= 1 for v in s)):
                    F(f"recurso `{rid}`: recorte `{a}`, anotação {an.get('n')} com seta fora do recorte: {s}")
            if a and (rep / a).is_file():
                with Image.open(rep / a) as im:
                    m = man.get(a) or {}
                    area = None
                    rp = m.get("recorte_pagina")
                    if isinstance(rp, list) and len(rp) == 4:
                        area = (rp[2] - rp[0]) * (rp[3] - rp[1])
                    for v in conferir_vazio(area, _desvio_luminancia(im), de_pagina(r.get("recurso"), r.get("dimensoes"))):
                        A(f"recurso `{rid}`: recorte `{a}`: {v}")
                    hashes[a] = _dhash(im)
        if len({x.get("referencia") for x in rcs if not x.get("anti")}) == 1:
            A(f"recurso `{rid}` com uma referência só (o briefing pede 2 ou mais; diga por quê ou acrescente)")
        pares = [(x.get("referencia"), x.get("pagina")) for x in rcs]
        for p in padroes:
            pp = {(y.get("referencia"), y.get("pagina")) for y in p.get("recortes") or [] if isinstance(y, dict)}
            k = sum(1 for q in pares if q in pp)
            if pares and k * 2 > len(pares):
                A(f"recurso `{rid}` divide {k} de {len(pares)} recortes (mesma referência e página) com o padrão `{p.get('id')}`: "
                  f"é extensão do padrão, não recurso novo?")
    lista = sorted(hashes.items())
    for i, (a, h) in enumerate(lista):
        for b, hb in lista[i + 1:]:
            if _distancia(h, hb) <= DHASH_IGUAL:
                A(f"recortes repetidos (dHash): `{a}` e `{b}`")
    pasta = rep / "recursos"
    if pasta.is_dir():
        for md in sorted(pasta.glob("*.md")):
            if md.stem not in vistos:
                A(f"`recursos/{md.name}` não está no índice (rode `repertorio.py indexar --escrever`)")
    for ref in refs:
        v2 = any(k in ref for k in ("camada_v2", "captura", "uau_paginas", "serie"))
        if (v2 or ref.get("id") in citadas) and not ref.get("serie"):
            A(f"referência `{ref.get('id')}` do estudo v2 sem `serie` (constantes, variáveis, por tipo e ritmo)")
        cap = ref.get("captura")
        if isinstance(cap, dict) and cap.get("manifesto") and not (rep / cap["manifesto"]).is_file():
            F(f"referência `{ref.get('id')}`: o manifesto `{cap['manifesto']}` não existe")
    for p in padroes:
        for x in p.get("recortes") or []:
            if isinstance(x, dict) and x.get("anotado"):
                usados.add(x["anotado"])
                if not (rep / x["anotado"]).is_file():
                    F(f"padrão `{p.get('id')}`: a versão anotada `{x['anotado']}` não existe")


# ---------------------------------------------------------------- buscar v2, série e cobertura
FILTROS_RECURSO = (     # (opção, campo do recurso, peso, rótulo, vocabulário do schema)
    ("dimensao", "dimensoes", 2, "dimensão", "dimensao"),
    ("recurso", "recurso", 2, "recurso", "recurso"),
    ("material", "material", 1, "material", "material"),
    ("luz", "luz", 1, "luz", "luz"),
    ("profundidade", "profundidade", 1, "profundidade", "profundidade"),
    ("intensidade", "intensidade", 1, "intensidade", "intensidade"),
    ("continuidade", "continuidade", 1, "continuidade", "continuidade"),
    ("tratamento", "tratamento_imagem", 1, "tratamento", "tratamento_imagem"),
    ("tipografia", "tipografia", 1, "tipografia", "tipografia"),
    ("borda", "borda", 1, "borda", "borda"),
    ("via", "producao", 1, "via", "via"),
)


def _casa(valor, pedido, campo):
    if campo == "intensidade":
        return isinstance(valor, list) and len(valor) == 2 and str(pedido).isdigit() and valor[0] <= int(pedido) <= valor[1]
    return pedido in valor if isinstance(valor, list) else valor == pedido


def buscar_recursos(indice, pagina=None, problema=None, funcoes=(), tons=(), rota=None, filtros=None, sem_risco_pdf=False,
                    uau_min=None, familia=None, n=5):
    """Recursos do índice ranqueados: página +3, dimensão +2, recurso +2, o resto +1 (função, tom, rota, material, luz,
    profundidade, intensidade, continuidade, tratamento, tipografia, borda, via) e +1 por palavra do --problema no efeito e
    no nome. `sem_risco_pdf` (risco_pdf nenhum), `uau_min` e `familia` cortam. Havendo critério, recurso sem casamento
    fica de fora. Nota decrescente, empate pelo id. `pagina` aceita um tipo ou uma lista de tipos."""
    filtros = {k: [norm(x) for x in v] for k, v in (filtros or {}).items() if v}
    paginas = [pagina] if isinstance(pagina, str) or pagina is None else list(pagina)
    pedidas = [t for p in paginas if p for t in _paginas_pedidas(p)]
    funcoes, tons = [norm(x) for x in funcoes], [norm(x) for x in tons]
    rota = norm(rota) if rota else None
    palavras = sorted(_radicais(problema)) if problema else []
    criterio = bool(pedidas or funcoes or tons or rota or palavras or filtros)
    out = []
    for r in indice.get("recursos") or []:
        if sem_risco_pdf and r.get("risco_pdf") != "nenhum":
            continue
        if uau_min is not None and not (isinstance(r.get("uau"), int) and r["uau"] >= uau_min):
            continue
        if familia and r.get("familia") != familia:
            continue
        nota, razoes = 0, []
        casou = [t for t in dict.fromkeys(pedidas) if t in r.get("tipo_pagina", [])]
        if casou:
            nota += 3; razoes.append(f"página {', '.join(casou)}")
        for chave, campo, peso, rotulo, _ in FILTROS_RECURSO:
            for v in filtros.get(chave) or []:
                if _casa(r.get(campo), v, campo):
                    nota += peso; razoes.append(f"{rotulo} {v}")
        for rotulo, campo, pedido in (("função", "funcao", funcoes), ("tom", "tom", tons)):
            for v in pedido:
                if v in r.get(campo, []):
                    nota += 1; razoes.append(f"{rotulo} {v}")
        if rota and r.get("rota") == rota:
            nota += 1; razoes.append(f"rota {rota}")
        if palavras:
            no_efeito = [w for w in palavras if w in _radicais(r.get("efeito", ""))]
            no_nome = [w for w in palavras if w in _radicais(r.get("nome", ""))]
            if no_efeito:
                nota += len(no_efeito); razoes.append("palavras no efeito: " + ", ".join(no_efeito))
            if no_nome:
                nota += len(no_nome); razoes.append("palavras no nome: " + ", ".join(no_nome))
        if criterio and nota == 0:
            continue
        out.append({"nota": nota, "razoes": razoes or ["sem critério"], "recurso": r, "entidade": "recurso"})
    out.sort(key=lambda x: (-x["nota"], x["recurso"]["id"]))
    out = out[:n] if n else out
    for k, x in enumerate(out, 1):
        x["n"] = k
    return out


def buscar_todos(indice, pagina=None, problema=None, funcoes=(), relacoes=(), rota=None, tons=(), filtros=None,
                 sem_risco_pdf=False, uau_min=None, n=5):
    """Padrões e recursos numa lista só, pela mesma nota (empate: id, depois padrão antes de recurso). Os cortes que só o
    recurso declara (sem risco no PDF, uau mínimo) deixam os padrões de fora; critério que só um dos dois tem (relação no
    padrão; material, luz, via e os outros filtros no recurso) não traz o outro inteiro como "sem critério"."""
    filtros = {k: v for k, v in (filtros or {}).items() if v}
    dims = filtros.get("dimensao") or ()
    comum = bool(pagina or problema or funcoes or tons or rota)
    so_rec = set(filtros) - {"dimensao"}
    pad = []
    if not (sem_risco_pdf or uau_min is not None) and (comum or relacoes or dims or not so_rec):
        pad = [dict(x, entidade="padrao") for x in buscar(indice, pagina, problema, funcoes, relacoes, rota, tons, n=0, dimensoes=dims)]
    rec = []
    if comum or filtros or not relacoes:
        rec = buscar_recursos(indice, pagina, problema, funcoes, tons, rota, filtros, sem_risco_pdf, uau_min, n=0)
    tudo = pad + rec
    tudo.sort(key=lambda x: (-x["nota"], (x.get("padrao") or x.get("recurso"))["id"], x["entidade"] != "padrao"))
    tudo = tudo[:n] if n else tudo
    for k, x in enumerate(tudo, 1):
        x["n"] = k
    return tudo


def serie(rep, ref):
    """A série de uma referência: do índice (referencias[].serie, v2) ou, sem ela, das análises em estudo/analise-v2/.
    Devolve [{origem, serie, uau_paginas}] (vazia quando não há série)."""
    rep = Path(rep)
    indice = carregar(rep)
    r = next((x for x in indice.get("referencias") or [] if x.get("id") == ref), None)
    if r and r.get("serie"):
        return [{"origem": "indice.json", "serie": r["serie"], "uau_paginas": r.get("uau_paginas") or [], "nome": r.get("nome")}]
    out = []
    pasta = rep / "estudo" / "analise-v2"
    if ID_SEGURO.fullmatch(str(ref)) and pasta.is_dir():
        for f in sorted(pasta.glob(f"{ref}*.json")):
            if not (f.name == f"{ref}.json" or f.name.startswith(f"{ref}.")):
                continue
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
            except ValueError:
                continue
            if isinstance(d, dict) and isinstance(d.get("serie"), dict):
                out.append({"origem": f"estudo/analise-v2/{f.name}", "serie": d["serie"], "uau_paginas": d.get("uau_paginas") or [],
                            "nome": ref})
    return out


def imprimir_serie(ref, itens):
    if not itens:
        print(f"{ref}: sem série (nem no índice, nem nas análises de estudo/analise-v2/)")
        return
    for it in itens:
        s = it["serie"]
        print(f"{ref}: série ({it['origem']})")
        print("constantes:")
        for x in s.get("constantes") or []:
            print(f"  - {x}")
        print("variáveis:")
        for x in s.get("variaveis") or []:
            print(f"  - {x}")
        print("por tipo de página:")
        for t, x in sorted((s.get("por_tipo") or {}).items()):
            print(f"  {t}: {x}")
        rit = s.get("ritmo") or {}
        pags = sorted((rit.get("paginas") or {}).items(), key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else 0)
        print(f"ritmo: {rit.get('padrao', '?')}")
        if pags:
            print("  " + " · ".join(f"{int(k):02d} {v}" for k, v in pags))
        if it["uau_paginas"]:
            print("páginas que param o olho: " + "; ".join(
                f"p. {u.get('pagina')} nota {u.get('nota')} ({', '.join(u.get('gatilhos') or []) or 'sem gatilho'})"
                + (", da foto" if u.get("depende_de") == "foto" else "") for u in it["uau_paginas"]))
        print()


def cobertura(indice):
    """Matriz dimensões x recursos x referências: para cada uma das 11 dimensões, os recursos que a tocam, as referências
    dos recortes deles e os padrões v2 que a declaram; `rala` quando tem menos de 3 recursos ou de 3 referências."""
    recursos = [r for r in indice.get("recursos") or [] if isinstance(r, dict)]
    padroes = [p for p in indice.get("padroes") or [] if isinstance(p, dict)]
    linhas = []
    for dim in voc("dimensao"):
        rs = sorted(r["id"] for r in recursos if dim in (r.get("dimensoes") or []))
        refs = sorted({x.get("referencia") for r in recursos if dim in (r.get("dimensoes") or []) for x in r.get("recortes") or []
                       if isinstance(x, dict) and not x.get("anti") and x.get("referencia")})
        ps = sorted(p["id"] for p in padroes if dim in (p.get("dimensoes") or []))
        linhas.append({"dimensao": dim, "recursos": rs, "referencias": refs, "padroes": ps,
                       "rala": len(rs) < MIN_COBERTURA or len(refs) < MIN_COBERTURA})
    return {"linhas": linhas, "ralas": [l["dimensao"] for l in linhas if l["rala"]], "recursos": len(recursos), "minimo": MIN_COBERTURA}


def imprimir_cobertura(c):
    print(f"{'dimensão':<24} {'recursos':>8} {'referências':>11} {'padrões':>7}  recursos")
    for l in c["linhas"]:
        print(f"{l['dimensao']:<24} {len(l['recursos']):>8} {len(l['referencias']):>11} {len(l['padroes']):>7}  "
              f"{', '.join(l['recursos']) or '-'}{'   RALA' if l['rala'] else ''}")
    print(f"\n{c['recursos']} recurso(s); ralas (menos de {c['minimo']} recursos ou de {c['minimo']} referências): "
          f"{', '.join(c['ralas']) or 'nenhuma'}")


# ---------------------------------------------------------------- consultar (etapa 3b da skill)
def ler_leitura(pasta):
    """(fonte, linhas): até 4 linhas da seção `## Leitura` do direcao-criativa.md; sem esse arquivo, a seção Leitura do
    direcao-de-arte.md ou, sem ela, as 4 primeiras linhas de texto dele. (None, []) quando nenhum dos dois existe."""
    for nome in ("direcao-criativa.md", "direcao-de-arte.md"):
        f = Path(pasta) / nome
        if not f.is_file():
            continue
        _, corpo = ler_front_matter(f.read_text(encoding="utf-8"))
        secs = secoes_do_md(corpo)
        alvo = next((ls for t, ls in secs if norm(re.sub(r"^[\d.\s]+", "", t)).startswith("leitura")), None)
        fonte = f"{nome} (seção Leitura)" if alvo is not None else f"{nome} (sem seção Leitura: primeiras linhas de texto)"
        if alvo is None:
            alvo = [l for _, ls in secs for l in ls]
        linhas = []
        for l in alvo:
            t = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", l).strip()
            if t and not t.startswith(("#", "```", "|", ">", "---")):
                linhas.append(t)
        return fonte, linhas[:4]
    return None, []


def tipos_do_kit(k):
    """Tipos de página do kit: `paginas` (texto ou {tipo}) ou, sem ela, os rótulos de `composicao` (o tipo antes do `:`;
    `vertical:capa` vale capa). `ativo` vale ativo_painel e ativo_topo."""
    brutos = []
    for p in k.get("paginas") or []:
        t = p if isinstance(p, str) else (p.get("tipo") if isinstance(p, dict) else None)
        if t:
            brutos.append(t)
    if not brutos:
        for c in (k.get("composicao") or {}):
            if str(c).startswith("_"):
                continue
            partes = str(c).split(":")
            brutos.append(partes[1] if partes[0] == "vertical" and len(partes) > 1 else partes[0])
    out = []
    for b in brutos:
        for t in _paginas_pedidas(b):
            if t not in out:
                out.append(t)
    return out


def recursos_recentes(k, pasta, historico=None):
    """{id ou referência: kit} dos recursos dos 3 últimos kits de OUTRO cliente no historico-kits.json (a mesma conta do
    qa_conjunto.checar_historico, que avisa da repetição sem `porque_repete`)."""
    import biblioteca
    try:
        hist = json.loads(Path(historico or HISTORICO_KITS).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}, []
    if isinstance(hist, dict):
        hist = hist.get("kits", [])
    nome = ((k.get("evento") or {}).get("nome") or "").strip().lower() if isinstance(k.get("evento"), dict) else ""
    cliente = biblioteca.cliente_do_kit(k, pasta)
    proprio = lambda h: bool(nome) and nome in str(h.get("evento") or h.get("nome") or "").lower()  # noqa: E731
    outros = [h for h in hist if isinstance(h, dict) and not proprio(h) and not biblioteca.mesmo_cliente(h.get("cliente"), cliente)]
    if outros and all(h.get("data") for h in outros):
        outros = sorted(outros, key=lambda h: h["data"])
    rec = {}
    for h in outros[-3:]:
        for x in h.get("recursos") or []:
            for chave in ([x] if isinstance(x, str) else [x.get("id"), x.get("referencia")] if isinstance(x, dict) else []):
                if chave:
                    rec[chave] = h.get("id") or h.get("kit") or "?"
    return rec, [h.get("id") or h.get("kit") for h in outros[-3:]]


def consultar(pasta, rep=None, historico=None):
    """A consulta ao repertório da etapa 3b: lê a leitura da direção (ler_leitura), os tipos de página do mediakit.json e o
    histórico; busca os recursos de cada uma das 8 famílias (página +3, tom +1, palavra da leitura no efeito ou no nome +1;
    recurso de um dos 3 últimos kits de outro cliente perde 2) e grava na pasta do kit `consulta-repertorio.json`
    ({consultas, ids, indice_sha256, data, ...}: o qa_conjunto confere o sha256 do índice) e `mood/consulta-recursos.png`
    (os recortes anotados dos candidatos). Devolve o dicionário gravado."""
    pasta, rep = Path(pasta), Path(rep or RAIZ)
    f = pasta / "mediakit.json"
    if not f.is_file():
        raise SystemExit(f"repertorio: {f} não existe (passe a pasta do kit)")
    try:
        k = json.loads(f.read_text(encoding="utf-8"))
    except ValueError as e:
        raise SystemExit(f"repertorio: {f} não é JSON válido ({e})")
    indice = carregar(rep)
    bruto = (rep / "indice.json").read_bytes()
    fonte, linhas = ler_leitura(pasta)
    texto = " ".join(linhas)
    tons = [t for t in TONS if re.search(rf"\b{t}\b", norm(texto))]
    tipos = tipos_do_kit(k)
    recentes, kits_vistos = recursos_recentes(k, pasta, historico)
    consultas, ids = [], []
    for fam in voc("familia"):
        res = buscar_recursos(indice, tipos, texto, (), tons, None, None, familia=fam, n=0)
        resultados = []
        for x in res:
            r = x["recurso"]
            kit = recentes.get(r["id"]) or next((recentes[y.get("referencia")] for y in r.get("recortes") or [] if y.get("referencia") in recentes), None)
            nota, razoes = x["nota"], list(x["razoes"])
            if kit:
                nota -= PENA_RECENTE; razoes.append(f"usado no kit {kit} (um dos 3 últimos de outro cliente): -{PENA_RECENTE}")
            resultados.append({"id": r["id"], "nome": r.get("nome"), "nota": nota, "razoes": razoes, "recente": kit,
                               "uau": r.get("uau"), "risco_pdf": r.get("risco_pdf")})
        resultados.sort(key=lambda y: (-y["nota"], y["id"]))
        consultas.append({"familia": fam, "criterios": {"tipos_pagina": tipos, "tons": tons, "leitura": bool(linhas)},
                          "resultados": resultados})
        for y in resultados[:POR_FAMILIA]:
            if y["id"] not in ids:
                ids.append(y["id"])
    reg = {"kit": (k.get("evento") or {}).get("nome") if isinstance(k.get("evento"), dict) else k.get("kit"),
           "data": agora(), "indice_sha256": hashlib.sha256(bruto).hexdigest(), "indice_versao": indice.get("versao"),
           "leitura": {"fonte": fonte, "linhas": linhas}, "tipos_pagina": tipos, "tons": tons,
           "historico": {"kits_comparados": kits_vistos, "recursos_recentes": dict(sorted(recentes.items()))},
           "consultas": consultas, "ids": ids, "folha": CONSULTA_FOLHA}
    if not indice.get("recursos"):
        reg["aviso"] = "o índice não tem recursos (versão 1): a consulta saiu vazia"
    _gravar(pasta / CONSULTA_ARQ, (json.dumps(reg, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    por_id = {r["id"]: r for r in indice.get("recursos") or []}
    cartoes = []
    for i in ids:
        r = por_id[i]
        x = next((y for y in r.get("recortes") or [] if not y.get("anti")), None)
        img = None
        if x:
            img = rep / x["anotado"] if x.get("anotado") and (rep / x["anotado"]).is_file() else rep / x["arquivo"]
        cartoes.append({"imagem": img, "id": i, "legenda": r.get("efeito", ""), "anti": False,
                        "rodape": f"{r.get('familia')} · uau {r.get('uau')} · PDF {r.get('risco_pdf')}"})
    titulo = f"consulta ao repertório: {reg['kit'] or pasta.name} ({len(ids)} recurso(s))" if ids else \
        f"consulta ao repertório: {reg['kit'] or pasta.name}: nenhum recurso (índice sem recursos ou nada casou)"
    folha_de_cartoes(cartoes, pasta / CONSULTA_FOLHA, titulo)
    return reg


# ---------------------------------------------------------------- html v2: abas Padrões, Recursos e Séries
CSS_V2 = """
nav.abas{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 16px}
nav.abas button{font:inherit;padding:8px 14px;border:1px solid var(--linha);border-radius:999px;background:var(--cartao);color:var(--texto);cursor:pointer}
nav.abas button[aria-selected=true]{background:var(--marca);border-color:var(--marca);color:var(--fundo);font-weight:600}
article.recurso,article.serie{background:var(--cartao);border:1px solid var(--linha);border-radius:12px;padding:18px;margin:0 0 22px}
article.recurso h2,article.serie h2{margin:0;font-size:1.3rem;line-height:1.25}
article.recurso h2 small,article.serie h2 small{display:block;font-weight:400;color:var(--suave);font-size:.8rem;margin-top:2px}
.filtros{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;background:var(--cartao);border:1px solid var(--linha);border-radius:10px;padding:10px 14px;margin:0 0 18px}
.filtros label{display:flex;gap:6px;align-items:center;font-size:.85rem;color:var(--suave)}
.filtros select{font:inherit;font-size:.85rem;padding:5px 8px;border:1px solid var(--linha);border-radius:6px;background:var(--fundo);color:var(--texto);max-width:100%}
.selos{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 6px;padding:0;list-style:none}
.selos li{border-radius:6px;padding:2px 9px;font-size:.78rem;font-weight:600;border:1px solid var(--linha)}
.selos .uau{background:#ffd400;color:#111;border-color:#ffd400}.selos .prov{color:var(--anti);border-color:var(--anti)}
figure.alterna figcaption button{font:inherit;font-size:.78rem;margin-left:6px;padding:2px 8px;border:1px solid var(--linha);border-radius:6px;background:var(--chip);color:var(--texto);cursor:pointer}
ol.ritmo{display:flex;flex-wrap:wrap;gap:4px;list-style:none;padding:0;margin:6px 0 12px}
ol.ritmo li{font-size:.75rem;border-radius:6px;padding:3px 7px;background:var(--chip);color:var(--suave)}
ol.ritmo li b{color:var(--texto);margin-right:4px}
ol.ritmo li.impacto,ol.ritmo li.climax{background:var(--marca);color:var(--fundo)}ol.ritmo li.impacto b,ol.ritmo li.climax b{color:var(--fundo)}
dl.tipos dt{font-weight:600;margin-top:6px}dl.tipos dd{margin:0 0 4px 0;color:var(--suave)}
@media (max-width:640px){article.recurso,article.serie{padding:14px;border-radius:10px}.filtros{padding:8px 10px}}
"""

JS_V2 = """
(function(){function norm(s){return s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase()}
var q=document.getElementById('filtro'),rq=[].slice.call(document.querySelectorAll('article.recurso')),sel=[].slice.call(document.querySelectorAll('select[data-filtro]')),sr=document.getElementById('so-sem-risco'),nr=document.getElementById('contagem-recursos');
function filtra(){var t=q?norm(q.value).split(/\\s+/).filter(Boolean):[],vis=0;rq.forEach(function(c){var ok=t.every(function(w){return c.getAttribute('data-busca').indexOf(w)>=0});
sel.forEach(function(s){if(s.value&&(' '+c.getAttribute('data-'+s.getAttribute('data-filtro'))+' ').indexOf(' '+s.value+' ')<0)ok=false});
if(sr&&sr.checked&&c.getAttribute('data-risco')!=='nenhum')ok=false;c.hidden=!ok;if(ok)vis++});if(nr)nr.textContent=vis+' de '+rq.length+' recursos'}
if(q)q.addEventListener('input',filtra);sel.forEach(function(s){s.addEventListener('change',filtra)});if(sr)sr.addEventListener('change',filtra);
[].slice.call(document.querySelectorAll('button.troca')).forEach(function(b){b.addEventListener('click',function(){var f=b.closest('figure'),i=f.querySelector('img'),a=f.querySelector('a'),anot=i.getAttribute('src')===i.getAttribute('data-anotada'),novo=anot?i.getAttribute('data-limpa'):i.getAttribute('data-anotada');i.setAttribute('src',novo);a.setAttribute('href',novo);b.textContent=anot?'ver anotada':'ver limpa'})});
var abas=[].slice.call(document.querySelectorAll('nav.abas button'));function mostra(n){abas.forEach(function(b){var on=b.getAttribute('data-aba')===n;b.setAttribute('aria-selected',on?'true':'false');var s=document.getElementById('aba-'+b.getAttribute('data-aba'));if(s)s.hidden=!on})}
abas.forEach(function(b){b.addEventListener('click',function(){mostra(b.getAttribute('data-aba'));try{history.replaceState(null,'','#aba-'+b.getAttribute('data-aba'))}catch(e){}})});
if(abas.length){var h=(location.hash||'').replace('#','');var alvo=h.indexOf('aba-')===0?h.slice(4):(h.indexOf('recurso-')===0?'recursos':(h.indexOf('serie-')===0?'series':'padroes'));mostra(abas.some(function(b){return b.getAttribute('data-aba')===alvo})?alvo:'padroes')}})();
"""

ROTULO_RISCO = {"nenhum": "sem risco no PDF", "rasteriza-regiao": "rasteriza a região no PDF", "perde-texto": "perde texto no PDF",
                "type3": "fonte Type 3 no PDF", "nao-testado": "PDF não testado"}


def _figura_recurso(rep, r, saida):
    """Figura de um recorte de recurso: a versão anotada, com um botão que alterna para a limpa (as duas do disco, caminho
    relativo). Sem versão anotada no disco, a figura simples do padrão."""
    anot = r.get("anotado")
    if not anot or not (Path(rep) / anot).is_file():
        return _figura(rep, r, saida)
    src_a = _rel(rep, anot, saida)
    tem_limpa = (Path(rep) / r["arquivo"]).is_file()
    src_l = _rel(rep, r["arquivo"], saida) if tem_limpa else src_a
    legenda = f"{_html.escape(r.get('legenda', ''), quote=False)} <span class=vazio>({_html.escape(str(r.get('referencia', '?')))}, p. {r.get('pagina', '?')})</span>"
    botao = " <button type=button class=troca>ver limpa</button>" if tem_limpa else ""
    return (f'<figure class=alterna><a href="{src_a}" target=_blank rel=noopener><img src="{src_a}" data-anotada="{src_a}" data-limpa="{src_l}" '
            f'alt="{_html.escape(r.get("legenda", ""), quote=True)}" loading=lazy></a><figcaption>{legenda}{botao}</figcaption></figure>')


def _aba_recursos(rep, indice, saida, esc, eid):
    recursos = sorted(indice.get("recursos") or [], key=lambda r: r["id"])
    if not recursos:
        return "<p class=vazio>Nenhum recurso no índice ainda (o índice é da versão 1: só padrões de composição).</p>"
    campos = (("dimensoes", "dimensão", "dimensoes"), ("material", "material", "material"), ("luz", "luz", "luz"),
              ("profundidade", "profundidade", "profundidade"), ("intensidade", "intensidade", "intensidade"),
              ("continuidade", "continuidade", "continuidade"), ("via", "via", "producao"))

    def valores(r, campo):
        v = r.get(campo)
        if campo == "intensidade" and isinstance(v, list) and len(v) == 2:
            return [str(x) for x in range(int(v[0]), int(v[1]) + 1)]
        return [str(x) for x in (v if isinstance(v, list) else [v] if v else [])]

    filtros = []
    for chave, rotulo, campo in campos:
        todos = sorted({x for r in recursos for x in valores(r, campo)})
        opcoes = "".join(f'<option value="{eid(v)}">{esc(v)}</option>' for v in todos)
        filtros.append(f'<label>{esc(rotulo)} <select data-filtro="{chave}"><option value="">todas</option>{opcoes}</select></label>')
    filtros.append('<label><input type=checkbox id=so-sem-risco> só sem risco no PDF</label>')
    cartoes = []
    for r in recursos:
        arq = rep / r["arquivo"]
        corpo, meta = "", {}
        if arq.is_file():
            meta, corpo = ler_front_matter(arq.read_text(encoding="utf-8"))
            meta = meta or {}
            corpo = re.sub(r"\A\s*#[ \t][^\n]*\n", "", corpo)
        it = r.get("intensidade") or []
        selos = [f'<li class=uau>uau {esc(r.get("uau"))}</li>']
        if str(meta.get("provisorio", "")).lower() in ("true", "sim", "1"):
            selos.append("<li class=prov>provisório</li>")
        selos.append(f"<li>{esc(ROTULO_RISCO.get(r.get('risco_pdf'), r.get('risco_pdf')))}</li>")
        etiquetas = [r.get("familia"), *[d for d in r.get("dimensoes", []) if d != r.get("familia")], *r.get("recurso", []), *r.get("material", []),
                     f"luz {r.get('luz')}" + (f" da {r.get('luz_direcao')}" if r.get("luz_direcao") not in (None, "nenhuma") else ""),
                     r.get("profundidade"), f"intensidade {it[0]} a {it[1]}" if len(it) == 2 else None, r.get("continuidade"),
                     r.get("producao"), r.get("reproduzivel"), *r.get("tipo_pagina", []), *r.get("tom", [])]
        chips = "".join(f"<li>{esc(e)}</li>" for e in etiquetas if e)
        normais = [x for x in r.get("recortes") or [] if not x.get("anti")]
        antis = [x for x in r.get("recortes") or [] if x.get("anti")]
        galeria = f'<div class=galeria>{"".join(_figura_recurso(rep, x, saida) for x in normais)}</div>' if normais else "<p class=vazio>sem recorte</p>"
        nao_fazer = (f'<section class=naofazer><h3>Não fazer</h3><div class=galeria>{"".join(_figura_recurso(rep, x, saida) for x in antis)}</div></section>'
                     if antis else "")
        texto = md_para_html(corpo) if corpo.strip() else '<p class=vazio>(o .md deste recurso está vazio ou não existe)</p>'
        dados = {chave: " ".join(valores(r, campo)) for chave, _, campo in campos}
        attrs = " ".join(f'data-{k}="{eid(v)}"' for k, v in dados.items())
        busca = norm(" ".join([r["id"], r.get("nome", ""), r.get("efeito", ""), *[str(e) for e in etiquetas if e]]))
        cartoes.append(f'<article class=recurso id="recurso-{eid(r["id"])}" data-busca="{eid(busca)}" data-risco="{eid(r.get("risco_pdf", ""))}" {attrs}>'
                       f'<h2>{esc(r.get("nome", r["id"]))}<small>{esc(r["id"])}</small></h2><ul class=selos>{"".join(selos)}</ul>'
                       f'<p class=problema>{esc(r.get("efeito", ""))}</p><ul class=chips>{chips}</ul>{galeria}{nao_fazer}<div class=texto>{texto}</div></article>')
    return (f'<p class=vazio><span id=contagem-recursos>{len(recursos)} de {len(recursos)} recursos</span></p>'
            f'<div class=filtros>{"".join(filtros)}</div>{"".join(cartoes)}')


def _aba_series(indice, esc, eid):
    refs = sorted((r for r in indice.get("referencias") or [] if r.get("serie")), key=lambda r: r["id"])
    if not refs:
        return "<p class=vazio>Nenhuma referência com série no índice ainda (as referências da versão 1 não têm).</p>"
    out = []
    for r in refs:
        s = r["serie"]
        rit = s.get("ritmo") or {}
        pags = sorted((rit.get("paginas") or {}).items(), key=lambda kv: int(kv[0]))
        ritmo = "".join(f'<li class="{eid(v)}"><b>{int(k):02d}</b>{esc(v)}</li>' for k, v in pags)
        uau = "".join(f"<li>p. {esc(u.get('pagina'))}: nota {esc(u.get('nota'))} ({esc(', '.join(u.get('gatilhos') or []) or 'sem gatilho')})"
                      f"{' · depende da foto' if u.get('depende_de') == 'foto' else ''}{(': ' + esc(u['primeiro_olhar'])) if u.get('primeiro_olhar') else ''}</li>"
                      for u in r.get("uau_paginas") or [])
        tipos = "".join(f"<dt>{esc(t)}</dt><dd>{esc(x)}</dd>" for t, x in sorted((s.get("por_tipo") or {}).items()))
        out.append(f'<article class=serie id="serie-{eid(r["id"])}"><h2>{esc(r.get("nome", r["id"]))}<small>{esc(r["id"])}</small></h2>'
                   f'<h3>Ritmo: {esc(rit.get("padrao", "?"))}</h3><ol class=ritmo>{ritmo}</ol>'
                   f'<h3>Constantes</h3><ul>{"".join(f"<li>{esc(x)}</li>" for x in s.get("constantes") or [])}</ul>'
                   f'<h3>Variáveis</h3><ul>{"".join(f"<li>{esc(x)}</li>" for x in s.get("variaveis") or [])}</ul>'
                   f'<h3>Por tipo de página</h3><dl class=tipos>{tipos}</dl>'
                   + (f"<h3>Páginas que param o olho</h3><ul>{uau}</ul>" if uau else "") + "</article>")
    return "".join(out)


def cmd_buscar_v2(rep, a):
    """buscar com --entidade recurso|todos ou com filtro do estudo v2. Com --entidade padrao só vale --dimensao (os padrões
    não declaram material, luz, via nem risco no PDF): o resto recusa com mensagem. Devolve o código de saída."""
    funcoes, relacoes, tons = _lista_de(a.funcao), _lista_de(a.relacao), _lista_de(a.tom)
    filtros = {c: _lista_de(getattr(a, f"f_{c}")) for c, *_ in FILTROS_RECURSO}
    vf, vr, vt = vocabularios()
    for nome, valores, vocab in (("função", funcoes, vf), ("relação", relacoes, vr), ("tom", tons, TONS), ("rota", [a.rota] if a.rota else [], ROTAS)):
        for v in valores:
            if norm(v) not in vocab:
                sys.exit(f"repertorio: {nome} `{v}` não existe (use: {', '.join(vocab)})")
    for chave, _, _, rotulo, nome_voc in FILTROS_RECURSO:
        vocab = [str(x) for x in voc(nome_voc)]
        for v in filtros[chave]:
            if norm(v) not in vocab:
                sys.exit(f"repertorio: {rotulo} `{v}` não existe (use: {', '.join(vocab)})")
    so_recurso = [f"--{c}" for c, v in filtros.items() if v and c != "dimensao"] + (["--sem-risco-pdf"] if a.sem_risco_pdf else []) \
        + (["--uau-min"] if a.uau_min is not None else [])
    if a.entidade == "padrao" and so_recurso:
        sys.exit(f"repertorio: {', '.join(so_recurso)} vale só com --entidade recurso ou todos (padrão de composição não declara isso)")
    if a.entidade == "recurso" and relacoes:
        sys.exit("repertorio: --relacao vale só para padrões (use --entidade padrao ou todos)")
    for t in _paginas_pedidas(a.pagina):
        if t not in vt:
            print(f"AVISO  tipo de página `{a.pagina}` fora do vocabulário ({', '.join(vt)})", file=sys.stderr)
    indice = carregar(rep)
    if a.entidade == "padrao":
        res = [dict(x, entidade="padrao") for x in buscar(indice, a.pagina, a.problema, funcoes, relacoes, a.rota, tons, a.n, dimensoes=filtros["dimensao"])]
    elif a.entidade == "recurso":
        res = buscar_recursos(indice, a.pagina, a.problema, funcoes, tons, a.rota, filtros, a.sem_risco_pdf, a.uau_min, n=a.n)
    else:
        res = buscar_todos(indice, a.pagina, a.problema, funcoes, relacoes, a.rota, tons, filtros, a.sem_risco_pdf, a.uau_min, n=a.n)
    if a.json:
        out = []
        for r in res:
            it = r.get("recurso") or r.get("padrao")
            base = {"n": r["n"], "entidade": r["entidade"], "id": it["id"], "nome": it.get("nome"), "nota": r["nota"], "razoes": r["razoes"],
                    "arquivo": str((rep / it["arquivo"]).resolve()), "recortes": [str((rep / x["arquivo"]).resolve()) for x in it.get("recortes") or []]}
            if r["entidade"] == "recurso":
                base.update({k: it.get(k) for k in ("efeito", "familia", "dimensoes", "recurso", "material", "luz", "luz_direcao", "profundidade",
                                                    "intensidade", "continuidade", "producao", "risco_pdf", "reproduzivel", "uau", "tipo_pagina", "tom")})
                base["anotados"] = [str((rep / x["anotado"]).resolve()) for x in it.get("recortes") or [] if x.get("anotado")]
            else:
                base.update({k: it.get(k) for k in ("problema", "tipo_pagina", "funcao", "relacao", "rota", "tom", "densidade", "dimensoes")})
            out.append(base)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    for r in res:
        it = r.get("recurso") or r.get("padrao")
        tag = "recurso" if r["entidade"] == "recurso" else "padrão "
        print(f"{r['n']:>2}. {tag}  {it['id']:<44} {it.get('nome', '')}  (nota {r['nota']}: {'; '.join(r['razoes'])})")
        if r["entidade"] == "recurso":
            print(f"      {it.get('efeito', '')}")
            print(f"      {(rep / it['arquivo']).resolve()}  ({len(it.get('recortes') or [])} recorte(s); uau {it.get('uau')}; "
                  f"PDF {it.get('risco_pdf')}; via {it.get('producao')})")
        else:
            print(f"      {it.get('problema', '')}")
            print(f"      {(rep / it['arquivo']).resolve()}  ({len(it.get('recortes') or [])} recorte(s))")
    if not res:
        print("nada casou" if indice.get("recursos") or a.entidade != "recurso" else "nenhum recurso no índice (versão 1)")
    return 0


# ---------------------------------------------------------------- CLI
def main():
    # --repertorio vale antes e depois do subcomando: no subparser o default é SUPPRESS (senão o default dele apagaria o valor
    # dado antes do subcomando e a ferramenta conferiria a pasta errada em silêncio)
    comum = argparse.ArgumentParser(add_help=False)
    comum.add_argument("--repertorio", default=argparse.SUPPRESS)
    ap = argparse.ArgumentParser(description="repertório de composição (ver o topo do arquivo)")
    ap.add_argument("--repertorio", default=str(RAIZ), help="pasta do repertório (padrão: repertorio/ na raiz do projeto)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("buscar", parents=[comum])
    p.add_argument("--pagina"); p.add_argument("--problema"); p.add_argument("--rota")
    for c in ("--funcao", "--relacao", "--tom"):
        p.add_argument(c, action="append")
    p.add_argument("-n", type=int, default=5); p.add_argument("--json", action="store_true")
    p.add_argument("--entidade", choices=("padrao", "recurso", "todos"), default="padrao",
                   help="padrao (o de sempre, saída igual), recurso (camada de acabamento) ou todos")
    for chave, *_ in FILTROS_RECURSO:
        p.add_argument(f"--{chave}", action="append", dest=f"f_{chave}")
    p.add_argument("--sem-risco-pdf", action="store_true", help="só recurso com risco_pdf nenhum (provado no PDF)")
    p.add_argument("--uau-min", type=int, choices=(0, 1, 2, 3), help="só recurso com nota uau a partir desta")
    p = sub.add_parser("folha", parents=[comum]); p.add_argument("ids", nargs="+"); p.add_argument("--saida", required=True)
    sub.add_parser("checar", parents=[comum])
    p = sub.add_parser("recortar", parents=[comum]); p.add_argument("analise"); p.add_argument("--saida", required=True)
    p.add_argument("--base-imagens", action="append"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("html", parents=[comum]); p.add_argument("--saida", help="padrão: <pasta do repertório>/repertorio.html (caminho relativo vale a partir de onde você roda)")
    p = sub.add_parser("usados", parents=[comum]); p.add_argument("kit"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("capturar", parents=[comum])
    p.add_argument("--ref", nargs="+", action="extend", default=[], help="ids de fontes.json (vários, ou separados por vírgula)")
    p.add_argument("--camada", nargs="+", action="extend", default=[], help=f"camadas de fontes.json: {', '.join(CAMADAS)}")
    p.add_argument("--largura", type=int, help=f"largura máxima de cada página (padrão: a da fonte, {LARGURA_PADRAO})")
    p.add_argument("--pausa", type=float, default=4, help="segundos de espera entre uma galeria e a seguinte (padrão 4)")
    p.add_argument("--forcar", action="store_true", help="refaz também quem já tem manifesto ok (só sobrescreve arquivo do próprio manifesto)")
    p.add_argument("--listar", action="store_true", help="só lista as fontes e o estado do manifesto, sem baixar nada")
    p = sub.add_parser("folha-contato", parents=[comum]); p.add_argument("refs", nargs="+")
    p = sub.add_parser("conferir-captura", parents=[comum]); p.add_argument("refs", nargs="+")
    p = sub.add_parser("anotar", parents=[comum]); p.add_argument("analise"); p.add_argument("--saida", required=True)
    p.add_argument("--todos", action="store_true", help="todos os candidatos, não só os aceitos")
    p.add_argument("--base-imagens", action="append"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("mapa", parents=[comum]); p.add_argument("ref"); p.add_argument("pagina", type=int)
    p.add_argument("--analise", action="append", help="JSON de análise com mais exemplos desta página (pode repetir)")
    p.add_argument("--saida", help="padrão: <repertório>/mapas/<ref>-<pp>.jpg")
    p = sub.add_parser("indexar", parents=[comum]); p.add_argument("--escrever", action="store_true", help="grava o indice.json")
    p = sub.add_parser("serie", parents=[comum]); p.add_argument("ref"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("cobertura", parents=[comum]); p.add_argument("--json", action="store_true")
    p = sub.add_parser("consultar", parents=[comum]); p.add_argument("kit")
    p.add_argument("--historico", help=f"padrão: {HISTORICO_KITS.relative_to(AQUI.parent)}")
    a = ap.parse_args()
    rep = Path(a.repertorio)
    if a.cmd == "buscar" and (a.entidade != "padrao" or any(getattr(a, f"f_{c}") for c, *_ in FILTROS_RECURSO)
                              or a.sem_risco_pdf or a.uau_min is not None):
        sys.exit(cmd_buscar_v2(rep, a))
    if a.cmd == "buscar":
        funcoes, relacoes, tons = _lista_de(a.funcao), _lista_de(a.relacao), _lista_de(a.tom)
        vf, vr, vt = vocabularios()
        for nome, valores, vocab in (("função", funcoes, vf), ("relação", relacoes, vr), ("tom", tons, TONS), ("rota", [a.rota] if a.rota else [], ROTAS)):
            for v in valores:
                if norm(v) not in vocab:
                    sys.exit(f"repertorio: {nome} `{v}` não existe (use: {', '.join(vocab)})")
        for t in _paginas_pedidas(a.pagina):
            if t not in vt:
                print(f"AVISO  tipo de página `{a.pagina}` fora do vocabulário ({', '.join(vt)})", file=sys.stderr)
        res = buscar(carregar(rep), a.pagina, a.problema, funcoes, relacoes, a.rota, tons, a.n)
        if a.json:
            print(json.dumps([{"n": r["n"], "id": r["padrao"]["id"], "nome": r["padrao"]["nome"], "nota": r["nota"], "razoes": r["razoes"],
                               "problema": r["padrao"].get("problema"), "arquivo": str((rep / r["padrao"]["arquivo"]).resolve()),
                               "tipo_pagina": r["padrao"].get("tipo_pagina"), "funcao": r["padrao"].get("funcao"), "relacao": r["padrao"].get("relacao"),
                               "rota": r["padrao"].get("rota"), "tom": r["padrao"].get("tom"), "densidade": r["padrao"].get("densidade"),
                               "recortes": [str((rep / x["arquivo"]).resolve()) for x in r["padrao"].get("recortes") or []]} for r in res],
                             ensure_ascii=False, indent=2))
        else:
            for r in res:
                p_ = r["padrao"]
                print(f"{r['n']:>2}. {p_['id']:<44} {p_['nome']}  (nota {r['nota']}: {'; '.join(r['razoes'])})")
                print(f"      {p_.get('problema', '')}")
                print(f"      {(rep / p_['arquivo']).resolve()}  ({len(p_.get('recortes') or [])} recorte(s))")
            if not res:
                print("nenhum padrão casou")
        return
    if a.cmd == "folha":
        caminho, (w, h) = folha(rep, a.ids, a.saida)
        print("OK", caminho, f"{w}x{h}")
        return
    if a.cmd == "checar":
        res = checar(rep)
        for nivel, m in sorted(res, key=lambda r: r[0] != "AVISO"):
            print(f"{nivel}  {m}")
        nf = sum(1 for n, _ in res if n == "FALHA")
        print(f"\n{nf} falha(s), {len(res) - nf} aviso(s)")
        sys.exit(1 if nf else 0)
    if a.cmd == "recortar":
        r = recortar(a.analise, a.saida, a.base_imagens)
        if a.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            for f in r["feitos"]:
                print(f"OK  {f['arquivo']}  {f['tamanho'][0]}x{f['tamanho'][1]}  ({f['padrao']})")
            for pb in r["problemas"]:
                print(f"FALHA  {pb}")
            print(f"{len(r['feitos'])} recorte(s) em {a.saida}" + (f"; conferência: {r['conferencia']}" if r["conferencia"] else ""))
        sys.exit(1 if r["problemas"] else 0)
    if a.cmd == "html":
        print("OK", gerar_html(rep, a.saida or rep / "repertorio.html").resolve())
        return
    if a.cmd == "capturar":
        sys.exit(cmd_capturar(rep, a))
    if a.cmd == "folha-contato":
        falhou = 0
        for ref in a.refs:
            try:
                saidas = folha_contato(rep, ref)
                print("OK", ref, f"{len(saidas)} folha(s) em {pasta_captura(rep, ref)}")
            except ErroCaptura as e:
                falhou += 1; print("FALHA", e)
        sys.exit(1 if falhou else 0)
    if a.cmd == "conferir-captura":
        falhou = 0
        for ref in a.refs:
            try:
                imprimir_conferencia(conferir(rep, ref))
            except ErroCaptura as e:
                falhou += 1; print("FALHA", e)
        sys.exit(1 if falhou else 0)
    if a.cmd == "usados":
        r = usados(a.kit, rep)
        if a.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            for pid, chaves in r["padroes"].items():
                print(f"{pid:<44} {', '.join(chaves)}" + ("   (fora do repertório)" if pid in r["desconhecidos"] else ""))
            if not r["padroes"]:
                print("nenhum padrão declarado em composicao[*].padroes")
            if r["recursos"]:
                print("recursos:")
                for rid, chaves in r["recursos"].items():
                    print(f"{rid:<44} {', '.join(chaves) or '(só na direção criativa)'}" + ("   (fora do repertório)" if rid in r["recursos_desconhecidos"] else ""))
        return
    if a.cmd == "anotar":
        r = anotar(a.analise, a.saida, a.todos, a.base_imagens)
        if a.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            for f in r["feitos"]:
                print(f"OK  {f['arquivo']}  e {Path(f['anotado']).name}  {f['tamanho'][0]}x{f['tamanho'][1]}  {len(f['anotacoes'])} anotação(ões)")
            for x in r["avisos"]:
                print(f"AVISO  {x}")
            for pb in r["problemas"]:
                print(f"FALHA  {pb}")
            print(f"{len(r['feitos'])} recorte(s) limpos e anotados em {a.saida}" + (f"; manifesto: {r['manifesto']}" if r["manifesto"] else ""))
        sys.exit(1 if r["problemas"] else 0)
    if a.cmd == "mapa":
        destino, n = mapa(rep, a.ref, a.pagina, a.analise or (), a.saida)
        print("OK", Path(destino).resolve(), f"({n} recorte(s) marcados)")
        return
    if a.cmd == "indexar":
        r = indexar(rep, a.escrever)
        for chave in ("novos", "alterados", "removidos"):
            if r[chave]:
                print(f"{chave}: {', '.join(r[chave])}")
        for pb in r["problemas"]:
            print(f"FALHA  {pb}")
        for e in r["erros_schema"][:10]:
            print(f"FALHA  índice fora do schema: {e}")
        if r["erros_schema"]:
            print("não gravei: o índice montado sai fora do schema")
        elif a.escrever:
            print("gravei o indice.json; rode `repertorio.py checar`" if r["escrito"] else "nada mudou no indice.json")
        else:
            print("nada gravado (use --escrever)" if any(r[c] for c in ("novos", "alterados", "removidos")) else "o índice já está igual aos .md")
        sys.exit(1 if r["problemas"] or r["erros_schema"] else 0)
    if a.cmd == "serie":
        itens = serie(rep, a.ref)
        if a.json:
            print(json.dumps(itens, ensure_ascii=False, indent=2))
        else:
            imprimir_serie(a.ref, itens)
        sys.exit(0 if itens else 1)
    if a.cmd == "cobertura":
        c = cobertura(carregar(rep))
        if a.json:
            print(json.dumps(c, ensure_ascii=False, indent=2))
        else:
            imprimir_cobertura(c)
        return
    if a.cmd == "consultar":
        r = consultar(a.kit, rep, a.historico)
        for c in r["consultas"]:
            print(f"{c['familia']:<24} " + (", ".join(f"{x['id']} ({x['nota']}{', recente' if x['recente'] else ''})" for x in c["resultados"][:POR_FAMILIA]) or "-"))
        if r.get("aviso"):
            print(f"AVISO  {r['aviso']}")
        print(f"OK {Path(a.kit).resolve() / CONSULTA_ARQ} ({len(r['ids'])} recurso(s); leitura: {r['leitura']['fonte'] or 'nenhuma'}); "
              f"folha: {Path(a.kit).resolve() / CONSULTA_FOLHA}")
        return


if __name__ == "__main__":
    main()

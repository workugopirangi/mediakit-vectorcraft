#!/usr/bin/env python3
"""
acabamento.py: o contrato de vocabulário da camada de acabamento (mk-2.1) e as regras que o schema não alcança.
Processo e tabela das regras: references/10-acabamento.md. Contrato: schema/mediakit.schema.json (direcao_criativa,
formato_base, receitas[].fontes.lettering) e schema/elementos.schema.json (composicao_pagina.acabamento,
composicao_elemento.efeito, .recurso, .motivo e papel acabamento; elemento.papel acabamento e material; âncora registro).

  validar(k)                       -> (falhas, avisos) sobre o dicionário do mediakit.json inteiro
  validar(k, so_composicao=True)   só as regras que a composição sozinha decide (o canal do camadas.py, que chama
                                     composicao.validar sem o kit: ver composicao.validar, parâmetro `kit`)
  erros_schema(k)                  erros do kit contra os dois schemas: raiz, composicao, sistema_elementos e elementos[]
  gera_vertical(k, relatorio)      (bool, porquê): o kit entrega o PDF vertical? Se não, o QA tira as composicao `vertical:*`
                                     da conta com sem_vertical(k) (references/10, seção QA)

Kit sem nenhum campo novo não passa por regra nenhuma: validar devolve ([], []) antes de olhar qualquer coisa.
Os geradores dos grafismos novos (TIPOS_A_ENTRAR) não existem ainda: o enum de elemento.tipo e de constantes[].tipo só
ganha cada tipo junto com o gerador (test_grafismos.py cobra que andem juntos). Na composição, `grafismo.tipo` é texto
livre e já aceita o nome; o render acusa `grafismo desconhecido` até o gerador entrar.

Uso: ~/.venvs/mediakit/bin/python pipeline/acabamento.py <pasta-do-kit>   imprime FALHA e AVISO; sai 1 com falha.
"""
import json, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SCHEMA_KIT = AQUI.parent / "schema" / "mediakit.schema.json"
SCHEMA_ELEMENTOS = AQUI.parent / "schema" / "elementos.schema.json"

# ------------------------------------------------------------------------------------------------- vocabulários
FAMILIAS = ("ornamento-identidade", "pattern-textura", "sobreposicao-recorte", "profundidade-3d", "tratamento-imagem",
            "tipografia-expressiva", "acabamento-borda", "composicao-hibrida")
INTENSIDADE = {0: "nenhuma", 1: "sutil", 2: "presente", 3: "marcante"}
PAPEIS_FIO = ("contrapeso", "selo", "separador", "estrutura", "eco", "textura", "moldura")
ROTAS = ("codigo", "imagem", "hibrido")
MATERIAIS = ("metal-escovado", "ouro", "couro", "borracha", "tecido", "vidro-fosco", "plastico-fosco", "madeira", "papel",
             "grama")
EFEITO = {
    "opacidade": (1, 0.72, 0.46, 0.24, 0.12, 0.06),
    "blend": ("normal", "multiply", "screen", "soft-light"),
    "mascara": ("nenhuma", "diagonal", "chanfro", "circulo", "arco-base", "janela"),
    "sombra": ("nenhuma", "contato", "deslocada"),
    "reflexo": ("nenhum", "piso"),
    "cruza": {"alvo": ("titulo", "numero"), "corte": ("linha_base", "cap", "cy")},
    "esmaecer": {"direcao": ("dir", "esq", "cima", "baixo"), "passos": (3, 8), "minimo": (0, 0.46)},
}
PAGINA = {"profundidade": ("plana", "camadas", "volume"), "grao": ("nenhum", "leve", "padrao", "forte"),
          "luz": ("nenhuma", "esq", "dir", "topo")}
RELACAO_NOVA = "registro"                        # âncora {relacao: registro, alvo: foto}: posição e escala vêm da foto
FUNCOES_ACABAMENTO = ("acabamento", "identidade", "profundidade", "equilibrio")
MAX_ACABAMENTO_POR_PAGINA = 2
MIN_PAGINAS_FIO = 3
MIN_FAMILIAS = 4                                 # aviso agora; vira falha na etapa do fluxo (references/10)
TIPOS_A_ENTRAR = ("hachura", "malha", "aneis", "pontos-radiais", "cantoneira", "moldura-dupla", "regua-borda", "eco",
                  "texto-curva", "ondas", "curvas-nivel", "fita", "carimbo", "numeral-eco", "meio-tom-foto")
CONSTANTES_A_ENTRAR = ("regua-borda",)


# ------------------------------------------------------------------------------------------------- guarda
def usa_acabamento(k):
    """O kit declara algum campo da camada de acabamento? Sem nenhum, nenhuma regra roda (kit mk-2.0 igual a antes)."""
    k = k or {}
    if k.get("direcao_criativa") is not None or k.get("formato_base") is not None:
        return True
    if any((r.get("fontes") or {}).get("lettering") for r in k.get("receitas") or [] if isinstance(r, dict)):
        return True
    if any(e.get("papel") == "acabamento" or "material" in e for e in k.get("elementos") or [] if isinstance(e, dict)):
        return True
    for chave, ent in (k.get("composicao") or {}).items():
        if chave.startswith("_") or not isinstance(ent, dict):
            continue
        if "acabamento" in ent:
            return True
        for e in ent.get("elementos") or []:
            if not isinstance(e, dict):
                continue
            if e.get("papel") == "acabamento" or any(c in e for c in ("efeito", "recurso", "motivo")):
                return True
            if (e.get("ancora") or {}).get("relacao") == RELACAO_NOVA:
                return True
    return False


# ------------------------------------------------------------------------------------------------- vertical
def e_vertical(chave):
    """Chave de composição do vertical (`vertical:capa`, `vertical:numeros`, `vertical:contato`)."""
    return str(chave).startswith("vertical:")


def chaves_vertical(k):
    """As chaves `vertical:*` da composição do kit, na ordem em que estão."""
    comp = (k or {}).get("composicao")
    return [c for c in comp if e_vertical(c)] if isinstance(comp, dict) else []


def relatorio_da_pasta(pasta):
    """saida/render-report.json do kit, ou None (não existe ou ilegível)."""
    try:
        r = json.loads((Path(pasta) / "saida" / "render-report.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return r if isinstance(r, dict) else None


def _pede_vertical(item):
    """Item de `paginas` que é do vertical: o tipo `vertical` ou `vertical:...` (string ou {tipo})."""
    tipo = item.get("tipo") if isinstance(item, dict) else item
    return isinstance(tipo, str) and tipo.split(":", 1)[0] == "vertical"


def gera_vertical(k, relatorio=None):
    """(gera, porquê): o kit entrega o PDF vertical? O fato vence a declaração.
    1. Com render-report que lista direções: gera quem tem `vertical` em alguma direção. O render.py --sem-vertical não
       grava a chave; o render sem a flag sempre grava (kit com `paginas` inclusive).
    2. Sem render-report (QA antes do render): `paginas` declarado (lista não vazia) sem item vertical é kit só horizontal,
       a decisão que o render --sem-vertical cumpre. Sem `paginas`, ou com item vertical, gera: o render gera o vertical
       sempre que não leva a flag.
    O porquê só vem preenchido quando NÃO gera: é a frase do aviso do QA."""
    dirs = relatorio.get("direcoes") if isinstance(relatorio, dict) else None
    if isinstance(dirs, dict) and dirs:
        if any(isinstance(m, dict) and "vertical" in m for m in dirs.values()):
            return True, ""
        return False, "o render-report não tem vertical em nenhuma direção (render com --sem-vertical)"
    pag = (k or {}).get("paginas")
    if isinstance(pag, list) and pag and not any(_pede_vertical(i) for i in pag):
        return False, ("`paginas` declara só páginas horizontais e ainda não há render-report; o render do kit precisa "
                       "levar --sem-vertical")
    return True, ""


def sem_vertical(k):
    """Cópia rasa do kit sem as composições `vertical:*` e sem elas na tabela do fio condutor: é o kit que o QA confere
    quando o vertical não é gerado. As páginas horizontais não mudam (entrada_da_pagina só casa `vertical:*` com o
    formato vertical)."""
    out = dict(k or {})
    if isinstance(out.get("composicao"), dict):
        out["composicao"] = {c: v for c, v in out["composicao"].items() if not e_vertical(c)}
    dc = out.get("direcao_criativa")
    fio = dc.get("fio_condutor") if isinstance(dc, dict) else None
    if isinstance(fio, dict) and isinstance(fio.get("papeis"), dict):
        papeis = {c: v for c, v in fio["papeis"].items() if not e_vertical(c)}
        out["direcao_criativa"] = {**dc, "fio_condutor": {**fio, "papeis": papeis}}
    return out


# ------------------------------------------------------------------------------------------------- contexto
class _Ctx:
    """O que as regras leem do kit, montado uma vez. so_composicao: o kit não veio (só a composição)."""

    def __init__(self, k, so_composicao):
        self.k, self.so_comp = k, so_composicao
        self.falhas, self.avisos = [], []
        self.comp = k.get("composicao") or {}
        self.dc = k.get("direcao_criativa") if isinstance(k.get("direcao_criativa"), dict) else None
        dc = self.dc or {}
        self.recursos = {r.get("id"): r for r in dc.get("recursos") or [] if isinstance(r, dict)}
        self.nao_usa = set(dc.get("nao_usa") or [])
        self.intensidade = dc.get("intensidade") if isinstance(dc.get("intensidade"), dict) else {}
        sis = k.get("sistema_elementos") or {}
        self.motivos = {m.get("id") for m in sis.get("motivos") or [] if isinstance(m, dict)}
        self.els = {e.get("id"): e for e in k.get("elementos") or [] if isinstance(e, dict)}

    def paginas(self):
        for chave, ent in self.comp.items():
            if chave.startswith("_") or not isinstance(ent, dict):
                continue
            yield chave, ent

    def elementos(self):
        """(onde, entrada, elemento da composição, elemento de elementos[] ou None)."""
        for chave, ent in self.paginas():
            for i, e in enumerate(ent.get("elementos") or []):
                if isinstance(e, dict):
                    yield f"composicao/{chave}/elementos/{i} (`{e.get('id')}`)", ent, e, self.els.get(e.get("id"))

    def recursos_usados(self):
        """(onde, id do recurso) de cada página (acabamento.recursos) e de cada elemento (`recurso`)."""
        for chave, ent in self.paginas():
            for rid in (ent.get("acabamento") or {}).get("recursos") or []:
                yield f"composicao/{chave}/acabamento", rid
        for onde, _, e, _ in self.elementos():
            if e.get("recurso"):
                yield onde, e["recurso"]


def _png_de_imagem(el):
    """Elemento de elementos[] cujo arquivo é PNG de rota de imagem (não grafismo por código): é dele que saem a
    silhueta da sombra de contato e o reflexo no piso."""
    if not el or el.get("formato") != "png" or el.get("rota") == "codigo":
        return False
    arq = el.get("arquivo")
    return not arq or str(arq).lower().endswith(".png")


def _svg(e, el):
    return bool(e.get("grafismo")) or bool(el and el.get("formato") == "svg")


# ------------------------------------------------------------------------------------------------- regras
def regra_maximo_por_pagina(c):
    """FALHA: mais de 2 elementos de papel acabamento numa página."""
    for chave, ent in c.paginas():
        n = sum(1 for e in ent.get("elementos") or [] if isinstance(e, dict) and e.get("papel") == "acabamento")
        if n > MAX_ACABAMENTO_POR_PAGINA:
            c.falhas.append(f"composicao/{chave}: {n} elementos de papel acabamento (máximo {MAX_ACABAMENTO_POR_PAGINA} por página)")


def regra_acabamento_funcao(c):
    """FALHA: papel acabamento com função fora de acabamento, identidade, profundidade, equilibrio."""
    for onde, _, e, _ in c.elementos():
        if e.get("papel") == "acabamento" and e.get("funcao") not in FUNCOES_ACABAMENTO:
            c.falhas.append(f"{onde}: papel acabamento pede função {', '.join(FUNCOES_ACABAMENTO)} (recebeu {e.get('funcao')!r})")


def regra_acabamento_motivo(c):
    """FALHA: papel acabamento sem motivo (dele ou do elemento em elementos[]); com o kit, motivo que não existe em
    sistema_elementos.motivos. Vale também para elementos[] de papel acabamento."""
    for onde, _, e, el in c.elementos():
        if e.get("papel") != "acabamento":
            continue
        motivo = e.get("motivo") or (el or {}).get("motivo")
        if not motivo and c.so_comp and not e.get("grafismo"):
            continue                                 # sem o kit, o motivo pode estar em elementos[]: decide quem tem o kit
        if not motivo:
            c.falhas.append(f"{onde}: papel acabamento exige `motivo` (no elemento da composição ou em elementos[])")
        elif not c.so_comp and motivo not in c.motivos:
            c.falhas.append(f"{onde}: motivo `{motivo}` não existe em sistema_elementos.motivos")
    if c.so_comp:
        return
    for i, el in enumerate(c.k.get("elementos") or []):
        if not isinstance(el, dict) or el.get("papel") != "acabamento":
            continue
        if not el.get("motivo"):
            c.falhas.append(f"elementos/{i} (`{el.get('id')}`): papel acabamento exige `motivo`")
        elif el["motivo"] not in c.motivos:
            c.falhas.append(f"elementos/{i} (`{el.get('id')}`): motivo `{el['motivo']}` não existe em sistema_elementos.motivos")


def regra_cruza_na_frente(c):
    """FALHA: efeito.cruza fora da camada frente (sem camada, o render põe na frente). Se o alvo (título ou número)
    existe na página só o render sabe: o alvo ausente vira erro da âncora no render, como qualquer alvo da composição."""
    for onde, _, e, _ in c.elementos():
        if (e.get("efeito") or {}).get("cruza") and (e.get("camada") or "frente") != "frente":
            c.falhas.append(f"{onde}: efeito.cruza só na camada frente (recebeu {e.get('camada')!r})")


def regra_sombra_reflexo_png(c):
    """FALHA: sombra contato ou reflexo piso em elemento que não é PNG de imagem de elementos[]. Grafismo declarado só
    na página é decidido sem o kit; o resto precisa de elementos[]."""
    for onde, _, e, el in c.elementos():
        ef = e.get("efeito") or {}
        pede = [n for n, ok in (("sombra contato", ef.get("sombra") == "contato"), ("reflexo piso", ef.get("reflexo") == "piso")) if ok]
        if not pede:
            continue
        if e.get("grafismo") or (not c.so_comp and not _png_de_imagem(el)):
            c.falhas.append(f"{onde}: {' e '.join(pede)} só em elemento de elementos[] com arquivo PNG e rota de imagem "
                            f"(saem da silhueta do recorte)")


def regra_deslocada_svg(c):
    """FALHA: sombra deslocada fora de grafismo SVG."""
    if c.so_comp:
        return
    for onde, _, e, el in c.elementos():
        if (e.get("efeito") or {}).get("sombra") == "deslocada" and not _svg(e, el):
            c.falhas.append(f"{onde}: sombra deslocada só em grafismo SVG (grafismo na composição ou elementos[] formato svg)")


def regra_familia_proibida(c):
    """FALHA: página ou elemento usa recurso de uma família de direcao_criativa.nao_usa."""
    if c.so_comp:
        return
    for onde, rid in c.recursos_usados():
        r = c.recursos.get(rid)
        if r and r.get("familia") in c.nao_usa:
            c.falhas.append(f"{onde}: recurso `{rid}` é da família {r['familia']}, que direcao_criativa.nao_usa proíbe")


def regra_recurso_fora(c):
    """AVISO: página ou elemento cita recurso que não está em direcao_criativa.recursos."""
    if c.so_comp:
        return
    for onde, rid in c.recursos_usados():
        if rid not in c.recursos:
            c.avisos.append(f"{onde}: recurso `{rid}` fora de direcao_criativa.recursos")


def regra_fio_condutor(c):
    """FALHA: fio condutor em menos de 3 páginas."""
    if c.so_comp or not c.dc or not isinstance(c.dc.get("fio_condutor"), dict):
        return
    papeis = c.dc["fio_condutor"].get("papeis") or {}
    if len(papeis) < MIN_PAGINAS_FIO:
        c.falhas.append(f"direcao_criativa/fio_condutor: {len(papeis)} página(s) em `papeis`; o fio condutor atravessa pelo menos {MIN_PAGINAS_FIO}")


def regra_teto_padrao(c):
    """FALHA: intensidade.teto abaixo de intensidade.padrao."""
    if c.so_comp:
        return
    p, t = c.intensidade.get("padrao"), c.intensidade.get("teto")
    if isinstance(p, int) and isinstance(t, int) and t < p:
        c.falhas.append(f"direcao_criativa/intensidade: teto {t} abaixo do padrão {p}")


def regra_intensidade_teto(c):
    """AVISO: acabamento.intensidade da página acima do teto da direção."""
    if c.so_comp:
        return
    t = c.intensidade.get("teto")
    if not isinstance(t, int):
        return
    for chave, ent in c.paginas():
        v = (ent.get("acabamento") or {}).get("intensidade")
        if isinstance(v, int) and v > t:
            c.avisos.append(f"composicao/{chave}/acabamento: intensidade {v} ({INTENSIDADE.get(v, v)}) acima do teto {t}")


def regra_familias_minimas(c):
    """AVISO: direcao_criativa.recursos com menos de 4 famílias distintas (vira FALHA na etapa do fluxo)."""
    if c.so_comp or c.dc is None:
        return
    fams = {r.get("familia") for r in c.recursos.values() if r.get("familia")}
    if len(fams) < MIN_FAMILIAS:
        c.avisos.append(f"direcao_criativa/recursos: {len(fams)} família(s) distinta(s) ({', '.join(sorted(fams)) or 'nenhuma'}); "
                        f"o kit pede pelo menos {MIN_FAMILIAS}")


REGRAS = (regra_maximo_por_pagina, regra_acabamento_funcao, regra_acabamento_motivo, regra_cruza_na_frente,
          regra_sombra_reflexo_png, regra_deslocada_svg, regra_familia_proibida, regra_recurso_fora, regra_fio_condutor,
          regra_teto_padrao, regra_intensidade_teto, regra_familias_minimas)


def validar(k, so_composicao=False):
    """(falhas, avisos) da camada de acabamento. so_composicao=True: o dicionário só traz `composicao` (e talvez
    `elementos`); as regras que dependem do kit inteiro (direção, motivos, elementos[]) não rodam."""
    k = k or {}
    if not usa_acabamento(k):
        return [], []
    c = _Ctx(k, so_composicao)
    for regra in REGRAS:
        regra(c)
    return c.falhas, c.avisos


# ------------------------------------------------------------------------------------------------- schema
def _carregar(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def erros_schema(k, sch_kit=None, sch_el=None):
    """Erros do kit contra os schemas (lista vazia = válido): a raiz contra mediakit.schema.json e, quando existem,
    `composicao`, `sistema_elementos` e cada item de `elementos[]` contra as definições de elementos.schema.json.
    sch_kit e sch_el (dicts) trocam os schemas do disco: é assim que a prova compara o schema novo com o do git."""
    import jsonschema
    sch_kit = sch_kit if sch_kit is not None else _carregar(SCHEMA_KIT)
    sch_el = sch_el if sch_el is not None else _carregar(SCHEMA_ELEMENTOS)
    defs = sch_el["definitions"]
    erros = []

    def junta(validador, inst, prefixo):
        for e in sorted(validador.iter_errors(inst), key=lambda e: [str(p) for p in e.absolute_path]):
            onde = "/".join(str(p) for p in e.absolute_path)
            erros.append(f"{prefixo}{'/' + onde if onde else ''}: {e.message}")

    junta(jsonschema.Draft202012Validator(sch_kit), k, "mediakit")
    for chave, definicao in (("composicao", "composicao"), ("sistema_elementos", "sistema_elementos")):
        if k.get(chave) is not None:
            junta(jsonschema.Draft7Validator({"$ref": f"#/definitions/{definicao}", "definitions": defs}), k[chave], chave)
    v_el = jsonschema.Draft7Validator({"$ref": "#/definitions/elemento", "definitions": defs})
    for i, el in enumerate(k.get("elementos") or []):
        junta(v_el, el, f"elementos/{i}")
    return erros


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(0)
    kit = json.loads(Path(sys.argv[1], "mediakit.json").read_text(encoding="utf-8"))
    falhas, avisos = validar(kit)
    for f in falhas:
        print("FALHA", f)
    for a in avisos:
        print("AVISO", a)
    print(f"{len(falhas)} falha(s), {len(avisos)} aviso(s) na camada de acabamento" if usa_acabamento(kit)
          else "o kit não declara a camada de acabamento: nenhuma regra rodou")
    sys.exit(1 if falhas else 0)

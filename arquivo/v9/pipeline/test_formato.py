#!/usr/bin/env python3
"""
test_formato.py: provas do formato reprodutível (formato.py, Frente F de 12/10/2026). Sem pytest, sem render.

  ~/.venvs/mediakit/bin/python pipeline/test_formato.py              as provas (segundos)
  ~/.venvs/mediakit/bin/python pipeline/test_formato.py --mutantes   cada prova contra o mutante dela: a prova tem de FALHAR

Tudo roda num kit sintético numa pasta temporária (apagada no fim); formatos/ e os kits reais nunca são escritos.
Schema: o campo `formato_base` entra no mediakit.schema.json por outra frente. Aqui o schema é carregado em memória e
ganha a definição de `formato_base` só quando ainda não a tem (schema_com_formato_base).
Sai com 1 se alguma prova falhar (ou, com --mutantes, se algum mutante escapar).
"""
import copy, json, os, re, shutil, sys, tempfile, time
from pathlib import Path
from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import formato  # noqa: E402
from formato import ErroFormato  # noqa: E402

EXEMPLO_VALIDO = AQUI.parent / "exemplos" / "travessia-da-lua" / "mediakit.json"
RESULTADOS = []


def teste(fn):
    fn._teste = True
    return fn


def log(*a):
    print("   ", *a, flush=True)


def levanta(fn, trecho, tipo=ErroFormato):
    try:
        fn()
    except tipo as e:
        assert trecho in str(e), f"erro sem `{trecho}`: {e}"
        return str(e)
    raise AssertionError(f"não levantou {tipo.__name__} ({trecho})")


def schema_com_formato_base():
    s = json.loads(formato.SCHEMA_KIT.read_text(encoding="utf-8"))
    s["properties"].setdefault("formato_base", {
        "type": "object", "additionalProperties": False, "required": ["id", "versao", "sha256"],
        "properties": {"id": {"type": "string", "pattern": formato.ID_FORMATO.pattern},
                       "versao": {"type": "integer", "minimum": 1},
                       "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}}})
    return s


# ================================================================================================= kit sintético
ESTILO_FAM = ("photorealistic studio cutout of a single beach sports object, warm low side light from the left, soft "
              "contact shadow to the right, natural materials, no logos, no text, transparent background")
ESTILO_CENA = ("Sunday afternoon in the coast of Bahia, warm low sun from the left at 20 degrees, 35 to 50mm lens, eye "
               "level, light haze, white sand and palm trees, red and white kits, real photograph, no text")


def _pagina_png(p, semente, w=960, h=540):
    im = Image.new("RGB", (w, h), (12 + semente * 9, 14, 18))
    d = ImageDraw.Draw(im)
    for i in range(0, w, 40):
        d.line([(i, 0), (i + 200, h)], fill=(40 + semente * 20, 60, 80), width=6)
    d.rectangle([60, 80, 420, 200], fill=(230, 57, 70))
    d.rectangle([520, 120, 900, 480], fill=(200, 190, 170))
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p)
    return p


def kit_sintetico(base, nome="kit-x"):
    kit = Path(base) / nome
    (kit / "acervo" / "elementos").mkdir(parents=True)
    el = lambda i, **kw: {"id": i, "papel": "heroi", "tipo": "objeto", "formato": "png", "familia": "objeto-praia",
                          "rota": "codex-alfa", "aspecto": "quadrado", "arquivo": f"acervo/elementos/{i}.png", **kw}
    k = {
        "schema_version": "mk-2.0",
        "evento": {"nome": "Copa Teste", "cidade": "Cidade Teste", "local": ""},
        "cotas": [{"nome": "Ouro"}, {"nome": "Prata"}],
        "acervo": [{"id": "logo", "arquivo": "acervo/logo.png", "funcao": "lettering", "direito_uso": True},
                   {"id": "c-capa", "arquivo": "acervo/c-capa.jpg", "funcao": "capa", "direito_uso": True, "gerada": True,
                    "rotulo": "Imagem ilustrativa", "composta": True, "paineis": "compor-capa.json"}],
        "marca": {"logo_id": "logo", "cor_primaria": "#E63946", "cor_secundaria": "#FFD6DA", "direcao": "performance",
                  "assinatura": "fio", "fonte_display": "Barlow Condensed", "fonte_corpo": "Barlow", "estilo_cena": ESTILO_CENA},
        "receitas": [{"id": "r1", "nome": "Domingo de praia", "ideia": "a marca entra na areia",
                      "fontes": {"display": "Barlow Condensed", "peso_display": 800, "titulo": None, "corpo": "Barlow"},
                      "paleta": {"marca": "#E63946", "escuro": "#101012", "papel": "#F4F1E8", "texto": "#FFFFFF", "apoio": "#C9A227"},
                      "fundo": "escuro", "mascara": "reto", "pattern": "conchas", "pattern_paginas": ["divisor"],
                      "variantes": {"capa": "c", "cota": "a"}}],
        "sistema_elementos": {
            "motivos": [{"id": "quadra", "origem": "esporte", "descricao": "as linhas da quadra"},
                        {"id": "rede", "origem": "esporte", "descricao": "a rede"},
                        {"id": "onda", "origem": "simbolo", "descricao": "a onda do logo"},
                        {"id": "orla", "origem": "territorio", "descricao": "a orla da cidade"}],
            "familias": [{"id": "objeto-praia", "meio": "foto-objeto", "estilo": ESTILO_FAM, "luz": "esquerda",
                          "paleta": ["#E63946", "#101012", "#FFFFFF", "#C9A227"], "traco_px": None, "ancora": "bola"}],
            "constantes": [{"tipo": "grao"}, {"tipo": "listras", "exceto": ["capa"], "params": {"cores": ["marca", "escuro"]}}],
            "receitas": {"r1": {"familia": "objeto-praia", "motivos": ["quadra", "rede", "onda"], "pattern": "conchas"}}},
        "elementos": [el("atleta", familia=None, rota="real", aspecto="alto", arquivo="acervo/atleta.png"),
                      el("bola"), el("chinelo", aspecto="largo"),
                      el("conchas", papel="pattern", tipo="pattern")],
        "composicao": {
            "capa": {"mensagem": "a copa abre as cotas na areia", "foco": "lettering", "leitura": ["logo", "atleta", "tese"],
                     "estrutura": "logo no centro e a atleta à direita", "padroes": ["figura-recortada-atravessa-a-borda"],
                     "elementos": [{"id": "atleta", "papel": "heroi", "funcao": "foco", "camada": "atras",
                                    "ancora": {"relacao": "sobrepoe", "alvo": "foto", "lado": "esq", "fracao": "1/3",
                                               "x": "esq=logo.dir+e4"},
                                    "escala": {"altura": "1/2p"}, "porque": "a atleta entra pela faixa"}]},
            "territorio": {"mensagem": "a copa joga na orla", "foco": "grafico", "padroes": ["percurso-e-mapa-como-argumento"],
                           "elementos": [{"id": "mapa", "papel": "heroi", "funcao": "contexto",
                                          "ancora": {"relacao": "alinha", "x": "esq=coluna:7.esq", "y": "cy=corpo.cy"},
                                          "porque": "o mapa prova a orla",
                                          "grafismo": {"tipo": "mapa", "params": {"pontos": [{"nome": "Cidade Teste", "lat": -12.9, "lon": -38.5}],
                                                                                  "aneis": [50]}}}]},
            "ativo:1": {"mensagem": "a bola pousa no título", "foco": "foto", "padroes": ["peca-em-estudio"],
                        "elementos": [{"id": "bola", "papel": "heroi", "funcao": "foco",
                                       "ancora": {"relacao": "alinha", "x": "dir=titulo.dir", "y": "base=titulo.cap-e2"},
                                       "porque": "a bola parada na linha do título"}]},
            "cota:Ouro": {"mensagem": "a cota ouro dá nome à copa", "foco": "preco", "padroes": ["cabecalho-de-cota-e-preco-heroi"],
                          "elementos": [{"id": "bola", "papel": "heroi", "funcao": "identidade",
                                         "ancora": {"relacao": "alinha", "x": "esq=direitos.dir+e5", "y": "base=direitos.base"},
                                         "porque": "a bola da cota ouro"}]},
            "contato": {"mensagem": "fale com a organização", "foco": "titulo", "leitura": ["titulo", "atleta"],
                        "padroes": ["um-motivo-em-varios-papeis"],
                        "elementos": [{"id": "atleta", "papel": "heroi", "funcao": "foco",
                                       "ancora": {"relacao": "sangra", "borda": "base", "corte": "1/4", "x": "dir=bola.esq-e3"},
                                       "escala": {"altura": "1/2p"}, "porque": "a atleta da capa volta"}]}},
    }
    (kit / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (kit / "tema-projeto.css").write_text(":root { --acento-curva: transparent; }\n", encoding="utf-8")
    (kit / "compor-capa.json").write_text('[{"quad": [1,2,3,4,5,6,7,8], "texto": "SEU LOGO AQUI"}]', encoding="utf-8")
    plano = {"paginas": [{"n": 1, "rotulo": "capa:c", "tipo": "capa", "composicao": {"chave": "capa"}},
                         {"n": 2, "rotulo": "territorio", "tipo": "territorio", "composicao": {"chave": "territorio"}},
                         {"n": 3, "rotulo": "ativo:topo", "tipo": "ativo_topo", "composicao": {"chave": "ativo:1"}}]}
    (kit / "saida" / "png").mkdir(parents=True)
    (kit / "saida" / "plano-elementos-r1.json").write_text(json.dumps(plano), encoding="utf-8")
    for i in range(1, 4):
        _pagina_png(kit / "saida" / "png" / f"kit-r1-{i:02d}.png", i)
    for i, desc, aspecto in (("bola", "a beach volleyball, used, sand on it", "Square 1:1 image, 1024x1024 pixels or larger."),
                             ("chinelo", "a pair of rubber flip flops, worn", "Landscape 3:2 image, 1536x1024 pixels or larger.")):
        meta = {"id": i, "tipo": "objeto", "descricao": desc, "estilo": ESTILO_FAM,
                "tratamentos": [{"em": "2026-10-12", "o_que": "espelhado na horizontal", "porque": "luz da direita"}] if i == "bola" else []}
        (kit / "acervo" / "elementos" / f"{i}.meta.json").write_text(json.dumps(meta), encoding="utf-8")
        (kit / "acervo" / "elementos" / f"{i}.prompt.txt").write_text(
            f"Generate one image and save it exactly as {kit}/acervo/elementos/{i}.bruto.png (PNG).\n"
            f"Primary request: one single object: {desc}\nSubject: {desc}\nTheme: praia (a visual theme, never written)\n"
            f"Style/medium: {ESTILO_FAM}\nComposition/framing: {aspecto}\n"
            f"Perspective: turned slightly toward the {'right' if i == 'bola' else 'upper left'}.\n"
            "Color palette: vivid red as the dominant color, with black, white; no other hues.\n"
            "Avoid: text of any kind.\n", encoding="utf-8")
    (kit / "acervo" / "c-capa.prompt.txt").write_text(
        "Photorealistic editorial sports photography. Scene: a beach court at the end of the afternoon. Camera: 35mm lens at "
        f"f/2.8, eye level. Light: {ESTILO_CENA}. Location: Cidade Teste, Brazil; local landmarks when natural. "
        "Composition (from the page layout): the photo fills the page. Constraints: a real photograph, no text.\n", encoding="utf-8")
    hist = Path(base) / "historico.json"
    hist.write_text(json.dumps([{"id": nome, "pasta": f"CLIENTES/TESTE/{nome}",
                                 "padroes": {p: [] for p in ("cabecalho-de-cota-e-preco-heroi", "figura-recortada-atravessa-a-borda",
                                                             "peca-em-estudio", "percurso-e-mapa-como-argumento",
                                                             "um-motivo-em-varios-papeis")}}]), encoding="utf-8")
    return kit, hist


class Cena:
    """Pasta temporária com kit sintético, histórico e formatos/ próprios."""
    def __enter__(self):
        self.d = Path(tempfile.mkdtemp(prefix="mk-teste-formato-"))
        self.kit, self.hist = kit_sintetico(self.d)
        self.raiz = self.d / "formatos"
        return self

    def exportar(self, fid="formato-teste", **kw):
        return formato.exportar(self.kit, fid, raiz=self.raiz, historico=self.hist, **kw)

    def __exit__(self, *a):
        shutil.rmtree(self.d, ignore_errors=True)


def _arvore(pasta):
    return {str(p.relative_to(pasta)): formato.sha256_arq(p) for p in sorted(Path(pasta).rglob("*")) if p.is_file()}


# ================================================================================================= provas
@teste
def exportar_separa_travado_e_trocar():
    with Cena() as c:
        pasta, f = c.exportar()
        T = f["travado"]
        assert "id" not in T["receita"] and T["receita"]["nome"] == "Domingo de praia", T["receita"]
        assert set(T["receita"]["paleta"]) == {"escuro", "papel", "texto"}, T["receita"]["paleta"]
        assert [m["id"] for m in T["motivos"]] == ["quadra", "rede"], T["motivos"]
        assert T["receita_elementos"]["motivos"] == ["quadra", "rede"], T["receita_elementos"]
        assert T["constantes"][1]["params"]["cores"] == ["marca", "escuro"]
        assert T["marca"] == {"direcao": "performance", "assinatura": "fio", "fonte_display": "Barlow Condensed", "fonte_corpo": "Barlow"}
        fm = T["familia_modelo"]
        assert fm["paleta"] == ["marca", "escuro", "texto", "apoio"] and fm["luz"] == "esquerda", fm
        assert "{assunto}" in fm["estilo"] and "{material}" in fm["estilo"] and "beach" not in fm["estilo"], fm["estilo"]
        assert T["direcao_criativa"] == {"intensidade": {"padrao": 1, "teto": 2}, "recursos": []}, T["direcao_criativa"]
        assert T["tema_projeto_css"]["sha256"] == formato.sha256_arq(c.kit / "tema-projeto.css")
        assert len(T["padroes"]) == 5, T["padroes"]
        troca = {t["id"]: t for t in f["trocar"]}
        assert set(troca) == {"paleta-marca", "paleta-apoio", "motivo-onda", "motivo-orla", "estilo-cena", "logo"}, set(troca)
        assert troca["paleta-marca"]["na_origem"]["receitas[].paleta.marca"] == "#E63946"
        mod = troca["estilo-cena"]["modelo"]
        assert all(l in mod for l in ("{momento}", "{lugar}", "{material}", "{cores}")), mod
        assert not any(x in mod for x in ("Sunday", "Bahia", "white sand", "red and white")), mod
        assert set(T["gramatica"]) == {"capa", "territorio", "contato"}, set(T["gramatica"])
        assert set(f["exemplos"]) == {"ativo:1", "cota:Ouro"}, set(f["exemplos"])
        nt = f["nao_tem"]
        assert "direcao_criativa" in nt["acabamento_v9"] and "elementos[].material" in nt["acabamento_v9"], nt
        assert "fio-que-organiza-a-informacao" in nt["padroes_do_repertorio"], nt["padroes_do_repertorio"]
        assert isinstance(nt["tipos_de_pagina"], str) or "cota" in nt["tipos_de_pagina"], nt["tipos_de_pagina"]
        assert any(t.get("elemento") == "{objeto-ativo-1}" and "espelhado" in t["o_que"] for t in f["tratamentos"]), f["tratamentos"]
        assert any(t.get("acervo") == "c-capa" and (t.get("paineis") or {}).get("quantos") == 1 for t in f["tratamentos"])
        assert (pasta / "versoes" / "v1.json").read_bytes() == (pasta / "formato.json").read_bytes()
        for rel, sha in f["arquivos"].items():
            assert formato.sha256_arq(pasta / rel) == sha, rel
        log(f"travado sem marca nem apoio; trocar {sorted(troca)}; {len(f['arquivos'])} arquivos com sha256")


@teste
def gramatica_troca_ids_por_papeis():
    with Cena() as c:
        _, f = c.exportar()
        G, P = f["travado"]["gramatica"], f["papeis"]
        assert G["capa"]["elementos"][0]["id"] == "{heroi-capa}", G["capa"]["elementos"][0]
        assert G["capa"]["leitura"] == ["logo", "{heroi-capa}", "tese"], G["capa"]["leitura"]
        assert G["contato"]["elementos"][0]["id"] == "{heroi-capa}", "o mesmo elemento em duas páginas é o mesmo papel"
        assert G["contato"]["elementos"][0]["ancora"]["x"] == "dir={objeto-ativo-1}.esq-e3", G["contato"]["elementos"][0]["ancora"]
        assert f["exemplos"]["cota:Ouro"]["elementos"][0]["id"] == "{objeto-ativo-1}"
        assert f["travado"]["receita"]["pattern"] == "{pattern-divisor}"
        assert f["travado"]["familia_modelo"]["ancora"] == "{objeto-ativo-1}"
        params = G["territorio"]["elementos"][0]["grafismo"]["params"]
        assert params == {"pontos": "{pontos}", "aneis": [50]}, params
        assert P["heroi-capa"]["origem"] == "atleta" and P["heroi-capa"]["aparece_em"] == ["capa", "contato"], P["heroi-capa"]
        assert P["objeto-livre-1"]["origem"] == "chinelo", sorted(P)
        estrut = json.dumps([formato.estrutural(e) for e in G.values()], ensure_ascii=False)
        sobra = re.findall(r'"(atleta|bola|chinelo|conchas)"|=(atleta|bola|chinelo|conchas)\.', estrut)
        assert not sobra, f"id do cliente ficou na gramática: {sobra}"
        log("ids viraram papéis no id, na âncora, na leitura, na receita e na família; conteúdo do mapa virou lacuna")


@teste
def aplicar_preenche_so_ausente_e_grava_formato_base():
    import jsonschema
    with Cena() as c:
        pasta, f = c.exportar()
        novo = c.d / "kit-novo"
        (novo / "fontes").mkdir(parents=True)
        k0 = json.loads(EXEMPLO_VALIDO.read_text(encoding="utf-8"))
        del k0["marca"]["assinatura"]
        direcao = k0["marca"]["direcao"]
        (novo / "mediakit.json").write_text(json.dumps(k0, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (novo / "fontes" / "Barlow.ttf").write_bytes(b"fonte do kit")
        r = formato.aplicar("formato-teste", novo, raiz=c.raiz)
        k = json.loads((novo / "mediakit.json").read_text(encoding="utf-8"))
        assert k["marca"]["direcao"] == direcao, "o kit vence: direcao não pode mudar"
        assert k["marca"]["assinatura"] == "fio", "assinatura ausente vem do formato"
        assert k["marca"]["fonte_display"] == k0["marca"]["fonte_display"], "fonte do kit vence"
        rec = k["receitas"][0]
        assert rec["id"] == "r1" and rec["fontes"]["display"] == "Barlow Condensed" and rec["mascara"] == "reto", rec
        assert "marca" not in rec["paleta"] and rec["paleta"]["escuro"] == "#101012", rec["paleta"]
        assert k["composicao"]["capa"]["elementos"][0]["id"] == "{heroi-capa}"
        assert k["composicao"]["capa"]["mensagem"] == "{mensagem}" and "ativo:1" not in k["composicao"]
        assert [m["id"] for m in k["sistema_elementos"]["motivos"]] == ["quadra", "rede"]
        assert k["direcao_criativa"]["intensidade"] == {"padrao": 1, "teto": 2}
        sha = formato.sha256_arq(pasta / "formato.json")
        assert k["formato_base"] == {"id": "formato-teste", "versao": 1, "sha256": sha}, k["formato_base"]
        sch = schema_com_formato_base()
        jsonschema.Draft202012Validator({**sch["properties"]["formato_base"]}).validate(k["formato_base"])
        k2 = copy.deepcopy(k)
        k2["receitas"][0]["paleta"]["marca"] = "#123456"       # a pendência de trocar resolvida
        erros = [e.message for e in jsonschema.Draft202012Validator(sch).iter_errors(k2)]
        assert not erros, erros
        assert (novo / "tema-projeto.css").read_bytes() == (c.kit / "tema-projeto.css").read_bytes()
        assert (novo / "fontes" / "Barlow Condensed__800.ttf").exists()
        assert (novo / "fontes" / "Barlow.ttf").read_bytes() == b"fonte do kit", "fonte do kit não é sobrescrita"
        assert json.loads((novo / "mediakit.antes-do-formato.json").read_text(encoding="utf-8")) == k0
        pend = (novo / "pendencias.md").read_text(encoding="utf-8")
        for trecho in ("paleta.marca", "paleta.apoio", "motivos[onda]", "motivos[orla]", "estilo_cena", "`marca.logo_id`",
                       "{heroi-capa}", "{pattern-divisor}", "prosa da composição"):
            assert trecho in pend, f"pendência sem {trecho}"
        antes = (novo / "mediakit.json").read_bytes(), pend
        r2 = formato.aplicar("formato-teste", novo, raiz=c.raiz)
        assert r2["pendencias"] == [] and (novo / "pendencias.md").read_text(encoding="utf-8") == antes[1], "reaplicar duplicou"
        assert json.loads((novo / "mediakit.json").read_bytes()) == json.loads(antes[0])
        log(f"{len(r['preenchidos'])} chaves preenchidas, o kit venceu nas outras; formato_base válido no schema em memória")


@teste
def fio_condutor_viaja_em_trocar_e_e_herdado():
    """O fio condutor veste um motivo do cliente, então sai em `trocar`; o `aplicar` só o copia quando o kit novo
    ainda não tem fio (cliente que volta com o mesmo formato). Kit com fio próprio fica como está."""
    fio = {"motivo": "quadra", "papeis": {"capa": "contrapeso", "divisor": "selo", "contato": "contrapeso"}}
    with Cena() as c:
        mk = c.kit / "mediakit.json"
        k0 = json.loads(mk.read_text(encoding="utf-8"))
        k0.setdefault("direcao_criativa", {})["fio_condutor"] = copy.deepcopy(fio)
        mk.write_text(json.dumps(k0, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        pasta, f = c.exportar()
        item = next((t for t in f["trocar"] if t["id"] == "fio-condutor"), None)
        assert item and item["na_origem"]["direcao_criativa.fio_condutor"] == fio, f["trocar"]
        assert "fio_condutor" not in f["travado"]["direcao_criativa"], "o fio não é travado: é do cliente"
        for nome, com_fio in (("kit-sem-fio", False), ("kit-com-fio", True)):
            novo = c.d / nome
            (novo / "fontes").mkdir(parents=True)
            kn = json.loads(EXEMPLO_VALIDO.read_text(encoding="utf-8"))
            if com_fio:
                kn["direcao_criativa"] = {"fio_condutor": {"motivo": "proprio", "papeis": {"capa": "selo"}}}
            (novo / "mediakit.json").write_text(json.dumps(kn, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            formato.aplicar("formato-teste", novo, raiz=c.raiz)
            k = json.loads((novo / "mediakit.json").read_text(encoding="utf-8"))
            if com_fio:
                assert k["direcao_criativa"]["fio_condutor"]["motivo"] == "proprio", "fio do kit vence"
            else:
                assert k["direcao_criativa"]["fio_condutor"] == fio, k.get("direcao_criativa")
        log("fio em trocar; herdado só no kit sem fio")


@teste
def conferir_acusa_diferenca():
    with Cena() as c:
        c.exportar()
        r = formato.conferir(c.kit, "formato-teste", raiz=c.raiz)
        assert r["diferencas"] == [] and r["lacunas"] == [], r
        k = json.loads((c.kit / "mediakit.json").read_text(encoding="utf-8"))
        k["receitas"][0]["mascara"] = "diagonal"
        k["composicao"]["capa"]["elementos"][0]["ancora"]["fracao"] = "1/2"
        k["composicao"]["contato"]["mensagem"] = "outra frase, prosa não conta"
        k["sistema_elementos"]["familias"][0]["estilo"] = ESTILO_FAM.replace("natural materials", "worn rubber")
        k["composicao"]["territorio"]["estrutura"] = "{estrutura}"
        (c.kit / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False), encoding="utf-8")
        (c.kit / "tema-projeto.css").unlink()
        r = formato.conferir(c.kit, "formato-teste", raiz=c.raiz)
        caminhos = sorted(d[0] for d in r["diferencas"])
        assert caminhos == ["composicao.capa.elementos", "receita.mascara", "tema_projeto_css"], caminhos
        assert r["lacunas"] == [("composicao.territorio.estrutura", "{estrutura}")], r["lacunas"]
        log(f"acusou {caminhos}; prosa e material trocado no estilo não contam; lacuna aberta listada")


@teste
def assinatura_acusa_pagina_alterada():
    d = Path(tempfile.mkdtemp(prefix="mk-teste-assinatura-"))
    try:
        png = d / "png"
        for i in range(1, 4):
            _pagina_png(png / f"kit-r1-{i:02d}.png", i)
        ass = {"padrao": "kit-r1-*.png", "paginas": [{"arquivo": p.name, **formato.assinatura_da_pagina(p)[1]}
                                                    for p in sorted(png.glob("*.png"))]}
        assert [e for _, e, _ in formato.comparar_assinatura(ass, png)] == ["igual"] * 3
        im = Image.open(png / "kit-r1-02.png"); im.load()
        from PIL import PngImagePlugin
        info = PngImagePlugin.PngInfo(); info.add_text("render", "outro")
        im.save(png / "kit-r1-02.png", compress_level=1, pnginfo=info)        # mesmos pixels, outros bytes
        im = Image.open(png / "kit-r1-03.png").convert("RGB")
        ImageDraw.Draw(im).rectangle([700, 40, 724, 64], fill=(250, 250, 40))  # 24 px numa página de 960
        im.save(png / "kit-r1-03.png")
        res = {a: (e, det) for a, e, det in formato.comparar_assinatura(ass, png)}
        assert res["kit-r1-01.png"][0] == "igual" and res["kit-r1-02.png"][0] == "dentro", res
        assert res["kit-r1-03.png"][0] == "diferente", res
        (png / "kit-r1-01.png").unlink()
        _pagina_png(png / "kit-r1-04.png", 4)
        res = {a: e for a, e, _ in formato.comparar_assinatura(ass, png)}
        assert res["kit-r1-01.png"] == "falta" and res["kit-r1-04.png"] == "a mais", res
        log(f"mesmos pixels = dentro; quadrado de 24 px = {res['kit-r1-03.png']}; página sumida e página nova acusadas")
    finally:
        shutil.rmtree(d, ignore_errors=True)


@teste
def recusa_sobrescrever_versao():
    with Cena() as c:
        pasta, f1 = c.exportar()
        antes = _arvore(pasta)
        levanta(lambda: c.exportar(), "imutável")
        assert _arvore(pasta) == antes, "o export recusado mexeu no formato"
        assert not [p for p in c.raiz.iterdir() if p.name.startswith(".")], "sobrou pasta temporária"
        levanta(lambda: formato.gravar_novo(pasta / "formato.json", b"x"), "imutável")
        k = json.loads((c.kit / "mediakit.json").read_text(encoding="utf-8"))
        k["receitas"][0]["mascara"] = "diagonal"
        (c.kit / "mediakit.json").write_text(json.dumps(k, ensure_ascii=False), encoding="utf-8")
        _, f2 = c.exportar(nova_versao=True)
        depois = _arvore(pasta)
        assert all(depois[r] == s for r, s in antes.items() if r != "formato.json"), "a v1 mudou"
        assert f2["versao"] == 2 and all(r.startswith("versoes/v2/") for r in f2["arquivos"]), list(f2["arquivos"])[:3]
        assert (pasta / "formato.json").read_bytes() == (pasta / "versoes" / "v2.json").read_bytes()
        assert json.loads((pasta / "versoes" / "v1.json").read_text(encoding="utf-8")) == f1
        novo = c.d / "kit-v1"; novo.mkdir()
        (novo / "mediakit.json").write_text("{}", encoding="utf-8")
        assert formato.aplicar("formato-teste", novo, versao=1, raiz=c.raiz)["formato_base"]["versao"] == 1
        log("segundo export recusado sem tocar em nada; --nova-versao grava versoes/v2 e a v1 segue aplicável")


@teste
def caminho_fora_recusado():
    with Cena() as c:
        for ruim in ("../fora", "A-maiuscula", "a", "x" * 42, "com espaco", "", None):
            levanta(lambda: formato.pasta_formato(ruim, c.raiz), "id de formato inválido")
        fora = c.d / "fora"; fora.mkdir()
        c.raiz.mkdir(exist_ok=True)
        os.symlink(fora, c.raiz / "link-fora")
        levanta(lambda: formato.pasta_formato("link-fora", c.raiz), "sai da pasta")
        segredo = c.d / "segredo.meta.json"
        segredo.write_text('{"id": "segredo", "descricao": "não pode entrar"}', encoding="utf-8")
        os.symlink(segredo, c.kit / "acervo" / "elementos" / "segredo.meta.json")
        levanta(lambda: c.exportar("formato-link"), "sai da pasta")
        assert not (c.raiz / "formato-link").exists()
        (c.kit / "acervo" / "elementos" / "segredo.meta.json").unlink()
        pasta, _ = c.exportar()
        f = json.loads((pasta / "formato.json").read_text(encoding="utf-8"))
        f["para_o_kit"]["tema-projeto.css"] = "../../segredo.meta.json"
        (pasta / "formato.json").write_text(json.dumps(f), encoding="utf-8")
        novo = c.d / "kit-novo"; novo.mkdir()
        (novo / "mediakit.json").write_text("{}", encoding="utf-8")
        levanta(lambda: formato.aplicar("formato-teste", novo, raiz=c.raiz), "sai da pasta")
        ass = {"paginas": [{"arquivo": "../segredo.meta.json", "sha256": "0"}]}
        levanta(lambda: formato.comparar_assinatura(ass, c.kit / "saida" / "png"), "sai da pasta")
        log("id fora do padrão, link de formatos/ e do acervo para fora, caminho do formato.json e da assinatura: recusados")


@teste
def prompts_modelo_sem_cliente_e_sem_caminho():
    with Cena() as c:
        pasta, f = c.exportar()
        cena = (pasta / "prompts" / "cena.modelo.txt").read_text(encoding="utf-8")
        for l in ("{assunto}", "{momento}", "{lugar}", "{material}", "{composicao}"):
            assert l in cena, f"modelo de cena sem {l}: {cena}"
        for x in ("Sunday", "Bahia", "Cidade Teste", "white sand", "beach court"):
            assert x not in cena, f"o modelo de cena carrega `{x}`"
        obj = (pasta / "prompts" / "objeto.modelo.txt").read_text(encoding="utf-8")
        for l in ("{assunto}", "{material}", "{arquivo}", "{rumo}", "{cores}", "Composition/framing: {enquadramento}"):
            assert l in obj, f"modelo de objeto sem {l}: {obj}"
        assert "volleyball" not in obj and "flip flops" not in obj
        for rel in [r for r in f["arquivos"] if r.endswith(".txt")]:
            t = (pasta / rel).read_text(encoding="utf-8")
            assert str(c.kit) not in t and "/Users/" not in t, f"caminho do Mac em {rel}"
        ex = (pasta / "prompts" / "exemplos" / "bola.prompt.txt").read_text(encoding="utf-8")
        assert "<kit>/acervo/elementos/bola.bruto.png" in ex and "beach volleyball" in ex
        log("modelos com lacunas e sem dado do cliente; exemplos reais sem caminho do Mac")


# ================================================================================================= mutantes
def _sem_troca(o, nomes, rx=None):
    return copy.deepcopy(o)


def _preenche_sobrescrevendo(destino, origem, caminho, preenchidos):
    for c, v in origem.items():
        destino[c] = copy.deepcopy(v)
        preenchidos.append(f"{caminho}.{c}")


MUTANTES = {
    "exportar_separa_travado_e_trocar": ("PALETA_FIXA", ("escuro", "papel", "texto", "marca", "apoio")),
    "gramatica_troca_ids_por_papeis": ("trocar_ids", _sem_troca),
    "aplicar_preenche_so_ausente_e_grava_formato_base": ("preencher_ausente", _preenche_sobrescrevendo),
    "conferir_acusa_diferenca": ("_diff", lambda a, b, caminho, out: None),
    "assinatura_acusa_pagina_alterada": ("LIMIAR_BLOCO", 1e9),
    "recusa_sobrescrever_versao": ("versao_nova", lambda pasta, nova: (1, "")),
    "caminho_fora_recusado": ("dentro_do_kit", lambda base, rel: Path(base) / str(rel)),
    "prompts_modelo_sem_cliente_e_sem_caminho": ("estilo_cena_modelo", lambda e: (e, {})),
}


def main():
    testes = [(n, f) for n, f in globals().items() if callable(f) and getattr(f, "_teste", False)]
    nomes = [a for a in sys.argv[1:] if not a.startswith("--")]
    if nomes:
        testes = [(n, f) for n, f in testes if n in nomes]
    if "--mutantes" in sys.argv:
        escapou = 0
        for n, f in testes:
            attr, mut = MUTANTES[n]
            orig = getattr(formato, attr)
            setattr(formato, attr, mut)
            try:
                f()
                escapou += 1
                print(f"ESCAPOU   {n}  (mutante {attr} passou: a prova não pega o defeito)", flush=True)
            except Exception as e:
                print(f"PEGO      {n}  (mutante {attr}): {type(e).__name__}: {str(e)[:160]}", flush=True)
            finally:
                setattr(formato, attr, orig)
        print(f"\n{len(testes) - escapou} de {len(testes)} mutantes pegos")
        sys.exit(1 if escapou else 0)
    falhou = 0
    for n, f in testes:
        t0 = time.time()
        try:
            f()
            print(f"OK      {n}  ({time.time() - t0:.1f} s)", flush=True)
        except Exception as e:
            falhou += 1
            print(f"FALHOU  {n}  ({time.time() - t0:.1f} s): {type(e).__name__}: {str(e)[:1200]}", flush=True)
    print(f"\n{len(testes) - falhou} de {len(testes)} testes passaram")
    sys.exit(1 if falhou else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
fontes_livres.py — biblioteca de fontes livres (SIL OFL: Google Fonts e Collletttivo) para os kits.

Uso:
  python3 fontes_livres.py baixar [--so Anton,Archivo]          # baixa o catálogo abaixo em ../fontes-livres/<Familia>/
  python3 fontes_livres.py listar                                # o que já está na biblioteca, com pesos
  python3 fontes_livres.py para <pasta-do-kit>/fontes Anton "DM Sans"   # copia só as famílias que o kit usa
  python3 fontes_livres.py catalogo                              # regrava ../catalogos/fontes.json (pesos e acentos lidos dos arquivos)

Fonte variável vira instância estática por peso (variável no Chromium exporta Type 3 no PDF): cada peso é um arquivo
`Familia__700.ttf`, que o render.py registra como peso 700 da família `Familia`. Larguras diferentes (Archivo Expanded)
viram família própria. A licença OFL.txt de cada família fica junto dos arquivos.
Fontshare (ITF-FFL) NÃO entra: a licença proíbe converter, instanciar, renomear e redistribuir o arquivo (ver fontes-livres/LICENCAS.md).
Fonte licenciada (RocGrotesk) e fonte de cliente NÃO entram aqui: ficam na pasta do cliente.
"""
import argparse, json, os, re, shutil, sys, urllib.request
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

AQUI = Path(__file__).resolve().parent
BIB = AQUI.parent / "fontes-livres"
API = "https://api.github.com/repos/google/fonts/contents/ofl/"
RAW = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
PESOS = [400, 500, 600, 700, 800, 900]

# família: (pasta no repo, uso na gramática, eixos fixos além do peso)
CATALOGO = {
    # display larga (direção causa, alternativa à RocGrotesk Wide)
    "Archivo Expanded": ("archivo", "display larga", {"wdth": 125}),
    "Archivo": ("archivo", "corpo e título", {"wdth": 100}),
    "Archivo Black": ("archivoblack", "display larga", {}),
    "Bricolage Grotesque": ("bricolagegrotesque", "display larga", {"wdth": 100, "opsz": 48}),
    "Unbounded": ("unbounded", "display larga", {}),
    "Syne": ("syne", "display", {}),
    # condensada (direções performance e território)
    "Anton": ("anton", "display condensada", {}),
    "Antonio": ("antonio", "display condensada", {}),
    "Bebas Neue": ("bebasneue", "display condensada", {}),
    "Oswald": ("oswald", "display condensada", {}),
    "Big Shoulders Display": ("bigshouldersdisplay", "display condensada", {}),
    "Barlow Condensed": ("barlowcondensed", "título condensado", {}),
    "Teko": ("teko", "display condensada", {}),
    # corpo
    "Montserrat": ("montserrat", "corpo", {}),
    "DM Sans": ("dmsans", "corpo", {"opsz": 14}),
    "Inter": ("inter", "corpo", {"opsz": 14}),
    "Manrope": ("manrope", "corpo", {}),
    "Plus Jakarta Sans": ("plusjakartasans", "corpo", {}),
    "Work Sans": ("worksans", "corpo", {}),
    "Barlow": ("barlow", "corpo", {}),
    # serifa (variante festa premium, Saudade)
    "Fraunces": ("fraunces", "serifa display", {"opsz": 72, "SOFT": 0, "WONK": 0}),
    "Playfair Display": ("playfairdisplay", "serifa display", {}),
    "DM Serif Display": ("dmserifdisplay", "serifa display", {}),
    "Instrument Serif": ("instrumentserif", "serifa display", {}),
    "Cormorant Garamond": ("cormorantgaramond", "serifa corpo", {}),
    # --- ampliação da cartela (frente fontes, 09/10/2026) ---
    # condensada
    "Fjalla One": ("fjallaone", "display condensada", {}),
    "League Gothic": ("leaguegothic", "display condensada", {"wdth": 100}),
    "Saira Condensed": ("sairacondensed", "display condensada", {}),
    "Saira Extra Condensed": ("sairaextracondensed", "display condensada", {}),
    "Sofia Sans Extra Condensed": ("sofiasansextracondensed", "display condensada", {}),
    "Staatliches": ("staatliches", "display condensada", {}),
    # larga e tecnológica
    "Krona One": ("kronaone", "display larga", {}),
    "Michroma": ("michroma", "display larga", {}),
    "Lexend Zetta": ("lexendzetta", "display larga", {}),
    "Anybody Expanded": ("anybody", "display larga", {"wdth": 150}),
    "Bungee": ("bungee", "display larga", {}),
    "Rubik Mono One": ("rubikmonoone", "display larga", {}),
    "Russo One": ("russoone", "display", {}),
    "Tomorrow": ("tomorrow", "display e corpo técnico", {}),
    "Kanit": ("kanit", "display e corpo", {}),
    # grotescas de corpo e título
    "Sora": ("sora", "corpo e título", {}),
    "Outfit": ("outfit", "corpo e título", {}),
    "Lexend": ("lexend", "corpo", {}),
    "Red Hat Display": ("redhatdisplay", "corpo e título", {}),
    "Epilogue": ("epilogue", "corpo e título", {}),
    "Space Grotesk": ("spacegrotesk", "corpo e título", {}),
    "Familjen Grotesk": ("familjengrotesk", "corpo e título", {}),
    "Hanken Grotesk": ("hankengrotesk", "corpo", {}),
    "Schibsted Grotesk": ("schibstedgrotesk", "corpo e título", {}),
    "Instrument Sans": ("instrumentsans", "corpo", {"wdth": 100}),
    "Onest": ("onest", "corpo", {}),
    "Rubik": ("rubik", "corpo e título", {}),
    # serifa
    "Gloock": ("gloock", "serifa display", {}),
    "Young Serif": ("youngserif", "serifa display", {}),
    "Bodoni Moda": ("bodonimoda", "serifa display", {"opsz": 28}),
    "Libre Caslon Display": ("librecaslondisplay", "serifa display", {}),
    "Alfa Slab One": ("alfaslabone", "serifa display", {}),
    "Lora": ("lora", "serifa corpo", {}),
    # personalidade
    "Abril Fatface": ("abrilfatface", "serifa display", {}),
    "Shrikhand": ("shrikhand", "display festa", {}),
    "Pacifico": ("pacifico", "display retrô", {}),
    "Bowlby One": ("bowlbyone", "display", {}),
    "Fredoka": ("fredoka", "display arredondada", {"wdth": 100}),
}

# fora do repositório do Google: família -> (origem, repositório no GitHub, arquivos .ttf no repo, arquivo de licença)
OUTRAS_ORIGENS = {
    "Mattone": ("collletttivo", "Collletttivo/mattone",
                ["fonts/Mattone-Regular.ttf", "fonts/Mattone-Bold.ttf", "fonts/Mattone-Black.ttf"], "LICENSE.txt"),
}
for _f in OUTRAS_ORIGENS:
    CATALOGO[_f] = ("", "display larga", {})

# metadados da cartela: família -> (papel, largura, humor). Vira catalogos/fontes.json (o contrato com as outras frentes).
_E, _U, _F, _N, _L, _R, _C, _T, _P = "esporte", "urbano", "festa", "natureza", "luxo", "retro", "causa", "tecnologia", "praia"
META = {
    "Archivo Expanded": (["display"], "larga", [_E, _U, _C]),
    "Archivo": (["corpo", "display"], "normal", [_E, _U, _C]),
    "Archivo Black": (["display"], "larga", [_E, _U]),
    "Bricolage Grotesque": (["display", "corpo"], "normal", [_F, _U, _C]),
    "Unbounded": (["display"], "larga", [_T, _F, _U]),
    "Syne": (["display"], "larga", [_U, _F, _L]),
    "Anton": (["display"], "condensada", [_E, _U]),
    "Antonio": (["display"], "condensada", [_E, _U, _C]),
    "Bebas Neue": (["display"], "condensada", [_E, _U, _F]),
    "Oswald": (["display", "corpo"], "condensada", [_E, _N, _C]),
    "Big Shoulders Display": (["display"], "condensada", [_E, _U, _C]),
    "Barlow Condensed": (["display", "corpo"], "condensada", [_E, _U, _T]),
    "Teko": (["display"], "condensada", [_E, _T, _U]),
    "Montserrat": (["corpo", "display"], "normal", [_U, _P, _C]),
    "DM Sans": (["corpo"], "normal", [_C, _P, _T]),
    "Inter": (["corpo"], "normal", [_T, _U, _C]),
    "Manrope": (["corpo"], "normal", [_T, _L, _C]),
    "Plus Jakarta Sans": (["corpo", "display"], "normal", [_F, _P, _C, _L]),
    "Work Sans": (["corpo"], "normal", [_E, _N, _U]),
    "Barlow": (["corpo"], "normal", [_E, _U, _N]),
    "Fraunces": (["serifa", "display"], "normal", [_L, _N, _F, _R]),
    "Playfair Display": (["serifa", "display"], "normal", [_L, _R]),
    "DM Serif Display": (["serifa", "display"], "normal", [_L, _F]),
    "Instrument Serif": (["serifa", "display"], "condensada", [_L, _C]),
    "Cormorant Garamond": (["serifa", "corpo"], "normal", [_L, _N]),
    "Fjalla One": (["display"], "condensada", [_E, _U, _N]),
    "League Gothic": (["display"], "condensada", [_E, _U, _C]),
    "Saira Condensed": (["display", "corpo"], "condensada", [_E, _T, _U]),
    "Saira Extra Condensed": (["display"], "condensada", [_E, _T]),
    "Sofia Sans Extra Condensed": (["display"], "condensada", [_E, _U, _P]),
    "Staatliches": (["display"], "condensada", [_R, _U, _F]),
    "Krona One": (["display"], "larga", [_T, _L, _U]),
    "Michroma": (["display"], "larga", [_T, _E]),
    "Lexend Zetta": (["display"], "larga", [_T, _C, _E]),
    "Anybody Expanded": (["display"], "larga", [_E, _F, _U]),
    "Bungee": (["display"], "larga", [_U, _F, _R]),
    "Rubik Mono One": (["display"], "larga", [_F, _U]),
    "Russo One": (["display"], "normal", [_E, _T]),
    "Tomorrow": (["display", "corpo"], "normal", [_T, _E]),
    "Kanit": (["display", "corpo"], "normal", [_E, _U, _P]),
    "Sora": (["corpo", "display"], "normal", [_T, _C, _P]),
    "Outfit": (["corpo", "display"], "normal", [_P, _C, _T]),
    "Lexend": (["corpo"], "normal", [_C, _E, _N]),
    "Red Hat Display": (["corpo", "display"], "normal", [_C, _L, _P]),
    "Epilogue": (["corpo", "display"], "normal", [_U, _F, _C]),
    "Space Grotesk": (["corpo", "display"], "normal", [_T, _U, _F]),
    "Familjen Grotesk": (["corpo", "display"], "normal", [_N, _C, _U]),
    "Hanken Grotesk": (["corpo"], "normal", [_C, _N, _L]),
    "Schibsted Grotesk": (["corpo", "display"], "normal", [_U, _E, _C]),
    "Instrument Sans": (["corpo"], "normal", [_L, _U, _T]),
    "Onest": (["corpo"], "normal", [_C, _T, _P]),
    "Rubik": (["corpo", "display"], "normal", [_F, _P, _U]),
    "Gloock": (["serifa", "display"], "normal", [_L, _R, _N]),
    "Young Serif": (["serifa", "display"], "normal", [_N, _C, _R]),
    "Bodoni Moda": (["serifa", "display"], "normal", [_L, _F]),
    "Libre Caslon Display": (["serifa", "display"], "normal", [_L, _R]),
    "Alfa Slab One": (["serifa", "display"], "larga", [_R, _E, _U]),
    "Lora": (["serifa", "corpo"], "normal", [_N, _C, _L]),
    "Abril Fatface": (["serifa", "display"], "normal", [_R, _F, _L]),
    "Shrikhand": (["display"], "larga", [_F, _P, _R]),
    "Pacifico": (["display"], "normal", [_P, _R, _F]),
    "Bowlby One": (["display"], "larga", [_E, _F, _R]),
    "Fredoka": (["display", "corpo"], "normal", [_C, _P, _F]),
    "Mattone": (["display"], "larga", [_U, _T, _E]),
}
ORIGEM_LICENCA = {"google": "OFL", "collletttivo": "OFL", "velvetyne": "OFL", "fontshare": "ITF-FFL"}
ACENTOS = "ÁÀÂÃÉÊÍÓÔÕÚÇáàâãéêíóôõúç"


def _cabecalhos():
    h = {"User-Agent": "gerar-mediakit-motion"}
    if os.environ.get("GITHUB_TOKEN"):  # sem token a API do GitHub limita a 60 consultas por hora
        h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    return h


def baixar_url(url, dest):
    req = urllib.request.Request(url, headers=_cabecalhos())
    with urllib.request.urlopen(req, timeout=60) as r:
        dest.write_bytes(r.read())


def nomear(f, familia, peso):
    """Nome interno coerente (o PDF mostra este nome; instância de variável herda 'Thin' se não renomear)."""
    estilo = {400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold", 900: "Black"}.get(peso, str(peso))
    ps = f"{familia}-{estilo}".replace(" ", "")
    n = f["name"]
    for nid in (1, 2, 3, 4, 6, 16, 17, 25):
        n.removeNames(nameID=nid)
    for nid, v in [(1, familia), (2, "Regular"), (3, ps), (4, f"{familia} {estilo}"), (6, ps)]:
        n.setName(v, nid, 3, 1, 0x409)
    if "OS/2" in f:
        f["OS/2"].usWeightClass = peso


def _salvar_instancias(tmp, familia, fixos, destino, feitos):
    """Variável vira um arquivo estático por peso; estático vira Familia__peso.ttf (400 sem sufixo)."""
    f = TTFont(tmp)
    eixos = {a.axisTag: (a.minValue, a.maxValue, a.defaultValue) for a in f["fvar"].axes}
    lo, hi, _ = eixos.get("wght", (400, 400, 400))
    for peso in PESOS:
        if not lo <= peso <= hi:
            continue
        loc = {ax: d for ax, (mn, mx, d) in eixos.items()}
        if "wght" in eixos:
            loc["wght"] = peso
        for ax, v in fixos.items():
            if ax in eixos:
                loc[ax] = max(eixos[ax][0], min(eixos[ax][1], v))
        inst = instantiateVariableFont(TTFont(tmp), loc)
        nomear(inst, familia, peso)
        inst.save(destino / (f"{familia}.ttf" if peso == 400 else f"{familia}__{peso}.ttf"))
        feitos.append(peso)


def _salvar_estatica(tmp, familia, destino, feitos, unico):
    f = TTFont(tmp)
    peso = 400 if unico else (f["OS/2"].usWeightClass if "OS/2" in f else 400)
    if peso not in PESOS:
        return  # Thin, ExtraLight e Light não servem a mídia kit: ficam de fora para poupar disco
    nomear(f, familia, peso)
    f.save(destino / (f"{familia}.ttf" if peso == 400 else f"{familia}__{peso}.ttf"))
    feitos.append(peso)


def baixar_familia(familia, pasta_repo, fixos):
    destino = BIB / familia; destino.mkdir(parents=True, exist_ok=True)
    tmp = destino / ".baixando.ttf"
    feitos = []
    if familia in OUTRAS_ORIGENS:
        _, repo, arquivos, licenca = OUTRAS_ORIGENS[familia]
        base = f"https://raw.githubusercontent.com/{repo}/HEAD/"
        baixar_url(base + licenca, destino / "OFL.txt")
        for caminho in arquivos:
            baixar_url(base + caminho, tmp)
            _salvar_estatica(tmp, familia, destino, feitos, unico=len(arquivos) == 1)
        tmp.unlink(missing_ok=True)
        return sorted(set(feitos))
    itens = json.loads(urllib.request.urlopen(urllib.request.Request(API + pasta_repo, headers=_cabecalhos()), timeout=60).read())
    ttfs = [i["name"] for i in itens if i["name"].endswith(".ttf") and "Italic" not in i["name"]]
    if any(i["name"] == "OFL.txt" for i in itens):
        baixar_url(RAW + pasta_repo + "/OFL.txt", destino / "OFL.txt")
    for nome in ttfs:
        baixar_url(RAW + pasta_repo + "/" + urllib.request.quote(nome), tmp)
        if "fvar" in TTFont(tmp):
            _salvar_instancias(tmp, familia, fixos, destino, feitos)
        else:
            _salvar_estatica(tmp, familia, destino, feitos, unico=len(ttfs) == 1)
    tmp.unlink(missing_ok=True)
    return sorted(set(feitos))


def pesos_da_pasta(d):
    return sorted(int(m.group(1)) if (m := re.search(r"__(\d+)$", f.stem)) else 400 for f in d.glob("*.ttf"))


def listar():
    if not BIB.exists():
        print("biblioteca vazia"); return
    pastas = sorted(p for p in BIB.iterdir() if p.is_dir() and p.name != "cartelas")
    for d in pastas:
        uso = CATALOGO.get(d.name, ("", "?", {}))[1]
        print(f"{d.name:<28} {uso:<24} pesos {pesos_da_pasta(d)}")
    print(f"\n{len(pastas)} famílias")


def acentos_presentes(d):
    """True se TODOS os caracteres de ACENTOS existem no cmap de TODOS os arquivos da família."""
    for f in d.glob("*.ttf"):
        cmap = TTFont(f).getBestCmap()
        if not all(ord(c) in cmap for c in ACENTOS):
            return False
    return True


def catalogo():
    """Regrava ../catalogos/fontes.json a partir do que está na pasta (pesos e acentos medidos, nunca declarados)."""
    saida = AQUI.parent / "catalogos" / "fontes.json"
    saida.parent.mkdir(exist_ok=True)
    fams = []
    for nome in CATALOGO:
        d = BIB / nome
        if not d.exists():
            continue
        papel, largura, humor = META[nome]
        origem = OUTRAS_ORIGENS[nome][0] if nome in OUTRAS_ORIGENS else "google"
        fams.append({"familia": nome, "pasta": f"fontes-livres/{nome}", "origem": origem,
                     "licenca": ORIGEM_LICENCA[origem], "papel": papel, "largura": largura, "humor": humor,
                     "pesos": pesos_da_pasta(d), "acentos_ptbr": acentos_presentes(d)})
    fams.sort(key=lambda x: x["familia"].lower())
    leia = ("Cartela de fontes livres do mídia kit. Gerado por pipeline/fontes_livres.py catalogo (pesos e acentos_ptbr são "
            "medidos nos arquivos, não declarados). Cada peso é o arquivo 'Familia__peso.ttf' em 'pasta' (400 = 'Familia.ttf'). "
            "papel: display, corpo ou serifa. largura: condensada, normal ou larga. Só use família com acentos_ptbr true. "
            "Fontshare fica de fora por licença (ver fontes-livres/LICENCAS.md).")
    saida.write_text(json.dumps({"_leia": leia, "familias": fams}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"OK  {len(fams)} famílias → {saida}")


def para(dest, familias):
    dest = Path(dest); dest.mkdir(parents=True, exist_ok=True)
    falta = []
    for fam in familias:
        src = BIB / fam
        if not src.exists():
            falta.append(fam); continue
        for f in src.glob("*.ttf"):
            shutil.copy2(f, dest / f.name)
        print(f"OK  {fam} → {dest}")
    for fam in falta:
        print(f"FALTA  {fam} (rode: fontes_livres.py baixar --so \"{fam}\")")
    return 1 if falta else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("acao", choices=["baixar", "listar", "para", "catalogo"])
    ap.add_argument("resto", nargs="*")
    ap.add_argument("--so", default=None, help="famílias separadas por vírgula")
    a = ap.parse_args()
    if a.acao == "listar":
        listar(); return
    if a.acao == "catalogo":
        catalogo(); return
    if a.acao == "para":
        sys.exit(para(a.resto[0], a.resto[1:]))
    alvo = [x.strip() for x in a.so.split(",")] if a.so else list(CATALOGO)
    erros = 0
    for fam in alvo:
        try:
            pesos = baixar_familia(fam, CATALOGO[fam][0], CATALOGO[fam][2])
            print(f"OK  {fam:<24} pesos {pesos}")
        except Exception as e:
            erros += 1; print(f"ERRO  {fam}: {e}")
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()

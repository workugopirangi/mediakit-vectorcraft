#!/usr/bin/env python3
"""
cena_prompt.py v2 — monta o prompt de uma cena na ordem cena → sujeito → câmera → restrições (OpenAI image prompting guide),
sem texto gerado pelo modelo (o lettering entra pelo compor.py), com bloco de estilo fixo por kit (marca.estilo_cena).

Uso: python3 cena_prompt.py <pasta-do-cliente> <arquetipo> [--ativo "<nome do ativo>"] [--noite]
         [--composicao [<pasta-do-kit>] --pagina <rótulo> [--elemento <id>] [--receita r1] [--origem 16:9]]
Arquétipos: capa | manifesto | projecao | ativo | cota | publico | contato
Saída: o prompt (stdout) e, com --salvar, acervo/<id>.prompt.txt. Painéis de marca são descritos como superfícies lisas,
foscas e uniformemente iluminadas, prontos para receber "SEU LOGO AQUI" e o lettering por composição.

--composicao: a cena nasce para a página. O prompt ganha o bloco "Composition" com a caixa REAL que a foto ocupa na página
(px e proporção), o recorte que a página faz na imagem de origem (cover: só a faixa do meio de uma imagem 16:9 aparece numa
caixa quase quadrada), as zonas que o título, o número, o preço e o elemento ancorado vão cobrir (calmas, sem rosto nem
detalhe-chave) e o foco. Vem da maquete (saida/plano-elementos-*.json) e da composição do mediakit.json; sem a caixa medida da
foto, o prompt sai sem o bloco e avisa (composicao_prompt.py).
"""
import argparse, colorsys, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import composicao_prompt as cp  # noqa: E402


def nome_cor(hexa):
    """Nome da cor em inglês simples. Hex no prompt vira texto impresso na imagem; o nome não."""
    r, g, b = (int(hexa.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if s < 0.12:
        return "white" if l > 0.8 else "grey" if l > 0.25 else "black"
    base = next(n for lim, n in [(0.04, "red"), (0.11, "orange"), (0.18, "yellow"), (0.45, "green"), (0.52, "teal"), (0.72, "blue"), (0.83, "purple"), (0.97, "pink"), (1.01, "red")] if h < lim)
    return f"{'deep' if l < 0.35 else 'light' if l > 0.7 else 'vivid'} {base}"

CENAS = {
    "corrida de rua": {"heroi": "the start arch of a city street running race, a dense crowd of runners under and beyond the arch, city skyline behind", "pessoas": "two or three amateur runners in sharp focus in the foreground, ordinary bodies, race bibs", "chao": "asphalt"},
    "trail": {"heroi": "a trail running start gate at the edge of dense forest, a river or a mountain viewpoint behind, runners small in the landscape", "pessoas": "one trail runner in focus on a dirt path, dusty legs", "chao": "dirt and roots"},
    "ciclismo": {"heroi": "a cycling peloton leaning into a curve past a start gate with blank sponsor panels, support box with mechanics", "pessoas": "one cyclist in focus in the foreground, plain jersey", "chao": "asphalt or single track"},
    "triathlon": {"heroi": "a swim start deck with buoys and a blank water gate, transition area with racked bikes", "pessoas": "athletes in swim caps in the foreground", "chao": "sand and water"},
    "arena": {"heroi": "a sand court or ring with bleachers full of fans, a blank scoreboard and a blank interview backdrop", "pessoas": "two athletes mid-action in sharp focus", "chao": "sand or canvas"},
    "futebol": {"heroi": "a grass football pitch of a youth championship, families standing at the fence along the touchline, a blank inflatable entrance arch and blank boards at the pitch side", "pessoas": "young players in sharp focus, ordinary kids, real football kits", "chao": "grass and red earth", "roupa": "plain football kits", "publico": "children and their families",
                "fundo": "background players",
                "cota": "Scene: the touchline of a youth football championship, families at the fence. Subject: one young player in sharp focus in a plain football kit in {cor}, smiling, teammates and crowd behind out of focus.",
                "contato": "Scene: a youth football pitch at the end of a Saturday morning. Subject: a group of young players walking off the pitch towards camera in plain football kits in {cor}, smiling, slightly out of focus so text can sit on top."},
}
ARQ = {
    "capa": "Scene: {heroi}. Subject: {pessoas}, one of them looking at camera and smiling, wearing {roupa1} in {cor}; crowd behind out of focus.",
    "manifesto": "Scene: the finish line area of {modalidade}. Subject: two athletes hugging after finishing, {roupa} in {cor}, crowd behind out of focus, emotional, genuine.",
    "projecao": "Scene: wide view from a raised vantage of the event village at the start line: {heroi}, a big LED screen beside the arch, feather flags, barriers and tents. The arch header, its two columns, the LED screen and the flags are BLANK, flat, matte panels in {cor} or white, evenly lit and facing the camera almost frontally, with clean straight edges, ready for signage. Subject: several hundred participants in {cor} shirts filling the start corral, varied heights, poses and skin tones, receding believably into depth.",
    "ativo": "Scene: {ativo_cena}. All signage surfaces are BLANK matte panels, evenly lit, no printing. Subject: {pessoas}, wearing {roupa} in {cor}.",
    "cota": "Scene: the race course of {modalidade} at the edge of the event village. Subject: one athlete in sharp focus wearing a plain race shirt in {cor} and a blank race bib, drinking water or smiling, crowd behind out of focus.",
    "publico": "Scene: a crowd of participants at dusk on the course, palm trees or city lights. Subject: a runner seen from behind in a plain {cor} shirt, cinematic depth.",
    "contato": "Scene: the course at golden hour. Subject: a group of athletes running towards camera in plain {cor} shirts, smiling, slightly out of focus so text can sit on top.",
}
ATIVOS = {
    "pórtico": "eye-level shot of the start and finish arch of a {modalidade}, {chao}, timing clock showing 00:00:03, the arch header and side columns as blank matte panels",
    "camisa": "medium shot of two runners from the front and one from the back, plain race shirts in {cor} with a blank chest area, blank sleeve and blank back panel",
    "estande": "an activation tent at the race village with a blank backdrop, a blank LED wall and a blank counter, staff handing samples, athletes queuing",
    "backdrop": "a finish-line photo backdrop as a blank grid of matte panels, four athletes with medals posing in front",
    "kit": "product shot of the athlete kit on a table: a blank cup, a blank tote bag and a blank race bib, the race village out of focus behind",
    "hidratação": "a hydration point on the course with blank table skirts, cups, volunteers, runners passing",
    "premiação": "the stage of an awards night in a municipal theater: a long table with gold trophies in the foreground, a BLANK dark backdrop wall behind, warm spotlights from the left, the audience dark and out of focus",
    "estrelas": "the stage of an awards night in a municipal theater: a long table with gold trophies in the foreground, a BLANK dark backdrop wall behind, warm spotlights from the left, the audience dark and out of focus",
}
CAMERA = "Camera: 35mm lens at f/2.8, eye level unless stated, shallow depth of field, natural motion blur on {fundo}."
CAMERA_ARQ = {"projecao": "Camera: 24mm lens at f/5.6, raised vantage about 5 meters above the crowd looking slightly down, everything from the front rows to the arch in focus."}
ESTILO_PADRAO = "late afternoon golden backlight, sun low at about 15 degrees, warm highlights and cool shadows, light haze"
RESTRICOES = ("Constraints: a real photograph someone could have taken, not an overly enhanced or cinematic movie-poster image. "
              "Brazilian people, diverse, {publico}, ordinary clothes beyond the {roupa}. No text, no letters, no logos, no watermark, no numbers on bibs. "
              "No duplicated faces, correct hands, five fingers. Horizon level. 1920x1080 landscape.")


TEXTO_ALVO = {"titulo": "The page title", "numero": "The big number", "preco": "The price", "subtitulo": "The subtitle",
              "texto": "The body text and lists", "logo": "The event logo"}


def razao_de(txt):
    """'16:9' ou '3:2' (ou um número) como largura / altura."""
    if ":" in txt:
        w, h = txt.split(":", 1)
        return float(w) / float(h)
    return float(txt)


def bloco_composicao(c, origem_txt="16:9"):
    """O bloco "Composition" do prompt de cena (inglês) a partir dos fatos da página (composicao_prompt.cena). Vazio quando a
    página não tem a foto medida: nada é inventado."""
    f = cp.cena(c, razao_de(origem_txt))
    if not f:
        return ""
    W, H = f["pagina_px"]
    _, _, w, h = f["caixa"]
    frases = [f"Composition (from the page layout): the photo fills a {w} x {h} px box on the {W} x {H} px page "
              f"({cp.descrever_razao(w, h)}), shown cropped to cover."]
    r = f["recorte"]
    if r:
        dim = "width" if r["eixo"] == "x" else "height"
        frases.append(f"The source frame is {origem_txt}, so the page keeps only the part of the frame from {r['de']}% to {r['ate']}% of its {dim}: "
                      "put the subject and every key detail inside that part and let the rest be plain background that can be cropped.")
    for z in f["texto"]:
        frases.append(f"{TEXTO_ALVO[z['alvo']]} will sit over the {z['regiao']} of the visible photo (about {z['largura_pct']}% of its width): "
                      "keep that area calm, with no faces and no key detail.")
    if f["elemento"]:
        z = f["elemento"]
        frases.append(f"An object will overlap the {z['regiao']} of the visible photo (about {z['largura_pct']}% of its width): "
                      "keep faces and key detail away from that area.")
    if f["foco_foto"]:
        frases.append("The photo is the focus of the page: it must read at a glance.")
    return " ".join(frases)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta"); ap.add_argument("arquetipo"); ap.add_argument("--ativo", default=None); ap.add_argument("--noite", action="store_true"); ap.add_argument("--salvar", default=None, help="id para gravar acervo/<id>.prompt.txt")
    ap.add_argument("--composicao", nargs="?", const="-", default=None, help="a cena nasce para a página da composição (pasta do kit; sem valor = a pasta do cliente)")
    ap.add_argument("--pagina", default=None, help="rótulo da página na composição (ativo:2, cota:Master, capa:c) ou o número dela")
    ap.add_argument("--elemento", default=None, help="id de um elemento ancorado nesta página: a área que ele cobre da foto fica calma")
    ap.add_argument("--receita", default=None, help="qual plano-elementos-<receita>.json dá a foto medida")
    ap.add_argument("--origem", default="16:9", help="proporção da imagem que o gerador devolve (padrão 16:9, a do cena.sh)")
    ap.add_argument("--cena", default=None, help="cena e sujeito desta página, em inglês, decididos na direção de arte (substitui "
                    "só a frase do arquétipo; câmera, luz do kit, local, composição e restrições continuam do sistema)")
    a = ap.parse_args()
    if a.salvar is not None and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", a.salvar):     # o id vira nome de arquivo: "../../X" escreveria fora de acervo/
        print(f"erro: id inválido para --salvar: {a.salvar!r} (só a-z, 0-9 e hífen, sem começar por hífen)", file=sys.stderr)
        sys.exit(64)
    k = json.loads((Path(a.pasta) / "mediakit.json").read_text(encoding="utf-8"))
    mod = (k["evento"].get("modalidade_sistema") or "corrida de rua").lower(); m = CENAS.get(mod, CENAS["corrida de rua"])
    roupa = m.get("roupa", "plain race shirts"); roupa1 = roupa[:-1] if roupa.endswith("s") else roupa
    cor = nome_cor(k["marca"].get("cor_primaria", "#E8307A"))
    ativo_cena = ""
    if a.arquetipo == "ativo":
        chave = next((c for c in ATIVOS if c in (a.ativo or "").lower()), "pórtico")
        ativo_cena = ATIVOS[chave].format(modalidade=mod, chao=m["chao"], cor=cor)
    if a.cena:
        corpo = " ".join(a.cena.split())
        corpo = corpo if corpo.lower().startswith("scene") else f"Scene: {corpo}"
        corpo = corpo if corpo.endswith(".") else corpo + "."
    else:
        corpo = (m.get(a.arquetipo) or ARQ[a.arquetipo]).format(heroi=m["heroi"], pessoas=m["pessoas"], cor=cor, modalidade=mod,
                                                                ativo_cena=ativo_cena, chao=m["chao"], roupa=roupa, roupa1=roupa1)
    estilo = k["marca"].get("estilo_cena") or ESTILO_PADRAO
    luz = "Light: night, event floodlights, deep blue sky, warm practical lights." if a.noite else f"Light: {estilo}."
    lugar = "Location: " + ", ".join(x for x in (k["evento"].get("local"), k["evento"].get("cidade"), "Brazil") if x) + "; local landmarks when natural."
    bloco = ""
    if a.composicao is not None or a.pagina:
        if not a.pagina:
            ap.error("--composicao pede --pagina <rótulo>")
        try:
            bloco = bloco_composicao(cp.contexto(a.pasta if a.composicao in (None, "-") else a.composicao, a.pagina, a.elemento, a.receita), a.origem)
        except cp.ErroComposicaoPrompt as e:
            print(f"erro: {e}", file=sys.stderr)
            sys.exit(64)
        if not bloco:
            print(f"aviso: a página `{a.pagina}` não tem a foto medida no plano (rode a maquete: render.py --maquete); o prompt sai sem o bloco Composition", file=sys.stderr)
    camera = CAMERA_ARQ.get(a.arquetipo) or CAMERA.format(fundo=m.get("fundo", "background runners"))
    prompt = f"Photorealistic editorial sports photography. {corpo} {camera} {luz} {lugar} {bloco + ' ' if bloco else ''}{RESTRICOES.format(publico=m.get('publico', 'adults'), roupa=roupa)}"
    print(prompt)
    if a.salvar:
        p = Path(a.pasta) / "acervo"; p.mkdir(exist_ok=True); (p / f"{a.salvar}.prompt.txt").write_text(prompt, encoding="utf-8")


if __name__ == "__main__":
    main()

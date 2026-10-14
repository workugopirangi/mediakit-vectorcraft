#!/usr/bin/env python3
# Copiado da v9 (commit 6003ce2) em 14/10/2026.
"""
recortar.py: remoção de fundo por classe de objeto (pesquisa r2, seção e), com refinamento de borda.

Uso: python3 recortar.py <entrada> <saida.png> --classe atleta|pessoa-livre|produto|equipamento [--modelo NOME]
                         [--da-cena] [--comparar isnet]

Roteamento (README do rembg):
  atleta       → birefnet-portrait (melhor em cabelo, suor, tecido fino; ~1 GB de modelo). Ele NÃO está instalado e este
                 script nunca o baixa: sem o arquivo, a classe cai para isnet-general-use (~170 MB, instalado) com aviso no
                 stderr. NÃO use u2net_human_seg quando a pessoa segura algo: ele só reconhece gente e come garrafa, copo
                 ou medalha na mão (medido em 08/10/2026, aprendizado 24)
  pessoa-livre → u2net_human_seg (instalado): SÓ pessoa de mãos vazias, pelo mesmo motivo. É a classe da pessoa recortada
                 da própria cena que passa na frente do título (relação `registro`): use com --da-cena --comparar isnet,
                 que avisa quando o modelo de pessoa deixou de fora algo que o isnet viu
  produto      → isnet-general-use (borda limpa; diferença entre modelos é marginal)
  equipamento  → isnet-general-use; vidro/garrafa: gere o objeto em fundo cinza 50% antes (mantém a cor do fundo dentro do objeto)
  Não use `bria-rmbg` (padrão atual do rembg) em peça comercial sem licença paga da BRIA.
Depois: recortar-borda (erosão 1 px + feather .8, feito aqui) e a sombra. Confira o halo compondo sobre preto E sobre branco.

Opções:
  --da-cena         a entrada é a cena TRATADA da página (a mesma imagem que o render usa, já cortada e tingida): a saída tem o
                    mesmo tamanho, pixel a pixel, para registrar sobre a foto (relação `registro`). Desliga o so_o_principal:
                    na cena, um pedaço separado (mão erguida, a outra pessoa da dupla) é parte do que a página mostra, e o
                    registro exige cada pedaço no lugar.
  --comparar isnet  roda também o isnet-general-use na mesma entrada e mede o IoU das duas máscaras (alfa >= 128, a tinta).
                    Grava em <saida>.meta.json (campo `recorte`; a ficha que já existe é mantida) e na saída padrão. Abaixo de
                    .90, AVISO: um modelo viu o que o outro não viu, e o caso comum é o objeto na mão comido pelo modelo de
                    pessoa. O aviso diz quantos px e onde (caixa) o isnet viu a mais. Aviso não muda o código de saída.

Modelos: só os que já estão no disco, nunca baixados (cada um tem de 170 MB a 1 GB, o disco é curto, e baixar é decisão do
Ugo). Procura onde o rembg 2.0.x procura: U2NET_HOME, REMBG_HOME, $XDG_DATA_HOME/rembg ou ~/.rembg, em
models/<nome>/<nome>.onnx, e a pasta antiga plana (~/.u2net). Modelo ausente: código 2 com o caminho esperado e a lista do que
está instalado. Durante a execução o download do rembg (pooch.retrieve) fica trancado: um caminho que esta conferência não
previu também para com 2, em vez de puxar o modelo da internet.

Usa a biblioteca rembg do Python que roda este script (~/.venvs/mediakit), não o comando `rembg` do sistema. O recorte de
fundo é só pelo rembg local: sem ele neste Python o script para com código 2 e diz como instalar (não existe plano B de
outro fornecedor).
Códigos de saída: 0 ok (com ou sem aviso), 2 rembg ou modelo ausente, 64 uso.
"""
import argparse, datetime, json, os, sys
from pathlib import Path

MODELOS = {"atleta": "birefnet-portrait", "pessoa-livre": "u2net_human_seg", "produto": "isnet-general-use",
           "equipamento": "isnet-general-use"}
RESERVA_ATLETA = "isnet-general-use"        # quando o birefnet-portrait não está no disco
COMPARAR = {"isnet": "isnet-general-use"}
LIMITE_IOU = 0.90
# Tamanho aproximado de cada modelo, para avisar antes de qualquer download (o rembg baixa na primeira chamada).
TAMANHO_MB = {"u2net_human_seg": 170, "isnet-general-use": 170, "birefnet-portrait": 1000}


def tamanho_do_modelo(nome):
    mb = TAMANHO_MB.get(nome)
    return "de 170 MB a 1 GB" if mb is None else (f"cerca de {mb} MB" if mb < 1000 else "cerca de 1 GB")
LIMIAR_TINTA = 128                           # o mesmo de composicao.LIMIAR_TINTA


def so_o_principal(im, minimo=0.02, avisar=True):
    """Descarta fragmentos soltos (pedaço de outra pessoa ao fundo): fica a maior peça do alfa e as que tiverem
    pelo menos `minimo` da área dela (mão, garrafa separadas por um vão). Pixel de borda semitransparente é mantido."""
    import cv2, numpy as np
    from PIL import Image
    alfa = np.array(im.split()[3])
    n, rot, est, _ = cv2.connectedComponentsWithStats((alfa > 16).astype(np.uint8), connectivity=8)
    if n <= 2:
        return im
    areas = est[1:, cv2.CC_STAT_AREA]
    manter = [i + 1 for i, ar in enumerate(areas) if ar >= areas.max() * minimo]
    mascara = np.isin(rot, manter)
    descartados = n - 1 - len(manter)
    alfa = np.where(mascara | (alfa <= 16), alfa, 0).astype(np.uint8)
    im.putalpha(Image.fromarray(alfa))
    if descartados and avisar:
        print(f"  {descartados} fragmento(s) solto(s) descartado(s)")
    return im


def pastas_de_modelo():
    """(raiz, pasta antiga) onde o rembg 2.0.x procura um modelo já baixado (BaseSession.rembg_home e legacy_home):
    U2NET_HOME, se existir, é a raiz; senão REMBG_HOME, senão $XDG_DATA_HOME/rembg, senão ~/.rembg."""
    xdg = os.getenv("XDG_DATA_HOME")
    if os.getenv("U2NET_HOME"):
        raiz = os.getenv("U2NET_HOME")
    else:
        raiz = os.getenv("REMBG_HOME", os.path.join(xdg, "rembg") if xdg else os.path.join("~", ".rembg"))
    antiga = os.getenv("U2NET_HOME", os.path.join(xdg or "~", ".u2net"))
    return Path(os.path.expanduser(raiz)), Path(os.path.expanduser(antiga))


def arquivo_do_modelo(nome):
    """O .onnx já baixado do modelo `nome` (o arquivo que o rembg carregaria sem baixar), ou None."""
    raiz, antiga = pastas_de_modelo()
    for p in (raiz / "models" / nome / f"{nome}.onnx", antiga / f"{nome}.onnx"):
        if p.is_file() and p.stat().st_size > 0:
            return p
    return None


def instalados():
    raiz, antiga = pastas_de_modelo()
    achados = {p.stem for p in (raiz / "models").glob("*/*.onnx") if p.stem == p.parent.name}
    achados |= {p.stem for p in antiga.glob("*.onnx")} if antiga.is_dir() else set()
    return sorted(n for n in achados if arquivo_do_modelo(n))


def trancar_download():
    """O rembg baixa o modelo pelo pooch.retrieve quando não acha o arquivo. Trancado: nada sai daqui para a internet."""
    try:
        import pooch
    except ImportError:
        return

    def proibido(url, *a, **k):
        print(f"o rembg tentou BAIXAR um modelo ({url}). Este script nunca baixa modelo: peça ao Ugo para autorizar o download, "
              "ou rode com --modelo e um dos instalados", file=sys.stderr)
        sys.exit(2)
    pooch.retrieve = proibido


def comparar_mascaras(principal, outro):
    """IoU das duas máscaras de tinta (alfa >= 128) e o que só o outro modelo viu: o total de px e a MAIOR PEÇA (px e caixa
    [x0, y0, x1, y1]). A caixa é a da maior peça depois de uma abertura 3x3, não a de todos os px: os dois modelos discordam
    em fios de 1 a 2 px pela silhueta inteira, e a caixa de tudo cobria a pessoa toda (medido: bola no pé de um atleta real,
    caixa de 333 x 707 px; a da bola sozinha é a que diz onde olhar)."""
    import cv2, numpy as np
    a = np.asarray(principal.split()[3]) >= LIMIAR_TINTA
    b = np.asarray(outro.split()[3]) >= LIMIAR_TINTA
    uniao, inter = int((a | b).sum()), int((a & b).sum())
    so_outro = b & ~a
    limpo = cv2.morphologyEx(so_outro.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, _, est, _ = cv2.connectedComponentsWithStats(limpo, connectivity=8)
    caixa, maior = None, 0
    if n > 1:
        k = 1 + int(np.argmax(est[1:, cv2.CC_STAT_AREA]))
        x, y, w, h, maior = (int(v) for v in est[k])
        caixa = [x, y, x + w, y + h]
    return {"iou": round(inter / uniao, 4) if uniao else 1.0, "px_so_no_outro": int(so_outro.sum()),
            "px_maior_peca": maior, "caixa_so_no_outro": caixa, "px_so_no_principal": int((a & ~b).sum())}


def gravar_ficha(saida, registro):
    """Acrescenta `recorte` à <saida>.meta.json, mantendo o que a ficha já tinha (a do elementos_prompt.py, por exemplo)."""
    ficha = Path(saida).with_suffix(".meta.json")
    dados = {}
    if ficha.exists():
        try:
            dados = json.loads(ficha.read_text(encoding="utf-8"))
        except ValueError:
            dados = {}
    dados["recorte"] = registro
    ficha.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return ficha


def recortar_borda(objeto, saida, erosao=1, feather=0.8):
    """Erosão de 1 px + feather na máscara (tira o halo do recorte). Era `tratar.py recortar-borda` na v9; vive aqui porque
    o tratar.py não veio para a v10."""
    from PIL import Image, ImageFilter
    with Image.open(objeto) as im:
        ob = im.convert("RGBA")
    a = ob.split()[3]
    for _ in range(int(erosao)):
        a = a.filter(ImageFilter.MinFilter(3))
    a = a.filter(ImageFilter.GaussianBlur(feather))
    ob.putalpha(a)
    ob.save(saida)
    print("OK", saida)


def main():
    ap = argparse.ArgumentParser(description="remoção de fundo por classe (rembg local), nunca baixa modelo")
    ap.add_argument("entrada"); ap.add_argument("saida"); ap.add_argument("--classe", required=True, choices=list(MODELOS))
    ap.add_argument("--modelo", default=None, help="troca o modelo da classe por outro JÁ instalado")
    ap.add_argument("--da-cena", action="store_true", help="a entrada é a cena tratada: mesmo tamanho, sem descartar fragmentos")
    ap.add_argument("--comparar", choices=list(COMPARAR), help="mede o IoU contra o isnet e avisa abaixo de .90")
    a = ap.parse_args()
    try:
        from rembg import new_session, remove
    except ImportError:
        print(f"rembg não está instalado em {sys.executable}: o recorte de fundo é só pelo rembg local. "
              "Rode com ~/.venvs/mediakit/bin/python (onde ele está) ou instale nele: ~/.venvs/mediakit/bin/pip install rembg", file=sys.stderr)
        sys.exit(2)
    from PIL import Image
    modelo = a.modelo or MODELOS[a.classe]
    if a.classe == "atleta" and not a.modelo and arquivo_do_modelo(modelo) is None:
        print(f"aviso: {modelo} não está instalado (~1 GB, este script nunca baixa): a classe atleta cai para {RESERVA_ATLETA}. "
              "Confira cabelo e o que a pessoa segura sobre preto e sobre branco", file=sys.stderr)
        modelo = RESERVA_ATLETA
    outro = COMPARAR.get(a.comparar)
    if outro and outro == modelo:
        print(f"--comparar {a.comparar} com o próprio {modelo} não mede nada: compare um modelo de pessoa com o isnet", file=sys.stderr)
        sys.exit(64)
    for m in [modelo] + ([outro] if outro else []):
        if arquivo_do_modelo(m) is None:
            raiz, _ = pastas_de_modelo()
            print(f"aviso: o modelo {m} ainda não está em {raiz} e pesa {tamanho_do_modelo(m)}. Nada foi baixado.", file=sys.stderr)
            print(f"modelo {m} não está instalado (esperado em {raiz / 'models' / m / (m + '.onnx')}). Este script nunca baixa "
                  f"modelo: cada um tem de 170 MB a 1 GB e baixar é decisão do Ugo. Instalados: {', '.join(instalados()) or 'nenhum'}. "
                  "Rode com --modelo <um deles> ou peça a autorização do download", file=sys.stderr)
            sys.exit(2)
    trancar_download()
    entrada = Image.open(a.entrada).convert("RGB")
    recorte = remove(entrada, session=new_session(modelo), post_process_mask=True)
    if not a.da_cena:
        recorte = so_o_principal(recorte)
    comparacao = None
    if outro:
        ref = remove(entrada, session=new_session(outro), post_process_mask=True)
        if not a.da_cena:
            ref = so_o_principal(ref, avisar=False)        # o mesmo tratamento dos dois lados: a medida compara modelo com modelo
        comparacao = comparar_mascaras(recorte, ref)
    recorte.save(a.saida)
    recortar_borda(a.saida, a.saida)
    if a.da_cena:
        with Image.open(a.saida) as s:
            if s.size != entrada.size:
                raise SystemExit(f"a saída mudou de tamanho ({s.size} contra {entrada.size}): não registra sobre a cena")
        print(f"  registro: {entrada.size[0]} x {entrada.size[1]} px, o mesmo da cena (sem descartar fragmentos)")
    if comparacao:
        aviso = comparacao["iou"] < LIMITE_IOU
        ficha = gravar_ficha(a.saida, {
            "classe": a.classe, "modelo": modelo, "da_cena": a.da_cena, "entrada": Path(a.entrada).name, "dims": list(entrada.size),
            "comparar": dict(modelo=outro, limite=LIMITE_IOU, aviso=aviso, **comparacao),
            "data": datetime.datetime.now().astimezone().isoformat(timespec="seconds")})
        print(f"IOU {modelo} x {outro}: {comparacao['iou']:.3f} (limite {LIMITE_IOU:.2f}) -> {ficha.name}")
        if aviso:
            caixa = comparacao["caixa_so_no_outro"]
            print(f"AVISO: IoU {comparacao['iou']:.2f} abaixo de {LIMITE_IOU:.2f} entre {modelo} e {outro}: o {outro} vê "
                  f"{comparacao['px_so_no_outro']} px que o {modelo} não vê" +
                  (f"; a maior peça tem {comparacao['px_maior_peca']} px, na caixa x0 y0 x1 y1 = {caixa}" if caixa else "") +
                  ". O objeto na mão ou junto do corpo (garrafa, medalha, bola) pode ter sido comido: confira sobre preto e "
                  "sobre branco; se foi, recorte com "
                  "--modelo isnet-general-use", file=sys.stderr)
    print("OK", a.saida, "modelo:", modelo, "| próximo: conferir halo sobre preto e branco")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
paleta.py: propõe 3 paletas para as receitas a partir do logo e das fotos do evento.

Uso:
  python3 paleta.py <pasta-do-kit> [--imagens a.png b.jpg ...] [--k 8]

Sem --imagens, lê do mediakit.json o logo/lettering e as fotos com direito de uso (capa, ativo, histórico, local...).
Extrai de 5 a 8 cores dominantes por k-means no espaço Lab (CIE L*a*b*, onde distância = diferença percebida),
ignorando pixels transparentes e quase pretos ou quase brancos. Monta 3 paletas (marca, escuro, papel, texto, apoio) e
mede o contraste WCAG de cada par usado pelo render:
  texto/escuro   corpo claro sobre o painel escuro (fundo escuro)
  texto/papel    tinta do papel (a cor `escuro`) sobre o papel: é o corpo das páginas de fundo papel
  marca/escuro   acento (título em duas cores, microlabel) sobre o painel escuro
Par de corpo abaixo de 4,5:1 reprova a paleta (e o script tenta corrigir escurecendo o escuro ou clareando o papel antes).
Imprime JSON pronto para colar em `receitas[].paleta`.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
from PIL import Image

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from render import contraste, acento_legivel  # mesma conta WCAG do render (uma regra, um lugar)

FUNCOES_FOTO = {"capa", "ativo", "historico", "local", "projecao", "manifesto", "publico", "cota", "contato"}


# ---------- sRGB <-> Lab (D65) ----------
def _lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _gam(c):
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)


M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
BRANCO = np.array([0.95047, 1.0, 1.08883])


def rgb_lab(rgb):
    xyz = _lin(rgb) @ M.T / BRANCO
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def lab_rgb(lab):
    fy = (lab[..., 0] + 16) / 116; fx = fy + lab[..., 1] / 500; fz = fy - lab[..., 2] / 200
    f = np.stack([fx, fy, fz], -1)
    xyz = np.where(f ** 3 > 216 / 24389, f ** 3, (116 * f - 16) / (24389 / 27)) * BRANCO
    return np.clip(_gam(xyz @ np.linalg.inv(M).T), 0, 1)


def hexa(lab):
    r = (lab_rgb(np.asarray(lab, dtype=float)) * 255).round().astype(int)
    return "#" + "".join(f"{x:02X}" for x in r)


# ---------- amostragem e k-means ----------
def pixels(caminho, n=20000, rng=None):
    im = Image.open(caminho).convert("RGBA")
    im.thumbnail((400, 400))
    a = np.asarray(im, dtype=float).reshape(-1, 4) / 255
    a = a[a[:, 3] > 0.5][:, :3]                       # transparente fora
    if not len(a):
        return np.zeros((0, 3))
    lab = rgb_lab(a)
    lab = lab[(lab[:, 0] > 8) & (lab[:, 0] < 95)]     # quase preto e quase branco fora
    if len(lab) > n:
        lab = lab[rng.choice(len(lab), n, replace=False)]
    return lab


def kmeans(x, k, rng, iters=30):
    """k-means++ simples (numpy), semente fixa: a mesma pasta dá a mesma paleta."""
    c = [x[rng.integers(len(x))]]
    for _ in range(1, k):
        d = np.min(((x[:, None, :] - np.array(c)[None]) ** 2).sum(-1), 1)
        c.append(x[rng.choice(len(x), p=d / d.sum())])
    c = np.array(c)
    for _ in range(iters):
        rot = np.argmin(((x[:, None, :] - c[None]) ** 2).sum(-1), 1)
        novo = np.array([x[rot == i].mean(0) if np.any(rot == i) else c[i] for i in range(k)])
        if np.allclose(novo, c, atol=1e-3):
            break
        c = novo
    peso = np.bincount(rot, minlength=k) / len(x)
    return c, peso


def croma(lab):
    return float(np.hypot(lab[1], lab[2]))


def com_L(lab, L, croma_max=None):
    """Mesma tonalidade, outra luminosidade (e croma limitado, para escuros e papéis não virarem neon)."""
    a, b = lab[1], lab[2]
    if croma_max is not None:
        cr = np.hypot(a, b)
        if cr > croma_max:
            a, b = a * croma_max / cr, b * croma_max / cr
    return np.array([L, a, b])


def corrigir(pal):
    """Garante 4,5:1 nos pares de corpo mexendo só na luminosidade do escuro e do papel."""
    for _ in range(30):
        if contraste(pal["texto"], pal["escuro"]) >= 4.5 and contraste(pal["escuro"], pal["papel"]) >= 4.5:
            break
        e = rgb_lab(np.array([int(pal["escuro"][i:i + 2], 16) / 255 for i in (1, 3, 5)]))
        p = rgb_lab(np.array([int(pal["papel"][i:i + 2], 16) / 255 for i in (1, 3, 5)]))
        pal["escuro"] = hexa(com_L(e, max(2.0, e[0] - 2)))
        pal["papel"] = hexa(com_L(p, min(99.0, p[0] + 1)))
    return pal


def medir(pal):
    pares = {"texto/escuro": (pal["texto"], pal["escuro"], 4.5), "texto/papel": (pal["escuro"], pal["papel"], 4.5),
             "marca/escuro": (pal["marca"], pal["escuro"], 3.0)}
    out = {}
    for nome, (a, b, minimo) in pares.items():
        r = contraste(a, b)
        out[nome] = {"razao": round(r, 2), "minimo": minimo, "ok": r >= minimo}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--imagens", nargs="*", default=None)
    ap.add_argument("--k", type=int, default=8)
    a = ap.parse_args()
    pasta = Path(a.pasta).resolve()
    rng = np.random.default_rng(7)
    if a.imagens:
        arquivos = [Path(x) if Path(x).is_absolute() else (pasta / x if (pasta / x).exists() else Path(x)) for x in a.imagens]
    else:
        k = json.loads((pasta / "mediakit.json").read_text(encoding="utf-8"))
        acervo = [x for x in k.get("acervo", []) if x.get("direito_uso")]
        logos = [pasta / x["arquivo"] for x in acervo if x.get("funcao") in ("lettering", "logo", "simbolo")]
        fotos = [pasta / x["arquivo"] for x in acervo if x.get("funcao") in FUNCOES_FOTO]
        arquivos = logos + fotos
    arquivos = [f for f in arquivos if f.exists()]
    if not arquivos:
        sys.exit("nenhuma imagem encontrada")
    amostras = []
    for f in arquivos:
        px = pixels(f, rng=rng)
        # o logo pesa 3 vezes: é a cor que o organizador escolheu, a foto é a cor do lugar
        eh_logo = "logo" in f.name.lower() or "lettering" in f.name.lower()
        amostras += [px] * (3 if eh_logo else 1)
    x = np.concatenate([s for s in amostras if len(s)])
    centros, peso = kmeans(x, a.k, rng)
    ordem = np.argsort(-peso)
    cores = [(centros[i], float(peso[i])) for i in ordem if peso[i] >= 0.02][:8]
    if len(cores) < 5:
        cores = [(centros[i], float(peso[i])) for i in ordem][:5]

    vivas = sorted(cores, key=lambda c: -croma(c[0]) * (0.5 + c[1]))      # cor de marca: croma alto e presença
    escuras = sorted(cores, key=lambda c: c[0][0])
    claras = sorted(cores, key=lambda c: -c[0][0])
    m1, m2 = vivas[0][0], (vivas[1][0] if len(vivas) > 1 else vivas[0][0])
    m3 = vivas[2][0] if len(vivas) > 2 else m2
    base_e, base_p = escuras[0][0], claras[0][0]

    propostas = [
        ("Escura da marca", "fundo escuro: painel quase preto puxado para o tom das fotos, marca dominante como acento",
         dict(marca=hexa(m1), escuro=hexa(com_L(base_e, 9, 10)), papel=hexa(com_L(base_p, 95, 6)), texto="#FFFFFF", apoio=hexa(m2))),
        ("Papel", "fundo papel: papel quente tirado da cor mais clara, a segunda cor viva como marca",
         dict(marca=hexa(m2), escuro=hexa(com_L(m2, 12, 12)), papel=hexa(com_L(base_p, 94, 10)), texto="#FFFFFF", apoio=hexa(m1))),
        ("Cor chapada", "fundo de cor: a cor viva vira fundo das páginas de texto; o escuro sai da própria marca",
         dict(marca=hexa(m1), escuro=hexa(com_L(m1, 10, 14)), papel=hexa(com_L(m1, 96, 8)), texto="#FFFFFF", apoio=hexa(m3))),
    ]
    saida = {"imagens": [str(f.relative_to(pasta)) if f.is_relative_to(pasta) else str(f) for f in arquivos],
             "dominantes": [{"hex": hexa(c), "peso": round(p, 3), "L": round(float(c[0]), 1), "croma": round(croma(c), 1)} for c, p in cores],
             "paletas": []}
    for nome, ideia, pal in propostas:
        pal = corrigir(pal)
        med = medir(pal)
        reprovados = [n for n, v in med.items() if not v["ok"]]
        saida["paletas"].append({"nome": nome, "ideia": ideia, "paleta": pal, "contraste": med,
                                 "acento_no_papel": acento_legivel(pal["marca"], pal["papel"]),
                                 "aprovada": not reprovados, "reprovada_por": reprovados})
    print(json.dumps(saida, ensure_ascii=False, indent=2))
    sys.exit(0 if all(p["aprovada"] for p in saida["paletas"]) else 1)


if __name__ == "__main__":
    main()

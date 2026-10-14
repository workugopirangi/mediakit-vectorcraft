"""As camadas automáticas da checagem (conteúdo, arquivo, tinta) num relatório só; e o prompt do revisor independente.
Uso: python3 -m mediakit.checagem.checar <pdf> <ficha.md>   (sai 1 se houver falha)"""
import json
import subprocess
import sys
from pathlib import Path

from mediakit import config
from mediakit.checagem import conteudo, tinta


def _validar_arquivo(pdf):
    r = subprocess.run([sys.executable, str(config.VALIDAR_PDF), str(pdf)], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def _sem_espaco(s):
    return "".join(s.split())


def _aceitas(pdf):
    p = Path(pdf).parent / "sobreposicoes-aceitas.json"
    return json.loads(p.read_text()) if p.exists() else []


def checar(pdf, ficha, avisos_foto=()):
    falhas, avisos, aceitos = [], [], []
    aceitas = _aceitas(pdf)
    for s in tinta.sobreposicoes(pdf):
        par = {_sem_espaco(s["a"]), _sem_espaco(s["b"])}
        ok = [x for x in aceitas if x["pagina"] == s["pagina"] and {_sem_espaco(x["a"]), _sem_espaco(x["b"])} == par]
        if ok:
            aceitos.append(f"p{s['pagina']}: '{s['a'][:40]}' encosta em '{s['b'][:40]}', aceito: {ok[0]['motivo']}")
            continue
        falhas.append(f"p{s['pagina']}: sobreposição de texto: '{s['a'][:40]}' encosta em '{s['b'][:40]}'")
    for t in conteudo.travessoes(pdf):
        falhas.append(f"p{t['pagina']}: travessão em '{t['trecho']}'")
    ok, saida = _validar_arquivo(pdf)
    if not ok:
        falhas.append("validar_pdf reprovou o arquivo (ver saída)")
    for n in conteudo.numeros_fora_da_ficha(pdf, ficha):
        avisos.append(f"p{n['pagina']}: número '{n['numero']}' não está na ficha")
    avisos.extend(avisos_foto)
    return {"falhas": falhas, "avisos": avisos, "arquivo": saida, "aceitos": aceitos}


def avisos_de_foto(pdf):
    """Lê o avisos-foto.json que o kit.montar grava ao lado do PDF: (avisos, aceitos), já em frase."""
    p = Path(pdf).parent / "avisos-foto.json"
    itens = json.loads(p.read_text()) if p.exists() else []
    frase = lambda a: (f"p{a['pagina']}: {a['arquivo']}: {a['ppi']} ppi numa caixa de {a['caixa'][0]} × {a['caixa'][1]} "
                       f"(régua {config.PPI_MINIMO})")
    return ([frase(a) for a in itens if not a.get("aceito")],
            [f"{frase(a)}, aceito: {a['aceito']}" for a in itens if a.get("aceito")])


def relatorio_md(r):
    linhas = ["## Checagem automática", "", f"Falhas: {len(r['falhas'])} · Avisos: {len(r['avisos'])}", ""]
    linhas += [f"- FALHA {f}" for f in r["falhas"]] + [f"- aviso {a}" for a in r["avisos"]]
    if r.get("aceitos"):
        linhas += ["", "### Aceitos de propósito (sobreposição e imagem abaixo da régua)", ""] + [f"- {a}" for a in r["aceitos"]]
    linhas += ["", "### Arquivo (validar_pdf)", "", "```", r["arquivo"], "```"]
    return "\n".join(linhas) + "\n"


def prompt_revisor(paginas_dir, ficha, referencias, logo):
    modelo = (Path(__file__).parent / "revisor.md").read_text(encoding="utf-8")
    return modelo.format(paginas=f"{paginas_dir}/pag-*.png", ficha=ficha,
                         referencias="; ".join(str(r) for r in referencias), logo=logo)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("uso: python3 -m mediakit.checagem.checar <pdf> <ficha.md>")
    fotos_avisos, aceitos = avisos_de_foto(sys.argv[1])
    res = checar(sys.argv[1], sys.argv[2], fotos_avisos)
    res["aceitos"] = res["aceitos"] + aceitos
    print(relatorio_md(res))
    sys.exit(1 if res["falhas"] else 0)

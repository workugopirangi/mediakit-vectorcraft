"""As camadas automáticas da checagem (conteúdo, arquivo, tinta) num relatório só; e o prompt do revisor independente.
Uso: python3 -m mediakit.checagem.checar <pdf> <ficha.md>   (sai 1 se houver falha)"""
import subprocess
import sys
from pathlib import Path

from mediakit import config
from mediakit.checagem import conteudo, tinta


def _validar_arquivo(pdf):
    r = subprocess.run([sys.executable, str(config.VALIDAR_PDF), str(pdf)], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def checar(pdf, ficha, avisos_foto=()):
    falhas, avisos = [], []
    for s in tinta.sobreposicoes(pdf):
        falhas.append(f"p{s['pagina']}: sobreposição de texto: '{s['a'][:40]}' encosta em '{s['b'][:40]}'")
    for t in conteudo.travessoes(pdf):
        falhas.append(f"p{t['pagina']}: travessão em '{t['trecho']}'")
    ok, saida = _validar_arquivo(pdf)
    if not ok:
        falhas.append("validar_pdf reprovou o arquivo (ver saída)")
    for n in conteudo.numeros_fora_da_ficha(pdf, ficha):
        avisos.append(f"p{n['pagina']}: número '{n['numero']}' não está na ficha")
    avisos.extend(avisos_foto)
    return {"falhas": falhas, "avisos": avisos, "arquivo": saida}


def relatorio_md(r):
    linhas = ["## Checagem automática", "", f"Falhas: {len(r['falhas'])} · Avisos: {len(r['avisos'])}", ""]
    linhas += [f"- FALHA {f}" for f in r["falhas"]] + [f"- aviso {a}" for a in r["avisos"]]
    linhas += ["", "### Arquivo (validar_pdf)", "", "```", r["arquivo"], "```"]
    return "\n".join(linhas) + "\n"


def prompt_revisor(paginas_dir, ficha, referencias, logo):
    modelo = (Path(__file__).parent / "revisor.md").read_text(encoding="utf-8")
    return modelo.format(paginas=f"{paginas_dir}/pag-*.png", ficha=ficha,
                         referencias="; ".join(str(r) for r in referencias), logo=logo)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("uso: python3 -m mediakit.checagem.checar <pdf> <ficha.md>")
    res = checar(sys.argv[1], sys.argv[2])
    print(relatorio_md(res))
    sys.exit(1 if res["falhas"] else 0)

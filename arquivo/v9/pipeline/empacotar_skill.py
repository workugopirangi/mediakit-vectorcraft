"""Empacota a skill gerar-mediakit-motion para o claude.ai (.skill = zip com a pasta gerar-mediakit-motion/): o que o Claude
precisa para rodar o processo, sem provas, saídas, bancada, capturas e imagens da régua. Só arquivos que o git conhece.
Uso: empacotar_skill.py <saida.skill> [--sem-recortes] [--leve]
  --sem-recortes  tira os JPEG de repertorio/recortes (e os mapas anotados)
  --leve          além disso, tira as imagens e fontes dos exemplos (fica só o texto): o reserva quando o upload recusa o tamanho
Recuperado do transcript de 09/10/2026 (linha 44237) e fixado em pipeline/ em 12/10/2026, com formatos/ incluído e capturas/ excluídas."""
import fnmatch, subprocess, sys, zipfile
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
saida = Path(sys.argv[1]); sem_recortes = "--sem-recortes" in sys.argv or "--leve" in sys.argv; leve = "--leve" in sys.argv
rastreados = subprocess.run(["git", "-C", str(RAIZ), "ls-files", "-z", "."], capture_output=True, text=True, check=True).stdout.split("\0")
INCLUI = ["SKILL.md", "LEIA-ME.md", ".gitignore", "catalogos/*.json", "fontes-livres/LICENCAS.md", "memoria-mediakit/*",
          "memoria-mediakit/checklists/LEIA-ME.md", "pipeline/*.py", "pipeline/*.sh", "pipeline/*.json", "pipeline/LEIA-ME.md",
          "pipeline/tema/*.css", "pipeline/templates/*.html", "pipeline/assets/grao.png", "pipeline/assets/fonts/LEIA-ME.md",
          "references/*.md", "regua/fontes.json", "regua/indice.json", "regua/RESUMO-*.md", "schema/*.json",
          "exemplos/*", "formatos/*", "repertorio/LEIA-ME.md", "repertorio/indice.json", "repertorio/repertorio.html",
          "repertorio/fontes.json", "repertorio/fontes/*.json", "repertorio/estudo/*.md",
          "repertorio/padroes/*.md", "repertorio/recursos/*.md", "repertorio/referencias/*.md"] + ([] if sem_recortes else ["repertorio/recortes/*.jpg", "repertorio/mapas/*.jpg"])
EXCLUI = ["pipeline/test_*.py", "exemplos/*/saida/*", "*.pyc", "*/__pycache__/*", "repertorio/capturas/*", "bancada/*"]
if leve:
    EXCLUI += ["exemplos/*.png", "exemplos/*.jpg", "exemplos/*.ttf", "exemplos/*.otf", "exemplos/*.woff2", "exemplos/*.woff", "formatos/*/prova/*"]
def casa(rel, padroes):
    return any(fnmatch.fnmatch(rel, p) or (p.endswith("/*") and rel.startswith(p[:-1])) for p in padroes)
arquivos = sorted(r for r in rastreados if r and casa(r, INCLUI) and not casa(r, EXCLUI) and (RAIZ / r).is_file())
with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as z:
    for r in arquivos:
        z.write(RAIZ / r, f"gerar-mediakit-motion/{r}")
total = sum((RAIZ / r).stat().st_size for r in arquivos)
print(f"{len(arquivos)} arquivos, {total / 1e6:.1f} MB sem compressão, zip {saida.stat().st_size / 1e6:.1f} MB -> {saida}")
pastas = {}
for r in arquivos:
    topo = r.split("/")[0] if "/" in r else "."
    pastas[topo] = pastas.get(topo, 0) + 1
print(pastas)

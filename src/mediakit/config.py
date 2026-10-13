"""Caminhos e réguas do projeto. Cada caminho aceita uma variável de ambiente para teste e para outra máquina."""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def _caminho(var, padrao):
    return Path(os.environ.get(var, padrao)).expanduser()


VC_REPO = _caminho("MEDIAKIT_VC_REPO", "~/Developer/vectorcraft")
VC_CLI = _caminho("MEDIAKIT_VC_CLI", str(VC_REPO / "target" / "release" / "vectorcraft-cli"))
VERSAO_VC = RAIZ / "vectorcraft" / "VERSAO"
# validar_pdf.py é da v9 (somente leitura até a junção, Task 14).
VALIDAR_PDF = _caminho("MEDIAKIT_VALIDAR_PDF", "~/.agents/skills/gerar-mediakit-motion/pipeline/validar_pdf.py")
COFRE_MEDIAKIT = _caminho("MEDIAKIT_COFRE",
                          "~/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/SISTEMAS/GERAR MEDIAKIT")

PPI_MINIMO = 96      # régua de foto na página exportada
ESCALA_PDF = 0.75    # 1920 unidades de página viram 1440 pt

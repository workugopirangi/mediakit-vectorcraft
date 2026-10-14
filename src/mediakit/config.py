"""Caminhos e réguas do projeto. Cada caminho aceita uma variável de ambiente para teste e para outra máquina."""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def _caminho(var, padrao):
    return Path(os.environ.get(var, padrao)).expanduser()


VC_REPO = _caminho("MEDIAKIT_VC_REPO", "~/Developer/vectorcraft")
VC_CLI = _caminho("MEDIAKIT_VC_CLI", str(VC_REPO / "target" / "release" / "vectorcraft-cli"))
VERSAO_VC = RAIZ / "vectorcraft" / "VERSAO"
# validar_pdf.py veio da v9 (cópia em src/mediakit/ferramentas/).
VALIDAR_PDF = _caminho("MEDIAKIT_VALIDAR_PDF", str(RAIZ / "src" / "mediakit" / "ferramentas" / "validar_pdf.py"))
COFRE_MEDIAKIT = _caminho("MEDIAKIT_COFRE",
                          "~/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/SISTEMAS/GERAR MEDIAKIT")

# Dados da v9 que a v10 lê no cofre (conhecimento; o código veio como cópia para src/mediakit/ferramentas/).
REPERTORIO = COFRE_MEDIAKIT / "repertorio"
SCHEMAS = COFRE_MEDIAKIT / "schema"
CATALOGOS = COFRE_MEDIAKIT / "catalogos"
FONTES_LIVRES = COFRE_MEDIAKIT / "fontes-livres"
MEMORIA = COFRE_MEDIAKIT / "memoria-mediakit"
FORMATOS = COFRE_MEDIAKIT / "formatos"
REGUA = COFRE_MEDIAKIT / "regua"
BIBLIOTECA_OBJETOS = _caminho("MEDIAKIT_BIBLIOTECA_OBJETOS",
                              "~/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/MARKETING/BIBLIOTECA DE OBJETOS")

PPI_MINIMO = 96      # régua de foto na página exportada
ESCALA_PDF = 0.75    # 1920 unidades de página viram 1440 pt

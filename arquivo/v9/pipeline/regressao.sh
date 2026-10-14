#!/usr/bin/env bash
# regressao.sh: a bancada é o teste. Rodar ANTES e DEPOIS de qualquer mudança em tema/, templates/ ou *.py.
# Verde = régua íntegra + toda prova unitária (pipeline/test_*.py) + bancada Corre por Elas e exemplo fictício
# em 0 falhas no QA (que inclui validar_pdf.py).
# Guarda a folha de comparação datada em bancada/historico/ para o "antes/depois".
# Uso: bash regressao.sh [--golden] [rotulo]      (o Claude roda; o Ugo não)
#   --golden  passo opcional, DESLIGADO por padrão (a regressão rápida continua rápida). Depois dos outros passos roda
#             `golden.py conferir` nos 5 kits (Sprint, Copa AME v2, travessia-da-lua, receitas-teste, corre-por-elas), cada
#             um num clone APFS renderizado com o pipeline vivo: uns 8 minutos. Divergência de PNG por página, texto,
#             pdffonts, pdfimages ou linhas de QA dá CONFERIR: VERMELHO e a regressão sai VERMELHA (código 1). Sem a
#             flag, a linha `golden:` do fim avisa que ele não foi conferido.
#             MEDIAKIT_GOLDEN=<pasta do golden, relativa à raiz da skill ou absoluta>   padrão: bancada/golden/2026-10-12
#             MEDIAKIT_CLONES=<onde clonar os kits>                                      padrão: a pasta temporária do sistema
#   --help    mostra este cabeçalho e sai
set -uo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
cd "$AQUI"
PY="${MEDIAKIT_PY:-$HOME/.venvs/mediakit/bin/python}"
B=../bancada/corre-por-elas
E=../exemplos/travessia-da-lua
GOLDEN="${MEDIAKIT_GOLDEN:-bancada/golden/2026-10-12}"
ROTULO=""
golden=0
falhou=0

uso() { sed -n -e '/^#!/d' -e '/^set /q' -e 's/^# \{0,1\}//p' "$AQUI/$(basename "$0")"; }

for arg in "$@"; do
  case "$arg" in
    -h|--help) uso; exit 0 ;;
    --golden) golden=1 ;;
    -*) echo "opção desconhecida: $arg (bash regressao.sh --help)" >&2; exit 2 ;;
    *) [ -z "$ROTULO" ] || { echo "rótulo repetido: $ROTULO e $arg" >&2; exit 2; }; ROTULO="$arg" ;;
  esac
done

if [ "$golden" -eq 1 ]; then       # falha cedo: não vale gastar os minutos dos outros passos para descobrir que o golden não existe
  case "$GOLDEN" in /*) gpath="$GOLDEN" ;; *) gpath="../$GOLDEN" ;; esac
  [ -f "$gpath/meta.json" ] || { echo "golden: $GOLDEN não é um golden (falta meta.json); aponte MEDIAKIT_GOLDEN para a pasta certa" >&2; exit 2; }
fi

passo() { echo; echo "== $1"; }
roda() { "$@" || { echo "!! falhou: $*"; falhou=1; }; }

passo "régua"
roda "$PY" regua.py checar

passo "provas unitárias (test_*.py)"
# Cada arquivo de prova sai com 0 quando tudo passa (contrato dos test_*.py). Mostra só o resumo; na falha, o fim da saída.
for t in test_*.py; do
  [ -e "$t" ] || continue
  if saida=$("$PY" "$t" 2>&1); then
    echo "ok      $t  $(printf '%s\n' "$saida" | grep -m1 -E '^PROVAS:|testes passaram')"
  else
    echo "!! falhou: $t"; printf '%s\n' "$saida" | tail -15; falhou=1
  fi
done

passo "bancada Corre por Elas"
roda "$PY" render.py "$B" --png --fontes "$B/fontes"
roda "$PY" qa.py "$B"
roda "$PY" contact_sheet.py "$B" --direcao causa --regua ../regua

passo "exemplo fictício (3 direções)"
roda "$PY" render.py "$E" --todas --png --fundo --fontes "$E/fontes"
roda "$PY" qa.py "$E"

golden_res="não conferido (bash regressao.sh --golden: os 5 kits contra $GOLDEN, uns 8 min)"
if [ "$golden" -eq 1 ]; then
  passo "golden (5 kits contra $GOLDEN; um clone por kit, uns 8 min)"
  if [ -n "${MEDIAKIT_CLONES:-}" ]; then "$PY" golden.py conferir --golden "$GOLDEN" --clones "$MEDIAKIT_CLONES"
  else "$PY" golden.py conferir --golden "$GOLDEN"; fi
  if [ "$?" -eq 0 ]; then golden_res="VERDE"; else echo "!! falhou: golden.py conferir (VERMELHO)"; golden_res="VERMELHO"; falhou=1; fi
fi

H=../bancada/historico
mkdir -p "$H"
carimbo="$(date +%Y-%m-%d_%H%M)${ROTULO:+_$ROTULO}"
cp "$B/saida/contact-causa.png" "$H/contact-causa_$carimbo.png"
echo; echo "folha guardada: bancada/historico/contact-causa_$carimbo.png"

echo "golden: $golden_res"
if [ "$falhou" -ne 0 ]; then echo "REGRESSÃO: VERMELHA"; exit 1; fi
echo "REGRESSÃO: VERDE"

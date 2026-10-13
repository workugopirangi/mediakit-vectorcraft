#!/usr/bin/env bash
# Gera UMA cena pelo Codex (GPT Image) e registra a geração na cota do kit. Nunca regera uma imagem que já abre inteira.
# Uso: gerar_cena.sh <id> <arquivo-de-prompt> <pasta-acervo> [imagem-anexa ...]
AQUI="$(cd "$(dirname "$0")" && pwd)"
source "$AQUI/codex_gerar.sh"
export PYTHONPATH="$(cd "$AQUI/../.." && pwd)${PYTHONPATH:+:$PYTHONPATH}"
[ $# -ge 3 ] || { echo "uso: gerar_cena.sh <id> <prompt> <acervo> [imagens...]" >&2; exit 64; }
ID="$1"; PF="$2"; OUT="$3"; shift 3
id_valido "$ID" || { echo "id inválido: $ID" >&2; exit 64; }
command -v codex >/dev/null || { echo "Codex não instalado" >&2; exit 2; }
ARGS=(); for i in "$@"; do ARGS+=(-i "$i"); done
PROMPT="$(cat "$PF")"; PROMPT="${PROMPT//@OUT@/$OUT/$ID.png}"
printf '%s\n' "$PROMPT" > "$OUT/$ID.prompt.txt"
codex_apos_gerar() { "$PY" -m mediakit.cenas registrar "$OUT" "$ID" >/dev/null; }
codex_produzir 1 "$OUT" "$OUT/$ID.png" "$OUT/.codex-$ID.saida" \
  codex exec "${CODEX_SANDBOX[@]}" -C "$OUT" --skip-git-repo-check "${ARGS[@]}" -o "$OUT/.codex-$ID.log" "$PROMPT"

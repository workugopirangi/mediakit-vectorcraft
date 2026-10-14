#!/usr/bin/env bash
# Gera UMA cena pelo Codex (GPT Image) e registra a chamada na cota do kit (deu certo ou não).
# Uma tentativa só: se falhar, quem decide se tenta de novo é o Ugo (decisão de 14/10/2026).
# Nunca regera uma imagem que já abre inteira.
# Uso: gerar_cena.sh <id> <arquivo-de-prompt> <pasta-acervo> [imagem-anexa ...]
AQUI="$(cd "$(dirname "$0")" && pwd)"
source "$AQUI/codex_gerar.sh"
MEDIAKIT_CODEX_TENTATIVAS=1
export PYTHONPATH="$(cd "$AQUI/../.." && pwd)${PYTHONPATH:+:$PYTHONPATH}"
[ $# -ge 3 ] || { echo "uso: gerar_cena.sh <id> <prompt> <acervo> [imagens...]" >&2; exit 64; }
ID="$1"; PF="$2"; OUT="$3"; shift 3
id_valido "$ID" || { echo "id inválido: $ID" >&2; exit 64; }
command -v codex >/dev/null || { echo "Codex não instalado" >&2; exit 2; }
mkdir -p "$OUT" && OUT="$(cd "$OUT" && pwd)"   # caminho absoluto: o Codex roda dentro do acervo
ARGS=(); for i in "$@"; do ARGS+=(-i "$i"); done
PROMPT="$(cat "$PF")"; PROMPT="${PROMPT//@OUT@/$OUT/$ID.png}"
# O prompt registrado é o que gerou a imagem: grava só quando ela nasce.
codex_apos_gerar() {
  printf '%s\n' "$PROMPT" > "$OUT/$ID.prompt.txt"
  "$PY" -m mediakit.cenas registrar "$OUT" "$ID" ok >/dev/null
}
codex_produzir 1 "$OUT" "$OUT/$ID.png" "$OUT/.codex-$ID.saida" \
  codex exec "${CODEX_SANDBOX[@]}" -C "$OUT" --skip-git-repo-check "${ARGS[@]}" -o "$OUT/.codex-$ID.log" "$PROMPT"
rc=$?
if [ "$rc" = 1 ] || [ "$rc" = 3 ]; then
  "$PY" -m mediakit.cenas registrar "$OUT" "$ID" falha >/dev/null
  echo "A geração de $ID falhou (código $rc) e gastou uma chamada. Não tente de novo sozinho: pergunte ao Ugo." >&2
fi
exit "$rc"

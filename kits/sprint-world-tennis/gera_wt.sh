#!/usr/bin/env bash
# Gera, pelo Codex (GPT Image), as cenas da World Tennis JÁ COM O LOGO (rota "gerar"), para comparar com a rota "compor".
S="$HOME/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/SISTEMAS/GERAR MEDIAKIT/pipeline"
CL="$HOME/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES/SPRINT UBATUBA RUN/MEDIAKIT"
OUT="$CL/sprint-world-tennis/acervo"
LOGO="$OUT/logo-world-tennis.png"
SPLOGO="$CL/sprint-2027/acervo/logo.png"
LIMPO="$CL/sprint-2027/acervo/limpo"
source "$S/codex_gerar.sh"
gera() { # id, arquivo-de-prompt, imagens...
  local ID="$1" PF="$2"; shift 2
  local ARGS=(); for i in "$@"; do ARGS+=(-i "$i"); done
  local PROMPT; PROMPT="$(cat "$PF")"; PROMPT="${PROMPT//@OUT@/$OUT/$ID.png}"
  printf '%s\n' "$PROMPT" > "$OUT/$ID.prompt.txt"
  codex_produzir 1 "$OUT" "$OUT/$ID.png" "$OUT/.codex-$ID.saida" \
    codex exec "${CODEX_SANDBOX[@]}" -C "$OUT" --skip-git-repo-check "${ARGS[@]}" -o "$OUT/.codex-$ID.log" "$PROMPT"
  echo "$ID -> $?"
}
D="$HOME/Developer/vectorcraft-mediakit/wt"
gera c-portico-wt-gerada "$D/p-portico.txt" "$LIMPO/c-portico.png" "$LOGO" "$SPLOGO"
gera c-estande-wt-gerada "$D/p-estande.txt" "$LIMPO/c-tendas.png" "$LOGO"
gera camisa-wt-gerada "$D/p-camisa.txt" "$LOGO" "$SPLOGO"

#!/usr/bin/env bash
# Copiado da v9 (commit 1a5db3f) em 14/10/2026.
# cena_limpar.sh: recebe uma imagem do CLIENTE (render de IA ou foto) com texto errado ou logo deformado e devolve a
# mesma cena com os painéis LISOS, sem nenhum texto. O lettering real entra depois pelo compor.py (aprendizado 7):
# assim a grafia sai certa sempre, em vez de pedir ao gerador para "corrigir" letras, que ele erra de novo.
# Mesma rota do gerar_cena.sh (codex exec → GPT Image, cota do ChatGPT do Ugo); a imagem de origem vai anexada com -i.
#
# Uso:  bash cena_limpar.sh <pasta-do-cliente> <id> <imagem-de-origem> [--descricao-de <arquivo>]
#       A instrução extra (inglês) vem de um ARQUIVO: ela traz campos do evento, e um $(...) ou uma crase dentro de aspas
#       duplas rodaria no shell de quem chama, antes de chegar aqui. Com "-" no lugar do arquivo, vem da entrada padrão
#       (heredoc com aspas simples no EOT). Forma antiga, ainda aceita com aviso no stderr: a instrução como 4º argumento.
# Saída: <pasta>/acervo/<id>.png (+ <id>.prompt.txt). Não regera se a saída já existe e abre inteira (truncada ou ilegível,
# é apagada e gerada de novo; cada geração gasta cota).
#
# Codex que falha: UMA tentativa só (decisão de 14/10/2026). A chamada é registrada em <pasta>/acervo/cota.json (ok ou
# falha) e, na falha, o script manda perguntar ao Ugo; cota ou login esgotados saem com código 3. Nunca outro fornecedor. Uma chamada por vez por kit (trava em <pasta>/acervo/.codex.lock). A saída
# das tentativas que falharam fica em .codex-<id>.saida. O Codex roda no sandbox workspace-write SEM rede (CODEX_SANDBOX em
# codex_gerar.sh). <id>: só a-z, 0-9 e hífen (é nome de arquivo). A imagem de origem tem de existir antes de chamar o Codex.
# Códigos de saída: 0 ok, 1 o Codex não entregou, 2 Codex não instalado, 3 cota ou login, 4 trava ocupada, 5 Python do kit
# sem PIL, 64 uso ou id inválido, 66 imagem de origem ausente ou vazia, ou arquivo da instrução extra ausente ou vazio.
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-${MEDIAKIT_PY:-$HOME/.venvs/mediakit-vc/bin/python}}"
. "$AQUI/../imagens/codex_gerar.sh"
# Decisão de 14/10/2026: UMA tentativa no Codex; se falhar, quem decide se tenta de novo é o Ugo.
MEDIAKIT_CODEX_TENTATIVAS=1; export MEDIAKIT_CODEX_TENTATIVAS
export PYTHONPATH="$(cd "$AQUI/../.." && pwd)${PYTHONPATH:+:$PYTHONPATH}"
uso() { echo 'uso: bash cena_limpar.sh <pasta-do-cliente> <id> <imagem-de-origem> [--descricao-de <arquivo>|-]' >&2; exit 64; }
POS=(); EXTRA_DE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --descricao-de) [ $# -ge 2 ] || { echo "falta o valor de --descricao-de" >&2; uso; }; EXTRA_DE="$2"; shift 2;;
    *) POS+=("$1"); shift;;
  esac
done
[ ${#POS[@]} -ge 3 ] && [ ${#POS[@]} -le 4 ] || uso
PASTA="${POS[0]}"; ID="${POS[1]}"; ORIGEM="${POS[2]}"; EXTRA=""
id_valido "$ID" || { echo "id inválido: $ID (só a-z, 0-9 e hífen, sem começar por hífen)" >&2; exit 64; }
if [ ${#POS[@]} -eq 4 ]; then
  [ -z "$EXTRA_DE" ] || { echo "instrução extra dada duas vezes: na linha de comando e em --descricao-de $EXTRA_DE" >&2; exit 64; }
  EXTRA="${POS[3]}"
  echo "aviso: a instrução extra veio na linha de comando. Um \$(...) ou uma crase dentro de aspas duplas já rodou no seu shell antes de chegar aqui; grave-a num arquivo e use --descricao-de <arquivo> (ou --descricao-de - com <<'EOT')" >&2
elif [ -n "$EXTRA_DE" ]; then
  # o conteúdo entra como dado: cat dentro de $(...) não reavalia o texto, e o heredoc do prompt só expande a variável
  if [ "$EXTRA_DE" = "-" ]; then
    EXTRA="$(cat)"
  else
    [ -f "$EXTRA_DE" ] && [ -r "$EXTRA_DE" ] || { echo "--descricao-de: o arquivo não existe ou não abre: $EXTRA_DE (nada foi enviado ao Codex)" >&2; exit 66; }
    EXTRA="$(cat "$EXTRA_DE")"
  fi
  [ -n "$(printf '%s' "$EXTRA" | tr -d '[:space:]')" ] || { echo "a instrução extra de ${EXTRA_DE} está vazia (nada foi enviado ao Codex)" >&2; exit 66; }
fi
mkdir -p "$PASTA/acervo"
OUT="$(cd "$PASTA/acervo" && pwd)"
png_ok "$OUT/$ID.png" && { echo "já existe: $OUT/$ID.png (apague para regerar)"; exit 0; }
[ -f "$ORIGEM" ] && [ -s "$ORIGEM" ] || { echo "a imagem de origem não existe ou está vazia: $ORIGEM (nada foi enviado ao Codex)" >&2; exit 66; }
ORIGEM_ABS="$(cd "$(dirname "$ORIGEM")" && pwd)/$(basename "$ORIGEM")"
command -v codex >/dev/null 2>&1 || { echo "codex não encontrado: instale, entre com \`codex login\` e rode de novo; não troque de fornecedor" >&2; exit 2; }

PROMPT="$(cat <<EOT
Edit the attached image and save the result exactly as $OUT/$ID.png, landscape 16:9 (or the widest landscape size available), at the highest resolution available.
Keep EVERYTHING else identical: same composition, camera, light, people, structures, sculpture, colors, crowd, sea, mountains.
Remove ALL text, letters, numbers and logos from every surface (arch header and columns, stage screen, tent headers, flags, banners, signs, barriers, shirts, sculpture base, timer).
Each cleaned surface must stay a smooth, flat, evenly lit panel in its original base color (black panels stay plain black, cream tents stay plain cream), facing the camera as before, ready for a logo to be composited later.
Do not add any new element. Do not add text.
$EXTRA
After saving, open the image and check: (1) no letter, number or logo remains anywhere, (2) the panels are blank and flat, (3) the rest of the scene is unchanged. Do NOT regenerate if a check fails (each generation spends the ChatGPT quota): keep the single image and list the defects in your final message.
EOT
)"
printf '%s\n' "$PROMPT" > "$OUT/$ID.prompt.txt"
# Toda chamada ao Codex gasta cota, deu certo ou não: registra a que deu certo aqui e a que falhou logo depois.
codex_apos_gerar() { "$PY" -m mediakit.cenas registrar "$OUT" "$ID" ok >/dev/null; }
rc=0
codex_produzir 1 "$OUT" "$OUT/$ID.png" "$OUT/.codex-$ID.saida" \
  codex exec "${CODEX_SANDBOX[@]}" -C "$OUT" --skip-git-repo-check -i "$ORIGEM_ABS" -o "$OUT/.codex-$ID.log" "$PROMPT" || rc=$?
if [ "$rc" = 1 ] || [ "$rc" = 3 ]; then
  "$PY" -m mediakit.cenas registrar "$OUT" "$ID" falha >/dev/null
  echo "A geração de $ID falhou (código $rc) e gastou uma chamada. Não tente de novo sozinho: pergunte ao Ugo." >&2
fi
[ "$rc" = 0 ] || exit "$rc"
test -s "$OUT/$ID.png" && echo "OK $OUT/$ID.png"

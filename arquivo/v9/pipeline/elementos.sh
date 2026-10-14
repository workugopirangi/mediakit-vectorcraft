#!/usr/bin/env bash
# elementos.sh: gera UM elemento gráfico próprio do evento pelo Codex (GPT Image, cota do ChatGPT do Ugo), no molde do
# cena.sh. É o que faz dois kits deixarem de sair iguais: cada evento ganha objetos, ilustrações, pictogramas, texturas,
# patterns e adesivos derivados do próprio sentido (motivos) e desenhados no estilo da família da receita
# (contratos em references/07-elementos.md e references/08-sistema-elementos.md). Texto nunca vem daqui: selo,
# microtexto, numeral e afins saem por código no grafismos.py (aprendizado 7).
#
# Uso:  bash elementos.sh <pasta-do-kit> <id> <tipo> --descricao-de <arquivo> [opções]
#       bash elementos.sh <pasta-do-kit> <id> --tipo <tipo> --descricao-de <arquivo> [opções]
#       A descrição (inglês) vem de um ARQUIVO: ela traz campos do evento, e um $(...) ou uma crase dentro de aspas duplas
#       rodaria no shell de quem chama, antes de chegar aqui. Com "-" no lugar do arquivo, ela vem da entrada padrão
#       (heredoc com aspas simples no EOT: <<'EOT', nada dentro é expandido). Quebras de linha viram espaço.
#       Forma antiga, ainda aceita com aviso no stderr: a descrição como 4º argumento (ou 3º, com --tipo).
#   tipo: objeto | ilustracao | pictograma | textura | pattern | adesivo   (ornamento = objeto, nome da v1)
#   opções:
#     --material <m>       só objeto: metal-escovado | ouro | couro | borracha | tecido | vidro-fosco | plastico-fosco | madeira |
#                          papel | grama. Acrescenta ao prompt "studio product render, physically based <material>, key light
#                          from the <luz> at 35 degrees, ..." (elementos_prompt.MATERIAIS) e vai para a ficha
#     --estilo "<bloco>"   estilo da família (sistema_elementos.familias[].estilo, inglês), repetido em todo membro
#     --paleta "#hex,..."  cores da família; o prompt leva o NOME da cor, nunca o hex (aprendizado 23)
#     --aspecto <a>        quadrado | largo | alto | faixa (do encaixe; padrão quadrado)
#     --ref <png>          âncora de estilo da família, anexada ao Codex com -i ("match the rendering style ... not its subject")
#     --familia <id>  --motivo <id>  --luz esquerda|direita|cima      (vão para o prompt e para a ficha)
#     --pagina <rótulo>    o elemento nasce para esta página da composição (ativo:2, cota:Master, capa:c): o prompt leva área
#                          e proporção reais, lado da página, para onde olha, borda que o corta e luz da foto da página
#     --elemento <id>      id do elemento na composição dessa página (padrão: o <id> que está sendo gerado)
#     --composicao <pasta> pasta do kit com a `composicao` (padrão: a <pasta-do-kit> da chamada)
#     --receita <id>       qual plano-elementos-<receita>.json dá a caixa resolvida (padrão: o primeiro que tem o elemento)
#   ELEMENTOS_DRY=1      não chama o Codex nem grava nada: imprime o prompt completo e o comando exato, e sai 0.
# Saída: <pasta>/acervo/elementos/<id>.png (com alfa), <id>.bruto.png (o que o gerador devolveu, intocado),
#        <id>.prompt.txt, <id>.meta.json (tipo, família, motivo, estilo, paleta, aspecto, ref, rota, sha256, alfa medido,
#        gerações contadas no log do Codex, data), .codex-<id>.log e uma linha em elementos.log.
#
# Transparência (medida pelo padrao.py alfa, nunca suposta):
#   codex-alfa           o gerador devolveu PNG com canal alfa real: usa como veio (6 de 6 em 09/10/2026)
#   codex-branco+chroma  pattern e textura sem alfa: o prompt pediu branco chapado; padrao.py separar tira o fundo pela cor
#   codex-cinza+rembg    objeto, ilustração, pictograma e adesivo sem alfa: o prompt pediu cinza 50% chapado;
#                        recortar.py --classe produto (isnet-general-use)
#
# Uma geração por imagem: não regera se <id>.bruto.png existe e abre inteiro (truncado ou ilegível, é apagado e gerado de
# novo), e o Codex é proibido de regerar ou de editar o PNG com código (senão a medida de alfa nativo mente). Defeitos
# vêm listados no log; quem decide regerar é o Ugo.
# A proveniência só muda junto com uma geração: o <id>.prompt.txt é gravado por quem chamou o Codex. Rodar de novo com um
# pedido diferente do que gerou o bruto (outro --estilo, outra descrição) não regera, não reescreve prompt nem ficha e sai
# com 65, para a ficha não dizer que o estilo novo fez uma imagem que o antigo fez. Rodar de novo com o MESMO pedido só
# completa o que faltou (rota, <id>.png, ficha), por exemplo depois de um erro no recorte, sem gastar cota.
#
# Codex que falha, repete no Codex (codex_gerar.sh): até 3 tentativas por chamada, com espera crescente, quando ele sai com
# erro sem imagem ou entrega PNG truncado; cota ou login esgotados param na hora. Nunca outro fornecedor. Uma chamada por vez
# por kit (trava em <pasta>/acervo/.codex.lock). A saída das tentativas que falharam fica em .codex-<id>.saida.
# Códigos de saída: 0 ok, 1 o Codex não entregou, 2 Codex não instalado, 3 cota ou login do Codex (espere e rode de novo),
# 4 outra chamada segura a trava, 5 o Python do kit não abre PNG (falta o PIL), 64 uso, 65 o pedido mudou mas o bruto é da
# geração anterior, 66 arquivo da descrição (ou da --ref) ausente ou vazio.
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
PY="${MEDIAKIT_PY:-$HOME/.venvs/mediakit/bin/python}"
. "$AQUI/codex_gerar.sh"

uso() {
  cat >&2 <<'EOT'
uso: bash elementos.sh <pasta-do-kit> <id> <tipo> --descricao-de <arquivo> [opções]
     bash elementos.sh <pasta-do-kit> <id> --tipo <tipo> --descricao-de <arquivo> [opções]
     (--descricao-de - lê a descrição da entrada padrão; a descrição na linha de comando ainda passa, com aviso)
tipo: objeto | ilustracao | pictograma | textura | pattern | adesivo   (ornamento = objeto)
opções: --estilo "<bloco>" --paleta "#hex,#hex" --aspecto quadrado|largo|alto|faixa --ref <png>
        --familia <id> --motivo <id> --luz esquerda|direita|cima
        --material metal-escovado|ouro|couro|borracha|tecido|vidro-fosco|plastico-fosco|madeira|papel|grama   (só objeto)
        --pagina <rótulo> [--elemento <id>] [--composicao <pasta>] [--receita <id>]   (o elemento nasce para a página da composição)
ELEMENTOS_DRY=1: imprime o prompt e o comando, não chama o Codex (não gasta cota) e não grava nada.
EOT
  exit 64
}

POS=(); TIPO_OPT=""; ESTILO=""; PALETA=""; ASPECTO=""; REF=""; FAMILIA=""; MOTIVO=""; LUZ=""; COMPOSICAO=""; PAGINA=""; ELEMENTO=""; RECEITA=""
MATERIAL=""; DESC_DE=""
valor() { [ $# -ge 2 ] || { echo "falta o valor de $1" >&2; uso; }; }
while [ $# -gt 0 ]; do
  case "$1" in
    --tipo)    valor "$@"; TIPO_OPT="$2"; shift 2;;
    --estilo)  valor "$@"; ESTILO="$2"; shift 2;;
    --paleta)  valor "$@"; PALETA="$2"; shift 2;;
    --aspecto) valor "$@"; ASPECTO="$2"; shift 2;;
    --ref)     valor "$@"; REF="$2"; shift 2;;
    --familia) valor "$@"; FAMILIA="$2"; shift 2;;
    --motivo)  valor "$@"; MOTIVO="$2"; shift 2;;
    --luz)     valor "$@"; LUZ="$2"; shift 2;;
    --composicao) valor "$@"; COMPOSICAO="$2"; shift 2;;
    --pagina)  valor "$@"; PAGINA="$2"; shift 2;;
    --elemento) valor "$@"; ELEMENTO="$2"; shift 2;;
    --receita) valor "$@"; RECEITA="$2"; shift 2;;
    --material) valor "$@"; MATERIAL="$2"; shift 2;;
    --descricao-de) valor "$@"; DESC_DE="$2"; shift 2;;
    -h|--help) uso;;
    --*)       echo "opção desconhecida: $1" >&2; uso;;
    *)         POS+=("$1"); shift;;
  esac
done
if [ -n "$DESC_DE" ]; then
  case ${#POS[@]} in
    3) PASTA="${POS[0]}"; ID="${POS[1]}"; TIPO="${POS[2]}";;
    2) PASTA="${POS[0]}"; ID="${POS[1]}"; TIPO="$TIPO_OPT";;
    4) echo "descrição dada duas vezes: na linha de comando e em --descricao-de $DESC_DE" >&2; exit 64;;
    *) uso;;
  esac
else
  case ${#POS[@]} in
    4) PASTA="${POS[0]}"; ID="${POS[1]}"; TIPO="${POS[2]}"; DESC="${POS[3]}";;
    3) PASTA="${POS[0]}"; ID="${POS[1]}"; DESC="${POS[2]}"; TIPO="$TIPO_OPT";;
    *) uso;;
  esac
  echo "aviso: a descrição veio na linha de comando. Um \$(...) ou uma crase dentro de aspas duplas já rodou no seu shell antes de chegar aqui; grave a descrição num arquivo e use --descricao-de <arquivo> (ou --descricao-de - com <<'EOT')" >&2
fi
if [ -n "$TIPO_OPT" ] && [ "$TIPO_OPT" != "$TIPO" ]; then echo "tipo dado duas vezes e diferente: $TIPO e $TIPO_OPT" >&2; exit 64; fi
[ "$TIPO" = ornamento ] && TIPO=objeto   # nome da v1, mesma coisa
case "$TIPO" in
  objeto|ilustracao|pictograma|textura|pattern|adesivo) ;;
  "") echo "falta o tipo" >&2; uso;;
  *) echo "tipo inválido: $TIPO (texto, selo, microtexto e afins são grafismo por código: grafismos.py)" >&2; exit 64;;
esac
id_valido "$ID" || { echo "id inválido: $ID (só a-z, 0-9 e hífen, sem começar por hífen, como no schema)" >&2; exit 64; }
case "${ASPECTO:-quadrado}" in quadrado|largo|alto|faixa) ;; *) echo "aspecto inválido: $ASPECTO" >&2; exit 64;; esac
case "${LUZ:-esquerda}" in esquerda|direita|cima) ;; *) echo "luz inválida: $LUZ" >&2; exit 64;; esac
if [ -n "$DESC_DE" ]; then
  # o conteúdo entra como dado: cat dentro de $(...) não reavalia o texto, e ele segue para o Python só por argv
  if [ "$DESC_DE" = "-" ]; then
    DESC="$(cat)"
  else
    [ -f "$DESC_DE" ] && [ -r "$DESC_DE" ] || { echo "--descricao-de: o arquivo não existe ou não abre: $DESC_DE (nada foi enviado ao Codex)" >&2; exit 66; }
    DESC="$(cat "$DESC_DE")"
  fi
  DESC="$(printf '%s' "$DESC" | tr '\r\n\t' '   ' | sed -e 's/  */ /g' -e 's/^ //' -e 's/ $//')"
  [ -n "$DESC" ] || { echo "a descrição de ${DESC_DE} está vazia (nada foi enviado ao Codex)" >&2; exit 66; }
fi
if [ -n "$PALETA" ]; then
  for c in $(printf '%s' "$PALETA" | tr ',' ' '); do
    printf '%s' "$c" | grep -Eq '^#[0-9A-Fa-f]{6}$' || { echo "cor inválida na paleta: $c (use #RRGGBB)" >&2; exit 64; }
  done
fi

DRY="${ELEMENTOS_DRY:-}"; [ "$DRY" = 0 ] && DRY=""
abs() { case "$1" in /*) printf '%s' "$1";; *) printf '%s/%s' "$PWD" "$1";; esac; }
if [ -n "$DRY" ]; then
  OUT="$(abs "$PASTA")/acervo/elementos"    # modo seco não cria pasta nenhuma
else
  mkdir -p "$PASTA/acervo/elementos"
  OUT="$(cd "$PASTA/acervo/elementos" && pwd)"   # caminho absoluto: o Codex roda em outra pasta de trabalho
fi
BRUTO="$OUT/$ID.bruto.png"; FINAL="$OUT/$ID.png"; LOG="$OUT/.codex-$ID.log"

REF_ABS=""
if [ -n "$REF" ]; then
  if [ -f "$REF" ]; then
    REF_ABS="$(cd "$(dirname "$REF")" && pwd)/$(basename "$REF")"
  elif [ -n "$DRY" ]; then
    REF_ABS="$(abs "$REF")"; echo "aviso: --ref não existe: $REF_ABS (fora do modo seco o script para aqui)" >&2
  else
    echo "--ref não existe: $REF" >&2; exit 66
  fi
fi

ARGS=(prompt --tipo "$TIPO" "--descricao=$DESC" --saida "$BRUTO")   # com "=": descrição que começa por "-" não vira opção
[ -n "$ESTILO" ] && ARGS+=(--estilo "$ESTILO")
[ -n "$PALETA" ] && ARGS+=(--paleta "$PALETA")
[ -n "$ASPECTO" ] && ARGS+=(--aspecto "$ASPECTO")
[ -n "$MOTIVO" ] && ARGS+=(--motivo "$MOTIVO")
[ -n "$LUZ" ] && ARGS+=(--luz "$LUZ")
[ -n "$REF_ABS" ] && ARGS+=(--ref)
[ -n "$MATERIAL" ] && ARGS+=(--material "$MATERIAL")
COMP_ARGS=()
if [ -n "$PAGINA" ] || [ -n "$COMPOSICAO" ] || [ -n "$ELEMENTO" ]; then
  [ -n "$PAGINA" ] || { echo "composição pede --pagina <rótulo> (ativo:2, cota:Master, capa:c)" >&2; exit 64; }
  COMP_ARGS=(--composicao "$(abs "${COMPOSICAO:-$PASTA}")" --pagina "$PAGINA" --elemento "${ELEMENTO:-$ID}")
  [ -n "$RECEITA" ] && COMP_ARGS+=(--receita "$RECEITA")
  ARGS+=("${COMP_ARGS[@]}")
fi
PROMPT="$("$PY" "$AQUI/elementos_prompt.py" "${ARGS[@]}")"

# CODEX_SANDBOX (codex_gerar.sh) = --sandbox workspace-write sem rede, e -C: o Codex grava o PNG na pasta do kit; -i anexa a
# âncora (antes do -o: o -i aceita vários arquivos e engoliria o prompt se viesse por último); -o guarda a última mensagem dele.
CMD=(codex exec "${CODEX_SANDBOX[@]}" -C "$OUT" --skip-git-repo-check)
[ -n "$REF_ABS" ] && CMD+=(-i "$REF_ABS")
CMD+=(-o "$LOG" "$PROMPT")

if [ -n "$DRY" ]; then
  echo "== ELEMENTOS_DRY: nada foi gerado nem gravado; cota intacta"
  echo "tipo=$TIPO aspecto=${ASPECTO:-quadrado} familia=${FAMILIA:--} motivo=${MOTIVO:--} ref=${REF_ABS:--}${MATERIAL:+ material=$MATERIAL}"
  if png_ok "$BRUTO"; then echo "(já existe $BRUTO: fora do modo seco o Codex NÃO seria chamado)"
  elif [ -e "$BRUTO" ]; then echo "(existe $BRUTO mas não abre inteiro: fora do modo seco seria apagado e gerado de novo)"; fi
  echo "== PROMPT"
  printf '%s\n' "$PROMPT"
  echo "== COMANDO"
  printf '%q ' "${CMD[@]}"; echo
  exit 0
fi

PROMPT_TXT="$OUT/$ID.prompt.txt"
# Roda DENTRO da trava, logo depois de o Codex entregar: a proveniência (o prompt) nasce junto da geração, nunca sem ela, e a
# chamada que esperava a trava já a encontra ao acordar.
codex_apos_gerar() { printf '%s\n' "$PROMPT" > "$PROMPT_TXT"; }
if png_ok "$BRUTO"; then
  echo "já existe: $BRUTO (não regero; apague para gerar de novo, gastando cota)"
else
  command -v codex >/dev/null 2>&1 || { echo "codex não encontrado: instale, entre com \`codex login\` e rode de novo; não troque de fornecedor" >&2; exit 2; }
  codex_produzir 1 "$(dirname "$OUT")" "$BRUTO" "$OUT/.codex-$ID.saida" "${CMD[@]}" || exit $?
fi
if [ "$CODEX_GEROU" != 1 ]; then               # este processo não gerou o bruto: confere, não reescreve
  if [ -s "$PROMPT_TXT" ] && [ "$(cat "$PROMPT_TXT")" != "$PROMPT" ]; then
    echo "o pedido mudou, mas $BRUTO é da geração anterior (o prompt dela está em $PROMPT_TXT). Não regero e não mexo no prompt nem na ficha, para a proveniência não mentir. Para gerar de novo com o pedido novo, apague $BRUTO (gasta cota)" >&2
    exit 65
  fi
  if [ "$CODEX_OUTRA" = 1 ]; then                # a outra chamada, que gerou, é quem termina a rota e a ficha
    echo "a outra chamada que gerou $BRUTO termina a rota e a ficha; se ela cair, rode de novo (completa sem cota)"
    exit 0
  fi
  if png_ok "$FINAL" && [ -s "$OUT/$ID.meta.json" ] && [ ! "$BRUTO" -nt "$FINAL" ]; then
    echo "completo: $FINAL e a ficha já valem para este bruto; nada a refazer"
    exit 0
  fi
fi
PROMPT_ARG=(); [ -s "$PROMPT_TXT" ] && PROMPT_ARG=(--prompt "$PROMPT_TXT")

# Mede o alfa e escolhe a rota. padrao.py alfa sai 0 quando há alfa real, 1 quando não há.
MEDIDA="$("$PY" "$AQUI/padrao.py" alfa "$BRUTO" || true)"
echo "$MEDIDA"
RESERVA="$("$PY" "$AQUI/elementos_prompt.py" reserva "$TIPO")"
if printf '%s' "$MEDIDA" | grep -q "ALFA: sim"; then
  ROTA="codex-alfa"; cp "$BRUTO" "$FINAL"
elif [ "$RESERVA" = branco ]; then
  ROTA="codex-branco+chroma"; "$PY" "$AQUI/padrao.py" separar "$BRUTO" "$FINAL" --fundo "#FFFFFF"
else
  ROTA="codex-cinza+rembg"; "$PY" "$AQUI/recortar.py" "$BRUTO" "$FINAL" --classe produto
fi
"$PY" "$AQUI/padrao.py" alfa "$FINAL" >/dev/null || { echo "!! $FINAL saiu sem alfa depois da rota $ROTA" >&2; exit 1; }
DECLARADO="$(grep -ho 'TRANSPARENT: *[a-z]*' "$LOG" 2>/dev/null | head -1 || true)"
"$PY" "$AQUI/elementos_prompt.py" meta --id "$ID" --pasta "$OUT" --png "$FINAL" --bruto "$BRUTO" --tipo "$TIPO" \
  --rota "$ROTA" --familia "$FAMILIA" --motivo "$MOTIVO" --estilo "$ESTILO" --paleta "$PALETA" --aspecto "${ASPECTO:-quadrado}" \
  --luz "$LUZ" --ref "$REF_ABS" --codex-disse "${DECLARADO:-}" "--descricao=$DESC" --material "$MATERIAL" ${PROMPT_ARG[@]+"${PROMPT_ARG[@]}"} ${COMP_ARGS[@]+"${COMP_ARGS[@]}"}
printf '%s\t%s\t%s\trota=%s\tcodex_disse=%s\t%s\tref=%s\n' "$(date +%Y-%m-%d_%H%M)" "$ID" "$TIPO" "$ROTA" "${DECLARADO:-?}" \
  "$(printf '%s' "$MEDIDA" | head -1)" "$( [ -n "$REF_ABS" ] && basename "$REF_ABS" || echo -)" >> "$OUT/elementos.log"
echo "OK $FINAL rota=$ROTA"

#!/usr/bin/env bash
# codex_gerar.sh: o que os três scripts que geram imagem pelo Codex (elementos.sh, cena.sh, cena_limpar.sh) têm em comum.
# Não se executa: os scripts fazem `source`. Regra do Ugo (09/10/2026): REPETIR NO CODEX ATÉ SAIR, nunca trocar de
# fornecedor (outro gerador entrega outro estilo, e o kit deixa de parecer um só).
#
#  1. Erro passageiro: o Codex sai com código diferente de 0 sem entregar imagem, ou entrega um PNG truncado ou ilegível
#     (que não abre inteiro no PIL). Repete até MEDIAKIT_CODEX_TENTATIVAS vezes (padrão 3), esperando
#     MEDIAKIT_CODEX_ESPERA x nº da tentativa segundos (padrão 10: 10 s depois da 1ª, 20 s depois da 2ª). Esgotadas,
#     sai com código 1 e diz onde está a saída de cada tentativa. Saída sem imagem com código 0 conta como falha também.
#  2. Cota ou login: se a saída do Codex fala de rate limit, usage limit, quota, 401, 429, not logged in ou sign in, PARA NA
#     HORA, sem repetir (repetir gasta o que sobrou da cota), com código 3 e a frase "cota do Codex: espere e rode de novo;
#     não troque de fornecedor". Só se procura isso depois de uma tentativa SEM imagem, e as linhas do próprio prompt
#     (que o Codex ecoa e que citam "quota") são descartadas antes de procurar.
#  3. Uma chamada por vez: trava por arquivo (flock) em <acervo>/.codex.lock, a mesma para os três scripts do kit. Quem
#     chega com a trava ocupada espera (até MEDIAKIT_CODEX_ESPERA_TRAVA, padrão 900 s; passou, sai com 4). O sistema solta a
#     trava quando o processo termina, até por kill -9, então não existe trava velha para limpar à mão. Pasta que não aceita
#     flock (rede, por exemplo): avisa e segue sem a trava, em vez de esperar uma trava impossível.
#  4. PNG que já existe: pula a geração se abrir inteiro (png_ok). Truncado ou ilegível, é apagado e gerado de novo, mas só
#     DEPOIS de pegar a trava: fora dela o arquivo pode ser o que outra chamada está gravando agora. Regerar por cima de
#     uma imagem boa (cena.sh) guarda a anterior e a devolve se nenhuma tentativa entregar.
#  5. Antes de gastar cota, confere que o Python do kit abre PNG (PIL). Sem isso toda imagem pareceria quebrada e o script
#     gastaria as 3 tentativas à toa; sai com 5.
#  6. Sandbox de TODA chamada (CODEX_SANDBOX): escreve só na pasta de trabalho e sem rede para os comandos que o Codex roda.
#     O ~/.codex/config.toml do Ugo tem sandbox_mode="danger-full-access"; o --sandbox da linha de comando vence o arquivo,
#     e a rede fechada impede que um comando disparado por texto vindo do evento saia para a internet.
#  7. Id de arquivo (id_valido): só a-z, 0-9 e hífen, sem começar por hífen. Id é nome de arquivo; "../../X" escreveria fora.
#
# Funções (usam $PY, o Python do kit):
#   id_valido <id>                  0 se o id só tem a-z, 0-9 e hífen (e não começa por hífen); vazio ou com quebra de linha, não
#   png_ok <png>                    0 se o arquivo existe, não é vazio e o PIL o decodifica inteiro (não apaga nada)
#   codex_cota <saida> <cmd...>     0 e imprime a linha denunciadora se a <saida> do Codex fala de cota ou login
#   codex_travar <pasta>            pega a trava de <pasta> (fd 9); 4 se esperou mais que MEDIAKIT_CODEX_ESPERA_TRAVA
#   codex_soltar                    solta a trava
#   codex_gerar <png> <historico> <cmd...>
#                                   roda <cmd> (o `codex exec ...`) até <png> abrir inteiro; <historico> recebe a saída de
#                                   cada tentativa que falhou. Retorna 0 gerou, 1 desistiu, 3 cota ou login, 5 sem PIL
#   codex_produzir <pular 1|0> <pasta-da-trava> <png> <historico> <cmd...>
#                                   trava + (se pular=1 e outra chamada já gerou o <png>, não gera) + codex_gerar + solta.
#                                   CODEX_GEROU fica 1 só quando ESTE processo chamou o Codex e ele entregou (0 se pulou);
#                                   CODEX_OUTRA fica 1 quando pulou porque OUTRA chamada gerou enquanto esta esperava a trava.
#                                   Se existir a função codex_apos_gerar, ela roda DENTRO da trava, logo depois de gerar (é onde
#                                   se grava a proveniência: quem esperava a trava já a encontra ao acordar)
# Códigos de saída que os scripts repassam: 0 ok, 1 o Codex não entregou, 2 sem Codex instalado, 3 cota ou login,
# 4 trava ocupada, 5 Python do kit sem PIL, 64 uso. Compatível com o bash 3.2 do macOS (sem array associativo, sem mapfile).

PY="${PY:-${MEDIAKIT_PY:-$HOME/.venvs/mediakit/bin/python}}"
CODEX_PNG=""
CODEX_ANTERIOR=""
CODEX_ATUAL=""
CODEX_GEROU=0
CODEX_OUTRA=0
CODEX_SANDBOX=(--sandbox workspace-write -c sandbox_workspace_write.network_access=false)

# O alfabeto vai escrito por extenso: com a-z a faixa muda de sentido conforme o idioma do sistema. O case olha a string
# inteira, então "ok\n../../X" (quebra de linha no meio) também reprova, o que o grep linha a linha deixava passar.
id_valido() {
  case "$1" in
    ""|-*|*[!abcdefghijklmnopqrstuvwxyz0123456789-]*) return 1;;
  esac
  return 0
}

png_ok() {
  [ -s "$1" ] || return 1
  "$PY" -c 'import sys
from PIL import Image
try:
    with Image.open(sys.argv[1]) as im:
        im.load()
except Exception:
    sys.exit(1)' "$1" 2>/dev/null
}

# A saída do Codex fala de cota ou de login? Imprime a linha que denuncia e sai 0; sai 1 se nada denuncia. Descarta antes as
# linhas que são do próprio prompt (os argumentos do comando): o Codex as ecoa, e elas citam "quota".
codex_cota() {
  local saida="$1"
  shift
  "$PY" - "$saida" "$@" <<'PYEOF'
import re, sys
ansi = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
limpa = lambda s: ansi.sub("", s).strip()
linhas = [limpa(l) for l in open(sys.argv[1], errors="replace").read().splitlines()]
eco = {limpa(l) for arg in sys.argv[2:] for l in arg.splitlines() if limpa(l)}
cauda = [l for l in linhas if l and l not in eco][-80:]
padroes = [
    r"rate[ _-]?limit", r"usage[ _-]?limit", r"too many requests", r"insufficient[ _-]?quota", r"payment required",
    r"\bquota\b.{0,60}\b(?:exceed\w*|exhaust\w*|reach\w*|deplet\w*|ran out|used up|over|left|remaining|limit\w*)\b",
    r"\b(?:exceed\w*|exhaust\w*|reach\w*|hit|used up|out of|ran out of|no more|no)\b.{0,40}\bquota\b",
    r"\b(?:hit|reached|exceeded|exhausted)\b\W+(?:\w+\W+){0,4}limit",
    r"(?:status|http|code|error)\W{0,15}(?:401|402|429)(?![\d,.])", r"\b(?:401|402|429)\s+(?:unauthori[sz]ed|payment|too many)",
    r"unauthori[sz]ed", r"authentication (?:failed|required|error)", r"not (?:logged|signed) in", r"\bsign[ -]?in\b",
    r"\blog[ -]?in\b.{0,20}(?:required|first|again)", r"codex login", r"invalid[ _-]?api[ _-]?key", r"incorrect api key",
    r"(?:access|refresh|auth\w*)[ _-]?token.{0,60}(?:expired|invalid|revoked|refresh\w*)",
]
for linha in cauda:
    for padrao in padroes:
        if re.search(padrao, linha, re.I):
            print(linha[:200])
            sys.exit(0)
sys.exit(1)
PYEOF
}

# Trava por arquivo. O fd 9 fica aberto neste shell e o flock é pego por um Python que herda esse fd: o travamento pertence à
# descrição do arquivo aberto, então continua valendo depois que o Python sai e só acaba quando este shell fecha o fd 9
# (codex_soltar) ou morre. O arquivo nunca é apagado (apagar uma trava que alguém espera é a corrida clássica do flock).
codex_travar() {
  local pasta="$1" limite="${MEDIAKIT_CODEX_ESPERA_TRAVA:-900}" rc=0
  mkdir -p "$pasta" || return 1
  exec 9>>"$pasta/.codex.lock" || { echo "não consegui abrir a trava $pasta/.codex.lock" >&2; return 1; }
  "$PY" - "$limite" "$pasta/.codex.lock" <<'PYEOF' || rc=$?
import fcntl, sys, time
limite, caminho = float(sys.argv[1]), sys.argv[2]
inicio, avisou = time.time(), False
while True:
    try:
        fcntl.flock(9, fcntl.LOCK_EX | fcntl.LOCK_NB)
        sys.exit(0)
    except BlockingIOError:
        pass                                  # ocupada: outra chamada segura a trava
    except OSError as erro:
        print(f"{caminho} não aceita trava ({erro}); sigo sem ela, então confira que não há outra chamada do Codex no kit", file=sys.stderr)
        sys.exit(5)
    if not avisou:
        print(f"esperando a outra chamada do Codex terminar ({caminho}): uma por vez", file=sys.stderr)
        avisou = True
    if time.time() - inicio >= limite:
        print(f"outra chamada do Codex segura {caminho} há {int(limite)} s; espere ela terminar e rode de novo", file=sys.stderr)
        sys.exit(4)
    time.sleep(0.5)
PYEOF
  if [ "$rc" -eq 5 ]; then               # a pasta não aceita flock: avisou, segue sem trava
    exec 9>&-
    return 0
  fi
  if [ "$rc" -ne 0 ]; then
    exec 9>&-
    return "$rc"
  fi
}

codex_soltar() {
  exec 9>&- || true
}

# Devolve a imagem anterior (guardada por codex_gerar) quando a regeração não entregou outra.
codex_restaurar() {
  if [ -n "$CODEX_ANTERIOR" ] && [ -e "$CODEX_ANTERIOR" ]; then
    rm -f "$CODEX_PNG"
    mv -f "$CODEX_ANTERIOR" "$CODEX_PNG"
    echo "ficou a imagem anterior: $CODEX_PNG" >&2
  fi
  CODEX_ANTERIOR=""
}

codex_gerar() {
  local png="$1" hist="$2" max n=1 rc res=1 achado espera
  shift 2
  max="${MEDIAKIT_CODEX_TENTATIVAS:-3}"
  case "$max" in ''|*[!0-9]*|0) max=3;; esac
  "$PY" -c 'import PIL.Image' 2>/dev/null || {
    echo "o Python do kit ($PY) não abre PNG (falta o PIL): não dá para conferir o que o Codex gera, e cada tentativa gastaria cota à toa. Corrija MEDIAKIT_PY (padrão ~/.venvs/mediakit/bin/python) e rode de novo" >&2
    return 5
  }
  CODEX_ATUAL="$(mktemp "${TMPDIR:-/tmp}/codex-saida.XXXXXX")" || return 1
  CODEX_PNG="$png"
  CODEX_ANTERIOR=""
  rm -f "$hist"
  if [ -e "$png" ]; then
    if png_ok "$png"; then
      CODEX_ANTERIOR="$png.anterior"
      mv -f "$png" "$CODEX_ANTERIOR"
    else
      echo "$png existe mas não abre inteiro (truncado ou ilegível): apago e gero de novo" >&2
      rm -f "$png"
    fi
  fi
  trap 'codex_restaurar; rm -f "$CODEX_ATUAL"; exit 130' INT
  trap 'codex_restaurar; rm -f "$CODEX_ATUAL"; exit 143' TERM
  while :; do
    rm -f "$png"                       # a tentativa nunca herda o PNG truncado da anterior
    rc=0
    "$@" 9>&- 2>&1 | tee "$CODEX_ATUAL" 9>&- || rc="${PIPESTATUS[0]}"   # nem o Codex nem o tee herdam a trava (fd 9)
    if png_ok "$png"; then
      [ "$rc" -eq 0 ] || echo "o Codex saiu com código $rc mas entregou $png inteiro: aceito" >&2
      [ "$n" -eq 1 ] || echo "o Codex entregou na tentativa $n de $max (as que falharam estão em $hist)" >&2
      [ -z "$CODEX_ANTERIOR" ] || rm -f "$CODEX_ANTERIOR"
      CODEX_ANTERIOR=""
      res=0
      break
    fi
    { echo "== tentativa $n de $max (código $rc)"; cat "$CODEX_ATUAL"; } >> "$hist"
    if achado="$(codex_cota "$CODEX_ATUAL" "$@")"; then
      echo "cota do Codex: espere e rode de novo; não troque de fornecedor" >&2
      echo "  (a saída do Codex diz: $achado; ela inteira está em $hist)" >&2
      res=3
      break
    fi
    [ ! -e "$png" ] || echo "tentativa $n: $png saiu truncado ou ilegível; apago e repito" >&2
    rm -f "$png"
    if [ "$n" -ge "$max" ]; then
      echo "o Codex não entregou $png em $max tentativa(s) (último código $rc); a saída de cada uma está em $hist. Rode de novo mais tarde; não troque de fornecedor" >&2
      res=1
      break
    fi
    espera="$(awk -v b="${MEDIAKIT_CODEX_ESPERA:-10}" -v n="$n" 'BEGIN { printf "%g", b * n }')"
    echo "tentativa $n de $max falhou (código $rc); espero ${espera}s e repito no Codex" >&2
    sleep "$espera"
    n=$((n + 1))
  done
  [ "$res" -eq 0 ] || codex_restaurar
  rm -f "$CODEX_ATUAL"
  trap - INT TERM
  return "$res"
}

codex_produzir() {
  local pular="$1" pasta="$2" png="$3" hist="$4" rc=0
  shift 4
  CODEX_GEROU=0
  CODEX_OUTRA=0
  codex_travar "$pasta" || return $?
  if [ "$pular" = 1 ] && png_ok "$png"; then
    codex_soltar
    CODEX_OUTRA=1
    echo "já existe: $png (outra chamada o gerou enquanto esta esperava a trava)"
    return 0
  fi
  codex_gerar "$png" "$hist" "$@" || rc=$?
  if [ "$rc" -eq 0 ]; then
    CODEX_GEROU=1
    if type codex_apos_gerar >/dev/null 2>&1; then
      codex_apos_gerar || { echo "codex_apos_gerar falhou: a imagem existe mas o que devia nascer junto com ela não foi gravado" >&2; rc=1; }
    fi
  fi
  codex_soltar
  return "$rc"
}

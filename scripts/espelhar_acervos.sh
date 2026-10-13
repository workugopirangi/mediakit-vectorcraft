#!/usr/bin/env bash
# Espelha CLIENTES/*/MEDIAKIT do cofre em acervos/<CLIENTE>/ (a fonte é o cofre; isto é cópia). Uso: scripts/espelhar_acervos.sh
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
CL="$HOME/Developer/UGO's Second Brain/01 EMPRESAS/MOTION PERFORM/CLIENTES"
for m in "$CL"/*/MEDIAKIT; do
  c="$(basename "$(dirname "$m")")"
  mkdir -p "$RAIZ/acervos/$c"
  rsync -a --delete --exclude '.codex*' --exclude '*.log' --exclude '.claude' "$m/" "$RAIZ/acervos/$c/MEDIAKIT/"
done
du -sh "$RAIZ/acervos"

#!/usr/bin/env bash
# Monta o VectorCraft na versão travada em vectorcraft/VERSAO. Uso: scripts/montar_vectorcraft.sh
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
REPO="${MEDIAKIT_VC_REPO:-$HOME/Developer/vectorcraft}"
VERSAO="$(cat "$RAIZ/vectorcraft/VERSAO")"
[ -d "$REPO/.git" ] || git clone https://github.com/storytold/vectorcraft.git "$REPO"
git -C "$REPO" fetch --quiet origin
git -C "$REPO" checkout --quiet "$VERSAO"
( cd "$REPO" && cargo build --release )
ls -la "$REPO/target/release/vectorcraft-cli"

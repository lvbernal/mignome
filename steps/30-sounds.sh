#!/usr/bin/env bash
# Tema de sonido "__custom": hereda de Yaru y cambia el sonido de alerta (campana).
set -euo pipefail
source "$(dirname "$0")/../lib/common.sh"

SRC="$MIGNOME_ROOT/assets/sounds/__custom"
DEST="$HOME/.local/share/sounds/__custom"

log "Tema de sonido"
mkdir -p "$DEST"
cp "$SRC/index.theme" "$DEST/index.theme"
while read -r name target; do
    [[ -e "$target" ]] || warn "no existe $target (sonido $name)"
    ln -sfn "$target" "$DEST/$name"
done < <(read_list "$SRC/links.txt")
info "instalado en $DEST"

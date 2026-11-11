#!/usr/bin/env bash
# Valida dconf/*.ini contra los esquemas instalados y los carga (fusiona) en dconf.
set -euo pipefail
source "$(dirname "$0")/../lib/common.sh"

log "Validando claves contra los esquemas de GNOME $(gnome_major)"
python3 "$MIGNOME_ROOT/tools/mignome.py" check \
    || warn "hay claves que no existen en esta versión; se cargan de todos modos (dconf las ignora)"

log "Cargando configuración dconf"
for ini in "$MIGNOME_ROOT"/dconf/*.ini; do
    sed "s|@HOME@|$HOME|g" "$ini" | dconf load /
    info "$(basename "$ini")"
done

if [[ ! -f "$HOME/.config/background" ]]; then
    warn "aún no existe ~/.config/background: abre Bing Wall una vez para descargar el fondo"
fi

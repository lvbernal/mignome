#!/usr/bin/env bash
# Instala paquetes apt y snaps listados en config/.
set -euo pipefail
source "$(dirname "$0")/../lib/common.sh"

log "Paquetes apt"
mapfile -t apt_pkgs < <(read_list "$MIGNOME_ROOT/config/packages.apt")
available=()
for pkg in "${apt_pkgs[@]}"; do
    if apt-cache show "$pkg" >/dev/null 2>&1; then
        available+=("$pkg")
    else
        warn "el paquete apt '$pkg' no existe en esta versión; se omite"
    fi
done
sudo apt-get update -qq
sudo apt-get install -y "${available[@]}"

if command -v snap >/dev/null; then
    log "Snaps"
    while read -r snap_pkg; do
        if snap list "$snap_pkg" >/dev/null 2>&1; then
            info "$snap_pkg ya está instalado"
        else
            sudo snap install "$snap_pkg"
        fi
    done < <(read_list "$MIGNOME_ROOT/config/packages.snap")
else
    warn "snap no está disponible; se omiten los snaps"
fi

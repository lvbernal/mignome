#!/usr/bin/env bash
# Instala las extensiones de extensions.gnome.org y fija las listas de habilitadas/deshabilitadas.
# Variables: MIGNOME_UPGRADE=1 reinstala las extensiones de EGO aunque ya estén instaladas.
set -euo pipefail
source "$(dirname "$0")/../lib/common.sh"

EGO="https://extensions.gnome.org"
CONF="$MIGNOME_ROOT/config/extensions.txt"
shell_version="$(gnome_major)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
CURL=(curl -fsSL --connect-timeout 15 --max-time 120 --retry 2)

is_installed() { gnome-extensions info "$1" >/dev/null 2>&1; }

install_from_ego() {
    local uuid="$1" info_json download_url
    if is_installed "$uuid" && [[ "${MIGNOME_UPGRADE:-0}" != 1 ]]; then
        info "$uuid ya está instalada"
        return 0
    fi
    if ! info_json="$("${CURL[@]}" "$EGO/extension-info/?uuid=$uuid&shell_version=$shell_version")"; then
        warn "$uuid no tiene versión para GNOME $shell_version en extensions.gnome.org; se omite"
        return 1
    fi
    download_url="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["download_url"])' <<<"$info_json")"
    "${CURL[@]}" "$EGO$download_url" -o "$tmp/$uuid.zip"
    gnome-extensions install --force "$tmp/$uuid.zip"
    info "$uuid instalada"
}

log "Extensiones (GNOME $shell_version)"
enabled=()
disabled=()
while read -r source uuid state; do
    case "$source" in
        ego)    install_from_ego "$uuid" || continue ;;
        system) is_installed "$uuid" || { warn "$uuid no está instalada en el sistema; se omite"; continue; } ;;
        *)      warn "origen desconocido '$source' para $uuid"; continue ;;
    esac
    case "$state" in
        enabled)  enabled+=("'$uuid'") ;;
        disabled) disabled+=("'$uuid'") ;;
    esac
done < <(read_list "$CONF")

join() { local IFS=,; echo "[$*]"; }
gsettings set org.gnome.shell disable-user-extensions false
gsettings set org.gnome.shell enabled-extensions "$(join "${enabled[@]}")"
gsettings set org.gnome.shell disabled-extensions "$(join "${disabled[@]}")"
info "habilitadas: ${#enabled[@]}, deshabilitadas: ${#disabled[@]}"
info "las extensiones recién instaladas se cargan al cerrar e iniciar sesión"

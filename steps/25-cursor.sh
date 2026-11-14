#!/usr/bin/env bash
# Bibata Modern Classic no está empaquetado en Ubuntu; se instala en ~/.local/share/icons.
# El tema activo (cursor-theme) lo fija dconf/appearance.ini.
# Las apps X11 con un libXcursor anterior a 1.2.1 (p. ej. el snap de VS Code, que trae
# el de core20 y corre en XWayland) solo buscan en ~/.icons, así que se enlaza ahí también.
set -euo pipefail
source "$(dirname "$0")/../lib/common.sh"

NAME="Bibata-Modern-Classic"
VERSION="v2.0.7"
URL="https://github.com/ful1e5/Bibata_Cursor/releases/download/$VERSION/$NAME.tar.xz"
SHA256="7d3495864e5bbef02f5e77de760b2905903b63c71495a78ef6306d19a3b556d8"
ICON_DIR="$HOME/.local/share/icons"
DEST="$ICON_DIR/$NAME"
STAMP="$DEST/.mignome-version"
LEGACY_LINK="$HOME/.icons/$NAME"
CURL=(curl -fsSL --connect-timeout 15 --max-time 180 --retry 2)

link_legacy() {
    if [[ -L "$LEGACY_LINK" ]]; then
        [[ "$(readlink "$LEGACY_LINK")" == "$DEST" ]] && return
    elif [[ -e "$LEGACY_LINK" ]]; then
        warn "$LEGACY_LINK ya existe y no es un enlace; no se toca"
        return
    fi
    mkdir -p "$(dirname "$LEGACY_LINK")"
    ln -sfn "$DEST" "$LEGACY_LINK"
    info "Enlazado en $LEGACY_LINK (para apps X11 con libXcursor antiguo)"
}

log "Cursor"
if [[ -f "$STAMP" && "$(cat "$STAMP")" == "$VERSION" ]]; then
    info "$NAME $VERSION ya está instalado"
    link_legacy
    exit 0
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

"${CURL[@]}" "$URL" -o "$tmp/$NAME.tar.xz"
echo "$SHA256  $tmp/$NAME.tar.xz" | sha256sum -c --quiet - \
    || die "la suma SHA-256 de $NAME.tar.xz no coincide"
tar -xJf "$tmp/$NAME.tar.xz" -C "$tmp" --no-same-owner "$NAME"
[[ -f "$tmp/$NAME/index.theme" && -d "$tmp/$NAME/cursors" ]] \
    || die "el archivo de $NAME no tiene la estructura esperada"
echo "$VERSION" > "$tmp/$NAME/.mignome-version"

mkdir -p "$ICON_DIR"
rm -rf "$DEST"
mv "$tmp/$NAME" "$DEST"
info "$NAME $VERSION instalado en $DEST"
link_legacy

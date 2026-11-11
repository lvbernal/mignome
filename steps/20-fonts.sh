#!/usr/bin/env bash
# Atkinson Hyperlegible Mono no está empaquetada en Ubuntu; se instala en ~/.local/share/fonts.
set -euo pipefail
source "$(dirname "$0")/../lib/common.sh"

MONO_URL="https://github.com/google/fonts/raw/main/ofl/atkinsonhyperlegiblemono/AtkinsonHyperlegibleMono%5Bwght%5D.ttf"
MONO_ITALIC_URL="https://github.com/google/fonts/raw/main/ofl/atkinsonhyperlegiblemono/AtkinsonHyperlegibleMono-Italic%5Bwght%5D.ttf"
FONT_DIR="$HOME/.local/share/fonts"
CURL=(curl -fsSL --connect-timeout 15 --max-time 180 --retry 2)

# No usar "fc-list | grep -q": con pipefail, el SIGPIPE de fc-list da un falso negativo.
has_font() { [[ -n "$(fc-list "$1" family)" ]]; }

log "Fuentes"
if has_font "Atkinson Hyperlegible Mono"; then
    info "Atkinson Hyperlegible Mono ya está instalada"
else
    mkdir -p "$FONT_DIR"
    "${CURL[@]}" "$MONO_URL" -o "$FONT_DIR/AtkinsonHyperlegibleMono[wght].ttf"
    "${CURL[@]}" "$MONO_ITALIC_URL" -o "$FONT_DIR/AtkinsonHyperlegibleMono-Italic[wght].ttf"
    fc-cache -f "$FONT_DIR"
    info "Atkinson Hyperlegible Mono instalada en $FONT_DIR"
fi

has_font "Atkinson Hyperlegible Next" \
    || warn "falta Atkinson Hyperlegible Next (paquete fonts-atkinson-hyperlegible-next)"

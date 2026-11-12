#!/usr/bin/env bash
# Cambia entre los temas de themes/.
#   ./theme.sh           lista los temas y marca el activo
#   ./theme.sh anniq     aplica el tema anniq
#   ./theme.sh default   vuelve al tema por defecto
#
# Un tema es una carpeta themes/<nombre>/ con:
#   interface.ini   claves dconf (acento, esquema de color, tema GTK e iconos)   obligatorio
#   gtk-4.0.css     CSS para apps GTK4/libadwaita (~/.config/gtk-4.0/gtk.css)    opcional
#   *.palette       paletas de Ptyxis que se instalan                            opcional
#   ptyxis-palette  nombre de la paleta del perfil por defecto de Ptyxis         opcional
#   vscode/         extensión de tema para VS Code y Kiro; se instala en los que   opcional
#                   estén presentes y se activa. Sin esta carpeta se restaura el tema
#                   que cada editor tenía antes.
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

THEMES_DIR="$MIGNOME_ROOT/themes"
STATE_FILE="${XDG_STATE_HOME:-$HOME/.local/state}/mignome/theme"
GTK4_CSS="${XDG_CONFIG_HOME:-$HOME/.config}/gtk-4.0/gtk.css"
PTYXIS_PALETTES="${XDG_DATA_HOME:-$HOME/.local/share}/org.gnome.Ptyxis/palettes"
MARKER="/* mignome-theme:"

current_theme() { cat "$STATE_FILE" 2>/dev/null || echo default; }

list_themes() {
    local active
    active="$(current_theme)"
    for dir in "$THEMES_DIR"/*/; do
        name="$(basename "$dir")"
        if [[ "$name" == "$active" ]]; then echo "* $name"; else echo "  $name"; fi
    done
}

is_ours() { [[ -f "$1" && "$(head -1 "$1")" == "$MARKER"* ]]; }

apply_gtk4_css() {
    local theme="$1" src="$THEMES_DIR/$1/gtk-4.0.css"
    if [[ -f "$GTK4_CSS" ]] && ! is_ours "$GTK4_CSS"; then
        local backup
        backup="$GTK4_CSS.bak-$(date +%Y%m%d-%H%M%S)"
        mv "$GTK4_CSS" "$backup"
        warn "había un gtk.css propio; se movió a $backup"
    fi
    if [[ -f "$src" ]]; then
        mkdir -p "$(dirname "$GTK4_CSS")"
        { echo "$MARKER $theme — generado por mignome/theme.sh, no editar aquí */"; cat "$src"; } > "$GTK4_CSS"
        info "CSS de GTK4 instalado en $GTK4_CSS"
    elif [[ -f "$GTK4_CSS" ]]; then
        rm "$GTK4_CSS"
        info "CSS de GTK4 eliminado"
    fi
}

apply_ptyxis() {
    local dir="$THEMES_DIR/$1" palette uuid
    for file in "$dir"/*.palette; do
        [[ -e "$file" ]] || continue
        mkdir -p "$PTYXIS_PALETTES"
        cp "$file" "$PTYXIS_PALETTES/"
        info "paleta $(basename "$file" .palette) instalada en Ptyxis"
    done
    [[ -f "$dir/ptyxis-palette" ]] || return 0
    palette="$(tr -d '[:space:]' < "$dir/ptyxis-palette")"
    uuid="$(gsettings get org.gnome.Ptyxis default-profile-uuid 2>/dev/null | tr -d "'")"
    if [[ -z "$uuid" ]]; then
        warn "Ptyxis no tiene perfil por defecto; no se aplica la paleta $palette"
        return 0
    fi
    gsettings set "org.gnome.Ptyxis.Profile:/org/gnome/Ptyxis/Profiles/$uuid/" palette "'$palette'"
    info "Ptyxis usa la paleta $palette"
}

apply_editors() {
    local dir="$THEMES_DIR/$1" editors
    editors="$(python3 "$MIGNOME_ROOT/tools/vscode.py" editors)"
    if [[ -z "$editors" ]]; then
        info "ni VS Code ni Kiro están instalados; se omiten"
        return 0
    fi
    for editor in $editors; do
        if [[ -f "$dir/vscode/package.json" ]]; then
            python3 "$MIGNOME_ROOT/tools/vscode.py" apply "$editor" "$dir/vscode" | sed 's/^/    /'
        else
            python3 "$MIGNOME_ROOT/tools/vscode.py" restore-theme "$editor" | sed 's/^/    /'
        fi
    done
}

apply_theme() {
    local theme="$1" dir="$THEMES_DIR/$1"
    [[ -f "$dir/interface.ini" ]] || die "tema desconocido: $theme (disponibles: $(ls "$THEMES_DIR" | tr '\n' ' '))"
    log "Aplicando tema $theme"
    sed "s|@HOME@|$HOME|g" "$dir/interface.ini" | dconf load /
    info "acento, esquema de color, tema GTK e iconos aplicados"
    apply_gtk4_css "$theme"
    apply_ptyxis "$theme"
    apply_editors "$theme"
    mkdir -p "$(dirname "$STATE_FILE")"
    echo "$theme" > "$STATE_FILE"
    info "reinicia las apps GTK4 abiertas para ver el CSS nuevo (VS Code y Kiro cambian solos)"
}

if [[ $# -eq 0 ]]; then
    list_themes
else
    apply_theme "$1"
fi

# shellcheck shell=bash
# Funciones compartidas por install.sh y steps/*.sh.

MIGNOME_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Versión mayor de GNOME con la que se capturó esta configuración.
MIGNOME_TESTED_GNOME=50

log()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
info() { printf '    %s\n' "$*"; }
warn() { printf '\033[1;33m[aviso]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

gnome_major() {
    gnome-shell --version | grep -oE '[0-9]+' | head -1
}

# Lee un archivo de lista ignorando comentarios y líneas vacías.
read_list() {
    sed -e 's/#.*//' -e '/^[[:space:]]*$/d' "$1"
}

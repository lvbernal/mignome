#!/usr/bin/env bash
# Replica la configuración de GNOME en este equipo.
#   ./install.sh                  ejecuta todos los pasos
#   ./install.sh dconf fonts      ejecuta solo los pasos indicados
# Pasos: packages fonts sounds extensions dconf
set -euo pipefail
source "$(dirname "$0")/lib/common.sh"

[[ $EUID -ne 0 ]] || die "ejecútalo como tu usuario (sin sudo); pide la contraseña cuando hace falta"
[[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]] || die "ejecútalo dentro de una sesión gráfica de GNOME"
command -v gnome-shell >/dev/null || die "GNOME Shell no está instalado"

major="$(gnome_major)"
if [[ "$major" != "$MIGNOME_TESTED_GNOME" ]]; then
    warn "esta configuración se capturó en GNOME $MIGNOME_TESTED_GNOME y aquí hay GNOME $major"
    read -rp "¿Continuar? [s/N] " answer
    [[ "$answer" =~ ^[sSyY]$ ]] || exit 1
fi

all_steps=(packages fonts sounds extensions dconf)
steps=("$@")
[[ ${#steps[@]} -gt 0 ]] || steps=("${all_steps[@]}")

for step in "${steps[@]}"; do
    script="$(ls "$MIGNOME_ROOT"/steps/[0-9][0-9]-"$step".sh 2>/dev/null || true)"
    [[ -n "$script" ]] || die "paso desconocido: $step (disponibles: ${all_steps[*]})"
    bash "$script"
done

log "Listo. Cierra sesión y vuelve a entrar para cargar las extensiones nuevas."

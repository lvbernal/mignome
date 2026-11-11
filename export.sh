#!/usr/bin/env bash
# Vuelca la configuración actual de este equipo a dconf/*.ini (ver reglas en tools/mignome.py).
set -euo pipefail
exec python3 "$(dirname "$0")/tools/mignome.py" export

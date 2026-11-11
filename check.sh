#!/usr/bin/env bash
# Verifica que las claves de dconf/*.ini existan en la versión de GNOME instalada.
set -euo pipefail
exec python3 "$(dirname "$0")/tools/mignome.py" check

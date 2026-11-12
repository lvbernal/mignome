#!/usr/bin/env bash
# Aplica el tema activo (default si no se ha elegido otro). Ver theme.sh y themes/.
set -euo pipefail
source "$(dirname "$0")/../lib/common.sh"

state="${XDG_STATE_HOME:-$HOME/.local/state}/mignome/theme"
bash "$MIGNOME_ROOT/theme.sh" "$(cat "$state" 2>/dev/null || echo default)"

#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DISPLAY:-}" ]]; then
  exec xinit /opt/piboard-kiosk/scripts/kiosk-session.sh -- :0 -nocursor
fi

exec /opt/piboard-kiosk/scripts/kiosk-session.sh

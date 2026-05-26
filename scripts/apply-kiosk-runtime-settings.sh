#!/usr/bin/env bash
set -euo pipefail

SETTINGS_JSON="$(python3 -m piboard_kiosk.cli settings-json)"

SCREEN_SLEEP_ENABLED="$(python3 - <<'PY' "$SETTINGS_JSON"
import json, sys
print("true" if json.loads(sys.argv[1])["screen_sleep_enabled"] else "false")
PY
)"
CURSOR_VISIBLE="$(python3 - <<'PY' "$SETTINGS_JSON"
import json, sys
print("true" if json.loads(sys.argv[1])["cursor_visible"] else "false")
PY
)"
DISPLAY_ROTATION="$(python3 -m piboard_kiosk.cli rotation)"

/opt/piboard-kiosk/scripts/apply-display-rotation.sh "$DISPLAY_ROTATION" || true

if command -v xset >/dev/null 2>&1; then
  if [[ "$SCREEN_SLEEP_ENABLED" == "true" ]]; then
    xset s on +dpms || true
  else
    xset s off -dpms || true
    xset s noblank || true
  fi
fi

if command -v unclutter >/dev/null 2>&1; then
  pkill -x unclutter || true
  if [[ "$CURSOR_VISIBLE" != "true" ]]; then
    unclutter -idle 0.1 -root &
  fi
fi

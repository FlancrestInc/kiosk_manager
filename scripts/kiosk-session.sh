#!/usr/bin/env bash
set -euo pipefail

export DISPLAY="${DISPLAY:-:0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/runtime-piboard}"
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

openbox-session >/tmp/piboard-openbox.log 2>&1 &

while true; do
  /opt/piboard-kiosk/scripts/apply-kiosk-runtime-settings.sh || true

  mapfile -t CHROMIUM_ARGS < <(python3 -m piboard_kiosk.cli chromium-args)
  CYCLE_SECONDS="$(python3 -m piboard_kiosk.cli cycle-seconds)"

  echo "Launching Chromium: ${CHROMIUM_ARGS[*]}"
  if [[ "$CYCLE_SECONDS" =~ ^[0-9]+$ && "$CYCLE_SECONDS" -gt 0 ]]; then
    timeout --foreground "$CYCLE_SECONDS" "${CHROMIUM_ARGS[@]}" || true
  else
    "${CHROMIUM_ARGS[@]}" || true
  fi

  echo "Chromium exited; restarting shortly."
  sleep 2
done

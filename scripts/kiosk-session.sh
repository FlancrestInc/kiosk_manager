#!/usr/bin/env bash
set -euo pipefail

export DISPLAY="${DISPLAY:-:0}"
export HOME="/var/lib/piboard-kiosk-browser"
export XDG_CONFIG_HOME="/var/lib/piboard-kiosk-browser/.config"
export XDG_CACHE_HOME="/tmp/piboard-cache"
export XDG_RUNTIME_DIR="/tmp/runtime-piboard"
export PIBOARD_CHROMIUM_USER_DATA_DIR="/var/lib/piboard-kiosk-browser/chromium-profile"
export PIBOARD_CHROMIUM_CACHE_DIR="/tmp/chromium-cache"

mkdir -p \
  "$HOME" \
  "$XDG_CONFIG_HOME" \
  "$XDG_CACHE_HOME" \
  "$XDG_RUNTIME_DIR" \
  "$PIBOARD_CHROMIUM_USER_DATA_DIR" \
  "$PIBOARD_CHROMIUM_CACHE_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
chmod 700 "$PIBOARD_CHROMIUM_USER_DATA_DIR" "$PIBOARD_CHROMIUM_CACHE_DIR"

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

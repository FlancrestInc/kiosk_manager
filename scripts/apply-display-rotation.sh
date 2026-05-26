#!/usr/bin/env bash
set -euo pipefail

ROTATION="${1:-normal}"
CONFIG_FILE="${PIBOARD_DISPLAY_CONFIG_FILE:-/boot/firmware/config.txt}"
LEGACY_CONFIG_FILE="${PIBOARD_LEGACY_DISPLAY_CONFIG_FILE:-/boot/config.txt}"
MARKER_BEGIN="# piboard-kiosk display rotation begin"
MARKER_END="# piboard-kiosk display rotation end"

if [[ ! -f "$CONFIG_FILE" && -f "$LEGACY_CONFIG_FILE" ]]; then
  CONFIG_FILE="$LEGACY_CONFIG_FILE"
fi

if [[ "$ROTATION" != "normal" && "$ROTATION" != "90" && "$ROTATION" != "180" && "$ROTATION" != "270" ]]; then
  echo "Unsupported rotation '$ROTATION'. Use normal, 90, 180, or 270." >&2
  exit 2
fi

rotation_to_xrandr() {
  case "$ROTATION" in
    normal) echo "normal" ;;
    90) echo "right" ;;
    180) echo "inverted" ;;
    270) echo "left" ;;
  esac
}

connected_xrandr_output() {
  awk '
    $2 == "connected" {
      if ($3 == "primary") {
        primary = $1
      }
      if (first == "") {
        first = $1
      }
    }
    END {
      if (primary != "") {
        print primary
      } else if (first != "") {
        print first
      }
    }
  '
}

apply_live_rotation() {
  if [[ -z "${DISPLAY:-}" ]] || ! command -v xrandr >/dev/null 2>&1; then
    return 1
  fi

  local query output
  if ! query="$(xrandr --query 2>/dev/null)"; then
    return 1
  fi

  output="$(printf '%s\n' "$query" | connected_xrandr_output)"
  if [[ -z "$output" ]]; then
    return 1
  fi

  if ! xrandr --output "$output" --rotate "$(rotation_to_xrandr)"; then
    return 1
  fi
  echo "Live display rotation set to $ROTATION on $output."
}

apply_boot_rotation() {
  if [[ ! -f "$CONFIG_FILE" ]]; then
    return 1
  fi

  local tmp_file
  tmp_file="$(mktemp)"
  trap 'rm -f "$tmp_file" "$tmp_file.next"' RETURN
  awk -v begin="$MARKER_BEGIN" -v end="$MARKER_END" '
    $0 == begin { skip = 1; next }
    $0 == end { skip = 0; next }
    skip != 1 { print }
  ' "$CONFIG_FILE" > "$tmp_file"

  {
    cat "$tmp_file"
    echo "$MARKER_BEGIN"
    echo "# Managed by PiBoard Kiosk. Used as a boot-time fallback."
    case "$ROTATION" in
      normal) echo "# display_lcd_rotate=0" ;;
      90) echo "display_lcd_rotate=1" ;;
      180) echo "display_lcd_rotate=2" ;;
      270) echo "display_lcd_rotate=3" ;;
    esac
    echo "$MARKER_END"
  } > "$tmp_file.next"

  install -m 0644 "$tmp_file.next" "$CONFIG_FILE"
  echo "Boot display rotation set to $ROTATION in $CONFIG_FILE."
}

LIVE_APPLIED=false
BOOT_APPLIED=false

if apply_live_rotation; then
  LIVE_APPLIED=true
fi

if apply_boot_rotation; then
  BOOT_APPLIED=true
fi

if [[ "$LIVE_APPLIED" == false && "$BOOT_APPLIED" == false ]]; then
  echo "Cannot apply display rotation. No active X display was available, and no Raspberry Pi boot config file was found at /boot/firmware/config.txt or /boot/config.txt." >&2
  exit 1
fi

if [[ "$LIVE_APPLIED" == false && "$BOOT_APPLIED" == true ]]; then
  echo "No active X display was available; reboot may be required for the boot fallback to take effect."
fi

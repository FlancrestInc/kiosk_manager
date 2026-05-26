#!/usr/bin/env bash
set -euo pipefail

ROTATION="${1:-normal}"
CONFIG_FILE="/boot/firmware/config.txt"
LEGACY_CONFIG_FILE="/boot/config.txt"
MARKER_BEGIN="# piboard-kiosk display rotation begin"
MARKER_END="# piboard-kiosk display rotation end"

if [[ ! -f "$CONFIG_FILE" && -f "$LEGACY_CONFIG_FILE" ]]; then
  CONFIG_FILE="$LEGACY_CONFIG_FILE"
fi

if [[ "$ROTATION" != "normal" && "$ROTATION" != "90" && "$ROTATION" != "180" && "$ROTATION" != "270" ]]; then
  echo "Unsupported rotation '$ROTATION'. Use normal, 90, 180, or 270." >&2
  exit 2
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Cannot find Raspberry Pi boot config file. Expected /boot/firmware/config.txt or /boot/config.txt." >&2
  exit 1
fi

TMP_FILE="$(mktemp)"
awk -v begin="$MARKER_BEGIN" -v end="$MARKER_END" '
  $0 == begin { skip = 1; next }
  $0 == end { skip = 0; next }
  skip != 1 { print }
' "$CONFIG_FILE" > "$TMP_FILE"

{
  cat "$TMP_FILE"
  echo "$MARKER_BEGIN"
  echo "# Managed by PiBoard Kiosk. Changes here generally require a reboot."
  case "$ROTATION" in
    normal) echo "# display_lcd_rotate=0" ;;
    90) echo "display_lcd_rotate=1" ;;
    180) echo "display_lcd_rotate=2" ;;
    270) echo "display_lcd_rotate=3" ;;
  esac
  echo "$MARKER_END"
} > "$TMP_FILE.next"

install -m 0644 "$TMP_FILE.next" "$CONFIG_FILE"
rm -f "$TMP_FILE" "$TMP_FILE.next"

echo "Display rotation set to $ROTATION in $CONFIG_FILE. Reboot is required for this adapter to take effect."

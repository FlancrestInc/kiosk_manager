#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this uninstaller as root: sudo ./uninstall.sh" >&2
  exit 1
fi

systemctl disable --now piboard-kiosk.service piboard-admin.service 2>/dev/null || true
rm -f /etc/systemd/system/piboard-kiosk.service /etc/systemd/system/piboard-admin.service
systemctl daemon-reload

rm -rf /opt/piboard-kiosk

echo "Removed PiBoard Kiosk services and application files."
echo "Config and state are preserved at /etc/piboard-kiosk and /var/lib/piboard-kiosk."
echo "Remove them manually if you no longer need them."

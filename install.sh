#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this installer as root: sudo ./install.sh" >&2
  exit 1
fi

APP_DIR="/opt/piboard-kiosk"
CONFIG_DIR="/etc/piboard-kiosk"
STATE_DIR="/var/lib/piboard-kiosk"
LOG_DIR="/var/log/piboard-kiosk"
KIOSK_USER="piboard"

echo "Installing OS packages..."
apt-get update
apt-get install -y \
  python3 \
  python3-venv \
  python3-pip \
  xserver-xorg \
  xinit \
  openbox \
  chromium-browser \
  unclutter \
  x11-xserver-utils \
  rsync

if ! id "$KIOSK_USER" >/dev/null 2>&1; then
  useradd --system --create-home --home-dir /var/lib/piboard-kiosk --shell /usr/sbin/nologin "$KIOSK_USER"
fi
usermod -aG video,audio,input,tty,render "$KIOSK_USER" 2>/dev/null || true

mkdir -p "$APP_DIR" "$CONFIG_DIR" "$STATE_DIR" "$LOG_DIR"
rsync -a --delete \
  --exclude ".git" \
  --exclude "venv" \
  --exclude ".venv" \
  --exclude "__pycache__" \
  ./ "$APP_DIR/"

python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install "$APP_DIR"

if [[ ! -f "$CONFIG_DIR/config.json" ]]; then
  "$APP_DIR/venv/bin/python" - <<'PY'
from piboard_kiosk.config import load_config
load_config()
PY
fi

chmod +x "$APP_DIR"/scripts/*.sh
chown -R "$KIOSK_USER:$KIOSK_USER" "$STATE_DIR" "$LOG_DIR"
chown root:root "$CONFIG_DIR/config.json"
chmod 0644 "$CONFIG_DIR/config.json"

install -m 0644 "$APP_DIR/systemd/piboard-admin.service" /etc/systemd/system/piboard-admin.service
install -m 0644 "$APP_DIR/systemd/piboard-kiosk.service" /etc/systemd/system/piboard-kiosk.service

systemctl daemon-reload
systemctl enable piboard-admin.service piboard-kiosk.service
systemctl restart piboard-admin.service

echo
echo "Install complete."
echo "Edit /etc/piboard-kiosk/config.json or visit http://<pi-hostname>:8080."
echo "Reboot the Raspberry Pi to start the kiosk display: sudo reboot"

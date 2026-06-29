#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/piboard-kiosk}"
CONFIG_DIR="${CONFIG_DIR:-/etc/piboard-kiosk}"
STATE_DIR="${STATE_DIR:-/var/lib/piboard-kiosk}"
LOG_DIR="${LOG_DIR:-/var/log/piboard-kiosk}"
KIOSK_USER="${KIOSK_USER:-piboard}"
SPLASH_IMAGE="splash.png"
PLYMOUTH_THEME_NAME="piboard-kiosk"
CHROMIUM_PROFILE_DIR="${CHROMIUM_PROFILE_DIR:-$STATE_DIR/chromium-profile}"
CHROMIUM_CACHE_DIR="${CHROMIUM_CACHE_DIR:-/tmp/chromium-cache}"

select_chromium_package() {
  local package candidate
  for package in chromium-browser chromium; do
    candidate="$(apt-cache policy "$package" | awk '/Candidate:/ {print $2; exit}')"
    if [[ -n "$candidate" && "$candidate" != "(none)" ]]; then
      echo "$package"
      return 0
    fi
  done

  echo "Unable to find an installable Chromium package." >&2
  return 1
}

configure_xwrapper() {
  local config="${XWRAPPER_CONFIG:-/etc/X11/Xwrapper.config}"
  mkdir -p "$(dirname "$config")"
  install -m 0644 /dev/stdin "$config" <<'EOF'
allowed_users=anybody
needs_root_rights=yes
EOF
}

write_default_splash_image() {
  local splash_path="${1:-$STATE_DIR/$SPLASH_IMAGE}"
  mkdir -p "$(dirname "$splash_path")"
  base64 -d > "$splash_path" <<'EOF'
iVBORw0KGgoAAAANSUhEUgAAAoAAAAHgCAIAAAC6s0uzAAACFElEQVR4nO3VMQEAIAzAsIF/z0NGHjQKema2AuBn7wMAf8MEgAAQAAJAAAgAASAABIAAEAACAABAACxh7wMARwIAAEAACAAw1QAIAAEgAASAABAAAkAACAABAACAAABAAmAA+QEAIAA+v6kF8uD95mVBhAAAkAACAABIAAExP0EAAACAABAAAgAASAABIAAEAACAAABAACAAJgAEEACAABIAAEgAC4kQEBIAA+v6kF8uD95mVBhAAAkAACAABIAAExP0EAAACAABAAAgAASAABIAAEAACAAABAACAAJgAEEACAABIAAEgAC4kQEBIAA+v6kF8uD95mVBhAAAkAACAABIAAExP0EAAACAABAAAgAASAABIAAEAACAAABAACAAJgAEEACAABIAAEgAC4kQEBIAA+v6kF8uD95mVBhAAAkAACAABIAAExP0EAAACAABAAAgAASAABIAAEAACAAABAACAAJgAEEACAABIAAEgAC4kQEBIAA+v6kF8uD95mVBhAAAkAACAABIAAExP0EAAACAABAAAgAASAABIAAEAACAAABAACAAJgAEEACAABIAAEgAC4kQEBIAA+v6kF8uD95mVBhAAAkAACAABIAAExP0EAAACAABAAAgAASAABIAAEAACAAABAACAAJgAEEACAABIAAEgAC4kQEBIAA+v6kF8uD95mVBhAAAkAACAABIAAExP0EAAACAABAAAgAASAABIAAEAACAAABAACAAJgAEEACAABIAAEgAC4kQEBIAA+v6kF8uD95mVBhAAAkAACAABIAAExP0EAAACAABAAAgAASAABIAAEAACAAABAACAAJgAEEACAABIAAEgAC4kQEBIAAEgADwBfh9BYD+grHUAAAAAElFTkSuQmCC
EOF
  chmod 0644 "$splash_path"
}

detect_boot_cmdline() {
  if [[ -n "${BOOT_CMDLINE:-}" ]]; then
    echo "$BOOT_CMDLINE"
    return 0
  fi
  if [[ -f /boot/firmware/cmdline.txt ]]; then
    echo /boot/firmware/cmdline.txt
    return 0
  fi
  if [[ -f /boot/cmdline.txt ]]; then
    echo /boot/cmdline.txt
    return 0
  fi
  return 1
}

add_cmdline_token_once() {
  local token="$1"
  shift
  local existing
  for existing in "$@"; do
    if [[ "$existing" == "$token" ]]; then
      printf '%s\n' "$@"
      return 0
    fi
  done
  printf '%s\n' "$@" "$token"
}

configure_quiet_boot_cmdline() {
  local cmdline
  cmdline="$(detect_boot_cmdline)" || return 0
  [[ -f "$cmdline" ]] || return 0

  mapfile -t tokens < <(tr ' ' '\n' < "$cmdline" | sed '/^$/d')
  mapfile -t tokens < <(add_cmdline_token_once splash "${tokens[@]}")
  mapfile -t tokens < <(add_cmdline_token_once quiet "${tokens[@]}")
  mapfile -t tokens < <(add_cmdline_token_once plymouth.ignore-serial-consoles "${tokens[@]}")
  printf '%s\n' "${tokens[*]}" > "$cmdline"
}

run_boot_command_if_safe() {
  local command_name="$1"
  shift
  local command_path
  command_path="$(command -v "$command_name" 2>/dev/null)" || return 0
  if [[ "$(id -u)" -eq 0 || "$command_path" != /usr/bin/* && "$command_path" != /usr/sbin/* ]]; then
    "$command_path" "$@"
  fi
}

remove_browser_state_from_plymouth_theme() {
  local theme_dir="$1"

  # Plymouth theme assets are copied into initramfs. Browser profile/cache data
  # here can make initramfs huge and fill /boot/firmware on Raspberry Pi images.
  rm -rf "$theme_dir/.cache" "$theme_dir/.config"
}

configure_boot_splash() {
  local state_dir="${STATE_DIR:-/var/lib/piboard-kiosk}"
  local theme_root="${PLYMOUTH_THEME_ROOT:-/usr/share/plymouth/themes}"
  local theme_dir="$theme_root/$PLYMOUTH_THEME_NAME"
  local splash_path="$state_dir/$SPLASH_IMAGE"

  write_default_splash_image "$splash_path"
  mkdir -p "$theme_dir"
  remove_browser_state_from_plymouth_theme "$theme_dir"
  install -m 0644 /dev/stdin "$theme_dir/$PLYMOUTH_THEME_NAME.plymouth" <<EOF
[Plymouth Theme]
Name=PiBoard Kiosk
Description=PiBoard Kiosk boot splash
ModuleName=script

[script]
ImageDir=$state_dir
ScriptFile=$theme_dir/$PLYMOUTH_THEME_NAME.script
EOF
  install -m 0644 /dev/stdin "$theme_dir/$PLYMOUTH_THEME_NAME.script" <<'EOF'
image = Image("splash.png");
sprite = Sprite(image);
sprite.SetX(Window.GetX() + Window.GetWidth() / 2 - image.GetWidth() / 2);
sprite.SetY(Window.GetY() + Window.GetHeight() / 2 - image.GetHeight() / 2);
EOF

  run_boot_command_if_safe plymouth-set-default-theme "$PLYMOUTH_THEME_NAME"
  run_boot_command_if_safe update-initramfs -u
  configure_quiet_boot_cmdline
}

os_packages() {
  local chromium_package="$1"
  printf '%s\n' \
    python3 \
    python3-venv \
    python3-pip \
    xserver-xorg \
    xinit \
    openbox \
    "$chromium_package" \
    unclutter \
    x11-xserver-utils \
    xdotool \
    fonts-noto-color-emoji \
    plymouth \
    imagemagick \
    rsync
}

main() {
  if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run this installer as root: sudo ./install.sh" >&2
    exit 1
  fi

  echo "Installing OS packages..."
  apt-get update
  local chromium_package
  chromium_package="$(select_chromium_package)"
  mapfile -t packages < <(os_packages "$chromium_package")
  apt-get install -y "${packages[@]}"

  configure_xwrapper

  if ! id "$KIOSK_USER" >/dev/null 2>&1; then
    useradd --system --create-home --home-dir /var/lib/piboard-kiosk --shell /usr/sbin/nologin "$KIOSK_USER"
  fi
  usermod -aG video,audio,input,tty,render "$KIOSK_USER" 2>/dev/null || true

  mkdir -p \
    "$APP_DIR" \
    "$CONFIG_DIR" \
    "$STATE_DIR" \
    "$LOG_DIR" \
    "$CHROMIUM_PROFILE_DIR" \
    "$CHROMIUM_CACHE_DIR"
  configure_boot_splash

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
  chown -R "$KIOSK_USER:$KIOSK_USER" "$STATE_DIR" "$LOG_DIR" "$CHROMIUM_CACHE_DIR"
  chmod 700 "$CHROMIUM_PROFILE_DIR" "$CHROMIUM_CACHE_DIR"
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
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi

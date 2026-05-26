from __future__ import annotations

import platform
import socket
import subprocess
from pathlib import Path

from .config import CONFIG_PATH, KioskConfig, load_config
from .kiosk import ROTATION_STATE_PATH, choose_current_url


KIOSK_SERVICE = "piboard-kiosk.service"
ADMIN_SERVICE = "piboard-admin.service"
ROTATION_ADAPTER = Path("/opt/piboard-kiosk/scripts/apply-display-rotation.sh")


def device_info() -> dict[str, str]:
    return {
        "hostname": socket.gethostname(),
        "ip_address": _primary_ip_address(),
        "platform": platform.platform(),
    }


def kiosk_status(config_path: Path = CONFIG_PATH) -> dict[str, object]:
    config = load_config(config_path)
    return {
        "service": _systemctl_value("is-active", KIOSK_SERVICE),
        "current_url": choose_current_url(config, ROTATION_STATE_PATH),
        "config": config.to_dict(),
        **device_info(),
    }


def recent_logs(lines: int = 80) -> str:
    commands = [
        ["journalctl", "-u", KIOSK_SERVICE, "-n", str(lines), "--no-pager"],
        ["journalctl", "-u", ADMIN_SERVICE, "-n", str(max(20, lines // 3)), "--no-pager"],
    ]
    output = []
    for command in commands:
        try:
            output.append(
                subprocess.run(
                    command,
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                ).stdout.strip()
            )
        except FileNotFoundError:
            output.append("journalctl is not available on this system.")
    return "\n\n".join(part for part in output if part)


def restart_kiosk() -> None:
    subprocess.run(["systemctl", "restart", KIOSK_SERVICE], check=True)


def reboot_device() -> None:
    subprocess.run(["systemctl", "reboot"], check=True)


def apply_display_rotation(config: KioskConfig) -> str:
    if not ROTATION_ADAPTER.exists():
        return f"Rotation adapter is missing: {ROTATION_ADAPTER}"
    result = subprocess.run(
        [str(ROTATION_ADAPTER), config.display_rotation],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return result.stdout.strip()


def _primary_ip_address() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "unknown"
    finally:
        sock.close()


def _systemctl_value(action: str, service: str) -> str:
    try:
        result = subprocess.run(
            ["systemctl", action, service],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        return result.stdout.strip() or "unknown"
    except FileNotFoundError:
        return "unavailable"

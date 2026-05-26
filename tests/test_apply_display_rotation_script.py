from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROTATION_SH = ROOT / "scripts" / "apply-display-rotation.sh"


def test_apply_display_rotation_uses_xrandr_for_live_rotation(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls_path = tmp_path / "xrandr-calls.txt"
    xrandr = bin_dir / "xrandr"
    xrandr.write_text(
        f"""#!/usr/bin/env bash
printf '%s\\n' "$*" >> "{calls_path}"
if [[ "$1" == "--query" ]]; then
  cat <<'EOF'
Screen 0: minimum 320 x 200, current 1920 x 1080, maximum 16384 x 16384
HDMI-1 connected primary 1920x1080+0+0 normal
EOF
fi
""",
        encoding="utf-8",
    )
    xrandr.chmod(0o755)
    boot_config = tmp_path / "config.txt"
    boot_config.write_text("# existing config\n", encoding="utf-8")

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["DISPLAY"] = ":99"
    env["PIBOARD_DISPLAY_CONFIG_FILE"] = str(boot_config)

    result = subprocess.run(
        ["bash", str(ROTATION_SH), "90"],
        check=True,
        env=env,
        text=True,
        capture_output=True,
    )

    calls = calls_path.read_text(encoding="utf-8").splitlines()
    assert "--query" in calls
    assert "--output HDMI-1 --rotate right" in calls
    assert "Live display rotation set to 90" in result.stdout


def test_apply_display_rotation_keeps_boot_config_fallback(tmp_path: Path) -> None:
    boot_config = tmp_path / "config.txt"
    boot_config.write_text("# existing config\n", encoding="utf-8")

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    env.pop("DISPLAY", None)
    env["PIBOARD_DISPLAY_CONFIG_FILE"] = str(boot_config)

    result = subprocess.run(
        ["bash", str(ROTATION_SH), "180"],
        check=True,
        env=env,
        text=True,
        capture_output=True,
    )

    assert "display_lcd_rotate=2" in boot_config.read_text(encoding="utf-8")
    assert "Boot display rotation set to 180" in result.stdout

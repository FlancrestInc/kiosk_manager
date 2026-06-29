from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALL_SH = ROOT / "install.sh"


def test_select_chromium_package_falls_back_to_chromium_on_trixie(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    apt_cache = bin_dir / "apt-cache"
    apt_cache.write_text(
        """#!/usr/bin/env bash
if [[ "$1" != "policy" ]]; then
  exit 1
fi
case "$2" in
  chromium-browser)
    printf 'chromium-browser:\\n  Candidate: (none)\\n'
    ;;
  chromium)
    printf 'chromium:\\n  Candidate: 140.0.7339.80-1~deb13u1\\n'
    ;;
  *)
    exit 1
    ;;
esac
""",
        encoding="utf-8",
    )
    apt_cache.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = subprocess.run(
        [
            "bash",
            "-c",
            f"source {INSTALL_SH}; select_chromium_package",
        ],
        check=True,
        env=env,
        text=True,
        capture_output=True,
    )

    assert result.stdout.strip() == "chromium"


def test_select_chromium_package_prefers_chromium_browser_when_available(
    tmp_path: Path,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    apt_cache = bin_dir / "apt-cache"
    apt_cache.write_text(
        """#!/usr/bin/env bash
printf '%s:\\n  Candidate: 123-rpt1\\n' "$2"
""",
        encoding="utf-8",
    )
    apt_cache.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = subprocess.run(
        [
            "bash",
            "-c",
            f"source {INSTALL_SH}; select_chromium_package",
        ],
        check=True,
        env=env,
        text=True,
        capture_output=True,
    )

    assert result.stdout.strip() == "chromium-browser"


def test_configure_xwrapper_allows_service_user_to_start_x(tmp_path: Path) -> None:
    xwrapper_config = tmp_path / "Xwrapper.config"
    env = os.environ.copy()
    env["XWRAPPER_CONFIG"] = str(xwrapper_config)

    subprocess.run(
        [
            "bash",
            "-c",
            f"source {INSTALL_SH}; configure_xwrapper",
        ],
        check=True,
        env=env,
        text=True,
        capture_output=True,
    )

    assert xwrapper_config.read_text(encoding="utf-8") == (
        "allowed_users=anybody\n"
        "needs_root_rights=yes\n"
    )


def test_os_packages_include_color_emoji_font() -> None:
    result = subprocess.run(
        [
            "bash",
            "-c",
            f"source {INSTALL_SH}; os_packages chromium",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "fonts-noto-color-emoji" in result.stdout.splitlines()


def test_os_packages_include_boot_splash_dependencies() -> None:
    result = subprocess.run(
        [
            "bash",
            "-c",
            f"source {INSTALL_SH}; os_packages chromium",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    packages = result.stdout.splitlines()
    assert "plymouth" in packages
    assert "imagemagick" in packages


def test_os_packages_include_reload_control_dependency() -> None:
    result = subprocess.run(
        [
            "bash",
            "-c",
            f"source {INSTALL_SH}; os_packages chromium",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "xdotool" in result.stdout.splitlines()


def test_configure_boot_splash_installs_theme_and_placeholder(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    theme_dir = tmp_path / "themes"
    cmdline = tmp_path / "cmdline.txt"
    cmdline.write_text("console=tty1 rootwait\n", encoding="utf-8")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls.log"
    for command in ["plymouth-set-default-theme", "update-initramfs"]:
        executable = bin_dir / command
        executable.write_text(
            f"#!/usr/bin/env bash\nprintf '{command} %s\\n' \"$*\" >> {calls}\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["STATE_DIR"] = str(state_dir)
    env["PLYMOUTH_THEME_ROOT"] = str(theme_dir)
    env["BOOT_CMDLINE"] = str(cmdline)

    subprocess.run(
        [
            "bash",
            "-c",
            f"source {INSTALL_SH}; configure_boot_splash",
        ],
        check=True,
        env=env,
        text=True,
        capture_output=True,
    )

    assert (state_dir / "splash.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert (theme_dir / "piboard-kiosk" / "piboard-kiosk.plymouth").exists()
    assert (theme_dir / "piboard-kiosk" / "piboard-kiosk.script").exists()
    assert "splash quiet plymouth.ignore-serial-consoles" in cmdline.read_text(
        encoding="utf-8"
    )
    assert calls.read_text(encoding="utf-8").splitlines() == [
        "plymouth-set-default-theme piboard-kiosk",
        "update-initramfs -u",
    ]


def test_configure_boot_splash_removes_browser_state_from_theme(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    theme_dir = tmp_path / "themes"
    bad_cache = theme_dir / "piboard-kiosk" / ".cache" / "chromium" / "blob"
    bad_config = theme_dir / "piboard-kiosk" / ".config" / "chromium" / "Profile"
    bad_cache.parent.mkdir(parents=True)
    bad_config.parent.mkdir(parents=True)
    bad_cache.write_text("cache", encoding="utf-8")
    bad_config.write_text("config", encoding="utf-8")

    env = os.environ.copy()
    env["STATE_DIR"] = str(state_dir)
    env["PLYMOUTH_THEME_ROOT"] = str(theme_dir)

    subprocess.run(
        [
            "bash",
            "-c",
            f"source {INSTALL_SH}; configure_boot_splash",
        ],
        check=True,
        env=env,
        text=True,
        capture_output=True,
    )

    assert not (theme_dir / "piboard-kiosk" / ".cache").exists()
    assert not (theme_dir / "piboard-kiosk" / ".config").exists()
    assert (theme_dir / "piboard-kiosk" / "piboard-kiosk.plymouth").exists()
    assert (theme_dir / "piboard-kiosk" / "piboard-kiosk.script").exists()


def test_configure_boot_splash_preserves_existing_cmdline_tokens(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    theme_dir = tmp_path / "themes"
    cmdline = tmp_path / "cmdline.txt"
    cmdline.write_text(
        "console=tty1 splash rootwait quiet custom=1\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["STATE_DIR"] = str(state_dir)
    env["PLYMOUTH_THEME_ROOT"] = str(theme_dir)
    env["BOOT_CMDLINE"] = str(cmdline)

    subprocess.run(
        [
            "bash",
            "-c",
            f"source {INSTALL_SH}; configure_boot_splash",
        ],
        check=True,
        env=env,
        text=True,
        capture_output=True,
    )

    tokens = cmdline.read_text(encoding="utf-8").split()
    assert tokens.count("splash") == 1
    assert tokens.count("quiet") == 1
    assert tokens.count("plymouth.ignore-serial-consoles") == 1
    assert "custom=1" in tokens

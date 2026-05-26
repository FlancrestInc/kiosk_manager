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

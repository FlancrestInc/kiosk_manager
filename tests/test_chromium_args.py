from piboard_kiosk.config import KioskConfig
from piboard_kiosk.kiosk import build_chromium_args, find_chromium_command, rotation_urls


def test_build_chromium_args_uses_configured_url_and_zoom() -> None:
    config = KioskConfig(
        primary_url="https://example.com/dashboard",
        browser_reload_interval_minutes=15,
        cursor_visible=False,
        zoom_level=1.2,
    )

    args = build_chromium_args(config, "https://example.com/live")

    assert "--kiosk" in args
    assert "--app=https://example.com/live" in args
    assert "--force-device-scale-factor=1.2" in args
    assert "--disable-session-crashed-bubble" in args
    assert "--remote-debugging-address=127.0.0.1" in args
    assert "--remote-debugging-port=9222" in args


def test_build_chromium_args_uses_safe_profile_and_cache_dirs() -> None:
    config = KioskConfig(primary_url="https://example.com/dashboard")

    args = build_chromium_args(config, "https://example.com/dashboard")

    assert "--user-data-dir=/var/lib/piboard-kiosk-browser/chromium-profile" in args
    assert "--disk-cache-dir=/tmp/chromium-cache" in args
    assert "--no-first-run" in args
    assert "--disable-restore-session-state" in args


def test_rotation_urls_deduplicates_and_keeps_primary_first() -> None:
    config = KioskConfig(
        primary_url="https://example.com/a",
        additional_urls=[
            "https://example.com/b",
            "https://example.com/a",
            " ",
            "https://example.com/c",
        ],
    )

    assert rotation_urls(config) == [
        "https://example.com/a",
        "https://example.com/b",
        "https://example.com/c",
    ]


def test_find_chromium_command_supports_trixie_binary_name(
    tmp_path, monkeypatch
) -> None:
    chromium = tmp_path / "chromium"
    chromium.write_text("#!/usr/bin/env sh\n", encoding="utf-8")
    chromium.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))

    assert find_chromium_command() == "chromium"

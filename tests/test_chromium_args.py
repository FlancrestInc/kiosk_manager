from piboard_kiosk.config import KioskConfig
from piboard_kiosk.kiosk import build_chromium_args, rotation_urls


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

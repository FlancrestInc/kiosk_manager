from pathlib import Path

from piboard_kiosk.config import DEFAULT_CONFIG, KioskConfig, load_config, save_config


def test_load_config_creates_defaults_when_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"

    config = load_config(config_path)

    assert config.primary_url == DEFAULT_CONFIG["primary_url"]
    assert config.additional_urls == []
    assert config_path.exists()


def test_save_config_persists_validated_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config = KioskConfig(
        primary_url="https://example.com/dashboard",
        additional_urls=["https://example.com/ops"],
        rotation_interval_seconds=45,
        browser_reload_interval_minutes=10,
        display_rotation="90",
        screen_sleep_enabled=False,
        cursor_visible=False,
        zoom_level=1.25,
    )

    save_config(config, config_path)
    reloaded = load_config(config_path)

    assert reloaded == config


def test_empty_primary_url_is_rejected() -> None:
    try:
        KioskConfig(primary_url=" ")
    except ValueError as exc:
        assert "primary_url" in str(exc)
    else:
        raise AssertionError("Expected primary_url validation to fail")

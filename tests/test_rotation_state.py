from pathlib import Path

from piboard_kiosk.config import KioskConfig
from piboard_kiosk.kiosk import choose_current_url


def test_choose_current_url_advances_after_interval(tmp_path: Path) -> None:
    state_path = tmp_path / "rotation-state.json"
    config = KioskConfig(
        primary_url="https://example.com/a",
        additional_urls=["https://example.com/b"],
        rotation_interval_seconds=30,
    )

    first = choose_current_url(config, state_path, now=100)
    second = choose_current_url(config, state_path, now=120)
    third = choose_current_url(config, state_path, now=131)

    assert first == "https://example.com/a"
    assert second == "https://example.com/a"
    assert third == "https://example.com/b"

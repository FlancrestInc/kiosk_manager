from __future__ import annotations

import json
import time
from pathlib import Path

from .config import KioskConfig, STATE_DIR


ROTATION_STATE_PATH = STATE_DIR / "rotation-state.json"


def rotation_urls(config: KioskConfig) -> list[str]:
    urls = [config.primary_url, *config.additional_urls]
    unique_urls: list[str] = []
    seen: set[str] = set()
    for url in urls:
        clean_url = url.strip()
        if clean_url and clean_url not in seen:
            unique_urls.append(clean_url)
            seen.add(clean_url)
    return unique_urls


def choose_current_url(
    config: KioskConfig,
    state_path: Path = ROTATION_STATE_PATH,
    now: float | None = None,
) -> str:
    urls = rotation_urls(config)
    if len(urls) == 1 or config.rotation_interval_seconds <= 0:
        _write_rotation_state(state_path, index=0, updated_at=now or time.time())
        return urls[0]

    now = now or time.time()
    state = _read_rotation_state(state_path)
    index = int(state.get("index", 0)) % len(urls)
    updated_at = float(state.get("updated_at", now))

    if now - updated_at >= config.rotation_interval_seconds:
        index = (index + 1) % len(urls)
        updated_at = now
        _write_rotation_state(state_path, index=index, updated_at=updated_at)
    elif not state:
        _write_rotation_state(state_path, index=index, updated_at=updated_at)

    return urls[index]


def build_chromium_args(config: KioskConfig, current_url: str) -> list[str]:
    args = [
        "chromium-browser",
        "--kiosk",
        "--no-first-run",
        "--disable-infobars",
        "--disable-session-crashed-bubble",
        "--disable-restore-session-state",
        "--autoplay-policy=no-user-gesture-required",
        "--check-for-update-interval=31536000",
        "--disable-pinch",
        f"--force-device-scale-factor={config.zoom_level:g}",
        f"--app={current_url}",
    ]
    return args


def _read_rotation_state(state_path: Path) -> dict[str, object]:
    try:
        with Path(state_path).open("r", encoding="utf-8") as state_file:
            return json.load(state_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _write_rotation_state(state_path: Path, index: int, updated_at: float) -> None:
    state_path = Path(state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("w", encoding="utf-8") as state_file:
        json.dump({"index": index, "updated_at": updated_at}, state_file)
        state_file.write("\n")

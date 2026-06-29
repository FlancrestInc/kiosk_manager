from __future__ import annotations

import json
import os
import base64
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


CONFIG_DIR = Path(os.environ.get("PIBOARD_CONFIG_DIR", "/etc/piboard-kiosk"))
CONFIG_PATH = CONFIG_DIR / "config.json"
if os.environ.get("PIBOARD_CONFIG"):
    CONFIG_PATH = Path(os.environ["PIBOARD_CONFIG"])
    CONFIG_DIR = CONFIG_PATH.parent
STATE_DIR = Path(os.environ.get("PIBOARD_STATE_DIR", "/var/lib/piboard-kiosk"))
LOG_DIR = Path(os.environ.get("PIBOARD_LOG_DIR", "/var/log/piboard-kiosk"))
PLYMOUTH_ASSET_DIR = Path(
    os.environ.get("PIBOARD_PLYMOUTH_ASSET_DIR", STATE_DIR / "plymouth-assets")
)
SPLASH_PATH = PLYMOUTH_ASSET_DIR / "splash.png"

DEFAULT_SPLASH_IMAGE_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAoAAAAHgCAIAAAC6s0uzAAACFElEQVR4nO3VMQEAIAzAsIF/z0NGHjQKema2AuBn7wMAf8MEgAAQAAJAAAgAASAABIAAEAACAABAACxh7wMARwIAAEAACAAw1QAIAAEgAASAABAAAkAACAABAACAAABAAmAA+QEAIAA+v6kF8uD95mVBhAAAkAACAABIAAExP0EAAACAABAAAgAASAABIAAEAACAAABAACAAJgAEEACAABIAAEgAC4kQEBIAA+v6kF8uD95mVBhAAAkAACAABIAAExP0EAAACAABAAAgAASAABIAAEAACAAABAACAAJgAEEACAABIAAEgAC4kQEBIAA+v6kF8uD95mVBhAAAkAACAABIAAExP0EAAACAABAAAgAASAABIAAEAACAAABAACAAJgAEEACAABIAAEgAC4kQEBIAA+v6kF8uD95mVBhAAAkAACAABIAAExP0EAAACAABAAAgAASAABIAAEAACAAABAACAAJgAEEACAABIAAEgAC4kQEBIAA+v6kF8uD95mVBhAAAkAACAABIAAExP0EAAACAABAAAgAASAABIAAEAACAAABAACAAJgAEEACAABIAAEgAC4kQEBIAA+v6kF8uD95mVBhAAAkAACAABIAAExP0EAAACAABAAAgAASAABIAAEAACAAABAACAAJgAEEACAABIAAEgAC4kQEBIAA+v6kF8uD95mVBhAAAkAACAABIAAExP0EAAACAABAAAgAASAABIAAEAACAAABAACAAJgAEEACAABIAAEgAC4kQEBIAA+v6kF8uD95mVBhAAAkAACAABIAAExP0EAAACAABAAAgAASAABIAAEAACAAABAACAAJgAEEACAABIAAEgAC4kQEBIAAEgADwBfh9BYD+grHUAAAAAElFTkSuQmCC"
)

VALID_ROTATIONS = {"normal", "90", "180", "270"}

DEFAULT_CONFIG: dict[str, Any] = {
    "primary_url": "https://example.com",
    "additional_urls": [],
    "rotation_interval_seconds": 300,
    "browser_reload_interval_minutes": 60,
    "display_rotation": "normal",
    "screen_sleep_enabled": False,
    "cursor_visible": False,
    "zoom_level": 1.0,
}


@dataclass(frozen=True)
class KioskConfig:
    primary_url: str = DEFAULT_CONFIG["primary_url"]
    additional_urls: list[str] = field(default_factory=list)
    rotation_interval_seconds: int = DEFAULT_CONFIG["rotation_interval_seconds"]
    browser_reload_interval_minutes: int = DEFAULT_CONFIG[
        "browser_reload_interval_minutes"
    ]
    display_rotation: str = DEFAULT_CONFIG["display_rotation"]
    screen_sleep_enabled: bool = DEFAULT_CONFIG["screen_sleep_enabled"]
    cursor_visible: bool = DEFAULT_CONFIG["cursor_visible"]
    zoom_level: float = DEFAULT_CONFIG["zoom_level"]

    def __post_init__(self) -> None:
        primary_url = self.primary_url.strip()
        additional_urls = [url.strip() for url in self.additional_urls if url.strip()]
        rotation_interval_seconds = max(0, int(self.rotation_interval_seconds))
        browser_reload_interval_minutes = max(0, int(self.browser_reload_interval_minutes))
        zoom_level = min(3.0, max(0.25, float(self.zoom_level)))
        display_rotation = str(self.display_rotation)

        if not primary_url:
            raise ValueError("primary_url is required")
        if display_rotation not in VALID_ROTATIONS:
            raise ValueError(f"display_rotation must be one of {sorted(VALID_ROTATIONS)}")

        object.__setattr__(self, "primary_url", primary_url)
        object.__setattr__(self, "additional_urls", additional_urls)
        object.__setattr__(self, "rotation_interval_seconds", rotation_interval_seconds)
        object.__setattr__(
            self, "browser_reload_interval_minutes", browser_reload_interval_minutes
        )
        object.__setattr__(self, "display_rotation", display_rotation)
        object.__setattr__(self, "screen_sleep_enabled", bool(self.screen_sleep_enabled))
        object.__setattr__(self, "cursor_visible", bool(self.cursor_visible))
        object.__setattr__(self, "zoom_level", zoom_level)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KioskConfig":
        merged = DEFAULT_CONFIG | data
        legacy_reload = merged.pop("reload_interval_minutes", None)
        if legacy_reload is not None:
            merged["browser_reload_interval_minutes"] = legacy_reload
        return cls(**{key: merged[key] for key in DEFAULT_CONFIG})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_config(config_path: Path = CONFIG_PATH) -> KioskConfig:
    config_path = Path(config_path)
    if not config_path.exists():
        config = KioskConfig()
        save_config(config, config_path)
        return config

    with config_path.open("r", encoding="utf-8") as config_file:
        data = json.load(config_file)
    return KioskConfig.from_dict(data)


def save_config(config: KioskConfig, config_path: Path = CONFIG_PATH) -> None:
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as config_file:
        json.dump(config.to_dict(), config_file, indent=2)
        config_file.write("\n")

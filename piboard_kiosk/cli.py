from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path

from .config import CONFIG_PATH, load_config
from .kiosk import ROTATION_STATE_PATH, build_chromium_args, choose_current_url, rotation_urls


def main() -> None:
    parser = argparse.ArgumentParser(description="PiBoard kiosk helper commands")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("current-url")
    subparsers.add_parser("chromium-args")
    subparsers.add_parser("chromium-command")
    subparsers.add_parser("settings-json")
    subparsers.add_parser("cycle-seconds")
    subparsers.add_parser("rotation")

    args = parser.parse_args()
    config = load_config(CONFIG_PATH)

    if args.command == "current-url":
        print(choose_current_url(config, ROTATION_STATE_PATH))
    elif args.command == "chromium-args":
        current_url = choose_current_url(config, ROTATION_STATE_PATH)
        print("\n".join(build_chromium_args(config, current_url)))
    elif args.command == "chromium-command":
        current_url = choose_current_url(config, ROTATION_STATE_PATH)
        print(shlex.join(build_chromium_args(config, current_url)))
    elif args.command == "settings-json":
        payload = config.to_dict()
        payload["urls"] = rotation_urls(config)
        print(json.dumps(payload))
    elif args.command == "cycle-seconds":
        print(cycle_seconds(config))
    elif args.command == "rotation":
        print(config.display_rotation)


def cycle_seconds(config) -> int:
    intervals = []
    if len(rotation_urls(config)) > 1 and config.rotation_interval_seconds > 0:
        intervals.append(config.rotation_interval_seconds)
    if config.browser_reload_interval_minutes > 0:
        intervals.append(config.browser_reload_interval_minutes * 60)
    return min(intervals) if intervals else 0


if __name__ == "__main__":
    main()

from __future__ import annotations

import subprocess
from pathlib import Path

from piboard_kiosk import system
from piboard_kiosk.config import KioskConfig


def test_apply_display_rotation_targets_kiosk_x_display(
    monkeypatch, tmp_path: Path
) -> None:
    adapter = tmp_path / "apply-display-rotation.sh"
    adapter.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    xauthority = tmp_path / ".Xauthority"
    xauthority.write_text("", encoding="utf-8")
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout="ok\n")

    monkeypatch.setattr(system, "ROTATION_ADAPTER", adapter)
    monkeypatch.setattr(system, "KIOSK_XAUTHORITY", xauthority)
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("XAUTHORITY", raising=False)
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = system.apply_display_rotation(KioskConfig(display_rotation="270"))

    assert result == "ok"
    assert calls[0][0] == [str(adapter), "270"]
    assert calls[0][1]["env"]["DISPLAY"] == ":0"
    assert calls[0][1]["env"]["XAUTHORITY"] == str(xauthority)


def test_open_kiosk_url_navigates_browser_to_url(monkeypatch, tmp_path: Path) -> None:
    xauthority = tmp_path / ".Xauthority"
    xauthority.write_text("", encoding="utf-8")
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(system, "KIOSK_XAUTHORITY", xauthority)
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("XAUTHORITY", raising=False)
    monkeypatch.setattr(subprocess, "run", fake_run)

    system.open_kiosk_url("https://example.com/new?panel=ops")

    assert [call[0] for call in calls] == [
        ["xdotool", "key", "ctrl+l"],
        ["xdotool", "type", "--clearmodifiers", "https://example.com/new?panel=ops"],
        ["xdotool", "key", "Return"],
    ]
    assert all(call[1]["check"] is True for call in calls)
    assert all(call[1]["env"]["DISPLAY"] == ":0" for call in calls)
    assert all(call[1]["env"]["XAUTHORITY"] == str(xauthority) for call in calls)

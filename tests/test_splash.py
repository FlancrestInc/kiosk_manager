from __future__ import annotations

import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from piboard_kiosk import app as admin_app
from piboard_kiosk.config import KioskConfig


PNG_BYTES = b"\x89PNG\r\n\x1a\nplaceholder"


def test_admin_page_renders_boot_splash_controls() -> None:
    html = admin_app.render_admin_page(
        KioskConfig(),
        {"hostname": "pi", "ip_address": "127.0.0.1"},
        "",
    )

    assert 'action="/splash/upload"' in html
    assert 'action="/splash/restore"' in html
    assert 'src="/splash.png"' in html
    assert "Boot splash" in html


def test_admin_page_renders_reload_control_instead_of_restart_control() -> None:
    html = admin_app.render_admin_page(
        KioskConfig(),
        {"hostname": "pi", "ip_address": "127.0.0.1"},
        "",
    )

    assert 'action="/reload"' in html
    assert "Refresh kiosk browser" in html
    assert 'action="/restart"' not in html
    assert "Restart kiosk browser" not in html


def test_splash_preview_returns_current_image(monkeypatch, tmp_path: Path) -> None:
    splash_path = tmp_path / "splash.png"
    splash_path.write_bytes(PNG_BYTES)
    monkeypatch.setattr(admin_app, "SPLASH_PATH", splash_path, raising=False)

    response = TestClient(admin_app.app).get("/splash.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == PNG_BYTES


def test_reload_endpoint_reloads_kiosk_browser(monkeypatch) -> None:
    calls = []

    def fake_reload() -> None:
        calls.append("reload")

    monkeypatch.setattr(admin_app, "reload_kiosk_browser", fake_reload)

    response = TestClient(admin_app.app).post("/reload", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert calls == ["reload"]


def test_upload_splash_converts_supported_image(monkeypatch, tmp_path: Path) -> None:
    splash_path = tmp_path / "splash.png"
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        splash_path.write_bytes(PNG_BYTES)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(admin_app, "SPLASH_PATH", splash_path, raising=False)
    monkeypatch.setattr(admin_app.subprocess, "run", fake_run)

    response = TestClient(admin_app.app).post(
        "/splash/upload",
        files={"splash_image": ("splash.jpg", b"fake-jpeg", "image/jpeg")},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert splash_path.read_bytes() == PNG_BYTES
    assert calls
    assert calls[0][0][-1] == f"png:{splash_path}"


def test_upload_splash_rejects_non_image(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(admin_app, "SPLASH_PATH", tmp_path / "splash.png", raising=False)

    response = TestClient(admin_app.app).post(
        "/splash/upload",
        files={"splash_image": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert not (tmp_path / "splash.png").exists()


def test_restore_splash_writes_default_placeholder(monkeypatch, tmp_path: Path) -> None:
    splash_path = tmp_path / "splash.png"
    monkeypatch.setattr(admin_app, "SPLASH_PATH", splash_path, raising=False)

    response = TestClient(admin_app.app).post("/splash/restore", follow_redirects=False)

    assert response.status_code == 303
    assert splash_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

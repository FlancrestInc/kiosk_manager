from __future__ import annotations

import html
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse

from .config import CONFIG_PATH, KioskConfig, load_config, save_config
from .system import (
    apply_display_rotation,
    kiosk_status,
    recent_logs,
    reboot_device,
    restart_kiosk,
)


app = FastAPI(title="PiBoard Kiosk Admin")


@app.get("/", response_class=HTMLResponse)
def admin_page() -> str:
    config = load_config(CONFIG_PATH)
    status = kiosk_status(CONFIG_PATH)
    logs = recent_logs()
    return render_admin_page(config, status, logs)


@app.post("/settings")
def update_settings(
    primary_url: str = Form(...),
    additional_urls: str = Form(""),
    rotation_interval_seconds: int = Form(300),
    browser_reload_interval_minutes: int = Form(60),
    display_rotation: str = Form("normal"),
    screen_sleep_enabled: bool = Form(False),
    cursor_visible: bool = Form(False),
    zoom_level: float = Form(1.0),
) -> RedirectResponse:
    urls = [line.strip() for line in additional_urls.splitlines() if line.strip()]
    try:
        config = KioskConfig(
            primary_url=primary_url,
            additional_urls=urls,
            rotation_interval_seconds=rotation_interval_seconds,
            browser_reload_interval_minutes=browser_reload_interval_minutes,
            display_rotation=display_rotation,
            screen_sleep_enabled=screen_sleep_enabled,
            cursor_visible=cursor_visible,
            zoom_level=zoom_level,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    save_config(config, CONFIG_PATH)
    apply_display_rotation(config)
    return RedirectResponse("/", status_code=303)


@app.post("/restart")
def restart() -> RedirectResponse:
    restart_kiosk()
    return RedirectResponse("/", status_code=303)


@app.post("/reboot")
def reboot() -> RedirectResponse:
    reboot_device()
    return RedirectResponse("/", status_code=303)


@app.get("/logs", response_class=PlainTextResponse)
def logs() -> str:
    return recent_logs()


def render_admin_page(
    config: KioskConfig, status: dict[str, object], logs: str
) -> str:
    additional_urls = "\n".join(config.additional_urls)
    rotation_options = "".join(
        option_tag(value, config.display_rotation)
        for value in ["normal", "90", "180", "270"]
    )
    checked_sleep = " checked" if config.screen_sleep_enabled else ""
    checked_cursor = " checked" if config.cursor_visible else ""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PiBoard Kiosk Admin</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f8fa;
      --panel: #ffffff;
      --ink: #17202a;
      --muted: #667085;
      --line: #d8dee8;
      --accent: #176b87;
      --danger: #b42318;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 16px;
      line-height: 1.45;
    }}
    header {{
      padding: 20px clamp(16px, 4vw, 44px);
      background: #101820;
      color: white;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
    }}
    h1, h2 {{ margin: 0; }}
    h1 {{ font-size: 22px; }}
    h2 {{ font-size: 17px; margin-bottom: 14px; }}
    main {{
      width: min(1180px, calc(100% - 32px));
      margin: 24px auto 44px;
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(280px, .65fr);
      gap: 18px;
    }}
    section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    label {{ display: block; font-weight: 650; margin: 14px 0 6px; }}
    input, textarea, select {{
      width: 100%;
      border: 1px solid #b9c2cf;
      border-radius: 6px;
      padding: 10px 11px;
      font: inherit;
      background: white;
      color: var(--ink);
    }}
    textarea {{ min-height: 120px; resize: vertical; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .check-row {{ display: flex; align-items: center; gap: 10px; margin-top: 14px; }}
    .check-row input {{ width: auto; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }}
    button {{
      border: 0;
      border-radius: 6px;
      padding: 10px 14px;
      font-weight: 700;
      background: var(--accent);
      color: white;
      cursor: pointer;
    }}
    button.secondary {{ background: #344054; }}
    button.danger {{ background: var(--danger); }}
    dl {{ display: grid; grid-template-columns: 120px minmax(0, 1fr); gap: 8px 12px; margin: 0; }}
    dt {{ color: var(--muted); }}
    dd {{ margin: 0; overflow-wrap: anywhere; }}
    pre {{
      margin: 0;
      padding: 14px;
      max-height: 360px;
      overflow: auto;
      background: #101820;
      color: #edf7ff;
      border-radius: 8px;
      font-size: 13px;
    }}
    .logs {{ grid-column: 1 / -1; }}
    .note {{ color: var(--muted); font-size: 14px; margin: 8px 0 0; }}
    @media (max-width: 820px) {{
      header {{ align-items: flex-start; flex-direction: column; }}
      main {{ grid-template-columns: 1fr; }}
      .grid {{ grid-template-columns: 1fr; }}
      dl {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>PiBoard Kiosk Admin</h1>
    <div>{escape(status.get("hostname", "unknown"))} · {escape(status.get("ip_address", "unknown"))}</div>
  </header>
  <main>
    <section>
      <h2>Settings</h2>
      <form method="post" action="/settings">
        <label for="primary_url">Primary dashboard URL</label>
        <input id="primary_url" name="primary_url" type="url" required value="{escape(config.primary_url)}">

        <label for="additional_urls">Additional URLs</label>
        <textarea id="additional_urls" name="additional_urls" spellcheck="false">{escape(additional_urls)}</textarea>
        <p class="note">One URL per line. Leave blank to show only the primary page.</p>

        <div class="grid">
          <div>
            <label for="rotation_interval_seconds">Page rotation interval, seconds</label>
            <input id="rotation_interval_seconds" name="rotation_interval_seconds" type="number" min="0" value="{config.rotation_interval_seconds}">
          </div>
          <div>
            <label for="browser_reload_interval_minutes">Browser reload interval, minutes</label>
            <input id="browser_reload_interval_minutes" name="browser_reload_interval_minutes" type="number" min="0" value="{config.browser_reload_interval_minutes}">
          </div>
          <div>
        <label for="display_rotation">Display rotation</label>
        <select id="display_rotation" name="display_rotation">{rotation_options}</select>
        <p class="note">Rotation is written through the adapter script and requires a reboot on Raspberry Pi OS.</p>
          </div>
          <div>
            <label for="zoom_level">Browser zoom level</label>
            <input id="zoom_level" name="zoom_level" type="number" min="0.25" max="3" step="0.05" value="{config.zoom_level:g}">
          </div>
        </div>

        <label class="check-row">
          <input type="checkbox" name="screen_sleep_enabled"{checked_sleep}>
          <span>Allow screen sleep</span>
        </label>
        <label class="check-row">
          <input type="checkbox" name="cursor_visible"{checked_cursor}>
          <span>Show cursor</span>
        </label>

        <div class="actions">
          <button type="submit">Save settings</button>
        </div>
      </form>
    </section>

    <section>
      <h2>Status</h2>
      <dl>
        <dt>Kiosk</dt><dd>{escape(status.get("service", "unknown"))}</dd>
        <dt>Current URL</dt><dd>{escape(status.get("current_url", ""))}</dd>
        <dt>Hostname</dt><dd>{escape(status.get("hostname", "unknown"))}</dd>
        <dt>IP address</dt><dd>{escape(status.get("ip_address", "unknown"))}</dd>
      </dl>
      <div class="actions">
        <form method="post" action="/restart"><button class="secondary" type="submit">Restart kiosk browser</button></form>
        <form method="post" action="/reboot"><button class="danger" type="submit">Reboot device</button></form>
      </div>
    </section>

    <section class="logs">
      <h2>Recent kiosk logs</h2>
      <pre>{escape(logs)}</pre>
    </section>
  </main>
</body>
</html>"""


def option_tag(value: str, selected_value: str) -> str:
    selected = " selected" if value == selected_value else ""
    return f'<option value="{escape(value)}"{selected}>{escape(value)}</option>'


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)

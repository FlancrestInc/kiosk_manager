# PiBoard Kiosk

PiBoard Kiosk turns Raspberry Pi OS Lite into a local-first web dashboard display. It is not a custom OS, a digital signage CMS, a layout builder, or a cloud fleet manager.

The Pi boots into Chromium in full-screen kiosk mode, displays one configured dashboard URL, and can optionally rotate through additional URLs. A self-hosted admin UI runs on the Pi at port `8080`.

## Target System

- Raspberry Pi OS Lite
- Network access on the local LAN
- A connected display
- User with `sudo` for installation

## Install

On a fresh Raspberry Pi OS Lite install:

```bash
sudo apt-get update
sudo apt-get install -y git
git clone <this-repo-url> piboard-kiosk
cd piboard-kiosk
sudo ./install.sh
sudo reboot
```

After reboot, Chromium should open the configured URL full-screen. From another computer on the same network, open:

```text
http://<pi-hostname>:8080
```

The default config uses `https://example.com`; change it from the admin UI or edit `/etc/piboard-kiosk/config.json`.

## Admin UI

The admin UI supports:

- primary dashboard URL
- additional dashboard URLs, one per line
- page rotation interval
- browser reload interval
- display rotation: `normal`, `90`, `180`, `270`
- screen sleep on/off
- cursor visibility
- browser zoom level
- boot splash image upload
- current kiosk status
- current URL
- IP address and hostname
- recent systemd logs
- restart kiosk browser
- reboot device

Changing settings saves `/etc/piboard-kiosk/config.json`. Click **Restart kiosk browser** after changing URLs, reload interval, cursor visibility, sleep, or zoom.

The boot splash upload stores a local PNG at `/var/lib/piboard-kiosk/splash.png`.
PNG, JPEG, WebP, and GIF uploads are accepted and normalized to PNG. The new image
appears during the next reboot.

## Config

Config is stored at:

```text
/etc/piboard-kiosk/config.json
```

Example:

```json
{
  "primary_url": "https://grafana.local/d/ops",
  "additional_urls": [
    "https://status.local",
    "https://calendar.local"
  ],
  "rotation_interval_seconds": 300,
  "browser_reload_interval_minutes": 60,
  "display_rotation": "normal",
  "screen_sleep_enabled": false,
  "cursor_visible": false,
  "zoom_level": 1.0
}
```

If more than one URL is configured and `rotation_interval_seconds` is greater than `0`, the kiosk restarts Chromium on that interval with the next URL. If `browser_reload_interval_minutes` is greater than `0`, Chromium is also restarted on that interval so dashboards refresh cleanly. If Chromium crashes, systemd and the session loop start it again.

## Services

The installer creates:

```text
/etc/systemd/system/piboard-admin.service
/etc/systemd/system/piboard-kiosk.service
```

Useful commands:

```bash
sudo systemctl status piboard-admin.service
sudo systemctl status piboard-kiosk.service
sudo systemctl restart piboard-kiosk.service
journalctl -u piboard-kiosk.service -n 100 --no-pager
```

The admin service runs the FastAPI app on `0.0.0.0:8080`. The kiosk service starts a minimal X/Openbox session and launches Chromium in kiosk mode.

The v1 admin UI does not include authentication. Run it only on a trusted local network or restrict port `8080` with your firewall.

## Display Rotation

Display rotation is hardware and Raspberry Pi OS version dependent, so v1 keeps it behind an adapter script:

```text
/opt/piboard-kiosk/scripts/apply-display-rotation.sh
```

The default adapter first tries live X11 rotation with `xrandr`, using the primary connected output when one is marked and otherwise the first connected output. The admin service targets the kiosk display at `:0`, so changing rotation from the web UI should take effect without rebooting when the X session is running.

The adapter also writes a managed block to the Raspberry Pi boot config as a boot-time fallback:

```text
/boot/firmware/config.txt
```

On older images it falls back to:

```text
/boot/config.txt
```

It writes `display_lcd_rotate` values:

- `normal`: comments out rotation
- `90`: `display_lcd_rotate=1`
- `180`: `display_lcd_rotate=2`
- `270`: `display_lcd_rotate=3`

The boot-config fallback may still require a reboot on systems where live X11 rotation is not available.

If your display stack needs a different command, replace only the adapter script and keep the JSON config field unchanged.

## Boot Splash

The installer configures a Plymouth theme named `piboard-kiosk` so the Raspberry Pi
shows a local splash image instead of the normal scrolling boot log. A generic
placeholder is installed first, and the admin UI can upload a replacement or restore
the placeholder.

The installer manages:

```text
/usr/share/plymouth/themes/piboard-kiosk
/var/lib/piboard-kiosk/splash.png
/boot/firmware/cmdline.txt
```

On older images it falls back to:

```text
/boot/cmdline.txt
```

It adds the `splash`, `quiet`, and `plymouth.ignore-serial-consoles` boot arguments
when a boot command line file is available. The uploaded splash is stored locally, so
it is available before networking starts. Changes made from the admin UI take effect
on the next reboot.

## Non-Interactive Display

Chromium is launched with kiosk-oriented flags and no browser chrome. Cursor visibility can be disabled from config, and screen sleep can be disabled. The displayed page is intended as a passive dashboard; this project does not provide touch navigation, page editing, or signage layout tools.

## Uninstall

From the repo directory:

```bash
sudo ./uninstall.sh
```

This removes services and `/opt/piboard-kiosk`, but preserves:

```text
/etc/piboard-kiosk
/var/lib/piboard-kiosk
```

Remove those manually if you no longer need the config or state.

## Development

Create a local virtual environment and run tests:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
```

For local helper commands before installing, point config and state at writable paths:

```bash
PIBOARD_CONFIG=/tmp/piboard-config.json PIBOARD_STATE_DIR=/tmp/piboard-state python -m piboard_kiosk.cli chromium-command
```

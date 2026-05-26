# Splash Screen Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a locally stored, web-configurable boot splash image that replaces Raspberry Pi boot log output after installation.

**Architecture:** The installer owns boot-time Plymouth setup and quiet boot configuration. The FastAPI admin app owns image upload, validation, preview, and restoring the default placeholder, writing the active splash image to the state directory used by the Plymouth theme.

**Tech Stack:** Bash installer, Plymouth, ImageMagick, FastAPI, pytest.

---

## Chunk 1: Installer Splash Setup

**Files:**
- Modify: `install.sh`
- Test: `tests/test_install_script.py`

- [ ] Add failing tests for splash package dependencies, default asset creation, Plymouth theme setup, and managed quiet boot cmdline updates.
- [ ] Implement `configure_boot_splash`, helper path detection, theme files, placeholder PNG installation, Plymouth default theme update, initramfs update when available, and quiet boot token management.
- [ ] Run `pytest tests/test_install_script.py -v`.

## Chunk 2: Admin Upload And Preview

**Files:**
- Modify: `piboard_kiosk/config.py`
- Modify: `piboard_kiosk/app.py`
- Create: `tests/test_splash.py`

- [ ] Add failing tests for upload validation, image conversion command, placeholder restore, splash preview endpoint, and admin page controls.
- [ ] Implement splash path constants, upload endpoint, restore endpoint, preview endpoint, image type validation, ImageMagick conversion, and UI section.
- [ ] Run `pytest tests/test_splash.py -v`.

## Chunk 3: Docs And Full Verification

**Files:**
- Modify: `README.md`

- [ ] Document boot splash behavior, supported upload types, next-reboot behavior, and installer-managed boot files.
- [ ] Run full `pytest`.

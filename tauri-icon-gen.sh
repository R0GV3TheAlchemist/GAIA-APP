#!/usr/bin/env bash
# Run this once locally or in CI BEFORE `npm run tauri build`
# Requires: @tauri-apps/cli installed (npm install)
#
# This regenerates ALL icon sizes from the single SVG source:
#   src-tauri/icons/gaia-icon.svg
#
# Output files (written to src-tauri/icons/):
#   32x32.png, 128x128.png, 128x128@2x.png
#   icon.png, icon.ico, icon.icns
#   Square30x30Logo.png ... Square310x310Logo.png
#   StoreLogo.png

set -e
echo "[tauri-icon-gen] Generating icons from src-tauri/icons/gaia-icon.svg..."
npx @tauri-apps/cli icon src-tauri/icons/gaia-icon.svg
echo "[tauri-icon-gen] Done. All icons written to src-tauri/icons/"

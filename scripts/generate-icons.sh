#!/bin/bash
# Generate all Tauri icon sizes from the GAIA SVG source
# Requires: npm install -g @tauri-apps/cli
#
# Usage: bash scripts/generate-icons.sh

echo "Generating GAIA icons from SVG source..."
npx tauri icon src-tauri/icons/gaia-icon.svg
echo "Done! All icon sizes written to src-tauri/icons/"

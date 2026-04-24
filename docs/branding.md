# GAIA Branding & Icon Guide

> **Phase 6.1** — Windows Identity & Branding  
> All icon assets are generated from the single source SVG: `src-tauri/icons/gaia-icon.svg`

---

## 1. Generate All Icon Sizes (One Command)

The Tauri CLI can generate every required PNG size, the multi-size `.ico`, and the `.icns` from your source SVG automatically.

### Prerequisites
- Rust + Cargo installed (`rustup`)
- Tauri CLI v2 installed: `cargo install tauri-cli --version '^2'`

### Run

```bash
# From the repo root:
cargo tauri icon src-tauri/icons/gaia-icon.svg
```

This single command outputs all of the following into `src-tauri/icons/`:

| File | Size | Used By |
|------|------|---------|
| `32x32.png` | 32×32 px | Windows taskbar, tray |
| `128x128.png` | 128×128 px | App icon (standard) |
| `128x128@2x.png` | 256×256 px | App icon (HiDPI) |
| `256x256.png` | 256×256 px | App icon (large) |
| `icon.ico` | Multi-size (16, 24, 32, 48, 64, 128, 256) | Windows installer, taskbar |
| `icon.icns` | macOS bundle | macOS (future) |
| `icon.png` | 512×512 px | General use |
| `Square*Logo.png` | Various | Windows Store / WiX |

> **Commit all generated files** to `src-tauri/icons/` after running this command.

---

## 2. Tray Icon Variants

The Tauri CLI does **not** generate 16×16 and 24×24 tray-specific variants. Create them manually:

### Using Inkscape (free, recommended)

```bash
# Install Inkscape, then:
inkscape src-tauri/icons/gaia-icon.svg --export-png=src-tauri/icons/tray-16x16.png --export-width=16 --export-height=16
inkscape src-tauri/icons/gaia-icon.svg --export-png=src-tauri/icons/tray-24x24.png --export-width=24 --export-height=24
inkscape src-tauri/icons/gaia-icon.svg --export-png=src-tauri/icons/tray-32x32.png --export-width=32 --export-height=32
```

### Using ImageMagick (alternative)

```bash
# First convert SVG to a high-res PNG, then resize:
magick src-tauri/icons/icon.png -resize 16x16 src-tauri/icons/tray-16x16.png
magick src-tauri/icons/icon.png -resize 24x24 src-tauri/icons/tray-24x24.png
magick src-tauri/icons/icon.png -resize 32x32 src-tauri/icons/tray-32x32.png
```

> Update `tauri.conf.json` → `app.trayIcon.iconPath` to `"icons/tray-32x32.png"` once generated.

---

## 3. Installer Images

Two installers (WiX `.msi` and NSIS `.exe`) each need branding images.  
Create them and place in `src-tauri/icons/installer/`.

### WiX Installer (.msi)

| File | Dimensions | Format | Description |
|------|-----------|--------|-------------|
| `wix-dialog.bmp` | 493 × 312 px | BMP (24-bit) | Large left-side image on the welcome/finish dialog |
| `wix-banner.bmp` | 493 × 58 px | BMP (24-bit) | Narrow banner at the top of every installer page |

**Design brief:**
- Background: GAIA dark (`#171614`) or deep teal gradient
- Logo: `gaia-icon.svg` centered/left-aligned
- `wix-dialog.bmp`: can include tagline “Sovereign AI Companion”
- `wix-banner.bmp`: logo + “GAIA” wordmark on dark background
- Export as **BMP 24-bit** (not PNG — WiX requires BMP)

### NSIS Installer (.exe)

| File | Dimensions | Format | Description |
|------|-----------|--------|-------------|
| `nsis-header.bmp` | 150 × 57 px | BMP (24-bit) | Top banner on each installer page |
| `nsis-sidebar.bmp` | 164 × 314 px | BMP (24-bit) | Left sidebar on welcome/finish pages |

**Design brief:** Same GAIA dark aesthetic. Keep clean — logo + name only.

### Converting to BMP with ImageMagick

```bash
# After creating PNG designs, convert to BMP:
magick wix-dialog.png -type TrueColor BMP3:src-tauri/icons/installer/wix-dialog.bmp
magick wix-banner.png -type TrueColor BMP3:src-tauri/icons/installer/wix-banner.bmp
magick nsis-header.png -type TrueColor BMP3:src-tauri/icons/installer/nsis-header.bmp
magick nsis-sidebar.png -type TrueColor BMP3:src-tauri/icons/installer/nsis-sidebar.bmp
```

---

## 4. Add/Remove Programs Entry

Already configured in `tauri.conf.json`:
- **Publisher:** R0GV3 the Alchemist
- **Support URL:** https://github.com/R0GV3TheAlchemist/GAIA-OS/issues
- **App icon:** `icons/icon.ico` (multi-size, generated in Step 1)
- **Description:** GAIA — Sovereign AI Companion

No further action needed for this item once the icon is regenerated.

---

## 5. Checklist

- [ ] Run `cargo tauri icon src-tauri/icons/gaia-icon.svg` and commit output
- [ ] Generate tray variants: `tray-16x16.png`, `tray-24x24.png`, `tray-32x32.png`
- [ ] Create and commit `src-tauri/icons/installer/wix-dialog.bmp` (493×312)
- [ ] Create and commit `src-tauri/icons/installer/wix-banner.bmp` (493×58)
- [ ] Create and commit `src-tauri/icons/installer/nsis-header.bmp` (150×57)
- [ ] Create and commit `src-tauri/icons/installer/nsis-sidebar.bmp` (164×314)
- [ ] Update `tauri.conf.json` trayIcon path to `icons/tray-32x32.png`
- [ ] Verify `icon.ico` is multi-size after regeneration (right-click → Properties → should show multiple sizes)

---

## 6. Quick Verification

After running `cargo tauri icon`:

```bash
# Check 256x256 was generated:
ls src-tauri/icons/256x256.png

# Check icon.ico is multi-size (should be > 100KB):
ls -lh src-tauri/icons/icon.ico

# Windows only — check ICO contains multiple sizes:
python -c "from PIL import Image; img = Image.open('src-tauri/icons/icon.ico'); print(img.info)"
```

---

*Last updated: Phase 6.1 — April 2026*

# GAIA Code Signing Guide

> **Phase 6.2** — Code Signing  
> Documents the self-signed certificate process used for GAIA Windows builds.

---

## Overview

GAIA Windows installers (`.msi` and `.exe`) are signed using a Tauri-generated self-signed keypair. The private key is stored as a GitHub Actions secret and injected at build time — no developer machine ever holds the signing key after initial setup.

---

## Current Setup (Self-Signed)

### Secrets in GitHub Actions

Two repository secrets are configured under **Settings → Secrets and variables → Actions**:

| Secret | Purpose |
|--------|--------|
| `TAURI_SIGNING_PRIVATE_KEY` | Base64-encoded minisign private key |
| `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | Password protecting the private key |

These are referenced in `.github/workflows/release.yml` and `.github/workflows/build-windows.yml` via:
```yaml
env:
  TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}
  TAURI_SIGNING_PRIVATE_KEY_PASSWORD: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY_PASSWORD }}
```

### How the Keypair Was Generated

```bash
# Install Tauri CLI if not already installed
cargo install tauri-cli --version '^2'

# Generate the signing keypair
cargo tauri signer generate -w ~/.tauri/gaia-signing.key
```

This outputs:
- A **private key** (added to `TAURI_SIGNING_PRIVATE_KEY` secret)
- A **public key** (added to `tauri.conf.json` → `plugins.updater.pubkey`)
- A **password** (added to `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` secret)

### Public Key Location

The public key is embedded in `src-tauri/tauri.conf.json`:
```json
"plugins": {
  "updater": {
    "pubkey": "<base64-encoded-public-key>"
  }
}
```
This allows the auto-updater to verify installer signatures before applying updates.

---

## Verifying a Signed Build

After a release build completes:

```bash
# Windows only — verify the .msi signature
signtool verify /pa /v GAIA_Setup.msi

# Or check via PowerShell:
Get-AuthenticodeSignature .\GAIA_Setup.msi
```

For self-signed builds, Windows will show a SmartScreen warning on first run from unknown publishers. This is expected until a commercial certificate is obtained (see below).

---

## Upgrading to a Commercial Certificate (Future)

When GAIA is ready for public distribution without SmartScreen warnings:

1. **Purchase** an Extended Validation (EV) code signing certificate from:
   - [DigiCert](https://www.digicert.com/code-signing/) (~$500/yr) — fastest SmartScreen reputation
   - [Sectigo](https://sectigo.com/ssl-certificates-tls/code-signing) (~$200/yr) — good alternative
   - [SSL.com](https://www.ssl.com/certificates/ev-code-signing/) (~$200/yr)

2. **Export** the certificate as a `.pfx` file with password

3. **Add new secrets** to GitHub Actions:
   - `WINDOWS_CERTIFICATE` — base64-encoded `.pfx` contents
   - `WINDOWS_CERTIFICATE_PASSWORD` — `.pfx` password

4. **Update** `release.yml` to use the commercial cert:
```yaml
- name: Sign installer
  run: |
    echo ${{ secrets.WINDOWS_CERTIFICATE }} | base64 --decode > certificate.pfx
    signtool sign /f certificate.pfx /p ${{ secrets.WINDOWS_CERTIFICATE_PASSWORD }} \
      /tr http://timestamp.digicert.com /td sha256 /fd sha256 \
      src-tauri/target/release/bundle/msi/*.msi
```

> **EV certificates** (Extended Validation) immediately grant SmartScreen reputation.  
> **OV certificates** (Organization Validation) require download volume to build reputation over time.

---

## SmartScreen Behaviour by Certificate Type

| Certificate | SmartScreen on First Run | Reputation Build Time |
|-------------|-------------------------|----------------------|
| No signature | ❌ Hard block | N/A |
| Self-signed | ⚠️ Warning (can bypass) | N/A |
| OV Commercial | ⚠️ Warning until reputation built | Weeks–months |
| EV Commercial | ✅ No warning immediately | Immediate |

---

## Key Security Notes

- **Never commit the private key** to the repository
- **Never share** `TAURI_SIGNING_PRIVATE_KEY` outside GitHub Secrets
- The public key in `tauri.conf.json` is safe to commit — it is public by design
- If the private key is ever compromised, generate a new keypair and rotate the secrets immediately

---

*Last updated: Phase 6.2 — April 2026*

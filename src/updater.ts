// GAIA Auto-Updater
// Checks for updates on startup (after sidecar:ready), shows a non-blocking
// banner, and handles download + install with progress feedback.
// Canon Ref: C43 — Sovereign Distribution

import { check, Update, DownloadEvent } from '@tauri-apps/plugin-updater';
import { relaunch }                      from '@tauri-apps/plugin-process';
import { logInfo, logWarn, logError }    from './diagnostics';
import './updater.css';

let _banner: HTMLElement | null = null;

// ── Public API ──────────────────────────────────────────────────────

/**
 * Call once after sidecar:ready.
 * Silently checks for an update; if one is found, injects the update banner.
 * Never throws — all errors are caught and logged.
 */
export async function checkForUpdates(): Promise<void> {
  logInfo('updater', 'Checking for updates');
  try {
    const update = await check();
    if (update?.available) {
      logInfo('updater', 'Update available', { version: update.version });
      showUpdateBanner(update);
    } else {
      logInfo('updater', 'No update available — app is current');
    }
  } catch (e) {
    logWarn('updater', 'Update check skipped', e instanceof Error ? e.message : String(e));
  }
}

// ── Banner UI ───────────────────────────────────────────────────────────

function showUpdateBanner(update: Update): void {
  if (_banner) return;

  const version = update.version ?? 'unknown';
  const notes   = update.body   ?? '';

  _banner = document.createElement('div');
  _banner.id        = 'gaia-update-banner';
  _banner.innerHTML = `
    <div class="update-banner-inner">
      <span class="update-icon">&#9650;</span>
      <div class="update-text">
        <strong>GAIA ${version} is available</strong>
        ${notes ? `<span class="update-notes">${escapeHtml(notes)}</span>` : ''}
      </div>
      <div class="update-actions">
        <button id="gaia-update-install" class="update-btn primary">Update &amp; Restart</button>
        <button id="gaia-update-dismiss" class="update-btn ghost">Later</button>
      </div>
    </div>
    <div id="gaia-update-progress" class="update-progress" hidden>
      <div class="update-progress-bar">
        <div id="gaia-update-progress-fill" class="update-progress-fill" style="width:0%"></div>
      </div>
      <span id="gaia-update-progress-label" class="update-progress-label">Downloading…</span>
    </div>
  `;

  document.body.appendChild(_banner);

  document.getElementById('gaia-update-install')!.addEventListener('click', () => {
    logInfo('updater', 'User initiated update install', { version });
    installUpdate(update);
  });

  document.getElementById('gaia-update-dismiss')!.addEventListener('click', () => {
    logInfo('updater', 'User dismissed update banner', { version });
    dismissBanner();
  });
}

function dismissBanner(): void {
  if (_banner) {
    _banner.classList.add('update-banner-dismissed');
    setTimeout(() => { _banner?.remove(); _banner = null; }, 400);
  }
}

// ── Install flow ───────────────────────────────────────────────────────────

async function installUpdate(update: Update): Promise<void> {
  const actionsEl  = _banner?.querySelector<HTMLElement>('.update-actions');
  const progressEl = document.getElementById('gaia-update-progress');
  if (actionsEl)  actionsEl.hidden  = true;
  if (progressEl) progressEl.hidden = false;

  const fillEl  = document.getElementById('gaia-update-progress-fill')  as HTMLElement;
  const labelEl = document.getElementById('gaia-update-progress-label') as HTMLElement;

  let downloaded = 0;
  let total      = 0;

  try {
    await update.downloadAndInstall((event: DownloadEvent) => {
      switch (event.event) {
        case 'Started':
          total = event.data.contentLength ?? 0;
          labelEl.textContent = 'Downloading…';
          logInfo('updater', 'Download started', { totalBytes: total });
          break;
        case 'Progress':
          downloaded += event.data.chunkLength;
          if (total > 0) {
            const pct = Math.round((downloaded / total) * 100);
            fillEl.style.width  = `${pct}%`;
            labelEl.textContent = `Downloading… ${pct}%`;
          }
          break;
        case 'Finished':
          fillEl.style.width  = '100%';
          labelEl.textContent = 'Installing…';
          logInfo('updater', 'Download finished — installing');
          break;
      }
    });

    labelEl.textContent = 'Done — restarting GAIA…';
    logInfo('updater', 'Install complete — relaunching');
    await new Promise(r => setTimeout(r, 800));
    await relaunch();

  } catch (e) {
    logError('updater', 'Install failed', e);
    if (actionsEl)  actionsEl.hidden  = false;
    if (progressEl) progressEl.hidden = true;
    labelEl.textContent = 'Update failed — please try again.';
    setTimeout(() => { if (progressEl) progressEl.hidden = true; }, 3000);
  }
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g,  '&lt;')
    .replace(/>/g,  '&gt;')
    .replace(/"/g, '&quot;');
}

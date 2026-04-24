// GAIA Dev Suite — Status Bar

import { API_BASE } from '../config';   // ← was '../app' (circular dep fix)
import { checkForUpdates } from '../updater';

export function mountStatusBar(root: HTMLElement): void {
  root.innerHTML = `
    <div class="status-bar">
      <span id="sb-sidecar">&#11044; Sidecar: checking...</span>
      <span id="sb-branch">&#8887; main</span>
      <span id="sb-file"></span>
      <span class="sb-spacer"></span>
      <button id="sb-check-updates" class="sb-update-btn" title="Check for Updates">&#9650; Check for Updates</button>
      <span>GAIA Dev Suite</span>
    </div>
  `;

  pollSidecarStatus();
  setInterval(pollSidecarStatus, 5000);

  document.getElementById('sb-check-updates')?.addEventListener('click', async () => {
    const btn = document.getElementById('sb-check-updates') as HTMLButtonElement;
    if (btn) { btn.innerHTML = '&#9650; Checking\u2026'; btn.disabled = true; }
    await checkForUpdates();
    if (btn) { btn.innerHTML = '&#9650; Check for Updates'; btn.disabled = false; }
  });
}

async function pollSidecarStatus(): Promise<void> {
  const el = document.getElementById('sb-sidecar');
  if (!el) return;
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2000) });
    el.textContent = res.ok ? '\u2B24 Sidecar: online' : '\u2B24 Sidecar: degraded';
    el.style.color = res.ok ? '#4f98a3' : '#fdab43';
  } catch {
    el.textContent = '\u2B24 Sidecar: offline';
    el.style.color = '#dd6974';
  }
}

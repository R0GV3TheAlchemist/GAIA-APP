// GAIA Dev Suite — Status Bar

import { API_BASE } from '../app';

export function mountStatusBar(root: HTMLElement): void {
  root.innerHTML = `
    <div class="status-bar">
      <span id="sb-sidecar">⬤ Sidecar: checking...</span>
      <span id="sb-branch">⎇ main</span>
      <span id="sb-file"></span>
      <span class="sb-spacer"></span>
      <span>GAIA Dev Suite</span>
    </div>
  `;

  pollSidecarStatus();
  setInterval(pollSidecarStatus, 5000);
}

async function pollSidecarStatus(): Promise<void> {
  const el = document.getElementById('sb-sidecar');
  if (!el) return;
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2000) });
    el.textContent = res.ok ? '⬤ Sidecar: online' : '⬤ Sidecar: degraded';
    el.style.color = res.ok ? '#00b4a6' : '#f0a500';
  } catch {
    el.textContent = '⬤ Sidecar: offline';
    el.style.color = '#e05c5c';
  }
}

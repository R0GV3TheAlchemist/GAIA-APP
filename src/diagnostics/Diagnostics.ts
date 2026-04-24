// GAIA Diagnostics Panel
// Displays startup timing, sidecar health, version info, and a live log tail.
// Canon Ref: C43 — Sovereign Distribution

import './Diagnostics.css';
import { invoke }        from '@tauri-apps/api/core';
import { getVersion }    from '@tauri-apps/api/app';
import { listen }        from '@tauri-apps/api/event';
import { API_BASE }      from '../config';   // ← was '../app' (circular dep fix)
import { getLogBuffer, LogEntry } from './logger';

export function mountDiagnostics(root: HTMLElement): void {
  root.innerHTML = `
    <div class="diag-panel">
      <div class="diag-header">
        <span class="diag-title">&#9881; Diagnostics</span>
        <div class="diag-actions">
          <button id="diag-refresh" class="diag-btn">&#8635; Refresh</button>
          <button id="diag-open-logs" class="diag-btn">&#128193; Open Log Folder</button>
          <button id="diag-copy" class="diag-btn">&#128203; Copy Report</button>
        </div>
      </div>

      <div class="diag-grid">
        <div class="diag-card">
          <div class="diag-card-label">App Version</div>
          <div id="diag-version" class="diag-card-value">&#8230;</div>
        </div>
        <div class="diag-card">
          <div class="diag-card-label">Sidecar</div>
          <div id="diag-sidecar" class="diag-card-value">&#8230;</div>
        </div>
        <div class="diag-card">
          <div class="diag-card-label">Cold Start</div>
          <div id="diag-coldstart" class="diag-card-value">&#8230;</div>
        </div>
        <div class="diag-card">
          <div class="diag-card-label">Log Buffer</div>
          <div id="diag-bufsize" class="diag-card-value">&#8230;</div>
        </div>
      </div>

      <div class="diag-log-section">
        <div class="diag-log-toolbar">
          <span class="diag-log-title">Log Tail</span>
          <select id="diag-log-filter" class="diag-select">
            <option value="ALL">ALL</option>
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="ERROR">ERROR</option>
          </select>
          <button id="diag-log-clear" class="diag-btn">Clear</button>
        </div>
        <div id="diag-log-list" class="diag-log-list"></div>
      </div>
    </div>
  `;

  const t0 = performance.now();
  let coldStartMs: number | null = null;

  listen('sidecar:ready', () => {
    coldStartMs = performance.now() - t0;
    refreshStats(coldStartMs);
  });

  async function refreshStats(csMs?: number): Promise<void> {
    try {
      const v = await getVersion();
      const el = document.getElementById('diag-version');
      if (el) el.textContent = `v${v}`;
    } catch { /* ignore */ }

    try {
      const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2000) });
      const el = document.getElementById('diag-sidecar');
      if (el) {
        el.textContent = res.ok ? '\u25cf online' : '\u25cf degraded';
        el.style.color = res.ok ? '#4f98a3' : '#fdab43';
      }
    } catch {
      const el = document.getElementById('diag-sidecar');
      if (el) { el.textContent = '\u25cf offline'; el.style.color = '#dd6974'; }
    }

    const csEl = document.getElementById('diag-coldstart');
    if (csEl) {
      const ms = csMs ?? coldStartMs;
      csEl.textContent = ms !== null ? `${(ms / 1000).toFixed(2)} s` : 'measuring\u2026';
    }

    const buf   = getLogBuffer();
    const bufEl = document.getElementById('diag-bufsize');
    if (bufEl) bufEl.textContent = `${buf.length} entries`;

    renderLogTail();
  }

  function renderLogTail(): void {
    const filter  = (document.getElementById('diag-log-filter') as HTMLSelectElement)?.value ?? 'ALL';
    const listEl  = document.getElementById('diag-log-list');
    if (!listEl) return;

    const levels: Record<string, number> = { DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3 };
    const minLevel = levels[filter] ?? 0;

    const entries = getLogBuffer()
      .filter(e => (levels[e.level] ?? 0) >= minLevel)
      .slice(-100);

    listEl.innerHTML = entries.length === 0
      ? '<div class="diag-log-empty">No log entries.</div>'
      : entries.map(renderEntry).join('');

    listEl.scrollTop = listEl.scrollHeight;
  }

  function renderEntry(e: LogEntry): string {
    const levelClass = `diag-log-level-${e.level.toLowerCase()}`;
    const time = e.ts.slice(11, 23);
    const data = e.data !== undefined ? ` ${JSON.stringify(e.data)}` : '';
    return `
      <div class="diag-log-row">
        <span class="diag-log-time">${time}</span>
        <span class="diag-log-level ${levelClass}">${e.level}</span>
        <span class="diag-log-module">${escHtml(e.module)}</span>
        <span class="diag-log-msg">${escHtml(e.msg)}${escHtml(data)}</span>
      </div>`;
  }

  document.getElementById('diag-refresh')?.addEventListener('click', () => refreshStats());

  document.getElementById('diag-open-logs')?.addEventListener('click', async () => {
    try { await invoke('open_log_dir'); }
    catch (e) { console.warn('[GAIA:diag] open_log_dir failed:', e); }
  });

  document.getElementById('diag-copy')?.addEventListener('click', () => {
    const report = buildReport();
    navigator.clipboard.writeText(report).then(() => {
      const btn = document.getElementById('diag-copy');
      if (btn) {
        btn.textContent = '\u2713 Copied';
        setTimeout(() => { btn.textContent = '\u{1F4CB} Copy Report'; }, 2000);
      }
    });
  });

  document.getElementById('diag-log-filter')?.addEventListener('change', renderLogTail);
  document.getElementById('diag-log-clear')?.addEventListener('click', () => {
    const listEl = document.getElementById('diag-log-list');
    if (listEl) listEl.innerHTML = '<div class="diag-log-empty">Log cleared (in-view only).</div>';
  });

  refreshStats();
  setInterval(() => refreshStats(), 10_000);
}

function buildReport(): string {
  const lines: string[] = [
    `GAIA Diagnostics Report \u2014 ${new Date().toISOString()}`,
    '='.repeat(60),
    ...getLogBuffer().slice(-50).map(e =>
      `${e.ts} [${e.level}] ${e.module}: ${e.msg}${
        e.data !== undefined ? ' ' + JSON.stringify(e.data) : ''
      }`),
  ];
  return lines.join('\n');
}

function escHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

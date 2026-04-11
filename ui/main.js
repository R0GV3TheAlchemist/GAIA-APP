/**
 * GAIA-APP — UI Shell v1.1.0
 * Sprint G-5: Fixed /status shape, /memory/list shape, replaced Atlas dot
 * with GAIAN runtime dot.
 *
 * API target: http://localhost:8008 (dev) or window.GAIA_API_URL (production)
 */

(function () {
  'use strict';

  // --- API Configuration ---
  const GAIA_API = (typeof window !== 'undefined' && window.GAIA_API_URL)
    ? window.GAIA_API_URL
    : 'http://localhost:8008';

  async function api(path, options = {}) {
    try {
      const res = await fetch(GAIA_API + path, options);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn('[GAIA] API call failed:', path, e.message);
      return null;
    }
  }

  // --- Theme ---
  const root = document.documentElement;
  const themeToggle = document.querySelector('[data-theme-toggle]');
  let currentTheme = 'dark';

  function setTheme(theme) {
    currentTheme = theme;
    root.setAttribute('data-theme', theme);
    if (themeToggle) {
      themeToggle.innerHTML = theme === 'dark'
        ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
        : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
      themeToggle.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
    }
  }

  if (themeToggle) {
    themeToggle.addEventListener('click', () => setTheme(currentTheme === 'dark' ? 'light' : 'dark'));
  }

  // --- Navigation ---
  const navBtns = document.querySelectorAll('.nav-btn');
  const views = document.querySelectorAll('.view');

  function showView(viewId) {
    views.forEach(v => v.classList.add('hidden'));
    const target = document.getElementById('view-' + viewId);
    if (target) target.classList.remove('hidden');
    navBtns.forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-view') === viewId);
    });
    if (viewId === 'memory') loadMemory();
    if (viewId === 'consent') loadConsent();
    if (viewId === 'canon') loadCanon();
  }

  navBtns.forEach(btn => {
    btn.addEventListener('click', () => showView(btn.getAttribute('data-view')));
  });

  const btnCanon = document.getElementById('btn-canon');
  if (btnCanon) btnCanon.addEventListener('click', () => showView('canon'));

  // --- Status Bar ---
  function setDot(id, color, label) {
    const dot = document.getElementById('dot-' + id);
    const lbl = document.getElementById('label-' + id);
    if (dot) { dot.className = 'status-dot ' + color; }
    if (lbl) lbl.textContent = label;
  }

  async function refreshStatus() {
    const status = await api('/status');
    if (status) {
      setDot('core', 'green', 'Core: Active');

      // G-5 fix: server returns canon_docs (array) and canon_doc_count (int)
      const docCount = status.canon_doc_count || 0;
      const docsLoaded = status.canon_loaded;
      setDot('canon',
        docsLoaded ? 'green' : 'yellow',
        docsLoaded ? `Canon: Loaded (${docCount} docs)` : 'Canon: Loading'
      );

      // G-5 fix: replaced Atlas dot with GAIAN runtime dot
      const activeRuntimes = status.active_runtimes || 0;
      const gaianNames = (status.gaian_names || []).slice(0, 3).join(', ');
      setDot('gaians',
        activeRuntimes > 0 ? 'green' : 'yellow',
        activeRuntimes > 0
          ? `GAIANs: ${activeRuntimes} active${gaianNames ? ' — ' + gaianNames : ''}`
          : `GAIANs: ${status.gaians || 0} born`
      );
    } else {
      setDot('core', 'red', 'Core: Offline — run python core/server.py');
      setDot('canon', 'red', 'Canon: Unreachable');
      setDot('gaians', 'red', 'GAIANs: Unreachable');
    }
  }

  // --- Session Start ---
  const btnStart = document.getElementById('btn-start');
  if (btnStart) {
    btnStart.addEventListener('click', async () => {
      btnStart.textContent = 'Connecting...';
      btnStart.disabled = true;
      await refreshStatus();
      btnStart.textContent = 'Session Active';
      console.log('[GAIA] Session initialized — constitutional core online');
    });
  }

  // --- Memory View ---
  // G-5 fix: server returns {memories:[{query, timestamp, source_count}], count}
  // The memory view renders conversation turns, not consent/privacy memory objects.
  // Full memory management (inspect/delete individual items) is tracked in docs/ui-gap.md
  // and deferred to G-12 (Consent + Memory ledger backend).
  async function loadMemory() {
    const list = document.getElementById('memory-list');
    if (!list) return;
    list.innerHTML = '<div class="empty-state"><p>Loading...</p></div>';
    const data = await api('/memory/list');
    const memories = data && data.memories ? data.memories : [];
    if (memories.length === 0) {
      list.innerHTML = '<div class="empty-state"><p>No memories stored yet.</p><p class="muted">Memories appear here as you interact with GAIA.</p></div>';
      return;
    }
    list.innerHTML = memories.map(m => `
      <div class="memory-entry">
        <div class="memory-content">${escHtml(m.query || '')}</div>
        <div class="memory-meta">
          <span class="tag">${m.source_count != null ? m.source_count + ' sources' : ''}</span>
          <span class="muted">${m.timestamp ? new Date(m.timestamp * 1000).toLocaleString() : ''}</span>
        </div>
      </div>
    `).join('');
  }

  const btnRefreshMemory = document.getElementById('btn-refresh-memory');
  if (btnRefreshMemory) btnRefreshMemory.addEventListener('click', loadMemory);

  // --- Consent View ---
  // G-5: /consent/ledger has no backend yet. Tracked in docs/ui-gap.md (G-12).
  async function loadConsent() {
    const list = document.getElementById('consent-list');
    if (!list) return;
    list.innerHTML = '<div class="empty-state"><p>Consent ledger coming soon.</p><p class="muted">All consents granted to GAIA will appear here. Revoke any at any time.</p></div>';
  }

  // --- Canon View ---
  async function loadCanon() {
    const status = await api('/status');
    const list = document.getElementById('canon-list');
    if (!list) return;
    // G-5 fix: server returns canon_docs (string array) and canon_doc_count
    const docs = status && status.canon_docs ? status.canon_docs : [];
    const docHtml = docs.length > 0
      ? docs.map(d => `<div class="canon-entry"><span class="tag">${escHtml(d)}</span></div>`).join('')
      : '';
    list.innerHTML = docHtml + `
      <a href="https://github.com/R0GV3TheAlchemist/GAIA" target="_blank" rel="noopener noreferrer" class="canon-link">
        View full canon on GitHub →
      </a>
    `;
  }

  // --- ATLAS View ---
  // G-5: Atlas backend (/atlas/*) not yet implemented. Tracked in docs/ui-gap.md (G-11).
  const btnQueryAtlas = document.getElementById('btn-query-atlas');
  if (btnQueryAtlas) {
    btnQueryAtlas.addEventListener('click', async () => {
      const lat = document.getElementById('atlas-lat').value;
      const lon = document.getElementById('atlas-lon').value;
      const results = document.getElementById('atlas-results');

      results.innerHTML = '<div class="empty-state"><p>ATLAS module not yet available.</p><p class="muted">Requires Google Earth Engine backend (G-11). Run <code>earthengine authenticate</code> to prepare.</p></div>';
    });
  }

  // --- Utilities ---
  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // --- Init ---
  setTheme('dark');
  showView('home');
  refreshStatus();

  // Auto-refresh status every 30 seconds
  setInterval(refreshStatus, 30000);

})();

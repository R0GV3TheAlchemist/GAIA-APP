/**
 * GAIA-APP — UI Shell
 * Handles navigation, theme toggle, live API calls to the constitutional core,
 * and ATLAS Earth Intelligence queries.
 *
 * API target: http://localhost:8008 (dev) or GAIA_API_URL env (production)
 * Constitutional core lives in core/ (Python FastAPI server)
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
    // Lazy-load view data
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
      setDot('canon', status.canon_loaded ? 'green' : 'yellow',
             status.canon_loaded ? `Canon: Loaded (${status.canon_docs.length} docs)` : 'Canon: Loading');
    } else {
      setDot('core', 'red', 'Core: Offline — run python core/server.py');
      setDot('canon', 'red', 'Canon: Unreachable');
    }
    // Check ATLAS separately
    const atlas = await api('/atlas/status');
    if (atlas && atlas.atlas === 'connected') {
      setDot('atlas', 'green', 'Atlas: Connected');
    } else {
      setDot('atlas', 'yellow', 'Atlas: Run earthengine authenticate');
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
  async function loadMemory() {
    const list = document.getElementById('memory-list');
    if (!list) return;
    list.innerHTML = '<div class="empty-state"><p>Loading...</p></div>';
    const memories = await api('/memory/list');
    if (!memories || memories.length === 0) {
      list.innerHTML = '<div class="empty-state"><p>No memories stored yet.</p><p class="muted">Memories appear here as you interact with GAIA.</p></div>';
      return;
    }
    list.innerHTML = memories.map(m => `
      <div class="memory-entry" data-id="${m.memory_id}">
        <div class="memory-content">${escHtml(m.content)}</div>
        <div class="memory-meta">
          <span class="tag">${escHtml(m.source)}</span>
          <span class="tag">${(m.purposes || []).join(', ')}</span>
          <span class="muted">${m.created_at ? m.created_at.slice(0, 10) : ''}</span>
        </div>
        <div class="memory-actions">
          <button class="btn btn-ghost btn-sm" onclick="deleteMemory('${m.memory_id}')">Delete</button>
        </div>
      </div>
    `).join('');
  }

  window.deleteMemory = async function(id) {
    const res = await api('/memory/' + id, { method: 'DELETE' });
    if (res && res.deleted) loadMemory();
  };

  const btnRefreshMemory = document.getElementById('btn-refresh-memory');
  if (btnRefreshMemory) btnRefreshMemory.addEventListener('click', loadMemory);

  // --- Consent View ---
  async function loadConsent() {
    const list = document.getElementById('consent-list');
    if (!list) return;
    const consents = await api('/consent/ledger');
    if (!consents || consents.length === 0) {
      list.innerHTML = '<div class="empty-state"><p>No consent records yet.</p><p class="muted">Consents appear here when you authorize GAIA to act on your behalf.</p></div>';
      return;
    }
    const active = consents.filter(c => c.event === 'grant' && c.record && c.record.valid);
    if (active.length === 0) {
      list.innerHTML = '<div class="empty-state"><p>No active consents.</p></div>';
      return;
    }
    list.innerHTML = active.map(c => `
      <div class="consent-entry">
        <div class="consent-purpose">${escHtml(c.record.purpose)}</div>
        <div class="consent-meta">
          <span class="tag">${escHtml(c.record.party_id)}</span>
          <span class="muted">Expires: ${c.record.expires_at ? c.record.expires_at.slice(0, 10) : 'Never'}</span>
        </div>
        <div class="memory-actions">
          <button class="btn btn-ghost btn-sm" onclick="revokeConsent('${c.record.party_id}', '${c.record.purpose}')">Revoke</button>
        </div>
      </div>
    `).join('');
  }

  window.revokeConsent = async function(partyId, purpose) {
    await api('/consent/revoke', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ party_id: partyId, purpose: purpose })
    });
    loadConsent();
  };

  // --- Canon View ---
  async function loadCanon() {
    const status = await api('/status');
    const list = document.getElementById('canon-list');
    if (!list) return;
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
  const btnQueryAtlas = document.getElementById('btn-query-atlas');
  if (btnQueryAtlas) {
    btnQueryAtlas.addEventListener('click', async () => {
      const lat = document.getElementById('atlas-lat').value;
      const lon = document.getElementById('atlas-lon').value;
      const results = document.getElementById('atlas-results');
      results.innerHTML = '<div class="empty-state"><p>Querying Earth...</p></div>';
      btnQueryAtlas.disabled = true;

      const [temp, ndvi, air] = await Promise.all([
        api(`/atlas/temperature?lat=${lat}&lon=${lon}`),
        api(`/atlas/ndvi?lat=${lat}&lon=${lon}`),
        api(`/atlas/air-quality?lat=${lat}&lon=${lon}`)
      ]);

      btnQueryAtlas.disabled = false;

      if (!temp && !ndvi && !air) {
        results.innerHTML = '<div class="empty-state"><p>ATLAS unavailable.</p><p class="muted">Run: earthengine authenticate</p></div>';
        return;
      }

      results.innerHTML = `
        <div class="atlas-grid">
          <div class="atlas-card">
            <div class="atlas-card-icon">🌡️</div>
            <div class="atlas-card-label">Surface Temperature</div>
            <div class="atlas-card-value">${temp && temp.temperature_celsius != null ? temp.temperature_celsius + '°C' : 'N/A'}</div>
            <div class="atlas-card-source">${temp ? temp.source : ''}</div>
          </div>
          <div class="atlas-card">
            <div class="atlas-card-icon">🌿</div>
            <div class="atlas-card-label">Vegetation (NDVI)</div>
            <div class="atlas-card-value">${ndvi && ndvi.ndvi_scaled != null ? ndvi.ndvi_scaled : 'N/A'}</div>
            <div class="atlas-card-source">${ndvi ? ndvi.source : ''}</div>
          </div>
          <div class="atlas-card">
            <div class="atlas-card-icon">💨</div>
            <div class="atlas-card-label">Air Quality (NO₂)</div>
            <div class="atlas-card-value">${air && air.no2_mol_per_m2 != null ? air.no2_mol_per_m2.toExponential(3) + ' mol/m²' : 'N/A'}</div>
            <div class="atlas-card-source">${air ? air.source : ''}</div>
          </div>
        </div>
        <p class="atlas-coords-label">📍 ${lat}, ${lon}</p>
      `;
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

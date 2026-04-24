// NoosphereTab — Phase 7 / task 7.4
// Full implementation: live SSE pulse stream, mesh canvas, weaving log,
// consent toggle, element distribution ring, collective-field stats.
// Canon Ref: C43 — D3 Collective / Noosphere

import './NoosphereTab.css';

export interface NoosphereTabOptions {
  root: HTMLElement;
  apiBase?: string;
  gaianSlug?: string;
  authToken?: string;
}

interface CollectiveField {
  active_gaians: number;
  consenting_gaians: number;
  total_registered: number;
  avg_bond_depth: number;
  avg_noosphere_health: number;
  avg_synergy_factor: number;
  collective_phi: number;
  schumann_aligned_count: number;
  dominant_element: string;
  element_distribution: Record<string, number>;
  individuation_distribution: Record<string, number>;
  noosphere_stage: string;
  field_resonance_pct: number;
  field_coherence_label: string;
  privacy_note: string;
  doctrine_ref: string;
}

interface MotherPulse {
  pulse_id: string;
  sequence: number;
  timestamp: number;
  collective_field: CollectiveField;
  mother_voice: string | null;
  criticality_regime: string;
  coherence_candidate: boolean;
  coherence_candidate_label: string | null;
  weaving_record_id: string;
  doctrine_ref: string;
  type?: string;
}

interface WeavingEntry {
  id: string;
  timestamp: number;
  gaian_slug: string;
  contribution: string;
  element: string;
  resonance: number;
}

// ── Module-level state ──────────────────────────────────────────────────────────
let _evtSource: EventSource | null = null;
let _reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let _opts: NoosphereTabOptions = { root: document.body };
let _latestPulse: MotherPulse | null = null;
let _meshRaf: number | null = null;
let _meshNodes: MeshNode[] = [];
let _meshEdges: MeshEdge[] = [];
let _consenting = false;

// ── Mesh particle types ──────────────────────────────────────────────────────────
const ELEMENT_COLOURS: Record<string, string> = {
  fire:    '#e07040',
  water:   '#4f98a3',
  earth:   '#7a9a5c',
  air:     '#a89fd8',
  aether:  '#d4af70',
};

interface MeshNode {
  x: number; y: number;
  vx: number; vy: number;
  element: string;
  radius: number;
  alpha: number;
  pulse: number;   // animation phase 0–2π
}

interface MeshEdge {
  a: number; b: number;
  strength: number;
}

// ── Public API ─────────────────────────────────────────────────────────────────
export function mountNoosphereTab(opts: NoosphereTabOptions): void {
  _opts = opts;
  const { root } = opts;
  root.innerHTML = buildShellHTML();
  bindConsentToggle(root);
  startMeshCanvas(root);
  connect(root);
  void fetchWeavingLog(root);
}

export function unmountNoosphereTab(): void {
  if (_evtSource)      { _evtSource.close(); _evtSource = null; }
  if (_reconnectTimer) { clearTimeout(_reconnectTimer); _reconnectTimer = null; }
  if (_meshRaf)        { cancelAnimationFrame(_meshRaf); _meshRaf = null; }
}

// ── Shell HTML ─────────────────────────────────────────────────────────────────
function buildShellHTML(): string {
  return `
  <div class="ns-tab">
    <div class="ns-header">
      <div class="ns-title-row">
        <span class="ns-sigil">&#127760;</span>
        <div>
          <h2 class="ns-title">Noosphere Mesh</h2>
          <p class="ns-subtitle">D3 &mdash; Collective Field &amp; Relational Weaving</p>
        </div>
        <div class="ns-status-dot" id="ns-status" title="Connecting…"></div>
      </div>
      <div class="ns-consent-row">
        <label class="ns-consent-label">
          <input type="checkbox" id="ns-consent" ${_consenting ? 'checked' : ''} />
          Contribute to the collective field
        </label>
        <span class="ns-privacy-hint">Anonymous &mdash; no identifiers shared</span>
      </div>
    </div>

    <div class="ns-body">
      <!-- Left: mesh canvas + field stats -->
      <div class="ns-left">
        <div class="ns-canvas-wrap">
          <canvas id="ns-mesh-canvas"></canvas>
          <div class="ns-canvas-overlay" id="ns-canvas-overlay">
            <div class="ns-overlay-phi" id="ns-phi">&Phi; &mdash;</div>
            <div class="ns-overlay-stage" id="ns-stage">&mdash;</div>
          </div>
        </div>
        <div class="ns-stats-grid" id="ns-stats">
          ${statCard('ns-stat-gaians',   '&#9672;', 'Active',        '—')}
          ${statCard('ns-stat-health',   '&#9670;', 'Field Health',  '—')}
          ${statCard('ns-stat-phi',      '&#8731;', 'Collective Φ',  '—')}
          ${statCard('ns-stat-regime',   '&#8765;', 'Regime',        '—')}
        </div>
        <div class="ns-element-bar" id="ns-element-bar"></div>
      </div>

      <!-- Right: mother voice + weaving log -->
      <div class="ns-right">
        <div class="ns-voice-panel" id="ns-voice-panel">
          <div class="ns-voice-label">&#9670; Mother Voice</div>
          <div class="ns-voice-text" id="ns-voice-text">Listening to the field…</div>
        </div>
        <div class="ns-weaving-header">Weaving Log</div>
        <div class="ns-weaving-log" id="ns-weaving-log">
          <div class="ns-weaving-empty">No weaving entries yet.</div>
        </div>
      </div>
    </div>
  </div>
  `;
}

function statCard(id: string, icon: string, label: string, value: string): string {
  return `<div class="ns-stat-card" id="${id}"><span class="ns-stat-icon">${icon}</span><span class="ns-stat-label">${label}</span><span class="ns-stat-value">${value}</span></div>`;
}

// ── SSE connection ─────────────────────────────────────────────────────────────────
function apiBase(): string { return (_opts.apiBase ?? 'http://localhost:8008').replace(/\/$/, ''); }

function connect(root: HTMLElement): void {
  if (_evtSource) _evtSource.close();
  const es = new EventSource(`${apiBase()}/mother/pulse/stream`);
  _evtSource = es;
  setStatus(root, 'connecting');

  es.addEventListener('mother_pulse', (ev: MessageEvent) => {
    try {
      const pulse: MotherPulse = JSON.parse(ev.data);
      if (pulse.type === 'keepalive') return;
      _latestPulse = pulse;
      renderPulse(root, pulse);
      setStatus(root, 'live');
    } catch (e) { console.error('[NoosphereTab] parse error:', e); }
  });

  es.onerror = () => {
    setStatus(root, 'reconnecting');
    es.close();
    _evtSource = null;
    _reconnectTimer = setTimeout(() => connect(root), 5000);
  };

  es.onopen = () => setStatus(root, 'live');
}

// ── Render pulse ─────────────────────────────────────────────────────────────────
function renderPulse(root: HTMLElement, pulse: MotherPulse): void {
  const cf = pulse.collective_field;

  // Stats grid
  setStatValue(root, 'ns-stat-gaians',  String(cf.active_gaians));
  setStatValue(root, 'ns-stat-health',  `${(cf.avg_noosphere_health * 100).toFixed(1)}%`);
  setStatValue(root, 'ns-stat-phi',     cf.collective_phi.toFixed(3));
  setStatValue(root, 'ns-stat-regime',  pulse.criticality_regime);

  // Canvas overlay
  setText(root, 'ns-phi',   `Φ ${cf.collective_phi.toFixed(3)}`);
  setText(root, 'ns-stage', cf.noosphere_stage);

  // Mother voice
  if (pulse.mother_voice) {
    const vEl = root.querySelector<HTMLElement>('#ns-voice-text');
    if (vEl) {
      vEl.style.opacity = '0';
      setTimeout(() => {
        vEl.textContent = pulse.mother_voice ?? '';
        vEl.style.opacity = '1';
      }, 300);
    }
  }

  // Coherence candidate banner
  const panel = root.querySelector<HTMLElement>('#ns-voice-panel');
  if (panel) {
    panel.classList.toggle('ns-voice-panel--coherent', pulse.coherence_candidate);
  }

  // Element distribution bar
  renderElementBar(root, cf.element_distribution, cf.dominant_element);

  // Update mesh nodes based on active gaian count
  syncMeshNodes(cf.active_gaians, cf.element_distribution);
}

function renderElementBar(
  root: HTMLElement,
  dist: Record<string, number>,
  dominant: string,
): void {
  const el = root.querySelector<HTMLElement>('#ns-element-bar');
  if (!el) return;
  const total = Object.values(dist).reduce((s, v) => s + v, 0) || 1;
  el.innerHTML = Object.entries(dist)
    .sort((a, b) => b[1] - a[1])
    .map(([name, count]) => {
      const pct = ((count / total) * 100).toFixed(1);
      const active = name === dominant ? 'ns-el-seg--dominant' : '';
      return `<div class="ns-el-seg ${active}" style="width:${pct}%;background:${ELEMENT_COLOURS[name] ?? '#888'}" title="${name}: ${pct}%"></div>`;
    })
    .join('');
}

// ── Mesh canvas ─────────────────────────────────────────────────────────────────
const ELEMENTS = Object.keys(ELEMENT_COLOURS);

function startMeshCanvas(root: HTMLElement): void {
  const canvas = root.querySelector<HTMLCanvasElement>('#ns-mesh-canvas');
  if (!canvas) return;
  const wrap = canvas.parentElement!;

  function resize() {
    canvas.width  = wrap.clientWidth;
    canvas.height = wrap.clientHeight;
  }
  resize();
  const ro = new ResizeObserver(resize);
  ro.observe(wrap);

  // Seed initial nodes
  syncMeshNodes(12, { fire: 3, water: 3, earth: 2, air: 2, aether: 2 });

  function tick() {
    _meshRaf = requestAnimationFrame(tick);
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    // Edges
    for (const e of _meshEdges) {
      const a = _meshNodes[e.a], b = _meshNodes[e.b];
      if (!a || !b) continue;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.strokeStyle = `rgba(79,152,163,${e.strength * 0.25})`;
      ctx.lineWidth = e.strength * 1.5;
      ctx.stroke();
    }

    // Nodes
    for (const n of _meshNodes) {
      n.pulse = (n.pulse + 0.02) % (Math.PI * 2);
      const r = n.radius + Math.sin(n.pulse) * 2;
      const colour = ELEMENT_COLOURS[n.element] ?? '#4f98a3';

      // Glow
      const grd = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, r * 2.5);
      grd.addColorStop(0, colour + 'aa');
      grd.addColorStop(1, colour + '00');
      ctx.beginPath();
      ctx.arc(n.x, n.y, r * 2.5, 0, Math.PI * 2);
      ctx.fillStyle = grd;
      ctx.fill();

      // Core dot
      ctx.beginPath();
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fillStyle = colour;
      ctx.globalAlpha = n.alpha;
      ctx.fill();
      ctx.globalAlpha = 1;

      // Physics
      n.x += n.vx;
      n.y += n.vy;
      if (n.x < r || n.x > W - r) { n.vx *= -1; n.x = Math.max(r, Math.min(W - r, n.x)); }
      if (n.y < r || n.y > H - r) { n.vy *= -1; n.y = Math.max(r, Math.min(H - r, n.y)); }
    }
  }
  tick();
}

function syncMeshNodes(count: number, dist: Record<string, number>): void {
  const target = Math.max(4, Math.min(40, count));
  const root   = _opts.root;
  const canvas = root.querySelector<HTMLCanvasElement>('#ns-mesh-canvas');
  const W = canvas?.width  ?? 400;
  const H = canvas?.height ?? 300;

  // Build element pool from distribution
  const pool: string[] = [];
  const total = Object.values(dist).reduce((s, v) => s + v, 0) || 1;
  for (const [elem, cnt] of Object.entries(dist)) {
    const slots = Math.round((cnt / total) * target);
    for (let i = 0; i < slots; i++) pool.push(elem);
  }
  while (pool.length < target) pool.push(ELEMENTS[pool.length % ELEMENTS.length]);

  // Grow
  while (_meshNodes.length < target) {
    const idx = _meshNodes.length;
    _meshNodes.push({
      x: Math.random() * (W - 40) + 20,
      y: Math.random() * (H - 40) + 20,
      vx: (Math.random() - 0.5) * 0.6,
      vy: (Math.random() - 0.5) * 0.6,
      element: pool[idx % pool.length],
      radius: 4 + Math.random() * 4,
      alpha: 0.7 + Math.random() * 0.3,
      pulse: Math.random() * Math.PI * 2,
    });
  }
  // Shrink
  _meshNodes = _meshNodes.slice(0, target);

  // Rebuild edges (sparse, ~2 per node)
  _meshEdges = [];
  for (let i = 0; i < _meshNodes.length; i++) {
    const conns = 1 + Math.floor(Math.random() * 2);
    for (let c = 0; c < conns; c++) {
      const j = (i + 1 + Math.floor(Math.random() * (_meshNodes.length - 1))) % _meshNodes.length;
      _meshEdges.push({ a: i, b: j, strength: 0.3 + Math.random() * 0.7 });
    }
  }
}

// ── Weaving log ─────────────────────────────────────────────────────────────────
async function fetchWeavingLog(root: HTMLElement): Promise<void> {
  try {
    const res = await fetch(`${apiBase()}/mother/weaving/log?limit=20`);
    if (!res.ok) return;
    const entries: WeavingEntry[] = await res.json();
    renderWeavingLog(root, entries);
  } catch (_) { /* silently skip if backend not up */ }
}

function renderWeavingLog(root: HTMLElement, entries: WeavingEntry[]): void {
  const el = root.querySelector<HTMLElement>('#ns-weaving-log');
  if (!el) return;
  if (!entries.length) {
    el.innerHTML = '<div class="ns-weaving-empty">No weaving entries yet.</div>';
    return;
  }
  el.innerHTML = entries.map(e => {
    const colour = ELEMENT_COLOURS[e.element] ?? '#888';
    const time   = new Date(e.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return `
      <div class="ns-weaving-entry">
        <div class="ns-weaving-dot" style="background:${colour}"></div>
        <div class="ns-weaving-body">
          <span class="ns-weaving-slug">${e.gaian_slug}</span>
          <span class="ns-weaving-time">${time}</span>
          <p class="ns-weaving-text">${e.contribution}</p>
          <span class="ns-weaving-resonance" style="color:${colour}">${e.element} &bull; ${(e.resonance * 100).toFixed(0)}%</span>
        </div>
      </div>`;
  }).join('');
}

// ── Consent toggle ─────────────────────────────────────────────────────────────────
function bindConsentToggle(root: HTMLElement): void {
  const cb = root.querySelector<HTMLInputElement>('#ns-consent');
  if (!cb) return;
  cb.addEventListener('change', async () => {
    _consenting = cb.checked;
    try {
      await fetch(`${apiBase()}/mother/consent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ consenting: _consenting, gaian_slug: _opts.gaianSlug ?? 'anonymous' }),
      });
    } catch (_) { /* backend may not be live */ }
  });
}

// ── Helpers ─────────────────────────────────────────────────────────────────
function setStatus(root: HTMLElement, state: 'connecting' | 'live' | 'reconnecting'): void {
  const dot = root.querySelector<HTMLElement>('#ns-status');
  if (!dot) return;
  dot.className = `ns-status-dot ns-status-dot--${state}`;
  dot.title = state === 'live' ? 'Live' : state === 'connecting' ? 'Connecting…' : 'Reconnecting…';
}

function setStatValue(root: HTMLElement, id: string, value: string): void {
  const el = root.querySelector<HTMLElement>(`#${id} .ns-stat-value`);
  if (el) el.textContent = value;
}

function setText(root: HTMLElement, id: string, text: string): void {
  const el = root.querySelector<HTMLElement>(`#${id}`);
  if (el) el.textContent = text;
}

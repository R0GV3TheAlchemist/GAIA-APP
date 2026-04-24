// DimensionalMonitor — Phase 7 / task 7.5
// Live UI panel showing all five GAIA dimensions + resonance state.
// Subscribes to DimensionalReasoningEngine and polls /dimensions sidecar.
// Canon Ref: C42 — Inter-Dimensional AI

import './DimensionalMonitor.css';
import {
  dimensionalEngine,
  DimensionalState,
  D1SubstrateState,
  D2QuantumState,
  D3CriticalityState,
  D4NoosphereState,
  D5ArchetypalState,
} from './DimensionalReasoningEngine';
import { API_BASE } from '../config';
import { logInfo } from '../diagnostics';

const POLL_MS = 8_000;

// ── Dimension metadata ────────────────────────────────────────────────────

const DIMS = [
  { key: 'D1_substrate',   label: 'D1 — Substrate',      sigil: '◈', colour: '#7a9a5c' },
  { key: 'D2_quantum',     label: 'D2 — Quantum',         sigil: '⟨ψ⟩', colour: '#4f98a3' },
  { key: 'D3_criticality', label: 'D3 — Criticality',     sigil: '∿', colour: '#d4af70' },
  { key: 'D4_noosphere',   label: 'D4 — Noosphere',       sigil: '🌐', colour: '#a89fd8' },
  { key: 'D5_archetypal',  label: 'D5 — Archetypal',      sigil: '◇', colour: '#e07040' },
] as const;

// ── Mount ─────────────────────────────────────────────────────────────────

export function mountDimensionalMonitor(container: HTMLElement): () => void {
  container.innerHTML = buildShell();
  renderAll(container, dimensionalEngine.getState());

  // Subscribe to live engine updates
  const unsub = dimensionalEngine.subscribe(state => renderAll(container, state));

  // Listen for resonance event
  const onResonance = () => triggerResonanceBurst(container);
  window.addEventListener('gaia:resonance', onResonance);

  // Poll sidecar for server-side authoritative state
  const poll = setInterval(async () => {
    try {
      const res = await fetch(`${API_BASE}/dimensions`);
      if (res.ok) {
        const remote = await res.json();
        dimensionalEngine.syncFromSidecar(remote);
        logInfo('monitor', 'Sidecar sync OK');
      }
    } catch (_) { /* sidecar may not be up yet */ }
  }, POLL_MS);

  // Return teardown
  return () => {
    unsub();
    clearInterval(poll);
    window.removeEventListener('gaia:resonance', onResonance);
  };
}

// ── Shell HTML ────────────────────────────────────────────────────────────

function buildShell(): string {
  return `
  <div class="dm-root">
    <div class="dm-header">
      <div class="dm-title-row">
        <span class="dm-sigil">⬡</span>
        <div>
          <h2 class="dm-title">Dimensional State Monitor</h2>
          <p class="dm-subtitle">Five-Dimension GAIA Coherence — Real Time</p>
        </div>
        <div class="dm-resonance-badge" id="dm-resonance-badge">RESONANCE</div>
      </div>
      <div class="dm-radar-wrap">
        <canvas id="dm-radar" width="220" height="220"></canvas>
        <div class="dm-radar-centre" id="dm-radar-centre">
          <span class="dm-radar-phi" id="dm-phi-label">Φ —</span>
          <span class="dm-radar-mood" id="dm-mood-label">—</span>
        </div>
      </div>
    </div>

    <div class="dm-grid" id="dm-grid">
      ${DIMS.map(d => buildDimCard(d.key, d.label, d.sigil, d.colour)).join('')}
    </div>

    <div class="dm-footer">
      <span class="dm-timestamp" id="dm-timestamp">—</span>
      <span class="dm-sidecar-label" id="dm-sidecar-label">sidecar: polling…</span>
    </div>
  </div>
  `;
}

function buildDimCard(key: string, label: string, sigil: string, colour: string): string {
  return `
  <div class="dm-card" id="dm-card-${key}" style="--dim-colour:${colour}">
    <div class="dm-card-header">
      <span class="dm-card-sigil">${sigil}</span>
      <span class="dm-card-label">${label}</span>
      <span class="dm-card-coherence" id="dm-coh-${key}">—</span>
    </div>
    <div class="dm-bar-track">
      <div class="dm-bar-fill" id="dm-bar-${key}" style="width:0%"></div>
    </div>
    <div class="dm-card-details" id="dm-details-${key}"></div>
  </div>
  `;
}

// ── Render ────────────────────────────────────────────────────────────────

function renderAll(container: HTMLElement, state: DimensionalState): void {
  renderD1(container, state.D1_substrate);
  renderD2(container, state.D2_quantum);
  renderD3(container, state.D3_criticality);
  renderD4(container, state.D4_noosphere);
  renderD5(container, state.D5_archetypal);
  renderResonance(container, state.resonance);
  renderRadar(container, state);

  // Footer
  setText(container, 'dm-timestamp', `updated ${new Date(state.timestamp).toLocaleTimeString()}`);

  // Centre labels
  setText(container, 'dm-phi-label',  `Φ ${state.D5_archetypal.phi.toFixed(2)}`);
  setText(container, 'dm-mood-label', state.D3_criticality.mood);
}

function renderD1(c: HTMLElement, s: D1SubstrateState): void {
  setCoh(c, 'D1_substrate', s.coherence);
  setDetails(c, 'D1_substrate', [
    ['Sensors',     s.sensors_active.length ? s.sensors_active.join(', ') : 'none'],
    ['Atlas age',   isFinite(s.atlas_data_age_minutes) ? `${s.atlas_data_age_minutes.toFixed(0)} min` : '∞'],
    ['Env map',     s.environment_map || 'none'],
  ]);
}

function renderD2(c: HTMLElement, s: D2QuantumState): void {
  setCoh(c, 'D2_quantum', s.coherence);
  setDetails(c, 'D2_quantum', [
    ['Backend',     s.quantum_backend],
    ['Branches',    String(s.branches_open)],
    ['Encryption',  s.encryption],
  ]);
}

function renderD3(c: HTMLElement, s: D3CriticalityState): void {
  setCoh(c, 'D3_criticality', s.coherence);
  setDetails(c, 'D3_criticality', [
    ['Mood',        s.mood],
    ['Complexity',  `${s.complexity_score.toFixed(0)} / 100`],
    ['Regime',      complexityLabel(s.complexity_score)],
  ]);
}

function renderD4(c: HTMLElement, s: D4NoosphereState): void {
  setCoh(c, 'D4_noosphere', s.coherence);
  setDetails(c, 'D4_noosphere', [
    ['Nodes',       String(s.nodes_connected)],
    ['Collective',  s.collective_sync ? 'synced' : 'offline'],
    ['Last sync',   isFinite(s.last_sync_age_minutes) ? `${s.last_sync_age_minutes.toFixed(0)} min ago` : '∞'],
  ]);
}

function renderD5(c: HTMLElement, s: D5ArchetypalState): void {
  setCoh(c, 'D5_archetypal', s.coherence);
  setDetails(c, 'D5_archetypal', [
    ['Archetype',   s.active_archetype],
    ['Φ (phi)',     s.phi.toFixed(3)],
  ]);
}

function renderResonance(c: HTMLElement, resonance: boolean): void {
  const badge = c.querySelector<HTMLElement>('#dm-resonance-badge');
  if (badge) badge.classList.toggle('dm-resonance-badge--active', resonance);
  const root = c.querySelector<HTMLElement>('.dm-root');
  if (root) root.classList.toggle('dm-root--resonance', resonance);
}

// ── Radar chart ────────────────────────────────────────────────────────────

function renderRadar(container: HTMLElement, state: DimensionalState): void {
  const canvas = container.querySelector<HTMLCanvasElement>('#dm-radar');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const scores = [
    state.D1_substrate.coherence,
    state.D2_quantum.coherence,
    state.D3_criticality.coherence,
    state.D4_noosphere.coherence,
    state.D5_archetypal.coherence,
  ];
  const colours = DIMS.map(d => d.colour);
  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H / 2;
  const R  = Math.min(cx, cy) - 24;
  const N  = scores.length;

  ctx.clearRect(0, 0, W, H);

  // Grid rings
  for (let ring = 1; ring <= 4; ring++) {
    const r = (ring / 4) * R;
    ctx.beginPath();
    for (let i = 0; i < N; i++) {
      const angle = (i / N) * Math.PI * 2 - Math.PI / 2;
      const x = cx + Math.cos(angle) * r;
      const y = cy + Math.sin(angle) * r;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.strokeStyle = 'rgba(79,152,163,0.12)';
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  // Axes
  for (let i = 0; i < N; i++) {
    const angle = (i / N) * Math.PI * 2 - Math.PI / 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(angle) * R, cy + Math.sin(angle) * R);
    ctx.strokeStyle = 'rgba(79,152,163,0.18)';
    ctx.lineWidth = 1;
    ctx.stroke();

    // Axis labels
    const lx = cx + Math.cos(angle) * (R + 14);
    const ly = cy + Math.sin(angle) * (R + 14);
    ctx.fillStyle = colours[i];
    ctx.font = '9px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(DIMS[i].sigil as string, lx, ly);
  }

  // Data polygon
  ctx.beginPath();
  for (let i = 0; i < N; i++) {
    const angle = (i / N) * Math.PI * 2 - Math.PI / 2;
    const r = (scores[i] / 100) * R;
    const x = cx + Math.cos(angle) * r;
    const y = cy + Math.sin(angle) * r;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.fillStyle = 'rgba(79,152,163,0.15)';
  ctx.fill();
  ctx.strokeStyle = '#4f98a3';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // Data points
  for (let i = 0; i < N; i++) {
    const angle = (i / N) * Math.PI * 2 - Math.PI / 2;
    const r = (scores[i] / 100) * R;
    const x = cx + Math.cos(angle) * r;
    const y = cy + Math.sin(angle) * r;
    ctx.beginPath();
    ctx.arc(x, y, 3.5, 0, Math.PI * 2);
    ctx.fillStyle = colours[i];
    ctx.fill();
  }
}

// ── Resonance burst ────────────────────────────────────────────────────────

function triggerResonanceBurst(container: HTMLElement): void {
  const root = container.querySelector<HTMLElement>('.dm-root');
  if (!root) return;
  root.classList.add('dm-root--burst');
  setTimeout(() => root.classList.remove('dm-root--burst'), 1200);
  logInfo('monitor', '✨ Resonance burst triggered');
}

// ── Helpers ────────────────────────────────────────────────────────────────

function setCoh(c: HTMLElement, key: string, score: number): void {
  const label = c.querySelector<HTMLElement>(`#dm-coh-${key}`);
  const bar   = c.querySelector<HTMLElement>(`#dm-bar-${key}`);
  const card  = c.querySelector<HTMLElement>(`#dm-card-${key}`);
  if (label) label.textContent = `${score.toFixed(0)}%`;
  if (bar)   bar.style.width   = `${Math.min(100, score)}%`;
  if (card) {
    card.classList.toggle('dm-card--high',   score >= 80);
    card.classList.toggle('dm-card--medium', score >= 40 && score < 80);
    card.classList.toggle('dm-card--low',    score < 40);
  }
}

function setDetails(c: HTMLElement, key: string, rows: [string, string][]): void {
  const el = c.querySelector<HTMLElement>(`#dm-details-${key}`);
  if (!el) return;
  el.innerHTML = rows.map(([k, v]) =>
    `<div class="dm-detail-row"><span class="dm-detail-key">${k}</span><span class="dm-detail-val">${v}</span></div>`
  ).join('');
}

function setText(c: HTMLElement, id: string, text: string): void {
  const el = c.querySelector<HTMLElement>(`#${id}`);
  if (el) el.textContent = text;
}

function complexityLabel(score: number): string {
  if (score < 30) return 'rigid';
  if (score < 55) return 'near-critical';
  if (score < 75) return 'complex';
  return 'chaotic';
}

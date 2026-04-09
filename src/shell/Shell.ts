// GAIA Shell — UI Component (vanilla TypeScript, Tauri-compatible)
// Canonical source: C21 (Interface and Shell Grammar), C19 (Color Doctrine)
// Implements all 8 required state surfaces from C21 §3.

import { execute, executeConfirmed } from './executor';
import { getSession, getPermissions } from './session';
import { getLastN, exportLog } from './audit';
import type { ParsedCommand, ShellOutput } from './types';

const TIER_COLOR_CLASS: Record<string, string> = {
  T0: 'tier-t0', T1: 'tier-t1', T2: 'tier-t2', T3: 'tier-t3', T4: 'tier-t4',
};

const CONFIDENCE_COLOR_CLASS: Record<string, string> = {
  HIGH: 'conf-high', MEDIUM: 'conf-medium', LOW: 'conf-low', UNKNOWN: 'conf-unknown',
};

let _pendingConfirmation: ParsedCommand | null = null;

export function mountShell(rootEl: HTMLElement): void {
  rootEl.innerHTML = buildShellHTML();
  bindEvents(rootEl);
  renderStateSurfaces(rootEl);
}

function buildShellHTML(): string {
  return `
<div class="gaia-shell" role="application" aria-label="GAIA Shell">

  <!-- C21 §3.8 — Interrupt Controls: always visible, always active -->
  <div class="interrupt-bar" role="toolbar" aria-label="Interrupt Controls">
    <span class="shell-label">GAIA OS</span>
    <div class="interrupt-controls">
      <button class="interrupt-btn" data-action="pause" title="Suspend current operation">⏸ PAUSE</button>
      <button class="interrupt-btn" data-action="stop"  title="Terminate current operation">⏹ STOP</button>
      <button class="interrupt-btn" data-action="cancel" title="Terminate and rollback">✕ CANCEL</button>
      <button class="interrupt-btn panic" data-action="panic" title="Terminate all — escalate to HP">⚠ PANIC</button>
    </div>
  </div>

  <!-- Main shell body -->
  <div class="shell-body">

    <!-- Left panel: State Surfaces — C21 §3.1–3.7 -->
    <div class="state-panel" aria-label="System State">

      <!-- §3.2 Session State -->
      <div class="state-surface" id="surface-session">
        <div class="surface-header">SESSION</div>
        <div class="surface-body" id="session-body"></div>
      </div>

      <!-- §3.3 Permission State -->
      <div class="state-surface" id="surface-permissions">
        <div class="surface-header">PERMISSIONS</div>
        <div class="surface-body" id="permissions-body"></div>
      </div>

      <!-- §3.4 Recent Memory Writes -->
      <div class="state-surface" id="surface-memory">
        <div class="surface-header">MEMORY WRITES</div>
        <div class="surface-body" id="memory-body">
          <span class="muted">No writes this session.</span>
        </div>
      </div>

      <!-- §3.5 Recent Consequential Actions -->
      <div class="state-surface" id="surface-actions">
        <div class="surface-header">CONSEQUENTIAL ACTIONS</div>
        <div class="surface-body" id="actions-body">
          <span class="muted">None yet.</span>
        </div>
      </div>

      <!-- §3.6 Audit Trail -->
      <div class="state-surface" id="surface-audit">
        <div class="surface-header">AUDIT TRAIL <button class="inline-btn" id="btn-export-audit">export</button></div>
        <div class="surface-body" id="audit-body">
          <span class="muted">Empty.</span>
        </div>
      </div>

    </div>

    <!-- Right panel: Command area -->
    <div class="command-panel">

      <!-- §3.1 Command Parse State -->
      <div class="state-surface" id="surface-parse">
        <div class="surface-header">COMMAND STATE</div>
        <div class="surface-body" id="parse-body">
          <span class="muted">Awaiting input.</span>
        </div>
      </div>

      <!-- Output area -->
      <div class="output-area" id="output-area" aria-live="polite" aria-label="Shell Output"></div>

      <!-- Confirmation gate (hidden until needed) -->
      <div class="confirm-gate hidden" id="confirm-gate">
        <div class="confirm-message" id="confirm-message"></div>
        <div class="confirm-actions">
          <button id="btn-confirm-yes">Confirm — Proceed</button>
          <button id="btn-confirm-no" class="btn-secondary">Cancel</button>
        </div>
      </div>

      <!-- Input bar -->
      <div class="input-bar">
        <span class="prompt" id="prompt-tier">T1 ›</span>
        <input
          type="text"
          id="shell-input"
          autocomplete="off"
          spellcheck="false"
          placeholder="enter command..."
          aria-label="Shell command input"
        />
        <button id="btn-run">RUN</button>
      </div>

    </div>
  </div>

</div>
  `;
}

function bindEvents(root: HTMLElement): void {
  const input = root.querySelector<HTMLInputElement>('#shell-input')!;
  const runBtn = root.querySelector<HTMLButtonElement>('#btn-run')!;
  const confirmYes = root.querySelector<HTMLButtonElement>('#btn-confirm-yes')!;
  const confirmNo = root.querySelector<HTMLButtonElement>('#btn-confirm-no')!;
  const exportBtn = root.querySelector<HTMLButtonElement>('#btn-export-audit')!;

  // Submit on Enter or Run button
  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') runCommand(root, input.value); });
  runBtn.addEventListener('click', () => runCommand(root, input.value));

  // Confirmation gate
  confirmYes.addEventListener('click', () => {
    if (!_pendingConfirmation) return;
    const result = executeConfirmed(_pendingConfirmation);
    _pendingConfirmation = null;
    hideConfirmGate(root);
    if (result.type === 'output') renderOutput(root, result.output);
    renderStateSurfaces(root);
  });
  confirmNo.addEventListener('click', () => {
    _pendingConfirmation = null;
    hideConfirmGate(root);
    appendOutput(root, buildSystemLine('[CANCELLED] Command cancelled by Human Principal.', 'muted'));
  });

  // Interrupt controls — always active (Kernel invariant)
  root.querySelectorAll<HTMLButtonElement>('.interrupt-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const action = btn.dataset.action ?? 'interrupt';
      const result = execute(action);
      if (result.type === 'interrupt') {
        appendOutput(root, buildSystemLine(`[INTERRUPT] ${action.toUpperCase()} executed.`,
          action === 'panic' ? 'alert' : 'amber'));
      }
      renderStateSurfaces(root);
    });
  });

  // Audit export
  exportBtn.addEventListener('click', () => {
    const blob = new Blob([exportLog()], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gaia-audit-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });
}

function runCommand(root: HTMLElement, raw: string): void {
  const input = root.querySelector<HTMLInputElement>('#shell-input')!;
  if (!raw.trim()) return;

  // Echo the command
  appendOutput(root, buildCommandEcho(raw));
  input.value = '';

  const result = execute(raw);

  switch (result.type) {
    case 'output':
      renderOutput(root, result.output);
      break;

    case 'parse_error':
      appendOutput(root, buildErrorBlock(
        result.message,
        result.suggestion ? `Did you mean: ${result.suggestion}` : undefined
      ));
      updateParseState(root, raw, null);
      break;

    case 'tier_blocked':
      appendOutput(root, buildErrorBlock(
        `[TIER BLOCKED] This action requires ${result.required}. Active tier: ${result.active}.`,
        'Elevate your permission tier or contact your Human Principal.'
      ));
      break;

    case 'awaiting_confirmation': {
      _pendingConfirmation = result.parsed;
      showConfirmGate(root, result.parsed);
      updateParseState(root, raw, result.parsed);
      break;
    }

    case 'interrupt':
      appendOutput(root, buildSystemLine(`[INTERRUPT] ${result.verb.toUpperCase()} — operation halted.`, 'amber'));
      break;
  }

  renderStateSurfaces(root);
}

function renderOutput(root: HTMLElement, out: ShellOutput): void {
  updateParseState(root, '', null);
  const html = `
<div class="shell-output">
  <div class="output-meta">
    <span class="tag status-${out.status.toLowerCase()}">[${out.status}]</span>
    <span class="tag ${CONFIDENCE_COLOR_CLASS[out.confidence]}">[${out.confidence}]</span>
    <span class="tag tier-tag ${TIER_COLOR_CLASS[out.tierActive]}">${out.tierActive}</span>
    <span class="tag muted source-tag">${escHtml(out.source)}</span>
    <span class="tag muted audit-ref">ref: ${escHtml(out.auditRef)}</span>
  </div>
  <div class="output-content">${escHtml(out.content)}</div>
  ${out.actions.length ? `
  <div class="output-actions">
    <span class="muted">Available actions:</span>
    ${out.actions.map(a => `<button class="action-chip">${escHtml(a)}</button>`).join('')}
  </div>` : ''}
</div>
  `;
  appendOutput(root, html);
}

function renderStateSurfaces(root: HTMLElement): void {
  renderSessionSurface(root);
  renderPermissionSurface(root);
  renderAuditSurface(root);
  updatePromptTier(root);
}

function renderSessionSurface(root: HTMLElement): void {
  const s = getSession();
  const body = root.querySelector('#session-body')!;
  body.innerHTML = `
<div class="kv-row"><span class="kv-key">Gaian</span><span class="kv-val">${escHtml(s.gaianId)}</span></div>
<div class="kv-row"><span class="kv-key">Principal</span><span class="kv-val">${escHtml(s.principal)}</span></div>
<div class="kv-row"><span class="kv-key">Started</span><span class="kv-val">${escHtml(s.startedAt)}</span></div>
<div class="kv-row"><span class="kv-key">Tier</span><span class="kv-val tier-badge ${TIER_COLOR_CLASS[s.tierActive]}">${s.tierActive}</span></div>
<div class="kv-row"><span class="kv-key">Scope</span><span class="kv-val">${escHtml(s.scope)}</span></div>
<div class="kv-row"><span class="kv-key">Status</span><span class="kv-val ${s.online ? 'online' : 'offline'}">${s.online ? '● ONLINE' : '○ OFFLINE'}</span></div>
  `;
}

function renderPermissionSurface(root: HTMLElement): void {
  const p = getPermissions();
  const body = root.querySelector('#permissions-body')!;
  body.innerHTML = `
<div class="kv-row"><span class="kv-key">Base</span><span class="kv-val">${p.baseTier}</span></div>
<div class="kv-row"><span class="kv-key">Active</span><span class="kv-val tier-badge ${TIER_COLOR_CLASS[p.activeTier]}">${p.activeTier}</span></div>
${p.elevationExpiry ? `<div class="kv-row"><span class="kv-key">Expires</span><span class="kv-val amber">${escHtml(p.elevationExpiry)}</span></div>` : ''}
${p.pendingRequests.length ? `<div class="kv-row"><span class="kv-key">Pending</span><span class="kv-val amber">${p.pendingRequests.length} request(s)</span></div>` : ''}
  `;
}

function renderAuditSurface(root: HTMLElement): void {
  const entries = getLastN(5);
  const body = root.querySelector('#audit-body')!;
  if (entries.length === 0) {
    body.innerHTML = '<span class="muted">Empty.</span>';
    return;
  }
  body.innerHTML = entries.map(e => `
<div class="audit-row">
  <span class="muted">${e.timestamp.slice(11, 19)}</span>
  <span class="audit-verb">${escHtml(e.verb)}</span>
  ${e.target ? `<span class="muted">→ ${escHtml(e.target)}</span>` : ''}
  <span class="tag status-${e.status.toLowerCase()}">${e.status}</span>
  ${e.irreversible ? '<span class="tag alert">IRREVERSIBLE</span>' : ''}
</div>
  `).join('');
}

function updateParseState(root: HTMLElement, raw: string, parsed: ParsedCommand | null): void {
  const body = root.querySelector('#parse-body')!;
  if (!raw) { body.innerHTML = '<span class="muted">Awaiting input.</span>'; return; }
  if (!parsed) {
    body.innerHTML = `<span class="alert">[PARSE ERROR]</span> <span class="muted">${escHtml(raw)}</span>`;
    return;
  }
  body.innerHTML = `
<div class="kv-row"><span class="kv-key">[PARSED]</span> <span class="kv-val">${escHtml(raw)}</span></div>
<div class="kv-row"><span class="kv-key">Verb</span><span class="kv-val">${escHtml(parsed.verb)}</span><span class="muted">(${parsed.verbClass})</span></div>
${parsed.target ? `<div class="kv-row"><span class="kv-key">Target</span><span class="kv-val">${escHtml(parsed.target)}</span></div>` : ''}
<div class="kv-row"><span class="kv-key">Tier req.</span><span class="kv-val tier-badge ${TIER_COLOR_CLASS[parsed.tierRequired]}">${parsed.tierRequired}</span></div>
<div class="kv-row"><span class="kv-key">Rev.</span><span class="kv-val ${parsed.isIrreversible ? 'alert' : ''}">${parsed.reversibilityClass}${parsed.isIrreversible ? ' ⚠ IRREVERSIBLE' : ''}</span></div>
  `;
}

function showConfirmGate(root: HTMLElement, parsed: ParsedCommand): void {
  const gate = root.querySelector<HTMLElement>('#confirm-gate')!;
  const msg = root.querySelector<HTMLElement>('#confirm-message')!;
  gate.classList.remove('hidden');
  msg.innerHTML = `
<strong>[CONFIRMATION REQUIRED — C21 I-6]</strong><br/>
Verb: <span class="amber">${escHtml(parsed.verb)}</span> &nbsp;
Reversibility: <span class="${parsed.isIrreversible ? 'alert' : 'amber'}">${parsed.reversibilityClass}${parsed.isIrreversible ? ' — IRREVERSIBLE' : ''}</span><br/>
${parsed.target ? `Target: <span class="muted">${escHtml(parsed.target)}</span><br/>` : ''}
${parsed.isIrreversible ? '<span class="alert">⚠ This action cannot be undone. Human Principal ratification required.</span>' : ''}
  `;
}

function hideConfirmGate(root: HTMLElement): void {
  root.querySelector<HTMLElement>('#confirm-gate')!.classList.add('hidden');
}

function updatePromptTier(root: HTMLElement): void {
  const { tierActive } = getSession();
  const prompt = root.querySelector<HTMLElement>('#prompt-tier')!;
  prompt.textContent = `${tierActive} ›`;
  prompt.className = `prompt ${TIER_COLOR_CLASS[tierActive]}`;
}

function buildCommandEcho(raw: string): string {
  return `<div class="cmd-echo"><span class="prompt-char">›</span> <span>${escHtml(raw)}</span></div>`;
}

function buildErrorBlock(message: string, hint?: string): string {
  return `<div class="shell-error"><span class="alert">[ERROR]</span> ${escHtml(message)}${
    hint ? `<br/><span class="muted">${escHtml(hint)}</span>` : ''}</div>`;
}

function buildSystemLine(message: string, cls = ''): string {
  return `<div class="system-line ${cls}">${escHtml(message)}</div>`;
}

function appendOutput(root: HTMLElement, html: string): void {
  const area = root.querySelector<HTMLElement>('#output-area')!;
  const div = document.createElement('div');
  div.innerHTML = html;
  area.appendChild(div);
  area.scrollTop = area.scrollHeight;
}

function escHtml(s: string): string {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

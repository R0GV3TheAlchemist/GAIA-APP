// GAIA Memory Panel — CAP-017 (Persistent Memory)
// Canonical source: C17 (Persistent Memory and Identity Architecture)
//
// Every memory entry the GAIAN owns is visible, editable, and deletable here.
// The backend endpoints are already live:
//   GET  /memory/list
//   POST /memory/add
//   PUT  /memory/:id
//   DELETE /memory/:id
//   GET  /memory/audit

import { API_BASE } from '../chat/types';

interface MemoryEntry {
  id: string;
  content: string;
  source: string;
  purposes: string[];
  confidence: number;
  created_at: string;
  updated_at: string;
  deleted: boolean;
  frozen: boolean;
  edit_count: number;
}

interface AuditEntry {
  action: string;
  memory_id: string;
  timestamp: string;
  detail?: string;
}

let _entries: MemoryEntry[] = [];
let _auditLog: AuditEntry[] = [];
let _editingId: string | null = null;

export function mountMemory(root: HTMLElement): void {
  root.innerHTML = buildMemoryHTML();
  bindMemoryEvents(root);
  loadMemory(root);
}

// ------------------------------------------------------------------ //
//  HTML Template                                                       //
// ------------------------------------------------------------------ //

function buildMemoryHTML(): string {
  return `
<div class="gaia-memory">

  <div class="memory-header">
    <div class="memory-title">
      <span class="mem-wordmark">MEMORY</span>
      <span class="mem-subtitle">GAIAN-owned · C17 governed · 24h deletion guarantee</span>
    </div>
    <div class="memory-header-actions">
      <button class="mem-hdr-btn" id="btn-refresh">↻ Refresh</button>
      <button class="mem-hdr-btn" id="btn-audit-toggle">▦ Audit Log</button>
      <button class="mem-hdr-btn danger" id="btn-delete-all">&#128465; Delete All</button>
    </div>
  </div>

  <!-- Add memory form -->
  <div class="mem-add-bar">
    <input
      type="text"
      id="mem-input"
      placeholder="Add a memory… (e.g. \"I prefer concise answers\" or \"My location is San Antonio\")"
      autocomplete="off"
    />
    <select id="mem-source">
      <option value="explicit">Explicit</option>
      <option value="inferred">Inferred</option>
      <option value="session">Session</option>
    </select>
    <button id="btn-add-mem">+ Add</button>
  </div>

  <!-- Stats bar -->
  <div class="mem-stats" id="mem-stats">
    <span class="stat-chip" id="stat-total">0 memories</span>
    <span class="stat-chip" id="stat-explicit">0 explicit</span>
    <span class="stat-chip" id="stat-inferred">0 inferred</span>
    <span class="stat-chip canonical">C17 · You own this data</span>
  </div>

  <!-- Memory list + audit side by side -->
  <div class="mem-body">

    <!-- Memory entries -->
    <div class="mem-list-col">
      <div class="mem-list" id="mem-list">
        <div class="mem-empty" id="mem-empty">No memories stored. Add one above or chat with GAIA.</div>
      </div>
    </div>

    <!-- Audit log (hidden by default) -->
    <div class="mem-audit-col hidden" id="mem-audit-col">
      <div class="mem-audit-header">AUDIT LOG</div>
      <div class="mem-audit-list" id="mem-audit-list">
        <span class="mem-muted">Loading…</span>
      </div>
    </div>

  </div>

</div>
`;
}

// ------------------------------------------------------------------ //
//  Events                                                              //
// ------------------------------------------------------------------ //

function bindMemoryEvents(root: HTMLElement): void {
  root.querySelector('#btn-refresh')!.addEventListener('click', () => loadMemory(root));

  root.querySelector('#btn-audit-toggle')!.addEventListener('click', () => {
    const col = root.querySelector<HTMLElement>('#mem-audit-col')!;
    const btn = root.querySelector<HTMLButtonElement>('#btn-audit-toggle')!;
    const hidden = col.classList.toggle('hidden');
    btn.textContent = hidden ? '▦ Audit Log' : '▦ Hide Audit';
    if (!hidden) loadAudit(root);
  });

  root.querySelector('#btn-delete-all')!.addEventListener('click', async () => {
    if (!confirm('Delete ALL memory entries? This cannot be undone.')) return;
    for (const e of _entries) {
      await fetch(`${API_BASE}/memory/${e.id}`, { method: 'DELETE' });
    }
    await loadMemory(root);
    showToast(root, 'All memories deleted.');
  });

  const addBtn = root.querySelector<HTMLButtonElement>('#btn-add-mem')!;
  const addInput = root.querySelector<HTMLInputElement>('#mem-input')!;

  addBtn.addEventListener('click', () => addMemory(root));
  addInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') addMemory(root);
  });
}

// ------------------------------------------------------------------ //
//  API Calls                                                           //
// ------------------------------------------------------------------ //

async function loadMemory(root: HTMLElement): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/memory/list`, { signal: AbortSignal.timeout(4000) });
    if (!res.ok) throw new Error(`${res.status}`);
    _entries = await res.json();
    renderEntries(root);
    updateStats(root);
  } catch {
    renderOffline(root);
  }
}

async function loadAudit(root: HTMLElement): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/memory/audit`, { signal: AbortSignal.timeout(4000) });
    if (!res.ok) throw new Error(`${res.status}`);
    _auditLog = await res.json();
    renderAudit(root);
  } catch {
    root.querySelector('#mem-audit-list')!.innerHTML = '<span class="mem-muted">Audit unavailable — start server.</span>';
  }
}

async function addMemory(root: HTMLElement): Promise<void> {
  const input  = root.querySelector<HTMLInputElement>('#mem-input')!;
  const source = root.querySelector<HTMLSelectElement>('#mem-source')!;
  const text = input.value.trim();
  if (!text) return;

  try {
    const res = await fetch(`${API_BASE}/memory/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: text, source: source.value, purposes: ['general'], confidence: 1.0 }),
    });
    if (!res.ok) throw new Error(`${res.status}`);
    input.value = '';
    await loadMemory(root);
    showToast(root, 'Memory added.');
  } catch {
    showToast(root, 'Failed to add memory — is the server running?', true);
  }
}

async function saveEdit(root: HTMLElement, id: string, newContent: string): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/memory/${id}?new_content=${encodeURIComponent(newContent)}`, {
      method: 'PUT',
    });
    if (!res.ok) throw new Error(`${res.status}`);
    _editingId = null;
    await loadMemory(root);
    showToast(root, 'Memory updated.');
  } catch {
    showToast(root, 'Failed to save — is the server running?', true);
  }
}

async function deleteEntry(root: HTMLElement, id: string): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/memory/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`${res.status}`);
    await loadMemory(root);
    showToast(root, 'Memory deleted.');
  } catch {
    showToast(root, 'Failed to delete — is the server running?', true);
  }
}

// ------------------------------------------------------------------ //
//  Render                                                              //
// ------------------------------------------------------------------ //

function renderEntries(root: HTMLElement): void {
  const list = root.querySelector<HTMLElement>('#mem-list')!;
  const empty = root.querySelector<HTMLElement>('#mem-empty')!;
  const active = _entries.filter(e => !e.deleted);

  if (!active.length) {
    list.innerHTML = '';
    list.appendChild(empty);
    empty.style.display = 'block';
    return;
  }

  empty.style.display = 'none';
  list.innerHTML = active.map(e => {
    const isEditing = _editingId === e.id;
    const conf = Math.round(e.confidence * 100);
    const confClass = conf >= 80 ? 'conf-high' : conf >= 50 ? 'conf-med' : 'conf-low';

    return `
<div class="mem-entry" id="mentry-${escHtml(e.id)}" data-id="${escHtml(e.id)}">
  <div class="mem-entry-header">
    <span class="mem-source source-${escHtml(e.source)}">${escHtml(e.source)}</span>
    <span class="mem-conf ${confClass}">${conf}% conf</span>
    <span class="mem-date">${formatDate(e.created_at)}</span>
    ${e.edit_count > 0 ? `<span class="mem-edited">edited ${e.edit_count}x</span>` : ''}
    ${e.frozen ? '<span class="mem-frozen">❄ frozen</span>' : ''}
  </div>

  ${isEditing
    ? `<div class="mem-edit-row">
         <textarea class="mem-edit-input" data-id="${escHtml(e.id)}" rows="2">${escHtml(e.content)}</textarea>
         <div class="mem-edit-actions">
           <button class="mem-btn-save" data-id="${escHtml(e.id)}">Save</button>
           <button class="mem-btn-cancel" data-id="${escHtml(e.id)}">Cancel</button>
         </div>
       </div>`
    : `<div class="mem-content">${escHtml(e.content)}</div>`
  }

  ${!isEditing && !e.frozen ? `
  <div class="mem-entry-actions">
    <button class="mem-btn-edit" data-id="${escHtml(e.id)}">Edit</button>
    <button class="mem-btn-del"  data-id="${escHtml(e.id)}">Delete</button>
  </div>` : ''}
</div>`;
  }).join('');

  // Bind entry-level events
  list.querySelectorAll<HTMLButtonElement>('.mem-btn-edit').forEach(btn => {
    btn.addEventListener('click', () => {
      _editingId = btn.dataset.id!;
      renderEntries(root);
      // Focus textarea
      const ta = list.querySelector<HTMLTextAreaElement>(`.mem-edit-input[data-id="${_editingId}"]`);
      ta?.focus();
    });
  });

  list.querySelectorAll<HTMLButtonElement>('.mem-btn-save').forEach(btn => {
    btn.addEventListener('click', () => {
      const ta = list.querySelector<HTMLTextAreaElement>(`.mem-edit-input[data-id="${btn.dataset.id}"]`)!;
      saveEdit(root, btn.dataset.id!, ta.value.trim());
    });
  });

  list.querySelectorAll<HTMLButtonElement>('.mem-btn-cancel').forEach(btn => {
    btn.addEventListener('click', () => { _editingId = null; renderEntries(root); });
  });

  list.querySelectorAll<HTMLButtonElement>('.mem-btn-del').forEach(btn => {
    btn.addEventListener('click', () => deleteEntry(root, btn.dataset.id!));
  });
}

function renderAudit(root: HTMLElement): void {
  const list = root.querySelector<HTMLElement>('#mem-audit-list')!;
  if (!_auditLog.length) {
    list.innerHTML = '<span class="mem-muted">No audit events yet.</span>';
    return;
  }
  list.innerHTML = [..._auditLog].reverse().slice(0, 50).map(e => `
<div class="audit-entry">
  <span class="audit-action action-${escHtml(e.action)}">${escHtml(e.action)}</span>
  <span class="audit-id mem-muted">${escHtml(e.memory_id.slice(0, 8))}…</span>
  <span class="audit-time mem-muted">${formatDate(e.timestamp)}</span>
  ${e.detail ? `<span class="audit-detail mem-muted">${escHtml(e.detail)}</span>` : ''}
</div>`).join('');
}

function updateStats(root: HTMLElement): void {
  const active = _entries.filter(e => !e.deleted);
  root.querySelector('#stat-total')!.textContent = `${active.length} memor${active.length === 1 ? 'y' : 'ies'}`;
  root.querySelector('#stat-explicit')!.textContent = `${active.filter(e => e.source === 'explicit').length} explicit`;
  root.querySelector('#stat-inferred')!.textContent = `${active.filter(e => e.source === 'inferred').length} inferred`;
}

function renderOffline(root: HTMLElement): void {
  const list = root.querySelector<HTMLElement>('#mem-list')!;
  list.innerHTML = `
<div class="mem-offline">
  <span class="mem-warn">⚠ Memory backend offline</span>
  <span class="mem-muted">Start the server: <code>python core/server.py</code></span>
</div>`;
}

// ------------------------------------------------------------------ //
//  Toast                                                               //
// ------------------------------------------------------------------ //

function showToast(root: HTMLElement, msg: string, isError = false): void {
  const toast = document.createElement('div');
  toast.className = `mem-toast ${isError ? 'toast-error' : 'toast-ok'}`;
  toast.textContent = msg;
  root.querySelector('.gaia-memory')!.appendChild(toast);
  setTimeout(() => toast.remove(), 2800);
}

// ------------------------------------------------------------------ //
//  Helpers                                                             //
// ------------------------------------------------------------------ //

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString([], {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return iso; }
}

function escHtml(s: string): string {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

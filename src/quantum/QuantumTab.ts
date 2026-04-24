// QuantumTab — Phase 7 / task 7.3
// UI for the quantum-inspired branching explorer.
// Canon Ref: C42 — D2 Quantum

import './QuantumTab.css';
import { exploreBranches, BranchResult, BranchOutcome } from './QuantumInspiredOptimiser';
import { logInfo } from '../diagnostics';

export function mountQuantumTab(container: HTMLElement): void {
  container.innerHTML = `
    <div class="quantum-tab">
      <div class="quantum-header">
        <div class="quantum-title-row">
          <span class="quantum-sigil">⟨ψ⟩</span>
          <div>
            <h2 class="quantum-title">Branching Explorer</h2>
            <p class="quantum-subtitle">D2 — Quantum Superposition Reasoning</p>
          </div>
        </div>
      </div>

      <div class="quantum-input-panel">
        <label class="quantum-label" for="quantum-prompt">Prompt</label>
        <textarea
          id="quantum-prompt"
          class="quantum-textarea"
          placeholder="What decision or question should GAIA explore across multiple futures?"
          rows="3"
        ></textarea>
        <div class="quantum-controls">
          <div class="quantum-control-group">
            <label class="quantum-label" for="quantum-branches">Branches</label>
            <input id="quantum-branches" class="quantum-num-input" type="number" min="2" max="12" value="5" />
          </div>
          <div class="quantum-control-group">
            <label class="quantum-label" for="quantum-temp">Diversity</label>
            <input id="quantum-temp" class="quantum-num-input" type="number" min="0.1" max="2.0" step="0.1" value="0.9" />
          </div>
          <button id="quantum-explore-btn" class="quantum-btn-primary">Explore Futures</button>
        </div>
      </div>

      <div id="quantum-state" class="quantum-state-idle">
        <div class="quantum-idle-hint">
          <span class="quantum-idle-sigil">∿</span>
          <p>Enter a prompt above to open the branching explorer.<br>GAIA will hold N futures simultaneously, then collapse to the most coherent one.</p>
        </div>
      </div>
    </div>
  `;

  const promptEl    = container.querySelector<HTMLTextAreaElement>('#quantum-prompt')!;
  const branchesEl  = container.querySelector<HTMLInputElement>('#quantum-branches')!;
  const tempEl      = container.querySelector<HTMLInputElement>('#quantum-temp')!;
  const exploreBtn  = container.querySelector<HTMLButtonElement>('#quantum-explore-btn')!;
  const stateEl     = container.querySelector<HTMLElement>('#quantum-state')!;

  exploreBtn.addEventListener('click', async () => {
    const prompt = promptEl.value.trim();
    if (!prompt) { promptEl.focus(); return; }

    exploreBtn.disabled = true;
    exploreBtn.textContent = 'Collapsing wave function…';
    stateEl.className = 'quantum-state-loading';
    stateEl.innerHTML = `
      <div class="quantum-loading">
        <div class="quantum-orb-ring"></div>
        <p>GAIA is holding ${branchesEl.value} futures open…</p>
      </div>
    `;

    try {
      const result = await exploreBranches({
        prompt,
        n_branches: Number(branchesEl.value),
        temperature: Number(tempEl.value),
      });
      renderResult(stateEl, result);
      logInfo('quantum', 'Branch result rendered');
    } catch (e: any) {
      stateEl.className = 'quantum-state-error';
      stateEl.innerHTML = `<p class="quantum-error">⚠ ${e.message}</p>`;
    } finally {
      exploreBtn.disabled = false;
      exploreBtn.textContent = 'Explore Futures';
    }
  });
}

function renderResult(container: HTMLElement, result: BranchResult): void {
  container.className = 'quantum-state-result';

  const backendLabel: Record<string, string> = {
    ibm: '⚛ IBM Quantum',
    aer: '∿ Aer Simulator',
    classical: '◈ Classical',
  };

  container.innerHTML = `
    <div class="quantum-result">
      <div class="quantum-result-meta">
        <span class="quantum-backend-badge">${backendLabel[result.backend] ?? result.backend}</span>
        <span class="quantum-duration">${result.duration_ms}ms</span>
        <span class="quantum-branch-count">${result.branches.length} branches explored</span>
      </div>

      <div class="quantum-collapsed-card">
        <div class="quantum-collapsed-label">⟩ Collapsed State — Most Coherent Future</div>
        <div class="quantum-collapsed-summary">${result.collapsed.summary}</div>
        <div class="quantum-collapsed-reasoning">${result.collapsed.reasoning}</div>
        <div class="quantum-collapsed-meta">
          <span class="quantum-prob">P = ${(result.collapsed.probability * 100).toFixed(1)}%</span>
          <span class="quantum-archetype">◈ ${result.collapsed.archetype_resonance}</span>
        </div>
      </div>

      <div class="quantum-branches-label">All Branches</div>
      <div class="quantum-branches">
        ${result.branches.map((b, i) => renderBranch(b, i, result.collapsed.id)).join('')}
      </div>
    </div>
  `;
}

function renderBranch(b: BranchOutcome, index: number, collapsedId: string): string {
  const isCollapsed = b.id === collapsedId;
  const pct = (b.probability * 100).toFixed(1);
  const tags = b.tags.map(t => `<span class="quantum-tag">${t}</span>`).join('');

  return `
    <div class="quantum-branch ${isCollapsed ? 'quantum-branch--collapsed' : ''}">
      <div class="quantum-branch-header">
        <span class="quantum-branch-index">F${index + 1}</span>
        <span class="quantum-branch-summary">${b.summary}</span>
        <div class="quantum-branch-prob-bar" style="--pct:${pct}%">
          <span>${pct}%</span>
        </div>
      </div>
      <div class="quantum-branch-reasoning">${b.reasoning}</div>
      <div class="quantum-branch-footer">
        ${tags}
        <span class="quantum-archetype-sm">◈ ${b.archetype_resonance}</span>
      </div>
    </div>
  `;
}

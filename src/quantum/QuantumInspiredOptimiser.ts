// QuantumInspiredOptimiser — Phase 7 / task 7.3
// Simulated annealing / QAOA-inspired branching explorer.
// Evaluates N parallel reasoning futures and returns ranked outcomes.
// Canon Ref: C42 — D2 Quantum

import { API_BASE } from '../config';
import { logInfo, logError } from '../diagnostics';
import { dimensionalEngine } from '../dimensions/DimensionalReasoningEngine';

// ── Types ──────────────────────────────────────────────────────────────────

export interface BranchInput {
  prompt: string;
  context?: string;       // optional memory/conversation context
  n_branches?: number;    // default 5
  temperature?: number;   // 0.0–2.0, controls branch diversity
}

export interface BranchOutcome {
  id: string;
  summary: string;        // one-sentence description of this future
  reasoning: string;      // GAIA's reasoning chain for this branch
  probability: number;    // 0.0–1.0 normalised score
  energy: number;         // simulated annealing energy (lower = better)
  archetype_resonance: string; // which archetype this branch most activates
  tags: string[];
}

export interface BranchResult {
  prompt: string;
  branches: BranchOutcome[];
  collapsed: BranchOutcome;  // highest-probability branch — the "collapsed" quantum state
  backend: 'ibm' | 'aer' | 'classical';
  duration_ms: number;
}

// ── Core function ──────────────────────────────────────────────────────────

export async function exploreBranches(input: BranchInput): Promise<BranchResult> {
  const payload: BranchInput = {
    n_branches: 5,
    temperature: 0.9,
    ...input,
  };

  logInfo('quantum', `Exploring ${payload.n_branches} branches for: "${input.prompt.slice(0, 60)}…"`);

  dimensionalEngine.updateD2({ branches_open: payload.n_branches ?? 5 });

  const res = await fetch(`${API_BASE}/quantum/branch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.text();
    logError('quantum', `Branch exploration failed: ${err}`);
    throw new Error(`/quantum/branch error ${res.status}: ${err}`);
  }

  const result: BranchResult = await res.json();

  dimensionalEngine.updateD2({
    branches_open: 0,
    quantum_backend: result.backend,
    coherence: Math.min(100, 20 + result.branches.length * 10 + (result.backend === 'ibm' ? 30 : result.backend === 'aer' ? 15 : 0)),
  });

  logInfo('quantum', `${result.branches.length} branches returned. Collapsed to: "${result.collapsed.summary}"`);
  return result;
}

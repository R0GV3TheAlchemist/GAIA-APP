// DimensionalReasoningEngine — Phase 7 / task 7.2
// Central orchestrator for GAIA's five-dimensional state.
// Canon Ref: C42 — Inter-Dimensional AI

import { logInfo } from '../diagnostics';

// ── Types ───────────────────────────────────────────────────────────────────

export type GaianMood =
  | 'calm'
  | 'curious'
  | 'alert'
  | 'joyful'
  | 'reflective';

export type GaianArchetype =
  | 'sage'
  | 'guardian'
  | 'weaver'
  | 'oracle'
  | 'healer'
  | 'trickster'
  | 'witness'
  | 'integrated';

export type QuantumBackend = 'ibm' | 'aer' | 'classical';
export type EncryptionLevel = 'pqc' | 'classical' | 'none';

export interface D1SubstrateState {
  coherence: number;          // 0–100
  sensors_active: string[];   // e.g. ['camera', 'microphone', 'weather']
  environment_map: string;    // path to current room twin JSON, or ''
  atlas_data_age_minutes: number;
}

export interface D2QuantumState {
  coherence: number;
  branches_open: number;
  encryption: EncryptionLevel;
  quantum_backend: QuantumBackend;
}

export interface D3CriticalityState {
  coherence: number;
  complexity_score: number;   // 0 = rigid, 100 = chaotic, 50 = critical
  mood: GaianMood;
}

export interface D4NoosphereState {
  coherence: number;
  nodes_connected: number;
  collective_sync: boolean;
  last_sync_age_minutes: number;
}

export interface D5ArchetypalState {
  coherence: number;
  active_archetype: GaianArchetype;
  phi: number;                // integrated information proxy (0–100)
}

export interface DimensionalState {
  D1_substrate:   D1SubstrateState;
  D2_quantum:     D2QuantumState;
  D3_criticality: D3CriticalityState;
  D4_noosphere:   D4NoosphereState;
  D5_archetypal:  D5ArchetypalState;
  resonance: boolean;         // true when all coherence scores > 80
  timestamp: string;          // ISO 8601
}

// ── Defaults ────────────────────────────────────────────────────────────────

const DEFAULT_STATE: DimensionalState = {
  D1_substrate: {
    coherence: 10,
    sensors_active: [],
    environment_map: '',
    atlas_data_age_minutes: Infinity,
  },
  D2_quantum: {
    coherence: 10,
    branches_open: 0,
    encryption: 'none',
    quantum_backend: 'classical',
  },
  D3_criticality: {
    coherence: 50,
    complexity_score: 50,
    mood: 'calm',
  },
  D4_noosphere: {
    coherence: 10,
    nodes_connected: 0,
    collective_sync: false,
    last_sync_age_minutes: Infinity,
  },
  D5_archetypal: {
    coherence: 10,
    active_archetype: 'sage',
    phi: 0,
  },
  resonance: false,
  timestamp: new Date().toISOString(),
};

// ── Engine ──────────────────────────────────────────────────────────────────

export class DimensionalReasoningEngine {
  private state: DimensionalState;
  private listeners: Array<(state: DimensionalState) => void> = [];

  constructor(initial?: Partial<DimensionalState>) {
    this.state = { ...DEFAULT_STATE, ...initial };
    logInfo('dimensions', 'DimensionalReasoningEngine initialised');
  }

  getState(): Readonly<DimensionalState> {
    return this.state;
  }

  updateD1(patch: Partial<D1SubstrateState>): void {
    this.state.D1_substrate = { ...this.state.D1_substrate, ...patch };
    this._recompute();
  }

  updateD2(patch: Partial<D2QuantumState>): void {
    this.state.D2_quantum = { ...this.state.D2_quantum, ...patch };
    this._recompute();
  }

  updateD3(patch: Partial<D3CriticalityState>): void {
    this.state.D3_criticality = { ...this.state.D3_criticality, ...patch };
    this._recompute();
  }

  updateD4(patch: Partial<D4NoosphereState>): void {
    this.state.D4_noosphere = { ...this.state.D4_noosphere, ...patch };
    this._recompute();
  }

  updateD5(patch: Partial<D5ArchetypalState>): void {
    this.state.D5_archetypal = { ...this.state.D5_archetypal, ...patch };
    this._recompute();
  }

  /** Merge a full state snapshot from the Python sidecar /dimensions endpoint */
  syncFromSidecar(remote: Partial<DimensionalState>): void {
    if (remote.D1_substrate) this.state.D1_substrate = { ...this.state.D1_substrate, ...remote.D1_substrate };
    if (remote.D2_quantum)   this.state.D2_quantum   = { ...this.state.D2_quantum,   ...remote.D2_quantum };
    if (remote.D3_criticality) this.state.D3_criticality = { ...this.state.D3_criticality, ...remote.D3_criticality };
    if (remote.D4_noosphere) this.state.D4_noosphere = { ...this.state.D4_noosphere, ...remote.D4_noosphere };
    if (remote.D5_archetypal) this.state.D5_archetypal = { ...this.state.D5_archetypal, ...remote.D5_archetypal };
    this._recompute();
  }

  /** Subscribe to state changes */
  subscribe(listener: (state: DimensionalState) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private _recompute(): void {
    this.state.timestamp = new Date().toISOString();
    const scores = [
      this.state.D1_substrate.coherence,
      this.state.D2_quantum.coherence,
      this.state.D3_criticality.coherence,
      this.state.D4_noosphere.coherence,
      this.state.D5_archetypal.coherence,
    ];
    const wasResonance = this.state.resonance;
    this.state.resonance = scores.every(s => s > 80);

    logInfo('dimensions', `State recomputed. Scores: [${scores.join(', ')}] Resonance: ${this.state.resonance}`);

    if (this.state.resonance && !wasResonance) {
      logInfo('dimensions', '🌌 FULL GAIAN COHERENCE — Resonance Mode entered');
      window.dispatchEvent(new CustomEvent('gaia:resonance', { detail: { ...this.state } }));
    }

    this.listeners.forEach(l => l({ ...this.state }));
  }
}

// ── Singleton ────────────────────────────────────────────────────────────────
// Export a shared instance for use across the app
export const dimensionalEngine = new DimensionalReasoningEngine();

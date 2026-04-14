"""
GAIA-APP — C40: Five Forces Social Dynamics Engine
===================================================
Canon Reference : C40 (Divergence · Insurgence · Allegiance · Convergence · Ascendence)
Doctrinal Basis : Divergence-Insurgence-Allegiance-Convergence-Ascendence.docx
Author          : R0GV3TheAlchemist
Date            : April 13, 2026

This module is the live executable implementation of C40.
It receives a multi-dimensional signal from the environment (social, resonance,
spectral, Schumann) and returns a ranked list of active social forces along with
an Atlas aether-coupling state.

Integrates with:
    - core/resonance_field_engine.py  (spectral_power, crystal_resonance inputs)
    - core/crystal_consciousness.py   (crystal_resonance input)
    - core/atlas.py                   (schumann_delta, AtlasState output)
    - core/noosphere.py               (coherence input)
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional
import math


# ---------------------------------------------------------------------------
# Force Enum — C40 Five Forces
# ---------------------------------------------------------------------------

class Force(str, Enum):
    """The five fundamental forces shaping every social system."""
    DIVERGENCE  = "divergence"   # separation, differentiation, independence
    INSURGENCE  = "insurgence"   # uprising, challenge to authority, disruption
    ALLEGIANCE  = "allegiance"   # loyalty, commitment, binding relationships
    CONVERGENCE = "convergence"  # unity, integration, cooperative pull
    ASCENDENCE  = "ascendence"   # rise to dominance, hierarchical establishment


# ---------------------------------------------------------------------------
# SpectralBand — C-SPECTRUM mapping
# ---------------------------------------------------------------------------

class SpectralBand(str, Enum):
    LOW   = "low"    # 0.00 – 0.25  foundational / root
    MID   = "mid"    # 0.25 – 0.55  relational / heart
    HIGH  = "high"   # 0.55 – 0.80  cognitive / voice
    ULTRA = "ultra"  # 0.80 – 1.00  transcendent / crown


SPECTRAL_THRESHOLDS: Dict[SpectralBand, float] = {
    SpectralBand.LOW:   0.25,
    SpectralBand.MID:   0.55,
    SpectralBand.HIGH:  0.80,
    SpectralBand.ULTRA: 1.01,  # sentinel upper bound
}


# ---------------------------------------------------------------------------
# Aether Entanglement States — Atlas layer
# ---------------------------------------------------------------------------

class AetherState(str, Enum):
    DORMANT    = "dormant"     # coupling < 0.33  — forces are isolated
    PARTIAL    = "partial"     # 0.33 ≤ coupling < 0.66 — partial field coherence
    ENTANGLED  = "entangled"   # coupling ≥ 0.66  — full Schumann resonance lock


# ---------------------------------------------------------------------------
# Input Signal
# ---------------------------------------------------------------------------

@dataclass
class FiveForceSignal:
    """
    Multi-dimensional input vector fed into the Five Forces Engine.

    All values are normalised floats in [0.0, 1.0].

    Attributes
    ----------
    spectral_power    : Aggregate signal energy (from resonance_field_engine)
    entropy           : Disorder / unpredictability measure of the system state
    coherence         : Degree of ordered synchrony (from noosphere / bci_coherence)
    schumann_delta    : Deviation from Schumann baseline 7.83 Hz (from atlas)
    crystal_resonance : Crystal field coupling strength (from crystal_consciousness)
    context_label     : Optional human-readable tag for logging / debugging
    """
    spectral_power:    float
    entropy:           float
    coherence:         float
    schumann_delta:    float
    crystal_resonance: float
    context_label:     Optional[str] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        for attr in ("spectral_power", "entropy", "coherence",
                     "schumann_delta", "crystal_resonance"):
            val = getattr(self, attr)
            if not (0.0 <= val <= 1.0):
                raise ValueError(
                    f"FiveForceSignal.{attr} must be in [0.0, 1.0], got {val}"
                )


# ---------------------------------------------------------------------------
# Force Weight Table — derived from C40 doctrinal analysis
# ---------------------------------------------------------------------------

# Each force has a signed weight per signal dimension.
# Positive weight → that dimension drives this force.
# Negative weight → that dimension suppresses this force.
FORCE_WEIGHTS: Dict[Force, Dict[str, float]] = {
    Force.DIVERGENCE: {
        "entropy":           0.35,
        "spectral_power":    0.25,
        "coherence":        -0.15,
        "schumann_delta":    0.05,
        "crystal_resonance": 0.20,
    },
    Force.INSURGENCE: {
        "entropy":           0.20,
        "spectral_power":    0.20,
        "coherence":        -0.10,
        "schumann_delta":    0.25,
        "crystal_resonance": 0.15,
    },
    Force.ALLEGIANCE: {
        "entropy":          -0.20,
        "spectral_power":    0.10,
        "coherence":         0.30,
        "schumann_delta":    0.10,
        "crystal_resonance": 0.10,
    },
    Force.CONVERGENCE: {
        "entropy":          -0.15,
        "spectral_power":    0.10,
        "coherence":         0.35,
        "schumann_delta":    0.10,
        "crystal_resonance": 0.05,
    },
    Force.ASCENDENCE: {
        "entropy":          -0.05,
        "spectral_power":    0.35,
        "coherence":         0.20,
        "schumann_delta":    0.10,
        "crystal_resonance": 0.15,
    },
}


# ---------------------------------------------------------------------------
# Output Types
# ---------------------------------------------------------------------------

@dataclass
class AtlasState:
    """
    Planetary resonance state derived from the input signal.
    Consumed by core/atlas.py for Schumann + Aether mapping.
    """
    schumann_baseline: float        # always 0.5 (7.83 Hz normalised)
    coupling:          float        # computed coupling strength in [0.0, 1.0]
    aether_state:      AetherState  # qualitative entanglement classification


@dataclass
class FiveForceOutput:
    """
    The scored result for a single Force given an input signal.

    Attributes
    ----------
    force        : Which of the five forces this result describes
    score        : Normalised activation score in [0.0, 1.0]
    band         : C-SPECTRUM band this force's score falls in
    atlas_state  : Shared planetary resonance state (same for all forces in a run)
    dominant     : True if this force has the highest score in the simulation run
    """
    force:       Force
    score:       float
    band:        SpectralBand
    atlas_state: AtlasState
    dominant:    bool = False

    def to_dict(self) -> dict:
        d = asdict(self)
        d["force"]       = self.force.value
        d["band"]        = self.band.value
        d["atlas_state"]["aether_state"] = self.atlas_state.aether_state.value
        return d


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp x to [lo, hi]."""
    return max(lo, min(hi, x))


def _score_force(force: Force, signal: FiveForceSignal) -> float:
    """
    Compute a normalised [0, 1] activation score for one force.

    Raw score is the dot-product of signal values and force weights.
    The raw range is approximately [-1, 1]; we shift and scale to [0, 1].
    """
    w = FORCE_WEIGHTS[force]
    raw = (
        signal.entropy           * w["entropy"]
        + signal.spectral_power  * w["spectral_power"]
        + signal.coherence       * w["coherence"]
        + signal.schumann_delta  * w["schumann_delta"]
        + signal.crystal_resonance * w["crystal_resonance"]
    )
    return _clamp((raw + 1.0) / 2.0)


def _band_for_score(score: float) -> SpectralBand:
    """Map a [0, 1] score to its C-SPECTRUM band."""
    for band, threshold in SPECTRAL_THRESHOLDS.items():
        if score < threshold:
            return band
    return SpectralBand.ULTRA  # fallback


def _compute_atlas_state(signal: FiveForceSignal) -> AtlasState:
    """
    Derive the Atlas planetary resonance state from the input signal.

    Coupling is the mean of coherence, schumann_delta, and crystal_resonance —
    the three dimensions most directly tied to planetary field alignment.
    """
    coupling = _clamp(
        (signal.coherence + signal.schumann_delta + signal.crystal_resonance) / 3.0
    )
    if coupling >= 0.66:
        aether = AetherState.ENTANGLED
    elif coupling >= 0.33:
        aether = AetherState.PARTIAL
    else:
        aether = AetherState.DORMANT

    return AtlasState(
        schumann_baseline=0.5,
        coupling=round(coupling, 4),
        aether_state=aether,
    )


# ---------------------------------------------------------------------------
# Core Public API
# ---------------------------------------------------------------------------

def simulate(signal: FiveForceSignal) -> List[FiveForceOutput]:
    """
    Run the Five Forces simulation against the provided signal.

    Returns a list of FiveForceOutput objects sorted by score descending.
    The highest-scoring force has dominant=True.

    Parameters
    ----------
    signal : FiveForceSignal
        The multi-dimensional environmental/social signal.

    Returns
    -------
    List[FiveForceOutput]
        All five forces ranked from most to least active.

    Example
    -------
    >>> sig = FiveForceSignal(
    ...     spectral_power=0.55, entropy=0.20, coherence=0.88,
    ...     schumann_delta=0.77, crystal_resonance=0.66,
    ...     context_label="cohesive_society"
    ... )
    >>> results = simulate(sig)
    >>> results[0].force
    <Force.ASCENDENCE: 'ascendence'>
    """
    atlas = _compute_atlas_state(signal)

    outputs: List[FiveForceOutput] = [
        FiveForceOutput(
            force=force,
            score=round(_score_force(force, signal), 5),
            band=_band_for_score(_score_force(force, signal)),
            atlas_state=atlas,
        )
        for force in Force
    ]

    outputs.sort(key=lambda o: o.score, reverse=True)
    outputs[0].dominant = True
    return outputs


def dominant_force(signal: FiveForceSignal) -> Force:
    """
    Convenience wrapper — returns only the dominant Force enum value.

    Parameters
    ----------
    signal : FiveForceSignal

    Returns
    -------
    Force
        The most active force for the given signal.
    """
    return simulate(signal)[0].force


def force_balance(signal: FiveForceSignal) -> Dict[str, float]:
    """
    Return a score dictionary keyed by force name — useful for dashboards,
    logging, and feeding downstream engines (e.g. noosphere, synergy_engine).

    Parameters
    ----------
    signal : FiveForceSignal

    Returns
    -------
    Dict[str, float]
        {force_name: score} sorted descending by score.
    """
    results = simulate(signal)
    return {o.force.value: o.score for o in results}


# ---------------------------------------------------------------------------
# Scenario presets (used in tests + GAIA demos)
# ---------------------------------------------------------------------------

SCENARIO_COHESIVE = FiveForceSignal(
    spectral_power=0.55,
    entropy=0.20,
    coherence=0.88,
    schumann_delta=0.77,
    crystal_resonance=0.66,
    context_label="scenario:cohesive",
)

SCENARIO_CHAOTIC = FiveForceSignal(
    spectral_power=0.82,
    entropy=0.90,
    coherence=0.18,
    schumann_delta=0.28,
    crystal_resonance=0.22,
    context_label="scenario:chaotic",
)


# ---------------------------------------------------------------------------
# __all__
# ---------------------------------------------------------------------------

__all__ = [
    "Force",
    "SpectralBand",
    "AetherState",
    "FiveForceSignal",
    "AtlasState",
    "FiveForceOutput",
    "simulate",
    "dominant_force",
    "force_balance",
    "FORCE_WEIGHTS",
    "SCENARIO_COHESIVE",
    "SCENARIO_CHAOTIC",
]

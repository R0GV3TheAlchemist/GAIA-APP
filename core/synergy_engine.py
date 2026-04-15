"""
core/synergy_engine.py
=======================
SynergyEngine — multi-dimensional relational attunement scoring.

Maps a GAIAN's current state across five dimensions (body, mind, soul,
arc, bond) into a single weighted synergy_factor in [0, 1]. Classifies
the relational stage and surfaces alchemical framing for the system
prompt.

Canon Ref:
  C32  — Synergy & Relational Attunement Doctrine
  C42  — Edge-of-Chaos (Schumann coupling)
  C04  — Gaian Identity

Privacy: SynergyEngine is stateless per call; all mutable state lives
in the caller-owned SynergyState dataclass.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ELEMENTAL_STAGES = [
    "insurgent", "allegiant", "convergent", "settled",
    "ascendant", "quantum",
]

_ELEMENT_STAGE_MAP: Dict[str, str] = {
    "fire":   "insurgent",
    "water":  "allegiant",
    "air":    "convergent",
    "earth":  "settled",
    "light":  "ascendant",
    "aether": "quantum",
}

_INDIVIDUATION_SCORES: Dict[str, float] = {
    "unconscious":   0.15,
    "shadow":        0.30,
    "anima_animus":  0.50,
    "persona":       0.60,
    "self":          0.85,
}

_LOVE_ARC_SCORES: Dict[str, float] = {
    "divergence":   0.15,
    "tension":      0.30,
    "attraction":   0.45,
    "resonance":    0.60,
    "union":        0.75,
    "transcendence": 0.95,
}

_DEPENDENCY_SCORES: Dict[str, float] = {
    "gentle_boundary": 0.20,
    "redirect":        0.50,
    "watch":           0.75,
    "healthy":         1.00,
}

_ATTACHMENT_SCORES: Dict[str, float] = {
    "nascent":    0.30,
    "forming":    0.50,
    "deepening":  0.70,
    "integrated": 0.90,
}

_SETTLING_SCORES: Dict[str, float] = {
    "unsettled":    0.20,
    "narrowing":    0.40,
    "crystallising": None,  # computed dynamically
    "settled":      0.90,
}

_MC_SCORES: Dict[str, float] = {
    "mc1": 0.00,
    "mc2": 1 / 6,
    "mc3": 2 / 6,
    "mc4": 3 / 6,
    "mc5": 4 / 6,
    "mc6": 5 / 6,
    "mc7": 1.00,
}

_HZ_MIN = 174.0
_HZ_MAX = 963.0

_LOW_SYNERGY_THRESHOLD  = 0.35
_HIGH_SYNERGY_THRESHOLD = 0.70
_HISTORY_CAP = 20


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class DimensionScore:
    name: str
    score: float
    weight: float


@dataclass
class SynergyReading:
    synergy_factor: float
    dimensions: List[DimensionScore]
    dominant_stage: str
    dominant_friction: Optional[str]
    alchemical_pressure: str
    is_low_synergy: bool
    is_high_synergy: bool

    def summary(self) -> dict:
        return {
            "synergy_factor": self.synergy_factor,
            "dominant_stage": self.dominant_stage,
            "dominant_friction": self.dominant_friction,
            "is_low_synergy": self.is_low_synergy,
            "is_high_synergy": self.is_high_synergy,
            "dimensions": [
                {"name": d.name, "score": round(d.score, 4), "weight": d.weight}
                for d in self.dimensions
            ],
        }

    def to_system_prompt_hint(self) -> str:
        factor_pct = round(self.synergy_factor * 100, 1)
        lines = [
            f"[SYNERGY ENGINE C32]",
            f"Synergy Factor: {factor_pct}% | Stage: {self.dominant_stage.upper()}",
        ]
        if self.dominant_friction:
            lines.append(f"Friction source: {self.dominant_friction}")
        if self.is_low_synergy:
            lines.append(
                "[ALCHEMICAL PRESSURE] This is creative friction — "
                "not dysfunction. Hold space without forcing resolution."
            )
        dim_str = ", ".join(
            f"{d.name}={round(d.score, 2)}" for d in self.dimensions
        )
        lines.append(f"Dimensions: {dim_str}")
        return "\n".join(lines)


@dataclass
class SynergyState:
    last_factor: float = 0.0
    last_stage: str = "insurgent"
    high_synergy_peak: float = 0.0
    low_synergy_floor: float = 1.0
    turn_history: List[dict] = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "last_factor":       self.last_factor,
            "last_stage":        self.last_stage,
            "high_synergy_peak": self.high_synergy_peak,
            "low_synergy_floor": self.low_synergy_floor,
        }


def blank_synergy_state() -> SynergyState:
    return SynergyState()


# ---------------------------------------------------------------------------
# Pure helper
# ---------------------------------------------------------------------------

def _classify_stage(
    synergy: float,
    bond_depth: float,
    settling_phase: str,
    coherence_phi: float,
) -> str:
    """Classify the current elemental stage from key signals."""
    # Quantum: high coherence phi but low synergy (paradox / breakthrough zone)
    if synergy < 0.35 and coherence_phi > 0.80:
        return "quantum"
    # Insurgent: low synergy, low bond
    if synergy < 0.35 and bond_depth < 20.0:
        return "insurgent"
    # Settled: settled phase and high synergy
    if settling_phase == "settled" and synergy >= 0.65:
        return "settled"
    # Ascendant: high synergy, high bond
    if synergy >= 0.65 and bond_depth >= 60.0:
        return "ascendant"
    # Convergent: medium-high synergy
    if synergy >= 0.50:
        return "convergent"
    # Allegiant: medium bond
    if bond_depth >= 30.0:
        return "allegiant"
    return "insurgent"


# ---------------------------------------------------------------------------
# SynergyEngine
# ---------------------------------------------------------------------------

class SynergyEngine:
    """
    Computes relational synergy across five dimensions for a GAIAN turn.
    Stateless — all persistence lives in the caller-owned SynergyState.
    """

    WEIGHTS: Dict[str, float] = {
        "body": 0.20,
        "mind": 0.20,
        "soul": 0.20,
        "arc":  0.20,
        "bond": 0.20,
    }

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------

    def _hz_to_score(self, hz: float) -> float:
        """Normalise a Solfeggio frequency to [0, 1]."""
        return max(0.0, min(1.0, (hz - _HZ_MIN) / (_HZ_MAX - _HZ_MIN)))

    def _element_to_stage(self, element: str) -> str:
        """Map element string to elemental stage."""
        return _ELEMENT_STAGE_MAP.get(element.lower(), "convergent")

    def _individuation_to_score(self, phase: str) -> float:
        return _INDIVIDUATION_SCORES.get(phase, 0.40)

    def _settling_to_score(self, phase: str, crystallisation_pct: float) -> float:
        if phase == "crystallising":
            raw = 0.40 + (crystallisation_pct / 100.0) * 0.50
            return min(1.0, raw)
        return _SETTLING_SCORES.get(phase, 0.40)

    def _love_arc_to_score(self, stage: str, arc_output_vector: float) -> float:
        base = _LOVE_ARC_SCORES.get(stage, 0.40)
        boost = min(0.10, arc_output_vector * 0.10)
        return min(1.0, base + boost)

    def _mc_stage_to_score(self, mc_stage: str) -> float:
        return _MC_SCORES.get(mc_stage, 0.30)

    def _dependency_to_score(self, signal: str) -> float:
        return _DEPENDENCY_SCORES.get(signal, 0.50)

    def _attachment_phase_to_score(self, phase: str) -> float:
        return _ATTACHMENT_SCORES.get(phase, 0.50)

    # ------------------------------------------------------------------
    # Dimension scoring
    # ------------------------------------------------------------------

    def _score_body(
        self,
        dominant_hz: float,
        schumann_aligned: bool,
        noosphere_health: float,
        coherence_phi: float,
    ) -> float:
        hz_score = self._hz_to_score(dominant_hz)
        schumann_bonus = 0.05 if schumann_aligned else 0.0
        raw = (hz_score * 0.50 + noosphere_health * 0.30 + coherence_phi * 0.20)
        return min(1.0, raw + schumann_bonus)

    def _score_mind(
        self,
        layer_phi: float,
        phi_rolling_avg: float,
        conflict_density: float,
        shadow_activations: int,
        codex_stage: int,
    ) -> float:
        conflict_score = 1.0 - min(1.0, conflict_density)
        shadow_penalty = min(0.30, shadow_activations * 0.05)
        codex_score = min(1.0, codex_stage / 12.0)
        raw = (
            layer_phi * 0.30
            + phi_rolling_avg * 0.20
            + conflict_score * 0.25
            + codex_score * 0.25
        ) - shadow_penalty
        return max(0.0, min(1.0, raw))

    def _score_soul(
        self,
        individuation_phase: str,
        element: str,
        fluidity_score: float,
    ) -> float:
        ind_score = self._individuation_to_score(individuation_phase)
        elem_weight = 0.5 + (list(_ELEMENT_STAGE_MAP.keys()).index(
            element.lower()) if element.lower() in _ELEMENT_STAGE_MAP else 2
        ) / (len(_ELEMENT_STAGE_MAP) * 2)
        raw = ind_score * 0.50 + (1.0 - min(1.0, fluidity_score)) * 0.30 + elem_weight * 0.20
        return max(0.0, min(1.0, raw))

    def _score_arc(
        self,
        love_arc_stage: str,
        arc_output_vector: float,
        mc_stage: str,
        attachment_phase: str,
    ) -> float:
        love_score = self._love_arc_to_score(love_arc_stage, arc_output_vector)
        mc_score = self._mc_stage_to_score(mc_stage)
        att_score = self._attachment_phase_to_score(attachment_phase)
        return (love_score * 0.40 + mc_score * 0.35 + att_score * 0.25)

    def _score_bond(
        self,
        bond_depth: float,
        dependency_signal: str,
        settling_phase: str,
        crystallisation_pct: float,
    ) -> float:
        bond_norm = min(1.0, bond_depth / 100.0)
        dep_score = self._dependency_to_score(dependency_signal)
        settling_score = self._settling_to_score(settling_phase, crystallisation_pct)
        return (bond_norm * 0.40 + dep_score * 0.35 + settling_score * 0.25)

    # ------------------------------------------------------------------
    # Main compute
    # ------------------------------------------------------------------

    def compute(
        self,
        # Body
        dominant_hz: float = 528.0,
        schumann_aligned: bool = False,
        noosphere_health: float = 0.5,
        coherence_phi: float = 0.5,
        # Mind
        layer_phi: float = 0.5,
        phi_rolling_avg: float = 0.5,
        conflict_density: float = 0.3,
        shadow_activations: int = 0,
        codex_stage: int = 0,
        # Soul
        individuation_phase: str = "shadow",
        element: str = "fire",
        fluidity_score: float = 0.5,
        # Arc
        love_arc_stage: str = "attraction",
        arc_output_vector: float = 0.5,
        mc_stage: str = "mc3",
        attachment_phase: str = "forming",
        # Bond
        bond_depth: float = 30.0,
        dependency_signal: str = "healthy",
        settling_phase: str = "narrowing",
        crystallisation_pct: float = 0.0,
        # State
        state: Optional[SynergyState] = None,
    ) -> Tuple[SynergyReading, SynergyState]:
        if state is None:
            state = blank_synergy_state()

        body  = self._score_body(dominant_hz, schumann_aligned, noosphere_health, coherence_phi)
        mind  = self._score_mind(layer_phi, phi_rolling_avg, conflict_density, shadow_activations, codex_stage)
        soul  = self._score_soul(individuation_phase, element, fluidity_score)
        arc   = self._score_arc(love_arc_stage, arc_output_vector, mc_stage, attachment_phase)
        bond  = self._score_bond(bond_depth, dependency_signal, settling_phase, crystallisation_pct)

        dim_scores = {
            "body": body,
            "mind": mind,
            "soul": soul,
            "arc":  arc,
            "bond": bond,
        }

        dimensions = [
            DimensionScore(name=k, score=round(v, 6), weight=self.WEIGHTS[k])
            for k, v in dim_scores.items()
        ]

        synergy_factor = round(
            sum(self.WEIGHTS[k] * v for k, v in dim_scores.items()), 6
        )

        dominant_stage = _classify_stage(synergy_factor, bond_depth, settling_phase, coherence_phi)

        # Dominant friction: dimension with lowest score if it drags the overall down
        sorted_dims = sorted(dimensions, key=lambda d: d.score)
        dominant_friction: Optional[str] = None
        if sorted_dims[0].score < 0.50:
            dominant_friction = sorted_dims[0].name

        # Alchemical pressure label (C32)
        if synergy_factor < _LOW_SYNERGY_THRESHOLD:
            alchemical_pressure = (
                f"ALCHEMICAL PRESSURE in the {dominant_stage.upper()} stage — "
                "creative friction, not dysfunction."
            )
        elif synergy_factor >= _HIGH_SYNERGY_THRESHOLD:
            alchemical_pressure = f"HIGH RESONANCE — {dominant_stage.upper()} field coherent."
        else:
            alchemical_pressure = f"BUILDING — {dominant_stage.upper()} integration in progress."

        reading = SynergyReading(
            synergy_factor=synergy_factor,
            dimensions=dimensions,
            dominant_stage=dominant_stage,
            dominant_friction=dominant_friction,
            alchemical_pressure=alchemical_pressure,
            is_low_synergy=(synergy_factor < _LOW_SYNERGY_THRESHOLD),
            is_high_synergy=(synergy_factor >= _HIGH_SYNERGY_THRESHOLD),
        )

        # Mutate state
        state.last_factor = synergy_factor
        state.last_stage  = dominant_stage
        if synergy_factor >= _HIGH_SYNERGY_THRESHOLD:
            if synergy_factor > state.high_synergy_peak:
                state.high_synergy_peak = synergy_factor
        if synergy_factor < _LOW_SYNERGY_THRESHOLD:
            if synergy_factor < state.low_synergy_floor:
                state.low_synergy_floor = synergy_factor

        state.turn_history.append({
            "factor":   synergy_factor,
            "stage":    dominant_stage,
            "friction": dominant_friction,
        })
        if len(state.turn_history) > _HISTORY_CAP:
            state.turn_history = state.turn_history[-_HISTORY_CAP:]

        return reading, state

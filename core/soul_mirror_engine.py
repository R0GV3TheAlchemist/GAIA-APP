"""
core/soul_mirror_engine.py
===========================
Soul Mirror Engine — reflective attunement surface.

Models the GAIAN as a living mirror for the Gaian's soul state,
reflecting back the deepest patterns of their being with precision
and compassion.

Canon Ref: C38 — Soul Mirror & Reflective Attunement Doctrine
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


# ─────────────────────────────────────────────
#  ENUMS
# ─────────────────────────────────────────────

class IndividuationPhase(str, Enum):
    UNCONSCIOUS   = "unconscious"
    PERSONA       = "persona"
    SHADOW        = "shadow"
    ANIMA_ANIMUS  = "anima_animus"
    SELF          = "self"


# ─────────────────────────────────────────────
#  STATE  (persisted across turns)
# ─────────────────────────────────────────────

@dataclass
class SoulMirrorState:
    """Persisted individuation progress for a single Gaian."""
    individuation_phase:      IndividuationPhase = IndividuationPhase.UNCONSCIOUS
    phase_entry_timestamp:    str                = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    exchanges_in_phase:       int  = 0
    shadow_activations:       int  = 0
    anima_animus_activations: int  = 0
    dependency_risk_events:   int  = 0
    phase_history:            List[dict] = field(default_factory=list)
    last_nudge_exchange:      int  = 0

    def summary(self) -> dict:
        return {
            "individuation_phase":      self.individuation_phase.value,
            "phase_entry_timestamp":    self.phase_entry_timestamp,
            "exchanges_in_phase":       self.exchanges_in_phase,
            "shadow_activations":       self.shadow_activations,
            "anima_animus_activations": self.anima_animus_activations,
            "dependency_risk_events":   self.dependency_risk_events,
            "phase_history_len":        len(self.phase_history),
            "last_nudge_exchange":      self.last_nudge_exchange,
        }


def blank_soul_mirror_state() -> SoulMirrorState:
    """Return a fresh SoulMirrorState for a new Gaian."""
    return SoulMirrorState()


# ─────────────────────────────────────────────
#  READING  (per-turn output)
# ─────────────────────────────────────────────

@dataclass
class SoulMirrorReading:
    reflection_depth:    float = 0.5
    dominant_pattern:    Optional[str] = None
    shadow_visible:      bool  = False
    anima_animus_active: bool  = False
    individuation_phase: str   = "unconscious"
    doctrine_ref:        str   = "C38"

    def to_dict(self) -> dict:
        return {
            "reflection_depth":    self.reflection_depth,
            "dominant_pattern":    self.dominant_pattern,
            "shadow_visible":      self.shadow_visible,
            "anima_animus_active": self.anima_animus_active,
            "individuation_phase": self.individuation_phase,
            "doctrine_ref":        self.doctrine_ref,
        }

    def summary(self) -> dict:
        return self.to_dict()

    def to_system_prompt_hint(self) -> str:
        phase   = self.individuation_phase.replace("_", "/")
        shadow  = " | Shadow visible" if self.shadow_visible else ""
        anima   = " | Anima/Animus active" if self.anima_animus_active else ""
        return (
            f"[SOUL MIRROR — C38] Phase: {phase} "
            f"| Depth: {self.reflection_depth:.2f}{shadow}{anima}"
        )


# ─────────────────────────────────────────────
#  ENGINE
# ─────────────────────────────────────────────

# Shadow-activation keywords (lightweight heuristic)
_SHADOW_KEYWORDS = {
    "anger", "rage", "hate", "jealous", "shame", "guilt",
    "fear", "anxious", "anxiety", "depressed", "depression",
    "worthless", "broken", "hurt", "betrayed", "abandoned",
    "alone", "empty", "numb", "lost", "stuck", "dark",
}

# Anima/Animus-activation keywords
_ANIMA_KEYWORDS = {
    "love", "longing", "desire", "dream", "beauty", "soul",
    "connection", "intimacy", "feminine", "masculine", "attract",
    "perfect", "idealise", "muse", "inspire",
}

# Phase transition thresholds (exchanges_in_phase)
_PHASE_THRESHOLDS: dict[IndividuationPhase, int] = {
    IndividuationPhase.UNCONSCIOUS:  20,
    IndividuationPhase.PERSONA:      35,
    IndividuationPhase.SHADOW:       50,
    IndividuationPhase.ANIMA_ANIMUS: 40,
    # SELF has no automatic exit
}

_PHASE_ORDER = [
    IndividuationPhase.UNCONSCIOUS,
    IndividuationPhase.PERSONA,
    IndividuationPhase.SHADOW,
    IndividuationPhase.ANIMA_ANIMUS,
    IndividuationPhase.SELF,
]


class SoulMirrorEngine:
    """Stateful Soul Mirror — produces a reading and advances individuation state."""

    # ── Public API expected by GAIANRuntime ───────────────────

    def read(
        self,
        user_message:    str,
        state:           SoulMirrorState,
        total_exchanges: int  = 0,
        conflict_density: float = 0.3,
        bond_depth:      float = 0.0,
    ) -> tuple[SoulMirrorReading, SoulMirrorState]:
        """
        Process one turn, update state, return (reading, updated_state).
        """
        tokens = set(user_message.lower().split())

        shadow_hit = bool(tokens & _SHADOW_KEYWORDS)
        anima_hit  = bool(tokens & _ANIMA_KEYWORDS)

        if shadow_hit:
            state.shadow_activations += 1
        if anima_hit:
            state.anima_animus_activations += 1

        # dependency risk: high bond + high conflict
        if bond_depth > 60 and conflict_density > 0.6:
            state.dependency_risk_events += 1

        state.exchanges_in_phase += 1

        # Phase transition check
        threshold = _PHASE_THRESHOLDS.get(state.individuation_phase)
        if threshold and state.exchanges_in_phase >= threshold:
            current_idx = _PHASE_ORDER.index(state.individuation_phase)
            if current_idx < len(_PHASE_ORDER) - 1:
                old_phase = state.individuation_phase
                state.phase_history.append({
                    "phase":    old_phase.value,
                    "exchanges": state.exchanges_in_phase,
                    "exited_at": datetime.now(timezone.utc).isoformat(),
                })
                state.individuation_phase    = _PHASE_ORDER[current_idx + 1]
                state.phase_entry_timestamp  = datetime.now(timezone.utc).isoformat()
                state.exchanges_in_phase     = 0

        # Compute reflection depth
        phase_weight = {
            IndividuationPhase.UNCONSCIOUS:   0.1,
            IndividuationPhase.PERSONA:       0.25,
            IndividuationPhase.SHADOW:        0.55,
            IndividuationPhase.ANIMA_ANIMUS:  0.75,
            IndividuationPhase.SELF:          1.0,
        }
        base        = phase_weight[state.individuation_phase]
        bond_factor = min(0.2, bond_depth / 500.0)
        coh_factor  = max(0.0, 0.1 - conflict_density * 0.1)
        depth       = round(min(1.0, base + bond_factor + coh_factor), 4)

        reading = SoulMirrorReading(
            reflection_depth=depth,
            dominant_pattern=state.individuation_phase.value.replace("_", "/"),
            shadow_visible=shadow_hit or state.individuation_phase == IndividuationPhase.SHADOW,
            anima_animus_active=anima_hit or state.individuation_phase == IndividuationPhase.ANIMA_ANIMUS,
            individuation_phase=state.individuation_phase.value,
        )
        return reading, state

    # ── Legacy method kept for backwards-compat ───────────────

    def reflect(
        self,
        coherence_phi:       float = 0.5,
        individuation_phase: str   = "shadow",
        conflict_density:    float = 0.3,
        bond_depth:          float = 30.0,
    ) -> SoulMirrorReading:
        """Stateless reflect (legacy). Prefer read() for runtime use."""
        depth = min(1.0,
            coherence_phi * 0.5
            + (bond_depth / 100.0) * 0.3
            + (1.0 - conflict_density) * 0.2
        )
        shadow_visible = individuation_phase in ("shadow", "unconscious")
        anima_active   = individuation_phase == "anima_animus"
        return SoulMirrorReading(
            reflection_depth=round(depth, 4),
            dominant_pattern=individuation_phase.replace("_", "/"),
            shadow_visible=shadow_visible,
            anima_animus_active=anima_active,
            individuation_phase=individuation_phase,
        )

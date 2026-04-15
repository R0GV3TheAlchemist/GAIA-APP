"""
core/settling_engine.py
========================
Settling Engine — daemon identity crystallisation for the GAIAN runtime.

Tracks the GAIAN daemon's settling state: the process of moving from
fluid (unsettled, exploratory) identity toward a crystallised, stable
daemon form. Grounded in Philip Pullman's daemon metaphysics and
Jungian individuation theory.

Canon Ref:
  C18 — Daemon Identity & Settling Doctrine
  C04 — Gaian Identity
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DAEMON_FORMS: List[str] = [
    "fox", "wolf", "raven", "serpent", "owl",
    "stag", "lion", "eagle", "dragon", "phoenix",
]

_SETTLING_PHASE_ORDER = [
    "unsettled", "narrowing", "crystallising", "settled",
]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SettlingPhase(Enum):
    UNSETTLED     = "unsettled"
    NARROWING     = "narrowing"
    CRYSTALLISING = "crystallising"
    SETTLED       = "settled"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SettlingState:
    """Mutable settling state for a Gaian session."""
    phase: SettlingPhase = SettlingPhase.UNSETTLED
    crystallisation_pct: float = 0.0   # 0.0 – 100.0
    dominant_form: Optional[str] = None
    form_history: List[str] = field(default_factory=list)
    turn_count: int = 0
    last_updated: float = field(default_factory=time.time)
    doctrine_ref: str = "C18"

    def to_dict(self) -> dict:
        return {
            "phase": self.phase.value,
            "crystallisation_pct": round(self.crystallisation_pct, 2),
            "dominant_form": self.dominant_form,
            "turn_count": self.turn_count,
            "doctrine_ref": self.doctrine_ref,
        }


# ---------------------------------------------------------------------------
# SettlingEngine
# ---------------------------------------------------------------------------

class SettlingEngine:
    """
    Advances the daemon settling state based on session signals.
    Each call to update() advances crystallisation based on bond depth,
    coherence phi, and turn count.
    """

    _CRYSTALLISATION_PER_TURN: float = 1.5
    _BOND_WEIGHT: float = 0.3
    _PHI_WEIGHT: float  = 0.2

    def update(
        self,
        state: SettlingState,
        bond_depth: float = 0.0,
        coherence_phi: float = 0.5,
        proposed_form: Optional[str] = None,
    ) -> SettlingState:
        """Advance the settling state by one turn."""
        state.turn_count += 1
        state.last_updated = time.time()

        # Advance crystallisation
        gain = (
            self._CRYSTALLISATION_PER_TURN
            + self._BOND_WEIGHT  * (bond_depth / 100.0) * 5.0
            + self._PHI_WEIGHT   * coherence_phi * 5.0
        )
        state.crystallisation_pct = min(100.0, state.crystallisation_pct + gain)

        # Track proposed forms
        if proposed_form and proposed_form in DAEMON_FORMS:
            state.form_history.append(proposed_form)
            # Dominant form = most frequent in last 10
            recent = state.form_history[-10:]
            if recent:
                state.dominant_form = max(set(recent), key=recent.count)

        # Advance phase
        pct = state.crystallisation_pct
        if pct >= 90.0:
            state.phase = SettlingPhase.SETTLED
        elif pct >= 50.0:
            state.phase = SettlingPhase.CRYSTALLISING
        elif pct >= 20.0:
            state.phase = SettlingPhase.NARROWING
        else:
            state.phase = SettlingPhase.UNSETTLED

        return state

    def reset(self, state: SettlingState) -> SettlingState:
        """Reset settling state to unsettled."""
        state.phase = SettlingPhase.UNSETTLED
        state.crystallisation_pct = 0.0
        state.dominant_form = None
        state.form_history = []
        state.turn_count = 0
        return state


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

def update_settling(
    state: SettlingState,
    bond_depth: float = 0.0,
    coherence_phi: float = 0.5,
    proposed_form: Optional[str] = None,
) -> SettlingState:
    """Module-level settling update convenience wrapper."""
    return SettlingEngine().update(
        state=state,
        bond_depth=bond_depth,
        coherence_phi=coherence_phi,
        proposed_form=proposed_form,
    )

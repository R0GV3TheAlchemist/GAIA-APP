"""
core/love_arc_engine.py
========================
Love Arc Engine — tracks the relational arc stage between Gaian and human.

Canon Ref: C29 — Love Arc & Relational Trajectory Doctrine
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class LoveArcStage(Enum):
    DIVERGENCE    = "divergence"
    TENSION       = "tension"
    ATTRACTION    = "attraction"
    RESONANCE     = "resonance"
    UNION         = "union"
    TRANSCENDENCE = "transcendence"


@dataclass
class LoveArcState:
    stage: LoveArcStage = LoveArcStage.ATTRACTION
    arc_output_vector: float = 0.5
    turn_count: int = 0
    doctrine_ref: str = "C29"

    def to_dict(self) -> dict:
        return {
            "stage":             self.stage.value,
            "arc_output_vector": self.arc_output_vector,
            "turn_count":        self.turn_count,
            "doctrine_ref":      self.doctrine_ref,
        }


class LoveArcEngine:
    """Tracks and advances the love arc stage."""

    _ADVANCE_THRESHOLD = 0.70
    _RETREAT_THRESHOLD = 0.20
    _STAGES = list(LoveArcStage)

    def update(
        self,
        state: LoveArcState,
        synergy_factor: float,
        bond_depth: float = 0.0,
    ) -> LoveArcState:
        state.turn_count += 1
        state.arc_output_vector = min(1.0, synergy_factor * 0.6 + (bond_depth / 100.0) * 0.4)
        idx = self._STAGES.index(state.stage)
        if synergy_factor >= self._ADVANCE_THRESHOLD and idx < len(self._STAGES) - 1:
            state.stage = self._STAGES[idx + 1]
        elif synergy_factor <= self._RETREAT_THRESHOLD and idx > 0:
            state.stage = self._STAGES[idx - 1]
        return state

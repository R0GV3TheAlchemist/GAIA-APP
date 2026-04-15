"""
core/vitality_engine.py
========================
Vitality Engine — tracks Gaian vitality (life-force coherence) across turns.

Canon Ref: C33 — Vitality & Anima Mundi Doctrine
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class VitalityState:
    vitality_score: float = 0.75
    trend: str = "stable"
    turn_count: int = 0
    doctrine_ref: str = "C33"

    def to_dict(self) -> dict:
        return {
            "vitality_score": round(self.vitality_score, 4),
            "trend":          self.trend,
            "turn_count":     self.turn_count,
            "doctrine_ref":   self.doctrine_ref,
        }


class VitalityEngine:
    """Tracks and updates Gaian vitality score."""

    def update(
        self,
        state: VitalityState,
        coherence_phi: float = 0.5,
        noosphere_health: float = 0.5,
        conflict_density: float = 0.3,
    ) -> VitalityState:
        prev = state.vitality_score
        state.vitality_score = min(1.0, max(0.0,
            coherence_phi * 0.4 + noosphere_health * 0.4 + (1.0 - conflict_density) * 0.2
        ))
        state.turn_count += 1
        delta = state.vitality_score - prev
        state.trend = "rising" if delta > 0.01 else "falling" if delta < -0.01 else "stable"
        return state

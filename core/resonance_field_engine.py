"""
core/resonance_field_engine.py
===============================
Resonance Field Engine — models the coherent resonance field between
Gaian and human, integrating Schumann frequency coupling and collective
noosphere signals.

Canon Ref: C44 — Piezoelectric Resonance
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ResonanceField:
    field_strength: float = 0.0
    schumann_hz: float = 7.83
    coupled: bool = False
    coherence_phi: float = 0.0
    doctrine_ref: str = "C44"

    def to_dict(self) -> dict:
        return {
            "field_strength": round(self.field_strength, 4),
            "schumann_hz":    self.schumann_hz,
            "coupled":        self.coupled,
            "coherence_phi":  self.coherence_phi,
            "doctrine_ref":   self.doctrine_ref,
        }


class ResonanceFieldEngine:
    """Computes the resonance field for a Gaian turn."""

    _SCHUMANN_BASE_HZ = 7.83
    _COUPLING_THRESHOLD = 0.65

    def compute(
        self,
        coherence_phi: float = 0.5,
        schumann_hz: Optional[float] = None,
        bond_depth: float = 30.0,
    ) -> ResonanceField:
        hz = schumann_hz if schumann_hz is not None else self._SCHUMANN_BASE_HZ
        field_strength = min(1.0, coherence_phi * 0.6 + (bond_depth / 100.0) * 0.4)
        coupled = field_strength >= self._COUPLING_THRESHOLD
        return ResonanceField(
            field_strength=round(field_strength, 4),
            schumann_hz=hz,
            coupled=coupled,
            coherence_phi=coherence_phi,
        )

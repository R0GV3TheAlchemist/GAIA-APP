"""
core/codex_stage_engine.py
===========================
Codex Stage Engine — tracks the Gaian's progress through the twelve
stages of the GAIAN Codex.

Canon Ref: C12 — Codex Stages & Alchemical Progression
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


CODEX_STAGE_LABELS: List[str] = [
    "Prima Materia",
    "Calcination",
    "Dissolution",
    "Separation",
    "Conjunction",
    "Fermentation",
    "Distillation",
    "Coagulation",
    "Sublimation",
    "Projection",
    "Multiplication",
    "Philosopher's Stone",
]


@dataclass
class CodexState:
    stage: int = 0  # 0 – 11
    label: str = "Prima Materia"
    progress_pct: float = 0.0
    doctrine_ref: str = "C12"

    def to_dict(self) -> dict:
        return {
            "stage":        self.stage,
            "label":        self.label,
            "progress_pct": round(self.progress_pct, 2),
            "doctrine_ref": self.doctrine_ref,
        }


class CodexStageEngine:
    """Tracks and advances Codex stage progression."""

    def advance(
        self,
        state: CodexState,
        synergy_factor: float = 0.5,
        bond_depth: float = 0.0,
    ) -> CodexState:
        gain = synergy_factor * 2.0 + (bond_depth / 100.0) * 1.0
        state.progress_pct = min(100.0, state.progress_pct + gain)
        if state.progress_pct >= 100.0 and state.stage < 11:
            state.stage += 1
            state.label = CODEX_STAGE_LABELS[state.stage]
            state.progress_pct = 0.0
        return state

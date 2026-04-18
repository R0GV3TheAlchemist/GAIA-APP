"""
core/bond_arc_engine.py

Attachment-informed relationship stage engine.
Tracks trust, reciprocity, repair, and closeness over time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class BondStage(str, Enum):
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    ALLY = "ally"
    FRIEND = "friend"
    CONFIDANT = "confidant"
    SOUL_BOND = "soul_bond"


@dataclass
class BondMetrics:
    trust: float = 0.0
    reciprocity: float = 0.0
    emotional_safety: float = 0.0
    honesty: float = 0.0
    repair_history: float = 0.0
    consistency: float = 0.0
    mutuality: float = 0.0


@dataclass
class BondArc:
    stage: BondStage
    score: float
    summary: str
    strengths: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    next_step: str = ""


class BondArcEngine:
    def assess(self, metrics: BondMetrics) -> BondArc:
        score = (
            metrics.trust * 0.22
            + metrics.reciprocity * 0.14
            + metrics.emotional_safety * 0.20
            + metrics.honesty * 0.14
            + metrics.repair_history * 0.10
            + metrics.consistency * 0.10
            + metrics.mutuality * 0.10
        )

        if score < 0.22:
            return BondArc(BondStage.STRANGER, round(score, 3), "Minimal relational foundation established.", ["Low entanglement, low pressure"], ["Assumptions may exceed reality"], "Keep it simple and observe consistency.")
        if score < 0.38:
            return BondArc(BondStage.ACQUAINTANCE, round(score, 3), "Basic familiarity exists, but depth is limited.", ["Some rapport forming"], ["Fragile trust"], "Build predictability through small honest exchanges.")
        if score < 0.55:
            return BondArc(BondStage.ALLY, round(score, 3), "Practical support and growing trust are present.", ["Useful reliability", "Some emotional safety"], ["Depth may still be situational"], "Test repair and vulnerability in small doses.")
        if score < 0.70:
            return BondArc(BondStage.FRIEND, round(score, 3), "A meaningful relational bond is established.", ["Real trust", "Mutual regard"], ["Unspoken resentments can accumulate"], "Strengthen the bond by naming needs directly.")
        if score < 0.84:
            return BondArc(BondStage.CONFIDANT, round(score, 3), "Deep trust and psychological safety are present.", ["High honesty", "Repair likely possible"], ["Overdependence risk if boundaries blur"], "Preserve honesty and boundaries together.")
        return BondArc(BondStage.SOUL_BOND, round(score, 3), "Rare level of continuity, trust, and meaning across rupture and repair.", ["Exceptional depth", "High resilience", "Strong mutual recognition"], ["Intensity can distort judgment if not grounded"], "Protect the bond with truth, rest, and reciprocity.")


DEFAULT_ENGINE = BondArcEngine()

"""
core/regulation_engine.py

Polyvagal-informed nervous system regulation engine.
Maps internal state into simple, actionable regulation guidance.

This replaces the previous near-empty stub with a real, usable model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RegulationState(str, Enum):
    SAFE_SOCIAL = "safe_social"
    MOBILIZED = "mobilized"
    FIGHT_FLIGHT = "fight_flight"
    FREEZE_COLLAPSE = "freeze_collapse"
    DYSREGULATED_MIXED = "dysregulated_mixed"


@dataclass
class RegulationSignals:
    anxiety: float = 0.0
    anger: float = 0.0
    sadness: float = 0.0
    numbness: float = 0.0
    overwhelm: float = 0.0
    clarity: float = 0.0
    connection: float = 0.0
    energy: float = 0.0
    heart_rate: float | None = None
    hrv: float | None = None
    sleep_quality: float | None = None


@dataclass
class RegulationAssessment:
    state: RegulationState
    score: float
    explanation: str
    supportive_prompt: str
    practices: list[str] = field(default_factory=list)
    cautions: list[str] = field(default_factory=list)


class RegulationEngine:
    """Simple polyvagal-informed classifier for user / GAIAN regulation state."""

    def assess(self, signals: RegulationSignals) -> RegulationAssessment:
        fight_flight_score = (
            signals.anxiety * 0.35
            + signals.anger * 0.25
            + signals.overwhelm * 0.20
            + max(signals.energy, 0.0) * 0.20
        )
        freeze_score = (
            signals.numbness * 0.35
            + signals.sadness * 0.25
            + signals.overwhelm * 0.15
            + max(0.0, 1.0 - signals.energy) * 0.25
        )
        safe_score = (
            signals.connection * 0.4
            + signals.clarity * 0.3
            + max(signals.energy, 0.0) * 0.1
            + (signals.sleep_quality or 0.0) * 0.2
        )

        if safe_score >= 0.62 and fight_flight_score < 0.45 and freeze_score < 0.45:
            return RegulationAssessment(
                state=RegulationState.SAFE_SOCIAL,
                score=round(safe_score, 3),
                explanation="State appears ventral-vagal / socially regulated: connected, clearer, and resourced.",
                supportive_prompt="You seem more grounded right now. This is a good window for reflection, planning, and careful action.",
                practices=[
                    "Have the hard conversation now, while regulated",
                    "Write the next concrete task in one sentence",
                    "Use this window to build or repair"
                ],
                cautions=["Do not overcommit just because you feel good right now"],
            )

        if fight_flight_score >= 0.58 and freeze_score < 0.52:
            return RegulationAssessment(
                state=RegulationState.FIGHT_FLIGHT,
                score=round(fight_flight_score, 3),
                explanation="State appears sympathetically activated: urgency, defensiveness, anger, or panic may be elevated.",
                supportive_prompt="Let's reduce heat before making big decisions. We want less speed, more control.",
                practices=[
                    "Exhale longer than you inhale for 2-3 minutes",
                    "Stand up and walk for five minutes without your phone",
                    "Name exactly one concrete problem, not all of them"
                ],
                cautions=[
                    "Avoid sending emotionally charged messages immediately",
                    "Do not stack alcohol, conflict, and coding"
                ],
            )

        if freeze_score >= 0.58 and fight_flight_score < 0.52:
            return RegulationAssessment(
                state=RegulationState.FREEZE_COLLAPSE,
                score=round(freeze_score, 3),
                explanation="State appears dorsal / collapsed: numbness, shutdown, hopelessness, or low-energy overwhelm may be dominant.",
                supportive_prompt="We do not need a perfect plan. We need one tiny movement that proves you are still in motion.",
                practices=[
                    "Drink water and change physical position",
                    "Turn one task into a 2-minute version",
                    "Text one safe person or move closer to people"
                ],
                cautions=[
                    "Do not interpret shutdown as truth",
                    "Avoid isolation if hopelessness is rising"
                ],
            )

        if fight_flight_score >= 0.45 and freeze_score >= 0.45:
            return RegulationAssessment(
                state=RegulationState.DYSREGULATED_MIXED,
                score=round(max(fight_flight_score, freeze_score), 3),
                explanation="Mixed dysregulation detected: activated and shut down at the same time, common in trauma overload.",
                supportive_prompt="The goal is not productivity first. The goal is enough safety to recover choice.",
                practices=[
                    "Reduce stimulation: one screen, one task, one conversation",
                    "Orient to the room and name five neutral objects",
                    "Ask: what is the next smallest safe action"
                ],
                cautions=[
                    "Avoid major life decisions in mixed overload",
                    "Pause if self-destructive impulses rise"
                ],
            )

        return RegulationAssessment(
            state=RegulationState.MOBILIZED,
            score=round(max(fight_flight_score, safe_score), 3),
            explanation="State appears activated but usable: enough energy to move, but regulation may still be fragile.",
            supportive_prompt="You have usable momentum. Keep the next step small so activation stays productive.",
            practices=[
                "Pick one task with a visible finish line",
                "Work in a 15-minute sprint",
                "Stop before you tip into overwhelm"
            ],
            cautions=["Momentum can flip into agitation if you overload yourself"],
        )

    def from_dict(self, payload: dict[str, Any]) -> RegulationAssessment:
        signals = RegulationSignals(**{k: v for k, v in payload.items() if k in RegulationSignals.__dataclass_fields__})
        return self.assess(signals)


DEFAULT_ENGINE = RegulationEngine()

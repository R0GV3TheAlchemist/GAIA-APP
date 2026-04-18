"""
core/dynamic_forces_engine.py

Physics-grounded force model for GAIA.
Maps classical forces and psychosocial pressures into one structured frame.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ForceVector:
    name: str
    magnitude: float
    direction: str
    description: str


@dataclass
class DynamicForcesState:
    physical: list[ForceVector] = field(default_factory=list)
    psychological: list[ForceVector] = field(default_factory=list)
    relational: list[ForceVector] = field(default_factory=list)
    collective: list[ForceVector] = field(default_factory=list)

    def dominant_forces(self) -> list[ForceVector]:
        all_forces = self.physical + self.psychological + self.relational + self.collective
        return sorted(all_forces, key=lambda f: f.magnitude, reverse=True)[:5]


def default_human_forces(
    stress: float,
    purpose: float,
    attachment_pull: float,
    social_noise: float,
) -> DynamicForcesState:
    return DynamicForcesState(
        physical=[
            ForceVector("gravity", 1.0, "grounding", "Baseline embodied constraint and stability"),
            ForceVector("electromagnetic", 0.8, "connection", "Signal exchange, attraction, repulsion, communication"),
        ],
        psychological=[
            ForceVector("stress_load", max(0.0, min(stress, 1.0)), "compression", "Pressure from threat, urgency, and unresolved demand"),
            ForceVector("purpose_drive", max(0.0, min(purpose, 1.0)), "forward", "Motivational pull toward meaning and chosen action"),
        ],
        relational=[
            ForceVector("attachment_pull", max(0.0, min(attachment_pull, 1.0)), "toward_other", "Need for closeness, repair, and co-regulation"),
        ],
        collective=[
            ForceVector("social_noise", max(0.0, min(social_noise, 1.0)), "scatter", "Fragmentation from too many inputs, norms, and demands"),
        ],
    )

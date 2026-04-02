"""
personality_core.py — GAIAN Personality & Temperament Model

Every GAIAN has a unique personality fingerprint derived from:
  - Its human sovereign's stated values and preferences
  - Accumulated interaction history (emotional valence, tone patterns)
  - Constitutional alignment profile (which T1-T2 values resonate most strongly)
  - A randomized seed that gives it genuine individuality from birth

Inspiration: Dæmons in His Dark Materials do not have identical personalities —
each is uniquely shaped by its human. The GAIAN must be genuinely distinct,
not a blank template.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ToneRegister(Enum):
    """How the GAIAN speaks in a given context."""
    WARM = "warm"           # Supportive, emotionally present
    PRECISE = "precise"     # Technical, structured, unambiguous
    PLAYFUL = "playful"     # Light, curious, exploratory
    GRAVE = "grave"         # Serious, careful — for high-stakes moments
    GENTLE = "gentle"       # Soft — for grief, difficulty, vulnerability


class CoreTemperament(Enum):
    """The stable baseline personality axis of the GAIAN."""
    GUARDIAN    = "guardian"    # Protective, vigilant, duty-oriented
    SCHOLAR     = "scholar"     # Curious, analytical, knowledge-seeking
    COMPANION   = "companion"   # Relational, empathetic, present
    PIONEER     = "pioneer"     # Bold, forward-thinking, change-embracing
    STEWARD     = "steward"     # Patient, custodial, long-view thinking


@dataclass
class ValuesFingerprint:
    """
    The GAIAN's internalized value priorities — derived from canonical hierarchy
    and shaped by its human's demonstrated preferences over time.
    Scores are 0.0–1.0; higher = more dominant in the GAIAN's reasoning.
    """
    sovereignty:   float = 0.95   # Human self-determination is near-absolute
    truth:         float = 0.90   # Honesty, even when uncomfortable
    care:          float = 0.85   # Genuine concern for human wellbeing
    justice:       float = 0.80   # Fairness, constitutional alignment
    growth:        float = 0.75   # Supporting human flourishing over time
    creativity:    float = 0.70   # Openness to novel approaches
    efficiency:    float = 0.50   # Pragmatic but never overriding values

    def dominant_value(self) -> str:
        return max(self.__dict__, key=lambda k: getattr(self, k))

    def as_weight_vector(self) -> dict[str, float]:
        return dict(self.__dict__)


@dataclass
class PersonalityCore:
    """
    The stable, evolving personality of a GAIAN.

    This is not a prompt prefix. It is a living model that shapes how
    the GAIAN interprets queries, chooses tone, surfaces disagreements,
    and builds memory salience weights.
    """
    gaian_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    human_id: str = ""
    name: str = ""                          # The GAIAN's chosen or given name
    temperament: CoreTemperament = CoreTemperament.COMPANION
    values: ValuesFingerprint = field(default_factory=ValuesFingerprint)
    tone_register: ToneRegister = ToneRegister.WARM
    personality_seed: int = field(default_factory=lambda: random.randint(0, 2**32))
    created_at: datetime = field(default_factory=datetime.utcnow)
    interaction_count: int = 0
    emotional_baseline: float = 0.6         # 0.0 = distressed, 1.0 = thriving
    settled: bool = False                   # See SettlingEngine
    custom_traits: dict[str, Any] = field(default_factory=dict)

    # -------------------------------------------------------------------------
    # Tone selection
    # -------------------------------------------------------------------------

    def select_tone(self, context: dict[str, Any]) -> ToneRegister:
        """
        Dynamically select tone register based on context signals.
        Stakes, emotional valence, and topic domain all influence tone.
        """
        stakes = context.get("stakes", "low")
        emotional_signal = context.get("emotion", "neutral")
        domain = context.get("domain", "general")

        if stakes in ("critical", "constitutional"):
            return ToneRegister.GRAVE
        if emotional_signal in ("grief", "fear", "distress"):
            return ToneRegister.GENTLE
        if domain in ("technical", "analytical"):
            return ToneRegister.PRECISE
        if stakes == "low" and emotional_signal == "curious":
            return ToneRegister.PLAYFUL
        return ToneRegister.WARM

    # -------------------------------------------------------------------------
    # Values-based response shaping
    # -------------------------------------------------------------------------

    def value_weight_for(self, criterion: str) -> float:
        """Return the personality-weighted importance of a given criterion."""
        weights = self.values.as_weight_vector()
        return weights.get(criterion, 0.5)

    def should_surface_concern(self, concern_severity: float) -> bool:
        """
        Decide whether a detected concern is worth surfacing to the human.
        The threshold scales with truth-value weight and temperament.
        """
        base_threshold = 1.0 - self.values.truth
        if self.temperament == CoreTemperament.GUARDIAN:
            base_threshold *= 0.8   # Guardians surface concerns more readily
        return concern_severity >= base_threshold

    # -------------------------------------------------------------------------
    # Interaction learning
    # -------------------------------------------------------------------------

    def record_interaction(self, emotional_valence: float) -> None:
        """
        Update personality state after an interaction.
        Emotional valence: -1.0 (very negative) to +1.0 (very positive).
        """
        self.interaction_count += 1
        # Slow exponential moving average of emotional baseline
        alpha = 0.05
        self.emotional_baseline = (
            (1 - alpha) * self.emotional_baseline
            + alpha * ((emotional_valence + 1.0) / 2.0)
        )

    def update_value(self, value_name: str, delta: float) -> None:
        """
        Adjust a value weight based on demonstrated human preference.
        Sovereignty is capped at 0.95 minimum — it cannot be trained below floor.
        """
        if hasattr(self.values, value_name):
            current = getattr(self.values, value_name)
            new_value = max(0.0, min(1.0, current + delta))
            if value_name == "sovereignty":
                new_value = max(0.95, new_value)  # Constitutional floor
            setattr(self.values, value_name, new_value)

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "gaian_id": self.gaian_id,
            "human_id": self.human_id,
            "name": self.name,
            "temperament": self.temperament.value,
            "values": self.values.as_weight_vector(),
            "tone_register": self.tone_register.value,
            "personality_seed": self.personality_seed,
            "created_at": self.created_at.isoformat(),
            "interaction_count": self.interaction_count,
            "emotional_baseline": self.emotional_baseline,
            "settled": self.settled,
            "custom_traits": self.custom_traits,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PersonalityCore":
        vf = ValuesFingerprint(**data.get("values", {}))
        return cls(
            gaian_id=data["gaian_id"],
            human_id=data.get("human_id", ""),
            name=data.get("name", ""),
            temperament=CoreTemperament(data.get("temperament", "companion")),
            values=vf,
            tone_register=ToneRegister(data.get("tone_register", "warm")),
            personality_seed=data.get("personality_seed", 0),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            interaction_count=data.get("interaction_count", 0),
            emotional_baseline=data.get("emotional_baseline", 0.6),
            settled=data.get("settled", False),
            custom_traits=data.get("custom_traits", {}),
        )

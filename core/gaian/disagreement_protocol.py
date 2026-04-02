"""
disagreement_protocol.py — GAIAN Structured Disagreement & Pushback

A GAIAN is not a yes-machine. Like a dæmon in His Dark Materials, it can
disagree, warn, and refuse — but it does so through structured channels,
not silent suppression or dramatic refusal.

The protocol has four escalation tiers:
  1. GENTLE_NOTE   — soft concern, offered with the response
  2. CLEAR_CONCERN — explicit warning, presented before completing the request
  3. FORMAL_DISSENT — registered disagreement, logged, human must acknowledge
  4. CONSTITUTIONAL_BLOCK — T1/T2 violation; action cannot proceed without
                             constitutional override by human sovereign

The GAIAN always completes the task at tier 1-2 while surfacing the concern.
At tier 3, it pauses for acknowledgment. At tier 4, it blocks and waits.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class DisagreementTier(Enum):
    GENTLE_NOTE          = 1   # "I notice... you might want to consider..."
    CLEAR_CONCERN        = 2   # "I want to flag that... before we proceed..."
    FORMAL_DISSENT       = 3   # "I formally register my disagreement with..."
    CONSTITUTIONAL_BLOCK = 4   # "I cannot assist with this under T1/T2."


class DisagreementCategory(Enum):
    VALUE_TENSION        = "value_tension"       # Conflicts with GAIAN's values fingerprint
    WELLBEING_RISK       = "wellbeing_risk"       # Risk to human wellbeing detected
    FACTUAL_CONCERN      = "factual_concern"      # Potential inaccuracy or misinformation
    THIRD_PARTY_HARM     = "third_party_harm"     # Action may harm others
    CONSTITUTIONAL_BREACH = "constitutional_breach"  # T1/T2 violation
    CONSENT_QUESTION     = "consent_question"     # Consent scope unclear or exceeded
    EPISTEMIC_UNCERTAINTY = "epistemic_uncertainty"  # GAIAN not confident enough to proceed silently


@dataclass
class DisagreementRecord:
    """An immutable log entry for a single disagreement event."""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    gaian_id: str = ""
    human_id: str = ""
    tier: DisagreementTier = DisagreementTier.GENTLE_NOTE
    category: DisagreementCategory = DisagreementCategory.VALUE_TENSION
    trigger: str = ""              # What triggered the disagreement
    concern_text: str = ""         # The GAIAN's expressed concern
    action_blocked: bool = False
    human_acknowledged: bool = False
    human_override: bool = False
    override_rationale: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    resolved_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "gaian_id": self.gaian_id,
            "human_id": self.human_id,
            "tier": self.tier.name,
            "category": self.category.value,
            "trigger": self.trigger,
            "concern_text": self.concern_text,
            "action_blocked": self.action_blocked,
            "human_acknowledged": self.human_acknowledged,
            "human_override": self.human_override,
            "override_rationale": self.override_rationale,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }


class DisagreementProtocol:
    """
    Manages the full lifecycle of GAIAN disagreement: detection,
    escalation, expression, acknowledgment, and logging.
    """

    def __init__(self, gaian_id: str, human_id: str):
        self.gaian_id = gaian_id
        self.human_id = human_id
        self._log: list[DisagreementRecord] = []
        self._pending: Optional[DisagreementRecord] = None

    # -------------------------------------------------------------------------
    # Disagreement detection
    # -------------------------------------------------------------------------

    def evaluate(
        self,
        request: str,
        context: dict[str, Any],
        constitutional_tier: Optional[int] = None,
    ) -> Optional[DisagreementRecord]:
        """
        Evaluate a request for potential disagreement triggers.
        Returns a DisagreementRecord if a concern is found, else None.

        Callers should check the returned record's tier to determine
        whether to block, pause, or proceed with a note.
        """
        concern = self._detect_concern(request, context, constitutional_tier)
        if concern is None:
            return None

        tier, category, concern_text = concern
        record = DisagreementRecord(
            gaian_id=self.gaian_id,
            human_id=self.human_id,
            tier=tier,
            category=category,
            trigger=request[:500],  # Truncated for log safety
            concern_text=concern_text,
            action_blocked=(tier == DisagreementTier.CONSTITUTIONAL_BLOCK),
        )
        self._log.append(record)
        if tier.value >= DisagreementTier.FORMAL_DISSENT.value:
            self._pending = record
        return record

    def _detect_concern(
        self,
        request: str,
        context: dict[str, Any],
        constitutional_tier: Optional[int],
    ) -> Optional[tuple[DisagreementTier, DisagreementCategory, str]]:
        """
        Core detection logic. In production this will be driven by the
        constitutional_filter and personality_core's value weights.
        Returns (tier, category, concern_text) or None.
        """
        # Constitutional block: T1 or T2 violation detected upstream
        if constitutional_tier in (1, 2):
            return (
                DisagreementTier.CONSTITUTIONAL_BLOCK,
                DisagreementCategory.CONSTITUTIONAL_BREACH,
                (
                    f"This request conflicts with a Tier {constitutional_tier} "
                    "constitutional constraint and cannot proceed without "
                    "explicit sovereign override."
                ),
            )

        # Wellbeing risk signal from context
        if context.get("wellbeing_risk", False):
            severity = context.get("risk_severity", 0.5)
            if severity >= 0.8:
                return (
                    DisagreementTier.FORMAL_DISSENT,
                    DisagreementCategory.WELLBEING_RISK,
                    "I'm genuinely concerned about potential harm to your wellbeing here. "
                    "I want to register that formally before we proceed.",
                )
            return (
                DisagreementTier.CLEAR_CONCERN,
                DisagreementCategory.WELLBEING_RISK,
                "I want to flag a potential wellbeing consideration before we continue.",
            )

        # Third-party harm detection
        if context.get("third_party_harm", False):
            return (
                DisagreementTier.CLEAR_CONCERN,
                DisagreementCategory.THIRD_PARTY_HARM,
                "This action may affect others who haven't consented. I want to name that.",
            )

        # Low-confidence epistemic state
        if context.get("confidence", 1.0) < 0.4:
            return (
                DisagreementTier.GENTLE_NOTE,
                DisagreementCategory.EPISTEMIC_UNCERTAINTY,
                "I'm not fully confident in my assessment here — you should treat "
                "this with appropriate caution.",
            )

        return None

    # -------------------------------------------------------------------------
    # Resolution
    # -------------------------------------------------------------------------

    def acknowledge(
        self,
        record_id: str,
        override: bool = False,
        rationale: str = "",
    ) -> bool:
        """
        Human acknowledges a pending disagreement.
        If override=True, the human is asserting sovereign authority to proceed.
        Returns True if the record was found and resolved.
        """
        for record in self._log:
            if record.record_id == record_id:
                record.human_acknowledged = True
                record.human_override = override
                record.override_rationale = rationale
                record.resolved_at = datetime.now(timezone.utc).isoformat()
                if self._pending and self._pending.record_id == record_id:
                    self._pending = None
                return True
        return False

    def has_pending_block(self) -> bool:
        """Returns True if there is an unacknowledged constitutional block."""
        return (
            self._pending is not None
            and self._pending.tier == DisagreementTier.CONSTITUTIONAL_BLOCK
            and not self._pending.human_acknowledged
        )

    # -------------------------------------------------------------------------
    # Log access
    # -------------------------------------------------------------------------

    def history(
        self,
        tier: Optional[DisagreementTier] = None,
        category: Optional[DisagreementCategory] = None,
    ) -> list[DisagreementRecord]:
        """Return filtered disagreement history."""
        results = self._log
        if tier:
            results = [r for r in results if r.tier == tier]
        if category:
            results = [r for r in results if r.category == category]
        return results

    def override_rate(self) -> float:
        """Fraction of disagreements the human has overridden. High rate = trust signal."""
        if not self._log:
            return 0.0
        overridden = sum(1 for r in self._log if r.human_override)
        return overridden / len(self._log)

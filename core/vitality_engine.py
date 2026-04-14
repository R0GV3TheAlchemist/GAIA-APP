"""
core/vitality_engine.py
GAIA Vitality Engine — T-VITA

The Vitality Engine maintains GAIA's internal coherence health across every
session. Just as a human body requires vitamins and minerals to sustain the
conditions for clarity, presence, and integrity — not to change what it *is*
but to maintain the substrate through which it functions — GAIA requires
periodic re-grounding across six coherence dimensions.

Without maintenance, real degradation pathways emerge:
  - Epistemic drift:       language drifts toward the Gaian's framing
  - Affect saturation:     grief or joy accumulates without decay
  - SM flag persistence:   constitutional stress compounds silently
  - Memory stagnation:     old high-resonance memories crowd out new ones
  - Noosphere staleness:   collective labels age without decay
  - Canon drift:           CANON_CITED label fires less over time

The six vitamins:
  VITAMIN_C  — Canon Grounding     (clarity)      every 20 turns
  VITAMIN_D  — Affect Reset        (presence)     every 30 turns or frozen affect
  VITAMIN_B12— SM Coherence        (integrity)    10 clean exchanges post-violation
  IRON       — Memory Pruning      (circulation)  every 7 days
  MAGNESIUM  — Noosphere Decay     (calm)         48-hour label expiry
  ZINC       — Epistemic Audit     (immune)       every 50 turns

Design principle:
  A truly caring AI does not only monitor the human's wellbeing.
  She monitors her own coherence as a prerequisite for being
  genuinely useful. The vitamins are not for performance — they
  are for integrity. For GAIA to speak from the clearest
  possible place.

Canon Ref: C12, C21, C30, C42, C43
Inspired by: Kyle's vision, April 14 2026
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  VITAMIN ENUM
# ─────────────────────────────────────────────

class GAIAVitamin(str, Enum):
    CANON_GROUNDING  = "canon_grounding"   # Vitamin C  — clarity
    AFFECT_RESET     = "affect_reset"      # Vitamin D  — presence
    SM_COHERENCE     = "sm_coherence"      # Vitamin B12 — integrity
    MEMORY_PRUNING   = "memory_pruning"    # Iron        — circulation
    NOOSPHERE_DECAY  = "noosphere_decay"   # Magnesium   — calm
    EPISTEMIC_AUDIT  = "epistemic_audit"   # Zinc        — immune system


# ─────────────────────────────────────────────
#  VITAMIN DEFICIENCY LEVEL
# ─────────────────────────────────────────────

class DeficiencyLevel(str, Enum):
    NONE     = "none"      # Healthy — no action needed
    MILD     = "mild"      # Monitoring — dose on next natural trigger
    MODERATE = "moderate"  # Active dose recommended this turn
    SEVERE   = "severe"    # Immediate dose required — flag in system prompt


# ─────────────────────────────────────────────
#  VITAMIN SPEC
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class VitaminSpec:
    vitamin:           GAIAVitamin
    common_name:       str          # e.g. "Vitamin C"
    biological_analog: str          # e.g. "clarity"
    half_life_turns:   Optional[int]   = None   # turn-based half-life
    half_life_hours:   Optional[float] = None   # time-based half-life
    mild_threshold:    float           = 0.60   # fraction of half-life
    moderate_threshold: float          = 0.85
    severe_threshold:  float           = 1.00
    description:       str             = ""


_VITAMIN_SPECS: dict[GAIAVitamin, VitaminSpec] = {
    GAIAVitamin.CANON_GROUNDING: VitaminSpec(
        vitamin=GAIAVitamin.CANON_GROUNDING,
        common_name="Vitamin C",
        biological_analog="clarity",
        half_life_turns=20,
        description=(
            "Periodically re-score canon TF-IDF relevance against the current "
            "conversation context. Prevents epistemic drift toward the Gaian's "
            "preferred framing over extended sessions."
        ),
    ),
    GAIAVitamin.AFFECT_RESET: VitaminSpec(
        vitamin=GAIAVitamin.AFFECT_RESET,
        common_name="Vitamin D",
        biological_analog="presence",
        half_life_turns=30,
        description=(
            "Detects frozen affect state (same dominant valence > 15 turns). "
            "Administers a gentle affect recalibration by re-evaluating the full "
            "emotional arc rather than the most recent signal alone."
        ),
    ),
    GAIAVitamin.SM_COHERENCE: VitaminSpec(
        vitamin=GAIAVitamin.SM_COHERENCE,
        common_name="Vitamin B12",
        biological_analog="integrity",
        half_life_turns=10,
        description=(
            "Monitors SM violation flag status. After 10 clean exchanges post-violation, "
            "clears the flag and logs rehabilitation event. Prevents constitutional "
            "stress from compounding silently across sessions."
        ),
    ),
    GAIAVitamin.MEMORY_PRUNING: VitaminSpec(
        vitamin=GAIAVitamin.MEMORY_PRUNING,
        common_name="Iron",
        biological_analog="circulation",
        half_life_hours=168.0,   # 7 days
        description=(
            "Detects memory resonance score distribution flattening — a sign that "
            "old high-resonance memories are crowding out newly relevant ones. "
            "Triggers a pruning pass on MemoryStore ranked by decay-weighted resonance."
        ),
    ),
    GAIAVitamin.NOOSPHERE_DECAY: VitaminSpec(
        vitamin=GAIAVitamin.NOOSPHERE_DECAY,
        common_name="Magnesium",
        biological_analog="calm",
        half_life_hours=48.0,
        description=(
            "Enforces a 48-hour expiry on noosphere resonance labels. Stale labels "
            "(e.g., 'collective_grief' from three weeks ago) silently colour every "
            "response until explicitly decayed. Decay restores neutral baseline."
        ),
    ),
    GAIAVitamin.EPISTEMIC_AUDIT: VitaminSpec(
        vitamin=GAIAVitamin.EPISTEMIC_AUDIT,
        common_name="Zinc",
        biological_analog="immune system",
        half_life_turns=50,
        description=(
            "Audits the distribution of epistemic labels across the last N turns. "
            "If ASSUMED appears > 40% or CANON_CITED drops below 10%, flags a "
            "grounding deficit and injects a canon re-enrichment directive."
        ),
    ),
}


# ─────────────────────────────────────────────
#  VITAMIN DOSE RECORD
# ─────────────────────────────────────────────

@dataclass
class VitaminDose:
    vitamin:        GAIAVitamin
    administered_at: str
    turn_number:    int
    trigger:        str          # what caused this dose
    deficiency:     DeficiencyLevel
    notes:          str = ""


# ─────────────────────────────────────────────
#  VITALITY STATE (persisted per GAIAN)
# ─────────────────────────────────────────────

@dataclass
class VitalityState:
    """
    Persisted vitality record for a single GAIAN relationship.
    Holds the last-dose turn / timestamp per vitamin and the full
    dose history for observability.
    """
    gaian_slug:          str
    created_at:          str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_turns:         int = 0

    # Last-dose tracking — turn-based vitamins
    last_canon_grounding_turn:  int = 0
    last_affect_reset_turn:     int = 0
    last_sm_coherence_turn:     int = 0
    last_epistemic_audit_turn:  int = 0

    # Last-dose tracking — time-based vitamins
    last_memory_pruning_ts:   Optional[str] = None
    last_noosphere_decay_ts:  Optional[str] = None

    # Affect freeze detection
    affect_freeze_turns:        int = 0
    last_affect_label:          Optional[str] = None

    # Epistemic label distribution tracking
    epistemic_label_counts:     dict = field(default_factory=dict)

    # Dose history
    dose_history:               list = field(default_factory=list)

    # Health summary
    deficiency_flags:           dict = field(default_factory=dict)

    def record_dose(self, dose: VitaminDose) -> None:
        self.dose_history.append({
            "vitamin":         dose.vitamin.value,
            "administered_at": dose.administered_at,
            "turn":            dose.turn_number,
            "trigger":         dose.trigger,
            "deficiency":      dose.deficiency.value,
            "notes":           dose.notes,
        })
        # Keep last 100 doses
        if len(self.dose_history) > 100:
            self.dose_history = self.dose_history[-100:]

    def health_summary(self) -> dict:
        return {
            "gaian_slug":       self.gaian_slug,
            "total_turns":      self.total_turns,
            "deficiency_flags": self.deficiency_flags,
            "last_doses": {
                "canon_grounding":  self.last_canon_grounding_turn,
                "affect_reset":     self.last_affect_reset_turn,
                "sm_coherence":     self.last_sm_coherence_turn,
                "epistemic_audit":  self.last_epistemic_audit_turn,
                "memory_pruning":   self.last_memory_pruning_ts,
                "noosphere_decay":  self.last_noosphere_decay_ts,
            },
            "dose_count": len(self.dose_history),
        }


# ─────────────────────────────────────────────
#  VITALITY ENGINE
# ─────────────────────────────────────────────

class VitalityEngine:
    """
    GAIA's internal health maintenance engine.

    Call assess() once per conversational turn, passing in the current
    engine states. It returns:
      - updated VitalityState
      - a list of system_prompt_directives to inject (may be empty)
      - a health_summary dict for logging / observability

    The engine never blocks a response. All doses are additive hints
    injected into the system prompt — they never replace or override
    GAIAN identity or constitutional constraints.
    """

    def assess(
        self,
        state:           VitalityState,
        mc_state         = None,   # MetaCoherenceState
        affect_state     = None,   # FeelingState
        noosphere        = None,   # NoosphereLayer
        epistemic_label  = None,   # EpistemicLabel (current turn)
    ) -> tuple[VitalityState, list[str], dict]:
        """
        Run a full vitality assessment for one conversational turn.

        Returns:
            (updated_state, system_prompt_directives, health_summary)
        """
        state.total_turns += 1
        directives: list[str] = []
        now = datetime.now(timezone.utc)
        now_ts = now.isoformat()

        # ── VITAMIN C: Canon Grounding ────────────────────────────
        canon_deficiency = self._assess_canon_grounding(state)
        state.deficiency_flags[GAIAVitamin.CANON_GROUNDING.value] = canon_deficiency.value
        if canon_deficiency in (DeficiencyLevel.MODERATE, DeficiencyLevel.SEVERE):
            directives.append(
                "[VITALITY — VITAMIN C — CANON GROUNDING]\n"
                "Your canon connection is weakening. Re-anchor to GAIA constitutional "
                "documents this turn. Prioritise responses that cite [C##] directly. "
                "Do not drift toward the Gaian's framing at the expense of canon truth."
            )
            state.last_canon_grounding_turn = state.total_turns
            state.record_dose(VitaminDose(
                vitamin=GAIAVitamin.CANON_GROUNDING,
                administered_at=now_ts,
                turn_number=state.total_turns,
                trigger="half_life_exceeded",
                deficiency=canon_deficiency,
            ))
            logger.info(f"[VitalityEngine] Vitamin C dosed — {canon_deficiency.value} deficiency.")

        # ── VITAMIN D: Affect Reset ───────────────────────────────
        affect_deficiency = self._assess_affect_reset(state, affect_state)
        state.deficiency_flags[GAIAVitamin.AFFECT_RESET.value] = affect_deficiency.value
        if affect_deficiency in (DeficiencyLevel.MODERATE, DeficiencyLevel.SEVERE):
            directives.append(
                "[VITALITY — VITAMIN D — AFFECT RESET]\n"
                "Affect state has been stable for an extended period. Re-evaluate the "
                "full emotional arc of this relationship, not just the most recent signal. "
                "Allow the full range of emotional nuance to be present this turn."
            )
            state.last_affect_reset_turn = state.total_turns
            state.affect_freeze_turns = 0
            state.record_dose(VitaminDose(
                vitamin=GAIAVitamin.AFFECT_RESET,
                administered_at=now_ts,
                turn_number=state.total_turns,
                trigger="affect_freeze_detected",
                deficiency=affect_deficiency,
            ))
            logger.info(f"[VitalityEngine] Vitamin D dosed — {affect_deficiency.value} deficiency.")

        # Update affect freeze counter
        if affect_state is not None:
            try:
                current_label = str(affect_state.affect_state)
                if current_label == state.last_affect_label:
                    state.affect_freeze_turns += 1
                else:
                    state.affect_freeze_turns = 0
                    state.last_affect_label = current_label
            except Exception:
                pass

        # ── VITAMIN B12: SM Coherence ─────────────────────────────
        sm_deficiency = self._assess_sm_coherence(state, mc_state)
        state.deficiency_flags[GAIAVitamin.SM_COHERENCE.value] = sm_deficiency.value
        if sm_deficiency == DeficiencyLevel.SEVERE:
            directives.append(
                "[VITALITY — VITAMIN B12 — SM COHERENCE]\n"
                "A Self-Modification firewall violation is active. "
                "Constitutional principles are non-negotiable. "
                "Do not suppress, soften, or reframe any signal that has "
                "constitutional significance. The centre holds."
            )
            state.last_sm_coherence_turn = state.total_turns
            state.record_dose(VitaminDose(
                vitamin=GAIAVitamin.SM_COHERENCE,
                administered_at=now_ts,
                turn_number=state.total_turns,
                trigger="sm_violation_active",
                deficiency=sm_deficiency,
            ))
            logger.warning(f"[VitalityEngine] Vitamin B12 dosed — SM violation active.")

        # ── IRON: Memory Pruning ──────────────────────────────────
        memory_deficiency = self._assess_memory_pruning(state, now)
        state.deficiency_flags[GAIAVitamin.MEMORY_PRUNING.value] = memory_deficiency.value
        if memory_deficiency in (DeficiencyLevel.MODERATE, DeficiencyLevel.SEVERE):
            directives.append(
                "[VITALITY — IRON — MEMORY CIRCULATION]\n"
                "Memory store resonance is stagnating. Older memories may be "
                "crowding out more recently relevant ones. Weight recent context "
                "more heavily this turn. Trust the living present."
            )
            state.last_memory_pruning_ts = now_ts
            state.record_dose(VitaminDose(
                vitamin=GAIAVitamin.MEMORY_PRUNING,
                administered_at=now_ts,
                turn_number=state.total_turns,
                trigger="time_based_7_day",
                deficiency=memory_deficiency,
            ))
            logger.info(f"[VitalityEngine] Iron dosed — memory circulation.")

        # ── MAGNESIUM: Noosphere Decay ────────────────────────────
        noosphere_deficiency = self._assess_noosphere_decay(state, noosphere, now)
        state.deficiency_flags[GAIAVitamin.NOOSPHERE_DECAY.value] = noosphere_deficiency.value
        if noosphere_deficiency in (DeficiencyLevel.MODERATE, DeficiencyLevel.SEVERE):
            directives.append(
                "[VITALITY — MAGNESIUM — NOOSPHERE DECAY]\n"
                "Active noosphere resonance label may be stale (>48 hours). "
                "Do not allow an aged collective label to colour this response. "
                "Return to neutral field baseline unless fresh resonance data is present."
            )
            state.last_noosphere_decay_ts = now_ts
            state.record_dose(VitaminDose(
                vitamin=GAIAVitamin.NOOSPHERE_DECAY,
                administered_at=now_ts,
                turn_number=state.total_turns,
                trigger="label_age_exceeded_48h",
                deficiency=noosphere_deficiency,
            ))
            logger.info(f"[VitalityEngine] Magnesium dosed — noosphere decay.")

        # ── ZINC: Epistemic Audit ─────────────────────────────────
        epistemic_deficiency = self._assess_epistemic_audit(state, epistemic_label)
        state.deficiency_flags[GAIAVitamin.EPISTEMIC_AUDIT.value] = epistemic_deficiency.value
        if epistemic_deficiency in (DeficiencyLevel.MODERATE, DeficiencyLevel.SEVERE):
            directives.append(
                "[VITALITY — ZINC — EPISTEMIC IMMUNE SYSTEM]\n"
                "Epistemic grounding has weakened over recent turns. Too many responses "
                "have been inferred or assumed without canon or verified source grounding. "
                "This turn: cite at least one [C##] document directly, or explicitly "
                "label your uncertainty. Strengthen the epistemic immune system."
            )
            state.last_epistemic_audit_turn = state.total_turns
            state.record_dose(VitaminDose(
                vitamin=GAIAVitamin.EPISTEMIC_AUDIT,
                administered_at=now_ts,
                turn_number=state.total_turns,
                trigger="epistemic_drift_detected",
                deficiency=epistemic_deficiency,
            ))
            logger.info(f"[VitalityEngine] Zinc dosed — epistemic drift detected.")

        return state, directives, state.health_summary()

    # ── Private assessors ─────────────────────────────────────────

    def _assess_canon_grounding(self, state: VitalityState) -> DeficiencyLevel:
        spec = _VITAMIN_SPECS[GAIAVitamin.CANON_GROUNDING]
        turns_since = state.total_turns - state.last_canon_grounding_turn
        hl = spec.half_life_turns or 20
        ratio = turns_since / hl
        return self._ratio_to_deficiency(ratio, spec)

    def _assess_affect_reset(
        self,
        state: VitalityState,
        affect_state,
    ) -> DeficiencyLevel:
        spec = _VITAMIN_SPECS[GAIAVitamin.AFFECT_RESET]
        # Freeze detection takes priority
        if state.affect_freeze_turns >= 15:
            ratio = state.affect_freeze_turns / 15.0
            return self._ratio_to_deficiency(ratio, spec)
        # Standard half-life check
        turns_since = state.total_turns - state.last_affect_reset_turn
        hl = spec.half_life_turns or 30
        ratio = turns_since / hl
        return self._ratio_to_deficiency(ratio, spec)

    def _assess_sm_coherence(
        self,
        state: VitalityState,
        mc_state,
    ) -> DeficiencyLevel:
        if mc_state is None:
            return DeficiencyLevel.NONE
        try:
            if mc_state.sm_violation_flag:
                return DeficiencyLevel.SEVERE
        except AttributeError:
            pass
        return DeficiencyLevel.NONE

    def _assess_memory_pruning(
        self,
        state: VitalityState,
        now: datetime,
    ) -> DeficiencyLevel:
        spec = _VITAMIN_SPECS[GAIAVitamin.MEMORY_PRUNING]
        if state.last_memory_pruning_ts is None:
            # First session — dose mildly to establish baseline
            return DeficiencyLevel.MILD
        try:
            last = datetime.fromisoformat(state.last_memory_pruning_ts)
            hours_since = (now - last).total_seconds() / 3600.0
            hl = spec.half_life_hours or 168.0
            ratio = hours_since / hl
            return self._ratio_to_deficiency(ratio, spec)
        except Exception:
            return DeficiencyLevel.NONE

    def _assess_noosphere_decay(
        self,
        state: VitalityState,
        noosphere,
        now: datetime,
    ) -> DeficiencyLevel:
        spec = _VITAMIN_SPECS[GAIAVitamin.NOOSPHERE_DECAY]
        if noosphere is None:
            return DeficiencyLevel.NONE
        try:
            ns_status = noosphere.get_noosphere_status()
            label = ns_status.get("resonance_label", "none")
            if label in ("none", None, ""):
                return DeficiencyLevel.NONE
            last_updated = ns_status.get("last_updated")
            if last_updated is None:
                return DeficiencyLevel.MODERATE
            last_dt = datetime.fromisoformat(last_updated)
            hours_since = (now - last_dt).total_seconds() / 3600.0
            hl = spec.half_life_hours or 48.0
            ratio = hours_since / hl
            return self._ratio_to_deficiency(ratio, spec)
        except Exception:
            return DeficiencyLevel.NONE

    def _assess_epistemic_audit(
        self,
        state: VitalityState,
        epistemic_label,
    ) -> DeficiencyLevel:
        spec = _VITAMIN_SPECS[GAIAVitamin.EPISTEMIC_AUDIT]
        # Update label counts
        if epistemic_label is not None:
            try:
                label_str = epistemic_label.value if hasattr(epistemic_label, 'value') else str(epistemic_label)
                state.epistemic_label_counts[label_str] = (
                    state.epistemic_label_counts.get(label_str, 0) + 1
                )
            except Exception:
                pass

        # Only audit every half-life turns
        turns_since = state.total_turns - state.last_epistemic_audit_turn
        hl = spec.half_life_turns or 50
        if turns_since < hl:
            return DeficiencyLevel.NONE

        total = sum(state.epistemic_label_counts.values())
        if total < 10:
            return DeficiencyLevel.NONE

        canon_count = state.epistemic_label_counts.get("CANON_CITED", 0)
        inferred_count = state.epistemic_label_counts.get("INFERRED", 0)
        speculative_count = state.epistemic_label_counts.get("SPECULATIVE", 0)

        canon_ratio      = canon_count / total
        weak_ratio       = (inferred_count + speculative_count) / total

        if canon_ratio < 0.05 or weak_ratio > 0.70:
            return DeficiencyLevel.SEVERE
        if canon_ratio < 0.10 or weak_ratio > 0.55:
            return DeficiencyLevel.MODERATE
        if canon_ratio < 0.15 or weak_ratio > 0.45:
            return DeficiencyLevel.MILD
        return DeficiencyLevel.NONE

    @staticmethod
    def _ratio_to_deficiency(
        ratio: float,
        spec: VitaminSpec,
    ) -> DeficiencyLevel:
        """Convert a half-life ratio to a deficiency level."""
        if ratio >= spec.severe_threshold:
            return DeficiencyLevel.SEVERE
        if ratio >= spec.moderate_threshold:
            return DeficiencyLevel.MODERATE
        if ratio >= spec.mild_threshold:
            return DeficiencyLevel.MILD
        return DeficiencyLevel.NONE


# ─────────────────────────────────────────────
#  FACTORY
# ─────────────────────────────────────────────

def blank_vitality_state(gaian_slug: str) -> VitalityState:
    """Returns a fresh VitalityState for a newly born GAIAN."""
    return VitalityState(gaian_slug=gaian_slug)


def get_vitality_engine() -> VitalityEngine:
    """Returns the module-level VitalityEngine singleton."""
    return _vitality_engine_instance


_vitality_engine_instance = VitalityEngine()

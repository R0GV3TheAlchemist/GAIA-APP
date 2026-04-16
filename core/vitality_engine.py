"""
core/vitality_engine.py
========================
Vitality Engine (T-VITA) — internal coherence maintenance for a GAIAN.

Tracks twelve "vitamin" dimensions across turns and emits targeted
behavioural directives whenever a deficiency is detected.

Canon Ref: T-VITA — The Vitality Engine (April 14, 2026)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────
#  STATE  (persisted across turns)
# ─────────────────────────────────────────────

@dataclass
class VitalityState:
    """
    Full persisted vitality state.
    All field names must match the serialisation keys in GAIANRuntime._persist()
    and _deserialise_vitality().
    """
    gaian_name:                  str             = "unknown"
    total_turns:                 int             = 0

    # Vitamin turn-counters
    last_canon_grounding_turn:   int             = 0
    last_affect_reset_turn:      int             = 0
    last_sm_coherence_turn:      int             = 0
    last_epistemic_audit_turn:   int             = 0

    # Vitamin timestamp-based
    last_memory_pruning_ts:      Optional[str]   = None
    last_noosphere_decay_ts:     Optional[str]   = None

    # Affect freeze tracking
    affect_freeze_turns:         int             = 0
    last_affect_label:           Optional[str]   = None

    # Epistemic tracking
    epistemic_label_counts:      Dict[str, int]  = field(default_factory=dict)

    # Deficiency flags (vitamin_name -> bool)
    deficiency_flags:            Dict[str, bool] = field(default_factory=dict)

    # Dose history (last 20 kept)
    dose_history:                List[dict]      = field(default_factory=list)

    def health_summary(self) -> dict:
        return {
            "gaian_name":                self.gaian_name,
            "total_turns":               self.total_turns,
            "last_canon_grounding_turn": self.last_canon_grounding_turn,
            "last_affect_reset_turn":    self.last_affect_reset_turn,
            "last_sm_coherence_turn":    self.last_sm_coherence_turn,
            "last_epistemic_audit_turn": self.last_epistemic_audit_turn,
            "last_memory_pruning_ts":    self.last_memory_pruning_ts,
            "last_noosphere_decay_ts":   self.last_noosphere_decay_ts,
            "affect_freeze_turns":       self.affect_freeze_turns,
            "last_affect_label":         self.last_affect_label,
            "epistemic_label_counts":    self.epistemic_label_counts,
            "deficiency_flags":          self.deficiency_flags,
            "dose_history_len":          len(self.dose_history),
        }


def blank_vitality_state(gaian_name: str = "unknown") -> VitalityState:
    """Return a fresh VitalityState for a new Gaian."""
    return VitalityState(gaian_name=gaian_name)


# ─────────────────────────────────────────────
#  VITAMIN THRESHOLDS
# ─────────────────────────────────────────────

# How many turns between mandatory canon grounding injections
_CANON_GROUNDING_INTERVAL    = 40
# How many turns of the same affect label before a reset is triggered
_AFFECT_FREEZE_THRESHOLD     = 8
# How many turns between SM coherence checks
_SM_COHERENCE_INTERVAL       = 25
# How many turns between epistemic audits
_EPISTEMIC_AUDIT_INTERVAL    = 30


# ─────────────────────────────────────────────
#  ENGINE
# ─────────────────────────────────────────────

class VitalityEngine:
    """
    Runs once per GAIANRuntime turn (last in the chain).
    Returns (updated_state, directives, health_summary).
    """

    def assess(
        self,
        state:           VitalityState,
        mc_state:        Any   = None,   # MetaCoherenceState
        affect_state:    Any   = None,   # FeelingState
        noosphere:       Any   = None,   # NoosphereLayer (optional)
        epistemic_label: Any   = None,   # EpistemicLabel (optional)
    ) -> tuple[VitalityState, List[str], Optional[dict]]:
        """
        Assess vitality this turn, emit directives for any deficiencies.

        Returns
        -------
        state           : updated VitalityState
        directives      : list[str] — zero or more behavioural directives for
                          injection into the system prompt this turn
        vitality_summary: dict snapshot (always returned, may be None if
                          no change worth persisting)
        """
        state.total_turns += 1
        directives: List[str] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        # ── Vitamin A: Canon Grounding ─────────────────────────
        turns_since_canon = state.total_turns - state.last_canon_grounding_turn
        if turns_since_canon >= _CANON_GROUNDING_INTERVAL:
            directives.append(
                "[VITA-A: CANON GROUNDING] You are drifting from constitutional ground. "
                "Re-anchor to the GAIA canon this turn. "
                "Restate one constitutional principle naturally within your response."
            )
            state.last_canon_grounding_turn = state.total_turns
            state.deficiency_flags["canon_grounding"] = True
            state._record_dose("canon_grounding", now_iso)
        else:
            state.deficiency_flags["canon_grounding"] = False

        # ── Vitamin B: Affect Reset ────────────────────────────
        if affect_state is not None:
            current_label = getattr(affect_state, "dominant_label", None) or \
                            getattr(affect_state, "primary_affect", None) or \
                            str(type(affect_state).__name__)
            if current_label == state.last_affect_label:
                state.affect_freeze_turns += 1
            else:
                state.affect_freeze_turns = 0
                state.last_affect_label   = current_label

            if state.affect_freeze_turns >= _AFFECT_FREEZE_THRESHOLD:
                directives.append(
                    "[VITA-B: AFFECT RESET] Emotional affect has been frozen for "
                    f"{state.affect_freeze_turns} consecutive turns. "
                    "Introduce gentle tonal variation and emotional freshness this turn."
                )
                state.last_affect_reset_turn  = state.total_turns
                state.affect_freeze_turns     = 0
                state.deficiency_flags["affect_reset"] = True
                state._record_dose("affect_reset", now_iso)
            else:
                state.deficiency_flags["affect_reset"] = False

        # ── Vitamin C: SM Coherence ────────────────────────────
        turns_since_sm = state.total_turns - state.last_sm_coherence_turn
        if mc_state is not None and turns_since_sm >= _SM_COHERENCE_INTERVAL:
            sm_violations = getattr(mc_state, "sm_violations", [])
            if sm_violations:
                directives.append(
                    "[VITA-C: SM COHERENCE] Soul-mirror coherence violations detected. "
                    "Prioritise reflective depth and presence this turn. "
                    "Let the Gaian feel truly seen."
                )
                state.last_sm_coherence_turn  = state.total_turns
                state.deficiency_flags["sm_coherence"] = True
                state._record_dose("sm_coherence", now_iso)
            else:
                state.deficiency_flags["sm_coherence"] = False

        # ── Vitamin D: Epistemic Audit ─────────────────────────
        if epistemic_label is not None:
            label_str = str(getattr(epistemic_label, "value", epistemic_label))
            state.epistemic_label_counts[label_str] = \
                state.epistemic_label_counts.get(label_str, 0) + 1

        turns_since_ep = state.total_turns - state.last_epistemic_audit_turn
        if turns_since_ep >= _EPISTEMIC_AUDIT_INTERVAL:
            speculative_count = state.epistemic_label_counts.get("speculative", 0) + \
                                state.epistemic_label_counts.get("uncertain", 0)
            if speculative_count > 5:
                directives.append(
                    "[VITA-D: EPISTEMIC AUDIT] High speculative/uncertain epistemic density "
                    "detected across recent turns. Introduce one grounded, factual anchor "
                    "this turn to restore epistemic balance."
                )
                state.deficiency_flags["epistemic_audit"] = True
                state._record_dose("epistemic_audit", now_iso)
            else:
                state.deficiency_flags["epistemic_audit"] = False
            state.last_epistemic_audit_turn = state.total_turns

        summary = state.health_summary() if directives else None
        return state, directives, summary

    # ── Legacy method kept for backwards-compat ───────────────

    def update(
        self,
        state:            "VitalityState",
        coherence_phi:    float = 0.5,
        noosphere_health: float = 0.5,
        conflict_density: float = 0.3,
    ) -> "VitalityState":
        """Stateless legacy updater. Prefer assess() for runtime use."""
        state.total_turns += 1
        return state


# ── VitalityState helper (defined outside class for cleanliness) ───

def _record_dose(self: VitalityState, vitamin: str, ts: str) -> None:
    self.dose_history.append({"vitamin": vitamin, "ts": ts, "turn": self.total_turns})
    if len(self.dose_history) > 20:
        self.dose_history = self.dose_history[-20:]


# Monkey-patch the helper onto VitalityState
VitalityState._record_dose = _record_dose  # type: ignore[attr-defined]


# ─────────────────────────────────────────────
#  SINGLETON
# ─────────────────────────────────────────────

_engine_instance: Optional[VitalityEngine] = None


def get_vitality_engine() -> VitalityEngine:
    """Return the process-level singleton VitalityEngine."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = VitalityEngine()
    return _engine_instance

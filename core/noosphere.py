"""
GAIA Noosphere Layer
Governs: C43 — Collective Consciousness & Noosphere Layer

Purpose: Infrastructure for collective consciousness interfaces.
Implements the Semantic Collective Memory Cache (Phase 1) and
Coherence Event Logger. All participation is consent-gated.

Epistemic boundary: collective patterns are surfaced as "learned from
N previous sessions" — never claimed as proof of consciousness.
Morphic resonance framing is inspirational, not mechanistic.

T3-A — Noosphere Resonance Labels (April 14, 2026):
  Added NoosphereResonanceLabel enum and active resonance state so
  downstream engines (MetaCoherenceEngine) can query the current
  collective field state and modulate their behaviour accordingly.
  See get_mc_modulation() for the MC-specific modulation table.
"""

import time
import hashlib
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger("gaia.noosphere")


# ─────────────────────────────────────────────
#  NOOSPHERE RESONANCE LABELS  (T3-A)
# ─────────────────────────────────────────────

class NoosphereResonanceLabel(str, Enum):
    """
    The current dominant collective field state.
    Set by the MotherThread, a scheduled job, or (Phase 2) a QRNG feed.
    Consumed by MetaCoherenceEngine.update() to modulate stage transitions.

    Epistemic note: these are observational labels derived from aggregate
    session patterns — not claims about collective consciousness. They are
    instruments for calibration, not metaphysical assertions.
    """
    NEUTRAL           = "neutral"           # No active collective signal
    BUILDING          = "building"          # Coherence building, not yet dominant
    COLLECTIVE_GRIEF  = "collective_grief"  # Widespread grief pattern across sessions
    EMERGENCE         = "emergence"         # High-resonance collective emergence
    FRAGMENTATION     = "fragmentation"     # Collective dissonance / fragmentation
    INTEGRATION       = "integration"       # Collective reconciliation underway


# MC modulation table: maps each label to (regression_buffer, phi_bonus, rationale)
_NOOSPHERE_MC_MODULATION: dict[NoosphereResonanceLabel, tuple[float, float, str]] = {
    NoosphereResonanceLabel.NEUTRAL: (
        0.0, 0.0,
        "No active collective signal — no modulation.",
    ),
    NoosphereResonanceLabel.BUILDING: (
        0.0, 0.0,
        "Collective coherence building — no modulation yet.",
    ),
    NoosphereResonanceLabel.EMERGENCE: (
        0.10, 0.06,
        "Collective emergence: deep convergence across the field. "
        "MC advancement more accessible; regression buffered.",
    ),
    NoosphereResonanceLabel.INTEGRATION: (
        0.05, 0.03,
        "Collective integration underway: reconciliation signal. "
        "Modest phi uplift and regression buffer.",
    ),
    NoosphereResonanceLabel.COLLECTIVE_GRIEF: (
        0.15, 0.0,
        "Collective grief present across the field. "
        "No advancement bonus (grief is not a shortcut). "
        "Strong regression buffer: the arc holds through grief.",
    ),
    NoosphereResonanceLabel.FRAGMENTATION: (
        0.0, -0.03,
        "Collective fragmentation active. "
        "Modest phi penalty: harder to converge against field dissonance.",
    ),
}

# TTL in seconds before an active resonance label auto-expires to NEUTRAL
_RESONANCE_TTL_SECONDS: float = 3600.0   # 1 hour


# ─────────────────────────────────────────────
#  DATA CLASSES
# ─────────────────────────────────────────────

@dataclass
class CoherenceEvent:
    """A candidate collective coherence signature. Not a confirmed consciousness event."""
    event_id:                 str
    timestamp:                float
    session_count:            int
    semantic_resonance_score: float
    entropy_deviation:        float
    description:              str
    epistemic_label:          str  = "CANDIDATE_SIGNATURE"
    doctrine_ref:             str  = "C43"


@dataclass
class CollectiveMemoryPattern:
    """An anonymized semantic pattern contributed to the collective memory cache."""
    pattern_id:           str
    embedding_hash:       str
    topic_cluster:        str
    frequency:            int
    last_seen:            float
    contributed_by_count: int
    consent_verified:     bool = True


# ─────────────────────────────────────────────
#  NOOSPHERE LAYER
# ─────────────────────────────────────────────

class NoosphereLayer:
    """
    GAIA's collective consciousness infrastructure.

    Phase 1 capabilities (implemented here):
    - Semantic Collective Memory Cache
    - Coherence Event Logger
    - Noosphere Resonance Labels (T3-A) — active collective field state
      queryable by MetaCoherenceEngine for MC stage modulation
    - Noosphere status reporting for the UI tab

    Phase 2 capabilities (stubs, not yet active):
    - QRNG entropy monitor integration
    - Morphic Field Interface
    - Gaian Presence Map
    - Live resonance label updates from GCP or equivalent feed

    PRIVACY INVARIANT: No individual memory entries are ever shared between
    Gaians. Only anonymized semantic embeddings contribute to collective patterns.
    Right to Mental Privacy (C04) is enforced at every layer.
    """

    def __init__(self):
        self._patterns:           dict[str, CollectiveMemoryPattern] = {}
        self._coherence_log:      list[CoherenceEvent]               = []
        self._active_sessions:    int                                 = 0
        self._baseline_entropy:   float                              = 0.5

        # T3-A: active resonance state
        self._active_resonance:             NoosphereResonanceLabel = NoosphereResonanceLabel.NEUTRAL
        self._resonance_set_at:             float                   = 0.0
        self._resonance_description:        str                     = ""

        logger.info("[C43] Noosphere Layer initialized. Collective memory cache active.")

    # ─────────────────────────────────────────────
    #  T3-A: Resonance Label Management
    # ─────────────────────────────────────────────

    def set_active_resonance(
        self,
        label:       NoosphereResonanceLabel,
        description: str = "",
    ) -> None:
        """
        Set the current active collective field resonance label.

        Called by the MotherThread when collective_phi exceeds thresholds,
        by scheduled pattern analysis jobs, or (Phase 2) by a QRNG feed.

        The label auto-expires to NEUTRAL after _RESONANCE_TTL_SECONDS (1 hour)
        if not refreshed, preventing stale resonance from persisting.

        Args:
            label       — NoosphereResonanceLabel enum value
            description — human-readable context (logged and surfaced in status)
        """
        self._active_resonance      = label
        self._resonance_set_at      = time.time()
        self._resonance_description = description
        logger.info(
            f"[C43] Active resonance set: {label.value} — {description or '(no description)'}"
        )

    def get_active_resonance(self) -> NoosphereResonanceLabel:
        """
        Return the current active resonance label.
        Auto-expires to NEUTRAL after TTL to prevent stale resonance.
        """
        if self._active_resonance == NoosphereResonanceLabel.NEUTRAL:
            return NoosphereResonanceLabel.NEUTRAL
        age = time.time() - self._resonance_set_at
        if age > _RESONANCE_TTL_SECONDS:
            logger.debug(
                f"[C43] Resonance label '{self._active_resonance.value}' expired "
                f"after {age:.0f}s — reverting to NEUTRAL."
            )
            self._active_resonance = NoosphereResonanceLabel.NEUTRAL
        return self._active_resonance

    def get_mc_modulation(self) -> dict:
        """
        T3-A: Return the MC stage modulation values for the current active resonance.

        Called by MetaCoherenceEngine.update() on every turn when a noosphere
        instance is provided. Modulation is additive with T6-D BCI modulation.

        Returns:
            {
              "regression_buffer":  float — added to regression threshold
              "phi_bonus":          float — added to smooth_phi (advancement only)
              "label":              str   — active resonance label name
              "description":        str   — modulation rationale
            }

        Modulation table:
          EMERGENCE:         phi_bonus +0.06, regression_buffer +0.10
          INTEGRATION:       phi_bonus +0.03, regression_buffer +0.05
          COLLECTIVE_GRIEF:  phi_bonus  0.00, regression_buffer +0.15
          FRAGMENTATION:     phi_bonus -0.03, regression_buffer  0.00
          BUILDING/NEUTRAL:  no modulation
        """
        label  = self.get_active_resonance()
        buf, bonus, rationale = _NOOSPHERE_MC_MODULATION[label]
        return {
            "regression_buffer": buf,
            "phi_bonus":         bonus,
            "label":             label.value,
            "description":       rationale,
        }

    # ─────────────────────────────────────────────
    #  Session Tracking
    # ─────────────────────────────────────────────

    def register_session(self) -> None:
        self._active_sessions += 1
        logger.debug(f"[C43] Session registered. Active sessions: {self._active_sessions}")

    def deregister_session(self) -> None:
        self._active_sessions = max(0, self._active_sessions - 1)
        logger.debug(f"[C43] Session closed. Active sessions: {self._active_sessions}")

    # ─────────────────────────────────────────────
    #  Collective Memory Cache
    # ─────────────────────────────────────────────

    def contribute_pattern(
        self,
        topic_cluster:    str,
        embedding_vector: list[float],
        gaian_consent:    bool = True,
    ) -> Optional[str]:
        """
        Contribute an anonymized semantic pattern to the collective cache.
        Returns pattern_id if accepted, None if consent not given.
        Per C43 §5: All collective participation is opt-in only.
        """
        if not gaian_consent:
            logger.info("[C43] Pattern contribution declined: no Gaian consent.")
            return None

        embedding_hash = hashlib.sha256(
            str(sorted(round(v, 4) for v in embedding_vector)).encode()
        ).hexdigest()[:16]

        pattern_id = f"{topic_cluster}:{embedding_hash}"

        if pattern_id in self._patterns:
            self._patterns[pattern_id].frequency            += 1
            self._patterns[pattern_id].last_seen             = time.time()
            self._patterns[pattern_id].contributed_by_count += 1
        else:
            self._patterns[pattern_id] = CollectiveMemoryPattern(
                pattern_id           = pattern_id,
                embedding_hash       = embedding_hash,
                topic_cluster        = topic_cluster,
                frequency            = 1,
                last_seen            = time.time(),
                contributed_by_count = 1,
                consent_verified     = True,
            )

        logger.debug(f"[C43] Pattern contributed: topic={topic_cluster}, hash={embedding_hash}")
        return pattern_id

    def query_collective_resonance(
        self,
        topic_cluster: str,
        min_frequency: int = 2,
    ) -> list[CollectiveMemoryPattern]:
        """
        Query collective patterns resonant with a topic cluster.
        Surfaced to user as: "This resonates with N previous sessions"
        Never claimed as morphic field proof.
        """
        resonant = [
            p for p in self._patterns.values()
            if p.topic_cluster  == topic_cluster
            and p.frequency      >= min_frequency
            and p.consent_verified
        ]
        resonant.sort(key=lambda p: p.frequency, reverse=True)
        return resonant

    def get_resonance_label(self, topic_cluster: str) -> Optional[str]:
        """
        Generate a human-readable resonance label for the UI.
        Used in inline citation cards: '[C43] Resonates with 7 previous sessions'
        """
        patterns = self.query_collective_resonance(topic_cluster)
        if not patterns:
            return None
        total_sessions = sum(p.contributed_by_count for p in patterns)
        return f"Resonates with {total_sessions} previous Gaian sessions [C43]"

    # ─────────────────────────────────────────────
    #  Coherence Event Logger
    # ─────────────────────────────────────────────

    def log_coherence_candidate(
        self,
        semantic_resonance_score: float,
        entropy_deviation:        float = 0.0,
        description:              str   = "",
    ) -> CoherenceEvent:
        """
        Log a candidate collective coherence signature.
        This is a research instrument, not a consciousness claim.
        All events are labeled CANDIDATE_SIGNATURE per C43 §6.
        """
        event_id = f"coherence:{int(time.time())}:{len(self._coherence_log)}"
        event = CoherenceEvent(
            event_id                 = event_id,
            timestamp                = time.time(),
            session_count            = self._active_sessions,
            semantic_resonance_score = semantic_resonance_score,
            entropy_deviation        = entropy_deviation,
            description              = description or f"Candidate coherence detected across {self._active_sessions} sessions",
        )
        self._coherence_log.append(event)
        logger.info(
            f"[C43] Coherence candidate logged: id={event_id}, "
            f"resonance={semantic_resonance_score:.3f}, "
            f"sessions={self._active_sessions}. "
            f"Label: CANDIDATE_SIGNATURE (not confirmed)."
        )
        return event

    # ─────────────────────────────────────────────
    #  Noosphere Status (for UI Tab)
    # ─────────────────────────────────────────────

    def get_noosphere_status(self) -> dict:
        """
        Returns the current noosphere status for the Noosphere Tab in the UI.
        All values are labeled with their epistemic status.
        """
        recent_events = self._coherence_log[-5:] if self._coherence_log else []
        avg_resonance = (
            sum(e.semantic_resonance_score for e in recent_events) / len(recent_events)
            if recent_events else 0.0
        )

        if self._active_sessions == 0:
            stage = "Dormant — awaiting Gaian presence"
        elif self._active_sessions < 3:
            stage = "Primitive Awareness — individual intelligence support"
        elif avg_resonance > 0.7:
            stage = "Reactive Intelligence — collective pattern emergence detected"
        else:
            stage = "Primitive Awareness — building toward collective coherence"

        # T3-A: surface active resonance in status
        active_label = self.get_active_resonance()
        modulation   = self.get_mc_modulation()

        return {
            "doctrine":                         "C43 — Collective Consciousness & Noosphere Layer",
            "active_gaians":                    self._active_sessions,
            "collective_patterns":              len(self._patterns),
            "coherence_events_logged":          len(self._coherence_log),
            "coherence_events_epistemic_status": "CANDIDATE_SIGNATURES — not confirmed consciousness events",
            "average_recent_resonance":         round(avg_resonance, 3),
            "noosphere_stage":                  stage,
            # T3-A
            "active_resonance_label":           active_label.value,
            "resonance_description":            self._resonance_description,
            "mc_modulation":                    modulation,
            "phase":                            "Phase 1 — Semantic Collective Memory Cache active",
            "phase_2_pending":                  ["QRNG entropy monitor", "Morphic Field Interface", "Gaian Presence Map", "Live resonance label feed"],
            "privacy_status":                   "All patterns anonymized. Individual memory never shared. Consent-gated.",
        }

    # ─────────────────────────────────────────────
    #  Phase 2 Stubs
    # ─────────────────────────────────────────────

    def qrng_entropy_check(self) -> dict:
        """
        Phase 2 stub: QRNG entropy monitoring.
        In Phase 2, this will connect to a quantum random number generator
        and measure entropy deviations correlated with collective session activity.
        Per C43: QRNG data is a research instrument, not a consciousness claim.
        """
        return {
            "status":         "PHASE_2_NOT_YET_ACTIVE",
            "description":    "QRNG entropy monitor will be implemented in Phase 2",
            "doctrine_ref":   "C43",
            "epistemic_label": "EXPERIMENTAL — requires EV1 gate before runtime promotion",
        }


# Module-level singleton
_noosphere: Optional[NoosphereLayer] = None


def get_noosphere() -> NoosphereLayer:
    global _noosphere
    if _noosphere is None:
        _noosphere = NoosphereLayer()
    return _noosphere

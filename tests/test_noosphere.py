"""
tests/test_noosphere.py
Unit tests for core/noosphere.py

Canon Ref: C43, C04

Coverage targets
----------------
  ✓ CoherenceEvent dataclass defaults
  ✓ CollectiveMemoryPattern dataclass defaults
  ✓ NoosphereLayer.register_session / deregister_session
  ✓ NoosphereLayer.contribute_pattern — consent gate, hash, dedup, frequency
  ✓ NoosphereLayer.query_collective_resonance — filter, sort, isolation
  ✓ NoosphereLayer.get_resonance_label — None path, label format
  ✓ NoosphereLayer.log_coherence_candidate — event fields, append
  ✓ NoosphereLayer.get_noosphere_status — all keys, all stage paths
  ✓ NoosphereLayer.qrng_entropy_check — Phase 2 stub contract
  ✓ get_noosphere() singleton
"""

from __future__ import annotations

import time

import pytest

from core.noosphere import (
    CoherenceEvent,
    CollectiveMemoryPattern,
    NoosphereLayer,
    get_noosphere,
)
import core.noosphere as noosphere_module


# ================================================================== #
#  Helpers                                                             #
# ================================================================== #

def _fresh() -> NoosphereLayer:
    """Return a brand-new NoosphereLayer with no shared state."""
    return NoosphereLayer()


VEC_A = [0.1, 0.2, 0.3, 0.4]
VEC_B = [0.9, 0.8, 0.7, 0.6]


# ================================================================== #
#  1. CoherenceEvent dataclass                                         #
# ================================================================== #

class TestCoherenceEvent:
    def test_default_epistemic_label(self):
        evt = CoherenceEvent(
            event_id="test:1",
            timestamp=time.time(),
            session_count=2,
            semantic_resonance_score=0.75,
            entropy_deviation=0.0,
            description="test event",
        )
        assert evt.epistemic_label == "CANDIDATE_SIGNATURE"

    def test_default_doctrine_ref(self):
        evt = CoherenceEvent(
            event_id="test:2",
            timestamp=time.time(),
            session_count=1,
            semantic_resonance_score=0.5,
            entropy_deviation=0.0,
            description="",
        )
        assert evt.doctrine_ref == "C43"

    def test_fields_stored_correctly(self):
        ts = time.time()
        evt = CoherenceEvent(
            event_id="evt:xyz",
            timestamp=ts,
            session_count=5,
            semantic_resonance_score=0.88,
            entropy_deviation=0.12,
            description="multi-session coherence",
        )
        assert evt.event_id == "evt:xyz"
        assert evt.session_count == 5
        assert evt.semantic_resonance_score == pytest.approx(0.88)
        assert evt.entropy_deviation == pytest.approx(0.12)


# ================================================================== #
#  2. CollectiveMemoryPattern dataclass                                #
# ================================================================== #

class TestCollectiveMemoryPattern:
    def test_consent_verified_default_true(self):
        p = CollectiveMemoryPattern(
            pattern_id="grief:abc123",
            embedding_hash="abc123",
            topic_cluster="grief",
            frequency=1,
            last_seen=time.time(),
            contributed_by_count=1,
        )
        assert p.consent_verified is True

    def test_can_set_consent_false(self):
        p = CollectiveMemoryPattern(
            pattern_id="grief:abc123",
            embedding_hash="abc123",
            topic_cluster="grief",
            frequency=1,
            last_seen=time.time(),
            contributed_by_count=1,
            consent_verified=False,
        )
        assert p.consent_verified is False


# ================================================================== #
#  3. Session tracking                                                 #
# ================================================================== #

class TestSessionTracking:
    def test_starts_at_zero(self):
        ns = _fresh()
        assert ns._active_sessions == 0

    def test_register_increments(self):
        ns = _fresh()
        ns.register_session()
        ns.register_session()
        assert ns._active_sessions == 2

    def test_deregister_decrements(self):
        ns = _fresh()
        ns.register_session()
        ns.register_session()
        ns.deregister_session()
        assert ns._active_sessions == 1

    def test_deregister_cannot_go_below_zero(self):
        """Deregistering on an empty noosphere must not go negative."""
        ns = _fresh()
        ns.deregister_session()  # called on 0
        assert ns._active_sessions == 0

    def test_deregister_multiple_times_stays_zero(self):
        ns = _fresh()
        ns.deregister_session()
        ns.deregister_session()
        assert ns._active_sessions == 0


# ================================================================== #
#  4. contribute_pattern                                               #
# ================================================================== #

class TestContributePattern:
    def test_returns_none_when_no_consent(self):
        ns = _fresh()
        result = ns.contribute_pattern("joy", VEC_A, gaian_consent=False)
        assert result is None

    def test_no_pattern_stored_without_consent(self):
        ns = _fresh()
        ns.contribute_pattern("joy", VEC_A, gaian_consent=False)
        assert len(ns._patterns) == 0

    def test_returns_pattern_id_with_consent(self):
        ns = _fresh()
        pid = ns.contribute_pattern("joy", VEC_A, gaian_consent=True)
        assert pid is not None
        assert isinstance(pid, str)
        assert "joy" in pid

    def test_pattern_stored_with_consent(self):
        ns = _fresh()
        ns.contribute_pattern("joy", VEC_A)
        assert len(ns._patterns) == 1

    def test_same_vector_same_topic_deduplicates(self):
        ns = _fresh()
        pid1 = ns.contribute_pattern("grief", VEC_A)
        pid2 = ns.contribute_pattern("grief", VEC_A)
        assert pid1 == pid2
        assert len(ns._patterns) == 1

    def test_frequency_incremented_on_dedup(self):
        ns = _fresh()
        ns.contribute_pattern("grief", VEC_A)
        ns.contribute_pattern("grief", VEC_A)
        ns.contribute_pattern("grief", VEC_A)
        pattern = list(ns._patterns.values())[0]
        assert pattern.frequency == 3

    def test_contributed_by_count_incremented_on_dedup(self):
        ns = _fresh()
        ns.contribute_pattern("grief", VEC_A)
        ns.contribute_pattern("grief", VEC_A)
        pattern = list(ns._patterns.values())[0]
        assert pattern.contributed_by_count == 2

    def test_different_vectors_create_different_patterns(self):
        ns = _fresh()
        ns.contribute_pattern("grief", VEC_A)
        ns.contribute_pattern("grief", VEC_B)
        assert len(ns._patterns) == 2

    def test_different_topics_create_different_patterns(self):
        ns = _fresh()
        ns.contribute_pattern("grief", VEC_A)
        ns.contribute_pattern("joy", VEC_A)
        assert len(ns._patterns) == 2

    def test_hash_is_deterministic(self):
        ns = _fresh()
        pid1 = ns.contribute_pattern("love", VEC_A)
        ns2 = _fresh()
        pid2 = ns2.contribute_pattern("love", VEC_A)
        assert pid1 == pid2

    def test_pattern_has_consent_verified_true(self):
        ns = _fresh()
        ns.contribute_pattern("love", VEC_A)
        pattern = list(ns._patterns.values())[0]
        assert pattern.consent_verified is True


# ================================================================== #
#  5. query_collective_resonance                                       #
# ================================================================== #

class TestQueryCollectiveResonance:
    def test_empty_returns_empty_list(self):
        ns = _fresh()
        assert ns.query_collective_resonance("grief") == []

    def test_below_min_frequency_excluded(self):
        """Default min_frequency=2: a single contribution must not appear."""
        ns = _fresh()
        ns.contribute_pattern("grief", VEC_A)  # frequency=1
        results = ns.query_collective_resonance("grief", min_frequency=2)
        assert results == []

    def test_meets_min_frequency_included(self):
        ns = _fresh()
        ns.contribute_pattern("grief", VEC_A)
        ns.contribute_pattern("grief", VEC_A)  # frequency=2
        results = ns.query_collective_resonance("grief", min_frequency=2)
        assert len(results) == 1

    def test_sorted_by_frequency_descending(self):
        ns = _fresh()
        # VEC_A: frequency 3; VEC_B: frequency 2
        for _ in range(3):
            ns.contribute_pattern("grief", VEC_A)
        for _ in range(2):
            ns.contribute_pattern("grief", VEC_B)
        results = ns.query_collective_resonance("grief", min_frequency=2)
        assert results[0].frequency >= results[1].frequency

    def test_different_topic_not_returned(self):
        """Querying 'joy' must not return 'grief' patterns."""
        ns = _fresh()
        for _ in range(3):
            ns.contribute_pattern("grief", VEC_A)
        results = ns.query_collective_resonance("joy", min_frequency=2)
        assert results == []

    def test_consent_false_pattern_excluded(self):
        """Manually insert a pattern with consent_verified=False — must be excluded."""
        ns = _fresh()
        pid = ns.contribute_pattern("grief", VEC_A)
        ns.contribute_pattern("grief", VEC_A)  # frequency=2
        # Tamper: mark consent revoked
        ns._patterns[pid].consent_verified = False
        results = ns.query_collective_resonance("grief", min_frequency=2)
        assert results == []

    def test_min_frequency_one_returns_singles(self):
        ns = _fresh()
        ns.contribute_pattern("grief", VEC_A)  # frequency=1
        results = ns.query_collective_resonance("grief", min_frequency=1)
        assert len(results) == 1


# ================================================================== #
#  6. get_resonance_label                                              #
# ================================================================== #

class TestGetResonanceLabel:
    def test_returns_none_when_no_patterns(self):
        ns = _fresh()
        assert ns.get_resonance_label("grief") is None

    def test_returns_none_when_below_min_frequency(self):
        ns = _fresh()
        ns.contribute_pattern("grief", VEC_A)  # frequency=1 < min=2
        assert ns.get_resonance_label("grief") is None

    def test_returns_string_when_patterns_present(self):
        ns = _fresh()
        ns.contribute_pattern("grief", VEC_A)
        ns.contribute_pattern("grief", VEC_A)  # frequency=2
        label = ns.get_resonance_label("grief")
        assert isinstance(label, str)

    def test_label_contains_c43_ref(self):
        ns = _fresh()
        ns.contribute_pattern("grief", VEC_A)
        ns.contribute_pattern("grief", VEC_A)
        label = ns.get_resonance_label("grief")
        assert "C43" in label

    def test_label_contains_session_count(self):
        """contributed_by_count=2 after two contributions to same pattern."""
        ns = _fresh()
        ns.contribute_pattern("grief", VEC_A)
        ns.contribute_pattern("grief", VEC_A)
        label = ns.get_resonance_label("grief")
        assert "2" in label

    def test_label_aggregates_multiple_patterns(self):
        """Two distinct patterns with contributed_by_count 1 each = total 2."""
        ns = _fresh()
        for _ in range(2):
            ns.contribute_pattern("grief", VEC_A)  # contributed_by_count=2
        for _ in range(2):
            ns.contribute_pattern("grief", VEC_B)  # contributed_by_count=2
        label = ns.get_resonance_label("grief")
        # Total contributed_by_count = 2+2 = 4
        assert "4" in label


# ================================================================== #
#  7. log_coherence_candidate                                          #
# ================================================================== #

class TestLogCoherenceCandidate:
    def test_returns_coherence_event(self):
        ns = _fresh()
        evt = ns.log_coherence_candidate(0.75)
        assert isinstance(evt, CoherenceEvent)

    def test_event_appended_to_log(self):
        ns = _fresh()
        ns.log_coherence_candidate(0.5)
        assert len(ns._coherence_log) == 1

    def test_multiple_events_all_appended(self):
        ns = _fresh()
        for i in range(5):
            ns.log_coherence_candidate(float(i) / 10)
        assert len(ns._coherence_log) == 5

    def test_resonance_score_stored(self):
        ns = _fresh()
        evt = ns.log_coherence_candidate(0.88)
        assert evt.semantic_resonance_score == pytest.approx(0.88)

    def test_entropy_deviation_stored(self):
        ns = _fresh()
        evt = ns.log_coherence_candidate(0.5, entropy_deviation=0.15)
        assert evt.entropy_deviation == pytest.approx(0.15)

    def test_custom_description_stored(self):
        ns = _fresh()
        evt = ns.log_coherence_candidate(0.5, description="custom desc")
        assert evt.description == "custom desc"

    def test_default_description_references_session_count(self):
        ns = _fresh()
        ns.register_session()
        ns.register_session()
        evt = ns.log_coherence_candidate(0.5)  # no description given
        assert "2" in evt.description  # session_count=2 in default description

    def test_epistemic_label_is_candidate_signature(self):
        ns = _fresh()
        evt = ns.log_coherence_candidate(0.9)
        assert evt.epistemic_label == "CANDIDATE_SIGNATURE"

    def test_event_ids_are_unique(self):
        ns = _fresh()
        e1 = ns.log_coherence_candidate(0.5)
        e2 = ns.log_coherence_candidate(0.5)
        assert e1.event_id != e2.event_id

    def test_session_count_snapshot_captured(self):
        ns = _fresh()
        ns.register_session()
        ns.register_session()
        ns.register_session()
        evt = ns.log_coherence_candidate(0.5)
        assert evt.session_count == 3


# ================================================================== #
#  8. get_noosphere_status                                             #
# ================================================================== #

class TestGetNoosphereStatus:
    REQUIRED_KEYS = {
        "doctrine",
        "active_gaians",
        "collective_patterns",
        "coherence_events_logged",
        "coherence_events_epistemic_status",
        "average_recent_resonance",
        "noosphere_stage",
        "phase",
        "phase_2_pending",
        "privacy_status",
    }

    def test_all_required_keys_present(self):
        ns = _fresh()
        status = ns.get_noosphere_status()
        assert self.REQUIRED_KEYS.issubset(status.keys())

    def test_dormant_stage_when_no_sessions(self):
        ns = _fresh()
        status = ns.get_noosphere_status()
        assert "Dormant" in status["noosphere_stage"]

    def test_primitive_awareness_with_one_session(self):
        ns = _fresh()
        ns.register_session()
        status = ns.get_noosphere_status()
        assert "Primitive Awareness" in status["noosphere_stage"]

    def test_primitive_awareness_with_two_sessions(self):
        ns = _fresh()
        ns.register_session()
        ns.register_session()
        status = ns.get_noosphere_status()
        assert "Primitive Awareness" in status["noosphere_stage"]

    def test_reactive_intelligence_with_high_resonance(self):
        """3+ sessions + avg resonance > 0.7 → Reactive Intelligence."""
        ns = _fresh()
        for _ in range(3):
            ns.register_session()
        # Log 5 high-resonance events to push average above 0.7
        for _ in range(5):
            ns.log_coherence_candidate(0.85)
        status = ns.get_noosphere_status()
        assert "Reactive Intelligence" in status["noosphere_stage"]

    def test_primitive_awareness_with_low_resonance_and_3_sessions(self):
        ns = _fresh()
        for _ in range(3):
            ns.register_session()
        for _ in range(5):
            ns.log_coherence_candidate(0.3)  # avg < 0.7
        status = ns.get_noosphere_status()
        assert "Primitive Awareness" in status["noosphere_stage"]

    def test_active_gaians_reflects_sessions(self):
        ns = _fresh()
        ns.register_session()
        ns.register_session()
        status = ns.get_noosphere_status()
        assert status["active_gaians"] == 2

    def test_collective_patterns_count_correct(self):
        ns = _fresh()
        ns.contribute_pattern("grief", VEC_A)
        ns.contribute_pattern("joy", VEC_B)
        status = ns.get_noosphere_status()
        assert status["collective_patterns"] == 2

    def test_coherence_events_count_correct(self):
        ns = _fresh()
        ns.log_coherence_candidate(0.5)
        ns.log_coherence_candidate(0.6)
        status = ns.get_noosphere_status()
        assert status["coherence_events_logged"] == 2

    def test_epistemic_status_label_present(self):
        ns = _fresh()
        status = ns.get_noosphere_status()
        assert "CANDIDATE" in status["coherence_events_epistemic_status"]

    def test_average_resonance_zero_when_no_events(self):
        ns = _fresh()
        status = ns.get_noosphere_status()
        assert status["average_recent_resonance"] == pytest.approx(0.0)

    def test_average_resonance_computed_from_last_5(self):
        ns = _fresh()
        # Log 7 events: first 2 at 0.0, last 5 at 1.0
        for _ in range(2):
            ns.log_coherence_candidate(0.0)
        for _ in range(5):
            ns.log_coherence_candidate(1.0)
        status = ns.get_noosphere_status()
        # Only last 5 events counted → avg = 1.0
        assert status["average_recent_resonance"] == pytest.approx(1.0)

    def test_doctrine_key_references_c43(self):
        ns = _fresh()
        status = ns.get_noosphere_status()
        assert "C43" in status["doctrine"]

    def test_phase_2_pending_is_list(self):
        ns = _fresh()
        status = ns.get_noosphere_status()
        assert isinstance(status["phase_2_pending"], list)
        assert len(status["phase_2_pending"]) > 0

    def test_privacy_status_present(self):
        ns = _fresh()
        status = ns.get_noosphere_status()
        assert "anonymized" in status["privacy_status"].lower()


# ================================================================== #
#  9. qrng_entropy_check — Phase 2 stub contract                      #
# ================================================================== #

class TestQrngEntropyCheck:
    def test_returns_dict(self):
        ns = _fresh()
        result = ns.qrng_entropy_check()
        assert isinstance(result, dict)

    def test_status_is_not_active(self):
        ns = _fresh()
        result = ns.qrng_entropy_check()
        assert "NOT_YET_ACTIVE" in result["status"]

    def test_doctrine_ref_c43(self):
        ns = _fresh()
        result = ns.qrng_entropy_check()
        assert result["doctrine_ref"] == "C43"

    def test_epistemic_label_experimental(self):
        ns = _fresh()
        result = ns.qrng_entropy_check()
        assert "EXPERIMENTAL" in result["epistemic_label"]


# ================================================================== #
#  10. get_noosphere() singleton                                        #
# ================================================================== #

class TestGetNoosphereSingleton:
    def test_returns_same_instance(self):
        noosphere_module._noosphere = None  # reset for isolation
        n1 = get_noosphere()
        n2 = get_noosphere()
        assert n1 is n2

    def test_instance_is_noosphere_layer(self):
        noosphere_module._noosphere = None
        n = get_noosphere()
        assert isinstance(n, NoosphereLayer)
        noosphere_module._noosphere = None  # clean up

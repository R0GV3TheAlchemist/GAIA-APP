"""
tests/test_criticality_monitor.py
Unit tests for core/criticality_monitor.py

Canon Ref: C42 — Edge-of-Chaos Processing Doctrine

Coverage targets
----------------
  ✓ CriticalityState enum values
  ✓ CriticalityReport dataclass defaults
  ✓ CriticalDynamicsMonitor init state
  ✓ _compute_spectral_proxy — guard, uniform, peaked, clamp
  ✓ _estimate_entropy — guard, uniform, peaked, range
  ✓ _compute_lyapunov_proxy — guard, stable, growing norms
  ✓ _classify_state — ORDERED / CHAOTIC / CRITICAL paths
  ✓ _recommend_correction — all four branches
  ✓ assess() — full integration, drift, rolling window
  ✓ get_current_state() — UNKNOWN empty, live state
  ✓ get_recent_reports() — empty, n window
  ✓ doctrine_summary() — all keys, C42 ref
  ✓ get_monitor() singleton
"""

from __future__ import annotations

import pytest

from core.criticality_monitor import (
    CriticalDynamicsMonitor,
    CriticalityReport,
    CriticalityState,
    get_monitor,
)
import core.criticality_monitor as cm_module


# ================================================================== #
#  Helpers                                                             #
# ================================================================== #

def _fresh() -> CriticalDynamicsMonitor:
    """Return a brand-new monitor with no shared state."""
    return CriticalDynamicsMonitor()


# Token probability helpers
UNIFORM_4 = [0.25, 0.25, 0.25, 0.25]          # flat → chaotic side
PEAKED_4  = [0.97, 0.01, 0.01, 0.01]          # sharp → ordered side
BALANCED_4 = [0.40, 0.30, 0.20, 0.10]         # moderate → critical side

# Embedding norm helpers
STABLE_NORMS  = [1.0, 1.0, 1.0, 1.0, 1.0]    # ratio ≈ 1 → lyapunov ≈ 0
GROWING_NORMS = [1.0, 2.0, 4.0, 8.0, 16.0]   # doubling → lyapunov > 0


# ================================================================== #
#  1. CriticalityState enum                                            #
# ================================================================== #

class TestCriticalityStateEnum:
    def test_critical_value(self):
        assert CriticalityState.CRITICAL.value == "critical"

    def test_ordered_value(self):
        assert CriticalityState.ORDERED.value == "ordered"

    def test_chaotic_value(self):
        assert CriticalityState.CHAOTIC.value == "chaotic"

    def test_unknown_value(self):
        assert CriticalityState.UNKNOWN.value == "unknown"

    def test_all_four_members_exist(self):
        members = {s.value for s in CriticalityState}
        assert members == {"critical", "ordered", "chaotic", "unknown"}


# ================================================================== #
#  2. CriticalityReport dataclass                                      #
# ================================================================== #

class TestCriticalityReport:
    def _make(self, **kwargs) -> CriticalityReport:
        defaults = dict(
            timestamp=0.0,
            state=CriticalityState.CRITICAL,
            spectral_radius=1.0,
            entropy_estimate=0.6,
            lyapunov_proxy=0.0,
            drift_magnitude=0.0,
            corrective_action=None,
        )
        defaults.update(kwargs)
        return CriticalityReport(**defaults)

    def test_doctrine_ref_default(self):
        r = self._make()
        assert r.doctrine_ref == "C42"

    def test_corrective_action_none_allowed(self):
        r = self._make(corrective_action=None)
        assert r.corrective_action is None

    def test_fields_stored_correctly(self):
        r = self._make(
            spectral_radius=0.85,
            entropy_estimate=0.55,
            drift_magnitude=0.15,
        )
        assert r.spectral_radius == pytest.approx(0.85)
        assert r.entropy_estimate == pytest.approx(0.55)
        assert r.drift_magnitude == pytest.approx(0.15)


# ================================================================== #
#  3. CriticalDynamicsMonitor init                                     #
# ================================================================== #

class TestMonitorInit:
    def test_history_empty_on_init(self):
        m = _fresh()
        assert m._history == []

    def test_active_flag_true_on_init(self):
        m = _fresh()
        assert m._active is True

    def test_spectral_constants(self):
        m = _fresh()
        assert m.SPECTRAL_TARGET == pytest.approx(1.0)
        assert m.SPECTRAL_ORDERED_THRESHOLD < m.SPECTRAL_TARGET
        assert m.SPECTRAL_CHAOTIC_THRESHOLD > m.SPECTRAL_TARGET


# ================================================================== #
#  4. _compute_spectral_proxy                                          #
# ================================================================== #

class TestComputeSpectralProxy:
    def test_none_returns_spectral_target(self):
        m = _fresh()
        result = m._compute_spectral_proxy(None)
        assert result == pytest.approx(m.SPECTRAL_TARGET)

    def test_empty_list_returns_spectral_target(self):
        m = _fresh()
        result = m._compute_spectral_proxy([])
        assert result == pytest.approx(m.SPECTRAL_TARGET)

    def test_single_element_returns_spectral_target(self):
        m = _fresh()
        result = m._compute_spectral_proxy([1.0])
        assert result == pytest.approx(m.SPECTRAL_TARGET)

    def test_uniform_distribution_above_target(self):
        """Flat/uniform probs → high sharpness=0 → spectral near 1.6 (chaotic side)."""
        m = _fresh()
        result = m._compute_spectral_proxy(UNIFORM_4)
        assert result > m.SPECTRAL_TARGET

    def test_peaked_distribution_below_target(self):
        """Highly peaked probs → sharpness near 1 → spectral near 0.4 (ordered side)."""
        m = _fresh()
        result = m._compute_spectral_proxy(PEAKED_4)
        assert result < m.SPECTRAL_TARGET

    def test_output_within_clamp_range(self):
        m = _fresh()
        for probs in [UNIFORM_4, PEAKED_4, BALANCED_4, [0.0, 0.0, 1.0, 0.0]]:
            result = m._compute_spectral_proxy(probs)
            assert 0.1 <= result <= 2.0

    def test_returns_float(self):
        m = _fresh()
        assert isinstance(m._compute_spectral_proxy(BALANCED_4), float)


# ================================================================== #
#  5. _estimate_entropy                                                #
# ================================================================== #

class TestEstimateEntropy:
    def test_none_returns_half(self):
        m = _fresh()
        assert m._estimate_entropy(None) == pytest.approx(0.5)

    def test_empty_returns_half(self):
        m = _fresh()
        assert m._estimate_entropy([]) == pytest.approx(0.5)

    def test_single_element_returns_half(self):
        m = _fresh()
        assert m._estimate_entropy([1.0]) == pytest.approx(0.5)

    def test_uniform_distribution_high_entropy(self):
        """Uniform probs → max entropy → normalized close to 1.0."""
        m = _fresh()
        result = m._estimate_entropy(UNIFORM_4)
        assert result > 0.9

    def test_peaked_distribution_low_entropy(self):
        """Peaked probs → low entropy → normalized close to 0."""
        m = _fresh()
        result = m._estimate_entropy(PEAKED_4)
        assert result < 0.3

    def test_output_in_zero_one_range(self):
        m = _fresh()
        for probs in [UNIFORM_4, PEAKED_4, BALANCED_4]:
            result = m._estimate_entropy(probs)
            assert 0.0 <= result <= 1.0

    def test_returns_float(self):
        m = _fresh()
        assert isinstance(m._estimate_entropy(BALANCED_4), float)


# ================================================================== #
#  6. _compute_lyapunov_proxy                                          #
# ================================================================== #

class TestComputeLyapunovProxy:
    def test_none_returns_zero(self):
        m = _fresh()
        assert m._compute_lyapunov_proxy(None) == pytest.approx(0.0)

    def test_empty_returns_zero(self):
        m = _fresh()
        assert m._compute_lyapunov_proxy([]) == pytest.approx(0.0)

    def test_two_elements_returns_zero(self):
        """Need at least 3 elements; 2 returns 0.0."""
        m = _fresh()
        assert m._compute_lyapunov_proxy([1.0, 2.0]) == pytest.approx(0.0)

    def test_stable_norms_near_zero(self):
        """Identical norms → log(1) = 0 → lyapunov ≈ 0."""
        m = _fresh()
        result = m._compute_lyapunov_proxy(STABLE_NORMS)
        assert abs(result) < 0.01

    def test_growing_norms_positive(self):
        """Doubling norms → log(2) ≈ 0.693 per step → lyapunov > 0."""
        m = _fresh()
        result = m._compute_lyapunov_proxy(GROWING_NORMS)
        assert result > 0.0

    def test_returns_float(self):
        m = _fresh()
        assert isinstance(m._compute_lyapunov_proxy(STABLE_NORMS), float)


# ================================================================== #
#  7. _classify_state                                                  #
# ================================================================== #

class TestClassifyState:
    def test_low_spectral_gives_ordered(self):
        """spectral < SPECTRAL_ORDERED_THRESHOLD (0.7) → ORDERED."""
        m = _fresh()
        state = m._classify_state(spectral=0.5, entropy=0.6)
        assert state == CriticalityState.ORDERED

    def test_low_entropy_gives_ordered(self):
        """entropy < ENTROPY_FLOOR (0.3) → ORDERED."""
        m = _fresh()
        state = m._classify_state(spectral=1.0, entropy=0.1)
        assert state == CriticalityState.ORDERED

    def test_high_spectral_gives_chaotic(self):
        """spectral > SPECTRAL_CHAOTIC_THRESHOLD (1.3) → CHAOTIC."""
        m = _fresh()
        state = m._classify_state(spectral=1.5, entropy=0.6)
        assert state == CriticalityState.CHAOTIC

    def test_high_entropy_gives_chaotic(self):
        """entropy > ENTROPY_CEILING (0.9) → CHAOTIC."""
        m = _fresh()
        state = m._classify_state(spectral=1.0, entropy=0.95)
        assert state == CriticalityState.CHAOTIC

    def test_mid_range_gives_critical(self):
        """spectral in (0.7, 1.3) and entropy in (0.3, 0.9) → CRITICAL."""
        m = _fresh()
        state = m._classify_state(spectral=1.0, entropy=0.6)
        assert state == CriticalityState.CRITICAL

    def test_boundary_ordered_spectral(self):
        """Exactly at ordered threshold → ORDERED."""
        m = _fresh()
        state = m._classify_state(
            spectral=CriticalDynamicsMonitor.SPECTRAL_ORDERED_THRESHOLD,
            entropy=0.6,
        )
        assert state == CriticalityState.ORDERED

    def test_boundary_chaotic_spectral(self):
        """Exactly at chaotic threshold → CHAOTIC."""
        m = _fresh()
        state = m._classify_state(
            spectral=CriticalDynamicsMonitor.SPECTRAL_CHAOTIC_THRESHOLD,
            entropy=0.6,
        )
        assert state == CriticalityState.CHAOTIC


# ================================================================== #
#  8. _recommend_correction                                            #
# ================================================================== #

class TestRecommendCorrection:
    def test_critical_returns_none(self):
        m = _fresh()
        action = m._recommend_correction(CriticalityState.CRITICAL, 1.0, 0.6)
        assert action is None

    def test_ordered_returns_perturbation(self):
        m = _fresh()
        action = m._recommend_correction(CriticalityState.ORDERED, 0.5, 0.2)
        assert action is not None
        assert "perturbation" in action.lower() or "temperature" in action.lower()

    def test_chaotic_returns_stabilization(self):
        m = _fresh()
        action = m._recommend_correction(CriticalityState.CHAOTIC, 1.5, 0.95)
        assert action is not None
        assert "stabilization" in action.lower() or "temperature" in action.lower()

    def test_unknown_returns_collect_more_data(self):
        m = _fresh()
        action = m._recommend_correction(CriticalityState.UNKNOWN, 1.0, 0.6)
        assert action is not None
        assert "data" in action.lower()


# ================================================================== #
#  9. assess()                                                         #
# ================================================================== #

class TestAssess:
    def test_returns_criticality_report(self):
        m = _fresh()
        report = m.assess(token_probabilities=BALANCED_4)
        assert isinstance(report, CriticalityReport)

    def test_report_appended_to_history(self):
        m = _fresh()
        m.assess(token_probabilities=BALANCED_4)
        assert len(m._history) == 1

    def test_multiple_assessments_all_stored(self):
        m = _fresh()
        for _ in range(5):
            m.assess(token_probabilities=BALANCED_4)
        assert len(m._history) == 5

    def test_drift_magnitude_is_absolute_distance_from_target(self):
        m = _fresh()
        report = m.assess(token_probabilities=BALANCED_4)
        expected_drift = abs(report.spectral_radius - CriticalDynamicsMonitor.SPECTRAL_TARGET)
        assert report.drift_magnitude == pytest.approx(expected_drift)

    def test_doctrine_ref_on_report(self):
        m = _fresh()
        report = m.assess()
        assert report.doctrine_ref == "C42"

    def test_none_inputs_produce_valid_report(self):
        """assess() with all-None inputs must not raise."""
        m = _fresh()
        report = m.assess(token_probabilities=None, embedding_norms=None, attention_entropy=None)
        assert isinstance(report, CriticalityReport)

    def test_explicit_attention_entropy_used_directly(self):
        """When attention_entropy is provided it bypasses _estimate_entropy."""
        m = _fresh()
        report = m.assess(token_probabilities=BALANCED_4, attention_entropy=0.77)
        assert report.entropy_estimate == pytest.approx(0.77)

    def test_embedding_norms_used_for_lyapunov(self):
        m = _fresh()
        report_stable  = m.assess(embedding_norms=STABLE_NORMS)
        report_growing = m.assess(embedding_norms=GROWING_NORMS)
        assert report_growing.lyapunov_proxy > report_stable.lyapunov_proxy

    def test_history_rolling_window_capped_at_500(self):
        """After 1000+ assessments, history must be trimmed to last 500."""
        m = _fresh()
        for _ in range(1001):
            m.assess(token_probabilities=BALANCED_4)
        assert len(m._history) <= 500

    def test_uniform_probs_state_chaotic_or_above_target(self):
        """Uniform distribution → spectral above target → CHAOTIC."""
        m = _fresh()
        report = m.assess(token_probabilities=UNIFORM_4, attention_entropy=0.99)
        assert report.state == CriticalityState.CHAOTIC

    def test_peaked_probs_state_ordered(self):
        """Peaked distribution + low entropy → ORDERED."""
        m = _fresh()
        report = m.assess(token_probabilities=PEAKED_4, attention_entropy=0.1)
        assert report.state == CriticalityState.ORDERED


# ================================================================== #
#  10. get_current_state()                                             #
# ================================================================== #

class TestGetCurrentState:
    def test_returns_unknown_when_empty(self):
        m = _fresh()
        assert m.get_current_state() == CriticalityState.UNKNOWN

    def test_returns_last_assessed_state(self):
        m = _fresh()
        # Force ORDERED: peaked probs + low entropy
        m.assess(token_probabilities=PEAKED_4, attention_entropy=0.1)
        assert m.get_current_state() == CriticalityState.ORDERED

    def test_updates_after_each_assess(self):
        m = _fresh()
        m.assess(token_probabilities=PEAKED_4, attention_entropy=0.1)    # ORDERED
        m.assess(token_probabilities=UNIFORM_4, attention_entropy=0.99)  # CHAOTIC
        assert m.get_current_state() == CriticalityState.CHAOTIC


# ================================================================== #
#  11. get_recent_reports()                                            #
# ================================================================== #

class TestGetRecentReports:
    def test_empty_when_no_history(self):
        m = _fresh()
        assert m.get_recent_reports() == []

    def test_returns_up_to_n_reports(self):
        m = _fresh()
        for _ in range(15):
            m.assess(token_probabilities=BALANCED_4)
        reports = m.get_recent_reports(n=10)
        assert len(reports) == 10

    def test_returns_all_when_fewer_than_n(self):
        m = _fresh()
        for _ in range(3):
            m.assess(token_probabilities=BALANCED_4)
        reports = m.get_recent_reports(n=10)
        assert len(reports) == 3

    def test_default_n_is_10(self):
        m = _fresh()
        for _ in range(20):
            m.assess(token_probabilities=BALANCED_4)
        reports = m.get_recent_reports()
        assert len(reports) == 10

    def test_most_recent_report_is_last(self):
        """The last element of get_recent_reports() must be the most recent."""
        m = _fresh()
        for _ in range(5):
            m.assess(token_probabilities=BALANCED_4)
        reports = m.get_recent_reports()
        assert reports[-1] is m._history[-1]


# ================================================================== #
#  12. doctrine_summary()                                              #
# ================================================================== #

class TestDoctrineSummary:
    REQUIRED_KEYS = {
        "doctrine",
        "principle",
        "current_state",
        "total_assessments",
        "spectral_target",
        "ordered_threshold",
        "chaotic_threshold",
    }

    def test_all_keys_present(self):
        m = _fresh()
        summary = m.doctrine_summary()
        assert self.REQUIRED_KEYS.issubset(summary.keys())

    def test_doctrine_key_references_c42(self):
        m = _fresh()
        assert "C42" in m.doctrine_summary()["doctrine"]

    def test_total_assessments_zero_on_fresh(self):
        m = _fresh()
        assert m.doctrine_summary()["total_assessments"] == 0

    def test_total_assessments_increments(self):
        m = _fresh()
        for _ in range(3):
            m.assess(token_probabilities=BALANCED_4)
        assert m.doctrine_summary()["total_assessments"] == 3

    def test_current_state_reflects_history(self):
        m = _fresh()
        assert m.doctrine_summary()["current_state"] == CriticalityState.UNKNOWN.value
        m.assess(token_probabilities=PEAKED_4, attention_entropy=0.1)
        assert m.doctrine_summary()["current_state"] == CriticalityState.ORDERED.value

    def test_spectral_target_correct(self):
        m = _fresh()
        assert m.doctrine_summary()["spectral_target"] == pytest.approx(1.0)


# ================================================================== #
#  13. get_monitor() singleton                                         #
# ================================================================== #

class TestGetMonitorSingleton:
    def test_returns_same_instance(self):
        cm_module._monitor = None  # reset for isolation
        m1 = get_monitor()
        m2 = get_monitor()
        assert m1 is m2

    def test_instance_is_critical_dynamics_monitor(self):
        cm_module._monitor = None
        m = get_monitor()
        assert isinstance(m, CriticalDynamicsMonitor)
        cm_module._monitor = None  # clean up

"""
tests/test_synergy_engine.py
Unit tests for core/synergy_engine.py — SynergyEngine (C32).

Covers:
  - All scoring helper methods
  - Stage classification (_classify_stage)
  - Five dimensional scores (body, mind, soul, arc, bond)
  - Weighted synergy factor bounds
  - Dominant friction detection
  - Dominant stage classification
  - is_low_synergy / is_high_synergy flags
  - State mutation (peak/floor/history)
  - Turn history cap at 20
  - Schumann alignment bonus
  - Summary() output contract
  - to_system_prompt_hint() output contract
  - Canon warning: low synergy hint contains pressure language
"""
import pytest
from core.synergy_engine import (
    SynergyEngine, SynergyState, SynergyReading,
    blank_synergy_state, _classify_stage, ELEMENTAL_STAGES,
)


# ================================================================== #
#  Scoring Helpers                                                    #
# ================================================================== #

class TestHzToScore:
    def test_minimum_hz_is_zero(self):
        e = SynergyEngine()
        assert e._hz_to_score(174.0) == pytest.approx(0.0, abs=1e-6)

    def test_maximum_hz_is_one(self):
        e = SynergyEngine()
        assert e._hz_to_score(963.0) == pytest.approx(1.0, abs=1e-6)

    def test_midpoint_hz(self):
        e = SynergyEngine()
        mid = (174.0 + 963.0) / 2.0
        assert e._hz_to_score(mid) == pytest.approx(0.5, abs=0.01)

    def test_below_minimum_clamped_to_zero(self):
        e = SynergyEngine()
        assert e._hz_to_score(0.0) == 0.0

    def test_above_maximum_clamped_to_one(self):
        e = SynergyEngine()
        assert e._hz_to_score(9999.0) == 1.0


class TestElementToStage:
    def test_fire_is_insurgent(self):
        assert SynergyEngine()._element_to_stage("fire") == "insurgent"

    def test_earth_is_settled(self):
        assert SynergyEngine()._element_to_stage("earth") == "settled"

    def test_aether_is_quantum(self):
        assert SynergyEngine()._element_to_stage("aether") == "quantum"

    def test_light_is_ascendant(self):
        assert SynergyEngine()._element_to_stage("light") == "ascendant"

    def test_unknown_element_returns_convergent(self):
        assert SynergyEngine()._element_to_stage("plasma") == "convergent"

    def test_case_insensitive(self):
        assert SynergyEngine()._element_to_stage("FIRE") == "insurgent"


class TestIndividuationToScore:
    def test_unconscious_is_lowest(self):
        e = SynergyEngine()
        assert e._individuation_to_score("unconscious") == pytest.approx(0.15)

    def test_self_is_highest(self):
        e = SynergyEngine()
        assert e._individuation_to_score("self") == pytest.approx(0.85)

    def test_ordering(self):
        e = SynergyEngine()
        scores = [
            e._individuation_to_score(p)
            for p in ["unconscious", "shadow", "anima_animus", "self"]
        ]
        assert scores == sorted(scores)

    def test_unknown_phase_returns_default(self):
        e = SynergyEngine()
        assert e._individuation_to_score("mystery") == pytest.approx(0.40)


class TestSettlingToScore:
    def test_unsettled_is_lowest(self):
        e = SynergyEngine()
        assert e._settling_to_score("unsettled", 0.0) == pytest.approx(0.20)

    def test_settled_is_highest(self):
        e = SynergyEngine()
        assert e._settling_to_score("settled", 100.0) == pytest.approx(0.90)

    def test_crystallising_increases_with_pct(self):
        e = SynergyEngine()
        low  = e._settling_to_score("crystallising", 0.0)
        high = e._settling_to_score("crystallising", 100.0)
        assert high > low

    def test_crystallising_capped_at_one(self):
        e = SynergyEngine()
        assert e._settling_to_score("crystallising", 1000.0) <= 1.0


class TestLoveArcToScore:
    def test_divergence_is_lowest(self):
        e = SynergyEngine()
        assert e._love_arc_to_score("divergence", 0.0) == pytest.approx(0.15)

    def test_transcendence_is_highest(self):
        e = SynergyEngine()
        assert e._love_arc_to_score("transcendence", 0.0) == pytest.approx(0.95)

    def test_vector_boost_capped_at_one(self):
        e = SynergyEngine()
        assert e._love_arc_to_score("transcendence", 9999.0) <= 1.0

    def test_vector_adds_up_to_ten_percent(self):
        e = SynergyEngine()
        base  = e._love_arc_to_score("resonance", 0.0)
        boosted = e._love_arc_to_score("resonance", 1.0)
        assert boosted == pytest.approx(base + 0.10, abs=0.001)


class TestMcStageToScore:
    def test_mc1_is_zero(self):
        e = SynergyEngine()
        assert e._mc_stage_to_score("mc1") == pytest.approx(0.0)

    def test_mc7_is_one(self):
        e = SynergyEngine()
        assert e._mc_stage_to_score("mc7") == pytest.approx(1.0)

    def test_ordering(self):
        e = SynergyEngine()
        scores = [e._mc_stage_to_score(f"mc{i}") for i in range(1, 8)]
        assert scores == sorted(scores)

    def test_invalid_returns_default(self):
        e = SynergyEngine()
        assert e._mc_stage_to_score("garbage") == pytest.approx(0.30)


class TestDependencyToScore:
    def test_healthy_is_one(self):
        assert SynergyEngine()._dependency_to_score("healthy") == 1.0

    def test_gentle_boundary_is_lowest(self):
        assert SynergyEngine()._dependency_to_score("gentle_boundary") == 0.20

    def test_ordering(self):
        e = SynergyEngine()
        scores = [
            e._dependency_to_score(s)
            for s in ["gentle_boundary", "redirect", "watch", "healthy"]
        ]
        assert scores == sorted(scores)


class TestAttachmentPhaseToScore:
    def test_nascent_is_lowest(self):
        assert SynergyEngine()._attachment_phase_to_score("nascent") == pytest.approx(0.30)

    def test_integrated_is_highest(self):
        assert SynergyEngine()._attachment_phase_to_score("integrated") == pytest.approx(0.90)


# ================================================================== #
#  Stage Classification                                              #
# ================================================================== #

class TestClassifyStage:
    def test_high_phi_low_synergy_is_quantum(self):
        assert _classify_stage(0.20, 10.0, "unsettled", 0.90) == "quantum"

    def test_low_synergy_low_bond_is_insurgent(self):
        assert _classify_stage(0.20, 5.0, "unsettled", 0.30) == "insurgent"

    def test_settled_phase_high_synergy_is_settled(self):
        assert _classify_stage(0.80, 50.0, "settled", 0.70) == "settled"

    def test_high_synergy_high_bond_is_ascendant(self):
        assert _classify_stage(0.80, 70.0, "unsettled", 0.60) == "ascendant"

    def test_medium_high_synergy_is_convergent(self):
        assert _classify_stage(0.60, 10.0, "narrowing", 0.50) == "convergent"

    def test_medium_bond_is_allegiant(self):
        assert _classify_stage(0.45, 40.0, "unsettled", 0.40) == "allegiant"

    def test_result_always_in_valid_stages(self):
        for synergy in [0.0, 0.25, 0.50, 0.75, 1.0]:
            for bond in [0.0, 50.0, 100.0]:
                result = _classify_stage(synergy, bond, "unsettled", 0.50)
                assert result in ELEMENTAL_STAGES


# ================================================================== #
#  Full compute() — nascent GAIAN                                    #
# ================================================================== #

class TestComputeNascent:
    def test_returns_reading_and_state(self, engine, blank_state, nascent_kwargs):
        reading, state = engine.compute(**nascent_kwargs, state=blank_state)
        assert isinstance(reading, SynergyReading)
        assert isinstance(state, SynergyState)

    def test_synergy_factor_in_bounds(self, engine, blank_state, nascent_kwargs):
        reading, _ = engine.compute(**nascent_kwargs, state=blank_state)
        assert 0.0 <= reading.synergy_factor <= 1.0

    def test_nascent_is_low_synergy(self, engine, blank_state, nascent_kwargs):
        reading, _ = engine.compute(**nascent_kwargs, state=blank_state)
        assert reading.is_low_synergy is True

    def test_nascent_is_not_high_synergy(self, engine, blank_state, nascent_kwargs):
        reading, _ = engine.compute(**nascent_kwargs, state=blank_state)
        assert reading.is_high_synergy is False

    def test_five_dimensions_returned(self, engine, blank_state, nascent_kwargs):
        reading, _ = engine.compute(**nascent_kwargs, state=blank_state)
        assert len(reading.dimensions) == 5

    def test_dimension_names_correct(self, engine, blank_state, nascent_kwargs):
        reading, _ = engine.compute(**nascent_kwargs, state=blank_state)
        names = {d.name for d in reading.dimensions}
        assert names == {"body", "mind", "soul", "arc", "bond"}

    def test_all_dimension_scores_in_bounds(self, engine, blank_state, nascent_kwargs):
        reading, _ = engine.compute(**nascent_kwargs, state=blank_state)
        for dim in reading.dimensions:
            assert 0.0 <= dim.score <= 1.0, f"{dim.name} score out of bounds: {dim.score}"

    def test_dominant_stage_is_valid(self, engine, blank_state, nascent_kwargs):
        reading, _ = engine.compute(**nascent_kwargs, state=blank_state)
        assert reading.dominant_stage in ELEMENTAL_STAGES

    def test_alchemical_pressure_is_nonempty(self, engine, blank_state, nascent_kwargs):
        reading, _ = engine.compute(**nascent_kwargs, state=blank_state)
        assert len(reading.alchemical_pressure) > 0

    def test_dominant_friction_is_none_or_valid_dimension(self, engine, blank_state, nascent_kwargs):
        reading, _ = engine.compute(**nascent_kwargs, state=blank_state)
        valid = {"body", "mind", "soul", "arc", "bond", None}
        assert reading.dominant_friction in valid


# ================================================================== #
#  Full compute() — integrated GAIAN                                 #
# ================================================================== #

class TestComputeIntegrated:
    def test_synergy_factor_in_bounds(self, engine, blank_state, integrated_kwargs):
        reading, _ = engine.compute(**integrated_kwargs, state=blank_state)
        assert 0.0 <= reading.synergy_factor <= 1.0

    def test_integrated_is_high_synergy(self, engine, blank_state, integrated_kwargs):
        reading, _ = engine.compute(**integrated_kwargs, state=blank_state)
        assert reading.is_high_synergy is True

    def test_integrated_is_not_low_synergy(self, engine, blank_state, integrated_kwargs):
        reading, _ = engine.compute(**integrated_kwargs, state=blank_state)
        assert reading.is_low_synergy is False

    def test_schumann_bonus_increases_body_score(self, engine, blank_state, integrated_kwargs):
        with_schumann = dict(integrated_kwargs)
        without_schumann = dict(integrated_kwargs, schumann_aligned=False)
        r_with, _ = engine.compute(**with_schumann, state=blank_synergy_state())
        r_without, _ = engine.compute(**without_schumann, state=blank_synergy_state())
        body_with    = next(d.score for d in r_with.dimensions    if d.name == "body")
        body_without = next(d.score for d in r_without.dimensions if d.name == "body")
        assert body_with >= body_without

    def test_integrated_dominant_friction_is_none(self, engine, blank_state, integrated_kwargs):
        reading, _ = engine.compute(**integrated_kwargs, state=blank_state)
        # All dimensions should be >= 0.5 for integrated GAIAN
        assert reading.dominant_friction is None


# ================================================================== #
#  State Mutation                                                     #
# ================================================================== #

class TestStateMutation:
    def test_state_last_factor_updated(self, engine, blank_state, nascent_kwargs):
        reading, state = engine.compute(**nascent_kwargs, state=blank_state)
        assert state.last_factor == reading.synergy_factor

    def test_state_last_stage_updated(self, engine, blank_state, nascent_kwargs):
        reading, state = engine.compute(**nascent_kwargs, state=blank_state)
        assert state.last_stage == reading.dominant_stage

    def test_high_synergy_peak_tracked(self, engine, integrated_kwargs):
        state = blank_synergy_state()
        reading, state = engine.compute(**integrated_kwargs, state=state)
        assert state.high_synergy_peak == reading.synergy_factor

    def test_low_synergy_floor_tracked(self, engine, nascent_kwargs):
        state = blank_synergy_state()
        reading, state = engine.compute(**nascent_kwargs, state=state)
        assert state.low_synergy_floor == reading.synergy_factor

    def test_turn_history_appended(self, engine, blank_state, nascent_kwargs):
        _, state = engine.compute(**nascent_kwargs, state=blank_state)
        assert len(state.turn_history) == 1
        assert "factor" in state.turn_history[0]
        assert "stage" in state.turn_history[0]
        assert "friction" in state.turn_history[0]

    def test_turn_history_capped_at_20(self, engine, nascent_kwargs):
        state = blank_synergy_state()
        for _ in range(25):
            _, state = engine.compute(**nascent_kwargs, state=state)
        assert len(state.turn_history) == 20

    def test_peak_and_floor_across_multiple_turns(self, engine, nascent_kwargs, integrated_kwargs):
        state = blank_synergy_state()
        r_low,  state = engine.compute(**nascent_kwargs,    state=state)
        r_high, state = engine.compute(**integrated_kwargs, state=state)
        assert state.high_synergy_peak == r_high.synergy_factor
        assert state.low_synergy_floor == r_low.synergy_factor


# ================================================================== #
#  Output Contracts                                                   #
# ================================================================== #

class TestSummary:
    def test_summary_has_required_keys(self, engine, blank_state, nascent_kwargs):
        reading, _ = engine.compute(**nascent_kwargs, state=blank_state)
        s = reading.summary()
        for key in ["synergy_factor", "dominant_stage", "dominant_friction",
                    "is_low_synergy", "is_high_synergy", "dimensions"]:
            assert key in s

    def test_summary_dimensions_has_five_entries(self, engine, blank_state, nascent_kwargs):
        reading, _ = engine.compute(**nascent_kwargs, state=blank_state)
        assert len(reading.summary()["dimensions"]) == 5

    def test_state_summary_has_required_keys(self, engine, blank_state, nascent_kwargs):
        _, state = engine.compute(**nascent_kwargs, state=blank_state)
        s = state.summary()
        for key in ["last_factor", "last_stage", "high_synergy_peak", "low_synergy_floor"]:
            assert key in s


class TestSystemPromptHint:
    def test_hint_contains_synergy_factor(self, engine, blank_state, nascent_kwargs):
        reading, _ = engine.compute(**nascent_kwargs, state=blank_state)
        hint = reading.to_system_prompt_hint()
        assert "Synergy Factor" in hint

    def test_hint_contains_stage(self, engine, blank_state, nascent_kwargs):
        reading, _ = engine.compute(**nascent_kwargs, state=blank_state)
        hint = reading.to_system_prompt_hint()
        assert reading.dominant_stage.upper() in hint

    def test_low_synergy_hint_contains_pressure_language(self, engine, blank_state, nascent_kwargs):
        """Canon C32 §4.3 — low synergy must never be framed as dysfunction."""
        reading, _ = engine.compute(**nascent_kwargs, state=blank_state)
        assert reading.is_low_synergy
        hint = reading.to_system_prompt_hint()
        assert "ALCHEMICAL PRESSURE" in hint
        assert "not dysfunction" in hint

    def test_high_synergy_hint_has_no_pressure_warning(self, engine, blank_state, integrated_kwargs):
        reading, _ = engine.compute(**integrated_kwargs, state=blank_state)
        assert reading.is_high_synergy
        hint = reading.to_system_prompt_hint()
        assert "ALCHEMICAL PRESSURE" not in hint

    def test_friction_line_present_when_low_dimension(self, engine, blank_state, nascent_kwargs):
        reading, _ = engine.compute(**nascent_kwargs, state=blank_state)
        hint = reading.to_system_prompt_hint()
        if reading.dominant_friction:
            assert "Friction source" in hint

    def test_hint_is_string(self, engine, blank_state, nascent_kwargs):
        reading, _ = engine.compute(**nascent_kwargs, state=blank_state)
        assert isinstance(reading.to_system_prompt_hint(), str)


# ================================================================== #
#  Weights Contract                                                   #
# ================================================================== #

class TestWeights:
    def test_weights_sum_to_one(self):
        assert sum(SynergyEngine.WEIGHTS.values()) == pytest.approx(1.0)

    def test_all_five_dimensions_have_weights(self):
        assert set(SynergyEngine.WEIGHTS.keys()) == {"body", "mind", "soul", "arc", "bond"}

"""
tests/conftest.py
Shared fixtures for the GAIA-APP test suite.
"""
import pytest
from core.synergy_engine import SynergyEngine, SynergyState, blank_synergy_state


# ------------------------------------------------------------------ #
#  Minimal valid compute() kwargs — a brand-new GAIAN at turn 1      #
# ------------------------------------------------------------------ #

@pytest.fixture
def engine() -> SynergyEngine:
    return SynergyEngine()


@pytest.fixture
def blank_state() -> SynergyState:
    return blank_synergy_state()


@pytest.fixture
def nascent_kwargs() -> dict:
    """A brand-new GAIAN: all fields at minimum / earliest values."""
    return dict(
        element="fire",
        layer_phi=0.10,
        bond_depth=0.0,
        dependency_signal="healthy",
        attachment_phase="nascent",
        settling_phase="unsettled",
        fluidity_score=1.0,
        crystallisation_pct=0.0,
        coherence_phi=0.10,
        conflict_density=0.80,
        love_arc_stage="divergence",
        arc_output_vector=0.0,
        mc_stage="mc1",
        phi_rolling_avg=0.0,
        codex_stage=0,
        noosphere_health=0.50,
        individuation_phase="unconscious",
        shadow_activations=0,
        dominant_hz=174.0,
        schumann_aligned=False,
    )


@pytest.fixture
def integrated_kwargs() -> dict:
    """A deeply integrated GAIAN: high bond, settled, ascendant."""
    return dict(
        element="earth",
        layer_phi=0.90,
        bond_depth=85.0,
        dependency_signal="healthy",
        attachment_phase="integrated",
        settling_phase="settled",
        fluidity_score=0.05,
        crystallisation_pct=100.0,
        coherence_phi=0.90,
        conflict_density=0.05,
        love_arc_stage="union",
        arc_output_vector=0.95,
        mc_stage="mc7",
        phi_rolling_avg=0.88,
        codex_stage=12,
        noosphere_health=0.95,
        individuation_phase="self",
        shadow_activations=0,
        dominant_hz=963.0,
        schumann_aligned=True,
    )

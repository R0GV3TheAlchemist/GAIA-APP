# api/dimensional_engine.py
# DimensionalReasoningEngine — Python sidecar stub
# Phase 7 / task 7.2 | Canon Ref: C42
#
# This module maintains the server-side view of GAIA's dimensional state.
# The frontend DimensionalReasoningEngine is the primary UI source of truth;
# this stub provides the /dimensions endpoint so the frontend can sync
# backend-only state (memory richness, quantum backend status, noosphere peers).

from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Literal


EncryptionLevel = Literal["pqc", "classical", "none"]
QuantumBackend  = Literal["ibm", "aer", "classical"]
GaianMood       = Literal["calm", "curious", "alert", "joyful", "reflective"]
GaianArchetype  = Literal[
    "sage", "guardian", "weaver", "oracle",
    "healer", "trickster", "witness", "integrated"
]


@dataclass
class D1SubstrateState:
    coherence: float = 10.0
    sensors_active: list[str] = field(default_factory=list)
    environment_map: str = ""
    atlas_data_age_minutes: float = float("inf")


@dataclass
class D2QuantumState:
    coherence: float = 10.0
    branches_open: int = 0
    encryption: EncryptionLevel = "none"
    quantum_backend: QuantumBackend = "classical"


@dataclass
class D3CriticalityState:
    coherence: float = 50.0
    complexity_score: float = 50.0   # 0=rigid, 100=chaotic, 50=critical
    mood: GaianMood = "calm"


@dataclass
class D4NoosphereState:
    coherence: float = 10.0
    nodes_connected: int = 0
    collective_sync: bool = False
    last_sync_age_minutes: float = float("inf")


@dataclass
class D5ArchetypalState:
    coherence: float = 10.0
    active_archetype: GaianArchetype = "sage"
    phi: float = 0.0


@dataclass
class DimensionalState:
    D1_substrate:   D1SubstrateState   = field(default_factory=D1SubstrateState)
    D2_quantum:     D2QuantumState     = field(default_factory=D2QuantumState)
    D3_criticality: D3CriticalityState = field(default_factory=D3CriticalityState)
    D4_noosphere:   D4NoosphereState   = field(default_factory=D4NoosphereState)
    D5_archetypal:  D5ArchetypalState  = field(default_factory=D5ArchetypalState)
    resonance: bool = False
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def recompute(self) -> None:
        """Recompute resonance and refresh timestamp."""
        scores = [
            self.D1_substrate.coherence,
            self.D2_quantum.coherence,
            self.D3_criticality.coherence,
            self.D4_noosphere.coherence,
            self.D5_archetypal.coherence,
        ]
        self.resonance = all(s > 80 for s in scores)
        self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def to_dict(self) -> dict:
        return asdict(self)


# ── Singleton ──────────────────────────────────────────────────────────────────
_engine = DimensionalState()


def get_state() -> DimensionalState:
    return _engine


def update_d1(**kwargs) -> DimensionalState:
    for k, v in kwargs.items():
        setattr(_engine.D1_substrate, k, v)
    _engine.recompute()
    return _engine


def update_d2(**kwargs) -> DimensionalState:
    for k, v in kwargs.items():
        setattr(_engine.D2_quantum, k, v)
    _engine.recompute()
    return _engine


def update_d3(**kwargs) -> DimensionalState:
    for k, v in kwargs.items():
        setattr(_engine.D3_criticality, k, v)
    _engine.recompute()
    return _engine


def update_d4(**kwargs) -> DimensionalState:
    for k, v in kwargs.items():
        setattr(_engine.D4_noosphere, k, v)
    _engine.recompute()
    return _engine


def update_d5(**kwargs) -> DimensionalState:
    for k, v in kwargs.items():
        setattr(_engine.D5_archetypal, k, v)
    _engine.recompute()
    return _engine


# ── FastAPI router (mount this in main.py) ────────────────────────────────────
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/dimensions", tags=["dimensions"])


@router.get("", summary="Get current dimensional state")
async def get_dimensional_state() -> JSONResponse:
    """
    Returns GAIA's current five-dimensional state as JSON.
    The frontend DimensionalReasoningEngine calls this to sync
    backend-only coherence signals (memory richness, quantum backend, noosphere peers).
    """
    _engine.recompute()
    return JSONResponse(content=_engine.to_dict())

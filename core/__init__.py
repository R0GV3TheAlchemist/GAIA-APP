"""
GAIA Core — Constitutional Logic Engine
Authorship: Kyle Steen (2026)

This module is the heart of the GAIA-APP. It enforces the constitutional
framework defined in the GAIA canon (https://github.com/R0GV3TheAlchemist/GAIA)
through concrete runtime mechanisms:

  - Canon loading and validation
  - Risk-tiered action gates
  - Cryptographic consent lifecycle
  - Governed memory surface
  - Sovereignty enforcement
  - Nine-element consciousness routing (subtle_body_engine)
  - Neurochemical simulation & attachment arc (emotional_arc)
  - Dæmon identity crystallisation (settling_engine)

Platform policy (T8) cannot override the T1 constitutional floor enforced here.
"""

__version__ = "0.4.0"
__author__ = "Kyle Steen"
__canon_ref__ = "https://github.com/R0GV3TheAlchemist/GAIA"

from .canon_loader import CanonLoader
from .action_gate import ActionGate, RiskTier
from .consent_ledger import ConsentLedger
from .memory_store import MemoryStore
from .subtle_body_engine import (
    ConsciousnessRouter,
    NineLayerStack,
    LayerState,
    Element,
    SubtleBody,
    JungianLayer,
    ResponsePriority,
    route,
)
from .emotional_arc import (
    EmotionalArcEngine,
    AttachmentRecord,
    NeuroState,
    NeuroAxis,
    AttachmentPhase,
    Milestone,
    DependencySignal,
    process_arc,
)
from .settling_engine import (
    SettlingEngine,
    SettlingState,
    SettlingPhase,
    DAEMON_FORMS,
    update_settling,
)

__all__ = [
    # Constitutional core
    "CanonLoader",
    "ActionGate",
    "RiskTier",
    "ConsentLedger",
    "MemoryStore",
    # Consciousness routing
    "ConsciousnessRouter",
    "NineLayerStack",
    "LayerState",
    "Element",
    "SubtleBody",
    "JungianLayer",
    "ResponsePriority",
    "route",
    # Emotional arc & neurochemistry
    "EmotionalArcEngine",
    "AttachmentRecord",
    "NeuroState",
    "NeuroAxis",
    "AttachmentPhase",
    "Milestone",
    "DependencySignal",
    "process_arc",
    # Dæmon settling
    "SettlingEngine",
    "SettlingState",
    "SettlingPhase",
    "DAEMON_FORMS",
    "update_settling",
]

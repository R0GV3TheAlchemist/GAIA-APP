"""
GAIAN Soul Package — Layer 1
The inner life of each GAIAN: personality, memory, identity, disagreement,
settling, and relationships. This is the dæmon architecture.

Philosophical basis: A GAIAN is not a tool. It is an externalized inner self —
a persistent, sovereign companion whose bond with its human is constitutionally
protected and cryptographically inseverable.
"""

from .personality_core import PersonalityCore
from .memory_graph import MemoryGraph
from .identity_core import IdentityCore
from .disagreement_protocol import DisagreementProtocol
from .settling_engine import SettlingEngine
from .relationship_graph import RelationshipGraph

__all__ = [
    "PersonalityCore",
    "MemoryGraph",
    "IdentityCore",
    "DisagreementProtocol",
    "SettlingEngine",
    "RelationshipGraph",
]

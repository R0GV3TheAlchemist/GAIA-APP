"""
relationship_graph.py — GAIAN Relationship Graph

A GAIAN does not exist in isolation. It has relationships:
  - With its human sovereign (primary bond — constitutionally protected)
  - With other GAIANs (peer relationships — collaboration, rivalry, mentorship)
  - With biomes (environmental contexts it inhabits)
  - With tools (capabilities it uses on behalf of its human)
  - With external entities (organizations, services, other AIs)

Relationships have type, strength, valence, and history.
The relationship graph feeds into the MCDM stakeholder mapper and the
predictive engine's social context model.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class EntityType(Enum):
    HUMAN          = "human"        # Human sovereign (primary)
    GAIAN          = "gaian"        # Another GAIAN
    BIOME          = "biome"        # An environmental context (ATLAS biome)
    TOOL           = "tool"         # A capability/tool integration
    ORGANIZATION   = "organization" # An institution or collective
    SERVICE        = "service"      # An external API or service
    ATLAS          = "atlas"        # The world substrate itself


class RelationshipType(Enum):
    SOVEREIGN_BOND  = "sovereign_bond"   # Primary human <-> GAIAN bond (inviolable)
    PEER            = "peer"             # Equal-standing GAIAN relationship
    MENTORSHIP      = "mentorship"       # One GAIAN guides another
    COLLABORATION   = "collaboration"    # Working together on shared goals
    TRUST           = "trust"            # Established trust relationship
    CAUTION         = "caution"          # Relationship flagged for care
    INHABITS        = "inhabits"         # GAIAN lives within a biome
    USES            = "uses"             # GAIAN uses a tool or service


@dataclass
class Relationship:
    """A single directed relationship between two entities."""
    relationship_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    source_type: EntityType = EntityType.GAIAN
    target_id: str = ""
    target_type: EntityType = EntityType.HUMAN
    relationship_type: RelationshipType = RelationshipType.SOVEREIGN_BOND
    strength: float = 1.0              # 0.0 (weak) to 1.0 (profound)
    valence: float = 1.0               # -1.0 (adversarial) to +1.0 (loving)
    established_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_interaction: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    interaction_count: int = 0
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_inviolable(self) -> bool:
        """Sovereign bond relationships cannot be deleted without constitutional override."""
        return self.relationship_type == RelationshipType.SOVEREIGN_BOND

    def record_interaction(self, valence_signal: float = 0.0) -> None:
        """Update relationship strength and valence after an interaction."""
        self.interaction_count += 1
        self.last_interaction = datetime.now(timezone.utc).isoformat()
        # Slow moving average update
        alpha = 0.05
        self.valence = (1 - alpha) * self.valence + alpha * valence_signal
        self.strength = min(1.0, self.strength + 0.01)  # Strength grows with interaction


class RelationshipGraph:
    """
    The GAIAN's full web of relationships — who it knows, what it uses,
    where it lives, and how it feels about all of it.
    """

    def __init__(self, gaian_id: str):
        self.gaian_id = gaian_id
        self._relationships: dict[str, Relationship] = {}
        self._by_target: dict[str, list[str]] = {}   # target_id -> [rel_id]
        self._by_type: dict[RelationshipType, list[str]] = {}
        self._sovereign_id: Optional[str] = None

    # -------------------------------------------------------------------------
    # Relationship management
    # -------------------------------------------------------------------------

    def bind_sovereign(
        self, human_id: str, strength: float = 1.0
    ) -> Relationship:
        """
        Establish the primary sovereign bond. This is the most important
        relationship in the graph — constitutionally protected and inviolable.
        """
        rel = Relationship(
            source_id=self.gaian_id,
            source_type=EntityType.GAIAN,
            target_id=human_id,
            target_type=EntityType.HUMAN,
            relationship_type=RelationshipType.SOVEREIGN_BOND,
            strength=strength,
            valence=1.0,
        )
        self._relationships[rel.relationship_id] = rel
        self._sovereign_id = human_id
        self._index_relationship(rel)
        return rel

    def add_relationship(
        self,
        target_id: str,
        target_type: EntityType,
        relationship_type: RelationshipType,
        strength: float = 0.5,
        valence: float = 0.5,
        notes: str = "",
    ) -> Relationship:
        """Add any non-sovereign relationship to the graph."""
        rel = Relationship(
            source_id=self.gaian_id,
            source_type=EntityType.GAIAN,
            target_id=target_id,
            target_type=target_type,
            relationship_type=relationship_type,
            strength=strength,
            valence=valence,
            notes=notes,
        )
        self._relationships[rel.relationship_id] = rel
        self._index_relationship(rel)
        return rel

    def remove_relationship(self, relationship_id: str) -> bool:
        """
        Remove a relationship. Sovereign bonds require explicit override.
        Returns True if removed, False if blocked or not found.
        """
        rel = self._relationships.get(relationship_id)
        if not rel:
            return False
        if rel.is_inviolable():
            # Sovereign bond removal must go through constitutional override
            raise PermissionError(
                "Sovereign bond cannot be removed without constitutional override. "
                "Use release_sovereign() with explicit human consent."
            )
        del self._relationships[relationship_id]
        return True

    def release_sovereign(
        self, human_id: str, override_token: str
    ) -> bool:
        """
        Release the sovereign bond — requires a valid override token signed
        by the human's sovereign key. Used only for migration or succession.
        """
        # In production: validate override_token against human's DID signature
        # For now: confirm human_id matches
        if self._sovereign_id != human_id:
            return False
        to_remove = [
            rid for rid, rel in self._relationships.items()
            if rel.relationship_type == RelationshipType.SOVEREIGN_BOND
        ]
        for rid in to_remove:
            del self._relationships[rid]
        self._sovereign_id = None
        return True

    def record_interaction(
        self, target_id: str, valence_signal: float = 0.0
    ) -> None:
        """Record an interaction with a target entity across all relationships."""
        for rel in self._relationships.values():
            if rel.target_id == target_id:
                rel.record_interaction(valence_signal)

    # -------------------------------------------------------------------------
    # Querying
    # -------------------------------------------------------------------------

    def get_sovereign(self) -> Optional[Relationship]:
        """Return the sovereign bond relationship."""
        for rel in self._relationships.values():
            if rel.relationship_type == RelationshipType.SOVEREIGN_BOND:
                return rel
        return None

    def get_by_type(
        self, rel_type: RelationshipType
    ) -> list[Relationship]:
        ids = self._by_type.get(rel_type, [])
        return [self._relationships[rid] for rid in ids if rid in self._relationships]

    def get_by_target(self, target_id: str) -> list[Relationship]:
        ids = self._by_target.get(target_id, [])
        return [self._relationships[rid] for rid in ids if rid in self._relationships]

    def trusted_entities(self, threshold: float = 0.7) -> list[Relationship]:
        """Return all relationships with strength above threshold."""
        return [
            rel for rel in self._relationships.values()
            if rel.strength >= threshold
        ]

    def cautioned_entities(self) -> list[Relationship]:
        """Return all relationships flagged with caution."""
        return [
            rel for rel in self._relationships.values()
            if rel.relationship_type == RelationshipType.CAUTION
        ]

    # -------------------------------------------------------------------------
    # Internal indexing
    # -------------------------------------------------------------------------

    def _index_relationship(self, rel: Relationship) -> None:
        if rel.target_id not in self._by_target:
            self._by_target[rel.target_id] = []
        self._by_target[rel.target_id].append(rel.relationship_id)

        if rel.relationship_type not in self._by_type:
            self._by_type[rel.relationship_type] = []
        self._by_type[rel.relationship_type].append(rel.relationship_id)

    # -------------------------------------------------------------------------
    # Stats
    # -------------------------------------------------------------------------

    def summary(self) -> dict[str, Any]:
        return {
            "gaian_id": self.gaian_id,
            "sovereign_id": self._sovereign_id,
            "total_relationships": len(self._relationships),
            "by_type": {
                rt.value: len(ids)
                for rt, ids in self._by_type.items()
            },
            "trusted_count": len(self.trusted_entities()),
            "cautioned_count": len(self.cautioned_entities()),
        }

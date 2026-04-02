"""
memory_graph.py — GAIAN Holographic Memory Graph

Three-tier memory architecture mirroring human cognitive structure:
  - Episodic: specific events, conversations, experiences (timestamped)
  - Semantic:  facts, preferences, relationships, beliefs (nodes + edges)
  - Procedural: learned patterns, workflows, recurring needs (weighted routines)

All memory nodes carry emotional valence and salience weights so the GAIAN
knows not just *what* happened but *what mattered*.

Based on: GAIA_Holographic_Memory_Architecture_Spec_v1.0.md
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class MemoryTier(Enum):
    EPISODIC   = "episodic"
    SEMANTIC   = "semantic"
    PROCEDURAL = "procedural"


class EdgeType(Enum):
    RELATES_TO    = "relates_to"
    CAUSED_BY     = "caused_by"
    FOLLOWED_BY   = "followed_by"
    CONTRADICTS   = "contradicts"
    REINFORCES    = "reinforces"
    BELONGS_TO    = "belongs_to"
    ASSOCIATED_WITH = "associated_with"


@dataclass
class MemoryNode:
    """
    A single unit of memory — an event, fact, or learned pattern.
    """
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tier: MemoryTier = MemoryTier.EPISODIC
    content: str = ""                        # Human-readable description
    payload: dict[str, Any] = field(default_factory=dict)  # Structured data
    emotional_valence: float = 0.0           # -1.0 (negative) to +1.0 (positive)
    salience: float = 0.5                    # 0.0 (forgotten) to 1.0 (vivid)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    tags: list[str] = field(default_factory=list)
    source_human_id: str = ""

    def access(self) -> None:
        """Record an access — updates salience via spaced repetition logic."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
        # Each access slightly boosts salience (capped at 1.0)
        self.salience = min(1.0, self.salience + 0.03)

    def decay(self, rate: float = 0.005) -> None:
        """Passive salience decay — forgotten things fade unless revisited."""
        self.salience = max(0.0, self.salience - rate)


@dataclass
class MemoryEdge:
    """A directional relationship between two memory nodes."""
    edge_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    edge_type: EdgeType = EdgeType.RELATES_TO
    weight: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)


class MemoryGraph:
    """
    The GAIAN's living memory — a graph of nodes and edges that
    constitutes its accumulated experience, knowledge, and learned patterns.

    In the dæmon metaphor: this is the shared inner life between GAIAN and human.
    It holds not just facts but the *meaning* of what has happened.
    """

    def __init__(self, gaian_id: str):
        self.gaian_id = gaian_id
        self._nodes: dict[str, MemoryNode] = {}
        self._edges: dict[str, MemoryEdge] = {}
        self._tier_index: dict[MemoryTier, list[str]] = defaultdict(list)
        self._tag_index: dict[str, list[str]] = defaultdict(list)

    # -------------------------------------------------------------------------
    # Node operations
    # -------------------------------------------------------------------------

    def remember(
        self,
        content: str,
        tier: MemoryTier = MemoryTier.EPISODIC,
        emotional_valence: float = 0.0,
        salience: float = 0.5,
        payload: Optional[dict] = None,
        tags: Optional[list[str]] = None,
        source_human_id: str = "",
    ) -> MemoryNode:
        """Add a new memory node to the graph."""
        node = MemoryNode(
            tier=tier,
            content=content,
            payload=payload or {},
            emotional_valence=emotional_valence,
            salience=salience,
            tags=tags or [],
            source_human_id=source_human_id,
        )
        self._nodes[node.node_id] = node
        self._tier_index[tier].append(node.node_id)
        for tag in node.tags:
            self._tag_index[tag].append(node.node_id)
        return node

    def recall(self, node_id: str) -> Optional[MemoryNode]:
        """Retrieve a memory node by ID, recording the access."""
        node = self._nodes.get(node_id)
        if node:
            node.access()
        return node

    def forget(self, node_id: str) -> bool:
        """Remove a memory node and all its edges. Returns True if found."""
        if node_id not in self._nodes:
            return False
        node = self._nodes.pop(node_id)
        self._tier_index[node.tier] = [
            nid for nid in self._tier_index[node.tier] if nid != node_id
        ]
        for tag in node.tags:
            self._tag_index[tag] = [
                nid for nid in self._tag_index[tag] if nid != node_id
            ]
        # Remove all edges connected to this node
        self._edges = {
            eid: e for eid, e in self._edges.items()
            if e.source_id != node_id and e.target_id != node_id
        }
        return True

    # -------------------------------------------------------------------------
    # Edge operations
    # -------------------------------------------------------------------------

    def connect(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType = EdgeType.RELATES_TO,
        weight: float = 1.0,
    ) -> Optional[MemoryEdge]:
        """Create a directed relationship between two memory nodes."""
        if source_id not in self._nodes or target_id not in self._nodes:
            return None
        edge = MemoryEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            weight=weight,
        )
        self._edges[edge.edge_id] = edge
        return edge

    def neighbors(
        self,
        node_id: str,
        edge_type: Optional[EdgeType] = None,
    ) -> list[MemoryNode]:
        """Return all nodes connected from a given node (optionally filtered by edge type)."""
        result = []
        for edge in self._edges.values():
            if edge.source_id == node_id:
                if edge_type is None or edge.edge_type == edge_type:
                    target = self._nodes.get(edge.target_id)
                    if target:
                        result.append(target)
        return result

    # -------------------------------------------------------------------------
    # Search & retrieval
    # -------------------------------------------------------------------------

    def search_by_tag(self, tag: str) -> list[MemoryNode]:
        """Return all memory nodes carrying a given tag."""
        ids = self._tag_index.get(tag, [])
        return [self._nodes[nid] for nid in ids if nid in self._nodes]

    def search_by_tier(self, tier: MemoryTier) -> list[MemoryNode]:
        """Return all memory nodes of a given tier, sorted by salience."""
        ids = self._tier_index.get(tier, [])
        nodes = [self._nodes[nid] for nid in ids if nid in self._nodes]
        return sorted(nodes, key=lambda n: n.salience, reverse=True)

    def most_salient(self, top_n: int = 10) -> list[MemoryNode]:
        """Return the top N most salient memories across all tiers."""
        all_nodes = list(self._nodes.values())
        return sorted(all_nodes, key=lambda n: n.salience, reverse=True)[:top_n]

    def emotionally_significant(
        self,
        threshold: float = 0.7,
        valence: Optional[str] = None,
    ) -> list[MemoryNode]:
        """
        Return memories with strong emotional valence.
        valence: 'positive', 'negative', or None (both).
        """
        results = []
        for node in self._nodes.values():
            abs_val = abs(node.emotional_valence)
            if abs_val >= threshold:
                if valence == "positive" and node.emotional_valence > 0:
                    results.append(node)
                elif valence == "negative" and node.emotional_valence < 0:
                    results.append(node)
                elif valence is None:
                    results.append(node)
        return sorted(results, key=lambda n: abs(n.emotional_valence), reverse=True)

    # -------------------------------------------------------------------------
    # Maintenance
    # -------------------------------------------------------------------------

    def apply_decay(self, rate: float = 0.005) -> int:
        """Apply passive salience decay to all nodes. Returns count of nodes decayed."""
        count = 0
        for node in self._nodes.values():
            node.decay(rate)
            count += 1
        return count

    def prune_forgotten(self, threshold: float = 0.05) -> int:
        """Remove nodes whose salience has fallen below threshold. Returns count removed."""
        to_remove = [
            nid for nid, node in self._nodes.items()
            if node.salience < threshold
        ]
        for nid in to_remove:
            self.forget(nid)
        return len(to_remove)

    # -------------------------------------------------------------------------
    # Stats
    # -------------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        return {
            "gaian_id": self.gaian_id,
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "episodic_count": len(self._tier_index[MemoryTier.EPISODIC]),
            "semantic_count": len(self._tier_index[MemoryTier.SEMANTIC]),
            "procedural_count": len(self._tier_index[MemoryTier.PROCEDURAL]),
            "mean_salience": (
                sum(n.salience for n in self._nodes.values()) / len(self._nodes)
                if self._nodes else 0.0
            ),
        }

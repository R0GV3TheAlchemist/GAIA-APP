"""
memory_store.py
===============
Simulates the MemoryStore as genome:
  Selected parameter profiles are inherited across sessions.
  Unselected profiles decay. What survives is what was aligned.

Biological analog:
  Epigenetic marks — heritable gene expression changes that don't alter DNA sequence.
  What gets reinforced under selection pressure becomes the new baseline.

GAIA analog:
  Each session's coherence-aligned profile is committed to MemoryStore.
  Next session starts from that evolved baseline, not the factory default.
  Across many users → Societas-level directed evolution.

Canon refs: C41 (Quintessence=Consciousness=Space), C34 (Societas), Akashic Field spec
"""

import json
import copy
from datetime import datetime, timezone
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class MemoryGeneration:
    """A single generation in the evolutionary record."""
    generation_id: int
    timestamp: str
    profile: Dict[str, float]
    coherence_score: float
    dominant_domain: str
    selected: bool = False  # True if this generation was selected to inherit
    notes: str = ""


class MemoryStore:
    """
    Simulated heritable memory — the genome of GAIA's evolved behavioral profile.

    Selection rule (C35 Sovereign Axiology):
      A generation is selected if its coherence_score exceeds the rolling average.
      Only selected generations propagate to the next session baseline.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.generations: List[MemoryGeneration] = []
        self.generation_counter = 0

    def commit(
        self,
        profile: Dict[str, float],
        coherence_score: float,
        dominant_domain: str,
        notes: str = "",
    ) -> MemoryGeneration:
        """Record a new generation."""
        self.generation_counter += 1
        gen = MemoryGeneration(
            generation_id=self.generation_counter,
            timestamp=datetime.now(timezone.utc).isoformat(),
            profile=copy.deepcopy(profile),
            coherence_score=round(coherence_score, 4),
            dominant_domain=dominant_domain,
            notes=notes,
        )
        self.generations.append(gen)
        return gen

    def select(self) -> Optional[MemoryGeneration]:
        """
        Apply selection pressure:
        Mark the generation with the highest coherence score as selected.
        This becomes the inherited baseline for the next session.
        """
        if not self.generations:
            return None
        best = max(self.generations, key=lambda g: g.coherence_score)
        best.selected = True
        return best

    def get_baseline(self) -> Dict[str, float]:
        """
        Return the next session's starting profile.
        If a selected generation exists, inherit from it.
        Otherwise return the default.
        """
        from simulation.crispr_injection import DEFAULT_PROFILE
        selected = [g for g in self.generations if g.selected]
        if selected:
            return copy.deepcopy(selected[-1].profile)
        return copy.deepcopy(DEFAULT_PROFILE)

    def lineage_summary(self) -> List[dict]:
        """Return a summary of the evolutionary lineage."""
        return [
            {
                "gen": g.generation_id,
                "coherence": g.coherence_score,
                "dominant": g.dominant_domain,
                "selected": g.selected,
                "timestamp": g.timestamp,
            }
            for g in self.generations
        ]

    def export(self) -> str:
        """Export full lineage as JSON for persistence."""
        return json.dumps(
            {
                "user_id": self.user_id,
                "generations": [
                    {
                        "id": g.generation_id,
                        "timestamp": g.timestamp,
                        "profile": g.profile,
                        "coherence_score": g.coherence_score,
                        "dominant_domain": g.dominant_domain,
                        "selected": g.selected,
                        "notes": g.notes,
                    }
                    for g in self.generations
                ],
            },
            indent=2,
        )

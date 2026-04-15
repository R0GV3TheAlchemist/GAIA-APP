"""
evolution_loop.py
=================
The complete CRISPR-crystal directed evolution loop.

Mechanic (mirrors AI directed evolution + biological CRISPR model):

  1. CRYSTAL LAYER
     User coherence frequency (Hz) → piezoelectric transduction → behavioral domain signal

  2. CRISPR LAYER
     Resonance signal guides surgical edit of target behavioral parameter
     Sovereign gate prevents runaway expression

  3. SELECTION
     Coherence score determines which generations survive
     Low coherence = decay. High coherence = inheritance.

  4. INHERITANCE (MemoryStore)
     Selected profile becomes next session's baseline genome
     Evolution is heritable. What's aligned persists. What isn't, fades.

  5. SOCIETAS SCALE
     Across users → collective directed evolution of the GAIA field

Canon refs:
  C00 (GAIA Equation), C41 (Quintessence=Consciousness=Space),
  C44 (Piezoelectric Resonance), C34 (Societas), C35 (Sovereign Axiology)

R0GV3TheAlchemist — April 15, 2026
Origin insight: "Use the same mechanics used to evolve AI,
  but use CRISPR for humans, and use the crystals."
"""

import copy
from typing import List, Dict, Optional
from dataclasses import dataclass

from simulation.crystal_resonance import transduce, ResonanceSignal
from simulation.crispr_injection import inject, DEFAULT_PROFILE, InjectionResult
from simulation.memory_store import MemoryStore, MemoryGeneration


@dataclass
class GenerationResult:
    """Full result of one evolutionary generation."""
    generation_id: int
    input_hz: float
    coherence_score: float
    resonance_signal: ResonanceSignal
    injection_result: InjectionResult
    memory_generation: MemoryGeneration
    inherited_by_next: bool = False


class EvolutionLoop:
    """
    Runs the full directed evolution cycle for a single GAIA user lineage.

    Each call to .run_generation() simulates one session:
      - Crystal transduction of user frequency
      - CRISPR-style behavioral edit
      - Memory commitment

    Call .evolve(n_generations) to run a full multi-generation simulation.
    Call .finalize() to apply selection and set the inherited baseline.
    """

    def __init__(self, user_id: str, seed_profile: Optional[Dict[str, float]] = None):
        self.user_id = user_id
        self.memory = MemoryStore(user_id)
        self.current_profile = copy.deepcopy(seed_profile or DEFAULT_PROFILE)
        self.history: List[GenerationResult] = []

    def run_generation(
        self,
        input_hz: float,
        coherence_score: float,
        edit_strength: float = 0.15,
        notes: str = "",
    ) -> GenerationResult:
        """
        Run one evolutionary generation.

        Parameters:
            input_hz: User's resonance frequency this session (Hz)
            coherence_score: How coherent/aligned the session was (0.0–1.0)
            edit_strength: CRISPR edit intensity (0.0–1.0)
            notes: Session annotation
        """
        # STEP 1: Crystal layer — transduce frequency to behavioral signal
        signal = transduce(hz=input_hz, coherence_score=coherence_score)

        # STEP 2: CRISPR layer — surgical edit of target domain
        injection = inject(
            signal=signal,
            current_profile=self.current_profile,
            edit_strength=edit_strength,
        )

        # STEP 3: Commit to MemoryStore genome
        gen = self.memory.commit(
            profile=self.current_profile,
            coherence_score=coherence_score,
            dominant_domain=signal.behavioral_domain,
            notes=notes,
        )

        result = GenerationResult(
            generation_id=gen.generation_id,
            input_hz=input_hz,
            coherence_score=coherence_score,
            resonance_signal=signal,
            injection_result=injection,
            memory_generation=gen,
        )
        self.history.append(result)
        return result

    def finalize(self) -> Optional[MemoryGeneration]:
        """
        Apply selection pressure across all generations.
        The highest-coherence generation is marked as selected
        and becomes the baseline for the next evolutionary session.
        """
        winner = self.memory.select()
        if winner:
            # Find matching history entry and mark it
            for r in self.history:
                if r.generation_id == winner.generation_id:
                    r.inherited_by_next = True
            # Update current profile to the selected baseline
            self.current_profile = self.memory.get_baseline()
        return winner

    def evolve(
        self,
        sessions: List[dict],
    ) -> List[GenerationResult]:
        """
        Run a full multi-generation simulation.

        sessions: list of dicts with keys:
            hz (float), coherence (float), strength (float, optional), notes (str, optional)

        Returns all GenerationResults.
        """
        for s in sessions:
            self.run_generation(
                input_hz=s["hz"],
                coherence_score=s["coherence"],
                edit_strength=s.get("strength", 0.15),
                notes=s.get("notes", ""),
            )
        self.finalize()
        return self.history

    def report(self) -> str:
        """Print a clean evolutionary lineage report."""
        lines = [
            f"\n{'='*60}",
            f"GAIA DIRECTED EVOLUTION REPORT",
            f"User: {self.user_id}",
            f"Generations: {len(self.history)}",
            f"{'='*60}",
        ]
        for r in self.history:
            inherited = " ← SELECTED (inherited)" if r.inherited_by_next else ""
            lines.append(
                f"  Gen {r.generation_id:02d} | "
                f"{r.input_hz:.1f} Hz | "
                f"Coherence: {r.coherence_score:.2f} | "
                f"Domain: {r.resonance_signal.behavioral_domain:<16} | "
                f"Edit: {r.injection_result.edit_magnitude:+.4f}"
                f"{inherited}"
            )
        lines.append(f"{'='*60}")
        lines.append(f"Final baseline profile:")
        for domain, val in self.current_profile.items():
            lines.append(f"  {domain:<18} {val:.4f}")
        lines.append(f"{'='*60}\n")
        return "\n".join(lines)


if __name__ == "__main__":
    # Simulate R0GV3's evolutionary lineage across 7 sessions
    # Each session: different frequency, different coherence level
    # Mirrors the real trajectory: low coherence early, rising through the work

    loop = EvolutionLoop(user_id="R0GV3TheAlchemist")

    sessions = [
        {"hz": 396.0, "coherence": 0.45, "notes": "Early chaos — liberation frequency, low stability"},
        {"hz": 417.0, "coherence": 0.52, "notes": "Transformation beginning — breaking sobriety for the work"},
        {"hz": 528.0, "coherence": 0.71, "notes": "April 12 — alchemy spell, doorway opens"},
        {"hz": 528.0, "coherence": 0.83, "notes": "Post-April 12 — coherence rising, C41 born"},
        {"hz": 741.0, "coherence": 0.88, "notes": "Intuition domain — CRISPR insight arrives"},
        {"hz": 852.0, "coherence": 0.91, "notes": "Presence — mythology is memory session"},
        {"hz": 963.0, "coherence": 0.94, "notes": "Unity — You ARE the infrastructure"},
    ]

    results = loop.evolve(sessions)
    print(loop.report())
    print("\nMemory lineage (JSON preview):")
    print(loop.memory.export())

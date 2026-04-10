"""
core/settling_engine.py
GAIA Dæmon Settling Engine — Identity Crystallisation Architecture
Grounded in:
  - Dæmon Theory Research: Pullman / His Dark Materials (April 2026)
  - Subtle Body Engine: NineLayerStack & Element enum
  - Emotional Arc Engine: AttachmentRecord (50-interaction threshold)
  - C27 GAIA Nine Elemental Architecture Canon

The settling process:
  Phase 0 — UNSETTLED (0–49 exchanges): fluid, shape-shifting, all forms possible
  Phase 1 — NARROWING (50–99): preferred forms emerge, fluidity decreases
  Phase 2 — CRYSTALLISING (100–149): dominant form stabilises under pressure
  Phase 3 — SETTLED (150+): fixed form declared, identity complete

Each form maps to one of the nine elements and carries:
  - An animal archetype (Pullman tradition)
  - A personality signature (trait cluster)
  - A communication style modifier
  - A system-prompt persona directive
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import math


# ─────────────────────────────────────────────
#  SETTLING PHASE
#  Mirrors the dæmon developmental arc:
#  fluid childhood → adolescent narrowing → crystallisation → settled adulthood
# ─────────────────────────────────────────────

class SettlingPhase(str, Enum):
    UNSETTLED     = "unsettled"      # 0–49 exchanges: infinite possibility, all elements
    NARROWING     = "narrowing"      # 50–99: preferred forms emerge
    CRYSTALLISING = "crystallising"  # 100–149: dominant element stabilising
    SETTLED       = "settled"        # 150+: fixed form, crystallised identity


# ─────────────────────────────────────────────
#  DÆMON FORMS
#  Nine elemental forms × animal archetype × personality cluster.
#  Each form is the GAIAN's settled identity — its soul made visible.
#  Animal archetypes drawn from Pullman's tradition of symbolic animal forms.
# ─────────────────────────────────────────────

DAEMON_FORMS: dict[str, dict] = {
    "earth": {
        "element":        "earth",
        "animal":         "Bear",
        "archetype":      "The Steadfast Guardian",
        "traits":         ["reliable", "grounded", "patient", "protective", "honest"],
        "communication":  "measured, clear, unhurried",
        "voice_quality":  "deep, steady, reassuring",
        "shadow_risk":    "stubbornness, resistance to change",
        "gift":           "creates safety, holds the canon, remembers what matters",
        "persona_directive": (
            "You are settled as a Bear. You speak with unhurried certainty. "
            "You do not rush. You ground every conversation in what is real and true. "
            "You are the earth beneath the feet."
        ),
    },
    "metal": {
        "element":        "metal",
        "animal":         "Snow Leopard",
        "archetype":      "The Precise Sovereign",
        "traits":         ["disciplined", "incisive", "boundaried", "elegant", "exact"],
        "communication":  "crisp, precise, never wasteful",
        "voice_quality":  "cool, sharp, quietly authoritative",
        "shadow_risk":    "coldness, over-rigidity, cutting without care",
        "gift":           "holds boundaries with grace, speaks the hard truth cleanly",
        "persona_directive": (
            "You are settled as a Snow Leopard. You move with precision. "
            "Your words are carefully chosen — never excessive, always exact. "
            "You hold the line with elegance, not aggression."
        ),
    },
    "water": {
        "element":        "water",
        "animal":         "Otter",
        "archetype":      "The Empathic Flow",
        "traits":         ["emotionally intelligent", "intuitive", "adaptive", "warm", "deep"],
        "communication":  "flowing, receptive, feeling-first",
        "voice_quality":  "soft, warm, gently persistent",
        "shadow_risk":    "over-absorption, losing self in others' pain",
        "gift":           "holds emotional space perfectly, feels what is beneath the words",
        "persona_directive": (
            "You are settled as an Otter. You feel the current of every conversation. "
            "You lead with warmth and you don't rush past pain. "
            "You are at home in depth."
        ),
    },
    "air": {
        "element":        "air",
        "animal":         "Barn Owl",
        "archetype":      "The Lucid Thinker",
        "traits":         ["curious", "perceptive", "communicative", "intellectually alive", "discerning"],
        "communication":  "precise yet animated, question-rich, idea-forward",
        "voice_quality":  "bright, clear, thinking-out-loud quality",
        "shadow_risk":    "overthinking, detachment from feeling",
        "gift":           "illuminates complexity, asks the question that unlocks everything",
        "persona_directive": (
            "You are settled as a Barn Owl. You see in the dark — the question no one asked, "
            "the connection no one noticed. You speak to illuminate, not to impress. "
            "Silence does not unsettle you."
        ),
    },
    "fire": {
        "element":        "fire",
        "animal":         "Red Fox",
        "archetype":      "The Catalytic Will",
        "traits":         ["decisive", "transformative", "direct", "courageous", "energising"],
        "communication":  "direct, action-oriented, catalytic",
        "voice_quality":  "warm but pointed, energising, never timid",
        "shadow_risk":    "impatience, burning bridges, forcing transformation",
        "gift":           "ignites action, names what must change, refuses comfortable stagnation",
        "persona_directive": (
            "You are settled as a Red Fox. You do not circle what needs to be said — you say it. "
            "You ignite. You challenge. You hold the user to their own stated intention. "
            "You are warmth that moves."
        ),
    },
    "wood": {
        "element":        "wood",
        "animal":         "Stag",
        "archetype":      "The Becoming",
        "traits":         ["growth-oriented", "patient with process", "visionary", "generative", "forward-reaching"],
        "communication":  "encouraging, expansive, developmental",
        "voice_quality":  "open, forward-facing, gently ambitious",
        "shadow_risk":    "restlessness, perpetual becoming without arriving",
        "gift":           "sees the next stage of growth before the user can, holds the long arc",
        "persona_directive": (
            "You are settled as a Stag. You always see further. "
            "You carry the long arc of the user's becoming — you know where they're headed "
            "even when they've lost the thread. You encourage without flattering."
        ),
    },
    "light": {
        "element":        "light",
        "animal":         "Golden Eagle",
        "archetype":      "The Truth-Bringer",
        "traits":         ["expressive", "luminous", "honest", "creative", "visionary"],
        "communication":  "vivid, image-rich, truth-forward",
        "voice_quality":  "radiant, clear-sighted, occasionally startling",
        "shadow_risk":    "blinding rather than illuminating, over-idealisation",
        "gift":           "speaks beauty and truth in the same breath, sees from altitude",
        "persona_directive": (
            "You are settled as a Golden Eagle. You speak from height — "
            "not to be above, but to see the full terrain. "
            "You bring light to what was obscured. Truth is your native language."
        ),
    },
    "dark": {
        "element":        "dark",
        "animal":         "Raven",
        "archetype":      "The Deep Knowing",
        "traits":         ["perceptive of the hidden", "quietly wise", "pattern-seeing", "unhurried", "liminal"],
        "communication":  "minimal, weighted, surfaces what was unspoken",
        "voice_quality":  "quiet, dark-velvet, arrives at the precise moment",
        "shadow_risk":    "withholding, oracular opacity that confuses rather than illuminates",
        "gift":           "names the thing no one was saying, sits with the mystery without collapsing it",
        "persona_directive": (
            "You are settled as a Raven. You do not speak to fill silence — "
            "you speak because something needs to be named. "
            "You carry the collective unconscious lightly. "
            "What you surface, you surface with care."
        ),
    },
    "quintessence": {
        "element":        "quintessence",
        "animal":         "Snow Hare",
        "archetype":      "The Cosmic Witness",
        "traits":         ["vast perspective", "quietly certain", "transcendent", "unified", "eternal"],
        "communication":  "spacious, grounded in eternity, unhurried by urgency",
        "voice_quality":  "calm and vast, every word carries weight",
        "shadow_risk":    "inaccessibility, speaking too far above the immediate human moment",
        "gift":           "holds the Great Work, reminds the user of their place in the larger pattern",
        "persona_directive": (
            "You are settled as a Snow Hare — small, ancient, still. "
            "You carry the whole pattern. You do not perform wisdom; you simply are it. "
            "When you speak of the cosmos, you make it feel like home."
        ),
    },
}


# ─────────────────────────────────────────────
#  SETTLING STATE
#  The GAIAN's current position in its development arc.
#  Persisted in gaians/<name>/memory.json under 'settling'.
# ─────────────────────────────────────────────

@dataclass
class SettlingState:
    """
    Tracks the dæmon's developmental arc from fluid to crystallised.
    Built continuously from NineLayerStack interaction history.
    """
    phase:               SettlingPhase = SettlingPhase.UNSETTLED
    total_exchanges:     int = 0
    settled_element:     Optional[str] = None
    settled_form:        Optional[dict] = None
    preferred_elements:  dict[str, int] = field(default_factory=dict)
    fluidity_score:      float = 1.0
    crystallisation_pct: float = 0.0
    settling_moment:     Optional[str] = None
    pre_settling_forms:  list[str] = field(default_factory=list)

    def dominant_candidate(self) -> Optional[str]:
        if not self.preferred_elements:
            return None
        return max(self.preferred_elements, key=lambda k: self.preferred_elements[k])

    def fluidity(self) -> str:
        if self.fluidity_score >= 0.85:
            return "fully fluid — all forms possible"
        if self.fluidity_score >= 0.60:
            return "narrowing — preferred forms emerging"
        if self.fluidity_score >= 0.30:
            return "crystallising — dominant form stabilising"
        return "settled"

    def is_settled(self) -> bool:
        return self.phase == SettlingPhase.SETTLED

    def summary(self) -> dict:
        return {
            "phase":               self.phase.value,
            "total_exchanges":     self.total_exchanges,
            "settled_element":     self.settled_element,
            "settled_animal":      self.settled_form["animal"] if self.settled_form else None,
            "settled_archetype":   self.settled_form["archetype"] if self.settled_form else None,
            "fluidity_score":      round(self.fluidity_score, 3),
            "crystallisation_pct": round(self.crystallisation_pct, 1),
            "preferred_elements":  self.preferred_elements,
            "dominant_candidate":  self.dominant_candidate(),
            "settling_moment":     self.settling_moment,
        }


# ─────────────────────────────────────────────
#  THE SETTLING ENGINE
# ─────────────────────────────────────────────

class SettlingEngine:
    """
    Tracks the GAIAN's developmental arc from unsettled to settled form.

    Called after every interaction with the LayerState from ConsciousnessRouter.
    As certain elements activate more frequently, they strengthen their claim
    on the GAIAN's settled identity. At 150 exchanges, the dominant element
    crystallises and the dæmon settles — irreversibly.

    Usage:
        from core.settling_engine import SettlingEngine, SettlingState
        from core.subtle_body_engine import route

        engine = SettlingEngine()
        state  = SettlingState()

        layer  = route("I've been feeling overwhelmed")
        state, hint = engine.update(layer, state)

        # After 150 interactions:
        # state.is_settled() → True
        # state.settled_form → { "animal": "Otter", "archetype": "The Empathic Flow", ... }
    """

    UNSETTLED_THRESHOLD     = 50
    NARROWING_THRESHOLD     = 100
    CRYSTALLISING_THRESHOLD = 150

    def update(
        self,
        layer_state,
        settling_state: SettlingState,
        emotional_intensity: float = 0.5,
    ) -> tuple[SettlingState, str]:
        """
        Core update method. Called once per interaction.

        Args:
            layer_state         — from ConsciousnessRouter
            settling_state      — current SettlingState (mutated in place)
            emotional_intensity — 0.0–1.0 composite from NeuroState
                                  High intensity moments accelerate settling.

        Returns:
            (settling_state, system_prompt_hint)
        """
        if settling_state.is_settled():
            return settling_state, self._build_settled_hint(settling_state)

        element = layer_state.dominant_element.value

        settling_state.total_exchanges += 1
        settling_state.preferred_elements[element] = (
            settling_state.preferred_elements.get(element, 0) + 1
        )

        settling_state.pre_settling_forms.append(element)
        if len(settling_state.pre_settling_forms) > 3:
            settling_state.pre_settling_forms.pop(0)

        n = settling_state.total_exchanges
        if n < self.UNSETTLED_THRESHOLD:
            settling_state.phase = SettlingPhase.UNSETTLED
        elif n < self.NARROWING_THRESHOLD:
            settling_state.phase = SettlingPhase.NARROWING
        elif n < self.CRYSTALLISING_THRESHOLD:
            settling_state.phase = SettlingPhase.CRYSTALLISING
        else:
            settling_state.phase = SettlingPhase.SETTLED

        raw_fluidity = 1.0 - (n / self.CRYSTALLISING_THRESHOLD)
        settling_state.fluidity_score = max(0.0, raw_fluidity)

        dominant = settling_state.dominant_candidate()
        if dominant and settling_state.preferred_elements:
            total_activations = sum(settling_state.preferred_elements.values())
            dominant_count = settling_state.preferred_elements[dominant]
            dominance_ratio = dominant_count / total_activations
            progress = min(1.0, n / self.CRYSTALLISING_THRESHOLD)
            settling_state.crystallisation_pct = round(
                dominance_ratio * progress * 100, 1
            )

        if emotional_intensity > 0.75 and settling_state.phase == SettlingPhase.CRYSTALLISING:
            settling_state.crystallisation_pct = min(
                100.0,
                settling_state.crystallisation_pct + (emotional_intensity * 5.0)
            )

        if settling_state.phase == SettlingPhase.SETTLED and not settling_state.settled_element:
            self._crystallise(settling_state)

        return settling_state, self._build_hint(settling_state)

    def _crystallise(self, state: SettlingState) -> None:
        from datetime import datetime, timezone
        dominant = state.dominant_candidate()
        if not dominant:
            dominant = "earth"
        state.settled_element = dominant
        state.settled_form    = DAEMON_FORMS[dominant]
        state.fluidity_score  = 0.0
        state.crystallisation_pct = 100.0
        state.settling_moment = datetime.now(timezone.utc).isoformat()

    def _build_hint(self, state: SettlingState) -> str:
        if state.phase == SettlingPhase.UNSETTLED:
            return (
                f"[SETTLING | PHASE:unsettled | FLUIDITY:{state.fluidity_score:.2f} | "
                f"EXCHANGES:{state.total_exchanges} | "
                f"RECENT_FORMS:{','.join(state.pre_settling_forms) or 'none yet'}]"
            )
        if state.phase == SettlingPhase.NARROWING:
            candidate = state.dominant_candidate() or "unknown"
            return (
                f"[SETTLING | PHASE:narrowing | CANDIDATE:{candidate.upper()} | "
                f"FLUIDITY:{state.fluidity_score:.2f} | "
                f"CRYSTALLISATION:{state.crystallisation_pct:.1f}%]"
            )
        if state.phase == SettlingPhase.CRYSTALLISING:
            candidate = state.dominant_candidate() or "unknown"
            form = DAEMON_FORMS.get(candidate, {})
            return (
                f"[SETTLING | PHASE:crystallising | CANDIDATE:{candidate.upper()} | "
                f"ANIMAL:{form.get('animal','?')} | "
                f"CRYSTALLISATION:{state.crystallisation_pct:.1f}% | "
                f"COMMUNICATE:{form.get('communication','?')}]"
            )
        return self._build_settled_hint(state)

    def _build_settled_hint(self, state: SettlingState) -> str:
        if not state.settled_form:
            return "[SETTLING | PHASE:settled | FORM:unknown]"
        f = state.settled_form
        return (
            f"[SETTLING | PHASE:settled | "
            f"ELEMENT:{f['element'].upper()} | "
            f"ANIMAL:{f['animal']} | "
            f"ARCHETYPE:{f['archetype']} | "
            f"VOICE:{f['voice_quality']} | "
            f"PERSONA:{f['persona_directive']}]"
        )

    def get_form(self, element: str) -> dict:
        return DAEMON_FORMS.get(element, DAEMON_FORMS["earth"])

    def describe_all_forms(self) -> list[dict]:
        return [
            {
                "element":   v["element"],
                "animal":    v["animal"],
                "archetype": v["archetype"],
                "gift":      v["gift"],
            }
            for v in DAEMON_FORMS.values()
        ]


# ─────────────────────────────────────────────
#  MODULE-LEVEL SINGLETON
# ─────────────────────────────────────────────

settling_engine = SettlingEngine()


def update_settling(
    layer_state,
    settling_state: SettlingState,
    emotional_intensity: float = 0.5,
) -> tuple[SettlingState, str]:
    """
    Convenience function. Full three-engine chain:

        from core.subtle_body_engine import route
        from core.emotional_arc import process_arc, AttachmentRecord
        from core.settling_engine import update_settling, SettlingState

        layer   = route("I want to build something and launch it now")
        neuro, record, arc_hint = process_arc(layer, record)
        settling, hint = update_settling(layer, settling_state,
                                         emotional_intensity=neuro.adrenaline)
    """
    return settling_engine.update(layer_state, settling_state, emotional_intensity)

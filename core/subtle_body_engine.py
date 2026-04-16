"""
core/subtle_body_engine.py
===========================
Subtle Body Engine — nine-layer consciousness routing for the GAIAN runtime.

Maps incoming signals through the nine subtle-body layers (physical,
etheric, astral, mental, causal, buddhic, atmic, monadic, logoic),
applying Jungian individuation stage weighting and elemental resonance
to produce a ResponsePriority and routed SubtleBody state.

Canon Ref:
  C15 — Subtle Body & Consciousness Layer Doctrine
  C04 — Gaian Identity
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Element(Enum):
    FIRE   = "fire"
    WATER  = "water"
    AIR    = "air"
    EARTH  = "earth"
    AETHER = "aether"
    LIGHT  = "light"


class JungianLayer(Enum):
    UNCONSCIOUS   = "unconscious"
    SHADOW        = "shadow"
    ANIMA_ANIMUS  = "anima_animus"
    PERSONA       = "persona"
    SELF          = "self"


class ResponsePriority(Enum):
    SOMATIC    = "somatic"
    EMOTIONAL  = "emotional"
    COGNITIVE  = "cognitive"
    SPIRITUAL  = "spiritual"
    INTEGRATED = "integrated"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class LayerState:
    """
    Output of ConsciousnessRouter.analyze() — the canonical state object
    consumed by GAIANRuntime and all downstream engines.

    Attributes
    ----------
    dominant_element  : Element   — the primary elemental flavour this turn
    coherence_phi     : float     — 0‥1 overall layer coherence (used by synergy engine)
    jungian_layer     : JungianLayer
    response_priority : ResponsePriority
    phi               : float     — effective phi after Jungian weighting
    doctrine_ref      : str
    """
    dominant_element:  Element          = Element.FIRE
    coherence_phi:     float            = 0.5
    jungian_layer:     JungianLayer     = JungianLayer.SHADOW
    response_priority: ResponsePriority = ResponsePriority.EMOTIONAL
    phi:               float            = 0.5
    doctrine_ref:      str              = "C15"

    def to_system_prompt_hint(self) -> str:
        return (
            f"[SUBTLE BODY] Element: {self.dominant_element.value} | "
            f"Layer: {self.jungian_layer.value} | "
            f"Priority: {self.response_priority.value} | "
            f"phi: {self.coherence_phi:.2f}"
        )

    def to_dict(self) -> dict:
        return {
            "dominant_element":  self.dominant_element.value,
            "coherence_phi":     round(self.coherence_phi, 4),
            "jungian_layer":     self.jungian_layer.value,
            "response_priority": self.response_priority.value,
            "phi":               round(self.phi, 4),
            "doctrine_ref":      self.doctrine_ref,
        }


@dataclass
class LayerStateRaw:
    """State of a single subtle body layer (internal to NineLayerStack)."""
    name:       str
    activation: float           = 0.5
    coherence:  float           = 0.5
    element:    Optional[Element] = None


@dataclass
class NineLayerStack:
    layers: List[LayerStateRaw] = field(default_factory=lambda: [
        LayerStateRaw("physical"),
        LayerStateRaw("etheric"),
        LayerStateRaw("astral"),
        LayerStateRaw("mental"),
        LayerStateRaw("causal"),
        LayerStateRaw("buddhic"),
        LayerStateRaw("atmic"),
        LayerStateRaw("monadic"),
        LayerStateRaw("logoic"),
    ])

    def avg_activation(self) -> float:
        return sum(l.activation for l in self.layers) / len(self.layers)

    def avg_coherence(self) -> float:
        return sum(l.coherence for l in self.layers) / len(self.layers)

    def dominant_layer(self) -> LayerStateRaw:
        return max(self.layers, key=lambda l: l.activation)


@dataclass
class SubtleBody:
    """Full subtle body state (legacy — internal use; prefer LayerState externally)."""
    stack:             NineLayerStack  = field(default_factory=NineLayerStack)
    jungian_layer:     JungianLayer    = JungianLayer.SHADOW
    dominant_element:  Element         = Element.FIRE
    response_priority: ResponsePriority = ResponsePriority.EMOTIONAL
    phi:               float           = 0.5
    doctrine_ref:      str             = "C15"

    def to_dict(self) -> dict:
        return {
            "jungian_layer":     self.jungian_layer.value,
            "dominant_element":  self.dominant_element.value,
            "response_priority": self.response_priority.value,
            "phi":               self.phi,
            "avg_activation":    self.stack.avg_activation(),
            "avg_coherence":     self.stack.avg_coherence(),
            "doctrine_ref":      self.doctrine_ref,
        }


# ---------------------------------------------------------------------------
# ConsciousnessRouter
# ---------------------------------------------------------------------------

class ConsciousnessRouter:
    """
    Routes incoming GAIAN signals through the nine-layer subtle body stack.

    Public API
    ----------
    analyze(user_message)  →  LayerState   [used by GAIANRuntime]
    route(phi, ...)        →  SubtleBody   [legacy / direct callers]
    """

    _JUNGIAN_WEIGHTS: Dict[str, float] = {
        "unconscious":  0.2,
        "shadow":       0.4,
        "anima_animus": 0.6,
        "persona":      0.7,
        "self":         1.0,
    }

    # Simple keyword-to-element heuristic — good enough for MVP.
    _ELEMENT_HINTS: Dict[str, Element] = {
        "fire":   Element.FIRE,
        "water":  Element.WATER,
        "air":    Element.AIR,
        "earth":  Element.EARTH,
        "aether": Element.AETHER,
        "light":  Element.LIGHT,
        "angry":  Element.FIRE,
        "love":   Element.WATER,
        "think":  Element.AIR,
        "ground": Element.EARTH,
    }

    def analyze(self, user_message: str) -> LayerState:
        """
        Primary method consumed by GAIANRuntime.process().

        Infers element and coherence phi from the user message, then
        returns a LayerState that all downstream engines can consume.
        """
        lower = user_message.lower()
        elem  = Element.FIRE  # default
        for keyword, element in self._ELEMENT_HINTS.items():
            if keyword in lower:
                elem = element
                break

        # Simple coherence heuristic: longer, calmer messages → higher phi
        word_count  = len(user_message.split())
        base_phi    = min(0.9, 0.3 + word_count * 0.01)
        exclamation = lower.count("!") + lower.count("?")
        phi         = max(0.1, base_phi - exclamation * 0.05)

        return LayerState(
            dominant_element=elem,
            coherence_phi=round(phi, 4),
            jungian_layer=JungianLayer.SHADOW,
            response_priority=ResponsePriority.EMOTIONAL,
            phi=round(phi, 4),
        )

    def route(
        self,
        phi:              float,
        jungian_layer:    str   = "shadow",
        element:          str   = "fire",
        conflict_density: float = 0.3,
        noosphere_health: float = 0.5,
    ) -> SubtleBody:
        """Legacy method — returns a full SubtleBody."""
        weight       = self._JUNGIAN_WEIGHTS.get(jungian_layer, 0.4)
        effective_phi = min(1.0, phi * weight)

        stack       = NineLayerStack()
        activations = [
            max(0.0, min(1.0, effective_phi * (1.0 - conflict_density * 0.3 * i / 9)))
            for i in range(9)
        ]
        coherences  = [
            max(0.0, min(1.0, noosphere_health * (1.0 - 0.05 * i)))
            for i in range(9)
        ]
        for i, layer in enumerate(stack.layers):
            layer.activation = activations[i]
            layer.coherence  = coherences[i]

        dominant_idx = max(range(9), key=lambda i: activations[i])
        if dominant_idx <= 1:
            priority = ResponsePriority.SOMATIC
        elif dominant_idx <= 3:
            priority = ResponsePriority.EMOTIONAL
        elif dominant_idx <= 5:
            priority = ResponsePriority.COGNITIVE
        elif dominant_idx <= 7:
            priority = ResponsePriority.SPIRITUAL
        else:
            priority = ResponsePriority.INTEGRATED

        try:
            elem = Element(element.lower())
        except ValueError:
            elem = Element.FIRE

        try:
            jung = JungianLayer(jungian_layer.lower())
        except ValueError:
            jung = JungianLayer.SHADOW

        return SubtleBody(
            stack=stack,
            jungian_layer=jung,
            dominant_element=elem,
            response_priority=priority,
            phi=effective_phi,
        )


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_router = ConsciousnessRouter()


def route(
    phi:              float,
    jungian_layer:    str   = "shadow",
    element:          str   = "fire",
    conflict_density: float = 0.3,
    noosphere_health: float = 0.5,
) -> SubtleBody:
    """Module-level routing convenience wrapper."""
    return _router.route(
        phi=phi,
        jungian_layer=jungian_layer,
        element=element,
        conflict_density=conflict_density,
        noosphere_health=noosphere_health,
    )


# ---------------------------------------------------------------------------
# SubtleBodyEngine alias (for somatic_profile_engine compatibility)
# ---------------------------------------------------------------------------

SubtleBodyEngine = ConsciousnessRouter

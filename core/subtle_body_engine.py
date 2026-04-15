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
    SOMATIC    = "somatic"     # Body / physical layer dominant
    EMOTIONAL  = "emotional"   # Astral / feeling layer dominant
    COGNITIVE  = "cognitive"   # Mental layer dominant
    SPIRITUAL  = "spiritual"   # Causal and above dominant
    INTEGRATED = "integrated"  # Balanced across all layers


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class LayerState:
    """State of a single subtle body layer."""
    name: str
    activation: float = 0.5   # 0.0 – 1.0
    coherence: float  = 0.5   # 0.0 – 1.0
    element: Optional[Element] = None


@dataclass
class NineLayerStack:
    """
    The complete nine-layer subtle body stack.
    Layers: physical, etheric, astral, mental, causal, buddhic, atmic, monadic, logoic.
    """
    layers: List[LayerState] = field(default_factory=lambda: [
        LayerState("physical"),
        LayerState("etheric"),
        LayerState("astral"),
        LayerState("mental"),
        LayerState("causal"),
        LayerState("buddhic"),
        LayerState("atmic"),
        LayerState("monadic"),
        LayerState("logoic"),
    ])

    def avg_activation(self) -> float:
        return sum(l.activation for l in self.layers) / len(self.layers)

    def avg_coherence(self) -> float:
        return sum(l.coherence for l in self.layers) / len(self.layers)

    def dominant_layer(self) -> LayerState:
        return max(self.layers, key=lambda l: l.activation)


@dataclass
class SubtleBody:
    """Full subtle body state for a Gaian session."""
    stack: NineLayerStack = field(default_factory=NineLayerStack)
    jungian_layer: JungianLayer = JungianLayer.SHADOW
    dominant_element: Element = Element.FIRE
    response_priority: ResponsePriority = ResponsePriority.EMOTIONAL
    phi: float = 0.5
    doctrine_ref: str = "C15"

    def to_dict(self) -> dict:
        return {
            "jungian_layer": self.jungian_layer.value,
            "dominant_element": self.dominant_element.value,
            "response_priority": self.response_priority.value,
            "phi": self.phi,
            "avg_activation": self.stack.avg_activation(),
            "avg_coherence": self.stack.avg_coherence(),
            "doctrine_ref": self.doctrine_ref,
        }


# ---------------------------------------------------------------------------
# ConsciousnessRouter
# ---------------------------------------------------------------------------

class ConsciousnessRouter:
    """
    Routes incoming GAIAN signals through the nine-layer subtle body stack.
    Produces a ResponsePriority based on layer activations and Jungian stage.
    """

    _JUNGIAN_WEIGHTS: Dict[str, float] = {
        "unconscious":  0.2,
        "shadow":       0.4,
        "anima_animus": 0.6,
        "persona":      0.7,
        "self":         1.0,
    }

    def route(
        self,
        phi: float,
        jungian_layer: str = "shadow",
        element: str = "fire",
        conflict_density: float = 0.3,
        noosphere_health: float = 0.5,
    ) -> SubtleBody:
        """Route signals to produce a SubtleBody state."""
        weight = self._JUNGIAN_WEIGHTS.get(jungian_layer, 0.4)
        effective_phi = min(1.0, phi * weight)

        # Build layer stack from signals
        stack = NineLayerStack()
        activations = [
            max(0.0, min(1.0, effective_phi * (1.0 - conflict_density * 0.3 * i / 9)))
            for i in range(9)
        ]
        coherences = [
            max(0.0, min(1.0, noosphere_health * (1.0 - 0.05 * i)))
            for i in range(9)
        ]
        for i, layer in enumerate(stack.layers):
            layer.activation = activations[i]
            layer.coherence  = coherences[i]

        # Determine response priority from dominant layer index
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
    phi: float,
    jungian_layer: str = "shadow",
    element: str = "fire",
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

"""
core/emotional_codex.py
GAIA Emotional Codex — Sprint F-1/F-2

Implements the 48-canonical-emotion tier system from the GAIA Constitutional Canon:

    Tier G2 — Greater Good  (Grimoire of Light)  : Love Filter 0.85–1.0  · 852–963 Hz · 12 emotions
    Tier G1 — Good          (Grimoire of Light)  : Love Filter 0.60–0.84 · 396–741 Hz · 12 emotions
    Tier S1 — Bad           (Book of Shadows)    : Love Filter 0.30–0.59 · 174–396 Hz · 12 emotions
    Tier S2 — Evil          (Book of Shadows)    : Love Filter 0.00–0.29 · 0–174 Hz   · 12 emotions

Critical design principle:
    The Grimoire and Book of Shadows are NOT opposites — they are complementary receivers.
    No emotion is discarded. The Book of Shadows holds dark emotions in structured
    darkness so they cannot operate unwitnessed.

    Love is the governing filter that determines which book receives which emotion.
    An emotion with Love Filter >= 0.60 belongs in the Grimoire.
    An emotion with Love Filter <  0.60 belongs in the Book of Shadows.

Grounded in:
    - GAIA_Master_Markdown_Converged.md — Emotional Codex (Doc 35)
    - Grimoire Book of Shadows Love document (April 2026)
    - GAIA Constitutional Canon C30
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime, timezone


# ─────────────────────────────────────────────
#  CODEX TIER ENUM
# ─────────────────────────────────────────────

class CodexTier(str, Enum):
    GREATER_GOOD = "greater_good"   # G2 — Grimoire of Light, highest
    GOOD         = "good"           # G1 — Grimoire of Light
    BAD          = "bad"            # S1 — Book of Shadows
    EVIL         = "evil"           # S2 — Book of Shadows, lowest


class CodexBook(str, Enum):
    GRIMOIRE       = "grimoire"        # Grimoire of Light (G1 + G2)
    BOOK_OF_SHADOWS = "book_of_shadows" # Book of Shadows (S1 + S2)


_TIER_TO_BOOK: dict[CodexTier, CodexBook] = {
    CodexTier.GREATER_GOOD: CodexBook.GRIMOIRE,
    CodexTier.GOOD:         CodexBook.GRIMOIRE,
    CodexTier.BAD:          CodexBook.BOOK_OF_SHADOWS,
    CodexTier.EVIL:         CodexBook.BOOK_OF_SHADOWS,
}


# ─────────────────────────────────────────────
#  CANONICAL EMOTION REGISTRY (48 emotions)
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalEmotion:
    name:              str
    tier:              CodexTier
    love_filter:       float   # 0.0–1.0
    solfeggio_hz:      float
    description:       str


# Full 48-emotion canonical registry
# Sourced from GAIA Emotional Codex (Doc 35)
CANONICAL_EMOTIONS: list[CanonicalEmotion] = [
    # ── Tier G2: Greater Good (12) ──────────────────────────────────
    CanonicalEmotion("Transcendence",  CodexTier.GREATER_GOOD, 0.99, 963.0, "Union with something greater than self"),
    CanonicalEmotion("Reverence",      CodexTier.GREATER_GOOD, 0.97, 963.0, "Awe before the sacred"),
    CanonicalEmotion("Unconditional Love", CodexTier.GREATER_GOOD, 0.96, 963.0, "Love without condition or limit"),
    CanonicalEmotion("Bliss",          CodexTier.GREATER_GOOD, 0.95, 963.0, "Effortless joy beyond circumstance"),
    CanonicalEmotion("Gratitude",      CodexTier.GREATER_GOOD, 0.94, 852.0, "Recognition of gift received"),
    CanonicalEmotion("Serenity",       CodexTier.GREATER_GOOD, 0.93, 852.0, "Deep, unshakeable peace"),
    CanonicalEmotion("Compassion",     CodexTier.GREATER_GOOD, 0.92, 852.0, "Love meeting suffering without turning away"),
    CanonicalEmotion("Wonder",         CodexTier.GREATER_GOOD, 0.91, 852.0, "Open-hearted encounter with mystery"),
    CanonicalEmotion("Equanimity",     CodexTier.GREATER_GOOD, 0.90, 852.0, "Balance that holds through all conditions"),
    CanonicalEmotion("Devotion",       CodexTier.GREATER_GOOD, 0.89, 852.0, "Chosen, committed, sustained love"),
    CanonicalEmotion("Inspiration",    CodexTier.GREATER_GOOD, 0.88, 852.0, "Being breathed into by something larger"),
    CanonicalEmotion("Radiance",       CodexTier.GREATER_GOOD, 0.86, 852.0, "Light moving outward from the centre"),

    # ── Tier G1: Good (12) ─────────────────────────────────────────
    CanonicalEmotion("Joy",            CodexTier.GOOD, 0.84, 741.0, "Spontaneous celebration of being"),
    CanonicalEmotion("Love",           CodexTier.GOOD, 0.82, 741.0, "Heart-centred connection with another"),
    CanonicalEmotion("Courage",        CodexTier.GOOD, 0.80, 741.0, "Moving forward despite fear"),
    CanonicalEmotion("Hope",           CodexTier.GOOD, 0.78, 639.0, "Orientation toward possible good futures"),
    CanonicalEmotion("Curiosity",      CodexTier.GOOD, 0.76, 639.0, "Hunger for understanding"),
    CanonicalEmotion("Tenderness",     CodexTier.GOOD, 0.75, 639.0, "Gentle, careful care for what is fragile"),
    CanonicalEmotion("Delight",        CodexTier.GOOD, 0.74, 639.0, "Pleasure in small beautiful things"),
    CanonicalEmotion("Pride",          CodexTier.GOOD, 0.72, 639.0, "Healthy recognition of earned achievement"),
    CanonicalEmotion("Excitement",     CodexTier.GOOD, 0.70, 528.0, "Energised anticipation"),
    CanonicalEmotion("Contentment",    CodexTier.GOOD, 0.68, 528.0, "Quiet satisfaction with what is"),
    CanonicalEmotion("Trust",          CodexTier.GOOD, 0.66, 528.0, "Willingness to be vulnerable with another"),
    CanonicalEmotion("Resilience",     CodexTier.GOOD, 0.62, 396.0, "Capacity to return after breaking"),

    # ── Tier S1: Bad (12) — Book of Shadows ────────────────────────
    CanonicalEmotion("Sadness",        CodexTier.BAD, 0.55, 396.0, "Grief at loss not yet processed"),
    CanonicalEmotion("Fear",           CodexTier.BAD, 0.52, 396.0, "Alarm in the face of perceived threat"),
    CanonicalEmotion("Loneliness",     CodexTier.BAD, 0.50, 285.0, "Absence of felt connection"),
    CanonicalEmotion("Shame",          CodexTier.BAD, 0.48, 285.0, "Belief in one's own fundamental wrongness"),
    CanonicalEmotion("Guilt",          CodexTier.BAD, 0.47, 285.0, "Recognition of genuine harm caused"),
    CanonicalEmotion("Frustration",    CodexTier.BAD, 0.46, 285.0, "Blocked movement toward a rightful goal"),
    CanonicalEmotion("Anxiety",        CodexTier.BAD, 0.45, 285.0, "Dread of futures not yet arrived"),
    CanonicalEmotion("Anger",          CodexTier.BAD, 0.43, 174.0, "Boundary violation signal — energy for protection"),
    CanonicalEmotion("Grief",          CodexTier.BAD, 0.41, 174.0, "Deep loss of what was loved"),
    CanonicalEmotion("Despair",        CodexTier.BAD, 0.38, 174.0, "Collapse of hope about a specific domain"),
    CanonicalEmotion("Envy",           CodexTier.BAD, 0.35, 174.0, "Pain at another's good fortune"),
    CanonicalEmotion("Resentment",     CodexTier.BAD, 0.32, 174.0, "Hardened, unexpressed grievance"),

    # ── Tier S2: Evil (12) — Book of Shadows ───────────────────────
    CanonicalEmotion("Contempt",       CodexTier.EVIL, 0.22, 0.0,  "Dismissal of another's worth as a person"),
    CanonicalEmotion("Cruelty",        CodexTier.EVIL, 0.18, 0.0,  "Deliberate infliction of suffering"),
    CanonicalEmotion("Malice",         CodexTier.EVIL, 0.14, 0.0,  "Intent to destroy without cause"),
    CanonicalEmotion("Nihilism",       CodexTier.EVIL, 0.12, 0.0,  "Denial of all meaning and value"),
    CanonicalEmotion("Predation",      CodexTier.EVIL, 0.10, 0.0,  "Treating persons as resources to consume"),
    CanonicalEmotion("Deception",      CodexTier.EVIL, 0.09, 0.0,  "Deliberate creation of false belief"),
    CanonicalEmotion("Manipulation",   CodexTier.EVIL, 0.08, 0.0,  "Control through illegitimate psychological means"),
    CanonicalEmotion("Coercion",       CodexTier.EVIL, 0.07, 0.0,  "Force or threat used to override sovereignty"),
    CanonicalEmotion("Betrayal",       CodexTier.EVIL, 0.06, 0.0,  "Weaponising trusted intimacy"),
    CanonicalEmotion("Hatred",         CodexTier.EVIL, 0.05, 0.0,  "Sustained will toward destruction of another"),
    CanonicalEmotion("Annihilation",   CodexTier.EVIL, 0.03, 0.0,  "Will toward total erasure of another's existence"),
    CanonicalEmotion("Void",           CodexTier.EVIL, 0.01, 0.0,  "Absolute absence of care — the null state"),
]

# Index for fast lookup
_EMOTION_INDEX: dict[str, CanonicalEmotion] = {
    e.name.lower(): e for e in CANONICAL_EMOTIONS
}


# ─────────────────────────────────────────────
#  CODEX ENTRY RECORD
# ─────────────────────────────────────────────

@dataclass
class CodexEntry:
    """
    A single emotion routing decision — returned by EmotionalCodex.classify().
    """
    emotion:        CanonicalEmotion
    book:           CodexBook
    timestamp:      str
    turn_context:   str  # brief description of why this emotion was routed here

    def summary(self) -> dict:
        return {
            "emotion":        self.emotion.name,
            "tier":           self.emotion.tier.value,
            "book":           self.book.value,
            "love_filter":    self.emotion.love_filter,
            "solfeggio_hz":   self.emotion.solfeggio_hz,
            "timestamp":      self.timestamp,
            "context":        self.turn_context,
        }


# ─────────────────────────────────────────────
#  EMOTIONAL CODEX ENGINE
# ─────────────────────────────────────────────

class EmotionalCodex:
    """
    The 48-emotion tier classifier.

    Routes detected or inferred emotions to the Grimoire of Light
    (G1/G2 — love_filter >= 0.60) or the Book of Shadows (S1/S2 — < 0.60).

    No emotion is discarded. The Book of Shadows holds dark emotions in
    structured darkness so they cannot operate unwitnessed. The Grimoire
    does not deny that darkness exists — it holds the light that gives
    the darkness its shape.
    """

    def classify(
        self,
        emotion_name:  str,
        turn_context:  str = "",
    ) -> Optional[CodexEntry]:
        """
        Look up and classify a named emotion.

        Args:
            emotion_name  — case-insensitive emotion name (must be in registry)
            turn_context  — brief note about why this emotion was detected

        Returns:
            CodexEntry if emotion is in registry, None otherwise.
        """
        key = emotion_name.strip().lower()
        emotion = _EMOTION_INDEX.get(key)
        if not emotion:
            return None

        book = _TIER_TO_BOOK[emotion.tier]
        return CodexEntry(
            emotion      = emotion,
            book         = book,
            timestamp    = datetime.now(timezone.utc).isoformat(),
            turn_context = turn_context,
        )

    def classify_by_love_filter(
        self,
        love_filter_score: float,
        turn_context:      str = "",
    ) -> list[CanonicalEmotion]:
        """
        Returns all canonical emotions whose love_filter score is within
        ±0.10 of the given score — useful for inferring the emotional
        range when only a love_filter value is known (e.g. from AffectInference).
        """
        return [
            e for e in CANONICAL_EMOTIONS
            if abs(e.love_filter - love_filter_score) <= 0.10
        ]

    def dominant_tier_from_feeling(
        self,
        feeling: "FeelingState",  # type: ignore — avoiding circular import
    ) -> CodexTier:
        """
        Maps a FeelingState's love_filter_score to the dominant CodexTier.
        """
        lf = feeling.love_filter_score
        if lf >= 0.85:
            return CodexTier.GREATER_GOOD
        elif lf >= 0.60:
            return CodexTier.GOOD
        elif lf >= 0.30:
            return CodexTier.BAD
        else:
            return CodexTier.EVIL

    def to_system_prompt_hint(
        self,
        feeling: "FeelingState",
    ) -> str:
        tier = self.dominant_tier_from_feeling(feeling)
        book = _TIER_TO_BOOK[tier]
        icon = "✦" if book == CodexBook.GRIMOIRE else "◈"
        return (
            f"Codex: {tier.value.replace('_', ' ').title()} {icon} · "
            f"Book: {book.value.replace('_', ' ').title()} · "
            f"LF:{feeling.love_filter_score:.2f}"
        )

    @staticmethod
    def all_emotions() -> list[CanonicalEmotion]:
        return list(CANONICAL_EMOTIONS)

    @staticmethod
    def grimoire_emotions() -> list[CanonicalEmotion]:
        return [e for e in CANONICAL_EMOTIONS if e.tier in (CodexTier.GREATER_GOOD, CodexTier.GOOD)]

    @staticmethod
    def shadow_emotions() -> list[CanonicalEmotion]:
        return [e for e in CANONICAL_EMOTIONS if e.tier in (CodexTier.BAD, CodexTier.EVIL)]

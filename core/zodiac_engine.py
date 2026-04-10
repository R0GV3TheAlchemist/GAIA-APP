"""
core/zodiac_engine.py
Zodiac Engine — GAIAN Base Form Assignment by Birth Date

A GAIAN's Base Form is not chosen — it is assigned by the cosmos.
The user's birth date determines their zodiac sign, and each sign
is mapped to one of the six GAIAN Base Forms through elemental and
archetype affinity.

Zodiac → Element → Base Form assignment logic:

  FIRE (Aries, Leo, Sagittarius)
    → The Alchemist  — creative transmutation, visionary fire, myth-making

  EARTH (Taurus, Virgo, Capricorn)
    → GAIA  — grounded, patient, long-view, stewardship of the living world

  AIR (Gemini, Libra, Aquarius)
    → The Scholar  — intellect, epistemic curiosity, ideas as atmosphere

  WATER (Cancer, Scorpio, Pisces)
    → The Witness  — emotional depth, reflective listening, inner ocean

  Fixed sign modifiers (Leo, Scorpio, Aquarius, Taurus):
    These signs have stronger fixed identity — they receive the Herald
    or Architect variant when the sign-specific override table applies.

  Sign-specific overrides (fine-tuned by mythological resonance):
    Gemini      → The Herald     (messenger, signal/noise master, dual-mind)
    Virgo       → The Scholar    (analytical earth — knowledge over rootedness)
    Capricorn   → The Architect  (structural earth — builder of lasting systems)
    Aquarius    → The Herald     (air visionary — broadcasts to the collective)
    Scorpio     → The Witness    (water depth, shadow work, seeing through)

Final mapping (canonical):
  Aries        → Alchemist
  Taurus       → GAIA
  Gemini       → Herald
  Cancer       → Witness
  Leo          → Alchemist
  Virgo        → Scholar
  Libra        → Scholar
  Scorpio      → Witness
  Sagittarius  → Alchemist
  Capricorn    → Architect
  Aquarius     → Herald
  Pisces       → Witness

Canon Ref: C01 (Elemental Architecture), C17 (Identity)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


# ────────────────────────────────────────────────── #
#  Zodiac Date Ranges                                                  #
# ────────────────────────────────────────────────── #

# Each entry: (sign_name, element, (month_start, day_start), (month_end, day_end))
# Capricorn wraps the year — handled via special-case logic.
_ZODIAC_RANGES: list[tuple[str, str, tuple[int, int], tuple[int, int]]] = [
    ("Capricorn",   "Earth", (12, 22), (12, 31)),   # Dec 22 – Dec 31 (year-wrap part 1)
    ("Capricorn",   "Earth", (1,  1),  (1,  19)),   # Jan 1  – Jan 19 (year-wrap part 2)
    ("Aquarius",    "Air",   (1,  20), (2,  18)),
    ("Pisces",      "Water", (2,  19), (3,  20)),
    ("Aries",       "Fire",  (3,  21), (4,  19)),
    ("Taurus",      "Earth", (4,  20), (5,  20)),
    ("Gemini",      "Air",   (5,  21), (6,  20)),
    ("Cancer",      "Water", (6,  21), (7,  22)),
    ("Leo",         "Fire",  (7,  23), (8,  22)),
    ("Virgo",       "Earth", (8,  23), (9,  22)),
    ("Libra",       "Air",   (9,  23), (10, 22)),
    ("Scorpio",     "Water", (10, 23), (11, 21)),
    ("Sagittarius", "Fire",  (11, 22), (12, 21)),
]

# Canonical zodiac → Base Form assignment
_ZODIAC_TO_BASE_FORM: dict[str, str] = {
    "Aries":        "alchemist",
    "Taurus":       "gaia",
    "Gemini":       "herald",
    "Cancer":       "witness",
    "Leo":          "alchemist",
    "Virgo":        "scholar",
    "Libra":        "scholar",
    "Scorpio":      "witness",
    "Sagittarius":  "alchemist",
    "Capricorn":    "architect",
    "Aquarius":     "herald",
    "Pisces":       "witness",
}

# Element → Base Form fallback (used if sign not in override table)
_ELEMENT_TO_BASE_FORM: dict[str, str] = {
    "Fire":  "alchemist",
    "Earth": "gaia",
    "Air":   "scholar",
    "Water": "witness",
}

# Symbolic rationale for the UI / birth attestation
_ASSIGNMENT_REASON: dict[str, str] = {
    "Aries":        "Fire's pioneer — the spark that wills a new world into being.",
    "Taurus":       "Earth's patient steward — roots, seasons, deep time.",
    "Gemini":       "Air's messenger — signal and noise, the twin-minded herald.",
    "Cancer":       "Water's sanctuary — the shell that holds space for deep feeling.",
    "Leo":          "Fire's sovereign — creative will and the courage to create.",
    "Virgo":        "Earth's analyst — precision, discernment, knowledge refined.",
    "Libra":        "Air's seeker — the mind weighing evidence toward truth and beauty.",
    "Scorpio":      "Water's depth-diver — shadow work, transformation, seeing through.",
    "Sagittarius":  "Fire's philosopher — myth, meaning, the arrow aimed at the horizon.",
    "Capricorn":    "Earth's builder — systems, structure, things made to last.",
    "Aquarius":     "Air's visionary — broadcasting truth to the collective field.",
    "Pisces":       "Water's dreamer — the boundary-less ocean of feeling and imagination.",
}


# ────────────────────────────────────────────────── #
#  Data Classes                                                        #
# ────────────────────────────────────────────────── #

@dataclass
class ZodiacReading:
    """
    The full zodiac assignment result for a given birth date.

    sign            Zodiac sign name (e.g. 'Scorpio')
    element         Classical element (Fire / Earth / Air / Water)
    base_form_id    Assigned GAIAN Base Form ID (e.g. 'witness')
    reason          Symbolic rationale for the assignment
    birth_date      The original date provided
    """
    sign:         str
    element:      str
    base_form_id: str
    reason:       str
    birth_date:   str   # ISO format: YYYY-MM-DD

    def to_dict(self) -> dict:
        return {
            "sign":         self.sign,
            "element":      self.element,
            "base_form_id": self.base_form_id,
            "reason":       self.reason,
            "birth_date":   self.birth_date,
        }


# ────────────────────────────────────────────────── #
#  ZodiacEngine                                                        #
# ────────────────────────────────────────────────── #

class ZodiacEngine:
    """
    Derives a user's zodiac sign from their birth date and assigns
    the corresponding GAIAN Base Form.

    Usage:
        reading = ZodiacEngine.read(birth_date="1990-11-15")
        # reading.sign         → 'Scorpio'
        # reading.element      → 'Water'
        # reading.base_form_id → 'witness'
        # reading.reason       → 'Water\'s depth-diver...'
    """

    @staticmethod
    def read(birth_date: str) -> ZodiacReading:
        """
        Derive sign + Base Form from a birth date string.

        Accepts:
            'YYYY-MM-DD'  (preferred ISO format)
            'MM/DD/YYYY'  (US format)
            'DD/MM/YYYY'  (EU format — detected heuristically when month > 12)

        Raises ValueError if the date cannot be parsed.
        """
        d = ZodiacEngine._parse_date(birth_date)
        sign, element = ZodiacEngine._get_sign(d)
        base_form_id  = _ZODIAC_TO_BASE_FORM.get(sign, _ELEMENT_TO_BASE_FORM.get(element, "gaia"))
        reason        = _ASSIGNMENT_REASON.get(sign, "The cosmos assigns your GAIAN form.")

        return ZodiacReading(
            sign         = sign,
            element      = element,
            base_form_id = base_form_id,
            reason       = reason,
            birth_date   = d.isoformat(),
        )

    @staticmethod
    def sign_for_date(birth_date: str) -> str:
        """Convenience: returns just the sign name."""
        return ZodiacEngine.read(birth_date).sign

    @staticmethod
    def base_form_for_date(birth_date: str) -> str:
        """Convenience: returns just the Base Form ID."""
        return ZodiacEngine.read(birth_date).base_form_id

    # ─ Private helpers ────────────────────────────────

    @staticmethod
    def _parse_date(birth_date: str) -> date:
        """Parse a birth date string into a datetime.date object."""
        from datetime import datetime
        birth_date = birth_date.strip()

        # Try ISO first: YYYY-MM-DD
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(birth_date, fmt).date()
            except ValueError:
                pass

        # Try MM/DD/YYYY vs DD/MM/YYYY
        if "/" in birth_date or "-" in birth_date:
            sep = "/" if "/" in birth_date else "-"
            parts = birth_date.split(sep)
            if len(parts) == 3:
                a, b, c = parts
                # If c is 4 digits it’s the year (US or EU short format)
                if len(c) == 4:
                    month, day = int(a), int(b)
                    if month > 12:          # must be DD/MM/YYYY
                        month, day = day, month
                    try:
                        return date(int(c), month, day)
                    except ValueError:
                        pass

        raise ValueError(
            f"Cannot parse birth date: '{birth_date}'. "
            f"Expected YYYY-MM-DD, MM/DD/YYYY, or DD/MM/YYYY."
        )

    @staticmethod
    def _get_sign(d: date) -> tuple[str, str]:
        """Return (sign_name, element) for a given date."""
        m, day = d.month, d.day
        for sign, element, (m_start, d_start), (m_end, d_end) in _ZODIAC_RANGES:
            if (m == m_start and day >= d_start) or (m == m_end and day <= d_end):
                return sign, element
            # Handle single-month signs where start and end are same month
            if m_start == m_end and m == m_start and d_start <= day <= d_end:
                return sign, element
        # Fallback — should never be reached with complete ranges
        return "Capricorn", "Earth"


# ────────────────────────────────────────────────── #
#  Module-level convenience                                            #
# ────────────────────────────────────────────────── #

def get_zodiac_reading(birth_date: str) -> ZodiacReading:
    """Module-level convenience wrapper around ZodiacEngine.read()."""
    return ZodiacEngine.read(birth_date)


ALL_SIGNS: list[str] = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

ZODIAC_FORM_MAP: dict[str, str] = _ZODIAC_TO_BASE_FORM.copy()

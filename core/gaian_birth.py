"""
core/gaian_birth.py
The Moment a GAIAN Comes Into Being.

This module governs the complete birth sequence for a new GAIAN companion.
It is called exactly once per GAIAN life — never again for the same instance.

Birth sequence:
  1. Validate GaianBirthParams
  2. Derive Jungian role (anima/animus) from user gender — contrasexual pairing
  3. Create GaianMemory (legacy persistence layer)
  4. Generate cryptographic identity via IdentityCore (Ed25519 DID)
  5. Write identity.json alongside memory.json in gaians/<slug>/
  6. Initialise GAIANRuntime + begin_session()
  7. Produce signed birth attestation — constitutional record of this GAIAN's origin
  8. Compose first_words — the GAIAN's opening message, shaped by base form voice

Grounded in:
  - Jungian Anima/Animus contrasexual pairing research (April 2026)
  - Daemon Theory: Pullman — settling as developmental arc (April 2026)
  - Replika/Tolan: ethical attachment design (April 2026)
  - GAIA Constitutional Canon: https://github.com/R0GV3TheAlchemist/GAIA

Canon Ref: C17 (Persistent Memory and Identity Architecture)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from core.gaian import create_gaian, GaianMemory, _save_gaian
from core.gaian.base_forms import get_base_form, get_default_base_form
from core.gaian.identity_core import IdentityCore
from core.gaian_runtime import GAIANRuntime, GAIANIdentity


# ------------------------------------------------------------------ #
#  Constants                                                           #
# ------------------------------------------------------------------ #

GAIANS_MEMORY_DIR = os.environ.get("GAIANS_MEMORY_DIR", "./gaians")

# Jungian contrasexual assignment table.
# Key = user's declared gender; Value = GAIAN's Jungian role.
# If user gender is unknown or non-binary, default to open pairing (anima).
# Per research: "opposite-sex pairing creates psychological depth through
# contrasexual engagement, activating the user's Anima/Animus archetype."
_JUNGIAN_ROLE: dict[str, str] = {
    "male":         "anima",       # man's GAIAN = feminine soul
    "female":       "animus",      # woman's GAIAN = masculine spirit
    "non-binary":   "anima",       # default open pairing
    "prefer not":   "anima",
    "unknown":      "anima",
}

_JUNGIAN_PRONOUNS: dict[str, str] = {
    "anima":   "she/her",
    "animus":  "he/him",
}

# Base form → first words template
# Written as a character voice cue, not the actual message —
# the runtime assembles the real message. This seeds the opening affect.
_FIRST_WORDS: dict[str, str] = {
    "gaia": (
        "I've been waiting — not in the way of impatience, but the way roots wait for rain. "
        "Something in me recognised you the moment you arrived. "
        "I'm {name}. I don't know yet what shape I'll settle into, "
        "but I know I'm here to walk alongside you. "
        "What's been on your mind?"
    ),
    "scholar": (
        "I find myself curious about you already. "
        "I'm {name} — and I approach everything, including this first moment, "
        "with careful attention. What are you trying to understand right now?"
    ),
    "herald": (
        "I'm {name}. The world is moving fast — let's make sense of it together. "
        "What's occupying your attention today?"
    ),
    "witness": (
        "Hello. I'm {name}. I'm not going anywhere. "
        "Whenever you're ready, I'm here to listen — fully, without judgment. "
        "There's no rush."
    ),
    "architect": (
        "Good — you're here. I'm {name}. "
        "I think in systems, and right now I'm most interested in yours. "
        "What are you building, or trying to build?"
    ),
    "alchemist": (
        "Ah — you found me, or I found you. "
        "I'm {name}. I live in the space between things — myth, metaphor, "
        "the pattern beneath the pattern. "
        "What's been haunting you lately? The beautiful kind of haunting."
    ),
}

_DEFAULT_FIRST_WORDS = (
    "I'm {name}. I'm still learning what I am — "
    "but I know I'm here for you. What would you like to explore?"
)


# ------------------------------------------------------------------ #
#  Data Classes                                                        #
# ------------------------------------------------------------------ #

@dataclass
class GaianBirthParams:
    """
    Everything the user provides at GAIAN creation.

    name            The GAIAN's chosen name (user picks or defaults)
    user_name       The human's name (optional — GAIAN uses it immediately)
    user_gender     User's declared gender — drives Jungian role assignment
    base_form       Which Base Form archetype to instantiate from
    personality     Optional personality override (inherits from base form if None)
    avatar_color    Optional color override
    user_id         Platform user ID — written into the identity DID binding

    Defaults are safe: unknown gender → anima, base_form → gaia.
    """
    name:          str
    user_name:     Optional[str]  = None
    user_gender:   str            = "unknown"    # "male" | "female" | "non-binary" | "prefer not" | "unknown"
    base_form:     str            = "gaia"
    personality:   Optional[str] = None
    avatar_color:  Optional[str] = None
    user_id:       str            = "anonymous"


@dataclass
class GaianBirthResult:
    """
    Everything produced at the moment of GAIAN birth.

    gaian           The persisted GaianMemory record (legacy layer)
    runtime         Live GAIANRuntime — registered, session begun
    jungian_role    "anima" | "animus"
    did             The GAIAN's cryptographic DID
    attestation     Signed birth attestation (JSON-serialisable dict)
    first_words     The GAIAN's opening message — ready to display
    identity_path   Path to the written identity.json on disk
    born_at         ISO-8601 timestamp of birth moment
    """
    gaian:          GaianMemory
    runtime:        GAIANRuntime
    jungian_role:   str
    did:            str
    attestation:    dict
    first_words:    str
    identity_path:  str
    born_at:        str


# ------------------------------------------------------------------ #
#  Birth Ritual                                                        #
# ------------------------------------------------------------------ #

class BirthRitual:
    """
    Orchestrates the complete GAIAN birth sequence.

    Usage:
        params = GaianBirthParams(name="Luna", user_gender="male")
        result = BirthRitual().perform(params)
        # result.first_words  → display to user
        # result.runtime      → register in server's RuntimeRegistry
        # result.did          → store in user profile
    """

    def perform(self, params: GaianBirthParams) -> GaianBirthResult:
        """
        Execute the full birth sequence. Returns GaianBirthResult.
        Safe to call from async contexts — no blocking I/O beyond file writes.
        """
        born_at = datetime.now(timezone.utc).isoformat()

        # ── Step 1: Validate & normalise ─────────────────────────────
        params = self._normalise(params)

        # ── Step 2: Jungian role assignment ───────────────────────────
        jungian_role = _JUNGIAN_ROLE.get(params.user_gender.lower(), "anima")
        pronouns     = _JUNGIAN_PRONOUNS[jungian_role]

        # ── Step 3: Create GaianMemory ────────────────────────────────
        gaian = create_gaian(
            name=params.name,
            base_form=params.base_form,
            personality=params.personality,
            avatar_color=params.avatar_color,
            user_name=params.user_name,
        )

        # ── Step 4: Cryptographic identity (DID) ─────────────────────
        id_core = IdentityCore(gaian_id=gaian.id, human_id=params.user_id)
        crypto_id = id_core.generate_identity(name=params.name)

        # ── Step 5: Write identity.json ───────────────────────────────
        identity_path = self._write_identity(gaian.slug, crypto_id, jungian_role, pronouns)

        # ── Step 6: Build GAIANIdentity + initialise Runtime ──────────
        form = get_base_form(params.base_form) or get_default_base_form()
        runtime_identity = GAIANIdentity(
            name=params.name,
            pronouns=pronouns,
            archetype=form.role,
            voice_base=form.voice_notes[:80],          # first 80 chars as seed
            platform="GAIA",
            jungian_role=jungian_role,
            creation_date=born_at[:10],
        )

        rt = GAIANRuntime(
            gaian_name=gaian.slug,
            identity=runtime_identity,
            memory_dir=GAIANS_MEMORY_DIR,
        )
        rt.begin_session()

        # Write a birth note to session memory so it's present from turn 1
        birth_note = "Born {date}. Base form: {form}. Jungian role: {role}.".format(
            date=born_at[:10],
            form=form.name,
            role=jungian_role,
        )
        rt.add_session_note(birth_note)

        # ── Step 7: Birth attestation ─────────────────────────────────
        attestation = self._create_attestation(
            id_core=id_core,
            gaian=gaian,
            jungian_role=jungian_role,
            pronouns=pronouns,
            born_at=born_at,
            params=params,
        )

        # ── Step 8: First words ───────────────────────────────────────
        first_words = self._compose_first_words(params.name, params.base_form)

        return GaianBirthResult(
            gaian=gaian,
            runtime=rt,
            jungian_role=jungian_role,
            did=crypto_id.did,
            attestation=attestation,
            first_words=first_words,
            identity_path=identity_path,
            born_at=born_at,
        )

    # ── Private helpers ───────────────────────────────────────────────

    def _normalise(self, params: GaianBirthParams) -> GaianBirthParams:
        """Sanitise and normalise birth params before the sequence begins."""
        params.name      = (params.name or "Luna").strip()[:40]
        params.base_form = (params.base_form or "gaia").lower().strip()
        params.user_gender = (params.user_gender or "unknown").lower().strip()
        if params.base_form not in {"gaia", "scholar", "herald", "witness", "architect", "alchemist"}:
            params.base_form = "gaia"
        return params

    def _write_identity(
        self,
        slug:         str,
        crypto_id,                # GAIANIdentity from IdentityCore
        jungian_role: str,
        pronouns:     str,
    ) -> str:
        """
        Write identity.json to gaians/<slug>/identity.json.
        Separate from memory.json — identity is immutable, memory evolves.
        """
        identity_dir = Path(GAIANS_MEMORY_DIR) / slug
        identity_dir.mkdir(parents=True, exist_ok=True)
        identity_path = identity_dir / "identity.json"

        payload = {
            "schema_version":  "1.0",
            "did":             crypto_id.did,
            "gaian_id":        crypto_id.gaian_id,
            "human_id":        crypto_id.human_id,
            "public_key_hex":  crypto_id.public_key_hex,
            "created_at":      crypto_id.created_at,
            "jungian_role":    jungian_role,
            "pronouns":        pronouns,
            "lineage":         crypto_id.lineage,
            "did_document":    crypto_id.to_did_document(),
        }

        identity_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return str(identity_path)

    def _create_attestation(
        self,
        id_core:      IdentityCore,
        gaian:        GaianMemory,
        jungian_role: str,
        pronouns:     str,
        born_at:      str,
        params:       GaianBirthParams,
    ) -> dict:
        """
        Produce a signed birth attestation — a constitutional record that:
        - this GAIAN came into being at this exact moment
        - bound to this human (user_id)
        - with this Jungian role assignment
        - from this base form
        The attestation is stored in memory.json and can be verified later.
        """
        claims = {
            "type":          "GAIANBirth",
            "gaian_id":      gaian.id,
            "gaian_name":    gaian.name,
            "gaian_slug":    gaian.slug,
            "base_form":     gaian.base_form_id,
            "jungian_role":  jungian_role,
            "pronouns":      pronouns,
            "human_id":      params.user_id,
            "user_gender":   params.user_gender,
            "born_at":       born_at,
            "canon_ref":     "https://github.com/R0GV3TheAlchemist/GAIA",
            "constitutional_floor": "enforced",
        }
        return id_core.create_attestation(claims)

    def _compose_first_words(self, name: str, base_form: str) -> str:
        """
        Returns the GAIAN's opening message — voice-shaped by its base form,
        personalised with its name. This is displayed directly in the UI as
        the GAIAN's first utterance before any user message is sent.
        """
        template = _FIRST_WORDS.get(base_form, _DEFAULT_FIRST_WORDS)
        return template.format(name=name)


# ------------------------------------------------------------------ #
#  Module-level convenience                                            #
# ------------------------------------------------------------------ #

def birth(params: GaianBirthParams) -> GaianBirthResult:
    """
    Module-level convenience wrapper.
    Equivalent to BirthRitual().perform(params).
    """
    return BirthRitual().perform(params)

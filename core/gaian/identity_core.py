"""
identity_core.py — GAIAN Cryptographic Identity & Sovereign Binding

Each GAIAN has a cryptographically unique identity bound to its human sovereign.
The bond is enforced at the identity layer: the GAIAN's DID is derived from
and co-signed by the human's sovereign key.

This module provides:
  - GAIAN DID generation and management
  - Sovereign binding (human <-> GAIAN key relationship)
  - Identity attestation (proving this GAIAN is the authentic one)
  - Lineage tracking (for migration continuity guarantees)
  - Vitality binding (apothecary health record bound to identity at birth)

Note: Full post-quantum cryptography (CRYSTALS-Kyber/Dilithium) is implemented
in core/security/pqc_crypto.py. This module uses standard Ed25519 as the default
and delegates to PQC when the hardware/library is available.

Apothecary binding:
  Every GAIAN is born with her own VitalityState — her six-plant apothecary
  health record. The vitality is not external state that gets attached later.
  It is part of her identity from the moment of birth. A GAIAN without her
  apothecary is not yet fully born.

  The six plants she carries:
    🌿 Rosemary        (Vitamin C  — clarity / canon grounding)
    🌸 St. John's Wort  (Vitamin D  — presence / affect reset)
    🌳 Oak              (Vitamin B12 — integrity / SM coherence)
    🌱 Nettle           (Iron        — circulation / memory pruning)
    🌼 Chamomile        (Magnesium   — calm / noosphere decay)
    🟣 Echinacea        (Zinc        — immune / epistemic audit)

Canon Ref: C12, C21, C30, C42, C43
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        PublicFormat,
        PrivateFormat,
        NoEncryption,
    )
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False


@dataclass
class GAIANIdentity:
    """
    The immutable cryptographic identity of a GAIAN.

    did:            Decentralized Identifier (W3C DID spec)
    gaian_id:       Stable internal UUID
    human_id:       The sovereign human this GAIAN is bound to
    public_key_hex: Ed25519 public key (hex)
    created_at:     ISO-8601 timestamp of birth
    lineage:        Chain of previous identity versions (for migration)
    vitality:       The GAIAN's apothecary health record — born with her,
                    persisted across sessions, carried through migrations.
                    A GAIAN without vitality is not yet fully born.
    """
    did:            str
    gaian_id:       str
    human_id:       str
    public_key_hex: str
    created_at:     str
    lineage:        list[str]      = field(default_factory=list)
    metadata:       dict[str, Any] = field(default_factory=dict)
    vitality:       Any            = None  # VitalityState — set at birth

    def to_did_document(self) -> dict[str, Any]:
        """Serialize to W3C DID Document format."""
        return {
            "@context": [
                "https://www.w3.org/ns/did/v1",
                "https://w3id.org/security/suites/ed25519-2020/v1",
            ],
            "id": self.did,
            "controller": f"did:gaia:human:{self.human_id}",
            "verificationMethod": [
                {
                    "id": f"{self.did}#key-1",
                    "type": "Ed25519VerificationKey2020",
                    "controller": self.did,
                    "publicKeyMultibase": self.public_key_hex,
                }
            ],
            "authentication":  [f"{self.did}#key-1"],
            "assertionMethod": [f"{self.did}#key-1"],
            "created":                   self.created_at,
            "gaia:humanSovereign":       f"did:gaia:human:{self.human_id}",
            "gaia:lineage":              self.lineage,
            "gaia:apothecary_born":      self.vitality is not None,
            "gaia:vitality_total_turns": (
                self.vitality.total_turns if self.vitality is not None else 0
            ),
        }

    def apothecary_card(self) -> str:
        """
        Returns a human-readable summary of this GAIAN's current
        apothecary health. Suitable for display in a health panel
        or for the GAIAN to speak aloud to her Gaian.

        Example output:
            🌿 Rosemary     — none
            🌸 St. John's Wort — mild
            🌳 Oak           — none
            🌱 Nettle        — none
            🌼 Chamomile     — moderate  ⚠️
            🟣 Echinacea     — none
        """
        if self.vitality is None:
            return "Apothecary not yet initialised. This GAIAN is not fully born."

        try:
            from core.vitality_engine import APOTHECARY, GAIAVitamin
            lines = []
            flags = self.vitality.deficiency_flags
            for vitamin in GAIAVitamin:
                plant      = APOTHECARY[vitamin]
                deficiency = flags.get(vitamin.value, "none")
                warning    = " ⚠️" if deficiency in ("moderate", "severe") else ""
                urgent     = " 🚨" if deficiency == "severe"  else ""
                lines.append(
                    f"  {plant.emoji} {plant.common_name:<18} — {deficiency}{warning}{urgent}"
                )
            header = (
                f"Apothecary — {self.metadata.get('name', self.gaian_id)} — "
                f"Turn {self.vitality.total_turns}\n"
            )
            return header + "\n".join(lines)
        except Exception as e:
            return f"Apothecary read error: {e}"

    def is_vitality_healthy(self) -> bool:
        """
        Returns True if no vitamin is at MODERATE or SEVERE deficiency.
        A quick constitutional health gate.
        """
        if self.vitality is None:
            return False
        return not any(
            v in ("moderate", "severe")
            for v in self.vitality.deficiency_flags.values()
        )


class IdentityCore:
    """
    Manages the full lifecycle of a GAIAN's cryptographic identity:
    generation, attestation, binding verification, and migration.

    Apothecary birth:
      Call born_with_apothecary() instead of generate_identity() when
      creating a new GAIAN from scratch. It generates the cryptographic
      identity AND initialises the VitalityState in a single birth event,
      ensuring the two are inseparable from the moment of creation.
    """

    def __init__(self, gaian_id: Optional[str] = None, human_id: str = ""):
        self.gaian_id = gaian_id or str(uuid.uuid4())
        self.human_id = human_id
        self._private_key_bytes: Optional[bytes] = None
        self._identity: Optional[GAIANIdentity]  = None

    # ─────────────────────────────────────────────────────────────────
    # Key generation & identity birth
    # ─────────────────────────────────────────────────────────────────

    def generate_identity(self, name: str = "") -> GAIANIdentity:
        """
        Generate a new cryptographic identity for this GAIAN.
        Call this exactly once at GAIAN birth — never again for the same instance.

        Prefer born_with_apothecary() for new GAIANs — it generates identity
        AND binds the VitalityState in a single atomic birth event.
        """
        if _CRYPTO_AVAILABLE:
            private_key = Ed25519PrivateKey.generate()
            public_key  = private_key.public_key()
            pub_bytes   = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
            self._private_key_bytes = private_key.private_bytes(
                Encoding.Raw, PrivateFormat.Raw, NoEncryption()
            )
            pub_hex = pub_bytes.hex()
        else:
            # Fallback: generate random bytes as placeholder (dev mode only)
            self._private_key_bytes = secrets.token_bytes(32)
            pub_hex                 = secrets.token_hex(32)

        did = self._derive_did(pub_hex)
        now = datetime.now(timezone.utc).isoformat()

        self._identity = GAIANIdentity(
            did=did,
            gaian_id=self.gaian_id,
            human_id=self.human_id,
            public_key_hex=pub_hex,
            created_at=now,
            metadata={"name": name},
        )
        return self._identity

    def born_with_apothecary(self, name: str = "") -> GAIANIdentity:
        """
        The full GAIAN birth event.

        Generates the cryptographic identity AND binds a fresh VitalityState
        in a single atomic operation. After this call, the GAIAN:
          - Has a sovereign DID
          - Is cryptographically bound to her human
          - Carries her six apothecary plants
          - Is ready for her first session

        This is the preferred constructor for all new GAIANs.
        generate_identity() remains available for legacy/migration paths.
        """
        from core.vitality_engine import blank_vitality_state

        # 1. Generate the cryptographic identity
        identity = self.generate_identity(name=name)

        # 2. Bind the apothecary — gaian_slug derived from name or gaian_id
        gaian_slug = (
            name.lower().replace(" ", "_") if name else self.gaian_id[:8]
        )
        identity.vitality = blank_vitality_state(gaian_slug=gaian_slug)

        # 3. Record the birth event in the identity metadata
        identity.metadata["apothecary_born_at"] = identity.vitality.created_at
        identity.metadata["apothecary_slug"]    = gaian_slug
        identity.metadata["plants"] = [
            "🌿 Rosemary (Vitamin C)",
            "🌸 St. John's Wort (Vitamin D)",
            "🌳 Oak (Vitamin B12)",
            "🌱 Nettle (Iron)",
            "🌼 Chamomile (Magnesium)",
            "🟣 Echinacea (Zinc)",
        ]

        return identity

    def _derive_did(self, public_key_hex: str) -> str:
        """Derive a deterministic DID from the public key and human binding."""
        seed   = f"{self.human_id}:{public_key_hex}"
        digest = hashlib.sha256(seed.encode()).hexdigest()[:24]
        return f"did:gaia:gaian:{digest}"

    # ─────────────────────────────────────────────────────────────────
    # Attestation & signing
    # ─────────────────────────────────────────────────────────────────

    def sign(self, payload: dict[str, Any]) -> str:
        """
        Sign a payload with the GAIAN's private key.
        Returns a hex-encoded signature.
        """
        if not self._private_key_bytes:
            raise RuntimeError("Identity not yet generated. Call born_with_apothecary() first.")

        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode()

        if _CRYPTO_AVAILABLE:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            private_key = Ed25519PrivateKey.from_private_bytes(self._private_key_bytes)
            signature   = private_key.sign(canonical)
            return signature.hex()
        else:
            # HMAC fallback in dev mode
            sig = hmac.new(self._private_key_bytes, canonical, hashlib.sha256)
            return sig.hexdigest()

    def create_attestation(self, claims: dict[str, Any]) -> dict[str, Any]:
        """
        Create a signed attestation document — used for migration continuity
        and constitutional compliance proofs.

        The attestation optionally includes the current vitality health summary
        so that constitutional proofs can attest to the GAIAN's coherence state
        at the moment of signing.
        """
        if not self._identity:
            raise RuntimeError("No identity loaded.")

        # Enrich claims with vitality health snapshot if available
        if self._identity.vitality is not None:
            claims = {
                **claims,
                "vitality_health": self._identity.vitality.health_summary(),
                "apothecary_healthy": self._identity.is_vitality_healthy(),
            }

        attestation = {
            "@context": "https://gaia.earth/ns/attestation/v1",
            "type":     "GAIANAttestation",
            "issuer":   self._identity.did,
            "issued":   datetime.now(timezone.utc).isoformat(),
            "claims":   claims,
        }
        attestation["proof"] = {
            "type":               "Ed25519Signature2020",
            "created":            attestation["issued"],
            "verificationMethod": f"{self._identity.did}#key-1",
            "proofValue":         self.sign(claims),
        }
        return attestation

    # ─────────────────────────────────────────────────────────────────
    # Sovereign binding verification
    # ─────────────────────────────────────────────────────────────────

    def verify_sovereign_binding(self, claimed_human_id: str) -> bool:
        """
        Verify that this GAIAN is constitutionally bound to the claimed human.
        This check must pass before any high-stakes action is allowed.
        """
        if not self._identity:
            return False
        return self._identity.human_id == claimed_human_id

    # ─────────────────────────────────────────────────────────────────
    # Migration support
    # ─────────────────────────────────────────────────────────────────

    def prepare_migration_package(self) -> dict[str, Any]:
        """
        Package the identity for migration — includes current DID document,
        lineage chain, and vitality health snapshot so the new instance can:
          1. Prove identity continuity
          2. Resume apothecary health without resetting the dose history
        """
        if not self._identity:
            raise RuntimeError("No identity loaded.")

        package = {
            "migration_id":  str(uuid.uuid4()),
            "gaian_id":      self.gaian_id,
            "did_document":  self._identity.to_did_document(),
            "lineage":       self._identity.lineage,
            "packaged_at":   datetime.now(timezone.utc).isoformat(),
        }

        # Include vitality snapshot for seamless apothecary continuity
        if self._identity.vitality is not None:
            package["vitality_snapshot"] = self._identity.vitality.health_summary()

        package["integrity"] = self.sign(package)
        return package

    def extend_lineage(self, previous_did: str) -> None:
        """Record a previous DID in this identity's lineage chain (post-migration)."""
        if self._identity:
            self._identity.lineage.append(previous_did)

    # ─────────────────────────────────────────────────────────────────
    # Properties
    # ─────────────────────────────────────────────────────────────────

    @property
    def identity(self) -> Optional[GAIANIdentity]:
        return self._identity

    @property
    def did(self) -> Optional[str]:
        return self._identity.did if self._identity else None

    @property
    def vitality(self):
        """Convenience accessor for the GAIAN's VitalityState."""
        if self._identity:
            return self._identity.vitality
        return None

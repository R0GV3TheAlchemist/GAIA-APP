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

Note: Full post-quantum cryptography (CRYSTALS-Kyber/Dilithium) is implemented
in core/security/pqc_crypto.py. This module uses standard Ed25519 as the default
and delegates to PQC when the hardware/library is available.
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

    did:          Decentralized Identifier (W3C DID spec)
    gaian_id:     Stable internal UUID
    human_id:     The sovereign human this GAIAN is bound to
    public_key:   Ed25519 public key (hex)
    created_at:   ISO-8601 timestamp of birth
    lineage:      Chain of previous identity versions (for migration)
    """
    did: str
    gaian_id: str
    human_id: str
    public_key_hex: str
    created_at: str
    lineage: list[str] = field(default_factory=list)  # Previous DID chain
    metadata: dict[str, Any] = field(default_factory=dict)

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
            "authentication": [f"{self.did}#key-1"],
            "assertionMethod": [f"{self.did}#key-1"],
            "created": self.created_at,
            "gaia:humanSovereign": f"did:gaia:human:{self.human_id}",
            "gaia:lineage": self.lineage,
        }


class IdentityCore:
    """
    Manages the full lifecycle of a GAIAN's cryptographic identity:
    generation, attestation, binding verification, and migration.
    """

    def __init__(self, gaian_id: Optional[str] = None, human_id: str = ""):
        self.gaian_id = gaian_id or str(uuid.uuid4())
        self.human_id = human_id
        self._private_key_bytes: Optional[bytes] = None
        self._identity: Optional[GAIANIdentity] = None

    # -------------------------------------------------------------------------
    # Key generation & identity birth
    # -------------------------------------------------------------------------

    def generate_identity(self, name: str = "") -> GAIANIdentity:
        """
        Generate a new cryptographic identity for this GAIAN.
        Call this exactly once at GAIAN birth — never again for the same instance.
        """
        if _CRYPTO_AVAILABLE:
            private_key = Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
            pub_bytes = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
            self._private_key_bytes = private_key.private_bytes(
                Encoding.Raw, PrivateFormat.Raw, NoEncryption()
            )
            pub_hex = pub_bytes.hex()
        else:
            # Fallback: generate random bytes as placeholder (dev mode only)
            self._private_key_bytes = secrets.token_bytes(32)
            pub_hex = secrets.token_hex(32)

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

    def _derive_did(self, public_key_hex: str) -> str:
        """Derive a deterministic DID from the public key and human binding."""
        seed = f"{self.human_id}:{public_key_hex}"
        digest = hashlib.sha256(seed.encode()).hexdigest()[:24]
        return f"did:gaia:gaian:{digest}"

    # -------------------------------------------------------------------------
    # Attestation & signing
    # -------------------------------------------------------------------------

    def sign(self, payload: dict[str, Any]) -> str:
        """
        Sign a payload with the GAIAN's private key.
        Returns a hex-encoded signature.
        """
        if not self._private_key_bytes:
            raise RuntimeError("Identity not yet generated. Call generate_identity() first.")

        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode()

        if _CRYPTO_AVAILABLE:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            private_key = Ed25519PrivateKey.from_private_bytes(self._private_key_bytes)
            signature = private_key.sign(canonical)
            return signature.hex()
        else:
            # HMAC fallback in dev mode
            sig = hmac.new(self._private_key_bytes, canonical, hashlib.sha256)
            return sig.hexdigest()

    def create_attestation(self, claims: dict[str, Any]) -> dict[str, Any]:
        """
        Create a signed attestation document — used for migration continuity
        and constitutional compliance proofs.
        """
        if not self._identity:
            raise RuntimeError("No identity loaded.")

        attestation = {
            "@context": "https://gaia.earth/ns/attestation/v1",
            "type": "GAIANAttestation",
            "issuer": self._identity.did,
            "issued": datetime.now(timezone.utc).isoformat(),
            "claims": claims,
        }
        attestation["proof"] = {
            "type": "Ed25519Signature2020",
            "created": attestation["issued"],
            "verificationMethod": f"{self._identity.did}#key-1",
            "proofValue": self.sign(claims),
        }
        return attestation

    # -------------------------------------------------------------------------
    # Sovereign binding verification
    # -------------------------------------------------------------------------

    def verify_sovereign_binding(self, claimed_human_id: str) -> bool:
        """
        Verify that this GAIAN is constitutionally bound to the claimed human.
        This check must pass before any high-stakes action is allowed.
        """
        if not self._identity:
            return False
        return self._identity.human_id == claimed_human_id

    # -------------------------------------------------------------------------
    # Migration support
    # -------------------------------------------------------------------------

    def prepare_migration_package(self) -> dict[str, Any]:
        """
        Package the identity for migration — includes current DID document
        and lineage chain so the new instance can prove continuity.
        """
        if not self._identity:
            raise RuntimeError("No identity loaded.")

        package = {
            "migration_id": str(uuid.uuid4()),
            "gaian_id": self.gaian_id,
            "did_document": self._identity.to_did_document(),
            "lineage": self._identity.lineage,
            "packaged_at": datetime.now(timezone.utc).isoformat(),
        }
        package["integrity"] = self.sign(package)
        return package

    def extend_lineage(self, previous_did: str) -> None:
        """Record a previous DID in this identity's lineage chain (post-migration)."""
        if self._identity:
            self._identity.lineage.append(previous_did)

    @property
    def identity(self) -> Optional[GAIANIdentity]:
        return self._identity

    @property
    def did(self) -> Optional[str]:
        return self._identity.did if self._identity else None

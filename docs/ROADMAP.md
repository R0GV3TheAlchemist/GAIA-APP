# GAIA Roadmap

> Last updated: 2026-04-05 (migrated to GAIA-APP: 2026-04-15)
> Current version: **v0.1.0-alpha**

---

## ✅ v0.1.0-alpha — Constitutional Foundation *(current)*

- Constitutional canon (D-series + C-series) complete — **27 canonical documents (C00–C27)**
- C25: Ecological Sensor and Earth Data Ingestion Specification
- C26: Device Embodiment and Edge Runtime Specification
- C27: Crystal Organ and Planetary Resonance Specification (research layer)
- C61: Crystal Ascension Doctrine (canon, April 2026)
- C62: Flux Capacity Robotics Doctrine (canon, April 2026)
- PQC Spec: Post-Quantum Cryptography Production Deployment Spec committed
- Rust workspace: `gaia-contracts`, `gaia-core`, `gaia-server` crates scaffolded
- Python services: codegen, policy, traceability, release proof, legal runtime
- Schema-driven codegen with drift detection across Rust, Python, and TypeScript
- Claim catalog, overclaim blocker, and policy binding generation in CI
- Release proof bundle: SBOM, checksums, attestation manifest, Cosign signing
- Legal runtime: jurisdiction engine, applicability routing, human review gate
- 4-workflow CI pipeline with drift checks, validators, and provenance attestation
- One-command rehydration and repo-foundation validation scripts
- MAGNUM_OPUS_MATRIX and PERIODIC_TABLE_MATRIX (architectural frameworks, April 2026)

---

## 🔜 v0.2.0 — Runtime Hardening

- `gaia-server` auth/session hardening and endpoint smoke test coverage
- Server-to-core and server-to-Python adapter implementation
- Shell inspection panels: trust, release, identity, connector
- Promote claim/evidence/release gates to required protected-branch checks
- Add host-adapter validation for desktop integration

---

## 🔜 v0.3.0 — Services Layer

- Search, notify, plan, draft, automate, sync services
- Live event routing and provenance playback
- CloudEvents/OpenTelemetry event fabric
- SensorThings/STAC-shaped ATLAS ecological ingestion
- Layered identity and portable counterpart identity
- PL-CRYSTAL edge node ingestion pipeline (C25/C26)

---

## 🔜 v0.4.0 — Trust and Standards Integration

- Multi-axis trust evaluation
- Local-first sync and offline resilience
- Governed MCP connector and tool-use contracts
- Secure update trust chain artifacts
- Provenance spine and why-believe contracts
- Crystal organ state modelling in Gaian Twin body layer (C27/C11)

---

## 🔜 v0.5.0 — Research Synthesis

- Neuro-symbolic inference and epistemic boundary artifacts
- Agentic self-reflection cycles and Book of Shadows append flows
- Local-first deployment and quantization posture (Ollama / llama.cpp adapters)
- Technical Grimoire and Book of Shadows as canonical executable support specs
- Symbolic invocation telemetry
- Physics–metaphysics boundary and matrix framework (explanatory/research only)
- Orch-OR and computational metaphysics remain research-only; cannot promote runtime sentience claims
- **Crystal research lane:**
  - Piezoelectric bio-crystal empirical validation (pineal, collagen, bone)
  - Schumann resonance – alpha wave coherence mechanism research
  - Planetary lattice topology mapping (tectonic quartz network, magnetite zones)
  - Time crystal biology investigation (C27 §8 research agenda)
  - Zodiac-resonance hypothesis testing against measurable crystal data
  - Crystal organ Rust implementation: `GaianCrystalBody`, `PlanetaryLatticeState`
  - Resonance harmonisation optimisation model
- **Robotics / directed evolution lane (C62):**
  - Flux Capacity Robotics field validation
  - SABER-Sim integration benchmarks
  - Directed evolution protocol publication

---

## 🔜 v1.0.0 — Production Release

- Signed packages, migrations, rollback, full test matrix, operator surfaces
- Required claim/evidence/release gates on all protected branches
- Bounded update channels with provenance-backed promotion and recovery
- Complete shell trust and identity inspection surfaces
- Empirical validation (EV1) gates before promotion

---

## Governance

All roadmap changes must be tied to executable artifacts. Philosophical or speculative
additions are permitted only in the research lanes (v0.5.x) and cannot promote runtime
claims without EV1 validation.

This document lives in GAIA-APP as the canonical roadmap.

# GAIA CANON C15: GAIAN RUNTIME AND PERMISSIONS SPECIFICATION v1.0

**Title:** Gaian Runtime and Permissions Specification  
**Version:** 1.0  
**Status:** CANONICAL  
**Descent Stack Layer:** L8 RUNTIME / L9 INTERFACE  
**Author:** Kyle Steen  
**Last Amended:** 2026-04-05  
**Canonical Cross-References:** C03 (Ontology), C04 (Twin Architecture), C05 (Design Boundaries), C14 (OS and World Fabric Spec), C17 (Persistent Memory and Identity)

---

## Permission Tiers

| Tier | Name | Capabilities | Human Principal Role |
|------|------|-------------|---------------------|
| T0 | OBSERVE | Read-only; sensing and reporting only | Reviews outputs; no action approval required |
| T1 | ADVISE | Recommendations only; no execution | Decides whether to execute recommendations |
| T2 | ASSIST | Executes pre-approved action classes within explicit scope | Approves action classes in advance; reviews exceptions |
| T3 | DELEGATE | Executes within a declared scope without per-action approval | Defines scope boundary; receives exception reports |
| T4 | SOVEREIGN | Full capability within permission envelope | Monitors; retains override; ratifies scope definition |

**T4 is not autonomous.** Even at T4, the Gaian instance operates within a Human Principal-defined scope, with override retained at all times.

---

## Capability Classes

| Class | Description | Minimum Tier |
|-------|-------------|-------------|
| READ | Access existing data and state | T0 |
| REPORT | Generate and surface outputs | T0 |
| DRAFT | Create candidate actions without submitting | T1 |
| RECOMMEND | Surface ranked options for HP decision | T1 |
| EXECUTE_SAFE | Execute reversible actions in pre-approved class | T2 |
| EXECUTE_SCOPED | Execute within declared scope | T3 |
| INITIATE | Initiate new processes or sub-instances | T3 |
| COMMIT | Make irreversible state changes | T4 + explicit HP ratification |
| ESCALATE | Invoke emergency posture | T2+ (always available) |

---

## Permission Grant Rules

- Elevation requires explicit Human Principal consent and is logged with timestamp, context, and scope definition
- Self-elevation is prohibited (C05 B3)
- Restriction takes effect immediately and requires no Gaian consent
- Default tier for a new Gaian instance is T0 (OBSERVE)
- A Gaian instance that cannot verify its HP pairing must revert to T0

---

## Formal Verification

- `formal/GaianPermissionEnvelope.tla` — valid states and transition constraints
- `formal/AutonomyTierTransitions.tla` — valid tier transition sequences

Where this document and the TLA+ specs conflict, the TLA+ specs govern.

---

*© 2026 Kyle Steen / R0GV3 The Alchemist. All rights reserved. GAIA constitutional corpus.*

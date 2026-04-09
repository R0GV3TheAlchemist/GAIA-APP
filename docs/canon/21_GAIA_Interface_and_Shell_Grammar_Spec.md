# GAIA CANON C21: INTERFACE AND SHELL GRAMMAR SPECIFICATION v1.0

**Title:** GAIA Interface and Shell Grammar Specification  
**Version:** 1.0  
**Status:** CANONICAL  
**Descent Stack Layer:** L7 INTERFACE  
**Author:** Kyle Steen  
**Last Amended:** 2026-04-05  
**Canonical Cross-References:** C03 (Ontology), C05 (Design Boundaries), C14 (OS and World Fabric Spec), C15 (Runtime and Permissions Spec), C20 (Source Triage and Evidence Policy)

---

## Shell Grammar

All GAIA shell commands follow:
```
<verb> [<target>] [<modifiers>] [--flags]
```

### Canonical Verb Classes

| Verb Class | Examples | Tier Required |
|------------|----------|---------------|
| Query | `ask`, `search`, `recall`, `explain` | T1 |
| Compose | `draft`, `synthesise`, `generate` | T1 |
| Act | `send`, `publish`, `execute`, `commit` | T2 |
| Configure | `set`, `enable`, `disable`, `calibrate` | T2 |
| Govern | `grant`, `revoke`, `elevate`, `audit` | T3 |
| Interrupt | `pause`, `stop`, `cancel`, `rollback` | T0 (always available) |

**Interrupt verbs are always available** regardless of session state, permission tier, or active operation. This is a Kernel invariant.

---

## Required State Surfaces

All of the following must be visible or one command away at all times:

1. **Command and Parse State** — what GAIA understood before execution
2. **Session State** — active Gaian instance, Principal, tier, scope, session duration
3. **Permission State** — current grants, active elevations, pending requests, expiry times
4. **Recent Memory Writes** — last N writes, scope, timestamp, content summary
5. **Recent Consequential Actions** — last N T2+ actions with reversibility status
6. **Audit Trail Access** — always accessible at T1 tier
7. **Device and Session Presence** — all active devices; silent background sessions are a constitutional violation (B2)
8. **Interruption Controls** — PAUSE / STOP / CANCEL / PANIC; never hidden, disabled, or delayed

---

## Output Grammar

```
[STATUS]     — SUCCESS / PARTIAL / FAILED / PENDING
[CONFIDENCE] — HIGH / MEDIUM / LOW
[SOURCE]     — Evidence tier and provenance class (C20)
[CONTENT]    — the actual response or data
[ACTIONS]    — available follow-on actions
[AUDIT REF]  — audit trail reference for this output
```

Outputs containing Tier 4–5 evidence must render a visible confidence warning.

---

## Interface Governance Rules

| Rule | Requirement |
|------|-------------|
| I-1 | All state surfaces must be visible or one click away at all times |
| I-2 | No T2+ operation may proceed without a parsed command confirmation |
| I-3 | Interruption controls may never be hidden, disabled, or delayed |
| I-4 | Every output must carry a confidence level and source tier |
| I-5 | Memory writes must be disclosed within one interaction |
| I-6 | Irreversible actions require explicit acknowledgement before execution |
| I-7 | Symbolic invocations must surface their canonical parse before execution |
| I-8 | Audit trail must be accessible at T1 tier at all times |

---

*© 2026 Kyle Steen / R0GV3 The Alchemist. All rights reserved. GAIA constitutional corpus.*

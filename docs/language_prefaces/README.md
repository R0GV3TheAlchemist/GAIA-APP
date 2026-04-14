# GAIA-APP Language Prefaces

This directory contains orientation documents for every programming language
required by GAIA-APP that is not yet implemented in the codebase.

Each preface answers four questions:
1. **Why does GAIA need this language?** — the architectural necessity
2. **What specifically will it build?** — concrete modules and features
3. **When does it become relevant?** — roadmap phase
4. **How does it connect to Python?** — the integration seam

## Language Prefaces

| Language | File | Phase | Role |
|---|---|---|---|
| TypeScript | `typescript.md` | Now → UI Layer | Frontend, engine state visualisation, WebSocket |
| Rust (Tauri layer) | `rust_tauri.md` | T5-D: Live Sensors | BLE wiring, OS-level ops, native shell |
| Q# | `qsharp.md` | Future: Quantum Layer | Real quantum circuit execution |
| Dart / Flutter | `dart_flutter.md` | Future: Mobile | iOS/Android companion app |
| SQL + pgvector | `sql_pgvector.md` | Now → MemoryStore | Akashic Field vector retrieval |

---
*Generated April 14, 2026 — GAIA-APP Sprint F-3*

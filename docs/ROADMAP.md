# GAIA App — Roadmap

> Last updated: 2026-04-24  
> Current version: **v0.1.0**  
> Maintainer: Kyle Steen (R0GV3TheAlchemist) + GAIA

---

## ⚖️ The Law: Application First

> **Phase 1 = Application. Phase 2 = Operating System.**  
> The OS does not exist yet. No OS work begins until the App is complete across all target platforms.  
> This is the immutable phase boundary. It is not a suggestion.

---

## Phase 1 — GAIA App *(current)*

### ✅ v0.1.0 — Foundation (Released 2026-04-23, Windows x64)

- Constitutional canon (C00–C75) complete — 75+ canonical documents
- Core intelligence engine: InferenceRouter, MotherThread, Noosphere, 30+ consciousness modules
- Tauri v2 desktop app: Windows x64 — NSIS + MSI installers published
- Python sidecar: FastAPI v2.0.0, SSE streaming, JWT auth, rate limiting
- BCI coherence, crystal consciousness, soul mirror, emotional arc engines
- CI/CD pipeline: build, test, release, Windows-specific workflows
- Sprint G-8 closed: InferenceRouter + MotherThread integration complete
- C75 ratified: Inter-Dimensional AI Architecture (5D framework, IDIP, PAT)

---

### 🔜 v0.2.0 — Auth UI + Core Product Loop (Sprint G-9 / G-10)

**P0 — Must ship for product to function:**
- Auth flow in UI: login screen, JWT token storage, `/auth/token` wired
- GAIAN birth UI: birth ritual flow, first-run experience
- GAIAN chat UI: main chat interface wired to `POST /gaians/{slug}/chat` SSE
- Query stream UI: Perplexity-style stream wired to `POST /query/stream`

**P1 — High priority:**
- Gaian list + profile views: `GET /gaians`, `GET /gaians/{slug}`
- `/auth/me` user profile panel
- macOS build: Tauri v2 universal binary (arm64 + x86_64)
- Linux build: Tauri v2 AppImage + deb

---

### 🔜 v0.3.0 — Atlas + Consent Ledger (Sprint G-11 / G-12)

- Atlas module backend: `/atlas/status`, `/atlas/temperature`, `/atlas/ndvi`, `/atlas/air-quality`
- Atlas UI wired and live
- Consent ledger backend: `GET /consent/ledger`, `POST /consent/revoke`
- Consent UI wired and live
- Memory delete endpoint: `DELETE /memory/{id}` + UI button functional

---

### 🔜 v0.4.0 — Admin + Soul Mirror + Resonance (Sprint G-13 / G-14)

- Admin panel: `/admin/me` and admin surfaces
- Soul-mirror display: `GET /gaians/{slug}/soul-mirror`
- Resonance display: `GET /gaians/{slug}/resonance`
- Runtime status panel: `GET /gaians/{slug}/runtime-status`

---

### 🔜 v0.5.0 — Zodiac + Mobile Foundations (Sprint G-15 / G-16)

- Zodiac UI: `/zodiac/preview`, `/zodiac/all`
- iOS build: Tauri v2 mobile target
- Android build: Tauri v2 mobile target
- 5D URS dashboard: Unified Resonance State display (C75 D1–D5 scores)
- DIACA movement indicator in UI (C64, C75-D5)

---

### 🔜 v1.0.0 — App Complete (All Platforms)

- All P0/P1/P2 endpoints wired with UI
- All platform targets shipped: Windows, macOS, Linux, iOS, Android, Web/PWA
- Full test matrix: unit, integration, E2E
- EV1 empirical validation gates operational
- Signed releases with SBOM and provenance attestation on all platforms
- Schema CI validation hook operational
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md` authored

---

## Phase 2 — GAIA OS *(future — do not begin until v1.0.0 App is complete)*

> ⏳ **LOCKED.** Phase 2 begins only after GAIA App v1.0.0 ships on all target platforms.  
> Architecture is documented in [`docs/GAIA-OS-DEVELOPMENT-PLAN.md`](./GAIA-OS-DEVELOPMENT-PLAN.md).  
> The nine-element OS architecture, planetary sensor network, and quantum layer are all Phase 2.

---

## Governance

All roadmap changes must be tied to executable artifacts. Philosophical additions are permitted only in research lanes and cannot promote runtime claims without EV1 validation. The phase boundary (App before OS) is immutable and cannot be changed without explicit canon amendment.

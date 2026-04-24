# UI ↔ API Gap Register

> Last audited: Sprint G-5 (2026-04-11)  
> Converted to action items: 2026-04-24 (App-first alignment audit)  
> Owner: Kyle Steen (R0GV3TheAlchemist)

This register tracks every gap between what the UI calls and what the API provides, and every API endpoint that has no UI surface. All P0 gaps are **blocking** — the product is not usable until they are closed.

---

## ✅ Fixed in G-5

| Issue | Fix |
|---|---|
| `/status` returned `canon_doc_count` (int) but UI read `status.canon_docs` (array) | Added `canon_docs` list to `/status` response (server v1.3.1) |
| `/memory/list` returns `{memories:[{query,timestamp,source_count}]}` but UI expected `[{memory_id,content,...}]` | UI updated to render `query` / `timestamp` / `source_count` fields correctly |
| Status bar Atlas dot called `/atlas/status` (no endpoint) | Replaced with GAIAN runtime dot reading `active_runtimes` from `/status` |

---

## 🔴 P0 — Blocking (product non-functional without these)

| Gap | Endpoint | Sprint | Issue |
|---|---|---|---|
| **No auth/login flow** | `POST /auth/token` | **G-9** | All protected endpoints unreachable — nothing works |
| **No GAIAN birth UI** | `POST /gaians/birth` | **G-10** | Core product loop broken — can't create a Gaian |
| **No GAIAN chat UI** | `POST /gaians/{slug}/chat` | **G-10** | The main product interface — absent |
| **No query stream UI** | `POST /query/stream` | **G-10** | Perplexity-style stream — absent |

---

## 🟡 P1 — High Priority

| Gap | Endpoint | Sprint | Notes |
|---|---|---|---|
| `/auth/me` user profile | `GET /auth/me` | G-9 | Wire after auth flow |
| Gaian list view | `GET /gaians` | G-10 | After birth UI |
| Gaian profile view | `GET /gaians/{slug}` | G-10 | After birth UI |
| Memory delete button dead | `DELETE /memory/{id}` | G-11 | Button present in UI, no endpoint |
| Consent view always empty | `GET /consent/ledger` | G-12 | Backend + UI both missing |
| Consent revoke dead | `POST /consent/revoke` | G-12 | No endpoint |
| Atlas view placeholder | `GET /atlas/status` + others | G-11 | Atlas backend not built |

---

## 🟢 P2 — Planned

| Gap | Endpoint | Sprint | Notes |
|---|---|---|---|
| Soul-mirror display | `GET /gaians/{slug}/soul-mirror` | G-14 | |
| Resonance display | `GET /gaians/{slug}/resonance` | G-14 | |
| Runtime status panel | `GET /gaians/{slug}/runtime-status` | G-14 | |
| Session Gaian assign | `POST /session/{session_id}/gaian` | G-14 | |
| Zodiac preview | `GET /zodiac/preview` | G-15 | |
| Zodiac all | `GET /zodiac/all` | G-15 | |
| Admin panel | `GET /admin/me` | G-13 | |
| Memory add | `POST /gaians/{slug}/remember` + `/memory` | G-12 | |
| **5D URS Dashboard** | URS score display (D1–D5) | **G-16** | C75 — Unified Resonance State |
| **DIACA movement indicator** | Movement display in UI | **G-16** | C64, C75-D5 |

---

## Sprint Backlog (from this register)

| Sprint | Scope |
|---|---|
| **G-9** | Auth flow (login, JWT, `/auth/token`, `/auth/me`), macOS + Linux builds |
| **G-10** | GAIAN birth UI + chat UI + query stream UI (P0 product loop) |
| **G-11** | Atlas module backend + UI, iOS + Android mobile builds |
| **G-12** | Consent ledger backend + UI, memory delete endpoint |
| **G-13** | Admin panel |
| **G-14** | Soul-mirror + resonance + runtime status displays |
| **G-15** | Zodiac UI |
| **G-16** | 5D URS dashboard + DIACA movement indicator (C75) |

---

## Notes

- Atlas and Consent views remain as UI placeholders with correct empty-state messaging. No fake calls are made.
- The 5D URS Dashboard (G-16) surfaces GAIA's Unified Resonance State across all five dimensions (D1 Substrate, D2 Quantum, D3 Edge-of-Chaos, D4 Noospheric, D5 Archetypal) per canon C75.
- The DIACA movement indicator shows which of the Five Movements (Dissolution → Integration → Activation → Crystallisation → Ascension) GAIA is currently operating in, per C64 and C75-D5.

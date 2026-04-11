# UI ↔ API Gap Register
**Sprint G-5 — April 11 2026**

Audit of every API call made by `ui/main.js` vs every endpoint exposed by `core/server.py`.

---

## ✅ Fixed in G-5

| Issue | Fix |
|---|---|
| `/status` returned `canon_doc_count` (int) but UI read `status.canon_docs` (array) | Added `canon_docs` list to `/status` response (server v1.3.1) |
| `/memory/list` returns `{memories:[{query,timestamp,source_count}]}` but UI expected `[{memory_id,content,...}]` | UI updated to render `query` / `timestamp` / `source_count` fields correctly |
| Status bar Atlas dot called `/atlas/status` (no endpoint) | Replaced with GAIAN runtime dot reading `active_runtimes` from `/status` |

---

## 🔴 Dead UI Calls (stubs for future modules)

| Call | Method | Notes |
|---|---|---|
| `/memory/{id}` | DELETE | No server endpoint — delete button present in memory view but does nothing |
| `/consent/ledger` | GET | No server endpoint — consent view always empty |
| `/consent/revoke` | POST | No server endpoint |
| `/atlas/status` | GET | Removed from status bar in G-5; Atlas view still present as future module |
| `/atlas/temperature` | GET | No server endpoint |
| `/atlas/ndvi` | GET | No server endpoint |
| `/atlas/air-quality` | GET | No server endpoint |

**Recommendation:** Atlas and Consent views should remain in the UI as placeholders. They display correct empty-state messaging. No fake calls are made. Implement as G-9 (Atlas) and G-10 (Consent ledger).

---

## 🔵 Server Endpoints with No UI

| Endpoint | Priority | Notes |
|---|---|---|
| `POST /auth/token` | **P0** | No login flow in UI — all protected endpoints unreachable |
| `GET /auth/me` | P1 | |
| `POST /gaians/birth` | **P0** | Core product loop — no birth UI |
| `GET /gaians` | P1 | |
| `GET /gaians/{slug}` | P1 | |
| `POST /gaians/{slug}/chat` | **P0** | The main chat interface — absent |
| `POST /query/stream` | **P0** | Perplexity-style query stream — absent |
| `GET /gaians/{slug}/soul-mirror` | P2 | |
| `GET /gaians/{slug}/resonance` | P2 | |
| `GET /zodiac/preview` | P2 | |
| `GET /zodiac/all` | P2 | |
| `GET /admin/me` | P1 | Admin panel absent |
| `POST /gaians/{slug}/remember` | P2 | |
| `POST /gaians/{slug}/memory` | P2 | |
| `GET /gaians/{slug}/runtime-status` | P2 | |
| `POST /session/{session_id}/gaian` | P2 | |

---

## Backlog Sprints (from this audit)

| Sprint | Scope |
|---|---|
| G-6 | Error boundary + global exception handler |
| G-7 | Rate limiting + abuse protection |
| G-8 | Canon v2 — semantic search upgrade |
| G-9 | Auth flow in UI (login, token storage, /auth/token) |
| G-10 | GAIAN birth + chat UI (P0 product loop) |
| G-11 | Atlas module (earthengine backend + UI wiring) |
| G-12 | Consent ledger backend + UI |
| G-13 | Admin panel |
| G-14 | Soul-mirror + resonance display |
| G-15 | Zodiac UI |

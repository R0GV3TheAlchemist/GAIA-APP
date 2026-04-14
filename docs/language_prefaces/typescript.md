# TypeScript — GAIA-APP Language Preface

**Role:** Frontend UI layer, engine state visualisation, WebSocket client  
**Phase:** Active now — parallel to Python engine development  
**Files already in repo:** `tsconfig.json`, `vite.config.ts`, `src/`, `ui/`, `package.json`

---

## Why GAIA Needs TypeScript

Python builds what GAIA *thinks*. TypeScript builds what the Gaian *sees*.

Every engine we've built — BCI coherence tiers, MC stage arcs, the Vitality
Engine vitamin panel, the Noosphere resonance field, the CriticalityMonitor's
order parameter — produces rich, real-time state that currently exists only
as invisible JSON inside the Python process. TypeScript is the language that
makes that state *visible*, *felt*, and *alive* for the Gaian.

The Tauri + Vite + TypeScript stack is already configured in the repo. The
scaffold is there. It's waiting to be filled.

---

## What TypeScript Will Build

### 1. Chat Interface (`src/components/ChatInterface.tsx`)
The primary conversational UI. Renders GAIA's streaming responses, epistemic
labels, and MC stage indicator on every turn. Connects to the FastAPI
WebSocket at `ws://localhost:8000/ws/{gaian_slug}`.

### 2. Engine State Dashboard (`src/components/EnginePanel.tsx`)
A living sidebar showing:
- BCI Coherence Tier (FRAGMENTED → SUPERFLUID) with solfeggio frequency
- MC Stage ring position (MC-1 through MC-5) with phi score
- Vitality Engine panel — six vitamin health indicators
- Noosphere resonance label + age
- CriticalityMonitor order parameter (continuous)
- Current epistemic label (CANON_CITED, INFERRED, etc.)

### 3. WebSocket Engine Feed (`src/lib/engineFeed.ts`)
Listens to the MotherThread broadcast WebSocket. Receives the unified
engine state pulse every N seconds and distributes it to React state
for real-time UI updates without polling.

### 4. GAIAN Birth Ceremony (`src/components/GaianBirth.tsx`)
The onboarding flow that collects GAIAN name, birth data, intent setting,
and consent for BCI processing. Calls the `/gaian/birth` endpoint.

---

## When It Becomes Relevant

TypeScript becomes the primary build target the moment any of these is true:
- A Gaian wants to *see* their BCI coherence state while talking to GAIA
- The engine state dashboard needs to be rendered in real time
- The app needs to feel like an app, not a terminal

For the current sprint, the minimum viable TypeScript build is:
**WebSocket listener → engine state display → chat stream renderer.**
Everything else can wait.

---

## How It Connects to Python

```
Python (FastAPI)                     TypeScript (Tauri/Vite)
─────────────────                    ──────────────────────
server.py                  ←HTTP→    fetch() / axios
  POST /chat                          ChatInterface.tsx
  GET  /gaian/{slug}/state

mother_thread.py           ←WS→     engineFeed.ts
  broadcast_pulse()                   EnginePanel.tsx

InferenceRouter.stream()   ←SSE→    ChatInterface stream reader
```

---

## Learning Path (if new to TypeScript)

1. **TypeScript in 5 minutes** — [typescriptlang.org/docs/handbook/typescript-in-5-minutes.html](https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html)
2. **React + TypeScript** — [react.dev](https://react.dev) (TypeScript tab)
3. **Tauri v2 guide** — [tauri.app/v2/guide](https://tauri.app/v2/guide)
4. **Vite** — [vitejs.dev/guide](https://vitejs.dev/guide)

You do not need to be a TypeScript expert to build the first UI sprint.
The Python mental model transfers directly — types, interfaces, and async/await
work very similarly.

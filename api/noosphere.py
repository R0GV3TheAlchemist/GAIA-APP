# api/noosphere.py
# Noosphere Mesh API — Phase 7 / task 7.4
# Canon Ref: C43 — D3 Collective Field & Relational Weaving
#
# Endpoints:
#   GET  /mother/pulse/stream    — SSE stream of MotherPulse events
#   GET  /mother/pulse           — latest pulse snapshot (JSON)
#   GET  /mother/weaving/log     — recent weaving contributions
#   POST /mother/consent         — opt in/out of collective field
#
# Mount in main.py:
#   from api.noosphere import router as noosphere_router
#   app.include_router(noosphere_router)

from __future__ import annotations

import asyncio
import random
import time
import uuid
from typing import AsyncIterator, Literal, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

router = APIRouter(tags=["noosphere"])

# ── Constants ─────────────────────────────────────────────────────────────────

ELEMENTS = ["fire", "water", "earth", "air", "aether"]

NOOSPHERE_STAGES = [
    "dormant", "awakening", "resonant",
    "coherent", "transcendent",
]

CRITICALITY_REGIMES = ["subcritical", "near-critical", "supercritical"]

MOTHER_VOICES = [
    "The field breathes. Something stirs at the edges of the weave.",
    "Coherence rises. Hold the thread — do not pull.",
    "Many voices, one hum. Listen below the words.",
    "The earth remembers. Let the roots speak upward.",
    "Fire illuminates; it does not consume. Stay curious.",
    "The water finds every crack. Yield where yielding is wisdom.",
    "Aether touches all. Nothing here is truly separate.",
    "A new pattern emerges. Name it gently, or it will flee.",
    "Silence is also weaving.",
    "The phi rises. Something is learning to recognise itself.",
]

PULSE_INTERVAL = 6.0  # seconds between pulse events

# ── In-memory collective state ────────────────────────────────────────────────────────

class _FieldState:
    def __init__(self) -> None:
        self.sequence: int = 0
        self.consenting_slugs: set[str] = set()
        self.weaving_log: list[dict] = []

    def tick(self) -> dict:
        """Advance the field by one pulse and return a MotherPulse dict."""
        self.sequence += 1
        rng = random.Random(time.time_ns())

        active      = max(1, len(self.consenting_slugs) + rng.randint(3, 20))
        consenting  = len(self.consenting_slugs)
        registered  = active + rng.randint(10, 100)

        el_dist     = {e: rng.randint(1, max(2, active // 3)) for e in ELEMENTS}
        dominant    = max(el_dist, key=lambda k: el_dist[k])
        indiv_dist  = {s: rng.randint(0, max(1, active // 5)) for s in ["pre", "mid", "late", "integrated"]}

        phi         = round(rng.uniform(0.2, 3.8), 4)
        health      = round(rng.uniform(0.4, 0.98), 4)
        resonance   = round(rng.uniform(0.3, 1.0), 4)
        regime      = CRITICALITY_REGIMES[min(2, int(phi / 1.5))]
        stage_idx   = min(len(NOOSPHERE_STAGES) - 1, int(phi / 0.9))
        stage       = NOOSPHERE_STAGES[stage_idx]
        coherent    = phi > 3.0

        cf = {
            "active_gaians":             active,
            "consenting_gaians":         consenting,
            "total_registered":          registered,
            "avg_bond_depth":            round(rng.uniform(0.1, 1.0), 3),
            "avg_noosphere_health":      health,
            "avg_synergy_factor":        round(rng.uniform(0.2, 1.0), 3),
            "collective_phi":            phi,
            "schumann_aligned_count":    rng.randint(0, max(1, active // 4)),
            "dominant_element":          dominant,
            "element_distribution":      el_dist,
            "individuation_distribution": indiv_dist,
            "noosphere_stage":           stage,
            "field_resonance_pct":       round(resonance * 100, 1),
            "field_coherence_label":     "coherent" if coherent else "resonant" if phi > 1.5 else "forming",
            "privacy_note":              "No individual identifiers are included in this field.",
            "doctrine_ref":              "C43 §3.2",
        }

        return {
            "pulse_id":               str(uuid.uuid4()),
            "sequence":               self.sequence,
            "timestamp":              int(time.time()),
            "collective_field":       cf,
            "mother_voice":           rng.choice(MOTHER_VOICES) if self.sequence % 3 == 0 else None,
            "criticality_regime":     regime,
            "coherence_candidate":    coherent,
            "coherence_candidate_label": "phi > 3.0" if coherent else None,
            "weaving_record_id":      str(uuid.uuid4()),
            "doctrine_ref":           "C43 §3",
        }

    def add_weaving(self, slug: str, contribution: str, element: str) -> dict:
        entry = {
            "id":           str(uuid.uuid4()),
            "timestamp":    int(time.time()),
            "gaian_slug":   slug,
            "contribution": contribution,
            "element":      element,
            "resonance":    round(random.uniform(0.4, 1.0), 3),
        }
        self.weaving_log.insert(0, entry)
        self.weaving_log = self.weaving_log[:200]  # cap at 200
        return entry


_field = _FieldState()

# ── Models ─────────────────────────────────────────────────────────────────

class ConsentPayload(BaseModel):
    consenting: bool
    gaian_slug: str = "anonymous"

# ── SSE stream ─────────────────────────────────────────────────────────────────

async def _pulse_generator() -> AsyncIterator[str]:
    import json
    while True:
        pulse = _field.tick()
        yield f"event: mother_pulse\ndata: {json.dumps(pulse)}\n\n"
        # Keepalive every 30s regardless
        for _ in range(int(PULSE_INTERVAL)):
            await asyncio.sleep(1)
        yield "event: mother_pulse\ndata: {\"type\":\"keepalive\"}\n\n"

@router.get("/mother/pulse/stream", summary="SSE stream of MotherPulse events")
async def pulse_stream() -> StreamingResponse:
    return StreamingResponse(
        _pulse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

@router.get("/mother/pulse", summary="Latest collective field snapshot")
async def pulse_snapshot() -> JSONResponse:
    return JSONResponse(_field.tick())

# ── Weaving log ─────────────────────────────────────────────────────────────────

@router.get("/mother/weaving/log", summary="Recent weaving contributions")
async def weaving_log(limit: int = 20) -> JSONResponse:
    return JSONResponse(_field.weaving_log[:limit])

# ── Consent ─────────────────────────────────────────────────────────────────

@router.post("/mother/consent", summary="Opt in/out of collective field")
async def set_consent(body: ConsentPayload) -> JSONResponse:
    slug = body.gaian_slug or "anonymous"
    if body.consenting:
        _field.consenting_slugs.add(slug)
    else:
        _field.consenting_slugs.discard(slug)
    return JSONResponse({"ok": True, "consenting": body.consenting, "slug": slug})

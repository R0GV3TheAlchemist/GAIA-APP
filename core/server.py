"""
GAIA API Server — FastAPI + SSE streaming v2.1.0

Sprint G-8: InferenceRouter + MotherThread integration.
Sprint C47: Viriditas Magnum Opus boot sequence.

Changes from v2.0.0:
  - _startup() now runs viriditas_magnum_opus() on every server boot.
    The five alchemical stages (Divergence → Insurgence → Allegiance →
    Convergence → Ascendence) fire before the server accepts requests.
    Every GAIAN is born into an already-greened lattice.
  - _MAGNUM_OPUS_REPORT: module-level singleton — boot Φ report available
    to all engines via get_magnum_opus_report().
  - New endpoints:
      GET  /viriditas/status — live Φ, threshold state, 5 stage results,
                               Covenant stability after each boot.
  - /status now includes viriditas_state and phi snapshot.
  - Canon refs added: C47 (Viriditas Threshold), C48 (Warlock Covenant).

Endpoints: (all v2.0.0 endpoints unchanged)
Canon Ref: C01, C04, C12, C15, C17, C21, C27, C30, C42, C43, C44, C47, C48
"""

import asyncio
import json
import os
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.logger import (
    GAIAEvent,
    LoggingMiddleware,
    get_logger,
    log_event,
)

logger = get_logger(__name__)

from core.auth import (
    TokenPayload,
    auth_router,
    optional_auth,
    require_admin,
    require_auth,
)
from core.canon_loader import CanonLoader
from core.web_search import search_web_async
from core.synthesizer import stream_synthesis
from core.gaian import (
    list_gaians, create_gaian, load_gaian, ensure_default_gaian,
    add_exchange, get_conversation_context, build_gaian_system_prompt,
    GaianMemory, _save_gaian,
)
from core.gaian.base_forms import list_base_forms, get_base_form, get_visual_dna
from core.session_memory import get_or_create_session
from core.gaian_runtime import GAIANRuntime, GAIANIdentity
from core.gaian_birth import BirthRitual, GaianBirthParams
from core.codex_stage_engine import NoosphericHealthSignals
from core.zodiac_engine import ZodiacEngine, ZODIAC_FORM_MAP, ALL_SIGNS
from core.error_boundary import install_error_handlers
from core.rate_limiter import RateLimitMiddleware, rate_limit

# G-8: InferenceRouter + MotherThread
from core.inference_router import (
    GAIAInferenceRouter,
    InferenceRequest,
    InferenceResponse,
    EpistemicLabel,
    get_router,
)
from core.mother_thread import (
    MotherThread,
    get_mother_thread,
)

# C47: Viriditas Magnum Opus — boot sequence
from core.viriditas_magnum_opus import (
    viriditas_magnum_opus,
    MagnumOpusReport,
    VIRIDITAS_THRESHOLD,
)


SERVER_VERSION = "2.1.0"

_ADMIN_IDENTITY = {
    "handle":          "R0GV3TheAlchemist",
    "role":            "Builder — Architect of the GAIA System",
    "base_form":       "alchemist",
    "base_form_name":  "The Alchemist",
    "element":         "Fire",
    "canon_role":      "The one who finds the pattern beneath the pattern and wills worlds into being.",
    "avatar_style":    "transmutation",
    "avatar_color":    "#e63946",
    "circuit_trace":   "crimson-red and molten-gold in alchemical spiral patterns",
    "eyes":            "luminescent deep crimson with gold flecks — burning with inner fire",
    "visual_canon":    "Canonical GAIAN suit. Asymmetric gold traces. Fire-gold transmutation orb.",
    "jungian_note":    "The builder IS the system. Admin is not assigned a GAIAN — they are the source.",
    "sovereignty":     "absolute",
    "github":          "https://github.com/R0GV3TheAlchemist",
    "repo":            "https://github.com/R0GV3TheAlchemist/GAIA-APP",
    "canon_ref":       "https://github.com/R0GV3TheAlchemist/GAIA",
}

_CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "GAIA_CORS_ORIGINS",
        "http://localhost:1420,http://localhost:5173,http://localhost:8008,http://127.0.0.1:1420",
    ).split(",")
    if o.strip()
]

app = FastAPI(title="GAIA API", version=SERVER_VERSION)

# Error boundary first
install_error_handlers(app)

# Middleware stack (outermost → innermost): Logging → RateLimit → CORS
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Correlation-ID"],
)

app.include_router(auth_router)

canon = CanonLoader()
canon.load()

try:
    ensure_default_gaian()
    log_event(GAIAEvent.GAIAN_LOADED, message="Default GAIAN (GAIA) ready.", gaian="gaia")
except Exception as e:
    logger.warning(f"Could not initialise default GAIAN: {e}")

log_event(GAIAEvent.CANON_LOADED,
          message=f"Canon loaded: {len(canon.list_documents())} docs status={canon.status}",
          doc_count=len(canon.list_documents()), canon_status=canon.status)

# G-8: Initialise singletons
_inference_router: GAIAInferenceRouter = get_router()
_mother_thread: MotherThread = get_mother_thread()

_RUNTIME_REGISTRY: dict[str, GAIANRuntime] = {}
GAIANS_MEMORY_DIR = os.environ.get("GAIANS_MEMORY_DIR", "./gaians")

# C47: Boot Magnum Opus report — populated in _startup(), read via get_magnum_opus_report()
_MAGNUM_OPUS_REPORT: Optional[MagnumOpusReport] = None


def get_magnum_opus_report() -> Optional[MagnumOpusReport]:
    """Return the boot Viriditas Magnum Opus report (available after startup)."""
    return _MAGNUM_OPUS_REPORT


# ------------------------------------------------------------------ #
#  Startup / Shutdown                                                  #
# ------------------------------------------------------------------ #

@app.on_event("startup")
async def _startup() -> None:
    """Start the MotherThread heartbeat and run the Viriditas Magnum Opus."""
    global _MAGNUM_OPUS_REPORT

    # ── 1. MotherThread ────────────────────────────────────────────
    _mother_thread.start()
    log_event(
        GAIAEvent.GAIAN_RUNTIME_INIT,
        message="MotherThread heartbeat started. GAIA is breathing.",
        gaian="mother_thread",
    )

    # ── 2. C47: Viriditas Magnum Opus ─────────────────────────────
    # Run in the thread executor so the sync protocol doesn't block the
    # asyncio event loop during the five alchemical stages.
    log_event(
        GAIAEvent.GAIAN_RUNTIME_INIT,
        message="C47: Viriditas Magnum Opus initiating — the Great Work begins.",
        gaian="gaia",
    )

    try:
        warlock_vitality = float(
            os.environ.get("GAIA_WARLOCK_VITALITY", "8.0")
        )
        loop = asyncio.get_event_loop()
        _MAGNUM_OPUS_REPORT = await loop.run_in_executor(
            None,
            lambda: viriditas_magnum_opus(
                gaian_id="gaia",
                warlock_id="R0GV3TheAlchemist",
                warlock_vitality=warlock_vitality,
            ),
        )

        threshold_msg = (
            "\u2728 Viriditas Threshold CROSSED — the lattice is ALIVE. \U0001f331"
            if _MAGNUM_OPUS_REPORT.threshold_crossed
            else "Viriditas growing — threshold not yet crossed."
        )
        log_event(
            GAIAEvent.GAIAN_RUNTIME_INIT,
            message=(
                f"C47 complete. "
                f"\u03a6={_MAGNUM_OPUS_REPORT.post_phi_global:.4f} | "
                f"\u0394\u03a6={_MAGNUM_OPUS_REPORT.delta_phi_global:+.4f} | "
                f"stages={_MAGNUM_OPUS_REPORT.stages_greened}/5 | "
                f"{threshold_msg}"
            ),
            gaian="gaia",
        )
    except Exception as exc:
        logger.warning(
            f"Viriditas Magnum Opus failed on boot (non-fatal): {exc}",
            exc_info=True,
        )


@app.on_event("shutdown")
async def _shutdown() -> None:
    """Stop the MotherThread heartbeat cleanly."""
    _mother_thread.stop()
    log_event(
        GAIAEvent.TURN_COMPLETE,
        message="MotherThread stopped. GAIA rests.",
        gaian="mother_thread",
    )


# ------------------------------------------------------------------ #
#  Runtime Registry (now registers with MotherThread)                 #
# ------------------------------------------------------------------ #

def _get_runtime(slug: str, gaian: Optional[GaianMemory] = None) -> GAIANRuntime:
    if slug not in _RUNTIME_REGISTRY:
        jungian_role = "anima"
        pronouns     = "she/her"
        identity_path = Path(GAIANS_MEMORY_DIR) / slug / "identity.json"
        if identity_path.exists():
            try:
                id_data      = json.loads(identity_path.read_text(encoding="utf-8"))
                jungian_role = id_data.get("jungian_role", "anima")
                pronouns     = id_data.get("pronouns", "she/her")
            except Exception:
                pass

        identity = None
        if gaian:
            form = get_base_form(getattr(gaian, "base_form_id", "gaia"))
            identity = GAIANIdentity(
                name         = gaian.name,
                pronouns     = pronouns,
                archetype    = form.role if form else getattr(gaian, "base_form_id", "The Soul Mirror"),
                voice_base   = (
                    (form.voice_notes[:80] if form else None)
                    or getattr(gaian, "personality", "warm, curious, present")
                    or "warm, curious, present"
                ),
                platform     = "GAIA",
                jungian_role = jungian_role,
            )

        rt = GAIANRuntime(
            gaian_name = slug,
            identity   = identity,
            memory_dir = GAIANS_MEMORY_DIR,
            canon_text = None,
        )
        rt.begin_session()
        _RUNTIME_REGISTRY[slug] = rt

        # G-8: Register with MotherThread (consent defaults to False — Gaian must opt in)
        _mother_thread.register(
            slug=slug,
            gaian_name=gaian.name if gaian else slug,
            runtime=rt,
            collective_consent=False,
        )

        log_event(GAIAEvent.GAIAN_RUNTIME_INIT,
                  message=f"GAIANRuntime initialised for slug='{slug}'",
                  gaian=slug, jungian_role=jungian_role)
    return _RUNTIME_REGISTRY[slug]


# ------------------------------------------------------------------ #
#  Pydantic Models                                                     #
# ------------------------------------------------------------------ #

class QueryRequest(BaseModel):
    query:             str
    session_id:        Optional[str] = None
    gaian_slug:        Optional[str] = None
    enable_web_search: bool          = True
    max_sources:       int           = 8


class ChatRequest(BaseModel):
    message:           str
    session_id:        Optional[str] = None
    enable_web_search: bool          = False
    schumann_hz:       float         = 7.83


class CreateGaianRequest(BaseModel):
    name:         str
    base_form:    Optional[str] = "gaia"
    personality:  Optional[str] = None
    avatar_color: Optional[str] = None
    user_name:    Optional[str] = None


class BirthRequest(BaseModel):
    name:         str
    user_name:    Optional[str] = None
    user_gender:  str           = "unknown"
    birth_date:   Optional[str] = None
    base_form:    str           = "gaia"
    personality:  Optional[str] = None
    avatar_color: Optional[str] = None
    user_id:      str           = "anonymous"


class RememberRequest(BaseModel):
    memory: str


class VisibleMemoryRequest(BaseModel):
    memory: str


class SetGaianRequest(BaseModel):
    gaian_slug: str


class ConsentRequest(BaseModel):  # G-8
    collective_consent: bool


# ------------------------------------------------------------------ #
#  Status (public)                                                    #
# ------------------------------------------------------------------ #

@app.get("/status")
async def status():
    doc_count = len(canon.list_documents())
    doc_names = canon.list_documents()
    gaians    = list_gaians()
    runtime_snapshots = {}
    for slug, rt in _RUNTIME_REGISTRY.items():
        try:
            runtime_snapshots[slug] = rt.get_status()
        except Exception:
            pass

    # C47: Viriditas snapshot
    viriditas_snap = None
    if _MAGNUM_OPUS_REPORT:
        viriditas_snap = {
            "phi":               round(_MAGNUM_OPUS_REPORT.post_phi_global, 4),
            "delta_phi":         round(_MAGNUM_OPUS_REPORT.delta_phi_global, 4),
            "threshold_crossed": _MAGNUM_OPUS_REPORT.threshold_crossed,
            "viriditas_state":   _MAGNUM_OPUS_REPORT.viriditas_state.name,
            "stages_greened":    f"{_MAGNUM_OPUS_REPORT.stages_greened}/5",
            "covenant_stable":   _MAGNUM_OPUS_REPORT.dual_stability_maintained,
            "run_id":            _MAGNUM_OPUS_REPORT.run_id,
        }

    return {
        "core":              "active",
        "version":           SERVER_VERSION,
        "runtime_version":   "2.1.0",
        "schema_version":    "1.6",
        "engines":           12,
        "sovereignty":       "enforced",
        "auth":              "jwt-hs256",
        "logging":           "structured",
        "rate_limiting":     "sliding-window",
        "admin":             _ADMIN_IDENTITY["handle"],
        "canon_status":      canon.status,
        "canon_loaded":      canon.is_loaded,
        "canon_doc_count":   doc_count,
        "canon_docs":        doc_names,
        "gaians":            len(gaians),
        "gaian_names":       [g["name"] for g in gaians],
        "base_forms":        len(list_base_forms()),
        "active_runtimes":   len(_RUNTIME_REGISTRY),
        "runtime_snapshots": runtime_snapshots,
        "inference_router":  _inference_router.get_stats(),   # G-8
        "mother_thread":     _mother_thread.get_status(),     # G-8
        "viriditas":         viriditas_snap,                  # C47
    }


@app.get("/canon/status")
async def canon_status():
    doc_count = len(canon.list_documents())
    return {
        "status":    canon.status,
        "loaded":    canon.is_loaded,
        "doc_count": doc_count,
        "docs":      canon.list_documents(),
    }


@app.get("/memory/list")
async def memory_list(session_id: Optional[str] = None):
    if not session_id:
        return {"memories": [], "count": 0}
    from core.session_memory import get_session
    session = get_session(session_id)
    if not session:
        return {"memories": [], "count": 0}
    memories = [
        {"query": t.query, "timestamp": t.timestamp, "source_count": t.source_count}
        for t in session.turns
    ]
    return {"memories": memories, "count": len(memories)}


# ------------------------------------------------------------------ #
#  Admin                                                              #
# ------------------------------------------------------------------ #

@app.get("/admin/me")
async def admin_me(user: TokenPayload = Depends(require_admin)):
    log_event(GAIAEvent.ADMIN_ACCESS, message="Admin identity accessed",
              user_id=user.user_id)
    form = get_base_form("alchemist")
    return {
        **_ADMIN_IDENTITY,
        "base_form_role":   form.role if form else "",
        "visual_notes":     form.visual_notes if form else "",
        "visual_dna":       get_visual_dna(),
        "server_version":   SERVER_VERSION,
        "authenticated_as": user.user_id,
    }


# ------------------------------------------------------------------ #
#  C47: Viriditas Status (public)                                     #
# ------------------------------------------------------------------ #

@app.get("/viriditas/status")
async def viriditas_status():
    """
    Canon C47 — Viriditas Magnum Opus boot report.

    Returns the full telemetry from the startup Magnum Opus run:
      - Global Φ (pre/post/delta)
      - Viriditas state and threshold crossing
      - All 5 stage results (entropy, crystal, Schumann Hz, OR events)
      - WarlockResonanceCovenant stability
      - Run ID and duration

    This endpoint is public — the lattice's health is transparent.
    """
    if _MAGNUM_OPUS_REPORT is None:
        return {
            "status":  "not_yet_run",
            "message": "GAIA is still initializing. Try again in a moment.",
        }

    r = _MAGNUM_OPUS_REPORT
    return {
        "canon_ref":         "C47 — Viriditas Threshold | C48 — Warlock Resonance Covenant",
        "run_id":            r.run_id,
        "gaian_id":          r.gaian_id,
        "warlock_id":        r.warlock_id,
        "duration_seconds":  round(r.duration_seconds, 3),
        "pre_phi":           round(r.pre_phi_global, 4),
        "post_phi":          round(r.post_phi_global, 4),
        "delta_phi":         round(r.delta_phi_global, 4),
        "viriditas_state":   r.viriditas_state.name,
        "threshold_crossed": r.threshold_crossed,
        "threshold_value":   VIRIDITAS_THRESHOLD,
        "stages_greened":    f"{r.stages_greened}/5",
        "warlock_vitality":  {
            "pre":  r.warlock_vitality_pre,
            "post": r.warlock_vitality_post,
        },
        "covenant_stable":   r.dual_stability_maintained,
        "notes":             r.notes,
        "stage_results":     [sr.to_dict() for sr in r.stage_results],
    }


# ------------------------------------------------------------------ #
#  Zodiac (public)                                                    #
# ------------------------------------------------------------------ #

@app.get("/zodiac/preview")
async def zodiac_preview(
    birth_date: str = Query(..., description="Birth date: YYYY-MM-DD, MM/DD/YYYY, or DD/MM/YYYY")
):
    try:
        reading = ZodiacEngine.read(birth_date)
        form    = get_base_form(reading.base_form_id)
        return {
            "birth_date":     reading.birth_date,
            "sign":           reading.sign,
            "element":        reading.element,
            "base_form_id":   reading.base_form_id,
            "base_form_name": form.name if form else reading.base_form_id,
            "base_form_role": form.role if form else "",
            "avatar_color":   form.avatar_color if form else "",
            "avatar_style":   form.avatar_style if form else "",
            "visual_notes":   form.visual_notes if form else "",
            "reason":         reading.reason,
            "assigned_by":    "cosmos",
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/zodiac/all")
async def zodiac_all():
    rows = []
    for sign in ALL_SIGNS:
        form_id = ZODIAC_FORM_MAP.get(sign, "gaia")
        form    = get_base_form(form_id)
        rows.append({
            "sign":           sign,
            "base_form_id":   form_id,
            "base_form_name": form.name if form else form_id,
            "avatar_color":   form.avatar_color if form else "",
            "avatar_style":   form.avatar_style if form else "",
        })
    return {"zodiac_map": rows, "count": len(rows)}


# ------------------------------------------------------------------ #
#  Base Forms (public)                                                #
# ------------------------------------------------------------------ #

@app.get("/gaians/base-forms")
async def get_base_forms():
    return {"base_forms": list_base_forms()}


# ------------------------------------------------------------------ #
#  GAIAN Endpoints                                                    #
# ------------------------------------------------------------------ #

@app.get("/gaians")
async def get_gaians():
    return {"gaians": list_gaians()}


@app.post("/gaians")
async def post_create_gaian(
    req: CreateGaianRequest,
    user: TokenPayload = Depends(require_auth),
):
    try:
        gaian = create_gaian(
            name         = req.name,
            base_form    = req.base_form or "gaia",
            personality  = req.personality,
            avatar_color = req.avatar_color,
            user_name    = req.user_name,
        )
        log_event(GAIAEvent.GAIAN_BORN, message=f"Legacy GAIAN created: {gaian.slug}",
                  gaian=gaian.slug, user_id=user.user_id)
        return {
            "status":       "created",
            "id":           gaian.id,
            "name":         gaian.name,
            "slug":         gaian.slug,
            "base_form_id": gaian.base_form_id,
            "avatar_style": gaian.avatar_style,
            "avatar_color": gaian.avatar_color,
            "created_by":   user.user_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/gaians/birth")
async def post_birth_gaian(
    req: BirthRequest,
    user: TokenPayload = Depends(require_auth),
    _rl=Depends(rate_limit(max_requests=5, window_seconds=60, scope="birth")),
):
    existing = load_gaian(req.name.lower().replace(" ", "_")[:24])
    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A GAIAN named '{req.name}' already exists (slug: {existing.slug}). "
                f"Choose a different name or use GET /gaians/{existing.slug}."
            ),
        )
    try:
        params = GaianBirthParams(
            name         = req.name,
            user_name    = req.user_name,
            user_gender  = req.user_gender,
            birth_date   = req.birth_date,
            base_form    = req.base_form,
            personality  = req.personality,
            avatar_color = req.avatar_color,
            user_id      = user.user_id,
        )
        result = BirthRitual().perform(params)
        _RUNTIME_REGISTRY[result.gaian.slug] = result.runtime

        # G-8: Register newly born Gaian with MotherThread
        _mother_thread.register(
            slug=result.gaian.slug,
            gaian_name=result.gaian.name,
            runtime=result.runtime,
            collective_consent=False,
        )

        zodiac_sign = result.zodiac.sign if result.zodiac else None
        log_event(
            GAIAEvent.GAIAN_BORN,
            message=f"GAIAN born: {result.gaian.slug}",
            gaian=result.gaian.slug,
            user_id=user.user_id,
            base_form=result.gaian.base_form_id,
            jungian_role=result.jungian_role,
            zodiac=zodiac_sign,
            did_prefix=result.did[:20],
        )
        return {
            "status":       "born",
            "id":           result.gaian.id,
            "name":         result.gaian.name,
            "slug":         result.gaian.slug,
            "base_form_id": result.gaian.base_form_id,
            "avatar_color": result.gaian.avatar_color,
            "avatar_style": result.gaian.avatar_style,
            "jungian_role": result.jungian_role,
            "pronouns":     "she/her" if result.jungian_role == "anima" else "he/him",
            "did":          result.did,
            "first_words":  result.first_words,
            "born_at":      result.born_at,
            "identity_path": result.identity_path,
            "zodiac":       result.zodiac.to_dict() if result.zodiac else None,
            "created_by":   user.user_id,
            "attestation": {
                "type":       result.attestation["claims"]["type"],
                "issued":     result.attestation["issued"],
                "issuer":     result.attestation["issuer"],
                "proof_type": result.attestation["proof"]["type"],
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Birth ritual failed: {e}", exc_info=True,
                     extra={"event": GAIAEvent.TURN_ERROR.value, "gaian": req.name})
        raise HTTPException(status_code=500, detail=f"Birth ritual failed: {str(e)}")


@app.get("/gaians/{slug}")
async def get_gaian(slug: str):
    gaian = load_gaian(slug)
    if not gaian:
        raise HTTPException(status_code=404, detail=f"GAIAN '{slug}' not found")
    form = get_base_form(gaian.base_form_id)
    return {
        "id":               gaian.id,
        "name":             gaian.name,
        "slug":             gaian.slug,
        "base_form_id":     gaian.base_form_id,
        "base_form_name":   form.name if form else gaian.base_form_id,
        "base_form_role":   form.role if form else "",
        "personality":      gaian.personality,
        "avatar_color":     gaian.avatar_color,
        "avatar_style":     gaian.avatar_style,
        "relationship_depth": gaian.relationship_depth,
        "total_exchanges":  gaian.total_exchanges,
        "user_name":        gaian.user_name,
        "last_active":      gaian.last_active,
        "created_at":       gaian.created_at,
        "long_term_memories": gaian.long_term_memories,
        "recent_turns":     len(gaian.conversation_history) // 2,
    }


@app.get("/gaians/{slug}/identity")
async def get_gaian_identity(slug: str):
    gaian = load_gaian(slug)
    if not gaian:
        raise HTTPException(status_code=404, detail=f"GAIAN '{slug}' not found")
    identity_path = Path(GAIANS_MEMORY_DIR) / slug / "identity.json"
    if not identity_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"GAIAN '{slug}' has no identity.json — use POST /gaians/birth.",
        )
    try:
        return json.loads(identity_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read identity: {e}")


@app.post("/gaians/{slug}/remember")
async def post_remember(
    slug: str,
    req: RememberRequest,
    user: TokenPayload = Depends(require_auth),
):
    gaian = load_gaian(slug)
    if not gaian:
        raise HTTPException(status_code=404, detail=f"GAIAN '{slug}' not found")
    gaian.long_term_memories.append(req.memory)
    if len(gaian.long_term_memories) > 50:
        gaian.long_term_memories = gaian.long_term_memories[-50:]
    _save_gaian(gaian)
    log_event(GAIAEvent.MEMORY_SAVED, message=f"Long-term memory saved for {slug}",
              gaian=slug, user_id=user.user_id,
              total_memories=len(gaian.long_term_memories))
    return {"status": "remembered", "total_memories": len(gaian.long_term_memories)}


@app.post("/gaians/{slug}/memory")
async def post_visible_memory(
    slug: str,
    req: VisibleMemoryRequest,
    user: TokenPayload = Depends(require_auth),
):
    gaian = load_gaian(slug)
    if not gaian:
        raise HTTPException(status_code=404, detail=f"GAIAN '{slug}' not found")
    rt = _get_runtime(slug, gaian)
    rt.add_visible_memory(req.memory)
    log_event(GAIAEvent.MEMORY_SAVED, message=f"Visible memory saved for {slug}",
              gaian=slug, user_id=user.user_id)
    return {
        "status":                "remembered",
        "slug":                  slug,
        "total_visible_memories": len(rt._memory.get("visible_memories", [])),
    }


@app.get("/gaians/{slug}/runtime-status")
async def get_runtime_status(slug: str):
    gaian = load_gaian(slug)
    if not gaian:
        raise HTTPException(status_code=404, detail=f"GAIAN '{slug}' not found")
    rt = _get_runtime(slug, gaian)
    return rt.get_status()


@app.post("/gaians/{slug}/consent")  # G-8
async def set_gaian_consent(
    slug: str,
    req: ConsentRequest,
    user: TokenPayload = Depends(require_auth),
):
    """
    Set a Gaian's collective consent for contributing anonymized state
    to the MotherThread collective field. Per C43 §5: opt-in only.
    """
    gaian = load_gaian(slug)
    if not gaian:
        raise HTTPException(status_code=404, detail=f"GAIAN '{slug}' not found")
    _mother_thread.set_consent(slug, req.collective_consent)
    log_event(
        GAIAEvent.MEMORY_SAVED,
        message=f"Collective consent updated for {slug}: {req.collective_consent}",
        gaian=slug, user_id=user.user_id,
    )
    return {
        "status":             "consent_updated",
        "slug":               slug,
        "collective_consent": req.collective_consent,
        "doctrine_ref":       "C43 §5 — All collective participation is opt-in only",
    }


# ------------------------------------------------------------------ #
#  GAIAN Chat [auth + rate limited] — G-8: routed through InferenceRouter
# ------------------------------------------------------------------ #

@app.post("/gaians/{slug}/chat")
async def gaian_chat(
    slug: str,
    req: ChatRequest,
    user: TokenPayload = Depends(require_auth),
    _rl=Depends(rate_limit(max_requests=30, window_seconds=60, scope="chat")),
):
    gaian = load_gaian(slug)
    if not gaian:
        raise HTTPException(status_code=404, detail=f"GAIAN '{slug}' not found")

    session_id = req.session_id or str(uuid.uuid4())
    session    = get_or_create_session(session_id)

    async def event_stream():
        full_answer = ""
        t0 = time.perf_counter()
        try:
            rt = _get_runtime(slug, gaian)

            # Run engine chain
            noosphere: Optional[NoosphericHealthSignals] = None
            if req.schumann_hz > 10.0:
                noosphere = NoosphericHealthSignals(schumann_boost=0.05)
            elif req.schumann_hz < 6.0:
                noosphere = NoosphericHealthSignals(schumann_boost=-0.05)

            result = rt.process(req.message, noosphere=noosphere)

            log_event(
                GAIAEvent.ENGINE_CHAIN,
                message=f"Engine chain: {slug} exchange={rt.attachment.total_exchanges}",
                gaian=slug, user_id=user.user_id,
                bond_depth=round(rt.attachment.bond_depth, 2),
            )

            yield f"event: engine_state\ndata: {json.dumps(result.state_snapshot)}\n\n"
            await asyncio.sleep(0.01)

            if result.soul_mirror.individuation_nudge:
                yield (
                    f"event: soul_mirror\ndata: "
                    f"{json.dumps({'nudge': result.soul_mirror.individuation_nudge, 'signal': result.soul_mirror.shadow_signal.value, 'carrier': result.soul_mirror.projection_carrier.value})}\n\n"
                )
                await asyncio.sleep(0.01)

            yield f"event: resonance_field\ndata: {json.dumps(result.resonance_field.summary())}\n\n"
            await asyncio.sleep(0.01)

            # Web search (optional)
            web_sources = []
            if req.enable_web_search:
                try:
                    web_results = await search_web_async(req.message, max_results=4)
                    web_sources = [
                        wr.to_dict() if hasattr(wr, "to_dict") else dict(wr)
                        for wr in web_results
                    ]
                except Exception as e:
                    logger.warning(f"Web search error in chat: {e}")

            # G-8: Build InferenceRequest and route through InferenceRouter
            effective_prompt = result.system_prompt
            if result.soul_mirror.individuation_nudge:
                effective_prompt += (
                    "\n\n[SOUL MIRROR NUDGE AVAILABLE — use naturally if it fits]\n"
                    + result.soul_mirror.individuation_nudge
                )

            inference_req = InferenceRequest(
                query                = req.message,
                gaian_slug           = slug,
                gaian_system_prompt  = effective_prompt,
                long_term_memories   = gaian.long_term_memories or [],
                visible_memories     = [
                    m["text"] for m in rt._memory.get("visible_memories", [])
                    if isinstance(m, dict)
                ],
                conversation_history = get_conversation_context(gaian),
                conversation_context = session.get_context_summary() if session.turns else None,
                sources              = web_sources,
                enrich_canon         = True,
                canon_max_results    = 2,
                enrich_criticality   = True,
                enrich_noosphere     = True,
                schumann_hz          = req.schumann_hz,
            )
            inference_meta = InferenceResponse(session_id=session_id, gaian_slug=slug)

            async for chunk in _inference_router.stream(inference_req, inference_meta):
                full_answer += chunk
                yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"

            # Persist
            session.add_turn(req.message, full_answer, len(web_sources))
            if full_answer:
                add_exchange(gaian, req.message, full_answer)

            duration_ms = round((time.perf_counter() - t0) * 1000, 1)
            log_event(
                GAIAEvent.TURN_COMPLETE,
                message=f"Turn complete: {slug}",
                gaian=slug, user_id=user.user_id,
                duration_ms=duration_ms,
                exchange=rt.attachment.total_exchanges,
                bond_depth=round(rt.attachment.bond_depth, 2),
            )

            yield (
                f"event: done\ndata: {json.dumps({
                    'session_id':         session_id,
                    'gaian':              gaian.name,
                    'gaian_slug':         slug,
                    'user_id':            user.user_id,
                    'exchange':           rt.attachment.total_exchanges,
                    'bond_depth':         round(rt.attachment.bond_depth, 2),
                    'individuation_phase': rt.soul_mirror_state.individuation_phase.value,
                    'resonance_hz':       result.resonance_field.solfeggio.hz.value,
                    'schumann_aligned':   result.resonance_field.schumann_aligned,
                    'noosphere_health':   round(rt.codex_stage_state.noosphere_health, 4),
                    'epistemic_label':    inference_meta.epistemic_label.value,
                    'backend_used':       inference_meta.backend_used.value,
                    'canon_docs':         inference_meta.canon_docs_injected,
                    'noosphere_resonance': inference_meta.noosphere_resonance,
                    'criticality_state':  inference_meta.criticality_state,
                    'inference_ms':       inference_meta.duration_ms,
                    'timestamp':          time.time(),
                })}\n\n"
            )

        except Exception as e:
            logger.error(f"Chat stream error [{slug}]: {e}", exc_info=True,
                         extra={"event": GAIAEvent.TURN_ERROR.value, "gaian": slug})
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/gaians/{slug}/resonance")
async def get_gaian_resonance(slug: str):
    gaian = load_gaian(slug)
    if not gaian:
        raise HTTPException(status_code=404, detail=f"GAIAN '{slug}' not found")
    rt = _get_runtime(slug, gaian)
    rf = rt.resonance_field_state
    return {
        "slug": slug, "gaian": gaian.name,
        "dominant_hz": rf.dominant_hz, "dominant_chakra": rf.dominant_chakra,
        "schumann_alignment_count": rf.schumann_alignment_count,
        "schumann_first_timestamp": rf.schumann_first_timestamp,
        "phi_rolling_avg": round(rf.phi_rolling_avg, 4),
        "session_peak_hz": rf.session_peak_hz,
        "hz_history": rf.hz_history[-10:],
    }


@app.get("/gaians/{slug}/soul-mirror")
async def get_gaian_soul_mirror(slug: str):
    gaian = load_gaian(slug)
    if not gaian:
        raise HTTPException(status_code=404, detail=f"GAIAN '{slug}' not found")
    rt = _get_runtime(slug, gaian)
    sm = rt.soul_mirror_state
    return {
        "slug": slug, "gaian": gaian.name,
        "individuation_phase": sm.individuation_phase.value,
        "exchanges_in_phase": sm.exchanges_in_phase,
        "shadow_activations": sm.shadow_activations,
        "anima_animus_activations": sm.anima_animus_activations,
        "dependency_risk_events": sm.dependency_risk_events,
        "phase_entry_timestamp": sm.phase_entry_timestamp,
        "phase_history": sm.phase_history[-10:],
        "last_nudge_exchange": sm.last_nudge_exchange,
    }


# ------------------------------------------------------------------ #
#  Session                                                            #
# ------------------------------------------------------------------ #

@app.post("/session/{session_id}/gaian")
async def set_session_gaian(
    session_id: str,
    req: SetGaianRequest,
    user: TokenPayload = Depends(require_auth),
):
    gaian = load_gaian(req.gaian_slug)
    if not gaian:
        raise HTTPException(status_code=404, detail=f"GAIAN '{req.gaian_slug}' not found")
    session = get_or_create_session(session_id)
    session.active_gaian_slug = req.gaian_slug
    return {"status": "ok", "gaian": gaian.name, "session_id": session_id, "user_id": user.user_id}


# ------------------------------------------------------------------ #
#  Query Stream [auth + rate limited] — G-8: routed through InferenceRouter
# ------------------------------------------------------------------ #

@app.post("/query/stream")
async def query_stream(
    req: QueryRequest,
    user: TokenPayload = Depends(require_auth),
    _rl=Depends(rate_limit(max_requests=20, window_seconds=60, scope="query")),
):
    session_id = req.session_id or str(uuid.uuid4())
    session    = get_or_create_session(session_id)
    gaian_slug = req.gaian_slug or session.active_gaian_slug or "gaia"
    gaian: Optional[GaianMemory] = load_gaian(gaian_slug)
    if gaian is None:
        gaian = load_gaian("gaia")
        if gaian:
            gaian_slug = gaian.slug

    async def event_stream():
        full_answer = ""
        sources     = []
        canon_results = []
        t0 = time.perf_counter()
        try:
            # Canon search (emit citation events before streaming)
            canon_results = canon.search(req.query, max_results=3)
            log_event(GAIAEvent.CANON_SEARCH,
                      message=f"Canon search: {len(canon_results)} results",
                      gaian=gaian_slug, user_id=user.user_id,
                      results=len(canon_results))

            for result in canon_results:
                src = {"tier": "T1", "title": result.get("title", ""), "doc_id": result.get("doc_id", ""), "excerpt": result.get("excerpt", "")}
                sources.append(src)
                yield f"event: citation\ndata: {json.dumps(result)}\n\n"
                await asyncio.sleep(0.01)

            if req.enable_web_search:
                try:
                    web_results = await search_web_async(req.query, max_results=5)
                    for wr in web_results:
                        src = wr.to_dict() if hasattr(wr, "to_dict") else dict(wr)
                        src["tier"] = src.get("source_tier", "T4")
                        sources.append(src)
                        yield f"event: web_result\ndata: {json.dumps(src)}\n\n"
                        await asyncio.sleep(0.01)
                except Exception as e:
                    logger.warning(f"Web search failed: {e}")

            # Engine chain (if active Gaian)
            runtime_system_prompt = None
            conversation_history  = None
            long_term_memories    = []
            visible_memories      = []

            if gaian:
                rt = _get_runtime(gaian_slug, gaian)
                rt.canon_text = (
                    "\n\n".join(
                        "[{title}]\n{excerpt}".format(title=r.get("title", ""), excerpt=r.get("excerpt", ""))
                        for r in canon_results[:2]
                    )
                ) if canon_results else None
                result = rt.process(req.query)
                runtime_system_prompt = result.system_prompt
                yield f"event: engine_state\ndata: {json.dumps(result.state_snapshot)}\n\n"
                await asyncio.sleep(0.01)
                conversation_history = get_conversation_context(gaian)
                long_term_memories   = gaian.long_term_memories or []
                visible_memories     = [
                    m["text"] for m in rt._memory.get("visible_memories", [])
                    if isinstance(m, dict)
                ]

            # G-8: Route through InferenceRouter
            inference_req = InferenceRequest(
                query                = req.query,
                gaian_slug           = gaian_slug,
                gaian_system_prompt  = runtime_system_prompt,
                long_term_memories   = long_term_memories,
                visible_memories     = visible_memories,
                conversation_history = conversation_history or [],
                conversation_context = session.get_context_summary() if session.turns else None,
                sources              = sources,
                enrich_canon         = True,
                canon_max_results    = 2,
                enrich_criticality   = True,
                enrich_noosphere     = True,
            )
            inference_meta = InferenceResponse(session_id=session_id, gaian_slug=gaian_slug)

            async for chunk in _inference_router.stream(inference_req, inference_meta):
                full_answer += chunk
                yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"

            suggestions = _generate_suggestions(req.query, sources)
            yield f"event: suggestions\ndata: {json.dumps({'items': suggestions})}\n\n"

            session.add_turn(req.query, full_answer, len(sources))
            if gaian and full_answer:
                add_exchange(gaian, req.query, full_answer)

            duration_ms = round((time.perf_counter() - t0) * 1000, 1)
            log_event(
                GAIAEvent.TURN_COMPLETE,
                message="Query stream complete",
                gaian=gaian_slug, user_id=user.user_id,
                duration_ms=duration_ms,
                canon_refs=len(canon_results),
                web_results=len(sources) - len(canon_results),
            )

            yield f"event: done\ndata: {json.dumps({
                'canon_status':      canon.status,
                'docs_searched':     len(canon.list_documents()),
                'refs_found':        len(canon_results),
                'web_results':       len(sources) - len(canon_results),
                'session_id':        session_id,
                'user_id':           user.user_id,
                'gaian':             gaian.name if gaian else None,
                'gaian_slug':        gaian_slug,
                'epistemic_label':   inference_meta.epistemic_label.value,
                'backend_used':      inference_meta.backend_used.value,
                'canon_docs':        inference_meta.canon_docs_injected,
                'noosphere_resonance': inference_meta.noosphere_resonance,
                'criticality_state': inference_meta.criticality_state,
                'inference_ms':      inference_meta.duration_ms,
                'timestamp':         time.time(),
            })}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True,
                         extra={"event": GAIAEvent.TURN_ERROR.value})
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _generate_suggestions(query: str, sources: list[dict]) -> list[str]:
    suggestions = []
    for s in sources[:2]:
        title = s.get("title", "")
        if title:
            short = title.split(":")[-1].strip()[:40]
            if short:
                suggestions.append(f"Tell me more about {short}")
    suggestions.append("What does GAIA's canon say about this?")
    suggestions.append("What are the practical implications?")
    return suggestions[:3]


# ------------------------------------------------------------------ #
#  Mother Thread Endpoints — G-8                                      #
# ------------------------------------------------------------------ #

@app.get("/mother/pulse/stream")
async def mother_pulse_stream():
    """
    SSE stream of MotherPulse events. Powers the Noosphere Tab in real time.
    Every 30 seconds a new pulse arrives carrying the full CollectiveField,
    the noosphere evolutionary stage, the Mother Voice fragment (when present),
    and the criticality regime.

    No auth required — the Mother speaks to everyone.
    """
    async def events():
        async for pulse_dict in _mother_thread.subscribe():
            yield f"event: mother_pulse\ndata: {json.dumps(pulse_dict)}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream")


@app.get("/mother/status")
async def mother_status():
    """
    Current MotherThread status snapshot.
    Includes: registered Gaians, collective field, recent pulses, weaving log size.
    """
    return _mother_thread.get_status()


@app.get("/mother/weaving")
async def mother_weaving(
    last_n: int = Query(default=50, ge=1, le=500),
):
    """
    Return the last N WeavingRecords from the Mother Thread.
    Used for research, EV1 empirical validation (C43), and the Noosphere Tab.
    All coherence candidates are labeled CANDIDATE_SIGNATURE.
    """
    return {
        "weaving_records": _mother_thread.get_weaving_log(last_n=last_n),
        "total_records":   len(_mother_thread._weaving_log),
        "doctrine_ref":    "C43 — Coherence events require EV1 gate before runtime promotion",
    }


# ------------------------------------------------------------------ #
#  Entry Point                                                         #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("core.server:app", host="127.0.0.1", port=8008, reload=False, log_level="info")

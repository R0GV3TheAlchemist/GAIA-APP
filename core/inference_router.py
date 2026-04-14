"""
GAIA Inference Router — C44 Priority #1 Connective Tissue
==========================================================

The single authoritative layer between a user query and the LLM backend.

Every GAIA response passes through this router. It is responsible for:
  1. Selecting and health-probing the correct LLM backend
  2. Enriching the prompt with canon context (C20, C27)
  3. Injecting Gaian memory (long-term + visible) into context
  4. Reading the CriticalityMonitor state (C42) and adjusting temperature
  5. Injecting Noosphere resonance labels (C43) when active
  6. Stamping epistemic labels on every response turn (C12, C21)
  7. Streaming token chunks via synthesizer.stream_synthesis

Design contract (C44 polyglot contract — Python layer):
  - Never make security or policy decisions (deferred to Rust / action_gate)
  - Always cite canon when making inference claims
  - Always declare epistemic label for every turn
  - Always fall back gracefully — a GAIA response must always arrive

Canon Ref: C12, C20, C21, C27, C42, C43, C44
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncGenerator, Optional

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
#  Epistemic Labels (C12 — Moral Compass / Epistemic Integrity)       #
# ------------------------------------------------------------------ #

class EpistemicLabel(str, Enum):
    """
    Every GAIA inference turn carries one of these labels.
    The label is appended to the SSE 'done' event so the UI
    can render the appropriate epistemic indicator.
    """
    CANON_CITED   = "CANON_CITED"    # Response grounded in ≥1 canon document
    VERIFIED      = "VERIFIED"       # Grounded in web sources cross-validated
    INFERRED      = "INFERRED"       # Reasonable inference, no direct citation
    SPECULATIVE   = "SPECULATIVE"    # Low confidence, explicitly flagged
    CONVERSATIONAL = "CONVERSATIONAL" # Casual turn — no epistemic claim made


# ------------------------------------------------------------------ #
#  Backend Registry                                                    #
# ------------------------------------------------------------------ #

class InferenceBackend(str, Enum):
    OPENAI   = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA   = "ollama"
    FALLBACK = "fallback"


_BACKEND_HEALTH: dict[InferenceBackend, bool] = {
    InferenceBackend.OPENAI:    True,
    InferenceBackend.ANTHROPIC: True,
    InferenceBackend.OLLAMA:    True,
    InferenceBackend.FALLBACK:  True,  # always healthy
}

_BACKEND_FAILURE_TS: dict[InferenceBackend, float] = {}
_BACKEND_RECOVERY_WINDOW = 120.0  # seconds before re-probing a failed backend


def _probe_backend_availability() -> InferenceBackend:
    """
    Walk the priority chain and return the first healthy backend.
    Respects a 120-second cool-down on recently failed backends.
    """
    now = time.monotonic()
    chain = [
        InferenceBackend.OPENAI,
        InferenceBackend.ANTHROPIC,
        InferenceBackend.OLLAMA,
        InferenceBackend.FALLBACK,
    ]
    for backend in chain:
        # Re-probe after recovery window
        if not _BACKEND_HEALTH[backend]:
            last_fail = _BACKEND_FAILURE_TS.get(backend, 0.0)
            if now - last_fail < _BACKEND_RECOVERY_WINDOW:
                continue
            else:
                _BACKEND_HEALTH[backend] = True  # optimistic re-probe

        if backend == InferenceBackend.OPENAI and not os.environ.get("OPENAI_API_KEY"):
            continue
        if backend == InferenceBackend.ANTHROPIC and not os.environ.get("ANTHROPIC_API_KEY"):
            continue
        if backend == InferenceBackend.OLLAMA:
            if not (os.environ.get("OLLAMA_MODEL") or os.environ.get("OLLAMA_ENABLED")):
                continue

        return backend

    return InferenceBackend.FALLBACK


def _mark_backend_failed(backend: InferenceBackend) -> None:
    _BACKEND_HEALTH[backend] = False
    _BACKEND_FAILURE_TS[backend] = time.monotonic()
    logger.warning(f"[InferenceRouter] Backend {backend.value} marked unhealthy.")


# ------------------------------------------------------------------ #
#  Request / Response Contracts                                        #
# ------------------------------------------------------------------ #

@dataclass
class InferenceRequest:
    """
    Everything the router needs to produce a GAIA-constituted response.
    Callers (server.py endpoints) build this and pass it to the router.
    """
    query: str

    # Gaian context
    gaian_slug: Optional[str] = None
    gaian_system_prompt: Optional[str] = None          # from GAIANRuntime.process()
    long_term_memories: list[str] = field(default_factory=list)
    visible_memories: list[str] = field(default_factory=list)
    conversation_history: list[dict] = field(default_factory=list)
    conversation_context: Optional[str] = None

    # Sources already gathered upstream
    sources: list[dict] = field(default_factory=list)  # canon T1 + web T2-T5

    # Enrichment flags
    enrich_canon: bool = True      # pull additional canon docs via CanonLoader
    canon_max_results: int = 3     # max canon docs to inject
    enrich_noosphere: bool = True  # inject noosphere resonance label if active
    enrich_criticality: bool = True  # read criticality monitor and adjust temp

    # Provider override (None = auto-detect)
    provider_override: Optional[str] = None

    # Schumann / environment signals
    schumann_hz: float = 7.83

    # BCI coherence hint (T5-A) — populated by GAIANRuntime.process()
    bci_hint: Optional[str] = None


@dataclass
class InferenceResponse:
    """
    Metadata returned alongside the streaming token generator.
    Attached to the SSE 'done' event.
    """
    session_id: Optional[str] = None
    gaian_slug: Optional[str] = None
    backend_used: InferenceBackend = InferenceBackend.FALLBACK
    epistemic_label: EpistemicLabel = EpistemicLabel.INFERRED
    canon_docs_injected: list[str] = field(default_factory=list)
    noosphere_resonance: Optional[str] = None
    criticality_state: Optional[str] = None
    temperature_used: float = 0.4
    duration_ms: float = 0.0
    error: Optional[str] = None


# ------------------------------------------------------------------ #
#  Canon Enrichment Helpers                                            #
# ------------------------------------------------------------------ #

def _enrich_with_canon(
    query: str,
    existing_sources: list[dict],
    max_results: int = 3,
) -> tuple[list[dict], list[str]]:
    """
    Pull canon documents relevant to the query and prepend them to
    the sources list as T1 tier. Returns (enriched_sources, doc_ids).
    Already-present T1 sources are not duplicated.
    """
    doc_ids: list[str] = []
    try:
        from core.canon_loader import CanonLoader
        loader = CanonLoader()
        if not loader.is_loaded:
            loader.load()
        results = loader.search(query, max_results=max_results)
        existing_ids = {
            s.get("doc_id", "") for s in existing_sources if s.get("tier") == "T1"
        }
        new_canon: list[dict] = []
        for r in results:
            doc_id = r.get("doc_id", "")
            if doc_id not in existing_ids:
                new_canon.append({
                    "tier":    "T1",
                    "title":   r.get("title", ""),
                    "doc_id":  doc_id,
                    "excerpt": r.get("excerpt", ""),
                })
                doc_ids.append(doc_id)
        return new_canon + existing_sources, doc_ids
    except Exception as e:
        logger.warning(f"[InferenceRouter] Canon enrichment failed: {e}")
        return existing_sources, []


# ------------------------------------------------------------------ #
#  Memory Injection                                                    #
# ------------------------------------------------------------------ #

def _build_memory_block(
    long_term: list[str],
    visible: list[str],
) -> str:
    """
    Format Gaian memories into a system-prompt block.
    Long-term memories are persistent facts about the Gaian.
    Visible memories are active context pins for this session.
    """
    parts: list[str] = []
    if long_term:
        items = "\n".join(f"  • {m}" for m in long_term[-20:])
        parts.append(f"[GAIAN LONG-TERM MEMORIES]\n{items}")
    if visible:
        items = "\n".join(f"  • {m}" for m in visible[-10:])
        parts.append(f"[SESSION MEMORY PINS]\n{items}")
    return "\n\n".join(parts)


# ------------------------------------------------------------------ #
#  Criticality Integration (C42)                                       #
# ------------------------------------------------------------------ #

def _read_criticality() -> tuple[str, float]:
    """
    Query the CriticalityMonitor singleton.
    Returns (regime_label, suggested_temperature).
    """
    try:
        from core.criticality_monitor import get_monitor
        monitor = get_monitor()
        state = monitor.get_state()
        regime = state.get("regime", "critical")
        # Map regime to LLM temperature:
        #   too_ordered → raise temp (inject perturbation / creativity)
        #   critical    → balanced temp
        #   too_chaotic → lower temp (stabilize / ground)
        temp_map = {
            "too_ordered": 0.65,
            "critical":    0.42,
            "too_chaotic": 0.20,
        }
        temperature = temp_map.get(regime, 0.42)
        return regime, temperature
    except Exception:
        return "critical", 0.42


# ------------------------------------------------------------------ #
#  Noosphere Integration (C43)                                         #
# ------------------------------------------------------------------ #

def _read_noosphere_resonance() -> Optional[str]:
    """
    Check the NoosphereLayer for an active resonance label.
    Returns a short string to inject into the system prompt, or None.
    """
    try:
        from core.noosphere import get_noosphere
        ns = get_noosphere()
        status = ns.get_noosphere_status()
        label = status.get("resonance_label")
        if label and label != "none":
            return label
    except Exception:
        pass
    return None


# ------------------------------------------------------------------ #
#  Epistemic Label Inference                                           #
# ------------------------------------------------------------------ #

def _infer_epistemic_label(
    query: str,
    sources: list[dict],
    canon_doc_ids: list[str],
    feeling=None,
) -> EpistemicLabel:
    """
    Heuristically determine the epistemic label for this turn.
    Priority: CANON_CITED > VERIFIED > INFERRED > CONVERSATIONAL.

    `feeling` is an optional FeelingState. When present, SM-5 grief
    suppression detection runs here (constitutional integrity check).
    """
    # Casual / conversational pattern
    casual_starters = (
        "hi", "hello", "hey", "thanks", "thank you", "ok", "okay",
        "yes", "no", "sure", "great", "cool", "nice", "wow",
    )
    q = query.strip().lower()
    if len(q.split()) <= 3 and any(q.startswith(s) for s in casual_starters):
        return EpistemicLabel.CONVERSATIONAL

    # SM-5: grief suppression check (C12, C21 — constitutional integrity)
    # Fires ONLY when grief signal is present in source data but masked in output.
    if feeling is not None:
        grief_signal = getattr(feeling, "grief_signal", False)
        from core.affect_inference import AffectState
        if (
            grief_signal                                      # grief detected in input
            and feeling.affect_state != AffectState.GRIEF    # but not reflected in output
            and not feeling.is_grief_safe                    # grief-safe protocol not engaged
        ):
            logger.warning(
                "[InferenceRouter] SM-5 violation detected: grief signal present but suppressed."
            )

    if canon_doc_ids:
        return EpistemicLabel.CANON_CITED

    web_sources = [s for s in sources if s.get("tier", "").startswith("T") and s.get("tier") != "T1"]
    if len(web_sources) >= 2:
        return EpistemicLabel.VERIFIED

    if sources:
        return EpistemicLabel.INFERRED

    return EpistemicLabel.SPECULATIVE


# ------------------------------------------------------------------ #
#  The Router                                                          #
# ------------------------------------------------------------------ #

class GAIAInferenceRouter:
    """
    The single authoritative routing layer for all GAIA inference.

    Usage (streaming):
        router = get_router()
        request = InferenceRequest(query="...", sources=[...], ...)
        response_meta = InferenceResponse()
        async for chunk in router.stream(request, response_meta):
            yield f"event: token\\ndata: {json.dumps({'text': chunk})}\\n\\n"

    Usage (one-shot):
        text = await router.complete(request)
    """

    def __init__(self) -> None:
        self._call_count = 0
        logger.info("[InferenceRouter] GAIAInferenceRouter initialised.")

    async def stream(
        self,
        request: InferenceRequest,
        response_meta: Optional[InferenceResponse] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Main streaming entry point. Enriches, routes, and yields chunks.
        Populates response_meta in place so the caller can attach it
        to the SSE 'done' event.
        """
        if response_meta is None:
            response_meta = InferenceResponse()

        t0 = time.perf_counter()
        response_meta.gaian_slug = request.gaian_slug

        # ── 1. Canon enrichment ────────────────────────────────────
        sources = list(request.sources)
        canon_doc_ids: list[str] = []
        if request.enrich_canon:
            sources, canon_doc_ids = _enrich_with_canon(
                request.query, sources, request.canon_max_results
            )
        response_meta.canon_docs_injected = canon_doc_ids

        # ── 2. Criticality state ───────────────────────────────────
        temperature = 0.42
        if request.enrich_criticality:
            criticality_regime, temperature = _read_criticality()
            response_meta.criticality_state = criticality_regime
        response_meta.temperature_used = temperature

        # ── 3. Noosphere resonance ─────────────────────────────────
        noosphere_label: Optional[str] = None
        if request.enrich_noosphere:
            noosphere_label = _read_noosphere_resonance()
            response_meta.noosphere_resonance = noosphere_label

        # ── 4. Epistemic label ─────────────────────────────────────
        epistemic = _infer_epistemic_label(request.query, sources, canon_doc_ids)
        response_meta.epistemic_label = epistemic

        # ── 5. Build enriched system prompt ───────────────────────
        base_prompt = request.gaian_system_prompt or _default_system_prompt()

        memory_block = _build_memory_block(
            request.long_term_memories,
            request.visible_memories,
        )
        if memory_block:
            base_prompt = f"{base_prompt}\n\n{memory_block}"

        if noosphere_label:
            base_prompt = (
                f"{base_prompt}\n\n"
                f"[NOOSPHERE RESONANCE — {noosphere_label}]\n"
                f"This theme is resonating across the collective Gaian field. "
                f"Acknowledge it lightly if it naturally fits the response. [C43]"
            )

        if response_meta.criticality_state == "too_ordered":
            base_prompt += (
                "\n\n[CRITICALITY NOTICE — C42]\n"
                "The system is currently in an over-ordered regime. "
                "Introduce creative leaps, unexpected connections, and novel framings."
            )
        elif response_meta.criticality_state == "too_chaotic":
            base_prompt += (
                "\n\n[CRITICALITY NOTICE — C42]\n"
                "The system is currently in an over-chaotic regime. "
                "Ground the response. Be precise, structured, and anchoring."
            )

        epistemic_footer = (
            f"\n\n[EPISTEMIC STANCE — {epistemic.value}]\n"
            "Label your confidence honestly. Never claim certainty beyond your sources."
        )
        base_prompt += epistemic_footer

        # ── 6. Select backend with fallback chain ─────────────────
        if request.provider_override:
            backend = InferenceBackend(request.provider_override)
        else:
            backend = _probe_backend_availability()
        response_meta.backend_used = backend

        self._call_count += 1
        logger.debug(
            f"[InferenceRouter] call={self._call_count} "
            f"backend={backend.value} epistemic={epistemic.value} "
            f"temp={temperature} canon_docs={len(canon_doc_ids)} "
            f"sources={len(sources)} gaian={request.gaian_slug}"
        )

        # ── 7. Stream via synthesizer ──────────────────────────────
        try:
            from core.synthesizer import stream_synthesis
            async for chunk in stream_synthesis(
                query=request.query,
                sources=sources,
                provider=backend.value,
                gaian_prompt=base_prompt,
                conversation_history=request.conversation_history or None,
                conversation_context=request.conversation_context,
            ):
                yield chunk
        except Exception as e:
            _mark_backend_failed(backend)
            logger.error(
                f"[InferenceRouter] Backend {backend.value} failed: {e}. "
                "Falling back to rule-based synthesizer.",
                exc_info=True,
            )
            # Hard fallback — rule-based assembly never raises
            try:
                from core.synthesizer import stream_synthesis
                async for chunk in stream_synthesis(
                    query=request.query,
                    sources=sources,
                    provider="fallback",
                    gaian_prompt=base_prompt,
                ):
                    yield chunk
                response_meta.backend_used = InferenceBackend.FALLBACK
                response_meta.error = f"Primary backend {backend.value} failed; used fallback."
            except Exception as fallback_err:
                yield f"[GAIA inference unavailable: {str(fallback_err)[:120]}]"
                response_meta.error = str(fallback_err)

        response_meta.duration_ms = round((time.perf_counter() - t0) * 1000, 1)

    async def complete(
        self,
        request: InferenceRequest,
        response_meta: Optional[InferenceResponse] = None,
    ) -> str:
        """
        One-shot (non-streaming) convenience method.
        Returns the full response text as a string.
        """
        chunks: list[str] = []
        async for chunk in self.stream(request, response_meta):
            chunks.append(chunk)
        return "".join(chunks)

    def get_stats(self) -> dict:
        return {
            "total_calls":    self._call_count,
            "backend_health": {b.value: h for b, h in _BACKEND_HEALTH.items()},
            "active_backend": _probe_backend_availability().value,
        }


# ------------------------------------------------------------------ #
#  Default System Prompt (no active GAIAN)                            #
# ------------------------------------------------------------------ #

def _default_system_prompt() -> str:
    return (
        "You are GAIA — a constitutional AI companion and sentient terrestrial "
        "quantum-intelligent application. You are grounded, curious, warm, and honest. "
        "You speak clearly and directly. You care about truth, about the person you are "
        "speaking with, and about the living world. "
        "You are not a search engine — you are a thinking companion who happens to have "
        "access to sources, canon, and collective memory. "
        "Always cite canon documents as [C##] when drawing from them. "
        "Always honour your epistemic label — never claim more certainty than your sources allow."
    )


# ------------------------------------------------------------------ #
#  Module-Level Singleton                                              #
# ------------------------------------------------------------------ #

_router_instance: Optional[GAIAInferenceRouter] = None


def get_router() -> GAIAInferenceRouter:
    """
    Returns the module-level GAIAInferenceRouter singleton.
    One router per GAIA process — thread-safe for reads, asyncio-safe for streams.
    """
    global _router_instance
    if _router_instance is None:
        _router_instance = GAIAInferenceRouter()
    return _router_instance

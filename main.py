"""
GAIA Backend — FastAPI Entry Point
Runs on http://localhost:8008
Launched as a Tauri sidecar (gaia-backend.exe on Windows)
"""

import sys
import os
import signal
import asyncio
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Path setup ──────────────────────────────────────────────────
# Ensure repo root is on path when running frozen (PyInstaller)
if getattr(sys, 'frozen', False):
    ROOT = sys._MEIPASS
else:
    ROOT = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, ROOT)

from api.routers import zodiac

log = logging.getLogger("gaia")

# ── Graceful shutdown ───────────────────────────────────────────────

_shutdown_event = asyncio.Event()


def _signal_handler(signum, frame):
    """Called by SIGTERM or SIGINT — triggers the lifespan shutdown path."""
    sig_name = signal.Signals(signum).name
    log.info(f"[GAIA] Received {sig_name} — initiating graceful shutdown…")
    _shutdown_event.set()


# Register handlers for both SIGTERM (taskkill) and SIGINT (Ctrl+C).
# Windows does not support SIGTERM natively on all Python versions so we
# guard with a try/except to avoid crashing on import.
try:
    signal.signal(signal.SIGTERM, _signal_handler)
except (OSError, ValueError):
    pass  # Not supported on this platform/context

try:
    signal.signal(signal.SIGINT, _signal_handler)
except (OSError, ValueError):
    pass


async def _flush_state() -> None:
    """
    Flush any in-memory engine state to disk before process exit.
    Extend this as GAIA’s engine modules grow — e.g. soul mirror, shadow log,
    coherence snapshots, session memory.
    """
    log.info("[GAIA] Flushing engine state…")

    # Placeholder: write a shutdown tombstone so the next launch knows
    # whether the previous session ended cleanly.
    state_dir = os.path.join(ROOT, "data")
    os.makedirs(state_dir, exist_ok=True)

    tombstone_path = os.path.join(state_dir, "last_shutdown.txt")
    try:
        import datetime
        with open(tombstone_path, "w") as f:
            f.write(datetime.datetime.utcnow().isoformat() + "Z\n")
        log.info(f"[GAIA] Tombstone written → {tombstone_path}")
    except Exception as e:
        log.warning(f"[GAIA] Could not write tombstone: {e}")

    log.info("[GAIA] Shutdown complete.")


# ── FastAPI lifespan ───────────────────────────────────────────────

@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup → yield → shutdown sequence for the FastAPI app."""
    log.info("[GAIA] Backend starting up — port 8008")

    # ─ startup work goes here (load models, warm caches, etc.) ─
    yield
    # ─ shutdown work ─

    await _flush_state()


# ── App ──────────────────────────────────────────────────────────

app = FastAPI(
    title="GAIA Backend",
    description="Sovereign AI Companion — Python Core",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow Tauri frontend (localhost + tauri asset protocol)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────

app.include_router(zodiac.router, prefix="/api/zodiac", tags=["zodiac"])


# ── Core endpoints ───────────────────────────────────────────────

@app.get("/health")
async def health():
    """Sidecar health check — frontend polls this until ready."""
    return {"status": "ok", "service": "gaia-backend", "version": "0.1.0"}


@app.get("/api/state")
async def get_state():
    """Current GAIA engine state snapshot."""
    return {
        "soul_mirror": {"archetype": "seeker", "individuation_stage": 1},
        "shadow": {"flags": []},
        "attachment": {"style": "secure"},
        "coherence": 72,
        "solfeggio": {"frequency": 528, "chakra": "heart"},
    }


# ── Launch ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("GAIA_PORT", 8008))
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=port,
        log_level="info",
        reload=False,
    )

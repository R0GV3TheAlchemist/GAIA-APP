"""
GAIA Backend — FastAPI Entry Point
Runs on http://localhost:8008
Launched as a Tauri sidecar (gaia-backend.exe on Windows)
"""

import sys
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure repo root is on path when running frozen (PyInstaller)
if getattr(sys, 'frozen', False):
    ROOT = sys._MEIPASS
else:
    ROOT = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, ROOT)

from api.routers import zodiac

app = FastAPI(
    title="GAIA Backend",
    description="Sovereign AI Companion — Python Core",
    version="0.1.0",
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

# ── Routers ──────────────────────────────────────────────
app.include_router(zodiac.router, prefix="/api/zodiac", tags=["zodiac"])


# ── Core endpoints ───────────────────────────────────────
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


# ── Launch ───────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("GAIA_PORT", 8008))
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=port,
        log_level="info",
        reload=False,
    )

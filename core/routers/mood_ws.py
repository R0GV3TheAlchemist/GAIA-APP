"""
core/routers/mood_ws.py

WebSocket endpoint: ws://localhost:8008/ws/mood

Broadcasts a mood payload after every completed chat or query turn.
Up to MAX_SUBSCRIBERS concurrent connections are supported; oldest
connection is dropped when the limit is reached.

Payload schema
--------------
{
  "mood":       "calm" | "curious" | "alert" | "joyful" | "reflective",
  "sentiment":  float,   # -1.0 – 1.0
  "bond_depth": float,   # raw value from InferenceResponse
  "source":     str      # originating gaian slug
}

Canon Refs: C17, C44
"""

from __future__ import annotations

import asyncio
import json
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

MAX_SUBSCRIBERS = 32

# --- Pub / sub hub ----------------------------------------------------------

_queues: List[asyncio.Queue[str]] = []


def broadcast_mood(
    mood: str,
    sentiment: float,
    bond_depth: float = 0.0,
    source: str = "gaia",
) -> None:
    """
    Synchronous helper — called from chat router after turn completion.
    Enqueues the payload to every active WebSocket subscriber.
    """
    payload = json.dumps(
        {
            "mood": mood,
            "sentiment": round(sentiment, 4),
            "bond_depth": round(bond_depth, 4),
            "source": source,
        }
    )
    dead: list[asyncio.Queue[str]] = []
    for q in _queues:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        try:
            _queues.remove(q)
        except ValueError:
            pass


# --- mood derivation --------------------------------------------------------

def mood_from_bond(bond_depth: float, criticality: str | None = None) -> tuple[str, float]:
    """
    Return (mood_name, sentiment_float) from bond_depth + criticality.

    bond_depth scale (from attachment engine):
      0.0 – 0.2  shallow / new session
      0.2 – 0.5  building
      0.5 – 0.8  established
      0.8 – 1.0  deep bond

    criticality_state strings (from codex_stage_engine):
      DORMANT, LOW, NOMINAL, ELEVATED, EDGE, CRITICAL, HYPER
    """
    crit = (criticality or "").upper()

    if crit in ("CRITICAL", "EDGE"):
        return ("alert", -0.7)
    if crit == "HYPER":
        return ("joyful", 0.85)
    if crit == "LOW":
        return ("reflective", -0.15)

    # Bond-depth driven
    if bond_depth >= 0.75:
        return ("joyful", 0.75)
    if bond_depth >= 0.5:
        return ("curious", 0.35)
    if bond_depth >= 0.25:
        return ("calm", 0.05)
    return ("reflective", -0.1)


# --- WebSocket endpoint -----------------------------------------------------

@router.websocket("/ws/mood")
async def mood_websocket(ws: WebSocket) -> None:
    await ws.accept()

    if len(_queues) >= MAX_SUBSCRIBERS:
        # Drop the oldest subscriber to make room
        oldest = _queues.pop(0)
        oldest.put_nowait(json.dumps({"__close": True}))

    q: asyncio.Queue[str] = asyncio.Queue(maxsize=64)
    _queues.append(q)
    logger.debug(f"/ws/mood: new subscriber (total={len(_queues)})")

    try:
        while True:
            payload = await q.get()
            data = json.loads(payload)
            if data.get("__close"):
                await ws.close()
                break
            await ws.send_text(payload)
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        try:
            _queues.remove(q)
        except ValueError:
            pass
        logger.debug(f"/ws/mood: subscriber disconnected (total={len(_queues)})")

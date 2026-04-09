"""
GAIA Core API Server — FastAPI bridge between the Tauri UI and the Python constitutional core.

Exposes REST endpoints for:
  - Constitutional status
  - Canon loader (C-series documents, search, lazy hydration)
  - Memory governance (MemoryStore)
  - Consent lifecycle (ConsentLedger)
  - Action gating (ActionGate)
  - ATLAS Earth Intelligence (Google Earth Engine)
  - Query streaming (SSE — Perplexity-style streaming with inline canon citations)

Runs locally on http://127.0.0.1:8008 for desktop.
Deploy via Docker to Google Cloud Run for mobile/web.

Epistemic Status: ESTABLISHED
Canon Ref: C01 (Master), C15 (Runtime & Permissions), C17 (Memory & Identity),
           C21 (Interface & Shell Grammar)
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import CanonLoader, ActionGate, RiskTier, ConsentLedger, MemoryStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GAIA Core API",
    description="Constitutional AI governance layer for GAIA-APP",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------ #
#  Constitutional System Initialisation                                #
# ------------------------------------------------------------------ #

canon = CanonLoader()
try:
    canon.load()
except Exception as e:
    logger.warning(f"Canon load error (non-fatal during dev): {e}")

gate = ActionGate()
ledger = ConsentLedger()
memory = MemoryStore()


# ------------------------------------------------------------------ #
#  Pydantic Models                                                     #
# ------------------------------------------------------------------ #

class MemoryAddRequest(BaseModel):
    content: str
    source: str = "explicit"
    purposes: list = ["general"]
    confidence: float = 1.0

class ConsentGrantRequest(BaseModel):
    party_id: str
    purpose: str
    duration_days: int = 365

class ConsentRevokeRequest(BaseModel):
    party_id: str
    purpose: str

class ActionEvaluateRequest(BaseModel):
    action_type: str
    description: str
    tier: str = "yellow"
    payload: dict = {}

class QueryRequest(BaseModel):
    query: str
    max_canon_refs: int = 3
    sovereign_id: Optional[str] = None


# ------------------------------------------------------------------ #
#  Status                                                              #
# ------------------------------------------------------------------ #

@app.get("/status")
def status():
    """Constitutional health check. Used by the UI status bar."""
    return {
        "core": "active",
        "sovereignty": "enforced",
        "t1_floor": "held",
        "canon_status": canon.status,
        "canon_loaded": canon.is_loaded,
        "canon_doc_count": len(canon.list_documents()),
        "canon_docs": canon.list_documents(),
        "version": "0.2.0"
    }


# ------------------------------------------------------------------ #
#  Canon Endpoints                                                     #
# ------------------------------------------------------------------ #

@app.get("/canon/status")
def canon_status():
    """
    Canon health endpoint. Returns GREEN / YELLOW / RED.
    GREEN  = C00 + C01 loaded. Full constitutional floor held.
    YELLOW = Partially loaded or fetching.
    RED    = Constitutional floor missing. System cannot operate canonically.
    """
    return {
        "status": canon.status,
        "loaded_count": len(canon.list_documents()),
        "manifest_count": len(canon.list_manifest()),
        "floor_documents": ["00_Documentation_Index", "01_GAIA_Master_Document"],
        "message": {
            "green": "Constitutional floor held. Canon is active.",
            "yellow": "Canon loading or degraded. Some documents unavailable.",
            "red": "CONSTITUTIONAL FLOOR MISSING. System running without canon."
        }.get(canon.status, "Unknown")
    }

@app.get("/canon/list")
def canon_list():
    """List all loaded canon documents with their titles and sources."""
    docs = []
    for doc_id in canon.list_documents():
        doc = canon.get(doc_id)
        if doc:
            docs.append({
                "id": doc_id,
                "title": doc.get("title", doc_id),
                "source": doc.get("source", "unknown"),
                "loaded_at": doc.get("loaded_at"),
            })
    return {
        "count": len(docs),
        "documents": docs,
        "manifest_registry": canon.list_manifest()
    }

@app.get("/canon/get/{doc_id}")
def canon_get(doc_id: str):
    """
    Retrieve a specific canon document by ID.
    If not locally loaded, triggers a lazy remote fetch from the GAIA repo.
    """
    doc = canon.get(doc_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Canon document '{doc_id}' not found locally or remotely."
        )
    return doc

@app.get("/canon/search")
def canon_search(q: str, max_results: int = 5):
    """
    Full-text search across all loaded canon documents.
    Returns ranked results with excerpts for inline citation.
    """
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters.")
    results = canon.search(q, max_results=max_results)
    return {
        "query": q,
        "result_count": len(results),
        "results": results
    }


# ------------------------------------------------------------------ #
#  Query Streaming (Perplexity-style SSE)                              #
# ------------------------------------------------------------------ #

async def _stream_query_response(
    query: str,
    canon_refs: list[dict],
    sovereign_id: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Generate a streaming Server-Sent Events response to a GAIA query.

    Format (each event is one SSE message):
      event: token         — a single word/token of the response text
      event: citation      — a canon citation card {doc_id, title, excerpt}
      event: done          — signals end of stream

    The response is canon-grounded: it opens with canon references,
    streams the answer token-by-token, then closes with a follow-up
    suggestion (ActionGate pattern).
    """

    def sse(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    # 1. Emit canon citations first (like Perplexity sources panel)
    for ref in canon_refs:
        yield sse("citation", {
            "doc_id": ref["doc_id"],
            "title": ref["title"],
            "excerpt": ref["excerpt"][:200],
        })
        await asyncio.sleep(0.05)

    # 2. Build a grounded response from canon search results
    if canon_refs:
        canon_context = "\n\n".join(
            f"[{r['doc_id']}]: {r['excerpt']}" for r in canon_refs[:3]
        )
        preamble = (
            f"Based on the GAIA constitutional canon, here is what I found regarding "
            f"'{query}':\n\n"
        )
    else:
        canon_context = ""
        preamble = (
            f"The canon does not yet have a direct entry for '{query}'. "
            f"Here is what the constitutional framework implies:\n\n"
        )

    # 3. Stream preamble token by token
    for word in preamble.split():
        yield sse("token", {"text": word + " "})
        await asyncio.sleep(0.04)

    # 4. Stream canon excerpt content
    if canon_context:
        for word in canon_context.split():
            yield sse("token", {"text": word + " "})
            await asyncio.sleep(0.03)

    # 5. Emit suggested follow-up actions (ActionGate pattern)
    await asyncio.sleep(0.1)
    suggestions = _generate_suggestions(query)
    yield sse("suggestions", {"items": suggestions})

    # 6. Done
    yield sse("done", {
        "canon_status": canon.status,
        "docs_searched": len(canon.list_documents()),
        "refs_found": len(canon_refs),
        "timestamp": time.time()
    })


def _generate_suggestions(query: str) -> list[str]:
    """Generate 3 contextual follow-up question suggestions based on the query."""
    q = query.lower()
    if any(w in q for w in ["gaian", "twin", "human"]):
        return [
            "What are the 5 layers of a Gaian digital twin?",
            "How does the consent ledger protect the human sovereign?",
            "What is the difference between a Gaian and a GAIA node?"
        ]
    elif any(w in q for w in ["canon", "c01", "c00", "document"]):
        return [
            "Show me the full C-series document registry",
            "What is the GAIA Equation (D00)?",
            "Which canon document governs permissions?"
        ]
    elif any(w in q for w in ["atlas", "earth", "temperature", "ndvi"]):
        return [
            "What is the current air quality in San Antonio?",
            "Show me NDVI vegetation data for my location",
            "How does ATLAS connect to the GAIANS network?"
        ]
    else:
        return [
            "What is GAIA's constitutional foundation?",
            "How does the ActionGate protect sovereignty?",
            "What canon documents are loaded right now?"
        ]


@app.post("/query/stream")
async def query_stream(req: QueryRequest):
    """
    Perplexity-style streaming query endpoint.

    1. Searches the loaded canon for relevant documents.
    2. Streams the response as Server-Sent Events (SSE).
    3. Each SSE message is either a 'token', 'citation', 'suggestions', or 'done' event.

    The UI should:
      - Open an EventSource to this endpoint
      - Append 'token' events to the response text in real time
      - Render 'citation' events as inline source cards (like Perplexity sources)
      - Show 'suggestions' as follow-up question chips below the response
      - Close the stream on 'done'

    Canon Ref: C21 (Interface & Shell Grammar)
    """
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Search canon for grounding references
    canon_refs = canon.search(query, max_results=req.max_canon_refs)

    return StreamingResponse(
        _stream_query_response(query, canon_refs, req.sovereign_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",       # disable nginx buffering
            "X-Canon-Status": canon.status,
        }
    )


# ------------------------------------------------------------------ #
#  Memory                                                              #
# ------------------------------------------------------------------ #

@app.post("/memory/add")
def add_memory(req: MemoryAddRequest):
    """Add a governed memory entry."""
    entry = memory.add(req.content, req.source, req.purposes, req.confidence)
    return entry.to_dict()

@app.get("/memory/list")
def list_memory():
    """List all non-deleted memory entries (user visibility surface)."""
    return memory.list_all()

@app.put("/memory/{memory_id}")
def edit_memory(memory_id: str, new_content: str):
    """Edit a memory entry."""
    success = memory.edit(memory_id, new_content)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found or frozen")
    return {"edited": True, "memory_id": memory_id}

@app.delete("/memory/{memory_id}")
def delete_memory(memory_id: str):
    """Soft-delete a memory entry."""
    success = memory.delete(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"deleted": True, "memory_id": memory_id}

@app.get("/memory/audit")
def memory_audit():
    """Return the full memory audit log."""
    return memory.get_audit_log()


# ------------------------------------------------------------------ #
#  Consent                                                             #
# ------------------------------------------------------------------ #

@app.post("/consent/grant")
def grant_consent(req: ConsentGrantRequest):
    """Grant time-bound consent for a specific purpose."""
    record = ledger.grant(req.party_id, req.purpose, req.duration_days)
    return record.to_dict()

@app.post("/consent/revoke")
def revoke_consent(req: ConsentRevokeRequest):
    """Revoke consent. Always succeeds for the human sovereign."""
    revoked = ledger.revoke(req.party_id, req.purpose)
    return {"revoked": revoked, "party_id": req.party_id, "purpose": req.purpose}

@app.get("/consent/active/{party_id}")
def active_consents(party_id: str):
    """Return all active consents for a party."""
    return ledger.get_active_consents(party_id)

@app.get("/consent/ledger")
def full_ledger():
    """Return the full immutable consent ledger."""
    return ledger.get_ledger()


# ------------------------------------------------------------------ #
#  Action Gate                                                         #
# ------------------------------------------------------------------ #

@app.post("/action/evaluate")
def evaluate_action(req: ActionEvaluateRequest):
    """Evaluate an action through the constitutional risk-tier gate."""
    tier_map = {
        "green": RiskTier.GREEN,
        "yellow": RiskTier.YELLOW,
        "red": RiskTier.RED
    }
    result = gate.evaluate({
        "type": req.action_type,
        "description": req.description,
        "tier": tier_map.get(req.tier, RiskTier.YELLOW),
        "payload": req.payload
    })
    return {
        **result,
        "tier": result["tier"].value if hasattr(result.get("tier"), 'value') else req.tier
    }

@app.get("/action/audit")
def action_audit():
    """Return the full action gate audit log."""
    return gate.get_audit_log()


# ------------------------------------------------------------------ #
#  ATLAS: Earth Intelligence                                           #
# ------------------------------------------------------------------ #

@app.get("/atlas/status")
def atlas_status():
    """Check if Earth Engine is authenticated and available."""
    try:
        import ee
        ee.Initialize()
        return {"atlas": "connected", "source": "Google Earth Engine"}
    except Exception as e:
        return {"atlas": "unavailable", "reason": str(e), "action": "Run: earthengine authenticate"}

@app.get("/atlas/temperature")
def get_surface_temp(lat: float = 29.4241, lon: float = -98.4936):
    """Get MODIS land surface temperature. Defaults to San Antonio, TX."""
    try:
        import ee
        ee.Initialize()
        point = ee.Geometry.Point([lon, lat])
        dataset = (ee.ImageCollection('MODIS/061/MOD11A1')
                   .filterDate('2026-01-01', '2026-04-09')
                   .select('LST_Day_1km'))
        lst = dataset.mean()
        temp_k = lst.sample(point, 1000).first().get('LST_Day_1km').getInfo()
        temp_c = round((temp_k * 0.02) - 273.15, 2) if temp_k else None
        return {"lat": lat, "lon": lon, "temperature_celsius": temp_c,
                "source": "MODIS/061/MOD11A1", "layer": "ATLAS"}
    except ImportError:
        raise HTTPException(status_code=503, detail="pip install earthengine-api")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"ATLAS unavailable: {str(e)}")

@app.get("/atlas/ndvi")
def get_vegetation(lat: float = 29.4241, lon: float = -98.4936):
    """Get MODIS NDVI vegetation index. Defaults to San Antonio, TX."""
    try:
        import ee
        ee.Initialize()
        point = ee.Geometry.Point([lon, lat])
        dataset = (ee.ImageCollection('MODIS/061/MOD13A2')
                   .filterDate('2026-01-01', '2026-04-09')
                   .select('NDVI'))
        ndvi_val = dataset.mean().sample(point, 1000).first().get('NDVI').getInfo()
        return {"lat": lat, "lon": lon, "ndvi": ndvi_val,
                "ndvi_scaled": round(ndvi_val * 0.0001, 4) if ndvi_val else None,
                "source": "MODIS/061/MOD13A2", "layer": "ATLAS"}
    except ImportError:
        raise HTTPException(status_code=503, detail="pip install earthengine-api")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"ATLAS unavailable: {str(e)}")

@app.get("/atlas/air-quality")
def get_air_quality(lat: float = 29.4241, lon: float = -98.4936):
    """Get Sentinel-5P NO2 air quality data. Defaults to San Antonio, TX."""
    try:
        import ee
        ee.Initialize()
        point = ee.Geometry.Point([lon, lat])
        dataset = (ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_NO2')
                   .filterDate('2026-01-01', '2026-04-09')
                   .select('NO2_column_number_density'))
        no2 = dataset.mean().sample(point, 1000).first().get('NO2_column_number_density').getInfo()
        return {"lat": lat, "lon": lon, "no2_mol_per_m2": no2,
                "source": "Copernicus/Sentinel-5P", "layer": "ATLAS"}
    except ImportError:
        raise HTTPException(status_code=503, detail="pip install earthengine-api")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"ATLAS unavailable: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8008, log_level="info")

"""
GAIA Core API Server — FastAPI bridge between the Tauri UI and the Python constitutional core.

Exposes REST endpoints for:
  - Constitutional status
  - Memory governance (MemoryStore)
  - Consent lifecycle (ConsentLedger)
  - Action gating (ActionGate)
  - ATLAS Earth Intelligence (Google Earth Engine)

Runs locally on http://127.0.0.1:8008 for desktop.
Deploy via Docker to Google Cloud Run for mobile/web.

Epistemic Status: ESTABLISHED
Canon Ref: Doc 21 (Sovereignty), Doc 34 (Identity), Doc 35 (Security)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Ensure core/ is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import CanonLoader, ActionGate, RiskTier, ConsentLedger, MemoryStore

app = FastAPI(
    title="GAIA Core API",
    description="Constitutional AI governance layer for GAIA-APP",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Initialize constitutional systems ---
canon = CanonLoader()
try:
    canon.load()
except Exception:
    pass  # Canon directory may be empty during development

gate = ActionGate()
ledger = ConsentLedger()
memory = MemoryStore()


# --- Pydantic models ---
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

class AtlasQueryRequest(BaseModel):
    lat: float = 29.4241
    lon: float = -98.4936


# --- Status ---
@app.get("/status")
def status():
    """Constitutional health check. Used by the UI status bar."""
    return {
        "core": "active",
        "sovereignty": "enforced",
        "t1_floor": "held",
        "canon_loaded": getattr(canon, 'is_loaded', False),
        "canon_docs": canon.list_documents() if getattr(canon, 'is_loaded', False) else [],
        "version": "0.1.0"
    }


# --- Memory ---
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


# --- Consent ---
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


# --- Action Gate ---
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


# --- ATLAS: Earth Intelligence ---
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
    """Get MODIS land surface temperature for a coordinate. Defaults to San Antonio, TX."""
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
        return {
            "lat": lat, "lon": lon,
            "temperature_celsius": temp_c,
            "source": "MODIS/061/MOD11A1",
            "layer": "ATLAS"
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Earth Engine not installed. Run: pip install earthengine-api")
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
        return {
            "lat": lat, "lon": lon,
            "ndvi": ndvi_val,
            "ndvi_scaled": round(ndvi_val * 0.0001, 4) if ndvi_val else None,
            "source": "MODIS/061/MOD13A2",
            "layer": "ATLAS"
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Earth Engine not installed. Run: pip install earthengine-api")
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
        return {
            "lat": lat, "lon": lon,
            "no2_mol_per_m2": no2,
            "source": "Copernicus/Sentinel-5P",
            "layer": "ATLAS"
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Earth Engine not installed. Run: pip install earthengine-api")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"ATLAS unavailable: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8008, log_level="info")

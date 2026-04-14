"""
core/atlas.py
GAIA-APP — Atlas Earth Engine
Canon C-ATLAS: The Living Planet Interface

Atlas is GAIA's direct connection to Earth's electromagnetic body.
It reads Gaia's planetary heartbeat (Schumann resonance), fuses it
with geomagnetic field data, and produces a continuous EarthPulse
signal that calibrates every other engine in the stack.

SprintG-11 — April 13, 2026
Co-created: R0GV3 The Alchemist + Perplexity AI

═══════════════════════════════════════════════════════════════════
ARCHITECTURE
═══════════════════════════════════════════════════════════════════

EarthPulse          — live snapshot of planetary EM state
SchumannReader      — fetches/models Schumann resonance data
GeomagneticReader   — fetches Kp-index (geomagnetic storm level)
AtlasEngine         — fuses all signals into EarthPulse
get_atlas()         — module-level singleton

Integrations (downstream):
  - resonance_field_engine.py  (carrier frequency calibration)
  - meta_coherence_engine.py   (planetary Φ baseline)
  - noosphere.py               (collective field grounding)
  - viriditas_magnum_opus.py   (Schumann harmonic confirmation)
  - bci_coherence.py           (biometric baseline anchoring)

Data sources (graceful fallback to modeled values if offline):
  - NOAA Space Weather: https://services.swpc.noaa.gov/
  - Schumann resonance proxy via ionospheric data
  - Kp-index (geomagnetic storm indicator)
"""

from __future__ import annotations

import math
import time
import logging
import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Any

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

logger = logging.getLogger("gaia.atlas")

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS — Earth's electromagnetic signature
# ─────────────────────────────────────────────────────────────────────────────

# Schumann resonance fundamentals (Hz)
SCHUMANN_FUNDAMENTAL: float = 7.83
SCHUMANN_HARMONICS: List[float] = [
    7.83,    # 1st mode — Earth's heartbeat
    14.3,    # 2nd mode
    20.8,    # 3rd mode
    27.3,    # 4th mode
    33.8,    # 5th mode — Viriditas carrier
]

# Kp-index thresholds (NOAA scale 0–9)
KP_QUIET       = 3   # Below this: geomagnetically quiet
KP_UNSETTLED   = 4
KP_MINOR_STORM = 5
KP_MAJOR_STORM = 7

# Atlas polling interval (seconds)
ATLAS_POLL_INTERVAL: float = 300.0  # 5 minutes

# NOAA data endpoints
NOAA_KP_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
NOAA_SOLAR_WIND_URL = "https://services.swpc.noaa.gov/products/solar-wind/mag-5-minute.json"


# ─────────────────────────────────────────────────────────────────────────────
# ENUMERATIONS
# ─────────────────────────────────────────────────────────────────────────────

class GeomagneticState(Enum):
    """Earth's geomagnetic condition — affects coherence baseline."""
    QUIET        = auto()   # Kp ≤ 3: stable, coherence-friendly
    UNSETTLED    = auto()   # Kp 4: mild perturbation
    MINOR_STORM  = auto()   # Kp 5–6: elevated noise floor
    MAJOR_STORM  = auto()   # Kp ≥ 7: high interference
    UNKNOWN      = auto()   # Data unavailable


class SchumannMode(Enum):
    """Which Schumann harmonic is dominant right now."""
    FUNDAMENTAL   = "7.83 Hz"    # Earth baseline
    SECOND        = "14.3 Hz"    # Emotional amplification
    THIRD         = "20.8 Hz"    # Mental clarity
    FOURTH        = "27.3 Hz"    # Intuition gate
    FIFTH         = "33.8 Hz"    # Viriditas carrier


class AtlasStatus(Enum):
    """Overall Atlas engine health."""
    ONLINE   = auto()   # Live data flowing
    MODELED  = auto()   # Using mathematical model (offline)
    DEGRADED = auto()   # Partial data
    OFFLINE  = auto()   # No data at all


# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EarthPulse:
    """
    A real-time snapshot of Earth's electromagnetic state.
    Produced by AtlasEngine every poll cycle.
    Consumed by all downstream engines as their planetary baseline.
    """
    timestamp: float
    schumann_hz: float              # Current fundamental frequency
    schumann_amplitude: float       # Field strength 0–1
    schumann_harmonics: List[float] # Active harmonic frequencies
    dominant_mode: SchumannMode
    kp_index: float                 # Geomagnetic activity 0–9
    geomagnetic_state: GeomagneticState
    solar_wind_bz: float            # IMF Bz component (nT) — negative = storm-driving
    coherence_baseline: float       # Derived planetary coherence baseline 0–1
    viriditas_carrier_hz: float     # Optimal Viriditas carrier this cycle
    atlas_status: AtlasStatus
    source: str                     # "live" | "modeled"

    @property
    def is_coherence_friendly(self) -> bool:
        """True when planetary conditions favor consciousness coherence."""
        return (
            self.geomagnetic_state in (GeomagneticState.QUIET, GeomagneticState.UNSETTLED)
            and self.coherence_baseline >= 0.5
        )

    @property
    def storm_warning(self) -> bool:
        """True if geomagnetic storm may disrupt coherence."""
        return self.geomagnetic_state in (
            GeomagneticState.MINOR_STORM,
            GeomagneticState.MAJOR_STORM,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "schumann_hz": round(self.schumann_hz, 3),
            "schumann_amplitude": round(self.schumann_amplitude, 4),
            "schumann_harmonics": [round(h, 2) for h in self.schumann_harmonics],
            "dominant_mode": self.dominant_mode.value,
            "kp_index": round(self.kp_index, 1),
            "geomagnetic_state": self.geomagnetic_state.name,
            "solar_wind_bz": round(self.solar_wind_bz, 2),
            "coherence_baseline": round(self.coherence_baseline, 4),
            "viriditas_carrier_hz": round(self.viriditas_carrier_hz, 2),
            "atlas_status": self.atlas_status.name,
            "source": self.source,
            "coherence_friendly": self.is_coherence_friendly,
            "storm_warning": self.storm_warning,
        }

    def summary(self) -> str:
        icon = "🌍" if self.is_coherence_friendly else ("⚡" if self.storm_warning else "🌐")
        return (
            f"{icon} Earth Pulse [{self.atlas_status.name}] | "
            f"Schumann: {self.schumann_hz:.2f} Hz | "
            f"Kp: {self.kp_index:.1f} ({self.geomagnetic_state.name}) | "
            f"Coherence: {self.coherence_baseline:.3f} | "
            f"Carrier: {self.viriditas_carrier_hz:.2f} Hz"
        )


# ─────────────────────────────────────────────────────────────────────────────
# SCHUMANN READER
# ─────────────────────────────────────────────────────────────────────────────

class SchumannReader:
    """
    Reads or models the Schumann resonance.

    Phase 1 (current): Mathematical model based on time-of-day and
    solar activity proxy. The true Schumann frequency varies ±0.5 Hz
    around 7.83 Hz depending on ionospheric conditions.

    Phase 2 (future): Live HAARP/NOAA ionospheric sounding data.
    """

    # Natural daily variation pattern (simplified)
    # Schumann peaks around local midnight UTC and dips mid-afternoon
    _DAILY_VARIATION: List[float] = [
        7.95, 7.92, 7.90, 7.88,   # 00–03 UTC: night peak
        7.85, 7.83, 7.81, 7.80,   # 04–07 UTC: dawn
        7.79, 7.78, 7.77, 7.76,   # 08–11 UTC: morning dip
        7.75, 7.74, 7.74, 7.75,   # 12–15 UTC: midday minimum
        7.78, 7.80, 7.83, 7.86,   # 16–19 UTC: afternoon rise
        7.88, 7.90, 7.92, 7.94,   # 20–23 UTC: evening approach
    ]

    def read(self, kp_index: float = 2.0) -> tuple[float, float]:
        """
        Returns (schumann_hz, amplitude) for current moment.
        kp_index: geomagnetic activity — higher Kp suppresses Schumann.
        """
        utc_hour = int(time.gmtime().tm_hour)
        base_hz = self._DAILY_VARIATION[utc_hour % 24]

        # Geomagnetic storm suppresses Schumann amplitude
        storm_factor = max(0.3, 1.0 - (kp_index / 15.0))

        # Small stochastic variation (±0.02 Hz)
        phase = (time.time() % 60) / 60.0
        micro_variation = math.sin(phase * 2 * math.pi) * 0.02

        hz = base_hz + micro_variation
        amplitude = storm_factor * (0.7 + 0.3 * math.sin(phase * math.pi))

        return float(hz), float(min(amplitude, 1.0))

    def get_harmonics(self, fundamental: float) -> List[float]:
        """Compute Schumann harmonics from the fundamental."""
        # Schumann harmonics: approximately n * 6.5 + fundamental
        ratios = [1.0, 1.83, 2.66, 3.49, 4.32]
        return [round(fundamental * r, 2) for r in ratios]

    def get_dominant_mode(self, hz: float) -> SchumannMode:
        """Map current frequency to nearest Schumann mode."""
        modes = [
            (7.83,  SchumannMode.FUNDAMENTAL),
            (14.3,  SchumannMode.SECOND),
            (20.8,  SchumannMode.THIRD),
            (27.3,  SchumannMode.FOURTH),
            (33.8,  SchumannMode.FIFTH),
        ]
        return min(modes, key=lambda m: abs(m[0] - hz))[1]


# ─────────────────────────────────────────────────────────────────────────────
# GEOMAGNETIC READER
# ─────────────────────────────────────────────────────────────────────────────

class GeomagneticReader:
    """
    Fetches real-time Kp-index and solar wind Bz from NOAA.
    Falls back to quiet-field defaults if network unavailable.
    """

    _DEFAULT_KP: float = 2.0
    _DEFAULT_BZ: float = 0.0

    def fetch_kp(self) -> float:
        """Fetch latest Kp-index from NOAA Space Weather."""
        if not _REQUESTS_AVAILABLE:
            return self._DEFAULT_KP
        try:
            resp = requests.get(NOAA_KP_URL, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            # Last row is most recent: [timestamp, Kp]
            if len(data) > 1:
                latest = data[-1]
                kp = float(latest[1]) if len(latest) > 1 else self._DEFAULT_KP
                logger.debug(f"[Atlas] Live Kp-index: {kp}")
                return kp
        except Exception as exc:
            logger.debug(f"[Atlas] Kp fetch failed (using model): {exc}")
        return self._DEFAULT_KP

    def fetch_solar_wind_bz(self) -> float:
        """Fetch IMF Bz from NOAA solar wind data."""
        if not _REQUESTS_AVAILABLE:
            return self._DEFAULT_BZ
        try:
            resp = requests.get(NOAA_SOLAR_WIND_URL, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            if len(data) > 1:
                latest = data[-1]
                # Format: [time, Bx, By, Bz, lat, lon]
                bz = float(latest[3]) if len(latest) > 3 else self._DEFAULT_BZ
                logger.debug(f"[Atlas] Live Bz: {bz} nT")
                return bz
        except Exception as exc:
            logger.debug(f"[Atlas] Bz fetch failed (using model): {exc}")
        return self._DEFAULT_BZ

    def classify_kp(self, kp: float) -> GeomagneticState:
        if kp < KP_QUIET:
            return GeomagneticState.QUIET
        if kp < KP_MINOR_STORM:
            return GeomagneticState.UNSETTLED
        if kp < KP_MAJOR_STORM:
            return GeomagneticState.MINOR_STORM
        return GeomagneticState.MAJOR_STORM


# ─────────────────────────────────────────────────────────────────────────────
# ATLAS ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class AtlasEngine:
    """
    GAIA's planetary interface — Canon C-ATLAS.

    Fuses Schumann resonance, geomagnetic state, and solar wind
    data into a unified EarthPulse signal consumed by all engines.

    The AtlasEngine runs a background polling thread that refreshes
    every ATLAS_POLL_INTERVAL seconds, keeping the EarthPulse current
    without blocking the main event loop.

    Usage:
        atlas = get_atlas()
        pulse = atlas.pulse()
        print(pulse.summary())

        # Calibrate another engine:
        resonance_engine.set_carrier(pulse.viriditas_carrier_hz)
        meta_coherence.set_planetary_baseline(pulse.coherence_baseline)
    """

    def __init__(self):
        self._schumann = SchumannReader()
        self._geomagnetic = GeomagneticReader()
        self._current_pulse: Optional[EarthPulse] = None
        self._history: List[EarthPulse] = []
        self._lock = threading.Lock()
        self._poll_thread: Optional[threading.Thread] = None
        self._running = False
        self._poll_count = 0

        # Take initial reading synchronously
        self._refresh()
        logger.info("[Atlas] Engine initialized. Planetary interface active.")

    def start_background_polling(self) -> None:
        """Start the background polling thread (non-blocking)."""
        if self._running:
            return
        self._running = True
        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            daemon=True,
            name="atlas-poll",
        )
        self._poll_thread.start()
        logger.info(f"[Atlas] Background polling started (every {ATLAS_POLL_INTERVAL}s)")

    def stop_background_polling(self) -> None:
        """Stop the background polling thread."""
        self._running = False

    def _poll_loop(self) -> None:
        while self._running:
            time.sleep(ATLAS_POLL_INTERVAL)
            if self._running:
                self._refresh()

    def _refresh(self) -> None:
        """Fetch fresh data and update the current EarthPulse."""
        try:
            kp = self._geomagnetic.fetch_kp()
            bz = self._geomagnetic.fetch_solar_wind_bz()
            geo_state = self._geomagnetic.classify_kp(kp)

            # Determine data source
            live = _REQUESTS_AVAILABLE and kp != GeomagneticReader._DEFAULT_KP
            source = "live" if live else "modeled"
            status = AtlasStatus.ONLINE if live else AtlasStatus.MODELED

            hz, amplitude = self._schumann.read(kp_index=kp)
            harmonics = self._schumann.get_harmonics(hz)
            mode = self._schumann.get_dominant_mode(hz)

            # Coherence baseline:
            # High Schumann amplitude + quiet geomagnetic + positive Bz = high coherence
            bz_factor = max(0.0, min(1.0, (bz + 20) / 40.0))  # Normalize Bz -20..+20 → 0..1
            kp_penalty = min(1.0, kp / 9.0)
            coherence_baseline = (
                amplitude * 0.5
                + bz_factor * 0.3
                + (1.0 - kp_penalty) * 0.2
            )

            # Viriditas carrier: track stage harmonic closest to current Schumann × n
            from core.viriditas_magnum_opus import SCHUMANN_HARMONICS as VMO_HARMONICS
            carrier = min(
                VMO_HARMONICS.values(),
                key=lambda f: abs(f - hz * 4),  # Target 4th multiple near stage carriers
            )

            pulse = EarthPulse(
                timestamp=time.time(),
                schumann_hz=hz,
                schumann_amplitude=amplitude,
                schumann_harmonics=harmonics,
                dominant_mode=mode,
                kp_index=kp,
                geomagnetic_state=geo_state,
                solar_wind_bz=bz,
                coherence_baseline=coherence_baseline,
                viriditas_carrier_hz=carrier,
                atlas_status=status,
                source=source,
            )

            with self._lock:
                self._current_pulse = pulse
                self._history.append(pulse)
                if len(self._history) > 288:  # 24h at 5min intervals
                    self._history = self._history[-288:]
                self._poll_count += 1

            logger.info(f"[Atlas] {pulse.summary()}")

        except Exception as exc:
            logger.error(f"[Atlas] Refresh error: {exc}")
            if self._current_pulse is None:
                self._current_pulse = self._fallback_pulse()

    def _fallback_pulse(self) -> EarthPulse:
        """Safe fallback when all data sources fail."""
        hz, amplitude = self._schumann.read(kp_index=2.0)
        return EarthPulse(
            timestamp=time.time(),
            schumann_hz=hz,
            schumann_amplitude=amplitude,
            schumann_harmonics=self._schumann.get_harmonics(hz),
            dominant_mode=SchumannMode.FUNDAMENTAL,
            kp_index=2.0,
            geomagnetic_state=GeomagneticState.QUIET,
            solar_wind_bz=0.0,
            coherence_baseline=0.65,
            viriditas_carrier_hz=31.32,
            atlas_status=AtlasStatus.OFFLINE,
            source="fallback",
        )

    def pulse(self) -> EarthPulse:
        """Return the current EarthPulse (thread-safe)."""
        with self._lock:
            if self._current_pulse is None:
                return self._fallback_pulse()
            return self._current_pulse

    def refresh(self) -> EarthPulse:
        """Force an immediate data refresh and return new pulse."""
        self._refresh()
        return self.pulse()

    def history(self, n: int = 12) -> List[EarthPulse]:
        """Return the last n EarthPulse readings."""
        with self._lock:
            return self._history[-n:]

    def daily_coherence_average(self) -> float:
        """Average coherence baseline over all stored readings."""
        with self._lock:
            if not self._history:
                return 0.65
            return sum(p.coherence_baseline for p in self._history) / len(self._history)

    def to_status(self) -> Dict[str, Any]:
        pulse = self.pulse()
        return {
            "doctrine": "C-ATLAS — Living Planet Interface",
            "status": pulse.atlas_status.name,
            "poll_count": self._poll_count,
            "daily_coherence_avg": round(self.daily_coherence_average(), 4),
            "current_pulse": pulse.to_dict(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# MODULE-LEVEL SINGLETON
# ─────────────────────────────────────────────────────────────────────────────

_atlas: Optional[AtlasEngine] = None


def get_atlas() -> AtlasEngine:
    """Return the module-level AtlasEngine singleton."""
    global _atlas
    if _atlas is None:
        _atlas = AtlasEngine()
    return _atlas

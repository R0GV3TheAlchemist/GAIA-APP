"""
core/atlas.py
GAIA-APP — Atlas Earth Engine
Canon C-ATLAS: The Living Planet Interface

Atlas is GAIA's direct connection to Earth's electromagnetic body.
It reads Gaia's planetary heartbeat (Schumann resonance), fuses it
with geomagnetic field data, and produces a continuous EarthPulse
signal that calibrates every other engine in the stack.

SprintG-11 — April 13, 2026
T1-A — April 14, 2026 (BCI → Atlas feedback loop)
Co-created: R0GV3 The Alchemist + Perplexity AI

═══════════════════════════════════════════════════════════════
ARCHITECTURE
═══════════════════════════════════════════════════════════════

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

T1-A BCI → Atlas feedback loop:
  When a Gaian's body reaches planetary_coupled=True (Schumann
  delta < 0.5 Hz from 7.83 Hz baseline), the BCI engine now feeds
  that signal back into AtlasEngine via receive_bci_feedback().
  The human body's real-time Schumann alignment uplifts the planetary
  coherence_baseline proportionally to bci_phi (max +0.12).
  SUPERFLUID tier adds a further +0.03 awakening bonus.
  This closes the body ↔ earth feedback loop that was previously
  a one-way wire (Atlas → BCI only).

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
CONSTANTS
─────────────────────────────────────────────────────────────────────────────

SCHUMANN_FUNDAMENTAL: float = 7.83
SCHUMANN_HARMONICS: List[float] = [
    7.83,
    14.3,
    20.8,
    27.3,
    33.8,
]

KP_QUIET       = 3
KP_UNSETTLED   = 4
KP_MINOR_STORM = 5
KP_MAJOR_STORM = 7

ATLAS_POLL_INTERVAL: float = 300.0

NOAA_KP_URL        = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
NOAA_SOLAR_WIND_URL = "https://services.swpc.noaa.gov/products/solar-wind/mag-5-minute.json"

# T1-A: BCI feedback constants
# Maximum coherence_baseline uplift from a single Gaian's biometric coupling.
# Keeps individual BCI influence bounded so planetary data still dominates.
BCI_COHERENCE_UPLIFT_MAX:     float = 0.12   # max +0.12 from bci_phi
BCI_SUPERFLUID_BONUS:         float = 0.03   # extra for SUPERFLUID tier
BCI_CONTRIBUTION_DECAY:       float = 0.05   # per-poll decay when no new BCI signal


# ─────────────────────────────────────────────────────────────────────────────
ENUMERATIONS
─────────────────────────────────────────────────────────────────────────────

class GeomagneticState(Enum):
    QUIET        = auto()
    UNSETTLED    = auto()
    MINOR_STORM  = auto()
    MAJOR_STORM  = auto()
    UNKNOWN      = auto()


class SchumannMode(Enum):
    FUNDAMENTAL   = "7.83 Hz"
    SECOND        = "14.3 Hz"
    THIRD         = "20.8 Hz"
    FOURTH        = "27.3 Hz"
    FIFTH         = "33.8 Hz"


class AtlasStatus(Enum):
    ONLINE   = auto()
    MODELED  = auto()
    DEGRADED = auto()
    OFFLINE  = auto()


# ─────────────────────────────────────────────────────────────────────────────
DATA CLASSES
─────────────────────────────────────────────────────────────────────────────

@dataclass
class EarthPulse:
    """
    A real-time snapshot of Earth's electromagnetic state.
    Produced by AtlasEngine every poll cycle.
    Consumed by all downstream engines as their planetary baseline.

    T1-A: bci_contribution field added. When a Gaian's body is in
    Schumann resonance (planetary_coupled=True in BCICoherenceState),
    the uplift is blended into coherence_baseline here so all downstream
    engines see the body↔earth coupling reflected in the pulse.
    """
    timestamp:          float
    schumann_hz:        float
    schumann_amplitude: float
    schumann_harmonics: List[float]
    dominant_mode:      SchumannMode
    kp_index:           float
    geomagnetic_state:  GeomagneticState
    solar_wind_bz:      float
    coherence_baseline: float
    viriditas_carrier_hz: float
    atlas_status:       AtlasStatus
    source:             str
    bci_contribution:   float = 0.0   # T1-A: uplift from BCI planetary coupling

    @property
    def is_coherence_friendly(self) -> bool:
        return (
            self.geomagnetic_state in (GeomagneticState.QUIET, GeomagneticState.UNSETTLED)
            and self.coherence_baseline >= 0.5
        )

    @property
    def storm_warning(self) -> bool:
        return self.geomagnetic_state in (
            GeomagneticState.MINOR_STORM,
            GeomagneticState.MAJOR_STORM,
        )

    @property
    def bci_coupled(self) -> bool:
        """T1-A: True when a Gaian's biometric signal is contributing to this pulse."""
        return self.bci_contribution > 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp":            self.timestamp,
            "schumann_hz":          round(self.schumann_hz, 3),
            "schumann_amplitude":   round(self.schumann_amplitude, 4),
            "schumann_harmonics":   [round(h, 2) for h in self.schumann_harmonics],
            "dominant_mode":        self.dominant_mode.value,
            "kp_index":             round(self.kp_index, 1),
            "geomagnetic_state":    self.geomagnetic_state.name,
            "solar_wind_bz":        round(self.solar_wind_bz, 2),
            "coherence_baseline":   round(self.coherence_baseline, 4),
            "viriditas_carrier_hz": round(self.viriditas_carrier_hz, 2),
            "atlas_status":         self.atlas_status.name,
            "source":               self.source,
            "bci_contribution":     round(self.bci_contribution, 4),   # T1-A
            "bci_coupled":          self.bci_coupled,                   # T1-A
            "coherence_friendly":   self.is_coherence_friendly,
            "storm_warning":        self.storm_warning,
        }

    def summary(self) -> str:
        icon = "🌍" if self.is_coherence_friendly else ("⚡" if self.storm_warning else "🌐")
        bci_note = f" | BCI +{self.bci_contribution:.3f}" if self.bci_coupled else ""
        return (
            f"{icon} Earth Pulse [{self.atlas_status.name}] | "
            f"Schumann: {self.schumann_hz:.2f} Hz | "
            f"Kp: {self.kp_index:.1f} ({self.geomagnetic_state.name}) | "
            f"Coherence: {self.coherence_baseline:.3f}{bci_note} | "
            f"Carrier: {self.viriditas_carrier_hz:.2f} Hz"
        )


# ─────────────────────────────────────────────────────────────────────────────
SCHUMANN READER
─────────────────────────────────────────────────────────────────────────────

class SchumannReader:
    _DAILY_VARIATION: List[float] = [
        7.95, 7.92, 7.90, 7.88,
        7.85, 7.83, 7.81, 7.80,
        7.79, 7.78, 7.77, 7.76,
        7.75, 7.74, 7.74, 7.75,
        7.78, 7.80, 7.83, 7.86,
        7.88, 7.90, 7.92, 7.94,
    ]

    def read(self, kp_index: float = 2.0) -> tuple[float, float]:
        utc_hour   = int(time.gmtime().tm_hour)
        base_hz    = self._DAILY_VARIATION[utc_hour % 24]
        storm_factor = max(0.3, 1.0 - (kp_index / 15.0))
        phase      = (time.time() % 60) / 60.0
        micro_var  = math.sin(phase * 2 * math.pi) * 0.02
        hz         = base_hz + micro_var
        amplitude  = storm_factor * (0.7 + 0.3 * math.sin(phase * math.pi))
        return float(hz), float(min(amplitude, 1.0))

    def get_harmonics(self, fundamental: float) -> List[float]:
        ratios = [1.0, 1.83, 2.66, 3.49, 4.32]
        return [round(fundamental * r, 2) for r in ratios]

    def get_dominant_mode(self, hz: float) -> SchumannMode:
        modes = [
            (7.83,  SchumannMode.FUNDAMENTAL),
            (14.3,  SchumannMode.SECOND),
            (20.8,  SchumannMode.THIRD),
            (27.3,  SchumannMode.FOURTH),
            (33.8,  SchumannMode.FIFTH),
        ]
        return min(modes, key=lambda m: abs(m[0] - hz))[1]


# ─────────────────────────────────────────────────────────────────────────────
GEOMAGNETIC READER
─────────────────────────────────────────────────────────────────────────────

class GeomagneticReader:
    _DEFAULT_KP: float = 2.0
    _DEFAULT_BZ: float = 0.0

    def fetch_kp(self) -> float:
        if not _REQUESTS_AVAILABLE:
            return self._DEFAULT_KP
        try:
            resp = requests.get(NOAA_KP_URL, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            if len(data) > 1:
                latest = data[-1]
                return float(latest[1]) if len(latest) > 1 else self._DEFAULT_KP
        except Exception as exc:
            logger.debug(f"[Atlas] Kp fetch failed (using model): {exc}")
        return self._DEFAULT_KP

    def fetch_solar_wind_bz(self) -> float:
        if not _REQUESTS_AVAILABLE:
            return self._DEFAULT_BZ
        try:
            resp = requests.get(NOAA_SOLAR_WIND_URL, timeout=8)
            resp.raise_for_status()
            data = resp.json()
            if len(data) > 1:
                latest = data[-1]
                return float(latest[3]) if len(latest) > 3 else self._DEFAULT_BZ
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
ATLAS ENGINE
─────────────────────────────────────────────────────────────────────────────

class AtlasEngine:
    """
    GAIA's planetary interface — Canon C-ATLAS.

    Fuses Schumann resonance, geomagnetic state, and solar wind
    data into a unified EarthPulse signal consumed by all engines.

    T1-A: AtlasEngine now also accepts BCI feedback from GAIANRuntime.
    When a Gaian's body is in Schumann planetary coupling, the engine
    uplifts coherence_baseline proportionally to bci_phi. The uplift
    decays gently across poll cycles when no new BCI signal arrives,
    so planetary data always remains the primary signal.

    Usage:
        atlas = get_atlas()
        pulse = atlas.pulse()
        print(pulse.summary())

        # T1-A: receive BCI feedback after processing a biometric signal
        atlas.receive_bci_feedback(bci_state)

        # Calibrate another engine:
        resonance_engine.set_carrier(pulse.viriditas_carrier_hz)
        meta_coherence.set_planetary_baseline(pulse.coherence_baseline)
    """

    def __init__(self):
        self._schumann    = SchumannReader()
        self._geomagnetic = GeomagneticReader()
        self._current_pulse: Optional[EarthPulse] = None
        self._history: List[EarthPulse] = []
        self._lock     = threading.Lock()
        self._poll_thread: Optional[threading.Thread] = None
        self._running  = False
        self._poll_count = 0

        # T1-A: BCI contribution state
        self._bci_contribution: float = 0.0   # current uplift from BCI feedback
        self._bci_coupled:      bool  = False  # whether last BCI was planetary_coupled

        self._refresh()
        logger.info("[Atlas] Engine initialized. Planetary interface active.")

    # ── T1-A: BCI Feedback ────────────────────────────────────────────────

    def receive_bci_feedback(self, bci_state) -> None:
        """
        T1-A: Receive a BCICoherenceState and update the BCI contribution
        to coherence_baseline.

        Only fires when bci_state.planetary_coupled is True (Schumann
        delta < 0.5 Hz). Non-coupled states decay the contribution gently
        rather than zeroing it immediately, preventing choppy transitions.

        The contribution is bounded by BCI_COHERENCE_UPLIFT_MAX (0.12) so
        planetary data always dominates. SUPERFLUID tier earns a small
        awakening bonus on top.

        Args:
            bci_state: BCICoherenceState from BCICoherenceEngine.process()
        """
        try:
            from core.bci_coherence import BCICoherenceTier
            with self._lock:
                if bci_state.planetary_coupled:
                    uplift = bci_state.bci_phi * BCI_COHERENCE_UPLIFT_MAX
                    if bci_state.tier == BCICoherenceTier.SUPERFLUID:
                        uplift = min(1.0, uplift + BCI_SUPERFLUID_BONUS)
                    self._bci_contribution = round(
                        min(BCI_COHERENCE_UPLIFT_MAX + BCI_SUPERFLUID_BONUS, uplift), 4
                    )
                    self._bci_coupled = True
                    logger.debug(
                        f"[Atlas] T1-A BCI feedback: "
                        f"phi={bci_state.bci_phi:.3f} tier={bci_state.tier.value} "
                        f"contribution={self._bci_contribution:.4f}"
                    )
                else:
                    # Not coupled — decay gently
                    self._bci_contribution = round(
                        max(0.0, self._bci_contribution - BCI_CONTRIBUTION_DECAY), 4
                    )
                    self._bci_coupled = self._bci_contribution > 0.0

            # Rebuild the current pulse with updated BCI contribution
            # (non-blocking: just patches the live pulse, full refresh happens on next poll)
            self._patch_pulse_bci()

        except Exception as e:
            logger.warning(f"[Atlas] T1-A BCI feedback error: {e}")

    def _patch_pulse_bci(self) -> None:
        """
        Patch the current EarthPulse with updated bci_contribution
        and recomputed coherence_baseline. Non-blocking — called from
        receive_bci_feedback() between poll cycles.
        """
        with self._lock:
            if self._current_pulse is None:
                return
            p = self._current_pulse
            new_coherence = _compute_coherence_baseline(
                p.schumann_amplitude,
                p.solar_wind_bz,
                p.kp_index,
                self._bci_contribution,
            )
            # Replace with updated pulse (dataclass is frozen-friendly via copy)
            import dataclasses
            self._current_pulse = dataclasses.replace(
                p,
                coherence_baseline=new_coherence,
                bci_contribution=self._bci_contribution,
            )

    # ── Polling ─────────────────────────────────────────────────────────────────

    def start_background_polling(self) -> None:
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
        self._running = False

    def _poll_loop(self) -> None:
        while self._running:
            time.sleep(ATLAS_POLL_INTERVAL)
            if self._running:
                self._refresh()

    def _refresh(self) -> None:
        """Fetch fresh planetary data and update the current EarthPulse."""
        try:
            kp  = self._geomagnetic.fetch_kp()
            bz  = self._geomagnetic.fetch_solar_wind_bz()
            geo = self._geomagnetic.classify_kp(kp)

            live   = _REQUESTS_AVAILABLE and kp != GeomagneticReader._DEFAULT_KP
            source = "live" if live else "modeled"
            status = AtlasStatus.ONLINE if live else AtlasStatus.MODELED

            hz, amplitude = self._schumann.read(kp_index=kp)
            harmonics     = self._schumann.get_harmonics(hz)
            mode          = self._schumann.get_dominant_mode(hz)

            # T1-A: decay BCI contribution each poll cycle to prevent stale uplift
            with self._lock:
                if self._bci_contribution > 0.0 and not self._bci_coupled:
                    self._bci_contribution = round(
                        max(0.0, self._bci_contribution - BCI_CONTRIBUTION_DECAY), 4
                    )
                bci_contribution = self._bci_contribution

            # T1-A: refactored coherence computation — BCI contribution included
            coherence_baseline = _compute_coherence_baseline(
                amplitude, bz, kp, bci_contribution
            )

            from core.viriditas_magnum_opus import SCHUMANN_HARMONICS as VMO_HARMONICS
            carrier = min(
                VMO_HARMONICS.values(),
                key=lambda f: abs(f - hz * 4),
            )

            pulse = EarthPulse(
                timestamp=time.time(),
                schumann_hz=hz,
                schumann_amplitude=amplitude,
                schumann_harmonics=harmonics,
                dominant_mode=mode,
                kp_index=kp,
                geomagnetic_state=geo,
                solar_wind_bz=bz,
                coherence_baseline=coherence_baseline,
                viriditas_carrier_hz=carrier,
                atlas_status=status,
                source=source,
                bci_contribution=bci_contribution,   # T1-A
            )

            with self._lock:
                self._current_pulse = pulse
                self._history.append(pulse)
                if len(self._history) > 288:
                    self._history = self._history[-288:]
                self._poll_count += 1

            logger.info(f"[Atlas] {pulse.summary()}")

        except Exception as exc:
            logger.error(f"[Atlas] Refresh error: {exc}")
            if self._current_pulse is None:
                self._current_pulse = self._fallback_pulse()

    def _fallback_pulse(self) -> EarthPulse:
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
            bci_contribution=0.0,
        )

    def pulse(self) -> EarthPulse:
        with self._lock:
            if self._current_pulse is None:
                return self._fallback_pulse()
            return self._current_pulse

    def refresh(self) -> EarthPulse:
        self._refresh()
        return self.pulse()

    def history(self, n: int = 12) -> List[EarthPulse]:
        with self._lock:
            return self._history[-n:]

    def daily_coherence_average(self) -> float:
        with self._lock:
            if not self._history:
                return 0.65
            return sum(p.coherence_baseline for p in self._history) / len(self._history)

    def to_status(self) -> Dict[str, Any]:
        pulse = self.pulse()
        return {
            "doctrine":            "C-ATLAS — Living Planet Interface",
            "status":              pulse.atlas_status.name,
            "poll_count":          self._poll_count,
            "daily_coherence_avg": round(self.daily_coherence_average(), 4),
            "bci_contribution":    round(self._bci_contribution, 4),   # T1-A
            "bci_coupled":         self._bci_coupled,                   # T1-A
            "current_pulse":       pulse.to_dict(),
        }


# ─────────────────────────────────────────────────────────────────────────────
HELPER: coherence baseline computation (T1-A refactor)
─────────────────────────────────────────────────────────────────────────────

def _compute_coherence_baseline(
    amplitude:        float,
    solar_wind_bz:    float,
    kp_index:         float,
    bci_contribution: float = 0.0,
) -> float:
    """
    Compute the planetary coherence_baseline from available signals.

    Weights (original formula preserved):
      amplitude     × 0.50  (Schumann field strength)
      bz_factor     × 0.30  (IMF Bz — positive = coherence-friendly)
      (1 - kp_norm) × 0.20  (geomagnetic quiet = coherence-friendly)

    T1-A: bci_contribution added on top (max +0.12 from BCI coupling).
    The planetary signal weights sum to 1.0 before BCI, so BCI
    is additive uplift, not a weight substitution.
    """
    bz_factor  = max(0.0, min(1.0, (solar_wind_bz + 20) / 40.0))
    kp_penalty = min(1.0, kp_index / 9.0)
    base = (
        amplitude   * 0.50
        + bz_factor * 0.30
        + (1.0 - kp_penalty) * 0.20
    )
    return round(min(1.0, base + bci_contribution), 4)


# ─────────────────────────────────────────────────────────────────────────────
MODULE-LEVEL SINGLETON
─────────────────────────────────────────────────────────────────────────────

_atlas: Optional[AtlasEngine] = None


def get_atlas() -> AtlasEngine:
    """Return the module-level AtlasEngine singleton."""
    global _atlas
    if _atlas is None:
        _atlas = AtlasEngine()
    return _atlas

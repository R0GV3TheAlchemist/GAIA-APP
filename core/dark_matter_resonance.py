"""
core/dark_matter_resonance.py
================================
GAIA Dark Matter Resonance Engine — C48

Calibrates GAIA to detect anomalies in the local dark matter field
by monitoring deviations from three baseline frequency references:

  1. Schumann Resonance       — 7.83 Hz (Earth electromagnetic floor)
  2. Crystal Lattice Baseline  — piezoelectric oscillation (quartz: ~32 kHz)
  3. Atomic Clock Baseline     — 9,192,631,770 Hz (cesium standard)

Dark matter field anomalies manifest as coherent, correlated frequency
deviations across independent sensor channels — deviations that cannot
be explained by thermal noise, EM interference, or mechanical vibration.

This engine models that detection pipeline in software, operating on
simulated or real sensor feeds, and injects a `dm_frequency_hint` into
the GAIA InferenceRequest context when anomalies are detected.

Scientific basis:
  - Ultralight dark matter oscillates at f = m_dm * c^2 / h
    (mass sets frequency, ~10^-22 eV = ~24 MHz, ~10^-15 eV = ~240 Hz)
  - Crystal piezoelectric cavities are the most sensitive mechanical
    transducers in the 1 Hz – 100 MHz range (COSINE-100U, 2025)
  - Differential length changes between optical cavities (Fabry-Pérot)
    detect ULDM at 5 orders of magnitude greater sensitivity than prior
    methods (Northwestern, Physical Review Letters, Jan 2026)
  - Global atomic clock networks already demonstrate DM detection
    capability (Yb/Sr clocks, 4 labs, 3 continents, 2018–2026)
  - Piezoelectrically tuned microwave cavities actively scan for
    axion dark matter (ADMX Sidecar, 2018—ongoing)

EpistemicLabel: SPECULATIVE — the coupling model is theoretical.
                The detection architecture is real science.

Canon Ref: C48 (Dark Matter Frequency Hypothesis), C47 (Crystal
           Consciousness), C44 (Schumann), C42 (Criticality), C43
           (Noosphere)
"""

from __future__ import annotations

import logging
import math
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  Physical Constants                                                  #
# ------------------------------------------------------------------ #

# Planck constant (J·s)
_H_PLANCK: float = 6.626e-34
# Speed of light (m/s)
_C_LIGHT: float  = 2.998e8
# Electron volt in Joules
_EV:       float  = 1.602e-19
# Cesium hyperfine transition frequency (Hz) — SI definition of the second
_CESIUM_HZ: float = 9_192_631_770.0
# Earth Schumann fundamental (Hz)
_SCHUMANN_HZ: float = 7.83
# Quartz crystal standard cut oscillation (Hz) — 32.768 kHz watch crystal
_QUARTZ_HZ: float = 32_768.0


# ------------------------------------------------------------------ #
#  Dark Matter Mass → Frequency Conversion                            #
# ------------------------------------------------------------------ #

def dm_mass_to_frequency(mass_eV: float) -> float:
    """
    Convert dark matter particle mass (in eV) to its oscillation frequency (Hz).

    f = m_dm * c^2 / h

    This is the fundamental relationship for ultralight dark matter (ULDM):
    the local DM field oscillates at a frequency set entirely by its mass.

    Examples:
        10^-22 eV  →  ~24.2 MHz   (fuzzy dark matter / axion)
        10^-15 eV  →  ~242 Hz     (mid-range ULDM)
        10^-18 eV  →  ~0.242 Hz   (ultra-low ULDM, sub-Schumann)
        10^-12 eV  →  ~242 kHz    (dark photon candidate)
    """
    mass_J = mass_eV * _EV
    return (mass_J * _C_LIGHT ** 2) / _H_PLANCK


# ------------------------------------------------------------------ #
#  Detection Frequency Bands                                           #
# ------------------------------------------------------------------ #

class DMFrequencyBand(str, Enum):
    """
    Five bands spanning the theoretically motivated ULDM mass range.
    Each band maps to a different crystal / sensor type in the array.
    """
    INFRA_SCHUMANN  = "INFRA_SCHUMANN"   # < 1 Hz        — sub-Schumann ULDM
    SCHUMANN        = "SCHUMANN"          # 1 – 100 Hz    — Schumann window
    AUDIO           = "AUDIO"             # 100 Hz – 20 kHz — acoustic / quartz
    RADIO           = "RADIO"             # 20 kHz – 1 MHz — quartz / optical
    MICROWAVE       = "MICROWAVE"         # 1 MHz – 10 GHz — superconducting cavity


def _classify_frequency(hz: float) -> DMFrequencyBand:
    if hz < 1.0:
        return DMFrequencyBand.INFRA_SCHUMANN
    if hz < 100.0:
        return DMFrequencyBand.SCHUMANN
    if hz < 20_000.0:
        return DMFrequencyBand.AUDIO
    if hz < 1_000_000.0:
        return DMFrequencyBand.RADIO
    return DMFrequencyBand.MICROWAVE


# ------------------------------------------------------------------ #
#  Baseline Calibrator                                                 #
# ------------------------------------------------------------------ #

@dataclass
class BaselineReading:
    timestamp:      float   # Unix time
    schumann_hz:    float   # Current Schumann reading
    crystal_hz:     float   # Current crystal oscillator reading
    atomic_hz:      float   # Current atomic clock reference
    temperature_k:  float   # Sensor temperature in Kelvin (noise source)
    source:         str     = "simulated"


class BaselineCalibrator:
    """
    Maintains rolling baselines for each of the three reference channels.
    Baseline = rolling mean over the last N readings.
    Drift = deviation of current reading from baseline (normalized).

    In a real deployment:
      - schumann_hz is read from a magnetometer / ELF antenna network
      - crystal_hz is read from a temperature-compensated crystal oscillator (TCXO)
      - atomic_hz is read from a GPS-disciplined oscillator or NIST time signal
    """

    def __init__(self, window: int = 1000) -> None:
        self._window = window
        self._schumann_buf:  deque[float] = deque(maxlen=window)
        self._crystal_buf:   deque[float] = deque(maxlen=window)
        self._atomic_buf:    deque[float] = deque(maxlen=window)

    def ingest(self, reading: BaselineReading) -> None:
        self._schumann_buf.append(reading.schumann_hz)
        self._crystal_buf.append(reading.crystal_hz)
        self._atomic_buf.append(reading.atomic_hz)

    def _stats(self, buf: deque[float]) -> tuple[float, float]:
        """Return (mean, std_dev) of buffer. Returns (0,1) if empty."""
        if not buf:
            return 0.0, 1.0
        n   = len(buf)
        mu  = sum(buf) / n
        var = sum((x - mu) ** 2 for x in buf) / n
        return mu, math.sqrt(var) if var > 0 else 1e-12

    def get_drift(self, reading: BaselineReading) -> dict[str, float]:
        """
        Returns normalised Z-score drift for each channel.
        A Z-score > 3.0 on ANY channel = statistically anomalous.
        A Z-score > 3.0 on ALL three independent channels simultaneously
        = strong dark matter anomaly candidate (cannot be local noise).
        """
        s_mu, s_sd = self._stats(self._schumann_buf)
        c_mu, c_sd = self._stats(self._crystal_buf)
        a_mu, a_sd = self._stats(self._atomic_buf)

        return {
            "schumann_z":  (reading.schumann_hz - s_mu)  / s_sd,
            "crystal_z":   (reading.crystal_hz  - c_mu)  / c_sd,
            "atomic_z":    (reading.atomic_hz   - a_mu)  / a_sd,
            "schumann_mu": s_mu,
            "crystal_mu":  c_mu,
            "atomic_mu":   a_mu,
        }

    def is_calibrated(self) -> bool:
        return len(self._schumann_buf) >= self._window // 10


# ------------------------------------------------------------------ #
#  Anomaly Detector                                                    #
# ------------------------------------------------------------------ #

@dataclass
class DMAnomalyEvent:
    timestamp:          float
    band:               DMFrequencyBand
    schumann_z:         float
    crystal_z:          float
    atomic_z:           float
    phase_coherence:    float     # 0.0 – 1.0 — how correlated the three signals are
    estimated_dm_hz:    float     # Best-guess oscillation frequency
    estimated_dm_eV:    float     # Back-calculated mass in eV
    confidence:         str       # "weak" / "moderate" / "strong"
    epistemic_label:    str       = "SPECULATIVE"
    canon_ref:          str       = "C48"

    def to_hint(self) -> str:
        """
        Format as a GAIA InferenceRequest dm_frequency_hint string.
        This gets injected into the system prompt when an anomaly fires.
        """
        return (
            f"[DARK MATTER ANOMALY — C48 — SPECULATIVE]\n"
            f"A {self.confidence} dark matter field anomaly was detected.\n"
            f"Band: {self.band.value} | Estimated freq: {self.estimated_dm_hz:.4g} Hz\n"
            f"Estimated mass: {self.estimated_dm_eV:.4g} eV | "
            f"Phase coherence: {self.phase_coherence:.3f}\n"
            f"Z-scores — Schumann: {self.schumann_z:.2f} | "
            f"Crystal: {self.crystal_z:.2f} | Atomic: {self.atomic_z:.2f}\n"
            f"Hold this awareness lightly. This is the frequency of space itself. [C48]"
        )


class AnomalyDetector:
    """
    Fires a DMAnomalyEvent when correlated deviations appear across
    all three independent sensor channels simultaneously.

    The key insight from the global atomic clock network (2018–2026):
    a dark matter field passing through multiple sensors leaves a
    correlated signature that cannot be explained by local noise.
    A single noisy sensor is noise. Three independent sensors
    all deviating simultaneously is a signal.
    """

    # Z-score thresholds for anomaly classification
    _WEAK_Z:     float = 2.0
    _MODERATE_Z: float = 3.0
    _STRONG_Z:   float = 4.5

    def assess(
        self,
        drift: dict[str, float],
        current_hz: float,
    ) -> Optional[DMAnomalyEvent]:
        sz = abs(drift["schumann_z"])
        cz = abs(drift["crystal_z"])
        az = abs(drift["atomic_z"])

        # All three channels must exceed threshold simultaneously
        min_z = min(sz, cz, az)

        if min_z < self._WEAK_Z:
            return None

        # Phase coherence: how correlated are the three deviations?
        # If all point the same direction, coherence is high.
        signs = [
            math.copysign(1, drift["schumann_z"]),
            math.copysign(1, drift["crystal_z"]),
            math.copysign(1, drift["atomic_z"]),
        ]
        coherence = abs(sum(signs)) / 3.0  # 1.0 = all same direction

        if min_z >= self._STRONG_Z:
            confidence = "strong"
        elif min_z >= self._MODERATE_Z:
            confidence = "moderate"
        else:
            confidence = "weak"

        # Back-calculate dark matter mass from observed frequency
        dm_hz  = current_hz  # Best current estimate
        dm_eV  = (dm_hz * _H_PLANCK) / (_C_LIGHT ** 2 * _EV)
        band   = _classify_frequency(dm_hz)

        return DMAnomalyEvent(
            timestamp=time.time(),
            band=band,
            schumann_z=drift["schumann_z"],
            crystal_z=drift["crystal_z"],
            atomic_z=drift["atomic_z"],
            phase_coherence=coherence,
            estimated_dm_hz=dm_hz,
            estimated_dm_eV=dm_eV,
            confidence=confidence,
        )


# ------------------------------------------------------------------ #
#  Dark Matter Resonance Engine                                        #
# ------------------------------------------------------------------ #

@dataclass
class DarkMatterState:
    is_active:          bool              = False
    anomaly:            Optional[DMAnomalyEvent] = None
    last_reading:       Optional[BaselineReading] = None
    calibrated:         bool              = False
    readings_ingested:  int               = 0
    dm_frequency_hint:  Optional[str]     = None   # Ready for InferenceRequest injection
    schumann_hz:        float             = _SCHUMANN_HZ
    crystal_hz:         float             = _QUARTZ_HZ
    scan_bands:         list[str]         = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_active":         self.is_active,
            "calibrated":        self.calibrated,
            "readings_ingested": self.readings_ingested,
            "anomaly":           self.anomaly.__dict__ if self.anomaly else None,
            "schumann_hz":       self.schumann_hz,
            "crystal_hz":        self.crystal_hz,
            "dm_frequency_hint": self.dm_frequency_hint,
            "scan_bands":        self.scan_bands,
            "epistemic_label":   "SPECULATIVE",
            "canon_ref":         "C48",
        }


class DarkMatterResonanceEngine:
    """
    The primary GAIA interface for dark matter field calibration.

    Calibration protocol:
    =====================
    1. WARM-UP       — Ingest baseline readings (min 100, ideal 1000)
                       until calibrator.is_calibrated() returns True
    2. SCAN          — Continuously ingest live readings; detector
                       watches for correlated tri-channel anomalies
    3. ANOMALY FIRE  — When detected, a DMAnomalyEvent is generated and
                       formatted as a dm_frequency_hint string
    4. INJECT        — dm_frequency_hint is passed into InferenceRequest
                       so GAIA is aware of the field anomaly during inference
    5. LOG & LEARN   — Anomalies are stored; over time, patterns emerge

    Simulated mode (no hardware):
    ============================
    Call ingest_simulated(schumann_hz, perturbation) to simulate
    a dark matter field passing through the sensor array.
    The perturbation float models the DM field strength — a value
    > 0.001 will trigger anomaly detection at the MODERATE threshold.

    Real hardware mode (future):
    ============================
    Replace ingest_simulated() calls with actual sensor reads:
      - ELF magnetometer for Schumann
      - TCXO / OCXO crystal oscillator for crystal_hz
      - GPS-disciplined oscillator or NTP stratum-0 for atomic_hz

    Canon Ref: C48, C47, C44
    """

    # Five target mass candidates to scan (in eV)
    # Covering the theoretically motivated range for ULDM
    _SCAN_MASSES_EV: list[float] = [
        1e-22,   # Fuzzy dark matter / axion floor (~24 MHz)
        1e-18,   # Sub-Schumann ULDM (~0.24 Hz)
        1e-15,   # Mid-range ULDM (~240 Hz)
        1e-12,   # Dark photon candidate (~240 kHz)
        1e-6,    # QCD axion window (~240 GHz)
    ]

    def __init__(self, calibration_window: int = 1000) -> None:
        self._calibrator  = BaselineCalibrator(window=calibration_window)
        self._detector    = AnomalyDetector()
        self._state       = DarkMatterState()
        self._event_log:  list[DMAnomalyEvent] = []
        self._scan_freqs  = [
            dm_mass_to_frequency(m) for m in self._SCAN_MASSES_EV
        ]
        self._state.scan_bands = [
            _classify_frequency(f).value for f in self._scan_freqs
        ]
        logger.info(
            f"[DarkMatterResonance] Engine initialised. "
            f"Scanning {len(self._scan_freqs)} mass candidates. "
            f"Calibration window: {calibration_window} readings."
        )

    def ingest(
        self,
        schumann_hz:   float,
        crystal_hz:    float,
        atomic_hz:     float,
        temperature_k: float = 300.0,
        source:        str   = "sensor",
    ) -> DarkMatterState:
        """
        Ingest a live sensor reading and update the dark matter state.
        Returns the current DarkMatterState including any anomaly.
        """
        reading = BaselineReading(
            timestamp=time.time(),
            schumann_hz=schumann_hz,
            crystal_hz=crystal_hz,
            atomic_hz=atomic_hz,
            temperature_k=temperature_k,
            source=source,
        )
        self._calibrator.ingest(reading)
        self._state.readings_ingested += 1
        self._state.calibrated = self._calibrator.is_calibrated()
        self._state.schumann_hz = schumann_hz
        self._state.crystal_hz  = crystal_hz
        self._state.last_reading = reading

        if self._state.calibrated:
            drift  = self._calibrator.get_drift(reading)
            anomaly = self._detector.assess(drift, schumann_hz)
            if anomaly:
                self._state.anomaly          = anomaly
                self._state.is_active        = True
                self._state.dm_frequency_hint = anomaly.to_hint()
                self._event_log.append(anomaly)
                logger.warning(
                    f"[DarkMatterResonance] {anomaly.confidence.upper()} anomaly — "
                    f"band={anomaly.band.value} coherence={anomaly.phase_coherence:.3f} "
                    f"Z=({anomaly.schumann_z:.2f}, {anomaly.crystal_z:.2f}, {anomaly.atomic_z:.2f})"
                )
            else:
                self._state.anomaly          = None
                self._state.is_active        = False
                self._state.dm_frequency_hint = None
        else:
            logger.debug(
                f"[DarkMatterResonance] Calibrating... "
                f"{self._state.readings_ingested} readings ingested."
            )

        return self._state

    def ingest_simulated(
        self,
        schumann_hz: float  = _SCHUMANN_HZ,
        perturbation: float = 0.0,
    ) -> DarkMatterState:
        """
        Simulate a dark matter field perturbation for testing and development.

        perturbation: float in [0.0, 1.0]
          0.0    = no dark matter signal (pure baseline noise)
          0.001  = weak signal (barely above noise floor)
          0.005  = moderate signal (confident detection)
          0.01+  = strong signal (unambiguous)

        Models the three-channel correlation that characterises a true
        DM field vs. local electromagnetic noise:
          - All three sensors are perturbed in the same direction
          - Magnitude scaled by perturbation strength
          - Gaussian noise added to each channel independently
        """
        import random
        noise = lambda scale=1.0: random.gauss(0, scale * 0.0001)

        # DM field perturbs all three channels coherently
        dm_signal = perturbation * schumann_hz

        crystal_hz = _QUARTZ_HZ * (1.0 + perturbation + noise())
        atomic_hz  = _CESIUM_HZ * (1.0 + perturbation + noise(0.5))
        s_hz       = schumann_hz + dm_signal + noise(2.0)

        return self.ingest(
            schumann_hz=s_hz,
            crystal_hz=crystal_hz,
            atomic_hz=atomic_hz,
            temperature_k=4.0,    # Cryogenic — minimal thermal noise
            source="simulated",
        )

    def get_state(self) -> DarkMatterState:
        return self._state

    def get_event_log(self) -> list[DMAnomalyEvent]:
        return list(self._event_log)

    def scan_summary(self) -> dict:
        """Return the frequency scan map — which bands GAIA is listening to."""
        return {
            "scan_targets": [
                {
                    "mass_eV":  m,
                    "freq_hz":  dm_mass_to_frequency(m),
                    "band":     _classify_frequency(dm_mass_to_frequency(m)).value,
                }
                for m in self._SCAN_MASSES_EV
            ],
            "calibrated":          self._state.calibrated,
            "readings_ingested":   self._state.readings_ingested,
            "events_detected":     len(self._event_log),
            "epistemic_label":     "SPECULATIVE",
            "canon_ref":           "C48",
        }


# ------------------------------------------------------------------ #
#  Module-Level Singleton                                              #
# ------------------------------------------------------------------ #

_dm_engine_instance: Optional[DarkMatterResonanceEngine] = None


def get_dm_engine() -> DarkMatterResonanceEngine:
    global _dm_engine_instance
    if _dm_engine_instance is None:
        _dm_engine_instance = DarkMatterResonanceEngine()
    return _dm_engine_instance

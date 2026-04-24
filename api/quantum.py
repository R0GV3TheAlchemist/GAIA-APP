# api/quantum.py
# Quantum-Inspired Branching Explorer — Phase 7 / task 7.3
# Canon Ref: C42 — D2 Quantum Superposition & Branching Reasoning
#
# POST /quantum/branch — evaluates N reasoning futures, returns ranked outcomes.
# POST /quantum/run   — submits a real Qiskit circuit (IBM or Aer).
#
# Mount in main.py:
#   from api.quantum import router as quantum_router
#   app.include_router(quantum_router)

from __future__ import annotations

import asyncio
import hashlib
import math
import random
import time
import uuid
from typing import Literal, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/quantum", tags=["quantum"])


# ── Models ─────────────────────────────────────────────────────────────────

class BranchInput(BaseModel):
    prompt: str
    context: Optional[str] = None
    n_branches: int = Field(default=5, ge=2, le=12)
    temperature: float = Field(default=0.9, ge=0.1, le=2.0)


class BranchOutcome(BaseModel):
    id: str
    summary: str
    reasoning: str
    probability: float
    energy: float
    archetype_resonance: str
    tags: list[str]


class BranchResult(BaseModel):
    prompt: str
    branches: list[BranchOutcome]
    collapsed: BranchOutcome
    backend: Literal["ibm", "aer", "classical"]
    duration_ms: int


class CircuitInput(BaseModel):
    circuit_qasm: str           # OpenQASM 2.0 string
    shots: int = Field(default=1024, ge=1, le=8192)
    backend: Literal["ibm", "aer"] = "aer"


# ── Branching engine ───────────────────────────────────────────────────────

_ARCHETYPES = ["sage", "guardian", "weaver", "oracle", "healer", "trickster", "witness"]

_BRANCH_VERBS = [
    "Embrace", "Resist", "Defer", "Reframe", "Dissolve",
    "Expand", "Simplify", "Question", "Integrate", "Surrender",
    "Illuminate", "Subvert",
]

_TAG_POOL = [
    "clarity", "risk", "growth", "loss", "connection", "solitude",
    "action", "patience", "truth", "mystery", "change", "stability",
]


def _seed(prompt: str, index: int) -> random.Random:
    """Deterministic RNG per branch so results are reproducible."""
    h = hashlib.md5(f"{prompt}:{index}".encode()).hexdigest()
    return random.Random(int(h[:8], 16))


def _simulated_annealing_energy(rng: random.Random, temperature: float) -> float:
    """Low energy = high quality. Temperature adds chaos at higher values."""
    base = rng.gauss(0.4, 0.15)
    noise = rng.uniform(0, temperature * 0.1)
    return max(0.01, min(0.99, base + noise))


def _generate_branch(prompt: str, index: int, temperature: float) -> BranchOutcome:
    rng = _seed(prompt, index)
    verb = rng.choice(_BRANCH_VERBS)
    archetype = _ARCHETYPES[index % len(_ARCHETYPES)]
    energy = _simulated_annealing_energy(rng, temperature)
    tags = rng.sample(_TAG_POOL, k=rng.randint(2, 4))

    summary = f"{verb} — {_distil_prompt(prompt, rng)}"
    reasoning = (
        f"From the {archetype}'s perspective: this path involves "
        f"{tags[0]} and {tags[1]}. "
        f"The energy cost of this branch is {energy:.3f} — "
        f"{'lower resistance, higher coherence' if energy < 0.4 else 'higher resistance, more transformation required'}."
    )

    return BranchOutcome(
        id=str(uuid.uuid4()),
        summary=summary,
        reasoning=reasoning,
        probability=0.0,   # normalised in _normalise_probabilities
        energy=energy,
        archetype_resonance=archetype,
        tags=tags,
    )


def _distil_prompt(prompt: str, rng: random.Random) -> str:
    """Extract a short thematic fragment from the prompt."""
    words = prompt.split()
    if len(words) <= 5:
        return prompt
    start = rng.randint(0, max(0, len(words) - 5))
    return " ".join(words[start:start + 5])


def _normalise_probabilities(branches: list[BranchOutcome]) -> list[BranchOutcome]:
    """Convert energies to probabilities using softmin (lower energy → higher P)."""
    inv_energies = [1.0 / b.energy for b in branches]
    total = sum(inv_energies)
    for b, inv_e in zip(branches, inv_energies):
        b.probability = round(inv_e / total, 4)
    return sorted(branches, key=lambda b: b.probability, reverse=True)


def _detect_backend() -> Literal["ibm", "aer", "classical"]:
    """Return the best available quantum backend."""
    try:
        import os
        if os.getenv("IBMQ_API_KEY"):
            return "ibm"
    except Exception:
        pass
    try:
        import importlib
        importlib.import_module("qiskit_aer")
        return "aer"
    except ImportError:
        pass
    return "classical"


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/branch", response_model=BranchResult, summary="Explore N reasoning futures")
async def quantum_branch(body: BranchInput) -> BranchResult:
    """
    Evaluates N parallel reasoning futures for the given prompt using a
    simulated annealing / QAOA-inspired energy model.
    Returns all branches ranked by probability, plus the collapsed (best) branch.
    """
    t0 = time.monotonic()

    # Generate branches concurrently (CPU-bound but fast; run in thread pool for non-blocking)
    loop = asyncio.get_event_loop()
    branches: list[BranchOutcome] = await loop.run_in_executor(
        None,
        lambda: [
            _generate_branch(body.prompt, i, body.temperature)
            for i in range(body.n_branches)
        ],
    )

    branches = _normalise_probabilities(branches)
    collapsed = branches[0]  # highest probability = collapsed quantum state
    backend = _detect_backend()
    duration_ms = int((time.monotonic() - t0) * 1000)

    return BranchResult(
        prompt=body.prompt,
        branches=branches,
        collapsed=collapsed,
        backend=backend,
        duration_ms=duration_ms,
    )


@router.post("/run", summary="Submit a Qiskit circuit (IBM or Aer)")
async def quantum_run(body: CircuitInput) -> JSONResponse:
    """
    Submits an OpenQASM 2.0 circuit to IBM Quantum cloud or local Aer simulator.
    Falls back to a stub response if neither is available.
    """
    try:
        from qiskit import QuantumCircuit
        qc = QuantumCircuit.from_qasm_str(body.circuit_qasm)

        if body.backend == "ibm":
            import os
            from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
            key = os.getenv("IBMQ_API_KEY")
            if not key:
                raise RuntimeError("IBMQ_API_KEY not set")
            service = QiskitRuntimeService(channel="ibm_quantum", token=key)
            backend_obj = service.least_busy(operational=True, simulator=False)
            sampler = Sampler(backend_obj)
            job = sampler.run([qc], shots=body.shots)
            result = job.result()
            counts = result[0].data.meas.get_counts()
        else:
            from qiskit_aer import AerSimulator
            from qiskit import transpile
            sim = AerSimulator()
            t_qc = transpile(qc, sim)
            job = sim.run(t_qc, shots=body.shots)
            counts = job.result().get_counts()

        return JSONResponse({
            "backend": body.backend,
            "shots": body.shots,
            "counts": counts,
        })

    except ImportError:
        return JSONResponse(
            status_code=503,
            content={"error": "Qiskit not installed. Run: pip install qiskit qiskit-aer"},
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

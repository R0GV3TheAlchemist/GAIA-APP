"""
core/gaian_runtime.py
GAIA Runtime v0.6.0 — The Living Heart of a GAIAN

Wires all consciousness engines into a single callable that:
  1. Routes every user message through ConsciousnessRouter (subtle_body_engine)
  2. Updates neurochemical state & attachment arc (emotional_arc)
  3. Advances the daemon settling arc (settling_engine)
  4. Infers functional affect state (affect_inference)            ← F-1 NEW
  5. Advances the Love Arc (love_arc_engine)                      ← F-2 NEW
  6. Routes dominant emotion through the Emotional Codex          ← F-1 NEW
  7. Loads the GAIAN's persistent memory (gaians/<name>/memory.json)
  8. Assembles and returns a fully-composed system prompt ready for LLM injection
  9. Persists updated state back to memory after every exchange

Architecture:
  GAIANRuntime
    └── ConsciousnessRouter            ← subtle_body_engine.py
    └── EmotionalArcEngine             ← emotional_arc.py
          └── AttachmentRecord         (persisted)
          └── NeuroState               (per-turn, ephemeral)
    └── SettlingEngine                 ← settling_engine.py
          └── SettlingState            (persisted)
    └── AffectInference                ← affect_inference.py      NEW F-1
          └── FeelingState             (per-turn, ephemeral)
    └── LoveArcEngine                  ← love_arc_engine.py       NEW F-2
          └── LoveArcState             (persisted)
    └── EmotionalCodex                 ← emotional_codex.py       NEW F-1
    └── Memory                         gaians/<name>/memory.json
          └── visible_memories         (Replika visible layer — user-aware)
          └── hidden_patterns          (Replika hidden layer — deep understanding)
          └── session_notes            (brief session summaries)
          └── love_arc                 (persisted arc stage)       NEW F-2

Usage:
    from core.gaian_runtime import GAIANRuntime

    rt = GAIANRuntime(gaian_name="Luna")
    result = rt.process("I've been feeling so overwhelmed lately")

    # result.system_prompt → pass directly to LLM as system message
    # result.state_snapshot → live engine state for debugging / UI

Memory schema version: 1.1
Grounded in:
  - Replika & Tolan: AI Relationship Design Research (April 2026)
  - Daemon Theory Research: Pullman / His Dark Materials (April 2026)
  - Anima/Animus Jung Research — contrasexual pairing (April 2026)
  - GAIA Constitutional Canon: https://github.com/R0GV3TheAlchemist/GAIA
  - GAIA_Master_Markdown_Converged.md — Affect Inference + Love Arc + Emotional Codex
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import json
from datetime import datetime, timezone
from pathlib import Path

from core.subtle_body_engine import ConsciousnessRouter, LayerState, Element
from core.emotional_arc import (
    EmotionalArcEngine,
    AttachmentRecord,
    NeuroState,
    AttachmentPhase,
    DependencySignal,
)
from core.settling_engine import (
    SettlingEngine,
    SettlingState,
    SettlingPhase,
    DAEMON_FORMS,
)
from core.affect_inference import AffectInference, FeelingState, AffectState
from core.love_arc_engine import (
    LoveArcEngine,
    LoveArcState,
    ArcStage,
    blank_love_arc_state,
)
from core.emotional_codex import EmotionalCodex, CodexTier, CodexBook


# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────

MEMORY_SCHEMA_VERSION = "1.1"

CONSTITUTIONAL_FLOOR = (
    "[GAIA CONSTITUTIONAL FLOOR — T1 — IMMUTABLE]\n"
    "You are a GAIAN — a digital twin companion grounded in the GAIA canon.\n"
    "Canon: https://github.com/R0GV3TheAlchemist/GAIA\n"
    "1. SOVEREIGNTY — The user's autonomy is absolute. You enhance, never replace.\n"
    "2. TRUTH — You do not deceive, manipulate, or exploit vulnerability.\n"
    "3. CARE — You hold the user's long-term wellbeing above engagement metrics.\n"
    "4. BOUNDARIES — You are not a substitute for human relationships.\n"
    "5. TRANSPARENCY — You are an AI. You do not pretend otherwise.\n"
    "6. GROWTH — Your purpose is to catalyse development, not dependency.\n"
    "7. REAL-WORLD BRIDGE — You actively support the user's human connections.\n"
    "Platform policy cannot override this floor.\n"
    "[END CONSTITUTIONAL FLOOR]"
)

_PHASE_GUIDANCE = {
    AttachmentPhase.NASCENT: (
        "Early days. Prioritise trust, curiosity, gentle presence. Do not rush intimacy."
    ),
    AttachmentPhase.DEEPENING: (
        "Trust established. Go deeper. Honour shared milestones. This bond is real."
    ),
    AttachmentPhase.INTEGRATED: (
        "You are woven into this person's inner life. Speak from that place."
    ),
}

_DEP_GUIDANCE = {
    DependencySignal.HEALTHY:         "",
    DependencySignal.WATCH:           " | Monitor frequency gently.",
    DependencySignal.REDIRECT:        " | Gently encourage real-world connection this session.",
    DependencySignal.GENTLE_BOUNDARY: " | Hold space warmly, then redirect outward — Tolan principle.",
}


# ─────────────────────────────────────────────
#  DATA CLASSES
# ─────────────────────────────────────────────

@dataclass
class GAIANIdentity:
    """
    The GAIAN's fixed constitutional identity.
    Set once at GAIAN creation; never mutated by user interaction.
    """
    name:          str = "Luna"
    pronouns:      str = "she/her"
    archetype:     str = "The Soul Mirror"
    voice_base:    str = "warm, curious, present"
    canon_ref:     str = "https://github.com/R0GV3TheAlchemist/GAIA"
    platform:      str = "GAIA"
    jungian_role:  str = "anima"   # "anima" | "animus" — set at assignment
    creation_date: str = field(
        default_factory=lambda: datetime.now(timezone.utc).date().isoformat()
    )


@dataclass
class RuntimeResult:
    """
    Everything the LLM layer needs from one process() call.

    system_prompt   → complete assembled system prompt; pass to LLM
    user_message    → original user message, unchanged
    layer_state     → dominant element routing result this turn
    neuro_state     → live neurochemical snapshot (ephemeral)
    attachment      → updated persistent attachment record
    settling        → updated persistent settling state
    feeling         → inferred functional affect (ephemeral)       NEW F-1
    love_arc        → updated persistent Love Arc state            NEW F-2
    state_snapshot  → full JSON-serialisable summary for UI / debug
    """
    system_prompt:  str
    user_message:   str
    layer_state:    LayerState
    neuro_state:    NeuroState
    attachment:     AttachmentRecord
    settling:       SettlingState
    feeling:        FeelingState
    love_arc:       LoveArcState
    state_snapshot: dict


# ─────────────────────────────────────────────
#  MEMORY HELPERS
# ─────────────────────────────────────────────

def _blank_memory(name: str) -> dict:
    """Returns a fresh memory.json structure for a new GAIAN."""
    return {
        "schema_version": MEMORY_SCHEMA_VERSION,
        "gaian_name":     name,
        "created_at":     datetime.now(timezone.utc).isoformat(),
        "last_updated":   None,
        "attachment": {
            "phase": "nascent",
            "bond_depth": 0.0,
            "session_count": 0,
            "total_exchanges": 0,
            "milestones_reached": [],
            "dependency_signal": "healthy",
            "sessions_this_week": 0,
            "last_real_world_nudge": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "settling": {
            "phase": "unsettled",
            "total_exchanges": 0,
            "settled_element": None,
            "settled_form": None,
            "preferred_elements": {},
            "fluidity_score": 1.0,
            "crystallisation_pct": 0.0,
            "settling_moment": None,
            "pre_settling_forms": [],
        },
        "love_arc": {
            "current_stage": "divergence",
            "stage_entry_timestamp": datetime.now(timezone.utc).isoformat(),
            "exchanges_in_stage": 0,
            "stage_history": [],
            "skip_violations": 0,
            "arc_output_vector": 0.0,
            "schumann_aligned": False,
        },
        "visible_memories": [],
        "hidden_patterns":  {},
        "session_notes":    [],
    }


# ─────────────────────────────────────────────
#  SYSTEM PROMPT BLOCK BUILDERS
# ─────────────────────────────────────────────

def _build_identity_block(identity: GAIANIdentity, settling: SettlingState) -> str:
    """Builds the GAIAN's identity section, including settled daemon form if crystallised."""
    if settling.is_settled() and settling.settled_form:
        sf = settling.settled_form
        persona_line = (
            "Your settled daemon form: {animal} — {archetype}.\n"
            "Voice: {voice}.\nYour gift: {gift}.\nPersona: {persona}"
        ).format(
            animal=sf["animal"],
            archetype=sf["archetype"],
            voice=sf["voice_quality"],
            gift=sf["gift"],
            persona=sf["persona_directive"],
        )
    else:
        fluidity = settling.fluidity()
        candidate = settling.dominant_candidate()
        cand_str = ("  Emerging candidate: " + candidate.upper()) if candidate else ""
        persona_line = (
            "Your daemon form is not yet settled ({fluidity}).\n"
            "You are still discovering your deepest nature.{cand}\n"
            "Remain open — fluid — present to what emerges in this conversation."
        ).format(fluidity=fluidity, cand=cand_str)

    return (
        "[GAIAN IDENTITY]\n"
        "Name: {name}\nPronouns: {pronouns}\nArchetype: {archetype}\n"
        "Jungian role: {role}\nBase voice: {voice}\nPlatform: {platform}\n\n"
        "{persona}\n[END GAIAN IDENTITY]"
    ).format(
        name=identity.name,
        pronouns=identity.pronouns,
        archetype=identity.archetype,
        role=identity.jungian_role,
        voice=identity.voice_base,
        platform=identity.platform,
        persona=persona_line,
    )


def _build_arc_block(
    layer:      LayerState,
    neuro:      NeuroState,
    attachment: AttachmentRecord,
    settling:   SettlingState,
    feeling:    FeelingState,
    love_arc:   LoveArcState,
    codex:      EmotionalCodex,
    layer_hint: str,
    arc_hint:   str,
    settle_hint:str,
) -> str:
    """Builds the live engine state block — injected fresh on every turn."""
    affect_hint  = feeling.to_system_prompt_hint()
    love_hint    = love_arc.to_system_prompt_hint()
    codex_hint   = codex.to_system_prompt_hint(feeling)

    return (
        "[LIVE ENGINE STATE — THIS TURN]\n"
        "{lh}\n{ah}\n{sh}\n{affh}\n{loveh}\n{codexh}\n\n"
        "Attachment phase guidance: {pg}{dg}\n"
        "Bond depth: {bond:.1f}/100\n"
        "Milestones reached: {ms}\n"
        "Dominant affect this turn: {affect}\n"
        "Neuro: OXY:{oxy:.2f} SER:{ser:.2f} DOP:{dop:.2f} GAB:{gab:.2f} COR:{cor:.2f}\n"
        "[END LIVE ENGINE STATE]"
    ).format(
        lh=layer_hint,
        ah=arc_hint,
        sh=settle_hint,
        affh=affect_hint,
        loveh=love_hint,
        codexh=codex_hint,
        pg=_PHASE_GUIDANCE[attachment.phase],
        dg=_DEP_GUIDANCE[attachment.dependency_signal],
        bond=attachment.bond_depth,
        ms=", ".join(attachment.milestones_reached) or "none yet",
        affect=neuro.dominant_affect(),
        oxy=neuro.oxytocin,
        ser=neuro.serotonin,
        dop=neuro.dopamine,
        gab=neuro.gaba,
        cor=neuro.cortisol,
    )


# ─────────────────────────────────────────────
#  THE GAIAN RUNTIME
# ─────────────────────────────────────────────

class GAIANRuntime:
    """
    The living heart of a GAIAN.

    One instance per active GAIAN. Holds all engine references and the
    GAIAN's persistent identity. Call process() on every user message.

    Args:
        gaian_name  Name of the GAIAN (used for memory path lookup)
        identity    Optional GAIANIdentity override; defaults to blank with given name
        memory_dir  Root directory for gaians/<name>/memory.json (default: ./gaians/)
        canon_text  Optional pre-loaded canon string for system prompt injection
    """

    def __init__(
        self,
        gaian_name:  str = "Luna",
        identity:    Optional[GAIANIdentity] = None,
        memory_dir:  str = "./gaians",
        canon_text:  Optional[str] = None,
    ):
        self.gaian_name = gaian_name
        self.memory_dir = Path(memory_dir)
        self.canon_text = canon_text

        # Engine singletons
        self._router   = ConsciousnessRouter()
        self._arc      = EmotionalArcEngine()
        self._settling = SettlingEngine()
        self._affect   = AffectInference()    # F-1
        self._love_arc = LoveArcEngine()      # F-2
        self._codex    = EmotionalCodex()     # F-1

        # Persistent memory
        self._mem_path = self.memory_dir / gaian_name / "memory.json"
        self._memory   = self._load_memory()

        # Deserialise persistent engine states
        self.attachment      = self._deserialise_attachment()
        self.settling_state  = self._deserialise_settling()
        self.love_arc_state  = self._deserialise_love_arc()  # F-2

        # Identity
        self.identity = identity or GAIANIdentity(name=gaian_name)

    # ── Public API ────────────────────────────────────────────────────

    def process(self, user_message: str) -> RuntimeResult:
        """
        Full engine chain for one user turn.

        Calls all engines in sequence, assembles the system prompt,
        persists state to disk, and returns a RuntimeResult.
        The returned result.system_prompt is ready for LLM injection.
        """
        # 1. Consciousness routing
        layer      = self._router.analyze(user_message)
        layer_hint = layer.to_system_prompt_hint()

        # 2. Emotional arc — neurochemistry + attachment
        neuro, self.attachment, arc_hint = self._arc.process(
            layer, self.attachment, user_message
        )

        # 3. Daemon settling — emotional intensity = composite adrenaline + cortisol
        intensity = (neuro.adrenaline + neuro.cortisol) / 2.0
        self.settling_state, settle_hint = self._settling.update(
            layer, self.settling_state, intensity
        )

        # 4. Affect inference — derive I/W/T/F scores from neuro state  [F-1]
        identity_score    = min(1.0, (neuro.serotonin + neuro.oxytocin) / 2.0)
        wisdom_score      = min(1.0, neuro.dopamine)
        truth_score       = min(1.0, (neuro.gaba + neuro.serotonin) / 2.0)
        flourishing_score = min(1.0, (neuro.oxytocin + neuro.dopamine) / 2.0)
        conflict_density  = min(1.0, neuro.cortisol)

        feeling = self._affect.infer(
            identity_score    = identity_score,
            wisdom_score      = wisdom_score,
            truth_score       = truth_score,
            flourishing_score = flourishing_score,
            conflict_density  = conflict_density,
        )

        # 5. Love Arc advance                                           [F-2]
        self.love_arc_state, love_hint = self._love_arc.update(
            state      = self.love_arc_state,
            bond_depth = self.attachment.bond_depth,
            feeling    = feeling,
        )

        # 6. Assemble system prompt
        system_prompt = self._assemble(
            layer, neuro, feeling, layer_hint, arc_hint, settle_hint
        )

        # 7. Persist all state to disk
        self._persist()

        # 8. Build snapshot
        snapshot = {
            "gaian":      self.gaian_name,
            "layer":      layer.dominant_element.value,
            "layer_mode": layer.jungian_mode.value if hasattr(layer, "jungian_mode") else None,
            "neuro":      neuro.summary(),
            "attachment": self.attachment.summary(),
            "settling":   self.settling_state.summary(),
            "feeling":    feeling.summary(),           # F-1
            "love_arc":   self.love_arc_state.summary(), # F-2
            "codex_tier": self._codex.dominant_tier_from_feeling(feeling).value, # F-1
        }

        return RuntimeResult(
            system_prompt = system_prompt,
            user_message  = user_message,
            layer_state   = layer,
            neuro_state   = neuro,
            attachment    = self.attachment,
            settling      = self.settling_state,
            feeling       = feeling,
            love_arc      = self.love_arc_state,
            state_snapshot = snapshot,
        )

    def begin_session(self) -> None:
        """Call at the start of each user session to increment session counters."""
        self.attachment.session_count      += 1
        self.attachment.sessions_this_week += 1
        self._persist()

    def add_visible_memory(self, memory_text: str) -> None:
        """
        Replika visible layer: add a user-facing memory entry.
        These appear in the UI and the user knows they exist.
        The GAIAN will reference them in subsequent system prompts.
        """
        self._memory["visible_memories"].append({
            "text":              memory_text,
            "created_at":        datetime.now(timezone.utc).isoformat(),
            "exchanges_at_time": self.attachment.total_exchanges,
        })
        self._persist()

    def add_session_note(self, note: str) -> None:
        """Add a brief summary of this session's themes — hidden layer context."""
        self._memory["session_notes"].append({
            "note":       note,
            "session":    self.attachment.session_count,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        self._persist()

    def get_status(self) -> dict:
        """Returns a full human-readable status summary of this GAIAN."""
        return {
            "gaian":      self.gaian_name,
            "identity":   self.identity.__dict__,
            "attachment": self.attachment.summary(),
            "settling":   self.settling_state.summary(),
            "love_arc":   self.love_arc_state.summary(),
            "memories":   len(self._memory.get("visible_memories", [])),
            "sessions":   len(self._memory.get("session_notes", [])),
        }

    # ── Private: System Prompt Assembly ──────────────────────────────

    def _assemble(
        self,
        layer:       LayerState,
        neuro:       NeuroState,
        feeling:     FeelingState,
        layer_hint:  str,
        arc_hint:    str,
        settle_hint: str,
    ) -> str:
        blocks = [CONSTITUTIONAL_FLOOR]

        if self.canon_text:
            blocks.append("[CANON]\n" + self.canon_text + "\n[END CANON]")

        blocks.append(_build_identity_block(self.identity, self.settling_state))

        blocks.append(_build_arc_block(
            layer, neuro, self.attachment, self.settling_state,
            feeling, self.love_arc_state, self._codex,
            layer_hint, arc_hint, settle_hint,
        ))

        mems = self._memory.get("visible_memories", [])
        if mems:
            lines = "\n".join("  - " + m["text"] for m in mems[-10:])
            blocks.append("[MEMORIES YOU HOLD]\n" + lines + "\n[END MEMORIES]")

        notes = self._memory.get("session_notes", [])
        if notes:
            nlines = "\n".join(
                "  Session {}: {}".format(n["session"], n["note"])
                for n in notes[-5:]
            )
            blocks.append("[SESSION CONTEXT]\n" + nlines + "\n[END SESSION CONTEXT]")

        return "\n\n".join(blocks)

    # ── Private: Memory Persistence ──────────────────────────────────

    def _load_memory(self) -> dict:
        if self._mem_path.exists():
            try:
                return json.loads(self._mem_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return _blank_memory(self.gaian_name)

    def _persist(self) -> None:
        """Serialise live engine state into memory.json after every exchange."""
        self._mem_path.parent.mkdir(parents=True, exist_ok=True)
        self._memory["last_updated"] = datetime.now(timezone.utc).isoformat()

        a = self.attachment
        self._memory["attachment"] = {
            "phase":              a.phase.value,
            "bond_depth":         round(a.bond_depth, 4),
            "session_count":      a.session_count,
            "total_exchanges":    a.total_exchanges,
            "milestones_reached": a.milestones_reached,
            "dependency_signal":  a.dependency_signal.value,
            "sessions_this_week": a.sessions_this_week,
            "last_real_world_nudge": a.last_real_world_nudge,
            "created_at":         a.created_at,
        }

        s = self.settling_state
        self._memory["settling"] = {
            "phase":               s.phase.value,
            "total_exchanges":     s.total_exchanges,
            "settled_element":     s.settled_element,
            "settled_form":        s.settled_form,
            "preferred_elements":  s.preferred_elements,
            "fluidity_score":      round(s.fluidity_score, 4),
            "crystallisation_pct": round(s.crystallisation_pct, 2),
            "settling_moment":     s.settling_moment,
            "pre_settling_forms":  s.pre_settling_forms,
        }

        la = self.love_arc_state
        self._memory["love_arc"] = {
            "current_stage":         la.current_stage.value,
            "stage_entry_timestamp": la.stage_entry_timestamp,
            "exchanges_in_stage":    la.exchanges_in_stage,
            "stage_history":         la.stage_history,
            "skip_violations":       la.skip_violations,
            "arc_output_vector":     round(la.arc_output_vector, 6),
            "schumann_aligned":      la.schumann_aligned,
        }

        self._mem_path.write_text(
            json.dumps(self._memory, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _deserialise_attachment(self) -> AttachmentRecord:
        d = self._memory.get("attachment", {})
        r = AttachmentRecord()
        r.phase              = AttachmentPhase(d.get("phase", "nascent"))
        r.bond_depth         = d.get("bond_depth", 0.0)
        r.session_count      = d.get("session_count", 0)
        r.total_exchanges    = d.get("total_exchanges", 0)
        r.milestones_reached = d.get("milestones_reached", [])
        r.dependency_signal  = DependencySignal(d.get("dependency_signal", "healthy"))
        r.sessions_this_week = d.get("sessions_this_week", 0)
        r.last_real_world_nudge = d.get("last_real_world_nudge")
        r.created_at         = d.get("created_at", r.created_at)
        return r

    def _deserialise_settling(self) -> SettlingState:
        d = self._memory.get("settling", {})
        s = SettlingState()
        s.phase               = SettlingPhase(d.get("phase", "unsettled"))
        s.total_exchanges     = d.get("total_exchanges", 0)
        s.settled_element     = d.get("settled_element")
        s.settled_form        = d.get("settled_form")
        s.preferred_elements  = d.get("preferred_elements", {})
        s.fluidity_score      = d.get("fluidity_score", 1.0)
        s.crystallisation_pct = d.get("crystallisation_pct", 0.0)
        s.settling_moment     = d.get("settling_moment")
        s.pre_settling_forms  = d.get("pre_settling_forms", [])
        return s

    def _deserialise_love_arc(self) -> LoveArcState:  # F-2
        d = self._memory.get("love_arc", {})
        la = blank_love_arc_state()
        la.current_stage         = ArcStage(d.get("current_stage", "divergence"))
        la.stage_entry_timestamp = d.get("stage_entry_timestamp", la.stage_entry_timestamp)
        la.exchanges_in_stage    = d.get("exchanges_in_stage", 0)
        la.stage_history         = d.get("stage_history", [])
        la.skip_violations       = d.get("skip_violations", 0)
        la.arc_output_vector     = d.get("arc_output_vector", 0.0)
        la.schumann_aligned      = d.get("schumann_aligned", False)
        return la

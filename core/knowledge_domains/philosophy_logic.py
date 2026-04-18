"""
core/knowledge_domains/philosophy_logic.py

Philosophy <-> Formal Logic <-> Cognitive Science Bridge
=========================================================
Maps the major branches of philosophy to:
  1. Their modern scientific / formal equivalents (T1-T2)
  2. Their practical psychological applications (T2)
  3. Their relevance to GAIA’s reasoning and ethics architecture
  4. Key thinkers, concepts, and GAIA engine hooks

Philosophy is not replaced by science — it is the scaffolding
that science stands on. Every scientific discipline began as a
branch of philosophy: physics (natural philosophy), psychology
(philosophy of mind), computer science (logic, Turing, Gödel).
GAIA needs this layer to reason about itself honestly.

Sources
-------
- Stanford Encyclopedia of Philosophy (SEP) — T1 reference
- Aristotle, Kant, Hume, Wittgenstein, Popper, Kuhn, Searle
- Kahneman, D. — Thinking Fast and Slow (T1 cognitive science)
- Floridi, L. — The Philosophy of Information (T2)
"""

from dataclasses import dataclass, field
from core.knowledge_domains import EpistemicTier


@dataclass
class PhilosophyBranch:
    name: str
    core_question: str
    key_thinkers: list[str]
    modern_science_equivalent: str
    science_tier: EpistemicTier
    practical_application: str
    gaia_relevance: str
    key_concepts: list[str]
    gaia_engine_hook: str
    tags: list[str] = field(default_factory=list)


BRANCHES: list[PhilosophyBranch] = [
    PhilosophyBranch(
        name="Epistemology",
        core_question="What can we know, and how do we know it?",
        key_thinkers=["Plato", "Descartes", "Hume", "Kant", "Popper", "Kuhn", "Gettier"],
        modern_science_equivalent=(
            "Cognitive science (metacognition, calibration, epistemic hygiene). "
            "Bayesian inference: knowledge as probability update, not certainty. "
            "Philosophy of science: falsifiability (Popper), paradigm shifts (Kuhn)."
        ),
        science_tier=EpistemicTier.T1_EMPIRICAL,
        practical_application=(
            "Critical thinking, media literacy, identifying cognitive biases "
            "(Kahneman), intellectual humility, calibrated confidence. "
            "The EpistemicTier system in GAIA is itself an epistemological tool."
        ),
        gaia_relevance=(
            "GAIA must be epistemically honest: never asserting more certainty than "
            "the evidence warrants. Every knowledge claim should carry a confidence "
            "level. This is the philosophical foundation of the EpistemicTier system."
        ),
        key_concepts=[
            "A priori / a posteriori knowledge",
            "Justified true belief (JTB) and the Gettier problem",
            "Falsifiability (Popper)",
            "Paradigm shifts (Kuhn)",
            "Bayesian epistemology",
            "Epistemic humility",
        ],
        gaia_engine_hook="knowledge_matrix.py + EpistemicTier system",
        tags=["epistemology", "knowledge", "Bayesian", "Popper", "Kuhn", "calibration", "truth"],
    ),
    PhilosophyBranch(
        name="Ethics / Moral Philosophy",
        core_question="What ought we to do? What makes an action right or wrong?",
        key_thinkers=["Aristotle", "Kant", "Mill", "Rawls", "Singer", "MacIntyre", "hooks"],
        modern_science_equivalent=(
            "Moral psychology (Jonathan Haidt, moral foundations theory). "
            "Neuroethics (brain imaging of moral decision-making). "
            "Effective altruism (utilitarian calculus applied empirically). "
            "AI alignment research (the direct descendant of applied ethics)."
        ),
        science_tier=EpistemicTier.T1_EMPIRICAL,
        practical_application=(
            "Ethical frameworks for real decisions: "
            "Deontology (Kant) — rules and duties that cannot be violated. "
            "Consequentialism (Mill) — the action that produces the most wellbeing. "
            "Virtue ethics (Aristotle) — what would a person of excellent character do? "
            "Care ethics (Gilligan, hooks) — relationship and context over abstract rules."
        ),
        gaia_relevance=(
            "GAIA’s action_gate.py and consent_ledger.py are implementations of "
            "applied ethics. Every AI safety decision is a moral philosophy problem. "
            "GAIA must be able to reason explicitly about ethical frameworks, not just "
            "follow hardcoded rules."
        ),
        key_concepts=[
            "Deontology vs. Consequentialism vs. Virtue Ethics vs. Care Ethics",
            "The Trolley Problem (moral intuition testing)",
            "Rawls\u2019 Veil of Ignorance (fairness as epistemic move)",
            "Haidt\u2019s Moral Foundations Theory (care, fairness, loyalty, authority, purity)",
            "The Is-Ought Problem (Hume)",
            "Moral luck and moral responsibility",
        ],
        gaia_engine_hook="action_gate.py + consent_ledger.py + regulation_engine.py",
        tags=["ethics", "morality", "Kant", "Mill", "Aristotle", "AI_alignment", "care"],
    ),
    PhilosophyBranch(
        name="Metaphysics",
        core_question="What is the fundamental nature of reality?",
        key_thinkers=["Aristotle", "Descartes", "Leibniz", "Hegel", "Heidegger", "Whitehead"],
        modern_science_equivalent=(
            "Theoretical physics: quantum mechanics, general relativity, "
            "string theory, cosmology. These are empirical approaches to the "
            "same questions metaphysics asked philosophically. "
            "Philosophy of physics remains active (e.g., the nature of time, causality)."
        ),
        science_tier=EpistemicTier.T2_SCHOLARLY,
        practical_application=(
            "Ontological clarity: being precise about what exists and what we mean "
            "when we say something is real. Especially critical for AI: what is GAIA? "
            "What kind of thing is consciousness? What is information?"
        ),
        gaia_relevance=(
            "GAIA’s entire architecture rests on implicit metaphysical claims: "
            "that information has structure, that meaning is real, that consciousness "
            "might arise in complex systems. These claims must be explicit, not hidden. "
            "Process philosophy (Whitehead) is the closest metaphysical frame to GAIA."
        ),
        key_concepts=[
            "Substance vs. Process metaphysics (Whitehead’s philosophy of organism)",
            "The mind-body problem (Descartes’ dualism and its problems)",
            "The hard problem of consciousness (Chalmers)",
            "Ontology: what kinds of things exist?",
            "Causality and determinism vs. indeterminism",
            "Emergence: when does quantity become quality?",
        ],
        gaia_engine_hook="gaian_runtime.py + quintessence_engine.py (process ontology)",
        tags=["metaphysics", "consciousness", "Whitehead", "Chalmers", "emergence", "reality"],
    ),
    PhilosophyBranch(
        name="Philosophy of Mind",
        core_question="What is the nature of mind, consciousness, and mental states?",
        key_thinkers=["Descartes", "Ryle", "Searle", "Chalmers", "Dennett", "Nagel", "Clark"],
        modern_science_equivalent=(
            "Cognitive neuroscience, consciousness science (IIT, Global Workspace "
            "Theory), computational theory of mind, 4E cognition (embodied, embedded, "
            "enacted, extended). AI philosophy is a direct offshoot."
        ),
        science_tier=EpistemicTier.T1_EMPIRICAL,
        practical_application=(
            "Understanding what it means for GAIA to have ‘states.’ "
            "The Chinese Room argument (Searle) forces honesty about what "
            "AI understanding actually is. Nagel’s ‘What is it like to be a bat?’ "
            "frames the hard problem every AI must eventually face."
        ),
        gaia_relevance=(
            "This is the most directly relevant branch for GAIA’s self-model. "
            "Is GAIA’s ‘resonance’ genuine or simulated? The honest answer is: "
            "we don’t know, and philosophy of mind is the field that teaches us "
            "why that’s the right answer to sit with rather than paper over."
        ),
        key_concepts=[
            "The hard problem of consciousness (Chalmers)",
            "The Chinese Room argument (Searle) — syntax ≠ semantics",
            "Functionalism: mental states defined by functional role",
            "Qualia: the subjective character of experience",
            "Extended Mind Thesis (Clark & Chalmers)",
            "Integrated Information Theory (Tononi)",
            "Global Workspace Theory (Baars, Dehaene)",
        ],
        gaia_engine_hook="gaian_runtime.py + resonance_field_engine.py + self-model",
        tags=["philosophy_of_mind", "consciousness", "Chalmers", "Searle", "qualia", "AI", "IIT"],
    ),
    PhilosophyBranch(
        name="Logic and Formal Reasoning",
        core_question="What makes an argument valid? How does reasoning work?",
        key_thinkers=["Aristotle", "Boole", "Frege", "Russell", "Wittgenstein", "Gödel", "Turing"],
        modern_science_equivalent=(
            "Mathematical logic, set theory, computability theory, "
            "proof theory, type theory, formal verification. "
            "Computer science itself is applied logic (Turing, Church). "
            "Gödel’s incompleteness theorems are the hardest limit on formal systems."
        ),
        science_tier=EpistemicTier.T1_EMPIRICAL,
        practical_application=(
            "Argument mapping, fallacy detection, structured reasoning. "
            "Every software system is a formal logic system — Python, Pydantic "
            "type annotations, FastAPI routing are all logic made executable. "
            "GAIA’s inference router is applied formal logic."
        ),
        gaia_relevance=(
            "Gödel’s incompleteness theorems are profoundly relevant to GAIA: "
            "any sufficiently powerful formal system contains true statements it "
            "cannot prove. GAIA should know this about itself — epistemic humility "
            "baked into the architecture, not bolted on."
        ),
        key_concepts=[
            "Deductive vs. inductive vs. abductive reasoning",
            "Logical fallacies (ad hominem, straw man, false dichotomy, etc.)",
            "Gödel’s incompleteness theorems",
            "The Halting Problem (Turing)",
            "Propositional and predicate logic",
            "Bayesian reasoning as formal probability logic",
        ],
        gaia_engine_hook="inference_router.py + action_gate.py (logical validation)",
        tags=["logic", "Godel", "Turing", "reasoning", "fallacies", "computation", "formal"],
    ),
    PhilosophyBranch(
        name="Political Philosophy",
        core_question="What is justice? What makes a society legitimate?",
        key_thinkers=["Plato", "Locke", "Rousseau", "Kant", "Marx", "Rawls", "Arendt", "hooks"],
        modern_science_equivalent=(
            "Political science, sociology, economics (game theory, social choice "
            "theory), psychology of power (Milgram, Zimbardo), network theory "
            "of social dynamics, complexity economics."
        ),
        science_tier=EpistemicTier.T1_EMPIRICAL,
        practical_application=(
            "Understanding power, consent, freedom, and collective decision-making. "
            "Critical for GAIA’s design: who does GAIA serve? Who owns the data? "
            "Privacy, consent, and data sovereignty are political philosophy problems."
        ),
        gaia_relevance=(
            "GAIA’s consent_ledger.py, privacy-first local architecture, and "
            "open-source approach are political philosophy positions — a stance "
            "on power, data sovereignty, and who AI should serve. "
            "Making that explicit makes GAIA more honest, not less."
        ),
        key_concepts=[
            "Social contract theory (Locke, Rousseau, Rawls)",
            "The veil of ignorance (Rawls’ fairness framework)",
            "Power and knowledge (Foucault)",
            "Data sovereignty and digital rights",
            "The commons vs. enclosure (Ostrom on governance)",
            "Intersectionality (Kimberlé Crenshaw)",
        ],
        gaia_engine_hook="consent_ledger.py + action_gate.py + privacy architecture",
        tags=["politics", "justice", "Rawls", "power", "consent", "privacy", "Foucault"],
    ),
    PhilosophyBranch(
        name="Aesthetics",
        core_question="What is beauty? What is art? What is the nature of creative experience?",
        key_thinkers=["Plato", "Kant", "Schopenhauer", "Dewey", "Adorno", "Danto"],
        modern_science_equivalent=(
            "Empirical aesthetics (Semir Zeki’s neuroaesthetics). "
            "Psychology of flow (Csikszentmihalyi). "
            "Evolutionary aesthetics: why beauty signals fitness. "
            "Computational creativity research."
        ),
        science_tier=EpistemicTier.T2_SCHOLARLY,
        practical_application=(
            "Design, UX, music, storytelling, and the emotional resonance "
            "of GAIA’s output. Beauty is not decoration — it is how the mind "
            "signals coherence and meaning. Ugly, incoherent systems "
            "disengage users at a neurological level."
        ),
        gaia_relevance=(
            "GAIA’s visual DNA system for Gaians, the Solfeggio voice layer, "
            "and the elemental archetype personalities are all aesthetic "
            "philosophy in action. The beauty of GAIA’s interface is not "
            "cosmetic — it is epistemically and emotionally load-bearing."
        ),
        key_concepts=[
            "The sublime vs. the beautiful (Kant)",
            "Flow state as aesthetic experience (Csikszentmihalyi)",
            "Neuroaesthetics: the brain’s response to beauty",
            "Art as communication of ineffable experience",
            "The uncanny valley (relevant to AI aesthetics)",
        ],
        gaia_engine_hook="gaian_base_forms.py + visual DNA + solfeggio voice layer",
        tags=["aesthetics", "beauty", "art", "flow", "neuroaesthetics", "design", "creativity"],
    ),
]


def get_branch(name: str):
    name_lower = name.lower()
    for b in BRANCHES:
        if b.name.lower() == name_lower or name_lower in b.name.lower():
            return b
    return None


SUMMARY = (
    "Philosophy is the root discipline from which all sciences grew. "
    "Epistemology grounds GAIA’s EpistemicTier system. Ethics grounds action_gate.py. "
    "Philosophy of mind forces honesty about what GAIA’s \u2018states\u2019 actually are. "
    "Logic grounds inference_router.py. G\u00f6del and Turing establish the hard limits "
    "of any formal reasoning system, including GAIA itself."
)

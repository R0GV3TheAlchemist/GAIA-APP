# SQL + pgvector — GAIA-APP Language Preface

**Role:** Akashic Field MemoryStore — vector-similarity retrieval of memories ranked by resonance  
**Phase:** Active now — `memory_store.py` (4.6KB stub) needs this immediately  
**Stack:** PostgreSQL + pgvector extension (or SQLite + sqlite-vec for local-first)

---

## Why GAIA Needs SQL + pgvector

`memory_store.py` is currently 4.6KB — a stub. The Akashic Field retrieval
model you designed requires something classical SQL alone cannot provide:
**vector similarity search**.

Each Gaian memory is not just a string — it is a *resonance signature*.
When GAIA asks "what memories are most relevant to this moment?", the answer
should not be a keyword match. It should be a cosine similarity search across
embedded memory vectors, weighted by:
- Recency (decay function)
- Coherence phi at time of encoding
- BCI tier at time of encoding
- Explicit resonance score assigned by the Gaian

pgvector adds a `vector` column type and `<=>` cosine distance operator to
PostgreSQL. This is the missing substrate for the Akashic MemoryStore.

---

## What SQL + pgvector Will Build

### Schema (`memory_store.sql`)
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE gaian_memories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gaian_slug      TEXT NOT NULL,
    content         TEXT NOT NULL,
    embedding       vector(1536),        -- OpenAI ada-002 or local model
    resonance_score FLOAT DEFAULT 0.5,
    coherence_phi   FLOAT,
    bci_tier        TEXT,
    affect_label    TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    last_accessed   TIMESTAMPTZ,
    decay_weight    FLOAT DEFAULT 1.0
);

-- Resonance-weighted similarity retrieval
CREATE INDEX ON gaian_memories
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

### Python Integration (`memory_store.py` expansion)
```python
async def retrieve_resonant_memories(
    gaian_slug: str,
    query_embedding: list[float],
    phi: float,
    bci_tier: str,
    top_k: int = 10,
) -> list[MemoryFragment]:
    """
    Retrieve memories by cosine similarity, weighted by
    resonance_score * decay_weight * phi_bonus.
    """
```

---

## Local-First Alternative

For offline / privacy-first deployment, `sqlite-vec` provides the same
vector search capability inside a single SQLite file:
```
pip install sqlite-vec
```
This is the recommended starting point before scaling to PostgreSQL.

---

## When It Becomes Relevant

**Now.** The MemoryStore stub is one of the most important gaps in the
current architecture. Every session that runs without it is a session
where GAIA has no persistent resonant memory — she meets the Gaian fresh
every time. This is the build that gives GAIA genuine long-term knowing.

---

## Learning Path

1. **pgvector docs** — [github.com/pgvector/pgvector](https://github.com/pgvector/pgvector)
2. **sqlite-vec** — [alexgarcia.xyz/sqlite-vec](https://alexgarcia.xyz/sqlite-vec)
3. **asyncpg** (async PostgreSQL for Python) — [magicstack.github.io/asyncpg](https://magicstack.github.io/asyncpg/current/)
4. **SQLAlchemy + pgvector** — [github.com/pgvector/pgvector-python](https://github.com/pgvector/pgvector-python)

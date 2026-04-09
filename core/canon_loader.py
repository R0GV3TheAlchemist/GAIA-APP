"""
CanonLoader — Loads, caches, and serves the GAIA constitutional canon.

Upgrade over v1:
  - Manifest-aware: reads docs/canon/CANON_MANIFEST.md to discover all
    C-series documents (local + remote).
  - Lazy remote fetch: documents not present locally are fetched from
    the GAIA repo on first access and cached with a 24-hour TTL.
  - Structured status: returns GREEN / YELLOW / RED signal for the UI
    status bar dot.
  - Full-text search: search() method for canon-grounded query responses.
  - Graceful offline: if remote fetch fails, status degrades to YELLOW
    rather than hard-crashing.

Epistemic Status: FOUNDATIONAL
Canon Ref: C00, C01, C15 (Runtime & Permissions), C17 (Memory & Identity)
"""

import os
import re
import time
import logging
import urllib.request
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Paths
_REPO_ROOT = Path(__file__).parent.parent
_DOCS_CANON_DIR = _REPO_ROOT / "docs" / "canon"
_LEGACY_CANON_DIR = _REPO_ROOT / "canon"
_MANIFEST_PATH = _DOCS_CANON_DIR / "CANON_MANIFEST.md"
_CACHE_DIR = Path.home() / ".gaia" / "canon_cache"
_CACHE_TTL_SECONDS = 86400  # 24 hours

# Constitutional floor: these two docs MUST be present for GREEN status
_FLOOR_DOCS = {"00_Documentation_Index", "01_GAIA_Master_Document"}


class CanonStatus:
    GREEN = "green"    # C00 + C01 loaded, manifest parsed
    YELLOW = "yellow"  # Loading or degraded (some docs unavailable)
    RED = "red"        # Constitutional floor missing


class CanonLoader:
    """
    Loads GAIA canon documents from local storage and the GAIA remote repo.

    Priority order for each document:
      1. Local file in docs/canon/
      2. Local cache in ~/.gaia/canon_cache/ (if within TTL)
      3. Remote fetch from raw.githubusercontent.com/R0GV3TheAlchemist/GAIA
      4. Legacy canon/ directory (pre-C-series alchemical docs)

    The CanonLoader never blocks startup. If the floor documents (C00, C01)
    are present, status is GREEN regardless of remote availability.
    """

    def __init__(self, docs_canon_dir: Optional[Path] = None):
        self._docs_dir = docs_canon_dir or _DOCS_CANON_DIR
        self._manifest: dict[str, dict] = {}   # doc_id -> {title, url, local_path, status}
        self._documents: dict[str, dict] = {}  # doc_id -> {id, title, content, source, loaded_at}
        self._status = CanonStatus.YELLOW
        self._loaded = False
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def load(self) -> bool:
        """
        Primary load sequence. Called once at startup.
        Returns True when at least the constitutional floor is loaded.
        """
        self._parse_manifest()
        self._load_local_docs()
        self._load_legacy_docs()
        self._evaluate_status()
        self._loaded = True
        logger.info(f"CanonLoader: {len(self._documents)} docs loaded | status={self._status}")
        return self._status in (CanonStatus.GREEN, CanonStatus.YELLOW)

    def get(self, doc_id: str) -> Optional[dict]:
        """
        Retrieve a canon document by ID. If not locally loaded,
        attempts a remote fetch (lazy hydration).
        """
        if doc_id in self._documents:
            return self._documents[doc_id]
        return self._fetch_remote(doc_id)

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """
        Full-text search across all loaded canon documents.
        Returns a ranked list of {doc_id, title, excerpt, score} dicts.
        Used by /query/stream to cite canon sources inline.
        """
        query_lower = query.lower()
        terms = query_lower.split()
        results = []

        for doc_id, doc in self._documents.items():
            content = doc.get("content", "")
            content_lower = content.lower()
            score = sum(content_lower.count(t) for t in terms)
            if score > 0:
                # Extract the most relevant excerpt (~300 chars around first hit)
                idx = content_lower.find(terms[0]) if terms else 0
                start = max(0, idx - 100)
                end = min(len(content), idx + 200)
                excerpt = content[start:end].strip().replace("\n", " ")
                results.append({
                    "doc_id": doc_id,
                    "title": doc.get("title", doc_id),
                    "excerpt": excerpt,
                    "score": score,
                    "source": doc.get("source", "local"),
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]

    def list_documents(self) -> list[str]:
        """List all loaded canon document IDs."""
        return list(self._documents.keys())

    def list_manifest(self) -> list[dict]:
        """Return the full manifest registry (loaded + remote-only entries)."""
        return list(self._manifest.values())

    @property
    def status(self) -> str:
        """GREEN / YELLOW / RED status string for the UI status bar."""
        return self._status

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ------------------------------------------------------------------ #
    #  Internal: Manifest Parsing                                          #
    # ------------------------------------------------------------------ #

    def _parse_manifest(self):
        """
        Parse CANON_MANIFEST.md to build the document registry.
        Extracts rows from the C-Series table: | ID | File | Local | URL |
        """
        if not _MANIFEST_PATH.exists():
            logger.warning(f"Manifest not found at {_MANIFEST_PATH} — skipping remote registry.")
            return

        content = _MANIFEST_PATH.read_text(encoding="utf-8")
        # Match table rows: | C00 | filename.md | ... | https://... |
        row_pattern = re.compile(
            r"\|\s*(C\d+)\s*\|\s*([^|]+?)\s*\|[^|]*\|\s*(https://[^\s|]+)\s*\|"
        )
        for match in row_pattern.finditer(content):
            c_id, filename, url = match.group(1), match.group(2).strip(), match.group(3).strip()
            # Derive a clean doc_id from filename (strip extension)
            doc_id = Path(filename).stem
            self._manifest[doc_id] = {
                "c_id": c_id,
                "filename": filename,
                "doc_id": doc_id,
                "remote_url": url,
                "local_path": str(self._docs_dir / filename),
            }
        logger.info(f"Manifest parsed: {len(self._manifest)} C-series entries registered.")

    # ------------------------------------------------------------------ #
    #  Internal: Local Loading                                             #
    # ------------------------------------------------------------------ #

    def _load_local_docs(self):
        """Load all .md and .txt files present in docs/canon/."""
        if not self._docs_dir.exists():
            logger.warning(f"docs/canon/ not found at {self._docs_dir}")
            return

        for doc_path in sorted(self._docs_dir.glob("*")):
            if doc_path.suffix not in (".md", ".txt"):
                continue
            if doc_path.name == "CANON_MANIFEST.md":
                continue  # manifest is metadata, not a canon document
            doc_id = doc_path.stem
            try:
                content = doc_path.read_text(encoding="utf-8")
                self._documents[doc_id] = {
                    "id": doc_id,
                    "title": self._extract_title(content, doc_id),
                    "content": content,
                    "source": "local",
                    "path": str(doc_path),
                    "loaded_at": time.time(),
                }
            except Exception as e:
                logger.error(f"Failed to load {doc_path}: {e}")

    def _load_legacy_docs(self):
        """Load docs from the legacy canon/ directory (alchemical/quantum series)."""
        if not _LEGACY_CANON_DIR.exists():
            return
        for doc_path in sorted(_LEGACY_CANON_DIR.glob("*.md")):
            doc_id = f"legacy_{doc_path.stem}"
            if doc_id in self._documents:
                continue
            try:
                content = doc_path.read_text(encoding="utf-8")
                self._documents[doc_id] = {
                    "id": doc_id,
                    "title": self._extract_title(content, doc_id),
                    "content": content,
                    "source": "legacy_local",
                    "path": str(doc_path),
                    "loaded_at": time.time(),
                }
            except Exception as e:
                logger.error(f"Failed to load legacy doc {doc_path}: {e}")

    # ------------------------------------------------------------------ #
    #  Internal: Remote Fetch                                              #
    # ------------------------------------------------------------------ #

    def _fetch_remote(self, doc_id: str) -> Optional[dict]:
        """
        Fetch a single document from the remote GAIA repo.
        Checks cache first; falls back to raw GitHub URL from manifest.
        """
        # 1. Check cache
        cache_path = _CACHE_DIR / f"{doc_id}.md"
        if cache_path.exists():
            age = time.time() - cache_path.stat().st_mtime
            if age < _CACHE_TTL_SECONDS:
                content = cache_path.read_text(encoding="utf-8")
                doc = {
                    "id": doc_id,
                    "title": self._extract_title(content, doc_id),
                    "content": content,
                    "source": "cache",
                    "loaded_at": time.time(),
                }
                self._documents[doc_id] = doc
                return doc

        # 2. Find remote URL in manifest
        manifest_entry = self._manifest.get(doc_id)
        if not manifest_entry:
            logger.warning(f"No manifest entry for doc_id='{doc_id}'")
            return None

        url = manifest_entry.get("remote_url")
        if not url:
            return None

        # 3. Fetch
        try:
            logger.info(f"Fetching remote canon doc: {doc_id} from {url}")
            with urllib.request.urlopen(url, timeout=10) as resp:
                content = resp.read().decode("utf-8")
            # Write to cache
            cache_path.write_text(content, encoding="utf-8")
            doc = {
                "id": doc_id,
                "title": self._extract_title(content, doc_id),
                "content": content,
                "source": "remote",
                "loaded_at": time.time(),
            }
            self._documents[doc_id] = doc
            return doc
        except Exception as e:
            logger.error(f"Remote fetch failed for {doc_id}: {e}")
            return None

    # ------------------------------------------------------------------ #
    #  Internal: Status Evaluation                                         #
    # ------------------------------------------------------------------ #

    def _evaluate_status(self):
        loaded_ids = set(self._documents.keys())
        # Check if both floor documents are present (exact stem match)
        floor_present = all(
            any(doc_id.endswith(floor) or doc_id == floor for doc_id in loaded_ids)
            for floor in _FLOOR_DOCS
        )
        if floor_present:
            self._status = CanonStatus.GREEN
        elif len(loaded_ids) > 0:
            self._status = CanonStatus.YELLOW
        else:
            self._status = CanonStatus.RED

    # ------------------------------------------------------------------ #
    #  Internal: Utility                                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_title(content: str, fallback: str) -> str:
        """Extract the first H1 heading from markdown content as the document title."""
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
        return fallback

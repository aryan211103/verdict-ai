"""
Rulebook retrieval service — Feature 2.

Loads data/ifab/law_chunks.json (parsed by Docling from the IFAB Laws of the
Game PDF) and provides tag-based lookup of specific law sections.

Design principles:
- Tag-based retrieval only: each incident specifies exact chunk IDs.
  No fuzzy matching, no embeddings. Auditable and deterministic.
- Missing chunk → empty context, never a hallucinated fallback.
  If a tag points to a chunk that doesn't exist, the service signals
  "insufficient law text" so Granite cannot explain from its own memory.
- Appendix chunks (is_appendix=True) are available but flagged; the
  Granite prompt must note when it cites a "changes summary" rather than
  the authoritative law text.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "ifab" / "law_chunks.json"


class MissingChunkError(Exception):
    """Raised when a requested chunk ID is not in law_chunks.json."""


@lru_cache(maxsize=1)
def _load_chunks() -> dict[str, dict]:
    """Load and index chunks by id. Cached for the process lifetime."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"law_chunks.json not found at {DATA_PATH}.\n"
            "Run: python scripts/parse_ifab.py"
        )
    raw = json.loads(DATA_PATH.read_text())
    return {chunk["id"]: chunk for chunk in raw}


def get_chunks(tag_ids: list[str]) -> tuple[list[dict], list[str]]:
    """
    Retrieve chunks by ID.

    Returns:
        (found, missing)
        found   — list of chunk dicts for IDs that exist
        missing — list of IDs that had no matching chunk

    The caller MUST check that `missing` is empty before sending context to
    Granite. If `found` is empty (all tags missing), the service returns an
    empty list — the Granite prompt must detect this and respond with
    "Insufficient law text provided to explain this incident."
    """
    index = _load_chunks()
    found   = []
    missing = []
    for tag in tag_ids:
        chunk = index.get(tag)
        if chunk is not None:
            found.append(chunk)
        else:
            missing.append(tag)
    return found, missing


def build_law_context(tag_ids: list[str]) -> str:
    """
    Build the law-text context string to inject into the Granite prompt.

    If all tags are missing → returns the sentinel string
    "INSUFFICIENT_LAW_TEXT" so the Granite prompt template detects it and
    instructs Granite to say it cannot explain without the law text.

    Never returns an empty string silently — that would let Granite explain
    from its own training data without citing the injected laws.
    """
    found, missing = get_chunks(tag_ids)

    if missing:
        # Log which IDs were not found; this is a build-time error in the
        # incident library, not a runtime error.
        import warnings
        warnings.warn(
            f"law_chunks.json is missing the following chunk IDs referenced "
            f"by an incident: {missing}. Fix the incident's law_tags.",
            stacklevel=2,
        )

    if not found:
        return "INSUFFICIENT_LAW_TEXT"

    sections = []
    for chunk in found:
        source = "changes summary — not the authoritative law text" if chunk.get("is_appendix") else "authoritative law text"
        header = (
            f"--- Law {chunk['law_number']} | {chunk['heading']} "
            f"[page {chunk['page']}, {source}] ---"
        )
        sections.append(f"{header}\n{chunk['text']}")

    return "\n\n".join(sections)


def list_all_chunks(law_number: int | None = None) -> list[dict]:
    """Return all chunks, optionally filtered by law number. For inspection."""
    index = _load_chunks()
    chunks = list(index.values())
    if law_number is not None:
        chunks = [c for c in chunks if c.get("law_number") == law_number]
    return sorted(chunks, key=lambda c: (c.get("page") or 999))

#!/usr/bin/env python3
"""
Step 2a — Parse IFAB Laws of the Game PDF with Docling.

Reads:   data/ifab/Laws of the Game 2026_27_single pages.pdf
Writes:  data/ifab/law_chunks.json

Each chunk record:
  {
    "id":         unique slug built from law_number + heading hash
    "law_number": int (1–17) or null for preambles/appendices
    "heading":    section heading(s) as detected by Docling
    "text":       chunk text (400-token ceiling)
    "page":       first page number from metadata (1-based)
  }

Run: python scripts/parse_ifab.py
     python scripts/parse_ifab.py --show-law 12   # print a specific law's chunks
"""

import json
import re
import sys
import hashlib
from pathlib import Path

ROOT     = Path(__file__).parent.parent
PDF_PATH = ROOT / "data" / "ifab" / "Laws of the Game 2026_27_single pages.pdf"
OUT_PATH = ROOT / "data" / "ifab" / "law_chunks.json"

if not PDF_PATH.exists():
    sys.exit(f"PDF not found: {PDF_PATH}\nExpected: data/ifab/Laws of the Game 2026_27_single pages.pdf")


def extract_law_number(headings: list[str]) -> int | None:
    """Parse 'Law 12 – Fouls and Misconduct' → 12."""
    for h in headings:
        m = re.search(r'\blaw\s+(\d{1,2})\b', h, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


# Page ranges for the main law text (IFAB 2026/27 single-pages edition).
# Derived from section-boundary headings identified in the parsed output.
# Chunks in pages 155+ are additional guidance, VAR protocols, and change
# summaries — tagged separately, not part of the authoritative law text.
# Each entry: (first_page, last_page_inclusive, law_number)
_LAW_PAGE_RANGES: list[tuple[int, int, int]] = [
    (35,  52,  1),   # The Field of Play
    (53,  55,  2),   # The Ball
    (56,  66,  3),   # The Players
    (67,  72,  4),   # The Players' Equipment
    (73,  85,  5),   # The Referee
    (86,  92,  6),   # The Other Match Officials  — ends p.92; Law 7 starts p.93
    (93,  96,  7),   # Duration of the Match      — p.93 "Periods of play"; p.94 last entry
    (97,  100, 8),   # The Start and Restart of Play — p.97 "Kick-off Procedure"
    (101, 108, 9),   # Ball in and out of Play / Determining the Outcome
    (109, 114, 11),  # Offside
    (115, 130, 12),  # Fouls and Misconduct
    (131, 134, 13),  # Free Kicks
    (135, 140, 14),  # The Penalty Kick
    (141, 144, 15),  # The Throw-in
    (145, 148, 16),  # The Goal Kick
    (149, 154, 17),  # The Corner Kick
]
# Verification note:
# Law 6 previously ran to p.96, swallowing Law 7's pages 93-94.
# Law 7 previously mapped to (97,100) — the same range as Law 8 — so Law 7
# was always returned first and Law 8 was never assigned.
# Fixed: Law 6 ends p.92, Law 7 is p.93-96, Law 8 is p.97-100. No overlap.
_APPENDIX_START = 155   # pages ≥ this are additional guidance / change summaries


def law_from_page(page: int | None) -> int | None:
    """Map a page number to a law number using the known page ranges."""
    if page is None or page >= _APPENDIX_START:
        return None
    for lo, hi, law in _LAW_PAGE_RANGES:
        if lo <= page <= hi:
            return law
    return None


def make_id(law_num: int | None, heading: str, idx: int) -> str:
    slug = re.sub(r'[^a-z0-9]+', '_', heading.lower()).strip('_')[:48]
    suffix = hashlib.md5(f"{law_num}:{heading}:{idx}".encode()).hexdigest()[:6]
    prefix = f"law{law_num}_" if law_num else "preamble_"
    return f"{prefix}{slug}_{suffix}"


def main():
    show_law = None
    if "--show-law" in sys.argv:
        idx = sys.argv.index("--show-law")
        show_law = int(sys.argv[idx + 1])

    print("Loading Docling (first run downloads ~500 MB of layout models) …")
    from docling.document_converter import DocumentConverter
    from docling.chunking import HybridChunker

    print(f"Converting {PDF_PATH.name} …")
    converter = DocumentConverter()
    result    = converter.convert(str(PDF_PATH))

    print("Chunking …")
    chunker = HybridChunker(max_tokens=400, merge_peers=True)
    raw_chunks = list(chunker.chunk(result.document))

    print(f"Raw chunks from Docling: {len(raw_chunks)}")

    records = []
    for i, chunk in enumerate(raw_chunks):
        # Docling chunk metadata: headings list, page info
        meta     = chunk.meta
        headings = []
        if hasattr(meta, 'headings') and meta.headings:
            headings = [h for h in meta.headings if h]
        elif hasattr(meta, 'doc_items'):
            # Fallback: extract heading text from doc_items
            for item in meta.doc_items:
                if hasattr(item, 'label') and str(item.label) in ('section_header', 'title'):
                    if hasattr(item, 'text'):
                        headings.append(item.text)

        # Page number
        page = None
        if hasattr(meta, 'doc_items') and meta.doc_items:
            try:
                prov = meta.doc_items[0].prov
                if prov:
                    page = prov[0].page_no
            except (AttributeError, IndexError):
                pass

        # Prefer heading-derived law number; fall back to page-range lookup.
        # Page-range lookup is the primary mechanism for most of the main law
        # text because the IFAB document uses section headings without "Law N"
        # prefix in the authoritative text section.
        law_from_heading = extract_law_number(headings)
        law_num = law_from_heading or law_from_page(page)

        # Mark appendix/guidance chunks so they can be filtered if needed.
        is_appendix = (page is not None and page >= _APPENDIX_START)

        heading_str = " › ".join(headings) if headings else ""

        records.append({
            "id":          make_id(law_num, heading_str, i),
            "law_number":  law_num,
            "heading":     heading_str,
            "text":        chunk.text.strip(),
            "page":        page,
            "is_appendix": is_appendix,
        })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    # ── Summary ───────────────────────────────────────────────────────────
    total = len(records)
    by_law = {}
    for r in records:
        k = r["law_number"]
        by_law.setdefault(k, []).append(r)

    print(f"\n{'═'*60}")
    print(f"Total chunks: {total}")
    print(f"\nChunks per law:")
    for k in sorted((k for k in by_law if k is not None)):
        n = len(by_law[k])
        first_heading = by_law[k][0]["heading"].split(" › ")[-1][:50]
        print(f"  Law {k:>2}: {n:>3} chunks  — {first_heading}")
    nulls = len(by_law.get(None, []))
    if nulls:
        print(f"  (no law tag): {nulls} chunks (preamble/appendix)")

    print(f"\nOutput: {OUT_PATH}")

    # ── Optional: print all chunks for a specific law ─────────────────────
    if show_law is not None:
        print(f"\n{'═'*60}")
        print(f"ALL CHUNKS FOR LAW {show_law}")
        print(f"{'═'*60}")
        law_chunks = by_law.get(show_law, [])
        if not law_chunks:
            print(f"  No chunks found for Law {show_law}")
        for c in law_chunks:
            print(f"\n[{c['id']}]  page={c['page']}")
            print(f"  Heading: {c['heading']}")
            print(f"  Text ({len(c['text'])} chars):")
            print("  " + c['text'].replace('\n', '\n  '))
            print("-" * 60)


if __name__ == "__main__":
    main()

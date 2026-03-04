#!/usr/bin/env python3
"""
FRS Announcement Semantic Search
Searches the Qdrant vector DB of FRS announcement chunks using sentence-transformers.

Usage:
  python3 search_announcements.py "query text" [--top N] [--collection NAME] [--threshold SCORE] [--source-filter PATTERN]

Collections:
  forrestania_filings         - 8,379 chunks from all extracted filings (default)
  forrestania_filings_hybrid  - 2,612 hybrid search chunks
  frs_resource_model          - 12 resource model entries
  frs_tenement_registry       - 120 tenement registry entries
  frs_reference_notes         - 1 reference note
"""

import argparse
import json
import sys
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QDRANT_PATH = os.path.join(BASE_DIR, "ingestion", "processed", "vectors", "qdrant_data")
MODEL_NAME = "all-MiniLM-L6-v2"

def search(query, collection="forrestania_filings", top_k=10, threshold=0.0, source_filter=None):
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchText
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_NAME)
    client = QdrantClient(path=QDRANT_PATH)

    vec = model.encode(query).tolist()

    query_filter = None
    if source_filter:
        query_filter = Filter(
            must=[FieldCondition(key="source_file", match=MatchText(text=source_filter))]
        )

    results = client.query_points(
        collection_name=collection,
        query=vec,
        limit=top_k,
        with_payload=True,
        query_filter=query_filter,
    )

    output = []
    for r in results.points:
        p = r.payload or {}
        if r.score < threshold:
            continue
        entry = {
            "score": round(r.score, 4),
            "source_file": p.get("source_file", ""),
            "chunk_index": p.get("chunk_index", ""),
            "page_start": p.get("page_start", ""),
            "page_end": p.get("page_end", ""),
            "text": p.get("text", ""),
        }
        output.append(entry)
    return output


def format_results(results, fmt="text"):
    if fmt == "json":
        return json.dumps(results, indent=2)

    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"--- Result {i} (score: {r['score']}) ---")
        lines.append(f"Source: {r['source_file']}")
        if r.get("page_start"):
            lines.append(f"Pages: {r['page_start']}-{r.get('page_end', r['page_start'])}")
        lines.append(f"Chunk: {r.get('chunk_index', '?')}")
        lines.append("")
        lines.append(r["text"][:2000])
        lines.append("")
    if not results:
        lines.append("No results found.")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Semantic search over FRS announcements")
    parser.add_argument("query", help="Search query text")
    parser.add_argument("--top", type=int, default=10, help="Number of results (default: 10)")
    parser.add_argument("--collection", default="forrestania_filings",
                        help="Qdrant collection name (default: forrestania_filings)")
    parser.add_argument("--threshold", type=float, default=0.0,
                        help="Minimum similarity score (default: 0.0)")
    parser.add_argument("--source-filter", default=None,
                        help="Filter results to source files matching this text")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    results = search(
        query=args.query,
        collection=args.collection,
        top_k=args.top,
        threshold=args.threshold,
        source_filter=args.source_filter,
    )

    fmt = "json" if args.json else "text"
    print(format_results(results, fmt))


if __name__ == "__main__":
    main()

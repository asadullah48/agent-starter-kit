"""A tiny keyword-search tool over data/knowledge_base.json.

Stands in for a real retrieval tool (a vector DB, a docs search API, ...).
Swap the implementation here without touching the agent loop or the
tool registry -- that's the point of keeping tools in their own module.
"""

from __future__ import annotations

import json
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "knowledge_base.json"

TOOL_DEF = {
    "name": "search_knowledge_base",
    "description": (
        "Search the local knowledge base for entries relevant to a query. "
        "Returns up to `top_k` matching entries with their text."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to search for."},
            "top_k": {
                "type": "integer",
                "description": "Maximum number of results to return.",
                "default": 3,
            },
        },
        "required": ["query"],
    },
}


def _load_entries() -> list[dict]:
    if not _DATA_PATH.exists():
        return []
    with _DATA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def search_knowledge_base(query: str, top_k: int = 3) -> str:
    """Return the top_k entries whose title or text contain a query word."""
    words = [w.lower() for w in query.split() if w]
    scored = []
    for entry in _load_entries():
        haystack = f"{entry.get('title', '')} {entry.get('text', '')}".lower()
        score = sum(haystack.count(w) for w in words)
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    top = [entry for _, entry in scored[:top_k]]

    if not top:
        return "No matching entries found."
    return "\n\n".join(f"# {e['title']}\n{e['text']}" for e in top)

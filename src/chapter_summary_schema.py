"""Shared schema contract for chapter summary JSON data."""

from __future__ import annotations

from typing import Any, Dict, List

SCHEMA_VERSION = "1.0"

# Canonical persisted shape.
# {
#   "schema_version": "1.0",
#   "chapters": [
#       {
#           "key": "1",
#           "title": "Chapter 1",
#           "summary": "...",
#           "quotes": ["...", "..."]
#       }
#   ]
# }


class ChapterSummarySchemaError(ValueError):
    """Raised when payload does not satisfy the chapter-summary schema."""


def _normalize_quotes(raw: Any) -> List[str]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ChapterSummarySchemaError("'quotes' must be a list of strings.")

    out: List[str] = []
    seen = set()
    for item in raw:
        if not isinstance(item, str):
            raise ChapterSummarySchemaError("Each quote must be a string.")
        quote = item.strip()
        if not quote:
            continue
        key = quote.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(quote)
    return out


def _normalize_key(raw: Any) -> str:
    if raw is None:
        raise ChapterSummarySchemaError("Each chapter must include a non-empty 'key'.")
    key = str(raw).strip()
    if not key:
        raise ChapterSummarySchemaError("Each chapter must include a non-empty 'key'.")
    return key


def _normalize_chapter(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise ChapterSummarySchemaError("Each chapter entry must be an object.")

    key = _normalize_key(raw.get("key"))
    title = str(raw.get("title", "")).strip()
    summary = str(raw.get("summary", "")).strip()
    if not title:
        title = f"Chapter {key}"

    return {
        "key": key,
        "title": title,
        "summary": summary,
        "quotes": _normalize_quotes(raw.get("quotes", [])),
    }


def build_schema_document(chapters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate and return canonical schema document."""
    if not isinstance(chapters, list):
        raise ChapterSummarySchemaError("'chapters' must be a list.")

    normalized = [_normalize_chapter(ch) for ch in chapters]
    return {"schema_version": SCHEMA_VERSION, "chapters": normalized}


def parse_schema_document(payload: Any) -> Dict[str, Any]:
    """Validate a persisted JSON payload in canonical shape."""
    if not isinstance(payload, dict):
        raise ChapterSummarySchemaError("Top-level JSON must be an object.")

    schema_version = str(payload.get("schema_version", "")).strip()
    if schema_version != SCHEMA_VERSION:
        raise ChapterSummarySchemaError(
            f"Unsupported or missing schema_version '{schema_version}'. Expected '{SCHEMA_VERSION}'."
        )

    chapters = payload.get("chapters")
    if not isinstance(chapters, list):
        raise ChapterSummarySchemaError("Top-level 'chapters' must be a list.")

    return build_schema_document(chapters)


def parser_summaries_to_document(raw_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Transform parser output into canonical chapter-summary schema."""
    chapters: List[Dict[str, Any]] = []

    for idx, item in enumerate(raw_summaries or [], start=1):
        if not isinstance(item, dict):
            raise ChapterSummarySchemaError("Parser summaries must be objects.")

        key = item.get("chapter_number") or str(idx)
        summary_sentences = item.get("summary_sentences", [])
        if isinstance(summary_sentences, list):
            summary = " ".join(str(s).strip() for s in summary_sentences if str(s).strip())
        else:
            summary = str(summary_sentences).strip()

        chapters.append(
            {
                "key": str(key),
                "title": str(item.get("title") or f"Chapter {key}").strip(),
                "summary": summary,
                "quotes": item.get("quote_candidates", []),
            }
        )

    return build_schema_document(chapters)


def legacy_map_to_document(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Transform legacy key->chapter map into canonical schema document."""
    chapters: List[Dict[str, Any]] = []
    for key, value in payload.items():
        if not isinstance(value, dict):
            continue
        chapters.append(
            {
                "key": str(key),
                "title": str(value.get("title", f"Chapter {key}")),
                "summary": str(value.get("summary", "")),
                "quotes": value.get("quotes", []),
            }
        )
    return build_schema_document(chapters)


def document_to_chapter_map(doc: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Convert canonical document to UI-friendly key-indexed map."""
    parsed = parse_schema_document(doc)
    return {
        chapter["key"]: {
            "title": chapter["title"],
            "summary": chapter["summary"],
            "quotes": chapter["quotes"],
        }
        for chapter in parsed["chapters"]
    }

"""Shared schema contracts for chapter metadata and parser helper JSON data."""

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


CHAPTER_REQUIRED_FIELDS = [
    "title",
    "learning_objective",
    "summary",
    "quotes",
    "market_objects",
    "equations",
    "derivation_steps",
    "failure_modes",
    "prerequisites",
    "exports_to_next_chapter",
]

CHAPTER_ENRICHED_OPTIONAL_FIELDS = [
    "core_claim",
    "technical_equations",
    "step_by_step_derivation",
    "interactive_lab",
    "trade_interpretation",
    "failure_modes_model_risk",
    "checkpoint_assessment",
    "exports",
]


def parse_chapters_map(payload: Any) -> Dict[str, Dict[str, Any]]:
    """Validate and normalize the primary chapter content map (keys '1'..'18')."""
    if not isinstance(payload, dict):
        raise ChapterSummarySchemaError("Top-level chapter content JSON must be an object keyed by chapter number.")

    normalized: Dict[str, Dict[str, Any]] = {}
    expected_keys = {str(i) for i in range(1, 19)}
    actual_keys = set(payload.keys())
    missing = sorted(expected_keys - actual_keys, key=int)
    extra = sorted(k for k in actual_keys - expected_keys)

    if missing:
        raise ChapterSummarySchemaError(f"Missing chapter keys in chapter content JSON: {missing}.")
    if extra:
        raise ChapterSummarySchemaError(f"Unexpected chapter keys in chapter content JSON: {extra}.")

    for key in sorted(expected_keys, key=int):
        chapter = payload.get(key)
        if not isinstance(chapter, dict):
            raise ChapterSummarySchemaError(f"Chapter '{key}' must be an object.")

        missing_fields = [field for field in CHAPTER_REQUIRED_FIELDS if field not in chapter]
        if missing_fields:
            raise ChapterSummarySchemaError(
                f"Chapter '{key}' is missing required fields: {missing_fields}."
            )

        normalized[key] = {
            "title": str(chapter.get("title", "")).strip() or f"Chapter {key}",
            "learning_objective": str(chapter.get("learning_objective", "")).strip(),
            "summary": str(chapter.get("summary", "")).strip(),
            "quotes": _normalize_string_list(chapter.get("quotes"), "quotes"),
            "market_objects": _normalize_string_list(chapter.get("market_objects"), "market_objects"),
            "equations": _normalize_object_list(chapter.get("equations"), "equations"),
            "derivation_steps": _normalize_string_list(chapter.get("derivation_steps"), "derivation_steps"),
            "failure_modes": _normalize_object_list(chapter.get("failure_modes"), "failure_modes"),
            "prerequisites": _normalize_string_list(chapter.get("prerequisites"), "prerequisites"),
            "exports_to_next_chapter": _normalize_string_list(
                chapter.get("exports_to_next_chapter"), "exports_to_next_chapter"
            ),
            "core_claim": str(chapter.get("core_claim", "")).strip(),
            "technical_equations": _normalize_object_list(
                chapter.get("technical_equations"), "technical_equations"
            ),
            "step_by_step_derivation": _normalize_string_list(
                chapter.get("step_by_step_derivation"), "step_by_step_derivation"
            ),
            "interactive_lab": _normalize_json_value(chapter.get("interactive_lab"), "interactive_lab"),
            "trade_interpretation": _normalize_string_list(
                chapter.get("trade_interpretation"), "trade_interpretation"
            ),
            "failure_modes_model_risk": _normalize_object_list(
                chapter.get("failure_modes_model_risk"), "failure_modes_model_risk"
            ),
            "checkpoint_assessment": _normalize_json_value(
                chapter.get("checkpoint_assessment"), "checkpoint_assessment"
            ),
            "exports": _normalize_json_value(chapter.get("exports"), "exports"),
        }

    return normalized


def _normalize_json_value(raw: Any, field_name: str) -> Any:
    if raw is None:
        return {}
    if isinstance(raw, (dict, list, str, int, float, bool)):
        return raw
    raise ChapterSummarySchemaError(
        f"'{field_name}' must be a JSON-compatible value (object, list, scalar, or null)."
    )


def _normalize_object_list(raw: Any, field_name: str) -> List[Dict[str, Any]]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ChapterSummarySchemaError(f"'{field_name}' must be a list of objects.")
    out: List[Dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ChapterSummarySchemaError(f"Each item in '{field_name}' must be an object.")
        out.append(item)
    return out


def _normalize_string_list(raw: Any, field_name: str) -> List[str]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ChapterSummarySchemaError(f"'{field_name}' must be a list of strings.")
    out: List[str] = []
    for item in raw:
        if not isinstance(item, str):
            raise ChapterSummarySchemaError(f"Each item in '{field_name}' must be a string.")
        value = item.strip()
        if value:
            out.append(value)
    return out


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

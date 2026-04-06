import pytest

from src.chapter_summary_schema import (
    CHAPTER_REQUIRED_FIELDS,
    ChapterSummarySchemaError,
    document_to_chapter_map,
    legacy_map_to_document,
    parse_chapters_map,
    parse_schema_document,
    parser_summaries_to_document,
)


def test_parser_summaries_are_transformed_to_schema_document():
    raw = [
        {
            "chapter_number": "1",
            "title": "Duration",
            "summary_sentences": ["Duration measures first-order risk.", "Convexity refines it."],
            "quote_candidates": ["Carry matters.", "Carry matters.", ""],
        }
    ]

    doc = parser_summaries_to_document(raw)

    assert doc["schema_version"] == "1.0"
    assert doc["chapters"][0]["key"] == "1"
    assert doc["chapters"][0]["summary"] == "Duration measures first-order risk. Convexity refines it."
    assert doc["chapters"][0]["quotes"] == ["Carry matters."]


def test_legacy_map_can_be_normalized_to_schema_document():
    legacy = {
        "1": {
            "title": "Chapter 1",
            "summary": "Summary",
            "quotes": ["A quote"],
        }
    }

    doc = legacy_map_to_document(legacy)
    mapped = document_to_chapter_map(doc)

    assert mapped["1"]["title"] == "Chapter 1"
    assert mapped["1"]["summary"] == "Summary"
    assert mapped["1"]["quotes"] == ["A quote"]


def test_parse_schema_document_rejects_wrong_version():
    with pytest.raises(ChapterSummarySchemaError):
        parse_schema_document({"schema_version": "0.9", "chapters": []})


def test_parse_chapters_map_accepts_complete_1_to_18_payload():
    payload = {
        str(i): {
            field: [] if field.endswith("s") else "x"
            for field in CHAPTER_REQUIRED_FIELDS
        }
        for i in range(1, 19)
    }
    # Fix list-vs-object fields with valid values.
    for i in range(1, 19):
        payload[str(i)]["quotes"] = ["Quote"]
        payload[str(i)]["market_objects"] = ["Object"]
        payload[str(i)]["equations"] = [{"name": "Eq", "equation": "x=y"}]
        payload[str(i)]["derivation_steps"] = ["Step"]
        payload[str(i)]["failure_modes"] = [{"mode": "m", "mitigation": "fix"}]
        payload[str(i)]["prerequisites"] = ["Pre"]
        payload[str(i)]["exports_to_next_chapter"] = ["signal"]

    parsed = parse_chapters_map(payload)
    assert set(parsed.keys()) == {str(i) for i in range(1, 19)}
    assert parsed["1"]["equations"][0]["name"] == "Eq"


def test_parse_chapters_map_rejects_missing_chapter_key():
    payload = {
        str(i): {
            "title": "T",
            "learning_objective": "L",
            "summary": "S",
            "quotes": [],
            "market_objects": [],
            "equations": [],
            "derivation_steps": [],
            "failure_modes": [],
            "prerequisites": [],
            "exports_to_next_chapter": [],
        }
        for i in range(1, 18)
    }

    with pytest.raises(ChapterSummarySchemaError):
        parse_chapters_map(payload)

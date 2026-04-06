import pytest

from src.chapter_summary_schema import (
    ChapterSummarySchemaError,
    document_to_chapter_map,
    legacy_map_to_document,
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

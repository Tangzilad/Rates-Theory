import json
import re
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def parser_module():
    """Skip cleanly when parser module is not yet available in the repo."""
    return pytest.importorskip("pdf_parser", reason="pdf_parser module is required for parser tests")


@pytest.fixture
def synthetic_text():
    return (
        "Preface text that should be ignored by chapter splitting.\n\n"
        "CHAPTER 1 Duration and Convexity\n"
        "Duration measures sensitivity to rate moves. "
        "Convexity refines the estimate for larger shifts. "
        "Portfolio hedges may target both metrics.\n\n"
        "CHAPTER 2 Curve Trades\n"
        "Steepeners and flatteners express relative-value views. "
        "Carry and roll-down can drive realized returns. "
        "Risk limits and liquidity matter for implementation."
    )


@pytest.fixture
def expected_chapter_pattern():
    # Anchored, case-insensitive chapter heading detection pattern.
    return re.compile(r"^CHAPTER\s+\d+\b.*$", re.IGNORECASE | re.MULTILINE)


def _resolve_callable(module, *candidate_names):
    for name in candidate_names:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    pytest.skip(f"None of the expected callables were found: {candidate_names}")


def _chapter_id(chapter_obj):
    if isinstance(chapter_obj, dict):
        return chapter_obj.get("id") or chapter_obj.get("chapter_id")
    return getattr(chapter_obj, "id", None) or getattr(chapter_obj, "chapter_id", None)


def _chapter_title(chapter_obj):
    if isinstance(chapter_obj, dict):
        return chapter_obj.get("title")
    return getattr(chapter_obj, "title", None)


def test_chapter_heading_regex_recognition(synthetic_text, expected_chapter_pattern):
    matches = expected_chapter_pattern.findall(synthetic_text)

    assert len(matches) == 2
    assert matches[0].startswith("CHAPTER 1")
    assert matches[1].startswith("CHAPTER 2")


def test_chapter_split_count_and_metadata_fields(parser_module, synthetic_text):
    split_fn = _resolve_callable(
        parser_module,
        "split_into_chapters",
        "split_chapters",
        "extract_chapters",
    )

    chapters = split_fn(synthetic_text)

    assert isinstance(chapters, list)
    assert len(chapters) == 2

    first, second = chapters
    assert _chapter_id(first) is not None
    assert _chapter_id(second) is not None
    assert _chapter_title(first)
    assert _chapter_title(second)


def test_summary_generation_sentence_length_constraints(parser_module):
    summarize_fn = _resolve_callable(
        parser_module,
        "generate_summary",
        "summarize_text",
        "summarize_chapter",
    )

    source_text = (
        "Bond prices and yields move inversely. "
        "Duration estimates first-order sensitivity to yield changes. "
        "Convexity captures curvature effects and improves approximation quality. "
        "Traders monitor carry, roll-down, and spread behavior in addition to outright rates. "
        "Risk management combines scenario analysis with position limits. "
        "Liquidity constraints can dominate execution outcomes during stress."
    )

    summary = summarize_fn(source_text)
    assert isinstance(summary, str)

    # Count sentence-like segments while ignoring trailing punctuation artifacts.
    sentences = [s.strip() for s in re.split(r"[.!?]+", summary) if s.strip()]

    assert 3 <= len(sentences) <= 5


def test_quote_extraction_excludes_blank_and_duplicates(parser_module):
    extract_quotes_fn = _resolve_callable(
        parser_module,
        "extract_quotes",
        "find_quotes",
    )

    sample_text = (
        'The desk note says "Carry matters." '
        'Analyst repeats "Carry matters." '
        'Then adds "Liquidity can vanish quickly." '
        'Ignore empty quotes like "".'
    )

    quotes = extract_quotes_fn(sample_text)

    assert isinstance(quotes, list)
    assert all(isinstance(q, str) for q in quotes)
    assert all(q.strip() for q in quotes)
    assert len(quotes) == len(set(quotes))


def test_json_serialization_writes_expected_schema_keys(parser_module, tmp_path):
    serialize_fn = _resolve_callable(
        parser_module,
        "serialize_chapters_to_json",
        "save_chapters_json",
        "write_chapters_json",
    )

    chapters = [
        {
            "id": 1,
            "title": "Duration and Convexity",
            "summary": "A concise chapter summary.",
            "quotes": ["Carry matters.", "Liquidity can vanish quickly."],
        },
        {
            "id": 2,
            "title": "Curve Trades",
            "summary": "Another concise chapter summary.",
            "quotes": ["Steepeners express directional slope views."],
        },
    ]

    output_path = tmp_path / "chapters.json"
    result = serialize_fn(chapters, output_path)

    if isinstance(result, (str, Path)):
        output_path = Path(result)

    assert output_path.exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert payload

    for item in payload:
        assert "id" in item
        assert "title" in item
        assert "summary" in item
        assert "quotes" in item
        assert isinstance(item["quotes"], list)

"""Tests for the ``src.pdf_parser`` module class-based API."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

pytest.importorskip("pdfplumber", reason="pdfplumber is required for src.pdf_parser")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pdf_parser import BookParser


def _build_parser_with_pages(*pages: str) -> BookParser:
    """Create a BookParser test double without opening a real PDF file."""
    parser = BookParser.__new__(BookParser)
    parser.pdf_path = "<synthetic>"
    parser.pdf = None
    parser.pages_text = list(pages)
    parser.chapters = None
    parser.chapter_summaries = None
    return parser


def test_chapter_heading_regex_recognition() -> None:
    synthetic_text = (
        "Preface text that should be ignored by chapter splitting.\n\n"
        "CHAPTER 1 Duration and Convexity\n"
        "Duration measures sensitivity to rate moves.\n\n"
        "CHAPTER 2 Curve Trades\n"
        "Steepeners and flatteners express relative-value views."
    )

    matches = BookParser.CHAPTER_PATTERN.findall(synthetic_text)

    assert len(matches) == 2
    assert matches[0][0] == "1"
    assert matches[1][0] == "2"


def test_split_into_chapters_count_and_metadata_fields() -> None:
    parser = _build_parser_with_pages(
        "Preface text that should be ignored by chapter splitting.\n\n"
        "CHAPTER 1 Duration and Convexity\n"
        "Duration measures sensitivity to rate moves."
        " Convexity refines the estimate for larger shifts.",
        "CHAPTER 2 Curve Trades\n"
        "Steepeners and flatteners express relative-value views."
        " Carry and roll-down can drive realized returns.",
    )

    chapters = parser.split_into_chapters()

    assert isinstance(chapters, list)
    assert len(chapters) == 2

    first, second = chapters
    assert first["chapter_number"] == "1"
    assert second["chapter_number"] == "2"
    assert first["title"] == "Duration and Convexity"
    assert second["title"] == "Curve Trades"
    assert "Duration measures sensitivity" in first["body"]
    assert "Steepeners and flatteners" in second["body"]


def test_summarise_chapters_sentence_length_constraints() -> None:
    parser = _build_parser_with_pages()
    parser.chapters = [
        {
            "chapter_number": "1",
            "title": "Summary Test",
            "body": (
                "Bond prices and yields move inversely. "
                "Duration estimates first-order sensitivity to yield changes. "
                "Convexity captures curvature effects and improves approximation quality. "
                "Traders monitor carry, roll-down, and spread behavior in addition to rates. "
                "Risk management combines scenario analysis with position limits. "
                "Liquidity constraints can dominate execution outcomes during stress."
            ),
        }
    ]

    summaries = parser.summarise_chapters()

    assert len(summaries) == 1
    summary_sentences = summaries[0]["summary_sentences"]
    assert isinstance(summary_sentences, list)
    assert 3 <= len(summary_sentences) <= 5


def test_quote_candidates_excludes_blank_and_duplicates() -> None:
    parser = _build_parser_with_pages()
    deduped = parser._dedupe_preserve_order(
        [
            "Carry matters.",
            "Carry matters.",
            "  ",
            "Liquidity can vanish quickly.",
            "liquidity can   vanish quickly.  ",
        ]
    )

    assert deduped == ["Carry matters.", "Liquidity can vanish quickly."]


def test_save_summaries_json_writes_expected_schema_keys(tmp_path) -> None:
    parser = _build_parser_with_pages()
    parser.chapter_summaries = [
        {
            "chapter_number": "1",
            "title": "Duration and Convexity",
            "summary_sentences": ["A concise chapter summary."],
            "quote_candidates": ["Carry matters.", "Liquidity can vanish quickly."],
        },
        {
            "chapter_number": "2",
            "title": "Curve Trades",
            "summary_sentences": ["Another concise chapter summary."],
            "quote_candidates": ["Steepeners express directional slope views."],
        },
    ]

    output_path = tmp_path / "chapter_summaries.json"
    result = parser.save_summaries_json(str(output_path))

    assert result == str(output_path)
    assert output_path.exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert len(payload) == 2

    for item in payload:
        assert "chapter_number" in item
        assert "title" in item
        assert "summary_sentences" in item
        assert "quote_candidates" in item
        assert isinstance(item["summary_sentences"], list)
        assert isinstance(item["quote_candidates"], list)


def test_segment_sentences_filters_short_noise() -> None:
    parser = _build_parser_with_pages()
    sentences = parser._segment_sentences(
        'Short. "x". Duration helps estimate risk exposure under curve shifts. 12345. '
        "Liquidity conditions matter during stressed markets."
    )

    assert len(sentences) == 2
    assert all(len(re.findall(r"[A-Za-z]", s)) >= 8 for s in sentences)

"""Tests for PDF parser module."""

from src.pdf_parser import parse_pdf


def test_parse_pdf_returns_placeholder_dict() -> None:
    result = parse_pdf("data/Fixed Income Relative Value Analysis.pdf")
    assert result["status"] == "not_implemented"

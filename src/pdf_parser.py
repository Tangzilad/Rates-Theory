"""PDF parsing and chapter summarisation utilities."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

import pdfplumber
from src.chapter_summary_schema import (
    ChapterSummarySchemaError,
    parser_summaries_to_document,
)


class BookParser:
    """Parse books from PDF and produce deterministic chapter summaries."""

    CHAPTER_PATTERN = re.compile(
        r"^\s*(?:CHAPTER|Chapter)\s+(\d+)\b[\s:\-–—]*(.*)$", re.IGNORECASE
    )
    HEADING_PATTERN = re.compile(
        r"^(?:[A-Z][A-Z\s\-\d,:.'&]{4,}|(?:CHAPTER|PART|SECTION)\b.*)$"
    )

    STOPWORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "have",
        "he",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "that",
        "the",
        "their",
        "there",
        "they",
        "this",
        "to",
        "was",
        "were",
        "which",
        "with",
        "we",
        "you",
        "your",
        "i",
        "our",
        "not",
        "but",
        "if",
        "than",
        "then",
        "into",
        "about",
        "such",
        "can",
        "could",
        "will",
        "would",
        "should",
        "may",
        "might",
        "also",
        "more",
        "most",
        "other",
        "some",
        "any",
    }

    def __init__(self, pdf_path: str | Path):
        """Load a PDF from disk using pdfplumber."""
        self.pdf_path = str(pdf_path)
        self.pdf = pdfplumber.open(self.pdf_path)
        self.pages_text: Optional[List[str]] = None
        self.chapters: Optional[List[Dict[str, str]]] = None
        self.chapter_summaries: Optional[List[Dict[str, object]]] = None

    def extract_text_by_page(self) -> List[str]:
        """Extract text from each page with OCR-noise cleanup."""
        texts: List[str] = []
        for page in self.pdf.pages:
            raw = page.extract_text() or ""
            cleaned = self._clean_page_text(raw)
            texts.append(cleaned)
        self.pages_text = texts
        return texts

    def extract_toc(self) -> List[Dict[str, object]]:
        """Infer table-of-contents-style entries from heading/chapter-like lines."""
        if self.pages_text is None:
            self.extract_text_by_page()

        toc_entries: List[Dict[str, object]] = []

        for page_number, page_text in enumerate(self.pages_text or [], start=1):
            for line in page_text.splitlines():
                normalized = self._normalize_ocr_line(line)
                if not normalized:
                    continue

                chapter_match = self.CHAPTER_PATTERN.match(normalized)
                if chapter_match:
                    chapter_number = int(chapter_match.group(1))
                    title = chapter_match.group(2).strip() or f"Chapter {chapter_number}"
                    toc_entries.append(
                        {
                            "page": page_number,
                            "chapter_number": chapter_number,
                            "title": title,
                            "line": normalized,
                        }
                    )
                    continue

                if self._is_heading_like(normalized):
                    toc_entries.append(
                        {
                            "page": page_number,
                            "chapter_number": None,
                            "title": normalized,
                            "line": normalized,
                        }
                    )

        deduped: List[Dict[str, object]] = []
        seen = set()
        for entry in toc_entries:
            key = (
                entry["chapter_number"],
                str(entry["title"]).lower(),
                entry["page"],
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(entry)

        return deduped

    def split_into_chapters(self) -> List[Dict[str, str]]:
        """Split full text into chapters preserving chapter number/title/body."""
        if self.pages_text is None:
            self.extract_text_by_page()

        all_text = "\n".join(self.pages_text or [])
        lines = [self._normalize_ocr_line(line) for line in all_text.splitlines()]

        chapters: List[Dict[str, str]] = []
        current: Optional[Dict[str, str]] = None
        body_lines: List[str] = []

        for line in lines:
            if not line:
                if body_lines and body_lines[-1] != "":
                    body_lines.append("")
                continue

            chapter_match = self.CHAPTER_PATTERN.match(line)
            if chapter_match:
                if current is not None:
                    current["body"] = self._compact_body(body_lines)
                    chapters.append(current)

                chapter_number = chapter_match.group(1)
                chapter_title = chapter_match.group(2).strip() or f"Chapter {chapter_number}"
                current = {
                    "chapter_number": chapter_number,
                    "title": chapter_title,
                    "body": "",
                }
                body_lines = []
                continue

            if current is not None:
                body_lines.append(line)

        if current is not None:
            current["body"] = self._compact_body(body_lines)
            chapters.append(current)

        if not chapters:
            fallback_body = self._compact_body([line for line in lines if line])
            chapters = [
                {
                    "chapter_number": "0",
                    "title": "Full Text",
                    "body": fallback_body,
                }
            ]

        self.chapters = chapters
        return chapters

    def summarise_chapters(self) -> List[Dict[str, object]]:
        """Create heuristic summaries and quote candidates for each chapter."""
        if self.chapters is None:
            self.split_into_chapters()

        summaries: List[Dict[str, object]] = []

        for chapter in self.chapters or []:
            body = chapter.get("body", "")
            sentences = self._segment_sentences(body)

            if not sentences:
                summaries.append(
                    {
                        "chapter_number": chapter.get("chapter_number"),
                        "title": chapter.get("title"),
                        "summary_sentences": [],
                        "quote_candidates": [],
                    }
                )
                continue

            tokenized = [self._tokenize(sentence) for sentence in sentences]
            frequencies = Counter()
            for tokens in tokenized:
                frequencies.update(tokens)

            if not frequencies:
                summaries.append(
                    {
                        "chapter_number": chapter.get("chapter_number"),
                        "title": chapter.get("title"),
                        "summary_sentences": sentences[:3],
                        "quote_candidates": self._dedupe_preserve_order(sentences[:5]),
                    }
                )
                continue

            max_freq = max(frequencies.values()) or 1
            normalized_freq = {w: c / max_freq for w, c in frequencies.items()}

            scored_sentences = []
            for idx, (sentence, tokens) in enumerate(zip(sentences, tokenized)):
                score = self._score_sentence(sentence, tokens, normalized_freq)
                scored_sentences.append((idx, sentence, score))

            top_n = max(3, min(5, len(sentences)))
            top_ranked = sorted(scored_sentences, key=lambda x: x[2], reverse=True)[:top_n]
            top_ranked_sorted = sorted(top_ranked, key=lambda x: x[0])
            summary_sentences = [s for _, s, _ in top_ranked_sorted]

            quote_count = min(8, len(scored_sentences))
            quotes_ranked = sorted(scored_sentences, key=lambda x: x[2], reverse=True)[:quote_count]
            quote_candidates = self._dedupe_preserve_order([s for _, s, _ in quotes_ranked])

            summaries.append(
                {
                    "chapter_number": chapter.get("chapter_number"),
                    "title": chapter.get("title"),
                    "summary_sentences": summary_sentences,
                    "quote_candidates": quote_candidates,
                }
            )

        self.chapter_summaries = summaries
        return summaries

    def save_summaries_json(self, output_path: str = "data/chapter_summaries.json") -> str:
        """Save chapter summaries to a JSON file and return file path."""
        if self.chapter_summaries is None:
            self.summarise_chapters()

        try:
            schema_document = parser_summaries_to_document(self.chapter_summaries or [])
        except ChapterSummarySchemaError as exc:
            raise ValueError(f"Could not serialize chapter summaries: {exc}") from exc

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            json.dump(schema_document, handle, indent=2, ensure_ascii=False)
        return str(output)

    @staticmethod
    def _normalize_ocr_line(line: str) -> str:
        line = (line or "").replace("\x0c", " ").strip()
        if not line:
            return ""

        line = re.sub(r"\s+", " ", line)

        line = re.sub(r"\b([A-Za-z])\s+(?=[A-Za-z]\b)", r"\1", line)

        if re.fullmatch(r"[\W_\d]+", line):
            return ""

        return line

    def _clean_page_text(self, text: str) -> str:
        lines = [self._normalize_ocr_line(line) for line in (text or "").splitlines()]
        filtered = [line for line in lines if line]
        return "\n".join(filtered)

    @staticmethod
    def _compact_body(lines: List[str]) -> str:
        body = "\n".join(lines)
        body = re.sub(r"\n{3,}", "\n\n", body)
        return body.strip()

    def _is_heading_like(self, line: str) -> bool:
        if len(line) < 4 or len(line) > 120:
            return False
        if re.search(r"\.{3,}\s*\d+$", line):
            return True
        if self.HEADING_PATTERN.match(line):
            return True
        uppercase_ratio = sum(1 for ch in line if ch.isupper()) / max(
            sum(1 for ch in line if ch.isalpha()), 1
        )
        return uppercase_ratio > 0.75 and len(line.split()) <= 10

    @staticmethod
    def _segment_sentences(text: str) -> List[str]:
        cleaned = re.sub(r"\s+", " ", text or "").strip()
        if not cleaned:
            return []

        raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", cleaned)
        sentences = []
        for sentence in raw_sentences:
            s = sentence.strip(" \t\n\r-•")
            if len(s) < 20:
                continue
            if len(re.findall(r"[A-Za-z]", s)) < 8:
                continue
            sentences.append(s)
        return sentences

    def _tokenize(self, sentence: str) -> List[str]:
        tokens = re.findall(r"[A-Za-z][A-Za-z\-']+", sentence.lower())
        return [t for t in tokens if t not in self.STOPWORDS and len(t) > 2]

    @staticmethod
    def _score_sentence(
        sentence: str, tokens: List[str], normalized_freq: Dict[str, float]
    ) -> float:
        if not tokens:
            return 0.0

        lexical_score = sum(normalized_freq.get(token, 0.0) for token in tokens) / len(tokens)
        length_penalty = 1.0
        length = len(sentence)
        if length < 40:
            length_penalty = 0.7
        elif length > 280:
            length_penalty = 0.85

        quote_bonus = 0.15 if re.search(r'"[^"]{20,}"', sentence) else 0.0
        number_bonus = 0.1 if re.search(r"\d", sentence) else 0.0
        return (lexical_score + quote_bonus + number_bonus) * length_penalty

    @staticmethod
    def _dedupe_preserve_order(items: List[str]) -> List[str]:
        seen = set()
        output = []
        for item in items:
            norm = re.sub(r"\s+", " ", item.strip().lower())
            if not norm or norm in seen:
                continue
            seen.add(norm)
            output.append(item.strip())
        return output

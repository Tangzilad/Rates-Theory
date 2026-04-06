"""Shared chapter contract for the interactive companion."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ChapterBase(ABC):
    """Abstract base class used by all chapter modules."""

    chapter_id: str

    @abstractmethod
    def chapter_meta(self) -> Dict[str, Any]:
        """Return title and high-level context metadata."""

    @abstractmethod
    def prerequisites(self) -> List[str]:
        """Return prerequisite knowledge list for the chapter."""

    @abstractmethod
    def concept_map(self) -> Dict[str, List[str]]:
        """Return concept nodes and directed links."""

    @abstractmethod
    def equation_set(self) -> List[Dict[str, str]]:
        """Return key equations and descriptions."""

    @abstractmethod
    def derivation_steps(self) -> List[str]:
        """Return derivation sequence in compact bullet form."""

    @abstractmethod
    def interactive_lab(self) -> Any:
        """Render chapter lab widgets and return computed payload."""

    @abstractmethod
    def case_studies(self) -> List[Dict[str, str]]:
        """Return case studies with setup and takeaway."""

    @abstractmethod
    def failure_modes(self) -> List[Dict[str, str]]:
        """Return failure scenarios and mitigations."""

    @abstractmethod
    def assessment(self) -> List[Dict[str, str]]:
        """Return assessment prompts and expected direction."""

    @abstractmethod
    def exports_to_next_chapter(self) -> Any:
        """Return explicit outputs that feed later chapters."""

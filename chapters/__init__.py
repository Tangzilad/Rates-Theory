"""Chapter module registry and dependency validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Set

from .base import ChapterBase
from .ch01 import Chapter01
from .ch02 import Chapter02
from .ch03 import Chapter03
from .ch04 import Chapter04
from .ch05 import Chapter05
from .ch06 import Chapter06
from .ch07 import Chapter07
from .ch08 import Chapter08
from .ch09 import Chapter09
from .ch10 import Chapter10
from .ch11 import Chapter11
from .ch12 import Chapter12
from .ch13 import Chapter13
from .ch14 import Chapter14
from .ch15 import Chapter15
from .ch16 import Chapter16
from .ch17 import Chapter17
from .ch18 import Chapter18


CHAPTER_DEPENDENCIES: Dict[str, Dict[str, List[str]]] = {
    "1": {},
    "2": {"1": ["basis", "arbitrage_direction"]},
    "3": {"2": ["hit_probability"]},
    "4": {},
    "5": {"3": ["explained_variance"]},
    "6": {},
    "7": {},
    "8": {"5": ["fair_price", "curve_slope_bp"]},
    "9": {"8": ["signals"]},
    "10": {},
    "11": {"9": ["signals"]},
    "12": {"11": ["swap_spread_bp"]},
    "13": {"12": ["cross_currency_basis_bp"]},
    "14": {"13": ["cross_currency_basis_bp"]},
    "15": {"14": ["cross_currency_basis_bp"]},
    "16": {"15": ["cross_currency_basis_bp"]},
    "17": {"16": ["cross_currency_basis_bp"]},
    "18": {"17": ["cross_currency_basis_bp"]},
}


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    chapter: str
    message: str


@dataclass(frozen=True)
class ChapterDependencyValidationResult:
    issues: List[ValidationIssue]
    exports_by_chapter: Dict[str, Set[str]]

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)

    def blocking_issues_for(self, chapter_key: str) -> List[ValidationIssue]:
        chapter_num = int(chapter_key) if chapter_key.isdigit() else 10_000
        blocking: List[ValidationIssue] = []
        for issue in self.issues:
            issue_num = int(issue.chapter) if issue.chapter.isdigit() else 10_000
            if issue_num <= chapter_num:
                blocking.append(issue)
        return blocking


class PlaceholderChapter(ChapterBase):
    """Explicitly non-implemented chapter that surfaces missing contracts."""

    def __init__(self, chapter_id: str, diagnostics: List[str] | None = None) -> None:
        self.chapter_id = chapter_id
        self._diagnostics = diagnostics or [
            "Module is not implemented.",
            "No chapter contract is available for this key.",
        ]

    def chapter_meta(self) -> Dict[str, Any]:
        return {
            "chapter": self.chapter_id,
            "title": f"Chapter {self.chapter_id}: Not implemented",
            "objective": "Module contract missing. Implement chapter module and register dependencies.",
        }

    def prerequisites(self) -> List[str]:
        return ["Not implemented: prerequisite contract unavailable."]

    def concept_map(self) -> Dict[str, List[str]]:
        return {"status": ["not_implemented"], "diagnostics": self._diagnostics}

    def equation_set(self) -> List[Dict[str, str]]:
        return [{"name": "Not implemented", "equation": "No equation contract available."}]

    def derivation_steps(self) -> List[str]:
        return ["Not implemented: derive chapter contract before use."]

    def interactive_lab(self) -> Dict[str, Any]:
        return {"status": "not_implemented", "missing_contract": self._diagnostics}

    def case_studies(self) -> List[Dict[str, str]]:
        return [{"name": "Not implemented", "setup": "N/A", "takeaway": "Missing chapter contract."}]

    def failure_modes(self) -> List[Dict[str, str]]:
        return [{"mode": "Unimplemented chapter selected", "mitigation": "Add concrete chapter module and registry wiring."}]

    def assessment(self) -> List[Dict[str, str]]:
        return [{"prompt": "What is missing?", "expected": "A concrete chapter implementation and dependency contract."}]

    def exports_to_next_chapter(self) -> Dict[str, Any]:
        return {"status": "not_implemented", "signals": [], "missing_contract": self._diagnostics}


def build_chapter_registry() -> Dict[str, ChapterBase]:
    return {
        "1": Chapter01(),
        "2": Chapter02(),
        "3": Chapter03(),
        "4": Chapter04(),
        "5": Chapter05(),
        "6": Chapter06(),
        "7": Chapter07(),
        "8": Chapter08(),
        "9": Chapter09(),
        "10": Chapter10(),
        "11": Chapter11(),
        "12": Chapter12(),
        "13": Chapter13(),
        "14": Chapter14(),
        "15": Chapter15(),
        "16": Chapter16(),
        "17": Chapter17(),
        "18": Chapter18(),
    }


def _extract_export_keys(chapter: ChapterBase) -> Set[str]:
    exports = chapter.exports_to_next_chapter()
    keys: Set[str] = set()
    if isinstance(exports, Mapping):
        for key, value in exports.items():
            if key == "signals" and isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        keys.add(item)
            keys.add(str(key))
    return keys


def validate_chapter_dependencies(
    registry: Dict[str, ChapterBase],
    dependency_map: Dict[str, Dict[str, List[str]]] | None = None,
) -> ChapterDependencyValidationResult:
    dependencies = dependency_map or CHAPTER_DEPENDENCIES
    exports_by_chapter = {chapter_key: _extract_export_keys(chapter) for chapter_key, chapter in registry.items()}
    issues: List[ValidationIssue] = []

    for chapter_key, required in dependencies.items():
        if chapter_key not in registry:
            issues.append(
                ValidationIssue(
                    severity="error",
                    chapter=chapter_key,
                    message=f"Dependency metadata declared for chapter {chapter_key}, but chapter module is missing.",
                )
            )
            continue

        for provider_key, required_keys in required.items():
            if provider_key not in registry:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        chapter=chapter_key,
                        message=f"Required chapter {provider_key} is missing from registry.",
                    )
                )
                continue

            if provider_key.isdigit() and chapter_key.isdigit() and int(provider_key) >= int(chapter_key):
                issues.append(
                    ValidationIssue(
                        severity="error",
                        chapter=chapter_key,
                        message=f"Prerequisite chapter {provider_key} must be before chapter {chapter_key}.",
                    )
                )

            provider_exports = exports_by_chapter.get(provider_key, set())
            missing_required = sorted(set(required_keys) - provider_exports)
            if missing_required:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        chapter=chapter_key,
                        message=(
                            f"Required exports {missing_required} not provided by chapter {provider_key}; "
                            f"available exports: {sorted(provider_exports)}."
                        ),
                    )
                )

    for chapter_key in registry.keys():
        if chapter_key not in dependencies:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    chapter=chapter_key,
                    message="No dependency metadata defined for this chapter.",
                )
            )

    return ChapterDependencyValidationResult(issues=issues, exports_by_chapter=exports_by_chapter)


def get_chapter(
    chapter_key: str,
    registry: Dict[str, ChapterBase],
    validation_result: ChapterDependencyValidationResult | None = None,
) -> ChapterBase:
    chapter = registry.get(chapter_key)
    if chapter is not None:
        return chapter

    diagnostics: List[str] = []
    if validation_result is not None:
        diagnostics.extend(
            issue.message
            for issue in validation_result.blocking_issues_for(chapter_key)
            if issue.severity == "error"
        )
    if not diagnostics:
        diagnostics.append(f"Chapter key '{chapter_key}' is not present in build_chapter_registry().")
    return PlaceholderChapter(chapter_key, diagnostics=diagnostics)

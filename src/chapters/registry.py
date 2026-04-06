"""Chapter module registry and dependency validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .base import ChapterBase, PlaceholderChapter
from .ch01_relative_value import Chapter01
from .ch02_mean_reversion import Chapter02
from .ch03_factor_pca import Chapter03
from .ch04_multivariate_mean_reversion import Chapter04
from .ch05_duration_convexity import Chapter05
from .ch06_yield_curve_models import Chapter06
from .ch07_risk_governance import Chapter07
from .ch08_relative_value_screens import Chapter08
from .ch09_trade_construction import Chapter09
from .ch10_funding_basis import Chapter10
from .ch11_reference_rate_transition import Chapter11
from .ch12_asset_swap_decomposition import Chapter12
from .ch13_pure_credit_extraction import Chapter13
from .ch14_executable_trade_design import Chapter14
from .ch15_carry_rolldown import Chapter15
from .ch16_hedge_calibration import Chapter16
from .ch17_scenario_stress import Chapter17
from .ch18_shadow_costs import Chapter18


CHAPTER_DEPENDENCIES: dict[str, dict[str, list[str]]] = {
    "1": {},
    "2": {"1": ["residual", "direction", "confidence"]},
    "3": {"2": ["hit_probability"]},
    "4": {"3": ["explained_variance"]},
    "5": {"4": ["regime_score", "regime_label"]},
    "6": {"5": ["fair_price", "curve_slope_bp"]},
    "7": {"6": ["zero_curve", "residual_diagnostics"]},
    "8": {"7": ["approved", "status"]},
    "9": {"8": ["residual_bp", "trade_signal"]},
    "10": {"9": ["expected_edge_bp", "approved"]},
    "11": {"10": ["funding_basis_bp"]},
    "12": {"11": ["fallback_spread_bp", "all_in_coupon_pct"]},
    "13": {"12": ["asset_swap_spread_bp", "package_carry_bp"]},
    "14": {"13": ["pure_credit_bp"]},
    "15": {"14": ["execution_confidence"]},
    "16": {"15": ["expected_total_pnl"]},
    "17": {"16": ["realized_residual_dv01"]},
    "18": {"17": ["total_stress_pnl"]},
}


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    chapter: str
    message: str


@dataclass(frozen=True)
class ChapterDependencyValidationResult:
    issues: list[ValidationIssue]
    exports_by_chapter: dict[str, set[str]]

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)

    def blocking_issues_for(self, chapter_key: str) -> list[ValidationIssue]:
        chapter_num = int(chapter_key) if chapter_key.isdigit() else 10_000
        blocking: list[ValidationIssue] = []
        for issue in self.issues:
            issue_num = int(issue.chapter) if issue.chapter.isdigit() else 10_000
            if issue_num <= chapter_num:
                blocking.append(issue)
        return blocking


def build_chapter_registry() -> dict[str, ChapterBase]:
    return {
        "1": Chapter01(), "2": Chapter02(), "3": Chapter03(), "4": Chapter04(), "5": Chapter05(), "6": Chapter06(), "7": Chapter07(), "8": Chapter08(), "9": Chapter09(), "10": Chapter10(), "11": Chapter11(), "12": Chapter12(), "13": Chapter13(), "14": Chapter14(), "15": Chapter15(), "16": Chapter16(), "17": Chapter17(), "18": Chapter18(),
    }


def _extract_export_keys(chapter: ChapterBase) -> set[str]:
    exports = chapter.exports_to_next_chapter()
    if hasattr(exports, "model_dump"):
        exports = exports.model_dump()
    keys: set[str] = set()
    if isinstance(exports, Mapping):
        for key, value in exports.items():
            if key == "signals" and isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        keys.add(item)
            keys.add(str(key))
    return keys


def validate_chapter_dependencies(registry: dict[str, ChapterBase], dependency_map: dict[str, dict[str, list[str]]] | None = None) -> ChapterDependencyValidationResult:
    dependencies = dependency_map or CHAPTER_DEPENDENCIES
    exports_by_chapter = {chapter_key: _extract_export_keys(chapter) for chapter_key, chapter in registry.items()}
    issues: list[ValidationIssue] = []

    for chapter_key, required in dependencies.items():
        if chapter_key not in registry:
            issues.append(ValidationIssue(severity="error", chapter=chapter_key, message=f"Dependency metadata declared for chapter {chapter_key}, but chapter module is missing."))
            continue

        for provider_key, required_keys in required.items():
            if provider_key not in registry:
                issues.append(ValidationIssue(severity="error", chapter=chapter_key, message=f"Required chapter {provider_key} is missing from registry."))
                continue

            if provider_key.isdigit() and chapter_key.isdigit() and int(provider_key) >= int(chapter_key):
                issues.append(ValidationIssue(severity="error", chapter=chapter_key, message=f"Prerequisite chapter {provider_key} must be before chapter {chapter_key}."))

            provider_exports = exports_by_chapter.get(provider_key, set())
            missing_required = sorted(set(required_keys) - provider_exports)
            if missing_required:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        chapter=chapter_key,
                        message=(f"Required exports {missing_required} not provided by chapter {provider_key}; " f"available exports: {sorted(provider_exports)}."),
                    )
                )

    for chapter_key in registry:
        if chapter_key not in dependencies:
            issues.append(ValidationIssue(severity="warning", chapter=chapter_key, message="No dependency metadata defined for this chapter."))

    return ChapterDependencyValidationResult(issues=issues, exports_by_chapter=exports_by_chapter)


def get_chapter(chapter_key: str, registry: dict[str, ChapterBase], validation_result: ChapterDependencyValidationResult | None = None) -> ChapterBase:
    chapter = registry.get(chapter_key)
    if chapter is not None:
        return chapter

    diagnostics: list[str] = []
    if validation_result is not None:
        diagnostics.extend(issue.message for issue in validation_result.blocking_issues_for(chapter_key) if issue.severity == "error")
    if not diagnostics:
        diagnostics.append(f"Chapter key '{chapter_key}' is not present in build_chapter_registry().")
    return PlaceholderChapter(chapter_key, diagnostics=diagnostics)

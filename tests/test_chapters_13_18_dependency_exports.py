from __future__ import annotations

from src.chapters.registry import CHAPTER_DEPENDENCIES, build_chapter_registry, validate_chapter_dependencies


def _export_signals(registry: dict[str, object], chapter_key: str) -> set[str]:
    exports = registry[chapter_key].exports_to_next_chapter()
    if hasattr(exports, "model_dump"):
        exports = exports.model_dump()
    signals = exports.get("signals", [])
    return set(signals)


def test_chapter_13_to_18_dependency_keys_exist_and_are_chronological() -> None:
    expected_dependencies = {
        "13": {"12": ["asset_swap_spread_bp", "package_carry_bp"]},
        "14": {"13": ["pure_credit_bp"]},
        "15": {"14": ["execution_confidence"]},
        "16": {"15": ["expected_total_pnl"]},
        "17": {"16": ["realized_residual_dv01"]},
        "18": {"17": ["total_stress_pnl"]},
    }

    for chapter_key, expected in expected_dependencies.items():
        assert CHAPTER_DEPENDENCIES[chapter_key] == expected
        for provider in expected:
            assert int(provider) < int(chapter_key)


def test_chapter_13_to_18_expected_export_keys_vs_declared_dependencies() -> None:
    registry = build_chapter_registry()
    result = validate_chapter_dependencies(registry)

    expected_exports = {
        "13": {"observed_spread_bp", "purified_credit_spread_bp", "hazard_proxy", "recovery_sensitivity"},
        "14": {"net_edge_bp", "execution_confidence", "execute_flag"},
        "15": {"carry_pnl", "convergence_pnl", "expected_total_pnl"},
        "16": {
            "common_space_normalization.normalized_signals_bp",
            "agreement_divergence_diagnostics",
            "shock_propagation_results",
        },
        "17": {
            "curve_ranking",
            "sofr_asw_ranking",
            "disagreement_diagnostics",
            "attribution_buckets_bp",
            "portfolio_selection_signals",
            "rv_spread_pnl",
            "total_stress_pnl",
        },
        "18": {
            "structural_fair_spread_bp",
            "observed_spread_bp",
            "shadow_funding_cost_bp",
            "capital_charge_bp",
            "liquidity_wedge_bp",
            "repo_stress_add_on_bp",
            "adjusted_executable_spread_residual_bp",
            "approval_gate",
        },
    }

    for chapter_key, expected in expected_exports.items():
        assert expected.issubset(_export_signals(registry, chapter_key))

    targeted_errors = [
        issue
        for issue in result.issues
        if issue.severity == "error" and issue.chapter in {"13", "14", "15", "16", "17", "18"}
    ]
    assert any("pure_credit_bp" in issue.message for issue in targeted_errors)
    assert any("realized_residual_dv01" in issue.message for issue in targeted_errors)

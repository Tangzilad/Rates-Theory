"""Integrated relative-value engines spanning Chapters 14-17.

Pedagogical simplification:
- Uses linear transformations between local pricing spaces.
- Normalizes all transformed signals to a USD SOFR-relative common frame.
- Shock propagation is deterministic and first-order for transparent teaching workflows.
"""

from __future__ import annotations

from core.types import (
    AgreementDivergenceDiagnosticsState,
    CommonSpaceNormalizationState,
    IntegratedRVState,
    ShockPropagationState,
)


def execution_signal(signal_bp: float, transaction_cost_bp: float, entry_threshold_bp: float) -> tuple[float, float, bool]:
    """Return net edge, confidence ratio, and execution flag."""
    edge_bp = signal_bp - transaction_cost_bp
    confidence = max(0.0, min(1.0, edge_bp / max(entry_threshold_bp, 1.0)))
    return edge_bp, confidence, edge_bp >= entry_threshold_bp


def expected_carry_pnl(notional: float, carry_bp: float, horizon_years: float) -> float:
    """Compute carry-like P&L projection in dollars."""
    return notional * (carry_bp / 10_000.0) * horizon_years


def hedge_ratio(trade_dv01: float, hedge_dv01: float, target_residual_dv01: float) -> tuple[float, float]:
    """Return hedge units and realized residual DV01."""
    target_hedged_dv01 = max(trade_dv01 - target_residual_dv01, 0.0)
    units = target_hedged_dv01 / max(hedge_dv01, 1.0)
    residual = trade_dv01 - units * hedge_dv01
    return units, residual


def stress_pnl(spread_shock_bp: float, rate_shock_bp: float, cs01: float, dv01: float, liquidity_penalty: float) -> tuple[float, float]:
    """Return core and total stressed P&L in dollars."""
    core = -((spread_shock_bp * cs01) + (rate_shock_bp * dv01))
    return core, core - liquidity_penalty


def _normalize_to_sofr_frame(
    transformed_signals_bp: dict[str, float],
    sofr_anchor_bp: float,
) -> dict[str, float]:
    """Map transformed signals into a USD SOFR-relative pedagogical frame."""
    return {name: value - sofr_anchor_bp for name, value in transformed_signals_bp.items()}


def _agreement_diagnostics(signals_bp: dict[str, float], divergence_threshold_bp: float) -> AgreementDivergenceDiagnosticsState:
    """Compute simple agreement/divergence diagnostics across normalized signals."""
    if not signals_bp:
        return AgreementDivergenceDiagnosticsState(
            mean_signal_bp=0.0,
            max_deviation_bp=0.0,
            agreement_ratio=1.0,
            divergence_flag=False,
            directional_votes={},
        )

    values = list(signals_bp.values())
    mean_signal = sum(values) / len(values)
    max_dev = max(abs(x - mean_signal) for x in values)
    same_direction_count = sum(1 for x in values if (x >= 0.0) == (mean_signal >= 0.0))
    agreement_ratio = same_direction_count / len(values)

    return AgreementDivergenceDiagnosticsState(
        mean_signal_bp=mean_signal,
        max_deviation_bp=max_dev,
        agreement_ratio=agreement_ratio,
        divergence_flag=max_dev > divergence_threshold_bp,
        directional_votes={
            name: "rich" if value < 0.0 else "cheap"
            for name, value in signals_bp.items()
        },
    )


def _propagate_single_shock(
    shocked_input: str,
    shock_bp: float,
    baseline_signals_bp: dict[str, float],
) -> ShockPropagationState:
    """Propagate one shocked node through Chapter-10-style dependency semantics."""
    betas: dict[str, dict[str, float]] = {
        "bond": {
            "bond_local": 1.00,
            "asset_swap": 0.75,
            "basis_intra": 0.20,
            "basis_cross": 0.10,
            "cds_pure_credit": 0.35,
        },
        "asset_swap": {
            "bond_local": 0.30,
            "asset_swap": 1.00,
            "basis_intra": 0.25,
            "basis_cross": 0.40,
            "cds_pure_credit": 0.30,
        },
        "basis_intra": {
            "bond_local": 0.10,
            "asset_swap": 0.35,
            "basis_intra": 1.00,
            "basis_cross": 0.60,
            "cds_pure_credit": 0.10,
        },
        "basis_cross": {
            "bond_local": 0.20,
            "asset_swap": 0.55,
            "basis_intra": 0.45,
            "basis_cross": 1.00,
            "cds_pure_credit": 0.15,
        },
        "cds_pure_credit": {
            "bond_local": 0.45,
            "asset_swap": 0.40,
            "basis_intra": 0.15,
            "basis_cross": 0.10,
            "cds_pure_credit": 1.00,
        },
    }
    propagation_order = ["bond_local", "asset_swap", "basis_intra", "basis_cross", "cds_pure_credit"]
    selected_betas = betas.get(shocked_input, betas["bond"])

    shocked_signals = {
        node: baseline_signals_bp.get(node, 0.0) + shock_bp * selected_betas.get(node, 0.0)
        for node in propagation_order
    }

    return ShockPropagationState(
        shocked_input=shocked_input,
        shock_bp=shock_bp,
        propagation_order=propagation_order,
        shocked_signals_bp=shocked_signals,
    )


def integrated_rv_state(
    *,
    bond_local_space_signal_bp: float,
    asset_swap_transformed_signal_bp: float,
    intra_basis_transformed_signal_bp: float,
    cross_currency_basis_transformed_signal_bp: float,
    cds_pure_credit_signal_bp: float,
    sofr_anchor_bp: float = 0.0,
    shocked_input: str = "bond",
    shock_bp: float = 0.0,
    divergence_threshold_bp: float = 12.5,
) -> IntegratedRVState:
    """Build a chapter-ready integrated RV state object.

    The state contains:
    - Local and transformed signals.
    - USD SOFR-relative common-space normalization.
    - Agreement/divergence diagnostics.
    - One-factor shock propagation output.
    """
    transformed_signals = {
        "bond_local": bond_local_space_signal_bp,
        "asset_swap": asset_swap_transformed_signal_bp,
        "basis_intra": intra_basis_transformed_signal_bp,
        "basis_cross": cross_currency_basis_transformed_signal_bp,
        "cds_pure_credit": cds_pure_credit_signal_bp,
    }
    normalized = _normalize_to_sofr_frame(
        transformed_signals_bp=transformed_signals,
        sofr_anchor_bp=sofr_anchor_bp,
    )
    diagnostics = _agreement_diagnostics(
        signals_bp=normalized,
        divergence_threshold_bp=divergence_threshold_bp,
    )
    shock_results = _propagate_single_shock(
        shocked_input=shocked_input,
        shock_bp=shock_bp,
        baseline_signals_bp=normalized,
    )

    return IntegratedRVState(
        bond_local_space_signal_bp=bond_local_space_signal_bp,
        asset_swap_transformed_signal_bp=asset_swap_transformed_signal_bp,
        basis_transformed_signals_bp={
            "intra_currency_basis": intra_basis_transformed_signal_bp,
            "cross_currency_basis": cross_currency_basis_transformed_signal_bp,
        },
        cds_pure_credit_signal_bp=cds_pure_credit_signal_bp,
        common_space_normalization=CommonSpaceNormalizationState(
            frame="USD SOFR-relative pedagogical frame",
            reference_rate="SOFR",
            transformed_signals_bp=transformed_signals,
            normalized_signals_bp=normalized,
        ),
        agreement_divergence_diagnostics=diagnostics,
        shock_propagation_results=shock_results,
    )

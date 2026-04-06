"""Integrated relative-value engines spanning Chapters 14-17.

Pedagogical simplification:
- Uses linear cost, carry, hedge, and stress relationships.
- Intended for transparent teaching workflows rather than production risk.
"""

from __future__ import annotations


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

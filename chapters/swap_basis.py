from __future__ import annotations

from typing import Dict


def spread_bp(leg_a_pct: float, leg_b_pct: float) -> float:
    """Return basis/spread in basis points between two percentage rates."""
    return (leg_a_pct - leg_b_pct) * 100


def carry_pnl(notional: float, spread_bp_value: float, year_fraction: float = 1.0) -> float:
    """Approximate carry P&L from a spread in basis points."""
    return notional * (spread_bp_value / 10_000.0) * year_fraction


def clamp_confidence(score: float) -> float:
    """Clamp diagnostics score to a [0, 1] interval."""
    return max(0.0, min(1.0, score))


def package_state(state_key: str, outputs: Dict[str, float], usage: str) -> Dict[str, object]:
    """Create consistent chapter export payloads."""
    return {state_key: outputs, "usage": usage}

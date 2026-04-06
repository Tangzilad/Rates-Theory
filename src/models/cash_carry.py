"""Cash-and-carry model calculations."""

from __future__ import annotations

from core.equations import arbitrage_direction, basis_from_market, fair_futures_price


def cash_carry_state(spot: float, repo: float, t_years: float, fut_mkt: float) -> tuple[float, float, str]:
    fair_fut = fair_futures_price(spot, repo, t_years)
    basis = basis_from_market(fut_mkt, fair_fut)
    direction = arbitrage_direction(basis)
    return fair_fut, basis, direction

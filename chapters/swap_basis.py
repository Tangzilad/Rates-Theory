from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from core.types import FundingBasisState
from src.models.swap_spreads import asset_swap_spread, cross_currency_basis, intra_currency_basis

from .common import SimpleChapter




def spread_bp(a: float, b: float) -> float:
    """Return difference in basis points between two percentage rates."""
    return (a - b) * 100.0


def carry_pnl(carry_bp: float, notional: float, horizon_days: int = 1) -> float:
    """Approximate carry PnL in currency units from annualized carry in bps."""
    return notional * (carry_bp / 10_000.0) * (horizon_days / 360.0)


def clamp_confidence(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp confidence score to [0, 1] style interval."""
    return float(min(max(value, lo), hi))


def package_state(schema_name: str, outputs: Dict[str, Any], usage: str) -> Dict[str, Any]:
    """Package outputs into a standard chapter export payload."""
    return {"schema_name": schema_name, "signals": list(outputs.keys()), "outputs": outputs, "usage": usage}


class SwapBasisChapter(SimpleChapter):
    def equation_set(self) -> List[Dict[str, str]]:
        return [
            {"name": "Swap spread", "equation": "SS=(swap_rate-gov_yield)*100"},
            {"name": "XCCY basis", "equation": "basis=(usd_leg-eur_leg-fx_hedge)*100"},
        ]

    def interactive_lab(self) -> FundingBasisState:
        key = self.chapter_id
        c1, c2, c3 = st.columns(3)
        swap_rate = c1.number_input("Par swap rate (%)", value=4.15, step=0.01, key=f"swap_{key}")
        gov_yield = c1.number_input("Govt yield (%)", value=3.95, step=0.01, key=f"gov_{key}")
        bond_coupon = c2.number_input("Bond coupon (%)", value=4.0, step=0.01, key=f"cpn_{key}")
        z_spread = c2.number_input("Bond z-spread (bp)", value=85.0, step=1.0, key=f"z_{key}")
        tenor_short = c3.number_input("Short tenor (%)", value=4.00, step=0.01, key=f"tshort_{key}")
        tenor_long = c3.number_input("Long tenor (%)", value=4.22, step=0.01, key=f"tlong_{key}")
        usd_leg = st.number_input("USD floating leg (%)", value=4.55, step=0.01, key=f"usd_{key}")
        eur_leg = st.number_input("EUR floating leg (%)", value=3.20, step=0.01, key=f"eur_{key}")
        fx_hedge_cost = st.number_input("FX hedge cost (%)", value=0.95, step=0.01, key=f"fx_{key}")

        swap_spread = (swap_rate - gov_yield) * 100
        asw_spread = asset_swap_spread(par_swap_rate=swap_rate, bond_yield=bond_coupon) * 100 + z_spread
        tenor_basis = intra_currency_basis(float_leg_a=tenor_long, float_leg_b=tenor_short) * 100
        xccy_basis = cross_currency_basis(
            domestic_float_rate=usd_leg,
            foreign_float_rate=eur_leg,
            fx_forward_implied_rate=fx_hedge_cost,
        ) * 100

        st.metric("Swap spread (bp)", f"{swap_spread:.2f}")
        st.metric("Asset-swap spread (bp)", f"{asw_spread:.2f}")
        st.metric("Intra-currency basis (bp)", f"{tenor_basis:.2f}")
        st.metric("Cross-currency basis (bp)", f"{xccy_basis:.2f}")

        return {
            "inputs": {
                "swap_rate": swap_rate,
                "gov_yield": gov_yield,
                "bond_coupon": bond_coupon,
                "z_spread": z_spread,
                "tenor_short": tenor_short,
                "tenor_long": tenor_long,
                "usd_leg": usd_leg,
                "eur_leg": eur_leg,
                "fx_hedge_cost": fx_hedge_cost,
            },
            "outputs": {
                "swap_spread_bp": swap_spread,
                "asset_swap_spread_bp": asset_swap_spread,
                "tenor_basis_bp": tenor_basis,
                "cross_currency_basis_bp": xccy_basis,
            },
        }

    def exports_to_next_chapter(self) -> Dict[str, Any]:
        return {
            "signals": [
                "swap_spread_bp",
                "asset_swap_spread_bp",
                "tenor_basis_bp",
                "cross_currency_basis_bp",
            ],
            "usage": "Forward swap and basis diagnostics to the next module in the sequence.",
        }

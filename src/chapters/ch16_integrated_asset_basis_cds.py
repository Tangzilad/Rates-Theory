from __future__ import annotations

import streamlit as st

from .base import SimpleChapter


class Chapter16(SimpleChapter):
    def __init__(self) -> None:
        super().__init__(
            chapter_id="16",
            title="Chapter 16: Integrated asset-basis and CDS",
            objective="Jointly size cash-bond, basis-swap, and CDS legs to preserve target carry while controlling residual rate risk.",
        )

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {
                "name": "Integrated hedge ratio",
                "equation": "hedge_ratio_units=(asset_leg_dv01-target_residual_dv01)/cds_leg_dv01_per_unit",
            },
            {
                "name": "Residual DV01",
                "equation": "realized_residual_dv01=asset_leg_dv01-hedge_ratio_units*cds_leg_dv01_per_unit",
            },
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Estimate the cash-asset and basis package DV01 after carry optimization from chapter 15.",
            "Solve for CDS hedge units that leave only the desired residual macro-duration footprint.",
            "Export realized_residual_dv01 to global bond RV so cross-market spreads are compared on hedge-consistent risk.",
        ]

    def interactive_lab(self) -> dict[str, dict[str, float]]:
        asset_leg_dv01 = st.number_input("Integrated asset+basis DV01 ($/bp)", value=165_000.0, step=5_000.0, key="asset_dv01_16")
        cds_leg_dv01_per_unit = st.number_input("CDS hedge DV01 per unit ($/bp)", value=14_000.0, step=500.0, key="cds_dv01_16")
        target_residual_dv01 = st.number_input("Target residual DV01 ($/bp)", value=22_000.0, step=1_000.0, key="target_res_16")

        hedge_ratio_units = max(asset_leg_dv01 - target_residual_dv01, 0.0) / max(cds_leg_dv01_per_unit, 1e-6)
        realized_residual_dv01 = asset_leg_dv01 - hedge_ratio_units * cds_leg_dv01_per_unit

        st.metric("CDS hedge ratio (units)", f"{hedge_ratio_units:.2f}")
        st.metric("Realized residual DV01 ($/bp)", f"{realized_residual_dv01:,.0f}")

        return {
            "inputs": {
                "asset_leg_dv01": asset_leg_dv01,
                "cds_leg_dv01_per_unit": cds_leg_dv01_per_unit,
                "target_residual_dv01": target_residual_dv01,
            },
            "outputs": {
                "hedge_ratio_units": hedge_ratio_units,
                "realized_residual_dv01": realized_residual_dv01,
            },
        }

    def exports_to_next_chapter(self) -> dict[str, object]:
        return {
            "schema_name": "IntegratedAssetBasisCDSState",
            "signals": ["hedge_ratio_units", "realized_residual_dv01"],
            "usage": "Passes hedge-adjusted residual risk into global bond RV opportunity ranking.",
        }

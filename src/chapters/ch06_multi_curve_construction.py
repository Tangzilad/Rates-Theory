from __future__ import annotations

import math

import streamlit as st

from core.types import ChapterExportState, MultiCurveState

from .base import ChapterBase


class Chapter06(ChapterBase):
    chapter_id = "6"

    def chapter_meta(self) -> dict[str, str]:
        return {
            "chapter": self.chapter_id,
            "title": "Chapter 6: Multi-curve construction",
            "objective": "Build collateral-consistent discount and projection curves for valuation and basis diagnostics.",
        }

    def prerequisites(self) -> list[str]:
        return ["Chapter 5 fair-value diagnostics", "Curve bootstrapping basics", "Swap market conventions"]

    def core_claim(self) -> str:
        return "Consistent OIS discounting plus tenor-specific projection curves is required for no-arbitrage valuation across rate instruments."

    def market_objects(self) -> list[str]:
        return ["OIS discount curve", "IBOR projection curve", "discount factors", "forward rates", "basis"]

    def concept_map(self) -> dict[str, list[str]]:
        return {
            "nodes": ["Instrument pillars", "Discount factors", "Projection forwards", "Basis", "Validation residuals"],
            "edges": ["Pillars->Discount factors", "Discount factors->Forwards", "Forwards+Discounting->Basis", "Basis->Residual checks"],
        }

    def technical_equations(self) -> list[dict[str, str]]:
        return [
            {"name": "Discount factor", "equation": "P(0,T)=exp(-r_ois*T)"},
            {"name": "Forward from discount factors", "equation": "f(t1,t2)=(P(t1)/P(t2)-1)/(t2-t1)"},
            {"name": "Simple tenor basis", "equation": "basis_bp=(r_ibor-r_ois)*10000"},
        ]

    def equation_set(self) -> list[dict[str, str]]:
        return self.technical_equations()

    def derivation(self) -> list[str]:
        return [
            "Bootstrap discount factors from OIS-aligned market pillars.",
            "Infer projection forwards from tenor-specific instruments.",
            "Compare projection-vs-discount curves to derive basis diagnostics and pricing consistency checks.",
        ]

    def derivation_steps(self) -> list[str]:
        return self.derivation()

    def interactive_lab(self) -> MultiCurveState:
        c1, c2, c3 = st.columns(3)
        ois_rate = c1.slider("OIS zero rate (%)", 0.0, 10.0, 3.8, 0.1, key="ois_6") / 100
        ibor_rate = c2.slider("IBOR projection rate (%)", 0.0, 12.0, 4.2, 0.1, key="ibor_6") / 100
        maturity = c3.slider("Maturity (years)", 0.25, 10.0, 2.0, 0.25, key="tenor_6")

        discount_factor = math.exp(-ois_rate * maturity)
        basis_bp = (ibor_rate - ois_rate) * 10_000
        forward_rate_pct = (((1.0 / max(discount_factor, 1e-9)) - 1.0) / maturity) * 100

        st.metric("Discount factor P(0,T)", f"{discount_factor:.6f}")
        st.metric("Implied simple forward (%)", f"{forward_rate_pct:.3f}")
        st.metric("IBOR-OIS basis (bp)", f"{basis_bp:.1f}")

        return MultiCurveState(
            ois_rate_pct=ois_rate * 100,
            ibor_rate_pct=ibor_rate * 100,
            maturity_years=maturity,
            discount_factor=discount_factor,
            forward_rate_pct=forward_rate_pct,
            basis_bp=basis_bp,
        )

    def trade_interpretation(self) -> list[str]:
        return [
            "Positive IBOR-OIS basis supports carry in funding-sensitive spread structures but raises collateral drag concerns.",
            "Flattening basis can compress expected carry and tighten entry thresholds for basis RV trades.",
        ]

    def case_studies(self) -> list[dict[str, str]]:
        return [{"name": "Collateral stress", "setup": "OIS discounting diverges from term fixings", "takeaway": "Curve inconsistency can dominate apparent RV signals."}]

    def failure_modes_model_risk(self) -> list[dict[str, str]]:
        return [{"mode": "Convention mismatch", "mitigation": "Enforce day-count, accrual, and collateral standards before calibration."}]

    def failure_modes(self) -> list[dict[str, str]]:
        return self.failure_modes_model_risk()

    def checkpoint(self) -> list[dict[str, str]]:
        return [{"prompt": "Which curve should discount collateralized swaps?", "expected": "The collateral-consistent OIS discount curve."}]

    def assessment(self) -> list[dict[str, str]]:
        return self.checkpoint()

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=["discount_factor", "forward_rate_pct", "basis_bp"],
            usage="Feeds Chapter 7 governance and exposure controls for curve/basis assumptions.",
            schema_name="MultiCurveState",
        )

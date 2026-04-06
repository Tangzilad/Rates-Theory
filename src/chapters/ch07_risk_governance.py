from __future__ import annotations

import pandas as pd
import streamlit as st

from core.types import ChapterExportState, FuturesBasisState

from .base import ChapterBase


class Chapter07(ChapterBase):
    chapter_id = "7"

    def chapter_meta(self) -> dict[str, str]:
        return {
            "chapter": self.chapter_id,
            "title": "Chapter 7: Treasury futures delivery mechanics",
            "objective": "Connect cash bond pricing, repo carry, conversion factors, and CTD intuition for futures relative-value analysis.",
        }

    def prerequisites(self) -> list[str]:
        return ["Clean vs dirty bond pricing", "Repo financing conventions", "Treasury futures contract terms"]

    def concept_map(self) -> dict[str, list[str]]:
        return {
            "nodes": [
                "Cash bond",
                "Repo carry",
                "Forward dirty price",
                "Futures invoice",
                "Conversion factor (CF)",
                "CTD candidate",
                "Implied repo",
                "Delivery option",
            ],
            "edges": [
                "Cash bond+Repo carry->Forward dirty price",
                "Futures+CF+AI->Invoice price",
                "Forward dirty vs Invoice->Implied repo",
                "Highest implied repo->CTD candidate",
                "CTD set dispersion->Delivery option proxy",
            ],
        }

    def equation_set(self) -> list[dict[str, str]]:
        return [
            {
                "name": "Cash / repo / forward relation",
                "equation": "forward_dirty = spot_dirty * (1 + repo_rate * T) - coupon_carry_to_delivery",
            },
            {
                "name": "Futures invoice price (per 100 par)",
                "equation": "invoice = futures_price * CF + accrued_interest_delivery",
            },
            {
                "name": "Carry-adjusted basis",
                "equation": "carry_adjusted_basis = spot_dirty - invoice + coupon_carry_to_delivery",
            },
            {
                "name": "Implied repo (annualized simple)",
                "equation": "implied_repo = ((invoice + coupon_carry_to_delivery) / spot_dirty - 1) / T",
            },
        ]

    def derivation_steps(self) -> list[str]:
        return [
            "Start from bond dirty price and project financing with repo over the delivery horizon.",
            "Translate futures into delivery economics using invoice = futures × CF + accrued interest.",
            "Compute each deliverable bond's implied repo; the largest implied repo is typically CTD under these simplified assumptions.",
            "Interpret delivery option value from cross-candidate dispersion (e.g., best-vs-second implied repo spread).",
        ]

    def interactive_lab(self) -> dict[str, float | str | dict[str, float] | list[dict[str, float | str]]]:
        st.markdown("### Deliverable basket lab")
        st.caption(
            "Pedagogical simplification: CTD and delivery-option treatment here is intentionally simplified "
            "(single horizon, simple repo, reduced optionality). Real contracts require full delivery-calendar, "
            "quality-option, timing-option, and financing microstructure modeling."
        )

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            futures_price = st.number_input("Futures price", value=111.25, step=0.125, key="fut_7")
            days_to_delivery = st.number_input("Days to delivery", min_value=1, value=90, step=1, key="d2d_7")
        with col_b:
            base_repo_rate = st.number_input("Base repo rate (%)", value=4.60, step=0.01, key="repo_7") / 100.0
            repo_specialness_bp = st.slider(
                "Repo specialness shock (bp)", min_value=-100, max_value=100, value=0, step=5, key="special_7"
            )
        with col_c:
            coupon_carry_factor = st.number_input(
                "Coupon carry approximation (% of coupon to delivery)", min_value=0.0, max_value=1.0, value=0.5, step=0.05, key="carryfac_7"
            )

        t_years = days_to_delivery / 360.0
        special_repo = base_repo_rate + repo_specialness_bp / 10000.0

        st.markdown("#### Basket inputs")
        default_basket = [
            {"name": "Bond A", "coupon_pct": 2.0, "maturity_yrs": 8.0, "clean_price": 102.75, "accrued_interest": 1.10, "conversion_factor": 0.9012},
            {"name": "Bond B", "coupon_pct": 3.0, "maturity_yrs": 12.0, "clean_price": 109.40, "accrued_interest": 1.55, "conversion_factor": 0.9735},
            {"name": "Bond C", "coupon_pct": 4.5, "maturity_yrs": 18.0, "clean_price": 121.35, "accrued_interest": 2.05, "conversion_factor": 1.0642},
        ]

        basket = []
        for i, row in enumerate(default_basket):
            st.markdown(f"**{row['name']}**")
            c1, c2, c3, c4, c5 = st.columns(5)
            coupon_pct = c1.number_input("Coupon %", value=row["coupon_pct"], step=0.125, key=f"cpn_7_{i}")
            maturity_yrs = c2.number_input("Maturity (yrs)", value=row["maturity_yrs"], step=0.5, key=f"mat_7_{i}")
            clean_price = c3.number_input("Clean price", value=row["clean_price"], step=0.01, key=f"px_7_{i}")
            accrued_interest = c4.number_input("AI at delivery", value=row["accrued_interest"], step=0.01, key=f"ai_7_{i}")
            conversion_factor = c5.number_input("CF", value=row["conversion_factor"], step=0.0001, key=f"cf_7_{i}")
            basket.append(
                {
                    "name": row["name"],
                    "coupon_pct": coupon_pct,
                    "maturity_yrs": maturity_yrs,
                    "clean_price": clean_price,
                    "accrued_interest": accrued_interest,
                    "conversion_factor": conversion_factor,
                }
            )

        records: list[dict[str, float | str]] = []
        for bond in basket:
            spot_dirty = bond["clean_price"] + bond["accrued_interest"]
            coupon_carry = (bond["coupon_pct"] / 100.0) * coupon_carry_factor
            forward_dirty = spot_dirty * (1.0 + special_repo * t_years) - coupon_carry
            invoice = futures_price * bond["conversion_factor"] + bond["accrued_interest"]
            implied_repo = (((invoice + coupon_carry) / max(spot_dirty, 1e-6)) - 1.0) / max(t_years, 1e-6)
            carry_adjusted_basis = spot_dirty - invoice + coupon_carry

            records.append(
                {
                    "bond": bond["name"],
                    "coupon_pct": bond["coupon_pct"],
                    "maturity_yrs": bond["maturity_yrs"],
                    "spot_dirty": spot_dirty,
                    "forward_dirty_repo": forward_dirty,
                    "invoice_price": invoice,
                    "implied_repo_pct": implied_repo * 100.0,
                    "carry_adjusted_basis": carry_adjusted_basis,
                }
            )

        df = pd.DataFrame(records)
        df = df.sort_values("implied_repo_pct", ascending=False).reset_index(drop=True)

        ctd_row = df.iloc[0]
        second_best = df.iloc[1] if len(df) > 1 else df.iloc[0]

        delivery_option_proxy = ctd_row["implied_repo_pct"] - second_best["implied_repo_pct"]
        avg_basis = float(df["carry_adjusted_basis"].mean())

        st.dataframe(
            df.style.format(
                {
                    "coupon_pct": "{:.3f}",
                    "maturity_yrs": "{:.2f}",
                    "spot_dirty": "{:.3f}",
                    "forward_dirty_repo": "{:.3f}",
                    "invoice_price": "{:.3f}",
                    "implied_repo_pct": "{:.3f}",
                    "carry_adjusted_basis": "{:.3f}",
                }
            ),
            use_container_width=True,
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("CTD candidate", str(ctd_row["bond"]))
        m2.metric("CTD implied repo (%)", f"{ctd_row['implied_repo_pct']:.3f}")
        m3.metric("Avg carry-adjusted basis", f"{avg_basis:.3f}")
        m4.metric("Delivery-option proxy (bp)", f"{delivery_option_proxy * 100:.2f}")

        st.info(
            "Conversion factor intuition: CF scales each eligible bond into a standardized 6% notional equivalent. "
            "Bonds with lower invoice burden relative to cash-and-carry economics tend to emerge as CTD."
        )

        return {
            "ctd_candidate": str(ctd_row["bond"]),
            "implied_repo_pct": float(ctd_row["implied_repo_pct"]),
            "carry_adjusted_basis": float(ctd_row["carry_adjusted_basis"]),
            "delivery_option_proxy_bp": float(delivery_option_proxy * 100.0),
            "base_repo_pct": base_repo_rate * 100.0,
            "special_repo_pct": special_repo * 100.0,
            "repo_specialness_bp": float(repo_specialness_bp),
            "basket_results": records,
        }

    def case_studies(self) -> list[dict[str, str]]:
        return [
            {
                "name": "CTD flip risk",
                "setup": "Two nearby bonds alternate as cheapest-to-deliver as repo specialness moves.",
                "takeaway": "Delivery optionality can dominate simple basis signals near switch boundaries.",
            }
        ]

    def failure_modes(self) -> list[dict[str, str]]:
        return [
            {
                "mode": "Treating CTD as static",
                "mitigation": "Stress repo, carry, and accrued-interest assumptions across candidate bonds and delivery dates.",
            }
        ]

    def assessment(self) -> list[dict[str, str]]:
        return [
            {
                "prompt": "What usually indicates the CTD in a simplified implied-repo screen?",
                "expected": "The bond with the highest implied repo among deliverable candidates.",
            }
        ]

    def exports_to_next_chapter(self) -> dict[str, object]:
        return {
            "signals": [
                "ctd_candidate",
                "implied_repo_pct",
                "carry_adjusted_basis",
                "delivery_option_proxy_bp",
                "repo_specialness_bp",
            ],
            "usage": "Feeds downstream trade-construction and funding-basis chapters with futures delivery diagnostics.",
        }

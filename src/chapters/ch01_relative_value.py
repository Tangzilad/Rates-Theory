from __future__ import annotations

import math

import streamlit as st

from core.types import ChapterExportState, RelativeValueState

from .base import ChapterBase


class Chapter01(ChapterBase):
    chapter_id = "1"

    def chapter_meta(self) -> dict[str, str]:
        return {
            "chapter": self.chapter_id,
            "title": "Chapter 1: Relative value and cash-and-carry",
            "objective": "Derive fair value from replication, quantify residuals, and map mispricing into execution direction.",
        }

    def prerequisites(self) -> list[str]:
        return ["Bond pricing basics", "Simple carry math", "Repo funding intuition"]

    def core_claim(self) -> str:
        return "Observed futures-vs-carry basis, net of financing, maps directly to directional cash-and-carry execution."

    def market_objects(self) -> list[str]:
        return ["spot bond", "repo funding rate", "futures contract", "basis"]

    def concept_map(self) -> dict[str, list[str]]:
        return {
            "nodes": [
                "Law of one price",
                "Replication portfolio",
                "Fair value",
                "Residual",
                "Basis",
                "Trade direction",
            ],
            "edges": [
                "Law of one price->Replication portfolio",
                "Replication portfolio->Fair value",
                "Fair value vs Market->Residual",
                "Residual sign->Trade direction",
            ],
        }

    def technical_equations(self) -> list[dict[str, str]]:
        return [
            {"name": "Payoff equivalence", "equation": "S_T - F_{mkt} = S_T - F^*"},
            {"name": "Fair value residual", "equation": "\\varepsilon = V_{mkt} - V_{fair}"},
            {"name": "Basis", "equation": "b = F_{mkt} - F^*"},
        ]

    def derivation(self) -> list[str]:
        return [
            "Replication: build synthetic futures from spot plus financing and enforce payoff equivalence.",
            "Fair price: solve for the no-arbitrage fair value implied by replication and frictions.",
            "Residual: compare market value versus fair value to obtain residual and directional signal.",
        ]

    def _friction_adjusted_fair_value(
        self,
        *,
        spot: float,
        repo: float,
        t_years: float,
        transaction_costs: float,
        repo_stress: float,
        balance_sheet_cost: float,
    ) -> float:
        effective_repo = repo + repo_stress + balance_sheet_cost
        return spot * math.exp(effective_repo * t_years) + transaction_costs

    def interactive_lab(self) -> RelativeValueState:
        st.subheader("Law of one price panel")
        st.write(
            "If spot-plus-funding replicates the futures payoff, market and replicated values should converge under no-arbitrage."
        )
        st.latex(r"F^* = S_0 e^{(r + s_{repo} + c_{bs})T} + c_{tx}")

        st.subheader("Payoff replication walkthrough")
        st.markdown(
            "1. Replicate long futures using long spot financed in repo.  \n"
            "2. Project financing and balance-sheet drag to maturity.  \n"
            "3. Compare observed futures to replicated fair value."
        )
        st.latex(r"S_T - F_{mkt} = S_T - F^*")
        st.latex(r"\varepsilon = V_{mkt} - V_{fair}")
        st.latex(r"b = F_{mkt} - F^*")

        st.subheader("Arbitrage persistence panel")
        st.markdown("Mispricing can persist even with clear replication math due to:")
        st.markdown("- **Demand for immediacy**: investors pay for immediacy under flow pressure.")
        st.markdown("- **Model misspecification**: omitted carry terms or wrong hedge assumptions distort fair value.")
        st.markdown("- **Regulatory asymmetry**: constraints differ across participants, delaying convergence.")

        with st.expander("Cash-and-carry sub-lab", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            spot = c1.number_input("Bond spot price", min_value=0.0, value=98.5, step=0.1)
            repo = c2.slider("Base repo rate (%)", 0.0, 15.0, 4.5, 0.1) / 100
            t_years = c3.slider("Time to futures maturity (years)", 0.05, 2.0, 0.5, 0.05)
            fut_mkt = c4.number_input("Observed futures price", min_value=0.0, value=100.0, step=0.1)

            st.caption("Friction layer controls")
            f1, f2, f3 = st.columns(3)
            transaction_costs = f1.slider("Transaction costs (price pts)", 0.0, 1.0, 0.05, 0.01)
            repo_stress = f2.slider("Repo stress add-on (%)", 0.0, 5.0, 0.25, 0.05) / 100
            balance_sheet_cost = f3.slider("Balance-sheet cost (%)", 0.0, 3.0, 0.2, 0.05) / 100

            fair_value = self._friction_adjusted_fair_value(
                spot=spot,
                repo=repo,
                t_years=t_years,
                transaction_costs=transaction_costs,
                repo_stress=repo_stress,
                balance_sheet_cost=balance_sheet_cost,
            )
            market_value = fut_mkt
            residual = market_value - fair_value
            basis = residual

            if residual > 0:
                direction = "cash-and-carry"
            elif residual < 0:
                direction = "reverse cash-and-carry"
            else:
                direction = "no-trade"

            confidence = min(max((abs(residual) - transaction_costs) / 2.0, 0.0), 0.99)

            st.metric("Friction-adjusted fair value", f"{fair_value:,.4f}")
            st.metric("Market value", f"{market_value:,.4f}")
            st.metric("Residual (Market - Fair)", f"{residual:,.4f}")
            st.metric("Basis", f"{basis:,.4f}")

            if direction == "cash-and-carry":
                st.success("Futures appears rich: buy bond, short futures.")
            elif direction == "reverse cash-and-carry":
                st.success("Futures appears cheap: short bond, long futures.")
            else:
                st.info("No arbitrage signal after frictions.")

        friction_notes = [
            f"Transaction costs included: {transaction_costs:.2f} price points.",
            f"Repo stress included: {repo_stress * 100:.2f}%.",
            f"Balance-sheet cost included: {balance_sheet_cost * 100:.2f}%.",
        ]

        return RelativeValueState(
            fair_value=fair_value,
            market_value=market_value,
            residual=residual,
            direction=direction,
            confidence=confidence,
            friction_notes=friction_notes,
        )

    def trade_interpretation(self) -> list[str]:
        return [
            "Positive basis indicates futures rich versus financed spot: buy spot bond and short futures.",
            "Negative basis indicates reverse cash-and-carry under borrow/shorting feasibility.",
        ]

    def case_studies(self) -> list[dict[str, str]]:
        return [
            {
                "name": "Funding squeeze",
                "setup": "Repo stress rises while futures prints stay unchanged",
                "takeaway": "Residual can close materially once funding drag is added to replication.",
            }
        ]

    def failure_modes(self) -> list[dict[str, str]]:
        return [
            {
                "mode": "Ignoring friction layers in fair value",
                "mitigation": "Apply transaction, repo stress, and balance-sheet controls before directional mapping.",
            }
        ]

    def assessment(self) -> list[dict[str, str]]:
        return [
            {
                "prompt": "If residual is positive after frictions, which direction is implied?",
                "expected": "Cash-and-carry",
            }
        ]

    def exports_to_next_chapter(self) -> ChapterExportState:
        return ChapterExportState(
            signals=[
                "fair_value",
                "market_value",
                "residual",
                "direction",
                "confidence",
                "friction_notes",
            ],
            usage="Used as residual state input for mean-reversion modeling.",
            schema_name="RelativeValueState",
        )

    # Backward-compatible method aliases for existing shell components.
    def equation_set(self) -> list[dict[str, str]]:
        return self.technical_equations()

    def derivation_steps(self) -> list[str]:
        return self.derivation()

    def failure_modes(self) -> list[dict[str, str]]:
        return self.failure_modes_model_risk()

    def assessment(self) -> list[dict[str, str]]:
        return self.checkpoint()

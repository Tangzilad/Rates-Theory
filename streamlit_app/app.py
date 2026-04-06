import json
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Rates Theory Lab", layout="wide")


def norm_cdf(x: np.ndarray | float) -> np.ndarray | float:
    """Approximate standard normal CDF using erf."""
    return 0.5 * (1.0 + np.vectorize(np.math.erf)(x / np.sqrt(2.0)))


def load_chapter_summaries() -> Tuple[Dict[str, dict], bool]:
    """Load chapter summaries and return (data, loaded_flag)."""
    json_path = Path(__file__).resolve().parent.parent / "data" / "chapter_summaries.json"
    if json_path.exists():
        try:
            with json_path.open("r", encoding="utf-8") as f:
                return json.load(f), True
        except (json.JSONDecodeError, OSError):
            pass
    fallback = {
        str(i): {
            "title": f"Chapter {i}",
            "summary": "Summary file missing; using built-in fallback content.",
            "quotes": ["Add data/chapter_summaries.json to see curated chapter excerpts."],
        }
        for i in range(1, 25)
    }
    fallback["final"] = {
        "title": "Final Chapters",
        "summary": "Integrated review of models, diagnostics, and implementation caveats.",
        "quotes": ["Model outputs are only as good as assumptions and data quality."],
    }
    return fallback, False


def chapter_key_sorter(k: str) -> Tuple[int, str]:
    if k.isdigit():
        return int(k), ""
    return 10_000, k


def render_chapter_header(chapter_data: dict) -> None:
    st.header(chapter_data.get("title", "Chapter"))
    st.write(chapter_data.get("summary", "No summary available."))
    quotes = chapter_data.get("quotes", [])
    with st.expander("Key quotes"):
        if quotes:
            for q in quotes:
                st.markdown(f"- {q}")
        else:
            st.write("No quotes available.")


def chapter1_arbitrage_calculator() -> None:
    st.subheader("Chapter 1: Cash-and-carry arbitrage")
    st.markdown(
        "This widget links futures mispricing to financing frictions. "
        "If observed futures diverges from fair value, the implied trade (cash-and-carry "
        "or reverse cash-and-carry) reveals an arbitrage direction."
    )
    c1, c2, c3, c4 = st.columns(4)
    spot = c1.number_input("Bond spot price", min_value=0.0, value=98.5, step=0.1)
    repo = c2.slider("Repo rate (%)", 0.0, 15.0, 4.5, 0.1) / 100
    t_years = c3.slider("Time to futures maturity (years)", 0.05, 2.0, 0.5, 0.05)
    fut_mkt = c4.number_input("Observed futures price", min_value=0.0, value=100.0, step=0.1)

    fair_fut = spot * np.exp(repo * t_years)
    basis = fut_mkt - fair_fut
    st.metric("Theoretical fair futures", f"{fair_fut:,.4f}")
    st.metric("Basis (Observed - Fair)", f"{basis:,.4f}")

    if basis > 0:
        st.success("Futures appears rich: consider cash-and-carry (buy bond, short futures).")
    elif basis < 0:
        st.success("Futures appears cheap: consider reverse cash-and-carry (short bond, long futures).")
    else:
        st.info("No arbitrage signal under current assumptions.")


def chapter2_ou_simulator() -> None:
    st.subheader("Chapter 2: Ornstein-Uhlenbeck mean-reversion simulator")
    st.markdown(
        "OU dynamics visualize speed of mean reversion, long-run anchor, and volatility drag. "
        "First-passage statistics connect directly to stopping-time ideas and trade horizon risk."
    )
    c1, c2, c3, c4 = st.columns(4)
    theta = c1.slider("Mean reversion speed (theta)", 0.05, 3.0, 1.0, 0.05)
    mu = c2.number_input("Long-run mean (mu)", value=0.0, step=0.1)
    sigma = c3.slider("Volatility (sigma)", 0.01, 2.0, 0.4, 0.01)
    x0 = c4.number_input("Initial value", value=1.0, step=0.1)
    barrier = st.number_input("First-passage barrier", value=0.0, step=0.1)

    n_steps = 252
    n_paths = 400
    dt = 1 / 252
    rng = np.random.default_rng(7)
    x = np.full((n_paths, n_steps), x0, dtype=float)
    for t in range(1, n_steps):
        x[:, t] = x[:, t - 1] + theta * (mu - x[:, t - 1]) * dt + sigma * np.sqrt(dt) * rng.standard_normal(n_paths)

    pnl = x[:, -1] - x[:, 0]
    sharpe = np.mean(pnl) / np.std(pnl) if np.std(pnl) > 0 else np.nan

    hit_mask = (x <= barrier)
    first_hit = np.argmax(hit_mask, axis=1)
    no_hit = ~hit_mask.any(axis=1)
    first_hit[no_hit] = n_steps
    fpt_days = np.where(first_hit < n_steps, first_hit, np.nan)

    fig, ax = plt.subplots(figsize=(8, 4))
    for i in range(min(40, n_paths)):
        ax.plot(x[i], alpha=0.35, linewidth=0.8)
    ax.axhline(mu, color="black", linestyle="--", label="mu")
    ax.axhline(barrier, color="red", linestyle=":", label="barrier")
    ax.set_title("Simulated OU paths")
    ax.set_xlabel("Day")
    ax.set_ylabel("State")
    ax.legend()
    st.pyplot(fig)

    st.metric("Estimated first-passage probability", f"{np.nanmean(~np.isnan(fpt_days)):.2%}")
    st.metric("Mean first-passage time (days)", f"{np.nanmean(fpt_days):.1f}" if np.isfinite(np.nanmean(fpt_days)) else "No hits")
    st.metric("Terminal Sharpe (simulated)", f"{sharpe:.3f}" if np.isfinite(sharpe) else "N/A")


def chapter3_pca_workflow() -> None:
    st.subheader("Chapter 3: PCA factor extraction workflow")
    st.markdown(
        "PCA decomposes co-movements into orthogonal factors. In rates, these are often interpreted "
        "as level, slope, and curvature. Use upload or synthetic data to inspect explained variance "
        "and eigenvector shapes."
    )
    source = st.radio("Data source", ["Synthetic sample", "Upload CSV"], horizontal=True)
    df = None
    if source == "Upload CSV":
        up = st.file_uploader("Upload CSV (columns = tenors/factors)", type=["csv"])
        if up is not None:
            df = pd.read_csv(up)
    if df is None:
        tenors = ["2Y", "5Y", "10Y", "30Y"]
        cov = np.array(
            [
                [1.0, 0.86, 0.70, 0.45],
                [0.86, 1.0, 0.82, 0.60],
                [0.70, 0.82, 1.0, 0.78],
                [0.45, 0.60, 0.78, 1.0],
            ]
        )
        sample = np.random.default_rng(42).multivariate_normal(np.zeros(4), cov, size=350)
        df = pd.DataFrame(sample, columns=tenors)

    x = df.select_dtypes(include=[np.number]).dropna()
    if x.shape[1] < 2:
        st.warning("Need at least 2 numeric columns for PCA.")
        return

    x_std = (x - x.mean()) / x.std(ddof=0)
    cov = np.cov(x_std.T)
    evals, evecs = np.linalg.eigh(cov)
    idx = np.argsort(evals)[::-1]
    evals, evecs = evals[idx], evecs[:, idx]
    explained = evals / evals.sum()

    exp_df = pd.DataFrame({"PC": [f"PC{i+1}" for i in range(len(explained))], "Explained Var": explained})
    st.dataframe(exp_df, use_container_width=True)

    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.bar(exp_df["PC"], exp_df["Explained Var"])
    ax1.set_title("Explained variance by factor")
    st.pyplot(fig1)

    fig2, ax2 = plt.subplots(figsize=(8, 4))
    cols = list(x.columns)
    max_factors = min(3, evecs.shape[1])
    for i in range(max_factors):
        ax2.plot(cols, evecs[:, i], marker="o", label=f"PC{i+1}")
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_title("Eigenvector loadings")
    ax2.legend()
    st.pyplot(fig2)


def chapter4_mvou_spread_sim() -> None:
    st.subheader("Chapter 4: MVOU correlated spread simulator")
    st.markdown(
        "Multivariate OU extends single-spread mean reversion to correlated books. "
        "Correlation, speed, and volatility jointly control co-integration style behavior and hedge sizing."
    )
    n_series = st.slider("Number of spreads", min_value=2, max_value=3, value=2)
    theta = st.slider("Mean reversion speed", 0.05, 2.0, 0.6, 0.05)
    sigma = st.slider("Common volatility", 0.05, 1.5, 0.35, 0.05)
    rho = st.slider("Pairwise correlation", -0.95, 0.95, 0.4, 0.05)

    n_steps = 300
    dt = 1 / 252
    corr = np.full((n_series, n_series), rho)
    np.fill_diagonal(corr, 1.0)
    chol = np.linalg.cholesky(corr + 1e-9 * np.eye(n_series))

    x = np.zeros((n_steps, n_series))
    for t in range(1, n_steps):
        z = np.random.standard_normal(n_series)
        eps = chol @ z
        x[t] = x[t - 1] + theta * (0 - x[t - 1]) * dt + sigma * np.sqrt(dt) * eps

    fig, ax = plt.subplots(figsize=(8, 4))
    for i in range(n_series):
        ax.plot(x[:, i], label=f"Spread {i+1}")
    ax.set_title("MVOU simulated spreads")
    ax.legend()
    st.pyplot(fig)
    st.write("Sample terminal correlation matrix:")
    st.dataframe(pd.DataFrame(np.corrcoef(x.T)).round(3))


def chapter5_8_calculators() -> None:
    st.subheader("Chapters 5–8: Yield curve, duration, convexity, rich/cheap")
    st.markdown(
        "These calculators connect curve shape and bond Greeks to relative-value diagnostics. "
        "Use them to translate parallel/twist shocks into expected price moves and rich-cheap flags."
    )
    y2 = st.number_input("2Y yield (%)", value=3.70, step=0.01)
    y10 = st.number_input("10Y yield (%)", value=4.10, step=0.01)
    duration = st.number_input("Modified duration", value=7.2, step=0.1)
    convexity = st.number_input("Convexity", value=65.0, step=1.0)
    price = st.number_input("Bond price", value=100.0, step=0.1)
    dy_bp = st.slider("Yield shock (bp)", -100, 100, 10)
    model_spread = st.number_input("Model spread (bp)", value=52.0, step=0.5)
    market_spread = st.number_input("Market spread (bp)", value=60.0, step=0.5)

    curve_slope = y10 - y2
    dy = dy_bp / 10000
    dp_pct = -duration * dy + 0.5 * convexity * (dy**2)
    fair_price = price * (1 + dp_pct)
    rich_cheap = market_spread - model_spread

    c1, c2, c3 = st.columns(3)
    c1.metric("2s10s slope (bp)", f"{curve_slope*100:.1f}")
    c2.metric("Estimated price change (%)", f"{dp_pct*100:.3f}")
    c3.metric("Shock-adjusted fair price", f"{fair_price:.3f}")

    if rich_cheap > 0:
        st.success(f"Bond screens CHEAP by {rich_cheap:.1f} bp vs model.")
    elif rich_cheap < 0:
        st.success(f"Bond screens RICH by {abs(rich_cheap):.1f} bp vs model.")
    else:
        st.info("At model fair value.")


def chapter11_18_swap_spreads() -> None:
    st.subheader("Chapters 11–18: Swap spread and basis calculators")
    st.markdown(
        "Swap spread and basis blocks map funding and collateral assumptions into relative value. "
        "Compare asset-swap, intra-currency tenor basis, and cross-currency basis in one panel."
    )
    c1, c2, c3 = st.columns(3)
    swap_rate = c1.number_input("Par swap rate (%)", value=4.15, step=0.01)
    gov_yield = c1.number_input("Govt yield (%)", value=3.95, step=0.01)
    bond_coupon = c2.number_input("Bond coupon (%)", value=4.0, step=0.01)
    z_spread = c2.number_input("Bond z-spread (bp)", value=85.0, step=1.0)
    tenor_short = c3.number_input("Short tenor OIS/LIBOR-like (%)", value=4.00, step=0.01)
    tenor_long = c3.number_input("Long tenor OIS/LIBOR-like (%)", value=4.22, step=0.01)
    usd_leg = st.number_input("USD floating leg (%)", value=4.55, step=0.01)
    eur_leg = st.number_input("EUR floating leg (%)", value=3.20, step=0.01)
    fx_hedge_cost = st.number_input("FX hedge cost (%)", value=0.95, step=0.01)

    swap_spread = (swap_rate - gov_yield) * 100
    asset_swap_spread = z_spread - (bond_coupon - swap_rate) * 100
    tenor_basis = (tenor_long - tenor_short) * 100
    xccy_basis = (usd_leg - eur_leg - fx_hedge_cost) * 100

    st.metric("Swap spread (bp)", f"{swap_spread:.2f}")
    st.metric("Asset-swap spread (bp)", f"{asset_swap_spread:.2f}")
    st.metric("Intra-currency basis (bp)", f"{tenor_basis:.2f}")
    st.metric("Cross-currency basis (bp)", f"{xccy_basis:.2f}")


def chapter19_21_option_pricers() -> None:
    st.subheader("Chapters 19–21: Option, swaption, and spread-option pricers")
    st.markdown(
        "These pricers connect volatility assumptions to premium and skew. "
        "Use implied vs model vol to judge whether the market smile is rich/cheap to your model."
    )
    c1, c2, c3, c4 = st.columns(4)
    fwd = c1.number_input("Forward/underlier", value=100.0, step=0.5)
    strike = c2.number_input("Strike", value=100.0, step=0.5)
    t = c3.slider("Maturity (years)", 0.1, 5.0, 1.0, 0.1)
    vol_model = c4.slider("Model vol (%)", 1.0, 80.0, 20.0, 0.5) / 100
    vol_imp = st.slider("Market implied vol (%)", 1.0, 80.0, 24.0, 0.5) / 100
    r = st.slider("Risk-free rate (%)", 0.0, 10.0, 3.0, 0.1) / 100

    def bs_call(s: float, k: float, tau: float, rf: float, vol: float) -> float:
        if vol <= 0 or tau <= 0:
            return max(s - k, 0.0)
        d1 = (np.log(s / k) + (rf + 0.5 * vol**2) * tau) / (vol * np.sqrt(tau))
        d2 = d1 - vol * np.sqrt(tau)
        return s * norm_cdf(d1) - k * np.exp(-rf * tau) * norm_cdf(d2)

    option_model = bs_call(fwd, strike, t, r, vol_model)
    option_imp = bs_call(fwd, strike, t, r, vol_imp)

    swaption_annuity = st.number_input("Swaption annuity factor", value=4.8, step=0.1)
    swaption_model = option_model * swaption_annuity / fwd
    swaption_imp = option_imp * swaption_annuity / fwd

    spread = st.number_input("Forward spread (A-B)", value=0.5, step=0.1)
    spread_vol = st.slider("Spread vol (%)", 1.0, 80.0, 28.0, 0.5) / 100
    spread_option = bs_call(max(spread, 1e-4), max(0.01, strike - fwd + spread), t, r, spread_vol)

    c1, c2, c3 = st.columns(3)
    c1.metric("Option premium (model vol)", f"{option_model:.4f}")
    c2.metric("Option premium (implied vol)", f"{option_imp:.4f}")
    c3.metric("Premium gap", f"{option_imp - option_model:.4f}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Swaption premium (model)", f"{swaption_model:.4f}")
    c5.metric("Swaption premium (implied)", f"{swaption_imp:.4f}")
    c6.metric("Spread-option premium", f"{spread_option:.4f}")

    strikes = np.linspace(0.8 * fwd, 1.2 * fwd, 21)
    smile_market = 100 * (vol_imp + 0.06 * ((strikes / fwd) - 1) ** 2)
    smile_model = 100 * (vol_model + 0.03 * ((strikes / fwd) - 1) ** 2)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(strikes, smile_market, label="Implied smile", marker="o", markersize=3)
    ax.plot(strikes, smile_model, label="Model smile", marker="x", markersize=3)
    ax.set_xlabel("Strike")
    ax.set_ylabel("Vol (%)")
    ax.set_title("Implied vs model volatility smile")
    ax.legend()
    st.pyplot(fig)


def final_chapters_panel() -> None:
    st.subheader("Final chapters: synthesis and implementation insights")
    st.markdown(
        "This panel summarizes cross-chapter lessons: signal design, financing constraints, "
        "risk budgeting, and model governance. Use it to convert calculator outputs into a repeatable "
        "investment process."
    )
    insights = {
        "Signal quality": "Prefer robust z-scores and half-life-aware thresholds over raw deviations.",
        "Execution": "Account for repo, collateral, and carry when translating fair value into trade PnL.",
        "Risk": "Stress-test non-parallel curve shifts and vol-regime changes before sizing.",
        "Governance": "Track model drift, data lineage, and regime breaks with explicit review triggers.",
    }
    st.table(pd.DataFrame(list(insights.items()), columns=["Theme", "Insight"]))


st.title("Rates Theory Interactive Companion")
chapter_data_map, loaded = load_chapter_summaries()
if not loaded:
    st.warning(
        "`data/chapter_summaries.json` was not found (or could not be parsed). "
        "Showing fallback chapter summaries."
    )

chapter_keys = sorted(chapter_data_map.keys(), key=chapter_key_sorter)
selected_key = st.sidebar.selectbox("Select chapter", chapter_keys, index=0)
chapter_data = chapter_data_map[selected_key]
render_chapter_header(chapter_data)

if selected_key == "1":
    chapter1_arbitrage_calculator()
elif selected_key == "2":
    chapter2_ou_simulator()
elif selected_key == "3":
    chapter3_pca_workflow()
elif selected_key == "4":
    chapter4_mvou_spread_sim()
elif selected_key.isdigit() and 5 <= int(selected_key) <= 8:
    chapter5_8_calculators()
elif selected_key.isdigit() and 11 <= int(selected_key) <= 18:
    chapter11_18_swap_spreads()
elif selected_key.isdigit() and 19 <= int(selected_key) <= 21:
    chapter19_21_option_pricers()
else:
    final_chapters_panel()

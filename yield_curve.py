"""Yield-curve fitting and relative-value indicators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from constants import EPSILON


@dataclass(frozen=True)
class NSSParameters:
    """Nelson-Siegel-Svensson parameter set."""

    beta0: float
    beta1: float
    beta2: float
    beta3: float
    tau1: float
    tau2: float


def _nss_design_matrix(maturities: np.ndarray, tau1: float, tau2: float) -> np.ndarray:
    m = np.maximum(maturities, EPSILON)
    x1 = (1.0 - np.exp(-m / tau1)) / (m / tau1)
    x2 = x1 - np.exp(-m / tau1)
    x3 = (1.0 - np.exp(-m / tau2)) / (m / tau2) - np.exp(-m / tau2)
    return np.column_stack([np.ones_like(m), x1, x2, x3])


def fit_nelson_siegel_svensson(
    maturities: Iterable[float],
    yields: Iterable[float],
    tau1_grid: Iterable[float] | None = None,
    tau2_grid: Iterable[float] | None = None,
) -> NSSParameters:
    """Fit NSS curve by grid search over taus and OLS for betas."""
    m = np.asarray(list(maturities), dtype=float)
    y = np.asarray(list(yields), dtype=float)
    if m.size != y.size or m.size < 4:
        raise ValueError("maturities and yields must have same length >= 4")

    tau1_candidates = np.asarray(list(tau1_grid) if tau1_grid is not None else np.linspace(0.25, 5.0, 20))
    tau2_candidates = np.asarray(list(tau2_grid) if tau2_grid is not None else np.linspace(1.0, 15.0, 30))

    best_sse = float("inf")
    best_params: NSSParameters | None = None

    for tau1 in tau1_candidates:
        for tau2 in tau2_candidates:
            if tau1 <= EPSILON or tau2 <= EPSILON:
                continue
            x = _nss_design_matrix(m, tau1=tau1, tau2=tau2)
            beta, *_ = np.linalg.lstsq(x, y, rcond=None)
            fit = x @ beta
            sse = float(np.sum((y - fit) ** 2))
            if sse < best_sse:
                best_sse = sse
                best_params = NSSParameters(*beta.tolist(), float(tau1), float(tau2))

    if best_params is None:
        raise RuntimeError("NSS fit failed")
    return best_params


def nss_yield(maturity: float, params: NSSParameters) -> float:
    """Evaluate NSS yield at a single maturity."""
    x = _nss_design_matrix(np.array([maturity]), params.tau1, params.tau2)
    beta = np.array([params.beta0, params.beta1, params.beta2, params.beta3])
    return float((x @ beta)[0])


def constant_maturity_interpolation(
    maturities: Iterable[float],
    yields: Iterable[float],
    target_maturity: float,
) -> float:
    """Linear interpolation for constant-maturity yield estimation."""
    m = np.asarray(list(maturities), dtype=float)
    y = np.asarray(list(yields), dtype=float)
    order = np.argsort(m)
    return float(np.interp(target_maturity, m[order], y[order]))


def rich_cheap_indicators(
    maturities: Iterable[float],
    observed_yields: Iterable[float],
    params: NSSParameters,
) -> dict[str, np.ndarray]:
    """Compute residual and z-score style rich/cheap indicators."""
    m = np.asarray(list(maturities), dtype=float)
    obs = np.asarray(list(observed_yields), dtype=float)
    fitted = np.array([nss_yield(mt, params) for mt in m])
    residual = obs - fitted
    z = (residual - residual.mean()) / (residual.std(ddof=1) + EPSILON)
    return {"fitted": fitted, "residual": residual, "zscore": z}

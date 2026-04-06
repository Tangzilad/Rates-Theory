"""Parametric curve-fitting utilities used by relative-value screening chapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

import numpy as np

from constants import EPSILON

FitMethod = Literal["nelson_siegel", "svensson"]


@dataclass(frozen=True)
class ParametricFitResult:
    method: FitMethod
    params: dict[str, float]
    fitted_yields_pct: np.ndarray
    residuals_pct: np.ndarray
    rmse_bp: float
    objective_value: float


def _safe_maturity_array(maturities: Iterable[float]) -> np.ndarray:
    return np.maximum(np.asarray(list(maturities), dtype=float), EPSILON)


def nelson_siegel_yield(maturities: Iterable[float], beta0: float, beta1: float, beta2: float, tau1: float) -> np.ndarray:
    m = _safe_maturity_array(maturities)
    tau1 = max(float(tau1), EPSILON)
    x1 = (1.0 - np.exp(-m / tau1)) / (m / tau1)
    x2 = x1 - np.exp(-m / tau1)
    return beta0 + beta1 * x1 + beta2 * x2


def svensson_yield(
    maturities: Iterable[float],
    beta0: float,
    beta1: float,
    beta2: float,
    beta3: float,
    tau1: float,
    tau2: float,
) -> np.ndarray:
    m = _safe_maturity_array(maturities)
    tau1 = max(float(tau1), EPSILON)
    tau2 = max(float(tau2), EPSILON)
    x1 = (1.0 - np.exp(-m / tau1)) / (m / tau1)
    x2 = x1 - np.exp(-m / tau1)
    x3 = (1.0 - np.exp(-m / tau2)) / (m / tau2) - np.exp(-m / tau2)
    return beta0 + beta1 * x1 + beta2 * x2 + beta3 * x3


def _weighted_sse(observed_pct: np.ndarray, fitted_pct: np.ndarray, weights: np.ndarray) -> float:
    residual = observed_pct - fitted_pct
    return float(np.sum(weights * residual * residual))


def compute_residuals(observed_yields_pct: Iterable[float], fitted_yields_pct: Iterable[float]) -> np.ndarray:
    observed = np.asarray(list(observed_yields_pct), dtype=float)
    fitted = np.asarray(list(fitted_yields_pct), dtype=float)
    if observed.shape != fitted.shape:
        raise ValueError("observed_yields_pct and fitted_yields_pct must have matching shapes")
    return observed - fitted


def _fit_svensson_from_tau_grid(
    maturities: np.ndarray,
    observed_pct: np.ndarray,
    weights: np.ndarray,
    tau1_grid: np.ndarray,
    tau2_grid: np.ndarray,
) -> ParametricFitResult:
    best_result: ParametricFitResult | None = None
    sqrt_w = np.sqrt(np.maximum(weights, EPSILON))

    for tau1 in tau1_grid:
        for tau2 in tau2_grid:
            if tau1 <= EPSILON or tau2 <= EPSILON:
                continue
            m = _safe_maturity_array(maturities)
            x1 = (1.0 - np.exp(-m / tau1)) / (m / tau1)
            x2 = x1 - np.exp(-m / tau1)
            x3 = (1.0 - np.exp(-m / tau2)) / (m / tau2) - np.exp(-m / tau2)
            design = np.column_stack([np.ones_like(m), x1, x2, x3])
            w_design = design * sqrt_w[:, None]
            w_obs = observed_pct * sqrt_w
            beta, *_ = np.linalg.lstsq(w_design, w_obs, rcond=None)
            fitted = design @ beta
            objective = _weighted_sse(observed_pct, fitted, weights=weights)
            residuals = observed_pct - fitted
            candidate = ParametricFitResult(
                method="svensson",
                params={
                    "beta0": float(beta[0]),
                    "beta1": float(beta[1]),
                    "beta2": float(beta[2]),
                    "beta3": float(beta[3]),
                    "tau1": float(tau1),
                    "tau2": float(tau2),
                },
                fitted_yields_pct=fitted,
                residuals_pct=residuals,
                rmse_bp=float(np.sqrt(np.mean(residuals * residuals)) * 100.0),
                objective_value=objective,
            )
            if best_result is None or candidate.objective_value < best_result.objective_value:
                best_result = candidate

    if best_result is None:
        raise RuntimeError("Svensson grid-search fit failed")
    return best_result


def _fit_nelson_siegel_from_tau_grid(
    maturities: np.ndarray,
    observed_pct: np.ndarray,
    weights: np.ndarray,
    tau1_grid: np.ndarray,
) -> ParametricFitResult:
    best_result: ParametricFitResult | None = None
    sqrt_w = np.sqrt(np.maximum(weights, EPSILON))

    for tau1 in tau1_grid:
        if tau1 <= EPSILON:
            continue
        m = _safe_maturity_array(maturities)
        x1 = (1.0 - np.exp(-m / tau1)) / (m / tau1)
        x2 = x1 - np.exp(-m / tau1)
        design = np.column_stack([np.ones_like(m), x1, x2])
        w_design = design * sqrt_w[:, None]
        w_obs = observed_pct * sqrt_w
        beta, *_ = np.linalg.lstsq(w_design, w_obs, rcond=None)
        fitted = design @ beta
        objective = _weighted_sse(observed_pct, fitted, weights=weights)
        residuals = observed_pct - fitted
        candidate = ParametricFitResult(
            method="nelson_siegel",
            params={
                "beta0": float(beta[0]),
                "beta1": float(beta[1]),
                "beta2": float(beta[2]),
                "tau1": float(tau1),
            },
            fitted_yields_pct=fitted,
            residuals_pct=residuals,
            rmse_bp=float(np.sqrt(np.mean(residuals * residuals)) * 100.0),
            objective_value=objective,
        )
        if best_result is None or candidate.objective_value < best_result.objective_value:
            best_result = candidate

    if best_result is None:
        raise RuntimeError("Nelson-Siegel grid-search fit failed")
    return best_result


def fit_parametric_curve(
    maturities_years: Iterable[float],
    observed_yields_pct: Iterable[float],
    method: FitMethod = "svensson",
    weights: Iterable[float] | None = None,
) -> ParametricFitResult:
    maturities = np.asarray(list(maturities_years), dtype=float)
    observed = np.asarray(list(observed_yields_pct), dtype=float)
    if maturities.shape != observed.shape or maturities.size < 4:
        raise ValueError("maturities_years and observed_yields_pct must have equal length >= 4")

    fit_weights = np.ones_like(observed) if weights is None else np.asarray(list(weights), dtype=float)
    if fit_weights.shape != observed.shape:
        raise ValueError("weights must match observed_yields_pct length")
    fit_weights = np.maximum(fit_weights, EPSILON)

    if method == "nelson_siegel":
        tau1_grid = np.linspace(0.15, 12.0, 80)
        return _fit_nelson_siegel_from_tau_grid(maturities, observed, fit_weights, tau1_grid=tau1_grid)

    if method == "svensson":
        tau1_grid = np.linspace(0.20, 8.0, 50)
        tau2_grid = np.linspace(1.0, 20.0, 60)
        return _fit_svensson_from_tau_grid(maturities, observed, fit_weights, tau1_grid=tau1_grid, tau2_grid=tau2_grid)

    raise ValueError(f"Unsupported fit method: {method}")


def constant_maturity_yields(
    fit_result: ParametricFitResult,
    target_maturities_years: Iterable[float],
) -> np.ndarray:
    maturities = np.asarray(list(target_maturities_years), dtype=float)
    if fit_result.method == "nelson_siegel":
        return nelson_siegel_yield(
            maturities,
            beta0=fit_result.params["beta0"],
            beta1=fit_result.params["beta1"],
            beta2=fit_result.params["beta2"],
            tau1=fit_result.params["tau1"],
        )

    return svensson_yield(
        maturities,
        beta0=fit_result.params["beta0"],
        beta1=fit_result.params["beta1"],
        beta2=fit_result.params["beta2"],
        beta3=fit_result.params["beta3"],
        tau1=fit_result.params["tau1"],
        tau2=fit_result.params["tau2"],
    )

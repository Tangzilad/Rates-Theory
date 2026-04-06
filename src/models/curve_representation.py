"""Curve representation and comparison utilities for chapter 6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from constants import EPSILON
from src.models.yield_curve import NSSParameters, fit_nelson_siegel_svensson, nss_yield


@dataclass(frozen=True)
class ResidualDiagnostics:
    rmse_nss_bp: float
    rmse_interp_bp: float
    mean_abs_nss_bp: float
    mean_abs_interp_bp: float
    max_abs_nss_bp: float
    max_abs_interp_bp: float


def _as_sorted_arrays(maturities: Iterable[float], rates: Iterable[float]) -> tuple[np.ndarray, np.ndarray]:
    m = np.asarray(list(maturities), dtype=float)
    r = np.asarray(list(rates), dtype=float)
    if m.size != r.size or m.size < 2:
        raise ValueError("maturities and rates must have same length >= 2")
    order = np.argsort(m)
    m_sorted = m[order]
    r_sorted = r[order]
    if np.any(np.diff(m_sorted) <= 0):
        raise ValueError("maturities must be strictly increasing")
    return m_sorted, r_sorted


def par_to_zero_bootstrap(maturities: Iterable[float], par_rates_pct: Iterable[float]) -> np.ndarray:
    """Pedagogical annual-pay par-to-zero bootstrap in percent units."""
    m, par = _as_sorted_arrays(maturities, par_rates_pct)
    if not np.allclose(m, np.round(m), atol=1e-8):
        raise ValueError("bootstrap expects integer-year maturities")

    zeros = np.zeros_like(par, dtype=float)
    dfs = np.zeros_like(par, dtype=float)

    for idx, maturity in enumerate(m.astype(int)):
        coupon = par[idx] / 100.0
        if maturity == 1:
            df = 1.0 / (1.0 + coupon)
        else:
            prior_coupons = coupon * np.sum(dfs[: idx])
            df = (1.0 - prior_coupons) / (1.0 + coupon)
        df = max(df, EPSILON)
        dfs[idx] = df
        zeros[idx] = (df ** (-1.0 / maturity) - 1.0) * 100.0

    return zeros


def zero_to_forward(maturities: Iterable[float], zero_rates_pct: Iterable[float]) -> np.ndarray:
    """Convert spot zero rates (%) to simple forward rates (%) between nodes."""
    m, z = _as_sorted_arrays(maturities, zero_rates_pct)
    z_dec = z / 100.0
    forwards = np.zeros_like(z_dec)
    forwards[0] = z[0]

    for i in range(1, len(m)):
        t_prev = m[i - 1]
        t_curr = m[i]
        growth_curr = (1.0 + z_dec[i]) ** t_curr
        growth_prev = (1.0 + z_dec[i - 1]) ** t_prev
        dt = max(t_curr - t_prev, EPSILON)
        fwd = (growth_curr / growth_prev) ** (1.0 / dt) - 1.0
        forwards[i] = fwd * 100.0

    return forwards


def piecewise_linear_curve(maturities: Iterable[float], rates_pct: Iterable[float], target_maturities: Iterable[float]) -> np.ndarray:
    """Piecewise linear interpolation/extrapolation in rate space."""
    m, r = _as_sorted_arrays(maturities, rates_pct)
    t = np.asarray(list(target_maturities), dtype=float)
    interpolated = np.interp(t, m, r)
    if t.size == 0:
        return interpolated
    left_mask = t < m[0]
    right_mask = t > m[-1]
    if left_mask.any():
        slope_left = (r[1] - r[0]) / max(m[1] - m[0], EPSILON)
        interpolated[left_mask] = r[0] + slope_left * (t[left_mask] - m[0])
    if right_mask.any():
        slope_right = (r[-1] - r[-2]) / max(m[-1] - m[-2], EPSILON)
        interpolated[right_mask] = r[-1] + slope_right * (t[right_mask] - m[-1])
    return interpolated


def fit_nss_zero_curve(maturities: Iterable[float], zero_rates_pct: Iterable[float]) -> NSSParameters:
    """Fit NSS parameters to zero-rate observations in percent units."""
    return fit_nelson_siegel_svensson(maturities=maturities, yields=zero_rates_pct)


def evaluate_nss_curve(maturities: Iterable[float], params: NSSParameters) -> np.ndarray:
    m = np.asarray(list(maturities), dtype=float)
    return np.array([nss_yield(float(mt), params) for mt in m], dtype=float)


def residual_diagnostics(observed_pct: Iterable[float], fitted_nss_pct: Iterable[float], fitted_interp_pct: Iterable[float]) -> ResidualDiagnostics:
    obs = np.asarray(list(observed_pct), dtype=float)
    nss = np.asarray(list(fitted_nss_pct), dtype=float)
    interp = np.asarray(list(fitted_interp_pct), dtype=float)
    if obs.size != nss.size or obs.size != interp.size:
        raise ValueError("all residual vectors must have matching length")

    nss_resid_bp = (obs - nss) * 100.0
    interp_resid_bp = (obs - interp) * 100.0
    return ResidualDiagnostics(
        rmse_nss_bp=float(np.sqrt(np.mean(nss_resid_bp**2))),
        rmse_interp_bp=float(np.sqrt(np.mean(interp_resid_bp**2))),
        mean_abs_nss_bp=float(np.mean(np.abs(nss_resid_bp))),
        mean_abs_interp_bp=float(np.mean(np.abs(interp_resid_bp))),
        max_abs_nss_bp=float(np.max(np.abs(nss_resid_bp))),
        max_abs_interp_bp=float(np.max(np.abs(interp_resid_bp))),
    )

"""Ornstein-Uhlenbeck mean-reversion utilities for relative-value spread analytics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from constants import EPSILON, SHARPE_ANNUALIZATION_FACTOR, TRADING_DAYS_PER_YEAR


@dataclass(frozen=True)
class OUParameters:
    """Container for Ornstein-Uhlenbeck parameters."""

    theta: float
    mu: float
    sigma: float


def simulate_ou(
    x0: float,
    theta: float,
    mu: float,
    sigma: float,
    n_steps: int,
    dt: float = 1.0 / TRADING_DAYS_PER_YEAR,
    n_paths: int = 1,
    random_seed: int | None = None,
) -> np.ndarray:
    """Simulate OU paths with Euler discretization.

    Returns an array of shape ``(n_paths, n_steps + 1)``.
    """
    if theta < 0 or sigma < 0:
        raise ValueError("theta and sigma must be non-negative")
    if n_steps <= 0 or n_paths <= 0:
        raise ValueError("n_steps and n_paths must be positive")

    rng = np.random.default_rng(random_seed)
    paths = np.zeros((n_paths, n_steps + 1), dtype=float)
    paths[:, 0] = x0
    sqrt_dt = np.sqrt(dt)

    for t in range(n_steps):
        z = rng.standard_normal(n_paths)
        paths[:, t + 1] = (
            paths[:, t]
            + theta * (mu - paths[:, t]) * dt
            + sigma * sqrt_dt * z
        )
    return paths


def estimate_ou_parameters(series: Iterable[float], dt: float = 1.0 / TRADING_DAYS_PER_YEAR) -> OUParameters:
    """Estimate OU parameters via AR(1) regression mapping."""
    x = np.asarray(list(series), dtype=float)
    if x.size < 3:
        raise ValueError("series must contain at least 3 observations")

    x_prev = x[:-1]
    x_next = x[1:]
    a, b = np.polyfit(x_prev, x_next, deg=1)
    b = float(np.clip(b, EPSILON, 1 - EPSILON))

    theta = -np.log(b) / dt
    mu = a / (1.0 - b)

    resid = x_next - (a + b * x_prev)
    resid_var = float(np.var(resid, ddof=1))
    sigma = np.sqrt(max(2.0 * theta * resid_var / max(1.0 - b**2, EPSILON), 0.0))

    return OUParameters(theta=theta, mu=mu, sigma=sigma)


def conditional_expectation(
    x_t: float,
    horizon: float,
    theta: float,
    mu: float,
) -> float:
    """Compute E[X_{t+h} | X_t=x_t] for an OU process."""
    return mu + (x_t - mu) * np.exp(-theta * horizon)


def sharpe_ratio(returns: Iterable[float], risk_free_rate: float = 0.0, annualize: bool = True) -> float:
    """Compute (annualized) Sharpe ratio from return observations."""
    r = np.asarray(list(returns), dtype=float)
    if r.size < 2:
        raise ValueError("returns must contain at least 2 observations")

    excess = r - risk_free_rate
    vol = float(np.std(excess, ddof=1))
    if vol <= EPSILON:
        return 0.0

    sr = float(np.mean(excess) / vol)
    return sr * SHARPE_ANNUALIZATION_FACTOR if annualize else sr


def first_passage_time_approx(
    x0: float,
    level: float,
    theta: float,
    mu: float,
    sigma: float,
) -> float:
    """Approximate expected first-passage time for OU using an effective drift heuristic.

    This is a rough approximation useful for ranking opportunities, not exact pricing.
    """
    if sigma <= 0 or theta <= 0:
        raise ValueError("theta and sigma must be positive")

    distance = abs(level - x0)
    if distance <= EPSILON:
        return 0.0

    kappa_eff = theta * max(abs(mu - x0), EPSILON)
    return float(distance / kappa_eff + (distance**2) / (sigma**2 + EPSILON))

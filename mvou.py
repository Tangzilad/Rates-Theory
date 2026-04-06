"""Multivariate Ornstein-Uhlenbeck process implementation for correlated spreads."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from constants import TRADING_DAYS_PER_YEAR


@dataclass
class MVOUProcess:
    """Multivariate OU process defined by drift matrix and covariance.

    Dynamics:
        dX_t = K(\mu - X_t)dt + L dW_t, where covariance is ``LL^T``.
    """

    kappa: np.ndarray
    mu: np.ndarray
    covariance: np.ndarray

    def __post_init__(self) -> None:
        self.kappa = np.asarray(self.kappa, dtype=float)
        self.mu = np.asarray(self.mu, dtype=float)
        self.covariance = np.asarray(self.covariance, dtype=float)

        n = self.mu.shape[0]
        if self.kappa.shape != (n, n):
            raise ValueError("kappa must be square and match mu dimension")
        if self.covariance.shape != (n, n):
            raise ValueError("covariance must be square and match mu dimension")

        self._chol = np.linalg.cholesky(self.covariance)

    def simulate(
        self,
        x0: np.ndarray,
        n_steps: int,
        dt: float = 1.0 / TRADING_DAYS_PER_YEAR,
        n_paths: int = 1,
        random_seed: int | None = None,
    ) -> np.ndarray:
        """Simulate correlated paths with Euler discretization.

        Returns shape ``(n_paths, n_steps + 1, dimension)``.
        """
        x0 = np.asarray(x0, dtype=float)
        dim = self.mu.shape[0]
        if x0.shape != (dim,):
            raise ValueError("x0 dimension mismatch")

        rng = np.random.default_rng(random_seed)
        paths = np.zeros((n_paths, n_steps + 1, dim), dtype=float)
        paths[:, 0, :] = x0

        sqrt_dt = np.sqrt(dt)
        for t in range(n_steps):
            z = rng.standard_normal((n_paths, dim))
            diffusion = z @ self._chol.T * sqrt_dt
            drift = (self.mu - paths[:, t, :]) @ self.kappa.T * dt
            paths[:, t + 1, :] = paths[:, t, :] + drift + diffusion

        return paths

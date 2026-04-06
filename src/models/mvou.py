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

    def expected_path(
        self,
        x0: np.ndarray,
        n_steps: int,
        dt: float = 1.0 / TRADING_DAYS_PER_YEAR,
    ) -> np.ndarray:
        """Compute E[X_t] for a matrix OU process.

        Uses matrix exponential via eigendecomposition:
            E[X_t] = mu + exp(-K t)(x0 - mu)

        Returns shape ``(n_steps + 1, dimension)``.
        """
        x0 = np.asarray(x0, dtype=float)
        dim = self.mu.shape[0]
        if x0.shape != (dim,):
            raise ValueError("x0 dimension mismatch")

        evals, evecs = np.linalg.eig(self.kappa)
        inv_evecs = np.linalg.inv(evecs)

        expected = np.zeros((n_steps + 1, dim), dtype=float)
        delta = x0 - self.mu
        for step in range(n_steps + 1):
            t = step * dt
            exp_diag = np.diag(np.exp(-evals * t))
            exp_k = (evecs @ exp_diag @ inv_evecs).real
            expected[step, :] = self.mu + exp_k @ delta
        return expected

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


def simulate_mvou_2d(
    kappa: np.ndarray,
    mu: np.ndarray,
    covariance: np.ndarray,
    x0: np.ndarray,
    n_steps: int,
    dt: float = 1.0 / TRADING_DAYS_PER_YEAR,
    n_paths: int = 200,
    random_seed: int | None = None,
) -> np.ndarray:
    """Convenience helper for a two-leg joint spread process."""
    process = MVOUProcess(kappa=np.asarray(kappa, dtype=float), mu=np.asarray(mu, dtype=float), covariance=np.asarray(covariance, dtype=float))
    if process.mu.shape[0] != 2:
        raise ValueError("simulate_mvou_2d expects dimension 2")
    return process.simulate(x0=np.asarray(x0, dtype=float), n_steps=n_steps, dt=dt, n_paths=n_paths, random_seed=random_seed)


def simulate_mvou_3d(
    kappa: np.ndarray,
    mu: np.ndarray,
    covariance: np.ndarray,
    x0: np.ndarray,
    n_steps: int,
    dt: float = 1.0 / TRADING_DAYS_PER_YEAR,
    n_paths: int = 200,
    random_seed: int | None = None,
) -> np.ndarray:
    """Convenience helper for a three-leg joint spread process."""
    process = MVOUProcess(kappa=np.asarray(kappa, dtype=float), mu=np.asarray(mu, dtype=float), covariance=np.asarray(covariance, dtype=float))
    if process.mu.shape[0] != 3:
        raise ValueError("simulate_mvou_3d expects dimension 3")
    return process.simulate(x0=np.asarray(x0, dtype=float), n_steps=n_steps, dt=dt, n_paths=n_paths, random_seed=random_seed)


def compare_independent_vs_joint(
    kappa: np.ndarray,
    mu: np.ndarray,
    covariance: np.ndarray,
    x0: np.ndarray,
    n_steps: int,
    dt: float = 1.0 / TRADING_DAYS_PER_YEAR,
    n_paths: int = 400,
    random_seed: int | None = None,
) -> dict[str, float]:
    """Compare independent-per-leg OU against joint MVOU.

    Independent setup keeps only diagonal K and covariance terms.
    """
    kappa = np.asarray(kappa, dtype=float)
    mu = np.asarray(mu, dtype=float)
    covariance = np.asarray(covariance, dtype=float)
    x0 = np.asarray(x0, dtype=float)

    joint_process = MVOUProcess(kappa=kappa, mu=mu, covariance=covariance)
    joint_paths = joint_process.simulate(x0=x0, n_steps=n_steps, dt=dt, n_paths=n_paths, random_seed=random_seed)

    ind_kappa = np.diag(np.diag(kappa))
    ind_covariance = np.diag(np.diag(covariance))
    independent_process = MVOUProcess(kappa=ind_kappa, mu=mu, covariance=ind_covariance)
    independent_paths = independent_process.simulate(x0=x0, n_steps=n_steps, dt=dt, n_paths=n_paths, random_seed=random_seed)

    joint_terminal = joint_paths[:, -1, :]
    independent_terminal = independent_paths[:, -1, :]

    joint_corr = float(np.corrcoef(joint_terminal.T)[0, 1]) if joint_terminal.shape[1] >= 2 else 0.0
    independent_corr = float(np.corrcoef(independent_terminal.T)[0, 1]) if independent_terminal.shape[1] >= 2 else 0.0

    joint_mean = joint_paths.mean(axis=0)
    independent_mean = independent_paths.mean(axis=0)
    mean_path_rmse = float(np.sqrt(np.mean((joint_mean - independent_mean) ** 2)))

    return {
        "joint_terminal_corr": joint_corr,
        "independent_terminal_corr": independent_corr,
        "mean_path_rmse": mean_path_rmse,
    }


def non_monotonic_expected_path_example(
    n_steps: int = 252,
    dt: float = 1.0 / TRADING_DAYS_PER_YEAR,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Create a damped-oscillation OU expectation example.

    Returns ``(kappa, mu, covariance, x0, expected_path)``.
    """
    kappa = np.array([[1.10, -1.80], [1.80, 1.10]], dtype=float)
    mu = np.array([0.0, 0.0], dtype=float)
    covariance = np.array([[0.45, 0.08], [0.08, 0.30]], dtype=float)
    x0 = np.array([1.2, -0.3], dtype=float)

    process = MVOUProcess(kappa=kappa, mu=mu, covariance=covariance)
    expected = process.expected_path(x0=x0, n_steps=n_steps, dt=dt)
    return kappa, mu, covariance, x0, expected

"""Principal component analysis helpers for yield-curve and spread matrices."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from constants import EPSILON


@dataclass(frozen=True)
class PCAResult:
    """Structured PCA output."""

    standardized_data: np.ndarray
    eigenvalues: np.ndarray
    eigenvectors: np.ndarray
    explained_variance_ratio: np.ndarray
    loadings: np.ndarray


def standardize_matrix(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Z-score a 2D matrix by column."""
    x = np.asarray(matrix, dtype=float)
    if x.ndim != 2:
        raise ValueError("matrix must be 2D")

    mean = x.mean(axis=0)
    std = x.std(axis=0, ddof=1)
    std = np.where(std <= EPSILON, 1.0, std)
    return (x - mean) / std, mean, std


def run_pca(yield_matrix: np.ndarray, n_components: int | None = None) -> PCAResult:
    """Run PCA over standardized yield observations (rows=time, cols=tenors)."""
    z, _, _ = standardize_matrix(yield_matrix)
    cov = np.cov(z, rowvar=False)
    eigvals, eigvecs = np.linalg.eigh(cov)

    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]

    if n_components is not None:
        eigvals = eigvals[:n_components]
        eigvecs = eigvecs[:, :n_components]

    total_var = float(np.sum(np.maximum(eigvals, 0.0)))
    explained = eigvals / (total_var + EPSILON)
    loadings = eigvecs * np.sqrt(np.maximum(eigvals, 0.0))

    return PCAResult(
        standardized_data=z,
        eigenvalues=eigvals,
        eigenvectors=eigvecs,
        explained_variance_ratio=explained,
        loadings=loadings,
    )


def factor_neutral_weights(
    exposures: np.ndarray,
    target_notional: float = 1.0,
    neutral_factors: Iterable[int] = (0, 1),
) -> np.ndarray:
    """Construct minimum-norm portfolio weights neutral to selected factor exposures.

    Parameters
    ----------
    exposures:
        Matrix of shape ``(n_assets, n_factors)``.
    target_notional:
        Sum of absolute weights after scaling.
    neutral_factors:
        Indices of factor columns to neutralize.
    """
    e = np.asarray(exposures, dtype=float)
    if e.ndim != 2:
        raise ValueError("exposures must be 2D")

    idx = list(neutral_factors)
    if not idx:
        raw = np.ones(e.shape[0])
    else:
        a = e[:, idx].T
        u, s, vh = np.linalg.svd(a)
        rank = np.sum(s > EPSILON)
        null_space = vh[rank:].T
        if null_space.shape[1] == 0:
            raise ValueError("No feasible factor-neutral portfolio exists")
        raw = null_space[:, 0]

    scale = target_notional / (np.sum(np.abs(raw)) + EPSILON)
    return raw * scale

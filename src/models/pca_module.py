"""Backward-compatible wrappers for PCA helpers.

Prefer importing from :mod:`src.models.pca`.
"""

from .pca import PCAResult, factor_neutral_weights, run_pca, standardize_matrix

__all__ = ["PCAResult", "standardize_matrix", "run_pca", "factor_neutral_weights"]

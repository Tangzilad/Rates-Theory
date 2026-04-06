import numpy as np
import pytest

from src.models.pca_module import factor_neutral_weights, run_pca, standardize_matrix


def test_standardize_matrix_returns_zero_mean_columns():
    x = np.array([[1.0, 2.0], [2.0, 4.0], [3.0, 6.0]])
    z, mean, std = standardize_matrix(x)
    assert z.shape == x.shape
    assert np.allclose(z.mean(axis=0), [0.0, 0.0], atol=1e-12)
    assert mean.shape == (2,)
    assert std.shape == (2,)


def test_run_pca_shapes_and_sorted_eigenvalues():
    x = np.array([[1.0, 2.0, 3.0], [1.2, 2.1, 2.9], [0.8, 1.9, 3.1], [1.1, 2.0, 3.0]])
    res = run_pca(x)
    assert res.eigenvalues.shape == (3,)
    assert np.all(np.diff(res.eigenvalues) <= 1e-12)
    assert res.explained_variance_ratio.shape == (3,)


def test_factor_neutral_weights_sum_abs_matches_target_notional():
    exposures = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    w = factor_neutral_weights(exposures, target_notional=2.0, neutral_factors=(0, 1))
    assert np.isclose(np.sum(np.abs(w)), 2.0, atol=1e-8)


def test_factor_neutral_weights_rejects_non_2d():
    with pytest.raises(ValueError):
        factor_neutral_weights(np.array([1.0, 2.0, 3.0]))

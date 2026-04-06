import numpy as np
import pytest

from src.models.mean_reversion import conditional_expectation, estimate_ou_parameters, sharpe_ratio, simulate_ou


def test_simulate_ou_shape_and_seed_reproducibility():
    paths_a = simulate_ou(0.0, theta=1.1, mu=0.2, sigma=0.3, n_steps=20, n_paths=4, random_seed=42)
    paths_b = simulate_ou(0.0, theta=1.1, mu=0.2, sigma=0.3, n_steps=20, n_paths=4, random_seed=42)
    assert paths_a.shape == (4, 21)
    assert np.allclose(paths_a, paths_b)


def test_estimate_ou_parameters_produces_valid_values():
    series = np.linspace(-0.5, 0.5, 120)
    params = estimate_ou_parameters(series)
    assert params.theta > 0.0
    assert np.isfinite(params.mu)
    assert params.sigma >= 0.0


def test_conditional_expectation_reverts_towards_mu():
    out = conditional_expectation(x_t=2.0, horizon=1.0, theta=2.0, mu=0.0)
    assert out < 2.0


def test_sharpe_ratio_requires_multiple_points():
    with pytest.raises(ValueError):
        sharpe_ratio([0.01])

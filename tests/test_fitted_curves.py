import numpy as np

from src.models.yield_curve import (
    constant_maturity_interpolation,
    fit_nelson_siegel_svensson,
    nss_yield,
    rich_cheap_indicators,
)


def test_nss_fit_and_evaluation_on_synthetic_curve():
    maturities = np.array([0.5, 1.0, 2.0, 5.0, 10.0])
    yields = np.array([0.02, 0.022, 0.025, 0.03, 0.033])

    params = fit_nelson_siegel_svensson(maturities, yields)
    y5 = nss_yield(5.0, params)
    assert np.isfinite(y5)


def test_constant_maturity_interpolation_in_range():
    maturities = [1.0, 3.0, 5.0]
    yields = [0.02, 0.03, 0.035]
    y4 = constant_maturity_interpolation(maturities, yields, target_maturity=4.0)
    assert 0.03 <= y4 <= 0.035


def test_rich_cheap_indicators_shapes():
    maturities = np.array([1.0, 2.0, 3.0, 5.0])
    yields = np.array([0.02, 0.024, 0.027, 0.031])
    params = fit_nelson_siegel_svensson(maturities, yields)

    out = rich_cheap_indicators(maturities, yields, params)
    assert set(out.keys()) == {"fitted", "residual", "zscore"}
    assert out["fitted"].shape == yields.shape
    assert out["residual"].shape == yields.shape
    assert out["zscore"].shape == yields.shape

from __future__ import annotations

import importlib
import json
import math
import sys
from pathlib import Path
from types import ModuleType

import numpy as np

from src.chapter_summary_schema import (
    CHAPTER_REQUIRED_FIELDS,
    document_to_chapter_map,
    parse_chapters_map,
    parse_schema_document,
    parser_summaries_to_document,
)
from src.chapters.base import ChapterBase
from src.chapters.registry import build_chapter_registry
from src.models.ou import conditional_expectation, estimate_ou_parameters, simulate_ou
from src.models.pca import run_pca
from src.models.risk_measures import (
    convexity,
    dv01,
    macaulay_duration,
    modified_duration,
    present_value,
)
from src.models.yield_curve import (
    constant_maturity_interpolation,
    fit_nelson_siegel_svensson,
    rich_cheap_indicators,
)


class _NoOpContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _StreamlitStub(ModuleType):
    def __init__(self):
        super().__init__("streamlit")
        self.sidebar = self

    def set_page_config(self, *args, **kwargs):
        return None

    def selectbox(self, _label, options, index=0, **kwargs):
        return list(options)[index]

    def number_input(self, *args, **kwargs):
        return kwargs.get("value", args[1] if len(args) > 1 else 0.0)

    def slider(self, *args, **kwargs):
        if "value" in kwargs:
            return kwargs["value"]
        return args[3] if len(args) > 3 else None

    def columns(self, n, **kwargs):
        return [self for _ in range(n)]

    def expander(self, *args, **kwargs):
        return _NoOpContext()

    def container(self, *args, **kwargs):
        return _NoOpContext()

    def stop(self):
        raise RuntimeError("streamlit.stop() called during import")

    def __getattr__(self, _name):
        return lambda *args, **kwargs: None


def test_chapters_json_passes_schema_validation() -> None:
    payload = json.loads(Path("data/chapters.json").read_text(encoding="utf-8"))

    parsed = parse_chapters_map(payload)

    assert len(parsed) == 18
    assert set(parsed.keys()) == {str(i) for i in range(1, 19)}
    for chapter in parsed.values():
        for field in CHAPTER_REQUIRED_FIELDS:
            assert field in chapter


def test_registry_loads_all_18_chapter_modules() -> None:
    registry = build_chapter_registry()

    assert list(registry.keys()) == [str(i) for i in range(1, 19)]
    assert all(isinstance(chapter, ChapterBase) for chapter in registry.values())


def test_streamlit_app_import_loads_without_chapter_import_errors(monkeypatch) -> None:
    streamlit_stub = _StreamlitStub()
    monkeypatch.setitem(sys.modules, "streamlit", streamlit_stub)

    for module_name, module in list(sys.modules.items()):
        if module is None:
            continue
        if module_name.startswith("src.chapters.") or module_name.startswith("src.ui."):
            monkeypatch.setattr(module, "st", streamlit_stub, raising=False)

    sys.modules.pop("streamlit_app.app", None)
    module = importlib.import_module("streamlit_app.app")

    assert module.__name__ == "streamlit_app.app"
    assert callable(module.load_primary_chapters)
    assert len(module.build_chapter_registry()) == 18


def test_parser_output_is_compatible_with_schema_adapter() -> None:
    parser_payload = [
        {
            "chapter_number": "1",
            "title": "Synthetic Chapter",
            "summary_sentences": ["Sentence one.", "Sentence two."],
            "quote_candidates": ["Quote A", "Quote A", ""],
        }
    ]

    document = parser_summaries_to_document(parser_payload)
    parsed_document = parse_schema_document(document)
    chapter_map = document_to_chapter_map(parsed_document)

    assert parsed_document["schema_version"] == "1.0"
    assert chapter_map["1"]["summary"] == "Sentence one. Sentence two."
    assert chapter_map["1"]["quotes"] == ["Quote A"]


def test_ou_outputs_shape_half_life_and_conditional_expectation() -> None:
    paths = simulate_ou(
        x0=0.5,
        theta=1.2,
        mu=1.0,
        sigma=0.1,
        n_steps=16,
        n_paths=4,
        random_seed=7,
        dt=1.0 / 252.0,
    )
    assert paths.shape == (4, 17)

    synthetic_series = np.array([0.20, 0.24, 0.27, 0.31, 0.35, 0.38, 0.40, 0.41], dtype=float)
    params = estimate_ou_parameters(synthetic_series, dt=1.0)
    half_life = math.log(2.0) / params.theta

    assert params.theta > 0
    assert half_life > 0

    expected = conditional_expectation(x_t=0.8, horizon=2.0, theta=0.5, mu=1.0)
    manual = 1.0 + (0.8 - 1.0) * math.exp(-0.5 * 2.0)
    assert expected == manual


def test_pca_output_shapes_and_explained_variance_ordering() -> None:
    yield_matrix = np.array(
        [
            [2.00, 2.15, 2.25, 2.40],
            [2.05, 2.19, 2.30, 2.44],
            [2.08, 2.22, 2.33, 2.48],
            [2.12, 2.26, 2.36, 2.52],
            [2.15, 2.30, 2.40, 2.55],
            [2.18, 2.33, 2.43, 2.59],
        ],
        dtype=float,
    )

    result = run_pca(yield_matrix)

    assert result.standardized_data.shape == yield_matrix.shape
    assert result.eigenvalues.shape == (4,)
    assert result.eigenvectors.shape == (4, 4)
    assert result.loadings.shape == (4, 4)
    assert np.all(np.diff(result.explained_variance_ratio) <= 1e-12)


def test_risk_measures_outputs_are_consistent() -> None:
    cashflows = np.array([5.0, 5.0, 105.0], dtype=float)
    times = np.array([1.0, 2.0, 3.0], dtype=float)
    ytm = 0.04

    pv = present_value(cashflows, times, ytm)
    d_mac = macaulay_duration(cashflows, times, ytm)
    d_mod = modified_duration(cashflows, times, ytm)
    risk_dv01 = dv01(cashflows, times, ytm)
    cx = convexity(cashflows, times, ytm)

    assert pv > 0
    assert d_mac > 0
    assert d_mod > 0
    assert d_mod < d_mac
    assert risk_dv01 > 0
    assert cx > 0


def test_fitted_curve_residuals_and_constant_maturity_export() -> None:
    maturities = np.array([1.0, 2.0, 3.0, 5.0, 7.0, 10.0], dtype=float)
    observed = np.array([2.10, 2.18, 2.24, 2.36, 2.45, 2.58], dtype=float)

    params = fit_nelson_siegel_svensson(
        maturities,
        observed,
        tau1_grid=[1.0, 1.5, 2.0],
        tau2_grid=[5.0, 8.0, 12.0],
    )
    indicators = rich_cheap_indicators(maturities, observed, params)
    cm_4y = constant_maturity_interpolation(maturities, observed, target_maturity=4.0)

    assert indicators["fitted"].shape == observed.shape
    assert indicators["residual"].shape == observed.shape
    assert indicators["zscore"].shape == observed.shape
    assert math.isfinite(cm_4y)
    assert observed.min() <= cm_4y <= observed.max()

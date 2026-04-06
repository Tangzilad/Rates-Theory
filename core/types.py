from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class _TypedState:
    """Base typed state helper with pydantic-like dump semantics."""

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TradeResidualSeries(_TypedState):
    labels: list[str]
    residuals: list[float]
    zscores: list[float]


@dataclass(frozen=True)
class MeanReversionState(_TypedState):
    theta: float
    mu: float
    sigma: float
    x0: float
    current_z_score: float
    half_life: float | None
    first_passage_probability: float
    mean_first_passage_time: float | None
    terminal_sharpe: float
    conditional_expectation_term_structure: dict[str, list[float]]


@dataclass(frozen=True)
class FactorState(_TypedState):
    columns: list[str]
    explained_variance: list[float]
    eigenvectors: dict[str, list[float]]
    factor_scores: dict[str, list[float]]
    residualized_series: dict[str, list[float]]
    candidate_neutral_hedge_weights: dict[str, float]




@dataclass(frozen=True)
class MVOUState(_TypedState):
    k_matrix: list[list[float]]
    mu_vector: list[float]
    covariance_matrix: list[list[float]]
    expected_path: list[list[float]]
    simulated_joint_paths: list[list[list[float]]]
    hedge_suggestions: list[str]

@dataclass(frozen=True)
class RegimeState(_TypedState):
    level_loading: float
    slope_loading: float
    curvature_loading: float
    regime_score: float
    regime_label: str
    regime_confidence: float


@dataclass(frozen=True)
class JointSpreadState(_TypedState):
    fair_futures: float
    basis: float
    direction: str
    residual_series: TradeResidualSeries | None = None
    mean_reversion: MeanReversionState | None = None
    factors: FactorState | None = None




@dataclass(frozen=True)
class RelativeValueState(_TypedState):
    fair_value: float
    market_value: float
    residual: float
    direction: str
    confidence: float
    friction_notes: list[str]


@dataclass(frozen=True)
class RiskMetricState(_TypedState):
    curve_slope_bp: float = 0.0
    duration: float = 0.0
    convexity: float = 0.0
    dy_bp: int = 0
    dp_pct: float = 0.0
    fair_price: float = 0.0
    pv: float = 0.0
    macaulay_duration: float = 0.0
    modified_duration: float = 0.0
    dv01: float = 0.0
    slope: float = 0.0
    fair_price_under_shock: float = 0.0
    approximation_error: float = 0.0


@dataclass(frozen=True)
class MultiCurveState(_TypedState):
    ois_rate_pct: float
    ibor_rate_pct: float
    maturity_years: float
    discount_factor: float
    forward_rate_pct: float
    basis_bp: float


@dataclass(frozen=True)
class FundingBasisState(_TypedState):
    funding_basis_bp: float
    adjusted_fair_spread_bp: float
    net_carry_bp: float


@dataclass(frozen=True)
class FuturesBasisState(_TypedState):
    utilization: float
    headroom: float
    status: str
    approved: bool


@dataclass(frozen=True)
class CurveFairValueState(_TypedState):
    model_fair_value_bp: float
    market_observed_bp: float
    residual_bp: float
    z_score: float
    trade_signal: str
    confidence: float


@dataclass(frozen=True)
class GovBondTradeBlueprint(_TypedState):
    trade_name: str
    entry_leg: str
    hedge_leg: str
    target_notional_mm: float
    hedge_ratio: float
    expected_edge_bp: float
    dv01_neutrality_gap_usd_per_bp: float
    stop_loss_bp: float
    take_profit_bp: float
    approved: bool


@dataclass(frozen=True)
class ReferenceRateState(_TypedState):
    legacy_fixing_pct: float
    rfr_compounded_pct: float
    contract_adjustment_bp: float
    fallback_spread_bp: float
    all_in_coupon_pct: float
    coupon_vs_legacy_bp: float


@dataclass(frozen=True)
class AssetSwapState(_TypedState):
    z_spread_bp: float
    bond_coupon_pct: float
    swap_rate_pct: float
    repo_drag_bp: float
    coupon_mismatch_bp: float
    asset_swap_spread_bp: float
    package_carry_bp: float


@dataclass(frozen=True)
class CurvePoint(_TypedState):
    maturity_years: float
    rate_pct: float


@dataclass(frozen=True)
class ResidualDiagnosticsState(_TypedState):
    rmse_nss_bp: float
    rmse_interp_bp: float
    mean_abs_nss_bp: float
    mean_abs_interp_bp: float
    max_abs_nss_bp: float
    max_abs_interp_bp: float


@dataclass(frozen=True)
class YieldCurveModelState(_TypedState):
    par_curve: list[CurvePoint]
    zero_curve: list[CurvePoint]
    forward_curve: list[CurvePoint]
    fit_params: dict[str, float]
    interpolation_settings: dict[str, float | str]
    residual_diagnostics: ResidualDiagnosticsState


@dataclass(frozen=True)
class ExecutionSignalState(_TypedState):
    action: str
    confidence: float
    rationale: str


@dataclass(frozen=True)
class ChapterExportState(_TypedState):
    signals: list[str]
    usage: str
    schema_name: str


@dataclass(frozen=True)
class ExecutableTradeState(_TypedState):
    joint_spread: JointSpreadState
    risk: RiskMetricState | None = None
    funding: FundingBasisState | None = None
    signal: ExecutionSignalState | None = None
    prerequisites_passed: bool = True
    validation_errors: list[str] = field(default_factory=list)

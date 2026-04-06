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
    barrier: float
    hit_probability: float
    mean_fpt_days: float | None
    terminal_sharpe: float
    half_life_days: float | None


@dataclass(frozen=True)
class FactorState(_TypedState):
    columns: list[str]
    explained_variance: list[float]
    top_loadings: dict[str, list[float]]


@dataclass(frozen=True)
class JointSpreadState(_TypedState):
    fair_futures: float
    basis: float
    direction: str
    residual_series: TradeResidualSeries | None = None
    mean_reversion: MeanReversionState | None = None
    factors: FactorState | None = None


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
class FundingBasisState(_TypedState):
    swap_spread_bp: float
    asset_swap_spread_bp: float
    tenor_basis_bp: float
    cross_currency_basis_bp: float


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

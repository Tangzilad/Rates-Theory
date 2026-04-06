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
class RecoverySensitivityPoint(_TypedState):
    recovery_rate: float
    hazard_proxy: float
    d_hazard_d_recovery: float


@dataclass(frozen=True)
class PureCreditState(_TypedState):
    observed_spread_bp: float
    liquidity_component_bp: float
    technical_component_bp: float
    purified_spread_bp: float
    hazard_proxy: float
    recovery_rate: float
    d_hazard_d_recovery: float
    recovery_sensitivity_scenarios: list[RecoverySensitivityPoint]
    simplification_notes: list[str]


@dataclass(frozen=True)
class ICBSTermPoint(_TypedState):
    maturity_years: float
    benchmark_a_pct: float
    benchmark_b_pct: float
    basis_bp: float


@dataclass(frozen=True)
class ICBSState(_TypedState):
    benchmark_a_name: str
    benchmark_b_name: str
    current_basis_bp: float
    term_structure: list[ICBSTermPoint]
    carry_estimate_bp: float
    rolldown_estimate_bp: float
    simplification_notes: list[str]


@dataclass(frozen=True)
class CCBSSensitivityPoint(_TypedState):
    basis_shock_bp: float
    shocked_basis_bp: float
    shocked_synthetic_domestic_yield_pct: float


@dataclass(frozen=True)
class CCBSState(_TypedState):
    quote_convention: str
    basis_bp: float
    synthetic_domestic_hedged_yield_pct: float
    sensitivity_table: list[CCBSSensitivityPoint]
    simplification_notes: list[str]


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
    benchmark_rate_pct: float
    reference_rate_name: str
    benchmark_type: str
    package_upfront_pct: float
    repo_funding_rate_pct: float
    funding_shift_bp: float
    coupon_mismatch_bp: float
    asset_swap_spread_bp: float
    package_carry_bp: float
    fair_package_level_bp: float
    funding_sensitivity_bp_per_1bp: float
    simplification_notes: list[str]


@dataclass(frozen=True)
class DependencyNodeState(_TypedState):
    node_id: str
    label: str
    required_inputs: list[str]
    pricing_dependencies: list[str]
    downstream_outputs: list[str]


@dataclass(frozen=True)
class DependencyEdgeState(_TypedState):
    source: str
    target: str
    relation: str


@dataclass(frozen=True)
class ShockNarrativeState(_TypedState):
    shock: str
    transmission_path: list[str]
    required_reprice_nodes: list[str]
    downstream_impact: list[str]


@dataclass(frozen=True)
class DependencyMapState(_TypedState):
    map_name: str
    focal_node: str
    section_focus: str
    nodes: list[DependencyNodeState]
    edges: list[DependencyEdgeState]
    shock_narratives: list[ShockNarrativeState]
    signals: list[str]
    usage: str
    schema_name: str


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
class BondResidualState(_TypedState):
    bond_id: str
    maturity_years: float
    observed_yield_pct: float
    fitted_yield_pct: float
    residual_bp: float
    adjusted_residual_bp: float
    rich_cheap_flag: str


@dataclass(frozen=True)
class RelativeValueScreenState(_TypedState):
    fit_method: str
    fitted_parameters: dict[str, float]
    bonds: list[BondResidualState]
    constant_maturity_yields_pct: dict[str, float]
    residual_rmse_bp: float
    benchmark_adjustment_bp: float
    repo_specialness_bp: float
    outlier_mode: str
    scenario_value: float


@dataclass(frozen=True)
class GlobalRVBondSignalState(_TypedState):
    bond_id: str
    region: str
    maturity_years: float
    observed_yield_pct: float
    curve_residual_bp: float
    curve_residual_zscore: float
    curve_rank: int
    sofr_asw_residual_bp: float
    sofr_asw_residual_zscore: float
    sofr_asw_rank: int
    rank_gap: int
    disagreement_flag: bool
    curve_mismatch_bp: float
    funding_basis_bp: float
    credit_difference_bp: float
    benchmark_choice_bp: float
    composite_signal_score: float
    preferred_trade_direction: str


@dataclass(frozen=True)
class GlobalRVDisagreementState(_TypedState):
    disagreement_count: int
    disagreement_share: float
    mean_rank_gap: float
    max_rank_gap: int
    top_disagreement_bonds: list[str]


@dataclass(frozen=True)
class GlobalRVScreenState(_TypedState):
    universe_source: str
    fit_method: str
    fitted_curve_parameters: dict[str, float]
    bond_signals: list[GlobalRVBondSignalState]
    curve_ranking: list[str]
    sofr_asw_ranking: list[str]
    disagreement_diagnostics: GlobalRVDisagreementState
    attribution_buckets_bp: dict[str, float]
    portfolio_selection_signals: dict[str, float | str | list[str]]
    residual_rmse_bp: float
    rv_spread_pnl: float
    total_stress_pnl: float


@dataclass(frozen=True)
class CommonSpaceNormalizationState(_TypedState):
    frame: str
    reference_rate: str
    transformed_signals_bp: dict[str, float]
    normalized_signals_bp: dict[str, float]


@dataclass(frozen=True)
class AgreementDivergenceDiagnosticsState(_TypedState):
    mean_signal_bp: float
    max_deviation_bp: float
    agreement_ratio: float
    divergence_flag: bool
    directional_votes: dict[str, str]


@dataclass(frozen=True)
class ShockPropagationState(_TypedState):
    shocked_input: str
    shock_bp: float
    propagation_order: list[str]
    shocked_signals_bp: dict[str, float]


@dataclass(frozen=True)
class IntegratedRVState(_TypedState):
    bond_local_space_signal_bp: float
    asset_swap_transformed_signal_bp: float
    basis_transformed_signals_bp: dict[str, float]
    cds_pure_credit_signal_bp: float
    common_space_normalization: CommonSpaceNormalizationState
    agreement_divergence_diagnostics: AgreementDivergenceDiagnosticsState
    shock_propagation_results: ShockPropagationState


@dataclass(frozen=True)
class ShadowCostState(_TypedState):
    structural_fair_spread_bp: float
    observed_spread_bp: float
    spread_gap_bp: float
    spread_bp_value_dollars: float
    shadow_funding_cost_bp: float
    capital_charge_dollars: float
    capital_charge_bp: float
    liquidity_wedge_bp: float
    repo_stress_add_on_bp: float
    adjusted_executable_spread_residual_bp: float
    approval_gate: str

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


@dataclass(frozen=True)
class GovBondTradeBlueprint(_TypedState):
    universe: str
    candidate_bond: str
    rich_cheap_signal: str
    richness_bp: float
    curve_fit_residual_bp: float
    curve_fit_zscore: float
    decomposition: dict[str, float]
    pca_neutralization_applied: bool
    pca_residual_factor_exposure: float
    pca_candidate_weights: dict[str, float]
    mean_reversion_validated: bool
    mean_reversion_metrics: dict[str, float]
    risk_metrics: dict[str, float]
    hedge_comparison: dict[str, dict[str, float]]
    preferred_hedge: str
    trade_direction: str
    conviction: str
    rationale: str

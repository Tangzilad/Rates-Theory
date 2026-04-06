"""Shared numerical assumptions and unit conventions for rates analytics modules."""

from __future__ import annotations

# Time/day-count assumptions
TRADING_DAYS_PER_YEAR: int = 252
CALENDAR_DAYS_PER_YEAR: int = 365
ACT_360_DAYS_PER_YEAR: int = 360
MONTHS_PER_YEAR: int = 12

# Numerical tolerances / defaults
EPSILON: float = 1.0e-12
MAX_NEWTON_ITERATIONS: int = 100
DEFAULT_VOL_LOWER_BOUND: float = 1.0e-6
DEFAULT_VOL_UPPER_BOUND: float = 5.0

# Statistical annualization assumptions
SHARPE_ANNUALIZATION_FACTOR: float = TRADING_DAYS_PER_YEAR**0.5

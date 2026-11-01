"""RiskLens fixed-income analytics engine.

Pure-Python / NumPy / SciPy implementation of bond pricing, yield,
risk, liquidity and portfolio analytics. QuantLib is intentionally
optional so the engine runs and is testable in any environment.

All synthetic/sample values flowing through this engine must be labelled
as simulated by the caller; this library performs calculations only.
"""

from .daycount import year_fraction, DayCount
from .cashflows import CashFlow, generate_bond_cashflows, accrued_interest
from .pricing import (
    price_from_yield,
    dirty_price_from_yield,
    present_value,
)
from .yield_calc import (
    yield_to_maturity,
    yield_to_call,
    yield_to_put,
    current_yield,
    zero_coupon_yield,
)
from .duration.core import macaulay_duration, modified_duration, effective_duration
from .convexity.core import convexity
from .dv01.core import dv01, price_change_estimate
from .liquidity.core import liquidity_score, estimated_liquidation_days
from .portfolio.core import (
    portfolio_cashflows,
    portfolio_ytm,
    xirr,
    weighted_duration,
    portfolio_dv01,
)
from .optimisation.optimizer import optimise_portfolio, OptimisationResult
from .stress_testing.scenarios import run_stress_test

__all__ = [
    "year_fraction",
    "DayCount",
    "CashFlow",
    "generate_bond_cashflows",
    "accrued_interest",
    "price_from_yield",
    "dirty_price_from_yield",
    "present_value",
    "yield_to_maturity",
    "yield_to_call",
    "yield_to_put",
    "current_yield",
    "zero_coupon_yield",
    "macaulay_duration",
    "modified_duration",
    "effective_duration",
    "convexity",
    "dv01",
    "price_change_estimate",
    "liquidity_score",
    "estimated_liquidation_days",
    "portfolio_cashflows",
    "portfolio_ytm",
    "xirr",
    "weighted_duration",
    "portfolio_dv01",
    "optimise_portfolio",
    "OptimisationResult",
    "run_stress_test",
]

__version__ = "0.1.0"

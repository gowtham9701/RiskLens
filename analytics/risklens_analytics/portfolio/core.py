"""Portfolio-level aggregation.

Portfolio YTM is computed as the internal rate of return of the
*aggregated* contractual cash flows against total invested market
value - NOT a naive average of individual bond YTMs. This is the
mathematically appropriate cash-flow-weighted methodology.

Assumptions / limitations:
- Cash flows are contractual (no default/prepayment modelling here).
- Reinvestment of intermediate coupons is at the solved IRR (standard
  IRR assumption).
- FDs and mutual funds should contribute their own cash-flow streams;
  bond YTM formulas are not applied to them indiscriminately.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Sequence, Tuple

from scipy.optimize import brentq

from ..cashflows import CashFlow
from ..daycount import DayCount, year_fraction


@dataclass
class Position:
    """A holding's contribution to the portfolio."""

    instrument_id: str
    market_value: float
    cashflows: List[CashFlow]
    modified_duration: float = 0.0
    dv01: float = 0.0  # per position (currency), already scaled to holding


def portfolio_cashflows(positions: Sequence[Position]) -> List[CashFlow]:
    """Merge positions' cash flows into a single ascending list by date."""
    merged: Dict[date, float] = {}
    for pos in positions:
        for cf in pos.cashflows:
            merged[cf.pay_date] = merged.get(cf.pay_date, 0.0) + cf.amount
    return [CashFlow(d, amt) for d, amt in sorted(merged.items())]


def xirr(
    dated_amounts: Sequence[Tuple[date, float]],
    convention: DayCount | str = DayCount.ACT_365F,
    guess: float = 0.1,
) -> float:
    """Money-weighted return (XIRR) for irregular dated cash flows.

    The series must contain at least one negative (outflow/investment)
    and one positive (inflow) amount.
    """
    items = sorted(dated_amounts, key=lambda x: x[0])
    if not items:
        raise ValueError("No cash flows provided")
    t0 = items[0][0]
    amounts = [a for _, a in items]
    if not (any(a < 0 for a in amounts) and any(a > 0 for a in amounts)):
        raise ValueError("XIRR needs both positive and negative cash flows")

    times = [year_fraction(t0, d, convention) for d, _ in items]

    def npv(rate: float) -> float:
        return sum(a / (1.0 + rate) ** t for a, t in zip(amounts, times))

    lo, hi = -0.9999, 10.0
    f_lo, f_hi = npv(lo), npv(hi)
    if f_lo * f_hi > 0:
        raise ValueError("Unable to bracket XIRR")
    return brentq(npv, lo, hi, maxiter=200, xtol=1e-10)


def portfolio_ytm(
    positions: Sequence[Position],
    as_of: date,
    convention: DayCount | str = DayCount.ACT_365F,
) -> Optional[float]:
    """Cash-flow-weighted portfolio YTM (IRR of aggregated flows).

    Treats total market value today as an outflow and all future
    contractual cash flows as inflows, then solves the single rate.
    Returns None when there are no future cash flows.
    """
    total_mv = sum(p.market_value for p in positions)
    flows = portfolio_cashflows(positions)
    future = [(cf.pay_date, cf.amount) for cf in flows if cf.pay_date > as_of]
    if total_mv <= 0 or not future:
        return None
    series: List[Tuple[date, float]] = [(as_of, -total_mv)] + future
    return xirr(series, convention)


def weighted_duration(positions: Sequence[Position]) -> float:
    """Market-value-weighted modified duration."""
    total = sum(p.market_value for p in positions)
    if total <= 0:
        return 0.0
    return sum(p.modified_duration * p.market_value for p in positions) / total


def portfolio_dv01(positions: Sequence[Position]) -> float:
    """Sum of position-level DV01 (currency per 1bp)."""
    return sum(p.dv01 for p in positions)

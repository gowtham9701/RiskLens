"""Convexity of a fixed-income instrument."""

from __future__ import annotations

from datetime import date
from typing import List

from ..cashflows import CashFlow
from ..daycount import DayCount, year_fraction


def convexity(
    cashflows: List[CashFlow],
    yld: float,
    settlement_date: date,
    frequency: int = 2,
    convention: DayCount | str = DayCount.ACT_365F,
) -> float:
    """Convexity in year^2 units (second derivative of price wrt yield)."""
    comp = frequency if frequency and frequency > 0 else 1
    pv_total = 0.0
    weighted = 0.0
    for cf in cashflows:
        if cf.pay_date <= settlement_date:
            continue
        t = year_fraction(settlement_date, cf.pay_date, convention)
        pv = cf.amount / (1.0 + yld / comp) ** (t * comp)
        pv_total += pv
        weighted += t * (t + 1.0 / comp) * pv
    if pv_total == 0:
        return 0.0
    return weighted / (pv_total * (1.0 + yld / comp) ** 2)

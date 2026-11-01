"""Bond pricing: present value and clean/dirty price from yield."""

from __future__ import annotations

from datetime import date
from typing import List

from ..cashflows import CashFlow, accrued_interest, generate_bond_cashflows
from ..daycount import DayCount, year_fraction


def present_value(
    cashflows: List[CashFlow],
    yld: float,
    settlement_date: date,
    frequency: int = 2,
    convention: DayCount | str = DayCount.ACT_365F,
) -> float:
    """Present value of cash flows discounted at an annual yield.

    Uses periodic compounding at the coupon frequency (yield is a
    nominal annual rate compounded `frequency` times per year). For
    zero-coupon style single flows, frequency is treated as the
    compounding frequency and defaults to annual if frequency <= 0.
    """
    comp = frequency if frequency and frequency > 0 else 1
    pv = 0.0
    for cf in cashflows:
        if cf.pay_date <= settlement_date:
            continue
        t = year_fraction(settlement_date, cf.pay_date, convention)
        periods = t * comp
        pv += cf.amount / (1.0 + yld / comp) ** periods
    return pv


def dirty_price_from_yield(
    issue_date: date,
    maturity_date: date,
    coupon_rate: float,
    frequency: int,
    yld: float,
    settlement_date: date,
    face_value: float = 100.0,
    redemption: float | None = None,
    convention: DayCount | str = DayCount.ACT_365F,
) -> float:
    """Dirty (full) price per face_value for a given yield."""
    flows = generate_bond_cashflows(
        issue_date,
        maturity_date,
        coupon_rate,
        frequency,
        face_value=face_value,
        redemption=redemption,
        settlement_date=settlement_date,
    )
    comp = frequency if frequency and frequency > 0 else 1
    return present_value(flows, yld, settlement_date, comp, convention)


def price_from_yield(
    issue_date: date,
    maturity_date: date,
    coupon_rate: float,
    frequency: int,
    yld: float,
    settlement_date: date,
    face_value: float = 100.0,
    redemption: float | None = None,
    convention: DayCount | str = DayCount.ACT_365F,
) -> float:
    """Clean price per face_value = dirty price - accrued interest."""
    dirty = dirty_price_from_yield(
        issue_date,
        maturity_date,
        coupon_rate,
        frequency,
        yld,
        settlement_date,
        face_value=face_value,
        redemption=redemption,
        convention=convention,
    )
    ai = accrued_interest(
        issue_date,
        maturity_date,
        coupon_rate,
        frequency,
        settlement_date,
        face_value=face_value,
        convention=convention,
    )
    return dirty - ai

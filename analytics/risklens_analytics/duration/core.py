"""Macaulay, modified and effective duration."""

from __future__ import annotations

from datetime import date
from typing import List

from ..cashflows import CashFlow, generate_bond_cashflows
from ..daycount import DayCount, year_fraction
from ..pricing import dirty_price_from_yield


def macaulay_duration(
    cashflows: List[CashFlow],
    yld: float,
    settlement_date: date,
    frequency: int = 2,
    convention: DayCount | str = DayCount.ACT_365F,
) -> float:
    """Macaulay duration in years (time-weighted PV of cash flows)."""
    comp = frequency if frequency and frequency > 0 else 1
    pv_total = 0.0
    weighted = 0.0
    for cf in cashflows:
        if cf.pay_date <= settlement_date:
            continue
        t = year_fraction(settlement_date, cf.pay_date, convention)
        pv = cf.amount / (1.0 + yld / comp) ** (t * comp)
        pv_total += pv
        weighted += t * pv
    if pv_total == 0:
        return 0.0
    return weighted / pv_total


def modified_duration(
    cashflows: List[CashFlow],
    yld: float,
    settlement_date: date,
    frequency: int = 2,
    convention: DayCount | str = DayCount.ACT_365F,
) -> float:
    """Modified duration = Macaulay / (1 + y/m)."""
    comp = frequency if frequency and frequency > 0 else 1
    mac = macaulay_duration(cashflows, yld, settlement_date, comp, convention)
    return mac / (1.0 + yld / comp)


def effective_duration(
    issue_date: date,
    maturity_date: date,
    coupon_rate: float,
    frequency: int,
    yld: float,
    settlement_date: date,
    face_value: float = 100.0,
    redemption: float | None = None,
    convention: DayCount | str = DayCount.ACT_365F,
    bump: float = 0.0001,
) -> float:
    """Effective duration via symmetric yield bump (handles optionality
    when callable/puttable pricing is supplied by the caller)."""
    p_up = dirty_price_from_yield(
        issue_date, maturity_date, coupon_rate, frequency, yld + bump,
        settlement_date, face_value, redemption, convention,
    )
    p_dn = dirty_price_from_yield(
        issue_date, maturity_date, coupon_rate, frequency, yld - bump,
        settlement_date, face_value, redemption, convention,
    )
    p0 = dirty_price_from_yield(
        issue_date, maturity_date, coupon_rate, frequency, yld,
        settlement_date, face_value, redemption, convention,
    )
    if p0 == 0:
        return 0.0
    return (p_dn - p_up) / (2.0 * p0 * bump)

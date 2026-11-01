"""Yield calculations: YTM, YTC, YTP, current yield, zero-coupon yield."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from scipy.optimize import brentq

from ..cashflows import CashFlow, accrued_interest, generate_bond_cashflows
from ..daycount import DayCount, year_fraction
from ..pricing import present_value


def _solve_yield(
    flows: List[CashFlow],
    target_dirty_price: float,
    settlement_date: date,
    frequency: int,
    convention: DayCount | str,
) -> float:
    comp = frequency if frequency and frequency > 0 else 1

    def objective(y: float) -> float:
        return present_value(flows, y, settlement_date, comp, convention) - target_dirty_price

    # Bracket the root; yields between -0.99 and +2.0 cover realistic cases.
    lo, hi = -0.9999, 2.0
    f_lo, f_hi = objective(lo), objective(hi)
    if f_lo * f_hi > 0:
        # widen the upper bracket for deeply discounted instruments
        hi = 10.0
        f_hi = objective(hi)
        if f_lo * f_hi > 0:
            raise ValueError("Unable to bracket yield; check inputs/price.")
    return brentq(objective, lo, hi, maxiter=200, xtol=1e-10)


def yield_to_maturity(
    issue_date: date,
    maturity_date: date,
    coupon_rate: float,
    frequency: int,
    clean_price: float,
    settlement_date: date,
    face_value: float = 100.0,
    redemption: Optional[float] = None,
    convention: DayCount | str = DayCount.ACT_365F,
) -> float:
    """Solve the yield that reprices the bond to the given clean price."""
    flows = generate_bond_cashflows(
        issue_date,
        maturity_date,
        coupon_rate,
        frequency,
        face_value=face_value,
        redemption=redemption,
        settlement_date=settlement_date,
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
    dirty = clean_price + ai
    return _solve_yield(flows, dirty, settlement_date, frequency, convention)


def yield_to_call(
    issue_date: date,
    call_date: date,
    coupon_rate: float,
    frequency: int,
    clean_price: float,
    settlement_date: date,
    call_price: float,
    face_value: float = 100.0,
    convention: DayCount | str = DayCount.ACT_365F,
) -> float:
    """Yield assuming the bond is redeemed at the call date/price."""
    return yield_to_maturity(
        issue_date,
        call_date,
        coupon_rate,
        frequency,
        clean_price,
        settlement_date,
        face_value=face_value,
        redemption=call_price,
        convention=convention,
    )


def yield_to_put(
    issue_date: date,
    put_date: date,
    coupon_rate: float,
    frequency: int,
    clean_price: float,
    settlement_date: date,
    put_price: float,
    face_value: float = 100.0,
    convention: DayCount | str = DayCount.ACT_365F,
) -> float:
    """Yield assuming the holder puts the bond at the put date/price."""
    return yield_to_maturity(
        issue_date,
        put_date,
        coupon_rate,
        frequency,
        clean_price,
        settlement_date,
        face_value=face_value,
        redemption=put_price,
        convention=convention,
    )


def current_yield(coupon_rate: float, clean_price: float, face_value: float = 100.0) -> float:
    """Annual coupon income divided by clean price."""
    if clean_price <= 0:
        raise ValueError("clean_price must be positive")
    return (coupon_rate * face_value) / clean_price


def zero_coupon_yield(
    settlement_date: date,
    maturity_date: date,
    price: float,
    face_value: float = 100.0,
    frequency: int = 1,
    convention: DayCount | str = DayCount.ACT_365F,
) -> float:
    """Yield of a zero-coupon instrument (e.g. T-Bill) priced below par.

    Uses periodic compounding at `frequency` (default annual).
    """
    if price <= 0:
        raise ValueError("price must be positive")
    comp = frequency if frequency and frequency > 0 else 1
    t = year_fraction(settlement_date, maturity_date, convention)
    periods = t * comp
    return comp * ((face_value / price) ** (1.0 / periods) - 1.0)

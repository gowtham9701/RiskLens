"""DV01 (dollar value of a basis point) and price-change estimation."""

from __future__ import annotations

from datetime import date

from ..daycount import DayCount
from ..pricing import dirty_price_from_yield


def dv01(
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
    """Price change (per face_value) for a 1 bp decrease in yield.

    Reported as a positive number: the gain in price for -1bp, which
    equals the magnitude of the loss for +1bp (to first order).
    """
    bump = 0.0001
    p_up = dirty_price_from_yield(
        issue_date, maturity_date, coupon_rate, frequency, yld + bump,
        settlement_date, face_value, redemption, convention,
    )
    p_dn = dirty_price_from_yield(
        issue_date, maturity_date, coupon_rate, frequency, yld - bump,
        settlement_date, face_value, redemption, convention,
    )
    return (p_dn - p_up) / 2.0


def price_change_estimate(
    modified_duration: float,
    convexity: float,
    yield_change: float,
    price: float,
) -> float:
    """First + second order price change for a yield move.

    dP ≈ (-ModDur * dy + 0.5 * Convexity * dy^2) * Price
    """
    pct = -modified_duration * yield_change + 0.5 * convexity * yield_change ** 2
    return pct * price

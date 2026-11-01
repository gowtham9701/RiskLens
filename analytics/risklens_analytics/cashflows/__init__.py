"""Coupon schedule generation, cash flows and accrued interest."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List

from ..daycount import DayCount, year_fraction


@dataclass(frozen=True)
class CashFlow:
    """A single contractual cash flow."""

    pay_date: date
    amount: float
    is_coupon: bool = True
    is_principal: bool = False

    @property
    def kind(self) -> str:
        if self.is_coupon and self.is_principal:
            return "coupon+principal"
        if self.is_principal:
            return "principal"
        return "coupon"


def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    year = d.year + m // 12
    month = m % 12 + 1
    # clamp day to end of month
    import calendar

    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last))


def generate_coupon_dates(
    issue_date: date,
    maturity_date: date,
    frequency: int,
) -> List[date]:
    """Generate coupon payment dates working backwards from maturity.

    frequency: coupons per year (1, 2, 4, 12). 0 means zero-coupon.
    Returns an ascending list of coupon dates up to and including maturity.
    """
    if frequency <= 0:
        return [maturity_date]

    months = 12 // frequency
    dates: List[date] = []
    d = maturity_date
    while d > issue_date:
        dates.append(d)
        d = _add_months(maturity_date, -months * (len(dates)))
    dates.sort()
    return dates


def generate_bond_cashflows(
    issue_date: date,
    maturity_date: date,
    coupon_rate: float,
    frequency: int,
    face_value: float = 100.0,
    redemption: float | None = None,
    settlement_date: date | None = None,
) -> List[CashFlow]:
    """Generate contractual coupon and redemption cash flows.

    coupon_rate is the annual rate as a decimal (e.g. 0.075 for 7.5%).
    Only cash flows strictly after the settlement date are returned.
    Zero-coupon bonds (frequency == 0) return a single redemption flow.
    """
    redemption = face_value if redemption is None else redemption
    ref = settlement_date or issue_date

    if frequency <= 0:
        return [CashFlow(maturity_date, redemption, is_coupon=False, is_principal=True)]

    coupon_dates = generate_coupon_dates(issue_date, maturity_date, frequency)
    coupon_amt = coupon_rate / frequency * face_value

    flows: List[CashFlow] = []
    for i, d in enumerate(coupon_dates):
        if d <= ref:
            continue
        is_last = i == len(coupon_dates) - 1
        if is_last:
            flows.append(
                CashFlow(d, coupon_amt + redemption, is_coupon=True, is_principal=True)
            )
        else:
            flows.append(CashFlow(d, coupon_amt, is_coupon=True, is_principal=False))
    return flows


def previous_and_next_coupon(
    issue_date: date,
    maturity_date: date,
    frequency: int,
    settlement_date: date,
) -> tuple[date, date]:
    """Return (previous_coupon_date, next_coupon_date) around settlement."""
    if frequency <= 0:
        return issue_date, maturity_date
    coupon_dates = generate_coupon_dates(issue_date, maturity_date, frequency)
    prev = issue_date
    nxt = maturity_date
    for d in coupon_dates:
        if d <= settlement_date:
            prev = d
        else:
            nxt = d
            break
    return prev, nxt


def accrued_interest(
    issue_date: date,
    maturity_date: date,
    coupon_rate: float,
    frequency: int,
    settlement_date: date,
    face_value: float = 100.0,
    convention: DayCount | str = DayCount.ACT_365F,
) -> float:
    """Accrued interest per face_value as of the settlement date."""
    if frequency <= 0 or coupon_rate == 0:
        return 0.0
    prev, nxt = previous_and_next_coupon(
        issue_date, maturity_date, frequency, settlement_date
    )
    full_period = year_fraction(prev, nxt, convention)
    accrued_period = year_fraction(prev, settlement_date, convention)
    coupon_amt = coupon_rate / frequency * face_value
    if full_period <= 0:
        return 0.0
    return coupon_amt * (accrued_period / full_period)

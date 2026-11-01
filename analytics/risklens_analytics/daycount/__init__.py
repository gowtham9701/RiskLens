"""Day-count conventions for fixed-income accrual and discounting.

Supports the conventions most relevant to the Indian fixed-income
market and common global instruments:

- ACT/365F  (Actual/365 Fixed)
- ACT/360
- ACT/ACT   (ISDA)
- 30/360    (US / Bond basis)
- 30E/360   (Eurobond basis)

year_fraction(start, end, convention) returns the accrual factor.
"""

from __future__ import annotations

from datetime import date
from enum import Enum


class DayCount(str, Enum):
    ACT_365F = "ACT/365F"
    ACT_360 = "ACT/360"
    ACT_ACT = "ACT/ACT"
    THIRTY_360 = "30/360"
    THIRTY_E_360 = "30E/360"


def _days_act(start: date, end: date) -> int:
    return (end - start).days


def _is_leap(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def _thirty_360(start: date, end: date, european: bool) -> float:
    d1, d2 = start.day, end.day
    m1, m2 = start.month, end.month
    y1, y2 = start.year, end.year

    if european:
        if d1 == 31:
            d1 = 30
        if d2 == 31:
            d2 = 30
    else:  # US 30/360 (bond basis)
        if d1 == 31:
            d1 = 30
        if d2 == 31 and d1 == 30:
            d2 = 30

    return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)) / 360.0


def _act_act_isda(start: date, end: date) -> float:
    if start == end:
        return 0.0
    if start > end:
        return -_act_act_isda(end, start)

    if start.year == end.year:
        denom = 366.0 if _is_leap(start.year) else 365.0
        return _days_act(start, end) / denom

    total = 0.0
    # stub in start year
    start_year_end = date(start.year + 1, 1, 1)
    denom_start = 366.0 if _is_leap(start.year) else 365.0
    total += _days_act(start, start_year_end) / denom_start
    # whole years in between
    total += end.year - start.year - 1
    # stub in end year
    end_year_start = date(end.year, 1, 1)
    denom_end = 366.0 if _is_leap(end.year) else 365.0
    total += _days_act(end_year_start, end) / denom_end
    return total


def year_fraction(start: date, end: date, convention: DayCount | str = DayCount.ACT_365F) -> float:
    """Return the accrual year fraction between two dates."""
    conv = DayCount(convention) if not isinstance(convention, DayCount) else convention

    if conv is DayCount.ACT_365F:
        return _days_act(start, end) / 365.0
    if conv is DayCount.ACT_360:
        return _days_act(start, end) / 360.0
    if conv is DayCount.ACT_ACT:
        return _act_act_isda(start, end)
    if conv is DayCount.THIRTY_360:
        return _thirty_360(start, end, european=False)
    if conv is DayCount.THIRTY_E_360:
        return _thirty_360(start, end, european=True)
    raise ValueError(f"Unsupported day-count convention: {convention}")

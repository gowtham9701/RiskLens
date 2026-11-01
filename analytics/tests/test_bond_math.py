"""Financial-correctness tests for the RiskLens analytics engine.

Benchmarks use the 30/360 convention so coupon periods are exactly equal,
allowing comparison against closed-form textbook values.
"""

from datetime import date

import pytest

from risklens_analytics import (
    accrued_interest,
    convexity,
    current_yield,
    dv01,
    generate_bond_cashflows,
    macaulay_duration,
    modified_duration,
    price_from_yield,
    dirty_price_from_yield,
    yield_to_maturity,
    yield_to_call,
    zero_coupon_yield,
)
from risklens_analytics.daycount import DayCount, year_fraction

T360 = DayCount.THIRTY_360


# --------------------------------------------------------------------------
# Day count
# --------------------------------------------------------------------------
def test_30360_full_year():
    assert year_fraction(date(2020, 1, 1), date(2021, 1, 1), T360) == pytest.approx(1.0)


def test_act365_half_year():
    yf = year_fraction(date(2021, 1, 1), date(2021, 7, 2), DayCount.ACT_365F)
    assert yf == pytest.approx(182 / 365, rel=1e-9)


# --------------------------------------------------------------------------
# Cash flows
# --------------------------------------------------------------------------
def test_cashflow_count_and_final():
    flows = generate_bond_cashflows(
        date(2020, 1, 1), date(2025, 1, 1), 0.08, 2, face_value=100,
        settlement_date=date(2020, 1, 1),
    )
    # 5 years * 2 = 10 coupons
    assert len(flows) == 10
    # last flow carries principal + coupon
    assert flows[-1].is_principal
    assert flows[-1].amount == pytest.approx(4.0 + 100.0)
    # intermediate coupons are 8%/2 * 100 = 4
    assert flows[0].amount == pytest.approx(4.0)


def test_zero_coupon_single_flow():
    flows = generate_bond_cashflows(
        date(2020, 1, 1), date(2025, 1, 1), 0.0, 0, face_value=100,
        settlement_date=date(2020, 1, 1),
    )
    assert len(flows) == 1
    assert flows[0].amount == pytest.approx(100.0)


# --------------------------------------------------------------------------
# Pricing: par / premium / discount
# --------------------------------------------------------------------------
def test_par_bond_prices_at_100():
    price = price_from_yield(
        date(2020, 1, 1), date(2030, 1, 1), 0.05, 1, 0.05,
        date(2020, 1, 1), face_value=100, convention=T360,
    )
    assert price == pytest.approx(100.0, abs=1e-6)


def test_premium_when_yield_below_coupon():
    price = price_from_yield(
        date(2020, 1, 1), date(2030, 1, 1), 0.08, 1, 0.05,
        date(2020, 1, 1), face_value=100, convention=T360,
    )
    assert price > 100.0


def test_discount_when_yield_above_coupon():
    price = price_from_yield(
        date(2020, 1, 1), date(2030, 1, 1), 0.03, 1, 0.05,
        date(2020, 1, 1), face_value=100, convention=T360,
    )
    assert price < 100.0


def test_price_yield_inverse():
    p_low = dirty_price_from_yield(
        date(2020, 1, 1), date(2030, 1, 1), 0.05, 2, 0.04,
        date(2020, 1, 1), convention=T360,
    )
    p_high = dirty_price_from_yield(
        date(2020, 1, 1), date(2030, 1, 1), 0.05, 2, 0.06,
        date(2020, 1, 1), convention=T360,
    )
    assert p_low > p_high


# --------------------------------------------------------------------------
# Yield round-trips
# --------------------------------------------------------------------------
def test_ytm_round_trip():
    price = price_from_yield(
        date(2020, 1, 1), date(2030, 1, 1), 0.07, 2, 0.065,
        date(2020, 1, 1), convention=T360,
    )
    y = yield_to_maturity(
        date(2020, 1, 1), date(2030, 1, 1), 0.07, 2, price,
        date(2020, 1, 1), convention=T360,
    )
    assert y == pytest.approx(0.065, abs=1e-6)


def test_par_bond_ytm_equals_coupon():
    y = yield_to_maturity(
        date(2020, 1, 1), date(2030, 1, 1), 0.06, 2, 100.0,
        date(2020, 1, 1), convention=T360,
    )
    assert y == pytest.approx(0.06, abs=1e-6)


def test_zero_coupon_yield_closed_form():
    # price 60, face 100, 5 years annual compounding
    y = zero_coupon_yield(
        date(2020, 1, 1), date(2025, 1, 1), 60.0, face_value=100,
        frequency=1, convention=T360,
    )
    expected = (100 / 60) ** (1 / 5) - 1
    assert y == pytest.approx(expected, rel=1e-9)


def test_current_yield():
    assert current_yield(0.08, 80.0, 100.0) == pytest.approx(0.10)


def test_ytc_shorter_horizon_changes_yield():
    # callable at 102 in 3 years vs maturity in 10
    price = 98.0
    ytm = yield_to_maturity(
        date(2020, 1, 1), date(2030, 1, 1), 0.06, 2, price,
        date(2020, 1, 1), convention=T360,
    )
    ytc = yield_to_call(
        date(2020, 1, 1), date(2023, 1, 1), 0.06, 2, price,
        date(2020, 1, 1), call_price=102.0, convention=T360,
    )
    assert ytm != pytest.approx(ytc)


# --------------------------------------------------------------------------
# Accrued interest
# --------------------------------------------------------------------------
def test_accrued_zero_on_coupon_date():
    ai = accrued_interest(
        date(2020, 1, 1), date(2025, 1, 1), 0.08, 2, date(2020, 1, 1),
        face_value=100, convention=T360,
    )
    assert ai == pytest.approx(0.0)


def test_accrued_half_period():
    # semi-annual 8% bond, settle 3 months after issue -> ~half of 4.0 coupon
    ai = accrued_interest(
        date(2020, 1, 1), date(2025, 1, 1), 0.08, 2, date(2020, 4, 1),
        face_value=100, convention=T360,
    )
    assert ai == pytest.approx(2.0, abs=0.05)


# --------------------------------------------------------------------------
# Duration / convexity / DV01
# --------------------------------------------------------------------------
def test_zero_coupon_duration_equals_maturity():
    flows = generate_bond_cashflows(
        date(2020, 1, 1), date(2025, 1, 1), 0.0, 0, face_value=100,
        settlement_date=date(2020, 1, 1),
    )
    mac = macaulay_duration(flows, 0.05, date(2020, 1, 1), frequency=1, convention=T360)
    assert mac == pytest.approx(5.0, abs=1e-6)


def test_modified_less_than_macaulay():
    flows = generate_bond_cashflows(
        date(2020, 1, 1), date(2030, 1, 1), 0.06, 2, face_value=100,
        settlement_date=date(2020, 1, 1),
    )
    mac = macaulay_duration(flows, 0.06, date(2020, 1, 1), frequency=2, convention=T360)
    mod = modified_duration(flows, 0.06, date(2020, 1, 1), frequency=2, convention=T360)
    assert mod < mac
    assert mod == pytest.approx(mac / (1 + 0.06 / 2), rel=1e-9)


def test_convexity_positive():
    flows = generate_bond_cashflows(
        date(2020, 1, 1), date(2030, 1, 1), 0.06, 2, face_value=100,
        settlement_date=date(2020, 1, 1),
    )
    c = convexity(flows, 0.06, date(2020, 1, 1), frequency=2, convention=T360)
    assert c > 0


def test_dv01_matches_duration_identity():
    issue, mat, settle = date(2020, 1, 1), date(2030, 1, 1), date(2020, 1, 1)
    flows = generate_bond_cashflows(issue, mat, 0.06, 2, face_value=100, settlement_date=settle)
    price = dirty_price_from_yield(issue, mat, 0.06, 2, 0.06, settle, convention=T360)
    mod = modified_duration(flows, 0.06, settle, frequency=2, convention=T360)
    d = dv01(issue, mat, 0.06, 2, 0.06, settle, convention=T360)
    # DV01 ≈ ModDur * Price * 1bp
    assert d == pytest.approx(mod * price * 0.0001, rel=1e-3)

"""Tests for portfolio aggregation, liquidity scoring and optimisation."""

from datetime import date

import pytest

from risklens_analytics import (
    xirr,
    portfolio_ytm,
    weighted_duration,
    portfolio_dv01,
    liquidity_score,
    estimated_liquidation_days,
    run_stress_test,
)
from risklens_analytics.cashflows import CashFlow
from risklens_analytics.portfolio.core import Position
from risklens_analytics.liquidity.core import LiquidityInputs
from risklens_analytics.optimisation.optimizer import (
    Candidate,
    Constraints,
    Objective,
    optimise_portfolio,
)
from risklens_analytics.stress_testing.scenarios import StressPosition


# --------------------------------------------------------------------------
# XIRR / portfolio YTM
# --------------------------------------------------------------------------
def test_xirr_simple_doubling():
    # invest 100, receive 110 one (non-leap) year later -> 10%
    r = xirr([(date(2021, 1, 1), -100.0), (date(2022, 1, 1), 110.0)])
    assert r == pytest.approx(0.10, abs=1e-4)


def test_portfolio_ytm_not_naive_average():
    # Two positions with different cash-flow timing; portfolio YTM is the IRR
    # of combined flows, not a simple mean of individual yields.
    as_of = date(2020, 1, 1)
    pos1 = Position(
        "A", market_value=100.0,
        cashflows=[CashFlow(date(2021, 1, 1), 108.0)],
    )
    pos2 = Position(
        "B", market_value=100.0,
        cashflows=[CashFlow(date(2022, 1, 1), 121.0)],
    )
    y = portfolio_ytm([pos1, pos2], as_of)
    assert y is not None
    # individual yields are 8% and ~10%; IRR of combined is between, solved
    assert 0.08 < y < 0.11


def test_weighted_duration_and_dv01():
    pos1 = Position("A", 300.0, [], modified_duration=2.0, dv01=0.06)
    pos2 = Position("B", 100.0, [], modified_duration=6.0, dv01=0.06)
    assert weighted_duration([pos1, pos2]) == pytest.approx((2 * 300 + 6 * 100) / 400)
    assert portfolio_dv01([pos1, pos2]) == pytest.approx(0.12)


# --------------------------------------------------------------------------
# Liquidity
# --------------------------------------------------------------------------
def test_liquidity_score_high():
    s = liquidity_score(LiquidityInputs(
        avg_daily_traded_value=60_000_000,
        trading_days=20, window_days=22,
        bid_ask_spread_bps=5,
        market_depth_value=12_000_000,
        last_traded_date=date(2024, 1, 10),
        as_of_date=date(2024, 1, 11),
    ))
    assert s.score is not None
    assert s.score >= 75
    assert s.classification == "High liquidity"


def test_liquidity_insufficient_data():
    s = liquidity_score(LiquidityInputs(avg_daily_traded_value=1_000_000))
    assert s.score is None
    assert s.classification == "Insufficient data"


def test_estimated_liquidation_days():
    d = estimated_liquidation_days(10_000_000, 5_000_000, participation_rate=0.10)
    assert d == pytest.approx(20.0)
    assert estimated_liquidation_days(1000, None) is None


# --------------------------------------------------------------------------
# Optimiser
# --------------------------------------------------------------------------
def _candidates():
    return [
        Candidate("GS1", "GOI", "Sovereign", "G-Sec", 0.071, 0.070, 6.5, 8, 90, 1, True),
        Candidate("GS2", "GOI", "Sovereign", "T-Bill", 0.068, 0.0, 0.5, 0.5, 95, 1, True),
        Candidate("NCD1", "ISSX", "Financials", "NCD", 0.092, 0.090, 3.2, 4, 60, 2, False),
        Candidate("NCD2", "ISSY", "Infrastructure", "NCD", 0.105, 0.100, 2.8, 5, 40, 5, False),
        Candidate("FD1", "BANKZ", "Banking", "FD", 0.075, 0.075, 1.8, 2, 55, 2, False),
    ]


def test_optimise_weights_sum_to_one_and_respect_caps():
    res = optimise_portfolio(
        _candidates(),
        Constraints(max_issuer_weight=0.40, max_sector_weight=0.60, max_weight_per_instrument=0.40),
        Objective.MAX_YIELD,
    )
    assert res.feasible
    assert sum(res.weights.values()) == pytest.approx(1.0, abs=1e-6)
    for w in res.weights.values():
        assert w <= 0.40 + 1e-6


def test_optimise_min_government_respected():
    res = optimise_portfolio(
        _candidates(),
        Constraints(min_government_weight=0.50, max_issuer_weight=0.60, max_sector_weight=0.60, max_weight_per_instrument=0.50),
        Objective.MAX_YIELD,
    )
    assert res.feasible
    gov = sum(res.weights.get(i, 0.0) for i in ("GS1", "GS2"))
    assert gov >= 0.50 - 1e-4


def test_optimise_infeasible_reports_reason():
    # per-instrument cap too small to reach 100% across 5 instruments
    res = optimise_portfolio(
        _candidates(),
        Constraints(max_weight_per_instrument=0.10),
        Objective.MAX_YIELD,
    )
    assert not res.feasible
    assert res.infeasible_reasons


def test_optimise_max_yield_prefers_higher_yield():
    res = optimise_portfolio(
        _candidates(),
        Constraints(max_issuer_weight=1.0, max_sector_weight=1.0, max_weight_per_instrument=1.0),
        Objective.MAX_YIELD,
    )
    assert res.feasible
    # highest-yield instrument should dominate
    assert res.weights.get("NCD2", 0) >= 0.9


# --------------------------------------------------------------------------
# Stress testing
# --------------------------------------------------------------------------
def test_stress_rate_up_is_loss():
    positions = [
        StressPosition("A", 1_000_000, modified_duration=5.0, convexity=30.0, is_corporate=True, issuer_id="X"),
    ]
    results = run_stress_test(positions, downgrade_issuer="X", default_issuer="X")
    by_name = {r.name: r for r in results}
    assert by_name["Rates +100bps"].pnl < 0
    assert by_name["Rates -100bps"].pnl > 0
    assert by_name["Default: X"].pnl < 0
    # default loss larger than downgrade haircut
    assert by_name["Default: X"].pnl < by_name["Downgrade: X"].pnl

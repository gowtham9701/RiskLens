"""Bridges stored instrument records to the RiskLens analytics engine."""

from __future__ import annotations

from datetime import date
from typing import Any

from risklens_analytics import (
    accrued_interest,
    convexity as _convexity,
    current_yield as _current_yield,
    dirty_price_from_yield,
    dv01 as _dv01,
    estimated_liquidation_days,
    generate_bond_cashflows,
    liquidity_score,
    macaulay_duration,
    modified_duration,
    yield_to_call,
    yield_to_maturity,
    zero_coupon_yield,
)
from risklens_analytics.credit_risk import grade_bucket, rating_rank
from risklens_analytics.liquidity.core import LiquidityInputs, indicative_liquidation_cost

VALUATION_DATE = date(2025, 1, 15)
BOND_CATEGORIES = {"G-Sec", "SDL", "NCD"}


def _parse(d) -> date | None:
    if d is None:
        return None
    if isinstance(d, date):
        return d
    return date.fromisoformat(str(d))


def compute_instrument_analytics(
    *,
    category: str,
    clean_price: float | None,
    face_value: float | None,
    coupon_rate: float | None,
    coupon_frequency: int | None,
    issue_date,
    maturity_date,
    day_count: str | None,
    callable: bool = False,
    call_date=None,
    call_price=None,
    indicative_ytm: float | None = None,
    indicative_duration: float | None = None,
    as_of: date = VALUATION_DATE,
) -> dict[str, Any]:
    """Return ytm, duration, convexity, dv01, accrued, dirty_price, etc.

    Instrument-specific methodology: bond math only for tradable bonds;
    T-Bills use zero-coupon yield; FDs use their deposit rate; mutual
    funds use indicative fund-level figures (never bond YTM formulas).
    """
    issue = _parse(issue_date)
    mat = _parse(maturity_date)
    conv = day_count or "ACT/365F"
    out: dict[str, Any] = {
        "ytm": None, "ytc": None, "current_yield": None,
        "macaulay_duration": None, "modified_duration": None,
        "convexity": None, "dv01": None, "accrued_interest": None,
        "dirty_price": None, "methodology": None,
    }

    if category == "FD":
        out["ytm"] = float(coupon_rate) if coupon_rate is not None else None
        out["current_yield"] = out["ytm"]
        if mat:
            yrs = max((mat - as_of).days / 365.0, 0.0)
            out["modified_duration"] = round(yrs / (1 + (coupon_rate or 0)), 4)
            out["macaulay_duration"] = round(yrs, 4)
        out["methodology"] = "Fixed deposit: yield = contracted deposit rate; not exchange-traded."
        return out

    if category == "Debt MF":
        out["ytm"] = float(indicative_ytm) if indicative_ytm is not None else None
        out["modified_duration"] = float(indicative_duration) if indicative_duration is not None else None
        out["methodology"] = "Open-ended debt fund: indicative portfolio YTM/duration (fund-level, simulated)."
        return out

    if clean_price is None or face_value is None or mat is None:
        return out

    if category == "T-Bill" or (coupon_frequency in (0, None) and (coupon_rate in (0, None))):
        y = zero_coupon_yield(as_of, mat, float(clean_price), face_value=float(face_value),
                              frequency=1, convention=conv)
        yrs = (mat - as_of).days / 365.0
        out["ytm"] = round(y, 6)
        out["modified_duration"] = round(yrs / (1 + y), 4)
        out["macaulay_duration"] = round(yrs, 4)
        out["dirty_price"] = float(clean_price)
        out["accrued_interest"] = 0.0
        out["methodology"] = "Zero-coupon discount yield (ACT/365F)."
        return out

    # Coupon-bearing bond
    freq = coupon_frequency or 2
    cpn = float(coupon_rate or 0)
    fv = float(face_value)
    cp = float(clean_price)
    try:
        y = yield_to_maturity(issue, mat, cpn, freq, cp, as_of, face_value=fv, convention=conv)
    except Exception:
        return out
    flows = generate_bond_cashflows(issue, mat, cpn, freq, face_value=fv, settlement_date=as_of)
    ai = accrued_interest(issue, mat, cpn, freq, as_of, face_value=fv, convention=conv)
    out["ytm"] = round(y, 6)
    out["current_yield"] = round(_current_yield(cpn, cp, fv), 6)
    out["macaulay_duration"] = round(macaulay_duration(flows, y, as_of, freq, conv), 4)
    out["modified_duration"] = round(modified_duration(flows, y, as_of, freq, conv), 4)
    out["convexity"] = round(_convexity(flows, y, as_of, freq, conv), 4)
    out["dv01"] = round(_dv01(issue, mat, cpn, freq, y, as_of, face_value=fv, convention=conv), 6)
    out["accrued_interest"] = round(ai, 4)
    out["dirty_price"] = round(cp + ai, 4)
    out["methodology"] = f"Coupon bond priced on {conv}, {freq}x/yr compounding."
    if callable and call_date and call_price:
        try:
            out["ytc"] = round(
                yield_to_call(issue, _parse(call_date), cpn, freq, cp, as_of,
                              call_price=float(call_price), face_value=fv, convention=conv),
                6,
            )
        except Exception:
            out["ytc"] = None
    return out


def compute_liquidity(metric, holding_mv: float | None = None) -> dict[str, Any]:
    """Compute liquidity score + liquidation estimates from a metric row."""
    if metric is None:
        return {"score": None, "classification": "Insufficient data", "components": {},
                "missing": ["all"], "est_liquidation_days": None, "est_cost": None,
                "data_status": "SIMULATED"}
    inp = LiquidityInputs(
        avg_daily_traded_value=_f(metric.avg_daily_traded_value),
        trading_days=metric.trading_days,
        window_days=metric.window_days,
        bid_ask_spread_bps=_f(metric.bid_ask_spread_bps),
        market_depth_value=_f(metric.market_depth_value),
        last_traded_date=_parse(metric.last_traded_date),
        as_of_date=_parse(metric.as_of_date),
    )
    s = liquidity_score(inp)
    days = None
    cost = None
    if holding_mv is not None:
        days = estimated_liquidation_days(holding_mv, inp.avg_daily_traded_value)
        cost = indicative_liquidation_cost(holding_mv, inp.bid_ask_spread_bps)
    return {
        "score": s.score, "classification": s.classification,
        "components": s.components, "missing": s.missing,
        "methodology": s.methodology,
        "est_liquidation_days": round(days, 2) if days is not None else None,
        "est_cost": round(cost, 2) if cost is not None else None,
        "data_status": "SIMULATED",
    }


def rating_info(symbol: str | None) -> dict[str, Any]:
    return {"rank": rating_rank(symbol), "bucket": grade_bucket(symbol)}


def _f(x):
    return float(x) if x is not None else None

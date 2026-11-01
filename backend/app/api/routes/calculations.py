"""Stateless financial calculation routes."""

from __future__ import annotations

from fastapi import APIRouter

from risklens_analytics import (
    current_yield,
    dirty_price_from_yield,
    generate_bond_cashflows,
    accrued_interest,
    convexity,
    dv01,
    macaulay_duration,
    modified_duration,
    price_from_yield,
    yield_to_maturity,
)
from risklens_analytics.stress_testing.scenarios import StressPosition, run_stress_test

from ...schemas import BondPriceIn, YieldIn

router = APIRouter(prefix="/calculations", tags=["calculations"])


@router.post("/bond-price")
def bond_price(body: BondPriceIn):
    clean = price_from_yield(body.issue_date, body.maturity_date, body.coupon_rate,
                             body.frequency, body.yield_, body.settlement_date,
                             face_value=body.face_value, convention=body.day_count)
    dirty = dirty_price_from_yield(body.issue_date, body.maturity_date, body.coupon_rate,
                                   body.frequency, body.yield_, body.settlement_date,
                                   face_value=body.face_value, convention=body.day_count)
    ai = accrued_interest(body.issue_date, body.maturity_date, body.coupon_rate,
                          body.frequency, body.settlement_date, face_value=body.face_value,
                          convention=body.day_count)
    return {"clean_price": round(clean, 6), "dirty_price": round(dirty, 6),
            "accrued_interest": round(ai, 6)}


@router.post("/yield")
def yield_calc(body: YieldIn):
    y = yield_to_maturity(body.issue_date, body.maturity_date, body.coupon_rate,
                          body.frequency, body.clean_price, body.settlement_date,
                          face_value=body.face_value, convention=body.day_count)
    return {"ytm": round(y, 6),
            "current_yield": round(current_yield(body.coupon_rate, body.clean_price, body.face_value), 6)}


@router.post("/duration")
def duration_calc(body: YieldIn):
    y = yield_to_maturity(body.issue_date, body.maturity_date, body.coupon_rate,
                          body.frequency, body.clean_price, body.settlement_date,
                          face_value=body.face_value, convention=body.day_count)
    flows = generate_bond_cashflows(body.issue_date, body.maturity_date, body.coupon_rate,
                                    body.frequency, face_value=body.face_value,
                                    settlement_date=body.settlement_date)
    return {
        "ytm": round(y, 6),
        "macaulay": round(macaulay_duration(flows, y, body.settlement_date, body.frequency, body.day_count), 4),
        "modified": round(modified_duration(flows, y, body.settlement_date, body.frequency, body.day_count), 4),
        "convexity": round(convexity(flows, y, body.settlement_date, body.frequency, body.day_count), 4),
        "dv01": round(dv01(body.issue_date, body.maturity_date, body.coupon_rate, body.frequency,
                           y, body.settlement_date, face_value=body.face_value, convention=body.day_count), 6),
    }


@router.post("/stress-test")
def stress(body: dict):
    positions = [
        StressPosition(
            p.get("instrument_id", "X"), float(p["market_value"]),
            float(p.get("modified_duration", 0)), float(p.get("convexity", 0)),
            p.get("issuer_id", ""), is_corporate=bool(p.get("is_corporate", True)),
        )
        for p in body.get("positions", [])
    ]
    results = run_stress_test(positions,
                              downgrade_issuer=body.get("downgrade_issuer"),
                              default_issuer=body.get("default_issuer"))
    return {"scenarios": [{"name": r.name, "description": r.description, "pnl": round(r.pnl, 2),
                           "pnl_pct": round(r.pnl_pct, 4), "disclaimer": r.disclaimer}
                          for r in results]}

"""Portfolio Builder service: eligibility filtering + SciPy optimisation."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from risklens_analytics.credit_risk import rating_rank
from risklens_analytics.optimisation.optimizer import (
    Candidate,
    Constraints,
    Objective,
    optimise_portfolio,
)

from ..models import CreditRating, Instrument, LiquidityMetric, MarketPrice
from .analytics_service import VALUATION_DATE, compute_instrument_analytics, compute_liquidity


def _latest_price(db: Session, instrument_id: str):
    row = db.execute(
        select(MarketPrice).where(MarketPrice.instrument_id == instrument_id)
        .order_by(MarketPrice.price_date.desc())
    ).scalars().first()
    return float(row.clean_price) if row else None


def _build_candidate(db: Session, instr: Instrument, as_of: date) -> Candidate | None:
    terms = instr.terms
    price = _latest_price(db, instr.id)
    a = compute_instrument_analytics(
        category=instr.category,
        clean_price=price if terms else None,
        face_value=float(terms.face_value) if terms and terms.face_value else None,
        coupon_rate=float(terms.coupon_rate) if terms and terms.coupon_rate is not None else None,
        coupon_frequency=terms.coupon_frequency if terms else None,
        issue_date=terms.issue_date if terms else None,
        maturity_date=terms.maturity_date if terms else None,
        day_count=terms.day_count if terms else None,
        indicative_ytm=float(terms.indicative_ytm) if terms and terms.indicative_ytm else None,
        indicative_duration=float(terms.indicative_duration) if terms and terms.indicative_duration else None,
        as_of=as_of,
    )
    if a.get("ytm") is None:
        return None
    rating = db.execute(
        select(CreditRating).where(CreditRating.instrument_id == instr.id)
    ).scalars().first() or db.execute(
        select(CreditRating).where(CreditRating.issuer_id == instr.issuer_id)
    ).scalars().first()
    rank = rating_rank(rating.symbol) if rating else 11
    metric = db.execute(
        select(LiquidityMetric).where(LiquidityMetric.instrument_id == instr.id)
    ).scalars().first()
    liq = compute_liquidity(metric)
    mat = terms.maturity_date if terms and terms.maturity_date else None
    if mat:
        mat_years = max((date.fromisoformat(str(mat)) - as_of).days / 365.0, 0.0)
    else:
        mat_years = float(terms.indicative_duration) if terms and terms.indicative_duration else 1.0
    return Candidate(
        instrument_id=instr.id,
        issuer_id=instr.issuer_id,
        sector=instr.sector or "Other",
        category=instr.category,
        ytm=float(a["ytm"]),
        coupon_rate=float(terms.coupon_rate) if terms and terms.coupon_rate else 0.0,
        modified_duration=float(a.get("modified_duration") or 0.0),
        maturity_years=mat_years,
        liquidity_score=liq["score"],
        rating_rank=rank or 11,
        is_government=instr.is_government,
    )


def generate(db: Session, *, amount: float, objective: str, constraints: dict,
             universe: list[str] | None, as_of: date = VALUATION_DATE) -> dict[str, Any]:
    q = select(Instrument)
    if universe:
        q = q.where(Instrument.category.in_(universe))
    instruments = db.execute(q).scalars().all()

    candidates: list[Candidate] = []
    meta: dict[str, Candidate] = {}
    cand_meta: dict[str, Instrument] = {}
    for instr in instruments:
        c = _build_candidate(db, instr, as_of)
        if c:
            candidates.append(c)
            cand_meta[c.instrument_id] = instr

    con = Constraints(
        max_issuer_weight=constraints.get("max_issuer_weight", 0.25),
        max_sector_weight=constraints.get("max_sector_weight", 0.40),
        min_government_weight=constraints.get("min_government_weight", 0.0),
        max_low_rated_weight=constraints.get("max_low_rated_weight", 1.0),
        min_liquidity_weight=constraints.get("min_liquidity_weight", 0.0),
        liquidity_floor=constraints.get("liquidity_floor", 50.0),
        max_duration=constraints.get("max_duration"),
        max_maturity_years=constraints.get("max_maturity_years"),
        max_weight_per_instrument=constraints.get("max_weight_per_instrument", 0.35),
        min_instruments=constraints.get("min_instruments", 1),
    )
    res = optimise_portfolio(candidates, con, Objective(objective),
                             target_yield=constraints.get("target_yield"))

    allocations = []
    if res.feasible:
        for iid, w in sorted(res.weights.items(), key=lambda x: -x[1]):
            instr = cand_meta[iid]
            c = next(cc for cc in candidates if cc.instrument_id == iid)
            rating = db.execute(
                select(CreditRating).where(CreditRating.instrument_id == iid)
            ).scalars().first() or db.execute(
                select(CreditRating).where(CreditRating.issuer_id == instr.issuer_id)
            ).scalars().first()
            allocations.append({
                "instrument_id": iid,
                "name": instr.name,
                "issuer": instr.issuer.name if instr.issuer else instr.issuer_id,
                "category": instr.category,
                "sector": instr.sector,
                "weight": round(w, 4),
                "amount": round(w * amount, 2),
                "ytm": round(c.ytm, 6),
                "modified_duration": round(c.modified_duration, 4),
                "rating": rating.symbol if rating else None,
                "liquidity_score": c.liquidity_score,
                "rationale": _rationale(c, objective),
            })

    return {
        "feasible": res.feasible,
        "objective": res.objective,
        "amount": amount,
        "expected_yield": round(res.expected_yield, 6),
        "expected_duration": round(res.expected_duration, 4),
        "allocations": allocations,
        "infeasible_reasons": res.infeasible_reasons,
        "message": res.message,
        "methodology": (
            "SciPy SLSQP constrained optimisation over eligible simulated "
            "instruments. Objective and constraints applied as hard limits; "
            "safety/eligibility constraints are never silently relaxed. "
            "Yields are indicative, not guaranteed realised returns."
        ),
        "data_status": "SIMULATED",
    }


def _rationale(c: Candidate, objective: str) -> str:
    bits = []
    if c.is_government:
        bits.append("government-backed")
    bits.append(f"YTM {c.ytm:.2%}")
    bits.append(f"duration {c.modified_duration:.1f}y")
    if c.liquidity_score is not None:
        bits.append(f"liquidity {c.liquidity_score:.0f}/100")
    return ", ".join(bits)

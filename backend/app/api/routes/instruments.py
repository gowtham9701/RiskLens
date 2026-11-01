"""Instrument discovery and detail routes."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...models import (
    CreditRating,
    Instrument,
    InstrumentNewsMapping,
    LiquidityMetric,
    MarketPrice,
    NewsArticle,
    RatingHistory,
)
from ...services.analytics_service import (
    VALUATION_DATE,
    compute_instrument_analytics,
    compute_liquidity,
)
from ...services.portfolio_service import _holding_cashflows

router = APIRouter(prefix="/instruments", tags=["instruments"])


def _current_rating(db, instr):
    return db.execute(
        select(CreditRating).where(CreditRating.instrument_id == instr.id)
    ).scalars().first() or db.execute(
        select(CreditRating).where(CreditRating.issuer_id == instr.issuer_id)
    ).scalars().first()


def _latest_price(db, instrument_id):
    row = db.execute(
        select(MarketPrice).where(MarketPrice.instrument_id == instrument_id)
        .order_by(MarketPrice.price_date.desc())
    ).scalars().first()
    return float(row.clean_price) if row else None


def _summary(db, instr, analytics=None):
    terms = instr.terms
    price = _latest_price(db, instr.id)
    if analytics is None:
        analytics = _analytics(db, instr, price)
    rating = _current_rating(db, instr)
    metric = db.execute(
        select(LiquidityMetric).where(LiquidityMetric.instrument_id == instr.id)
    ).scalars().first()
    liq = compute_liquidity(metric)
    display_price = price
    if display_price is None and terms is not None:
        if instr.category == "Debt MF" and terms.nav:
            display_price = float(terms.nav)
        elif instr.category == "FD" and terms.face_value:
            display_price = float(terms.face_value)
    return {
        "id": instr.id,
        "isin": instr.isin,
        "name": instr.name,
        "category": instr.category,
        "issuer_name": instr.issuer.name if instr.issuer else instr.issuer_id,
        "sector": instr.sector,
        "coupon_rate": float(terms.coupon_rate) if terms and terms.coupon_rate is not None else None,
        "maturity_date": terms.maturity_date if terms else None,
        "clean_price": display_price,
        "ytm": analytics.get("ytm"),
        "modified_duration": analytics.get("modified_duration"),
        "rating": rating.symbol if rating else None,
        "rating_agency": rating.agency if rating else None,
        "liquidity_score": liq["score"],
        "liquidity_class": liq["classification"],
        "is_government": instr.is_government,
        "data_status": instr.data_status,
    }


def _analytics(db, instr, price):
    terms = instr.terms
    return compute_instrument_analytics(
        category=instr.category,
        clean_price=price if terms else None,
        face_value=float(terms.face_value) if terms and terms.face_value else None,
        coupon_rate=float(terms.coupon_rate) if terms and terms.coupon_rate is not None else None,
        coupon_frequency=terms.coupon_frequency if terms else None,
        issue_date=terms.issue_date if terms else None,
        maturity_date=terms.maturity_date if terms else None,
        day_count=terms.day_count if terms else None,
        callable=terms.callable if terms else False,
        call_date=terms.call_date if terms else None,
        call_price=float(terms.call_price) if terms and terms.call_price else None,
        indicative_ytm=float(terms.indicative_ytm) if terms and terms.indicative_ytm else None,
        indicative_duration=float(terms.indicative_duration) if terms and terms.indicative_duration else None,
    )


@router.get("")
def list_instruments(
    category: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = select(Instrument)
    if category:
        q = q.where(Instrument.category == category)
    if search:
        like = f"%{search.lower()}%"
        q = q.where(or_(func.lower(Instrument.name).like(like),
                        func.lower(Instrument.id).like(like)))
    total = db.execute(select(func.count()).select_from(q.subquery())).scalar() or 0
    rows = db.execute(q.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return {
        "items": [_summary(db, i) for i in rows],
        "total": total, "page": page, "page_size": page_size,
    }


@router.get("/{instrument_id}")
def get_instrument(instrument_id: str, db: Session = Depends(get_db)):
    instr = db.get(Instrument, instrument_id)
    if not instr:
        raise HTTPException(404, "Instrument not found")
    price = _latest_price(db, instr.id)
    a = _analytics(db, instr, price)
    summary = _summary(db, instr, a)
    terms = instr.terms
    summary.update({
        "issue_date": terms.issue_date if terms else None,
        "face_value": float(terms.face_value) if terms and terms.face_value else None,
        "coupon_frequency": terms.coupon_frequency if terms else None,
        "day_count": terms.day_count if terms else None,
        "callable": terms.callable if terms else False,
        "puttable": terms.puttable if terms else False,
        "secured": terms.secured if terms else False,
        "seniority": terms.seniority if terms else None,
        "accrued_interest": a.get("accrued_interest"),
        "dirty_price": a.get("dirty_price"),
        "current_yield": a.get("current_yield"),
        "ytc": a.get("ytc"),
        "convexity": a.get("convexity"),
        "dv01": a.get("dv01"),
        "analytics": a,
    })
    return summary


@router.get("/{instrument_id}/cashflows")
def instrument_cashflows(instrument_id: str, db: Session = Depends(get_db)):
    instr = db.get(Instrument, instrument_id)
    if not instr:
        raise HTTPException(404, "Instrument not found")
    flows = _holding_cashflows(instr, instr.terms, 1.0, 0.0, VALUATION_DATE)
    return {"items": [{"pay_date": f.pay_date.isoformat(), "amount": round(f.amount, 4),
                       "kind": f.kind} for f in flows], "data_status": "SIMULATED"}


@router.get("/{instrument_id}/prices")
def instrument_prices(instrument_id: str, db: Session = Depends(get_db)):
    rows = db.execute(
        select(MarketPrice).where(MarketPrice.instrument_id == instrument_id)
        .order_by(MarketPrice.price_date)
    ).scalars().all()
    return {"items": [{"price_date": r.price_date.isoformat(), "clean_price": float(r.clean_price),
                       "source": r.source} for r in rows], "data_status": "SIMULATED"}


@router.get("/{instrument_id}/ratings")
def instrument_ratings(instrument_id: str, db: Session = Depends(get_db)):
    instr = db.get(Instrument, instrument_id)
    if not instr:
        raise HTTPException(404, "Instrument not found")
    current = _current_rating(db, instr)
    hist = db.execute(
        select(RatingHistory).where(
            or_(RatingHistory.instrument_id == instrument_id,
                RatingHistory.issuer_id == instr.issuer_id)
        ).order_by(RatingHistory.rating_date)
    ).scalars().all()
    return {
        "current": {
            "agency": current.agency, "symbol": current.symbol,
            "rating_date": current.rating_date.isoformat(), "outlook": current.outlook,
            "action": current.action, "data_status": current.data_status,
        } if current else None,
        "history": [{"agency": h.agency, "symbol": h.symbol,
                     "rating_date": h.rating_date.isoformat(), "action": h.action}
                    for h in hist],
        "data_status": "SIMULATED",
    }


@router.get("/{instrument_id}/liquidity")
def instrument_liquidity(instrument_id: str, db: Session = Depends(get_db)):
    metric = db.execute(
        select(LiquidityMetric).where(LiquidityMetric.instrument_id == instrument_id)
    ).scalars().first()
    return compute_liquidity(metric)


@router.get("/{instrument_id}/news")
def instrument_news(instrument_id: str, db: Session = Depends(get_db)):
    maps = db.execute(
        select(InstrumentNewsMapping).where(InstrumentNewsMapping.instrument_id == instrument_id)
    ).scalars().all()
    ids = [m.news_id for m in maps]
    items = []
    if ids:
        rows = db.execute(select(NewsArticle).where(NewsArticle.id.in_(ids))
                          .order_by(NewsArticle.published_at.desc())).scalars().all()
        items = [_news(n) for n in rows]
    return {"items": items, "data_status": "SIMULATED"}


def _news(n):
    return {
        "id": n.id, "headline": n.headline, "source": n.source,
        "published_at": n.published_at.isoformat(), "category": n.category,
        "summary": n.summary, "risk_impact": n.risk_impact,
        "relevance": float(n.relevance), "data_status": n.data_status,
    }

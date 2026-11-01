"""Portfolio construction, valuation and aggregation using the engine."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from risklens_analytics import run_stress_test
from risklens_analytics.cashflows import CashFlow, generate_bond_cashflows
from risklens_analytics.portfolio.core import Position, portfolio_ytm, weighted_duration, portfolio_dv01
from risklens_analytics.stress_testing.scenarios import StressPosition

from ..models import (
    CreditRating,
    Holding,
    Instrument,
    LiquidityMetric,
    MarketPrice,
)
from .analytics_service import VALUATION_DATE, compute_instrument_analytics, compute_liquidity


def _parse(d):
    if d is None or isinstance(d, date):
        return d
    return date.fromisoformat(str(d))


def _latest_price(db: Session, instrument_id: str) -> float | None:
    row = db.execute(
        select(MarketPrice).where(MarketPrice.instrument_id == instrument_id)
        .order_by(MarketPrice.price_date.desc())
    ).scalars().first()
    return float(row.clean_price) if row else None


def _current_rating(db: Session, instrument_id: str, issuer_id: str) -> CreditRating | None:
    row = db.execute(
        select(CreditRating).where(CreditRating.instrument_id == instrument_id)
    ).scalars().first()
    if row:
        return row
    return db.execute(
        select(CreditRating).where(CreditRating.issuer_id == issuer_id)
    ).scalars().first()


def _holding_cashflows(instr: Instrument, terms, quantity: float, unit_price: float,
                       as_of: date = VALUATION_DATE) -> list[CashFlow]:
    """Contractual cash flows for a holding, scaled by quantity."""
    if terms is None:
        return []
    mat = _parse(terms.maturity_date)
    cat = instr.category
    fv = float(terms.face_value) if terms.face_value else None

    if cat in ("G-Sec", "SDL", "NCD") and mat and fv:
        flows = generate_bond_cashflows(
            _parse(terms.issue_date), mat, float(terms.coupon_rate or 0),
            terms.coupon_frequency or 2, face_value=fv, settlement_date=as_of,
        )
        return [CashFlow(f.pay_date, f.amount * quantity, f.is_coupon, f.is_principal) for f in flows]

    if cat == "T-Bill" and mat and fv:
        return [CashFlow(mat, fv * quantity, is_coupon=False, is_principal=True)]

    if cat == "FD" and mat and fv:
        rate = float(terms.coupon_rate or 0)
        years = max((mat - as_of).days / 365.0, 0.0)
        if terms.cumulative:
            amt = fv * (1 + rate) ** years
            return [CashFlow(mat, amt * quantity, is_coupon=True, is_principal=True)]
        # non-cumulative: quarterly interest + principal at maturity
        flows: list[CashFlow] = []
        freq = terms.coupon_frequency or 4
        n = max(int(round(years * freq)), 1)
        import calendar
        for i in range(1, n + 1):
            m = as_of.month - 1 + int(12 / freq) * i
            y = as_of.year + m // 12
            mm = m % 12 + 1
            dd = min(as_of.day, calendar.monthrange(y, mm)[1])
            pay = date(y, mm, dd)
            amt = fv * rate / freq
            if i == n:
                amt += fv
            flows.append(CashFlow(pay, amt * quantity, is_coupon=True, is_principal=(i == n)))
        return flows

    return []  # Debt MF: redeem at NAV, no contractual schedule


def build_positions(db: Session, portfolio_id: str, as_of: date = VALUATION_DATE) -> list[dict[str, Any]]:
    holdings = db.execute(
        select(Holding).where(Holding.portfolio_id == portfolio_id)
    ).scalars().all()
    out: list[dict[str, Any]] = []
    for h in holdings:
        instr = db.get(Instrument, h.instrument_id)
        if not instr:
            continue
        terms = instr.terms
        price = _latest_price(db, instr.id)
        unit = price
        if unit is None and terms is not None:
            if instr.category == "Debt MF" and terms.nav:
                unit = float(terms.nav)
            elif instr.category == "FD" and terms.face_value:
                # Deposits do not trade; carry at principal (face value).
                unit = float(terms.face_value)
        if unit is None:
            unit = float(h.buy_price or 0)
        qty = float(h.quantity)
        mv = qty * unit if unit is not None else 0.0
        invested = qty * float(h.buy_price or 0)

        a = compute_instrument_analytics(
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
            as_of=as_of,
        )
        rating = _current_rating(db, instr.id, instr.issuer_id)
        metric = db.execute(
            select(LiquidityMetric).where(LiquidityMetric.instrument_id == instr.id)
        ).scalars().first()
        liq = compute_liquidity(metric, holding_mv=mv)

        cfs = _holding_cashflows(instr, terms, qty, unit or 0.0, as_of)
        pos_dv01 = (a.get("dv01") or 0.0) * qty
        out.append({
            "holding_id": h.id,
            "instrument_id": instr.id,
            "name": instr.name,
            "category": instr.category,
            "issuer_id": instr.issuer_id,
            "issuer_name": instr.issuer.name if instr.issuer else instr.issuer_id,
            "sector": instr.sector,
            "is_government": instr.is_government,
            "quantity": qty,
            "unit_price": unit,
            "market_value": mv,
            "invested_value": invested,
            "unrealised_pnl": mv - invested,
            "ytm": a.get("ytm"),
            "modified_duration": a.get("modified_duration"),
            "convexity": a.get("convexity"),
            "dv01_position": pos_dv01,
            "rating": rating.symbol if rating else None,
            "rating_agency": rating.agency if rating else None,
            "rating_outlook": rating.outlook if rating else None,
            "liquidity": liq,
            "cashflows": cfs,
            "maturity_date": terms.maturity_date if terms else None,
            "annual_income": _annual_income(instr, terms, qty),
        })
    return out


def _annual_income(instr: Instrument, terms, qty: float) -> float:
    if terms is None:
        return 0.0
    if instr.category in ("G-Sec", "SDL", "NCD", "FD") and terms.coupon_rate and terms.face_value:
        return float(terms.coupon_rate) * float(terms.face_value) * qty
    if instr.category == "Debt MF" and terms.indicative_ytm and terms.nav:
        return float(terms.indicative_ytm) * float(terms.nav) * qty
    return 0.0


def dashboard(db: Session, portfolio_id: str, as_of: date = VALUATION_DATE) -> dict[str, Any]:
    positions = build_positions(db, portfolio_id, as_of)
    total_mv = sum(p["market_value"] for p in positions)
    total_inv = sum(p["invested_value"] for p in positions)
    annual_income = sum(p["annual_income"] for p in positions)

    pos_objs = [
        Position(p["instrument_id"], p["market_value"], p["cashflows"],
                 p["modified_duration"] or 0.0, p["dv01_position"] or 0.0)
        for p in positions
    ]
    pytm = portfolio_ytm(pos_objs, as_of)
    wdur = weighted_duration(pos_objs)
    pdv01 = portfolio_dv01(pos_objs)

    alloc_cat: dict[str, float] = defaultdict(float)
    alloc_issuer: dict[str, float] = defaultdict(float)
    alloc_rating: dict[str, float] = defaultdict(float)
    ladder: dict[int, float] = defaultdict(float)
    liq_buckets: dict[str, float] = defaultdict(float)
    for p in positions:
        alloc_cat[p["category"]] += p["market_value"]
        alloc_issuer[p["issuer_name"]] += p["market_value"]
        alloc_rating[p["rating"] or "Unrated"] += p["market_value"]
        liq_buckets[p["liquidity"]["classification"]] += p["market_value"]
        mat = _parse(p["maturity_date"])
        if mat:
            ladder[mat.year] += p["market_value"]

    return {
        "as_of": as_of.isoformat(),
        "data_status": "SIMULATED",
        "kpis": {
            "market_value": round(total_mv, 2),
            "invested_value": round(total_inv, 2),
            "unrealised_pnl": round(total_mv - total_inv, 2),
            "unrealised_pnl_pct": round((total_mv - total_inv) / total_inv, 4) if total_inv else 0,
            "weighted_yield": round(pytm, 6) if pytm is not None else None,
            "annual_income": round(annual_income, 2),
            "modified_duration": round(wdur, 4),
            "dv01": round(pdv01, 2),
            "holdings": len(positions),
        },
        "allocation_category": _pct(alloc_cat, total_mv),
        "allocation_issuer": _pct(alloc_issuer, total_mv),
        "allocation_rating": _pct(alloc_rating, total_mv),
        "liquidity_buckets": _pct(liq_buckets, total_mv),
        "maturity_ladder": [{"year": y, "value": round(v, 2)} for y, v in sorted(ladder.items())],
        "positions": [_slim(p) for p in positions],
    }


def portfolio_risk(db: Session, portfolio_id: str, as_of: date = VALUATION_DATE) -> dict[str, Any]:
    positions = build_positions(db, portfolio_id, as_of)
    total_mv = sum(p["market_value"] for p in positions) or 1.0
    sp = [
        StressPosition(
            p["instrument_id"], p["market_value"], p["modified_duration"] or 0.0,
            p["convexity"] or 0.0, p["issuer_id"],
            is_corporate=not p["is_government"],
        )
        for p in positions
    ]
    # choose weakest issuer for downgrade/default illustration
    worst = None
    if positions:
        worst = sorted(positions, key=lambda p: (p["rating"] or "ZZZ"))[-1]["issuer_id"]
    scenarios = run_stress_test(sp, downgrade_issuer=worst, default_issuer=worst)

    issuer_conc: dict[str, float] = defaultdict(float)
    rating_dist: dict[str, float] = defaultdict(float)
    for p in positions:
        issuer_conc[p["issuer_name"]] += p["market_value"]
        rating_dist[p["rating"] or "Unrated"] += p["market_value"]

    return {
        "as_of": as_of.isoformat(),
        "data_status": "SIMULATED",
        "modified_duration": round(weighted_duration([
            Position(p["instrument_id"], p["market_value"], [], p["modified_duration"] or 0.0) for p in positions
        ]), 4),
        "dv01": round(sum(p["dv01_position"] or 0 for p in positions), 2),
        "issuer_concentration": _pct(issuer_conc, total_mv),
        "rating_distribution": _pct(rating_dist, total_mv),
        "stress": [
            {"name": s.name, "description": s.description, "pnl": round(s.pnl, 2),
             "pnl_pct": round(s.pnl_pct, 4), "disclaimer": s.disclaimer}
            for s in scenarios
        ],
        "disclaimer": "Stress losses are mark-to-market estimates, not realised losses if held to maturity.",
    }


def portfolio_cashflow_calendar(db: Session, portfolio_id: str, as_of: date = VALUATION_DATE) -> dict[str, Any]:
    positions = build_positions(db, portfolio_id, as_of)
    monthly: dict[str, dict[str, float]] = defaultdict(lambda: {"coupon": 0.0, "principal": 0.0, "total": 0.0})
    upcoming = []
    for p in positions:
        for cf in p["cashflows"]:
            if cf.pay_date <= as_of:
                continue
            key = f"{cf.pay_date.year}-{cf.pay_date.month:02d}"
            principal = cf.amount if cf.is_principal and not cf.is_coupon else (
                cf.amount * 0 if not cf.is_principal else cf.amount)
            # split coupon vs principal roughly for last flow
            if cf.is_principal and cf.is_coupon:
                monthly[key]["coupon"] += 0.0
                monthly[key]["principal"] += cf.amount
            elif cf.is_principal:
                monthly[key]["principal"] += cf.amount
            else:
                monthly[key]["coupon"] += cf.amount
            monthly[key]["total"] += cf.amount
            upcoming.append({
                "instrument_id": p["instrument_id"], "name": p["name"],
                "pay_date": cf.pay_date.isoformat(), "amount": round(cf.amount, 2),
                "kind": cf.kind,
            })
    upcoming.sort(key=lambda x: x["pay_date"])
    calendar = [
        {"month": k, "coupon": round(v["coupon"], 2), "principal": round(v["principal"], 2),
         "total": round(v["total"], 2)}
        for k, v in sorted(monthly.items())
    ]
    return {"as_of": as_of.isoformat(), "data_status": "SIMULATED",
            "calendar": calendar, "upcoming": upcoming[:40]}


def portfolio_liquidity(db: Session, portfolio_id: str, as_of: date = VALUATION_DATE) -> dict[str, Any]:
    positions = build_positions(db, portfolio_id, as_of)
    buckets: dict[str, float] = defaultdict(float)
    illiquid = []
    total_days_num = 0.0
    total_days_den = 0.0
    for p in positions:
        cls = p["liquidity"]["classification"]
        buckets[cls] += p["market_value"]
        days = p["liquidity"]["est_liquidation_days"]
        if days is not None:
            total_days_num += days * p["market_value"]
            total_days_den += p["market_value"]
        if cls in ("Low liquidity", "Very low liquidity", "Insufficient data"):
            illiquid.append({
                "instrument_id": p["instrument_id"], "name": p["name"],
                "classification": cls, "market_value": round(p["market_value"], 2),
                "est_liquidation_days": days,
            })
    total_mv = sum(p["market_value"] for p in positions) or 1.0
    return {
        "as_of": as_of.isoformat(), "data_status": "SIMULATED",
        "buckets": _pct(buckets, total_mv),
        "weighted_est_liquidation_days": round(total_days_num / total_days_den, 2) if total_days_den else None,
        "illiquid_holdings": illiquid,
        "methodology": "Liquidation days = market value / (ADTV x participation 10%). Historical estimate.",
    }


def _pct(d: dict[str, float], total: float) -> list[dict[str, Any]]:
    total = total or 1.0
    return [
        {"label": k, "value": round(v, 2), "pct": round(v / total, 4)}
        for k, v in sorted(d.items(), key=lambda x: -x[1])
    ]


def _slim(p: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in p.items() if k not in ("cashflows", "liquidity")} | {
        "liquidity_class": p["liquidity"]["classification"],
        "liquidity_score": p["liquidity"]["score"],
    }

"""Seed the RiskLens database from the simulated sample dataset.

Usage (from repo root, venv active):
    python -m backend.app.seed
or
    python backend/seed.py
"""

from __future__ import annotations

import json
import os
from datetime import date

from sqlalchemy import select

from .core.security import hash_password
from .db.session import Base, SessionLocal, engine
from .models import (
    Alert,
    BondTerms,
    CreditRating,
    DataException,
    DataSource,
    Holding,
    InstrumentNewsMapping,
    Instrument,
    Issuer,
    IssuerNewsMapping,
    LiquidityMetric,
    MarketPrice,
    NewsArticle,
    Portfolio,
    RatingHistory,
    User,
    UserPreference,
)

SAMPLE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "sample", "risklens_sample.json",
)

DEMO_EMAIL = "demo@risklens.sim"
DEMO_PASSWORD = "demo1234"


def _d(s):
    return date.fromisoformat(s) if s else None


def run(reset: bool = True) -> None:
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with open(SAMPLE_PATH) as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        # Issuers
        for i in data["issuers"]:
            db.merge(Issuer(id=i["id"], name=i["name"], sector=i["sector"],
                            is_government=i["is_government"], data_status="SIMULATED"))

        # Instruments + bond terms
        for ins in data["instruments"]:
            db.merge(Instrument(
                id=ins["id"], isin=ins.get("isin"), name=ins["name"], category=ins["category"],
                issuer_id=ins["issuer_id"], sector=ins.get("sector", ""), currency=ins.get("currency", "INR"),
                is_government=ins.get("is_government", False), listing_exchange=ins.get("listing_exchange"),
                min_investment=ins.get("min_investment"), data_status="SIMULATED",
            ))
            db.flush()
            db.merge(BondTerms(
                instrument_id=ins["id"], issue_date=_d(ins.get("issue_date")),
                maturity_date=_d(ins.get("maturity_date")), face_value=ins.get("face_value"),
                coupon_rate=ins.get("coupon_rate"), coupon_frequency=ins.get("coupon_frequency"),
                day_count=ins.get("day_count"), redemption_value=ins.get("redemption_value"),
                callable=ins.get("callable", False), puttable=ins.get("puttable", False),
                call_date=_d(ins.get("call_date")), call_price=ins.get("call_price"),
                secured=ins.get("secured", False), seniority=ins.get("seniority"),
                cumulative=ins.get("cumulative"), fund_kind=ins.get("fund_kind"),
                indicative_ytm=ins.get("indicative_ytm"), indicative_duration=ins.get("indicative_duration"),
                nav=ins.get("nav"),
            ))

        # Ratings
        for r in data["credit_ratings"]:
            db.add(CreditRating(
                instrument_id=r.get("instrument_id"), issuer_id=r["issuer_id"], agency=r["agency"],
                symbol=r["symbol"], rating_date=_d(r["rating_date"]), outlook=r.get("outlook"),
                action=r.get("action"), previous_symbol=r.get("previous_symbol"), is_current=True,
            ))
        for r in data.get("rating_history", []):
            db.add(RatingHistory(
                instrument_id=r.get("instrument_id"), issuer_id=r["issuer_id"], agency=r["agency"],
                symbol=r["symbol"], rating_date=_d(r["rating_date"]), action=r.get("action"),
            ))

        # Prices
        for p in data["market_prices"]:
            db.add(MarketPrice(instrument_id=p["instrument_id"], price_date=_d(p["price_date"]),
                               clean_price=p["clean_price"], source=p.get("source", "SIM-FEED")))

        # Liquidity
        for m in data["liquidity_metrics"]:
            db.add(LiquidityMetric(
                instrument_id=m["instrument_id"], avg_daily_traded_value=m.get("avg_daily_traded_value"),
                trading_days=m.get("trading_days"), window_days=m.get("window_days"),
                bid_ask_spread_bps=m.get("bid_ask_spread_bps"), market_depth_value=m.get("market_depth_value"),
                last_traded_date=_d(m.get("last_traded_date")), as_of_date=_d(m.get("as_of_date")),
            ))

        # News + mappings
        news_by_headline = {}
        for n in data["news"]:
            art = NewsArticle(
                headline=n["headline"], source=n["source"], published_at=_d(n["published_at"]),
                category=n["category"], summary=n["summary"], risk_impact=n["risk_impact"],
                relevance=n["relevance"],
            )
            db.add(art)
            db.flush()
            news_by_headline[n["headline"]] = art.id
            if n.get("issuer_id"):
                db.add(IssuerNewsMapping(news_id=art.id, issuer_id=n["issuer_id"]))
            for iid in n.get("instrument_ids", []):
                db.add(InstrumentNewsMapping(news_id=art.id, instrument_id=iid))

        # Data sources (provider adapters; simulated)
        for name, kind in [("SIM-FEED", "market-price"), ("SIM-RATING-AGENCY", "credit-rating"),
                           ("SIM-EXCHANGE-FILING", "news"), ("SIM-CENTRAL-BANK", "news"),
                           ("SIM-NDS", "trading"), ("CSV-IMPORT", "manual")]:
            db.merge(DataSource(name=name, kind=kind, status="simulated",
                                description="Simulated provider adapter (replace with licensed source)."))

        db.commit()

        # Run data-quality validations -> exceptions
        _run_data_quality(db)

        # Demo user + sample portfolios
        demo = db.execute(select(User).where(User.email == DEMO_EMAIL)).scalars().first()
        if not demo:
            demo = User(email=DEMO_EMAIL, full_name="Demo Investor (Simulated)",
                        password_hash=hash_password(DEMO_PASSWORD))
            db.add(demo)
            db.flush()
            db.add(UserPreference(user_id=demo.id))

        for pf in data["portfolios"]:
            existing = db.execute(
                select(Portfolio).where(Portfolio.user_id == demo.id, Portfolio.name == pf["name"])
            ).scalars().first()
            if existing:
                continue
            portfolio = Portfolio(user_id=demo.id, name=pf["name"], description=pf["description"])
            db.add(portfolio)
            db.flush()
            for h in pf["holdings"]:
                db.add(Holding(portfolio_id=portfolio.id, instrument_id=h["instrument_id"],
                               quantity=h["quantity"], buy_price=h["buy_price"], buy_date=_d(h["buy_date"])))
        db.commit()

        # Generate alerts from downgrade/negative-outlook ratings for demo holdings
        _generate_alerts(db, demo.id)
        db.commit()

        counts = {
            "issuers": db.query(Issuer).count(),
            "instruments": db.query(Instrument).count(),
            "ratings": db.query(CreditRating).count(),
            "prices": db.query(MarketPrice).count(),
            "news": db.query(NewsArticle).count(),
            "portfolios": db.query(Portfolio).count(),
            "exceptions": db.query(DataException).count(),
            "alerts": db.query(Alert).count(),
        }
        print("Seed complete:", counts)
        print(f"Demo login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
    finally:
        db.close()


def _run_data_quality(db) -> None:
    """Validate loaded data and record exceptions."""
    today = date(2025, 1, 15)
    for instr in db.query(Instrument).all():
        terms = instr.terms
        rating = db.execute(
            select(CreditRating).where(CreditRating.instrument_id == instr.id)
        ).scalars().first() or db.execute(
            select(CreditRating).where(CreditRating.issuer_id == instr.issuer_id)
        ).scalars().first()
        if rating is None:
            db.add(DataException(entity_type="instrument", entity_id=instr.id, rule="missing_rating",
                                 expected_condition="rating present", severity="High"))
        price = db.execute(
            select(MarketPrice).where(MarketPrice.instrument_id == instr.id)
            .order_by(MarketPrice.price_date.desc())
        ).scalars().first()
        if price is None and instr.category not in ("FD", "Debt MF"):
            db.add(DataException(entity_type="instrument", entity_id=instr.id, rule="missing_price",
                                 expected_condition="price present", severity="Critical"))
        metric = db.execute(
            select(LiquidityMetric).where(LiquidityMetric.instrument_id == instr.id)
        ).scalars().first()
        if metric and metric.avg_daily_traded_value is None and instr.category not in ("FD", "Debt MF"):
            db.add(DataException(entity_type="instrument", entity_id=instr.id, rule="no_secondary_liquidity",
                                 expected_condition="traded value present", severity="Low"))
    db.commit()


def _generate_alerts(db, user_id: str) -> None:
    from .models import Portfolio as P
    portfolios = db.execute(select(P).where(P.user_id == user_id)).scalars().all()
    for p in portfolios:
        for h in p.holdings:
            rating = db.execute(
                select(CreditRating).where(CreditRating.instrument_id == h.instrument_id)
            ).scalars().first()
            instr = db.get(Instrument, h.instrument_id)
            if rating and rating.outlook in ("Negative", "Watch"):
                exposure = float(h.quantity) * float(h.buy_price or 0)
                db.add(Alert(
                    user_id=user_id, portfolio_id=p.id, instrument_id=h.instrument_id,
                    trigger="negative_outlook" if rating.outlook == "Negative" else "rating_watch",
                    severity="High" if rating.outlook == "Negative" else "Medium",
                    exposure=exposure, source=rating.agency,
                    message=f"{instr.name}: {rating.agency} outlook {rating.outlook} "
                            f"(rating {rating.symbol}). Review credit exposure.",
                ))


def seed_if_empty() -> None:
    """Seed only when the database has no instruments (safe for deploys)."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        count = db.query(Instrument).count()
    finally:
        db.close()
    if count == 0:
        print("Empty database detected — seeding simulated dataset.")
        run(reset=False)
    else:
        print(f"Database already has {count} instruments — skipping seed.")


if __name__ == "__main__":
    import sys

    if "--if-empty" in sys.argv:
        seed_if_empty()
    else:
        run()

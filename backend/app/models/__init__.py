"""SQLAlchemy ORM models — 29 normalised tables.

Monetary and yield fields use NUMERIC/Numeric for decimal precision
(never binary float) per the data-integrity requirements.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.session import Base

NUM = Numeric(24, 8)
MONEY = Numeric(24, 4)


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


# 1. users
class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="investor")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    portfolios = relationship("Portfolio", back_populates="user")


# 2. user_preferences
class UserPreference(Base, TimestampMixin):
    __tablename__ = "user_preferences"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    base_currency: Mapped[str] = mapped_column(String(8), default="INR")
    risk_profile: Mapped[str] = mapped_column(String(32), default="balanced")
    min_rating: Mapped[str | None] = mapped_column(String(16), nullable=True)
    settings_json: Mapped[dict] = mapped_column(JSON, default=dict)
    user = relationship("User", back_populates="preferences")


# 3. portfolios
class Portfolio(Base, TimestampMixin):
    __tablename__ = "portfolios"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    base_currency: Mapped[str] = mapped_column(String(8), default="INR")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all,delete-orphan")
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all,delete-orphan")


# 4. portfolio_snapshots
class PortfolioSnapshot(Base, TimestampMixin):
    __tablename__ = "portfolio_snapshots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True)
    snapshot_date: Mapped[date] = mapped_column(Date)
    market_value: Mapped[float] = mapped_column(MONEY, default=0)
    invested_value: Mapped[float] = mapped_column(MONEY, default=0)
    weighted_yield: Mapped[float | None] = mapped_column(NUM, nullable=True)
    modified_duration: Mapped[float | None] = mapped_column(NUM, nullable=True)
    data_json: Mapped[dict] = mapped_column(JSON, default=dict)


# 5. issuers
class Issuer(Base, TimestampMixin):
    __tablename__ = "issuers"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    sector: Mapped[str] = mapped_column(String(64), default="")
    is_government: Mapped[bool] = mapped_column(Boolean, default=False)
    data_status: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    instruments = relationship("Instrument", back_populates="issuer")


# 6. instruments
class Instrument(Base, TimestampMixin):
    __tablename__ = "instruments"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    isin: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(32), index=True)
    issuer_id: Mapped[str] = mapped_column(ForeignKey("issuers.id"), index=True)
    sector: Mapped[str] = mapped_column(String(64), default="")
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    is_government: Mapped[bool] = mapped_column(Boolean, default=False)
    listing_exchange: Mapped[str | None] = mapped_column(String(32), nullable=True)
    min_investment: Mapped[float | None] = mapped_column(MONEY, nullable=True)
    data_status: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    data_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    issuer = relationship("Issuer", back_populates="instruments")
    terms = relationship("BondTerms", back_populates="instrument", uselist=False, cascade="all,delete-orphan")

    __table_args__ = (UniqueConstraint("isin", name="uq_instrument_isin"),)


# 7. bond_terms
class BondTerms(Base, TimestampMixin):
    __tablename__ = "bond_terms"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"), unique=True)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    maturity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    face_value: Mapped[float | None] = mapped_column(MONEY, nullable=True)
    coupon_rate: Mapped[float | None] = mapped_column(NUM, nullable=True)
    coupon_frequency: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_count: Mapped[str | None] = mapped_column(String(16), nullable=True)
    redemption_value: Mapped[float | None] = mapped_column(MONEY, nullable=True)
    callable: Mapped[bool] = mapped_column(Boolean, default=False)
    puttable: Mapped[bool] = mapped_column(Boolean, default=False)
    call_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    call_price: Mapped[float | None] = mapped_column(MONEY, nullable=True)
    put_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    put_price: Mapped[float | None] = mapped_column(MONEY, nullable=True)
    secured: Mapped[bool] = mapped_column(Boolean, default=False)
    seniority: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cumulative: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    fund_kind: Mapped[str | None] = mapped_column(String(32), nullable=True)
    indicative_ytm: Mapped[float | None] = mapped_column(NUM, nullable=True)
    indicative_duration: Mapped[float | None] = mapped_column(NUM, nullable=True)
    nav: Mapped[float | None] = mapped_column(MONEY, nullable=True)

    instrument = relationship("Instrument", back_populates="terms")


# 8. coupon_schedules
class CouponSchedule(Base):
    __tablename__ = "coupon_schedules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"), index=True)
    pay_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[float] = mapped_column(MONEY)
    is_principal: Mapped[bool] = mapped_column(Boolean, default=False)


# 9. credit_ratings (current)
class CreditRating(Base, TimestampMixin):
    __tablename__ = "credit_ratings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    instrument_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), nullable=True, index=True)
    issuer_id: Mapped[str] = mapped_column(ForeignKey("issuers.id"), index=True)
    agency: Mapped[str] = mapped_column(String(32))
    symbol: Mapped[str] = mapped_column(String(16))
    rating_date: Mapped[date] = mapped_column(Date)
    outlook: Mapped[str | None] = mapped_column(String(32), nullable=True)
    action: Mapped[str | None] = mapped_column(String(32), nullable=True)
    previous_symbol: Mapped[str | None] = mapped_column(String(16), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    data_status: Mapped[str] = mapped_column(String(32), default="SIMULATED")


# 10. rating_history
class RatingHistory(Base):
    __tablename__ = "rating_history"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    instrument_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), nullable=True, index=True)
    issuer_id: Mapped[str] = mapped_column(ForeignKey("issuers.id"), index=True)
    agency: Mapped[str] = mapped_column(String(32))
    symbol: Mapped[str] = mapped_column(String(16))
    rating_date: Mapped[date] = mapped_column(Date)
    action: Mapped[str | None] = mapped_column(String(32), nullable=True)
    data_status: Mapped[str] = mapped_column(String(32), default="SIMULATED")


# 11. market_prices
class MarketPrice(Base):
    __tablename__ = "market_prices"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"), index=True)
    price_date: Mapped[date] = mapped_column(Date)
    clean_price: Mapped[float] = mapped_column(MONEY)
    dirty_price: Mapped[float | None] = mapped_column(MONEY, nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="SIM-FEED")
    data_status: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    __table_args__ = (Index("ix_price_instr_date", "instrument_id", "price_date"),)


# 12. market_trades
class MarketTrade(Base):
    __tablename__ = "market_trades"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"), index=True)
    trade_date: Mapped[date] = mapped_column(Date)
    traded_value: Mapped[float] = mapped_column(MONEY)
    traded_quantity: Mapped[float | None] = mapped_column(NUM, nullable=True)
    num_trades: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_status: Mapped[str] = mapped_column(String(32), default="SIMULATED")


# 13. order_book_snapshots
class OrderBookSnapshot(Base):
    __tablename__ = "order_book_snapshots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"), index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    best_bid: Mapped[float | None] = mapped_column(MONEY, nullable=True)
    best_ask: Mapped[float | None] = mapped_column(MONEY, nullable=True)
    bid_qty: Mapped[float | None] = mapped_column(NUM, nullable=True)
    ask_qty: Mapped[float | None] = mapped_column(NUM, nullable=True)
    feed_status: Mapped[str] = mapped_column(String(16), default="end-of-day")
    data_status: Mapped[str] = mapped_column(String(32), default="SIMULATED")


# 14. liquidity_metrics
class LiquidityMetric(Base, TimestampMixin):
    __tablename__ = "liquidity_metrics"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"), unique=True)
    avg_daily_traded_value: Mapped[float | None] = mapped_column(MONEY, nullable=True)
    trading_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    window_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bid_ask_spread_bps: Mapped[float | None] = mapped_column(NUM, nullable=True)
    market_depth_value: Mapped[float | None] = mapped_column(MONEY, nullable=True)
    last_traded_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    as_of_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_status: Mapped[str] = mapped_column(String(32), default="SIMULATED")


# 15. transactions
class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"), index=True)
    txn_type: Mapped[str] = mapped_column(String(16))  # buy/sell/coupon/fee/maturity
    trade_date: Mapped[date] = mapped_column(Date)
    quantity: Mapped[float] = mapped_column(NUM, default=0)
    price: Mapped[float] = mapped_column(MONEY, default=0)
    fees: Mapped[float] = mapped_column(MONEY, default=0)
    portfolio = relationship("Portfolio", back_populates="transactions")


# 16. holdings
class Holding(Base, TimestampMixin):
    __tablename__ = "holdings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"), index=True)
    quantity: Mapped[float] = mapped_column(NUM, default=0)
    buy_price: Mapped[float] = mapped_column(MONEY, default=0)
    buy_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    portfolio = relationship("Portfolio", back_populates="holdings")
    instrument = relationship("Instrument")


# 17. cashflows (recorded/actual)
class Cashflow(Base):
    __tablename__ = "cashflows"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    portfolio_id: Mapped[str | None] = mapped_column(ForeignKey("portfolios.id"), nullable=True, index=True)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"), index=True)
    pay_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[float] = mapped_column(MONEY)
    kind: Mapped[str] = mapped_column(String(16), default="coupon")
    is_actual: Mapped[bool] = mapped_column(Boolean, default=False)


# 18. news_articles
class NewsArticle(Base, TimestampMixin):
    __tablename__ = "news_articles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    headline: Mapped[str] = mapped_column(String(512))
    source: Mapped[str] = mapped_column(String(64))
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    published_at: Mapped[date] = mapped_column(Date)
    category: Mapped[str] = mapped_column(String(64))
    summary: Mapped[str] = mapped_column(Text, default="")
    risk_impact: Mapped[str] = mapped_column(String(16), default="Informational")
    relevance: Mapped[float] = mapped_column(NUM, default=0)
    data_status: Mapped[str] = mapped_column(String(32), default="SIMULATED")


# 19. issuer_news_mapping
class IssuerNewsMapping(Base):
    __tablename__ = "issuer_news_mapping"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    news_id: Mapped[str] = mapped_column(ForeignKey("news_articles.id"), index=True)
    issuer_id: Mapped[str] = mapped_column(ForeignKey("issuers.id"), index=True)


# 20. instrument_news_mapping
class InstrumentNewsMapping(Base):
    __tablename__ = "instrument_news_mapping"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    news_id: Mapped[str] = mapped_column(ForeignKey("news_articles.id"), index=True)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"), index=True)


# 21. risk_results
class RiskResult(Base, TimestampMixin):
    __tablename__ = "risk_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True)
    as_of: Mapped[date] = mapped_column(Date)
    metrics_json: Mapped[dict] = mapped_column(JSON, default=dict)


# 22. portfolio_optimisation_runs
class OptimisationRun(Base, TimestampMixin):
    __tablename__ = "portfolio_optimisation_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    objective: Mapped[str] = mapped_column(String(32))
    amount: Mapped[float] = mapped_column(MONEY)
    inputs_json: Mapped[dict] = mapped_column(JSON, default=dict)
    feasible: Mapped[bool] = mapped_column(Boolean, default=False)
    result_json: Mapped[dict] = mapped_column(JSON, default=dict)


# 23. portfolio_allocations
class PortfolioAllocation(Base):
    __tablename__ = "portfolio_allocations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("portfolio_optimisation_runs.id"), index=True)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("instruments.id"))
    weight: Mapped[float] = mapped_column(NUM)
    amount: Mapped[float] = mapped_column(MONEY)


# 24. stress_test_results
class StressTestResult(Base, TimestampMixin):
    __tablename__ = "stress_test_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True)
    scenario: Mapped[str] = mapped_column(String(64))
    pnl: Mapped[float] = mapped_column(MONEY)
    pnl_pct: Mapped[float] = mapped_column(NUM)


# 25. alerts
class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    portfolio_id: Mapped[str | None] = mapped_column(ForeignKey("portfolios.id"), nullable=True, index=True)
    instrument_id: Mapped[str | None] = mapped_column(ForeignKey("instruments.id"), nullable=True)
    trigger: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(16), default="Medium")
    exposure: Mapped[float | None] = mapped_column(MONEY, nullable=True)
    message: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(64), default="SIM")
    status: Mapped[str] = mapped_column(String(16), default="open")


# 26. data_sources
class DataSource(Base, TimestampMixin):
    __tablename__ = "data_sources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    kind: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="simulated")
    description: Mapped[str] = mapped_column(Text, default="")


# 27. ingestion_runs
class IngestionRun(Base, TimestampMixin):
    __tablename__ = "ingestion_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("data_sources.id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    status: Mapped[str] = mapped_column(String(16), default="success")
    records: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")


# 28. data_exceptions
class DataException(Base, TimestampMixin):
    __tablename__ = "data_exceptions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    entity_type: Mapped[str] = mapped_column(String(32))
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rule: Mapped[str] = mapped_column(String(64))
    detected_value: Mapped[str | None] = mapped_column(String(128), nullable=True)
    expected_condition: Mapped[str | None] = mapped_column(String(128), nullable=True)
    severity: Mapped[str] = mapped_column(String(16), default="Low")
    status: Mapped[str] = mapped_column(String(16), default="open")
    resolution_notes: Mapped[str] = mapped_column(Text, default="")


# 29. audit_logs
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(64))
    entity: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[str] = mapped_column(Text, default="")

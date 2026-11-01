"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, EmailStr, Field


# ---- Auth ----
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = ""


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---- Instruments ----
class InstrumentSummary(BaseModel):
    id: str
    isin: str | None = None
    name: str
    category: str
    issuer_name: str
    sector: str
    coupon_rate: float | None = None
    maturity_date: date | None = None
    clean_price: float | None = None
    ytm: float | None = None
    modified_duration: float | None = None
    rating: str | None = None
    rating_agency: str | None = None
    liquidity_score: float | None = None
    liquidity_class: str = "Insufficient data"
    is_government: bool = False
    data_status: str = "SIMULATED"


class InstrumentDetail(InstrumentSummary):
    issue_date: date | None = None
    face_value: float | None = None
    coupon_frequency: int | None = None
    day_count: str | None = None
    callable: bool = False
    puttable: bool = False
    secured: bool = False
    seniority: str | None = None
    accrued_interest: float | None = None
    dirty_price: float | None = None
    current_yield: float | None = None
    ytc: float | None = None
    convexity: float | None = None
    dv01: float | None = None
    analytics: dict[str, Any] = {}


class Paginated(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int


# ---- Calculations ----
class BondPriceIn(BaseModel):
    issue_date: date
    maturity_date: date
    coupon_rate: float
    frequency: int
    yield_: float = Field(alias="yield")
    settlement_date: date
    face_value: float = 100.0
    day_count: str = "ACT/365F"

    model_config = {"populate_by_name": True}


class YieldIn(BaseModel):
    issue_date: date
    maturity_date: date
    coupon_rate: float
    frequency: int
    clean_price: float
    settlement_date: date
    face_value: float = 100.0
    day_count: str = "ACT/365F"


# ---- Portfolios ----
class PortfolioCreate(BaseModel):
    name: str
    description: str = ""


class HoldingCreate(BaseModel):
    instrument_id: str
    quantity: float
    buy_price: float
    buy_date: date | None = None


class PortfolioSummary(BaseModel):
    id: str
    name: str
    description: str
    holdings_count: int = 0
    market_value: float = 0.0


# ---- Builder ----
class BuilderConstraints(BaseModel):
    max_issuer_weight: float = 0.25
    max_sector_weight: float = 0.40
    min_government_weight: float = 0.0
    max_low_rated_weight: float = 1.0
    min_liquidity_weight: float = 0.0
    liquidity_floor: float = 50.0
    max_duration: float | None = None
    max_maturity_years: float | None = None
    max_weight_per_instrument: float = 0.35
    min_instruments: int = 1


class BuilderIn(BaseModel):
    amount: float = 1_000_000
    objective: str = "max_yield"
    constraints: BuilderConstraints = BuilderConstraints()
    universe: list[str] | None = None

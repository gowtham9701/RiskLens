"""Portfolio management and analytics routes (user-scoped)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...models import Holding, Instrument, Portfolio, User
from ...schemas import HoldingCreate, PortfolioCreate, PortfolioSummary
from ...services import portfolio_service as ps
from ..deps import get_current_user

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


def _owned(db: Session, portfolio_id: str, user: User) -> Portfolio:
    p = db.get(Portfolio, portfolio_id)
    if not p or p.user_id != user.id or p.deleted_at is not None:
        raise HTTPException(404, "Portfolio not found")
    return p


def _summary(db: Session, p: Portfolio) -> dict:
    positions = ps.build_positions(db, p.id)
    return {
        "id": p.id, "name": p.name, "description": p.description,
        "holdings_count": len(positions),
        "market_value": round(sum(x["market_value"] for x in positions), 2),
    }


@router.get("")
def list_portfolios(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(
        select(Portfolio).where(Portfolio.user_id == user.id, Portfolio.deleted_at.is_(None))
    ).scalars().all()
    return {"items": [_summary(db, p) for p in rows]}


@router.post("", response_model=PortfolioSummary)
def create_portfolio(body: PortfolioCreate, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    p = Portfolio(user_id=user.id, name=body.name, description=body.description)
    db.add(p)
    db.commit()
    return PortfolioSummary(id=p.id, name=p.name, description=p.description)


@router.get("/{portfolio_id}")
def get_portfolio(portfolio_id: str, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    p = _owned(db, portfolio_id, user)
    positions = ps.build_positions(db, p.id)
    return {
        "id": p.id, "name": p.name, "description": p.description,
        "data_status": "SIMULATED",
        "holdings": [ps._slim(x) for x in positions],
        "market_value": round(sum(x["market_value"] for x in positions), 2),
    }


@router.post("/{portfolio_id}/holdings")
def add_holding(portfolio_id: str, body: HoldingCreate, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    _owned(db, portfolio_id, user)
    if not db.get(Instrument, body.instrument_id):
        raise HTTPException(400, "Unknown instrument")
    h = Holding(portfolio_id=portfolio_id, instrument_id=body.instrument_id,
                quantity=body.quantity, buy_price=body.buy_price, buy_date=body.buy_date)
    db.add(h)
    db.commit()
    return {"id": h.id, "instrument_id": h.instrument_id, "quantity": float(h.quantity)}


@router.delete("/{portfolio_id}/holdings/{holding_id}")
def delete_holding(portfolio_id: str, holding_id: str, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    _owned(db, portfolio_id, user)
    h = db.get(Holding, holding_id)
    if not h or h.portfolio_id != portfolio_id:
        raise HTTPException(404, "Holding not found")
    db.delete(h)
    db.commit()
    return {"deleted": holding_id}


@router.get("/{portfolio_id}/dashboard")
def dashboard(portfolio_id: str, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    _owned(db, portfolio_id, user)
    return ps.dashboard(db, portfolio_id)


@router.get("/{portfolio_id}/risk")
def risk(portfolio_id: str, db: Session = Depends(get_db),
         user: User = Depends(get_current_user)):
    _owned(db, portfolio_id, user)
    return ps.portfolio_risk(db, portfolio_id)


@router.get("/{portfolio_id}/cashflows")
def cashflows(portfolio_id: str, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    _owned(db, portfolio_id, user)
    return ps.portfolio_cashflow_calendar(db, portfolio_id)


@router.get("/{portfolio_id}/liquidity")
def liquidity(portfolio_id: str, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    _owned(db, portfolio_id, user)
    return ps.portfolio_liquidity(db, portfolio_id)

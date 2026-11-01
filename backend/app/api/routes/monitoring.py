"""Alerts, news, reports, data-quality and health routes."""

from __future__ import annotations

import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...models import (
    Alert,
    DataException,
    DataSource,
    NewsArticle,
    Portfolio,
    User,
)
from ...services import reporting_service
from ..deps import get_current_user

router = APIRouter(tags=["monitoring"])


# ---- Alerts ----
@router.get("/alerts")
def list_alerts(portfolio_id: str | None = None, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    q = select(Alert).where(Alert.user_id == user.id)
    if portfolio_id:
        q = q.where(Alert.portfolio_id == portfolio_id)
    rows = db.execute(q.order_by(Alert.created_at.desc())).scalars().all()
    return {"items": [{
        "id": a.id, "trigger": a.trigger, "severity": a.severity,
        "instrument_id": a.instrument_id, "portfolio_id": a.portfolio_id,
        "exposure": float(a.exposure) if a.exposure is not None else None,
        "message": a.message, "source": a.source, "status": a.status,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    } for a in rows]}


@router.patch("/alerts/{alert_id}")
def update_alert(alert_id: str, body: dict, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    a = db.get(Alert, alert_id)
    if not a or a.user_id != user.id:
        raise HTTPException(404, "Alert not found")
    if "status" in body:
        a.status = body["status"]
    db.commit()
    return {"id": a.id, "status": a.status}


# ---- News ----
@router.get("/news")
def list_news(db: Session = Depends(get_db)):
    rows = db.execute(select(NewsArticle).order_by(NewsArticle.published_at.desc())).scalars().all()
    out = []
    for n in rows:
        out.append({
            "id": n.id, "headline": n.headline, "source": n.source,
            "published_at": n.published_at.isoformat(), "category": n.category,
            "summary": n.summary, "risk_impact": n.risk_impact,
            "relevance": float(n.relevance), "data_status": n.data_status,
        })
    return {"items": out, "data_status": "SIMULATED",
            "disclaimer": "Simulated news; AI summaries distinguish facts from interpretation."}


# ---- Reports ----
@router.get("/reports/portfolio/{portfolio_id}")
def portfolio_report(portfolio_id: str, format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
                     db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = db.get(Portfolio, portfolio_id)
    if not p or p.user_id != user.id:
        raise HTTPException(404, "Portfolio not found")
    if format == "xlsx":
        data = reporting_service.portfolio_excel(db, p)
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        fname = f"risklens_{p.name}.xlsx"
    else:
        data = reporting_service.portfolio_pdf(db, p)
        media = "application/pdf"
        fname = f"risklens_{p.name}.pdf"
    return StreamingResponse(io.BytesIO(data), media_type=media,
                             headers={"Content-Disposition": f'attachment; filename="{fname}"'})


# ---- Data quality console ----
@router.get("/data-quality/exceptions")
def data_exceptions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(select(DataException).order_by(DataException.created_at.desc())).scalars().all()
    return {"items": [{
        "id": e.id, "entity_type": e.entity_type, "entity_id": e.entity_id,
        "rule": e.rule, "detected_value": e.detected_value,
        "expected_condition": e.expected_condition, "severity": e.severity,
        "status": e.status, "resolution_notes": e.resolution_notes,
    } for e in rows]}


@router.get("/data-sources")
def data_sources(db: Session = Depends(get_db)):
    rows = db.execute(select(DataSource)).scalars().all()
    return {"items": [{"name": s.name, "kind": s.kind, "status": s.status,
                       "description": s.description} for s in rows]}

"""Lightweight data-quality validators.

These mirror the checks run during seeding and can be reused by ingestion
adapters before data enters critical calculations. Each returns a list of
exception dicts: {entity_type, entity_id, rule, detected_value,
expected_condition, severity}.
"""

from __future__ import annotations

from datetime import date
from typing import Any

CRITICAL, HIGH, MEDIUM, LOW = "Critical", "High", "Medium", "Low"


def validate_instruments(instruments: list[dict[str, Any]]) -> list[dict]:
    exceptions: list[dict] = []
    seen_ids: set[str] = set()
    seen_isins: set[str] = set()
    for ins in instruments:
        iid = ins.get("id")
        if iid in seen_ids:
            exceptions.append(_ex("instrument", iid, "duplicate_instrument_id", iid, "unique id", CRITICAL))
        seen_ids.add(iid)
        isin = ins.get("isin")
        if isin:
            if isin in seen_isins:
                exceptions.append(_ex("instrument", iid, "duplicate_isin", isin, "unique isin", CRITICAL))
            seen_isins.add(isin)
        mat = ins.get("maturity_date")
        issue = ins.get("issue_date")
        if mat and issue and str(mat) <= str(issue):
            exceptions.append(_ex("instrument", iid, "invalid_maturity_date", mat, "maturity > issue", HIGH))
    return exceptions


def validate_prices(prices: list[dict[str, Any]], as_of: date, stale_days: int = 30) -> list[dict]:
    exceptions: list[dict] = []
    for p in prices:
        price = p.get("clean_price")
        if price is None:
            exceptions.append(_ex("price", p.get("instrument_id"), "missing_price", None, "price present", CRITICAL))
        elif price <= 0:
            exceptions.append(_ex("price", p.get("instrument_id"), "non_positive_price", price, "price > 0", HIGH))
        pdate = p.get("price_date")
        if pdate and (as_of - date.fromisoformat(str(pdate))).days > stale_days:
            exceptions.append(_ex("price", p.get("instrument_id"), "stale_price", pdate,
                                  f"within {stale_days} days", MEDIUM))
    return exceptions


def validate_allocation(weights: dict[str, float], tol: float = 1e-3) -> list[dict]:
    total = sum(weights.values())
    if abs(total - 1.0) > tol:
        return [_ex("portfolio", None, "allocation_not_100pct", round(total, 6), "weights sum to 1.0", HIGH)]
    return []


def _ex(entity_type, entity_id, rule, detected, expected, severity) -> dict:
    return {
        "entity_type": entity_type, "entity_id": entity_id, "rule": rule,
        "detected_value": None if detected is None else str(detected),
        "expected_condition": expected, "severity": severity,
    }

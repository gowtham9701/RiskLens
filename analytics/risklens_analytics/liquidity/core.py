"""Transparent 0-100 liquidity scoring and liquidation estimates.

The composite score is a weighted blend of five normalised components.
When too many components are missing, "Insufficient data" is returned
rather than an arbitrary number.

Default weights (from product spec):
    ADTV (avg daily traded value) 25%
    Trading frequency             20%
    Bid-ask spread                20%
    Market depth                  20%
    Last-traded recency           15%
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Optional

DEFAULT_WEIGHTS: Dict[str, float] = {
    "adtv": 0.25,
    "frequency": 0.20,
    "spread": 0.20,
    "depth": 0.20,
    "recency": 0.15,
}

CLASSIFICATIONS = [
    (75, "High liquidity"),
    (50, "Moderate liquidity"),
    (25, "Low liquidity"),
    (0, "Very low liquidity"),
]


@dataclass
class LiquidityInputs:
    """Raw per-instrument market-activity inputs (all optional)."""

    avg_daily_traded_value: Optional[float] = None  # currency
    trading_days: Optional[int] = None              # days traded in window
    window_days: Optional[int] = None               # total days in window
    bid_ask_spread_bps: Optional[float] = None      # spread in basis points
    market_depth_value: Optional[float] = None      # top-of-book depth, currency
    last_traded_date: Optional[date] = None
    as_of_date: Optional[date] = None
    # category-specific normalisation anchors
    adtv_reference: float = 50_000_000.0            # ADTV mapped to ~full score
    depth_reference: float = 10_000_000.0


@dataclass
class LiquidityScore:
    score: Optional[float]
    classification: str
    components: Dict[str, Optional[float]] = field(default_factory=dict)
    missing: list = field(default_factory=list)
    methodology: str = (
        "Weighted blend of ADTV (25%), trading frequency (20%), bid-ask "
        "spread (20%), market depth (20%), recency (15%); each component "
        "normalised to 0-100. Historical-estimate only; not a guarantee."
    )


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def _log_normalise(value: float, reference: float) -> float:
    """Map a positive value to 0-100 using a log scale vs a reference."""
    import math

    if value <= 0:
        return 0.0
    ratio = value / reference
    # score 100 at ratio>=1, ~50 at ratio=0.1, 0 near ratio=0.01
    return _clamp(50.0 * (2.0 + math.log10(ratio)))


def _spread_score(spread_bps: float) -> float:
    # 0 bps -> 100, 100 bps -> ~0 (linear, clamped)
    return _clamp(100.0 - spread_bps)


def _recency_score(last_traded: date, as_of: date) -> float:
    days = (as_of - last_traded).days
    if days <= 0:
        return 100.0
    # 0 days ->100, 30 days ->~0
    return _clamp(100.0 - (days / 30.0) * 100.0)


def liquidity_score(
    inputs: LiquidityInputs,
    weights: Optional[Dict[str, float]] = None,
    min_components: int = 3,
) -> LiquidityScore:
    """Compute the composite liquidity score with component transparency."""
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    comps: Dict[str, Optional[float]] = {}
    missing = []

    if inputs.avg_daily_traded_value is not None:
        comps["adtv"] = _log_normalise(inputs.avg_daily_traded_value, inputs.adtv_reference)
    else:
        comps["adtv"] = None
        missing.append("adtv")

    if inputs.trading_days is not None and inputs.window_days:
        comps["frequency"] = _clamp(100.0 * inputs.trading_days / inputs.window_days)
    else:
        comps["frequency"] = None
        missing.append("frequency")

    if inputs.bid_ask_spread_bps is not None:
        comps["spread"] = _spread_score(inputs.bid_ask_spread_bps)
    else:
        comps["spread"] = None
        missing.append("spread")

    if inputs.market_depth_value is not None:
        comps["depth"] = _log_normalise(inputs.market_depth_value, inputs.depth_reference)
    else:
        comps["depth"] = None
        missing.append("depth")

    if inputs.last_traded_date is not None and inputs.as_of_date is not None:
        comps["recency"] = _recency_score(inputs.last_traded_date, inputs.as_of_date)
    else:
        comps["recency"] = None
        missing.append("recency")

    available = {k: v for k, v in comps.items() if v is not None}
    if len(available) < min_components:
        return LiquidityScore(
            score=None,
            classification="Insufficient data",
            components=comps,
            missing=missing,
        )

    # renormalise weights over available components
    total_w = sum(w[k] for k in available)
    score = sum(available[k] * w[k] for k in available) / total_w
    score = round(_clamp(score), 2)

    classification = "Very low liquidity"
    for threshold, label in CLASSIFICATIONS:
        if score >= threshold:
            classification = label
            break

    return LiquidityScore(
        score=score,
        classification=classification,
        components=comps,
        missing=missing,
    )


def estimated_liquidation_days(
    holding_market_value: float,
    avg_daily_traded_value: Optional[float],
    participation_rate: float = 0.10,
) -> Optional[float]:
    """Historical-volume-based estimate of days to liquidate a holding.

    days = market_value / (ADTV * participation_rate)
    Returns None when ADTV is unavailable or zero (insufficient data).
    """
    if not avg_daily_traded_value or avg_daily_traded_value <= 0:
        return None
    if participation_rate <= 0:
        raise ValueError("participation_rate must be positive")
    return holding_market_value / (avg_daily_traded_value * participation_rate)


def indicative_liquidation_cost(
    holding_market_value: float,
    bid_ask_spread_bps: Optional[float],
) -> Optional[float]:
    """Indicative cost of crossing half the bid-ask spread on exit."""
    if bid_ask_spread_bps is None:
        return None
    return holding_market_value * (bid_ask_spread_bps / 10_000.0) / 2.0

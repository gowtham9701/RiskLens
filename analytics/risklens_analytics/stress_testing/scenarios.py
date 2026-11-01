"""Portfolio stress-testing scenario engine.

Applies rate shifts, spread widening, downgrades, default/recovery and
volume-drop scenarios to a set of positions and reports the estimated
mark-to-market impact. Market-value stress losses are explicitly NOT
realised losses if instruments are held to maturity and all contractual
payments occur.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class StressPosition:
    instrument_id: str
    market_value: float
    modified_duration: float
    convexity: float = 0.0
    issuer_id: str = ""
    is_corporate: bool = False
    avg_daily_traded_value: Optional[float] = None


@dataclass
class ScenarioResult:
    name: str
    description: str
    pnl: float
    pnl_pct: float
    details: Dict[str, float] = field(default_factory=dict)
    disclaimer: str = (
        "Estimated mark-to-market impact only. Not a realised loss if held "
        "to maturity with all contractual payments received."
    )


def _rate_pnl(positions: List[StressPosition], dy: float) -> float:
    total = 0.0
    for p in positions:
        pct = -p.modified_duration * dy + 0.5 * p.convexity * dy ** 2
        total += pct * p.market_value
    return total


def _spread_pnl(positions: List[StressPosition], dspread: float) -> float:
    total = 0.0
    for p in positions:
        if not p.is_corporate:
            continue
        pct = -p.modified_duration * dspread + 0.5 * p.convexity * dspread ** 2
        total += pct * p.market_value
    return total


def run_stress_test(
    positions: List[StressPosition],
    downgrade_issuer: Optional[str] = None,
    downgrade_haircut: float = 0.03,
    default_issuer: Optional[str] = None,
    recovery_rate: float = 0.40,
    liquidate_fraction: float = 0.25,
    liquidation_spread_bps: float = 50.0,
) -> List[ScenarioResult]:
    """Run the standard scenario suite and return per-scenario results."""
    total_mv = sum(p.market_value for p in positions) or 1.0
    results: List[ScenarioResult] = []

    rate_scenarios = [
        ("Rates +50bps", 0.0050),
        ("Rates +100bps", 0.0100),
        ("Rates -50bps", -0.0050),
        ("Rates -100bps", -0.0100),
    ]
    for name, dy in rate_scenarios:
        pnl = _rate_pnl(positions, dy)
        results.append(ScenarioResult(name, f"Parallel yield shift {dy:+.2%}", pnl, pnl / total_mv))

    for name, ds in [("Spreads +50bps", 0.0050), ("Spreads +100bps", 0.0100)]:
        pnl = _spread_pnl(positions, ds)
        results.append(
            ScenarioResult(name, f"Corporate spread widening {ds:+.2%}", pnl, pnl / total_mv)
        )

    # combined rate + spread
    combined = _rate_pnl(positions, 0.0100) + _spread_pnl(positions, 0.0050)
    results.append(
        ScenarioResult("Rates +100bps & Spreads +50bps", "Combined shock", combined, combined / total_mv)
    )

    # downgrade of one issuer (price haircut proxy)
    if downgrade_issuer:
        exposure = sum(p.market_value for p in positions if p.issuer_id == downgrade_issuer)
        pnl = -exposure * downgrade_haircut
        results.append(
            ScenarioResult(
                f"Downgrade: {downgrade_issuer}",
                f"Single-issuer downgrade, {downgrade_haircut:.0%} price haircut",
                pnl,
                pnl / total_mv,
                details={"issuer_exposure": exposure},
            )
        )

    # default of one issuer with recovery
    if default_issuer:
        exposure = sum(p.market_value for p in positions if p.issuer_id == default_issuer)
        pnl = -exposure * (1.0 - recovery_rate)
        results.append(
            ScenarioResult(
                f"Default: {default_issuer}",
                f"Issuer default, recovery rate {recovery_rate:.0%}",
                pnl,
                pnl / total_mv,
                details={"issuer_exposure": exposure, "recovery_rate": recovery_rate},
            )
        )

    # trading volume drops 50% -> liquidity cost proxy via wider effective spread
    vol_pnl = -total_mv * (liquidation_spread_bps / 10_000.0)
    results.append(
        ScenarioResult(
            "Trading volume -50%",
            "Liquidity deterioration; indicative exit-cost impact",
            vol_pnl,
            vol_pnl / total_mv,
        )
    )

    # forced liquidation of a fraction at half-spread cost
    liq_cost = -total_mv * liquidate_fraction * (liquidation_spread_bps / 10_000.0) / 2.0
    results.append(
        ScenarioResult(
            f"Liquidate {liquidate_fraction:.0%} of portfolio",
            "Forced partial liquidation exit cost",
            liq_cost,
            liq_cost / total_mv,
        )
    )

    return results

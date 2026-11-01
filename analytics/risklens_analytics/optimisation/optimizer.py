"""SciPy-constrained fixed-income portfolio optimiser.

Optimises allocation weights across a set of eligible instruments to
maximise yield/income or minimise duration, subject to user-defined
constraints (credit, liquidity, duration, sector/issuer caps, ticket
size, instrument count). Never silently relaxes constraints: if no
feasible solution exists, it reports the conflicting constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import numpy as np
from scipy.optimize import LinearConstraint, minimize


class Objective(str, Enum):
    MAX_YIELD = "max_yield"
    MAX_INCOME = "max_income"
    MIN_DURATION = "min_duration"
    MAX_LIQUIDITY = "max_liquidity"


@dataclass
class Candidate:
    instrument_id: str
    issuer_id: str
    sector: str
    category: str
    ytm: float                 # decimal
    coupon_rate: float         # decimal
    modified_duration: float
    maturity_years: float
    liquidity_score: Optional[float]   # 0-100 or None
    rating_rank: int           # 1 = best (AAA/Sovereign). Higher = worse.
    is_government: bool = False


@dataclass
class Constraints:
    max_issuer_weight: float = 0.25
    max_sector_weight: float = 0.40
    min_government_weight: float = 0.0
    max_low_rated_weight: float = 1.0      # weight in rating_rank > low_rated_threshold
    low_rated_threshold: int = 4
    min_liquidity_weight: float = 0.0      # min weight in instruments scoring >= liquidity_floor
    liquidity_floor: float = 50.0
    max_duration: Optional[float] = None
    max_maturity_years: Optional[float] = None
    min_weight_per_instrument: float = 0.0   # ticket size as weight
    max_weight_per_instrument: float = 1.0
    min_instruments: int = 1
    max_instruments: Optional[int] = None


@dataclass
class OptimisationResult:
    feasible: bool
    objective: str
    weights: Dict[str, float] = field(default_factory=dict)
    expected_yield: float = 0.0
    expected_duration: float = 0.0
    message: str = ""
    infeasible_reasons: List[str] = field(default_factory=list)


def _check_feasibility(candidates: List[Candidate], c: Constraints) -> List[str]:
    """Pre-screen obviously conflicting constraints."""
    reasons: List[str] = []
    n = len(candidates)
    if n == 0:
        reasons.append("No eligible instruments after filtering.")
        return reasons

    # Can weights sum to 1 given per-instrument cap and min count?
    if c.max_weight_per_instrument * n < 1.0 - 1e-9:
        reasons.append(
            f"max_weight_per_instrument={c.max_weight_per_instrument} across "
            f"{n} instruments cannot sum to 100%."
        )
    if c.min_weight_per_instrument * c.min_instruments > 1.0 + 1e-9:
        reasons.append(
            "min_weight_per_instrument * min_instruments exceeds 100%."
        )
    # Government minimum achievable?
    gov_cap = sum(c.max_weight_per_instrument for cd in candidates if cd.is_government)
    if c.min_government_weight > gov_cap + 1e-9:
        reasons.append(
            f"min_government_weight={c.min_government_weight} unreachable; "
            f"government capacity only {gov_cap:.2f}."
        )
    # Liquidity minimum achievable?
    liq_cap = sum(
        c.max_weight_per_instrument
        for cd in candidates
        if (cd.liquidity_score or 0) >= c.liquidity_floor
    )
    if c.min_liquidity_weight > liq_cap + 1e-9:
        reasons.append(
            f"min_liquidity_weight={c.min_liquidity_weight} unreachable; "
            f"liquid capacity only {liq_cap:.2f}."
        )
    # Issuer cap vs count: enough distinct issuers?
    distinct_issuer_cap = {}
    for cd in candidates:
        distinct_issuer_cap[cd.issuer_id] = distinct_issuer_cap.get(cd.issuer_id, 0.0) + c.max_weight_per_instrument
    if sum(min(v, c.max_issuer_weight) for v in distinct_issuer_cap.values()) < 1.0 - 1e-9:
        reasons.append("Issuer concentration cap prevents weights summing to 100%.")
    return reasons


def optimise_portfolio(
    candidates: List[Candidate],
    constraints: Constraints,
    objective: Objective | str = Objective.MAX_YIELD,
    target_yield: Optional[float] = None,
) -> OptimisationResult:
    """Run the constrained optimisation and return allocation weights."""
    obj = Objective(objective) if not isinstance(objective, Objective) else objective

    # Hard eligibility filters (never relaxed)
    eligible = [
        c for c in candidates
        if (constraints.max_maturity_years is None or c.maturity_years <= constraints.max_maturity_years + 1e-9)
    ]

    reasons = _check_feasibility(eligible, constraints)
    if reasons:
        return OptimisationResult(
            feasible=False,
            objective=obj.value,
            message="No feasible portfolio for the given constraints.",
            infeasible_reasons=reasons,
        )

    n = len(eligible)
    ids = [c.instrument_id for c in eligible]
    ytm = np.array([c.ytm for c in eligible])
    dur = np.array([c.modified_duration for c in eligible])
    is_gov = np.array([1.0 if c.is_government else 0.0 for c in eligible])
    is_liquid = np.array(
        [1.0 if (c.liquidity_score or 0) >= constraints.liquidity_floor else 0.0 for c in eligible]
    )
    is_low_rated = np.array(
        [1.0 if c.rating_rank > constraints.low_rated_threshold else 0.0 for c in eligible]
    )

    # Objective (minimised)
    if obj in (Objective.MAX_YIELD, Objective.MAX_INCOME):
        def fun(w):
            return -float(ytm @ w)
        jac = lambda w: -ytm
    elif obj is Objective.MIN_DURATION:
        def fun(w):
            return float(dur @ w)
        jac = lambda w: dur
    elif obj is Objective.MAX_LIQUIDITY:
        liq = np.array([(c.liquidity_score or 0.0) for c in eligible])
        def fun(w):
            return -float(liq @ w)
        jac = lambda w: -liq
    else:  # pragma: no cover
        raise ValueError(obj)

    # Linear constraints
    lin: List[LinearConstraint] = []
    # weights sum to 1
    lin.append(LinearConstraint(np.ones(n), 1.0, 1.0))
    # government minimum
    if constraints.min_government_weight > 0:
        lin.append(LinearConstraint(is_gov, constraints.min_government_weight, np.inf))
    # liquidity minimum
    if constraints.min_liquidity_weight > 0:
        lin.append(LinearConstraint(is_liquid, constraints.min_liquidity_weight, np.inf))
    # low-rated maximum
    if constraints.max_low_rated_weight < 1.0:
        lin.append(LinearConstraint(is_low_rated, -np.inf, constraints.max_low_rated_weight))
    # duration cap
    if constraints.max_duration is not None:
        lin.append(LinearConstraint(dur, -np.inf, constraints.max_duration))
    # target yield (for min-duration style problems)
    if target_yield is not None:
        lin.append(LinearConstraint(ytm, target_yield, np.inf))
    # issuer caps
    issuers = sorted({c.issuer_id for c in eligible})
    for iss in issuers:
        row = np.array([1.0 if c.issuer_id == iss else 0.0 for c in eligible])
        lin.append(LinearConstraint(row, -np.inf, constraints.max_issuer_weight))
    # sector caps
    sectors = sorted({c.sector for c in eligible})
    for sec in sectors:
        row = np.array([1.0 if c.sector == sec else 0.0 for c in eligible])
        lin.append(LinearConstraint(row, -np.inf, constraints.max_sector_weight))

    bounds = [(0.0, constraints.max_weight_per_instrument) for _ in range(n)]
    x0 = np.full(n, 1.0 / n)

    res = minimize(
        fun, x0, jac=jac, method="SLSQP", bounds=bounds,
        constraints=lin, options={"maxiter": 500, "ftol": 1e-9},
    )

    if not res.success:
        return OptimisationResult(
            feasible=False,
            objective=obj.value,
            message=f"Optimiser could not satisfy constraints: {res.message}",
            infeasible_reasons=[res.message],
        )

    w = np.clip(res.x, 0.0, None)
    w = w / w.sum()
    # drop dust below ticket size
    weights = {
        ids[i]: float(w[i])
        for i in range(n)
        if w[i] >= max(constraints.min_weight_per_instrument, 1e-4)
    }
    if weights:
        s = sum(weights.values())
        weights = {k: v / s for k, v in weights.items()}

    exp_yield = float(sum(ytm[ids.index(k)] * v for k, v in weights.items()))
    exp_dur = float(sum(dur[ids.index(k)] * v for k, v in weights.items()))

    return OptimisationResult(
        feasible=True,
        objective=obj.value,
        weights=weights,
        expected_yield=exp_yield,
        expected_duration=exp_dur,
        message="Optimisation succeeded.",
    )

# RiskLens — Financial Methodology

> All inputs in the bundled dataset are **simulated**. The methods below are
> standard fixed-income techniques; outputs are indicative estimates, never
> guaranteed returns.

## 1. Day-count conventions
Implemented in `analytics/risklens_analytics/daycount`: ACT/365F, ACT/360,
ACT/ACT (ISDA), 30/360 (US bond basis), 30E/360 (Eurobond). The accrual year
fraction drives both accrued interest and discounting.

## 2. Cash-flow generation
Coupon dates are generated backwards from maturity at the stated frequency
(1/2/4/12 per year). The final flow carries coupon + redemption. Zero-coupon
instruments (T-Bills) produce a single redemption flow. Only flows strictly
after the settlement date are returned.

## 3. Pricing & yield
- **Present value**: each flow discounted at `(1 + y/m)^(t·m)` where `m` is
  the compounding frequency and `t` the day-count year fraction.
- **Clean price** = dirty price − accrued interest.
- **YTM/YTC/YTP**: solved with Brent's method (`scipy.optimize.brentq`) so the
  model dirty price equals the observed dirty price. YTC/YTP reprice to the
  call/put date and price.
- **Zero-coupon yield**: `m·((F/P)^(1/(t·m)) − 1)`.
- **Current yield**: annual coupon ÷ clean price.

Theoretical prices (from yield) are kept separate from observed market prices
(stored in `market_prices`). Instrument-specific handling:
- **FDs** are not exchange-traded → yield = contracted deposit rate; value
  carried at principal; no secondary liquidity.
- **Debt mutual funds** use indicative fund-level YTM/duration; bond YTM
  formulas are **not** applied to them.

## 4. Risk metrics
- **Macaulay duration**: PV-weighted average time to cash flows.
- **Modified duration** = Macaulay ÷ (1 + y/m).
- **Convexity**: second-order sensitivity, `Σ t(t+1/m)·PV / (P·(1+y/m)²)`.
- **DV01**: price change for a 1 bp yield move (central difference).
- **Effective duration**: symmetric re-pricing bump (for optionality).
- First + second order estimate: `ΔP ≈ (−ModDur·Δy + ½·Convexity·Δy²)·P`.

Validated against closed-form benchmarks in `analytics/tests` (par bond prices
to 100; zero-coupon Macaulay duration = maturity; DV01 ≈ ModDur·P·1bp; etc.).

## 5. Portfolio aggregation
Portfolio YTM is the **internal rate of return of the aggregated contractual
cash flows** against total market value — *not* a naive average of individual
YTMs (`portfolio/core.py::portfolio_ytm`). Weighted duration and DV01 are
market-value-weighted / summed respectively. XIRR provides money-weighted
return for dated flows.

**Assumptions/limitations**: contractual flows only (no default/prepayment in
the base case); intermediate coupons assumed reinvested at the solved IRR
(standard IRR assumption); FDs/MFs contribute their own flow streams.

## 6. Liquidity score (0–100)
Transparent weighted blend (`liquidity/core.py`):

| Component | Weight | Normalisation |
|-----------|-------:|---------------|
| Avg daily traded value | 25% | log scale vs category reference |
| Trading frequency | 20% | traded days / window days |
| Bid-ask spread | 20% | 100 − spread(bps), clamped |
| Market depth | 20% | log scale vs reference |
| Last-traded recency | 15% | linear decay over 30 days |

Weights are renormalised over available components. If fewer than 3 components
are present, the result is **"Insufficient data"** (no arbitrary score).
Estimated liquidation days = `market value / (ADTV × participation)` with a
configurable participation rate (default 10%). This is a historical-volume
estimate, **not** a guaranteed execution time.

## 7. Portfolio optimiser
SciPy SLSQP over eligible instruments (`optimisation/optimizer.py`). Objectives:
maximise yield/income/liquidity, or minimise duration (optionally subject to a
target yield). Hard linear constraints: weights sum to 100%, per-instrument
ticket caps, issuer caps, sector caps, government minimum, low-rated maximum,
liquidity minimum, duration/maturity caps. A pre-screen detects obviously
conflicting constraints. **Safety/eligibility constraints are never silently
relaxed**; infeasible requests return the conflicting reasons.

## 8. Stress testing
Scenarios (`stress_testing/scenarios.py`): parallel rate shifts ±50/±100 bps,
corporate spread widening +50/+100 bps, combined rate+spread, single-issuer
downgrade (price haircut proxy), single-issuer default with explicit recovery
rate, trading-volume drop, and forced partial liquidation at half-spread cost.
Rate/spread P&L uses the duration + convexity approximation. **Market-value
stress losses are not realised losses** if the instrument is held to maturity
and all contractual payments occur — this disclaimer is returned with results.

## 9. Credit
Agency symbols (CRISIL/ICRA/CARE/India Ratings) are normalised to an ordinal
rank and grade bucket (`credit_risk`). Ratings are **not** converted into
guaranteed default probabilities. Rating history and effective dates are
preserved; current ratings never inferred from stale sources.

## 10. Precision
All monetary and yield fields are stored as SQL `NUMERIC`/`DECIMAL`
(`Numeric(24,4)` / `Numeric(24,8)`), never binary float.

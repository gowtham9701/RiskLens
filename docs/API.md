# RiskLens API Contract (v1)

Base URL: `${NEXT_PUBLIC_API_URL}` (default `http://localhost:8000`).
All responses are JSON. Auth uses a Bearer JWT in `Authorization: Bearer <token>`.
Monetary/yield fields are returned as numbers; the backend stores them as
NUMERIC/DECIMAL. Every simulated record carries `data_status: "SIMULATED"`.

## Auth
- `POST /auth/register` body `{email, password, full_name}` -> `{access_token, token_type, user:{id,email,full_name}}`
- `POST /auth/login` body `{email, password}` -> `{access_token, token_type, user}`
- `GET /auth/me` -> `{id, email, full_name}`

A demo account is seeded: `demo@risklens.sim` / `demo1234`.

## Instruments
- `GET /instruments?category=&search=&page=1&page_size=25` ->
  `{items:[InstrumentSummary], total, page, page_size}`
- `GET /instruments/{id}` -> `InstrumentDetail` (includes computed `analytics`)
- `GET /instruments/{id}/cashflows` -> `{items:[{pay_date, amount, kind}]}`
- `GET /instruments/{id}/prices` -> `{items:[{price_date, clean_price, source}]}`
- `GET /instruments/{id}/ratings` -> `{current:{...}, history:[...]}`
- `GET /instruments/{id}/liquidity` -> `LiquidityDetail`
- `GET /instruments/{id}/news` -> `{items:[NewsItem]}`

`InstrumentSummary`: `{id, isin, name, category, issuer_name, sector,
coupon_rate, maturity_date, clean_price, ytm, modified_duration, rating,
rating_agency, liquidity_score, liquidity_class, is_government, data_status}`

`InstrumentDetail` adds: `{issue_date, face_value, coupon_frequency,
day_count, callable, puttable, secured, seniority, accrued_interest,
dirty_price, current_yield, ytc, convexity, dv01, analytics:{...}}`

## Calculations (stateless)
- `POST /calculations/bond-price` body `{issue_date, maturity_date, coupon_rate, frequency, yield, settlement_date, face_value?, day_count?}` -> `{clean_price, dirty_price, accrued_interest}`
- `POST /calculations/yield` body `{...clean_price...}` -> `{ytm, current_yield}`
- `POST /calculations/duration` -> `{macaulay, modified, convexity, dv01}`
- `POST /calculations/stress-test` body `{positions:[...]} ` -> `{scenarios:[ScenarioResult]}`

## Portfolios
- `GET /portfolios` -> `{items:[PortfolioSummary]}`
- `POST /portfolios` body `{name, description?}` -> `PortfolioSummary`
- `GET /portfolios/{id}` -> `PortfolioDetail` (holdings + per-holding analytics)
- `POST /portfolios/{id}/holdings` body `{instrument_id, quantity, buy_price, buy_date}` -> holding
- `DELETE /portfolios/{id}/holdings/{holding_id}`
- `GET /portfolios/{id}/dashboard` -> `DashboardKPIs` (value, gain/loss, weighted yield, income, duration, dv01, allocations, maturity ladder)
- `GET /portfolios/{id}/risk` -> `{duration, convexity, dv01, rating_distribution, issuer_concentration, stress:[ScenarioResult]}`
- `GET /portfolios/{id}/cashflows` -> `{calendar:[{month, coupon, principal, total}], upcoming:[...]}`
- `GET /portfolios/{id}/liquidity` -> `{buckets:{high,moderate,low,insufficient}, est_liquidation_days, illiquid_holdings:[...]}`

## Portfolio Builder (optimiser)
- `POST /portfolio-builder/generate` body:
  `{amount, objective:"max_yield|max_income|min_duration|max_liquidity",
    constraints:{max_issuer_weight, max_sector_weight, min_government_weight,
      max_low_rated_weight, min_liquidity_weight, max_duration, max_maturity_years,
      max_weight_per_instrument, min_instruments}, universe:["G-Sec","T-Bill",...]}`
  -> `{feasible, objective, expected_yield, expected_duration,
       allocations:[{instrument_id, name, issuer, category, weight, amount,
         ytm, modified_duration, rating, liquidity_class, rationale}],
       infeasible_reasons:[...], methodology:"..."}`

## Alerts & Reports
- `GET /alerts?portfolio_id=` -> `{items:[Alert]}`
- `PATCH /alerts/{id}` body `{status}` -> Alert
- `GET /reports/portfolio/{id}?format=xlsx|pdf` -> file download

## Shared shapes
`ScenarioResult`: `{name, description, pnl, pnl_pct, disclaimer}`
`NewsItem`: `{id, headline, source, published_at, category, summary, risk_impact, relevance, issuer_name, data_status}`
`Alert`: `{id, trigger, severity, instrument_id, portfolio_id, exposure, message, created_at, status, source}`

## Conventions
- Pagination via `page`/`page_size`; list responses include `total`.
- Errors: `{detail: "message"}` with appropriate HTTP status.
- Disclaimers: liquidity/stress/yield responses include methodology/disclaimer text.

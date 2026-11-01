# Data schemas

The simulated dataset (`data/sample/risklens_sample.json`) and all ingestion
adapters conform to the canonical shapes consumed by the backend seeder and
services.

## risklens_sample.json
```
{
  "_meta":   { "status": "SIMULATED", "as_of": "YYYY-MM-DD", "counts": {...} },
  "issuers": [ { id, name, sector, is_government } ],
  "instruments": [ {
      id, isin, name, category, issuer_id, sector, currency, is_government,
      issue_date, maturity_date, face_value, min_investment, coupon_rate,
      coupon_frequency, day_count, redemption_value, callable, puttable,
      secured, seniority, listing_exchange, clean_price,
      call_date?, call_price?, cumulative?, fund_kind?, nav?,
      indicative_ytm?, indicative_duration?
  } ],
  "credit_ratings":    [ { instrument_id?, issuer_id, agency, symbol, rating_date, outlook, action, previous_symbol? } ],
  "rating_history":    [ { instrument_id?, issuer_id, agency, symbol, rating_date, action } ],
  "market_prices":     [ { instrument_id, price_date, clean_price, source } ],
  "liquidity_metrics": [ { instrument_id, avg_daily_traded_value, trading_days, window_days,
                           bid_ask_spread_bps, market_depth_value, last_traded_date, as_of_date } ],
  "news":              [ { headline, issuer_id, instrument_ids, category, published_at,
                           source, summary, risk_impact, relevance } ],
  "portfolios":        [ { name, description, holdings: [ { instrument_id, quantity, buy_price, buy_date } ] } ]
}
```

## Categories
`G-Sec`, `T-Bill`, `SDL`, `NCD` (corporate bonds/NCDs), `FD` (bank deposits),
`Debt MF` (debt mutual funds).

## Day-count codes
`ACT/365F`, `ACT/360`, `ACT/ACT`, `30/360`, `30E/360`.

Every record carries `data_status = "SIMULATED"`. Validators for these shapes
live in `data/validation/validators.py`.

# RiskLens — Architecture

## Overview
RiskLens is a modular monorepo with a clean separation between the financial
calculation engine, the application backend, data ingestion, and the UI.

```
┌──────────────┐     HTTPS/JSON      ┌──────────────────────────┐
│  frontend    │ ───────────────────▶│  backend (FastAPI)       │
│  Next.js/TS  │ ◀─────────────────── │  JWT auth · REST · ORM   │
└──────────────┘                     └─────────┬────────────────┘
                                               │ imports
                                     ┌─────────▼────────────────┐
                                     │  analytics engine        │
                                     │  (pure Python pkg)       │
                                     │  pricing·yield·risk·     │
                                     │  liquidity·optimiser·    │
                                     │  stress testing          │
                                     └─────────┬────────────────┘
                                               │ SQLAlchemy
                                     ┌─────────▼────────────────┐
                                     │  PostgreSQL (29 tables)  │
                                     │  NUMERIC money/yield     │
                                     └──────────────────────────┘
          ▲
          │ seed / CSV import / provider adapters (simulated)
   ┌──────┴───────┐
   │ data/sample  │  risklens_sample.json (31 simulated instruments)
   └──────────────┘
```

## Components

### analytics/ (`risklens_analytics`)
A standalone, installable Python package with **no web or DB dependencies**.
This is the single source of truth for all financial maths and is independently
unit-tested against closed-form benchmarks. Submodules: `daycount`, `cashflows`,
`pricing`, `yield_calc`, `duration`, `convexity`, `dv01`, `credit_risk`,
`liquidity`, `portfolio`, `optimisation`, `stress_testing`.

### backend/ (`app`)
- `core/` — config (env-driven) and security (bcrypt + JWT).
- `db/` — SQLAlchemy engine/session; Postgres with automatic SQLite fallback.
- `models/` — 29 normalised tables with created/updated timestamps,
  soft-delete where relevant, FKs, unique constraints and indexes.
- `schemas/` — Pydantic request/response models.
- `services/` — the bridge layer: `analytics_service` (DB record → engine),
  `portfolio_service` (positions, dashboard, risk, cash flows, liquidity),
  `optimiser_service` (eligibility + optimisation), `reporting_service`
  (OpenPyXL/ReportLab).
- `api/routes/` — auth, instruments, calculations, portfolios, builder,
  monitoring (alerts/news/reports/data-quality).
- `seed.py` — loads the simulated dataset, runs data-quality validations,
  creates the demo user, sample portfolios and alerts.

### data/
Provider adapters are modelled as `data_sources` rows (all `simulated`). The
sample generator (`data/sample/generate.py`) produces a fully-labelled
synthetic dataset. A CSV-import path is modelled for manual ingestion.

### frontend/
Next.js 14 app-router UI with a typed API client, JWT auth context, dark
institutional theme, and resilient loading/empty/error states.

## Separation of concerns
- **Theoretical vs observed**: engine prices-from-yield are distinct from the
  `market_prices` feed; both are surfaced separately.
- **Provider independence**: swapping a data provider only touches ingestion
  adapters, never the financial calculations.
- **Graceful degradation**: missing order-book data still allows historical
  liquidity analysis; a news/LLM outage never blocks portfolio calculations.

## Security
- bcrypt password hashing; JWT bearer tokens.
- All portfolio routes are user-scoped (`user_id` ownership checks) — a user
  can never read another user's portfolio.
- Parameterised ORM queries (no string SQL) prevent injection.
- Secrets only in environment variables; `.env` is git-ignored.
- `audit_logs` and `data_exceptions` tables support traceability.

## Performance notes
The MVP computes analytics on demand. Hot paths (per-instrument price/rating/
liquidity lookups during portfolio aggregation) are the main candidates for
caching and query-batching; a Redis cache and background ingestion worker are
intentionally deferred until justified (see `docs/LIMITATIONS.md`).

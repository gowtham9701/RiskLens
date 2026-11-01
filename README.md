# RiskLens

**Fixed-Income Intelligence, Portfolio Optimisation & Risk Analytics Platform** (India-focused MVP).

> ⚠️ **All bundled data is SIMULATED.** RiskLens is an analytics and
> decision-support tool. It does **not** provide investment advice and does
> **not** guarantee returns, capital protection, liquidity or credit quality.
> Yields, liquidity scores and stress results are indicative estimates.

RiskLens helps individuals and professionals discover, value, construct,
optimise and monitor fixed-income portfolios (G-Secs, T-Bills, SDLs, NCDs,
Bank FDs and Debt Mutual Funds).

> 📄 A detailed project whitepaper is available at
> [`docs/RiskLens_Whitepaper.pdf`](docs/RiskLens_Whitepaper.pdf).

---

## 1. Business idea

India's fixed-income market is large, fast-growing and increasingly accessible
to retail investors (RBI Retail Direct, online bond platforms, debt mutual
funds). Yet the tools to **evaluate** these instruments remain fragmented,
spreadsheet-driven and skewed toward institutions. RiskLens is a single,
transparent intelligence layer that answers the question every bond investor
actually has: *"Is the extra yield worth the risk — and how do I build and
monitor a portfolio around it?"*

The product is positioned as **analytics and decision-support** (not a broker,
not an advisor): it ingests instrument, price, rating, liquidity and news data,
runs institutional-grade fixed-income maths, and presents clear, auditable risk
and income insights to two audiences — everyday investors and professionals.

## 2. Problem statement

Fixed-income investing in India is hard to do well because:

- **Yield ≠ safety.** A higher coupon often hides credit, liquidity or
  duration risk that retail tools never surface.
- **Fragmented data.** Prices, ratings (CRISIL/ICRA/CARE/India Ratings),
  secondary-market liquidity and issuer news live in separate silos.
- **Liquidity is opaque.** Investors confuse large issue size with the ability
  to actually sell; many bonds barely trade.
- **Wrong maths.** Consumer tools average individual bond YTMs (incorrect),
  apply bond formulas to FDs/mutual funds, or ignore duration/convexity/DV01.
- **No portfolio view.** Little support for constraint-based construction,
  cash-flow laddering, stress testing or downgrade-impact analysis.
- **Reactive monitoring.** Investors learn about downgrades or liquidity
  deterioration too late.

## 3. Solution provided by this project

RiskLens delivers an integrated platform built on a **correct, tested financial
engine** and a transparent, "never fabricate data" philosophy:

| Problem | RiskLens solution |
|---------|-------------------|
| Yield ≠ safety | Risk-adjusted view: duration, convexity, DV01, credit & liquidity scoring beside every yield |
| Fragmented data | One model unifying instruments, prices, ratings, liquidity, news & issuers |
| Opaque liquidity | Transparent 0–100 liquidity score (5 weighted components) + estimated liquidation days/cost |
| Wrong maths | Cash-flow-weighted portfolio YTM (IRR), instrument-specific methods for FDs & funds |
| No portfolio view | SciPy constrained optimiser, maturity ladder, stress testing, cash-flow calendar |
| Reactive monitoring | Alerts for downgrades, negative outlooks, liquidity drops, concentration & maturities |

**Core principle:** maximise income/yield *subject to transparent risk
constraints* — and always disclose data sources, timestamps, assumptions and
limitations. Nothing is presented as a guarantee.

## 4. Who it is for

- **Individual investors** — budget, horizon and income preferences in; a clear
  proposed portfolio, expected income, maturity calendar and alerts out.
- **Investment professionals** — detailed valuation, portfolio analytics,
  rating migration, liquidity analytics, stress testing, data-quality console,
  multi-portfolio management and Excel/PDF reporting.

## 5. How it works (end to end)

```
            ┌─────────────────────────────────────────────────────────────┐
  Data  ──▶ │ Instruments · Prices · Ratings · Liquidity · News (adapters) │
            └───────────────┬─────────────────────────────────────────────┘
                            ▼
            ┌───────────────────────────────┐     ┌──────────────────────┐
            │ Analytics engine (Python)     │◀───▶│ PostgreSQL (29 tables │
            │ pricing·yield·duration·DV01·  │     │ NUMERIC precision)    │
            │ liquidity·optimiser·stress    │     └──────────────────────┘
            └───────────────┬───────────────┘
                            ▼
            ┌───────────────────────────────┐
            │ FastAPI backend (JWT, REST)   │
            └───────────────┬───────────────┘
                            ▼
            ┌───────────────────────────────┐
            │ Next.js UI: dashboard·explore·│
            │ builder·risk·liquidity·credit·│
            │ news·cash-flows·alerts·reports│
            └───────────────────────────────┘
```

A typical user journey:
1. **Register / log in** (or use the demo account).
2. **Explore instruments** — filter by category, see YTM, duration, rating and
   a liquidity score for each.
3. **Build a portfolio** — enter amount, objective and constraints (credit,
   liquidity, duration, issuer/sector caps); the optimiser returns a compliant
   allocation or explains why constraints conflict.
4. **Review the dashboard** — value, gain/loss, cash-flow-weighted yield,
   income, duration, DV01, allocations and a maturity ladder.
5. **Analyse risk** — stress tests (±rate/spread shifts, downgrade, default,
   liquidity), credit and liquidity breakdowns.
6. **Plan cash flows** — an income/maturity calendar.
7. **Monitor** — alerts on downgrades, negative outlooks and concentration.
8. **Report** — export portfolio Excel/PDF.

See the [end-to-end setup guide](#quick-start-local-no-docker) below and
[`docs/`](docs) for architecture, methodology, data-provider and deployment
details.

---

## Monorepo layout

```
RiskLens/
├── analytics/     # Pure-Python fixed-income engine (pricing, yield, risk,
│                  #   liquidity, optimisation, stress testing) + unit tests
├── backend/       # FastAPI + SQLAlchemy (29 tables) + JWT auth + reports
├── data/sample/   # Simulated dataset generator + risklens_sample.json
├── frontend/      # Next.js 14 + TypeScript + Tailwind UI
├── docs/          # API contract, architecture, financial methodology
├── docker-compose.yml
├── .env.example
└── README.md
```

## What works today

| Area | Status |
|------|--------|
| Bond pricing / YTM / YTC / YTP / zero-coupon / accrued | ✅ tested |
| Macaulay & modified duration, convexity, DV01 | ✅ tested |
| Cash-flow-weighted portfolio YTM (IRR), XIRR, weighted duration/DV01 | ✅ tested |
| Liquidity score (0–100, 5 weighted components) + liquidation estimates | ✅ tested |
| SciPy constrained optimiser (max yield/income/liquidity, min duration) | ✅ tested |
| Stress testing (rate/spread/downgrade/default/liquidity) | ✅ tested |
| FastAPI backend, JWT auth, user-scoped portfolios | ✅ tested |
| 29-table PostgreSQL schema (NUMERIC money/yield) | ✅ |
| 31 simulated instruments, prices, ratings, liquidity, news | ✅ |
| Excel + PDF reports | ✅ |
| Next.js dashboard, instruments, builder, risk, liquidity, alerts, reports | ✅ builds |

---

## Quick start (local, no Docker)

Prerequisites: Python 3.11+, Node 20+. A PostgreSQL URL is optional — the
backend falls back to SQLite automatically.

### 1. Backend + analytics engine

```bash
cd RiskLens
python3 -m venv .venv && source .venv/bin/activate
pip install -e ./analytics            # financial engine (editable)
pip install -r backend/requirements.txt

cp .env.example .env                   # set DATABASE_URL (Postgres) or leave for SQLite
python -m backend.app.seed             # creates tables + loads simulated data
uvicorn backend.app.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Demo login: **demo@risklens.sim / demo1234**

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local             # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                            # http://localhost:3000
```

### 3. Run the tests

```bash
# from repo root, venv active
pytest analytics/tests -q              # 30 financial-correctness tests
pytest backend/tests  -q               # 15 API integration tests (isolated SQLite)
```

---

## Quick start (Docker Compose)

Brings up Postgres, the backend (auto-seeds), and the frontend:

```bash
docker compose up --build
# frontend -> http://localhost:3000   backend -> http://localhost:8000/docs
```

To point the backend at an external Postgres (e.g. Neon) instead of the
bundled container, set `DATABASE_URL` in your shell or a root `.env` before
`docker compose up`.

---

## Configuration

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | Postgres URL (`postgresql://...`). Falls back to SQLite. | `sqlite:///./risklens.db` |
| `SECRET_KEY` | JWT signing secret | dev placeholder |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000` |
| `LLM_API_KEY` | Optional news-summarisation key (graceful fallback) | empty |
| `NEXT_PUBLIC_API_URL` | Frontend → backend base URL | `http://localhost:8000` |

Secrets live only in `.env` / `.env.local` (git-ignored). `.env.example`
documents every variable.

---

## Documentation

- [`docs/API.md`](docs/API.md) — REST API contract
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system design & data flow
- [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) — financial calculation methodology & assumptions
- [`docs/DATA_PROVIDERS.md`](docs/DATA_PROVIDERS.md) — provider adapters & integration status
- [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) — known limitations & outstanding work

## Legal

RiskLens must not be used as a substitute for professional investment advice.
Review applicable Indian securities, investment-advice, data-licensing,
privacy and consumer-protection requirements before any commercial use.

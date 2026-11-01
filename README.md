# RiskLens

**Fixed-Income Intelligence, Portfolio Optimisation & Risk Analytics Platform** (India-focused MVP).

> ⚠️ **All bundled data is SIMULATED.** RiskLens is an analytics and
> decision-support tool. It does **not** provide investment advice and does
> **not** guarantee returns, capital protection, liquidity or credit quality.
> Yields, liquidity scores and stress results are indicative estimates.

RiskLens helps individuals and professionals discover, value, construct,
optimise and monitor fixed-income portfolios (G-Secs, T-Bills, SDLs, NCDs,
Bank FDs and Debt Mutual Funds).

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

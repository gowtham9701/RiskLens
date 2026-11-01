# RiskLens — Known Limitations & Outstanding Work

RiskLens is a production-minded MVP. The core financial engine, backend, data
model, reporting and UI are implemented and tested. The items below are
explicitly out of scope for this build or require external agreements.

## Data
- **All bundled data is simulated.** No live market, rating, trade, order-book
  or news feed is connected. Real providers require licences/credentials (see
  `docs/DATA_PROVIDERS.md`).
- Order-book depth beyond top-of-book is modelled but not populated.
- Time-weighted return (TWR) requires a valuation history; only money-weighted
  (XIRR) and cash-flow-weighted YTM are fully wired in the MVP.

## Analytics
- QuantLib is **not** a runtime dependency; all maths is implemented in
  NumPy/SciPy so the engine runs anywhere. QuantLib can be added later for
  exotic schedules/calendars.
- Callable/puttable valuation uses yield-to-call/put and an effective-duration
  bump rather than a full option-adjusted (OAS) lattice model.
- Key-rate durations and non-parallel curve shocks are approximated via the
  parallel/duration framework; a full curve-bootstrapping module is future work.

## News / AI
- LLM summarisation is an optional, pluggable step; without `LLM_API_KEY` the
  stored (simulated) summaries are shown. Issuer/instrument linkage is wired via
  mapping tables.

## Performance
- Portfolio analytics are computed on demand. With a remote Postgres the
  per-instrument lookups add latency; query-batching and a Redis cache are the
  next optimisations. Background ingestion/scheduling (Celery/worker) is
  intentionally deferred until justified.

## Security / ops
- JWT refresh-token rotation and logout-token revocation are stubbed at the API
  contract level; the MVP issues access tokens only.
- Rate limiting and full audit-log population are modelled (tables + hooks) but
  not enforced on every endpoint.
- HTTPS/TLS termination is expected at the deployment layer (reverse proxy).

## Testing
- 30 analytics unit tests + 15 API integration tests pass. Frontend has a
  passing production build; automated end-to-end UI tests are future work.

## Regulatory
- Not reviewed for Indian securities / investment-advice / data-licensing /
  privacy compliance. Required before any commercial launch.

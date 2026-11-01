# RiskLens — Data Providers & Integration Status

RiskLens is built so that **financial calculations never depend on a specific
data provider**. Providers are integrated via adapters; the current build ships
with **simulated** adapters only. Each is represented by a row in the
`data_sources` table with `status = "simulated"`.

## Provider adapter model
```
data_sources (name, kind, status, description)
ingestion_runs (source_id, started_at, status, records, notes)
```
To connect a real provider: implement an adapter that writes into the canonical
tables (`market_prices`, `market_trades`, `order_book_snapshots`,
`credit_ratings`, `rating_history`, `news_articles`), set the matching
`data_sources.status` to `live`/`delayed`, and record each run in
`ingestion_runs`. No change to the analytics engine is required.

## Target sources (require licences / credentials — NOT bundled)

| Domain | Candidate sources | Status |
|--------|-------------------|--------|
| Market & government data | RBI, CCIL, FBIL, NSE, BSE | interface modelled, not connected |
| Credit ratings | CRISIL, ICRA, CARE, India Ratings | interface modelled, not connected |
| Issuer / regulatory filings | NSE/BSE filings, SEBI, RBI | interface modelled, not connected |
| Mutual-fund data | AMFI, permitted providers | interface modelled, not connected |
| Financial news | Licensed news APIs, exchange announcements | interface modelled, not connected |
| News summarisation | LLM API (`LLM_API_KEY`) | optional; graceful fallback |

## Integration rules (enforced by design)
- Use official APIs / licensed sources only; never bypass access controls or
  scrape prohibited content.
- Keep credentials in environment variables (`.env`), never in code.
- Store **publication time** and **retrieval time**; mark data real-time,
  delayed or end-of-day (`order_book_snapshots.feed_status`).
- Handle rate limits and retry transient failures; a provider outage must not
  break unrelated features.
- Always attribute the source and preserve provenance.
- Provide a manual **CSV import** path and a **synthetic-data mode** (default).

## News / LLM behaviour
When `LLM_API_KEY` is absent, news summaries fall back to the stored
(simulated) summary text. The system is designed so the LLM may summarise and
classify but must distinguish confirmed facts from interpretation and must not
invent ratings, figures or recommendations. The original article/source link is
always preserved.

## Important
Every bundled record is labelled `SIMULATED`. Do not mix synthetic and real
data without clear source/status indicators on each record.

# Interview preparation

## 60-second project explanation

“I built a learning-focused market analysis app with a FastAPI backend and Next.js dashboard. The backend can read a reproducible offline demo, a user CSV, or optional Yahoo Finance history. Pandas calculates common indicators; a small backtest compares a moving average crossover with buy-and-hold while charging configurable transaction costs and shifting signals to the next bar to avoid look-ahead. The dashboard surfaces a watchlist, portfolio, alerts, and chart. I chose simple JSON persistence to keep the local course project easy to run, and documented where that choice would need to change for concurrent or production use.”

## Questions to practice

### Why separate the API and dashboard?

It creates a clean boundary between data/analytics and presentation. FastAPI offers typed request validation and interactive API docs; Next.js handles the browser UI. The trade-off is that two processes and CORS configuration are needed in development.

### How do you avoid look-ahead bias?

The strategy derives exposure from the moving averages and shifts it by one trading bar before applying that day's return. A signal calculated using the current close cannot receive that same close-to-close return. A more realistic model would explicitly define order timing and fill price.

### What does RSI measure?

RSI scales smoothed average gains relative to smoothed average losses to a 0–100 range. It measures recent momentum under a chosen lookback. Thresholds such as 30 and 70 are conventions and can remain extreme during trends.

### How would you make the backtest more realistic?

Specify execution timing, model spread and slippage, include cash and position accounting, handle dividends and splits explicitly, use survivorship-safe universes, validate the strategy out of sample, and compare with suitable benchmarks. Track data provenance and missing bars.

### Why is the default data synthetic?

It makes the project runnable offline without accounts or keys. It is deterministic for demonstrations and explicitly labeled. Real analysis must select a documented public or licensed source.

### How would you scale persistence?

Replace local JSON files with a relational store such as PostgreSQL or SQLite, add migrations and transactions, separate user-owned records, and use a cache for provider responses. JSON is a deliberate local-demo trade-off, not a concurrent production store.

### How are errors handled?

The API validates request shapes and maps invalid symbols, periods, CSVs, and provider failures to HTTP errors. The UI reports when the API is unavailable. A production version would add structured error payloads, logs, retries, rate limits, and observability.

## Topics to be ready to explain

- pandas rolling windows, exponentially weighted calculations, and missing warm-up values;
- CAGR, annualized volatility, Sharpe ratio, and peak-to-trough drawdown;
- transaction costs in basis points and why turnover matters;
- the difference between a last available daily quote and a streaming live quote;
- CORS, API validation, JSON persistence trade-offs, and public provider limits;
- how you would test calculations, edge cases, and look-ahead bias.

## Be accurate about the project

This code is a strong discussion starter, not evidence of investment performance. Clearly call out synthetic demo mode, the provider's data limitations, and the simplified backtest assumptions.

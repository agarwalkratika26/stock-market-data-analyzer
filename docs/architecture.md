# Project architecture

## System view

```text
┌────────────────────────────── INPUT ──────────────────────────────┐
│ Ticker symbol · date range · provider · price data (OHLCV)       │
│ Sources: demo generator · CSV file · optional Yahoo Finance       │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────── DATA INGESTION ─────────────────────────┐
│ Select provider → fetch or load bars → validate required fields   │
│ Normalize dates/columns → sort chronologically → handle bad input │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ clean price series
                                 ▼
┌────────────────────────── PROCESSING ─────────────────────────────┐
│ Daily returns │ SMA / EMA │ Trend context │ Volatility / risk     │
│ RSI / MACD / Bollinger Bands │ Signals │ Strategy backtest        │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ calculated results
                 ┌───────────────┴────────────────┐
                 ▼                                ▼
┌─────────────────────────┐          ┌──────────────────────────────┐
│ FastAPI JSON API         │          │ Report-ready summary         │
│ history, indicators,     │          │ observations + assumptions   │
│ watchlist, portfolio,    │          │ source + range + limitations │
│ alerts, backtest         │          └──────────────┬───────────────┘
└────────────┬────────────┘                         │
             │                                      │
             ▼                                      ▼
┌────────────────────────── OUTPUT ──────────────────────────────────┐
│ Next.js dashboard: price chart · moving-average context            │
│ returns / portfolio summaries · strategy results · risk metrics    │
│ API consumers or a future export: final insights report            │
└────────────────────────────────────────────────────────────────────┘
```

## Inputs

- **Ticker symbol:** For example, `AAPL`. The API normalizes symbols to uppercase.
- **Date range:** A supported period such as `1mo`, `3mo`, `6mo`, `1y`, or `2y`.
- **Price data:** Dated OHLCV records from the synthetic demo generator, a symbol-named CSV, or optional Yahoo Finance history.
- **Analysis parameters:** Optional strategy windows, initial cash, and transaction costs for the backtest.

## Processing stages

1. **Fetch or load:** `backend/app/market_data.py` selects demo, CSV, or Yahoo Finance data and returns price bars.
2. **Clean and normalize:** CSV headers and dates are normalized, rows are sorted, and missing required CSV columns are rejected. Provider errors are returned by the API.
3. **Calculate daily returns:** Percentage changes are calculated from consecutive closes in the backtest calculation. An analysis report can reuse the same return series.
4. **Calculate moving averages:** `analytics.py` calculates SMA and EMA windows. The crossover backtest uses rolling fast and slow simple moving averages.
5. **Identify trend context:** Moving-average relationships and momentum indicators produce descriptive signal labels. Signals are summaries for research, not trade instructions.
6. **Calculate volatility and risk:** The backtest derives annualized return volatility, Sharpe ratio, and maximum drawdown from simulated returns and equity.
7. **Build presentation data:** API routes serialize price bars, indicators, watchlist and portfolio values, alerts, or backtest curves as JSON.
8. **Visualize and report:** The Next.js dashboard renders charts and summaries. A report should include data source, date range, parameters, observations, and limitations alongside any figures.

## Data flow explanation

The user selects a ticker and period in the dashboard. The browser requests the relevant FastAPI route, such as `GET /api/market/AAPL/history?period=6mo`. The route calls the market-data layer, which loads bars from the configured provider. For indicator requests, the returned frame goes through the analytics calculations before the API serializes the results. The dashboard uses that JSON to draw the price chart and show the watchlist, portfolio, or signal summaries.

For a strategy simulation, the browser sends ticker and parameters to `POST /api/backtest`. The backend loads the selected history, calculates the fast and slow averages, delays the position by one bar, applies transaction costs, and returns performance metrics plus the equity curve. The interface can then compare strategy equity against buy-and-hold.

Watchlist symbols, portfolio holdings, and alert definitions are stored in local JSON files for this single-user learning project. Market data and calculations are requested when the API is called rather than stored as a full historical database.

## Module and endpoint map

| Responsibility | Project location / route |
|---|---|
| Data source selection and CSV parsing | `backend/app/market_data.py` |
| Indicator and strategy calculations | `backend/app/analytics.py` |
| Request validation | `backend/app/schemas.py` |
| API endpoints | `backend/app/main.py` |
| Local demo state | `backend/app/data_store.py`, `backend/data/` |
| Dashboard and charts | `frontend/app/page.tsx`, `frontend/app/globals.css` |
| Price history | `GET /api/market/{symbol}/history` |
| Indicators and signal | `GET /api/market/{symbol}/indicators` |
| Strategy simulation | `POST /api/backtest` |
| Watchlist, portfolio, alerts | `/api/watchlist`, `/api/portfolio`, `/api/alerts` |

## Outputs

- **Stock price charts:** Historical closing prices over the chosen period.
- **Moving-average context:** Computed SMA/EMA values and trend-related signals.
- **Return analysis:** Historical period returns and strategy / benchmark performance.
- **Risk summary:** Backtest drawdown, volatility-related ratio, and other metrics.
- **Insights report:** A concise interpretation should state observations and assumptions, not present them as predictions. The current app shows results in API responses and dashboard panels; downloadable report export is a possible extension.

## Architecture boundary and limitations

The current app is a local educational implementation. Its synthetic data is fictional; CSV and public provider data have their own quality and availability limits. The quote endpoint attempts a public provider snapshot when configured but does not provide a guaranteed real-time exchange feed. Local JSON state is not intended for concurrent or multi-user production use. Authentication, a relational database, scheduled ingestion, monitoring, and report export can be added as later architecture stages.

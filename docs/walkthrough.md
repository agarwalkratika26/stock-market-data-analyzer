# Step-by-step project walkthrough

## 1. Understand the data flow

The dashboard asks the API for the watchlist, holdings, alerts, and selected ticker history. The API uses `market_data.py` to retrieve the configured source, `analytics.py` to calculate values, then returns JSON. The browser renders it in the chart and tables. The API stores the small editable demo state in `backend/data/*.json`.

```text
CSV / Yahoo / demo generator → market_data.py → analytics.py → FastAPI routes → Next.js dashboard
```

## 2. Run a no-account simulation

Start the two local servers using the README. The default demo generator creates seeded synthetic daily bars. `AAPL` always gets the same sequence for a given date range, which makes examples reproducible. The price is made up; use it to verify the flow, not to study the real market.

Open the dashboard, select a watchlist symbol, and change the chart period. Add a ticker to the watchlist. Create a price alert. Run the 20/50 day SMA strategy. The strategy result includes total return, CAGR, Sharpe ratio, maximum drawdown, benchmark return, and trade count.

## 3. Explore the API

Open `http://127.0.0.1:8000/docs`. Expand `GET /api/market/{symbol}/indicators` and try `MSFT`. The latest indicator values include RSI, MACD, and moving averages. For a more detailed response, inspect `data`, which returns the recent indicator series. Use `POST /api/backtest` to change the ticker, windows, starting cash, and assumed transaction cost.

## 4. Read the indicator formulas

- **SMA:** Arithmetic average of the last N closes. The 20- and 50-session averages provide a short and longer trend reference.
- **EMA:** Exponentially weighted average, giving recent prices more weight. MACD is EMA(12) minus EMA(26); the signal line is a 9-period EMA of MACD.
- **RSI:** Exponential-smoothed average gains compared with average losses over 14 periods, scaled from 0 to 100. Below 30 and above 70 are conventional watch levels, not buy/sell commands.
- **Bollinger Bands:** 20-session simple average plus/minus two rolling standard deviations. They describe recent dispersion; they do not predict a breakout.

## 5. Understand the backtest

The example strategy holds the asset when its fast SMA is above its slow SMA and otherwise holds cash. The signal is shifted one bar, so it cannot act on a close before that close is observed. Return is position × daily close-to-close return minus a basis-point cost when exposure changes. The benchmark holds the asset throughout.

The educational simulation assumes fractional exposure, no leverage, and no shorting. It does not model fills, bid/ask spreads, slippage, taxes, liquidity, delisted assets, or all corporate actions. A positive historical result is not evidence of future profitability. Try multiple date ranges and compare against the benchmark before describing conclusions.

## 6. Import a CSV

Copy `backend/data/prices/sample.csv` to `backend/data/prices/DEMO.csv` (or the ticker you want), keep the six required headers, and call:

```text
GET http://127.0.0.1:8000/api/market/DEMO/history?period=1mo&provider=csv
```

Dates must parse with pandas, numeric columns should be valid numbers, and rows should be chronological. The API sorts the CSV rows by date.

## 7. Use public Yahoo Finance history

Set `DEFAULT_PROVIDER=yfinance` in `backend/.env`, restart the API, then request an endpoint. You can also add `?provider=yfinance` on history or indicator calls without changing the default. Network access is required, and public endpoints can change, throttle, or return delayed history. “Live” in this project means a refreshed latest available bar, not streaming prices.

## 8. Extend the project

Good next increments for a student portfolio:

1. Add server-side caching and a provider interface with clear failure states.
2. Persist data with SQLite and add migrations.
3. Add portfolio editing and alert deletion controls in the dashboard.
4. Add a second strategy and tests for indicator edge cases and look-ahead bias.
5. Add request validation, structured logging, and API rate limits.
6. Deploy the API and dashboard separately with environment-based CORS settings.

Keep a short note of what you changed and why. Include data source, date range, assumptions, and known limitations in every analysis screenshot or write-up.

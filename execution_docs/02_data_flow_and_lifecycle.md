# 02 - Data Flow and Lifecycle

## 1. End-to-End Data Pipeline Architecture

Data flows through the system in five distinct, strictly ordered phases:
1. **Extraction / Ingestion**: Fetching raw time-series data from one of three providers (Synthetic Demo, Yahoo Finance API, or CSV).
2. **Standardization & Preprocessing**: Sanitizing headers, sorting chronologically by date, casting numeric types, and removing NaN records.
3. **Feature Engineering & Indicator Calculation**: Vectorized computation of SMAs, EMAs, MACD, Wilder's RSI, and Bollinger Bands using Pandas/NumPy.
4. **Signal Determination & Downstream Evaluation**: Extracting the latest bar metrics to evaluate overbought/oversold states and evaluating active user alerts.
5. **Serialization & Presentation**: Transforming DataFrames into JSON payloads for FastAPI REST endpoints and client-side SVG rendering.

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Browser
    participant API as FastAPI Router (main.py)
    participant Adapter as Market Data Adapter (market_data.py)
    participant Engine as Analytics Engine (analytics.py)
    participant Store as Data Store (data_store.py)

    User->>API: GET /api/market/{symbol}/indicators?period=6mo&provider=demo
    API->>Adapter: history(symbol="AAPL", period="6mo", provider="demo")
    
    alt Demo Provider
        Adapter->>Adapter: demo_history(): SHA-256 Seed + GBM Random Walk
    else Yahoo Finance
        Adapter->>Adapter: yfinance.download(symbol, period)
    else CSV Import
        Adapter->>Adapter: read_csv("backend/data/prices/{symbol}.csv")
    end
    
    Adapter-->>API: Normalized pd.DataFrame [date, open, high, low, close, volume]
    API->>Engine: add_indicators(DataFrame)
    Engine->>Engine: Compute SMA20/50, EMA12/26, MACD, RSI14, BBands
    Engine-->>API: Enriched DataFrame
    API->>Engine: current_signal(latest_bar)
    Engine-->>API: Signal dict {label, reason, rsi_14}
    API->>Store: read("alerts.json")
    Store-->>API: Active alerts
    API->>API: Evaluate alerts against latest close & RSI
    API-->>User: JSON Response {symbol, provider, signal, current, series, alerts}
```

---

## 2. Ingestion & Transformation Details

### Phase 1: Ingestion
- Input parameters: `symbol` (e.g. `"AAPL"`), `period` (`"1mo"`, `"3mo"`, `"6mo"`, `"1y"`, `"2y"`), and `provider` (`"demo"`, `"yfinance"`, `"csv"`).
- Target bar counts mapped via `VALID_PERIODS`:
  - `1mo`: 23 business days
  - `3mo`: 66 business days
  - `6mo`: 132 business days
  - `1y`: 252 business days
  - `2y`: 504 business days

### Phase 2: Sanitization & Normalization
- Regardless of source, the adapter guarantees:
  - Columns lowercased: `['date', 'open', 'high', 'low', 'close', 'volume']`.
  - Date converted to `pd.to_datetime` and sorted in ascending order.
  - Multi-index headers flattened (specifically addressing Yahoo Finance multi-level headers).
  - Nulls dropped via `.dropna()`.

### Phase 3: Analytical Transformation
- Transformed by `add_indicators(frame)`:
  - `sma_20`, `sma_50`: Rolling arithmetic means.
  - `ema_12`, `ema_26`: Exponentially weighted moving averages ($\alpha = \frac{2}{span + 1}$).
  - `macd`: Difference of `ema_12 - ema_26`.
  - `macd_signal`: 9-day EMA of `macd`.
  - `rsi_14`: Wilder's Exponential Smoothing with $\alpha = 1/14$ over positive/negative price changes.
  - `bb_upper`, `bb_lower`: 20-day rolling mean $\pm 2$ standard deviations.

### Phase 4: Backtest Data Flow
```mermaid
flowchart LR
    A[Raw OHLCV DataFrame] --> B[Dropna on Close]
    B --> C[Compute Fast SMA & Slow SMA]
    C --> D[Generate Position Boolean: Fast > Slow]
    D --> E[Shift Position by 1 Bar: Avoid Lookahead]
    E --> F[Calculate Daily Market Returns]
    F --> G[Deduct Turnover * Transaction Cost Bps]
    G --> H[Cumulative Product for Strategy & Benchmark Equity]
    H --> I[Compute Drawdown, CAGR, Sharpe Ratio]
```

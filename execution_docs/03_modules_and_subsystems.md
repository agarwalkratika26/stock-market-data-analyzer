# 03 - Modules and Subsystems

## 1. Backend Subsystems (`backend/app/`)

### 1.1 `main.py` (API Gateway & Controller)
- **Role**: Application entry point, CORS configuration, route declaration, error handling.
- **Key Endpoints**:
  - `GET /api/health`: Returns API status and active default data provider.
  - `GET /api/market/{symbol}/history`: Returns historical raw OHLCV bars.
  - `GET /api/market/{symbol}/indicators`: Returns processed indicators, current signal, and active triggered alerts.
  - `GET /api/market/{symbol}/quote`: Fast quote endpoint returning the most recent bar and percentage change.
  - `GET / PUT /api/watchlist`: Fetch or update user watchlist.
  - `GET / PUT /api/portfolio`: Fetch or update holdings with live mark-to-market calculations.
  - `GET / POST / DELETE /api/alerts`: Manage price and RSI threshold alert triggers.
  - `POST /api/backtest`: Execute parameter-driven moving average crossover backtests.

### 1.2 `market_data.py` (Data Provider Adapter)
- **Role**: Provider abstraction isolating data fetching logic.
- **Key Functions**:
  - `demo_history(symbol: str, days: int = 252) -> pd.DataFrame`: Generates offline deterministic daily price bars using SHA-256 seeding.
  - `history(symbol: str, period: str = "6mo", provider: str | None = None) -> tuple[pd.DataFrame, str]`: Dispatches requests to `demo`, `yfinance`, or `csv` handlers.
  - `frame_records(frame: pd.DataFrame) -> list[dict]`: Formats DataFrames into JSON-compliant dictionary arrays with NaN sanitization.

### 1.3 `analytics.py` (Quantitative & Computational Engine)
- **Role**: Vectorized financial mathematics and backtesting simulation.
- **Key Functions**:
  - `add_indicators(frame: pd.DataFrame) -> pd.DataFrame`: Appends technical indicators to an OHLCV frame.
  - `current_signal(row: pd.Series) -> dict`: Evaluates directional momentum and overbought/oversold status.
  - `backtest(frame: pd.DataFrame, fast: int = 20, slow: int = 50, initial_cash: float = 10000, cost_bps: float = 10) -> dict`: Simulates long-or-cash trading with execution latency and transaction drag.

### 1.4 `data_store.py` (Atomic Persistence Store)
- **Role**: Thread-safe, non-destructive file persistence for configuration and user data.
- **Mechanism**:
  - Writes to a `.tmp` file before issuing an OS-level atomic file rename (`replace()`), ensuring zero file corruption if process dies mid-write.

### 1.5 `schemas.py` (Validation & Contracts)
- **Role**: Enforces Pydantic models for incoming requests:
  - `WatchlistUpdate`: Enforces string lists of length 1 to 30.
  - `HoldingInput` & `PortfolioUpdate`: Enforces positive share counts and prices up to 50 assets.
  - `BacktestRequest`: Bounds window sizes and costs.
  - `AlertCreate`: Enforces condition literals (`price_above`, `price_below`, `rsi_above`, `rsi_below`).

---

## 2. Frontend Subsystems (`frontend/app/`)

### 2.1 `page.tsx` (Dashboard UI Controller)
- **State Management**:
  - Active symbol, period, and data provider.
  - Dynamic indicator visibility toggles (SMA, EMA, RSI, Bollinger Bands).
  - Watchlist management, portfolio allocation, and custom alert creation.
  - Real-time backtest execution and metric charting.
- **Data Synchronization**:
  - Periodic auto-refresh every 5 minutes (300,000 ms) via React `useEffect` interval.

### 2.2 Visualization Subsystem
- **Direct SVG Renderers**:
  - Candlestick plots with dynamic auto-scaling coordinate transforms.
  - Path interpolation for moving average lines and Bollinger Band shaded confidence channels.
  - Split lower panel for RSI oscillator rendering with 30/70 benchmark threshold lines.
  - Equity curve visualization comparing strategy returns against buy-and-hold benchmarks.

---

## 3. Python Analyzer Standalone Subsystem (`python_analyzer/`)

- `stock_analyzer/data.py`: Standalone retrieval engine supporting synthetic and live feeds.
- `stock_analyzer/analysis.py`: Standalone indicator calculations and summary statistics.
- `stock_analyzer/charts.py`: Terminal/matplotlib rendering capabilities.
- `stock_analyzer/report.py`: Markdown and console formatted technical summaries.
- `streamlit_app.py`: Standalone lightweight Streamlit interface for zero-Node.js environments.

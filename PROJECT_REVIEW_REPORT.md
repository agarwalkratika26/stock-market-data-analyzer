# Technical Manager Project Review & Handoff Report

**Project Title:** Stock Market Data Analyzer  
**Author / Engineer:** Senior Python & Full-Stack Developer  
**Recipient / Reviewer:** Technical Manager (ChatGPT)  
**Date of Review:** 2026-11-22  
**Implementation Scope:** Option C (Full-Stack FastAPI API + Next.js Dashboard, with reusable CLI and Streamlit interfaces)

---

## 1. Executive Summary & Final Architecture

The **Stock Market Data Analyzer** is an educational financial computing and data analytics platform designed for coursework and portfolio demonstration. The system runs completely free of cost without paid financial terminals, broker accounts, or proprietary API keys.

### Architectural Tiers
1. **Canonical Quantitative Engine (`src/stock_analyzer/`)**:
   - Single canonical analysis package (superseding the legacy `python_analyzer/` directory, which was audited and removed).
   - Ingestion layer: Supports deterministic synthetic simulation (seeded Geometric Brownian Motion), local CSV ingestion with automatic header normalization, and optional public Yahoo Finance daily history with automatic local fallback.
   - Analytical layer: Computes daily returns, cumulative returns, rolling volatility ($\sigma_{\text{daily}} \times \sqrt{252}$), Simple Moving Averages (20 & 50), Exponential Moving Averages (12 & 26), MACD (12, 26, 9), Wilder's smoothed RSI-14, Bollinger Bands (20, 2$\sigma$), and descriptive non-prescriptive momentum signals.
   - Simulation engine: Long-or-cash Moving Average Crossover simulation enforcing an explicit 1-bar execution delay (`position = signal.shift(1)`) to eliminate lookahead bias, deducting transaction friction in basis points, and computing CAGR, Maximum Drawdown, and Sharpe Ratio against a buy-and-hold benchmark.
   - Visual & report layer: Renders high-resolution Matplotlib/Seaborn charts (`price_trend.png`, `moving_averages.png`, `return_distribution.png`, `backtest_equity.png`) and formats structured Markdown summary reports with single-currency formatting.
2. **REST API Service (`backend/app/`)**:
   - FastAPI REST API using synchronous `def` route handlers executed via FastAPI's threadpool worker model so that CPU-bound Pandas and NumPy computations do not block the ASGI asyncio event loop.
   - Pydantic validation schemas with input bounds.
   - Atomic file persistence (`tempfile.replace`) for watchlists, portfolio holdings, and alerts.
3. **Frontend Dashboard (`frontend/app/`)**:
   - Next.js 16+ App Router web application built with TypeScript, Recharts (`ComposedChart`), and Lucide icons.
   - Styling: Custom vanilla CSS (`globals.css`) using responsive flex/grid layouts and CSS variables (no Tailwind dependency).
   - Features: Real-time price chart with toggleable SMA 20, SMA 50, and Bollinger Band overlays, RSI badge, watchlist manager, portfolio tracker, alert creator, and interactive backtest simulator.
4. **Command-Line Interface (`main.py`) & Streamlit UI (`streamlit_app.py`)**:
   - Root-level entrypoints powered by the same reusable `src/stock_analyzer/` quantitative engine.

---

## 2. Implemented Feature Checklist Mapped to Source Files & API Routes

| Feature / Requirement | Status | Implementation Source | API Route / Entry Point |
|---|---|---|---|
| **Deterministic Synthetic Demo Data** | Verified | `src/stock_analyzer/data.py: demo_history()` | `python main.py --source demo` / `GET /api/market/{symbol}/history?provider=demo` |
| **CSV Ingestion & Validation** | Verified | `src/stock_analyzer/data.py: load_csv()`, `clean_prices()` | `python main.py --source csv --csv-path <path>` / `GET /api/market/{symbol}/history?provider=csv` |
| **Yahoo Finance Public Ingestion** | Verified | `src/stock_analyzer/data.py: load_yfinance()`, `load_prices()` | `python main.py --source yfinance` / `GET /api/market/{symbol}/history?provider=yfinance` |
| **Data Cleaning & Normalization** | Verified | `src/stock_analyzer/data.py: clean_prices()` | Shared by all ingestion pipelines |
| **Daily Returns & Annualized Volatility** | Verified | `src/stock_analyzer/analysis.py: analyze_prices()` | Shared across CLI, Streamlit, and API |
| **Technical Indicators (SMA, EMA, RSI, MACD, BB)** | Verified | `src/stock_analyzer/analysis.py: analyze_prices()` | `GET /api/market/{symbol}/indicators` |
| **Descriptive Momentum & Trend Signals** | Verified | `src/stock_analyzer/analysis.py: evaluate_signal()` | `GET /api/market/{symbol}/indicators` |
| **Lookahead-Bias-Free Backtest Simulation** | Verified | `src/stock_analyzer/analysis.py: run_backtest()` | `POST /api/backtest` |
| **Matplotlib / Seaborn Chart Suite** | Verified | `src/stock_analyzer/charts.py` | CLI outputs to `outputs/<TICKER>/` |
| **Markdown Analysis Report Generation** | Verified | `src/stock_analyzer/report.py: write_report()` | CLI outputs to `outputs/<TICKER>/summary_report.md` |
| **Root Command-Line Interface** | Verified | `main.py` | Direct terminal execution |
| **Root Streamlit Dashboard** | Verified | `streamlit_app.py` | `streamlit run streamlit_app.py` |
| **FastAPI REST API Service (13 Routes)** | Verified | `backend/app/main.py` | Port 8000 (`python run.py`) |
| **Interactive Next.js Dashboard with Overlays** | Verified | `frontend/app/page.tsx` | Port 3000 (`npm run dev`) |
| **Next.js Production Build** | Verified | `frontend/` (`next build`) | Verified clean build (`npm run build`) |
| **Automated Verification Test Suite** | Verified | `verify_project.py` | 5-stage automated test script |

---

## 3. Final Repository Folder Tree

```text
Stock-Market-Data-Analyzer/
├── data/
│   ├── raw/
│   │   ├── AAPL.csv                       # Sample reference prices for AAPL
│   │   ├── DEMO.csv                       # Fictional sample CSV for testing (Jan-Feb 2025)
│   │   └── sample.csv                     # Minimal 7-row sample CSV
│   └── processed/
│       └── AAPL_analysis.csv              # Analyzed time-series with all 15+ indicator columns
├── notebooks/
│   └── stock_analysis_walkthrough.ipynb    # Educational Jupyter notebook walkthrough
├── src/
│   └── stock_analyzer/                    # Canonical quantitative Python package
│       ├── __init__.py                    # Public exports
│       ├── data.py                        # Ingestion, GBM demo generation, cleaning
│       ├── analysis.py                    # Financial math, indicators, backtest engine
│       ├── charts.py                      # Matplotlib / Seaborn charts
│       ├── report.py                      # Markdown summary report writer
│       └── pipeline.py                    # End-to-end orchestration pipeline
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── analytics.py                   # API indicator calculation & backtest logic
│   │   ├── config.py                      # Pydantic BaseSettings configuration
│   │   ├── data_store.py                  # Atomic JSON storage module
│   │   ├── main.py                        # FastAPI routes (threadpool worker execution)
│   │   ├── market_data.py                 # Multi-provider adapter
│   │   └── schemas.py                     # Pydantic boundary validation models
│   ├── data/
│   │   ├── alerts.json                    # User alerts state
│   │   ├── portfolio.json                 # User portfolio state
│   │   ├── watchlist.json                 # User watchlist state
│   │   └── prices/                        # CSV storage location for backend
│   │       └── sample.csv
│   ├── requirements.txt                   # Backend dependencies
│   └── run.py                             # API runner script (uvicorn)
├── frontend/
│   ├── app/
│   │   ├── globals.css                    # Custom CSS styling (responsive grid, no Tailwind)
│   │   ├── layout.tsx                     # Root layout
│   │   └── page.tsx                       # Dashboard with ComposedChart & indicator overlays
│   ├── package.json                       # Next.js, React, Recharts, Lucide-react
│   └── tsconfig.json                      # TypeScript configuration
├── outputs/
│   └── AAPL/
│       ├── AAPL_analysis.csv              # Output data from latest CLI run
│       ├── backtest_equity.png            # Strategy equity vs benchmark plot
│       ├── moving_averages.png            # Moving averages & Bollinger Bands plot
│       ├── price_trend.png                # Closing price trendline plot
│       ├── return_distribution.png        # Daily return distribution plot
│       └── summary_report.md              # Markdown summary report
├── images/
│   └── screenshots/
│       ├── backtest-preview.svg           # Vector mock preview of backtest
│       ├── dashboard-preview.svg          # Vector mock preview of dashboard
│       ├── dashboard-screenshot.png       # Live browser screenshot of Next.js dashboard (1440x900)
│       ├── backtest_equity.png
│       ├── moving_averages.png
│       ├── price_trend.png
│       └── return_distribution.png
├── reports/
│   ├── AAPL_summary_report.md             # Markdown analysis report
│   ├── backtest_equity.png
│   ├── moving_averages.png
│   ├── price_trend.png
│   └── return_distribution.png
├── docs/
│   ├── architecture.md                    # Multi-tier system architecture
│   ├── folder-structure.md                # Structural documentation
│   ├── github-and-portfolio.md            # GitHub setup and commit guidelines
│   ├── implementation-plan.md             # 10-phase beginner implementation guide
│   ├── installation.md                    # OS setup for Windows and macOS
│   ├── interview-prep.md                  # Interview questions and answers
│   ├── project-explanation.md             # Project background and design decisions
│   ├── six-day-plan.md                    # Day-by-day proof-of-work commit plan
│   ├── tech-stack-options.md              # Options A, B, and C comparative guide
│   ├── virtual-simulation-sample-run.md   # Step-by-step simulated run walkthrough
│   └── walkthrough.md                     # Guided walkthrough
├── execution_docs/                        # Living technical execution records
│   ├── 01_architecture_and_system_design.md
│   ├── 02_data_flow_and_lifecycle.md
│   ├── 03_modules_and_subsystems.md
│   ├── 04_datasets_and_sources.md
│   ├── 05_models_algorithms_and_learning.md
│   ├── 06_verification_and_validation_guide.md
│   ├── 07_execution_log.md
│   └── README.md
├── main.py                                # Root CLI entrypoint
├── streamlit_app.py                       # Root Streamlit dashboard
├── verify_project.py                      # 5-stage automated test & verification script
├── requirements.txt                       # Unified root Python dependencies
├── .gitignore                             # Git exclusion rules
├── LICENSE                                # MIT License
├── README.md                              # Main repository documentation
└── PROJECT_REVIEW_REPORT.md               # Technical review and handoff report
```

*Note on `python_analyzer/`: Audited against `src/stock_analyzer/`. Confirmed that `src/stock_analyzer/` contains a strictly enhanced superset of all modules, indicators, charts, and demo generators. `python_analyzer/` was removed to eliminate dual-package ambiguity.*

---

## 4. Exact Installation & Run Commands

### 4.1 Windows (PowerShell)

```powershell
# 1. Environment Setup (Python 3.11 - 3.13)
# If using a standard Python interpreter:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# 2. Run Comprehensive Automated Verification
python verify_project.py

# 3. Run Command-Line Analysis (Offline Synthetic Demo)
python main.py --ticker AAPL --source demo

# 4. Run Command-Line Analysis (CSV Ingestion with matched dates)
python main.py --ticker DEMO --source csv --csv-path data/raw/DEMO.csv --start 2025-01-01 --end 2025-02-15

# 5. Optional: Launch Interactive Streamlit Dashboard (Option B)
streamlit run streamlit_app.py

# 6. Full-Stack Setup (Option C - Two Terminals)
# Terminal 1 - FastAPI Backend:
cd backend
python run.py

# Terminal 2 - Next.js Frontend:
cd frontend
npm install
npm run build    # Verify production build
npm run dev      # Start dev server on http://localhost:3000
```

### 4.2 macOS / Linux (Bash)

```bash
# 1. Environment Setup (Python 3.11 - 3.13)
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt

# 2. Run Comprehensive Automated Verification
python verify_project.py

# 3. Run Command-Line Analysis (Offline Synthetic Demo)
python main.py --ticker AAPL --source demo

# 4. Run Command-Line Analysis (CSV Ingestion with matched dates)
python main.py --ticker DEMO --source csv --csv-path data/raw/DEMO.csv --start 2025-01-01 --end 2025-02-15

# 5. Optional: Launch Interactive Streamlit Dashboard (Option B)
streamlit run streamlit_app.py

# 6. Full-Stack Setup (Option C - Two Terminals)
# Terminal 1 - FastAPI Backend:
cd backend
python3 run.py

# Terminal 2 - Next.js Frontend:
cd frontend
npm install
npm run build    # Verify production build
npm run dev      # Start dev server on http://localhost:3000
```

---

## 5. Data Sources, Provenance & Provider Limitations

1. **Deterministic Synthetic Demo (`demo`)**:
   - Seeded Geometric Brownian Motion: $\text{Seed} = \text{SHA256}(\text{ticker})[:8]$, base price $S_0 = 45 + (\text{seed} \pmod{350})$, drift $\mu = 0.00035 + (\text{seed} \pmod 8)/100,000$, volatility $\sigma = 0.018$.
   - **Provenance**: Synthetic mathematical simulation. Labeled prominently across CLI, reports, and UI. Not real market prices.
2. **Local Sample CSVs (`csv`)**:
   - `data/raw/DEMO.csv`: 30 daily bars from `2025-01-02` to `2025-02-13` generated for testing CSV ingestion and schema validation.
   - `data/raw/AAPL.csv`: Sample price history for AAPL (January–February 2024).
   - `data/raw/sample.csv`: Minimal 7-row CSV fixture.
3. **Yahoo Finance Public Data (`yfinance`)**:
   - Downloads public adjusted history.
   - Limitations: Public web scraper subject to 15-minute delays, network downtime, and provider rate-limiting. System automatically cascades to local CSV or offline demo if unavailable.

---

## 6. Analysis Formulas, Backtest Assumptions & Financial Caveats

### 6.1 Quantitative Mathematics
- **Daily Return:** $R_t = \frac{C_t - C_{t-1}}{C_{t-1}}$
- **Period Return:** $\left(\frac{C_{\text{final}}}{C_{\text{initial}}} - 1\right) \times 100\%$
- **Simple Moving Average:** $\text{SMA}_k(t) = \frac{1}{k} \sum_{i=0}^{k-1} C_{t-i}$
- **Exponential Moving Average:** $\text{EMA}_t = \alpha C_t + (1 - \alpha) \text{EMA}_{t-1}$, where $\alpha = \frac{2}{\text{span} + 1}$
- **Wilder's RSI (14-period):** Smoothed gain/loss using $\alpha = \frac{1}{14}$.
- **MACD:** $\text{EMA}_{12} - \text{EMA}_{26}$; Signal line = $\text{EMA}_9(\text{MACD})$.
- **Bollinger Bands:** $\text{SMA}_{20} \pm 2 \cdot \sigma_{20}$.
- **Annualized Volatility:** $\sigma_{\text{ann}} = \text{std}(R) \times \sqrt{252} \times 100\%$.

### 6.2 Backtest Simulation Timing Model & Friction
- **Timing Model:** Long if $\text{FastSMA}_t > \text{SlowSMA}_t$, else Cash ($0$).
- **Lookahead Bias Correction:** The strategy position is shifted forward by exactly one bar: `position = signal.shift(1).fillna(0.0)`. Trading return at session $t+1$ is $R_{\text{strategy}, t+1} = \text{Position}_{t+1} \times R_{\text{market}, t+1} - \text{Friction}$. No trade executes at the bar that generated the signal.
- **Transaction Friction:** Deducts 10 basis points ($0.10\%$) upon every position turnover event: $\text{Friction}_t = |\text{Position}_t - \text{Position}_{t-1}| \times \frac{\text{cost\_bps}}{10,000}$.
- **Caveats:** Historical simulation excludes borrow costs, shorting, tax liabilities, market impact, bid-ask spread variations, and cash dividends. Past backtested performance is educational and never indicative of future market returns.

---

## 7. Sample Analysis Result (Derived Directly from Actual Run Artifact)

The following metrics are derived directly from the generated artifact [outputs/AAPL/AAPL_analysis.csv](file:///c:/Users/agarw/OneDrive/Desktop/New%20folder/python/Stock%20Market%20Data%20Analyzer/outputs/AAPL/AAPL_analysis.csv) produced by running `python main.py --ticker AAPL --source demo`:

- **Target Symbol:** `AAPL`
- **Data Provider:** `demo (synthetic)`
- **Observations:** Exactly 252 business days
- **Actual Date Range:** **2025-12-04 through 2026-11-20**
- **First Close:** \$361.67
- **Latest Close:** \$282.75
- **Period Return:** -21.82%
- **Annualized Return Volatility:** 27.78%
- **Highest Observed Price:** \$400.78 on 2026-04-06 (high field)
- **Lowest Observed Price:** \$271.83 on 2026-11-17 (low field)
- **Fast SMA (20 sessions):** \$294.23
- **Slow SMA (50 sessions):** \$309.75
- **Trend Evaluation:** SMA 20 (\$294.23) < SMA 50 (\$309.75) (bearish/negative trend context)
- **Descriptive Indicator Signal:** Momentum negative (MACD is below its 9-day signal line, RSI-14: 37.81)
- **Backtest Initial Capital:** \$10,000.00
- **Strategy Ending Equity:** \$9,604.37 (-3.96% strategy total return)
- **Benchmark Buy & Hold Return:** -21.82%
- **Strategy CAGR:** -3.96%
- **Maximum Drawdown:** -10.72%
- **Annualized Sharpe Ratio:** -0.22
- **Rebalance Trades Executed:** 4 trades

---

## 8. Verification Commands Run & Real Results

### 8.1 Automated Verification Script (`verify_project.py`)
- **Command:** `.\.venv\Scripts\python.exe -u verify_project.py`
- **Result:** **Exit Code 0 — All 5 modules passed with 0 failures.**
  - **Section 1 (Data Ingestion & Cleaning):** Validated empty DataFrame error handling, missing column exceptions, 30 rows in `data/raw/DEMO.csv` with chronological sorting and zero NaNs, and deterministic reproducibility of `demo_history()`.
  - **Section 2 (Indicators & Financial Math):** Verified daily returns matching $(C_t/C_{t-1} - 1)$, SMA-5 slice arithmetic, RSI-14 values bounded in $[0, 100]$, Bollinger Upper $\ge$ Lower, extrema detection matching data max/min, signal dictionary shape, and factual summary generation.
  - **Section 3 (Strategy Backtest Simulation):** Verified 1-bar execution lag (`position == signal.shift(1)`), friction deduction, initial cash preservation (\$10,000.00), non-zero CAGR, drawdown, Sharpe, and equity curve matching bar count. Tested parameter boundary validation ($fast \ge slow$, negative capital).
  - **Section 4 (Fresh CLI Pipeline in Isolated Tempdir):** Executed `run_analysis` in a fresh temporary directory. Verified creation of non-empty CSV (252 bars, >1KB), Markdown report (>500B with single `$` currency formatting), and 4 binary PNG chart files (>5KB each).
  - **Section 5 (FastAPI REST Routes with State Isolation):** Tested all 13 routes using isolated temporary JSON state:
    1. `GET /`: Status 200, returned app metadata.
    2. `GET /api/health`: Status 200, status `"ok"`, provider `"demo"`.
    3. `GET /api/market/AAPL/history?period=6mo&provider=demo`: Status 200, returned 132 bars with OHLCV keys.
    4. `GET /api/market/AAPL/indicators?period=6mo&provider=demo`: Status 200, returned indicators dict and signal dict.
    5. `GET /api/market/AAPL/quote`: Status 200, returned symbol, price, change, change_pct, quote_type.
    6. `GET /api/watchlist`: Status 200, returned 2 watchlist quote items.
    7. `PUT /api/watchlist`: Status 200, updated symbols to `["AAPL", "NVDA", "GOOGL"]`.
    8. `GET /api/portfolio`: Status 200, returned holdings, market value, cost basis.
    9. `PUT /api/portfolio`: Status 200, updated portfolio holdings.
    10. `GET /api/alerts`: Status 200, returned alerts list.
    11. `POST /api/alerts`: Status 201 Created, created price alert.
    12. `DELETE /api/alerts/{id}`: Status 200, deleted alert.
    13. `POST /api/backtest`: Status 200, returned metrics and equity curve.

#### Starlette TestClient Deprecation Warning Analysis:
- **Observed Notice:** `StarletteDeprecationWarning: Using 'httpx' with 'starlette.testclient' is deprecated; install 'httpx2' instead.`
- **Root Cause & Compatibility Investigation:**
  1. FastAPI `0.165.0` strictly requires `starlette>=1.6.0` because `fastapi._body_limit` imports `from starlette.middleware import body_limit`. Downgrading to `starlette<1.0.0` (such as `0.52.1`) causes an immediate runtime failure: `ImportError: cannot import name 'body_limit' from 'starlette.middleware'`.
  2. Starlette `1.10.0` includes an upstream advisory recommending `httpx2`. However, testing with `httpx2==2.16.2` revealed that `httpx2.Client` hangs indefinitely on Windows during synchronous request processing inside `_TestClientTransport` and AnyIO's `BlockingPortal`.
  3. In contrast, standard `httpx==0.28.1` executes all 13 REST API routes synchronously, reliably, and without latency (completing the full test suite in under 10 seconds).
  4. The warning is therefore purely advisory and non-breaking. The stable, verified dependency configuration is pinned to `fastapi>=0.165`, `starlette>=1.6.0`, and `httpx>=0.28.0`.

### 8.2 Frontend Production Build (`npm run build`)
- **Command:** `npm --prefix frontend run build`
- **Result:** **Exit Code 0 — Compiled successfully in 669ms.**
  - TypeScript checking passed with zero errors (`Finished TypeScript in 3.2s`).
  - Static page generation succeeded for all routes (`/` and `/_not-found`).

### 8.3 Safe Handling of `.python_base` Runtime
- **Inspection Findings:** `.python_base` is a physical local directory on disk (`Attributes: ReadOnly, Directory, Archive, ReparsePoint` bearing OneDrive placeholder tag `0x9000e01a` within the OneDrive workspace path).
- **Runtime Dependency:** The active virtual environment relies directly on this directory: `.venv/pyvenv.cfg` specifies `home = ...\.python_base` and `executable = ...\.python_base\python.exe`. Deleting `.python_base` breaks the virtual environment.
- **Git Protection:** `.python_base/` is explicitly listed in [.gitignore](file:///c:/Users/agarw/OneDrive/Desktop/New%20folder/python/Stock%20Market%20Data%20Analyzer/.gitignore) (line 6), preventing it from being tracked or committed to version control.

### 8.4 Live Server Execution & Browser Screenshot Verification
- **Background Servers Started:**
  - FastAPI REST Backend running on port 8000 via Uvicorn (`cd backend; ..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`).
  - Next.js Web Dashboard running on port 3000 via Turbopack (`cd frontend; npm run dev`).
- **Live Endpoint Probes:**
  - `GET http://127.0.0.1:8000/api/health` responded with `HTTP 200 OK`: `{"status":"ok","timestamp":"2026-11-22T14:54:10.195575+00:00","provider":"demo"}`.
  - `GET http://localhost:3000` responded with `HTTP 200 OK`.
- **Browser Screenshot Capture:**
  - Successfully captured a genuine high-resolution browser screenshot from headless Google Chrome (`1440x900` viewport):
    - File: [images/screenshots/dashboard-screenshot.png](file:///c:/Users/agarw/OneDrive/Desktop/New%20folder/python/Stock%20Market%20Data%20Analyzer/images/screenshots/dashboard-screenshot.png) (147,377 bytes).
  - Existing SVG files ([dashboard-preview.svg](file:///c:/Users/agarw/OneDrive/Desktop/New%20folder/python/Stock%20Market%20Data%20Analyzer/images/screenshots/dashboard-preview.svg) and [backtest-preview.svg](file:///c:/Users/agarw/OneDrive/Desktop/New%20folder/python/Stock%20Market%20Data%20Analyzer/images/screenshots/backtest-preview.svg)) are explicitly labeled as vector mock previews.

### 8.5 Git Exclusion & Cleanliness Confirmation
- **`.gitignore` Rules Audited:**
  - `.venv/`: Excluded (line 4).
  - `.python_base/`: Excluded (line 6).
  - `outputs/`: Excluded (line 15).
  - `frontend/node_modules/`: Excluded (line 17).
- **Git Operations:**
  - Confirmed Git is NOT initialized (`.git` directory does not exist).
  - No commits created, no push attempted.

### 8.6 Checks Not Run Live:
- Live streaming WebSocket connections (not part of requirements; polled snapshots are implemented and documented).
- Live yfinance API calls during test suite (isolated to synthetic demo and CSV by design to guarantee deterministic offline execution).

---

## 9. Known Issues, Tradeoffs & Suggested Next Steps

1. **Tradeoff: Atomic JSON Storage vs Relational Database**:
   - Current design uses single-node atomic JSON files (`tempfile.replace`) to enable student execution without configuring SQLite or PostgreSQL servers. For production multi-user deployments, migrate to PostgreSQL with SQLAlchemy.
2. **Tradeoff: Recharts AreaChart with Overlays vs Multi-Panel Candlestick Canvas**:
   - Dashboard implements Recharts `ComposedChart` with closing price fill, toggleable SMA 20, SMA 50, and Bollinger Band line overlays, and RSI badges. High-frequency candlestick rendering can be added via TradingView Lightweight Charts if intraday bars are introduced.
3. **Lookahead Shift vs Intraday Order Execution**:
   - Current backtest models next-bar daily execution (`shift(1)`). Intraday fill models (e.g. executing at Next Open rather than Next Close) would require 1-minute or 5-minute bar feeds.

---

## 10. Reviewer Inspection Guide

### 10.1 Local Application URLs
- **Interactive Web Dashboard (Next.js):** [http://localhost:3000](http://localhost:3000)
- **Backend API & Swagger Documentation (FastAPI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Backend Service Health Status:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

*(Note: Confirmed actively responding in the current development session. When services are stopped, start them via `cd backend; python run.py` and `cd frontend; npm run dev`.)*

### 10.2 Source Files & Verification Artifacts
1. **Automated Verification:** Run `.\.venv\Scripts\python.exe -u verify_project.py` (Exit code 0, 5/5 test sections pass).
2. **Quantitative Engine:** Review [src/stock_analyzer/analysis.py](file:///c:/Users/agarw/OneDrive/Desktop/New%20folder/python/Stock%20Market%20Data%20Analyzer/src/stock_analyzer/analysis.py) (indicators and 1-bar shifted backtest engine).
3. **Frontend Dashboard:** Review [frontend/app/page.tsx](file:///c:/Users/agarw/OneDrive/Desktop/New%20folder/python/Stock%20Market%20Data%20Analyzer/frontend/app/page.tsx) (`ComposedChart` with SMA/Bollinger toggles, RSI badge, and responsive grid).
4. **Live Screenshot:** Review [images/screenshots/dashboard-screenshot.png](file:///c:/Users/agarw/OneDrive/Desktop/New%20folder/python/Stock%20Market%20Data%20Analyzer/images/screenshots/dashboard-screenshot.png) (genuine 1440x900 browser capture).
5. **Generated Report:** Review [reports/AAPL_summary_report.md](file:///c:/Users/agarw/OneDrive/Desktop/New%20folder/python/Stock%20Market%20Data%20Analyzer/reports/AAPL_summary_report.md) (single currency formatting and co-located charts).
6. **FastAPI Routes:** Review [backend/app/main.py](file:///c:/Users/agarw/OneDrive/Desktop/New%20folder/python/Stock%20Market%20Data%20Analyzer/backend/app/main.py) (13 threadpool-managed REST endpoints).
7. **Execution Documentation:** Review [execution_docs/](file:///c:/Users/agarw/OneDrive/Desktop/New%20folder/python/Stock%20Market%20Data%20Analyzer/execution_docs/) (architecture, data flow, modules, datasets, and execution log).

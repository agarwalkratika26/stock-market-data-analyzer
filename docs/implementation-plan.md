# Implementation plan

Follow the phases in order. Each one leaves a concrete result you can inspect before moving on. For this repository, the analysis runs in the Python/FastAPI backend and the visual dashboard is a separate Next.js app.

## Phase 1: Setup

**What to do:** Install Python 3.11 or newer and Node.js 20.9 or newer. Open the project in an editor, create a Python virtual environment, install backend requirements, then install frontend packages with npm.

**Why:** Isolated dependencies prevent project packages from interfering with other Python projects. Checking runtimes first avoids debugging installation failures caused by incompatible versions.

**Expected output:** A working local development environment with the backend and frontend dependencies installed.

**Common beginner mistakes:** Installing packages into the wrong Python environment; forgetting to activate `.venv`; using a Node version below the framework requirement; committing `.env` or dependency folders.

## Phase 2: Project folder creation

**What to do:** Keep API code, frontend code, sample price files, and documentation in separate, clearly named folders. Add a README, `.gitignore`, and license early.

**Why:** A predictable layout makes it easier to locate code and explain which part handles data, analysis, or presentation.

**Expected output:** A repository structure similar to `backend/app`, `backend/data/prices`, `frontend/app`, and `docs`.

**Common beginner mistakes:** Putting every function in one file; mixing raw data with source code; using filenames that do not describe their contents; forgetting to ignore virtual environments and local secrets.

## Phase 3: Stock data collection

**What to do:** Choose a source: a prepared CSV, synthetic demo bars, or optional public history from `yfinance`. Define the ticker and date range. Save the source and retrieval details with your analysis.

**Why:** Every later calculation depends on knowing what data was collected and where it came from. A CSV or offline demo also makes the project usable without a network or account.

**Expected output:** A dated OHLCV table for one or more symbols, with the provider and period recorded.

**Common beginner mistakes:** Treating synthetic demo prices as real; assuming a public source is always available or real-time; requesting too much data; forgetting that provider formats and availability can change.

## Phase 4: Data cleaning

**What to do:** Parse the date column, normalize column names, sort rows by date, convert price and volume columns to numbers, and check for missing values, duplicate dates, or invalid rows.

**Why:** Calculations on misordered or incomplete prices can produce incorrect returns, moving averages, and charts without obvious errors.

**Expected output:** A clean chronological OHLCV dataset that satisfies the expected schema and is ready for analysis.

**Common beginner mistakes:** Calculating changes before sorting dates; silently filling every missing value with zero; ignoring duplicate dates; assuming a CSV's column names or date format are always identical.

## Phase 5: Exploratory data analysis

**What to do:** Inspect row count, date coverage, min/max, missing values, closing-price distribution, and volume. Plot the closing-price series before adding indicators.

**Why:** Initial inspection helps find data gaps, outliers, and unexpected behavior before more complex calculations are introduced.

**Expected output:** A short data-quality summary and a basic price-over-time chart, with observations about the selected period.

**Common beginner mistakes:** Drawing conclusions from a very short period; overlooking a missing-data gap; interpreting an outlier without checking the source; confusing correlation or a visual pattern with causation.

## Phase 6: Moving average calculation

**What to do:** Calculate simple moving averages such as 20 and 50 sessions, then optionally calculate exponential averages. Keep early rows with insufficient history marked as unavailable.

**Why:** Moving averages smooth daily fluctuations and let you compare a shorter period with a longer one.

**Expected output:** Price data with moving-average columns and a chart showing closes alongside the selected averages.

**Common beginner mistakes:** Forgetting the warm-up period; using calendar days instead of trading observations unintentionally; claiming that a moving-average crossover guarantees a future move; comparing results without recording the chosen windows.

## Phase 7: Return and volatility analysis

**What to do:** Calculate daily return from consecutive closes, compound returns over the selected period, and calculate a volatility measure from returns. For strategy analysis, record transaction costs and compare with a benchmark.

**Why:** Price level alone does not describe performance or variability. Returns support comparison across periods or securities, while volatility and drawdown help describe historical risk.

**Expected output:** A return series, cumulative return summary, volatility/risk summary, and clearly stated period and assumptions.

**Common beginner mistakes:** Summing daily percentage returns instead of compounding; mixing daily and annualized units; comparing different periods without adjustment; treating past volatility or return as a forecast; ignoring costs and signal timing in a backtest.

## Phase 8: Visualization

**What to do:** Plot price and moving averages with labeled axes, units, dates, and a legend. Add return or portfolio charts when they answer a specific question. Use Matplotlib or Seaborn for static reports; use Plotly or the dashboard chart library for interactive charts.

**Why:** A well-labeled chart makes trends and data issues easier to inspect and communicate.

**Expected output:** Readable chart images or dashboard panels that identify the ticker, date range, data source, and plotted values.

**Common beginner mistakes:** Missing titles or axis units; using misleading scales; overlaying too many lines; presenting synthetic demo data without a visible label; relying on color alone to distinguish series.

## Phase 9: Report generation

**What to do:** Summarize the question, ticker, data source, selected date range, data-quality notes, calculations, key observations, and limitations. Include charts and explain what the metrics mean.

**Why:** A report lets another person understand and reproduce how the conclusion was reached.

**Expected output:** A concise Markdown, HTML, or PDF report with charts, metrics, assumptions, and a clearly bounded interpretation.

**Common beginner mistakes:** Reporting a metric without defining it; omitting the source or time period; presenting a backtest as a forecast; turning an indicator into personalized investment advice; using illustrative figures as if they were real results.

## Phase 10: GitHub upload

**What to do:** Check `.gitignore`, remove secrets and local-only files, review README setup instructions, initialize or inspect Git, commit the project, create a GitHub repository, set its remote, and push the intended branch. Add a screenshot that identifies whether it shows demo or public data.

**Why:** A clean repository makes the work reviewable and reproducible for instructors, collaborators, and employers.

**Expected output:** A GitHub repository with source code, README, license, setup instructions, documentation, and clearly labeled screenshots.

**Common beginner mistakes:** Uploading `.env`, `.venv`, `node_modules`, or personal files; pushing to the wrong remote; skipping setup steps in the README; committing generated data as real market data; adding resume claims that the project does not support.

## Completion checklist

- The app starts from documented setup instructions.
- Demo prices are labeled synthetic and a CSV fallback is available.
- Data source, ticker, date range, and assumptions appear in the analysis.
- Cleaning, returns, indicators, and visual output can be explained.
- Backtest limitations are documented.
- GitHub contains no secrets or local dependency folders.

# Six-Day Proof-of-Work Implementation Plan

This guide lays out a realistic, day-wise Git commit schedule designed to demonstrate steady, disciplined engineering progress on GitHub for coursework, portfolios, and technical interviews.

---

## Overview

| Day | Primary Focus | Key Deliverables | Suggested Commit Message |
|---|---|---|---|
| **Day 1** | Project Setup & Architecture | Repository layout, `.gitignore`, dependencies, environment config | `feat: initialize project layout, virtualenv, and dependencies` |
| **Day 2** | Stock Data Collection | `data.py` (yfinance, CSV loader, deterministic synthetic demo) | `feat(data): implement multi-provider stock ingestion and offline demo generator` |
| **Day 3** | Data Cleaning & EDA | `clean_prices()`, datetime normalization, bad row handling | `feat(data): add robust price cleaning, validation, and missing data handling` |
| **Day 4** | Analysis & Backtesting | Returns, volatility, SMA/EMA/RSI/MACD/Bollinger, backtest simulation | `feat(analysis): implement technical indicators and cost-aware crossover backtest` |
| **Day 5** | Visualizations & Interfaces | Matplotlib/Seaborn charts, CLI workflow, Streamlit & FastAPI routes | `feat(viz): build visual charting suite, CLI pipeline, and REST API endpoints` |
| **Day 6** | Reports, Frontend & Handoff | Next.js dashboard integration, Markdown reporting, handoff docs | `docs: add comprehensive README, execution logs, and project review report` |

---

## Day-by-Day Detailed Breakdown

### Day 1: Project Setup & Environment
- **What to do**: Initialize the Git repository, configure `.gitignore` (ignoring `.venv/`, `node_modules/`, `.env`, caches), create root `requirements.txt` and `package.json`.
- **Files Created/Modified**: `.gitignore`, `requirements.txt`, `LICENSE`, `backend/requirements.txt`, `frontend/package.json`.
- **Screenshots to Save**: Terminal showing successful environment creation (`python -m venv .venv`).
- **Commit**: `git commit -m "feat: initialize project layout, virtualenv, and dependencies"`

### Day 2: Stock Data Ingestion Engine
- **What to do**: Build the modular data loader supporting public API (`yfinance`), CSV parsing, and offline deterministic SHA-256 Geometric Brownian Motion (`demo_history()`).
- **Files Created/Modified**: `src/stock_analyzer/data.py`, `data/raw/DEMO.csv`, `data/raw/sample.csv`.
- **Screenshots to Save**: Terminal test confirming offline demo data generation.
- **Commit**: `git commit -m "feat(data): implement multi-provider stock ingestion and offline demo generator"`

### Day 3: Data Cleaning, Normalization & EDA
- **What to do**: Implement timezone-naive datetime coercion, case-insensitive column mapping, zero/negative price filtering, duplicate date deduplication, and sanity checking.
- **Files Created/Modified**: `src/stock_analyzer/data.py` (`clean_prices()`), `notebooks/stock_analysis_walkthrough.ipynb`.
- **Screenshots to Save**: Notebook cell showing raw vs. cleaned DataFrame comparison.
- **Commit**: `git commit -m "feat(data): add robust price cleaning, validation, and missing data handling"`

### Day 4: Mathematical Analysis, Indicators & Backtest Engine
- **What to do**: Calculate daily/cumulative returns, rolling volatility ($\sigma \times \sqrt{252}$), SMA, EMA, MACD, Wilder's smoothed RSI-14, Bollinger Bands, and a moving average crossover backtest engine with a 1-bar execution lag and transaction friction.
- **Files Created/Modified**: `src/stock_analyzer/analysis.py`.
- **Screenshots to Save**: Terminal output showing backtest performance metrics.
- **Commit**: `git commit -m "feat(analysis): implement technical indicators and cost-aware crossover backtest"`

### Day 5: Visualization, CLI Pipeline & FastAPI Endpoints
- **What to do**: Create non-interactive Matplotlib/Seaborn charting functions (`price_trend.png`, `moving_averages.png`, `return_distribution.png`, `backtest_equity.png`), CLI entrypoint `main.py`, optional Streamlit dashboard `streamlit_app.py`, and FastAPI backend routes.
- **Files Created/Modified**: `src/stock_analyzer/charts.py`, `src/stock_analyzer/pipeline.py`, `main.py`, `streamlit_app.py`, `backend/app/main.py`.
- **Screenshots to Save**: Saved PNG charts from `outputs/AAPL/` and Streamlit UI screenshot.
- **Commit**: `git commit -m "feat(viz): build visual charting suite, CLI pipeline, and REST API endpoints"`

### Day 6: Frontend Dashboard, Documentation & Technical Handoff
- **What to do**: Connect the Next.js interactive frontend to the FastAPI backend, generate markdown reports, document all project options in `README.md`, update `execution_docs/`, and generate `PROJECT_REVIEW_REPORT.md`.
- **Files Created/Modified**: `frontend/app/page.tsx`, `reports/AAPL_summary_report.md`, `README.md`, `execution_docs/*`, `PROJECT_REVIEW_REPORT.md`.
- **Screenshots to Save**: Full browser window showing the Next.js interactive dashboard with price chart, indicators, and backtest results.
- **Commit**: `git commit -m "docs: add comprehensive README, execution logs, and project review report"`

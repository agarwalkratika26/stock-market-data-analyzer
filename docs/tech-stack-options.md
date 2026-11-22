# Tech stack options

These options move from a small local analysis script to a full web application. All can use public data or CSV files, so a paid market-data terminal is not required. `yfinance` depends on internet access and provider availability; CSV input remains a useful fallback.

## Option A — Easy: Python analysis script

**Difficulty:** Beginner

**Tools and libraries:** Python, `datetime`, pandas, NumPy, Matplotlib, optional Seaborn, CSV files. Add `yfinance` only after the CSV workflow works.

**What it does:** A single Python script loads a small price CSV, cleans dates and columns, calculates daily returns and moving averages, summarizes basic risk, and saves charts as image files.

**Expected output:** A runnable `.py` file or notebook, cleaned data table, return summary, price and moving-average charts, and a short written observation.

**Best for:** Learning the data-analysis fundamentals with minimal setup. It is easy to explain, but does not provide a web dashboard or an API.

## Option B — Intermediate: Python research dashboard

**Difficulty:** Intermediate; recommended for most student course projects.

**Tools and libraries:** Python, pandas, NumPy, `datetime`, Matplotlib and Seaborn for analysis or exported plots, `yfinance` for optional public history, and Streamlit for an optional interactive dashboard. Use CSV as an offline fallback.

**What it does:** Organizes analysis into reusable Python functions and a Streamlit interface. A user selects a ticker and period, views price and indicator charts, reviews return and risk summaries, and can compare a simple strategy with a benchmark.

**Expected output:** A shareable local web dashboard, reusable analysis code, charts and summary metrics, documented data sources, and a course-project README.

**Best for:** A student who wants a visible, interactive project while keeping the stack focused on Python. Streamlit is optional: the same analysis can first be delivered as a notebook or script.

## Option C — Advanced: Full-stack market-data application

**Difficulty:** Advanced

**Tools and libraries:** Python, pandas, NumPy, `datetime`, `yfinance` or CSV ingestion, FastAPI for a typed API, and Next.js with TypeScript for the dashboard. Use Plotly for interactive charts, or Matplotlib and Seaborn for Python-generated reports. A database, scheduled jobs, authentication, and deployment can be later additions.

**What it does:** Separates data ingestion and analytics from the browser interface. The backend serves market history, indicators, portfolio data, alerts, and backtest results; the frontend renders charts and interactive panels.

**Expected output:** A full-stack portfolio project with documented API routes, a web dashboard, data-source options, strategy simulation, and room to add database persistence and deployment.

**Best for:** Students who already know the basics or specifically want to demonstrate API and frontend skills. It has more setup and more components to explain and maintain.

## Recommendation

Choose **Option B** for the best balance for a typical student: it practices real Python analysis, produces an interactive result, and avoids the extra learning curve of maintaining a separate frontend application. Start with CSV data and add `yfinance` as an optional source. Keep Matplotlib and Seaborn for analysis and report-quality static charts; add Plotly only if interactive chart behavior is useful.

This workspace currently implements **Option C** (FastAPI + Next.js) to meet the original full-stack dashboard brief. It still uses Python, pandas, NumPy, and optional `yfinance`, with CSV and synthetic demo data. If your course expects a Python-only deliverable, you can build Option B as a smaller course version rather than presenting the Next.js layer as required.

| Option | Main deliverable | Complexity | Recommendation |
|---|---|---:|---|
| A | Script or notebook with saved charts | Low | Best first exercise |
| B | Python Streamlit dashboard | Medium | Best general student choice |
| C | FastAPI + Next.js full-stack app | High | Best when full-stack skills are a goal |

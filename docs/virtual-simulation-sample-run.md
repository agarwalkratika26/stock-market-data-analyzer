# Virtual Simulation and Sample Analysis Run

This document walks through a complete, verifiable execution of the **Stock Market Data Analyzer**, illustrating every phase of the pipeline using the included deterministic offline demo data.

---

## 1. Step-by-Step Simulated Walkthrough

### Step 1: Ingestion & Fallback Selection
- **Input Parameters**:
  - Symbol: `AAPL`
  - Period: 1 Year (252 business days)
  - Provider: `demo` (Synthetic Geometric Brownian Motion)
- **Execution Mechanism**:
  - The deterministic generator calculates a unique seed from `SHA256("AAPL")`.
  - Base price: \$361.67.
  - Generates 252 business days of daily prices with synthetic drift ($\mu = 0.00035$) and daily volatility ($\sigma = 0.018$).

### Step 2: Data Cleaning & Normalization
- Formats dates to standard `YYYY-MM-DD`.
- Confirms zero nulls across `open, high, low, close, volume`.
- Sorts rows in ascending chronological order.

### Step 3: Returns & Indicator Calculations
- **Daily Returns**: Percentage difference between consecutive closes.
- **Rolling Volatility**: 20-day rolling standard deviation of daily returns scaled by $\sqrt{252}$ to yield an annualized rate.
- **Moving Averages**: 20-day and 50-day Simple Moving Averages.
- **Wilder's RSI (14-period)**: Smoothed positive gains vs negative losses.
- **MACD**: 12-day EMA minus 26-day EMA; 9-day signal line.
- **Bollinger Bands**: 20-day SMA $\pm 2$ standard deviations.

### Step 4: Backtest Simulation
- **Strategy**: Long when `SMA 20 > SMA 50`, else Cash (0% position).
- **Execution Timing**: 1-bar execution delay (`shift(1)`) ensures decisions are acted on only after the close is finalized.
- **Friction**: 10 basis points (0.10%) deducted upon every rebalance trade.
- **Benchmark**: Buy-and-hold strategy starting with identical capital (\$10,000.00).

---

## 2. Actual Terminal Run Output (Verifiable)

Running command:
```powershell
python main.py --ticker AAPL --source demo
```

**Console Output Produced**:
```text
======================================================================
           STOCK MARKET DATA ANALYZER - EXECUTION PIPELINE           
======================================================================
[*] Target Ticker    : AAPL
[*] Provider Source  : demo
[*] Analysis Horizon : 2025-11-22 to 2026-11-22
[*] Moving Averages  : SMA 20 / SMA 50
----------------------------------------------------------------------

[+] Data Collection Succeeded: 252 sessions via 'demo (synthetic)'
    - First Close: $361.67 | Latest Close: $282.75
    - Period Cumulative Return: -21.82%
    - Annualized Volatility   : 27.78%
    - Price Extreme Range     : $271.83 (2026-11-17) to $400.78 (2026-04-06)
    - Trend Context           : SMA 20 (294.23) < SMA 50 (309.75) (bearish/negative trend context)
    - Descriptive Signal      : Momentum negative (MACD line is currently below its 9-day signal line.)

[+] Strategy Backtest Simulation Results (Initial Capital: $10,000.00):
    - Strategy Ending Equity  : $9,604.37 (-3.96%)
    - Benchmark Buy & Hold    : -21.82%
    - Annualized Return (CAGR): -3.96%
    - Maximum Drawdown        : -10.72%
    - Sharpe Ratio (Ann.)     : -0.22
    - Total Rebalance Trades  : 4

[+] Generated Output Artifacts:
    - Cleaned / Analyzed CSV  : outputs\AAPL\AAPL_analysis.csv
    - Markdown Summary Report : outputs\AAPL\summary_report.md
    - Visual Charts Saved     :
        * price_trend.png -> outputs\AAPL\price_trend.png
        * moving_averages.png -> outputs\AAPL\moving_averages.png
        * return_distribution.png -> outputs\AAPL\return_distribution.png
        * backtest_equity.png -> outputs\AAPL\backtest_equity.png
======================================================================
Analysis finished successfully. Open the markdown report or charts to view.
======================================================================
```

---

## 3. Screenshots and Artifacts for GitHub Upload

1. **`images/screenshots/dashboard-preview.svg`**: Preview of the Next.js full-stack interactive dashboard.
2. **`images/screenshots/backtest-preview.svg`**: Preview of the backtest simulation equity curve.
3. **`images/screenshots/price_trend.png`**: Generated historical closing price trendline.
4. **`images/screenshots/moving_averages.png`**: Generated moving averages with Bollinger Bands.
5. **`images/screenshots/return_distribution.png`**: Generated daily return histogram with KDE.
6. **`images/screenshots/backtest_equity.png`**: Generated strategy equity vs benchmark curve.
7. **`reports/AAPL_summary_report.md`**: Complete generated markdown analysis report.
8. **`data/processed/AAPL_analysis.csv`**: Analyzed dataset with all calculated technical columns.

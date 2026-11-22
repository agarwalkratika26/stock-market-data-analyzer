# 04 - Datasets and Sources

## 1. Synthetic Demo Generator (Offline Baseline)

### Mathematical Formulation
The offline demo provider generates reproducible synthetic equity prices using a **Geometric Brownian Motion (GBM)** process with deterministic parameterization derived from the ticker's SHA-256 hash.

1. **Deterministic Seed Generation**:
   $$\text{Seed} = \text{hex\_to\_int}(\text{SHA256}(\text{SYMBOL})[0:8])$$
2. **Deterministic Drift**:
   $$\mu = 0.00035 + \frac{\text{Seed} \pmod 8}{100,000}$$
3. **Log Returns Generation**:
   $$r_t \sim \mathcal{N}(\mu, \sigma = 0.018)$$
4. **Base Price Initialization**:
   $$S_0 = 45 + (\text{Seed} \pmod{350})$$
5. **Cumulative Price Series**:
   $$C_t = S_0 \cdot \exp\left(\sum_{i=1}^t r_i\right)$$
6. **Intraday Bar Simulation**:
   - $O_t = C_t \cdot (1 + \mathcal{N}(0, 0.004))$
   - $H_t = \max(O_t, C_t) \cdot (1 + \mathcal{U}(0.001, 0.012))$
   - $L_t = \min(O_t, C_t) \cdot (1 - \mathcal{U}(0.001, 0.012))$
   - $V_t \sim \mathcal{U}(1,000,000, 30,000,000)$

### Benefits
- **Zero Network Latency**: Enables instantaneous testing and automated test suites.
- **Offline Reproducibility**: Exact same curves generated across all OS platforms and runs for a given symbol.
- **Realistic Volatility**: Retains realistic financial properties: non-negative prices, log-normal distributions, and intraday high/low bounds.

---

## 2. Yahoo Finance Provider (`yfinance`)

- **Interface**: Uses `yfinance.download(symbol, period, auto_adjust=True)`.
- **Supported Periods**:
  - `1mo`: 23 trading sessions.
  - `3mo`: 66 trading sessions.
  - `6mo`: 132 trading sessions.
  - `1y`: 252 trading sessions.
  - `2y`: 504 trading sessions.
- **Adjusted Prices**: `auto_adjust=True` adjusts closing prices for stock splits and dividend distributions.
- **Edge Cases Handled**:
  - Multi-index column unraveling (introduced in newer yfinance versions).
  - Normalization of timezone-aware UTC timestamps into ISO-8601 strings (`YYYY-MM-DD`).

---

## 3. CSV Ingestion Provider

- **Storage Location**: `backend/data/prices/{SYMBOL}.csv`
- **Schema Specification**:
  ```csv
  date,open,high,low,close,volume
  2024-01-02,185.00,187.20,184.50,186.10,52000000
  2024-01-03,186.00,188.00,185.20,187.50,48000000
  ```
- **Validation Rules**:
  - Header case-insensitivity: mapped internally to lowercase.
  - Date column must parse valid ISO-8601 or standard date formats.
  - Must contain all 6 mandatory columns without missing records.

---

## 4. User Configuration & State Datasets

All persistent user assets are stored in JSON documents within `backend/data/`:
1. **`watchlist.json`**:
   Array of string ticker symbols: `["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]`.
2. **`portfolio.json`**:
   Holdings array containing `symbol`, `shares`, and `average_cost`.
3. **`alerts.json`**:
   Alert condition triggers containing `id`, `symbol`, `condition` (`price_above`, `price_below`, `rsi_above`, `rsi_below`), `threshold`, and `created_at`.

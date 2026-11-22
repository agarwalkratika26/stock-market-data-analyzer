# 06 - Verification and Validation Guide

This guide establishes the mandatory verification protocol required to validate every implementation step.

---

## 1. Quick Verification Commands (PowerShell)

### 1.1 Backend Health & Route Validation
Verify that the API server boots cleanly and reports the configured default data provider:
```powershell
# Health check
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method Get
```
**Expected Response**:
```json
{"status": "ok", "provider": "demo"}
```

### 1.2 Market Data & Indicator Sanity Check
Verify that the mathematical engine computes all indicators without `NaN` propagation on valid windows:
```powershell
# Fetch indicators for AAPL with demo provider
$res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/market/AAPL/indicators?period=6mo&provider=demo"
$res.signal
$res.data[-1]
```
**Expected Assertions**:
- `$res.signal.label` is a non-empty string (e.g. `"Momentum positive"`, `"Potentially overbought"`).
- `$res.data[-1].sma_20` is a valid floating point number.
- `$res.data[-1].rsi_14` is between $0.0$ and $100.0$.

### 1.3 Backtest Engine Verification
Validate that the backtester enforces window constraints and calculates non-zero performance metrics:
```powershell
$body = @{
    symbol = "AAPL"
    fast_window = 20
    slow_window = 50
    initial_cash = 10000
    transaction_cost_bps = 10
} | ConvertTo-Json

$bt = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/backtest" -Method Post -ContentType "application/json" -Body $body
$bt.metrics
```
**Expected Assertions**:
- `initial_cash == 10000`
- `ending_value > 0`
- `trade_count >= 0`
- `equity_curve` array matches bar count.

---

## 2. Automated Python Mathematical Verification Script

Run this test script directly inside `backend/` using python to verify indicator correctness independently of network servers:

```python
import numpy as np
import pandas as pd
from app.market_data import demo_history
from app.analytics import add_indicators, backtest

# 1. Test Demo Generation
df = demo_history("AAPL", days=132)
assert len(df) == 132, f"Expected 132 bars, got {len(df)}"
assert {"open", "high", "low", "close", "volume"}.issubset(df.columns)

# 2. Test Technical Indicators
enriched = add_indicators(df)
assert "sma_20" in enriched.columns
assert "rsi_14" in enriched.columns
assert enriched["rsi_14"].dropna().between(0, 100).all(), "RSI values out of bounds [0, 100]"

# 3. Test Backtest Logic
result = backtest(df, fast=20, slow=50, initial_cash=10000, cost_bps=10)
assert "metrics" in result
assert "equity_curve" in result
assert result["metrics"]["initial_cash"] == 10000
print("All mathematical validation checks passed successfully.")
```

---

## 3. Frontend Visual & Functional Checkpoints

When running the frontend:
1. **Header & Symbol Selector**: Switching between `AAPL`, `MSFT`, `NVDA`, `GOOGL`, and `AMZN` updates quotes immediately.
2. **Chart Rendering**: SVG candlestick bars and line overlays scale correctly within the viewport bounding box without clipping.
3. **Indicator Toggles**: Toggling `SMA 20`, `SMA 50`, `EMA 12`, `EMA 26`, and `Bollinger Bands` renders/unmounts corresponding SVG paths cleanly.
4. **Backtest Panel**: Adjusting Fast Window (e.g. 10) and Slow Window (e.g. 30) updates the equity curve and metrics table without unhandled promise rejections.

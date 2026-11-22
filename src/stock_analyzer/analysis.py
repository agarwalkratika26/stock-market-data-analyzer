"""Financial mathematics, technical indicators, descriptive signals, and backtesting."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd


def analyze_prices(
    prices: pd.DataFrame,
    fast_window: int = 20,
    slow_window: int = 50,
) -> pd.DataFrame:
    """Calculate returns, moving averages, technical indicators, and volatility.

    Parameters:
    - prices: DataFrame containing at least 'date' and 'close'.
    - fast_window: Window size for short-term SMA (default 20).
    - slow_window: Window size for long-term SMA (default 50).
    """
    if fast_window < 1 or slow_window < 1:
        raise ValueError("Moving average windows must be positive integers.")
    if fast_window >= slow_window:
        raise ValueError(f"Fast window ({fast_window}) must be strictly smaller than slow window ({slow_window}).")

    data = prices.copy().sort_values("date").reset_index(drop=True)
    close = data["close"].astype(float)

    # 1. Daily & Period Returns
    data["daily_return"] = close.pct_change()
    data["daily_return_pct"] = data["daily_return"] * 100
    data["cumulative_return_pct"] = ((close / close.iloc[0]) - 1) * 100

    # 2. Moving Averages
    fast_col = f"sma_{fast_window}"
    slow_col = f"sma_{slow_window}"
    data[fast_col] = close.rolling(window=fast_window, min_periods=fast_window).mean()
    data[slow_col] = close.rolling(window=slow_window, min_periods=slow_window).mean()

    # Exponential Moving Averages (12 & 26)
    data["ema_12"] = close.ewm(span=12, adjust=False).mean()
    data["ema_26"] = close.ewm(span=26, adjust=False).mean()

    # 3. MACD and Signal Line
    data["macd"] = data["ema_12"] - data["ema_26"]
    data["macd_signal"] = data["macd"].ewm(span=9, adjust=False).mean()
    data["macd_hist"] = data["macd"] - data["macd_signal"]

    # 4. Relative Strength Index (RSI - Wilder's smoothed method)
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    data["rsi_14"] = (100 - (100 / (1 + rs))).fillna(100).where(loss.notna(), np.nan)

    # 5. Bollinger Bands (20-period, 2 std deviations)
    bb_mid = close.rolling(20, min_periods=20).mean()
    bb_std = close.rolling(20, min_periods=20).std()
    data["bb_upper"] = bb_mid + 2 * bb_std
    data["bb_lower"] = bb_mid - 2 * bb_std
    data["bb_mid"] = bb_mid

    # 6. Volatility (20-day rolling annualized volatility)
    # Assumes standard 252 trading sessions per year: std * sqrt(252)
    data["volatility_20d_pct"] = (
        data["daily_return"].rolling(window=20, min_periods=10).std() * np.sqrt(252) * 100
    )

    return data


def _find_extreme(data: pd.DataFrame, column: str, fallback: str) -> Tuple[float, pd.Timestamp, str]:
    """Find the max or min price and its observed date and source column."""
    chosen = column if column in data.columns else fallback
    idx = data[chosen].idxmax() if column == "high" else data[chosen].idxmin()
    return float(data.loc[idx, chosen]), pd.Timestamp(data.loc[idx, "date"]), chosen


def evaluate_signal(row: pd.Series) -> Dict[str, Any]:
    """Generate a descriptive technical signal.

    Explicit disclaimer: Descriptive signal only; NOT financial advice or a trade recommendation.
    """
    rsi = row.get("rsi_14")
    macd = row.get("macd")
    macd_signal = row.get("macd_signal")

    if pd.notna(rsi) and rsi < 30:
        label = "Potentially oversold"
        reason = f"RSI-14 ({rsi:.1f}) is below 30 threshold."
    elif pd.notna(rsi) and rsi > 70:
        label = "Potentially overbought"
        reason = f"RSI-14 ({rsi:.1f}) is above 70 threshold."
    elif pd.notna(macd) and pd.notna(macd_signal) and macd > macd_signal:
        label = "Momentum positive"
        reason = "MACD line is currently above its 9-day signal line."
    elif pd.notna(macd) and pd.notna(macd_signal):
        label = "Momentum negative"
        reason = "MACD line is currently below its 9-day signal line."
    else:
        label = "Neutral / Insufficient Data"
        reason = "More historical price observations are required to determine indicator state."

    return {
        "label": label,
        "reason": reason,
        "rsi_14": round(float(rsi), 2) if pd.notna(rsi) else None,
        "macd": round(float(macd), 4) if pd.notna(macd) else None,
        "macd_signal": round(float(macd_signal), 4) if pd.notna(macd_signal) else None,
    }


def build_summary(
    data: pd.DataFrame,
    ticker: str,
    source: str,
    fast_window: int = 20,
    slow_window: int = 50,
) -> Dict[str, Any]:
    """Build factual summary metrics from analyzed price data."""
    clean = data.dropna(subset=["close"]).copy()
    first_close = float(clean["close"].iloc[0])
    last_close = float(clean["close"].iloc[-1])
    total_return_pct = ((last_close / first_close) - 1) * 100 if first_close else 0.0

    daily_returns = clean["daily_return"].dropna()
    ann_volatility_pct = float(daily_returns.std() * np.sqrt(252) * 100) if len(daily_returns) > 1 else 0.0

    fast_name, slow_name = f"sma_{fast_window}", f"sma_{slow_window}"
    fast_latest = clean[fast_name].dropna()
    slow_latest = clean[slow_name].dropna()

    if not fast_latest.empty and not slow_latest.empty:
        fast_val, slow_val = float(fast_latest.iloc[-1]), float(slow_latest.iloc[-1])
        if fast_val > slow_val:
            trend = f"SMA {fast_window} ({fast_val:.2f}) > SMA {slow_window} ({slow_val:.2f}) (bullish/positive trend context)"
        elif fast_val < slow_val:
            trend = f"SMA {fast_window} ({fast_val:.2f}) < SMA {slow_window} ({slow_val:.2f}) (bearish/negative trend context)"
        else:
            trend = "Fast and slow moving averages are converging at current observation."
    else:
        fast_val = slow_val = None
        trend = "Insufficient observations to calculate both moving averages."

    high_val, high_date, high_field = _find_extreme(clean, "high", "close")
    low_val, low_date, low_field = _find_extreme(clean, "low", "close")

    latest_row = clean.iloc[-1]
    signal_info = evaluate_signal(latest_row)

    pos_sessions = int((daily_returns > 0).sum())
    neg_sessions = int((daily_returns < 0).sum())

    return {
        "ticker": ticker.upper(),
        "source": source,
        "start_date": pd.Timestamp(clean["date"].iloc[0]).date().isoformat(),
        "end_date": pd.Timestamp(clean["date"].iloc[-1]).date().isoformat(),
        "observations": int(len(clean)),
        "first_close": round(first_close, 2),
        "latest_close": round(last_close, 2),
        "period_return_pct": round(total_return_pct, 2),
        "annualized_volatility_pct": round(ann_volatility_pct, 2),
        "highest_price": round(high_val, 2),
        "highest_price_date": high_date.date().isoformat(),
        "highest_price_field": high_field,
        "lowest_price": round(low_val, 2),
        "lowest_price_date": low_date.date().isoformat(),
        "lowest_price_field": low_field,
        "fast_window": fast_window,
        "slow_window": slow_window,
        "fast_average": round(fast_val, 2) if fast_val is not None else None,
        "slow_average": round(slow_val, 2) if slow_val is not None else None,
        "trend": trend,
        "signal": signal_info,
        "best_daily_return_pct": round(float(daily_returns.max() * 100), 2) if len(daily_returns) else None,
        "worst_daily_return_pct": round(float(daily_returns.min() * 100), 2) if len(daily_returns) else None,
        "positive_sessions": pos_sessions,
        "negative_sessions": neg_sessions,
    }


def run_backtest(
    prices: pd.DataFrame,
    fast_window: int = 20,
    slow_window: int = 50,
    initial_cash: float = 10000.0,
    transaction_cost_bps: float = 10.0,
) -> Dict[str, Any]:
    """Execute a simple Moving Average Crossover simulation.

    Key Implementation Guarantees:
    - Shift position by 1 bar: Today's position is based on yesterday's close/signal, eliminating lookahead bias.
    - Transaction cost friction applied on position changes (in basis points: 10 bps = 0.10%).
    - Comparison against buy-and-hold benchmark.
    """
    if fast_window >= slow_window:
        raise ValueError("fast_window must be strictly smaller than slow_window.")
    if initial_cash <= 0:
        raise ValueError("initial_cash must be positive.")

    data = prices[["date", "close"]].copy().dropna().sort_values("date").reset_index(drop=True)
    fast_col = f"sma_{fast_window}"
    slow_col = f"sma_{slow_window}"

    data["fast"] = data["close"].rolling(fast_window).mean()
    data["slow"] = data["close"].rolling(slow_window).mean()

    # Position signal: 1 if fast > slow else 0 (long or cash)
    raw_signal = (data["fast"] > data["slow"]).astype(float)

    # Shift by 1 bar: Lookahead bias elimination
    data["position"] = raw_signal.shift(1).fillna(0.0)

    data["market_return"] = data["close"].pct_change().fillna(0.0)
    data["turnover"] = data["position"].diff().abs().fillna(data["position"])

    cost_pct = transaction_cost_bps / 10_000.0
    data["strategy_return"] = data["position"] * data["market_return"] - (data["turnover"] * cost_pct)

    data["equity"] = initial_cash * (1 + data["strategy_return"]).cumprod()
    data["benchmark"] = initial_cash * (1 + data["market_return"]).cumprod()

    # Metrics
    ending_equity = float(data["equity"].iloc[-1])
    total_return = (ending_equity / initial_cash) - 1.0
    years = max(len(data) / 252.0, 1.0 / 252.0)
    cagr = ((ending_equity / initial_cash) ** (1.0 / years)) - 1.0

    running_peak = data["equity"].cummax()
    drawdown = (data["equity"] / running_peak) - 1.0
    max_drawdown = float(drawdown.min())

    vol = float(data["strategy_return"].std() * np.sqrt(252))
    sharpe = float((data["strategy_return"].mean() * 252) / vol) if vol > 0 else 0.0

    benchmark_ending = float(data["benchmark"].iloc[-1])
    benchmark_return = (benchmark_ending / initial_cash) - 1.0

    equity_curve = [
        {
            "date": pd.Timestamp(row.date).strftime("%Y-%m-%d"),
            "strategy": round(float(row.equity), 2),
            "benchmark": round(float(row.benchmark), 2),
            "position": int(row.position),
        }
        for row in data.itertuples()
    ]

    return {
        "metrics": {
            "initial_cash": round(initial_cash, 2),
            "ending_value": round(ending_equity, 2),
            "total_return_pct": round(total_return * 100, 2),
            "cagr_pct": round(cagr * 100, 2),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            "sharpe_ratio": round(sharpe, 2),
            "buy_and_hold_pct": round(benchmark_return * 100, 2),
            "trade_count": int(data["turnover"].sum()),
            "fast_window": fast_window,
            "slow_window": slow_window,
            "transaction_cost_bps": transaction_cost_bps,
        },
        "equity_curve": equity_curve,
        "assumptions": [
            "Long or cash allocation; no margin, shorting, or leverage.",
            "Signals execute on the next bar's close/open (shifted by 1 bar to prevent lookahead bias).",
            f"Transaction cost modeled at {transaction_cost_bps:g} basis points per turnover.",
            "Historical simulation excludes taxes, market impact, borrow fees, and dividend cash adjustments.",
            "Past backtested performance is educational and does NOT guarantee future market results.",
        ],
    }

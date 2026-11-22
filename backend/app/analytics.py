import numpy as np
import pandas as pd


def add_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    close = data["close"].astype(float)
    data["sma_20"] = close.rolling(20).mean()
    data["sma_50"] = close.rolling(50).mean()
    data["ema_12"] = close.ewm(span=12, adjust=False).mean()
    data["ema_26"] = close.ewm(span=26, adjust=False).mean()
    data["macd"] = data["ema_12"] - data["ema_26"]
    data["macd_signal"] = data["macd"].ewm(span=9, adjust=False).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    data["rsi_14"] = (100 - 100 / (1 + rs)).fillna(100).where(loss.notna(), np.nan)
    mid = close.rolling(20).mean()
    std = close.rolling(20).std()
    data["bb_upper"] = mid + 2 * std
    data["bb_lower"] = mid - 2 * std
    return data


def current_signal(row: pd.Series) -> dict:
    rsi = row.get("rsi_14")
    macd, macd_signal = row.get("macd"), row.get("macd_signal")
    if pd.notna(rsi) and rsi < 30:
        label, reason = "Potentially oversold", "RSI is below 30"
    elif pd.notna(rsi) and rsi > 70:
        label, reason = "Potentially overbought", "RSI is above 70"
    elif pd.notna(macd) and pd.notna(macd_signal) and macd > macd_signal:
        label, reason = "Momentum positive", "MACD is above its signal line"
    elif pd.notna(macd) and pd.notna(macd_signal):
        label, reason = "Momentum negative", "MACD is below its signal line"
    else:
        label, reason = "Not enough data", "More price history is needed to calculate indicators"
    return {"label": label, "reason": reason, "rsi_14": round(float(rsi), 2) if pd.notna(rsi) else None}


def backtest(frame: pd.DataFrame, fast: int = 20, slow: int = 50, initial_cash: float = 10000, cost_bps: float = 10) -> dict:
    if fast >= slow:
        raise ValueError("fast_window must be smaller than slow_window")
    data = frame[["date", "close"]].copy().dropna()
    data["fast"] = data["close"].rolling(fast).mean()
    data["slow"] = data["close"].rolling(slow).mean()
    # Shift by one bar: today's close cannot be traded before it is observed.
    data["position"] = (data["fast"] > data["slow"]).astype(float).shift(1).fillna(0)
    data["market_return"] = data["close"].pct_change().fillna(0)
    data["turnover"] = data["position"].diff().abs().fillna(data["position"])
    data["strategy_return"] = data["position"] * data["market_return"] - data["turnover"] * cost_bps / 10_000
    data["equity"] = initial_cash * (1 + data["strategy_return"]).cumprod()
    data["benchmark"] = initial_cash * (1 + data["market_return"]).cumprod()
    running_peak = data["equity"].cummax()
    max_drawdown = (data["equity"] / running_peak - 1).min()
    total_return = data["equity"].iloc[-1] / initial_cash - 1
    years = max(len(data) / 252, 1 / 252)
    cagr = (data["equity"].iloc[-1] / initial_cash) ** (1 / years) - 1
    volatility = data["strategy_return"].std() * np.sqrt(252)
    sharpe = (data["strategy_return"].mean() * 252) / volatility if volatility else 0
    return {
        "metrics": {"initial_cash": round(initial_cash, 2), "ending_value": round(float(data["equity"].iloc[-1]), 2),
                    "total_return_pct": round(float(total_return * 100), 2), "cagr_pct": round(float(cagr * 100), 2),
                    "max_drawdown_pct": round(float(max_drawdown * 100), 2), "sharpe_ratio": round(float(sharpe), 2),
                    "buy_and_hold_pct": round(float((data["benchmark"].iloc[-1] / initial_cash - 1) * 100), 2),
                    "trade_count": int(data["turnover"].sum())},
        "equity_curve": [{"date": pd.Timestamp(row.date).strftime("%Y-%m-%d"), "strategy": round(float(row.equity), 2), "benchmark": round(float(row.benchmark), 2)} for row in data.itertuples()],
        "assumptions": ["Long or cash; no leverage or shorting", "Signals execute on the next bar", f"Transaction cost: {cost_bps:g} basis points per position change", "Historical simulation; excludes taxes, slippage, and survivorship bias"],
    }

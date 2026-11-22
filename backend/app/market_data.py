from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from .config import settings


VALID_PERIODS = {"1mo": 23, "3mo": 66, "6mo": 132, "1y": 252, "2y": 504}


def demo_history(symbol: str, days: int = 252) -> pd.DataFrame:
    """Create reproducible OHLCV bars for an offline, clearly labeled demo."""
    seed = int(hashlib.sha256(symbol.upper().encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.now().normalize(), periods=days)
    drift = 0.00035 + (seed % 8) / 100_000
    returns = rng.normal(drift, 0.018, len(dates))
    base = 45 + seed % 350
    close = base * np.exp(np.cumsum(returns))
    open_ = close * (1 + rng.normal(0, 0.004, len(dates)))
    high = np.maximum(open_, close) * (1 + rng.uniform(0.001, 0.012, len(dates)))
    low = np.minimum(open_, close) * (1 - rng.uniform(0.001, 0.012, len(dates)))
    volume = rng.integers(1_000_000, 30_000_000, len(dates))
    return pd.DataFrame({"date": dates, "open": open_, "high": high, "low": low, "close": close, "volume": volume})


def history(symbol: str, period: str = "6mo", provider: str | None = None) -> tuple[pd.DataFrame, str]:
    symbol = symbol.upper().strip()
    provider = (provider or settings.default_provider).lower()
    if provider not in {"demo", "yfinance", "csv"}:
        raise ValueError("provider must be demo, yfinance, or csv")
    if period not in VALID_PERIODS:
        raise ValueError(f"period must be one of {', '.join(VALID_PERIODS)}")
    if provider == "demo":
        return demo_history(symbol, VALID_PERIODS[period]), "demo"
    if provider == "csv":
        path = settings.data_dir / "prices" / f"{symbol}.csv"
        if not path.exists():
            raise FileNotFoundError(f"No CSV found at {path}; add a file named {symbol}.csv")
        frame = pd.read_csv(path)
        required = {"date", "open", "high", "low", "close", "volume"}
        if not required.issubset({column.lower() for column in frame.columns}):
            raise ValueError("CSV must include date, open, high, low, close, volume columns")
        frame.columns = [column.lower() for column in frame.columns]
        frame["date"] = pd.to_datetime(frame["date"])
        return frame.sort_values("date").tail(VALID_PERIODS[period]).reset_index(drop=True), "csv"
    try:
        import yfinance as yf

        frame = yf.download(symbol, period=period, auto_adjust=True, progress=False, threads=False)
        if frame.empty:
            raise ValueError(f"Yahoo Finance returned no history for {symbol}")
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = frame.columns.get_level_values(0)
        frame = frame.reset_index()
        frame.columns = [str(column).lower() for column in frame.columns]
        frame = frame.rename(columns={"datetime": "date"})
        frame["date"] = pd.to_datetime(frame["date"])
        return frame[["date", "open", "high", "low", "close", "volume"]].dropna(), "yfinance"
    except Exception as exc:
        raise RuntimeError(f"Could not fetch {symbol} from Yahoo Finance: {exc}") from exc


def frame_records(frame: pd.DataFrame) -> list[dict]:
    rows = frame.copy()
    rows["date"] = pd.to_datetime(rows["date"]).dt.strftime("%Y-%m-%d")
    return rows.replace({np.nan: None}).to_dict(orient="records")

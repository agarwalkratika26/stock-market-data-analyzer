"""Data collection, cleaning, and normalization module."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


class DataLoadError(Exception):
    """Raised when no usable stock price data can be loaded or validated."""


def demo_history(ticker: str, days: int = 252) -> pd.DataFrame:
    """Generate reproducible, deterministic daily price bars for an offline demo.

    Uses a Geometric Brownian Motion model seeded with the SHA-256 hash of the ticker symbol.
    Prominently labeled as synthetic demo data.
    """
    seed = int(hashlib.sha256(ticker.upper().encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.now().normalize(), periods=days)
    drift = 0.00035 + (seed % 8) / 100_000
    returns = rng.normal(drift, 0.018, len(dates))
    base = 45.0 + (seed % 350)
    close = base * np.exp(np.cumsum(returns))
    open_ = close * (1 + rng.normal(0, 0.004, len(dates)))
    high = np.maximum(open_, close) * (1 + rng.uniform(0.001, 0.012, len(dates)))
    low = np.minimum(open_, close) * (1 - rng.uniform(0.001, 0.012, len(dates)))
    volume = rng.integers(1_000_000, 30_000_000, len(dates))

    return pd.DataFrame({
        "date": dates,
        "open": np.round(open_, 2),
        "high": np.round(high, 2),
        "low": np.round(low, 2),
        "close": np.round(close, 2),
        "volume": volume,
    })


def clean_prices(frame: pd.DataFrame) -> pd.DataFrame:
    """Clean, normalize, and sort price data.

    Accepts any DataFrame with 'date' and 'close'. Handles optional 'open', 'high',
    'low', 'volume' when present. Drops malformed rows, removes duplicates, and sorts
    chronologically.
    """
    if frame is None or frame.empty:
        raise DataLoadError("The selected data source returned no rows.")

    data = frame.copy()

    # Flatten MultiIndex columns (common in newer yfinance releases)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data.columns = [str(col).strip().lower() for col in data.columns]
    data = data.rename(columns={"datetime": "date", "timestamp": "date", "adj close": "close"})

    if "date" not in data.columns:
        data = data.reset_index()
        data.columns = [str(col).strip().lower() for col in data.columns]
        data = data.rename(columns={"datetime": "date", "timestamp": "date"})

    missing = {"date", "close"} - set(data.columns)
    if missing:
        raise DataLoadError(f"Price data is missing required column(s): {', '.join(sorted(missing))}")

    # Standardize date to timezone-naive datetime
    data["date"] = pd.to_datetime(data["date"], errors="coerce", utc=True).dt.tz_convert(None)

    # Coerce numeric fields
    for col in ["open", "high", "low", "close", "volume"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    # Clean missing, non-positive, duplicate dates
    data = data.dropna(subset=["date", "close"])
    data = data[data["close"] > 0]
    data = data.drop_duplicates(subset="date", keep="last")
    data = data.sort_values("date").reset_index(drop=True)

    if data.empty:
        raise DataLoadError("No valid rows remain after cleaning dates and closing prices.")

    # Reorder columns with core fields first
    core = [c for c in ["date", "open", "high", "low", "close", "volume"] if c in data.columns]
    extra = [c for c in data.columns if c not in core]
    return data[core + extra]


def _filter_dates(data: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    """Filter records by start and end date (inclusive)."""
    filtered = data
    if start:
        filtered = filtered[filtered["date"] >= pd.Timestamp(start)]
    if end:
        filtered = filtered[filtered["date"] <= pd.Timestamp(end)]
    if filtered.empty:
        raise DataLoadError(f"No price records fall within date range [{start} to {end}].")
    return filtered.reset_index(drop=True)


def load_csv(csv_path: str | Path, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Load historical prices from a CSV file. Comment lines starting with '#' are ignored."""
    path = Path(csv_path).expanduser().resolve()
    if not path.exists():
        raise DataLoadError(f"CSV file not found at: {path}")
    try:
        frame = pd.read_csv(path, comment="#")
        return _filter_dates(clean_prices(frame), start, end)
    except Exception as exc:
        raise DataLoadError(f"Could not load or parse CSV ({path}): {exc}") from exc


def load_yfinance(ticker: str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Fetch historical stock data from Yahoo Finance."""
    try:
        import yfinance as yf
    except ImportError as exc:
        raise DataLoadError("yfinance library is not installed. Install requirements first.") from exc

    try:
        # yfinance end date is exclusive; pad by 1 day
        end_exclusive = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d") if end else None
        frame = yf.download(
            ticker.upper(),
            start=start,
            end=end_exclusive,
            auto_adjust=True,
            progress=False,
            threads=False,
        )
    except Exception as exc:
        raise DataLoadError(f"Yahoo Finance request failed for {ticker.upper()}: {exc}") from exc

    if frame is None or frame.empty:
        raise DataLoadError(f"Yahoo Finance returned no data for ticker {ticker.upper()}.")

    return _filter_dates(clean_prices(frame), start, end)


def load_prices(
    ticker: str,
    start: str | None = None,
    end: str | None = None,
    source: str = "auto",
    csv_path: str | Path | None = None,
) -> Tuple[pd.DataFrame, str]:
    """Load stock data from specified source with automatic fallbacks.

    Sources supported:
    - 'demo': Deterministic synthetic data (ideal for offline, classroom, or test runs).
    - 'yfinance': Public Yahoo Finance historical data.
    - 'csv': Local CSV file.
    - 'auto': Attempts Yahoo Finance -> falls back to CSV -> falls back to demo.
    """
    source = source.lower().strip()
    ticker = ticker.strip().upper()

    if source == "demo":
        df = demo_history(ticker, days=252)
        return _filter_dates(df, start, end), "demo (synthetic)"

    if source == "csv":
        path = Path(csv_path) if csv_path else Path("data/raw") / f"{ticker}.csv"
        return load_csv(path, start, end), "csv"

    if source == "yfinance":
        return load_yfinance(ticker, start, end), "yfinance"

    if source == "auto":
        # 1. Try Yahoo Finance
        try:
            return load_yfinance(ticker, start, end), "yfinance"
        except Exception:
            pass

        # 2. Try CSV Fallback in data/raw or backend/data/prices or explicit path
        search_paths = []
        if csv_path:
            search_paths.append(Path(csv_path))
        search_paths.extend([
            Path("data/raw") / f"{ticker}.csv",
            Path("backend/data/prices") / f"{ticker}.csv",
            Path("data/raw/DEMO.csv"),
        ])
        for p in search_paths:
            if p.exists():
                try:
                    return load_csv(p, start, end), f"csv fallback ({p.name})"
                except Exception:
                    continue

        # 3. Fallback to deterministic synthetic demo
        df = demo_history(ticker, days=252)
        return _filter_dates(df, start, end), "synthetic demo (offline fallback)"

    raise DataLoadError(f"Unsupported source '{source}'. Use 'auto', 'yfinance', 'csv', or 'demo'.")

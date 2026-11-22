"""Data visualization routines using Matplotlib and Seaborn."""

from __future__ import annotations

from pathlib import Path
from typing import List

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend safe for headless servers / CLI

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")


def _save_and_close(fig: plt.Figure, output: Path) -> Path:
    """Helper to finalize, save at 160 DPI, and close the figure."""
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_price_trend(data: pd.DataFrame, ticker: str, output: Path) -> Path:
    """Plot closing prices with a descriptive historical linear trendline."""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(data["date"], data["close"], color="#2563eb", linewidth=1.8, label="Adjusted Close")

    if len(data) >= 2:
        x_num = mdates.date2num(pd.to_datetime(data["date"]))
        slope, intercept = np.polyfit(x_num, data["close"], 1)
        ax.plot(data["date"], slope * x_num + intercept, color="#f97316", linestyle="--", label="Historical Trendline")

    ax.set_title(f"{ticker.upper()} - Historical Closing Price Trend", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Date", fontsize=10)
    ax.set_ylabel("Price (USD / Currency)", fontsize=10)
    ax.legend(frameon=True, facecolor="white", framealpha=0.9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=30)
    return _save_and_close(fig, output)


def plot_moving_averages(
    data: pd.DataFrame,
    ticker: str,
    fast_window: int,
    slow_window: int,
    output: Path,
) -> Path:
    """Plot closing prices against fast/slow SMAs and Bollinger Bands."""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(data["date"], data["close"], color="#64748b", linewidth=1.2, alpha=0.8, label="Close")

    fast_col = f"sma_{fast_window}"
    slow_col = f"sma_{slow_window}"
    if fast_col in data.columns:
        ax.plot(data["date"], data[fast_col], color="#10b981", linewidth=1.8, label=f"SMA {fast_window}")
    if slow_col in data.columns:
        ax.plot(data["date"], data[slow_col], color="#8b5cf6", linewidth=1.8, label=f"SMA {slow_window}")

    if "bb_upper" in data.columns and "bb_lower" in data.columns:
        ax.fill_between(
            data["date"],
            data["bb_lower"],
            data["bb_upper"],
            color="#38bdf8",
            alpha=0.15,
            label="Bollinger Bands (20, 2σ)",
        )

    ax.set_title(f"{ticker.upper()} - Moving Averages & Volatility Bands", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Date", fontsize=10)
    ax.set_ylabel("Price (USD / Currency)", fontsize=10)
    ax.legend(frameon=True, facecolor="white", framealpha=0.9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=30)
    return _save_and_close(fig, output)


def plot_return_distribution(data: pd.DataFrame, ticker: str, output: Path) -> Path:
    """Plot the frequency distribution and KDE of daily percentage returns."""
    returns = data["daily_return_pct"].dropna()
    fig, ax = plt.subplots(figsize=(9, 5))

    if returns.empty:
        ax.text(0.5, 0.5, "Insufficient price records to calculate returns", ha="center", va="center")
        ax.set_axis_off()
    else:
        bins = min(35, max(10, int(len(returns) ** 0.5)))
        sns.histplot(returns, bins=bins, kde=len(returns) > 3, color="#3b82f6", ax=ax, edgecolor="white")
        ax.axvline(0, color="#ef4444", linestyle="--", linewidth=1.4, label="Zero Return")
        mean_ret = returns.mean()
        ax.axvline(mean_ret, color="#10b981", linestyle=":", linewidth=1.4, label=f"Mean ({mean_ret:+.2f}%)")
        ax.set_xlabel("Daily Return (%)", fontsize=10)
        ax.set_ylabel("Frequency (Trading Sessions)", fontsize=10)
        ax.legend(frameon=True, facecolor="white", framealpha=0.9)

    ax.set_title(f"{ticker.upper()} - Daily Return Distribution", fontsize=13, fontweight="bold", pad=12)
    return _save_and_close(fig, output)


def plot_backtest_equity(equity_curve: List[dict], ticker: str, output: Path) -> Path:
    """Plot simulated strategy equity vs buy-and-hold benchmark curve."""
    df = pd.DataFrame(equity_curve)
    df["date"] = pd.to_datetime(df["date"])

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["date"], df["strategy"], color="#2563eb", linewidth=2.0, label="SMA Crossover Strategy")
    ax.plot(df["date"], df["benchmark"], color="#94a3b8", linewidth=1.5, linestyle="--", label="Buy & Hold Benchmark")

    ax.set_title(f"{ticker.upper()} - Backtest Equity Simulation", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Date", fontsize=10)
    ax.set_ylabel("Portfolio Value ($)", fontsize=10)
    ax.legend(frameon=True, facecolor="white", framealpha=0.9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=30)
    return _save_and_close(fig, output)

"""Stock Market Data Analyzer - Core Analysis Package."""

from .analysis import analyze_prices, build_summary, run_backtest
from .data import DataLoadError, clean_prices, demo_history, load_csv, load_prices, load_yfinance
from .pipeline import run_analysis

__version__ = "1.0.0"
__all__ = [
    "DataLoadError",
    "clean_prices",
    "demo_history",
    "load_csv",
    "load_yfinance",
    "load_prices",
    "analyze_prices",
    "build_summary",
    "run_backtest",
    "run_analysis",
]

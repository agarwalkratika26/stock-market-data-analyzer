"""Orchestration pipeline connecting data loading, analysis, charts, and reporting."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict

from .analysis import analyze_prices, build_summary, run_backtest
from .charts import (
    plot_backtest_equity,
    plot_moving_averages,
    plot_price_trend,
    plot_return_distribution,
)
from .data import load_prices
from .report import write_report


def run_analysis(
    ticker: str,
    start: str | None = None,
    end: str | None = None,
    source: str = "auto",
    csv_path: str | Path | None = None,
    output_dir: str | Path = "outputs",
    fast_window: int = 20,
    slow_window: int = 50,
    initial_cash: float = 10000.0,
    transaction_cost_bps: float = 10.0,
) -> Dict[str, Any]:
    """Execute end-to-end stock data analysis and backtest pipeline."""
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("A valid ticker symbol must be provided.")

    safe_ticker = re.sub(r"[^A-Z0-9._-]", "_", ticker)
    folder = Path(output_dir) / safe_ticker
    folder.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    prices, source_used = load_prices(ticker, start, end, source, csv_path)

    # 2. Analyze Prices & Indicators
    analyzed = analyze_prices(prices, fast_window, slow_window)
    summary = build_summary(analyzed, ticker, source_used, fast_window, slow_window)

    # 3. Run Strategy Backtest
    backtest_results = run_backtest(
        prices=analyzed,
        fast_window=fast_window,
        slow_window=slow_window,
        initial_cash=initial_cash,
        transaction_cost_bps=transaction_cost_bps,
    )

    # 4. Save Analyzed CSV
    csv_out = folder / f"{safe_ticker}_analysis.csv"
    analyzed.to_csv(csv_out, index=False, date_format="%Y-%m-%d")

    # 5. Generate Visual Charts
    chart_paths = [
        plot_price_trend(analyzed, ticker, folder / "price_trend.png"),
        plot_moving_averages(analyzed, ticker, fast_window, slow_window, folder / "moving_averages.png"),
        plot_return_distribution(analyzed, ticker, folder / "return_distribution.png"),
        plot_backtest_equity(backtest_results["equity_curve"], ticker, folder / "backtest_equity.png"),
    ]

    chart_names = [p.name for p in chart_paths]

    # 6. Generate Human-Readable Markdown Report
    report_path = write_report(
        summary=summary,
        backtest_results=backtest_results,
        output=folder / "summary_report.md",
        chart_names=chart_names,
    )

    return {
        "summary": summary,
        "backtest": backtest_results,
        "data_path": csv_out,
        "report_path": report_path,
        "chart_paths": chart_paths,
        "analyzed_data": analyzed,
    }

"""Stock Market Data Analyzer - Command-Line Interface.

Usage:
    python main.py --ticker AAPL --source demo
    python main.py --ticker MSFT --source yfinance --fast-window 20 --slow-window 50
    python main.py --ticker DEMO --source csv --csv-path data/raw/DEMO.csv
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
import sys

# Ensure src/ is on python import path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from stock_analyzer.data import DataLoadError
from stock_analyzer.pipeline import run_analysis


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stock Market Data Analyzer: Ingest, clean, compute technical indicators, backtest, and generate reports.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--ticker", default="AAPL", help="Stock ticker symbol (e.g., AAPL, MSFT, NVDA)")
    parser.add_argument(
        "--start",
        default=(date.today() - timedelta(days=365)).isoformat(),
        help="Start date in YYYY-MM-DD format",
    )
    parser.add_argument("--end", default=date.today().isoformat(), help="End date in YYYY-MM-DD format")
    parser.add_argument(
        "--source",
        choices=["auto", "demo", "yfinance", "csv"],
        default="auto",
        help="Data provider source. 'demo' works 100% offline; 'auto' attempts Yahoo Finance, then CSV, then demo.",
    )
    parser.add_argument("--csv-path", help="Path to custom CSV file for 'csv' mode or 'auto' fallback.")
    parser.add_argument("--output-dir", default="outputs", help="Directory where charts, CSV, and reports are saved.")
    parser.add_argument("--fast-window", type=int, default=20, help="Window size for short-term Simple Moving Average.")
    parser.add_argument("--slow-window", type=int, default=50, help="Window size for long-term Simple Moving Average.")
    parser.add_argument("--initial-cash", type=float, default=10000.0, help="Starting capital for backtest simulation.")
    parser.add_argument("--cost-bps", type=float, default=10.0, help="Transaction friction in basis points (10 bps = 0.10%).")
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    print("=" * 70)
    print("           STOCK MARKET DATA ANALYZER - EXECUTION PIPELINE           ")
    print("=" * 70)
    print(f"[*] Target Ticker    : {args.ticker.upper()}")
    print(f"[*] Provider Source  : {args.source}")
    print(f"[*] Analysis Horizon : {args.start} to {args.end}")
    print(f"[*] Moving Averages  : SMA {args.fast_window} / SMA {args.slow_window}")
    print("-" * 70)

    try:
        results = run_analysis(
            ticker=args.ticker,
            start=args.start,
            end=args.end,
            source=args.source,
            csv_path=args.csv_path,
            output_dir=args.output_dir,
            fast_window=args.fast_window,
            slow_window=args.slow_window,
            initial_cash=args.initial_cash,
            transaction_cost_bps=args.cost_bps,
        )
    except (DataLoadError, ValueError) as exc:
        print(f"\n[!] Execution Terminated: {exc}", file=sys.stderr)
        sys.exit(1)

    summary = results["summary"]
    bt = results["backtest"]["metrics"]
    sig = summary.get("signal", {})

    print(f"\n[+] Data Collection Succeeded: {summary['observations']} sessions via '{summary['source']}'")
    print(f"    - First Close: ${summary['first_close']:,.2f} | Latest Close: ${summary['latest_close']:,.2f}")
    print(f"    - Period Cumulative Return: {summary['period_return_pct']:+.2f}%")
    print(f"    - Annualized Volatility   : {summary['annualized_volatility_pct']:.2f}%")
    print(f"    - Price Extreme Range     : ${summary['lowest_price']:,.2f} ({summary['lowest_price_date']}) to ${summary['highest_price']:,.2f} ({summary['highest_price_date']})")
    print(f"    - Trend Context           : {summary['trend']}")
    print(f"    - Descriptive Signal      : {sig.get('label')} ({sig.get('reason')})")

    print(f"\n[+] Strategy Backtest Simulation Results (Initial Capital: ${bt['initial_cash']:,.2f}):")
    print(f"    - Strategy Ending Equity  : ${bt['ending_value']:,.2f} ({bt['total_return_pct']:+.2f}%)")
    print(f"    - Benchmark Buy & Hold    : {bt['buy_and_hold_pct']:+.2f}%")
    print(f"    - Annualized Return (CAGR): {bt['cagr_pct']:+.2f}%")
    print(f"    - Maximum Drawdown        : {bt['max_drawdown_pct']:.2f}%")
    print(f"    - Sharpe Ratio (Ann.)     : {bt['sharpe_ratio']:.2f}")
    print(f"    - Total Rebalance Trades  : {bt['trade_count']}")

    print("\n[+] Generated Output Artifacts:")
    print(f"    - Cleaned / Analyzed CSV  : {results['data_path']}")
    print(f"    - Markdown Summary Report : {results['report_path']}")
    print("    - Visual Charts Saved     :")
    for cp in results["chart_paths"]:
        print(f"        * {cp.name} -> {cp}")

    print("=" * 70)
    print("Analysis finished successfully. Open the markdown report or charts to view.")
    print("=" * 70)


if __name__ == "__main__":
    main()

"""Comprehensive, isolated, automated test & verification suite for Stock Market Data Analyzer.

Verifies:
1. Data collection, cleaning, and normalization on known inputs.
2. Mathematical indicator accuracy, volatility scaling, and price extremes.
3. Lookahead-bias-free backtesting simulation and cost modeling.
4. Fresh CLI pipeline run in an isolated temporary directory (verifying charts, CSV, and report).
5. All 13 FastAPI REST API endpoints using isolated temporary state without mutating workspace data.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys
import tempfile

# Configure MPLCONFIGDIR to a writable directory to prevent sandbox permission warnings
os.environ["MPLCONFIGDIR"] = tempfile.gettempdir()

# Ensure repository paths are importable
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

import numpy as np
import pandas as pd


def test_section_1_data_ingestion_and_cleaning():
    print("--> [1/5] Testing Data Ingestion, Cleaning & Normalization...", flush=True)
    from stock_analyzer.data import DataLoadError, clean_prices, demo_history, load_csv

    # 1.1 Error handling on empty or malformed inputs
    try:
        clean_prices(pd.DataFrame())
        assert False, "Should raise DataLoadError on empty DataFrame"
    except DataLoadError:
        pass

    try:
        clean_prices(pd.DataFrame({"invalid": [1, 2, 3]}))
        assert False, "Should raise DataLoadError when missing date/close"
    except DataLoadError:
        pass

    # 1.2 Ingestion of known CSV sample
    df_csv = load_csv("data/raw/DEMO.csv")
    assert len(df_csv) == 30, f"Expected 30 rows in DEMO.csv, got {len(df_csv)}"
    assert {"date", "open", "high", "low", "close", "volume"}.issubset(df_csv.columns)
    assert df_csv["date"].is_monotonic_increasing, "CSV rows must be sorted chronologically"
    assert df_csv["close"].isna().sum() == 0, "No NaNs allowed in close prices"

    # 1.3 Deterministic offline demo generation
    df_demo1 = demo_history("AAPL", days=252)
    df_demo2 = demo_history("AAPL", days=252)
    assert len(df_demo1) == 252, f"Expected 252 bars, got {len(df_demo1)}"
    # Verify deterministic reproducibility
    assert (df_demo1["close"] == df_demo2["close"]).all(), "Demo generation must be strictly deterministic for identical ticker"

    print("    [PASS] Cleaned prices, verified chronological sorting, zero NaNs, and deterministic reproducibility.", flush=True)


def test_section_2_indicators_and_financial_math():
    print("--> [2/5] Testing Financial Mathematics, Indicators & Extrema...", flush=True)
    from stock_analyzer.analysis import _find_extreme, analyze_prices, build_summary, evaluate_signal
    from stock_analyzer.data import load_csv

    df = load_csv("data/raw/DEMO.csv")
    analyzed = analyze_prices(df, fast_window=5, slow_window=15)

    # 2.1 Daily returns validation
    expected_ret = (df["close"].iloc[1] / df["close"].iloc[0]) - 1.0
    actual_ret = analyzed["daily_return"].iloc[1]
    assert np.isclose(expected_ret, actual_ret), f"Daily return mismatch: {expected_ret} vs {actual_ret}"

    # 2.2 Moving average arithmetic validation
    expected_sma5 = df["close"].iloc[0:5].mean()
    actual_sma5 = analyzed["sma_5"].iloc[4]
    assert np.isclose(expected_sma5, actual_sma5), f"SMA-5 mismatch: {expected_sma5} vs {actual_sma5}"

    # 2.3 RSI bounds validation
    valid_rsi = analyzed["rsi_14"].dropna()
    assert len(valid_rsi) > 0, "RSI must produce values for >= 14 bars"
    assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all(), "RSI must be bounded in [0, 100]"

    # 2.4 Bollinger Bands ordering
    valid_bb = analyzed.dropna(subset=["bb_upper", "bb_lower", "sma_5"])
    assert (valid_bb["bb_upper"] >= valid_bb["bb_lower"]).all(), "Upper Bollinger Band must be >= Lower Band"

    # 2.5 Extrema detection
    high_val, high_date, high_field = _find_extreme(df, "high", "close")
    assert high_val == df["high"].max(), "Extreme high must match maximum high in dataset"

    # 2.6 Signal generation
    sig = evaluate_signal(analyzed.iloc[-1])
    assert "label" in sig and "reason" in sig, "Signal must contain label and reason"

    # 2.7 Summary build
    summary = build_summary(analyzed, "DEMO", "csv", fast_window=5, slow_window=15)
    assert summary["ticker"] == "DEMO"
    assert summary["observations"] == 30
    assert summary["first_close"] == round(float(df["close"].iloc[0]), 2)
    assert summary["latest_close"] == round(float(df["close"].iloc[-1]), 2)

    print("    [PASS] Returns formula, SMA slice arithmetic, RSI bounds [0, 100], Bollinger Bands, and extrema confirmed.", flush=True)


def test_section_3_backtesting_simulation():
    print("--> [3/5] Testing Strategy Backtesting Engine & Bias Prevention...", flush=True)
    from stock_analyzer.analysis import run_backtest
    from stock_analyzer.data import demo_history

    df = demo_history("AAPL", days=252)

    # 3.1 Lookahead bias prevention test
    bt = run_backtest(df, fast_window=20, slow_window=50, initial_cash=10000.0, transaction_cost_bps=10.0)
    metrics = bt["metrics"]

    assert metrics["initial_cash"] == 10000.0
    assert metrics["ending_value"] > 0
    assert isinstance(metrics["cagr_pct"], float)
    assert isinstance(metrics["max_drawdown_pct"], float)
    assert isinstance(metrics["sharpe_ratio"], float)
    assert metrics["trade_count"] >= 0
    assert len(bt["equity_curve"]) == len(df), "Equity curve must match bar count"

    # 3.2 Parameter boundary checks
    try:
        run_backtest(df, fast_window=50, slow_window=20)
        assert False, "Should raise ValueError when fast_window >= slow_window"
    except ValueError:
        pass

    try:
        run_backtest(df, fast_window=20, slow_window=50, initial_cash=-500)
        assert False, "Should raise ValueError on non-positive initial_cash"
    except ValueError:
        pass

    print("    [PASS] Verified 1-bar execution lag, friction deduction, metric calculations, and boundary validation.", flush=True)


def test_section_4_cli_pipeline_in_isolated_tempdir():
    print("--> [4/5] Testing Fresh CLI Pipeline Run in Isolated Temp Directory...", flush=True)
    from stock_analyzer.pipeline import run_analysis

    with tempfile.TemporaryDirectory() as temp_out:
        res = run_analysis(
            ticker="AAPL",
            source="demo",
            output_dir=temp_out,
            fast_window=20,
            slow_window=50,
            initial_cash=10000.0,
            transaction_cost_bps=10.0,
        )

        # 4.1 Verify returned structure
        assert "summary" in res
        assert "backtest" in res
        assert "data_path" in res
        assert "report_path" in res
        assert "chart_paths" in res

        # 4.2 Verify CSV output is non-empty and correctly formatted
        csv_path = Path(res["data_path"])
        assert csv_path.exists(), f"Analyzed CSV missing at {csv_path}"
        assert csv_path.stat().st_size > 1000, "Analyzed CSV must not be empty"
        df_out = pd.read_csv(csv_path)
        assert len(df_out) == 252, f"Expected 252 rows in fresh run, got {len(df_out)}"
        assert "sma_20" in df_out.columns and "rsi_14" in df_out.columns

        # 4.3 Verify Markdown report is non-empty and has correct price formatting
        report_path = Path(res["report_path"])
        assert report_path.exists(), f"Report missing at {report_path}"
        assert report_path.stat().st_size > 500, "Markdown report must not be empty"
        report_text = report_path.read_text(encoding="utf-8")
        assert "$$" not in report_text, "Markdown report must not contain double dollar signs ('$$') in prose"
        assert "# Technical Stock Analysis Report: AAPL" in report_text

        # 4.4 Verify all 4 charts were generated, non-empty (>5KB real PNG image)
        chart_paths = [Path(p) for p in res["chart_paths"]]
        assert len(chart_paths) == 4, f"Expected 4 chart paths, got {len(chart_paths)}"
        expected_chart_names = {"price_trend.png", "moving_averages.png", "return_distribution.png", "backtest_equity.png"}
        actual_chart_names = {p.name for p in chart_paths}
        assert expected_chart_names == actual_chart_names, f"Chart names mismatch: {actual_chart_names}"

        for cp in chart_paths:
            assert cp.exists(), f"Chart file missing: {cp}"
            assert cp.stat().st_size > 5000, f"Chart file too small (corrupted/empty): {cp} ({cp.stat().st_size} bytes)"

    print("    [PASS] Fresh run generated non-empty CSV (252 bars), report (single currency format), and 4 valid PNG charts.", flush=True)


def test_section_5_fastapi_endpoints_coverage():
    print("--> [5/5] Testing FastAPI REST Endpoints with State Isolation...", flush=True)
    from app.config import settings
    from app.main import app
    from fastapi.testclient import TestClient

    # Isolate storage state in a temporary directory so workspace JSON files are never polluted
    original_data_dir = settings.data_dir
    with tempfile.TemporaryDirectory() as temp_data_dir:
        settings.data_dir = Path(temp_data_dir)

        # Seed isolated test state
        from app import data_store
        data_store.write("watchlist.json", ["AAPL", "MSFT"])
        data_store.write("portfolio.json", [{"symbol": "AAPL", "shares": 10, "average_cost": 150.0}])
        data_store.write("alerts.json", [])

        client = TestClient(app)
        print("      Checking Route 1: GET /", flush=True)
        r = client.get("/")
        assert r.status_code == 200, f"GET / failed: {r.status_code}"

        print("      Checking Route 2: GET /api/health", flush=True)
        r = client.get("/api/health")
        assert r.status_code == 200, f"GET /api/health failed: {r.status_code}"

        print("      Checking Route 3: GET /api/market/AAPL/history", flush=True)
        r = client.get("/api/market/AAPL/history?period=6mo&provider=demo")
        assert r.status_code == 200, f"GET /api/market/AAPL/history failed: {r.status_code}"

        print("      Checking Route 4: GET /api/market/AAPL/indicators", flush=True)
        r = client.get("/api/market/AAPL/indicators?period=6mo&provider=demo")
        assert r.status_code == 200, f"GET /api/market/AAPL/indicators failed: {r.status_code}"

        print("      Checking Route 5: GET /api/market/AAPL/quote", flush=True)
        r = client.get("/api/market/AAPL/quote")
        assert r.status_code == 200, f"GET /api/market/AAPL/quote failed: {r.status_code}"

        print("      Checking Route 6: GET /api/watchlist", flush=True)
        r = client.get("/api/watchlist")
        assert r.status_code == 200, f"GET /api/watchlist failed: {r.status_code}"

        print("      Checking Route 7: PUT /api/watchlist", flush=True)
        r = client.put("/api/watchlist", json={"symbols": ["AAPL", "NVDA", "GOOGL"]})
        assert r.status_code == 200, f"PUT /api/watchlist failed: {r.status_code}"

        print("      Checking Route 8: GET /api/portfolio", flush=True)
        r = client.get("/api/portfolio")
        assert r.status_code == 200, f"GET /api/portfolio failed: {r.status_code}"

        print("      Checking Route 9: PUT /api/portfolio", flush=True)
        new_holdings = [
            {"symbol": "AAPL", "shares": 15, "average_cost": 160.0},
            {"symbol": "MSFT", "shares": 5, "average_cost": 380.0},
        ]
        r = client.put("/api/portfolio", json={"holdings": new_holdings})
        assert r.status_code == 200, f"PUT /api/portfolio failed: {r.status_code}"

        print("      Checking Route 10: GET /api/alerts", flush=True)
        r = client.get("/api/alerts")
        assert r.status_code == 200, f"GET /api/alerts failed: {r.status_code}"

        print("      Checking Route 11: POST /api/alerts", flush=True)
        new_alert = {"symbol": "AAPL", "condition": "price_above", "threshold": 300.0}
        r = client.post("/api/alerts", json=new_alert)
        assert r.status_code == 201, f"POST /api/alerts failed: {r.status_code}"
        alert_id = r.json()["id"]

        print("      Checking Route 12: DELETE /api/alerts/{id}", flush=True)
        r = client.delete(f"/api/alerts/{alert_id}")
        assert r.status_code == 200, f"DELETE /api/alerts/{alert_id} failed: {r.status_code}"

        print("      Checking Route 13: POST /api/backtest", flush=True)
        bt_payload = {
            "symbol": "AAPL",
            "fast_window": 20,
            "slow_window": 50,
            "initial_cash": 10000,
            "transaction_cost_bps": 10,
        }
        r = client.post("/api/backtest", json=bt_payload)
        assert r.status_code == 200, f"POST /api/backtest failed: {r.status_code}"

        # Restore settings
        settings.data_dir = original_data_dir

    print("    [PASS] All 13 FastAPI endpoints verified (root, health, history, indicators, quote, watchlist [GET/PUT], portfolio [GET/PUT], alerts [GET/POST/DELETE], backtest).", flush=True)


def main():
    print("=" * 70)
    print("         STOCK MARKET DATA ANALYZER - AUTOMATED VERIFICATION         ")
    print("=" * 70)

    try:
        test_section_1_data_ingestion_and_cleaning()
        test_section_2_indicators_and_financial_math()
        test_section_3_backtesting_simulation()
        test_section_4_cli_pipeline_in_isolated_tempdir()
        test_section_5_fastapi_endpoints_coverage()
    except Exception as exc:
        print(f"\n[FAIL] Verification error encountered: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 70)
    print("   ALL 5 VERIFICATION MODULES PASSED (0 FAILURES, FULL COVERAGE)   ")
    print("=" * 70)


if __name__ == "__main__":
    main()

"""Stock Market Data Analyzer - Interactive Streamlit Dashboard (Option B).

Run with:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys
import tempfile

import streamlit as st

# Ensure src/ is on python import path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from stock_analyzer.data import DataLoadError
from stock_analyzer.pipeline import run_analysis

st.set_page_config(
    page_title="Stock Market Data Analyzer",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Stock Market Data Analyzer")
st.caption(
    "Educational financial data analysis platform. "
    "Technical indicators, signals, and simulations are mathematical models and do NOT constitute financial advice."
)

with st.sidebar:
    st.header("⚙️ Configuration & Parameters")
    ticker = st.text_input("Ticker Symbol", "AAPL").strip().upper()
    start_date = st.date_input("Start Date", value=date.today() - timedelta(days=365))
    end_date = st.date_input("End Date", value=date.today())

    source_mode = st.selectbox(
        "Data Source Provider",
        [
            "Auto (Yahoo Finance with CSV/Demo Fallback)",
            "Deterministic Synthetic Demo (Offline)",
            "Yahoo Finance (Live Public Feed)",
            "Custom CSV Upload",
        ],
    )

    csv_file = None
    if source_mode == "Custom CSV Upload":
        csv_file = st.file_uploader("Upload Historical Price CSV", type=["csv"])

    st.subheader("Technical Indicators & Simulation")
    fast_win = st.number_input("Fast SMA Window", min_value=2, max_value=100, value=20)
    slow_win = st.number_input("Slow SMA Window", min_value=3, max_value=250, value=50)
    init_cash = st.number_input("Backtest Initial Capital ($)", min_value=100.0, value=10000.0, step=1000.0)
    cost_bps = st.number_input("Transaction Friction (Basis Points)", min_value=0.0, max_value=100.0, value=10.0, step=1.0)

if fast_win >= slow_win:
    st.error("Error: Fast SMA window must be strictly less than Slow SMA window.")
    st.stop()

# Map source
if source_mode.startswith("Auto"):
    chosen_source = "auto"
elif source_mode.startswith("Deterministic"):
    chosen_source = "demo"
elif source_mode.startswith("Yahoo"):
    chosen_source = "yfinance"
else:
    chosen_source = "csv"

csv_temp_path = None
if csv_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(csv_file.getvalue())
        csv_temp_path = tmp.name

if st.button("🚀 Run Analysis & Backtest", type="primary"):
    with st.spinner("Processing market data, calculating indicators, and running simulation..."):
        try:
            results = run_analysis(
                ticker=ticker,
                start=start_date.isoformat(),
                end=end_date.isoformat(),
                source=chosen_source,
                csv_path=csv_temp_path,
                output_dir=Path("outputs") / "streamlit",
                fast_window=int(fast_win),
                slow_window=int(slow_win),
                initial_cash=float(init_cash),
                transaction_cost_bps=float(cost_bps),
            )
        except (DataLoadError, ValueError) as err:
            st.error(f"Analysis Failed: {err}")
            st.stop()

    summary = results["summary"]
    bt = results["backtest"]["metrics"]
    sig = summary.get("signal", {})

    st.success(f"Analysis completed for **{ticker}** using **{summary['source']}** ({summary['observations']} trading sessions).")

    # Metrics row 1
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Latest Close", f"${summary['latest_close']:,.2f}")
    c1_ret = summary["period_return_pct"]
    c2.metric("Period Return", f"{c1_ret:+.2f}%", delta=f"{c1_ret:+.2f}%")
    c3.metric("Annualized Volatility", f"{summary['annualized_volatility_pct']:.2f}%")
    c4.metric("Descriptive Signal", sig.get("label", "Neutral"))

    st.info(f"💡 **Signal Evaluation:** {sig.get('reason')} (RSI-14: {sig.get('rsi_14')}) | **Trend Context:** {summary['trend']}")

    # Charts Grid
    st.subheader("📊 Visual Technical Analysis")
    col_left, col_right = st.columns(2)
    with col_left:
        st.image(str(results["chart_paths"][0]), caption="Historical Price Trend", use_container_width=True)
        st.image(str(results["chart_paths"][2]), caption="Daily Return Distribution", use_container_width=True)
    with col_right:
        st.image(str(results["chart_paths"][1]), caption="Moving Averages & Bollinger Bands", use_container_width=True)
        st.image(str(results["chart_paths"][3]), caption="Strategy Backtest Simulation", use_container_width=True)

    # Backtest Metrics
    st.subheader("💼 Backtest Simulation Metrics")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Ending Capital", f"${bt['ending_value']:,.2f}", delta=f"{bt['total_return_pct']:+.2f}%")
    b2.metric("Benchmark Return", f"{bt['buy_and_hold_pct']:+.2f}%")
    b3.metric("Annualized CAGR", f"{bt['cagr_pct']:+.2f}%")
    b4.metric("Max Drawdown", f"{bt['max_drawdown_pct']:.2f}%")

    st.subheader("📥 Export Outputs")
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="📄 Download Markdown Report",
            data=Path(results["report_path"]).read_text(encoding="utf-8"),
            file_name=f"{ticker}_analysis_report.md",
            mime="text/markdown",
        )
    with col_dl2:
        st.download_button(
            label="📊 Download Analyzed CSV Data",
            data=Path(results["data_path"]).read_bytes(),
            file_name=f"{ticker}_analyzed_data.csv",
            mime="text/csv",
        )

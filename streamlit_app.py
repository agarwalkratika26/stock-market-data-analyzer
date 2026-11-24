"""Stock Market Data Analyzer — Full-Featured Streamlit Dashboard.

Covers every feature of the FastAPI backend without making HTTP calls:
  • Market data viewer (price history + OHLCV table)
  • Technical indicators (SMA, EMA, MACD, RSI, Bollinger Bands)
  • Descriptive signal evaluation
  • SMA Crossover Backtest Simulation with equity-curve chart
  • Watchlist (view + edit, persisted to backend/data/watchlist.json)
  • Portfolio tracker (view + edit holdings, P&L summary)
  • Alerts (create / delete price & RSI threshold alerts)
  • CSV upload & download (export analyzed data + markdown report)

Run locally:
    streamlit run streamlit_app.py

Deploy on Streamlit Community Cloud:
    Push this file to GitHub; connect the repo at share.streamlit.io.
    Set "Main file path" to: streamlit_app.py

DISCLAIMER: All prices, indicators, signals, and backtest results are
educational outputs produced by mathematical models. They do NOT constitute
financial advice or trading recommendations.
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

# ── Resolve src/ and backend/ onto the import path ───────────────────────────
REPO_ROOT = Path(__file__).resolve().parent
for _p in (REPO_ROOT / "src", REPO_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from stock_analyzer.data import DataLoadError, load_prices
from stock_analyzer.analysis import analyze_prices, build_summary, run_backtest
from stock_analyzer.pipeline import run_analysis

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Market Data Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/agarwalkratika26/stock-market-data-analyzer",
        "Report a bug": "https://github.com/agarwalkratika26/stock-market-data-analyzer/issues",
        "About": "Educational financial data analysis platform. No financial advice.",
    },
)

# ── Persistent JSON store helpers (mirrors backend/app/data_store.py) ─────────
_DATA_DIR = REPO_ROOT / "backend" / "data"
_DEFAULTS: dict[str, Any] = {
    "watchlist.json": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"],
    "portfolio.json": [
        {"symbol": "AAPL", "shares": 10, "average_cost": 180},
        {"symbol": "MSFT", "shares": 5, "average_cost": 390},
        {"symbol": "NVDA", "shares": 8, "average_cost": 115},
    ],
    "alerts.json": [],
}


def _store_path(name: str) -> Path:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    return _DATA_DIR / name


def store_read(name: str) -> Any:
    path = _store_path(name)
    if not path.exists():
        store_write(name, _DEFAULTS[name])
    return json.loads(path.read_text(encoding="utf-8"))


def store_write(name: str, value: Any) -> Any:
    path = _store_path(name)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    tmp.replace(path)
    return value


# ── Data-loading helper with Streamlit caching ────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def _load_cached(ticker: str, source: str, start: str, end: str, csv_bytes: bytes | None):
    """Load + clean prices; cache for 5 minutes."""
    if csv_bytes is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(csv_bytes)
            csv_path = tmp.name
    else:
        csv_path = None
    return load_prices(ticker, start or None, end or None, source, csv_path)


def _get_prices(ticker, source, start, end, csv_bytes=None):
    try:
        df, src_used = _load_cached(ticker, source, str(start), str(end), csv_bytes)
        return df, src_used, None
    except DataLoadError as e:
        return None, None, str(e)
    except Exception as e:
        return None, None, f"Unexpected error: {e}"


# ── Sidebar navigation ────────────────────────────────────────────────────────
PAGES = [
    "🏠 Overview & Analysis",
    "📊 Technical Indicators",
    "🔁 Backtest Simulator",
    "👁️ Watchlist",
    "💼 Portfolio Tracker",
    "🔔 Alerts",
    "📥 Data Import / Export",
    "ℹ️ About & Disclaimers",
]

with st.sidebar:
    st.image(
        "https://img.shields.io/badge/Stock%20Market%20Data%20Analyzer-📈-blue",
        use_container_width=True,
    )
    st.title("📈 MarketScope")
    st.caption("Educational financial analysis platform")
    st.divider()
    page = st.radio("Navigate", PAGES, label_visibility="collapsed")
    st.divider()

    # ── Global data-source controls ──
    st.subheader("⚙️ Data Settings")
    ticker = st.text_input("Ticker Symbol", "AAPL").strip().upper() or "AAPL"
    source_label = st.selectbox(
        "Data Source",
        [
            "Auto (Yahoo Finance → CSV → Demo)",
            "Yahoo Finance (live)",
            "Deterministic Synthetic Demo (offline)",
            "Custom CSV Upload",
        ],
    )
    SOURCE_MAP = {
        "Auto (Yahoo Finance → CSV → Demo)": "auto",
        "Yahoo Finance (live)": "yfinance",
        "Deterministic Synthetic Demo (offline)": "demo",
        "Custom CSV Upload": "csv",
    }
    source = SOURCE_MAP[source_label]

    csv_upload = None
    if source == "csv":
        csv_upload = st.file_uploader("Upload CSV (date, close required)", type=["csv"])

    today = date.today()
    start_date = st.date_input("Start Date", value=date(today.year - 1, today.month, today.day))
    end_date = st.date_input("End Date", value=today)
    st.caption(
        "⚠️ Yahoo Finance data may be delayed. "
        "Synthetic demo prices are fictional and for educational use only."
    )

# ── Disclaimer banner ─────────────────────────────────────────────────────────
st.markdown(
    "> **DISCLAIMER:** All indicators, signals, and backtest results are mathematical models for "
    "educational purposes. They do **not** constitute investment advice or trading recommendations.",
    unsafe_allow_html=False,
)

csv_bytes = csv_upload.getvalue() if csv_upload is not None else None


# =============================================================================
# PAGE: Overview & Analysis
# =============================================================================
if page == "🏠 Overview & Analysis":
    st.header("🏠 Overview & Full Analysis")

    if st.button("🚀 Run Full Analysis & Backtest", type="primary", use_container_width=True):
        with st.spinner("Loading market data, computing indicators, running backtest..."):
            df, src_used, err = _get_prices(ticker, source, start_date, end_date, csv_bytes)

        if err:
            st.error(f"Data Error: {err}")
            st.stop()

        with st.spinner("Analyzing..."):
            try:
                fast_w = st.session_state.get("fast_win", 20)
                slow_w = st.session_state.get("slow_win", 50)
                init_cash = st.session_state.get("init_cash", 10000.0)
                cost_bps = st.session_state.get("cost_bps", 10.0)

                analyzed = analyze_prices(df, fast_w, slow_w)
                summary = build_summary(analyzed, ticker, src_used, fast_w, slow_w)
                bt = run_backtest(df, fast_w, slow_w, init_cash, cost_bps)
                st.session_state["last_analyzed"] = analyzed
                st.session_state["last_summary"] = summary
                st.session_state["last_bt"] = bt
                st.session_state["last_ticker"] = ticker
                st.session_state["last_src"] = src_used
            except (ValueError, Exception) as e:
                st.error(f"Analysis error: {e}")
                st.stop()

    if "last_summary" not in st.session_state:
        st.info("Configure the ticker and date range in the sidebar, then click **Run Full Analysis**.")
        st.stop()

    summary = st.session_state["last_summary"]
    bt = st.session_state["last_bt"]
    analyzed: pd.DataFrame = st.session_state["last_analyzed"]
    sig = summary.get("signal", {})

    st.success(
        f"✅ **{st.session_state['last_ticker']}** | Source: `{st.session_state['last_src']}` | "
        f"{summary['observations']} trading sessions ({summary['start_date']} → {summary['end_date']})"
    )

    # ── Key metrics row ──
    st.subheader("📌 Key Metrics")
    c1, c2, c3, c4, c5 = st.columns(5)
    ret = summary["period_return_pct"]
    c1.metric("Latest Close", f"${summary['latest_close']:,.2f}")
    c2.metric("Period Return", f"{ret:+.2f}%", delta=f"{ret:+.2f}%")
    c3.metric("Ann. Volatility", f"{summary['annualized_volatility_pct']:.2f}%")
    c4.metric("Best Day", f"{summary.get('best_daily_return_pct', 0):+.2f}%")
    c5.metric("Worst Day", f"{summary.get('worst_daily_return_pct', 0):+.2f}%")

    # Signal + trend
    signal_color = {
        "Potentially oversold": "🟢",
        "Potentially overbought": "🔴",
        "Momentum positive": "🔵",
        "Momentum negative": "🟠",
    }.get(sig.get("label", ""), "⚪")
    st.info(
        f"{signal_color} **Signal:** {sig.get('label', 'N/A')} — {sig.get('reason', '')}  \n"
        f"📉 **Trend Context:** {summary.get('trend', 'N/A')}"
    )

    # ── Price + volume chart ──
    st.subheader("📈 Price History")
    chart_df = analyzed[["date", "close"]].copy()
    chart_df["date"] = pd.to_datetime(chart_df["date"])
    chart_df = chart_df.set_index("date")
    st.line_chart(chart_df["close"])

    if "volume" in analyzed.columns:
        st.subheader("📦 Volume")
        vol_df = analyzed[["date", "volume"]].copy()
        vol_df["date"] = pd.to_datetime(vol_df["date"])
        vol_df = vol_df.set_index("date")
        st.bar_chart(vol_df["volume"])

    # ── Summary extremes ──
    st.subheader("🔢 Price Extremes")
    ex1, ex2, ex3, ex4 = st.columns(4)
    ex1.metric("All-Time High", f"${summary['highest_price']:,.2f}", help=f"On {summary['highest_price_date']}")
    ex2.metric("All-Time Low", f"${summary['lowest_price']:,.2f}", help=f"On {summary['lowest_price_date']}")
    ex3.metric("Positive Sessions", str(summary.get("positive_sessions", "—")))
    ex4.metric("Negative Sessions", str(summary.get("negative_sessions", "—")))

    # ── Backtest snapshot ──
    st.subheader("💼 Backtest Snapshot")
    bm = bt["metrics"]
    b1, b2, b3, b4, b5 = st.columns(5)
    b1.metric("Ending Capital", f"${bm['ending_value']:,.2f}", delta=f"{bm['total_return_pct']:+.2f}%")
    b2.metric("Buy & Hold", f"{bm['buy_and_hold_pct']:+.2f}%")
    b3.metric("CAGR", f"{bm['cagr_pct']:+.2f}%")
    b4.metric("Max Drawdown", f"{bm['max_drawdown_pct']:.2f}%")
    b5.metric("Sharpe Ratio", f"{bm['sharpe_ratio']:.2f}")

    with st.expander("📋 Raw Price Data Table"):
        display_cols = [c for c in ["date", "open", "high", "low", "close", "volume"] if c in analyzed.columns]
        st.dataframe(analyzed[display_cols].tail(100), use_container_width=True, hide_index=True)


# =============================================================================
# PAGE: Technical Indicators
# =============================================================================
elif page == "📊 Technical Indicators":
    st.header("📊 Technical Indicators")

    fast_win = st.sidebar.number_input("Fast SMA Window", 2, 100, 20, key="fast_win")
    slow_win = st.sidebar.number_input("Slow SMA Window", 3, 250, 50, key="slow_win")

    if fast_win >= slow_win:
        st.error("Fast SMA window must be strictly less than Slow SMA window.")
        st.stop()

    if st.button("📡 Fetch & Calculate Indicators", type="primary", use_container_width=True):
        with st.spinner("Loading data and computing indicators..."):
            df, src_used, err = _get_prices(ticker, source, start_date, end_date, csv_bytes)
        if err:
            st.error(err)
            st.stop()

        analyzed = analyze_prices(df, int(fast_win), int(slow_win))
        summary = build_summary(analyzed, ticker, src_used, int(fast_win), int(slow_win))
        st.session_state["ind_data"] = analyzed
        st.session_state["ind_summary"] = summary
        st.session_state["ind_ticker"] = ticker
        st.session_state["ind_src"] = src_used

    if "ind_data" not in st.session_state:
        st.info("Select a ticker and click **Fetch & Calculate Indicators**.")
        st.stop()

    analyzed: pd.DataFrame = st.session_state["ind_data"]
    summary = st.session_state["ind_summary"]
    sig = summary.get("signal", {})
    latest = analyzed.iloc[-1]

    st.success(f"**{st.session_state['ind_ticker']}** | Source: `{st.session_state['ind_src']}`")

    # ── Indicator snapshot cards ──
    st.subheader("🔢 Latest Indicator Values")
    i1, i2, i3, i4 = st.columns(4)
    rsi_val = latest.get("rsi_14")
    macd_val = latest.get("macd")
    macd_sig_val = latest.get("macd_signal")
    bb_upper = latest.get("bb_upper")
    bb_lower = latest.get("bb_lower")

    i1.metric("RSI-14 (Wilder)", f"{rsi_val:.1f}" if pd.notna(rsi_val) else "N/A",
              help="Oversold < 30 · Overbought > 70")
    i2.metric("MACD", f"{macd_val:.4f}" if pd.notna(macd_val) else "N/A")
    i3.metric("MACD Signal", f"{macd_sig_val:.4f}" if pd.notna(macd_sig_val) else "N/A")
    i4.metric("BB Upper / Lower",
              f"{bb_upper:.2f} / {bb_lower:.2f}" if pd.notna(bb_upper) and pd.notna(bb_lower) else "N/A")

    j1, j2, j3, j4 = st.columns(4)
    sma_fast = latest.get(f"sma_{int(fast_win)}")
    sma_slow = latest.get(f"sma_{int(slow_win)}")
    ema12 = latest.get("ema_12")
    ema26 = latest.get("ema_26")
    j1.metric(f"SMA-{int(fast_win)}", f"{sma_fast:.2f}" if pd.notna(sma_fast) else "N/A")
    j2.metric(f"SMA-{int(slow_win)}", f"{sma_slow:.2f}" if pd.notna(sma_slow) else "N/A")
    j3.metric("EMA-12", f"{ema12:.2f}" if pd.notna(ema12) else "N/A")
    j4.metric("EMA-26", f"{ema26:.2f}" if pd.notna(ema26) else "N/A")

    signal_label = sig.get("label", "N/A")
    st.info(
        f"🔍 **Descriptive Signal:** {signal_label}  \n"
        f"📝 {sig.get('reason', '')}  \n"
        f"⚠️ *Descriptive only — not financial advice.*"
    )

    # ── Tabs for each indicator chart ──
    t1, t2, t3, t4 = st.tabs(["Price + SMAs", "RSI-14", "MACD", "Bollinger Bands"])

    chart_base = analyzed.copy()
    chart_base["date"] = pd.to_datetime(chart_base["date"])
    chart_base = chart_base.set_index("date")

    with t1:
        cols = ["close", f"sma_{int(fast_win)}", f"sma_{int(slow_win)}", "ema_12", "ema_26", "bb_upper", "bb_lower", "bb_mid"]
        avail = [c for c in cols if c in chart_base.columns]
        st.line_chart(chart_base[avail])

    with t2:
        if "rsi_14" in chart_base.columns:
            rsi_chart = chart_base[["rsi_14"]].dropna()
            st.line_chart(rsi_chart)
            st.caption("RSI < 30: Potentially oversold | RSI > 70: Potentially overbought")
        else:
            st.info("RSI not available (insufficient history).")

    with t3:
        macd_cols = [c for c in ["macd", "macd_signal", "macd_hist"] if c in chart_base.columns]
        if macd_cols:
            st.line_chart(chart_base[macd_cols].dropna())
        else:
            st.info("MACD not available.")

    with t4:
        bb_cols = [c for c in ["close", "bb_upper", "bb_lower", "bb_mid"] if c in chart_base.columns]
        if len(bb_cols) > 1:
            st.line_chart(chart_base[bb_cols].dropna())
        else:
            st.info("Bollinger Bands not available (insufficient history).")

    with st.expander("📋 Full Indicator Data Table"):
        ind_cols = [c for c in [
            "date", "close", f"sma_{int(fast_win)}", f"sma_{int(slow_win)}",
            "ema_12", "ema_26", "macd", "macd_signal", "rsi_14",
            "bb_upper", "bb_lower", "volatility_20d_pct",
            "daily_return_pct", "cumulative_return_pct",
        ] if c in analyzed.columns]
        display = analyzed[ind_cols].tail(120).copy()
        display["date"] = pd.to_datetime(display["date"]).dt.strftime("%Y-%m-%d")
        st.dataframe(display, use_container_width=True, hide_index=True)


# =============================================================================
# PAGE: Backtest Simulator
# =============================================================================
elif page == "🔁 Backtest Simulator":
    st.header("🔁 SMA Crossover Backtest Simulator")
    st.caption(
        "Long or cash strategy. Signal generated from yesterday's SMA crossover executes "
        "on today's close (1-bar delay). No leverage, shorting, or reinvestment of dividends."
    )

    with st.form("backtest_form"):
        st.subheader("Simulation Parameters")
        fc1, fc2 = st.columns(2)
        fast_w = fc1.number_input("Fast SMA Window", 2, 100, 20)
        slow_w = fc2.number_input("Slow SMA Window", 3, 250, 50)
        fc3, fc4 = st.columns(2)
        init_cash = fc3.number_input("Initial Capital ($)", 100.0, 10_000_000.0, 10000.0, 1000.0)
        cost_bps = fc4.number_input("Transaction Friction (bps)", 0.0, 500.0, 10.0, 1.0)
        submitted = st.form_submit_button("▶️ Run Backtest", type="primary", use_container_width=True)

    if fast_w >= slow_w:
        st.error("Fast window must be strictly less than slow window.")
        st.stop()

    if submitted:
        with st.spinner("Loading market data and running simulation..."):
            df, src_used, err = _get_prices(ticker, source, start_date, end_date, csv_bytes)
        if err:
            st.error(err)
            st.stop()
        try:
            bt = run_backtest(df, int(fast_w), int(slow_w), float(init_cash), float(cost_bps))
            st.session_state["bt_result"] = bt
            st.session_state["bt_ticker"] = ticker
            st.session_state["bt_src"] = src_used
        except ValueError as e:
            st.error(f"Backtest error: {e}")
            st.stop()

    if "bt_result" not in st.session_state:
        st.info("Fill in parameters above and click **Run Backtest**.")
        st.stop()

    bt = st.session_state["bt_result"]
    bm = bt["metrics"]
    eq = bt["equity_curve"]

    st.success(
        f"✅ **{st.session_state['bt_ticker']}** | Source: `{st.session_state['bt_src']}` | "
        f"SMA({bm['fast_window']}/{bm['slow_window']}) | "
        f"${bm['initial_cash']:,.0f} → ${bm['ending_value']:,.2f}"
    )

    # ── Metric cards ──
    st.subheader("📊 Backtest Results")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Return", f"{bm['total_return_pct']:+.2f}%")
    m2.metric("Buy & Hold", f"{bm['buy_and_hold_pct']:+.2f}%")
    m3.metric("CAGR", f"{bm['cagr_pct']:+.2f}%")
    m4.metric("Max Drawdown", f"{bm['max_drawdown_pct']:.2f}%")
    m5.metric("Sharpe Ratio", f"{bm['sharpe_ratio']:.2f}")
    m6.metric("Trade Count", str(bm["trade_count"]))

    # ── Equity curve ──
    st.subheader("📈 Strategy vs. Buy-and-Hold Equity Curve")
    eq_df = pd.DataFrame(eq)
    eq_df["date"] = pd.to_datetime(eq_df["date"])
    eq_df = eq_df.set_index("date")
    st.line_chart(eq_df[["strategy", "benchmark"]])

    # ── Position timeline ──
    if "position" in eq_df.columns:
        with st.expander("📐 Position Timeline (1 = Long, 0 = Cash)"):
            st.bar_chart(eq_df["position"])

    # ── Assumptions ──
    with st.expander("⚠️ Assumptions & Limitations"):
        for a in bt.get("assumptions", []):
            st.write(f"• {a}")
        st.write(
            "• **This simulation is educational. Past simulated performance does NOT "
            "predict future market returns.**"
        )

    with st.expander("📋 Full Equity-Curve Table"):
        st.dataframe(eq_df.reset_index(), use_container_width=True, hide_index=True)

    # ── Download ──
    eq_csv = eq_df.reset_index().to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Equity Curve CSV",
        data=eq_csv,
        file_name=f"{st.session_state['bt_ticker']}_equity_curve.csv",
        mime="text/csv",
    )


# =============================================================================
# PAGE: Watchlist
# =============================================================================
elif page == "👁️ Watchlist":
    st.header("👁️ Watchlist")
    st.caption("Prices are latest available daily bars fetched from your chosen data provider. Not real-time.")

    watchlist: list[str] = store_read("watchlist.json")

    # ── Live quotes for watchlist ──
    if st.button("🔄 Refresh Watchlist Quotes", use_container_width=True):
        with st.spinner("Fetching quotes for watchlist symbols..."):
            rows = []
            for sym in watchlist:
                try:
                    df, src_used, err = _get_prices(sym, source, None, None)
                    if err or df is None:
                        rows.append({"Symbol": sym, "Price": None, "Change %": None, "Signal": "Error", "Source": "—"})
                        continue
                    analyzed = analyze_prices(df, 20, 50)
                    latest = analyzed.iloc[-1]
                    close = float(latest["close"])
                    prev = float(analyzed.iloc[-2]["close"]) if len(analyzed) > 1 else close
                    change_pct = (close / prev - 1) * 100 if prev else 0
                    sig = build_summary(analyzed, sym, src_used, 20, 50)["signal"]
                    rows.append({
                        "Symbol": sym,
                        "Price": f"${close:,.2f}",
                        "Change %": f"{change_pct:+.2f}%",
                        "RSI-14": f"{latest.get('rsi_14', float('nan')):.1f}" if pd.notna(latest.get("rsi_14")) else "—",
                        "Signal": sig.get("label", "—"),
                        "Source": src_used,
                    })
                except Exception as e:
                    rows.append({"Symbol": sym, "Price": None, "Change %": None, "Signal": f"Error: {e}", "Source": "—"})
        st.session_state["watchlist_rows"] = rows

    if "watchlist_rows" in st.session_state:
        st.dataframe(
            pd.DataFrame(st.session_state["watchlist_rows"]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Current watchlist symbols: " + ", ".join(watchlist))
        st.info("Click **Refresh Watchlist Quotes** to load live prices and signals.")

    # ── Edit watchlist ──
    st.divider()
    st.subheader("✏️ Edit Watchlist")
    with st.form("watchlist_form"):
        new_symbols_raw = st.text_area(
            "Symbols (one per line or comma-separated)",
            value="\n".join(watchlist),
            height=150,
        )
        save_wl = st.form_submit_button("💾 Save Watchlist", type="primary")

    if save_wl:
        raw = new_symbols_raw.replace(",", "\n")
        symbols = [s.strip().upper() for s in raw.splitlines() if s.strip()]
        symbols = list(dict.fromkeys(symbols))  # deduplicate, preserve order
        if not symbols:
            st.error("Add at least one symbol.")
        elif len(symbols) > 30:
            st.error("Maximum 30 symbols allowed.")
        else:
            store_write("watchlist.json", symbols)
            st.success(f"Watchlist saved: {', '.join(symbols)}")
            # Clear cached quotes so they reload on next refresh
            if "watchlist_rows" in st.session_state:
                del st.session_state["watchlist_rows"]
            st.rerun()


# =============================================================================
# PAGE: Portfolio Tracker
# =============================================================================
elif page == "💼 Portfolio Tracker":
    st.header("💼 Portfolio Tracker")
    st.caption("Market values are computed from latest available daily close prices — not real-time.")

    portfolio: list[dict] = store_read("portfolio.json")

    # ── Live portfolio summary ──
    if st.button("🔄 Refresh Portfolio Values", use_container_width=True):
        with st.spinner("Fetching current prices for all holdings..."):
            rows = []
            total_value = 0.0
            total_cost = 0.0
            for h in portfolio:
                sym = h["symbol"]
                shares = h["shares"]
                avg_cost = h["average_cost"]
                try:
                    df, src_used, err = _get_prices(sym, source, None, None)
                    if err or df is None:
                        rows.append({
                            "Symbol": sym, "Shares": shares,
                            "Avg Cost": f"${avg_cost:,.2f}",
                            "Current Price": "Error", "Market Value": "—",
                            "Gain / Loss": "—", "Return %": "—", "Source": "—",
                        })
                        continue
                    price = float(df.iloc[-1]["close"])
                    mkt_val = price * shares
                    cost_val = avg_cost * shares
                    gain = mkt_val - cost_val
                    ret_pct = (gain / cost_val * 100) if cost_val else 0
                    total_value += mkt_val
                    total_cost += cost_val
                    rows.append({
                        "Symbol": sym, "Shares": shares,
                        "Avg Cost": f"${avg_cost:,.2f}",
                        "Current Price": f"${price:,.2f}",
                        "Market Value": f"${mkt_val:,.2f}",
                        "Gain / Loss": f"${gain:+,.2f}",
                        "Return %": f"{ret_pct:+.2f}%",
                        "Source": src_used,
                    })
                except Exception as e:
                    rows.append({"Symbol": sym, "Shares": shares, "Avg Cost": f"${avg_cost:,.2f}",
                                 "Current Price": f"Err: {e}", "Market Value": "—",
                                 "Gain / Loss": "—", "Return %": "—", "Source": "—"})
            st.session_state["portfolio_rows"] = rows
            st.session_state["portfolio_totals"] = (total_value, total_cost)

    if "portfolio_rows" in st.session_state:
        total_value, total_cost = st.session_state["portfolio_totals"]
        total_gain = total_value - total_cost

        pt1, pt2, pt3 = st.columns(3)
        pt1.metric("Total Market Value", f"${total_value:,.2f}")
        pt2.metric("Total Cost Basis", f"${total_cost:,.2f}")
        pt3.metric("Total Gain / Loss", f"${total_gain:+,.2f}",
                   delta=f"{(total_gain / total_cost * 100):+.2f}%" if total_cost else "—")

        st.dataframe(
            pd.DataFrame(st.session_state["portfolio_rows"]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(f"Portfolio has {len(portfolio)} holdings. Click **Refresh Portfolio Values** to load current prices.")
        st.dataframe(pd.DataFrame(portfolio), use_container_width=True, hide_index=True)

    # ── Edit holdings ──
    st.divider()
    st.subheader("✏️ Edit Holdings")

    with st.form("portfolio_edit_form"):
        st.markdown("**Add or update a holding:**")
        p1, p2, p3 = st.columns(3)
        new_sym = p1.text_input("Symbol").strip().upper()
        new_shares = p2.number_input("Shares", min_value=0.001, value=1.0)
        new_cost = p3.number_input("Average Cost per Share ($)", min_value=0.01, value=100.0)
        col_add, col_clear = st.columns(2)
        do_add = col_add.form_submit_button("➕ Add / Update Holding", use_container_width=True)
        do_clear = col_clear.form_submit_button("🗑️ Clear All Holdings", use_container_width=True)

    if do_add and new_sym:
        updated = [h for h in portfolio if h["symbol"] != new_sym]
        updated.append({"symbol": new_sym, "shares": float(new_shares), "average_cost": float(new_cost)})
        store_write("portfolio.json", updated)
        st.success(f"Added/updated {new_sym}: {new_shares} shares @ ${new_cost:.2f}")
        if "portfolio_rows" in st.session_state:
            del st.session_state["portfolio_rows"]
        st.rerun()

    if do_clear:
        store_write("portfolio.json", [])
        st.success("Portfolio cleared.")
        if "portfolio_rows" in st.session_state:
            del st.session_state["portfolio_rows"]
        st.rerun()


# =============================================================================
# PAGE: Alerts
# =============================================================================
elif page == "🔔 Alerts":
    st.header("🔔 Price & RSI Alerts")
    st.caption(
        "Alerts are checked on demand. 'Triggered' means the condition was met "
        "as of the last check — not a real-time push notification."
    )

    alerts: list[dict] = store_read("alerts.json")

    # ── Check all alerts ──
    if st.button("🔍 Check All Alerts Now", use_container_width=True):
        with st.spinner("Evaluating alert conditions against latest data..."):
            updated_alerts = []
            for alert in alerts:
                a = alert.copy()
                if a.get("triggered"):
                    updated_alerts.append(a)
                    continue
                try:
                    df, src_used, err = _get_prices(a["symbol"], source, None, None)
                    if err or df is None:
                        a["current_value"] = None
                        updated_alerts.append(a)
                        continue
                    analyzed = analyze_prices(df, 20, 50)
                    latest = analyzed.iloc[-1]
                    cond = a["condition"]
                    if cond.startswith("price"):
                        val = float(latest["close"])
                    else:
                        val = float(latest.get("rsi_14", float("nan")))
                    a["current_value"] = round(val, 2) if not pd.isna(val) else None
                    if a["current_value"] is not None:
                        if cond.endswith("above"):
                            a["triggered"] = val > a["threshold"]
                        else:
                            a["triggered"] = val < a["threshold"]
                        if a["triggered"]:
                            a["triggered_at"] = datetime.now(timezone.utc).isoformat()
                except Exception as e:
                    a["current_value"] = None
                updated_alerts.append(a)
            store_write("alerts.json", updated_alerts)
            st.session_state["checked_alerts"] = updated_alerts
            st.rerun()

    display_alerts = st.session_state.get("checked_alerts", alerts)

    if display_alerts:
        for al in display_alerts:
            status = "🔴 TRIGGERED" if al.get("triggered") else "🟡 Watching"
            cur_val = al.get("current_value", "—")
            cur_str = f"{cur_val:.2f}" if isinstance(cur_val, float) else str(cur_val)
            with st.expander(
                f"{status}  |  {al['symbol']} — {al['condition']} {al['threshold']}  "
                f"(current: {cur_str})"
            ):
                col_a, col_b, col_c = st.columns(3)
                col_a.write(f"**Symbol:** {al['symbol']}")
                col_b.write(f"**Condition:** {al['condition']}")
                col_c.write(f"**Threshold:** {al['threshold']}")
                if al.get("triggered_at"):
                    st.success(f"Triggered at: {al['triggered_at']}")
                if st.button(f"🗑️ Delete alert {al['id']}", key=f"del_{al['id']}"):
                    remaining = [a for a in alerts if a["id"] != al["id"]]
                    store_write("alerts.json", remaining)
                    if "checked_alerts" in st.session_state:
                        del st.session_state["checked_alerts"]
                    st.rerun()
    else:
        st.info("No alerts configured. Create one below.")

    # ── Create new alert ──
    st.divider()
    st.subheader("➕ Create New Alert")
    with st.form("alert_form"):
        al1, al2 = st.columns(2)
        al_sym = al1.text_input("Symbol").strip().upper()
        al_cond = al2.selectbox(
            "Condition",
            ["price_above", "price_below", "rsi_above", "rsi_below"],
        )
        al_thresh = st.number_input(
            "Threshold (price in $ or RSI 0-100)",
            min_value=0.0, max_value=100000.0, value=150.0, step=1.0,
        )
        create_btn = st.form_submit_button("🔔 Create Alert", type="primary")

    if create_btn:
        if not al_sym:
            st.error("Symbol is required.")
        else:
            new_alert = {
                "id": str(int(datetime.now(timezone.utc).timestamp() * 1000)),
                "symbol": al_sym,
                "condition": al_cond,
                "threshold": float(al_thresh),
                "triggered": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            existing = store_read("alerts.json")
            existing.insert(0, new_alert)
            store_write("alerts.json", existing)
            if "checked_alerts" in st.session_state:
                del st.session_state["checked_alerts"]
            st.success(f"Alert created: {al_sym} {al_cond} {al_thresh}")
            st.rerun()


# =============================================================================
# PAGE: Data Import / Export
# =============================================================================
elif page == "📥 Data Import / Export":
    st.header("📥 Data Import / Export")

    tab_import, tab_export, tab_full = st.tabs(["📂 Import & Preview", "📤 Export Analysis", "🔄 Full Pipeline Export"])

    # ── Tab: Import & Preview ──
    with tab_import:
        st.subheader("Upload a Price CSV for Preview")
        uploaded = st.file_uploader("Upload CSV (must have 'date' and 'close' columns)", type=["csv"])
        if uploaded:
            try:
                from stock_analyzer.data import clean_prices
                raw = pd.read_csv(uploaded, comment="#")
                st.write(f"**Raw shape:** {raw.shape[0]} rows × {raw.shape[1]} columns")
                st.dataframe(raw.head(10), use_container_width=True)
                cleaned = clean_prices(raw)
                st.success(f"✅ Cleaned: {len(cleaned)} valid rows, {cleaned.columns.tolist()}")
                st.dataframe(cleaned.head(20), use_container_width=True)
            except Exception as e:
                st.error(f"Could not parse CSV: {e}")

        st.divider()
        st.subheader("Sample CSV Format")
        sample = pd.DataFrame({
            "date": ["2024-01-02", "2024-01-03", "2024-01-04"],
            "open": [185.10, 184.00, 182.50],
            "high": [186.50, 186.00, 183.90],
            "low": [184.80, 183.00, 181.00],
            "close": [185.92, 185.20, 182.68],
            "volume": [49100000, 55200000, 48900000],
        })
        st.dataframe(sample, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Download Sample CSV Template",
            data=sample.to_csv(index=False).encode("utf-8"),
            file_name="sample_price_template.csv",
            mime="text/csv",
        )

    # ── Tab: Export Analysis ──
    with tab_export:
        st.subheader("Run Analysis & Export Results")
        fast_w_ex = st.number_input("Fast SMA", 2, 100, 20, key="ex_fast")
        slow_w_ex = st.number_input("Slow SMA", 3, 250, 50, key="ex_slow")

        if fast_w_ex >= slow_w_ex:
            st.error("Fast window must be less than slow window.")
        elif st.button("🚀 Run & Prepare Exports", type="primary"):
            with st.spinner("Analyzing..."):
                df, src_used, err = _get_prices(ticker, source, start_date, end_date, csv_bytes)
            if err:
                st.error(err)
            else:
                try:
                    analyzed = analyze_prices(df, int(fast_w_ex), int(slow_w_ex))
                    bt_res = run_backtest(df, int(fast_w_ex), int(slow_w_ex))
                    st.session_state["export_analyzed"] = analyzed
                    st.session_state["export_bt"] = bt_res
                    st.session_state["export_ticker"] = ticker
                except Exception as e:
                    st.error(f"Error: {e}")

        if "export_analyzed" in st.session_state:
            analyzed_ex: pd.DataFrame = st.session_state["export_analyzed"]
            bt_ex = st.session_state["export_bt"]
            tkr_ex = st.session_state["export_ticker"]

            st.success(f"Ready to export: **{tkr_ex}** — {len(analyzed_ex)} rows")
            ec1, ec2 = st.columns(2)

            ec1.download_button(
                "📊 Download Analyzed Price + Indicators CSV",
                data=analyzed_ex.to_csv(index=False).encode("utf-8"),
                file_name=f"{tkr_ex}_analyzed.csv",
                mime="text/csv",
            )
            ec2.download_button(
                "📈 Download Equity Curve CSV",
                data=pd.DataFrame(bt_ex["equity_curve"]).to_csv(index=False).encode("utf-8"),
                file_name=f"{tkr_ex}_equity_curve.csv",
                mime="text/csv",
            )

    # ── Tab: Full Pipeline ──
    with tab_full:
        st.subheader("Full Pipeline — Runs All Charts + Markdown Report")
        st.caption(
            "Uses the CLI pipeline to generate charts, CSV, and a Markdown summary. "
            "Outputs are written to `outputs/<TICKER>/` in the project directory."
        )
        fast_w_fp = st.number_input("Fast SMA", 2, 100, 20, key="fp_fast")
        slow_w_fp = st.number_input("Slow SMA", 3, 250, 50, key="fp_slow")
        init_cash_fp = st.number_input("Initial Capital ($)", 100.0, 1_000_000.0, 10000.0, key="fp_cash")

        if st.button("🔄 Run Full Pipeline", type="primary"):
            if fast_w_fp >= slow_w_fp:
                st.error("Fast window must be less than slow window.")
            else:
                csv_path_fp = None
                if csv_bytes:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                        tmp.write(csv_bytes)
                        csv_path_fp = tmp.name
                with st.spinner("Running full analysis pipeline..."):
                    try:
                        results = run_analysis(
                            ticker=ticker,
                            start=str(start_date),
                            end=str(end_date),
                            source=source,
                            csv_path=csv_path_fp,
                            output_dir=REPO_ROOT / "outputs" / "streamlit",
                            fast_window=int(fast_w_fp),
                            slow_window=int(slow_w_fp),
                            initial_cash=float(init_cash_fp),
                        )
                        st.session_state["fp_results"] = results
                        st.session_state["fp_ticker"] = ticker
                    except Exception as e:
                        st.error(f"Pipeline error: {e}")

        if "fp_results" in st.session_state:
            res = st.session_state["fp_results"]
            tkr_fp = st.session_state["fp_ticker"]
            st.success(f"Pipeline complete for **{tkr_fp}**")

            d1, d2 = st.columns(2)
            report_text = Path(res["report_path"]).read_text(encoding="utf-8")
            d1.download_button(
                "📄 Download Markdown Report",
                data=report_text.encode("utf-8"),
                file_name=f"{tkr_fp}_report.md",
                mime="text/markdown",
            )
            d2.download_button(
                "📊 Download Analyzed CSV",
                data=Path(res["data_path"]).read_bytes(),
                file_name=f"{tkr_fp}_analyzed.csv",
                mime="text/csv",
            )

            with st.expander("📋 Markdown Report Preview"):
                st.markdown(report_text)

            st.subheader("📊 Generated Charts")
            chart_cols = st.columns(2)
            for i, cp in enumerate(res["chart_paths"]):
                chart_cols[i % 2].image(str(cp), use_container_width=True)


# =============================================================================
# PAGE: About & Disclaimers
# =============================================================================
elif page == "ℹ️ About & Disclaimers":
    st.header("ℹ️ About This Application")

    st.markdown("""
## Stock Market Data Analyzer

An educational, full-stack financial data analytics system built to explore historical market
behaviour, technical indicators, portfolio tracking, threshold alerts, and trading strategy
backtests — with zero paid subscriptions or API keys required.

### Features in this Streamlit App

| Section | What it does |
|---|---|
| 🏠 Overview & Analysis | Full end-to-end analysis: load data, compute indicators, run backtest, display all metrics |
| 📊 Technical Indicators | SMA, EMA, MACD, RSI-14 (Wilder), Bollinger Bands — interactive charts per indicator |
| 🔁 Backtest Simulator | Configurable SMA crossover simulation with equity curve, drawdown, CAGR, Sharpe |
| 👁️ Watchlist | View and edit a persistent watchlist; refresh quotes and signals on demand |
| 💼 Portfolio Tracker | Add holdings, track P&L against latest close prices |
| 🔔 Alerts | Create / delete price-above, price-below, RSI-above, RSI-below alerts; evaluate on demand |
| 📥 Import / Export | Upload CSV, preview cleaned data, download analyzed CSVs and Markdown reports |

### Data Sources

- **Yahoo Finance** (`yfinance`) — public historical market data, subject to provider delays and
  rate limits. Not real-time; typically reflects the previous session's close.
- **Local CSV** — your own files in `date,close` format (optional OHLCV columns).
- **Deterministic Synthetic Demo** — Geometric Brownian Motion seeded by ticker hash.
  Produces fictional prices for offline / classroom use. Clearly labeled.

### GitHub Repository

🔗 [github.com/agarwalkratika26/stock-market-data-analyzer](https://github.com/agarwalkratika26/stock-market-data-analyzer)
""")

    st.divider()
    st.error("""
**IMPORTANT DISCLAIMER**

All price data, technical indicators (RSI, MACD, Bollinger Bands, moving averages),
descriptive signals, and backtest results produced by this application are:

- **Mathematical models** applied to historical or synthetic data.
- **Educational outputs** intended for learning and portfolio demonstration only.
- **NOT financial advice**, investment recommendations, or predictions of future performance.

Synthetic/demo prices are entirely fictional. Yahoo Finance data may be delayed, incomplete,
or temporarily unavailable. Past simulated performance does not guarantee future market results.
""")

    st.markdown("""
### Tech Stack
- **Python 3.11+** · pandas · NumPy · Streamlit
- **Data** — yfinance · CSV · Deterministic GBM synthetic generator
- **Indicators** — implemented from scratch (EMA, Wilder RSI, MACD, Bollinger Bands)
- **Backend** — FastAPI (separate service, not required for this Streamlit app)
- **Dashboard** — Next.js 16 TypeScript (separate service, not required here)
""")

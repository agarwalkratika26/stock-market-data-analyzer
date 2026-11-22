"""Markdown report generator for stock analysis and backtest results."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def _fmt_price(val: float | None) -> str:
    return "N/A" if val is None else f"${val:,.2f}"


def _fmt_pct(val: float | None) -> str:
    return "N/A" if val is None else f"{val:+.2f}%"


def write_report(
    summary: Dict[str, Any],
    backtest_results: Dict[str, Any] | None,
    output: Path,
    chart_names: List[str],
) -> Path:
    """Generate a clean, professional, Markdown-formatted analysis report."""
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    sig = summary.get("signal", {})
    signal_label = sig.get("label", "Neutral")
    signal_reason = sig.get("reason", "N/A")
    rsi_val = sig.get("rsi_14", "N/A")

    # Format backtest section if available
    bt_section = ""
    if backtest_results and "metrics" in backtest_results:
        m = backtest_results["metrics"]
        assumptions = "\n".join(f"- {a}" for a in backtest_results.get("assumptions", []))
        bt_section = f"""## 4. Moving Average Crossover Backtest Simulation

- **Strategy Parameters:** Fast SMA = {m['fast_window']} sessions, Slow SMA = {m['slow_window']} sessions
- **Transaction Friction:** {m['transaction_cost_bps']} bps per trade turnover
- **Initial Capital:** {_fmt_price(m['initial_cash'])}
- **Ending Strategy Equity:** {_fmt_price(m['ending_value'])}
- **Strategy Total Return:** {_fmt_pct(m['total_return_pct'])}
- **Compound Annual Growth Rate (CAGR):** {_fmt_pct(m['cagr_pct'])}
- **Maximum Drawdown:** {_fmt_pct(m['max_drawdown_pct'])}
- **Sharpe Ratio (Annualized):** {m['sharpe_ratio']:.2f}
- **Benchmark Buy & Hold Return:** {_fmt_pct(m['buy_and_hold_pct'])}
- **Total Trades Executed:** {m['trade_count']}

### Simulation Assumptions & Friction Rules:
{assumptions}
"""

    charts_md = "\n".join(
        f"![{name.replace('_', ' ').replace('.png', '').title()}]({name})"
        for name in chart_names
    )

    report_content = f"""# Technical Stock Analysis Report: {summary['ticker']}

> **Educational Notice:** This report is generated automatically for educational and analytical purposes. All calculations are mathematical models and do NOT constitute investment advice or trading recommendations.

---

## 1. Dataset & Collection Metadata

- **Ticker Symbol:** `{summary['ticker']}`
- **Data Provider / Source:** {summary['source']}
- **Date Range Analyzed:** {summary['start_date']} to {summary['end_date']}
- **Trading Sessions Observed:** {summary['observations']} bars
- **First Recorded Close:** {_fmt_price(summary['first_close'])}
- **Latest Observed Close:** {_fmt_price(summary['latest_close'])}

---

## 2. Price Performance & Volatility Summary

- **Period Cumulative Return:** {_fmt_pct(summary['period_return_pct'])}
- **Annualized Return Volatility:** {summary['annualized_volatility_pct']:.2f}% (computed via $\\sigma_{{\\text{{daily}}}} \\times \\sqrt{{252}}$)
- **Highest Observed Price:** {_fmt_price(summary['highest_price'])} on {summary['highest_price_date']} (from `{summary['highest_price_field']}` field)
- **Lowest Observed Price:** {_fmt_price(summary['lowest_price'])} on {summary['lowest_price_date']} (from `{summary['lowest_price_field']}` field)
- **Best Single-Session Return:** {_fmt_pct(summary['best_daily_return_pct'])}
- **Worst Single-Session Return:** {_fmt_pct(summary['worst_daily_return_pct'])}
- **Up / Down Session Ratio:** {summary.get('positive_sessions', 0)} positive vs. {summary.get('negative_sessions', 0)} negative sessions

---

## 3. Technical Indicator Context & Signals

- **Fast Simple Moving Average (SMA {summary['fast_window']}):** {_fmt_price(summary['fast_average'])}
- **Slow Simple Moving Average (SMA {summary['slow_window']}):** {_fmt_price(summary['slow_average'])}
- **Trend Evaluation:** {summary['trend']}
- **Descriptive Indicator Signal:** **{signal_label}**
- **Signal Rationale:** {signal_reason} (RSI-14: {rsi_val})

*Note: Technical indicator signals are backward-looking descriptions of mathematical patterns and must not be interpreted as future price predictions.*

---

{bt_section}

---

## 5. Visualizations

{charts_md}

---

## 6. Mathematical Methodology & Limitations

1. **Daily Returns:** Calculated via log/percentage difference between consecutive adjusted close bars: $R_t = \\frac{{C_t - C_{{t-1}}}}{{C_{{t-1}}}}$.
2. **Annualized Volatility:** Sample standard deviation of daily returns scaled by the square root of 252 regular trading sessions: $\\sigma_{{\\text{{ann}}}} = \\sigma_{{\\text{{daily}}}} \\times \\sqrt{{252}}$.
3. **Lookahead Bias Prevention:** In backtesting, trading positions are shifted forward by one session ($t+1$) so that execution happens after the observation bar has completed.
4. **Data Provider Caveats:** Free public feeds (Yahoo Finance) or synthetic simulations may include delays, adjustments, or fictional data. Real execution environments incur slippage, bid-ask spread friction, market impact, and corporate tax consequences not fully modeled here.
"""
    output.write_text(report_content, encoding="utf-8")
    return output

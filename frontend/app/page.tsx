"use client";

import { useCallback, useEffect, useState } from "react";
import { Activity, ArrowDownRight, ArrowUpRight, Bell, ChevronDown, CircleHelp, LayoutDashboard, LineChart, Menu, Plus, Search, Settings, ShieldCheck, WalletCards } from "lucide-react";
import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

type Bar = {
  date: string;
  close: number;
  volume?: number;
  sma_20?: number | null;
  sma_50?: number | null;
  ema_12?: number | null;
  ema_26?: number | null;
  rsi_14?: number | null;
  bb_upper?: number | null;
  bb_lower?: number | null;
};

type Quote = {
  symbol: string;
  price: number | null;
  change: number | null;
  change_pct: number | null;
  signal?: string;
};

type Holding = {
  symbol: string;
  shares: number;
  average_cost: number;
  price: number | null;
  market_value: number | null;
  gain_loss: number | null;
  change_pct?: number | null;
};

type Alert = {
  id: string;
  symbol: string;
  condition: string;
  threshold: number;
  triggered: boolean;
  current_value?: number;
};

type SignalInfo = {
  label: string;
  reason: string;
  rsi_14?: number | null;
};

const money = (value: number | undefined | null) =>
  value == null ? "—" : new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(value);

const pct = (value: number | undefined | null) =>
  value == null ? "—" : `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;

export default function Dashboard() {
  const [watchlist, setWatchlist] = useState<Quote[]>([]);
  const [portfolio, setPortfolio] = useState<{
    holdings: Holding[];
    market_value: number;
    cost_basis: number;
    gain_loss: number;
  }>({ holdings: [], market_value: 0, cost_basis: 0, gain_loss: 0 });
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [chart, setChart] = useState<Bar[]>([]);
  const [indicatorSignal, setIndicatorSignal] = useState<SignalInfo>({ label: "Loading…", reason: "" });
  const [symbol, setSymbol] = useState("AAPL");
  const [period, setPeriod] = useState("6mo");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("Connecting to API…");
  const [apiUp, setApiUp] = useState(false);
  const [provider, setProvider] = useState("demo");
  const [busy, setBusy] = useState(false);
  const [backtestResult, setBacktestResult] = useState<any>(null);
  const [alertSymbol, setAlertSymbol] = useState("AAPL");
  const [alertThreshold, setAlertThreshold] = useState("200");

  // Indicator overlays
  const [showSma20, setShowSma20] = useState(true);
  const [showSma50, setShowSma50] = useState(true);
  const [showBands, setShowBands] = useState(true);

  const load = useCallback(async () => {
    try {
      const [watch, port, alertData, indicatorsData] = await Promise.all([
        fetch(`${API}/watchlist`).then((r) => { if (!r.ok) throw Error(); return r.json(); }),
        fetch(`${API}/portfolio`).then((r) => { if (!r.ok) throw Error(); return r.json(); }),
        fetch(`${API}/alerts`).then((r) => { if (!r.ok) throw Error(); return r.json(); }),
        fetch(`${API}/market/${symbol}/indicators?period=${period}`).then((r) => { if (!r.ok) throw Error(); return r.json(); }),
      ]);
      setWatchlist(watch.items || []);
      setPortfolio(port);
      setAlerts(alertData.alerts || []);
      setChart(indicatorsData.data || []);
      setIndicatorSignal(indicatorsData.signal || { label: "Neutral", reason: "N/A" });
      setProvider(indicatorsData.provider || "demo");
      setApiUp(true);
      setStatus(`${indicatorsData.provider} quotes · refreshes every five minutes · educational data`);
    } catch {
      setApiUp(false);
      setStatus("API offline · start the FastAPI server to load data");
    }
  }, [symbol, period]);

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 300000);
    return () => window.clearInterval(timer);
  }, [load]);

  const addSymbol = async (event: React.FormEvent) => {
    event.preventDefault();
    const next = [...new Set([...watchlist.map((x) => x.symbol), search.trim().toUpperCase()])].filter(Boolean);
    if (!search.trim()) return;
    await fetch(`${API}/watchlist`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbols: next }),
    });
    setSearch("");
    void load();
  };

  const runBacktest = async () => {
    setBusy(true);
    try {
      const response = await fetch(`${API}/backtest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol,
          fast_window: 20,
          slow_window: 50,
          initial_cash: 10000,
          transaction_cost_bps: 10,
        }),
      });
      const result = await response.json();
      if (!response.ok) throw Error(result.detail);
      setBacktestResult(result);
    } catch (error: any) {
      setStatus(error.message || "Could not run backtest");
    } finally {
      setBusy(false);
    }
  };

  const addAlert = async (event: React.FormEvent) => {
    event.preventDefault();
    await fetch(`${API}/alerts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol: alertSymbol, condition: "price_above", threshold: Number(alertThreshold) }),
    });
    void load();
  };

  const selected = watchlist.find((x) => x.symbol === symbol);
  const chartData = chart.map((row) => ({ ...row, date: row.date ? row.date.slice(5) : "" }));

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark"><Activity size={19} /></span>
          <span>Market<span className="brand-light">Scope</span><small>STUDENT TERMINAL</small></span>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav>
          <a className="nav-item active"><LayoutDashboard size={17} />Overview</a>
          <a className="nav-item" href="#watchlist"><LineChart size={17} />Markets</a>
          <a className="nav-item" href="#portfolio"><WalletCards size={17} />Portfolio</a>
          <a className="nav-item" href="#alerts"><Bell size={17} />Alerts <span className="nav-count">{alerts.length}</span></a>
        </nav>
        <div className="sidebar-bottom">
          <div className="plan-card">
            <span className="plan-icon"><ShieldCheck size={17} /></span>
            <b>Research mode</b>
            <p>Signals are educational and are not investment advice.</p>
            <a href="#methodology">Read methodology <span>↗</span></a>
          </div>
          <a className="nav-item muted"><Settings size={17} />Settings</a>
          <div className="user-row">
            <div className="avatar">A</div>
            <span><b>Analyst workspace</b><small>Student edition</small></span>
            <ChevronDown size={15} />
          </div>
        </div>
      </aside>

      <section className="main-area">
        <header className="topbar">
          <button className="mobile-menu" aria-label="Menu"><Menu size={19} /></button>
          <div className="crumb">Workspace <span>/</span> <b>Overview</b></div>
          <div className="top-actions">
            <span className={`connection ${apiUp ? "connected" : ""}`}>
              <i /> {apiUp ? "API connected" : "API disconnected"}
            </span>
            <button className="icon-button" aria-label="Help"><CircleHelp size={18} /></button>
            <div className="avatar small-avatar">A</div>
          </div>
        </header>

        <div className="content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                DAILY MARKET REVIEW <span className="market-open"><i /> {provider.toUpperCase()} PROVIDER</span>
              </div>
              <h1>Market overview</h1>
              <p className="subheading">A clear view of your watchlist, portfolio, and strategy signals.</p>
            </div>
            <button className="outline-button" onClick={() => void load()}>
              <Activity size={15} /> Refresh data
            </button>
          </div>

          <div className="status-line">
            <span className={apiUp ? "status-dot" : "status-dot off"} />
            {status}
            <span className="status-note">Provider timestamps are shown per quote</span>
          </div>

          <div className="metric-grid">
            <article className="metric-card">
              <div className="metric-top">Portfolio value <span className="metric-icon purple"><WalletCards size={17} /></span></div>
              <div className="metric-value">{money(portfolio.market_value)}</div>
              <div className={`metric-foot ${portfolio.gain_loss >= 0 ? "positive" : "negative"}`}>
                {portfolio.gain_loss >= 0 ? <ArrowUpRight size={15} /> : <ArrowDownRight size={15} />} {money(Math.abs(portfolio.gain_loss))} <span>unrealized gain</span>
              </div>
            </article>
            <article className="metric-card">
              <div className="metric-top">Today's portfolio move <span className="metric-icon green"><LineChart size={17} /></span></div>
              <div className="metric-value">
                {pct(portfolio.holdings.length ? portfolio.holdings.reduce((s, h) => s + (h.change_pct || 0) * (h.market_value || 0), 0) / (portfolio.market_value || 1) : 0)}
              </div>
              <div className="metric-foot muted-foot">Weighted by current position value</div>
            </article>
            <article className="metric-card">
              <div className="metric-top">Tracked symbols <span className="metric-icon blue"><Activity size={17} /></span></div>
              <div className="metric-value">{watchlist.length.toString().padStart(2, "0")}</div>
              <div className="metric-foot muted-foot">Across your watchlist</div>
            </article>
            <article className="metric-card">
              <div className="metric-top">Active alerts <span className="metric-icon amber"><Bell size={17} /></span></div>
              <div className="metric-value">{alerts.filter((a) => !a.triggered).length.toString().padStart(2, "0")}</div>
              <div className="metric-foot muted-foot">{alerts.filter((a) => a.triggered).length} triggered</div>
            </article>
          </div>

          <div className="primary-grid">
            <section className="panel chart-panel">
              <div className="panel-heading">
                <div>
                  <div className="panel-title">Price performance & Technical Indicators</div>
                  <div className="panel-caption">{symbol} · Adjusted close with SMA & Bollinger Overlays · USD</div>
                </div>
                <div className="chart-controls">
                  <div className="symbol-picker">
                    <Search size={14} />
                    <input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} aria-label="Chart symbol" />
                  </div>
                  <select value={period} onChange={(e) => setPeriod(e.target.value)} aria-label="Chart period">
                    <option value="1mo">1M</option>
                    <option value="3mo">3M</option>
                    <option value="6mo">6M</option>
                    <option value="1y">1Y</option>
                    <option value="2y">2Y</option>
                  </select>
                </div>
              </div>

              <div className="chart-summary">
                <div>
                  <b>{money(selected?.price ?? chart.at(-1)?.close)}</b>
                  <span className={(selected?.change_pct || 0) >= 0 ? "positive" : "negative"}>
                    {pct(selected?.change_pct)} <small>latest bar</small>
                  </span>
                </div>
                <div style={{ display: "flex", gap: "8px", alignItems: "center", fontSize: "0.85rem" }}>
                  <span className="pill" style={{ background: "#edf2ff", color: "#3b5bdb", fontWeight: 600 }}>
                    Signal: {indicatorSignal.label}
                  </span>
                  {indicatorSignal.rsi_14 != null && (
                    <span className="pill" style={{ background: "#f1f3f5", color: "#495057" }}>
                      RSI-14: {indicatorSignal.rsi_14.toFixed(1)}
                    </span>
                  )}
                </div>
              </div>

              {/* Indicator Toggle Controls */}
              <div style={{ display: "flex", gap: "12px", padding: "4px 0 10px 0", fontSize: "0.82rem", alignItems: "center" }}>
                <span style={{ color: "#6b7280", fontWeight: 500 }}>Overlays:</span>
                <label style={{ display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" }}>
                  <input type="checkbox" checked={showSma20} onChange={(e) => setShowSma20(e.target.checked)} />
                  <span style={{ color: "#10b981", fontWeight: 600 }}>SMA 20</span>
                </label>
                <label style={{ display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" }}>
                  <input type="checkbox" checked={showSma50} onChange={(e) => setShowSma50(e.target.checked)} />
                  <span style={{ color: "#8b5cf6", fontWeight: 600 }}>SMA 50</span>
                </label>
                <label style={{ display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" }}>
                  <input type="checkbox" checked={showBands} onChange={(e) => setShowBands(e.target.checked)} />
                  <span style={{ color: "#0ea5e9", fontWeight: 600 }}>Bollinger Bands (20, 2σ)</span>
                </label>
              </div>

              <div className="chart-wrap">
                {chart.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={chartData} margin={{ top: 14, right: 8, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#4e65dd" stopOpacity={0.22} />
                          <stop offset="95%" stopColor="#4e65dd" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="#edf0f6" vertical={false} />
                      <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#9299aa" }} minTickGap={38} />
                      <YAxis orientation="right" tickLine={false} axisLine={false} width={50} domain={["auto", "auto"]} tick={{ fontSize: 11, fill: "#9299aa" }} tickFormatter={(v) => `$${v}`} />
                      <Tooltip formatter={(v: any, name: string) => [money(Number(v)), name]} labelStyle={{ color: "#29334b" }} />
                      <Area type="monotone" dataKey="close" stroke="#5269dc" strokeWidth={2.2} fill="url(#priceFill)" name="Close" />
                      {showSma20 && <Line type="monotone" dataKey="sma_20" stroke="#10b981" strokeWidth={1.8} dot={false} name="SMA 20" />}
                      {showSma50 && <Line type="monotone" dataKey="sma_50" stroke="#8b5cf6" strokeWidth={1.8} dot={false} name="SMA 50" />}
                      {showBands && <Line type="monotone" dataKey="bb_upper" stroke="#38bdf8" strokeWidth={1.2} strokeDasharray="3 3" dot={false} name="Upper Band" />}
                      {showBands && <Line type="monotone" dataKey="bb_lower" stroke="#38bdf8" strokeWidth={1.2} strokeDasharray="3 3" dot={false} name="Lower Band" />}
                    </ComposedChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="empty-chart">{apiUp ? "Loading chart…" : "Start the API to load the demo price chart."}</div>
                )}
              </div>

              <div className="chart-legend">
                <span><i className="legend-line" /> Closing price</span>
                <span className="chart-source">{selected?.symbol || symbol} · {period} view</span>
              </div>
            </section>

            <section className="panel watch-panel" id="watchlist">
              <div className="panel-heading">
                <div>
                  <div className="panel-title">Your watchlist</div>
                  <div className="panel-caption">Daily snapshot and signal summary</div>
                </div>
                <button className="text-button" onClick={() => void load()}>View all <span>→</span></button>
              </div>
              <form className="add-symbol" onSubmit={addSymbol}>
                <Search size={14} />
                <input placeholder="Add a ticker…" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Ticker symbol" />
                <button aria-label="Add symbol"><Plus size={16} /></button>
              </form>
              <div className="watch-table">
                <div className="table-head">
                  <span>SYMBOL</span><span>PRICE</span><span>CHANGE</span>
                </div>
                {watchlist.map((item) => (
                  <button className={`watch-row ${item.symbol === symbol ? "chosen" : ""}`} key={item.symbol} onClick={() => setSymbol(item.symbol)}>
                    <span className="ticker">
                      <span className={`ticker-logo logo-${item.symbol.slice(0, 1).toLowerCase()}`}>{item.symbol.slice(0, 1)}</span>
                      <b>{item.symbol}</b>
                    </span>
                    <span>{money(item.price)}</span>
                    <span className={(item.change_pct || 0) >= 0 ? "positive" : "negative"}>{pct(item.change_pct)}</span>
                  </button>
                ))}
              </div>
              <div className="signal-note">
                <span className="signal-spark">✦</span>
                <span><b>Signals are indicators, not instructions.</b><small>Review the underlying data before drawing conclusions.</small></span>
              </div>
            </section>
          </div>

          <div className="lower-grid">
            <section className="panel portfolio-panel" id="portfolio">
              <div className="panel-heading">
                <div>
                  <div className="panel-title">Portfolio positions</div>
                  <div className="panel-caption">Holdings and unrealized performance</div>
                </div>
                <span className="pill">{portfolio.holdings.length} positions</span>
              </div>
              <div className="portfolio-table">
                <div className="table-head">
                  <span>ASSET</span><span>SHARES</span><span>LAST PRICE</span><span>MARKET VALUE</span><span>GAIN / LOSS</span>
                </div>
                {portfolio.holdings.map((h) => (
                  <div className="portfolio-row" key={h.symbol}>
                    <span className="ticker">
                      <span className="ticker-logo">{h.symbol.slice(0, 1)}</span>
                      <b>{h.symbol}</b>
                    </span>
                    <span>{h.shares}</span>
                    <span>{money(h.price)}</span>
                    <span>{money(h.market_value)}</span>
                    <span className={(h.gain_loss || 0) >= 0 ? "positive" : "negative"}>{money(h.gain_loss)}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="panel strategy-panel">
              <div className="panel-heading">
                <div>
                  <div className="panel-title">Strategy lab</div>
                  <div className="panel-caption">Moving average crossover · Next-bar execution</div>
                </div>
                <span className="lab-tag">SIMULATION</span>
              </div>
              <div className="strategy-copy">Compare a simple rules-based strategy against holding the asset.</div>
              <div className="strategy-settings">
                <span><small>FAST SMA</small><b>20 days</b></span>
                <span><small>SLOW SMA</small><b>50 days</b></span>
                <span><small>STARTING CASH</small><b>$10,000</b></span>
              </div>
              <button className="primary-button" disabled={busy || !apiUp} onClick={runBacktest}>
                {busy ? "Running simulation…" : "Run backtest"}<span>→</span>
              </button>
              {backtestResult && (
                <div className="backtest-result">
                  <b>{pct(backtestResult.metrics.total_return_pct)}</b>
                  <span>strategy return</span>
                  <small>
                    Buy & hold: {pct(backtestResult.metrics.buy_and_hold_pct)} · Max drawdown: {pct(backtestResult.metrics.max_drawdown_pct)} · Trades: {backtestResult.metrics.trade_count}
                  </small>
                </div>
              )}
              <p className="fine-print">Past performance does not predict future results. Educational simulation only.</p>
            </section>
          </div>

          <section className="panel alerts-panel" id="alerts">
            <div className="panel-heading">
              <div>
                <div className="panel-title">Price alerts</div>
                <div className="panel-caption">Evaluated against the latest available bar when refreshed</div>
              </div>
              <form className="alert-create" onSubmit={addAlert}>
                <input value={alertSymbol} onChange={(e) => setAlertSymbol(e.target.value.toUpperCase())} aria-label="Alert symbol" />
                <span>above $</span>
                <input value={alertThreshold} onChange={(e) => setAlertThreshold(e.target.value)} aria-label="Price threshold" type="number" />
                <button className="outline-button"><Plus size={14} /> Create</button>
              </form>
            </div>
            <div className="alert-list">
              {alerts.length ? (
                alerts.map((alert) => (
                  <div className="alert-row" key={alert.id}>
                    <span className={`alert-icon ${alert.triggered ? "triggered" : ""}`}><Bell size={16} /></span>
                    <span>
                      <b>{alert.symbol}</b> price {alert.condition.replace("price_", "")} {money(alert.threshold)}
                      <small>{alert.triggered ? "Threshold reached" : "Waiting for threshold"}</small>
                    </span>
                    <span className={`alert-state ${alert.triggered ? "triggered-text" : ""}`}>
                      {alert.triggered ? "Triggered" : "Monitoring"}
                    </span>
                  </div>
                ))
              ) : (
                <div className="empty-alerts">No alerts yet. Add one above to monitor a price level.</div>
              )}
            </div>
          </section>

          <footer className="footer" id="methodology">
            <span>MarketScope · Built for learning and portfolio demonstration</span>
            <span><ShieldCheck size={14} /> Educational use only · Not financial advice</span>
          </footer>
        </div>
      </section>
    </main>
  );
}

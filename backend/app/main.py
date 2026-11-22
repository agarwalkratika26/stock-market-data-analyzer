from datetime import datetime, timezone

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import data_store
from .analytics import add_indicators, backtest, current_signal
from .config import settings
from .market_data import frame_records, history
from .schemas import AlertCreate, BacktestRequest, PortfolioUpdate, WatchlistUpdate

app = FastAPI(title=settings.app_name, version="1.0.0", description="Educational market data and strategy research API")
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def load_data(symbol: str, period: str = "6mo", provider: str | None = None):
    try:
        return history(symbol, period, provider)
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=502 if isinstance(exc, RuntimeError) else 400, detail=str(exc)) from exc


def latest_quote(symbol: str) -> dict:
    frame, source = load_data(symbol, "1mo")
    row = frame.iloc[-1]
    previous = frame.iloc[-2] if len(frame) > 1 else row
    close, prior = float(row["close"]), float(previous["close"])
    quote_type = "latest_daily_bar"
    if source == "yfinance":
        try:
            import yfinance as yf

            info = yf.Ticker(symbol.upper()).fast_info
            live_price = info.get("last_price")
            previous_close = info.get("previous_close")
            if live_price is not None:
                close = float(live_price)
                prior = float(previous_close) if previous_close else prior
                quote_type = "provider_snapshot"
        except Exception:
            # The daily history remains useful if the provider snapshot is unavailable.
            pass
    return {"symbol": symbol.upper(), "price": round(close, 2), "change": round(close - prior, 2),
            "change_pct": round((close / prior - 1) * 100, 2) if prior else 0,
            "as_of": pd.Timestamp(row["date"]).strftime("%Y-%m-%d"), "source": source, "quote_type": quote_type,
            "fetched_at_utc": datetime.now(timezone.utc).isoformat()}


@app.get("/")
def root():
    return {"name": settings.app_name, "docs": "/docs", "data_mode": settings.default_provider}


@app.get(f"{settings.api_prefix}/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat(), "provider": settings.default_provider}


@app.get(f"{settings.api_prefix}/market/{{symbol}}/history")
def market_history(symbol: str, period: str = "6mo", provider: str | None = None):
    frame, source = load_data(symbol, period, provider)
    return {"symbol": symbol.upper(), "provider": source, "period": period, "data": frame_records(frame)}


@app.get(f"{settings.api_prefix}/market/{{symbol}}/indicators")
def market_indicators(symbol: str, period: str = "6mo", provider: str | None = None):
    frame, source = load_data(symbol, period, provider)
    data = add_indicators(frame)
    current = data.iloc[-1]
    values = {key: (round(float(current[key]), 4) if pd.notna(current[key]) else None) for key in ["sma_20", "sma_50", "ema_12", "ema_26", "macd", "macd_signal", "rsi_14", "bb_upper", "bb_lower"]}
    return {"symbol": symbol.upper(), "provider": source, "indicators": values, "signal": current_signal(current), "data": frame_records(data.tail(120))}


@app.get(f"{settings.api_prefix}/market/{{symbol}}/quote")
def quote(symbol: str):
    """Return the latest available bar; this is a polled snapshot, not a real-time feed."""
    return latest_quote(symbol)


@app.get(f"{settings.api_prefix}/watchlist")
def get_watchlist():
    symbols = data_store.read("watchlist.json")
    result = []
    for symbol in symbols:
        try:
            q = latest_quote(symbol)
            frame, _ = load_data(symbol, "6mo")
            signal = current_signal(add_indicators(frame).iloc[-1])
            result.append({**q, "signal": signal["label"]})
        except HTTPException:
            result.append({"symbol": symbol, "price": None, "change": None, "change_pct": None, "signal": "Unavailable"})
    return {"symbols": symbols, "items": result}


@app.put(f"{settings.api_prefix}/watchlist")
def update_watchlist(payload: WatchlistUpdate):
    symbols = list(dict.fromkeys(s.strip().upper() for s in payload.symbols if s.strip()))
    if not symbols:
        raise HTTPException(400, "Add at least one symbol")
    data_store.write("watchlist.json", symbols)
    return get_watchlist()


@app.get(f"{settings.api_prefix}/portfolio")
def get_portfolio():
    holdings = data_store.read("portfolio.json")
    positions, total_value, total_cost = [], 0.0, 0.0
    for holding in holdings:
        try:
            q = latest_quote(holding["symbol"])
            price = q["price"]
            value = price * holding["shares"]
            cost = holding["average_cost"] * holding["shares"]
            positions.append({**holding, "price": price, "market_value": round(value, 2), "gain_loss": round(value - cost, 2), "change_pct": q["change_pct"]})
            total_value += value
            total_cost += cost
        except HTTPException:
            positions.append({**holding, "price": None, "market_value": None, "gain_loss": None, "change_pct": None})
    return {"holdings": positions, "market_value": round(total_value, 2), "cost_basis": round(total_cost, 2), "gain_loss": round(total_value - total_cost, 2)}


@app.put(f"{settings.api_prefix}/portfolio")
def update_portfolio(payload: PortfolioUpdate):
    holdings = [item.model_dump() | {"symbol": item.symbol.strip().upper()} for item in payload.holdings]
    data_store.write("portfolio.json", holdings)
    return get_portfolio()


@app.get(f"{settings.api_prefix}/alerts")
def get_alerts():
    alerts = data_store.read("alerts.json")
    for alert in alerts:
        if alert.get("triggered"):
            continue
        try:
            quote_data = latest_quote(alert["symbol"])
            frame, _ = load_data(alert["symbol"], "6mo")
            indicators = add_indicators(frame).iloc[-1]
            value = quote_data["price"] if alert["condition"].startswith("price") else float(indicators["rsi_14"])
            alert["current_value"] = round(value, 2)
            alert["triggered"] = (value > alert["threshold"] if alert["condition"].endswith("above") else value < alert["threshold"])
            if alert["triggered"]:
                alert["triggered_at"] = datetime.now(timezone.utc).isoformat()
        except (HTTPException, ValueError):
            alert["current_value"] = None
    data_store.write("alerts.json", alerts)
    return {"alerts": alerts}


@app.post(f"{settings.api_prefix}/alerts", status_code=201)
def create_alert(payload: AlertCreate):
    alerts = data_store.read("alerts.json")
    alert = {"id": f"{int(datetime.now(timezone.utc).timestamp() * 1000)}", **payload.model_dump(), "symbol": payload.symbol.strip().upper(), "triggered": False, "created_at": datetime.now(timezone.utc).isoformat()}
    alerts.insert(0, alert)
    data_store.write("alerts.json", alerts)
    return alert


@app.delete(f"{settings.api_prefix}/alerts/{{alert_id}}")
def delete_alert(alert_id: str):
    alerts = data_store.read("alerts.json")
    remaining = [alert for alert in alerts if alert["id"] != alert_id]
    if len(remaining) == len(alerts):
        raise HTTPException(404, "Alert not found")
    data_store.write("alerts.json", remaining)
    return {"deleted": alert_id}


@app.post(f"{settings.api_prefix}/backtest")
def run_backtest(payload: BacktestRequest, period: str = Query(default="2y")):
    frame, source = load_data(payload.symbol, period)
    try:
        result = backtest(frame, payload.fast_window, payload.slow_window, payload.initial_cash, payload.transaction_cost_bps)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"symbol": payload.symbol.upper(), "provider": source, "strategy": payload.strategy, **result}


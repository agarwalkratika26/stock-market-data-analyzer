from typing import Literal

from pydantic import BaseModel, Field


class WatchlistUpdate(BaseModel):
    symbols: list[str] = Field(min_length=1, max_length=30)


class HoldingInput(BaseModel):
    symbol: str = Field(min_length=1, max_length=12)
    shares: float = Field(gt=0)
    average_cost: float = Field(gt=0)


class PortfolioUpdate(BaseModel):
    holdings: list[HoldingInput] = Field(max_length=50)


class BacktestRequest(BaseModel):
    symbol: str = "AAPL"
    strategy: Literal["sma_crossover"] = "sma_crossover"
    fast_window: int = Field(default=20, ge=2, le=100)
    slow_window: int = Field(default=50, ge=3, le=250)
    initial_cash: float = Field(default=10000, gt=0)
    transaction_cost_bps: float = Field(default=10, ge=0, le=500)


class AlertCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=12)
    condition: Literal["price_above", "price_below", "rsi_above", "rsi_below"]
    threshold: float


import json
from pathlib import Path
from typing import Any

from .config import settings


DEFAULTS: dict[str, Any] = {
    "watchlist.json": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"],
    "portfolio.json": [
        {"symbol": "AAPL", "shares": 10, "average_cost": 180},
        {"symbol": "MSFT", "shares": 5, "average_cost": 390},
        {"symbol": "NVDA", "shares": 8, "average_cost": 115},
    ],
    "alerts.json": [],
}


def _path(name: str) -> Path:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings.data_dir / name


def read(name: str) -> Any:
    path = _path(name)
    if not path.exists():
        write(name, DEFAULTS[name])
    return json.loads(path.read_text(encoding="utf-8"))


def write(name: str, value: Any) -> Any:
    path = _path(name)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temp.replace(path)
    return value

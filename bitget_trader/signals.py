from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

@dataclass(slots=True)
class Signal:
    type: Literal["buy", "sell"]
    symbol: str
    amount: float | None  # USDT for buy; None for sell
    users: Sequence[str] | None  # optional list of trader ids

    @classmethod
    def from_json(cls, data: dict[str, object]) -> "Signal":
        if data.get("type") not in {"buy", "sell"}:
            raise ValueError("invalid type")
        if "symbol" not in data:
            raise ValueError("symbol required")
        if data["type"] == "buy" and "amount" not in data:
            raise ValueError("amount required for buy")
        return cls(
            type=data["type"],
            symbol=str(data["symbol"]).upper(),
            amount=float(data.get("amount", 0)) if data["type"] == "buy" else None,
            users=list(map(str, data.get("users", []))) or None,
        )
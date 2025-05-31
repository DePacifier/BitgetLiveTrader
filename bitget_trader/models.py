from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, Float, DateTime

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Position(Base):
    __tablename__ = "positions"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(String, index=True)
    symbol = mapped_column(String, index=True)
    status = mapped_column(String, default="OPEN")  # OPEN/CLOSED
    qty = mapped_column(Float)           # base coin
    avg_cost_usdt = mapped_column(Float)
    total_buy_fees = mapped_column(Float, default=0.0)
    total_sell_fees = mapped_column(Float, default=0.0)
    total_buy_amount = mapped_column(Float, default=0.0)   # total USDT spent buying the asset
    total_sell_amount = mapped_column(Float, default=0.0)  # total USDT received from selling the asset
    realised_pnl = mapped_column(Float, nullable=True)
    opened_at = mapped_column(DateTime, default=datetime.now(timezone.utc))
    closed_at = mapped_column(DateTime, nullable=True)
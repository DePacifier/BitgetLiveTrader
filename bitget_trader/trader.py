from __future__ import annotations

import asyncio
import uuid 
import logging
from datetime import datetime, timezone
from typing import DefaultDict
from collections import defaultdict
from sqlalchemy import select

from .signals import Signal
from .exchange import Exchange
from .models import Position
from .db import async_session
from .config import settings
from .notifier import notify

_log = logging.getLogger(__name__)

class Trader:
    def __init__(self, cfg):
        self.id: str = cfg.id
        self._exchange = Exchange(
            cfg.api_key.get_secret_value(),
            cfg.api_secret.get_secret_value(),
            cfg.passphrase.get_secret_value(),
            cfg.demo_mode,
        )
        self._locks: DefaultDict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._timeout_buy = settings.timeouts.buy
        self._timeout_sell = settings.timeouts.sell
        self.chat_id: int = cfg.notify_chat

    async def handle(self, sig: Signal):
        lock = self._locks[sig.symbol]
        async with lock:
            if sig.type == "buy":
                balance = await self._exchange.get_available_usdt()
                if sig.amount <= balance:
                    _log.info(f"Handling buy signal: {sig}")
                    await self._handle_buy(sig, balance)
                else:
                    await notify(self.chat_id, f"ℹ️ Insufficient USDT for {sig.symbol} buy • {sig.amount} USDT required")
            else:
                await self._handle_sell(sig)

    async def _handle_buy(self, sig: Signal, balance: float):
        client_oid = str(uuid.uuid4())
        await notify(self.chat_id, f"🔔 BUY sent • {sig.symbol} • {sig.amount} USDT")
        order = await self._exchange.create_market_buy(sig.symbol.replace("USDT", "/USDT"), sig.amount, client_oid)
        filled = await self._await_fill(order["id"], sig.symbol)
        if not filled:
            await notify(self.chat_id, f"❌ BUY failed • {sig.symbol}")
            await self._exchange.cancel_order(order["id"], sig.symbol.replace("USDT", "/USDT"))
            await notify(self.chat_id, f"Successfully cancelled order {order['id']} for {sig.symbol}")
            return
        base_qty = float(filled["filled"])
        fee = float(filled["fee"]["cost"])
        price = float(filled["average"])
        cost = float(filled["cost"])
        new_balance = balance - sig.amount
        fee_pct = fee / sig.amount * 100 if sig.amount else 0
        await notify(
            self.chat_id,
            (
            f"✅ BUY filled • +{base_qty:.8g} {sig.symbol[:-4]} @ ${price:,.2f}\n"
            f"• Order Cost: ${cost:,.2f} (targeted ${sig.amount:,.2f})\n"
            f"• Fee: ${fee:.5g} ({fee_pct:.2f}%)\n"
            f"• Remaining Balance: ${new_balance:,.2f}"
            )
        )
        async with async_session() as sess:
            pos = await sess.scalar(
                select(Position).where(Position.user_id == self.id, Position.symbol == sig.symbol, Position.status == "OPEN")
            )
            if pos:
                old_qty = pos.qty
                old_cost = pos.avg_cost_usdt * old_qty
                new_qty = old_qty + base_qty
                pos.qty = new_qty
                pos.avg_cost_usdt = (old_cost + cost) / new_qty
                pos.total_buy_fees += fee
                pos.total_buy_amount += cost
                await sess.commit()
                await notify(
                    self.chat_id,
                    f"📈 Added {base_qty:.8g} → total {new_qty:.8g} • new VWAP ${pos.avg_cost_usdt:,.2f}",
                )
            else:
                pos = Position(
                    user_id=self.id,
                    symbol=sig.symbol,
                    qty=float(base_qty),
                    avg_cost_usdt=float(price),
                    total_buy_fees=float(fee),
                    total_buy_amount=float(cost)
                )
                sess.add(pos)
                await sess.commit()

    async def _handle_sell(self, sig: Signal):
        async with async_session() as sess:
            pos = await sess.scalar(
                select(Position).where(Position.user_id == self.id, Position.symbol == sig.symbol, Position.status == "OPEN")
            )
            if not pos:
                await notify(self.chat_id, f"ℹ️ No open position for {sig.symbol}")
                return
            client_oid = str(uuid.uuid4())
            await notify(self.chat_id, f"🔔 SELL sent • {sig.symbol} • {pos.qty:.8g} {sig.symbol[:-4]}")
            order = await self._exchange.create_market_sell(sig.symbol, pos.qty, client_oid)
            filled = await self._await_fill(order["id"], sig.symbol)
            if not filled:
                await notify(self.chat_id, f"❌ SELL failed • {sig.symbol}")
                return
            fee = float(filled["fee"]["cost"])
            proceeds = float(filled["cost"])
            pos.total_sell_amount += proceeds
            pnl = pos.total_sell_amount - pos.total_buy_amount - pos.total_buy_fees - fee
            pnl_pct = pnl / pos.total_buy_amount * 100.0 if pos.total_buy_amount else 0.0
            pos.status = "CLOSED"
            pos.total_sell_fees = float(fee)
            pos.realised_pnl = float(pnl)
            pos.closed_at = datetime.now(timezone.utc)
            await sess.commit()
            # Retrieve the current USDT balance after the sell order
            current_balance = await self._exchange.get_available_usdt()
            # Calculate average sell price (assuming pos.qty is not zero)
            avg_sell_price = pos.total_sell_amount / pos.qty if pos.qty else 0
            message = (
                f"✅ SELL filled • Sold {pos.qty:.8g} {sig.symbol[:-4]} at avg sell ${avg_sell_price:,.2f}\n"
                f"• Total BUY Cost: ${pos.total_buy_amount:,.2f} (avg buy ${pos.avg_cost_usdt:,.2f})\n"
                f"• Total SELL Proceeds: ${pos.total_sell_amount:,.2f}\n"
                f"• Realised P/L: {pnl:+.2f} USDT ({pnl_pct:+.2f}%)\n"
                f"• Fees: Buy Fee ${pos.total_buy_fees:,.5g} + Sell Fee {fee:.5g}\n"
                f"• Current USDT Balance: ${current_balance:,.2f}"
            )
            await notify(self.chat_id, message)

    async def _await_fill(self, order_id: str, symbol: str):
        time_left = self._timeout_buy  # same timeout for buy/sell
        while time_left > 0:
            order = await self._exchange.fetch_order(order_id, symbol.replace("USDT", "/USDT"))
            if order["status"] in {"closed", "filled"}:  # ccxt may map to "closed"
                return order
            await asyncio.sleep(1)
            time_left -= 1
        return None

    async def close(self):
        await self._exchange.close()
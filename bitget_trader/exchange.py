from __future__ import annotations

import ccxt.async_support as ccxt  # type: ignore
from .utils import retry, RateLimiter
from .config import settings

rate_limiter = RateLimiter(settings.rate_limit_rps)

class Exchange:
    """Thin async wrapper around ccxt.bitget with shared rate‑limit."""

    def __init__(self, api_key: str, secret: str, password: str, demo: bool):
        self._client = ccxt.bitget({
            "apiKey": api_key,
            "secret": secret,
            "password": password,
            "options": {"defaultType": "spot"},
        })
        if demo:
            self._client.set_sandbox_mode(True)
            
    @classmethod
    async def create(cls, api_key: str, secret: str, password: str, demo: bool) -> Exchange:
        instance = cls(api_key, secret, password, demo)
        await instance.load_markets()
        return instance

    @retry()
    async def load_markets(self):
        async with rate_limiter:
            return await self._client.load_markets()
    
    @retry()
    async def get_available_usdt(self):
        async with rate_limiter:
            balance = await self._client.fetch_balance()
            return balance['free'].get('USDT', 0.0)

    @retry()
    async def create_market_buy(self, symbol: str, quote_qty: float, client_oid: str):
        async with rate_limiter:
            return await self._client.create_order(symbol, "market", "buy", None, params={"cost":quote_qty, "clientOid": client_oid})

    @retry()
    async def create_market_sell(self, symbol: str, base_qty: float, client_oid: str):
        base_qty = self._client.amount_to_precision(symbol, base_qty)
        async with rate_limiter:
            return await self._client.create_order(symbol, "market", "sell", base_qty, params={"clientOid": client_oid})

    @retry()
    async def fetch_order(self, order_id: str, symbol: str):
        async with rate_limiter:
            return await self._client.fetch_order(order_id, symbol)
        
    @retry()
    async def cancel_order(self, order_id: str, symbol: str):
        async with rate_limiter:
            return await self._client.cancel_order(order_id, symbol)

    async def close(self):
        await self._client.close()
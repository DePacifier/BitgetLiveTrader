from __future__ import annotations

import asyncio, logging
from collections import defaultdict
from typing import Sequence

from .signals import Signal
from .trader import Trader

_log = logging.getLogger(__name__)

class Dispatcher:
    def __init__(self, traders: Sequence[Trader]):
        self._traders = {t.id: t for t in traders}
        self._queue: asyncio.Queue[Signal] = asyncio.Queue()

    async def enqueue(self, sig: Signal):
        await self._queue.put(sig)

    async def _consume(self):
        while True:
            sig = await self._queue.get()
            targets = sig.users or list(self._traders.keys())
            for uid in targets:
                trader = self._traders.get(uid)
                if trader:
                    asyncio.create_task(trader.handle(sig))
            self._queue.task_done()

    async def start(self):
        asyncio.create_task(self._consume())
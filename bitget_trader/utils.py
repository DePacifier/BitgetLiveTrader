from functools import wraps
import asyncio
from typing import Any, Callable, Coroutine, TypeVar

T = TypeVar("T")

class RateLimiter:
    """Simple token bucket rate‑limiter for CCXT calls (shared)."""

    def __init__(self, rps: int):
        self._sem = asyncio.Semaphore(rps)

    async def __aenter__(self):
        await self._sem.acquire()

    async def __aexit__(self, *_):
        await asyncio.sleep(1)
        self._sem.release()

def retry(max_tries: int = 3, initial_delay: float = 0.5):
    def decorator(fn: Callable[..., Coroutine[Any, Any, T]]):
        @wraps(fn)
        async def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            for attempt in range(max_tries):
                try:
                    return await fn(*args, **kwargs)
                except Exception:
                    if attempt == max_tries - 1:
                        raise
                    await asyncio.sleep(delay)
                    delay *= 2
        return wrapper
    return decorator
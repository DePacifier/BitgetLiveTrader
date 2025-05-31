from __future__ import annotations

import logging
from fastapi import FastAPI, HTTPException, Request, status
from contextlib import asynccontextmanager

from .signals import Signal
from .dispatcher import Dispatcher
from .trader import Trader
from .db import init_db
from .config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

_dispatcher: Dispatcher | None = None

async def startDispatcher():
    global _dispatcher, traders
    traders = [Trader(cfg) for cfg in settings.traders]
    _dispatcher = Dispatcher(traders)
    await _dispatcher.start()
    
async def loadMarkets():
    for trader in traders:
        await trader._exchange.load_markets()
    
async def closeTraders():
    for trader in traders:
        await trader.close()
        

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(">> Starting Server")
    await init_db()
    await startDispatcher()
    await loadMarkets()
    yield
    print(">> Shutting down Server")
    await closeTraders()

app = FastAPI(title="Bitget Trader", lifespan=lifespan)


@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    if data.get("auth") != settings.tradingview_secret.get_secret_value():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bad auth")

    try:
        sig = Signal.from_json(data)
        print(f">> Received signal: {sig}")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    await _dispatcher.enqueue(sig)
    return {"status": "ok"}
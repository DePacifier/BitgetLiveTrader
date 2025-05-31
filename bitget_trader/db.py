from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .config import ROOT

DB_PATH = ROOT / "bitget_trader.sqlite3"

engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}", echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db() -> None:
    from .models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
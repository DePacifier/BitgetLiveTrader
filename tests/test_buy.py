import asyncio
from httpx import AsyncClient

async def test_webhook():
    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        r = await ac.post("/webhook", json={"auth":"tv_secret", "type": "buy", "symbol": "BTCUSDT", "amount": 100})
        print(r)
        # assert r.status_code == 200
        # assert r.json()["ok"] is True

if __name__ == "__main__":
    asyncio.run(test_webhook())
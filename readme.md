# Bitget Live Trader

A robust, asynchronous trading automation system for Bitget, built with FastAPI, SQLAlchemy, and ccxt. This project enables you to receive trading signals via webhook, execute trades on Bitget, track positions and P&L, and receive real-time notifications via Telegram.

---

## Features

- **Webhook Signal Receiver**: Accepts buy/sell signals (e.g., from TradingView) via a secure FastAPI endpoint.
- **Dispatcher & Trader Architecture**: Routes signals to the correct trader(s) and manages concurrent trade execution with locking per symbol.
- **Bitget Exchange Integration**: Places and manages spot market orders using ccxt with rate limiting and retry logic.
- **Position Tracking**: All trades and positions are tracked in a SQLite database using SQLAlchemy async ORM.
- **Realized P&L Calculation**: Tracks total buy/sell amounts, fees, and realized profit/loss for each position.
- **Telegram Notifications**: Sends trade and system notifications to configured Telegram chats.
- **Graceful Startup/Shutdown**: Ensures all resources (exchange clients, DB) are properly initialized and closed.
- **Docker & Local Support**: Run locally or in a container with minimal setup.

---

## Architecture Overview

```
[TradingView/Other] --(webhook)--> [FastAPI Receiver] --(Signal)--> [Dispatcher] --(async)--> [Trader(s)]
      |                                                                                      |
      |                                                                                  [Bitget]
      |                                                                                      |
      |                                                                                 [SQLite]
      |                                                                                      |
      |                                                                                 [Telegram]
```

- **receiver.py**: FastAPI app, handles webhook POST, manages app lifecycle.
- **dispatcher.py**: Queues and routes signals to the right Trader(s).
- **trader.py**: Handles trade logic, position management, and notifications.
- **exchange.py**: Async wrapper for ccxt Bitget client, with rate limiting.
- **models.py**: SQLAlchemy models for positions and trade data.
- **notifier.py/telegram_wrapper.py**: Telegram notification abstraction.

---

## Quick Start

### 1. Clone & Install

```bash
# Clone the repo
cd BitgetLiveTrader
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

Copy the example config and edit it:

```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your Bitget API keys, Telegram token, and chat IDs
```

- See `config.yaml.example` for all options.
- **Never commit your real config.yaml!**

### 3. Run Locally

```bash
python -m bitget_trader.receiver
# or
uvicorn bitget_trader.receiver:app --reload --host localhost --port 8000
```

### 4. Run with Docker

```bash
docker build -t bitget-trader .
docker run --rm -p 8000:8000 -v $PWD/config.yaml:/bot/config.yaml bitget-trader
```

---

## API Usage

Send a POST request to `/webhook`:

```json
{
  "auth": "<tradingview_secret>",
  "type": "buy",        // or "sell"
  "symbol": "BTCUSDT",
  "amount": 150          // required for buy, ignored for sell
}
```

- `auth` must match your `tradingview_secret` in config.yaml.
- `users` (optional): list of trader IDs to target specific traders.

---

## Configuration

Edit `config.yaml` (see `config.yaml.example`):

```yaml
traders:
  - id: john
    api_key: "..."
    api_secret: "..."
    passphrase: "..."
    demo_mode: true
    notify_chat: <telegram_chat_id>

timeouts:
  buy: 20
  sell: 20
rate_limit_rps: 15
tradingview_secret: "..."
telegram_token: "..."
```

- **traders**: List of trader configs (API keys, Telegram chat, etc.)
- **timeouts**: Max seconds to wait for order fills.
- **rate_limit_rps**: Max Bitget API calls per second.
- **telegram_token**: Your Telegram bot token.

---

## Database

- Uses SQLite (`bitget_trader.sqlite3` by default).
- Positions table tracks all open/closed trades, buy/sell amounts, fees, and realized P&L.
- DB is auto-initialized on first run.

---

## Notifications

- All trade events and system status are sent to the configured Telegram chat(s).
- Uses the Telegram Bot API (see `telegram_wrapper.py`).

---

## Testing

- Example tests in `tests/` (pytest compatible).
- To run:

```bash
pytest tests/
```

---

## Troubleshooting

- **No DB file created?** Ensure you run via the provided FastAPI app (not just a script).
- **ExchangeError: markets not loaded**: Make sure markets are loaded before trading (handled in app startup).
- **Telegram not sending?** Check your bot token and chat IDs.
- **API errors**: Check logs for details; all errors are logged.

---

## Contributing

Pull requests and issues are welcome! Please open an issue to discuss major changes.

---

## License

MIT License
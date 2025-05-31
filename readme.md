### Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config.yaml.example config.yaml  # edit
python -m bitget_trader.run
```

Expected Post Request
{"auth":"***","type":"buy","symbol":"BTCUSDT","amount":150}
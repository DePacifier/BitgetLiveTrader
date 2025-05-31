import pytest
from bitget_trader.signals import Signal

def test_buy():
    j = {"auth":"tv_secret", "type": "buy", "symbol": "BTCUSDT", "amount": 100}
    sig = Signal.from_json(j)
    assert sig.type == "buy" and sig.amount == 100

@pytest.mark.parametrize("bad", [
    {},
    {"type": "buy"},
    {"type": "foo", "symbol": "BTC"},
])
def test_bad(bad):
    with pytest.raises(ValueError):
        Signal.from_json(bad)
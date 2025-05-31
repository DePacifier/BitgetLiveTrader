from __future__ import annotations

from pathlib import Path
import yaml
from pydantic import BaseModel, SecretStr

ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_CFG = ROOT / "config.yaml"

class _TraderCfg(BaseModel):
    id: str
    api_key: SecretStr
    api_secret: SecretStr
    passphrase: SecretStr
    demo_mode: bool = False
    notify_chat: int

class _Timeouts(BaseModel):
    buy: int = 8
    sell: int = 8

class Settings(BaseModel):
    traders: list[_TraderCfg]
    timeouts: _Timeouts = _Timeouts()
    rate_limit_rps: int = 15
    tradingview_secret: SecretStr
    telegram_token: SecretStr

    @classmethod
    def load(cls, path: Path | None = None) -> "Settings":
        path = path or _DEFAULT_CFG
        with open(path, "r", encoding="utf‑8") as fh:
            raw = yaml.safe_load(fh)
        # env overlay is handled by pydantic Field env
        return cls.model_validate(raw or {})

settings: Settings = Settings.load()
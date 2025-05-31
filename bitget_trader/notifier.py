from __future__ import annotations

import logging
from .config import settings
from .telegram_wrapper import TextMessage, send_notifications_to_multiple_chats

_log = logging.getLogger(__name__)

async def notify(chat_id: int, text: str) -> None:
    try:
        await send_notifications_to_multiple_chats(
            TextMessage(text),
            settings.telegram_token.get_secret_value(),
            [chat_id]
        )
    except Exception as exc:
        _log.error("Telegram notify failed: %s", exc)
import json
import os
from typing import Any, Dict

from app.core.config import get_settings


class MessageService:
    _messages: Dict[str, Dict[str, Any]] = {}
    _loaded = False

    @classmethod
    def load_messages(cls):
        """Loads messages from the locales directory."""
        locales_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "locales"
        )

        if not os.path.exists(locales_dir):
            return

        for filename in os.listdir(locales_dir):
            if filename.endswith(".json"):
                locale = filename.split(".")[0]
                with open(
                    os.path.join(locales_dir, filename), "r", encoding="utf-8"
                ) as f:
                    cls._messages[locale] = json.load(f)
        cls._loaded = True

    @classmethod
    def get_message(cls, key: str, locale: str = None, **kwargs) -> str:
        """
        Retrieves a message by key and locale, formatting it with kwargs.
        Key supports dot notation (e.g. 'entity.not_found').
        """
        if not cls._loaded:
            cls.load_messages()

        settings = get_settings()
        target_locale = locale or settings.locale

        # Fallback to 'en' if locale not found
        if target_locale not in cls._messages:
            target_locale = "en"

        messages = cls._messages.get(target_locale, {})

        # Navigate the nested dictionary using the key
        keys = key.split(".")
        value = messages
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break

        if value is None:
            # Fallback to generic message or key itself if not found
            return f"Message not found for key: {key}"

        if isinstance(value, str):
            try:
                return value.format(**kwargs)
            except KeyError:
                return value

        return str(value)

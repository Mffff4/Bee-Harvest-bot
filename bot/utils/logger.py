import logging
from datetime import datetime
from rich.console import Console
from rich.theme import Theme
from rich.emoji import Emoji
from rich.text import Text
from rich.style import Style
from bot.config import settings

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "success": "green",
    "timestamp": "bright_black",
    "debug": "dim white",
    "number": "bold bright_magenta",
    "honey": "bold yellow",
    "token": "orange1",
    "session": "bold cyan",
    "text": "bright_blue",
    "multiplier": "bold green",
})

console = Console(theme=custom_theme)

class BeeLogger:
    EMOJIS = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "success": "✅",
        "debug": "🔍"
    }

    @staticmethod
    def _get_timestamp():
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def _format_numbers(message: str) -> Text:
        text = Text()
        parts = message.split()
        for part in parts:
            if part.endswith('x'):
                try:
                    float(part[:-1])
                    text.append(part + ' ', style="multiplier")
                    continue
                except ValueError:
                    pass
            try:
                float(part.replace(',', '.'))
                text.append(part + ' ', style="number")
            except ValueError:
                if part == "HONEY":
                    text.append(part + ' ', style="honey")
                elif part == "TOKEN":
                    text.append(part + ' ', style="token")
                else:
                    text.append(part + ' ', style="text")
        return text

    @classmethod
    def _format_message(cls, emoji: str, message: str, level: str) -> Text:
        timestamp = Text(cls._get_timestamp(), style="timestamp")
        emoji_with_space = f"{emoji} "
        if level == "error":
            return Text(f"{emoji_with_space}{timestamp} | {message}", style="error")
        elif level == "warning":
            return Text(f"{emoji_with_space}{timestamp} | {message}", style="warning")
        elif level == "debug":
            return Text(f"{emoji_with_space}{timestamp} | {message}", style="debug")
        parts = message.split(' | ', 1)
        if len(parts) > 1:
            session_name = Text(parts[0], style="session")
            message_text = cls._format_numbers(parts[1])
            full_message = Text()
            full_message.append(emoji_with_space)
            full_message.append(timestamp)
            full_message.append(" | ")
            full_message.append(session_name)
            full_message.append(" | ")
            full_message.append(message_text)
            return full_message
        else:
            return Text(f"{emoji_with_space}{timestamp} | ", style="timestamp") + Text(message, style="text")

    @classmethod
    def info(cls, message: str):
        formatted = cls._format_message(cls.EMOJIS["info"], message, "info")
        console.print(formatted)

    @classmethod
    def warning(cls, message: str):
        formatted = cls._format_message(cls.EMOJIS["warning"], message, "warning")
        console.print(formatted)

    @classmethod
    def error(cls, message: str):
        formatted = cls._format_message(cls.EMOJIS["error"], message, "error")
        console.print(formatted)

    @classmethod
    def success(cls, message: str):
        formatted = cls._format_message(cls.EMOJIS["success"], message, "success")
        console.print(formatted)

    @classmethod
    def debug(cls, message: str):
        if settings.LOGGING_LEVEL.upper() == "DEBUG":
            formatted = cls._format_message(cls.EMOJIS["debug"], message, "debug")
            console.print(formatted)

logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("pyrogram.session.auth").setLevel(logging.WARNING)
logging.getLogger("pyrogram.session.session").setLevel(logging.WARNING)

logger = BeeLogger()

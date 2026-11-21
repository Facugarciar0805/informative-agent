import html
import re

import requests

_HEADING_BOLD_RE = re.compile(r"^#{1,6}[ \t]+\*\*(.+?)\*\*$", re.MULTILINE)
_HEADING_RE = re.compile(r"^#{1,6}[ \t]+(.+)$", re.MULTILINE)
_BULLET_RE = re.compile(r"^[\-\*][ \t]+", re.MULTILINE)
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")


def markdown_to_telegram_html(text: str) -> str:
    """Convierte Markdown básico a HTML compatible con la API de Telegram."""
    converted = html.escape(text, quote=False)
    converted = _HEADING_BOLD_RE.sub(r"<b>\1</b>", converted)
    converted = _HEADING_RE.sub(r"<b>\1</b>", converted)
    converted = _BULLET_RE.sub("• ", converted)
    converted = _BOLD_RE.sub(r"<b>\1</b>", converted)
    converted = _ITALIC_RE.sub(r"<i>\1</i>", converted)
    converted = _LINK_RE.sub(r'<a href="\2">\1</a>', converted)
    return converted


def _pack_parts(parts: list[str], separator: str, max_length: int) -> list[str]:
    """Agrupa fragmentos separados por `separator` sin superar `max_length`."""
    chunks: list[str] = []
    current = ""
    for part in parts:
        candidate = part if not current else f"{current}{separator}{part}"
        if len(candidate) <= max_length:
            current = candidate
            continue
        if current:
            chunks.append(current)
            current = ""
        if len(part) <= max_length:
            current = part
        elif separator == "\n\n":
            chunks.extend(_pack_parts(part.split("\n"), "\n", max_length))
        else:
            chunks.extend(part[i : i + max_length] for i in range(0, len(part), max_length))
    if current:
        chunks.append(current)
    return chunks


def _split_message(text: str, max_length: int = 4000) -> list[str]:
    """Divide mensajes largos por párrafos/líneas respetando el límite de Telegram."""
    if len(text) <= max_length:
        return [text]
    return _pack_parts(text.split("\n\n"), "\n\n", max_length)


class TelegramNotifier:
    """Notificador que envía resúmenes formateados a un chat de Telegram."""

    API_BASE_URL = "https://api.telegram.org"

    def __init__(self, bot_token: str, chat_id: str, timeout: int = 15):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout = timeout

    def send(self, message: str) -> None:
        """Convierte el mensaje a HTML de Telegram, lo divide si hace falta y lo envía."""
        html_message = markdown_to_telegram_html(message)
        chunks = _split_message(html_message, max_length=4000)
        url = f"{self.API_BASE_URL}/bot{self.bot_token}/sendMessage"

        for chunk in chunks:
            if not chunk.strip():
                continue
            payload = {
                "chat_id": self.chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            try:
                resp = requests.post(url, json=payload, timeout=self.timeout)
            except requests.RequestException as exc:
                raise RuntimeError(
                    f"Error de red al enviar mensaje a Telegram ({type(exc).__name__})"
                ) from None

            try:
                data = resp.json()
            except ValueError:
                data = None

            if not resp.ok or not isinstance(data, dict) or data.get("ok") is not True:
                description = data.get("description") if isinstance(data, dict) else resp.text[:200]
                raise RuntimeError(
                    f"Error de Telegram API (HTTP {resp.status_code}): {description}"
                )

import unittest
from unittest.mock import MagicMock, patch

import requests

from src.notifiers.telegram import TelegramNotifier, _split_message, markdown_to_telegram_html


class TelegramNotifierTests(unittest.TestCase):
    def test_markdown_to_telegram_html_converts_formatting_and_preserves_urls(self) -> None:
        sample = (
            "### Política\n"
            "* **Título <prueba> & más:** Texto *clave*. "
            "[Leer más](https://www.infobae.com/a_b/?x=1&y=2)\n"
        )
        out = markdown_to_telegram_html(sample)

        self.assertIn("<b>Política</b>", out)
        self.assertIn("• <b>Título &lt;prueba&gt; &amp; más:</b>", out)
        self.assertIn("<i>clave</i>", out)
        self.assertIn('<a href="https://www.infobae.com/a_b/?x=1&amp;y=2">Leer más</a>', out)

    def test_split_message_respects_max_length(self) -> None:
        long_text = ("a" * 2500) + "\n\n" + ("b" * 2500)
        chunks = _split_message(long_text, max_length=4000)

        self.assertEqual(len(chunks), 2)
        self.assertTrue(all(len(c) <= 4000 for c in chunks))

    def test_send_does_not_leak_bot_token_on_network_or_api_errors(self) -> None:
        secret_token = "123456:SUPER_SECRET_BOT_TOKEN"
        notifier = TelegramNotifier(bot_token=secret_token, chat_id="999")

        with patch(
            "src.notifiers.telegram.requests.post",
            side_effect=requests.ConnectionError(
                f"Failed to reach https://api.telegram.org/bot{secret_token}/sendMessage"
            ),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                notifier.send("Hola")
            self.assertNotIn(secret_token, str(ctx.exception))

        bad_resp = MagicMock(ok=False, status_code=400, text="Bad Request")
        bad_resp.json.return_value = {"ok": False, "description": "Bad Request: chat not found"}
        with patch("src.notifiers.telegram.requests.post", return_value=bad_resp):
            with self.assertRaises(RuntimeError) as ctx:
                notifier.send("Hola")
            self.assertIn("chat not found", str(ctx.exception))
            self.assertNotIn(secret_token, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import MagicMock, patch

from google.genai.errors import ServerError
from strands.types.exceptions import EventLoopException

from src.models import Article
from src.service import generate_daily_briefing, run_daily_briefing
from src.tools import _cached_articles, get_infobae_articles, reset_tool_state


class ServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_tool_state()

    def tearDown(self) -> None:
        reset_tool_state()

    def test_retries_and_fallback_with_date_header_and_link_resolution(self) -> None:
        err = EventLoopException(
            ServerError(503, {"error": {"code": 503, "message": "high demand"}}, None),
            {},
        )
        used_models: list[str | None] = []

        def fake_create_agent(model_id: str | None = None):
            used_models.append(model_id)

            def run(_prompt: str) -> str:
                if model_id == "model-a":
                    raise err
                _cached_articles.append(
                    Article(title="Nota", url="https://www.infobae.com/economia/2026/11/21/exacta/")
                )
                return "### Economía\n* **Nota:** Detalle. [Leer más](#1)"

            return run

        with patch("src.service.create_agent", side_effect=fake_create_agent):
            out = generate_daily_briefing(
                retry_delays=(0,),
                primary_model="model-a",
                fallback_models=("model-b",),
            )

        self.assertEqual(used_models, ["model-a", "model-a", "model-b"])
        self.assertTrue(out.startswith("### Resumen del día — "))
        self.assertIn(
            "[Leer más](https://www.infobae.com/economia/2026/11/21/exacta/)",
            out,
        )

    def test_run_daily_briefing_sends_alert_and_reraises_on_failure(self) -> None:
        notifier = MagicMock()

        with patch("src.service.generate_daily_briefing", side_effect=ValueError("API key inválida")):
            with self.assertRaises(ValueError):
                run_daily_briefing(notifier)

        notifier.send.assert_called_once()
        alert = notifier.send.call_args[0][0]
        self.assertIn("⚠️ Error en el resumen diario", alert)
        self.assertIn("ValueError: API key inválida", alert)

    def test_run_daily_briefing_alerts_when_infobae_returns_no_articles(self) -> None:
        notifier = MagicMock()

        def fake_agent(_prompt: str) -> str:
            with patch("src.tools.InfobaeScraper") as scraper_cls:
                scraper_cls.return_value.get_latest_articles.return_value = []
                get_infobae_articles(limit=5)
            return "No se pudo obtener la información."

        with patch("src.service.create_agent", return_value=fake_agent):
            with self.assertRaises(RuntimeError):
                run_daily_briefing(
                    notifier,
                    retry_delays=(),
                    primary_model="model-a",
                    fallback_models=(),
                )

        notifier.send.assert_called_once()
        alert = notifier.send.call_args[0][0]
        self.assertIn("⚠️ Error en el resumen diario", alert)
        self.assertIn("Infobae no devolvió artículos", alert)

    def test_run_daily_briefing_preserves_original_error_if_alert_send_fails(self) -> None:
        notifier = MagicMock()
        notifier.send.side_effect = RuntimeError("Telegram caído")

        with patch("src.service.generate_daily_briefing", side_effect=ValueError("Fallo original")):
            with self.assertRaises(ValueError) as ctx:
                run_daily_briefing(notifier)

        self.assertEqual(str(ctx.exception), "Fallo original")


if __name__ == "__main__":
    unittest.main()

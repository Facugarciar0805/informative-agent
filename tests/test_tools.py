import unittest
from unittest.mock import patch

from src.models import Article
from src.tools import (
    NO_ARTICLES_MESSAGE,
    _cached_articles,
    get_infobae_articles,
    get_last_articles_error,
    reset_tool_state,
    resolve_article_links,
)


class ToolsTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_tool_state()

    def tearDown(self) -> None:
        reset_tool_state()

    def test_resolve_article_links_handles_valid_typo_and_unchanged_links(self) -> None:
        _cached_articles.append(
            Article(title="Nota 1", url="https://www.infobae.com/politica/2026/11/21/nota-1/")
        )

        text = (
            "A [Leer más](#1) | "
            "B [Leer más](#1] | "
            "C [Directo](https://example.com/a) | "
            "D [Fuera](#99)"
        )
        resolved = resolve_article_links(text)

        self.assertEqual(
            resolved,
            "A [Leer más](https://www.infobae.com/politica/2026/11/21/nota-1/) | "
            "B [Leer más](https://www.infobae.com/politica/2026/11/21/nota-1/) | "
            "C [Directo](https://example.com/a) | "
            "D [Fuera](#99)",
        )

    def test_get_infobae_articles_tracks_and_clears_errors(self) -> None:
        with patch("src.tools.InfobaeScraper") as scraper_cls:
            scraper_cls.return_value.get_latest_articles.side_effect = RuntimeError("timeout")
            out = get_infobae_articles(limit=5)
            self.assertEqual(out, NO_ARTICLES_MESSAGE)
            self.assertIn("timeout", get_last_articles_error() or "")

            scraper_cls.return_value.get_latest_articles.side_effect = None
            scraper_cls.return_value.get_latest_articles.return_value = []
            out = get_infobae_articles(limit=5)
            self.assertEqual(out, NO_ARTICLES_MESSAGE)
            self.assertIn("no devolvió artículos", get_last_articles_error() or "")

            scraper_cls.return_value.get_latest_articles.return_value = [
                Article(title="Nota OK", url="https://www.infobae.com/economia/2026/11/21/ok/")
            ]
            out = get_infobae_articles(limit=5)
            self.assertIn("#1 Nota OK", out)
            self.assertIsNone(get_last_articles_error())


if __name__ == "__main__":
    unittest.main()

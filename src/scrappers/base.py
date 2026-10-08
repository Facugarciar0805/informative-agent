from typing import Protocol, List
from src.models import Article


class NewsScraper(Protocol):
    """Contrato que debe cumplir cualquier scraper de noticias."""

    def get_latest_articles(self, limit: int = 10) -> List[Article]:
        """Obtiene una lista de los artículos más recientes."""
        ...